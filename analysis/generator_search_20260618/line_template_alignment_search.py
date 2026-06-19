#!/usr/bin/env python3
"""Line-template alignment search for the 469 pair table.

This pass tests whether rows, columns, diagonals, or anti-diagonals of the
triangular 55-cell pair table are generated from a short line template by
substring alignment, reversal, or circular symbol shifts. This is different
from single-line marginal statistics: it asks whether an entire family of
matrix lines can be compressed by one reusable template.

Mechanical only. No plaintext or translation is promoted.
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

OUT_JSON = HERE / "line_template_alignment_results.json"
OUT_MD = HERE / "line_template_alignment_report.md"

SIGMA = list("*ABCEFILNORSTV")
RANDOM_SEED = 46920260619
CONTROL_TRIALS = 2000
SYMBOL_ORDERS = {
    "alphabet": SIGMA,
    "alphabet_reverse": list(reversed(SIGMA)),
}


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


def build_grid(pair_table: dict) -> dict[tuple[int, int], str]:
    return {pair: primary_pair_symbol(pair_table, pair) for pair in natural_pairs()}


def line_families(grid: dict[tuple[int, int], str]) -> dict[str, list[dict]]:
    families: dict[str, list[dict]] = {}
    rows = []
    for a in range(10):
        pairs = [(a, b) for b in range(a, 10)]
        rows.append({"id": f"row_{a}", "pairs": pairs, "text": "".join(grid[p] for p in pairs)})
    families["rows"] = rows
    cols = []
    for b in range(10):
        pairs = [(a, b) for a in range(0, b + 1)]
        cols.append({"id": f"col_{b}", "pairs": pairs, "text": "".join(grid[p] for p in pairs)})
    families["cols"] = cols
    diffs = []
    for d in range(10):
        pairs = [(a, a + d) for a in range(0, 10 - d)]
        diffs.append({"id": f"diff_{d}", "pairs": pairs, "text": "".join(grid[p] for p in pairs)})
    families["diagonal_diff"] = diffs
    sums = []
    for s in range(19):
        pairs = [(a, s - a) for a in range(10) if a <= s - a < 10]
        if pairs:
            sums.append({"id": f"sum_{s}", "pairs": pairs, "text": "".join(grid[p] for p in pairs)})
    families["anti_diagonal_sum"] = sums
    return families


def symbol_orders_from_labels(labels: list[str], pairs: list[tuple[int, int]]) -> dict[str, list[str]]:
    counts = Counter(labels)
    first = {}
    for idx, label in enumerate(labels):
        first.setdefault(label, idx)
    diag_counts = Counter(label for pair, label in zip(pairs, labels) if pair[0] == pair[1])
    out = dict(SYMBOL_ORDERS)
    out["frequency_desc"] = sorted(SIGMA, key=lambda s: (-counts[s], s))
    out["frequency_asc"] = sorted(SIGMA, key=lambda s: (counts[s], s))
    out["first_use"] = sorted(SIGMA, key=lambda s: (first.get(s, 999), s))
    out["diag_pressure"] = sorted(SIGMA, key=lambda s: (-diag_counts[s], -counts[s], s))
    return out


def shift_text(text: str, order: list[str], shift: int) -> str:
    index = {symbol: idx for idx, symbol in enumerate(order)}
    return "".join(order[(index[ch] + shift) % len(order)] for ch in text)


def mismatches(a: str, b: str) -> int:
    return sum(x != y for x, y in zip(a, b))


def best_align_line(
    line: str,
    template: str,
    allow_reverse: bool,
    symbol_order: list[str] | None,
) -> dict:
    best = None
    variants = [(template, "forward")]
    if allow_reverse:
        variants.append((template[::-1], "reverse"))
    shifts = [0] if symbol_order is None else list(range(len(symbol_order)))
    for variant, orientation in variants:
        for shift in shifts:
            shifted = shift_text(variant, symbol_order, shift) if symbol_order is not None else variant
            if len(shifted) < len(line):
                continue
            for start in range(0, len(shifted) - len(line) + 1):
                sub = shifted[start : start + len(line)]
                cost = mismatches(line, sub)
                row = {
                    "mismatches": cost,
                    "start": start,
                    "orientation": orientation,
                    "shift": shift,
                    "substring": sub,
                }
                if best is None or (
                    cost,
                    start,
                    0 if orientation == "forward" else 1,
                    shift,
                ) < (
                    best["mismatches"],
                    best["start"],
                    0 if best["orientation"] == "forward" else 1,
                    best["shift"],
                ):
                    best = row
    if best is None:
        return {"mismatches": len(line), "start": None, "orientation": None, "shift": None, "substring": ""}
    return best


def evaluate_family(lines: list[dict], mode: str, order_name: str | None, order: list[str] | None) -> dict:
    allow_reverse = mode in {"substring_reverse", "substring_reverse_shift"}
    allow_shift = mode in {"substring_shift", "substring_reverse_shift"}
    effective_order = order if allow_shift else None
    templates = [line["text"] for line in lines]
    rows = []
    for template_idx, template in enumerate(templates):
        total = 0
        detail = []
        for line in lines:
            aligned = best_align_line(line["text"], template, allow_reverse, effective_order)
            total += aligned["mismatches"]
            detail.append({"line_id": line["id"], **aligned})
        rows.append(
            {
                "template_line_id": lines[template_idx]["id"],
                "template": template,
                "total_mismatches": total,
                "detail": detail,
            }
        )
    best = min(rows, key=lambda row: (row["total_mismatches"], len(row["template"]), row["template_line_id"]))
    total_chars = sum(len(line["text"]) for line in lines)
    lookup_bits = total_chars * math.log2(len(SIGMA))
    template_bits = len(best["template"]) * math.log2(len(SIGMA))
    address_bits = len(lines) * (math.log2(max(1, len(best["template"]))) + 2.0)
    if allow_reverse:
        address_bits += len(lines)
    if allow_shift:
        address_bits += len(lines) * math.log2(len(SIGMA))
    exception_bits = best["total_mismatches"] * (math.log2(total_chars) + math.log2(len(SIGMA)))
    mdl_bits = template_bits + address_bits + exception_bits
    return {
        "mode": mode,
        "symbol_order": order_name,
        "line_count": len(lines),
        "total_chars": total_chars,
        "template_line_id": best["template_line_id"],
        "template": best["template"],
        "total_mismatches": best["total_mismatches"],
        "match_fraction": 1.0 - best["total_mismatches"] / total_chars,
        "lookup_cost_bits": lookup_bits,
        "mdl_cost_bits": mdl_bits,
        "mdl_gain_vs_lookup_bits": lookup_bits - mdl_bits,
        "lookup_cost_ratio": mdl_bits / lookup_bits,
        "detail": best["detail"],
    }


def search_all(families: dict[str, list[dict]], symbol_orders: dict[str, list[str]]) -> list[dict]:
    rows = []
    for family_name, lines in families.items():
        for mode in ["substring", "substring_reverse"]:
            rows.append({"family": family_name, **evaluate_family(lines, mode, None, None)})
        for order_name, order in symbol_orders.items():
            for mode in ["substring_shift", "substring_reverse_shift"]:
                rows.append({"family": family_name, **evaluate_family(lines, mode, order_name, order)})
    rows.sort(
        key=lambda row: (
            -row["mdl_gain_vs_lookup_bits"],
            -row["match_fraction"],
            row["family"],
            row["mode"],
            row["symbol_order"] or "",
        )
    )
    return rows


def control(best_key: tuple[str, str, str | None], labels: list[str], pairs: list[tuple[int, int]]) -> dict:
    rng = random.Random(RANDOM_SEED + 1)
    family_name, mode, order_name = best_key
    values = []
    gains = []
    for _ in range(CONTROL_TRIALS):
        shuffled = labels[:]
        rng.shuffle(shuffled)
        grid = dict(zip(pairs, shuffled))
        families = line_families(grid)
        orders = symbol_orders_from_labels(shuffled, pairs)
        row = evaluate_family(families[family_name], mode, order_name, orders.get(order_name))
        values.append(row["match_fraction"])
        gains.append(row["mdl_gain_vs_lookup_bits"])
    return {
        "trials": CONTROL_TRIALS,
        "match_fraction": summarize(values),
        "mdl_gain_vs_lookup_bits": summarize(gains),
    }


def summarize(values: list[float]) -> dict:
    mean = sum(values) / len(values)
    sd = (sum((value - mean) ** 2 for value in values) / (len(values) - 1)) ** 0.5
    return {"mean": mean, "sd": sd, "min": min(values), "max": max(values), "values": values[:20]}


def p_ge(values: list[float], observed: float) -> float:
    return (sum(value >= observed for value in values) + 1) / (len(values) + 1)


def verdict(best: dict, ctrl: dict) -> str:
    p_gain = p_ge(ctrl["mdl_gain_vs_lookup_bits"]["values_full"], best["mdl_gain_vs_lookup_bits"]) if "values_full" in ctrl["mdl_gain_vs_lookup_bits"] else 1.0
    if best["mdl_gain_vs_lookup_bits"] > 0 and best["lookup_cost_ratio"] < 1.0 and p_gain <= 0.01:
        return "candidate_line_template_generator"
    if best["match_fraction"] >= 0.70 and best["lookup_cost_ratio"] < 1.2:
        return "weak_line_template_signal"
    return "rejected_control"


def main() -> int:
    formula = load_json(FORMULA_JSON)
    pair_table = formula["pair_table"]
    pairs = natural_pairs()
    labels = [primary_pair_symbol(pair_table, pair) for pair in pairs]
    grid = dict(zip(pairs, labels))
    families = line_families(grid)
    symbol_orders = symbol_orders_from_labels(labels, pairs)
    rows = search_all(families, symbol_orders)
    best = rows[0]
    best_key = (best["family"], best["mode"], best["symbol_order"])

    rng = random.Random(RANDOM_SEED + 1)
    match_controls = []
    gain_controls = []
    for _ in range(CONTROL_TRIALS):
        shuffled = labels[:]
        rng.shuffle(shuffled)
        ctrl_grid = dict(zip(pairs, shuffled))
        ctrl_families = line_families(ctrl_grid)
        ctrl_orders = symbol_orders_from_labels(shuffled, pairs)
        row = evaluate_family(ctrl_families[best_key[0]], best_key[1], best_key[2], ctrl_orders.get(best_key[2]))
        match_controls.append(row["match_fraction"])
        gain_controls.append(row["mdl_gain_vs_lookup_bits"])

    match_mean = sum(match_controls) / len(match_controls)
    match_sd = (sum((value - match_mean) ** 2 for value in match_controls) / (len(match_controls) - 1)) ** 0.5
    gain_mean = sum(gain_controls) / len(gain_controls)
    gain_sd = (sum((value - gain_mean) ** 2 for value in gain_controls) / (len(gain_controls) - 1)) ** 0.5
    ctrl = {
        "trials": CONTROL_TRIALS,
        "match_fraction": {
            "mean": match_mean,
            "sd": match_sd,
            "min": min(match_controls),
            "max": max(match_controls),
            "p_ge_observed": p_ge(match_controls, best["match_fraction"]),
        },
        "mdl_gain_vs_lookup_bits": {
            "mean": gain_mean,
            "sd": gain_sd,
            "min": min(gain_controls),
            "max": max(gain_controls),
            "p_ge_observed": p_ge(gain_controls, best["mdl_gain_vs_lookup_bits"]),
        },
    }
    result_verdict = (
        "candidate_line_template_generator"
        if best["mdl_gain_vs_lookup_bits"] > 0 and ctrl["mdl_gain_vs_lookup_bits"]["p_ge_observed"] <= 0.01
        else "weak_line_template_signal"
        if best["match_fraction"] >= 0.70 and ctrl["match_fraction"]["p_ge_observed"] <= 0.05
        else "rejected_control"
    )
    result = {
        "schema": "line_template_alignment_results.v1",
        "translation_delta": "NONE",
        "control_trials": CONTROL_TRIALS,
        "best": best,
        "top_rows": rows[:80],
        "control": ctrl,
        "verdict": result_verdict,
    }
    write_json(OUT_JSON, result)

    lines = [
        "# Line-Template Alignment Search",
        "",
        "Generated by `line_template_alignment_search.py`.",
        "",
        "This pass tests whether whole row/column/diagonal families can be",
        "compressed as substrings, reversals, or symbol-shifted variants of one",
        "short template line. It is mechanical only and assigns no plaintext.",
        "",
        "## Summary",
        "",
        "| Best family | Mode | Symbol order | Match fraction | MDL/lookup | Control p(match) | Control p(MDL) | Verdict |",
        "|---|---|---|---:|---:|---:|---:|---|",
        f"| `{best['family']}` | `{best['mode']}` | `{best['symbol_order']}` | {best['match_fraction']:.3f} | {best['lookup_cost_ratio']:.3f} | {ctrl['match_fraction']['p_ge_observed']:.4f} | {ctrl['mdl_gain_vs_lookup_bits']['p_ge_observed']:.4f} | `{result_verdict}` |",
        "",
        f"Best template `{best['template_line_id']}`: `{best['template']}`.",
        "",
        "## Top Rows",
        "",
        "| Family | Mode | Order | Template | Match | MDL/lookup | MDL gain bits |",
        "|---|---|---|---|---:|---:|---:|",
    ]
    for row in rows[:25]:
        lines.append(
            f"| `{row['family']}` | `{row['mode']}` | `{row['symbol_order']}` | `{row['template']}` | "
            f"{row['match_fraction']:.3f} | {row['lookup_cost_ratio']:.3f} | {row['mdl_gain_vs_lookup_bits']:.1f} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "A line-template generator would need to compress the line family better",
            "than literal labels and beat the same search on inventory-preserving",
            "shuffles. This pass does not promote plaintext or a glossary.",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT_JSON.relative_to(HERE)}")
    print(f"wrote {OUT_MD.relative_to(HERE)}")
    print(
        "best={} {} match={:.3f} ratio={:.3f} p={:.4f} verdict={}".format(
            best["family"],
            best["mode"],
            best["match_fraction"],
            best["lookup_cost_ratio"],
            ctrl["mdl_gain_vs_lookup_bits"]["p_ge_observed"],
            result_verdict,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
