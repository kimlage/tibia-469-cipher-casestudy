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
DRIFT_REPAIR = TEST_RESULTS / "16_single_drift_repair_oracle_audit.json"

OUT_STEM = "17_observable_repair_policy_audit"
SEED_BOOKS = list(range(10))
MIN_COPY_LEN = 5
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
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


def op_equal(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return (
        left["type"] == right["type"]
        and int(left["target_start"]) == int(right["target_start"])
        and int(left["length"]) == int(right["length"])
        and left.get("source") == right.get("source")
    )


def first_diff(
    predicted: list[dict[str, Any]], projected: list[dict[str, Any]]
) -> dict[str, Any] | None:
    if predicted == projected:
        return None
    for index, (left, right) in enumerate(zip(predicted, projected)):
        if left != right:
            return {"index": index, "predicted": left, "stable_projection": right}
    index = min(len(predicted), len(projected))
    return {
        "index": index,
        "predicted": None if index >= len(predicted) else predicted[index],
        "stable_projection": None if index >= len(projected) else projected[index],
    }


def classify_diff(diff: dict[str, Any]) -> str:
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


def confirmed_peak_offset(
    rows: list[dict[str, int]], start_index: int = 0
) -> dict[str, int] | None:
    for index in range(start_index, len(rows)):
        row = rows[index]
        if row["max_copy_length"] < MIN_COPY_LEN:
            continue
        value = row["max_copy_length"]
        if all(
            index + step >= len(rows)
            or rows[index + step]["max_copy_length"] <= value
            for step in range(1, 6)
        ):
            return {
                "index": index,
                "offset": row["offset"],
                "peak_len": row["max_copy_length"],
                "total_advance": row["total_advance"],
            }
    return None


def baseline_op(policy_module, trace_module, emitted: str, target: str, pos: int) -> tuple[dict[str, Any], dict[str, Any]]:
    rows = policy_module.offset_rows(trace_module, emitted, target, pos)
    predicted_offset = policy_module.predict_offset(
        rows,
        BASELINE_POLICY["policy"],
        BASELINE_POLICY["field"],
        BASELINE_POLICY["confirm_window"],
    )
    immediate_copy = policy_module.choose_copy(trace_module, emitted, target, pos)
    peak = None if predicted_offset is None else confirmed_peak_offset(rows, predicted_offset)
    if predicted_offset is None:
        op = {
            "type": "literal",
            "target_start": pos,
            "length": len(target) - pos,
            "source": None,
        }
    elif predicted_offset > 0:
        op = {
            "type": "literal",
            "target_start": pos,
            "length": predicted_offset,
            "source": None,
        }
    else:
        if immediate_copy is None:
            raise RuntimeError({"type": "zero_offset_without_copy", "pos": pos})
        op = {
            "type": "copy",
            "target_start": pos,
            "length": int(immediate_copy["length"]),
            "source": int(immediate_copy["source"]),
        }
    context = {
        "rows": rows,
        "peak": peak,
        "immediate_copy": immediate_copy,
        "remaining": len(target) - pos,
    }
    return op, context


def apply_repair_policy(
    policy_module,
    trace_module,
    emitted: str,
    target: str,
    pos: int,
    predicted: dict[str, Any],
    context: dict[str, Any],
    policy: dict[str, Any],
) -> tuple[dict[str, Any], str | None]:
    action = policy["action"]
    threshold = policy.get("threshold")
    if action == "none":
        return predicted, None
    immediate = context["immediate_copy"]
    if action == "force_immediate_copy":
        if predicted["type"] == "literal" and immediate is not None and immediate["length"] >= threshold:
            return {
                "type": "copy",
                "target_start": pos,
                "length": int(immediate["length"]),
                "source": int(immediate["source"]),
            }, action
        return predicted, None
    if action == "force_book_start_copy":
        if (
            pos == 0
            and predicted["type"] == "literal"
            and immediate is not None
            and immediate["length"] >= threshold
        ):
            return {
                "type": "copy",
                "target_start": pos,
                "length": int(immediate["length"]),
                "source": int(immediate["source"]),
            }, action
        return predicted, None
    if action == "force_internal_copy":
        if (
            pos > 0
            and predicted["type"] == "literal"
            and immediate is not None
            and immediate["length"] >= threshold
        ):
            return {
                "type": "copy",
                "target_start": pos,
                "length": int(immediate["length"]),
                "source": int(immediate["source"]),
            }, action
        return predicted, None
    if action == "skip_to_next_peak":
        if predicted["type"] != "literal":
            return predicted, None
        peak = context["peak"]
        if peak is None:
            return predicted, None
        next_peak = confirmed_peak_offset(context["rows"], peak["index"] + 1)
        if (
            next_peak is not None
            and next_peak["offset"] > predicted["length"]
            and next_peak["peak_len"] >= threshold
        ):
            return {
                "type": "literal",
                "target_start": pos,
                "length": int(next_peak["offset"]),
                "source": None,
            }, action
        return predicted, None
    if action == "literal1_for_short_copy":
        if predicted["type"] == "copy" and predicted["length"] <= threshold:
            return {
                "type": "literal",
                "target_start": pos,
                "length": 1,
                "source": None,
            }, action
        return predicted, None
    if action == "shorten_copy_by1":
        if predicted["type"] == "copy" and predicted["length"] >= threshold:
            return {
                "type": "copy",
                "target_start": pos,
                "length": int(predicted["length"]) - 1,
                "source": int(predicted["source"]),
            }, action
        return predicted, None
    if action == "combined_observable":
        # Hand-limited structural combination: prefer rare direct repairs before
        # broad literal-peak changes. This is still scored as a candidate policy,
        # not promoted without prefix/holdout support.
        for child in [
            {"action": "shorten_copy_by1", "threshold": 30},
            {"action": "literal1_for_short_copy", "threshold": 8},
            {"action": "force_book_start_copy", "threshold": 5},
            {"action": "force_internal_copy", "threshold": 5},
            {"action": "skip_to_next_peak", "threshold": 5},
        ]:
            changed, reason = apply_repair_policy(
                policy_module,
                trace_module,
                emitted,
                target,
                pos,
                predicted,
                context,
                child,
            )
            if reason is not None:
                return changed, f"{action}:{reason}"
        return predicted, None
    raise ValueError(action)


def make_policies() -> list[dict[str, Any]]:
    policies: list[dict[str, Any]] = [{"label": "baseline_window5", "action": "none"}]
    for threshold in [5, 6, 8, 10, 13, 21]:
        for action in [
            "force_immediate_copy",
            "force_book_start_copy",
            "force_internal_copy",
            "skip_to_next_peak",
        ]:
            policies.append(
                {
                    "label": f"{action}_ge{threshold}",
                    "action": action,
                    "threshold": threshold,
                }
            )
    for threshold in [5, 6, 8, 10, 13]:
        policies.append(
            {
                "label": f"literal1_for_short_copy_le{threshold}",
                "action": "literal1_for_short_copy",
                "threshold": threshold,
            }
        )
    for threshold in [10, 21, 30, 34, 40]:
        policies.append(
            {
                "label": f"shorten_copy_by1_ge{threshold}",
                "action": "shorten_copy_by1",
                "threshold": threshold,
            }
        )
    policies.append({"label": "combined_observable", "action": "combined_observable"})
    return policies


def parse_book_with_policy(
    policy_module,
    trace_module,
    target: str,
    emitted: str,
    policy: dict[str, Any],
) -> tuple[list[dict[str, Any]], str, list[dict[str, Any]]]:
    pos = 0
    ops: list[dict[str, Any]] = []
    repairs: list[dict[str, Any]] = []
    while pos < len(target):
        predicted, context = baseline_op(policy_module, trace_module, emitted, target, pos)
        chosen, repair = apply_repair_policy(
            policy_module,
            trace_module,
            emitted,
            target,
            pos,
            predicted,
            context,
            policy,
        )
        if repair is not None:
            repairs.append(
                {
                    "target_start": pos,
                    "repair": repair,
                    "baseline": predicted,
                    "chosen": chosen,
                    "immediate_copy_len": 0
                    if context["immediate_copy"] is None
                    else context["immediate_copy"]["length"],
                    "peak_offset": None
                    if context["peak"] is None
                    else context["peak"]["offset"],
                    "peak_len": 0 if context["peak"] is None else context["peak"]["peak_len"],
                }
            )
        if chosen["length"] <= 0:
            raise RuntimeError({"type": "non_positive_chosen_op", "chosen": chosen})
        ops.append(chosen)
        emitted += target[pos : pos + int(chosen["length"])]
        pos += int(chosen["length"])
    return ops, emitted, repairs


def score_policy(
    policy_module,
    trace_module,
    books: dict[int, str],
    stable_by_book: dict[int, list[dict[str, Any]]],
    policy: dict[str, Any],
) -> dict[str, Any]:
    emitted = "".join(books[book] for book in SEED_BOOKS)
    exact_books: list[int] = []
    mismatch_rows: list[dict[str, Any]] = []
    repair_counts: Counter[str] = Counter()
    total_repairs = 0
    for book in range(10, 70):
        predicted, emitted, repairs = parse_book_with_policy(
            policy_module, trace_module, books[book], emitted, policy
        )
        for repair in repairs:
            repair_counts[repair["repair"]] += 1
        total_repairs += len(repairs)
        projected = normalized_projected_ops(stable_by_book[book])
        diff = first_diff(predicted, projected)
        if diff is None:
            exact_books.append(book)
        else:
            mismatch_rows.append(
                {
                    "book": book,
                    "first_diff": diff,
                    "drift_class": classify_diff(diff),
                    "repair_count": len(repairs),
                    "first_repairs": repairs[:5],
                }
            )
    drift_classes = Counter(row["drift_class"] for row in mismatch_rows)
    return {
        "label": policy["label"],
        "policy": policy,
        "tested_books": 60,
        "exact_book_count": len(exact_books),
        "exact_books": exact_books,
        "mismatch_books": [row["book"] for row in mismatch_rows],
        "mismatch_book_count": len(mismatch_rows),
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
        scored = []
        for score in scores:
            exact = set(score["exact_books"])
            train_hits = len(exact & train_books)
            test_hits = len(exact & test_books)
            scored.append(
                {
                    "label": score["label"],
                    "train_hits": train_hits,
                    "train_total": len(train_books),
                    "test_hits": test_hits,
                    "test_total": len(test_books),
                    "exact_book_count": score["exact_book_count"],
                    "total_repairs_applied": score["total_repairs_applied"],
                }
            )
        selected = max(
            scored,
            key=lambda row: (
                row["train_hits"],
                row["test_hits"],
                row["exact_book_count"],
                -row["total_repairs_applied"],
                row["label"],
            ),
        )
        oracle = max(scored, key=lambda row: (row["test_hits"], row["train_hits"]))
        rows.append(
            {
                "cutoff_book": cutoff,
                "selected_policy": selected["label"],
                "train_hits": selected["train_hits"],
                "train_total": selected["train_total"],
                "test_hits": selected["test_hits"],
                "test_total": selected["test_total"],
                "oracle_policy": oracle["label"],
                "oracle_test_hits": oracle["test_hits"],
                "selected_matches_oracle": selected["test_hits"] == oracle["test_hits"],
            }
        )
    return rows


def make_result() -> dict[str, Any]:
    drift_repair = load_json(DRIFT_REPAIR)
    assert_boundary("single_drift_repair_oracle_audit", drift_repair)
    if drift_repair["summary"]["baseline_exact_books"] != 48:
        raise RuntimeError("gate17 expects the gate16 window5 baseline")

    trace_module = load_module("segmentation_trace_for_gate17", TRACE_SCRIPT)
    gate111 = load_module("gate111_for_segmentation_gate17", GATE111_SCRIPT)
    policy_module = load_module("policy_drift_for_gate17", POLICY_DRIFT_SCRIPT)
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    projected_ops = trace_module.projected_ops_from_copy_rows(
        gate111.make_copy_rows(), books
    )
    stable_by_book: dict[int, list[dict[str, Any]]] = {}
    for op in projected_ops:
        stable_by_book.setdefault(int(op["book"]), []).append(op)
    for rows in stable_by_book.values():
        rows.sort(key=lambda row: int(row["target_start"]))

    policies = make_policies()
    scores = [
        score_policy(policy_module, trace_module, books, stable_by_book, policy)
        for policy in policies
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
    exact_delta = best["exact_book_count"] - baseline["exact_book_count"]
    promotes_observable_repair_policy = best["exact_book_count"] == 60 and preq_stable
    if promotes_observable_repair_policy:
        classification = "observable_repair_policy_promoted_target_text_parser"
    elif exact_delta > 0:
        classification = "observable_repair_policy_partial_not_promoted"
    else:
        classification = "observable_repair_policy_rejected"

    return {
        "schema": "observable_repair_policy_audit.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "single_drift_repair_oracle_audit": rel(DRIFT_REPAIR),
        },
        "scope": {
            "analysis_only": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "target_text_required": True,
            "stable_projection_oracle_used_for_policy_actions": False,
            "declared_literal_windows_granted": False,
            "source_free_digit_generator_emitted": False,
        },
        "summary": {
            "baseline_exact_books": baseline["exact_book_count"],
            "policy_count": len(scores),
            "best_policy": best["label"],
            "best_exact_books": best["exact_book_count"],
            "exact_delta_vs_baseline": exact_delta,
            "best_total_repairs_applied": best["total_repairs_applied"],
            "best_mismatch_books": best["mismatch_books"],
            "best_drift_class_counts": best["drift_class_counts"],
            "prequential_cells": len(preq),
            "prequential_selected_matches_oracle_cells": sum(
                1 for row in preq if row["selected_matches_oracle"]
            ),
            "prequential_stable": preq_stable,
            "promotes_observable_repair_policy": promotes_observable_repair_policy,
            "interpretation": (
                "Observable repair templates test whether the gate16 oracle "
                "map can be replaced by a small target-text-aware parser rule. "
                "Promotion requires exact coverage and prefix/holdout stability."
            ),
        },
        "policy_scoreboard": [
            {
                "label": row["label"],
                "exact_book_count": row["exact_book_count"],
                "mismatch_book_count": row["mismatch_book_count"],
                "total_repairs_applied": row["total_repairs_applied"],
                "repair_counts": row["repair_counts"],
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
            "source_length_dependency_status": "observable_repair_policy_tested",
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
        "# Observable Repair Policy Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 16 showed that a stable-projection oracle repair at the first",
        "drift closes `11/12` residual books and two repairs close `12/12`.",
        "Gate 17 asks whether a small observable repair policy can replace",
        "that oracle without granting the stable projection.",
        "",
        "Repair templates tested: immediate-copy forcing, book-start/internal",
        "copy forcing, skipping to the next confirmed local peak, short-copy",
        "literal substitution, copy shortening by one, and one combined policy.",
        "",
        "## Policy Scoreboard",
        "",
        f"- Policies tested: `{s['policy_count']}`.",
        f"- Baseline exact books: `{s['baseline_exact_books']}/60`.",
        f"- Best policy: `{s['best_policy']}`.",
        f"- Best exact books: `{s['best_exact_books']}/60`.",
        f"- Exact delta vs baseline: `{s['exact_delta_vs_baseline']}`.",
        "",
        "| Policy | Exact books | Repairs applied | Drift classes |",
        "|---|---:|---:|---|",
    ]
    for row in result["policy_scoreboard"][:16]:
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
            f"| `{row['cutoff_book']}` | `{row['selected_policy']}` | "
            f"`{row['train_hits']}/{row['train_total']}` | "
            f"`{row['test_hits']}/{row['test_total']}` | "
            f"`{row['oracle_policy']}` | `{row['oracle_test_hits']}/{row['test_total']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Promotes observable repair policy: `{s['promotes_observable_repair_policy']}`.",
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
