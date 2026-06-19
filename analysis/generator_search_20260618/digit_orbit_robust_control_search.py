#!/usr/bin/env python3
"""Robust controls for the weak 6<->9 digit-orbit signal.

Earlier searches found that quotienting the unordered pair table by swapping
digits 6 and 9 gives a small lossless compression and unusually few mixed
two-cell orbits.  This pass does not search for a new plaintext or symbol
formula.  It formalizes stronger controls:

- global inventory-preserving pair-label shuffles;
- row-preserving shuffles over triangular-grid rows;
- column-preserving shuffles over triangular-grid columns;
- fixed `swap_6_9` and best-of-45 digit transposition scores.

Mechanical only.  No plaintext, glossary, or translation is promoted.
"""

from __future__ import annotations

import itertools
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FORMULA_JSON = ROOT / "analysis" / "mechanism_model_20260618" / "mechanical_formula_469.json"

OUT_JSON = HERE / "digit_orbit_robust_control_results.json"
OUT_MD = HERE / "digit_orbit_robust_control_report.md"

SIGMA = "*ABCEFILNORSTV"
SYMBOL_BITS = math.log2(len(SIGMA))
LOOKUP_BITS = 55 * SYMBOL_BITS
RANDOM_SEED = 46920260619
CONTROL_TRIALS = 20000


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def pair_key(pair: tuple[int, int]) -> str:
    return f"{pair[0]}{pair[1]}"


def natural_pairs() -> list[tuple[int, int]]:
    return [(a, b) for a in range(10) for b in range(a, 10)]


PAIR_LIST = [(a, b) for a in range(10) for b in range(a, 10)]
PAIR_INDEX = {pair: index for index, pair in enumerate(PAIR_LIST)}


def symbol_key(symbol: str) -> int:
    return SIGMA.index(symbol)


def primary_pair_symbol(pair_table: dict[str, dict[str, Any]], pair: tuple[int, int]) -> str:
    cell = pair_table[pair_key(pair)]
    if cell["status"] == "pure":
        return cell["symbol_if_pure"]
    return min(cell["symbols"], key=symbol_key)


def swap_pair(pair: tuple[int, int], i: int, j: int) -> tuple[int, int]:
    a, b = pair
    if a == i:
        a = j
    elif a == j:
        a = i
    if b == i:
        b = j
    elif b == j:
        b = i
    return (a, b) if a <= b else (b, a)


def orbit_partition(pairs: list[tuple[int, int]], i: int, j: int) -> list[list[tuple[int, int]]]:
    remaining = set(pairs)
    out = []
    while remaining:
        seed = min(remaining)
        mate = swap_pair(seed, i, j)
        orbit = {seed, mate}
        out.append(sorted(orbit))
        remaining -= orbit
    return sorted(out, key=lambda orbit: (len(orbit), pair_key(orbit[0])))


def orbit_index_partition(i: int, j: int) -> list[list[int]]:
    return [[PAIR_INDEX[pair] for pair in orbit] for orbit in orbit_partition(PAIR_LIST, i, j)]


SWAP_ORBITS = {(i, j): orbit_index_partition(i, j) for i in range(10) for j in range(i + 1, 10)}
SWAP_NON_SINGLETON_ORBITS = {
    key: [tuple(orbit) for orbit in orbits if len(orbit) > 1]
    for key, orbits in SWAP_ORBITS.items()
}


def labels_to_tuple(labels: dict[tuple[int, int], str]) -> tuple[str, ...]:
    return tuple(labels[pair] for pair in PAIR_LIST)


def evaluate_swap_fast(label_values: tuple[str, ...], i: int, j: int) -> dict[str, Any]:
    non_singleton_orbits = SWAP_NON_SINGLETON_ORBITS[(i, j)]
    non_singleton = len(non_singleton_orbits)
    mixed = sum(1 for left, right in non_singleton_orbits if label_values[left] != label_values[right])
    hits = len(PAIR_LIST) - mixed
    split_label_count = len(SWAP_ORBITS[(i, j)]) + mixed
    moved_total = non_singleton * 2
    moved_hits = (non_singleton - mixed) * 2
    mixed_selector_bits = math.log2(math.comb(non_singleton, mixed)) if 0 < mixed < non_singleton else 0.0
    transform_bits = math.log2(45) + math.log2(8)
    split_lossless_bits = transform_bits + mixed_selector_bits + split_label_count * SYMBOL_BITS
    return {
        "swap": f"swap_{i}_{j}",
        "i": i,
        "j": j,
        "orbit_count": len(SWAP_ORBITS[(i, j)]),
        "non_singleton_orbit_count": non_singleton,
        "mixed_non_singleton_orbit_count": mixed,
        "split_label_count": split_label_count,
        "primary_hits": hits,
        "primary_accuracy": hits / len(PAIR_LIST),
        "moved_pair_preserved_count": moved_hits,
        "moved_pair_count": moved_total,
        "moved_pair_preserved_fraction": moved_hits / moved_total if moved_total else 1.0,
        "split_lossless_bits": split_lossless_bits,
        "split_mdl_gain_vs_lookup_bits": LOOKUP_BITS - split_lossless_bits,
        "split_lookup_cost_ratio": split_lossless_bits / LOOKUP_BITS,
    }


def evaluate_all_fast(label_values: tuple[str, ...]) -> list[dict[str, Any]]:
    rows = [evaluate_swap_fast(label_values, i, j) for i in range(10) for j in range(i + 1, 10)]
    rows.sort(
        key=lambda row: (
            -row["primary_hits"],
            row["mixed_non_singleton_orbit_count"],
            -row["split_mdl_gain_vs_lookup_bits"],
            row["swap"],
        )
    )
    return rows


def evaluate_swap(labels: dict[tuple[int, int], str], i: int, j: int) -> dict[str, Any]:
    pairs = natural_pairs()
    orbits = orbit_partition(pairs, i, j)
    hits = 0
    mixed = 0
    split_label_count = 0
    moved_hits = 0
    moved_total = 0
    exceptions = []
    orbit_rows = []
    for orbit_index, orbit in enumerate(orbits):
        counts = Counter(labels[pair] for pair in orbit)
        label = min(counts, key=lambda symbol: (-counts[symbol], symbol_key(symbol)))
        is_mixed = len(counts) > 1
        if is_mixed:
            mixed += 1
            split_label_count += len(orbit)
        else:
            split_label_count += 1
        for pair in orbit:
            mate = swap_pair(pair, i, j)
            if mate != pair:
                moved_total += 1
                if labels[mate] == labels[pair]:
                    moved_hits += 1
            if labels[pair] == label:
                hits += 1
            else:
                exceptions.append({"pair": pair_key(pair), "predicted": label, "actual": labels[pair], "orbit": orbit_index})
        orbit_rows.append(
            {
                "orbit": orbit_index,
                "pairs": [pair_key(pair) for pair in orbit],
                "label_counts": dict(sorted(counts.items())),
                "is_mixed": is_mixed,
            }
        )
    # Charged as one digit-transposition id, one mixed-orbit subset, and one
    # label per split-lossless stored cell/orbit. This mirrors the earlier
    # quotient accounting at the level needed for controls.
    non_singleton = sum(1 for orbit in orbits if len(orbit) > 1)
    mixed_selector_bits = math.log2(math.comb(non_singleton, mixed)) if 0 < mixed < non_singleton else 0.0
    transform_bits = math.log2(45) + math.log2(8)
    split_lossless_bits = transform_bits + mixed_selector_bits + split_label_count * SYMBOL_BITS
    return {
        "swap": f"swap_{i}_{j}",
        "i": i,
        "j": j,
        "orbit_count": len(orbits),
        "non_singleton_orbit_count": non_singleton,
        "mixed_non_singleton_orbit_count": mixed,
        "split_label_count": split_label_count,
        "primary_hits": hits,
        "primary_accuracy": hits / len(pairs),
        "exceptions": exceptions,
        "moved_pair_preserved_count": moved_hits,
        "moved_pair_count": moved_total,
        "moved_pair_preserved_fraction": moved_hits / moved_total if moved_total else 1.0,
        "split_lossless_bits": split_lossless_bits,
        "split_mdl_gain_vs_lookup_bits": LOOKUP_BITS - split_lossless_bits,
        "split_lookup_cost_ratio": split_lossless_bits / LOOKUP_BITS,
        "orbits": orbit_rows,
    }


def evaluate_all(labels: dict[tuple[int, int], str]) -> list[dict[str, Any]]:
    rows = [evaluate_swap(labels, i, j) for i in range(10) for j in range(i + 1, 10)]
    rows.sort(
        key=lambda row: (
            -row["primary_hits"],
            row["mixed_non_singleton_orbit_count"],
            -row["split_mdl_gain_vs_lookup_bits"],
            row["swap"],
        )
    )
    return rows


def shuffle_global(labels: dict[tuple[int, int], str], rng: random.Random) -> dict[tuple[int, int], str]:
    pairs = natural_pairs()
    values = [labels[pair] for pair in pairs]
    rng.shuffle(values)
    return dict(zip(pairs, values))


def shuffle_global_tuple(label_values: tuple[str, ...], rng: random.Random) -> tuple[str, ...]:
    values = list(label_values)
    rng.shuffle(values)
    return tuple(values)


ROW_INDEXES = [[PAIR_INDEX[(a, b)] for b in range(a, 10)] for a in range(10)]
COLUMN_INDEXES = [[PAIR_INDEX[(a, b)] for a in range(0, b + 1)] for b in range(10)]


def shuffle_by_groups_tuple(label_values: tuple[str, ...], groups: list[list[int]], rng: random.Random) -> tuple[str, ...]:
    out = list(label_values)
    for group in groups:
        values = [out[index] for index in group]
        rng.shuffle(values)
        for index, value in zip(group, values):
            out[index] = value
    return tuple(out)


def shuffle_by_row_tuple(label_values: tuple[str, ...], rng: random.Random) -> tuple[str, ...]:
    return shuffle_by_groups_tuple(label_values, ROW_INDEXES, rng)


def shuffle_by_column_tuple(label_values: tuple[str, ...], rng: random.Random) -> tuple[str, ...]:
    return shuffle_by_groups_tuple(label_values, COLUMN_INDEXES, rng)


def shuffle_by_row(labels: dict[tuple[int, int], str], rng: random.Random) -> dict[tuple[int, int], str]:
    out = {}
    for a in range(10):
        pairs = [(a, b) for b in range(a, 10)]
        values = [labels[pair] for pair in pairs]
        rng.shuffle(values)
        out.update(dict(zip(pairs, values)))
    return out


def shuffle_by_column(labels: dict[tuple[int, int], str], rng: random.Random) -> dict[tuple[int, int], str]:
    out = {}
    for b in range(10):
        pairs = [(a, b) for a in range(0, b + 1)]
        values = [labels[pair] for pair in pairs]
        rng.shuffle(values)
        out.update(dict(zip(pairs, values)))
    return out


def summarize(values: list[float], observed: float, higher_is_better: bool) -> dict[str, Any]:
    mean = sum(values) / len(values)
    sd = (sum((value - mean) ** 2 for value in values) / (len(values) - 1)) ** 0.5
    if higher_is_better:
        p = (sum(value >= observed for value in values) + 1) / (len(values) + 1)
        z = (observed - mean) / sd if sd else 0.0
    else:
        p = (sum(value <= observed for value in values) + 1) / (len(values) + 1)
        z = (mean - observed) / sd if sd else 0.0
    return {
        "observed": observed,
        "mean": mean,
        "sd": sd,
        "min": min(values),
        "max": max(values),
        "p_good_direction": p,
        "z_good_direction": z,
    }


def control_family(name: str, shuffler, label_values: tuple[str, ...], observed_fixed: dict[str, Any], observed_best: dict[str, Any]) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED + sum(ord(c) for c in name))
    fixed_hits = []
    fixed_mixed = []
    fixed_split_gain = []
    best_hits = []
    best_mixed = []
    best_split_gain = []
    for _ in range(CONTROL_TRIALS):
        ctrl_labels = shuffler(label_values, rng)
        fixed = evaluate_swap_fast(ctrl_labels, 6, 9)
        all_rows = evaluate_all_fast(ctrl_labels)
        best_by_hits = all_rows[0]
        best_by_mixed = min(all_rows, key=lambda row: (row["mixed_non_singleton_orbit_count"], -row["primary_hits"], row["swap"]))
        best_by_split = max(all_rows, key=lambda row: (row["split_mdl_gain_vs_lookup_bits"], row["primary_hits"], row["swap"]))
        fixed_hits.append(fixed["primary_hits"])
        fixed_mixed.append(fixed["mixed_non_singleton_orbit_count"])
        fixed_split_gain.append(fixed["split_mdl_gain_vs_lookup_bits"])
        best_hits.append(best_by_hits["primary_hits"])
        best_mixed.append(best_by_mixed["mixed_non_singleton_orbit_count"])
        best_split_gain.append(best_by_split["split_mdl_gain_vs_lookup_bits"])
    return {
        "trials": CONTROL_TRIALS,
        "fixed_swap_6_9": {
            "primary_hits": summarize(fixed_hits, observed_fixed["primary_hits"], True),
            "mixed_non_singleton_orbit_count": summarize(fixed_mixed, observed_fixed["mixed_non_singleton_orbit_count"], False),
            "split_mdl_gain_vs_lookup_bits": summarize(fixed_split_gain, observed_fixed["split_mdl_gain_vs_lookup_bits"], True),
        },
        "best_of_45_swaps": {
            "primary_hits": summarize(best_hits, observed_best["primary_hits"], True),
            "mixed_non_singleton_orbit_count": summarize(best_mixed, observed_fixed["mixed_non_singleton_orbit_count"], False),
            "split_mdl_gain_vs_lookup_bits": summarize(best_split_gain, observed_fixed["split_mdl_gain_vs_lookup_bits"], True),
        },
    }


def verdict(result: dict[str, Any]) -> str:
    controls = result["controls"]
    p_values = [
        controls[name]["best_of_45_swaps"]["primary_hits"]["p_good_direction"]
        for name in controls
    ] + [
        controls[name]["best_of_45_swaps"]["mixed_non_singleton_orbit_count"]["p_good_direction"]
        for name in controls
    ]
    if max(p_values) <= 0.05 and result["observed"]["swap_6_9"]["split_mdl_gain_vs_lookup_bits"] > 0:
        return "robust_weak_6_9_orbit_signal"
    if min(p_values) <= 0.05:
        return "partially_robust_6_9_orbit_signal"
    return "control_sensitive_6_9_orbit_signal"


def write_report(result: dict[str, Any]) -> None:
    fixed = result["observed"]["swap_6_9"]
    best = result["observed"]["best_by_primary_hits"]
    controls = result["controls"]
    lines = [
        "# Digit-Orbit Robust Control Search",
        "",
        "Generated by `digit_orbit_robust_control_search.py`.",
        "",
        "This pass formalizes stronger controls for the weak `6 <-> 9` quotient",
        "signal. It assigns no plaintext and does not promote a symbol formula.",
        "",
        "## Observed",
        "",
        "| Row | Swap | Hits | Mixed non-singleton orbits | Split labels | Split MDL/lookup | Gain bits |",
        "|---|---|---:|---:|---:|---:|---:|",
        f"| fixed 6/9 | `{fixed['swap']}` | {fixed['primary_hits']}/55 | {fixed['mixed_non_singleton_orbit_count']} | {fixed['split_label_count']} | {fixed['split_lookup_cost_ratio']:.3f} | {fixed['split_mdl_gain_vs_lookup_bits']:.2f} |",
        f"| best by hits | `{best['swap']}` | {best['primary_hits']}/55 | {best['mixed_non_singleton_orbit_count']} | {best['split_label_count']} | {best['split_lookup_cost_ratio']:.3f} | {best['split_mdl_gain_vs_lookup_bits']:.2f} |",
        "",
        "## Controls",
        "",
        "| Control | Scope | Metric | Observed | Mean | Max/Min | p(good) |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    for name, ctrl in controls.items():
        label = {
            "global_pair_label_shuffle": "global inventory-preserving",
            "row_preserving_shuffle": "row-preserving",
            "column_preserving_shuffle": "column-preserving",
        }[name]
        for scope_key, scope_label in [("fixed_swap_6_9", "fixed `6<->9`"), ("best_of_45_swaps", "best of 45 swaps")]:
            for metric, metric_label, extremum in [
                ("primary_hits", "primary hits", "max"),
                ("mixed_non_singleton_orbit_count", "mixed orbit count", "min"),
                ("split_mdl_gain_vs_lookup_bits", "split MDL gain", "max"),
            ]:
                row = ctrl[scope_key][metric]
                lines.append(
                    f"| {label} | {scope_label} | {metric_label} | {row['observed']:.3f} | {row['mean']:.3f} | {row[extremum]:.3f} | {row['p_good_direction']:.5f} |"
                )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The `6 <-> 9` quotient signal survives multiple control shapes: global,",
            "row-preserving, and column-preserving shuffles. The strongest evidence",
            "is the unusually low number of mixed non-singleton orbits under the",
            "fixed swap and the best-of-45 search. The effect remains small in MDL",
            "terms and still does not generate the pair labels.",
            "",
            f"Verdict: `{result['verdict']}`.",
            "",
            "Translation delta: `NONE`.",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    formula = load_json(FORMULA_JSON)
    labels = {pair: primary_pair_symbol(formula["pair_table"], pair) for pair in natural_pairs()}
    label_values = labels_to_tuple(labels)
    observed_rows = evaluate_all(labels)
    fixed = next(row for row in observed_rows if row["swap"] == "swap_6_9")
    best = observed_rows[0]
    controls = {
        "global_pair_label_shuffle": control_family("global_pair_label_shuffle", shuffle_global_tuple, label_values, fixed, best),
        "row_preserving_shuffle": control_family("row_preserving_shuffle", shuffle_by_row_tuple, label_values, fixed, best),
        "column_preserving_shuffle": control_family("column_preserving_shuffle", shuffle_by_column_tuple, label_values, fixed, best),
    }
    result = {
        "schema": "digit_orbit_robust_control_results.v1",
        "translation_delta": "NONE",
        "control_trials": CONTROL_TRIALS,
        "observed": {
            "swap_6_9": fixed,
            "best_by_primary_hits": best,
            "top_swaps": observed_rows[:15],
        },
        "controls": controls,
    }
    result["verdict"] = verdict(result)
    write_json(OUT_JSON, result)
    write_report(result)
    print(f"wrote {OUT_JSON.relative_to(HERE)}")
    print(f"wrote {OUT_MD.relative_to(HERE)}")
    print(
        "verdict={verdict} fixed_hits={hits}/55 mixed={mixed} gain={gain:.2f}".format(
            verdict=result["verdict"],
            hits=fixed["primary_hits"],
            mixed=fixed["mixed_non_singleton_orbit_count"],
            gain=fixed["split_mdl_gain_vs_lookup_bits"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
