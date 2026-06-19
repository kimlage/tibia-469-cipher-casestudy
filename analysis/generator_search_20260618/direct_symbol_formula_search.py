#!/usr/bin/env python3
"""Direct symbol-index formula search for the 55 unordered 469 pair cells.

This pass tests formulas of the form:

    unordered digit pair (a,b) -> numeric expression -> symbol-order index

The model is deliberately not allowed to learn a key->symbol table or a
feature-group majority table. A candidate must predict positions in a complete
symbol order and must beat inventory-preserving label shuffles / random symbol
orders while costing less than the raw 55-cell lookup.

Mechanical only: no plaintext, glossary entry, or translation is produced.
"""

from __future__ import annotations

import itertools
import json
import math
import random
from collections import Counter
from pathlib import Path
from typing import Iterable

import numpy as np


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FORMULA_JSON = ROOT / "analysis" / "mechanism_model_20260618" / "mechanical_formula_469.json"

OUT_JSON = HERE / "direct_symbol_formula_results.json"
OUT_MD = HERE / "direct_symbol_formula_report.md"

SIGMA = "*ABCEFILNORSTV"
SYMBOL_COUNT = len(SIGMA)
PAIR_COUNT = 55
RANDOM_SEED = 46920260619

RAW_MODULI = (14, 55)
AFFINE_COEFS = (-3, -2, -1, 1, 2, 3)
QUADRATIC_COEFS = (-2, -1, 0, 1, 2)
OFFSETS_BY_MOD = {
    14: tuple(range(14)),
    55: tuple(range(-7, 8)),
}

INVENTORY_LABEL_SHUFFLE_TRIALS = 120
SYMBOL_ORDER_SHUFFLE_TRIALS = 120
ORDER_BATCH_SIZE = 4
TOP_ROWS_PER_ORDER = 20
TOP_ROWS_OUT = 50

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

LORE_DIGIT_SEEDS = ("469", "3478", "43153", "34784", "74032", "45331", "19", "39")


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def natural_pairs() -> list[tuple[int, int, str]]:
    return [(a, b, f"{a}{b}") for a in range(10) for b in range(a, 10)]


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


def primary_symbol(cell: dict) -> str:
    if cell["status"] == "pure":
        return cell["symbol_if_pure"]
    return sorted(cell["symbols"])[0]


def build_targets(formula: dict) -> list[dict]:
    rows = []
    for a, b, pair in natural_pairs():
        cell = formula["pair_table"][pair]
        symbols = sorted(cell["symbols"])
        rows.append(
            {
                "pair": pair,
                "a": a,
                "b": b,
                "status": cell["status"],
                "primary_symbol": primary_symbol(cell),
                "acceptable_symbols": symbols,
            }
        )
    return rows


def code_usage_counts(formula: dict) -> Counter[str]:
    counts: Counter[str] = Counter()
    for code, count in formula["code_counts"].items():
        symbol = formula["code_to_symbol"].get(code)
        if symbol is not None:
            counts[symbol] += int(count)
    return counts


def code_table_first_use(formula: dict) -> list[str]:
    out: list[str] = []
    for code in sorted(formula["code_to_symbol"], key=int):
        symbol = formula["code_to_symbol"][code]
        if symbol not in out:
            out.append(symbol)
    return out


def build_symbol_orders(formula: dict, targets: list[dict]) -> dict[str, dict]:
    primary_labels = [row["primary_symbol"] for row in targets]
    cell_counts = Counter(primary_labels)
    usage_counts = code_usage_counts(formula)
    orders: dict[str, dict] = {}

    add_symbol_order(orders, "alphabetic", SIGMA, source="alphabet")
    add_symbol_order(orders, "alphabetic_rev", reversed(SIGMA), source="alphabet")
    add_symbol_order(
        orders,
        "cell_frequency_desc",
        [symbol for symbol, _count in cell_counts.most_common()],
        source="cell_inventory",
    )
    add_symbol_order(
        orders,
        "cell_frequency_asc",
        [symbol for symbol, _count in sorted(cell_counts.items(), key=lambda item: (item[1], item[0]))],
        source="cell_inventory",
    )
    add_symbol_order(
        orders,
        "code_usage_desc",
        [symbol for symbol, _count in usage_counts.most_common()],
        source="code_usage",
    )
    add_symbol_order(
        orders,
        "code_usage_asc",
        [symbol for symbol, _count in sorted(usage_counts.items(), key=lambda item: (item[1], item[0]))],
        source="code_usage",
    )
    add_symbol_order(
        orders,
        "code_table_first_use",
        code_table_first_use(formula),
        source="code_table_order",
    )

    first_seen: list[str] = []
    for symbol in primary_labels:
        if symbol not in first_seen:
            first_seen.append(symbol)
    add_symbol_order(
        orders,
        "cell_first_use",
        first_seen,
        source="target_label_order",
        target_label_leakage=True,
    )
    add_symbol_order(
        orders,
        "cell_first_use_rev",
        reversed(first_seen),
        source="target_label_order",
        target_label_leakage=True,
    )

    diagonal_symbols = [targets[index_for_pair(i, i)]["primary_symbol"] for i in range(10)]
    add_symbol_order(
        orders,
        "diagonal_first",
        diagonal_symbols,
        source="target_label_order",
        target_label_leakage=True,
    )
    add_symbol_order(
        orders,
        "diagonal_first_rev",
        reversed(diagonal_symbols),
        source="target_label_order",
        target_label_leakage=True,
    )

    for name, word in LORE_WORDS.items():
        add_symbol_order(
            orders,
            f"lore_{name}",
            word,
            source="lore_word",
            uses_lore=True,
            lore_word=word,
        )
    return orders


def index_for_pair(a: int, b: int) -> int:
    if a > b:
        a, b = b, a
    # Number of upper-triangular row-major cells before row a, plus offset.
    return a * 10 - (a * (a - 1)) // 2 + (b - a)


def row_triangular_index(a: int, b: int) -> int:
    return index_for_pair(a, b)


def col_triangular_index(a: int, b: int) -> int:
    return b * (b + 1) // 2 + a


def arithmetic_features(targets: list[dict]) -> dict[str, list[int]]:
    features: dict[str, list[int]] = {
        "a": [],
        "b": [],
        "sum": [],
        "diff": [],
        "prod": [],
        "triangular_index": [],
        "row_triangular_index": [],
        "min": [],
        "max": [],
        "a2": [],
        "b2": [],
        "sum2": [],
        "diff2": [],
    }
    for row in targets:
        a, b = row["a"], row["b"]
        s = a + b
        d = b - a
        p = a * b
        values = {
            "a": a,
            "b": b,
            "sum": s,
            "diff": d,
            "prod": p,
            "triangular_index": col_triangular_index(a, b),
            "row_triangular_index": row_triangular_index(a, b),
            "min": min(a, b),
            "max": max(a, b),
            "a2": a * a,
            "b2": b * b,
            "sum2": s * s,
            "diff2": d * d,
        }
        for key, value in values.items():
            features[key].append(value)
    return features


def digit_order_from_seed(seed: str) -> list[int]:
    out: list[int] = []
    for char in seed:
        if char.isdigit():
            digit = int(char)
            if digit not in out:
                out.append(digit)
    for digit in range(10):
        if digit not in out:
            out.append(digit)
    return out


def digit_orders() -> dict[str, list[int]]:
    orders = {
        "natural": list(range(10)),
        "natural_rev": list(reversed(range(10))),
    }
    for seed in LORE_DIGIT_SEEDS:
        orders[f"lore_digits_{seed}"] = digit_order_from_seed(seed)
    return orders


def digit_distance_features(targets: list[dict], order: list[int]) -> dict[str, list[int]]:
    pos = {digit: index for index, digit in enumerate(order)}
    features: dict[str, list[int]] = {
        "pos_sum": [],
        "line_dist": [],
        "cycle_dist": [],
        "pos_prod": [],
        "pos_triangular_index": [],
        "pos_min": [],
        "pos_max": [],
        "edge": [],
    }
    for row in targets:
        pa = pos[row["a"]]
        pb = pos[row["b"]]
        lo, hi = sorted((pa, pb))
        raw = abs(pa - pb)
        values = {
            "pos_sum": pa + pb,
            "line_dist": raw,
            "cycle_dist": min(raw, 10 - raw),
            "pos_prod": pa * pb,
            "pos_triangular_index": col_triangular_index(lo, hi),
            "pos_min": lo,
            "pos_max": hi,
            "edge": min(lo, 9 - hi),
        }
        for key, value in values.items():
            features[key].append(value)
    return features


def expression_for(offset: int, coefs: tuple[int, ...], names: tuple[str, ...], raw_mod: int) -> str:
    terms = [str(offset)]
    for coef, name in zip(coefs, names):
        terms.append(f"{coef:+d}*{name}")
    inner = " ".join(terms)
    if raw_mod == SYMBOL_COUNT:
        return f"({inner}) mod 14"
    return f"(({inner}) mod {raw_mod}) mod 14"


def build_formula_bank(targets: list[dict]) -> tuple[np.ndarray, list[dict], dict]:
    seen: dict[bytes, dict] = {}
    attempts = 0
    family_attempts: Counter[str] = Counter()
    arith = arithmetic_features(targets)

    def add_formula(meta: dict, values: list[int]) -> None:
        nonlocal attempts
        attempts += 1
        family_attempts[meta["family"]] += 1
        raw_mod = meta["raw_mod"]
        pred = bytes(((value % raw_mod) % SYMBOL_COUNT for value in values))
        previous = seen.get(pred)
        if previous is None or meta["complexity_score"] < previous["complexity_score"]:
            seen[pred] = meta

    def emit_affine(feature_values: dict[str, list[int]], feature_names: list[str], family: str, prefix: str) -> None:
        for raw_mod in RAW_MODULI:
            for size in (1, 2):
                for names in itertools.combinations(feature_names, size):
                    vectors = [feature_values[name] for name in names]
                    for coefs in itertools.product(AFFINE_COEFS, repeat=size):
                        for offset in OFFSETS_BY_MOD[raw_mod]:
                            values = [
                                offset + sum(coef * vector[idx] for coef, vector in zip(coefs, vectors))
                                for idx in range(PAIR_COUNT)
                            ]
                            complexity = size + sum(abs(coef) for coef in coefs) / 10.0 + abs(offset) / 25.0
                            add_formula(
                                {
                                    "formula_id": f"{prefix}:{raw_mod}:{offset}:{','.join(map(str, coefs))}:{','.join(names)}",
                                    "family": family,
                                    "raw_mod": raw_mod,
                                    "expression": expression_for(offset, coefs, names, raw_mod),
                                    "features": list(names),
                                    "coefs": list(coefs),
                                    "offset": offset,
                                    "term_count": size,
                                    "complexity_score": complexity,
                                },
                                values,
                            )

    arithmetic_names = [
        "a",
        "b",
        "sum",
        "diff",
        "prod",
        "triangular_index",
        "row_triangular_index",
        "min",
        "max",
        "a2",
        "b2",
        "sum2",
        "diff2",
    ]
    emit_affine(arith, arithmetic_names, "arithmetic_affine", "arith")

    quad_names = ("a", "b", "a2", "ab", "b2")
    quad_values = {
        "a": arith["a"],
        "b": arith["b"],
        "a2": arith["a2"],
        "ab": arith["prod"],
        "b2": arith["b2"],
    }
    for raw_mod in RAW_MODULI:
        for coefs in itertools.product(QUADRATIC_COEFS, repeat=len(quad_names)):
            if all(coef == 0 for coef in coefs):
                continue
            if coefs[2] == 0 and coefs[3] == 0 and coefs[4] == 0:
                continue
            vectors = [quad_values[name] for name in quad_names]
            for offset in OFFSETS_BY_MOD[raw_mod]:
                values = [
                    offset + sum(coef * vector[idx] for coef, vector in zip(coefs, vectors))
                    for idx in range(PAIR_COUNT)
                ]
                terms = tuple(name for coef, name in zip(coefs, quad_names) if coef != 0)
                complexity = len(terms) + sum(abs(coef) for coef in coefs) / 10.0 + abs(offset) / 25.0 + 0.5
                add_formula(
                    {
                        "formula_id": f"quadratic_ab:{raw_mod}:{offset}:{','.join(map(str, coefs))}",
                        "family": "quadratic_ab",
                        "raw_mod": raw_mod,
                        "expression": expression_for(offset, coefs, quad_names, raw_mod),
                        "features": list(quad_names),
                        "coefs": list(coefs),
                        "offset": offset,
                        "term_count": len(terms),
                        "complexity_score": complexity,
                    },
                    values,
                )

    for order_id, order in digit_orders().items():
        dist = digit_distance_features(targets, order)
        dist_names = list(dist)
        before = attempts
        emit_affine(dist, dist_names, "digit_order_distance_affine", f"dist:{order_id}")
        for meta in list(seen.values()):
            if meta["family"] == "digit_order_distance_affine" and meta["formula_id"].startswith(f"dist:{order_id}:"):
                meta["digit_order_id"] = order_id
                meta["digit_order"] = order
        family_attempts[f"digit_order:{order_id}"] += attempts - before

    prediction_keys = list(seen)
    prediction_blob = b"".join(prediction_keys)
    predictions = np.frombuffer(prediction_blob, dtype=np.uint8).reshape(len(prediction_keys), PAIR_COUNT).copy()
    metas = [seen[key] for key in prediction_keys]
    stats = {
        "attempted_formula_count": attempts,
        "unique_prediction_vector_count": len(metas),
        "family_attempts": dict(sorted(family_attempts.items())),
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
        bool(row.get("target_label_leakage", False)),
        bool(row.get("uses_lore", False)),
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
        "uses_lore": bool(symbol_order.get("uses_lore") or meta.get("digit_order_id", "").startswith("lore_")),
        "target_label_leakage": bool(symbol_order.get("target_label_leakage")),
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
        best_hit = int(hits.max())
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
    best_by_order.sort(key=row_sort_key)
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
    for _trial in range(INVENTORY_LABEL_SHUFFLE_TRIALS):
        shuffled = primary_labels[:]
        rng.shuffle(shuffled)
        hit = best_hits_for_orders(predictions, shuffled, orders)
        hits_values.append(hit)
        mdl_values.append(mdl_row(hit, stats["attempted_formula_count"], len(symbol_orders))["mdl_gain_vs_lookup_bits"])
    return {
        "method": "inventory_preserving_label_shuffle",
        "trials": INVENTORY_LABEL_SHUFFLE_TRIALS,
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
    for _trial in range(SYMBOL_ORDER_SHUFFLE_TRIALS):
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
        "trials": SYMBOL_ORDER_SHUFFLE_TRIALS,
        "orders_per_trial": symbol_order_count,
        "hits": summarize_values(hits_values, observed_best["primary_hits"]),
        "mdl_gain": summarize_values(mdl_values, observed_best["mdl_gain_vs_lookup_bits"]),
    }


def classify(best: dict, controls: dict) -> str:
    label_p = controls["inventory_label_shuffle"]["hits"]["p_good_direction"]
    order_p = controls["symbol_order_shuffle"]["hits"]["p_good_direction"]
    mdl_label_p = controls["inventory_label_shuffle"]["mdl_gain"]["p_good_direction"]
    mdl_order_p = controls["symbol_order_shuffle"]["mdl_gain"]["p_good_direction"]
    if best["target_label_leakage"]:
        return "rejected_target_order_leakage"
    if not best["compresses_vs_lookup"]:
        return "rejected_no_compression"
    if max(label_p, order_p, mdl_label_p, mdl_order_p) <= 0.01:
        return "candidate_direct_symbol_formula"
    return "rejected_control"


def compact_row(row: dict) -> dict:
    drop = {"predictions", "primary_misses"}
    return {key: value for key, value in row.items() if key not in drop}


def write_report(result: dict) -> None:
    best = result["observed"]["best"]
    label_control = result["controls"]["inventory_label_shuffle"]
    order_control = result["controls"]["symbol_order_shuffle"]
    lines = [
        "# Direct Symbol-Index Formula Search",
        "",
        "Generated by `direct_symbol_formula_search.py`.",
        "",
        "This pass tests direct formulas `f(a,b) -> symbol-order index` for the",
        "55 unordered pair cells. It does not use a key-to-symbol lookup, does",
        "not learn majority labels for feature groups, and does not produce or",
        "promote plaintext.",
        "",
        "Translation delta: `NONE`.",
        "",
        "## Search Space",
        "",
        f"- Source: `{FORMULA_JSON.relative_to(ROOT)}`.",
        f"- Pair cells: `{PAIR_COUNT}` unordered cells.",
        f"- Symbol alphabet: `{SIGMA}` (`{SYMBOL_COUNT}` symbols).",
        f"- Symbol orders tested: `{result['search_space']['symbol_order_count']}`.",
        f"- Formula attempts: `{result['search_space']['attempted_formula_count']}`.",
        f"- Unique prediction vectors: `{result['search_space']['unique_prediction_vector_count']}`.",
        "- Formula families: arithmetic affine, quadratic in `(a,b)`, and",
        "  digit-order distance affine over natural/lore digit orders.",
        "",
        "Conflict handling: unordered cell `19` is a known `I/N` conflict.",
        "Tables below rank by the stable primary label and also report",
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
        "| Hits | Acceptable | MDL/lookup | Order | Family | Formula | Leakage |",
        "|---:|---:|---:|---|---|---|---|",
    ]
    for row in result["observed"]["top_rows"][:20]:
        leakage = "yes" if row["target_label_leakage"] else "no"
        lines.append(
            f"| {row['primary_hits']}/55 | {row['acceptable_hits']}/55 | "
            f"{row['lookup_cost_ratio']:.3f} | `{row['symbol_order_id']}` | "
            f"`{row['family']}` | `{row['expression']}` | {leakage} |"
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
    if result["verdict"] == "candidate_direct_symbol_formula":
        lines.extend(
            [
                "A direct symbol-index formula passed the configured compression",
                "and control gates. This would still be mechanical only and would",
                "not imply plaintext.",
            ]
        )
    else:
        lines.extend(
            [
                "No tested direct formula qualifies as a candidate. The best row",
                "does not satisfy the required combination of below-lookup MDL and",
                "control performance. This preserves the prior conclusion that a",
                "compact original exact pair-cell placement remains unrecovered.",
            ]
        )
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    formula = load_json(FORMULA_JSON)
    targets = build_targets(formula)
    symbol_orders = build_symbol_orders(formula, targets)
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
        "schema": "direct_symbol_formula_results.v1",
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
            "raw_moduli": list(RAW_MODULI),
            "affine_coefs": list(AFFINE_COEFS),
            "quadratic_coefs": list(QUADRATIC_COEFS),
            "offsets_by_mod": {str(key): list(value) for key, value in OFFSETS_BY_MOD.items()},
            "lore_words": LORE_WORDS,
            "lore_digit_seeds": list(LORE_DIGIT_SEEDS),
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
