#!/usr/bin/env python3
"""Frequency-weighted stochastic inventory model for the 469 pair table.

Most deterministic placement searches failed. This pass formalizes the
strongest positive clue found so far:

    1. give every internal symbol at least one unordered pair cell;
    2. distribute the remaining pair cells by internal corpus frequency;
    3. place those labels across the 55 cells without a detectable geometric
       rule.

This is a stochastic mechanical generator candidate, not a semantic
translation and not a claim that the exact random seed is recoverable.
"""

from __future__ import annotations

import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FORMULA_JSON = ROOT / "analysis" / "mechanism_model_20260618" / "mechanical_formula_469.json"
OCC_STREAMS = ROOT / "analysis" / "audit_20260609" / "homophone_channel" / "occ_streams.json"

OUT_JSON = HERE / "frequency_weighted_stochastic_inventory_results.json"
OUT_MD = HERE / "frequency_weighted_stochastic_inventory_report.md"

SIGMA = "*ABCEFILNORSTV"
RANDOM_SEED = 46920260620
TRIALS = 100000
PLACEMENT_TRIALS = 20000


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def all_pairs() -> list[str]:
    return [f"{i}{j}" for i in range(10) for j in range(i, 10)]


def primary_pair_symbol(pair_table: dict, pair: str) -> str:
    row = pair_table[pair]
    if row["status"] == "pure":
        return row["symbol_if_pure"]
    return sorted(row["symbols"])[0]


def corpus_symbol_counts() -> Counter[str]:
    occ = load_json(OCC_STREAMS)["occ"]
    return Counter({symbol: len(rows) for symbol, rows in occ.items()})


def pearson(xs: list[float], ys: list[float]) -> float:
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    dx = sum((x - mx) ** 2 for x in xs)
    dy = sum((y - my) ** 2 for y in ys)
    if not dx or not dy:
        return 0.0
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / math.sqrt(dx * dy)


def ranks(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda idx: values[idx])
    out = [0.0] * len(values)
    idx = 0
    while idx < len(order):
        end = idx + 1
        while end < len(order) and values[order[end]] == values[order[idx]]:
            end += 1
        rank = (idx + end - 1) / 2 + 1
        for pos in range(idx, end):
            out[order[pos]] = rank
        idx = end
    return out


def spearman(xs: list[float], ys: list[float]) -> float:
    return pearson(ranks(xs), ranks(ys))


def log2_multinomial_prob(counts: Counter[str], probs: dict[str, float]) -> float:
    total = sum(counts.values())
    log2p = (math.lgamma(total + 1) - sum(math.lgamma(counts[symbol] + 1) for symbol in SIGMA)) / math.log(2)
    for symbol in SIGMA:
        count = counts[symbol]
        if count:
            log2p += count * math.log2(probs[symbol])
    return log2p


def multinomial_sample(rng: random.Random, total: int, probs: dict[str, float]) -> Counter[str]:
    symbols = list(SIGMA)
    cumulative = []
    acc = 0.0
    for symbol in symbols:
        acc += probs[symbol]
        cumulative.append((acc, symbol))
    out = Counter()
    for _ in range(total):
        value = rng.random()
        for limit, symbol in cumulative:
            if value <= limit:
                out[symbol] += 1
                break
    return out


def l1_to_expected(counts: Counter[str], expected: dict[str, float]) -> float:
    return sum(abs(counts[symbol] - expected[symbol]) for symbol in SIGMA)


def max_abs_to_expected(counts: Counter[str], expected: dict[str, float]) -> float:
    return max(abs(counts[symbol] - expected[symbol]) for symbol in SIGMA)


def summarize(values: list[float], observed: float, high_is_good: bool) -> dict:
    mean = sum(values) / len(values)
    sd = (sum((value - mean) ** 2 for value in values) / (len(values) - 1)) ** 0.5
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


def centrality_p(values: list[float], observed: float) -> dict:
    low = (sum(value <= observed for value in values) + 1) / (len(values) + 1)
    high = (sum(value >= observed for value in values) + 1) / (len(values) + 1)
    return {"p_le": low, "p_ge": high, "two_sided_tail": 2 * min(low, high)}


def pair_coords(pair: str) -> tuple[int, int]:
    return int(pair[0]), int(pair[1])


def placement_metrics(labels_by_pair: dict[str, str]) -> dict:
    pairs = all_pairs()
    by_symbol = defaultdict(list)
    for pair, symbol in labels_by_pair.items():
        by_symbol[symbol].append(pair)

    distances = []
    for symbol_pairs in by_symbol.values():
        for idx, left in enumerate(symbol_pairs):
            x1, y1 = pair_coords(left)
            for right in symbol_pairs[idx + 1 :]:
                x2, y2 = pair_coords(right)
                distances.append(abs(x1 - x2) + abs(y1 - y2))
    adjacent_total = 0
    adjacent_same = 0
    for idx, left in enumerate(pairs):
        x1, y1 = pair_coords(left)
        for right in pairs[idx + 1 :]:
            x2, y2 = pair_coords(right)
            if abs(x1 - x2) + abs(y1 - y2) == 1:
                adjacent_total += 1
                adjacent_same += labels_by_pair[left] == labels_by_pair[right]

    features = {
        "x": [int(pair[0]) for pair in pairs],
        "y": [int(pair[1]) for pair in pairs],
        "sum": [int(pair[0]) + int(pair[1]) for pair in pairs],
        "diff": [int(pair[1]) - int(pair[0]) for pair in pairs],
        "product": [int(pair[0]) * int(pair[1]) for pair in pairs],
        "diagonal": [int(pair[0]) == int(pair[1]) for pair in pairs],
        "sum_mod3": [(int(pair[0]) + int(pair[1])) % 3 for pair in pairs],
    }

    def majority_accuracy(keys: list) -> float:
        grouped = defaultdict(list)
        for pair, key in zip(pairs, keys):
            grouped[key].append(labels_by_pair[pair])
        majority = {key: Counter(values).most_common(1)[0][0] for key, values in grouped.items()}
        return sum(majority[key] == labels_by_pair[pair] for pair, key in zip(pairs, keys)) / len(pairs)

    return {
        "mean_same_symbol_distance": sum(distances) / len(distances),
        "adjacent_same_fraction": adjacent_same / adjacent_total,
        "best_single_feature_accuracy": max(majority_accuracy(keys) for keys in features.values()),
    }


def placement_control(labels_by_pair: dict[str, str]) -> dict:
    rng = random.Random(RANDOM_SEED + 1)
    pairs = all_pairs()
    labels = [labels_by_pair[pair] for pair in pairs]
    observed = placement_metrics(labels_by_pair)
    values = {key: [] for key in observed}
    shuffled = labels[:]
    for _trial in range(PLACEMENT_TRIALS):
        rng.shuffle(shuffled)
        current = {pair: symbol for pair, symbol in zip(pairs, shuffled)}
        metrics = placement_metrics(current)
        for key, value in metrics.items():
            values[key].append(value)
    return {
        "observed": observed,
        "mean_same_symbol_distance": {
            **summarize(values["mean_same_symbol_distance"], observed["mean_same_symbol_distance"], high_is_good=False),
            **{f"central_{k}": v for k, v in centrality_p(values["mean_same_symbol_distance"], observed["mean_same_symbol_distance"]).items()},
        },
        "adjacent_same_fraction": {
            **summarize(values["adjacent_same_fraction"], observed["adjacent_same_fraction"], high_is_good=True),
            **{f"central_{k}": v for k, v in centrality_p(values["adjacent_same_fraction"], observed["adjacent_same_fraction"]).items()},
        },
        "best_single_feature_accuracy": summarize(
            values["best_single_feature_accuracy"],
            observed["best_single_feature_accuracy"],
            high_is_good=True,
        ),
    }


def main() -> int:
    formula = load_json(FORMULA_JSON)
    pair_table = formula["pair_table"]
    corpus_counts = corpus_symbol_counts()
    total_corpus = sum(corpus_counts.values())
    probs = {symbol: corpus_counts[symbol] / total_corpus for symbol in SIGMA}
    uniform = {symbol: 1 / len(SIGMA) for symbol in SIGMA}

    labels_by_pair = {pair: primary_pair_symbol(pair_table, pair) for pair in all_pairs()}
    observed_counts = Counter(labels_by_pair.values())
    if any(observed_counts[symbol] < 1 for symbol in SIGMA):
        raise ValueError("floor-one model requires every symbol to appear at least once")
    extra_counts = Counter({symbol: observed_counts[symbol] - 1 for symbol in SIGMA})
    extra_total = sum(extra_counts.values())
    expected_extra = {symbol: extra_total * probs[symbol] for symbol in SIGMA}

    log2_floor_frequency = log2_multinomial_prob(extra_counts, probs)
    log2_floor_uniform = log2_multinomial_prob(extra_counts, uniform)
    bits_gain_vs_uniform = log2_floor_frequency - log2_floor_uniform
    log2_all_frequency = log2_multinomial_prob(observed_counts, probs)
    log2_all_uniform = log2_multinomial_prob(observed_counts, uniform)

    observed_l1 = l1_to_expected(extra_counts, expected_extra)
    observed_max_abs = max_abs_to_expected(extra_counts, expected_extra)
    observed_corr = pearson([observed_counts[symbol] for symbol in SIGMA], [corpus_counts[symbol] for symbol in SIGMA])
    observed_spearman = spearman([observed_counts[symbol] for symbol in SIGMA], [corpus_counts[symbol] for symbol in SIGMA])

    rng = random.Random(RANDOM_SEED)
    sim_l1 = []
    sim_max_abs = []
    sim_corr = []
    sim_spearman = []
    for _trial in range(TRIALS):
        sample_extra = multinomial_sample(rng, extra_total, probs)
        sample_counts = Counter({symbol: sample_extra[symbol] + 1 for symbol in SIGMA})
        sim_l1.append(l1_to_expected(sample_extra, expected_extra))
        sim_max_abs.append(max_abs_to_expected(sample_extra, expected_extra))
        sim_corr.append(pearson([sample_counts[symbol] for symbol in SIGMA], [corpus_counts[symbol] for symbol in SIGMA]))
        sim_spearman.append(spearman([sample_counts[symbol] for symbol in SIGMA], [corpus_counts[symbol] for symbol in SIGMA]))

    placement = placement_control(labels_by_pair)
    l1_central = centrality_p(sim_l1, observed_l1)
    corr_central = centrality_p(sim_corr, observed_corr)
    verdict = "candidate_generator_stochastic_inventory"
    if bits_gain_vs_uniform < 10 or l1_central["two_sided_tail"] < 0.02 or corr_central["two_sided_tail"] < 0.02:
        verdict = "rejected_control"

    result = {
        "schema": "frequency_weighted_stochastic_inventory_results.v1",
        "random_seed": RANDOM_SEED,
        "trials": TRIALS,
        "placement_trials": PLACEMENT_TRIALS,
        "alphabet": list(SIGMA),
        "observed_primary_pair_counts": dict(observed_counts),
        "observed_extra_counts_after_one_each": dict(extra_counts),
        "corpus_symbol_counts": dict(corpus_counts),
        "corpus_probabilities": probs,
        "expected_extra_counts": expected_extra,
        "model_comparison": {
            "floor_frequency_log2_probability": log2_floor_frequency,
            "floor_uniform_log2_probability": log2_floor_uniform,
            "floor_frequency_bits_gain_vs_uniform": bits_gain_vs_uniform,
            "all_slots_frequency_log2_probability": log2_all_frequency,
            "all_slots_uniform_log2_probability": log2_all_uniform,
            "all_slots_frequency_bits_gain_vs_uniform": log2_all_frequency - log2_all_uniform,
        },
        "fit_metrics": {
            "extra_l1_to_expected": {**summarize(sim_l1, observed_l1, high_is_good=False), **{f"central_{k}": v for k, v in l1_central.items()}},
            "extra_max_abs_to_expected": summarize(sim_max_abs, observed_max_abs, high_is_good=False),
            "pair_count_pearson_vs_corpus": {**summarize(sim_corr, observed_corr, high_is_good=True), **{f"central_{k}": v for k, v in corr_central.items()}},
            "pair_count_spearman_vs_corpus": summarize(sim_spearman, observed_spearman, high_is_good=True),
        },
        "placement_randomness": placement,
        "formula_candidate": [
            "Give each internal symbol one unordered pair cell.",
            "Allocate the remaining 41 cells by corpus symbol frequency.",
            "Place labels across unordered pair cells without a detected deterministic layout rule.",
        ],
        "verdict": verdict,
        "method_note": "Uses the primary label for conflict cell {19}; the mechanical formula still records the {19,91} I/N conflict explicitly.",
    }
    write_json(OUT_JSON, result)

    lines = [
        "# Frequency-Weighted Stochastic Inventory",
        "",
        "Generated by `frequency_weighted_stochastic_inventory.py`.",
        "",
        "This is the strongest currently supported formula-like generator: give",
        "every internal symbol at least one pair cell, then allocate the remaining",
        "41 cells according to internal corpus frequency. Exact cell placement is",
        "treated as random/hand placement unless a later rule explains it.",
        "",
        "## Model Comparison",
        "",
        "| Model | log2 probability | bits vs uniform |",
        "|---|---:|---:|",
        f"| one-each + frequency extras | {log2_floor_frequency:.2f} | {bits_gain_vs_uniform:.2f} |",
        f"| one-each + uniform extras | {log2_floor_uniform:.2f} | 0.00 |",
        f"| all-slots frequency | {log2_all_frequency:.2f} | {log2_all_frequency - log2_all_uniform:.2f} |",
        f"| all-slots uniform | {log2_all_uniform:.2f} | 0.00 |",
        "",
        "## Fit Under Frequency Model",
        "",
        "| Metric | Observed | Control mean | central two-sided p |",
        "|---|---:|---:|---:|",
        (
            f"| extra L1 to expected | {observed_l1:.3f} | "
            f"{sum(sim_l1)/len(sim_l1):.3f} | {l1_central['two_sided_tail']:.3f} |"
        ),
        (
            f"| pair-count Pearson vs corpus | {observed_corr:.3f} | "
            f"{sum(sim_corr)/len(sim_corr):.3f} | {corr_central['two_sided_tail']:.3f} |"
        ),
        "",
        "## Placement Randomness Check",
        "",
        "| Metric | Observed | Control mean | p high/low |",
        "|---|---:|---:|---:|",
        (
            f"| mean same-symbol distance | {placement['observed']['mean_same_symbol_distance']:.3f} | "
            f"{placement['mean_same_symbol_distance']['control_mean']:.3f} | "
            f"{placement['mean_same_symbol_distance']['central_two_sided_tail']:.3f} |"
        ),
        (
            f"| adjacent same fraction | {placement['observed']['adjacent_same_fraction']:.3f} | "
            f"{placement['adjacent_same_fraction']['control_mean']:.3f} | "
            f"{placement['adjacent_same_fraction']['central_two_sided_tail']:.3f} |"
        ),
        (
            f"| best single-feature accuracy | {placement['observed']['best_single_feature_accuracy']:.3f} | "
            f"{placement['best_single_feature_accuracy']['control_mean']:.3f} | "
            f"{placement['best_single_feature_accuracy']['p_good_direction']:.3f} |"
        ),
        "",
        "## Verdict",
        "",
        f"`{verdict}`.",
        "",
        "This does not recover an exact deterministic seed. It does provide a",
        "compact stochastic mechanical formula for the homophone inventory, while",
        "leaving exact cell placement as random/hand placement under current",
        "evidence.",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(f"verdict={verdict} bits_gain={bits_gain_vs_uniform:.2f} l1_tail={l1_central['two_sided_tail']:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
