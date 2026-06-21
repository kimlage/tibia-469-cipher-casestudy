from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

PRUNE_131 = HERE / "scripts" / "131_online_formula_recipe_prune_audit.py"
COMPILE_129 = HERE / "scripts" / "129_online_deterministic_reparse_compile.py"
ACTIVE_FORMULA = (
    HERE
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_splitonly_online_reparse_formula_469.json"
)
OUT_FORMULA = (
    HERE
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_splitonly_online_reparse_canonical_formula_469.json"
)
ACTIVE_TOTAL_KEY = (
    "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_splitonly_online_reparse_bits"
)
OUT_TOTAL_KEY = (
    "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_splitonly_online_reparse_canonical_bits"
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


def assert_canonical_recipe(formula: dict[str, Any]) -> dict[str, int]:
    counts = {
        "book_length_fields": 0,
        "copy_target_start_fields": 0,
        "literal_ops": 0,
        "copy_ops": 0,
    }
    for book in map(str, formula["policy"]["book_order"]):
        recipe = formula["book_recipes"][book]
        if "length" in recipe:
            counts["book_length_fields"] += 1
        for op in recipe["ops"]:
            if op["type"] == "literal":
                counts["literal_ops"] += 1
            elif op["type"] == "copy":
                counts["copy_ops"] += 1
                if "target_start" in op:
                    counts["copy_target_start_fields"] += 1
            else:
                raise ValueError(op)
    if counts["book_length_fields"] or counts["copy_target_start_fields"]:
        raise RuntimeError({"type": "noncanonical_recipe_fields", "counts": counts})
    return counts


def main() -> None:
    prune131 = load_module("recipe_prune_audit_131", PRUNE_131)
    compile129 = load_module("online_reparse_compile_129", COMPILE_129)
    audit126 = compile129.load_audit_126()
    frontier = load_module("frontier", audit126.FRONTIER)
    midpoint = load_module("midpoint", audit126.MIDPOINT)
    copy_module = load_module("copy_context", audit126.COPY_CONTEXT)
    item_module = load_module("item_context", audit126.ITEM_CONTEXT)

    active = load_json(ACTIVE_FORMULA)
    books = {str(key): value for key, value in load_json(audit126.BOOKS_DIGITS).items()}
    active_bits = float(active["mdl_estimate_rough"][ACTIVE_TOTAL_KEY])
    active_recipe_bytes = recipe_json_bytes(active["book_recipes"])

    canonical, removed = prune131.strip_recipe_fields(active, books)
    canonical_score = compile129.score_splitonly_formula(
        formula=canonical,
        books=books,
        audit126=audit126,
        frontier=frontier,
        midpoint=midpoint,
        copy_module=copy_module,
        item_module=item_module,
    )
    if canonical_score["validation"]["errors"]:
        raise RuntimeError(canonical_score["validation"])
    if abs(float(canonical_score["total_bits"]) - active_bits) > 1e-9:
        raise RuntimeError({"active_bits": active_bits, "canonical_bits": canonical_score["total_bits"]})
    if any(
        removed[key]
        for key in ("book_length_mismatches", "target_start_mismatches", "literal_length_mismatches")
    ):
        raise RuntimeError({"type": "derived_field_mismatch", "removed": removed})

    canonical_counts = assert_canonical_recipe(canonical)
    canonical_recipe_bytes = recipe_json_bytes(canonical["book_recipes"])
    out = copy.deepcopy(canonical)
    out["schema"] = "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_splitonly_online_reparse_canonical_formula.v1"
    out["classification"] = "canonical_online_recipe_representation"
    out["source_formula"] = rel(ACTIVE_FORMULA)
    out["source_audit"] = rel(PRUNE_131)
    out["translation_delta"] = "NONE"
    out["mdl_estimate_rough"] = {
        **out["mdl_estimate_rough"],
        OUT_TOTAL_KEY: canonical_score["total_bits"],
        f"previous_{ACTIVE_TOTAL_KEY}": active_bits,
        "canonical_recipe_json_saved_bytes": active_recipe_bytes - canonical_recipe_bytes,
        "canonical_recipe_removed_book_length_fields": removed["book_length_fields"],
        "canonical_recipe_removed_copy_target_start_fields": removed["copy_target_start_fields"],
    }
    out["policy"] = {
        **out["policy"],
        "recipe_representation": {
            "family": "canonical_ops_without_derivable_targets",
            "book_length": "derived from operation lengths",
            "copy_target_start": "derived from cumulative operation position within book",
            "remaining_declared_dependencies": [
                "operation type sequence",
                "literal text payload",
                "literal run length",
                "copy source_digit_pos",
                "copy length",
            ],
        },
    }
    out["validation"] = {
        **out["validation"],
        "canonical_recipe_roundtrip_audit": canonical_score["validation"],
        "canonical_recipe_field_counts": canonical_counts,
        "canonical_recipe_removed_fields": removed,
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
        "schema": "canonical_online_recipe_formula_compile.v1",
        "test": "132_canonical_online_recipe_formula_compile",
        "classification": "canonical_online_recipe_representation",
        "translation_delta": "NONE",
        "source_formula": rel(ACTIVE_FORMULA),
        "output_formula": rel(OUT_FORMULA),
        "active_bits": active_bits,
        "canonical_bits": canonical_score["total_bits"],
        "score_delta_bits": canonical_score["total_bits"] - active_bits,
        "roundtrip_ok": canonical_score["validation"]["books_roundtrip_ok"],
        "removed_fields": removed,
        "canonical_field_counts": canonical_counts,
        "recipe_json_bytes": {
            "active": active_recipe_bytes,
            "canonical": canonical_recipe_bytes,
            "saved": active_recipe_bytes - canonical_recipe_bytes,
        },
        "promotion_rule": (
            "Promote only as representation simplification if canonical recipe "
            "has no book length or copy target_start fields, preserves the active "
            "bit cost and 70/70 roundtrip, and keeps translation_delta NONE."
        ),
        "boundary": {
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "semantic_delta": "NONE",
            "authorial_intent_claim": False,
        },
    }

    lines = [
        "# 132. Canonical Online Recipe Formula Compile",
        "",
        "Classification: `canonical_online_recipe_representation`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Audit 131 proved that per-book `length` and copy `target_start` are",
        "derivable representation fields in the online reparse formula. This",
        "compile materializes the canonical formula projection without those",
        "fields.",
        "",
        "## Result",
        "",
        f"- Active bits: `{active_bits:.3f}`",
        f"- Canonical bits: `{canonical_score['total_bits']:.3f}`",
        f"- Score delta: `{canonical_score['total_bits'] - active_bits:+.12f}`",
        f"- Roundtrip: `{canonical_score['validation']['books_roundtrip_ok']}/70`",
        f"- Removed book `length` fields: `{removed['book_length_fields']}`",
        f"- Removed copy `target_start` fields: `{removed['copy_target_start_fields']}`",
        f"- Recipe JSON byte reduction: `{active_recipe_bytes - canonical_recipe_bytes}`",
        "",
        "## Promoted Formula",
        "",
        f"- [`{OUT_FORMULA.name}`](../../{OUT_FORMULA.name})",
        "",
        "## Interpretation",
        "",
        "This is a lossless mechanical representation improvement. The current",
        "`8343.062` bit bound is unchanged, but the committed formula no longer",
        "needs to carry fields that can be derived during decoding. Literal payload,",
        "copy source, and copy length remain declared recipe dependencies.",
        "",
        "## Boundary",
        "",
        "- No plaintext or translation is introduced.",
        "- Row0/table origin is unchanged.",
        "- The compression bound is not lowered by this compile.",
    ]
    write_result("132_canonical_online_recipe_formula_compile", result, lines)


if __name__ == "__main__":
    main()
