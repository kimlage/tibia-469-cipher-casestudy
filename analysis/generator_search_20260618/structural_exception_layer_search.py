#!/usr/bin/env python3
"""Structural exception-layer test for the 469 generator search.

This pass asks whether the already-known anomalies form a compact mechanical
render layer over the pair/code table:

- missing ordered 39 / lower orphan 93
- directed conflict 19/91
- tape/literal-only diagonal E cells 33/66
- diagonal E pressure
- zero-omission geometry
- lower-triangle mirror rendering

It is deliberately mechanical. It creates no plaintext, glossary, or
translation claim.
"""

from __future__ import annotations

import json
import math
import random
from collections import Counter
from pathlib import Path
from statistics import mean, pstdev
from typing import Callable


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

FORMULA_JSON = ROOT / "analysis" / "mechanism_model_20260618" / "mechanical_formula_469.json"
DIRECTED_JSON = HERE / "directed_pair_surface_results.json"
TAPE_LITERAL_JSON = HERE / "tape_literal_exception_results.json"
ZERO_COMPACT_JSON = HERE / "zero_compact_rule_results.json"

OUT_JSON = HERE / "structural_exception_layer_results.json"
OUT_MD = HERE / "structural_exception_layer_report.md"

RANDOM_SEED = 46920260619
CONTROL_TRIALS = 20000

MIRROR_RULE_BITS = 8.0
DIRECTED_OVERLAY_HEADER_BITS = 4.0
EXCEPTION_LAYER_HEADER_BITS = 4.0
DIAGONAL_ANCHOR_RULE_BITS = 12.0
ZERO_GEOMETRY_RULE_BITS = 8.0


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


def present(codes: list[str], code_to_symbol: dict[str, str]) -> list[str]:
    return [code for code in codes if code in code_to_symbol]


def missing(codes: list[str], code_to_symbol: dict[str, str]) -> list[str]:
    return [code for code in codes if code not in code_to_symbol]


def quantile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    index = min(len(ordered) - 1, max(0, round(q * (len(ordered) - 1))))
    return ordered[index]


def summarize_control(values: list[float], observed: float, high_is_good: bool = True) -> dict:
    avg = mean(values)
    sd = pstdev(values)
    if high_is_good:
        p = (sum(value >= observed for value in values) + 1) / (len(values) + 1)
        z = (observed - avg) / sd if sd else 0.0
    else:
        p = (sum(value <= observed for value in values) + 1) / (len(values) + 1)
        z = (avg - observed) / sd if sd else 0.0
    return {
        "observed": observed,
        "trials": len(values),
        "control_mean": avg,
        "control_sd_population": sd,
        "control_min": min(values),
        "control_p50": quantile(values, 0.50),
        "control_p95": quantile(values, 0.95),
        "control_p99": quantile(values, 0.99),
        "control_max": max(values),
        "z_good_direction": z,
        "p_value_good_direction": p,
    }


def evaluate_model(
    name: str,
    model_type: str,
    target_codes: list[str],
    code_to_symbol: dict[str, str],
    predict: Callable[[str], str | None],
    description_bits: float,
    description: str,
    derives: list[str],
    leaves_lookup: list[str],
    mdl_reference_bits: float,
    prior_lossless_bits: float | None,
) -> dict:
    correct = 0
    predicted = 0
    errors = []
    uncovered = []
    for code in target_codes:
        actual = code_to_symbol[code]
        expected = predict(code)
        if expected is None:
            uncovered.append({"code": code, "actual": actual})
            continue
        predicted += 1
        if expected == actual:
            correct += 1
        else:
            errors.append({"code": code, "actual": actual, "predicted": expected})

    residual_count = len(errors) + len(uncovered)
    residual_bits = residual_count * evaluate_model.residual_correction_bits
    lossless_bits = description_bits + residual_bits
    return {
        "name": name,
        "model_type": model_type,
        "description": description,
        "correct": correct,
        "predicted": predicted,
        "total": len(target_codes),
        "coverage": predicted / len(target_codes),
        "covered_accuracy": correct / predicted if predicted else 0.0,
        "strict_accuracy": correct / len(target_codes),
        "error_count": len(errors),
        "uncovered_count": len(uncovered),
        "errors": errors,
        "uncovered": uncovered,
        "mdl": {
            "description_bits": description_bits,
            "residual_correction_bits": residual_bits,
            "lossless_bits": lossless_bits,
            "delta_bits_vs_ordered_lookup": mdl_reference_bits - lossless_bits,
            "delta_bits_vs_previous_lossless_model": (
                None if prior_lossless_bits is None else prior_lossless_bits - lossless_bits
            ),
        },
        "derives": derives,
        "leaves_lookup": leaves_lookup,
    }


def build_unordered_lookup(code_to_symbol: dict[str, str]) -> dict[str, str]:
    lookup = {}
    for pair in unordered_pairs():
        upper = pair
        lower = reverse_code(pair)
        if upper in code_to_symbol:
            lookup[pair] = code_to_symbol[upper]
        elif lower in code_to_symbol:
            lookup[pair] = code_to_symbol[lower]
    return lookup


def mirror_residuals(code_to_symbol: dict[str, str]) -> dict:
    rows = []
    for code in present(lower_codes(), code_to_symbol):
        rev = reverse_code(code)
        if rev not in code_to_symbol:
            rows.append({"kind": "lower_orphan", "code": code, "actual": code_to_symbol[code], "reverse": rev})
        elif code_to_symbol[rev] != code_to_symbol[code]:
            rows.append(
                {
                    "kind": "directed_conflict",
                    "code": code,
                    "actual": code_to_symbol[code],
                    "reverse": rev,
                    "reverse_symbol": code_to_symbol[rev],
                }
            )
    return {
        "residuals": rows,
        "error_codes": [row["code"] for row in rows if row["kind"] == "directed_conflict"],
        "orphan_codes": [row["code"] for row in rows if row["kind"] == "lower_orphan"],
    }


def mirror_match_control(
    code_to_symbol: dict[str, str],
    reverse_available_lower: list[str],
    rng: random.Random,
) -> dict:
    upper_labels = [code_to_symbol[reverse_code(code)] for code in reverse_available_lower]
    lower_labels = [code_to_symbol[code] for code in reverse_available_lower]
    observed = sum(left == right for left, right in zip(upper_labels, lower_labels))
    values = []
    shuffled = lower_labels[:]
    for _trial in range(CONTROL_TRIALS):
        rng.shuffle(shuffled)
        values.append(sum(left == right for left, right in zip(upper_labels, shuffled)))
    out = summarize_control(values, observed)
    out.update(
        {
            "null": "shuffle lower-triangle labels over reverse-available positions, preserving lower inventory",
            "evaluated_positions": len(reverse_available_lower),
        }
    )
    return out


def exception_pick_control(
    code_to_symbol: dict[str, str],
    reverse_available_lower: list[str],
    present_lower: list[str],
    observed_conflict: str,
    observed_orphan: str,
    rng: random.Random,
) -> dict:
    observed = 2
    values = []
    for _trial in range(CONTROL_TRIALS):
        conflict_pick = rng.choice(reverse_available_lower)
        orphan_pick = rng.choice(present_lower)
        values.append(int(conflict_pick == observed_conflict) + int(orphan_pick == observed_orphan))
    out = summarize_control(values, observed)
    out.update(
        {
            "null": "choose one random reverse-available lower code and one random present lower code as exceptions",
            "conflict_candidate_count": len(reverse_available_lower),
            "orphan_candidate_count": len(present_lower),
            "observed_exception_codes": [observed_conflict, observed_orphan],
        }
    )
    return out


def diagonal_anchor_control(
    code_to_symbol: dict[str, str],
    tape_pair_only_outside: list[str],
    rng: random.Random,
) -> dict:
    diagonal = [code for code in upper_codes() if code[0] == code[1] and code in code_to_symbol]
    observed_set = set(tape_pair_only_outside)
    observed_exact = 2
    observed_e = sum(1 for code in tape_pair_only_outside if code_to_symbol.get(code) == "E")
    exact_values = []
    both_e_values = []
    for _trial in range(CONTROL_TRIALS):
        sample = set(rng.sample(diagonal, len(tape_pair_only_outside)))
        exact_values.append(len(sample & observed_set))
        both_e_values.append(sum(1 for code in sample if code_to_symbol[code] == "E"))
    exact = summarize_control(exact_values, observed_exact)
    both_e = summarize_control(both_e_values, observed_e)
    exact.update(
        {
            "null": "choose two random present diagonal cells as the anchor set",
            "diagonal_candidate_count": len(diagonal),
            "observed_anchor_codes": tape_pair_only_outside,
            "score": "overlap with {33,66}",
        }
    )
    both_e.update(
        {
            "null": "choose two random present diagonal cells and count E labels",
            "diagonal_candidate_count": len(diagonal),
            "observed_anchor_codes": tape_pair_only_outside,
            "score": "E-labeled sampled diagonal cells",
        }
    )
    return {"exact_anchor_set": exact, "both_are_e": both_e}


def diagonal_e_pressure_control(code_to_symbol: dict[str, str], pair_lookup: dict[str, str], rng: random.Random) -> dict:
    pairs = unordered_pairs()
    labels = [pair_lookup[pair] for pair in pairs]
    diagonal = [pair for pair in pairs if pair[0] == pair[1]]
    observed = sum(1 for pair in diagonal if pair_lookup[pair] == "E")
    values = []
    shuffled = labels[:]
    for _trial in range(CONTROL_TRIALS):
        rng.shuffle(shuffled)
        table = dict(zip(pairs, shuffled))
        values.append(sum(1 for pair in diagonal if table[pair] == "E"))
    out = summarize_control(values, observed)
    out.update(
        {
            "null": "shuffle unordered pair labels over the 55 fixed cells, preserving inventory",
            "diagonal_cells": diagonal,
            "diagonal_count": len(diagonal),
            "observed_e_diagonal_count": observed,
            "unordered_e_cell_count": Counter(labels)["E"],
        }
    )
    return out


def report_lines(result: dict) -> list[str]:
    models = result["models"]
    controls = result["controls"]
    anomalies = result["anomalies"]
    selected = result["selected_model"]
    ordered_bits = result["mdl_parameters"]["ordered_lookup_reference_bits"]
    lines = [
        "# Structural Exception Layer Search",
        "",
        "Generated by `structural_exception_layer_search.py`.",
        "",
        "Scope: mechanical code/table/rendering evidence only. No translation,",
        "glossary, or plaintext is created or promoted.",
        "",
        "## Question",
        "",
        "Do the known anomalies form a compact structural layer over the existing",
        "mechanical formula, or are they just isolated lookup patches?",
        "",
        "## Incremental Models",
        "",
        f"Reference saturated ordered lookup: {ordered_bits:.1f} bits for 99 ordered labels.",
        "",
        "| Model | Correct | Raw acc | Residuals | Lossless MDL bits | Delta vs ordered | Delta vs previous |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in models:
        mdl = row["mdl"]
        prev = mdl["delta_bits_vs_previous_lossless_model"]
        prev_text = "n/a" if prev is None else f"{prev:.1f}"
        residuals = row["error_count"] + row["uncovered_count"]
        lines.append(
            f"| `{row['name']}` | {row['correct']}/{row['total']} | {row['strict_accuracy']:.3f} | "
            f"{residuals} | {mdl['lossless_bits']:.1f} | {mdl['delta_bits_vs_ordered_lookup']:.1f} | {prev_text} |"
        )

    lines += [
        "",
        f"Selected compact structural layer: `{selected['name']}`.",
        "",
        "The selected layer is not the cheapest possible lossless notation once an",
        "unordered pair lookup is already allowed. Its value is structural: it",
        "derives the lower surface as a mirror of the upper surface and isolates",
        "the two remaining lower-side anomalies.",
        "",
        "## Controls",
        "",
        "| Test | Observed | Control mean | Control max | p | Interpretation |",
        "|---|---:|---:|---:|---:|---|",
    ]
    lines.append(
        "| mirror lower matches | "
        f"{controls['mirror_lower_match_shuffle']['observed']:.0f} | "
        f"{controls['mirror_lower_match_shuffle']['control_mean']:.2f} | "
        f"{controls['mirror_lower_match_shuffle']['control_max']:.0f} | "
        f"{controls['mirror_lower_match_shuffle']['p_value_good_direction']:.5f} | strong structural signal |"
    )
    lines.append(
        "| random exception picks hit 91+93 | "
        f"{controls['exception_pick_control']['observed']:.0f} | "
        f"{controls['exception_pick_control']['control_mean']:.3f} | "
        f"{controls['exception_pick_control']['control_max']:.0f} | "
        f"{controls['exception_pick_control']['p_value_good_direction']:.5f} | known exceptions are compact, but still exceptions |"
    )
    lines.append(
        "| diagonal E pressure | "
        f"{controls['diagonal_e_pressure_shuffle']['observed']:.0f} | "
        f"{controls['diagonal_e_pressure_shuffle']['control_mean']:.2f} | "
        f"{controls['diagonal_e_pressure_shuffle']['control_max']:.0f} | "
        f"{controls['diagonal_e_pressure_shuffle']['p_value_good_direction']:.5f} | suggestive only |"
    )
    lines.append(
        "| 33/66 exact diagonal anchor set | "
        f"{controls['diagonal_anchor_control']['exact_anchor_set']['observed']:.0f} | "
        f"{controls['diagonal_anchor_control']['exact_anchor_set']['control_mean']:.2f} | "
        f"{controls['diagonal_anchor_control']['exact_anchor_set']['control_max']:.0f} | "
        f"{controls['diagonal_anchor_control']['exact_anchor_set']['p_value_good_direction']:.5f} | conditional anchor is narrow |"
    )
    tape_control = controls["existing_tape_literal_exception_control"]
    lines.append(
        "| prior tape-only/literal-only Bonferroni | "
        f"{tape_control['best_raw_p']:.5f} raw p | n/a | n/a | "
        f"{tape_control['bonferroni_p']:.5f} | not promoted after multiplicity |"
    )
    zero = controls["zero_omission_geometry"]
    lines.append(
        "| zero geometry holdout MDL | "
        f"{zero['holdout_mdl_gain_vs_code_only_bits']:.1f} bits | n/a | n/a | "
        f"{zero['train_shuffle_p_good_direction']:.5f} | separate zero-render support |"
    )

    lines += [
        "",
        "## Anomaly Accounting",
        "",
        "| Anomaly | Status in this layer | What is derived | What remains lookup/metadata |",
        "|---|---|---|---|",
    ]
    for anomaly in anomalies:
        lines.append(
            f"| `{anomaly['id']}` | {anomaly['status']} | {anomaly['derived']} | {anomaly['lookup_or_metadata']} |"
        )

    lines += [
        "",
        "## Verdict",
        "",
        result["conclusion"]["summary"],
        "",
        f"Classification: `{result['conclusion']['classification']}`.",
        f"Translation delta: `{result['translation_delta']}`.",
        "",
    ]
    return lines


def main() -> int:
    formula = load_json(FORMULA_JSON)
    directed = load_json(DIRECTED_JSON)
    tape_literal = load_json(TAPE_LITERAL_JSON)
    zero_compact = load_json(ZERO_COMPACT_JSON)

    code_to_symbol: dict[str, str] = dict(sorted(formula["code_to_symbol"].items()))
    symbols = list(formula["formula"]["internal_alphabet"])
    label_bits = math.log2(len(symbols))
    code_address_bits = math.log2(100)
    pair_address_bits = math.log2(55)
    correction_bits = code_address_bits + label_bits
    evaluate_model.residual_correction_bits = correction_bits

    target_codes = present(all_ordered_codes(), code_to_symbol)
    present_upper = present(upper_codes(), code_to_symbol)
    present_lower = present(lower_codes(), code_to_symbol)
    missing_ordered = missing(all_ordered_codes(), code_to_symbol)
    pair_lookup = build_unordered_lookup(code_to_symbol)
    mirror = mirror_residuals(code_to_symbol)

    lower_reverse_available = [
        code for code in present_lower if reverse_code(code) in code_to_symbol
    ]
    reverse_available_pairs = [
        (reverse_code(code), code) for code in lower_reverse_available
    ]
    same_reverse_pairs = [
        (upper, lower)
        for upper, lower in reverse_available_pairs
        if code_to_symbol[upper] == code_to_symbol[lower]
    ]

    tape_pair_only_outside = sorted(tape_literal["sets"]["pair_only_outside"])
    diagonal_anchor_codes = {"33", "66"}
    if set(tape_pair_only_outside) != diagonal_anchor_codes:
        raise ValueError(f"unexpected pair_only_outside set: {tape_pair_only_outside}")

    ordered_lookup_bits = len(target_codes) * label_bits
    unordered_lookup_bits = len(pair_lookup) * label_bits
    upper_lookup_bits = len(present_upper) * label_bits
    upper_without_anchor_bits = (len(present_upper) - len(diagonal_anchor_codes)) * label_bits

    def predict_unordered(code: str) -> str | None:
        return pair_lookup.get(pair_key(code))

    def predict_unordered_directed_overlay(code: str) -> str | None:
        if code == "91":
            return code_to_symbol[code]
        return predict_unordered(code)

    def predict_upper_mirror(code: str) -> str | None:
        if code[0] <= code[1]:
            return code_to_symbol.get(code)
        return code_to_symbol.get(reverse_code(code))

    def predict_upper_mirror_exceptions(code: str) -> str | None:
        if code in {"91", "93"}:
            return code_to_symbol[code]
        return predict_upper_mirror(code)

    def predict_diagonal_anchor_exceptions(code: str) -> str | None:
        if code in diagonal_anchor_codes:
            return "E"
        return predict_upper_mirror_exceptions(code)

    models = []
    prior_bits = None
    model_specs = [
        (
            "unordered_lookup",
            "unordered_pair_lookup_single_label",
            predict_unordered,
            unordered_lookup_bits,
            "Store one label for each unordered pair cell; render both directions with that label.",
            ["54/55 pure unordered pair classes and the lower orphan as pair-cell lookup"],
            ["sole conflict 91 is wrong unless stored as residual; all pair labels are still lookup"],
        ),
        (
            "unordered_lookup_plus_directed_render",
            "unordered_pair_lookup_with_one_directed_overlay",
            predict_unordered_directed_overlay,
            unordered_lookup_bits + DIRECTED_OVERLAY_HEADER_BITS + correction_bits,
            "Store unordered pair labels plus one directed overlay for 91=N.",
            ["the 19/91 conflict as a single directed render overlay"],
            ["55 unordered labels, including pair 39 from lower 93, are still lookup"],
        ),
        (
            "directed_render_plus_exception_layer",
            "upper_lookup_mirror_lower_with_91_93_exceptions",
            predict_upper_mirror_exceptions,
            upper_lookup_bits + MIRROR_RULE_BITS + EXCEPTION_LAYER_HEADER_BITS + 2 * correction_bits,
            "Store the upper surface, mirror lower cells, and encode 91 plus 93 as the exception layer.",
            ["43/44 reverse-available lower cells by mirror; 91 and 93 isolated as the residual layer"],
            ["54 upper/diagonal labels are still lookup; 91 and 93 are explicit metadata"],
        ),
        (
            "diagonal_E_anchors_plus_exceptions",
            "upper_lookup_mirror_lower_with_diagonal_e_anchor_rule",
            predict_diagonal_anchor_exceptions,
            upper_without_anchor_bits
            + MIRROR_RULE_BITS
            + EXCEPTION_LAYER_HEADER_BITS
            + 2 * correction_bits
            + DIAGONAL_ANCHOR_RULE_BITS
            + label_bits,
            "Replace stored labels for 33/66 with a tape/literal-only diagonal=>E anchor rule, plus 91/93 exceptions.",
            ["33 and 66 from the pair-only-outside diagonal E anchor rule; lower surface by mirror"],
            ["52 upper labels and the anchor symbol E remain lookup-like; tape anchor is weak after controls"],
        ),
        (
            "mirror_lower_plus_exceptions",
            "selected_compact_structural_layer",
            predict_upper_mirror_exceptions,
            upper_lookup_bits + MIRROR_RULE_BITS + EXCEPTION_LAYER_HEADER_BITS + 2 * correction_bits,
            "Selected structural layer: upper lookup, mirror lower, and exactly the 91/93 exceptions.",
            ["lower-triangle rendering except the two named residuals"],
            ["upper/unordered symbol identities are not derived; this is not a matrix-origin formula"],
        ),
    ]
    for name, model_type, predict, bits, description, derives, leaves_lookup in model_specs:
        row = evaluate_model(
            name=name,
            model_type=model_type,
            target_codes=target_codes,
            code_to_symbol=code_to_symbol,
            predict=predict,
            description_bits=bits,
            description=description,
            derives=derives,
            leaves_lookup=leaves_lookup,
            mdl_reference_bits=ordered_lookup_bits,
            prior_lossless_bits=prior_bits,
        )
        models.append(row)
        prior_bits = row["mdl"]["lossless_bits"]

    rng = random.Random(RANDOM_SEED)
    controls = {
        "mirror_lower_match_shuffle": mirror_match_control(code_to_symbol, lower_reverse_available, rng),
        "exception_pick_control": exception_pick_control(
            code_to_symbol=code_to_symbol,
            reverse_available_lower=lower_reverse_available,
            present_lower=present_lower,
            observed_conflict="91",
            observed_orphan="93",
            rng=rng,
        ),
        "diagonal_anchor_control": diagonal_anchor_control(code_to_symbol, tape_pair_only_outside, rng),
        "diagonal_e_pressure_shuffle": diagonal_e_pressure_control(code_to_symbol, pair_lookup, rng),
        "existing_directed_surface_controls": directed["controls"],
        "existing_tape_literal_exception_control": {
            "best_raw_p": tape_literal["best_raw_p"],
            "bonferroni_p": tape_literal["bonferroni_p"],
            "pair_diagonal_count": tape_literal["controls"]["pair_diagonal_count"],
            "pair_all_e": tape_literal["controls"]["pair_all_e"],
            "verdict": tape_literal["verdict"],
        },
        "zero_omission_geometry": {
            "source": str(ZERO_COMPACT_JSON.relative_to(ROOT)),
            "model": zero_compact["selected_by_mdl_gain"]["name"],
            "holdout_balanced_accuracy": zero_compact["selected_by_mdl_gain"]["holdout"]["balanced_accuracy"],
            "holdout_accuracy": zero_compact["selected_by_mdl_gain"]["holdout"]["accuracy"],
            "holdout_errors": zero_compact["selected_by_mdl_gain"]["holdout"]["errors"],
            "holdout_mdl_bits": zero_compact["selected_by_mdl_gain"]["holdout_mdl_bits"],
            "holdout_mdl_gain_vs_code_only_bits": zero_compact["selected_by_mdl_gain"][
                "holdout_mdl_gain_vs_code_only_bits"
            ],
            "train_shuffle_p_good_direction": zero_compact["selected_by_mdl_gain"][
                "train_delta_balanced_accuracy_vs_code_only_shuffle"
            ]["p_good_direction"],
            "rule_description_bits": zero_compact["selected_by_mdl_gain"]["rule_description_bits"],
            "classification": zero_compact["overall_classification"],
            "note": "zero-render support only; it does not derive pair-table labels",
        },
    }

    anomalies = [
        {
            "id": "missing_ordered_39_lower_orphan_93",
            "status": "compact metadata in mirror model",
            "derived": "upper 39 absence explains why mirror rendering cannot cover lower 93",
            "lookup_or_metadata": "93=N is still stored as orphan metadata; N is not derived",
        },
        {
            "id": "conflict_19_91",
            "status": "explicit exception",
            "derived": "the layer isolates it as the only reverse-available lower conflict",
            "lookup_or_metadata": "91=N is not predicted by the mirror rule; it is an explicit directed exception",
        },
        {
            "id": "tape_only_diagonal_E_33_66",
            "status": "weak anchor, not selected",
            "derived": "a possible rule can mark pair-only-outside diagonal cells as E",
            "lookup_or_metadata": "prior Bonferroni control remains non-promoted; E is still an anchor label",
        },
        {
            "id": "diagonal_E_pressure",
            "status": "suggestive pressure only",
            "derived": "diagonal E count is measured against inventory-preserving shuffles",
            "lookup_or_metadata": "does not recover the full diagonal or table placement",
        },
        {
            "id": "zero_omission_geometry",
            "status": "separate supporting render layer",
            "derived": "previous-code descending/diagonal geometry improves zero-omission holdout MDL",
            "lookup_or_metadata": "zero rendering is not a symbol-label generator and remains incomplete",
        },
        {
            "id": "mirror_lower",
            "status": "strong structural layer",
            "derived": f"{len(same_reverse_pairs)}/{len(reverse_available_pairs)} reverse-available lower pairs copy the upper symbol",
            "lookup_or_metadata": "the upper/unordered labels themselves remain lookup",
        },
    ]

    selected = next(row for row in models if row["name"] == "mirror_lower_plus_exceptions")
    unordered_lossless = next(row for row in models if row["name"] == "unordered_lookup")["mdl"]["lossless_bits"]
    conclusion = {
        "classification": "compact_render_layer_over_lookup_not_new_matrix_formula",
        "summary": (
            "The anomalies do form a compact render/exception layer for the ordered surface: "
            "mirror lower is far above shuffled controls, and the only residual lower-side "
            "codes are 91 and 93. The layer saves substantial MDL versus a saturated ordered "
            "lookup, but it does not beat the most compact unordered-pair lookup with one "
            "residual correction. Diagonal E anchors and zero-omission geometry are useful "
            "mechanical side evidence, not a promoted table-origin formula."
        ),
        "translation_or_glossary_created": False,
        "semantic_delta": "NONE",
        "selected_delta_vs_unordered_lookup_lossless_bits": unordered_lossless - selected["mdl"]["lossless_bits"],
    }

    result = {
        "schema": "structural_exception_layer_search.v1",
        "created_at": "2026-06-19",
        "random_seed": RANDOM_SEED,
        "control_trials": CONTROL_TRIALS,
        "scope": "mechanical_ordered_code_table_and_render_layers_only_no_semantics",
        "source_files": {
            "mechanical_formula": str(FORMULA_JSON.relative_to(ROOT)),
            "directed_surface": str(DIRECTED_JSON.relative_to(ROOT)),
            "tape_literal_exception": str(TAPE_LITERAL_JSON.relative_to(ROOT)),
            "zero_compact_rule": str(ZERO_COMPACT_JSON.relative_to(ROOT)),
        },
        "translation_delta": "NONE",
        "mdl_parameters": {
            "alphabet": "".join(symbols),
            "alphabet_size": len(symbols),
            "label_bits": label_bits,
            "code_address_bits": code_address_bits,
            "pair_address_bits": pair_address_bits,
            "residual_correction_bits": correction_bits,
            "mirror_rule_bits": MIRROR_RULE_BITS,
            "directed_overlay_header_bits": DIRECTED_OVERLAY_HEADER_BITS,
            "exception_layer_header_bits": EXCEPTION_LAYER_HEADER_BITS,
            "diagonal_anchor_rule_bits": DIAGONAL_ANCHOR_RULE_BITS,
            "zero_geometry_rule_bits": ZERO_GEOMETRY_RULE_BITS,
            "ordered_lookup_reference_bits": ordered_lookup_bits,
            "note": "rough internal MDL for comparing these render-layer models only",
        },
        "diagnostics": {
            "ordered_present_count": len(target_codes),
            "missing_ordered": missing_ordered,
            "upper_present_count": len(present_upper),
            "lower_present_count": len(present_lower),
            "reverse_available_lower_count": len(lower_reverse_available),
            "mirror_same_reverse_pairs": len(same_reverse_pairs),
            "mirror_residuals": mirror,
            "tape_pair_only_outside": tape_pair_only_outside,
            "diagonal_anchor_codes": sorted(diagonal_anchor_codes),
            "pair_lookup_size": len(pair_lookup),
            "symbols": symbols,
        },
        "models": models,
        "selected_model": selected,
        "controls": controls,
        "anomalies": anomalies,
        "conclusion": conclusion,
    }

    write_json(OUT_JSON, result)
    OUT_MD.write_text("\n".join(report_lines(result)), encoding="utf-8")
    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(f"wrote {OUT_MD.relative_to(ROOT)}")
    print(
        "selected={name} correct={correct}/{total} lossless_bits={bits:.1f} "
        "delta_vs_ordered={delta:.1f} mirror_p={mirror_p:.5f} exception_p={exception_p:.5f}".format(
            name=selected["name"],
            correct=selected["correct"],
            total=selected["total"],
            bits=selected["mdl"]["lossless_bits"],
            delta=selected["mdl"]["delta_bits_vs_ordered_lookup"],
            mirror_p=controls["mirror_lower_match_shuffle"]["p_value_good_direction"],
            exception_p=controls["exception_pick_control"]["p_value_good_direction"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
