from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

BOOTSTRAP = TEST_RESULTS / "18_online_bootstrap_seed_policy_audit.json"
RESCORE = TEST_RESULTS / "19_seeded_online_formula_rescore_audit.json"
LOSS = TEST_RESULTS / "20_seeded_rescore_loss_decomposition.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def make_result() -> dict[str, Any]:
    bootstrap = load_json(BOOTSTRAP)
    rescore = load_json(RESCORE)
    loss = load_json(LOSS)
    formula_delta = rescore["summary"]["seeded_online_delta_vs_online_bits"]
    local_saving = bootstrap["summary"]["raw_seeded_stream_saving_vs_online_bits"]
    payload_penalty = loss["summary"]["seeded_payload_penalty_bits"]
    non_payload_savings = loss["summary"]["seeded_non_payload_savings_bits"]

    descriptor_policies = [
        {
            "policy": "zero_cost_deterministic_raw_if_online_loses",
            "descriptor_bits": 0.0,
            "description": (
                "Best-case deterministic fallback: no exception list is charged. "
                "This is the most favorable possible promotion test."
            ),
        },
        {
            "policy": "one_book_index_exception",
            "descriptor_bits": math.log2(70),
            "description": "Identify the single exception book among 70 books.",
        },
        {
            "policy": "exception_count_plus_one_book_index",
            "descriptor_bits": math.log2(71) + math.log2(70),
            "description": "Encode the exception count and then the selected book index.",
        },
        {
            "policy": "book_bitmask",
            "descriptor_bits": 70.0,
            "description": "A direct one-bit-per-book exception mask.",
        },
    ]
    rows = []
    for policy in descriptor_policies:
        descriptor = policy["descriptor_bits"]
        rows.append(
            {
                **policy,
                "local_seed_net_vs_online_bits": local_saving - descriptor,
                "full_formula_delta_vs_online_bits": formula_delta + descriptor,
                "full_formula_promotes": (formula_delta + descriptor) < 0,
            }
        )

    promotion_threshold_descriptor_bits = -formula_delta
    return {
        "schema": "seed_exception_signal_cost_audit.v1",
        "classification": "seed_exception_cannot_promote_under_nonnegative_signal_cost",
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "online_bootstrap_seed_policy": rel(BOOTSTRAP),
            "seeded_online_formula_rescore": rel(RESCORE),
            "seeded_rescore_loss_decomposition": rel(LOSS),
        },
        "rows": rows,
        "summary": {
            "local_seed_saving_bits": local_saving,
            "zero_cost_full_formula_delta_vs_online_bits": formula_delta,
            "promotion_threshold_descriptor_bits": promotion_threshold_descriptor_bits,
            "nonnegative_descriptor_can_promote": any(row["full_formula_promotes"] for row in rows),
            "payload_penalty_bits": payload_penalty,
            "non_payload_savings_bits": non_payload_savings,
            "interpretation": (
                "The seed exception already loses under complete formula rescoring "
                "before any descriptor cost is charged. A promoted exception policy "
                "would require a negative signal cost, which is inadmissible."
            ),
        },
        "decision": {
            "exception_signal_status": "rejected_for_formula_promotion",
            "seed_policy_status": "bootstrap_accounting_only",
            "compression_bound_status": "unchanged",
            "generation_explanation_status": "seed_exception_boundary_closed",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / "21_seed_exception_signal_cost_audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Seed Exception Signal Cost Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Audits 18-20 show that a raw seed for book `0` closes the local online",
        "bootstrap failure but fails complete formula rescoring. This audit asks",
        "whether any reasonable exception-signaling policy can rescue promotion.",
        "",
        "## Summary",
        "",
        f"- Local seed saving: `{result['summary']['local_seed_saving_bits']:.3f}` bits.",
        f"- Zero-cost full-formula delta vs online: `{result['summary']['zero_cost_full_formula_delta_vs_online_bits']:.3f}` bits.",
        f"- Descriptor threshold required for promotion: `< {result['summary']['promotion_threshold_descriptor_bits']:.3f}` bits.",
        f"- Nonnegative descriptor can promote: `{result['summary']['nonnegative_descriptor_can_promote']}`.",
        f"- Literal-payload penalty: `{result['summary']['payload_penalty_bits']:.3f}` bits.",
        f"- Non-payload savings: `{result['summary']['non_payload_savings_bits']:.3f}` bits.",
        "",
        "## Policies",
        "",
        "| Policy | Descriptor bits | Local net vs online | Full formula delta vs online | Promotes |",
        "|---|---:|---:|---:|---|",
    ]
    for row in result["rows"]:
        lines.append(
            f"| `{row['policy']}` | `{row['descriptor_bits']:.3f}` | "
            f"`{row['local_seed_net_vs_online_bits']:.3f}` | "
            f"`{row['full_formula_delta_vs_online_bits']:.3f}` | "
            f"`{row['full_formula_promotes']}` |"
        )

    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- The best-case zero-cost fallback is already `0.979` bits worse than the existing online formula.",
            "- Any real descriptor or exception signal makes the formula promotion strictly worse.",
            "- The seed exception remains a bootstrap explanation only; no new compression bound, row0 derivation, plaintext claim, or case reopening is introduced.",
        ]
    )
    (TEST_RESULTS / "21_seed_exception_signal_cost_audit.md").write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
