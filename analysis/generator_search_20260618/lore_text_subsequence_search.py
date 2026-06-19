#!/usr/bin/env python3
"""Lore-text subsequence/window search for the 469 pair table.

This is a deliberately generous test of a tempting generator idea:

    maybe the 55 unordered pair cells were filled from a lore text, quote,
    title list, or formula-family string.

The search normalizes lore text to the internal symbol alphabet and asks
whether any matrix traversal is visible as a contiguous window or as a
subsequence. Controls shuffle the same source texts and repeat the same
search, so frequency-heavy source text is not allowed to masquerade as a
generator.

Mechanical only. No plaintext or glossary is promoted.
"""

from __future__ import annotations

import json
import random
from collections import Counter, defaultdict
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FORMULA_JSON = ROOT / "analysis" / "mechanism_model_20260618" / "mechanical_formula_469.json"

OUT_JSON = HERE / "lore_text_subsequence_results.json"
OUT_MD = HERE / "lore_text_subsequence_report.md"

SIGMA = "*ABCEFILNORSTV"
RANDOM_SEED = 469
CONTROL_REPS = 500
GLOBAL_CONTROL_REPS = 300
random.seed(RANDOM_SEED)


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def normalize_source(text: str) -> str:
    return "".join(ch for ch in text.upper() if ch in SIGMA)


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


def adjacent_digit_symbols(code_to_symbol: dict[str, str], digits: str) -> str:
    return "".join(code_to_symbol[pair] for pair in (digits[idx : idx + 2] for idx in range(len(digits) - 1)) if pair in code_to_symbol)


def chunk_digit_symbols(code_to_symbol: dict[str, str], digits: str, offset: int) -> str:
    out = []
    idx = offset
    while idx + 1 < len(digits):
        pair = digits[idx : idx + 2]
        if pair in code_to_symbol:
            out.append(code_to_symbol[pair])
        idx += 2
    return "".join(out)


def source_texts(code_to_symbol: dict[str, str]) -> dict[str, str]:
    demona_digits = "3243153347843839911934323233220321232"
    curated = {
        "great_calculator_quote": "It was me who assisted the great calculator to assemble the bonelords language.",
        "wrinkled_subjective_viewer": "The name is not fixed, but a complex formula that changes for the subjective viewer.",
        "demona_formula_family_words": "Honeminas Tridiag Donina Red Light Teleportation Through the Magic Web gate coordinate vector formula energy.",
        "honeminas_formula_raw": "g[a_,x_] := a g[3,2] + (4,3,1,5,3).(3,4,7,8,4) e=3m*2g+3p",
        "tridiag_formula_raw": "a=3er*8g+99k g[a_,l_] := e*g[1,1]+9g*3a h:=3pe-34u",
        "donina_formula_raw": "ft:=E[3,2,3]*fd(3.2),as->20 io=g[i,u]+2 ds(%)=[tr3+12\\32p-q] gh/3u+32=<%sd>",
        "secret_library_pair_words": "Secret Library book seven four zero three two four five three three one.",
        "paradox_mirror_context": "Paradox Tower mirror Riddler subjective viewer mad mage valley formula gibberish comparandum.",
        "all_curated_lore_words": (
            "You Cannot Even Imagine great calculator assemble bonelords language "
            "Honeminas Tridiag Donina Red Light Teleportation Through the Magic Web "
            "formula gate coordinate vector energy subjective viewer mirror pair "
            "Secret Library seven four zero three two four five three three one "
            "Paradox Tower Riddler Wydrin madman Tibia bonelord beholder Benna Telbenna Itelbenna Fas"
        ),
        "demona_numbers_adjacent_symbols": adjacent_digit_symbols(code_to_symbol, demona_digits),
        "demona_numbers_chunk_offset0": chunk_digit_symbols(code_to_symbol, demona_digits, 0),
        "demona_numbers_chunk_offset1": chunk_digit_symbols(code_to_symbol, demona_digits, 1),
        "secret_library_adjacent_symbols": adjacent_digit_symbols(code_to_symbol, "7403245331"),
        "secret_library_chunk_offset0": chunk_digit_symbols(code_to_symbol, "7403245331", 0),
        "secret_library_chunk_offset1": chunk_digit_symbols(code_to_symbol, "7403245331", 1),
    }
    return {key: normalize_source(value) for key, value in curated.items() if normalize_source(value)}


def window_score(pair_table: dict, pairs: list[str], window: str) -> tuple[int, int]:
    ok = 0
    for pair, char in zip(pairs, window):
        ok += char in acceptable_pair_symbols(pair_table, pair)
    return ok, len(pairs)


def best_window_for_text(pair_table: dict, orders: dict[str, list[str]], text: str) -> dict:
    rows = []
    for order_id, pairs in orders.items():
        if len(text) < len(pairs):
            continue
        for reverse in (False, True):
            oriented = text[::-1] if reverse else text
            for start in range(0, len(oriented) - len(pairs) + 1):
                window = oriented[start : start + len(pairs)]
                correct, total = window_score(pair_table, pairs, window)
                rows.append(
                    {
                        "order": order_id,
                        "reverse_source": reverse,
                        "start": start,
                        "window": window,
                        "correct": correct,
                        "total": total,
                        "accuracy": correct / total,
                    }
                )
    if not rows:
        return {
            "order": None,
            "reverse_source": False,
            "start": None,
            "window": "",
            "correct": 0,
            "total": 0,
            "accuracy": 0.0,
        }
    rows.sort(key=lambda row: (-row["accuracy"], row["order"], row["reverse_source"], row["start"]))
    return rows[0]


def best_lcs_for_text(pair_table: dict, orders: dict[str, list[str]], text: str) -> dict:
    rows = []
    for order_id, pairs in orders.items():
        for reverse in (False, True):
            oriented = text[::-1] if reverse else text
            prev = [0] * (len(oriented) + 1)
            for pair in pairs:
                cur = [0]
                allowed = acceptable_pair_symbols(pair_table, pair)
                for idx, char in enumerate(oriented, start=1):
                    if char in allowed:
                        cur.append(prev[idx - 1] + 1)
                    else:
                        cur.append(max(prev[idx], cur[-1]))
                prev = cur
            length = prev[-1]
            rows.append(
                {
                    "order": order_id,
                    "reverse_source": reverse,
                    "lcs_length": length,
                    "target_length": len(pairs),
                    "ratio": length / len(pairs),
                }
            )
    rows.sort(key=lambda row: (-row["ratio"], row["order"], row["reverse_source"]))
    return rows[0]


def source_shuffle_controls(pair_table: dict, orders: dict[str, list[str]], text: str, metric: str, observed: float) -> dict:
    values = []
    chars = list(text)
    for _ in range(CONTROL_REPS):
        random.shuffle(chars)
        shuffled = "".join(chars)
        if metric == "window":
            value = best_window_for_text(pair_table, orders, shuffled)["accuracy"]
        else:
            value = best_lcs_for_text(pair_table, orders, shuffled)["ratio"]
        values.append(value)
    mean = sum(values) / len(values)
    if len(values) > 1:
        sd = (sum((value - mean) ** 2 for value in values) / (len(values) - 1)) ** 0.5
    else:
        sd = 0.0
    return {
        "control_reps": len(values),
        "shuffle_mean": mean,
        "shuffle_sd": sd,
        "z_vs_shuffle": (observed - mean) / sd if sd else 0.0,
        "p_ge": (sum(value >= observed for value in values) + 1) / (len(values) + 1),
        "control_max": max(values),
    }


def global_shuffle_control(pair_table: dict, orders: dict[str, list[str]], sources: dict[str, str], metric: str, observed: float) -> dict:
    values = []
    source_items = list(sources.items())
    for _ in range(GLOBAL_CONTROL_REPS):
        best = 0.0
        for _, text in source_items:
            chars = list(text)
            random.shuffle(chars)
            shuffled = "".join(chars)
            if metric == "window":
                best = max(best, best_window_for_text(pair_table, orders, shuffled)["accuracy"])
            else:
                best = max(best, best_lcs_for_text(pair_table, orders, shuffled)["ratio"])
        values.append(best)
    mean = sum(values) / len(values)
    sd = (sum((value - mean) ** 2 for value in values) / (len(values) - 1)) ** 0.5
    return {
        "control_reps": len(values),
        "global_shuffle_mean": mean,
        "global_shuffle_sd": sd,
        "global_z_vs_shuffle": (observed - mean) / sd if sd else 0.0,
        "global_p_ge": (sum(value >= observed for value in values) + 1) / (len(values) + 1),
        "global_control_max": max(values),
    }


def symbol_count_summary(pair_table: dict, orders: dict[str, list[str]]) -> dict:
    order = orders["upper_row"]
    counts = Counter(primary_pair_symbol(pair_table, pair) for pair in order)
    conflict_pairs = [pair for pair in order if len(acceptable_pair_symbols(pair_table, pair)) > 1]
    return {
        "primary_symbol_counts": dict(sorted(counts.items())),
        "conflict_pairs": conflict_pairs,
    }


def main() -> int:
    formula = load_json(FORMULA_JSON)
    pair_table = formula["pair_table"]
    code_to_symbol = formula["code_to_symbol"]
    orders = pair_orders()
    sources = source_texts(code_to_symbol)

    source_rows = []
    for source_id, text in sources.items():
        best_window = best_window_for_text(pair_table, orders, text)
        best_lcs = best_lcs_for_text(pair_table, orders, text)
        window_controls = source_shuffle_controls(pair_table, orders, text, "window", best_window["accuracy"])
        lcs_controls = source_shuffle_controls(pair_table, orders, text, "lcs", best_lcs["ratio"])
        source_rows.append(
            {
                "source_id": source_id,
                "normalized_length": len(text),
                "normalized_text_preview": text[:120],
                "best_window": {**best_window, **window_controls},
                "best_lcs": {**best_lcs, **lcs_controls},
            }
        )

    source_rows.sort(
        key=lambda row: (
            -row["best_window"]["accuracy"],
            row["best_window"]["p_ge"],
            -row["best_lcs"]["ratio"],
            row["source_id"],
        )
    )
    best_window_source = source_rows[0]
    best_lcs_source = sorted(source_rows, key=lambda row: (-row["best_lcs"]["ratio"], row["best_lcs"]["p_ge"], row["source_id"]))[0]

    window_global = global_shuffle_control(pair_table, orders, sources, "window", best_window_source["best_window"]["accuracy"])
    lcs_global = global_shuffle_control(pair_table, orders, sources, "lcs", best_lcs_source["best_lcs"]["ratio"])

    promoted = (
        best_window_source["best_window"]["accuracy"] >= 0.60
        and window_global["global_p_ge"] <= 0.01
        and best_lcs_source["best_lcs"]["ratio"] >= 0.80
        and lcs_global["global_p_ge"] <= 0.01
    )
    verdict = "candidate_generator" if promoted else "rejected_control"

    result = {
        "schema": "lore_text_subsequence_results.v1",
        "random_seed": RANDOM_SEED,
        "source_count": len(sources),
        "orders_tested": list(orders),
        "symbol_count_summary": symbol_count_summary(pair_table, orders),
        "best_window_source": best_window_source,
        "best_lcs_source": best_lcs_source,
        "window_global_control": window_global,
        "lcs_global_control": lcs_global,
        "rows": source_rows,
        "verdict": verdict,
        "promotion_rule": "requires window accuracy >=0.60 and global p<=0.01 plus LCS ratio >=0.80 and global p<=0.01",
    }
    write_json(OUT_JSON, result)

    lines = [
        "# Lore Text Subsequence Search",
        "",
        "Generated by `lore_text_subsequence_search.py`.",
        "",
        "This pass tests whether a longer lore quote, formula-family text, title",
        "bundle, or numeric-lore rendering can generate the 55 unordered pair",
        "cells as a matrix traversal. It does not translate 469.",
        "",
        "## Best Contiguous Window",
        "",
        "| Source | Length | Order | Reverse | Accuracy | p(source shuffle) | p(global) |",
        "|---|---:|---|---|---:|---:|---:|",
    ]
    best = best_window_source["best_window"]
    lines.append(
        f"| `{best_window_source['source_id']}` | {best_window_source['normalized_length']} | "
        f"`{best['order']}` | `{best['reverse_source']}` | "
        f"{best['correct']}/{best['total']} ({best['accuracy']:.3f}) | "
        f"{best['p_ge']:.3f} | {window_global['global_p_ge']:.3f} |"
    )
    lines.extend(
        [
            "",
            "## Best Subsequence",
            "",
            "| Source | Length | Order | Reverse | LCS / target | p(source shuffle) | p(global) |",
            "|---|---:|---|---|---:|---:|---:|",
        ]
    )
    best_lcs = best_lcs_source["best_lcs"]
    lines.append(
        f"| `{best_lcs_source['source_id']}` | {best_lcs_source['normalized_length']} | "
        f"`{best_lcs['order']}` | `{best_lcs['reverse_source']}` | "
        f"{best_lcs['lcs_length']}/{best_lcs['target_length']} ({best_lcs['ratio']:.3f}) | "
        f"{best_lcs['p_ge']:.3f} | {lcs_global['global_p_ge']:.3f} |"
    )
    lines.extend(
        [
            "",
            "## Top Window Rows",
            "",
            "| Source | Accuracy | Source p | Window preview |",
            "|---|---:|---:|---|",
        ]
    )
    for row in source_rows[:10]:
        item = row["best_window"]
        preview = item["window"][:60]
        lines.append(f"| `{row['source_id']}` | {item['accuracy']:.3f} | {item['p_ge']:.3f} | `{preview}` |")
    lines.extend(
        [
            "",
            "## Verdict",
            "",
            f"`{verdict}`.",
            "",
            "Longer lore text does not currently recover the pair-cell placement beyond",
            "same-source and global shuffled controls. The lore remains useful as",
            "mechanism context: assembled, calculated, formulaic, pair/mirror-aware.",
            "It is not an accepted source-text generator for the 55-cell table.",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(f"verdict={verdict} best_window={best_window_source['source_id']} accuracy={best['accuracy']:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
