#!/usr/bin/env python3
"""Compile a tape-based mechanical formula for 469.

This converts the existing 62-module formula into a higher-order formula:

1. 16 overlap-tape components.
2. 62 module aliases as slices of those components.
3. Book recipes that may merge adjacent same-component module aliases and the
   literal digits between them into direct tape spans.

The output is a mechanical generator only. It does not translate 469.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FORMULA_JSON = ROOT / "analysis" / "mechanism_model_20260618" / "mechanical_formula_469.json"
OVERLAP_JSON = HERE / "module_overlap_grammar_results.json"

OUT_JSON = HERE / "tape_based_formula_469.json"
OUT_MD = HERE / "tape_based_formula_report.md"

LOG2_10 = math.log2(10)


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def numeric_key(value: str) -> tuple[int, int | str]:
    try:
        return (0, int(value))
    except ValueError:
        return (1, value)


def ceil_log2(value: int) -> int:
    return max(1, math.ceil(math.log2(max(2, value))))


def reconstruct_from_original(formula: dict) -> dict[str, str]:
    modules = {module["id"]: module["text"] for module in formula["modules"]}
    return {
        str(book): "".join(modules[item["id"]] if item["type"] == "module" else item["text"] for item in recipe)
        for book, recipe in formula["book_recipes"].items()
    }


def reconstruct_from_tape(formula: dict) -> dict[str, str]:
    components = {component["id"]: component["text"] for component in formula["tape_components"]}
    module_slices = {item["id"]: item for item in formula["module_slices"]}
    out = {}
    for book, recipe in formula["book_recipes"].items():
        parts = []
        for item in recipe:
            if item["type"] == "literal":
                parts.append(item["text"])
            elif item["type"] == "module_slice":
                sl = module_slices[item["id"]]
                parts.append(components[sl["component_id"]][sl["start"] : sl["end"]])
            elif item["type"] == "tape_span":
                parts.append(components[item["component_id"]][item["start"] : item["end"]])
            else:
                raise ValueError(item)
        out[str(book)] = "".join(parts)
    return out


def compile_book_recipe(original_recipe: list[dict], components: dict[str, str], module_slices: dict[str, dict]) -> tuple[list[dict], dict]:
    out = []
    stats = {
        "source_module_refs": 0,
        "source_literal_items": 0,
        "source_literal_digits": 0,
        "merged_module_refs": 0,
        "absorbed_literal_items": 0,
        "absorbed_literal_digits": 0,
        "tape_spans": 0,
        "module_slice_refs": 0,
        "literal_items": 0,
        "literal_digits": 0,
    }
    index = 0
    while index < len(original_recipe):
        item = original_recipe[index]
        if item["type"] == "literal":
            stats["source_literal_items"] += 1
            stats["source_literal_digits"] += len(item["text"])
            stats["literal_items"] += 1
            stats["literal_digits"] += len(item["text"])
            out.append({"type": "literal", "length": len(item["text"]), "sha256": sha256(item["text"]), "text": item["text"]})
            index += 1
            continue
        if item["type"] != "module":
            raise ValueError(item)

        stats["source_module_refs"] += 1
        current = module_slices[item["id"]]
        chain = {
            "type": "tape_span",
            "component_id": current["component_id"],
            "start": current["start"],
            "end": current["end"],
            "length": current["end"] - current["start"],
            "source_module_ids": [item["id"]],
            "absorbed_literal_texts": [],
            "sha256": "",
        }
        next_index = index + 1
        while next_index < len(original_recipe):
            literal_items = []
            literal_text = ""
            probe = next_index
            while probe < len(original_recipe) and original_recipe[probe]["type"] == "literal":
                literal_items.append(original_recipe[probe])
                literal_text += original_recipe[probe]["text"]
                probe += 1
            if probe >= len(original_recipe) or original_recipe[probe]["type"] != "module":
                break
            nxt = module_slices[original_recipe[probe]["id"]]
            if nxt["component_id"] != chain["component_id"] or nxt["start"] < chain["end"]:
                break
            component = components[chain["component_id"]]
            if component[chain["end"] : nxt["start"]] != literal_text:
                break
            stats["source_module_refs"] += 1
            stats["merged_module_refs"] += 1
            stats["source_literal_items"] += len(literal_items)
            stats["source_literal_digits"] += len(literal_text)
            stats["absorbed_literal_items"] += len(literal_items)
            stats["absorbed_literal_digits"] += len(literal_text)
            chain["source_module_ids"].append(original_recipe[probe]["id"])
            chain["absorbed_literal_texts"].append(literal_text)
            chain["end"] = nxt["end"]
            chain["length"] = chain["end"] - chain["start"]
            next_index = probe + 1

        if len(chain["source_module_ids"]) > 1:
            span_text = components[chain["component_id"]][chain["start"] : chain["end"]]
            chain["sha256"] = sha256(span_text)
            stats["tape_spans"] += 1
            out.append(chain)
            index = next_index
        else:
            stats["module_slice_refs"] += 1
            out.append(
                {
                    "type": "module_slice",
                    "id": item["id"],
                    "component_id": current["component_id"],
                    "start": current["start"],
                    "end": current["end"],
                    "length": current["end"] - current["start"],
                }
            )
            index += 1
    return out, stats


def add_stats(left: dict, right: dict) -> dict:
    out = dict(left)
    for key, value in right.items():
        out[key] = out.get(key, 0) + value
    return out


def estimate_bits(base_formula: dict, tape_formula: dict, stats: dict) -> dict:
    original_module_digits = sum(module["length"] for module in base_formula["modules"])
    tape_digits = sum(component["length"] for component in tape_formula["tape_components"])
    max_component_len = max(component["length"] for component in tape_formula["tape_components"])
    component_id_bits = ceil_log2(len(tape_formula["tape_components"]))
    component_pos_bits = ceil_log2(max_component_len + 1)
    module_slice_address_bits = len(tape_formula["module_slices"]) * (component_id_bits + 2 * component_pos_bits)
    original_inventory_bits = original_module_digits * LOG2_10
    tape_inventory_bits = tape_digits * LOG2_10 + module_slice_address_bits

    # Recipe cost is deliberately rough and comparable only inside this report.
    module_id_bits = ceil_log2(len(tape_formula["module_slices"]))
    original_recipe_bits = (
        stats["source_module_refs"] * module_id_bits
        + stats["source_literal_digits"] * LOG2_10
        + stats["source_literal_items"] * 16
    )
    tape_recipe_bits = (
        stats["module_slice_refs"] * module_id_bits
        + stats["tape_spans"] * (component_id_bits + 2 * component_pos_bits)
        + stats["literal_digits"] * LOG2_10
        + stats["literal_items"] * 16
    )
    return {
        "original_module_inventory_digits": original_module_digits,
        "tape_component_digits": tape_digits,
        "module_slice_address_bits": module_slice_address_bits,
        "original_inventory_bits": original_inventory_bits,
        "tape_inventory_bits": tape_inventory_bits,
        "inventory_gain_bits": original_inventory_bits - tape_inventory_bits,
        "original_recipe_bits_rough": original_recipe_bits,
        "tape_recipe_bits_rough": tape_recipe_bits,
        "recipe_gain_bits_rough": original_recipe_bits - tape_recipe_bits,
        "total_gain_bits_rough": (original_inventory_bits + original_recipe_bits) - (tape_inventory_bits + tape_recipe_bits),
    }


def write_report(result: dict) -> None:
    stats = result["validation"]["recipe_stats"]
    bits = result["mdl_estimate"]
    lines = [
        "# Tape-Based Mechanical Formula",
        "",
        "Generated by `tape_based_formula_compile.py`.",
        "",
        "This is a higher-order mechanical formula for the 70-book layer. It",
        "replaces the literal 62-module inventory with 16 overlap-tape components",
        "plus module slices, and merges same-component book recipe chains when",
        "literal digits are exact tape gaps.",
        "",
        "The JSON also carries the base `code_to_symbol`, `symbol_to_codes`, and",
        "`pair_table` maps so it is self-contained for the current mechanical",
        "language layer.",
        "",
        "It is not a translation and creates no plaintext.",
        "",
        "## Validation",
        "",
        f"- Book roundtrip: {result['validation']['books_roundtrip_ok']} / {result['validation']['book_count']}.",
        f"- Module slice roundtrip: {result['validation']['module_slices_roundtrip_ok']} / {result['validation']['module_slice_count']}.",
        f"- Translation delta: `{result['translation_delta']}`.",
        "",
        "## Recipe Compression",
        "",
        f"- Source module references: {stats['source_module_refs']}.",
        f"- Source literal digits: {stats['source_literal_digits']}.",
        f"- Tape spans created: {stats['tape_spans']}.",
        f"- Merged module references: {stats['merged_module_refs']}.",
        f"- Absorbed literal digits: {stats['absorbed_literal_digits']}.",
        f"- Remaining literal digits: {stats['literal_digits']}.",
        f"- Remaining module-slice references: {stats['module_slice_refs']}.",
        "",
        "## Rough MDL",
        "",
        f"- Original module inventory: {bits['original_module_inventory_digits']} digits / {bits['original_inventory_bits']:.1f} bits.",
        f"- Tape component inventory: {bits['tape_component_digits']} digits + slice addresses / {bits['tape_inventory_bits']:.1f} bits.",
        f"- Inventory gain: {bits['inventory_gain_bits']:.1f} bits.",
        f"- Rough recipe gain: {bits['recipe_gain_bits_rough']:.1f} bits.",
        f"- Rough total gain: {bits['total_gain_bits_rough']:.1f} bits.",
        "",
        "## Verdict",
        "",
    ]
    if result["verdict"] == "candidate_tape_based_formula":
        lines.append(
            "The tape formula is a lossless 70/70 mechanical generator and is more "
            "compact than the literal module table under the rough internal MDL "
            "estimate. It is the current best book-layer formula, but it still does "
            "not explain the original 10x10 pair-table placement or any semantics."
        )
    else:
        lines.append("The tape formula failed validation or MDL and is not promoted.")
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    base = load_json(FORMULA_JSON)
    overlap = load_json(OVERLAP_JSON)
    model = overlap["best_overlap_tape_model"]
    components = {row["component_id"]: row["text"] for row in model["components"]}
    module_slices = {row["module_id"]: row for row in model["module_slices"]}
    module_texts = {module["id"]: module["text"] for module in base["modules"]}

    module_slice_rows = []
    module_errors = []
    for module_id, sl in sorted(module_slices.items(), key=lambda item: item[0]):
        text = components[sl["component_id"]][sl["start"] : sl["end"]]
        if text != module_texts[module_id]:
            module_errors.append(module_id)
        module_slice_rows.append(
            {
                "id": module_id,
                "component_id": sl["component_id"],
                "start": sl["start"],
                "end": sl["end"],
                "length": sl["end"] - sl["start"],
                "sha256": sha256(text),
            }
        )

    recipes = {}
    stats = {}
    total_stats: dict[str, int] = {}
    for book in sorted(base["book_recipes"], key=numeric_key):
        recipe, row_stats = compile_book_recipe(base["book_recipes"][book], components, module_slices)
        recipes[book] = recipe
        stats[book] = row_stats
        total_stats = add_stats(total_stats, row_stats)

    formula = {
        "schema": "tape_based_469_formula.v1",
        "source_formula": str(FORMULA_JSON.relative_to(ROOT)),
        "source_overlap_model": str(OVERLAP_JSON.relative_to(ROOT)),
        "scope": "mechanical_generator_only",
        "translation_delta": "NONE",
        "code_to_symbol": base["code_to_symbol"],
        "symbol_to_codes": base["symbol_to_codes"],
        "pair_table": base["pair_table"],
        "code_counts": base["code_counts"],
        "tape_components": [
            {"id": row["component_id"], "length": row["length"], "sha256": sha256(row["text"]), "text": row["text"]}
            for row in model["components"]
        ],
        "module_slices": module_slice_rows,
        "book_recipes": recipes,
        "book_recipe_stats": stats,
    }
    original_books = reconstruct_from_original(base)
    tape_books = reconstruct_from_tape(formula)
    book_errors = [book for book in sorted(original_books, key=numeric_key) if original_books[book] != tape_books.get(book)]
    bits = estimate_bits(base, formula, total_stats)
    formula["validation"] = {
        "book_count": len(original_books),
        "books_roundtrip_ok": len(original_books) - len(book_errors),
        "book_errors": book_errors,
        "module_slice_count": len(module_slice_rows),
        "module_slices_roundtrip_ok": len(module_slice_rows) - len(module_errors),
        "module_slice_errors": module_errors,
        "recipe_stats": total_stats,
    }
    formula["mdl_estimate"] = bits
    formula["verdict"] = (
        "candidate_tape_based_formula"
        if not book_errors and not module_errors and bits["total_gain_bits_rough"] > 0
        else "not_promoted"
    )

    write_json(OUT_JSON, formula)
    write_report(formula)
    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(
        f"verdict={formula['verdict']} books={formula['validation']['books_roundtrip_ok']}/{formula['validation']['book_count']} "
        f"module_slices={formula['validation']['module_slices_roundtrip_ok']}/{formula['validation']['module_slice_count']} "
        f"gain_bits={bits['total_gain_bits_rough']:.1f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
