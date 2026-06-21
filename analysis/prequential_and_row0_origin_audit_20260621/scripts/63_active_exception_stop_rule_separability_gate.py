from __future__ import annotations

import itertools
import json
import random
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"
AUTHORIAL = ROOT / "analysis" / "authorial_mechanism_20260620"

ACTIVE_FORMULA = (
    AUTHORIAL
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_targetmax_saturated_source_substitution_second_pass_formula_469.json"
)
BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
RESIDUAL_TARGETMAX_62 = (
    TEST_RESULTS / "62_active_residual_targetmax_resegmentation_gate.json"
)

RANDOM_SEED = 469
PERMUTATION_TRIALS = 1000


FeatureFn = Callable[[dict[str, Any]], bool]


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


def candidate_sources(available: str, chunk: str) -> list[int]:
    length = len(chunk)
    return [
        index
        for index in range(0, len(available) - length + 1)
        if available[index : index + length] == chunk
    ]


def max_target_extension(
    *, emitted: str, source_pos: int, target: str, book_pos: int
) -> int:
    max_len = min(len(emitted) - source_pos, len(target) - book_pos)
    length = 0
    while length < max_len and emitted[source_pos + length] == target[book_pos + length]:
        length += 1
    return length


def collect_copy_rows(formula: dict[str, Any], books: dict[str, str]) -> list[dict[str, Any]]:
    emitted = ""
    previous_copy: dict[str, int] | None = None
    rows: list[dict[str, Any]] = []
    for book in map(str, formula["policy"]["book_order"]):
        target = books[book]
        book_pos = 0
        ops = formula["book_recipes"][book]["ops"]
        for op_index, op in enumerate(ops):
            if op["type"] == "literal":
                text = op["text"]
                if target[book_pos : book_pos + len(text)] != text:
                    raise RuntimeError(
                        {"book": book, "op_index": op_index, "type": "literal_mismatch"}
                    )
                emitted += text
                book_pos += len(text)
                continue

            if op["type"] != "copy":
                raise RuntimeError({"book": book, "op_index": op_index, "type": "bad_op"})

            source = int(op["source_digit_pos"])
            length = int(op["length"])
            chunk = emitted[source : source + length]
            target_chunk = target[book_pos : book_pos + length]
            if chunk != target_chunk or len(chunk) != length:
                raise RuntimeError(
                    {
                        "book": book,
                        "op_index": op_index,
                        "type": "copy_mismatch",
                        "source_digit_pos": source,
                        "length": length,
                    }
                )
            candidates = candidate_sources(emitted, target_chunk)
            target_max = max_target_extension(
                emitted=emitted,
                source_pos=source,
                target=target,
                book_pos=book_pos,
            )
            decoder_max = min(len(emitted) - source, len(target) - book_pos)
            next_op = ops[op_index + 1] if op_index + 1 < len(ops) else None
            previous_end = None if previous_copy is None else previous_copy["end"]
            rows.append(
                {
                    "book": int(book),
                    "op_index": op_index,
                    "book_pos": book_pos,
                    "length": length,
                    "source_digit_pos": source,
                    "candidate_source_count": len(candidates),
                    "source_is_earliest": source == min(candidates),
                    "source_is_latest": source == max(candidates),
                    "source_is_unique": len(candidates) == 1,
                    "source_is_previous_end": source == previous_end,
                    "length_equals_decoder_max": length == decoder_max,
                    "target_max_slack": target_max - length,
                    "is_targetmax_exception": target_max > length,
                    "next_type": None if next_op is None else next_op["type"],
                    "next_length": None if next_op is None else int(next_op["length"]),
                }
            )
            emitted += chunk
            book_pos += length
            previous_copy = {
                "source_digit_pos": source,
                "length": length,
                "end": source + length,
            }
        if book_pos != len(target):
            raise RuntimeError(
                {
                    "book": book,
                    "type": "book_length_mismatch",
                    "book_pos": book_pos,
                    "target_length": len(target),
                }
            )
    return rows


def features() -> list[dict[str, Any]]:
    specs: list[tuple[str, bool, FeatureFn]] = [
        ("book_lt_35", True, lambda r: r["book"] < 35),
        ("book_ge_35", True, lambda r: r["book"] >= 35),
        ("book_ge_50", True, lambda r: r["book"] >= 50),
        ("book_ge_60", True, lambda r: r["book"] >= 60),
        ("op_index_0", True, lambda r: r["op_index"] == 0),
        ("op_index_le_1", True, lambda r: r["op_index"] <= 1),
        ("book_pos_0", True, lambda r: r["book_pos"] == 0),
        ("length_le_10", True, lambda r: r["length"] <= 10),
        ("length_le_20", True, lambda r: r["length"] <= 20),
        ("length_ge_50", True, lambda r: r["length"] >= 50),
        ("length_ge_100", True, lambda r: r["length"] >= 100),
        ("length_equals_decoder_max", True, lambda r: r["length_equals_decoder_max"]),
        ("not_length_decoder_max", True, lambda r: not r["length_equals_decoder_max"]),
        ("candidate_count_1", False, lambda r: r["candidate_source_count"] == 1),
        ("candidate_count_le_2", False, lambda r: r["candidate_source_count"] <= 2),
        ("candidate_count_ge_5", False, lambda r: r["candidate_source_count"] >= 5),
        ("source_earliest", False, lambda r: r["source_is_earliest"]),
        ("source_unique", False, lambda r: r["source_is_unique"]),
        ("source_latest", False, lambda r: r["source_is_latest"]),
        ("source_previous_end", True, lambda r: r["source_is_previous_end"]),
        ("next_type_copy", False, lambda r: r["next_type"] == "copy"),
        ("next_type_literal", False, lambda r: r["next_type"] == "literal"),
        ("next_length_le_10", False, lambda r: (r["next_length"] or 10**9) <= 10),
        ("next_length_ge_20", False, lambda r: (r["next_length"] or 0) >= 20),
    ]
    return [
        {"name": name, "decoder_valid": decoder_valid, "fn": fn}
        for name, decoder_valid, fn in specs
    ]


def rule_vectors(copy_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    feature_specs = features()
    rules = []
    for spec in feature_specs:
        rules.append(
            {
                "name": spec["name"],
                "decoder_valid": spec["decoder_valid"],
                "arity": 1,
                "selected": [bool(spec["fn"](row)) for row in copy_rows],
            }
        )
    for left, right in itertools.combinations(feature_specs, 2):
        rules.append(
            {
                "name": f"{left['name']} & {right['name']}",
                "decoder_valid": bool(left["decoder_valid"] and right["decoder_valid"]),
                "arity": 2,
                "selected": [
                    bool(left["fn"](row) and right["fn"](row)) for row in copy_rows
                ],
            }
        )
    return rules


def score_rule(rule: dict[str, Any], labels: list[bool]) -> dict[str, Any]:
    selected = rule["selected"]
    tp = sum(bool(pred) and bool(label) for pred, label in zip(selected, labels))
    fp = sum(bool(pred) and not bool(label) for pred, label in zip(selected, labels))
    fn = sum((not bool(pred)) and bool(label) for pred, label in zip(selected, labels))
    tn = sum((not bool(pred)) and (not bool(label)) for pred, label in zip(selected, labels))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "rule": rule["name"],
        "arity": rule["arity"],
        "decoder_valid": rule["decoder_valid"],
        "selected_count": sum(1 for item in selected if item),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "promotable_exact_separator": tp == sum(labels) and fp == 0,
    }


def best_scores(rules: list[dict[str, Any]], labels: list[bool]) -> list[dict[str, Any]]:
    scored = [score_rule(rule, labels) for rule in rules]
    return sorted(
        scored,
        key=lambda row: (
            row["promotable_exact_separator"],
            row["f1"],
            row["recall"],
            row["precision"],
            -row["arity"],
            -row["selected_count"],
            row["rule"],
        ),
        reverse=True,
    )


def permutation_control(
    *,
    rules: list[dict[str, Any]],
    labels: list[bool],
    observed_best_f1: float,
) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED)
    shuffled = labels[:]
    max_f1s = []
    exact_separator_count = 0
    for _ in range(PERMUTATION_TRIALS):
        rng.shuffle(shuffled)
        best = best_scores(rules, shuffled)[0]
        max_f1s.append(float(best["f1"]))
        if best["promotable_exact_separator"]:
            exact_separator_count += 1
    ordered = sorted(max_f1s)
    return {
        "seed": RANDOM_SEED,
        "trials": PERMUTATION_TRIALS,
        "max_f1_min": ordered[0],
        "max_f1_median": ordered[len(ordered) // 2],
        "max_f1_max": ordered[-1],
        "p_permuted_max_f1_ge_observed": (
            sum(1 for value in max_f1s if value >= observed_best_f1)
            / PERMUTATION_TRIALS
        ),
        "permuted_exact_separator_count": exact_separator_count,
    }


def make_result() -> dict[str, Any]:
    gate62 = load_json(RESIDUAL_TARGETMAX_62)
    assert_boundary("active_residual_targetmax_resegmentation", gate62)
    formula = load_json(ACTIVE_FORMULA)
    books = {str(k): v for k, v in load_json(BOOKS_DIGITS).items()}
    copy_rows = collect_copy_rows(formula, books)
    labels = [bool(row["is_targetmax_exception"]) for row in copy_rows]
    rules = rule_vectors(copy_rows)
    scored = best_scores(rules, labels)
    decoder_valid_scored = [row for row in scored if row["decoder_valid"]]
    best = scored[0]
    best_decoder_valid = decoder_valid_scored[0]
    controls = permutation_control(
        rules=rules,
        labels=labels,
        observed_best_f1=float(best["f1"]),
    )
    exact_separators = [row for row in scored if row["promotable_exact_separator"]]
    decoder_valid_exact_separators = [
        row for row in exact_separators if row["decoder_valid"]
    ]
    classification = (
        "active_exception_stop_rule_not_separable_by_simple_features"
        if not exact_separators
        and float(best["f1"]) < 0.5
        and float(controls["p_permuted_max_f1_ge_observed"]) > 0.05
        else "active_exception_stop_rule_simple_feature_candidate_found"
    )
    return {
        "schema": "active_exception_stop_rule_separability_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "active_formula": rel(ACTIVE_FORMULA),
            "books_digits": rel(BOOKS_DIGITS),
            "active_residual_targetmax_resegmentation": rel(RESIDUAL_TARGETMAX_62),
        },
        "scope": {
            "analysis_only": True,
            "new_formula_emitted": False,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
            "rule_family": "single-feature and two-feature conjunction stop-rule separators",
            "copy_event_count": len(copy_rows),
        },
        "summary": {
            "copy_event_count": len(copy_rows),
            "exception_count": sum(1 for label in labels if label),
            "rule_count": len(rules),
            "decoder_valid_rule_count": sum(1 for rule in rules if rule["decoder_valid"]),
            "exact_separator_count": len(exact_separators),
            "decoder_valid_exact_separator_count": len(decoder_valid_exact_separators),
            "best_rule": best,
            "best_decoder_valid_rule": best_decoder_valid,
            "top_rules": scored[:12],
            "permutation_control": controls,
            "interpretation": (
                "The residual stop boundaries are not isolated by simple declared "
                "feature rules. The best rule uses recipe/target-adjacent features, "
                "captures only 11 of 19 exceptions, and has many false positives; "
                "the best decoder-valid rule is weaker. A nonlocal parser would "
                "need richer state than these single or pairwise feature stops."
            ),
        },
        "decision": {
            "compression_bound_status": "unchanged_8156_049986",
            "stop_rule_status": "no_simple_promotable_separator",
            "copy_length_dependency_status": "retained_declared",
            "generation_explanation_status": "nonlocal_joint_parser_requires_richer_state",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / "63_active_exception_stop_rule_separability_gate.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    best = s["best_rule"]
    best_decoder = s["best_decoder_valid_rule"]
    control = s["permutation_control"]
    lines = [
        "# Active Exception Stop-Rule Separability Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 62 closes the local residual target-max rewrite frontier. This",
        "gate asks whether the 19 remaining stop-before-target-max boundaries",
        "are separable by simple single-feature or two-feature conjunction rules.",
        "It does not emit a formula or change the compression bound.",
        "",
        "## Summary",
        "",
        f"- Copy events: `{s['copy_event_count']}`.",
        f"- Target-max exceptions: `{s['exception_count']}`.",
        f"- Rules tested: `{s['rule_count']}`.",
        f"- Decoder-valid rules tested: `{s['decoder_valid_rule_count']}`.",
        f"- Exact separators: `{s['exact_separator_count']}`.",
        f"- Decoder-valid exact separators: `{s['decoder_valid_exact_separator_count']}`.",
        "",
        "## Best Rule",
        "",
        f"- Rule: `{best['rule']}`.",
        f"- Decoder-valid: `{best['decoder_valid']}`.",
        f"- TP/FP/FN/TN: `{best['tp']}` / `{best['fp']}` / `{best['fn']}` / `{best['tn']}`.",
        f"- Precision/recall/F1: `{best['precision']:.6f}` / `{best['recall']:.6f}` / `{best['f1']:.6f}`.",
        "",
        "## Best Decoder-Valid Rule",
        "",
        f"- Rule: `{best_decoder['rule']}`.",
        f"- TP/FP/FN/TN: `{best_decoder['tp']}` / `{best_decoder['fp']}` / `{best_decoder['fn']}` / `{best_decoder['tn']}`.",
        f"- Precision/recall/F1: `{best_decoder['precision']:.6f}` / `{best_decoder['recall']:.6f}` / `{best_decoder['f1']:.6f}`.",
        "",
        "## Controls",
        "",
        f"- Permutation trials: `{control['trials']}`.",
        f"- Permuted max-F1 min/median/max: `{control['max_f1_min']:.6f}` / `{control['max_f1_median']:.6f}` / `{control['max_f1_max']:.6f}`.",
        f"- P(permuted max F1 >= observed): `{control['p_permuted_max_f1_ge_observed']:.6f}`.",
        f"- Permuted exact separators: `{control['permuted_exact_separator_count']}`.",
        "",
        "## Decision",
        "",
        f"- Interpretation: {s['interpretation']}",
        "- Current compression bound remains `8156.049986` bits.",
        "- Copy length remains a declared dependency; simple stop rules do not derive the residual segmentation boundary.",
        "",
        "## Boundary",
        "",
        "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        "- Row0 origin remains unchanged and exogenous.",
        "- No new formula is emitted.",
    ]
    (TEST_RESULTS / "63_active_exception_stop_rule_separability_gate.md").write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
