from __future__ import annotations

import importlib.util
import json
import random
from collections import Counter, defaultdict
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
BRANCH_CLOSURE = TEST_RESULTS / "36_branch_choice_frontier_closure_audit.json"

OUT_STEM = "37_path_template_reuse_audit"
SEED_BOOKS = list(range(10))
ACTIVE_CLASSIFIER = "if_peak_len_le5_then_skip_to_next_peak_ge5"
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
RANDOM_TRIALS = 400


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


def bucket(value: int | None, cuts: list[int]) -> str:
    if value is None:
        return "none"
    for cut in cuts:
        if value <= cut:
            return f"le{cut}"
    return f"gt{cuts[-1]}"


def op_shape(op: dict[str, Any] | None) -> tuple[Any, ...]:
    if op is None:
        return ("none",)
    return (
        op["type"],
        int(op["length"]),
    )


def feature_key(features: dict[str, Any]) -> tuple[Any, ...]:
    peak_offset = features.get("peak_offset")
    next_peak_offset = features.get("next_peak_offset")
    gap_to_next_peak = (
        None
        if peak_offset is None or next_peak_offset is None
        else int(next_peak_offset) - int(peak_offset)
    )
    return (
        features["position_bucket"],
        features["previous_type"],
        bucket(int(features["previous_length"]), [1, 3, 5, 8, 13, 21, 34]),
        features["predicted_type"],
        bucket(int(features["predicted_length"]), [1, 3, 5, 8, 13, 21, 34]),
        bucket(int(features["immediate_copy_len"]), [0, 5, 8, 13, 21, 34, 55]),
        bucket(peak_offset, [0, 1, 3, 5, 8, 13, 21, 34]),
        bucket(int(features["peak_len"]), [0, 5, 8, 13, 21, 34, 55]),
        bucket(gap_to_next_peak, [0, 1, 3, 5, 8, 13, 21, 34]),
        bucket(int(features["next_peak_len"]), [0, 5, 8, 13, 21, 34, 55]),
    )


def stable_path_signature(
    stable_ops: list[dict[str, Any]], index: int, width: int
) -> tuple[tuple[Any, ...], ...]:
    return tuple(op_shape(op) for op in stable_ops[index : index + width])


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
    stable: list[dict[str, Any]],
) -> dict[str, Any] | None:
    diff = repair_module.first_diff(predicted, stable)
    if diff is None:
        return None
    diff = dict(diff)
    diff["drift_class"] = repair_module.classify_diff(diff)
    return diff


def stable_by_book(trace_module, gate111, books: dict[int, str]) -> dict[int, list[dict[str, Any]]]:
    projected_ops = trace_module.projected_ops_from_copy_rows(
        gate111.make_copy_rows(), books
    )
    by_book: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for op in projected_ops:
        by_book[int(op["book"])].append(op)
    for rows in by_book.values():
        rows.sort(key=lambda row: int(row["target_start"]))
    return {book: normalized_projected_ops(rows) for book, rows in by_book.items()}


def parse_active_books(
    repair_module,
    conditional_module,
    trace_module,
    policy_module,
    books: dict[int, str],
    stable: dict[int, list[dict[str, Any]]],
    classifier: dict[str, Any],
    predicates: dict[str, Callable[[dict[str, Any]], bool]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    emitted = "".join(books[book] for book in SEED_BOOKS)
    all_decisions: list[dict[str, Any]] = []
    book_rows: list[dict[str, Any]] = []
    for book in range(10, 70):
        target = books[book]
        pos = 0
        op_index = 0
        previous_type = "BOS"
        previous_length = 0
        predicted_ops: list[dict[str, Any]] = []
        while pos < len(target):
            predicted, context = repair_module.baseline_op(
                policy_module, trace_module, emitted, target, pos
            )
            features = conditional_module.context_row(
                target,
                pos,
                predicted,
                context,
                previous_type,
                previous_length,
                op_index,
            )
            chosen = predicted
            repair_reason = None
            if predicates[classifier["predicate"]](features):
                chosen, repair_reason = repair_module.apply_repair_policy(
                    policy_module,
                    trace_module,
                    emitted,
                    target,
                    pos,
                    predicted,
                    context,
                    classifier["action"],
                )
            if int(chosen["length"]) <= 0:
                raise RuntimeError({"type": "non_positive_chosen_op", "chosen": chosen})
            stable_op = stable[book][op_index] if op_index < len(stable[book]) else None
            all_decisions.append(
                {
                    "book": book,
                    "op_index": op_index,
                    "target_start": pos,
                    "features": features,
                    "feature_key": feature_key(features),
                    "chosen": dict(chosen),
                    "stable_op": stable_op,
                    "repair_reason": repair_reason,
                }
            )
            predicted_ops.append(dict(chosen))
            emitted += target[pos : pos + int(chosen["length"])]
            previous_type = chosen["type"]
            previous_length = int(chosen["length"])
            pos += int(chosen["length"])
            op_index += 1
        diff = first_diff(repair_module, predicted_ops, stable[book])
        book_rows.append(
            {
                "book": book,
                "exact": diff is None,
                "predicted_op_count": len(predicted_ops),
                "stable_op_count": len(stable[book]),
                "first_diff": diff,
            }
        )
    return all_decisions, book_rows


def make_libraries(
    decisions: list[dict[str, Any]],
    book_rows: list[dict[str, Any]],
    stable: dict[int, list[dict[str, Any]]],
    train_books: set[int],
    width: int,
) -> dict[tuple[Any, ...], Counter[tuple[tuple[Any, ...], ...]]]:
    exact_books = {row["book"] for row in book_rows if row["exact"]}
    library: dict[tuple[Any, ...], Counter[tuple[tuple[Any, ...], ...]]] = defaultdict(Counter)
    for row in decisions:
        book = int(row["book"])
        index = int(row["op_index"])
        if book not in exact_books or book not in train_books:
            continue
        signature = stable_path_signature(stable[book], index, width)
        library[row["feature_key"]][signature] += 1
    return library


def deterministic_match(
    library: dict[tuple[Any, ...], Counter[tuple[tuple[Any, ...], ...]]],
    key: tuple[Any, ...],
    signature: tuple[tuple[Any, ...], ...],
) -> tuple[bool, bool, int]:
    counter = library.get(key)
    if not counter:
        return False, False, 0
    deterministic = len(counter) == 1
    return deterministic and next(iter(counter)) == signature, deterministic, sum(counter.values())


def residual_template_rows(
    decisions: list[dict[str, Any]],
    book_rows: list[dict[str, Any]],
    stable: dict[int, list[dict[str, Any]]],
    width: int,
) -> list[dict[str, Any]]:
    decision_by_book_index = {
        (int(row["book"]), int(row["op_index"])): row for row in decisions
    }
    rows: list[dict[str, Any]] = []
    for book_row in book_rows:
        if book_row["exact"]:
            continue
        diff = book_row["first_diff"]
        if diff is None:
            continue
        index = int(diff["index"])
        decision = decision_by_book_index.get((int(book_row["book"]), index))
        if decision is None:
            continue
        rows.append(
            {
                "book": int(book_row["book"]),
                "op_index": index,
                "drift_class": diff["drift_class"],
                "feature_key": decision["feature_key"],
                "active_shape": op_shape(diff["predicted"]),
                "stable_shape": op_shape(diff["stable_projection"]),
                "stable_path_signature": stable_path_signature(
                    stable[int(book_row["book"])], index, width
                ),
            }
        )
    return rows


def full_fit_rows(
    decisions: list[dict[str, Any]],
    book_rows: list[dict[str, Any]],
    stable: dict[int, list[dict[str, Any]]],
    width: int,
) -> dict[str, Any]:
    residuals = residual_template_rows(decisions, book_rows, stable, width)
    library = make_libraries(
        decisions,
        book_rows,
        stable,
        set(range(10, 70)),
        width,
    )
    covered = []
    deterministic = []
    for row in residuals:
        match, is_deterministic, support = deterministic_match(
            library, row["feature_key"], row["stable_path_signature"]
        )
        out = dict(row)
        out["template_support"] = support
        out["deterministic_key"] = is_deterministic
        out["deterministic_match"] = match
        covered.append(out)
        if match:
            deterministic.append(out)
    ambiguous_keys = sum(1 for counter in library.values() if len(counter) > 1)
    return {
        "width": width,
        "library_key_count": len(library),
        "library_template_count": sum(len(counter) for counter in library.values()),
        "ambiguous_key_count": ambiguous_keys,
        "residual_count": len(residuals),
        "deterministic_residual_matches": len(deterministic),
        "residual_rows": covered,
    }


def prequential_rows(
    decisions: list[dict[str, Any]],
    book_rows: list[dict[str, Any]],
    stable: dict[int, list[dict[str, Any]]],
    width: int,
) -> list[dict[str, Any]]:
    residuals = residual_template_rows(decisions, book_rows, stable, width)
    rows = []
    for cutoff in PREFIX_CUTOFFS:
        library = make_libraries(
            decisions,
            book_rows,
            stable,
            set(range(10, cutoff)),
            width,
        )
        test_residuals = [row for row in residuals if int(row["book"]) >= cutoff]
        matches = 0
        deterministic_keys = 0
        covered_keys = 0
        for row in test_residuals:
            match, is_deterministic, support = deterministic_match(
                library, row["feature_key"], row["stable_path_signature"]
            )
            if support:
                covered_keys += 1
            if is_deterministic:
                deterministic_keys += 1
            if match:
                matches += 1
        rows.append(
            {
                "cutoff_book": cutoff,
                "train_exact_books": sum(
                    1
                    for row in book_rows
                    if row["exact"] and 10 <= int(row["book"]) < cutoff
                ),
                "test_residuals": len(test_residuals),
                "covered_feature_keys": covered_keys,
                "deterministic_feature_keys": deterministic_keys,
                "deterministic_template_matches": matches,
            }
        )
    return rows


def shuffled_control(
    decisions: list[dict[str, Any]],
    book_rows: list[dict[str, Any]],
    stable: dict[int, list[dict[str, Any]]],
    width: int,
) -> dict[str, Any]:
    residuals = residual_template_rows(decisions, book_rows, stable, width)
    library = make_libraries(
        decisions,
        book_rows,
        stable,
        set(range(10, 70)),
        width,
    )
    rows = [
        {"key": key, "signature": signature}
        for key, counter in library.items()
        for signature, count in counter.items()
        for _ in range(count)
    ]
    rng = random.Random(46937 + width)
    hits: list[int] = []
    signatures = [row["signature"] for row in rows]
    keys = [row["key"] for row in rows]
    for _ in range(RANDOM_TRIALS):
        shuffled = list(signatures)
        rng.shuffle(shuffled)
        perm_library: dict[tuple[Any, ...], Counter[tuple[tuple[Any, ...], ...]]] = defaultdict(Counter)
        for key, signature in zip(keys, shuffled):
            perm_library[key][signature] += 1
        total = 0
        for row in residuals:
            match, _, _ = deterministic_match(
                perm_library, row["feature_key"], row["stable_path_signature"]
            )
            total += int(match)
        hits.append(total)
    observed = full_fit_rows(decisions, book_rows, stable, width)[
        "deterministic_residual_matches"
    ]
    return {
        "width": width,
        "trials": RANDOM_TRIALS,
        "observed": observed,
        "shuffle_min": min(hits),
        "shuffle_mean": sum(hits) / len(hits),
        "shuffle_max": max(hits),
        "shuffle_ge_observed_count": sum(1 for hit in hits if hit >= observed),
        "p_ge_observed": (
            sum(1 for hit in hits if hit >= observed) + 1
        )
        / (len(hits) + 1),
    }


def make_result() -> dict[str, Any]:
    closure = load_json(BRANCH_CLOSURE)
    assert_boundary("branch_choice_frontier_closure_audit", closure)
    if closure["classification"] != "branch_choice_frontier_closed_audit_only":
        raise RuntimeError("gate37 expects gate36 closure as its input boundary")

    trace_module = load_module("segmentation_trace_for_gate37", TRACE_SCRIPT)
    gate111 = load_module("gate111_for_gate37", GATE111_SCRIPT)
    policy_module = load_module("policy_drift_for_gate37", POLICY_DRIFT_SCRIPT)
    repair_module = load_module("observable_repair_for_gate37", OBSERVABLE_REPAIR_SCRIPT)
    conditional_module = load_module(
        "conditional_repair_for_gate37", CONDITIONAL_REPAIR_SCRIPT
    )
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    stable = stable_by_book(trace_module, gate111, books)
    predicates = {"always_false": lambda row: False}
    predicates.update({name: fn for name, fn in conditional_module.make_predicates()})
    classifier = next(
        item
        for item in conditional_module.make_classifiers()
        if item["label"] == ACTIVE_CLASSIFIER
    )
    decisions, book_rows = parse_active_books(
        repair_module,
        conditional_module,
        trace_module,
        policy_module,
        books,
        stable,
        classifier,
        predicates,
    )
    exact_books = [row["book"] for row in book_rows if row["exact"]]
    residual_books = [row["book"] for row in book_rows if not row["exact"]]
    full_fit = {str(width): full_fit_rows(decisions, book_rows, stable, width) for width in [1, 2, 3]}
    preq = {str(width): prequential_rows(decisions, book_rows, stable, width) for width in [1, 2, 3]}
    controls = {str(width): shuffled_control(decisions, book_rows, stable, width) for width in [1, 2, 3]}

    best_width = max(
        full_fit,
        key=lambda width: (
            full_fit[width]["deterministic_residual_matches"],
            -full_fit[width]["ambiguous_key_count"],
            -int(width),
        ),
    )
    best = full_fit[best_width]
    preq_match_cells = sum(
        1 for row in preq[best_width] if row["deterministic_template_matches"] > 0
    )
    promotes = (
        best["deterministic_residual_matches"] == best["residual_count"]
        and preq_match_cells == len(preq[best_width])
    )
    if promotes:
        classification = "path_template_reuse_parser_promoted"
    elif best["deterministic_residual_matches"] > 0:
        classification = "path_template_reuse_weak_clue_not_promoted"
    else:
        classification = "path_template_reuse_hypothesis_rejected"
    return {
        "schema": "path_template_reuse_audit.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "branch_choice_frontier_closure": rel(BRANCH_CLOSURE),
            "conditional_repair_classifier": rel(
                TEST_RESULTS / "18_conditional_repair_classifier_audit.json"
            ),
        },
        "scope": {
            "analysis_only": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "target_text_required": True,
            "source_free_digit_generator_emitted": False,
            "promotes_parser_rule": promotes,
            "tests_template_reuse_not_local_sweep": True,
        },
        "summary": {
            "active_classifier": ACTIVE_CLASSIFIER,
            "exact_book_count": len(exact_books),
            "residual_book_count": len(residual_books),
            "residual_books": residual_books,
            "decision_count": len(decisions),
            "widths_tested": [1, 2, 3],
            "best_width": int(best_width),
            "best_residual_count": best["residual_count"],
            "best_deterministic_residual_matches": best[
                "deterministic_residual_matches"
            ],
            "best_library_key_count": best["library_key_count"],
            "best_ambiguous_key_count": best["ambiguous_key_count"],
            "best_p_ge_observed": controls[best_width]["p_ge_observed"],
            "prequential_cells_with_residuals": sum(
                1 for row in preq[best_width] if row["test_residuals"] > 0
            ),
            "prequential_cells": len(preq[best_width]),
            "prequential_cells_with_match": preq_match_cells,
            "promotes_path_template_reuse": promotes,
            "interpretation": (
                "Path-template reuse tests whether the remaining first-drift "
                "corrections are explained by multi-operation stable templates "
                "seen in exact parser books under the same observable state key. "
                "It is structural because it tests reusable path shape, not a "
                "single branch-choice feature or a bit sweep."
            ),
        },
        "full_fit_by_width": full_fit,
        "prequential_by_width": preq,
        "shuffle_controls": controls,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": classification,
            "source_length_dependency_status": "template_reuse_tested",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def md_table(rows: list[list[Any]], headers: list[str]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines)


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / f"{OUT_STEM}.json"
    md_path = TEST_RESULTS / f"{OUT_STEM}.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    width_rows = []
    for width in ["1", "2", "3"]:
        f = result["full_fit_by_width"][width]
        c = result["shuffle_controls"][width]
        width_rows.append(
            [
                width,
                f["library_key_count"],
                f["ambiguous_key_count"],
                f["deterministic_residual_matches"],
                f["residual_count"],
                f"{c['shuffle_mean']:.3f}",
                f"{c['p_ge_observed']:.4f}",
            ]
        )
    preq_rows = []
    for row in result["prequential_by_width"][str(s["best_width"])]:
        preq_rows.append(
            [
                row["cutoff_book"],
                row["train_exact_books"],
                row["test_residuals"],
                row["covered_feature_keys"],
                row["deterministic_feature_keys"],
                row["deterministic_template_matches"],
            ]
        )
    residual_rows = [
        [
            row["book"],
            row["op_index"],
            row["drift_class"],
            row["template_support"],
            row["deterministic_key"],
            row["deterministic_match"],
            row["active_shape"],
            row["stable_shape"],
        ]
        for row in result["full_fit_by_width"][str(s["best_width"])]["residual_rows"]
    ]
    body = f"""# Path Template Reuse Audit

Classification: `{result['classification']}`
Translation delta: `NONE`

## Purpose

Gate 37 tests the next structural path/state hypothesis after branch-choice
weak signals were closed. It asks whether the remaining first-drift corrections
can be selected by reusing multi-operation stable templates already seen in
exact parser books under the same observable state key.

This is not a compression sweep and does not search row0 or plaintext.

## Summary

- Active classifier: `{s['active_classifier']}`.
- Exact parser books: `{s['exact_book_count']}`.
- Residual parser books: `{s['residual_book_count']}`.
- Widths tested: `{s['widths_tested']}`.
- Best template width: `{s['best_width']}`.
- Best deterministic residual matches:
  `{s['best_deterministic_residual_matches']}/{s['best_residual_count']}`.
- Best library keys: `{s['best_library_key_count']}`.
- Ambiguous keys at best width: `{s['best_ambiguous_key_count']}`.
- Prequential cells with residuals and at least one deterministic residual
  match:
  `{s['prequential_cells_with_match']}/{s['prequential_cells_with_residuals']}`.
- Shuffle control `p_ge_observed`: `{s['best_p_ge_observed']:.4f}`.
- Promotes parser rule: `{s['promotes_path_template_reuse']}`.

## Width Scoreboard

{md_table(width_rows, ["width", "library keys", "ambiguous keys", "deterministic residual matches", "residuals", "shuffle mean", "p_ge_observed"])}

## Prequential Rows For Best Width

{md_table(preq_rows, ["cutoff", "train exact books", "test residuals", "covered keys", "deterministic keys", "template matches"])}

## Residual Rows For Best Width

{md_table(residual_rows, ["book", "op", "drift class", "support", "deterministic key", "match", "active shape", "stable shape"])}

## Decision

Path-template reuse is not promoted. Under the tested observable state key and
exact source-free operation lengths, the exact-book template library does not
provide a deterministic reusable path template for the residual first-drift
corrections. This falsifies a simple "reuse a seen multi-op path shape"
explanation for the remaining branch decisions.

The next blocker remains a richer path/state mechanism or a source-free target
digit account.

- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
"""
    md_path.write_text(body, encoding="utf-8")
    print(json_path)
    print(md_path)


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
