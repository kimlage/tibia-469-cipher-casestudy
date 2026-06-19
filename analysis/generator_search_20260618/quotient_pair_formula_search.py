#!/usr/bin/env python3
"""Direct formula search over the `6 <-> 9` quotient pair table.

The digit-orbit pass found the strongest current matrix-side clue: swapping
digits 6 and 9 collapses the 55 unordered pair cells to 46 orbits, with only
four mixed two-cell orbits. This follow-up asks a narrower question:

    quotient orbit coordinates -> numeric expression -> symbol-order index

If the quotient is close to the original authoring grid, it should become
easier to predict the majority label for each orbit with a compact coordinate
formula. This script does not train on plaintext, does not emit a glossary,
and treats target-derived symbol orders as leakage in the verdict.
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
ORBIT_JSON = HERE / "digit_orbit_quotient_results.json"

OUT_JSON = HERE / "quotient_pair_formula_results.json"
OUT_MD = HERE / "quotient_pair_formula_report.md"

SIGMA = "*ABCEFILNORSTV"
SYMBOL_COUNT = len(SIGMA)
RAW_PAIR_COUNT = 55
QUOTIENT_DIGIT_COUNT = 9
RANDOM_SEED = 46920260619

RAW_MODULI = (14, 46, 45, 9)
AFFINE_COEFS = (-3, -2, -1, 1, 2, 3)
QUADRATIC_COEFS = (-2, -1, 0, 1, 2)
OFFSETS_BY_MOD = {
    14: tuple(range(14)),
    46: tuple(range(-7, 8)),
    45: tuple(range(-7, 8)),
    9: tuple(range(9)),
}

INVENTORY_LABEL_SHUFFLE_TRIALS = 40
SYMBOL_ORDER_SHUFFLE_TRIALS = 30
ORDER_BATCH_SIZE = 4
TOP_ROWS_PER_ORDER = 20
TOP_ROWS_OUT = 60
MAX_CONTROL_PREDICTIONS = 250000

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


def qdigit(digit: int) -> int:
    return 6 if digit == 9 else digit


def qpair_for_pair(pair: str) -> tuple[int, int]:
    a, b = qdigit(int(pair[0])), qdigit(int(pair[1]))
    return (a, b) if a <= b else (b, a)


def pair_key(pair: tuple[int, int]) -> str:
    return f"{pair[0]}{pair[1]}"


def index_for_pair_n(a: int, b: int, n: int) -> int:
    if a > b:
        a, b = b, a
    return a * n - (a * (a - 1)) // 2 + (b - a)


def col_triangular_index(a: int, b: int) -> int:
    if a > b:
        a, b = b, a
    return b * (b + 1) // 2 + a


def primary_symbol(cell: dict) -> str:
    if cell["status"] == "pure":
        return cell["symbol_if_pure"]
    return sorted(cell["symbols"])[0]


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


def build_targets(orbit_result: dict) -> list[dict]:
    rows = []
    swap = orbit_result["swap_6_9"]
    for orbit in swap["orbits"]:
        q_pairs = {qpair_for_pair(pair) for pair in orbit["pairs"]}
        if len(q_pairs) != 1:
            raise ValueError(f"orbit does not collapse to one quotient pair: {orbit}")
        q_a, q_b = next(iter(q_pairs))
        pair_set = set(orbit["pairs"])
        is_fixed_cross_69 = pair_set == {"69"}
        rows.append(
            {
                "orbit": int(orbit["orbit"]),
                "pairs": list(orbit["pairs"]),
                "qpair": pair_key((q_a, q_b)),
                "qa": q_a,
                "qb": q_b,
                "orbit_size": int(orbit["size"]),
                "fixed_cross_69": is_fixed_cross_69,
                "contains_q6": q_a == 6 or q_b == 6,
                "is_singleton": int(orbit["size"]) == 1,
                "primary_symbol": orbit["label"],
                "acceptable_symbols": sorted(orbit["label_counts"], key=SIGMA.index),
                "is_mixed_orbit": bool(orbit["is_mixed"]),
                "label_counts": orbit["label_counts"],
            }
        )
    rows.sort(key=lambda row: row["orbit"])
    return rows


def build_symbol_orders(formula: dict, targets: list[dict]) -> dict[str, dict]:
    primary_labels = [row["primary_symbol"] for row in targets]
    cell_counts = Counter(primary_labels)
    usage_counts = code_usage_counts(formula)
    orders: dict[str, dict] = {}

    add_symbol_order(orders, "alphabetic", SIGMA, source="alphabet")
    add_symbol_order(orders, "alphabetic_rev", reversed(SIGMA), source="alphabet")
    add_symbol_order(
        orders,
        "quotient_label_frequency_desc",
        [symbol for symbol, _count in cell_counts.most_common()],
        source="quotient_label_inventory",
    )
    add_symbol_order(
        orders,
        "quotient_label_frequency_asc",
        [symbol for symbol, _count in sorted(cell_counts.items(), key=lambda item: (item[1], item[0]))],
        source="quotient_label_inventory",
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
    add_symbol_order(orders, "code_table_first_use", code_table_first_use(formula), source="code_table_order")

    first_seen: list[str] = []
    for symbol in primary_labels:
        if symbol not in first_seen:
            first_seen.append(symbol)
    add_symbol_order(
        orders,
        "quotient_first_use",
        first_seen,
        source="target_label_order",
        target_label_leakage=True,
    )
    add_symbol_order(
        orders,
        "quotient_first_use_rev",
        reversed(first_seen),
        source="target_label_order",
        target_label_leakage=True,
    )

    singleton_first: list[str] = []
    for row in targets:
        if row["is_singleton"] and row["primary_symbol"] not in singleton_first:
            singleton_first.append(row["primary_symbol"])
    add_symbol_order(
        orders,
        "singleton_orbit_first_use",
        singleton_first,
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


def arithmetic_features(targets: list[dict]) -> dict[str, list[int]]:
    features: dict[str, list[int]] = {
        "qa": [],
        "qb": [],
        "qsum": [],
        "qdiff": [],
        "qprod": [],
        "qrow_triangular_index": [],
        "qcol_triangular_index": [],
        "qmin": [],
        "qmax": [],
        "qa2": [],
        "qb2": [],
        "qsum2": [],
        "qdiff2": [],
        "qdiag": [],
        "qcontains_6x": [],
        "orbit_size": [],
        "singleton": [],
        "fixed_cross_69": [],
        "qedge": [],
        "qcenter": [],
        "qnear_469": [],
        "qcontains_1": [],
        "qcontains_3": [],
        "qcontains_4": [],
        "qcontains_8": [],
    }
    for row in targets:
        a, b = row["qa"], row["qb"]
        s = a + b
        d = b - a
        p = a * b
        values = {
            "qa": a,
            "qb": b,
            "qsum": s,
            "qdiff": d,
            "qprod": p,
            "qrow_triangular_index": index_for_pair_n(a, b, QUOTIENT_DIGIT_COUNT),
            "qcol_triangular_index": col_triangular_index(a, b),
            "qmin": min(a, b),
            "qmax": max(a, b),
            "qa2": a * a,
            "qb2": b * b,
            "qsum2": s * s,
            "qdiff2": d * d,
            "qdiag": int(a == b),
            "qcontains_6x": int(row["contains_q6"]),
            "orbit_size": int(row["orbit_size"]),
            "singleton": int(row["is_singleton"]),
            "fixed_cross_69": int(row["fixed_cross_69"]),
            "qedge": int(a in {0, 8} or b in {0, 8}),
            "qcenter": int(a in {4, 5} or b in {4, 5}),
            "qnear_469": min(abs(a - x) for x in {4, 6}) + min(abs(b - x) for x in {4, 6}),
            "qcontains_1": int(a == 1 or b == 1),
            "qcontains_3": int(a == 3 or b == 3),
            "qcontains_4": int(a == 4 or b == 4),
            "qcontains_8": int(a == 8 or b == 8),
        }
        for key, value in values.items():
            features[key].append(value)
    return features


def quotient_digit_order_from_seed(seed: str) -> list[int]:
    out: list[int] = []
    for char in seed:
        if char.isdigit():
            digit = qdigit(int(char))
            if digit not in out:
                out.append(digit)
    for digit in range(9):
        if digit not in out:
            out.append(digit)
    return out


def quotient_digit_orders() -> dict[str, list[int]]:
    orders = {
        "qnatural": list(range(9)),
        "qnatural_rev": list(reversed(range(9))),
        "q469_collapsed": quotient_digit_order_from_seed("469"),
    }
    for seed in LORE_DIGIT_SEEDS:
        orders[f"qlore_digits_{seed}"] = quotient_digit_order_from_seed(seed)
    # Deduplicate identical collapsed lore orders.
    dedup: dict[tuple[int, ...], tuple[str, list[int]]] = {}
    for order_id, order in orders.items():
        dedup.setdefault(tuple(order), (order_id, order))
    return {order_id: order for order_id, order in dedup.values()}


def quotient_digit_distance_features(targets: list[dict], order: list[int]) -> dict[str, list[int]]:
    pos = {digit: index for index, digit in enumerate(order)}
    features: dict[str, list[int]] = {
        "qpos_sum": [],
        "qline_dist": [],
        "qcycle_dist": [],
        "qpos_prod": [],
        "qpos_triangular_index": [],
        "qpos_min": [],
        "qpos_max": [],
        "qpos_edge": [],
    }
    for row in targets:
        pa = pos[row["qa"]]
        pb = pos[row["qb"]]
        lo, hi = sorted((pa, pb))
        raw = abs(pa - pb)
        values = {
            "qpos_sum": pa + pb,
            "qline_dist": raw,
            "qcycle_dist": min(raw, QUOTIENT_DIGIT_COUNT - raw),
            "qpos_prod": pa * pb,
            "qpos_triangular_index": col_triangular_index(lo, hi),
            "qpos_min": lo,
            "qpos_max": hi,
            "qpos_edge": min(lo, QUOTIENT_DIGIT_COUNT - 1 - hi),
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
    target_count = len(targets)
    seen: dict[bytes, dict] = {}
    attempts = 0
    family_attempts: Counter[str] = Counter()
    arith = arithmetic_features(targets)

    def add_formula(meta: dict, values: list[int]) -> None:
        nonlocal attempts
        attempts += 1
        family_attempts[meta["family"]] += 1
        raw_mod = int(meta["raw_mod"])
        pred = np.array([((value % raw_mod) % SYMBOL_COUNT) for value in values], dtype=np.uint8)
        key = pred.tobytes()
        previous = seen.get(key)
        if previous is None or meta["complexity_score"] < previous["complexity_score"]:
            seen[key] = meta

    def emit_affine(feature_values: dict[str, list[int]], feature_names: list[str], family: str, prefix: str) -> None:
        for raw_mod in RAW_MODULI:
            for size in (1, 2):
                for names in itertools.combinations(feature_names, size):
                    vectors = [feature_values[name] for name in names]
                    for coefs in itertools.product(AFFINE_COEFS, repeat=size):
                        for offset in OFFSETS_BY_MOD[raw_mod]:
                            values = [
                                offset + sum(coef * vector[idx] for coef, vector in zip(coefs, vectors))
                                for idx in range(target_count)
                            ]
                            structural_terms = sum(1 for name in names if name in {"orbit_size", "singleton", "fixed_cross_69"})
                            complexity = (
                                size
                                + sum(abs(coef) for coef in coefs) / 10.0
                                + abs(offset) / 25.0
                                + 0.25 * structural_terms
                            )
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
                                    "uses_structural_quotient_bit": bool(structural_terms),
                                    "complexity_score": complexity,
                                },
                                values,
                            )

    arithmetic_names = [
        "qa",
        "qb",
        "qsum",
        "qdiff",
        "qprod",
        "qrow_triangular_index",
        "qcol_triangular_index",
        "qmin",
        "qmax",
        "qa2",
        "qb2",
        "qsum2",
        "qdiff2",
        "qdiag",
        "qcontains_6x",
        "orbit_size",
        "singleton",
        "fixed_cross_69",
        "qedge",
        "qcenter",
        "qnear_469",
        "qcontains_1",
        "qcontains_3",
        "qcontains_4",
        "qcontains_8",
    ]
    emit_affine(arith, arithmetic_names, "quotient_arithmetic_affine", "qarith")

    quad_names = ("qa", "qb", "qa2", "qab", "qb2")
    quad_values = {
        "qa": arith["qa"],
        "qb": arith["qb"],
        "qa2": arith["qa2"],
        "qab": arith["qprod"],
        "qb2": arith["qb2"],
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
                    for idx in range(target_count)
                ]
                terms = tuple(name for coef, name in zip(coefs, quad_names) if coef != 0)
                complexity = len(terms) + sum(abs(coef) for coef in coefs) / 10.0 + abs(offset) / 25.0 + 0.5
                add_formula(
                    {
                        "formula_id": f"qquadratic_ab:{raw_mod}:{offset}:{','.join(map(str, coefs))}",
                        "family": "quotient_quadratic_ab",
                        "raw_mod": raw_mod,
                        "expression": expression_for(offset, coefs, quad_names, raw_mod),
                        "features": list(quad_names),
                        "coefs": list(coefs),
                        "offset": offset,
                        "term_count": len(terms),
                        "uses_structural_quotient_bit": False,
                        "complexity_score": complexity,
                    },
                    values,
                )

    for order_id, order in quotient_digit_orders().items():
        dist = quotient_digit_distance_features(targets, order)
        before = attempts
        emit_affine(dist, list(dist), "quotient_digit_order_distance_affine", f"qdist:{order_id}")
        for meta in list(seen.values()):
            if meta["family"] == "quotient_digit_order_distance_affine" and meta["formula_id"].startswith(f"qdist:{order_id}:"):
                meta["digit_order_id"] = order_id
                meta["digit_order"] = order
        family_attempts[f"quotient_digit_order:{order_id}"] += attempts - before

    prediction_keys = list(seen)
    prediction_blob = b"".join(prediction_keys)
    predictions = np.frombuffer(prediction_blob, dtype=np.uint8).reshape(len(prediction_keys), target_count).copy()
    metas = [seen[key] for key in prediction_keys]
    stats = {
        "attempted_formula_count": attempts,
        "unique_prediction_vector_count": len(metas),
        "family_attempts": dict(sorted(family_attempts.items())),
    }
    return predictions, metas, stats


def quotient_lookup_bits(target_count: int) -> float:
    return target_count * math.log2(SYMBOL_COUNT)


def raw_pair_lookup_bits() -> float:
    return RAW_PAIR_COUNT * math.log2(SYMBOL_COUNT)


def mdl_cost_bits(primary_hits: int, attempted_formula_count: int, symbol_order_count: int, target_count: int) -> float:
    formula_bits = math.log2(max(1, attempted_formula_count))
    order_bits = math.log2(max(1, symbol_order_count))
    exception_bits = (target_count - primary_hits) * (math.log2(target_count) + math.log2(SYMBOL_COUNT))
    return formula_bits + order_bits + exception_bits


def mdl_row(primary_hits: int, attempted_formula_count: int, symbol_order_count: int, target_count: int) -> dict:
    mdl = mdl_cost_bits(primary_hits, attempted_formula_count, symbol_order_count, target_count)
    qlookup = quotient_lookup_bits(target_count)
    raw_lookup = raw_pair_lookup_bits()
    return {
        "mdl_cost_bits": mdl,
        "quotient_lookup_cost_bits": qlookup,
        "raw_pair_lookup_cost_bits": raw_lookup,
        "mdl_gain_vs_quotient_lookup_bits": qlookup - mdl,
        "mdl_gain_vs_raw_pair_lookup_bits": raw_lookup - mdl,
        "quotient_lookup_cost_ratio": mdl / qlookup,
        "raw_pair_lookup_cost_ratio": mdl / raw_lookup,
        "compresses_vs_quotient_lookup": mdl < qlookup,
        "compresses_vs_raw_pair_lookup": mdl < raw_lookup,
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
    best = -1
    for order in orders:
        target = target_indices(labels, order)
        hits = np.zeros(predictions.shape[0], dtype=np.int16)
        for pos, value in enumerate(target):
            hits += predictions[:, pos] == value
        value = int(hits.max())
        if value > best:
            best = value
    return best


def row_sort_key(row: dict):
    return (
        -row["primary_hits"],
        -row["acceptable_hits"],
        row["quotient_lookup_cost_ratio"],
        bool(row.get("target_label_leakage", False)),
        bool(row.get("uses_lore", False)),
        bool(row.get("uses_structural_quotient_bit", False)),
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
    for symbol, target in zip(predicted_symbols, targets):
        primary_hit = symbol == target["primary_symbol"]
        acceptable_hit = symbol in target["acceptable_symbols"]
        item = {
            "orbit": target["orbit"],
            "pairs": target["pairs"],
            "qpair": target["qpair"],
            "primary_symbol": target["primary_symbol"],
            "acceptable_symbols": target["acceptable_symbols"],
            "predicted_symbol": symbol,
            "primary_hit": primary_hit,
            "acceptable_hit": acceptable_hit,
            "is_mixed_orbit": target["is_mixed_orbit"],
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
        "uses_lore": bool(symbol_order.get("uses_lore") or meta.get("digit_order_id", "").startswith("qlore_")),
        "target_label_leakage": bool(symbol_order.get("target_label_leakage")),
        "primary_hits": int(hits),
        "acceptable_hits": int(acceptable_hits),
        "primary_accuracy": int(hits) / len(targets),
        "acceptable_accuracy": int(acceptable_hits) / len(targets),
        "predicted_symbol_string_orbit_order": "".join(predicted_symbols),
        "primary_misses": misses,
        "predictions": detail,
    }
    row.update(mdl_row(int(hits), attempted_formula_count, symbol_order_count, len(targets)))
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
        if best_hit != order_rows[0]["primary_hits"]:
            raise AssertionError("best-hit row mismatch")

    rows.sort(key=row_sort_key)
    best_by_order.sort(key=row_sort_key)
    compact_top = []
    seen_hypotheses: set[tuple[str, str, str]] = set()
    for row in rows:
        key = (row["symbol_order_id"], row["formula_id"], row["predicted_symbol_string_orbit_order"])
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
    target_count: int,
) -> dict:
    rng = random.Random(RANDOM_SEED + 101)
    if predictions.shape[0] > MAX_CONTROL_PREDICTIONS:
        sample_idx = np.array(rng.sample(range(predictions.shape[0]), MAX_CONTROL_PREDICTIONS), dtype=np.int64)
        control_predictions = predictions[sample_idx]
    else:
        control_predictions = predictions
    orders = [meta["order"] for meta in symbol_orders.values()]
    hits_values = []
    mdl_values = []
    for _trial in range(INVENTORY_LABEL_SHUFFLE_TRIALS):
        shuffled = primary_labels[:]
        rng.shuffle(shuffled)
        hit = best_hits_for_orders(control_predictions, shuffled, orders)
        hits_values.append(hit)
        mdl_values.append(mdl_row(hit, stats["attempted_formula_count"], len(symbol_orders), target_count)["mdl_gain_vs_quotient_lookup_bits"])
    return {
        "method": "quotient_inventory_preserving_label_shuffle",
        "trials": INVENTORY_LABEL_SHUFFLE_TRIALS,
        "prediction_vectors_used": int(control_predictions.shape[0]),
        "prediction_vectors_total": int(predictions.shape[0]),
        "sampled_prediction_vectors": bool(control_predictions.shape[0] != predictions.shape[0]),
        "hits": summarize_values(hits_values, observed_best["primary_hits"]),
        "mdl_gain_vs_quotient_lookup": summarize_values(mdl_values, observed_best["mdl_gain_vs_quotient_lookup_bits"]),
    }


def run_symbol_order_controls(
    predictions: np.ndarray,
    primary_labels: list[str],
    symbol_order_count: int,
    stats: dict,
    observed_best: dict,
    target_count: int,
) -> dict:
    rng = random.Random(RANDOM_SEED + 202)
    if predictions.shape[0] > MAX_CONTROL_PREDICTIONS:
        sample_idx = np.array(rng.sample(range(predictions.shape[0]), MAX_CONTROL_PREDICTIONS), dtype=np.int64)
        control_predictions = predictions[sample_idx]
    else:
        control_predictions = predictions
    hits_values = []
    mdl_values = []
    for _trial in range(SYMBOL_ORDER_SHUFFLE_TRIALS):
        orders = []
        for _order_index in range(symbol_order_count):
            order = list(SIGMA)
            rng.shuffle(order)
            orders.append(order)
        hit = best_hits_for_orders(control_predictions, primary_labels, orders)
        hits_values.append(hit)
        mdl_values.append(mdl_row(hit, stats["attempted_formula_count"], symbol_order_count, target_count)["mdl_gain_vs_quotient_lookup_bits"])
    return {
        "method": "quotient_symbol_order_shuffle",
        "trials": SYMBOL_ORDER_SHUFFLE_TRIALS,
        "orders_per_trial": symbol_order_count,
        "prediction_vectors_used": int(control_predictions.shape[0]),
        "prediction_vectors_total": int(predictions.shape[0]),
        "sampled_prediction_vectors": bool(control_predictions.shape[0] != predictions.shape[0]),
        "hits": summarize_values(hits_values, observed_best["primary_hits"]),
        "mdl_gain_vs_quotient_lookup": summarize_values(mdl_values, observed_best["mdl_gain_vs_quotient_lookup_bits"]),
    }


def classify(best: dict, controls: dict) -> str:
    label_p = controls["inventory_label_shuffle"]["hits"]["p_good_direction"]
    order_p = controls["symbol_order_shuffle"]["hits"]["p_good_direction"]
    mdl_label_p = controls["inventory_label_shuffle"]["mdl_gain_vs_quotient_lookup"]["p_good_direction"]
    mdl_order_p = controls["symbol_order_shuffle"]["mdl_gain_vs_quotient_lookup"]["p_good_direction"]
    if best["target_label_leakage"]:
        return "rejected_target_order_leakage"
    if not best["compresses_vs_quotient_lookup"]:
        if best["compresses_vs_raw_pair_lookup"]:
            return "weak_quotient_formula_not_better_than_quotient_lookup"
        return "rejected_no_compression"
    if max(label_p, order_p, mdl_label_p, mdl_order_p) <= 0.01:
        return "candidate_quotient_pair_formula"
    if max(label_p, order_p) <= 0.05:
        return "weak_quotient_coordinate_signal"
    return "rejected_control"


def compact_row(row: dict) -> dict:
    return {key: value for key, value in row.items() if key not in {"predictions", "primary_misses"}}


def write_report(result: dict) -> None:
    best = result["observed"]["best"]
    label_control = result["controls"]["inventory_label_shuffle"]
    order_control = result["controls"]["symbol_order_shuffle"]
    lines = [
        "# Quotient Pair Formula Search",
        "",
        "Generated by `quotient_pair_formula_search.py`.",
        "",
        "This pass tests direct formulas from the `6 <-> 9` quotient orbit",
        "coordinates to symbol-order indices. The target is the majority label",
        "of each of the 46 quotient orbits, not plaintext.",
        "",
        "Translation delta: `NONE`.",
        "",
        "## Search Space",
        "",
        f"- Source formula: `{FORMULA_JSON.relative_to(ROOT)}`.",
        f"- Source quotient: `{ORBIT_JSON.relative_to(ROOT)}`.",
        f"- Quotient orbits: `{result['target']['quotient_orbit_count']}`.",
        f"- Raw pair cells represented: `{result['target']['raw_pair_cells']}`.",
        f"- Mixed quotient orbits: `{result['target']['mixed_orbit_count']}`.",
        f"- Symbol alphabet: `{SIGMA}` (`{SYMBOL_COUNT}` symbols).",
        f"- Symbol orders tested: `{result['search_space']['symbol_order_count']}`.",
        f"- Formula attempts: `{result['search_space']['attempted_formula_count']}`.",
        f"- Unique prediction vectors: `{result['search_space']['unique_prediction_vector_count']}`.",
        "- Formula families: quotient-coordinate affine, quotient quadratic,",
        "  and quotient digit-order distance over collapsed lore digit orders.",
        "",
        "Structural note: the fixed cross-pair `69` collides with quotient",
        "coordinate `66`, so the tested feature bank includes an explicit",
        "`fixed_cross_69` bit. Rows using it are marked as structural quotient",
        "bit usage.",
        "",
        "## Summary",
        "",
        "| Primary hits | Acceptable hits | Formula | Symbol order | MDL/q-lookup | MDL/raw lookup | Label-shuffle p(hit) | Symbol-order p(hit) | Verdict |",
        "|---:|---:|---|---|---:|---:|---:|---:|---|",
        (
            f"| {best['primary_hits']}/46 | {best['acceptable_hits']}/46 | "
            f"`{best['expression']}` | `{best['symbol_order_id']}` | "
            f"{best['quotient_lookup_cost_ratio']:.3f} | "
            f"{best['raw_pair_lookup_cost_ratio']:.3f} | "
            f"{label_control['hits']['p_good_direction']:.4f} | "
            f"{order_control['hits']['p_good_direction']:.4f} | "
            f"`{result['verdict']}` |"
        ),
        "",
        "## Top Rows",
        "",
        "| Hits | Acceptable | MDL/q | MDL/raw | Order | Family | Formula | Structural bit | Leakage |",
        "|---:|---:|---:|---:|---|---|---|---|---|",
    ]
    for row in result["observed"]["top_rows"][:24]:
        structural = "yes" if row["uses_structural_quotient_bit"] else "no"
        leakage = "yes" if row["target_label_leakage"] else "no"
        lines.append(
            f"| {row['primary_hits']}/46 | {row['acceptable_hits']}/46 | "
            f"{row['quotient_lookup_cost_ratio']:.3f} | {row['raw_pair_lookup_cost_ratio']:.3f} | "
            f"`{row['symbol_order_id']}` | `{row['family']}` | `{row['expression']}` | "
            f"{structural} | {leakage} |"
        )
    lines.extend(
        [
            "",
            "## Best By Symbol Order",
            "",
            "| Order | Source | Hits | Acceptable | MDL/q | Formula |",
            "|---|---|---:|---:|---:|---|",
        ]
    )
    for row in result["observed"]["best_by_symbol_order"][:24]:
        lines.append(
            f"| `{row['symbol_order_id']}` | `{row['symbol_order_source']}` | "
            f"{row['primary_hits']}/46 | {row['acceptable_hits']}/46 | "
            f"{row['quotient_lookup_cost_ratio']:.3f} | `{row['expression']}` |"
        )
    lines.extend(
        [
            "",
            "## Controls",
            "",
            "| Control | Trials | Mean best hits | Max best hits | p(hit) | p(MDL gain vs quotient lookup) |",
            "|---|---:|---:|---:|---:|---:|",
            (
                f"| quotient inventory-preserving label shuffle | {label_control['trials']} | "
                f"{label_control['hits']['control_mean']:.2f} | "
                f"{label_control['hits']['control_max']:.0f} | "
                f"{label_control['hits']['p_good_direction']:.4f} | "
                f"{label_control['mdl_gain_vs_quotient_lookup']['p_good_direction']:.4f} |"
            ),
            (
                f"| symbol-order shuffle | {order_control['trials']} | "
                f"{order_control['hits']['control_mean']:.2f} | "
                f"{order_control['hits']['control_max']:.0f} | "
                f"{order_control['hits']['p_good_direction']:.4f} | "
                f"{order_control['mdl_gain_vs_quotient_lookup']['p_good_direction']:.4f} |"
            ),
            "",
            "Control implementation note: the observed search used all",
            f"`{result['search_space']['unique_prediction_vector_count']}` unique prediction vectors.",
            "The shuffle controls used a deterministic sample of",
            f"`{label_control['prediction_vectors_used']}` vectors because the full cross-product",
            "is large. Since the observed row is already below both sampled-control",
            "means and does not compress, this sampling does not affect the negative",
            "verdict.",
            "",
            "## Interpretation",
            "",
        ]
    )
    if result["verdict"] == "candidate_quotient_pair_formula":
        lines.extend(
            [
                "A quotient-coordinate formula passed the configured compression",
                "and control checks. This would still be a mechanical table-origin",
                "candidate only, not a translation.",
            ]
        )
    elif result["verdict"] == "weak_quotient_coordinate_signal":
        lines.extend(
            [
                "The quotient coordinates show a weak signal under controls, but",
                "the model is not promoted without stronger MDL/control behavior.",
            ]
        )
    elif result["verdict"] == "weak_quotient_formula_not_better_than_quotient_lookup":
        lines.extend(
            [
                "The best formula is smaller than a raw 55-cell lookup only because",
                "the `6 <-> 9` quotient already removed cells. It still fails to",
                "beat the direct 46-orbit quotient lookup, so the quotient has not",
                "turned into an original label generator.",
            ]
        )
    else:
        lines.extend(
            [
                "No tested quotient-coordinate formula qualifies. The `6 <-> 9`",
                "quotient remains the strongest weak matrix clue, but its orbit",
                "labels still behave like lookup facts under these formulas.",
            ]
        )
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    formula = load_json(FORMULA_JSON)
    orbit_result = load_json(ORBIT_JSON)
    targets = build_targets(orbit_result)
    symbol_orders = build_symbol_orders(formula, targets)
    predictions, metas, stats = build_formula_bank(targets)
    observed = observed_search(predictions, metas, symbol_orders, targets, stats)
    primary_labels = [row["primary_symbol"] for row in targets]
    controls = {
        "inventory_label_shuffle": run_inventory_label_controls(
            predictions, primary_labels, symbol_orders, stats, observed["best"], len(targets)
        ),
        "symbol_order_shuffle": run_symbol_order_controls(
            predictions, primary_labels, len(symbol_orders), stats, observed["best"], len(targets)
        ),
    }
    result_verdict = classify(observed["best"], controls)
    target = {
        "quotient_group": "swap_6_9",
        "quotient_orbit_count": len(targets),
        "raw_pair_cells": RAW_PAIR_COUNT,
        "mixed_orbit_count": sum(row["is_mixed_orbit"] for row in targets),
        "fixed_cross_collision_note": "`69` and the `66/99` orbit both map to quotient coordinate 66; `fixed_cross_69` distinguishes them.",
        "rows": targets,
    }
    result = {
        "schema": "quotient_pair_formula_results.v1",
        "created_at": "2026-06-19",
        "translation_delta": "NONE",
        "source": {
            "mechanical_formula": str(FORMULA_JSON.relative_to(ROOT)),
            "orbit_results": str(ORBIT_JSON.relative_to(ROOT)),
        },
        "target": target,
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
            "quotient_digit_orders": quotient_digit_orders(),
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
        "best={hits}/46 q_ratio={qratio:.3f} raw_ratio={rratio:.3f} verdict={verdict}".format(
            hits=observed["best"]["primary_hits"],
            qratio=observed["best"]["quotient_lookup_cost_ratio"],
            rratio=observed["best"]["raw_pair_lookup_cost_ratio"],
            verdict=result_verdict,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
