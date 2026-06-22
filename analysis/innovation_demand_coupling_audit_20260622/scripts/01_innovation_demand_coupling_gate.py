#!/usr/bin/env python3
"""Test whether innovation replay events are synchronized to decoder demand.

The promoted unified innovation payload concatenates seed payload and literal
payload into one stream, then replays that stream with literal/copy events. This
gate tests a genuinely different causal-state candidate: perhaps replay event
boundaries are not chosen by local content alone, but by the downstream demand
surface that consumes the innovation stream as seed books and literal payload
runs.

It is analysis-only. It does not use leaked data, row0 semantics, plaintext, or
translation.
"""

from __future__ import annotations

import json
import math
import random
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis/innovation_demand_coupling_audit_20260622"
OUT_DIR = FRONT / "reports/test_results"
JSON_OUT = OUT_DIR / "01_innovation_demand_coupling_gate.json"
MD_OUT = OUT_DIR / "01_innovation_demand_coupling_gate.md"
FINAL_OUT = FRONT / "reports/final_innovation_demand_coupling_audit.md"

PAYLOAD_GATE = ROOT / "analysis/unified_innovation_payload_audit_20260622/reports/test_results/01_unified_innovation_payload_gate.json"
TRIALS = 2000
RNG_SEED = 46920260622


def load_json(path: Path) -> Any:
    with path.open() as f:
        return json.load(f)


def log2_comb(n: int, k: int) -> float:
    if k < 0 or k > n:
        return float("inf")
    return (math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)) / math.log(2)


def quantile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    pos = min(len(ordered) - 1, max(0, int(math.ceil(q * len(ordered)) - 1)))
    return ordered[pos]


def assert_boundary(data: dict[str, Any]) -> None:
    if data.get("translation_delta") != "NONE":
        raise RuntimeError("translation boundary changed")
    if data.get("case_reopened", False) is not False:
        raise RuntimeError("case reopened")
    if data.get("plaintext_claim", False) is not False:
        raise RuntimeError("plaintext introduced")
    if data.get("row0_status") != "unchanged_exogenous":
        raise RuntimeError("row0 changed")
    if data.get("classification") != "PROMOTED_UNIFIED_INNOVATION_PAYLOAD_LEDGER":
        raise RuntimeError("unified innovation payload is not the promoted input ledger")


def containing_segment(segments: list[dict[str, Any]], start: int, end: int) -> dict[str, Any] | None:
    for segment in segments:
        if int(segment["start"]) <= start and end <= int(segment["end"]):
            return segment
    return None


def boundary_hits(boundaries: set[int], demand_boundaries: set[int]) -> int:
    return len(boundaries & demand_boundaries)


def within_segment_count(events: list[dict[str, Any]], segments: list[dict[str, Any]]) -> int:
    count = 0
    for event in events:
        start = int(event["start"])
        end = start + int(event["length"])
        if containing_segment(segments, start, end):
            count += 1
    return count


def cumulative_boundaries(lengths: list[int]) -> set[int]:
    boundaries = set()
    pos = 0
    for length in lengths[:-1]:
        pos += length
        boundaries.add(pos)
    return boundaries


def permuted_events_from_lengths(lengths: list[int]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    pos = 0
    for length in lengths:
        events.append({"start": pos, "length": length, "kind": "control"})
        pos += length
    return events


def make_result() -> dict[str, Any]:
    payload = load_json(PAYLOAD_GATE)
    assert_boundary(payload)
    events = payload["event_ledger"]
    segments = payload["segments"]
    stream_len = int(payload["summary"]["stream_digits"])

    demand_boundaries = {int(segment["start"]) for segment in segments} | {int(segment["end"]) for segment in segments}
    internal_demand = demand_boundaries - {0, stream_len}
    event_boundaries = {int(event["start"]) for event in events[1:]}
    event_lengths = [int(event["length"]) for event in events]
    segment_lengths = [int(segment["length"]) for segment in segments]

    hit_count = boundary_hits(event_boundaries, internal_demand)
    miss_count = len(event_boundaries) - hit_count
    within_count = within_segment_count(events, segments)
    cross_count = len(events) - within_count

    raw_boundary_bits = log2_comb(stream_len - 1, len(event_boundaries))
    demand_boundary_bits = (
        math.log2(len(event_boundaries) + 1)
        + log2_comb(len(internal_demand), hit_count)
        + log2_comb((stream_len - 1) - len(internal_demand), miss_count)
    )
    demand_boundary_delta = raw_boundary_bits - demand_boundary_bits

    rng = random.Random(RNG_SEED)
    random_hit_counts: list[int] = []
    all_positions = list(range(1, stream_len))
    for _ in range(TRIALS):
        sample = set(rng.sample(all_positions, len(event_boundaries)))
        random_hit_counts.append(boundary_hits(sample, internal_demand))

    permuted_length_hits: list[int] = []
    permuted_length_within: list[int] = []
    for _ in range(TRIALS):
        lengths = event_lengths[:]
        rng.shuffle(lengths)
        boundaries = cumulative_boundaries(lengths)
        permuted_length_hits.append(boundary_hits(boundaries, internal_demand))
        permuted_length_within.append(within_segment_count(permuted_events_from_lengths(lengths), segments))

    shuffled_segment_hits: list[int] = []
    for _ in range(TRIALS):
        lengths = segment_lengths[:]
        rng.shuffle(lengths)
        shuffled_internal = cumulative_boundaries(lengths)
        shuffled_segment_hits.append(boundary_hits(event_boundaries, shuffled_internal))

    copy_rows: list[dict[str, Any]] = []
    for event_index, event in enumerate(events):
        if event["kind"] != "copy":
            continue
        target_start = int(event["start"])
        target_end = target_start + int(event["length"])
        source_start = int(event["source"])
        source_end = source_start + int(event["length"])
        target_segment = containing_segment(segments, target_start, target_end)
        source_segment = containing_segment(segments, source_start, source_end)
        copy_rows.append(
            {
                "event_index": event_index,
                "start": target_start,
                "length": int(event["length"]),
                "source": source_start,
                "target_segment_label": target_segment["label"] if target_segment else None,
                "source_segment_label": source_segment["label"] if source_segment else None,
                "target_within_demand_segment": target_segment is not None,
                "source_within_demand_segment": source_segment is not None,
                "same_demand_segment": bool(
                    target_segment
                    and source_segment
                    and target_segment["label"] == source_segment["label"]
                ),
            }
        )

    boundary_program_promoted = (
        hit_count > quantile(random_hit_counts, 0.95)
        and hit_count > quantile(permuted_length_hits, 0.95)
        and demand_boundary_delta > 0
    )
    weak_within_segment_clue = within_count > quantile(permuted_length_within, 0.95)
    promoted = boundary_program_promoted
    classification = "innovation_demand_within_segment_weak_clue_not_program" if weak_within_segment_clue else "innovation_demand_coupling_not_promoted"

    return {
        "schema": "innovation_demand_coupling_gate.v1",
        "scope": "analysis_only_new_causal_state_candidate",
        "classification": classification,
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "translation_delta": "NONE",
        "plaintext_claim": False,
        "case_reopened": False,
        "row0_status": "unchanged_exogenous",
        "compression_bound_status": "unchanged",
        "inputs": {"unified_innovation_payload_gate": str(PAYLOAD_GATE.relative_to(ROOT))},
        "summary": {
            "stream_digits": stream_len,
            "innovation_events": len(events),
            "consumer_segments": len(segments),
            "internal_event_boundaries": len(event_boundaries),
            "internal_consumer_boundaries": len(internal_demand),
            "event_boundary_demand_hits": hit_count,
            "event_boundary_demand_misses": miss_count,
            "events_within_single_consumer_segment": within_count,
            "events_crossing_consumer_segments": cross_count,
            "raw_boundary_bits": raw_boundary_bits,
            "demand_boundary_bits": demand_boundary_bits,
            "demand_boundary_saving_bits": demand_boundary_delta,
            "boundary_program_promoted": boundary_program_promoted,
            "weak_within_segment_clue": weak_within_segment_clue,
            "promoted": promoted,
        },
        "controls": {
            "trials": TRIALS,
            "rng_seed": RNG_SEED,
            "random_boundary_hit_p95": quantile(random_hit_counts, 0.95),
            "random_boundary_hit_mean": sum(random_hit_counts) / len(random_hit_counts),
            "permuted_event_length_hit_p95": quantile(permuted_length_hits, 0.95),
            "permuted_event_length_hit_mean": sum(permuted_length_hits) / len(permuted_length_hits),
            "permuted_event_length_within_p95": quantile(permuted_length_within, 0.95),
            "permuted_event_length_within_mean": sum(permuted_length_within) / len(permuted_length_within),
            "shuffled_consumer_segment_hit_p95": quantile(shuffled_segment_hits, 0.95),
            "shuffled_consumer_segment_hit_mean": sum(shuffled_segment_hits) / len(shuffled_segment_hits),
        },
        "copy_demand_alignment": {
            "copy_events": len(copy_rows),
            "target_within_demand_segment": sum(1 for row in copy_rows if row["target_within_demand_segment"]),
            "source_within_demand_segment": sum(1 for row in copy_rows if row["source_within_demand_segment"]),
            "same_demand_segment": sum(1 for row in copy_rows if row["same_demand_segment"]),
            "sample_rows": copy_rows[:20],
        },
        "decision": {
            "innovation_demand_coupling_promoted": promoted,
            "weak_within_segment_clue": weak_within_segment_clue,
            "external_field_reduced": False,
            "v9_reduction_bits": 0.0,
            "reason": (
                "consumer-demand boundaries do not explain replay event boundaries after paid boundary coding and controls; within-segment containment is only a weak clue"
                if weak_within_segment_clue and not promoted
                else (
                    "consumer-demand boundaries do not explain replay event boundaries after paid boundary coding and controls"
                    if not promoted
                    else "consumer-demand boundary program passes controls and needs executable decoder integration"
                )
            ),
            "next_blocker": (
                "innovation replay policy remains external; demand surface is not sufficient as the missing causal state"
                if not promoted
                else "integrate demand-coupled state into an executable replay decoder with paid corrections"
            ),
        },
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    c = result["controls"]
    lines = [
        "# Innovation Demand Coupling Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        "This gate tests whether innovation replay events are synchronized to the downstream consumer segments that use the innovation tape as seed payload and literal payload.",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Stream digits | `{s['stream_digits']}` |",
        f"| Innovation events | `{s['innovation_events']}` |",
        f"| Consumer segments | `{s['consumer_segments']}` |",
        f"| Event-boundary demand hits | `{s['event_boundary_demand_hits']}/{s['internal_event_boundaries']}` |",
        f"| Events within one consumer segment | `{s['events_within_single_consumer_segment']}/{s['innovation_events']}` |",
        f"| Demand-boundary saving bits | `{s['demand_boundary_saving_bits']:.3f}` |",
        f"| Weak within-segment clue | `{s['weak_within_segment_clue']}` |",
        f"| Boundary program promoted | `{s['boundary_program_promoted']}` |",
        "",
        "## Controls",
        "",
        "| Control | Value |",
        "| --- | ---: |",
        f"| Random boundary hit p95 | `{c['random_boundary_hit_p95']}` |",
        f"| Random boundary hit mean | `{c['random_boundary_hit_mean']:.3f}` |",
        f"| Permuted event-length hit p95 | `{c['permuted_event_length_hit_p95']}` |",
        f"| Permuted event-length hit mean | `{c['permuted_event_length_hit_mean']:.3f}` |",
        f"| Permuted event-length within p95 | `{c['permuted_event_length_within_p95']}` |",
        f"| Permuted event-length within mean | `{c['permuted_event_length_within_mean']:.3f}` |",
        f"| Shuffled consumer-segment hit p95 | `{c['shuffled_consumer_segment_hit_p95']}` |",
        "",
        "## Decision",
        "",
        f"`{result['decision']['reason']}`",
        "",
        f"Next blocker: `{result['decision']['next_blocker']}`",
        "",
        "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
    ]
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Final Innovation Demand Coupling Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        "The tested new causal-state candidate is the downstream demand surface: seed and literal-payload consumer segments over the unified innovation tape.",
        f"It does not explain replay boundaries: only `{s['event_boundary_demand_hits']}/{s['internal_event_boundaries']}` internal replay starts hit consumer boundaries, and the paid demand-boundary codec saves `{s['demand_boundary_saving_bits']:.3f}` bits.",
        f"There is a weak containment clue: `{s['events_within_single_consumer_segment']}/{s['innovation_events']}` replay events stay inside one consumer segment, above the permuted-length p95, but this does not derive the event boundaries or reduce a decoder field.",
        "",
        "The demand surface is therefore not promoted as the missing innovation replay policy.",
        "",
        "## Decision",
        "",
        "`innovation_demand_within_segment_weak_clue_not_program`.",
        "",
        "No executable source is integrated, no v9 field is reduced, and no formula is promoted.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_innovation_demand_coupling_gate.py](../scripts/01_innovation_demand_coupling_gate.py)",
        "- [01_innovation_demand_coupling_gate.json](test_results/01_innovation_demand_coupling_gate.json)",
        "- [01_innovation_demand_coupling_gate.md](test_results/01_innovation_demand_coupling_gate.md)",
    ]
    FINAL_OUT.write_text("\n".join(lines) + "\n")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    result = make_result()
    JSON_OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_markdown(result)
    write_final(result)


if __name__ == "__main__":
    main()
