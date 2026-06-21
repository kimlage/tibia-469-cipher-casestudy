from __future__ import annotations

import json
import random
from pathlib import Path
from statistics import mean, median
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

GATE100 = TEST_RESULTS / "100_skeleton_rule_coverage_audit.json"
GATE103 = TEST_RESULTS / "103_copy_availability_type_exception_ledger.json"

RANDOM_SEED = 469105
CONTROL_TRIALS = 2000


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def assert_boundary(name: str, data: dict[str, Any]) -> None:
    if data.get("translation_delta") != "NONE":
        raise RuntimeError(f"{name} changed translation boundary")
    if data.get("case_reopened", False) is not False:
        raise RuntimeError(f"{name} reopened case")
    if data.get("plaintext_claim", False) is not False:
        raise RuntimeError(f"{name} introduced plaintext")
    decision = data.get("decision", {})
    if decision.get("row0_origin_status") not in {
        None,
        "unchanged_exogenous",
        "exogenous_under_current_evidence",
    }:
        raise RuntimeError(f"{name} changed row0 origin")
    if decision.get("translation_or_plaintext_status", "NONE") != "NONE":
        raise RuntimeError(f"{name} introduced translation/plaintext")


def bitmask(rows: list[dict[str, Any]], fn: Callable[[dict[str, Any]], bool]) -> int:
    mask = 0
    for index, row in enumerate(rows):
        if fn(row):
            mask |= 1 << index
    return mask


def score(mask: int, label_mask: int, total: int) -> dict[str, Any]:
    tp = (mask & label_mask).bit_count()
    fp = (mask & ~label_mask).bit_count()
    fn = ((~mask) & label_mask).bit_count()
    tn = total - tp - fp - fn
    errors = fp + fn
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )
    return {
        "errors": errors,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def summarize(values: list[int]) -> dict[str, Any]:
    return {
        "trials": len(values),
        "min": min(values),
        "median": median(values),
        "mean": mean(values),
        "max": max(values),
    }


def primitive_masks(rows: list[dict[str, Any]]) -> list[tuple[str, int]]:
    items: list[tuple[str, int]] = []

    def add(name: str, fn: Callable[[dict[str, Any]], bool]) -> None:
        mask = bitmask(rows, fn)
        if mask and mask != (1 << len(rows)) - 1:
            items.append((name, mask))

    add("op_index_eq_0", lambda row: int(row["op_index"]) == 0)
    add("op_index_le_1", lambda row: int(row["op_index"]) <= 1)
    add("op_index_ge_1", lambda row: int(row["op_index"]) >= 1)
    for threshold in [1, 2, 3, 4, 5, 6, 7, 10, 12, 13, 20, 24, 50, 100, 133]:
        add(
            f"length_le_{threshold}",
            lambda row, threshold=threshold: int(row["length"]) <= threshold,
        )
        add(
            f"length_ge_{threshold}",
            lambda row, threshold=threshold: int(row["length"]) >= threshold,
        )
    for threshold in [1, 2, 3, 5, 10, 20, 24, 35, 50, 55, 88, 100, 125, 149, 200, 281]:
        add(
            f"target_start_le_{threshold}",
            lambda row, threshold=threshold: int(row["target_start"]) <= threshold,
        )
        add(
            f"target_start_ge_{threshold}",
            lambda row, threshold=threshold: int(row["target_start"]) >= threshold,
        )
    for threshold in [10, 20, 24, 35, 50, 55, 88, 100, 125, 149, 200, 281]:
        add(
            f"remaining_le_{threshold}",
            lambda row, threshold=threshold: int(row["remaining"]) <= threshold,
        )
        add(
            f"remaining_ge_{threshold}",
            lambda row, threshold=threshold: int(row["remaining"]) >= threshold,
        )
    add("prev_none", lambda row: row["previous_in_book_type"] is None)
    add("prev_copy", lambda row: row["previous_in_book_type"] == "copy")
    for threshold in [5, 6, 10, 11, 12, 13, 20, 24, 50, 100, 112, 133]:
        add(
            f"prev_len_le_{threshold}",
            lambda row, threshold=threshold: row["previous_in_book_length"] is not None
            and int(row["previous_in_book_length"]) <= threshold,
        )
        add(
            f"prev_len_ge_{threshold}",
            lambda row, threshold=threshold: row["previous_in_book_length"] is not None
            and int(row["previous_in_book_length"]) >= threshold,
        )
    return items


def make_rule_masks(primitives: list[tuple[str, int]], total: int) -> list[tuple[str, int, str]]:
    all_mask = (1 << total) - 1
    seen: dict[int, tuple[str, int, str]] = {}
    for name, mask in primitives:
        seen.setdefault(mask, (name, mask, "primitive"))
    for index, (name_a, mask_a) in enumerate(primitives):
        for name_b, mask_b in primitives[index + 1 :]:
            and_mask = mask_a & mask_b
            if and_mask and and_mask != all_mask:
                seen.setdefault(and_mask, (f"({name_a} and {name_b})", and_mask, "pair"))
            or_mask = mask_a | mask_b
            if or_mask and or_mask != all_mask:
                seen.setdefault(or_mask, (f"({name_a} or {name_b})", or_mask, "pair"))
    return list(seen.values())


def rows_for_mask(rows: list[dict[str, Any]], mask: int, label_mask: int) -> dict[str, Any]:
    false_positive = []
    false_negative = []
    true_positive = []
    for index, row in enumerate(rows):
        predicted = bool(mask & (1 << index))
        actual = bool(label_mask & (1 << index))
        compact = {
            "book": int(row["book"]),
            "op_index": int(row["op_index"]),
            "target_start": int(row["target_start"]),
            "remaining": int(row["remaining"]),
            "length": int(row["length"]),
            "type": row["type"],
        }
        if predicted and actual:
            true_positive.append(compact)
        elif predicted and not actual:
            false_positive.append(compact)
        elif actual and not predicted:
            false_negative.append(compact)
    return {
        "true_positive_rows": true_positive,
        "false_positive_rows": false_positive,
        "false_negative_rows": false_negative,
    }


def make_result() -> dict[str, Any]:
    gate100 = load_json(GATE100)
    gate103 = load_json(GATE103)
    assert_boundary("skeleton_rule_coverage_audit", gate100)
    assert_boundary("copy_availability_type_exception_ledger", gate103)
    if gate103["classification"] != "copy_availability_type_exception_audit_only":
        raise RuntimeError("gate103 did not keep copy availability audit-only")

    rows = sorted(
        [
            row
            for row in gate100["skeleton_rows"]
            if bool(row["copy_available_minlen"])
        ],
        key=lambda row: (int(row["book"]), int(row["op_index"])),
    )
    label_mask = bitmask(rows, lambda row: row["type"] == "literal")
    total = len(rows)
    exception_count = label_mask.bit_count()
    primitives = primitive_masks(rows)
    rule_masks = make_rule_masks(primitives, total)
    scored = []
    for name, mask, kind in rule_masks:
        scored.append({"rule": name, "kind": kind, **score(mask, label_mask, total), "mask": mask})
    scored.sort(key=lambda row: (row["errors"], -row["f1"], row["kind"], row["rule"]))
    best = scored[0]
    best_single = next(row for row in scored if row["kind"] == "primitive")

    rng = random.Random(RANDOM_SEED)
    control_min_errors: list[int] = []
    indexes = list(range(total))
    for _ in range(CONTROL_TRIALS):
        label_indexes = rng.sample(indexes, exception_count)
        shuffled_label_mask = 0
        for index in label_indexes:
            shuffled_label_mask |= 1 << index
        control_min_errors.append(
            min(
                score(mask, shuffled_label_mask, total)["errors"]
                for _name, mask, _kind in rule_masks
            )
        )
    empirical_p = (
        sum(1 for value in control_min_errors if value <= best["errors"])
        / CONTROL_TRIALS
    )

    residual_exact_exception_records = int(best["errors"])
    availability_baseline_errors = int(gate103["summary"]["availability_rule_errors"])
    gate103_conditioned_records = int(
        gate103["summary"]["availability_conditioned_skeleton_records"]
    )
    rule_conditioned_records = (
        int(gate103["summary"]["op_count"]) + residual_exact_exception_records
    )
    promotes_exception_rule = (
        best["errors"] == 0
        and gate103["scope"]["target_text_dependency_retained"] is False
    )
    classification = (
        "optional_literal_exception_rule_promotable"
        if promotes_exception_rule
        else "optional_literal_exception_rule_audit_only"
    )

    row_examples = rows_for_mask(rows, int(best["mask"]), label_mask)
    top_rules = [
        {key: value for key, value in row.items() if key != "mask"}
        for row in scored[:10]
    ]
    return {
        "schema": "optional_literal_exception_rule_audit.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "gate100_skeleton_rule_coverage": rel(GATE100),
            "gate103_copy_availability_type_exception": rel(GATE103),
        },
        "scope": {
            "analysis_only": True,
            "tests_optional_literal_exception_rules": True,
            "target_text_dependency_retained": True,
            "compression_bound_changed": False,
            "new_formula_emitted": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
            "rule_library_excludes_book_id": True,
            "control_trials": CONTROL_TRIALS,
            "random_seed": RANDOM_SEED,
        },
        "summary": {
            "available_rows": total,
            "optional_literal_exception_rows": exception_count,
            "availability_baseline_errors": availability_baseline_errors,
            "primitive_rule_count": len(primitives),
            "total_rule_count_after_dedup": len(rule_masks),
            "best_rule": best["rule"],
            "best_rule_kind": best["kind"],
            "best_rule_errors": best["errors"],
            "best_rule_tp": best["tp"],
            "best_rule_fp": best["fp"],
            "best_rule_fn": best["fn"],
            "best_rule_precision": best["precision"],
            "best_rule_recall": best["recall"],
            "best_single_rule": best_single["rule"],
            "best_single_rule_errors": best_single["errors"],
            "error_delta_vs_availability_baseline": best["errors"] - availability_baseline_errors,
            "gate103_conditioned_skeleton_records": gate103_conditioned_records,
            "rule_conditioned_skeleton_records": rule_conditioned_records,
            "record_delta_vs_gate103_conditioned": (
                rule_conditioned_records - gate103_conditioned_records
            ),
            "promotes_exception_rule": promotes_exception_rule,
            "interpretation": (
                "A short target-dependent rule explains most optional literal "
                "exceptions: available-copy rows with length <= 5 and remaining "
                ">= 10 account for all 17 optional literals but incorrectly mark "
                "3 copy rows. This is far better than shuffled controls, but it "
                "still depends on target copy availability and on the external "
                "length atlas, so it is a structural clue rather than a promoted "
                "generator."
            ),
        },
        "controls": {
            "shuffled_exception_labels": {
                **summarize(control_min_errors),
                "empirical_p_min_errors_lte_observed": empirical_p,
            }
        },
        "top_rules": top_rules,
        "best_rule_rows": row_examples,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": "optional_literal_exception_rule_audit_only",
            "skeleton_status": "exception_rule_partial_target_dependent_clue",
            "source_dependency_status": "retained_declared_dependency",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / "105_optional_literal_exception_rule_audit.json"
    md_path = TEST_RESULTS / "105_optional_literal_exception_rule_audit.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    c = result["controls"]["shuffled_exception_labels"]
    lines = [
        "# Optional Literal Exception Rule Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 103 reduced operation type to target-dependent copy availability plus",
        "`17` optional literal exceptions. This audit tests whether those exceptions",
        "are explained by simple non-book-id rules over skeleton fields.",
        "",
        "## Result",
        "",
        f"- Available-copy rows: `{s['available_rows']}`.",
        f"- Optional literal exceptions: `{s['optional_literal_exception_rows']}`.",
        f"- Availability baseline errors: `{s['availability_baseline_errors']}`.",
        f"- Primitive / total deduped rules: `{s['primitive_rule_count']}` / `{s['total_rule_count_after_dedup']}`.",
        f"- Best rule: `{s['best_rule']}`.",
        f"- Best rule errors: `{s['best_rule_errors']}`.",
        f"- Best rule TP/FP/FN: `{s['best_rule_tp']}` / `{s['best_rule_fp']}` / `{s['best_rule_fn']}`.",
        f"- Best single rule/errors: `{s['best_single_rule']}` / `{s['best_single_rule_errors']}`.",
        f"- Error delta vs availability baseline: `{s['error_delta_vs_availability_baseline']}`.",
        f"- Rule-conditioned skeleton records: `{s['rule_conditioned_skeleton_records']}`.",
        f"- Record delta vs gate 103 conditioned skeleton: `{s['record_delta_vs_gate103_conditioned']}`.",
        "",
        "## Controls",
        "",
        f"- Shuffled-label min/median/mean/max best errors: `{c['min']}` / `{c['median']}` / `{c['mean']:.3f}` / `{c['max']}`.",
        f"- Empirical p(min errors <= observed): `{c['empirical_p_min_errors_lte_observed']:.6f}`.",
        "",
        "## Decision",
        "",
        f"- Promotes exception rule: `{s['promotes_exception_rule']}`.",
        f"- {s['interpretation']}",
        "- Taxonomy: `AUDIT_ONLY`.",
        "- No compression-bound change is introduced.",
        "- No formula is emitted.",
        "- Row0 remains unchanged and exogenous.",
        "- No plaintext, translation, semantic reading, or case reopening is introduced.",
    ]
    md_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    result = make_result()
    write_result(result)
    print(json.dumps(result["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
