from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

COMPILE_129 = HERE / "scripts" / "129_online_deterministic_reparse_compile.py"
SOURCE_FORMULA = (
    HERE
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_splitonly_online_reparse_literal_length_derived_formula_469.json"
)
OUT_FORMULA = (
    HERE
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_splitonly_online_reparse_type_derived_formula_469.json"
)
SOURCE_TOTAL_KEY = (
    "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_splitonly_online_reparse_literal_length_derived_bits"
)
OUT_TOTAL_KEY = (
    "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_splitonly_online_reparse_type_derived_bits"
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def write_result(name: str, result: dict[str, Any], lines: list[str]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"{name}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / f"{name}.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def recipe_json_bytes(recipe: dict[str, Any]) -> int:
    return len(json.dumps(recipe, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def strip_op_types(formula: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    out = copy.deepcopy(formula)
    removed = {
        "type_fields": 0,
        "literal_ops": 0,
        "copy_ops": 0,
        "ambiguous_ops": [],
        "unclassifiable_ops": [],
    }
    for book in map(str, out["policy"]["book_order"]):
        for op_index, op in enumerate(out["book_recipes"][book]["ops"]):
            has_text = "text" in op
            has_source = "source_digit_pos" in op
            has_length = "length" in op
            if has_text and not has_source and not has_length:
                derived_type = "literal"
                removed["literal_ops"] += 1
            elif has_source and has_length and not has_text:
                derived_type = "copy"
                removed["copy_ops"] += 1
            elif has_text and (has_source or has_length):
                removed["ambiguous_ops"].append({"book": book, "op_index": op_index, "op": op})
                continue
            else:
                removed["unclassifiable_ops"].append({"book": book, "op_index": op_index, "op": op})
                continue

            declared_type = op.get("type")
            if declared_type is not None:
                removed["type_fields"] += 1
                if declared_type != derived_type:
                    removed["ambiguous_ops"].append(
                        {
                            "book": book,
                            "op_index": op_index,
                            "declared_type": declared_type,
                            "derived_type": derived_type,
                        }
                    )
                del op["type"]
    return out, removed


def normalize_ops(formula: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(formula)
    for book in map(str, out["policy"]["book_order"]):
        for op in out["book_recipes"][book]["ops"]:
            has_text = "text" in op
            has_source = "source_digit_pos" in op
            has_length = "length" in op
            if has_text and not has_source and not has_length:
                op["type"] = "literal"
                op["length"] = len(op["text"])
            elif has_source and has_length and not has_text:
                op["type"] = "copy"
            else:
                raise RuntimeError({"type": "cannot_normalize_op", "book": book, "op": op})
    return out


def assert_type_derived(formula: dict[str, Any]) -> dict[str, int]:
    counts = {
        "type_fields": 0,
        "literal_shape_ops": 0,
        "copy_shape_ops": 0,
        "ambiguous_ops": 0,
    }
    for book in map(str, formula["policy"]["book_order"]):
        recipe = formula["book_recipes"][book]
        if "length" in recipe:
            raise RuntimeError({"type": "book_length_field_retained", "book": book})
        for op in recipe["ops"]:
            counts["type_fields"] += "type" in op
            has_text = "text" in op
            has_source = "source_digit_pos" in op
            has_length = "length" in op
            if has_text and not has_source and not has_length:
                counts["literal_shape_ops"] += 1
            elif has_source and has_length and not has_text:
                counts["copy_shape_ops"] += 1
            else:
                counts["ambiguous_ops"] += 1
    if counts["type_fields"] or counts["ambiguous_ops"]:
        raise RuntimeError({"type": "type_derivation_failed", "counts": counts})
    return counts


def main() -> None:
    compile129 = load_module("online_reparse_compile_129", COMPILE_129)
    audit126 = compile129.load_audit_126()
    frontier = load_module("frontier", audit126.FRONTIER)
    midpoint = load_module("midpoint", audit126.MIDPOINT)
    copy_module = load_module("copy_context", audit126.COPY_CONTEXT)
    item_module = load_module("item_context", audit126.ITEM_CONTEXT)

    source = load_json(SOURCE_FORMULA)
    books = {str(key): value for key, value in load_json(audit126.BOOKS_DIGITS).items()}
    source_bits = float(source["mdl_estimate_rough"][SOURCE_TOTAL_KEY])
    source_recipe_bytes = recipe_json_bytes(source["book_recipes"])

    derived, removed = strip_op_types(source)
    if removed["ambiguous_ops"] or removed["unclassifiable_ops"]:
        raise RuntimeError(removed)
    type_counts = assert_type_derived(derived)
    normalized = normalize_ops(derived)
    score = compile129.score_splitonly_formula(
        formula=normalized,
        books=books,
        audit126=audit126,
        frontier=frontier,
        midpoint=midpoint,
        copy_module=copy_module,
        item_module=item_module,
    )
    if score["validation"]["errors"]:
        raise RuntimeError(score["validation"])
    if abs(float(score["total_bits"]) - source_bits) > 1e-9:
        raise RuntimeError({"source_bits": source_bits, "derived_bits": score["total_bits"]})

    derived_recipe_bytes = recipe_json_bytes(derived["book_recipes"])
    out = copy.deepcopy(derived)
    out["schema"] = "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_splitonly_online_reparse_type_derived_formula.v1"
    out["classification"] = "op_type_derived_canonical_online_recipe"
    out["source_formula"] = rel(SOURCE_FORMULA)
    out["translation_delta"] = "NONE"
    out["mdl_estimate_rough"] = {
        **out["mdl_estimate_rough"],
        OUT_TOTAL_KEY: score["total_bits"],
        f"previous_{SOURCE_TOTAL_KEY}": source_bits,
        "op_type_derived_recipe_json_saved_bytes": source_recipe_bytes - derived_recipe_bytes,
        "op_type_derived_removed_type_fields": removed["type_fields"],
    }
    out["policy"] = {
        **out["policy"],
        "recipe_representation": {
            **out["policy"].get("recipe_representation", {}),
            "family": "canonical_ops_with_derived_type_and_literal_lengths",
            "operation_type": "derived from op field shape: text => literal, source_digit_pos+length => copy",
            "remaining_declared_dependencies": [
                "literal text payload",
                "copy source_digit_pos",
                "copy length",
            ],
        },
    }
    out["validation"] = {
        **out["validation"],
        "op_type_derived_roundtrip_audit": score["validation"],
        "op_type_derived_field_counts": type_counts,
        "op_type_derived_removed_fields": removed,
    }
    out["boundary"] = {
        **out["boundary"],
        "translation_delta": "NONE",
        "row0_origin_changed": False,
        "semantic_delta": "NONE",
        "authorial_intent_claim": False,
        "compression_bound_changed": False,
        "representation_simplified": True,
    }
    OUT_FORMULA.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result = {
        "schema": "op_type_derived_recipe_compile.v1",
        "test": "134_op_type_derived_recipe_compile",
        "classification": "op_type_derived_canonical_online_recipe",
        "translation_delta": "NONE",
        "source_formula": rel(SOURCE_FORMULA),
        "output_formula": rel(OUT_FORMULA),
        "source_bits": source_bits,
        "derived_bits": score["total_bits"],
        "score_delta_bits": score["total_bits"] - source_bits,
        "roundtrip_ok": score["validation"]["books_roundtrip_ok"],
        "removed_fields": removed,
        "type_field_counts": type_counts,
        "recipe_json_bytes": {
            "source": source_recipe_bytes,
            "op_type_derived": derived_recipe_bytes,
            "saved": source_recipe_bytes - derived_recipe_bytes,
        },
        "normalization_rule": "For validation only, op type is restored from field shape and literal length from len(text).",
        "boundary": {
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "semantic_delta": "NONE",
            "authorial_intent_claim": False,
        },
    }

    lines = [
        "# 134. Op-Type-Derived Recipe Compile",
        "",
        "Classification: `op_type_derived_canonical_online_recipe`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "The literal-length-derived formula still carried explicit operation",
        "`type` fields. This compile tests whether operation type is derivable",
        "from each op's field shape: `text` means literal, while",
        "`source_digit_pos` plus `length` means copy.",
        "",
        "## Result",
        "",
        f"- Source bits: `{source_bits:.3f}`",
        f"- Type-derived bits: `{score['total_bits']:.3f}`",
        f"- Score delta: `{score['total_bits'] - source_bits:+.12f}`",
        f"- Roundtrip: `{score['validation']['books_roundtrip_ok']}/70`",
        f"- Removed `type` fields: `{removed['type_fields']}`",
        f"- Literal-shaped ops: `{type_counts['literal_shape_ops']}`",
        f"- Copy-shaped ops: `{type_counts['copy_shape_ops']}`",
        f"- Additional recipe JSON byte reduction: `{source_recipe_bytes - derived_recipe_bytes}`",
        "",
        "## Promoted Formula",
        "",
        f"- [`{OUT_FORMULA.name}`](../../{OUT_FORMULA.name})",
        "",
        "## Interpretation",
        "",
        "Operation type is not an independent recipe dependency in the compact",
        "formula. After this compile, the remaining operation-level declared",
        "dependencies are literal payload text, copy source, and copy length.",
        "",
        "## Boundary",
        "",
        "- No plaintext or translation is introduced.",
        "- Row0/table origin is unchanged.",
        "- The compression bound is unchanged.",
    ]
    write_result("134_op_type_derived_recipe_compile", result, lines)


if __name__ == "__main__":
    main()
