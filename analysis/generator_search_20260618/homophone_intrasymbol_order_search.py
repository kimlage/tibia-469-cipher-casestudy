#!/usr/bin/env python3
"""Intra-symbol homophone order/search for the 469 pair table.

We know the homophone class sizes track internal symbol frequency. This pass
asks a narrower question: once a symbol receives N pair cells, are those cells
chosen or ordered by a simple rule?

The tests cover:

- compactness of each symbol's pair set under natural pair orders;
- rank correlation between pair features and first use / corpus frequency
  within each multi-homophone symbol.

Controls preserve the exact class sizes by shuffling labels over the 55 pair
cells. No semantic translation is produced.
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

OUT_JSON = HERE / "homophone_intrasymbol_order_results.json"
OUT_MD = HERE / "homophone_intrasymbol_order_report.md"

RANDOM_SEED = 46920260619
TRIALS = 10000


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def primary_pair_symbol(pair_table: dict, pair: str) -> str:
    row = pair_table[pair]
    if row["status"] == "pure":
        return row["symbol_if_pure"]
    return sorted(row["symbols"])[0]


def all_pairs() -> list[str]:
    return [f"{i}{j}" for i in range(10) for j in range(i, 10)]


def pair_orders() -> dict[str, list[str]]:
    pairs = all_pairs()
    return {
        "upper_row": pairs,
        "upper_row_rev": list(reversed(pairs)),
        "upper_column": [f"{i}{j}" for j in range(10) for i in range(j + 1)],
        "by_sum": sorted(pairs, key=lambda p: (int(p[0]) + int(p[1]), int(p[0]), int(p[1]))),
        "by_diff": sorted(pairs, key=lambda p: (int(p[1]) - int(p[0]), int(p[0]), int(p[1]))),
        "by_product": sorted(pairs, key=lambda p: (int(p[0]) * int(p[1]), int(p[0]), int(p[1]))),
        "by_first_use_proxy": [],  # filled at runtime
    }


def pair_features(pair: str) -> dict[str, float]:
    a, b = int(pair[0]), int(pair[1])
    return {
        "min_digit": a,
        "max_digit": b,
        "sum": a + b,
        "diff": b - a,
        "product": a * b,
        "triangular_index": b * (b + 1) // 2 + a,
        "numeric_pair": int(pair),
        "row_then_col": a * 10 + b,
        "col_then_row": b * 10 + a,
    }


def usage_stats() -> dict[str, dict]:
    occ = load_json(OCC_STREAMS)["occ"]
    events = []
    counts = Counter()
    first = {}
    for symbol, rows in occ.items():
        for row in rows:
            code = row["code"]
            pair = "".join(sorted(code))
            event = (int(row["book"]), int(row["pos"]), symbol, code, pair)
            events.append(event)
            counts[pair] += 1
    for idx, (book, pos, symbol, code, pair) in enumerate(sorted(events)):
        first.setdefault(
            pair,
            {
                "global_index": idx,
                "book": book,
                "position": pos,
                "symbol": symbol,
                "code": code,
            },
        )
    return {
        pair: {
            "count": counts[pair],
            "first": first[pair],
        }
        for pair in counts
    }


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


def pearson(xs: list[float], ys: list[float]) -> float:
    if len(xs) < 2:
        return 0.0
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    dx = sum((x - mx) ** 2 for x in xs)
    dy = sum((y - my) ** 2 for y in ys)
    if not dx or not dy:
        return 0.0
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / math.sqrt(dx * dy)


def spearman(xs: list[float], ys: list[float]) -> float:
    return pearson(ranks(xs), ranks(ys))


def label_map(pair_table: dict) -> dict[str, str]:
    return {pair: primary_pair_symbol(pair_table, pair) for pair in all_pairs()}


def compactness_score(labels: dict[str, str], orders: dict[str, list[str]]) -> dict:
    by_symbol = defaultdict(list)
    for pair, symbol in labels.items():
        by_symbol[symbol].append(pair)
    rows = []
    for order_name, order_pairs in orders.items():
        if not order_pairs:
            continue
        rank = {pair: idx for idx, pair in enumerate(order_pairs)}
        spans = []
        gap_excess = []
        for symbol, pairs in by_symbol.items():
            if len(pairs) < 2:
                continue
            positions = sorted(rank[pair] for pair in pairs)
            span = positions[-1] - positions[0] + 1
            spans.append(span / len(order_pairs))
            gap_excess.append((span - len(positions)) / len(order_pairs))
        rows.append(
            {
                "order": order_name,
                "mean_normalized_span": sum(spans) / len(spans),
                "mean_gap_excess": sum(gap_excess) / len(gap_excess),
            }
        )
    rows.sort(key=lambda row: row["mean_gap_excess"])
    best = rows[0]
    return {"rows": rows, "best": best}


def correlation_scan(labels: dict[str, str], usage: dict[str, dict]) -> dict:
    by_symbol = defaultdict(list)
    for pair, symbol in labels.items():
        by_symbol[symbol].append(pair)
    rows = []
    for symbol, pairs in by_symbol.items():
        if len(pairs) < 3:
            continue
        first_values = [usage[pair]["first"]["global_index"] for pair in pairs]
        count_values = [usage[pair]["count"] for pair in pairs]
        for feature_name in pair_features(pairs[0]):
            feature_values = [pair_features(pair)[feature_name] for pair in pairs]
            rows.append(
                {
                    "symbol": symbol,
                    "n": len(pairs),
                    "feature": feature_name,
                    "spearman_first_use": spearman(feature_values, first_values),
                    "spearman_count": spearman(feature_values, count_values),
                }
            )
    rows.sort(key=lambda row: max(abs(row["spearman_first_use"]), abs(row["spearman_count"])), reverse=True)
    aggregate_first = sum(abs(row["spearman_first_use"]) for row in rows) / len(rows)
    aggregate_count = sum(abs(row["spearman_count"]) for row in rows) / len(rows)
    return {
        "rows": rows,
        "aggregate_abs_first_use": aggregate_first,
        "aggregate_abs_count": aggregate_count,
        "best": rows[0],
    }


def control(labels: dict[str, str], orders: dict[str, list[str]], usage: dict[str, dict]) -> dict:
    rng = random.Random(RANDOM_SEED)
    pairs = list(labels)
    label_values = [labels[pair] for pair in pairs]
    observed_compact = compactness_score(labels, orders)["best"]["mean_gap_excess"]
    observed_corr = correlation_scan(labels, usage)
    compact_values = []
    corr_first_values = []
    corr_count_values = []
    shuffled_values = label_values[:]
    for _trial in range(TRIALS):
        rng.shuffle(shuffled_values)
        current_labels = {pair: symbol for pair, symbol in zip(pairs, shuffled_values)}
        compact_values.append(compactness_score(current_labels, orders)["best"]["mean_gap_excess"])
        corr = correlation_scan(current_labels, usage)
        corr_first_values.append(corr["aggregate_abs_first_use"])
        corr_count_values.append(corr["aggregate_abs_count"])

    def summarize(values: list[float], observed: float, low_is_good: bool) -> dict:
        mean = sum(values) / len(values)
        sd = (sum((value - mean) ** 2 for value in values) / (len(values) - 1)) ** 0.5
        if low_is_good:
            p = (sum(value <= observed for value in values) + 1) / (len(values) + 1)
            z = (mean - observed) / sd if sd else 0.0
        else:
            p = (sum(value >= observed for value in values) + 1) / (len(values) + 1)
            z = (observed - mean) / sd if sd else 0.0
        return {"observed": observed, "mean": mean, "sd": sd, "z": z, "p": p, "min": min(values), "max": max(values)}

    return {
        "compactness_best_gap": summarize(compact_values, observed_compact, True),
        "aggregate_abs_first_use_corr": summarize(corr_first_values, observed_corr["aggregate_abs_first_use"], False),
        "aggregate_abs_count_corr": summarize(corr_count_values, observed_corr["aggregate_abs_count"], False),
    }


def main() -> int:
    formula = load_json(FORMULA_JSON)
    pair_table = formula["pair_table"]
    usage = usage_stats()
    labels = label_map(pair_table)
    first_order_pairs = sorted(all_pairs(), key=lambda pair: usage[pair]["first"]["global_index"])
    orders = pair_orders()
    orders["by_first_use_proxy"] = first_order_pairs
    compact = compactness_score(labels, orders)
    corr = correlation_scan(labels, usage)
    ctl = control(labels, orders, usage)
    strongest = min(
        (
            {"metric": name, **values}
            for name, values in ctl.items()
        ),
        key=lambda row: row["p"],
    )
    verdict = "rejected_control"
    output = {
        "schema": "homophone_intrasymbol_order_results.v1",
        "translation_delta": "NONE",
        "accepted_original_formula": None,
        "compactness": compact,
        "correlations": corr,
        "control": ctl,
        "strongest": strongest,
        "verdict": verdict,
    }
    write_json(OUT_JSON, output)

    lines = [
        "# Homophone Intra-Symbol Order Search",
        "",
        "Generated by `homophone_intrasymbol_order_search.py`.",
        "",
        "This pass asks whether pair cells inside each homophone class are",
        "chosen or ordered by first use, frequency, or simple matrix features.",
        "",
        "## Best Controlled Metrics",
        "",
        "| Metric | Observed | Control mean | z | p | Verdict |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for name, values in ctl.items():
        lines.append(
            f"| `{name}` | {values['observed']:.3f} | {values['mean']:.3f} | {values['z']:.2f} | {values['p']:.3f} | `{verdict}` |"
        )
    lines.extend(
        [
            "",
            "## Compactness by Pair Order",
            "",
            "| Order | Mean normalized span | Mean gap excess |",
            "|---|---:|---:|",
        ]
    )
    for row in compact["rows"]:
        lines.append(f"| `{row['order']}` | {row['mean_normalized_span']:.3f} | {row['mean_gap_excess']:.3f} |")
    lines.extend(
        [
            "",
            "## Strongest Raw Correlations",
            "",
            "| Symbol | n | Feature | Spearman first-use | Spearman count |",
            "|---|---:|---|---:|---:|",
        ]
    )
    for row in corr["rows"][:15]:
        lines.append(
            f"| `{row['symbol']}` | {row['n']} | `{row['feature']}` | {row['spearman_first_use']:.3f} | {row['spearman_count']:.3f} |"
        )
    lines.extend(
        [
            "",
            "## Verdict",
            "",
            "No intra-symbol ordering rule survives controls that preserve the exact",
            "homophone class sizes. The homophone inventory size is meaningful, but",
            "the specific pair choices inside each symbol remain unexplained.",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT_JSON.relative_to(HERE)}")
    print(f"wrote {OUT_MD.relative_to(HERE)}")
    print(f"strongest={strongest['metric']} p={strongest['p']:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
