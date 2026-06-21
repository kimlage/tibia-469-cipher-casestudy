from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"
ROW0_PARALLEL = ROOT / "analysis" / "row0_origin_parallel_20260621"
ROW0_TEST_RESULTS = ROW0_PARALLEL / "reports" / "test_results"

FINAL_ROW0_REPORT = ROW0_PARALLEL / "reports" / "final_row0_origin_parallel_report.md"
NEXT_FRONTIER_REPORT = ROW0_PARALLEL / "reports" / "row0_next_frontier_report.md"
DEEP_PROVENANCE = ROW0_TEST_RESULTS / "154_row0_deep_provenance_audit.json"
SURFACE_EXCEPTION = ROW0_TEST_RESULTS / "157_row0_surface_exception_focus.json"
NEXT_FRONTIER = ROW0_TEST_RESULTS / "158_row0_next_frontier_synthesis.json"
PAID_ANCHOR = ROW0_TEST_RESULTS / "159_row0_paid_anchor_reduction_gate.json"


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
    deep = load_json(DEEP_PROVENANCE)
    surface = load_json(SURFACE_EXCEPTION)
    next_frontier = load_json(NEXT_FRONTIER)
    paid = load_json(PAID_ANCHOR)

    for name, data in [
        ("row0_deep_provenance_audit", deep),
        ("row0_surface_exception_focus", surface),
        ("row0_next_frontier_synthesis", next_frontier),
        ("row0_paid_anchor_reduction_gate", paid),
    ]:
        assert_no_semantics(name, data)

    if paid["summary"]["full_explicit_pair_label_model_promoted"]:
        raise RuntimeError("paid anchor gate promoted full explicit pair+label model")
    if paid["summary"]["controlled_paid_subset_promoted"]:
        raise RuntimeError("paid anchor gate promoted controlled paid subset")
    if next_frontier["decisions"]["overall"] != (
        "row0_advance_requires_primary_source_or_new_paid_anchor_source"
    ):
        raise RuntimeError("row0 next frontier decision changed")

    return {
        "schema": "row0_parallel_provenance_bridge_audit.v1",
        "classification": "row0_parallel_provenance_integrated_origin_still_exogenous",
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "final_row0_parallel_report": rel(FINAL_ROW0_REPORT),
            "row0_next_frontier_report": rel(NEXT_FRONTIER_REPORT),
            "deep_provenance": rel(DEEP_PROVENANCE),
            "surface_exception": rel(SURFACE_EXCEPTION),
            "next_frontier": rel(NEXT_FRONTIER),
            "paid_anchor": rel(PAID_ANCHOR),
        },
        "summary": {
            "parallel_verdict": "row0_origin_exogenous_under_current_evidence",
            "deep_provenance_decision": deep["decision"],
            "surface_mechanical_clue": surface["decision"],
            "next_frontier_decision": next_frontier["decisions"]["overall"],
            "paid_anchor_decision": paid["decision"],
            "lookup_baseline_bits": paid["baseline_lookup_bits"],
            "all_anchors_nominal_reduction_bits": paid["summary"][
                "all_anchors_nominal_reduction_bits"
            ],
            "all_anchors_pair_identity_only_net_bits": paid["summary"][
                "all_anchors_pair_identity_only_net_bits"
            ],
            "all_anchors_explicit_pair_label_net_bits": paid["summary"][
                "all_anchors_explicit_pair_label_net_bits"
            ],
            "rare_singletons_nominal_reduction_bits": paid["summary"][
                "rare_singletons_nominal_reduction_bits"
            ],
            "rare_singletons_explicit_pair_label_net_bits": paid["summary"][
                "rare_singletons_explicit_pair_label_net_bits"
            ],
            "diagonal_family_net_with_label_arrangement_bits": paid["summary"][
                "diagonal_family_net_with_label_arrangement_bits"
            ],
            "full_explicit_pair_label_model_promoted": paid["summary"][
                "full_explicit_pair_label_model_promoted"
            ],
            "controlled_paid_subset_promoted": paid["summary"][
                "controlled_paid_subset_promoted"
            ],
            "risk_register": deep["risk_register"],
            "frontier_order": next_frontier["frontier_order"],
        },
        "decision": {
            "row0_origin_status": "exogenous_under_current_evidence",
            "artifact_provenance_status": (
                "project_import_reconstruction_layers_traced_cipsoft_origin_untraced"
            ),
            "surface_exception_status": "promoted_mechanical_clue_not_label_origin",
            "paid_anchor_status": "explicit_paid_anchor_model_does_not_beat_lookup",
            "generation_explanation_status": (
                "book_formula_may_use_row0_as_substrate_but_does_not_derive_row0"
            ),
            "translation_or_plaintext_status": "NONE",
            "next_valid_unlocks": [
                "primary CipSoft/in-game row0 symbol table or exact crib",
                "fixed external source predicting row0 labels without search leakage",
                "paid holdout-capable row0 algorithm below lookup cost",
                "earlier authorial worksheet/source order artifact",
            ],
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / "47_row0_parallel_provenance_bridge_audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    lines = [
        "# Row0 Parallel Provenance Bridge Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "This bridge imports the independent `row0_origin_parallel_20260621`",
        "frontier into the prequential/row0 audit without changing book-generation",
        "bits. It separates local project provenance from a CipSoft/authorial",
        "origin claim and checks that paid worksheet anchors still do not promote.",
        "",
        "## Evidence",
        "",
        f"- Parallel verdict: `{s['parallel_verdict']}`.",
        f"- Deep provenance decision: `{s['deep_provenance_decision']}`.",
        f"- Surface exception clue: `{s['surface_mechanical_clue']}`.",
        f"- Paid anchor decision: `{s['paid_anchor_decision']}`.",
        f"- Lookup baseline: `{s['lookup_baseline_bits']:.3f}` bits.",
        f"- All worksheet anchors nominal reduction: `{s['all_anchors_nominal_reduction_bits']:.3f}` bits.",
        f"- All worksheet anchors explicit pair+label net: `{s['all_anchors_explicit_pair_label_net_bits']:.3f}` bits.",
        f"- Rare-singleton anchors nominal reduction: `{s['rare_singletons_nominal_reduction_bits']:.3f}` bits.",
        f"- Rare-singleton anchors explicit pair+label net: `{s['rare_singletons_explicit_pair_label_net_bits']:.3f}` bits.",
        f"- Diagonal-family narrow paid net: `{s['diagonal_family_net_with_label_arrangement_bits']:.3f}` bits.",
        f"- Full explicit pair+label model promoted: `{s['full_explicit_pair_label_model_promoted']}`.",
        f"- Controlled paid subset promoted: `{s['controlled_paid_subset_promoted']}`.",
        "",
        "## Provenance Risk Register",
        "",
    ]
    for row in s["risk_register"]:
        lines.append(
            f"- `{row['risk']}`: {row['assessment']} Mitigation: {row['mitigation']}"
        )
    lines.extend(
        [
            "",
            "## Next Frontier",
            "",
        ]
    )
    for index, item in enumerate(s["frontier_order"], start=1):
        lines.append(f"{index}. `{item}`")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- `row0` origin remains exogenous under current evidence.",
            "- The repository explains preservation, import, reconstruction, and audit layers, not CipSoft origin.",
            "- Ordered-surface asymmetry is a real mechanical clue but does not assign the pair labels.",
            "- Paid worksheet anchors do not beat lookup once anchor identity and label data are charged.",
            "- The book-generation formula may use row0 as a substrate but still does not derive row0.",
            "",
            "## Boundary",
            "",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
            "- No book-generation compression bound is changed.",
            "- No row0-origin formula is promoted.",
        ]
    )
    (TEST_RESULTS / "47_row0_parallel_provenance_bridge_audit.md").write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
