from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"
AUTHORIAL_RESULTS = ROOT / "analysis" / "authorial_mechanism_20260620" / "reports" / "test_results"

COMPONENT_ABLATION = AUTHORIAL_RESULTS / "121_prequential_component_ablation_audit.json"
SPLIT_ONLY_COMPILE = AUTHORIAL_RESULTS / "123_item_type_split_only_formula_compile.json"
ALPHA_RESWEEP = AUTHORIAL_RESULTS / "124_item_type_split_only_alpha_resweep.json"
OP_TYPE_DERIVED = AUTHORIAL_RESULTS / "134_op_type_derived_recipe_compile.json"
ACTIVE_PROFILE = AUTHORIAL_RESULTS / "145_current_active_prequential_profile_audit.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def assert_boundary(name: str, data: dict[str, Any], *, allow_bound_change: bool = False) -> None:
    if data.get("translation_delta") != "NONE":
        raise RuntimeError(f"{name} changed translation boundary")
    if data.get("case_reopened", False) is not False:
        raise RuntimeError(f"{name} reopened case")
    if data.get("plaintext_claim", False) is not False:
        raise RuntimeError(f"{name} introduced plaintext")
    boundary = data.get("boundary", {})
    if boundary.get("semantic_delta", "NONE") != "NONE":
        raise RuntimeError(f"{name} introduced semantic delta")
    if boundary.get("row0_origin_changed", False) is not False:
        raise RuntimeError(f"{name} changed row0 origin")
    if (
        boundary.get("compression_bound_changed", False) is not False
        and not allow_bound_change
    ):
        raise RuntimeError(f"{name} changed compression bound")
    if boundary.get("authorial_intent_claim", False) is not False:
        raise RuntimeError(f"{name} introduced authorial intent claim")


def make_result() -> dict[str, Any]:
    ablation = load_json(COMPONENT_ABLATION)
    split_only = load_json(SPLIT_ONLY_COMPILE)
    alpha = load_json(ALPHA_RESWEEP)
    op_type = load_json(OP_TYPE_DERIVED)
    active = load_json(ACTIVE_PROFILE)

    for name, data in [
        ("prequential_component_ablation", ablation),
        ("item_type_split_only_formula_compile", split_only),
        ("item_type_split_only_alpha_resweep", alpha),
        ("op_type_derived_recipe_compile", op_type),
        ("current_active_prequential_profile", active),
    ]:
        assert_boundary(name, data)

    item_stats = split_only["item_stats"]
    forced_total = (
        int(item_stats["forced_literal_to_copy"])
        + int(item_stats["forced_remaining_short_to_literal"])
    )
    split_only_promoted = (
        split_only["classification"] == "controlled_item_type_split_only_formula_improvement"
        and bool(split_only["promoted_under_same_declaration_charge"])
        and bool(split_only["promoted_even_with_one_extra_declaration_bit"])
        and float(split_only["candidate_gain_bits"]) > 0
        and int(split_only["validation"]["books_roundtrip_ok"]) == 70
        and not item_stats["forced_rule_violations"]
    )
    alpha_retained = (
        alpha["classification"] == "item_type_split_only_alpha_resweep_retains_current"
        and int(alpha["current_alpha"]) == int(alpha["best_model"]["alpha"]) == 2
        and float(alpha["best_model"]["delta_vs_current_bits"]) == 0.0
    )
    op_type_derived = (
        op_type["classification"] == "op_type_derived_canonical_online_recipe"
        and int(op_type["removed_fields"]["type_fields"]) == 348
        and int(op_type["roundtrip_ok"]) == 70
        and float(op_type["score_delta_bits"]) == 0.0
        and not op_type["removed_fields"]["ambiguous_ops"]
        and not op_type["removed_fields"]["unclassifiable_ops"]
    )
    profile_component_present = (
        "item_type split-only forced-rule context" in active["scope"]["components_tested"]
        and int(active["full_corpus_accounting"]["event_counts"]["item_type"]) == 265
        and active["decision"]["generation_explanation_strengthened"] is True
    )
    classification = (
        "item_type_split_only_retained_op_type_shape_derived"
        if split_only_promoted
        and alpha_retained
        and op_type_derived
        and profile_component_present
        else "item_type_op_shape_boundary_unresolved"
    )

    return {
        "schema": "item_type_op_shape_boundary_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "prequential_component_ablation": rel(COMPONENT_ABLATION),
            "item_type_split_only_formula_compile": rel(SPLIT_ONLY_COMPILE),
            "item_type_split_only_alpha_resweep": rel(ALPHA_RESWEEP),
            "op_type_derived_recipe_compile": rel(OP_TYPE_DERIVED),
            "current_active_prequential_profile": rel(ACTIVE_PROFILE),
        },
        "summary": {
            "ablation_simpler_components": ablation["summary"][
                "components_where_simpler_variant_beats_active"
            ],
            "active_compression_bound_bits_before_split_only": split_only[
                "active_compression_bound_bits"
            ],
            "split_only_candidate_total_bits": split_only["candidate_total_bits"],
            "split_only_gain_bits": split_only["candidate_gain_bits"],
            "split_only_conservative_gain_bits": split_only[
                "conservative_candidate_gain_bits"
            ],
            "active_item_type_bits": split_only["active_item_type_bits"],
            "split_only_item_type_bits": split_only["split_only_item_type_bits"],
            "coded_item_type_items": item_stats["coded_items"],
            "forced_literal_to_copy": item_stats["forced_literal_to_copy"],
            "forced_remaining_short_to_literal": item_stats[
                "forced_remaining_short_to_literal"
            ],
            "forced_item_type_items": forced_total,
            "forced_rule_violations": item_stats["forced_rule_violations"],
            "current_alpha": alpha["current_alpha"],
            "best_alpha": alpha["best_model"]["alpha"],
            "nearest_alpha1_delta_bits": alpha["rows"][1]["delta_vs_current_bits"],
            "op_type_fields_removed": op_type["removed_fields"]["type_fields"],
            "literal_shape_ops": op_type["type_field_counts"]["literal_shape_ops"],
            "copy_shape_ops": op_type["type_field_counts"]["copy_shape_ops"],
            "ambiguous_shape_ops": op_type["type_field_counts"]["ambiguous_ops"],
            "op_type_score_delta_bits": op_type["score_delta_bits"],
            "op_type_roundtrip_ok": op_type["roundtrip_ok"],
            "active_profile_item_type_events": active["full_corpus_accounting"][
                "event_counts"
            ]["item_type"],
            "active_profile_item_type_stream_bits": active["full_corpus_accounting"][
                "component_stream_bits"
            ]["item_type_stream_bits"],
            "split_only_promoted": split_only_promoted,
            "alpha_retained": alpha_retained,
            "op_type_derived": op_type_derived,
            "profile_component_present": profile_component_present,
            "interpretation": (
                "Item type is retained as a split-only forced-rule stream in the "
                "generation profile, but explicit operation type is not a compact "
                "recipe dependency once field shape distinguishes literal from copy."
            ),
        },
        "decision": {
            "compression_bound_status": "split_only_already_promoted_upstream_unchanged_here",
            "item_type_model_status": "split_only_forced_rule_context_retained",
            "item_type_alpha_status": "alpha_2_retained",
            "op_type_recipe_field_status": "derived_from_field_shape",
            "generation_explanation_status": "item_type_boundary_sharpened",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / "33_item_type_op_shape_boundary_gate.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    s = result["summary"]
    lines = [
        "# Item Type Op Shape Boundary Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Item type appears in two places: as a learned literal/copy operation",
        "sequence in the generation ledger, and as an explicit `type` field in",
        "some recipe JSON projections. This gate separates those two meanings.",
        "",
        "## Summary",
        "",
        f"- Split-only formula bits: `{s['active_compression_bound_bits_before_split_only']:.3f}` -> `{s['split_only_candidate_total_bits']:.3f}`.",
        f"- Split-only gain: `{s['split_only_gain_bits']:.3f}` bits.",
        f"- Conservative split-only gain: `{s['split_only_conservative_gain_bits']:.3f}` bits.",
        f"- Item-type stream bits: `{s['active_item_type_bits']:.3f}` -> `{s['split_only_item_type_bits']:.3f}`.",
        f"- Coded item-type items: `{s['coded_item_type_items']}`.",
        f"- Forced item-type items: `{s['forced_item_type_items']}` (`literal->copy {s['forced_literal_to_copy']}`, `short suffix {s['forced_remaining_short_to_literal']}`).",
        f"- Current/best alpha: `{s['current_alpha']}` / `{s['best_alpha']}`.",
        f"- Nearest alpha-1 delta: `{s['nearest_alpha1_delta_bits']:.3f}` bits.",
        f"- Removed explicit op `type` fields: `{s['op_type_fields_removed']}`.",
        f"- Literal/copy-shaped ops: `{s['literal_shape_ops']}` / `{s['copy_shape_ops']}`.",
        f"- Ambiguous shape ops: `{s['ambiguous_shape_ops']}`.",
        f"- Op-type derivation score delta: `{s['op_type_score_delta_bits']:.12f}` bits.",
        "",
        "## Interpretation",
        "",
        "The split-only item-type model is retained as a real mechanical component:",
        "it improved the old bound and alpha `2` remains best. That does not mean",
        "the compact recipe must carry explicit op `type` fields. Once operation",
        "shape is normalized, `text` means literal and `source_digit_pos` plus",
        "`length` means copy; the explicit `type` field is derivable with zero",
        "score delta and `70/70` roundtrip.",
        "",
        "## Boundary",
        "",
        "- No new compression bound is promoted by this gate.",
        "- Item-type sequence modeling and recipe `type` fields are separate layers.",
        "- Row0 origin remains unchanged and exogenous.",
        "- No plaintext, translation, semantic reading, or case reopening is introduced.",
    ]
    (TEST_RESULTS / "33_item_type_op_shape_boundary_gate.md").write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
