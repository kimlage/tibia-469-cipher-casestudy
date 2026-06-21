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
ACTIVE_FORMULA = (
    HERE
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_splitonly_online_reparse_formula_469.json"
)
ACTIVE_TOTAL_KEY = (
    "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_splitonly_online_reparse_bits"
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


def strip_recipe_fields(formula: dict[str, Any], books: dict[str, str]) -> tuple[dict[str, Any], dict[str, Any]]:
    out = copy.deepcopy(formula)
    removed = {
        "book_length_fields": 0,
        "copy_target_start_fields": 0,
        "book_length_mismatches": [],
        "target_start_mismatches": [],
        "literal_length_mismatches": [],
    }
    stripped_recipes: dict[str, dict[str, Any]] = {}
    for book in map(str, out["policy"]["book_order"]):
        recipe = out["book_recipes"][book]
        ops = recipe["ops"]
        reconstructed_length = sum(int(op["length"]) for op in ops)
        if "length" in recipe:
            removed["book_length_fields"] += 1
            if int(recipe["length"]) != reconstructed_length or reconstructed_length != len(books[book]):
                removed["book_length_mismatches"].append(
                    {
                        "book": book,
                        "declared_length": int(recipe["length"]),
                        "ops_length": reconstructed_length,
                        "book_digits_length": len(books[book]),
                    }
                )

        stripped_ops = []
        book_pos = 0
        for op_index, op in enumerate(ops):
            stripped_op = {key: value for key, value in op.items() if key != "target_start"}
            if op["type"] == "literal":
                if len(op["text"]) != int(op["length"]):
                    removed["literal_length_mismatches"].append(
                        {
                            "book": book,
                            "op_index": op_index,
                            "text_length": len(op["text"]),
                            "declared_length": int(op["length"]),
                        }
                    )
            elif op["type"] == "copy" and "target_start" in op:
                removed["copy_target_start_fields"] += 1
                if int(op["target_start"]) != book_pos:
                    removed["target_start_mismatches"].append(
                        {
                            "book": book,
                            "op_index": op_index,
                            "declared_target_start": int(op["target_start"]),
                            "derived_target_start": book_pos,
                        }
                    )
            stripped_ops.append(stripped_op)
            book_pos += int(op["length"])
        stripped_recipes[book] = {"ops": stripped_ops}

    out["book_recipes"] = stripped_recipes
    return out, removed


def collect_recipe_dependency_stats(formula: dict[str, Any]) -> dict[str, Any]:
    stats = {
        "books": 0,
        "ops": 0,
        "literal_ops": 0,
        "literal_digits": 0,
        "copy_ops": 0,
        "copied_digits": 0,
        "copy_source_fields": 0,
        "copy_length_fields": 0,
        "literal_text_fields": 0,
        "literal_length_fields": 0,
    }
    for book in map(str, formula["policy"]["book_order"]):
        stats["books"] += 1
        for op in formula["book_recipes"][book]["ops"]:
            stats["ops"] += 1
            if op["type"] == "literal":
                stats["literal_ops"] += 1
                stats["literal_digits"] += int(op["length"])
                stats["literal_text_fields"] += 1
                stats["literal_length_fields"] += 1
            elif op["type"] == "copy":
                stats["copy_ops"] += 1
                stats["copied_digits"] += int(op["length"])
                stats["copy_source_fields"] += 1
                stats["copy_length_fields"] += 1
            else:
                raise ValueError(op)
    stats["literal_digit_fraction"] = stats["literal_digits"] / max(1, stats["literal_digits"] + stats["copied_digits"])
    stats["copied_digit_fraction"] = stats["copied_digits"] / max(1, stats["literal_digits"] + stats["copied_digits"])
    return stats


def main() -> None:
    compile129 = load_module("online_reparse_compile_129", COMPILE_129)
    audit126 = compile129.load_audit_126()
    frontier = load_module("frontier", audit126.FRONTIER)
    midpoint = load_module("midpoint", audit126.MIDPOINT)
    copy_module = load_module("copy_context", audit126.COPY_CONTEXT)
    item_module = load_module("item_context", audit126.ITEM_CONTEXT)

    formula = load_json(ACTIVE_FORMULA)
    books = {str(key): value for key, value in load_json(audit126.BOOKS_DIGITS).items()}
    active_bits = float(formula["mdl_estimate_rough"][ACTIVE_TOTAL_KEY])
    active_score = compile129.score_splitonly_formula(
        formula=formula,
        books=books,
        audit126=audit126,
        frontier=frontier,
        midpoint=midpoint,
        copy_module=copy_module,
        item_module=item_module,
    )
    if active_score["validation"]["errors"]:
        raise RuntimeError(active_score["validation"])

    stripped_formula, removed = strip_recipe_fields(formula, books)
    stripped_score = compile129.score_splitonly_formula(
        formula=stripped_formula,
        books=books,
        audit126=audit126,
        frontier=frontier,
        midpoint=midpoint,
        copy_module=copy_module,
        item_module=item_module,
    )
    if stripped_score["validation"]["errors"]:
        raise RuntimeError(stripped_score["validation"])

    active_recipe_bytes = recipe_json_bytes(formula["book_recipes"])
    stripped_recipe_bytes = recipe_json_bytes(stripped_formula["book_recipes"])
    score_delta = float(stripped_score["total_bits"]) - float(active_score["total_bits"])
    same_score = abs(score_delta) < 1e-9
    no_mismatches = not any(
        removed[key]
        for key in ("book_length_mismatches", "target_start_mismatches", "literal_length_mismatches")
    )
    classification = (
        "lossless_recipe_representation_simplification"
        if same_score and no_mismatches
        else "recipe_representation_prune_blocked"
    )
    dependency_stats = collect_recipe_dependency_stats(stripped_formula)

    result = {
        "schema": "online_formula_recipe_prune_audit.v1",
        "test": "131_online_formula_recipe_prune_audit",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": rel(ACTIVE_FORMULA),
        "active_compression_bound_bits": active_bits,
        "active_recomputed_bits": active_score["total_bits"],
        "stripped_recomputed_bits": stripped_score["total_bits"],
        "score_delta_bits": score_delta,
        "active_roundtrip_ok": active_score["validation"]["books_roundtrip_ok"],
        "stripped_roundtrip_ok": stripped_score["validation"]["books_roundtrip_ok"],
        "removed_fields": removed,
        "recipe_json_bytes": {
            "active": active_recipe_bytes,
            "stripped_projection": stripped_recipe_bytes,
            "saved": active_recipe_bytes - stripped_recipe_bytes,
        },
        "remaining_recipe_dependency_stats": dependency_stats,
        "interpretation": {
            "target_start": "derivable from cumulative emitted length within each book",
            "book_length": "derivable from op lengths and checked against canonical book digit length",
            "not_removed": [
                "literal text payload",
                "literal run lengths",
                "copy source_digit_pos",
                "copy lengths",
                "item sequence implied by op type",
            ],
        },
        "boundary": {
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "semantic_delta": "NONE",
            "authorial_intent_claim": False,
            "active_formula_file_rewritten": False,
        },
    }

    lines = [
        "# 131. Online Formula Recipe Prune Audit",
        "",
        f"Classification: `{classification}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Audit 129 promoted an online reparse formula. This audit checks whether",
        "that formula's committed recipe still carries fields that are derivable",
        "from the recipe itself rather than required to generate the books.",
        "",
        "## Result",
        "",
        f"- Active recomputed bound: `{active_score['total_bits']:.3f}` bits",
        f"- Stripped projection bound: `{stripped_score['total_bits']:.3f}` bits",
        f"- Score delta: `{score_delta:+.12f}` bits",
        f"- Active roundtrip: `{active_score['validation']['books_roundtrip_ok']}/70`",
        f"- Stripped roundtrip: `{stripped_score['validation']['books_roundtrip_ok']}/70`",
        f"- Removed book `length` fields: `{removed['book_length_fields']}`",
        f"- Removed copy `target_start` fields: `{removed['copy_target_start_fields']}`",
        f"- Recipe JSON byte reduction: `{active_recipe_bytes - stripped_recipe_bytes}` bytes",
        "",
        "## Remaining Declared Recipe Dependency",
        "",
        "| Field family | Count | Digits covered |",
        "|---|---:|---:|",
        f"| Literal runs | `{dependency_stats['literal_ops']}` | `{dependency_stats['literal_digits']}` |",
        f"| Copy ops | `{dependency_stats['copy_ops']}` | `{dependency_stats['copied_digits']}` |",
        f"| Copy source fields | `{dependency_stats['copy_source_fields']}` | `{dependency_stats['copied_digits']}` |",
        f"| Copy length fields | `{dependency_stats['copy_length_fields']}` | `{dependency_stats['copied_digits']}` |",
        "",
        "## Interpretation",
        "",
    ]
    if classification == "lossless_recipe_representation_simplification":
        lines.extend(
            [
                "The per-book `length` field and copy `target_start` field are",
                "representation artifacts for the active online formula. Removing",
                "them in-memory preserves the exact cost and `70/70` roundtrip.",
                "The bound is unchanged, but the canonical recipe can be documented",
                "more tightly: book length is recovered from operation lengths, and",
                "copy target start is recovered from cumulative position.",
            ]
        )
    else:
        lines.extend(
            [
                "At least one supposedly derivable field failed the invariant check.",
                "Do not simplify the active recipe representation until the mismatch",
                "is resolved.",
            ]
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- No plaintext or translation is introduced.",
            "- Row0/table origin is unchanged.",
            "- The active formula file is not rewritten by this audit.",
            "- Remaining literal payload and copy source/length fields are still",
            "  required declared recipe dependencies.",
        ]
    )
    write_result("131_online_formula_recipe_prune_audit", result, lines)


if __name__ == "__main__":
    main()
