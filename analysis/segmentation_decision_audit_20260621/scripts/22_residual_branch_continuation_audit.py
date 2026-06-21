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
RESIDUAL_FEATURE = TEST_RESULTS / "21_post_repair_residual_feature_audit.json"

OUT_STEM = "22_residual_branch_continuation_audit"
SEED_BOOKS = list(range(10))
ACTIVE_CLASSIFIER = "if_peak_len_le5_then_skip_to_next_peak_ge5"
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]


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


def op_key(op: dict[str, Any]) -> tuple[Any, ...]:
    return (op["type"], int(op["target_start"]), int(op["length"]), op.get("source"))


def op_equals(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return op_key(left) == op_key(right)


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


def first_diff(predicted: list[dict[str, Any]], stable: list[dict[str, Any]]) -> dict[str, Any] | None:
    if predicted == stable:
        return None
    for index, (left, right) in enumerate(zip(predicted, stable)):
        if left != right:
            return {
                "index": index,
                "predicted": left,
                "stable_projection": right,
            }
    index = min(len(predicted), len(stable))
    return {
        "index": index,
        "predicted": None if index >= len(predicted) else predicted[index],
        "stable_projection": None if index >= len(stable) else stable[index],
    }


def active_decision(
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
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    baseline, context = repair_module.baseline_op(
        policy_module, trace_module, emitted, target, pos
    )
    row = conditional_module.context_row(
        target, pos, baseline, context, previous_type, previous_length, op_index
    )
    if not predicates[classifier["predicate"]](row):
        return baseline, context, {"baseline": baseline, "repair": None, "features": row}
    chosen, reason = repair_module.apply_repair_policy(
        policy_module,
        trace_module,
        emitted,
        target,
        pos,
        baseline,
        context,
        classifier["action"],
    )
    return chosen, context, {"baseline": baseline, "repair": reason, "features": row}


def confirmed_peak_offsets(rows: list[dict[str, int]], max_offsets: int = 16) -> list[int]:
    offsets: list[int] = []
    for index, row in enumerate(rows):
        if row["max_copy_length"] < 5:
            continue
        value = row["max_copy_length"]
        if all(
            index + step >= len(rows)
            or rows[index + step]["max_copy_length"] <= value
            for step in range(1, 6)
        ):
            offsets.append(int(row["offset"]))
        if len(offsets) >= max_offsets:
            break
    return offsets


def valid_copy(emitted: str, target: str, op: dict[str, Any]) -> bool:
    source = op.get("source")
    length = int(op["length"])
    start = int(op["target_start"])
    if source is None or source < 0 or length < 5:
        return False
    if source + length > len(emitted) or start + length > len(target):
        return False
    return emitted[source : source + length] == target[start : start + length]


def add_candidate(
    candidates: dict[tuple[Any, ...], dict[str, Any]],
    op: dict[str, Any],
    label: str,
    observable: bool,
    emitted: str,
    target: str,
) -> None:
    length = int(op["length"])
    if length <= 0 or int(op["target_start"]) + length > len(target):
        return
    if op["type"] == "copy" and not valid_copy(emitted, target, op):
        return
    key = op_key(op)
    existing = candidates.get(key)
    if existing is None:
        candidates[key] = {"label": label, "observable": observable, "op": op}
    else:
        existing["label"] += f"+{label}"
        existing["observable"] = bool(existing["observable"] or observable)


def candidate_branches(
    emitted: str,
    target: str,
    pos: int,
    active_op: dict[str, Any],
    stable_op: dict[str, Any],
    context: dict[str, Any],
) -> list[dict[str, Any]]:
    candidates: dict[tuple[Any, ...], dict[str, Any]] = {}
    add_candidate(candidates, dict(active_op), "active_parser", True, emitted, target)

    remaining = len(target) - pos
    literal_lengths: set[int] = {1, remaining}
    if active_op["type"] == "literal":
        literal_lengths.add(int(active_op["length"]))
    for offset in confirmed_peak_offsets(context["rows"]):
        literal_lengths.add(offset)
    for offset in [row["offset"] for row in context["rows"] if row["max_copy_length"] >= 5][:8]:
        literal_lengths.add(int(offset))
    for length in sorted(literal_lengths):
        add_candidate(
            candidates,
            {"type": "literal", "target_start": pos, "length": length, "source": None},
            "observable_literal_stop",
            True,
            emitted,
            target,
        )

    immediate = context["immediate_copy"]
    if immediate is not None:
        max_len = int(immediate["length"])
        copy_lengths = {5, max_len}
        if max_len > 5:
            copy_lengths.add(max_len - 1)
        if max_len > 6:
            copy_lengths.add(max_len // 2)
        for length in sorted(copy_lengths):
            add_candidate(
                candidates,
                {
                    "type": "copy",
                    "target_start": pos,
                    "length": length,
                    "source": int(immediate["source"]),
                },
                "observable_immediate_copy",
                True,
                emitted,
                target,
            )

    add_candidate(candidates, dict(stable_op), "stable_projection_oracle", False, emitted, target)
    return list(candidates.values())


def parse_after_forced(
    repair_module,
    conditional_module,
    trace_module,
    policy_module,
    predicates: dict[str, Callable[[dict[str, Any]], bool]],
    classifier: dict[str, Any],
    target: str,
    emitted: str,
    forced_op: dict[str, Any],
) -> list[dict[str, Any]]:
    pos = int(forced_op["target_start"]) + int(forced_op["length"])
    emitted = emitted + target[int(forced_op["target_start"]) : pos]
    previous_type = forced_op["type"]
    previous_length = int(forced_op["length"])
    ops = [dict(forced_op)]
    op_index = 1
    while pos < len(target):
        chosen, _context, _meta = active_decision(
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
            op_index,
        )
        if int(chosen["length"]) <= 0:
            raise RuntimeError({"type": "non_positive_chosen_op", "chosen": chosen})
        ops.append(chosen)
        emitted += target[pos : pos + int(chosen["length"])]
        previous_type = chosen["type"]
        previous_length = int(chosen["length"])
        pos += int(chosen["length"])
        op_index += 1
    return ops


def branch_metrics(
    predicted_suffix: list[dict[str, Any]],
    stable_suffix: list[dict[str, Any]],
) -> dict[str, Any]:
    literal_digits = sum(
        int(op["length"]) for op in predicted_suffix if op["type"] == "literal"
    )
    copy_digits = sum(
        int(op["length"]) for op in predicted_suffix if op["type"] == "copy"
    )
    copy_count = sum(1 for op in predicted_suffix if op["type"] == "copy")
    diff = first_diff(predicted_suffix, stable_suffix)
    prefix_match = 0
    for left, right in zip(predicted_suffix, stable_suffix):
        if left != right:
            break
        prefix_match += 1
    return {
        "suffix_exact": diff is None,
        "stable_prefix_match_ops": prefix_match,
        "first_diff_index": None if diff is None else diff["index"],
        "suffix_op_count": len(predicted_suffix),
        "suffix_literal_digits": literal_digits,
        "suffix_copy_digits": copy_digits,
        "suffix_copy_count": copy_count,
    }


OBJECTIVES: dict[str, Callable[[dict[str, Any]], tuple[Any, ...]]] = {
    "min_suffix_ops": lambda row: (
        row["metrics"]["suffix_op_count"],
        row["metrics"]["suffix_literal_digits"],
        -row["metrics"]["suffix_copy_digits"],
        row["label"],
    ),
    "min_suffix_literals": lambda row: (
        row["metrics"]["suffix_literal_digits"],
        row["metrics"]["suffix_op_count"],
        -row["metrics"]["suffix_copy_digits"],
        row["label"],
    ),
    "max_suffix_copy_digits": lambda row: (
        -row["metrics"]["suffix_copy_digits"],
        row["metrics"]["suffix_op_count"],
        row["metrics"]["suffix_literal_digits"],
        row["label"],
    ),
    "max_suffix_copy_count": lambda row: (
        -row["metrics"]["suffix_copy_count"],
        row["metrics"]["suffix_op_count"],
        row["metrics"]["suffix_literal_digits"],
        row["label"],
    ),
    "balanced_ops_literals": lambda row: (
        row["metrics"]["suffix_op_count"] * 5
        + row["metrics"]["suffix_literal_digits"],
        -row["metrics"]["suffix_copy_digits"],
        row["label"],
    ),
    "oracle_max_stable_prefix": lambda row: (
        -row["metrics"]["stable_prefix_match_ops"],
        row["metrics"]["suffix_op_count"],
        row["label"],
    ),
}


def collect_decisions() -> dict[str, Any]:
    residual_feature = load_json(RESIDUAL_FEATURE)
    assert_boundary("post_repair_residual_feature_audit", residual_feature)
    if residual_feature["summary"]["active_exact_books"] != 50:
        raise RuntimeError("gate22 expects the gate21 active parser at 50/60")

    trace_module = load_module("segmentation_trace_for_gate22", TRACE_SCRIPT)
    gate111 = load_module("gate111_for_segmentation_gate22", GATE111_SCRIPT)
    policy_module = load_module("policy_drift_for_gate22", POLICY_DRIFT_SCRIPT)
    repair_module = load_module("observable_repair_for_gate22", OBSERVABLE_REPAIR_SCRIPT)
    conditional_module = load_module("conditional_repair_for_gate22", CONDITIONAL_REPAIR_SCRIPT)
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

    decisions: list[dict[str, Any]] = []
    emitted_prefix = "".join(books[book] for book in SEED_BOOKS)
    for book in range(10, 70):
        target = books[book]
        stable_ops = normalize_stable_ops(stable_by_book[book])
        emitted = emitted_prefix
        pos = 0
        previous_type = "BOS"
        previous_length = 0
        for stable_index, stable in enumerate(stable_ops):
            chosen, context, meta = active_decision(
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
            clean = op_equals(chosen, stable)
            row = {
                "book": book,
                "target_start": pos,
                "stable_index": stable_index,
                "kind": "clean_control" if clean else "residual_first_drift",
                "drift_class": None if clean else classify_diff(chosen, stable),
                "active_op": chosen,
                "stable_op": stable,
                "baseline_op": meta["baseline"],
                "active_repair": meta["repair"],
                "branches": [],
            }
            stable_suffix = stable_ops[stable_index:]
            for candidate in candidate_branches(
                emitted, target, pos, chosen, stable, context
            ):
                if not candidate["observable"]:
                    # Keep the stable oracle branch only as an availability marker;
                    # non-oracle objectives never select it.
                    if op_equals(candidate["op"], stable):
                        row["stable_candidate_observable"] = False
                    continue
                predicted_suffix = parse_after_forced(
                    repair_module,
                    conditional_module,
                    trace_module,
                    policy_module,
                    predicates,
                    classifier,
                    target,
                    emitted,
                    candidate["op"],
                )
                metrics = branch_metrics(predicted_suffix, stable_suffix)
                row["branches"].append(
                    {
                        "label": candidate["label"],
                        "op": candidate["op"],
                        "is_active": op_equals(candidate["op"], chosen),
                        "is_stable": op_equals(candidate["op"], stable),
                        "metrics": metrics,
                    }
                )
            row["stable_candidate_observable"] = any(
                branch["is_stable"] for branch in row["branches"]
            )
            decisions.append(row)
            if not clean:
                break
            emitted += target[pos : pos + int(chosen["length"])]
            previous_type = chosen["type"]
            previous_length = int(chosen["length"])
            pos += int(chosen["length"])
        emitted_prefix += target
    return {"decisions": decisions}


def choose_branch(decision: dict[str, Any], objective: str) -> dict[str, Any] | None:
    branches = decision["branches"]
    if not branches:
        return None
    return min(branches, key=OBJECTIVES[objective])


def score_objective(decisions: list[dict[str, Any]], objective: str) -> dict[str, Any]:
    rows = []
    for decision in decisions:
        chosen = choose_branch(decision, objective)
        if chosen is None:
            continue
        rows.append(
            {
                "book": decision["book"],
                "kind": decision["kind"],
                "chosen_is_stable": chosen["is_stable"],
                "chosen_is_active": chosen["is_active"],
                "chosen_label": chosen["label"],
                "chosen_op": chosen["op"],
            }
        )
    residual_rows = [row for row in rows if row["kind"] == "residual_first_drift"]
    clean_rows = [row for row in rows if row["kind"] == "clean_control"]
    residual_hits = sum(1 for row in residual_rows if row["chosen_is_stable"])
    clean_hits = sum(1 for row in clean_rows if row["chosen_is_stable"])
    clean_false_changes = sum(1 for row in clean_rows if not row["chosen_is_stable"])
    return {
        "objective": objective,
        "residual_hits": residual_hits,
        "residual_total": len(residual_rows),
        "clean_hits": clean_hits,
        "clean_total": len(clean_rows),
        "clean_false_changes": clean_false_changes,
        "total_hits": residual_hits + clean_hits,
        "total_total": len(rows),
        "selected_branch_counts": dict(
            sorted(Counter(row["chosen_label"] for row in rows).items())
        ),
        "residual_miss_books": [
            row["book"] for row in residual_rows if not row["chosen_is_stable"]
        ],
    }


def prequential_selection(decisions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    objective_names = [name for name in OBJECTIVES if not name.startswith("oracle_")]
    for cutoff in PREFIX_CUTOFFS:
        train = [row for row in decisions if row["book"] < cutoff]
        test = [row for row in decisions if row["book"] >= cutoff]
        train_scores = [score_objective(train, objective) for objective in objective_names]
        selected = max(
            train_scores,
            key=lambda row: (
                row["total_hits"],
                row["residual_hits"],
                -row["clean_false_changes"],
                row["objective"],
            ),
        )
        test_score = score_objective(test, selected["objective"])
        oracle_scores = [score_objective(test, objective) for objective in objective_names]
        oracle = max(
            oracle_scores,
            key=lambda row: (
                row["total_hits"],
                row["residual_hits"],
                -row["clean_false_changes"],
                row["objective"],
            ),
        )
        rows.append(
            {
                "cutoff_book": cutoff,
                "selected_objective": selected["objective"],
                "train_total_hits": selected["total_hits"],
                "train_total": selected["total_total"],
                "test_total_hits": test_score["total_hits"],
                "test_total": test_score["total_total"],
                "test_residual_hits": test_score["residual_hits"],
                "test_residual_total": test_score["residual_total"],
                "test_clean_false_changes": test_score["clean_false_changes"],
                "oracle_objective": oracle["objective"],
                "oracle_test_total_hits": oracle["total_hits"],
                "oracle_test_residual_hits": oracle["residual_hits"],
                "selected_matches_oracle_total_hits": (
                    test_score["total_hits"] == oracle["total_hits"]
                ),
            }
        )
    return rows


def public_decision_row(decision: dict[str, Any]) -> dict[str, Any]:
    branch_summaries = []
    for branch in sorted(
        decision["branches"],
        key=lambda row: (
            not row["is_stable"],
            not row["is_active"],
            row["op"]["type"],
            int(row["op"]["length"]),
            row["label"],
        ),
    )[:10]:
        branch_summaries.append(
            {
                "label": branch["label"],
                "op": branch["op"],
                "is_active": branch["is_active"],
                "is_stable": branch["is_stable"],
                "suffix_exact": branch["metrics"]["suffix_exact"],
                "stable_prefix_match_ops": branch["metrics"]["stable_prefix_match_ops"],
                "suffix_op_count": branch["metrics"]["suffix_op_count"],
                "suffix_literal_digits": branch["metrics"]["suffix_literal_digits"],
            }
        )
    return {
        "book": decision["book"],
        "kind": decision["kind"],
        "drift_class": decision["drift_class"],
        "target_start": decision["target_start"],
        "active_op": decision["active_op"],
        "stable_op": decision["stable_op"],
        "stable_candidate_observable": decision["stable_candidate_observable"],
        "branch_count": len(decision["branches"]),
        "branches": branch_summaries,
    }


def make_result() -> dict[str, Any]:
    collected = collect_decisions()
    decisions = collected["decisions"]
    residual_decisions = [
        row for row in decisions if row["kind"] == "residual_first_drift"
    ]
    clean_decisions = [row for row in decisions if row["kind"] == "clean_control"]
    objective_scores = [
        score_objective(decisions, objective) for objective in OBJECTIVES
    ]
    objective_scores.sort(
        key=lambda row: (
            -row["total_hits"],
            -row["residual_hits"],
            row["clean_false_changes"],
            row["objective"],
        )
    )
    non_oracle_scores = [
        row for row in objective_scores if not row["objective"].startswith("oracle_")
    ]
    best_non_oracle = non_oracle_scores[0]
    oracle_score = next(
        row for row in objective_scores if row["objective"] == "oracle_max_stable_prefix"
    )
    preq = prequential_selection(decisions)
    residual_available = sum(
        1 for row in residual_decisions if row["stable_candidate_observable"]
    )
    clean_available = sum(
        1 for row in clean_decisions if row["stable_candidate_observable"]
    )
    promotes = (
        best_non_oracle["residual_hits"] == len(residual_decisions)
        and best_non_oracle["clean_false_changes"] == 0
        and all(row["test_clean_false_changes"] == 0 for row in preq)
        and all(row["test_residual_hits"] == row["test_residual_total"] for row in preq)
    )
    classification = (
        "residual_branch_continuation_rule_promoted"
        if promotes
        else "residual_branch_continuation_objectives_rejected"
    )
    return {
        "schema": "residual_branch_continuation_audit.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "post_repair_residual_feature_audit": rel(RESIDUAL_FEATURE),
        },
        "scope": {
            "analysis_only": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "target_text_required": True,
            "stable_projection_used_as_label_only": True,
            "declared_literal_windows_granted": False,
            "source_free_digit_generator_emitted": False,
            "promotes_parser_rule": promotes,
        },
        "summary": {
            "active_classifier": ACTIVE_CLASSIFIER,
            "residual_decision_count": len(residual_decisions),
            "clean_control_count": len(clean_decisions),
            "residual_stable_observable_candidates": residual_available,
            "clean_stable_observable_candidates": clean_available,
            "objective_count": len(OBJECTIVES),
            "best_non_oracle_objective": best_non_oracle["objective"],
            "best_non_oracle_residual_hits": best_non_oracle["residual_hits"],
            "best_non_oracle_clean_false_changes": best_non_oracle[
                "clean_false_changes"
            ],
            "oracle_residual_hits": oracle_score["residual_hits"],
            "oracle_clean_false_changes": oracle_score["clean_false_changes"],
            "prequential_cells": len(preq),
            "prequential_zero_clean_false_change_cells": sum(
                1 for row in preq if row["test_clean_false_changes"] == 0
            ),
            "prequential_cover_all_test_residual_cells": sum(
                1
                for row in preq
                if row["test_residual_hits"] == row["test_residual_total"]
            ),
            "prequential_selected_matches_oracle_cells": sum(
                1 for row in preq if row["selected_matches_oracle_total_hits"]
            ),
            "promotes_branch_continuation_rule": promotes,
            "interpretation": (
                "Gate 22 tests whether residual choices become mechanical when "
                "candidate first operations are scored by their active-parser "
                "continuation. Stable projection is used only as the scoring "
                "label; non-oracle objectives may select only observable branches."
            ),
        },
        "objective_scoreboard": objective_scores,
        "prequential_rows": preq,
        "residual_decision_rows": [
            public_decision_row(row) for row in residual_decisions
        ],
        "clean_control_sample_rows": [
            public_decision_row(row) for row in clean_decisions[:20]
        ],
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": classification,
            "source_length_dependency_status": "branch_continuation_objectives_rejected"
            if not promotes
            else "branch_continuation_rule_promoted",
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
        "# Residual Branch Continuation Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 22 tests the next path-state hypothesis after simple feature",
        "flags failed: perhaps the stable residual operation is selected by",
        "how the active parser continues after a forced first branch.",
        "Stable projection is used only as the evaluation label; non-oracle",
        "objectives may choose only observable local branches.",
        "",
        "## Branch Availability",
        "",
        f"- Active classifier: `{s['active_classifier']}`.",
        f"- Residual decisions: `{s['residual_decision_count']}`.",
        f"- Clean controls: `{s['clean_control_count']}`.",
        f"- Residual stable operations available as observable candidates: `{s['residual_stable_observable_candidates']}/{s['residual_decision_count']}`.",
        f"- Clean stable operations available as observable candidates: `{s['clean_stable_observable_candidates']}/{s['clean_control_count']}`.",
        "",
        "## Objective Scoreboard",
        "",
        "| Objective | Residual hits | Clean false changes | Total hits |",
        "|---|---:|---:|---:|",
    ]
    for row in result["objective_scoreboard"]:
        lines.append(
            f"| `{row['objective']}` | `{row['residual_hits']}/{row['residual_total']}` | "
            f"`{row['clean_false_changes']}` | `{row['total_hits']}/{row['total_total']}` |"
        )
    lines.extend(
        [
            "",
            "## Prefix/Holdout",
            "",
            "| Cutoff | Selected objective | Test residual hits | Test clean false changes | Oracle objective |",
            "|---:|---|---:|---:|---|",
        ]
    )
    for row in result["prequential_rows"]:
        lines.append(
            f"| `{row['cutoff_book']}` | `{row['selected_objective']}` | "
            f"`{row['test_residual_hits']}/{row['test_residual_total']}` | "
            f"`{row['test_clean_false_changes']}` | `{row['oracle_objective']}` |"
        )
    lines.extend(
        [
            "",
            "## Residual Branch Rows",
            "",
            "| Book | Class | Target | Stable candidate? | Branches |",
            "|---:|---|---:|---|---:|",
        ]
    )
    for row in result["residual_decision_rows"]:
        lines.append(
            f"| `{row['book']}` | `{row['drift_class']}` | `{row['target_start']}` | "
            f"`{row['stable_candidate_observable']}` | `{row['branch_count']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Promotes branch-continuation rule: `{s['promotes_branch_continuation_rule']}`.",
            f"- Best non-oracle objective: `{s['best_non_oracle_objective']}`.",
            f"- Best non-oracle residual hits: `{s['best_non_oracle_residual_hits']}/{s['residual_decision_count']}`.",
            f"- Best non-oracle clean false changes: `{s['best_non_oracle_clean_false_changes']}`.",
            f"- Oracle-prefix diagnostic residual hits: `{s['oracle_residual_hits']}/{s['residual_decision_count']}`.",
            f"- Prequential zero-clean-false-change cells: `{s['prequential_zero_clean_false_change_cells']}/{s['prequential_cells']}`.",
            f"- Prequential cover-all-test-residual cells: `{s['prequential_cover_all_test_residual_cells']}/{s['prequential_cells']}`.",
            f"- {s['interpretation']}",
            "- Observable continuation objectives do not recover the residual stable choices without damaging clean controls.",
            "- The remaining blocker is not just first-branch consequence under these simple path metrics.",
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
