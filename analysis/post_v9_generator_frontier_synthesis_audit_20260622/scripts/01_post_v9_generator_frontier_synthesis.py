#!/usr/bin/env python3
"""Post-v9 generator frontier synthesis.

This audit deliberately steps back after the v7-v9 executable reductions. It
computes the remaining innovation-replay dependencies and tests whether the
next tempting local reduction, copy-length defaults, should be promoted. The
goal is to avoid turning small field codecs into "generator progress".

Analysis-only: no row0, plaintext, semantics, or compression-bound change.
"""

from __future__ import annotations

import json
import math
import random
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "post_v9_generator_frontier_synthesis_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"

UNIFIED_PAYLOAD_GATE = (
    ROOT
    / "analysis"
    / "unified_innovation_payload_audit_20260622"
    / "reports"
    / "test_results"
    / "01_unified_innovation_payload_gate.json"
)
EXECUTABLE_V9_GATE = (
    ROOT
    / "analysis"
    / "executable_v9_innovation_copy_continuation_audit_20260622"
    / "reports"
    / "test_results"
    / "01_executable_v9_innovation_copy_continuation_gate.json"
)
INNOVATION_POLICY_GATE = (
    ROOT
    / "analysis"
    / "innovation_replay_policy_frontier_audit_20260622"
    / "reports"
    / "test_results"
    / "01_innovation_replay_policy_frontier_gate.json"
)

JSON_OUT = TEST_RESULTS / "01_post_v9_generator_frontier_synthesis.json"
MD_OUT = TEST_RESULTS / "01_post_v9_generator_frontier_synthesis.md"
FINAL_OUT = FRONT / "reports" / "final_post_v9_generator_frontier_synthesis_audit.md"

RANDOM_SEED = 46920260622
CONTROL_TRIALS = 500
PROMOTION_MIN_NET_BITS = 50.0


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


def replay_residuals(events: list[dict[str, Any]], stream_len: int) -> dict[str, Any]:
    copy_events = [event for event in events if event["kind"] == "copy"]
    literal_events = [event for event in events if event["kind"] == "literal"]
    copy_length_bits = sum(math.log2(max(1, min(64, stream_len - int(event["start"])))) for event in copy_events)
    copy_source_bits = sum(math.log2(max(1, int(event["start"]))) for event in copy_events)
    literal_run_bits = sum(1.0 + math.log2(max(1, min(64, stream_len - int(event["start"])))) for event in literal_events)
    copy_type_bits = float(len(copy_events))
    copy_length_counts = Counter(int(event["length"]) for event in copy_events)
    return {
        "copy_length_bits_before_any_default": copy_length_bits,
        "copy_length_counts": dict(sorted(copy_length_counts.items())),
        "copy_ops": len(copy_events),
        "copy_source_bits_before_v9_continuation": copy_source_bits,
        "copy_type_bits": copy_type_bits,
        "literal_run_bits": literal_run_bits,
        "literal_runs": len(literal_events),
        "replay_events": len(events),
    }


def copy_length_default_candidate(events: list[dict[str, Any]], stream_len: int) -> dict[str, Any]:
    copy_events = [event for event in events if event["kind"] == "copy"]
    labels = []
    source_values = []
    for event in copy_events:
        start = int(event["start"])
        length = int(event["length"])
        length_bits = math.log2(max(1, min(64, stream_len - start)))
        if length == min(64, stream_len - start):
            label = "cap"
        elif length == 9:
            label = "len9"
        else:
            label = "paid"
        labels.append(label)
        source_values.append(length_bits)
    counts = Counter(labels)
    gross_saving = sum(bits for label, bits in zip(labels, source_values) if label != "paid")
    # Pay exact label positions with a multinomial index plus a small model
    # declaration: one bit for enabling this family and six bits for declaring
    # the literal default length 9. The cap rule is implicit in MAX_COPY_LEN=64.
    multinomial = math.lgamma(len(labels) + 1) / math.log(2)
    for count in counts.values():
        multinomial -= math.lgamma(count + 1) / math.log(2)
    declaration = 7.0
    net_saving = gross_saving - multinomial - declaration
    rng = random.Random(RANDOM_SEED)
    values = []
    positive_count = counts["cap"] + counts["len9"]
    for _ in range(CONTROL_TRIALS):
        picked = set(rng.sample(range(len(labels)), positive_count))
        values.append(sum(source_values[idx] for idx in picked) - multinomial - declaration)
    ordered = sorted(values)
    return {
        "classification": (
            "MICRO_REDUCTION_NOT_PROMOTED"
            if 0 < net_saving < PROMOTION_MIN_NET_BITS
            else "REJECTED_COPY_LENGTH_DEFAULT"
            if net_saving <= 0
            else "PROMOTABLE_CANDIDATE_REQUIRES_INTEGRATION"
        ),
        "control_p05": ordered[int(0.05 * (len(ordered) - 1))],
        "control_p50": ordered[int(0.50 * (len(ordered) - 1))],
        "control_p95": ordered[int(0.95 * (len(ordered) - 1))],
        "counts": dict(counts),
        "declaration_bits": declaration,
        "gross_saving_bits": gross_saving,
        "multinomial_pattern_bits": multinomial,
        "net_saving_bits": net_saving,
        "promotion_min_net_bits": PROMOTION_MIN_NET_BITS,
        "reason": (
            "positive but below promotion threshold and control-close; keep out of executable line"
            if 0 < net_saving < PROMOTION_MIN_NET_BITS
            else "not positive"
            if net_saving <= 0
            else "large enough to consider separately"
        ),
        "trials": CONTROL_TRIALS,
    }


def make_result() -> dict[str, Any]:
    payload = load_json(UNIFIED_PAYLOAD_GATE)
    v9 = load_json(EXECUTABLE_V9_GATE)
    policy = load_json(INNOVATION_POLICY_GATE)
    for name, data in [
        ("unified_innovation_payload_gate", payload),
        ("executable_v9_innovation_copy_continuation_gate", v9),
        ("innovation_replay_policy_frontier_gate", policy),
    ]:
        assert_boundary(name, data)
    if v9["classification"] != "PROMOTED_EXECUTABLE_V9_INNOVATION_COPY_CONTINUATION_LEDGER":
        raise RuntimeError("v9 ledger is not promoted")
    stream_len = int(payload["summary"]["stream_digits"])
    residuals = replay_residuals(payload["event_ledger"], stream_len)
    length_candidate = copy_length_default_candidate(payload["event_ledger"], stream_len)
    promoted = False
    return {
        "case_reopened": False,
        "classification": "post_v9_frontier_synthesis_no_new_program_promoted",
        "compression_bound_status": "unchanged",
        "decision": {
            "next_blocker": (
                "innovation replay schedule and copy/literal/source-length policy remain "
                "the main non-source-free dependency"
            ),
            "plaintext_claim": False,
            "promoted_new_program": promoted,
            "row0_status": "unchanged_exogenous",
            "translation_delta": "NONE",
        },
        "inputs": {
            "executable_v9_gate": rel(EXECUTABLE_V9_GATE),
            "innovation_replay_policy_frontier_gate": rel(INNOVATION_POLICY_GATE),
            "unified_innovation_payload_gate": rel(UNIFIED_PAYLOAD_GATE),
        },
        "plaintext_claim": False,
        "residual_ledger": {
            "innovation_policy_best_exact_prefix": policy["summary"]["best_exact_prefix"],
            "innovation_policy_classification": policy["classification"],
            "v9_external_bits_total_content_included": v9["summary"]["v9_external_bits_total_content_included"],
            **residuals,
        },
        "row0_status": "unchanged_exogenous",
        "schema": "post_v9_generator_frontier_synthesis.v1",
        "scope": "analysis_only_post_v9_generator_frontier",
        "tested_candidates": {
            "copy_length_cap_or_len9_default": length_candidate,
        },
        "summary": {
            "copy_length_default_net_bits": length_candidate["net_saving_bits"],
            "copy_length_default_status": length_candidate["classification"],
            "new_program_promoted": promoted,
            "next_blocker": "innovation_replay_policy",
            "v9_external_bits_total_content_included": v9["summary"]["v9_external_bits_total_content_included"],
        },
        "translation_delta": "NONE",
        "validation": {
            "errors": [],
            "v9_roundtrip_70_70": bool(v9["validation"]["roundtrip_70_70"]),
        },
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    residual = result["residual_ledger"]
    candidate = result["tested_candidates"]["copy_length_cap_or_len9_default"]
    lines = [
        "# Post-v9 Generator Frontier Synthesis",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Residual Ledger",
        "",
        f"- V9 total content-included bits: `{s['v9_external_bits_total_content_included']:.3f}`.",
        f"- Replay events: `{residual['replay_events']}`.",
        f"- Copy ops: `{residual['copy_ops']}`; literal runs: `{residual['literal_runs']}`.",
        f"- Remaining copy length bits before candidate: `{residual['copy_length_bits_before_any_default']:.3f}`.",
        f"- Literal run type/length bits: `{residual['literal_run_bits']:.3f}`.",
        "",
        "## Candidate Tested",
        "",
        f"- Copy length default status: `{candidate['classification']}`.",
        f"- Net saving: `{candidate['net_saving_bits']:.3f}` bits.",
        f"- Control p50: `{candidate['control_p50']:.3f}` bits.",
        f"- Reason: {candidate['reason']}.",
        "",
        "## Decision",
        "",
        "`post_v9_frontier_synthesis_no_new_program_promoted`.",
        "",
        "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
    ]
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    s = result["summary"]
    residual = result["residual_ledger"]
    candidate = result["tested_candidates"]["copy_length_cap_or_len9_default"]
    lines = [
        "# Final Post-v9 Generator Frontier Synthesis Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        "This audit steps back after v9 and asks whether the next tempting local "
        "codec should actually become v10. It computes the remaining innovation "
        "replay dependencies and tests the strongest obvious copy-length default "
        "candidate.",
        "",
        f"The executable frontier remains v9 at "
        f"`{s['v9_external_bits_total_content_included']:.3f}` content-included bits. "
        f"The replay still has `{residual['replay_events']}` events: "
        f"`{residual['copy_ops']}` copies and `{residual['literal_runs']}` literal runs.",
        "",
        "The copy-length default candidate derives `cap` and `len=9` cases. It is "
        f"positive but too small/control-close: net saving `{candidate['net_saving_bits']:.3f}` "
        f"bits, below the `{candidate['promotion_min_net_bits']:.1f}` bit promotion "
        "threshold, with random-label controls nearby. It is therefore recorded as "
        "`MICRO_REDUCTION_NOT_PROMOTED`, not integrated as v10.",
        "",
        "## Decision",
        "",
        "`post_v9_frontier_synthesis_no_new_program_promoted`.",
        "",
        "The next real blocker remains the innovation replay policy: event schedule, "
        "copy/literal decision, and non-continuation copy source-length choices. "
        "Further tiny field defaults should not be counted as generator progress "
        "unless they materially reduce the executable ledger and survive stronger controls.",
        "",
        "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_post_v9_generator_frontier_synthesis.py](../scripts/01_post_v9_generator_frontier_synthesis.py)",
        "- [01_post_v9_generator_frontier_synthesis.json](test_results/01_post_v9_generator_frontier_synthesis.json)",
        "- [01_post_v9_generator_frontier_synthesis.md](test_results/01_post_v9_generator_frontier_synthesis.md)",
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
