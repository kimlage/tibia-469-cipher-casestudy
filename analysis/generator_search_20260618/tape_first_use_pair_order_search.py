#!/usr/bin/env python3
"""Tape first-use pair-order search.

The tape-token projection gives a first-use order for 53 of the 55 unordered
pair cells. This pass tests whether that order is a simple matrix traversal or
digit-coordinate formula, which would be a candidate for the original pair-table
construction.

Mechanical only. No plaintext is promoted.
"""

from __future__ import annotations

import json
import math
import random
from pathlib import Path

import tape_tokenization_analysis as tape_tokens


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TAPE_FORMULA_JSON = HERE / "tape_based_formula_469.json"

OUT_JSON = HERE / "tape_first_use_pair_order_results.json"
OUT_MD = HERE / "tape_first_use_pair_order_report.md"

RANDOM_SEED = 46920260624
CONTROL_TRIALS = 5000


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def all_pairs() -> list[str]:
    return [f"{i}{j}" for i in range(10) for j in range(i, 10)]


def spiral_first_unordered() -> list[str]:
    seen = []
    seen_set = set()
    top, bottom, left, right = 0, 9, 0, 9
    while top <= bottom and left <= right:
        for col in range(left, right + 1):
            pair = "".join(map(str, sorted((top, col))))
            if pair not in seen_set:
                seen.append(pair)
                seen_set.add(pair)
        top += 1
        for row in range(top, bottom + 1):
            pair = "".join(map(str, sorted((row, right))))
            if pair not in seen_set:
                seen.append(pair)
                seen_set.add(pair)
        right -= 1
        if top <= bottom:
            for col in range(right, left - 1, -1):
                pair = "".join(map(str, sorted((bottom, col))))
                if pair not in seen_set:
                    seen.append(pair)
                    seen_set.add(pair)
            bottom -= 1
        if left <= right:
            for row in range(bottom, top - 1, -1):
                pair = "".join(map(str, sorted((row, left))))
                if pair not in seen_set:
                    seen.append(pair)
                    seen_set.add(pair)
            left += 1
    return seen


def natural_orders() -> dict[str, list[str]]:
    pairs = all_pairs()
    rows = {
        "upper_row": pairs,
        "upper_row_rev": list(reversed(pairs)),
        "upper_row_snake": [
            pair
            for i in range(10)
            for pair in ([f"{i}{j}" for j in range(i, 10)] if i % 2 == 0 else [f"{i}{j}" for j in range(9, i - 1, -1)])
        ],
        "upper_col": [f"{i}{j}" for j in range(10) for i in range(j + 1)],
        "upper_col_rev": list(reversed([f"{i}{j}" for j in range(10) for i in range(j + 1)])),
        "by_sum": sorted(pairs, key=lambda p: (int(p[0]) + int(p[1]), int(p[0]), int(p[1]))),
        "by_sum_rev": sorted(pairs, key=lambda p: (-(int(p[0]) + int(p[1])), int(p[0]), int(p[1]))),
        "by_diff": sorted(pairs, key=lambda p: (int(p[1]) - int(p[0]), int(p[0]), int(p[1]))),
        "by_diff_rev": sorted(pairs, key=lambda p: (-(int(p[1]) - int(p[0])), int(p[0]), int(p[1]))),
        "by_product": sorted(pairs, key=lambda p: (int(p[0]) * int(p[1]), int(p[0]), int(p[1]))),
        "by_product_rev": sorted(pairs, key=lambda p: (-(int(p[0]) * int(p[1])), int(p[0]), int(p[1]))),
        "by_triangular_index": sorted(pairs, key=lambda p: int(p[1]) * (int(p[1]) + 1) // 2 + int(p[0])),
        "center_distance": sorted(pairs, key=lambda p: ((int(p[0]) - 4.5) ** 2 + (int(p[1]) - 4.5) ** 2, int(p[0]), int(p[1]))),
        "center_distance_rev": sorted(pairs, key=lambda p: (-((int(p[0]) - 4.5) ** 2 + (int(p[1]) - 4.5) ** 2), int(p[0]), int(p[1]))),
        "diagonal_then_rows": sorted(pairs, key=lambda p: (int(p[1]) - int(p[0]), int(p[0]))),
        "spiral_first_unordered": spiral_first_unordered(),
    }
    # Lore-number digit order variants: sort pair cells by first occurrence of
    # either digit in the clue string, then by the natural cell.
    for seed in ["469", "3478", "43153", "34784", "74032", "45331"]:
        rank = {int(digit): idx for idx, digit in enumerate(dict.fromkeys(seed + "0123456789"))}
        rows[f"digit_order_{seed}"] = sorted(pairs, key=lambda p: (rank[int(p[0])], rank[int(p[1])], p))
    return rows


def ranks(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda index: values[index])
    out = [0.0] * len(values)
    index = 0
    while index < len(order):
        end = index + 1
        while end < len(order) and values[order[end]] == values[order[index]]:
            end += 1
        rank = (index + end - 1) / 2.0
        for pos in range(index, end):
            out[order[pos]] = rank
        index = end
    return out


def spearman(a: list[float], b: list[float]) -> float:
    ra = ranks(a)
    rb = ranks(b)
    mean_a = sum(ra) / len(ra)
    mean_b = sum(rb) / len(rb)
    numerator = sum((x - mean_a) * (y - mean_b) for x, y in zip(ra, rb))
    denom_a = sum((x - mean_a) ** 2 for x in ra)
    denom_b = sum((y - mean_b) ** 2 for y in rb)
    denom = math.sqrt(denom_a * denom_b)
    return numerator / denom if denom else 0.0


def lcs_len(left: list[str], right: list[str]) -> int:
    # For this pass both lists contain the same pair set, so LCS is LIS over
    # right-side ranks.
    import bisect

    rank = {item: index for index, item in enumerate(right)}
    piles: list[int] = []
    for item in left:
        value = rank[item]
        pos = bisect.bisect_left(piles, value)
        if pos == len(piles):
            piles.append(value)
        else:
            piles[pos] = value
    return len(piles)


def adjacency_hits(left: list[str], right: list[str]) -> int:
    right_adj = {frozenset((right[index], right[index + 1])) for index in range(len(right) - 1)}
    return sum(frozenset((left[index], left[index + 1])) in right_adj for index in range(len(left) - 1))


def score_order(tape_order: list[str], candidate: list[str]) -> dict:
    observed_set = set(tape_order)
    candidate_filtered = [pair for pair in candidate if pair in observed_set]
    candidate_rank = {pair: idx for idx, pair in enumerate(candidate_filtered)}
    tape_rank = list(range(len(tape_order)))
    cand_rank_values = [candidate_rank[pair] for pair in tape_order]
    rho = spearman(tape_rank, cand_rank_values)
    lcs = lcs_len(tape_order, candidate_filtered)
    adj = adjacency_hits(tape_order, candidate_filtered)
    return {
        "observed_pair_count": len(tape_order),
        "candidate_pair_count": len(candidate_filtered),
        "spearman": rho,
        "abs_spearman": abs(rho),
        "lcs": lcs,
        "lcs_fraction": lcs / len(tape_order),
        "adjacency_hits": adj,
        "adjacency_fraction": adj / max(1, len(tape_order) - 1),
    }


def summarize(values: list[float], observed: float, high_is_good: bool = True) -> dict:
    mean = sum(values) / len(values)
    sd = (sum((value - mean) ** 2 for value in values) / (len(values) - 1)) ** 0.5
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
        "z_good_direction": z,
        "p_good_direction": p,
        "control_min": min(values),
        "control_max": max(values),
    }


def tape_first_pair_order(formula: dict) -> tuple[list[str], list[dict]]:
    books, segment_maps = tape_tokens.reconstruct_books(formula)
    token_maps = tape_tokens.align_tokens(books)
    projected = tape_tokens.project_tokens(token_maps, segment_maps)
    component_order = {row["id"]: index for index, row in enumerate(formula["tape_components"])}
    first = {}
    for row in projected:
        if not row["mapped_to_tape"]:
            continue
        key = (component_order[row["component_id"]], row["component_start"], row["component_end"], int(row["book"]), row["token_index"])
        if row["pair_key"] not in first or key < first[row["pair_key"]]["sort_key"]:
            first[row["pair_key"]] = {**row, "sort_key": key}
    ordered_rows = sorted(first.values(), key=lambda row: row["sort_key"])
    return [row["pair_key"] for row in ordered_rows], ordered_rows


def run_controls(tape_order: list[str], candidates: dict[str, list[str]]) -> list[dict]:
    rng = random.Random(RANDOM_SEED)
    rows = []
    observed_set = set(tape_order)
    for order_id, candidate in candidates.items():
        observed = score_order(tape_order, candidate)
        controls = {"abs_spearman": [], "lcs": [], "adjacency_hits": []}
        candidate_filtered = [pair for pair in candidate if pair in observed_set]
        current = tape_order[:]
        for _trial in range(CONTROL_TRIALS):
            rng.shuffle(current)
            score = score_order(current, candidate_filtered)
            controls["abs_spearman"].append(score["abs_spearman"])
            controls["lcs"].append(score["lcs"])
            controls["adjacency_hits"].append(score["adjacency_hits"])
        row = {
            "order_id": order_id,
            **observed,
            "abs_spearman_control": summarize(controls["abs_spearman"], observed["abs_spearman"]),
            "lcs_control": summarize(controls["lcs"], observed["lcs"]),
            "adjacency_control": summarize(controls["adjacency_hits"], observed["adjacency_hits"]),
        }
        row["best_raw_p"] = min(
            row["abs_spearman_control"]["p_good_direction"],
            row["lcs_control"]["p_good_direction"],
            row["adjacency_control"]["p_good_direction"],
        )
        rows.append(row)
    rows.sort(key=lambda row: (row["best_raw_p"], -row["lcs"], -row["abs_spearman"]))
    metric_count = len(candidates) * 3
    for row in rows:
        row["bonferroni_p"] = min(1.0, row["best_raw_p"] * metric_count)
        row["verdict"] = "candidate" if row["bonferroni_p"] <= 0.01 else "rejected_control"
    return rows


def write_report(result: dict) -> None:
    lines = [
        "# Tape First-Use Pair Order Search",
        "",
        "Generated by `tape_first_use_pair_order_search.py`.",
        "",
        "This pass tests whether the first-use order of unordered pair cells inside",
        "the reusable tape layer matches a simple matrix traversal or lore-digit",
        "order. It does not translate 469.",
        "",
        "## First Pair Order",
        "",
        f"- Observed on tape: {result['observed_pair_count']} / 55 pairs.",
        f"- Missing from tape: `{result['missing_pairs']}`.",
        f"- First 30: `{result['first_30']}`.",
        "",
        "## Best Orders",
        "",
        "| Order | rho | LCS | Adjacent hits | raw p | Bonferroni p | Verdict |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in result["rows"][:20]:
        lines.append(
            f"| `{row['order_id']}` | {row['spearman']:.3f} | {row['lcs']} | "
            f"{row['adjacency_hits']} | {row['best_raw_p']:.5f} | {row['bonferroni_p']:.5f} | `{row['verdict']}` |"
        )
    lines += ["", "## Verdict", ""]
    if result["verdict"] == "candidate_tape_first_use_order":
        lines.append("A tape first-use order survived controls. Treat as mechanical only.")
    else:
        lines.append(
            "No tested row/column/diagonal/spiral/coordinate/lore-digit order explains "
            "the order in which pair cells first appear on the reusable tapes. This "
            "argues against deriving the pair table by a simple tape-introduction "
            "walk."
        )
    lines += ["", f"Translation delta: `{result['translation_delta']}`.", ""]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    formula = load_json(TAPE_FORMULA_JSON)
    tape_order, first_rows = tape_first_pair_order(formula)
    candidates = natural_orders()
    rows = run_controls(tape_order, candidates)
    missing_pairs = [pair for pair in all_pairs() if pair not in set(tape_order)]
    verdict = "candidate_tape_first_use_order" if rows[0]["bonferroni_p"] <= 0.01 else "rejected_control"
    result = {
        "schema": "tape_first_use_pair_order_results.v1",
        "random_seed": RANDOM_SEED,
        "control_trials": CONTROL_TRIALS,
        "observed_pair_count": len(tape_order),
        "missing_pairs": missing_pairs,
        "first_30": tape_order[:30],
        "first_rows_top30": [
            {
                "pair_key": row["pair_key"],
                "code": row["code"],
                "symbol": row["symbol"],
                "component_id": row["component_id"],
                "component_start": row["component_start"],
                "book": row["book"],
                "token_index": row["token_index"],
            }
            for row in first_rows[:30]
        ],
        "rows": rows,
        "best": rows[0],
        "verdict": verdict,
        "translation_delta": "NONE",
    }
    write_json(OUT_JSON, result)
    write_report(result)
    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(
        f"verdict={verdict} best={rows[0]['order_id']} raw_p={rows[0]['best_raw_p']:.5f} "
        f"bonferroni={rows[0]['bonferroni_p']:.5f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
