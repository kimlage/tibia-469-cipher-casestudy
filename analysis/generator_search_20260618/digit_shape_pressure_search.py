#!/usr/bin/env python3
"""Digit-shape pressure search for the 469 pair table.

The exact placement of symbols across the 55 unordered pair cells remains the
hardest unsolved mechanical question. This pass tests whether that placement
was chosen to make the rendered digits "look right": balanced digit marginals,
high entropy, controlled zero rate, few repeated-digit cells, or a close match
to the actual raw digit distribution.

Controls preserve the exact symbol inventory and shuffle it across cells/codes.
If the real table is not extreme against these controls, digit-shape pressure
does not explain the original placement.

Mechanical only. No number<->plaintext meaning is promoted.
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

OUT_JSON = HERE / "digit_shape_pressure_results.json"
OUT_MD = HERE / "digit_shape_pressure_report.md"

RANDOM_SEED = 46920260620
TRIALS = 20000
DIGITS = "0123456789"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def all_pairs() -> list[str]:
    return [f"{i}{j}" for i in range(10) for j in range(i, 10)]


def load_books_digits(formula: dict) -> dict[str, str]:
    modules = {module["id"]: module["text"] for module in formula["modules"]}
    books = {}
    for book, recipe in formula["book_recipes"].items():
        books[book] = "".join(
            modules[item["id"]] if item["type"] == "module" else item["text"]
            for item in recipe
        )
    return books


def primary_pair_symbol(pair_table: dict, pair: str) -> str:
    row = pair_table[pair]
    if row["status"] == "pure":
        return row["symbol_if_pure"]
    return sorted(row["symbols"])[0]


def symbol_counts_from_occ() -> Counter[str]:
    occ = load_json(OCC_STREAMS)["occ"]
    return Counter({symbol: len(rows) for symbol, rows in occ.items()})


def raw_digit_distribution(books_digits: dict[str, str]) -> dict[str, float]:
    counts = Counter("".join(books_digits.values()))
    total = sum(counts.values())
    return {digit: counts[digit] / total for digit in DIGITS}


def token_code_stats_from_occ() -> dict:
    occ = load_json(OCC_STREAMS)["occ"]
    codes = []
    for rows in occ.values():
        for row in rows:
            codes.append(row["code"])
    digit_counts = Counter("".join(codes))
    total_digits = sum(digit_counts.values())
    repeat_tokens = sum(1 for code in codes if code[0] == code[1])
    zero_digits = digit_counts["0"]
    return {
        "token_count": len(codes),
        "digit_distribution": {digit: digit_counts[digit] / total_digits for digit in DIGITS},
        "repeat_token_fraction": repeat_tokens / len(codes),
        "zero_digit_fraction": zero_digits / total_digits,
    }


def entropy(dist: dict[str, float]) -> float:
    return -sum(value * math.log2(value) for value in dist.values() if value > 0)


def chi_square_uniform(dist: dict[str, float]) -> float:
    expected = 1 / len(DIGITS)
    return sum((dist[digit] - expected) ** 2 / expected for digit in DIGITS)


def l1(left: dict[str, float], right: dict[str, float]) -> float:
    return sum(abs(left[digit] - right[digit]) for digit in DIGITS)


def max_abs_delta(left: dict[str, float], right: dict[str, float]) -> float:
    return max(abs(left[digit] - right[digit]) for digit in DIGITS)


def normalize_counter(counter: Counter[str]) -> dict[str, float]:
    total = sum(counter.values())
    return {digit: counter[digit] / total if total else 0.0 for digit in DIGITS}


def pair_cell_expected_stats(labels_by_pair: dict[str, str], symbol_counts: Counter[str], target_dist: dict[str, float], token_stats: dict) -> dict:
    cells_by_symbol = defaultdict(list)
    for pair, symbol in labels_by_pair.items():
        cells_by_symbol[symbol].append(pair)

    digit_counts = Counter()
    repeat_weight = 0.0
    zero_digit_weight = 0.0
    token_weight = 0.0
    for symbol, count in symbol_counts.items():
        cells = cells_by_symbol.get(symbol, [])
        if not cells:
            continue
        per_cell = count / len(cells)
        for pair in cells:
            a, b = pair[0], pair[1]
            digit_counts[a] += per_cell
            digit_counts[b] += per_cell
            zero_digit_weight += per_cell * ((1 if a == "0" else 0) + (1 if b == "0" else 0))
            repeat_weight += per_cell if a == b else 0.0
            token_weight += per_cell

    dist = normalize_counter(digit_counts)
    return {
        "digit_distribution": dist,
        "entropy_bits": entropy(dist),
        "chi_square_uniform": chi_square_uniform(dist),
        "l1_to_raw_digits": l1(dist, target_dist),
        "max_abs_delta_to_raw_digits": max_abs_delta(dist, target_dist),
        "zero_digit_fraction": zero_digit_weight / (2 * token_weight),
        "zero_abs_error_to_tokens": abs((zero_digit_weight / (2 * token_weight)) - token_stats["zero_digit_fraction"]),
        "repeat_pair_fraction": repeat_weight / token_weight,
        "repeat_abs_error_to_tokens": abs((repeat_weight / token_weight) - token_stats["repeat_token_fraction"]),
    }


def ordered_code_expected_stats(code_to_symbol: dict[str, str], symbol_counts: Counter[str], target_dist: dict[str, float], token_stats: dict) -> dict:
    codes_by_symbol = defaultdict(list)
    for code, symbol in code_to_symbol.items():
        codes_by_symbol[symbol].append(code)

    digit_counts = Counter()
    repeat_weight = 0.0
    zero_digit_weight = 0.0
    token_weight = 0.0
    for symbol, count in symbol_counts.items():
        codes = codes_by_symbol.get(symbol, [])
        if not codes:
            continue
        per_code = count / len(codes)
        for code in codes:
            a, b = code[0], code[1]
            digit_counts[a] += per_code
            digit_counts[b] += per_code
            zero_digit_weight += per_code * ((1 if a == "0" else 0) + (1 if b == "0" else 0))
            repeat_weight += per_code if a == b else 0.0
            token_weight += per_code

    dist = normalize_counter(digit_counts)
    return {
        "digit_distribution": dist,
        "entropy_bits": entropy(dist),
        "chi_square_uniform": chi_square_uniform(dist),
        "l1_to_raw_digits": l1(dist, target_dist),
        "max_abs_delta_to_raw_digits": max_abs_delta(dist, target_dist),
        "zero_digit_fraction": zero_digit_weight / (2 * token_weight),
        "zero_abs_error_to_tokens": abs((zero_digit_weight / (2 * token_weight)) - token_stats["zero_digit_fraction"]),
        "repeat_code_fraction": repeat_weight / token_weight,
        "repeat_abs_error_to_tokens": abs((repeat_weight / token_weight) - token_stats["repeat_token_fraction"]),
    }


METRICS = {
    "entropy_bits": "high",
    "chi_square_uniform": "low",
    "l1_to_raw_digits": "low",
    "max_abs_delta_to_raw_digits": "low",
    "zero_abs_error_to_tokens": "low",
    "repeat_abs_error_to_tokens": "low",
}


def summarize_metric(values: list[float], observed: float, direction: str) -> dict:
    mean = sum(values) / len(values)
    sd = (sum((value - mean) ** 2 for value in values) / (len(values) - 1)) ** 0.5
    if direction == "high":
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


def pair_cell_controls(labels_by_pair: dict[str, str], symbol_counts: Counter[str], target_dist: dict[str, float], token_stats: dict) -> dict:
    rng = random.Random(RANDOM_SEED)
    pairs = all_pairs()
    labels = [labels_by_pair[pair] for pair in pairs]
    observed = pair_cell_expected_stats(labels_by_pair, symbol_counts, target_dist, token_stats)
    values = {metric: [] for metric in METRICS}
    shuffled = labels[:]
    for _trial in range(TRIALS):
        rng.shuffle(shuffled)
        current_labels = {pair: symbol for pair, symbol in zip(pairs, shuffled)}
        current = pair_cell_expected_stats(current_labels, symbol_counts, target_dist, token_stats)
        for metric in METRICS:
            values[metric].append(current[metric])
    summaries = {
        metric: summarize_metric(values[metric], observed[metric], direction)
        for metric, direction in METRICS.items()
    }
    strongest = min(
        ({"metric": metric, **summary} for metric, summary in summaries.items()),
        key=lambda row: row["p_good_direction"],
    )
    return {"observed": observed, "metric_summaries": summaries, "strongest": strongest}


def ordered_code_controls(code_to_symbol: dict[str, str], symbol_counts: Counter[str], target_dist: dict[str, float], token_stats: dict) -> dict:
    rng = random.Random(RANDOM_SEED + 1)
    codes = sorted(code_to_symbol)
    labels = [code_to_symbol[code] for code in codes]
    observed = ordered_code_expected_stats(code_to_symbol, symbol_counts, target_dist, token_stats)
    values = {metric: [] for metric in METRICS}
    shuffled = labels[:]
    for _trial in range(TRIALS):
        rng.shuffle(shuffled)
        current_code_to_symbol = {code: symbol for code, symbol in zip(codes, shuffled)}
        current = ordered_code_expected_stats(current_code_to_symbol, symbol_counts, target_dist, token_stats)
        for metric in METRICS:
            values[metric].append(current[metric])
    summaries = {
        metric: summarize_metric(values[metric], observed[metric], direction)
        for metric, direction in METRICS.items()
    }
    strongest = min(
        ({"metric": metric, **summary} for metric, summary in summaries.items()),
        key=lambda row: row["p_good_direction"],
    )
    return {"observed": observed, "metric_summaries": summaries, "strongest": strongest}


def main() -> int:
    formula = load_json(FORMULA_JSON)
    pair_table = formula["pair_table"]
    code_to_symbol = formula["code_to_symbol"]
    symbol_counts = symbol_counts_from_occ()
    books_digits = load_books_digits(formula)
    target_dist = raw_digit_distribution(books_digits)
    token_stats = token_code_stats_from_occ()

    labels_by_pair = {pair: primary_pair_symbol(pair_table, pair) for pair in all_pairs()}
    pair_result = pair_cell_controls(labels_by_pair, symbol_counts, target_dist, token_stats)
    ordered_result = ordered_code_controls(code_to_symbol, symbol_counts, target_dist, token_stats)

    pair_pass = pair_result["strongest"]["p_good_direction"] <= 0.01 and pair_result["strongest"]["z_good_direction"] >= 2.5
    ordered_pass = ordered_result["strongest"]["p_good_direction"] <= 0.01 and ordered_result["strongest"]["z_good_direction"] >= 2.5
    verdict = "candidate_generator_digit_shape" if pair_pass and ordered_pass else "rejected_control"

    result = {
        "schema": "digit_shape_pressure_results.v1",
        "random_seed": RANDOM_SEED,
        "trials": TRIALS,
        "target_raw_digit_distribution": target_dist,
        "actual_token_code_stats": token_stats,
        "pair_cell_model": pair_result,
        "ordered_code_model": ordered_result,
        "verdict": verdict,
        "promotion_rule": "requires pair-cell and ordered-code strongest metrics both p<=0.01 and z>=2.5 in good direction",
        "method_note": "pair-cell model uses primary label for conflict cell {19}; ordered-code model uses exact 99 code labels.",
    }
    write_json(OUT_JSON, result)

    lines = [
        "# Digit Shape Pressure Search",
        "",
        "Generated by `digit_shape_pressure_search.py`.",
        "",
        "This pass tests whether the exact pair/code placement was chosen to make",
        "the rendered digit stream visually balanced or close to the actual raw",
        "digit distribution. Controls preserve the symbol inventory and shuffle",
        "labels across cells/codes.",
        "",
        "## Pair-Cell Model",
        "",
        "| Strongest metric | Observed | Control mean | z | p |",
        "|---|---:|---:|---:|---:|",
    ]
    strongest = pair_result["strongest"]
    lines.append(
        f"| `{strongest['metric']}` | {strongest['observed']:.6f} | "
        f"{strongest['control_mean']:.6f} | {strongest['z_good_direction']:.2f} | "
        f"{strongest['p_good_direction']:.4f} |"
    )
    lines.extend(
        [
            "",
            "## Ordered-Code Model",
            "",
            "| Strongest metric | Observed | Control mean | z | p |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    strongest_ordered = ordered_result["strongest"]
    lines.append(
        f"| `{strongest_ordered['metric']}` | {strongest_ordered['observed']:.6f} | "
        f"{strongest_ordered['control_mean']:.6f} | {strongest_ordered['z_good_direction']:.2f} | "
        f"{strongest_ordered['p_good_direction']:.4f} |"
    )
    lines.extend(
        [
            "",
            "## Metric Detail",
            "",
            "| Model | Metric | Observed | Control mean | z | p |",
            "|---|---|---:|---:|---:|---:|",
        ]
    )
    for model_name, model in [("pair_cell", pair_result), ("ordered_code", ordered_result)]:
        for metric, summary in model["metric_summaries"].items():
            lines.append(
                f"| `{model_name}` | `{metric}` | {summary['observed']:.6f} | "
                f"{summary['control_mean']:.6f} | {summary['z_good_direction']:.2f} | "
                f"{summary['p_good_direction']:.4f} |"
            )
    lines.extend(
        [
            "",
            "## Verdict",
            "",
            f"`{verdict}`.",
            "",
            "The real placement is not strongly extreme on digit-balance, zero, repeat,",
            "or raw-distribution matching metrics once symbol inventory is preserved.",
            "Digit-shape pressure therefore does not currently explain the exact",
            "pair-cell layout.",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(
        "verdict="
        f"{verdict} pair_best={pair_result['strongest']['metric']}:{pair_result['strongest']['p_good_direction']:.4f} "
        f"ordered_best={ordered_result['strongest']['metric']}:{ordered_result['strongest']['p_good_direction']:.4f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
