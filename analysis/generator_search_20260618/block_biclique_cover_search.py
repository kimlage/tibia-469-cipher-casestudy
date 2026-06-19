#!/usr/bin/env python3
"""Block/biclique cover search for the 469 unordered pair table.

This pass is deliberately different from pair_rule_cover_search.py.  It does
not learn a decision list of arbitrary predicates.  Instead, it asks whether
each symbol's cells look like a small union of digit-set blocks: induced
cliques, bicliques, digit stars, interval rectangles, parity/mod classes, and
diagonal subsets.  A second pass uses the same block library as a global
priority/disjoint assignment model.

Mechanical only: no plaintext, glossary entry, or translation is produced.
"""

from __future__ import annotations

import json
import math
import random
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FORMULA_JSON = ROOT / "analysis" / "mechanism_model_20260618" / "mechanical_formula_469.json"

OUT_JSON = HERE / "block_biclique_cover_results.json"
OUT_MD = HERE / "block_biclique_cover_report.md"

SIGMA = "*ABCEFILNORSTV"
DIGITS = tuple(range(10))
PAIRS = [(a, b) for a in DIGITS for b in range(a, 10)]
PAIR_NAMES = [f"{a}{b}" for a, b in PAIRS]
PAIR_INDEX = {pair: idx for idx, pair in enumerate(PAIR_NAMES)}
ALL_MASK = (1 << len(PAIRS)) - 1

RANDOM_SEED = 46920260619
CONTROL_TRIALS = 80
INDEPENDENT_MAX_BLOCKS = 6
GLOBAL_MAX_BLOCKS = 28
GLOBAL_BUDGETS = (4, 8, 12, 18, 24, 28)

SYMBOL_BITS = math.log2(len(SIGMA))
CELL_BITS = math.log2(len(PAIRS))
MEMBERSHIP_EXCEPTION_BITS = CELL_BITS + 1.0
LABEL_EXCEPTION_BITS = CELL_BITS + SYMBOL_BITS
BLOCK_SIZE_WEIGHT = 0.08
BLOCK_OVERHEAD_BITS = 1.0

FAMILY_BASE_BITS = {
    "both_in_set": 2.5,
    "one_in_set_other_in_set": 3.2,
    "exact_digit_star": 2.8,
    "interval_block": 2.4,
    "parity_mod_class_block": 2.8,
    "diagonal_subset": 3.0,
}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def bits_for_inventory(labels: list[str]) -> float:
    counts = Counter(labels)
    out = math.lgamma(len(labels) + 1) / math.log(2)
    for count in counts.values():
        out -= math.lgamma(count + 1) / math.log(2)
    return out


def primary_pair_symbol(pair_table: dict[str, dict[str, Any]], pair: str) -> str:
    row = pair_table[pair]
    if row["status"] == "pure":
        return row["symbol_if_pure"]
    return sorted(row["symbols"])[0]


def acceptable_pair_symbols(pair_table: dict[str, dict[str, Any]], pair: str) -> set[str]:
    return set(pair_table[pair]["symbols"])


def label_masks(labels: list[str]) -> dict[str, int]:
    masks = {symbol: 0 for symbol in SIGMA}
    for idx, symbol in enumerate(labels):
        masks[symbol] |= 1 << idx
    return masks


def cells_from_mask(mask: int) -> list[str]:
    return [PAIR_NAMES[idx] for idx in range(len(PAIR_NAMES)) if mask & (1 << idx)]


def mask_for_pairs(pairs: set[tuple[int, int]]) -> int:
    mask = 0
    for a, b in pairs:
        if a > b:
            a, b = b, a
        mask |= 1 << PAIR_INDEX[f"{a}{b}"]
    return mask


def mask_both_in(digits: frozenset[int]) -> int:
    return mask_for_pairs({(a, b) for a in digits for b in digits})


def mask_cross(left: frozenset[int], right: frozenset[int]) -> int:
    return mask_for_pairs({(a, b) for a in left for b in right})


def mask_star(center: int, leaves: frozenset[int]) -> int:
    return mask_for_pairs({(center, leaf) for leaf in leaves})


def mask_diagonal(diff: int, starts: frozenset[int]) -> int:
    return mask_for_pairs({(a, a + diff) for a in starts if 0 <= a <= a + diff <= 9})


def set_name(digits: frozenset[int]) -> str:
    return "".join(str(digit) for digit in sorted(digits))


def add_digit_set(
    out: dict[frozenset[int], dict[str, Any]],
    digits: set[int] | frozenset[int],
    name: str,
    family: str,
    cost_bits: float,
) -> None:
    frozen = frozenset(digits)
    if not frozen:
        return
    old = out.get(frozen)
    if old is None or (cost_bits, len(name), name) < (old["cost_bits"], len(old["name"]), old["name"]):
        out[frozen] = {
            "digits": tuple(sorted(frozen)),
            "name": name,
            "family": family,
            "cost_bits": round(cost_bits, 4),
        }


def build_digit_sets() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    all_sets: dict[frozenset[int], dict[str, Any]] = {}
    simple_sets: dict[frozenset[int], dict[str, Any]] = {}
    interval_sets: dict[frozenset[int], dict[str, Any]] = {}
    mod_sets: dict[frozenset[int], dict[str, Any]] = {}

    def add_all(digits: set[int] | frozenset[int], name: str, family: str, cost_bits: float) -> None:
        add_digit_set(all_sets, digits, name, family, cost_bits)

    def add_simple(digits: set[int] | frozenset[int], name: str, family: str, cost_bits: float) -> None:
        add_digit_set(simple_sets, digits, name, family, cost_bits)
        add_all(digits, name, family, cost_bits)

    def add_interval(digits: set[int] | frozenset[int], name: str, cost_bits: float) -> None:
        add_digit_set(interval_sets, digits, name, "interval", cost_bits)
        add_simple(digits, name, "interval", cost_bits)

    def add_mod(digits: set[int] | frozenset[int], name: str, cost_bits: float) -> None:
        add_digit_set(mod_sets, digits, name, "mod_class", cost_bits)
        add_simple(digits, name, "mod_class", cost_bits)

    add_simple(set(DIGITS), "all", "constant", 0.5)
    for digit in DIGITS:
        add_simple({digit}, f"d{digit}", "single_digit", math.log2(10))

    for lo in DIGITS:
        for hi in range(lo, 10):
            digits = set(range(lo, hi + 1))
            span = hi - lo + 1
            add_interval(digits, f"interval_{lo}_{hi}", 3.0 + 0.18 * span)

    add_mod({0, 2, 4, 6, 8}, "parity_even", 2.0)
    add_mod({1, 3, 5, 7, 9}, "parity_odd", 2.0)
    for modulus in range(3, 6):
        for residue in range(modulus):
            digits = {digit for digit in DIGITS if digit % modulus == residue}
            add_mod(digits, f"mod_{modulus}_{residue}", 2.8 + math.log2(modulus))

    # Arbitrary small digit sets let the search detect true bicliques/stars,
    # but their cost is intentionally close to listing the digits.
    for size in range(2, 6):
        for subset in combinations(DIGITS, size):
            frozen = frozenset(subset)
            add_all(frozen, f"set_{set_name(frozen)}", "explicit_set", 1.4 + size * math.log2(10))

    # Complements of small sets are also explicit, with an added negation bit.
    for size in range(1, 5):
        for subset in combinations(DIGITS, size):
            frozen = frozenset(set(DIGITS) - set(subset))
            add_all(
                frozen,
                f"not_{set_name(frozenset(subset))}",
                "explicit_complement",
                2.4 + size * math.log2(10),
            )

    ordered_all = sorted(all_sets.values(), key=lambda row: (row["cost_bits"], len(row["digits"]), row["name"]))
    ordered_simple = sorted(simple_sets.values(), key=lambda row: (row["cost_bits"], len(row["digits"]), row["name"]))
    ordered_intervals = sorted(interval_sets.values(), key=lambda row: (row["cost_bits"], len(row["digits"]), row["name"]))
    ordered_mod = sorted(mod_sets.values(), key=lambda row: (row["cost_bits"], len(row["digits"]), row["name"]))
    return ordered_all, ordered_simple, ordered_intervals, ordered_mod


def block_cost(family: str, component_bits: float, size: int) -> float:
    return (
        FAMILY_BASE_BITS[family]
        + BLOCK_OVERHEAD_BITS
        + component_bits
        + BLOCK_SIZE_WEIGHT * size
    )


def add_block(
    out: dict[int, dict[str, Any]],
    *,
    family: str,
    name: str,
    mask: int,
    component_bits: float,
    detail: dict[str, Any],
) -> None:
    if mask == 0:
        return
    size = mask.bit_count()
    cost_bits = block_cost(family, component_bits, size)
    row = {
        "name": name,
        "family": family,
        "mask": mask,
        "size": size,
        "cost_bits": round(cost_bits, 4),
        "detail": detail,
    }
    old = out.get(mask)
    if old is None or (row["cost_bits"], row["family"], row["name"]) < (
        old["cost_bits"],
        old["family"],
        old["name"],
    ):
        out[mask] = row


def build_blocks() -> list[dict[str, Any]]:
    all_sets, simple_sets, interval_sets, mod_sets = build_digit_sets()
    blocks: dict[int, dict[str, Any]] = {}

    for desc in all_sets:
        digits = frozenset(desc["digits"])
        add_block(
            blocks,
            family="both_in_set",
            name=f"both_in_{desc['name']}",
            mask=mask_both_in(digits),
            component_bits=desc["cost_bits"],
            detail={"set": desc},
        )

    for left_idx, left_desc in enumerate(simple_sets):
        left = frozenset(left_desc["digits"])
        for right_desc in simple_sets[left_idx:]:
            right = frozenset(right_desc["digits"])
            if left_desc["name"] == "all" and right_desc["name"] == "all":
                continue
            add_block(
                blocks,
                family="one_in_set_other_in_set",
                name=f"one_in_{left_desc['name']}_other_in_{right_desc['name']}",
                mask=mask_cross(left, right),
                component_bits=left_desc["cost_bits"] + right_desc["cost_bits"],
                detail={"left": left_desc, "right": right_desc},
            )

    for center in DIGITS:
        for leaves_desc in simple_sets:
            leaves = frozenset(leaves_desc["digits"])
            add_block(
                blocks,
                family="exact_digit_star",
                name=f"star_{center}_to_{leaves_desc['name']}",
                mask=mask_star(center, leaves),
                component_bits=math.log2(10) + leaves_desc["cost_bits"],
                detail={"center": center, "leaves": leaves_desc},
            )

    for left_desc in interval_sets:
        left = frozenset(left_desc["digits"])
        for right_desc in interval_sets:
            right = frozenset(right_desc["digits"])
            if (left_desc["name"], right_desc["name"]) > (right_desc["name"], left_desc["name"]):
                continue
            add_block(
                blocks,
                family="interval_block",
                name=f"interval_block_{left_desc['name']}__{right_desc['name']}",
                mask=mask_cross(left, right),
                component_bits=left_desc["cost_bits"] + right_desc["cost_bits"],
                detail={"left_interval": left_desc, "right_interval": right_desc},
            )

    for left_desc in mod_sets:
        left = frozenset(left_desc["digits"])
        for right_desc in mod_sets:
            right = frozenset(right_desc["digits"])
            if (left_desc["name"], right_desc["name"]) > (right_desc["name"], left_desc["name"]):
                continue
            add_block(
                blocks,
                family="parity_mod_class_block",
                name=f"mod_block_{left_desc['name']}__{right_desc['name']}",
                mask=mask_cross(left, right),
                component_bits=left_desc["cost_bits"] + right_desc["cost_bits"],
                detail={"left_class": left_desc, "right_class": right_desc},
            )

    for diff in range(10):
        valid_starts = {a for a in DIGITS if a + diff <= 9}
        start_sets = all_sets if diff == 0 else simple_sets
        for starts_desc in start_sets:
            starts = frozenset(starts_desc["digits"]) & valid_starts
            if not starts:
                continue
            add_block(
                blocks,
                family="diagonal_subset",
                name=f"diag_diff_{diff}_starts_{starts_desc['name']}",
                mask=mask_diagonal(diff, starts),
                component_bits=math.log2(10) + starts_desc["cost_bits"],
                detail={"diff": diff, "starts": starts_desc},
            )

    return sorted(blocks.values(), key=lambda row: (row["cost_bits"], row["size"], row["name"]))


def public_block(block: dict[str, Any], claim_mask: int | None = None) -> dict[str, Any]:
    row = {
        "name": block["name"],
        "family": block["family"],
        "size": block["size"],
        "cost_bits": block["cost_bits"],
        "cells": cells_from_mask(block["mask"]),
        "detail": block["detail"],
    }
    if claim_mask is not None:
        row["claim_size"] = claim_mask.bit_count()
        row["claim_cells"] = cells_from_mask(claim_mask)
    return row


def cover_metrics(mask: int, target: int) -> dict[str, Any]:
    tp = (mask & target).bit_count()
    fp = (mask & ~target & ALL_MASK).bit_count()
    fn = (target & ~mask).bit_count()
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def independent_objective(blocks: list[dict[str, Any]], target: int) -> tuple[float, int, dict[str, Any]]:
    mask = 0
    block_bits = 0.0
    for block in blocks:
        mask |= block["mask"]
        block_bits += block["cost_bits"]
    metrics = cover_metrics(mask, target)
    exception_bits = (metrics["fp"] + metrics["fn"]) * MEMBERSHIP_EXCEPTION_BITS
    return block_bits + exception_bits, mask, metrics


def greedy_symbol_cover(
    symbol: str,
    target: int,
    candidates: list[dict[str, Any]],
    max_blocks: int = INDEPENDENT_MAX_BLOCKS,
) -> dict[str, Any]:
    selected: list[dict[str, Any]] = []
    current_cost, current_mask, current_metrics = independent_objective(selected, target)

    for _step in range(max_blocks):
        best = None
        for block in candidates:
            if not (block["mask"] & target):
                continue
            new_mask = current_mask | block["mask"]
            if new_mask == current_mask:
                continue
            projected = selected + [block]
            objective, _mask, metrics = independent_objective(projected, target)
            gain = current_cost - objective
            rank = (
                gain,
                metrics["tp"],
                -metrics["fp"],
                -block["cost_bits"],
                -block["size"],
            )
            if best is None or rank > best["rank"]:
                best = {
                    "rank": rank,
                    "block": block,
                    "objective": objective,
                    "mask": new_mask,
                    "metrics": metrics,
                }
        if best is None or best["rank"][0] <= 1e-9:
            break
        selected.append(best["block"])
        current_cost = best["objective"]
        current_mask = best["mask"]
        current_metrics = best["metrics"]

    target_count = target.bit_count()
    lookup_bits = target_count * CELL_BITS
    return {
        "symbol": symbol,
        "target_count": target_count,
        "block_count": len(selected),
        "blocks": [public_block(block) for block in selected],
        "cover_cells": cells_from_mask(current_mask),
        "cost_bits": current_cost,
        "lookup_membership_bits": lookup_bits,
        "gain_vs_membership_lookup_bits": lookup_bits - current_cost,
        **current_metrics,
    }


def independent_cover_summary(labels: list[str], candidates: list[dict[str, Any]]) -> dict[str, Any]:
    masks = label_masks(labels)
    rows = [
        greedy_symbol_cover(symbol, masks[symbol], candidates)
        for symbol in SIGMA
        if masks[symbol]
    ]
    total_target = sum(row["target_count"] for row in rows)
    weighted_f1 = sum(row["f1"] * row["target_count"] for row in rows) / total_target
    macro_f1 = sum(row["f1"] for row in rows) / len(rows)
    total_cost = sum(row["cost_bits"] for row in rows)
    total_lookup = sum(row["lookup_membership_bits"] for row in rows)
    exact_symbols = sum(1 for row in rows if row["fp"] == 0 and row["fn"] == 0)
    return {
        "symbol_rows": rows,
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1,
        "exact_symbol_covers": exact_symbols,
        "total_cost_bits": total_cost,
        "total_membership_lookup_bits": total_lookup,
        "gain_vs_membership_lookup_bits": total_lookup - total_cost,
    }


def default_for_remaining(remaining: int, masks: dict[str, int]) -> tuple[str, int]:
    best_symbol = max(
        SIGMA,
        key=lambda symbol: ((remaining & masks[symbol]).bit_count(), -SIGMA.index(symbol)),
    )
    return best_symbol, (remaining & masks[best_symbol]).bit_count()


def global_status(
    selected: list[dict[str, Any]],
    labels: list[str],
    masks: dict[str, int],
    raw_lookup_bits: float,
    inventory_lookup_bits: float,
) -> dict[str, Any]:
    assigned = 0
    assigned_hits = 0
    block_bits = 0.0
    public_rows = []
    predictions: list[str | None] = [None] * len(labels)

    for item in selected:
        block = item["block"]
        symbol = item["symbol"]
        claim = block["mask"] & ~assigned
        if claim == 0:
            continue
        assigned |= claim
        hits = (claim & masks[symbol]).bit_count()
        assigned_hits += hits
        block_bits += block["cost_bits"] + SYMBOL_BITS
        for idx in range(len(labels)):
            if claim & (1 << idx):
                predictions[idx] = symbol
        public_row = public_block(block, claim)
        public_row.update(
            {
                "symbol": symbol,
                "hits": hits,
                "false_hits": claim.bit_count() - hits,
            }
        )
        public_rows.append(public_row)

    remaining = ALL_MASK & ~assigned
    default_symbol, default_hits = default_for_remaining(remaining, masks)
    for idx in range(len(labels)):
        if predictions[idx] is None:
            predictions[idx] = default_symbol

    primary_hits = sum(1 for predicted, actual in zip(predictions, labels) if predicted == actual)
    errors = len(labels) - primary_hits
    model_bits = SYMBOL_BITS + block_bits
    mdl_bits = model_bits + errors * LABEL_EXCEPTION_BITS
    return {
        "block_count": len(public_rows),
        "blocks": public_rows,
        "default_symbol": default_symbol,
        "assigned_cells": assigned.bit_count(),
        "default_cells": remaining.bit_count(),
        "primary_hits": primary_hits,
        "primary_accuracy": primary_hits / len(labels),
        "primary_errors": errors,
        "model_bits": model_bits,
        "mdl_bits": mdl_bits,
        "raw_lookup_bits": raw_lookup_bits,
        "inventory_lookup_bits": inventory_lookup_bits,
        "gain_vs_raw_lookup_bits": raw_lookup_bits - mdl_bits,
        "gain_vs_inventory_lookup_bits": inventory_lookup_bits - mdl_bits,
        "mdl_ratio_vs_raw_lookup": mdl_bits / raw_lookup_bits,
        "mdl_ratio_vs_inventory_lookup": mdl_bits / inventory_lookup_bits,
        "predicted": "".join(str(symbol) for symbol in predictions),
    }


def greedy_global_trace(
    labels: list[str],
    candidates: list[dict[str, Any]],
    max_blocks: int,
) -> list[dict[str, Any]]:
    masks = label_masks(labels)
    raw_lookup_bits = len(labels) * SYMBOL_BITS
    inventory_lookup_bits = bits_for_inventory(labels)
    selected: list[dict[str, Any]] = []
    states = [
        global_status(selected, labels, masks, raw_lookup_bits, inventory_lookup_bits)
    ]
    current = states[-1]
    assigned = 0
    assigned_hits = 0
    model_bits = SYMBOL_BITS

    for _step in range(max_blocks):
        best = None
        for block in candidates:
            claim = block["mask"] & ~assigned
            if claim == 0:
                continue
            claim_size = claim.bit_count()
            claim_counts = {
                symbol: (claim & masks[symbol]).bit_count()
                for symbol in SIGMA
            }
            symbol, hits = max(
                claim_counts.items(),
                key=lambda item: (item[1], -SIGMA.index(item[0])),
            )
            if hits == 0:
                continue
            new_assigned = assigned | claim
            default_hits = max(
                (ALL_MASK & ~assigned & masks[symbol]).bit_count() - claim_counts[symbol]
                for symbol in SIGMA
            )
            primary_hits = assigned_hits + hits + default_hits
            errors = len(labels) - primary_hits
            new_model_bits = model_bits + block["cost_bits"] + SYMBOL_BITS
            mdl_bits = new_model_bits + errors * LABEL_EXCEPTION_BITS
            gain = current["mdl_bits"] - mdl_bits
            false_hits = claim_size - hits
            rank = (
                gain,
                hits,
                -false_hits,
                -block["cost_bits"],
                -block["size"],
            )
            if best is None or rank > best["rank"]:
                best = {
                    "rank": rank,
                    "item": {"block": block, "symbol": symbol},
                    "claim": claim,
                    "hits": hits,
                    "mdl_bits": mdl_bits,
                    "model_bits": new_model_bits,
                }
        if best is None or best["rank"][0] <= 1e-9:
            break
        selected.append(best["item"])
        assigned |= best["claim"]
        assigned_hits += best["hits"]
        model_bits = best["model_bits"]
        current = global_status(selected, labels, masks, raw_lookup_bits, inventory_lookup_bits)
        states.append(current)
    return states


def global_by_budget(labels: list[str], candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    trace = greedy_global_trace(labels, candidates, GLOBAL_MAX_BLOCKS)
    rows = []
    for budget in GLOBAL_BUDGETS:
        eligible = [state for state in trace if state["block_count"] <= budget]
        state = min(eligible, key=lambda row: (row["mdl_bits"], -row["primary_hits"], row["block_count"]))
        copied = dict(state)
        copied["max_blocks"] = budget
        rows.append(copied)
    return rows


def add_acceptable_hits(global_row: dict[str, Any], pair_table: dict[str, dict[str, Any]]) -> None:
    acceptable = 0
    exceptions = []
    for predicted, pair in zip(global_row["predicted"], PAIR_NAMES):
        if predicted in acceptable_pair_symbols(pair_table, pair):
            acceptable += 1
        else:
            exceptions.append(pair)
    global_row["acceptable_hits"] = acceptable
    global_row["acceptable_accuracy"] = acceptable / len(PAIR_NAMES)
    global_row["acceptable_exceptions"] = exceptions


def p_ge(values: list[float], observed: float) -> float:
    return (sum(value >= observed for value in values) + 1) / (len(values) + 1)


def p_le(values: list[float], observed: float) -> float:
    return (sum(value <= observed for value in values) + 1) / (len(values) + 1)


def summarize_controls(observed_independent: dict[str, Any], observed_global: dict[str, Any], control_rows: list[dict[str, Any]]) -> dict[str, Any]:
    independent_macro_f1 = [row["independent"]["macro_f1"] for row in control_rows]
    independent_weighted_f1 = [row["independent"]["weighted_f1"] for row in control_rows]
    independent_total_cost = [row["independent"]["total_cost_bits"] for row in control_rows]
    global_hits = [row["global"]["primary_hits"] for row in control_rows]
    global_mdl = [row["global"]["mdl_bits"] for row in control_rows]
    global_inventory_gain = [row["global"]["gain_vs_inventory_lookup_bits"] for row in control_rows]
    global_raw_gain = [row["global"]["gain_vs_raw_lookup_bits"] for row in control_rows]

    return {
        "trials": len(control_rows),
        "independent_macro_f1_mean": sum(independent_macro_f1) / len(independent_macro_f1),
        "independent_macro_f1_max": max(independent_macro_f1),
        "independent_macro_f1_p_ge": p_ge(independent_macro_f1, observed_independent["macro_f1"]),
        "independent_weighted_f1_mean": sum(independent_weighted_f1) / len(independent_weighted_f1),
        "independent_weighted_f1_max": max(independent_weighted_f1),
        "independent_weighted_f1_p_ge": p_ge(independent_weighted_f1, observed_independent["weighted_f1"]),
        "independent_total_cost_mean": sum(independent_total_cost) / len(independent_total_cost),
        "independent_total_cost_min": min(independent_total_cost),
        "independent_total_cost_p_le": p_le(independent_total_cost, observed_independent["total_cost_bits"]),
        "global_primary_hits_mean": sum(global_hits) / len(global_hits),
        "global_primary_hits_max": max(global_hits),
        "global_primary_hits_p_ge": p_ge(global_hits, observed_global["primary_hits"]),
        "global_mdl_bits_mean": sum(global_mdl) / len(global_mdl),
        "global_mdl_bits_min": min(global_mdl),
        "global_mdl_bits_p_le": p_le(global_mdl, observed_global["mdl_bits"]),
        "global_inventory_gain_mean": sum(global_inventory_gain) / len(global_inventory_gain),
        "global_inventory_gain_max": max(global_inventory_gain),
        "global_inventory_gain_p_ge": p_ge(global_inventory_gain, observed_global["gain_vs_inventory_lookup_bits"]),
        "global_raw_gain_mean": sum(global_raw_gain) / len(global_raw_gain),
        "global_raw_gain_max": max(global_raw_gain),
        "global_raw_gain_p_ge": p_ge(global_raw_gain, observed_global["gain_vs_raw_lookup_bits"]),
    }


def run_controls(labels: list[str], candidates: list[dict[str, Any]], observed_independent: dict[str, Any], observed_global: dict[str, Any]) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED)
    rows = []
    for trial in range(CONTROL_TRIALS):
        shuffled = labels[:]
        rng.shuffle(shuffled)
        independent = independent_cover_summary(shuffled, candidates)
        global_rows = global_by_budget(shuffled, candidates)
        best_global = min(global_rows, key=lambda row: (row["mdl_bits"], -row["primary_hits"], row["block_count"]))
        rows.append(
            {
                "trial": trial,
                "independent": {
                    "macro_f1": independent["macro_f1"],
                    "weighted_f1": independent["weighted_f1"],
                    "exact_symbol_covers": independent["exact_symbol_covers"],
                    "total_cost_bits": independent["total_cost_bits"],
                    "gain_vs_membership_lookup_bits": independent["gain_vs_membership_lookup_bits"],
                },
                "global": {
                    "primary_hits": best_global["primary_hits"],
                    "block_count": best_global["block_count"],
                    "mdl_bits": best_global["mdl_bits"],
                    "gain_vs_inventory_lookup_bits": best_global["gain_vs_inventory_lookup_bits"],
                    "gain_vs_raw_lookup_bits": best_global["gain_vs_raw_lookup_bits"],
                    "max_blocks": best_global["max_blocks"],
                },
            }
        )
    return {
        "summary": summarize_controls(observed_independent, observed_global, rows),
        "trial_rows": rows,
    }


def verdict(best_global: dict[str, Any], control_summary: dict[str, Any]) -> str:
    if (
        best_global["gain_vs_inventory_lookup_bits"] > 0
        and control_summary["global_inventory_gain_p_ge"] <= 0.01
        and best_global["primary_hits"] >= 45
    ):
        return "candidate_block_formula"
    if (
        best_global["gain_vs_inventory_lookup_bits"] > 0
        and control_summary["global_inventory_gain_p_ge"] <= 0.05
    ):
        return "weak_block_signal_not_promoted"
    if best_global["gain_vs_raw_lookup_bits"] > 0 and control_summary["global_raw_gain_p_ge"] <= 0.05:
        return "compression_only_not_semantic"
    return "lookup_disguise"


def block_family_counts(blocks: list[dict[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(block["family"] for block in blocks).items()))


def write_report(result: dict[str, Any]) -> None:
    best = result["best_global"]
    ctrl = result["control"]["summary"]
    independent = result["independent_cover"]
    lines = [
        "# Block/Biclique Cover Search",
        "",
        "Generated by `block_biclique_cover_search.py`.",
        "",
        "This pass tests whether the unordered 55-cell pair table can be",
        "described as a small union of digit-set blocks per symbol, plus a",
        "global priority/disjoint assignment model. It is mechanical only:",
        "no plaintext, glossary entry, or translation is produced.",
        "",
        "## Summary",
        "",
        "| Block candidates | Independent weighted F1 | Global hits | Global blocks | MDL bits | Inventory lookup bits | p(hit) | p(MDL<=) | Verdict |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---|",
        (
            f"| {result['block_library']['candidate_count']} | "
            f"{independent['weighted_f1']:.3f} | "
            f"{best['primary_hits']}/55 ({best['acceptable_hits']}/55 acceptable) | "
            f"{best['block_count']} | "
            f"{best['mdl_bits']:.1f} | "
            f"{best['inventory_lookup_bits']:.1f} | "
            f"{ctrl['global_primary_hits_p_ge']:.4f} | "
            f"{ctrl['global_mdl_bits_p_le']:.4f} | "
            f"`{result['verdict']}` |"
        ),
        "",
        "## Relation To Pair Rule Cover",
        "",
        "`pair_rule_cover_search.py` tested a decision list of predicates over",
        "individual cells. This script uses those same cells as a colored",
        "digit graph and asks whether each color class decomposes into a few",
        "set blocks: `both_in_set`, `one_in_set_other_in_set`, exact digit",
        "stars, interval blocks, parity/mod blocks, and diagonal subsets.",
        "",
        "## Global Budget Sweep",
        "",
        "| Max blocks | Chosen blocks | Primary hits | Acceptable hits | MDL bits | MDL/inventory lookup |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for row in result["global_by_budget"]:
        lines.append(
            f"| {row['max_blocks']} | {row['block_count']} | "
            f"{row['primary_hits']}/55 | {row['acceptable_hits']}/55 | "
            f"{row['mdl_bits']:.1f} | {row['mdl_ratio_vs_inventory_lookup']:.3f} |"
        )

    lines.extend(
        [
            "",
        "## Independent Symbol Covers",
        "",
        "| Symbol | Target | Blocks | F1 | TP | FP | FN | Cost bits | Best blocks |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for row in independent["symbol_rows"]:
        block_names = ", ".join(f"`{block['name']}`" for block in row["blocks"][:4])
        if len(row["blocks"]) > 4:
            block_names += ", ..."
        lines.append(
            f"| `{row['symbol']}` | {row['target_count']} | {row['block_count']} | "
            f"{row['f1']:.3f} | {row['tp']} | {row['fp']} | {row['fn']} | "
            f"{row['cost_bits']:.1f} | {block_names or '-'} |"
        )

    lines.extend(
        [
            "",
            "## Best Global Disjoint Assignment",
            "",
            f"Default symbol: `{best['default_symbol']}`. The model assigns",
            f"{best['assigned_cells']} cells by blocks and leaves",
            f"{best['default_cells']} cells to the default.",
            "",
            "| # | Symbol | Family | Block | Claim | Hits | False hits | Cost bits |",
            "|---:|---|---|---|---:|---:|---:|---:|",
        ]
    )
    for idx, block in enumerate(best["blocks"], start=1):
        lines.append(
            f"| {idx} | `{block['symbol']}` | `{block['family']}` | `{block['name']}` | "
            f"{block['claim_size']} | {block['hits']} | {block['false_hits']} | "
            f"{block['cost_bits']:.1f} |"
        )

    lines.extend(
        [
            "",
            "## Controls",
            "",
            "| Metric | Observed | Shuffle mean | Shuffle best | p |",
            "|---|---:|---:|---:|---:|",
            (
                f"| Independent macro F1 | {independent['macro_f1']:.3f} | "
                f"{ctrl['independent_macro_f1_mean']:.3f} | "
                f"{ctrl['independent_macro_f1_max']:.3f} | "
                f"{ctrl['independent_macro_f1_p_ge']:.4f} |"
            ),
            (
                f"| Independent weighted F1 | {independent['weighted_f1']:.3f} | "
                f"{ctrl['independent_weighted_f1_mean']:.3f} | "
                f"{ctrl['independent_weighted_f1_max']:.3f} | "
                f"{ctrl['independent_weighted_f1_p_ge']:.4f} |"
            ),
            (
                f"| Global primary hits | {best['primary_hits']} | "
                f"{ctrl['global_primary_hits_mean']:.2f} | "
                f"{ctrl['global_primary_hits_max']} | "
                f"{ctrl['global_primary_hits_p_ge']:.4f} |"
            ),
            (
                f"| Global MDL bits | {best['mdl_bits']:.1f} | "
                f"{ctrl['global_mdl_bits_mean']:.1f} | "
                f"{ctrl['global_mdl_bits_min']:.1f} | "
                f"{ctrl['global_mdl_bits_p_le']:.4f} |"
            ),
            "",
            "## Interpretation",
            "",
        ]
    )
    if result["verdict"] == "lookup_disguise":
        lines.extend(
            [
                "The block library can find local-looking pieces, but the best",
                "global disjoint model does not beat an inventory-preserving",
                "lookup and is not exceptional against label shuffles. This",
                "therefore confirms the earlier lookup-disguise conclusion",
                "rather than adding a new generator.",
            ]
        )
    else:
        lines.extend(
            [
                "The block model found a compressive signal. This remains",
                "mechanical-only and would still need independent holdout",
                "evidence before any generator claim could be promoted.",
            ]
        )
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    formula = load_json(FORMULA_JSON)
    pair_table = formula["pair_table"]
    labels = [primary_pair_symbol(pair_table, pair) for pair in PAIR_NAMES]
    blocks = build_blocks()

    independent = independent_cover_summary(labels, blocks)
    global_rows = global_by_budget(labels, blocks)
    for row in global_rows:
        add_acceptable_hits(row, pair_table)
    best_global = min(global_rows, key=lambda row: (row["mdl_bits"], -row["primary_hits"], row["block_count"]))
    control = run_controls(labels, blocks, independent, best_global)
    result_verdict = verdict(best_global, control["summary"])

    result = {
        "schema": "block_biclique_cover_results.v1",
        "translation_delta": "NONE",
        "script": "block_biclique_cover_search.py",
        "random_seed": RANDOM_SEED,
        "control_trials": CONTROL_TRIALS,
        "symbol_inventory": dict(sorted(Counter(labels).items())),
        "cost_model": {
            "symbol_bits": SYMBOL_BITS,
            "cell_bits": CELL_BITS,
            "membership_exception_bits": MEMBERSHIP_EXCEPTION_BITS,
            "label_exception_bits": LABEL_EXCEPTION_BITS,
            "block_size_weight": BLOCK_SIZE_WEIGHT,
            "block_overhead_bits": BLOCK_OVERHEAD_BITS,
            "family_base_bits": FAMILY_BASE_BITS,
            "raw_lookup_bits": len(labels) * SYMBOL_BITS,
            "inventory_lookup_bits": bits_for_inventory(labels),
        },
        "block_library": {
            "candidate_count": len(blocks),
            "family_counts": block_family_counts(blocks),
        },
        "independent_cover": independent,
        "global_by_budget": global_rows,
        "best_global": best_global,
        "control": control,
        "verdict": result_verdict,
        "interpretation": {
            "new_vs_pair_rule_cover": (
                "This is a set/block decomposition test, not a predicate "
                "decision-list. It asks whether whole symbol classes are "
                "compact unions of digit-set bicliques/stars/diagonals."
            ),
            "mechanical_scope": "No plaintext or semantic symbol meanings are inferred.",
        },
    }
    write_json(OUT_JSON, result)
    write_report(result)
    print(f"wrote {OUT_JSON.relative_to(HERE)}")
    print(f"wrote {OUT_MD.relative_to(HERE)}")
    print(
        "blocks={} independent_weighted_f1={:.3f} global_hits={}/55 "
        "acceptable={}/55 mdl={:.1f} inventory_lookup={:.1f} p_hit={:.4f} verdict={}".format(
            len(blocks),
            independent["weighted_f1"],
            best_global["primary_hits"],
            best_global["acceptable_hits"],
            best_global["mdl_bits"],
            best_global["inventory_lookup_bits"],
            control["summary"]["global_primary_hits_p_ge"],
            result_verdict,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
