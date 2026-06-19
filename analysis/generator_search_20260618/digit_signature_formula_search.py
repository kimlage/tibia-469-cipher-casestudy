#!/usr/bin/env python3
"""Digit-signature formula search for the 55 unordered 469 pair cells.

This pass tests a deliberately narrow generator hypothesis:

    digit -> small row/column signature -> auditable pair combination -> symbol

The signatures are derived from the pair table itself: incident-symbol
marginals, diagonal labels, frequent-symbol incidence, and tape/first-use
features when the compiled tape formula is available. Candidate formulas are
not allowed to store a pair->symbol lookup. A diagnostic partition model may
store labels for signature buckets, but it is MDL-penalized as a bucket label
table and explicitly marked lookup-like when it degenerates.

Mechanical only. No plaintext is promoted.
"""

from __future__ import annotations

import json
import math
import random
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from itertools import combinations, product
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
FORMULA_JSON = HERE / "tape_based_formula_469.json"
OUT_JSON = HERE / "digit_signature_formula_results.json"
OUT_MD = HERE / "digit_signature_formula_report.md"

RANDOM_SEED = 46920260619
CONTROL_TRIALS = 100
TOP_SYMBOL_LIMIT = 4

COEFS = (-1, 1)
OFFSETS = tuple(range(14))
SYMBOL_ALPHABET = "*ABCEFILNORSTV"


def all_pairs() -> list[str]:
    return [f"{a}{b}" for a in range(10) for b in range(a, 10)]


PAIRS = all_pairs()
PAIR_COUNT = len(PAIRS)
PAIR_TO_INDEX = {pair: index for index, pair in enumerate(PAIRS)}
LOG2 = math.log(2)


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def primary_symbol(cell: dict[str, Any]) -> str:
    if cell["status"] == "pure":
        return str(cell["symbol_if_pure"])
    return sorted(cell["symbols"])[0]


def entropy(labels: list[str]) -> float:
    counts = Counter(labels)
    total = len(labels)
    if total == 0:
        return 0.0
    return -sum((count / total) * math.log2(count / total) for count in counts.values())


def bits_choose(n: int, k: int) -> float:
    if k < 0 or k > n:
        return float("inf")
    if k == 0 or k == n:
        return 0.0
    return (math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)) / LOG2


def multinomial_bits(counts: Counter[str]) -> float:
    total = sum(counts.values())
    return (math.lgamma(total + 1) - sum(math.lgamma(count + 1) for count in counts.values())) / LOG2


def residual_bits(error_count: int, symbol_count: int) -> float:
    if error_count == 0:
        return 0.0
    return bits_choose(PAIR_COUNT, error_count) + error_count * math.log2(symbol_count)


def bucket_count(value: int) -> int:
    if value <= 0:
        return 0
    if value == 1:
        return 1
    if value == 2:
        return 2
    if value <= 4:
        return 3
    if value <= 8:
        return 4
    if value <= 16:
        return 5
    return 6


def sanitize_symbol(symbol: str) -> str:
    return "star" if symbol == "*" else symbol.lower()


def normalize_order(symbols: list[str], full_symbols: list[str]) -> list[str]:
    out: list[str] = []
    for symbol in symbols:
        if symbol in full_symbols and symbol not in out:
            out.append(symbol)
    for symbol in full_symbols:
        if symbol not in out:
            out.append(symbol)
    return out


def target_labels(formula: dict[str, Any]) -> tuple[dict[str, str], dict[str, set[str]]]:
    labels: dict[str, str] = {}
    acceptable: dict[str, set[str]] = {}
    for pair in PAIRS:
        cell = formula["pair_table"][pair]
        labels[pair] = primary_symbol(cell)
        acceptable[pair] = set(cell["symbols"])
    return labels, acceptable


def token_tape_stats(formula: dict[str, Any]) -> dict[str, Any]:
    pair_stats = {
        pair: {
            "total_tokens": 0,
            "tape_tokens": 0,
            "omitted_zero_tokens": 0,
            "first_observed": 999999,
            "first_tape_component": 99,
            "first_tape_start": 9999,
        }
        for pair in PAIRS
    }
    digit_stats = {
        str(digit): {
            "total_tokens": 0,
            "tape_tokens": 0,
            "omitted_zero_tokens": 0,
            "first_observed": 999999,
            "first_tape_component": 99,
            "first_tape_start": 9999,
        }
        for digit in range(10)
    }
    notes: list[str] = []
    try:
        sys.path.insert(0, str(HERE))
        import tape_tokenization_analysis as tape_tokens  # type: ignore

        component_order = {row["id"]: index for index, row in enumerate(formula["tape_components"])}
        books, segment_maps = tape_tokens.reconstruct_books(formula)
        token_maps = tape_tokens.align_tokens(books)
        projected = tape_tokens.project_tokens(token_maps, segment_maps)
        for row in projected:
            pair = row["pair_key"]
            if pair not in pair_stats:
                continue
            observed_key = int(row["book"]) * 10000 + int(row["token_index"])
            pair_stats[pair]["total_tokens"] += 1
            pair_stats[pair]["first_observed"] = min(pair_stats[pair]["first_observed"], observed_key)
            digit_chars = set(pair)
            for digit in digit_chars:
                digit_stats[digit]["total_tokens"] += 1
                digit_stats[digit]["first_observed"] = min(digit_stats[digit]["first_observed"], observed_key)
            if row["omitted_zero"]:
                pair_stats[pair]["omitted_zero_tokens"] += 1
                for digit in digit_chars:
                    digit_stats[digit]["omitted_zero_tokens"] += 1
            if row["mapped_to_tape"]:
                component = component_order[row["component_id"]]
                start = int(row["component_start"])
                pair_stats[pair]["tape_tokens"] += 1
                if (component, start) < (
                    pair_stats[pair]["first_tape_component"],
                    pair_stats[pair]["first_tape_start"],
                ):
                    pair_stats[pair]["first_tape_component"] = component
                    pair_stats[pair]["first_tape_start"] = start
                for digit in digit_chars:
                    digit_stats[digit]["tape_tokens"] += 1
                    if (component, start) < (
                        digit_stats[digit]["first_tape_component"],
                        digit_stats[digit]["first_tape_start"],
                    ):
                        digit_stats[digit]["first_tape_component"] = component
                        digit_stats[digit]["first_tape_start"] = start
        notes.append("tape_tokenization_analysis projection succeeded")
        available = True
    except Exception as exc:  # pragma: no cover - report path, not expected path
        notes.append(f"tape projection unavailable: {exc}")
        available = False
    return {"available": available, "pair": pair_stats, "digit": digit_stats, "notes": notes}


def code_usage_order(formula: dict[str, Any], full_symbols: list[str], reverse: bool = False) -> list[str]:
    counts: Counter[str] = Counter()
    for code, count in formula["code_counts"].items():
        symbol = formula["code_to_symbol"].get(code)
        if symbol is not None:
            counts[symbol] += int(count)
    rows = sorted(((counts[symbol], symbol) for symbol in full_symbols), reverse=reverse)
    if reverse:
        return [symbol for _count, symbol in rows]
    return [symbol for _count, symbol in sorted(rows, key=lambda item: (-item[0], item[1]))]


def build_symbol_orders(
    labels: dict[str, str],
    formula: dict[str, Any],
    tape_stats: dict[str, Any],
    full_symbols: list[str],
) -> dict[str, list[str]]:
    cell_counts = Counter(labels.values())
    first_seen = [labels[pair] for pair in PAIRS]
    diagonal_seen = [labels[f"{digit}{digit}"] for digit in range(10)]
    tape_seen = [
        labels[pair]
        for pair in sorted(
            PAIRS,
            key=lambda pair: (
                tape_stats["pair"][pair]["first_tape_component"],
                tape_stats["pair"][pair]["first_tape_start"],
                tape_stats["pair"][pair]["first_observed"],
                pair,
            ),
        )
    ]
    orders = {
        "alphabetic": normalize_order(list(SYMBOL_ALPHABET), full_symbols),
        "alphabetic_rev": normalize_order(list(reversed(SYMBOL_ALPHABET)), full_symbols),
        "cell_frequency_desc": normalize_order(
            [symbol for symbol, _count in sorted(cell_counts.items(), key=lambda item: (-item[1], item[0]))],
            full_symbols,
        ),
        "cell_frequency_asc": normalize_order(
            [symbol for symbol, _count in sorted(cell_counts.items(), key=lambda item: (item[1], item[0]))],
            full_symbols,
        ),
        "code_usage_desc": normalize_order(code_usage_order(formula, full_symbols), full_symbols),
        "code_usage_asc": normalize_order(list(reversed(code_usage_order(formula, full_symbols))), full_symbols),
        "cell_first_use": normalize_order(first_seen, full_symbols),
        "diagonal_first_use": normalize_order(diagonal_seen, full_symbols),
        "tape_first_use": normalize_order(tape_seen, full_symbols),
    }
    deduped: dict[str, list[str]] = {}
    seen: set[tuple[str, ...]] = set()
    for order_id, order in orders.items():
        key = tuple(order)
        if key not in seen:
            deduped[order_id] = order
            seen.add(key)
    return deduped


def top_symbols_from_labels(labels: dict[str, str]) -> list[str]:
    counts = Counter(labels.values())
    return [symbol for symbol, _count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:TOP_SYMBOL_LIMIT]]


def build_digit_signatures(
    labels: dict[str, str],
    tape_stats: dict[str, Any],
    full_symbols: list[str],
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    top_symbols = top_symbols_from_labels(labels)
    cell_counts = Counter(labels.values())
    frequency_order = [symbol for symbol, _count in sorted(cell_counts.items(), key=lambda item: (-item[1], item[0]))]
    for symbol in full_symbols:
        if symbol not in frequency_order:
            frequency_order.append(symbol)
    symbol_rank = {symbol: index for index, symbol in enumerate(frequency_order)}
    signatures: dict[str, dict[str, Any]] = {}
    for digit in range(10):
        d = str(digit)
        incident = [pair for pair in PAIRS if d in pair]
        incident_labels = [labels[pair] for pair in incident]
        counts = Counter(incident_labels)
        top1_symbol, top1_count = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0]
        diag_symbol = labels[f"{digit}{digit}"]
        top_mask = 0
        strong_mask = 0
        top_counts: dict[str, int] = {}
        for bit, symbol in enumerate(top_symbols):
            count = counts.get(symbol, 0)
            top_counts[symbol] = count
            if count:
                top_mask |= 1 << bit
            if count >= 2:
                strong_mask |= 1 << bit
        tape_digit = tape_stats["digit"][d]
        signatures[d] = {
            "digit": digit,
            "incident_pairs": len(incident),
            "diag_symbol": diag_symbol,
            "diag_rank": symbol_rank[diag_symbol],
            "top1_symbol": top1_symbol,
            "top1_rank": symbol_rank[top1_symbol],
            "top1_count": top1_count,
            "distinct_symbols": len(counts),
            "entropy_bin": int(round(entropy(incident_labels) * 3)),
            "top_mask": top_mask,
            "strong_mask": strong_mask,
            "top_counts": top_counts,
            "first_observed_bin": min(99, int(tape_digit["first_observed"]) // 10000),
            "first_tape_component": int(tape_digit["first_tape_component"]),
            "first_tape_start_bin": min(99, int(tape_digit["first_tape_start"]) // 25),
            "total_token_bucket": bucket_count(int(tape_digit["total_tokens"])),
            "tape_token_bucket": bucket_count(int(tape_digit["tape_tokens"])),
            "omitted_zero_bucket": bucket_count(int(tape_digit["omitted_zero_tokens"])),
        }
    return signatures, top_symbols


def triangular_index(a: int, b: int) -> int:
    return a * 10 - (a * (a - 1)) // 2 + (b - a)


def build_pair_features(
    labels: dict[str, str],
    digit_signatures: dict[str, dict[str, Any]],
    top_symbols: list[str],
    tape_stats: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    features: dict[str, dict[str, Any]] = {}
    for pair in PAIRS:
        a = int(pair[0])
        b = int(pair[1])
        da = digit_signatures[str(a)]
        db = digit_signatures[str(b)]
        pstats = tape_stats["pair"][pair]
        row: dict[str, Any] = {
            "a": a,
            "b": b,
            "sum": a + b,
            "diff": b - a,
            "prod": a * b,
            "triangular": triangular_index(a, b),
            "diagonal": int(a == b),
            "has_zero": int(a == 0 or b == 0),
            "has_nine": int(a == 9 or b == 9),
            "same_parity": int((a % 2) == (b % 2)),
            "sum_mod3": (a + b) % 3,
            "diag_rank_sum": int(da["diag_rank"]) + int(db["diag_rank"]),
            "diag_rank_absdiff": abs(int(da["diag_rank"]) - int(db["diag_rank"])),
            "diag_rank_min": min(int(da["diag_rank"]), int(db["diag_rank"])),
            "diag_rank_max": max(int(da["diag_rank"]), int(db["diag_rank"])),
            "diag_same": int(da["diag_symbol"] == db["diag_symbol"]),
            "top1_rank_sum": int(da["top1_rank"]) + int(db["top1_rank"]),
            "top1_rank_absdiff": abs(int(da["top1_rank"]) - int(db["top1_rank"])),
            "top1_count_sum": int(da["top1_count"]) + int(db["top1_count"]),
            "top1_same": int(da["top1_symbol"] == db["top1_symbol"]),
            "distinct_sum": int(da["distinct_symbols"]) + int(db["distinct_symbols"]),
            "entropy_bin_sum": int(da["entropy_bin"]) + int(db["entropy_bin"]),
            "entropy_bin_absdiff": abs(int(da["entropy_bin"]) - int(db["entropy_bin"])),
            "top_mask_or": int(da["top_mask"]) | int(db["top_mask"]),
            "top_mask_and": int(da["top_mask"]) & int(db["top_mask"]),
            "strong_mask_or": int(da["strong_mask"]) | int(db["strong_mask"]),
            "strong_mask_and": int(da["strong_mask"]) & int(db["strong_mask"]),
            "first_observed_bin_sum": int(da["first_observed_bin"]) + int(db["first_observed_bin"]),
            "first_observed_bin_absdiff": abs(int(da["first_observed_bin"]) - int(db["first_observed_bin"])),
            "first_tape_component_sum": int(da["first_tape_component"]) + int(db["first_tape_component"]),
            "first_tape_component_absdiff": abs(
                int(da["first_tape_component"]) - int(db["first_tape_component"])
            ),
            "first_tape_start_bin_sum": int(da["first_tape_start_bin"]) + int(db["first_tape_start_bin"]),
            "first_tape_start_bin_absdiff": abs(
                int(da["first_tape_start_bin"]) - int(db["first_tape_start_bin"])
            ),
            "digit_total_token_bucket_sum": int(da["total_token_bucket"]) + int(db["total_token_bucket"]),
            "digit_tape_token_bucket_sum": int(da["tape_token_bucket"]) + int(db["tape_token_bucket"]),
            "digit_omitted_zero_bucket_sum": int(da["omitted_zero_bucket"]) + int(db["omitted_zero_bucket"]),
            "pair_total_token_bucket": bucket_count(int(pstats["total_tokens"])),
            "pair_tape_token_bucket": bucket_count(int(pstats["tape_tokens"])),
            "pair_omitted_zero_bucket": bucket_count(int(pstats["omitted_zero_tokens"])),
            "pair_first_observed_bin": min(99, int(pstats["first_observed"]) // 10000),
            "pair_first_tape_component": int(pstats["first_tape_component"]),
            "pair_first_tape_start_bin": min(99, int(pstats["first_tape_start"]) // 25),
            "diag_symbols_sorted": "|".join(sorted([str(da["diag_symbol"]), str(db["diag_symbol"])])),
            "top1_symbols_sorted": "|".join(sorted([str(da["top1_symbol"]), str(db["top1_symbol"])])),
            "target_label": labels[pair],
        }
        for symbol in top_symbols:
            key = sanitize_symbol(symbol)
            ca = int(da["top_counts"][symbol])
            cb = int(db["top_counts"][symbol])
            row[f"inc_{key}_sum"] = ca + cb
            row[f"inc_{key}_absdiff"] = abs(ca - cb)
            row[f"inc_{key}_min"] = min(ca, cb)
        features[pair] = row
    return features


def numeric_feature_names(top_symbols: list[str]) -> list[str]:
    names = [
        "sum",
        "diff",
        "triangular",
        "diagonal",
        "has_zero",
        "diag_rank_sum",
        "diag_rank_absdiff",
        "diag_same",
        "top1_rank_sum",
        "top1_rank_absdiff",
        "top1_same",
        "distinct_sum",
        "top_mask_or",
        "strong_mask_or",
        "first_tape_component_sum",
        "first_tape_component_absdiff",
        "pair_tape_token_bucket",
        "pair_first_tape_component",
    ]
    for symbol in top_symbols:
        key = sanitize_symbol(symbol)
        names.append(f"inc_{key}_sum")
    return names


def expression(offset: int, coefs: tuple[int, ...], names: tuple[str, ...]) -> str:
    terms = [str(offset)]
    terms.extend(f"{coef:+d}*{name}" for coef, name in zip(coefs, names))
    return f"({' '.join(terms)}) mod 14"


def build_index_formula_bank(features: dict[str, dict[str, Any]], names: list[str]) -> list[dict[str, Any]]:
    seen: dict[bytes, dict[str, Any]] = {}
    vectors = {name: [int(features[pair][name]) for pair in PAIRS] for name in names}
    attempts = 0
    for size in (1, 2):
        for feature_names in combinations(names, size):
            feature_vectors = [vectors[name] for name in feature_names]
            for coefs in product(COEFS, repeat=size):
                for offset in OFFSETS:
                    attempts += 1
                    indices = bytes(
                        (offset + sum(coef * vector[idx] for coef, vector in zip(coefs, feature_vectors))) % 14
                        for idx in range(PAIR_COUNT)
                    )
                    complexity = size + sum(abs(coef) for coef in coefs) / 10.0 + offset / 25.0
                    meta = {
                        "family": "signature_index_formula",
                        "formula_id": f"idx:{offset}:{','.join(map(str, coefs))}:{','.join(feature_names)}",
                        "expression": expression(offset, coefs, feature_names),
                        "features": list(feature_names),
                        "coefs": list(coefs),
                        "offset": offset,
                        "term_count": size,
                        "complexity_score": complexity,
                    }
                    previous = seen.get(indices)
                    if previous is None or complexity < previous["complexity_score"]:
                        seen[indices] = meta
    rows = [{"indices": indices, "_index_masks": index_masks(indices), **meta} for indices, meta in seen.items()]
    rows.sort(key=lambda row: (row["term_count"], row["complexity_score"], row["formula_id"]))
    for row in rows:
        row["search_attempts_before_dedup"] = attempts
        row["unique_index_vector_count"] = len(rows)
    return rows


def target_masks(acceptable: dict[str, set[str]], full_symbols: list[str]) -> dict[str, int]:
    masks = {symbol: 0 for symbol in full_symbols}
    for index, pair in enumerate(PAIRS):
        for symbol in acceptable[pair]:
            masks[symbol] |= 1 << index
    return masks


def single_label_masks(labels: dict[str, str], full_symbols: list[str]) -> dict[str, int]:
    masks = {symbol: 0 for symbol in full_symbols}
    for index, pair in enumerate(PAIRS):
        masks[labels[pair]] |= 1 << index
    return masks


def index_masks(indices: bytes) -> list[int]:
    masks = [0] * 14
    for position, value in enumerate(indices):
        masks[value] |= 1 << position
    return masks


def predictions_from_indices(indices: bytes, order: list[str]) -> dict[str, str]:
    return {pair: order[indices[index]] for index, pair in enumerate(PAIRS)}


def evaluate_index_formulas(
    labels: dict[str, str],
    acceptable: dict[str, set[str]],
    formula_bank: list[dict[str, Any]],
    orders: dict[str, list[str]],
    full_symbols: list[str],
    include_details: bool = True,
) -> dict[str, Any]:
    primary_masks = single_label_masks(labels, full_symbols)
    acceptable_masks = target_masks(acceptable, full_symbols)
    candidate_count = len(formula_bank) * len(orders)
    model_bits = math.log2(candidate_count) if candidate_count else 0.0
    best_accuracy: dict[str, Any] | None = None
    best_mdl: dict[str, Any] | None = None
    top_rows: list[dict[str, Any]] = []

    for row in formula_bank:
        imasks = row["_index_masks"]
        for order_id, order in orders.items():
            primary_correct = sum((imasks[idx] & primary_masks[order[idx]]).bit_count() for idx in range(14))
            accepted_correct = sum((imasks[idx] & acceptable_masks[order[idx]]).bit_count() for idx in range(14))
            primary_errors = PAIR_COUNT - primary_correct
            accepted_errors = PAIR_COUNT - accepted_correct
            mdl_bits = model_bits + residual_bits(primary_errors, len(full_symbols))
            result = {
                **{key: value for key, value in row.items() if key != "indices" and not key.startswith("_")},
                "symbol_order_id": order_id,
                "symbol_order": order,
                "primary_correct": primary_correct,
                "primary_errors": primary_errors,
                "accepted_correct": accepted_correct,
                "accepted_errors": accepted_errors,
                "model_bits": model_bits,
                "residual_bits": residual_bits(primary_errors, len(full_symbols)),
                "mdl_bits": mdl_bits,
                "candidate_count": candidate_count,
            }
            accuracy_key = (
                accepted_correct,
                primary_correct,
                -mdl_bits,
                -row["complexity_score"],
                row["formula_id"],
                order_id,
            )
            if best_accuracy is None or accuracy_key > best_accuracy["_sort_key"]:
                best_accuracy = {**result, "_sort_key": accuracy_key, "_indices": row["indices"]}
            mdl_key = (mdl_bits, primary_errors, accepted_errors, row["complexity_score"], row["formula_id"], order_id)
            if best_mdl is None or mdl_key < best_mdl["_sort_key"]:
                best_mdl = {**result, "_sort_key": mdl_key, "_indices": row["indices"]}
            if include_details and (len(top_rows) < 20 or accuracy_key > top_rows[-1]["_sort_key"]):
                top_rows.append({**result, "_sort_key": accuracy_key})
                top_rows.sort(key=lambda item: item["_sort_key"], reverse=True)
                top_rows = top_rows[:20]

    assert best_accuracy is not None and best_mdl is not None
    mismatches = []
    if include_details:
        best_predictions = predictions_from_indices(best_accuracy["_indices"], best_accuracy["symbol_order"])
        mismatches = [
            {
                "pair": pair,
                "target": labels[pair],
                "acceptable": sorted(acceptable[pair]),
                "predicted": best_predictions[pair],
            }
            for pair in PAIRS
            if best_predictions[pair] not in acceptable[pair]
        ]
    for item in (best_accuracy, best_mdl):
        item.pop("_sort_key", None)
        item.pop("_indices", None)
    for item in top_rows:
        item.pop("_sort_key", None)
    return {
        "best_accuracy": best_accuracy,
        "best_mdl": best_mdl,
        "top_accuracy_rows": top_rows,
        "best_accuracy_mismatches": mismatches,
    }


PARTITION_FEATURE_SETS = [
    ("diag_symbols_sorted",),
    ("top1_symbols_sorted",),
    ("top_mask_or",),
    ("strong_mask_or",),
    ("diag_rank_sum", "diag_rank_absdiff"),
    ("top1_rank_sum", "top1_rank_absdiff"),
    ("top_mask_or", "strong_mask_or"),
    ("diag_symbols_sorted", "top1_symbols_sorted"),
    ("diag_rank_sum", "top_mask_or"),
    ("top1_rank_sum", "top_mask_or"),
    ("entropy_bin_sum", "distinct_sum"),
    ("first_tape_component_sum", "first_tape_start_bin_sum"),
    ("pair_first_tape_component", "pair_first_tape_start_bin"),
    ("pair_total_token_bucket", "pair_tape_token_bucket"),
    ("diag_symbols_sorted", "top_mask_or", "strong_mask_or"),
    ("top1_symbols_sorted", "top_mask_or", "pair_tape_token_bucket"),
    ("diag_rank_sum", "diag_rank_absdiff", "top_mask_or"),
    ("top1_rank_sum", "top1_rank_absdiff", "strong_mask_or"),
    ("first_observed_bin_sum", "pair_first_observed_bin", "top_mask_or"),
]


def majority_label(pairs: list[str], labels: dict[str, str]) -> str:
    return sorted(Counter(labels[pair] for pair in pairs).items(), key=lambda item: (-item[1], item[0]))[0][0]


def evaluate_partition_models(
    labels: dict[str, str],
    acceptable: dict[str, set[str]],
    features: dict[str, dict[str, Any]],
    full_symbols: list[str],
) -> dict[str, Any]:
    best_accuracy: dict[str, Any] | None = None
    best_mdl: dict[str, Any] | None = None
    rows = []
    feature_set_bits = math.log2(len(PARTITION_FEATURE_SETS))
    for feature_set in PARTITION_FEATURE_SETS:
        groups: dict[tuple[Any, ...], list[str]] = defaultdict(list)
        for pair in PAIRS:
            groups[tuple(features[pair][feature] for feature in feature_set)].append(pair)
        predictions: dict[str, str] = {}
        bucket_labels: dict[str, str] = {}
        for key, pairs in groups.items():
            label = majority_label(pairs, labels)
            bucket_labels[repr(key)] = label
            for pair in pairs:
                predictions[pair] = label
        primary_correct = sum(1 for pair in PAIRS if predictions[pair] == labels[pair])
        accepted_correct = sum(1 for pair in PAIRS if predictions[pair] in acceptable[pair])
        primary_errors = PAIR_COUNT - primary_correct
        bucket_count_value = len(groups)
        singleton_buckets = sum(1 for pairs in groups.values() if len(pairs) == 1)
        model_bits = feature_set_bits + bucket_count_value * math.log2(len(full_symbols))
        mdl_bits = model_bits + residual_bits(primary_errors, len(full_symbols))
        row = {
            "family": "signature_bucket_partition",
            "feature_set": list(feature_set),
            "primary_correct": primary_correct,
            "primary_errors": primary_errors,
            "accepted_correct": accepted_correct,
            "accepted_errors": PAIR_COUNT - accepted_correct,
            "bucket_count": bucket_count_value,
            "singleton_buckets": singleton_buckets,
            "max_bucket_size": max(len(pairs) for pairs in groups.values()),
            "model_bits": model_bits,
            "residual_bits": residual_bits(primary_errors, len(full_symbols)),
            "mdl_bits": mdl_bits,
            "lookup_like": bucket_count_value >= 30 or singleton_buckets >= 20,
            "bucket_labels": bucket_labels if bucket_count_value <= 24 else None,
        }
        rows.append(row)
        accuracy_key = (
            accepted_correct,
            primary_correct,
            -mdl_bits,
            -bucket_count_value,
            tuple(feature_set),
        )
        if best_accuracy is None or accuracy_key > best_accuracy["_sort_key"]:
            best_accuracy = {**row, "_sort_key": accuracy_key}
        mdl_key = (mdl_bits, primary_errors, accepted_correct, bucket_count_value, tuple(feature_set))
        if best_mdl is None or mdl_key < best_mdl["_sort_key"]:
            best_mdl = {**row, "_sort_key": mdl_key}
    assert best_accuracy is not None and best_mdl is not None
    for item in (best_accuracy, best_mdl):
        item.pop("_sort_key", None)
    rows.sort(key=lambda row: (row["accepted_errors"], row["primary_errors"], row["mdl_bits"], row["bucket_count"]))
    return {
        "best_accuracy": best_accuracy,
        "best_mdl": best_mdl,
        "top_accuracy_rows": rows[:10],
    }


def evaluate_table(
    labels: dict[str, str],
    acceptable: dict[str, set[str]],
    formula: dict[str, Any],
    tape_stats: dict[str, Any],
    full_symbols: list[str],
    include_details: bool = True,
) -> dict[str, Any]:
    digit_signatures, top_symbols = build_digit_signatures(labels, tape_stats, full_symbols)
    pair_features = build_pair_features(labels, digit_signatures, top_symbols, tape_stats)
    feature_names = numeric_feature_names(top_symbols)
    orders = build_symbol_orders(labels, formula, tape_stats, full_symbols)
    formula_bank = build_index_formula_bank(pair_features, feature_names)
    index_result = evaluate_index_formulas(labels, acceptable, formula_bank, orders, full_symbols, include_details)
    partition_result = evaluate_partition_models(labels, acceptable, pair_features, full_symbols)
    best_family_rows = [
        {**index_result["best_accuracy"], "model_family": "signature_index_formula"},
        {**partition_result["best_accuracy"], "model_family": "signature_bucket_partition"},
    ]
    best_family_rows.sort(
        key=lambda row: (
            row["accepted_correct"],
            row["primary_correct"],
            -row["mdl_bits"],
            row["model_family"],
        ),
        reverse=True,
    )
    out = {
        "top_symbols": top_symbols,
        "symbol_orders_tested": {key: value for key, value in orders.items()},
        "numeric_feature_count": len(feature_names),
        "numeric_features": feature_names,
        "index_formula": index_result,
        "partition_model": partition_result,
        "best_accuracy_overall": best_family_rows[0],
    }
    if include_details:
        out["digit_signatures"] = digit_signatures
    return out


def shuffle_labels(labels: dict[str, str], rng: random.Random) -> dict[str, str]:
    values = [labels[pair] for pair in PAIRS]
    rng.shuffle(values)
    return dict(zip(PAIRS, values))


def summarize_distribution(values: list[float], observed: float, lower_is_better: bool = False) -> dict[str, float]:
    mean = sum(values) / len(values)
    if len(values) > 1:
        sd = (sum((value - mean) ** 2 for value in values) / (len(values) - 1)) ** 0.5
    else:
        sd = 0.0
    if lower_is_better:
        p = (sum(value <= observed for value in values) + 1) / (len(values) + 1)
        z = (mean - observed) / sd if sd else 0.0
    else:
        p = (sum(value >= observed for value in values) + 1) / (len(values) + 1)
        z = (observed - mean) / sd if sd else 0.0
    return {
        "observed": observed,
        "control_mean": mean,
        "control_sd": sd,
        "control_min": min(values),
        "control_max": max(values),
        "p_good_direction": p,
        "z_good_direction": z,
    }


def run_controls(
    labels: dict[str, str],
    formula: dict[str, Any],
    tape_stats: dict[str, Any],
    full_symbols: list[str],
    observed: dict[str, Any],
) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED)
    metrics: dict[str, list[float]] = defaultdict(list)
    control_summaries: list[dict[str, Any]] = []
    for trial in range(CONTROL_TRIALS):
        if trial and trial % 10 == 0:
            print(f"control {trial}/{CONTROL_TRIALS}", file=sys.stderr)
        shuffled = shuffle_labels(labels, rng)
        acceptable = {pair: {shuffled[pair]} for pair in PAIRS}
        row = evaluate_table(shuffled, acceptable, formula, tape_stats, full_symbols, include_details=False)
        idx = row["index_formula"]["best_accuracy"]
        part = row["partition_model"]["best_accuracy"]
        overall = row["best_accuracy_overall"]
        metrics["index_primary_correct"].append(float(idx["primary_correct"]))
        metrics["index_mdl_bits"].append(float(idx["mdl_bits"]))
        metrics["partition_primary_correct"].append(float(part["primary_correct"]))
        metrics["partition_mdl_bits"].append(float(part["mdl_bits"]))
        metrics["overall_primary_correct"].append(float(overall["primary_correct"]))
        metrics["overall_mdl_bits"].append(float(overall["mdl_bits"]))
        if trial < 20:
            control_summaries.append(
                {
                    "trial": trial,
                    "index_primary_correct": idx["primary_correct"],
                    "index_mdl_bits": idx["mdl_bits"],
                    "partition_primary_correct": part["primary_correct"],
                    "partition_mdl_bits": part["mdl_bits"],
                    "overall_family": overall["model_family"],
                    "overall_primary_correct": overall["primary_correct"],
                    "overall_mdl_bits": overall["mdl_bits"],
                }
            )
    observed_metrics = {
        "index_primary_correct": observed["index_formula"]["best_accuracy"]["primary_correct"],
        "index_mdl_bits": observed["index_formula"]["best_accuracy"]["mdl_bits"],
        "partition_primary_correct": observed["partition_model"]["best_accuracy"]["primary_correct"],
        "partition_mdl_bits": observed["partition_model"]["best_accuracy"]["mdl_bits"],
        "overall_primary_correct": observed["best_accuracy_overall"]["primary_correct"],
        "overall_mdl_bits": observed["best_accuracy_overall"]["mdl_bits"],
    }
    summaries = {
        key: summarize_distribution(
            values,
            float(observed_metrics[key]),
            lower_is_better=key.endswith("_mdl_bits"),
        )
        for key, values in metrics.items()
    }
    return {
        "type": "inventory_preserving_label_shuffle",
        "seed": RANDOM_SEED,
        "trials": CONTROL_TRIALS,
        "summaries": summaries,
        "first_trials": control_summaries,
    }


def verdict(observed: dict[str, Any], controls: dict[str, Any], baselines: dict[str, float]) -> dict[str, Any]:
    best = observed["best_accuracy_overall"]
    lookup_bits = baselines["inventory_preserving_pair_lookup_bits"]
    p_accuracy = controls["summaries"]["overall_primary_correct"]["p_good_direction"]
    mdl_beats_lookup = best["mdl_bits"] < lookup_bits
    lossless = best["primary_errors"] == 0
    significant = p_accuracy <= 0.01
    if lossless and mdl_beats_lookup and significant:
        status = "POSITIVE_STRUCTURAL_CANDIDATE"
        summary = "A compact digit-signature model is lossless, below lookup MDL, and stronger than shuffled controls."
    elif best["accepted_errors"] <= 2 and significant:
        status = "WEAK_STRUCTURAL_SIGNAL"
        summary = "The signature model is better than controls but is not a lossless, lookup-beating generator."
    else:
        status = "NEGATIVE_PLATEAU_CONFIRMED"
        summary = "No simple digit-signature formula clears the lossless, lookup-beating, control-separated bar."
    return {
        "status": status,
        "summary": summary,
        "translation_delta": "NONE",
        "new_plaintext": False,
        "conservative_read": (
            "Treat any hit as structural diagnostics only; the search does not produce or promote plaintext."
        ),
        "criteria": {
            "lossless_primary_table": lossless,
            "mdl_below_inventory_lookup": mdl_beats_lookup,
            "inventory_shuffle_p_le_0_01": significant,
        },
    }


def write_report(result: dict[str, Any]) -> None:
    observed = result["observed"]
    controls = result["controls"]
    baselines = result["mdl_baselines"]
    best = observed["best_accuracy_overall"]
    idx = observed["index_formula"]["best_accuracy"]
    part = observed["partition_model"]["best_accuracy"]
    lines = [
        "# Digit Signature Formula Search",
        "",
        "Generated by `digit_signature_formula_search.py`.",
        "",
        "Scope: test whether the 55-cell unordered pair table can be generated by",
        "a simple digit-signature model. The signatures use row/column marginals,",
        "diagonal labels, frequent-symbol incidence, and tape/first-use features",
        "when available. No pair->symbol lookup is allowed in the index-formula",
        "family; the bucket-partition diagnostic pays MDL for every bucket label.",
        "",
        "Mechanical-only result: `translation_delta=NONE`; no plaintext is promoted.",
        "",
        "## Target And Baselines",
        "",
        f"- Pair cells: {PAIR_COUNT}.",
        f"- Symbol inventory: `{''.join(result['target']['symbols'])}`.",
        f"- Primary inventory: `{result['target']['primary_label_stream']}`.",
        f"- Inventory-preserving lookup MDL: {baselines['inventory_preserving_pair_lookup_bits']:.2f} bits.",
        f"- Raw literal table MDL: {baselines['raw_literal_table_bits']:.2f} bits.",
        "",
        "## Best Observed Models",
        "",
        "### Index Formula",
        "",
        f"- Correct primary cells: {idx['primary_correct']} / {PAIR_COUNT}.",
        f"- Accepted cells: {idx['accepted_correct']} / {PAIR_COUNT}.",
        f"- MDL: {idx['mdl_bits']:.2f} bits "
        f"(model {idx['model_bits']:.2f}, residual {idx['residual_bits']:.2f}).",
        f"- Symbol order: `{idx['symbol_order_id']}` = `{''.join(idx['symbol_order'])}`.",
        f"- Formula: `{idx['expression']}`.",
        f"- Features: `{', '.join(idx['features'])}`.",
        "",
        "### Signature Bucket Diagnostic",
        "",
        f"- Correct primary cells: {part['primary_correct']} / {PAIR_COUNT}.",
        f"- Accepted cells: {part['accepted_correct']} / {PAIR_COUNT}.",
        f"- Buckets: {part['bucket_count']} "
        f"({part['singleton_buckets']} singletons; lookup_like={part['lookup_like']}).",
        f"- MDL: {part['mdl_bits']:.2f} bits "
        f"(model {part['model_bits']:.2f}, residual {part['residual_bits']:.2f}).",
        f"- Features: `{', '.join(part['feature_set'])}`.",
        "",
        "### Best Accuracy Overall",
        "",
        f"- Family: `{best['model_family']}`.",
        f"- Primary errors: {best['primary_errors']}; accepted errors: {best['accepted_errors']}.",
        f"- MDL vs lookup: {best['mdl_bits']:.2f} bits vs "
        f"{baselines['inventory_preserving_pair_lookup_bits']:.2f} bits.",
        "",
        "## Inventory-Preserving Label Shuffle Controls",
        "",
        f"- Trials: {controls['trials']}; seed: {controls['seed']}.",
    ]
    for key in [
        "index_primary_correct",
        "partition_primary_correct",
        "overall_primary_correct",
        "index_mdl_bits",
        "partition_mdl_bits",
        "overall_mdl_bits",
    ]:
        row = controls["summaries"][key]
        lines.append(
            f"- `{key}`: observed {row['observed']:.2f}, control mean {row['control_mean']:.2f}, "
            f"range {row['control_min']:.2f}-{row['control_max']:.2f}, "
            f"p_good={row['p_good_direction']:.4f}."
        )
    lines.extend(
        [
            "",
            "## Verdict",
            "",
            f"Status: `{result['verdict']['status']}`.",
            "",
            result["verdict"]["summary"],
            "",
            "Conservative interpretation: this is an analysis-only structural probe.",
            "Because the digit signatures are themselves derived from the pair table,",
            "any apparent compression must beat both lookup MDL and inventory-preserving",
            "label shuffles before it can be treated as a generator. This run does not",
            "change the project conclusion and does not reopen translation.",
        ]
    )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    formula = load_json(FORMULA_JSON)
    labels, acceptable = target_labels(formula)
    full_symbols = normalize_order(list(SYMBOL_ALPHABET), sorted(set(formula["symbol_to_codes"])))
    counts = Counter(labels.values())
    baselines = {
        "inventory_preserving_pair_lookup_bits": multinomial_bits(counts),
        "raw_literal_table_bits": PAIR_COUNT * math.log2(len(full_symbols)),
    }
    tape_stats = token_tape_stats(formula)
    observed = evaluate_table(labels, acceptable, formula, tape_stats, full_symbols, include_details=True)
    controls = run_controls(labels, formula, tape_stats, full_symbols, observed)
    result = {
        "schema": "digit_signature_formula_results_v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_formula": str(FORMULA_JSON.relative_to(HERE)),
        "scope": "55 unordered pair cells; mechanical structural generator search only",
        "translation_delta": "NONE",
        "new_plaintext": False,
        "target": {
            "pair_count": PAIR_COUNT,
            "symbols": full_symbols,
            "primary_label_stream": "".join(labels[pair] for pair in PAIRS),
            "primary_counts": dict(sorted(counts.items())),
            "conflict_cells": {
                pair: sorted(symbols)
                for pair, symbols in acceptable.items()
                if len(symbols) > 1
            },
        },
        "feature_policy": {
            "digit_signature_sources": [
                "incident pair-table symbol marginals",
                "diagonal symbol per digit",
                "presence/counts for frequent symbols",
                "compiled tape first-use and token counts when available",
            ],
            "pair_lookup_allowed": False,
            "bucket_partition_label_table_is_mdl_penalized": True,
            "control": "inventory-preserving label shuffle with signatures recomputed per shuffle",
        },
        "tape_projection": {
            "available": tape_stats["available"],
            "notes": tape_stats["notes"],
        },
        "mdl_baselines": baselines,
        "observed": observed,
        "controls": controls,
    }
    result["verdict"] = verdict(observed, controls, baselines)
    write_json(OUT_JSON, result)
    write_report(result)
    print(f"wrote {OUT_JSON}")
    print(f"wrote {OUT_MD}")
    print(result["verdict"]["status"])


if __name__ == "__main__":
    main()
