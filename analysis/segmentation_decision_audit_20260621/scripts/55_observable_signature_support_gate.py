from __future__ import annotations

import importlib.util
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

GATE50_SCRIPT = HERE / "scripts" / "50_source_interval_context_gate.py"
GATE54 = TEST_RESULTS / "54_book_start_copy_subclass_gate.json"

OUT_STEM = "55_observable_signature_support_gate"
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
BIG = 10**9


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


def op_key(op: dict[str, Any]) -> tuple[Any, ...]:
    return (op["type"], int(op["target_start"]), int(op["length"]), op.get("source"))


def length_bucket(value: int) -> str:
    for cut in [1, 2, 3, 5, 8, 13, 21, 34, 55, 89]:
        if value <= cut:
            return f"le{cut}"
    return "gt89"


def count_bucket(value: int) -> str:
    for cut in [0, 1, 2, 3, 5, 8, 13, 21]:
        if value <= cut:
            return f"le{cut}"
    return "gt21"


def interval_bucket(value: int) -> str:
    if value >= BIG:
        return "none"
    for cut in [0, 1, 2, 3, 4, 6, 8, 13, 21]:
        if value <= cut:
            return f"le{cut}"
    return "gt21"


def payload_bucket(value: int) -> str:
    for cut in [0, 1, 2, 3, 5, 8, 13, 21]:
        if value <= cut:
            return f"le{cut}"
    return "gt21"


def copy_branch_rows(row: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        branch
        for branch in row["branches"]
        if branch["branch"]["op"]["type"] == "copy"
    ]


def literal_branch_rows(row: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        branch
        for branch in row["branches"]
        if branch["branch"]["op"]["type"] == "literal"
    ]


def candidate_stats(row: dict[str, Any]) -> dict[str, Any]:
    copies = copy_branch_rows(row)
    literals = literal_branch_rows(row)
    copy_lengths = [int(item["branch"]["op"]["length"]) for item in copies]
    literal_lengths = [int(item["branch"]["op"]["length"]) for item in literals]
    intervals = [
        int(item["features"]["source_target_interval_distance"])
        for item in copies
    ]
    payloads = [int(item["features"]["payload_occurrences"]) for item in copies]
    return {
        "branch_count": len(row["branches"]),
        "copy_count": len(copies),
        "literal_count": len(literals),
        "copy_lengths": sorted(copy_lengths),
        "literal_lengths": sorted(literal_lengths),
        "copy_length_buckets": tuple(sorted(length_bucket(value) for value in copy_lengths)),
        "literal_length_buckets": tuple(
            sorted(length_bucket(value) for value in literal_lengths)
        ),
        "max_copy_length": max(copy_lengths, default=0),
        "min_copy_interval": min(intervals, default=BIG),
        "max_copy_payload": max(payloads, default=0),
        "copy_feature_profile": tuple(
            sorted(
                (
                    length_bucket(int(item["branch"]["op"]["length"])),
                    payload_bucket(int(item["features"]["payload_occurrences"])),
                    interval_bucket(
                        int(item["features"]["source_target_interval_distance"])
                    ),
                )
                for item in copies
            )
        ),
        "copy_exact_feature_profile": tuple(
            sorted(
                (
                    int(item["branch"]["op"]["length"]),
                    payload_bucket(int(item["features"]["payload_occurrences"])),
                    interval_bucket(
                        int(item["features"]["source_target_interval_distance"])
                    ),
                )
                for item in copies
            )
        ),
    }


def flatten_rows(source_module) -> list[dict[str, Any]]:
    out = []
    for row in source_module.build_choice_rows():
        stats = candidate_stats(row)
        stable_op = row["stable_op"]
        active_op = row["active_op"]
        stable_branch_index = None
        for index, branch in enumerate(row["branches"]):
            if op_key(branch["branch"]["op"]) == op_key(stable_op):
                stable_branch_index = index
                break
        out.append(
            {
                "book": int(row["book"]),
                "target_start": int(row["target_start"]),
                "stable_index": int(row["stable_index"]),
                "kind": row["kind"],
                "drift_class": row["drift_class"],
                "active_op": active_op,
                "stable_op": stable_op,
                "stable_shape_label": (stable_op["type"], int(stable_op["length"])),
                "stable_action_label": (
                    "keep_active"
                    if op_key(active_op) == op_key(stable_op)
                    else f"change_to_{stable_op['type']}_{int(stable_op['length'])}"
                ),
                "stable_rank_label": (
                    "stable_branch_absent"
                    if stable_branch_index is None
                    else f"branch_index_{stable_branch_index}"
                ),
                "active_type": active_op["type"],
                "active_length": int(active_op["length"]),
                "stats": stats,
            }
        )
    return out


SignatureFn = tuple[str, Callable[[dict[str, Any]], tuple[Any, ...]]]


def signature_functions() -> list[SignatureFn]:
    return [
        (
            "decision_coarse",
            lambda row: (
                "start" if row["target_start"] == 0 else "internal",
                "first" if row["stable_index"] == 0 else "later",
                row["active_type"],
                length_bucket(row["active_length"]),
                count_bucket(row["stats"]["branch_count"]),
                count_bucket(row["stats"]["copy_count"]),
            ),
        ),
        (
            "candidate_count_extrema",
            lambda row: (
                "start" if row["target_start"] == 0 else "internal",
                "first" if row["stable_index"] == 0 else "later",
                row["active_type"],
                length_bucket(row["active_length"]),
                count_bucket(row["stats"]["branch_count"]),
                count_bucket(row["stats"]["copy_count"]),
                count_bucket(row["stats"]["literal_count"]),
                length_bucket(row["stats"]["max_copy_length"]),
                interval_bucket(row["stats"]["min_copy_interval"]),
                payload_bucket(row["stats"]["max_copy_payload"]),
            ),
        ),
        (
            "candidate_length_buckets",
            lambda row: (
                "start" if row["target_start"] == 0 else "internal",
                "first" if row["stable_index"] == 0 else "later",
                row["active_type"],
                length_bucket(row["active_length"]),
                row["stats"]["copy_length_buckets"],
                row["stats"]["literal_length_buckets"],
            ),
        ),
        (
            "candidate_feature_profile",
            lambda row: (
                "start" if row["target_start"] == 0 else "internal",
                "first" if row["stable_index"] == 0 else "later",
                row["active_type"],
                length_bucket(row["active_length"]),
                row["stats"]["copy_feature_profile"],
                row["stats"]["literal_length_buckets"],
            ),
        ),
        (
            "candidate_exact_length_profile",
            lambda row: (
                "start" if row["target_start"] == 0 else "internal",
                "first" if row["stable_index"] == 0 else "later",
                row["active_type"],
                row["active_length"],
                tuple(row["stats"]["copy_lengths"]),
                tuple(row["stats"]["literal_lengths"]),
            ),
        ),
        (
            "candidate_exact_feature_profile",
            lambda row: (
                "start" if row["target_start"] == 0 else "internal",
                "first" if row["stable_index"] == 0 else "later",
                row["active_type"],
                row["active_length"],
                row["stats"]["copy_exact_feature_profile"],
                tuple(row["stats"]["literal_lengths"]),
            ),
        ),
    ]


def label_value(row: dict[str, Any], label_mode: str) -> tuple[Any, ...]:
    value = row[label_mode]
    if isinstance(value, tuple):
        return value
    return (value,)


def build_support(
    rows: list[dict[str, Any]],
    signature_fn: Callable[[dict[str, Any]], tuple[Any, ...]],
    label_mode: str,
    train_books: set[int],
    leave_out: tuple[int, int] | None = None,
) -> dict[tuple[Any, ...], Counter[tuple[Any, ...]]]:
    support: dict[tuple[Any, ...], Counter[tuple[Any, ...]]] = defaultdict(Counter)
    for row in rows:
        if row["book"] not in train_books:
            continue
        if leave_out == (row["book"], row["stable_index"]):
            continue
        support[signature_fn(row)][label_value(row, label_mode)] += 1
    return support


def classify_query(
    row: dict[str, Any],
    support: dict[tuple[Any, ...], Counter[tuple[Any, ...]]],
    signature_fn: Callable[[dict[str, Any]], tuple[Any, ...]],
    label_mode: str,
) -> dict[str, Any]:
    signature = signature_fn(row)
    counter = support.get(signature, Counter())
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
    majority = labels[0][0] if labels else None
    return {
        "book": row["book"],
        "stable_index": row["stable_index"],
        "kind": row["kind"],
        "drift_class": row["drift_class"],
        "active_op": row["active_op"],
        "stable_op": row["stable_op"],
        "target_start": row["target_start"],
        "stable_label": stable,
        "support_count": sum(counter.values()),
        "support_label_count": len(counter),
        "majority_label": majority,
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
    signature_fn: Callable[[dict[str, Any]], tuple[Any, ...]],
    label_mode: str,
) -> dict[str, Any]:
    all_books = {row["book"] for row in rows}
    query_rows = []
    for row in rows:
        if row["kind"] != "residual_first_drift":
            continue
        support = build_support(
            rows,
            signature_fn,
            label_mode,
            all_books,
            leave_out=(row["book"], row["stable_index"]),
        )
        query_rows.append(classify_query(row, support, signature_fn, label_mode))
    summary = summarize(query_rows)
    return {
        "signature": signature_name,
        "label_mode": label_mode,
        **summary,
        "rows": query_rows,
    }


def prequential_score(
    rows: list[dict[str, Any]],
    signature_name: str,
    signature_fn: Callable[[dict[str, Any]], tuple[Any, ...]],
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
        support = build_support(rows, signature_fn, label_mode, train_books)
        query_rows = [
            classify_query(row, support, signature_fn, label_mode) for row in query
        ]
        summary = summarize(query_rows)
        out.append(
            {
                "cutoff_book": cutoff,
                "signature": signature_name,
                "label_mode": label_mode,
                **summary,
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
    gate54 = load_json(GATE54)
    assert_boundary("book_start_copy_subclass_gate", gate54)
    if gate54["classification"] != "book_start_copy_subclass_weak_clue_not_promoted":
        raise RuntimeError("gate55 expects gate54 weak-clue state")

    source_module = load_module("source_interval_for_gate55", GATE50_SCRIPT)
    rows = flatten_rows(source_module)
    signatures = signature_functions()
    label_modes = [
        "stable_shape_label",
        "stable_action_label",
        "stable_rank_label",
    ]
    scores = []
    preq_by_pair = {}
    for signature_name, signature_fn in signatures:
        for label_mode in label_modes:
            score = full_fit_score(rows, signature_name, signature_fn, label_mode)
            scores.append(score)
            preq_by_pair[f"{signature_name}/{label_mode}"] = prequential_score(
                rows, signature_name, signature_fn, label_mode
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
        classification = "observable_signature_support_parser_promoted"
    elif best["deterministic_matches"] > 0:
        classification = "observable_signature_support_weak_clue_not_promoted"
    else:
        classification = "observable_signature_support_rejected"
    return {
        "schema": "observable_signature_support_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "book_start_copy_subclass_gate": rel(GATE54),
            "source_interval_context_script": rel(GATE50_SCRIPT),
        },
        "scope": {
            "analysis_only": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "target_text_required": True,
            "source_free_digit_generator_emitted": False,
            "uses_drift_class_as_feature": False,
            "tests_observable_candidate_signature_support": True,
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
            "prequential_cells": len(best_preq),
            "prequential_cells_with_residuals": cells_with_residuals,
            "prequential_cells_with_deterministic_match": cells_with_match,
            "prequential_cover_all_residual_cells": cells_cover_all,
            "promotes_observable_signature_parser": promotes,
            "interpretation": (
                "Gate 55 tests whether observable decision/candidate signatures "
                "provide support for the residual stable labels. It is a support "
                "and collision audit, not another branch-ranking policy."
            ),
        },
        "scoreboard": [
            {
                key: value
                for key, value in score.items()
                if key != "rows"
            }
            for score in scores
        ],
        "best_rows": best["rows"],
        "best_prequential_rows": best_preq,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": classification,
            "source_length_dependency_status": "observable_signature_support_tested",
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
    body = f"""# Observable Signature Support Gate

Classification: `{result['classification']}`
Translation delta: `NONE`

## Purpose

Gate 55 asks whether the remaining residual `(source,length)` choices are
supported by repeated observable decision/candidate signatures. It does not
score a new branch policy. Instead, each residual first-drift decision is
queried against other decisions with the same observable signature. A signature
can promote only if it deterministically supports the needed stable label and
generalizes under prefix/holdout.

The signature families use book/start position, active operation shape, branch
counts, candidate length profiles, and copy feature buckets. They do not use
`drift_class`, plaintext, semantics, or row0 origin information.

## Summary

- Decisions: `{s['decision_count']}`.
- Residual decisions: `{s['residual_count']}`.
- Signature families: `{s['signature_family_count']}`.
- Label modes: `{s['label_mode_count']}`.
- Best signature: `{s['best_signature']}`.
- Best label mode: `{s['best_label_mode']}`.
- Best deterministic residual matches:
  `{s['best_deterministic_matches']}/{s['best_query_count']}`.
- Best supported residuals: `{s['best_supported_count']}/{s['best_query_count']}`.
- Best status counts: `{s['best_status_counts']}`.
- Prefix/holdout cells with any deterministic match:
  `{s['prequential_cells_with_deterministic_match']}/{s['prequential_cells_with_residuals']}`.
- Prefix/holdout cover-all residual cells:
  `{s['prequential_cover_all_residual_cells']}/{s['prequential_cells_with_residuals']}`.
- Promotes parser rule: `{s['promotes_observable_signature_parser']}`.

## Scoreboard

{md_table(scoreboard_rows, ["signature", "label mode", "deterministic matches", "supported", "contradictions", "ambiguous with stable", "status counts"])}

## Prefix/Holdout For Best Signature

{md_table(preq_rows, ["cutoff", "deterministic matches", "supported", "contradictions", "status counts"])}

## Residual Rows For Best Signature

{md_table(residual_rows, ["book", "op", "class", "active", "stable", "support", "labels", "majority", "status"])}

## Decision

Observable candidate signatures do not promote a segmentation parser. The best
full-fit signature explains only the listed deterministic residual subset, and
prefix/holdout does not cover all held-out residuals. The remaining residual
choices therefore still require either richer latent path/state information or
a source-free account of the target digit stream.

- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
"""
    md_path.write_text(body, encoding="utf-8")


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
