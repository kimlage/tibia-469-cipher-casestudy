from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

ORDER_FRONTIER = TEST_RESULTS / "22_online_order_frontier_controls.json"
ORDER_CONTROL = (
    ROOT
    / "analysis"
    / "authorial_mechanism_20260620"
    / "reports"
    / "test_results"
    / "130_online_reparse_order_control_audit.json"
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def promotion_threshold(raw_delta_vs_numeric_bits: float) -> float:
    return -raw_delta_vs_numeric_bits


def make_result() -> dict[str, Any]:
    frontier = load_json(ORDER_FRONTIER)
    control = load_json(ORDER_CONTROL)
    frontier_by_name = {row["name"]: row for row in frontier["rows"]}
    rows = []
    for control_row in control["rows"]:
        name = control_row["name"]
        frontier_row = frontier_by_name[name]
        summary = frontier_row["summary"]
        raw_delta = float(control_row["raw_delta_vs_numeric_bits"])
        descriptor_bits = float(control_row["descriptor_bits"])
        charged_delta = float(control_row["charged_delta_vs_numeric_bits"])
        required_descriptor = promotion_threshold(raw_delta)
        rows.append(
            {
                "name": name,
                "family": control_row["family"],
                "frontier_after_bootstrap_raw_wins": summary[
                    "after_bootstrap_beats_raw_count"
                ],
                "frontier_after_bootstrap_book_count": summary["after_bootstrap_book_count"],
                "frontier_perfect_after_bootstrap": summary[
                    "after_bootstrap_beats_raw_count"
                ]
                == summary["after_bootstrap_book_count"],
                "frontier_total_gain_delta_vs_numeric_bits": frontier_row[
                    "delta_total_gain_vs_numeric_bits"
                ],
                "frontier_mean_after_bootstrap_delta_vs_numeric_bits": frontier_row[
                    "delta_after_bootstrap_mean_gain_vs_numeric_bits"
                ],
                "full_formula_raw_delta_vs_numeric_bits": raw_delta,
                "descriptor_bits": descriptor_bits,
                "full_formula_charged_delta_vs_numeric_bits": charged_delta,
                "required_descriptor_to_beat_numeric_bits": required_descriptor,
                "nonnegative_descriptor_can_promote": required_descriptor >= 0.0
                and descriptor_bits < required_descriptor,
                "raw_formula_beats_numeric": raw_delta < 0.0,
                "charged_formula_beats_numeric": charged_delta < 0.0,
            }
        )

    frontier_best_total = frontier["summary"]["best_total_gain_order"]["name"]
    frontier_best_mean = frontier["summary"]["best_after_bootstrap_mean_gain_order"][
        "name"
    ]
    control_best_raw = control["best_raw"]["name"]
    control_best_charged = control["best_charged"]["name"]
    perfect_frontier_rows = [row for row in rows if row["frontier_perfect_after_bootstrap"]]
    frontier_positive_but_formula_worse = [
        row
        for row in rows
        if row["frontier_total_gain_delta_vs_numeric_bits"] > 0
        and row["full_formula_charged_delta_vs_numeric_bits"] > 0
    ]
    promotable_rows = [row for row in rows if row["charged_formula_beats_numeric"]]
    if promotable_rows:
        classification = "order_frontier_control_promotable_candidate_found"
    elif frontier_positive_but_formula_worse:
        classification = "frontier_metric_not_formula_promotion_score"
    else:
        classification = "order_frontier_controls_not_promotable"

    return {
        "schema": "order_frontier_promotion_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "online_order_frontier_controls": rel(ORDER_FRONTIER),
            "online_reparse_order_control_audit": rel(ORDER_CONTROL),
        },
        "summary": {
            "frontier_best_total_gain_order": frontier_best_total,
            "frontier_best_after_bootstrap_mean_order": frontier_best_mean,
            "full_formula_best_raw_order": control_best_raw,
            "full_formula_best_charged_order": control_best_charged,
            "perfect_frontier_after_bootstrap_order_count": len(perfect_frontier_rows),
            "order_count": len(rows),
            "frontier_positive_but_formula_worse_orders": [
                row["name"] for row in frontier_positive_but_formula_worse
            ],
            "promotable_order_count": len(promotable_rows),
            "promotable_orders": [row["name"] for row in promotable_rows],
            "minimum_full_formula_raw_delta_vs_numeric_bits": min(
                row["full_formula_raw_delta_vs_numeric_bits"] for row in rows
            ),
            "minimum_full_formula_charged_delta_vs_numeric_bits": min(
                row["full_formula_charged_delta_vs_numeric_bits"] for row in rows
            ),
            "random_04": next(row for row in rows if row["name"] == "random_04"),
            "interpretation": (
                "The per-book frontier raw-win metric is useful as a predictive "
                "control, but it is not the full formula promotion score. Every "
                "tested non-numeric order remains worse than numeric under the "
                "complete online formula ledger before or after descriptor cost."
            ),
        },
        "rows": rows,
        "decision": {
            "compression_bound_status": "unchanged",
            "generation_explanation_status": "frontier_metric_demoted_from_promotion_score",
            "numeric_order_status": "not_proved_by_frontier_but_retained_by_full_formula_gate",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / "23_order_frontier_promotion_gate.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    random_04 = result["summary"]["random_04"]
    lines = [
        "# Order Frontier Promotion Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Audit 22 showed that the per-book online frontier is not numeric-order",
        "unique: several simple and random order controls also beat raw coding",
        "after their bootstrap position. This audit checks whether that local",
        "frontier metric can promote a non-numeric order once the complete online",
        "formula ledger and order-description cost are applied.",
        "",
        "## Summary",
        "",
        f"- Frontier best total-gain order: "
        f"`{result['summary']['frontier_best_total_gain_order']}`.",
        f"- Frontier best after-bootstrap mean order: "
        f"`{result['summary']['frontier_best_after_bootstrap_mean_order']}`.",
        f"- Full-formula best raw order: `{result['summary']['full_formula_best_raw_order']}`.",
        f"- Full-formula best charged order: "
        f"`{result['summary']['full_formula_best_charged_order']}`.",
        f"- Perfect after-bootstrap frontier orders: "
        f"`{result['summary']['perfect_frontier_after_bootstrap_order_count']}/"
        f"{result['summary']['order_count']}`.",
        f"- Promotable non-numeric orders: "
        f"`{result['summary']['promotable_order_count']}`.",
        f"- `random_04` frontier total delta vs numeric: "
        f"`{random_04['frontier_total_gain_delta_vs_numeric_bits']:+.3f}` bits.",
        f"- `random_04` full-formula raw delta vs numeric: "
        f"`{random_04['full_formula_raw_delta_vs_numeric_bits']:+.3f}` bits.",
        f"- `random_04` full-formula charged delta vs numeric: "
        f"`{random_04['full_formula_charged_delta_vs_numeric_bits']:+.3f}` bits.",
        "",
        "## Gate Table",
        "",
        "| Order | Frontier after bootstrap | Frontier total delta | Full raw delta | Descriptor | Charged delta | Promotable |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in result["rows"]:
        lines.append(
            f"| `{row['name']}` | "
            f"`{row['frontier_after_bootstrap_raw_wins']}/"
            f"{row['frontier_after_bootstrap_book_count']}` | "
            f"`{row['frontier_total_gain_delta_vs_numeric_bits']:+.3f}` | "
            f"`{row['full_formula_raw_delta_vs_numeric_bits']:+.3f}` | "
            f"`{row['descriptor_bits']:.3f}` | "
            f"`{row['full_formula_charged_delta_vs_numeric_bits']:+.3f}` | "
            f"`{row['charged_formula_beats_numeric']}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The order-frontier metric is a predictive diagnostic, not a promotion",
            "score. `random_04` is the clearest example: it is better than numeric",
            "on the book-bounded frontier total, but it is worse by `188.584` bits",
            "under the complete online formula before order cost and by `521.038`",
            "bits after charging its arbitrary permutation descriptor. No tested",
            "non-numeric order can lower the compression bound under a nonnegative",
            "descriptor.",
            "",
            "## Boundary",
            "",
            "- No compression bound is promoted.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
            "- Row0/table origin remains exogenous.",
        ]
    )
    (TEST_RESULTS / "23_order_frontier_promotion_gate.md").write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
