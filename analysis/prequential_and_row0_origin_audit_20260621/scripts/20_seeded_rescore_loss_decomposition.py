from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

RESCORE = TEST_RESULTS / "19_seeded_online_formula_rescore_audit.json"
BOOTSTRAP = TEST_RESULTS / "18_online_bootstrap_seed_policy_audit.json"

COMPONENT_LABELS = {
    "literal_bits_no_payload": "literal_length_or_structure",
    "literal_payload_bits": "literal_payload",
    "copy_address_bits": "copy_address",
    "copy_length_code_bits": "copy_length",
    "item_type_split_only_stream_bits": "item_type",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def candidate_by_name(rescore: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["candidate"]: row for row in rescore["candidates"]}


def decompose(candidate: dict[str, Any]) -> dict[str, Any]:
    deltas = candidate["component_delta_vs_online_bits"]
    rows = [
        {
            "component": key,
            "label": COMPONENT_LABELS[key],
            "delta_bits": deltas[key],
            "effect": "penalty" if deltas[key] > 0 else "saving" if deltas[key] < 0 else "neutral",
        }
        for key in COMPONENT_LABELS
    ]
    penalties = [row for row in rows if row["delta_bits"] > 0]
    savings = [row for row in rows if row["delta_bits"] < 0]
    return {
        "component_rows": rows,
        "total_penalty_bits": sum(row["delta_bits"] for row in penalties),
        "total_saving_bits": -sum(row["delta_bits"] for row in savings),
        "net_delta_bits": candidate["delta_vs_online_bits"],
        "largest_penalty": max(penalties, key=lambda row: row["delta_bits"]) if penalties else None,
        "largest_saving": min(savings, key=lambda row: row["delta_bits"]) if savings else None,
        "penalty_components": [row["component"] for row in penalties],
        "saving_components": [row["component"] for row in savings],
    }


def make_result() -> dict[str, Any]:
    rescore = load_json(RESCORE)
    bootstrap = load_json(BOOTSTRAP)
    candidates = candidate_by_name(rescore)
    seeded = candidates["seeded_online_formula_rescored"]
    bounded = candidates["book_bounded_seeded_online_formula_rescored"]
    seeded_decomposition = decompose(seeded)
    bounded_decomposition = decompose(bounded)
    local_seed_saving = bootstrap["summary"]["raw_seeded_stream_saving_vs_online_bits"]
    payload_penalty = next(
        row["delta_bits"]
        for row in seeded_decomposition["component_rows"]
        if row["component"] == "literal_payload_bits"
    )

    return {
        "schema": "seeded_rescore_loss_decomposition.v1",
        "classification": "seed_rescore_loss_explained_by_literal_payload_penalty",
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "seeded_online_formula_rescore": rel(RESCORE),
            "online_bootstrap_seed_policy": rel(BOOTSTRAP),
        },
        "local_bootstrap_accounting": {
            "raw_seeded_stream_saving_vs_online_bits": local_seed_saving,
            "raw_seeded_failure_books": bootstrap["summary"]["raw_seeded_failure_books"],
            "raw_seeded_raw_wins_or_ties": bootstrap["summary"]["raw_seeded_raw_wins_or_ties"],
        },
        "seeded_online_formula_rescored": seeded_decomposition,
        "book_bounded_seeded_online_formula_rescored": bounded_decomposition,
        "summary": {
            "seeded_delta_vs_online_bits": seeded["delta_vs_online_bits"],
            "seeded_payload_penalty_bits": payload_penalty,
            "seeded_non_payload_savings_bits": seeded_decomposition["total_saving_bits"],
            "seeded_total_penalty_bits": seeded_decomposition["total_penalty_bits"],
            "payload_penalty_exceeds_local_seed_saving": payload_penalty > local_seed_saving,
            "book_bounded_delta_vs_online_bits": bounded["delta_vs_online_bits"],
            "book_bounded_largest_penalty_component": bounded_decomposition["largest_penalty"],
            "promoted_candidate_count": rescore["summary"]["promoted_candidate_count"],
            "interpretation": (
                "The seed saves local cold-start accounting, but the complete "
                "formula scorer charges the full literal payload for book 0. "
                "That payload penalty is larger than the local seed saving and "
                "outweighs copy/item/literal-structure savings."
            ),
        },
        "decision": {
            "loss_decomposition_status": "explained",
            "seed_policy_status": "bootstrap_accounting_only",
            "compression_bound_status": "unchanged",
            "generation_explanation_status": "seed_caveat_clarified_not_promoted",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / "20_seeded_rescore_loss_decomposition.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Seeded Rescore Loss Decomposition",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Audit 19 rejected the book-0 seed policy as a full-formula promotion.",
        "This audit decomposes that rejection by component so the local-vs-full",
        "scorer mismatch is explicit.",
        "",
        "## Summary",
        "",
        f"- Local bootstrap saving from audit 18: `{result['local_bootstrap_accounting']['raw_seeded_stream_saving_vs_online_bits']:.3f}` bits.",
        f"- Seeded formula delta vs online: `{result['summary']['seeded_delta_vs_online_bits']:.3f}` bits.",
        f"- Seeded literal-payload penalty: `{result['summary']['seeded_payload_penalty_bits']:.3f}` bits.",
        f"- Seeded non-payload savings: `{result['summary']['seeded_non_payload_savings_bits']:.3f}` bits.",
        f"- Payload penalty exceeds local seed saving: `{result['summary']['payload_penalty_exceeds_local_seed_saving']}`.",
        f"- Book-bounded seeded delta vs online: `{result['summary']['book_bounded_delta_vs_online_bits']:.3f}` bits.",
        "",
        "## Seeded Online Formula",
        "",
        "| Component | Effect | Delta bits |",
        "|---|---|---:|",
    ]
    for row in result["seeded_online_formula_rescored"]["component_rows"]:
        lines.append(f"| `{row['label']}` | `{row['effect']}` | `{row['delta_bits']:.3f}` |")

    lines.extend(
        [
            "",
            "## Book-Bounded Seeded Formula",
            "",
            "| Component | Effect | Delta bits |",
            "|---|---|---:|",
        ]
    )
    for row in result["book_bounded_seeded_online_formula_rescored"]["component_rows"]:
        lines.append(f"| `{row['label']}` | `{row['effect']}` | `{row['delta_bits']:.3f}` |")

    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- The seed policy fails full rescoring because literal payload cost dominates the local seed saving.",
            "- This clarifies the boundary between local bootstrap accounting and complete formula promotion.",
            "- No plaintext, translation, row0-origin change, or case reopening is introduced.",
        ]
    )
    (TEST_RESULTS / "20_seeded_rescore_loss_decomposition.md").write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
