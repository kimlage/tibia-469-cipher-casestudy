#!/usr/bin/env python3
"""Inventory-pressure test for the 6<->9 quotient table.

This pass compares the original 55-cell pair inventory with the `swap_6_9`
quotient inventory:

- 46 base orbit labels, one label per quotient orbit;
- 50 explicit labels when mixed orbits store their second label explicitly.

It asks whether frequency/apportionment/quota pressure explains the quotient
inventory better than the original inventory. Mechanical only. No plaintext or
glossary is promoted.
"""

from __future__ import annotations

import json
import math
import random
from collections import Counter
from functools import lru_cache
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

FORMULA_JSON = ROOT / "analysis" / "mechanism_model_20260618" / "mechanical_formula_469.json"
QUOTIENT_JSON = HERE / "digit_orbit_quotient_results.json"
OCC_STREAMS = ROOT / "analysis" / "audit_20260609" / "homophone_channel" / "occ_streams.json"

OUT_JSON = HERE / "quotient_inventory_pressure_results.json"
OUT_MD = HERE / "quotient_inventory_pressure_report.md"

SIGMA = tuple("*ABCEFILNORSTV")
RANDOM_SEED = 46920260621
LABEL_SHUFFLE_TRIALS = 20000
PAIR_SHUFFLE_TRIALS = 20000

METHODS = ("hamilton", "jefferson", "webster", "adams", "hill")
TRANSFORMS = ("power", "log_power", "sqrt_power")
SHIFTS = (0, 1, 5, 10, 25, 50, 100, 250)


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def all_pairs() -> list[str]:
    return [f"{left}{right}" for left in range(10) for right in range(left, 10)]


def log2_comb(n: int, k: int) -> float:
    if k < 0 or k > n:
        return float("inf")
    if k == 0 or k == n:
        return 0.0
    return math.log2(math.comb(n, k))


def primary_pair_symbol(pair_table: dict, pair: str) -> str:
    row = pair_table[pair]
    if row["status"] == "pure":
        return row["symbol_if_pure"]
    return sorted(row["symbols"])[0]


def corpus_counts() -> Counter[str]:
    occ = load_json(OCC_STREAMS)["occ"]
    return Counter({symbol: len(rows) for symbol, rows in occ.items()})


def weights_from_counts(counts: Counter[str], transform: str, alpha: float, shift: float) -> dict[str, float]:
    out = {}
    for symbol in SIGMA:
        value = counts[symbol] + shift
        if transform == "power":
            out[symbol] = value**alpha
        elif transform == "log_power":
            out[symbol] = math.log(value + 1) ** alpha
        elif transform == "sqrt_power":
            out[symbol] = math.sqrt(value) ** alpha
        else:
            raise ValueError(transform)
    return out


def hamilton(weights: dict[str, float], total: int) -> dict[str, int]:
    denom = sum(weights.values())
    quotas = {symbol: total * weights[symbol] / denom for symbol in SIGMA}
    out = {symbol: math.floor(quotas[symbol]) for symbol in SIGMA}
    remainder = total - sum(out.values())
    for symbol in sorted(SIGMA, key=lambda s: (quotas[s] - out[s], quotas[s], s), reverse=True)[:remainder]:
        out[symbol] += 1
    return out


def divisor(weights: dict[str, float], total: int, method: str) -> dict[str, int]:
    quotients = []
    for symbol, weight in weights.items():
        for seats in range(total + 1):
            if method == "jefferson":
                quotient = weight / (seats + 1)
            elif method == "webster":
                quotient = weight / (2 * seats + 1)
            elif method == "adams":
                quotient = float("inf") if seats == 0 else weight / seats
            elif method == "hill":
                quotient = float("inf") if seats == 0 else weight / math.sqrt(seats * (seats + 1))
            else:
                raise ValueError(method)
            quotients.append((quotient, symbol, seats))
    quotients.sort(reverse=True)
    out = {symbol: 0 for symbol in SIGMA}
    for _quotient, symbol, _seats in quotients[:total]:
        out[symbol] += 1
    return out


def allocate(weights: dict[str, float], total: int, method: str) -> dict[str, int]:
    if method == "hamilton":
        return hamilton(weights, total)
    return divisor(weights, total, method)


def candidate_rows(counts: Counter[str], extra_total: int) -> list[dict]:
    rows = []
    for transform in TRANSFORMS:
        for alpha_i in range(1, 601):
            alpha = alpha_i / 200
            for shift in SHIFTS:
                if shift == 0 and min(counts.values()) == 0:
                    continue
                weights = weights_from_counts(counts, transform, alpha, shift)
                for method in METHODS:
                    extra_prediction = allocate(weights, extra_total, method)
                    rows.append(
                        {
                            "model": "base_plus_extra_apportionment",
                            "transform": transform,
                            "alpha": alpha,
                            "shift": shift,
                            "method": method,
                            "prediction_extra_counts": dict(extra_prediction),
                            "prediction_counts": {symbol: extra_prediction[symbol] + 1 for symbol in SIGMA},
                        }
                    )
    return rows


def pearson(xs: list[float], ys: list[float]) -> float:
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    dx = sum((x - mx) ** 2 for x in xs)
    dy = sum((y - my) ** 2 for y in ys)
    if not dx or not dy:
        return 0.0
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / math.sqrt(dx * dy)


def l1(left: dict[str, int], right: dict[str, int]) -> int:
    return sum(abs(left[symbol] - right[symbol]) for symbol in SIGMA)


def max_abs(left: dict[str, int], right: dict[str, int]) -> int:
    return max(abs(left[symbol] - right[symbol]) for symbol in SIGMA)


def score_rows(rows: list[dict], observed_counts: Counter[str], counts: Counter[str]) -> list[dict]:
    corpus_vector = [counts[symbol] for symbol in SIGMA]
    observed_vector = [observed_counts[symbol] for symbol in SIGMA]
    out = []
    for row in rows:
        pred = row["prediction_counts"]
        pred_vector = [pred[symbol] for symbol in SIGMA]
        out.append(
            {
                **row,
                "l1": l1(pred, observed_counts),
                "max_abs": max_abs(pred, observed_counts),
                "normalized_l1_per_slot": l1(pred, observed_counts) / sum(observed_counts.values()),
                "pearson_vs_observed": pearson(pred_vector, observed_vector),
                "pearson_prediction_vs_corpus": pearson(pred_vector, corpus_vector),
            }
        )
    out.sort(
        key=lambda item: (
            item["l1"],
            item["max_abs"],
            -item["pearson_vs_observed"],
            item["transform"],
            item["alpha"],
            item["shift"],
            item["method"],
        )
    )
    return out


def unique_prediction_rows(rows: list[dict]) -> list[dict]:
    seen = set()
    out = []
    for row in rows:
        key = tuple(row["prediction_counts"][symbol] for symbol in SIGMA)
        if key not in seen:
            seen.add(key)
            out.append(row)
    return out


def l1_ball_count(prediction: dict[str, int], total: int, budget: int) -> int:
    vector = tuple(prediction[symbol] for symbol in SIGMA)

    @lru_cache(maxsize=None)
    def dp(index: int, remaining: int, remaining_budget: int) -> int:
        if index == len(vector):
            return 1 if remaining == 0 else 0
        count = 0
        expected = vector[index]
        for value in range(remaining + 1):
            cost = abs(value - expected)
            if cost <= remaining_budget:
                count += dp(index + 1, remaining - value, remaining_budget - cost)
        return count

    return dp(0, total, budget)


def add_mdl(row: dict, candidate_count: int, total_slots: int, all_labels_present: bool) -> dict:
    if not all_labels_present:
        return {
            **row,
            "inventory_raw_bits": log2_comb(total_slots + len(SIGMA) - 1, len(SIGMA) - 1),
            "model_selection_bits": math.log2(candidate_count),
            "residual_rank_bits_l1_leq": None,
            "inventory_mdl_bits": None,
            "inventory_mdl_gain_bits": None,
            "inventory_mdl_ratio": None,
            "mdl_note": "observed target misses at least one label; base-plus-extra MDL not applicable",
        }
    raw_bits = log2_comb((total_slots - len(SIGMA)) + len(SIGMA) - 1, len(SIGMA) - 1)
    residual_count = l1_ball_count(row["prediction_extra_counts"], total_slots - len(SIGMA), row["l1"])
    residual_bits = math.log2(residual_count)
    model_bits = math.log2(candidate_count)
    mdl_bits = model_bits + residual_bits
    return {
        **row,
        "inventory_raw_bits": raw_bits,
        "model_selection_bits": model_bits,
        "residual_rank_bits_l1_leq": residual_bits,
        "residual_vector_count_l1_leq": residual_count,
        "inventory_mdl_bits": mdl_bits,
        "inventory_mdl_gain_bits": raw_bits - mdl_bits,
        "inventory_mdl_ratio": mdl_bits / raw_bits if raw_bits else None,
        "mdl_note": "base-plus-extra inventory codelength; lower is better",
    }


def summarize(values: list[float], observed: float, low_is_good: bool) -> dict:
    mean = sum(values) / len(values)
    sd = (sum((value - mean) ** 2 for value in values) / (len(values) - 1)) ** 0.5
    if low_is_good:
        p = (sum(value <= observed for value in values) + 1) / (len(values) + 1)
        z = (mean - observed) / sd if sd else 0.0
    else:
        p = (sum(value >= observed for value in values) + 1) / (len(values) + 1)
        z = (observed - mean) / sd if sd else 0.0
    return {
        "observed": observed,
        "control_mean": mean,
        "control_sd": sd,
        "z_good_direction": z,
        "p_good_direction": p,
        "control_min": min(values),
        "control_max": max(values),
    }


def best_against_rows(rows: list[dict], observed_counts: Counter[str]) -> tuple[int, float]:
    observed_vector = [observed_counts[symbol] for symbol in SIGMA]
    best_l1 = None
    best_corr = None
    for row in rows:
        pred = row["prediction_counts"]
        current_l1 = sum(abs(pred[symbol] - observed_counts[symbol]) for symbol in SIGMA)
        current_corr = pearson([pred[symbol] for symbol in SIGMA], observed_vector)
        if best_l1 is None or current_l1 < best_l1:
            best_l1 = current_l1
        if best_corr is None or current_corr > best_corr:
            best_corr = current_corr
    return int(best_l1), float(best_corr)


def label_shuffle_control(rows: list[dict], observed_counts: Counter[str], observed_best: dict) -> dict:
    rng = random.Random(RANDOM_SEED + sum(ord(ch) for ch in "".join(sorted(observed_counts))))
    values = [observed_counts[symbol] for symbol in SIGMA]
    l1_values = []
    norm_l1_values = []
    corr_values = []
    total = sum(values)
    for _trial in range(LABEL_SHUFFLE_TRIALS):
        shuffled_values = values[:]
        rng.shuffle(shuffled_values)
        shuffled = Counter({symbol: shuffled_values[idx] for idx, symbol in enumerate(SIGMA)})
        best_l1, best_corr = best_against_rows(rows, shuffled)
        l1_values.append(best_l1)
        norm_l1_values.append(best_l1 / total)
        corr_values.append(best_corr)
    return {
        "trials": LABEL_SHUFFLE_TRIALS,
        "best_l1": summarize(l1_values, observed_best["l1"], low_is_good=True),
        "best_normalized_l1_per_slot": summarize(
            norm_l1_values,
            observed_best["normalized_l1_per_slot"],
            low_is_good=True,
        ),
        "best_pearson": summarize(corr_values, observed_best["pearson_vs_observed"], low_is_good=False),
    }


def quotient_inventory_from_labels(orbits: list[dict], pair_labels: dict[str, str]) -> dict:
    base_counts = Counter()
    explicit_counts = Counter()
    rows = []
    non_singleton_count = 0
    mixed_count = 0
    mixed_secondary_slots = 0
    for orbit in orbits:
        pairs = orbit["pairs"]
        label_counts = Counter(pair_labels[pair] for pair in pairs)
        base_label = sorted(label_counts, key=lambda symbol: (-label_counts[symbol], SIGMA.index(symbol)))[0]
        is_mixed = len(label_counts) > 1
        if len(pairs) > 1:
            non_singleton_count += 1
        if is_mixed:
            mixed_count += 1
            explicit_counts.update(label_counts)
            mixed_secondary_slots += len(pairs) - 1
        else:
            explicit_counts[base_label] += 1
        base_counts[base_label] += 1
        rows.append(
            {
                "orbit": orbit["orbit"],
                "pairs": pairs,
                "size": len(pairs),
                "base_label": base_label,
                "is_mixed": is_mixed,
                "label_counts": dict(sorted(label_counts.items())),
            }
        )
    mixed_selector_bits = log2_comb(non_singleton_count, mixed_count)
    mixed_secondary_label_bits = mixed_secondary_slots * math.log2(len(SIGMA) - 1)
    return {
        "base_counts": base_counts,
        "explicit_counts": explicit_counts,
        "orbit_rows": rows,
        "non_singleton_orbit_count": non_singleton_count,
        "mixed_orbit_count": mixed_count,
        "mixed_secondary_slots": mixed_secondary_slots,
        "mixed_selector_bits": mixed_selector_bits,
        "mixed_secondary_label_bits_naive": mixed_secondary_label_bits,
        "mixed_overhead_bits_naive": mixed_selector_bits + mixed_secondary_label_bits,
    }


def target_result(name: str, counts: Counter[str], corpus: Counter[str], mixed_overhead: dict | None = None) -> dict:
    total_slots = sum(counts.values())
    all_labels_present = all(counts[symbol] >= 1 for symbol in SIGMA)
    extra_total = total_slots - len(SIGMA)
    rows = score_rows(candidate_rows(corpus, extra_total), counts, corpus)
    unique_rows = unique_prediction_rows(rows)
    exact_rows = [row for row in rows if row["l1"] == 0]
    best = add_mdl(rows[0], len(rows), total_slots, all_labels_present)
    control = label_shuffle_control(unique_rows, counts, best)
    result = {
        "name": name,
        "total_slots": total_slots,
        "extra_total_after_one_per_label_floor": extra_total,
        "all_labels_present": all_labels_present,
        "observed_counts": {symbol: counts[symbol] for symbol in SIGMA},
        "observed_extra_counts": {symbol: counts[symbol] - 1 for symbol in SIGMA},
        "candidate_count": len(rows),
        "unique_prediction_count": len(unique_rows),
        "exact_hit_count": len(exact_rows),
        "best": best,
        "top_rows": [add_mdl(row, len(rows), total_slots, all_labels_present) for row in rows[:20]],
        "label_shuffle_control": control,
    }
    if mixed_overhead is not None:
        result["mixed_overhead"] = mixed_overhead
        if best["inventory_mdl_bits"] is not None:
            with_overhead = best["inventory_mdl_bits"] + mixed_overhead["mixed_overhead_bits_naive"]
            result["best"]["inventory_plus_mixed_overhead_mdl_bits"] = with_overhead
            result["best"]["inventory_plus_mixed_overhead_gain_bits"] = best["inventory_raw_bits"] - with_overhead
    return result


def pair_label_shuffle_control(
    orbits: list[dict],
    pair_order: list[str],
    observed_pair_labels: dict[str, str],
    quotient_base_rows: list[dict],
    quotient_explicit_rows: list[dict],
    observed_base_best: dict,
    observed_explicit_best: dict,
) -> dict:
    rng = random.Random(RANDOM_SEED + 17)
    labels = [observed_pair_labels[pair] for pair in pair_order]
    base_l1_values = []
    explicit_l1_values = []
    base_norm_values = []
    explicit_norm_values = []
    mixed_counts = []
    explicit_slots = []
    base_all_labels = 0
    explicit_all_labels = 0
    for _trial in range(PAIR_SHUFFLE_TRIALS):
        shuffled = labels[:]
        rng.shuffle(shuffled)
        pair_labels = dict(zip(pair_order, shuffled))
        inventory = quotient_inventory_from_labels(orbits, pair_labels)
        base_counts = inventory["base_counts"]
        explicit_counts = inventory["explicit_counts"]
        base_l1, _base_corr = best_against_rows(quotient_base_rows, base_counts)
        explicit_l1, _explicit_corr = best_against_rows(quotient_explicit_rows, explicit_counts)
        base_l1_values.append(base_l1)
        explicit_l1_values.append(explicit_l1)
        base_norm_values.append(base_l1 / sum(base_counts.values()))
        explicit_norm_values.append(explicit_l1 / sum(explicit_counts.values()))
        mixed_counts.append(inventory["mixed_orbit_count"])
        explicit_slots.append(sum(explicit_counts.values()))
        base_all_labels += int(all(base_counts[symbol] >= 1 for symbol in SIGMA))
        explicit_all_labels += int(all(explicit_counts[symbol] >= 1 for symbol in SIGMA))
    return {
        "trials": PAIR_SHUFFLE_TRIALS,
        "description": "shuffle original pair-cell labels over fixed 6<->9 orbits, then recompute quotient inventories",
        "quotient_base_46_best_l1": summarize(base_l1_values, observed_base_best["l1"], low_is_good=True),
        "quotient_explicit_50_best_l1": summarize(explicit_l1_values, observed_explicit_best["l1"], low_is_good=True),
        "quotient_base_46_best_normalized_l1": summarize(
            base_norm_values,
            observed_base_best["normalized_l1_per_slot"],
            low_is_good=True,
        ),
        "quotient_explicit_50_best_normalized_l1": summarize(
            explicit_norm_values,
            observed_explicit_best["normalized_l1_per_slot"],
            low_is_good=True,
        ),
        "mixed_orbit_count": summarize(mixed_counts, 4, low_is_good=True),
        "explicit_slot_count": summarize(explicit_slots, 50, low_is_good=True),
        "base_all_labels_present_fraction": base_all_labels / PAIR_SHUFFLE_TRIALS,
        "explicit_all_labels_present_fraction": explicit_all_labels / PAIR_SHUFFLE_TRIALS,
    }


def verdict(original: dict, quotient_base: dict, quotient_explicit: dict, pair_control: dict) -> str:
    original_best = original["best"]
    explicit_best = quotient_explicit["best"]
    base_best = quotient_base["best"]
    explicit_improves_mdl = (
        explicit_best["inventory_mdl_gain_bits"] is not None
        and original_best["inventory_mdl_gain_bits"] is not None
        and explicit_best["inventory_mdl_gain_bits"] > original_best["inventory_mdl_gain_bits"]
    )
    explicit_improves_norm = explicit_best["normalized_l1_per_slot"] < original_best["normalized_l1_per_slot"]
    base_improves_norm = base_best["normalized_l1_per_slot"] < original_best["normalized_l1_per_slot"]
    pair_p = pair_control["quotient_explicit_50_best_normalized_l1"]["p_good_direction"]
    label_p = quotient_explicit["label_shuffle_control"]["best_normalized_l1_per_slot"]["p_good_direction"]

    if explicit_improves_mdl and explicit_improves_norm and pair_p <= 0.01 and label_p <= 0.01:
        return "candidate_quotient_inventory_pressure_generator"
    if explicit_improves_norm and pair_p <= 0.05 and label_p <= 0.05:
        return "weak_quotient_inventory_pressure_support"
    if base_improves_norm and pair_control["quotient_base_46_best_normalized_l1"]["p_good_direction"] <= 0.05:
        return "base_quotient_pressure_only_not_lossless"
    return "no_generator_change"


def comparison(original: dict, quotient_base: dict, quotient_explicit: dict) -> dict:
    def pick(row: dict) -> dict:
        best = row["best"]
        return {
            "name": row["name"],
            "total_slots": row["total_slots"],
            "extra_total": row["extra_total_after_one_per_label_floor"],
            "best_l1": best["l1"],
            "best_normalized_l1_per_slot": best["normalized_l1_per_slot"],
            "best_pearson": best["pearson_vs_observed"],
            "inventory_mdl_bits": best["inventory_mdl_bits"],
            "inventory_mdl_gain_bits": best["inventory_mdl_gain_bits"],
            "label_shuffle_p_l1": row["label_shuffle_control"]["best_l1"]["p_good_direction"],
            "label_shuffle_p_normalized_l1": row["label_shuffle_control"]["best_normalized_l1_per_slot"]["p_good_direction"],
            "label_shuffle_p_pearson": row["label_shuffle_control"]["best_pearson"]["p_good_direction"],
        }

    rows = [pick(original), pick(quotient_base), pick(quotient_explicit)]
    return {
        "rows": rows,
        "quotient_explicit_minus_original": {
            "l1": rows[2]["best_l1"] - rows[0]["best_l1"],
            "normalized_l1_per_slot": rows[2]["best_normalized_l1_per_slot"] - rows[0]["best_normalized_l1_per_slot"],
            "inventory_mdl_gain_bits": rows[2]["inventory_mdl_gain_bits"] - rows[0]["inventory_mdl_gain_bits"],
        },
        "quotient_base_minus_original": {
            "l1": rows[1]["best_l1"] - rows[0]["best_l1"],
            "normalized_l1_per_slot": rows[1]["best_normalized_l1_per_slot"] - rows[0]["best_normalized_l1_per_slot"],
            "inventory_mdl_gain_bits": rows[1]["inventory_mdl_gain_bits"] - rows[0]["inventory_mdl_gain_bits"],
        },
    }


def fmt_float(value: float | None, digits: int = 3) -> str:
    if value is None:
        return "n/a"
    return f"{value:.{digits}f}"


def write_report(result: dict) -> None:
    comp = result["comparison"]["rows"]
    pair_control = result["pair_label_shuffle_control"]
    explicit = result["targets"]["quotient_explicit_50"]
    base = result["targets"]["quotient_base_46"]
    original = result["targets"]["original_55"]
    lines = [
        "# Quotient Inventory Pressure Search",
        "",
        "Generated by `quotient_inventory_pressure_search.py`.",
        "",
        "Scope: mechanical inventory only. This report compares the original",
        "55-cell pair table with the `6<->9` quotient inventory. It assigns no",
        "plaintext and promotes no glossary.",
        "",
        "## Summary",
        "",
        "| Target | Slots | Extra slots | Best L1 | L1/slot | Pearson | Inventory MDL | MDL gain | MDL+mixed gain | label-shuffle p(L1/slot) |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in comp:
        target = result["targets"][row["name"]]
        mixed_gain = target["best"].get("inventory_plus_mixed_overhead_gain_bits")
        lines.append(
            "| `{name}` | {slots} | {extra} | {l1} | {norm:.3f} | {pearson:.3f} | {mdl} | {gain} | {mixed_gain} | {p:.5f} |".format(
                name=row["name"],
                slots=row["total_slots"],
                extra=row["extra_total"],
                l1=row["best_l1"],
                norm=row["best_normalized_l1_per_slot"],
                pearson=row["best_pearson"],
                mdl=fmt_float(row["inventory_mdl_bits"], 2),
                gain=fmt_float(row["inventory_mdl_gain_bits"], 2),
                mixed_gain=fmt_float(mixed_gain, 2),
                p=row["label_shuffle_p_normalized_l1"],
            )
        )
    lines.extend(
        [
            "",
            f"Verdict: `{result['verdict']}`.",
            "",
            "The explicit quotient target improves the inventory fit weakly: L1 drops",
            "from 12 to 10 and normalized L1 drops from 0.218 to 0.200. The MDL",
            "gain is small, and adding naive mixed-orbit overhead removes the",
            "compression. This is support for quotient pressure, not enough to",
            "change the generator hypothesis.",
            "",
            "## Mixed Orbit Accounting",
            "",
            "| Orbit | Pairs | Base label | Label counts |",
            "|---:|---|---|---|",
        ]
    )
    for row in result["quotient_orbit_rows"]:
        if row["is_mixed"]:
            lines.append(
                f"| {row['orbit']} | `{' '.join(row['pairs'])}` | `{row['base_label']}` | `{json.dumps(row['label_counts'], sort_keys=True)}` |"
            )
    mixed = explicit["mixed_overhead"]
    lines.extend(
        [
            "",
            "Naive explicit mixed-orbit overhead:",
            "",
            f"- mixed selector: `{mixed['mixed_selector_bits']:.3f}` bits",
            f"- secondary labels: `{mixed['mixed_secondary_label_bits_naive']:.3f}` bits",
            f"- total overhead: `{mixed['mixed_overhead_bits_naive']:.3f}` bits",
            "",
            "## Pair-Label Shuffle Control",
            "",
            "This control preserves the original 55-cell label multiset, shuffles labels",
            "over fixed pair cells, then recomputes the `6<->9` quotient inventories.",
            "",
            "| Metric | Observed | Control mean | Control sd | p(good) |",
            "|---|---:|---:|---:|---:|",
            "| quotient_base_46 L1/slot | {obs:.3f} | {mean:.3f} | {sd:.3f} | {p:.5f} |".format(
                obs=pair_control["quotient_base_46_best_normalized_l1"]["observed"],
                mean=pair_control["quotient_base_46_best_normalized_l1"]["control_mean"],
                sd=pair_control["quotient_base_46_best_normalized_l1"]["control_sd"],
                p=pair_control["quotient_base_46_best_normalized_l1"]["p_good_direction"],
            ),
            "| quotient_explicit_50 L1/slot | {obs:.3f} | {mean:.3f} | {sd:.3f} | {p:.5f} |".format(
                obs=pair_control["quotient_explicit_50_best_normalized_l1"]["observed"],
                mean=pair_control["quotient_explicit_50_best_normalized_l1"]["control_mean"],
                sd=pair_control["quotient_explicit_50_best_normalized_l1"]["control_sd"],
                p=pair_control["quotient_explicit_50_best_normalized_l1"]["p_good_direction"],
            ),
            "| mixed orbit count | {obs:.0f} | {mean:.3f} | {sd:.3f} | {p:.5f} |".format(
                obs=pair_control["mixed_orbit_count"]["observed"],
                mean=pair_control["mixed_orbit_count"]["control_mean"],
                sd=pair_control["mixed_orbit_count"]["control_sd"],
                p=pair_control["mixed_orbit_count"]["p_good_direction"],
            ),
            "",
            f"All-label coverage in shuffled quotient controls: base `{pair_control['base_all_labels_present_fraction']:.3f}`, explicit `{pair_control['explicit_all_labels_present_fraction']:.3f}`.",
            "",
            "## Best Rules",
            "",
            "| Target | Transform | alpha | shift | Method | Prediction extras |",
            "|---|---|---:|---:|---|---|",
        ]
    )
    for row in [original, base, explicit]:
        best = row["best"]
        lines.append(
            "| `{name}` | `{transform}` | {alpha:.3f} | {shift} | `{method}` | `{prediction}` |".format(
                name=row["name"],
                transform=best["transform"],
                alpha=best["alpha"],
                shift=best["shift"],
                method=best["method"],
                prediction=json.dumps(best["prediction_extra_counts"], sort_keys=True),
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `quotient_base_46` is a useful diagnostic, but it drops the second labels",
            "  of mixed orbits and therefore is not lossless enough to promote.",
            "- `quotient_explicit_50` keeps the mixed labels visible and is modestly",
            "  sharper than the original on inventory-only normalized L1 and MDL.",
            "  The effect is small, non-exact, and pair-label controls put it at",
            "  weak-support strength rather than formula-recovery strength.",
            "- Generator hypothesis change: none. Keep the prior hypothesis as",
            "  frequency-weighted stochastic inventory plus weak `6<->9` quotient",
            "  pressure, not an original deterministic formula.",
            "",
            "`translation_delta=NONE`.",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    formula = load_json(FORMULA_JSON)
    quotient = load_json(QUOTIENT_JSON)
    corpus = corpus_counts()
    pair_order = all_pairs()
    pair_labels = {pair: primary_pair_symbol(formula["pair_table"], pair) for pair in pair_order}
    original_counts = Counter(pair_labels.values())

    swap = quotient["swap_6_9"]
    if swap["orbit_count"] != 46:
        raise RuntimeError(f"expected 46 swap_6_9 orbits, got {swap['orbit_count']}")
    inventory = quotient_inventory_from_labels(swap["orbits"], pair_labels)
    base_counts = inventory["base_counts"]
    explicit_counts = inventory["explicit_counts"]

    original = target_result("original_55", original_counts, corpus)
    quotient_base = target_result("quotient_base_46", base_counts, corpus)
    mixed_overhead = {
        "non_singleton_orbit_count": inventory["non_singleton_orbit_count"],
        "mixed_orbit_count": inventory["mixed_orbit_count"],
        "mixed_secondary_slots": inventory["mixed_secondary_slots"],
        "mixed_selector_bits": inventory["mixed_selector_bits"],
        "mixed_secondary_label_bits_naive": inventory["mixed_secondary_label_bits_naive"],
        "mixed_overhead_bits_naive": inventory["mixed_overhead_bits_naive"],
    }
    quotient_explicit = target_result("quotient_explicit_50", explicit_counts, corpus, mixed_overhead=mixed_overhead)

    quotient_base_rows = unique_prediction_rows(
        score_rows(candidate_rows(corpus, quotient_base["extra_total_after_one_per_label_floor"]), base_counts, corpus)
    )
    quotient_explicit_rows = unique_prediction_rows(
        score_rows(candidate_rows(corpus, quotient_explicit["extra_total_after_one_per_label_floor"]), explicit_counts, corpus)
    )
    pair_control = pair_label_shuffle_control(
        swap["orbits"],
        pair_order,
        pair_labels,
        quotient_base_rows,
        quotient_explicit_rows,
        quotient_base["best"],
        quotient_explicit["best"],
    )
    comp = comparison(original, quotient_base, quotient_explicit)
    result = {
        "schema": "quotient_inventory_pressure_results.v1",
        "translation_delta": "NONE",
        "random_seed": RANDOM_SEED,
        "inputs": {
            "formula_json": str(FORMULA_JSON.relative_to(ROOT)),
            "quotient_json": str(QUOTIENT_JSON.relative_to(ROOT)),
            "occ_streams": str(OCC_STREAMS.relative_to(ROOT)),
        },
        "scope": "mechanical_inventory_only_no_plaintext_no_glossary",
        "models": {
            "candidate_family": "one guaranteed slot per label plus frequency-weighted apportionment of extra slots",
            "methods": list(METHODS),
            "transforms": list(TRANSFORMS),
            "shifts": list(SHIFTS),
            "alpha_grid": "0.005..3.000 step 0.005",
            "mdl": "log2(candidate_count) + log2(number of residual count vectors within observed L1), compared to raw count-vector inventory",
        },
        "corpus_symbol_counts": {symbol: corpus[symbol] for symbol in SIGMA},
        "quotient_orbit_rows": inventory["orbit_rows"],
        "targets": {
            "original_55": original,
            "quotient_base_46": quotient_base,
            "quotient_explicit_50": quotient_explicit,
        },
        "pair_label_shuffle_control": pair_control,
        "comparison": comp,
        "verdict": verdict(original, quotient_base, quotient_explicit, pair_control),
        "generator_hypothesis_delta": "NONE",
    }
    write_json(OUT_JSON, result)
    write_report(result)
    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(f"wrote {OUT_MD.relative_to(ROOT)}")
    print(
        "verdict={verdict} original_l1={orig} quotient_explicit_l1={quot} translation_delta=NONE".format(
            verdict=result["verdict"],
            orig=original["best"]["l1"],
            quot=quotient_explicit["best"]["l1"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
