#!/usr/bin/env python3
"""Innovation replay policy frontier gate.

Executable v7 reduces the raw content payload by replaying one innovation
stream with a paid target-conditioned previous-copy ledger. This audit asks the
next generative question: can simple online policies reproduce that replay from
decoder-visible state, or is the copy/literal decision still external?

Analysis-only: no row0, plaintext, semantics, or compression-bound change.
"""

from __future__ import annotations

import json
import math
import random
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "innovation_replay_policy_frontier_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"

UNIFIED_PAYLOAD_GATE = (
    ROOT
    / "analysis"
    / "unified_innovation_payload_audit_20260622"
    / "reports"
    / "test_results"
    / "01_unified_innovation_payload_gate.json"
)
EXECUTABLE_V7_GATE = (
    ROOT
    / "analysis"
    / "executable_v7_unified_innovation_payload_audit_20260622"
    / "reports"
    / "test_results"
    / "01_executable_v7_unified_innovation_payload_gate.json"
)

JSON_OUT = TEST_RESULTS / "01_innovation_replay_policy_frontier_gate.json"
MD_OUT = TEST_RESULTS / "01_innovation_replay_policy_frontier_gate.md"
FINAL_OUT = FRONT / "reports" / "final_innovation_replay_policy_frontier_audit.md"

MIN_LENS = [4, 6, 8, 10, 12, 16]
LOOKAHEADS = [2, 3, 4, 5, 6, 8]
MAX_COPY_LEN = 64
LOG2_10 = math.log2(10)
RANDOM_SEED = 46920260622
SHUFFLE_TRIALS = 40


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


def render_events(events: list[dict[str, Any]]) -> str:
    out: list[str] = []
    for event in events:
        if event["kind"] == "literal":
            out.append(str(event["text"]))
        else:
            available = "".join(out)
            source = int(event["source"])
            length = int(event["length"])
            out.append(available[source : source + length])
    return "".join(out)


def literal_tape(events: list[dict[str, Any]]) -> str:
    return "".join(str(event["text"]) for event in events if event["kind"] == "literal")


def exact_prefix_len(a: str, b: str) -> int:
    n = min(len(a), len(b))
    for i in range(n):
        if a[i] != b[i]:
            return i
    return n


def correction_bits(generated: str, target: str) -> float:
    prefix = exact_prefix_len(generated, target)
    return (len(target) - prefix) * LOG2_10


def find_previous_prefix(available: str, prefix: str, min_len: int) -> tuple[int, int] | None:
    if len(prefix) < min_len:
        return None
    max_len = min(MAX_COPY_LEN, len(prefix))
    for length in range(max_len, min_len - 1, -1):
        needle = prefix[:length]
        source = available.rfind(needle)
        if source >= 0:
            return source, length
    return None


def find_suffix_continuation(available: str, min_len: int, lookahead: int) -> tuple[int, int] | None:
    if len(available) < lookahead:
        return None
    suffix = available[-lookahead:]
    source = available[:-lookahead].rfind(suffix)
    if source < 0:
        return None
    max_len = min(MAX_COPY_LEN, len(available) - source)
    if max_len < min_len:
        return None
    return source + lookahead, min(max_len - lookahead, MAX_COPY_LEN)


def run_policy(
    policy: str,
    target_len: int,
    lit_tape: str,
    *,
    min_len: int,
    lookahead: int,
) -> dict[str, Any]:
    out: list[str] = []
    lit_pos = 0
    copy_ops = 0
    literal_digits = 0
    guard = 0
    while len("".join(out)) < target_len and guard < target_len * 4:
        guard += 1
        available = "".join(out)
        remaining = target_len - len(available)
        action: tuple[int, int] | None = None
        if policy == "literal_only":
            action = None
        elif policy == "copy_literal_prefix_latest":
            action = find_previous_prefix(available, lit_tape[lit_pos:], min_len)
        elif policy == "copy_literal_prefix_then_literal":
            action = find_previous_prefix(available, lit_tape[lit_pos:], min_len)
        elif policy == "copy_suffix_continuation":
            action = find_suffix_continuation(available, min_len, lookahead)
        elif policy == "copy_suffix_else_literal_prefix":
            action = find_suffix_continuation(available, min_len, lookahead)
            if action is None:
                action = find_previous_prefix(available, lit_tape[lit_pos:], min_len)
        else:
            raise KeyError(policy)

        if action is not None:
            source, length = action
            length = max(0, min(length, remaining, len(available) - source))
            if length >= min_len:
                out.append(available[source : source + length])
                copy_ops += 1
                continue
        if lit_pos >= len(lit_tape):
            break
        out.append(lit_tape[lit_pos])
        lit_pos += 1
        literal_digits += 1
    rendered = "".join(out)[:target_len]
    return {
        "copy_ops": copy_ops,
        "exact_prefix": None,
        "literal_digits_consumed": literal_digits,
        "lookahead": lookahead,
        "min_len": min_len,
        "policy": policy,
        "rendered_len": len(rendered),
        "rendered": rendered,
    }


def score_policy(row: dict[str, Any], target: str, v7_bits: float) -> dict[str, Any]:
    rendered = str(row["rendered"])
    prefix = exact_prefix_len(rendered, target)
    corr = correction_bits(rendered, target)
    # Policy declaration is intentionally small; if it still fails, the result
    # is not a parameter-accounting artifact.
    model_bits = math.log2(5) + math.log2(len(MIN_LENS)) + math.log2(len(LOOKAHEADS))
    total = model_bits + row["literal_digits_consumed"] * LOG2_10 + corr
    return {
        "copy_ops": int(row["copy_ops"]),
        "delta_vs_v7_payload_replay_bits": total - v7_bits,
        "exact_prefix": prefix,
        "literal_digits_consumed": int(row["literal_digits_consumed"]),
        "lookahead": int(row["lookahead"]),
        "min_len": int(row["min_len"]),
        "policy": row["policy"],
        "rendered_len": int(row["rendered_len"]),
        "suffix_correction_bits": corr,
        "total_bits_after_suffix_correction": total,
    }


def boundary_alignment(events: list[dict[str, Any]], segments: list[dict[str, Any]]) -> dict[str, Any]:
    segment_bounds = {0}
    for segment in segments:
        segment_bounds.add(int(segment["start"]))
        segment_bounds.add(int(segment["end"]))
    event_bounds = {0}
    for event in events:
        event_bounds.add(int(event["start"]))
        event_bounds.add(int(event["start"]) + int(event["length"]))
    copy_events = [event for event in events if event["kind"] == "copy"]
    return {
        "event_count": len(events),
        "event_end_on_segment_boundary": sum(1 for event in events if int(event["start"]) + int(event["length"]) in segment_bounds),
        "event_start_on_segment_boundary": sum(1 for event in events if int(event["start"]) in segment_bounds),
        "event_start_end_on_segment_boundary": sum(
            1
            for event in events
            if int(event["start"]) in segment_bounds
            and int(event["start"]) + int(event["length"]) in segment_bounds
        ),
        "copy_source_end_on_event_boundary": sum(
            1 for event in copy_events if int(event["source"]) + int(event["length"]) in event_bounds
        ),
        "copy_source_start_on_event_boundary": sum(1 for event in copy_events if int(event["source"]) in event_bounds),
        "copy_source_start_end_on_event_boundary": sum(
            1
            for event in copy_events
            if int(event["source"]) in event_bounds
            and int(event["source"]) + int(event["length"]) in event_bounds
        ),
        "copy_event_count": len(copy_events),
        "segment_boundary_count": len(segment_bounds),
    }


def shuffled_literal_tape_control(target: str, lit_tape: str, best_policy: dict[str, Any]) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED)
    values = []
    for _ in range(SHUFFLE_TRIALS):
        chars = list(lit_tape)
        rng.shuffle(chars)
        row = run_policy(
            str(best_policy["policy"]),
            len(target),
            "".join(chars),
            min_len=int(best_policy["min_len"]),
            lookahead=int(best_policy["lookahead"]),
        )
        values.append(exact_prefix_len(str(row["rendered"]), target))
    ordered = sorted(values)
    return {
        "exact_prefix_p05": ordered[int(0.05 * (len(ordered) - 1))],
        "exact_prefix_p50": ordered[int(0.50 * (len(ordered) - 1))],
        "exact_prefix_p95": ordered[int(0.95 * (len(ordered) - 1))],
        "trials": SHUFFLE_TRIALS,
    }


def make_result() -> dict[str, Any]:
    payload = load_json(UNIFIED_PAYLOAD_GATE)
    v7 = load_json(EXECUTABLE_V7_GATE)
    assert_boundary("unified_innovation_payload_gate", payload)
    assert_boundary("executable_v7_unified_innovation_payload_gate", v7)
    if v7["classification"] != "PROMOTED_EXECUTABLE_V7_UNIFIED_INNOVATION_PAYLOAD_LEDGER":
        raise RuntimeError("v7 ledger is not promoted")
    target = render_events(payload["event_ledger"])
    lit_tape = literal_tape(payload["event_ledger"])
    policies = [
        "literal_only",
        "copy_literal_prefix_latest",
        "copy_suffix_continuation",
        "copy_suffix_else_literal_prefix",
    ]
    rows = []
    v7_bits = float(payload["summary"]["total_bits_after_declaration"])
    for policy in policies:
        for min_len in MIN_LENS:
            for lookahead in LOOKAHEADS:
                row = run_policy(policy, len(target), lit_tape, min_len=min_len, lookahead=lookahead)
                rows.append(score_policy(row, target, v7_bits))
    best = max(rows, key=lambda item: (int(item["exact_prefix"]), -float(item["total_bits_after_suffix_correction"])))
    best_by_policy = {}
    for policy in policies:
        policy_rows = [row for row in rows if row["policy"] == policy]
        best_by_policy[policy] = max(
            policy_rows,
            key=lambda item: (int(item["exact_prefix"]), -float(item["total_bits_after_suffix_correction"])),
        )
    controls = {"shuffled_literal_tape": shuffled_literal_tape_control(target, lit_tape, best)}
    alignment = boundary_alignment(payload["event_ledger"], payload["segments"])
    promoted = (
        best["exact_prefix"] == len(target)
        and best["delta_vs_v7_payload_replay_bits"] < 0
        and best["exact_prefix"] > controls["shuffled_literal_tape"]["exact_prefix_p95"]
    )
    return {
        "alignment": alignment,
        "case_reopened": False,
        "classification": (
            "PROMOTED_INNOVATION_REPLAY_POLICY"
            if promoted
            else "innovation_replay_policy_not_promoted"
        ),
        "compression_bound_status": "unchanged",
        "controls": controls,
        "decision": {
            "innovation_replay_policy_promoted": promoted,
            "next_blocker": (
                "copy/literal decision and copy source-length policy for the unified "
                "innovation replay remain external"
            ),
            "plaintext_claim": False,
            "row0_status": "unchanged_exogenous",
            "translation_delta": "NONE",
        },
        "inputs": {
            "executable_v7_gate": rel(EXECUTABLE_V7_GATE),
            "unified_innovation_payload_gate": rel(UNIFIED_PAYLOAD_GATE),
        },
        "plaintext_claim": False,
        "policy_rows": sorted(rows, key=lambda item: (-int(item["exact_prefix"]), float(item["total_bits_after_suffix_correction"])))[:40],
        "best_by_policy": best_by_policy,
        "row0_status": "unchanged_exogenous",
        "schema": "innovation_replay_policy_frontier_gate.v1",
        "scope": "analysis_only_innovation_replay_policy_frontier",
        "summary": {
            "best_delta_vs_v7_payload_replay_bits": float(best["delta_vs_v7_payload_replay_bits"]),
            "best_exact_prefix": int(best["exact_prefix"]),
            "best_literal_digits_consumed": int(best["literal_digits_consumed"]),
            "best_policy": best["policy"],
            "best_rendered_len": int(best["rendered_len"]),
            "literal_tape_digits": len(lit_tape),
            "promoted": promoted,
            "target_digits": len(target),
            "v7_payload_replay_bits": v7_bits,
        },
        "translation_delta": "NONE",
        "validation": {
            "errors": [],
            "target_digits": len(target),
            "literal_tape_digits": len(lit_tape),
        },
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    a = result["alignment"]
    lines = [
        "# Innovation Replay Policy Frontier Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        f"- Target innovation stream: `{s['target_digits']}` digits.",
        f"- Literal tape residual: `{s['literal_tape_digits']}` digits.",
        f"- Best policy: `{s['best_policy']}`.",
        f"- Best exact prefix: `{s['best_exact_prefix']}/{s['target_digits']}`.",
        f"- Best delta vs v7 payload replay: `{s['best_delta_vs_v7_payload_replay_bits']:.3f}` bits.",
        f"- Segment-boundary event starts: `{a['event_start_on_segment_boundary']}/{a['event_count']}`.",
        f"- Segment-boundary event ends: `{a['event_end_on_segment_boundary']}/{a['event_count']}`.",
        f"- Copy source start+end on replay event boundaries: `{a['copy_source_start_end_on_event_boundary']}/{a['copy_event_count']}`.",
        "",
        "## Decision",
        "",
        f"`{result['classification']}`.",
        "",
        "The tested online policies do not replace the v7 replay ledger.",
        "",
        "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
    ]
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    s = result["summary"]
    a = result["alignment"]
    lines = [
        "# Final Innovation Replay Policy Frontier Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        "This audit tests the blocker left by executable v7: the unified innovation "
        "payload is now a smaller executable dependency, but its replay ledger is "
        "still target-conditioned. The gate tries simple online policies using "
        "only emitted material, total stream length, and the residual literal tape.",
        "",
        f"The best policy is `{s['best_policy']}` and reaches only "
        f"`{s['best_exact_prefix']}/{s['target_digits']}` exact prefix digits. "
        f"After suffix correction it is `{s['best_delta_vs_v7_payload_replay_bits']:.3f}` "
        "bits versus the v7 payload replay ledger.",
        "",
        "Boundary diagnostics do not rescue the route: event starts hit segment "
        f"boundaries in `{a['event_start_on_segment_boundary']}/{a['event_count']}` "
        f"cases, event ends in `{a['event_end_on_segment_boundary']}/{a['event_count']}`, "
        "and copy source start+end both hit replay event boundaries in "
        f"`{a['copy_source_start_end_on_event_boundary']}/{a['copy_event_count']}` copies.",
        "",
        "## Decision",
        "",
        "`innovation_replay_policy_not_promoted`.",
        "",
        "The result keeps v7 promoted as a paid executable payload reduction, but "
        "does not turn its replay ledger into a source-free generator. The next "
        "blocker is specifically the copy/literal decision and copy source-length "
        "policy for the innovation stream.",
        "",
        "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_innovation_replay_policy_frontier_gate.py](../scripts/01_innovation_replay_policy_frontier_gate.py)",
        "- [01_innovation_replay_policy_frontier_gate.json](test_results/01_innovation_replay_policy_frontier_gate.json)",
        "- [01_innovation_replay_policy_frontier_gate.md](test_results/01_innovation_replay_policy_frontier_gate.md)",
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
