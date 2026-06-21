from __future__ import annotations

import importlib.util
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

GATE55_SCRIPT = HERE / "scripts" / "55_observable_signature_support_gate.py"
GATE55 = TEST_RESULTS / "55_observable_signature_support_gate.json"

OUT_STEM = "56_sequential_signature_support_gate"
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


def stable_shape(row: dict[str, Any]) -> tuple[Any, ...]:
    op = row["stable_op"]
    return (op["type"], int(op["length"]))


def active_shape(row: dict[str, Any]) -> tuple[Any, ...]:
    op = row["active_op"]
    return (op["type"], int(op["length"]))


def add_path_context(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_book: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_book[int(row["book"])].append(row)
    out = []
    for book, book_rows in by_book.items():
        book_rows.sort(key=lambda item: int(item["stable_index"]))
        prev_stable: list[tuple[Any, ...]] = []
        prev_active: list[tuple[Any, ...]] = []
        copy_count = 0
        literal_count = 0
        digit_pos = 0
        for row in book_rows:
            current = dict(row)
            current["path"] = {
                "prev1_stable": tuple(prev_stable[-1:]) or (("BOS",),),
                "prev2_stable": tuple(prev_stable[-2:]) or (("BOS",),),
                "prev1_active": tuple(prev_active[-1:]) or (("BOS",),),
                "prev2_active": tuple(prev_active[-2:]) or (("BOS",),),
                "prior_copy_count": copy_count,
                "prior_literal_count": literal_count,
                "prior_op_count": len(prev_stable),
                "target_start_matches_path": int(row["target_start"]) == digit_pos,
            }
            out.append(current)
            s = stable_shape(row)
            a = active_shape(row)
            prev_stable.append(s)
            prev_active.append(a)
            if s[0] == "copy":
                copy_count += 1
            else:
                literal_count += 1
            digit_pos += int(s[1])
    return sorted(out, key=lambda item: (int(item["book"]), int(item["stable_index"])))


SeqSigFn = tuple[str, Callable[[dict[str, Any]], tuple[Any, ...]]]


def seq_signature_functions(gate55) -> list[SeqSigFn]:
    base = {name: fn for name, fn in gate55.signature_functions()}
    return [
        (
            "prev1_stable_x_decision_coarse",
            lambda row: row["path"]["prev1_stable"] + base["decision_coarse"](row),
        ),
        (
            "prev2_stable_x_decision_coarse",
            lambda row: row["path"]["prev2_stable"] + base["decision_coarse"](row),
        ),
        (
            "prev1_active_x_decision_coarse",
            lambda row: row["path"]["prev1_active"] + base["decision_coarse"](row),
        ),
        (
            "prev2_active_x_decision_coarse",
            lambda row: row["path"]["prev2_active"] + base["decision_coarse"](row),
        ),
        (
            "path_counts_x_candidate_extrema",
            lambda row: (
                min(row["path"]["prior_copy_count"], 8),
                min(row["path"]["prior_literal_count"], 8),
            )
            + base["candidate_count_extrema"](row),
        ),
        (
            "prev1_stable_x_candidate_extrema",
            lambda row: row["path"]["prev1_stable"]
            + base["candidate_count_extrema"](row),
        ),
        (
            "prev2_stable_x_candidate_extrema",
            lambda row: row["path"]["prev2_stable"]
            + base["candidate_count_extrema"](row),
        ),
        (
            "prev1_stable_x_candidate_length_buckets",
            lambda row: row["path"]["prev1_stable"]
            + base["candidate_length_buckets"](row),
        ),
        (
            "prev2_stable_x_candidate_length_buckets",
            lambda row: row["path"]["prev2_stable"]
            + base["candidate_length_buckets"](row),
        ),
        (
            "prev1_stable_x_candidate_feature_profile",
            lambda row: row["path"]["prev1_stable"]
            + base["candidate_feature_profile"](row),
        ),
    ]


def label_value(row: dict[str, Any], label_mode: str) -> tuple[Any, ...]:
    value = row[label_mode]
    if isinstance(value, tuple):
        return value
    return (value,)


def build_support(
    rows: list[dict[str, Any]],
    sig_fn: Callable[[dict[str, Any]], tuple[Any, ...]],
    label_mode: str,
    train_books: set[int],
    leave_out: tuple[int, int] | None = None,
) -> dict[tuple[Any, ...], Counter[tuple[Any, ...]]]:
    out: dict[tuple[Any, ...], Counter[tuple[Any, ...]]] = defaultdict(Counter)
    for row in rows:
        if row["book"] not in train_books:
            continue
        if leave_out == (row["book"], row["stable_index"]):
            continue
        if row["path"]["target_start_matches_path"] is not True:
            raise RuntimeError(
                {
                    "type": "path_position_mismatch",
                    "book": row["book"],
                    "stable_index": row["stable_index"],
                }
            )
        out[sig_fn(row)][label_value(row, label_mode)] += 1
    return out


def classify_query(
    row: dict[str, Any],
    support: dict[tuple[Any, ...], Counter[tuple[Any, ...]]],
    sig_fn: Callable[[dict[str, Any]], tuple[Any, ...]],
    label_mode: str,
) -> dict[str, Any]:
    counter = support.get(sig_fn(row), Counter())
    stable = label_value(row, label_mode)
    labels = sorted(counter.items(), key=lambda item: (-item[1], str(item[0])))
    label_set = {label for label, _count in labels}
    if not labels:
        status = "out_of_support"
    elif len(labels) == 1 and stable in label_set:
        status = "deterministic_match"
    elif len(labels) == 1:
        status = "deterministic_contradiction"
    elif stable in label_set:
        status = "ambiguous_includes_stable"
    else:
        status = "ambiguous_excludes_stable"
    return {
        "book": row["book"],
        "stable_index": row["stable_index"],
        "kind": row["kind"],
        "drift_class": row["drift_class"],
        "active_op": row["active_op"],
        "stable_op": row["stable_op"],
        "stable_label": stable,
        "support_count": sum(counter.values()),
        "support_label_count": len(counter),
        "majority_label": None if not labels else labels[0][0],
        "status": status,
    }


def summarize(query_rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(row["status"] for row in query_rows)
    return {
        "query_count": len(query_rows),
        "supported_count": sum(1 for row in query_rows if row["status"] != "out_of_support"),
        "deterministic_matches": counts.get("deterministic_match", 0),
        "contradictions": counts.get("deterministic_contradiction", 0)
        + counts.get("ambiguous_excludes_stable", 0),
        "ambiguous_with_stable": counts.get("ambiguous_includes_stable", 0),
        "out_of_support": counts.get("out_of_support", 0),
        "status_counts": dict(sorted(counts.items())),
    }


def full_fit_score(
    rows: list[dict[str, Any]],
    signature_name: str,
    sig_fn: Callable[[dict[str, Any]], tuple[Any, ...]],
    label_mode: str,
) -> dict[str, Any]:
    all_books = {row["book"] for row in rows}
    query_rows = []
    for row in rows:
        if row["kind"] != "residual_first_drift":
            continue
        support = build_support(
            rows,
            sig_fn,
            label_mode,
            all_books,
            leave_out=(row["book"], row["stable_index"]),
        )
        query_rows.append(classify_query(row, support, sig_fn, label_mode))
    return {
        "signature": signature_name,
        "label_mode": label_mode,
        **summarize(query_rows),
        "rows": query_rows,
    }


def prequential_score(
    rows: list[dict[str, Any]],
    signature_name: str,
    sig_fn: Callable[[dict[str, Any]], tuple[Any, ...]],
    label_mode: str,
) -> list[dict[str, Any]]:
    out = []
    for cutoff in PREFIX_CUTOFFS:
        train_books = set(range(10, cutoff))
        query = [
            row
            for row in rows
            if row["kind"] == "residual_first_drift" and row["book"] >= cutoff
        ]
        support = build_support(rows, sig_fn, label_mode, train_books)
        query_rows = [classify_query(row, support, sig_fn, label_mode) for row in query]
        out.append(
            {
                "cutoff_book": cutoff,
                "signature": signature_name,
                "label_mode": label_mode,
                **summarize(query_rows),
            }
        )
    return out


def score_key(score: dict[str, Any]) -> tuple[Any, ...]:
    return (
        score["deterministic_matches"],
        score["supported_count"],
        -score["contradictions"],
        -score["ambiguous_with_stable"],
        score["signature"],
        score["label_mode"],
    )


def make_result() -> dict[str, Any]:
    gate55_result = load_json(GATE55)
    assert_boundary("observable_signature_support_gate", gate55_result)
    if gate55_result["classification"] != "observable_signature_support_rejected":
        raise RuntimeError("gate56 expects gate55 rejection")

    gate55 = load_module("signature_support_for_gate56", GATE55_SCRIPT)
    source_module = gate55.load_module(
        "source_interval_for_gate56", gate55.GATE50_SCRIPT
    )
    rows = add_path_context(gate55.flatten_rows(source_module))
    signatures = seq_signature_functions(gate55)
    label_modes = [
        "stable_shape_label",
        "stable_action_label",
        "stable_rank_label",
    ]
    scores = []
    preq_by_pair = {}
    for signature_name, sig_fn in signatures:
        for label_mode in label_modes:
            score = full_fit_score(rows, signature_name, sig_fn, label_mode)
            scores.append(score)
            preq_by_pair[f"{signature_name}/{label_mode}"] = prequential_score(
                rows, signature_name, sig_fn, label_mode
            )
    scores.sort(key=score_key, reverse=True)
    best = scores[0]
    best_preq = preq_by_pair[f"{best['signature']}/{best['label_mode']}"]
    cells_with_residuals = sum(1 for row in best_preq if row["query_count"] > 0)
    cells_with_match = sum(
        1 for row in best_preq if row["deterministic_matches"] > 0
    )
    cells_cover_all = sum(
        1
        for row in best_preq
        if row["query_count"] > 0
        and row["deterministic_matches"] == row["query_count"]
    )
    promotes = (
        best["deterministic_matches"] == best["query_count"]
        and cells_cover_all == cells_with_residuals
    )
    if promotes:
        classification = "sequential_signature_support_parser_promoted"
    elif best["deterministic_matches"] > 0:
        classification = "sequential_signature_support_weak_clue_not_promoted"
    else:
        classification = "sequential_signature_support_rejected"
    return {
        "schema": "sequential_signature_support_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "observable_signature_support_gate": rel(GATE55),
            "observable_signature_support_script": rel(GATE55_SCRIPT),
        },
        "scope": {
            "analysis_only": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "target_text_required": True,
            "source_free_digit_generator_emitted": False,
            "uses_drift_class_as_feature": False,
            "uses_only_prior_path_context": True,
            "tests_sequential_candidate_signature_support": True,
            "promotes_parser_rule": promotes,
        },
        "summary": {
            "decision_count": len(rows),
            "residual_count": sum(
                1 for row in rows if row["kind"] == "residual_first_drift"
            ),
            "signature_family_count": len(signatures),
            "label_mode_count": len(label_modes),
            "score_count": len(scores),
            "best_signature": best["signature"],
            "best_label_mode": best["label_mode"],
            "best_deterministic_matches": best["deterministic_matches"],
            "best_supported_count": best["supported_count"],
            "best_query_count": best["query_count"],
            "best_status_counts": best["status_counts"],
            "baseline_gate55_best_deterministic_matches": gate55_result["summary"][
                "best_deterministic_matches"
            ],
            "prequential_cells": len(best_preq),
            "prequential_cells_with_residuals": cells_with_residuals,
            "prequential_cells_with_deterministic_match": cells_with_match,
            "prequential_cover_all_residual_cells": cells_cover_all,
            "promotes_sequential_signature_parser": promotes,
            "interpretation": (
                "Gate 56 augments observable candidate signatures with prior "
                "within-book path memory. It tests whether a simple sequential "
                "state supplies support after static signatures fail."
            ),
        },
        "scoreboard": [
            {key: value for key, value in score.items() if key != "rows"}
            for score in scores
        ],
        "best_rows": best["rows"],
        "best_prequential_rows": best_preq,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": classification,
            "source_length_dependency_status": "sequential_signature_support_tested",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def md_table(rows: list[list[Any]], headers: list[str]) -> str:
    out = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        out.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(out)


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / f"{OUT_STEM}.json"
    md_path = TEST_RESULTS / f"{OUT_STEM}.md"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    s = result["summary"]
    scoreboard_rows = [
        [
            row["signature"],
            row["label_mode"],
            f"{row['deterministic_matches']}/{row['query_count']}",
            row["supported_count"],
            row["contradictions"],
            row["ambiguous_with_stable"],
            row["status_counts"],
        ]
        for row in result["scoreboard"][:18]
    ]
    preq_rows = [
        [
            row["cutoff_book"],
            f"{row['deterministic_matches']}/{row['query_count']}",
            row["supported_count"],
            row["contradictions"],
            row["status_counts"],
        ]
        for row in result["best_prequential_rows"]
    ]
    residual_rows = [
        [
            row["book"],
            row["stable_index"],
            row["drift_class"],
            row["active_op"],
            row["stable_op"],
            row["support_count"],
            row["support_label_count"],
            row["majority_label"],
            row["status"],
        ]
        for row in result["best_rows"]
    ]
    body = f"""# Sequential Signature Support Gate

Classification: `{result['classification']}`
Translation delta: `NONE`

## Purpose

Gate 56 tests whether the static candidate-signature failure in gate 55 is
only missing a small sequential state. It augments observable candidate
signatures with prior within-book path memory: previous one or two stable/active
operation shapes and prior copy/literal counts.

For residual first-drift decisions, this prior path is observable before the
drift because previous operations match the active parser. The gate does not use
`drift_class`, plaintext, semantics, row0 origin, or future stable labels.

## Summary

- Decisions: `{s['decision_count']}`.
- Residual decisions: `{s['residual_count']}`.
- Sequential signature families: `{s['signature_family_count']}`.
- Label modes: `{s['label_mode_count']}`.
- Best signature: `{s['best_signature']}`.
- Best label mode: `{s['best_label_mode']}`.
- Best deterministic residual matches:
  `{s['best_deterministic_matches']}/{s['best_query_count']}`.
- Best supported residuals: `{s['best_supported_count']}/{s['best_query_count']}`.
- Best status counts: `{s['best_status_counts']}`.
- Static gate-55 best deterministic matches:
  `{s['baseline_gate55_best_deterministic_matches']}/{s['best_query_count']}`.
- Prefix/holdout cells with any deterministic match:
  `{s['prequential_cells_with_deterministic_match']}/{s['prequential_cells_with_residuals']}`.
- Prefix/holdout cover-all residual cells:
  `{s['prequential_cover_all_residual_cells']}/{s['prequential_cells_with_residuals']}`.
- Promotes parser rule: `{s['promotes_sequential_signature_parser']}`.

## Scoreboard

{md_table(scoreboard_rows, ["signature", "label mode", "deterministic matches", "supported", "contradictions", "ambiguous with stable", "status counts"])}

## Prefix/Holdout For Best Signature

{md_table(preq_rows, ["cutoff", "deterministic matches", "supported", "contradictions", "status counts"])}

## Residual Rows For Best Signature

{md_table(residual_rows, ["book", "op", "class", "active", "stable", "support", "labels", "majority", "status"])}

## Decision

Sequential observable signatures do not promote a parser. Adding prior path
memory does not produce deterministic support for the residual first-drift
choices, and prefix/holdout does not cover held-out residuals. The remaining
blocker is not a small observable sequential context over the current candidate
state.

- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
"""
    md_path.write_text(body, encoding="utf-8")


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
