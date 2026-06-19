#!/usr/bin/env python3
"""Directed surface analysis for the ordered 00..99 469 code table.

This pass treats the compiled mechanical formula as the source of truth and
asks a narrow question: is the ordered table itself a new matrix formula, or is
the lower triangle mostly a rendering/orientation layer copied from the upper
triangle?

Mechanical only. No plaintext, glossary, or translation claim is introduced.
"""

from __future__ import annotations

import json
import random
from collections import Counter
from pathlib import Path
from statistics import mean, pstdev
from typing import Callable


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FORMULA_JSON = ROOT / "analysis" / "mechanism_model_20260618" / "mechanical_formula_469.json"

OUT_JSON = HERE / "directed_pair_surface_results.json"
OUT_MD = HERE / "directed_pair_surface_report.md"

RANDOM_SEED = 46920260619
CONTROL_TRIALS = 20000


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def all_ordered_codes() -> list[str]:
    return [f"{row}{col}" for row in range(10) for col in range(10)]


def upper_codes() -> list[str]:
    return [f"{row}{col}" for row in range(10) for col in range(row, 10)]


def lower_codes() -> list[str]:
    return [f"{row}{col}" for row in range(10) for col in range(row)]


def unordered_pairs() -> list[str]:
    return [f"{row}{col}" for row in range(10) for col in range(row, 10)]


def pair_key(code: str) -> str:
    return "".join(sorted(code))


def reverse_code(code: str) -> str:
    return code[::-1]


def inventory(codes: list[str], code_to_symbol: dict[str, str], symbols: list[str]) -> dict[str, int]:
    counts = Counter(code_to_symbol[code] for code in codes if code in code_to_symbol)
    return {symbol: counts.get(symbol, 0) for symbol in symbols}


def present(codes: list[str], code_to_symbol: dict[str, str]) -> list[str]:
    return [code for code in codes if code in code_to_symbol]


def missing(codes: list[str], code_to_symbol: dict[str, str]) -> list[str]:
    return [code for code in codes if code not in code_to_symbol]


def pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def evaluate(
    name: str,
    model_type: str,
    target_codes: list[str],
    code_to_symbol: dict[str, str],
    predict: Callable[[str], str | set[str] | None],
    parameters: dict,
    notes: list[str],
) -> dict:
    correct = 0
    predicted = 0
    errors = []
    uncovered = []
    set_valued = False
    for code in target_codes:
        actual = code_to_symbol[code]
        expected = predict(code)
        if expected is None:
            uncovered.append({"code": code, "actual": actual})
            continue
        predicted += 1
        if isinstance(expected, set):
            set_valued = True
            ok = actual in expected
            rendered = sorted(expected)
        else:
            ok = actual == expected
            rendered = expected
        if ok:
            correct += 1
        else:
            errors.append({"code": code, "actual": actual, "predicted": rendered})

    total = len(target_codes)
    return {
        "name": name,
        "model_type": model_type,
        "target": {
            "codes": "present ordered codes" if total == len(code_to_symbol) else "present lower-triangle codes",
            "total": total,
        },
        "parameters": parameters,
        "set_valued": set_valued,
        "coverage": predicted / total if total else 0.0,
        "covered_accuracy": correct / predicted if predicted else 0.0,
        "strict_accuracy": correct / total if total else 0.0,
        "correct": correct,
        "predicted": predicted,
        "total": total,
        "uncovered_count": len(uncovered),
        "error_count": len(errors),
        "uncovered": uncovered,
        "errors": errors,
        "notes": notes,
    }


def summarize_control(scores: list[int], observed: int) -> dict:
    sorted_scores = sorted(scores)

    def quantile(q: float) -> int:
        if not sorted_scores:
            return 0
        idx = min(len(sorted_scores) - 1, max(0, round(q * (len(sorted_scores) - 1))))
        return sorted_scores[idx]

    return {
        "observed": observed,
        "trials": len(scores),
        "control_mean": mean(scores),
        "control_sd_population": pstdev(scores),
        "control_min": min(scores),
        "control_p50": quantile(0.50),
        "control_p95": quantile(0.95),
        "control_p99": quantile(0.99),
        "control_max": max(scores),
        "p_value_ge_observed": (sum(score >= observed for score in scores) + 1) / (len(scores) + 1),
    }


def lower_inventory_shuffle_control(
    code_to_symbol: dict[str, str],
    reverse_available_lower: list[str],
    rng: random.Random,
) -> dict:
    upper_labels = [code_to_symbol[reverse_code(code)] for code in reverse_available_lower]
    lower_labels = [code_to_symbol[code] for code in reverse_available_lower]
    observed = sum(left == right for left, right in zip(upper_labels, lower_labels))
    scores = []
    shuffled = lower_labels[:]
    for _ in range(CONTROL_TRIALS):
        rng.shuffle(shuffled)
        scores.append(sum(left == right for left, right in zip(upper_labels, shuffled)))
    out = summarize_control(scores, observed)
    out.update(
        {
            "null": "shuffle labels across reverse-available lower-triangle positions, preserving lower inventory",
            "evaluated_positions": len(reverse_available_lower),
        }
    )
    return out


def ordered_inventory_shuffle_control(
    code_to_symbol: dict[str, str],
    reverse_available_pairs: list[tuple[str, str]],
    rng: random.Random,
) -> dict:
    codes = sorted(code_to_symbol)
    labels = [code_to_symbol[code] for code in codes]
    observed = sum(code_to_symbol[upper] == code_to_symbol[lower] for upper, lower in reverse_available_pairs)
    scores = []
    shuffled = labels[:]
    for _ in range(CONTROL_TRIALS):
        rng.shuffle(shuffled)
        table = dict(zip(codes, shuffled))
        scores.append(sum(table[upper] == table[lower] for upper, lower in reverse_available_pairs))
    out = summarize_control(scores, observed)
    out.update(
        {
            "null": "shuffle labels across all present ordered 00..99 codes, preserving global ordered inventory",
            "evaluated_pairs": len(reverse_available_pairs),
        }
    )
    return out


def best_symbol_permutation(
    observations: list[tuple[str, str]],
    symbols: list[str],
) -> dict:
    index = {symbol: pos for pos, symbol in enumerate(symbols)}
    weights = [[0 for _ in symbols] for _ in symbols]
    for upper_symbol, lower_symbol in observations:
        weights[index[upper_symbol]][index[lower_symbol]] += 1

    # Dynamic programming over a 14-symbol assignment is small and avoids
    # optional dependencies. The secondary score prefers identity ties.
    dp: dict[int, tuple[int, int, list[int]]] = {0: (0, 0, [])}
    for upper_idx in range(len(symbols)):
        next_dp: dict[int, tuple[int, int, list[int]]] = {}
        for mask, (score, identity_score, path) in dp.items():
            for lower_idx in range(len(symbols)):
                bit = 1 << lower_idx
                if mask & bit:
                    continue
                candidate = (
                    score + weights[upper_idx][lower_idx],
                    identity_score + int(upper_idx == lower_idx),
                    path + [lower_idx],
                )
                current = next_dp.get(mask | bit)
                if current is None or candidate[:2] > current[:2]:
                    next_dp[mask | bit] = candidate
        dp = next_dp

    full_mask = (1 << len(symbols)) - 1
    score, identity_score, path = dp[full_mask]
    mapping = {symbols[upper_idx]: symbols[lower_idx] for upper_idx, lower_idx in enumerate(path)}
    identity_score_observed = sum(upper == lower for upper, lower in observations)
    return {
        "best_score": score,
        "identity_score": identity_score_observed,
        "identity_tie_symbols": identity_score,
        "mapping": mapping,
        "confusion": {
            upper: {lower: weights[index[upper]][index[lower]] for lower in symbols if weights[index[upper]][index[lower]]}
            for upper in symbols
            if any(weights[index[upper]])
        },
    }


def build_unordered_single_lookup(code_to_symbol: dict[str, str]) -> dict[str, str]:
    lookup = {}
    for pair in unordered_pairs():
        upper = pair
        lower = reverse_code(pair)
        if upper in code_to_symbol:
            lookup[pair] = code_to_symbol[upper]
        elif lower in code_to_symbol:
            lookup[pair] = code_to_symbol[lower]
    return lookup


def build_unordered_set_lookup(code_to_symbol: dict[str, str]) -> dict[str, set[str]]:
    lookup = {}
    for pair in unordered_pairs():
        symbols = set()
        upper = pair
        lower = reverse_code(pair)
        if upper in code_to_symbol:
            symbols.add(code_to_symbol[upper])
        if lower in code_to_symbol:
            symbols.add(code_to_symbol[lower])
        if symbols:
            lookup[pair] = symbols
    return lookup


def main() -> None:
    formula = load_json(FORMULA_JSON)
    code_to_symbol: dict[str, str] = dict(sorted(formula["code_to_symbol"].items()))
    symbols = list(formula["formula"]["internal_alphabet"])

    ordered = all_ordered_codes()
    upper = upper_codes()
    lower = lower_codes()
    present_ordered = present(ordered, code_to_symbol)
    present_upper = present(upper, code_to_symbol)
    present_lower = present(lower, code_to_symbol)
    missing_ordered = missing(ordered, code_to_symbol)
    missing_upper = missing(upper, code_to_symbol)
    missing_lower = missing(lower, code_to_symbol)

    reverse_available_pairs = []
    reverse_conflicts = []
    reverse_same_pairs = []
    reverse_missing = []
    for row in range(10):
        for col in range(row + 1, 10):
            upper_code = f"{row}{col}"
            lower_code = f"{col}{row}"
            upper_present = upper_code in code_to_symbol
            lower_present = lower_code in code_to_symbol
            if upper_present and lower_present:
                reverse_available_pairs.append((upper_code, lower_code))
                if code_to_symbol[upper_code] == code_to_symbol[lower_code]:
                    reverse_same_pairs.append((upper_code, lower_code))
                else:
                    reverse_conflicts.append(
                        {
                            "upper_code": upper_code,
                            "upper_symbol": code_to_symbol[upper_code],
                            "lower_code": lower_code,
                            "lower_symbol": code_to_symbol[lower_code],
                        }
                    )
            elif lower_present or upper_present:
                reverse_missing.append(
                    {
                        "upper_code": upper_code,
                        "upper_present": upper_present,
                        "upper_symbol": code_to_symbol.get(upper_code),
                        "lower_code": lower_code,
                        "lower_present": lower_present,
                        "lower_symbol": code_to_symbol.get(lower_code),
                    }
                )

    present_non_diagonal = [code for code in present_ordered if code[0] != code[1]]
    reverse_available_codes = [code for code in present_non_diagonal if reverse_code(code) in code_to_symbol]
    reverse_preserving_codes = [
        code for code in reverse_available_codes if code_to_symbol[code] == code_to_symbol[reverse_code(code)]
    ]
    reverse_conflict_codes = [
        code for code in reverse_available_codes if code_to_symbol[code] != code_to_symbol[reverse_code(code)]
    ]

    reverse_available_lower = [lower_code for _, lower_code in reverse_available_pairs]
    lower_orphans = [
        code
        for code in present_lower
        if reverse_code(code) not in code_to_symbol
    ]

    unordered_single_lookup = build_unordered_single_lookup(code_to_symbol)
    unordered_set_lookup = build_unordered_set_lookup(code_to_symbol)

    def predict_ordered_lookup(code: str) -> str | None:
        return code_to_symbol.get(code)

    def predict_unordered_single(code: str) -> str | None:
        return unordered_single_lookup.get(pair_key(code))

    def predict_unordered_set(code: str) -> set[str] | None:
        return unordered_set_lookup.get(pair_key(code))

    def predict_mirror_base_lower(code: str) -> str | None:
        return code_to_symbol.get(reverse_code(code))

    def predict_mirror_exception_91_lower(code: str) -> str | None:
        if code == "91":
            return code_to_symbol[code]
        return predict_mirror_base_lower(code)

    lower_orphan_metadata = {code: code_to_symbol[code] for code in lower_orphans}

    def predict_mirror_exception_missing_lower(code: str) -> str | None:
        if code == "91":
            return code_to_symbol[code]
        if code in lower_orphan_metadata:
            return lower_orphan_metadata[code]
        return predict_mirror_base_lower(code)

    def lift_upper_plus_lower(lower_predict: Callable[[str], str | None]) -> Callable[[str], str | None]:
        def predict(code: str) -> str | None:
            if code[0] <= code[1]:
                return code_to_symbol.get(code)
            return lower_predict(code)

        return predict

    permutation_observations = [
        (code_to_symbol[upper_code], code_to_symbol[lower_code])
        for upper_code, lower_code in reverse_available_pairs
    ]
    permutation = best_symbol_permutation(permutation_observations, symbols)
    permutation_mapping = permutation["mapping"]

    def predict_symbol_permutation_lower(code: str) -> str | None:
        reverse = reverse_code(code)
        if reverse not in code_to_symbol:
            return None
        return permutation_mapping[code_to_symbol[reverse]]

    lower_models = [
        evaluate(
            "mirror_copy_lower_surface",
            "render_orientation_layer",
            present_lower,
            code_to_symbol,
            predict_mirror_base_lower,
            {
                "stored_surface": "upper triangle including diagonal",
                "stored_upper_entries": len(present_upper),
                "rule": "lower(ab) = upper(ba) when upper counterpart is present",
            },
            [
                "Tests only whether lower-triangle rendering is a transpose of the upper surface.",
                "It does not derive the upper/unordered symbols.",
            ],
        ),
        evaluate(
            "mirror_copy_plus_exception_91",
            "render_orientation_layer_plus_one_exception",
            present_lower,
            code_to_symbol,
            predict_mirror_exception_91_lower,
            {
                "stored_surface": "upper triangle including diagonal",
                "stored_upper_entries": len(present_upper),
                "explicit_exceptions": {"91": code_to_symbol["91"]},
            },
            [
                "Adds the observed 19/91 conflict as one directed lower-surface exception.",
                "Still leaves the 93 lower orphan uncovered because 39 is absent.",
            ],
        ),
        evaluate(
            "mirror_copy_plus_exception_and_missing_39_metadata",
            "render_orientation_layer_plus_exception_and_orphan_metadata",
            present_lower,
            code_to_symbol,
            predict_mirror_exception_missing_lower,
            {
                "stored_surface": "upper triangle including diagonal",
                "stored_upper_entries": len(present_upper),
                "explicit_exceptions": {"91": code_to_symbol["91"]},
                "reverse_missing_lower_metadata": lower_orphan_metadata,
            },
            [
                "This renders the lower surface completely, but uses metadata for the absent upper code 39.",
                "It is not an independent formula for the matrix labels.",
            ],
        ),
        evaluate(
            "symbol_permutation_lower_surface",
            "lower_surface_symbol_permutation_probe",
            present_lower,
            code_to_symbol,
            predict_symbol_permutation_lower,
            {
                "mapping": permutation_mapping,
                "best_reverse_available_score": permutation["best_score"],
                "identity_reverse_available_score": permutation["identity_score"],
            },
            [
                "A global symbol permutation does not improve on the identity mirror relation.",
                "Useful as a negative control against a hidden lower-surface alphabet substitution.",
            ],
        ),
    ]

    ordered_models = [
        evaluate(
            "ordered_lookup_complete",
            "saturated_ordered_matrix_lookup",
            present_ordered,
            code_to_symbol,
            predict_ordered_lookup,
            {
                "stored_entries": len(code_to_symbol),
                "domain": "00..99 except missing code 39",
            },
            [
                "Exact because it stores every present ordered code.",
                "This is a matrix lookup, not a compact generator for the labels.",
            ],
        ),
        evaluate(
            "unordered_pair_lookup_single_label",
            "unordered_matrix_lookup_with_one_forced_conflict_choice",
            present_ordered,
            code_to_symbol,
            predict_unordered_single,
            {
                "stored_unordered_cells": len(unordered_single_lookup),
                "representative_policy": "use upper code label if present, else the present lower orphan",
            },
            [
                "Almost all ordered labels are explained by the unordered cell label.",
                "The forced single-label cell cannot satisfy both 19=I and 91=N.",
            ],
        ),
        evaluate(
            "unordered_pair_lookup_set_valued_diagnostic",
            "unordered_matrix_lookup_with_conflict_set",
            present_ordered,
            code_to_symbol,
            predict_unordered_set,
            {
                "stored_unordered_cells": len(unordered_set_lookup),
                "conflict_cells": {
                    pair: sorted(symbol_set)
                    for pair, symbol_set in unordered_set_lookup.items()
                    if len(symbol_set) > 1
                },
            },
            [
                "Set-valued acceptance records the conflict instead of rendering one directed symbol.",
                "It is diagnostic metadata, not a single-symbol rendering formula.",
            ],
        ),
        evaluate(
            "upper_lookup_plus_mirror_lower",
            "upper_matrix_lookup_plus_render_orientation_layer",
            present_ordered,
            code_to_symbol,
            lift_upper_plus_lower(predict_mirror_base_lower),
            {
                "stored_upper_entries": len(present_upper),
                "lower_rule": "transpose from upper when reverse is present",
            },
            [
                "Combines an explicit upper matrix with the base lower mirror rule.",
                "The remaining failures are 91 and lower orphan 93.",
            ],
        ),
        evaluate(
            "upper_lookup_plus_mirror_lower_plus_exception_91",
            "upper_matrix_lookup_plus_render_orientation_layer_plus_one_exception",
            present_ordered,
            code_to_symbol,
            lift_upper_plus_lower(predict_mirror_exception_91_lower),
            {
                "stored_upper_entries": len(present_upper),
                "explicit_exceptions": {"91": code_to_symbol["91"]},
            },
            [
                "Adds the directed 91 exception to the upper-plus-mirror rendering layer.",
                "The only remaining uncovered present ordered code is 93 because 39 is absent.",
            ],
        ),
        evaluate(
            "upper_lookup_plus_mirror_lower_plus_exception_and_missing_39_metadata",
            "upper_matrix_lookup_plus_complete_render_metadata",
            present_ordered,
            code_to_symbol,
            lift_upper_plus_lower(predict_mirror_exception_missing_lower),
            {
                "stored_upper_entries": len(present_upper),
                "explicit_exceptions": {"91": code_to_symbol["91"]},
                "reverse_missing_lower_metadata": lower_orphan_metadata,
            },
            [
                "This is lossless for the ordered table only after adding the 91 exception and 93 orphan metadata.",
                "The content labels still come from lookup/metadata, so this is not a generative matrix formula.",
            ],
        ),
    ]

    rng = random.Random(RANDOM_SEED)
    controls = {
        "lower_inventory_shuffle_mirror_matches": lower_inventory_shuffle_control(
            code_to_symbol, reverse_available_lower, rng
        ),
        "ordered_inventory_shuffle_reverse_pair_matches": ordered_inventory_shuffle_control(
            code_to_symbol, reverse_available_pairs, rng
        ),
    }

    diagnostics = {
        "ordered_domain": {
            "total_codes": len(ordered),
            "present_count": len(present_ordered),
            "missing_count": len(missing_ordered),
            "missing_codes": missing_ordered,
        },
        "surfaces": {
            "upper_including_diagonal": {
                "total_codes": len(upper),
                "present_count": len(present_upper),
                "missing_count": len(missing_upper),
                "missing_codes": missing_upper,
                "inventory": inventory(present_upper, code_to_symbol, symbols),
            },
            "lower_strict": {
                "total_codes": len(lower),
                "present_count": len(present_lower),
                "missing_count": len(missing_lower),
                "missing_codes": missing_lower,
                "inventory": inventory(present_lower, code_to_symbol, symbols),
            },
            "ordered_present": {
                "inventory": inventory(present_ordered, code_to_symbol, symbols),
            },
        },
        "directed_conflict": {
            "pair": "19/91",
            "19": code_to_symbol.get("19"),
            "91": code_to_symbol.get("91"),
            "is_conflict": code_to_symbol.get("19") != code_to_symbol.get("91"),
        },
        "mirror_transposition": {
            "reverse_available_unordered_pairs": len(reverse_available_pairs),
            "same_symbol_unordered_pairs": len(reverse_same_pairs),
            "conflict_unordered_pairs": len(reverse_conflicts),
            "conflicts": reverse_conflicts,
            "reverse_missing_unordered_pairs": reverse_missing,
            "present_non_diagonal_codes": len(present_non_diagonal),
            "reverse_available_present_non_diagonal_codes": len(reverse_available_codes),
            "reverse_preserving_present_non_diagonal_codes": len(reverse_preserving_codes),
            "reverse_conflict_present_non_diagonal_codes": len(reverse_conflict_codes),
            "reverse_conflict_codes": reverse_conflict_codes,
            "lower_orphans": lower_orphans,
        },
        "symbol_permutation_probe": permutation,
    }

    conclusion = {
        "classification": "render_orientation_layer_over_lookup_not_new_matrix_formula",
        "summary": (
            "The ordered table is 99 present codes over the 00..99 domain, with 39 absent. "
            "The lower triangle is almost exactly the transpose/mirror of the upper triangle: "
            "43/44 reverse-available unordered pairs match, with one directed conflict 19=I vs 91=N, "
            "and one lower orphan 93=N because upper 39 is missing. "
            "A complete ordered lookup is lossless but saturated; mirror-copy plus the 91 exception "
            "and missing-39 metadata renders the ordered surface losslessly without deriving the "
            "upper/unordered symbol labels."
        ),
        "semantic_delta": "NONE",
        "translation_or_glossary_created": False,
    }

    results = {
        "schema": "directed_pair_surface_search.v1",
        "created_at": "2026-06-19",
        "input": str(FORMULA_JSON.relative_to(ROOT)),
        "random_seed": RANDOM_SEED,
        "control_trials": CONTROL_TRIALS,
        "scope": "mechanical_ordered_code_table_only_no_semantics",
        "diagnostics": diagnostics,
        "models": {
            "ordered_surface": ordered_models,
            "lower_surface": lower_models,
        },
        "controls": controls,
        "conclusion": conclusion,
    }

    write_json(OUT_JSON, results)
    OUT_MD.write_text(render_markdown(results), encoding="utf-8")


def render_model_row(model: dict) -> str:
    return (
        f"| `{model['name']}` | {model['model_type']} | "
        f"{model['correct']}/{model['total']} | {pct(model['strict_accuracy'])} | "
        f"{pct(model['coverage'])} | {model['error_count']} | {model['uncovered_count']} |"
    )


def render_markdown(results: dict) -> str:
    diag = results["diagnostics"]
    controls = results["controls"]
    lower_control = controls["lower_inventory_shuffle_mirror_matches"]
    ordered_control = controls["ordered_inventory_shuffle_reverse_pair_matches"]
    conflict = diag["directed_conflict"]
    mirror = diag["mirror_transposition"]

    ordered_rows = "\n".join(render_model_row(model) for model in results["models"]["ordered_surface"])
    lower_rows = "\n".join(render_model_row(model) for model in results["models"]["lower_surface"])

    conflict_lines = "\n".join(
        f"- `{item['upper_code']}` -> `{item['upper_symbol']}`, "
        f"`{item['lower_code']}` -> `{item['lower_symbol']}`"
        for item in mirror["conflicts"]
    )
    if not conflict_lines:
        conflict_lines = "- none"

    reverse_missing_lines = "\n".join(
        f"- upper `{item['upper_code']}` present={item['upper_present']} symbol={item['upper_symbol']}; "
        f"lower `{item['lower_code']}` present={item['lower_present']} symbol={item['lower_symbol']}"
        for item in mirror["reverse_missing_unordered_pairs"]
    )
    if not reverse_missing_lines:
        reverse_missing_lines = "- none"

    return f"""# Directed Pair Surface Search

Generated by `directed_pair_surface_search.py` from
`analysis/mechanism_model_20260618/mechanical_formula_469.json`.

Mechanical scope only: this report studies the ordered code table and the
upper/lower rendering relation. It creates no translation, glossary, or
plaintext claim.

## Core detections

- Ordered domain: {diag['ordered_domain']['present_count']}/100 present codes.
- Missing ordered code: `{diag['ordered_domain']['missing_codes'][0]}`.
- Upper triangle including diagonal: {diag['surfaces']['upper_including_diagonal']['present_count']}/55 present; missing `{diag['surfaces']['upper_including_diagonal']['missing_codes'][0]}`.
- Lower strict triangle: {diag['surfaces']['lower_strict']['present_count']}/45 present; no lower code is missing.
- Directed conflict: `19` -> `{conflict['19']}` and `91` -> `{conflict['91']}`.
- Reverse-available unordered pairs: {mirror['same_symbol_unordered_pairs']}/{mirror['reverse_available_unordered_pairs']} preserve the same symbol.
- Code-level reverse preservation: {mirror['reverse_preserving_present_non_diagonal_codes']}/{mirror['reverse_available_present_non_diagonal_codes']} present non-diagonal directed codes preserve the reverse symbol.

Conflict pairs:

{conflict_lines}

Reverse-missing pairs:

{reverse_missing_lines}

## Ordered-surface models

| Model | Type | Correct | Strict accuracy | Coverage | Errors | Uncovered |
|---|---|---:|---:|---:|---:|---:|
{ordered_rows}

## Lower-surface models

| Model | Type | Correct | Strict accuracy | Coverage | Errors | Uncovered |
|---|---|---:|---:|---:|---:|---:|
{lower_rows}

## Inventory-preserving controls

- Lower-label shuffle, fixed upper labels: observed mirror matches
  {lower_control['observed']}/{lower_control['evaluated_positions']}; control mean
  {lower_control['control_mean']:.2f}, max {lower_control['control_max']},
  p >= observed = {lower_control['p_value_ge_observed']:.6f}.
- Ordered-label shuffle across all present ordered codes: observed reverse-pair
  matches {ordered_control['observed']}/{ordered_control['evaluated_pairs']};
  control mean {ordered_control['control_mean']:.2f}, max
  {ordered_control['control_max']}, p >= observed =
  {ordered_control['p_value_ge_observed']:.6f}.

## Interpretation

The complete ordered lookup is a lossless matrix table, but it is saturated: it
stores all 99 present ordered labels. The unordered-pair lookup explains the
table as 55 unordered cells except for the directed `19`/`91` conflict when a
single symbol must be rendered.

The mirror-copy family is best interpreted as a render/orientation layer over
the upper/unordered lookup, not as a new formula that derives matrix contents.
Base mirror-copy explains 43/45 lower codes strictly: it misses `93` because
`39` is absent and misrenders `91` because `19` maps to `I`. Adding the `91`
exception gives 44/45 lower codes. Adding missing-`39`/lower-`93` metadata gives
45/45 lower codes, but the upper/unordered symbols are still lookup facts.

The symbol-permutation probe does not improve on identity mirror-copy, so there
is no evidence here for a hidden lower-surface alphabet substitution.

Conclusion: `render_orientation_layer_over_lookup_not_new_matrix_formula`.
Semantic delta: `NONE`.
"""


if __name__ == "__main__":
    main()
