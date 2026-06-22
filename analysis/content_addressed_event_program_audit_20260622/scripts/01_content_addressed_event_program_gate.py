#!/usr/bin/env python3
"""Content-addressed event program gate.

This audit replaces separated exact-length composition and copy-source/hint
fields with a single event rank over prior content chunks. Given the promoted
online x64 coarse-control stream, a copy event chooses a prior chunk inside the
coarse length bucket; length and canonical source are then derived from that
chunk. Literal events consume an innovation chunk and pay its length delimiter
inside the coarse bucket plus digit payload.

The gate is analysis-only. It does not touch row0, plaintext, semantics, or the
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
FRONT = ROOT / "analysis" / "content_addressed_event_program_audit_20260622"
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
ONLINE_X64_FINAL = (
    ROOT
    / "analysis"
    / "online_x64_coarse_control_program_audit_20260622"
    / "reports"
    / "final_online_x64_coarse_control_program_audit.md"
)
RESIDUAL_COUPLING_FINAL = (
    ROOT
    / "analysis"
    / "executable_v2_residual_coupling_audit_20260622"
    / "reports"
    / "final_executable_v2_residual_coupling_audit.md"
)
REMAINING_TAPE_FINAL = (
    ROOT
    / "analysis"
    / "executable_v2_remaining_tape_coupling_audit_20260622"
    / "reports"
    / "final_executable_v2_remaining_tape_coupling_audit.md"
)

JSON_OUT = TEST_RESULTS / "01_content_addressed_event_program_gate.json"
MD_OUT = TEST_RESULTS / "01_content_addressed_event_program_gate.md"
FINAL_OUT = FRONT / "reports" / "final_content_addressed_event_program_audit.md"

BUCKET_RANGES = {
    "len_0008": (1, 8),
    "len_0016": (9, 16),
    "len_0032": (17, 32),
    "len_0064": (33, 64),
    "len_0128": (65, 128),
    "len_0256p": (129, None),
}
POLICIES = [
    "long_freq_recent",
    "freq_recent_long",
    "recent_long_freq",
    "short_freq_recent",
]
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
TOP_KS = [1, 8, 20, 80, 256, 1024]
RANDOM_SEED = 46920260622
RANDOM_TRIALS = 300
LOG2_10 = math.log2(10)
ONLINE_X64_COARSE_BITS = 876.412

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


def bucket_bounds(bucket: str, upper_bound: int) -> tuple[int, int]:
    low, high = BUCKET_RANGES[bucket]
    high = upper_bound if high is None else min(high, upper_bound)
    if high < low:
        return low, low - 1
    return low, high


def feasible_literal_lengths(bucket: str, remaining: int) -> int:
    low, high = bucket_bounds(bucket, remaining)
    return max(0, high - low + 1)


def policy_key(name: str) -> PolicyKey:
    if name == "long_freq_recent":
        return lambda row, available_len: (
            -int(row["length"]),
            -int(row["count"]),
            available_len - (int(row["max_source"]) + int(row["length"])),
            row["chunk"],
        )
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
    if name == "short_freq_recent":
        return lambda row, available_len: (
            int(row["length"]),
            -int(row["count"]),
            available_len - (int(row["max_source"]) + int(row["length"])),
            row["chunk"],
        )
    raise KeyError(name)


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


def rank_for_payload(
    candidates: list[ChunkRow],
    payload: str,
    length: int,
    available_len: int,
    policy: str,
) -> int | None:
    correct = None
    for row in candidates:
        if row["chunk"] == payload and int(row["length"]) == length:
            correct = row
            break
    if correct is None:
        return None
    key_fn = policy_key(policy)
    correct_key = key_fn(correct, available_len)
    return 1 + sum(1 for row in candidates if key_fn(row, available_len) < correct_key)


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


def build_event_rows(material_mode: str = "canonical") -> tuple[list[dict[str, Any]], dict[str, Any]]:
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    by_book, ledger = grouped_ledger_rows()
    prior_books: list[int] = list(range(10))
    emitted_books = {book: books[book] for book in range(10)}
    events: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    order = list(range(10, 70))
    if material_mode == "permuted_book_order":
        rng = random.Random(RANDOM_SEED + 17)
        rng.shuffle(order)
    for book in order:
        rendered: list[str] = []
        if material_mode == "reverse_previous_books":
            material_books = list(reversed(prior_books))
        else:
            material_books = list(prior_books)
        previous_material = "".join(emitted_books[idx] for idx in material_books)
        for row in by_book[book]:
            op_type = str(row["op_type"])
            start = int(row["target_start"])
            length = int(row["exact_length"])
            bucket = str(row["coarse_type_length_bucket"]).split(":", 1)[1]
            remaining = int(row["book_length"]) - start
            available = previous_material + "".join(rendered)
            if material_mode == "shuffled_previous_digits":
                rng = random.Random(RANDOM_SEED + book * 1000 + int(row["op_index"]))
                chars = list(available)
                rng.shuffle(chars)
                available = "".join(chars)
            if op_type == "literal":
                payload = str(row["literal_payload"])
                length_options = feasible_literal_lengths(bucket, remaining)
                length_bits = math.log2(max(1, length_options))
                event = {
                    "book": book,
                    "canonical_source": None,
                    "canonical_source_matches_raw": None,
                    "candidate_count": 0,
                    "coarse_type_length_bucket": row["coarse_type_length_bucket"],
                    "copy_source_raw": None,
                    "event_kind": "literal",
                    "event_rank_bits_by_policy": {policy: 0.0 for policy in POLICIES},
                    "event_rank_by_policy": {policy: None for policy in POLICIES},
                    "exact_length": length,
                    "fields_derived": ["target_start", "op_type", "length_bucket"],
                    "fields_paid": ["literal_length_within_bucket", "literal_payload_digits"],
                    "length_derived_from_content_event": False,
                    "literal_length_bits": length_bits,
                    "literal_payload": payload,
                    "literal_payload_bits": float(row["literal_payload_bits"]),
                    "op_index": int(row["op_index"]),
                    "raw_v2_bits": float(row["composition_index_bits_charged_here"])
                    + float(row["literal_payload_bits"]),
                    "source_derived_from_content": False,
                    "target_start": start,
                    "target_text_dependency": ["literal_payload_is_target_digits"],
                    "total_content_event_bits_by_policy": {
                        policy: length_bits + float(row["literal_payload_bits"])
                        for policy in POLICIES
                    },
                }
                events.append(event)
                rendered.append(payload)
                continue
            low, high = bucket_bounds(bucket, min(len(available), remaining))
            payload = books[book][start : start + length]
            candidates = [] if high < low else unique_chunks_in_bucket(available, low, high)
            ranks = {
                policy: rank_for_payload(candidates, payload, length, len(available), policy)
                for policy in POLICIES
            }
            if any(rank is None for rank in ranks.values()):
                errors.append(
                    {
                        "book": book,
                        "op_index": int(row["op_index"]),
                        "material_mode": material_mode,
                        "reason": "target_chunk_missing_from_candidate_set",
                    }
                )
            canonical_source = available.find(payload)
            raw_source = int(row["copy_source_raw"])
            event = {
                "book": book,
                "canonical_source": canonical_source if canonical_source >= 0 else None,
                "canonical_source_matches_raw": canonical_source == raw_source,
                "candidate_count": len(candidates),
                "coarse_type_length_bucket": row["coarse_type_length_bucket"],
                "copy_source_raw": raw_source,
                "event_kind": "copy",
                "event_rank_bits_by_policy": {
                    policy: math.log2(rank) if rank is not None else math.log2(max(1, len(candidates) + 1))
                    for policy, rank in ranks.items()
                },
                "event_rank_by_policy": ranks,
                "exact_length": length,
                "fields_derived": [
                    "target_start",
                    "op_type",
                    "length_bucket",
                    "exact_length_from_selected_chunk",
                    "canonical_source_from_selected_chunk",
                ],
                "fields_paid": ["content_event_rank"],
                "length_derived_from_content_event": True,
                "literal_length_bits": 0.0,
                "literal_payload": None,
                "literal_payload_bits": 0.0,
                "op_index": int(row["op_index"]),
                "raw_v2_bits": float(row["composition_index_bits_charged_here"])
                + float(row["copy_hint_rank_bits"]),
                "source_derived_from_content": canonical_source >= 0,
                "target_start": start,
                "target_text_dependency": ["target_chunk_used_to_measure_content_rank"],
                "total_content_event_bits_by_policy": {
                    policy: math.log2(rank) if rank is not None else math.log2(max(1, len(candidates) + 1))
                    for policy, rank in ranks.items()
                },
                "v2_copy_hint_rank_bits": float(row["copy_hint_rank_bits"]),
            }
            events.append(event)
            rendered.append(payload)
        rendered_book = "".join(rendered)
        if rendered_book != books[book]:
            errors.append(
                {
                    "book": book,
                    "material_mode": material_mode,
                    "reason": "rendered_book_mismatch",
                    "rendered_length": len(rendered_book),
                    "expected_length": len(books[book]),
                }
            )
        emitted_books[book] = rendered_book
        prior_books.append(book)
    events.sort(key=lambda item: (int(item["book"]), int(item["op_index"])))
    return events, {
        "errors": errors,
        "material_mode": material_mode,
        "processed_order": order,
        "roundtrip_books": sum(
            1 for book in range(10, 70) if emitted_books.get(book) == books[book]
        ),
    }


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, math.ceil((p / 100.0) * len(ordered)) - 1))
    return ordered[index]


def summarize(events: list[dict[str, Any]], selected_policy: str | None = None) -> dict[str, Any]:
    copy_events = [row for row in events if row["event_kind"] == "copy"]
    literal_events = [row for row in events if row["event_kind"] == "literal"]
    policy_copy_bits = {
        policy: sum(float(row["event_rank_bits_by_policy"][policy]) for row in copy_events)
        for policy in POLICIES
    }
    policy_total_bits = {
        policy: sum(float(row["total_content_event_bits_by_policy"][policy]) for row in events)
        for policy in POLICIES
    }
    best_policy = selected_policy or min(policy_total_bits, key=lambda policy: policy_total_bits[policy])
    candidate_counts = [int(row["candidate_count"]) for row in copy_events]
    baseline_bits = sum(float(row["raw_v2_bits"]) for row in events)
    literal_bits = sum(float(row["literal_payload_bits"]) for row in literal_events)
    literal_length_bits = sum(float(row["literal_length_bits"]) for row in literal_events)
    content_copy_bits = policy_copy_bits[best_policy]
    total_bits = policy_total_bits[best_policy]
    topk_hits = {
        str(k): sum(
            1
            for row in copy_events
            if row["event_rank_by_policy"][best_policy] is not None
            and int(row["event_rank_by_policy"][best_policy]) <= k
        )
        for k in TOP_KS
    }
    books_with_all_copy_rank1 = set(range(10, 70))
    for row in copy_events:
        if row["event_rank_by_policy"][best_policy] != 1:
            books_with_all_copy_rank1.discard(int(row["book"]))
    nontrivial_books = {
        int(row["book"])
        for row in events
        if row["event_kind"] == "copy" or int(row["exact_length"]) > 8
    }
    return {
        "baseline_residual_bits_replaced": baseline_bits,
        "best_policy_if_fit": min(policy_total_bits, key=lambda policy: policy_total_bits[policy]),
        "books_all_copy_rank1": len(books_with_all_copy_rank1),
        "books_all_copy_rank1_nontrivial": len(books_with_all_copy_rank1 & nontrivial_books),
        "candidate_count_max": max(candidate_counts) if candidate_counts else 0,
        "candidate_count_mean": mean(candidate_counts) if candidate_counts else 0.0,
        "candidate_count_median": sorted(candidate_counts)[len(candidate_counts) // 2]
        if candidate_counts
        else 0,
        "content_copy_event_rank_bits": content_copy_bits,
        "content_event_delta_vs_v2_residual_bits": total_bits - baseline_bits,
        "content_event_residual_bits": total_bits,
        "copy_ops": len(copy_events),
        "literal_event_bits": literal_bits + literal_length_bits,
        "literal_length_bits": literal_length_bits,
        "literal_ops": len(literal_events),
        "literal_payload_bits": literal_bits,
        "ops": len(events),
        "policy_copy_rank_bits": policy_copy_bits,
        "policy_total_event_bits": policy_total_bits,
        "selected_policy": best_policy,
        "source_derived_copy_ops": sum(1 for row in copy_events if row["source_derived_from_content"]),
        "source_matches_raw_copy_ops": sum(1 for row in copy_events if row["canonical_source_matches_raw"]),
        "topk_hits": topk_hits,
        "v2_copy_hint_bits": sum(float(row.get("v2_copy_hint_rank_bits", 0.0)) for row in copy_events),
        "v2_total_with_online_coarse_excluding_seed": ONLINE_X64_COARSE_BITS + baseline_bits,
        "new_total_with_online_coarse_excluding_seed": ONLINE_X64_COARSE_BITS + total_bits,
    }


def prefix_holdouts(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for cutoff in PREFIX_CUTOFFS:
        train = [row for row in events if int(row["book"]) < cutoff]
        test = [row for row in events if int(row["book"]) >= cutoff]
        train_summary = summarize(train)
        policy = train_summary["best_policy_if_fit"]
        test_summary = summarize(test, selected_policy=policy)
        rows.append(
            {
                "cutoff": cutoff,
                "selected_policy": policy,
                "test_baseline_bits": test_summary["baseline_residual_bits_replaced"],
                "test_content_event_bits": test_summary["content_event_residual_bits"],
                "test_delta_vs_v2": test_summary["content_event_delta_vs_v2_residual_bits"],
                "test_copy_ops": test_summary["copy_ops"],
                "test_top80_hits": test_summary["topk_hits"]["80"],
            }
        )
    return rows


def same_multiset_chunk_control(events: list[dict[str, Any]], selected_policy: str) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED + 101)
    copy_events = [row for row in events if row["event_kind"] == "copy"]
    ranks_by_bucket: dict[str, list[int]] = defaultdict(list)
    counts_by_bucket: dict[str, list[int]] = defaultdict(list)
    for row in copy_events:
        rank = row["event_rank_by_policy"][selected_policy]
        if rank is not None:
            ranks_by_bucket[str(row["coarse_type_length_bucket"])].append(int(rank))
        counts_by_bucket[str(row["coarse_type_length_bucket"])].append(max(1, int(row["candidate_count"])))
    totals = []
    for _ in range(RANDOM_TRIALS):
        total = 0.0
        for row in copy_events:
            bucket = str(row["coarse_type_length_bucket"])
            rank_pool = ranks_by_bucket.get(bucket) or [max(1, int(row["candidate_count"]))]
            # Same multiset of observed event ranks within bucket, assigned to
            # different event sites. This preserves chunk difficulty distribution
            # but breaks site alignment.
            rank = rng.choice(rank_pool)
            total += math.log2(max(1, rank))
        totals.append(total)
    observed = sum(
        float(row["event_rank_bits_by_policy"][selected_policy]) for row in copy_events
    )
    return {
        "observed_copy_rank_bits": observed,
        "p05": percentile(totals, 5),
        "p50": percentile(totals, 50),
        "p95": percentile(totals, 95),
        "beats_p05": observed < percentile(totals, 5),
        "trials": RANDOM_TRIALS,
    }


def random_rank_control(events: list[dict[str, Any]], selected_policy: str) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED + 202)
    copy_events = [row for row in events if row["event_kind"] == "copy"]
    totals = []
    for _ in range(RANDOM_TRIALS):
        total = 0.0
        for row in copy_events:
            total += math.log2(rng.randint(1, max(1, int(row["candidate_count"]))))
        totals.append(total)
    observed = sum(
        float(row["event_rank_bits_by_policy"][selected_policy]) for row in copy_events
    )
    return {
        "observed_copy_rank_bits": observed,
        "p05": percentile(totals, 5),
        "p50": percentile(totals, 50),
        "p95": percentile(totals, 95),
        "beats_p05": observed < percentile(totals, 5),
        "trials": RANDOM_TRIALS,
    }


def material_availability_control(mode: str) -> dict[str, Any]:
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    by_book, _ledger = grouped_ledger_rows()
    prior_books: list[int] = list(range(10))
    emitted_books = {book: books[book] for book in range(10)}
    order = list(range(10, 70))
    if mode == "permuted_book_order":
        rng = random.Random(RANDOM_SEED + 17)
        rng.shuffle(order)
    copy_ops = 0
    available_copy_ops = 0
    missing_copy_ops = 0
    exact_books = 0
    first_missing: list[dict[str, Any]] = []
    for book in order:
        rendered: list[str] = []
        material_books = list(reversed(prior_books)) if mode == "reverse_previous_books" else list(prior_books)
        previous_material = "".join(emitted_books[idx] for idx in material_books)
        for row in by_book[book]:
            op_type = str(row["op_type"])
            start = int(row["target_start"])
            length = int(row["exact_length"])
            available = previous_material + "".join(rendered)
            if mode == "shuffled_previous_digits":
                rng = random.Random(RANDOM_SEED + book * 1000 + int(row["op_index"]))
                chars = list(available)
                rng.shuffle(chars)
                available = "".join(chars)
            if op_type == "literal":
                rendered.append(str(row["literal_payload"]))
                continue
            copy_ops += 1
            payload = books[book][start : start + length]
            if available.find(payload) >= 0:
                available_copy_ops += 1
            else:
                missing_copy_ops += 1
                if len(first_missing) < 12:
                    first_missing.append(
                        {
                            "book": book,
                            "op_index": int(row["op_index"]),
                            "length": length,
                            "mode": mode,
                            "target_start": start,
                        }
                    )
            rendered.append(payload)
        rendered_book = "".join(rendered)
        if rendered_book == books[book]:
            exact_books += 1
        emitted_books[book] = rendered_book
        prior_books.append(book)
    return {
        "material_mode": mode,
        "copy_ops": copy_ops,
        "target_content_available_copy_ops": available_copy_ops,
        "target_content_missing_copy_ops": missing_copy_ops,
        "first_missing": first_missing,
        "roundtrip_books_with_paid_target_payload": exact_books,
        "interpretation": (
            "availability-only control; it does not enumerate candidate ranks "
            "because the control question is whether previous material still "
            "contains the chosen content under the perturbation"
        ),
    }


def literal_tape_shuffle_control(events: list[dict[str, Any]]) -> dict[str, Any]:
    literal_events = [row for row in events if row["event_kind"] == "literal"]
    tape = "".join(str(row["literal_payload"]) for row in literal_events)
    rng = random.Random(RANDOM_SEED + 303)
    shuffled = list(tape)
    rng.shuffle(shuffled)
    shuffled_tape = "".join(shuffled)
    pos = 0
    exact_chunks = 0
    for row in literal_events:
        length = int(row["exact_length"])
        if shuffled_tape[pos : pos + length] == row["literal_payload"]:
            exact_chunks += 1
        pos += length
    return {
        "literal_chunks": len(literal_events),
        "literal_digits": len(tape),
        "raw_payload_bits_unchanged_by_shuffle": len(tape) * LOG2_10,
        "same_position_exact_chunks_after_shuffle": exact_chunks,
        "interpretation": (
            "raw literal-payload coding is insensitive to tape order; shuffled "
            "replay only tests whether the existing innovation order is itself "
            "needed for exact replay"
        ),
    }


def make_result() -> dict[str, Any]:
    events, validation = build_event_rows()
    full = summarize(events)
    selected_policy = full["selected_policy"]
    holdouts = prefix_holdouts(events)
    controls = {
        "book_order_permuted": material_availability_control("permuted_book_order"),
        "literal_tape_shuffled": literal_tape_shuffle_control(events),
        "previous_material_reversed_order": material_availability_control("reverse_previous_books"),
        "previous_material_shuffled_digits": material_availability_control("shuffled_previous_digits"),
        "random_rank": random_rank_control(events, selected_policy),
        "same_multiset_shuffled_chunks": same_multiset_chunk_control(events, selected_policy),
    }
    reduces_ledger = full["content_event_residual_bits"] < full["baseline_residual_bits_replaced"]
    beats_random = controls["random_rank"]["beats_p05"]
    source_removed = full["source_derived_copy_ops"] == full["copy_ops"]
    holdout_improves = sum(row["test_delta_vs_v2"] < 0 for row in holdouts)
    promoted = reduces_ledger and beats_random and holdout_improves >= 4
    classification = (
        "PROMOTED_CONTENT_ADDRESSED_EVENT_PROGRAM"
        if promoted
        else "content_addressed_event_program_not_promoted"
    )
    compact_rows = [
        {
            "book": row["book"],
            "candidate_count": row["candidate_count"],
            "canonical_source": row["canonical_source"],
            "event_kind": row["event_kind"],
            "exact_length": row["exact_length"],
            "op_index": row["op_index"],
            "rank": row["event_rank_by_policy"][selected_policy],
            "rank_bits": row["event_rank_bits_by_policy"][selected_policy],
            "target_start": row["target_start"],
        }
        for row in sorted(
            [item for item in events if item["event_kind"] == "copy"],
            key=lambda item: int(item["event_rank_by_policy"][selected_policy] or 10**12),
            reverse=True,
        )[:30]
    ]
    return {
        "case_reopened": False,
        "classification": classification,
        "compression_bound_status": "unchanged",
        "controls": controls,
        "decision": {
            "content_addressed_event_program_promoted": promoted,
            "copy_source_removed_as_raw_field": source_removed,
            "generation_explanation_status": (
                "promoted" if promoted else "not_promoted_weak_source_derivation_only"
            ),
            "next_blocker": (
                "origin/content remains external: composition residual, copy "
                "chunk content, literal innovation, and seed payload"
            ),
            "plaintext_claim": False,
            "row0_status": "unchanged_exogenous",
            "translation_delta": "NONE",
        },
        "event_ledger_rows": events,
        "hardest_copy_rows": compact_rows,
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "executable_v2_remaining_tape_coupling": rel(REMAINING_TAPE_FINAL),
            "executable_v2_residual_coupling": rel(RESIDUAL_COUPLING_FINAL),
            "online_x64_coarse_control_program": rel(ONLINE_X64_FINAL),
            "unified_external_tape_ledger": rel(UNIFIED_LEDGER),
        },
        "plaintext_claim": False,
        "prefix_holdouts": holdouts,
        "row0_status": "unchanged_exogenous",
        "schema": "content_addressed_event_program_gate.v1",
        "scope": "analysis_only_content_addressed_event_program",
        "summary": {
            **full,
            "beats_random_rank_control": beats_random,
            "holdout_splits_improving_v2": holdout_improves,
            "online_x64_coarse_bits": ONLINE_X64_COARSE_BITS,
            "promoted": promoted,
            "reduces_v2_residual_ledger": reduces_ledger,
            "secondary_clue": (
                "WEAK_CONTENT_ADDRESSED_SOURCE_DERIVATION_CLUE"
                if source_removed and beats_random
                else "NONE"
            ),
        },
        "translation_delta": "NONE",
        "validation": validation,
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Content-Addressed Event Program Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Question",
        "",
        "Given the promoted online x64 coarse-control stream, can copy events "
        "choose prior content chunks so exact length and source derive from the "
        "selected chunk, replacing `composition_index + copy_hint/source`?",
        "",
        "## Cost Comparison",
        "",
        f"- Selected content policy: `{s['selected_policy']}`.",
        f"- V2 residual being replaced: `{s['baseline_residual_bits_replaced']:.3f}` bits.",
        f"- Content-event residual: `{s['content_event_residual_bits']:.3f}` bits.",
        f"- Delta vs v2 residual: `{s['content_event_delta_vs_v2_residual_bits']:.3f}` bits.",
        f"- V2 total with online x64 excluding seed: `{s['v2_total_with_online_coarse_excluding_seed']:.3f}` bits.",
        f"- New total with online x64 excluding seed: `{s['new_total_with_online_coarse_excluding_seed']:.3f}` bits.",
        f"- Copy content-rank bits: `{s['content_copy_event_rank_bits']:.3f}`.",
        f"- Literal event bits: `{s['literal_event_bits']:.3f}` (`{s['literal_payload_bits']:.3f}` payload + `{s['literal_length_bits']:.3f}` length delimiters).",
        "",
        "## Source/Length Derivation",
        "",
        f"- Copy ops: `{s['copy_ops']}`.",
        f"- Source derived from selected content: `{s['source_derived_copy_ops']}/{s['copy_ops']}`.",
        f"- Canonical source equals raw source: `{s['source_matches_raw_copy_ops']}/{s['copy_ops']}`.",
        f"- Candidate count median/mean/max: `{s['candidate_count_median']}` / `{s['candidate_count_mean']:.3f}` / `{s['candidate_count_max']}`.",
        f"- Top-80 content-rank hits: `{s['topk_hits']['80']}/{s['copy_ops']}`.",
        "",
        "## Controls",
        "",
        "| Control | Metric | Result |",
        "| --- | --- | ---: |",
    ]
    controls = result["controls"]
    lines.extend(
        [
            f"| `random_rank` | observed/p05/p50/p95 | `{controls['random_rank']['observed_copy_rank_bits']:.3f}` / `{controls['random_rank']['p05']:.3f}` / `{controls['random_rank']['p50']:.3f}` / `{controls['random_rank']['p95']:.3f}` |",
            f"| `same_multiset_shuffled_chunks` | observed/p05/p50/p95 | `{controls['same_multiset_shuffled_chunks']['observed_copy_rank_bits']:.3f}` / `{controls['same_multiset_shuffled_chunks']['p05']:.3f}` / `{controls['same_multiset_shuffled_chunks']['p50']:.3f}` / `{controls['same_multiset_shuffled_chunks']['p95']:.3f}` |",
            f"| `previous_material_reversed_order` | content available | `{controls['previous_material_reversed_order']['target_content_available_copy_ops']}/{controls['previous_material_reversed_order']['copy_ops']}` |",
            f"| `previous_material_shuffled_digits` | content available | `{controls['previous_material_shuffled_digits']['target_content_available_copy_ops']}/{controls['previous_material_shuffled_digits']['copy_ops']}` |",
            f"| `book_order_permuted` | content available | `{controls['book_order_permuted']['target_content_available_copy_ops']}/{controls['book_order_permuted']['copy_ops']}` |",
            f"| `literal_tape_shuffled` | exact chunks after shuffle | `{controls['literal_tape_shuffled']['same_position_exact_chunks_after_shuffle']}/{controls['literal_tape_shuffled']['literal_chunks']}` |",
        ]
    )
    lines.extend(
        [
            "",
            "## Prefix Holdout",
            "",
            "| Cutoff | Policy | Test copy ops | Content bits | V2 bits | Delta | Top80 |",
            "| ---: | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in result["prefix_holdouts"]:
        lines.append(
            f"| `{row['cutoff']}` | `{row['selected_policy']}` | `{row['test_copy_ops']}` | "
            f"`{row['test_content_event_bits']:.3f}` | `{row['test_baseline_bits']:.3f}` | "
            f"`{row['test_delta_vs_v2']:.3f}` | `{row['test_top80_hits']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            (
                "`PROMOTED_CONTENT_ADDRESSED_EVENT_PROGRAM`: the content event "
                "program reduces the v2 residual ledger after controls."
                if result["summary"]["promoted"]
                else "`content_addressed_event_program_not_promoted` as a full "
                "program. It removes raw source as a field only by replacing it "
                "with a larger content-rank tape, so the residual burden moves "
                "to chunk content rather than becoming a small generator."
            ),
            "",
            "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        ]
    )
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Final Content-Addressed Event Program Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        "The gate tested a representation shift: copy events select prior content "
        "inside the online-x64 coarse bucket, then exact length and canonical "
        "source derive from that chunk. Literal events retain an innovation tape "
        "and pay a length delimiter because the composition index is no longer "
        "granted.",
        "",
        f"Residual v2 cost for `composition_index + copy_hint_rank/source + "
        f"literal_payload` is `{s['baseline_residual_bits_replaced']:.3f}` bits. "
        f"The content-addressed residual costs `{s['content_event_residual_bits']:.3f}` "
        f"bits, a delta of `{s['content_event_delta_vs_v2_residual_bits']:.3f}` bits.",
        "",
        f"All `{s['copy_ops']}` copy events can derive a canonical source after the "
        "target content is selected, but only "
        f"`{s['source_matches_raw_copy_ops']}/{s['copy_ops']}` canonical sources "
        "match the original raw source. The selected content-rank policy has "
        f"`{s['topk_hits']['80']}/{s['copy_ops']}` top-80 hits.",
        "",
        "## Decision",
        "",
        (
            "`PROMOTED_CONTENT_ADDRESSED_EVENT_PROGRAM`: this front reduces the "
            "external ledger after paying content ranks and controls."
            if result["summary"]["promoted"]
            else "`content_addressed_event_program_not_promoted`. Source can be "
            "canonically derived after a content chunk is selected, but the chunk "
            "selection tape is larger than the v2 residual it replaces. This is "
            "not a smaller executable generator."
        ),
        "",
        "The next barrier is origin/content, not coarse-control: exact composition "
        "residual, copy chunk content, literal innovation, and seed payload remain "
        "external. `row0`, plaintext, translation, semantics, and `compression_bound` "
        "remain unchanged.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_content_addressed_event_program_gate.py](../scripts/01_content_addressed_event_program_gate.py)",
        "- [01_content_addressed_event_program_gate.json](test_results/01_content_addressed_event_program_gate.json)",
        "- [01_content_addressed_event_program_gate.md](test_results/01_content_addressed_event_program_gate.md)",
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
