from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"
AUTHORIAL_RESULTS = ROOT / "analysis" / "authorial_mechanism_20260620" / "reports" / "test_results"

RECIPE_PRUNE = AUTHORIAL_RESULTS / "131_online_formula_recipe_prune_audit.json"
CANONICAL_COMPILE = AUTHORIAL_RESULTS / "132_canonical_online_recipe_formula_compile.json"
LITERAL_LENGTH_DERIVED = AUTHORIAL_RESULTS / "133_literal_length_derived_recipe_compile.json"
OP_TYPE_DERIVED = AUTHORIAL_RESULTS / "134_op_type_derived_recipe_compile.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def assert_boundary(name: str, data: dict[str, Any]) -> None:
    if data.get("translation_delta") != "NONE":
        raise RuntimeError(f"{name} changed translation boundary")
    boundary = data.get("boundary", {})
    if boundary.get("semantic_delta", "NONE") != "NONE":
        raise RuntimeError(f"{name} introduced semantic delta")
    if boundary.get("row0_origin_changed", False) is not False:
        raise RuntimeError(f"{name} changed row0 origin")
    if boundary.get("compression_bound_changed", False) is not False:
        raise RuntimeError(f"{name} changed compression bound")
    if boundary.get("authorial_intent_claim", False) is not False:
        raise RuntimeError(f"{name} introduced authorial intent claim")


def make_result() -> dict[str, Any]:
    recipe_prune = load_json(RECIPE_PRUNE)
    canonical = load_json(CANONICAL_COMPILE)
    literal_length = load_json(LITERAL_LENGTH_DERIVED)
    op_type = load_json(OP_TYPE_DERIVED)

    for name, data in [
        ("online_formula_recipe_prune", recipe_prune),
        ("canonical_online_recipe_formula_compile", canonical),
        ("literal_length_derived_recipe_compile", literal_length),
        ("op_type_derived_recipe_compile", op_type),
    ]:
        assert_boundary(name, data)

    active_bits = float(recipe_prune["active_compression_bound_bits"])
    bit_values = [
        float(recipe_prune["active_recomputed_bits"]),
        float(recipe_prune["stripped_recomputed_bits"]),
        float(canonical["active_bits"]),
        float(canonical["canonical_bits"]),
        float(literal_length["canonical_bits"]),
        float(literal_length["derived_bits"]),
        float(op_type["source_bits"]),
        float(op_type["derived_bits"]),
    ]
    if any(abs(bits - active_bits) > 1e-9 for bits in bit_values):
        raise RuntimeError("recipe representation compiles changed bit cost")

    roundtrip_values = [
        int(recipe_prune["active_roundtrip_ok"]),
        int(recipe_prune["stripped_roundtrip_ok"]),
        int(canonical["roundtrip_ok"]),
        int(literal_length["roundtrip_ok"]),
        int(op_type["roundtrip_ok"]),
    ]
    if any(value != 70 for value in roundtrip_values):
        raise RuntimeError("recipe representation compiles no longer roundtrip 70/70")

    removed_book_length = int(recipe_prune["removed_fields"]["book_length_fields"])
    removed_copy_target = int(recipe_prune["removed_fields"]["copy_target_start_fields"])
    removed_literal_length = int(literal_length["removed_fields"]["literal_length_fields"])
    removed_type_fields = int(op_type["removed_fields"]["type_fields"])
    removed_field_count = (
        removed_book_length
        + removed_copy_target
        + removed_literal_length
        + removed_type_fields
    )
    byte_savings = {
        "active_to_canonical": int(canonical["recipe_json_bytes"]["saved"]),
        "canonical_to_literal_length_derived": int(
            literal_length["recipe_json_bytes"]["saved"]
        ),
        "literal_length_to_type_derived": int(op_type["recipe_json_bytes"]["saved"]),
    }
    total_byte_saving = (
        int(recipe_prune["recipe_json_bytes"]["active"])
        - int(op_type["recipe_json_bytes"]["op_type_derived"])
    )

    remaining = recipe_prune["remaining_recipe_dependency_stats"]
    remaining_declared_dependencies = {
        "literal_text_fields": int(remaining["literal_text_fields"]),
        "literal_digits": int(remaining["literal_digits"]),
        "copy_source_fields": int(remaining["copy_source_fields"]),
        "copy_length_fields": int(remaining["copy_length_fields"]),
        "copied_digits": int(remaining["copied_digits"]),
    }
    dependencies_retained = (
        remaining_declared_dependencies["literal_text_fields"] == 87
        and remaining_declared_dependencies["literal_digits"] == 857
        and remaining_declared_dependencies["copy_source_fields"] == 261
        and remaining_declared_dependencies["copy_length_fields"] == 261
        and remaining_declared_dependencies["copied_digits"] == 10406
    )

    derivable_fields_removed = (
        removed_book_length == 70
        and removed_copy_target == 261
        and removed_literal_length == 87
        and removed_type_fields == 348
    )
    classification = (
        "recipe_representation_artifacts_removed_dependencies_retained"
        if derivable_fields_removed and dependencies_retained
        else "recipe_representation_dependency_boundary_unresolved"
    )

    return {
        "schema": "recipe_representation_dependency_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "online_formula_recipe_prune": rel(RECIPE_PRUNE),
            "canonical_online_recipe_formula_compile": rel(CANONICAL_COMPILE),
            "literal_length_derived_recipe_compile": rel(LITERAL_LENGTH_DERIVED),
            "op_type_derived_recipe_compile": rel(OP_TYPE_DERIVED),
        },
        "summary": {
            "active_bits": active_bits,
            "final_type_derived_bits": float(op_type["derived_bits"]),
            "score_delta_bits": float(op_type["score_delta_bits"]),
            "roundtrip_ok": 70,
            "removed_book_length_fields": removed_book_length,
            "removed_copy_target_start_fields": removed_copy_target,
            "removed_literal_length_fields": removed_literal_length,
            "removed_type_fields": removed_type_fields,
            "removed_independent_field_count": removed_field_count,
            "recipe_json_bytes_active": int(recipe_prune["recipe_json_bytes"]["active"]),
            "recipe_json_bytes_type_derived": int(
                op_type["recipe_json_bytes"]["op_type_derived"]
            ),
            "total_recipe_json_byte_saving": total_byte_saving,
            "stage_byte_savings": byte_savings,
            "remaining_declared_dependencies": remaining_declared_dependencies,
            "literal_digit_fraction": float(remaining["literal_digit_fraction"]),
            "copied_digit_fraction": float(remaining["copied_digit_fraction"]),
            "ambiguous_or_unclassifiable_ops": (
                len(op_type["removed_fields"]["ambiguous_ops"])
                + len(op_type["removed_fields"]["unclassifiable_ops"])
            ),
            "derivable_fields_removed": derivable_fields_removed,
            "dependencies_retained": dependencies_retained,
            "interpretation": (
                "Book length, copy target_start, literal length, and operation "
                "type are representation artifacts under the compact online "
                "recipe. Removing them preserves the 8343.062-bit score and "
                "70/70 roundtrip. Literal text, copy source, and copy length "
                "remain declared operation-level dependencies."
            ),
        },
        "decision": {
            "compression_bound_status": "unchanged",
            "recipe_representation_status": "derivable_fields_removed",
            "remaining_recipe_dependency_status": (
                "literal_text_copy_source_copy_length_retained"
            ),
            "generation_explanation_status": "recipe_description_simplified_not_final_method",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / "30_recipe_representation_dependency_gate.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    s = result["summary"]
    deps = s["remaining_declared_dependencies"]
    lines = [
        "# Recipe Representation Dependency Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "The online formula compiles remove several fields from the operation",
        "recipe without changing the score. This gate separates derivable",
        "representation artifacts from recipe dependencies that remain declared.",
        "",
        "## Summary",
        "",
        f"- Active/type-derived bits: `{s['active_bits']:.3f}` / `{s['final_type_derived_bits']:.3f}`.",
        f"- Score delta: `{s['score_delta_bits']:.12f}` bits.",
        f"- Roundtrip: `{s['roundtrip_ok']}/70`.",
        f"- Removed book `length` fields: `{s['removed_book_length_fields']}`.",
        f"- Removed copy `target_start` fields: `{s['removed_copy_target_start_fields']}`.",
        f"- Removed literal `length` fields: `{s['removed_literal_length_fields']}`.",
        f"- Removed op `type` fields: `{s['removed_type_fields']}`.",
        f"- Total removed independent fields: `{s['removed_independent_field_count']}`.",
        f"- Recipe JSON bytes: `{s['recipe_json_bytes_active']}` -> `{s['recipe_json_bytes_type_derived']}`.",
        f"- Total JSON byte saving: `{s['total_recipe_json_byte_saving']}`.",
        "",
        "## Remaining Declared Dependencies",
        "",
        f"- Literal text fields: `{deps['literal_text_fields']}` covering `{deps['literal_digits']}` digits.",
        f"- Copy source fields: `{deps['copy_source_fields']}` covering `{deps['copied_digits']}` copied digits.",
        f"- Copy length fields: `{deps['copy_length_fields']}` covering `{deps['copied_digits']}` copied digits.",
        f"- Literal/copied digit fractions: `{s['literal_digit_fraction']:.6f}` / `{s['copied_digit_fraction']:.6f}`.",
        "",
        "## Interpretation",
        "",
        "This is a mechanical-description simplification, not a compression-bound",
        "promotion. Book length is derived from operation lengths, copy target",
        "start from cumulative emitted position, literal length from `len(text)`,",
        "and operation type from field shape. The compact recipe still has to",
        "declare literal payload, copy source, and copy length.",
        "",
        "## Boundary",
        "",
        "- No compression bound is promoted.",
        "- Row0 origin remains unchanged and exogenous.",
        "- No plaintext, translation, semantic reading, or case reopening is introduced.",
    ]
    (TEST_RESULTS / "30_recipe_representation_dependency_gate.md").write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
