#!/usr/bin/env python3
"""Origin analysis for the 469 overlap-tape module model.

`module_overlap_grammar_search.py` shows that the 62 literal modules can be
stored as slices of 16 numeric components. This pass asks whether those
components behave like real book-layer units:

- do full components occur in the books?
- do module slices cover each component coherently?
- do adjacent modules in book recipes sometimes become one component interval,
  absorbing literal residual digits as gaps?

Mechanical only. No plaintext or glossary is promoted.
"""

from __future__ import annotations

import json
import random
from collections import Counter, defaultdict
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FORMULA_JSON = ROOT / "analysis" / "mechanism_model_20260618" / "mechanical_formula_469.json"
OVERLAP_JSON = HERE / "module_overlap_grammar_results.json"

OUT_JSON = HERE / "module_tape_origin_results.json"
OUT_MD = HERE / "module_tape_origin_report.md"

RANDOM_SEED = 46920260623
CONTROL_TRIALS = 2000


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def numeric_key(value: str) -> tuple[int, int | str]:
    try:
        return (0, int(value))
    except ValueError:
        return (1, value)


def reconstruct_books(formula: dict) -> dict[str, str]:
    modules = {module["id"]: module["text"] for module in formula["modules"]}
    return {
        str(book): "".join(modules[item["id"]] if item["type"] == "module" else item["text"] for item in recipe)
        for book, recipe in formula["book_recipes"].items()
    }


def all_occurrences(haystack: str, needle: str) -> list[int]:
    out = []
    start = 0
    while True:
        pos = haystack.find(needle, start)
        if pos < 0:
            return out
        out.append(pos)
        start = pos + 1


def longest_common_substring_length(left: str, right: str) -> int:
    previous = [0] * (len(right) + 1)
    best = 0
    for left_char in left:
        current = [0] * (len(right) + 1)
        for index, right_char in enumerate(right, start=1):
            if left_char == right_char:
                value = previous[index - 1] + 1
                current[index] = value
                if value > best:
                    best = value
        previous = current
    return best


def component_occurrence_rows(components: dict[str, str], books: dict[str, str]) -> list[dict]:
    rows = []
    for component_id, text in sorted(components.items()):
        hits = []
        longest = {"book": None, "length": 0, "fraction": 0.0}
        for book, raw in books.items():
            for pos in all_occurrences(raw, text):
                hits.append({"book": book, "offset": pos})
            length = longest_common_substring_length(text, raw)
            if length > longest["length"]:
                longest = {"book": book, "length": length, "fraction": length / len(text)}
        rows.append(
            {
                "component_id": component_id,
                "length": len(text),
                "full_book_hit_count": len(hits),
                "full_book_hits": sorted(hits, key=lambda item: (numeric_key(item["book"]), item["offset"]))[:20],
                "longest_book_match": longest,
            }
        )
    return rows


def union_length(intervals: list[tuple[int, int]]) -> int:
    if not intervals:
        return 0
    intervals = sorted(intervals)
    total = 0
    cur_start, cur_end = intervals[0]
    for start, end in intervals[1:]:
        if start <= cur_end:
            cur_end = max(cur_end, end)
        else:
            total += cur_end - cur_start
            cur_start, cur_end = start, end
    total += cur_end - cur_start
    return total


def component_slice_rows(components: dict[str, str], module_slices: dict[str, dict]) -> list[dict]:
    by_component: dict[str, list[tuple[str, int, int]]] = defaultdict(list)
    for module_id, item in module_slices.items():
        by_component[item["component_id"]].append((module_id, item["start"], item["end"]))
    rows = []
    for component_id, text in sorted(components.items()):
        intervals = [(start, end) for _module_id, start, end in by_component[component_id]]
        covered = union_length(intervals)
        rows.append(
            {
                "component_id": component_id,
                "length": len(text),
                "module_slice_count": len(intervals),
                "union_covered_digits": covered,
                "union_covered_fraction": covered / len(text),
                "modules": [
                    {"module_id": module_id, "start": start, "end": end}
                    for module_id, start, end in sorted(by_component[component_id], key=lambda item: (item[1], item[2], item[0]))
                ],
            }
        )
    return rows


def recipe_gap_analysis(formula: dict, components: dict[str, str], module_slices: dict[str, dict]) -> dict:
    rows = []
    total_literal_digits = sum(
        len(item["text"])
        for recipe in formula["book_recipes"].values()
        for item in recipe
        if item["type"] == "literal"
    )
    absorbed_literal_digits = 0
    accepted_links = 0
    accepted_zero_gap_links = 0
    candidate_links = 0
    for book in sorted(formula["book_recipes"], key=numeric_key):
        recipe = formula["book_recipes"][book]
        book_rows = []
        index = 0
        while index < len(recipe):
            item = recipe[index]
            if item["type"] == "literal":
                index += 1
                continue
            if item["type"] != "module":
                raise ValueError(item)

            current = module_slices[item["id"]]
            chain = {
                "book": book,
                "component_id": current["component_id"],
                "start": current["start"],
                "end": current["end"],
                "modules": [item["id"]],
                "absorbed_literal_digits": 0,
                "links": 0,
                "zero_gap_links": 0,
            }
            next_index = index + 1
            while next_index < len(recipe):
                literal_text = ""
                probe = next_index
                while probe < len(recipe) and recipe[probe]["type"] == "literal":
                    literal_text += recipe[probe]["text"]
                    probe += 1
                if probe >= len(recipe) or recipe[probe]["type"] != "module":
                    break
                nxt = module_slices[recipe[probe]["id"]]
                candidate_links += 1
                if nxt["component_id"] != chain["component_id"]:
                    break
                component = components[chain["component_id"]]
                expected_gap = component[chain["end"] : nxt["start"]] if nxt["start"] >= chain["end"] else None
                if expected_gap is not None and expected_gap == literal_text:
                    accepted_links += 1
                    if not literal_text:
                        accepted_zero_gap_links += 1
                    chain["modules"].append(recipe[probe]["id"])
                    chain["end"] = nxt["end"]
                    chain["absorbed_literal_digits"] += len(literal_text)
                    chain["links"] += 1
                    chain["zero_gap_links"] += 1 if not literal_text else 0
                    absorbed_literal_digits += len(literal_text)
                    next_index = probe + 1
                else:
                    break
            if chain["links"]:
                book_rows.append(chain)
            index = max(index + 1, next_index)
        rows.extend(book_rows)
    return {
        "total_literal_digits_in_recipes": total_literal_digits,
        "absorbed_literal_digits": absorbed_literal_digits,
        "absorbed_literal_fraction": absorbed_literal_digits / total_literal_digits if total_literal_digits else 0.0,
        "candidate_adjacent_module_links": candidate_links,
        "accepted_adjacent_module_links": accepted_links,
        "accepted_zero_gap_links": accepted_zero_gap_links,
        "chains": rows,
    }


def shuffled_components(components: dict[str, str], rng: random.Random) -> dict[str, str]:
    out = {}
    for component_id, text in components.items():
        chars = list(text)
        rng.shuffle(chars)
        out[component_id] = "".join(chars)
    return out


def summarize(values: list[float], observed: float, high_is_good: bool = True) -> dict:
    mean = sum(values) / len(values)
    sd = (sum((value - mean) ** 2 for value in values) / (len(values) - 1)) ** 0.5 if len(values) > 1 else 0.0
    if high_is_good:
        p = (sum(value >= observed for value in values) + 1) / (len(values) + 1)
        z = (observed - mean) / sd if sd else 0.0
    else:
        p = (sum(value <= observed for value in values) + 1) / (len(values) + 1)
        z = (mean - observed) / sd if sd else 0.0
    return {
        "observed": observed,
        "control_mean": mean,
        "control_sd": sd,
        "z_good_direction": z,
        "p_good_direction": p,
        "control_min": min(values),
        "control_max": max(values),
    }


def gap_controls(formula: dict, components: dict[str, str], module_slices: dict[str, dict], observed: dict) -> dict:
    rng = random.Random(RANDOM_SEED)
    absorbed_values = []
    accepted_link_values = []
    for _trial in range(CONTROL_TRIALS):
        shuffled = shuffled_components(components, rng)
        current = recipe_gap_analysis(formula, shuffled, module_slices)
        absorbed_values.append(current["absorbed_literal_digits"])
        accepted_link_values.append(current["accepted_adjacent_module_links"])
    return {
        "absorbed_literal_digits": summarize(absorbed_values, observed["absorbed_literal_digits"], high_is_good=True),
        "accepted_adjacent_module_links": summarize(
            accepted_link_values, observed["accepted_adjacent_module_links"], high_is_good=True
        ),
    }


def write_report(result: dict) -> None:
    lines = [
        "# Module Tape Origin Search",
        "",
        "Generated by `module_tape_origin_search.py`.",
        "",
        "This pass validates whether the overlap-tape components behave like real",
        "book-layer assembly units. It is mechanical only and promotes no",
        "plaintext.",
        "",
        "## Component Occurrence",
        "",
        "| Component | Length | Full book hits | Longest book match | Match fraction |",
        "|---|---:|---:|---|---:|",
    ]
    for row in result["component_occurrence_rows"]:
        longest = row["longest_book_match"]
        lines.append(
            f"| `{row['component_id']}` | {row['length']} | {row['full_book_hit_count']} | "
            f"`book {longest['book']}` / {longest['length']} | {longest['fraction']:.3f} |"
        )
    lines += [
        "",
        "## Slice Coverage",
        "",
        "| Component | Module slices | Union coverage | Coverage fraction |",
        "|---|---:|---:|---:|",
    ]
    for row in result["component_slice_rows"]:
        lines.append(
            f"| `{row['component_id']}` | {row['module_slice_count']} | "
            f"{row['union_covered_digits']} / {row['length']} | {row['union_covered_fraction']:.3f} |"
        )
    gap = result["recipe_gap_analysis"]
    controls = result["gap_controls"]
    lines += [
        "",
        "## Recipe Gap Absorption",
        "",
        f"- Literal digits in recipes: {gap['total_literal_digits_in_recipes']}.",
        f"- Literal digits absorbed as same-component gaps: {gap['absorbed_literal_digits']}.",
        f"- Accepted adjacent module links: {gap['accepted_adjacent_module_links']}.",
        f"- Zero-gap links among accepted links: {gap['accepted_zero_gap_links']}.",
        f"- Absorbed-digit shuffle p: {controls['absorbed_literal_digits']['p_good_direction']:.5f}.",
        f"- Link-count shuffle p: {controls['accepted_adjacent_module_links']['p_good_direction']:.5f}.",
        "",
        "| Book | Component | Interval | Modules | Absorbed literal digits |",
        "|---|---|---|---|---:|",
    ]
    for row in gap["chains"][:30]:
        lines.append(
            f"| `{row['book']}` | `{row['component_id']}` | `{row['start']}..{row['end']}` | "
            f"`{','.join(row['modules'])}` | {row['absorbed_literal_digits']} |"
        )
    lines += ["", "## Verdict", ""]
    if result["verdict"] == "secondary_support_overlap_tape_origin":
        lines.append(
            "The overlap components behave like real assembly units: most occur as full "
            "book substrings, all module slices validate, and some residual literal "
            "digits are explainable as same-component gaps. This supports the "
            "higher-order module-tape generator layer, without adding semantics."
        )
    else:
        lines.append(
            "The component model validates as a compression layer, but this pass does "
            "not add enough book-recipe evidence to promote it as an origin layer."
        )
    lines += ["", f"Translation delta: `{result['translation_delta']}`.", ""]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    formula = load_json(FORMULA_JSON)
    overlap = load_json(OVERLAP_JSON)
    model = overlap["best_overlap_tape_model"]
    components = {row["component_id"]: row["text"] for row in model["components"]}
    module_slices = {row["module_id"]: row for row in model["module_slices"]}
    books = reconstruct_books(formula)

    modules = {module["id"]: module["text"] for module in formula["modules"]}
    slice_errors = []
    for module_id, item in module_slices.items():
        text = components[item["component_id"]][item["start"] : item["end"]]
        if text != modules[module_id]:
            slice_errors.append(module_id)

    occurrence_rows = component_occurrence_rows(components, books)
    slice_rows = component_slice_rows(components, module_slices)
    gap = recipe_gap_analysis(formula, components, module_slices)
    controls = gap_controls(formula, components, module_slices, gap)
    full_hit_components = sum(1 for row in occurrence_rows if row["full_book_hit_count"])
    verdict = (
        "secondary_support_overlap_tape_origin"
        if not slice_errors
        and full_hit_components >= 12
        and controls["absorbed_literal_digits"]["p_good_direction"] <= 0.01
        else "not_promoted"
    )
    result = {
        "schema": "module_tape_origin_results.v1",
        "random_seed": RANDOM_SEED,
        "control_trials": CONTROL_TRIALS,
        "component_count": len(components),
        "module_slice_count": len(module_slices),
        "slice_validation_errors": slice_errors,
        "full_hit_components": full_hit_components,
        "component_occurrence_rows": occurrence_rows,
        "component_slice_rows": slice_rows,
        "recipe_gap_analysis": gap,
        "gap_controls": controls,
        "verdict": verdict,
        "translation_delta": "NONE",
    }
    write_json(OUT_JSON, result)
    write_report(result)
    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(
        f"verdict={verdict} full_hit_components={full_hit_components}/{len(components)} "
        f"absorbed_literals={gap['absorbed_literal_digits']} "
        f"p={controls['absorbed_literal_digits']['p_good_direction']:.5f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
