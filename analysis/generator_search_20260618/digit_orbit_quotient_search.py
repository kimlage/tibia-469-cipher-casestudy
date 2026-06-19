#!/usr/bin/env python3
"""Digit-orbit quotient search for the 469 pair table.

This pass follows up the weak `6 <-> 9` automorphism signal. Instead of asking
whether a permutation preserves every cell directly, it asks whether quotienting
the 55 unordered pair cells by a small digit-transformation group yields a
shorter generator: one label per orbit plus explicit exceptions.

Mechanical only. No plaintext or translation is promoted.
"""

from __future__ import annotations

import itertools
import json
import math
import random
from collections import Counter
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FORMULA_JSON = ROOT / "analysis" / "mechanism_model_20260618" / "mechanical_formula_469.json"

OUT_JSON = HERE / "digit_orbit_quotient_results.json"
OUT_MD = HERE / "digit_orbit_quotient_report.md"

SIGMA = list("*ABCEFILNORSTV")
RANDOM_SEED = 46920260619
CONTROL_TRIALS = 200
TOP_COMBO_GENERATORS = [
    "swap_6_9",
    "swap_3_9",
    "swap_7_8",
    "swap_2_4",
    "swap_2_3",
    "swap_3_4",
    "swap_4_5",
    "swap_1_9",
    "swap_3_6",
    "swap_0_5",
]


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def natural_pairs() -> list[tuple[int, int]]:
    return [(a, b) for a in range(10) for b in range(a, 10)]


def pair_key(pair: tuple[int, int]) -> str:
    return f"{pair[0]}{pair[1]}"


def primary_pair_symbol(pair_table: dict, pair: tuple[int, int]) -> str:
    row = pair_table[pair_key(pair)]
    if row["status"] == "pure":
        return row["symbol_if_pure"]
    return sorted(row["symbols"])[0]


def acceptable_pair_symbols(pair_table: dict, pair: tuple[int, int]) -> set[str]:
    return set(pair_table[pair_key(pair)]["symbols"])


def permute_pair(pair: tuple[int, int], perm: tuple[int, ...]) -> tuple[int, int]:
    a, b = perm[pair[0]], perm[pair[1]]
    return (a, b) if a <= b else (b, a)


def compose(left: tuple[int, ...], right: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(left[right[d]] for d in range(10))


def transposition(i: int, j: int) -> tuple[int, ...]:
    perm = list(range(10))
    perm[i], perm[j] = perm[j], perm[i]
    return tuple(perm)


def named_generators() -> dict[str, tuple[int, ...]]:
    rows = {
        "reverse_9_minus_d": tuple(9 - d for d in range(10)),
        "decimal_shift_1": tuple((d + 1) % 10 for d in range(10)),
        "decimal_shift_4": tuple((d + 4) % 10 for d in range(10)),
        "decimal_shift_6": tuple((d + 6) % 10 for d in range(10)),
        "affine_3d_plus_1": tuple((3 * d + 1) % 10 for d in range(10)),
        "affine_7d_plus_4": tuple((7 * d + 4) % 10 for d in range(10)),
    }
    for i in range(10):
        for j in range(i + 1, 10):
            rows[f"swap_{i}_{j}"] = transposition(i, j)
    return rows


def closure(generators: list[tuple[int, ...]], max_size: int = 720) -> list[tuple[int, ...]]:
    identity = tuple(range(10))
    seen = {identity}
    frontier = [identity]
    while frontier:
        current = frontier.pop()
        for generator in generators:
            for candidate in (compose(generator, current), compose(current, generator)):
                if candidate not in seen:
                    seen.add(candidate)
                    frontier.append(candidate)
                    if len(seen) > max_size:
                        return sorted(seen)
    return sorted(seen)


def candidate_groups() -> list[dict]:
    generators = named_generators()
    rows = [{"id": "identity", "family": "identity", "generator_ids": [], "generators": []}]
    for name, perm in generators.items():
        rows.append(
            {
                "id": name,
                "family": "single_generator",
                "generator_ids": [name],
                "generators": [perm],
            }
        )
    for size in [2, 3]:
        for combo in itertools.combinations(TOP_COMBO_GENERATORS, size):
            rows.append(
                {
                    "id": "combo_" + "__".join(combo),
                    "family": f"{size}_generator_combo",
                    "generator_ids": list(combo),
                    "generators": [generators[name] for name in combo],
                }
            )
    # Lore-shaped groups that directly combine known anomalies.
    lore_combos = [
        ("lore_469_swap_6_9_plus_4_9", ["swap_6_9", "swap_4_9"]),
        ("lore_conflict_1_9_plus_6_9", ["swap_1_9", "swap_6_9"]),
        ("missing_39_plus_6_9", ["swap_3_9", "swap_6_9"]),
        ("tape_edge_3_6_plus_6_9", ["swap_3_6", "swap_6_9"]),
        ("mirror_7_8_plus_6_9", ["swap_7_8", "swap_6_9"]),
    ]
    for cid, names in lore_combos:
        rows.append(
            {
                "id": cid,
                "family": "lore_anomaly_combo",
                "generator_ids": names,
                "generators": [generators[name] for name in names],
            }
        )
    dedup = {}
    for row in rows:
        group = tuple(closure(row["generators"]))
        dedup.setdefault(group, {**row, "group": list(group)})
    return list(dedup.values())


def orbit_partition(pairs: list[tuple[int, int]], group: list[tuple[int, ...]]) -> list[list[tuple[int, int]]]:
    remaining = set(pairs)
    orbits = []
    while remaining:
        seed = min(remaining)
        orbit = {permute_pair(seed, perm) for perm in group}
        changed = True
        while changed:
            changed = False
            for pair in list(orbit):
                for perm in group:
                    nxt = permute_pair(pair, perm)
                    if nxt not in orbit:
                        orbit.add(nxt)
                        changed = True
        sorted_orbit = sorted(orbit)
        orbits.append(sorted_orbit)
        remaining -= orbit
    return sorted(orbits, key=lambda items: (len(items), pair_key(items[0])))


def log2_comb(n: int, k: int) -> float:
    if k < 0 or k > n:
        return float("inf")
    return math.log2(math.comb(n, k)) if 0 < k < n else 0.0


def evaluate_group(row: dict, pairs: list[tuple[int, int]], labels: dict[tuple[int, int], str], acceptables: dict[tuple[int, int], set[str]]) -> dict:
    group = [tuple(perm) for perm in row["group"]]
    orbits = orbit_partition(pairs, group)
    predictions: dict[tuple[int, int], str] = {}
    orbit_rows = []
    primary_hits = 0
    acceptable_hits = 0
    exceptions = []
    mixed_orbits = []
    split_label_count = 0
    for orbit_index, orbit in enumerate(orbits):
        counts = Counter(labels[pair] for pair in orbit)
        label, count = sorted(counts.items(), key=lambda item: (-item[1], SIGMA.index(item[0])))[0]
        is_mixed = len(counts) > 1
        split_label_count += len(orbit) if is_mixed else 1
        if is_mixed:
            mixed_orbits.append(orbit_index)
        for pair in orbit:
            predictions[pair] = label
            if labels[pair] == label:
                primary_hits += 1
            else:
                exceptions.append(
                    {
                        "pair": pair_key(pair),
                        "orbit": orbit_index,
                        "predicted": label,
                        "actual": labels[pair],
                    }
                )
            if label in acceptables[pair]:
                acceptable_hits += 1
        orbit_rows.append(
            {
                "orbit": orbit_index,
                "size": len(orbit),
                "pairs": [pair_key(pair) for pair in orbit],
                "label": label,
                "is_mixed": is_mixed,
                "label_counts": dict(sorted(counts.items())),
            }
        )

    lookup_bits = len(pairs) * math.log2(len(SIGMA))
    group_bits = max(0.0, len(row["generator_ids"]) * math.log2(45) + math.log2(8))
    orbit_label_bits = len(orbits) * math.log2(len(SIGMA))
    exception_bits = len(exceptions) * (math.log2(len(pairs)) + math.log2(len(SIGMA)))
    mdl_bits = group_bits + orbit_label_bits + exception_bits
    non_singleton_orbits = sum(1 for orbit in orbits if len(orbit) > 1)
    mixed_selector_bits = log2_comb(non_singleton_orbits, len(mixed_orbits))
    split_lossless_bits = group_bits + split_label_count * math.log2(len(SIGMA)) + mixed_selector_bits
    return {
        "id": row["id"],
        "family": row["family"],
        "generator_ids": row["generator_ids"],
        "group_size": len(group),
        "orbit_count": len(orbits),
        "non_singleton_orbits": non_singleton_orbits,
        "mixed_orbit_count": len(mixed_orbits),
        "mixed_orbits": mixed_orbits,
        "largest_orbit": max(len(orbit) for orbit in orbits),
        "primary_hits": primary_hits,
        "acceptable_hits": acceptable_hits,
        "primary_accuracy": primary_hits / len(pairs),
        "acceptable_accuracy": acceptable_hits / len(pairs),
        "exception_count": len(exceptions),
        "exceptions": exceptions,
        "orbits": orbit_rows,
        "mdl_bits": mdl_bits,
        "lookup_cost_bits": lookup_bits,
        "mdl_gain_vs_lookup_bits": lookup_bits - mdl_bits,
        "lookup_cost_ratio": mdl_bits / lookup_bits,
        "split_lossless_bits": split_lossless_bits,
        "split_label_count": split_label_count,
        "split_mixed_selector_bits": mixed_selector_bits,
        "split_mdl_gain_vs_lookup_bits": lookup_bits - split_lossless_bits,
        "split_lookup_cost_ratio": split_lossless_bits / lookup_bits,
    }


def control(
    observed_best_hits: int,
    observed_best_mdl_gain: float,
    observed_best_split_gain: float,
    candidates: list[dict],
    pairs: list[tuple[int, int]],
    labels_list: list[str],
    acceptables: dict[tuple[int, int], set[str]],
) -> dict:
    rng = random.Random(RANDOM_SEED + 1)
    best_hits = []
    best_mdl = []
    best_split = []
    for _ in range(CONTROL_TRIALS):
        shuffled = labels_list[:]
        rng.shuffle(shuffled)
        labels = dict(zip(pairs, shuffled))
        # For controls, acceptable conflict is not meaningful; primary labels are the target.
        ctrl_acceptables = {pair: {labels[pair]} for pair in pairs}
        rows = [evaluate_group(cand, pairs, labels, ctrl_acceptables) for cand in candidates if cand["id"] != "identity"]
        best_hits.append(max(row["primary_hits"] for row in rows))
        best_mdl.append(max(row["mdl_gain_vs_lookup_bits"] for row in rows))
        best_split.append(max(row["split_mdl_gain_vs_lookup_bits"] for row in rows))

    def summarize(values: list[float], observed: float, higher_is_better: bool = True) -> dict:
        mean = sum(values) / len(values)
        sd = (sum((value - mean) ** 2 for value in values) / (len(values) - 1)) ** 0.5
        if higher_is_better:
            p = (sum(value >= observed for value in values) + 1) / (len(values) + 1)
            z = (observed - mean) / sd if sd else 0.0
        else:
            p = (sum(value <= observed for value in values) + 1) / (len(values) + 1)
            z = (mean - observed) / sd if sd else 0.0
        return {
            "observed": observed,
            "mean": mean,
            "sd": sd,
            "min": min(values),
            "max": max(values),
            "p_good_direction": p,
            "z_good_direction": z,
        }

    return {
        "trials": CONTROL_TRIALS,
        "best_primary_hits": summarize(best_hits, observed_best_hits),
        "best_mdl_gain_bits": summarize(best_mdl, observed_best_mdl_gain),
        "best_split_mdl_gain_bits": summarize(best_split, observed_best_split_gain),
    }


def verdict(best: dict, best_by_split: dict, ctrl: dict) -> str:
    if (
        best_by_split["split_mdl_gain_vs_lookup_bits"] > 0
        and best_by_split["primary_hits"] == 55
        and ctrl["best_split_mdl_gain_bits"]["p_good_direction"] <= 0.01
    ):
        return "candidate_lossless_digit_orbit_formula"
    if (
        best_by_split["split_mdl_gain_vs_lookup_bits"] > 0
        and ctrl["best_split_mdl_gain_bits"]["p_good_direction"] <= 0.05
    ):
        return "weak_lossless_orbit_compression"
    if best["mdl_gain_vs_lookup_bits"] > 0 and best["exception_count"] == 0 and ctrl["best_mdl_gain_bits"]["p_good_direction"] <= 0.01:
        return "candidate_digit_orbit_formula"
    if best["primary_hits"] >= 50 and ctrl["best_primary_hits"]["p_good_direction"] <= 0.05:
        if best["mdl_gain_vs_lookup_bits"] <= 0:
            return "weak_orbit_signal_not_compressed"
        return "weak_orbit_signal"
    if best["lookup_cost_ratio"] >= 1.0:
        return "lookup_disguise"
    return "rejected_control"


def write_report(result: dict) -> None:
    best = result["best"]
    best_by_split = result["best_by_split_mdl_gain"]
    swap = result["swap_6_9"]
    ctrl = result["control"]
    lines = [
        "# Digit Orbit Quotient Search",
        "",
        "Generated by `digit_orbit_quotient_search.py`.",
        "",
        "This pass tests whether digit transformations can quotient the 55-cell",
        "pair table into fewer orbits, with one symbol per orbit plus explicit",
        "exceptions. It is mechanical only and assigns no plaintext.",
        "",
        "## Summary",
        "",
        "| Best by hits | Orbits | Group size | Hits | Exceptions | Exception MDL/lookup | Split MDL/lookup | Control p(hit) | Control p(split MDL) | Verdict |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
        f"| `{best['id']}` | {best['orbit_count']} | {best['group_size']} | {best['primary_hits']}/55 | {best['exception_count']} | {best['lookup_cost_ratio']:.3f} | {best['split_lookup_cost_ratio']:.3f} | {ctrl['best_primary_hits']['p_good_direction']:.4f} | {ctrl['best_split_mdl_gain_bits']['p_good_direction']:.4f} | `{result['verdict']}` |",
        "",
        f"Best by split-lossless MDL: `{best_by_split['id']}` with gain `{best_by_split['split_mdl_gain_vs_lookup_bits']:.1f}` bits and split MDL/lookup `{best_by_split['split_lookup_cost_ratio']:.3f}`.",
        "",
        "## Focus: `swap_6_9`",
        "",
        f"`swap_6_9` yields `{swap['orbit_count']}` orbits and `{swap['exception_count']}` exceptions after choosing one majority label per orbit. Under the split-lossless model it stores `{swap['split_label_count']}` labels, marks `{swap['mixed_orbit_count']}` mixed non-singleton orbits, and has MDL/lookup `{swap['split_lookup_cost_ratio']:.3f}`.",
        "",
        "| Pair | Orbit | Predicted orbit label | Actual symbol |",
        "|---|---:|---|---|",
    ]
    for item in swap["exceptions"]:
        lines.append(f"| `{item['pair']}` | {item['orbit']} | `{item['predicted']}` | `{item['actual']}` |")
    lines.extend(
        [
            "",
            "## Top Rows",
            "",
            "| Group | Family | Orbits | Group size | Hits | Exceptions | Exception MDL/lookup | Split MDL/lookup | Split gain bits |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in result["top_rows"][:30]:
        lines.append(
            f"| `{row['id']}` | `{row['family']}` | {row['orbit_count']} | {row['group_size']} | {row['primary_hits']}/55 | {row['exception_count']} | {row['lookup_cost_ratio']:.3f} | {row['split_lookup_cost_ratio']:.3f} | {row['split_mdl_gain_vs_lookup_bits']:.1f} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The quotient view sharpens the automorphism clue: `6` and `9` can be",
            "treated as an orbit with only four mixed two-cell orbits. The",
            "split-lossless accounting is slightly below raw pair lookup, but",
            "the gain is small and broad group-search controls still make this",
            "a weak clue rather than the recovered original generator.",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    formula = load_json(FORMULA_JSON)
    pairs = natural_pairs()
    labels = {pair: primary_pair_symbol(formula["pair_table"], pair) for pair in pairs}
    acceptables = {pair: acceptable_pair_symbols(formula["pair_table"], pair) for pair in pairs}
    candidates = candidate_groups()
    rows = [evaluate_group(row, pairs, labels, acceptables) for row in candidates]
    rows.sort(
        key=lambda row: (
            -row["primary_hits"],
            row["lookup_cost_ratio"],
            row["group_size"],
            row["id"],
        )
    )
    nontrivial = [row for row in rows if row["id"] != "identity"]
    best = nontrivial[0]
    best_by_mdl = max(nontrivial, key=lambda row: (row["mdl_gain_vs_lookup_bits"], row["primary_hits"], -row["group_size"]))
    best_by_split = max(nontrivial, key=lambda row: (row["split_mdl_gain_vs_lookup_bits"], row["primary_hits"], -row["group_size"]))
    swap_6_9 = next(row for row in nontrivial if row["id"] == "swap_6_9")
    ctrl = control(
        best["primary_hits"],
        best_by_mdl["mdl_gain_vs_lookup_bits"],
        best_by_split["split_mdl_gain_vs_lookup_bits"],
        candidates,
        pairs,
        [labels[pair] for pair in pairs],
        acceptables,
    )
    result = {
        "schema": "digit_orbit_quotient_results.v1",
        "translation_delta": "NONE",
        "candidate_count": len(candidates),
        "best": best,
        "best_by_mdl_gain": best_by_mdl,
        "best_by_split_mdl_gain": best_by_split,
        "swap_6_9": swap_6_9,
        "top_rows": nontrivial[:80],
        "control": ctrl,
        "verdict": verdict(best, best_by_split, ctrl),
    }
    write_json(OUT_JSON, result)
    write_report(result)
    print(f"wrote {OUT_JSON.relative_to(HERE)}")
    print(f"wrote {OUT_MD.relative_to(HERE)}")
    print(
        "best={id} hits={hits}/55 exceptions={exc} split_ratio={ratio:.3f} verdict={verdict}".format(
            id=best["id"],
            hits=best["primary_hits"],
            exc=best["exception_count"],
            ratio=best["split_lookup_cost_ratio"],
            verdict=result["verdict"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
