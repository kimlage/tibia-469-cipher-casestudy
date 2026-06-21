from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

GATE41 = TEST_RESULTS / "41_latent_state_lookup_cost_gate.json"
GATE46 = TEST_RESULTS / "46_branch_rank_position_audit.json"

OUT_STEM = "47_branch_rank_exception_cost_gate"


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
        return math.inf
    return math.log2(math.comb(n, k))


def log2_factorial(n: int) -> float:
    return math.lgamma(n + 1) / math.log(2)


def multiset_order_bits(labels: list[tuple[Any, ...]]) -> float:
    counts = Counter(labels)
    return log2_factorial(len(labels)) - sum(
        log2_factorial(count) for count in counts.values()
    )


def label(value: Any) -> tuple[Any, ...]:
    if value is None:
        return ("none",)
    if isinstance(value, dict):
        return (value.get("type"), int(value.get("length", 0)))
    return tuple(value)


def make_result() -> dict[str, Any]:
    gate41 = load_json(GATE41)
    gate46 = load_json(GATE46)
    assert_boundary("latent_state_lookup_cost_gate", gate41)
    assert_boundary("branch_rank_position_audit", gate46)
    if gate46["classification"] != "branch_rank_rule_rejected":
        raise RuntimeError("gate47 expects gate46 rank rejection")

    summary41 = gate41["summary"]
    summary46 = gate46["summary"]
    best_ranker = summary46["best_top1_ranker"]
    ranker_count = int(summary46["ranker_count"])
    decision_universe = int(summary41["decision_universe"])
    total_decisions = int(summary46["residual_count"]) + int(
        summary46["clean_control_count"]
    )
    residual_total = int(summary46["residual_count"])
    residual_hits = int(summary46["best_top1_residual_hits"])
    residual_misses = residual_total - residual_hits
    clean_false_changes = int(summary46["best_top1_clean_false_changes"])
    global_correction_count = residual_misses + clean_false_changes

    best_rows = gate46["best_top1_rows"]
    residual_rows = [
        row for row in best_rows if row["kind"] == "residual_first_drift"
    ]
    clean_rows = [row for row in best_rows if row["kind"] == "clean_control"]
    missed_residual_labels = [
        label(row["stable_op"])
        for row in residual_rows
        if not row["top_is_stable"]
    ]
    clean_rollback_labels = [
        label(row["stable_op"]) for row in clean_rows if not row["top_is_stable"]
    ]

    ranker_id_bits = math.log2(ranker_count)
    baseline_lookup_bits = float(summary41["first_drift_lookup_lower_bound_bits"])
    baseline_site_bits = float(summary41["site_bits_first_drift"])

    # Lower bound: apply the ranker everywhere, then identify all decisions
    # where it must be rolled back. Label costs are included separately and can
    # only make the rule more expensive.
    global_site_bits = log2_comb(total_decisions, global_correction_count)
    global_label_bits = multiset_order_bits(
        missed_residual_labels + clean_rollback_labels
    )
    global_lower_bound_bits = ranker_id_bits + global_site_bits
    global_with_labels_bits = global_lower_bound_bits + global_label_bits

    # Lower bound: first declare the residual sites, apply the ranker only
    # there, then pay for residual misses. This is not source-free; it is a
    # best-case accounting of the weak rank signal after site lookup.
    residual_gated_site_bits = baseline_site_bits
    residual_miss_site_bits = log2_comb(residual_total, residual_misses)
    residual_miss_label_bits = multiset_order_bits(missed_residual_labels)
    residual_gated_lower_bound_bits = (
        residual_gated_site_bits + ranker_id_bits + residual_miss_site_bits
    )
    residual_gated_with_labels_bits = (
        residual_gated_lower_bound_bits + residual_miss_label_bits
    )

    # The residual-gated variant is explicitly not source-free: it gets the
    # residual sites from the lookup it is supposed to replace. It may be a
    # diagnostic lower bound, but only the global variant can promote.
    promotes = global_with_labels_bits < baseline_lookup_bits
    classification = (
        "branch_rank_exception_cost_promoted"
        if promotes
        else "branch_rank_exception_cost_rejected"
    )
    return {
        "schema": "branch_rank_exception_cost_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "latent_state_lookup_cost_gate": rel(GATE41),
            "branch_rank_position_audit": rel(GATE46),
        },
        "scope": {
            "analysis_only": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "target_text_required": True,
            "stable_projection_used_as_label_only": True,
            "source_free_digit_generator_emitted": False,
            "promotes_parser_rule": promotes,
            "prices_rank_signal_against_lookup": True,
        },
        "summary": {
            "interpretation": (
                "This gate asks whether the weak gate-46 branch-rank signal "
                "reduces ad hoc description cost after paying for the ranker, "
                "clean rollbacks, and residual misses. It compares against the "
                "gate-41 first-drift lookup lower bound."
            ),
            "best_ranker": best_ranker,
            "ranker_count": ranker_count,
            "ranker_id_bits": ranker_id_bits,
            "baseline_lookup_bits": baseline_lookup_bits,
            "residual_hits": residual_hits,
            "residual_misses": residual_misses,
            "clean_false_changes": clean_false_changes,
            "global_correction_count": global_correction_count,
            "global_ranker_lower_bound_bits": global_lower_bound_bits,
            "global_ranker_with_labels_bits": global_with_labels_bits,
            "residual_gated_lower_bound_bits": residual_gated_lower_bound_bits,
            "residual_gated_with_labels_bits": residual_gated_with_labels_bits,
            "residual_gated_net_vs_lookup_bits": (
                residual_gated_with_labels_bits - baseline_lookup_bits
            ),
            "best_net_vs_lookup_bits": min(
                global_with_labels_bits, residual_gated_with_labels_bits
            )
            - baseline_lookup_bits,
            "best_promotable_net_vs_lookup_bits": (
                global_with_labels_bits - baseline_lookup_bits
            ),
            "promotes_branch_rank_exception_cost": promotes,
        },
        "cost_rows": [
            {
                "model": "gate41_first_drift_lookup",
                "bits": baseline_lookup_bits,
                "net_vs_lookup": 0.0,
                "boundary": "baseline explicit residual lookup",
            },
            {
                "model": "global_ranker_lower_bound_without_labels",
                "bits": global_lower_bound_bits,
                "net_vs_lookup": global_lower_bound_bits - baseline_lookup_bits,
                "boundary": "optimistic lower bound; no correction labels charged",
            },
            {
                "model": "global_ranker_with_labels",
                "bits": global_with_labels_bits,
                "net_vs_lookup": global_with_labels_bits - baseline_lookup_bits,
                "boundary": "ranker everywhere plus clean/residual corrections",
            },
            {
                "model": "residual_gated_ranker_lower_bound_without_labels",
                "bits": residual_gated_lower_bound_bits,
                "net_vs_lookup": residual_gated_lower_bound_bits - baseline_lookup_bits,
                "boundary": "not source-free; residual site lookup granted",
            },
            {
                "model": "residual_gated_ranker_with_labels",
                "bits": residual_gated_with_labels_bits,
                "net_vs_lookup": residual_gated_with_labels_bits - baseline_lookup_bits,
                "boundary": "not source-free; residual site lookup plus miss labels",
            },
        ],
        "residual_miss_labels": missed_residual_labels,
        "clean_rollback_count_by_label": {
            repr(key): value for key, value in sorted(Counter(clean_rollback_labels).items())
        },
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": classification,
            "source_length_dependency_status": "rank_signal_priced_against_lookup",
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
        [
            row["model"],
            f"{row['bits']:.3f}",
            f"{row['net_vs_lookup']:.3f}",
            row["boundary"],
        ]
        for row in result["cost_rows"]
    ]
    body = f"""# Branch Rank Exception Cost Gate

Classification: `{result['classification']}`
Translation delta: `NONE`

## Purpose

Gate 47 prices the weak branch-rank signal from gate 46. It asks whether
`{s['best_ranker']}` still reduces ad hoc description after paying for the
ranker ID, residual misses, and the clean controls it breaks.

## Summary

- Baseline residual lookup: `{s['baseline_lookup_bits']:.3f}` bits.
- Ranker ID cost: `{s['ranker_id_bits']:.3f}` bits across `{s['ranker_count']}` rankers.
- Residual hits/misses: `{s['residual_hits']}` / `{s['residual_misses']}`.
- Clean false changes: `{s['clean_false_changes']}`.
- Global correction count: `{s['global_correction_count']}`.
- Global ranker lower bound: `{s['global_ranker_lower_bound_bits']:.3f}` bits before labels.
- Global ranker with labels: `{s['global_ranker_with_labels_bits']:.3f}` bits.
- Residual-gated lower bound: `{s['residual_gated_lower_bound_bits']:.3f}` bits before miss labels.
- Residual-gated with labels: `{s['residual_gated_with_labels_bits']:.3f}` bits.
- Residual-gated net vs lookup: `{s['residual_gated_net_vs_lookup_bits']:.3f}` bits, audit-only because residual sites are granted.
- Best promotable net vs lookup: `{s['best_promotable_net_vs_lookup_bits']:.3f}` bits.
- Promotes branch-rank exception cost: `{s['promotes_branch_rank_exception_cost']}`.

## Cost Rows

{md_table(cost_rows, ['model', 'bits', 'net vs lookup', 'boundary'])}

## Decision

The weak rank signal is not promoted. Applying the ranker globally creates too
many clean rollbacks. Applying it only at residual sites is cheaper than the
plain label lookup, but only after granting the residual site lookup the
hypothesis was meant to reduce; that row is audit-only and not a parser rule.

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
