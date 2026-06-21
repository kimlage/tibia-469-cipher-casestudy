from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

GATE20 = TEST_RESULTS / "20_post_repair_residual_oracle_audit.json"
GATE39 = TEST_RESULTS / "39_observable_state_support_audit.json"
GATE40 = TEST_RESULTS / "40_latent_state_requirement_audit.json"
OUT_STEM = "41_latent_state_lookup_cost_gate"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def assert_boundary(name: str, data: dict[str, Any]) -> None:
    if data.get("translation_delta") != "NONE":
        raise RuntimeError(f"{name} changed translation boundary")
    if data.get("case_reopened", False) is not False:
        raise RuntimeError(f"{name} reopened case")
    if data.get("plaintext_claim", False) is not False:
        raise RuntimeError(f"{name} introduced plaintext")
    decision = data.get("decision", {})
    if decision.get("row0_origin_status") not in {
        None,
        "unchanged_exogenous",
        "exogenous_under_current_evidence",
    }:
        raise RuntimeError(f"{name} changed row0 origin")
    if decision.get("translation_or_plaintext_status", "NONE") != "NONE":
        raise RuntimeError(f"{name} introduced translation/plaintext")


def log2_comb(n: int, k: int) -> float:
    if k < 0 or k > n:
        raise ValueError((n, k))
    return math.log2(math.comb(n, k))


def log2_factorial(n: int) -> float:
    return math.lgamma(n + 1) / math.log(2)


def multiset_order_bits(labels: list[tuple[Any, ...]]) -> float:
    counts = Counter(labels)
    return log2_factorial(len(labels)) - sum(
        log2_factorial(count) for count in counts.values()
    )


def oracle_correction_count(gate20: dict[str, Any]) -> int:
    hist = gate20["summary"]["full_oracle_correction_count_histogram"]
    return sum(int(key) * int(value) for key, value in hist.items())


def make_result() -> dict[str, Any]:
    gate20 = load_json(GATE20)
    gate39 = load_json(GATE39)
    gate40 = load_json(GATE40)
    for name, data in [
        ("post_repair_residual_oracle_audit", gate20),
        ("observable_state_support_audit", gate39),
        ("latent_state_requirement_audit", gate40),
    ]:
        assert_boundary(name, data)
    if gate40["classification"] != "latent_state_requirement_audit_only":
        raise RuntimeError("gate41 expects gate40 latent-state requirement audit")

    rows = gate40["best_rows"]
    labels = [tuple(row["stable_label"]) for row in rows]
    label_counts = Counter(labels)
    decision_count = int(gate39["summary"]["decision_count"])
    residual_site_count = int(gate40["summary"]["best_query_count"])
    full_oracle_events = oracle_correction_count(gate20)
    distinct_label_count = len(label_counts)

    site_bits_first_drift = log2_comb(decision_count, residual_site_count)
    site_bits_full_oracle_lower_bound = log2_comb(decision_count, full_oracle_events)
    free_multiset_order_bits = multiset_order_bits(labels)
    free_dictionary_per_site_bits = (
        0.0
        if distinct_label_count <= 1
        else residual_site_count * math.log2(distinct_label_count)
    )
    first_drift_lookup_lower_bound_bits = (
        site_bits_first_drift + free_multiset_order_bits
    )
    first_drift_lookup_dictionary_bits = (
        site_bits_first_drift + free_dictionary_per_site_bits
    )
    full_parser_lookup_lower_bound_bits = (
        site_bits_full_oracle_lower_bound + free_multiset_order_bits
    )
    promotes = False
    classification = "latent_state_lookup_cost_audit_only"
    return {
        "schema": "latent_state_lookup_cost_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "post_repair_residual_oracle_audit": rel(GATE20),
            "observable_state_support_audit": rel(GATE39),
            "latent_state_requirement_audit": rel(GATE40),
        },
        "scope": {
            "analysis_only": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "target_text_required": True,
            "source_free_digit_generator_emitted": False,
            "promotes_parser_rule": promotes,
            "prices_latent_lookup_not_formula": True,
        },
        "summary": {
            "decision_universe": decision_count,
            "first_drift_residual_sites": residual_site_count,
            "full_oracle_min_correction_events": full_oracle_events,
            "distinct_first_drift_stable_labels": distinct_label_count,
            "stable_label_counts": {
                str(label): count for label, count in sorted(label_counts.items())
            },
            "site_bits_first_drift": site_bits_first_drift,
            "site_bits_full_oracle_lower_bound": site_bits_full_oracle_lower_bound,
            "free_multiset_order_bits": free_multiset_order_bits,
            "free_dictionary_per_site_bits": free_dictionary_per_site_bits,
            "first_drift_lookup_lower_bound_bits": first_drift_lookup_lower_bound_bits,
            "first_drift_lookup_dictionary_bits": first_drift_lookup_dictionary_bits,
            "full_parser_lookup_lower_bound_bits": full_parser_lookup_lower_bound_bits,
            "simple_split_deterministic_matches": gate40["summary"][
                "best_deterministic_matches"
            ],
            "promotes_latent_lookup_formula": promotes,
            "interpretation": (
                "A latent-state hypothesis must beat an explicit residual lookup. "
                "This gate prices the minimum ad hoc lookup needed after exposed "
                "state and simple splits fail; it is not a new compression bound."
            ),
        },
        "residual_rows": rows,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": classification,
            "source_length_dependency_status": "latent_lookup_priced_not_promoted",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def md_table(rows: list[list[Any]], headers: list[str]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines)


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / f"{OUT_STEM}.json"
    md_path = TEST_RESULTS / f"{OUT_STEM}.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    cost_rows = [
        ["site_bits_first_drift", f"{s['site_bits_first_drift']:.3f}"],
        [
            "site_bits_full_oracle_lower_bound",
            f"{s['site_bits_full_oracle_lower_bound']:.3f}",
        ],
        ["free_multiset_order_bits", f"{s['free_multiset_order_bits']:.3f}"],
        [
            "free_dictionary_per_site_bits",
            f"{s['free_dictionary_per_site_bits']:.3f}",
        ],
        [
            "first_drift_lookup_lower_bound_bits",
            f"{s['first_drift_lookup_lower_bound_bits']:.3f}",
        ],
        [
            "first_drift_lookup_dictionary_bits",
            f"{s['first_drift_lookup_dictionary_bits']:.3f}",
        ],
        [
            "full_parser_lookup_lower_bound_bits",
            f"{s['full_parser_lookup_lower_bound_bits']:.3f}",
        ],
    ]
    residual_rows = [
        [
            row["book"],
            row["op_index"],
            row["active_label"],
            row["stable_label"],
            row["status"],
        ]
        for row in result["residual_rows"]
    ]
    body = f"""# Latent State Lookup Cost Gate

Classification: `{result['classification']}`
Translation delta: `NONE`

## Purpose

Gate 41 prices the fallback hypothesis "there is a latent state" after exposed
state, nearest trajectories, templates, and simple splits fail. It asks how
expensive an explicit latent lookup would be before any candidate rule earns
the right to be called mechanical.

This is not a promoted parser and not a new compression bound.

## Summary

- Decision universe: `{s['decision_universe']}`.
- First-drift residual sites: `{s['first_drift_residual_sites']}`.
- Full-oracle minimum correction events: `{s['full_oracle_min_correction_events']}`.
- Distinct first-drift stable labels: `{s['distinct_first_drift_stable_labels']}`.
- Simple split deterministic matches:
  `{s['simple_split_deterministic_matches']}`.
- First-drift lookup lower bound:
  `{s['first_drift_lookup_lower_bound_bits']:.3f}` bits.
- First-drift lookup with per-site label dictionary:
  `{s['first_drift_lookup_dictionary_bits']:.3f}` bits.
- Full-parser lookup lower bound:
  `{s['full_parser_lookup_lower_bound_bits']:.3f}` bits.
- Promotes latent lookup formula: `{s['promotes_latent_lookup_formula']}`.

## Cost Ledger

{md_table(cost_rows, ["component", "bits"])}

## Residual Rows

{md_table(residual_rows, ["book", "op", "active label", "stable label", "status"])}

## Decision

Latent state is not promoted by naming it. Under current evidence, a latent
state that merely selects the residual sites and labels is an explicit lookup,
with a first-drift lower bound of `{s['first_drift_lookup_lower_bound_bits']:.3f}`
bits before any human-readable rule is charged. Because the post-repair oracle
requires at least `{s['full_oracle_min_correction_events']}` correction events,
even that is not a full parser explanation.

The next acceptable progress must provide a compact rule for this latent state,
or switch to a source-free target digit account.

- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
"""
    md_path.write_text(body, encoding="utf-8")
    print(json_path)
    print(md_path)


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
