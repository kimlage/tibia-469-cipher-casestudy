from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"
OUT = HERE / "literal_reference_formula_469.json"
FORMULA = ROOT / "analysis/generator_search_20260618/tape_based_formula_469.json"
LOG2_10 = math.log2(10)


def write_result(name: str, result: dict, lines: list[str]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"{name}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / f"{name}.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def ref_cost_bits(component_count: int, max_component_len: int, max_literal_len: int) -> int:
    return (
        math.ceil(math.log2(component_count))
        + math.ceil(math.log2(max_component_len + 1))
        + math.ceil(math.log2(max_literal_len + 1))
    )


def find_ref(text: str, components: list[dict]) -> dict | None:
    matches = []
    for component in components:
        start = component["text"].find(text)
        if start >= 0:
            matches.append(
                {
                    "component_id": component["id"],
                    "start": start,
                    "end": start + len(text),
                    "length": len(text),
                }
            )
    if not matches:
        return None
    # Stable deterministic choice: shortest component, then earliest start.
    component_lengths = {component["id"]: component["length"] for component in components}
    matches.sort(key=lambda row: (component_lengths[row["component_id"]], row["start"], row["component_id"]))
    return matches[0]


def render_recipe(recipe: list[dict], component_text: dict[str, str]) -> str:
    parts = []
    for item in recipe:
        if item["type"] in {"module_slice", "tape_span", "tape_ref"}:
            parts.append(component_text[item["component_id"]][item["start"] : item["end"]])
        elif item["type"] == "literal":
            parts.append(item["text"])
        else:
            raise ValueError(f"unknown recipe item type: {item['type']}")
    return "".join(parts)


def main() -> None:
    data = json.loads(FORMULA.read_text(encoding="utf-8"))
    components = data["tape_components"]
    component_text = {component["id"]: component["text"] for component in components}
    max_component_len = max(component["length"] for component in components)
    max_literal_len = max(
        item["length"]
        for recipe in data["book_recipes"].values()
        for item in recipe
        if item["type"] == "literal"
    )
    per_ref_bits = ref_cost_bits(len(components), max_component_len, max_literal_len)

    new_recipes = {}
    ref_items = []
    kept_literal_items = []
    baseline_literal_bits = 0.0
    new_reference_bits = 0.0
    saved_bits = 0.0
    for book, recipe in data["book_recipes"].items():
        new_recipe = []
        for item in recipe:
            if item["type"] != "literal":
                new_recipe.append(item)
                continue
            literal_bits = item["length"] * LOG2_10
            ref = find_ref(item["text"], components)
            if ref is not None and literal_bits > per_ref_bits:
                new_item = {
                    "type": "tape_ref",
                    "component_id": ref["component_id"],
                    "start": ref["start"],
                    "end": ref["end"],
                    "length": ref["length"],
                    "source_literal_sha256": item["sha256"],
                    "source_literal_length": item["length"],
                }
                new_recipe.append(new_item)
                ref_items.append({"book": book, **new_item, "saved_bits": literal_bits - per_ref_bits})
                baseline_literal_bits += literal_bits
                new_reference_bits += per_ref_bits
                saved_bits += literal_bits - per_ref_bits
            else:
                new_recipe.append(item)
                kept_literal_items.append({"book": book, "length": item["length"], "reason": "no_positive_ref"})
                baseline_literal_bits += literal_bits
                new_reference_bits += literal_bits
        new_recipes[book] = new_recipe

    errors = []
    for book, recipe in data["book_recipes"].items():
        old_text = render_recipe(recipe, component_text)
        new_text = render_recipe(new_recipes[book], component_text)
        if old_text != new_text:
            errors.append({"book": book, "old_len": len(old_text), "new_len": len(new_text)})

    output = {
        "schema": "literal_reference_tape_formula.v1",
        "scope": "mechanical_generator_only_no_semantics",
        "source_formula": str(FORMULA.relative_to(ROOT)),
        "translation_delta": "NONE",
        "book_recipes": new_recipes,
        "tape_components": components,
        "reference_policy": {
            "per_reference_bits": per_ref_bits,
            "component_count": len(components),
            "max_component_len": max_component_len,
            "max_literal_len": max_literal_len,
            "accept_if_literal_bits_gt_reference_bits": True,
        },
        "validation": {
            "books_roundtrip_ok": len(data["book_recipes"]) - len(errors),
            "book_count": len(data["book_recipes"]),
            "errors": errors,
        },
        "mdl_delta_rough": {
            "baseline_literal_bits_for_considered_literals": baseline_literal_bits,
            "new_reference_or_literal_bits": new_reference_bits,
            "saved_bits": saved_bits,
            "reference_items": len(ref_items),
            "kept_literal_items": len(kept_literal_items),
            "referenced_literal_digits": sum(item["length"] for item in ref_items),
            "kept_literal_digits": sum(item["length"] for item in kept_literal_items),
        },
    }
    OUT.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    classification = "candidate_literal_reference_formula" if not errors and saved_bits > 0 else "literal_reference_not_promoted"
    result = {
        "schema": "literal_reference_formula_compile.v1",
        "test": "05_literal_reference_formula_compile",
        "classification": classification,
        "translation_delta": "NONE",
        "output_formula": str(OUT.relative_to(ROOT)),
        "per_reference_bits": per_ref_bits,
        "reference_items": len(ref_items),
        "referenced_literal_digits": sum(item["length"] for item in ref_items),
        "kept_literal_items": len(kept_literal_items),
        "kept_literal_digits": sum(item["length"] for item in kept_literal_items),
        "saved_bits_rough": saved_bits,
        "books_roundtrip_ok": output["validation"]["books_roundtrip_ok"],
        "book_count": output["validation"]["book_count"],
        "errors": errors,
        "top_refs": sorted(ref_items, key=lambda row: row["saved_bits"], reverse=True)[:20],
    }
    lines = [
        "# Literal Reference Formula Compile",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This pass compiles a candidate improvement over the tape formula by",
        "replacing remaining literal strings with references into existing tape",
        "components when the reference address is cheaper than storing digits.",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Per-reference bits | `{per_ref_bits}` |",
        f"| Reference items | `{len(ref_items)}` |",
        f"| Referenced literal digits | `{sum(item['length'] for item in ref_items)}` |",
        f"| Kept literal items | `{len(kept_literal_items)}` |",
        f"| Kept literal digits | `{sum(item['length'] for item in kept_literal_items)}` |",
        f"| Rough saved bits | `{saved_bits:.1f}` |",
        f"| Book roundtrip | `{output['validation']['books_roundtrip_ok']}/{output['validation']['book_count']}` |",
        "",
        "## Boundary",
        "",
        "This is a mechanical reference-layer improvement only. It does not explain",
        "the pair table, does not add source authority, and does not translate any",
        "book.",
    ]
    write_result("05_literal_reference_formula_compile", result, lines)


if __name__ == "__main__":
    main()
