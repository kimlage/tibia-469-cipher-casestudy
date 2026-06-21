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
PRUNE_REPORT = HERE / "reports" / "test_results" / "131_online_formula_recipe_prune_audit.md"
CANONICAL_FORMULA = (
    HERE
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_splitonly_online_reparse_canonical_formula_469.json"
)
OUT_FORMULA = (
    HERE
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_splitonly_online_reparse_literal_length_derived_formula_469.json"
)
CANONICAL_TOTAL_KEY = (
    "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_splitonly_online_reparse_canonical_bits"
)
OUT_TOTAL_KEY = (
    "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_splitonly_online_reparse_literal_length_derived_bits"
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


def strip_literal_lengths(formula: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    out = copy.deepcopy(formula)
    removed = {
        "literal_length_fields": 0,
        "literal_length_mismatches": [],
        "copy_length_fields_retained": 0,
        "copy_target_start_fields": 0,
        "book_length_fields": 0,
    }
    for book in map(str, out["policy"]["book_order"]):
        recipe = out["book_recipes"][book]
        if "length" in recipe:
            removed["book_length_fields"] += 1
        for op_index, op in enumerate(recipe["ops"]):
            if op["type"] == "literal":
                if "length" in op:
                    removed["literal_length_fields"] += 1
                    if len(op["text"]) != int(op["length"]):
                        removed["literal_length_mismatches"].append(
                            {
                                "book": book,
                                "op_index": op_index,
                                "text_length": len(op["text"]),
                                "declared_length": int(op["length"]),
                            }
                        )
                    del op["length"]
            elif op["type"] == "copy":
                if "length" in op:
                    removed["copy_length_fields_retained"] += 1
                if "target_start" in op:
                    removed["copy_target_start_fields"] += 1
            else:
                raise ValueError(op)
    return out, removed


def normalize_literal_lengths(formula: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(formula)
    for book in map(str, out["policy"]["book_order"]):
        for op in out["book_recipes"][book]["ops"]:
            if op["type"] == "literal" and "length" not in op:
                op["length"] = len(op["text"])
    return out


def assert_literal_length_derived(formula: dict[str, Any]) -> dict[str, int]:
    counts = {
        "literal_length_fields": 0,
        "literal_ops": 0,
        "copy_length_fields": 0,
        "copy_ops": 0,
        "copy_target_start_fields": 0,
        "book_length_fields": 0,
    }
    for book in map(str, formula["policy"]["book_order"]):
        recipe = formula["book_recipes"][book]
        if "length" in recipe:
            counts["book_length_fields"] += 1
        for op in recipe["ops"]:
            if op["type"] == "literal":
                counts["literal_ops"] += 1
                if "length" in op:
                    counts["literal_length_fields"] += 1
            elif op["type"] == "copy":
                counts["copy_ops"] += 1
                if "length" in op:
                    counts["copy_length_fields"] += 1
                if "target_start" in op:
                    counts["copy_target_start_fields"] += 1
            else:
                raise ValueError(op)
    if counts["literal_length_fields"] or counts["book_length_fields"] or counts["copy_target_start_fields"]:
        raise RuntimeError({"type": "nonderived_recipe_fields", "counts": counts})
    return counts


def main() -> None:
    compile129 = load_module("online_reparse_compile_129", COMPILE_129)
    audit126 = compile129.load_audit_126()
    frontier = load_module("frontier", audit126.FRONTIER)
    midpoint = load_module("midpoint", audit126.MIDPOINT)
    copy_module = load_module("copy_context", audit126.COPY_CONTEXT)
    item_module = load_module("item_context", audit126.ITEM_CONTEXT)

    canonical = load_json(CANONICAL_FORMULA)
    books = {str(key): value for key, value in load_json(audit126.BOOKS_DIGITS).items()}
    canonical_bits = float(canonical["mdl_estimate_rough"][CANONICAL_TOTAL_KEY])
    canonical_recipe_bytes = recipe_json_bytes(canonical["book_recipes"])

    derived, removed = strip_literal_lengths(canonical)
    if removed["literal_length_mismatches"]:
        raise RuntimeError(removed)
    derived_counts = assert_literal_length_derived(derived)
    normalized = normalize_literal_lengths(derived)
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
    if abs(float(score["total_bits"]) - canonical_bits) > 1e-9:
        raise RuntimeError({"canonical_bits": canonical_bits, "derived_bits": score["total_bits"]})

    derived_recipe_bytes = recipe_json_bytes(derived["book_recipes"])
    out = copy.deepcopy(derived)
    out["schema"] = "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_splitonly_online_reparse_literal_length_derived_formula.v1"
    out["classification"] = "literal_length_derived_canonical_online_recipe"
    out["source_formula"] = rel(CANONICAL_FORMULA)
    out["source_audit"] = rel(PRUNE_REPORT)
    out["translation_delta"] = "NONE"
    out["mdl_estimate_rough"] = {
        **out["mdl_estimate_rough"],
        OUT_TOTAL_KEY: score["total_bits"],
        f"previous_{CANONICAL_TOTAL_KEY}": canonical_bits,
        "literal_length_derived_recipe_json_saved_bytes": canonical_recipe_bytes - derived_recipe_bytes,
        "literal_length_derived_removed_literal_length_fields": removed["literal_length_fields"],
    }
    out["policy"] = {
        **out["policy"],
        "recipe_representation": {
            **out["policy"].get("recipe_representation", {}),
            "family": "canonical_ops_with_derived_literal_lengths",
            "literal_length": "derived from literal text length",
            "remaining_declared_dependencies": [
                "operation type sequence",
                "literal text payload",
                "copy source_digit_pos",
                "copy length",
            ],
        },
    }
    out["validation"] = {
        **out["validation"],
        "literal_length_derived_roundtrip_audit": score["validation"],
        "literal_length_derived_field_counts": derived_counts,
        "literal_length_derived_removed_fields": removed,
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
        "schema": "literal_length_derived_recipe_compile.v1",
        "test": "133_literal_length_derived_recipe_compile",
        "classification": "literal_length_derived_canonical_online_recipe",
        "translation_delta": "NONE",
        "source_formula": rel(CANONICAL_FORMULA),
        "output_formula": rel(OUT_FORMULA),
        "canonical_bits": canonical_bits,
        "derived_bits": score["total_bits"],
        "score_delta_bits": score["total_bits"] - canonical_bits,
        "roundtrip_ok": score["validation"]["books_roundtrip_ok"],
        "removed_fields": removed,
        "derived_field_counts": derived_counts,
        "recipe_json_bytes": {
            "canonical": canonical_recipe_bytes,
            "literal_length_derived": derived_recipe_bytes,
            "saved": canonical_recipe_bytes - derived_recipe_bytes,
        },
        "normalization_rule": "For validation only, literal op length is restored as len(op['text']).",
        "boundary": {
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "semantic_delta": "NONE",
            "authorial_intent_claim": False,
        },
    }

    lines = [
        "# 133. Literal-Length-Derived Recipe Compile",
        "",
        "Classification: `literal_length_derived_canonical_online_recipe`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "The canonical online formula still carried `length` on literal operations,",
        "even though that value is derivable from the literal text payload. This",
        "compile materializes a stricter recipe representation where literal",
        "length is restored only during validation as `len(text)`.",
        "",
        "## Result",
        "",
        f"- Canonical bits: `{canonical_bits:.3f}`",
        f"- Literal-length-derived bits: `{score['total_bits']:.3f}`",
        f"- Score delta: `{score['total_bits'] - canonical_bits:+.12f}`",
        f"- Roundtrip: `{score['validation']['books_roundtrip_ok']}/70`",
        f"- Removed literal `length` fields: `{removed['literal_length_fields']}`",
        f"- Copy `length` fields retained: `{removed['copy_length_fields_retained']}`",
        f"- Additional recipe JSON byte reduction: `{canonical_recipe_bytes - derived_recipe_bytes}`",
        "",
        "## Promoted Formula",
        "",
        f"- [`{OUT_FORMULA.name}`](../../{OUT_FORMULA.name})",
        "",
        "## Interpretation",
        "",
        "Literal run length is not an independent recipe dependency when the",
        "literal payload text is already declared. Copy length remains a real",
        "declared dependency because copied text is not stored in the operation.",
        "",
        "## Boundary",
        "",
        "- No plaintext or translation is introduced.",
        "- Row0/table origin is unchanged.",
        "- The compression bound is unchanged.",
    ]
    write_result("133_literal_length_derived_recipe_compile", result, lines)


if __name__ == "__main__":
    main()
