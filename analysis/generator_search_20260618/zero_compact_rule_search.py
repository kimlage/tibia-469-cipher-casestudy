#!/usr/bin/env python3
"""Compact human-rule audit for leading-zero omission.

This pass takes the strongest local signals from the zero-omission audit and
tests them as fixed, readable render rules on top of the `code_only` baseline.
It is mechanical only: no plaintext, glossary, or translation layer is created.
"""

from __future__ import annotations

import json
import math
import random
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

import zero_omission_rule_explainer as zero_rules  # noqa: E402


OUT_JSON = HERE / "zero_compact_rule_results.json"
OUT_MD = HERE / "zero_compact_rule_report.md"
MANIFEST = HERE / "generator_holdout_manifest.json"

RANDOM_SEED = 46920260623
CONTROL_TRIALS = 2000

PRIMARY_PREV_CODES = frozenset({"89", "76", "91", "11", "96", "65", "74"})
SECONDARY_PREV_CODES = frozenset({"54", "50", "21", "75", "71", "95", "64"})
NEGATIVE_06_PREV_CODES = frozenset({"80", "45", "18"})
BOUNDARY_PREV_SYMBOLS = frozenset({"<s>", "*"})


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def binom_bits(n: int, k: int) -> float:
    if k <= 0:
        return 0.0
    if k > n:
        raise ValueError((n, k))
    return math.log2(math.comb(n, k))


def error_bits(error_count: int, row_count: int) -> float:
    return error_count * math.log2(row_count + 1)


def baseline_description_bits(train: list[dict]) -> float:
    cardinality = len({row["code"] for row in train})
    return len({row["code"] for row in train}) * (1.0 + math.log2(cardinality + 1))


def make_code_only(train: list[dict]) -> Callable[[dict], bool]:
    by_code: dict[str, list[bool]] = defaultdict(list)
    for row in train:
        by_code[row["code"]].append(row["label"])
    default = Counter(row["label"] for row in train).most_common(1)[0][0]
    majority = {code: Counter(values).most_common(1)[0][0] for code, values in by_code.items()}
    return lambda row: majority.get(row["code"], default)


def is_code(value: str) -> bool:
    return len(value) == 2 and value.isdigit()


def prev_code_descending_or_diagonal(row: dict) -> bool:
    prev = row["prev_code"]
    return is_code(prev) and int(prev[0]) >= int(prev[1])


def negative_06(row: dict) -> bool:
    return row["code"] == "06" and (
        row["prev_symbol"] == "V" or row["prev_code"] in NEGATIVE_06_PREV_CODES
    )


@dataclass(frozen=True)
class RuleSpec:
    name: str
    description: str
    whitelist: frozenset[str] = frozenset()
    negative_override: bool = False
    boundary: bool = False
    geometry: bool = False


def apply_rule(row: dict, baseline: Callable[[dict], bool], spec: RuleSpec) -> bool:
    prediction = baseline(row)
    if spec.geometry and prev_code_descending_or_diagonal(row):
        prediction = True
    if spec.whitelist and row["prev_code"] in spec.whitelist:
        prediction = True
    if spec.boundary and row["prev_symbol"] in BOUNDARY_PREV_SYMBOLS:
        prediction = True
    if spec.negative_override and negative_06(row):
        prediction = False
    return prediction


def predictions(rows: list[dict], baseline: Callable[[dict], bool], spec: RuleSpec) -> list[bool]:
    return [apply_rule(row, baseline, spec) for row in rows]


def score(rows: list[dict], preds: list[bool]) -> dict:
    y = [row["label"] for row in rows]
    tn, fp, fn, tp = confusion_matrix(y, preds, labels=[False, True]).ravel()
    return {
        "accuracy": accuracy_score(y, preds),
        "balanced_accuracy": balanced_accuracy_score(y, preds),
        "errors": int(sum(left != right for left, right in zip(y, preds))),
        "tp_omit": int(tp),
        "tn_keep": int(tn),
        "fp_false_omit": int(fp),
        "fn_false_keep": int(fn),
    }


def rule_cost_bits(spec: RuleSpec, train: list[dict]) -> float:
    prev_code_cardinality = len({row["prev_code"] for row in train if is_code(row["prev_code"])})
    prev_symbol_cardinality = len({row["prev_symbol"] for row in train})
    code_cardinality = len({row["code"] for row in train})
    bits = 0.0
    if spec.whitelist:
        bits += 2.0 + math.log2(prev_code_cardinality + 1) + binom_bits(
            prev_code_cardinality, len(spec.whitelist)
        )
    if spec.negative_override:
        bits += (
            3.0
            + math.log2(code_cardinality + 1)
            + math.log2(prev_symbol_cardinality + 1)
            + math.log2(prev_code_cardinality + 1)
            + binom_bits(prev_code_cardinality, len(NEGATIVE_06_PREV_CODES))
        )
    if spec.boundary:
        bits += 2.0 + math.log2(prev_symbol_cardinality + 1) + binom_bits(
            prev_symbol_cardinality, len(BOUNDARY_PREV_SYMBOLS)
        )
    if spec.geometry:
        # Fixed relation over the previous two digits: choose feature, orientation,
        # and inclusive diagonal. It is not charged as a lookup table.
        bits += 8.0
    return bits


def mdl_bits(train: list[dict], rows: list[dict], scored: dict, spec: RuleSpec) -> float:
    return baseline_description_bits(train) + rule_cost_bits(spec, train) + error_bits(scored["errors"], len(rows))


def code_preserving_label_shuffle(rows: list[dict], rng: random.Random) -> list[dict]:
    shuffled = [dict(row) for row in rows]
    labels = [row["label"] for row in rows]
    by_code: dict[str, list[int]] = defaultdict(list)
    for index, row in enumerate(rows):
        by_code[row["code"]].append(index)
    for indices in by_code.values():
        values = [labels[index] for index in indices]
        rng.shuffle(values)
        for index, value in zip(indices, values):
            shuffled[index]["label"] = value
    return shuffled


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


def component_stats(rows: list[dict], spec: RuleSpec) -> dict:
    components = {
        "whitelist": lambda row: bool(spec.whitelist and row["prev_code"] in spec.whitelist),
        "negative_06_override": lambda row: bool(spec.negative_override and negative_06(row)),
        "boundary": lambda row: bool(spec.boundary and row["prev_symbol"] in BOUNDARY_PREV_SYMBOLS),
        "geometry": lambda row: bool(spec.geometry and prev_code_descending_or_diagonal(row)),
    }
    out = {}
    for name, fn in components.items():
        if name == "whitelist" and not spec.whitelist:
            continue
        if name == "negative_06_override" and not spec.negative_override:
            continue
        if name == "boundary" and not spec.boundary:
            continue
        if name == "geometry" and not spec.geometry:
            continue
        hits = [row for row in rows if fn(row)]
        out[name] = {
            "support": len(hits),
            "omitted": int(sum(row["label"] for row in hits)),
            "omitted_fraction": (sum(row["label"] for row in hits) / len(hits)) if hits else None,
        }
    return out


def control_for_spec(train: list[dict], spec: RuleSpec, rng: random.Random) -> dict:
    baseline = make_code_only(train)
    observed_rule = score(train, predictions(train, baseline, spec))
    observed_base = score(train, predictions(train, baseline, RuleSpec("code_only", "code_only")))
    observed_delta = observed_rule["balanced_accuracy"] - observed_base["balanced_accuracy"]
    deltas = []
    for _trial in range(CONTROL_TRIALS):
        shuffled = code_preserving_label_shuffle(train, rng)
        shuffled_base = score(shuffled, predictions(shuffled, baseline, RuleSpec("code_only", "code_only")))
        shuffled_rule = score(shuffled, predictions(shuffled, baseline, spec))
        deltas.append(shuffled_rule["balanced_accuracy"] - shuffled_base["balanced_accuracy"])
    return summarize(deltas, observed_delta, high_is_good=True)


def evaluate_spec(train: list[dict], test: list[dict], baseline_mdl: float, spec: RuleSpec, rng: random.Random) -> dict:
    baseline = make_code_only(train)
    train_preds = predictions(train, baseline, spec)
    test_preds = predictions(test, baseline, spec)
    train_score = score(train, train_preds)
    holdout_score = score(test, test_preds)
    holdout_mdl = mdl_bits(train, test, holdout_score, spec)
    mdl_gain = baseline_mdl - holdout_mdl
    train_control = control_for_spec(train, spec, rng)
    verdict = "supporting_render_layer"
    if holdout_score["balanced_accuracy"] <= 0.5 or train_control["p_good_direction"] > 0.10:
        verdict = "rejected_control"
    if (
        holdout_score["balanced_accuracy"] > 0.5
        and train_control["p_good_direction"] <= 0.05
        and mdl_gain > 0
    ):
        verdict = "candidate_compact_render_rule_mdl"
    elif holdout_score["balanced_accuracy"] > 0.5 and train_control["p_good_direction"] <= 0.05:
        verdict = "supporting_render_layer"
    return {
        "name": spec.name,
        "description": spec.description,
        "rule": {
            "prev_code_whitelist": sorted(spec.whitelist),
            "negative_06_override": spec.negative_override,
            "negative_06_prev_codes": sorted(NEGATIVE_06_PREV_CODES) if spec.negative_override else [],
            "negative_06_prev_symbol": "V" if spec.negative_override else None,
            "boundary_prev_symbols": sorted(BOUNDARY_PREV_SYMBOLS) if spec.boundary else [],
            "geometry_prev_code_descending_or_diagonal": spec.geometry,
        },
        "train": train_score,
        "holdout": holdout_score,
        "rule_description_bits": rule_cost_bits(spec, train),
        "holdout_mdl_bits": holdout_mdl,
        "holdout_mdl_gain_vs_code_only_bits": mdl_gain,
        "train_delta_balanced_accuracy_vs_code_only_shuffle": train_control,
        "train_component_stats": component_stats(train, spec),
        "holdout_component_stats": component_stats(test, spec),
        "verdict": verdict,
    }


def candidate_specs() -> list[RuleSpec]:
    primary_secondary = PRIMARY_PREV_CODES | SECONDARY_PREV_CODES
    return [
        RuleSpec("code_only", "Per-code train majority baseline."),
        RuleSpec("primary_prev_code_whitelist", "code_only plus primary positive prev_code whitelist.", PRIMARY_PREV_CODES),
        RuleSpec("secondary_prev_code_whitelist", "code_only plus secondary positive prev_code whitelist.", SECONDARY_PREV_CODES),
        RuleSpec(
            "primary_plus_secondary_prev_code_whitelist",
            "code_only plus primary and secondary positive prev_code whitelists.",
            primary_secondary,
        ),
        RuleSpec(
            "negative_06_override_only",
            "code_only plus keep-zero override for code=06 after V/80/45/18.",
            negative_override=True,
        ),
        RuleSpec("boundary_only", "code_only plus omit after book/star boundary.", boundary=True),
        RuleSpec("geometry_descdiag_only", "code_only plus omit after prev_code with first digit >= second digit.", geometry=True),
        RuleSpec(
            "primary_with_negative_06",
            "primary whitelist with negative code=06 override.",
            PRIMARY_PREV_CODES,
            negative_override=True,
        ),
        RuleSpec(
            "primary_with_negative_06_and_boundary",
            "primary whitelist, negative code=06 override, and boundary omission.",
            PRIMARY_PREV_CODES,
            negative_override=True,
            boundary=True,
        ),
        RuleSpec(
            "primary_secondary_with_negative_06_and_boundary",
            "primary+secondary whitelist, negative code=06 override, and boundary omission.",
            primary_secondary,
            negative_override=True,
            boundary=True,
        ),
        RuleSpec(
            "geometry_with_negative_06_and_boundary",
            "descending/diagonal proxy with negative code=06 override and boundary omission.",
            negative_override=True,
            boundary=True,
            geometry=True,
        ),
        RuleSpec(
            "primary_geometry_with_negative_06_and_boundary",
            "primary whitelist plus descending/diagonal proxy, negative code=06 override, and boundary omission.",
            PRIMARY_PREV_CODES,
            negative_override=True,
            boundary=True,
            geometry=True,
        ),
        RuleSpec(
            "primary_secondary_geometry_with_negative_06_and_boundary",
            "primary+secondary whitelist plus descending/diagonal proxy, negative code=06 override, and boundary omission.",
            primary_secondary,
            negative_override=True,
            boundary=True,
            geometry=True,
        ),
    ]


def write_report(result: dict) -> None:
    baseline = result["baseline"]
    selected = result["selected_by_balanced_accuracy"]
    mdl_selected = result["selected_by_mdl_gain"]
    lines = [
        "# Zero Compact Rule Search",
        "",
        "Generated by `zero_compact_rule_search.py`.",
        "",
        "This pass tests fixed, human-readable zero-rendering rules from the",
        "local-context audit. It does not create a translation or glossary.",
        "",
        "## Setup",
        "",
        f"- Train examples: {result['train_examples']}",
        f"- Holdout examples: {result['holdout_examples']}",
        f"- Holdout books: `{', '.join(result['holdout_books'])}`",
        f"- Code-preserving train-label shuffle trials: {result['control_trials']}",
        "",
        "## Holdout Results",
        "",
        "| Model | Bal acc | Acc | Errors | MDL bits | MDL gain vs code_only | Train shuffle p | Verdict |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
        (
            f"| `code_only` | {baseline['holdout']['balanced_accuracy']:.3f} | "
            f"{baseline['holdout']['accuracy']:.3f} | {baseline['holdout']['errors']} | "
            f"{baseline['holdout_mdl_bits']:.1f} | 0.0 | n/a | `baseline` |"
        ),
    ]
    for row in result["candidate_rows"]:
        if row["name"] == "code_only":
            continue
        lines.append(
            f"| `{row['name']}` | {row['holdout']['balanced_accuracy']:.3f} | "
            f"{row['holdout']['accuracy']:.3f} | {row['holdout']['errors']} | "
            f"{row['holdout_mdl_bits']:.1f} | {row['holdout_mdl_gain_vs_code_only_bits']:.1f} | "
            f"{row['train_delta_balanced_accuracy_vs_code_only_shuffle']['p_good_direction']:.5f} | "
            f"`{row['verdict']}` |"
        )
    lines += [
        "",
        "## Selected Views",
        "",
        (
            f"- Best holdout balanced accuracy: `{selected['name']}` "
            f"({selected['holdout']['balanced_accuracy']:.3f}, "
            f"{selected['holdout']['errors']} errors, MDL gain "
            f"{selected['holdout_mdl_gain_vs_code_only_bits']:.1f} bits)."
        ),
        (
            f"- Best rough MDL gain: `{mdl_selected['name']}` "
            f"({mdl_selected['holdout_mdl_gain_vs_code_only_bits']:.1f} bits, "
            f"{mdl_selected['holdout']['balanced_accuracy']:.3f} balanced accuracy)."
        ),
        f"- Overall classification: `{result['overall_classification']}`.",
        "",
        "## Rule Notes",
        "",
        "- The primary whitelist is `{89,76,91,11,96,65,74}`.",
        "- The secondary whitelist variant adds `{54,50,21,75,71,95,64}`.",
        "- The negative override keeps zero for `code=06` when `prev_symbol=V` or `prev_code in {80,45,18}`.",
        "- The boundary rule omits after `prev_symbol in {<s>, *}`.",
        "- The geometry proxy omits after two-digit `prev_code` where first digit >= second digit.",
        "",
        "## Interpretation",
        "",
    ]
    if result["overall_classification"] == "candidate_compact_render_rule_mdl":
        lines.append(
            "At least one fixed compact render rule beats code_only under the rough MDL estimate. "
            "This remains a mechanical render-layer result, not a semantic reading."
        )
    else:
        lines.append(
            "The fixed rules recover the local zero-omission signal, but the selected predictive "
            "rule does not beat code_only under rough MDL. Classify this as `supporting_render_layer`."
        )
    lines += ["", "Translation delta: `NONE`.", ""]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    train, test = zero_rules.build_dataset()
    manifest = load_json(MANIFEST)
    rng = random.Random(RANDOM_SEED)

    baseline_spec = RuleSpec("code_only", "Per-code train majority baseline.")
    baseline = evaluate_spec(train, test, 0.0, baseline_spec, rng)
    baseline["holdout_mdl_bits"] = mdl_bits(train, test, baseline["holdout"], baseline_spec)
    baseline["holdout_mdl_gain_vs_code_only_bits"] = 0.0
    baseline["verdict"] = "baseline"
    baseline_mdl = baseline["holdout_mdl_bits"]

    rows = []
    for spec in candidate_specs():
        if spec.name == "code_only":
            row = baseline
        else:
            row = evaluate_spec(train, test, baseline_mdl, spec, rng)
        rows.append(row)

    non_baseline = [row for row in rows if row["name"] != "code_only"]
    selected_by_bal = max(
        non_baseline,
        key=lambda row: (
            row["holdout"]["balanced_accuracy"],
            row["holdout"]["accuracy"],
            row["holdout_mdl_gain_vs_code_only_bits"],
        ),
    )
    selected_by_mdl = max(
        non_baseline,
        key=lambda row: (
            row["holdout_mdl_gain_vs_code_only_bits"],
            row["holdout"]["balanced_accuracy"],
            row["holdout"]["accuracy"],
        ),
    )
    if selected_by_bal["holdout_mdl_gain_vs_code_only_bits"] > 0:
        overall = "candidate_compact_render_rule_mdl"
    elif selected_by_bal["holdout"]["balanced_accuracy"] > baseline["holdout"]["balanced_accuracy"]:
        overall = "supporting_render_layer"
    else:
        overall = "rejected_control"

    result = {
        "schema": "zero_compact_rule_results.v1",
        "random_seed": RANDOM_SEED,
        "control_trials": CONTROL_TRIALS,
        "split": "generator_holdout_manifest.book_holdouts",
        "holdout_books": [str(book) for book in manifest["book_holdouts"]],
        "train_examples": len(train),
        "holdout_examples": len(test),
        "baseline": baseline,
        "candidate_rows": rows,
        "selected_by_balanced_accuracy": selected_by_bal,
        "selected_by_mdl_gain": selected_by_mdl,
        "overall_classification": overall,
        "translation_delta": "NONE",
    }
    write_json(OUT_JSON, result)
    write_report(result)
    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(
        f"overall={overall} best_bal={selected_by_bal['name']} "
        f"bal={selected_by_bal['holdout']['balanced_accuracy']:.3f} "
        f"errors={selected_by_bal['holdout']['errors']} "
        f"mdl_gain={selected_by_bal['holdout_mdl_gain_vs_code_only_bits']:.1f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
