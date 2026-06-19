#!/usr/bin/env python3
"""Anchored remaining-fill search.

This pass composes the strongest matrix-side clues in a narrow, auditable way:

1. Fix the exact local priority E layer from `priority_masked_e_layer_search`.
2. Fill only the remaining cells using simple pair orders, including 6<->9
   quotient-shaped orders.
3. Compare observed remaining inventory as an upper bound against a
   frequency-derived inventory.

It asks whether the local E layer unlocks a formula for the rest of the pair
table. It assigns no plaintext.
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
OCC_STREAMS = ROOT / "analysis" / "audit_20260609" / "homophone_channel" / "occ_streams.json"
OUT_JSON = HERE / "anchored_remaining_fill_results.json"
OUT_MD = HERE / "anchored_remaining_fill_report.md"

RANDOM_SEED = 46920260619
CONTROL_TRIALS = 1000
SYMBOLS = "*ABCEFILNORSTV"
PAIRS = [f"{a}{b}" for a in range(10) for b in range(a, 10)]
SYMBOL_BITS = math.log2(len(SYMBOLS))
CELL_BITS = math.log2(len(PAIRS))
LABEL_EXCEPTION_BITS = CELL_BITS + SYMBOL_BITS


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def pair_symbol(pair_table: dict[str, Any], pair: str) -> str:
    row = pair_table[pair]
    if row["status"] == "pure":
        return row["symbol_if_pure"]
    return "+".join(sorted(row["symbols"]))


def labels_from_formula() -> dict[str, str]:
    formula = load_json(FORMULA_JSON)
    return {pair: pair_symbol(formula["pair_table"], pair) for pair in PAIRS}


def corpus_symbol_counts() -> Counter[str]:
    occ = load_json(OCC_STREAMS)["occ"]
    return Counter({symbol: len(rows) for symbol, rows in occ.items()})


def fixed_claims() -> dict[str, str]:
    out = {
        "45": "F",
        "55": "V",
        "77": "N",
        "88": "A",
        "11": "E",
        "33": "E",
        "44": "E",
        "66": "E",
        "99": "E",
    }
    for pair in PAIRS:
        a, b = int(pair[0]), int(pair[1])
        if a * b == 5:
            out[pair] = "E"
        if a in {4, 5, 7, 8} and b in {4, 5, 7, 8} and pair not in {"45", "55", "77", "88"}:
            out[pair] = "E"
    return out


def log2_multinomial(labels: list[str]) -> float:
    counts = Counter(labels)
    bits = math.lgamma(len(labels) + 1) / math.log(2)
    for count in counts.values():
        bits -= math.lgamma(count + 1) / math.log(2)
    return bits


def apportion(total: int, weights: dict[str, float]) -> Counter[str]:
    weight_sum = sum(weights.values())
    raw = {symbol: total * weights[symbol] / weight_sum for symbol in SYMBOLS}
    floors = {symbol: int(math.floor(raw[symbol])) for symbol in SYMBOLS}
    remaining = total - sum(floors.values())
    order = sorted(SYMBOLS, key=lambda symbol: (raw[symbol] - floors[symbol], weights[symbol], symbol), reverse=True)
    out = Counter(floors)
    for symbol in order[:remaining]:
        out[symbol] += 1
    return out


def inventories(labels: dict[str, str], remaining_pairs: list[str], claims: dict[str, str]) -> dict[str, Counter[str]]:
    observed_remaining = Counter(labels[pair] for pair in remaining_pairs)
    global_total = len(PAIRS)
    corpus_counts = corpus_symbol_counts()
    full_frequency = Counter({symbol: 1 for symbol in SYMBOLS})
    full_frequency.update(apportion(global_total - len(SYMBOLS), {symbol: corpus_counts[symbol] for symbol in SYMBOLS}))
    claim_counts = Counter(claims.values())
    frequency_remaining = Counter({symbol: max(0, full_frequency[symbol] - claim_counts[symbol]) for symbol in SYMBOLS})
    delta = len(remaining_pairs) - sum(frequency_remaining.values())
    if delta > 0:
        weights = {symbol: corpus_counts[symbol] for symbol in SYMBOLS}
        for symbol, count in apportion(delta, weights).items():
            frequency_remaining[symbol] += count
    elif delta < 0:
        for symbol in sorted(SYMBOLS, key=lambda item: (frequency_remaining[item], corpus_counts[item]), reverse=True):
            if delta == 0:
                break
            removable = min(frequency_remaining[symbol], -delta)
            frequency_remaining[symbol] -= removable
            delta += removable
    return {
        "observed_remaining_upper_bound": observed_remaining,
        "frequency_remaining": frequency_remaining,
    }


def qdigit(digit: int) -> int:
    return 6 if digit == 9 else digit


def pair_orders(remaining_pairs: list[str]) -> dict[str, list[str]]:
    def coords(pair: str) -> tuple[int, int]:
        return int(pair[0]), int(pair[1])

    def qcoords(pair: str) -> tuple[int, int]:
        a, b = coords(pair)
        qa, qb = sorted((qdigit(a), qdigit(b)))
        return qa, qb

    orders = {
        "natural": sorted(remaining_pairs, key=lambda p: coords(p)),
        "reverse": sorted(remaining_pairs, key=lambda p: coords(p), reverse=True),
        "by_sum": sorted(remaining_pairs, key=lambda p: (sum(coords(p)), coords(p))),
        "by_sum_rev": sorted(remaining_pairs, key=lambda p: (-sum(coords(p)), coords(p))),
        "by_diff": sorted(remaining_pairs, key=lambda p: (coords(p)[1] - coords(p)[0], coords(p))),
        "by_product": sorted(remaining_pairs, key=lambda p: (coords(p)[0] * coords(p)[1], coords(p))),
        "by_product_rev": sorted(remaining_pairs, key=lambda p: (-(coords(p)[0] * coords(p)[1]), coords(p))),
        "q_natural": sorted(remaining_pairs, key=lambda p: (qcoords(p), coords(p))),
        "q_by_sum": sorted(remaining_pairs, key=lambda p: (sum(qcoords(p)), qcoords(p), coords(p))),
        "q_by_diff": sorted(remaining_pairs, key=lambda p: (qcoords(p)[1] - qcoords(p)[0], qcoords(p), coords(p))),
        "q_same_then_cross": sorted(
            remaining_pairs,
            key=lambda p: (int(6 in coords(p) or 9 in coords(p)), qcoords(p), coords(p)),
        ),
        "highblock_out": sorted(
            remaining_pairs,
            key=lambda p: (int(int(p[0]) in {4, 5, 7, 8} or int(p[1]) in {4, 5, 7, 8}), coords(p)),
        ),
    }
    return orders


def symbol_orders(corpus_counts: Counter[str], observed_counts: Counter[str]) -> dict[str, list[str]]:
    first_table = []
    labels = labels_from_formula()
    for pair in PAIRS:
        symbol = labels[pair]
        if symbol in SYMBOLS and symbol not in first_table:
            first_table.append(symbol)
    for symbol in SYMBOLS:
        if symbol not in first_table:
            first_table.append(symbol)
    return {
        "first_code_table": first_table,
        "alphabet": list(SYMBOLS),
        "alphabet_reverse": list(reversed(SYMBOLS)),
        "corpus_desc": sorted(SYMBOLS, key=lambda symbol: (-corpus_counts[symbol], symbol)),
        "corpus_asc": sorted(SYMBOLS, key=lambda symbol: (corpus_counts[symbol], symbol)),
        "observed_remaining_desc": sorted(SYMBOLS, key=lambda symbol: (-observed_counts[symbol], symbol)),
    }


def sequence_fill(order: list[str], quotas: Counter[str], symbol_order: list[str], method: str) -> dict[str, str]:
    remaining = Counter(quotas)
    out: dict[str, str] = {}
    if method == "blocks":
        stream = []
        for symbol in symbol_order:
            stream.extend([symbol] * remaining[symbol])
        return {pair: symbol for pair, symbol in zip(order, stream)}
    if method == "round_robin":
        stream = []
        while len(stream) < len(order):
            progressed = False
            for symbol in symbol_order:
                if remaining[symbol] > 0:
                    stream.append(symbol)
                    remaining[symbol] -= 1
                    progressed = True
            if not progressed:
                break
        return {pair: symbol for pair, symbol in zip(order, stream)}
    if method == "largest_quota":
        for pair in order:
            symbol = max(symbol_order, key=lambda item: (remaining[item], -symbol_order.index(item)))
            out[pair] = symbol
            remaining[symbol] -= 1
        return out
    raise ValueError(method)


def evaluate(labels: dict[str, str], claims: dict[str, str], fill: dict[str, str], model_cost_bits: float) -> dict[str, Any]:
    predicted = dict(claims)
    predicted.update(fill)
    hits = sum(1 for pair in PAIRS if predicted.get(pair) == labels[pair])
    anchored_hits = sum(1 for pair, symbol in claims.items() if labels[pair] == symbol)
    remaining_pairs = [pair for pair in PAIRS if pair not in claims]
    remaining_hits = sum(1 for pair in remaining_pairs if predicted.get(pair) == labels[pair])
    errors = len(PAIRS) - hits
    inventory_bits = log2_multinomial([labels[pair] for pair in PAIRS])
    mdl_bits = model_cost_bits + errors * LABEL_EXCEPTION_BITS
    return {
        "hits": hits,
        "accuracy": hits / len(PAIRS),
        "anchored_hits": anchored_hits,
        "remaining_hits": remaining_hits,
        "remaining_accuracy": remaining_hits / len(remaining_pairs),
        "errors": errors,
        "mdl_bits": mdl_bits,
        "inventory_lookup_bits": inventory_bits,
        "gain_vs_inventory_lookup_bits": inventory_bits - mdl_bits,
        "mdl_ratio_vs_inventory_lookup": mdl_bits / inventory_bits,
    }


def search(labels: dict[str, str], inventory_mode: str | None = None) -> list[dict[str, Any]]:
    claims = fixed_claims()
    remaining_pairs = [pair for pair in PAIRS if pair not in claims]
    invs = inventories(labels, remaining_pairs, claims)
    corpus_counts = corpus_symbol_counts()
    orders = pair_orders(remaining_pairs)
    sym_orders = symbol_orders(corpus_counts, invs["observed_remaining_upper_bound"])
    rows = []
    inventory_items = invs.items() if inventory_mode is None else [(inventory_mode, invs[inventory_mode])]
    for inv_name, quotas in inventory_items:
        if sum(quotas.values()) != len(remaining_pairs):
            continue
        for order_name, order in orders.items():
            for sym_order_name, sym_order in sym_orders.items():
                for method in ["round_robin", "blocks", "largest_quota"]:
                    fill = sequence_fill(order, quotas, sym_order, method)
                    cost = 84.3 + 12.0 + math.log2(len(orders)) + math.log2(len(sym_orders)) + math.log2(3)
                    if inv_name == "observed_remaining_upper_bound":
                        cost += log2_multinomial([labels[pair] for pair in remaining_pairs])
                    else:
                        cost += 18.0
                    metrics = evaluate(labels, claims, fill, cost)
                    rows.append(
                        {
                            "inventory": inv_name,
                            "pair_order": order_name,
                            "symbol_order": sym_order_name,
                            "sequence": method,
                            **metrics,
                        }
                    )
    rows.sort(key=lambda row: (-row["hits"], row["mdl_bits"], row["inventory"], row["pair_order"], row["symbol_order"], row["sequence"]))
    return rows


def controls(labels: dict[str, str], observed_best: dict[str, Any]) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED)
    label_values = [labels[pair] for pair in PAIRS]
    best_hits = []
    best_gains = []
    for _trial in range(CONTROL_TRIALS):
        shuffled = label_values[:]
        rng.shuffle(shuffled)
        shuffled_labels = {pair: symbol for pair, symbol in zip(PAIRS, shuffled)}
        rows = search(shuffled_labels, observed_best["inventory"])
        best = rows[0]
        best_hits.append(best["hits"])
        best_gains.append(best["gain_vs_inventory_lookup_bits"])

    def summarize(values: list[float], observed: float) -> dict[str, float]:
        mean = sum(values) / len(values)
        sd = (sum((value - mean) ** 2 for value in values) / (len(values) - 1)) ** 0.5
        return {
            "observed": observed,
            "mean": mean,
            "sd": sd,
            "min": min(values),
            "max": max(values),
            "p_good_direction": (sum(value >= observed for value in values) + 1) / (len(values) + 1),
            "z_good_direction": (observed - mean) / sd if sd else 0.0,
        }

    return {
        "trials": CONTROL_TRIALS,
        "best_hits": summarize(best_hits, observed_best["hits"]),
        "best_gain_vs_inventory_lookup_bits": summarize(best_gains, observed_best["gain_vs_inventory_lookup_bits"]),
    }


def classify(best: dict[str, Any], ctrl: dict[str, Any]) -> str:
    if best["gain_vs_inventory_lookup_bits"] > 0 and ctrl["best_gain_vs_inventory_lookup_bits"]["p_good_direction"] <= 0.05:
        return "candidate_anchored_remaining_formula"
    if best["hits"] >= 28 and ctrl["best_hits"]["p_good_direction"] <= 0.05:
        return "weak_anchored_remaining_signal"
    return "anchored_remaining_fill_not_promoted"


def write_report(result: dict[str, Any]) -> None:
    best = result["best"]
    ctrl = result["controls"]
    lines = [
        "# Anchored Remaining Fill Search",
        "",
        "Generated by `anchored_remaining_fill_search.py`.",
        "",
        "This composes fixed E-priority anchors with simple remaining-cell fill",
        "orders, including 6<->9 quotient-shaped orders. It does not assign",
        "plaintext.",
        "",
        "## Summary",
        "",
        "| Hits | Remaining hits | Inventory | Pair order | Symbol order | Sequence | MDL/inventory | Gain | p(hit) | p(MDL) | Verdict |",
        "|---:|---:|---|---|---|---|---:|---:|---:|---:|---|",
        f"| {best['hits']}/55 | {best['remaining_hits']}/40 | `{best['inventory']}` | `{best['pair_order']}` | `{best['symbol_order']}` | `{best['sequence']}` | {best['mdl_ratio_vs_inventory_lookup']:.3f} | {best['gain_vs_inventory_lookup_bits']:.1f} | {ctrl['best_hits']['p_good_direction']:.5f} | {ctrl['best_gain_vs_inventory_lookup_bits']['p_good_direction']:.5f} | `{result['verdict']}` |",
        "",
        "## Top Rows",
        "",
        "| Hits | Remaining | Inventory | Pair order | Symbol order | Sequence | MDL/inventory | Gain |",
        "|---:|---:|---|---|---|---|---:|---:|",
    ]
    for row in result["top_rows"]:
        lines.append(
            f"| {row['hits']}/55 | {row['remaining_hits']}/40 | `{row['inventory']}` | `{row['pair_order']}` | `{row['symbol_order']}` | `{row['sequence']}` | {row['mdl_ratio_vs_inventory_lookup']:.3f} | {row['gain_vs_inventory_lookup_bits']:.1f} |"
        )
    lines += [
        "",
        "## Interpretation",
        "",
        "The observed-remaining inventory row is an upper bound because it sees the",
        "target inventory after anchors. The frequency-derived row is the",
        "non-target inventory variant. A promotable formula would need positive",
        "MDL against inventory lookup and search-level controls.",
        "",
        f"Translation delta: `{result['translation_delta']}`.",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    labels = labels_from_formula()
    rows = search(labels)
    best = rows[0]
    ctrl = controls(labels, best)
    result = {
        "schema": "anchored_remaining_fill_results.v1",
        "source": str(FORMULA_JSON.relative_to(ROOT)),
        "control_trials": CONTROL_TRIALS,
        "best": best,
        "top_rows": rows[:25],
        "controls": ctrl,
        "verdict": classify(best, ctrl),
        "translation_delta": "NONE",
        "new_plaintext": False,
    }
    write_json(OUT_JSON, result)
    write_report(result)
    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(
        "hits={hits}/55 remaining={remaining}/40 gain={gain:.1f} p={p:.5f} verdict={verdict}".format(
            hits=best["hits"],
            remaining=best["remaining_hits"],
            gain=best["gain_vs_inventory_lookup_bits"],
            p=ctrl["best_gain_vs_inventory_lookup_bits"]["p_good_direction"],
            verdict=result["verdict"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
