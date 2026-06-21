from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

PREQ_ORDER_CONTROL = (
    ROOT
    / "analysis"
    / "authorial_mechanism_20260620"
    / "reports"
    / "test_results"
    / "120_prequential_order_control_audit.json"
)
ONLINE_FRONTIER_CONTROLS = (
    ROOT
    / "analysis"
    / "prequential_and_row0_origin_audit_20260621"
    / "reports"
    / "test_results"
    / "22_online_order_frontier_controls.json"
)
ORDER_FRONTIER_PROMOTION = (
    ROOT
    / "analysis"
    / "prequential_and_row0_origin_audit_20260621"
    / "reports"
    / "test_results"
    / "23_order_frontier_promotion_gate.json"
)
ONLINE_REPARSE_ORDER_CONTROL = (
    ROOT
    / "analysis"
    / "authorial_mechanism_20260620"
    / "reports"
    / "test_results"
    / "130_online_reparse_order_control_audit.json"
)

OUT_STEM = "01_book_order_dependency_gate"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def assert_boundary(name: str, data: dict[str, Any]) -> None:
    if data.get("translation_delta") != "NONE":
        raise RuntimeError(f"{name} changed translation boundary")
    if data.get("case_reopened", False) is True:
        raise RuntimeError(f"{name} reopened case")
    if data.get("plaintext_claim", False) is True:
        raise RuntimeError(f"{name} introduced plaintext")
    decision = data.get("decision", {})
    if decision and decision.get("row0_origin_status") not in {
        None,
        "unchanged_exogenous",
        "exogenous_under_current_evidence",
    }:
        raise RuntimeError(f"{name} changed row0 origin")
    if decision and decision.get("translation_or_plaintext_status", "NONE") != "NONE":
        raise RuntimeError(f"{name} introduced translation/plaintext")


def make_result() -> dict[str, Any]:
    preq = load_json(PREQ_ORDER_CONTROL)
    frontier = load_json(ONLINE_FRONTIER_CONTROLS)
    promotion = load_json(ORDER_FRONTIER_PROMOTION)
    reparse = load_json(ONLINE_REPARSE_ORDER_CONTROL)
    assert_boundary("prequential_order_control", preq)
    assert_boundary("online_frontier_controls", frontier)
    assert_boundary("order_frontier_promotion", promotion)
    assert_boundary("online_reparse_order_control", reparse)

    preq_summary = preq["summary"]
    frontier_summary = frontier["summary"]
    promotion_summary = promotion["summary"]
    random_summary = reparse["random_summary"]
    numeric_order_promoted_as_generator = False
    arbitrary_order_promoted = (
        promotion_summary["promotable_order_count"] > 0
        or random_summary["random_charged_le_numeric_count"] > 0
    )
    classification = (
        "book_order_generator_promoted"
        if numeric_order_promoted_as_generator
        else "book_order_dependency_retained"
    )
    return {
        "schema": "book_order_dependency_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "prequential_order_control": rel(PREQ_ORDER_CONTROL),
            "online_frontier_controls": rel(ONLINE_FRONTIER_CONTROLS),
            "order_frontier_promotion_gate": rel(ORDER_FRONTIER_PROMOTION),
            "online_reparse_order_control": rel(ONLINE_REPARSE_ORDER_CONTROL),
        },
        "scope": {
            "analysis_only": True,
            "tests_numeric_order_specificity": True,
            "tests_non_numeric_order_promotion": True,
            "does_not_search_new_arbitrary_orders": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
        },
        "summary": {
            "numeric_order": list(range(70)),
            "preq_prefix_online_beats_uniform_cutoffs": preq_summary[
                "prefix_online_beats_uniform_cutoffs"
            ],
            "preq_prefix_online_order_specific_cutoffs_at_p05": preq_summary[
                "prefix_online_order_specific_cutoffs_at_p05"
            ],
            "preq_prefix_frozen_order_specific_cutoffs_at_p05": preq_summary[
                "prefix_frozen_order_specific_cutoffs_at_p05"
            ],
            "frontier_numeric_after_bootstrap_raw_wins": frontier_summary[
                "numeric_after_bootstrap_beats_raw_count"
            ],
            "frontier_after_bootstrap_book_count": frontier_summary[
                "after_bootstrap_book_count"
            ],
            "frontier_orders_with_perfect_after_bootstrap": frontier_summary[
                "orders_with_perfect_after_bootstrap_count"
            ],
            "frontier_random_orders_with_perfect_after_bootstrap": frontier_summary[
                "random_orders_with_perfect_after_bootstrap_count"
            ],
            "frontier_best_total_gain_order": frontier_summary[
                "best_total_gain_order"
            ]["name"],
            "frontier_best_total_gain_delta_vs_numeric_bits": frontier_summary[
                "best_total_gain_order"
            ]["delta_vs_numeric_bits"],
            "promotion_full_formula_best_raw_order": promotion_summary[
                "full_formula_best_raw_order"
            ],
            "promotion_full_formula_best_charged_order": promotion_summary[
                "full_formula_best_charged_order"
            ],
            "promotion_promotable_order_count": promotion_summary[
                "promotable_order_count"
            ],
            "random_04_full_formula_charged_delta_vs_numeric_bits": promotion_summary[
                "random_04"
            ]["full_formula_charged_delta_vs_numeric_bits"],
            "online_reparse_classification": reparse["classification"],
            "online_reparse_numeric_bits": reparse["numeric_recomputed_bits"],
            "online_reparse_random_raw_le_numeric_count": random_summary[
                "random_raw_le_numeric_count"
            ],
            "online_reparse_random_charged_le_numeric_count": random_summary[
                "random_charged_le_numeric_count"
            ],
            "online_reparse_random_raw_min_delta_vs_numeric_bits": (
                random_summary["raw_min_bits"] - reparse["numeric_recomputed_bits"]
            ),
            "arbitrary_order_descriptor_bits": reparse[
                "arbitrary_order_descriptor_bits"
            ],
            "numeric_order_promoted_as_generator": numeric_order_promoted_as_generator,
            "arbitrary_order_promoted": arbitrary_order_promoted,
            "interpretation": (
                "Numeric order remains the compact canonical order used by the "
                "formula, and arbitrary non-numeric orders are not promoted. But "
                "the predictive controls do not prove that numeric order is an "
                "authorial or mechanically generated order."
            ),
        },
        "evidence_rows": [
            {
                "gate": "prequential_order_control",
                "classification": preq["classification"],
                "supports": "learned components beat uniform",
                "limits": "numeric prefixes are not unusually strong against random same-size train sets",
            },
            {
                "gate": "online_frontier_controls",
                "classification": frontier["classification"],
                "supports": "numeric online frontier is predictive after bootstrap",
                "limits": "10/11 tested orders and 6/6 random orders also have perfect after-bootstrap raw wins",
            },
            {
                "gate": "order_frontier_promotion",
                "classification": promotion["classification"],
                "supports": "frontier metric is not a promotion score",
                "limits": "no tested non-numeric order promotes after full formula and descriptor costs",
            },
            {
                "gate": "online_reparse_order_control",
                "classification": reparse["classification"],
                "supports": "numeric order survives named/random full reparse controls",
                "limits": "survival of canonical numeric order is not a derivation of that order",
            },
        ],
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": classification,
            "book_order_status": "canonical_numeric_order_retained_not_generated",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / f"{OUT_STEM}.json"
    md_path = TEST_RESULTS / f"{OUT_STEM}.md"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    s = result["summary"]
    lines = [
        "# Book Order Dependency Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Consolidate the existing order controls against the current generation",
        "boundary: is numeric book order a generated mechanism, merely the",
        "canonical compact order, or replaceable by an arbitrary order?",
        "",
        "## Summary",
        "",
        f"- Prequential prefix online beats uniform cutoffs: `{s['preq_prefix_online_beats_uniform_cutoffs']}`.",
        f"- Prequential numeric-order-specific cutoffs at p<=0.05: `{s['preq_prefix_online_order_specific_cutoffs_at_p05']}` online / `{s['preq_prefix_frozen_order_specific_cutoffs_at_p05']}` frozen.",
        f"- Numeric online frontier raw wins after bootstrap: `{s['frontier_numeric_after_bootstrap_raw_wins']}/{s['frontier_after_bootstrap_book_count']}`.",
        f"- Orders with perfect after-bootstrap frontier: `{s['frontier_orders_with_perfect_after_bootstrap']}`.",
        f"- Random orders with perfect after-bootstrap frontier: `{s['frontier_random_orders_with_perfect_after_bootstrap']}`.",
        f"- Frontier best total-gain order: `{s['frontier_best_total_gain_order']}` (`{s['frontier_best_total_gain_delta_vs_numeric_bits']:+.3f}` bits vs numeric).",
        f"- Full-formula best raw/charged order: `{s['promotion_full_formula_best_raw_order']}` / `{s['promotion_full_formula_best_charged_order']}`.",
        f"- Promotable non-numeric orders: `{s['promotion_promotable_order_count']}`.",
        f"- `random_04` full-formula charged delta vs numeric: `{s['random_04_full_formula_charged_delta_vs_numeric_bits']:+.3f}` bits.",
        f"- Online reparse random raw/charged <= numeric: `{s['online_reparse_random_raw_le_numeric_count']}` / `{s['online_reparse_random_charged_le_numeric_count']}`.",
        "",
        "## Evidence Matrix",
        "",
        "| Gate | Classification | Supports | Limits |",
        "| --- | --- | --- | --- |",
    ]
    for row in result["evidence_rows"]:
        lines.append(
            f"| `{row['gate']}` | `{row['classification']}` | {row['supports']} | {row['limits']} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Numeric order promoted as generator: `{s['numeric_order_promoted_as_generator']}`.",
            f"- Arbitrary order promoted: `{s['arbitrary_order_promoted']}`.",
            f"- {s['interpretation']}",
            "- Compression bound is unchanged.",
            "- Row0 remains exogenous and unchanged.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        ]
    )
    md_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    result = make_result()
    write_result(result)
    print(json.dumps(result["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
