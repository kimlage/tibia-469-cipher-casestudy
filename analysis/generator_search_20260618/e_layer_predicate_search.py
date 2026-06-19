#!/usr/bin/env python3
"""E-layer predicate search.

This pass asks a narrower question than the global pair-table formula search:
can the `E` cells be described as a compact mechanical layer or fallback using
small digit-pair predicates, especially after the shared `i>=j` diagonal/zero
signal?

It does not assign plaintext and does not claim to generate the full 469 table.
"""

from __future__ import annotations

import itertools
import json
import math
import random
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FORMULA_JSON = ROOT / "analysis" / "mechanism_model_20260618" / "mechanical_formula_469.json"

OUT_JSON = HERE / "e_layer_predicate_results.json"
OUT_MD = HERE / "e_layer_predicate_report.md"

RANDOM_SEED = 46920260619
CONTROL_TRIALS = 1000
MAX_TERMS = 2


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def pair_cells() -> list[str]:
    return [f"{a}{b}" for a in range(10) for b in range(a, 10)]


CELLS = pair_cells()
CELL_INDEX = {cell: index for index, cell in enumerate(CELLS)}
FULL_MASK = (1 << len(CELLS)) - 1


def pair_symbol(pair_table: dict[str, Any], pair: str) -> str:
    row = pair_table[pair]
    if row["status"] == "pure":
        return row["symbol_if_pure"]
    return "+".join(sorted(row["symbols"]))


def mask_from_cells(cells: Iterable[str]) -> int:
    mask = 0
    for cell in cells:
        mask |= 1 << CELL_INDEX[cell]
    return mask


DIAG_MASK = mask_from_cells(cell for cell in CELLS if cell[0] == cell[1])
OFFDIAG_MASK = FULL_MASK ^ DIAG_MASK


@dataclass(frozen=True)
class Term:
    name: str
    family: str
    mask: int
    cost: float


def add_term(terms: list[Term], name: str, family: str, cost: float, fn) -> None:
    mask = mask_from_cells(cell for cell in CELLS if fn(int(cell[0]), int(cell[1])))
    if mask and mask != FULL_MASK:
        terms.append(Term(name, family, mask, cost))


def term_library() -> list[Term]:
    terms: list[Term] = []
    add_term(terms, "diag", "line", 1.0, lambda a, b: a == b)
    add_term(terms, "anti_diag_9", "line", 1.2, lambda a, b: a + b == 9)
    add_term(terms, "anti_diag_10", "line", 1.2, lambda a, b: a + b == 10)
    add_term(terms, "upper_half_sum_ge_9", "sum_range", 1.8, lambda a, b: a + b >= 9)
    add_term(terms, "lower_half_sum_le_9", "sum_range", 1.8, lambda a, b: a + b <= 9)

    for digit in range(10):
        add_term(terms, f"loop_{digit}", "loop", 1.8, lambda a, b, d=digit: a == d and b == d)
        add_term(terms, f"contains_{digit}", "digit", 2.0, lambda a, b, d=digit: a == d or b == d)
        add_term(terms, f"not_contains_{digit}", "digit", 2.2, lambda a, b, d=digit: a != d and b != d)
    for value in range(19):
        add_term(terms, f"sum_eq_{value}", "sum", 2.0, lambda a, b, v=value: a + b == v)
    for value in range(10):
        add_term(terms, f"diff_eq_{value}", "diff", 1.8, lambda a, b, v=value: b - a == v)
    products = sorted({int(cell[0]) * int(cell[1]) for cell in CELLS})
    for value in products:
        add_term(terms, f"prod_eq_{value}", "product", 2.0, lambda a, b, v=value: a * b == v)
    for lo in products:
        for hi in products:
            if hi < lo:
                continue
            if hi - lo > 14:
                continue
            add_term(terms, f"prod_between_{lo}_{hi}", "product_range", 2.8, lambda a, b, l=lo, h=hi: l <= a * b <= h)

    named_sets = {
        "015": {0, 1, 5},
        "069": {0, 6, 9},
        "169": {1, 6, 9},
        "3478": {3, 4, 7, 8},
        "4578": {4, 5, 7, 8},
        "469": {4, 6, 9},
        "square": {0, 1, 4, 9},
        "zero_eight": {0, 8},
        "three_six": {3, 6},
        "even": {0, 2, 4, 6, 8},
        "odd": {1, 3, 5, 7, 9},
        "prime": {2, 3, 5, 7},
    }
    for name, digits in named_sets.items():
        add_term(terms, f"both_in_{name}", "digit_set", 2.4, lambda a, b, s=digits: a in s and b in s)
        add_term(terms, f"exactly_one_in_{name}", "digit_set", 2.4, lambda a, b, s=digits: (a in s) ^ (b in s))
        add_term(terms, f"contains_any_{name}", "digit_set", 2.2, lambda a, b, s=digits: a in s or b in s)

    for modulus in [2, 3, 4, 5, 6, 10]:
        for residue in range(modulus):
            add_term(
                terms,
                f"sum_mod_{modulus}_{residue}",
                "modular",
                2.4,
                lambda a, b, m=modulus, r=residue: (a + b) % m == r,
            )
            add_term(
                terms,
                f"prod_mod_{modulus}_{residue}",
                "modular",
                2.6,
                lambda a, b, m=modulus, r=residue: (a * b) % m == r,
            )
            add_term(
                terms,
                f"diff_mod_{modulus}_{residue}",
                "modular",
                2.4,
                lambda a, b, m=modulus, r=residue: (b - a) % m == r,
            )

    dedup: dict[int, Term] = {}
    for term in terms:
        old = dedup.get(term.mask)
        if old is None or term.cost < old.cost or (term.cost == old.cost and term.name < old.name):
            dedup[term.mask] = term
    return sorted(dedup.values(), key=lambda term: (term.cost, term.name))


def log2_comb(n: int, k: int) -> float:
    if k < 0 or k > n:
        return float("inf")
    if k == 0 or k == n:
        return 0.0
    return math.log2(math.comb(n, k))


log2_comb = lru_cache(maxsize=None)(log2_comb)


def score_mask(
    mask: int,
    target: int,
    target_count: int,
    universe: int,
    model_cost: float,
    names: list[str],
) -> dict[str, Any]:
    mask &= universe
    universe_count = universe.bit_count()
    tp = (mask & target).bit_count()
    fp = (mask & ~target & universe).bit_count()
    fn = target_count - tp
    tn = universe_count - tp - fp - fn
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / target_count if target_count else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    correction_bits = log2_comb(mask.bit_count(), fp) + log2_comb(universe_count - mask.bit_count(), fn)
    lookup_bits = log2_comb(universe_count, target_count)
    mdl_bits = model_cost + correction_bits
    return {
        "terms": names,
        "mask_hex": hex(mask),
        "universe_count": universe_count,
        "selected_count": mask.bit_count(),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "model_cost_bits": model_cost,
        "correction_bits": correction_bits,
        "lookup_bits": lookup_bits,
        "mdl_bits": mdl_bits,
        "mdl_gain_vs_e_lookup_bits": lookup_bits - mdl_bits,
        "exact": fp == 0 and fn == 0,
    }


def candidate_masks(terms: list[Term], universe: int) -> list[dict[str, Any]]:
    best: dict[int, dict[str, Any]] = {}
    for size in range(1, MAX_TERMS + 1):
        for combo in itertools.combinations(terms, size):
            mask = 0
            cost = math.log2(len(terms) + 1)
            names = []
            for term in combo:
                mask |= term.mask
                cost += term.cost
                names.append(term.name)
            mask &= universe
            if not mask or mask == universe:
                continue
            old = best.get(mask)
            if old is None or cost < old["cost"] or (cost == old["cost"] and names < old["terms"]):
                best[mask] = {"mask": mask, "cost": cost, "terms": names}
    return list(best.values())


def best_for_target(candidates: list[dict[str, Any]], target: int, target_count: int, universe: int) -> dict[str, Any]:
    best: dict[str, Any] | None = None
    best_key: tuple[Any, ...] | None = None
    for row in candidates:
        scored = score_mask(row["mask"], target, target_count, universe, row["cost"], row["terms"])
        key = (
            -scored["mdl_gain_vs_e_lookup_bits"],
            -int(scored["exact"]),
            -scored["f1"],
            scored["model_cost_bits"],
            scored["terms"],
        )
        if best is None or best_key is None or key < best_key:
            best = scored
            best_key = key
    if best is None:
        raise RuntimeError("no candidate masks available")
    return best


def summarize(values: list[float], observed: float) -> dict[str, float]:
    mean = sum(values) / len(values)
    sd = (sum((value - mean) ** 2 for value in values) / (len(values) - 1)) ** 0.5
    return {
        "observed": observed,
        "mean": mean,
        "sd": sd,
        "min": min(values),
        "max": max(values),
        "z_good_direction": (observed - mean) / sd if sd else 0.0,
        "p_good_direction": (sum(value >= observed for value in values) + 1) / (len(values) + 1),
    }


def controls(candidates: list[dict[str, Any]], observed: dict[str, Any], target_count: int, universe: int) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED)
    universe_indexes = [index for index, _cell in enumerate(CELLS) if (universe >> index) & 1]
    mdl_gains = []
    f1s = []
    exacts = []
    for _trial in range(CONTROL_TRIALS):
        indexes = set(rng.sample(universe_indexes, target_count))
        target = sum(1 << index for index in indexes)
        best = best_for_target(candidates, target, target_count, universe)
        mdl_gains.append(best["mdl_gain_vs_e_lookup_bits"])
        f1s.append(best["f1"])
        exacts.append(1.0 if best["exact"] else 0.0)
    return {
        "trials": CONTROL_TRIALS,
        "universe_count": len(universe_indexes),
        "best_mdl_gain": summarize(mdl_gains, observed["mdl_gain_vs_e_lookup_bits"]),
        "best_f1": summarize(f1s, observed["f1"]),
        "exact_fit_rate": summarize(exacts, 1.0 if observed["exact"] else 0.0),
    }


def classify(best: dict[str, Any], ctrl: dict[str, Any]) -> str:
    if best["mdl_gain_vs_e_lookup_bits"] > 0 and ctrl["best_mdl_gain"]["p_good_direction"] <= 0.05:
        if best["exact"]:
            return "candidate_e_layer_formula"
        return "weak_e_layer_signal"
    if best["f1"] >= 0.75:
        return "e_layer_microfit_not_promoted"
    return "rejected_control"


def write_report(result: dict[str, Any]) -> None:
    all_e = result["all_e"]
    residual = result["residual_offdiag_e"]
    all_best = all_e["best"]
    all_ctrl = all_e["controls"]
    residual_best = residual["best"]
    residual_ctrl = residual["controls"]
    lines = [
        "# E-Layer Predicate Search",
        "",
        "Generated by `e_layer_predicate_search.py`.",
        "",
        "This pass tests whether `E` is a compact mechanical layer over the",
        "55 unordered pair cells. It does not assign plaintext or solve the full",
        "pair table.",
        "",
        "## Summary",
        "",
        "| Pass | Terms | TP | FP | FN | F1 | MDL gain vs lookup | Control p(MDL) | Verdict |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|",
        f"| all_E_55 | `{' OR '.join(all_best['terms'])}` | {all_best['tp']} | {all_best['fp']} | {all_best['fn']} | {all_best['f1']:.3f} | {all_best['mdl_gain_vs_e_lookup_bits']:.1f} | {all_ctrl['best_mdl_gain']['p_good_direction']:.5f} | `{all_e['verdict']}` |",
        f"| residual_offdiag_E_45 | `{' OR '.join(residual_best['terms'])}` | {residual_best['tp']} | {residual_best['fp']} | {residual_best['fn']} | {residual_best['f1']:.3f} | {residual_best['mdl_gain_vs_e_lookup_bits']:.1f} | {residual_ctrl['best_mdl_gain']['p_good_direction']:.5f} | `{residual['verdict']}` |",
        "",
        "## E Cells",
        "",
        f"- Target E cells: `{', '.join(result['e_cells'])}`.",
        f"- Diagonal E baseline: `{', '.join(result['diagonal_baseline']['e_diagonal_cells'])}` "
        f"({result['diagonal_baseline']['e_diagonal_count']}/{result['diagonal_baseline']['diagonal_count']}).",
        f"- Residual off-diagonal E cells: `{', '.join(result['residual_e_cells'])}`.",
        f"- All-E selected cells: `{', '.join(all_e['selected_cells'])}`.",
        f"- Residual selected cells: `{', '.join(residual['selected_cells'])}`.",
        "",
        "## Controls",
        "",
        f"- All-E best-MDL control p: `{all_ctrl['best_mdl_gain']['p_good_direction']:.5f}`.",
        f"- All-E best-F1 control p: `{all_ctrl['best_f1']['p_good_direction']:.5f}`.",
        f"- All-E exact-fit control p: `{all_ctrl['exact_fit_rate']['p_good_direction']:.5f}`.",
        f"- Residual best-MDL control p: `{residual_ctrl['best_mdl_gain']['p_good_direction']:.5f}`.",
        f"- Residual best-F1 control p: `{residual_ctrl['best_f1']['p_good_direction']:.5f}`.",
        f"- Residual exact-fit control p: `{residual_ctrl['exact_fit_rate']['p_good_direction']:.5f}`.",
        "",
        "## Interpretation",
        "",
        "The all-E pass asks whether any binary E inventory predicate beats an",
        "E-specific lookup. The residual pass is stricter: it removes diagonal",
        "cells and asks whether the six off-diagonal E cells are still explained",
        "after the already-known diagonal/`i>=j` pressure is spent.",
        "",
        f"Translation delta: `{result['translation_delta']}`.",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    formula = load_json(FORMULA_JSON)
    e_cells = sorted(pair for pair in CELLS if pair_symbol(formula["pair_table"], pair) == "E")
    residual_e_cells = [cell for cell in e_cells if cell[0] != cell[1]]
    terms = term_library()
    all_candidates = candidate_masks(terms, FULL_MASK)
    residual_candidates = candidate_masks(terms, OFFDIAG_MASK)

    all_target = mask_from_cells(e_cells)
    all_best = best_for_target(all_candidates, all_target, len(e_cells), FULL_MASK)
    all_ctrl = controls(all_candidates, all_best, len(e_cells), FULL_MASK)
    all_selected = [cell for cell in CELLS if (int(all_best["mask_hex"], 16) >> CELL_INDEX[cell]) & 1]

    residual_target = mask_from_cells(residual_e_cells)
    residual_best = best_for_target(residual_candidates, residual_target, len(residual_e_cells), OFFDIAG_MASK)
    residual_ctrl = controls(residual_candidates, residual_best, len(residual_e_cells), OFFDIAG_MASK)
    residual_selected = [
        cell for cell in CELLS if (int(residual_best["mask_hex"], 16) >> CELL_INDEX[cell]) & 1
    ]
    residual_verdict = classify(residual_best, residual_ctrl)
    result = {
        "schema": "e_layer_predicate_results.v1",
        "source": str(FORMULA_JSON.relative_to(ROOT)),
        "term_count": len(terms),
        "all_candidate_count": len(all_candidates),
        "residual_candidate_count": len(residual_candidates),
        "max_terms": MAX_TERMS,
        "e_cells": e_cells,
        "residual_e_cells": residual_e_cells,
        "diagonal_baseline": {
            "diagonal_cells": [cell for cell in CELLS if cell[0] == cell[1]],
            "e_diagonal_cells": [cell for cell in e_cells if cell[0] == cell[1]],
            "e_diagonal_count": len([cell for cell in e_cells if cell[0] == cell[1]]),
            "diagonal_count": DIAG_MASK.bit_count(),
        },
        "all_e": {
            "selected_cells": all_selected,
            "best": all_best,
            "controls": all_ctrl,
            "verdict": classify(all_best, all_ctrl),
        },
        "residual_offdiag_e": {
            "selected_cells": residual_selected,
            "best": residual_best,
            "controls": residual_ctrl,
            "verdict": residual_verdict,
        },
        "best": residual_best,
        "controls": residual_ctrl,
        "verdict": residual_verdict,
        "translation_delta": "NONE",
        "new_plaintext": False,
    }
    write_json(OUT_JSON, result)
    write_report(result)
    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(
        "best={terms} f1={f1:.3f} gain={gain:.1f} p={p:.5f} verdict={verdict}".format(
            terms=" OR ".join(residual_best["terms"]),
            f1=residual_best["f1"],
            gain=residual_best["mdl_gain_vs_e_lookup_bits"],
            p=residual_ctrl["best_mdl_gain"]["p_good_direction"],
            verdict=result["verdict"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
