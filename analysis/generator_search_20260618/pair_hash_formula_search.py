#!/usr/bin/env python3
"""Hash/PRNG formula search for the 55 unordered 469 pair cells.

This pass is narrower than direct_symbol_formula_search.py. It does not test
plain arithmetic expressions as direct symbol-index formulas. Instead each
candidate is a small cell-local generator:

    cell_id, a, b, lore seed -> hash/PRNG output -> fixed symbol order

The generator is never allowed to learn a key->symbol table. Symbol orders are
predeclared from alphabetic, lore words, and lore-seeded permutations only.

Mechanical only: no plaintext, glossary entry, or translation is produced.
"""

from __future__ import annotations

import itertools
import json
import math
import random
from collections import Counter
from pathlib import Path
from typing import Callable, Iterable

import numpy as np


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FORMULA_JSON = ROOT / "analysis" / "mechanism_model_20260618" / "mechanical_formula_469.json"

OUT_JSON = HERE / "pair_hash_formula_results.json"
OUT_MD = HERE / "pair_hash_formula_report.md"

SIGMA = "*ABCEFILNORSTV"
SYMBOL_COUNT = len(SIGMA)
PAIR_COUNT = 55
U32_MASK = 0xFFFFFFFF
RANDOM_SEED = 46920260619

LORE_SEEDS = (469, 3478, 43153, 34784, 74032, 45331, 1)
LORE_WORDS = {
    "tibia": "TIBIA",
    "bonelord": "BONELORD",
    "beholder": "BEHOLDER",
    "cipsoft": "CIPSOFT",
    "knightmare": "KNIGHTMARE",
    "honeminas": "HONEMINAS",
    "tridiag": "TRIDIAG",
    "donina": "DONINA",
    "magic_web": "MAGICWEB",
    "mathemagic": "MATHEMAGIC",
    "great_calculator": "GREATCALCULATOR",
    "subjective_viewer": "SUBJECTIVEVIEWER",
}

LCG_MODULI = (14, 31, 55, 97, 251, 256, 469, 65521)
LCG_MULTIPLIERS = (3, 5, 17, 31, 65, 1103515245)
LCG_INCREMENT_KINDS = ("zero", "one", "digit_sum")
LCG_ROUNDS = (1, 2)

XORSHIFT_TRIPLES = ((13, 17, 5), (7, 9, 13), (5, 11, 3), (3, 7, 11), (9, 15, 7))
MIDDLE_SQUARE_WIDTHS = (4, 5, 6)
MIDDLE_SQUARE_ROUNDS = (1, 2)
HASH_BASES = (17, 31, 131, 257)
HASH_MODULI = (65521, 1000003, 2**32)

CONTROL_TRIALS = 120
ORDER_BATCH_SIZE = 4
TOP_ROWS_PER_ORDER = 15
TOP_ROWS_OUT = 50


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def natural_pairs() -> list[tuple[int, int, str]]:
    return [(a, b, f"{a}{b}") for a in range(10) for b in range(a, 10)]


def index_for_pair(a: int, b: int) -> int:
    if a > b:
        a, b = b, a
    return a * 10 - (a * (a - 1)) // 2 + (b - a)


def col_triangular_index(a: int, b: int) -> int:
    if a > b:
        a, b = b, a
    return b * (b + 1) // 2 + a


def primary_symbol(cell: dict) -> str:
    if cell["status"] == "pure":
        return cell["symbol_if_pure"]
    return sorted(cell["symbols"])[0]


def build_targets(formula: dict) -> list[dict]:
    rows = []
    for a, b, pair in natural_pairs():
        cell = formula["pair_table"][pair]
        rows.append(
            {
                "cell_id": index_for_pair(a, b),
                "pair": pair,
                "a": a,
                "b": b,
                "status": cell["status"],
                "primary_symbol": primary_symbol(cell),
                "acceptable_symbols": sorted(cell["symbols"]),
            }
        )
    return rows


def normalize_symbol_order(symbols: Iterable[str]) -> list[str]:
    out: list[str] = []
    for symbol in symbols:
        if symbol in SIGMA and symbol not in out:
            out.append(symbol)
    for symbol in SIGMA:
        if symbol not in out:
            out.append(symbol)
    return out


def add_symbol_order(orders: dict[str, dict], order_id: str, symbols: Iterable[str], **meta) -> None:
    order = normalize_symbol_order(symbols)
    if len(order) != SYMBOL_COUNT or len(set(order)) != SYMBOL_COUNT:
        raise ValueError(f"bad symbol order {order_id}")
    orders[order_id] = {"order": order, **meta}


def seeded_symbol_permutation(seed: int) -> list[str]:
    order = list(SIGMA)
    rng = random.Random(seed)
    rng.shuffle(order)
    return order


def seeded_cycle_order(seed: int) -> list[str]:
    steps = [1, 3, 5, 9, 11, 13]
    start = seed % SYMBOL_COUNT
    step = steps[(seed // SYMBOL_COUNT) % len(steps)]
    return [SIGMA[(start + step * idx) % SYMBOL_COUNT] for idx in range(SYMBOL_COUNT)]


def build_symbol_orders() -> dict[str, dict]:
    orders: dict[str, dict] = {}
    add_symbol_order(orders, "alphabetic", SIGMA, source="fixed_alphabet")
    add_symbol_order(orders, "alphabetic_rev", reversed(SIGMA), source="fixed_alphabet")
    add_symbol_order(orders, "star_last", "ABCEFILNORSTV*", source="fixed_alphabet")
    add_symbol_order(orders, "vowels_first", "AEIO*BCFLNRSTV", source="fixed_alphabet")

    for seed in LORE_SEEDS:
        add_symbol_order(
            orders,
            f"seed_shuffle_{seed}",
            seeded_symbol_permutation(seed),
            source="lore_seed_shuffle",
            seed=seed,
        )
        add_symbol_order(
            orders,
            f"seed_cycle_{seed}",
            seeded_cycle_order(seed),
            source="lore_seed_cycle",
            seed=seed,
        )

    for name, word in LORE_WORDS.items():
        add_symbol_order(
            orders,
            f"lore_word_{name}",
            word,
            source="lore_word",
            lore_word=word,
        )
    return orders


def cell_features(targets: list[dict]) -> dict[str, list[int]]:
    features: dict[str, list[int]] = {
        "cell_id": [],
        "cell_id_1": [],
        "pair_num": [],
        "pair_num_rev": [],
        "ab_pack": [],
        "tri_col": [],
        "sumdiff_pack": [],
        "quadratic_pack": [],
    }
    for row in targets:
        a, b, cell_id = row["a"], row["b"], row["cell_id"]
        values = {
            "cell_id": cell_id,
            "cell_id_1": cell_id + 1,
            "pair_num": 10 * a + b,
            "pair_num_rev": 10 * b + a,
            "ab_pack": (cell_id << 8) | (a << 4) | b,
            "tri_col": col_triangular_index(a, b),
            "sumdiff_pack": (a + b) * 10 + (b - a),
            "quadratic_pack": a * a + 10 * a * b + 100 * b * b + cell_id,
        }
        for key, value in values.items():
            features[key].append(value)
    return features


def digit_sum(value: int) -> int:
    return sum(int(char) for char in str(abs(value)))


def reverse_digits(value: int) -> int:
    return int(str(abs(value))[::-1])


def fold_u32(value: int) -> int:
    value &= U32_MASK
    return value ^ (value >> 16) ^ (value >> 8)


def byte_sum(value: int) -> int:
    value &= U32_MASK
    return sum((value >> shift) & 0xFF for shift in (0, 8, 16, 24))


POST_TRANSFORMS: dict[str, Callable[[int], int]] = {
    "low_mod": lambda value: value,
    "xor_fold": fold_u32,
    "high_nibble": lambda value: (value >> 4),
    "digit_sum": digit_sum,
}


def splitmix32(value: int) -> int:
    value = (value + 0x9E3779B9) & U32_MASK
    value = ((value ^ (value >> 16)) * 0x85EBCA6B) & U32_MASK
    value = ((value ^ (value >> 13)) * 0xC2B2AE35) & U32_MASK
    return (value ^ (value >> 16)) & U32_MASK


def xorshift32(value: int, shifts: tuple[int, int, int]) -> int:
    value &= U32_MASK
    if value == 0:
        value = 0x6D2B79F5
    a, b, c = shifts
    value ^= (value << a) & U32_MASK
    value ^= value >> b
    value ^= (value << c) & U32_MASK
    return value & U32_MASK


def middle_square(value: int, width: int, rounds: int) -> int:
    modulus = 10**width
    value %= modulus
    for _round in range(rounds):
        square = value * value
        text = str(square).zfill(width * 2)
        start = (len(text) - width) // 2
        value = int(text[start : start + width]) % modulus
    return value


def rolling_hash(text: str, seed: int, base: int, modulus: int) -> int:
    value = seed % modulus
    for char in text:
        value = (value * base + ord(char)) % modulus
    return value


def lcg_increment(kind: str, seed: int, modulus: int) -> int:
    if kind == "zero":
        return 0
    if kind == "one":
        return 1 % modulus
    if kind == "digit_sum":
        return digit_sum(seed) % modulus
    raise ValueError(kind)


def cell_payload(value: int, row: dict, seed: int) -> int:
    return value + seed + 101 * row["cell_id"] + 17 * row["a"] + 31 * row["b"]


def expression_with_post(base: str, post: str) -> str:
    if post == "low_mod":
        return f"({base}) mod 14"
    return f"{post}({base}) mod 14"


def build_formula_bank(targets: list[dict]) -> tuple[np.ndarray, list[dict], dict]:
    features = cell_features(targets)
    input_ids = list(features)
    seen: dict[bytes, dict] = {}
    attempts = 0
    family_attempts: Counter[str] = Counter()

    def add_prediction(meta_base: dict, values: list[int]) -> None:
        nonlocal attempts
        for post_id, post_func in POST_TRANSFORMS.items():
            attempts += 1
            family_attempts[meta_base["family"]] += 1
            pred = bytes(post_func(value) % SYMBOL_COUNT for value in values)
            meta = {
                **meta_base,
                "post_transform": post_id,
                "expression": expression_with_post(meta_base["base_expression"], post_id),
                "formula_id": f"{meta_base['formula_id']}|post={post_id}",
                "complexity_score": meta_base["complexity_score"] + (0.15 if post_id != "low_mod" else 0.0),
            }
            previous = seen.get(pred)
            if previous is None or meta["complexity_score"] < previous["complexity_score"]:
                seen[pred] = meta

    for seed in LORE_SEEDS:
        seed_digits = [int(char) for char in str(seed)]
        seed_digit_sum = digit_sum(seed)
        for input_id in input_ids[:6]:
            input_values = features[input_id]
            for modulus in LCG_MODULI:
                for multiplier in LCG_MULTIPLIERS:
                    for increment_kind in LCG_INCREMENT_KINDS:
                        increment = lcg_increment(increment_kind, seed, modulus)
                        for rounds in LCG_ROUNDS:
                            values = []
                            for value, row in zip(input_values, targets):
                                state = cell_payload(value, row, seed) % modulus
                                for _round in range(rounds):
                                    state = (multiplier * state + increment) % modulus
                                values.append(state)
                            add_prediction(
                                {
                                    "family": "lcg_cell",
                                    "formula_id": (
                                        f"lcg:{seed}:{input_id}:m{modulus}:a{multiplier}:"
                                        f"c{increment_kind}:r{rounds}"
                                    ),
                                    "base_expression": (
                                        f"LCG(seed={seed}, input={input_id}, m={modulus}, "
                                        f"a={multiplier}, c={increment_kind}, rounds={rounds}, "
                                        "payload=cell_id+a+b)"
                                    ),
                                    "seed": seed,
                                    "input_id": input_id,
                                    "modulus": modulus,
                                    "multiplier": multiplier,
                                    "increment_kind": increment_kind,
                                    "rounds": rounds,
                                    "complexity_score": 2.5 + rounds + math.log2(modulus) / 12.0,
                                },
                                values,
                            )

            for shifts in XORSHIFT_TRIPLES:
                values = [
                    xorshift32(
                        (
                            cell_payload(value, row, seed)
                            + seed * 0x45D9F3B
                            + (idx + 1) * 0x9E3779B9
                        )
                        & U32_MASK,
                        shifts,
                    )
                    for idx, (value, row) in enumerate(zip(input_values, targets))
                ]
                add_prediction(
                    {
                        "family": "xorshift_cell",
                        "formula_id": f"xorshift:{seed}:{input_id}:{'-'.join(map(str, shifts))}",
                        "base_expression": (
                            f"xorshift32(seed={seed}, input={input_id}, shifts={shifts}, "
                            "payload=cell_id+a+b)"
                        ),
                        "seed": seed,
                        "input_id": input_id,
                        "shifts": list(shifts),
                        "complexity_score": 4.0,
                    },
                    values,
                )

            for width in MIDDLE_SQUARE_WIDTHS:
                for rounds in MIDDLE_SQUARE_ROUNDS:
                    values = [
                        middle_square(cell_payload(value, row, seed), width, rounds)
                        for value, row in zip(input_values, targets)
                    ]
                    add_prediction(
                        {
                            "family": "middle_square_cell",
                            "formula_id": f"middle_square:{seed}:{input_id}:w{width}:r{rounds}",
                            "base_expression": (
                                f"middle_square(seed={seed}, input={input_id}, "
                                f"width={width}, rounds={rounds}, payload=cell_id+a+b)"
                            ),
                            "seed": seed,
                            "input_id": input_id,
                            "width": width,
                            "rounds": rounds,
                            "complexity_score": 3.5 + rounds + width / 10.0,
                        },
                        values,
                    )

        for template_id in ("seed_cell_ab", "cell_seed_ab", "ab_seed_cell", "seed_pair"):
            for base in HASH_BASES:
                for modulus in HASH_MODULI:
                    values = []
                    for row in targets:
                        if template_id == "seed_cell_ab":
                            text = f"{seed}:{row['cell_id']:02d}:{row['a']}:{row['b']}"
                        elif template_id == "cell_seed_ab":
                            text = f"{row['cell_id']:02d}:{seed}:{row['a']}:{row['b']}"
                        elif template_id == "ab_seed_cell":
                            text = f"{row['a']}{row['b']}:{seed}:{row['cell_id']:02d}"
                        else:
                            text = f"{seed}:{row['pair']}"
                        values.append(rolling_hash(text, seed, base, modulus))
                    add_prediction(
                        {
                            "family": "rolling_hash_cell",
                            "formula_id": f"rolling_hash:{seed}:{template_id}:b{base}:m{modulus}",
                            "base_expression": (
                                f"rolling_hash(template={template_id}, seed={seed}, "
                                f"base={base}, m={modulus})"
                            ),
                            "seed": seed,
                            "template_id": template_id,
                            "base": base,
                            "modulus": modulus,
                            "complexity_score": 4.5 + math.log2(modulus) / 16.0,
                        },
                        values,
                    )

        mix_specs = {
            "digit_weighted_sum": [
                (
                    (row["cell_id"] + 1) * seed_digits[row["a"] % len(seed_digits)]
                    + (row["a"] + 1) * seed_digits[row["b"] % len(seed_digits)]
                    + row["b"] * seed_digit_sum
                )
                for row in targets
            ],
            "digit_cross_xor": [
                (
                    (row["cell_id"] << 4)
                    ^ (seed_digits[row["a"] % len(seed_digits)] << 8)
                    ^ (seed_digits[row["b"] % len(seed_digits)] << 12)
                    ^ seed
                )
                for row in targets
            ],
            "reverse_seed_mix": [
                (reverse_digits(seed) + row["cell_id"] * seed_digit_sum + row["a"] * 10 + row["b"])
                for row in targets
            ],
            "splitmix_cell": [
                splitmix32(seed ^ (row["cell_id"] * 0x9E3779B1) ^ (row["a"] * 0x85EBCA77) ^ row["b"])
                for row in targets
            ],
            "byte_sum_mulxor": [
                byte_sum((seed + row["cell_id"] * 257 + row["a"] * 17 + row["b"]) * 0x45D9F3B)
                for row in targets
            ],
        }
        for mix_id, values in mix_specs.items():
            add_prediction(
                {
                    "family": "digit_mix_cell",
                    "formula_id": f"digit_mix:{seed}:{mix_id}",
                    "base_expression": f"digit_mix(seed={seed}, variant={mix_id})",
                    "seed": seed,
                    "mix_id": mix_id,
                    "complexity_score": 3.0,
                },
                values,
            )

    prediction_keys = list(seen)
    prediction_blob = b"".join(prediction_keys)
    predictions = np.frombuffer(prediction_blob, dtype=np.uint8).reshape(len(prediction_keys), PAIR_COUNT).copy()
    metas = [seen[key] for key in prediction_keys]
    stats = {
        "attempted_formula_count": attempts,
        "unique_prediction_vector_count": len(metas),
        "family_attempts": dict(sorted(family_attempts.items())),
        "input_features": input_ids,
        "post_transforms": list(POST_TRANSFORMS),
    }
    return predictions, metas, stats


def lookup_bits() -> float:
    return PAIR_COUNT * math.log2(SYMBOL_COUNT)


def mdl_cost_bits(primary_hits: int, attempted_formula_count: int, symbol_order_count: int) -> float:
    formula_bits = math.log2(max(1, attempted_formula_count))
    order_bits = math.log2(max(1, symbol_order_count))
    exception_bits = (PAIR_COUNT - primary_hits) * (math.log2(PAIR_COUNT) + math.log2(SYMBOL_COUNT))
    return formula_bits + order_bits + exception_bits


def mdl_row(primary_hits: int, attempted_formula_count: int, symbol_order_count: int) -> dict:
    mdl = mdl_cost_bits(primary_hits, attempted_formula_count, symbol_order_count)
    raw = lookup_bits()
    return {
        "mdl_cost_bits": mdl,
        "lookup_cost_bits": raw,
        "mdl_gain_vs_lookup_bits": raw - mdl,
        "lookup_cost_ratio": mdl / raw,
        "compresses_vs_lookup": mdl < raw,
    }


def target_indices(labels: list[str], order: list[str]) -> np.ndarray:
    index = {symbol: idx for idx, symbol in enumerate(order)}
    return np.array([index[label] for label in labels], dtype=np.uint8)


def summarize_values(values: list[float], observed: float, high_is_good: bool = True) -> dict:
    mean = sum(values) / len(values)
    sd = (sum((value - mean) ** 2 for value in values) / (len(values) - 1)) ** 0.5 if len(values) > 1 else 0.0
    if high_is_good:
        p = (sum(value >= observed for value in values) + 1) / (len(values) + 1)
        z = (observed - mean) / sd if sd else 0.0
    else:
        p = (sum(value <= observed for value in values) + 1) / (len(values) + 1)
        z = (mean - observed) / sd if sd else 0.0
    return {
        "observed": observed,
        "control_mean": mean,
        "control_sd": sd,
        "control_min": min(values),
        "control_max": max(values),
        "z_good_direction": z,
        "p_good_direction": p,
    }


def best_hits_for_orders(predictions: np.ndarray, labels: list[str], orders: list[list[str]]) -> int:
    target_matrix = np.stack([target_indices(labels, order) for order in orders], axis=0)
    best = -1
    for start in range(0, len(orders), ORDER_BATCH_SIZE):
        batch = target_matrix[start : start + ORDER_BATCH_SIZE]
        hits = np.count_nonzero(predictions[:, None, :] == batch[None, :, :], axis=2)
        value = int(hits.max())
        if value > best:
            best = value
    return best


def row_sort_key(row: dict):
    return (
        -row["primary_hits"],
        -row["acceptable_hits"],
        row["lookup_cost_ratio"],
        row["complexity_score"],
        row["symbol_order_id"],
        row["formula_id"],
    )


def materialize_row(
    prediction_index: int,
    hits: int,
    predictions: np.ndarray,
    metas: list[dict],
    symbol_order_id: str,
    symbol_order: dict,
    targets: list[dict],
    attempted_formula_count: int,
    symbol_order_count: int,
) -> dict:
    meta = metas[prediction_index]
    order = symbol_order["order"]
    pred_indices = predictions[prediction_index]
    predicted_symbols = [order[int(idx)] for idx in pred_indices]
    acceptable_hits = sum(symbol in set(row["acceptable_symbols"]) for symbol, row in zip(predicted_symbols, targets))
    detail = []
    misses = []
    for symbol, row in zip(predicted_symbols, targets):
        primary_hit = symbol == row["primary_symbol"]
        acceptable_hit = symbol in row["acceptable_symbols"]
        item = {
            "pair": row["pair"],
            "cell_id": row["cell_id"],
            "primary_symbol": row["primary_symbol"],
            "acceptable_symbols": row["acceptable_symbols"],
            "predicted_symbol": symbol,
            "primary_hit": primary_hit,
            "acceptable_hit": acceptable_hit,
        }
        detail.append(item)
        if not primary_hit:
            misses.append(item)
    row = {
        **{key: value for key, value in meta.items() if key != "complexity_score"},
        "complexity_score": meta["complexity_score"],
        "symbol_order_id": symbol_order_id,
        "symbol_order": order,
        "symbol_order_source": symbol_order.get("source"),
        "primary_hits": int(hits),
        "acceptable_hits": int(acceptable_hits),
        "primary_accuracy": int(hits) / PAIR_COUNT,
        "acceptable_accuracy": int(acceptable_hits) / PAIR_COUNT,
        "predicted_symbol_string_natural_pair_order": "".join(predicted_symbols),
        "primary_misses": misses,
        "predictions": detail,
    }
    row.update(mdl_row(int(hits), attempted_formula_count, symbol_order_count))
    return row


def observed_search(predictions: np.ndarray, metas: list[dict], symbol_orders: dict[str, dict], targets: list[dict], stats: dict) -> dict:
    primary_labels = [row["primary_symbol"] for row in targets]
    rows: list[dict] = []
    best_by_order = []
    for order_id, order_meta in symbol_orders.items():
        target = target_indices(primary_labels, order_meta["order"])
        hits = np.count_nonzero(predictions == target, axis=1)
        top_count = min(TOP_ROWS_PER_ORDER, len(hits))
        candidate_indices = np.argpartition(-hits, top_count - 1)[:top_count]
        order_rows = [
            materialize_row(
                int(idx),
                int(hits[idx]),
                predictions,
                metas,
                order_id,
                order_meta,
                targets,
                stats["attempted_formula_count"],
                len(symbol_orders),
            )
            for idx in candidate_indices
        ]
        order_rows.sort(key=row_sort_key)
        rows.extend(order_rows)
        best_by_order.append({key: value for key, value in order_rows[0].items() if key not in {"predictions", "primary_misses"}})

    rows.sort(key=row_sort_key)
    compact_top = []
    seen_hypotheses: set[tuple[str, str, str]] = set()
    for row in rows:
        key = (row["symbol_order_id"], row["formula_id"], row["predicted_symbol_string_natural_pair_order"])
        if key in seen_hypotheses:
            continue
        seen_hypotheses.add(key)
        compact_top.append(row)
        if len(compact_top) >= TOP_ROWS_OUT:
            break
    best_by_order.sort(key=row_sort_key)
    return {
        "best": compact_top[0],
        "top_rows": compact_top,
        "best_by_symbol_order": best_by_order,
    }


def run_inventory_label_controls(
    predictions: np.ndarray,
    primary_labels: list[str],
    symbol_orders: dict[str, dict],
    stats: dict,
    observed_best: dict,
) -> dict:
    rng = random.Random(RANDOM_SEED + 101)
    orders = [meta["order"] for meta in symbol_orders.values()]
    hits_values = []
    mdl_values = []
    for _trial in range(CONTROL_TRIALS):
        shuffled = primary_labels[:]
        rng.shuffle(shuffled)
        hit = best_hits_for_orders(predictions, shuffled, orders)
        hits_values.append(hit)
        mdl_values.append(mdl_row(hit, stats["attempted_formula_count"], len(symbol_orders))["mdl_gain_vs_lookup_bits"])
    return {
        "method": "inventory_preserving_label_shuffle",
        "trials": CONTROL_TRIALS,
        "hits": summarize_values(hits_values, observed_best["primary_hits"]),
        "mdl_gain": summarize_values(mdl_values, observed_best["mdl_gain_vs_lookup_bits"]),
    }


def run_symbol_order_controls(
    predictions: np.ndarray,
    primary_labels: list[str],
    symbol_order_count: int,
    stats: dict,
    observed_best: dict,
) -> dict:
    rng = random.Random(RANDOM_SEED + 202)
    hits_values = []
    mdl_values = []
    for _trial in range(CONTROL_TRIALS):
        orders = []
        for _order_index in range(symbol_order_count):
            order = list(SIGMA)
            rng.shuffle(order)
            orders.append(order)
        hit = best_hits_for_orders(predictions, primary_labels, orders)
        hits_values.append(hit)
        mdl_values.append(mdl_row(hit, stats["attempted_formula_count"], symbol_order_count)["mdl_gain_vs_lookup_bits"])
    return {
        "method": "symbol_order_shuffle",
        "trials": CONTROL_TRIALS,
        "orders_per_trial": symbol_order_count,
        "hits": summarize_values(hits_values, observed_best["primary_hits"]),
        "mdl_gain": summarize_values(mdl_values, observed_best["mdl_gain_vs_lookup_bits"]),
    }


def classify(best: dict, controls: dict) -> str:
    label_p = controls["inventory_label_shuffle"]["hits"]["p_good_direction"]
    order_p = controls["symbol_order_shuffle"]["hits"]["p_good_direction"]
    mdl_label_p = controls["inventory_label_shuffle"]["mdl_gain"]["p_good_direction"]
    mdl_order_p = controls["symbol_order_shuffle"]["mdl_gain"]["p_good_direction"]
    if not best["compresses_vs_lookup"]:
        return "rejected_no_compression"
    if max(label_p, order_p, mdl_label_p, mdl_order_p) <= 0.01:
        return "candidate_hash_prng_formula"
    return "rejected_control"


def compact_row(row: dict) -> dict:
    drop = {"predictions", "primary_misses"}
    return {key: value for key, value in row.items() if key not in drop}


def write_report(result: dict) -> None:
    best = result["observed"]["best"]
    label_control = result["controls"]["inventory_label_shuffle"]
    order_control = result["controls"]["symbol_order_shuffle"]
    lines = [
        "# Pair Hash/PRNG Formula Search",
        "",
        "Generated by `pair_hash_formula_search.py`.",
        "",
        "This pass tests cell-local hash/PRNG formulas for the 55 unordered",
        "pair cells: `cell_id,a,b,seed -> index -> fixed symbol order`. It is",
        "distinct from `direct_symbol_formula_search.py` because it does not",
        "search free arithmetic symbol-index expressions and does not learn a",
        "key-to-symbol table. Symbol orders are fixed before scoring from",
        "alphabetic order, lore words, or lore-seeded permutations/cycles.",
        "",
        "Translation delta: `NONE`.",
        "",
        "## Search Space",
        "",
        f"- Source: `{FORMULA_JSON.relative_to(ROOT)}`.",
        f"- Pair cells: `{PAIR_COUNT}` unordered cells.",
        f"- Symbol alphabet: `{SIGMA}` (`{SYMBOL_COUNT}` symbols).",
        f"- Lore seeds: `{', '.join(map(str, LORE_SEEDS))}`.",
        f"- Symbol orders tested: `{result['search_space']['symbol_order_count']}`.",
        f"- Formula attempts: `{result['search_space']['attempted_formula_count']}`.",
        f"- Unique prediction vectors: `{result['search_space']['unique_prediction_vector_count']}`.",
        "- Formula families: small LCG, xorshift32, middle-square, rolling",
        "  modular hash, and digit-mix/splitmix variants over `cell_id,a,b`.",
        "",
        "Conflict handling: unordered cell `19` is a known `I/N` conflict.",
        "Tables rank by the stable primary label and also report",
        "`acceptable_hits`, where either listed symbol is accepted for conflict",
        "cells.",
        "",
        "## Summary",
        "",
        "| Primary hits | Acceptable hits | Formula | Symbol order | MDL/lookup | Label-shuffle p(hit) | Symbol-order p(hit) | Verdict |",
        "|---:|---:|---|---|---:|---:|---:|---|",
        (
            f"| {best['primary_hits']}/55 | {best['acceptable_hits']}/55 | "
            f"`{best['expression']}` | `{best['symbol_order_id']}` | "
            f"{best['lookup_cost_ratio']:.3f} | "
            f"{label_control['hits']['p_good_direction']:.4f} | "
            f"{order_control['hits']['p_good_direction']:.4f} | "
            f"`{result['verdict']}` |"
        ),
        "",
        "## Top Rows",
        "",
        "| Hits | Acceptable | MDL/lookup | Order | Family | Formula |",
        "|---:|---:|---:|---|---|---|",
    ]
    for row in result["observed"]["top_rows"][:20]:
        lines.append(
            f"| {row['primary_hits']}/55 | {row['acceptable_hits']}/55 | "
            f"{row['lookup_cost_ratio']:.3f} | `{row['symbol_order_id']}` | "
            f"`{row['family']}` | `{row['expression']}` |"
        )
    lines.extend(
        [
            "",
            "## Best By Symbol Order",
            "",
            "| Order | Source | Hits | Acceptable | MDL/lookup | Formula |",
            "|---|---|---:|---:|---:|---|",
        ]
    )
    for row in result["observed"]["best_by_symbol_order"][:20]:
        lines.append(
            f"| `{row['symbol_order_id']}` | `{row['symbol_order_source']}` | "
            f"{row['primary_hits']}/55 | {row['acceptable_hits']}/55 | "
            f"{row['lookup_cost_ratio']:.3f} | `{row['expression']}` |"
        )
    lines.extend(
        [
            "",
            "## Controls",
            "",
            "| Control | Trials | Mean best hits | Max best hits | p(hit) | p(MDL gain) |",
            "|---|---:|---:|---:|---:|---:|",
            (
                f"| inventory-preserving label shuffle | {label_control['trials']} | "
                f"{label_control['hits']['control_mean']:.2f} | "
                f"{label_control['hits']['control_max']:.0f} | "
                f"{label_control['hits']['p_good_direction']:.4f} | "
                f"{label_control['mdl_gain']['p_good_direction']:.4f} |"
            ),
            (
                f"| symbol-order shuffle | {order_control['trials']} | "
                f"{order_control['hits']['control_mean']:.2f} | "
                f"{order_control['hits']['control_max']:.0f} | "
                f"{order_control['hits']['p_good_direction']:.4f} | "
                f"{order_control['mdl_gain']['p_good_direction']:.4f} |"
            ),
            "",
            "## Interpretation",
            "",
        ]
    )
    if result["verdict"] == "candidate_hash_prng_formula":
        lines.extend(
            [
                "A hash/PRNG cell formula passed the configured compression and",
                "control gates. This remains mechanical only and would not imply",
                "plaintext.",
            ]
        )
    else:
        lines.extend(
            [
                "No tested hash/PRNG cell formula qualifies as a candidate. The",
                "best row does not satisfy the required combination of below-lookup",
                "MDL and control performance. This preserves the prior conclusion",
                "that a compact original exact pair-cell generator remains",
                "unrecovered.",
            ]
        )
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    formula = load_json(FORMULA_JSON)
    targets = build_targets(formula)
    symbol_orders = build_symbol_orders()
    predictions, metas, stats = build_formula_bank(targets)
    observed = observed_search(predictions, metas, symbol_orders, targets, stats)
    primary_labels = [row["primary_symbol"] for row in targets]
    controls = {
        "inventory_label_shuffle": run_inventory_label_controls(
            predictions, primary_labels, symbol_orders, stats, observed["best"]
        ),
        "symbol_order_shuffle": run_symbol_order_controls(
            predictions, primary_labels, len(symbol_orders), stats, observed["best"]
        ),
    }
    result_verdict = classify(observed["best"], controls)

    result = {
        "schema": "pair_hash_formula_results.v1",
        "created_at": "2026-06-19",
        "translation_delta": "NONE",
        "source": str(FORMULA_JSON.relative_to(ROOT)),
        "target": {
            "pair_cells": PAIR_COUNT,
            "symbols": list(SIGMA),
            "primary_conflict_policy": "pure symbol else sorted(cell.symbols)[0]",
            "conflict_cells": [
                {
                    "pair": row["pair"],
                    "cell_id": row["cell_id"],
                    "acceptable_symbols": row["acceptable_symbols"],
                    "primary_symbol": row["primary_symbol"],
                }
                for row in targets
                if len(row["acceptable_symbols"]) > 1
            ],
        },
        "search_space": {
            **stats,
            "symbol_order_count": len(symbol_orders),
            "symbol_orders": symbol_orders,
            "lore_seeds": list(LORE_SEEDS),
            "lore_words": LORE_WORDS,
            "lcg_moduli": list(LCG_MODULI),
            "lcg_multipliers": list(LCG_MULTIPLIERS),
            "lcg_increment_kinds": list(LCG_INCREMENT_KINDS),
            "lcg_rounds": list(LCG_ROUNDS),
            "xorshift_triples": [list(item) for item in XORSHIFT_TRIPLES],
            "middle_square_widths": list(MIDDLE_SQUARE_WIDTHS),
            "middle_square_rounds": list(MIDDLE_SQUARE_ROUNDS),
            "hash_bases": list(HASH_BASES),
            "hash_moduli": list(HASH_MODULI),
            "control_trials": CONTROL_TRIALS,
        },
        "observed": {
            "best": observed["best"],
            "top_rows": [compact_row(row) for row in observed["top_rows"]],
            "best_by_symbol_order": observed["best_by_symbol_order"],
        },
        "controls": controls,
        "verdict": result_verdict,
    }
    write_json(OUT_JSON, result)
    write_report(result)

    print(f"wrote {OUT_JSON.relative_to(HERE)}")
    print(f"wrote {OUT_MD.relative_to(HERE)}")
    print(
        "best={}/55 acceptable={}/55 order={} mdl_ratio={:.3f} p_label={:.4f} p_order={:.4f} verdict={}".format(
            observed["best"]["primary_hits"],
            observed["best"]["acceptable_hits"],
            observed["best"]["symbol_order_id"],
            observed["best"]["lookup_cost_ratio"],
            controls["inventory_label_shuffle"]["hits"]["p_good_direction"],
            controls["symbol_order_shuffle"]["hits"]["p_good_direction"],
            result_verdict,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
