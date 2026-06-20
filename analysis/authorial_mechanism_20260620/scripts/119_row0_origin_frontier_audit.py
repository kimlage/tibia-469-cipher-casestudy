from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"


SOURCES = {
    "prequential": REPORTS / "118_prequential_generation_model_audit.json",
    "matrix_exhaustive": ROOT / "analysis/generator_search_20260618/matrix_generator_exhaustive_results.json",
    "pair_rule_cover": ROOT / "analysis/generator_search_20260618/pair_rule_cover_results.json",
    "digit_orbit": ROOT / "analysis/generator_search_20260618/digit_orbit_robust_control_results.json",
    "tape_feature": ROOT / "analysis/generator_search_20260618/tape_feature_pair_label_results.json",
    "bilinear_low_rank": ROOT / "analysis/generator_search_20260618/bilinear_low_rank_pair_factor_results.json",
    "structural_exception": ROOT / "analysis/generator_search_20260618/structural_exception_layer_results.json",
    "k5_eye": ROOT / "analysis/eye_model_20260619/k5_eye_pair_model_results.json",
    "eye_state_5x2": ROOT / "analysis/eye_model_20260619/eye_state_5x2_model_results.json",
    "hierarchical_provenance": REPORTS / "09_hierarchical_provenance_pair_label_audit.json",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def write_result(name: str, result: dict[str, Any], lines: list[str]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"{name}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / f"{name}.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def pct(value: float) -> str:
    return f"{100 * value:.1f}%"


def pvalue_text(value: float | None) -> str:
    if value is None:
        return "n/a"
    if value < 0.0001:
        return f"{value:.2e}"
    return f"{value:.4f}"


def main() -> None:
    prequential = load_json(SOURCES["prequential"])
    matrix = load_json(SOURCES["matrix_exhaustive"])
    pair_rule = load_json(SOURCES["pair_rule_cover"])
    orbit = load_json(SOURCES["digit_orbit"])
    tape_feature = load_json(SOURCES["tape_feature"])
    bilinear = load_json(SOURCES["bilinear_low_rank"])
    structural = load_json(SOURCES["structural_exception"])
    k5 = load_json(SOURCES["k5_eye"])
    eye5x2 = load_json(SOURCES["eye_state_5x2"])
    provenance = load_json(SOURCES["hierarchical_provenance"])

    matrix_best = matrix["best_by_cells"]
    pair_best = pair_rule["best"]
    orbit_observed = orbit["observed"]["best_by_primary_hits"]
    orbit_control = orbit["controls"]["column_preserving_shuffle"]["fixed_swap_6_9"]["primary_hits"]
    tape_best = tape_feature["best"]
    bilinear_best = bilinear["best_by_loo"]
    bilinear_control = bilinear["control"]["loo_accuracy"]
    structural_conclusion = structural["conclusion"]
    k5_label = k5["best_label_rule"]
    eye5x2_label = eye5x2["best_label_rule"]
    provenance_stump = provenance["best_stump"]
    provenance_control = provenance["controls"]["stump_hits"]

    families = [
        {
            "family": "matrix_generator_exhaustive",
            "status": "rejected_lookup_disguise",
            "source": rel(SOURCES["matrix_exhaustive"]),
            "key_result": {
                "best_hits": matrix_best["cells_hit"],
                "pair_count": 55,
                "coverage_fraction": matrix_best["coverage_fraction"],
                "mdl_gain_vs_lookup_bits": matrix_best["mdl_gain_vs_lookup_bits"],
                "classification_count_lookup_disguise": matrix["classification_counts"]["lookup_disguise"],
            },
            "interpretation": "Large candidate sweep finds above-control partial matches, but every tested candidate is more expensive than lookup and classified as lookup disguise.",
        },
        {
            "family": "pair_rule_cover",
            "status": "rejected_lookup_disguise",
            "source": rel(SOURCES["pair_rule_cover"]),
            "key_result": {
                "best_hits": pair_best["primary_hits"],
                "pair_count": 55,
                "accuracy": pair_best["primary_accuracy"],
                "mdl_gain_vs_lookup_bits": pair_best["primary_mdl_gain_vs_lookup_bits"],
                "rule_count": pair_best["rule_count"],
            },
            "interpretation": "Predicate covers can describe frequent labels, but the exception burden exceeds direct lookup cost.",
        },
        {
            "family": "digit_orbit_6_9",
            "status": "weak_signal_not_formula",
            "source": rel(SOURCES["digit_orbit"]),
            "key_result": {
                "primary_hits": orbit_observed["primary_hits"],
                "pair_count": 55,
                "mixed_non_singleton_orbit_count": orbit_observed["mixed_non_singleton_orbit_count"],
                "fixed_swap_control_p": orbit_control["p_good_direction"],
            },
            "interpretation": "The 6/9 swap has robust weak structure, but it compresses only a quotient layer and does not derive the full table.",
        },
        {
            "family": "tape_feature_pair_label",
            "status": "rejected_control",
            "source": rel(SOURCES["tape_feature"]),
            "key_result": {
                "best_hits": tape_best["correct"],
                "pair_count": tape_best["total"],
                "accuracy": tape_best["accuracy"],
                "rule_class": tape_best["rule_class"],
                "predicate": tape_best["predicate"]["id"],
            },
            "interpretation": "Tape/grid features do not predict row0 labels strongly enough to bridge book generation back to table origin.",
        },
        {
            "family": "bilinear_low_rank_pair_factor",
            "status": "weak_low_rank_signal_not_formula",
            "source": rel(SOURCES["bilinear_low_rank"]),
            "key_result": {
                "loo_hits": bilinear_best["loo_correct"],
                "pair_count": 55,
                "loo_accuracy": bilinear_best["loo_accuracy"],
                "control_p_ge_observed": bilinear_control["p_ge_observed"],
                "parameter_ratio_to_inventory_lookup": bilinear["mdl_context"]["lower_bound_parameter_ratio_to_inventory_lookup"],
            },
            "interpretation": "A rank-1 surface is a real weak signal, but even a favorable parameter lower bound is far costlier than inventory lookup.",
        },
        {
            "family": "structural_exception_layer",
            "status": "supporting_render_layer_not_origin_formula",
            "source": rel(SOURCES["structural_exception"]),
            "key_result": {
                "classification": structural_conclusion["classification"],
                "delta_vs_unordered_lookup_lossless_bits": structural_conclusion[
                    "selected_delta_vs_unordered_lookup_lossless_bits"
                ],
            },
            "interpretation": "Exception/render geometry helps explain the ordered surface, not the unordered pair-label origin.",
        },
        {
            "family": "k5_eye_pair_model",
            "status": "rejected_control",
            "source": rel(SOURCES["k5_eye"]),
            "key_result": {
                "label_hits": int(round(k5_label["accuracy"] * 55)),
                "pair_count": 55,
                "accuracy": k5_label["accuracy"],
                "label_gain_control_p": k5["controls"]["label_gain_p"],
            },
            "interpretation": "The five-eye combinatoric scale matches 55 cells, but the actual label generator is ordinary under controls.",
        },
        {
            "family": "eye_state_5x2_model",
            "status": "rejected_control",
            "source": rel(SOURCES["eye_state_5x2"]),
            "key_result": {
                "label_hits": int(round(eye5x2_label["accuracy"] * 55)),
                "pair_count": 55,
                "accuracy": eye5x2_label["accuracy"],
                "label_gain_control_p": eye5x2["controls"]["label_gain_p"],
            },
            "interpretation": "Adding binary state improves raw hits slightly but still fails as a promoted pair-cell formula.",
        },
        {
            "family": "hierarchical_provenance_pair_label",
            "status": "rejected_as_row0_origin",
            "source": rel(SOURCES["hierarchical_provenance"]),
            "key_result": {
                "best_hits": provenance_stump["hits"],
                "pair_count": 55,
                "accuracy": provenance_stump["accuracy"],
                "stump_hit_control_p": provenance_control["p_ge_observed"],
                "gain_vs_lookup_bits": provenance_stump["gain_vs_lookup_bits"],
            },
            "interpretation": "The best book-generation provenance feature is ordinary under hit controls and much more expensive than lookup.",
        },
    ]

    row0_origin_status = {
        "classification": "row0_origin_frontier_saturated_current_corpus",
        "translation_delta": "NONE",
        "compression_bound_bits": prequential["compression_bound_bits"],
        "generation_explanation": "partial_predictive_book_generator_not_row0_origin",
        "frontier_decision": "Do not continue broad row0 origin brute force on the current corpus unless the next test supplies a new structural mechanism, external evidence, holdout-predictive table labels, or a simpler charged rule that beats lookup and controls.",
        "row0_dependency": "The active sequential LZ formula assumes the row0 code table as substrate; it does not derive the 10x10 pair table.",
    }

    advancement_requirements = [
        "Predict pair-cell labels under holdout or prequential scoring, not after seeing the whole table.",
        "Beat direct unordered-pair inventory lookup after charging rule, mapping, exception, and search costs.",
        "Explain the special ordered-surface facts, including the {19,91} conflict and missing 39, without ad hoc posthoc overrides.",
        "Generalize against inventory-preserving, label-shuffle, and topology/control baselines.",
        "Or supply CipSoft/in-game primary evidence for a symbol table or exact book-to-plaintext crib.",
    ]

    result = {
        "schema": "row0_origin_frontier_audit.v1",
        "test": "119_row0_origin_frontier_audit",
        "classification": row0_origin_status["classification"],
        "translation_delta": "NONE",
        "inputs": {name: rel(path) for name, path in SOURCES.items()},
        "status": row0_origin_status,
        "families": families,
        "advancement_requirements": advancement_requirements,
        "summary": {
            "families_indexed": len(families),
            "promoted_row0_origin_formula_count": 0,
            "weak_signal_count": sum(1 for row in families if row["status"].startswith("weak")),
            "rejected_or_supporting_count": sum(1 for row in families if not row["status"].startswith("weak")),
        },
    }

    lines = [
        "# 119. Row0 Origin Frontier Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "This audit changes the unit from compressor tuning to the unresolved origin",
        "of the `row0` / 10x10 pair table. It indexes the existing table-origin",
        "tests and records whether any family can be promoted as a generative",
        "formula for the pair labels.",
        "",
        "The answer remains no. The active sequential LZ model keeps",
        f"`{prequential['compression_bound_bits']:.3f}` bits as `compression_bound`,",
        "but it assumes `row0`; it does not derive the pair-cell table.",
        "",
        "## Family Ledger",
        "",
        "| Family | Status | Key evidence |",
        "|---|---|---|",
    ]

    for row in families:
        evidence = row["key_result"]
        if row["family"] == "matrix_generator_exhaustive":
            key = (
                f"{evidence['best_hits']}/55 hits, "
                f"{evidence['mdl_gain_vs_lookup_bits']:.1f} bits vs lookup, "
                f"{evidence['classification_count_lookup_disguise']} lookup-disguise candidates"
            )
        elif row["family"] == "pair_rule_cover":
            key = (
                f"{evidence['best_hits']}/55 hits ({pct(evidence['accuracy'])}), "
                f"{evidence['mdl_gain_vs_lookup_bits']:.1f} bits vs lookup"
            )
        elif row["family"] == "digit_orbit_6_9":
            key = (
                f"{evidence['primary_hits']}/55 quotient-preserved hits, "
                f"fixed-swap control p={pvalue_text(evidence['fixed_swap_control_p'])}"
            )
        elif row["family"] == "tape_feature_pair_label":
            key = f"{evidence['best_hits']}/55 hits via `{evidence['predicate']}`"
        elif row["family"] == "bilinear_low_rank_pair_factor":
            key = (
                f"{evidence['loo_hits']}/55 leave-one-out hits, "
                f"control p={pvalue_text(evidence['control_p_ge_observed'])}, "
                f"{evidence['parameter_ratio_to_inventory_lookup']:.3f}x inventory lookup"
            )
        elif row["family"] == "structural_exception_layer":
            key = (
                f"{evidence['classification']}; "
                f"{evidence['delta_vs_unordered_lookup_lossless_bits']:.1f} bits vs unordered lookup"
            )
        elif row["family"] in {"k5_eye_pair_model", "eye_state_5x2_model"}:
            key = (
                f"{evidence['label_hits']}/55 label hits, "
                f"label-gain control p={pvalue_text(evidence['label_gain_control_p'])}"
            )
        else:
            key = (
                f"{evidence['best_hits']}/55 hits, "
                f"hit control p={pvalue_text(evidence['stump_hit_control_p'])}, "
                f"{evidence['gain_vs_lookup_bits']:.1f} bits vs lookup"
            )
        lines.append(f"| `{row['family']}` | `{row['status']}` | {key} |")

    lines.extend(
        [
            "",
            "## Decision",
            "",
            "The row0/table-origin frontier is saturated under the current corpus.",
            "This is not a claim that the table has no origin; it is a narrower",
            "claim that the tested source families do not produce a charged,",
            "controlled, holdout-capable row0 formula.",
            "",
            "Further micro-sweeps over book compression should not be treated as",
            "mainline progress unless they also improve generation explanation.",
            "Further row0 work should proceed only if it satisfies at least one",
            "of the following requirements:",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in advancement_requirements)
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- `compression_bound`: active best charged book-generator cost.",
            "- `generation_explanation`: still partial; predictive for book-level",
            "  learned components, not a derivation of `row0`.",
            "- `row0_origin`: open but frontier-saturated on the current evidence.",
            "- `translation_delta`: `NONE`.",
        ]
    )

    write_result("119_row0_origin_frontier_audit", result, lines)


if __name__ == "__main__":
    main()
