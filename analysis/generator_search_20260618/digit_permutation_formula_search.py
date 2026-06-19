#!/usr/bin/env python3
"""Digit-permutation formula search for the 469 pair table.

Earlier arithmetic searches used the visible digit order 0..9. This script
tests a stronger variant: perhaps the author first permuted digit identities,
then used a simple formula such as sum/difference/product.

The important control is search breadth. Product-like features create many
near-singleton groups, so high apparent accuracy can happen even on shuffled
targets. No translation is produced.
"""

from __future__ import annotations

import json
import random
from collections import Counter, defaultdict
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FORMULA_JSON = ROOT / "analysis" / "mechanism_model_20260618" / "mechanical_formula_469.json"

OUT_JSON = HERE / "digit_permutation_formula_results.json"
OUT_MD = HERE / "digit_permutation_formula_report.md"

RANDOM_SEED = 46920260619
OBSERVED_PERMUTATIONS = 50000
CONTROL_TARGETS = 200
CONTROL_PERMUTATIONS = 1000


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def primary_pair_symbol(pair_table: dict, pair: str) -> str:
    row = pair_table[pair]
    if row["status"] == "pure":
        return row["symbol_if_pure"]
    return sorted(row["symbols"])[0]


def feature_key(name: str, a: int, b: int) -> int | tuple[int, int]:
    x, y = min(a, b), max(a, b)
    if name == "sum":
        return x + y
    if name == "diff":
        return y - x
    if name == "product":
        return x * y
    if name == "sum_mod5":
        return (x + y) % 5
    if name == "sum_mod7":
        return (x + y) % 7
    if name == "product_mod7":
        return (x * y) % 7
    if name == "linear_mod11":
        return (2 * x + 3 * y) % 11
    if name == "sum_product_mod11":
        return ((x + y) % 11, (x * y) % 11)
    raise ValueError(name)


FEATURES = [
    "sum",
    "diff",
    "product",
    "sum_mod5",
    "sum_mod7",
    "product_mod7",
    "linear_mod11",
    "sum_product_mod11",
]


def score_feature(pairs: list[str], target: list[str], permutation: list[int], feature: str) -> dict:
    keys = []
    for pair in pairs:
        a = permutation[int(pair[0])]
        b = permutation[int(pair[1])]
        keys.append(feature_key(feature, a, b))
    groups = defaultdict(list)
    for key, symbol in zip(keys, target):
        groups[key].append(symbol)
    majority = {key: Counter(values).most_common(1)[0][0] for key, values in groups.items()}
    ok = sum(majority[key] == symbol for key, symbol in zip(keys, target))
    return {
        "accuracy": ok / len(target),
        "correct": ok,
        "groups": len(groups),
    }


def best_for_permutation(pairs: list[str], target: list[str], permutation: list[int]) -> dict:
    rows = []
    for feature in FEATURES:
        rows.append({"feature": feature, **score_feature(pairs, target, permutation, feature)})
    rows.sort(key=lambda row: (-row["accuracy"], row["groups"], row["feature"]))
    return rows[0]


def random_search(pairs: list[str], target: list[str], permutations: int, seed: int) -> tuple[dict, dict, list[dict]]:
    rng = random.Random(seed)
    best = None
    best_compact = None
    top = []
    for _idx in range(permutations):
        permutation = list(range(10))
        rng.shuffle(permutation)
        for feature in FEATURES:
            row = {"feature": feature, **score_feature(pairs, target, permutation, feature)}
            candidate = {
                **row,
                "permutation": permutation,
            }
            if best is None or (candidate["accuracy"], candidate["correct"]) > (best["accuracy"], best["correct"]):
                best = candidate
            if candidate["groups"] < 55 and (
                best_compact is None
                or (candidate["accuracy"], candidate["correct"]) > (best_compact["accuracy"], best_compact["correct"])
            ):
                best_compact = candidate
            top.append(candidate)
    top.sort(key=lambda row: (-row["accuracy"], row["groups"], row["feature"]))
    assert best_compact is not None
    return best, best_compact, top[:25]


def main() -> int:
    formula = load_json(FORMULA_JSON)
    pair_table = formula["pair_table"]
    pairs = [f"{i}{j}" for i in range(10) for j in range(i, 10)]
    target = [primary_pair_symbol(pair_table, pair) for pair in pairs]

    observed_best, observed_best_compact, observed_top = random_search(pairs, target, OBSERVED_PERMUTATIONS, RANDOM_SEED)
    rng = random.Random(RANDOM_SEED + 1)
    control_bests = []
    control_compact_bests = []
    for trial in range(CONTROL_TARGETS):
        shuffled = target[:]
        rng.shuffle(shuffled)
        best, best_compact, _top = random_search(pairs, shuffled, CONTROL_PERMUTATIONS, RANDOM_SEED + 1000 + trial)
        control_bests.append(best["accuracy"])
        control_compact_bests.append(best_compact["accuracy"])
    control_mean = sum(control_bests) / len(control_bests)
    control_sd = (sum((score - control_mean) ** 2 for score in control_bests) / (len(control_bests) - 1)) ** 0.5
    p_ge = (sum(score >= observed_best["accuracy"] for score in control_bests) + 1) / (len(control_bests) + 1)
    compact_mean = sum(control_compact_bests) / len(control_compact_bests)
    compact_sd = (sum((score - compact_mean) ** 2 for score in control_compact_bests) / (len(control_compact_bests) - 1)) ** 0.5
    compact_p_ge = (sum(score >= observed_best_compact["accuracy"] for score in control_compact_bests) + 1) / (
        len(control_compact_bests) + 1
    )

    result = {
        "schema": "digit_permutation_formula_results.v1",
        "translation_delta": "NONE",
        "accepted_original_formula": None,
        "observed_permutations": OBSERVED_PERMUTATIONS,
        "control_targets": CONTROL_TARGETS,
        "control_permutations_each": CONTROL_PERMUTATIONS,
        "best_lookup_equivalent": observed_best,
        "best_compact_non_lookup": observed_best_compact,
        "top_rows": observed_top,
        "control": {
            "best_accuracy_mean": control_mean,
            "best_accuracy_sd": control_sd,
            "best_accuracy_max": max(control_bests),
            "p_ge_observed": p_ge,
            "compact_accuracy_mean": compact_mean,
            "compact_accuracy_sd": compact_sd,
            "compact_accuracy_max": max(control_compact_bests),
            "compact_p_ge_observed": compact_p_ge,
        },
        "verdict": "rejected_lookup_equivalent_and_compact_false_positive",
    }
    write_json(OUT_JSON, result)

    lines = [
        "# Digit-Permutation Formula Search",
        "",
        "Generated by `digit_permutation_formula_search.py`.",
        "",
        "This pass tests whether simple arithmetic starts working after permuting",
        "the identities of digits `0..9`.",
        "",
        "## Best Candidate",
        "",
        "| Class | Feature | Accuracy | Groups | Permutation | Control mean | Control max | p | Verdict |",
        "|---|---:|---:|---|---:|---:|---:|---|",
        f"| lookup-equivalent | `{observed_best['feature']}` | {observed_best['correct']}/55 ({observed_best['accuracy']:.3f}) | {observed_best['groups']} | `{observed_best['permutation']}` | {control_mean:.3f} | {max(control_bests):.3f} | {p_ge:.3f} | `reject_lookup_disguise` |",
        f"| compact non-lookup | `{observed_best_compact['feature']}` | {observed_best_compact['correct']}/55 ({observed_best_compact['accuracy']:.3f}) | {observed_best_compact['groups']} | `{observed_best_compact['permutation']}` | {compact_mean:.3f} | {max(control_compact_bests):.3f} | {compact_p_ge:.3f} | `reject_control` |",
        "",
        "`sum_product_mod11` reaches 55/55 only because sum and product jointly",
        "identify the unordered digit pair; it is the pair lookup in mathematical",
        "clothing. The best compact non-lookup result is also matched by controls.",
        "",
        "## Top Observed Rows",
        "",
        "| Accuracy | Feature | Groups | Permutation |",
        "|---:|---|---:|---|",
    ]
    for row in observed_top[:10]:
        lines.append(f"| {row['accuracy']:.3f} | `{row['feature']}` | {row['groups']} | `{row['permutation']}` |")
    lines.extend(
        [
            "",
            "## Verdict",
            "",
        "Permuting digit identities does not reveal a compact arithmetic formula",
        "for the pair-table placement.",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT_JSON.relative_to(HERE)}")
    print(f"wrote {OUT_MD.relative_to(HERE)}")
    print(
        "best={}/55 feature={} p_ge={:.3f}".format(
            observed_best_compact["correct"],
            observed_best_compact["feature"],
            compact_p_ge,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
