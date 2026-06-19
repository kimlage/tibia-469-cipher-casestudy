#!/usr/bin/env python3
"""6<->9 split-label pair search for the 469 pair table.

The quotient pass found a weak mechanical clue: swapping digit identities 6 and
9 collapses the 55 unordered pair cells to 46 orbits with four mixed two-cell
orbits.  This follow-up asks a narrower question:

    do the nine label-pairs inside those 6<->9 orbits have their own compact
    generator, or are they just another small lookup/exception ledger?

Mechanical only.  No plaintext, glossary, or semantic translation is promoted.
"""

from __future__ import annotations

import json
import math
import random
from collections import Counter
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FORMULA_JSON = ROOT / "analysis" / "mechanism_model_20260618" / "mechanical_formula_469.json"

OUT_JSON = HERE / "digit_orbit_split_label_pair_results.json"
OUT_MD = HERE / "digit_orbit_split_label_pair_report.md"

SIGMA = "*ABCEFILNORSTV"
SYMBOL_BITS = math.log2(len(SIGMA))
DIRECTED_LOOKUP_BITS = 18 * SYMBOL_BITS
PAIR_ALPHABET_BITS = math.log2((len(SIGMA) * (len(SIGMA) + 1)) // 2)
PAIR_LOOKUP_BITS = 9 * PAIR_ALPHABET_BITS
RANDOM_SEED = 46920260619
CONTROL_TRIALS = 500


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


def symbol_key(symbol: str) -> int:
    return SIGMA.index(symbol)


def pair_key(pair: tuple[int, int]) -> str:
    return f"{pair[0]}{pair[1]}"


def primary_pair_symbol(pair_table: dict[str, dict[str, Any]], pair: tuple[int, int]) -> str:
    cell = pair_table[pair_key(pair)]
    if cell["status"] == "pure":
        return cell["symbol_if_pure"]
    return min(cell["symbols"], key=symbol_key)


def orbit_pair_for_x(x: int, side_digit: int) -> tuple[int, int]:
    if x == 6 and side_digit == 9:
        return (9, 9)
    a, b = x, side_digit
    return (a, b) if a <= b else (b, a)


def build_orbit_rows(formula: dict[str, Any]) -> list[dict[str, Any]]:
    pair_table = formula["pair_table"]
    rows: list[dict[str, Any]] = []
    for x in range(9):
        pair6 = orbit_pair_for_x(x, 6)
        pair9 = orbit_pair_for_x(x, 9)
        label6 = primary_pair_symbol(pair_table, pair6)
        label9 = primary_pair_symbol(pair_table, pair9)
        ordered = sorted([label6, label9], key=symbol_key)
        rows.append(
            {
                "x": x,
                "pair6": pair_key(pair6),
                "pair9": pair_key(pair9),
                "label6": label6,
                "label9": label9,
                "pair_label_directed": label6 + label9,
                "pair_label_unordered": "".join(ordered),
                "base_label": ordered[0],
                "secondary_label": ordered[1] if ordered[0] != ordered[1] else None,
                "mixed": label6 != label9,
                "lower_label_on_side6": label6 == ordered[0],
            }
        )
    return rows


def all_pair_primary_labels(formula: dict[str, Any]) -> list[str]:
    labels = []
    for a in range(10):
        for b in range(a, 10):
            labels.append(primary_pair_symbol(formula["pair_table"], (a, b)))
    return labels


def unique_in_order(values: list[str]) -> str:
    out = []
    for value in values:
        if value not in out:
            out.append(value)
    for value in SIGMA:
        if value not in out:
            out.append(value)
    return "".join(out)


def symbol_orders(formula: dict[str, Any], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pair_labels = all_pair_primary_labels(formula)
    freq = Counter(pair_labels)
    freq_order = "".join(sorted(SIGMA, key=lambda symbol: (-freq[symbol], SIGMA.index(symbol))))
    table_first = unique_in_order(pair_labels)
    orbit_first = unique_in_order([row["label6"] for row in rows] + [row["label9"] for row in rows])
    orders = [
        {"id": "sigma", "symbols": SIGMA, "bits": 1.0},
        {"id": "sigma_reverse", "symbols": SIGMA[::-1], "bits": 1.2},
        {"id": "pair_frequency_desc", "symbols": freq_order, "bits": 3.0},
        {"id": "pair_frequency_asc", "symbols": freq_order[::-1], "bits": 3.2},
        {"id": "pair_table_first", "symbols": table_first, "bits": 3.5},
        {"id": "pair_table_first_reverse", "symbols": table_first[::-1], "bits": 3.7},
        {"id": "orbit_first", "symbols": orbit_first, "bits": 4.0},
        {"id": "orbit_first_reverse", "symbols": orbit_first[::-1], "bits": 4.2},
    ]
    dedup: dict[str, dict[str, Any]] = {}
    for order in orders:
        dedup.setdefault(order["symbols"], order)
    return list(dedup.values())


def side_formula_candidates(orders: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for order in orders:
        symbols = order["symbols"]
        n = len(symbols)
        for a in range(n):
            for b in range(n):
                pred = [symbols[(a * x + b) % n] for x in range(9)]
                candidates.append(
                    {
                        "id": f"{order['id']}|affine|a={a}|b={b}",
                        "family": "side_affine_symbol_order",
                        "order": order["id"],
                        "a": a,
                        "b": b,
                        "prediction": pred,
                        "model_bits": order["bits"] + 2 * math.log2(n),
                    }
                )
    return candidates


def best_side_models(labels: list[str], candidates: list[dict[str, Any]]) -> dict[str, Any]:
    by_hits = []
    by_mdl = []
    for cand in candidates:
        errors = [
            {"x": x, "predicted": cand["prediction"][x], "actual": labels[x]}
            for x in range(9)
            if cand["prediction"][x] != labels[x]
        ]
        hits = 9 - len(errors)
        bits = cand["model_bits"] + len(errors) * (math.log2(9) + SYMBOL_BITS)
        row = {
            "id": cand["id"],
            "family": cand["family"],
            "order": cand["order"],
            "hits": hits,
            "exceptions": len(errors),
            "model_bits": cand["model_bits"],
            "lossless_bits": bits,
            "errors": errors,
        }
        by_hits.append(row)
        by_mdl.append(row)
    by_hits.sort(key=lambda row: (-row["hits"], row["lossless_bits"], row["id"]))
    by_mdl.sort(key=lambda row: (row["lossless_bits"], -row["hits"], row["id"]))
    return {"best_by_hits": by_hits[0], "best_by_lossless_mdl": by_mdl[0]}


def affine_side_summary(labels6: list[str], labels9: list[str], side_candidates: list[dict[str, Any]]) -> dict[str, Any]:
    side6 = best_side_models(labels6, side_candidates)
    side9 = best_side_models(labels9, side_candidates)
    hit_bits = (
        side6["best_by_hits"]["model_bits"]
        + side9["best_by_hits"]["model_bits"]
        + (18 - side6["best_by_hits"]["hits"] - side9["best_by_hits"]["hits"]) * (math.log2(18) + SYMBOL_BITS)
    )
    mdl_bits = side6["best_by_lossless_mdl"]["lossless_bits"] + side9["best_by_lossless_mdl"]["lossless_bits"]
    return {
        "id": "independent_side_affine_symbol_order",
        "family": "directed_label_formula",
        "directed_hits": side6["best_by_hits"]["hits"] + side9["best_by_hits"]["hits"],
        "lossless_bits_for_best_hits": hit_bits,
        "best_lossless_bits": mdl_bits,
        "best_side6_by_hits": side6["best_by_hits"],
        "best_side9_by_hits": side9["best_by_hits"],
        "best_side6_by_mdl": side6["best_by_lossless_mdl"],
        "best_side9_by_mdl": side9["best_by_lossless_mdl"],
        "directed_lookup_ratio": mdl_bits / DIRECTED_LOOKUP_BITS,
    }


def best_period_template(directed_pairs: list[tuple[str, str]]) -> dict[str, Any]:
    candidates = []
    for period in range(1, 6):
        template: list[tuple[str, str]] = []
        for residue in range(period):
            bucket = [directed_pairs[x] for x in range(9) if x % period == residue]
            pair = Counter(bucket).most_common(1)[0][0]
            template.append(pair)
        predicted = [template[x % period] for x in range(9)]
        errors = [
            {"x": x, "predicted": "".join(predicted[x]), "actual": "".join(directed_pairs[x])}
            for x in range(9)
            if predicted[x] != directed_pairs[x]
        ]
        pair_hits = 9 - len(errors)
        directed_hits = sum(
            int(predicted[x][0] == directed_pairs[x][0]) + int(predicted[x][1] == directed_pairs[x][1])
            for x in range(9)
        )
        model_bits = math.log2(5) + period * (2 * SYMBOL_BITS)
        lossless_bits = model_bits + len(errors) * (math.log2(9) + 2 * SYMBOL_BITS)
        candidates.append(
            {
                "id": f"directed_pair_period_{period}",
                "family": "periodic_directed_pair_template",
                "period": period,
                "template": ["".join(pair) for pair in template],
                "pair_hits": pair_hits,
                "directed_hits": directed_hits,
                "exceptions": len(errors),
                "model_bits": model_bits,
                "lossless_bits": lossless_bits,
                "errors": errors,
                "pair_lookup_ratio": lossless_bits / PAIR_LOOKUP_BITS,
            }
        )
    candidates.sort(key=lambda row: (-row["directed_hits"], row["lossless_bits"], row["id"]))
    by_hits = candidates[0]
    by_mdl = min(candidates, key=lambda row: (row["lossless_bits"], -row["directed_hits"], row["id"]))
    return {"best_by_hits": by_hits, "best_by_lossless_mdl": by_mdl, "top_rows": candidates}


def selector_rules() -> list[dict[str, Any]]:
    rules: list[dict[str, Any]] = [
        {"id": "none", "xs": set(), "cost": 0.5},
        {"id": "all", "xs": set(range(9)), "cost": 0.5},
        {"id": "edge_0_8", "xs": {0, 8}, "cost": 1.8},
        {"id": "lore_exception_19_39", "xs": {1, 3}, "cost": 1.8},
        {"id": "lore_469_projected", "xs": {4, 6}, "cost": 2.0},
        {"id": "fibonacci_digits", "xs": {0, 1, 2, 3, 5, 8}, "cost": 2.4},
        {"id": "triangular_digits", "xs": {0, 1, 3, 6}, "cost": 2.3},
        {"id": "square_digits", "xs": {0, 1, 4}, "cost": 2.2},
    ]
    for k in range(9):
        rules.append({"id": f"x_le_{k}", "xs": set(range(k + 1)), "cost": 1.7})
        rules.append({"id": f"x_ge_{k}", "xs": set(range(k, 9)), "cost": 1.7})
    for modulus in range(2, 7):
        for residue in range(modulus):
            rules.append(
                {
                    "id": f"x_mod_{modulus}_eq_{residue}",
                    "xs": {x for x in range(9) if x % modulus == residue},
                    "cost": 2.0 + math.log2(modulus) / 4,
                }
            )
    atomic = rules[:]
    for left in atomic:
        for right in atomic:
            if left["id"] >= right["id"]:
                continue
            rules.append(
                {
                    "id": f"or({left['id']},{right['id']})",
                    "xs": set(left["xs"]) | set(right["xs"]),
                    "cost": left["cost"] + right["cost"] + 1.0,
                }
            )
    dedup: dict[tuple[int, ...], dict[str, Any]] = {}
    for rule in rules:
        key = tuple(sorted(rule["xs"]))
        current = dedup.get(key)
        if current is None or rule["cost"] < current["cost"]:
            dedup[key] = rule
    return list(dedup.values())


def side_rules(mixed_xs: list[int]) -> list[dict[str, Any]]:
    return [
        {"id": "all_lower_on_6", "side6_xs": set(mixed_xs), "cost": 0.7},
        {"id": "all_lower_on_9", "side6_xs": set(), "cost": 0.7},
        {"id": "parity_even_6_odd_9", "side6_xs": {x for x in mixed_xs if x % 2 == 0}, "cost": 1.5},
        {"id": "edge_0_8_on_6_else_9", "side6_xs": {x for x in mixed_xs if x in {0, 8}}, "cost": 1.8},
        {"id": "lore_exception_19_39_on_9_else_6", "side6_xs": {x for x in mixed_xs if x not in {1, 3}}, "cost": 2.0},
        {"id": "x_mod_4_eq_0_on_6_else_9", "side6_xs": {x for x in mixed_xs if x % 4 == 0}, "cost": 2.1},
    ]


def best_selector(target_xs: set[int], rules: list[dict[str, Any]]) -> dict[str, Any]:
    exact = [rule for rule in rules if rule["xs"] == target_xs]
    combinatorial = {"id": "explicit_subset_index", "xs": target_xs, "cost": log2_comb(9, len(target_xs))}
    if not exact:
        return combinatorial
    return min([combinatorial] + exact, key=lambda rule: (rule["cost"], rule["id"]))


def secondary_label_bits(labels: list[str]) -> dict[str, Any]:
    if not labels:
        return {"model": "none", "bits": 0.0, "default": None, "exceptions": []}
    candidates = []
    for default in SIGMA:
        errors = [
            {"index": index, "actual": label}
            for index, label in enumerate(labels)
            if label != default
        ]
        bits = SYMBOL_BITS + len(errors) * (math.log2(len(labels)) + SYMBOL_BITS)
        candidates.append({"model": "default_plus_exceptions", "bits": bits, "default": default, "exceptions": errors})
    return min(candidates, key=lambda row: (row["bits"], row["default"]))


def best_side_rule(target_side6_xs: set[int], mixed_xs: list[int]) -> dict[str, Any]:
    exact = [rule for rule in side_rules(mixed_xs) if rule["side6_xs"] == target_side6_xs]
    explicit = {"id": "explicit_side_bits", "side6_xs": target_side6_xs, "cost": len(mixed_xs)}
    if not exact:
        return explicit
    return min([explicit] + exact, key=lambda rule: (rule["cost"], rule["id"]))


def structural_split_model(directed_pairs: list[tuple[str, str]], rules: list[dict[str, Any]]) -> dict[str, Any]:
    base_labels = []
    mixed_xs = []
    secondary_labels = []
    side6_low_xs = set()
    for x, pair in enumerate(directed_pairs):
        ordered = sorted(pair, key=symbol_key)
        base_labels.append(ordered[0])
        if ordered[0] != ordered[1]:
            mixed_xs.append(x)
            secondary_labels.append(ordered[1])
            if pair[0] == ordered[0]:
                side6_low_xs.add(x)
    selector = best_selector(set(mixed_xs), rules)
    secondary = secondary_label_bits(secondary_labels)
    side = best_side_rule(side6_low_xs, mixed_xs)
    base_bits = 9 * SYMBOL_BITS
    total_bits = base_bits + selector["cost"] + secondary["bits"] + side["cost"]
    return {
        "id": "base_sequence_plus_selector_secondary_side",
        "family": "split_metadata_structural_model",
        "directed_hits": 18,
        "pair_hits": 9,
        "mixed_xs": mixed_xs,
        "base_sequence": "".join(base_labels),
        "secondary_sequence": "".join(secondary_labels),
        "base_sequence_bits": base_bits,
        "selector_rule": selector["id"],
        "selector_bits": selector["cost"],
        "secondary_model": secondary,
        "side_rule": side["id"],
        "side_bits": side["cost"],
        "lossless_bits": total_bits,
        "directed_lookup_ratio": total_bits / DIRECTED_LOOKUP_BITS,
        "pair_lookup_ratio": total_bits / PAIR_LOOKUP_BITS,
    }


def evaluate(labels6: list[str], labels9: list[str], side_candidates: list[dict[str, Any]], rules: list[dict[str, Any]]) -> dict[str, Any]:
    pairs = list(zip(labels6, labels9))
    affine = affine_side_summary(labels6, labels9, side_candidates)
    period = best_period_template(pairs)
    structural = structural_split_model(pairs, rules)
    best_formula_hits = max(affine["directed_hits"], period["best_by_hits"]["directed_hits"])
    best_formula_bits = min(affine["best_lossless_bits"], period["best_by_lossless_mdl"]["lossless_bits"])
    return {
        "affine": affine,
        "periodic_pair_template": period,
        "structural_split_model": structural,
        "summary": {
            "best_formula_directed_hits": best_formula_hits,
            "best_formula_lossless_bits": best_formula_bits,
            "structural_lossless_bits": structural["lossless_bits"],
        },
    }


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


def controls(observed: dict[str, Any], labels6: list[str], labels9: list[str], side_candidates: list[dict[str, Any]], rules: list[dict[str, Any]]) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED)
    observed_pairs = list(zip(labels6, labels9))
    pair_shuffle_hits = []
    pair_shuffle_formula_bits = []
    pair_shuffle_structural_bits = []
    directed_shuffle_hits = []
    directed_shuffle_formula_bits = []
    directed_shuffle_structural_bits = []
    for _ in range(CONTROL_TRIALS):
        pair_rows = observed_pairs[:]
        rng.shuffle(pair_rows)
        row6 = [pair[0] for pair in pair_rows]
        row9 = [pair[1] for pair in pair_rows]
        pair_result = evaluate(row6, row9, side_candidates, rules)
        pair_shuffle_hits.append(pair_result["summary"]["best_formula_directed_hits"])
        pair_shuffle_formula_bits.append(pair_result["summary"]["best_formula_lossless_bits"])
        pair_shuffle_structural_bits.append(pair_result["summary"]["structural_lossless_bits"])

        directed = labels6 + labels9
        rng.shuffle(directed)
        row6 = directed[:9]
        row9 = directed[9:]
        directed_result = evaluate(row6, row9, side_candidates, rules)
        directed_shuffle_hits.append(directed_result["summary"]["best_formula_directed_hits"])
        directed_shuffle_formula_bits.append(directed_result["summary"]["best_formula_lossless_bits"])
        directed_shuffle_structural_bits.append(directed_result["summary"]["structural_lossless_bits"])

    summary = observed["summary"]
    return {
        "trials": CONTROL_TRIALS,
        "pair_row_shuffle_preserving_directed_pairs": {
            "best_formula_directed_hits": summarize(pair_shuffle_hits, summary["best_formula_directed_hits"], True),
            "best_formula_lossless_bits": summarize(pair_shuffle_formula_bits, summary["best_formula_lossless_bits"], False),
            "structural_lossless_bits": summarize(pair_shuffle_structural_bits, summary["structural_lossless_bits"], False),
        },
        "directed_label_shuffle_preserving_inventory": {
            "best_formula_directed_hits": summarize(directed_shuffle_hits, summary["best_formula_directed_hits"], True),
            "best_formula_lossless_bits": summarize(directed_shuffle_formula_bits, summary["best_formula_lossless_bits"], False),
            "structural_lossless_bits": summarize(directed_shuffle_structural_bits, summary["structural_lossless_bits"], False),
        },
    }


def verdict(result: dict[str, Any]) -> str:
    obs = result["observed"]
    ctrl = result["controls"]
    formula_hits = obs["summary"]["best_formula_directed_hits"]
    formula_p = ctrl["directed_label_shuffle_preserving_inventory"]["best_formula_directed_hits"]["p_good_direction"]
    structural_p = ctrl["pair_row_shuffle_preserving_directed_pairs"]["structural_lossless_bits"]["p_good_direction"]
    structural_bits = obs["summary"]["structural_lossless_bits"]
    if formula_hits >= 14 and formula_p <= 0.05 and obs["summary"]["best_formula_lossless_bits"] < DIRECTED_LOOKUP_BITS:
        return "candidate_split_label_formula"
    if structural_bits < PAIR_LOOKUP_BITS and structural_p <= 0.05:
        return "weak_split_metadata_compression"
    if structural_bits < PAIR_LOOKUP_BITS:
        return "split_metadata_bookkeeping_control_not_decisive"
    return "lookup_disguise_or_rejected_control"


def write_report(result: dict[str, Any]) -> None:
    rows = result["orbit_rows"]
    obs = result["observed"]
    ctrl = result["controls"]
    structural = obs["structural_split_model"]
    affine = obs["affine"]
    period = obs["periodic_pair_template"]
    lines = [
        "# Digit-Orbit Split Label Pair Search",
        "",
        "Generated by `digit_orbit_split_label_pair_search.py`.",
        "",
        "Scope: the nine non-singleton orbits created by the weak `6 <-> 9` quotient.",
        "This tests whether their directed label-pairs are generated by compact",
        "cycles/formulas, not just whether each orbit is mixed. It is mechanical",
        "only and assigns no plaintext.",
        "",
        "## Target Rows",
        "",
        "| x | pair6 | label6 | pair9 | label9 | unordered labels | mixed | lower label on side6 |",
        "|---:|---|---|---|---|---|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['x']} | `{row['pair6']}` | `{row['label6']}` | `{row['pair9']}` | `{row['label9']}` | `{row['pair_label_unordered']}` | {str(row['mixed']).lower()} | {str(row['lower_label_on_side6']).lower()} |"
        )
    lines.extend(
        [
            "",
            "## Best Mechanical Attempts",
            "",
            "| Family | Directed hits | Lossless bits | Lookup ratio | Notes |",
            "|---|---:|---:|---:|---|",
            f"| independent side affine symbol-order formulas | {affine['directed_hits']}/18 | {affine['best_lossless_bits']:.2f} | {affine['directed_lookup_ratio']:.3f} | best side6 `{affine['best_side6_by_hits']['id']}`, best side9 `{affine['best_side9_by_hits']['id']}` |",
            f"| periodic directed-pair template | {period['best_by_hits']['directed_hits']}/18 | {period['best_by_lossless_mdl']['lossless_bits']:.2f} | {period['best_by_lossless_mdl']['pair_lookup_ratio']:.3f} | best period `{period['best_by_hits']['period']}` by hits |",
            f"| base sequence + selector + secondary + side rule | {structural['directed_hits']}/18 | {structural['lossless_bits']:.2f} | {structural['pair_lookup_ratio']:.3f} | selector `{structural['selector_rule']}`, side `{structural['side_rule']}` |",
            "",
            "The exact structural row is not a formula for the matrix because it still",
            "stores the nine base labels. It is included to measure whether the split",
            "metadata itself is compact after the `6 <-> 9` quotient.",
            "",
            "## Exact Structural Model",
            "",
            f"- Base sequence: `{structural['base_sequence']}` (`{structural['base_sequence_bits']:.2f}` bits).",
            f"- Mixed x-set: `{structural['mixed_xs']}` via `{structural['selector_rule']}` (`{structural['selector_bits']:.2f}` bits).",
            f"- Secondary sequence: `{structural['secondary_sequence']}` via default `{structural['secondary_model']['default']}` plus `{len(structural['secondary_model']['exceptions'])}` exception(s) (`{structural['secondary_model']['bits']:.2f}` bits).",
            f"- Side rule: `{structural['side_rule']}` (`{structural['side_bits']:.2f}` bits).",
            f"- Pair-label lookup baseline: `{PAIR_LOOKUP_BITS:.2f}` bits; directed-label baseline: `{DIRECTED_LOOKUP_BITS:.2f}` bits.",
            "",
            "## Controls",
            "",
            "| Control | Metric | Observed | Mean | Max/Min | p(good) |",
            "|---|---|---:|---:|---:|---:|",
        ]
    )
    pair_ctrl = ctrl["pair_row_shuffle_preserving_directed_pairs"]
    directed_ctrl = ctrl["directed_label_shuffle_preserving_inventory"]
    lines.append(
        f"| pair-row shuffle | best formula directed hits | {pair_ctrl['best_formula_directed_hits']['observed']:.3f} | {pair_ctrl['best_formula_directed_hits']['mean']:.3f} | {pair_ctrl['best_formula_directed_hits']['max']:.3f} | {pair_ctrl['best_formula_directed_hits']['p_good_direction']:.4f} |"
    )
    lines.append(
        f"| pair-row shuffle | structural lossless bits | {pair_ctrl['structural_lossless_bits']['observed']:.2f} | {pair_ctrl['structural_lossless_bits']['mean']:.2f} | {pair_ctrl['structural_lossless_bits']['min']:.2f} | {pair_ctrl['structural_lossless_bits']['p_good_direction']:.4f} |"
    )
    lines.append(
        f"| directed-label shuffle | best formula directed hits | {directed_ctrl['best_formula_directed_hits']['observed']:.3f} | {directed_ctrl['best_formula_directed_hits']['mean']:.3f} | {directed_ctrl['best_formula_directed_hits']['max']:.3f} | {directed_ctrl['best_formula_directed_hits']['p_good_direction']:.4f} |"
    )
    lines.append(
        f"| directed-label shuffle | structural lossless bits | {directed_ctrl['structural_lossless_bits']['observed']:.2f} | {directed_ctrl['structural_lossless_bits']['mean']:.2f} | {directed_ctrl['structural_lossless_bits']['min']:.2f} | {directed_ctrl['structural_lossless_bits']['p_good_direction']:.4f} |"
    )
    lines.extend(
        [
            "",
            "## Verdict",
            "",
            f"`{result['verdict']}`.",
            "",
            "Conservative reading: the split layer can be described compactly as",
            "stored base labels plus a small mixed-orbit side/secondary ledger, but",
            "the direct formula families do not generate the label-pairs. This",
            "tightens the `6 <-> 9` clue as bookkeeping, not as the original formula.",
            "",
            "Translation delta: `NONE`.",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    formula = load_json(FORMULA_JSON)
    rows = build_orbit_rows(formula)
    labels6 = [row["label6"] for row in rows]
    labels9 = [row["label9"] for row in rows]
    orders = symbol_orders(formula, rows)
    side_candidates = side_formula_candidates(orders)
    rules = selector_rules()
    observed = evaluate(labels6, labels9, side_candidates, rules)
    ctrl = controls(observed, labels6, labels9, side_candidates, rules)
    result = {
        "schema": "digit_orbit_split_label_pair_results.v1",
        "translation_delta": "NONE",
        "target": "6_9_quotient_split_label_pairs",
        "directed_lookup_bits": DIRECTED_LOOKUP_BITS,
        "pair_lookup_bits": PAIR_LOOKUP_BITS,
        "orbit_rows": rows,
        "symbol_orders": [{"id": order["id"], "symbols": order["symbols"], "bits": order["bits"]} for order in orders],
        "observed": observed,
        "controls": ctrl,
    }
    result["verdict"] = verdict(result)
    write_json(OUT_JSON, result)
    write_report(result)
    print(f"wrote {OUT_JSON.relative_to(HERE)}")
    print(f"wrote {OUT_MD.relative_to(HERE)}")
    print(
        "verdict={verdict} formula_hits={hits}/18 structural_bits={bits:.2f} pair_ratio={ratio:.3f}".format(
            verdict=result["verdict"],
            hits=observed["summary"]["best_formula_directed_hits"],
            bits=observed["summary"]["structural_lossless_bits"],
            ratio=observed["structural_split_model"]["pair_lookup_ratio"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
