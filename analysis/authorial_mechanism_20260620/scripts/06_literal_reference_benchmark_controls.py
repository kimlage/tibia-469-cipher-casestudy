from __future__ import annotations

import json
import math
import random
from pathlib import Path
from statistics import mean, pstdev


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

BASE_FORMULA = ROOT / "analysis/mechanism_model_20260618/mechanical_formula_469.json"
TAPE_FORMULA = ROOT / "analysis/generator_search_20260618/tape_based_formula_469.json"
REFERENCE_FORMULA = HERE / "literal_reference_formula_469.json"

LOG2_10 = math.log2(10)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_result(name: str, result: dict, lines: list[str]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"{name}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / f"{name}.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def formula_item_length(item: dict) -> int:
    if "length" in item:
        return int(item["length"])
    if item.get("type") == "literal":
        return len(item["text"])
    return int(item["end"]) - int(item["start"])


def ceil_log2(value: int) -> int:
    return max(1, math.ceil(math.log2(max(2, value))))


def reference_cost_bits(component_count: int, max_component_len: int, max_literal_len: int) -> int:
    return (
        ceil_log2(component_count)
        + ceil_log2(max_component_len + 1)
        + ceil_log2(max_literal_len + 1)
    )


def tape_components(formula: dict) -> list[dict]:
    return [
        {"id": component["id"], "text": component["text"], "length": len(component["text"])}
        for component in formula["tape_components"]
    ]


def literal_records(formula: dict) -> list[dict]:
    records = []
    for book, recipe in formula["book_recipes"].items():
        touched_components = {
            item["component_id"]
            for item in recipe
            if item["type"] in {"module_slice", "tape_span", "tape_ref"}
        }
        for ordinal, item in enumerate(recipe):
            if item["type"] == "literal":
                records.append(
                    {
                        "book": str(book),
                        "ordinal": ordinal,
                        "text": item["text"],
                        "length": len(item["text"]),
                        "touched_components": sorted(touched_components),
                    }
                )
    return records


def find_reference(text: str, components: list[dict], forbidden_component_ids: set[str] | None = None) -> dict | None:
    forbidden_component_ids = forbidden_component_ids or set()
    matches = []
    for component in components:
        if component["id"] in forbidden_component_ids:
            continue
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
    component_lengths = {component["id"]: component["length"] for component in components}
    matches.sort(key=lambda row: (component_lengths[row["component_id"]], row["start"], row["component_id"]))
    return matches[0]


def score_references(
    records: list[dict],
    components: list[dict],
    per_ref_bits: int,
    *,
    exclude_touched_components: bool = False,
) -> dict:
    hits = []
    considered = 0
    considered_digits = 0
    for record in records:
        literal_bits = record["length"] * LOG2_10
        if literal_bits <= per_ref_bits:
            continue
        considered += 1
        considered_digits += record["length"]
        forbidden = set(record["touched_components"]) if exclude_touched_components else set()
        match = find_reference(record["text"], components, forbidden)
        if match is None:
            continue
        hits.append(
            {
                "book": record["book"],
                "ordinal": record["ordinal"],
                "length": record["length"],
                "component_id": match["component_id"],
                "saved_bits": literal_bits - per_ref_bits,
            }
        )
    return {
        "considered_items": considered,
        "considered_digits": considered_digits,
        "reference_items": len(hits),
        "referenced_digits": sum(hit["length"] for hit in hits),
        "saved_bits": sum(hit["saved_bits"] for hit in hits),
        "top_hits": sorted(hits, key=lambda row: row["saved_bits"], reverse=True)[:20],
    }


def shuffled_components(components: list[dict], rng: random.Random) -> list[dict]:
    out = []
    for component in components:
        chars = list(component["text"])
        rng.shuffle(chars)
        out.append({"id": component["id"], "text": "".join(chars), "length": component["length"]})
    return out


def random_digit_records(records: list[dict], rng: random.Random) -> list[dict]:
    out = []
    for record in records:
        text = "".join(str(rng.randrange(10)) for _ in range(record["length"]))
        out.append({**record, "text": text})
    return out


def shuffled_book_records(records: list[dict], rng: random.Random) -> list[dict]:
    touched = [record["touched_components"] for record in records]
    rng.shuffle(touched)
    return [{**record, "touched_components": list(touched[index])} for index, record in enumerate(records)]


def summarize_control(values: list[float], observed: float) -> dict:
    if not values:
        return {
            "runs": 0,
            "mean": 0.0,
            "sd": 0.0,
            "min": 0.0,
            "max": 0.0,
            "p_ge_observed": None,
        }
    return {
        "runs": len(values),
        "mean": mean(values),
        "sd": pstdev(values),
        "min": min(values),
        "max": max(values),
        "p_ge_observed": (sum(value >= observed for value in values) + 1) / (len(values) + 1),
    }


def run_controls(
    records: list[dict],
    components: list[dict],
    per_ref_bits: int,
    observed_unrestricted: float,
    observed_exclude_touched: float,
    runs: int = 400,
) -> dict:
    component_shuffle_values = []
    component_shuffle_items = []
    random_literal_values = []
    random_literal_items = []
    shuffled_book_exclusion_values = []
    shuffled_book_exclusion_items = []

    for seed in range(runs):
        rng = random.Random(469000 + seed)

        component_control = score_references(
            records,
            shuffled_components(components, rng),
            per_ref_bits,
        )
        component_shuffle_values.append(component_control["saved_bits"])
        component_shuffle_items.append(component_control["reference_items"])

        literal_control = score_references(
            random_digit_records(records, rng),
            components,
            per_ref_bits,
        )
        random_literal_values.append(literal_control["saved_bits"])
        random_literal_items.append(literal_control["reference_items"])

        book_control = score_references(
            shuffled_book_records(records, rng),
            components,
            per_ref_bits,
            exclude_touched_components=True,
        )
        shuffled_book_exclusion_values.append(book_control["saved_bits"])
        shuffled_book_exclusion_items.append(book_control["reference_items"])

    component_summary = summarize_control(component_shuffle_values, observed_unrestricted)
    component_summary["reference_items_mean"] = mean(component_shuffle_items)
    component_summary["reference_items_max"] = max(component_shuffle_items)

    random_literal_summary = summarize_control(random_literal_values, observed_unrestricted)
    random_literal_summary["reference_items_mean"] = mean(random_literal_items)
    random_literal_summary["reference_items_max"] = max(random_literal_items)

    shuffled_book_summary = summarize_control(shuffled_book_exclusion_values, observed_exclude_touched)
    shuffled_book_summary["reference_items_mean"] = mean(shuffled_book_exclusion_items)
    shuffled_book_summary["reference_items_max"] = max(shuffled_book_exclusion_items)

    return {
        "component_digit_shuffle": component_summary,
        "random_length_matched_literals": random_literal_summary,
        "shuffled_book_exclusion": shuffled_book_summary,
    }


def model_cost_table(base: dict, tape: dict, ref: dict) -> list[dict]:
    tape_bits = tape["mdl_estimate"]
    ref_saved = ref["mdl_delta_rough"]["saved_bits"]
    original_total = tape_bits["original_inventory_bits"] + tape_bits["original_recipe_bits_rough"]
    tape_total = tape_bits["tape_inventory_bits"] + tape_bits["tape_recipe_bits_rough"]
    ref_total = tape_total - ref_saved
    return [
        {
            "model": "mechanical_formula_469",
            "schema": base["schema"],
            "inventory_bits": tape_bits["original_inventory_bits"],
            "recipe_bits_rough": tape_bits["original_recipe_bits_rough"],
            "total_bits_rough": original_total,
            "delta_vs_previous_bits": 0.0,
            "literal_digits": base["validation"]["literal_digits"],
            "roundtrip": bool(base["validation"]["roundtrip_ok"]),
        },
        {
            "model": "tape_based_formula_469",
            "schema": tape["schema"],
            "inventory_bits": tape_bits["tape_inventory_bits"],
            "recipe_bits_rough": tape_bits["tape_recipe_bits_rough"],
            "total_bits_rough": tape_total,
            "delta_vs_previous_bits": original_total - tape_total,
            "literal_digits": tape["validation"]["recipe_stats"]["literal_digits"],
            "roundtrip": tape["validation"]["books_roundtrip_ok"] == tape["validation"]["book_count"],
        },
        {
            "model": "literal_reference_formula_469",
            "schema": ref["schema"],
            "inventory_bits": tape_bits["tape_inventory_bits"],
            "recipe_bits_rough": tape_bits["tape_recipe_bits_rough"] - ref_saved,
            "total_bits_rough": ref_total,
            "delta_vs_previous_bits": tape_total - ref_total,
            "literal_digits": ref["mdl_delta_rough"]["kept_literal_digits"],
            "roundtrip": ref["validation"]["books_roundtrip_ok"] == ref["validation"]["book_count"],
        },
    ]


def classify(real_score: dict, controls: dict, ref_formula: dict) -> str:
    if ref_formula["translation_delta"] != "NONE":
        return "invalid_translation_delta_changed"
    if ref_formula["validation"]["errors"]:
        return "invalid_roundtrip_errors"
    component_p = controls["component_digit_shuffle"]["p_ge_observed"]
    random_p = controls["random_length_matched_literals"]["p_ge_observed"]
    if real_score["saved_bits"] > 0 and component_p <= 0.01 and random_p <= 0.01:
        return "controlled_mechanical_improvement_no_semantics"
    return "candidate_requires_more_controls"


def main() -> None:
    base = load_json(BASE_FORMULA)
    tape = load_json(TAPE_FORMULA)
    ref = load_json(REFERENCE_FORMULA)
    components = tape_components(tape)
    records = literal_records(tape)
    max_component_len = max(component["length"] for component in components)
    max_literal_len = max(record["length"] for record in records)
    per_ref_bits = reference_cost_bits(len(components), max_component_len, max_literal_len)

    real_unrestricted = score_references(records, components, per_ref_bits)
    real_exclude_touched = score_references(
        records,
        components,
        per_ref_bits,
        exclude_touched_components=True,
    )
    controls = run_controls(
        records,
        components,
        per_ref_bits,
        real_unrestricted["saved_bits"],
        real_exclude_touched["saved_bits"],
    )
    costs = model_cost_table(base, tape, ref)
    classification = classify(real_unrestricted, controls, ref)

    result = {
        "schema": "literal_reference_benchmark_controls.v1",
        "test": "06_literal_reference_benchmark_controls",
        "classification": classification,
        "translation_delta": "NONE",
        "inputs": {
            "base_formula": str(BASE_FORMULA.relative_to(ROOT)),
            "tape_formula": str(TAPE_FORMULA.relative_to(ROOT)),
            "reference_formula": str(REFERENCE_FORMULA.relative_to(ROOT)),
        },
        "reference_policy": {
            "per_reference_bits": per_ref_bits,
            "component_count": len(components),
            "max_component_len": max_component_len,
            "max_literal_len": max_literal_len,
            "item_overhead_policy": "neutral_between_literal_and_reference_items",
        },
        "model_costs": costs,
        "real_scores": {
            "unrestricted": real_unrestricted,
            "exclude_touched_book_components": real_exclude_touched,
        },
        "controls": controls,
        "boundary": {
            "semantic_delta": "NONE",
            "pair_table_origin_explained": False,
            "authorial_intent_claim": False,
        },
    }

    cost_lines = [
        "| Model | Rough total bits | Gain vs previous | Literal digits | Roundtrip |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in costs:
        cost_lines.append(
            "| `{model}` | `{total:.1f}` | `{delta:.1f}` | `{literal}` | `{roundtrip}` |".format(
                model=row["model"],
                total=row["total_bits_rough"],
                delta=row["delta_vs_previous_bits"],
                literal=row["literal_digits"],
                roundtrip=row["roundtrip"],
            )
        )

    lines = [
        "# Literal Reference Benchmark and Controls",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This benchmark compares the base module formula, the tape formula, and",
        "the literal-reference formula under the same rough internal cost ledger.",
        "The item overhead is held neutral between literal and reference items, so",
        "the reported gain is the address-vs-digit payload delta only.",
        "",
        "## Model Cost Ladder",
        "",
        *cost_lines,
        "",
        "## Real Reference Scores",
        "",
        "| Mode | Reference items | Referenced digits | Saved bits |",
        "|---|---:|---:|---:|",
        (
            f"| unrestricted | `{real_unrestricted['reference_items']}` | "
            f"`{real_unrestricted['referenced_digits']}` | `{real_unrestricted['saved_bits']:.1f}` |"
        ),
        (
            f"| exclude components already touched by the same book | "
            f"`{real_exclude_touched['reference_items']}` | "
            f"`{real_exclude_touched['referenced_digits']}` | `{real_exclude_touched['saved_bits']:.1f}` |"
        ),
        "",
        "## Negative Controls",
        "",
        "| Control | Runs | Mean saved bits | Max saved bits | p(>= observed) |",
        "|---|---:|---:|---:|---:|",
    ]
    for key, observed in [
        ("component_digit_shuffle", real_unrestricted["saved_bits"]),
        ("random_length_matched_literals", real_unrestricted["saved_bits"]),
        ("shuffled_book_exclusion", real_exclude_touched["saved_bits"]),
    ]:
        row = controls[key]
        lines.append(
            f"| `{key}` | `{row['runs']}` | `{row['mean']:.1f}` | "
            f"`{row['max']:.1f}` | `{row['p_ge_observed']:.4f}` |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "The literal-reference layer is promoted only as a controlled mechanical",
            "compression improvement. It does not explain the 10x10 pair-table",
            "origin, does not create plaintext, and does not support any private",
            "authorial-intent claim.",
        ]
    )
    write_result("06_literal_reference_benchmark_controls", result, lines)


if __name__ == "__main__":
    main()
