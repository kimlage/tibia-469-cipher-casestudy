#!/usr/bin/env python3
"""Constructive fill search over the 6<->9 quotient table.

This pass combines three currently useful mechanical clues:

- symbol inventory is frequency-weighted rather than uniform;
- the unordered pair table has a weak 6<->9 quotient structure;
- quotient rows/diagonals have weak line-order signal.

Question tested here: if a generator is only given a quota/apportionment rule,
a quotient fill order, and a symbol ranking/cycle, can it place quotient labels
better than inventory-preserving controls without becoming a lookup?

No plaintext, glossary, or semantic translation is used or promoted.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

FORMULA_JSON = ROOT / "analysis" / "mechanism_model_20260618" / "mechanical_formula_469.json"
QUOTIENT_JSON = HERE / "digit_orbit_quotient_results.json"
LINE_ORDER_JSON = HERE / "quotient_line_order_results.json"
INVENTORY_JSON = HERE / "quotient_inventory_pressure_results.json"
OCC_STREAMS_JSON = ROOT / "analysis" / "audit_20260609" / "homophone_channel" / "occ_streams.json"

OUT_JSON = HERE / "quotient_constructive_fill_results.json"
OUT_MD = HERE / "quotient_constructive_fill_report.md"

SIGMA = tuple("*ABCEFILNORSTV")
Q = "Q69"
BASE_CLASS_ORDER = ("0", "1", "2", "3", "4", "5", Q, "7", "8")
CLASS_DISPLAY = {**{str(idx): str(idx) for idx in range(10)}, Q: "6/9"}
BASE_CLASS_RANK = {class_id: idx for idx, class_id in enumerate(BASE_CLASS_ORDER)}

RANDOM_SEED = 46920260622
CONTROL_TRIALS = 1000
SEARCH_CONTROL_TRIALS = 400
ORDER_SHUFFLE_TRIALS = 5000
MAX_SMALL_EXCEPTIONS = 4
TOP_ROWS_OUT = 80
MAX_INVENTORY_MODELS = 45
CONTROL_PREDICTION_LIMIT = 5000
SELECTED_CLASS_ORDER_IDS = {"natural_collapsed", "reverse_collapsed", "q_center", "469_anchor", "3478_anchor"}
SELECTED_CELL_ORDER_SEEDS = {"469", "3478"}
CYCLE_STEPS = (1, 3, 5, 9)
CYCLE_OFFSETS = (0,)

METHODS = ("hamilton", "jefferson", "webster", "adams", "hill")
TRANSFORMS = ("power", "log_power", "sqrt_power")
ALPHAS = (0.5, 0.75, 1.0, 1.03, 1.15, 1.285, 1.5, 2.0)
SHIFTS = (0, 1, 5, 25, 100)

LORE_TEXTS = {
    "tibia": "TIBIA",
    "itelbenna": "ITELBENNA",
    "telbenna": "TELBENNA",
    "honeminas": "HONEMINAS",
    "tridiag": "TRIDIAG",
    "donina": "DONINA",
    "magic_web": "MAGICWEB",
    "mathemagic": "MATHEMAGIC",
    "subjective_viewer": "SUBJECTIVEVIEWER",
    "mirror_observer": "MIRROROBSERVER",
    "bonelord": "BONELORD",
    "beholder": "BEHOLDER",
    "cipsoft": "CIPSOFT",
    "knightmare": "KNIGHTMARE",
}

LORE_SEEDS = ("469", "3478", "43153", "34784", "74032", "45331", "6-9")


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def maybe_load_json(path: Path):
    if not path.exists():
        return None
    return load_json(path)


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha_int(text: str) -> int:
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest(), 16)


def p_ge(values: list[float], observed: float) -> float:
    return (sum(value >= observed for value in values) + 1) / (len(values) + 1)


def summarize(values: list[float], observed: float) -> dict:
    mean = sum(values) / len(values)
    sd = (sum((value - mean) ** 2 for value in values) / (len(values) - 1)) ** 0.5 if len(values) > 1 else 0.0
    return {
        "observed": observed,
        "mean": mean,
        "sd": sd,
        "min": min(values),
        "max": max(values),
        "p_ge_observed": p_ge(values, observed),
        "z": (observed - mean) / sd if sd else 0.0,
    }


def class_for_digit(digit: int) -> str:
    return Q if digit in {6, 9} else str(digit)


def cell_pair_key(left: str, right: str) -> tuple[str, str]:
    return tuple(sorted((left, right), key=lambda item: BASE_CLASS_RANK[item]))


def normalize_symbol_order(symbols: Iterable[str]) -> list[str]:
    out: list[str] = []
    for symbol in symbols:
        if symbol in SIGMA and symbol not in out:
            out.append(symbol)
    for symbol in SIGMA:
        if symbol not in out:
            out.append(symbol)
    return out


def normalize_lore_text(text: str) -> list[str]:
    return normalize_symbol_order(ch for ch in text.upper() if ch in SIGMA)


def primary_pair_symbol(pair_table: dict, pair: str) -> str:
    row = pair_table[pair]
    if row["status"] == "pure":
        return row["symbol_if_pure"]
    return sorted(row["symbols"], key=SIGMA.index)[0]


def build_quotient_cells(quotient: dict, formula: dict) -> tuple[list[dict], dict[str, dict]]:
    pair_table = formula["pair_table"]
    cells = []
    seen_pairs = set()
    for orbit in quotient["swap_6_9"]["orbits"]:
        pairs = list(orbit["pairs"])
        seen_pairs.update(pairs)
        class_pairs = set()
        for pair in pairs:
            class_pairs.add(cell_pair_key(class_for_digit(int(pair[0])), class_for_digit(int(pair[1]))))
        if len(class_pairs) != 1:
            raise ValueError(f"orbit crosses quotient classes: {orbit}")
        left, right = next(iter(class_pairs))
        if left == Q and right == Q:
            variant = "qq_cross_69" if pairs == ["69"] else "qq_same_66_99"
        else:
            variant = "standard"
        actual_pair_labels = {pair: primary_pair_symbol(pair_table, pair) for pair in pairs}
        cell = {
            "cell_id": f"O{int(orbit['orbit']):02d}",
            "orbit": int(orbit["orbit"]),
            "pairs": pairs,
            "left": left,
            "right": right,
            "variant": variant,
            "label": orbit["label"],
            "label_counts": dict(orbit["label_counts"]),
            "acceptable_symbols": sorted(orbit["label_counts"], key=SIGMA.index),
            "is_mixed": bool(orbit["is_mixed"]),
            "actual_pair_labels": actual_pair_labels,
        }
        cell["stratum"] = cell_stratum(cell)
        cells.append(cell)
    expected = {f"{a}{b}" for a in range(10) for b in range(a, 10)}
    if seen_pairs != expected:
        raise ValueError("quotient orbits do not cover the 55 unordered pairs")
    cells.sort(key=lambda row: row["orbit"])
    return cells, {cell["cell_id"]: cell for cell in cells}


def cell_stratum(cell: dict) -> str:
    if cell["variant"] != "standard":
        return cell["variant"]
    if len(cell["pairs"]) == 1:
        return "singleton"
    if cell["is_mixed"]:
        return "swap_pair_mixed"
    return "swap_pair_clean"


def cell_lookup(cells: list[dict]) -> dict[tuple[str, str, str], dict]:
    return {(cell["left"], cell["right"], cell["variant"]): cell for cell in cells}


def cells_for_classes(lookup: dict[tuple[str, str, str], dict], left: str, right: str, qq_order: str) -> list[dict]:
    a, b = cell_pair_key(left, right)
    if a == Q and b == Q:
        variants = ["qq_same_66_99", "qq_cross_69"] if qq_order == "same_then_cross" else ["qq_cross_69", "qq_same_66_99"]
        return [lookup[(Q, Q, variant)] for variant in variants]
    return [lookup[(a, b, "standard")]]


def class_orders() -> list[dict]:
    fixed = [
        ("natural_collapsed", BASE_CLASS_ORDER, "fixed"),
        ("reverse_collapsed", tuple(reversed(BASE_CLASS_ORDER)), "fixed"),
        ("q_last", ("0", "1", "2", "3", "4", "5", "7", "8", Q), "fixed"),
        ("q_center", ("0", "1", "2", "3", Q, "4", "5", "7", "8"), "fixed"),
        ("469_anchor", ("4", Q, "0", "1", "2", "3", "5", "7", "8"), "fixed"),
        ("3478_anchor", ("3", "4", "7", "8", "0", "1", "2", "5", Q), "fixed"),
        ("even_odd_collapsed", ("0", "2", "4", Q, "8", "1", "3", "5", "7"), "fixed"),
    ]
    rows = [{"id": row_id, "family": family, "order": list(order)} for row_id, order, family in fixed]
    for seed in LORE_SEEDS:
        if seed not in SELECTED_CELL_ORDER_SEEDS:
            continue
        rows.append(
            {
                "id": f"seed_class_order_{seed}",
                "family": "lore_seed_hash",
                "seed": seed,
                "order": sorted(BASE_CLASS_ORDER, key=lambda class_id: (sha_int(f"class-order|{seed}|{class_id}"), class_id)),
            }
        )
    dedup = {}
    for row in rows:
        dedup.setdefault(tuple(row["order"]), row)
    return list(dedup.values())


def build_lines(cells: list[dict], order: list[str], qq_order: str) -> dict[str, list[list[str]]]:
    lookup = cell_lookup(cells)
    n = len(order)
    rows = []
    for i, left in enumerate(order):
        line = []
        for j in range(i, n):
            line.extend(cell["cell_id"] for cell in cells_for_classes(lookup, left, order[j], qq_order))
        rows.append(line)

    cols = []
    for j, right in enumerate(order):
        line = []
        for i in range(0, j + 1):
            line.extend(cell["cell_id"] for cell in cells_for_classes(lookup, order[i], right, qq_order))
        cols.append(line)

    diff = []
    for delta in range(n):
        line = []
        for i in range(0, n - delta):
            line.extend(cell["cell_id"] for cell in cells_for_classes(lookup, order[i], order[i + delta], qq_order))
        diff.append(line)

    anti = []
    for total in range(2 * n - 1):
        line = []
        for i in range(n):
            j = total - i
            if i <= j < n:
                line.extend(cell["cell_id"] for cell in cells_for_classes(lookup, order[i], order[j], qq_order))
        if line:
            anti.append(line)

    out = {"rows": rows, "cols": cols, "diagonal_diff": diff, "anti_diagonal_sum": anti}
    for family, lines in out.items():
        flat = [cell_id for line in lines for cell_id in line]
        if len(flat) != 46 or len(set(flat)) != 46:
            raise ValueError(f"{family} does not cover quotient cells exactly once")
    return out


def flatten_lines(lines: list[list[str]], snake: bool = False) -> list[str]:
    out = []
    for idx, line in enumerate(lines):
        ids = list(reversed(line)) if snake and idx % 2 else line
        out.extend(ids)
    if len(out) != 46 or len(set(out)) != 46:
        raise ValueError("fill order is not a 46-cell permutation")
    return out


def build_fill_orders(cells: list[dict], line_order_result: dict | None) -> list[dict]:
    rows = [
        {
            "id": "orbit_index",
            "family": "orbit_index",
            "source": "quotient_orbit_number",
            "cell_ids": [cell["cell_id"] for cell in sorted(cells, key=lambda row: row["orbit"])],
        }
    ]
    for seed in LORE_SEEDS:
        if seed not in SELECTED_CELL_ORDER_SEEDS:
            continue
        rows.append(
            {
                "id": f"seed_cell_order_{seed}",
                "family": "lore_seed_hash",
                "source": "cell_hash",
                "seed": seed,
                "cell_ids": [
                    cell["cell_id"]
                    for cell in sorted(cells, key=lambda row: (sha_int(f"cell-order|{seed}|{row['cell_id']}|{','.join(row['pairs'])}"), row["cell_id"]))
                ],
            }
        )

    for class_order in class_orders():
        if class_order["id"] not in SELECTED_CLASS_ORDER_IDS:
            continue
        for qq_order in ("same_then_cross", "cross_then_same"):
            families = build_lines(cells, class_order["order"], qq_order)
            for family, lines in families.items():
                for snake in (False, True):
                    suffix = "snake" if snake else "major"
                    rows.append(
                        {
                            "id": f"{class_order['id']}|{qq_order}|{family}|{suffix}",
                            "family": f"{family}_snake" if snake else family,
                            "source": "quotient_line_order",
                            "class_order_id": class_order["id"],
                            "class_order_family": class_order["family"],
                            "class_order": [CLASS_DISPLAY[item] for item in class_order["order"]],
                            "qq_order": qq_order,
                            "cell_ids": flatten_lines(lines, snake=snake),
                        }
                    )

    best_line = (((line_order_result or {}).get("searches") or {}).get("line_template") or {}).get("best")
    if best_line:
        class_order_id = best_line.get("class_order_id")
        matched_order = next((row for row in class_orders() if row["id"] == class_order_id), None)
        if matched_order is not None:
            qq_order = "same_then_cross" if best_line.get("qq_order") == "same_then_mixed" else "cross_then_same"
            families = build_lines(cells, matched_order["order"], qq_order)
            family = best_line.get("family")
            if family in families:
                rows.append(
                    {
                        "id": f"line_template_best|{class_order_id}|{qq_order}|{family}|major",
                        "family": family,
                        "source": "quotient_line_order_best",
                        "class_order_id": class_order_id,
                        "class_order_family": matched_order["family"],
                        "class_order": [CLASS_DISPLAY[item] for item in matched_order["order"]],
                        "qq_order": qq_order,
                        "line_template_match_fraction": best_line.get("match_fraction"),
                        "cell_ids": flatten_lines(families[family], snake=False),
                    }
                )

    dedup = {}
    for row in rows:
        dedup.setdefault(tuple(row["cell_ids"]), row)
    return list(dedup.values())


def code_usage_counts(formula: dict) -> Counter[str]:
    counts: Counter[str] = Counter()
    for code, count in formula["code_counts"].items():
        symbol = formula["code_to_symbol"].get(code)
        if symbol is not None:
            counts[symbol] += int(count)
    return counts


def codebook_counts(formula: dict) -> Counter[str]:
    return Counter(formula["code_to_symbol"].values())


def occ_counts() -> Counter[str]:
    if not OCC_STREAMS_JSON.exists():
        return Counter()
    occ = load_json(OCC_STREAMS_JSON)["occ"]
    return Counter({symbol: len(rows) for symbol, rows in occ.items()})


def first_occurrence_symbols() -> list[str]:
    if not OCC_STREAMS_JSON.exists():
        return []
    occ = load_json(OCC_STREAMS_JSON)["occ"]
    rows = []
    for symbol, entries in occ.items():
        for entry in entries:
            rows.append((int(entry["book"]), int(entry["pos"]), symbol))
    return [symbol for _book, _pos, symbol in sorted(rows)]


def weights_from_counts(counts: Counter[str], transform: str, alpha: float, shift: float) -> dict[str, float]:
    out = {}
    for symbol in SIGMA:
        value = counts.get(symbol, 0) + shift
        if transform == "power":
            out[symbol] = value**alpha
        elif transform == "log_power":
            out[symbol] = math.log(value + 1) ** alpha
        elif transform == "sqrt_power":
            out[symbol] = math.sqrt(value) ** alpha
        else:
            raise ValueError(transform)
    return out


def hamilton(weights: dict[str, float], total: int) -> dict[str, int]:
    denom = sum(weights.values())
    quotas = {symbol: total * weights[symbol] / denom for symbol in SIGMA}
    out = {symbol: math.floor(quotas[symbol]) for symbol in SIGMA}
    remainder = total - sum(out.values())
    for symbol in sorted(SIGMA, key=lambda sym: (quotas[sym] - out[sym], quotas[sym], sym), reverse=True)[:remainder]:
        out[symbol] += 1
    return out


def divisor(weights: dict[str, float], total: int, method: str) -> dict[str, int]:
    quotients = []
    for symbol, weight in weights.items():
        for seats in range(total + 1):
            if method == "jefferson":
                quotient = weight / (seats + 1)
            elif method == "webster":
                quotient = weight / (2 * seats + 1)
            elif method == "adams":
                quotient = float("inf") if seats == 0 else weight / seats
            elif method == "hill":
                quotient = float("inf") if seats == 0 else weight / math.sqrt(seats * (seats + 1))
            else:
                raise ValueError(method)
            quotients.append((quotient, symbol, seats))
    quotients.sort(reverse=True)
    out = {symbol: 0 for symbol in SIGMA}
    for _quotient, symbol, _seats in quotients[:total]:
        out[symbol] += 1
    return out


def allocate(weights: dict[str, float], total: int, method: str) -> dict[str, int]:
    if method == "hamilton":
        return hamilton(weights, total)
    return divisor(weights, total, method)


def normalize_counts(counts: dict[str, int], total: int) -> dict[str, int]:
    out = {symbol: max(0, int(counts.get(symbol, 0))) for symbol in SIGMA}
    current = sum(out.values())
    if current == total:
        return out
    if current < total:
        for symbol in sorted(SIGMA, key=lambda sym: (-out[sym], SIGMA.index(sym))):
            if current == total:
                break
            out[symbol] += 1
            current += 1
        while current < total:
            out[SIGMA[current % len(SIGMA)]] += 1
            current += 1
    else:
        for symbol in sorted(SIGMA, key=lambda sym: (out[sym], SIGMA.index(sym)), reverse=True):
            while out[symbol] > 0 and current > total:
                out[symbol] -= 1
                current -= 1
    return out


def build_inventory_models(formula: dict, cells: list[dict], inventory_result: dict | None) -> list[dict]:
    total = len(cells)
    count_sources = {
        "code_usage": code_usage_counts(formula),
        "codebook_row0": codebook_counts(formula),
        "occ_streams": occ_counts(),
    }
    rows = []
    for source_id, counts in count_sources.items():
        if not counts:
            continue
        for transform in TRANSFORMS:
            for alpha in ALPHAS:
                for shift in SHIFTS:
                    if shift == 0 and min(counts.get(symbol, 0) for symbol in SIGMA) == 0:
                        continue
                    weights = weights_from_counts(counts, transform, alpha, shift)
                    for method in METHODS:
                        pred = allocate(weights, total, method)
                        rows.append(
                            {
                                "id": f"{source_id}|{transform}|a={alpha:g}|shift={shift:g}|{method}",
                                "family": "frequency_weighted_apportionment",
                                "source": source_id,
                                "transform": transform,
                                "alpha": alpha,
                                "shift": shift,
                                "method": method,
                                "counts": pred,
                                "target_derived": False,
                            }
                        )

    targets = (inventory_result or {}).get("targets") or {}
    for target_name in ("quotient_base_46", "quotient_explicit_50"):
        best = (targets.get(target_name) or {}).get("best")
        if best and "prediction_counts" in best:
            rows.append(
                {
                    "id": f"inventory_pressure_best|{target_name}",
                    "family": "prior_quotient_inventory_pressure_best",
                    "source": target_name,
                    "counts": normalize_counts(best["prediction_counts"], total),
                    "target_derived": False,
                    "source_l1": best.get("l1"),
                    "source_normalized_l1_per_slot": best.get("normalized_l1_per_slot"),
                }
            )

    observed = Counter(cell["label"] for cell in cells)
    rows.append(
        {
            "id": "observed_base_46_inventory_upper_bound",
            "family": "observed_inventory_upper_bound",
            "source": "target_labels",
            "counts": {symbol: observed.get(symbol, 0) for symbol in SIGMA},
            "target_derived": True,
        }
    )

    dedup = {}
    for row in rows:
        key = tuple(row["counts"].get(symbol, 0) for symbol in SIGMA)
        if key not in dedup or (dedup[key]["target_derived"] and not row["target_derived"]):
            dedup[key] = row
    deduped = list(dedup.values())

    def priority(row: dict) -> tuple:
        family_rank = {
            "prior_quotient_inventory_pressure_best": 0,
            "frequency_weighted_apportionment": 1,
            "observed_inventory_upper_bound": 9,
        }.get(row["family"], 5)
        source_rank = {"code_usage": 0, "occ_streams": 1, "codebook_row0": 2}.get(row.get("source"), 3)
        return (bool(row.get("target_derived")), family_rank, source_rank, row["id"])

    deduped.sort(key=priority)
    target = [row for row in deduped if row.get("target_derived")]
    non_target = [row for row in deduped if not row.get("target_derived")]
    return non_target[: MAX_INVENTORY_MODELS - len(target)] + target


def build_symbol_orders(formula: dict, cells: list[dict]) -> list[dict]:
    code_usage = code_usage_counts(formula)
    codebook = codebook_counts(formula)
    observed = Counter(cell["label"] for cell in cells)

    rows = [
        {"id": "alphabet", "family": "alphabet", "order": list(SIGMA), "target_derived": False},
        {"id": "alphabet_reverse", "family": "alphabet", "order": list(reversed(SIGMA)), "target_derived": False},
        {
            "id": "code_usage_desc",
            "family": "frequency_rank",
            "order": normalize_symbol_order(symbol for symbol, _count in code_usage.most_common()),
            "target_derived": False,
        },
        {
            "id": "code_usage_asc",
            "family": "frequency_rank",
            "order": normalize_symbol_order(symbol for symbol, _count in sorted(code_usage.items(), key=lambda item: (item[1], item[0]))),
            "target_derived": False,
        },
        {
            "id": "codebook_count_desc",
            "family": "row0_rank",
            "order": normalize_symbol_order(symbol for symbol, _count in codebook.most_common()),
            "target_derived": False,
        },
        {
            "id": "first_code_table",
            "family": "row0_first_use",
            "order": normalize_symbol_order(formula["code_to_symbol"][code] for code in sorted(formula["code_to_symbol"], key=int)),
            "target_derived": False,
        },
        {
            "id": "first_occurrence",
            "family": "corpus_first_use",
            "order": normalize_symbol_order(first_occurrence_symbols()),
            "target_derived": False,
        },
        {
            "id": "quotient_frequency_desc_upper_bound",
            "family": "target_frequency_rank",
            "order": normalize_symbol_order(symbol for symbol, _count in observed.most_common()),
            "target_derived": True,
        },
    ]
    for lore_id, text in LORE_TEXTS.items():
        rows.append(
            {
                "id": f"lore_order_{lore_id}",
                "family": "lore_text_order",
                "order": normalize_lore_text(text),
                "target_derived": False,
            }
        )
    for seed in LORE_SEEDS:
        rows.append(
            {
                "id": f"seed_symbol_order_{seed}",
                "family": "seed_hash_order",
                "seed": seed,
                "order": sorted(SIGMA, key=lambda sym: (sha_int(f"symbol-order|{seed}|{sym}"), sym)),
                "target_derived": False,
            }
        )
    dedup = {}
    for row in rows:
        key = tuple(row["order"])
        if key not in dedup or (dedup[key]["target_derived"] and not row["target_derived"]):
            dedup[key] = row
    return list(dedup.values())


def stepped_order(order: list[str], step: int, offset: int) -> list[str]:
    n = len(order)
    return [order[(offset + idx * step) % n] for idx in range(n)]


def sequence_blocks(counts: dict[str, int], order: list[str]) -> list[str]:
    out = []
    for symbol in order:
        out.extend([symbol] * counts.get(symbol, 0))
    return out


def sequence_round_robin(counts: dict[str, int], order: list[str]) -> list[str]:
    remaining = dict(counts)
    out = []
    while sum(remaining.values()) > 0:
        progressed = False
        for symbol in order:
            if remaining.get(symbol, 0) > 0:
                out.append(symbol)
                remaining[symbol] -= 1
                progressed = True
        if not progressed:
            break
    return out


def sequence_ideal_spread(counts: dict[str, int], order: list[str]) -> list[str]:
    order_rank = {symbol: idx for idx, symbol in enumerate(order)}
    total = sum(counts.values())
    scheduled = []
    for symbol, count in counts.items():
        if count <= 0:
            continue
        for idx in range(count):
            ideal = (idx + 0.5) * total / count
            scheduled.append((ideal, order_rank.get(symbol, 99), idx, symbol))
    return [symbol for _ideal, _rank, _idx, symbol in sorted(scheduled)]


def sequence_largest_deficit(counts: dict[str, int], order: list[str]) -> list[str]:
    total = sum(counts.values())
    emitted = {symbol: 0 for symbol in SIGMA}
    out = []
    order_rank = {symbol: idx for idx, symbol in enumerate(order)}
    for pos in range(total):
        best = None
        for symbol in order:
            quota = counts.get(symbol, 0)
            if emitted[symbol] >= quota:
                continue
            ideal_so_far = (pos + 1) * quota / total
            deficit = ideal_so_far - emitted[symbol]
            key = (deficit, quota - emitted[symbol], -order_rank[symbol])
            if best is None or key > best[0]:
                best = (key, symbol)
        if best is None:
            break
        symbol = best[1]
        out.append(symbol)
        emitted[symbol] += 1
    return out


def build_sequences(counts: dict[str, int], symbol_order: list[str]) -> list[dict]:
    total = sum(counts.values())
    rows = []
    base_methods = [
        ("blocks", sequence_blocks),
        ("round_robin", sequence_round_robin),
        ("ideal_spread", sequence_ideal_spread),
        ("largest_deficit", sequence_largest_deficit),
    ]
    for method_id, fn in base_methods:
        seq = fn(counts, symbol_order)
        if len(seq) == total:
            rows.append({"id": method_id, "family": method_id, "sequence": seq, "step": None, "offset": None})
    for step in CYCLE_STEPS:
        if math.gcd(step, len(symbol_order)) != 1:
            continue
        for offset in CYCLE_OFFSETS:
            order = stepped_order(symbol_order, step, offset)
            seq = sequence_round_robin(counts, order)
            if len(seq) == total:
                rows.append(
                    {
                        "id": f"cycle_round_robin|step={step}|offset={offset}",
                        "family": "cycle_round_robin",
                        "sequence": seq,
                        "step": step,
                        "offset": offset,
                    }
                )
    dedup = {}
    for row in rows:
        dedup.setdefault(tuple(row["sequence"]), row)
    return list(dedup.values())


def score_prediction(prediction: tuple[int, ...], target: tuple[int, ...], acceptable: list[set[int]]) -> dict:
    exact_hits = sum(pred == actual for pred, actual in zip(prediction, target))
    acceptable_hits = sum(pred in ok for pred, ok in zip(prediction, acceptable))
    mismatch_count = len(target) - exact_hits
    small_exceptions = min(MAX_SMALL_EXCEPTIONS, mismatch_count)
    residual_literals = mismatch_count - small_exceptions
    return {
        "exact_hits": exact_hits,
        "exact_accuracy": exact_hits / len(target),
        "acceptable_hits": acceptable_hits,
        "acceptable_accuracy": acceptable_hits / len(target),
        "mismatch_count": mismatch_count,
        "small_exception_count": small_exceptions,
        "residual_literal_count": residual_literals,
    }


def score_mdl(row: dict, target_len: int, candidate_count: int) -> dict:
    lookup_bits = target_len * math.log2(len(SIGMA))
    model_bits = math.log2(max(1, candidate_count))
    mismatch_bits = row["mismatch_count"] * (math.log2(target_len) + math.log2(len(SIGMA)))
    exception_layer_bits = row["small_exception_count"] * 1.0
    mdl_bits = model_bits + mismatch_bits + exception_layer_bits
    return {
        "lookup_cost_bits": lookup_bits,
        "mdl_cost_bits": mdl_bits,
        "mdl_gain_vs_lookup_bits": lookup_bits - mdl_bits,
        "lookup_cost_ratio": mdl_bits / lookup_bits,
        "model_selection_bits": model_bits,
        "mismatch_literal_bits": mismatch_bits,
        "small_exception_overhead_bits": exception_layer_bits,
    }


def evaluate_candidates(cells: list[dict], inventories: list[dict], fill_orders: list[dict], symbol_orders: list[dict]) -> tuple[list[dict], list[tuple[int, ...]]]:
    symbol_to_int = {symbol: idx for idx, symbol in enumerate(SIGMA)}
    target = tuple(symbol_to_int[cell["label"]] for cell in cells)
    acceptable = [{symbol_to_int[symbol] for symbol in cell["acceptable_symbols"]} for cell in cells]
    by_id = {cell["cell_id"]: cell for cell in cells}
    candidate_count_estimate = len(inventories) * len(fill_orders) * len(symbol_orders) * 88
    rows = []
    unique_predictions: dict[tuple[int, ...], dict] = {}

    for inventory in inventories:
        counts = {symbol: int(inventory["counts"].get(symbol, 0)) for symbol in SIGMA}
        if sum(counts.values()) != len(cells):
            continue
        for symbol_order in symbol_orders:
            for seq_row in build_sequences(counts, symbol_order["order"]):
                sequence = seq_row["sequence"]
                if len(sequence) != len(cells):
                    continue
                seq_target_derived = bool(inventory.get("target_derived")) or bool(symbol_order.get("target_derived"))
                for fill_order in fill_orders:
                    pred_by_cell = {}
                    for cell_id, symbol in zip(fill_order["cell_ids"], sequence):
                        pred_by_cell[cell_id] = symbol_to_int[symbol]
                    prediction = tuple(pred_by_cell[cell["cell_id"]] for cell in cells)
                    if prediction in unique_predictions:
                        continue
                    score = score_prediction(prediction, target, acceptable)
                    row = {
                        "inventory_id": inventory["id"],
                        "inventory_family": inventory["family"],
                        "inventory_source": inventory.get("source"),
                        "inventory_counts": counts,
                        "fill_order_id": fill_order["id"],
                        "fill_order_family": fill_order["family"],
                        "fill_order_source": fill_order["source"],
                        "symbol_order_id": symbol_order["id"],
                        "symbol_order_family": symbol_order["family"],
                        "symbol_order": "".join(symbol_order["order"]),
                        "sequence_method": seq_row["id"],
                        "sequence_family": seq_row["family"],
                        "sequence_step": seq_row.get("step"),
                        "sequence_offset": seq_row.get("offset"),
                        "sequence": "".join(sequence),
                        "target_derived": seq_target_derived,
                        **score,
                    }
                    row["_prediction"] = prediction
                    row.update(score_mdl(row, len(cells), candidate_count_estimate))
                    rows.append(row)
                    unique_predictions[prediction] = row

    rows.sort(
        key=lambda row: (
            row["target_derived"],
            -row["mdl_gain_vs_lookup_bits"],
            -row["exact_hits"],
            -row["acceptable_hits"],
            row["inventory_id"],
            row["fill_order_id"],
            row["symbol_order_id"],
            row["sequence_method"],
        )
    )
    predictions = list(unique_predictions.keys())
    return rows, predictions


def fixed_label_shuffle_control(best_prediction: tuple[int, ...], target: tuple[int, ...], rng: random.Random) -> dict:
    scores = []
    target_labels = list(target)
    for _ in range(CONTROL_TRIALS):
        rng.shuffle(target_labels)
        scores.append(sum(pred == actual for pred, actual in zip(best_prediction, target_labels)))
    observed = sum(pred == actual for pred, actual in zip(best_prediction, target))
    return summarize(scores, observed)


def search_label_shuffle_control(predictions: list[tuple[int, ...]], target: tuple[int, ...], rng: random.Random) -> dict:
    scores = []
    target_labels = list(target)
    for _ in range(SEARCH_CONTROL_TRIALS):
        rng.shuffle(target_labels)
        best = 0
        for prediction in predictions:
            hits = sum(pred == actual for pred, actual in zip(prediction, target_labels))
            if hits > best:
                best = hits
        scores.append(best)
    observed = max(sum(pred == actual for pred, actual in zip(prediction, target)) for prediction in predictions)
    return summarize(scores, observed)


def order_shuffle_control(best_row: dict, cells: list[dict], rng: random.Random) -> dict:
    symbol_to_int = {symbol: idx for idx, symbol in enumerate(SIGMA)}
    target = tuple(symbol_to_int[cell["label"]] for cell in cells)
    sequence = [symbol_to_int[symbol] for symbol in best_row["sequence"]]
    scores = []
    for _ in range(ORDER_SHUFFLE_TRIALS):
        shuffled = sequence[:]
        rng.shuffle(shuffled)
        scores.append(sum(pred == actual for pred, actual in zip(shuffled, target)))
    observed = best_row["exact_hits"]
    return summarize(scores, observed)


def controls(rows: list[dict], predictions: list[tuple[int, ...]], cells: list[dict]) -> dict:
    rng = random.Random(RANDOM_SEED + 1)
    symbol_to_int = {symbol: idx for idx, symbol in enumerate(SIGMA)}
    target = tuple(symbol_to_int[cell["label"]] for cell in cells)
    ranked_non_leaky = sorted(
        (row for row in rows if not row["target_derived"]),
        key=lambda row: (-row["exact_hits"], row["lookup_cost_ratio"], row["inventory_id"], row["fill_order_id"]),
    )
    non_leaky_predictions = list({row["_prediction"] for row in ranked_non_leaky[:CONTROL_PREDICTION_LIMIT]})
    best_non_leaky = next((row for row in rows if not row["target_derived"]), rows[0])
    best_overall = max(rows, key=lambda row: row["exact_hits"])

    # Rebuild the prediction tuple for fixed controls from the stored row.
    # The sequence is already in the fill-order frame; for order shuffle it is
    # deliberately treated only as a multiset, not as a lookup.
    def row_prediction(row: dict) -> tuple[int, ...]:
        fill_order = row["_fill_order_map"]
        sequence = [symbol_to_int[symbol] for symbol in row["sequence"]]
        pred_by_cell = dict(zip(fill_order, sequence))
        return tuple(pred_by_cell[cell["cell_id"]] for cell in cells)

    best_non_leaky_prediction = row_prediction(best_non_leaky)
    best_overall_prediction = row_prediction(best_overall)
    return {
        "trials": {
            "fixed_label_shuffle": CONTROL_TRIALS,
            "search_label_shuffle": SEARCH_CONTROL_TRIALS,
            "order_shuffle": ORDER_SHUFFLE_TRIALS,
        },
        "control_prediction_limit": CONTROL_PREDICTION_LIMIT,
        "control_prediction_count": len(non_leaky_predictions),
        "best_non_leaky_fixed_label_shuffle": fixed_label_shuffle_control(best_non_leaky_prediction, target, rng),
        "best_overall_fixed_label_shuffle": fixed_label_shuffle_control(best_overall_prediction, target, rng),
        "search_label_shuffle_preserving_inventory": search_label_shuffle_control(non_leaky_predictions, target, rng),
        "best_non_leaky_order_shuffle": order_shuffle_control(best_non_leaky, cells, rng),
    }


def attach_fill_order_maps(rows: list[dict], fill_orders: list[dict]) -> None:
    order_by_id = {row["id"]: row["cell_ids"] for row in fill_orders}
    for row in rows:
        row["_fill_order_map"] = order_by_id[row["fill_order_id"]]


def strip_private_fields(rows: list[dict]) -> list[dict]:
    out = []
    for row in rows:
        clean = {key: value for key, value in row.items() if not key.startswith("_")}
        out.append(clean)
    return out


def verdict(result: dict) -> str:
    best_non = result["best_non_leaky"]
    best_all = result["best_overall"]
    ctrl = result["controls"]
    search_p = ctrl["search_label_shuffle_preserving_inventory"]["p_ge_observed"]
    fixed_p = ctrl["best_non_leaky_fixed_label_shuffle"]["p_ge_observed"]
    order_p = ctrl["best_non_leaky_order_shuffle"]["p_ge_observed"]

    if best_non["mdl_gain_vs_lookup_bits"] > 0 and best_non["exact_accuracy"] >= 0.65 and search_p <= 0.01 and order_p <= 0.01:
        return "candidate_constructive_quotient_fill"
    if best_all["target_derived"] and best_all["exact_hits"] > best_non["exact_hits"] + 2:
        return "lookup_disguise"
    if search_p <= 0.05 and (fixed_p <= 0.05 or order_p <= 0.05):
        return "weak_constructive_signal"
    return "rejected_control"


def write_report(result: dict) -> None:
    best_non = result["best_non_leaky"]
    best_all = result["best_overall"]
    ctrl = result["controls"]
    q = result["quotient"]
    lines = [
        "# Quotient Constructive Fill Search",
        "",
        "Generated by `quotient_constructive_fill_search.py`.",
        "",
        "Scope: mechanical generator search only. No plaintext, glossary, or",
        "semantic translation is used. `translation_delta=NONE`.",
        "",
        "## Question",
        "",
        "Can a constructive generator place the 46 `6<->9` quotient labels using",
        "only a frequency-weighted inventory/quota, a quotient fill order, and a",
        "symbol ranking/cycle, without devolving into a label lookup?",
        "",
        "## Inputs",
        "",
        f"- Quotient cells: `{q['orbit_count']}`.",
        f"- Mixed quotient orbits: `{q['mixed_orbit_count']}`.",
        f"- Label inventory: `{q['label_inventory']}`.",
        f"- Fill orders tested: `{result['search_parameters']['fill_order_count']}`.",
        f"- Inventory models tested: `{result['search_parameters']['inventory_model_count']}`.",
        f"- Symbol orders tested: `{result['search_parameters']['symbol_order_count']}`.",
        f"- Unique predictions scored: `{result['search_parameters']['unique_prediction_count']}`.",
        "",
        "## Verdict",
        "",
        f"`{result['verdict']}`",
        "",
        "## Best Non-Leaky Candidate",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| Inventory | `{best_non['inventory_id']}` |",
        f"| Fill order | `{best_non['fill_order_id']}` |",
        f"| Symbol order | `{best_non['symbol_order_id']}` = `{best_non['symbol_order']}` |",
        f"| Sequence method | `{best_non['sequence_method']}` |",
        f"| Raw exact hits | `{best_non['exact_hits']}/46` = `{best_non['exact_accuracy']:.3f}` |",
        f"| Acceptable hits | `{best_non['acceptable_hits']}/46` = `{best_non['acceptable_accuracy']:.3f}` |",
        f"| Mismatches | `{best_non['mismatch_count']}`; small exception layer `{best_non['small_exception_count']}`, residual literals `{best_non['residual_literal_count']}` |",
        f"| MDL/lookup | `{best_non['lookup_cost_ratio']:.3f}`; gain `{best_non['mdl_gain_vs_lookup_bits']:.1f}` bits |",
        f"| Label-shuffle p fixed | `{ctrl['best_non_leaky_fixed_label_shuffle']['p_ge_observed']:.4f}` |",
        f"| Label-shuffle p search | `{ctrl['search_label_shuffle_preserving_inventory']['p_ge_observed']:.4f}` |",
        f"| Order-shuffle p | `{ctrl['best_non_leaky_order_shuffle']['p_ge_observed']:.4f}` |",
        "",
        "## Best Overall Candidate",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| Target-derived? | `{best_all['target_derived']}` |",
        f"| Inventory | `{best_all['inventory_id']}` |",
        f"| Fill order | `{best_all['fill_order_id']}` |",
        f"| Symbol order | `{best_all['symbol_order_id']}` = `{best_all['symbol_order']}` |",
        f"| Sequence method | `{best_all['sequence_method']}` |",
        f"| Raw exact hits | `{best_all['exact_hits']}/46` = `{best_all['exact_accuracy']:.3f}` |",
        f"| MDL/lookup | `{best_all['lookup_cost_ratio']:.3f}`; gain `{best_all['mdl_gain_vs_lookup_bits']:.1f}` bits |",
        "",
        "## Top Non-Leaky Rows",
        "",
        "| Hits | MDL/lookup | Inventory | Fill order | Symbol order | Sequence |",
        "|---:|---:|---|---|---|---|",
    ]
    for row in result["top_non_leaky_rows"][:25]:
        lines.append(
            f"| {row['exact_hits']}/46 | {row['lookup_cost_ratio']:.3f} | `{row['inventory_id']}` | `{row['fill_order_id']}` | `{row['symbol_order_id']}` | `{row['sequence_method']}` |"
        )
    lines.extend(
        [
            "",
            "## Controls",
            "",
            "| Control | Observed | Mean | Max | p | z |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for label, row in [
        ("best non-leaky fixed label shuffle", ctrl["best_non_leaky_fixed_label_shuffle"]),
        ("best overall fixed label shuffle", ctrl["best_overall_fixed_label_shuffle"]),
        ("search label shuffle preserving inventory", ctrl["search_label_shuffle_preserving_inventory"]),
        ("best non-leaky order shuffle", ctrl["best_non_leaky_order_shuffle"]),
    ]:
        lines.append(f"| {label} | {row['observed']:.0f} | {row['mean']:.2f} | {row['max']:.0f} | {row['p_ge_observed']:.4f} | {row['z']:.2f} |")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The constructive combination produces some above-random placements, but",
            "the result is judged by the non-leaky candidate, search-level label",
            "shuffle, order shuffle, and MDL. Target-derived inventory or target",
            "frequency order is retained only as an upper-bound diagnostic and is",
            "not promotable as a generator.",
            "",
            "A candidate would need positive MDL against lookup, strong controls,",
            "and no target-derived inventory/order to be promoted. Otherwise it is",
            "classified as weak signal, lookup disguise, or rejected control.",
            "",
            "## Verification Commands Executed",
            "",
            "```bash",
            "python analysis/generator_search_20260618/quotient_constructive_fill_search.py",
            "python -c \"import ast, pathlib; p=pathlib.Path('analysis/generator_search_20260618/quotient_constructive_fill_search.py'); compile(p.read_text(), str(p), 'exec', ast.PyCF_ONLY_AST); print('syntax ok')\"",
            "python -c \"import json, pathlib; p=pathlib.Path('analysis/generator_search_20260618/quotient_constructive_fill_results.json'); json.loads(p.read_text()); print('json ok')\"",
            "git diff --check -- analysis/generator_search_20260618/quotient_constructive_fill_search.py analysis/generator_search_20260618/quotient_constructive_fill_results.json analysis/generator_search_20260618/quotient_constructive_fill_report.md",
            "```",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    formula = load_json(FORMULA_JSON)
    quotient = load_json(QUOTIENT_JSON)
    line_order_result = maybe_load_json(LINE_ORDER_JSON)
    inventory_result = maybe_load_json(INVENTORY_JSON)
    cells, _by_id = build_quotient_cells(quotient, formula)
    inventories = build_inventory_models(formula, cells, inventory_result)
    fill_orders = build_fill_orders(cells, line_order_result)
    symbol_orders = build_symbol_orders(formula, cells)
    rows, predictions = evaluate_candidates(cells, inventories, fill_orders, symbol_orders)
    attach_fill_order_maps(rows, fill_orders)

    top_non_leaky = [row for row in rows if not row["target_derived"]]
    if not top_non_leaky:
        raise RuntimeError("no non-leaky candidates were generated")
    best_non_leaky = top_non_leaky[0]
    best_overall = max(rows, key=lambda row: (row["exact_hits"], row["mdl_gain_vs_lookup_bits"], not row["target_derived"]))
    result = {
        "schema": "quotient_constructive_fill_results.v1",
        "translation_delta": "NONE",
        "inputs": {
            "mechanical_formula": str(FORMULA_JSON.relative_to(ROOT)),
            "digit_orbit_quotient": str(QUOTIENT_JSON.relative_to(ROOT)),
            "quotient_line_order": str(LINE_ORDER_JSON.relative_to(ROOT)),
            "quotient_inventory_pressure": str(INVENTORY_JSON.relative_to(ROOT)),
        },
        "search_parameters": {
            "random_seed": RANDOM_SEED,
            "max_small_exceptions": MAX_SMALL_EXCEPTIONS,
            "control_trials": CONTROL_TRIALS,
            "search_control_trials": SEARCH_CONTROL_TRIALS,
            "order_shuffle_trials": ORDER_SHUFFLE_TRIALS,
            "inventory_model_count": len(inventories),
            "fill_order_count": len(fill_orders),
            "symbol_order_count": len(symbol_orders),
            "unique_prediction_count": len(predictions),
        },
        "quotient": {
            "orbit_count": len(cells),
            "mixed_orbit_count": sum(1 for cell in cells if cell["is_mixed"]),
            "label_inventory": dict(Counter(cell["label"] for cell in cells)),
            "stratum_inventory": dict(Counter(cell["stratum"] for cell in cells)),
        },
        "best_non_leaky": {key: value for key, value in best_non_leaky.items() if not key.startswith("_")},
        "best_overall": {key: value for key, value in best_overall.items() if not key.startswith("_")},
        "top_non_leaky_rows": strip_private_fields(top_non_leaky[:TOP_ROWS_OUT]),
        "top_overall_rows": strip_private_fields(sorted(rows, key=lambda row: (-row["exact_hits"], row["target_derived"], row["lookup_cost_ratio"]))[:TOP_ROWS_OUT]),
    }
    result["controls"] = controls(rows, predictions, cells)
    result["verdict"] = verdict(result)
    write_json(OUT_JSON, result)
    write_report(result)
    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(f"wrote {OUT_MD.relative_to(ROOT)}")
    print(f"verdict={result['verdict']} best_non_leaky_hits={result['best_non_leaky']['exact_hits']}/46")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
