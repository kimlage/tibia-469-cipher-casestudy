#!/usr/bin/env python3
"""Locate the promoted Chayenne holdout spans inside the innovation tape.

The previous gate promoted Chayenne as external holdout validation of the
innovation module bank. This gate asks what that validation actually touches:
replay event boundaries, downstream consumer-segment boundaries, or only
subspans inside larger literal/source segments.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis/chayenne_holdout_boundary_alignment_audit_20260622"
OUT_DIR = FRONT / "reports/test_results"
JSON_OUT = OUT_DIR / "01_chayenne_holdout_boundary_alignment_gate.json"
MD_OUT = OUT_DIR / "01_chayenne_holdout_boundary_alignment_gate.md"
FINAL_OUT = FRONT / "reports/final_chayenne_holdout_boundary_alignment_audit.md"

HOLDOUT_GATE = ROOT / "analysis/chayenne_external_holdout_innovation_replay_audit_20260622/reports/test_results/01_chayenne_external_holdout_innovation_replay_gate.json"
PAYLOAD_GATE = ROOT / "analysis/unified_innovation_payload_audit_20260622/reports/test_results/01_unified_innovation_payload_gate.json"


def load_json(path: Path) -> Any:
    with path.open() as f:
        return json.load(f)


def assert_boundary(name: str, data: dict[str, Any]) -> None:
    if data.get("translation_delta") != "NONE":
        raise RuntimeError(f"{name} translation changed")
    if data.get("case_reopened", False) is not False:
        raise RuntimeError(f"{name} reopened case")
    if data.get("plaintext_claim", False) is not False:
        raise RuntimeError(f"{name} introduced plaintext")
    if data.get("row0_status") != "unchanged_exogenous":
        raise RuntimeError(f"{name} changed row0")


def containing_span(rows: list[dict[str, Any]], start: int, end: int) -> dict[str, Any] | None:
    for row in rows:
        row_start = int(row["start"])
        row_end = row_start + int(row["length"]) if "end" not in row else int(row["end"])
        if row_start <= start and end <= row_end:
            out = dict(row)
            out["_computed_end"] = row_end
            return out
    return None


def boundary_set_from_events(events: list[dict[str, Any]]) -> set[int]:
    out = {0}
    for event in events:
        start = int(event["start"])
        out.add(start)
        out.add(start + int(event["length"]))
    return out


def boundary_set_from_segments(segments: list[dict[str, Any]]) -> set[int]:
    out = set()
    for segment in segments:
        out.add(int(segment["start"]))
        out.add(int(segment["end"]))
    return out


def make_result() -> dict[str, Any]:
    holdout = load_json(HOLDOUT_GATE)
    payload = load_json(PAYLOAD_GATE)
    assert_boundary("holdout", holdout)
    assert_boundary("payload", payload)
    if holdout["classification"] != "PROMOTED_CHAYENNE_EXTERNAL_HOLDOUT_VALIDATION":
        raise RuntimeError("Chayenne holdout is not promoted")
    if payload["classification"] != "PROMOTED_UNIFIED_INNOVATION_PAYLOAD_LEDGER":
        raise RuntimeError("payload ledger is not promoted")

    chayenne = next(row for row in holdout["external_rows"] if row["name"] == "chayenne")
    copy_events = [event for event in chayenne["event_samples"] if event["kind"] == "copy"]
    replay_events = payload["event_ledger"]
    consumer_segments = payload["segments"]
    event_boundaries = boundary_set_from_events(replay_events)
    consumer_boundaries = boundary_set_from_segments(consumer_segments)

    rows = []
    for index, event in enumerate(copy_events):
        source_start = int(event["offset"])
        source_end = source_start + int(event["length"])
        replay_container = containing_span(replay_events, source_start, source_end)
        consumer_container = containing_span(consumer_segments, source_start, source_end)
        rows.append(
            {
                "chayenne_copy_index": index,
                "chayenne_target_start": int(event["start"]),
                "source_start": source_start,
                "source_end": source_end,
                "length": int(event["length"]),
                "start_is_replay_boundary": source_start in event_boundaries,
                "end_is_replay_boundary": source_end in event_boundaries,
                "start_is_consumer_boundary": source_start in consumer_boundaries,
                "end_is_consumer_boundary": source_end in consumer_boundaries,
                "replay_event_kind": replay_container["kind"] if replay_container else None,
                "replay_event_start": int(replay_container["start"]) if replay_container else None,
                "replay_event_end": replay_container["_computed_end"] if replay_container else None,
                "consumer_segment_kind": consumer_container["kind"] if consumer_container else None,
                "consumer_segment_label": consumer_container["label"] if consumer_container else None,
                "consumer_segment_start": int(consumer_container["start"]) if consumer_container else None,
                "consumer_segment_end": int(consumer_container["end"]) if consumer_container else None,
                "contained_in_single_replay_event": replay_container is not None,
                "contained_in_single_consumer_segment": consumer_container is not None,
            }
        )

    replay_boundary_aligned = sum(1 for row in rows if row["start_is_replay_boundary"] and row["end_is_replay_boundary"])
    consumer_boundary_aligned = sum(1 for row in rows if row["start_is_consumer_boundary"] and row["end_is_consumer_boundary"])
    replay_contained = sum(1 for row in rows if row["contained_in_single_replay_event"])
    consumer_contained = sum(1 for row in rows if row["contained_in_single_consumer_segment"])

    promotes_event_boundary = replay_boundary_aligned == len(rows) and len(rows) > 0
    promotes_subspan_module = (
        len(rows) > 0
        and replay_boundary_aligned == 0
        and consumer_contained == len(rows)
    )
    classification = (
        "PROMOTED_CHAYENNE_EVENT_BOUNDARY_HOLDOUT"
        if promotes_event_boundary
        else (
            "PROMOTED_CHAYENNE_SUBSPAN_MODULE_HOLDOUT_CLUE_NOT_EVENT_POLICY"
            if promotes_subspan_module
            else "chayenne_holdout_boundary_alignment_not_promoted"
        )
    )

    return {
        "schema": "chayenne_holdout_boundary_alignment_gate.v1",
        "scope": "analysis_only_external_holdout_boundary_localization",
        "classification": classification,
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "translation_delta": "NONE",
        "plaintext_claim": False,
        "case_reopened": False,
        "row0_status": "unchanged_exogenous",
        "compression_bound_status": "unchanged",
        "inputs": {
            "chayenne_external_holdout": str(HOLDOUT_GATE.relative_to(ROOT)),
            "unified_innovation_payload": str(PAYLOAD_GATE.relative_to(ROOT)),
        },
        "summary": {
            "chayenne_copy_spans": len(rows),
            "replay_boundary_aligned_spans": replay_boundary_aligned,
            "consumer_boundary_aligned_spans": consumer_boundary_aligned,
            "contained_in_single_replay_event": replay_contained,
            "contained_in_single_consumer_segment": consumer_contained,
            "promotes_event_boundary": promotes_event_boundary,
            "promotes_subspan_module_holdout": promotes_subspan_module,
        },
        "span_rows": rows,
        "decision": {
            "event_boundary_policy_promoted": promotes_event_boundary,
            "subspan_module_holdout_clue_promoted": promotes_subspan_module,
            "origin_source_promoted": False,
            "external_field_reduced": False,
            "v9_reduction_bits": 0.0,
            "reason": (
                "Chayenne spans align with replay event boundaries"
                if promotes_event_boundary
                else (
                    "Chayenne validates subspans inside the innovation module bank, not replay event boundaries"
                    if promotes_subspan_module
                    else "Chayenne holdout spans do not yield a clean boundary-alignment clue"
                )
            ),
            "next_blocker": "external holdout validation still does not derive the replay event policy or innovation origin",
        },
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Chayenne Holdout Boundary Alignment Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Chayenne copy spans | `{s['chayenne_copy_spans']}` |",
        f"| Replay-boundary aligned spans | `{s['replay_boundary_aligned_spans']}` |",
        f"| Consumer-boundary aligned spans | `{s['consumer_boundary_aligned_spans']}` |",
        f"| Contained in one replay event | `{s['contained_in_single_replay_event']}` |",
        f"| Contained in one consumer segment | `{s['contained_in_single_consumer_segment']}` |",
        "",
        "## Span Rows",
        "",
        "| Copy | Source Span | Replay Event | Consumer Segment | Replay Boundary | Consumer Boundary |",
        "| ---: | --- | --- | --- | ---: | ---: |",
    ]
    for row in result["span_rows"]:
        replay = f"{row['replay_event_kind']}:{row['replay_event_start']}-{row['replay_event_end']}"
        segment = f"{row['consumer_segment_label']}:{row['consumer_segment_start']}-{row['consumer_segment_end']}"
        lines.append(
            f"| `{row['chayenne_copy_index']}` | `{row['source_start']}-{row['source_end']}` | `{replay}` | `{segment}` | `{row['start_is_replay_boundary'] and row['end_is_replay_boundary']}` | `{row['start_is_consumer_boundary'] and row['end_is_consumer_boundary']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"`{result['decision']['reason']}`",
            "",
            "This preserves the positive external holdout result while locating it at subspan/module-bank level, not at replay-event-policy level.",
            "",
            f"Next blocker: `{result['decision']['next_blocker']}`",
            "",
            "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        ]
    )
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Final Chayenne Holdout Boundary Alignment Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        "The promoted Chayenne holdout was localized inside the unified innovation tape.",
        f"Its `{s['chayenne_copy_spans']}` copy spans align with replay event boundaries in `{s['replay_boundary_aligned_spans']}` cases and consumer boundaries in `{s['consumer_boundary_aligned_spans']}` cases.",
        f"Both spans are contained inside single consumer segments (`{s['contained_in_single_consumer_segment']}/{s['chayenne_copy_spans']}`), so the result validates reusable subspans in the module bank rather than the replay event boundary policy.",
        "",
        "## Decision",
        "",
        f"`{result['classification']}`.",
        "",
        "No event policy, origin source, v9 reduction, plaintext, or translation is promoted.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_chayenne_holdout_boundary_alignment_gate.py](../scripts/01_chayenne_holdout_boundary_alignment_gate.py)",
        "- [01_chayenne_holdout_boundary_alignment_gate.json](test_results/01_chayenne_holdout_boundary_alignment_gate.json)",
        "- [01_chayenne_holdout_boundary_alignment_gate.md](test_results/01_chayenne_holdout_boundary_alignment_gate.md)",
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
