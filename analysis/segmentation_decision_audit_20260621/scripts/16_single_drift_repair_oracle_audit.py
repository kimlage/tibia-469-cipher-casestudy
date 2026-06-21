from __future__ import annotations

import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

PREQ = ROOT / "analysis" / "prequential_and_row0_origin_audit_20260621"
GATE111_SCRIPT = PREQ / "scripts" / "111_decoder_length_candidate_ambiguity_audit.py"
BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
TRACE_SCRIPT = HERE / "scripts" / "01_segmentation_decision_trace.py"
POLICY_DRIFT_SCRIPT = HERE / "scripts" / "09_integrated_parser_policy_and_drift_audit.py"
POLICY_DRIFT = TEST_RESULTS / "09_integrated_parser_policy_and_drift_audit.json"
RESIDUAL_CONTEXT = TEST_RESULTS / "12_integrated_parser_residual_context_audit.json"
SOURCE_BOUNDARY = TEST_RESULTS / "15_source_boundary_alignment_audit.json"

OUT_STEM = "16_single_drift_repair_oracle_audit"
SEED_BOOKS = list(range(10))
MAX_CORRECTION_BUDGET = 5
BASELINE_POLICY = {
    "policy": "first_confirmed_peak",
    "field": "max_copy_length",
    "confirm_window": 5,
}


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


def op_equals(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return (
        left["type"] == right["type"]
        and int(left["target_start"]) == int(right["target_start"])
        and int(left["length"]) == int(right["length"])
        and left.get("source") == right.get("source")
    )


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


def next_parser_op(
    trace_module,
    policy_module,
    emitted: str,
    target: str,
    pos: int,
) -> dict[str, Any]:
    rows = policy_module.offset_rows(trace_module, emitted, target, pos)
    predicted_offset = policy_module.predict_offset(
        rows,
        BASELINE_POLICY["policy"],
        BASELINE_POLICY["field"],
        BASELINE_POLICY["confirm_window"],
    )
    if predicted_offset is None:
        return {
            "type": "literal",
            "target_start": pos,
            "length": len(target) - pos,
            "source": None,
        }
    if predicted_offset > 0:
        return {
            "type": "literal",
            "target_start": pos,
            "length": predicted_offset,
            "source": None,
        }
    copy = policy_module.choose_copy(trace_module, emitted, target, pos)
    if copy is None:
        raise RuntimeError(
            {
                "type": "predicted_zero_offset_without_copy",
                "target_start": pos,
            }
        )
    return {
        "type": "copy",
        "target_start": pos,
        "length": int(copy["length"]),
        "source": int(copy["source"]),
    }


def classify_op_diff(predicted: dict[str, Any], stable: dict[str, Any]) -> str:
    return policy_module_classify(
        {
            "index": 0,
            "predicted": predicted,
            "stable_projection": stable,
        }
    )


def policy_module_classify(diff: dict[str, Any]) -> str:
    predicted = diff["predicted"]
    stable = diff["stable_projection"]
    if predicted is None:
        return "predicted_sequence_ended_early"
    if stable is None:
        return "predicted_extra_operation"
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


def parse_with_correction_budget(
    trace_module,
    policy_module,
    target: str,
    emitted_start: str,
    stable_ops: list[dict[str, Any]],
    correction_budget: int,
) -> dict[str, Any]:
    emitted = emitted_start
    pos = 0
    stable_index = 0
    corrections: list[dict[str, Any]] = []
    matched_ops = 0
    while pos < len(target):
        if stable_index >= len(stable_ops):
            return {
                "exact": False,
                "failure": "stable_projection_ended_before_target",
                "corrections": corrections,
                "matched_ops": matched_ops,
            }
        stable = stable_ops[stable_index]
        if int(stable["target_start"]) != pos:
            return {
                "exact": False,
                "failure": "parser_position_desynced_from_stable_projection",
                "corrections": corrections,
                "matched_ops": matched_ops,
                "pos": pos,
                "stable_index": stable_index,
                "stable": stable,
            }
        predicted = next_parser_op(trace_module, policy_module, emitted, target, pos)
        if op_equals(predicted, stable):
            chosen = predicted
            matched_ops += 1
        else:
            if len(corrections) >= correction_budget:
                return {
                    "exact": False,
                    "failure": "correction_budget_exhausted",
                    "corrections": corrections,
                    "matched_ops": matched_ops,
                    "first_unrepaired_diff": {
                        "stable_index": stable_index,
                        "predicted": predicted,
                        "stable_projection": stable,
                        "drift_class": classify_op_diff(predicted, stable),
                    },
                }
            corrections.append(
                {
                    "stable_index": stable_index,
                    "target_start": pos,
                    "predicted": predicted,
                    "stable_projection": stable,
                    "drift_class": classify_op_diff(predicted, stable),
                }
            )
            chosen = stable
        emitted += target[pos : pos + int(chosen["length"])]
        pos += int(chosen["length"])
        stable_index += 1
    return {
        "exact": stable_index == len(stable_ops),
        "failure": None if stable_index == len(stable_ops) else "target_ended_before_stable_projection",
        "corrections": corrections,
        "matched_ops": matched_ops,
        "stable_ops": len(stable_ops),
    }


def make_result() -> dict[str, Any]:
    policy_drift = load_json(POLICY_DRIFT)
    residual_context = load_json(RESIDUAL_CONTEXT)
    source_boundary = load_json(SOURCE_BOUNDARY)
    assert_boundary("integrated_parser_policy_and_drift_audit", policy_drift)
    assert_boundary("integrated_parser_residual_context_audit", residual_context)
    assert_boundary("source_boundary_alignment_audit", source_boundary)
    if policy_drift["summary"]["best_policy"] != "max_copy_length:window5":
        raise RuntimeError("gate16 expects the window5 baseline parser")

    trace_module = load_module("segmentation_trace_for_gate16", TRACE_SCRIPT)
    gate111 = load_module("gate111_for_segmentation_gate16", GATE111_SCRIPT)
    policy_module = load_module("policy_drift_for_gate16", POLICY_DRIFT_SCRIPT)
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    projected_ops = trace_module.projected_ops_from_copy_rows(
        gate111.make_copy_rows(), books
    )
    stable_by_book: dict[int, list[dict[str, Any]]] = {}
    for op in projected_ops:
        stable_by_book.setdefault(int(op["book"]), []).append(op)
    for rows in stable_by_book.values():
        rows.sort(key=lambda row: int(row["target_start"]))

    book_rows: list[dict[str, Any]] = []
    budget_hits: dict[int, int] = {budget: 0 for budget in range(MAX_CORRECTION_BUDGET + 1)}
    emitted_prefix = "".join(books[book] for book in SEED_BOOKS)
    for book in range(10, 70):
        target = books[book]
        stable_ops = normalize_stable_ops(stable_by_book[book])
        budget_results = {
            budget: parse_with_correction_budget(
                trace_module,
                policy_module,
                target,
                emitted_prefix,
                stable_ops,
                budget,
            )
            for budget in range(MAX_CORRECTION_BUDGET + 1)
        }
        min_budget = None
        for budget, row in budget_results.items():
            if row["exact"]:
                budget_hits[budget] += 1
                if min_budget is None:
                    min_budget = budget
        first_repair = budget_results[1]["corrections"][:1]
        full_repair = parse_with_correction_budget(
            trace_module,
            policy_module,
            target,
            emitted_prefix,
            stable_ops,
            len(stable_ops),
        )
        book_rows.append(
            {
                "book": book,
                "stable_op_count": len(stable_ops),
                "min_correction_budget_to_exact_le5": min_budget,
                "full_oracle_correction_count": len(full_repair["corrections"]),
                "baseline_exact": budget_results[0]["exact"],
                "one_correction_exact": budget_results[1]["exact"],
                "budget_exact": {
                    str(budget): budget_results[budget]["exact"]
                    for budget in range(MAX_CORRECTION_BUDGET + 1)
                },
                "first_correction": first_repair[0] if first_repair else None,
                "failure_at_budget0": budget_results[0].get("first_unrepaired_diff"),
                "failure_at_budget1": budget_results[1].get("first_unrepaired_diff"),
            }
        )
        emitted_prefix += target

    residual_rows = [row for row in book_rows if not row["baseline_exact"]]
    one_correction_repairs = [
        row["book"] for row in residual_rows if row["one_correction_exact"]
    ]
    correction_count_histogram = Counter(
        row["full_oracle_correction_count"] for row in residual_rows
    )
    first_correction_classes = Counter(
        row["first_correction"]["drift_class"]
        for row in residual_rows
        if row["first_correction"] is not None
    )
    budget_scoreboard = [
        {
            "correction_budget": budget,
            "exact_books": budget_hits[budget],
            "residual_repairs_vs_baseline": budget_hits[budget]
            - budget_hits[0],
        }
        for budget in range(MAX_CORRECTION_BUDGET + 1)
    ]
    promotes_local_repair_rule = (
        budget_hits[1] == 60
        and len(set(first_correction_classes)) == 1
    )
    if budget_hits[1] == 60:
        classification = "single_drift_oracle_closes_parser_but_rule_missing"
    elif budget_hits[1] > budget_hits[0]:
        classification = "single_drift_oracle_partial_path_dependency"
    else:
        classification = "single_drift_oracle_no_local_repair"

    return {
        "schema": "single_drift_repair_oracle_audit.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "integrated_parser_policy_and_drift_audit": rel(POLICY_DRIFT),
            "integrated_parser_residual_context_audit": rel(RESIDUAL_CONTEXT),
            "source_boundary_alignment_audit": rel(SOURCE_BOUNDARY),
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
            "baseline_policy": "max_copy_length:window5",
            "tested_books": 60,
            "baseline_exact_books": budget_hits[0],
            "one_correction_exact_books": budget_hits[1],
            "one_correction_repairs_residual_books": one_correction_repairs,
            "one_correction_repair_count": len(one_correction_repairs),
            "max_budget_exact_books": budget_hits[MAX_CORRECTION_BUDGET],
            "residual_book_count": len(residual_rows),
            "full_oracle_correction_count_histogram": dict(
                sorted(correction_count_histogram.items())
            ),
            "first_correction_drift_classes": dict(sorted(first_correction_classes.items())),
            "promotes_local_repair_rule": promotes_local_repair_rule,
            "interpretation": (
                "A stable-projection oracle correction at the first drift is "
                "a diagnostic upper bound, not a rule. It tests whether the "
                "remaining parser failures are isolated first-decision errors "
                "or deeper path dependencies."
            ),
        },
        "budget_scoreboard": budget_scoreboard,
        "residual_book_rows": residual_rows,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": classification,
            "source_length_dependency_status": "first_drift_oracle_only_no_promoted_rule",
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
        "# Single Drift Repair Oracle Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 16 asks whether the `12` residual books from the integrated",
        "`window5` parser are local first-decision failures or deeper path",
        "dependencies. It grants an explicit stable-projection oracle only",
        "for diagnostics: when the parser first diverges, the audit can replace",
        "that one operation with the stable operation and then resume the same",
        "parser.",
        "",
        "This is not a promoted parser rule because the repair operation is",
        "chosen from the stable projection.",
        "",
        "## Correction Budget",
        "",
        "| Stable-oracle corrections per book | Exact books | Residual repairs vs baseline |",
        "|---:|---:|---:|",
    ]
    for row in result["budget_scoreboard"]:
        lines.append(
            f"| `{row['correction_budget']}` | `{row['exact_books']}/60` | "
            f"`{row['residual_repairs_vs_baseline']}` |"
        )
    lines.extend(
        [
            "",
            "## Residual Topology",
            "",
            f"- Baseline exact books: `{s['baseline_exact_books']}/60`.",
            f"- One-correction exact books: `{s['one_correction_exact_books']}/60`.",
            f"- Residual books repaired by one correction: `{s['one_correction_repairs_residual_books']}`.",
            f"- Full-oracle correction-count histogram on residual books: `{s['full_oracle_correction_count_histogram']}`.",
            f"- First-correction drift classes: `{s['first_correction_drift_classes']}`.",
            "",
            "| Book | First correction class | Full oracle corrections | One correction exact? |",
            "|---:|---|---:|---|",
        ]
    )
    for row in result["residual_book_rows"]:
        first = row["first_correction"]
        lines.append(
            f"| `{row['book']}` | `{None if first is None else first['drift_class']}` | "
            f"`{row['full_oracle_correction_count']}` | `{row['one_correction_exact']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Promotes local repair rule: `{s['promotes_local_repair_rule']}`.",
            f"- {s['interpretation']}",
            "- The result is an oracle dependency map, not a new generator.",
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
