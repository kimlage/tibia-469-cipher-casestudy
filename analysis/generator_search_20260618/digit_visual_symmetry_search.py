#!/usr/bin/env python3
"""Visual 6/9 symmetry search for the 469 pair table.

This pass tests a narrow origin hypothesis: the 55 unordered digit-pair cells
may have been assigned by visual/geometric transformations involving the
digits 6 and 9. Candidate transforms include seven-segment rotation/mirrors,
numpad rotation/mirrors, clock/circle rotation/mirrors, and a direct 6<->9
swap. The score is compression-oriented: a useful symmetry should group pair
cells into same-label orbits and beat a raw lookup after a rough MDL penalty.

Controls preserve the exact 55-cell label inventory and shuffle labels across
cells, then let each shuffled table choose its own best visual transform. This
keeps the verdict conservative.

Mechanical only. No plaintext, glossary, or translation is promoted.
"""

from __future__ import annotations

import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FORMULA_JSON = ROOT / "analysis" / "mechanism_model_20260618" / "mechanical_formula_469.json"

OUT_JSON = HERE / "digit_visual_symmetry_results.json"
OUT_MD = HERE / "digit_visual_symmetry_report.md"

RANDOM_SEED = 46920260618
TRIALS = 5000
DIGITS = "0123456789"
TARGET_CODES = ["19", "91", "39", "93", "33", "66"]

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

SEGMENT_TRANSFORMS = {
    "rotate180": {"a": "d", "b": "e", "c": "f", "d": "a", "e": "b", "f": "c", "g": "g"},
    "mirror_vertical": {"a": "a", "b": "f", "c": "e", "d": "d", "e": "c", "f": "b", "g": "g"},
    "mirror_horizontal": {"a": "d", "b": "c", "c": "b", "d": "a", "e": "f", "f": "e", "g": "g"},
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def pair_cells() -> list[str]:
    return [f"{a}{b}" for a in range(10) for b in range(a, 10)]


CELLS = pair_cells()
CELL_SET = set(CELLS)


def unordered_pair(code: str) -> str:
    return "".join(sorted(code))


def label_key(row: dict[str, Any]) -> str:
    return "+".join(sorted(row["symbols"]))


def transform_pair(pair: str, digit_map: dict[str, str | None]) -> str | None:
    a = digit_map.get(pair[0])
    b = digit_map.get(pair[1])
    if a is None or b is None:
        return None
    return unordered_pair(f"{a}{b}")


def transform_ordered_code(code: str, digit_map: dict[str, str | None]) -> str | None:
    a = digit_map.get(code[0])
    b = digit_map.get(code[1])
    if a is None or b is None:
        return None
    return f"{a}{b}"


class DSU:
    def __init__(self, items: list[str]) -> None:
        self.parent = {item: item for item in items}

    def find(self, item: str) -> str:
        parent = self.parent[item]
        if parent != item:
            self.parent[item] = self.find(parent)
        return self.parent[item]

    def union(self, left: str, right: str) -> None:
        root_left = self.find(left)
        root_right = self.find(right)
        if root_left != root_right:
            self.parent[root_right] = root_left

    def components(self) -> list[list[str]]:
        grouped: dict[str, list[str]] = defaultdict(list)
        for item in self.parent:
            grouped[self.find(item)].append(item)
        return [sorted(values) for values in grouped.values()]


def seven_segment_digit_map(mode: str, projection: str) -> tuple[dict[str, str | None], dict[str, Any]]:
    segment_map = SEGMENT_TRANSFORMS[mode]
    out: dict[str, str | None] = {}
    distances: dict[str, Any] = {}
    for digit, segments in SEGMENTS.items():
        transformed = {segment_map[segment] for segment in segments}
        exact = [candidate for candidate, candidate_segments in SEGMENTS.items() if candidate_segments == transformed]
        if exact:
            out[digit] = exact[0]
            distances[digit] = {"target": exact[0], "distance": 0, "projection": "exact"}
            continue
        if projection == "exact":
            out[digit] = None
            distances[digit] = {"target": None, "distance": None, "projection": "undefined"}
            continue
        scored = []
        for candidate, candidate_segments in SEGMENTS.items():
            distance = len(transformed ^ candidate_segments)
            scored.append((distance, candidate))
        scored.sort()
        best_distance = scored[0][0]
        best_candidates = [candidate for distance, candidate in scored if distance == best_distance]
        if len(best_candidates) == 1 and best_distance <= 2:
            out[digit] = best_candidates[0]
            distances[digit] = {"target": best_candidates[0], "distance": best_distance, "projection": "nearest_unique_le2"}
        else:
            out[digit] = None
            distances[digit] = {
                "target": None,
                "distance": best_distance,
                "projection": "ambiguous_or_far",
                "candidates": best_candidates,
            }
    return out, distances


def numpad_digit_map(mode: str, zero_policy: str) -> dict[str, str | None]:
    coords = {
        "7": (0, 0),
        "8": (1, 0),
        "9": (2, 0),
        "4": (0, 1),
        "5": (1, 1),
        "6": (2, 1),
        "1": (0, 2),
        "2": (1, 2),
        "3": (2, 2),
        "0": (1, 3),
    }
    by_coord = {coord: digit for digit, coord in coords.items()}

    def apply(coord: tuple[int, int]) -> tuple[int, int]:
        x, y = coord
        if mode == "rotate180":
            return 2 - x, 2 - y
        if mode == "mirror_vertical":
            return 2 - x, y
        if mode == "mirror_horizontal":
            return x, 2 - y
        raise ValueError(mode)

    out: dict[str, str | None] = {}
    for digit, coord in coords.items():
        target = by_coord.get(apply(coord))
        if target is None and digit == "0" and zero_policy == "zero_fixed":
            target = "0"
        out[digit] = target
    return out


def clock_digit_map(order: str, mode: str) -> dict[str, str]:
    n = len(order)
    out = {}
    for idx, digit in enumerate(order):
        if mode == "rotate180":
            target_idx = (idx + n // 2) % n
        elif mode == "mirror_vertical":
            target_idx = (-idx) % n
        elif mode == "mirror_horizontal":
            target_idx = (n // 2 - idx) % n
        else:
            raise ValueError(mode)
        out[digit] = order[target_idx]
    return out


def identity_with_swaps(*swaps: tuple[str, str]) -> dict[str, str]:
    out = {digit: digit for digit in DIGITS}
    for left, right in swaps:
        out[left], out[right] = out[right], out[left]
    return out


def candidate_transforms() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = [
        {
            "id": "local_swap_6_9_identity_else",
            "family": "six_nine_specific",
            "digit_map": identity_with_swaps(("6", "9")),
            "note": "Direct local 6<->9 visual rotation hypothesis; all other digits fixed.",
        }
    ]

    for mode in ["rotate180", "mirror_vertical", "mirror_horizontal"]:
        for projection in ["exact", "nearest"]:
            digit_map, distances = seven_segment_digit_map(mode, projection)
            rows.append(
                {
                    "id": f"sevenseg_{mode}_{projection}",
                    "family": "seven_segment",
                    "digit_map": digit_map,
                    "segment_projection": distances,
                    "note": "Seven-segment visual transform; nearest mode is conservative only when unique and distance <= 2.",
                }
            )

    for mode in ["rotate180", "mirror_vertical", "mirror_horizontal"]:
        policies = ["strict"]
        if mode in {"rotate180", "mirror_horizontal"}:
            policies.append("zero_fixed")
        for zero_policy in policies:
            rows.append(
                {
                    "id": f"numpad_{mode}_{zero_policy}",
                    "family": "numpad",
                    "digit_map": numpad_digit_map(mode, zero_policy),
                    "note": "Numpad transform over the 1..9 grid; strict leaves 0 undefined when no opposite key exists.",
                }
            )

    for order in ["0123456789", "1234567890"]:
        for mode in ["rotate180", "mirror_vertical", "mirror_horizontal"]:
            rows.append(
                {
                    "id": f"clock_{order}_{mode}",
                    "family": "clock",
                    "digit_map": clock_digit_map(order, mode),
                    "note": "Digits placed on a 10-position clock/circle in the listed order.",
                }
            )

    rows.append(
        {
            "id": "overlay_swap_3_6_identity_else",
            "family": "required_overlay_control",
            "digit_map": identity_with_swaps(("3", "6")),
            "note": "Control overlay for the required 33/66 check; not a 6/9 generator claim.",
        }
    )
    return rows


def component_rows(digit_map: dict[str, str | None]) -> tuple[list[list[str]], dict[str, str | None]]:
    dsu = DSU(CELLS)
    targets: dict[str, str | None] = {}
    for cell in CELLS:
        target = transform_pair(cell, digit_map)
        if target in CELL_SET and target != cell:
            dsu.union(cell, target)
        targets[cell] = target if target in CELL_SET else None
    return dsu.components(), targets


def score_transform(
    transform: dict[str, Any],
    labels: dict[str, str],
    label_space_size: int,
    rule_choice_bits: float,
) -> dict[str, Any]:
    components, targets = component_rows(transform["digit_map"])
    bits_per_label = math.log2(label_space_size)
    bits_per_exception = math.log2(len(CELLS)) + bits_per_label
    lookup_bits = len(CELLS) * bits_per_label

    total_hits = 0
    total_errors = 0
    nontrivial_cells = 0
    nontrivial_hits = 0
    nontrivial_errors = 0
    component_summaries = []

    for component in components:
        counts = Counter(labels[cell] for cell in component)
        majority_label, majority_hits = counts.most_common(1)[0]
        errors = len(component) - majority_hits
        total_hits += majority_hits
        total_errors += errors
        if len(component) > 1:
            nontrivial_cells += len(component)
            nontrivial_hits += majority_hits
            nontrivial_errors += errors
            component_summaries.append(
                {
                    "cells": component,
                    "labels": dict(sorted(counts.items())),
                    "majority_label": majority_label,
                    "hits": majority_hits,
                    "errors": errors,
                }
            )

    edge_total = 0
    edge_hits = 0
    edge_mismatches = []
    mapped_cells = 0
    for cell in CELLS:
        target = targets[cell]
        if target is None:
            continue
        mapped_cells += 1
        if target == cell:
            continue
        edge_total += 1
        if labels[cell] == labels[target]:
            edge_hits += 1
        elif len(edge_mismatches) < 20:
            edge_mismatches.append(
                {
                    "cell": cell,
                    "target": target,
                    "source_label": labels[cell],
                    "target_label": labels[target],
                }
            )

    model_bits = rule_choice_bits + len(components) * bits_per_label + total_errors * bits_per_exception
    return {
        "id": transform["id"],
        "family": transform["family"],
        "note": transform["note"],
        "digit_map": transform["digit_map"],
        "mapped_cells": mapped_cells,
        "components": len(components),
        "nontrivial_components": sum(1 for component in components if len(component) > 1),
        "nontrivial_cells": nontrivial_cells,
        "nontrivial_hits": nontrivial_hits,
        "nontrivial_errors": nontrivial_errors,
        "nontrivial_accuracy": (nontrivial_hits / nontrivial_cells) if nontrivial_cells else None,
        "majority_hits": total_hits,
        "majority_errors": total_errors,
        "majority_accuracy": total_hits / len(CELLS),
        "edge_total": edge_total,
        "edge_hits": edge_hits,
        "edge_accuracy": (edge_hits / edge_total) if edge_total else None,
        "lookup_cost_bits": lookup_bits,
        "model_cost_bits": model_bits,
        "model_cost_gain_bits": lookup_bits - model_bits,
        "best_nontrivial_components": sorted(
            component_summaries,
            key=lambda row: (-len(row["cells"]), row["errors"], row["cells"]),
        )[:20],
        "edge_mismatches_sample": edge_mismatches,
    }


def best_by_mdl(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return sorted(
        rows,
        key=lambda row: (
            -row["model_cost_gain_bits"],
            -row["majority_hits"],
            -row["nontrivial_cells"],
            row["id"],
        ),
    )[0]


def best_by_hits(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return sorted(
        rows,
        key=lambda row: (
            -row["nontrivial_hits"],
            -(row["nontrivial_accuracy"] if row["nontrivial_accuracy"] is not None else -1),
            -row["edge_hits"],
            row["model_cost_bits"],
            row["id"],
        ),
    )[0]


def summarize_high(values: list[float], observed: float) -> dict[str, float]:
    mean = sum(values) / len(values)
    sd = (sum((value - mean) ** 2 for value in values) / (len(values) - 1)) ** 0.5
    return {
        "observed": observed,
        "control_mean": mean,
        "control_sd": sd,
        "control_min": min(values),
        "control_max": max(values),
        "z_good_direction": (observed - mean) / sd if sd else 0.0,
        "p_good_direction": (sum(value >= observed for value in values) + 1) / (len(values) + 1),
    }


def code_overlay(code: str, formula: dict[str, Any], labels: dict[str, str]) -> dict[str, Any]:
    code_to_symbol = formula["code_to_symbol"]
    pair = unordered_pair(code)
    return {
        "code": code,
        "ordered_symbol": code_to_symbol.get(code),
        "ordered_code_present": code in code_to_symbol,
        "unordered_pair": pair,
        "unordered_pair_label": labels[pair],
        "unordered_pair_status": formula["pair_table"][pair]["status"],
    }


def required_overlays(formula: dict[str, Any], labels: dict[str, str]) -> list[dict[str, Any]]:
    rows = []
    rows.append(
        {
            "id": "19_91_ordered_reversal",
            "codes": [code_overlay("19", formula, labels), code_overlay("91", formula, labels)],
            "observation": "19 and 91 are both present but map to different ordered symbols; the unordered pair cell is a conflict label.",
            "interpretation": "This is an exception to simple unordered visual symmetry, not a plaintext clue.",
        }
    )
    rows.append(
        {
            "id": "39_absent_93_present",
            "codes": [code_overlay("39", formula, labels), code_overlay("93", formula, labels)],
            "observation": "39 is absent from the ordered code table while 93 is present; the unordered pair cell 39 exists through 93.",
            "interpretation": "This is an omission/orientation fact, not evidence for a complete 55-cell visual formula.",
        }
    )
    rows.append(
        {
            "id": "33_66_same_pair_label",
            "codes": [code_overlay("33", formula, labels), code_overlay("66", formula, labels)],
            "observation": "33 and 66 share the same pair label in the mechanical table.",
            "interpretation": "The equality is tracked as a visual overlay candidate and tested against controls.",
        }
    )
    return rows


def transform_overlay_trace(transform: dict[str, Any], formula: dict[str, Any], labels: dict[str, str]) -> dict[str, Any]:
    traces = []
    for code in TARGET_CODES:
        target_code = transform_ordered_code(code, transform["digit_map"])
        target_pair = unordered_pair(target_code) if target_code is not None else None
        traces.append(
            {
                "code": code,
                "ordered_symbol": formula["code_to_symbol"].get(code),
                "target_code": target_code,
                "target_ordered_symbol": formula["code_to_symbol"].get(target_code) if target_code is not None else None,
                "target_pair": target_pair,
                "source_pair_label": labels[unordered_pair(code)],
                "target_pair_label": labels[target_pair] if target_pair in labels else None,
                "pair_label_preserved": labels[unordered_pair(code)] == labels[target_pair] if target_pair in labels else None,
            }
        )
    return {"transform_id": transform["id"], "family": transform["family"], "traces": traces}


def run_controls(
    labels: dict[str, str],
    transforms: list[dict[str, Any]],
    label_space_size: int,
    rule_choice_bits: float,
    observed_mdl_best: dict[str, Any],
    observed_hit_best: dict[str, Any],
) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED)
    label_values = [labels[cell] for cell in CELLS]
    control_best_gain = []
    control_best_hits = []
    control_best_edge_hits = []
    control_best_edge_accuracy = []

    shuffled = label_values[:]
    for _trial in range(TRIALS):
        rng.shuffle(shuffled)
        shuffled_labels = {cell: label for cell, label in zip(CELLS, shuffled)}
        rows = [score_transform(transform, shuffled_labels, label_space_size, rule_choice_bits) for transform in transforms]
        mdl_row = best_by_mdl(rows)
        hit_row = best_by_hits(rows)
        control_best_gain.append(mdl_row["model_cost_gain_bits"])
        control_best_hits.append(hit_row["nontrivial_hits"])
        control_best_edge_hits.append(hit_row["edge_hits"])
        control_best_edge_accuracy.append(hit_row["edge_accuracy"] or 0.0)

    return {
        "trials": TRIALS,
        "random_seed": RANDOM_SEED,
        "label_shuffle": "preserves exact 55-cell label multiset, including the 19 conflict label",
        "best_mdl_gain_bits": summarize_high(control_best_gain, observed_mdl_best["model_cost_gain_bits"]),
        "best_nontrivial_hits": summarize_high(control_best_hits, observed_hit_best["nontrivial_hits"]),
        "best_edge_hits": summarize_high(control_best_edge_hits, observed_hit_best["edge_hits"]),
        "best_edge_accuracy": summarize_high(control_best_edge_accuracy, observed_hit_best["edge_accuracy"] or 0.0),
    }


def verdict(observed_mdl_best: dict[str, Any], controls: dict[str, Any]) -> str:
    if (
        observed_mdl_best["model_cost_gain_bits"] > 0
        and observed_mdl_best["nontrivial_cells"] >= 20
        and (observed_mdl_best["nontrivial_accuracy"] or 0.0) >= 0.75
        and controls["best_mdl_gain_bits"]["p_good_direction"] <= 0.01
    ):
        return "candidate_visual_symmetry_generator_needs_independent_evidence"
    return "reject_visual_6_9_symmetry_as_pair_matrix_formula"


def markdown_table_row(row: dict[str, Any]) -> str:
    nontriv_acc = "n/a" if row["nontrivial_accuracy"] is None else f"{row['nontrivial_accuracy']:.3f}"
    edge_acc = "n/a" if row["edge_accuracy"] is None else f"{row['edge_accuracy']:.3f}"
    return (
        f"| `{row['id']}` | `{row['family']}` | {row['nontrivial_hits']}/{row['nontrivial_cells']} "
        f"({nontriv_acc}) | {row['edge_hits']}/{row['edge_total']} ({edge_acc}) | "
        f"{row['majority_hits']}/55 | {row['model_cost_bits']:.1f} | {row['model_cost_gain_bits']:.1f} |"
    )


def write_report(result: dict[str, Any]) -> None:
    observed_mdl = result["observed_best_by_mdl"]
    observed_hits = result["observed_best_by_hits"]
    controls = result["controls"]
    rows = result["transform_rows"]

    lines = [
        "# Digit Visual Symmetry Search",
        "",
        "Generated by `digit_visual_symmetry_search.py`.",
        "",
        "Scope: mechanical generator-origin testing only. This pass tests whether",
        "the 55 unordered pair cells can be compressed by visual transformations",
        "centered on 6/9-style geometry: 180-degree rotation, vertical/horizontal",
        "mirrors, seven-segment projections, numpad geometry, and clock/circle",
        "geometry. It does not assign plaintext or promote a glossary.",
        "",
        f"- Source: `{result['source']}`",
        f"- Translation delta: `{result['translation_delta']}`",
        f"- Label-shuffle controls: {controls['trials']} trials, seed `{controls['random_seed']}`",
        "",
        "## Best Results",
        "",
        "| Selection | Transform | Nontrivial orbit hits | Edge hits | Total majority hits | MDL bits | Gain vs lookup | Control p |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
        (
            f"| Best MDL | `{observed_mdl['id']}` | {observed_mdl['nontrivial_hits']}/{observed_mdl['nontrivial_cells']} | "
            f"{observed_mdl['edge_hits']}/{observed_mdl['edge_total']} | {observed_mdl['majority_hits']}/55 | "
            f"{observed_mdl['model_cost_bits']:.1f} | {observed_mdl['model_cost_gain_bits']:.1f} | "
            f"{controls['best_mdl_gain_bits']['p_good_direction']:.4f} |"
        ),
        (
            f"| Best hits | `{observed_hits['id']}` | {observed_hits['nontrivial_hits']}/{observed_hits['nontrivial_cells']} | "
            f"{observed_hits['edge_hits']}/{observed_hits['edge_total']} | {observed_hits['majority_hits']}/55 | "
            f"{observed_hits['model_cost_bits']:.1f} | {observed_hits['model_cost_gain_bits']:.1f} | "
            f"{controls['best_nontrivial_hits']['p_good_direction']:.4f} |"
        ),
        "",
        "Lookup baseline is the rough cost of storing one label for each of the",
        "55 pair cells. A visual rule only helps if its orbit labels plus",
        "exceptions cost less than that baseline and also beat shuffled-label",
        "tables that are allowed to choose their own best transform.",
        "",
        "## Top Transform Rows",
        "",
        "| Transform | Family | Nontrivial orbit hits | Edge hits | Total majority hits | MDL bits | Gain vs lookup |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in rows[:12]:
        lines.append(markdown_table_row(row))

    lines.extend(
        [
            "",
            "## Required Overlays",
            "",
            "| Overlay | Ordered facts | Pair-cell fact | Interpretation |",
            "|---|---|---|---|",
        ]
    )
    for overlay in result["required_overlays"]:
        facts = []
        for code_row in overlay["codes"]:
            symbol = code_row["ordered_symbol"] if code_row["ordered_symbol"] is not None else "ABSENT"
            facts.append(f"{code_row['code']}={symbol}")
        pair_facts = ", ".join(
            f"{code_row['unordered_pair']}={code_row['unordered_pair_label']}" for code_row in overlay["codes"]
        )
        lines.append(
            f"| `{overlay['id']}` | `{', '.join(facts)}` | `{pair_facts}` | {overlay['interpretation']} |"
        )

    lines.extend(
        [
            "",
            "## Control Summary",
            "",
            "| Metric | Observed | Control mean | Control max | p(good direction) |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for key, label in [
        ("best_mdl_gain_bits", "Best MDL gain bits"),
        ("best_nontrivial_hits", "Best nontrivial hits"),
        ("best_edge_hits", "Best edge hits"),
        ("best_edge_accuracy", "Best edge accuracy"),
    ]:
        row = controls[key]
        lines.append(
            f"| {label} | {row['observed']:.3f} | {row['control_mean']:.3f} | "
            f"{row['control_max']:.3f} | {row['p_good_direction']:.4f} |"
        )

    lines.extend(
        [
            "",
            "## Verdict",
            "",
            f"`{result['verdict']}`.",
            "",
            "The required overlays are real mechanical facts worth keeping in the",
            "audit trail, especially 19/91 as an ordered conflict, 39 as an",
            "ordered omission with 93 present, and the 33/66 same-label check.",
            "They do not combine into a compact visual 6/9 formula for the 55-cell",
            "pair matrix. This is a useful rejection, not a translation result.",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    formula = load_json(FORMULA_JSON)
    labels = {cell: label_key(formula["pair_table"][cell]) for cell in CELLS}
    label_space_size = len(set(labels.values()))
    transforms = candidate_transforms()
    rule_choice_bits = math.log2(len(transforms) + 1)
    rows = [score_transform(transform, labels, label_space_size, rule_choice_bits) for transform in transforms]
    rows.sort(
        key=lambda row: (
            -row["model_cost_gain_bits"],
            -row["majority_hits"],
            -row["nontrivial_hits"],
            row["id"],
        )
    )

    observed_mdl_best = best_by_mdl(rows)
    observed_hit_best = best_by_hits(rows)
    controls = run_controls(labels, transforms, label_space_size, rule_choice_bits, observed_mdl_best, observed_hit_best)
    final_verdict = verdict(observed_mdl_best, controls)
    transform_by_id = {transform["id"]: transform for transform in transforms}

    result = {
        "schema": "digit_visual_symmetry_results.v1",
        "source": str(FORMULA_JSON.relative_to(ROOT)),
        "translation_delta": "NONE",
        "hypothesis": "55 unordered pair cells explained by visual/geometric transformations around 6 and 9",
        "random_seed": RANDOM_SEED,
        "trials": TRIALS,
        "label_space": sorted(set(labels.values())),
        "label_counts": dict(sorted(Counter(labels.values()).items())),
        "lookup_cost_bits": observed_mdl_best["lookup_cost_bits"],
        "rule_choice_bits": rule_choice_bits,
        "observed_best_by_mdl": observed_mdl_best,
        "observed_best_by_hits": observed_hit_best,
        "transform_rows": rows,
        "required_overlays": required_overlays(formula, labels),
        "overlay_traces": [
            transform_overlay_trace(transform_by_id[row["id"]], formula, labels)
            for row in rows[:8]
        ],
        "controls": controls,
        "verdict": final_verdict,
        "scope_guard": {
            "plaintext_promoted": False,
            "glossary_created": False,
            "docs_updated": False,
            "generator_search_suite_touched": False,
        },
    }
    write_json(OUT_JSON, result)
    write_report(result)

    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(f"wrote {OUT_MD.relative_to(ROOT)}")
    print(
        "verdict={verdict} best_mdl={best} gain={gain:.2f} p={p:.4f}".format(
            verdict=final_verdict,
            best=observed_mdl_best["id"],
            gain=observed_mdl_best["model_cost_gain_bits"],
            p=controls["best_mdl_gain_bits"]["p_good_direction"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
