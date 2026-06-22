#!/usr/bin/env python3
"""Causal content-aware event-policy gate for the innovation replay.

This is the next internal route after simple event n-grams failed. The decoder
state is the emitted innovation stream plus the remaining literal tape. At true
event boundaries, the gate enumerates causal copy/literal candidates, ranks the
true event under fixed content-aware policies selected on prefix data, and then
tries to keep the true suffix in a finite event beam.

It is analysis-only. It does not use row0, plaintext, translation, semantics, or
leaked data.
"""

from __future__ import annotations

import heapq
import json
import math
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis/causal_content_aware_event_policy_audit_20260622"
OUT_DIR = FRONT / "reports/test_results"
JSON_OUT = OUT_DIR / "01_causal_content_aware_event_policy_gate.json"
MD_OUT = OUT_DIR / "01_causal_content_aware_event_policy_gate.md"
FINAL_OUT = FRONT / "reports/final_causal_content_aware_event_policy_audit.md"

PAYLOAD_GATE = ROOT / "analysis/unified_innovation_payload_audit_20260622/reports/test_results/01_unified_innovation_payload_gate.json"
V9_GATE = ROOT / "analysis/executable_v9_innovation_copy_continuation_audit_20260622/reports/test_results/01_executable_v9_innovation_copy_continuation_gate.json"

MIN_COPY_LEN = 8
MAX_COPY_LEN = 64
EVENT_PREFIX_CUTOFFS = [20, 35, 50]
POLICIES = [
    "longest_copy_then_literal",
    "continuation_then_longest_copy",
    "recent_long_copy",
    "literal_long_then_copy",
    "low_address_then_copy",
]
MODEL_COST_BITS = math.log2(len(POLICIES))
BEAM_WIDTHS = [8, 32, 128]
TOP_CANDIDATES_PER_STATE = 8
MAX_BEAM_EVENTS = 8


@dataclass(frozen=True)
class Candidate:
    kind: str
    length: int
    source: int | None = None


def load_json(path: Path) -> Any:
    with path.open() as f:
        return json.load(f)


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


def render_events(events: list[dict[str, Any]]) -> str:
    output: list[str] = []
    for event in events:
        if event["kind"] == "literal":
            output.append(str(event["text"]))
            continue
        available = "".join(output)
        output.append(available[int(event["source"]) : int(event["source"]) + int(event["length"])])
    return "".join(output)


def literal_tape(events: list[dict[str, Any]]) -> str:
    return "".join(str(event["text"]) for event in events if event["kind"] == "literal")


def literal_positions(events: list[dict[str, Any]]) -> list[int]:
    positions = []
    cursor = 0
    for event in events:
        positions.append(cursor)
        if event["kind"] == "literal":
            cursor += int(event["length"])
    return positions


def true_candidate(event: dict[str, Any]) -> Candidate:
    if event["kind"] == "literal":
        return Candidate("literal", int(event["length"]))
    return Candidate("copy", int(event["length"]), int(event["source"]))


def iter_candidates(prefix_len: int, literal_remaining: int):
    for length in range(1, literal_remaining + 1):
        yield Candidate("literal", length)
    for source in range(prefix_len):
        max_len = min(MAX_COPY_LEN, prefix_len - source)
        for length in range(MIN_COPY_LEN, max_len + 1):
            yield Candidate("copy", length, source)


def candidate_count(prefix_len: int, literal_remaining: int) -> int:
    copy_count = 0
    for source in range(prefix_len):
        max_len = min(MAX_COPY_LEN, prefix_len - source)
        if max_len >= MIN_COPY_LEN:
            copy_count += max_len - MIN_COPY_LEN + 1
    return literal_remaining + copy_count


def is_continuation(candidate: Candidate, previous_event: dict[str, Any] | None, start: int) -> bool:
    if candidate.kind != "copy" or previous_event is None or previous_event["kind"] != "copy":
        return False
    return (
        candidate.source == int(previous_event["source"]) + int(previous_event["length"])
        and start == int(previous_event["start"]) + int(previous_event["length"])
    )


def score_candidate(candidate: Candidate, policy: str, prefix: str, previous_event: dict[str, Any] | None) -> tuple[float, ...]:
    start = len(prefix)
    if candidate.kind == "literal":
        if policy == "literal_long_then_copy":
            return (2.0, float(candidate.length), 0.0)
        return (0.0, float(candidate.length), 0.0)
    age = start - int(candidate.source)
    continuation = 1.0 if is_continuation(candidate, previous_event, start) else 0.0
    if policy == "longest_copy_then_literal":
        return (1.0, float(candidate.length), -float(age), -float(candidate.source or 0))
    if policy == "continuation_then_longest_copy":
        return (1.5 + continuation, float(candidate.length), -float(age), -float(candidate.source or 0))
    if policy == "recent_long_copy":
        return (1.0, float(candidate.length) - math.log2(max(1, age)), -float(age))
    if policy == "literal_long_then_copy":
        return (1.0, float(candidate.length), -float(age))
    if policy == "low_address_then_copy":
        return (1.0, -math.log2(max(1, int(candidate.source) + 1)), float(candidate.length))
    raise KeyError(policy)


def sort_key(candidate: Candidate, policy: str, prefix: str, previous_event: dict[str, Any] | None) -> tuple[tuple[float, ...], int, int]:
    return (
        score_candidate(candidate, policy, prefix, previous_event),
        candidate.length,
        candidate.source if candidate.source is not None else -1,
    )


def ranked_candidates(prefix: str, literal_remaining: int, previous_event: dict[str, Any] | None, policy: str) -> list[Candidate]:
    return heapq.nlargest(
        TOP_CANDIDATES_PER_STATE,
        iter_candidates(len(prefix), literal_remaining),
        key=lambda cand: sort_key(cand, policy, prefix, previous_event),
    )


def beam_candidate_pool(prefix: str, literal_remaining: int, previous_event: dict[str, Any] | None, policy: str) -> list[Candidate]:
    """Small causal candidate pool for beam search.

    Exact rank accounting still uses the full candidate set. The beam is only a
    survival pilot, so it uses representative content-aware candidates instead
    of sorting every source/length pair at every generated state.
    """

    start = len(prefix)
    pool: set[Candidate] = set()
    literal_lengths = [1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, literal_remaining]
    if policy == "literal_long_then_copy":
        literal_lengths = list(reversed(literal_lengths))
    for length in literal_lengths:
        if 1 <= length <= literal_remaining:
            pool.add(Candidate("literal", length))

    if previous_event and previous_event.get("kind") == "copy":
        cont_source = int(previous_event["source"]) + int(previous_event["length"])
        if 0 <= cont_source < start:
            max_len = min(MAX_COPY_LEN, start - cont_source)
            for length in {MIN_COPY_LEN, int(previous_event["length"]), max_len}:
                if MIN_COPY_LEN <= length <= max_len:
                    pool.add(Candidate("copy", length, cont_source))

    source_candidates = set()
    for source in range(max(0, start - 256), start):
        source_candidates.add(source)
    for source in range(min(start, 32)):
        source_candidates.add(source)
    if start > 0:
        step = max(1, start // 32)
        for source in range(0, start, step):
            source_candidates.add(source)

    for source in source_candidates:
        max_len = min(MAX_COPY_LEN, start - source)
        if max_len < MIN_COPY_LEN:
            continue
        for length in {MIN_COPY_LEN, min(16, max_len), min(32, max_len), max_len}:
            if MIN_COPY_LEN <= length <= max_len:
                pool.add(Candidate("copy", length, source))

    return heapq.nlargest(
        TOP_CANDIDATES_PER_STATE,
        pool,
        key=lambda cand: sort_key(cand, policy, prefix, previous_event),
    )


def rank_true_event(
    prefix: str,
    literal_remaining: int,
    previous_event: dict[str, Any] | None,
    event: dict[str, Any],
    policy: str,
) -> dict[str, Any]:
    true = true_candidate(event)
    true_key = sort_key(true, policy, prefix, previous_event)
    better = 0
    found = False
    for candidate in iter_candidates(len(prefix), literal_remaining):
        if candidate == true:
            found = True
            continue
        if sort_key(candidate, policy, prefix, previous_event) > true_key:
            better += 1
    rank = better + 1 if found else None
    total_candidates = candidate_count(len(prefix), literal_remaining)
    return {
        "candidate_count": total_candidates,
        "event_kind": event["kind"],
        "event_length": int(event["length"]),
        "policy": policy,
        "rank": rank,
        "rank_bits": math.log2(rank) if rank else math.log2(total_candidates + 1),
        "raw_choice_bits": math.log2(total_candidates),
        "top1": rank == 1,
        "top5": bool(rank and rank <= 5),
        "top20": bool(rank and rank <= 20),
    }


def evaluate_policy(events: list[dict[str, Any]], stream: str, lit_positions: list[int], literal_len: int, cutoff: int, policy: str) -> dict[str, Any]:
    rows = []
    for index in range(cutoff, len(events)):
        start = int(events[index]["start"])
        prefix = stream[:start]
        previous = events[index - 1] if index > 0 else None
        literal_remaining = literal_len - lit_positions[index]
        rows.append(rank_true_event(prefix, literal_remaining, previous, events[index], policy))
    return {
        "cutoff": cutoff,
        "events": len(rows),
        "model_cost_bits": MODEL_COST_BITS,
        "policy": policy,
        "rank_bits": sum(row["rank_bits"] for row in rows) + MODEL_COST_BITS,
        "raw_choice_bits": sum(row["raw_choice_bits"] for row in rows),
        "saving_bits": sum(row["raw_choice_bits"] for row in rows) - (sum(row["rank_bits"] for row in rows) + MODEL_COST_BITS),
        "top1": sum(row["top1"] for row in rows),
        "top5": sum(row["top5"] for row in rows),
        "top20": sum(row["top20"] for row in rows),
    }


def select_policy(events: list[dict[str, Any]], stream: str, lit_positions: list[int], literal_len: int, cutoff: int) -> str:
    if cutoff <= 1:
        return POLICIES[0]
    scored = []
    for policy in POLICIES:
        rows = []
        for index in range(1, cutoff):
            start = int(events[index]["start"])
            prefix = stream[:start]
            previous = events[index - 1]
            literal_remaining = literal_len - lit_positions[index]
            rows.append(rank_true_event(prefix, literal_remaining, previous, events[index], policy))
        rank_bits = sum(row["rank_bits"] for row in rows) + MODEL_COST_BITS
        raw_bits = sum(row["raw_choice_bits"] for row in rows)
        scored.append((rank_bits - raw_bits, policy))
    return min(scored)[1]


def apply_candidate(prefix: str, literal_tape_text: str, lit_pos: int, candidate: Candidate) -> tuple[str, int] | None:
    if candidate.kind == "literal":
        if lit_pos + candidate.length > len(literal_tape_text):
            return None
        return prefix + literal_tape_text[lit_pos : lit_pos + candidate.length], lit_pos + candidate.length
    if candidate.source is None:
        return None
    copied = prefix[candidate.source : candidate.source + candidate.length]
    if len(copied) != candidate.length:
        return None
    return prefix + copied, lit_pos


def beam_suffix(
    events: list[dict[str, Any]],
    stream: str,
    literal_tape_text: str,
    lit_positions: list[int],
    cutoff: int,
    policy: str,
    width: int,
) -> dict[str, Any]:
    start_text = stream[: int(events[cutoff]["start"])]
    start_lit = lit_positions[cutoff]
    true_suffix = [true_candidate(event) for event in events[cutoff : min(len(events), cutoff + MAX_BEAM_EVENTS)]]
    beam: list[tuple[float, str, int, tuple[Candidate, ...], dict[str, Any] | None]] = [
        (0.0, start_text, start_lit, tuple(), events[cutoff - 1] if cutoff > 0 else None)
    ]
    survives = 0
    for step, true in enumerate(true_suffix):
        expanded = []
        for cost, text, lit_pos, suffix, previous_event in beam:
            literal_remaining = len(literal_tape_text) - lit_pos
            for rank, candidate in enumerate(beam_candidate_pool(text, literal_remaining, previous_event, policy), start=1):
                applied = apply_candidate(text, literal_tape_text, lit_pos, candidate)
                if applied is None:
                    continue
                new_text, new_lit = applied
                synthetic_event = {
                    "kind": candidate.kind,
                    "length": candidate.length,
                    "source": candidate.source if candidate.source is not None else -1,
                    "start": len(text),
                }
                expanded.append((cost + math.log2(rank), new_text, new_lit, suffix + (candidate,), synthetic_event))
        beam = heapq.nsmallest(width, expanded, key=lambda item: item[0])
        suffixes = {item[3] for item in beam}
        if tuple(true_suffix[: step + 1]) in suffixes:
            survives = step + 1
    final_suffixes = [item[3] for item in beam]
    exact = tuple(true_suffix) in final_suffixes
    return {
        "beam_width": width,
        "events_tested": len(true_suffix),
        "exact_suffix_in_beam": exact,
        "true_survives_events": survives,
    }


def make_result() -> dict[str, Any]:
    payload = load_json(PAYLOAD_GATE)
    v9 = load_json(V9_GATE)
    assert_boundary("payload", payload)
    assert_boundary("v9", v9)
    if payload["classification"] != "PROMOTED_UNIFIED_INNOVATION_PAYLOAD_LEDGER":
        raise RuntimeError("payload replay is not promoted")
    if v9["classification"] != "PROMOTED_EXECUTABLE_V9_INNOVATION_COPY_CONTINUATION_LEDGER":
        raise RuntimeError("v9 is not promoted")
    events = payload["event_ledger"]
    stream = render_events(events)
    lit_tape = literal_tape(events)
    lit_pos = literal_positions(events)

    splits = []
    for cutoff in EVENT_PREFIX_CUTOFFS:
        policy = select_policy(events, stream, lit_pos, len(lit_tape), cutoff)
        evaluated = evaluate_policy(events, stream, lit_pos, len(lit_tape), cutoff, policy)
        evaluated["beam"] = [
            beam_suffix(events, stream, lit_tape, lit_pos, cutoff, policy, width)
            for width in BEAM_WIDTHS
        ]
        splits.append(evaluated)

    promoted = (
        sum(split["saving_bits"] > 0 for split in splits) >= 2
        and sum(any(row["exact_suffix_in_beam"] for row in split["beam"]) for split in splits) >= 1
    )
    return {
        "schema": "causal_content_aware_event_policy_gate.v1",
        "scope": "analysis_only_causal_content_aware_event_policy",
        "classification": (
            "PROMOTED_CAUSAL_CONTENT_AWARE_EVENT_POLICY_CANDIDATE"
            if promoted
            else "causal_content_aware_event_policy_not_promoted"
        ),
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "translation_delta": "NONE",
        "plaintext_claim": False,
        "case_reopened": False,
        "row0_status": "unchanged_exogenous",
        "compression_bound_status": "unchanged",
        "inputs": {
            "payload_gate": rel(PAYLOAD_GATE),
            "v9_gate": rel(V9_GATE),
        },
        "policies": POLICIES,
        "splits": splits,
        "summary": {
            "event_count": len(events),
            "literal_tape_digits": len(lit_tape),
            "positive_splits": sum(split["saving_bits"] > 0 for split in splits),
            "top1_total": sum(split["top1"] for split in splits),
            "top5_total": sum(split["top5"] for split in splits),
            "top20_total": sum(split["top20"] for split in splits),
            "total_rank_bits": sum(split["rank_bits"] for split in splits),
            "total_raw_choice_bits": sum(split["raw_choice_bits"] for split in splits),
            "total_saving_bits": sum(split["saving_bits"] for split in splits),
            "beam_exact_splits": sum(any(row["exact_suffix_in_beam"] for row in split["beam"]) for split in splits),
            "promoted": promoted,
        },
        "decision": {
            "causal_content_aware_policy_promoted": promoted,
            "v9_reduction_bits": 0.0,
            "reason": (
                "content-aware candidate ranking reduces event choices and keeps true suffix in beam"
                if promoted
                else "content-aware ranking does not produce a complete event decoder; true suffixes do not survive finite beams"
            ),
            "next_blocker": (
                "candidate ranking is insufficient without a stronger global objective or external authoring source"
                if not promoted
                else "candidate needs executable integration with paid corrections"
            ),
        },
    }


def write_markdown(result: dict[str, Any]) -> None:
    lines = [
        "# Causal Content-Aware Event Policy Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        "This gate ranks literal/copy event candidates using only emitted content, literal tape position, and copy-lineage features.",
        "",
        "| Cutoff | Policy | Events | Saving Bits | Top1 | Top5 | Top20 | Beam Exact | Max Survives |",
        "| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for split in result["splits"]:
        max_survives = max(row["true_survives_events"] for row in split["beam"])
        beam_exact = sum(row["exact_suffix_in_beam"] for row in split["beam"])
        lines.append(
            f"| {split['cutoff']} | `{split['policy']}` | {split['events']} | {split['saving_bits']:.3f} | {split['top1']} | {split['top5']} | {split['top20']} | {beam_exact} | {max_survives} |"
        )
    s = result["summary"]
    lines.extend(
        [
            "",
            "## Totals",
            "",
            f"- Total saving bits vs raw candidate choice: `{s['total_saving_bits']:.3f}`.",
            f"- Positive splits: `{s['positive_splits']}/3`.",
            f"- Exact suffix beam splits: `{s['beam_exact_splits']}/3`.",
            f"- Top-20 true event hits: `{s['top20_total']}`.",
            "",
            "## Decision",
            "",
            f"`{result['decision']['reason']}`",
            "",
            "No v9 reduction is integrated in this run.",
            "",
            "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        ]
    )
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Final Causal Content-Aware Event Policy Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        "This audit tests the remaining internal route after simple event n-grams failed: content-aware event selection over the v9 innovation replay.",
        "At each true event boundary, it enumerates causal literal/copy candidates from the emitted stream and literal tape, selects a policy on prefix events, and checks both paid rank and finite-beam survival.",
        "",
        f"Across the three prefix holdouts, total rank saving is `{s['total_saving_bits']:.3f}` bits, with `{s['positive_splits']}/3` positive splits and `{s['beam_exact_splits']}/3` exact suffix beam hits.",
        f"True events are top-20 in `{s['top20_total']}` suffix decisions, but this does not become a complete event decoder.",
        "",
        "## Decision",
        "",
        f"`{result['classification']}`.",
        "",
        result["decision"]["reason"].capitalize() + ".",
        "",
        "This does not change v9, row0, plaintext, semantics, or the compression bound.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_causal_content_aware_event_policy_gate.py](../scripts/01_causal_content_aware_event_policy_gate.py)",
        "- [01_causal_content_aware_event_policy_gate.json](test_results/01_causal_content_aware_event_policy_gate.json)",
        "- [01_causal_content_aware_event_policy_gate.md](test_results/01_causal_content_aware_event_policy_gate.md)",
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
