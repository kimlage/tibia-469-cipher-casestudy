#!/usr/bin/env python3
"""Finite-group pair formula search for the 469 pair table.

This pass tests a compact formula family not covered by visible digit
arithmetic or hidden digit order:

    digit -> hidden value in Z_m
    pair  -> sum/difference/product/quadratic key in Z_m
    key   -> symbol by majority table

If this were the original construction, it should beat inventory-preserving
label controls and cost less than the 55-cell lookup. No semantics are used.
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

OUT_JSON = HERE / "finite_group_pair_formula_results.json"
OUT_MD = HERE / "finite_group_pair_formula_report.md"

SIGMA = "*ABCEFILNORSTV"
RANDOM_SEED = 46920260619
MODULI = list(range(2, 19))
MODELS = ["sum", "cyclic_diff", "sum_and_cyclic_diff", "product", "quadratic_sum"]
STARTS_PER_MODEL = 12
MAX_SWEEPS = 5
CONTROL_TRIALS = 35

LORE_SEEDS = ["469", "3478", "43153", "34784", "74032", "45331"]


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def natural_pairs() -> list[tuple[int, int]]:
    return [(i, j) for i in range(10) for j in range(i, 10)]


def primary_pair_symbol(pair_table: dict, pair: str) -> str:
    row = pair_table[pair]
    if row["status"] == "pure":
        return row["symbol_if_pure"]
    return sorted(row["symbols"])[0]


def key_for(model: str, assignment: list[int], pair: tuple[int, int], modulus: int):
    a, b = pair
    x, y = assignment[a] % modulus, assignment[b] % modulus
    if model == "sum":
        return (x + y) % modulus
    if model == "cyclic_diff":
        diff = (x - y) % modulus
        return min(diff, (-diff) % modulus)
    if model == "sum_and_cyclic_diff":
        diff = (x - y) % modulus
        return ((x + y) % modulus, min(diff, (-diff) % modulus))
    if model == "product":
        return (x * y) % modulus
    if model == "quadratic_sum":
        return (x * x + y * y) % modulus
    raise ValueError(model)


def score_assignment(model: str, assignment: list[int], modulus: int, pairs: list[tuple[int, int]], labels: list[str]) -> dict:
    groups: dict[object, Counter[str]] = defaultdict(Counter)
    for pair, symbol in zip(pairs, labels):
        groups[key_for(model, assignment, pair, modulus)][symbol] += 1
    correct = sum(counter.most_common(1)[0][1] for counter in groups.values())
    group_count = len(groups)
    lookup_bits = len(labels) * math.log2(len(SIGMA))
    assignment_bits = 10 * math.log2(modulus)
    model_bits = math.log2(len(MODELS)) + math.log2(len(MODULI)) + 4.0
    group_bits = group_count * math.log2(len(SIGMA))
    exception_bits = (len(labels) - correct) * (math.log2(len(labels)) + math.log2(len(SIGMA)))
    mdl_bits = assignment_bits + model_bits + group_bits + exception_bits
    return {
        "model": model,
        "modulus": modulus,
        "assignment": assignment[:],
        "correct": correct,
        "accuracy": correct / len(labels),
        "groups": group_count,
        "mdl_cost_bits": mdl_bits,
        "lookup_cost_bits": lookup_bits,
        "mdl_gain_vs_lookup_bits": lookup_bits - mdl_bits,
        "lookup_cost_ratio": mdl_bits / lookup_bits,
    }


def better(row: dict, best: dict | None) -> bool:
    if best is None:
        return True
    return (
        row["correct"],
        row["mdl_gain_vs_lookup_bits"],
        -row["groups"],
        -row["modulus"],
        row["model"],
    ) > (
        best["correct"],
        best["mdl_gain_vs_lookup_bits"],
        -best["groups"],
        -best["modulus"],
        best["model"],
    )


def seed_assignment(seed: str, modulus: int) -> list[int]:
    digits = [int(ch) for ch in seed]
    if not digits:
        digits = [0]
    out = []
    value = 0
    for idx in range(10):
        value = (value + digits[idx % len(digits)] + idx) % modulus
        out.append(value)
    return out


def initial_assignments(modulus: int, rng: random.Random, starts: int) -> list[list[int]]:
    out = []
    out.append([digit % modulus for digit in range(10)])
    out.append([(digit * digit + digit) % modulus for digit in range(10)])
    out.append([(3 * digit + 1) % modulus for digit in range(10)])
    for seed in LORE_SEEDS:
        out.append(seed_assignment(seed, modulus))
    while len(out) < starts:
        out.append([rng.randrange(modulus) for _ in range(10)])
    return out[:starts]


def hillclimb(model: str, modulus: int, start: list[int], pairs: list[tuple[int, int]], labels: list[str]) -> dict:
    assignment = start[:]
    best = score_assignment(model, assignment, modulus, pairs, labels)
    for _sweep in range(MAX_SWEEPS):
        improved = False
        for digit in range(10):
            current_value = assignment[digit]
            local_best = best
            local_value = current_value
            for value in range(modulus):
                if value == current_value:
                    continue
                trial = assignment[:]
                trial[digit] = value
                row = score_assignment(model, trial, modulus, pairs, labels)
                if better(row, local_best):
                    local_best = row
                    local_value = value
            if local_value != current_value:
                assignment[digit] = local_value
                best = local_best
                improved = True
        if not improved:
            break
    return best


def search(labels: list[str], pairs: list[tuple[int, int]], seed: int) -> dict:
    rng = random.Random(seed)
    rows = []
    best = None
    for modulus in MODULI:
        starts = initial_assignments(modulus, rng, STARTS_PER_MODEL)
        for model in MODELS:
            for start in starts:
                row = hillclimb(model, modulus, start, pairs, labels)
                rows.append(row)
                if better(row, best):
                    best = row
    rows.sort(key=lambda row: (-row["correct"], -row["mdl_gain_vs_lookup_bits"], row["groups"], row["modulus"], row["model"]))
    assert best is not None
    return {"best": best, "top_rows": rows[:40], "row_count": len(rows)}


def control(labels: list[str], pairs: list[tuple[int, int]], observed: dict) -> dict:
    rng = random.Random(RANDOM_SEED + 1)
    hits = []
    mdl = []
    group_counts = []
    for trial in range(CONTROL_TRIALS):
        shuffled = labels[:]
        rng.shuffle(shuffled)
        row = search(shuffled, pairs, RANDOM_SEED + 1000 + trial)["best"]
        hits.append(row["correct"])
        mdl.append(row["mdl_gain_vs_lookup_bits"])
        group_counts.append(row["groups"])

    def summary(values: list[float], observed_value: float) -> dict:
        mean = sum(values) / len(values)
        sd = (sum((value - mean) ** 2 for value in values) / (len(values) - 1)) ** 0.5
        return {
            "mean": mean,
            "sd": sd,
            "max": max(values),
            "min": min(values),
            "p_ge_observed": (sum(value >= observed_value for value in values) + 1) / (len(values) + 1),
        }

    return {
        "trials": CONTROL_TRIALS,
        "hits": summary(hits, observed["correct"]),
        "mdl_gain": summary(mdl, observed["mdl_gain_vs_lookup_bits"]),
        "groups": summary(group_counts, observed["groups"]),
    }


def verdict(best: dict, ctrl: dict) -> str:
    if best["lookup_cost_ratio"] >= 1.0:
        return "lookup_disguise"
    if best["correct"] >= 45 and ctrl["hits"]["p_ge_observed"] <= 0.01 and best["mdl_gain_vs_lookup_bits"] > 0:
        return "candidate_finite_group_pair_formula"
    if ctrl["hits"]["p_ge_observed"] <= 0.05 or ctrl["mdl_gain"]["p_ge_observed"] <= 0.05:
        return "weak_finite_group_signal"
    return "rejected_control"


def main() -> int:
    formula = load_json(FORMULA_JSON)
    pair_table = formula["pair_table"]
    pairs = natural_pairs()
    labels = [primary_pair_symbol(pair_table, f"{a}{b}") for a, b in pairs]
    observed = search(labels, pairs, RANDOM_SEED)
    ctrl = control(labels, pairs, observed["best"])
    result_verdict = verdict(observed["best"], ctrl)
    result = {
        "schema": "finite_group_pair_formula_results.v1",
        "translation_delta": "NONE",
        "moduli": MODULI,
        "models": MODELS,
        "starts_per_model": STARTS_PER_MODEL,
        "max_sweeps": MAX_SWEEPS,
        "observed": observed,
        "control": ctrl,
        "verdict": result_verdict,
    }
    write_json(OUT_JSON, result)

    best = observed["best"]
    lines = [
        "# Finite-Group Pair Formula Search",
        "",
        "Generated by `finite_group_pair_formula_search.py`.",
        "",
        "This pass tests whether each digit has a hidden value in `Z_m`, and",
        "the pair symbol is generated by modular sum/difference/product-like",
        "keys. It is mechanical only and assigns no plaintext.",
        "",
        "## Summary",
        "",
        "| Best hits | Model | Modulus | Groups | MDL/lookup | Control p(hit) | Control p(MDL) | Verdict |",
        "|---:|---|---:|---:|---:|---:|---:|---|",
        f"| {best['correct']}/55 | `{best['model']}` | {best['modulus']} | {best['groups']} | {best['lookup_cost_ratio']:.3f} | {ctrl['hits']['p_ge_observed']:.4f} | {ctrl['mdl_gain']['p_ge_observed']:.4f} | `{result_verdict}` |",
        "",
        f"Best assignment digit0..9: `{best['assignment']}`.",
        "",
        "## Top Rows",
        "",
        "| Hits | Model | m | Groups | MDL/lookup | Assignment |",
        "|---:|---|---:|---:|---:|---|",
    ]
    for row in observed["top_rows"][:20]:
        lines.append(
            f"| {row['correct']}/55 | `{row['model']}` | {row['modulus']} | {row['groups']} | {row['lookup_cost_ratio']:.3f} | `{row['assignment']}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "A finite-group formula would be useful only if it beats the same search",
            "on inventory-preserving shuffled labels and costs less than the table",
            "lookup. This pass does not satisfy that condition.",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT_JSON.relative_to(HERE)}")
    print(f"wrote {OUT_MD.relative_to(HERE)}")
    print(
        "best={}/55 model={} m={} p_hit={:.4f} verdict={}".format(
            best["correct"],
            best["model"],
            best["modulus"],
            ctrl["hits"]["p_ge_observed"],
            result_verdict,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
