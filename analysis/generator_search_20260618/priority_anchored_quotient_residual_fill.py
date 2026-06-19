#!/usr/bin/env python3
"""Priority-anchored quotient residual fill.

This is the quotient-correct ablation for the priority E layer:

1. Collapse pair cells by the weak-but-robust `6<->9` quotient.
2. Fix the priority E/blocker layer as quotient anchors.
3. Fill only the 32 unanchored quotient cells with simple quotient orders and
   frequency-derived or observed-residual inventory.
4. Shuffle only residual labels in controls, preserving the fixed anchors.

Mechanical audit only. No plaintext or glossary is inferred.
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
QUOTIENT_JSON = HERE / "digit_orbit_quotient_results.json"
OCC_STREAMS = ROOT / "analysis" / "audit_20260609" / "homophone_channel" / "occ_streams.json"
OUT_JSON = HERE / "priority_anchored_quotient_residual_fill_results.json"
OUT_MD = HERE / "priority_anchored_quotient_residual_fill_report.md"

RANDOM_SEED = 46920260619
CONTROL_TRIALS = 1000
SYMBOLS = "*ABCEFILNORSTV"
SYMBOL_BITS = math.log2(len(SYMBOLS))
ORBIT_BITS = math.log2(46)
LABEL_EXCEPTION_BITS = ORBIT_BITS + SYMBOL_BITS


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def corpus_symbol_counts() -> Counter[str]:
    occ = load_json(OCC_STREAMS)["occ"]
    return Counter({symbol: len(rows) for symbol, rows in occ.items()})


def swap_6_9_orbits() -> list[dict[str, Any]]:
    data = load_json(QUOTIENT_JSON)
    for row in data["top_rows"]:
        if row["id"] == "swap_6_9":
            return row["orbits"]
    raise RuntimeError("swap_6_9 quotient not found")


def fixed_pair_claims() -> dict[str, str]:
    claims = {
        "45": "F",
        "55": "V",
        "77": "N",
        "88": "A",
        "11": "E",
        "33": "E",
        "44": "E",
        "66": "E",
        "99": "E",
        "15": "E",
        "47": "E",
        "48": "E",
        "57": "E",
        "58": "E",
        "78": "E",
    }
    return claims


def quotient_labels_and_anchors(orbits: list[dict[str, Any]]) -> tuple[dict[int, str], dict[int, str]]:
    labels = {row["orbit"]: row["label"] for row in orbits}
    pair_claims = fixed_pair_claims()
    anchors: dict[int, str] = {}
    for row in orbits:
        claims = {pair_claims[pair] for pair in row["pairs"] if pair in pair_claims}
        if not claims:
            continue
        if len(claims) != 1:
            raise ValueError(f"conflicting anchor claims in orbit {row['orbit']}: {claims}")
        symbol = next(iter(claims))
        anchors[row["orbit"]] = symbol
    return labels, anchors


def log2_multinomial(labels: list[str]) -> float:
    counts = Counter(labels)
    bits = math.lgamma(len(labels) + 1) / math.log(2)
    for count in counts.values():
        bits -= math.lgamma(count + 1) / math.log(2)
    return bits


def apportion(total: int, symbols: list[str], weights: dict[str, float]) -> Counter[str]:
    weight_sum = sum(weights[symbol] for symbol in symbols)
    raw = {symbol: total * weights[symbol] / weight_sum for symbol in symbols}
    floors = {symbol: int(math.floor(raw[symbol])) for symbol in symbols}
    remaining = total - sum(floors.values())
    order = sorted(symbols, key=lambda symbol: (raw[symbol] - floors[symbol], weights[symbol], symbol), reverse=True)
    out = Counter(floors)
    for symbol in order[:remaining]:
        out[symbol] += 1
    return out


def inventories(labels: dict[int, str], residual_orbits: list[int]) -> dict[str, Counter[str]]:
    observed = Counter(labels[orbit] for orbit in residual_orbits)
    corpus = corpus_symbol_counts()
    residual_symbols = [symbol for symbol in SYMBOLS if symbol != "E"]
    frequency = Counter({symbol: 1 for symbol in residual_symbols})
    extras = len(residual_orbits) - len(residual_symbols)
    frequency.update(apportion(extras, residual_symbols, {symbol: corpus[symbol] for symbol in residual_symbols}))
    return {
        "observed_residual_upper_bound": observed,
        "frequency_no_e_residual": frequency,
    }


def orbit_key(row: dict[str, Any]) -> tuple[int, int]:
    first = row["pairs"][0]
    return int(first[0]), int(first[1])


def quotient_orders(orbits: list[dict[str, Any]], residual_orbits: list[int]) -> dict[str, list[int]]:
    by_id = {row["orbit"]: row for row in orbits}

    def coords(orbit: int) -> tuple[int, int]:
        return orbit_key(by_id[orbit])

    orders = {
        "orbit_index": sorted(residual_orbits),
        "q_natural": sorted(residual_orbits, key=lambda orbit: coords(orbit)),
        "q_reverse": sorted(residual_orbits, key=lambda orbit: coords(orbit), reverse=True),
        "q_by_sum": sorted(residual_orbits, key=lambda orbit: (sum(coords(orbit)), coords(orbit))),
        "q_by_sum_rev": sorted(residual_orbits, key=lambda orbit: (-sum(coords(orbit)), coords(orbit))),
        "q_by_diff": sorted(residual_orbits, key=lambda orbit: (coords(orbit)[1] - coords(orbit)[0], coords(orbit))),
        "q_by_product": sorted(residual_orbits, key=lambda orbit: (coords(orbit)[0] * coords(orbit)[1], coords(orbit))),
        "q_by_product_rev": sorted(
            residual_orbits,
            key=lambda orbit: (-(coords(orbit)[0] * coords(orbit)[1]), coords(orbit)),
        ),
        "mixed_orbits_last": sorted(
            residual_orbits,
            key=lambda orbit: (int(by_id[orbit]["is_mixed"]), coords(orbit)),
        ),
        "mixed_orbits_first": sorted(
            residual_orbits,
            key=lambda orbit: (-int(by_id[orbit]["is_mixed"]), coords(orbit)),
        ),
    }
    return orders


def symbol_orders(observed: Counter[str]) -> dict[str, list[str]]:
    corpus = corpus_symbol_counts()
    return {
        "first_code_table": list("*NRVFTIEAOLSBC"),
        "alphabet": list(SYMBOLS),
        "alphabet_reverse": list(reversed(SYMBOLS)),
        "corpus_desc": sorted(SYMBOLS, key=lambda symbol: (-corpus[symbol], symbol)),
        "corpus_asc": sorted(SYMBOLS, key=lambda symbol: (corpus[symbol], symbol)),
        "observed_residual_desc": sorted(SYMBOLS, key=lambda symbol: (-observed[symbol], symbol)),
    }


def fill(order: list[int], quotas: Counter[str], symbol_order: list[str], method: str) -> dict[int, str]:
    remaining = Counter(quotas)
    if method == "blocks":
        stream = []
        for symbol in symbol_order:
            stream.extend([symbol] * remaining[symbol])
        return {orbit: symbol for orbit, symbol in zip(order, stream)}
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
        return {orbit: symbol for orbit, symbol in zip(order, stream)}
    if method == "largest_quota":
        out = {}
        for orbit in order:
            symbol = max(symbol_order, key=lambda item: (remaining[item], -symbol_order.index(item)))
            out[orbit] = symbol
            remaining[symbol] -= 1
        return out
    raise ValueError(method)


def evaluate(labels: dict[int, str], anchors: dict[int, str], residual_fill: dict[int, str], model_bits: float) -> dict[str, Any]:
    predictions = dict(anchors)
    predictions.update(residual_fill)
    anchor_hits = sum(1 for orbit, symbol in anchors.items() if labels[orbit] == symbol)
    residual_orbits = [orbit for orbit in labels if orbit not in anchors]
    residual_hits = sum(1 for orbit in residual_orbits if predictions[orbit] == labels[orbit])
    hits = anchor_hits + residual_hits
    errors = len(labels) - hits
    lookup_bits = log2_multinomial([labels[orbit] for orbit in sorted(labels)])
    mdl_bits = model_bits + errors * LABEL_EXCEPTION_BITS
    return {
        "anchor_hits": anchor_hits,
        "anchor_count": len(anchors),
        "residual_hits": residual_hits,
        "residual_count": len(residual_orbits),
        "combined_hits": hits,
        "combined_accuracy": hits / len(labels),
        "residual_accuracy": residual_hits / len(residual_orbits),
        "errors": errors,
        "mdl_bits": mdl_bits,
        "quotient_lookup_bits": lookup_bits,
        "mdl_ratio_vs_quotient_lookup": mdl_bits / lookup_bits,
        "gain_vs_quotient_lookup_bits": lookup_bits - mdl_bits,
    }


def search(orbits: list[dict[str, Any]], labels: dict[int, str], anchors: dict[int, str]) -> list[dict[str, Any]]:
    residual_orbits = [orbit for orbit in sorted(labels) if orbit not in anchors]
    invs = inventories(labels, residual_orbits)
    orders = quotient_orders(orbits, residual_orbits)
    sym_orders = symbol_orders(invs["observed_residual_upper_bound"])
    rows = []
    for inv_name, quotas in invs.items():
        if sum(quotas.values()) != len(residual_orbits):
            continue
        for order_name, order in orders.items():
            for sym_order_name, sym_order in sym_orders.items():
                for method in ["round_robin", "blocks", "largest_quota"]:
                    residual_fill = fill(order, quotas, sym_order, method)
                    model_bits = 78.0 + math.log2(len(orders)) + math.log2(len(sym_orders)) + math.log2(3)
                    if inv_name == "observed_residual_upper_bound":
                        model_bits += log2_multinomial([labels[orbit] for orbit in residual_orbits])
                    else:
                        model_bits += 18.0
                    metrics = evaluate(labels, anchors, residual_fill, model_bits)
                    rows.append(
                        {
                            "inventory": inv_name,
                            "quotient_order": order_name,
                            "symbol_order": sym_order_name,
                            "sequence_method": method,
                            **metrics,
                        }
                    )
    rows.sort(
        key=lambda row: (
            -row["residual_hits"],
            -row["combined_hits"],
            row["mdl_bits"],
            row["inventory"],
            row["quotient_order"],
            row["symbol_order"],
            row["sequence_method"],
        )
    )
    return rows


def residual_shuffle_controls(
    orbits: list[dict[str, Any]],
    labels: dict[int, str],
    anchors: dict[int, str],
    observed: dict[str, Any],
) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED)
    residual_orbits = [orbit for orbit in sorted(labels) if orbit not in anchors]
    residual_labels = [labels[orbit] for orbit in residual_orbits]
    residual_hits = []
    combined_hits = []
    gains = []
    for _trial in range(CONTROL_TRIALS):
        shuffled_values = residual_labels[:]
        rng.shuffle(shuffled_values)
        shuffled = dict(labels)
        for orbit, symbol in zip(residual_orbits, shuffled_values):
            shuffled[orbit] = symbol
        best = search(orbits, shuffled, anchors)[0]
        residual_hits.append(best["residual_hits"])
        combined_hits.append(best["combined_hits"])
        gains.append(best["gain_vs_quotient_lookup_bits"])

    def summarize(values: list[float], observed_value: float) -> dict[str, float]:
        mean = sum(values) / len(values)
        sd = (sum((value - mean) ** 2 for value in values) / (len(values) - 1)) ** 0.5
        return {
            "observed": observed_value,
            "mean": mean,
            "sd": sd,
            "min": min(values),
            "max": max(values),
            "p_good_direction": (sum(value >= observed_value for value in values) + 1) / (len(values) + 1),
            "z_good_direction": (observed_value - mean) / sd if sd else 0.0,
        }

    return {
        "trials": CONTROL_TRIALS,
        "residual_hits": summarize(residual_hits, observed["residual_hits"]),
        "combined_hits": summarize(combined_hits, observed["combined_hits"]),
        "gain_vs_quotient_lookup_bits": summarize(gains, observed["gain_vs_quotient_lookup_bits"]),
    }


def classify(best: dict[str, Any], ctrl: dict[str, Any]) -> str:
    if best["gain_vs_quotient_lookup_bits"] > 0 and ctrl["gain_vs_quotient_lookup_bits"]["p_good_direction"] <= 0.05:
        return "candidate_priority_anchored_quotient_formula"
    if best["residual_hits"] >= 14 and ctrl["residual_hits"]["p_good_direction"] <= 0.05:
        return "weak_priority_anchored_quotient_signal"
    return "priority_anchored_quotient_residual_not_promoted"


def write_report(result: dict[str, Any]) -> None:
    best = result["best"]
    ctrl = result["controls"]
    lines = [
        "# Priority-Anchored Quotient Residual Fill",
        "",
        "Generated by `priority_anchored_quotient_residual_fill.py`.",
        "",
        "This is the quotient-correct ablation: fixed priority E/blocker anchors",
        "are preserved, and only residual quotient labels are shuffled in controls.",
        "",
        "## Summary",
        "",
        "| Anchors | Residual hits | Combined hits | Inventory | Order | Symbol order | Sequence | MDL/lookup | Gain | p(residual) | p(MDL) | Verdict |",
        "|---:|---:|---:|---|---|---|---|---:|---:|---:|---:|---|",
        f"| {best['anchor_hits']}/{best['anchor_count']} | {best['residual_hits']}/{best['residual_count']} | {best['combined_hits']}/46 | `{best['inventory']}` | `{best['quotient_order']}` | `{best['symbol_order']}` | `{best['sequence_method']}` | {best['mdl_ratio_vs_quotient_lookup']:.3f} | {best['gain_vs_quotient_lookup_bits']:.1f} | {ctrl['residual_hits']['p_good_direction']:.5f} | {ctrl['gain_vs_quotient_lookup_bits']['p_good_direction']:.5f} | `{result['verdict']}` |",
        "",
        "## Anchors",
        "",
        f"- Anchor quotient cells: `{result['anchor_count']}`.",
        f"- Residual quotient cells: `{result['residual_count']}`.",
        f"- Residual observed inventory: `{result['residual_observed_inventory']}`.",
        "",
        "## Top Rows",
        "",
        "| Residual | Combined | Inventory | Order | Symbol order | Sequence | MDL/lookup | Gain |",
        "|---:|---:|---|---|---|---|---:|---:|",
    ]
    for row in result["top_rows"]:
        lines.append(
            f"| {row['residual_hits']}/{row['residual_count']} | {row['combined_hits']}/46 | `{row['inventory']}` | `{row['quotient_order']}` | `{row['symbol_order']}` | `{row['sequence_method']}` | {row['mdl_ratio_vs_quotient_lookup']:.3f} | {row['gain_vs_quotient_lookup_bits']:.1f} |"
        )
    lines += [
        "",
        "## Interpretation",
        "",
        "A positive result would show that the E-priority layer unlocks an ordered",
        "quotient residual worksheet. A negative result means the exact E layer",
        "remains local and does not explain non-E placement.",
        "",
        f"Translation delta: `{result['translation_delta']}`.",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    orbits = swap_6_9_orbits()
    labels, anchors = quotient_labels_and_anchors(orbits)
    rows = search(orbits, labels, anchors)
    best = rows[0]
    ctrl = residual_shuffle_controls(orbits, labels, anchors, best)
    residual_orbits = [orbit for orbit in sorted(labels) if orbit not in anchors]
    result = {
        "schema": "priority_anchored_quotient_residual_fill_results.v1",
        "source": str(QUOTIENT_JSON.relative_to(ROOT)),
        "anchor_count": len(anchors),
        "residual_count": len(residual_orbits),
        "anchor_orbits": anchors,
        "residual_observed_inventory": dict(Counter(labels[orbit] for orbit in residual_orbits)),
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
        "anchors={anchor_hits}/{anchor_count} residual={residual_hits}/{residual_count} combined={combined}/46 gain={gain:.1f} p={p:.5f} verdict={verdict}".format(
            anchor_hits=best["anchor_hits"],
            anchor_count=best["anchor_count"],
            residual_hits=best["residual_hits"],
            residual_count=best["residual_count"],
            combined=best["combined_hits"],
            gain=best["gain_vs_quotient_lookup_bits"],
            p=ctrl["gain_vs_quotient_lookup_bits"]["p_good_direction"],
            verdict=result["verdict"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
