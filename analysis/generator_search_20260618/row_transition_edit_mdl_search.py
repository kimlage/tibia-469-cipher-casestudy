#!/usr/bin/env python3
"""Row-to-row edit grammar search for the 469 pair table.

This pass tests a human-workflow hypothesis that was not covered by the direct
cell-formula searches: perhaps the 55-cell pair table was drafted line by line,
with each row/column/diagonal derived from the previous one by simple
transformations and a small edit log.

The model is deliberately charged for every transform choice and every literal
edit. If a line is only explained by many substitutions, the result should look
like a lookup table. No plaintext, glossary, or semantic meaning is promoted.
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

OUT_JSON = HERE / "row_transition_edit_mdl_results.json"
OUT_MD = HERE / "row_transition_edit_mdl_report.md"

SIGMA = tuple("*ABCEFILNORSTV")
SYMBOL_BITS = math.log2(len(SIGMA))
RANDOM_SEED = 46920260619
CONTROL_TRIALS = 400
SHIFT_ORDER_NAMES = {"alphabet", "frequency_desc"}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def natural_pairs() -> list[tuple[int, int]]:
    return [(a, b) for a in range(10) for b in range(a, 10)]


def pair_key(pair: tuple[int, int]) -> str:
    return f"{pair[0]}{pair[1]}"


def primary_pair_symbol(pair_table: dict[str, Any], pair: tuple[int, int]) -> str:
    row = pair_table[pair_key(pair)]
    if row["status"] == "pure":
        return row["symbol_if_pure"]
    return sorted(row["symbols"])[0]


def build_grid(pair_table: dict[str, Any]) -> dict[tuple[int, int], str]:
    return {pair: primary_pair_symbol(pair_table, pair) for pair in natural_pairs()}


def line_families(grid: dict[tuple[int, int], str]) -> dict[str, list[dict[str, Any]]]:
    families: dict[str, list[dict[str, Any]]] = {}

    rows = []
    for a in range(10):
        pairs = [(a, b) for b in range(a, 10)]
        rows.append({"id": f"row_{a}", "pairs": [pair_key(p) for p in pairs], "text": "".join(grid[p] for p in pairs)})
    families["rows"] = rows

    cols = []
    for b in range(10):
        pairs = [(a, b) for a in range(0, b + 1)]
        cols.append({"id": f"col_{b}", "pairs": [pair_key(p) for p in pairs], "text": "".join(grid[p] for p in pairs)})
    families["cols"] = cols

    diffs = []
    for d in range(10):
        pairs = [(a, a + d) for a in range(0, 10 - d)]
        diffs.append({"id": f"diff_{d}", "pairs": [pair_key(p) for p in pairs], "text": "".join(grid[p] for p in pairs)})
    families["diagonal_diff"] = diffs

    sums = []
    for s in range(19):
        pairs = [(a, s - a) for a in range(10) if a <= s - a < 10]
        if pairs:
            sums.append({"id": f"sum_{s}", "pairs": [pair_key(p) for p in pairs], "text": "".join(grid[p] for p in pairs)})
    families["anti_diagonal_sum"] = sums

    return families


def symbol_orders(labels: list[str], pairs: list[tuple[int, int]]) -> dict[str, list[str]]:
    counts = Counter(labels)
    first_seen: dict[str, int] = {}
    for idx, label in enumerate(labels):
        first_seen.setdefault(label, idx)
    diagonal_counts = Counter(label for pair, label in zip(pairs, labels) if pair[0] == pair[1])
    return {
        "alphabet": list(SIGMA),
        "alphabet_reverse": list(reversed(SIGMA)),
        "frequency_desc": sorted(SIGMA, key=lambda symbol: (-counts[symbol], symbol)),
        "frequency_asc": sorted(SIGMA, key=lambda symbol: (counts[symbol], symbol)),
        "first_use": sorted(SIGMA, key=lambda symbol: (first_seen.get(symbol, 999), symbol)),
        "diagonal_pressure": sorted(SIGMA, key=lambda symbol: (-diagonal_counts[symbol], -counts[symbol], symbol)),
    }


def shift_text(text: str, order: list[str], shift: int) -> str:
    index = {symbol: idx for idx, symbol in enumerate(order)}
    return "".join(order[(index[ch] + shift) % len(order)] for ch in text)


def edit_distance_bits(source: str, target: str) -> dict[str, Any]:
    """Return a charged edit script from source to target.

    The cost is intentionally conservative. A substitution or insertion must
    pay for an edit opcode plus the literal replacement symbol. Deletes pay an
    opcode but no symbol. This makes repeated copying cheap and literal
    relabeling expensive.
    """

    n, m = len(source), len(target)
    op_bits = math.log2(4)
    delete_bits = op_bits + 1.0
    insert_bits = op_bits + SYMBOL_BITS
    substitute_bits = op_bits + SYMBOL_BITS

    dp = [[0.0] * (m + 1) for _ in range(n + 1)]
    back: list[list[tuple[int, int, str] | None]] = [[None] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        dp[i][0] = dp[i - 1][0] + delete_bits
        back[i][0] = (i - 1, 0, "delete")
    for j in range(1, m + 1):
        dp[0][j] = dp[0][j - 1] + insert_bits
        back[0][j] = (0, j - 1, "insert")

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            options = []
            if source[i - 1] == target[j - 1]:
                options.append((dp[i - 1][j - 1], i - 1, j - 1, "match"))
            else:
                options.append((dp[i - 1][j - 1] + substitute_bits, i - 1, j - 1, "substitute"))
            options.append((dp[i - 1][j] + delete_bits, i - 1, j, "delete"))
            options.append((dp[i][j - 1] + insert_bits, i, j - 1, "insert"))
            cost, prev_i, prev_j, op = min(options, key=lambda item: (item[0], item[3]))
            dp[i][j] = cost
            back[i][j] = (prev_i, prev_j, op)

    counts = Counter()
    i, j = n, m
    while i or j:
        item = back[i][j]
        if item is None:
            raise RuntimeError("edit backtrace failed")
        prev_i, prev_j, op = item
        counts[op] += 1
        i, j = prev_i, prev_j

    return {
        "edit_bits": dp[n][m],
        "matches": counts["match"],
        "substitutes": counts["substitute"],
        "inserts": counts["insert"],
        "deletes": counts["delete"],
    }


def transform_variants(source: str, transform_set: str, orders: dict[str, list[str]]) -> list[dict[str, Any]]:
    variants = [{"name": "copy", "source": source, "parameter": None}]
    if transform_set in {"reverse", "symbol_shift", "reverse_symbol_shift"}:
        variants.append({"name": "reverse", "source": source[::-1], "parameter": None})
    if transform_set in {"symbol_shift", "reverse_symbol_shift"}:
        for order_name, order in orders.items():
            if order_name not in SHIFT_ORDER_NAMES:
                continue
            for shift in range(1, len(order)):
                variants.append(
                    {
                        "name": f"shift:{order_name}",
                        "source": shift_text(source, order, shift),
                        "parameter": shift,
                    }
                )
                if transform_set == "reverse_symbol_shift":
                    variants.append(
                        {
                            "name": f"reverse_shift:{order_name}",
                            "source": shift_text(source[::-1], order, shift),
                            "parameter": shift,
                        }
                    )
    return variants


def best_transition(source: str, target: str, transform_set: str, orders: dict[str, list[str]]) -> dict[str, Any]:
    variants = transform_variants(source, transform_set, orders)
    transform_bits = math.log2(len(variants))
    best = None
    for variant in variants:
        edit = edit_distance_bits(variant["source"], target)
        total = transform_bits + edit["edit_bits"]
        row = {
            "transform": variant["name"],
            "parameter": variant["parameter"],
            "transform_bits": transform_bits,
            "total_bits": total,
            **edit,
        }
        if best is None or (
            row["total_bits"],
            row["substitutes"],
            row["inserts"],
            row["deletes"],
            row["transform"],
            row["parameter"] if row["parameter"] is not None else -1,
        ) < (
            best["total_bits"],
            best["substitutes"],
            best["inserts"],
            best["deletes"],
            best["transform"],
            best["parameter"] if best["parameter"] is not None else -1,
        ):
            best = row
    if best is None:
        raise RuntimeError("no transition variants")
    return best


def evaluate_lines(
    family_name: str,
    lines: list[dict[str, Any]],
    line_order: str,
    transform_set: str,
    orders: dict[str, list[str]],
) -> dict[str, Any]:
    ordered = list(lines)
    if line_order == "reverse":
        ordered = list(reversed(ordered))
    if line_order not in {"forward", "reverse"}:
        raise ValueError(line_order)

    first = ordered[0]
    first_bits = len(first["text"]) * SYMBOL_BITS
    transition_rows = []
    total_bits = first_bits
    for previous, current in zip(ordered, ordered[1:]):
        transition = best_transition(previous["text"], current["text"], transform_set, orders)
        total_bits += transition["total_bits"]
        transition_rows.append(
            {
                "from": previous["id"],
                "to": current["id"],
                "source": previous["text"],
                "target": current["text"],
                **transition,
            }
        )

    total_chars = sum(len(line["text"]) for line in ordered)
    lookup_bits = total_chars * SYMBOL_BITS
    matches = sum(row["matches"] for row in transition_rows)
    edits = sum(row["substitutes"] + row["inserts"] + row["deletes"] for row in transition_rows)
    copied_fraction = matches / max(1, total_chars - len(first["text"]))
    return {
        "family": family_name,
        "line_order": line_order,
        "transform_set": transform_set,
        "line_count": len(ordered),
        "total_chars": total_chars,
        "first_line_id": first["id"],
        "first_line": first["text"],
        "first_line_bits": first_bits,
        "transition_bits": total_bits - first_bits,
        "mdl_bits": total_bits,
        "lookup_bits": lookup_bits,
        "mdl_gain_vs_lookup_bits": lookup_bits - total_bits,
        "lookup_ratio": total_bits / lookup_bits,
        "copied_fraction_after_first": copied_fraction,
        "edit_count": edits,
        "substitute_count": sum(row["substitutes"] for row in transition_rows),
        "insert_count": sum(row["inserts"] for row in transition_rows),
        "delete_count": sum(row["deletes"] for row in transition_rows),
        "transitions": transition_rows,
    }


def search_grid(grid: dict[tuple[int, int], str], labels: list[str], pairs: list[tuple[int, int]]) -> list[dict[str, Any]]:
    families = line_families(grid)
    orders = symbol_orders(labels, pairs)
    rows = []
    for family_name, lines in families.items():
        for line_order in ["forward", "reverse"]:
            for transform_set in ["copy", "reverse", "symbol_shift", "reverse_symbol_shift"]:
                rows.append(evaluate_lines(family_name, lines, line_order, transform_set, orders))
    rows.sort(
        key=lambda row: (
            -row["mdl_gain_vs_lookup_bits"],
            row["lookup_ratio"],
            -row["copied_fraction_after_first"],
            row["family"],
            row["line_order"],
            row["transform_set"],
        )
    )
    return rows


def summarize(values: list[float], observed: float, higher_is_better: bool = True) -> dict[str, float]:
    mean = sum(values) / len(values)
    sd = (sum((value - mean) ** 2 for value in values) / (len(values) - 1)) ** 0.5 if len(values) > 1 else 0.0
    if higher_is_better:
        p = (sum(value >= observed for value in values) + 1) / (len(values) + 1)
        z = (observed - mean) / sd if sd else 0.0
    else:
        p = (sum(value <= observed for value in values) + 1) / (len(values) + 1)
        z = (mean - observed) / sd if sd else 0.0
    return {"observed": observed, "mean": mean, "sd": sd, "min": min(values), "max": max(values), "p": p, "z": z}


def controls(labels: list[str], pairs: list[tuple[int, int]], observed_best: dict[str, Any]) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED)
    best_gains = []
    best_ratios = []
    best_copied = []
    fixed_gains = []
    fixed_key = (observed_best["family"], observed_best["line_order"], observed_best["transform_set"])
    for _ in range(CONTROL_TRIALS):
        shuffled = labels[:]
        rng.shuffle(shuffled)
        grid = dict(zip(pairs, shuffled))
        rows = search_grid(grid, shuffled, pairs)
        best = rows[0]
        best_gains.append(best["mdl_gain_vs_lookup_bits"])
        best_ratios.append(best["lookup_ratio"])
        best_copied.append(best["copied_fraction_after_first"])
        fixed = next(
            row
            for row in rows
            if (row["family"], row["line_order"], row["transform_set"]) == fixed_key
        )
        fixed_gains.append(fixed["mdl_gain_vs_lookup_bits"])

    return {
        "trials": CONTROL_TRIALS,
        "inventory_label_shuffle_best_of_search": {
            "mdl_gain_vs_lookup_bits": summarize(best_gains, observed_best["mdl_gain_vs_lookup_bits"], True),
            "lookup_ratio": summarize(best_ratios, observed_best["lookup_ratio"], False),
            "copied_fraction_after_first": summarize(best_copied, observed_best["copied_fraction_after_first"], True),
        },
        "inventory_label_shuffle_fixed_winner": {
            "key": {
                "family": observed_best["family"],
                "line_order": observed_best["line_order"],
                "transform_set": observed_best["transform_set"],
            },
            "mdl_gain_vs_lookup_bits": summarize(fixed_gains, observed_best["mdl_gain_vs_lookup_bits"], True),
        },
    }


def verdict(best: dict[str, Any], ctrl: dict[str, Any]) -> str:
    best_p = ctrl["inventory_label_shuffle_best_of_search"]["mdl_gain_vs_lookup_bits"]["p"]
    fixed_p = ctrl["inventory_label_shuffle_fixed_winner"]["mdl_gain_vs_lookup_bits"]["p"]
    if best["mdl_gain_vs_lookup_bits"] > 0 and best_p <= 0.01 and fixed_p <= 0.01:
        return "candidate_row_transition_generator"
    if best["mdl_gain_vs_lookup_bits"] > 0 and (best_p <= 0.05 or fixed_p <= 0.05):
        return "weak_row_transition_signal"
    if best["mdl_gain_vs_lookup_bits"] > 0:
        return "positive_edit_compression_control_sensitive"
    return "row_transition_not_promoted"


def make_json_safe(row: dict[str, Any]) -> dict[str, Any]:
    out = dict(row)
    out["transitions"] = row["transitions"][:20]
    return out


def write_report(result: dict[str, Any]) -> None:
    best = result["best"]
    ctrl_best = result["controls"]["inventory_label_shuffle_best_of_search"]
    ctrl_fixed = result["controls"]["inventory_label_shuffle_fixed_winner"]
    lines = [
        "# Row Transition Edit MDL Search",
        "",
        "Generated by `row_transition_edit_mdl_search.py`.",
        "",
        "This pass tests whether a 469 author could have drafted the pair table",
        "line by line, deriving each row/column/diagonal from the previous one",
        "with simple transforms plus charged literal edits. It is mechanical",
        "only and assigns no plaintext.",
        "",
        "## Best Observed Model",
        "",
        "| Family | Order | Transform set | First line | Copied after first | Edits | MDL bits | Lookup ratio | Gain | Verdict |",
        "|---|---|---|---|---:|---:|---:|---:|---:|---|",
        f"| `{best['family']}` | `{best['line_order']}` | `{best['transform_set']}` | `{best['first_line_id']}={best['first_line']}` | {best['copied_fraction_after_first']:.3f} | {best['edit_count']} | {best['mdl_bits']:.2f} | {best['lookup_ratio']:.3f} | {best['mdl_gain_vs_lookup_bits']:.2f} | `{result['verdict']}` |",
        "",
        "## Controls",
        "",
        "| Control lens | Metric | Observed | Mean | Best control | p(good) |",
        "|---|---|---:|---:|---:|---:|",
        f"| best-of-search shuffle | gain bits | {ctrl_best['mdl_gain_vs_lookup_bits']['observed']:.2f} | {ctrl_best['mdl_gain_vs_lookup_bits']['mean']:.2f} | {ctrl_best['mdl_gain_vs_lookup_bits']['max']:.2f} | {ctrl_best['mdl_gain_vs_lookup_bits']['p']:.5f} |",
        f"| best-of-search shuffle | lookup ratio | {ctrl_best['lookup_ratio']['observed']:.3f} | {ctrl_best['lookup_ratio']['mean']:.3f} | {ctrl_best['lookup_ratio']['min']:.3f} | {ctrl_best['lookup_ratio']['p']:.5f} |",
        f"| best-of-search shuffle | copied fraction | {ctrl_best['copied_fraction_after_first']['observed']:.3f} | {ctrl_best['copied_fraction_after_first']['mean']:.3f} | {ctrl_best['copied_fraction_after_first']['max']:.3f} | {ctrl_best['copied_fraction_after_first']['p']:.5f} |",
        f"| fixed winner shuffle | gain bits | {ctrl_fixed['mdl_gain_vs_lookup_bits']['observed']:.2f} | {ctrl_fixed['mdl_gain_vs_lookup_bits']['mean']:.2f} | {ctrl_fixed['mdl_gain_vs_lookup_bits']['max']:.2f} | {ctrl_fixed['mdl_gain_vs_lookup_bits']['p']:.5f} |",
        "",
        "## Top Rows",
        "",
        "| Gain | Ratio | Copied | Edits | Family | Order | Transform set | First line |",
        "|---:|---:|---:|---:|---|---|---|---|",
    ]
    for row in result["top_rows"][:20]:
        lines.append(
            f"| {row['mdl_gain_vs_lookup_bits']:.2f} | {row['lookup_ratio']:.3f} | {row['copied_fraction_after_first']:.3f} | {row['edit_count']} | `{row['family']}` | `{row['line_order']}` | `{row['transform_set']}` | `{row['first_line_id']}={row['first_line']}` |"
        )
    lines += [
        "",
        "## Interpretation",
        "",
        "A promoted line-workflow model would need to save bits versus the raw",
        "55-cell label lookup and beat inventory-preserving label shuffles under",
        "the same best-of-search flexibility. Otherwise the apparent derivation",
        "is just a compact-looking way to pay for literal edits.",
        "",
        f"Translation delta: `{result['translation_delta']}`.",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    formula = load_json(FORMULA_JSON)
    pair_table = formula["pair_table"]
    pairs = natural_pairs()
    grid = build_grid(pair_table)
    labels = [grid[pair] for pair in pairs]

    rows = search_grid(grid, labels, pairs)
    best = rows[0]
    ctrl = controls(labels, pairs, best)
    result = {
        "schema": "row_transition_edit_mdl_results.v1",
        "source": str(FORMULA_JSON.relative_to(ROOT)),
        "random_seed": RANDOM_SEED,
        "control_trials": CONTROL_TRIALS,
        "best": make_json_safe(best),
        "top_rows": [make_json_safe(row) for row in rows[:50]],
        "controls": ctrl,
        "verdict": verdict(best, ctrl),
        "translation_delta": "NONE",
    }
    write_json(OUT_JSON, result)
    write_report(result)
    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(f"verdict={result['verdict']} best={best['family']}/{best['line_order']}/{best['transform_set']} gain={best['mdl_gain_vs_lookup_bits']:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
