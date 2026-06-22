#!/usr/bin/env python3
"""Target-free global content objective for the innovation replay.

The previous content-aware gate found that causal features improve rank but do
not decode the event suffix. This gate tests a stronger target-free objective:
given an emitted prefix, the remaining literal tape, and the final stream
length, can a beam search minimize event cost and generate the true suffix?

The decoder never scores candidates against the target stream. The target is
used only after decoding for validation and exact-suffix checks.
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
FRONT = ROOT / "analysis/global_content_objective_event_program_audit_20260622"
OUT_DIR = FRONT / "reports/test_results"
JSON_OUT = OUT_DIR / "01_global_content_objective_event_program_gate.json"
MD_OUT = OUT_DIR / "01_global_content_objective_event_program_gate.md"
FINAL_OUT = FRONT / "reports/final_global_content_objective_event_program_audit.md"

PAYLOAD_GATE = ROOT / "analysis/unified_innovation_payload_audit_20260622/reports/test_results/01_unified_innovation_payload_gate.json"
V9_GATE = ROOT / "analysis/executable_v9_innovation_copy_continuation_audit_20260622/reports/test_results/01_executable_v9_innovation_copy_continuation_gate.json"

LOG2_10 = math.log2(10)
MIN_COPY_LEN = 8
MAX_COPY_LEN = 64
EVENT_PREFIX_CUTOFFS = [20, 35, 50]
BEAM_WIDTHS = [16, 64]
MAX_EVENTS = 40


@dataclass(frozen=True)
class Action:
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
    out: list[str] = []
    for event in events:
        if event["kind"] == "literal":
            out.append(str(event["text"]))
        else:
            available = "".join(out)
            out.append(available[int(event["source"]) : int(event["source"]) + int(event["length"])])
    return "".join(out)


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


def true_actions(events: list[dict[str, Any]], start_index: int, count: int) -> tuple[Action, ...]:
    actions: list[Action] = []
    for event in events[start_index : start_index + count]:
        if event["kind"] == "literal":
            actions.append(Action("literal", int(event["length"])))
        else:
            actions.append(Action("copy", int(event["length"]), int(event["source"])))
    return tuple(actions)


def action_cost(action: Action, prefix_len: int) -> float:
    if action.kind == "literal":
        return 1.0 + math.log2(max(1, action.length)) + action.length * LOG2_10
    source_bits = math.log2(max(1, (action.source or 0) + 1))
    length_bits = math.log2(max(1, action.length - MIN_COPY_LEN + 1))
    return 1.0 + source_bits + length_bits


def action_pool(text: str, lit_pos: int, literal_text: str, target_len: int) -> list[Action]:
    remaining_output = target_len - len(text)
    remaining_literal = len(literal_text) - lit_pos
    pool: set[Action] = set()
    for length in [1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, remaining_literal, remaining_output]:
        if 1 <= length <= remaining_literal and length <= remaining_output:
            pool.add(Action("literal", length))

    prefix_len = len(text)
    source_candidates = set()
    for source in range(max(0, prefix_len - 96), prefix_len, 4):
        source_candidates.add(source)
    for source in range(min(prefix_len, 16)):
        source_candidates.add(source)
    if prefix_len > 0:
        step = max(1, prefix_len // 16)
        for source in range(0, prefix_len, step):
            source_candidates.add(source)

    for source in source_candidates:
        max_len = min(MAX_COPY_LEN, prefix_len - source, remaining_output)
        if max_len < MIN_COPY_LEN:
            continue
        for length in [MIN_COPY_LEN, min(16, max_len), min(32, max_len), min(48, max_len), max_len]:
            if MIN_COPY_LEN <= length <= max_len:
                pool.add(Action("copy", length, source))

    return heapq.nsmallest(20, pool, key=lambda action: action_cost(action, prefix_len))


def apply_action(text: str, literal_text: str, lit_pos: int, action: Action) -> tuple[str, int] | None:
    if action.kind == "literal":
        if lit_pos + action.length > len(literal_text):
            return None
        return text + literal_text[lit_pos : lit_pos + action.length], lit_pos + action.length
    if action.source is None:
        return None
    chunk = text[action.source : action.source + action.length]
    if len(chunk) != action.length:
        return None
    return text + chunk, lit_pos


def exact_prefix_len(a: str, b: str) -> int:
    n = min(len(a), len(b))
    for idx in range(n):
        if a[idx] != b[idx]:
            return idx
    return n


def decode_suffix(
    prefix: str,
    literal_text: str,
    lit_pos: int,
    target_len: int,
    width: int,
    true: str,
    true_actions_prefix: tuple[Action, ...],
) -> dict[str, Any]:
    beam: list[tuple[float, str, int, tuple[Action, ...]]] = [(0.0, prefix, lit_pos, tuple())]
    true_survives = 0
    for _ in range(MAX_EVENTS):
        completed = [
            row
            for row in beam
            if len(row[1]) == target_len and row[2] == len(literal_text)
        ]
        if completed:
            beam = heapq.nsmallest(width, completed + beam, key=lambda row: row[0])
            break
        expanded: list[tuple[float, str, int, tuple[Action, ...]]] = []
        for cost, text, lp, actions in beam:
            if len(text) >= target_len:
                if len(text) == target_len:
                    expanded.append((cost, text, lp, actions))
                continue
            for action in action_pool(text, lp, literal_text, target_len):
                applied = apply_action(text, literal_text, lp, action)
                if applied is None:
                    continue
                new_text, new_lp = applied
                if len(new_text) > target_len:
                    continue
                expanded.append((cost + action_cost(action, len(text)), new_text, new_lp, actions + (action,)))
        if not expanded:
            break
        beam = heapq.nsmallest(width, expanded, key=lambda row: row[0])
        action_prefixes = {row[3] for row in beam}
        for length in range(true_survives + 1, min(len(true_actions_prefix), max(len(row[3]) for row in beam)) + 1):
            if true_actions_prefix[:length] in action_prefixes:
                true_survives = length
            else:
                break

    best = min(beam, key=lambda row: row[0])
    exact_rows = [row for row in beam if row[1] == true and row[2] == len(literal_text)]
    exact_rank = None
    if exact_rows:
        ordered = sorted(beam, key=lambda row: row[0])
        for idx, row in enumerate(ordered, start=1):
            if row[1] == true and row[2] == len(literal_text):
                exact_rank = idx
                break
    return {
        "best_cost": best[0],
        "best_exact_prefix_digits": exact_prefix_len(best[1], true),
        "best_len": len(best[1]),
        "best_literal_pos": best[2],
        "best_action_count": len(best[3]),
        "exact_target_in_beam": bool(exact_rows),
        "exact_target_rank": exact_rank,
        "final_beam_size": len(beam),
        "true_action_survives": true_survives,
        "width": width,
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
    target = render_events(events)
    literal_text = literal_tape(events)
    lit_pos_by_event = literal_positions(events)
    rows = []
    for cutoff in EVENT_PREFIX_CUTOFFS:
        prefix = target[: int(events[cutoff]["start"])]
        lit_pos = lit_pos_by_event[cutoff]
        true_prefix_actions = true_actions(events, cutoff, MAX_EVENTS)
        decodes = [
            decode_suffix(prefix, literal_text, lit_pos, len(target), width, target, true_prefix_actions)
            for width in BEAM_WIDTHS
        ]
        rows.append(
            {
                "cutoff": cutoff,
                "prefix_digits": len(prefix),
                "remaining_digits": len(target) - len(prefix),
                "literal_remaining": len(literal_text) - lit_pos,
                "decodes": decodes,
            }
        )

    promoted = any(any(row["exact_target_in_beam"] for row in split["decodes"]) for split in rows)
    return {
        "schema": "global_content_objective_event_program_gate.v1",
        "scope": "analysis_only_global_content_objective_event_program",
        "classification": (
            "PROMOTED_GLOBAL_CONTENT_OBJECTIVE_EVENT_PROGRAM_CANDIDATE"
            if promoted
            else "global_content_objective_event_program_not_promoted"
        ),
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "translation_delta": "NONE",
        "plaintext_claim": False,
        "case_reopened": False,
        "row0_status": "unchanged_exogenous",
        "compression_bound_status": "unchanged",
        "inputs": {"payload_gate": rel(PAYLOAD_GATE), "v9_gate": rel(V9_GATE)},
        "cutoffs": EVENT_PREFIX_CUTOFFS,
        "beam_widths": BEAM_WIDTHS,
        "summary": {
            "exact_beam_splits": sum(any(row["exact_target_in_beam"] for row in split["decodes"]) for split in rows),
            "max_true_action_survives": max(row["true_action_survives"] for split in rows for row in split["decodes"]),
            "best_exact_prefix_digits": max(row["best_exact_prefix_digits"] for split in rows for row in split["decodes"]),
            "target_digits": len(target),
            "literal_tape_digits": len(literal_text),
            "promoted": promoted,
        },
        "splits": rows,
        "decision": {
            "global_content_objective_promoted": promoted,
            "v9_reduction_bits": 0.0,
            "reason": (
                "target-free global event objective keeps the true suffix in beam"
                if promoted
                else "target-free global event objective does not keep or generate the true innovation suffix"
            ),
            "next_blocker": (
                "objective is insufficient without external authoring surface or a stronger causal state"
                if not promoted
                else "candidate needs executable integration and correction ledger"
            ),
        },
    }


def write_markdown(result: dict[str, Any]) -> None:
    lines = [
        "# Global Content Objective Event Program Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        "This target-free decoder receives emitted prefix, remaining literal tape, and final stream length. It minimizes literal/copy event cost without scoring candidates against the target.",
        "",
        "| Cutoff | Width | Best Prefix Digits | True Actions Survive | Exact Target In Beam | Best Len | Literal Pos |",
        "| ---: | ---: | ---: | ---: | --- | ---: | ---: |",
    ]
    for split in result["splits"]:
        for row in split["decodes"]:
            lines.append(
                f"| {split['cutoff']} | {row['width']} | {row['best_exact_prefix_digits']} | {row['true_action_survives']} | `{row['exact_target_in_beam']}` | {row['best_len']} | {row['best_literal_pos']} |"
            )
    s = result["summary"]
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"`{result['decision']['reason']}`",
            "",
            f"Exact beam splits: `{s['exact_beam_splits']}/3`; max true-action survival: `{s['max_true_action_survives']}`; best exact prefix: `{s['best_exact_prefix_digits']}/{s['target_digits']}`.",
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
        "# Final Global Content Objective Event Program Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        "This audit tests the strongest remaining internal route in target-free form: a global content objective over literal/copy events for the v9 innovation replay.",
        "The decoder gets the true emitted prefix, remaining literal tape, and final output length, but does not score candidates against target content.",
        "",
        f"The true suffix is in the final beam for `{s['exact_beam_splits']}/3` prefix holdouts. The maximum true-action survival is `{s['max_true_action_survives']}` events, and the best generated exact prefix is `{s['best_exact_prefix_digits']}/{s['target_digits']}` digits.",
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
        "- [01_global_content_objective_event_program_gate.py](../scripts/01_global_content_objective_event_program_gate.py)",
        "- [01_global_content_objective_event_program_gate.json](test_results/01_global_content_objective_event_program_gate.json)",
        "- [01_global_content_objective_event_program_gate.md](test_results/01_global_content_objective_event_program_gate.md)",
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
