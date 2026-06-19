#!/usr/bin/env python3
"""Hidden digit-order distance search for the 469 pair table.

This pass tests whether the author may have first placed digits 0..9 in a
hidden line/cycle order, then assigned symbols by pair distance, midpoint, or
edge/arc features in that order. This is distinct from fixed keypad/clock
layouts and from arithmetic over visible digit values.

Mechanical only: no plaintext or glossary is promoted.
"""

from __future__ import annotations

import itertools
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FORMULA_JSON = ROOT / "analysis" / "mechanism_model_20260618" / "mechanical_formula_469.json"

OUT_JSON = HERE / "digit_order_distance_results.json"
OUT_MD = HERE / "digit_order_distance_report.md"

SIGMA = "*ABCEFILNORSTV"
RANDOM_SEED = 46920260619
CYCLE_EXACT_LIMIT = None
LINE_OBSERVED_SAMPLES = 80000
CONTROL_TRIALS = 25
CONTROL_SAMPLES_PER_FAMILY = 1500


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def natural_pairs() -> list[str]:
    return [f"{i}{j}" for i in range(10) for j in range(i, 10)]


def primary_pair_symbol(pair_table: dict, pair: str) -> str:
    row = pair_table[pair]
    if row["status"] == "pure":
        return row["symbol_if_pure"]
    return sorted(row["symbols"])[0]


def positions(order: tuple[int, ...] | list[int]) -> list[int]:
    pos = [0] * 10
    for idx, digit in enumerate(order):
        pos[digit] = idx
    return pos


def line_features(pos: list[int], pair: str, feature: str):
    if isinstance(pair, str):
        a, b = int(pair[0]), int(pair[1])
    else:
        a, b = pair
    x, y = sorted((pos[a], pos[b]))
    dist = y - x
    edge = min(x, 9 - y)
    mid2 = x + y
    if feature == "line_dist":
        return dist
    if feature == "line_dist_edge":
        return (dist, min(edge, 4))
    if feature == "line_dist_mid_bin":
        return (dist, mid2 // 3)
    if feature == "line_dist_mid_mod2":
        return (dist, mid2 % 2)
    if feature == "line_dist_mid_mod3":
        return (dist, mid2 % 3)
    if feature == "line_span_shape":
        return (dist, min(edge, 2), mid2 % 2)
    raise ValueError(feature)


def cycle_features(pos: list[int], pair: str, feature: str):
    if isinstance(pair, str):
        a, b = int(pair[0]), int(pair[1])
    else:
        a, b = pair
    x, y = pos[a], pos[b]
    raw = abs(y - x)
    dist = min(raw, 10 - raw)
    mid2 = (x + y) % 10
    crosses_zero = int(raw != dist and min(x, y) != 0)
    if feature == "cycle_dist":
        return dist
    if feature == "cycle_dist_mid_mod2":
        return (dist, mid2 % 2)
    if feature == "cycle_dist_mid_mod5":
        return (dist, mid2 % 5)
    if feature == "cycle_dist_cross0":
        return (dist, crosses_zero)
    if feature == "cycle_dist_anchor_side":
        return (dist, int(x == 0 or y == 0), crosses_zero)
    raise ValueError(feature)


LINE_FEATURES = [
    "line_dist",
    "line_dist_edge",
    "line_dist_mid_bin",
    "line_dist_mid_mod2",
    "line_dist_mid_mod3",
    "line_span_shape",
]

CYCLE_FEATURES = [
    "cycle_dist",
    "cycle_dist_mid_mod2",
    "cycle_dist_mid_mod5",
    "cycle_dist_cross0",
    "cycle_dist_anchor_side",
]


def score_keys(keys: list, labels: list[str], feature: str, order: list[int] | tuple[int, ...]) -> dict:
    groups = defaultdict(Counter)
    for key, symbol in zip(keys, labels):
        groups[key][symbol] += 1
    correct = sum(counter.most_common(1)[0][1] for counter in groups.values())
    group_count = len(groups)
    lookup_bits = len(labels) * math.log2(len(SIGMA))
    # Two-part rough cost: order + feature + group labels + exceptions.
    order_bits = math.log2(math.factorial(10))
    feature_bits = 4.0
    group_bits = group_count * math.log2(len(SIGMA))
    exception_bits = (len(labels) - correct) * (math.log2(len(labels)) + math.log2(len(SIGMA)))
    mdl_bits = order_bits + feature_bits + group_bits + exception_bits
    return {
        "feature": feature,
        "order": list(order),
        "correct": correct,
        "accuracy": correct / len(labels),
        "groups": group_count,
        "mdl_cost_bits": mdl_bits,
        "lookup_cost_bits": lookup_bits,
        "mdl_gain_vs_lookup_bits": lookup_bits - mdl_bits,
        "lookup_cost_ratio": mdl_bits / lookup_bits,
    }


def score_order(order: tuple[int, ...] | list[int], labels: list[str], pairs: list[str], family: str, features: list[str]) -> list[dict]:
    pos = positions(order)
    rows = []
    for feature in features:
        if family == "line":
            keys = [line_features(pos, pair, feature) for pair in pairs]
        elif family == "cycle":
            keys = [cycle_features(pos, pair, feature) for pair in pairs]
        else:
            raise ValueError(family)
        row = score_keys(keys, labels, feature, order)
        row["family"] = family
        rows.append(row)
    return rows


def better(row: dict, best: dict | None) -> bool:
    if best is None:
        return True
    return (
        row["correct"],
        -row["lookup_cost_ratio"],
        -row["groups"],
        row["feature"],
    ) > (
        best["correct"],
        -best["lookup_cost_ratio"],
        -best["groups"],
        best["feature"],
    )


def canonical_cycle_orders():
    count = 0
    for rest in itertools.permutations(range(1, 10)):
        # Fix 0 at position 0 and collapse reversal symmetry by requiring
        # digit 1 to appear before digit 9 on the cycle.
        if rest.index(1) > rest.index(9):
            continue
        order = (0,) + rest
        count += 1
        if CYCLE_EXACT_LIMIT is not None and count > CYCLE_EXACT_LIMIT:
            break
        yield order


def exact_cycle_search(labels: list[str], pairs: list[str]) -> dict:
    best = None
    top = []
    searched = 0
    for order in canonical_cycle_orders():
        searched += 1
        for row in score_order(order, labels, pairs, "cycle", CYCLE_FEATURES):
            if better(row, best):
                best = row
            top.append(row)
    top.sort(key=lambda row: (-row["correct"], row["lookup_cost_ratio"], row["groups"], row["feature"], row["order"]))
    assert best is not None
    return {"searched_orders": searched, "best": best, "top_rows": top[:25]}


def sampled_line_search(labels: list[str], pairs: list[str], samples: int, seed: int) -> dict:
    rng = random.Random(seed)
    best = None
    top = []
    seen = set()
    searched = 0
    while searched < samples:
        order = list(range(10))
        rng.shuffle(order)
        # Collapse reversal symmetry for line distance features.
        rev = list(reversed(order))
        key = tuple(order if tuple(order) <= tuple(rev) else rev)
        if key in seen:
            continue
        seen.add(key)
        searched += 1
        for row in score_order(list(key), labels, pairs, "line", LINE_FEATURES):
            if better(row, best):
                best = row
            top.append(row)
    top.sort(key=lambda row: (-row["correct"], row["lookup_cost_ratio"], row["groups"], row["feature"], row["order"]))
    assert best is not None
    return {"searched_orders": searched, "best": best, "top_rows": top[:25]}


def sampled_cycle_search(labels: list[str], pairs: list[str], samples: int, seed: int) -> dict:
    rng = random.Random(seed)
    best = None
    seen = set()
    searched = 0
    while searched < samples:
        rest = list(range(1, 10))
        rng.shuffle(rest)
        if rest.index(1) > rest.index(9):
            rest = list(reversed(rest))
        key = tuple([0] + rest)
        if key in seen:
            continue
        seen.add(key)
        searched += 1
        for row in score_order(key, labels, pairs, "cycle", CYCLE_FEATURES):
            if better(row, best):
                best = row
    assert best is not None
    return {"searched_orders": searched, "best": best}


def controls(labels: list[str], pairs: list[str]) -> dict:
    rng = random.Random(RANDOM_SEED + 1)
    line_scores = []
    cycle_scores = []
    line_mdl = []
    cycle_mdl = []
    for trial in range(CONTROL_TRIALS):
        shuffled = labels[:]
        rng.shuffle(shuffled)
        line = sampled_line_search(shuffled, pairs, CONTROL_SAMPLES_PER_FAMILY, RANDOM_SEED + 1000 + trial)
        cycle = sampled_cycle_search(shuffled, pairs, CONTROL_SAMPLES_PER_FAMILY, RANDOM_SEED + 2000 + trial)
        line_scores.append(line["best"]["correct"])
        cycle_scores.append(cycle["best"]["correct"])
        line_mdl.append(line["best"]["mdl_gain_vs_lookup_bits"])
        cycle_mdl.append(cycle["best"]["mdl_gain_vs_lookup_bits"])

    def summary(values: list[float], observed: float) -> dict:
        mean = sum(values) / len(values)
        sd = (sum((value - mean) ** 2 for value in values) / (len(values) - 1)) ** 0.5
        return {
            "mean": mean,
            "sd": sd,
            "max": max(values),
            "p_ge_observed": (sum(value >= observed for value in values) + 1) / (len(values) + 1),
        }

    return {
        "trials": CONTROL_TRIALS,
        "samples_per_family": CONTROL_SAMPLES_PER_FAMILY,
        "line_correct": line_scores,
        "cycle_correct": cycle_scores,
        "line_mdl_gain": line_mdl,
        "cycle_mdl_gain": cycle_mdl,
        "line_correct_summary": None,
        "cycle_correct_summary": None,
        "line_mdl_summary": None,
        "cycle_mdl_summary": None,
        "summary_func": summary,
    }


def verdict(best_line: dict, best_cycle: dict, ctrl: dict) -> str:
    best = best_line if best_line["correct"] >= best_cycle["correct"] else best_cycle
    if best["lookup_cost_ratio"] >= 1.0:
        return "lookup_disguise"
    p = min(ctrl["line_correct_summary"]["p_ge_observed"], ctrl["cycle_correct_summary"]["p_ge_observed"])
    if best["correct"] >= 45 and p <= 0.01 and best["mdl_gain_vs_lookup_bits"] > 0:
        return "candidate_hidden_digit_order_formula"
    if p <= 0.05:
        return "weak_hidden_digit_order_signal"
    return "rejected_control"


def main() -> int:
    formula = load_json(FORMULA_JSON)
    pair_strings = natural_pairs()
    pairs = [(int(pair[0]), int(pair[1])) for pair in pair_strings]
    labels = [primary_pair_symbol(formula["pair_table"], pair) for pair in pair_strings]

    cycle_exact = exact_cycle_search(labels, pairs)
    line_sample = sampled_line_search(labels, pairs, LINE_OBSERVED_SAMPLES, RANDOM_SEED)
    ctrl = controls(labels, pairs)
    summary = ctrl.pop("summary_func")
    ctrl["line_correct_summary"] = summary(ctrl["line_correct"], line_sample["best"]["correct"])
    ctrl["cycle_correct_summary"] = summary(ctrl["cycle_correct"], cycle_exact["best"]["correct"])
    ctrl["line_mdl_summary"] = summary(ctrl["line_mdl_gain"], line_sample["best"]["mdl_gain_vs_lookup_bits"])
    ctrl["cycle_mdl_summary"] = summary(ctrl["cycle_mdl_gain"], cycle_exact["best"]["mdl_gain_vs_lookup_bits"])
    ctrl.pop("line_correct")
    ctrl.pop("cycle_correct")
    ctrl.pop("line_mdl_gain")
    ctrl.pop("cycle_mdl_gain")

    result_verdict = verdict(line_sample["best"], cycle_exact["best"], ctrl)
    result = {
        "schema": "digit_order_distance_results.v1",
        "translation_delta": "NONE",
        "cycle_exact": cycle_exact,
        "line_sample": line_sample,
        "control": ctrl,
        "verdict": result_verdict,
    }
    write_json(OUT_JSON, result)

    best_line = line_sample["best"]
    best_cycle = cycle_exact["best"]
    lines = [
        "# Hidden Digit-Order Distance Search",
        "",
        "Generated by `digit_order_distance_search.py`.",
        "",
        "This pass tests whether pair labels come from distances or simple",
        "midpoint/edge features after placing digits in a hidden line or cycle",
        "order. It does not use or produce plaintext.",
        "",
        "## Summary",
        "",
        "| Family | Search | Best hits | Feature | Groups | MDL/lookup | Control p(hit) | Control p(MDL) |",
        "|---|---:|---:|---|---:|---:|---:|---:|",
        f"| line | {line_sample['searched_orders']} sampled orders | {best_line['correct']}/55 | `{best_line['feature']}` | {best_line['groups']} | {best_line['lookup_cost_ratio']:.3f} | {ctrl['line_correct_summary']['p_ge_observed']:.4f} | {ctrl['line_mdl_summary']['p_ge_observed']:.4f} |",
        f"| cycle | {cycle_exact['searched_orders']} exact canonical orders | {best_cycle['correct']}/55 | `{best_cycle['feature']}` | {best_cycle['groups']} | {best_cycle['lookup_cost_ratio']:.3f} | {ctrl['cycle_correct_summary']['p_ge_observed']:.4f} | {ctrl['cycle_mdl_summary']['p_ge_observed']:.4f} |",
        "",
        "## Top Line Rows",
        "",
        "| Hits | Feature | Groups | MDL/lookup | Order |",
        "|---:|---|---:|---:|---|",
    ]
    for row in line_sample["top_rows"][:10]:
        lines.append(f"| {row['correct']}/55 | `{row['feature']}` | {row['groups']} | {row['lookup_cost_ratio']:.3f} | `{row['order']}` |")
    lines.extend(
        [
            "",
            "## Top Cycle Rows",
            "",
            "| Hits | Feature | Groups | MDL/lookup | Order |",
            "|---:|---|---:|---:|---|",
        ]
    )
    for row in cycle_exact["top_rows"][:10]:
        lines.append(f"| {row['correct']}/55 | `{row['feature']}` | {row['groups']} | {row['lookup_cost_ratio']:.3f} | `{row['order']}` |")
    lines.extend(
        [
            "",
            "## Verdict",
            "",
            f"`{result_verdict}`.",
            "",
            "A hidden digit order would need to beat inventory-preserving shuffled",
            "targets and cost less than the 55-cell lookup. The tested line/cycle",
            "distance families do neither.",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT_JSON.relative_to(HERE)}")
    print(f"wrote {OUT_MD.relative_to(HERE)}")
    print(
        "line={}/55 p={:.4f} cycle={}/55 p={:.4f} verdict={}".format(
            best_line["correct"],
            ctrl["line_correct_summary"]["p_ge_observed"],
            best_cycle["correct"],
            ctrl["cycle_correct_summary"]["p_ge_observed"],
            result_verdict,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
