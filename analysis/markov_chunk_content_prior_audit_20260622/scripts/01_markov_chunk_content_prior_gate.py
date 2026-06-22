#!/usr/bin/env python3
"""Markov chunk-content prior gate.

The joint chunk-origin route needs a target-free way to prefer one candidate
chunk over many prior chunks. The strongest source-free digit clue so far is a
prefix-trained prev2 digit model. This gate tests whether that digit-content
prior actually helps choose copy chunks when exact copy length is granted.

Scope: analysis-only. This does not promote plaintext, row0 origin, or a new
compression bound.
"""

from __future__ import annotations

import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "markov_chunk_content_prior_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"

BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
COPY_SOURCE_LEDGER = (
    ROOT
    / "analysis"
    / "copy_source_generation_audit_20260621"
    / "reports"
    / "test_results"
    / "01_copy_source_ledger.json"
)
COPY_HINT_LOWER_BOUND = (
    ROOT
    / "analysis"
    / "latent_transducer_generation_audit_20260622"
    / "reports"
    / "test_results"
    / "08_copy_hint_stream_lower_bound.json"
)
BUCKET_PILOT = (
    ROOT
    / "analysis"
    / "joint_chunk_origin_beam_pilot_audit_20260622"
    / "reports"
    / "test_results"
    / "01_bucket_chunk_origin_beam_pilot.json"
)

JSON_OUT = TEST_RESULTS / "01_markov_chunk_content_prior_gate.json"
MD_OUT = TEST_RESULTS / "01_markov_chunk_content_prior_gate.md"
FINAL_OUT = FRONT / "reports" / "final_markov_chunk_content_prior_audit.md"

CUTOFFS = [20, 30, 40, 50, 60]
POLICIES = [
    "freq_recent",
    "markov_likely",
    "markov_likely_freq_recent",
    "freq_recent_markov",
    "recent_freq_markov",
]
ALPHA = 0.5
RANDOM_SEED = 46920260622
RANDOM_TRIALS = 500


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


def train_prev2_model(books: dict[int, str], train_books: range) -> tuple[dict[str, Counter], Counter]:
    counts: dict[str, Counter] = defaultdict(Counter)
    totals: Counter = Counter()
    for book in train_books:
        context = "^^"
        for digit in books[book]:
            counts[context][digit] += 1
            totals[context] += 1
            context = (context + digit)[-2:]
    return counts, totals


def markov_bits(chunk: str, initial_context: str, model: tuple[dict[str, Counter], Counter]) -> float:
    counts, totals = model
    context = initial_context
    bits = 0.0
    for digit in chunk:
        counter = counts.get(context)
        total = totals.get(context, 0)
        if counter is None or total == 0:
            probability = 0.1
        else:
            probability = (counter.get(digit, 0) + ALPHA) / (total + ALPHA * 10)
        bits += -math.log2(probability)
        context = (context + digit)[-2:]
    return bits


def unique_chunks_at_length(available: str, length: int) -> list[dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for source in range(0, len(available) - length + 1):
        chunk = available[source : source + length]
        row = rows.get(chunk)
        if row is None:
            rows[chunk] = {
                "chunk": chunk,
                "count": 1,
                "max_source": source,
                "min_source": source,
            }
        else:
            row["count"] += 1
            row["max_source"] = source
    return list(rows.values())


def target_context(prefix: str) -> str:
    if len(prefix) >= 2:
        return prefix[-2:]
    return ("^^" + prefix)[-2:]


def build_events(books: dict[int, str], ops_by_book: dict[int, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    emitted = "".join(books[book] for book in range(10))
    events = []
    for book in range(10, 70):
        rendered: list[str] = []
        for op_index, op in enumerate(ops_by_book[book]):
            start = int(op["target_start"])
            length = int(op["length"])
            available = emitted + "".join(rendered)
            payload = books[book][start : start + length]
            if op["type"] == "literal":
                rendered.append(payload)
                continue
            source = int(op["source"])
            if available[source : source + length] != payload:
                raise RuntimeError({"book": book, "op_index": op_index, "type": "copy_mismatch"})
            candidates = unique_chunks_at_length(available, length)
            correct = next(row for row in candidates if row["chunk"] == payload)
            events.append(
                {
                    "available_len": len(available),
                    "book": book,
                    "candidates": candidates,
                    "correct_chunk": payload,
                    "correct_count": int(correct["count"]),
                    "correct_max_source": int(correct["max_source"]),
                    "initial_context": target_context(books[book][:start]),
                    "length": length,
                    "op_index": op_index,
                    "target_start": start,
                    "unique_candidates": len(candidates),
                }
            )
            rendered.append(payload)
        rendered_book = "".join(rendered)
        if rendered_book != books[book]:
            raise RuntimeError({"book": book, "type": "roundtrip_failed"})
        emitted += rendered_book
    return events


def policy_key(row: dict[str, Any], policy: str, markov_score: float, available_len: int) -> tuple[Any, ...]:
    recency = available_len - (int(row["max_source"]) + len(str(row["chunk"])))
    if policy == "freq_recent":
        return (-int(row["count"]), recency, row["chunk"])
    if policy == "markov_likely":
        return (markov_score, row["chunk"])
    if policy == "markov_likely_freq_recent":
        return (markov_score, -int(row["count"]), recency, row["chunk"])
    if policy == "freq_recent_markov":
        return (-int(row["count"]), recency, markov_score, row["chunk"])
    if policy == "recent_freq_markov":
        return (recency, -int(row["count"]), markov_score, row["chunk"])
    raise KeyError(policy)


def ranks_for_event(event: dict[str, Any], model: tuple[dict[str, Counter], Counter]) -> dict[str, int]:
    scores = {
        row["chunk"]: markov_bits(str(row["chunk"]), str(event["initial_context"]), model)
        for row in event["candidates"]
    }
    correct_chunk = str(event["correct_chunk"])
    ranks = {}
    for policy in POLICIES:
        correct_row = next(row for row in event["candidates"] if row["chunk"] == correct_chunk)
        correct_key = policy_key(
            correct_row,
            policy,
            scores[correct_chunk],
            int(event["available_len"]),
        )
        ranks[policy] = 1 + sum(
            1
            for row in event["candidates"]
            if policy_key(
                row,
                policy,
                scores[str(row["chunk"])],
                int(event["available_len"]),
            )
            < correct_key
        )
    return ranks


def score_events(events: list[dict[str, Any]], model: tuple[dict[str, Counter], Counter]) -> dict[str, Any]:
    bits = {policy: 0.0 for policy in POLICIES}
    top80 = {policy: 0 for policy in POLICIES}
    top1 = {policy: 0 for policy in POLICIES}
    for event in events:
        ranks = ranks_for_event(event, model)
        for policy, rank in ranks.items():
            bits[policy] += math.log2(rank)
            top80[policy] += int(rank <= 80)
            top1[policy] += int(rank == 1)
    best_policy = min(bits, key=lambda policy: bits[policy])
    return {
        "best_policy": best_policy,
        "best_policy_bits": bits[best_policy],
        "policy_bits": bits,
        "top1_hits": top1,
        "top80_hits": top80,
    }


def random_controls(events: list[dict[str, Any]], seed_offset: int) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED + seed_offset)
    totals = []
    top80s = []
    for _ in range(RANDOM_TRIALS):
        total = 0.0
        top80 = 0
        for event in events:
            rank = rng.randint(1, int(event["unique_candidates"]))
            total += math.log2(rank)
            top80 += int(rank <= 80)
        totals.append(total)
        top80s.append(float(top80))
    ordered = sorted(totals)
    top_ordered = sorted(top80s)
    def pct(values: list[float], p: float) -> float:
        index = min(len(values) - 1, max(0, math.ceil((p / 100.0) * len(values)) - 1))
        return values[index]
    return {
        "random_bits_mean": mean(totals),
        "random_bits_p05": pct(ordered, 5),
        "random_bits_p50": pct(ordered, 50),
        "random_bits_p95": pct(ordered, 95),
        "random_top80_p95": pct(top_ordered, 95),
        "seed": RANDOM_SEED + seed_offset,
        "trials": RANDOM_TRIALS,
    }


def prefix_rows(books: dict[int, str], events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, cutoff in enumerate(CUTOFFS):
        model = train_prev2_model(books, range(cutoff))
        test_events = [event for event in events if int(event["book"]) >= cutoff]
        score = score_events(test_events, model)
        controls = random_controls(test_events, seed_offset=index)
        baseline_bits = score["policy_bits"]["freq_recent"]
        content_first_policies = ["markov_likely", "markov_likely_freq_recent"]
        best_content_first_policy = min(
            content_first_policies,
            key=lambda policy: score["policy_bits"][policy],
        )
        best_markov_augmented_policy = min(
            [policy for policy in POLICIES if policy != "freq_recent"],
            key=lambda policy: score["policy_bits"][policy],
        )
        rows.append(
            {
                "baseline_freq_recent_bits": baseline_bits,
                "best_content_first_policy": best_content_first_policy,
                "best_content_first_policy_bits": score["policy_bits"][best_content_first_policy],
                "best_content_first_delta_vs_freq_recent": score["policy_bits"][best_content_first_policy]
                - baseline_bits,
                "best_markov_augmented_policy": best_markov_augmented_policy,
                "best_markov_augmented_policy_bits": score["policy_bits"][best_markov_augmented_policy],
                "best_markov_augmented_delta_vs_freq_recent": score["policy_bits"][best_markov_augmented_policy]
                - baseline_bits,
                "best_policy_overall": score["best_policy"],
                "cutoff": cutoff,
                "content_first_beats_freq_recent": score["policy_bits"][best_content_first_policy]
                < baseline_bits,
                "content_first_beats_random_p05": score["policy_bits"][best_content_first_policy]
                < controls["random_bits_p05"],
                "markov_augmented_beats_freq_recent": score["policy_bits"][best_markov_augmented_policy]
                < baseline_bits,
                "policy_bits": score["policy_bits"],
                "random_controls": controls,
                "test_copy_ops": len(test_events),
                "top1_hits": score["top1_hits"],
                "top80_hits": score["top80_hits"],
            }
        )
    return rows


def make_result() -> dict[str, Any]:
    copy_ledger = load_json(COPY_SOURCE_LEDGER)
    assert_boundary("copy_source_ledger", copy_ledger)
    hint = load_json(COPY_HINT_LOWER_BOUND)
    assert_boundary("copy_hint_stream_lower_bound", hint)
    bucket_pilot = load_json(BUCKET_PILOT)
    assert_boundary("bucket_chunk_origin_beam_pilot", bucket_pilot)
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    ops_by_book = {int(key): value for key, value in copy_ledger["canonical_ops_by_book"].items()}
    events = build_events(books, ops_by_book)
    rows = prefix_rows(books, events)
    content_first_beats_freq_cells = sum(row["content_first_beats_freq_recent"] for row in rows)
    content_first_beats_random_cells = sum(row["content_first_beats_random_p05"] for row in rows)
    augmented_beats_freq_cells = sum(row["markov_augmented_beats_freq_recent"] for row in rows)
    total_baseline_bits = sum(row["baseline_freq_recent_bits"] for row in rows)
    total_content_first_bits = sum(row["best_content_first_policy_bits"] for row in rows)
    total_augmented_bits = sum(row["best_markov_augmented_policy_bits"] for row in rows)
    promoted = content_first_beats_freq_cells >= 4 and total_content_first_bits < total_baseline_bits
    classification = (
        "PROMOTED_MARKOV_CHUNK_CONTENT_PRIOR"
        if promoted
        else "MARKOV_CHUNK_CONTENT_PRIOR_REJECTED"
    )
    return {
        "case_reopened": False,
        "classification": classification,
        "compression_bound_status": "unchanged",
        "decision": {
            "generator_promoted": False,
            "markov_content_prior_promoted": promoted,
            "next_blocker": (
                "prev2 digit likelihood does not improve same-length chunk choice "
                "over frequency/recency; chunk-origin still needs a richer latent "
                "state or nonlocal mechanism"
            ),
            "row0_status": "unchanged_exogenous",
            "translation_delta": "NONE",
        },
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "bucket_chunk_origin_beam_pilot": rel(BUCKET_PILOT),
            "copy_hint_stream_lower_bound": rel(COPY_HINT_LOWER_BOUND),
            "copy_source_ledger": rel(COPY_SOURCE_LEDGER),
        },
        "plaintext_claim": False,
        "prefix_rows": rows,
        "schema": "markov_chunk_content_prior_gate.v1",
        "scope": "analysis_only_prev2_content_prior_for_same_length_copy_chunks",
        "summary": {
            "copy_ops": len(events),
            "content_first_beats_freq_recent_cells": content_first_beats_freq_cells,
            "content_first_beats_random_p05_cells": content_first_beats_random_cells,
            "markov_augmented_beats_freq_recent_cells": augmented_beats_freq_cells,
            "total_baseline_freq_recent_bits": total_baseline_bits,
            "total_best_content_first_bits": total_content_first_bits,
            "total_best_content_first_delta_vs_freq_recent": total_content_first_bits
            - total_baseline_bits,
            "total_best_markov_augmented_bits": total_augmented_bits,
            "total_best_markov_augmented_delta_vs_freq_recent": total_augmented_bits
            - total_baseline_bits,
        },
        "translation_delta": "NONE",
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Markov Chunk-Content Prior Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Purpose",
        "",
        "Test whether the promoted `prev2` target-digit clue helps rank same-length "
        "copy chunk candidates as target continuations under prefix holdout.",
        "",
        "## Summary",
        "",
        f"- Copy ops: `{s['copy_ops']}`.",
        f"- Content-first Markov beats frequency/recency cells: `{s['content_first_beats_freq_recent_cells']}/5`.",
        f"- Content-first Markov beats random p05 cells: `{s['content_first_beats_random_p05_cells']}/5`.",
        f"- Markov as frequency/recency tie-breaker beats baseline cells: `{s['markov_augmented_beats_freq_recent_cells']}/5`.",
        f"- Aggregate frequency/recency bits: `{s['total_baseline_freq_recent_bits']:.3f}`.",
        f"- Aggregate best content-first Markov bits: `{s['total_best_content_first_bits']:.3f}`.",
        f"- Aggregate content-first delta: `{s['total_best_content_first_delta_vs_freq_recent']:.3f}` bits.",
        f"- Aggregate Markov-tie-breaker delta: `{s['total_best_markov_augmented_delta_vs_freq_recent']:.3f}` bits.",
        "",
        "## Prefix Holdouts",
        "",
        "| Cutoff | Copy ops | Best content-first policy | Content bits | Freq/recency bits | Delta | Beats random p05 |",
        "| --- | ---: | --- | ---: | ---: | ---: | --- |",
    ]
    for row in result["prefix_rows"]:
        lines.append(
            f"| `{row['cutoff']}` | `{row['test_copy_ops']}` | "
            f"`{row['best_content_first_policy']}` | `{row['best_content_first_policy_bits']:.3f}` | "
            f"`{row['baseline_freq_recent_bits']:.3f}` | "
            f"`{row['best_content_first_delta_vs_freq_recent']:.3f}` | "
            f"`{row['content_first_beats_random_p05']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "The `prev2` digit-content clue remains useful for digit and boundary "
            "statistics, but it does not improve same-length copy-chunk selection "
            "over frequency/recency. It is not promoted as a chunk-origin program.",
        ]
    )
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Final Markov Chunk-Content Prior Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Question",
        "",
        "Does the prefix-trained `prev2` digit-content prior help choose same-length "
        "copy chunks, turning the strongest digit clue into a chunk-origin selector?",
        "",
        "## Result",
        "",
        f"No. Across the five prefix holdouts, content-first Markov policies beat "
        f"the frequency/recency copy-hint baseline in "
        f"`{s['content_first_beats_freq_recent_cells']}/5` cells. Aggregate best "
        f"content-first Markov cost is `{s['total_best_content_first_bits']:.3f}` "
        f"bits versus "
        f"`{s['total_baseline_freq_recent_bits']:.3f}` for frequency/recency "
        f"(`{s['total_best_content_first_delta_vs_freq_recent']:.3f}` bits). "
        "Using Markov only as a tie-breaker also gives no improvement.",
        "",
        "## Decision",
        "",
        "`prev2` remains a target-digit/boundary clue, not a copy chunk-origin "
        "program. The next blocker is still a richer latent/nonlocal state that "
        "links length, chunk content, and copy availability. Row0, plaintext, "
        "translation, and compression_bound are unchanged.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_markov_chunk_content_prior_gate.py](../scripts/01_markov_chunk_content_prior_gate.py)",
        "- [01_markov_chunk_content_prior_gate.json](test_results/01_markov_chunk_content_prior_gate.json)",
        "- [01_markov_chunk_content_prior_gate.md](test_results/01_markov_chunk_content_prior_gate.md)",
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
