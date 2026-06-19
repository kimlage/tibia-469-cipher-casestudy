#!/usr/bin/env python3
"""Digit/symbol automorphism search for the 469 pair table.

This pass asks whether the 55-cell unordered pair table has a hidden symmetry:
a digit permutation maps cells to cells while preserving labels, or preserving
labels up to one fixed symbol permutation. A true compact construction might
leave such a trace. A lookup table generally should not.

Mechanical only. No plaintext or translation is promoted.
"""

from __future__ import annotations

import itertools
import json
import math
import random
from collections import Counter
from functools import lru_cache
from pathlib import Path

try:
    from scipy.optimize import linear_sum_assignment
except Exception:  # pragma: no cover - fallback for minimal environments
    linear_sum_assignment = None


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FORMULA_JSON = ROOT / "analysis" / "mechanism_model_20260618" / "mechanical_formula_469.json"

OUT_JSON = HERE / "digit_symbol_automorphism_results.json"
OUT_MD = HERE / "digit_symbol_automorphism_report.md"

SIGMA = list("*ABCEFILNORSTV")
RANDOM_SEED = 46920260619
RANDOM_PERMUTATIONS = 350
CONTROL_TRIALS = 150


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def natural_pairs() -> list[tuple[int, int]]:
    return [(a, b) for a in range(10) for b in range(a, 10)]


def primary_pair_symbol(pair_table: dict, pair: tuple[int, int]) -> str:
    row = pair_table[f"{pair[0]}{pair[1]}"]
    if row["status"] == "pure":
        return row["symbol_if_pure"]
    return sorted(row["symbols"])[0]


def permute_pair(pair: tuple[int, int], perm: tuple[int, ...]) -> tuple[int, int]:
    a, b = perm[pair[0]], perm[pair[1]]
    return (a, b) if a <= b else (b, a)


def affine_permutations() -> list[dict]:
    out = []
    for mul in [1, 3, 7, 9]:
        for add in range(10):
            perm = tuple((mul * digit + add) % 10 for digit in range(10))
            if len(set(perm)) == 10:
                out.append({"id": f"affine_mod10_{mul}_{add}", "family": "affine_mod10", "perm": perm})
    return out


def simple_permutations() -> list[dict]:
    out = [
        {"id": "identity", "family": "identity", "perm": tuple(range(10))},
        {"id": "reverse_9_minus_d", "family": "reflection", "perm": tuple(9 - d for d in range(10))},
        {"id": "swap_19", "family": "known_conflict", "perm": tuple(9 if d == 1 else 1 if d == 9 else d for d in range(10))},
        {"id": "swap_33_66", "family": "tape_exception", "perm": tuple(6 if d == 3 else 3 if d == 6 else d for d in range(10))},
    ]
    for i in range(10):
        for j in range(i + 1, 10):
            perm = list(range(10))
            perm[i], perm[j] = perm[j], perm[i]
            out.append({"id": f"swap_{i}_{j}", "family": "transposition", "perm": tuple(perm)})
    for shift in range(1, 10):
        out.append({"id": f"decimal_shift_{shift}", "family": "decimal_shift", "perm": tuple((d + shift) % 10 for d in range(10))})
    return out


def lore_seed_permutations() -> list[dict]:
    seeds = ["469", "3478", "43153", "34784", "74032", "45331", "1", "1991", "3366", "3993"]
    out = []
    for seed in seeds:
        seen = []
        for ch in seed:
            digit = int(ch)
            if digit not in seen:
                seen.append(digit)
        for digit in range(10):
            if digit not in seen:
                seen.append(digit)
        out.append({"id": f"seed_order_{seed}", "family": "lore_seed_order", "perm": tuple(seen)})
        inv = [0] * 10
        for idx, digit in enumerate(seen):
            inv[digit] = idx
        out.append({"id": f"seed_rank_{seed}", "family": "lore_seed_rank", "perm": tuple(inv)})
    return out


def random_permutations(count: int) -> list[dict]:
    rng = random.Random(RANDOM_SEED)
    out = []
    seen = set()
    while len(out) < count:
        perm = list(range(10))
        rng.shuffle(perm)
        tup = tuple(perm)
        if tup in seen:
            continue
        seen.add(tup)
        out.append({"id": f"random_{len(out):04d}", "family": "random_sample", "perm": tup})
    return out


def candidate_permutations() -> list[dict]:
    rows = simple_permutations() + affine_permutations() + lore_seed_permutations() + random_permutations(RANDOM_PERMUTATIONS)
    dedup = {}
    for row in rows:
        dedup.setdefault(row["perm"], row)
    return list(dedup.values())


def best_symbol_mapping(confusion: list[list[int]]) -> tuple[int, list[int]]:
    n = len(SIGMA)
    if linear_sum_assignment is not None:
        rows, cols = linear_sum_assignment([[-value for value in row] for row in confusion])
        mapping = [0] * n
        score = 0
        for row, col in zip(rows, cols):
            mapping[row] = col
            score += confusion[row][col]
        return score, mapping

    @lru_cache(maxsize=None)
    def dp(source_idx: int, used_mask: int) -> tuple[int, tuple[int, ...]]:
        if source_idx == n:
            return 0, ()
        best_score = -1
        best_tail: tuple[int, ...] = ()
        for target_idx in range(n):
            if used_mask & (1 << target_idx):
                continue
            score, tail = dp(source_idx + 1, used_mask | (1 << target_idx))
            score += confusion[source_idx][target_idx]
            if score > best_score:
                best_score = score
                best_tail = (target_idx,) + tail
        return best_score, best_tail

    score, mapping = dp(0, 0)
    return score, list(mapping)


def evaluate_perm(row: dict, pairs: list[tuple[int, int]], labels_by_pair: dict[tuple[int, int], str]) -> dict:
    perm = row["perm"]
    identity_hits = 0
    confusion = [[0 for _ in SIGMA] for _ in SIGMA]
    symbol_index = {symbol: idx for idx, symbol in enumerate(SIGMA)}
    for pair in pairs:
        src = labels_by_pair[pair]
        dst = labels_by_pair[permute_pair(pair, perm)]
        if src == dst:
            identity_hits += 1
        confusion[symbol_index[src]][symbol_index[dst]] += 1
    mapped_hits, mapping_indices = best_symbol_mapping(confusion)
    mapping = {SIGMA[i]: SIGMA[mapping_indices[i]] for i in range(len(SIGMA))}
    lookup_bits = len(pairs) * math.log2(len(SIGMA))
    perm_bits = math.log2(math.factorial(10))
    symbol_perm_bits = math.log2(math.factorial(len(SIGMA)))
    identity_exception_bits = (len(pairs) - identity_hits) * (math.log2(len(pairs)) + math.log2(len(SIGMA)))
    mapped_exception_bits = (len(pairs) - mapped_hits) * (math.log2(len(pairs)) + math.log2(len(SIGMA)))
    identity_mdl = perm_bits + identity_exception_bits
    mapped_mdl = perm_bits + symbol_perm_bits + mapped_exception_bits
    return {
        "id": row["id"],
        "family": row["family"],
        "perm": list(perm),
        "identity_hits": identity_hits,
        "identity_accuracy": identity_hits / len(pairs),
        "mapped_hits": mapped_hits,
        "mapped_accuracy": mapped_hits / len(pairs),
        "symbol_mapping": mapping,
        "identity_mdl_bits": identity_mdl,
        "mapped_mdl_bits": mapped_mdl,
        "lookup_cost_bits": lookup_bits,
        "identity_mdl_gain_vs_lookup_bits": lookup_bits - identity_mdl,
        "mapped_mdl_gain_vs_lookup_bits": lookup_bits - mapped_mdl,
        "identity_lookup_cost_ratio": identity_mdl / lookup_bits,
        "mapped_lookup_cost_ratio": mapped_mdl / lookup_bits,
    }


def permutation_trace(row: dict, pairs: list[tuple[int, int]], labels_by_pair: dict[tuple[int, int], str]) -> dict:
    rows = []
    for pair in pairs:
        target = permute_pair(pair, tuple(row["perm"]))
        source_symbol = labels_by_pair[pair]
        target_symbol = labels_by_pair[target]
        rows.append(
            {
                "pair": f"{pair[0]}{pair[1]}",
                "target_pair": f"{target[0]}{target[1]}",
                "source_symbol": source_symbol,
                "target_symbol": target_symbol,
                "same_pair": pair == target,
                "symbol_preserved": source_symbol == target_symbol,
            }
        )
    moved = [item for item in rows if not item["same_pair"]]
    mismatches = [item for item in rows if not item["symbol_preserved"]]
    moved_mismatches = [item for item in moved if not item["symbol_preserved"]]
    return {
        "permutation_id": row["id"],
        "moved_pair_count": len(moved),
        "moved_pair_preserved_count": sum(1 for item in moved if item["symbol_preserved"]),
        "mismatch_count": len(mismatches),
        "moved_mismatch_count": len(moved_mismatches),
        "moved_pairs": moved,
        "mismatches": mismatches,
    }


def control(labels: list[str], pairs: list[tuple[int, int]], best_identity: int, best_mapped: int, candidates: list[dict]) -> dict:
    rng = random.Random(RANDOM_SEED + 1)
    identity_scores = []
    mapped_scores = []
    for _ in range(CONTROL_TRIALS):
        shuffled = labels[:]
        rng.shuffle(shuffled)
        labels_by_pair = dict(zip(pairs, shuffled))
        best_i = 0
        best_m = 0
        for cand in candidates:
            if cand["id"] == "identity":
                continue
            row = evaluate_perm(cand, pairs, labels_by_pair)
            best_i = max(best_i, row["identity_hits"])
            best_m = max(best_m, row["mapped_hits"])
        identity_scores.append(best_i)
        mapped_scores.append(best_m)

    def summary(values: list[int], observed: int) -> dict:
        mean = sum(values) / len(values)
        sd = (sum((value - mean) ** 2 for value in values) / (len(values) - 1)) ** 0.5
        return {
            "observed": observed,
            "mean": mean,
            "sd": sd,
            "min": min(values),
            "max": max(values),
            "p_ge_observed": (sum(value >= observed for value in values) + 1) / (len(values) + 1),
        }

    return {
        "trials": CONTROL_TRIALS,
        "identity_hits": summary(identity_scores, best_identity),
        "mapped_hits": summary(mapped_scores, best_mapped),
    }


def verdict(best_identity: dict, best_mapped: dict, ctrl: dict) -> str:
    if (
        best_identity["identity_mdl_gain_vs_lookup_bits"] > 0
        and ctrl["identity_hits"]["p_ge_observed"] <= 0.01
        and best_identity["identity_hits"] >= 45
    ):
        return "candidate_digit_automorphism"
    if (
        best_mapped["mapped_mdl_gain_vs_lookup_bits"] > 0
        and ctrl["mapped_hits"]["p_ge_observed"] <= 0.01
        and best_mapped["mapped_hits"] >= 45
    ):
        return "candidate_digit_symbol_automorphism"
    if ctrl["identity_hits"]["p_ge_observed"] <= 0.05 or ctrl["mapped_hits"]["p_ge_observed"] <= 0.05:
        return "weak_symmetry_signal"
    return "rejected_control"


def main() -> int:
    formula = load_json(FORMULA_JSON)
    pairs = natural_pairs()
    labels_by_pair = {pair: primary_pair_symbol(formula["pair_table"], pair) for pair in pairs}
    labels = [labels_by_pair[pair] for pair in pairs]
    candidates = candidate_permutations()
    rows = [evaluate_perm(cand, pairs, labels_by_pair) for cand in candidates]
    rows.sort(
        key=lambda row: (
            -row["mapped_hits"],
            -row["identity_hits"],
            row["mapped_lookup_cost_ratio"],
            row["family"],
            row["id"],
        )
    )
    identity_row = next(row for row in rows if row["id"] == "identity")
    nontrivial_rows = [row for row in rows if row["id"] != "identity"]
    best_mapped = max(nontrivial_rows, key=lambda row: (row["mapped_hits"], -row["mapped_lookup_cost_ratio"], row["id"]))
    best_identity = max(nontrivial_rows, key=lambda row: (row["identity_hits"], -row["identity_lookup_cost_ratio"], row["id"]))
    ctrl = control(labels, pairs, best_identity["identity_hits"], best_mapped["mapped_hits"], candidates)
    result_verdict = verdict(best_identity, best_mapped, ctrl)
    result = {
        "schema": "digit_symbol_automorphism_results.v1",
        "translation_delta": "NONE",
        "candidate_count": len(candidates),
        "identity_sanity_check": identity_row,
        "best_identity": best_identity,
        "best_identity_trace": permutation_trace(best_identity, pairs, labels_by_pair),
        "best_mapped": best_mapped,
        "best_mapped_trace": permutation_trace(best_mapped, pairs, labels_by_pair),
        "top_rows": nontrivial_rows[:80],
        "control": ctrl,
        "verdict": result_verdict,
    }
    write_json(OUT_JSON, result)

    lines = [
        "# Digit/Symbol Automorphism Search",
        "",
        "Generated by `digit_symbol_automorphism_search.py`.",
        "",
        "This pass tests whether a permutation of digit identities maps the",
        "55-cell pair table to itself, either preserving symbols directly or",
        "through one fixed symbol permutation. It is mechanical only and assigns",
        "no plaintext.",
        "",
        "## Summary",
        "",
        "| Best type | Permutation | Hits | MDL/lookup | Control p | Verdict |",
        "|---|---|---:|---:|---:|---|",
        f"| identity sanity check | `identity` | {identity_row['identity_hits']}/55 | {identity_row['identity_lookup_cost_ratio']:.3f} | n/a | `trivial_not_scored` |",
        f"| identity-symbol | `{best_identity['id']}` | {best_identity['identity_hits']}/55 | {best_identity['identity_lookup_cost_ratio']:.3f} | {ctrl['identity_hits']['p_ge_observed']:.4f} | `{result_verdict}` |",
        f"| mapped-symbol | `{best_mapped['id']}` | {best_mapped['mapped_hits']}/55 | {best_mapped['mapped_lookup_cost_ratio']:.3f} | {ctrl['mapped_hits']['p_ge_observed']:.4f} | `{result_verdict}` |",
        "",
        f"Candidate digit permutations tested: `{len(candidates)}`.",
        "",
        "## Top Rows",
        "",
        "| Permutation | Family | Identity hits | Mapped hits | Mapped MDL/lookup | Symbol mapping preview |",
        "|---|---|---:|---:|---:|---|",
    ]
    for row in nontrivial_rows[:25]:
        preview = " ".join(f"{k}->{v}" for k, v in list(row["symbol_mapping"].items())[:6])
        lines.append(
            f"| `{row['id']}` | `{row['family']}` | {row['identity_hits']}/55 | {row['mapped_hits']}/55 | {row['mapped_lookup_cost_ratio']:.3f} | `{preview}` |"
        )
    identity_trace = result["best_identity_trace"]
    lines.extend(
        [
            "",
            "## Best Identity-Symbol Trace",
            "",
            f"Best non-trivial permutation: `{best_identity['id']}`.",
            "",
            f"It moves `{identity_trace['moved_pair_count']}` unordered pair cells; `{identity_trace['moved_pair_preserved_count']}` of those moved cells keep the same primary symbol. Across all 55 cells it has `{identity_trace['mismatch_count']}` symbol mismatches.",
            "",
            "| Pair | Maps to | Source symbol | Target symbol |",
            "|---|---|---|---|",
        ]
    )
    for item in identity_trace["mismatches"]:
        lines.append(
            f"| `{item['pair']}` | `{item['target_pair']}` | `{item['source_symbol']}` | `{item['target_symbol']}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "A symmetry would be useful only if it is compact, beats shuffled-label",
            "controls, and saves bits versus the pair lookup. This pass keeps weak",
            "symmetry hints in the ledger but does not promote a translation.",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT_JSON.relative_to(HERE)}")
    print(f"wrote {OUT_MD.relative_to(HERE)}")
    print(
        "identity={}/55 mapped={}/55 p_mapped={:.4f} verdict={}".format(
            best_identity["identity_hits"],
            best_mapped["mapped_hits"],
            ctrl["mapped_hits"]["p_ge_observed"],
            result_verdict,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
