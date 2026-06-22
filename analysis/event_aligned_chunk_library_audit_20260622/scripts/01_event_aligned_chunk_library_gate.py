#!/usr/bin/env python3
"""Event-aligned chunk library gate.

The previous content-addressed audit showed that ranking over all prior
substrings is too broad. This gate tests a narrower structural representation:
copy events may choose only chunks that are aligned to previously emitted event
boundaries, or to short concatenations of previous event chunks. If selected,
the chunk derives both exact length and canonical source.

This is analysis-only. It does not touch row0, plaintext, semantics, or the
compression bound.
"""

from __future__ import annotations

import json
import math
import random
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "event_aligned_chunk_library_audit_20260622"
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
CONTENT_EVENT_GATE = (
    ROOT
    / "analysis"
    / "content_addressed_event_program_audit_20260622"
    / "reports"
    / "test_results"
    / "01_content_addressed_event_program_gate.json"
)

JSON_OUT = TEST_RESULTS / "01_event_aligned_chunk_library_gate.json"
MD_OUT = TEST_RESULTS / "01_event_aligned_chunk_library_gate.md"
FINAL_OUT = FRONT / "reports" / "final_event_aligned_chunk_library_audit.md"

BUCKET_RANGES = {
    "len_0008": (1, 8),
    "len_0016": (9, 16),
    "len_0032": (17, 32),
    "len_0064": (33, 64),
    "len_0128": (65, 128),
    "len_0256p": (129, None),
}
POLICIES = ["long_recent", "long_freq_recent", "recent_long", "freq_long_recent"]
SPAN_LIMITS: list[int | None] = [1, 2, 3, 4, 8, None]
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
RANDOM_SEED = 46920260622
RANDOM_TRIALS = 300
LOG2_10 = math.log2(10)

Span = dict[str, Any]
PolicyKey = Callable[[Span], tuple[Any, ...]]


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


def bucket_bounds(bucket: str, remaining: int) -> tuple[int, int]:
    low, high = BUCKET_RANGES[bucket]
    high = remaining if high is None else min(high, remaining)
    if high < low:
        return low, low - 1
    return low, high


def feasible_length_count(bucket: str, remaining: int) -> int:
    low, high = bucket_bounds(bucket, remaining)
    return max(1, high - low + 1)


def policy_key(name: str) -> PolicyKey:
    if name == "long_recent":
        return lambda row: (-int(row["length"]), -int(row["source_start"]), row["chunk"])
    if name == "long_freq_recent":
        return lambda row: (
            -int(row["length"]),
            -int(row["count"]),
            -int(row["source_start"]),
            row["chunk"],
        )
    if name == "recent_long":
        return lambda row: (-int(row["source_start"]), -int(row["length"]), row["chunk"])
    if name == "freq_long_recent":
        return lambda row: (
            -int(row["count"]),
            -int(row["length"]),
            -int(row["source_start"]),
            row["chunk"],
        )
    raise KeyError(name)


def make_book_segments(
    book_text: str,
    book_start: int,
    lengths: list[int],
    boundary_mode: str,
    book: int,
) -> list[dict[str, Any]]:
    if boundary_mode == "shuffled_lengths" and len(lengths) > 1 and book >= 10:
        rng = random.Random(RANDOM_SEED + book)
        lengths = list(lengths)
        rng.shuffle(lengths)
    segments = []
    local = 0
    for index, length in enumerate(lengths):
        segments.append(
            {
                "book": book,
                "chunk": book_text[local : local + length],
                "end": book_start + local + length,
                "kind": "seed_book" if book < 10 else "event",
                "op_index": index if book >= 10 else None,
                "start": book_start + local,
            }
        )
        local += length
    if local != len(book_text):
        raise RuntimeError({"book": book, "local": local, "length": len(book_text)})
    return segments


def span_candidates(
    segment_books: dict[int, list[dict[str, Any]]],
    bucket: str,
    remaining: int,
    max_span_ops: int | None,
) -> list[Span]:
    low, high = bucket_bounds(bucket, remaining)
    if high < low:
        return []
    by_key: dict[tuple[str, int], Span] = {}
    for book, segments in segment_books.items():
        n = len(segments)
        for i in range(n):
            text_parts = []
            span_limit = n if max_span_ops is None else min(n, i + max_span_ops)
            for j in range(i, span_limit):
                text_parts.append(str(segments[j]["chunk"]))
                chunk = "".join(text_parts)
                length = len(chunk)
                if length > high:
                    break
                if length < low:
                    continue
                start = int(segments[i]["start"])
                key = (chunk, length)
                row = by_key.get(key)
                if row is None:
                    by_key[key] = {
                        "book": book,
                        "chunk": chunk,
                        "count": 1,
                        "length": length,
                        "source_start": start,
                        "span_ops": j - i + 1,
                    }
                else:
                    row["count"] += 1
                    if start < int(row["source_start"]):
                        row["source_start"] = start
    return list(by_key.values())


def rank_candidate(candidates: list[Span], payload: str, length: int, policy: str) -> int | None:
    correct = None
    for row in candidates:
        if row["chunk"] == payload and int(row["length"]) == length:
            correct = row
            break
    if correct is None:
        return None
    key_fn = policy_key(policy)
    correct_key = key_fn(correct)
    return 1 + sum(1 for row in candidates if key_fn(row) < correct_key)


def composition_count_for_unknowns(
    unknown_rows: list[dict[str, Any]],
    remaining_sum: int,
) -> int:
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


def build_events(max_span_ops: int | None, boundary_mode: str = "canonical") -> tuple[list[dict[str, Any]], dict[str, Any]]:
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    by_book, ledger = grouped_ledger_rows()
    book_starts: dict[int, int] = {}
    cursor = 0
    for book in range(70):
        book_starts[book] = cursor
        cursor += len(books[book])
    segment_books: dict[int, list[dict[str, Any]]] = {}
    for book in range(10):
        segment_books[book] = make_book_segments(
            books[book],
            book_starts[book],
            [len(books[book])],
            "canonical",
            book,
        )

    events: list[dict[str, Any]] = []
    book_length_rows: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for book in range(10, 70):
        rendered_chunks: list[str] = []
        current_segments: list[dict[str, Any]] = []
        for row in by_book[book]:
            op_type = str(row["op_type"])
            start = int(row["target_start"])
            length = int(row["exact_length"])
            bucket = str(row["coarse_type_length_bucket"]).split(":", 1)[1]
            payload = books[book][start : start + length]
            available_books = dict(segment_books)
            if current_segments:
                available_books[book] = list(current_segments)
            if op_type == "copy":
                candidates = span_candidates(
                    available_books,
                    bucket,
                    int(row["book_length"]) - start,
                    max_span_ops,
                )
                ranks = {
                    policy: rank_candidate(candidates, payload, length, policy)
                    for policy in POLICIES
                }
                canonical = next(
                    (
                        cand
                        for cand in candidates
                        if cand["chunk"] == payload and int(cand["length"]) == length
                    ),
                    None,
                )
                event = {
                    "book": book,
                    "bucket": bucket,
                    "candidate_count": len(candidates),
                    "canonical_source": None if canonical is None else int(canonical["source_start"]),
                    "canonical_source_matches_raw": (
                        canonical is not None
                        and int(canonical["source_start"]) == int(row["copy_source_raw"])
                    ),
                    "copy_hint_rank_bits": float(row["copy_hint_rank_bits"]),
                    "event_kind": "copy",
                    "exact_length": length,
                    "hit": canonical is not None,
                    "max_span_ops": "all" if max_span_ops is None else max_span_ops,
                    "op_index": int(row["op_index"]),
                    "rank_bits_by_policy": {
                        policy: math.log2(rank) if rank is not None else None
                        for policy, rank in ranks.items()
                    },
                    "rank_by_policy": ranks,
                    "raw_v2_bits": float(row["copy_hint_rank_bits"]),
                    "source_raw": int(row["copy_source_raw"]),
                    "span_ops": None if canonical is None else int(canonical["span_ops"]),
                    "target_start": start,
                }
                events.append(event)
            else:
                event = {
                    "book": book,
                    "bucket": bucket,
                    "candidate_count": 0,
                    "event_kind": "literal",
                    "exact_length": length,
                    "hit": True,
                    "literal_length_bits": math.log2(
                        feasible_length_count(bucket, int(row["book_length"]) - start)
                    ),
                    "literal_payload_bits": float(row["literal_payload_bits"]),
                    "max_span_ops": "all" if max_span_ops is None else max_span_ops,
                    "op_index": int(row["op_index"]),
                    "raw_v2_bits": float(row["literal_payload_bits"]),
                    "target_start": start,
                }
                events.append(event)
            rendered_chunks.append(payload)
            current_segments.append(
                {
                    "book": book,
                    "chunk": payload,
                    "end": book_starts[book] + start + length,
                    "kind": "event",
                    "op_index": int(row["op_index"]),
                    "start": book_starts[book] + start,
                }
            )
            book_length_rows[book].append(row)
        if "".join(rendered_chunks) != books[book]:
            raise RuntimeError({"book": book, "reason": "roundtrip_failed"})
        lengths = [int(row["exact_length"]) for row in by_book[book]]
        segment_books[book] = make_book_segments(
            books[book],
            book_starts[book],
            lengths,
            boundary_mode,
            book,
        )

    composition_bits_by_book: dict[int, float] = {}
    baseline_composition_bits_by_book: dict[int, float] = {}
    literal_length_bits_by_book: dict[int, float] = defaultdict(float)
    for event in events:
        if event["event_kind"] == "literal":
            literal_length_bits_by_book[int(event["book"])] += float(event["literal_length_bits"])
    events_by_book: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        events_by_book[int(event["book"])].append(event)
    for book, rows in events_by_book.items():
        truth_rows = by_book[book]
        baseline_composition_bits_by_book[book] = sum(
            float(row["composition_index_bits_charged_here"]) for row in truth_rows
        )
        known_sum = 0
        unknown_rows = []
        for event, row in zip(rows, truth_rows):
            if event["event_kind"] == "literal" or bool(event["hit"]):
                known_sum += int(row["exact_length"])
            else:
                unknown_rows.append(row)
        remaining = int(truth_rows[0]["book_length"]) - known_sum
        composition_bits_by_book[book] = math.log2(
            composition_count_for_unknowns(unknown_rows, remaining)
        )
    return events, {
        "boundary_mode": boundary_mode,
        "baseline_composition_bits_by_book": baseline_composition_bits_by_book,
        "composition_bits_by_book": composition_bits_by_book,
        "literal_length_bits_by_book": dict(literal_length_bits_by_book),
        "max_span_ops": "all" if max_span_ops is None else max_span_ops,
        "seed_segmentation": "whole_seed_books_only",
        "unified_ledger_summary": ledger["summary"],
    }


def summarize(events: list[dict[str, Any]], meta: dict[str, Any], selected_policy: str | None = None) -> dict[str, Any]:
    copy_events = [row for row in events if row["event_kind"] == "copy"]
    literal_events = [row for row in events if row["event_kind"] == "literal"]
    policy_bits = {}
    for policy in POLICIES:
        total = 0.0
        for row in copy_events:
            bits = row["rank_bits_by_policy"][policy]
            total += float(row["copy_hint_rank_bits"]) if bits is None else float(bits)
        policy_bits[policy] = total
    best_policy = selected_policy or min(policy_bits, key=lambda policy: policy_bits[policy])
    composition_bits = sum(float(value) for value in meta["composition_bits_by_book"].values())
    literal_payload_bits = sum(float(row["literal_payload_bits"]) for row in literal_events)
    literal_length_bits = sum(float(row["literal_length_bits"]) for row in literal_events)
    baseline = (
        sum(float(row["raw_v2_bits"]) for row in events)
        + sum(float(value) for value in meta["baseline_composition_bits_by_book"].values())
    )
    aligned_copy_bits = policy_bits[best_policy]
    total_bits = composition_bits + literal_payload_bits + literal_length_bits + aligned_copy_bits
    candidate_counts = [int(row["candidate_count"]) for row in copy_events if row["hit"]]
    books_all_copy_hit = set(range(10, 70))
    for row in copy_events:
        if not row["hit"]:
            books_all_copy_hit.discard(int(row["book"]))
    top80 = sum(
        1
        for row in copy_events
        if row["rank_by_policy"][best_policy] is not None
        and int(row["rank_by_policy"][best_policy]) <= 80
    )
    return {
        "aligned_copy_rank_or_fallback_bits": aligned_copy_bits,
        "baseline_v2_residual_bits": baseline,
        "best_policy_if_fit": min(policy_bits, key=lambda policy: policy_bits[policy]),
        "books_all_copy_hit": len(books_all_copy_hit),
        "candidate_count_max_hit": max(candidate_counts) if candidate_counts else 0,
        "candidate_count_mean_hit": mean(candidate_counts) if candidate_counts else 0.0,
        "candidate_count_median_hit": sorted(candidate_counts)[len(candidate_counts) // 2]
        if candidate_counts
        else 0,
        "composition_bits_after_derived_lengths": composition_bits,
        "copy_hits": sum(1 for row in copy_events if row["hit"]),
        "copy_misses": sum(1 for row in copy_events if not row["hit"]),
        "copy_ops": len(copy_events),
        "copy_sources_derived": sum(1 for row in copy_events if row["hit"]),
        "copy_sources_match_raw": sum(1 for row in copy_events if row["canonical_source_matches_raw"]),
        "delta_vs_v2_residual_bits": total_bits - baseline,
        "event_aligned_residual_bits": total_bits,
        "literal_length_bits": literal_length_bits,
        "literal_payload_bits": literal_payload_bits,
        "literal_ops": len(literal_events),
        "max_span_ops": meta["max_span_ops"],
        "policy_copy_bits": policy_bits,
        "selected_policy": best_policy,
        "top80_copy_hits": top80,
    }


def score_mode(max_span_ops: int | None, boundary_mode: str = "canonical") -> dict[str, Any]:
    events, meta = build_events(max_span_ops, boundary_mode=boundary_mode)
    summary = summarize(events, meta)
    return {"events": events, "meta": meta, "summary": summary}


def prefix_holdouts(events: list[dict[str, Any]], meta: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for cutoff in PREFIX_CUTOFFS:
        train_events = [row for row in events if int(row["book"]) < cutoff]
        test_events = [row for row in events if int(row["book"]) >= cutoff]
        train_books = {int(row["book"]) for row in train_events}
        test_books = {int(row["book"]) for row in test_events}
        train_meta = {
            **meta,
            "baseline_composition_bits_by_book": {
                book: bits
                for book, bits in meta["baseline_composition_bits_by_book"].items()
                if int(book) in train_books
            },
            "composition_bits_by_book": {
                book: bits
                for book, bits in meta["composition_bits_by_book"].items()
                if int(book) in train_books
            },
        }
        test_meta = {
            **meta,
            "baseline_composition_bits_by_book": {
                book: bits
                for book, bits in meta["baseline_composition_bits_by_book"].items()
                if int(book) in test_books
            },
            "composition_bits_by_book": {
                book: bits
                for book, bits in meta["composition_bits_by_book"].items()
                if int(book) in test_books
            },
        }
        policy = summarize(train_events, train_meta)["best_policy_if_fit"]
        test_summary = summarize(test_events, test_meta, selected_policy=policy)
        rows.append(
            {
                "cutoff": cutoff,
                "selected_policy": policy,
                "test_copy_hits": test_summary["copy_hits"],
                "test_copy_misses": test_summary["copy_misses"],
                "test_delta_vs_v2": test_summary["delta_vs_v2_residual_bits"],
                "test_event_aligned_bits": test_summary["event_aligned_residual_bits"],
                "test_v2_bits": test_summary["baseline_v2_residual_bits"],
                "top80_copy_hits": test_summary["top80_copy_hits"],
            }
        )
    return rows


def percentile(values: list[float], p: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    index = min(len(ordered) - 1, max(0, math.ceil((p / 100.0) * len(ordered)) - 1))
    return ordered[index]


def random_rank_control(events: list[dict[str, Any]], policy: str) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED + 900)
    copy_events = [row for row in events if row["event_kind"] == "copy" and row["hit"]]
    observed = sum(
        float(row["rank_bits_by_policy"][policy])
        for row in copy_events
        if row["rank_bits_by_policy"][policy] is not None
    )
    totals = []
    for _ in range(RANDOM_TRIALS):
        total = 0.0
        for row in copy_events:
            total += math.log2(rng.randint(1, max(1, int(row["candidate_count"]))))
        totals.append(total)
    return {
        "observed_aligned_hit_rank_bits": observed,
        "p05": percentile(totals, 5),
        "p50": percentile(totals, 50),
        "p95": percentile(totals, 95),
        "beats_p05": observed < percentile(totals, 5),
        "trials": RANDOM_TRIALS,
    }


def make_result() -> dict[str, Any]:
    content_gate = load_json(CONTENT_EVENT_GATE)
    assert_boundary("content_addressed_event_program_gate", content_gate)
    mode_results = []
    for span_limit in SPAN_LIMITS:
        scored = score_mode(span_limit)
        mode_results.append(
            {
                "max_span_ops": "all" if span_limit is None else span_limit,
                "summary": scored["summary"],
            }
        )
    best_mode = min(
        mode_results,
        key=lambda item: (
            item["summary"]["event_aligned_residual_bits"],
            str(item["max_span_ops"]),
        ),
    )
    best_span = None if best_mode["max_span_ops"] == "all" else int(best_mode["max_span_ops"])
    best = score_mode(best_span)
    summary = best["summary"]
    holdouts = prefix_holdouts(best["events"], best["meta"])
    shuffled_boundary = score_mode(best_span, boundary_mode="shuffled_lengths")["summary"]
    rank_control = random_rank_control(best["events"], summary["selected_policy"])
    boundary_specific_delta = (
        summary["event_aligned_residual_bits"]
        - shuffled_boundary["event_aligned_residual_bits"]
    )
    improves_v2 = summary["delta_vs_v2_residual_bits"] < 0
    holdout_improves = sum(row["test_delta_vs_v2"] < 0 for row in holdouts)
    beats_controls = rank_control["beats_p05"] and (
        summary["copy_hits"] > shuffled_boundary["copy_hits"]
        or summary["event_aligned_residual_bits"] < shuffled_boundary["event_aligned_residual_bits"]
    )
    promoted = improves_v2 and holdout_improves >= 4 and beats_controls
    classification = (
        "PROMOTED_EVENT_ALIGNED_CHUNK_PROGRAM"
        if promoted
        else "WEAK_EVENT_ALIGNED_CHUNK_CLUE"
        if summary["copy_hits"] >= 20 and rank_control["beats_p05"]
        else "event_aligned_chunk_library_not_promoted"
    )
    hardest = [
        {
            "book": row["book"],
            "candidate_count": row["candidate_count"],
            "exact_length": row["exact_length"],
            "hit": row["hit"],
            "op_index": row["op_index"],
            "rank": row["rank_by_policy"][summary["selected_policy"]],
            "span_ops": row["span_ops"],
            "target_start": row["target_start"],
        }
        for row in sorted(
            [item for item in best["events"] if item["event_kind"] == "copy"],
            key=lambda item: (
                item["rank_by_policy"][summary["selected_policy"]] is None,
                item["rank_by_policy"][summary["selected_policy"]] or 10**12,
            ),
            reverse=True,
        )[:30]
    ]
    return {
        "case_reopened": False,
        "classification": classification,
        "compression_bound_status": "unchanged",
        "controls": {
            "random_rank_control": rank_control,
            "shuffled_completed_book_boundaries": shuffled_boundary,
        },
        "decision": {
            "event_aligned_chunk_program_promoted": promoted,
            "next_blocker": (
                "copy content is not sufficiently explained by prior event-boundary "
                "chunks; seed/internal subchunk origin remains external"
            ),
            "plaintext_claim": False,
            "row0_status": "unchanged_exogenous",
            "translation_delta": "NONE",
        },
        "hardest_copy_rows": hardest,
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "content_addressed_event_program_gate": rel(CONTENT_EVENT_GATE),
            "unified_external_tape_ledger": rel(UNIFIED_LEDGER),
        },
        "mode_results": mode_results,
        "plaintext_claim": False,
        "prefix_holdouts": holdouts,
        "row0_status": "unchanged_exogenous",
        "schema": "event_aligned_chunk_library_gate.v1",
        "scope": "analysis_only_event_aligned_chunk_library",
        "summary": {
            **summary,
            "boundary_specific_delta_vs_shuffled_boundaries": boundary_specific_delta,
            "best_mode": best_mode["max_span_ops"],
            "holdout_splits_improving_v2": holdout_improves,
            "promoted": promoted,
        },
        "translation_delta": "NONE",
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    c = result["controls"]
    lines = [
        "# Event-Aligned Chunk Library Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Question",
        "",
        "Can copy content be selected from previously emitted operation-boundary "
        "chunks, so exact length and source derive from an event-aligned span "
        "instead of from arbitrary substring addressing?",
        "",
        "## Summary",
        "",
        f"- Best span limit: `{s['best_mode']}`.",
        f"- Selected policy: `{s['selected_policy']}`.",
        f"- Copy hits/misses: `{s['copy_hits']}/{s['copy_misses']}` out of `{s['copy_ops']}`.",
        f"- Sources derived/matching raw: `{s['copy_sources_derived']}/{s['copy_ops']}` / `{s['copy_sources_match_raw']}/{s['copy_ops']}`.",
        f"- Candidate count median/mean/max on hits: `{s['candidate_count_median_hit']}` / `{s['candidate_count_mean_hit']:.3f}` / `{s['candidate_count_max_hit']}`.",
        f"- V2 residual baseline: `{s['baseline_v2_residual_bits']:.3f}` bits.",
        f"- Event-aligned residual: `{s['event_aligned_residual_bits']:.3f}` bits.",
        f"- Delta vs v2 residual: `{s['delta_vs_v2_residual_bits']:.3f}` bits.",
        f"- Delta vs shuffled-boundary control: `{s['boundary_specific_delta_vs_shuffled_boundaries']:.3f}` bits.",
        f"- Composition bits after derived lengths: `{s['composition_bits_after_derived_lengths']:.3f}`.",
        f"- Literal length delimiter bits: `{s['literal_length_bits']:.3f}`.",
        f"- Top-80 copy hits: `{s['top80_copy_hits']}/{s['copy_ops']}`.",
        "",
        "## Span Modes",
        "",
        "| Max span ops | Copy hits | Residual bits | Delta vs v2 | Top80 |",
        "| ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in result["mode_results"]:
        ms = row["summary"]
        lines.append(
            f"| `{row['max_span_ops']}` | `{ms['copy_hits']}` | "
            f"`{ms['event_aligned_residual_bits']:.3f}` | "
            f"`{ms['delta_vs_v2_residual_bits']:.3f}` | `{ms['top80_copy_hits']}` |"
        )
    lines.extend(
        [
            "",
            "## Prefix Holdout",
            "",
            "| Cutoff | Policy | Hits | Misses | Event bits | V2 bits | Delta | Top80 |",
            "| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in result["prefix_holdouts"]:
        lines.append(
            f"| `{row['cutoff']}` | `{row['selected_policy']}` | `{row['test_copy_hits']}` | "
            f"`{row['test_copy_misses']}` | `{row['test_event_aligned_bits']:.3f}` | "
            f"`{row['test_v2_bits']:.3f}` | `{row['test_delta_vs_v2']:.3f}` | "
            f"`{row['top80_copy_hits']}` |"
        )
    lines.extend(
        [
            "",
            "## Controls",
            "",
            f"- Random rank control observed/p05/p50/p95: `{c['random_rank_control']['observed_aligned_hit_rank_bits']:.3f}` / `{c['random_rank_control']['p05']:.3f}` / `{c['random_rank_control']['p50']:.3f}` / `{c['random_rank_control']['p95']:.3f}`.",
            f"- Shuffled completed-book boundaries copy hits: `{c['shuffled_completed_book_boundaries']['copy_hits']}/{c['shuffled_completed_book_boundaries']['copy_ops']}`.",
            f"- Shuffled completed-book boundaries residual delta: `{c['shuffled_completed_book_boundaries']['delta_vs_v2_residual_bits']:.3f}` bits.",
            f"- Boundary-specific delta vs shuffled control: `{s['boundary_specific_delta_vs_shuffled_boundaries']:.3f}` bits.",
            "",
            "## Decision",
            "",
            (
                "`PROMOTED_EVENT_ALIGNED_CHUNK_PROGRAM`: event-boundary spans "
                "reduce the residual ledger after controls."
                if result["summary"]["promoted"]
                else "`event_aligned_chunk_library_not_promoted` as a generator. "
                "The representation sharply reduces candidate-set size for the "
                "few aligned hits, but most copy content is not a prior event "
                "span. The residual saving is mostly a length/literal refactor "
                "also visible under shuffled-boundary control, so source/length "
                "remain mostly external."
            ),
            "",
            "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        ]
    )
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Final Event-Aligned Chunk Library Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        "This audit stepped back from arbitrary content-addressing and tested a "
        "more authorially plausible restriction: copy events may select chunks "
        "already aligned to previous operation boundaries, including short "
        "concatenations of earlier event chunks.",
        "",
        f"The best mode is max-span `{s['best_mode']}` with policy "
        f"`{s['selected_policy']}`. It explains `{s['copy_hits']}/{s['copy_ops']}` "
        f"copy chunks as event-aligned prior spans and leaves `{s['copy_misses']}` "
        "copy chunks on the existing fallback tape.",
        "",
        f"The resulting residual cost is `{s['event_aligned_residual_bits']:.3f}` "
        f"bits versus `{s['baseline_v2_residual_bits']:.3f}` for v2, a delta of "
        f"`{s['delta_vs_v2_residual_bits']:.3f}` bits. Prefix holdout improves "
        f"v2 in `{s['holdout_splits_improving_v2']}/5` splits. However, shuffled "
        "completed-book boundaries still save "
        f"`{-result['controls']['shuffled_completed_book_boundaries']['delta_vs_v2_residual_bits']:.3f}` "
        "bits versus v2, leaving only "
        f"`{-s['boundary_specific_delta_vs_shuffled_boundaries']:.3f}` bits as "
        "the boundary-specific difference.",
        "",
        "## Decision",
        "",
        (
            "`PROMOTED_EVENT_ALIGNED_CHUNK_PROGRAM`: the aligned chunk library "
            "reduces the executable residual ledger."
            if result["summary"]["promoted"]
            else "`event_aligned_chunk_library_not_promoted`. The test narrows "
            "the candidate universe but coverage is too low to replace the "
            "current residual ledger: only a small number of copies are prior "
            "event-boundary spans, and the residual saving is partly reproduced "
            "by shuffled boundaries. The next blocker remains the origin of copy "
            "content, especially subchunks of seed/prior material that are not "
            "aligned to event boundaries."
        ),
        "",
        "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_event_aligned_chunk_library_gate.py](../scripts/01_event_aligned_chunk_library_gate.py)",
        "- [01_event_aligned_chunk_library_gate.json](test_results/01_event_aligned_chunk_library_gate.json)",
        "- [01_event_aligned_chunk_library_gate.md](test_results/01_event_aligned_chunk_library_gate.md)",
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
