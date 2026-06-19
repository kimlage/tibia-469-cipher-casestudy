#!/usr/bin/env python3
"""Seven-segment orbit exception selector.

The broad visual-symmetry pass found that exact seven-segment 180-degree
rotation is the best visual MDL row, but still loses to raw lookup by a few
bits. This narrow follow-up asks whether its two mixed orbitals are selected by
a compact, human-readable rule instead of stored as arbitrary exceptions.

Mechanical only. No plaintext, glossary, or semantic translation is promoted.
"""

from __future__ import annotations

import itertools
import json
import math
import random
from collections import Counter
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FORMULA_JSON = ROOT / "analysis" / "mechanism_model_20260618" / "mechanical_formula_469.json"
VISUAL_JSON = HERE / "digit_visual_symmetry_results.json"

OUT_JSON = HERE / "sevenseg_orbit_exception_selector_results.json"
OUT_MD = HERE / "sevenseg_orbit_exception_selector_report.md"

SIGMA = list("*ABCEFILNORSTV")
RANDOM_SEED = 46920260619
CONTROL_TRIALS = 5000


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def primary_pair_symbol(pair_table: dict[str, Any], pair: str) -> str:
    row = pair_table[pair]
    if row["status"] == "pure":
        return row["symbol_if_pure"]
    return sorted(row["symbols"])[0]


SEGMENTS = {
    "0": set("abcdef"),
    "1": set("bc"),
    "2": set("abdeg"),
    "3": set("abcdg"),
    "4": set("bcfg"),
    "5": set("acdfg"),
    "6": set("acdefg"),
    "7": set("abc"),
    "8": set("abcdefg"),
    "9": set("abcdfg"),
}


def segment_features(digit: int) -> dict[str, Any]:
    segments = SEGMENTS[str(digit)]
    return {
        "segment_count": len(segments),
        "closed_loop": digit in {0, 6, 8, 9},
        "two_loops": digit == 8,
        "zero_or_eight": digit in {0, 8},
        "two_or_five": digit in {2, 5},
        "endpoint_fixed": digit in {0, 2, 5, 8},
        "even": digit % 2 == 0,
        "prime": digit in {2, 3, 5, 7},
        "edge_defined": digit in {0, 8},
        "middle_defined": digit in {2, 5},
    }


def build_orbit_rows(pair_table: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for anchor in [0, 2, 5, 6, 8]:
        if anchor == 6:
            pair6, pair9 = "66", "99"
        else:
            pair6 = "".join(sorted(f"{anchor}6"))
            pair9 = "".join(sorted(f"{anchor}9"))
        label6 = primary_pair_symbol(pair_table, pair6)
        label9 = primary_pair_symbol(pair_table, pair9)
        ordered = sorted([label6, label9], key=SIGMA.index)
        rows.append(
            {
                "anchor": anchor,
                "pair6": pair6,
                "pair9": pair9,
                "label6": label6,
                "label9": label9,
                "mixed": label6 != label9,
                "label_pair_sorted": ordered,
                "side6_is_low_symbol": label6 == ordered[0],
                "is_diagonal_orbit": anchor == 6,
                "anchor_distance_from_4_6_9": min(abs(anchor - digit) for digit in [4, 6, 9]),
                "anchor_in_469": anchor in {4, 6, 9},
                "anchor_in_3478": anchor in {3, 4, 7, 8},
                "anchor_in_39": anchor in {3, 9},
                "anchor_in_19": anchor in {1, 9},
                "anchor_in_33_66": anchor in {3, 6},
                **segment_features(anchor),
            }
        )
    return rows


def predicate_library(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    predicates: list[dict[str, Any]] = []

    def add(name: str, family: str, cost: float, fn) -> None:
        mask = [bool(fn(row)) for row in rows]
        if any(mask) and not all(mask):
            predicates.append({"name": name, "family": family, "cost": cost, "mask": mask})

    anchors = sorted(row["anchor"] for row in rows)
    for anchor in anchors:
        add(f"anchor_eq_{anchor}", "exact_anchor", 2.5, lambda row, value=anchor: row["anchor"] == value)
        add(f"anchor_le_{anchor}", "range", 1.6, lambda row, value=anchor: row["anchor"] <= value)
        add(f"anchor_ge_{anchor}", "range", 1.6, lambda row, value=anchor: row["anchor"] >= value)

    for modulus in [2, 3, 4, 5]:
        for residue in range(modulus):
            add(
                f"anchor_mod_{modulus}_{residue}",
                "modular",
                2.0,
                lambda row, m=modulus, r=residue: row["anchor"] % m == r,
            )

    for field in [
        "closed_loop",
        "two_loops",
        "zero_or_eight",
        "two_or_five",
        "endpoint_fixed",
        "even",
        "prime",
        "edge_defined",
        "middle_defined",
        "is_diagonal_orbit",
        "anchor_in_469",
        "anchor_in_3478",
        "anchor_in_39",
        "anchor_in_19",
        "anchor_in_33_66",
    ]:
        add(field, "glyph_or_lore_set", 1.8, lambda row, f=field: row[f])

    for field in ["segment_count", "anchor_distance_from_4_6_9"]:
        values = sorted({row[field] for row in rows})
        for value in values:
            add(f"{field}_eq_{value}", "numeric_glyph", 2.4, lambda row, f=field, v=value: row[f] == v)
            add(f"{field}_le_{value}", "numeric_glyph", 2.2, lambda row, f=field, v=value: row[f] <= v)
            add(f"{field}_ge_{value}", "numeric_glyph", 2.2, lambda row, f=field, v=value: row[f] >= v)

    base = [predicate for predicate in predicates if predicate["cost"] <= 2.2]
    for left_idx, left in enumerate(base):
        for right in base[left_idx + 1 :]:
            and_mask = [a and b for a, b in zip(left["mask"], right["mask"])]
            or_mask = [a or b for a, b in zip(left["mask"], right["mask"])]
            if any(and_mask) and not all(and_mask):
                predicates.append(
                    {
                        "name": f"and({left['name']},{right['name']})",
                        "family": "compound_and",
                        "cost": left["cost"] + right["cost"] + 0.8,
                        "mask": and_mask,
                    }
                )
            if any(or_mask) and not all(or_mask):
                predicates.append(
                    {
                        "name": f"or({left['name']},{right['name']})",
                        "family": "compound_or",
                        "cost": left["cost"] + right["cost"] + 0.8,
                        "mask": or_mask,
                    }
                )

    dedup: dict[tuple[bool, ...], dict[str, Any]] = {}
    for predicate in predicates:
        key = tuple(predicate["mask"])
        old = dedup.get(key)
        if old is None or predicate["cost"] < old["cost"] or (
            predicate["cost"] == old["cost"] and predicate["name"] < old["name"]
        ):
            dedup[key] = predicate
    return sorted(dedup.values(), key=lambda row: (row["cost"], row["name"]))


def score_predicate(predicate: dict[str, Any], target: list[bool]) -> dict[str, Any]:
    mask = predicate["mask"]
    tp = sum(m and t for m, t in zip(mask, target))
    fp = sum(m and not t for m, t in zip(mask, target))
    fn = sum((not m) and t for m, t in zip(mask, target))
    tn = sum((not m) and (not t) for m, t in zip(mask, target))
    return {
        **predicate,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "correct": tp + tn,
        "exact": fp == 0 and fn == 0,
        "predicted_true_count": sum(mask),
    }


def orientation_rules(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    mixed_rows = [row for row in rows if row["mixed"]]
    rules: list[dict[str, Any]] = []

    def add(name: str, family: str, cost: float, fn) -> None:
        predictions = [bool(fn(row)) for row in mixed_rows]
        correct = sum(pred == row["side6_is_low_symbol"] for pred, row in zip(predictions, mixed_rows))
        rules.append(
            {
                "name": name,
                "family": family,
                "cost": cost,
                "correct": correct,
                "total": len(mixed_rows),
                "predictions": predictions,
            }
        )

    add("side6_low_always", "constant", 0.3, lambda row: True)
    add("side6_high_always", "constant", 0.3, lambda row: False)
    add("side6_low_if_anchor_even", "parity", 1.0, lambda row: row["anchor"] % 2 == 0)
    add("side6_low_if_anchor_le_0", "range", 1.3, lambda row: row["anchor"] <= 0)
    add("side6_low_if_anchor_ge_8", "range", 1.3, lambda row: row["anchor"] >= 8)
    rules.sort(key=lambda row: (-row["correct"], row["cost"], row["name"]))
    return rules


def summarize_high(values: list[float], observed: float) -> dict[str, float]:
    mean = sum(values) / len(values)
    sd = (sum((value - mean) ** 2 for value in values) / (len(values) - 1)) ** 0.5
    return {
        "observed": observed,
        "mean": mean,
        "sd": sd,
        "min": min(values),
        "max": max(values),
        "p_good_direction": (sum(value >= observed for value in values) + 1) / (len(values) + 1),
    }


def summarize_low(values: list[float], observed: float) -> dict[str, float]:
    mean = sum(values) / len(values)
    sd = (sum((value - mean) ** 2 for value in values) / (len(values) - 1)) ** 0.5
    return {
        "observed": observed,
        "mean": mean,
        "sd": sd,
        "min": min(values),
        "max": max(values),
        "p_good_direction": (sum(value <= observed for value in values) + 1) / (len(values) + 1),
    }


def controls(
    predicates: list[dict[str, Any]],
    observed_selector: dict[str, Any],
    observed_orientation: dict[str, Any],
    mixed_count: int,
    orientation_true_count: int,
) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED)
    best_correct: list[float] = []
    best_exact_cost: list[float] = []
    orientation_correct: list[float] = []
    for _ in range(CONTROL_TRIALS):
        true_indexes = set(rng.sample(range(5), mixed_count))
        target = [idx in true_indexes for idx in range(5)]
        rows = [score_predicate(predicate, target) for predicate in predicates]
        best_correct.append(max(row["correct"] for row in rows))
        exact_costs = [row["cost"] for row in rows if row["exact"]]
        best_exact_cost.append(min(exact_costs) if exact_costs else 99.0)

        orientation_bits = [idx < orientation_true_count for idx in range(mixed_count)]
        rng.shuffle(orientation_bits)
        candidates = [
            [True for _ in range(mixed_count)],
            [False for _ in range(mixed_count)],
            [idx % 2 == 0 for idx in range(mixed_count)],
            [idx == 0 for idx in range(mixed_count)],
            [idx + 1 == mixed_count for idx in range(mixed_count)],
        ]
        orientation_correct.append(max(sum(a == b for a, b in zip(candidate, orientation_bits)) for candidate in candidates))

    return {
        "trials": CONTROL_TRIALS,
        "mixed_rule_correct": summarize_high(best_correct, observed_selector["correct"]),
        "mixed_rule_exact_cost": {
            **summarize_low(best_exact_cost, observed_selector["cost"]),
            "observed_cost": observed_selector["cost"],
            "control_min_cost": min(best_exact_cost),
            "control_mean_cost": sum(best_exact_cost) / len(best_exact_cost),
        },
        "orientation_rule_correct": summarize_high(orientation_correct, observed_orientation["correct"]),
    }


def mdl_estimate(
    visual_best: dict[str, Any],
    selector: dict[str, Any],
    orientation_rule: dict[str, Any],
    mixed_count: int,
) -> dict[str, Any]:
    lookup_bits = visual_best["lookup_cost_bits"]
    label_space = len(SIGMA) + 1  # includes the 19 I+N conflict label used by the visual pass.
    bits_per_label = math.log2(label_space)
    uniform_component_count = visual_best["components"] - mixed_count
    # Same orbit labels as the visual pass, but replace arbitrary exception
    # cell ids by a selector and an orientation rule. Mixed orbits still need
    # two unordered labels, because this test does not derive labels.
    model_bits = (
        visual_best["digit_map_choice_bits"] if "digit_map_choice_bits" in visual_best else math.log2(19)
    )
    model_bits += uniform_component_count * bits_per_label
    model_bits += mixed_count * math.log2(math.comb(label_space, 2))
    model_bits += selector["cost"] + orientation_rule["cost"]
    return {
        "raw_lookup_bits": lookup_bits,
        "visual_best_model_bits": visual_best["model_cost_bits"],
        "model_bits": model_bits,
        "gain_vs_raw_lookup_bits": lookup_bits - model_bits,
        "gain_vs_visual_best_bits": visual_best["model_cost_bits"] - model_bits,
        "lookup_cost_ratio": model_bits / lookup_bits,
        "components": {
            "uniform_component_label_bits": uniform_component_count * bits_per_label,
            "mixed_label_pair_bits": mixed_count * math.log2(math.comb(label_space, 2)),
            "selector_cost_bits": selector["cost"],
            "orientation_rule_cost_bits": orientation_rule["cost"],
        },
    }


def classify(selector: dict[str, Any], orientation: dict[str, Any], mdl: dict[str, Any], ctrl: dict[str, Any]) -> str:
    if (
        selector["exact"]
        and orientation["correct"] == orientation["total"]
        and mdl["gain_vs_raw_lookup_bits"] > 0
        and ctrl["mixed_rule_exact_cost"]["p_good_direction"] <= 0.01
    ):
        return "candidate_sevenseg_exception_selector"
    if selector["exact"] and orientation["correct"] == orientation["total"] and mdl["gain_vs_visual_best_bits"] > 0:
        return "weak_visual_exception_microfit_not_formula"
    return "rejected_control"


def write_report(result: dict[str, Any]) -> None:
    selector = result["best_selector"]
    orientation = result["best_orientation_rule"]
    mdl = result["mdl"]
    ctrl = result["controls"]
    lines = [
        "# Seven-Segment Orbit Exception Selector",
        "",
        "Generated by `sevenseg_orbit_exception_selector.py`.",
        "",
        "This is a narrow follow-up to the visual symmetry pass. It tests whether",
        "the two mixed orbitals under exact seven-segment 180-degree rotation are",
        "selected by a compact glyph/lore predicate rather than arbitrary lookup.",
        "It does not derive labels or assign plaintext.",
        "",
        "## Summary",
        "",
        "| Selector | Exact | Cost | Orientation rule | Orientation hits | MDL/lookup | Gain vs lookup | Gain vs visual row | p(selector cost) | Verdict |",
        "|---|---:|---:|---|---:|---:|---:|---:|---:|---|",
        f"| `{selector['name']}` | {selector['exact']} | {selector['cost']:.1f} | `{orientation['name']}` | {orientation['correct']}/{orientation['total']} | {mdl['lookup_cost_ratio']:.3f} | {mdl['gain_vs_raw_lookup_bits']:.1f} | {mdl['gain_vs_visual_best_bits']:.1f} | {ctrl['mixed_rule_exact_cost']['p_good_direction']:.4f} | `{result['verdict']}` |",
        "",
        "## Orbit Rows",
        "",
        "| Anchor | pair6 | label6 | pair9 | label9 | Mixed | side6 low? |",
        "|---:|---|---|---|---|---|---|",
    ]
    for row in result["orbit_rows"]:
        lines.append(
            f"| {row['anchor']} | `{row['pair6']}` | `{row['label6']}` | `{row['pair9']}` | `{row['label9']}` | `{row['mixed']}` | `{row['side6_is_low_symbol']}` |"
        )
    lines.extend(
        [
            "",
            "## Top Selector Rules",
            "",
            "| Rule | Family | Cost | Correct | TP | FP | FN | Exact |",
            "|---|---|---:|---:|---:|---:|---:|---|",
        ]
    )
    for row in result["top_selectors"][:20]:
        lines.append(
            f"| `{row['name']}` | `{row['family']}` | {row['cost']:.1f} | {row['correct']}/5 | {row['tp']} | {row['fp']} | {row['fn']} | `{row['exact']}` |"
        )
    lines.extend(
        [
            "",
            "## Controls",
            "",
            f"- Selector exact-cost p: `{ctrl['mixed_rule_exact_cost']['p_good_direction']:.5f}`.",
            f"- Orientation p: `{ctrl['orientation_rule_correct']['p_good_direction']:.5f}`.",
            "",
            "## Interpretation",
            "",
            "The observed mixed orbitals are exactly the `0` and `8` anchors:",
            "`06/09` and `68/89`. That is a compact glyph rule, but the target has",
            "only five orbitals and controls often find equally cheap exact selectors",
            "over two-of-five subsets. It improves the prior visual row slightly but",
            "does not become an original pair-table formula.",
            "",
            f"Translation delta: `{result['translation_delta']}`.",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    formula = load_json(FORMULA_JSON)
    visual = load_json(VISUAL_JSON)
    visual_best = visual["observed_best_by_mdl"]
    rows = build_orbit_rows(formula["pair_table"])
    predicates = predicate_library(rows)
    target = [row["mixed"] for row in rows]
    selector_scores = [score_predicate(predicate, target) for predicate in predicates]
    selector_scores.sort(key=lambda row: (-int(row["exact"]), -row["correct"], row["cost"], row["name"]))
    orientations = orientation_rules(rows)
    best_selector = selector_scores[0]
    best_orientation = orientations[0]
    mixed_count = sum(target)
    orientation_true_count = sum(row["side6_is_low_symbol"] for row in rows if row["mixed"])
    ctrl = controls(predicates, best_selector, best_orientation, mixed_count, orientation_true_count)
    mdl = mdl_estimate(visual_best, best_selector, best_orientation, mixed_count)
    result = {
        "schema": "sevenseg_orbit_exception_selector_results.v1",
        "source": str(FORMULA_JSON.relative_to(ROOT)),
        "visual_source": str(VISUAL_JSON.relative_to(ROOT)),
        "translation_delta": "NONE",
        "new_plaintext": False,
        "orbit_rows": rows,
        "best_selector": best_selector,
        "best_orientation_rule": best_orientation,
        "top_selectors": selector_scores[:80],
        "top_orientation_rules": orientations,
        "controls": ctrl,
        "mdl": mdl,
        "verdict": classify(best_selector, best_orientation, mdl, ctrl),
    }
    write_json(OUT_JSON, result)
    write_report(result)
    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(
        "selector={selector} gain={gain:.1f} p={p:.5f} verdict={verdict}".format(
            selector=best_selector["name"],
            gain=mdl["gain_vs_raw_lookup_bits"],
            p=ctrl["mixed_rule_exact_cost"]["p_good_direction"],
            verdict=result["verdict"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
