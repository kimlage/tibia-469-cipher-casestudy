#!/usr/bin/env python3
"""Constructive search for the 469 unordered-pair table.

The deep formula pass already showed that the 55 unordered-pair cells are the
real hard boundary: arithmetic/grid rules only recover the table when they
become a lookup. This script asks a narrower historical question:

Could a human author have filled the 55 pair cells by a simple constructive
procedure, such as frequency-based homophone allocation, a lore-source text,
a corpus slice, or a seeded shuffle?

This remains mechanical only. It does not promote plaintext.
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

OUT_JSON = HERE / "pair_table_constructive_leaderboard.json"
OUT_MD = HERE / "pair_table_constructive_report.md"

SIGMA = "*ABCEFILNORSTV"
RANDOM_SEED = 469
random.seed(RANDOM_SEED)

SEEDS = [1, 469, 3478, 43153, 34784, 74032, 45331, 486486]

SOURCE_TEXTS = {
    "tibia": "TIBIA",
    "bonelord": "BONELORD",
    "beholder": "BEHOLDER",
    "benna": "BENNA",
    "telbenna": "TELBENNA",
    "itelbenna": "ITELBENNA",
    "fas": "FAS",
    "tibiabenna": "TIBIABENNA",
    "honeminas": "HONEMINAS",
    "tridiag": "TRIDIAG",
    "donina": "DONINA",
    "magic_web": "MAGICWEB",
    "mathemagic": "MATHEMAGIC",
    "great_calculator": "GREATCALCULATOR",
    "subjective_viewer": "SUBJECTIVEVIEWER",
    "one_not_tibia_silly": "ITS ONE NOT TIBIA SILLY",
    "wrinkled_formula": "DIFFERENT FORMULA FOR THE SUBJECTIVE VIEWER",
    "honeminas_formula_numbers": "43153 34784 3478 34 78 99 469",
    "known_internal_sample": "ITELBENNAIFIININSBASTFNENIIFINI",
}


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def normalize_source(text: str) -> str:
    return "".join(ch for ch in text.upper() if ch in SIGMA)


def pearson(xs: list[float], ys: list[float]) -> float:
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = sum((x - mx) ** 2 for x in xs)
    dy = sum((y - my) ** 2 for y in ys)
    return num / math.sqrt(dx * dy) if dx and dy else 0.0


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


def pair_orders() -> dict[str, list[str]]:
    pairs = [f"{i}{j}" for i in range(10) for j in range(i, 10)]
    orders = {
        "upper_row": pairs,
        "upper_row_rev": list(reversed(pairs)),
        "upper_row_snake": [
            pair
            for i in range(10)
            for pair in ([f"{i}{j}" for j in range(i, 10)] if i % 2 == 0 else [f"{i}{j}" for j in range(9, i - 1, -1)])
        ],
        "upper_column": [f"{i}{j}" for j in range(10) for i in range(j + 1)],
        "upper_column_snake": [
            pair
            for j in range(10)
            for pair in ([f"{i}{j}" for i in range(j + 1)] if j % 2 == 0 else [f"{i}{j}" for i in range(j, -1, -1)])
        ],
        "by_sum": sorted(pairs, key=lambda p: (int(p[0]) + int(p[1]), int(p[0]), int(p[1]))),
        "by_sum_rev": sorted(pairs, key=lambda p: (int(p[0]) + int(p[1]), int(p[0]), int(p[1])), reverse=True),
        "by_diff": sorted(pairs, key=lambda p: (int(p[1]) - int(p[0]), int(p[0]), int(p[1]))),
        "by_diff_rev": sorted(pairs, key=lambda p: (int(p[1]) - int(p[0]), int(p[0]), int(p[1])), reverse=True),
        "by_product": sorted(pairs, key=lambda p: (int(p[0]) * int(p[1]), int(p[0]), int(p[1]))),
        "by_triangular_index": sorted(pairs, key=lambda p: int(p[1]) * (int(p[1]) + 1) // 2 + int(p[0])),
    }
    coords = []
    top, left, bottom, right = 0, 0, 9, 9
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
    seen = []
    seen_set = set()
    for a, b in coords:
        pair = f"{min(a, b)}{max(a, b)}"
        if pair not in seen_set:
            seen.append(pair)
            seen_set.add(pair)
    orders["spiral_first_unordered"] = seen
    return orders


def acceptable_pair_symbols(pair_table: dict, pair: str) -> set[str]:
    row = pair_table[pair]
    if row["status"] == "pure":
        return {row["symbol_if_pure"]}
    return set(row["symbols"])


def primary_pair_symbol(pair_table: dict, pair: str) -> str:
    row = pair_table[pair]
    if row["status"] == "pure":
        return row["symbol_if_pure"]
    return sorted(row["symbols"])[0]


def symbol_sequences_from_occ() -> dict[str, str]:
    occ = load_json(OCC_STREAMS)["occ"]
    by_book: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for symbol, rows in occ.items():
        for row in rows:
            by_book[str(row["book"])].append((int(row["pos"]), symbol))
    return {book: "".join(sym for _, sym in sorted(rows)) for book, rows in by_book.items()}


def frequency_allocation_test(formula: dict) -> dict:
    occ = load_json(OCC_STREAMS)["occ"]
    corpus_counts = {symbol: len(rows) for symbol, rows in occ.items()}
    ordered_code_counts = Counter(formula["code_to_symbol"].values())
    pair_counts = Counter()
    for row in formula["pair_table"].values():
        if row["status"] == "pure":
            pair_counts[row["symbol_if_pure"]] += 1.0
        else:
            for symbol in row["symbols"]:
                pair_counts[symbol] += 1.0 / len(row["symbols"])

    symbols = sorted(set(SIGMA) | set(corpus_counts) | set(pair_counts))
    pair_vector = [float(pair_counts.get(symbol, 0.0)) for symbol in symbols]
    ordered_vector = [float(ordered_code_counts.get(symbol, 0.0)) for symbol in symbols]
    corpus_vector = [float(corpus_counts.get(symbol, 0.0)) for symbol in symbols]

    pair_pearson = pearson(pair_vector, corpus_vector)
    pair_spearman = pearson(ranks(pair_vector), ranks(corpus_vector))
    ordered_pearson = pearson(ordered_vector, corpus_vector)

    shuffled = pair_vector[:]
    ge = 0
    control_scores = []
    for _ in range(20000):
        random.shuffle(shuffled)
        score = pearson(shuffled, corpus_vector)
        control_scores.append(score)
        ge += score >= pair_pearson
    p_ge = (ge + 1) / (len(control_scores) + 1)
    control_mean = sum(control_scores) / len(control_scores)
    control_sd = (sum((score - control_mean) ** 2 for score in control_scores) / (len(control_scores) - 1)) ** 0.5

    total_corpus = sum(corpus_counts.values())
    expected = {symbol: 55 * corpus_counts.get(symbol, 0) / total_corpus for symbol in symbols}
    rounded = {symbol: math.floor(expected[symbol]) for symbol in symbols}
    remainder = 55 - sum(rounded.values())
    for symbol in sorted(symbols, key=lambda s: (expected[s] - rounded[s], expected[s]), reverse=True)[:remainder]:
        rounded[symbol] += 1
    l1 = sum(abs(pair_counts.get(symbol, 0.0) - rounded[symbol]) for symbol in symbols)

    rows = [
        {
            "symbol": symbol,
            "pair_slots_split_conflict": pair_counts.get(symbol, 0.0),
            "ordered_codes": ordered_code_counts.get(symbol, 0),
            "corpus_occurrences": corpus_counts.get(symbol, 0),
            "expected_pair_slots_from_corpus": expected[symbol],
            "rounded_expected_slots": rounded[symbol],
        }
        for symbol in symbols
    ]
    return {
        "hypothesis_id": "pair_table_frequency_allocation",
        "targets_explained": ["F", "A"],
        "pair_count_vs_corpus_pearson": pair_pearson,
        "pair_count_vs_corpus_spearman": pair_spearman,
        "ordered_code_count_vs_corpus_pearson": ordered_pearson,
        "label_shuffle_p_ge": p_ge,
        "label_shuffle_mean": control_mean,
        "label_shuffle_sd": control_sd,
        "rounded_corpus_model_l1": l1,
        "rows": rows,
        "verdict": "candidate_generator_explains_homophone_allocation_not_cell_placement",
    }


def score_predictions(pair_table: dict, pairs: list[str], predicted: list[str]) -> dict:
    ok = []
    for pair, pred in zip(pairs, predicted):
        ok.append(pred in acceptable_pair_symbols(pair_table, pair))
    return {
        "correct": sum(ok),
        "total": len(ok),
        "accuracy": sum(ok) / len(ok),
    }


def source_fill_search(formula: dict) -> dict:
    pair_table = formula["pair_table"]
    rows = []
    for source_id, raw_text in SOURCE_TEXTS.items():
        source = normalize_source(raw_text)
        if len(source) < 2:
            continue
        for order_id, pairs in pair_orders().items():
            n = len(source)
            strides = [stride for stride in range(1, n + 1) if math.gcd(stride, n) == 1]
            for reverse in (False, True):
                text = source[::-1] if reverse else source
                for stride in strides:
                    for offset in range(n):
                        predicted = [text[(offset + idx * stride) % n] for idx in range(len(pairs))]
                        score = score_predictions(pair_table, pairs, predicted)
                        rows.append(
                            {
                                "hypothesis_id": "pair_table_source_cycle",
                                "source_id": source_id,
                                "source": text,
                                "source_length": n,
                                "order": order_id,
                                "reverse": reverse,
                                "stride": stride,
                                "offset": offset,
                                **score,
                            }
                        )
    rows.sort(key=lambda row: (-row["accuracy"], row["source_length"], row["order"], row["source_id"]))

    best = rows[0]
    controls = []
    source_chars = list(best["source"])
    for _ in range(500):
        random.shuffle(source_chars)
        text = "".join(source_chars)
        best_ctrl = 0.0
        n = len(text)
        strides = [stride for stride in range(1, n + 1) if math.gcd(stride, n) == 1]
        for pairs in pair_orders().values():
            for stride in strides:
                for offset in range(n):
                    predicted = [text[(offset + idx * stride) % n] for idx in range(len(pairs))]
                    best_ctrl = max(best_ctrl, score_predictions(pair_table, pairs, predicted)["accuracy"])
        controls.append(best_ctrl)
    ctrl_mean = sum(controls) / len(controls)
    ctrl_sd = (sum((score - ctrl_mean) ** 2 for score in controls) / (len(controls) - 1)) ** 0.5
    z = (best["accuracy"] - ctrl_mean) / ctrl_sd if ctrl_sd else 0.0
    p_ge = (sum(score >= best["accuracy"] for score in controls) + 1) / (len(controls) + 1)

    return {
        "hypothesis_id": "pair_table_source_cycle_search",
        "top_rows": rows[:50],
        "best": best,
        "best_source_shuffle_control_mean": ctrl_mean,
        "best_source_shuffle_control_sd": ctrl_sd,
        "best_source_shuffle_z": z,
        "best_source_shuffle_p_ge": p_ge,
        "verdict": "rejected_control" if best["accuracy"] < 0.5 or p_ge > 0.05 else "candidate_generator",
    }


def longest_common_substring(a: str, b: str) -> int:
    prev = [0] * (len(b) + 1)
    best = 0
    for ca in a:
        cur = [0]
        for idx, cb in enumerate(b, start=1):
            val = prev[idx - 1] + 1 if ca == cb else 0
            cur.append(val)
            if val > best:
                best = val
        prev = cur
    return best


def corpus_slice_search(formula: dict) -> dict:
    pair_table = formula["pair_table"]
    book_sequences = symbol_sequences_from_occ()
    corpus = "#".join(book_sequences[book] for book in sorted(book_sequences, key=lambda x: int(x)))
    rows = []
    for order_id, pairs in pair_orders().items():
        seq = "".join(primary_pair_symbol(pair_table, pair) for pair in pairs)
        best_len = longest_common_substring(seq, corpus)
        controls = []
        chars = list(seq)
        for _ in range(500):
            random.shuffle(chars)
            controls.append(longest_common_substring("".join(chars), corpus))
        ctrl_mean = sum(controls) / len(controls)
        ctrl_sd = (sum((value - ctrl_mean) ** 2 for value in controls) / (len(controls) - 1)) ** 0.5
        rows.append(
            {
                "order": order_id,
                "sequence": seq,
                "longest_corpus_substring": best_len,
                "shuffle_mean": ctrl_mean,
                "shuffle_sd": ctrl_sd,
                "z_vs_shuffle": (best_len - ctrl_mean) / ctrl_sd if ctrl_sd else 0.0,
            }
        )
    rows.sort(key=lambda row: (-row["longest_corpus_substring"], -row["z_vs_shuffle"]))
    best = rows[0]
    return {
        "hypothesis_id": "pair_table_as_corpus_slice",
        "rows": rows,
        "best": best,
        "verdict": "rejected_control" if best["longest_corpus_substring"] < 12 or best["z_vs_shuffle"] < 3 else "candidate_generator",
    }


def majority_accuracy(keys: list, target: list[str]) -> tuple[float, int]:
    groups = defaultdict(list)
    for key, symbol in zip(keys, target):
        groups[key].append(symbol)
    majority = {key: Counter(values).most_common(1)[0][0] for key, values in groups.items()}
    ok = sum(majority[key] == symbol for key, symbol in zip(keys, target))
    return ok / len(target), len(groups)


def spatial_feature_diagnostics(formula: dict) -> dict:
    pair_table = formula["pair_table"]
    pairs = [f"{i}{j}" for i in range(10) for j in range(i, 10)]
    target = [primary_pair_symbol(pair_table, pair) for pair in pairs]
    features = {
        "x_min_digit": [int(pair[0]) for pair in pairs],
        "y_max_digit": [int(pair[1]) for pair in pairs],
        "sum": [int(pair[0]) + int(pair[1]) for pair in pairs],
        "diff": [int(pair[1]) - int(pair[0]) for pair in pairs],
        "product": [int(pair[0]) * int(pair[1]) for pair in pairs],
        "diagonal": [int(pair[0]) == int(pair[1]) for pair in pairs],
        "border": [int(pair[0]) in {0, 9} or int(pair[1]) in {0, 9} for pair in pairs],
        "parity": [(int(pair[0]) + int(pair[1])) % 2 for pair in pairs],
        "sum_mod3": [(int(pair[0]) + int(pair[1])) % 3 for pair in pairs],
        "triangular_index_mod7": [
            (int(pair[1]) * (int(pair[1]) + 1) // 2 + int(pair[0])) % 7
            for pair in pairs
        ],
    }
    rows = []
    for name, keys in features.items():
        observed, groups = majority_accuracy(keys, target)
        controls = []
        shuffled = target[:]
        for _ in range(5000):
            random.shuffle(shuffled)
            controls.append(majority_accuracy(keys, shuffled)[0])
        mean = sum(controls) / len(controls)
        sd = (sum((score - mean) ** 2 for score in controls) / (len(controls) - 1)) ** 0.5
        rows.append(
            {
                "feature": name,
                "accuracy": observed,
                "groups": groups,
                "shuffle_mean": mean,
                "shuffle_sd": sd,
                "z_vs_shuffle": (observed - mean) / sd if sd else 0.0,
                "p_ge": (sum(score >= observed for score in controls) + 1) / (len(controls) + 1),
            }
        )
    rows.sort(key=lambda row: (-row["accuracy"], row["p_ge"], row["groups"]))
    best = rows[0]
    return {
        "hypothesis_id": "pair_table_spatial_feature_diagnostics",
        "rows": rows,
        "best": best,
        "verdict": "rejected_control" if best["p_ge"] > 0.05 else "candidate_generator",
    }


def spatial_dispersion_diagnostics(formula: dict) -> dict:
    pair_table = formula["pair_table"]
    pairs = [f"{i}{j}" for i in range(10) for j in range(i, 10)]
    labels = [primary_pair_symbol(pair_table, pair) for pair in pairs]
    coords = {pair: (int(pair[0]), int(pair[1])) for pair in pairs}

    def manhattan(left: str, right: str) -> int:
        x1, y1 = coords[left]
        x2, y2 = coords[right]
        return abs(x1 - x2) + abs(y1 - y2)

    def metrics(current_labels: list[str]) -> dict:
        by_symbol = defaultdict(list)
        for pair, label in zip(pairs, current_labels):
            by_symbol[label].append(pair)
        symbol_means = []
        weighted_distances = []
        for symbol_pairs in by_symbol.values():
            if len(symbol_pairs) < 2:
                continue
            distances = [
                manhattan(left, right)
                for idx, left in enumerate(symbol_pairs)
                for right in symbol_pairs[idx + 1 :]
            ]
            symbol_means.append(sum(distances) / len(distances))
            weighted_distances.extend(distances)
        adjacent_same = 0
        adjacent_total = 0
        for idx, left in enumerate(pairs):
            for jdx, right in enumerate(pairs[idx + 1 :], start=idx + 1):
                if manhattan(left, right) != 1:
                    continue
                adjacent_total += 1
                adjacent_same += current_labels[idx] == current_labels[jdx]
        return {
            "mean_symbol_distance": sum(symbol_means) / len(symbol_means),
            "weighted_pair_distance": sum(weighted_distances) / len(weighted_distances),
            "adjacent_same_fraction": adjacent_same / adjacent_total,
            "adjacent_same_count": adjacent_same,
            "adjacent_total": adjacent_total,
        }

    observed = metrics(labels)
    controls = []
    shuffled = labels[:]
    for _ in range(10000):
        random.shuffle(shuffled)
        controls.append(metrics(shuffled[:]))

    rows = []
    for key in ["mean_symbol_distance", "weighted_pair_distance", "adjacent_same_fraction"]:
        values = [control[key] for control in controls]
        mean = sum(values) / len(values)
        sd = (sum((value - mean) ** 2 for value in values) / (len(values) - 1)) ** 0.5
        rows.append(
            {
                "metric": key,
                "observed": observed[key],
                "shuffle_mean": mean,
                "shuffle_sd": sd,
                "z_vs_shuffle": (observed[key] - mean) / sd if sd else 0.0,
                "p_ge": (sum(value >= observed[key] for value in values) + 1) / (len(values) + 1),
                "p_le": (sum(value <= observed[key] for value in values) + 1) / (len(values) + 1),
            }
        )
    strongest = max(rows, key=lambda row: abs(row["z_vs_shuffle"]))
    return {
        "hypothesis_id": "pair_table_spatial_dispersion",
        "observed": observed,
        "rows": rows,
        "strongest": strongest,
        "verdict": "rejected_control",
    }


def lcg_stream(seed: int, a: int, c: int, m: int = 2**31):
    state = seed % m
    while True:
        state = (a * state + c) % m
        yield state


def xorshift32_stream(seed: int):
    state = seed & 0xFFFFFFFF or 0x6D2B79F5
    while True:
        state ^= (state << 13) & 0xFFFFFFFF
        state ^= (state >> 17) & 0xFFFFFFFF
        state ^= (state << 5) & 0xFFFFFFFF
        yield state & 0xFFFFFFFF


def permutation_from_stream(stream, n: int) -> list[int]:
    return [idx for idx, _ in sorted(((idx, next(stream)) for idx in range(n)), key=lambda item: (item[1], item[0]))]


def seeded_placement_search(formula: dict, allocation: dict) -> dict:
    pair_table = formula["pair_table"]
    pairs = pair_orders()["upper_row"]
    pair_counts = {}
    for row in allocation["rows"]:
        symbol = row["symbol"]
        # For actual 55-slot placement we need integers; assign the conflict
        # cell to the lexicographically first acceptable symbol and keep the
        # conflict exception explicit in the report.
        pair_counts[symbol] = int(round(row["pair_slots_split_conflict"]))
    diff = 55 - sum(pair_counts.values())
    if diff:
        pair_counts["I"] = pair_counts.get("I", 0) + diff

    symbol_orders = {
        "sigma": list(SIGMA),
        "frequency_desc": [
            row["symbol"]
            for row in sorted(allocation["rows"], key=lambda r: (-r["corpus_occurrences"], r["symbol"]))
            if row["symbol"] in SIGMA
        ],
        "pair_count_desc": [
            row["symbol"]
            for row in sorted(allocation["rows"], key=lambda r: (-r["pair_slots_split_conflict"], r["symbol"]))
            if row["symbol"] in SIGMA
        ],
    }
    generators = {
        "lcg_ansi": lambda seed: lcg_stream(seed, 1103515245, 12345),
        "lcg_small_21_1": lambda seed: lcg_stream(seed, 21, 1, 1000003),
        "lcg_small_37_17": lambda seed: lcg_stream(seed, 37, 17, 1000003),
        "xorshift32": xorshift32_stream,
    }
    rows = []
    for order_id, order_pairs in pair_orders().items():
        for symbol_order_id, symbol_order in symbol_orders.items():
            multiset = []
            for symbol in symbol_order:
                multiset.extend([symbol] * pair_counts.get(symbol, 0))
            for symbol in SIGMA:
                if symbol not in symbol_order:
                    multiset.extend([symbol] * pair_counts.get(symbol, 0))
            if len(multiset) != 55:
                continue
            for seed in SEEDS:
                for gen_id, gen_factory in generators.items():
                    perm = permutation_from_stream(gen_factory(seed), 55)
                    predicted_by_index = ["?"] * 55
                    for src_idx, slot_idx in enumerate(perm):
                        predicted_by_index[slot_idx] = multiset[src_idx]
                    predicted = [predicted_by_index[pairs.index(pair)] for pair in order_pairs]
                    score = score_predictions(pair_table, order_pairs, predicted)
                    rows.append(
                        {
                            "seed": seed,
                            "generator": gen_id,
                            "order": order_id,
                            "symbol_order": symbol_order_id,
                            **score,
                        }
                    )
    rows.sort(key=lambda row: (-row["accuracy"], row["seed"], row["generator"]))

    controls = []
    best_shape = rows[0]
    for seed in range(1000, 1500):
        perm = permutation_from_stream(generators[best_shape["generator"]](seed), 55)
        symbol_order = symbol_orders[best_shape["symbol_order"]]
        multiset = []
        for symbol in symbol_order:
            multiset.extend([symbol] * pair_counts.get(symbol, 0))
        predicted_by_index = ["?"] * 55
        for src_idx, slot_idx in enumerate(perm):
            predicted_by_index[slot_idx] = multiset[src_idx]
        order_pairs = pair_orders()[best_shape["order"]]
        predicted = [predicted_by_index[pairs.index(pair)] for pair in order_pairs]
        controls.append(score_predictions(pair_table, order_pairs, predicted)["accuracy"])
    ctrl_mean = sum(controls) / len(controls)
    ctrl_sd = (sum((score - ctrl_mean) ** 2 for score in controls) / (len(controls) - 1)) ** 0.5
    best = rows[0]
    return {
        "hypothesis_id": "pair_table_seeded_placement",
        "searched_rows": len(rows),
        "top_rows": rows[:50],
        "best": best,
        "control_mean": ctrl_mean,
        "control_sd": ctrl_sd,
        "z_vs_control_seeds": (best["accuracy"] - ctrl_mean) / ctrl_sd if ctrl_sd else 0.0,
        "control_p_ge": (sum(score >= best["accuracy"] for score in controls) + 1) / (len(controls) + 1),
        "verdict": "rejected_control",
    }


def write_outputs(results: dict) -> None:
    write_json(OUT_JSON, {"schema": "pair_table_constructive_leaderboard.v1", **results})
    allocation = results["frequency_allocation"]
    source = results["source_fill"]
    corpus = results["corpus_slice"]
    spatial = results["spatial_features"]
    dispersion = results["spatial_dispersion"]
    seeded = results["seeded_placement"]

    lines = [
        "# Pair-Table Constructive Search",
        "",
        "Generated by `pair_table_constructive_search.py`.",
        "",
        "This pass searches for a plausible mechanical construction of the 55",
        "unordered pair cells. It does not translate 469.",
        "",
        "## 1. Homophone Allocation",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Pair-slot count vs corpus frequency Pearson | {allocation['pair_count_vs_corpus_pearson']:.3f} |",
        f"| Pair-slot count vs corpus frequency Spearman | {allocation['pair_count_vs_corpus_spearman']:.3f} |",
        f"| Ordered-code count vs corpus frequency Pearson | {allocation['ordered_code_count_vs_corpus_pearson']:.3f} |",
        f"| Label-shuffle p(>= observed Pearson) | {allocation['label_shuffle_p_ge']:.5f} |",
        f"| Rounded corpus-frequency model L1 error | {allocation['rounded_corpus_model_l1']:.1f} |",
        "",
        "| Symbol | Pair slots | Ordered codes | Corpus occurrences | Expected slots | Rounded |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in allocation["rows"]:
        lines.append(
            f"| `{row['symbol']}` | {row['pair_slots_split_conflict']:.1f} | {row['ordered_codes']} | {row['corpus_occurrences']} | {row['expected_pair_slots_from_corpus']:.2f} | {row['rounded_expected_slots']} |"
        )
    lines.extend(
        [
            "",
            "Verdict: this is the strongest new mechanical clue in the generator",
            "direction. The pair table looks like a homophonic alphabet whose class",
            "sizes track the internal symbol frequencies. It explains the allocation",
            "pressure, not the exact cell placement.",
            "",
            "## 2. Source-Text Cycle Fill",
            "",
            "| Source | Order | Accuracy | Stride | Offset | Control p | Verdict |",
            "|---|---|---:|---:|---:|---:|---|",
            f"| `{source['best']['source_id']}` | `{source['best']['order']}` | {source['best']['accuracy']:.3f} | {source['best']['stride']} | {source['best']['offset']} | {source['best_source_shuffle_p_ge']:.3f} | `{source['verdict']}` |",
            "",
            "Top source-cycle candidates do not beat shuffled-source controls strongly",
            "enough to promote.",
            "",
            "## 3. Pair Table as Corpus Slice",
            "",
            "| Order | Longest corpus substring | Shuffle mean | z | Verdict |",
            "|---|---:|---:|---:|---|",
            f"| `{corpus['best']['order']}` | {corpus['best']['longest_corpus_substring']} | {corpus['best']['shuffle_mean']:.2f} | {corpus['best']['z_vs_shuffle']:.2f} | `{corpus['verdict']}` |",
            "",
            "The pair-table sequence was not found as a long copied slice of the book",
            "symbol corpus.",
            "",
            "## 4. Spatial Feature Diagnostics",
            "",
            "| Best feature | Accuracy | Groups | Shuffle mean | p(>= observed) | Verdict |",
            "|---|---:|---:|---:|---:|---|",
            f"| `{spatial['best']['feature']}` | {spatial['best']['accuracy']:.3f} | {spatial['best']['groups']} | {spatial['best']['shuffle_mean']:.3f} | {spatial['best']['p_ge']:.3f} | `{spatial['verdict']}` |",
            "",
            "The best-looking raw feature is tested on the 55 unordered-pair cells,",
            "so mirror symmetry is already controlled. No spatial feature survives",
            "that fair control.",
            "",
            "## 5. Spatial Dispersion Diagnostics",
            "",
            "| Strongest metric | Observed | Shuffle mean | z | p low | p high | Verdict |",
            "|---|---:|---:|---:|---:|---:|---|",
            f"| `{dispersion['strongest']['metric']}` | {dispersion['strongest']['observed']:.3f} | {dispersion['strongest']['shuffle_mean']:.3f} | {dispersion['strongest']['z_vs_shuffle']:.2f} | {dispersion['strongest']['p_le']:.3f} | {dispersion['strongest']['p_ge']:.3f} | `{dispersion['verdict']}` |",
            "",
            "The placement does not show a strong anti-clustering or clustering",
            "signature after preserving the pair-symbol counts.",
            "",
            "## 6. Seeded Placement",
            "",
            "| Seed | Generator | Order | Symbol order | Accuracy | Uncorrected control p | Verdict |",
            "|---:|---|---|---|---:|---:|---|",
            f"| {seeded['best']['seed']} | `{seeded['best']['generator']}` | `{seeded['best']['order']}` | `{seeded['best']['symbol_order']}` | {seeded['best']['accuracy']:.3f} | {seeded['control_p_ge']:.3f} | `{seeded['verdict']}` |",
            "",
            f"The seeded search tested {seeded['searched_rows']} post-hoc combinations.",
            "The best row has low absolute accuracy, and its control p-value is",
            "uncorrected for that broad search. No lore seed is promoted.",
            "",
            "## Overall Verdict",
            "",
            "New finding: the homophone inventory is not arbitrary. It is strongly",
            "consistent with frequency-weighted allocation over the internal symbol",
            "alphabet. Still not found: the exact original placement formula for the",
            "55 pair cells.",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    formula = load_json(FORMULA_JSON)
    allocation = frequency_allocation_test(formula)
    results = {
        "translation_delta": "NONE",
        "accepted_original_formula": None,
        "frequency_allocation": allocation,
        "source_fill": source_fill_search(formula),
        "corpus_slice": corpus_slice_search(formula),
        "spatial_features": spatial_feature_diagnostics(formula),
        "spatial_dispersion": spatial_dispersion_diagnostics(formula),
        "seeded_placement": seeded_placement_search(formula, allocation),
    }
    write_outputs(results)
    print(f"wrote {OUT_JSON.relative_to(HERE)}")
    print(f"wrote {OUT_MD.relative_to(HERE)}")
    print(
        "frequency_allocation pearson={:.3f} p_ge={:.5f}".format(
            allocation["pair_count_vs_corpus_pearson"],
            allocation["label_shuffle_p_ge"],
        )
    )
    print(
        "best_source_fill accuracy={:.3f} p_ge={:.3f}".format(
            results["source_fill"]["best"]["accuracy"],
            results["source_fill"]["best_source_shuffle_p_ge"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
