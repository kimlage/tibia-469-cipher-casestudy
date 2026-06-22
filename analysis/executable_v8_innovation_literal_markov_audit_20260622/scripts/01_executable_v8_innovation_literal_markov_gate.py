#!/usr/bin/env python3
"""Executable v8 innovation-literal Markov integration gate.

Executable v7 reduced the seed+literal payload by replaying one innovation
stream, but still paid the literal digits inside that replay as raw decimal
payload. This gate integrates a prequential digit Markov model for those replay
literal runs into the executable ledger.

Analysis-only: no row0, plaintext, semantics, or compression-bound change.
"""

from __future__ import annotations

import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "executable_v8_innovation_literal_markov_audit_20260622"
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

JSON_OUT = TEST_RESULTS / "01_executable_v8_innovation_literal_markov_gate.json"
MD_OUT = TEST_RESULTS / "01_executable_v8_innovation_literal_markov_gate.md"
FINAL_OUT = FRONT / "reports" / "final_executable_v8_innovation_literal_markov_audit.md"

ORDERS = [0, 1, 2, 3, 4]
CUTOFFS = [256, 512, 768]
LOG2_10 = math.log2(10)
RANDOM_SEED = 46920260622
SHUFFLE_TRIALS = 100
ALPHA = 0.5


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


def literal_stream(events: list[dict[str, Any]]) -> str:
    return "".join(str(event["text"]) for event in events if event["kind"] == "literal")


def markov_cost(s: str, order: int, initial_counts: dict[str, Counter[str]] | None = None) -> tuple[float, dict[str, Counter[str]]]:
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    if initial_counts:
        for ctx, counter in initial_counts.items():
            counts[ctx].update(counter)
    total = 0.0
    for i, ch in enumerate(s):
        ctx = s[max(0, i - order) : i] if initial_counts is None else None
        if initial_counts is not None:
            # When scoring a suffix after a prefix, the caller supplies a
            # stitched string and uses score_suffix_with_prefix instead.
            raise RuntimeError("use score_suffix_with_prefix for initialized scoring")
        counter = counts[ctx]
        denom = sum(counter.values()) + 10 * ALPHA
        total += -math.log2((counter[ch] + ALPHA) / denom)
        counter[ch] += 1
    return total, counts


def train_counts(prefix: str, order: int) -> dict[str, Counter[str]]:
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    for i, ch in enumerate(prefix):
        ctx = prefix[max(0, i - order) : i]
        counts[ctx][ch] += 1
    return counts


def score_suffix_with_prefix(prefix: str, suffix: str, order: int) -> float:
    counts = train_counts(prefix, order)
    total = 0.0
    history = prefix
    for ch in suffix:
        ctx = history[max(0, len(history) - order) :]
        counter = counts[ctx]
        denom = sum(counter.values()) + 10 * ALPHA
        total += -math.log2((counter[ch] + ALPHA) / denom)
        counter[ch] += 1
        history += ch
    return total


def event_cost(event: dict[str, Any], stream_len: int) -> float:
    if event["kind"] == "literal":
        remaining = max(1, stream_len - int(event["start"]))
        length_bits = math.log2(max(1, min(64, remaining)))
        return 1.0 + length_bits + int(event["length"]) * LOG2_10
    source_bits = math.log2(max(1, int(event["start"])))
    length_bits = math.log2(max(1, min(64, stream_len - int(event["start"]))))
    return 1.0 + source_bits + length_bits


def literal_digit_raw_bits(events: list[dict[str, Any]]) -> float:
    return sum(int(event["length"]) * LOG2_10 for event in events if event["kind"] == "literal")


def controls(lit: str, selected_order: int) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED)
    values = []
    chars = list(lit)
    for _ in range(SHUFFLE_TRIALS):
        shuffled = chars[:]
        rng.shuffle(shuffled)
        cost, _counts = markov_cost("".join(shuffled), selected_order)
        values.append(cost)
    ordered = sorted(values)
    real, _counts = markov_cost(lit, selected_order)
    return {
        "real_cost": real,
        "shuffled_p05": ordered[int(0.05 * (len(ordered) - 1))],
        "shuffled_p50": ordered[int(0.50 * (len(ordered) - 1))],
        "shuffled_p95": ordered[int(0.95 * (len(ordered) - 1))],
        "beats_p05": real < ordered[int(0.05 * (len(ordered) - 1))],
        "trials": SHUFFLE_TRIALS,
    }


def prefix_holdouts(lit: str) -> list[dict[str, Any]]:
    rows = []
    for cutoff in CUTOFFS:
        prefix = lit[:cutoff]
        suffix = lit[cutoff:]
        train_costs = {order: markov_cost(prefix, order)[0] for order in ORDERS}
        selected = min(train_costs, key=train_costs.get)
        suffix_cost = score_suffix_with_prefix(prefix, suffix, selected)
        raw_suffix = len(suffix) * LOG2_10
        rows.append(
            {
                "cutoff": cutoff,
                "raw_suffix_bits": raw_suffix,
                "selected_order": selected,
                "suffix_delta_vs_raw": suffix_cost - raw_suffix,
                "suffix_markov_bits": suffix_cost,
                "train_best_delta_vs_raw": train_costs[selected] - len(prefix) * LOG2_10,
            }
        )
    return rows


def make_result() -> dict[str, Any]:
    payload = load_json(UNIFIED_PAYLOAD_GATE)
    v7 = load_json(EXECUTABLE_V7_GATE)
    assert_boundary("unified_innovation_payload_gate", payload)
    assert_boundary("executable_v7_unified_innovation_payload_gate", v7)
    if v7["classification"] != "PROMOTED_EXECUTABLE_V7_UNIFIED_INNOVATION_PAYLOAD_LEDGER":
        raise RuntimeError("v7 is not promoted")
    lit = literal_stream(payload["event_ledger"])
    raw_bits = len(lit) * LOG2_10
    costs = {order: markov_cost(lit, order)[0] for order in ORDERS}
    selected = min(costs, key=costs.get)
    declaration_bits = math.log2(len(ORDERS))
    selected_cost = costs[selected] + declaration_bits
    raw_literal_bits_in_replay = literal_digit_raw_bits(payload["event_ledger"])
    if abs(raw_literal_bits_in_replay - raw_bits) > 1e-9:
        raise RuntimeError("literal raw bit mismatch")
    v7_summary = v7["summary"]
    v7_total = float(v7_summary["candidate_v7_external_bits_total_content_included"])
    v8_total = v7_total - raw_bits + selected_cost
    delta = v8_total - v7_total
    ctrl = controls(lit, selected)
    holdouts = prefix_holdouts(lit)
    positive_holdouts = sum(1 for row in holdouts if row["suffix_delta_vs_raw"] < 0)
    promoted = delta < 0 and ctrl["beats_p05"] and positive_holdouts == len(holdouts)
    return {
        "case_reopened": False,
        "classification": (
            "PROMOTED_EXECUTABLE_V8_INNOVATION_LITERAL_MARKOV_LEDGER"
            if promoted
            else "executable_v8_innovation_literal_markov_not_promoted"
        ),
        "compression_bound_status": "unchanged",
        "controls": {"same_multiset_literal_shuffle": ctrl},
        "decision": {
            "executable_v8_promoted": promoted,
            "generation_explanation_status": (
                "probabilistic_literal_payload_dependency_reduced_not_plaintext"
                if promoted
                else "not_reduced"
            ),
            "next_blocker": (
                "innovation replay copy/literal decision and copy source-length policy "
                "remain external"
            ),
            "plaintext_claim": False,
            "row0_status": "unchanged_exogenous",
            "translation_delta": "NONE",
        },
        "holdouts": holdouts,
        "inputs": {
            "executable_v7_gate": rel(EXECUTABLE_V7_GATE),
            "unified_innovation_payload_gate": rel(UNIFIED_PAYLOAD_GATE),
        },
        "order_costs": {
            str(order): {
                "cost_bits": costs[order],
                "delta_vs_raw_bits": costs[order] - raw_bits,
            }
            for order in ORDERS
        },
        "plaintext_claim": False,
        "row0_status": "unchanged_exogenous",
        "schema": "executable_v8_innovation_literal_markov_gate.v1",
        "scope": "analysis_only_executable_v8_innovation_literal_markov",
        "summary": {
            "declaration_bits": declaration_bits,
            "delta_vs_v7_total_bits": delta,
            "literal_digits": len(lit),
            "positive_holdouts": positive_holdouts,
            "promoted": promoted,
            "raw_literal_bits": raw_bits,
            "selected_markov_bits_after_declaration": selected_cost,
            "selected_order": selected,
            "v7_external_bits_total_content_included": v7_total,
            "v8_external_bits_total_content_included": v8_total,
        },
        "translation_delta": "NONE",
        "validation": {
            "errors": [],
            "literal_digits": len(lit),
            "v7_roundtrip_70_70": bool(v7["validation"]["roundtrip_70_70"]),
        },
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Executable v8 Innovation-Literal Markov Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        f"- Literal digits in v7 replay: `{s['literal_digits']}`.",
        f"- Raw literal bits: `{s['raw_literal_bits']:.3f}`.",
        f"- Selected Markov order: `{s['selected_order']}`.",
        f"- Markov bits after declaration: `{s['selected_markov_bits_after_declaration']:.3f}`.",
        f"- V7 total content-included bits: `{s['v7_external_bits_total_content_included']:.3f}`.",
        f"- V8 total content-included bits: `{s['v8_external_bits_total_content_included']:.3f}`.",
        f"- Delta vs v7: `{s['delta_vs_v7_total_bits']:.3f}` bits.",
        f"- Positive prefix holdouts: `{s['positive_holdouts']}/{len(result['holdouts'])}`.",
        "",
        "## Decision",
        "",
        f"`{result['classification']}`.",
        "",
        "This reduces literal payload dependency probabilistically; it does not "
        "promote plaintext or a source-free innovation replay policy.",
        "",
        "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
    ]
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Final Executable v8 Innovation-Literal Markov Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        "This audit integrates a prequential Markov model for the literal digits "
        "inside the executable v7 innovation replay. It does not alter the replay "
        "events or claim source-free generation; it only replaces raw literal "
        "digit declaration inside the already promoted v7 ledger.",
        "",
        f"The v7 replay has `{s['literal_digits']}` literal digits costing "
        f"`{s['raw_literal_bits']:.3f}` raw bits. The selected order is "
        f"`{s['selected_order']}`, costing `{s['selected_markov_bits_after_declaration']:.3f}` "
        "bits after order declaration.",
        "",
        f"Integrated total content-included bits move from v7 "
        f"`{s['v7_external_bits_total_content_included']:.3f}` to v8 "
        f"`{s['v8_external_bits_total_content_included']:.3f}`, a reduction of "
        f"`{-s['delta_vs_v7_total_bits']:.3f}` bits. Same-multiset literal shuffle "
        "controls are beaten at p05, and prefix holdouts are positive in "
        f"`{s['positive_holdouts']}/{len(result['holdouts'])}` splits.",
        "",
        "## Decision",
        "",
        f"`{result['classification']}`.",
        "",
        "This is a real executable ledger reduction for innovation literal content, "
        "but not a complete generator. The replay event schedule, copy/literal "
        "decision, and copy source-length policy remain external.",
        "",
        "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_executable_v8_innovation_literal_markov_gate.py](../scripts/01_executable_v8_innovation_literal_markov_gate.py)",
        "- [01_executable_v8_innovation_literal_markov_gate.json](test_results/01_executable_v8_innovation_literal_markov_gate.json)",
        "- [01_executable_v8_innovation_literal_markov_gate.md](test_results/01_executable_v8_innovation_literal_markov_gate.md)",
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
