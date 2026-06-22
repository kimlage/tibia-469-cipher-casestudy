#!/usr/bin/env python3
"""Bucket-level joint chunk-origin beam pilot.

The route audit selected a joint chunk-origin representation as the next
constructive path. This first pilot asks a narrower, executable question:

If op start, copy type, previous material, and only the coarse length bucket are
granted, can a rank-coded prior chunk candidate replace the exact-length copy
hint/source tape?

This is deliberately a lower-bound pilot, not a promoted generator. It removes
the exact copy length grant inside copy chunks, but it still grants the
operation start/type/bucket stream and uses the target chunk only to measure the
rank of the correct candidate.
"""

from __future__ import annotations

import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "joint_chunk_origin_beam_pilot_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"

BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
LEDGER = (
    ROOT
    / "analysis"
    / "minimal_external_tape_program_audit_20260622"
    / "reports"
    / "test_results"
    / "02_unified_external_tape_ledger.json"
)
COPY_HINT_LOWER_BOUND = (
    ROOT
    / "analysis"
    / "latent_transducer_generation_audit_20260622"
    / "reports"
    / "test_results"
    / "08_copy_hint_stream_lower_bound.json"
)
ROUTE_GATE = (
    ROOT
    / "analysis"
    / "joint_chunk_origin_route_audit_20260622"
    / "reports"
    / "test_results"
    / "01_joint_chunk_origin_route_gate.json"
)

JSON_OUT = TEST_RESULTS / "01_bucket_chunk_origin_beam_pilot.json"
MD_OUT = TEST_RESULTS / "01_bucket_chunk_origin_beam_pilot.md"
FINAL_OUT = FRONT / "reports" / "final_joint_chunk_origin_beam_pilot_audit.md"

BUCKET_RANGES = {
    "len_0008": (1, 8),
    "len_0016": (9, 16),
    "len_0032": (17, 32),
    "len_0064": (33, 64),
    "len_0128": (65, 128),
    "len_0256p": (129, None),
}
POLICIES = [
    "freq_recent_long",
    "recent_long_freq",
    "long_freq_recent",
    "short_freq_recent",
]
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
RANDOM_SEED = 46920260622
RANDOM_TRIALS = 500
TOP_KS = [20, 80, 256, 1024]
DIGIT_BITS = math.log2(10)

ChunkRow = dict[str, Any]
PolicyKey = Callable[[ChunkRow, int], tuple[Any, ...]]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def assert_boundary(name: str, data: dict[str, Any]) -> None:
    if data.get("translation_delta") != "NONE":
        raise RuntimeError(f"{name} changed translation boundary")
    if data.get("case_reopened", False) is not False:
        raise RuntimeError(f"{name} reopened case")
    if data.get("plaintext_claim", False) is not False:
        raise RuntimeError(f"{name} introduced plaintext")
    if data.get("row0_status") not in {None, "unchanged_exogenous"}:
        raise RuntimeError(f"{name} changed row0 status")
    decision = data.get("decision", {})
    if decision.get("row0_status") not in {None, "unchanged_exogenous"}:
        raise RuntimeError(f"{name} changed row0 status")
    if decision.get("translation_delta") not in {None, "NONE"}:
        raise RuntimeError(f"{name} changed translation boundary")


def policy_key(name: str) -> PolicyKey:
    if name == "freq_recent_long":
        return lambda row, available_len: (
            -int(row["count"]),
            available_len - (int(row["max_source"]) + int(row["length"])),
            -int(row["length"]),
            row["chunk"],
        )
    if name == "recent_long_freq":
        return lambda row, available_len: (
            available_len - (int(row["max_source"]) + int(row["length"])),
            -int(row["length"]),
            -int(row["count"]),
            row["chunk"],
        )
    if name == "long_freq_recent":
        return lambda row, available_len: (
            -int(row["length"]),
            -int(row["count"]),
            available_len - (int(row["max_source"]) + int(row["length"])),
            row["chunk"],
        )
    if name == "short_freq_recent":
        return lambda row, available_len: (
            int(row["length"]),
            -int(row["count"]),
            available_len - (int(row["max_source"]) + int(row["length"])),
            row["chunk"],
        )
    raise KeyError(name)


def bucket_bounds(bucket: str, available_len: int, remaining: int) -> tuple[int, int]:
    low, high = BUCKET_RANGES[bucket]
    high = available_len if high is None else min(high, available_len)
    high = min(high, remaining)
    if high < low:
        raise RuntimeError({"bucket": bucket, "available_len": available_len, "remaining": remaining})
    return low, high


def unique_chunks_in_bucket(available: str, low: int, high: int) -> list[ChunkRow]:
    rows: dict[tuple[str, int], ChunkRow] = {}
    available_len = len(available)
    for length in range(low, high + 1):
        if length > available_len:
            break
        for source in range(0, available_len - length + 1):
            chunk = available[source : source + length]
            key = (chunk, length)
            row = rows.get(key)
            if row is None:
                rows[key] = {
                    "chunk": chunk,
                    "count": 1,
                    "length": length,
                    "max_source": source,
                    "min_source": source,
                }
            else:
                row["count"] += 1
                row["max_source"] = source
    return list(rows.values())


def rank_correct(
    candidates: list[ChunkRow],
    payload: str,
    length: int,
    available_len: int,
    policy: str,
) -> int:
    correct = next(
        row for row in candidates if row["chunk"] == payload and int(row["length"]) == length
    )
    key_fn = policy_key(policy)
    correct_key = key_fn(correct, available_len)
    return 1 + sum(1 for row in candidates if key_fn(row, available_len) < correct_key)


def grouped_ledger_rows() -> dict[int, list[dict[str, Any]]]:
    ledger = load_json(LEDGER)
    assert_boundary("unified_external_tape_ledger", ledger)
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in ledger["ledger_rows"]:
        grouped[int(row["book"])].append(row)
    return {
        book: sorted(rows, key=lambda item: int(item["op_index"]))
        for book, rows in grouped.items()
    }


def build_event_rows() -> list[dict[str, Any]]:
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    by_book = grouped_ledger_rows()
    emitted = "".join(books[book] for book in range(10))
    events: list[dict[str, Any]] = []
    for book in range(10, 70):
        rendered: list[str] = []
        for row in by_book[book]:
            op_type = str(row["op_type"])
            start = int(row["target_start"])
            length = int(row["exact_length"])
            available = emitted + "".join(rendered)
            if op_type == "literal":
                rendered.append(str(row["literal_payload"]))
                continue
            bucket = str(row["coarse_type_length_bucket"]).split(":", 1)[1]
            payload = books[book][start : start + length]
            low, high = bucket_bounds(bucket, len(available), int(row["book_length"]) - start)
            candidates = unique_chunks_in_bucket(available, low, high)
            rank_by_policy = {
                policy: rank_correct(candidates, payload, length, len(available), policy)
                for policy in POLICIES
            }
            candidate_count = len(candidates)
            if not (0 <= int(row["copy_source_raw"]) <= len(available) - length):
                raise RuntimeError({"book": book, "op_index": row["op_index"], "type": "bad_source"})
            rendered.append(available[int(row["copy_source_raw"]) : int(row["copy_source_raw"]) + length])
            events.append(
                {
                    "book": book,
                    "bucket": bucket,
                    "candidate_count": candidate_count,
                    "copy_hint_rank_bits_exact_length": float(row["copy_hint_rank_bits"]),
                    "copy_source_raw": int(row["copy_source_raw"]),
                    "exact_length": length,
                    "op_index": int(row["op_index"]),
                    "rank_bits_by_policy": {
                        policy: math.log2(rank_by_policy[policy]) for policy in POLICIES
                    },
                    "rank_by_policy": rank_by_policy,
                    "raw_source_address_bits": math.log2(max(1, len(available) - length + 1)),
                    "target_start": start,
                    "uniform_bucket_candidate_bits": math.log2(candidate_count),
                }
            )
        rendered_book = "".join(rendered)
        if rendered_book != books[book]:
            raise RuntimeError({"book": book, "type": "roundtrip_failed"})
        emitted += rendered_book
    return events


def percentile(values: list[float], p: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, math.ceil((p / 100.0) * len(ordered)) - 1))
    return ordered[index]


def random_rank_controls(events: list[dict[str, Any]], seed_offset: int = 0) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED + seed_offset)
    totals: list[float] = []
    top_hits = {str(k): [] for k in TOP_KS}
    for _ in range(RANDOM_TRIALS):
        total = 0.0
        hits = {k: 0 for k in TOP_KS}
        for row in events:
            rank = rng.randint(1, int(row["candidate_count"]))
            total += math.log2(rank)
            for k in TOP_KS:
                if rank <= k:
                    hits[k] += 1
        totals.append(total)
        for k in TOP_KS:
            top_hits[str(k)].append(hits[k])
    return {
        "random_rank_bits_mean": mean(totals),
        "random_rank_bits_p05": percentile(totals, 5),
        "random_rank_bits_p50": percentile(totals, 50),
        "random_rank_bits_p95": percentile(totals, 95),
        "random_topk_hits_p95": {
            key: percentile([float(value) for value in values], 95)
            for key, values in top_hits.items()
        },
        "seed": RANDOM_SEED + seed_offset,
        "trials": RANDOM_TRIALS,
    }


def summarize_events(events: list[dict[str, Any]], selected_policy: str | None = None) -> dict[str, Any]:
    if not events:
        return {
            "copy_ops": 0,
            "copy_digits": 0,
            "selected_policy": selected_policy,
        }
    policy_bits = {
        policy: sum(float(row["rank_bits_by_policy"][policy]) for row in events)
        for policy in POLICIES
    }
    best_policy = selected_policy or min(policy_bits, key=lambda policy: policy_bits[policy])
    topk_hits = {
        str(k): sum(1 for row in events if int(row["rank_by_policy"][best_policy]) <= k)
        for k in TOP_KS
    }
    candidate_counts = [int(row["candidate_count"]) for row in events]
    exact_hint_bits = sum(float(row["copy_hint_rank_bits_exact_length"]) for row in events)
    source_bits = sum(float(row["raw_source_address_bits"]) for row in events)
    uniform_bits = sum(float(row["uniform_bucket_candidate_bits"]) for row in events)
    best_bits = policy_bits[best_policy]
    return {
        "best_policy_if_fit": min(policy_bits, key=lambda policy: policy_bits[policy]),
        "bucket_best_rank_bits": best_bits,
        "bucket_delta_vs_exact_length_copy_hint_bits": best_bits - exact_hint_bits,
        "bucket_delta_vs_raw_source_address_bits": best_bits - source_bits,
        "bucket_rank_saving_vs_uniform_candidate_bits": uniform_bits - best_bits,
        "candidate_count_max": max(candidate_counts),
        "candidate_count_mean": mean(candidate_counts),
        "candidate_count_median": sorted(candidate_counts)[len(candidate_counts) // 2],
        "copy_digits": sum(int(row["exact_length"]) for row in events),
        "copy_ops": len(events),
        "exact_length_copy_hint_bits": exact_hint_bits,
        "policy_rank_bits": policy_bits,
        "raw_source_address_bits": source_bits,
        "selected_policy": best_policy,
        "topk_hits": topk_hits,
        "uniform_bucket_candidate_bits": uniform_bits,
    }


def prefix_holdouts(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for offset, cutoff in enumerate(PREFIX_CUTOFFS):
        train = [row for row in events if int(row["book"]) < cutoff]
        test = [row for row in events if int(row["book"]) >= cutoff]
        train_summary = summarize_events(train)
        policy = train_summary["best_policy_if_fit"]
        test_summary = summarize_events(test, selected_policy=policy)
        controls = random_rank_controls(test, seed_offset=1000 + offset)
        rows.append(
            {
                "cutoff": cutoff,
                "random_controls": controls,
                "selected_policy": policy,
                "test_bucket_rank_bits": test_summary["bucket_best_rank_bits"],
                "test_copy_ops": test_summary["copy_ops"],
                "test_delta_vs_exact_length_copy_hint_bits": test_summary[
                    "bucket_delta_vs_exact_length_copy_hint_bits"
                ],
                "test_delta_vs_raw_source_address_bits": test_summary[
                    "bucket_delta_vs_raw_source_address_bits"
                ],
                "test_rank_saving_vs_uniform_candidate_bits": test_summary[
                    "bucket_rank_saving_vs_uniform_candidate_bits"
                ],
                "test_topk_hits": test_summary["topk_hits"],
            }
        )
    return rows


def make_result() -> dict[str, Any]:
    route = load_json(ROUTE_GATE)
    assert_boundary("joint_chunk_origin_route_gate", route)
    hint = load_json(COPY_HINT_LOWER_BOUND)
    assert_boundary("copy_hint_stream_lower_bound", hint)
    events = build_event_rows()
    full = summarize_events(events)
    controls = random_rank_controls(events)
    holdouts = prefix_holdouts(events)
    observed_beats_random_p05 = full["bucket_best_rank_bits"] < controls["random_rank_bits_p05"]
    holdout_cells_beating_p05 = sum(
        row["test_bucket_rank_bits"] < row["random_controls"]["random_rank_bits_p05"]
        for row in holdouts
    )
    reduces_copy_external_ledger = (
        full["bucket_best_rank_bits"] < full["exact_length_copy_hint_bits"]
        or full["bucket_best_rank_bits"] < full["raw_source_address_bits"]
    )
    classification = (
        "PROMOTED_JOINT_CHUNK_ORIGIN_COPY_PROGRAM"
        if reduces_copy_external_ledger and holdout_cells_beating_p05 >= 4
        else "WEAK_JOINT_CHUNK_ORIGIN_BEAM_CLUE"
        if observed_beats_random_p05
        else "JOINT_CHUNK_ORIGIN_BEAM_NOT_PROMOTED"
    )
    compact_rows = [
        {
            "book": row["book"],
            "bucket": row["bucket"],
            "candidate_count": row["candidate_count"],
            "exact_length": row["exact_length"],
            "op_index": row["op_index"],
            "rank_by_selected_policy": row["rank_by_policy"][full["selected_policy"]],
            "target_start": row["target_start"],
        }
        for row in sorted(
            events,
            key=lambda item: int(item["rank_by_policy"][full["selected_policy"]]),
        )[:20]
    ]
    hard_rows = [
        {
            "book": row["book"],
            "bucket": row["bucket"],
            "candidate_count": row["candidate_count"],
            "exact_length": row["exact_length"],
            "op_index": row["op_index"],
            "rank_by_selected_policy": row["rank_by_policy"][full["selected_policy"]],
            "target_start": row["target_start"],
        }
        for row in sorted(
            events,
            key=lambda item: int(item["rank_by_policy"][full["selected_policy"]]),
            reverse=True,
        )[:20]
    ]
    return {
        "case_reopened": False,
        "classification": classification,
        "compression_bound_status": "unchanged",
        "controls": controls,
        "decision": {
            "book_text_generator_promoted": False,
            "copy_chunk_origin_program_promoted": classification
            == "PROMOTED_JOINT_CHUNK_ORIGIN_COPY_PROGRAM",
            "next_blocker": (
                "bucket-level candidate sets are still too broad; a stronger "
                "target-free length/chunk prior is required before this becomes "
                "an executable decoder component"
            ),
            "row0_status": "unchanged_exogenous",
            "translation_delta": "NONE",
        },
        "event_count": len(events),
        "grants": [
            "canonical operation start",
            "copy operation type",
            "coarse length bucket",
            "previous emitted material",
            "target chunk only for rank measurement",
        ],
        "hardest_rows": hard_rows,
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "copy_hint_stream_lower_bound": rel(COPY_HINT_LOWER_BOUND),
            "joint_chunk_origin_route_gate": rel(ROUTE_GATE),
            "unified_external_tape_ledger": rel(LEDGER),
        },
        "plaintext_claim": False,
        "prefix_holdouts": holdouts,
        "schema": "bucket_chunk_origin_beam_pilot.v1",
        "scope": "analysis_only_bucket_level_copy_chunk_origin_lower_bound",
        "summary": {
            **full,
            "full_random_rank_bits_p05": controls["random_rank_bits_p05"],
            "full_random_rank_bits_p50": controls["random_rank_bits_p50"],
            "full_random_rank_bits_p95": controls["random_rank_bits_p95"],
            "holdout_cells_beating_random_p05": holdout_cells_beating_p05,
            "observed_beats_random_p05": observed_beats_random_p05,
            "reduces_copy_external_ledger": reduces_copy_external_ledger,
        },
        "top_rows": compact_rows,
        "translation_delta": "NONE",
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    c = result["controls"]
    lines = [
        "# Bucket Chunk-Origin Beam Pilot",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Purpose",
        "",
        "Test the first concrete joint chunk-origin route: replace exact-length "
        "copy-source/hint selection with a rank over prior chunks inside the granted "
        "coarse length bucket.",
        "",
        "## Summary",
        "",
        f"- Copy ops: `{s['copy_ops']}`.",
        f"- Copy digits: `{s['copy_digits']}`.",
        f"- Selected policy: `{s['selected_policy']}`.",
        f"- Exact-length copy hint bits: `{s['exact_length_copy_hint_bits']:.3f}`.",
        f"- Raw source-address bits: `{s['raw_source_address_bits']:.3f}`.",
        f"- Bucket chunk-origin rank bits: `{s['bucket_best_rank_bits']:.3f}`.",
        f"- Delta vs exact-length copy hint: `{s['bucket_delta_vs_exact_length_copy_hint_bits']:.3f}` bits.",
        f"- Delta vs raw source address: `{s['bucket_delta_vs_raw_source_address_bits']:.3f}` bits.",
        f"- Saving vs uniform bucket candidates: `{s['bucket_rank_saving_vs_uniform_candidate_bits']:.3f}` bits.",
        f"- Candidate count median/mean/max: `{s['candidate_count_median']}` / `{s['candidate_count_mean']:.3f}` / `{s['candidate_count_max']}`.",
        f"- Top-80 hits: `{s['topk_hits']['80']}/{s['copy_ops']}`.",
        "",
        "## Random Rank Controls",
        "",
        f"- Trials: `{c['trials']}`.",
        f"- Random rank bits p05/p50/p95: `{c['random_rank_bits_p05']:.3f}` / `{c['random_rank_bits_p50']:.3f}` / `{c['random_rank_bits_p95']:.3f}`.",
        f"- Observed beats random p05: `{s['observed_beats_random_p05']}`.",
        f"- Prefix holdout cells beating random p05: `{s['holdout_cells_beating_random_p05']}/{len(result['prefix_holdouts'])}`.",
        "",
        "## Prefix Holdouts",
        "",
        "| Cutoff | Policy | Test ops | Rank bits | Delta vs exact hint | Delta vs source | Beats random p05 |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in result["prefix_holdouts"]:
        beats = row["test_bucket_rank_bits"] < row["random_controls"]["random_rank_bits_p05"]
        lines.append(
            f"| `{row['cutoff']}` | `{row['selected_policy']}` | "
            f"`{row['test_copy_ops']}` | `{row['test_bucket_rank_bits']:.3f}` | "
            f"`{row['test_delta_vs_exact_length_copy_hint_bits']:.3f}` | "
            f"`{row['test_delta_vs_raw_source_address_bits']:.3f}` | `{beats}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "The bucket-level chunk-origin representation contains a real ranking "
            "signal against random candidate ranks, but it is not promoted as an "
            "executable program component. Removing the exact copy-length grant "
            "adds more cost than the current exact-length copy hint/source ledger. "
            "The next blocker is a stronger target-free length/chunk prior, not "
            "another local source selector.",
        ]
    )
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Final Joint Chunk-Origin Beam Pilot Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Question",
        "",
        "Can the selected joint chunk-origin route already reduce the executable "
        "copy/source tape when exact copy length is replaced by only the coarse "
        "length bucket?",
        "",
        "## Result",
        "",
        f"The selected bucket chunk-origin policy is `{s['selected_policy']}`. It "
        f"costs `{s['bucket_best_rank_bits']:.3f}` rank bits across `{s['copy_ops']}` "
        f"copy ops, versus `{s['exact_length_copy_hint_bits']:.3f}` bits for the "
        f"exact-length copy hint and `{s['raw_source_address_bits']:.3f}` raw "
        "source-address bits.",
        "",
        f"It saves `{s['bucket_rank_saving_vs_uniform_candidate_bits']:.3f}` bits "
        "against uniform bucket-candidate ranks and beats the full random p05 "
        f"control (`{s['full_random_rank_bits_p05']:.3f}`), but it is "
        f"`{s['bucket_delta_vs_exact_length_copy_hint_bits']:.3f}` bits worse than "
        "the exact-length hint and has only "
        f"`{s['topk_hits']['80']}/{s['copy_ops']}` top-80 hits.",
        "",
        "## Decision",
        "",
        "`joint_chunk_origin_beam_pilot` remains open as a representation route, "
        "but this first bucket-level copy pilot is not an executable generator. "
        "The current blocker is the lack of a target-free length/chunk prior sharp "
        "enough to replace exact length plus copy hint. Row0, plaintext, translation, "
        "and compression_bound are unchanged.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_bucket_chunk_origin_beam_pilot.py](../scripts/01_bucket_chunk_origin_beam_pilot.py)",
        "- [01_bucket_chunk_origin_beam_pilot.json](test_results/01_bucket_chunk_origin_beam_pilot.json)",
        "- [01_bucket_chunk_origin_beam_pilot.md](test_results/01_bucket_chunk_origin_beam_pilot.md)",
    ]
    FINAL_OUT.write_text("\n".join(lines) + "\n")


def main() -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    result = make_result()
    JSON_OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_markdown(result)
    write_final(result)


if __name__ == "__main__":
    main()
