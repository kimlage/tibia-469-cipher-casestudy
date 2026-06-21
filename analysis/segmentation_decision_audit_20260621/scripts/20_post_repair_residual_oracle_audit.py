from __future__ import annotations

import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
PREQ = ROOT / "analysis" / "prequential_and_row0_origin_audit_20260621"
GATE111_SCRIPT = PREQ / "scripts" / "111_decoder_length_candidate_ambiguity_audit.py"
TRACE_SCRIPT = HERE / "scripts" / "01_segmentation_decision_trace.py"
POLICY_DRIFT_SCRIPT = HERE / "scripts" / "09_integrated_parser_policy_and_drift_audit.py"
OBSERVABLE_REPAIR_SCRIPT = HERE / "scripts" / "17_observable_repair_policy_audit.py"
CONDITIONAL_REPAIR_SCRIPT = HERE / "scripts" / "18_conditional_repair_classifier_audit.py"
TWO_STAGE_REPAIR = TEST_RESULTS / "19_two_stage_conditional_repair_audit.json"

OUT_STEM = "20_post_repair_residual_oracle_audit"
SEED_BOOKS = list(range(10))
MAX_CORRECTION_BUDGET = 5
ACTIVE_CLASSIFIER = "if_peak_len_le5_then_skip_to_next_peak_ge5"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


def normalize_stable_ops(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "type": row["type"],
            "target_start": int(row["target_start"]),
            "length": int(row["length"]),
            "source": row["source"],
        }
        for row in rows
    ]


def op_equals(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return (
        left["type"] == right["type"]
        and int(left["target_start"]) == int(right["target_start"])
        and int(left["length"]) == int(right["length"])
        and left.get("source") == right.get("source")
    )


def classify_diff(predicted: dict[str, Any], stable: dict[str, Any]) -> str:
    if predicted["type"] == "literal" and stable["type"] == "literal":
        if predicted["length"] < stable["length"]:
            return "literal_understop"
        if predicted["length"] > stable["length"]:
            return "literal_overstop"
        return "literal_other_mismatch"
    if predicted["type"] == "literal" and stable["type"] == "copy":
        if predicted["target_start"] == 0:
            return "book_start_copy_missed_as_literal"
        return "internal_copy_missed_as_literal"
    if predicted["type"] == "copy" and stable["type"] == "literal":
        return "copy_started_inside_stable_literal"
    if predicted["type"] == "copy" and stable["type"] == "copy":
        if predicted["source"] == stable["source"] and predicted["length"] != stable["length"]:
            return "copy_length_drift_same_source"
        if predicted["length"] == stable["length"] and predicted["source"] != stable["source"]:
            return "copy_source_drift_same_length"
        return "copy_pair_drift"
    return "other_drift"


def active_next_op(
    repair_module,
    conditional_module,
    trace_module,
    policy_module,
    predicates: dict[str, Callable[[dict[str, Any]], bool]],
    classifier: dict[str, Any],
    emitted: str,
    target: str,
    pos: int,
    previous_type: str,
    previous_length: int,
    op_index: int,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    predicted, context = repair_module.baseline_op(
        policy_module, trace_module, emitted, target, pos
    )
    row = conditional_module.context_row(
        target, pos, predicted, context, previous_type, previous_length, op_index
    )
    if not predicates[classifier["predicate"]](row):
        return predicted, None
    repaired, reason = repair_module.apply_repair_policy(
        policy_module,
        trace_module,
        emitted,
        target,
        pos,
        predicted,
        context,
        classifier["action"],
    )
    if reason is None:
        return predicted, None
    return repaired, {
        "target_start": pos,
        "predicate": classifier["predicate"],
        "repair": reason,
        "baseline": predicted,
        "chosen": repaired,
        "features": row,
    }


def parse_with_oracle_budget(
    repair_module,
    conditional_module,
    trace_module,
    policy_module,
    predicates: dict[str, Callable[[dict[str, Any]], bool]],
    classifier: dict[str, Any],
    target: str,
    emitted_start: str,
    stable_ops: list[dict[str, Any]],
    correction_budget: int,
) -> dict[str, Any]:
    emitted = emitted_start
    pos = 0
    stable_index = 0
    previous_type = "BOS"
    previous_length = 0
    parser_repairs: list[dict[str, Any]] = []
    oracle_corrections: list[dict[str, Any]] = []
    while pos < len(target):
        if stable_index >= len(stable_ops):
            return {
                "exact": False,
                "failure": "stable_projection_ended_before_target",
                "oracle_corrections": oracle_corrections,
                "parser_repairs": parser_repairs,
            }
        stable = stable_ops[stable_index]
        if int(stable["target_start"]) != pos:
            return {
                "exact": False,
                "failure": "parser_position_desynced_from_stable_projection",
                "oracle_corrections": oracle_corrections,
                "parser_repairs": parser_repairs,
                "pos": pos,
                "stable_index": stable_index,
                "stable": stable,
            }
        predicted, repair = active_next_op(
            repair_module,
            conditional_module,
            trace_module,
            policy_module,
            predicates,
            classifier,
            emitted,
            target,
            pos,
            previous_type,
            previous_length,
            stable_index,
        )
        if repair is not None:
            parser_repairs.append(repair)
        if op_equals(predicted, stable):
            chosen = predicted
        else:
            if len(oracle_corrections) >= correction_budget:
                return {
                    "exact": False,
                    "failure": "correction_budget_exhausted",
                    "oracle_corrections": oracle_corrections,
                    "parser_repairs": parser_repairs,
                    "first_unrepaired_diff": {
                        "stable_index": stable_index,
                        "target_start": pos,
                        "predicted": predicted,
                        "stable_projection": stable,
                        "drift_class": classify_diff(predicted, stable),
                    },
                }
            oracle_corrections.append(
                {
                    "stable_index": stable_index,
                    "target_start": pos,
                    "predicted": predicted,
                    "stable_projection": stable,
                    "drift_class": classify_diff(predicted, stable),
                }
            )
            chosen = stable
        emitted += target[pos : pos + int(chosen["length"])]
        previous_type = chosen["type"]
        previous_length = int(chosen["length"])
        pos += int(chosen["length"])
        stable_index += 1
    return {
        "exact": stable_index == len(stable_ops),
        "failure": None if stable_index == len(stable_ops) else "target_ended_before_stable_projection",
        "oracle_corrections": oracle_corrections,
        "parser_repairs": parser_repairs,
        "stable_ops": len(stable_ops),
    }


def make_result() -> dict[str, Any]:
    two_stage = load_json(TWO_STAGE_REPAIR)
    assert_boundary("two_stage_conditional_repair_audit", two_stage)
    if two_stage["summary"]["active_exact_books"] != 50:
        raise RuntimeError("gate20 expects the gate18 active parser at 50/60")

    trace_module = load_module("segmentation_trace_for_gate20", TRACE_SCRIPT)
    gate111 = load_module("gate111_for_segmentation_gate20", GATE111_SCRIPT)
    policy_module = load_module("policy_drift_for_gate20", POLICY_DRIFT_SCRIPT)
    repair_module = load_module("observable_repair_for_gate20", OBSERVABLE_REPAIR_SCRIPT)
    conditional_module = load_module("conditional_repair_for_gate20", CONDITIONAL_REPAIR_SCRIPT)
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    projected_ops = trace_module.projected_ops_from_copy_rows(
        gate111.make_copy_rows(), books
    )
    stable_by_book: dict[int, list[dict[str, Any]]] = {}
    for op in projected_ops:
        stable_by_book.setdefault(int(op["book"]), []).append(op)
    for rows in stable_by_book.values():
        rows.sort(key=lambda row: int(row["target_start"]))

    classifiers = {row["label"]: row for row in conditional_module.make_classifiers()}
    classifier = classifiers[ACTIVE_CLASSIFIER]
    predicates = {"always_false": lambda row: False}
    predicates.update({name: fn for name, fn in conditional_module.make_predicates()})

    budget_hits = {budget: 0 for budget in range(MAX_CORRECTION_BUDGET + 1)}
    book_rows: list[dict[str, Any]] = []
    emitted_prefix = "".join(books[book] for book in SEED_BOOKS)
    for book in range(10, 70):
        target = books[book]
        stable_ops = normalize_stable_ops(stable_by_book[book])
        budget_results = {
            budget: parse_with_oracle_budget(
                repair_module,
                conditional_module,
                trace_module,
                policy_module,
                predicates,
                classifier,
                target,
                emitted_prefix,
                stable_ops,
                budget,
            )
            for budget in range(MAX_CORRECTION_BUDGET + 1)
        }
        full_oracle = parse_with_oracle_budget(
            repair_module,
            conditional_module,
            trace_module,
            policy_module,
            predicates,
            classifier,
            target,
            emitted_prefix,
            stable_ops,
            len(stable_ops),
        )
        min_budget = None
        for budget, result in budget_results.items():
            if result["exact"]:
                budget_hits[budget] += 1
                if min_budget is None:
                    min_budget = budget
        book_rows.append(
            {
                "book": book,
                "stable_op_count": len(stable_ops),
                "baseline_exact": budget_results[0]["exact"],
                "one_correction_exact": budget_results[1]["exact"],
                "min_correction_budget_to_exact_le5": min_budget,
                "full_oracle_correction_count": len(full_oracle["oracle_corrections"]),
                "parser_repair_count_without_oracle": len(budget_results[0]["parser_repairs"]),
                "first_oracle_correction": (
                    None
                    if not full_oracle["oracle_corrections"]
                    else full_oracle["oracle_corrections"][0]
                ),
                "failure_at_budget0": budget_results[0].get("first_unrepaired_diff"),
                "failure_at_budget1": budget_results[1].get("first_unrepaired_diff"),
            }
        )
        emitted_prefix += target

    residual_rows = [row for row in book_rows if not row["baseline_exact"]]
    one_correction_repairs = [
        row["book"] for row in residual_rows if row["one_correction_exact"]
    ]
    correction_histogram = Counter(
        row["full_oracle_correction_count"] for row in residual_rows
    )
    first_correction_classes = Counter(
        row["first_oracle_correction"]["drift_class"]
        for row in residual_rows
        if row["first_oracle_correction"] is not None
    )
    promotes = budget_hits[1] == 60
    classification = (
        "post_repair_oracle_localizes_residual_not_promoted"
        if budget_hits[1] > budget_hits[0]
        else "post_repair_oracle_no_localization_gain"
    )
    return {
        "schema": "post_repair_residual_oracle_audit.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "two_stage_conditional_repair_audit": rel(TWO_STAGE_REPAIR),
        },
        "scope": {
            "analysis_only": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "target_text_required": True,
            "stable_projection_oracle_used": True,
            "declared_literal_windows_granted": False,
            "source_free_digit_generator_emitted": False,
            "promotes_parser_rule": False,
        },
        "summary": {
            "active_classifier": ACTIVE_CLASSIFIER,
            "active_exact_books": budget_hits[0],
            "residual_book_count": len(residual_rows),
            "one_correction_exact_books": budget_hits[1],
            "one_correction_repairs_residual_books": one_correction_repairs,
            "one_correction_repair_count": len(one_correction_repairs),
            "max_budget_exact_books": budget_hits[MAX_CORRECTION_BUDGET],
            "full_oracle_correction_count_histogram": dict(
                sorted(correction_histogram.items())
            ),
            "first_oracle_correction_drift_classes": dict(
                sorted(first_correction_classes.items())
            ),
            "promotes_post_repair_oracle_as_rule": promotes,
            "interpretation": (
                "After the gate18 non-oracle repair, this audit grants stable-"
                "projection corrections only to measure whether the remaining "
                "drifts are local first-decision failures or deeper path dependencies."
            ),
        },
        "budget_scoreboard": [
            {
                "correction_budget": budget,
                "exact_books": budget_hits[budget],
                "residual_repairs_vs_active": budget_hits[budget] - budget_hits[0],
            }
            for budget in range(MAX_CORRECTION_BUDGET + 1)
        ],
        "residual_book_rows": residual_rows,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": classification,
            "source_length_dependency_status": "post_repair_residual_oracle_map",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / f"{OUT_STEM}.json"
    md_path = TEST_RESULTS / f"{OUT_STEM}.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    lines = [
        "# Post-Repair Residual Oracle Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 20 keeps the gate-18 non-oracle classifier active, then grants",
        "stable-projection oracle corrections only as a diagnostic upper bound.",
        "It asks whether the remaining `10` residual books are still local",
        "first-decision failures or have become deeper path dependencies.",
        "",
        "## Correction Budget",
        "",
        f"- Active classifier: `{s['active_classifier']}`.",
        f"- Active exact books: `{s['active_exact_books']}/60`.",
        "",
        "| Stable-oracle corrections per book | Exact books | Residual repairs vs active |",
        "|---:|---:|---:|",
    ]
    for row in result["budget_scoreboard"]:
        lines.append(
            f"| `{row['correction_budget']}` | `{row['exact_books']}/60` | "
            f"`{row['residual_repairs_vs_active']}` |"
        )
    lines.extend(
        [
            "",
            "## Residual Topology",
            "",
            f"- One-correction repaired residual books: `{s['one_correction_repairs_residual_books']}`.",
            f"- Full-oracle correction-count histogram: `{s['full_oracle_correction_count_histogram']}`.",
            f"- First-oracle correction drift classes: `{s['first_oracle_correction_drift_classes']}`.",
            "",
            "| Book | First oracle class | Full oracle corrections | One correction exact? |",
            "|---:|---|---:|---|",
        ]
    )
    for row in result["residual_book_rows"]:
        first = row["first_oracle_correction"]
        lines.append(
            f"| `{row['book']}` | `{None if first is None else first['drift_class']}` | "
            f"`{row['full_oracle_correction_count']}` | `{row['one_correction_exact']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Promotes parser rule: `{s['promotes_post_repair_oracle_as_rule']}`.",
            f"- {s['interpretation']}",
            "- The result is an oracle dependency map, not a generator.",
            "- Compression bound is unchanged.",
            "- Row0 remains exogenous and unchanged.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
            "",
        ]
    )
    md_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    result = make_result()
    write_result(result)
    print(json.dumps(result["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
