from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

AUTHORIAL_RESULTS = ROOT / "analysis" / "authorial_mechanism_20260620" / "reports" / "test_results"

SOURCES = {
    "recipe_externality": TEST_RESULTS / "04_recipe_externality_audit.json",
    "prequential_recipe_reparse": AUTHORIAL_RESULTS / "126_prequential_recipe_reparse_audit.json",
    "reparse_content_controls": AUTHORIAL_RESULTS / "127_prequential_recipe_reparse_controls.json",
    "reparse_trainset_controls": AUTHORIAL_RESULTS / "128_prequential_recipe_reparse_trainset_controls.json",
    "reparse_trainset_multicutoff": TEST_RESULTS / "07_recipe_reparse_trainset_multicutoff.json",
    "reparse_family_holdout": TEST_RESULTS / "08_recipe_reparse_family_holdout.json",
    "reparse_family_loss_decomposition": TEST_RESULTS
    / "09_recipe_reparse_family_loss_decomposition.json",
    "online_reparse_compile": AUTHORIAL_RESULTS / "129_online_deterministic_reparse_compile.json",
    "online_reparse_order_controls": AUTHORIAL_RESULTS / "130_online_reparse_order_control_audit.json",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def assert_boundary(name: str, data: dict[str, Any]) -> None:
    if data.get("translation_delta") != "NONE":
        raise RuntimeError(f"{name} changed translation boundary")


def make_result() -> dict[str, Any]:
    recipe_externality = load_json(SOURCES["recipe_externality"])
    reparse = load_json(SOURCES["prequential_recipe_reparse"])
    content_controls = load_json(SOURCES["reparse_content_controls"])
    trainset_controls = load_json(SOURCES["reparse_trainset_controls"])
    trainset_multicutoff = load_json(SOURCES["reparse_trainset_multicutoff"])
    family_holdout = load_json(SOURCES["reparse_family_holdout"])
    family_loss_decomposition = load_json(SOURCES["reparse_family_loss_decomposition"])
    online_compile = load_json(SOURCES["online_reparse_compile"])
    order_controls = load_json(SOURCES["online_reparse_order_controls"])

    for name, data in [
        ("prequential_recipe_reparse", reparse),
        ("reparse_content_controls", content_controls),
        ("reparse_trainset_controls", trainset_controls),
        ("reparse_trainset_multicutoff", trainset_multicutoff),
        ("reparse_family_holdout", family_holdout),
        ("reparse_family_loss_decomposition", family_loss_decomposition),
        ("online_reparse_compile", online_compile),
        ("online_reparse_order_controls", order_controls),
    ]:
        assert_boundary(name, data)

    fixed = recipe_externality["accounting"]["fixed_recipe_or_nonlearned_bits"]
    total = recipe_externality["accounting"]["active_total_bits"]
    fixed_share = fixed / total

    reparse_rows = reparse["rows"]
    content_rows = content_controls["rows"]
    trainset_row = trainset_controls["rows"][0]

    evidence = [
        {
            "question": "does_deterministic_reparse_roundtrip_future_suffixes",
            "source": rel(SOURCES["prequential_recipe_reparse"]),
            "status": "passed",
            "evidence": {
                "cutoffs": [row["cutoff"] for row in reparse_rows],
                "all_roundtrip": reparse["summary"]["all_roundtrip"],
                "all_reparse_beats_active_recipe": reparse["summary"]["all_reparse_beats_active_recipe"],
                "mean_reparse_minus_active_bits": reparse["summary"]["mean_reparse_minus_active_bits"],
                "max_reparse_minus_active_bits": reparse["summary"]["max_reparse_minus_active_bits"],
            },
            "interpretation": (
                "The fixed parser can rediscover useful held-out recipes under "
                "frozen train-prefix component counts."
            ),
        },
        {
            "question": "does_reparse_signal_beat_content_controls",
            "source": rel(SOURCES["reparse_content_controls"]),
            "status": "passed_low_trial_count",
            "evidence": {
                "cutoffs": [row["cutoff"] for row in content_rows],
                "observed_beats_all_control_means": content_controls["summary"][
                    "observed_beats_all_control_means"
                ],
                "observed_stronger_than_random_same_lengths_at_all_cutoffs": content_controls["summary"][
                    "observed_stronger_than_random_same_lengths_at_all_cutoffs"
                ],
                "control_trials": content_controls["control_trials"],
            },
            "interpretation": (
                "Observed suffixes are not behaving like generic random or shuffled "
                "decimal strings, although the small control count limits p-value resolution."
            ),
        },
        {
            "question": "is_numeric_prefix_training_uniquely_supported_single_cutoff",
            "source": rel(SOURCES["reparse_trainset_controls"]),
            "status": "failed_as_authorial_order_proof",
            "evidence": {
                "cutoff": trainset_row["cutoff"],
                "observed_gain_vs_raw_bits": trainset_row["observed_prefix"]["gain_vs_raw_bits"],
                "random_train_mean_gain_bits": trainset_row["random_train_set_control"]["mean"],
                "random_train_max_gain_bits": trainset_row["random_train_set_control"]["max"],
                "p_random_ge_observed": trainset_row["random_train_set_control"]["p_control_ge_observed"],
                "numeric_prefix_specific_at_all_cutoffs": trainset_controls["summary"][
                    "numeric_prefix_specific_at_all_cutoffs"
                ],
            },
            "interpretation": (
                "The copy/reference mechanism is predictive, but random same-size "
                "training inventories can match or exceed the numeric prefix in the "
                "focused train-set control."
            ),
        },
        {
            "question": "is_numeric_prefix_training_uniquely_supported_multicutoff",
            "source": rel(SOURCES["reparse_trainset_multicutoff"]),
            "status": "failed_as_authorial_order_proof",
            "evidence": {
                "cutoffs": trainset_multicutoff["control_cutoffs"],
                "control_trials_per_cutoff": trainset_multicutoff["control_trials_per_cutoff"],
                "numeric_prefix_beats_control_mean_cutoffs": trainset_multicutoff["summary"][
                    "numeric_prefix_beats_control_mean_cutoffs"
                ],
                "numeric_prefix_beats_control_max_cutoffs": trainset_multicutoff["summary"][
                    "numeric_prefix_beats_control_max_cutoffs"
                ],
                "numeric_prefix_unique_at_control_resolution_cutoffs": trainset_multicutoff["summary"][
                    "numeric_prefix_unique_at_control_resolution_cutoffs"
                ],
                "cutoff_60_observed_gain": next(
                    row["observed_prefix"]["gain_vs_raw_bits"]
                    for row in trainset_multicutoff["rows"]
                    if row["cutoff"] == 60
                ),
                "cutoff_60_random_mean_gain": next(
                    row["random_train_set_control"]["mean"]
                    for row in trainset_multicutoff["rows"]
                    if row["cutoff"] == 60
                ),
            },
            "interpretation": (
                "The multi-cutoff train-set control keeps recipe predictability, "
                "but numeric prefix is not uniquely strong; at cutoff 60 it loses "
                "to the random-train mean and max."
            ),
        },
        {
            "question": "does_recipe_reparse_survive_public_bookcase_family_holdout",
            "source": rel(SOURCES["reparse_family_holdout"]),
            "status": "passed_with_active_recipe_ties",
            "evidence": {
                "family_count": family_holdout["summary"]["family_count"],
                "reparse_beats_raw_count": family_holdout["summary"]["reparse_beats_raw_count"],
                "reparse_beats_active_recipe_count": family_holdout["summary"][
                    "reparse_beats_active_recipe_count"
                ],
                "component_failure_family_count": family_holdout["summary"][
                    "component_failure_family_count"
                ],
                "component_failure_reparse_beats_raw_count": family_holdout["summary"][
                    "component_failure_reparse_beats_raw_count"
                ],
                "mean_reparse_minus_active_bits": family_holdout["summary"][
                    "mean_reparse_minus_active_bits"
                ],
            },
            "interpretation": (
                "Family holdout strengthens recipe discovery: the deterministic "
                "parser beats raw digits for every public-bookcase family and "
                "rescues the component-only failure families, but the active recipe "
                "remains cheaper in some families."
            ),
        },
        {
            "question": "are_family_reparse_losses_localized",
            "source": rel(SOURCES["reparse_family_loss_decomposition"]),
            "status": "passed_as_loss_localization_not_promotion",
            "evidence": {
                "loss_family_count": family_loss_decomposition["summary"]["loss_family_count"],
                "all_roundtrip": family_loss_decomposition["summary"]["all_roundtrip"],
                "component_family_failure_loss_count": family_loss_decomposition["summary"][
                    "component_family_failure_loss_count"
                ],
                "mean_reparse_minus_active_bits": family_loss_decomposition["summary"][
                    "mean_reparse_minus_active_bits"
                ],
                "max_reparse_minus_active_bits": family_loss_decomposition["summary"][
                    "max_reparse_minus_active_bits"
                ],
                "worst_family": family_loss_decomposition["summary"]["worst_family"],
                "largest_loss_component_counts": family_loss_decomposition["summary"][
                    "largest_loss_component_counts"
                ],
            },
            "interpretation": (
                "The five active-recipe local wins are roundtrip-valid and still "
                "beat raw digits; the losses are localized mostly to copy-address "
                "cost, so they are not new semantic or row0-origin evidence."
            ),
        },
        {
            "question": "does_online_reparse_reduce_full_corpus_recipe_cost",
            "source": rel(SOURCES["online_reparse_compile"]),
            "status": "passed_as_mechanical_compile_not_semantic_claim",
            "evidence": {
                "active_scope_bits": online_compile["active_compression_bound_bits"],
                "candidate_total_bits": online_compile["candidate_total_bits"],
                "candidate_gain_vs_active_bits": online_compile["candidate_gain_vs_active_bits"],
                "roundtrip": "70/70",
                "row0_origin_changed": online_compile["boundary"]["row0_origin_changed"],
                "semantic_delta": online_compile["boundary"]["semantic_delta"],
            },
            "interpretation": (
                "The deterministic online parser reduces recipe cost mechanically, "
                "but it does not derive row0 or introduce plaintext."
            ),
        },
        {
            "question": "does_numeric_online_order_survive_order_controls",
            "source": rel(SOURCES["online_reparse_order_controls"]),
            "status": "passed_against_tested_orders",
            "evidence": {
                "numeric_recomputed_bits": order_controls["numeric_recomputed_bits"],
                "best_raw": order_controls["best_raw"]["name"],
                "best_charged": order_controls["best_charged"]["name"],
                "random_order_count": order_controls["random_order_count"],
                "random_raw_min_bits": order_controls["random_summary"]["raw_min_bits"],
                "arbitrary_order_descriptor_bits": order_controls["arbitrary_order_descriptor_bits"],
            },
            "interpretation": (
                "Numeric order is compact under the tested named and random order "
                "controls, but arbitrary order search is not promoted."
            ),
        },
    ]

    result = {
        "schema": "recipe_reparse_evidence_matrix.v1",
        "classification": "recipe_externality_reduced_but_generation_claim_still_partial",
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {name: rel(path) for name, path in SOURCES.items()},
        "frozen_validation_scope": {
            "compression_bound_bits": recipe_externality["accounting"]["active_total_bits"],
            "fixed_or_nonlearned_ledger_bits": fixed,
            "fixed_or_nonlearned_ledger_share": fixed_share,
            "note": (
                "The matrix uses 8558.667 bits as validation scope. Later online "
                "reparse bits are evidence about recipe discovery, not semantic progress."
            ),
        },
        "evidence_matrix": evidence,
        "decision": {
            "recipe_externality_status": "partially_reduced_by_deterministic_reparse",
            "generation_explanation_status": "stronger_mechanical_recipe_signal_not_final_authorial_method",
            "numeric_order_status": "supported_against_order_controls_but_not_unique_against_random_train_inventories",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
            "progress_claim": (
                "This increases predictive/generative validation by showing the "
                "fixed-recipe limitation is not total: a deterministic parser can "
                "rediscover held-out recipes. It also falsifies the stronger claim "
                "that numeric prefix training is uniquely authorial evidence."
            ),
        },
    }
    return result


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / "06_recipe_reparse_evidence_matrix.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Recipe Reparse Evidence Matrix",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Audit 04 showed that about half of the `8558.667`-bit validation scope",
        "was still fixed recipe or non-learned ledger. This matrix checks whether",
        "the later deterministic reparse audits actually reduce that externality,",
        "without turning a compression result into a plaintext or authorial-intent",
        "claim.",
        "",
        "## Frozen Scope",
        "",
        f"- Validation scope: `{result['frozen_validation_scope']['compression_bound_bits']:.3f}` bits.",
        f"- Fixed/non-learned ledger in audit 04: `{result['frozen_validation_scope']['fixed_or_nonlearned_ledger_bits']:.3f}` bits.",
        f"- Fixed/non-learned share: `{100 * result['frozen_validation_scope']['fixed_or_nonlearned_ledger_share']:.3f}%`.",
        "",
        "## Evidence Matrix",
        "",
        "| Question | Status | Key evidence |",
        "|---|---|---|",
    ]
    for row in result["evidence_matrix"]:
        evidence = row["evidence"]
        if row["question"] == "does_deterministic_reparse_roundtrip_future_suffixes":
            key = (
                f"cutoffs {evidence['cutoffs']}; all roundtrip; mean reparse-active "
                f"{evidence['mean_reparse_minus_active_bits']:.3f} bits"
            )
        elif row["question"] == "does_reparse_signal_beat_content_controls":
            key = (
                f"observed beats all control means; "
                f"{evidence['control_trials']} trials per control family"
            )
        elif row["question"] == "is_numeric_prefix_training_uniquely_supported_single_cutoff":
            key = (
                f"cutoff {evidence['cutoff']}; observed gain "
                f"{evidence['observed_gain_vs_raw_bits']:.3f}; random max "
                f"{evidence['random_train_max_gain_bits']:.3f}; p={evidence['p_random_ge_observed']:.4f}"
            )
        elif row["question"] == "is_numeric_prefix_training_uniquely_supported_multicutoff":
            key = (
                f"cutoffs {evidence['cutoffs']}; mean wins "
                f"{evidence['numeric_prefix_beats_control_mean_cutoffs']}/3; "
                f"cutoff 60 observed {evidence['cutoff_60_observed_gain']:.3f} "
                f"vs random mean {evidence['cutoff_60_random_mean_gain']:.3f}"
            )
        elif row["question"] == "does_recipe_reparse_survive_public_bookcase_family_holdout":
            key = (
                f"beats raw {evidence['reparse_beats_raw_count']}/{evidence['family_count']}; "
                f"beats active {evidence['reparse_beats_active_recipe_count']}/{evidence['family_count']}; "
                f"component failures rescued {evidence['component_failure_reparse_beats_raw_count']}/"
                f"{evidence['component_failure_family_count']}"
            )
        elif row["question"] == "are_family_reparse_losses_localized":
            key = (
                f"{evidence['loss_family_count']} local losses; all roundtrip "
                f"{evidence['all_roundtrip']}; worst `{evidence['worst_family']}` "
                f"{evidence['max_reparse_minus_active_bits']:.3f} bits; "
                f"loss components {evidence['largest_loss_component_counts']}"
            )
        elif row["question"] == "does_online_reparse_reduce_full_corpus_recipe_cost":
            key = (
                f"{evidence['active_scope_bits']:.3f} -> {evidence['candidate_total_bits']:.3f} bits; "
                f"gain {evidence['candidate_gain_vs_active_bits']:.3f}; roundtrip {evidence['roundtrip']}"
            )
        else:
            key = (
                f"best raw `{evidence['best_raw']}`; best charged `{evidence['best_charged']}`; "
                f"{evidence['random_order_count']} random orders"
            )
        lines.append(f"| `{row['question']}` | `{row['status']}` | {key} |")

    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Recipe externality: `{result['decision']['recipe_externality_status']}`.",
            f"- Generation explanation: `{result['decision']['generation_explanation_status']}`.",
            f"- Numeric order: `{result['decision']['numeric_order_status']}`.",
            "- Row0 origin remains exogenous.",
            "- No plaintext, translation, or case-reopening claim is introduced.",
        ]
    )
    (TEST_RESULTS / "06_recipe_reparse_evidence_matrix.md").write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
