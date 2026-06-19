#!/usr/bin/env python3
"""Colored graph motif search for the 469 pair table.

The 55 unordered digit cells are treated as a complete graph on digits 0..9
with loops. Each cell receives the primary symbol/color from the frozen
mechanical formula. This pass searches for graph motifs beyond the incidence
degree checks: triangles, wedges, 3-stars, simple paths of length 2 and 3,
same-color spectral-radius summaries, and digit orbit counts.

The control is an inventory-preserving shuffle of the 55 cell labels. This is
mechanical-only evidence. It does not translate 469 and does not promote a
formula without a predictive/MDL gain.
"""

from __future__ import annotations

import argparse
import json
import math
import random
from collections import Counter
from itertools import combinations, permutations
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FORMULA_JSON = ROOT / "analysis" / "mechanism_model_20260618" / "mechanical_formula_469.json"

OUT_JSON = HERE / "pair_graph_motif_results.json"
OUT_MD = HERE / "pair_graph_motif_report.md"

RANDOM_SEED = 46920260619
CONTROL_TRIALS = 2000
DIGITS = list(range(10))

PAIRS = [(i, j) for i in DIGITS for j in range(i, 10)]
PAIR_NAMES = [f"{i}{j}" for i, j in PAIRS]
PAIR_INDEX = {pair: index for index, pair in enumerate(PAIRS)}

TRIANGLES = [
    (
        PAIR_INDEX[(a, b)],
        PAIR_INDEX[(a, c)],
        PAIR_INDEX[(b, c)],
        (a, b, c),
    )
    for a, b, c in combinations(DIGITS, 3)
]

WEDGES = []
for center in DIGITS:
    for left, right in combinations([digit for digit in DIGITS if digit != center], 2):
        WEDGES.append(
            (
                center,
                PAIR_INDEX[tuple(sorted((center, left)))],
                PAIR_INDEX[tuple(sorted((center, right)))],
                (left, right),
            )
        )

STARS3 = []
for center in DIGITS:
    for leaves in combinations([digit for digit in DIGITS if digit != center], 3):
        STARS3.append(
            (
                center,
                tuple(PAIR_INDEX[tuple(sorted((center, leaf)))] for leaf in leaves),
                leaves,
            )
        )

PATH2 = [
    (
        a,
        b,
        c,
        PAIR_INDEX[tuple(sorted((a, b)))],
        PAIR_INDEX[tuple(sorted((b, c)))],
    )
    for a, b, c in permutations(DIGITS, 3)
]

PATH3 = [
    (
        a,
        b,
        c,
        d,
        PAIR_INDEX[tuple(sorted((a, b)))],
        PAIR_INDEX[tuple(sorted((b, c)))],
        PAIR_INDEX[tuple(sorted((c, d)))],
    )
    for a, b, c, d in permutations(DIGITS, 4)
]


METRIC_SPECS = [
    {
        "metric": "triangles_mono_total",
        "family": "triangles",
        "direction": "high",
        "description": "monochrome triangles over distinct digits",
        "explainability": 0.55,
    },
    {
        "metric": "triangles_three_color_total",
        "family": "triangles",
        "direction": "low",
        "description": "3-color triangles over distinct digits",
        "explainability": 0.55,
    },
    {
        "metric": "triangles_pattern_entropy",
        "family": "triangles",
        "direction": "low",
        "description": "entropy of triangle color-pattern counts",
        "explainability": 0.45,
    },
    {
        "metric": "orbit_triangle_mono_l2",
        "family": "orbits",
        "direction": "high",
        "description": "digit imbalance of monochrome-triangle vertex orbits",
        "explainability": 0.50,
    },
    {
        "metric": "wedges_same_total",
        "family": "wedges",
        "direction": "high",
        "description": "same-color length-2 wedges by center",
        "explainability": 0.60,
    },
    {
        "metric": "wedges_same_center_l2",
        "family": "wedges",
        "direction": "high",
        "description": "center-digit imbalance in same-color wedges",
        "explainability": 0.55,
    },
    {
        "metric": "wedges_same_leaf_l2",
        "family": "orbits",
        "direction": "high",
        "description": "leaf-digit imbalance in same-color wedges",
        "explainability": 0.45,
    },
    {
        "metric": "star3_mono_total",
        "family": "stars3",
        "direction": "high",
        "description": "3-edge stars whose three cells have one color",
        "explainability": 0.60,
    },
    {
        "metric": "star3_three_color_total",
        "family": "stars3",
        "direction": "low",
        "description": "3-edge stars whose three cells have three colors",
        "explainability": 0.55,
    },
    {
        "metric": "star3_pattern_entropy",
        "family": "stars3",
        "direction": "low",
        "description": "entropy of 3-star color-pattern counts",
        "explainability": 0.45,
    },
    {
        "metric": "star3_mono_center_l2",
        "family": "orbits",
        "direction": "high",
        "description": "center-digit imbalance in monochrome 3-stars",
        "explainability": 0.50,
    },
    {
        "metric": "path2_same_total",
        "family": "paths",
        "direction": "high",
        "description": "ordered simple length-2 paths with repeated color",
        "explainability": 0.50,
    },
    {
        "metric": "path2_transition_entropy",
        "family": "paths",
        "direction": "low",
        "description": "entropy of ordered length-2 color transitions",
        "explainability": 0.40,
    },
    {
        "metric": "path2_same_center_l2",
        "family": "orbits",
        "direction": "high",
        "description": "center-digit imbalance in repeated-color length-2 paths",
        "explainability": 0.45,
    },
    {
        "metric": "path3_mono_total",
        "family": "paths",
        "direction": "high",
        "description": "ordered simple length-3 paths with one edge color",
        "explainability": 0.50,
    },
    {
        "metric": "path3_three_color_total",
        "family": "paths",
        "direction": "low",
        "description": "ordered simple length-3 paths with three edge colors",
        "explainability": 0.50,
    },
    {
        "metric": "path3_palindrome_total",
        "family": "paths",
        "direction": "high",
        "description": "length-3 paths where first and third edge colors match",
        "explainability": 0.50,
    },
    {
        "metric": "path3_pattern_entropy",
        "family": "paths",
        "direction": "low",
        "description": "entropy of length-3 color-pattern counts",
        "explainability": 0.40,
    },
    {
        "metric": "path3_palindrome_internal_l2",
        "family": "orbits",
        "direction": "high",
        "description": "internal-digit imbalance for path color palindromes",
        "explainability": 0.45,
    },
    {
        "metric": "spectral_radius_sum",
        "family": "spectral",
        "direction": "high",
        "description": "sum of same-color matrix spectral radii",
        "explainability": 0.35,
    },
    {
        "metric": "spectral_radius_max",
        "family": "spectral",
        "direction": "high",
        "description": "largest same-color matrix spectral radius",
        "explainability": 0.35,
    },
    {
        "metric": "spectral_radius_l2",
        "family": "spectral",
        "direction": "high",
        "description": "imbalance of spectral radii across colors",
        "explainability": 0.30,
    },
    {
        "metric": "spectral_radius_entropy",
        "family": "spectral",
        "direction": "low",
        "description": "entropy of same-color spectral radii across colors",
        "explainability": 0.30,
    },
    {
        "metric": "orbit_all_l2_sum",
        "family": "orbits",
        "direction": "high",
        "description": "sum of selected digit-orbit imbalance scores",
        "explainability": 0.40,
    },
]


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def primary_pair_symbol(pair_table: dict[str, Any], pair: str) -> str:
    row = pair_table[pair]
    if row["status"] == "pure":
        return row["symbol_if_pure"]
    return sorted(row["symbols"])[0]


def labels_from_formula(formula: dict[str, Any]) -> tuple[list[str], list[dict[str, Any]]]:
    labels = []
    conflict_notes = []
    for pair in PAIR_NAMES:
        row = formula["pair_table"][pair]
        symbol = primary_pair_symbol(formula["pair_table"], pair)
        labels.append(symbol)
        if row["status"] != "pure":
            conflict_notes.append(
                {
                    "pair": pair,
                    "status": row["status"],
                    "symbols": row["symbols"],
                    "primary_symbol_used": symbol,
                }
            )
    return labels, conflict_notes


def entropy_from_counts(values: list[float]) -> float:
    total = sum(values)
    if total <= 0:
        return 0.0
    entropy = 0.0
    for value in values:
        if value:
            p = value / total
            entropy -= p * math.log2(p)
    return entropy


def imbalance_l2(values: list[float]) -> float:
    if not values:
        return 0.0
    mean = sum(values) / len(values)
    return sum((value - mean) ** 2 for value in values)


def pattern_key(colors: tuple[str, ...]) -> str:
    ids: dict[str, int] = {}
    next_id = 0
    parts = []
    for color in colors:
        if color not in ids:
            ids[color] = next_id
            next_id += 1
        parts.append(str(ids[color]))
    return "".join(parts)


def spectral_radius(matrix: list[list[float]]) -> float:
    vector = [1.0 / math.sqrt(10.0)] * 10
    for _ in range(36):
        projected = [sum(matrix[row][col] * vector[col] for col in range(10)) for row in range(10)]
        norm = math.sqrt(sum(value * value for value in projected))
        if norm == 0:
            return 0.0
        vector = [value / norm for value in projected]
    return sum(
        vector[row] * sum(matrix[row][col] * vector[col] for col in range(10))
        for row in range(10)
    )


def same_color_spectral_profile(labels: list[str], symbols: list[str]) -> dict[str, dict[str, float]]:
    matrices = {symbol: [[0.0] * 10 for _ in range(10)] for symbol in symbols}
    for index, (left, right) in enumerate(PAIRS):
        matrix = matrices[labels[index]]
        matrix[left][right] = 1.0
        matrix[right][left] = 1.0

    profile = {}
    for symbol in symbols:
        matrix = matrices[symbol]
        profile[symbol] = {
            "cell_count": float(sum(1 for label in labels if label == symbol)),
            "loop_count": float(sum(matrix[digit][digit] for digit in DIGITS)),
            "spectral_radius": spectral_radius(matrix),
        }
    return profile


def compute_metrics(labels: list[str], symbols: list[str], include_details: bool = False) -> dict[str, Any]:
    metrics: dict[str, float] = {}
    details: dict[str, Any] = {}

    triangle_counts = Counter()
    triangle_by_digit = {
        "mono": [0] * 10,
        "two_color": [0] * 10,
        "three_color": [0] * 10,
    }
    for edge1, edge2, edge3, digits in TRIANGLES:
        colors = (labels[edge1], labels[edge2], labels[edge3])
        unique = len(set(colors))
        category = {1: "mono", 2: "two_color", 3: "three_color"}[unique]
        triangle_counts[category] += 1
        for digit in digits:
            triangle_by_digit[category][digit] += 1

    metrics["triangles_mono_total"] = float(triangle_counts["mono"])
    metrics["triangles_three_color_total"] = float(triangle_counts["three_color"])
    metrics["triangles_pattern_entropy"] = entropy_from_counts(
        [triangle_counts["mono"], triangle_counts["two_color"], triangle_counts["three_color"]]
    )
    metrics["orbit_triangle_mono_l2"] = imbalance_l2(triangle_by_digit["mono"])

    wedge_counts = Counter()
    wedge_same_by_center = [0] * 10
    wedge_same_by_leaf = [0] * 10
    for center, edge1, edge2, leaves in WEDGES:
        same = labels[edge1] == labels[edge2]
        wedge_counts["same" if same else "different"] += 1
        if same:
            wedge_same_by_center[center] += 1
            for leaf in leaves:
                wedge_same_by_leaf[leaf] += 1

    metrics["wedges_same_total"] = float(wedge_counts["same"])
    metrics["wedges_same_center_l2"] = imbalance_l2(wedge_same_by_center)
    metrics["wedges_same_leaf_l2"] = imbalance_l2(wedge_same_by_leaf)

    star3_counts = Counter()
    star3_mono_by_center = [0] * 10
    star3_mono_by_leaf = [0] * 10
    for center, edges, leaves in STARS3:
        colors = tuple(labels[edge] for edge in edges)
        unique = len(set(colors))
        category = {1: "mono", 2: "two_color", 3: "three_color"}[unique]
        star3_counts[category] += 1
        if unique == 1:
            star3_mono_by_center[center] += 1
            for leaf in leaves:
                star3_mono_by_leaf[leaf] += 1

    metrics["star3_mono_total"] = float(star3_counts["mono"])
    metrics["star3_three_color_total"] = float(star3_counts["three_color"])
    metrics["star3_pattern_entropy"] = entropy_from_counts(
        [star3_counts["mono"], star3_counts["two_color"], star3_counts["three_color"]]
    )
    metrics["star3_mono_center_l2"] = imbalance_l2(star3_mono_by_center)

    path2_counts = Counter()
    path2_transition_counts = Counter()
    path2_same_by_center = [0] * 10
    path2_same_by_endpoint = [0] * 10
    for left, center, right, edge1, edge2 in PATH2:
        colors = (labels[edge1], labels[edge2])
        same = colors[0] == colors[1]
        path2_counts["same" if same else "different"] += 1
        path2_transition_counts[colors] += 1
        if same:
            path2_same_by_center[center] += 1
            path2_same_by_endpoint[left] += 1
            path2_same_by_endpoint[right] += 1

    metrics["path2_same_total"] = float(path2_counts["same"])
    metrics["path2_transition_entropy"] = entropy_from_counts(list(path2_transition_counts.values()))
    metrics["path2_same_center_l2"] = imbalance_l2(path2_same_by_center)

    path3_counts = Counter()
    path3_pattern_counts = Counter()
    path3_palindrome_by_internal = [0] * 10
    path3_palindrome_by_endpoint = [0] * 10
    for start, mid1, mid2, end, edge1, edge2, edge3 in PATH3:
        colors = (labels[edge1], labels[edge2], labels[edge3])
        unique = len(set(colors))
        category = {1: "mono", 2: "two_color", 3: "three_color"}[unique]
        path3_counts[category] += 1
        path3_pattern_counts[pattern_key(colors)] += 1
        if colors[0] == colors[2]:
            path3_counts["palindrome"] += 1
            path3_palindrome_by_internal[mid1] += 1
            path3_palindrome_by_internal[mid2] += 1
            path3_palindrome_by_endpoint[start] += 1
            path3_palindrome_by_endpoint[end] += 1

    metrics["path3_mono_total"] = float(path3_counts["mono"])
    metrics["path3_three_color_total"] = float(path3_counts["three_color"])
    metrics["path3_palindrome_total"] = float(path3_counts["palindrome"])
    metrics["path3_pattern_entropy"] = entropy_from_counts(list(path3_pattern_counts.values()))
    metrics["path3_palindrome_internal_l2"] = imbalance_l2(path3_palindrome_by_internal)

    spectral_profile = same_color_spectral_profile(labels, symbols)
    radii = [spectral_profile[symbol]["spectral_radius"] for symbol in symbols]
    metrics["spectral_radius_sum"] = sum(radii)
    metrics["spectral_radius_max"] = max(radii) if radii else 0.0
    metrics["spectral_radius_l2"] = imbalance_l2(radii)
    metrics["spectral_radius_entropy"] = entropy_from_counts(radii)

    metrics["orbit_all_l2_sum"] = (
        metrics["orbit_triangle_mono_l2"]
        + metrics["wedges_same_center_l2"]
        + metrics["wedges_same_leaf_l2"]
        + metrics["star3_mono_center_l2"]
        + metrics["path2_same_center_l2"]
        + metrics["path3_palindrome_internal_l2"]
    )

    if include_details:
        details = {
            "triangle_counts": dict(triangle_counts),
            "triangle_by_digit": triangle_by_digit,
            "wedge_counts": dict(wedge_counts),
            "wedge_same_by_center": wedge_same_by_center,
            "wedge_same_by_leaf": wedge_same_by_leaf,
            "star3_counts": dict(star3_counts),
            "star3_mono_by_center": star3_mono_by_center,
            "star3_mono_by_leaf": star3_mono_by_leaf,
            "path2_counts": dict(path2_counts),
            "path2_same_by_center": path2_same_by_center,
            "path2_same_by_endpoint": path2_same_by_endpoint,
            "path3_counts": dict(path3_counts),
            "path3_pattern_counts": dict(sorted(path3_pattern_counts.items())),
            "path3_palindrome_by_internal": path3_palindrome_by_internal,
            "path3_palindrome_by_endpoint": path3_palindrome_by_endpoint,
            "spectral_profile": spectral_profile,
        }

    return {"metrics": metrics, "details": details}


def empirical_summary(values: list[float], observed: float, direction: str) -> dict[str, float]:
    mean = sum(values) / len(values)
    sd = math.sqrt(sum((value - mean) ** 2 for value in values) / (len(values) - 1)) if len(values) > 1 else 0.0
    le = sum(value <= observed for value in values)
    ge = sum(value >= observed for value in values)
    if direction == "high":
        p = (ge + 1) / (len(values) + 1)
        z = (observed - mean) / sd if sd else 0.0
    elif direction == "low":
        p = (le + 1) / (len(values) + 1)
        z = (mean - observed) / sd if sd else 0.0
    else:
        p = min(1.0, 2.0 * (min(le, ge) + 1) / (len(values) + 1))
        z = abs(observed - mean) / sd if sd else 0.0
    return {
        "observed": observed,
        "control_mean": mean,
        "control_sd": sd,
        "control_min": min(values),
        "control_max": max(values),
        "p_good_direction": p,
        "z_good_direction": z,
        "percentile_le": le / len(values),
    }


def add_fdr_q(rows: list[dict[str, Any]]) -> None:
    ordered = sorted(rows, key=lambda row: row["p_good_direction"])
    total = len(ordered)
    running = 1.0
    for rank, row in reversed(list(enumerate(ordered, start=1))):
        running = min(running, row["p_good_direction"] * total / rank)
        row["fdr_q"] = min(1.0, running)


def classify_row(row: dict[str, Any]) -> tuple[str, str]:
    if (
        row["bonferroni_p"] <= 0.01
        and row["explainability"] >= 0.70
        and row["mdl_proxy_bits_saved"] > 0.0
    ):
        return "candidate", "corrected p passes and a compact predictive MDL gain exists"
    if row["bonferroni_p"] <= 0.05 and row["explainability"] >= 0.45:
        return "weak", "corrected p passes, but this is descriptive and saves no MDL bits"
    if row["p_good_direction"] <= 0.01 and row["z_good_direction"] >= 2.5 and row["explainability"] >= 0.45:
        return "weak", "raw p/effect are notable, but the multiple-test gate does not pass"
    return "rejected", "control comparison and MDL/explainability gate do not support it"


def run_controls(
    observed_labels: list[str],
    symbols: list[str],
    trials: int,
    seed: int,
) -> dict[str, list[float]]:
    rng = random.Random(seed)
    shuffled = observed_labels[:]
    values = {spec["metric"]: [] for spec in METRIC_SPECS}
    for _trial in range(trials):
        rng.shuffle(shuffled)
        current = compute_metrics(shuffled, symbols, include_details=False)["metrics"]
        for metric in values:
            values[metric].append(current[metric])
    return values


def metric_rows(
    observed_metrics: dict[str, float],
    controls: dict[str, list[float]],
) -> list[dict[str, Any]]:
    rows = []
    test_count = len(METRIC_SPECS)
    for spec in METRIC_SPECS:
        metric = spec["metric"]
        summary = empirical_summary(controls[metric], observed_metrics[metric], spec["direction"])
        row = {
            **spec,
            **summary,
            "bonferroni_p": min(1.0, summary["p_good_direction"] * test_count),
            "mdl_proxy_bits_saved": 0.0,
            "mdl_note": "descriptive motif statistic only; no cell-label prediction rule",
        }
        row["classification"], row["classification_reason"] = classify_row(row)
        rows.append(row)
    add_fdr_q(rows)
    class_rank = {"candidate": 0, "weak": 1, "rejected": 2}
    rows.sort(
        key=lambda row: (
            class_rank[row["classification"]],
            row["bonferroni_p"],
            row["p_good_direction"],
        )
    )
    return rows


def overall_verdict(rows: list[dict[str, Any]]) -> str:
    classes = {row["classification"] for row in rows}
    if "candidate" in classes:
        return "candidate_motif_not_promoted"
    if "weak" in classes:
        return "weak_motif_anomaly_no_formula"
    return "rejected_no_motif_formula"


def format_float(value: float, digits: int = 3) -> str:
    if abs(value) >= 1000:
        return f"{value:.1f}"
    return f"{value:.{digits}f}"


def write_report(result: dict[str, Any]) -> None:
    top_rows = result["metric_rows"][:12]
    details = result["observed_details"]
    lines = [
        "# Pair Graph Motif Search",
        "",
        "Generated by `pair_graph_motif_search.py`.",
        "",
        "Scope: mechanical motif search over the 55 unordered pair-table cells.",
        "No translation, glossary, or plaintext promotion is attempted.",
        "",
        "## Controls",
        "",
        f"- Formula source: `{result['formula_source']}`.",
        f"- Cells: `{result['cell_count']}` unordered cells on digits `0..9`, loops included.",
        f"- Label inventory: `{result['label_inventory']}`.",
        f"- Control trials: `{result['control_trials']}` inventory-preserving shuffles.",
        f"- Random seed: `{result['random_seed']}`.",
        f"- Conflict handling: `{result['conflict_handling']}`.",
        "",
        "## Verdict",
        "",
        f"`{result['verdict']}`.",
        "",
        "The best motif statistics are descriptive only. They do not provide a",
        "cell-label prediction rule or a positive MDL gain, so this pass does not",
        "promote a generator formula.",
        "",
        "## Top Metrics",
        "",
        "| Metric | Class | Observed | Control mean | z | p | Bonf. p | FDR q |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in top_rows:
        lines.append(
            "| `{metric}` | `{classification}` | {observed} | {mean} | {z} | {p:.5f} | {bonf:.5f} | {q:.5f} |".format(
                metric=row["metric"],
                classification=row["classification"],
                observed=format_float(row["observed"]),
                mean=format_float(row["control_mean"]),
                z=format_float(row["z_good_direction"], 2),
                p=row["p_good_direction"],
                bonf=row["bonferroni_p"],
                q=row["fdr_q"],
            )
        )

    lines += [
        "",
        "## Observed Motifs",
        "",
        f"- Triangles: `{details['triangle_counts']}`.",
        f"- Wedges: `{details['wedge_counts']}`.",
        f"- 3-edge stars: `{details['star3_counts']}`.",
        f"- Length-2 paths: `{details['path2_counts']}`.",
        f"- Length-3 paths: `{details['path3_counts']}`.",
        "",
        "## Digit Orbit Counts",
        "",
        "| Orbit vector | Digits 0..9 |",
        "|---|---|",
        f"| triangle mono vertices | `{details['triangle_by_digit']['mono']}` |",
        f"| wedge same center | `{details['wedge_same_by_center']}` |",
        f"| wedge same leaf | `{details['wedge_same_by_leaf']}` |",
        f"| 3-star mono center | `{details['star3_mono_by_center']}` |",
        f"| path2 same center | `{details['path2_same_by_center']}` |",
        f"| path3 palindrome internal | `{details['path3_palindrome_by_internal']}` |",
        "",
        "## Same-Color Spectral Profile",
        "",
        "| Symbol | Cells | Loops | Spectral radius |",
        "|---|---:|---:|---:|",
    ]
    for symbol, profile in result["observed_details"]["spectral_profile"].items():
        lines.append(
            f"| `{symbol}` | {int(profile['cell_count'])} | {int(profile['loop_count'])} | "
            f"{profile['spectral_radius']:.4f} |"
        )

    lines += [
        "",
        "## Classification Policy",
        "",
        "- `candidate`: corrected p <= 0.01 plus compact predictive MDL gain.",
        "- `weak`: corrected p <= 0.05, or strong raw p/effect, but no MDL gain.",
        "- `rejected`: control comparison plus MDL/explainability do not support the motif.",
        "",
        "All rows in this pass have `mdl_proxy_bits_saved = 0.0` because they are",
        "motif summaries rather than a formula that predicts hidden cells.",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trials", type=int, default=CONTROL_TRIALS, help="inventory-preserving control shuffles")
    parser.add_argument("--seed", type=int, default=RANDOM_SEED, help="random seed for control shuffles")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.trials < 1000:
        raise SystemExit("at least 1000 control trials are required for this pass")

    formula = load_json(FORMULA_JSON)
    labels, conflict_notes = labels_from_formula(formula)
    symbols = sorted(set(labels))
    observed = compute_metrics(labels, symbols, include_details=True)
    controls = run_controls(labels, symbols, args.trials, args.seed)
    rows = metric_rows(observed["metrics"], controls)
    verdict = overall_verdict(rows)

    result = {
        "schema": "pair_graph_motif_results.v1",
        "formula_source": str(FORMULA_JSON.relative_to(ROOT)),
        "created_by": "pair_graph_motif_search.py",
        "random_seed": args.seed,
        "control_trials": args.trials,
        "cell_count": len(PAIRS),
        "motif_counts": {
            "triangles": len(TRIANGLES),
            "wedges": len(WEDGES),
            "stars3": len(STARS3),
            "ordered_path2": len(PATH2),
            "ordered_path3": len(PATH3),
        },
        "path_definition": "simple paths over distinct vertices; all path cells are distinct; loops excluded",
        "label_inventory": dict(sorted(Counter(labels).items())),
        "symbols": symbols,
        "conflict_handling": "non-pure cells use the deterministic sorted-symbol primary label, matching pair_graph_incidence_search.py",
        "conflict_notes": conflict_notes,
        "observed_metrics": observed["metrics"],
        "observed_details": observed["details"],
        "metric_rows": rows,
        "best_metric": rows[0],
        "classification_policy": {
            "candidate": "corrected p <= 0.01 plus compact predictive MDL gain",
            "weak": "corrected p <= 0.05, or strong raw p/effect, without MDL gain",
            "rejected": "control comparison and MDL/explainability gate do not support it",
            "mdl_proxy_bits_saved": 0.0,
        },
        "verdict": verdict,
        "formula_promoted": False,
        "translation_delta": "NONE",
    }

    write_json(OUT_JSON, result)
    write_report(result)
    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(f"wrote {OUT_MD.relative_to(ROOT)}")
    print(
        "verdict={verdict} best={metric} class={classification} p={p:.5f} bonferroni={bonf:.5f}".format(
            verdict=verdict,
            metric=rows[0]["metric"],
            classification=rows[0]["classification"],
            p=rows[0]["p_good_direction"],
            bonf=rows[0]["bonferroni_p"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
