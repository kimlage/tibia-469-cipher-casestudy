from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"
AUTHORIAL_RESULTS = ROOT / "analysis" / "authorial_mechanism_20260620" / "reports" / "test_results"

COPY_LENGTH_DEFAULT = AUTHORIAL_RESULTS / "136_copy_length_default_decodability_audit.json"
COPY_LENGTH_MIDPOINT = AUTHORIAL_RESULTS / "148_copy_length_midpoint_context_audit.json"
MIDPOINT_GATE = TEST_RESULTS / "27_copy_length_midpoint_context_gate.json"
RECIPE_REPRESENTATION_GATE = TEST_RESULTS / "30_recipe_representation_dependency_gate.json"


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
    default = load_json(COPY_LENGTH_DEFAULT)
    midpoint = load_json(COPY_LENGTH_MIDPOINT)
    midpoint_gate = load_json(MIDPOINT_GATE)
    recipe_gate = load_json(RECIPE_REPRESENTATION_GATE)

    assert_boundary("copy_length_default_decodability", default, allow_bound_change=True)
    for name, data in [
        ("copy_length_midpoint_context", midpoint),
        ("copy_length_midpoint_context_gate", midpoint_gate),
        ("recipe_representation_dependency_gate", recipe_gate),
    ]:
        assert_boundary(name, data)

    copy_items = int(default["copy_items"])
    encoder_only = default["encoder_only_rule"]
    best_decodable = default["best_decodable_rule"]
    model = default["default_exception_model"]
    midpoint_summary = midpoint_gate["summary"]
    remaining = recipe_gate["summary"]["remaining_declared_dependencies"]

    encoder_rule_rejected = (
        int(encoder_only["match_count"]) == 238
        and int(encoder_only["exception_count"]) == 23
        and encoder_only["decodable"] is False
    )
    decodable_rule_retained = (
        best_decodable["decodable"] is True
        and best_decodable["default_key"] == "decoder_max_possible_default"
        and int(model["default_count"]) == 60
        and int(model["exception_count"]) == 201
        and default["boundary"]["copy_length_dependency_remodeled"] is True
        and default["boundary"]["copy_length_dependency_removed"] is False
    )
    midpoint_retained = (
        midpoint_gate["classification"]
        == "copy_length_midpoint_context_generalizes_searched_cutoff_rejected"
        and midpoint_summary["midpoint_supported"] is True
        and midpoint_summary["searched_boundary_promoted"] is False
    )
    dependency_retained = (
        int(remaining["copy_length_fields"]) == copy_items
        and int(remaining["copied_digits"]) == 10406
    )
    classification = (
        "copy_length_partly_decodable_context_supported_dependency_retained"
        if encoder_rule_rejected
        and decodable_rule_retained
        and midpoint_retained
        and dependency_retained
        else "copy_length_derivation_boundary_unresolved"
    )

    return {
        "schema": "copy_length_derivation_boundary_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "copy_length_default_decodability": rel(COPY_LENGTH_DEFAULT),
            "copy_length_midpoint_context": rel(COPY_LENGTH_MIDPOINT),
            "copy_length_midpoint_context_gate": rel(MIDPOINT_GATE),
            "recipe_representation_dependency_gate": rel(RECIPE_REPRESENTATION_GATE),
        },
        "summary": {
            "copy_items": copy_items,
            "active_copy_length_bits": default["active_copy_length_bits"],
            "candidate_copy_length_bits": default["candidate_copy_length_bits"],
            "candidate_gain_bits": default["candidate_gain_bits"],
            "conservative_extra_declaration_bits": default[
                "conservative_extra_declaration_bits"
            ],
            "encoder_target_max_match_count": encoder_only["match_count"],
            "encoder_target_max_exception_count": encoder_only["exception_count"],
            "encoder_target_max_coverage_fraction": encoder_only["coverage_fraction"],
            "encoder_target_max_decodable": encoder_only["decodable"],
            "decoder_max_possible_default_count": model["default_count"],
            "decoder_max_possible_exception_count": model["exception_count"],
            "decoder_max_possible_coverage_fraction": best_decodable[
                "coverage_fraction"
            ],
            "decoder_default_exception_stream_bits": model["stream_bits"],
            "decoder_default_exception_flag_bits": model["flag_bits"],
            "decoder_exception_length_bits": model["exception_length_bits"],
            "decoder_exception_length_context": model["exception_length_context"],
            "midpoint_gain_vs_global_bits": midpoint_summary[
                "midpoint_gain_vs_global_bits"
            ],
            "midpoint_prefix_frozen_win_count": midpoint_summary[
                "prefix_frozen_midpoint_win_count"
            ],
            "midpoint_prefix_frozen_split_count": midpoint_summary[
                "prefix_frozen_split_count"
            ],
            "midpoint_permutation_p": midpoint_summary[
                "p_permuted_midpoint_gain_ge_observed"
            ],
            "best_cutoff_delta_vs_midpoint_bits": midpoint_summary[
                "best_cutoff_delta_vs_midpoint_bits"
            ],
            "copy_length_fields_retained_in_compact_recipe": remaining[
                "copy_length_fields"
            ],
            "copied_digits_covered": remaining["copied_digits"],
            "encoder_rule_rejected": encoder_rule_rejected,
            "decodable_rule_retained": decodable_rule_retained,
            "midpoint_retained": midpoint_retained,
            "dependency_retained": dependency_retained,
            "interpretation": (
                "Copy length has a useful decodable default/exception model and "
                "a supported midpoint context, but it is not derived. The strong "
                "target-max rule is encoder-only, and the compact recipe still "
                "declares one copy length per copy op."
            ),
        },
        "decision": {
            "compression_bound_status": "already_promoted_upstream_unchanged_here",
            "copy_length_encoder_rule_status": "target_max_encoder_only_rejected_as_decoder_rule",
            "copy_length_decodable_model_status": "decoder_max_possible_default_exception_retained",
            "copy_length_context_status": "midpoint_context_retained",
            "copy_length_dependency_status": "declared_copy_lengths_retained",
            "generation_explanation_status": "copy_length_boundary_sharpened",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / "32_copy_length_derivation_boundary_gate.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    s = result["summary"]
    lines = [
        "# Copy Length Derivation Boundary Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Copy length is one of the remaining declared recipe dependencies. This",
        "gate consolidates the default/exception compile, the midpoint context",
        "validation, and the compact recipe dependency ledger to decide whether",
        "copy length has become decoder-derived or remains declared.",
        "",
        "## Summary",
        "",
        f"- Copy items: `{s['copy_items']}`.",
        f"- Active/candidate copy-length bits: `{s['active_copy_length_bits']:.3f}` / `{s['candidate_copy_length_bits']:.3f}`.",
        f"- Candidate gain already promoted upstream: `{s['candidate_gain_bits']:.3f}` bits.",
        f"- Encoder target-max matches: `{s['encoder_target_max_match_count']}/{s['copy_items']}`.",
        f"- Encoder target-max decodable: `{s['encoder_target_max_decodable']}`.",
        f"- Decoder max-possible defaults/exceptions: `{s['decoder_max_possible_default_count']}` / `{s['decoder_max_possible_exception_count']}`.",
        f"- Decoder default/exception stream bits: `{s['decoder_default_exception_stream_bits']:.3f}`.",
        f"- Midpoint gain vs global: `{s['midpoint_gain_vs_global_bits']:.3f}` bits.",
        f"- Midpoint prefix-frozen wins: `{s['midpoint_prefix_frozen_win_count']}/{s['midpoint_prefix_frozen_split_count']}`.",
        f"- P(permuted midpoint gain >= observed): `{s['midpoint_permutation_p']:.4f}`.",
        f"- Best searched cutoff delta vs midpoint: `{s['best_cutoff_delta_vs_midpoint_bits']:.3f}` bits.",
        f"- Copy-length fields retained in compact recipe: `{s['copy_length_fields_retained_in_compact_recipe']}`.",
        f"- Copied digits covered: `{s['copied_digits_covered']}`.",
        "",
        "## Interpretation",
        "",
        "The copy-length model is improved but not eliminated. The high-coverage",
        "target-max rule matches most copies, but it is encoder-only because it",
        "depends on future target text. The decodable `decoder_max_possible`",
        "default plus adaptive exceptions is retained, and the natural midpoint",
        "context generalizes under prefix and permutation controls. The compact",
        "recipe still declares copy length for all copy ops.",
        "",
        "## Boundary",
        "",
        "- No new compression bound is promoted by this gate.",
        "- Copy length remains a declared dependency.",
        "- Row0 origin remains unchanged and exogenous.",
        "- No plaintext, translation, semantic reading, or case reopening is introduced.",
    ]
    (TEST_RESULTS / "32_copy_length_derivation_boundary_gate.md").write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
