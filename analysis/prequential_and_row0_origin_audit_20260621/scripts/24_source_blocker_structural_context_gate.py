from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"
AUTHORIAL_RESULTS = ROOT / "analysis" / "authorial_mechanism_20260620" / "reports" / "test_results"

CROSS_OP_BREAK_EVEN = AUTHORIAL_RESULTS / "153_cross_op_source_break_even_audit.json"
SOURCE_CONTEXT = AUTHORIAL_RESULTS / "154_copy_source_structural_context_audit.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def make_result() -> dict[str, Any]:
    break_even = load_json(CROSS_OP_BREAK_EVEN)
    source_context = load_json(SOURCE_CONTEXT)

    for name, data in [
        ("cross_op_source_break_even", break_even),
        ("copy_source_structural_context", source_context),
    ]:
        if data.get("translation_delta") != "NONE":
            raise RuntimeError(f"{name} changed translation boundary")
        if data.get("case_reopened") is not False:
            raise RuntimeError(f"{name} reopened case")
        if data.get("plaintext_claim") is not False:
            raise RuntimeError(f"{name} introduced plaintext")

    candidate_delta = float(break_even["candidate"]["delta_bits"])
    source_margin = float(break_even["break_even"]["source_delta_margin_over_break_even_bits"])
    no_source_oracle_delta = float(break_even["break_even"]["no_source_oracle_delta_bits"])
    active_source_delta = float(break_even["break_even"]["active_copy_source_delta_bits"])
    best_context = source_context["best_non_global"]
    best_context_delta = float(best_context["delta_vs_global_bits"])
    prefix_rows = source_context["prefix_future_suffix"]["rows"]
    prefix_losses = [
        float(row["candidate_minus_global_frozen_bits"]) for row in prefix_rows
    ]
    context_promoted = bool(source_context["decision"]["structural_context_promoted"])

    source_blocker_closed = (
        candidate_delta > 0
        and source_margin > 0
        and no_source_oracle_delta < 0
        and best_context_delta > 0
        and all(value > 0 for value in prefix_losses)
        and not context_promoted
    )
    classification = (
        "simple_source_contexts_do_not_rescue_cross_op_near_tie"
        if source_blocker_closed
        else "source_context_gate_requires_followup"
    )

    return {
        "schema": "source_blocker_structural_context_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "cross_op_source_break_even": rel(CROSS_OP_BREAK_EVEN),
            "copy_source_structural_context": rel(SOURCE_CONTEXT),
        },
        "summary": {
            "cross_op_candidate_delta_bits": candidate_delta,
            "source_delta_margin_over_break_even_bits": source_margin,
            "no_source_oracle_delta_bits": no_source_oracle_delta,
            "active_copy_source_delta_bits": active_source_delta,
            "best_non_global_context": best_context["name"],
            "best_non_global_context_delta_vs_global_bits": best_context_delta,
            "best_non_global_context_full_bits": best_context["bits"],
            "prefix_frozen_split_count": len(prefix_rows),
            "best_context_prefix_frozen_loss_count": sum(
                1 for value in prefix_losses if value > 0
            ),
            "best_context_min_prefix_frozen_delta_bits": min(prefix_losses),
            "best_context_max_prefix_frozen_delta_bits": max(prefix_losses),
            "structural_context_promoted": context_promoted,
            "interpretation": (
                "The cross-op candidate is blocked only narrowly by source cost, "
                "but the tested simple source contexts worsen the full source "
                "stream and every prefix-frozen split. The next source advance "
                "needs a new derivation or representation, not a simple declared "
                "context split."
            ),
        },
        "decision": {
            "compression_bound_status": "unchanged",
            "cross_op_candidate_status": "not_promoted",
            "source_free_oracle_status": "not_promoted_non_decodable",
            "source_context_status": "simple_structural_contexts_rejected",
            "generation_explanation_status": "source_blocker_localized",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / "24_source_blocker_structural_context_gate.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    summary = result["summary"]
    lines = [
        "# Source Blocker Structural Context Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Audits 153-154 isolate a tight source-cost blocker: the best cross-op",
        "optional literal repair would improve under a source-free oracle, but",
        "source-free coding is not decodable and the active source ledger remains",
        "slightly above break-even. This gate checks whether the follow-up",
        "structural source contexts actually rescue that blocker.",
        "",
        "## Summary",
        "",
        f"- Cross-op candidate delta: `{summary['cross_op_candidate_delta_bits']:+.3f}` bits.",
        f"- Source margin over break-even: "
        f"`{summary['source_delta_margin_over_break_even_bits']:+.3f}` bits.",
        f"- Source-free oracle delta: `{summary['no_source_oracle_delta_bits']:+.3f}` bits.",
        f"- Active copy-source delta: `{summary['active_copy_source_delta_bits']:+.3f}` bits.",
        f"- Best non-global source context: `{summary['best_non_global_context']}`.",
        f"- Best non-global context delta vs global: "
        f"`{summary['best_non_global_context_delta_vs_global_bits']:+.3f}` bits.",
        f"- Prefix-frozen losses for best context: "
        f"`{summary['best_context_prefix_frozen_loss_count']}/"
        f"{summary['prefix_frozen_split_count']}`.",
        f"- Min/max prefix-frozen delta: "
        f"`{summary['best_context_min_prefix_frozen_delta_bits']:+.3f}` / "
        f"`{summary['best_context_max_prefix_frozen_delta_bits']:+.3f}` bits.",
        "",
        "## Interpretation",
        "",
        "The near tie is real but not promotable. The source-free oracle would",
        "save enough bits, but it removes a required decodable source choice.",
        "The tested mechanical context split that comes closest, `book_half`,",
        "is still `+5.872` bits worse on the full source stream and worse in",
        "all `5/5` prefix-frozen checks. That rejects simple structural context",
        "splitting as the next source fix.",
        "",
        "## Boundary",
        "",
        "- No compression bound is promoted.",
        "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        "- Row0/table origin remains exogenous.",
    ]
    (TEST_RESULTS / "24_source_blocker_structural_context_gate.md").write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
