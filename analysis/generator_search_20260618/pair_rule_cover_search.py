#!/usr/bin/env python3
"""Human-predicate rule-cover search for the 55 unordered pair cells.

This pass tests a different possible authoring mechanism from the path/fill
ledgers: maybe the exact table was made from a short list of predicates over
digit-pair properties (digit incidence, diagonals, sums, differences, modulo
classes, or lore digit sets). It keeps the result mechanical only.
"""

from __future__ import annotations

import json
import math
import random
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FORMULA_JSON = ROOT / "analysis" / "mechanism_model_20260618" / "mechanical_formula_469.json"

OUT_JSON = HERE / "pair_rule_cover_results.json"
OUT_MD = HERE / "pair_rule_cover_report.md"

SIGMA = "*ABCEFILNORSTV"
RANDOM_SEED = 46920260619
CONTROL_TRIALS = 120
MAX_RULES = 18

LORE_DIGIT_SETS = {
    "469": {4, 6, 9},
    "3478": {3, 4, 7, 8},
    "43153": {1, 3, 4, 5},
    "34784": {3, 4, 7, 8},
    "74032": {0, 2, 3, 4, 7},
    "45331": {1, 3, 4, 5},
    "honeminas_left": {1, 3, 4, 5},
    "honeminas_right": {3, 4, 7, 8},
    "one_tibia": {1},
    "conflict_digits": {1, 9},
    "missing39_digits": {3, 9},
    "tape_edge_33_66": {3, 6},
}


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def natural_pairs() -> list[str]:
    return [f"{i}{j}" for i in range(10) for j in range(i, 10)]


def pair_mask(pairs: list[str], predicate) -> int:
    mask = 0
    for idx, pair in enumerate(pairs):
        a, b = int(pair[0]), int(pair[1])
        if predicate(a, b, idx, pair):
            mask |= 1 << idx
    return mask


def add_predicate(predicates: dict[str, dict], pairs: list[str], name: str, family: str, cost: float, predicate) -> None:
    mask = pair_mask(pairs, predicate)
    if mask == 0 or mask == (1 << len(pairs)) - 1:
        return
    old = predicates.get(name)
    if old is None or cost < old["cost"]:
        predicates[name] = {"name": name, "family": family, "cost": cost, "mask": mask}


def build_predicates(pairs: list[str]) -> list[dict]:
    predicates: dict[str, dict] = {}
    all_digits = set(range(10))

    add_predicate(predicates, pairs, "diagonal", "geometry", 1.0, lambda a, b, _idx, _p: a == b)
    add_predicate(predicates, pairs, "off_diagonal", "geometry", 1.0, lambda a, b, _idx, _p: a != b)
    add_predicate(predicates, pairs, "even_even", "parity", 1.5, lambda a, b, _idx, _p: a % 2 == 0 and b % 2 == 0)
    add_predicate(predicates, pairs, "odd_odd", "parity", 1.5, lambda a, b, _idx, _p: a % 2 == 1 and b % 2 == 1)
    add_predicate(predicates, pairs, "mixed_parity", "parity", 1.5, lambda a, b, _idx, _p: a % 2 != b % 2)
    for digit in range(10):
        add_predicate(predicates, pairs, f"has_{digit}", "digit_incidence", 1.5, lambda a, b, _idx, _p, d=digit: a == d or b == d)
        add_predicate(predicates, pairs, f"not_has_{digit}", "digit_incidence", 1.8, lambda a, b, _idx, _p, d=digit: a != d and b != d)
        add_predicate(predicates, pairs, f"loop_{digit}", "digit_incidence", 2.0, lambda a, b, _idx, _p, d=digit: a == d and b == d)
        add_predicate(predicates, pairs, f"min_{digit}", "position", 2.0, lambda a, _b, _idx, _p, d=digit: a == d)
        add_predicate(predicates, pairs, f"max_{digit}", "position", 2.0, lambda _a, b, _idx, _p, d=digit: b == d)
    for value in range(19):
        add_predicate(predicates, pairs, f"sum_{value}", "arithmetic", 2.0, lambda a, b, _idx, _p, v=value: a + b == v)
    for value in range(10):
        add_predicate(predicates, pairs, f"diff_{value}", "arithmetic", 2.0, lambda a, b, _idx, _p, v=value: b - a == v)
        add_predicate(predicates, pairs, f"product_last_{value}", "arithmetic", 2.5, lambda a, b, _idx, _p, v=value: (a * b) % 10 == v)
    for modulus in range(2, 11):
        for residue in range(modulus):
            add_predicate(predicates, pairs, f"sum_mod_{modulus}_{residue}", "modular", 2.5, lambda a, b, _idx, _p, m=modulus, r=residue: (a + b) % m == r)
            add_predicate(predicates, pairs, f"diff_mod_{modulus}_{residue}", "modular", 2.5, lambda a, b, _idx, _p, m=modulus, r=residue: (b - a) % m == r)
            add_predicate(predicates, pairs, f"tri_index_mod_{modulus}_{residue}", "triangular_index", 3.0, lambda _a, _b, idx, _p, m=modulus, r=residue: idx % m == r)

    curated_sets = dict(LORE_DIGIT_SETS)
    curated_sets.update(
        {
            "low_0_4": set(range(5)),
            "high_5_9": set(range(5, 10)),
            "corners": {0, 9},
            "center_4_5": {4, 5},
            "center_3_6": {3, 4, 5, 6},
            "primes": {2, 3, 5, 7},
            "squares": {0, 1, 4, 9},
            "evens": {0, 2, 4, 6, 8},
            "odds": {1, 3, 5, 7, 9},
        }
    )
    for size in range(1, 5):
        for subset in combinations(range(10), size):
            curated_sets["set_" + "".join(str(d) for d in subset)] = set(subset)
    for name, digits in curated_sets.items():
        key = "".join(str(d) for d in sorted(digits))
        set_cost = 2.5 + 0.6 * len(digits)
        add_predicate(predicates, pairs, f"both_in_{name}_{key}", "digit_set", set_cost, lambda a, b, _idx, _p, s=digits: a in s and b in s)
        add_predicate(predicates, pairs, f"intersects_{name}_{key}", "digit_set", set_cost, lambda a, b, _idx, _p, s=digits: a in s or b in s)
        add_predicate(predicates, pairs, f"exactly_one_in_{name}_{key}", "digit_set", set_cost + 0.5, lambda a, b, _idx, _p, s=digits: (a in s) ^ (b in s))
        complement = all_digits - digits
        if complement and len(complement) <= 5:
            add_predicate(predicates, pairs, f"both_out_{name}_{key}", "digit_set", set_cost + 0.5, lambda a, b, _idx, _p, s=digits: a not in s and b not in s)
    # Pairwise conjunctions among cheap primitives catch rules like
    # "has 9 and low digit" without enumerating every table cell.
    base = sorted([p for p in predicates.values() if p["cost"] <= 2.5], key=lambda item: item["name"])
    for left_idx, left in enumerate(base):
        for right in base[left_idx + 1 :]:
            mask = left["mask"] & right["mask"]
            if mask == 0 or mask == left["mask"] or mask == right["mask"]:
                continue
            name = f"and({left['name']},{right['name']})"
            predicates[name] = {
                "name": name,
                "family": "compound",
                "cost": left["cost"] + right["cost"] + 0.8,
                "mask": mask,
            }
    return sorted(predicates.values(), key=lambda item: (item["cost"], item["name"]))


def primary_pair_symbol(pair_table: dict, pair: str) -> str:
    row = pair_table[pair]
    if row["status"] == "pure":
        return row["symbol_if_pure"]
    return sorted(row["symbols"])[0]


def acceptable_pair_symbols(pair_table: dict, pair: str) -> set[str]:
    return set(pair_table[pair]["symbols"])


def label_masks(labels: list[str]) -> dict[str, int]:
    masks = {symbol: 0 for symbol in SIGMA}
    for idx, symbol in enumerate(labels):
        masks[symbol] |= 1 << idx
    return masks


def default_correct(remaining: int, masks: dict[str, int]) -> tuple[str, int]:
    best_symbol = max(SIGMA, key=lambda symbol: ((remaining & masks[symbol]).bit_count(), -SIGMA.index(symbol)))
    return best_symbol, (remaining & masks[best_symbol]).bit_count()


def evaluate_rules(rules: list[dict], default_symbol: str, labels: list[str], pair_table: dict, pairs: list[str]) -> dict:
    predictions = []
    for idx, pair in enumerate(pairs):
        predicted = default_symbol
        for rule in rules:
            if rule["mask"] & (1 << idx):
                predicted = rule["symbol"]
                break
        predictions.append(predicted)
    primary_hits = sum(1 for pred, actual in zip(predictions, labels) if pred == actual)
    acceptable_hits = sum(1 for pred, pair in zip(predictions, pairs) if pred in acceptable_pair_symbols(pair_table, pair))
    exceptions = [pair for pred, pair in zip(predictions, pairs) if pred not in acceptable_pair_symbols(pair_table, pair)]
    return {
        "primary_hits": primary_hits,
        "acceptable_hits": acceptable_hits,
        "primary_accuracy": primary_hits / len(labels),
        "acceptable_accuracy": acceptable_hits / len(labels),
        "exceptions": exceptions,
        "predicted": "".join(predictions),
    }


def greedy_decision_list(labels: list[str], pair_table: dict, pairs: list[str], predicates: list[dict], max_rules: int) -> dict:
    masks = label_masks(labels)
    all_mask = (1 << len(labels)) - 1
    remaining = all_mask
    rules: list[dict] = []
    current_default, current_default_hits = default_correct(remaining, masks)
    current_score = current_default_hits
    current_cost = 0.0
    assigned_hits = 0
    trace = []

    for _step in range(max_rules):
        best = None
        for predicate in predicates:
            cover = predicate["mask"] & remaining
            cover_size = cover.bit_count()
            if cover_size == 0:
                continue
            new_remaining = remaining & ~cover
            new_default, new_default_hits = default_correct(new_remaining, masks)
            for symbol in SIGMA:
                rule_hits = (cover & masks[symbol]).bit_count()
                total_hits = assigned_hits + rule_hits + new_default_hits
                gain = total_hits - current_score
                if gain < 0:
                    continue
                false_hits = cover_size - rule_hits
                rule_cost = predicate["cost"] + math.log2(len(SIGMA))
                rank = (gain, -false_hits, -rule_cost, rule_hits, cover_size)
                if best is None or rank > best["rank"]:
                    best = {
                        "rank": rank,
                        "predicate": predicate,
                        "symbol": symbol,
                        "cover": cover,
                        "cover_size": cover_size,
                        "hits": rule_hits,
                        "false_hits": false_hits,
                        "default": new_default,
                        "total_hits": total_hits,
                        "rule_cost": rule_cost,
                    }
        if best is None or best["rank"][0] <= 0:
            break
        predicate = best["predicate"]
        rules.append(
            {
                "predicate": predicate["name"],
                "family": predicate["family"],
                "symbol": best["symbol"],
                "mask": best["cover"],
                "cover_size": best["cover_size"],
                "hits": best["hits"],
                "false_hits": best["false_hits"],
                "cost": best["rule_cost"],
            }
        )
        remaining &= ~best["cover"]
        assigned_hits += best["hits"]
        current_default = best["default"]
        current_score = best["total_hits"]
        current_cost += best["rule_cost"]
        trace.append(
            {
                "rule_count": len(rules),
                "primary_hits_with_default": current_score,
                "default_symbol": current_default,
                "last_rule": {
                    "predicate": predicate["name"],
                    "family": predicate["family"],
                    "symbol": best["symbol"],
                    "cover_size": best["cover_size"],
                    "hits": best["hits"],
                    "false_hits": best["false_hits"],
                },
            }
        )

    evaluated = evaluate_rules(rules, current_default, labels, pair_table, pairs)
    lookup_bits = len(labels) * math.log2(len(SIGMA))
    exception_unit_bits = math.log2(len(labels)) + math.log2(len(SIGMA))
    acceptable_exception_bits = (len(labels) - evaluated["acceptable_hits"]) * exception_unit_bits
    primary_exception_bits = (len(labels) - evaluated["primary_hits"]) * exception_unit_bits
    acceptable_mdl_bits = current_cost + math.log2(len(SIGMA)) + acceptable_exception_bits
    primary_mdl_bits = current_cost + math.log2(len(SIGMA)) + primary_exception_bits
    return {
        "rule_count": len(rules),
        "rules": [
            {key: value for key, value in rule.items() if key != "mask"}
            for rule in rules
        ],
        "default_symbol": current_default,
        "primary_hits": evaluated["primary_hits"],
        "acceptable_hits": evaluated["acceptable_hits"],
        "primary_accuracy": evaluated["primary_accuracy"],
        "acceptable_accuracy": evaluated["acceptable_accuracy"],
        "exceptions": evaluated["exceptions"],
        "predicted": evaluated["predicted"],
        "rule_cost_bits": current_cost + math.log2(len(SIGMA)),
        "mdl_cost_bits": acceptable_mdl_bits,
        "lookup_cost_bits": lookup_bits,
        "mdl_gain_vs_lookup_bits": lookup_bits - acceptable_mdl_bits,
        "lookup_cost_ratio": acceptable_mdl_bits / lookup_bits,
        "primary_mdl_cost_bits": primary_mdl_bits,
        "primary_mdl_gain_vs_lookup_bits": lookup_bits - primary_mdl_bits,
        "primary_lookup_cost_ratio": primary_mdl_bits / lookup_bits,
        "trace": trace,
    }


def symbol_cover(labels: list[str], predicates: list[dict], max_terms: int = 5) -> list[dict]:
    masks = label_masks(labels)
    rows = []
    for symbol in SIGMA:
        target = masks[symbol]
        if target == 0:
            continue
        cover = 0
        terms = []
        for _ in range(max_terms):
            best = None
            for predicate in predicates:
                new_cover = cover | predicate["mask"]
                tp = (new_cover & target).bit_count()
                fp = (new_cover & ~target).bit_count()
                fn = (target & ~new_cover).bit_count()
                score = 2 * tp - fp - fn - 0.15 * predicate["cost"]
                rank = (score, tp, -fp, -predicate["cost"])
                if best is None or rank > best["rank"]:
                    best = {"rank": rank, "predicate": predicate, "new_cover": new_cover, "tp": tp, "fp": fp, "fn": fn}
            if best is None or best["new_cover"] == cover:
                break
            cover = best["new_cover"]
            terms.append(best["predicate"]["name"])
        tp = (cover & target).bit_count()
        fp = (cover & ~target).bit_count()
        fn = (target & ~cover).bit_count()
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        rows.append({"symbol": symbol, "target_count": target.bit_count(), "terms": terms, "tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall, "f1": f1})
    rows.sort(key=lambda row: (-row["f1"], row["symbol"]))
    return rows


def control(labels: list[str], pair_table: dict, pairs: list[str], predicates: list[dict], observed: dict) -> dict:
    rng = random.Random(RANDOM_SEED)
    scores = []
    symbols = labels[:]
    for _trial in range(CONTROL_TRIALS):
        rng.shuffle(symbols)
        trial = greedy_decision_list(symbols[:], pair_table, pairs, predicates, MAX_RULES)
        scores.append(
            {
                "primary_hits": trial["primary_hits"],
                "primary_mdl_gain_vs_lookup_bits": trial["primary_mdl_gain_vs_lookup_bits"],
                "rule_count": trial["rule_count"],
            }
        )
    primary_hits = [row["primary_hits"] for row in scores]
    mdl_gains = [row["primary_mdl_gain_vs_lookup_bits"] for row in scores]

    def p_ge(values: list[float], observed_value: float) -> float:
        return (sum(value >= observed_value for value in values) + 1) / (len(values) + 1)

    return {
        "trials": CONTROL_TRIALS,
        "primary_hits_mean": sum(primary_hits) / len(primary_hits),
        "primary_hits_max": max(primary_hits),
        "primary_hits_p_ge": p_ge(primary_hits, observed["primary_hits"]),
        "primary_mdl_gain_mean": sum(mdl_gains) / len(mdl_gains),
        "primary_mdl_gain_max": max(mdl_gains),
        "primary_mdl_gain_p_ge": p_ge(mdl_gains, observed["primary_mdl_gain_vs_lookup_bits"]),
    }


def verdict(best: dict, ctrl: dict) -> str:
    if best["primary_lookup_cost_ratio"] >= 1.0:
        return "lookup_disguise"
    if best["primary_hits"] >= 45 and ctrl["primary_hits_p_ge"] <= 0.01 and best["primary_mdl_gain_vs_lookup_bits"] > 0:
        return "candidate_pair_rule_formula"
    if ctrl["primary_hits_p_ge"] <= 0.05 or ctrl["primary_mdl_gain_p_ge"] <= 0.05:
        return "weak_pair_rule_signal"
    return "not_promoted"


def main() -> int:
    formula = load_json(FORMULA_JSON)
    pair_table = formula["pair_table"]
    pairs = natural_pairs()
    labels = [primary_pair_symbol(pair_table, pair) for pair in pairs]
    predicates = build_predicates(pairs)
    by_rules = []
    for max_rules in (4, 8, 12, 18):
        row = greedy_decision_list(labels, pair_table, pairs, predicates, max_rules)
        row["max_rules"] = max_rules
        by_rules.append(row)
    best = sorted(by_rules, key=lambda row: (-row["acceptable_hits"], row["lookup_cost_ratio"], row["max_rules"]))[0]
    ctrl = control(labels, pair_table, pairs, predicates, best)
    symbol_rows = symbol_cover(labels, predicates)
    result_verdict = verdict(best, ctrl)
    result = {
        "schema": "pair_rule_cover_results.v1",
        "translation_delta": "NONE",
        "predicate_count": len(predicates),
        "control_trials": CONTROL_TRIALS,
        "best": best,
        "by_rule_budget": by_rules,
        "symbol_cover_rows": symbol_rows,
        "control": ctrl,
        "verdict": result_verdict,
    }
    write_json(OUT_JSON, result)

    lines = [
        "# Pair Rule-Cover Search",
        "",
        "Generated by `pair_rule_cover_search.py`.",
        "",
        "This pass asks whether the exact 55 pair-cell labels can be generated",
        "from a short human-readable decision list over digit-pair predicates.",
        "It uses no plaintext and assigns no meanings.",
        "",
        "## Summary",
        "",
        "| Predicate count | Best hits | Rule count | MDL/lookup | Control p(hit) | Control p(MDL) | Verdict |",
        "|---:|---:|---:|---:|---:|---:|---|",
        f"| {len(predicates)} | {best['primary_hits']}/55 | {best['rule_count']} | {best['primary_lookup_cost_ratio']:.3f} | {ctrl['primary_hits_p_ge']:.4f} | {ctrl['primary_mdl_gain_p_ge']:.4f} | `{result_verdict}` |",
        "",
        "## Best Decision List",
        "",
        f"Default symbol: `{best['default_symbol']}`.",
        "",
        "| # | Predicate | Family | Symbol | Cover | Hits | False hits |",
        "|---:|---|---|---|---:|---:|---:|",
    ]
    for idx, rule in enumerate(best["rules"], start=1):
        lines.append(
            f"| {idx} | `{rule['predicate']}` | `{rule['family']}` | `{rule['symbol']}` | {rule['cover_size']} | {rule['hits']} | {rule['false_hits']} |"
        )
    lines.extend(
        [
            "",
            "## Independent Symbol Covers",
            "",
            "| Symbol | Target | F1 | TP | FP | FN | Terms |",
            "|---|---:|---:|---:|---:|---:|---|",
        ]
    )
    for row in symbol_rows:
        lines.append(
            f"| `{row['symbol']}` | {row['target_count']} | {row['f1']:.3f} | {row['tp']} | {row['fp']} | {row['fn']} | {', '.join('`'+term+'`' for term in row['terms'][:5])} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "A compact predicate rule would be interesting only if it beats",
            "inventory-preserving label shuffles and has lower rough MDL than a lookup.",
            f"Current verdict: `{result_verdict}`.",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT_JSON.relative_to(HERE)}")
    print(f"wrote {OUT_MD.relative_to(HERE)}")
    print(
        "predicates={} best={}/55 rules={} p_hit={:.4f} verdict={}".format(
            len(predicates),
            best["primary_hits"],
            best["rule_count"],
            ctrl["primary_hits_p_ge"],
            result_verdict,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
