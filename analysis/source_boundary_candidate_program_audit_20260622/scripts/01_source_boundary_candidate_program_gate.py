#!/usr/bin/env python3
"""Source-boundary candidate program gate.

Event-aligned chunks explain too few copy events. This gate tests the next
structural possibility: a copy's source and length are derived by choosing an
interval between decoder-visible boundaries in the already emitted material.

The program pays an interval rank only when both exact source boundaries are in
the candidate set. Otherwise it falls back to the executable-v2 copy-hint tape.
Book-level composition cost is recomputed after the derived copy lengths are
removed from the residual length composition.

Analysis-only: no row0, plaintext, semantics, or compression-bound change.
"""

from __future__ import annotations

import bisect
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "source_boundary_candidate_program_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"

BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
UNIFIED_LEDGER = (
    ROOT
    / "analysis"
    / "minimal_external_tape_program_audit_20260622"
    / "reports"
    / "test_results"
    / "02_unified_external_tape_ledger.json"
)
EVENT_ALIGNED_GATE = (
    ROOT
    / "analysis"
    / "event_aligned_chunk_library_audit_20260622"
    / "reports"
    / "test_results"
    / "01_event_aligned_chunk_library_gate.json"
)

JSON_OUT = TEST_RESULTS / "01_source_boundary_candidate_program_gate.json"
MD_OUT = TEST_RESULTS / "01_source_boundary_candidate_program_gate.md"
FINAL_OUT = FRONT / "reports" / "final_source_boundary_candidate_program_audit.md"

BUCKET_RANGES = {
    "len_0008": (1, 8),
    "len_0016": (9, 16),
    "len_0032": (17, 32),
    "len_0064": (33, 64),
    "len_0128": (65, 128),
    "len_0256p": (129, None),
}
SYSTEMS = [
    "event_boundaries",
    "surprisal_top05",
    "surprisal_top10",
    "surprisal_top20",
    "event_plus_surprisal_top05",
    "event_plus_surprisal_top10",
    "event_plus_surprisal_top20",
]
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
RANDOM_SEED = 46920260622
RANDOM_TRIALS = 300
LOG2_10 = math.log2(10)


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


def grouped_ledger_rows() -> tuple[dict[int, list[dict[str, Any]]], dict[str, Any]]:
    ledger = load_json(UNIFIED_LEDGER)
    assert_boundary("unified_external_tape_ledger", ledger)
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in ledger["ledger_rows"]:
        grouped[int(row["book"])].append(row)
    return {
        book: sorted(rows, key=lambda item: int(item["op_index"]))
        for book, rows in grouped.items()
    }, ledger


def bucket_bounds(bucket: str, upper: int) -> tuple[int, int]:
    low, high = BUCKET_RANGES[bucket]
    high = upper if high is None else min(high, upper)
    if high < low:
        return low, low - 1
    return low, high


def composition_count_for_unknowns(unknown_rows: list[dict[str, Any]], remaining_sum: int) -> int:
    dp = {0: 1}
    for row in unknown_rows:
        bucket = str(row["coarse_type_length_bucket"]).split(":", 1)[1]
        low, high = bucket_bounds(bucket, int(row["book_length"]) - int(row["target_start"]))
        next_dp: dict[int, int] = defaultdict(int)
        for current_sum, count in dp.items():
            for length in range(low, high + 1):
                total = current_sum + length
                if total <= remaining_sum:
                    next_dp[total] += count
        dp = dict(next_dp)
    return max(1, dp.get(remaining_sum, 0))


def event_boundary_set(segment_boundaries: set[int], available_len: int) -> set[int]:
    return {value for value in segment_boundaries if 0 <= value <= available_len} | {0, available_len}


def surprisal_boundaries(available: str, fraction: float) -> set[int]:
    if not available:
        return {0}
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    global_counts: Counter[str] = Counter()
    for idx, digit in enumerate(available):
        global_counts[digit] += 1
        if idx >= 2:
            counts[available[idx - 2 : idx]][digit] += 1
    global_total = sum(global_counts.values())
    scored = []
    for pos in range(1, len(available)):
        digit = available[pos]
        ctx = available[pos - 2 : pos] if pos >= 2 else ""
        counter = counts.get(ctx)
        if counter and sum(counter.values()):
            total = sum(counter.values())
            probability = (counter[digit] + 0.5) / (total + 5.0)
        else:
            probability = (global_counts[digit] + 0.5) / (global_total + 5.0)
        scored.append((-math.log2(max(probability, 1e-300)), pos))
    keep = max(1, math.ceil(len(scored) * fraction))
    chosen = {pos for _score, pos in sorted(scored, reverse=True)[:keep]}
    return chosen | {0, len(available)}


def interval_count(boundaries: list[int], low: int, high: int) -> int:
    total = 0
    for start in boundaries:
        lo = bisect.bisect_left(boundaries, start + low)
        hi = bisect.bisect_right(boundaries, start + high)
        total += max(0, hi - lo)
    return max(1, total)


def long_recent_rank(boundaries: list[int], source: int, length: int, low: int, high: int) -> int:
    longer = 0
    for start in boundaries:
        lo = bisect.bisect_left(boundaries, start + length + 1)
        hi = bisect.bisect_right(boundaries, start + high)
        longer += max(0, hi - lo)
    same_longer_source = sum(1 for start in boundaries if start > source and start + length in boundary_set_global)
    return 1 + longer + same_longer_source


boundary_set_global: set[int] = set()


def recent_long_rank(boundaries: list[int], source: int, length: int, low: int, high: int) -> int:
    rank = 1
    for start in boundaries:
        if start > source:
            lo = bisect.bisect_left(boundaries, start + low)
            hi = bisect.bisect_right(boundaries, start + high)
            rank += max(0, hi - lo)
        elif start == source:
            lo = bisect.bisect_left(boundaries, start + length + 1)
            hi = bisect.bisect_right(boundaries, start + high)
            rank += max(0, hi - lo)
    return rank


def build_boundary_systems(available: str, event_boundaries: set[int]) -> dict[str, set[int]]:
    s05 = surprisal_boundaries(available, 0.05)
    s10 = surprisal_boundaries(available, 0.10)
    s20 = surprisal_boundaries(available, 0.20)
    eb = event_boundary_set(event_boundaries, len(available))
    return {
        "event_boundaries": eb,
        "surprisal_top05": s05,
        "surprisal_top10": s10,
        "surprisal_top20": s20,
        "event_plus_surprisal_top05": eb | s05,
        "event_plus_surprisal_top10": eb | s10,
        "event_plus_surprisal_top20": eb | s20,
    }


def score_system(system_name: str, shuffled_event_boundaries: bool = False) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    by_book, ledger = grouped_ledger_rows()
    emitted = "".join(books[book] for book in range(10))
    event_boundaries = {0}
    cursor = 0
    for book in range(10):
        cursor += len(books[book])
        event_boundaries.add(cursor)
    rows: list[dict[str, Any]] = []
    event_rows_by_book: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for book in range(10, 70):
        rendered: list[str] = []
        for op in by_book[book]:
            available = emitted + "".join(rendered)
            local_boundaries = set(event_boundaries)
            if rendered:
                prefix_cursor = len(emitted)
                acc = 0
                local_boundaries.add(prefix_cursor)
                for chunk in rendered:
                    acc += len(chunk)
                    local_boundaries.add(prefix_cursor + acc)
            if shuffled_event_boundaries:
                rng = random.Random(RANDOM_SEED + book * 1000 + int(op["op_index"]))
                count = len(local_boundaries)
                local_boundaries = set(rng.sample(range(len(available) + 1), min(count, len(available) + 1)))
                local_boundaries |= {0, len(available)}
            systems = build_boundary_systems(available, local_boundaries)
            op_type = str(op["op_type"])
            length = int(op["exact_length"])
            start = int(op["target_start"])
            if op_type == "copy":
                bucket = str(op["coarse_type_length_bucket"]).split(":", 1)[1]
                low, high = bucket_bounds(bucket, int(op["book_length"]) - start)
                source = int(op["copy_source_raw"])
                source_end = source + length
                boundaries = sorted(systems[system_name])
                boundary_set = set(boundaries)
                hit = source in boundary_set and source_end in boundary_set and low <= length <= high
                count = interval_count(boundaries, low, high)
                global boundary_set_global
                boundary_set_global = boundary_set
                long_rank = long_recent_rank(boundaries, source, length, low, high) if hit else None
                recent_rank = recent_long_rank(boundaries, source, length, low, high) if hit else None
                row = {
                    "available_len": len(available),
                    "book": book,
                    "boundary_count": len(boundaries),
                    "candidate_interval_count": count,
                    "copy_hint_rank_bits": float(op["copy_hint_rank_bits"]),
                    "event_kind": "copy",
                    "exact_length": length,
                    "hit": hit,
                    "long_recent_rank_bits": math.log2(long_rank) if long_rank else None,
                    "op_index": int(op["op_index"]),
                    "raw_v2_bits": float(op["copy_hint_rank_bits"]),
                    "recent_long_rank_bits": math.log2(recent_rank) if recent_rank else None,
                    "source": source,
                    "source_end": source_end,
                    "system": system_name,
                    "target_start": start,
                    "uniform_interval_bits": math.log2(count),
                }
            else:
                row = {
                    "book": book,
                    "event_kind": "literal",
                    "exact_length": length,
                    "hit": True,
                    "literal_payload_bits": float(op["literal_payload_bits"]),
                    "op_index": int(op["op_index"]),
                    "raw_v2_bits": float(op["literal_payload_bits"]),
                    "system": system_name,
                    "target_start": start,
                }
            rows.append(row)
            event_rows_by_book[book].append(row)
            chunk = books[book][start : start + length]
            rendered.append(chunk)
        rendered_book = "".join(rendered)
        if rendered_book != books[book]:
            raise RuntimeError({"book": book, "reason": "roundtrip_failed"})
        for chunk in rendered:
            emitted_start = len(emitted)
            emitted += chunk
            event_boundaries.add(emitted_start)
            event_boundaries.add(len(emitted))
    composition_bits_by_book = {}
    baseline_composition_bits_by_book = {}
    for book, scored_rows in event_rows_by_book.items():
        truth_rows = by_book[book]
        known_sum = 0
        unknown = []
        for scored, op in zip(scored_rows, truth_rows):
            if scored["event_kind"] == "copy" and scored["hit"]:
                known_sum += int(op["exact_length"])
            else:
                unknown.append(op)
        remaining = int(truth_rows[0]["book_length"]) - known_sum
        composition_bits_by_book[book] = math.log2(composition_count_for_unknowns(unknown, remaining))
        baseline_composition_bits_by_book[book] = sum(
            float(op["composition_index_bits_charged_here"]) for op in truth_rows
        )
    return rows, {
        "baseline_composition_bits_by_book": baseline_composition_bits_by_book,
        "composition_bits_by_book": composition_bits_by_book,
        "ledger_summary": ledger["summary"],
        "shuffled_event_boundaries": shuffled_event_boundaries,
        "system": system_name,
    }


def summarize(rows: list[dict[str, Any]], meta: dict[str, Any], policy: str | None = None) -> dict[str, Any]:
    copy_rows = [row for row in rows if row["event_kind"] == "copy"]
    literal_rows = [row for row in rows if row["event_kind"] == "literal"]
    policy_bits = {}
    for name in ("long_recent", "recent_long", "uniform"):
        total = 0.0
        for row in copy_rows:
            if not row["hit"]:
                total += float(row["copy_hint_rank_bits"])
            elif name == "uniform":
                total += float(row["uniform_interval_bits"])
            else:
                total += float(row[f"{name}_rank_bits"])
        policy_bits[name] = total
    selected = policy or min(policy_bits, key=lambda key: policy_bits[key])
    composition = sum(float(value) for value in meta["composition_bits_by_book"].values())
    baseline_composition = sum(float(value) for value in meta["baseline_composition_bits_by_book"].values())
    literal_payload = sum(float(row["literal_payload_bits"]) for row in literal_rows)
    baseline = (
        baseline_composition
        + literal_payload
        + sum(float(row["copy_hint_rank_bits"]) for row in copy_rows)
    )
    total = composition + literal_payload + policy_bits[selected]
    hit_rows = [row for row in copy_rows if row["hit"]]
    interval_counts = [int(row["candidate_interval_count"]) for row in hit_rows]
    return {
        "baseline_v2_residual_bits": baseline,
        "boundary_count_mean": mean([int(row["boundary_count"]) for row in copy_rows]) if copy_rows else 0.0,
        "candidate_interval_count_max_hit": max(interval_counts) if interval_counts else 0,
        "candidate_interval_count_mean_hit": mean(interval_counts) if interval_counts else 0.0,
        "candidate_interval_count_median_hit": sorted(interval_counts)[len(interval_counts) // 2]
        if interval_counts
        else 0,
        "composition_bits_after_derived_copy_lengths": composition,
        "copy_hits": len(hit_rows),
        "copy_misses": len(copy_rows) - len(hit_rows),
        "copy_ops": len(copy_rows),
        "delta_vs_v2_residual_bits": total - baseline,
        "literal_payload_bits": literal_payload,
        "policy_copy_or_fallback_bits": policy_bits,
        "selected_policy": selected,
        "source_boundary_program_bits": total,
        "system": meta["system"],
        "top80_hits": sum(
            1
            for row in hit_rows
            if row[f"{selected}_rank_bits"] is not None
            and 2 ** float(row[f"{selected}_rank_bits"]) <= 80
        )
        if selected != "uniform"
        else sum(1 for row in hit_rows if int(row["candidate_interval_count"]) <= 80),
    }


def prefix_holdouts(rows: list[dict[str, Any]], meta: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for cutoff in PREFIX_CUTOFFS:
        train_books = {int(row["book"]) for row in rows if int(row["book"]) < cutoff}
        test_books = {int(row["book"]) for row in rows if int(row["book"]) >= cutoff}
        train_rows = [row for row in rows if int(row["book"]) < cutoff]
        test_rows = [row for row in rows if int(row["book"]) >= cutoff]
        train_meta = {
            **meta,
            "baseline_composition_bits_by_book": {
                book: value
                for book, value in meta["baseline_composition_bits_by_book"].items()
                if int(book) in train_books
            },
            "composition_bits_by_book": {
                book: value
                for book, value in meta["composition_bits_by_book"].items()
                if int(book) in train_books
            },
        }
        test_meta = {
            **meta,
            "baseline_composition_bits_by_book": {
                book: value
                for book, value in meta["baseline_composition_bits_by_book"].items()
                if int(book) in test_books
            },
            "composition_bits_by_book": {
                book: value
                for book, value in meta["composition_bits_by_book"].items()
                if int(book) in test_books
            },
        }
        policy = summarize(train_rows, train_meta)["selected_policy"]
        scored = summarize(test_rows, test_meta, policy=policy)
        out.append(
            {
                "cutoff": cutoff,
                "selected_policy": policy,
                "test_boundary_bits": scored["source_boundary_program_bits"],
                "test_copy_hits": scored["copy_hits"],
                "test_delta_vs_v2": scored["delta_vs_v2_residual_bits"],
                "test_v2_bits": scored["baseline_v2_residual_bits"],
            }
        )
    return out


def percentile(values: list[float], p: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    index = min(len(ordered) - 1, max(0, math.ceil((p / 100.0) * len(ordered)) - 1))
    return ordered[index]


def random_boundary_control(best_rows: list[dict[str, Any]], best_summary: dict[str, Any]) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED + 77)
    copy_rows = [row for row in best_rows if row["event_kind"] == "copy"]
    totals = []
    hits = []
    for _ in range(RANDOM_TRIALS):
        total_bits = 0.0
        hit_count = 0
        for row in copy_rows:
            boundary_count = max(2, int(row["boundary_count"]))
            available_len = int(row["available_len"])
            sampled = set(rng.sample(range(available_len + 1), min(boundary_count, available_len + 1)))
            sampled |= {0, available_len}
            hit = int(row["source"]) in sampled and int(row["source_end"]) in sampled
            if hit:
                hit_count += 1
                total_bits += math.log2(max(1, boundary_count * boundary_count / 2))
            else:
                total_bits += float(row["copy_hint_rank_bits"])
        totals.append(total_bits)
        hits.append(hit_count)
    observed_copy_bits = best_summary["policy_copy_or_fallback_bits"][best_summary["selected_policy"]]
    return {
        "observed_copy_or_fallback_bits": observed_copy_bits,
        "observed_hits": best_summary["copy_hits"],
        "random_bits_p05": percentile(totals, 5),
        "random_bits_p50": percentile(totals, 50),
        "random_bits_p95": percentile(totals, 95),
        "random_hits_p95": percentile([float(value) for value in hits], 95),
        "trials": RANDOM_TRIALS,
    }


def make_result() -> dict[str, Any]:
    event_gate = load_json(EVENT_ALIGNED_GATE)
    assert_boundary("event_aligned_chunk_library_gate", event_gate)
    system_results = []
    scored_by_system = {}
    for system in SYSTEMS:
        rows, meta = score_system(system)
        summary = summarize(rows, meta)
        system_results.append(summary)
        scored_by_system[system] = (rows, meta, summary)
    best_summary = min(system_results, key=lambda row: row["source_boundary_program_bits"])
    best_rows, best_meta, best_summary = scored_by_system[best_summary["system"]]
    holdouts = prefix_holdouts(best_rows, best_meta)
    shuffled_rows, shuffled_meta = score_system(best_summary["system"], shuffled_event_boundaries=True)
    shuffled_summary = summarize(shuffled_rows, shuffled_meta, policy=best_summary["selected_policy"])
    random_control = random_boundary_control(best_rows, best_summary)
    holdout_improves = sum(row["test_delta_vs_v2"] < 0 for row in holdouts)
    beats_control = (
        best_summary["source_boundary_program_bits"] < shuffled_summary["source_boundary_program_bits"]
        and best_summary["copy_hits"] > random_control["random_hits_p95"]
    )
    promoted = (
        best_summary["delta_vs_v2_residual_bits"] < 0
        and holdout_improves >= 4
        and best_summary["copy_hits"] >= 25
        and beats_control
    )
    classification = (
        "PROMOTED_SOURCE_BOUNDARY_PROGRAM"
        if promoted
        else "WEAK_SOURCE_BOUNDARY_CLUE"
        if best_summary["copy_hits"] >= 10 and holdout_improves >= 4
        else "source_boundary_candidate_program_not_promoted"
    )
    return {
        "case_reopened": False,
        "classification": classification,
        "compression_bound_status": "unchanged",
        "controls": {
            "random_boundary_control": random_control,
            "shuffled_event_boundaries": shuffled_summary,
        },
        "decision": {
            "next_blocker": (
                "source intervals are not sufficiently captured by event or "
                "prev2-surprisal boundary systems; subchunk origin remains external"
            ),
            "plaintext_claim": False,
            "row0_status": "unchanged_exogenous",
            "source_boundary_program_promoted": promoted,
            "translation_delta": "NONE",
        },
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "event_aligned_chunk_library_gate": rel(EVENT_ALIGNED_GATE),
            "unified_external_tape_ledger": rel(UNIFIED_LEDGER),
        },
        "plaintext_claim": False,
        "prefix_holdouts": holdouts,
        "row0_status": "unchanged_exogenous",
        "schema": "source_boundary_candidate_program_gate.v1",
        "scope": "analysis_only_source_boundary_candidate_program",
        "summary": {
            **best_summary,
            "holdout_splits_improving_v2": holdout_improves,
            "promoted": promoted,
        },
        "system_results": system_results,
        "translation_delta": "NONE",
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    c = result["controls"]
    lines = [
        "# Source-Boundary Candidate Program Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Question",
        "",
        "Can copy source and length be derived by choosing an interval between "
        "decoder-visible boundaries in the already emitted material?",
        "",
        "## Summary",
        "",
        f"- Best boundary system: `{s['system']}`.",
        f"- Selected interval policy: `{s['selected_policy']}`.",
        f"- Copy hits/misses: `{s['copy_hits']}/{s['copy_misses']}` out of `{s['copy_ops']}`.",
        f"- V2 residual baseline: `{s['baseline_v2_residual_bits']:.3f}` bits.",
        f"- Source-boundary program bits: `{s['source_boundary_program_bits']:.3f}` bits.",
        f"- Delta vs v2 residual: `{s['delta_vs_v2_residual_bits']:.3f}` bits.",
        f"- Composition bits after derived copy lengths: `{s['composition_bits_after_derived_copy_lengths']:.3f}`.",
        f"- Boundary count mean: `{s['boundary_count_mean']:.3f}`.",
        f"- Candidate interval count median/mean/max on hits: `{s['candidate_interval_count_median_hit']}` / `{s['candidate_interval_count_mean_hit']:.3f}` / `{s['candidate_interval_count_max_hit']}`.",
        f"- Top-80 hits: `{s['top80_hits']}/{s['copy_ops']}`.",
        "",
        "## Systems",
        "",
        "| System | Hits | Bits | Delta vs v2 | Policy |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for row in result["system_results"]:
        lines.append(
            f"| `{row['system']}` | `{row['copy_hits']}` | "
            f"`{row['source_boundary_program_bits']:.3f}` | "
            f"`{row['delta_vs_v2_residual_bits']:.3f}` | `{row['selected_policy']}` |"
        )
    lines.extend(
        [
            "",
            "## Prefix Holdout",
            "",
            "| Cutoff | Policy | Hits | Program bits | V2 bits | Delta |",
            "| ---: | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in result["prefix_holdouts"]:
        lines.append(
            f"| `{row['cutoff']}` | `{row['selected_policy']}` | `{row['test_copy_hits']}` | "
            f"`{row['test_boundary_bits']:.3f}` | `{row['test_v2_bits']:.3f}` | "
            f"`{row['test_delta_vs_v2']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Controls",
            "",
            f"- Shuffled event-boundary program bits: `{c['shuffled_event_boundaries']['source_boundary_program_bits']:.3f}`.",
            f"- Shuffled event-boundary hits: `{c['shuffled_event_boundaries']['copy_hits']}/{c['shuffled_event_boundaries']['copy_ops']}`.",
            f"- Random boundary hits p95: `{c['random_boundary_control']['random_hits_p95']:.3f}`.",
            f"- Random boundary copy bits p05/p50/p95: `{c['random_boundary_control']['random_bits_p05']:.3f}` / `{c['random_boundary_control']['random_bits_p50']:.3f}` / `{c['random_boundary_control']['random_bits_p95']:.3f}`.",
            "",
            "## Decision",
            "",
            (
                "`PROMOTED_SOURCE_BOUNDARY_PROGRAM`: source intervals reduce the "
                "residual ledger and beat controls."
                if result["summary"]["promoted"]
                else "`source_boundary_candidate_program_not_promoted` as a "
                "generator. Candidate boundary systems explain too few source "
                "intervals, so source/length remain mostly external."
            ),
            "",
            "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        ]
    )
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Final Source-Boundary Candidate Program Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        "This audit tested whether the subchunks missed by the event-aligned chunk "
        "library can instead be generated as intervals between decoder-visible "
        "boundaries in previous material: event/book boundaries, source-side "
        "`prev2` surprisal boundaries, and their unions.",
        "",
        f"The best system is `{s['system']}` with policy `{s['selected_policy']}`. "
        f"It derives `{s['copy_hits']}/{s['copy_ops']}` copy source intervals. "
        f"The program costs `{s['source_boundary_program_bits']:.3f}` bits versus "
        f"`{s['baseline_v2_residual_bits']:.3f}` for v2, a delta of "
        f"`{s['delta_vs_v2_residual_bits']:.3f}` bits. Prefix holdout improves "
        f"v2 in `{s['holdout_splits_improving_v2']}/5` splits.",
        "",
        "## Decision",
        "",
        (
            "`PROMOTED_SOURCE_BOUNDARY_PROGRAM`: this route reduces the external "
            "source/length ledger and passes controls."
            if result["summary"]["promoted"]
            else "`source_boundary_candidate_program_not_promoted`. The tested "
            "source-side boundary systems do not capture enough copy intervals "
            "to become a generator. The current blocker remains subchunk origin: "
            "where the copied interval boundaries come from before content/rank "
            "is paid."
        ),
        "",
        "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_source_boundary_candidate_program_gate.py](../scripts/01_source_boundary_candidate_program_gate.py)",
        "- [01_source_boundary_candidate_program_gate.json](test_results/01_source_boundary_candidate_program_gate.json)",
        "- [01_source_boundary_candidate_program_gate.md](test_results/01_source_boundary_candidate_program_gate.md)",
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
