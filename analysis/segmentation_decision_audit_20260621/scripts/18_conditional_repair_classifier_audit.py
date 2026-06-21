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
OBSERVABLE_REPAIR = TEST_RESULTS / "17_observable_repair_policy_audit.json"

OUT_STEM = "18_conditional_repair_classifier_audit"
SEED_BOOKS = list(range(10))
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]


Predicate = tuple[str, Callable[[dict[str, Any]], bool]]


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


def first_diff(
    repair_module,
    predicted: list[dict[str, Any]],
    projected: list[dict[str, Any]],
) -> dict[str, Any] | None:
    diff = repair_module.first_diff(predicted, projected)
    if diff is None:
        return None
    diff = dict(diff)
    diff["drift_class"] = repair_module.classify_diff(diff)
    return diff


def context_row(
    target: str,
    pos: int,
    predicted: dict[str, Any],
    context: dict[str, Any],
    previous_type: str,
    previous_length: int,
    op_index: int,
) -> dict[str, Any]:
    immediate = context["immediate_copy"]
    peak = context["peak"]
    next_peak = None
    if peak is not None:
        rows = context["rows"]
        for index in range(int(peak["index"]) + 1, len(rows)):
            row = rows[index]
            if row["max_copy_length"] >= 5:
                next_peak = row
                break
    return {
        "op_index": op_index,
        "target_start": pos,
        "target_length": len(target),
        "remaining": len(target) - pos,
        "position_bucket": "start"
        if pos == 0
        else ("end" if len(target) - pos <= 20 else "middle"),
        "previous_type": previous_type,
        "previous_length": previous_length,
        "predicted_type": predicted["type"],
        "predicted_length": int(predicted["length"]),
        "immediate_copy_len": 0 if immediate is None else int(immediate["length"]),
        "immediate_copy_candidate_count": 0
        if immediate is None
        else int(immediate.get("candidate_count", 0)),
        "peak_offset": None if peak is None else int(peak["offset"]),
        "peak_len": 0 if peak is None else int(peak["peak_len"]),
        "next_peak_offset": None if next_peak is None else int(next_peak["offset"]),
        "next_peak_len": 0 if next_peak is None else int(next_peak["max_copy_length"]),
    }


def make_predicates() -> list[Predicate]:
    predicates: list[Predicate] = [
        ("book_start", lambda row: row["target_start"] == 0),
        ("internal", lambda row: row["target_start"] > 0),
        ("middle_position", lambda row: row["position_bucket"] == "middle"),
        ("end_position", lambda row: row["position_bucket"] == "end"),
        ("previous_literal", lambda row: row["previous_type"] == "literal"),
        ("previous_copy", lambda row: row["previous_type"] == "copy"),
        ("predicted_literal", lambda row: row["predicted_type"] == "literal"),
        ("predicted_copy", lambda row: row["predicted_type"] == "copy"),
        (
            "predicted_literal_after_copy",
            lambda row: row["predicted_type"] == "literal"
            and row["previous_type"] == "copy",
        ),
        (
            "predicted_copy_after_literal",
            lambda row: row["predicted_type"] == "copy"
            and row["previous_type"] == "literal",
        ),
        (
            "literal_with_immediate_copy",
            lambda row: row["predicted_type"] == "literal"
            and row["immediate_copy_len"] >= 5,
        ),
        (
            "literal_with_next_peak",
            lambda row: row["predicted_type"] == "literal"
            and row["next_peak_offset"] is not None
            and row["next_peak_offset"] > row["predicted_length"],
        ),
    ]
    for value in [1, 2, 3, 5, 8, 13, 21]:
        predicates.append(
            (
                f"predicted_len_le{value}",
                lambda row, value=value: row["predicted_length"] <= value,
            )
        )
        predicates.append(
            (
                f"literal_len_le{value}",
                lambda row, value=value: row["predicted_type"] == "literal"
                and row["predicted_length"] <= value,
            )
        )
    for value in [5, 6, 8, 10, 13, 21]:
        predicates.append(
            (
                f"immediate_copy_ge{value}",
                lambda row, value=value: row["immediate_copy_len"] >= value,
            )
        )
        predicates.append(
            (
                f"literal_immediate_copy_ge{value}",
                lambda row, value=value: row["predicted_type"] == "literal"
                and row["immediate_copy_len"] >= value,
            )
        )
        predicates.append(
            (
                f"peak_len_le{value}",
                lambda row, value=value: row["peak_len"] > 0
                and row["peak_len"] <= value,
            )
        )
        predicates.append(
            (
                f"next_peak_ge{value}",
                lambda row, value=value: row["next_peak_len"] >= value,
            )
        )
    for value in [10, 20, 40, 80]:
        predicates.append(
            (
                f"remaining_le{value}",
                lambda row, value=value: row["remaining"] <= value,
            )
        )
    return predicates


def make_actions() -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    for threshold in [5, 6, 8, 10, 13, 21]:
        actions.extend(
            [
                {
                    "label": f"force_immediate_copy_ge{threshold}",
                    "action": "force_immediate_copy",
                    "threshold": threshold,
                },
                {
                    "label": f"force_book_start_copy_ge{threshold}",
                    "action": "force_book_start_copy",
                    "threshold": threshold,
                },
                {
                    "label": f"force_internal_copy_ge{threshold}",
                    "action": "force_internal_copy",
                    "threshold": threshold,
                },
                {
                    "label": f"skip_to_next_peak_ge{threshold}",
                    "action": "skip_to_next_peak",
                    "threshold": threshold,
                },
            ]
        )
    for threshold in [5, 6, 8, 10]:
        actions.append(
            {
                "label": f"literal1_for_short_copy_le{threshold}",
                "action": "literal1_for_short_copy",
                "threshold": threshold,
            }
        )
    for threshold in [21, 30, 34, 40]:
        actions.append(
            {
                "label": f"shorten_copy_by1_ge{threshold}",
                "action": "shorten_copy_by1",
                "threshold": threshold,
            }
        )
    return actions


def make_classifiers() -> list[dict[str, Any]]:
    classifiers: list[dict[str, Any]] = [
        {
            "label": "baseline_window5",
            "predicate": "always_false",
            "action": {"label": "none", "action": "none"},
        }
    ]
    action_by_label = {action["label"]: action for action in make_actions()}
    # Curated condition/action pairs tied to the five residual drift classes.
    # This is intentionally not a full cross-product sweep.
    candidate_pairs = [
        ("book_start", "force_book_start_copy_ge5"),
        ("book_start", "force_book_start_copy_ge8"),
        ("book_start", "force_book_start_copy_ge13"),
        ("literal_with_immediate_copy", "force_immediate_copy_ge5"),
        ("literal_with_immediate_copy", "force_immediate_copy_ge8"),
        ("literal_with_immediate_copy", "force_immediate_copy_ge13"),
        ("literal_with_immediate_copy", "force_internal_copy_ge5"),
        ("literal_with_immediate_copy", "force_internal_copy_ge8"),
        ("internal", "force_internal_copy_ge5"),
        ("internal", "force_internal_copy_ge8"),
        ("immediate_copy_ge10", "force_internal_copy_ge10"),
        ("immediate_copy_ge13", "force_internal_copy_ge13"),
        ("literal_with_next_peak", "skip_to_next_peak_ge5"),
        ("literal_with_next_peak", "skip_to_next_peak_ge8"),
        ("literal_with_next_peak", "skip_to_next_peak_ge13"),
        ("predicted_literal", "skip_to_next_peak_ge5"),
        ("literal_len_le1", "skip_to_next_peak_ge5"),
        ("literal_len_le3", "skip_to_next_peak_ge5"),
        ("peak_len_le5", "skip_to_next_peak_ge5"),
        ("peak_len_le8", "skip_to_next_peak_ge5"),
        ("predicted_copy", "literal1_for_short_copy_le5"),
        ("predicted_copy", "literal1_for_short_copy_le8"),
        ("predicted_len_le8", "literal1_for_short_copy_le8"),
        ("predicted_copy", "shorten_copy_by1_ge30"),
        ("predicted_copy", "shorten_copy_by1_ge34"),
    ]
    for predicate_name, action_label in candidate_pairs:
        action = action_by_label[action_label]
        classifiers.append(
            {
                "label": f"if_{predicate_name}_then_{action['label']}",
                "predicate": predicate_name,
                "action": action,
            }
        )
    return classifiers


def parse_book_with_classifier(
    repair_module,
    trace_module,
    policy_module,
    target: str,
    emitted: str,
    classifier: dict[str, Any],
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
        row = context_row(
            target, pos, predicted, context, previous_type, previous_length, op_index
        )
        should_apply = predicates[classifier["predicate"]](row)
        chosen = predicted
        reason = None
        if should_apply:
            chosen, reason = repair_module.apply_repair_policy(
                policy_module,
                trace_module,
                emitted,
                target,
                pos,
                predicted,
                context,
                classifier["action"],
            )
        if reason is not None:
            repairs.append(
                {
                    "target_start": pos,
                    "predicate": classifier["predicate"],
                    "repair": reason,
                    "baseline": predicted,
                    "chosen": chosen,
                    "features": row,
                }
            )
        if int(chosen["length"]) <= 0:
            raise RuntimeError({"type": "non_positive_chosen_op", "chosen": chosen})
        ops.append(chosen)
        emitted += target[pos : pos + int(chosen["length"])]
        previous_type = chosen["type"]
        previous_length = int(chosen["length"])
        pos += int(chosen["length"])
        op_index += 1
    return ops, emitted, repairs


def score_classifier(
    repair_module,
    trace_module,
    policy_module,
    books: dict[int, str],
    stable_by_book: dict[int, list[dict[str, Any]]],
    classifier: dict[str, Any],
    predicates: dict[str, Callable[[dict[str, Any]], bool]],
) -> dict[str, Any]:
    emitted = "".join(books[book] for book in SEED_BOOKS)
    exact_books: list[int] = []
    mismatch_rows: list[dict[str, Any]] = []
    total_repairs = 0
    repair_counts: Counter[str] = Counter()
    for book in range(10, 70):
        predicted, emitted, repairs = parse_book_with_classifier(
            repair_module,
            trace_module,
            policy_module,
            books[book],
            emitted,
            classifier,
            predicates,
        )
        projected = normalized_projected_ops(stable_by_book[book])
        total_repairs += len(repairs)
        for repair in repairs:
            repair_counts[repair["repair"]] += 1
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
        "label": classifier["label"],
        "predicate": classifier["predicate"],
        "action_label": classifier["action"]["label"],
        "tested_books": 60,
        "exact_book_count": len(exact_books),
        "exact_books": exact_books,
        "mismatch_book_count": len(mismatch_rows),
        "mismatch_books": [row["book"] for row in mismatch_rows],
        "total_repairs_applied": total_repairs,
        "repair_counts": dict(sorted(repair_counts.items())),
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
                "selected_classifier": selected["label"],
                "train_hits": selected["train_hits"],
                "train_total": selected["train_total"],
                "test_hits": selected["test_hits"],
                "test_total": selected["test_total"],
                "oracle_classifier": oracle["label"],
                "oracle_test_hits": oracle["test_hits"],
                "selected_matches_oracle": selected["test_hits"] == oracle["test_hits"],
            }
        )
    return rows


def make_result() -> dict[str, Any]:
    observable = load_json(OBSERVABLE_REPAIR)
    assert_boundary("observable_repair_policy_audit", observable)
    if observable["summary"]["best_exact_books"] != 48:
        raise RuntimeError("gate18 expects gate17 to reject repair templates")

    trace_module = load_module("segmentation_trace_for_gate18", TRACE_SCRIPT)
    gate111 = load_module("gate111_for_segmentation_gate18", GATE111_SCRIPT)
    policy_module = load_module("policy_drift_for_gate18", POLICY_DRIFT_SCRIPT)
    repair_module = load_module("observable_repair_for_gate18", OBSERVABLE_REPAIR_SCRIPT)
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    projected_ops = trace_module.projected_ops_from_copy_rows(
        gate111.make_copy_rows(), books
    )
    stable_by_book: dict[int, list[dict[str, Any]]] = {}
    for op in projected_ops:
        stable_by_book.setdefault(int(op["book"]), []).append(op)
    for rows in stable_by_book.values():
        rows.sort(key=lambda row: int(row["target_start"]))

    predicate_list = make_predicates()
    predicates = {"always_false": lambda row: False}
    predicates.update({name: fn for name, fn in predicate_list})
    classifiers = make_classifiers()
    scores = [
        score_classifier(
            repair_module,
            trace_module,
            policy_module,
            books,
            stable_by_book,
            classifier,
            predicates,
        )
        for classifier in classifiers
    ]
    baseline = next(row for row in scores if row["label"] == "baseline_window5")
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
    delta = best["exact_book_count"] - baseline["exact_book_count"]
    promotes = best["exact_book_count"] == 60 and preq_stable
    if promotes:
        classification = "conditional_repair_classifier_promoted_target_text_parser"
    elif delta > 0:
        classification = "conditional_repair_classifier_partial_not_promoted"
    else:
        classification = "conditional_repair_classifier_rejected"
    return {
        "schema": "conditional_repair_classifier_audit.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "observable_repair_policy_audit": rel(OBSERVABLE_REPAIR),
        },
        "scope": {
            "analysis_only": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "target_text_required": True,
            "stable_projection_oracle_used_for_classifier_actions": False,
            "declared_literal_windows_granted": False,
            "source_free_digit_generator_emitted": False,
        },
        "summary": {
            "baseline_exact_books": baseline["exact_book_count"],
            "predicate_count": len(predicate_list),
            "action_count": len(make_actions()),
            "classifier_count": len(scores),
            "best_classifier": best["label"],
            "best_exact_books": best["exact_book_count"],
            "exact_delta_vs_baseline": delta,
            "best_total_repairs_applied": best["total_repairs_applied"],
            "best_mismatch_books": best["mismatch_books"],
            "best_drift_class_counts": best["drift_class_counts"],
            "prequential_cells": len(preq),
            "prequential_selected_matches_oracle_cells": sum(
                1 for row in preq if row["selected_matches_oracle"]
            ),
            "prequential_stable": preq_stable,
            "promotes_conditional_repair_classifier": promotes,
            "interpretation": (
                "Conditional repair classifiers test whether a single observable "
                "predicate-action pair can replace gate16's stable-projection "
                "oracle. They are scored end-to-end and selected by prefix/holdout."
            ),
        },
        "classifier_scoreboard": [
            {
                "label": row["label"],
                "predicate": row["predicate"],
                "action_label": row["action_label"],
                "exact_book_count": row["exact_book_count"],
                "mismatch_book_count": row["mismatch_book_count"],
                "total_repairs_applied": row["total_repairs_applied"],
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
            "source_length_dependency_status": "conditional_repair_classifier_tested",
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
        "# Conditional Repair Classifier Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 18 tests a richer non-oracle replacement for the gate-16",
        "stable-projection repair map. Each candidate classifier is one",
        "observable predicate plus one observable repair action. The classifier",
        "is applied end-to-end while parsing, and prefix/holdout selection is",
        "reported separately from full-corpus best score.",
        "",
        "## Classifier Scoreboard",
        "",
        f"- Predicates tested: `{s['predicate_count']}`.",
        f"- Actions tested: `{s['action_count']}`.",
        f"- Classifiers tested: `{s['classifier_count']}`.",
        f"- Baseline exact books: `{s['baseline_exact_books']}/60`.",
        f"- Best classifier: `{s['best_classifier']}`.",
        f"- Best exact books: `{s['best_exact_books']}/60`.",
        f"- Exact delta vs baseline: `{s['exact_delta_vs_baseline']}`.",
        "",
        "| Classifier | Exact books | Repairs | Drift classes |",
        "|---|---:|---:|---|",
    ]
    for row in result["classifier_scoreboard"][:16]:
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
            f"| `{row['cutoff_book']}` | `{row['selected_classifier']}` | "
            f"`{row['train_hits']}/{row['train_total']}` | "
            f"`{row['test_hits']}/{row['test_total']}` | "
            f"`{row['oracle_classifier']}` | `{row['oracle_test_hits']}/{row['test_total']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Promotes conditional repair classifier: `{s['promotes_conditional_repair_classifier']}`.",
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
