from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"
OUT = HERE / "hierarchical_reference_formula_469.json"

LITERAL_REFERENCE = HERE / "literal_reference_formula_469.json"
INVENTORY_REFERENCE = HERE / "tape_inventory_self_reference_formula.json"
BASE_MECHANICAL = ROOT / "analysis/mechanism_model_20260618/mechanical_formula_469.json"
TAPE_FORMULA = ROOT / "analysis/generator_search_20260618/tape_based_formula_469.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_result(name: str, result: dict, lines: list[str]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"{name}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / f"{name}.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def reconstruct_components(inventory_formula: dict) -> dict[str, str]:
    emitted = ""
    components = {}
    errors = []
    for recipe in inventory_formula["tape_component_recipes"]:
        parts = []
        for op in recipe["ops"]:
            if op["type"] == "literal":
                chunk = op["text"]
            elif op["type"] == "self_ref":
                chunk = emitted[op["source_pos"] : op["source_pos"] + op["length"]]
            else:
                raise ValueError(op)
            parts.append(chunk)
            emitted += chunk
        text = "".join(parts)
        if len(text) != recipe["length"]:
            errors.append({"component_id": recipe["component_id"], "expected_length": recipe["length"], "actual_length": len(text)})
        components[recipe["component_id"]] = text
        emitted += "#"
    if errors:
        raise ValueError(errors)
    return components


def render_books(book_recipes: dict, components: dict[str, str]) -> dict[str, str]:
    books = {}
    for book, recipe in book_recipes.items():
        parts = []
        for item in recipe:
            if item["type"] == "literal":
                parts.append(item["text"])
            elif item["type"] in {"module_slice", "tape_span", "tape_ref"}:
                parts.append(components[item["component_id"]][item["start"] : item["end"]])
            else:
                raise ValueError(item)
        books[str(book)] = "".join(parts)
    return books


def render_base_books(base: dict) -> dict[str, str]:
    modules = {module["id"]: module["text"] for module in base["modules"]}
    out = {}
    for book, recipe in base["book_recipes"].items():
        parts = []
        for item in recipe:
            if item["type"] == "module":
                parts.append(modules[item["id"]])
            elif item["type"] == "literal":
                parts.append(item["text"])
            else:
                raise ValueError(item)
        out[str(book)] = "".join(parts)
    return out


def main() -> None:
    base = load_json(BASE_MECHANICAL)
    tape = load_json(TAPE_FORMULA)
    literal = load_json(LITERAL_REFERENCE)
    inventory = load_json(INVENTORY_REFERENCE)

    components = reconstruct_components(inventory)
    rendered = render_books(literal["book_recipes"], components)
    expected = render_base_books(base)
    errors = []
    for book, text in expected.items():
        if rendered.get(str(book)) != text:
            errors.append(
                {
                    "book": str(book),
                    "expected_length": len(text),
                    "actual_length": len(rendered.get(str(book), "")),
                }
            )

    tape_bits = tape["mdl_estimate"]
    literal_saved = literal["mdl_delta_rough"]["saved_bits"]
    inventory_saved = inventory["mdl_delta_rough"]["saved_bits"]
    original_total = tape_bits["original_inventory_bits"] + tape_bits["original_recipe_bits_rough"]
    tape_total = tape_bits["tape_inventory_bits"] + tape_bits["tape_recipe_bits_rough"]
    literal_total = tape_total - literal_saved
    hierarchical_total = literal_total - inventory_saved

    output = {
        "schema": "hierarchical_reference_469_formula.v1",
        "scope": "mechanical_generator_only_no_semantics",
        "translation_delta": "NONE",
        "source_formulas": {
            "base_mechanical": str(BASE_MECHANICAL.relative_to(ROOT)),
            "tape_formula": str(TAPE_FORMULA.relative_to(ROOT)),
            "literal_reference": str(LITERAL_REFERENCE.relative_to(ROOT)),
            "tape_inventory_self_reference": str(INVENTORY_REFERENCE.relative_to(ROOT)),
        },
        "component_generation": inventory["tape_component_recipes"],
        "book_recipes": literal["book_recipes"],
        "validation": {
            "book_count": len(expected),
            "books_roundtrip_ok": len(expected) - len(errors),
            "errors": errors,
            "component_count": inventory["validation"]["component_count"],
            "components_roundtrip_ok": inventory["validation"]["components_roundtrip_ok"],
        },
        "mdl_estimate_rough": {
            "base_module_formula_bits": original_total,
            "tape_formula_bits": tape_total,
            "literal_reference_formula_bits": literal_total,
            "hierarchical_reference_formula_bits": hierarchical_total,
            "gain_vs_base_module_formula_bits": original_total - hierarchical_total,
            "gain_vs_tape_formula_bits": tape_total - hierarchical_total,
            "gain_vs_literal_reference_formula_bits": literal_total - hierarchical_total,
            "literal_reference_saved_bits": literal_saved,
            "tape_inventory_self_reference_saved_bits": inventory_saved,
        },
        "boundary": {
            "semantic_delta": "NONE",
            "pair_table_origin_explained": False,
            "authorial_intent_claim": False,
        },
    }
    OUT.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    classification = "hierarchical_reference_formula_roundtrips_no_semantics" if not errors else "hierarchical_reference_formula_failed"
    result = {
        "schema": "hierarchical_reference_formula_compile.v1",
        "test": "08_hierarchical_reference_formula_compile",
        "classification": classification,
        "translation_delta": "NONE",
        "output_formula": str(OUT.relative_to(ROOT)),
        "validation": output["validation"],
        "mdl_estimate_rough": output["mdl_estimate_rough"],
    }

    bits = output["mdl_estimate_rough"]
    lines = [
        "# Hierarchical Reference Formula Compile",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This compiler combines the controlled literal-reference recipe layer with",
        "the tape-inventory self-reference layer. The decoder first reconstructs",
        "the 16 tape components from literal runs and self-references, then renders",
        "all 70 books from the existing component slice/span/reference recipes.",
        "",
        "## Rough Cost Ladder",
        "",
        "| Model | Rough total bits | Gain vs previous |",
        "|---|---:|---:|",
        f"| Base module formula | `{bits['base_module_formula_bits']:.1f}` | `0.0` |",
        f"| Tape formula | `{bits['tape_formula_bits']:.1f}` | `{bits['base_module_formula_bits'] - bits['tape_formula_bits']:.1f}` |",
        f"| Literal-reference formula | `{bits['literal_reference_formula_bits']:.1f}` | `{bits['literal_reference_saved_bits']:.1f}` |",
        f"| Hierarchical reference formula | `{bits['hierarchical_reference_formula_bits']:.1f}` | `{bits['tape_inventory_self_reference_saved_bits']:.1f}` |",
        "",
        "## Validation",
        "",
        f"- Component roundtrip: `{output['validation']['components_roundtrip_ok']}/{output['validation']['component_count']}`.",
        f"- Book roundtrip: `{output['validation']['books_roundtrip_ok']}/{output['validation']['book_count']}`.",
        "",
        "## Boundary",
        "",
        "This is the current strongest mechanical book-generation formula in this",
        "front. It remains a generator/compression result only: no plaintext, no",
        "pair-table origin, and no authorial-intent claim are promoted.",
    ]
    write_result("08_hierarchical_reference_formula_compile", result, lines)


if __name__ == "__main__":
    main()
