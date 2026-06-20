from __future__ import annotations

import json
import math
import random
from pathlib import Path
from statistics import mean, pstdev


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"
OUT = HERE / "tape_inventory_self_reference_formula.json"
TAPE_FORMULA = ROOT / "analysis/generator_search_20260618/tape_based_formula_469.json"

LOG2_10 = math.log2(10)
SEP = "#"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_result(name: str, result: dict, lines: list[str]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"{name}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / f"{name}.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def ceil_log2(value: int) -> int:
    return max(1, math.ceil(math.log2(max(2, value))))


def source_position_bits(components: list[dict]) -> int:
    total_digits = sum(len(component["text"]) for component in components)
    separators = max(0, len(components) - 1)
    return ceil_log2(total_digits + separators + 1)


def add_index_entries(available: str, index: dict[str, list[int]], min_len: int, previous_len: int) -> None:
    """Add newly available min_len substrings.

    The decoder may only reference already-emitted digits. Separator-spanning
    source substrings are excluded because component boundaries are structural,
    not digit payload.
    """

    for end in range(max(min_len, previous_len + 1), len(available) + 1):
        start = end - min_len
        key = available[start:end]
        if SEP not in key:
            index.setdefault(key, []).append(start)


def best_previous_match(
    target: str,
    pos: int,
    available: str,
    index: dict[str, list[int]],
    min_len: int,
    max_ref_len: int,
) -> dict | None:
    if pos + min_len > len(target):
        return None
    key = target[pos : pos + min_len]
    candidates = index.get(key, [])
    if not candidates:
        return None

    best = None
    max_target_len = min(max_ref_len, len(target) - pos)
    for source_pos in candidates:
        length = min_len
        while length < max_target_len:
            next_source = source_pos + length
            if next_source >= len(available) or available[next_source] == SEP:
                break
            if available[next_source] != target[pos + length]:
                break
            length += 1
        if best is None or length > best["length"] or (
            length == best["length"] and source_pos < best["source_pos"]
        ):
            best = {"source_pos": source_pos, "length": length}
    return best


def merge_literal_ops(ops: list[dict], text: str) -> list[dict]:
    if not text:
        return ops
    if ops and ops[-1]["type"] == "literal":
        ops[-1]["text"] += text
        ops[-1]["length"] += len(text)
    else:
        ops.append({"type": "literal", "text": text, "length": len(text)})
    return ops


def encode_components(
    components: list[dict],
    *,
    min_len: int,
    max_ref_len: int,
    pos_bits: int,
    len_bits: int,
    allow_current_component_refs: bool = True,
) -> dict:
    ref_bits = 1 + pos_bits + len_bits
    literal_run_overhead = 1 + len_bits
    baseline_digits = sum(len(component["text"]) for component in components)
    baseline_bits = baseline_digits * LOG2_10

    available = ""
    index: dict[str, list[int]] = {}
    recipes = []
    refs = []
    literal_digits = 0

    for component in components:
        text = component["text"]
        pos = 0
        ops: list[dict] = []
        component_start_available = len(available)
        while pos < len(text):
            match = best_previous_match(text, pos, available, index, min_len, max_ref_len)
            if match is not None and not allow_current_component_refs:
                if match["source_pos"] >= component_start_available:
                    match = None
            if match is not None and match["length"] * LOG2_10 > ref_bits:
                chunk = text[pos : pos + match["length"]]
                op = {
                    "type": "self_ref",
                    "source_pos": match["source_pos"],
                    "length": match["length"],
                    "target_start": pos,
                }
                ops.append(op)
                refs.append({"component_id": component["id"], **op})
                previous_len = len(available)
                available += chunk
                add_index_entries(available, index, min_len, previous_len)
                pos += match["length"]
            else:
                chunk = text[pos]
                merge_literal_ops(ops, chunk)
                literal_digits += 1
                previous_len = len(available)
                available += chunk
                add_index_entries(available, index, min_len, previous_len)
                pos += 1
        recipes.append({"component_id": component["id"], "length": len(text), "ops": ops})
        previous_len = len(available)
        available += SEP
        add_index_entries(available, index, min_len, previous_len)

    literal_runs = sum(1 for recipe in recipes for op in recipe["ops"] if op["type"] == "literal")
    ref_count = len(refs)
    encoded_bits = (
        literal_digits * LOG2_10
        + literal_runs * literal_run_overhead
        + ref_count * ref_bits
    )
    emitted = ""
    errors = []
    for recipe, component in zip(recipes, components):
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
        if text != component["text"]:
            errors.append(component["id"])
        emitted += SEP

    return {
        "min_len": min_len,
        "max_ref_len": max_ref_len,
        "pos_bits": pos_bits,
        "len_bits": len_bits,
        "ref_bits": ref_bits,
        "literal_run_overhead_bits": literal_run_overhead,
        "baseline_digits": baseline_digits,
        "baseline_bits": baseline_bits,
        "encoded_bits": encoded_bits,
        "gain_bits": baseline_bits - encoded_bits,
        "literal_digits": literal_digits,
        "literal_runs": literal_runs,
        "reference_items": ref_count,
        "referenced_digits": sum(ref["length"] for ref in refs),
        "top_refs": sorted(refs, key=lambda row: row["length"], reverse=True)[:20],
        "recipes": recipes,
        "roundtrip_ok": not errors,
        "errors": errors,
    }


def best_encoding(
    components: list[dict],
    *,
    min_lens: list[int],
    max_ref_len: int,
    allow_current_component_refs: bool = True,
) -> dict:
    pos_bits = source_position_bits(components)
    len_bits = ceil_log2(max_ref_len + 1)
    encodings = [
        encode_components(
            components,
            min_len=min_len,
            max_ref_len=max_ref_len,
            pos_bits=pos_bits,
            len_bits=len_bits,
            allow_current_component_refs=allow_current_component_refs,
        )
        for min_len in min_lens
    ]
    encodings.sort(key=lambda row: (row["gain_bits"], row["referenced_digits"]), reverse=True)
    best = encodings[0]
    return {**best, "search_space": {"min_lens": min_lens, "max_ref_len": max_ref_len}}


def shuffled_components(components: list[dict], rng: random.Random) -> list[dict]:
    out = []
    for component in components:
        chars = list(component["text"])
        rng.shuffle(chars)
        out.append({**component, "text": "".join(chars)})
    return out


def random_components(components: list[dict], rng: random.Random) -> list[dict]:
    return [
        {**component, "text": "".join(str(rng.randrange(10)) for _ in range(len(component["text"])))}
        for component in components
    ]


def order_shuffled_components(components: list[dict], rng: random.Random) -> list[dict]:
    out = [dict(component) for component in components]
    rng.shuffle(out)
    return out


def summarize(values: list[float], observed: float) -> dict:
    return {
        "runs": len(values),
        "mean": mean(values),
        "sd": pstdev(values),
        "min": min(values),
        "max": max(values),
        "p_ge_observed": (sum(value >= observed for value in values) + 1) / (len(values) + 1),
    }


def run_controls(components: list[dict], observed_gain: float, min_lens: list[int], max_ref_len: int, runs: int) -> dict:
    component_shuffle = []
    random_same_lengths = []
    order_shuffle = []
    for seed in range(runs):
        rng = random.Random(469700 + seed)
        component_shuffle.append(
            best_encoding(
                shuffled_components(components, rng),
                min_lens=min_lens,
                max_ref_len=max_ref_len,
            )["gain_bits"]
        )
        random_same_lengths.append(
            best_encoding(
                random_components(components, rng),
                min_lens=min_lens,
                max_ref_len=max_ref_len,
            )["gain_bits"]
        )
        order_shuffle.append(
            best_encoding(
                order_shuffled_components(components, rng),
                min_lens=min_lens,
                max_ref_len=max_ref_len,
            )["gain_bits"]
        )
    return {
        "component_digit_shuffle": summarize(component_shuffle, observed_gain),
        "random_same_lengths": summarize(random_same_lengths, observed_gain),
        "component_order_shuffle": summarize(order_shuffle, observed_gain),
    }


def classify(best: dict, previous_only: dict, controls: dict) -> str:
    if not best["roundtrip_ok"]:
        return "invalid_roundtrip_errors"
    if best["gain_bits"] <= 0:
        return "no_inventory_self_reference_gain"
    if controls["component_digit_shuffle"]["p_ge_observed"] <= 0.01 and controls["random_same_lengths"]["p_ge_observed"] <= 0.01:
        if controls["component_order_shuffle"]["p_ge_observed"] <= 0.05:
            return "controlled_tape_inventory_self_reference_improvement"
        return "controlled_inventory_reuse_order_not_promoted"
    if previous_only["gain_bits"] > 0:
        return "candidate_inventory_self_reference_requires_stronger_controls"
    return "generic_compression_not_promoted"


def main() -> None:
    tape = load_json(TAPE_FORMULA)
    components = [
        {"id": component["id"], "text": component["text"], "length": len(component["text"])}
        for component in tape["tape_components"]
    ]
    min_lens = [6, 7, 8, 9, 10, 12, 15, 20]
    max_ref_len = 128
    best = best_encoding(
        components,
        min_lens=min_lens,
        max_ref_len=max_ref_len,
        allow_current_component_refs=True,
    )
    previous_only = best_encoding(
        components,
        min_lens=min_lens,
        max_ref_len=max_ref_len,
        allow_current_component_refs=False,
    )
    controls = run_controls(components, best["gain_bits"], min_lens, max_ref_len, runs=300)
    classification = classify(best, previous_only, controls)

    output_formula = {
        "schema": "tape_inventory_self_reference_formula.v1",
        "scope": "mechanical_generator_only_no_semantics",
        "source_formula": str(TAPE_FORMULA.relative_to(ROOT)),
        "translation_delta": "NONE",
        "policy": {
            "min_len": best["min_len"],
            "max_ref_len": max_ref_len,
            "pos_bits": best["pos_bits"],
            "len_bits": best["len_bits"],
            "reference_bits": best["ref_bits"],
            "literal_run_overhead_bits": best["literal_run_overhead_bits"],
            "component_order": [component["id"] for component in components],
        },
        "tape_component_recipes": best["recipes"],
        "validation": {
            "component_count": len(components),
            "components_roundtrip_ok": len(components) if best["roundtrip_ok"] else len(components) - len(best["errors"]),
            "errors": best["errors"],
        },
        "mdl_delta_rough": {
            "baseline_tape_inventory_bits": best["baseline_bits"],
            "self_reference_inventory_bits": best["encoded_bits"],
            "saved_bits": best["gain_bits"],
            "reference_items": best["reference_items"],
            "referenced_digits": best["referenced_digits"],
            "literal_digits": best["literal_digits"],
            "literal_runs": best["literal_runs"],
        },
    }
    OUT.write_text(json.dumps(output_formula, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result = {
        "schema": "tape_inventory_self_reference_search.v1",
        "test": "07_tape_inventory_self_reference_search",
        "classification": classification,
        "translation_delta": "NONE",
        "output_formula": str(OUT.relative_to(ROOT)),
        "input_formula": str(TAPE_FORMULA.relative_to(ROOT)),
        "best_encoding": {key: value for key, value in best.items() if key != "recipes"},
        "previous_components_only": {key: value for key, value in previous_only.items() if key != "recipes"},
        "controls": controls,
        "boundary": {
            "semantic_delta": "NONE",
            "pair_table_origin_explained": False,
            "authorial_intent_claim": False,
            "compression_note": "This is a tape-inventory generator refinement, not a plaintext model.",
        },
    }

    lines = [
        "# Tape Inventory Self-Reference Search",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This search asks whether the 16 tape components still contain a smaller",
        "mechanical inventory layer. It encodes each component as literal runs plus",
        "references to already emitted tape digits, charges source position and",
        "length bits, and lets the real corpus and every control choose the best",
        "minimum reference length from the same search set.",
        "",
        "## Best Real Encoding",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Min reference length | `{best['min_len']}` |",
        f"| Baseline tape inventory bits | `{best['baseline_bits']:.1f}` |",
        f"| Self-reference inventory bits | `{best['encoded_bits']:.1f}` |",
        f"| Rough saved bits | `{best['gain_bits']:.1f}` |",
        f"| Reference items | `{best['reference_items']}` |",
        f"| Referenced digits | `{best['referenced_digits']}` |",
        f"| Literal digits | `{best['literal_digits']}` |",
        f"| Literal runs | `{best['literal_runs']}` |",
        f"| Component roundtrip | `{best['roundtrip_ok']}` |",
        "",
        "## Previous-Component-Only Diagnostic",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Rough saved bits | `{previous_only['gain_bits']:.1f}` |",
        f"| Reference items | `{previous_only['reference_items']}` |",
        f"| Referenced digits | `{previous_only['referenced_digits']}` |",
        "",
        "## Negative Controls",
        "",
        "| Control | Runs | Mean saved bits | Max saved bits | p(>= observed) |",
        "|---|---:|---:|---:|---:|",
    ]
    for key, row in controls.items():
        lines.append(
            f"| `{key}` | `{row['runs']}` | `{row['mean']:.1f}` | "
            f"`{row['max']:.1f}` | `{row['p_ge_observed']:.4f}` |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "The result is a mechanical inventory refinement only. It does not explain",
            "the 10x10 pair-table placement, does not translate the books, and does",
            "not support private authorial-intent claims.",
        ]
    )
    write_result("07_tape_inventory_self_reference_search", result, lines)


if __name__ == "__main__":
    main()
