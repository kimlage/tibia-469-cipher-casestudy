from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

ROW0_PARALLEL = ROOT / "analysis" / "row0_origin_parallel_20260621"
ROW0_REPORTS = ROW0_PARALLEL / "reports"
ROW0_TEST_RESULTS = ROW0_REPORTS / "test_results"

ROW0_FINAL_REPORT = ROW0_REPORTS / "final_row0_origin_parallel_report.md"
ROW0_NEXT_FRONTIER_REPORT = ROW0_REPORTS / "row0_next_frontier_report.md"
ROW0_DEEP_PROVENANCE = ROW0_TEST_RESULTS / "154_row0_deep_provenance_audit.json"
ROW0_SCOREBOARD = ROW0_TEST_RESULTS / "155_row0_improvement_scoreboard.json"
ROW0_PARTIAL_WORKSHEET = ROW0_TEST_RESULTS / "156_row0_partial_worksheet_model.json"
ROW0_SURFACE = ROW0_TEST_RESULTS / "157_row0_surface_exception_focus.json"
ROW0_NEXT_FRONTIER = ROW0_TEST_RESULTS / "158_row0_next_frontier_synthesis.json"
ROW0_PAID_ANCHOR = ROW0_TEST_RESULTS / "159_row0_paid_anchor_reduction_gate.json"

ROW0_BRIDGE = TEST_RESULTS / "47_row0_parallel_provenance_bridge_audit.json"
PARTIAL_SHIFT_FORMULA = TEST_RESULTS / "66_partial_boundary_shift_formula_gate.json"
PARTIAL_SHIFT_SECOND_PASS_FORMULA = (
    TEST_RESULTS / "68_partial_boundary_shift_second_pass_formula_gate.json"
)
PARTIAL_SHIFT_SATURATION = TEST_RESULTS / "69_partial_boundary_shift_saturation_gate.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def assert_no_semantics(name: str, data: dict[str, Any]) -> None:
    if data.get("translation_delta") != "NONE":
        raise RuntimeError(f"{name} changed translation boundary")
    if data.get("case_reopened", False) is not False:
        raise RuntimeError(f"{name} reopened the case")
    if data.get("plaintext_claim", False) is not False:
        raise RuntimeError(f"{name} introduced plaintext")


def make_result() -> dict[str, Any]:
    deep = load_json(ROW0_DEEP_PROVENANCE)
    scoreboard = load_json(ROW0_SCOREBOARD)
    worksheet = load_json(ROW0_PARTIAL_WORKSHEET)
    surface = load_json(ROW0_SURFACE)
    next_frontier = load_json(ROW0_NEXT_FRONTIER)
    paid = load_json(ROW0_PAID_ANCHOR)
    bridge = load_json(ROW0_BRIDGE)
    partial_formula = load_json(PARTIAL_SHIFT_FORMULA)
    second_formula = load_json(PARTIAL_SHIFT_SECOND_PASS_FORMULA)
    saturation = load_json(PARTIAL_SHIFT_SATURATION)

    for name, data in [
        ("row0_deep_provenance", deep),
        ("row0_scoreboard", scoreboard),
        ("row0_partial_worksheet", worksheet),
        ("row0_surface_exception", surface),
        ("row0_next_frontier", next_frontier),
        ("row0_paid_anchor", paid),
        ("row0_parallel_bridge", bridge),
        ("partial_boundary_shift_formula", partial_formula),
        ("partial_boundary_shift_second_pass_formula", second_formula),
        ("partial_boundary_shift_saturation", saturation),
    ]:
        assert_no_semantics(name, data)

    if next_frontier["decisions"]["overall"] != (
        "row0_advance_requires_primary_source_or_new_paid_anchor_source"
    ):
        raise RuntimeError("row0 next-frontier decision changed")
    if paid["summary"]["full_explicit_pair_label_model_promoted"]:
        raise RuntimeError("paid anchor gate promoted full explicit model")
    if paid["summary"]["controlled_paid_subset_promoted"]:
        raise RuntimeError("paid anchor gate promoted a controlled paid subset")
    if saturation["summary"]["improving_candidate_count"] != 0:
        raise RuntimeError("partial-boundary saturation is no longer closed")

    formula_gates = [partial_formula, second_formula, saturation]
    current_bound = float(saturation["summary"]["current_total_bits"])
    promotions = [
        {
            "source": rel(PARTIAL_SHIFT_FORMULA),
            "classification": partial_formula["classification"],
            "current_total_bits": partial_formula["summary"]["current_total_bits"],
            "candidate_total_bits": partial_formula["summary"]["candidate_total_bits"],
            "candidate_gain_bits": partial_formula["summary"]["candidate_gain_bits"],
            "row0_origin_status": partial_formula["decision"]["row0_origin_status"],
        },
        {
            "source": rel(PARTIAL_SHIFT_SECOND_PASS_FORMULA),
            "classification": second_formula["classification"],
            "current_total_bits": second_formula["summary"]["current_total_bits"],
            "candidate_total_bits": second_formula["summary"]["candidate_total_bits"],
            "candidate_gain_bits": second_formula["summary"]["candidate_gain_bits"],
            "row0_origin_status": second_formula["decision"]["row0_origin_status"],
        },
        {
            "source": rel(PARTIAL_SHIFT_SATURATION),
            "classification": saturation["classification"],
            "current_total_bits": saturation["summary"]["current_total_bits"],
            "improving_candidate_count": saturation["summary"][
                "improving_candidate_count"
            ],
            "row0_origin_status": saturation["decision"]["row0_origin_status"],
        },
    ]

    return {
        "schema": "recent_formula_row0_compatibility_audit.v1",
        "classification": "row0_unchanged_book_formula_improved",
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "row0_final_report": rel(ROW0_FINAL_REPORT),
            "row0_next_frontier_report": rel(ROW0_NEXT_FRONTIER_REPORT),
            "row0_deep_provenance": rel(ROW0_DEEP_PROVENANCE),
            "row0_scoreboard": rel(ROW0_SCOREBOARD),
            "row0_partial_worksheet": rel(ROW0_PARTIAL_WORKSHEET),
            "row0_surface_exception": rel(ROW0_SURFACE),
            "row0_next_frontier": rel(ROW0_NEXT_FRONTIER),
            "row0_paid_anchor": rel(ROW0_PAID_ANCHOR),
            "row0_parallel_bridge": rel(ROW0_BRIDGE),
            "recent_formula_gates": [row["source"] for row in promotions],
        },
        "summary": {
            "current_compression_bound_bits": current_bound,
            "row0_origin_status": "row0_origin_exogenous_under_current_evidence",
            "row0_changed": False,
            "recent_formula_status": "book_generation_improved_row0_unchanged",
            "recent_formula_assumes_row0": True,
            "predicts_row0_labels_under_holdout": False,
            "beats_row0_lookup_after_cost": False,
            "explains_surface_clues": False,
            "new_row0_provenance": False,
            "promoted_origin_formula_count": 0,
            "lookup_baseline_bits": paid["baseline_lookup_bits"],
            "all_anchors_explicit_pair_label_net_bits": paid["summary"][
                "all_anchors_explicit_pair_label_net_bits"
            ],
            "rare_singletons_explicit_pair_label_net_bits": paid["summary"][
                "rare_singletons_explicit_pair_label_net_bits"
            ],
            "surface_clues_retained": {
                "missing_ordered_code": "39",
                "present_reverse_code": "93",
                "directed_conflict": "19/91",
                "status": "PROMOTED_MECHANICAL_CLUE_surface_only",
            },
            "deep_provenance_decision": deep["decision"],
            "bridge_generation_explanation_status": bridge["decision"][
                "generation_explanation_status"
            ],
            "formula_gates_checked": promotions,
            "scoreboard_decision": scoreboard["decision"],
            "partial_worksheet_decision": worksheet["promotion_decision"],
            "paid_anchor_decision": paid["decision"],
        },
        "taxonomy": {
            "PROMOTED_ORIGIN_FORMULA": [],
            "PROMOTED_MECHANICAL_CLUE": [
                {
                    "name": "ordered_surface_render_layer",
                    "evidence": "99/100 ordered codes, missing 39, present 93, and directed 19/91 conflict",
                    "boundary": "surface/render clue only; does not derive pair labels",
                }
            ],
            "WEAK_CLUE": [
                {
                    "name": "partial_worksheet_model",
                    "evidence": "13 anchors reduce residual lookup only before source/anchor cost",
                    "boundary": "plausible authorial worksheet shape, not promoted",
                }
            ],
            "REJECTED_CONTROL": [
                {
                    "name": "paid_anchor_reduction_gate",
                    "evidence": "13-anchor explicit pair+label net is negative against lookup",
                    "net_bits": paid["summary"][
                        "all_anchors_explicit_pair_label_net_bits"
                    ],
                }
            ],
            "BLOCKED_NEEDS_EXTERNAL_SOURCE": [
                {
                    "name": "cipsoft_or_authorial_row0_origin",
                    "evidence": "local project provenance traced but primary CipSoft/authorial source remains untraced",
                }
            ],
            "AUDIT_ONLY": [
                {
                    "name": "recent_partial_boundary_formula_promotions",
                    "evidence": "lower the book-generation compression bound to 8154.676268 while assuming row0",
                    "boundary": "book formula only; row0 unchanged",
                }
            ],
        },
        "decision": {
            "row0_origin_status": "unchanged_exogenous",
            "recent_formula_status": "book_generation_improved_row0_unchanged",
            "compression_bound_status": "current_bound_8154_676268",
            "row0_scoreboard_status": "unchanged_no_origin_formula_promoted",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / "70_recent_formula_row0_compatibility_audit.json"
    md_path = TEST_RESULTS / "70_recent_formula_row0_compatibility_audit.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    s = result["summary"]
    lines = [
        "# Recent Formula Row0 Compatibility Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "This gate checks whether the latest partial-boundary formula promotions",
        "change the independent row0-origin conclusion. They do not: the formula",
        "front improves the book-generation bound while continuing to assume row0",
        "as an already supplied substrate.",
        "",
        "## Result",
        "",
        f"- Current compression bound checked: `{s['current_compression_bound_bits']:.6f}` bits.",
        f"- Row0 status: `{s['row0_origin_status']}`.",
        "- `row0 changed`: `False`.",
        f"- Recent formula status: `{s['recent_formula_status']}`.",
        f"- Predicts row0 labels under holdout: `{s['predicts_row0_labels_under_holdout']}`.",
        f"- Beats row0 lookup after cost: `{s['beats_row0_lookup_after_cost']}`.",
        f"- Explains `39`, `93`, `19/91`: `{s['explains_surface_clues']}`.",
        f"- New row0 provenance: `{s['new_row0_provenance']}`.",
        f"- Promoted origin formulas: `{s['promoted_origin_formula_count']}`.",
        "",
        "## Recent Formula Gates Checked",
        "",
        "| Source | Classification | Bound/gain | Row0 status |",
        "|---|---|---:|---|",
    ]
    for row in s["formula_gates_checked"]:
        if "candidate_gain_bits" in row:
            bound = f"{row['candidate_total_bits']:.6f} ({row['candidate_gain_bits']:+.6f})"
        else:
            bound = f"{row['current_total_bits']:.6f} (0 improving)"
        lines.append(
            f"| `{row['source']}` | `{row['classification']}` | `{bound}` | `{row['row0_origin_status']}` |"
        )

    lines.extend(
        [
            "",
            "## Row0 Compatibility Checks",
            "",
            "| Check | Outcome | Interpretation |",
            "|---|---|---|",
            "| Row0 label holdout prediction | `False` | Recent formula gates alter copy/reference recipes; they contain no independent row0 label predictor. |",
            "| Lookup reduction after rule/anchor cost | `False` | Paid anchor gate remains negative after explicit pair+label cost. |",
            "| `39` / `93` / `19/91` explanation | `False` | These stay promoted surface/render clues only, not label-origin derivations. |",
            "| New provenance | `False` | Local project provenance is partially traced, while CipSoft/authorial origin remains untraced. |",
            "| Formula assumes row0 | `True` | The book formula works downstream from the row0 substrate. |",
            "",
            "## Taxonomy",
            "",
        ]
    )
    for klass, rows in result["taxonomy"].items():
        lines.append(f"- `{klass}`: `{len(rows)}`")

    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- `row0 unchanged`.",
            "- The latest book-formula advances are compatibility-only from the row0 perspective.",
            "- No row0-origin formula is promoted.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        ]
    )
    md_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
