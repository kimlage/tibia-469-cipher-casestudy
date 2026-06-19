#!/usr/bin/env python3
"""Line/order/template search on the `6 <-> 9` quotient table.

This is a quotient-table follow-up to `digit_orbit_quotient_search.py`.
It does not re-test the original 55-cell triangular table. Instead it collapses
digits 6 and 9 into one class, keeps the two distinct internal quotient cells
`{66,99}` and `{69}`, and tests the resulting 46 orbit labels for:

- row/column/diagonal template alignment;
- fill-order periodic templates and seed cycles;
- quotient-grid index symmetries.

Mechanical only. No plaintext, glossary, or translation is promoted.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

FORMULA_JSON = ROOT / "analysis" / "mechanism_model_20260618" / "mechanical_formula_469.json"
QUOTIENT_JSON = HERE / "digit_orbit_quotient_results.json"

OUT_JSON = HERE / "quotient_line_order_results.json"
OUT_MD = HERE / "quotient_line_order_report.md"

SIGMA = list("*ABCEFILNORSTV")
RANDOM_SEED = 46920260619
CONTROL_TRIALS = 1000
MAX_PERIOD = 23

Q = "Q69"
BASE_CLASS_ORDER = ["0", "1", "2", "3", "4", "5", Q, "7", "8"]
CLASS_DIGITS = {
    "0": (0,),
    "1": (1,),
    "2": (2,),
    "3": (3,),
    "4": (4,),
    "5": (5,),
    Q: (6, 9),
    "7": (7,),
    "8": (8,),
}
CLASS_DISPLAY = {**{str(i): str(i) for i in range(10)}, Q: "6/9"}
BASE_CLASS_RANK = {class_id: idx for idx, class_id in enumerate(BASE_CLASS_ORDER)}

LORE_SEEDS = [
    "469",
    "6-9",
    "4-6-9",
    "bonelord",
    "beholder",
    "magic-web",
    "mota",
    "serpentine-tower",
]


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha_int(text: str) -> int:
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest(), 16)


def class_for_digit(digit: int) -> str:
    return Q if digit in {6, 9} else str(digit)


def pair_key(pair: tuple[int, int]) -> str:
    return f"{pair[0]}{pair[1]}"


def cell_pair_key(left: str, right: str) -> tuple[str, str]:
    return tuple(sorted((left, right), key=lambda item: BASE_CLASS_RANK[item]))


def primary_pair_symbol(pair_table: dict, pair: str) -> str:
    row = pair_table[pair]
    if row["status"] == "pure":
        return row["symbol_if_pure"]
    return sorted(row["symbols"])[0]


def class_order_id(order: list[str]) -> str:
    return "-".join(CLASS_DISPLAY[item].replace("/", "") for item in order)


def class_orders() -> list[dict]:
    orders = [
        {
            "id": "natural_collapsed",
            "family": "fixed",
            "order": BASE_CLASS_ORDER,
            "description": "0,1,2,3,4,5,6/9,7,8",
        },
        {
            "id": "reverse_collapsed",
            "family": "fixed",
            "order": list(reversed(BASE_CLASS_ORDER)),
            "description": "reverse of natural_collapsed",
        },
        {
            "id": "q_last",
            "family": "fixed",
            "order": ["0", "1", "2", "3", "4", "5", "7", "8", Q],
            "description": "natural order with the collapsed 6/9 class last",
        },
        {
            "id": "q_center",
            "family": "fixed",
            "order": ["0", "1", "2", "3", Q, "4", "5", "7", "8"],
            "description": "collapsed 6/9 class placed on the center index",
        },
        {
            "id": "469_anchor",
            "family": "fixed",
            "order": ["4", Q, "0", "1", "2", "3", "5", "7", "8"],
            "description": "4 adjacent to the collapsed 6/9 class, then residual digits",
        },
        {
            "id": "even_odd_collapsed",
            "family": "fixed",
            "order": ["0", "2", "4", Q, "8", "1", "3", "5", "7"],
            "description": "even-like classes first, then odd classes",
        },
    ]
    for seed in LORE_SEEDS:
        order = sorted(BASE_CLASS_ORDER, key=lambda class_id: (sha_int(f"class-order|{seed}|{class_id}"), class_id))
        orders.append(
            {
                "id": f"seed_order_{seed}",
                "family": "lore_seed_hash",
                "seed": seed,
                "order": order,
                "description": "deterministic class order from SHA-256(seed,class)",
            }
        )

    dedup: dict[tuple[str, ...], dict] = {}
    for row in orders:
        dedup.setdefault(tuple(row["order"]), row)
    return list(dedup.values())


def symbol_orders(labels: list[str], cells: list[dict]) -> dict[str, list[str]]:
    counts = Counter(labels)
    first = {}
    for idx, label in enumerate(labels):
        first.setdefault(label, idx)
    diagonal_counts = Counter(cell["label"] for cell in cells if cell["left"] == cell["right"])
    out = {
        "alphabet": SIGMA,
        "alphabet_reverse": list(reversed(SIGMA)),
        "frequency_desc": sorted(SIGMA, key=lambda sym: (-counts[sym], sym)),
        "first_use": sorted(SIGMA, key=lambda sym: (first.get(sym, 999), sym)),
        "diagonal_pressure": sorted(SIGMA, key=lambda sym: (-diagonal_counts[sym], -counts[sym], sym)),
    }
    for seed in LORE_SEEDS:
        out[f"seed_symbols_{seed}"] = sorted(SIGMA, key=lambda sym: (sha_int(f"symbol-order|{seed}|{sym}"), sym))
    return out


def build_quotient_cells(quotient: dict, formula: dict) -> tuple[list[dict], dict[str, dict]]:
    pair_table = formula["pair_table"]
    swap = quotient["swap_6_9"]
    cells = []
    seen_pairs = set()
    for orbit in swap["orbits"]:
        pairs = orbit["pairs"]
        seen_pairs.update(pairs)
        class_pairs = set()
        for pair in pairs:
            a, b = int(pair[0]), int(pair[1])
            class_pairs.add(cell_pair_key(class_for_digit(a), class_for_digit(b)))
        if len(class_pairs) != 1:
            raise ValueError(f"orbit crosses quotient class pairs: {orbit}")
        left, right = next(iter(class_pairs))
        if left == Q and right == Q:
            variant = "qq_mixed" if pairs == ["69"] else "qq_same"
        else:
            variant = "standard"
        actual_pair_labels = {pair: primary_pair_symbol(pair_table, pair) for pair in pairs}
        cell_id = f"O{orbit['orbit']:02d}"
        cells.append(
            {
                "cell_id": cell_id,
                "orbit": orbit["orbit"],
                "pairs": pairs,
                "left": left,
                "right": right,
                "variant": variant,
                "label": orbit["label"],
                "is_mixed": orbit["is_mixed"],
                "label_counts": orbit["label_counts"],
                "actual_pair_labels": actual_pair_labels,
                "stratum": cell_stratum(left, right, variant, pairs, orbit["is_mixed"]),
            }
        )
    expected = {f"{a}{b}" for a in range(10) for b in range(a, 10)}
    if seen_pairs != expected:
        missing = sorted(expected - seen_pairs)
        extra = sorted(seen_pairs - expected)
        raise ValueError(f"quotient pairs do not cover original table: missing={missing} extra={extra}")
    if len(cells) != 46:
        raise ValueError(f"expected 46 quotient cells, got {len(cells)}")
    by_id = {cell["cell_id"]: cell for cell in cells}
    return cells, by_id


def cell_stratum(left: str, right: str, variant: str, pairs: list[str], is_mixed: bool) -> str:
    if variant != "standard":
        return variant
    if len(pairs) == 1:
        return "singleton"
    if is_mixed:
        return "swap_pair_mixed"
    return "swap_pair_clean"


def cell_lookup(cells: list[dict]) -> dict[tuple[str, str, str], dict]:
    lookup = {}
    for cell in cells:
        lookup[(cell["left"], cell["right"], cell["variant"])] = cell
    return lookup


def cells_for_classes(lookup: dict[tuple[str, str, str], dict], left: str, right: str, qq_order: str) -> list[dict]:
    a, b = cell_pair_key(left, right)
    if a == Q and b == Q:
        variants = ["qq_same", "qq_mixed"] if qq_order == "same_then_mixed" else ["qq_mixed", "qq_same"]
        return [lookup[(Q, Q, variant)] for variant in variants]
    return [lookup[(a, b, "standard")]]


def build_lines(cells: list[dict], order: list[str], qq_order: str) -> dict[str, list[dict]]:
    lookup = cell_lookup(cells)
    families: dict[str, list[dict]] = {}
    n = len(order)

    rows = []
    for i, left in enumerate(order):
        line_cells = []
        for j in range(i, n):
            line_cells.extend(cells_for_classes(lookup, left, order[j], qq_order))
        rows.append(line_row("row", CLASS_DISPLAY[left], line_cells))
    families["rows"] = rows

    cols = []
    for j, right in enumerate(order):
        line_cells = []
        for i in range(0, j + 1):
            line_cells.extend(cells_for_classes(lookup, order[i], right, qq_order))
        cols.append(line_row("col", CLASS_DISPLAY[right], line_cells))
    families["cols"] = cols

    diffs = []
    for diff in range(n):
        line_cells = []
        for i in range(0, n - diff):
            line_cells.extend(cells_for_classes(lookup, order[i], order[i + diff], qq_order))
        diffs.append(line_row("diff", str(diff), line_cells))
    families["diagonal_diff"] = diffs

    sums = []
    for total in range(2 * n - 1):
        line_cells = []
        for i in range(n):
            j = total - i
            if i <= j < n:
                line_cells.extend(cells_for_classes(lookup, order[i], order[j], qq_order))
        if line_cells:
            sums.append(line_row("sum", str(total), line_cells))
    families["anti_diagonal_sum"] = sums

    for family, lines in families.items():
        covered = [cell_id for line in lines for cell_id in line["cell_ids"]]
        if len(covered) != 46 or len(set(covered)) != 46:
            raise ValueError(f"{family} does not cover the quotient exactly once")
    return families


def line_row(kind: str, index: str, cells: list[dict]) -> dict:
    return {
        "id": f"{kind}_{index}",
        "length": len(cells),
        "cell_ids": [cell["cell_id"] for cell in cells],
        "orbits": [cell["orbit"] for cell in cells],
        "text": "".join(cell["label"] for cell in cells),
    }


def shift_text(text: str, order: list[str], shift: int) -> str:
    index = {symbol: idx for idx, symbol in enumerate(order)}
    return "".join(order[(index[ch] + shift) % len(order)] for ch in text)


def mismatches(left: str, right: str) -> int:
    return sum(a != b for a, b in zip(left, right))


def best_align_line(line: str, template: str, allow_reverse: bool, order: list[str] | None) -> dict:
    best = None
    variants = [(template, "forward")]
    if allow_reverse:
        variants.append((template[::-1], "reverse"))
    shifts = [0] if order is None else list(range(len(order)))
    for base, orientation in variants:
        for shift in shifts:
            shifted = shift_text(base, order, shift) if order is not None else base
            if len(shifted) < len(line):
                continue
            for start in range(len(shifted) - len(line) + 1):
                substring = shifted[start : start + len(line)]
                row = {
                    "mismatches": mismatches(line, substring),
                    "start": start,
                    "orientation": orientation,
                    "shift": shift,
                    "substring": substring,
                }
                key = (row["mismatches"], row["start"], row["orientation"], row["shift"])
                if best is None or key < (best["mismatches"], best["start"], best["orientation"], best["shift"]):
                    best = row
    if best is None:
        return {"mismatches": len(line), "start": None, "orientation": None, "shift": None, "substring": ""}
    return best


def evaluate_template_family(
    class_order: dict,
    qq_order: str,
    family_name: str,
    lines: list[dict],
    mode: str,
    symbol_order_name: str | None,
    symbol_order: list[str] | None,
    candidate_count: int,
) -> dict:
    allow_reverse = mode in {"substring_reverse", "substring_reverse_shift"}
    allow_shift = mode in {"substring_shift", "substring_reverse_shift"}
    effective_order = symbol_order if allow_shift else None
    rows = []
    for template_line in lines:
        total = 0
        detail = []
        for line in lines:
            aligned = best_align_line(line["text"], template_line["text"], allow_reverse, effective_order)
            total += aligned["mismatches"]
            detail.append({"line_id": line["id"], "line_text": line["text"], **aligned})
        rows.append({"template_line_id": template_line["id"], "template": template_line["text"], "total_mismatches": total, "detail": detail})
    best = min(rows, key=lambda row: (row["total_mismatches"], len(row["template"]), row["template_line_id"]))
    total_chars = sum(len(line["text"]) for line in lines)
    lookup_bits = total_chars * math.log2(len(SIGMA))
    template_bits = len(best["template"]) * math.log2(len(SIGMA))
    address_bits = len(lines) * (math.log2(max(1, len(best["template"]))) + 2.0)
    if allow_reverse:
        address_bits += len(lines)
    if allow_shift:
        address_bits += len(lines) * math.log2(len(SIGMA))
    exception_bits = best["total_mismatches"] * (math.log2(total_chars) + math.log2(len(SIGMA)))
    multiple_test_bits = math.log2(candidate_count)
    mdl_bits = template_bits + address_bits + exception_bits + multiple_test_bits
    return {
        "class_order_id": class_order["id"],
        "class_order_family": class_order["family"],
        "class_order": [CLASS_DISPLAY[item] for item in class_order["order"]],
        "qq_order": qq_order,
        "family": family_name,
        "mode": mode,
        "symbol_order": symbol_order_name,
        "line_count": len(lines),
        "total_chars": total_chars,
        "template_line_id": best["template_line_id"],
        "template": best["template"],
        "total_mismatches": best["total_mismatches"],
        "match_fraction": 1.0 - best["total_mismatches"] / total_chars,
        "lookup_cost_bits": lookup_bits,
        "mdl_cost_bits": mdl_bits,
        "mdl_gain_vs_lookup_bits": lookup_bits - mdl_bits,
        "lookup_cost_ratio": mdl_bits / lookup_bits,
        "detail": best["detail"],
    }


def search_line_templates(cells: list[dict], orders: list[dict], orders_by_name: dict[str, list[str]]) -> list[dict]:
    candidate_count = len(orders) * 2 * 4 * (2 + 2 * len(orders_by_name))
    rows = []
    for class_order in orders:
        for qq_order in ["same_then_mixed", "mixed_then_same"]:
            families = build_lines(cells, class_order["order"], qq_order)
            for family_name, lines in families.items():
                for mode in ["substring", "substring_reverse"]:
                    rows.append(evaluate_template_family(class_order, qq_order, family_name, lines, mode, None, None, candidate_count))
                for symbol_order_name, symbol_order in orders_by_name.items():
                    for mode in ["substring_shift", "substring_reverse_shift"]:
                        rows.append(
                            evaluate_template_family(
                                class_order,
                                qq_order,
                                family_name,
                                lines,
                                mode,
                                symbol_order_name,
                                symbol_order,
                                candidate_count,
                            )
                        )
    rows.sort(key=lambda row: (-row["mdl_gain_vs_lookup_bits"], -row["match_fraction"], row["class_order_id"], row["family"], row["mode"]))
    return rows


def flatten_lines(lines: list[dict], reverse_alternate: bool = False) -> list[str]:
    cell_ids = []
    for idx, line in enumerate(lines):
        ids = line["cell_ids"]
        if reverse_alternate and idx % 2:
            ids = list(reversed(ids))
        cell_ids.extend(ids)
    if len(cell_ids) != 46 or len(set(cell_ids)) != 46:
        raise ValueError("fill order is not a 46-cell permutation")
    return cell_ids


def build_fill_orders(cells: list[dict], orders: list[dict]) -> list[dict]:
    rows = []
    natural_cells = sorted(cells, key=lambda cell: cell["orbit"])
    rows.append({"id": "orbit_index", "family": "quotient_orbit", "class_order_id": None, "qq_order": None, "cell_ids": [cell["cell_id"] for cell in natural_cells]})
    for seed in LORE_SEEDS:
        seed_cells = sorted(cells, key=lambda cell: (sha_int(f"cell-order|{seed}|{cell['cell_id']}|{','.join(cell['pairs'])}"), cell["cell_id"]))
        rows.append(
            {
                "id": f"seed_cell_order_{seed}",
                "family": "lore_seed_hash",
                "seed": seed,
                "class_order_id": None,
                "qq_order": None,
                "cell_ids": [cell["cell_id"] for cell in seed_cells],
            }
        )
    for class_order in orders:
        for qq_order in ["same_then_mixed", "mixed_then_same"]:
            families = build_lines(cells, class_order["order"], qq_order)
            for family_name, lines in families.items():
                rows.append(
                    {
                        "id": f"{class_order['id']}|{qq_order}|{family_name}|major",
                        "family": family_name,
                        "class_order_id": class_order["id"],
                        "class_order": [CLASS_DISPLAY[item] for item in class_order["order"]],
                        "qq_order": qq_order,
                        "cell_ids": flatten_lines(lines),
                    }
                )
                rows.append(
                    {
                        "id": f"{class_order['id']}|{qq_order}|{family_name}|snake",
                        "family": f"{family_name}_snake",
                        "class_order_id": class_order["id"],
                        "class_order": [CLASS_DISPLAY[item] for item in class_order["order"]],
                        "qq_order": qq_order,
                        "cell_ids": flatten_lines(lines, reverse_alternate=True),
                    }
                )
    dedup = {}
    for row in rows:
        dedup.setdefault(tuple(row["cell_ids"]), row)
    return list(dedup.values())


def best_periodic_template(order_row: dict, by_id: dict[str, dict], candidate_count: int) -> dict:
    labels = [by_id[cell_id]["label"] for cell_id in order_row["cell_ids"]]
    n = len(labels)
    lookup_bits = n * math.log2(len(SIGMA))
    best = None
    for period in range(1, min(MAX_PERIOD, n - 1) + 1):
        template = []
        mismatched_positions = []
        for slot in range(period):
            slot_labels = [labels[idx] for idx in range(slot, n, period)]
            winner = sorted(Counter(slot_labels).items(), key=lambda item: (-item[1], SIGMA.index(item[0])))[0][0]
            template.append(winner)
        for idx, label in enumerate(labels):
            predicted = template[idx % period]
            if predicted != label:
                mismatched_positions.append({"index": idx, "cell_id": order_row["cell_ids"][idx], "predicted": predicted, "actual": label})
        exception_bits = len(mismatched_positions) * (math.log2(n) + math.log2(len(SIGMA)))
        period_bits = math.log2(MAX_PERIOD) + period * math.log2(len(SIGMA))
        mdl_bits = period_bits + exception_bits + math.log2(candidate_count)
        row = {
            **{key: value for key, value in order_row.items() if key != "cell_ids"},
            "sequence": "".join(labels),
            "period": period,
            "template": "".join(template),
            "mismatch_count": len(mismatched_positions),
            "match_fraction": 1.0 - len(mismatched_positions) / n,
            "lookup_cost_bits": lookup_bits,
            "mdl_cost_bits": mdl_bits,
            "mdl_gain_vs_lookup_bits": lookup_bits - mdl_bits,
            "lookup_cost_ratio": mdl_bits / lookup_bits,
            "mismatches": mismatched_positions[:30],
        }
        if best is None or (row["mdl_gain_vs_lookup_bits"], row["match_fraction"], -row["period"]) > (
            best["mdl_gain_vs_lookup_bits"],
            best["match_fraction"],
            -best["period"],
        ):
            best = row
    return best


_SEED_SYMBOL_ORDER_CACHE: dict[str, list[str]] | None = None


def seed_symbol_orders() -> dict[str, list[str]]:
    global _SEED_SYMBOL_ORDER_CACHE
    if _SEED_SYMBOL_ORDER_CACHE is not None:
        return _SEED_SYMBOL_ORDER_CACHE
    out = {"alphabet": SIGMA, "alphabet_reverse": list(reversed(SIGMA))}
    for seed in LORE_SEEDS:
        out[f"seed_symbols_{seed}"] = sorted(SIGMA, key=lambda sym: (sha_int(f"symbol-cycle|{seed}|{sym}"), sym))
    _SEED_SYMBOL_ORDER_CACHE = out
    return out


def best_seed_cycle(order_row: dict, by_id: dict[str, dict], candidate_count: int) -> dict:
    labels = [by_id[cell_id]["label"] for cell_id in order_row["cell_ids"]]
    n = len(labels)
    lookup_bits = n * math.log2(len(SIGMA))
    best = None
    cycle_orders = seed_symbol_orders()
    cycle_order_bits = math.log2(len(cycle_orders))
    for symbol_order_id, order in cycle_orders.items():
        for step in range(1, len(order)):
            for offset in range(len(order)):
                mismatched_positions = []
                for idx, label in enumerate(labels):
                    predicted = order[(offset + idx * step) % len(order)]
                    if predicted != label:
                        mismatched_positions.append({"index": idx, "cell_id": order_row["cell_ids"][idx], "predicted": predicted, "actual": label})
                exception_bits = len(mismatched_positions) * (math.log2(n) + math.log2(len(SIGMA)))
                cycle_bits = cycle_order_bits + 2 * math.log2(len(order))
                mdl_bits = cycle_bits + exception_bits + math.log2(candidate_count)
                row = {
                    **{key: value for key, value in order_row.items() if key != "cell_ids"},
                    "sequence": "".join(labels),
                    "symbol_order_id": symbol_order_id,
                    "symbol_order": "".join(order),
                    "step": step,
                    "offset": offset,
                    "mismatch_count": len(mismatched_positions),
                    "match_fraction": 1.0 - len(mismatched_positions) / n,
                    "lookup_cost_bits": lookup_bits,
                    "mdl_cost_bits": mdl_bits,
                    "mdl_gain_vs_lookup_bits": lookup_bits - mdl_bits,
                    "lookup_cost_ratio": mdl_bits / lookup_bits,
                    "mismatches": mismatched_positions[:30],
                }
                if best is None or (row["mdl_gain_vs_lookup_bits"], row["match_fraction"]) > (
                    best["mdl_gain_vs_lookup_bits"],
                    best["match_fraction"],
                ):
                    best = row
    return best


def search_fill_orders(cells: list[dict], by_id: dict[str, dict], orders: list[dict]) -> tuple[list[dict], list[dict]]:
    fill_orders = build_fill_orders(cells, orders)
    period_rows = [best_periodic_template(row, by_id, len(fill_orders)) for row in fill_orders]
    cycle_candidate_orders = seed_cycle_fill_orders(fill_orders)
    cycle_rows = [best_seed_cycle(row, by_id, len(cycle_candidate_orders)) for row in cycle_candidate_orders]
    period_rows.sort(key=lambda row: (-row["mdl_gain_vs_lookup_bits"], -row["match_fraction"], row["id"]))
    cycle_rows.sort(key=lambda row: (-row["mdl_gain_vs_lookup_bits"], -row["match_fraction"], row["id"]))
    return period_rows, cycle_rows


def seed_cycle_fill_orders(fill_orders: list[dict]) -> list[dict]:
    return [
        row
        for row in fill_orders
        if row["family"] in {"quotient_orbit", "lore_seed_hash"}
        or (
            row.get("class_order_id") in {"natural_collapsed", "q_center", "469_anchor"}
            and not row["family"].endswith("_snake")
        )
    ]


def anti_reverse_mapping(cells: list[dict], class_order: dict, qq_order: str) -> dict[str, str]:
    lookup = cell_lookup(cells)
    order = class_order["order"]
    pos = {class_id: idx for idx, class_id in enumerate(order)}
    n = len(order)
    mapping = {}
    for cell in cells:
        i, j = sorted((pos[cell["left"]], pos[cell["right"]]))
        ti, tj = n - 1 - j, n - 1 - i
        target_classes = (order[ti], order[tj])
        target_cells = cells_for_classes(lookup, target_classes[0], target_classes[1], qq_order)
        if len(target_cells) == 1 and cell["variant"] == "standard":
            mapping[cell["cell_id"]] = target_cells[0]["cell_id"]
        elif len(target_cells) == 2 and cell["left"] == Q and cell["right"] == Q:
            variant_to_target = {target["variant"]: target for target in target_cells}
            mapping[cell["cell_id"]] = variant_to_target[cell["variant"]]["cell_id"]
    return mapping


def evaluate_symmetry(cells: list[dict], by_id: dict[str, dict], class_order: dict, qq_order: str, candidate_count: int) -> dict:
    mapping = anti_reverse_mapping(cells, class_order, qq_order)
    pairs = []
    for source, target in sorted(mapping.items()):
        if source <= target:
            pairs.append((source, target))
    identity_hits = sum(by_id[source]["label"] == by_id[target]["label"] for source, target in pairs)
    transition_counts = defaultdict(Counter)
    for source, target in pairs:
        transition_counts[by_id[source]["label"]][by_id[target]["label"]] += 1
    relabel_hits = sum(counter.most_common(1)[0][1] for counter in transition_counts.values())
    covered = len(pairs)
    lookup_bits = covered * math.log2(len(SIGMA)) if covered else 0.0
    exception_bits = (covered - identity_hits) * (math.log2(max(1, covered)) + math.log2(len(SIGMA)))
    identity_mdl_bits = math.log2(candidate_count) + exception_bits
    relabel_bits = len(transition_counts) * math.log2(len(SIGMA))
    relabel_exception_bits = (covered - relabel_hits) * (math.log2(max(1, covered)) + math.log2(len(SIGMA)))
    relabel_mdl_bits = math.log2(candidate_count) + relabel_bits + relabel_exception_bits
    return {
        "symmetry": "anti_reverse_index",
        "class_order_id": class_order["id"],
        "class_order_family": class_order["family"],
        "class_order": [CLASS_DISPLAY[item] for item in class_order["order"]],
        "qq_order": qq_order,
        "covered_pairs": covered,
        "mapped_cells": len(mapping),
        "identity_hits": identity_hits,
        "identity_accuracy": identity_hits / covered if covered else 0.0,
        "best_relabel_hits": relabel_hits,
        "best_relabel_accuracy": relabel_hits / covered if covered else 0.0,
        "lookup_cost_bits": lookup_bits,
        "identity_mdl_gain_vs_lookup_bits": lookup_bits - identity_mdl_bits,
        "best_relabel_mdl_gain_vs_lookup_bits": lookup_bits - relabel_mdl_bits,
        "label_mapping": {label: counter.most_common(1)[0][0] for label, counter in sorted(transition_counts.items())},
        "sample_pairs": [{"source": source, "target": target, "source_label": by_id[source]["label"], "target_label": by_id[target]["label"]} for source, target in pairs[:30]],
    }


def search_symmetries(cells: list[dict], by_id: dict[str, dict], orders: list[dict]) -> list[dict]:
    candidate_count = len(orders) * 2
    rows = []
    for class_order in orders:
        for qq_order in ["same_then_mixed", "mixed_then_same"]:
            rows.append(evaluate_symmetry(cells, by_id, class_order, qq_order, candidate_count))
    rows.sort(key=lambda row: (-row["best_relabel_mdl_gain_vs_lookup_bits"], -row["best_relabel_accuracy"], row["class_order_id"]))
    return rows


def clone_with_labels(cells: list[dict], labels_by_cell: dict[str, str]) -> tuple[list[dict], dict[str, dict]]:
    new_cells = []
    for cell in cells:
        row = dict(cell)
        row["label"] = labels_by_cell[cell["cell_id"]]
        row["label_counts"] = {row["label"]: len(row["pairs"])}
        row["is_mixed"] = False
        new_cells.append(row)
    return new_cells, {cell["cell_id"]: cell for cell in new_cells}


def run_search(cells: list[dict], by_id: dict[str, dict], orders: list[dict]) -> dict:
    labels = [cell["label"] for cell in sorted(cells, key=lambda item: item["orbit"])]
    line_rows = search_line_templates(cells, orders, symbol_orders(labels, cells))
    period_rows, cycle_rows = search_fill_orders(cells, by_id, orders)
    symmetry_rows = search_symmetries(cells, by_id, orders)
    return {
        "line_template": line_rows,
        "fill_period": period_rows,
        "seed_cycle": cycle_rows,
        "symmetry": symmetry_rows,
    }


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


def shuffled_labels_global(cells: list[dict], rng: random.Random) -> dict[str, str]:
    cell_ids = [cell["cell_id"] for cell in sorted(cells, key=lambda item: item["orbit"])]
    labels = [cell["label"] for cell in sorted(cells, key=lambda item: item["orbit"])]
    rng.shuffle(labels)
    return dict(zip(cell_ids, labels))


def shuffled_labels_by_stratum(cells: list[dict], rng: random.Random) -> dict[str, str]:
    labels_by_cell = {}
    strata = defaultdict(list)
    for cell in cells:
        strata[cell["stratum"]].append(cell)
    for stratum_cells in strata.values():
        labels = [cell["label"] for cell in stratum_cells]
        rng.shuffle(labels)
        for cell, label in zip(stratum_cells, labels):
            labels_by_cell[cell["cell_id"]] = label
    return labels_by_cell


def find_class_order(orders: list[dict], class_order_id: str) -> dict:
    for order in orders:
        if order["id"] == class_order_id:
            return order
    raise KeyError(class_order_id)


def fixed_line_template_eval(cells: list[dict], orders: list[dict], observed_best: dict) -> dict:
    labels = [cell["label"] for cell in sorted(cells, key=lambda item: item["orbit"])]
    orders_by_name = symbol_orders(labels, cells)
    class_order = find_class_order(orders, observed_best["class_order_id"])
    families = build_lines(cells, class_order["order"], observed_best["qq_order"])
    candidate_count = len(orders) * 2 * 4 * (2 + 2 * len(orders_by_name))
    symbol_order_name = observed_best["symbol_order"]
    symbol_order = orders_by_name.get(symbol_order_name) if symbol_order_name is not None else None
    return evaluate_template_family(
        class_order,
        observed_best["qq_order"],
        observed_best["family"],
        families[observed_best["family"]],
        observed_best["mode"],
        symbol_order_name,
        symbol_order,
        candidate_count,
    )


def fixed_period_eval(cells: list[dict], by_id: dict[str, dict], orders: list[dict], observed_best: dict) -> dict:
    fill_orders = build_fill_orders(cells, orders)
    order_row = next(row for row in fill_orders if row["id"] == observed_best["id"])
    return best_periodic_template(order_row, by_id, len(fill_orders))


def fixed_seed_cycle_eval(cells: list[dict], by_id: dict[str, dict], orders: list[dict], observed_best: dict) -> dict:
    fill_orders = build_fill_orders(cells, orders)
    cycle_orders = seed_cycle_fill_orders(fill_orders)
    order_row = next(row for row in cycle_orders if row["id"] == observed_best["id"])
    return best_seed_cycle(order_row, by_id, len(cycle_orders))


def fixed_symmetry_eval(cells: list[dict], by_id: dict[str, dict], orders: list[dict], observed_best: dict) -> dict:
    class_order = find_class_order(orders, observed_best["class_order_id"])
    return evaluate_symmetry(cells, by_id, class_order, observed_best["qq_order"], len(orders) * 2)


def control(cells: list[dict], orders: list[dict], observed: dict) -> dict:
    rng = random.Random(RANDOM_SEED + 1)
    observed_best = {
        "line": observed["line_template"][0],
        "period": observed["fill_period"][0],
        "cycle": observed["seed_cycle"][0],
        "symmetry": observed["symmetry"][0],
    }
    observed_metrics = {
        "line_best_mdl_gain_bits": observed_best["line"]["mdl_gain_vs_lookup_bits"],
        "line_best_match_fraction": observed_best["line"]["match_fraction"],
        "period_best_mdl_gain_bits": observed_best["period"]["mdl_gain_vs_lookup_bits"],
        "period_best_match_fraction": observed_best["period"]["match_fraction"],
        "seed_cycle_best_mdl_gain_bits": observed_best["cycle"]["mdl_gain_vs_lookup_bits"],
        "seed_cycle_best_match_fraction": observed_best["cycle"]["match_fraction"],
        "symmetry_best_relabel_gain_bits": observed_best["symmetry"]["best_relabel_mdl_gain_vs_lookup_bits"],
        "symmetry_best_relabel_accuracy": observed_best["symmetry"]["best_relabel_accuracy"],
    }
    buckets = {
        "global_label_shuffle": defaultdict(list),
        "stratified_inventory_shuffle": defaultdict(list),
    }
    for _ in range(CONTROL_TRIALS):
        for control_name, shuffle_fn in [
            ("global_label_shuffle", shuffled_labels_global),
            ("stratified_inventory_shuffle", shuffled_labels_by_stratum),
        ]:
            labels_by_cell = shuffle_fn(cells, rng)
            ctrl_cells, ctrl_by_id = clone_with_labels(cells, labels_by_cell)
            line_row = fixed_line_template_eval(ctrl_cells, orders, observed_best["line"])
            period_row = fixed_period_eval(ctrl_cells, ctrl_by_id, orders, observed_best["period"])
            cycle_row = fixed_seed_cycle_eval(ctrl_cells, ctrl_by_id, orders, observed_best["cycle"])
            symmetry_row = fixed_symmetry_eval(ctrl_cells, ctrl_by_id, orders, observed_best["symmetry"])
            buckets[control_name]["line_best_mdl_gain_bits"].append(line_row["mdl_gain_vs_lookup_bits"])
            buckets[control_name]["line_best_match_fraction"].append(line_row["match_fraction"])
            buckets[control_name]["period_best_mdl_gain_bits"].append(period_row["mdl_gain_vs_lookup_bits"])
            buckets[control_name]["period_best_match_fraction"].append(period_row["match_fraction"])
            buckets[control_name]["seed_cycle_best_mdl_gain_bits"].append(cycle_row["mdl_gain_vs_lookup_bits"])
            buckets[control_name]["seed_cycle_best_match_fraction"].append(cycle_row["match_fraction"])
            buckets[control_name]["symmetry_best_relabel_gain_bits"].append(symmetry_row["best_relabel_mdl_gain_vs_lookup_bits"])
            buckets[control_name]["symmetry_best_relabel_accuracy"].append(symmetry_row["best_relabel_accuracy"])
    return {
        "trials": CONTROL_TRIALS,
        "scope": "fixed_observed_winner_configs",
        "observed_metrics": observed_metrics,
        "global_label_shuffle": {
            metric: summarize(values, observed_metrics[metric])
            for metric, values in buckets["global_label_shuffle"].items()
        },
        "stratified_inventory_shuffle": {
            metric: summarize(values, observed_metrics[metric])
            for metric, values in buckets["stratified_inventory_shuffle"].items()
        },
    }


def verdict(result: dict) -> str:
    ctrl = result["control"]
    line = result["searches"]["line_template"]["best"]
    period = result["searches"]["fill_period"]["best"]
    cycle = result["searches"]["seed_cycle"]["best"]
    symmetry = result["searches"]["symmetry"]["best"]

    line_p = ctrl["global_label_shuffle"]["line_best_mdl_gain_bits"]["p_ge_observed"]
    period_p = ctrl["global_label_shuffle"]["period_best_mdl_gain_bits"]["p_ge_observed"]
    cycle_p = ctrl["global_label_shuffle"]["seed_cycle_best_mdl_gain_bits"]["p_ge_observed"]
    symmetry_p = ctrl["global_label_shuffle"]["symmetry_best_relabel_gain_bits"]["p_ge_observed"]
    line_p_strat = ctrl["stratified_inventory_shuffle"]["line_best_mdl_gain_bits"]["p_ge_observed"]
    period_p_strat = ctrl["stratified_inventory_shuffle"]["period_best_mdl_gain_bits"]["p_ge_observed"]
    cycle_p_strat = ctrl["stratified_inventory_shuffle"]["seed_cycle_best_mdl_gain_bits"]["p_ge_observed"]
    symmetry_p_strat = ctrl["stratified_inventory_shuffle"]["symmetry_best_relabel_gain_bits"]["p_ge_observed"]

    if line["mdl_gain_vs_lookup_bits"] > 0 and line["lookup_cost_ratio"] < 1.0 and line_p <= 0.01 and line_p_strat <= 0.01:
        return "candidate_quotient_line_template_generator"
    if period["mdl_gain_vs_lookup_bits"] > 0 and period["lookup_cost_ratio"] < 1.0 and period_p <= 0.01 and period_p_strat <= 0.01:
        return "candidate_quotient_fill_order_generator"
    if cycle["mdl_gain_vs_lookup_bits"] > 0 and cycle["lookup_cost_ratio"] < 1.0 and cycle_p <= 0.01 and cycle_p_strat <= 0.01:
        return "candidate_quotient_seed_cycle_generator"
    if symmetry["best_relabel_mdl_gain_vs_lookup_bits"] > 0 and symmetry_p <= 0.01 and symmetry_p_strat <= 0.01:
        return "candidate_quotient_symmetry_generator"
    if min(line_p, period_p, cycle_p, symmetry_p) <= 0.05:
        return "weak_quotient_structure_signal_not_formula"
    return "rejected_control"


def compact_top(rows: list[dict], count: int = 25) -> list[dict]:
    return rows[:count]


def write_report(result: dict) -> None:
    line = result["searches"]["line_template"]["best"]
    period = result["searches"]["fill_period"]["best"]
    cycle = result["searches"]["seed_cycle"]["best"]
    symmetry = result["searches"]["symmetry"]["best"]
    ctrl = result["control"]
    q = result["quotient"]
    lines = [
        "# Quotient Line/Order Search",
        "",
        "Generated by `quotient_line_order_search.py`.",
        "",
        "Scope: mechanical generator search only. This pass uses the `6<->9`",
        "quotient table with 46 orbit labels, not the original 55-cell pair",
        "table. The collapsed class is written as `6/9`; the internal quotient",
        "keeps `{66,99}` and `{69}` as separate cells. `translation_delta=NONE`.",
        "",
        "## Quotient Input",
        "",
        f"- Orbit count: `{q['orbit_count']}`.",
        f"- Label inventory: `{q['label_inventory']}`.",
        f"- Mixed swap orbits inherited from quotient search: `{q['mixed_orbit_count']}`.",
        f"- Source files: `{QUOTIENT_JSON.relative_to(ROOT)}` and `{FORMULA_JSON.relative_to(ROOT)}`.",
        "",
        "## Summary",
        "",
        "| Front | Best candidate | Score | Control p(global fixed) | Control p(stratified fixed) |",
        "|---|---|---:|---:|---:|",
        f"| Line template | `{line['class_order_id']} / {line['qq_order']} / {line['family']} / {line['mode']}` | gain {line['mdl_gain_vs_lookup_bits']:.1f} bits, match {line['match_fraction']:.3f} | {ctrl['global_label_shuffle']['line_best_mdl_gain_bits']['p_ge_observed']:.4f} | {ctrl['stratified_inventory_shuffle']['line_best_mdl_gain_bits']['p_ge_observed']:.4f} |",
        f"| Fill-order period | `{period['id']}` | gain {period['mdl_gain_vs_lookup_bits']:.1f} bits, period {period['period']}, match {period['match_fraction']:.3f} | {ctrl['global_label_shuffle']['period_best_mdl_gain_bits']['p_ge_observed']:.4f} | {ctrl['stratified_inventory_shuffle']['period_best_mdl_gain_bits']['p_ge_observed']:.4f} |",
        f"| Seed cycle | `{cycle['id']} / {cycle['symbol_order_id']}` | gain {cycle['mdl_gain_vs_lookup_bits']:.1f} bits, match {cycle['match_fraction']:.3f} | {ctrl['global_label_shuffle']['seed_cycle_best_mdl_gain_bits']['p_ge_observed']:.4f} | {ctrl['stratified_inventory_shuffle']['seed_cycle_best_mdl_gain_bits']['p_ge_observed']:.4f} |",
        f"| Symmetry | `{symmetry['class_order_id']} / {symmetry['qq_order']}` | relabel gain {symmetry['best_relabel_mdl_gain_vs_lookup_bits']:.1f} bits, relabel acc {symmetry['best_relabel_accuracy']:.3f} | {ctrl['global_label_shuffle']['symmetry_best_relabel_gain_bits']['p_ge_observed']:.4f} | {ctrl['stratified_inventory_shuffle']['symmetry_best_relabel_gain_bits']['p_ge_observed']:.4f} |",
        "",
        f"Verdict: `{result['verdict']}`.",
        "",
        "## Best Line Template",
        "",
        f"- Class order: `{line['class_order']}`.",
        f"- Template line: `{line['template_line_id']}` = `{line['template']}`.",
        f"- Mode/order: `{line['mode']}` / `{line['symbol_order']}`.",
        f"- Mismatches: `{line['total_mismatches']}` of `{line['total_chars']}` quotient cells.",
        f"- MDL/lookup: `{line['lookup_cost_ratio']:.3f}`.",
        "",
        "## Best Fill Period",
        "",
        f"- Order: `{period['id']}`.",
        f"- Sequence: `{period['sequence']}`.",
        f"- Period/template: `{period['period']}` / `{period['template']}`.",
        f"- Mismatches: `{period['mismatch_count']}` of 46 quotient cells.",
        f"- MDL/lookup: `{period['lookup_cost_ratio']:.3f}`.",
        "",
        "## Best Seed Cycle",
        "",
        f"- Fill order: `{cycle['id']}`.",
        f"- Symbol cycle: `{cycle['symbol_order_id']}` = `{cycle['symbol_order']}`.",
        f"- Step/offset: `{cycle['step']}` / `{cycle['offset']}`.",
        f"- Mismatches: `{cycle['mismatch_count']}` of 46 quotient cells.",
        f"- MDL/lookup: `{cycle['lookup_cost_ratio']:.3f}`.",
        "",
        "## Best Symmetry",
        "",
        f"- Symmetry: `{symmetry['symmetry']}`.",
        f"- Class order: `{symmetry['class_order']}`.",
        f"- Covered unordered pairs: `{symmetry['covered_pairs']}`; mapped cells: `{symmetry['mapped_cells']}`.",
        f"- Identity accuracy: `{symmetry['identity_accuracy']:.3f}`; best relabel accuracy: `{symmetry['best_relabel_accuracy']:.3f}`.",
        f"- Best relabel map: `{symmetry['label_mapping']}`.",
        "",
        "## Top Line-Template Rows",
        "",
        "| Class order | QQ order | Family | Mode | Symbol order | Template | Match | MDL/lookup | Gain bits |",
        "|---|---|---|---|---|---|---:|---:|---:|",
    ]
    for row in result["searches"]["line_template"]["top_rows"][:20]:
        lines.append(
            f"| `{row['class_order_id']}` | `{row['qq_order']}` | `{row['family']}` | `{row['mode']}` | `{row['symbol_order']}` | `{row['template']}` | {row['match_fraction']:.3f} | {row['lookup_cost_ratio']:.3f} | {row['mdl_gain_vs_lookup_bits']:.1f} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The quotient table can be scanned in many mechanically plausible ways,",
            "including row/column/diagonal traversals, a few deterministic 469/lore",
            "seed orders, and anti-diagonal index reversal. The selected best rows",
            "are then re-scored under inventory-preserving label shuffles. These",
            "fixed-winner controls are a guard against mistaking quotient geometry",
            "for a generator. Under that control, this pass does not promote",
            "plaintext, a glossary, or a recovered original formula.",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    formula = load_json(FORMULA_JSON)
    quotient = load_json(QUOTIENT_JSON)
    cells, by_id = build_quotient_cells(quotient, formula)
    orders = class_orders()
    observed = run_search(cells, by_id, orders)
    result = {
        "schema": "quotient_line_order_results.v1",
        "translation_delta": "NONE",
        "inputs": {
            "quotient": str(QUOTIENT_JSON.relative_to(ROOT)),
            "mechanical_formula": str(FORMULA_JSON.relative_to(ROOT)),
        },
        "search_parameters": {
            "random_seed": RANDOM_SEED,
            "control_trials": CONTROL_TRIALS,
            "max_period": MAX_PERIOD,
            "class_order_count": len(orders),
            "lore_seed_count": len(LORE_SEEDS),
        },
        "quotient": {
            "orbit_count": len(cells),
            "class_count": len(BASE_CLASS_ORDER),
            "collapsed_class": "6/9",
            "qq_internal_cells": ["{66,99}", "{69}"],
            "label_inventory": dict(sorted(Counter(cell["label"] for cell in cells).items())),
            "stratum_inventory": dict(sorted(Counter(cell["stratum"] for cell in cells).items())),
            "mixed_orbit_count": sum(1 for cell in cells if cell["is_mixed"]),
            "cells": cells,
        },
        "searches": {
            "line_template": {"best": observed["line_template"][0], "top_rows": compact_top(observed["line_template"], 80)},
            "fill_period": {"best": observed["fill_period"][0], "top_rows": compact_top(observed["fill_period"], 80)},
            "seed_cycle": {"best": observed["seed_cycle"][0], "top_rows": compact_top(observed["seed_cycle"], 80)},
            "symmetry": {"best": observed["symmetry"][0], "top_rows": compact_top(observed["symmetry"], 80)},
        },
    }
    result["control"] = control(cells, orders, observed)
    result["verdict"] = verdict(result)
    write_json(OUT_JSON, result)
    write_report(result)
    print(f"wrote {OUT_JSON.relative_to(HERE)}")
    print(f"wrote {OUT_MD.relative_to(HERE)}")
    print(
        "verdict={verdict} line_gain={line:.1f} period_gain={period:.1f} cycle_gain={cycle:.1f} symmetry_gain={sym:.1f}".format(
            verdict=result["verdict"],
            line=result["searches"]["line_template"]["best"]["mdl_gain_vs_lookup_bits"],
            period=result["searches"]["fill_period"]["best"]["mdl_gain_vs_lookup_bits"],
            cycle=result["searches"]["seed_cycle"]["best"]["mdl_gain_vs_lookup_bits"],
            sym=result["searches"]["symmetry"]["best"]["best_relabel_mdl_gain_vs_lookup_bits"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
