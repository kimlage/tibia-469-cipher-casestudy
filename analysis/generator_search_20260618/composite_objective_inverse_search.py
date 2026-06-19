#!/usr/bin/env python3
"""Composite objective inverse search for the 469 pair table.

Several earlier passes rejected single objectives: row/column balance,
digit-shape pressure, context clustering, and repeat-rich symbol streams. This
pass asks a narrower process question that those tests did not cover:

    Could the observed 55-cell pair table be a local optimum for a sparse,
    human-plausible *combination* of such objectives?

The search is inverse and conservative. It enumerates small non-negative
integer-weight combinations of named metrics and checks whether any single
swap of two pair labels improves the composite score. It then repeats the same
best-of-search against inventory-preserving label shuffles.

Mechanical only. No plaintext, glossary, or semantic meaning is promoted.
"""

from __future__ import annotations

import itertools
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FORMULA_JSON = ROOT / "analysis" / "mechanism_model_20260618" / "mechanical_formula_469.json"
OCC_STREAMS = ROOT / "analysis" / "audit_20260609" / "homophone_channel" / "occ_streams.json"

OUT_JSON = HERE / "composite_objective_inverse_results.json"
OUT_MD = HERE / "composite_objective_inverse_report.md"

RANDOM_SEED = 46920260620
CONTROL_TRIALS = 80
SIGMA = tuple("*ABCEFILNORSTV")
DIGITS = "0123456789"
WEIGHT_PATTERNS = {
    1: [(1,)],
    2: [(1, 1), (1, 2), (2, 1), (1, 3), (3, 1)],
    3: [(1, 1, 1), (2, 1, 1), (1, 2, 1), (1, 1, 2), (3, 1, 1), (1, 3, 1), (1, 1, 3)],
}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def natural_pairs() -> list[str]:
    return [f"{a}{b}" for a in range(10) for b in range(a, 10)]


def pair_tuple(pair: str) -> tuple[int, int]:
    return int(pair[0]), int(pair[1])


def pair_key_from_code(code: str) -> str:
    return "".join(sorted(code))


def primary_pair_symbol(pair_table: dict[str, Any], pair: str) -> str:
    row = pair_table[pair]
    if row["status"] == "pure":
        return row["symbol_if_pure"]
    return sorted(row["symbols"])[0]


def entropy(counter: Counter[str]) -> float:
    total = sum(counter.values())
    if not total:
        return 0.0
    return -sum((count / total) * math.log2(count / total) for count in counter.values() if count)


def l2_against_expected(counts: dict[object, Counter[str]], global_counts: Counter[str], total_cells: int) -> float:
    value = 0.0
    for counter in counts.values():
        line_total = sum(counter.values())
        for symbol in SIGMA:
            expected = line_total * global_counts[symbol] / total_cells
            value += (counter[symbol] - expected) ** 2
    return value


def incident_counts(pairs: list[str], labels: list[str]) -> dict[int, Counter[str]]:
    counts = {digit: Counter() for digit in range(10)}
    for pair, label in zip(pairs, labels):
        a, b = pair_tuple(pair)
        counts[a][label] += 1
        if a != b:
            counts[b][label] += 1
    return counts


def line_counts(pairs: list[str], labels: list[str]) -> dict[str, Counter[str]]:
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    for pair, label in zip(pairs, labels):
        a, b = pair_tuple(pair)
        counts[f"row_{a}"][label] += 1
        counts[f"col_{b}"][label] += 1
        counts[f"sum_{a + b}"][label] += 1
        counts[f"diff_{b - a}"][label] += 1
        if a == b:
            counts["diag"][label] += 1
        if a in {0, 9} or b in {0, 9}:
            counts["border"][label] += 1
    return counts


def same_symbol_shared_digit(pairs: list[str], labels: list[str]) -> float:
    total = 0
    pair_digits = [{*pair} for pair in pairs]
    for left in range(len(pairs)):
        for right in range(left + 1, len(pairs)):
            if labels[left] == labels[right] and pair_digits[left].intersection(pair_digits[right]):
                total += 1
    return float(total)


def same_symbol_line_runs(pairs: list[str], labels: list[str]) -> float:
    by_pair = dict(zip(pairs, labels))
    total = 0
    for a in range(10):
        row = [by_pair[f"{a}{b}"] for b in range(a, 10)]
        total += sum(1 for x, y in zip(row, row[1:]) if x == y)
    for b in range(10):
        col = [by_pair[f"{a}{b}"] for a in range(0, b + 1)]
        total += sum(1 for x, y in zip(col, col[1:]) if x == y)
    for diff in range(10):
        line = [by_pair[f"{a}{a + diff}"] for a in range(0, 10 - diff)]
        total += sum(1 for x, y in zip(line, line[1:]) if x == y)
    return float(total)


def symbol_counts_from_occ() -> Counter[str]:
    occ = load_json(OCC_STREAMS)["occ"]
    return Counter({symbol: len(rows) for symbol, rows in occ.items()})


def token_pair_sequences() -> list[list[str]]:
    occ = load_json(OCC_STREAMS)["occ"]
    by_book: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for rows in occ.values():
        for row in rows:
            by_book[str(row["book"])].append((int(row["pos"]), pair_key_from_code(row["code"])))
    return [[pair for _, pair in sorted(rows)] for _, rows in sorted(by_book.items(), key=lambda item: int(item[0]))]


def context_edges(sequences: list[list[str]]) -> dict[tuple[str, str], float]:
    counts: Counter[tuple[str, str]] = Counter()
    for seq in sequences:
        for left, right in zip(seq, seq[1:]):
            if left <= right:
                counts[(left, right)] += 1
            else:
                counts[(right, left)] += 1
    return dict(counts)


def raw_digit_distribution(formula: dict[str, Any]) -> dict[str, float]:
    modules = {module["id"]: module["text"] for module in formula["modules"]}
    digits = []
    for recipe in formula["book_recipes"].values():
        digits.append("".join(modules[item["id"]] if item["type"] == "module" else item["text"] for item in recipe))
    counts = Counter("".join(digits))
    total = sum(counts.values())
    return {digit: counts[digit] / total for digit in DIGITS}


def token_code_stats() -> dict[str, float]:
    occ = load_json(OCC_STREAMS)["occ"]
    codes = [row["code"] for rows in occ.values() for row in rows]
    digit_counts = Counter("".join(codes))
    total_digits = sum(digit_counts.values())
    return {
        "zero_fraction": digit_counts["0"] / total_digits,
        "repeat_fraction": sum(1 for code in codes if code[0] == code[1]) / len(codes),
    }


def normalize_counter(counter: Counter[str]) -> dict[str, float]:
    total = sum(counter.values())
    return {digit: counter[digit] / total if total else 0.0 for digit in DIGITS}


def l1_digits(left: dict[str, float], right: dict[str, float]) -> float:
    return sum(abs(left[digit] - right[digit]) for digit in DIGITS)


def digit_pressure(labels_by_pair: dict[str, str], symbol_counts: Counter[str], raw_dist: dict[str, float], token_stats: dict[str, float]) -> dict[str, float]:
    cells_by_symbol: dict[str, list[str]] = defaultdict(list)
    for pair, symbol in labels_by_pair.items():
        cells_by_symbol[symbol].append(pair)
    digit_counts: Counter[str] = Counter()
    zero_weight = repeat_weight = token_weight = 0.0
    for symbol, count in symbol_counts.items():
        cells = cells_by_symbol.get(symbol, [])
        if not cells:
            continue
        per_cell = count / len(cells)
        for pair in cells:
            a, b = pair[0], pair[1]
            digit_counts[a] += per_cell
            digit_counts[b] += per_cell
            zero_weight += per_cell * ((1 if a == "0" else 0) + (1 if b == "0" else 0))
            repeat_weight += per_cell if a == b else 0.0
            token_weight += per_cell
    dist = normalize_counter(digit_counts)
    return {
        "digit_entropy": -sum(value * math.log2(value) for value in dist.values() if value),
        "digit_l1_to_raw": l1_digits(dist, raw_dist),
        "zero_error": abs((zero_weight / (2 * token_weight)) - token_stats["zero_fraction"]),
        "repeat_error": abs((repeat_weight / token_weight) - token_stats["repeat_fraction"]),
    }


def swap69(pair: str) -> str:
    trans = str.maketrans({"6": "9", "9": "6"})
    a, b = sorted(pair.translate(trans))
    return f"{a}{b}"


class MetricContext:
    def __init__(self, formula: dict[str, Any]) -> None:
        self.pairs = natural_pairs()
        self.symbol_counts = symbol_counts_from_occ()
        self.raw_dist = raw_digit_distribution(formula)
        self.token_stats = token_code_stats()
        self.edges = context_edges(token_pair_sequences())


FEATURES = [
    "incident_entropy_sum",
    "incident_balance",
    "line_balance",
    "avoid_shared_digit",
    "avoid_line_runs",
    "context_same_edge",
    "digit_entropy",
    "digit_l1_to_raw",
    "zero_fit",
    "repeat_fit",
    "swap69_symmetry",
]
FEATURE_INDEX = {feature: idx for idx, feature in enumerate(FEATURES)}


def metrics(labels: list[str], ctx: MetricContext) -> dict[str, float]:
    pairs = ctx.pairs
    global_counts = Counter(labels)
    inc = incident_counts(pairs, labels)
    lines = line_counts(pairs, labels)
    by_pair = dict(zip(pairs, labels))
    pressure = digit_pressure(by_pair, ctx.symbol_counts, ctx.raw_dist, ctx.token_stats)
    context_same = 0.0
    for (left, right), count in ctx.edges.items():
        if by_pair[left] == by_pair[right]:
            context_same += count
    swap_hits = sum(1 for pair in pairs if by_pair[pair] == by_pair[swap69(pair)])
    return {
        "incident_entropy_sum": sum(entropy(counter) for counter in inc.values()),
        "incident_balance": -l2_against_expected(inc, global_counts, len(labels)),
        "line_balance": -l2_against_expected(lines, global_counts, len(labels)),
        "avoid_shared_digit": -same_symbol_shared_digit(pairs, labels),
        "avoid_line_runs": -same_symbol_line_runs(pairs, labels),
        "context_same_edge": context_same,
        "digit_entropy": pressure["digit_entropy"],
        "digit_l1_to_raw": -pressure["digit_l1_to_raw"],
        "zero_fit": -pressure["zero_error"],
        "repeat_fit": -pressure["repeat_error"],
        "swap69_symmetry": float(swap_hits),
    }


def metric_scaler(labels: list[str], ctx: MetricContext, rng: random.Random, trials: int = 400) -> dict[str, dict[str, float]]:
    values = {feature: [] for feature in FEATURES}
    for _ in range(trials):
        shuffled = labels[:]
        rng.shuffle(shuffled)
        row = metrics(shuffled, ctx)
        for feature in FEATURES:
            values[feature].append(row[feature])
    out = {}
    for feature, rows in values.items():
        mean = sum(rows) / len(rows)
        sd = (sum((value - mean) ** 2 for value in rows) / (len(rows) - 1)) ** 0.5
        out[feature] = {"mean": mean, "sd": sd if sd else 1.0, "min": min(rows), "max": max(rows)}
    return out


def scaled_vector(raw: dict[str, float], scaler: dict[str, dict[str, float]]) -> dict[str, float]:
    return {feature: (raw[feature] - scaler[feature]["mean"]) / scaler[feature]["sd"] for feature in FEATURES}


def swap_vectors(labels: list[str], ctx: MetricContext, scaler: dict[str, dict[str, float]]) -> tuple[dict[str, float], list[dict[str, Any]]]:
    base = scaled_vector(metrics(labels, ctx), scaler)
    rows = []
    for left in range(len(labels)):
        for right in range(left + 1, len(labels)):
            if labels[left] == labels[right]:
                continue
            trial = labels[:]
            trial[left], trial[right] = trial[right], trial[left]
            vec = scaled_vector(metrics(trial, ctx), scaler)
            rows.append(
                {
                    "left_index": left,
                    "right_index": right,
                    "left_pair": ctx.pairs[left],
                    "right_pair": ctx.pairs[right],
                    "delta": {feature: vec[feature] - base[feature] for feature in FEATURES},
                }
            )
    return base, rows


def objective_candidates() -> list[dict[str, Any]]:
    candidates = []
    for size, weight_patterns in WEIGHT_PATTERNS.items():
        for feature_subset in itertools.combinations(FEATURES, size):
            for weights in weight_patterns:
                weight_sum = sum(weights)
                candidates.append(
                    {
                        "features": feature_subset,
                        "feature_indices": tuple(FEATURE_INDEX[feature] for feature in feature_subset),
                        "weights": weights,
                        "normalized_weights": tuple(weight / weight_sum for weight in weights),
                        "complexity": size + math.log2(weight_sum),
                    }
                )
    return candidates


OBJECTIVES = objective_candidates()


def evaluate_objective(base: list[float], swaps: list[dict[str, Any]], objective: dict[str, Any]) -> dict[str, Any]:
    features = objective["features"]
    feature_indices = objective["feature_indices"]
    weights = objective["normalized_weights"]
    base_score = sum(base[index] * weight for index, weight in zip(feature_indices, weights))
    best = None
    for row in swaps:
        delta = row["delta"]
        improvement = sum(delta[index] * weight for index, weight in zip(feature_indices, weights))
        if best is None or improvement > best["improvement"]:
            best = {
                "improvement": improvement,
                "left_pair": row["left_pair"],
                "right_pair": row["right_pair"],
            }
    if best is None:
        best = {"improvement": 0.0, "left_pair": None, "right_pair": None}
    return {
        "features": list(features),
        "weights": list(objective["weights"]),
        "normalized_weights": list(weights),
        "complexity": objective["complexity"],
        "base_score": base_score,
        "best_swap_improvement": best["improvement"],
        "best_swap": [best["left_pair"], best["right_pair"]],
        "is_local_optimum": best["improvement"] <= 1e-12,
    }


def best_objectives(labels: list[str], ctx: MetricContext, scaler: dict[str, dict[str, float]], limit: int = 20) -> list[dict[str, Any]]:
    base, swaps = swap_vectors(labels, ctx, scaler)
    base_array = [base[feature] for feature in FEATURES]
    swap_arrays = [
        {
            "left_pair": row["left_pair"],
            "right_pair": row["right_pair"],
            "delta": [row["delta"][feature] for feature in FEATURES],
        }
        for row in swaps
    ]
    rows = [evaluate_objective(base_array, swap_arrays, objective) for objective in OBJECTIVES]
    rows.sort(
        key=lambda row: (
            0 if row["is_local_optimum"] else 1,
            row["best_swap_improvement"],
            row["complexity"],
            -row["base_score"],
            row["features"],
            row["weights"],
        )
    )
    return rows[:limit]


def controls(labels: list[str], ctx: MetricContext, scaler: dict[str, dict[str, float]], observed_best: dict[str, Any]) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED + 2)
    best_improvements = []
    local_optimum_flags = []
    matching_key_improvements = []
    observed_key = (tuple(observed_best["features"]), tuple(observed_best["weights"]))
    for _ in range(CONTROL_TRIALS):
        shuffled = labels[:]
        rng.shuffle(shuffled)
        rows = best_objectives(shuffled, ctx, scaler, limit=len(OBJECTIVES))
        best = rows[0]
        best_improvements.append(best["best_swap_improvement"])
        local_optimum_flags.append(1.0 if best["is_local_optimum"] else 0.0)
        match = next(row for row in rows if (tuple(row["features"]), tuple(row["weights"])) == observed_key)
        matching_key_improvements.append(match["best_swap_improvement"])
    return {
        "trials": CONTROL_TRIALS,
        "best_of_search": {
            "best_swap_improvement": summarize(best_improvements, observed_best["best_swap_improvement"], lower_is_better=True),
            "local_optimum_rate": sum(local_optimum_flags) / len(local_optimum_flags),
        },
        "fixed_observed_objective": {
            "key": {"features": observed_best["features"], "weights": observed_best["weights"]},
            "best_swap_improvement": summarize(matching_key_improvements, observed_best["best_swap_improvement"], lower_is_better=True),
        },
    }


def summarize(values: list[float], observed: float, lower_is_better: bool) -> dict[str, float]:
    mean = sum(values) / len(values)
    sd = (sum((value - mean) ** 2 for value in values) / (len(values) - 1)) ** 0.5 if len(values) > 1 else 0.0
    if lower_is_better:
        p = (sum(value <= observed for value in values) + 1) / (len(values) + 1)
        z = (mean - observed) / sd if sd else 0.0
    else:
        p = (sum(value >= observed for value in values) + 1) / (len(values) + 1)
        z = (observed - mean) / sd if sd else 0.0
    return {"observed": observed, "mean": mean, "sd": sd, "min": min(values), "max": max(values), "p": p, "z": z}


def verdict(observed_best: dict[str, Any], ctrl: dict[str, Any]) -> str:
    p_best = ctrl["best_of_search"]["best_swap_improvement"]["p"]
    p_fixed = ctrl["fixed_observed_objective"]["best_swap_improvement"]["p"]
    if observed_best["is_local_optimum"] and p_best <= 0.01 and p_fixed <= 0.01:
        return "candidate_composite_objective_generator"
    if observed_best["is_local_optimum"]:
        return "local_optimum_but_control_common"
    if p_best <= 0.05 or p_fixed <= 0.05:
        return "weak_composite_objective_signal_not_formula"
    return "rejected_composite_objective"


def write_report(result: dict[str, Any]) -> None:
    best = result["best_objectives"][0]
    ctrl_best = result["controls"]["best_of_search"]
    ctrl_fixed = result["controls"]["fixed_observed_objective"]
    lines = [
        "# Composite Objective Inverse Search",
        "",
        "Generated by `composite_objective_inverse_search.py`.",
        "",
        "This pass tests whether the observed pair table is a local optimum",
        "for a sparse non-negative combination of named mechanical objectives.",
        "It assigns no plaintext.",
        "",
        "## Best Observed Composite",
        "",
        "| Features | Weights | Local optimum | Best swap | Best swap improvement | Base score | Verdict |",
        "|---|---|---:|---|---:|---:|---|",
        f"| `{', '.join(best['features'])}` | `{best['weights']}` | {best['is_local_optimum']} | `{best['best_swap'][0]}<->{best['best_swap'][1]}` | {best['best_swap_improvement']:.4f} | {best['base_score']:.3f} | `{result['verdict']}` |",
        "",
        "## Controls",
        "",
        "| Lens | Observed improvement | Mean | Best control | p(good) |",
        "|---|---:|---:|---:|---:|",
        f"| best-of-search shuffle | {ctrl_best['best_swap_improvement']['observed']:.4f} | {ctrl_best['best_swap_improvement']['mean']:.4f} | {ctrl_best['best_swap_improvement']['min']:.4f} | {ctrl_best['best_swap_improvement']['p']:.5f} |",
        f"| fixed observed objective | {ctrl_fixed['best_swap_improvement']['observed']:.4f} | {ctrl_fixed['best_swap_improvement']['mean']:.4f} | {ctrl_fixed['best_swap_improvement']['min']:.4f} | {ctrl_fixed['best_swap_improvement']['p']:.5f} |",
        "",
        f"Control local-optimum rate under best-of-search: `{ctrl_best['local_optimum_rate']:.3f}`.",
        "",
        "## Top Observed Objectives",
        "",
        "| Rank | Features | Weights | Local optimum | Best improvement | Best swap |",
        "|---:|---|---|---:|---:|---|",
    ]
    for idx, row in enumerate(result["best_objectives"][:20], start=1):
        lines.append(
            f"| {idx} | `{', '.join(row['features'])}` | `{row['weights']}` | {row['is_local_optimum']} | {row['best_swap_improvement']:.4f} | `{row['best_swap'][0]}<->{row['best_swap'][1]}` |"
        )
    lines += [
        "",
        "## Feature Set",
        "",
        "- `incident_entropy_sum`: maximize symbol diversity per digit endpoint.",
        "- `incident_balance`: minimize endpoint-symbol L2 imbalance.",
        "- `line_balance`: minimize row/column/sum/diff line-symbol L2 imbalance.",
        "- `avoid_shared_digit`: discourage same-symbol cells sharing a digit.",
        "- `avoid_line_runs`: discourage adjacent same-symbol line runs.",
        "- `context_same_edge`: reward same-symbol adjacent pair context in the books.",
        "- `digit_entropy`: maximize expected rendered digit entropy.",
        "- `digit_l1_to_raw`: match raw digit distribution.",
        "- `zero_fit`: match observed token zero fraction.",
        "- `repeat_fit`: match observed repeated-code fraction.",
        "- `swap69_symmetry`: reward label preservation under digit swap `6<->9`.",
        "",
        "## Interpretation",
        "",
        "A composite objective would be plausible only if a sparse objective makes",
        "the observed table a local optimum and this is rare under the same",
        "best-of-search on inventory-preserving shuffles. Otherwise the apparent",
        "objective is just post-hoc tuning over many weak metrics.",
        "",
        f"Translation delta: `{result['translation_delta']}`.",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    formula = load_json(FORMULA_JSON)
    ctx = MetricContext(formula)
    labels = [primary_pair_symbol(formula["pair_table"], pair) for pair in ctx.pairs]
    rng = random.Random(RANDOM_SEED)
    scaler = metric_scaler(labels, ctx, rng)
    observed_rows = best_objectives(labels, ctx, scaler, limit=len(OBJECTIVES))
    top_rows = observed_rows[:50]
    ctrl = controls(labels, ctx, scaler, observed_rows[0])
    result = {
        "schema": "composite_objective_inverse_results.v1",
        "source": str(FORMULA_JSON.relative_to(ROOT)),
        "random_seed": RANDOM_SEED,
        "control_trials": CONTROL_TRIALS,
        "candidate_objectives": len(OBJECTIVES),
        "features": FEATURES,
        "scaler": scaler,
        "best_objectives": top_rows,
        "controls": ctrl,
        "verdict": verdict(observed_rows[0], ctrl),
        "translation_delta": "NONE",
    }
    write_json(OUT_JSON, result)
    write_report(result)
    best = observed_rows[0]
    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(
        f"verdict={result['verdict']} local={best['is_local_optimum']} "
        f"best_improvement={best['best_swap_improvement']:.4f} objective={','.join(best['features'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
