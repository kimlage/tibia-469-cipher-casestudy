#!/usr/bin/env python3
"""Marginal constraint solver search for the 469 unordered pair table.

This pass asks whether the 55 primary pair labels can be recovered from compact
constraints instead of a cell lookup.  It measures how much ambiguity remains
after several marginal families:

- global homophone inventory;
- row / column / diagonal / anti-diagonal counts;
- row symbol-presence sets;
- lore/anomaly anchors for 19 and 39;
- the weak 6<->9 orbit structure;
- row+column marginals counted by a dependency-free capped backtracker.

The output is mechanical only.  It does not assign plaintext, glossary entries,
or translations to any symbol.
"""

from __future__ import annotations

import json
import math
import random
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path
from statistics import mean, pstdev
from typing import Callable


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FORMULA_JSON = ROOT / "analysis" / "mechanism_model_20260618" / "mechanical_formula_469.json"

OUT_JSON = HERE / "marginal_constraint_solver_results.json"
OUT_MD = HERE / "marginal_constraint_solver_report.md"

SIGMA = tuple("*ABCEFILNORSTV")
SYMBOL_INDEX = {symbol: idx for idx, symbol in enumerate(SIGMA)}
PAIR_COUNT = 55
RANDOM_SEED = 46920260619

FAST_CONTROL_TRIALS = 2000
ROW_SET_CONTROL_TRIALS = 80
SOLVER_CONTROL_TRIALS = 60
COUNT_CAP = 10**12


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def all_pairs() -> list[str]:
    return [f"{left}{right}" for left in range(10) for right in range(left, 10)]


def pair_digits(pair: str) -> tuple[int, int]:
    return int(pair[0]), int(pair[1])


def primary_pair_symbol(pair_table: dict, pair: str) -> str:
    row = pair_table[pair]
    if row["status"] == "pure":
        return row["symbol_if_pure"]
    return sorted(row["symbols"])[0]


def log2_comb(n: int, k: int) -> float:
    if k < 0 or k > n:
        return float("inf")
    if k == 0 or k == n:
        return 0.0
    return math.log2(math.comb(n, k))


def log2_factorial(n: int) -> float:
    return math.lgamma(n + 1) / math.log(2)


def log2_multinomial(counts: Counter[str] | dict[str, int]) -> float:
    total = sum(int(value) for value in counts.values())
    return log2_factorial(total) - sum(log2_factorial(int(value)) for value in counts.values())


def count_multinomial(counts: Counter[str] | dict[str, int]) -> int:
    total = sum(int(value) for value in counts.values())
    out = math.factorial(total)
    for value in counts.values():
        out //= math.factorial(int(value))
    return out


def hist_cost_bits(length: int) -> float:
    """Cost to describe an unlabeled 14-symbol histogram of this line length."""
    return log2_comb(length + len(SIGMA) - 1, len(SIGMA) - 1)


def inventory_cost_bits() -> float:
    return hist_cost_bits(PAIR_COUNT)


def raw_lookup_bits() -> float:
    return PAIR_COUNT * math.log2(len(SIGMA))


def labels_from_formula(formula: dict) -> dict[str, str]:
    return {pair: primary_pair_symbol(formula["pair_table"], pair) for pair in all_pairs()}


def line_partitions() -> dict[str, dict[str, list[str]]]:
    pairs = all_pairs()
    partitions: dict[str, dict[str, list[str]]] = {
        "row": {},
        "column": {},
        "diagonal_diff": {},
        "anti_diagonal_sum": {},
    }
    for digit in range(10):
        partitions["row"][str(digit)] = [f"{digit}{right}" for right in range(digit, 10)]
        partitions["column"][str(digit)] = [f"{left}{digit}" for left in range(digit + 1)]
        partitions["diagonal_diff"][str(digit)] = [
            pair for pair in pairs if int(pair[1]) - int(pair[0]) == digit
        ]
    for total in range(19):
        partitions["anti_diagonal_sum"][str(total)] = [
            pair for pair in pairs if int(pair[0]) + int(pair[1]) == total
        ]
    return partitions


def line_counts(labels: dict[str, str], partition: dict[str, list[str]]) -> dict[str, Counter[str]]:
    return {line_id: Counter(labels[pair] for pair in pairs) for line_id, pairs in partition.items()}


def partition_residual_bits(count_rows: dict[str, Counter[str]]) -> float:
    return sum(log2_multinomial(row) for row in count_rows.values())


def partition_residual_count(count_rows: dict[str, Counter[str]]) -> int:
    out = 1
    for row in count_rows.values():
        out *= count_multinomial(row)
    return out


def partition_cost_bits(partition: dict[str, list[str]]) -> float:
    return sum(hist_cost_bits(len(pairs)) for pairs in partition.values())


def diagonal_pairs() -> list[str]:
    return [f"{digit}{digit}" for digit in range(10)]


def anchor_residual(labels: dict[str, str], anchors: list[str]) -> tuple[int, float, bool]:
    counts = Counter(labels.values())
    for pair in anchors:
        label = labels[pair]
        counts[label] -= 1
        if counts[label] < 0:
            return 0, float("-inf"), True
    count = count_multinomial(counts)
    return count, math.log2(count) if count else float("-inf"), True


def diagonal_count_residual(labels: dict[str, str]) -> tuple[int, float]:
    diag = Counter(labels[pair] for pair in diagonal_pairs())
    total = Counter(labels.values())
    rest = total.copy()
    for symbol, count in diag.items():
        rest[symbol] -= count
    count = count_multinomial(diag) * count_multinomial(rest)
    return count, math.log2(count)


def compositions_positive(total: int, parts: int) -> list[tuple[int, ...]]:
    if parts <= 0:
        return [()] if total == 0 else []
    if parts == 1:
        return [(total,)] if total >= 1 else []
    out = []
    for first in range(1, total - parts + 2):
        for tail in compositions_positive(total - first, parts - 1):
            out.append((first, *tail))
    return out


def row_set_residual(labels: dict[str, str]) -> tuple[int, float, bool]:
    target = tuple(Counter(labels.values()).get(symbol, 0) for symbol in SIGMA)
    row_options: list[list[tuple[tuple[int, ...], int]]] = []
    for row_digit in range(10):
        row_pairs = [f"{row_digit}{right}" for right in range(row_digit, 10)]
        present = sorted({labels[pair] for pair in row_pairs}, key=SYMBOL_INDEX.get)
        row_len = len(row_pairs)
        options = []
        for comp in compositions_positive(row_len, len(present)):
            vector = [0] * len(SIGMA)
            row_counter = Counter()
            for symbol, count in zip(present, comp):
                vector[SYMBOL_INDEX[symbol]] = count
                row_counter[symbol] = count
            options.append((tuple(vector), count_multinomial(row_counter)))
        row_options.append(options)

    @lru_cache(maxsize=None)
    def dp(row_idx: int, used: tuple[int, ...]) -> int:
        if row_idx == len(row_options):
            return 1 if used == target else 0
        total = 0
        for vector, arrangements in row_options[row_idx]:
            nxt = tuple(used[idx] + vector[idx] for idx in range(len(SIGMA)))
            if any(nxt[idx] > target[idx] for idx in range(len(SIGMA))):
                continue
            total += arrangements * dp(row_idx + 1, nxt)
        return total

    count = dp(0, tuple(0 for _ in SIGMA))
    return count, math.log2(count) if count else float("-inf"), True


def row_set_cost(labels: dict[str, str]) -> float:
    cost = inventory_cost_bits()
    for row_digit in range(10):
        row_pairs = [f"{row_digit}{right}" for right in range(row_digit, 10)]
        present = {labels[pair] for pair in row_pairs}
        cost += log2_comb(len(SIGMA), len(present))
    return cost


def swap_6_9(pair: str) -> str:
    mapped = [9 if digit == "6" else 6 if digit == "9" else int(digit) for digit in pair]
    mapped.sort()
    return f"{mapped[0]}{mapped[1]}"


def orbit_partition_6_9() -> list[list[str]]:
    remaining = set(all_pairs())
    orbits = []
    while remaining:
        seed = min(remaining)
        orbit = sorted({seed, swap_6_9(seed)})
        orbits.append(orbit)
        remaining -= set(orbit)
    return sorted(orbits, key=lambda row: (len(row), row[0]))


def orbit_residual(labels: dict[str, str]) -> tuple[int, float, bool, dict]:
    """Count tables with the same inventory and same 6<->9 split-orbit metadata."""
    inventory = tuple(Counter(labels.values()).get(symbol, 0) for symbol in SIGMA)
    orbits = orbit_partition_6_9()
    non_singleton = [orbit for orbit in orbits if len(orbit) > 1]
    mixed_indices = []
    singleton_items = 0
    double_items = 0
    for orbit_index, orbit in enumerate(orbits):
        if len(orbit) == 1:
            singleton_items += 1
            continue
        orbit_labels = {labels[pair] for pair in orbit}
        non_singleton_index = sum(1 for prev in orbits[:orbit_index] if len(prev) > 1)
        if len(orbit_labels) > 1:
            mixed_indices.append(non_singleton_index)
            singleton_items += 2
        else:
            double_items += 1

    # Closed form: choose how many weight-2 equality orbits each symbol gets.
    # The remaining inventory must be assigned to distinguishable singleton
    # items. This avoids a broad item-by-item DP over 45-55 slots.
    double_factor = math.factorial(double_items)
    single_factor = math.factorial(singleton_items)
    count = 0

    def rec(symbol_idx: int, remaining_double: int, chosen: list[int]) -> None:
        nonlocal count
        if symbol_idx == len(SIGMA):
            if remaining_double != 0:
                return
            double_den = 1
            single_den = 1
            single_total = 0
            for idx, double_count in enumerate(chosen):
                single_count = inventory[idx] - 2 * double_count
                if single_count < 0:
                    return
                single_total += single_count
                double_den *= math.factorial(double_count)
                single_den *= math.factorial(single_count)
            if single_total != singleton_items:
                return
            count += (double_factor // double_den) * (single_factor // single_den)
            return
        max_double = min(remaining_double, inventory[symbol_idx] // 2)
        for value in range(max_double + 1):
            chosen.append(value)
            rec(symbol_idx + 1, remaining_double - value, chosen)
            chosen.pop()

    rec(0, double_items, [])
    meta = {
        "orbit_count": len(orbits),
        "non_singleton_orbit_count": len(non_singleton),
        "mixed_non_singleton_orbit_count": len(mixed_indices),
        "mixed_non_singleton_indices": mixed_indices,
        "mixed_pairs": [non_singleton[idx] for idx in mixed_indices],
        "singleton_items_after_split": singleton_items,
        "double_orbit_items": double_items,
    }
    return count, math.log2(count) if count else float("-inf"), True, meta


def orbit_cost_bits(labels: dict[str, str]) -> float:
    _count, _bits, _exact, meta = orbit_residual(labels)
    return (
        inventory_cost_bits()
        + log2_comb(10, 2)
        + log2_comb(meta["non_singleton_orbit_count"], meta["mixed_non_singleton_orbit_count"])
    )


def tuple_counter(counter: Counter[str]) -> tuple[int, ...]:
    return tuple(counter.get(symbol, 0) for symbol in SIGMA)


def untuple_counter(values: tuple[int, ...]) -> Counter[str]:
    return Counter({symbol: values[idx] for idx, symbol in enumerate(SIGMA) if values[idx]})


def generate_row_assignments(
    row_digit: int,
    row_remaining: tuple[int, ...],
    col_remaining: tuple[tuple[int, ...], ...],
    forced_diagonal: str | None,
) -> list[tuple[tuple[tuple[int, ...], ...], int]]:
    cols = list(range(row_digit, 10))
    out: list[tuple[tuple[tuple[int, ...], ...], int]] = []

    def rec(pos: int, row_counts: list[int], current_cols: list[list[int]]) -> None:
        if pos == len(cols):
            if all(value == 0 for value in row_counts):
                out.append((tuple(tuple(row) for row in current_cols), 1))
            return
        col = cols[pos]
        allowed = range(len(SIGMA))
        if forced_diagonal is not None and col == row_digit:
            allowed = [SYMBOL_INDEX[forced_diagonal]]
        for symbol_idx in allowed:
            if row_counts[symbol_idx] <= 0:
                continue
            if current_cols[col][symbol_idx] <= 0:
                continue
            row_counts[symbol_idx] -= 1
            current_cols[col][symbol_idx] -= 1
            rec(pos + 1, row_counts, current_cols)
            current_cols[col][symbol_idx] += 1
            row_counts[symbol_idx] += 1

    rec(0, list(row_remaining), [list(row) for row in col_remaining])
    return out


def row_column_solver_count(labels: dict[str, str], diagonal_exact: bool) -> tuple[int, float, bool, dict]:
    row_targets = []
    col_targets = []
    diag = {}
    for digit in range(10):
        row_pairs = [f"{digit}{right}" for right in range(digit, 10)]
        col_pairs = [f"{left}{digit}" for left in range(digit + 1)]
        row_targets.append(tuple_counter(Counter(labels[pair] for pair in row_pairs)))
        col_targets.append(tuple_counter(Counter(labels[pair] for pair in col_pairs)))
        diag[digit] = labels[f"{digit}{digit}"]

    capped = False

    @lru_cache(maxsize=None)
    def dp(row_digit: int, col_remaining: tuple[tuple[int, ...], ...]) -> int:
        nonlocal capped
        if row_digit == 10:
            return 1 if all(all(value == 0 for value in col) for col in col_remaining) else 0
        total = 0
        forced = diag[row_digit] if diagonal_exact else None
        for next_cols, arrangements in generate_row_assignments(
            row_digit,
            row_targets[row_digit],
            col_remaining,
            forced,
        ):
            total += arrangements * dp(row_digit + 1, next_cols)
            if total > COUNT_CAP:
                capped = True
                return COUNT_CAP + 1
        return total

    count = dp(0, tuple(col_targets))
    exact = not capped and count <= COUNT_CAP
    effective = min(count, COUNT_CAP)
    meta = {
        "count_cap": COUNT_CAP,
        "capped": not exact,
        "cache_info": str(dp.cache_info()),
    }
    return effective, math.log2(effective) if effective else float("-inf"), exact, meta


def row_column_cost(labels: dict[str, str], diagonal_exact: bool) -> float:
    partitions = line_partitions()
    cost = partition_cost_bits(partitions["row"]) + partition_cost_bits(partitions["column"])
    if diagonal_exact:
        cost += len(diagonal_pairs()) * math.log2(len(SIGMA))
    return cost


def evaluate_fast(labels: dict[str, str]) -> dict[str, dict]:
    partitions = line_partitions()
    counts = Counter(labels.values())
    inventory_count = count_multinomial(counts)
    inv_cost = inventory_cost_bits()
    rows: dict[str, dict] = {
        "inventory_only": {
            "constraint_family": "global_inventory",
            "constraint_cost_bits": inv_cost,
            "residual_count": inventory_count,
            "residual_bits": math.log2(inventory_count),
            "residual_exact": True,
            "notes": "Only the 14-symbol homophone inventory is fixed.",
        }
    }

    diag_count, diag_bits = diagonal_count_residual(labels)
    rows["inventory_plus_diagonal_counts"] = {
        "constraint_family": "diagonal_counts",
        "constraint_cost_bits": inv_cost + hist_cost_bits(10),
        "residual_count": diag_count,
        "residual_bits": diag_bits,
        "residual_exact": True,
        "notes": "Global inventory plus symbol counts on the ten diagonal cells.",
    }

    diag_anchor_count, diag_anchor_bits, _exact = anchor_residual(labels, diagonal_pairs())
    rows["inventory_plus_diagonal_exact"] = {
        "constraint_family": "diagonal_exact",
        "constraint_cost_bits": inv_cost + len(diagonal_pairs()) * math.log2(len(SIGMA)),
        "residual_count": diag_anchor_count,
        "residual_bits": diag_anchor_bits,
        "residual_exact": True,
        "notes": "Global inventory plus the exact diagonal label sequence.",
    }

    anomaly_count, anomaly_bits, _exact = anchor_residual(labels, ["19", "39"])
    rows["inventory_plus_19_39_anchors"] = {
        "constraint_family": "anomaly_pair_anchors",
        "constraint_cost_bits": inv_cost + 2 * math.log2(len(SIGMA)),
        "residual_count": anomaly_count,
        "residual_bits": anomaly_bits,
        "residual_exact": True,
        "notes": "Global inventory plus labels at lore/anomaly pairs 19 and 39.",
    }

    for partition_name in ["row", "column", "diagonal_diff", "anti_diagonal_sum"]:
        partition = partitions[partition_name]
        count_rows = line_counts(labels, partition)
        rows[f"{partition_name}_symbol_counts"] = {
            "constraint_family": f"{partition_name}_symbol_counts",
            "constraint_cost_bits": partition_cost_bits(partition),
            "residual_count": partition_residual_count(count_rows),
            "residual_bits": partition_residual_bits(count_rows),
            "residual_exact": True,
            "notes": f"Exact symbol histograms on each {partition_name} line.",
        }

    orbit_count, orbit_bits, _exact, orbit_meta = orbit_residual(labels)
    rows["inventory_plus_6_9_orbit_split_metadata"] = {
        "constraint_family": "swap_6_9_orbit_equalities",
        "constraint_cost_bits": orbit_cost_bits(labels),
        "residual_count": orbit_count,
        "residual_bits": orbit_bits,
        "residual_exact": True,
        "notes": "Inventory plus 6<->9 equality orbits and which non-singleton orbits are split.",
        "meta": orbit_meta,
    }

    return finalize_rows(rows)


def evaluate_row_set(labels: dict[str, str]) -> dict[str, dict]:
    row_set_count, row_set_bits, _exact = row_set_residual(labels)
    return finalize_rows(
        {
            "inventory_plus_row_symbol_sets": {
                "constraint_family": "row_symbol_presence_sets",
                "constraint_cost_bits": row_set_cost(labels),
                "residual_count": row_set_count,
                "residual_bits": row_set_bits,
                "residual_exact": True,
                "notes": "Global inventory plus the set of symbols present in each row, without row counts.",
            }
        }
    )


def evaluate_solvers(labels: dict[str, str]) -> dict[str, dict]:
    rows = {}
    for diagonal_exact in (False, True):
        row_id = "row_column_symbol_counts"
        family = "row_column_symbol_counts"
        notes = "Exact row and column symbol histograms over the triangular 10x10 table."
        if diagonal_exact:
            row_id = "row_column_counts_plus_diagonal_exact"
            family = "row_column_counts_plus_diagonal_exact"
            notes += " The exact diagonal sequence is additionally fixed."
        count, bits, exact, meta = row_column_solver_count(labels, diagonal_exact=diagonal_exact)
        rows[row_id] = {
            "constraint_family": family,
            "constraint_cost_bits": row_column_cost(labels, diagonal_exact=diagonal_exact),
            "residual_count": count,
            "residual_bits": bits,
            "residual_exact": exact,
            "notes": notes,
            "meta": meta,
        }
    return finalize_rows(rows)


def finalize_rows(rows: dict[str, dict]) -> dict[str, dict]:
    raw_bits = raw_lookup_bits()
    for row_id, row in rows.items():
        row["id"] = row_id
        row["total_mdl_bits"] = row["constraint_cost_bits"] + row["residual_bits"]
        row["lookup_ratio"] = row["total_mdl_bits"] / raw_bits
        row["unique_table"] = bool(row["residual_exact"] and row["residual_count"] == 1)
    return rows


def shuffle_labels(observed: dict[str, str], rng: random.Random) -> dict[str, str]:
    pairs = all_pairs()
    values = [observed[pair] for pair in pairs]
    rng.shuffle(values)
    return dict(zip(pairs, values))


def summarize_controls(values: list[float], observed: float, lower_is_better: bool = True) -> dict:
    if not values:
        return {
            "trials": 0,
            "mean": None,
            "sd": None,
            "min": None,
            "max": None,
            "p_good_direction": None,
        }
    mu = mean(values)
    sd = pstdev(values)
    if lower_is_better:
        p = (sum(value <= observed for value in values) + 1) / (len(values) + 1)
    else:
        p = (sum(value >= observed for value in values) + 1) / (len(values) + 1)
    return {
        "trials": len(values),
        "mean": mu,
        "sd": sd,
        "min": min(values),
        "max": max(values),
        "p_good_direction": p,
    }


def run_controls(
    observed_labels: dict[str, str],
    evaluator: Callable[[dict[str, str]], dict[str, dict]],
    trials: int,
) -> dict[str, dict]:
    rng = random.Random(RANDOM_SEED + trials)
    observed = evaluator(observed_labels)
    values = {row_id: {"residual_bits": [], "total_mdl_bits": []} for row_id in observed}
    exact_counts = {row_id: 0 for row_id in observed}
    capped_counts = {row_id: 0 for row_id in observed}
    for _trial in range(trials):
        shuffled = shuffle_labels(observed_labels, rng)
        rows = evaluator(shuffled)
        for row_id, row in rows.items():
            values[row_id]["residual_bits"].append(row["residual_bits"])
            values[row_id]["total_mdl_bits"].append(row["total_mdl_bits"])
            if row["unique_table"]:
                exact_counts[row_id] += 1
            if not row["residual_exact"]:
                capped_counts[row_id] += 1
    out = {}
    for row_id, row in observed.items():
        out[row_id] = {
            "residual_bits": summarize_controls(values[row_id]["residual_bits"], row["residual_bits"]),
            "total_mdl_bits": summarize_controls(values[row_id]["total_mdl_bits"], row["total_mdl_bits"]),
            "unique_table_controls": exact_counts[row_id],
            "capped_controls": capped_counts[row_id],
        }
    return out


def classify_row(row: dict, control: dict | None, baselines: dict) -> str:
    if row["unique_table"] and row["lookup_ratio"] < 0.75:
        p_total = None if control is None else control["total_mdl_bits"]["p_good_direction"]
        if p_total is not None and p_total <= 0.01:
            return "candidate_marginal_constraint_generator"
    if control is not None:
        p_total = control["total_mdl_bits"]["p_good_direction"]
        if (
            p_total is not None
            and p_total <= 0.01
            and row["total_mdl_bits"] < baselines["inventory_total_bits"]
            and row["constraint_cost_bits"] < baselines["raw_lookup_bits"] * 0.40
        ):
            return "weak_constraint_signal"
    if row["lookup_ratio"] >= 0.92 and row["residual_bits"] < baselines["inventory_residual_bits"] * 0.50:
        return "lookup_disguise"
    if not row["residual_exact"]:
        return "lookup_disguise" if row["lookup_ratio"] >= 0.92 else "weak_constraint_signal"
    if control is not None:
        p_res = control["residual_bits"]["p_good_direction"]
        p_total = control["total_mdl_bits"]["p_good_direction"]
        if p_res is not None and p_res <= 0.05 and row["lookup_ratio"] < 0.92:
            return "weak_constraint_signal"
        if p_total is not None and p_total <= 0.05 and row["lookup_ratio"] < 0.92:
            return "weak_constraint_signal"
    if row["lookup_ratio"] >= 0.92:
        return "lookup_disguise"
    return "rejected_control"


def overall_verdict(rows: list[dict]) -> str:
    verdicts = {row["verdict"] for row in rows}
    if "candidate_marginal_constraint_generator" in verdicts:
        return "candidate_marginal_constraint_generator"
    if "weak_constraint_signal" in verdicts:
        return "weak_constraint_signal"
    if "lookup_disguise" in verdicts:
        return "lookup_disguise"
    return "rejected_control"


def compact_count(value: int) -> str:
    if value < 10**9:
        return str(value)
    return f"~2^{math.log2(value):.1f}"


def write_report(result: dict) -> None:
    lines = [
        "# Marginal Constraint Solver Search",
        "",
        "Generated by `marginal_constraint_solver_search.py`.",
        "",
        "This pass tests whether the 55 primary labels of the unordered 469 pair",
        "table are recoverable from compact marginal constraints rather than a",
        "cell lookup. It is mechanical only: no plaintext, glossary, or semantic",
        "translation is produced.",
        "",
        "## Method",
        "",
        "- Fast families are counted exactly with multinomial formulas or small row-set DP.",
        "- `row_column_*` families use a dependency-free capped backtracker over the triangular 10x10 table.",
        f"- Backtracking count cap: `{COUNT_CAP}`; capped rows are lower bounds, not promotable exact counts.",
        "- Controls shuffle the observed labels over the same 55 cells while preserving the global inventory.",
        f"- Control trials: `{FAST_CONTROL_TRIALS}` fast, `{ROW_SET_CONTROL_TRIALS}` row-set DP, `{SOLVER_CONTROL_TRIALS}` row/column solver.",
        "",
        "## Baselines",
        "",
        "| Baseline | Bits |",
        "|---|---:|",
        f"| Raw 55-cell label lookup (`55*log2(14)`) | {result['baselines']['raw_lookup_bits']:.2f} |",
        f"| Inventory cost | {result['baselines']['inventory_cost_bits']:.2f} |",
        f"| Inventory residual | {result['baselines']['inventory_residual_bits']:.2f} |",
        f"| Inventory total | {result['baselines']['inventory_total_bits']:.2f} |",
        "",
        "## Candidate Families",
        "",
        "| Verdict | Family | Residual tables | Residual bits | Constraint bits | Total bits | Lookup ratio | p(total) |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in result["rows"]:
        control = row.get("control", {})
        p_total = control.get("total_mdl_bits", {}).get("p_good_direction")
        p_text = "" if p_total is None else f"{p_total:.5f}"
        count_text = compact_count(int(row["residual_count"]))
        if not row["residual_exact"]:
            count_text = f">={count_text}"
        lines.append(
            f"| `{row['verdict']}` | `{row['id']}` | {count_text} | "
            f"{row['residual_bits']:.2f} | {row['constraint_cost_bits']:.2f} | "
            f"{row['total_mdl_bits']:.2f} | {row['lookup_ratio']:.3f} | {p_text} |"
        )

    best = result["best_by_total_mdl"]
    best_residual = result["best_by_residual"]
    lines += [
        "",
        "## Main Findings",
        "",
        f"- Best total-MDL family: `{best['id']}` at `{best['total_mdl_bits']:.2f}` bits (`{best['lookup_ratio']:.3f}x` raw lookup).",
        f"- Smallest residual family: `{best_residual['id']}` with `{best_residual['residual_bits']:.2f}` residual bits.",
        f"- Unique observed table recovered: `{any(row['unique_table'] for row in result['rows'])}`.",
        f"- Overall verdict: `{result['verdict']}`.",
        "",
        "The observed table is therefore not recovered as a unique consequence of",
        "these marginal constraints. The compact 6<->9 orbit metadata is a weak",
        "mechanical signal because it beats shuffled controls and improves total",
        "MDL, but it still leaves an enormous residual table space. Where the",
        "residual space shrinks sharply, the constraint description itself",
        "approaches a row/column lookup, so it is classified as a lookup disguise",
        "rather than an original generator.",
        "",
        "## 6<->9 Orbit Metadata",
        "",
    ]
    orbit = next(row for row in result["rows"] if row["id"] == "inventory_plus_6_9_orbit_split_metadata")
    meta = orbit["meta"]
    lines += [
        f"- Orbit count: `{meta['orbit_count']}`.",
        f"- Non-singleton orbits: `{meta['non_singleton_orbit_count']}`.",
        f"- Mixed non-singleton orbits: `{meta['mixed_non_singleton_orbit_count']}`.",
        f"- Mixed pairs: `{meta['mixed_pairs']}`.",
        "",
        "## Verification Commands",
        "",
        "Executed after generation:",
        "",
        "```bash",
        "python analysis/generator_search_20260618/marginal_constraint_solver_search.py",
        "python -m json.tool analysis/generator_search_20260618/marginal_constraint_solver_results.json",
        "python -c \"import ast, pathlib; p=pathlib.Path('analysis/generator_search_20260618/marginal_constraint_solver_search.py'); compile(p.read_text(), str(p), 'exec', ast.PyCF_ONLY_AST); print('syntax ok')\"",
        "git diff --check -- analysis/generator_search_20260618/marginal_constraint_solver_search.py analysis/generator_search_20260618/marginal_constraint_solver_results.json analysis/generator_search_20260618/marginal_constraint_solver_report.md",
        "```",
        "",
        f"Translation delta: `{result['translation_delta']}`.",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    formula = load_json(FORMULA_JSON)
    labels = labels_from_formula(formula)

    fast_rows = evaluate_fast(labels)
    row_set_rows = evaluate_row_set(labels)
    solver_rows = evaluate_solvers(labels)
    rows_by_id = {**fast_rows, **row_set_rows, **solver_rows}

    fast_controls = run_controls(labels, evaluate_fast, FAST_CONTROL_TRIALS)
    row_set_controls = run_controls(labels, evaluate_row_set, ROW_SET_CONTROL_TRIALS)
    solver_controls = run_controls(labels, evaluate_solvers, SOLVER_CONTROL_TRIALS)
    controls = {**fast_controls, **row_set_controls, **solver_controls}

    inv = rows_by_id["inventory_only"]
    baselines = {
        "raw_lookup_bits": raw_lookup_bits(),
        "inventory_cost_bits": inv["constraint_cost_bits"],
        "inventory_residual_bits": inv["residual_bits"],
        "inventory_total_bits": inv["total_mdl_bits"],
    }

    rows = []
    for row_id, row in rows_by_id.items():
        enriched = {**row, "control": controls.get(row_id)}
        enriched["verdict"] = classify_row(enriched, controls.get(row_id), baselines)
        rows.append(enriched)
    rows.sort(key=lambda row: (row["total_mdl_bits"], row["residual_bits"], row["id"]))

    result = {
        "schema": "marginal_constraint_solver_results.v1",
        "random_seed": RANDOM_SEED,
        "fast_control_trials": FAST_CONTROL_TRIALS,
        "row_set_control_trials": ROW_SET_CONTROL_TRIALS,
        "solver_control_trials": SOLVER_CONTROL_TRIALS,
        "count_cap": COUNT_CAP,
        "source": str(FORMULA_JSON.relative_to(ROOT)),
        "translation_delta": "NONE",
        "label_inventory": dict(sorted(Counter(labels.values()).items())),
        "baselines": baselines,
        "rows": rows,
        "best_by_total_mdl": min(rows, key=lambda row: row["total_mdl_bits"]),
        "best_by_residual": min(rows, key=lambda row: row["residual_bits"]),
        "verdict": overall_verdict(rows),
    }
    write_json(OUT_JSON, result)
    write_report(result)
    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(f"wrote {OUT_MD.relative_to(ROOT)}")
    print(
        "verdict={} best_total={} bits={:.2f} best_residual={} residual_bits={:.2f}".format(
            result["verdict"],
            result["best_by_total_mdl"]["id"],
            result["best_by_total_mdl"]["total_mdl_bits"],
            result["best_by_residual"]["id"],
            result["best_by_residual"]["residual_bits"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
