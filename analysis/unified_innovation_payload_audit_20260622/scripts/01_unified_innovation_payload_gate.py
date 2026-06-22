#!/usr/bin/env python3
"""Unified innovation payload gate.

The executable v6 ledger still pays two raw content tapes:

* seed books 0..9: 1696 digits / 5633.990 bits
* derived-book literal payload: 266 digits / 883.633 bits

This audit tests whether those two fields can be unified into one executable
innovation payload program. The program receives segment lengths from the
existing decoder contract, then reconstructs the combined innovation stream
with paid literal runs and paid previous-copy events. This is a ledger test, not
a translation or plaintext claim.
"""

from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "unified_innovation_payload_audit_20260622"
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
EXECUTABLE_V6_GATE = (
    ROOT
    / "analysis"
    / "executable_v6_literal_span_origin_audit_20260622"
    / "reports"
    / "test_results"
    / "01_executable_v6_literal_span_origin_gate.json"
)

JSON_OUT = TEST_RESULTS / "01_unified_innovation_payload_gate.json"
MD_OUT = TEST_RESULTS / "01_unified_innovation_payload_gate.md"
FINAL_OUT = FRONT / "reports" / "final_unified_innovation_payload_audit.md"

LOG2_10 = math.log2(10)
MIN_LENS = [3, 4, 5, 6, 8, 10, 12, 16]
MAX_COPY_LEN = 64
RANDOM_SEED = 46920260622
CONTROL_TRIALS = 30
PREFIX_CUTOFFS = [256, 512, 1024, 1536]


@dataclass(frozen=True)
class Segment:
    kind: str
    label: str
    text: str


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
    if decision.get("translation_delta") not in {None, "NONE"}:
        raise RuntimeError(f"{name} changed translation boundary")
    if decision.get("row0_status") not in {None, "unchanged_exogenous"}:
        raise RuntimeError(f"{name} changed row0 status")


def load_segments() -> tuple[list[Segment], dict[str, Any]]:
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    ledger = load_json(UNIFIED_LEDGER)
    v6 = load_json(EXECUTABLE_V6_GATE)
    assert_boundary("unified_external_tape_ledger", ledger)
    assert_boundary("executable_v6_literal_span_origin_gate", v6)
    segments = [
        Segment("seed_book", f"seed_book_{book}", books[book]) for book in range(10)
    ]
    literal_rows = [
        row
        for row in sorted(ledger["ledger_rows"], key=lambda item: (int(item["book"]), int(item["op_index"])))
        if row["op_type"] == "literal"
    ]
    for row in literal_rows:
        payload = str(row["literal_payload"])
        segments.append(
            Segment(
                "derived_literal",
                f"literal_b{row['book']}_op{row['op_index']}_{row['literal_tape_start']}_{row['literal_tape_end']}",
                payload,
            )
        )
    return segments, {"ledger": ledger, "v6": v6}


def event_cost(event: dict[str, Any], stream_len: int) -> float:
    if event["kind"] == "literal":
        remaining = max(1, stream_len - int(event["start"]))
        length_bits = math.log2(max(1, min(MAX_COPY_LEN, remaining)))
        return 1.0 + length_bits + int(event["length"]) * LOG2_10
    source_bits = math.log2(max(1, int(event["start"])))
    length_bits = math.log2(max(1, min(MAX_COPY_LEN, stream_len - int(event["start"]))))
    return 1.0 + source_bits + length_bits


def add_previous_substrings(
    stream: str,
    latest_by_len: dict[int, dict[str, int]],
    old_end: int,
    new_end: int,
) -> None:
    for end in range(old_end + 1, new_end + 1):
        max_len = min(MAX_COPY_LEN, end)
        for length in range(1, max_len + 1):
            latest_by_len.setdefault(length, {})[stream[end - length : end]] = end - length


def longest_previous(
    stream: str,
    pos: int,
    min_len: int,
    latest_by_len: dict[int, dict[str, int]],
) -> tuple[int, int | None]:
    upper = min(MAX_COPY_LEN, len(stream) - pos)
    for length in range(upper, min_len - 1, -1):
        source = latest_by_len.get(length, {}).get(stream[pos : pos + length])
        if source is not None:
            return length, source
    return 0, None


def greedy_parse(stream: str, min_len: int) -> dict[str, Any]:
    raw_events: list[dict[str, Any]] = []
    pos = 0
    latest_by_len: dict[int, dict[str, int]] = {}
    indexed_until = 0
    while pos < len(stream):
        if indexed_until < pos:
            add_previous_substrings(stream, latest_by_len, indexed_until, pos)
            indexed_until = pos
        length, source = longest_previous(stream, pos, min_len, latest_by_len)
        if length >= min_len and source is not None:
            raw_events.append({"kind": "copy", "start": pos, "length": length, "source": source})
            pos += length
            continue
        raw_events.append({"kind": "literal_digit", "start": pos, "length": 1, "text": stream[pos]})
        pos += 1

    events: list[dict[str, Any]] = []
    literal_buffer: list[str] = []
    literal_start: int | None = None
    for event in raw_events:
        if event["kind"] == "literal_digit":
            if literal_start is None:
                literal_start = int(event["start"])
            literal_buffer.append(str(event["text"]))
            continue
        if literal_buffer:
            text = "".join(literal_buffer)
            events.append({"kind": "literal", "start": literal_start, "length": len(text), "text": text})
            literal_buffer = []
            literal_start = None
        events.append(event)
    if literal_buffer:
        text = "".join(literal_buffer)
        events.append({"kind": "literal", "start": literal_start, "length": len(text), "text": text})

    total_bits = sum(event_cost(event, len(stream)) for event in events)
    copy_events = [event for event in events if event["kind"] == "copy"]
    literal_events = [event for event in events if event["kind"] == "literal"]
    copied_digits = sum(int(event["length"]) for event in copy_events)
    literal_digits = sum(int(event["length"]) for event in literal_events)
    return {
        "copied_digits": copied_digits,
        "copy_ops": len(copy_events),
        "delta_vs_raw_bits": total_bits - len(stream) * LOG2_10,
        "events": events,
        "literal_digits": literal_digits,
        "literal_runs": len(literal_events),
        "min_len": min_len,
        "raw_bits": len(stream) * LOG2_10,
        "stream_digits": len(stream),
        "total_bits": total_bits,
    }


def render_events(events: list[dict[str, Any]]) -> str:
    output: list[str] = []
    for event in events:
        if event["kind"] == "literal":
            output.append(str(event["text"]))
            continue
        available = "".join(output)
        source = int(event["source"])
        length = int(event["length"])
        output.append(available[source : source + length])
    return "".join(output)


def split_segments(stream: str, segments: list[Segment]) -> list[dict[str, Any]]:
    out = []
    cursor = 0
    for segment in segments:
        end = cursor + len(segment.text)
        out.append(
            {
                "kind": segment.kind,
                "label": segment.label,
                "length": len(segment.text),
                "matches": stream[cursor:end] == segment.text,
                "start": cursor,
                "end": end,
            }
        )
        cursor = end
    return out


def score_all_minlens(stream: str) -> dict[str, Any]:
    parses = {str(min_len): greedy_parse(stream, min_len) for min_len in MIN_LENS}
    best_key = min(parses, key=lambda key: parses[key]["total_bits"])
    return {"best_min_len": int(best_key), "parses": parses}


def shuffled_digit_controls(stream: str) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED + 11)
    values = []
    copied = []
    for _ in range(CONTROL_TRIALS):
        chars = list(stream)
        rng.shuffle(chars)
        score = score_all_minlens("".join(chars))
        best = score["parses"][str(score["best_min_len"])]
        values.append(float(best["delta_vs_raw_bits"]))
        copied.append(int(best["copied_digits"]))
    ordered = sorted(values)
    copied_ordered = sorted(copied)
    return {
        "copied_digits_p95": copied_ordered[int(0.95 * (len(copied_ordered) - 1))],
        "delta_bits_p05": ordered[int(0.05 * (len(ordered) - 1))],
        "delta_bits_p50": ordered[int(0.50 * (len(ordered) - 1))],
        "delta_bits_p95": ordered[int(0.95 * (len(ordered) - 1))],
        "trials": CONTROL_TRIALS,
    }


def segment_order_controls(segments: list[Segment]) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED + 29)
    values = []
    copied = []
    for _ in range(CONTROL_TRIALS):
        shuffled = list(segments)
        rng.shuffle(shuffled)
        stream = "".join(segment.text for segment in shuffled)
        score = score_all_minlens(stream)
        best = score["parses"][str(score["best_min_len"])]
        values.append(float(best["delta_vs_raw_bits"]))
        copied.append(int(best["copied_digits"]))
    ordered = sorted(values)
    copied_ordered = sorted(copied)
    return {
        "copied_digits_p95": copied_ordered[int(0.95 * (len(copied_ordered) - 1))],
        "delta_bits_p05": ordered[int(0.05 * (len(ordered) - 1))],
        "delta_bits_p50": ordered[int(0.50 * (len(ordered) - 1))],
        "delta_bits_p95": ordered[int(0.95 * (len(ordered) - 1))],
        "trials": CONTROL_TRIALS,
    }


def prefix_holdouts(stream: str) -> list[dict[str, Any]]:
    rows = []
    for cutoff in PREFIX_CUTOFFS:
        if cutoff >= len(stream):
            continue
        train_score = score_all_minlens(stream[:cutoff])
        selected = train_score["best_min_len"]
        test_parse = greedy_parse(stream[cutoff:], selected)
        # Cold-start holdout cannot copy from train in the simple parser above;
        # include a replay variant where the test may copy from frozen prefix.
        replay_stream = stream[:cutoff] + stream[cutoff:]
        full_replay = greedy_parse(replay_stream, selected)
        replay_test_events = [
            event for event in full_replay["events"] if int(event["start"]) >= cutoff
        ]
        replay_bits = sum(event_cost(event, len(replay_stream)) for event in replay_test_events)
        test_raw = (len(stream) - cutoff) * LOG2_10
        rows.append(
            {
                "cold_start_delta_bits": test_parse["delta_vs_raw_bits"],
                "cutoff": cutoff,
                "replay_delta_bits": replay_bits - test_raw,
                "replay_events": len(replay_test_events),
                "replay_test_raw_bits": test_raw,
                "selected_min_len": selected,
                "test_digits": len(stream) - cutoff,
                "train_digits": cutoff,
                "train_delta_bits": train_score["parses"][str(selected)]["delta_vs_raw_bits"],
            }
        )
    return rows


def make_result() -> dict[str, Any]:
    segments, inputs = load_segments()
    stream = "".join(segment.text for segment in segments)
    v6_summary = inputs["v6"]["summary"]
    baseline_bits = float(v6_summary["seed_payload_bits"]) + float(v6_summary["literal_payload_bits"])
    if abs(baseline_bits - len(stream) * LOG2_10) > 1e-6:
        raise RuntimeError({"baseline_bits": baseline_bits, "stream_bits": len(stream) * LOG2_10})
    scored = score_all_minlens(stream)
    best = scored["parses"][str(scored["best_min_len"])]
    rendered = render_events(best["events"])
    segment_roundtrip = split_segments(rendered, segments)
    controls = {
        "same_multiset_digit_shuffle": shuffled_digit_controls(stream),
        "segment_order_shuffle": segment_order_controls(segments),
    }
    holdouts = prefix_holdouts(stream)
    declaration_bits = math.log2(len(MIN_LENS))
    total_with_declaration = float(best["total_bits"]) + declaration_bits
    delta_with_declaration = total_with_declaration - baseline_bits
    beats_digit_control = delta_with_declaration < controls["same_multiset_digit_shuffle"]["delta_bits_p05"]
    beats_order_control = delta_with_declaration < controls["segment_order_shuffle"]["delta_bits_p05"]
    positive_holdouts = sum(1 for row in holdouts if row["replay_delta_bits"] < 0)
    promoted = (
        rendered == stream
        and delta_with_declaration < 0
        and beats_digit_control
        and positive_holdouts >= 3
    )
    weak = rendered == stream and delta_with_declaration < 0 and beats_digit_control
    classification = (
        "PROMOTED_UNIFIED_INNOVATION_PAYLOAD_LEDGER"
        if promoted
        else "WEAK_UNIFIED_INNOVATION_PAYLOAD_CLUE"
        if weak
        else "unified_innovation_payload_not_promoted"
    )
    external_excluding_seed_v6 = float(v6_summary["v6_external_bits_excluding_seed"])
    candidate_external_including_seed = (
        external_excluding_seed_v6
        - float(v6_summary["literal_payload_bits"])
        + total_with_declaration
    )
    result = {
        "case_reopened": False,
        "classification": classification,
        "compression_bound_status": "unchanged",
        "controls": controls,
        "decision": {
            "generation_explanation_status": (
                "paid_content_ledger_reduced_not_source_free_generator"
                if classification.startswith("PROMOTED")
                else "content_payload_surface_only"
            ),
            "plaintext_claim": False,
            "row0_status": "unchanged_exogenous",
            "translation_delta": "NONE",
            "unified_innovation_payload_promoted": promoted,
        },
        "holdouts": holdouts,
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "executable_v6_gate": rel(EXECUTABLE_V6_GATE),
            "unified_external_tape_ledger": rel(UNIFIED_LEDGER),
        },
        "plaintext_claim": False,
        "row0_status": "unchanged_exogenous",
        "schema": "unified_innovation_payload_gate.v1",
        "scope": "analysis_only_unified_innovation_payload",
        "segments": segment_roundtrip,
        "summary": {
            "baseline_seed_plus_literal_bits": baseline_bits,
            "beats_digit_shuffle_p05": beats_digit_control,
            "beats_segment_order_shuffle_p05": beats_order_control,
            "best_min_len": scored["best_min_len"],
            "candidate_external_bits_including_seed_replacing_seed_and_literal_payload": candidate_external_including_seed,
            "copied_digits": int(best["copied_digits"]),
            "copy_ops": int(best["copy_ops"]),
            "delta_bits_after_declaration": delta_with_declaration,
            "literal_digits": int(best["literal_digits"]),
            "literal_runs": int(best["literal_runs"]),
            "min_len_declaration_bits": declaration_bits,
            "positive_replay_holdouts": positive_holdouts,
            "promoted": promoted,
            "raw_stream_bits": len(stream) * LOG2_10,
            "roundtrip_segments": all(item["matches"] for item in segment_roundtrip),
            "roundtrip_stream": rendered == stream,
            "seed_digits": sum(len(segment.text) for segment in segments if segment.kind == "seed_book"),
            "stream_digits": len(stream),
            "total_bits_after_declaration": total_with_declaration,
            "v6_external_bits_excluding_seed": external_excluding_seed_v6,
            "v6_external_bits_including_seed": float(v6_summary["v6_external_bits_including_seed"]),
            "v6_literal_payload_bits": float(v6_summary["literal_payload_bits"]),
            "v6_seed_payload_bits": float(v6_summary["seed_payload_bits"]),
        },
        "translation_delta": "NONE",
        "validation": {
            "errors": [],
            "literal_segments": sum(1 for segment in segments if segment.kind == "derived_literal"),
            "roundtrip_stream": rendered == stream,
            "seed_segments": sum(1 for segment in segments if segment.kind == "seed_book"),
        },
    }
    result["event_ledger"] = best["events"]
    # Keep convenient samples near the summary for quick review.
    result["event_samples"] = {
        "first": best["events"][:40],
        "last": best["events"][-20:],
    }
    result["scoreboard"] = {
        min_len: {
            key: value
            for key, value in parse.items()
            if key != "events"
        }
        for min_len, parse in scored["parses"].items()
    }
    return result


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Unified Innovation Payload Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        f"- Stream digits: `{s['stream_digits']}` (`{s['seed_digits']}` seed + `{s['stream_digits'] - s['seed_digits']}` derived literal).",
        f"- Raw seed+literal payload bits: `{s['baseline_seed_plus_literal_bits']:.3f}`.",
        f"- Best min_len: `{s['best_min_len']}`.",
        f"- Paid replay bits after min_len declaration: `{s['total_bits_after_declaration']:.3f}`.",
        f"- Delta after declaration: `{s['delta_bits_after_declaration']:.3f}` bits.",
        f"- Candidate total replacing v6 seed+literal payloads: `{s['candidate_external_bits_including_seed_replacing_seed_and_literal_payload']:.3f}`.",
        f"- Copied digits: `{s['copied_digits']}`; literal digits: `{s['literal_digits']}`.",
        f"- Replay holdouts positive: `{s['positive_replay_holdouts']}/{len(result['holdouts'])}`.",
        f"- Beats same-multiset digit shuffle p05: `{s['beats_digit_shuffle_p05']}`.",
        f"- Beats segment-order shuffle p05: `{s['beats_segment_order_shuffle_p05']}`.",
        "",
        "## Decision",
        "",
        f"`{result['classification']}`.",
        "",
        "This is a paid innovation-payload ledger test. It does not infer plaintext, "
        "does not change row0, and does not make the replay policy source-free.",
        "",
        "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
    ]
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Final Unified Innovation Payload Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        "This audit stops treating seed payload and derived-book literal payload as "
        "separate content fields. It concatenates the `1696` seed digits and the "
        "`266` v6 literal digits into one innovation stream, then asks whether a "
        "paid previous-copy/literal replay ledger can reconstruct that stream more "
        "cheaply than raw declaration.",
        "",
        f"The raw stream has `{s['stream_digits']}` digits and costs "
        f"`{s['baseline_seed_plus_literal_bits']:.3f}` bits. The best paid replay "
        f"uses `min_len={s['best_min_len']}`, copies `{s['copied_digits']}` digits, "
        f"leaves `{s['literal_digits']}` literal digits, and costs "
        f"`{s['total_bits_after_declaration']:.3f}` bits after declaring the min_len. "
        f"Delta: `{s['delta_bits_after_declaration']:.3f}` bits.",
        "",
        f"If used to replace v6's separate seed and literal payload declarations, "
        f"the executable ledger including seed moves from "
        f"`{s['v6_external_bits_including_seed']:.3f}` to "
        f"`{s['candidate_external_bits_including_seed_replacing_seed_and_literal_payload']:.3f}` bits.",
        "",
        f"Controls: same-multiset digit shuffle beaten at p05 is "
        f"`{s['beats_digit_shuffle_p05']}`; segment-order shuffle beaten at p05 is "
        f"`{s['beats_segment_order_shuffle_p05']}`. Replay prefix holdouts are "
        f"positive in `{s['positive_replay_holdouts']}/{len(result['holdouts'])}` splits.",
        "",
        "## Decision",
        "",
        f"`{result['classification']}`.",
        "",
        "This can only be promoted as a paid payload-ledger reduction if it beats "
        "the controls and holdouts. It is not a source-free generator: copy starts "
        "and payload replay are still target-conditioned by the known innovation "
        "stream. The remaining generative blocker is the policy that decides when "
        "and why those innovation chunks are introduced.",
        "",
        "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_unified_innovation_payload_gate.py](../scripts/01_unified_innovation_payload_gate.py)",
        "- [01_unified_innovation_payload_gate.json](test_results/01_unified_innovation_payload_gate.json)",
        "- [01_unified_innovation_payload_gate.md](test_results/01_unified_innovation_payload_gate.md)",
    ]
    FINAL_OUT.write_text("\n".join(lines) + "\n")


def main() -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    result = make_result()
    if result["translation_delta"] != "NONE":
        raise RuntimeError("translation boundary changed")
    if result["plaintext_claim"] is not False or result["case_reopened"] is not False:
        raise RuntimeError("semantic boundary violated")
    if result["row0_status"] != "unchanged_exogenous":
        raise RuntimeError("row0 boundary changed")
    JSON_OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_markdown(result)
    write_final(result)
    print(json.dumps(result["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
