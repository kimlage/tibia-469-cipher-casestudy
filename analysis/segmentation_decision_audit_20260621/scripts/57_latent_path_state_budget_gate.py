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
GATE48 = TEST_RESULTS / "48_residual_site_detector_gate.json"
GATE56 = TEST_RESULTS / "56_sequential_signature_support_gate.json"

OUT_STEM = "57_latent_path_state_budget_gate"


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


def stable_label(row: dict[str, Any]) -> tuple[Any, ...]:
    label = row["stable_label"]
    if isinstance(label, list):
        return tuple(label)
    if isinstance(label, tuple):
        return label
    return (label,)


def make_cost_rows(
    labels: list[tuple[Any, ...]],
    decision_universe: int,
    baseline_lookup_bits: float,
    site_bits: float,
    label_order_bits: float,
    gate48_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    residual_count = len(labels)
    distinct_label_count = len(set(labels))
    best_zero_fp_tp = int(gate48_summary["best_zero_fp_tp"])
    misses_after_zero_fp = residual_count - best_zero_fp_tp
    zero_fp_missed_labels = labels[best_zero_fp_tp:]
    zero_fp_miss_bits = log2_comb(decision_universe, misses_after_zero_fp) + (
        multiset_order_bits(zero_fp_missed_labels)
        if zero_fp_missed_labels
        else 0.0
    )
    rows = [
        {
            "model": "explicit_residual_shape_lookup",
            "valid_without_oracle": True,
            "site_oracle_granted": False,
            "site_bits": site_bits,
            "label_bits": label_order_bits,
            "dictionary_bits_lower_bound": 0.0,
            "total_bits": site_bits + label_order_bits,
            "net_vs_lookup_bits": site_bits + label_order_bits - baseline_lookup_bits,
            "interpretation": "The current lower-bound lookup: choose residual sites and the multiset order of stable shape labels.",
        },
        {
            "model": "latent_state_ids_with_label_dictionary",
            "valid_without_oracle": True,
            "site_oracle_granted": False,
            "site_bits": site_bits,
            "label_bits": label_order_bits,
            "dictionary_bits_lower_bound": 0.0,
            "total_bits": site_bits + label_order_bits,
            "net_vs_lookup_bits": site_bits + label_order_bits - baseline_lookup_bits,
            "interpretation": "A latent state alphabet reused only by stable shape label is no cheaper than the explicit lookup before charging state semantics.",
        },
        {
            "model": "zero_fp_site_detector_plus_remaining_lookup_lower_bound",
            "valid_without_oracle": False,
            "site_oracle_granted": False,
            "site_bits": 0.0,
            "label_bits": zero_fp_miss_bits,
            "dictionary_bits_lower_bound": 0.0,
            "total_bits": zero_fp_miss_bits,
            "net_vs_lookup_bits": zero_fp_miss_bits - baseline_lookup_bits,
            "interpretation": "Audit-only lower bound: uses gate48's best zero-FP detector but ignores detector/rule cost and ordering of which residuals it catches.",
        },
        {
            "model": "residual_site_oracle_labels_only",
            "valid_without_oracle": False,
            "site_oracle_granted": True,
            "site_bits": 0.0,
            "label_bits": label_order_bits,
            "dictionary_bits_lower_bound": 0.0,
            "total_bits": label_order_bits,
            "net_vs_lookup_bits": label_order_bits - baseline_lookup_bits,
            "interpretation": "Invalid as a parser: it becomes cheap only by granting the residual sites for free.",
        },
        {
            "model": "one_state_per_distinct_label_with_site_oracle",
            "valid_without_oracle": False,
            "site_oracle_granted": True,
            "site_bits": 0.0,
            "label_bits": label_order_bits,
            "dictionary_bits_lower_bound": math.log2(max(1, distinct_label_count)),
            "total_bits": label_order_bits + math.log2(max(1, distinct_label_count)),
            "net_vs_lookup_bits": label_order_bits
            + math.log2(max(1, distinct_label_count))
            - baseline_lookup_bits,
            "interpretation": "Invalid as a parser: it names reusable label states but still receives all residual sites for free.",
        },
    ]
    return rows


def make_result() -> dict[str, Any]:
    gate41 = load_json(GATE41)
    gate48 = load_json(GATE48)
    gate56 = load_json(GATE56)
    for name, data in [
        ("latent_state_lookup_cost_gate", gate41),
        ("residual_site_detector_gate", gate48),
        ("sequential_signature_support_gate", gate56),
    ]:
        assert_boundary(name, data)
    if gate56["classification"] != "sequential_signature_support_rejected":
        raise RuntimeError("gate57 expects gate56 rejection")

    rows = gate56["best_rows"]
    labels = [stable_label(row) for row in rows]
    label_counts = Counter(labels)
    gate41_summary = gate41["summary"]
    gate48_summary = gate48["summary"]
    gate56_summary = gate56["summary"]
    decision_universe = int(gate41_summary["decision_universe"])
    residual_count = len(labels)
    site_bits = log2_comb(decision_universe, residual_count)
    label_order_bits = multiset_order_bits(labels)
    baseline_lookup_bits = float(gate41_summary["first_drift_lookup_lower_bound_bits"])
    cost_rows = make_cost_rows(
        labels,
        decision_universe,
        baseline_lookup_bits,
        site_bits,
        label_order_bits,
        gate48_summary,
    )
    valid_rows = [row for row in cost_rows if row["valid_without_oracle"]]
    best_valid = min(valid_rows, key=lambda row: row["total_bits"])
    invalid_rows = [row for row in cost_rows if not row["valid_without_oracle"]]
    best_invalid = min(invalid_rows, key=lambda row: row["total_bits"])
    unsupported = gate56_summary["best_status_counts"].get("out_of_support", 0)
    distinct_labels = len(label_counts)
    promotes = (
        best_valid["total_bits"] < baseline_lookup_bits
        and unsupported < residual_count
    )
    if promotes:
        classification = "latent_path_state_budget_promoted"
    else:
        classification = "latent_path_state_budget_rejected_lookup_repackaging"
    return {
        "schema": "latent_path_state_budget_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "latent_state_lookup_cost_gate": rel(GATE41),
            "residual_site_detector_gate": rel(GATE48),
            "sequential_signature_support_gate": rel(GATE56),
        },
        "scope": {
            "analysis_only": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "target_text_required": True,
            "source_free_digit_generator_emitted": False,
            "promotes_parser_rule": promotes,
            "prices_latent_state_after_support_failures": True,
        },
        "summary": {
            "decision_universe": decision_universe,
            "residual_count": residual_count,
            "unsupported_residuals_under_gate56_best": unsupported,
            "distinct_stable_shape_labels": distinct_labels,
            "stable_shape_label_counts": {
                repr(label): count for label, count in sorted(label_counts.items())
            },
            "site_bits": site_bits,
            "label_order_bits": label_order_bits,
            "baseline_lookup_bits": baseline_lookup_bits,
            "best_valid_model": best_valid["model"],
            "best_valid_bits": best_valid["total_bits"],
            "best_valid_net_vs_lookup_bits": best_valid["net_vs_lookup_bits"],
            "best_invalid_model": best_invalid["model"],
            "best_invalid_bits": best_invalid["total_bits"],
            "best_invalid_net_vs_lookup_bits": best_invalid["net_vs_lookup_bits"],
            "gate48_best_zero_fp_tp": gate48_summary["best_zero_fp_tp"],
            "gate48_prequential_cover_all_residual_cells": gate48_summary[
                "prequential_cover_all_residual_cells"
            ],
            "gate56_best_supported_count": gate56_summary["best_supported_count"],
            "promotes_latent_path_state_budget": promotes,
            "interpretation": (
                "After observable and sequential signatures fail, a latent state "
                "must still pay for residual sites and labels. Any cheap row here "
                "that grants residual sites is an oracle, not a generator."
            ),
        },
        "cost_rows": cost_rows,
        "residual_rows": rows,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": classification,
            "source_length_dependency_status": "latent_state_budget_priced",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def md_table(rows: list[list[Any]], headers: list[str]) -> str:
    out = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        out.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(out)


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / f"{OUT_STEM}.json"
    md_path = TEST_RESULTS / f"{OUT_STEM}.md"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    s = result["summary"]
    cost_rows = [
        [
            row["model"],
            row["valid_without_oracle"],
            row["site_oracle_granted"],
            f"{row['site_bits']:.3f}",
            f"{row['label_bits']:.3f}",
            f"{row['dictionary_bits_lower_bound']:.3f}",
            f"{row['total_bits']:.3f}",
            f"{row['net_vs_lookup_bits']:.3f}",
        ]
        for row in result["cost_rows"]
    ]
    residual_rows = [
        [
            row["book"],
            row["stable_index"],
            row["drift_class"],
            row["stable_label"],
            row["status"],
        ]
        for row in result["residual_rows"]
    ]
    body = f"""# Latent Path-State Budget Gate

Classification: `{result['classification']}`
Translation delta: `NONE`

## Purpose

Gate 57 prices what remains after observable candidate signatures and short
sequential signatures fail. A latent path-state explanation must do more than
rename the residual lookup: it has to cover residual sites and labels without
receiving either for free.

This is not a compression sweep and not a promoted parser.

## Summary

- Decision universe: `{s['decision_universe']}`.
- Residual decisions: `{s['residual_count']}`.
- Unsupported residuals under gate 56 best signature:
  `{s['unsupported_residuals_under_gate56_best']}/{s['residual_count']}`.
- Distinct stable shape labels: `{s['distinct_stable_shape_labels']}`.
- Site bits: `{s['site_bits']:.3f}`.
- Label-order bits: `{s['label_order_bits']:.3f}`.
- Baseline lookup bits: `{s['baseline_lookup_bits']:.3f}`.
- Best valid model: `{s['best_valid_model']}`.
- Best valid net vs lookup: `{s['best_valid_net_vs_lookup_bits']:.3f}`.
- Best invalid/oracle model: `{s['best_invalid_model']}`.
- Best invalid/oracle net vs lookup: `{s['best_invalid_net_vs_lookup_bits']:.3f}`.
- Gate 48 best zero-FP residual-site detector TP:
  `{s['gate48_best_zero_fp_tp']}/{s['residual_count']}`.
- Promotes latent path-state budget: `{s['promotes_latent_path_state_budget']}`.

## Cost Rows

{md_table(cost_rows, ["model", "valid", "site oracle", "site bits", "label bits", "dictionary bits", "total bits", "net vs lookup"])}

## Residual Rows

{md_table(residual_rows, ["book", "op", "class", "stable label", "gate56 status"])}

## Decision

No latent path-state budget is promoted. The best valid latent-state accounting
is the explicit residual shape lookup itself: it pays the same `{s['baseline_lookup_bits']:.3f}`
bits before any interpretable state rule is charged. The cheaper rows are
invalid as parser explanations because they grant residual sites or ignore the
failed site detector.

- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
"""
    md_path.write_text(body, encoding="utf-8")


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
