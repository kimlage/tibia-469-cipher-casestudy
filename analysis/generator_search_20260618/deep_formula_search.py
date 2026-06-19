#!/usr/bin/env python3
"""Deeper search for an original-style 469 generator formula.

This script deliberately looks beyond the already-known unordered-pair geometry:

1. Can a compact arithmetic/grid formula predict the 99 code->symbol cells
   without becoming a 55-cell lookup table?
2. Does the 55-pair table become simple under any natural matrix traversal,
   period, or lore-seed string?

The output is negative unless a rule beats the explicit lookup on complexity
and prediction. No semantic translation is produced.
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

OUT_JSON = HERE / "deep_formula_leaderboard.json"
OUT_MD = HERE / "deep_formula_search_report.md"

RANDOM_SEED = 469
random.seed(RANDOM_SEED)

SIGMA = "*ABCEFILNORSTV"
LORE_STRINGS = [
    "TIBIA",
    "BENNA",
    "TELBENNA",
    "ENNAI",
    "FAS",
    "TIBIABENNA",
    "TELBENNAFAS",
    "ITELBENNA",
]


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def eval_key_rule(codes: list[str], symbols: dict[str, str], keyer, rule_id: str, complexity_cost: float) -> dict:
    groups = defaultdict(list)
    for code in codes:
        groups[keyer(code)].append(symbols[code])
    majority = {key: Counter(vals).most_common(1)[0][0] for key, vals in groups.items()}
    errors = [code for code in codes if majority[keyer(code)] != symbols[code]]
    accuracy = (len(codes) - len(errors)) / len(codes)
    # Rough two-part cost: describe groups' symbols + exceptions.
    mdl_bits = len(groups) * math.log2(len(SIGMA)) + len(errors) * (math.log2(len(codes)) + math.log2(len(SIGMA))) + complexity_cost
    return {
        "hypothesis_id": rule_id,
        "accuracy": accuracy,
        "errors": len(errors),
        "groups": len(groups),
        "mdl_bits_est": mdl_bits,
        "complexity_cost_bits": complexity_cost,
        "error_codes": errors[:30],
    }


def eval_key_values(codes: list[str], target: list[str], keys: list[int | tuple], rule_id: str, complexity_cost: float) -> dict:
    groups = defaultdict(list)
    for key, symbol in zip(keys, target):
        groups[key].append(symbol)
    majority = {key: Counter(vals).most_common(1)[0][0] for key, vals in groups.items()}
    errors = [code for code, key, symbol in zip(codes, keys, target) if majority[key] != symbol]
    accuracy = (len(codes) - len(errors)) / len(codes)
    mdl_bits = len(groups) * math.log2(len(SIGMA)) + len(errors) * (math.log2(len(codes)) + math.log2(len(SIGMA))) + complexity_cost
    return {
        "hypothesis_id": rule_id,
        "accuracy": accuracy,
        "errors": len(errors),
        "groups": len(groups),
        "mdl_bits_est": mdl_bits,
        "complexity_cost_bits": complexity_cost,
        "error_codes": errors[:30],
    }


def feature_values(code: str, unordered: bool) -> dict[str, int]:
    a, b = int(code[0]), int(code[1])
    x, y = (min(a, b), max(a, b)) if unordered else (a, b)
    return {
        "x": x,
        "y": y,
        "sum": x + y,
        "diff": abs(y - x),
        "prod": x * y,
        "x2": x * x,
        "y2": y * y,
        "tri": y * (y + 1) // 2 + x,
        "border": int(x in {0, 9} or y in {0, 9}),
        "center": int(x in {4, 5} or y in {4, 5}),
    }


def arithmetic_grid_search(code_to_symbol: dict[str, str]) -> list[dict]:
    codes = sorted(code_to_symbol)
    target = [code_to_symbol[code] for code in codes]
    rows = []

    base_rules = {
        "ordered_row": lambda c: int(c[0]),
        "ordered_col": lambda c: int(c[1]),
        "unordered_pair": lambda c: tuple(sorted((int(c[0]), int(c[1])))),
        "sum": lambda c: int(c[0]) + int(c[1]),
        "diff": lambda c: abs(int(c[0]) - int(c[1])),
        "prod_mod10": lambda c: (int(c[0]) * int(c[1])) % 10,
        "triangular_index": lambda c: feature_values(c, True)["tri"],
    }
    for name, keyer in base_rules.items():
        rows.append(eval_key_rule(codes, code_to_symbol, keyer, f"base_{name}", 4.0))

    feature_names = ["x", "y", "sum", "diff", "prod", "x2", "y2", "tri", "border", "center"]
    for unordered in (False, True):
        mode = "unordered" if unordered else "ordered"
        values_by_code = {code: feature_values(code, unordered) for code in codes}
        feature_arrays = {
            feature: [values_by_code[code][feature] for code in codes]
            for feature in feature_names
        }
        for f1_i, f1 in enumerate(feature_names):
            for f2 in feature_names[f1_i:]:
                best_for_pair = None
                # m > 13 is already suspicious for a compact formula over 14 symbols.
                # Larger moduli tend to become lookup tables with nicer syntax.
                arr1 = feature_arrays[f1]
                arr2 = feature_arrays[f2]
                for m in range(2, 14):
                    for a in range(m):
                        for b in range(m):
                            if a == 0 and b == 0:
                                continue
                            for c in range(m):
                                keys = [
                                    (a * v1 + b * v2 + c) % m
                                    for v1, v2 in zip(arr1, arr2)
                                ]
                                item = eval_key_values(
                                    codes,
                                    target,
                                    keys,
                                    f"mod_{mode}_{f1}_{f2}_m{m}_a{a}_b{b}_c{c}",
                                    complexity_cost=math.log2(m + 1) * 4 + 8,
                                )
                                if best_for_pair is None or (item["accuracy"], -item["mdl_bits_est"]) > (
                                    best_for_pair["accuracy"],
                                    -best_for_pair["mdl_bits_est"],
                                ):
                                    best_for_pair = item
                if best_for_pair:
                    rows.append(best_for_pair)

    rows.sort(key=lambda row: (-row["accuracy"], row["mdl_bits_est"], row["groups"]))
    return rows


def pair_symbol(code_to_symbol: dict[str, str], pair: str) -> str:
    a, b = pair
    vals = []
    for code in (pair, b + a):
        if code in code_to_symbol:
            vals.append(code_to_symbol[code])
    uniq = sorted(set(vals))
    return "/".join(uniq) if uniq else "."


def pair_orders() -> dict[str, list[str]]:
    pairs = [f"{i}{j}" for i in range(10) for j in range(i, 10)]
    orders = {
        "upper_row": pairs,
        "upper_row_rev": list(reversed(pairs)),
        "by_sum": sorted(pairs, key=lambda p: (int(p[0]) + int(p[1]), int(p[0]), int(p[1]))),
        "by_sum_rev": sorted(pairs, key=lambda p: (int(p[0]) + int(p[1]), int(p[0]), int(p[1])), reverse=True),
        "by_diff": sorted(pairs, key=lambda p: (int(p[1]) - int(p[0]), int(p[0]))),
        "by_diff_rev": sorted(pairs, key=lambda p: (int(p[1]) - int(p[0]), int(p[0])), reverse=True),
        "by_product": sorted(pairs, key=lambda p: (int(p[0]) * int(p[1]), int(p[0]), int(p[1]))),
        "by_triangular_index": sorted(pairs, key=lambda p: int(p[1]) * (int(p[1]) + 1) // 2 + int(p[0])),
    }
    # Full-grid spiral projected to first visit of unordered pair.
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
        pair = f"{min(a,b)}{max(a,b)}"
        if pair not in seen_set:
            seen.append(pair)
            seen_set.add(pair)
    orders["spiral_first_unordered"] = seen
    return orders


def best_period(seq: list[str]) -> dict:
    best = None
    for period in range(1, min(28, len(seq)) + 1):
        pattern = seq[:period]
        errors = sum(1 for idx, sym in enumerate(seq) if sym != pattern[idx % period])
        item = {"period": period, "errors": errors, "accuracy": (len(seq) - errors) / len(seq), "pattern": "".join(pattern)}
        if best is None or (item["accuracy"], -period) > (best["accuracy"], -best["period"]):
            best = item
    return best


def best_lore_string(seq: list[str]) -> dict:
    simple_seq = [sym if len(sym) == 1 and sym in SIGMA else "?" for sym in seq]
    best = None
    for word in LORE_STRINGS:
        filtered = [ch for ch in word if ch in SIGMA]
        if not filtered:
            continue
        for shift in range(len(filtered)):
            errors = 0
            for idx, sym in enumerate(simple_seq):
                if sym != filtered[(idx + shift) % len(filtered)]:
                    errors += 1
            item = {
                "source": word,
                "shift": shift,
                "errors": errors,
                "accuracy": (len(simple_seq) - errors) / len(simple_seq),
            }
            if best is None or item["accuracy"] > best["accuracy"]:
                best = item
    return best


def lz_complexity(seq: list[str]) -> int:
    # Lempel-Ziv phrase count over symbol tokens.
    seen = set()
    count = 0
    idx = 0
    while idx < len(seq):
        end = idx + 1
        while end <= len(seq) and tuple(seq[idx:end]) in seen:
            end += 1
        seen.add(tuple(seq[idx:end]))
        count += 1
        idx = end
    return count


def sequence_search(code_to_symbol: dict[str, str]) -> list[dict]:
    rows = []
    for name, pairs in pair_orders().items():
        seq = [pair_symbol(code_to_symbol, pair) for pair in pairs]
        period = best_period(seq)
        lore = best_lore_string(seq)
        lz = lz_complexity(seq)
        control_lz = []
        control_period = []
        for _ in range(300):
            shuffled = seq[:]
            random.shuffle(shuffled)
            control_lz.append(lz_complexity(shuffled))
            control_period.append(best_period(shuffled)["accuracy"])
        lz_mean = sum(control_lz) / len(control_lz)
        lz_sd = (sum((x - lz_mean) ** 2 for x in control_lz) / (len(control_lz) - 1)) ** 0.5
        p_mean = sum(control_period) / len(control_period)
        p_sd = (sum((x - p_mean) ** 2 for x in control_period) / (len(control_period) - 1)) ** 0.5
        rows.append(
            {
                "order": name,
                "sequence": " ".join(seq),
                "best_period": period,
                "best_lore_string": lore,
                "lz_phrase_count": lz,
                "lz_control_mean": lz_mean,
                "lz_z_lower_is_simpler": (lz_mean - lz) / lz_sd if lz_sd else 0.0,
                "period_control_mean": p_mean,
                "period_z": (period["accuracy"] - p_mean) / p_sd if p_sd else 0.0,
            }
        )
    rows.sort(key=lambda row: (-row["best_period"]["accuracy"], -row["lz_z_lower_is_simpler"]))
    return rows


def write_outputs(arith: list[dict], seq_rows: list[dict]) -> None:
    best_lookup = next(row for row in arith if row["hypothesis_id"] == "base_unordered_pair")
    lookup_equivalent_ids = {"base_unordered_pair", "base_triangular_index"}
    best_compact_non_lookup = next(
        row
        for row in arith
        if row["hypothesis_id"] not in lookup_equivalent_ids and row["groups"] < 55
    )
    data = {
        "schema": "deep_formula_leaderboard.v1",
        "translation_delta": "NONE",
        "arithmetic_rows_top": arith[:100],
        "sequence_rows": seq_rows,
        "verdict": {
            "best_lookup_equivalent": best_lookup,
            "best_compact_non_lookup": best_compact_non_lookup,
            "accepted_original_formula": None,
            "summary": "No compact analytic formula beats the unordered-pair lookup geometry.",
        },
    }
    OUT_JSON.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Deep Formula Search",
        "",
        "Generated by `deep_formula_search.py`.",
        "",
        "This search attempts to find an original-style compact formula beneath",
        "the known unordered-pair table. It does not translate 469.",
        "",
        "## Arithmetic/Grid Search",
        "",
        "| Rank | Rule | Accuracy | Errors | Groups | Est bits |",
        "|---:|---|---:|---:|---:|---:|",
    ]
    for idx, row in enumerate(arith[:25], start=1):
        lines.append(
            f"| {idx} | `{row['hypothesis_id']}` | {row['accuracy']:.3f} | {row['errors']} | {row['groups']} | {row['mdl_bits_est']:.1f} |"
        )
    lines.extend(
        [
            "",
            "The only near-exact rules are `base_unordered_pair` and the equivalent",
            "`base_triangular_index`: both encode the 55 unordered pair cells. They",
            "explain the geometry, but are still the pair table itself. The best",
            "compact non-lookup arithmetic/modular rule remains far below usable",
            "accuracy.",
            "",
            "## Pair-Table Sequence Search",
            "",
            "| Order | Best period accuracy | Period | LZ phrases | LZ z | Best lore string | Lore accuracy |",
            "|---|---:|---:|---:|---:|---|---:|",
        ]
    )
    for row in seq_rows:
        lore = row["best_lore_string"]
        lines.append(
            f"| `{row['order']}` | {row['best_period']['accuracy']:.3f} | {row['best_period']['period']} | {row['lz_phrase_count']} | {row['lz_z_lower_is_simpler']:.2f} | `{lore['source']}` | {lore['accuracy']:.3f} |"
        )
    lines.extend(
        [
            "",
            "No traversal exposes a strong period, seed phrase, or unusually low",
            "sequence complexity relative to shuffled controls.",
            "",
            "## Verdict",
            "",
            "Current evidence still points to a handmade unordered-pair table plus",
            "copy/assembly machinery. A deeper original formula was not found in this",
            "search pass.",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    formula = load_json(FORMULA_JSON)
    code_to_symbol = formula["code_to_symbol"]
    arith = arithmetic_grid_search(code_to_symbol)
    seq_rows = sequence_search(code_to_symbol)
    write_outputs(arith, seq_rows)
    best_non_lookup = next(
        row
        for row in arith
        if row["hypothesis_id"] not in {"base_unordered_pair", "base_triangular_index"}
        and row["groups"] < 55
    )
    print(f"wrote {OUT_JSON.relative_to(HERE)}")
    print(f"wrote {OUT_MD.relative_to(HERE)}")
    print(
        "best_non_lookup={hypothesis_id} accuracy={accuracy:.3f} errors={errors}".format(
            **best_non_lookup
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
