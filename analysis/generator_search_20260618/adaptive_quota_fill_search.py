#!/usr/bin/env python3
"""Adaptive quota-fill search for the 469 pair table.

This pass tests a plausible authoring mechanism that was not covered by fixed
pair-order sequence tests: keep the observed homophone inventory as quotas, then
fill pair cells online using simple local rules over already-filled neighbours.

The search is deliberately permissive and records weak rows instead of pruning
early. It is mechanical only and assigns no plaintext.
"""

from __future__ import annotations

import json
import math
import random
from collections import Counter
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FORMULA_JSON = ROOT / "analysis" / "mechanism_model_20260618" / "mechanical_formula_469.json"

OUT_JSON = HERE / "adaptive_quota_fill_results.json"
OUT_MD = HERE / "adaptive_quota_fill_report.md"

SIGMA = list("*ABCEFILNORSTV")
RANDOM_SEED = 46920260619
CONTROL_TRIALS = 500
LORE_SEEDS = ["469", "3478", "43153", "34784", "74032", "45331"]


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def natural_pairs() -> list[tuple[int, int]]:
    return [(a, b) for a in range(10) for b in range(a, 10)]


def primary_pair_symbol(pair_table: dict, pair: tuple[int, int]) -> str:
    row = pair_table[f"{pair[0]}{pair[1]}"]
    if row["status"] == "pure":
        return row["symbol_if_pure"]
    return sorted(row["symbols"])[0]


def pair_features(pair: tuple[int, int]) -> dict[str, int | bool]:
    a, b = pair
    return {
        "a": a,
        "b": b,
        "sum": a + b,
        "diff": b - a,
        "product": a * b,
        "diag": a == b,
        "border": a in (0, 9) or b in (0, 9),
        "center_dist": abs(a - 4.5) + abs(b - 4.5),
    }


def seeded_value(pair: tuple[int, int], seed: str) -> int:
    value = int(seed)
    a, b = pair
    for item in (a, b, a + b, b - a, a * 10 + b):
        value = (value * 1103515245 + item + 12345) & 0x7FFFFFFF
    return value


def pair_orders(pairs: list[tuple[int, int]]) -> dict[str, list[tuple[int, int]]]:
    orders = {
        "row_major": sorted(pairs),
        "col_major": sorted(pairs, key=lambda p: (p[1], p[0])),
        "sum_then_row": sorted(pairs, key=lambda p: (p[0] + p[1], p[0], p[1])),
        "sum_desc_then_row": sorted(pairs, key=lambda p: (-(p[0] + p[1]), p[0], p[1])),
        "diff_then_row": sorted(pairs, key=lambda p: (p[1] - p[0], p[0], p[1])),
        "diag_first": sorted(pairs, key=lambda p: (p[1] != p[0], p[0] + p[1], p[0])),
        "near_diagonal_first": sorted(pairs, key=lambda p: (p[1] - p[0], p[0] + p[1], p[0])),
        "border_first": sorted(pairs, key=lambda p: (not (p[0] in (0, 9) or p[1] in (0, 9)), p[0] + p[1], p[0])),
        "center_first": sorted(pairs, key=lambda p: (abs(p[0] - 4.5) + abs(p[1] - 4.5), p[0], p[1])),
        "center_last": sorted(pairs, key=lambda p: (-(abs(p[0] - 4.5) + abs(p[1] - 4.5)), p[0], p[1])),
    }
    for seed in LORE_SEEDS:
        orders[f"seed_{seed}"] = sorted(pairs, key=lambda p, s=seed: seeded_value(p, s))
    return orders


def symbol_orders(labels: list[str], pairs: list[tuple[int, int]]) -> dict[str, list[str]]:
    counts = Counter(labels)
    first_index = {}
    for idx, label in enumerate(labels):
        first_index.setdefault(label, idx)
    diag_counts = Counter(label for pair, label in zip(pairs, labels) if pair[0] == pair[1])
    return {
        "alphabet": SIGMA[:],
        "alphabet_reverse": list(reversed(SIGMA)),
        "frequency_desc": sorted(SIGMA, key=lambda s: (-counts[s], s)),
        "frequency_asc": sorted(SIGMA, key=lambda s: (counts[s], s)),
        "first_use": sorted(SIGMA, key=lambda s: (first_index.get(s, 10**9), s)),
        "diag_pressure": sorted(SIGMA, key=lambda s: (-diag_counts[s], -counts[s], s)),
    }


def neighbours(pair: tuple[int, int], filled: dict[tuple[int, int], str]) -> list[str]:
    a, b = pair
    candidates = [
        (a - 1, b) if a > 0 and a - 1 <= b else None,
        (a, b - 1) if b > a else None,
        (a - 1, b - 1) if a > 0 else None,
        (a + 1, b) if a + 1 <= b else None,
        (a, b + 1) if b < 9 else None,
    ]
    return [filled[p] for p in candidates if p in filled]


def score_symbol(
    rule: str,
    symbol: str,
    pair: tuple[int, int],
    remaining: Counter[str],
    filled: dict[tuple[int, int], str],
    row_counts: dict[tuple[int, str], int],
    col_counts: dict[tuple[int, str], int],
) -> tuple[float, ...]:
    a, b = pair
    neigh = neighbours(pair, filled)
    same_neigh = sum(1 for item in neigh if item == symbol)
    row_col_load = row_counts.get((a, symbol), 0) + col_counts.get((b, symbol), 0)
    rem = remaining[symbol]
    if rule == "first_available":
        return (0.0,)
    if rule == "avoid_same_neighbours":
        return (-same_neigh, -row_col_load, rem)
    if rule == "prefer_same_neighbours":
        return (same_neigh, -row_col_load, rem)
    if rule == "row_col_balance":
        return (-row_col_load, -same_neigh, rem)
    if rule == "quota_pressure":
        return (rem, -row_col_load, -same_neigh)
    if rule == "diagonal_e_anchor":
        diag_bonus = 1 if a == b and symbol == "E" else 0
        return (diag_bonus, -same_neigh, -row_col_load, rem)
    if rule == "border_star_anchor":
        border_bonus = 1 if (a in (0, 9) or b in (0, 9)) and symbol == "*" else 0
        return (border_bonus, -same_neigh, -row_col_load, rem)
    if rule == "vowel_consonant_alternate":
        vowels = set("AEIO")
        neigh_vowels = sum(1 for item in neigh if item in vowels)
        want_vowel = len(neigh) > 0 and neigh_vowels <= len(neigh) / 2
        return (1 if (symbol in vowels) == want_vowel else 0, -row_col_load, rem)
    raise ValueError(rule)


def fill_table(
    pair_order: list[tuple[int, int]],
    symbol_order: list[str],
    quotas: Counter[str],
    rule: str,
) -> dict[tuple[int, int], str]:
    remaining = quotas.copy()
    filled: dict[tuple[int, int], str] = {}
    row_counts: dict[tuple[int, str], int] = {}
    col_counts: dict[tuple[int, str], int] = {}
    order_rank = {symbol: idx for idx, symbol in enumerate(symbol_order)}
    for pair in pair_order:
        candidates = [symbol for symbol in symbol_order if remaining[symbol] > 0]
        if not candidates:
            raise RuntimeError("quota exhausted")
        best = max(
            candidates,
            key=lambda symbol: (
                score_symbol(rule, symbol, pair, remaining, filled, row_counts, col_counts),
                -order_rank[symbol],
            ),
        )
        filled[pair] = best
        remaining[best] -= 1
        a, b = pair
        row_counts[(a, best)] = row_counts.get((a, best), 0) + 1
        col_counts[(b, best)] = col_counts.get((b, best), 0) + 1
    return filled


def evaluate(pred: dict[tuple[int, int], str], target: dict[tuple[int, int], str]) -> dict:
    correct_pairs = [f"{a}{b}" for (a, b), label in target.items() if pred[(a, b)] == label]
    return {
        "correct": len(correct_pairs),
        "accuracy": len(correct_pairs) / len(target),
        "correct_pairs": correct_pairs,
    }


def mdl_bits(correct: int, variant_count: int, label_count: int = 55) -> dict:
    lookup_bits = label_count * math.log2(len(SIGMA))
    exceptions = label_count - correct
    rule_bits = math.log2(max(variant_count, 1)) + 8.0
    exception_bits = exceptions * (math.log2(label_count) + math.log2(len(SIGMA)))
    total = rule_bits + exception_bits
    return {
        "lookup_cost_bits": lookup_bits,
        "mdl_cost_bits": total,
        "mdl_gain_vs_lookup_bits": lookup_bits - total,
        "lookup_cost_ratio": total / lookup_bits,
        "exceptions": exceptions,
    }


def verdict(row: dict, control: dict) -> str:
    if row["mdl"]["lookup_cost_ratio"] >= 1.0:
        return "lookup_disguise"
    if control["p_ge_observed"] <= 0.01 and row["correct"] >= 40:
        return "candidate_adaptive_quota_fill"
    if control["p_ge_observed"] <= 0.05:
        return "weak_adaptive_quota_signal"
    return "rejected_control"


def control_for_prediction(pred_labels: list[str], labels: list[str], observed_correct: int) -> dict:
    rng = random.Random(RANDOM_SEED + 99)
    hits = []
    for _ in range(CONTROL_TRIALS):
        shuffled = labels[:]
        rng.shuffle(shuffled)
        hits.append(sum(1 for a, b in zip(pred_labels, shuffled) if a == b))
    mean = sum(hits) / len(hits)
    sd = (sum((value - mean) ** 2 for value in hits) / (len(hits) - 1)) ** 0.5
    return {
        "trials": CONTROL_TRIALS,
        "mean": mean,
        "sd": sd,
        "min": min(hits),
        "max": max(hits),
        "p_ge_observed": (sum(value >= observed_correct for value in hits) + 1) / (len(hits) + 1),
    }


def main() -> int:
    formula = load_json(FORMULA_JSON)
    pairs = natural_pairs()
    labels = [primary_pair_symbol(formula["pair_table"], pair) for pair in pairs]
    target = dict(zip(pairs, labels))
    quotas = Counter(labels)
    p_orders = pair_orders(pairs)
    s_orders = symbol_orders(labels, pairs)
    rules = [
        "first_available",
        "avoid_same_neighbours",
        "prefer_same_neighbours",
        "row_col_balance",
        "quota_pressure",
        "diagonal_e_anchor",
        "border_star_anchor",
        "vowel_consonant_alternate",
    ]
    variant_count = len(p_orders) * len(s_orders) * len(rules)
    rows = []
    for pair_order_name, pair_order in p_orders.items():
        for symbol_order_name, symbol_order in s_orders.items():
            for rule in rules:
                pred = fill_table(pair_order, symbol_order, quotas, rule)
                metrics = evaluate(pred, target)
                pred_labels = [pred[pair] for pair in pairs]
                row = {
                    "pair_order": pair_order_name,
                    "symbol_order": symbol_order_name,
                    "rule": rule,
                    **metrics,
                    "mdl": mdl_bits(metrics["correct"], variant_count),
                    "prediction": {f"{a}{b}": pred[(a, b)] for a, b in pairs},
                }
                rows.append(row)
    rows.sort(
        key=lambda row: (
            -row["correct"],
            row["mdl"]["lookup_cost_ratio"],
            row["pair_order"],
            row["symbol_order"],
            row["rule"],
        )
    )
    best = rows[0]
    best_pred_labels = [best["prediction"][f"{a}{b}"] for a, b in pairs]
    ctrl = control_for_prediction(best_pred_labels, labels, best["correct"])
    result_verdict = verdict(best, ctrl)
    result = {
        "schema": "adaptive_quota_fill_results.v1",
        "translation_delta": "NONE",
        "pair_orders": len(p_orders),
        "symbol_orders": len(s_orders),
        "rules": rules,
        "variant_count": variant_count,
        "target_inventory": dict(sorted(quotas.items())),
        "best": best,
        "top_rows": rows[:100],
        "control": ctrl,
        "verdict": result_verdict,
    }
    write_json(OUT_JSON, result)

    lines = [
        "# Adaptive Quota-Fill Search",
        "",
        "Generated by `adaptive_quota_fill_search.py`.",
        "",
        "This pass gives the generator the observed homophone inventory as",
        "symbol quotas, then asks whether simple online/local fill rules can",
        "place those symbols into the 55 unordered pair cells. It is a",
        "mechanical-origin test only.",
        "",
        "## Summary",
        "",
        "| Best hits | Pair order | Symbol order | Rule | MDL/lookup | Control p(hit) | Verdict |",
        "|---:|---|---|---|---:|---:|---|",
        f"| {best['correct']}/55 | `{best['pair_order']}` | `{best['symbol_order']}` | `{best['rule']}` | {best['mdl']['lookup_cost_ratio']:.3f} | {ctrl['p_ge_observed']:.4f} | `{result_verdict}` |",
        "",
        f"Search variants: `{variant_count}`.",
        "",
        "## Top Rows",
        "",
        "| Hits | Pair order | Symbol order | Rule | MDL/lookup |",
        "|---:|---|---|---|---:|",
    ]
    for row in rows[:25]:
        lines.append(
            f"| {row['correct']}/55 | `{row['pair_order']}` | `{row['symbol_order']}` | `{row['rule']}` | {row['mdl']['lookup_cost_ratio']:.3f} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "A useful adaptive-fill formula would need to beat inventory-preserving",
            "shuffle controls and reduce rough MDL relative to explicit pair lookup.",
            "This front records all rows but promotes none unless both conditions are",
            "met.",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT_JSON.relative_to(HERE)}")
    print(f"wrote {OUT_MD.relative_to(HERE)}")
    print(
        "best={}/55 order={} symbol_order={} rule={} p={:.4f} verdict={}".format(
            best["correct"],
            best["pair_order"],
            best["symbol_order"],
            best["rule"],
            ctrl["p_ge_observed"],
            result_verdict,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
