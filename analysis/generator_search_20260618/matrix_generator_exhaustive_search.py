#!/usr/bin/env python3
"""Permissive matrix-generator ledger for the 55 unordered pair cells.

This pass intentionally does not stop early on coverage, exception, or p-value
thresholds. It records every generated candidate, scores it, and classifies the
result afterward. The output is mechanical only: no plaintext is inferred.
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
OCC_STREAMS = ROOT / "analysis" / "audit_20260609" / "homophone_channel" / "occ_streams.json"

OUT_JSON = HERE / "matrix_generator_exhaustive_results.json"
OUT_MD = HERE / "matrix_generator_exhaustive_report.md"
OUT_TSV = HERE / "matrix_generator_exhaustive_candidates.tsv"

SIGMA = "*ABCEFILNORSTV"
SEEDS = ("469", "3478", "43153", "34784", "74032", "45331", "1")
LORE_WORDS = {
    "tibia": "TIBIA",
    "telbenna": "TELBENNA",
    "itelbenna": "ITELBENNA",
    "honeminas": "HONEMINAS",
    "tridiag": "TRIDIAG",
    "donina": "DONINA",
    "magic_web": "MAGICWEB",
    "mathemagic": "MATHEMAGIC",
    "great_calculator": "GREATCALCULATOR",
    "subjective_viewer": "SUBJECTIVEVIEWER",
    "mirror": "MIRROR",
    "observer": "OBSERVER",
    "bonelord": "BONELORD",
    "beholder": "BEHOLDER",
    "cipsoft": "CIPSOFT",
    "knightmare": "KNIGHTMARE",
}
RANDOM_SEED = 46920260619
CONTROL_METHOD = "color_permutation_normal_approx_all_candidates"
TOP_MONTE_CARLO_TRIALS = 5000


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def compact_row(row: dict) -> dict:
    drop = {"exception_pairs", "primary_exception_pairs", "predicted_natural"}
    return {key: value for key, value in row.items() if key not in drop}


def write_candidate_tsv(path: Path, rows: list[dict]) -> None:
    columns = [
        "hypothesis_id",
        "pair_order",
        "pair_order_family",
        "symbol_order",
        "symbol_order_source",
        "algorithm",
        "reverse",
        "overlay",
        "cells_hit",
        "primary_cells_hit",
        "exception_count",
        "primary_exception_count",
        "coverage_fraction",
        "primary_coverage_fraction",
        "mdl_cost_bits",
        "lookup_cost_ratio",
        "mdl_gain_vs_lookup_bits",
        "control_p",
        "control_p_monte_carlo_top",
        "uses_lore",
        "uses_holdout",
        "uses_target_label_order",
        "posthoc_override",
        "explains_19_91",
        "explains_missing_39",
        "covers_19_91",
        "covers_pair_39",
        "predicted_19",
        "predicted_39",
        "predicted_prefix",
        "verdict",
    ]
    lines = ["\t".join(columns)]
    for row in rows:
        values = []
        for column in columns:
            value = row.get(column, "")
            if isinstance(value, float):
                values.append(f"{value:.12g}")
            else:
                values.append(str(value))
        lines.append("\t".join(values))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def gamma_bits(value: int) -> int:
    if value <= 1:
        return 1
    return 2 * int(math.floor(math.log2(value))) + 1


def natural_pairs() -> list[str]:
    return [f"{i}{j}" for i in range(10) for j in range(i, 10)]


def pair_key(a: int, b: int) -> str:
    return f"{min(a, b)}{max(a, b)}"


def unique_pair_order(coords: list[tuple[int, int]]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for a, b in coords:
        pair = pair_key(a, b)
        if pair not in seen:
            seen.add(pair)
            out.append(pair)
    for pair in natural_pairs():
        if pair not in seen:
            out.append(pair)
    return out


def spiral_coords(size: int = 10) -> list[tuple[int, int]]:
    coords: list[tuple[int, int]] = []
    top, left, bottom, right = 0, 0, size - 1, size - 1
    while top <= bottom and left <= right:
        for y in range(left, right + 1):
            coords.append((top, y))
        top += 1
        for x in range(top, bottom + 1):
            coords.append((x, right))
        right -= 1
        if top <= bottom:
            for y in range(right, left - 1, -1):
                coords.append((bottom, y))
            bottom -= 1
        if left <= right:
            for x in range(bottom, top - 1, -1):
                coords.append((x, left))
            left += 1
    return coords


def digit_rank(seed: str) -> dict[int, int]:
    order: list[int] = []
    for char in seed:
        digit = int(char)
        if digit not in order:
            order.append(digit)
    for digit in range(10):
        if digit not in order:
            order.append(digit)
    return {digit: idx for idx, digit in enumerate(order)}


def adjacent_seed_pairs(seed: str, skip: int) -> list[str]:
    digits = [int(char) for char in seed]
    if len(digits) == 1:
        digits = digits * 2
    stream = (digits * (80 // len(digits) + 2))[:80]
    coords = [(stream[idx], stream[idx + skip]) for idx in range(len(stream) - skip)]
    return unique_pair_order(coords)


def build_pair_orders(pair_usage: dict[str, int]) -> dict[str, dict]:
    pairs = natural_pairs()
    orders: dict[str, dict] = {}

    def add(order_id: str, pair_list: list[str], **meta) -> None:
        if len(pair_list) != 55 or len(set(pair_list)) != 55:
            raise ValueError(f"bad pair order {order_id}")
        orders[order_id] = {"pairs": pair_list, **meta}

    add("upper_row", pairs, family="matrix_path")
    add("upper_row_rev", list(reversed(pairs)), family="matrix_path")
    add(
        "upper_row_snake",
        [
            pair
            for i in range(10)
            for pair in ([f"{i}{j}" for j in range(i, 10)] if i % 2 == 0 else [f"{i}{j}" for j in range(9, i - 1, -1)])
        ],
        family="matrix_path",
    )
    add("upper_column", [f"{i}{j}" for j in range(10) for i in range(j + 1)], family="matrix_path")
    add(
        "upper_column_snake",
        [
            pair
            for j in range(10)
            for pair in ([f"{i}{j}" for i in range(j + 1)] if j % 2 == 0 else [f"{i}{j}" for i in range(j, -1, -1)])
        ],
        family="matrix_path",
    )
    add("by_sum", sorted(pairs, key=lambda p: (int(p[0]) + int(p[1]), int(p[0]), int(p[1]))), family="matrix_feature")
    add("by_sum_rev", sorted(pairs, key=lambda p: (int(p[0]) + int(p[1]), int(p[0]), int(p[1])), reverse=True), family="matrix_feature")
    add("by_diff", sorted(pairs, key=lambda p: (int(p[1]) - int(p[0]), int(p[0]), int(p[1]))), family="matrix_feature")
    add("by_diff_rev", sorted(pairs, key=lambda p: (int(p[1]) - int(p[0]), int(p[0]), int(p[1])), reverse=True), family="matrix_feature")
    add("by_product", sorted(pairs, key=lambda p: (int(p[0]) * int(p[1]), int(p[0]), int(p[1]))), family="matrix_feature")
    add("by_product_rev", sorted(pairs, key=lambda p: (int(p[0]) * int(p[1]), int(p[0]), int(p[1])), reverse=True), family="matrix_feature")
    add("by_triangular_index", sorted(pairs, key=lambda p: int(p[1]) * (int(p[1]) + 1) // 2 + int(p[0])), family="matrix_feature")
    add("diagonal_then_near", sorted(pairs, key=lambda p: (int(p[1]) - int(p[0]), int(p[0]), int(p[1]))), family="matrix_layer")
    add("far_then_diagonal", sorted(pairs, key=lambda p: (-(int(p[1]) - int(p[0])), int(p[0]), int(p[1]))), family="matrix_layer")
    add(
        "border_then_inner",
        sorted(
            pairs,
            key=lambda p: (
                not (int(p[0]) in {0, 9} or int(p[1]) in {0, 9}),
                abs(int(p[0]) - 4.5) + abs(int(p[1]) - 4.5),
                int(p[0]),
                int(p[1]),
            ),
        ),
        family="matrix_layer",
    )
    add(
        "center_out",
        sorted(pairs, key=lambda p: ((int(p[0]) - 4.5) ** 2 + (int(p[1]) - 4.5) ** 2, int(p[0]), int(p[1]))),
        family="matrix_layer",
    )
    add(
        "corner_out",
        sorted(pairs, key=lambda p: (-((int(p[0]) - 4.5) ** 2 + (int(p[1]) - 4.5) ** 2), int(p[0]), int(p[1]))),
        family="matrix_layer",
    )
    add("spiral_first_unordered", unique_pair_order(spiral_coords()), family="matrix_path")
    add("row_major_10x10_first_unordered", unique_pair_order([(i, j) for i in range(10) for j in range(10)]), family="matrix_path")
    add("column_major_10x10_first_unordered", unique_pair_order([(i, j) for j in range(10) for i in range(10)]), family="matrix_path")
    add(
        "row_snake_10x10_first_unordered",
        unique_pair_order(
            [
                (i, j)
                for i in range(10)
                for j in (range(10) if i % 2 == 0 else range(9, -1, -1))
            ]
        ),
        family="matrix_path",
    )
    add(
        "column_snake_10x10_first_unordered",
        unique_pair_order(
            [
                (i, j)
                for j in range(10)
                for i in (range(10) if j % 2 == 0 else range(9, -1, -1))
            ]
        ),
        family="matrix_path",
    )
    add(
        "full_by_sum_first_unordered",
        unique_pair_order(sorted([(i, j) for i in range(10) for j in range(10)], key=lambda xy: (xy[0] + xy[1], xy[0], xy[1]))),
        family="matrix_path",
    )
    add(
        "code_usage_desc",
        sorted(pairs, key=lambda p: (-pair_usage.get(p, 0), int(p[0]), int(p[1]))),
        family="usage_pressure",
    )
    add(
        "code_usage_asc",
        sorted(pairs, key=lambda p: (pair_usage.get(p, 0), int(p[0]), int(p[1]))),
        family="usage_pressure",
    )
    add("conflict19_first", ["19"] + [p for p in pairs if p != "19"], family="special_anomaly", explicit_19_91_rule=True)
    add("conflict19_last", [p for p in pairs if p != "19"] + ["19"], family="special_anomaly", explicit_19_91_rule=True)
    add("missing39_first", ["39"] + [p for p in pairs if p != "39"], family="special_anomaly", explicit_missing_39_rule=True)
    add("missing39_last", [p for p in pairs if p != "39"] + ["39"], family="special_anomaly", explicit_missing_39_rule=True)
    add(
        "special_19_39_first",
        ["19", "39"] + [p for p in pairs if p not in {"19", "39"}],
        family="special_anomaly",
        explicit_19_91_rule=True,
        explicit_missing_39_rule=True,
    )
    add(
        "special_19_39_last",
        [p for p in pairs if p not in {"19", "39"}] + ["19", "39"],
        family="special_anomaly",
        explicit_19_91_rule=True,
        explicit_missing_39_rule=True,
    )
    for seed in SEEDS:
        rank = digit_rank(seed)
        add(
            f"digit_order_{seed}_sumrank",
            sorted(pairs, key=lambda p: (rank[int(p[0])] + rank[int(p[1])], rank[int(p[0])], rank[int(p[1])])),
            family="lore_seed_rank",
            uses_lore=True,
        )
        add(
            f"digit_order_{seed}_diffrank",
            sorted(pairs, key=lambda p: (abs(rank[int(p[1])] - rank[int(p[0])]), rank[int(p[0])], rank[int(p[1])])),
            family="lore_seed_rank",
            uses_lore=True,
        )
        add(f"adjacent_lore_{seed}_then_natural", adjacent_seed_pairs(seed, 1), family="lore_seed_walk", uses_lore=True)
        add(f"skip_lore_{seed}_then_natural", adjacent_seed_pairs(seed, 2), family="lore_seed_walk", uses_lore=True)
    return orders


def normalize_symbol_order(symbols: list[str]) -> list[str]:
    out: list[str] = []
    for symbol in symbols:
        if symbol in SIGMA and symbol not in out:
            out.append(symbol)
    for symbol in SIGMA:
        if symbol not in out:
            out.append(symbol)
    return out


def corpus_symbol_first_order() -> list[str]:
    occ = load_json(OCC_STREAMS)["occ"]
    events: list[tuple[int, int, str]] = []
    for symbol, rows in occ.items():
        for row in rows:
            events.append((int(row["book"]), int(row["pos"]), symbol))
    seen: set[str] = set()
    out: list[str] = []
    for _book, _pos, symbol in sorted(events):
        if symbol not in seen:
            seen.add(symbol)
            out.append(symbol)
    return out


def build_symbol_orders(pair_counts: Counter[str], corpus_counts: Counter[str], primary_labels: dict[str, str]) -> dict[str, dict]:
    orders: dict[str, dict] = {
        "alpha": {"order": normalize_symbol_order(list(SIGMA)), "source": "alphabet"},
        "alpha_rev": {"order": normalize_symbol_order(list(reversed(SIGMA))), "source": "alphabet"},
        "pair_count_desc": {"order": normalize_symbol_order([s for s, _ in pair_counts.most_common()]), "source": "inventory"},
        "pair_count_asc": {"order": normalize_symbol_order([s for s, _ in sorted(pair_counts.items(), key=lambda item: (item[1], item[0]))]), "source": "inventory"},
        "corpus_freq_desc": {"order": normalize_symbol_order([s for s, _ in corpus_counts.most_common()]), "source": "usage"},
        "corpus_freq_asc": {"order": normalize_symbol_order([s for s, _ in sorted(corpus_counts.items(), key=lambda item: (item[1], item[0]))]), "source": "usage"},
        "first_corpus_symbol": {"order": normalize_symbol_order(corpus_symbol_first_order()), "source": "usage"},
    }
    first_table: list[str] = []
    for pair in natural_pairs():
        symbol = primary_labels[pair]
        if symbol not in first_table:
            first_table.append(symbol)
    orders["pair_table_first_seen"] = {
        "order": normalize_symbol_order(first_table),
        "source": "target_label_order",
        "target_label_leakage": True,
    }
    orders["pair_table_first_seen_rev"] = {
        "order": normalize_symbol_order(list(reversed(first_table))),
        "source": "target_label_order",
        "target_label_leakage": True,
    }
    diagonal_symbols = [primary_labels[f"{i}{i}"] for i in range(10)]
    orders["diagonal_symbols_first"] = {
        "order": normalize_symbol_order(diagonal_symbols),
        "source": "target_label_order",
        "target_label_leakage": True,
    }
    for name, word in LORE_WORDS.items():
        orders[f"lore_{name}"] = {
            "order": normalize_symbol_order(list(word)),
            "source": "lore_word",
            "uses_lore": True,
        }
    return orders


def block_sequence(order: list[str], counts: Counter[str]) -> list[str]:
    out: list[str] = []
    for symbol in order:
        out.extend([symbol] * counts[symbol])
    return out


def round_robin_sequence(order: list[str], counts: Counter[str]) -> list[str]:
    remaining = counts.copy()
    out: list[str] = []
    while sum(remaining.values()) > 0:
        for symbol in order:
            if remaining[symbol] > 0:
                out.append(symbol)
                remaining[symbol] -= 1
    return out


def greedy_balance_sequence(order: list[str], counts: Counter[str]) -> list[str]:
    remaining = counts.copy()
    order_index = {symbol: idx for idx, symbol in enumerate(order)}
    out: list[str] = []
    while sum(remaining.values()) > 0:
        candidates = [symbol for symbol, count in remaining.items() if count > 0]
        candidates.sort(key=lambda symbol: (-remaining[symbol], order_index.get(symbol, 999)))
        if out and len(candidates) > 1 and candidates[0] == out[-1]:
            candidates = candidates[1:] + candidates[:1]
        symbol = candidates[0]
        out.append(symbol)
        remaining[symbol] -= 1
    return out


def low_discrepancy_sequence(order: list[str], counts: Counter[str]) -> list[str]:
    slots: list[tuple[float, int, str]] = []
    order_index = {symbol: idx for idx, symbol in enumerate(order)}
    for symbol in order:
        count = counts[symbol]
        for idx in range(count):
            slots.append(((idx + 0.5) / count, order_index[symbol], symbol))
    return [symbol for _position, _order, symbol in sorted(slots)]


def layered_frequency_sequence(order: list[str], counts: Counter[str]) -> list[str]:
    remaining = counts.copy()
    order_index = {symbol: idx for idx, symbol in enumerate(order)}
    out: list[str] = []
    while sum(remaining.values()) > 0:
        layer = [symbol for symbol in order if remaining[symbol] > 0]
        layer.sort(key=lambda symbol: (remaining[symbol], order_index[symbol]))
        for symbol in layer:
            out.append(symbol)
            remaining[symbol] -= 1
    return out


def seed_skip_sequence(order: list[str], counts: Counter[str], seed: str) -> list[str]:
    remaining = counts.copy()
    out: list[str] = []
    index = 0
    digits = [int(char) for char in seed]
    step_index = 0
    while sum(remaining.values()) > 0:
        index = (index + digits[step_index % len(digits)] + 1) % len(order)
        step_index += 1
        for offset in range(len(order)):
            symbol = order[(index + offset) % len(order)]
            if remaining[symbol] > 0:
                out.append(symbol)
                remaining[symbol] -= 1
                index = (index + offset) % len(order)
                break
    return out


def build_sequences(order: list[str], counts: Counter[str]) -> dict[str, dict]:
    sequences = {
        "block": {"sequence": block_sequence(order, counts)},
        "round_robin": {"sequence": round_robin_sequence(order, counts)},
        "greedy_balance": {"sequence": greedy_balance_sequence(order, counts)},
        "low_discrepancy": {"sequence": low_discrepancy_sequence(order, counts)},
        "layered_frequency": {"sequence": layered_frequency_sequence(order, counts)},
    }
    for seed in SEEDS:
        sequences[f"seed_skip_{seed}"] = {
            "sequence": seed_skip_sequence(order, counts, seed),
            "uses_lore": True,
        }
    return sequences


def acceptable_pair_symbols(pair_table: dict, pair: str) -> set[str]:
    row = pair_table[pair]
    return set(row["symbols"])


def primary_pair_symbol(pair_table: dict, pair: str) -> str:
    row = pair_table[pair]
    if row["status"] == "pure":
        return row["symbol_if_pure"]
    return sorted(row["symbols"])[0]


def build_pair_usage(formula: dict) -> dict[str, int]:
    usage = Counter()
    for code, count in formula.get("code_counts", {}).items():
        usage["".join(sorted(code))] += int(count)
    return dict(usage)


def build_corpus_symbol_counts(formula: dict) -> Counter[str]:
    counts: Counter[str] = Counter()
    for code, count in formula.get("code_counts", {}).items():
        symbol = formula["code_to_symbol"].get(code)
        if symbol:
            counts[symbol] += int(count)
    return counts


def overlay_defs(primary_labels: dict[str, str]) -> list[dict]:
    diag_e = {f"{i}{i}": "E" for i in range(10)}
    pair_19_symbols = ["I", "N"]
    return [
        {"id": "none", "forced": {}, "rule_bits": 0},
        {
            "id": "force_19_primary",
            "forced": {"19": primary_labels["19"]},
            "rule_bits": 12,
            "explicit_19_91_rule": True,
            "posthoc_override": True,
        },
        {
            "id": "force_19_conflict_alt",
            "forced": {"19": next(symbol for symbol in pair_19_symbols if symbol != primary_labels["19"])},
            "rule_bits": 12,
            "explicit_19_91_rule": True,
            "posthoc_override": True,
        },
        {
            "id": "force_missing39_observed",
            "forced": {"39": primary_labels["39"]},
            "rule_bits": 12,
            "explicit_missing_39_rule": True,
            "posthoc_override": True,
        },
        {
            "id": "force_19_and_39_observed",
            "forced": {"19": primary_labels["19"], "39": primary_labels["39"]},
            "rule_bits": 18,
            "explicit_19_91_rule": True,
            "explicit_missing_39_rule": True,
            "posthoc_override": True,
        },
        {
            "id": "force_33_66_observed",
            "forced": {"33": primary_labels["33"], "66": primary_labels["66"]},
            "rule_bits": 18,
            "explicit_tape_exception_rule": True,
            "posthoc_override": True,
        },
        {
            "id": "force_33_66_19_39_observed",
            "forced": {"33": primary_labels["33"], "66": primary_labels["66"], "19": primary_labels["19"], "39": primary_labels["39"]},
            "rule_bits": 28,
            "explicit_19_91_rule": True,
            "explicit_missing_39_rule": True,
            "explicit_tape_exception_rule": True,
            "posthoc_override": True,
        },
        {
            "id": "diagonal_to_E",
            "forced": diag_e,
            "rule_bits": 10,
            "explicit_diagonal_rule": True,
        },
    ]


def rough_mdl_bits(
    exception_count: int,
    pair_order_count: int,
    symbol_order_count: int,
    algorithm_count: int,
    pair_meta: dict,
    symbol_meta: dict,
    sequence_meta: dict,
    overlay: dict,
    reverse: bool,
) -> float:
    lookup_cell_bits = math.log2(55) + math.log2(len(SIGMA))
    rule_bits = 12.0
    rule_bits += math.log2(pair_order_count)
    rule_bits += math.log2(symbol_order_count)
    rule_bits += math.log2(algorithm_count)
    rule_bits += 1.0 if reverse else 0.0
    rule_bits += overlay.get("rule_bits", 0)
    if pair_meta.get("uses_lore") or symbol_meta.get("uses_lore") or sequence_meta.get("uses_lore"):
        rule_bits += 4.0
    if pair_meta.get("explicit_19_91_rule") or overlay.get("explicit_19_91_rule"):
        rule_bits += 4.0
    if pair_meta.get("explicit_missing_39_rule") or overlay.get("explicit_missing_39_rule"):
        rule_bits += 4.0
    if symbol_meta.get("target_label_leakage"):
        rule_bits += 70.0
    if overlay.get("posthoc_override"):
        rule_bits += 8.0 + gamma_bits(max(1, len(overlay["forced"])))
    return rule_bits + exception_count * lookup_cell_bits


def classify(row: dict) -> str:
    if row["uses_target_label_order"] or row["lookup_cost_ratio"] >= 1.0:
        return "lookup_disguise"
    if row["control_p"] <= 0.01 and row["coverage_fraction"] >= 0.65 and row["mdl_gain_vs_lookup_bits"] > 0:
        return "candidate_matrix_generator"
    if row["control_p"] <= 0.05 or row["explains_19_91"] or row["explains_missing_39"] or row["covers_19_91"] is False:
        return "weak_matrix_signal"
    return "not_enough_evidence"


def control_cache_builder(observed_primary_labels: list[str]):
    cache: dict[tuple[int, ...], dict] = {}
    observed_counts = Counter(observed_primary_labels)
    total = len(observed_primary_labels)

    def get(predicted_labels: list[str]) -> dict:
        key = tuple(Counter(predicted_labels).get(symbol, 0) for symbol in SIGMA)
        if key not in cache:
            pred_counts = {symbol: count for symbol, count in zip(SIGMA, key)}
            q = {symbol: observed_counts[symbol] / total for symbol in SIGMA}
            mean = sum(pred_counts[symbol] * observed_counts[symbol] / total for symbol in SIGMA)
            variance = sum(pred_counts[symbol] * q[symbol] * (1.0 - q[symbol]) for symbol in SIGMA)
            for idx, left in enumerate(SIGMA):
                left_count = pred_counts[left]
                if left_count >= 2:
                    both = observed_counts[left] * (observed_counts[left] - 1) / (total * (total - 1))
                    variance += left_count * (left_count - 1) * (both - q[left] * q[left])
                for right in SIGMA[idx + 1 :]:
                    right_count = pred_counts[right]
                    if left_count and right_count:
                        both = observed_counts[left] * observed_counts[right] / (total * (total - 1))
                        variance += 2 * left_count * right_count * (both - q[left] * q[right])
            sd = math.sqrt(max(variance, 0.0))
            cache[key] = {"mean": mean, "sd": sd}
        return cache[key]

    def p_value(predicted_labels: list[str], observed_score: int) -> tuple[float, float, float]:
        dist = get(predicted_labels)
        mean = dist["mean"]
        sd = dist["sd"]
        if sd == 0:
            p = 1.0 if observed_score <= mean else 0.0
        else:
            z = (observed_score - 0.5 - mean) / sd
            p = 0.5 * math.erfc(z / math.sqrt(2.0))
        return p, dist["mean"], dist["sd"]

    p_value.cache = cache  # type: ignore[attr-defined]
    return p_value


def monte_carlo_p(predicted_labels: list[str], observed_labels: list[str], observed_score: int, trials: int) -> float:
    rng = random.Random(RANDOM_SEED + observed_score + sum(ord(ch) for ch in "".join(predicted_labels)))
    ge = 0
    for _trial in range(trials):
        shuffled = observed_labels[:]
        rng.shuffle(shuffled)
        score = sum(1 for predicted, observed in zip(predicted_labels, shuffled) if predicted == observed)
        if score >= observed_score:
            ge += 1
    return (ge + 1) / (trials + 1)


def score_candidate(
    pair_table: dict,
    primary_labels: dict[str, str],
    candidate_pairs: list[str],
    candidate_labels: list[str],
) -> dict:
    predicted_by_pair = dict(zip(candidate_pairs, candidate_labels))
    exceptions = []
    primary_exceptions = []
    for pair in natural_pairs():
        predicted = predicted_by_pair[pair]
        acceptable = acceptable_pair_symbols(pair_table, pair)
        if predicted not in acceptable:
            exceptions.append(pair)
        if predicted != primary_labels[pair]:
            primary_exceptions.append(pair)
    return {
        "cells_hit": 55 - len(exceptions),
        "primary_cells_hit": 55 - len(primary_exceptions),
        "exception_pairs": exceptions,
        "primary_exception_pairs": primary_exceptions,
        "predicted_natural": "".join(predicted_by_pair[pair] for pair in natural_pairs()),
        "covers_19_91": predicted_by_pair["19"] in acceptable_pair_symbols(pair_table, "19"),
        "covers_pair_39": predicted_by_pair["39"] in acceptable_pair_symbols(pair_table, "39"),
        "predicted_19": predicted_by_pair["19"],
        "predicted_39": predicted_by_pair["39"],
    }


def main() -> int:
    formula = load_json(FORMULA_JSON)
    pair_table = formula["pair_table"]
    pairs = natural_pairs()
    primary_labels = {pair: primary_pair_symbol(pair_table, pair) for pair in pairs}
    pair_counts = Counter(primary_labels.values())
    corpus_counts = build_corpus_symbol_counts(formula)
    pair_usage = build_pair_usage(formula)
    pair_orders = build_pair_orders(pair_usage)
    symbol_orders = build_symbol_orders(pair_counts, corpus_counts, primary_labels)
    overlays = overlay_defs(primary_labels)

    sequence_count = 5 + len(SEEDS)
    lookup_bits = 55 * math.log2(len(SIGMA))
    p_value = control_cache_builder([primary_labels[pair] for pair in pairs])

    rows: list[dict] = []
    for pair_order_id, pair_meta in pair_orders.items():
        candidate_pairs = pair_meta["pairs"]
        for symbol_order_id, symbol_meta in symbol_orders.items():
            sequences = build_sequences(symbol_meta["order"], pair_counts)
            for algorithm_id, sequence_meta in sequences.items():
                base_sequence = sequence_meta["sequence"]
                if len(base_sequence) != 55:
                    raise ValueError((symbol_order_id, algorithm_id, len(base_sequence)))
                for reverse in (False, True):
                    sequence = list(reversed(base_sequence)) if reverse else base_sequence
                    for overlay in overlays:
                        predicted = sequence[:]
                        pair_index = {pair: idx for idx, pair in enumerate(candidate_pairs)}
                        for pair, forced_symbol in overlay["forced"].items():
                            predicted[pair_index[pair]] = forced_symbol
                        score = score_candidate(pair_table, primary_labels, candidate_pairs, predicted)
                        predicted_natural_labels = list(score["predicted_natural"])
                        control_p, control_mean, control_sd = p_value(predicted_natural_labels, score["primary_cells_hit"])
                        mdl_bits = rough_mdl_bits(
                            exception_count=len(score["exception_pairs"]),
                            pair_order_count=len(pair_orders),
                            symbol_order_count=len(symbol_orders),
                            algorithm_count=sequence_count,
                            pair_meta=pair_meta,
                            symbol_meta=symbol_meta,
                            sequence_meta=sequence_meta,
                            overlay=overlay,
                            reverse=reverse,
                        )
                        row = {
                            "hypothesis_id": f"{pair_order_id}::{symbol_order_id}::{algorithm_id}::rev{int(reverse)}::{overlay['id']}",
                            "pair_order": pair_order_id,
                            "pair_order_family": pair_meta.get("family", "unknown"),
                            "symbol_order": symbol_order_id,
                            "symbol_order_source": symbol_meta.get("source", "unknown"),
                            "algorithm": algorithm_id,
                            "reverse": reverse,
                            "overlay": overlay["id"],
                            "cells_hit": score["cells_hit"],
                            "coverage_fraction": score["cells_hit"] / 55,
                            "primary_cells_hit": score["primary_cells_hit"],
                            "primary_coverage_fraction": score["primary_cells_hit"] / 55,
                            "exception_count": len(score["exception_pairs"]),
                            "exception_pairs": score["exception_pairs"],
                            "primary_exception_count": len(score["primary_exception_pairs"]),
                            "predicted_natural": score["predicted_natural"],
                            "predicted_prefix": score["predicted_natural"][:24],
                            "mdl_cost_bits": mdl_bits,
                            "lookup_cost_bits": lookup_bits,
                            "mdl_gain_vs_lookup_bits": lookup_bits - mdl_bits,
                            "lookup_cost_ratio": mdl_bits / lookup_bits,
                            "control_p": control_p,
                            "control_mean_hits": control_mean,
                            "control_sd_hits": control_sd,
                            "uses_lore": bool(pair_meta.get("uses_lore") or symbol_meta.get("uses_lore") or sequence_meta.get("uses_lore")),
                            "uses_holdout": False,
                            "uses_target_label_order": bool(symbol_meta.get("target_label_leakage")),
                            "posthoc_override": bool(overlay.get("posthoc_override")),
                            "explains_19_91": bool(pair_meta.get("explicit_19_91_rule") or overlay.get("explicit_19_91_rule")),
                            "explains_missing_39": bool(pair_meta.get("explicit_missing_39_rule") or overlay.get("explicit_missing_39_rule")),
                            "covers_19_91": score["covers_19_91"],
                            "covers_pair_39": score["covers_pair_39"],
                            "predicted_19": score["predicted_19"],
                            "predicted_39": score["predicted_39"],
                        }
                        row["verdict"] = classify(row)
                        rows.append(row)

    rows.sort(
        key=lambda row: (
            -row["cells_hit"],
            -row["primary_cells_hit"],
            row["lookup_cost_ratio"],
            row["control_p"],
            row["hypothesis_id"],
        )
    )
    best_by_mdl = sorted(rows, key=lambda row: (-row["mdl_gain_vs_lookup_bits"], -row["cells_hit"], row["hypothesis_id"]))[0]
    best_special = sorted(
        [row for row in rows if row["explains_19_91"] or row["explains_missing_39"]],
        key=lambda row: (-row["cells_hit"], row["lookup_cost_ratio"], row["hypothesis_id"]),
    )[:25]
    observed_primary_list = [primary_labels[pair] for pair in pairs]
    mc_seen: set[str] = set()
    for row in rows[:25] + best_special[:25]:
        if row["hypothesis_id"] in mc_seen:
            continue
        mc_seen.add(row["hypothesis_id"])
        row["control_p_monte_carlo_top"] = monte_carlo_p(
            list(row["predicted_natural"]),
            observed_primary_list,
            row["primary_cells_hit"],
            TOP_MONTE_CARLO_TRIALS,
        )
    class_counts = Counter(row["verdict"] for row in rows)
    family_best = {}
    for row in rows:
        family_best.setdefault(row["pair_order_family"], row)
    write_candidate_tsv(OUT_TSV, rows)

    promoted = [row for row in rows if row["verdict"] == "candidate_matrix_generator"]
    overall_verdict = "mechanical_partial_not_final"
    if promoted:
        overall_verdict = "candidate_matrix_generator_found_but_not_semantic"
    elif rows[0]["cells_hit"] < 45:
        overall_verdict = "mechanical_partial_not_final_no_exact_matrix_formula"

    result = {
        "schema": "matrix_generator_exhaustive_results.v1",
        "created_at": "2026-06-19",
        "translation_delta": "NONE",
        "exploration_policy": "no_hard_gates_thresholds_are_descriptive_only",
        "state": "mechanical_partial_not_final",
        "candidate_count": len(rows),
        "pair_order_count": len(pair_orders),
        "symbol_order_count": len(symbol_orders),
        "algorithm_count": sequence_count,
        "overlay_count": len(overlays),
        "control_method": CONTROL_METHOD,
        "top_monte_carlo_trials": TOP_MONTE_CARLO_TRIALS,
        "control_count_signatures": len(p_value.cache),  # type: ignore[attr-defined]
        "observed_primary_label_string": "".join(primary_labels[pair] for pair in pairs),
        "pair_counts": dict(sorted(pair_counts.items())),
        "lookup_cost_bits": lookup_bits,
        "best_by_cells": rows[0],
        "best_by_mdl": best_by_mdl,
        "best_special_19_39": best_special,
        "family_best": {key: compact_row(value) for key, value in family_best.items()},
        "classification_counts": dict(sorted(class_counts.items())),
        "overall_verdict": overall_verdict,
        "candidate_ledger_tsv": OUT_TSV.name,
        "top_candidates": [compact_row(row) for row in rows[:200]],
    }
    write_json(OUT_JSON, result)

    lines = [
        "# Matrix Generator Exhaustive Search",
        "",
        "Generated by `matrix_generator_exhaustive_search.py`.",
        "",
        "This is a permissive ledger. Coverage, exceptions, MDL, p-values, and",
        "special-anomaly handling are recorded for every candidate; none of those",
        "numbers are used as an exploration stop condition. They only classify",
        "confidence afterward.",
        "",
        "Translation delta: `NONE`.",
        "",
        "## Search Breadth",
        "",
        f"- Pair orders: `{len(pair_orders)}`.",
        f"- Symbol orders: `{len(symbol_orders)}`.",
        f"- Sequence algorithms: `{sequence_count}`.",
        f"- Overlays/compositions: `{len(overlays)}`.",
        f"- Total candidates recorded: `{len(rows)}`.",
        f"- Full compact candidate ledger: `{OUT_TSV.name}`.",
        f"- Control method for all candidates: `{CONTROL_METHOD}`.",
        f"- Monte Carlo trials on top/special rows: `{TOP_MONTE_CARLO_TRIALS}`.",
        "",
        "## Best By Coverage",
        "",
        "| Hits | Primary hits | MDL/lookup | Control p | MC p | Pair order | Symbol order | Algorithm | Overlay | Class |",
        "|---:|---:|---:|---:|---:|---|---|---|---|---|",
    ]
    for row in rows[:20]:
        lines.append(
            f"| {row['cells_hit']}/55 | {row['primary_cells_hit']}/55 | {row['lookup_cost_ratio']:.3f} | {row['control_p']:.4f} | "
            f"{row.get('control_p_monte_carlo_top', float('nan')):.4f} | "
            f"`{row['pair_order']}` | `{row['symbol_order']}` | `{row['algorithm']}` | `{row['overlay']}` | `{row['verdict']}` |"
        )
    lines.extend(
        [
            "",
            "## Best Special-Anomaly Rows",
            "",
            "| Hits | 19/91 rule | missing 39 rule | Covers 19 | Covers 39 | MDL/lookup | Candidate | Class |",
            "|---:|---|---|---|---|---:|---|---|",
        ]
    )
    for row in best_special[:12]:
        lines.append(
            f"| {row['cells_hit']}/55 | `{row['explains_19_91']}` | `{row['explains_missing_39']}` | "
            f"`{row['covers_19_91']}` | `{row['covers_pair_39']}` | {row['lookup_cost_ratio']:.3f} | "
            f"`{row['hypothesis_id']}` | `{row['verdict']}` |"
        )
    lines.extend(
        [
            "",
            "## Classification Counts",
            "",
            "| Class | Count |",
            "|---|---:|",
        ]
    )
    for verdict, count in sorted(class_counts.items()):
        lines.append(f"| `{verdict}` | {count} |")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"Current overall verdict: `{overall_verdict}`.",
            "",
            f"The best row reaches `{rows[0]['cells_hit']}/55` acceptable pair-cell hits",
            f"(`{rows[0]['primary_cells_hit']}/55` against the primary conflict choice).",
            "This is a matrix-placement clue ledger, not a recovered original formula.",
            "Rows that explicitly touch `{19,91}` or missing ordered code `39` are kept",
            "even when they are weak, because those anomalies may matter in later",
            "compositions. Rows marked `lookup_disguise` are still recorded; the label",
            "means their exact repair cost is at least table-like under this rough MDL.",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT_JSON.relative_to(HERE)}")
    print(f"wrote {OUT_MD.relative_to(HERE)}")
    print(f"wrote {OUT_TSV.relative_to(HERE)}")
    print(
        "candidates={} best={}/55 primary={}/55 verdict={}".format(
            len(rows),
            rows[0]["cells_hit"],
            rows[0]["primary_cells_hit"],
            overall_verdict,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
