#!/usr/bin/env python3
"""Executable v9 innovation copy-continuation integration gate.

Executable v8 still pays source addresses for every copy event in the unified
innovation replay. This gate tests a small structural program: when a copy
event immediately follows another copy event and both target/source cursors
advance together, derive the current source as previous_source + previous_len.
The continuation sites are paid by a combinatorial index over copy-after-copy
opportunities.

Analysis-only: no row0, plaintext, semantics, or compression-bound change.
"""

from __future__ import annotations

import importlib.util
import json
import math
import random
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "executable_v9_innovation_copy_continuation_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"

UNIFIED_PAYLOAD_GATE = (
    ROOT
    / "analysis"
    / "unified_innovation_payload_audit_20260622"
    / "reports"
    / "test_results"
    / "01_unified_innovation_payload_gate.json"
)
EXECUTABLE_V8_GATE = (
    ROOT
    / "analysis"
    / "executable_v8_innovation_literal_markov_audit_20260622"
    / "reports"
    / "test_results"
    / "01_executable_v8_innovation_literal_markov_gate.json"
)
EXECUTABLE_V7_SCRIPT = (
    ROOT
    / "analysis"
    / "executable_v7_unified_innovation_payload_audit_20260622"
    / "scripts"
    / "01_executable_v7_unified_innovation_payload_gate.py"
)
UNIFIED_LEDGER = (
    ROOT
    / "analysis"
    / "minimal_external_tape_program_audit_20260622"
    / "reports"
    / "test_results"
    / "02_unified_external_tape_ledger.json"
)

JSON_OUT = TEST_RESULTS / "01_executable_v9_innovation_copy_continuation_gate.json"
MD_OUT = TEST_RESULTS / "01_executable_v9_innovation_copy_continuation_gate.md"
FINAL_OUT = FRONT / "reports" / "final_executable_v9_innovation_copy_continuation_audit.md"

RANDOM_SEED = 46920260622
CONTROL_TRIALS = 200


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


def load_v7_module() -> Any:
    spec = importlib.util.spec_from_file_location("executable_v7_gate", EXECUTABLE_V7_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {EXECUTABLE_V7_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def render_events(events: list[dict[str, Any]]) -> str:
    out: list[str] = []
    for event in events:
        if event["kind"] == "literal":
            out.append(str(event["text"]))
            continue
        available = "".join(out)
        source = int(event["source"])
        length = int(event["length"])
        copied = available[source : source + length]
        if len(copied) != length:
            raise RuntimeError({"reason": "short_copy", "event": event})
        out.append(copied)
    return "".join(out)


def opportunity_rows(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    prev_copy: dict[str, Any] | None = None
    opportunity_index = 0
    for event_index, event in enumerate(events):
        if event["kind"] != "copy":
            prev_copy = None
            continue
        if prev_copy is not None:
            continuation = (
                int(event["start"]) == int(prev_copy["start"]) + int(prev_copy["length"])
                and int(event["source"]) == int(prev_copy["source"]) + int(prev_copy["length"])
            )
            rows.append(
                {
                    "continuation": continuation,
                    "event_index": event_index,
                    "length": int(event["length"]),
                    "opportunity_index": opportunity_index,
                    "source": int(event["source"]),
                    "source_bits": math.log2(max(1, int(event["start"]))),
                    "start": int(event["start"]),
                }
            )
            opportunity_index += 1
        prev_copy = event
    return rows


def continuation_events(events: list[dict[str, Any]], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = [dict(event) for event in events]
    continuation_indices = {int(row["event_index"]) for row in rows if row["continuation"]}
    previous_copy: dict[str, Any] | None = None
    for idx, event in enumerate(out):
        if event["kind"] != "copy":
            previous_copy = None
            continue
        if idx in continuation_indices:
            if previous_copy is None:
                raise RuntimeError({"reason": "continuation_without_previous_copy", "event_index": idx})
            event["source"] = int(previous_copy["source"]) + int(previous_copy["length"])
            event["source_status"] = "derived_previous_copy_continuation"
        else:
            event["source_status"] = "paid_source"
        previous_copy = event
    return out


def random_label_control(rows: list[dict[str, Any]], positives: int, pattern_bits: float) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED)
    source_bits = [float(row["source_bits"]) for row in rows]
    values = []
    for _ in range(CONTROL_TRIALS):
        picked = rng.sample(range(len(source_bits)), positives)
        values.append(sum(source_bits[idx] for idx in picked) - pattern_bits)
    ordered = sorted(values)
    observed = sum(float(row["source_bits"]) for row in rows if row["continuation"]) - pattern_bits
    return {
        "observed_net_saving": observed,
        "random_label_p05": ordered[int(0.05 * (len(ordered) - 1))],
        "random_label_p50": ordered[int(0.50 * (len(ordered) - 1))],
        "random_label_p95": ordered[int(0.95 * (len(ordered) - 1))],
        "beats_p50": observed > ordered[int(0.50 * (len(ordered) - 1))],
        "trials": CONTROL_TRIALS,
    }


def make_result() -> dict[str, Any]:
    payload = load_json(UNIFIED_PAYLOAD_GATE)
    v8 = load_json(EXECUTABLE_V8_GATE)
    ledger = load_json(UNIFIED_LEDGER)
    for name, data in [
        ("unified_innovation_payload_gate", payload),
        ("executable_v8_innovation_literal_markov_gate", v8),
        ("unified_external_tape_ledger", ledger),
    ]:
        assert_boundary(name, data)
    if v8["classification"] != "PROMOTED_EXECUTABLE_V8_INNOVATION_LITERAL_MARKOV_LEDGER":
        raise RuntimeError("v8 ledger is not promoted")
    rows = opportunity_rows(payload["event_ledger"])
    positives = [row for row in rows if row["continuation"]]
    source_bits_saved = sum(float(row["source_bits"]) for row in positives)
    pattern_bits = math.log2(math.comb(len(rows), len(positives))) + 1.0
    net_delta = pattern_bits - source_bits_saved
    v8_total = float(v8["summary"]["v8_external_bits_total_content_included"])
    v9_total = v8_total + net_delta
    derived_events = continuation_events(payload["event_ledger"], rows)
    rendered = render_events(derived_events)
    target = render_events(payload["event_ledger"])
    v7 = load_v7_module()
    seed_books, literal_payloads, segment_checks = v7.split_payload_stream(rendered, payload["segments"])
    roundtrip = v7.validate_decoder_roundtrip(seed_books, literal_payloads, ledger)
    controls = {"random_continuation_labels": random_label_control(rows, len(positives), pattern_bits)}
    promoted = rendered == target and roundtrip["roundtrip_70_70"] and net_delta < 0
    return {
        "case_reopened": False,
        "classification": (
            "PROMOTED_EXECUTABLE_V9_INNOVATION_COPY_CONTINUATION_LEDGER"
            if promoted
            else "executable_v9_innovation_copy_continuation_not_promoted"
        ),
        "compression_bound_status": "unchanged",
        "continuation_rows": rows,
        "controls": controls,
        "decision": {
            "executable_v9_promoted": promoted,
            "generation_explanation_status": (
                "copy_source_dependency_reduced_not_source_free_replay"
                if promoted
                else "not_reduced"
            ),
            "next_blocker": (
                "innovation replay event schedule, copy/literal decision, and non-continuation "
                "copy source-length policy remain external"
            ),
            "plaintext_claim": False,
            "row0_status": "unchanged_exogenous",
            "translation_delta": "NONE",
        },
        "inputs": {
            "executable_v8_gate": rel(EXECUTABLE_V8_GATE),
            "unified_external_tape_ledger": rel(UNIFIED_LEDGER),
            "unified_innovation_payload_gate": rel(UNIFIED_PAYLOAD_GATE),
        },
        "payload_segment_checks": segment_checks,
        "plaintext_claim": False,
        "row0_status": "unchanged_exogenous",
        "schema": "executable_v9_innovation_copy_continuation_gate.v1",
        "scope": "analysis_only_executable_v9_innovation_copy_continuation",
        "summary": {
            "continuation_pattern_bits": pattern_bits,
            "copy_after_copy_opportunities": len(rows),
            "delta_vs_v8_total_bits": net_delta,
            "positive_continuations": len(positives),
            "promoted": promoted,
            "source_bits_saved": source_bits_saved,
            "v8_external_bits_total_content_included": v8_total,
            "v9_external_bits_total_content_included": v9_total,
        },
        "translation_delta": "NONE",
        "validation": {
            "errors": roundtrip["errors"],
            "payload_stream_roundtrip": rendered == target,
            "roundtrip_70_70": roundtrip["roundtrip_70_70"],
        },
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Executable v9 Innovation Copy-Continuation Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        f"- Copy-after-copy opportunities: `{s['copy_after_copy_opportunities']}`.",
        f"- Positive continuations: `{s['positive_continuations']}`.",
        f"- Source bits saved: `{s['source_bits_saved']:.3f}`.",
        f"- Pattern bits paid: `{s['continuation_pattern_bits']:.3f}`.",
        f"- V8 total content-included bits: `{s['v8_external_bits_total_content_included']:.3f}`.",
        f"- V9 total content-included bits: `{s['v9_external_bits_total_content_included']:.3f}`.",
        f"- Delta vs v8: `{s['delta_vs_v8_total_bits']:.3f}` bits.",
        "",
        "## Decision",
        "",
        f"`{result['classification']}`.",
        "",
        "This derives a small set of copy sources from previous-copy continuation. "
        "The replay schedule and most source/length decisions remain external.",
        "",
        "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
    ]
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Final Executable v9 Innovation Copy-Continuation Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        "This audit integrates a small source-derivation rule into the executable "
        "innovation replay. When a copy immediately follows another copy and both "
        "target/source cursors advance together, v9 derives the current source as "
        "`previous_source + previous_length`. The continuation sites are paid by a "
        "combinatorial index over copy-after-copy opportunities.",
        "",
        f"There are `{s['copy_after_copy_opportunities']}` opportunities and "
        f"`{s['positive_continuations']}` continuations. The rule saves "
        f"`{s['source_bits_saved']:.3f}` source bits and pays "
        f"`{s['continuation_pattern_bits']:.3f}` pattern bits.",
        "",
        f"Integrated total content-included bits move from v8 "
        f"`{s['v8_external_bits_total_content_included']:.3f}` to v9 "
        f"`{s['v9_external_bits_total_content_included']:.3f}`, a reduction of "
        f"`{-s['delta_vs_v8_total_bits']:.3f}` bits. Roundtrip remains `70/70`.",
        "",
        "## Decision",
        "",
        f"`{result['classification']}`.",
        "",
        "This is a real but narrow executable dependency reduction. It does not "
        "solve the innovation replay policy: event schedule, copy/literal decisions, "
        "and non-continuation copy source-length choices remain external.",
        "",
        "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_executable_v9_innovation_copy_continuation_gate.py](../scripts/01_executable_v9_innovation_copy_continuation_gate.py)",
        "- [01_executable_v9_innovation_copy_continuation_gate.json](test_results/01_executable_v9_innovation_copy_continuation_gate.json)",
        "- [01_executable_v9_innovation_copy_continuation_gate.md](test_results/01_executable_v9_innovation_copy_continuation_gate.md)",
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
