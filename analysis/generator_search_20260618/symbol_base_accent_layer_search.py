#!/usr/bin/env python3
"""Symbol base+accent layer search for the 469 pair table.

Most table-origin searches treat the 14 internal symbols as atomic labels. This
pass tests a different authoring hypothesis: the visible/internal symbols may
be a refinement of a smaller base alphabet plus an accent/variant layer.

The model charges:

- the symbol partition into base classes;
- a base-label table, either raw over 55 cells or split-lossless under the
  weak 6<->9 quotient;
- a default symbol per base class plus explicit accent exceptions.

No plaintext, glossary, or semantic translation is promoted.
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

OUT_JSON = HERE / "symbol_base_accent_layer_results.json"
OUT_MD = HERE / "symbol_base_accent_layer_report.md"

SIGMA = "*ABCEFILNORSTV"
SYMBOL_BITS = math.log2(len(SIGMA))
RAW_LOOKUP_BITS = 55 * SYMBOL_BITS
TRANSFORM_6_9_BITS = math.log2(45) + math.log2(8)
RANDOM_SEED = 46920260619
CONTROL_TRIALS = 80
MAX_K = 5


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def log2_comb(n: int, k: int) -> float:
    if k < 0 or k > n:
        return float("inf")
    if k == 0 or k == n:
        return 0.0
    return math.log2(math.comb(n, k))


def pair_key(pair: tuple[int, int]) -> str:
    return f"{pair[0]}{pair[1]}"


def natural_pairs() -> list[tuple[int, int]]:
    return [(a, b) for a in range(10) for b in range(a, 10)]


PAIR_LIST = natural_pairs()
PAIR_INDEX = {pair: index for index, pair in enumerate(PAIR_LIST)}


def symbol_key(symbol: str) -> int:
    return SIGMA.index(symbol)


def primary_pair_symbol(pair_table: dict[str, dict[str, Any]], pair: tuple[int, int]) -> str:
    cell = pair_table[pair_key(pair)]
    if cell["status"] == "pure":
        return cell["symbol_if_pure"]
    return min(cell["symbols"], key=symbol_key)


def all_pair_labels(formula: dict[str, Any]) -> list[str]:
    return [primary_pair_symbol(formula["pair_table"], pair) for pair in PAIR_LIST]


def unique_in_order(values: list[str]) -> str:
    out = []
    for value in values:
        if value in SIGMA and value not in out:
            out.append(value)
    for value in SIGMA:
        if value not in out:
            out.append(value)
    return "".join(out)


def symbol_orders(labels: list[str]) -> list[dict[str, Any]]:
    counts = Counter(labels)
    freq_desc = "".join(sorted(SIGMA, key=lambda symbol: (-counts[symbol], symbol_key(symbol))))
    first_use = unique_in_order(labels)
    lore_texts = {
        "tibia": "TIBIA",
        "bonelord": "BONELORD",
        "magic_web": "MAGICWEB",
    }
    rows = [
        {"id": "sigma", "symbols": SIGMA, "bits": 1.0, "source": "fixed"},
        {"id": "sigma_reverse", "symbols": SIGMA[::-1], "bits": 1.2, "source": "fixed"},
        {"id": "frequency_desc", "symbols": freq_desc, "bits": 2.5, "source": "frequency"},
        {"id": "frequency_asc", "symbols": freq_desc[::-1], "bits": 2.7, "source": "frequency"},
        {"id": "pair_table_first_use", "symbols": first_use, "bits": 3.0, "source": "code_table"},
        {"id": "pair_table_first_use_reverse", "symbols": first_use[::-1], "bits": 3.2, "source": "code_table"},
    ]
    for key, text in lore_texts.items():
        rows.append({"id": f"lore_{key}", "symbols": unique_in_order(list(text)), "bits": 4.0, "source": "lore"})
    dedup: dict[str, dict[str, Any]] = {}
    for row in rows:
        dedup.setdefault(row["symbols"], row)
    return list(dedup.values())


def contiguous_partitions(order: dict[str, Any]) -> list[dict[str, Any]]:
    symbols = order["symbols"]
    rows = []
    for k in range(2, MAX_K + 1):
        for cuts in itertools.combinations(range(1, len(symbols)), k - 1):
            starts = (0,) + cuts
            ends = cuts + (len(symbols),)
            groups = [symbols[start:end] for start, end in zip(starts, ends)]
            rows.append(
                {
                    "id": f"{order['id']}|contiguous|k={k}|cuts={','.join(map(str, cuts))}",
                    "family": "contiguous_symbol_order",
                    "k": k,
                    "groups": groups,
                    "partition_bits": order["bits"] + log2_comb(len(symbols) - 1, k - 1),
                    "order_id": order["id"],
                    "order_source": order["source"],
                }
            )
    return rows


def grouped_by_counts(labels: list[str]) -> list[dict[str, Any]]:
    counts = Counter(labels)
    by_count: dict[int, list[str]] = defaultdict(list)
    for symbol in SIGMA:
        by_count[counts[symbol]].append(symbol)
    groups = ["".join(sorted(values, key=symbol_key)) for _count, values in sorted(by_count.items(), key=lambda item: -item[0])]
    return [
        {
            "id": "exact_frequency_ties",
            "family": "frequency_tie_partition",
            "k": len(groups),
            "groups": groups,
            "partition_bits": 6.0,
            "order_id": "frequency_ties",
            "order_source": "frequency",
        }
    ]


def partition_map(groups: list[str]) -> dict[str, int]:
    out = {}
    for index, group in enumerate(groups):
        for symbol in group:
            out[symbol] = index
    if set(out) != set(SIGMA):
        raise ValueError(groups)
    return out


def swap_pair(pair: tuple[int, int]) -> tuple[int, int]:
    a, b = pair
    a = 9 if a == 6 else 6 if a == 9 else a
    b = 9 if b == 6 else 6 if b == 9 else b
    return (a, b) if a <= b else (b, a)


def swap_orbits() -> list[list[int]]:
    remaining = set(PAIR_LIST)
    out = []
    while remaining:
        seed = min(remaining)
        orbit = {seed, swap_pair(seed)}
        out.append(sorted(PAIR_INDEX[pair] for pair in orbit))
        remaining -= orbit
    return sorted(out, key=lambda orbit: (len(orbit), orbit[0]))


SWAP_ORBITS = swap_orbits()


def base_raw_bits(base_labels: list[int], k: int) -> dict[str, Any]:
    bits = len(base_labels) * math.log2(k)
    return {
        "base_model": "raw_55_base_lookup",
        "base_bits": bits,
        "base_mixed_orbits": None,
        "base_label_slots": len(base_labels),
    }


def base_swap_bits(base_labels: list[int], k: int) -> dict[str, Any]:
    mixed = 0
    slots = 0
    for orbit in SWAP_ORBITS:
        values = {base_labels[index] for index in orbit}
        if len(values) > 1:
            mixed += 1
            slots += len(orbit)
        else:
            slots += 1
    non_singleton = sum(1 for orbit in SWAP_ORBITS if len(orbit) > 1)
    selector_bits = log2_comb(non_singleton, mixed)
    bits = TRANSFORM_6_9_BITS + selector_bits + slots * math.log2(k)
    return {
        "base_model": "swap_6_9_base_split_lossless",
        "base_bits": bits,
        "base_mixed_orbits": mixed,
        "base_label_slots": slots,
        "base_selector_bits": selector_bits,
    }


def accent_bits(labels: list[str], base_labels: list[int], groups: list[str]) -> dict[str, Any]:
    cells_by_base: dict[int, list[int]] = defaultdict(list)
    for index, base in enumerate(base_labels):
        cells_by_base[base].append(index)
    default_bits = 0.0
    exception_bits = 0.0
    exceptions = []
    defaults = {}
    for base, cells in sorted(cells_by_base.items()):
        group = groups[base]
        if len(group) == 1:
            defaults[base] = group
            continue
        counts = Counter(labels[index] for index in cells)
        default = min(counts, key=lambda symbol: (-counts[symbol], symbol_key(symbol)))
        defaults[base] = default
        default_bits += math.log2(len(group))
        for index in cells:
            if labels[index] == default:
                continue
            alt_count = max(1, len(group) - 1)
            cost = math.log2(len(cells)) + math.log2(alt_count)
            exception_bits += cost
            exceptions.append(
                {
                    "pair": pair_key(PAIR_LIST[index]),
                    "base": base,
                    "default": default,
                    "actual": labels[index],
                    "cost_bits": cost,
                }
            )
    return {
        "accent_default_bits": default_bits,
        "accent_exception_bits": exception_bits,
        "accent_exception_count": len(exceptions),
        "accent_bits": default_bits + exception_bits,
        "defaults": {str(key): value for key, value in defaults.items()},
        "exceptions": exceptions[:80],
    }


def evaluate_partition(labels: list[str], part: dict[str, Any], base_model: str) -> dict[str, Any]:
    mapping = partition_map(part["groups"])
    base_labels = [mapping[symbol] for symbol in labels]
    if base_model == "raw":
        base = base_raw_bits(base_labels, part["k"])
    elif base_model == "swap_6_9":
        base = base_swap_bits(base_labels, part["k"])
    else:
        raise ValueError(base_model)
    accent = accent_bits(labels, base_labels, part["groups"])
    total_bits = part["partition_bits"] + base["base_bits"] + accent["accent_bits"]
    return {
        **{key: value for key, value in part.items() if key != "groups"},
        "groups": part["groups"],
        **base,
        **accent,
        "total_bits": total_bits,
        "lookup_ratio": total_bits / RAW_LOOKUP_BITS,
        "gain_vs_raw_lookup_bits": RAW_LOOKUP_BITS - total_bits,
    }


def candidate_partitions(labels: list[str]) -> list[dict[str, Any]]:
    rows = []
    for order in symbol_orders(labels):
        rows.extend(contiguous_partitions(order))
    rows.extend(grouped_by_counts(labels))
    dedup: dict[tuple[str, ...], dict[str, Any]] = {}
    for row in rows:
        key = tuple(sorted("".join(sorted(group)) for group in row["groups"]))
        current = dedup.get(key)
        if current is None or row["partition_bits"] < current["partition_bits"]:
            dedup[key] = row
    return list(dedup.values())


def run_search(labels: list[str]) -> dict[str, Any]:
    rows = []
    partitions = candidate_partitions(labels)
    for part in partitions:
        rows.append(evaluate_partition(labels, part, "raw"))
        rows.append(evaluate_partition(labels, part, "swap_6_9"))
    rows.sort(
        key=lambda row: (
            -row["gain_vs_raw_lookup_bits"],
            row["accent_exception_count"],
            row["k"],
            row["id"],
            row["base_model"],
        )
    )
    return {
        "candidate_partition_count": len(partitions),
        "candidate_model_count": len(rows),
        "best": rows[0],
        "top_rows": rows[:80],
    }


def controls(labels: list[str], observed: dict[str, Any]) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED)
    gains = []
    bits = []
    exceptions = []
    base_mixed = []
    for _ in range(CONTROL_TRIALS):
        shuffled = labels[:]
        rng.shuffle(shuffled)
        best = run_search(shuffled)["best"]
        gains.append(best["gain_vs_raw_lookup_bits"])
        bits.append(best["total_bits"])
        exceptions.append(best["accent_exception_count"])
        base_mixed.append(best["base_mixed_orbits"] if best["base_mixed_orbits"] is not None else 99)
    best_obs = observed["best"]
    return {
        "trials": CONTROL_TRIALS,
        "inventory_label_shuffle": {
            "best_gain_vs_raw_lookup_bits": summarize(gains, best_obs["gain_vs_raw_lookup_bits"], True),
            "best_total_bits": summarize(bits, best_obs["total_bits"], False),
            "accent_exception_count": summarize(exceptions, best_obs["accent_exception_count"], False),
            "base_mixed_orbits": summarize(base_mixed, best_obs["base_mixed_orbits"] if best_obs["base_mixed_orbits"] is not None else 99, False),
        },
    }


def summarize(values: list[float], observed: float, higher_is_better: bool) -> dict[str, Any]:
    mean = sum(values) / len(values)
    sd = (sum((value - mean) ** 2 for value in values) / (len(values) - 1)) ** 0.5 if len(values) > 1 else 0.0
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


def verdict(result: dict[str, Any]) -> str:
    best = result["observed"]["best"]
    p = result["controls"]["inventory_label_shuffle"]["best_gain_vs_raw_lookup_bits"]["p_good_direction"]
    if best["gain_vs_raw_lookup_bits"] > 0 and p <= 0.05 and best["base_model"] == "swap_6_9":
        return "candidate_symbol_base_accent_with_6_9"
    if best["gain_vs_raw_lookup_bits"] > 0 and p <= 0.05:
        return "weak_symbol_base_accent_compression"
    if best["gain_vs_raw_lookup_bits"] > 0:
        return "symbol_base_accent_positive_control_sensitive"
    return "symbol_base_accent_not_promoted"


def write_report(result: dict[str, Any]) -> None:
    best = result["observed"]["best"]
    ctrl = result["controls"]["inventory_label_shuffle"]
    lines = [
        "# Symbol Base+Accent Layer Search",
        "",
        "Generated by `symbol_base_accent_layer_search.py`.",
        "",
        "This pass asks whether the 14 internal symbols are better treated as",
        "a smaller base alphabet plus accent/refinement exceptions. It assigns",
        "no plaintext.",
        "",
        "## Best Model",
        "",
        "| Base model | k | Partition | Accent exceptions | Bits | Lookup ratio | Gain | Control p |",
        "|---|---:|---|---:|---:|---:|---:|---:|",
        f"| `{best['base_model']}` | {best['k']} | `{best['id']}` | {best['accent_exception_count']} | {best['total_bits']:.2f} | {best['lookup_ratio']:.3f} | {best['gain_vs_raw_lookup_bits']:.2f} | {ctrl['best_gain_vs_raw_lookup_bits']['p_good_direction']:.5f} |",
        "",
        f"Groups: `{'; '.join(best['groups'])}`.",
        "",
        "## Controls",
        "",
        "| Metric | Observed | Mean | Max/Min | p(good) |",
        "|---|---:|---:|---:|---:|",
        f"| best gain vs raw lookup | {ctrl['best_gain_vs_raw_lookup_bits']['observed']:.2f} | {ctrl['best_gain_vs_raw_lookup_bits']['mean']:.2f} | {ctrl['best_gain_vs_raw_lookup_bits']['max']:.2f} | {ctrl['best_gain_vs_raw_lookup_bits']['p_good_direction']:.5f} |",
        f"| best total bits | {ctrl['best_total_bits']['observed']:.2f} | {ctrl['best_total_bits']['mean']:.2f} | {ctrl['best_total_bits']['min']:.2f} | {ctrl['best_total_bits']['p_good_direction']:.5f} |",
        f"| accent exceptions | {ctrl['accent_exception_count']['observed']:.0f} | {ctrl['accent_exception_count']['mean']:.2f} | {ctrl['accent_exception_count']['min']:.0f} | {ctrl['accent_exception_count']['p_good_direction']:.5f} |",
        "",
        "## Interpretation",
        "",
        "A base+accent layer would be useful if it reduced the table below raw",
        "symbol lookup and survived the same partition search on inventory-preserving",
        "label shuffles. This pass charges the partition and does not allow the",
        "accent layer to become free per-cell lookup.",
        "",
        f"Verdict: `{result['verdict']}`.",
        "",
        "Translation delta: `NONE`.",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    formula = load_json(FORMULA_JSON)
    labels = all_pair_labels(formula)
    observed = run_search(labels)
    result = {
        "schema": "symbol_base_accent_layer_results.v1",
        "translation_delta": "NONE",
        "baselines": {
            "raw_lookup_bits": RAW_LOOKUP_BITS,
            "symbol_bits": SYMBOL_BITS,
        },
        "observed": observed,
    }
    result["controls"] = controls(labels, observed)
    result["verdict"] = verdict(result)
    write_json(OUT_JSON, result)
    write_report(result)
    print(f"wrote {OUT_JSON.relative_to(HERE)}")
    print(f"wrote {OUT_MD.relative_to(HERE)}")
    print(
        "verdict={verdict} gain={gain:.2f} model={model}".format(
            verdict=result["verdict"],
            gain=observed["best"]["gain_vs_raw_lookup_bits"],
            model=observed["best"]["base_model"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
