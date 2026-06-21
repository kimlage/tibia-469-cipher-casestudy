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
CONDITIONAL_REPAIR = TEST_RESULTS / "18_conditional_repair_classifier_audit.json"

OUT_STEM = "19_two_stage_conditional_repair_audit"
SEED_BOOKS = list(range(10))
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
ACTIVE_FIRST_STAGE = "if_peak_len_le5_then_skip_to_next_peak_ge5"


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


def normalized_projected_ops(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "type": row["type"],
            "target_start": int(row["target_start"]),
            "length": int(row["length"]),
            "source": row["source"],
        }
        for row in rows
    ]


def classifier_map(conditional_module) -> dict[str, dict[str, Any]]:
    return {row["label"]: row for row in conditional_module.make_classifiers()}


def make_pipelines(conditional_module) -> list[dict[str, Any]]:
    classifiers = classifier_map(conditional_module)
    first = classifiers[ACTIVE_FIRST_STAGE]
    pipelines = [
        {
            "label": ACTIVE_FIRST_STAGE,
            "first_stage": first,
            "second_stage": None,
        }
    ]
    for classifier in conditional_module.make_classifiers():
        if classifier["label"] in {"baseline_window5", ACTIVE_FIRST_STAGE}:
            continue
        pipelines.append(
            {
                "label": f"{ACTIVE_FIRST_STAGE}__then__{classifier['label']}",
                "first_stage": first,
                "second_stage": classifier,
            }
        )
    return pipelines


def parse_book_with_pipeline(
    repair_module,
    conditional_module,
    trace_module,
    policy_module,
    target: str,
    emitted: str,
    pipeline: dict[str, Any],
    predicates: dict[str, Callable[[dict[str, Any]], bool]],
) -> tuple[list[dict[str, Any]], str, list[dict[str, Any]]]:
    pos = 0
    op_index = 0
    previous_type = "BOS"
    previous_length = 0
    ops: list[dict[str, Any]] = []
    repairs: list[dict[str, Any]] = []
    while pos < len(target):
        predicted, context = repair_module.baseline_op(
            policy_module, trace_module, emitted, target, pos
        )
        chosen = predicted
        row = conditional_module.context_row(
            target, pos, predicted, context, previous_type, previous_length, op_index
        )
        for stage_name in ["first_stage", "second_stage"]:
            classifier = pipeline[stage_name]
            if classifier is None:
                continue
            if not predicates[classifier["predicate"]](row):
                continue
            repaired, reason = repair_module.apply_repair_policy(
                policy_module,
                trace_module,
                emitted,
                target,
                pos,
                chosen,
                context,
                classifier["action"],
            )
            if reason is None:
                continue
            repairs.append(
                {
                    "target_start": pos,
                    "stage": stage_name,
                    "predicate": classifier["predicate"],
                    "repair": reason,
                    "baseline": predicted,
                    "chosen_before": chosen,
                    "chosen_after": repaired,
                    "features": row,
                }
            )
            chosen = repaired
            # Keep the first stage from being immediately overwritten by the
            # second stage at the same target position.
            if stage_name == "first_stage":
                break
        if int(chosen["length"]) <= 0:
            raise RuntimeError({"type": "non_positive_chosen_op", "chosen": chosen})
        ops.append(chosen)
        emitted += target[pos : pos + int(chosen["length"])]
        previous_type = chosen["type"]
        previous_length = int(chosen["length"])
        pos += int(chosen["length"])
        op_index += 1
    return ops, emitted, repairs


def first_diff(repair_module, predicted: list[dict[str, Any]], projected: list[dict[str, Any]]) -> dict[str, Any] | None:
    diff = repair_module.first_diff(predicted, projected)
    if diff is None:
        return None
    diff = dict(diff)
    diff["drift_class"] = repair_module.classify_diff(diff)
    return diff


def score_pipeline(
    repair_module,
    conditional_module,
    trace_module,
    policy_module,
    books: dict[int, str],
    stable_by_book: dict[int, list[dict[str, Any]]],
    pipeline: dict[str, Any],
    predicates: dict[str, Callable[[dict[str, Any]], bool]],
) -> dict[str, Any]:
    emitted = "".join(books[book] for book in SEED_BOOKS)
    exact_books: list[int] = []
    mismatch_rows: list[dict[str, Any]] = []
    repair_counts: Counter[str] = Counter()
    stage_counts: Counter[str] = Counter()
    total_repairs = 0
    for book in range(10, 70):
        predicted, emitted, repairs = parse_book_with_pipeline(
            repair_module,
            conditional_module,
            trace_module,
            policy_module,
            books[book],
            emitted,
            pipeline,
            predicates,
        )
        projected = normalized_projected_ops(stable_by_book[book])
        total_repairs += len(repairs)
        for repair in repairs:
            repair_counts[repair["repair"]] += 1
            stage_counts[repair["stage"]] += 1
        diff = first_diff(repair_module, predicted, projected)
        if diff is None:
            exact_books.append(book)
        else:
            mismatch_rows.append(
                {
                    "book": book,
                    "first_diff": diff,
                    "drift_class": diff["drift_class"],
                    "repair_count": len(repairs),
                    "first_repairs": repairs[:5],
                }
            )
    drift_classes = Counter(row["drift_class"] for row in mismatch_rows)
    return {
        "label": pipeline["label"],
        "second_stage": None
        if pipeline["second_stage"] is None
        else pipeline["second_stage"]["label"],
        "tested_books": 60,
        "exact_book_count": len(exact_books),
        "exact_books": exact_books,
        "mismatch_book_count": len(mismatch_rows),
        "mismatch_books": [row["book"] for row in mismatch_rows],
        "total_repairs_applied": total_repairs,
        "repair_counts": dict(sorted(repair_counts.items())),
        "stage_counts": dict(sorted(stage_counts.items())),
        "drift_class_counts": dict(sorted(drift_classes.items())),
        "mismatch_rows": mismatch_rows,
    }


def prequential_selection(scores: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for cutoff in PREFIX_CUTOFFS:
        train_books = set(range(10, cutoff))
        test_books = set(range(cutoff, 70))
        candidates = []
        for score in scores:
            exact = set(score["exact_books"])
            candidates.append(
                {
                    "label": score["label"],
                    "train_hits": len(exact & train_books),
                    "train_total": len(train_books),
                    "test_hits": len(exact & test_books),
                    "test_total": len(test_books),
                    "exact_book_count": score["exact_book_count"],
                    "total_repairs_applied": score["total_repairs_applied"],
                }
            )
        selected = max(
            candidates,
            key=lambda row: (
                row["train_hits"],
                row["test_hits"],
                row["exact_book_count"],
                -row["total_repairs_applied"],
                row["label"],
            ),
        )
        oracle = max(candidates, key=lambda row: (row["test_hits"], row["train_hits"]))
        rows.append(
            {
                "cutoff_book": cutoff,
                "selected_pipeline": selected["label"],
                "train_hits": selected["train_hits"],
                "train_total": selected["train_total"],
                "test_hits": selected["test_hits"],
                "test_total": selected["test_total"],
                "oracle_pipeline": oracle["label"],
                "oracle_test_hits": oracle["test_hits"],
                "selected_matches_oracle": selected["test_hits"] == oracle["test_hits"],
            }
        )
    return rows


def make_result() -> dict[str, Any]:
    conditional = load_json(CONDITIONAL_REPAIR)
    assert_boundary("conditional_repair_classifier_audit", conditional)
    if conditional["summary"]["best_classifier"] != ACTIVE_FIRST_STAGE:
        raise RuntimeError("gate19 expects the gate18 peak-length repair")

    trace_module = load_module("segmentation_trace_for_gate19", TRACE_SCRIPT)
    gate111 = load_module("gate111_for_segmentation_gate19", GATE111_SCRIPT)
    policy_module = load_module("policy_drift_for_gate19", POLICY_DRIFT_SCRIPT)
    repair_module = load_module("observable_repair_for_gate19", OBSERVABLE_REPAIR_SCRIPT)
    conditional_module = load_module("conditional_repair_for_gate19", CONDITIONAL_REPAIR_SCRIPT)
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    projected_ops = trace_module.projected_ops_from_copy_rows(
        gate111.make_copy_rows(), books
    )
    stable_by_book: dict[int, list[dict[str, Any]]] = {}
    for op in projected_ops:
        stable_by_book.setdefault(int(op["book"]), []).append(op)
    for rows in stable_by_book.values():
        rows.sort(key=lambda row: int(row["target_start"]))

    predicate_list = conditional_module.make_predicates()
    predicates = {"always_false": lambda row: False}
    predicates.update({name: fn for name, fn in predicate_list})
    pipelines = make_pipelines(conditional_module)
    scores = [
        score_pipeline(
            repair_module,
            conditional_module,
            trace_module,
            policy_module,
            books,
            stable_by_book,
            pipeline,
            predicates,
        )
        for pipeline in pipelines
    ]
    active = next(row for row in scores if row["label"] == ACTIVE_FIRST_STAGE)
    best = max(
        scores,
        key=lambda row: (
            row["exact_book_count"],
            -row["total_repairs_applied"],
            row["label"],
        ),
    )
    preq = prequential_selection(scores)
    preq_stable = all(row["selected_matches_oracle"] for row in preq)
    delta = best["exact_book_count"] - active["exact_book_count"]
    promotes = best["exact_book_count"] == 60 and preq_stable
    if promotes:
        classification = "two_stage_conditional_repair_promoted_target_text_parser"
    elif delta > 0:
        classification = "two_stage_conditional_repair_partial_not_promoted"
    else:
        classification = "two_stage_conditional_repair_rejected"
    return {
        "schema": "two_stage_conditional_repair_audit.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "conditional_repair_classifier_audit": rel(CONDITIONAL_REPAIR),
        },
        "scope": {
            "analysis_only": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "target_text_required": True,
            "stable_projection_oracle_used_for_pipeline_actions": False,
            "declared_literal_windows_granted": False,
            "source_free_digit_generator_emitted": False,
        },
        "summary": {
            "active_first_stage": ACTIVE_FIRST_STAGE,
            "active_exact_books": active["exact_book_count"],
            "pipeline_count": len(scores),
            "best_pipeline": best["label"],
            "best_second_stage": best["second_stage"],
            "best_exact_books": best["exact_book_count"],
            "exact_delta_vs_active": delta,
            "best_total_repairs_applied": best["total_repairs_applied"],
            "best_mismatch_books": best["mismatch_books"],
            "best_drift_class_counts": best["drift_class_counts"],
            "prequential_cells": len(preq),
            "prequential_selected_matches_oracle_cells": sum(
                1 for row in preq if row["selected_matches_oracle"]
            ),
            "prequential_stable": preq_stable,
            "promotes_two_stage_repair": promotes,
            "interpretation": (
                "Two-stage repair tests whether the gate18 prefix-stable repair "
                "can be followed by one more observable predicate-action rule. "
                "The second stage is scored end-to-end and selected by prefix/holdout."
            ),
        },
        "pipeline_scoreboard": [
            {
                "label": row["label"],
                "second_stage": row["second_stage"],
                "exact_book_count": row["exact_book_count"],
                "mismatch_book_count": row["mismatch_book_count"],
                "total_repairs_applied": row["total_repairs_applied"],
                "stage_counts": row["stage_counts"],
                "drift_class_counts": row["drift_class_counts"],
                "mismatch_books": row["mismatch_books"],
            }
            for row in sorted(
                scores,
                key=lambda item: (
                    -item["exact_book_count"],
                    item["total_repairs_applied"],
                    item["label"],
                ),
            )
        ],
        "best_mismatch_rows": best["mismatch_rows"],
        "prequential_rows": preq,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": classification,
            "source_length_dependency_status": "two_stage_conditional_repair_tested",
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
        "# Two-Stage Conditional Repair Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 19 keeps the gate-18 repair as the first stage and tests whether",
        "one additional observable predicate-action rule can close more of the",
        "remaining `10/60` drift books without using the stable projection as",
        "an oracle.",
        "",
        "## Pipeline Scoreboard",
        "",
        f"- Active first stage: `{s['active_first_stage']}`.",
        f"- Active exact books: `{s['active_exact_books']}/60`.",
        f"- Pipelines tested: `{s['pipeline_count']}`.",
        f"- Best pipeline: `{s['best_pipeline']}`.",
        f"- Best exact books: `{s['best_exact_books']}/60`.",
        f"- Exact delta vs active first stage: `{s['exact_delta_vs_active']}`.",
        "",
        "| Pipeline | Exact books | Repairs | Drift classes |",
        "|---|---:|---:|---|",
    ]
    for row in result["pipeline_scoreboard"][:16]:
        lines.append(
            f"| `{row['label']}` | `{row['exact_book_count']}/60` | "
            f"`{row['total_repairs_applied']}` | `{row['drift_class_counts']}` |"
        )
    lines.extend(
        [
            "",
            "## Prequential Selection",
            "",
            "| Cutoff | Selected | Train hits | Test hits | Oracle | Oracle test hits |",
            "|---:|---|---:|---:|---|---:|",
        ]
    )
    for row in result["prequential_rows"]:
        lines.append(
            f"| `{row['cutoff_book']}` | `{row['selected_pipeline']}` | "
            f"`{row['train_hits']}/{row['train_total']}` | "
            f"`{row['test_hits']}/{row['test_total']}` | "
            f"`{row['oracle_pipeline']}` | `{row['oracle_test_hits']}/{row['test_total']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Promotes two-stage repair: `{s['promotes_two_stage_repair']}`.",
            f"- Prequential selected matches oracle cells: `{s['prequential_selected_matches_oracle_cells']}/{s['prequential_cells']}`.",
            f"- {s['interpretation']}",
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
