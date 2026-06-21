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
    "family_holdout_address_space": TEST_RESULTS / "10_family_holdout_address_space_audit.json",
    "family_holdout_address_corrected_scoreboard": TEST_RESULTS
    / "11_family_holdout_address_corrected_scoreboard.json",
    "family_holdout_no_test_carryover": TEST_RESULTS
    / "12_family_holdout_no_test_carryover_audit.json",
    "leave_one_book_out_no_self": TEST_RESULTS / "13_leave_one_book_out_no_self_audit.json",
    "leave_one_book_out_source_attribution": TEST_RESULTS
    / "14_leave_one_book_out_source_attribution_audit.json",
    "leave_one_book_out_book_bounded_source": TEST_RESULTS
    / "15_leave_one_book_out_book_bounded_source_audit.json",
    "leave_one_book_out_family_excluded_source": TEST_RESULTS
    / "16_leave_one_book_out_family_excluded_source_audit.json",
    "online_prefix_book_frontier": TEST_RESULTS / "17_online_prefix_book_frontier_audit.json",
    "online_bootstrap_seed_policy": TEST_RESULTS
    / "18_online_bootstrap_seed_policy_audit.json",
    "seeded_online_formula_rescore": TEST_RESULTS
    / "19_seeded_online_formula_rescore_audit.json",
    "seeded_rescore_loss_decomposition": TEST_RESULTS
    / "20_seeded_rescore_loss_decomposition.json",
    "seed_exception_signal_cost": TEST_RESULTS / "21_seed_exception_signal_cost_audit.json",
    "online_order_frontier_controls": TEST_RESULTS
    / "22_online_order_frontier_controls.json",
    "order_frontier_promotion_gate": TEST_RESULTS
    / "23_order_frontier_promotion_gate.json",
    "source_blocker_structural_context_gate": TEST_RESULTS
    / "24_source_blocker_structural_context_gate.json",
    "source_canonicality_decodability_gate": TEST_RESULTS
    / "25_source_canonicality_decodability_gate.json",
    "source_state_dependency_gate": TEST_RESULTS / "26_source_state_dependency_gate.json",
    "copy_length_midpoint_context_gate": TEST_RESULTS
    / "27_copy_length_midpoint_context_gate.json",
    "literal_copy_availability_gate": TEST_RESULTS / "28_literal_copy_availability_gate.json",
    "literal_payload_model_gate": TEST_RESULTS / "29_literal_payload_model_gate.json",
    "recipe_representation_dependency_gate": TEST_RESULTS
    / "30_recipe_representation_dependency_gate.json",
    "item_type_op_shape_boundary_gate": TEST_RESULTS
    / "33_item_type_op_shape_boundary_gate.json",
    "current_active_profile_boundary_gate": TEST_RESULTS
    / "34_current_active_profile_boundary_gate.json",
    "copy_source_state_compression_gate": TEST_RESULTS
    / "35_copy_source_state_compression_gate.json",
    "active_reparse_feasibility_after_state_compression_gate": TEST_RESULTS
    / "36_active_reparse_feasibility_after_state_compression_gate.json",
    "cutoff60_source_state_reparse_prototype_gate": TEST_RESULTS
    / "37_cutoff60_source_state_reparse_prototype_gate.json",
    "multicutoff_source_state_reparse_reprice_gate": TEST_RESULTS
    / "38_multicutoff_source_state_reparse_reprice_gate.json",
    "multicutoff_source_choice_optimizer_gate": TEST_RESULTS
    / "39_multicutoff_source_choice_optimizer_gate.json",
    "multicutoff_global_source_path_optimizer_gate": TEST_RESULTS
    / "40_multicutoff_global_source_path_optimizer_gate.json",
    "full_corpus_source_path_formula_gate": TEST_RESULTS
    / "41_full_corpus_source_path_formula_gate.json",
    "full_corpus_source_substitution_frontier_gate": TEST_RESULTS
    / "42_full_corpus_source_substitution_frontier_gate.json",
    "full_corpus_source_substitution_second_pass_gate": TEST_RESULTS
    / "43_full_corpus_source_substitution_second_pass_gate.json",
    "full_corpus_source_substitution_third_pass_gate": TEST_RESULTS
    / "44_full_corpus_source_substitution_third_pass_gate.json",
    "full_corpus_source_substitution_fourth_pass_gate": TEST_RESULTS
    / "45_full_corpus_source_substitution_fourth_pass_gate.json",
    "source_substitution_saturation_audit": TEST_RESULTS
    / "46_source_substitution_saturation_audit.json",
    "source_selection_derivation_boundary_gate": TEST_RESULTS
    / "31_source_selection_derivation_boundary_gate.json",
    "copy_length_derivation_boundary_gate": TEST_RESULTS
    / "32_copy_length_derivation_boundary_gate.json",
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
    address_space = load_json(SOURCES["family_holdout_address_space"])
    address_corrected = load_json(SOURCES["family_holdout_address_corrected_scoreboard"])
    no_test_carryover = load_json(SOURCES["family_holdout_no_test_carryover"])
    leave_one_out = load_json(SOURCES["leave_one_book_out_no_self"])
    source_attribution = load_json(SOURCES["leave_one_book_out_source_attribution"])
    book_bounded = load_json(SOURCES["leave_one_book_out_book_bounded_source"])
    family_excluded = load_json(SOURCES["leave_one_book_out_family_excluded_source"])
    online_frontier = load_json(SOURCES["online_prefix_book_frontier"])
    bootstrap_seed = load_json(SOURCES["online_bootstrap_seed_policy"])
    seeded_rescore = load_json(SOURCES["seeded_online_formula_rescore"])
    seeded_loss = load_json(SOURCES["seeded_rescore_loss_decomposition"])
    seed_signal = load_json(SOURCES["seed_exception_signal_cost"])
    order_frontier = load_json(SOURCES["online_order_frontier_controls"])
    promotion_gate = load_json(SOURCES["order_frontier_promotion_gate"])
    source_gate = load_json(SOURCES["source_blocker_structural_context_gate"])
    source_canonicality_gate = load_json(SOURCES["source_canonicality_decodability_gate"])
    source_state_gate = load_json(SOURCES["source_state_dependency_gate"])
    copy_length_midpoint_gate = load_json(SOURCES["copy_length_midpoint_context_gate"])
    literal_copy_gate = load_json(SOURCES["literal_copy_availability_gate"])
    literal_payload_model_gate = load_json(SOURCES["literal_payload_model_gate"])
    recipe_representation_gate = load_json(SOURCES["recipe_representation_dependency_gate"])
    item_type_op_shape_boundary_gate = load_json(SOURCES["item_type_op_shape_boundary_gate"])
    current_active_profile_gate = load_json(SOURCES["current_active_profile_boundary_gate"])
    copy_source_state_compression_gate = load_json(SOURCES["copy_source_state_compression_gate"])
    active_reparse_feasibility_gate = load_json(
        SOURCES["active_reparse_feasibility_after_state_compression_gate"]
    )
    source_state_reparse_prototype_gate = load_json(
        SOURCES["cutoff60_source_state_reparse_prototype_gate"]
    )
    multicutoff_source_state_reprice_gate = load_json(
        SOURCES["multicutoff_source_state_reparse_reprice_gate"]
    )
    source_choice_optimizer_gate = load_json(
        SOURCES["multicutoff_source_choice_optimizer_gate"]
    )
    global_source_path_optimizer_gate = load_json(
        SOURCES["multicutoff_global_source_path_optimizer_gate"]
    )
    full_corpus_source_path_formula_gate = load_json(
        SOURCES["full_corpus_source_path_formula_gate"]
    )
    full_corpus_source_substitution_frontier_gate = load_json(
        SOURCES["full_corpus_source_substitution_frontier_gate"]
    )
    full_corpus_source_substitution_second_pass_gate = load_json(
        SOURCES["full_corpus_source_substitution_second_pass_gate"]
    )
    full_corpus_source_substitution_third_pass_gate = load_json(
        SOURCES["full_corpus_source_substitution_third_pass_gate"]
    )
    full_corpus_source_substitution_fourth_pass_gate = load_json(
        SOURCES["full_corpus_source_substitution_fourth_pass_gate"]
    )
    source_substitution_saturation = load_json(
        SOURCES["source_substitution_saturation_audit"]
    )
    source_selection_gate = load_json(SOURCES["source_selection_derivation_boundary_gate"])
    copy_length_derivation_gate = load_json(SOURCES["copy_length_derivation_boundary_gate"])
    online_compile = load_json(SOURCES["online_reparse_compile"])
    order_controls = load_json(SOURCES["online_reparse_order_controls"])

    for name, data in [
        ("prequential_recipe_reparse", reparse),
        ("reparse_content_controls", content_controls),
        ("reparse_trainset_controls", trainset_controls),
        ("reparse_trainset_multicutoff", trainset_multicutoff),
        ("reparse_family_holdout", family_holdout),
        ("reparse_family_loss_decomposition", family_loss_decomposition),
        ("family_holdout_address_space", address_space),
        ("family_holdout_address_corrected_scoreboard", address_corrected),
        ("family_holdout_no_test_carryover", no_test_carryover),
        ("leave_one_book_out_no_self", leave_one_out),
        ("leave_one_book_out_source_attribution", source_attribution),
        ("leave_one_book_out_book_bounded_source", book_bounded),
        ("leave_one_book_out_family_excluded_source", family_excluded),
        ("online_prefix_book_frontier", online_frontier),
        ("online_bootstrap_seed_policy", bootstrap_seed),
        ("seeded_online_formula_rescore", seeded_rescore),
        ("seeded_rescore_loss_decomposition", seeded_loss),
        ("seed_exception_signal_cost", seed_signal),
        ("online_order_frontier_controls", order_frontier),
        ("order_frontier_promotion_gate", promotion_gate),
        ("source_blocker_structural_context_gate", source_gate),
        ("source_canonicality_decodability_gate", source_canonicality_gate),
        ("source_state_dependency_gate", source_state_gate),
        ("copy_length_midpoint_context_gate", copy_length_midpoint_gate),
        ("literal_copy_availability_gate", literal_copy_gate),
        ("literal_payload_model_gate", literal_payload_model_gate),
        ("recipe_representation_dependency_gate", recipe_representation_gate),
        ("item_type_op_shape_boundary_gate", item_type_op_shape_boundary_gate),
        ("current_active_profile_boundary_gate", current_active_profile_gate),
        ("copy_source_state_compression_gate", copy_source_state_compression_gate),
        (
            "active_reparse_feasibility_after_state_compression_gate",
            active_reparse_feasibility_gate,
        ),
        ("cutoff60_source_state_reparse_prototype_gate", source_state_reparse_prototype_gate),
        (
            "multicutoff_source_state_reparse_reprice_gate",
            multicutoff_source_state_reprice_gate,
        ),
        ("multicutoff_source_choice_optimizer_gate", source_choice_optimizer_gate),
        ("multicutoff_global_source_path_optimizer_gate", global_source_path_optimizer_gate),
        ("full_corpus_source_path_formula_gate", full_corpus_source_path_formula_gate),
        (
            "full_corpus_source_substitution_frontier_gate",
            full_corpus_source_substitution_frontier_gate,
        ),
        (
            "full_corpus_source_substitution_second_pass_gate",
            full_corpus_source_substitution_second_pass_gate,
        ),
        (
            "full_corpus_source_substitution_third_pass_gate",
            full_corpus_source_substitution_third_pass_gate,
        ),
        (
            "full_corpus_source_substitution_fourth_pass_gate",
            full_corpus_source_substitution_fourth_pass_gate,
        ),
        (
            "source_substitution_saturation_audit",
            source_substitution_saturation,
        ),
        ("source_selection_derivation_boundary_gate", source_selection_gate),
        ("copy_length_derivation_boundary_gate", copy_length_derivation_gate),
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
            "question": "do_family_copy_address_losses_survive_same_coordinate_repricing",
            "source": rel(SOURCES["family_holdout_address_space"]),
            "status": "failed_as_real_reparse_loss",
            "evidence": {
                "family_count": address_space["summary"]["family_count"],
                "all_rebased_active_roundtrip": address_space["summary"][
                    "all_rebased_active_roundtrip"
                ],
                "original_positive_address_loss_count": address_space["summary"][
                    "original_positive_address_loss_count"
                ],
                "rebased_nonpositive_address_loss_count": address_space["summary"][
                    "rebased_nonpositive_address_loss_count"
                ],
                "mean_original_address_delta_bits": address_space["summary"][
                    "mean_original_address_delta_bits"
                ],
                "mean_rebased_address_delta_bits": address_space["summary"][
                    "mean_rebased_address_delta_bits"
                ],
                "total_coordinate_shift_bits": address_space["summary"][
                    "total_coordinate_shift_bits"
                ],
                "epsilon_bits": address_space["epsilon_bits"],
            },
            "interpretation": (
                "The copy-address losses are a coordinate-comparison artifact: "
                "active original-coordinate address bits are not a fair family "
                "holdout comparator when held-out books are emitted after the "
                "training complement."
            ),
        },
        {
            "question": "does_family_holdout_reparse_beat_active_after_address_correction",
            "source": rel(SOURCES["family_holdout_address_corrected_scoreboard"]),
            "status": "passed_address_corrected_family_holdout",
            "evidence": {
                "family_count": address_corrected["summary"]["family_count"],
                "reparse_beats_raw_count": address_corrected["summary"][
                    "reparse_beats_raw_count"
                ],
                "original_reparse_beats_or_ties_active_count": address_corrected["summary"][
                    "original_reparse_beats_or_ties_active_count"
                ],
                "address_corrected_reparse_beats_or_ties_active_count": address_corrected[
                    "summary"
                ]["address_corrected_reparse_beats_or_ties_active_count"],
                "mean_original_reparse_minus_active_bits": address_corrected["summary"][
                    "mean_original_reparse_minus_active_bits"
                ],
                "mean_address_corrected_reparse_minus_active_bits": address_corrected[
                    "summary"
                ]["mean_address_corrected_reparse_minus_active_bits"],
                "address_corrected_worse_labels": address_corrected["summary"][
                    "address_corrected_worse_labels"
                ],
            },
            "interpretation": (
                "Under same-coordinate copy-address costs, deterministic reparse "
                "beats or ties the active family recipe for every public-bookcase "
                "family. This strengthens predictive recipe validation while "
                "leaving row0 and semantics unchanged."
            ),
        },
        {
            "question": "does_family_holdout_reparse_depend_on_test_carryover",
            "source": rel(SOURCES["family_holdout_no_test_carryover"]),
            "status": "passed_no_test_carryover_raw_baseline",
            "evidence": {
                "family_count": no_test_carryover["summary"]["family_count"],
                "roundtrip_family_count": no_test_carryover["summary"][
                    "roundtrip_family_count"
                ],
                "no_test_carryover_beats_raw_count": no_test_carryover["summary"][
                    "no_test_carryover_beats_raw_count"
                ],
                "standard_reparse_beats_raw_count": no_test_carryover["summary"][
                    "standard_reparse_beats_raw_count"
                ],
                "mean_no_test_carryover_gain_vs_raw_bits": no_test_carryover["summary"][
                    "mean_no_test_carryover_gain_vs_raw_bits"
                ],
                "mean_standard_gain_vs_raw_bits": no_test_carryover["summary"][
                    "mean_standard_gain_vs_raw_bits"
                ],
                "failure_labels": no_test_carryover["summary"]["failure_labels"],
            },
            "interpretation": (
                "The positive public-bookcase family signal does not require "
                "cross-book carryover inside the held-out family: each held-out "
                "book still beats raw digit coding when parsed from the training "
                "complement alone."
            ),
        },
        {
            "question": "does_single_book_holdout_reparse_without_self",
            "source": rel(SOURCES["leave_one_book_out_no_self"]),
            "status": "passed_singleton_complement_inventory",
            "evidence": {
                "book_count": leave_one_out["summary"]["book_count"],
                "roundtrip_book_count": leave_one_out["summary"]["roundtrip_book_count"],
                "beats_raw_count": leave_one_out["summary"]["beats_raw_count"],
                "mean_gain_vs_raw_bits": leave_one_out["summary"]["mean_gain_vs_raw_bits"],
                "min_gain_vs_raw_bits": leave_one_out["summary"]["min_gain_vs_raw_bits"],
                "max_gain_vs_raw_bits": leave_one_out["summary"]["max_gain_vs_raw_bits"],
                "failure_books": leave_one_out["summary"]["failure_books"],
                "weakest_books": leave_one_out["summary"]["weakest_books"][:5],
            },
            "interpretation": (
                "Every individual book can be mechanically reparsed from the "
                "other 69 books with positive gain versus raw digit coding. This "
                "is item-level redundancy evidence, not an authorial-order proof."
            ),
        },
        {
            "question": "where_do_singleton_holdout_copies_source_from",
            "source": rel(SOURCES["leave_one_book_out_source_attribution"]),
            "status": "mapped_with_boundary_caveat",
            "evidence": {
                "book_count": source_attribution["summary"]["book_count"],
                "roundtrip_book_count": source_attribution["summary"]["roundtrip_book_count"],
                "total_copy_items": source_attribution["summary"]["total_copy_items"],
                "total_copied_digits": source_attribution["summary"]["total_copied_digits"],
                "total_cross_boundary_copy_items": source_attribution["summary"][
                    "total_cross_boundary_copy_items"
                ],
                "cross_boundary_copied_digit_share": source_attribution["summary"][
                    "cross_boundary_copied_digit_share"
                ],
                "current_prefix_copied_digits": source_attribution["summary"][
                    "current_prefix_copied_digits"
                ],
                "current_prefix_copied_digit_share": source_attribution["summary"][
                    "current_prefix_copied_digit_share"
                ],
                "mean_distinct_source_books_per_target": source_attribution["summary"][
                    "mean_distinct_source_books_per_target"
                ],
                "mean_top_source_share": source_attribution["summary"]["mean_top_source_share"],
            },
            "interpretation": (
                "Singleton holdout copies are now attributable to source books "
                "or the already-emitted current prefix. The map also exposes a "
                "boundary caveat: many copied digits cross artificial boundaries "
                "created by concatenating source books without separators."
            ),
        },
        {
            "question": "does_singleton_holdout_survive_book_bounded_sources",
            "source": rel(SOURCES["leave_one_book_out_book_bounded_source"]),
            "status": "passed_book_bounded_source_constraint",
            "evidence": {
                "book_count": book_bounded["summary"]["book_count"],
                "roundtrip_book_count": book_bounded["summary"]["roundtrip_book_count"],
                "beats_raw_count": book_bounded["summary"]["beats_raw_count"],
                "mean_book_bounded_gain_vs_raw_bits": book_bounded["summary"][
                    "mean_book_bounded_gain_vs_raw_bits"
                ],
                "min_book_bounded_gain_vs_raw_bits": book_bounded["summary"][
                    "min_book_bounded_gain_vs_raw_bits"
                ],
                "mean_book_bounded_minus_unbounded_bits": book_bounded["summary"][
                    "mean_book_bounded_minus_unbounded_bits"
                ],
                "max_book_bounded_minus_unbounded_bits": book_bounded["summary"][
                    "max_book_bounded_minus_unbounded_bits"
                ],
                "failure_books": book_bounded["summary"]["failure_books"],
            },
            "interpretation": (
                "Forbidding copy sources from crossing source-book boundaries "
                "preserves positive singleton holdout gain for every book. The "
                "boundary caveat is therefore not required for the item-level "
                "predictive signal."
            ),
        },
        {
            "question": "does_singleton_holdout_survive_same_family_source_exclusion",
            "source": rel(SOURCES["leave_one_book_out_family_excluded_source"]),
            "status": "passed_family_excluded_source_constraint",
            "evidence": {
                "book_count": family_excluded["summary"]["book_count"],
                "family_labeled_book_count": family_excluded["summary"][
                    "family_labeled_book_count"
                ],
                "roundtrip_book_count": family_excluded["summary"]["roundtrip_book_count"],
                "beats_raw_count": family_excluded["summary"]["beats_raw_count"],
                "family_labeled_beats_raw_count": family_excluded["summary"][
                    "family_labeled_beats_raw_count"
                ],
                "mean_family_excluded_gain_vs_raw_bits": family_excluded["summary"][
                    "mean_family_excluded_gain_vs_raw_bits"
                ],
                "min_family_excluded_gain_vs_raw_bits": family_excluded["summary"][
                    "min_family_excluded_gain_vs_raw_bits"
                ],
                "mean_family_excluded_minus_book_bounded_bits": family_excluded["summary"][
                    "mean_family_excluded_minus_book_bounded_bits"
                ],
                "max_family_excluded_minus_book_bounded_bits": family_excluded["summary"][
                    "max_family_excluded_minus_book_bounded_bits"
                ],
                "failure_books": family_excluded["summary"]["failure_books"],
                "weakest_books": family_excluded["summary"]["weakest_books"][:5],
            },
            "interpretation": (
                "For books with known public-bookcase family labels, removing the "
                "entire same family from frozen train counts and copy sources still "
                "preserves positive singleton holdout gain. Same-family source "
                "memorization is therefore not required for the observed item-level "
                "signal."
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
            "question": "which_recipe_fields_are_derivable_representation_artifacts",
            "source": rel(SOURCES["recipe_representation_dependency_gate"]),
            "status": "passed_derivable_fields_removed_dependencies_retained",
            "evidence": {
                "active_bits": recipe_representation_gate["summary"]["active_bits"],
                "final_type_derived_bits": recipe_representation_gate["summary"][
                    "final_type_derived_bits"
                ],
                "score_delta_bits": recipe_representation_gate["summary"][
                    "score_delta_bits"
                ],
                "removed_book_length_fields": recipe_representation_gate["summary"][
                    "removed_book_length_fields"
                ],
                "removed_copy_target_start_fields": recipe_representation_gate[
                    "summary"
                ]["removed_copy_target_start_fields"],
                "removed_literal_length_fields": recipe_representation_gate[
                    "summary"
                ]["removed_literal_length_fields"],
                "removed_type_fields": recipe_representation_gate["summary"][
                    "removed_type_fields"
                ],
                "removed_independent_field_count": recipe_representation_gate[
                    "summary"
                ]["removed_independent_field_count"],
                "total_recipe_json_byte_saving": recipe_representation_gate[
                    "summary"
                ]["total_recipe_json_byte_saving"],
                "remaining_declared_dependencies": recipe_representation_gate[
                    "summary"
                ]["remaining_declared_dependencies"],
            },
            "interpretation": (
                "Book length, copy target_start, literal length, and op type are "
                "derivable in the compact recipe; literal text, copy source, and "
                "copy length remain declared dependencies."
            ),
        },
        {
            "question": "is_item_type_sequence_or_recipe_type_field_dependency",
            "source": rel(SOURCES["item_type_op_shape_boundary_gate"]),
            "status": "split_only_sequence_retained_op_type_field_derived",
            "evidence": {
                "split_only_gain_bits": item_type_op_shape_boundary_gate["summary"][
                    "split_only_gain_bits"
                ],
                "split_only_conservative_gain_bits": item_type_op_shape_boundary_gate[
                    "summary"
                ]["split_only_conservative_gain_bits"],
                "active_item_type_bits": item_type_op_shape_boundary_gate["summary"][
                    "active_item_type_bits"
                ],
                "split_only_item_type_bits": item_type_op_shape_boundary_gate[
                    "summary"
                ]["split_only_item_type_bits"],
                "coded_item_type_items": item_type_op_shape_boundary_gate["summary"][
                    "coded_item_type_items"
                ],
                "forced_item_type_items": item_type_op_shape_boundary_gate["summary"][
                    "forced_item_type_items"
                ],
                "forced_rule_violations": item_type_op_shape_boundary_gate["summary"][
                    "forced_rule_violations"
                ],
                "current_alpha": item_type_op_shape_boundary_gate["summary"][
                    "current_alpha"
                ],
                "best_alpha": item_type_op_shape_boundary_gate["summary"]["best_alpha"],
                "nearest_alpha1_delta_bits": item_type_op_shape_boundary_gate["summary"][
                    "nearest_alpha1_delta_bits"
                ],
                "op_type_fields_removed": item_type_op_shape_boundary_gate["summary"][
                    "op_type_fields_removed"
                ],
                "literal_shape_ops": item_type_op_shape_boundary_gate["summary"][
                    "literal_shape_ops"
                ],
                "copy_shape_ops": item_type_op_shape_boundary_gate["summary"][
                    "copy_shape_ops"
                ],
                "ambiguous_shape_ops": item_type_op_shape_boundary_gate["summary"][
                    "ambiguous_shape_ops"
                ],
                "op_type_score_delta_bits": item_type_op_shape_boundary_gate["summary"][
                    "op_type_score_delta_bits"
                ],
                "op_type_roundtrip_ok": item_type_op_shape_boundary_gate["summary"][
                    "op_type_roundtrip_ok"
                ],
            },
            "interpretation": (
                "The split-only item-type stream remains a mechanical component, "
                "while the explicit op type field in compact recipe JSON is a "
                "derivable representation artifact."
            ),
        },
        {
            "question": "is_current_active_8177_profile_validated_or_recipe_discovered",
            "source": rel(SOURCES["current_active_profile_boundary_gate"]),
            "status": "active_profile_validated_recipe_discovery_blocked",
            "evidence": {
                "active_compression_bound_bits": current_active_profile_gate["summary"][
                    "active_compression_bound_bits"
                ],
                "copy_length_default_exception_bits": current_active_profile_gate[
                    "summary"
                ]["copy_length_default_exception_bits"],
                "copy_length_gain_bits": current_active_profile_gate["summary"][
                    "copy_length_gain_bits"
                ],
                "copy_source_default_exception_bits": current_active_profile_gate[
                    "summary"
                ]["copy_source_default_exception_bits"],
                "copy_source_gain_bits": current_active_profile_gate["summary"][
                    "copy_source_gain_bits"
                ],
                "learned_component_stream_share_pct": current_active_profile_gate[
                    "summary"
                ]["learned_component_stream_share_pct"],
                "fixed_recipe_or_declaration_bits": current_active_profile_gate[
                    "summary"
                ]["fixed_recipe_or_declaration_bits"],
                "active_prefix_frozen_min_gain_bits": current_active_profile_gate[
                    "summary"
                ]["active_prefix_gain_summary"]["frozen_min_gain_bits"],
                "active_block_frozen_min_gain_bits": current_active_profile_gate[
                    "summary"
                ]["active_block_gain_summary"]["frozen_min_gain_bits"],
                "active_family_frozen_min_gain_bits": current_active_profile_gate[
                    "summary"
                ]["active_family_gain_summary"]["frozen_min_gain_bits"],
                "active_family_frozen_nonpositive_count": current_active_profile_gate[
                    "summary"
                ]["active_family_gain_summary"]["frozen_nonpositive_count"],
                "default_exception_only_family_frozen_nonpositive_count": (
                    current_active_profile_gate["summary"][
                        "default_exception_validation_family_nonpositive_frozen_count"
                    ]
                ),
                "recipe_discovery_proved": current_active_profile_gate["summary"][
                    "recipe_discovery_proved"
                ],
                "active_reparse_state_key_required": current_active_profile_gate[
                    "summary"
                ]["active_reparse_state_key_required"],
                "cutoff10_state_proxy": current_active_profile_gate["summary"][
                    "cutoff10_state_proxy"
                ],
                "cutoff10_old_reparse_state_count": current_active_profile_gate[
                    "summary"
                ]["cutoff10_old_reparse_state_count"],
                "best_state_free_default": current_active_profile_gate["summary"][
                    "best_state_free_default"
                ],
                "best_state_free_worse_than_active_total_bits": (
                    current_active_profile_gate["summary"][
                        "best_state_free_worse_than_active_total_bits"
                    ]
                ),
            },
            "interpretation": (
                "The active 8177-bit component profile is stronger than the "
                "default/exception-only validation, but exact active reparse is "
                "still path-state-bound and recipe discovery is not proved."
            ),
        },
        {
            "question": "can_copy_source_previous_pair_state_be_compressed",
            "source": rel(SOURCES["copy_source_state_compression_gate"]),
            "status": "previous_pair_state_compressed_to_previous_end",
            "evidence": {
                "previous_pair_state_key": copy_source_state_compression_gate["summary"][
                    "previous_pair_state_key"
                ],
                "compressed_state_key": copy_source_state_compression_gate["summary"][
                    "compressed_state_key"
                ],
                "source_default_stream_bits": copy_source_state_compression_gate[
                    "summary"
                ]["source_default_stream_bits"],
                "source_default_count": copy_source_state_compression_gate["summary"][
                    "source_default_count"
                ],
                "source_exception_count": copy_source_state_compression_gate["summary"][
                    "source_exception_count"
                ],
                "end_default_mismatch_count": copy_source_state_compression_gate[
                    "summary"
                ]["end_default_mismatch_count"],
                "total_pair_state_proxy": copy_source_state_compression_gate[
                    "summary"
                ]["total_pair_state_proxy"],
                "total_end_state_proxy": copy_source_state_compression_gate["summary"][
                    "total_end_state_proxy"
                ],
                "total_end_proxy_reduction_pct": copy_source_state_compression_gate[
                    "summary"
                ]["total_end_proxy_reduction_pct"],
                "cutoff10_pair_state_proxy": copy_source_state_compression_gate[
                    "summary"
                ]["cutoff_rows"][0]["candidate_graph_summary"]["pair_state_proxy"],
                "cutoff10_end_state_proxy": copy_source_state_compression_gate[
                    "summary"
                ]["cutoff_rows"][0]["candidate_graph_summary"]["end_state_proxy"],
                "parser_promoted": copy_source_state_compression_gate["summary"][
                    "parser_promoted"
                ],
                "recipe_discovery_removed": copy_source_state_compression_gate[
                    "summary"
                ]["recipe_discovery_removed"],
            },
            "interpretation": (
                "The active source default only needs previous copy end, not the "
                "full previous source/length pair. This reduces state size but "
                "does not promote a complete active parser."
            ),
        },
        {
            "question": "does_source_state_compression_make_active_reparse_feasible",
            "source": rel(
                SOURCES["active_reparse_feasibility_after_state_compression_gate"]
            ),
            "status": "source_state_dimension_reduced_parser_unpromoted",
            "evidence": {
                "old_state_key": active_reparse_feasibility_gate["summary"][
                    "old_state_key"
                ],
                "pre_compression_required_state_key": active_reparse_feasibility_gate[
                    "summary"
                ]["pre_compression_required_state_key"],
                "compressed_source_state_key": active_reparse_feasibility_gate[
                    "summary"
                ]["compressed_source_state_key"],
                "total_pair_state_proxy": active_reparse_feasibility_gate["summary"][
                    "total_pair_state_proxy"
                ],
                "total_end_state_proxy": active_reparse_feasibility_gate["summary"][
                    "total_end_state_proxy"
                ],
                "total_pair_to_end_proxy_reduction_pct": (
                    active_reparse_feasibility_gate["summary"][
                        "total_pair_to_end_proxy_reduction_pct"
                    ]
                ),
                "total_end_proxy_multiplier_over_old_reparse": (
                    active_reparse_feasibility_gate["summary"][
                        "total_end_proxy_multiplier_over_old_reparse"
                    ]
                ),
                "max_book_end_state_proxy": active_reparse_feasibility_gate[
                    "summary"
                ]["max_book_end_state_proxy"],
                "all_books_below_1m_end_state_proxy": active_reparse_feasibility_gate[
                    "summary"
                ]["all_books_below_1m_end_state_proxy"],
                "cutoff60_max_book_end_state_proxy": active_reparse_feasibility_gate[
                    "summary"
                ]["cutoff60_max_book_end_state_proxy"],
                "cutoff60_books_below_250k": active_reparse_feasibility_gate[
                    "summary"
                ]["cutoff60_books_below_250k"],
                "cutoff60_book_count": active_reparse_feasibility_gate["summary"][
                    "cutoff60_book_count"
                ],
                "parser_promoted": active_reparse_feasibility_gate["summary"][
                    "parser_promoted"
                ],
                "recipe_discovery_removed": active_reparse_feasibility_gate[
                    "summary"
                ]["recipe_discovery_removed"],
                "remaining_blockers": active_reparse_feasibility_gate["summary"][
                    "remaining_blockers"
                ],
            },
            "interpretation": (
                "Previous-copy-end compression makes book-local source-state "
                "prototypes plausible by proxy, but exact active reparse remains "
                "unpromoted because the full objective and remaining recipe "
                "dependencies are still unresolved."
            ),
        },
        {
            "question": "does_cutoff60_reparse_execute_with_source_state_repricing",
            "source": rel(SOURCES["cutoff60_source_state_reparse_prototype_gate"]),
            "status": "cutoff60_source_state_reprice_roundtrip_positive_unpromoted",
            "evidence": {
                "roundtrip_book_count": source_state_reparse_prototype_gate["summary"][
                    "roundtrip_book_count"
                ],
                "book_count": source_state_reparse_prototype_gate["summary"][
                    "book_count"
                ],
                "beats_raw_book_count": source_state_reparse_prototype_gate["summary"][
                    "beats_raw_book_count"
                ],
                "beats_uniform_address_reparse_book_count": (
                    source_state_reparse_prototype_gate["summary"][
                        "beats_uniform_address_reparse_book_count"
                    ]
                ),
                "source_state_bits": source_state_reparse_prototype_gate["summary"][
                    "aggregate"
                ]["bits"],
                "uniform_address_reparse_bits": source_state_reparse_prototype_gate[
                    "summary"
                ]["aggregate"]["uniform_address_reparse_bits"],
                "source_state_minus_uniform_address_bits": (
                    source_state_reparse_prototype_gate["summary"]["aggregate"][
                        "source_state_minus_uniform_address_bits"
                    ]
                ),
                "gain_vs_raw_digit_uniform_bits": source_state_reparse_prototype_gate[
                    "summary"
                ]["aggregate"]["gain_vs_raw_digit_uniform_bits"],
                "source_default_count": source_state_reparse_prototype_gate[
                    "summary"
                ]["aggregate"]["source_default_count"],
                "source_exception_count": source_state_reparse_prototype_gate[
                    "summary"
                ]["aggregate"]["source_exception_count"],
                "not_recipe_reoptimization": source_state_reparse_prototype_gate[
                    "scope"
                ]["not_recipe_reoptimization"],
            },
            "interpretation": (
                "The compressed source-state ledger can be executed on cutoff-60 "
                "deterministic reparse recipes and is cheaper than uniform source "
                "addresses in aggregate, but it is a repricing test rather than "
                "source-state recipe reoptimization."
            ),
        },
        {
            "question": "does_source_state_repricing_generalize_across_prefix_cutoffs",
            "source": rel(SOURCES["multicutoff_source_state_reparse_reprice_gate"]),
            "status": "multicutoff_source_state_reprice_generalizes_aggregate_unpromoted",
            "evidence": {
                "cutoff_count": multicutoff_source_state_reprice_gate["summary"][
                    "cutoff_count"
                ],
                "all_roundtrip": multicutoff_source_state_reprice_gate["summary"][
                    "all_roundtrip"
                ],
                "all_books_beat_raw": multicutoff_source_state_reprice_gate[
                    "summary"
                ]["all_books_beat_raw"],
                "aggregate_beats_uniform_cutoff_count": (
                    multicutoff_source_state_reprice_gate["summary"][
                        "aggregate_beats_uniform_cutoff_count"
                    ]
                ),
                "total_source_state_bits": multicutoff_source_state_reprice_gate[
                    "summary"
                ]["total_source_state_bits"],
                "total_uniform_address_reparse_bits": (
                    multicutoff_source_state_reprice_gate["summary"][
                        "total_uniform_address_reparse_bits"
                    ]
                ),
                "total_source_state_minus_uniform_address_bits": (
                    multicutoff_source_state_reprice_gate["summary"][
                        "total_source_state_minus_uniform_address_bits"
                    ]
                ),
                "total_source_defaults": multicutoff_source_state_reprice_gate[
                    "summary"
                ]["total_source_defaults"],
                "total_source_exceptions": multicutoff_source_state_reprice_gate[
                    "summary"
                ]["total_source_exceptions"],
                "not_recipe_reoptimization": multicutoff_source_state_reprice_gate[
                    "scope"
                ]["not_recipe_reoptimization"],
            },
            "interpretation": (
                "Source-state repricing generalizes over the standard prefix "
                "cutoffs in aggregate while preserving roundtrip and raw-digit "
                "wins, but it still reprices deterministic recipes rather than "
                "discovering source-state-optimal recipes."
            ),
        },
        {
            "question": "can_fixed_segmentation_source_choice_improve_repricing",
            "source": rel(SOURCES["multicutoff_source_choice_optimizer_gate"]),
            "status": "failed_no_cheaper_source_choices_found",
            "evidence": {
                "cutoff_count": source_choice_optimizer_gate["summary"][
                    "cutoff_count"
                ],
                "all_roundtrip": source_choice_optimizer_gate["summary"][
                    "all_roundtrip"
                ],
                "all_books_beat_raw": source_choice_optimizer_gate["summary"][
                    "all_books_beat_raw"
                ],
                "aggregate_beats_reprice_cutoff_count": source_choice_optimizer_gate[
                    "summary"
                ]["aggregate_beats_reprice_cutoff_count"],
                "aggregate_beats_uniform_cutoff_count": source_choice_optimizer_gate[
                    "summary"
                ]["aggregate_beats_uniform_cutoff_count"],
                "total_bits": source_choice_optimizer_gate["summary"]["total_bits"],
                "total_reprice_bits": source_choice_optimizer_gate["summary"][
                    "total_reprice_bits"
                ],
                "total_source_choice_minus_reprice_bits": source_choice_optimizer_gate[
                    "summary"
                ]["total_source_choice_minus_reprice_bits"],
                "total_source_choice_minus_uniform_address_bits": source_choice_optimizer_gate[
                    "summary"
                ]["total_source_choice_minus_uniform_address_bits"],
                "total_changed_sources": source_choice_optimizer_gate["summary"][
                    "total_changed_sources"
                ],
                "total_copy_items": source_choice_optimizer_gate["summary"][
                    "total_copy_items"
                ],
                "not_segmentation_reoptimization": source_choice_optimizer_gate[
                    "scope"
                ]["not_segmentation_reoptimization"],
            },
            "interpretation": (
                "A greedy source-choice optimizer over fixed segmentation and "
                "copy lengths changes no sources. The next source-state advance "
                "therefore needs segmentation, copy-length, or global path-state "
                "optimization rather than local source substitution."
            ),
        },
        {
            "question": "can_global_source_path_improve_fixed_segmentation",
            "source": rel(SOURCES["multicutoff_global_source_path_optimizer_gate"]),
            "status": "passed_partial_global_source_path_improves_reprice",
            "evidence": {
                "cutoff_count": global_source_path_optimizer_gate["summary"][
                    "cutoff_count"
                ],
                "all_roundtrip": global_source_path_optimizer_gate["summary"][
                    "all_roundtrip"
                ],
                "all_books_beat_raw": global_source_path_optimizer_gate["summary"][
                    "all_books_beat_raw"
                ],
                "aggregate_beats_reprice_cutoff_count": global_source_path_optimizer_gate[
                    "summary"
                ]["aggregate_beats_reprice_cutoff_count"],
                "total_bits": global_source_path_optimizer_gate["summary"][
                    "total_bits"
                ],
                "total_reprice_bits": global_source_path_optimizer_gate["summary"][
                    "total_reprice_bits"
                ],
                "total_source_path_minus_reprice_bits": global_source_path_optimizer_gate[
                    "summary"
                ]["total_source_path_minus_reprice_bits"],
                "total_source_path_minus_uniform_address_bits": global_source_path_optimizer_gate[
                    "summary"
                ]["total_source_path_minus_uniform_address_bits"],
                "total_changed_sources": global_source_path_optimizer_gate["summary"][
                    "total_changed_sources"
                ],
                "total_copy_events": global_source_path_optimizer_gate["summary"][
                    "total_copy_events"
                ],
                "total_source_defaults": global_source_path_optimizer_gate["summary"][
                    "total_source_defaults"
                ],
                "total_source_exceptions": global_source_path_optimizer_gate[
                    "summary"
                ]["total_source_exceptions"],
                "max_state_count": global_source_path_optimizer_gate["summary"][
                    "max_state_count"
                ],
                "total_transition_count": global_source_path_optimizer_gate[
                    "summary"
                ]["total_transition_count"],
                "not_segmentation_reoptimization": global_source_path_optimizer_gate[
                    "scope"
                ]["not_segmentation_reoptimization"],
            },
            "interpretation": (
                "A global DP over source choices improves the fixed deterministic "
                "reparse recipes under `previous_copy_end`, proving that the "
                "remaining source-state value is path-dependent rather than local. "
                "Segmentation and copy lengths remain fixed."
            ),
        },
        {
            "question": "can_full_corpus_source_path_improve_formula_bound",
            "source": rel(SOURCES["full_corpus_source_path_formula_gate"]),
            "status": "passed_fixed_recipe_source_path_formula_improves_bound",
            "evidence": {
                "active_total_bits": full_corpus_source_path_formula_gate["summary"][
                    "active_total_bits"
                ],
                "candidate_total_bits": full_corpus_source_path_formula_gate[
                    "summary"
                ]["candidate_total_bits"],
                "candidate_gain_bits": full_corpus_source_path_formula_gate[
                    "summary"
                ]["candidate_gain_bits"],
                "active_copy_source_bits": full_corpus_source_path_formula_gate[
                    "summary"
                ]["active_copy_source_bits"],
                "candidate_copy_source_bits": full_corpus_source_path_formula_gate[
                    "summary"
                ]["candidate_copy_source_bits"],
                "adaptive_copy_source_delta_bits": full_corpus_source_path_formula_gate[
                    "summary"
                ]["adaptive_copy_source_delta_bits"],
                "frozen_source_delta_bits": full_corpus_source_path_formula_gate[
                    "summary"
                ]["frozen_source_delta_bits"],
                "changed_source_count": full_corpus_source_path_formula_gate[
                    "summary"
                ]["changed_source_count"],
                "copy_event_count": full_corpus_source_path_formula_gate["summary"][
                    "copy_event_count"
                ],
                "candidate_count": full_corpus_source_path_formula_gate["summary"][
                    "candidate_count"
                ],
                "source_default_count": full_corpus_source_path_formula_gate[
                    "summary"
                ]["source_default_count"],
                "source_exception_count": full_corpus_source_path_formula_gate[
                    "summary"
                ]["source_exception_count"],
                "max_state_count": full_corpus_source_path_formula_gate["summary"][
                    "max_state_count"
                ],
                "candidate_output_formula": full_corpus_source_path_formula_gate[
                    "candidate_output_formula"
                ],
                "fixed_segmentation": full_corpus_source_path_formula_gate["scope"][
                    "fixed_segmentation"
                ],
                "fixed_copy_lengths": full_corpus_source_path_formula_gate["scope"][
                    "fixed_copy_lengths"
                ],
            },
            "interpretation": (
                "The full-corpus source-path candidate survives the real adaptive "
                "source-stream rescore and lowers the compression bound. This is "
                "a fixed-recipe source-path improvement, not complete parser "
                "discovery."
            ),
        },
        {
            "question": "can_single_pair_source_substitution_improve_formula_bound",
            "source": rel(SOURCES["full_corpus_source_substitution_frontier_gate"]),
            "status": "passed_single_pair_source_substitution_improves_bound",
            "evidence": {
                "active_total_bits": full_corpus_source_substitution_frontier_gate[
                    "summary"
                ]["active_total_bits"],
                "candidate_total_bits": full_corpus_source_substitution_frontier_gate[
                    "summary"
                ]["candidate_total_bits"],
                "candidate_gain_bits": full_corpus_source_substitution_frontier_gate[
                    "summary"
                ]["candidate_gain_bits"],
                "active_copy_source_bits": full_corpus_source_substitution_frontier_gate[
                    "summary"
                ]["active_copy_source_bits"],
                "candidate_copy_source_bits": full_corpus_source_substitution_frontier_gate[
                    "summary"
                ]["candidate_copy_source_bits"],
                "copy_event_count": full_corpus_source_substitution_frontier_gate[
                    "summary"
                ]["copy_event_count"],
                "single_substitution_count": full_corpus_source_substitution_frontier_gate[
                    "summary"
                ]["single_substitution_count"],
                "positive_single_count": full_corpus_source_substitution_frontier_gate[
                    "summary"
                ]["positive_single_count"],
                "pair_substitution_count": full_corpus_source_substitution_frontier_gate[
                    "summary"
                ]["pair_substitution_count"],
                "positive_pair_count": full_corpus_source_substitution_frontier_gate[
                    "summary"
                ]["positive_pair_count"],
                "best_arity": full_corpus_source_substitution_frontier_gate[
                    "summary"
                ]["best_arity"],
                "candidate_output_formula": full_corpus_source_substitution_frontier_gate[
                    "candidate_output_formula"
                ],
                "searched_triples_or_higher": full_corpus_source_substitution_frontier_gate[
                    "scope"
                ]["searched_triples_or_higher"],
            },
            "interpretation": (
                "Exact single and pair same-chunk source substitution search "
                "finds one further fixed-recipe source improvement. This lowers "
                "the bound but leaves triples/higher and active parser discovery "
                "outside the gate."
            ),
        },
        {
            "question": "does_second_pass_single_pair_source_substitution_still_improve",
            "source": rel(SOURCES["full_corpus_source_substitution_second_pass_gate"]),
            "status": "passed_microscopic_second_pass_source_substitution_improves_bound",
            "evidence": {
                "active_total_bits": full_corpus_source_substitution_second_pass_gate[
                    "summary"
                ]["active_total_bits"],
                "candidate_total_bits": full_corpus_source_substitution_second_pass_gate[
                    "summary"
                ]["candidate_total_bits"],
                "candidate_gain_bits": full_corpus_source_substitution_second_pass_gate[
                    "summary"
                ]["candidate_gain_bits"],
                "single_substitution_count": full_corpus_source_substitution_second_pass_gate[
                    "summary"
                ]["single_substitution_count"],
                "positive_single_count": full_corpus_source_substitution_second_pass_gate[
                    "summary"
                ]["positive_single_count"],
                "pair_substitution_count": full_corpus_source_substitution_second_pass_gate[
                    "summary"
                ]["pair_substitution_count"],
                "positive_pair_count": full_corpus_source_substitution_second_pass_gate[
                    "summary"
                ]["positive_pair_count"],
                "best_arity": full_corpus_source_substitution_second_pass_gate[
                    "summary"
                ]["best_arity"],
                "searched_triples_or_higher": full_corpus_source_substitution_second_pass_gate[
                    "scope"
                ]["searched_triples_or_higher"],
            },
            "interpretation": (
                "The second pass finds only a microscopic single/pair source "
                "substitution improvement. This is counted as a compression-bound "
                "step, not as a stronger generation explanation."
            ),
        },
        {
            "question": "does_third_pass_single_pair_source_substitution_still_improve",
            "source": rel(SOURCES["full_corpus_source_substitution_third_pass_gate"]),
            "status": "passed_microscopic_third_pass_source_substitution_improves_bound",
            "evidence": {
                "active_total_bits": full_corpus_source_substitution_third_pass_gate[
                    "summary"
                ]["active_total_bits"],
                "candidate_total_bits": full_corpus_source_substitution_third_pass_gate[
                    "summary"
                ]["candidate_total_bits"],
                "candidate_gain_bits": full_corpus_source_substitution_third_pass_gate[
                    "summary"
                ]["candidate_gain_bits"],
                "single_substitution_count": full_corpus_source_substitution_third_pass_gate[
                    "summary"
                ]["single_substitution_count"],
                "positive_single_count": full_corpus_source_substitution_third_pass_gate[
                    "summary"
                ]["positive_single_count"],
                "pair_substitution_count": full_corpus_source_substitution_third_pass_gate[
                    "summary"
                ]["pair_substitution_count"],
                "positive_pair_count": full_corpus_source_substitution_third_pass_gate[
                    "summary"
                ]["positive_pair_count"],
                "best_arity": full_corpus_source_substitution_third_pass_gate[
                    "summary"
                ]["best_arity"],
                "searched_triples_or_higher": full_corpus_source_substitution_third_pass_gate[
                    "scope"
                ]["searched_triples_or_higher"],
            },
            "interpretation": (
                "The third pass still finds a positive single/pair source "
                "substitution, but the gain remains microscopic and smaller than "
                "the second-pass gain. This supports saturation of the local "
                "fixed-recipe source frontier."
            ),
        },
        {
            "question": "does_fourth_pass_single_pair_source_substitution_still_improve",
            "source": rel(SOURCES["full_corpus_source_substitution_fourth_pass_gate"]),
            "status": "passed_microscopic_fourth_pass_source_substitution_improves_bound",
            "evidence": {
                "active_total_bits": full_corpus_source_substitution_fourth_pass_gate[
                    "summary"
                ]["active_total_bits"],
                "candidate_total_bits": full_corpus_source_substitution_fourth_pass_gate[
                    "summary"
                ]["candidate_total_bits"],
                "candidate_gain_bits": full_corpus_source_substitution_fourth_pass_gate[
                    "summary"
                ]["candidate_gain_bits"],
                "single_substitution_count": full_corpus_source_substitution_fourth_pass_gate[
                    "summary"
                ]["single_substitution_count"],
                "positive_single_count": full_corpus_source_substitution_fourth_pass_gate[
                    "summary"
                ]["positive_single_count"],
                "pair_substitution_count": full_corpus_source_substitution_fourth_pass_gate[
                    "summary"
                ]["pair_substitution_count"],
                "positive_pair_count": full_corpus_source_substitution_fourth_pass_gate[
                    "summary"
                ]["positive_pair_count"],
                "best_arity": full_corpus_source_substitution_fourth_pass_gate[
                    "summary"
                ]["best_arity"],
                "searched_triples_or_higher": full_corpus_source_substitution_fourth_pass_gate[
                    "scope"
                ]["searched_triples_or_higher"],
            },
            "interpretation": (
                "The fourth pass still finds a positive single/pair source "
                "substitution, but the gain shrinks again. This updates the "
                "compression bound while strengthening the saturation diagnosis "
                "for the local fixed-recipe source frontier."
            ),
        },
        {
            "question": "is_repeated_local_source_substitution_now_saturated",
            "source": rel(SOURCES["source_substitution_saturation_audit"]),
            "status": "passed_stop_mainline_local_source_micro_sweeps",
            "evidence": {
                "current_compression_bound_bits": source_substitution_saturation[
                    "summary"
                ]["current_compression_bound_bits"],
                "tail_pass_gains_bits": source_substitution_saturation["summary"][
                    "tail_pass_gains_bits"
                ],
                "tail_cumulative_gain_bits": source_substitution_saturation[
                    "summary"
                ]["tail_cumulative_gain_bits"],
                "last_pass_positive_pair_fraction": source_substitution_saturation[
                    "summary"
                ]["last_pass_positive_pair_fraction"],
                "last_pass_pair_candidates_per_gain_bit": source_substitution_saturation[
                    "summary"
                ]["last_pass_pair_candidates_per_gain_bit"],
                "minimum_pair_selector_floor_bits": source_substitution_saturation[
                    "summary"
                ]["minimum_pair_selector_floor_bits"],
                "tail_selector_floor_minus_tail_gain_bits": source_substitution_saturation[
                    "summary"
                ]["tail_selector_floor_minus_tail_gain_bits"],
                "stop_rule": source_substitution_saturation["summary"]["stop_rule"],
                "frontier_saturated": source_substitution_saturation["summary"][
                    "frontier_saturated"
                ],
            },
            "interpretation": (
                "The repeated local same-chunk source-substitution path is now "
                "classified as saturated for mainline work. The latest gains are "
                "far below even a minimal selector-cost sanity check, so future "
                "progress should require structure, holdout prediction, or row0 "
                "origin evidence."
            ),
        },
        {
            "question": "where_is_the_online_prefix_per_book_frontier",
            "source": rel(SOURCES["online_prefix_book_frontier"]),
            "status": "passed_after_bootstrap_with_book0_failure",
            "evidence": {
                "book_count": online_frontier["summary"]["book_count"],
                "book_bounded_roundtrip_book_count": online_frontier["summary"][
                    "book_bounded_roundtrip_book_count"
                ],
                "book_bounded_online_beats_raw_count": online_frontier["summary"][
                    "book_bounded_online_beats_raw_count"
                ],
                "after_bootstrap_book_count": online_frontier["summary"][
                    "after_bootstrap_book_count"
                ],
                "book_bounded_after_bootstrap_beats_raw_count": online_frontier[
                    "summary"
                ]["book_bounded_after_bootstrap_beats_raw_count"],
                "book_bounded_online_failure_books": online_frontier["summary"][
                    "book_bounded_online_failure_books"
                ],
                "mean_book_bounded_online_gain_vs_raw_bits": online_frontier["summary"][
                    "mean_book_bounded_online_gain_vs_raw_bits"
                ],
                "min_book_bounded_online_gain_vs_raw_bits": online_frontier["summary"][
                    "min_book_bounded_online_gain_vs_raw_bits"
                ],
                "total_book_bounded_online_gain_vs_raw_bits": online_frontier["summary"][
                    "total_book_bounded_online_gain_vs_raw_bits"
                ],
                "cumulative_book_bounded_break_even_book": online_frontier["summary"][
                    "cumulative_book_bounded_break_even_book"
                ],
            },
            "interpretation": (
                "At per-book sequential granularity, the previous-books-only "
                "parser fails against raw only for the cold-start book 0. After "
                "that bootstrap, the book-bounded online variant beats raw for "
                "every remaining book."
            ),
        },
        {
            "question": "does_an_explicit_book0_seed_close_the_online_bootstrap_failure",
            "source": rel(SOURCES["online_bootstrap_seed_policy"]),
            "status": "passed_as_bootstrap_accounting_not_bound_promotion",
            "evidence": {
                "book0_raw_uniform_bits": bootstrap_seed["book0"]["raw_uniform_bits"],
                "book0_online_reparse_bits": bootstrap_seed["book0"][
                    "book_bounded_online_reparse_bits"
                ],
                "book0_online_minus_raw_bits": bootstrap_seed["book0"][
                    "book0_online_minus_raw_bits"
                ],
                "raw_seeded_raw_wins_or_ties": bootstrap_seed["summary"][
                    "raw_seeded_raw_wins_or_ties"
                ],
                "raw_seeded_strict_raw_wins": bootstrap_seed["summary"][
                    "raw_seeded_strict_raw_wins"
                ],
                "raw_seeded_failure_books": bootstrap_seed["summary"][
                    "raw_seeded_failure_books"
                ],
                "raw_seeded_stream_saving_vs_online_bits": bootstrap_seed["summary"][
                    "raw_seeded_stream_saving_vs_online_bits"
                ],
                "raw_seeded_gain_vs_raw_bits": bootstrap_seed["summary"][
                    "raw_seeded_gain_vs_raw_bits"
                ],
            },
            "interpretation": (
                "Charging book 0 as an explicit raw seed closes the only local "
                "previous-books-only failure. This is useful bootstrap accounting, "
                "not a promoted compression bound or authorial proof."
            ),
        },
        {
            "question": "does_book0_seed_survive_complete_formula_rescoring",
            "source": rel(SOURCES["seeded_online_formula_rescore"]),
            "status": "failed_as_formula_promotion",
            "evidence": {
                "online_formula_bits": seeded_rescore["summary"]["online_formula_bits"],
                "seeded_online_formula_bits": seeded_rescore["summary"][
                    "seeded_online_formula_bits"
                ],
                "seeded_online_delta_vs_online_bits": seeded_rescore["summary"][
                    "seeded_online_delta_vs_online_bits"
                ],
                "book_bounded_seeded_formula_bits": seeded_rescore["summary"][
                    "book_bounded_seeded_formula_bits"
                ],
                "book_bounded_seeded_delta_vs_online_bits": seeded_rescore["summary"][
                    "book_bounded_seeded_delta_vs_online_bits"
                ],
                "promoted_candidate_count": seeded_rescore["summary"][
                    "promoted_candidate_count"
                ],
                "promoted_candidates": seeded_rescore["summary"]["promoted_candidates"],
                "all_roundtrip": seeded_rescore["summary"]["all_roundtrip"],
            },
            "interpretation": (
                "The seed policy is useful as local bootstrap accounting, but "
                "converting it into formula recipes and rescoring under the full "
                "ledger does not beat the existing online formula."
            ),
        },
        {
            "question": "why_does_seeded_rescore_fail",
            "source": rel(SOURCES["seeded_rescore_loss_decomposition"]),
            "status": "explained_by_literal_payload_penalty",
            "evidence": {
                "local_seed_saving_bits": seeded_loss["local_bootstrap_accounting"][
                    "raw_seeded_stream_saving_vs_online_bits"
                ],
                "seeded_delta_vs_online_bits": seeded_loss["summary"][
                    "seeded_delta_vs_online_bits"
                ],
                "seeded_payload_penalty_bits": seeded_loss["summary"][
                    "seeded_payload_penalty_bits"
                ],
                "seeded_non_payload_savings_bits": seeded_loss["summary"][
                    "seeded_non_payload_savings_bits"
                ],
                "payload_penalty_exceeds_local_seed_saving": seeded_loss["summary"][
                    "payload_penalty_exceeds_local_seed_saving"
                ],
                "book_bounded_delta_vs_online_bits": seeded_loss["summary"][
                    "book_bounded_delta_vs_online_bits"
                ],
                "book_bounded_largest_penalty_component": seeded_loss["summary"][
                    "book_bounded_largest_penalty_component"
                ],
            },
            "interpretation": (
                "The complete formula scorer rejects the seed because the literal "
                "payload penalty outweighs the local bootstrap saving and the "
                "non-payload component savings."
            ),
        },
        {
            "question": "can_exception_signaling_rescue_the_book0_seed",
            "source": rel(SOURCES["seed_exception_signal_cost"]),
            "status": "failed_requires_negative_descriptor_cost",
            "evidence": {
                "local_seed_saving_bits": seed_signal["summary"]["local_seed_saving_bits"],
                "zero_cost_full_formula_delta_vs_online_bits": seed_signal["summary"][
                    "zero_cost_full_formula_delta_vs_online_bits"
                ],
                "promotion_threshold_descriptor_bits": seed_signal["summary"][
                    "promotion_threshold_descriptor_bits"
                ],
                "nonnegative_descriptor_can_promote": seed_signal["summary"][
                    "nonnegative_descriptor_can_promote"
                ],
                "one_book_index_full_delta_bits": next(
                    row["full_formula_delta_vs_online_bits"]
                    for row in seed_signal["rows"]
                    if row["policy"] == "one_book_index_exception"
                ),
                "book_bitmask_full_delta_bits": next(
                    row["full_formula_delta_vs_online_bits"]
                    for row in seed_signal["rows"]
                    if row["policy"] == "book_bitmask"
                ),
            },
            "interpretation": (
                "The zero-cost deterministic fallback is already worse than the "
                "existing online formula. Any real exception signal makes the "
                "seed policy less promotable, so the seed boundary is closed."
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
        {
            "question": "is_the_online_prefix_book_frontier_numeric_order_unique",
            "source": rel(SOURCES["online_order_frontier_controls"]),
            "status": "failed_as_numeric_order_uniqueness_proof",
            "evidence": {
                "numeric_after_bootstrap_beats_raw_count": order_frontier["summary"][
                    "numeric_after_bootstrap_beats_raw_count"
                ],
                "after_bootstrap_book_count": order_frontier["summary"][
                    "after_bootstrap_book_count"
                ],
                "orders_with_perfect_after_bootstrap_count": order_frontier["summary"][
                    "orders_with_perfect_after_bootstrap_count"
                ],
                "order_count": order_frontier["controls"]["order_count"],
                "random_orders_with_perfect_after_bootstrap_count": order_frontier["summary"][
                    "random_orders_with_perfect_after_bootstrap_count"
                ],
                "random_order_count": order_frontier["controls"]["random_order_count"],
                "best_after_bootstrap_mean_gain_order": order_frontier["summary"][
                    "best_after_bootstrap_mean_gain_order"
                ]["name"],
                "best_after_bootstrap_mean_gain_delta_vs_numeric_bits": order_frontier[
                    "summary"
                ]["best_after_bootstrap_mean_gain_order"]["delta_vs_numeric_bits"],
                "best_total_gain_order": order_frontier["summary"]["best_total_gain_order"][
                    "name"
                ],
                "best_total_gain_delta_vs_numeric_bits": order_frontier["summary"][
                    "best_total_gain_order"
                ]["delta_vs_numeric_bits"],
            },
            "interpretation": (
                "The numeric online frontier still predicts after bootstrap, but "
                "the same per-book criterion is matched by simple and random "
                "control orders. It cannot prove numeric order on its own."
            ),
        },
        {
            "question": "can_order_frontier_control_orders_promote_a_formula",
            "source": rel(SOURCES["order_frontier_promotion_gate"]),
            "status": "failed_no_promotable_order",
            "evidence": {
                "frontier_best_total_gain_order": promotion_gate["summary"][
                    "frontier_best_total_gain_order"
                ],
                "full_formula_best_raw_order": promotion_gate["summary"][
                    "full_formula_best_raw_order"
                ],
                "full_formula_best_charged_order": promotion_gate["summary"][
                    "full_formula_best_charged_order"
                ],
                "promotable_order_count": promotion_gate["summary"][
                    "promotable_order_count"
                ],
                "random_04_frontier_total_delta_vs_numeric_bits": promotion_gate[
                    "summary"
                ]["random_04"]["frontier_total_gain_delta_vs_numeric_bits"],
                "random_04_full_formula_raw_delta_vs_numeric_bits": promotion_gate[
                    "summary"
                ]["random_04"]["full_formula_raw_delta_vs_numeric_bits"],
                "random_04_full_formula_charged_delta_vs_numeric_bits": promotion_gate[
                    "summary"
                ]["random_04"]["full_formula_charged_delta_vs_numeric_bits"],
            },
            "interpretation": (
                "The best local frontier order is worse under the complete formula "
                "ledger. The order-frontier metric is therefore retained as a "
                "predictive diagnostic, not a compression-bound promotion score."
            ),
        },
        {
            "question": "do_simple_source_contexts_rescue_the_cross_op_near_tie",
            "source": rel(SOURCES["source_blocker_structural_context_gate"]),
            "status": "failed_simple_contexts_worse",
            "evidence": {
                "cross_op_candidate_delta_bits": source_gate["summary"][
                    "cross_op_candidate_delta_bits"
                ],
                "source_delta_margin_over_break_even_bits": source_gate["summary"][
                    "source_delta_margin_over_break_even_bits"
                ],
                "no_source_oracle_delta_bits": source_gate["summary"][
                    "no_source_oracle_delta_bits"
                ],
                "best_non_global_context": source_gate["summary"][
                    "best_non_global_context"
                ],
                "best_non_global_context_delta_vs_global_bits": source_gate["summary"][
                    "best_non_global_context_delta_vs_global_bits"
                ],
                "best_context_prefix_frozen_loss_count": source_gate["summary"][
                    "best_context_prefix_frozen_loss_count"
                ],
                "prefix_frozen_split_count": source_gate["summary"][
                    "prefix_frozen_split_count"
                ],
            },
            "interpretation": (
                "The tight cross-op near miss is blocked by decodable source cost. "
                "Simple structural source contexts do not remove that blocker."
            ),
        },
        {
            "question": "does_earliest_source_canonicality_remove_decoder_source",
            "source": rel(SOURCES["source_canonicality_decodability_gate"]),
            "status": "failed_encoder_side_only",
            "evidence": {
                "earliest_source_count": source_canonicality_gate["summary"][
                    "earliest_source_count"
                ],
                "copy_items": source_canonicality_gate["summary"]["copy_items"],
                "unique_source_count": source_canonicality_gate["summary"][
                    "unique_source_count"
                ],
                "ambiguous_source_count": source_canonicality_gate["summary"][
                    "ambiguous_source_count"
                ],
                "earliest_exact_chunk_rule_decoder_computable": source_canonicality_gate[
                    "summary"
                ]["earliest_exact_chunk_rule_decoder_computable"],
                "copy_source_dependency_removed_by_canonicality": source_canonicality_gate[
                    "summary"
                ]["copy_source_dependency_removed_by_canonicality"],
                "default_exception_default_matches": source_canonicality_gate[
                    "summary"
                ]["default_exception_default_matches"],
                "default_exception_exceptions": source_canonicality_gate["summary"][
                    "default_exception_exceptions"
                ],
            },
            "interpretation": (
                "Every source is canonical relative to its copied chunk, but that "
                "chunk is not decoder-known future target information. The source "
                "ledger remains a decoding dependency."
            ),
        },
        {
            "question": "can_state_free_source_defaults_remove_previous_copy_state",
            "source": rel(SOURCES["source_state_dependency_gate"]),
            "status": "failed_state_dependency_retained",
            "evidence": {
                "required_state_key": source_state_gate["summary"][
                    "active_reparse_state_key_required"
                ],
                "best_state_free_default": source_state_gate["summary"][
                    "best_state_free_default"
                ],
                "best_state_free_total_penalty_bits": source_state_gate["summary"][
                    "best_state_free_total_penalty_bits"
                ],
                "prefix_frozen_loss_count": source_state_gate["summary"][
                    "prefix_frozen_loss_count"
                ],
                "prefix_frozen_split_count": source_state_gate["summary"][
                    "prefix_frozen_split_count"
                ],
                "prefix_frozen_gap_bits_min": source_state_gate["summary"][
                    "prefix_frozen_gap_bits_min"
                ],
                "prefix_frozen_gap_bits_mean": source_state_gate["summary"][
                    "prefix_frozen_gap_bits_mean"
                ],
                "prefix_frozen_gap_bits_max": source_state_gate["summary"][
                    "prefix_frozen_gap_bits_max"
                ],
                "canonicality_removed_source_dependency": source_state_gate["summary"][
                    "canonicality_removed_source_dependency"
                ],
                "state_free_default_promoted": source_state_gate["summary"][
                    "state_free_default_promoted"
                ],
            },
            "interpretation": (
                "The active copy-source default cannot currently be replaced by "
                "a decoder-computable state-free rule. Previous-copy source and "
                "length remain part of the recipe-discovery state boundary."
            ),
        },
        {
            "question": "is_copy_source_selection_decoder_derivable",
            "source": rel(SOURCES["source_selection_derivation_boundary_gate"]),
            "status": "failed_encoder_canonical_but_decoder_dependency_retained",
            "evidence": {
                "earliest_source_hits": source_selection_gate["summary"][
                    "earliest_source_hits"
                ],
                "copy_items": source_selection_gate["summary"]["copy_items"],
                "latest_source_hits": source_selection_gate["summary"][
                    "latest_source_hits"
                ],
                "previous_source_hits": source_selection_gate["summary"][
                    "previous_source_hits"
                ],
                "previous_source_plus_length_hits": source_selection_gate["summary"][
                    "previous_source_plus_length_hits"
                ],
                "unique_source_candidate_ops": source_selection_gate["summary"][
                    "unique_source_candidate_ops"
                ],
                "ambiguous_source_candidate_ops": source_selection_gate["summary"][
                    "ambiguous_source_candidate_ops"
                ],
                "random_candidate_expected_hits": source_selection_gate["summary"][
                    "random_candidate_expected_hits"
                ],
                "distance_replacement_total_worse_than_active_bits": source_selection_gate[
                    "summary"
                ]["distance_replacement_total_worse_than_active_bits"],
                "distance_prefix_frozen_loss_count": source_selection_gate["summary"][
                    "distance_prefix_frozen_loss_count"
                ],
                "distance_prefix_online_loss_count": source_selection_gate["summary"][
                    "distance_prefix_online_loss_count"
                ],
                "prefix_split_count": source_selection_gate["summary"][
                    "prefix_split_count"
                ],
                "best_state_free_default": source_selection_gate["summary"][
                    "best_state_free_default"
                ],
                "best_state_free_total_penalty_bits": source_selection_gate[
                    "summary"
                ]["best_state_free_total_penalty_bits"],
                "earliest_exact_chunk_rule_decoder_computable": source_selection_gate[
                    "summary"
                ]["earliest_exact_chunk_rule_decoder_computable"],
                "copy_source_dependency_removed_by_canonicality": source_selection_gate[
                    "summary"
                ]["copy_source_dependency_removed_by_canonicality"],
            },
            "interpretation": (
                "Source selection is completely earliest-source canonical from "
                "the encoder side, but the rule depends on future target text. "
                "Distance and state-free replacements are worse, so copy source "
                "remains declared."
            ),
        },
        {
            "question": "does_copy_length_midpoint_context_generalize",
            "source": rel(SOURCES["copy_length_midpoint_context_gate"]),
            "status": "passed_midpoint_retained_searched_cutoff_rejected",
            "evidence": {
                "midpoint_gain_vs_global_bits": copy_length_midpoint_gate["summary"][
                    "midpoint_gain_vs_global_bits"
                ],
                "best_boundary_cutoff": copy_length_midpoint_gate["summary"][
                    "best_boundary_cutoff"
                ],
                "best_cutoff_delta_vs_midpoint_bits": copy_length_midpoint_gate[
                    "summary"
                ]["best_cutoff_delta_vs_midpoint_bits"],
                "midpoint_boundary_rank": copy_length_midpoint_gate["summary"][
                    "midpoint_boundary_rank"
                ],
                "prefix_frozen_midpoint_win_count": copy_length_midpoint_gate[
                    "summary"
                ]["prefix_frozen_midpoint_win_count"],
                "prefix_frozen_split_count": copy_length_midpoint_gate["summary"][
                    "prefix_frozen_split_count"
                ],
                "prefix_frozen_midpoint_minus_global_bits_min": copy_length_midpoint_gate[
                    "summary"
                ]["prefix_frozen_midpoint_minus_global_bits_min"],
                "prefix_frozen_midpoint_minus_global_bits_mean": copy_length_midpoint_gate[
                    "summary"
                ]["prefix_frozen_midpoint_minus_global_bits_mean"],
                "prefix_frozen_midpoint_minus_global_bits_max": copy_length_midpoint_gate[
                    "summary"
                ]["prefix_frozen_midpoint_minus_global_bits_max"],
                "p_permuted_midpoint_gain_ge_observed": copy_length_midpoint_gate[
                    "summary"
                ]["p_permuted_midpoint_gain_ge_observed"],
                "searched_boundary_promoted": copy_length_midpoint_gate["summary"][
                    "searched_boundary_promoted"
                ],
            },
            "interpretation": (
                "The natural book-midpoint context is a supported copy-length "
                "component, while the slightly better searched cutoff is rejected "
                "as ad-hoc local tuning."
            ),
        },
        {
            "question": "is_copy_length_decoder_derived",
            "source": rel(SOURCES["copy_length_derivation_boundary_gate"]),
            "status": "failed_partly_decodable_dependency_retained",
            "evidence": {
                "copy_items": copy_length_derivation_gate["summary"]["copy_items"],
                "encoder_target_max_match_count": copy_length_derivation_gate[
                    "summary"
                ]["encoder_target_max_match_count"],
                "encoder_target_max_decodable": copy_length_derivation_gate[
                    "summary"
                ]["encoder_target_max_decodable"],
                "decoder_max_possible_default_count": copy_length_derivation_gate[
                    "summary"
                ]["decoder_max_possible_default_count"],
                "decoder_max_possible_exception_count": copy_length_derivation_gate[
                    "summary"
                ]["decoder_max_possible_exception_count"],
                "candidate_gain_bits": copy_length_derivation_gate["summary"][
                    "candidate_gain_bits"
                ],
                "midpoint_gain_vs_global_bits": copy_length_derivation_gate[
                    "summary"
                ]["midpoint_gain_vs_global_bits"],
                "midpoint_prefix_frozen_win_count": copy_length_derivation_gate[
                    "summary"
                ]["midpoint_prefix_frozen_win_count"],
                "midpoint_prefix_frozen_split_count": copy_length_derivation_gate[
                    "summary"
                ]["midpoint_prefix_frozen_split_count"],
                "copy_length_fields_retained_in_compact_recipe": copy_length_derivation_gate[
                    "summary"
                ]["copy_length_fields_retained_in_compact_recipe"],
                "copied_digits_covered": copy_length_derivation_gate["summary"][
                    "copied_digits_covered"
                ],
            },
            "interpretation": (
                "Copy length is partly modeled by a decodable max-possible default "
                "and supported midpoint context, but the high-coverage target-max "
                "rule is encoder-only and compact recipes still declare every copy "
                "length."
            ),
        },
        {
            "question": "how_much_literal_payload_is_forced_by_copy_unavailability",
            "source": rel(SOURCES["literal_copy_availability_gate"]),
            "status": "passed_literal_externality_reduced_not_removed",
            "evidence": {
                "forced_literal_items_no_copy_candidate": literal_copy_gate["summary"][
                    "forced_literal_items_no_copy_candidate"
                ],
                "literal_items": literal_copy_gate["summary"]["literal_items"],
                "forced_literal_digits_no_copy_candidate": literal_copy_gate["summary"][
                    "forced_literal_digits_no_copy_candidate"
                ],
                "literal_digits": literal_copy_gate["summary"]["literal_digits"],
                "optional_literal_items_copy_candidate_available": literal_copy_gate[
                    "summary"
                ]["optional_literal_items_copy_candidate_available"],
                "optional_literal_digits_copy_candidate_available": literal_copy_gate[
                    "summary"
                ]["optional_literal_digits_copy_candidate_available"],
                "in_literal_candidate_repairs_scored": literal_copy_gate["summary"][
                    "in_literal_candidate_repairs_scored"
                ],
                "in_literal_best_delta_bits": literal_copy_gate["summary"][
                    "in_literal_best_delta_bits"
                ],
                "cross_op_valid_candidate_count": literal_copy_gate["summary"][
                    "cross_op_valid_candidate_count"
                ],
                "cross_op_best_delta_bits": literal_copy_gate["summary"][
                    "cross_op_best_delta_bits"
                ],
                "near_tie_copy_source_penalty_bits": literal_copy_gate["summary"][
                    "near_tie_copy_source_penalty_bits"
                ],
                "near_tie_copy_length_penalty_bits": literal_copy_gate["summary"][
                    "near_tie_copy_length_penalty_bits"
                ],
                "local_repairs_closed": literal_copy_gate["summary"][
                    "local_repairs_closed"
                ],
            },
            "interpretation": (
                "Most literal payload is forced by absence of legal copy candidates. "
                "The residual optional literal frontier is small, and simple "
                "in-literal/cross-op replacement repairs do not improve the active "
                "ledger."
            ),
        },
        {
            "question": "can_literal_payload_model_be_simplified_after_availability_gate",
            "source": rel(SOURCES["literal_payload_model_gate"]),
            "status": "failed_active_order2_retained",
            "evidence": {
                "active_literal_payload_bits": literal_payload_model_gate["summary"][
                    "active_literal_payload_bits"
                ],
                "active_context_count": literal_payload_model_gate["summary"][
                    "active_context_count"
                ],
                "order1_full_corpus_delta_vs_order2_bits": literal_payload_model_gate[
                    "summary"
                ]["order1_full_corpus_delta_vs_order2_bits"],
                "order1_online_delta_vs_order2_total_bits": literal_payload_model_gate[
                    "summary"
                ]["order1_online_delta_vs_order2_total_bits"],
                "order1_frozen_delta_vs_order2_total_bits": literal_payload_model_gate[
                    "summary"
                ]["order1_frozen_delta_vs_order2_total_bits"],
                "order1_frozen_win_cutoffs": literal_payload_model_gate["summary"][
                    "order1_frozen_win_cutoffs"
                ],
                "best_modal_default_delta_vs_active_bits": literal_payload_model_gate[
                    "summary"
                ]["best_modal_default_delta_vs_active_bits"],
                "best_non_active_structural_label": literal_payload_model_gate[
                    "summary"
                ]["best_non_active_structural_label"],
                "best_non_active_structural_delta_vs_active_bits": literal_payload_model_gate[
                    "summary"
                ]["best_non_active_structural_delta_vs_active_bits"],
                "simplifications_rejected": literal_payload_model_gate["summary"][
                    "simplifications_rejected"
                ],
            },
            "interpretation": (
                "After forced literal availability is separated, the remaining "
                "literal payload stream still requires the active order2 "
                "previous-emitted-digit model under the tested simplifications."
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
            "numeric_order_status": "frontier_not_unique_and_control_orders_not_promotable",
            "source_state_status": "path_dependent_previous_copy_state_retained",
            "source_selection_status": "encoder_canonical_decoder_dependency_retained",
            "copy_length_context_status": "midpoint_context_retained",
            "copy_length_derivation_status": "partly_decodable_dependency_retained",
            "literal_externality_status": "reduced_not_removed",
            "literal_payload_model_status": "active_order2_retained",
            "recipe_representation_status": "derivable_fields_removed_dependencies_retained",
            "item_type_boundary_status": "split_only_retained_op_type_field_derived",
            "current_active_profile_status": "8177_bound_validated_recipe_discovery_blocked",
            "copy_source_state_compression_status": "previous_pair_state_compressed_to_previous_end",
            "active_reparse_feasibility_status": "source_state_dimension_reduced_parser_unpromoted",
            "source_state_reparse_prototype_status": "cutoff60_reprice_executable_roundtrips_but_unpromoted",
            "multicutoff_source_state_reprice_status": "aggregate_generalizes_reprice_only_unpromoted",
            "source_choice_optimizer_status": "fixed_segmentation_source_choice_no_change_boundary",
            "global_source_path_optimizer_status": "fixed_segmentation_global_source_path_improves_unpromoted",
            "full_corpus_source_path_formula_status": "fixed_recipe_source_path_improves_bound_to_8162_412",
            "source_substitution_frontier_status": "single_pair_source_substitution_improves_bound_to_8160_827",
            "source_substitution_second_pass_status": "microscopic_single_pair_improves_bound_to_8160_826",
            "source_substitution_third_pass_status": "microscopic_single_pair_improves_bound_to_8160_825917",
            "source_substitution_fourth_pass_status": "microscopic_single_pair_improves_bound_to_8160_825608",
            "source_substitution_saturation_status": "local_same_chunk_source_substitution_no_longer_mainline",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
            "progress_claim": (
                "This increases predictive/generative validation by showing the "
                "fixed-recipe limitation is not total: a deterministic parser can "
                "rediscover held-out recipes. It also falsifies the stronger claim "
                "that numeric prefix training is uniquely authorial evidence and "
                "reduces same-family source memorization as an explanation for "
                "singleton holdout performance."
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
        elif row["question"] == "do_family_copy_address_losses_survive_same_coordinate_repricing":
            key = (
                f"original losses {evidence['original_positive_address_loss_count']}/"
                f"{evidence['family_count']}; rebased nonpositive "
                f"{evidence['rebased_nonpositive_address_loss_count']}/"
                f"{evidence['family_count']}; mean delta "
                f"{evidence['mean_original_address_delta_bits']:.3f} -> "
                f"{evidence['mean_rebased_address_delta_bits']:.3f} bits"
            )
        elif row["question"] == "does_family_holdout_reparse_beat_active_after_address_correction":
            key = (
                f"beats raw {evidence['reparse_beats_raw_count']}/{evidence['family_count']}; "
                f"beats/ties active {evidence['original_reparse_beats_or_ties_active_count']}/"
                f"{evidence['family_count']} -> "
                f"{evidence['address_corrected_reparse_beats_or_ties_active_count']}/"
                f"{evidence['family_count']}; mean reparse-active "
                f"{evidence['mean_original_reparse_minus_active_bits']:.3f} -> "
                f"{evidence['mean_address_corrected_reparse_minus_active_bits']:.3f}"
            )
        elif row["question"] == "does_family_holdout_reparse_depend_on_test_carryover":
            key = (
                f"roundtrip {evidence['roundtrip_family_count']}/{evidence['family_count']}; "
                f"no-carry beats raw {evidence['no_test_carryover_beats_raw_count']}/"
                f"{evidence['family_count']}; mean gain "
                f"{evidence['mean_no_test_carryover_gain_vs_raw_bits']:.3f} bits"
            )
        elif row["question"] == "does_single_book_holdout_reparse_without_self":
            key = (
                f"roundtrip {evidence['roundtrip_book_count']}/{evidence['book_count']}; "
                f"beats raw {evidence['beats_raw_count']}/{evidence['book_count']}; "
                f"mean gain {evidence['mean_gain_vs_raw_bits']:.3f}; "
                f"min gain {evidence['min_gain_vs_raw_bits']:.3f}"
            )
        elif row["question"] == "where_do_singleton_holdout_copies_source_from":
            key = (
                f"{evidence['total_copy_items']} copy items; "
                f"{evidence['total_copied_digits']} copied digits; "
                f"boundary share {evidence['cross_boundary_copied_digit_share']:.3f}; "
                f"current-prefix share {evidence['current_prefix_copied_digit_share']:.6f}"
            )
        elif row["question"] == "does_singleton_holdout_survive_book_bounded_sources":
            key = (
                f"roundtrip {evidence['roundtrip_book_count']}/{evidence['book_count']}; "
                f"beats raw {evidence['beats_raw_count']}/{evidence['book_count']}; "
                f"mean gain {evidence['mean_book_bounded_gain_vs_raw_bits']:.3f}; "
                f"mean penalty {evidence['mean_book_bounded_minus_unbounded_bits']:.3f}"
            )
        elif row["question"] == "does_singleton_holdout_survive_same_family_source_exclusion":
            key = (
                f"roundtrip {evidence['roundtrip_book_count']}/{evidence['book_count']}; "
                f"beats raw {evidence['beats_raw_count']}/{evidence['book_count']}; "
                f"family-labeled {evidence['family_labeled_beats_raw_count']}/"
                f"{evidence['family_labeled_book_count']}; mean gain "
                f"{evidence['mean_family_excluded_gain_vs_raw_bits']:.3f}; "
                f"max penalty {evidence['max_family_excluded_minus_book_bounded_bits']:.3f}"
            )
        elif row["question"] == "does_online_reparse_reduce_full_corpus_recipe_cost":
            key = (
                f"{evidence['active_scope_bits']:.3f} -> {evidence['candidate_total_bits']:.3f} bits; "
                f"gain {evidence['candidate_gain_vs_active_bits']:.3f}; roundtrip {evidence['roundtrip']}"
            )
        elif row["question"] == "which_recipe_fields_are_derivable_representation_artifacts":
            deps = evidence["remaining_declared_dependencies"]
            key = (
                f"bits {evidence['active_bits']:.3f} -> "
                f"{evidence['final_type_derived_bits']:.3f}; "
                f"delta {evidence['score_delta_bits']:+.12f}; removed fields "
                f"book_length {evidence['removed_book_length_fields']}, "
                f"copy_target {evidence['removed_copy_target_start_fields']}, "
                f"literal_length {evidence['removed_literal_length_fields']}, "
                f"type {evidence['removed_type_fields']} "
                f"(total {evidence['removed_independent_field_count']}); "
                f"JSON saved {evidence['total_recipe_json_byte_saving']}; "
                f"remaining literal_text {deps['literal_text_fields']}, "
                f"copy_source {deps['copy_source_fields']}, "
                f"copy_length {deps['copy_length_fields']}"
            )
        elif row["question"] == "is_item_type_sequence_or_recipe_type_field_dependency":
            key = (
                f"item-type gain {evidence['split_only_gain_bits']:.3f} bits "
                f"(conservative {evidence['split_only_conservative_gain_bits']:.3f}); "
                f"stream {evidence['active_item_type_bits']:.3f} -> "
                f"{evidence['split_only_item_type_bits']:.3f}; "
                f"coded/forced items {evidence['coded_item_type_items']}/"
                f"{evidence['forced_item_type_items']}; alpha "
                f"{evidence['current_alpha']} retained, alpha1 delta "
                f"{evidence['nearest_alpha1_delta_bits']:.3f}; "
                f"op type fields removed {evidence['op_type_fields_removed']}, "
                f"shape ops {evidence['literal_shape_ops']}/"
                f"{evidence['copy_shape_ops']}, ambiguous "
                f"{evidence['ambiguous_shape_ops']}; score delta "
                f"{evidence['op_type_score_delta_bits']:+.12f}; "
                f"roundtrip {evidence['op_type_roundtrip_ok']}/70"
            )
        elif row["question"] == "is_current_active_8177_profile_validated_or_recipe_discovered":
            key = (
                f"active {evidence['active_compression_bound_bits']:.3f} bits; "
                f"length/source defaults {evidence['copy_length_default_exception_bits']:.3f}/"
                f"{evidence['copy_source_default_exception_bits']:.3f}; gains "
                f"{evidence['copy_length_gain_bits']:.3f}/"
                f"{evidence['copy_source_gain_bits']:.3f}; learned share "
                f"{evidence['learned_component_stream_share_pct']:.3f}%; "
                f"frozen min prefix/block/family "
                f"{evidence['active_prefix_frozen_min_gain_bits']:.3f}/"
                f"{evidence['active_block_frozen_min_gain_bits']:.3f}/"
                f"{evidence['active_family_frozen_min_gain_bits']:.3f}; "
                f"family failures active/default-only "
                f"{evidence['active_family_frozen_nonpositive_count']}/"
                f"{evidence['default_exception_only_family_frozen_nonpositive_count']}; "
                f"recipe proved {evidence['recipe_discovery_proved']}; state "
                f"`{evidence['active_reparse_state_key_required']}`; cutoff10 "
                f"state proxy {evidence['cutoff10_state_proxy']} vs old "
                f"{evidence['cutoff10_old_reparse_state_count']}; state-free "
                f"`{evidence['best_state_free_default']}` "
                f"{evidence['best_state_free_worse_than_active_total_bits']:+.3f}"
            )
        elif row["question"] == "can_copy_source_previous_pair_state_be_compressed":
            key = (
                f"`{evidence['previous_pair_state_key']}` -> "
                f"`{evidence['compressed_state_key']}`; stream "
                f"{evidence['source_default_stream_bits']:.3f}; "
                f"default/exception {evidence['source_default_count']}/"
                f"{evidence['source_exception_count']}; mismatches "
                f"{evidence['end_default_mismatch_count']}; proxy "
                f"{evidence['total_pair_state_proxy']} -> "
                f"{evidence['total_end_state_proxy']} "
                f"({evidence['total_end_proxy_reduction_pct']:.3f}% reduction); "
                f"cutoff10 {evidence['cutoff10_pair_state_proxy']} -> "
                f"{evidence['cutoff10_end_state_proxy']}; parser promoted "
                f"{evidence['parser_promoted']}; recipe removed "
                f"{evidence['recipe_discovery_removed']}"
            )
        elif row["question"] == "does_source_state_compression_make_active_reparse_feasible":
            key = (
                f"`{evidence['pre_compression_required_state_key']}` -> "
                f"`{evidence['compressed_source_state_key']}`; proxy "
                f"{evidence['total_pair_state_proxy']} -> "
                f"{evidence['total_end_state_proxy']} "
                f"({evidence['total_pair_to_end_proxy_reduction_pct']:.3f}%); "
                f"end/old {evidence['total_end_proxy_multiplier_over_old_reparse']:.1f}x; "
                f"max book end {evidence['max_book_end_state_proxy']}; "
                f"all <=1m {evidence['all_books_below_1m_end_state_proxy']}; "
                f"cutoff60 <=250k {evidence['cutoff60_books_below_250k']}/"
                f"{evidence['cutoff60_book_count']}; parser promoted "
                f"{evidence['parser_promoted']}"
            )
        elif row["question"] == "does_cutoff60_reparse_execute_with_source_state_repricing":
            key = (
                f"roundtrip {evidence['roundtrip_book_count']}/"
                f"{evidence['book_count']}; raw wins "
                f"{evidence['beats_raw_book_count']}/{evidence['book_count']}; "
                f"uniform-address wins "
                f"{evidence['beats_uniform_address_reparse_book_count']}/"
                f"{evidence['book_count']}; bits "
                f"{evidence['source_state_bits']:.3f} vs "
                f"{evidence['uniform_address_reparse_bits']:.3f}; delta "
                f"{evidence['source_state_minus_uniform_address_bits']:+.3f}; "
                f"raw gain {evidence['gain_vs_raw_digit_uniform_bits']:.3f}; "
                f"default/exception {evidence['source_default_count']}/"
                f"{evidence['source_exception_count']}; reoptimized "
                f"{not evidence['not_recipe_reoptimization']}"
            )
        elif row["question"] == "does_source_state_repricing_generalize_across_prefix_cutoffs":
            key = (
                f"cutoffs {evidence['cutoff_count']}; roundtrip "
                f"{evidence['all_roundtrip']}; raw wins "
                f"{evidence['all_books_beat_raw']}; aggregate uniform wins "
                f"{evidence['aggregate_beats_uniform_cutoff_count']}/"
                f"{evidence['cutoff_count']}; bits "
                f"{evidence['total_source_state_bits']:.3f} vs "
                f"{evidence['total_uniform_address_reparse_bits']:.3f}; delta "
                f"{evidence['total_source_state_minus_uniform_address_bits']:+.3f}; "
                f"default/exception {evidence['total_source_defaults']}/"
                f"{evidence['total_source_exceptions']}; reoptimized "
                f"{not evidence['not_recipe_reoptimization']}"
            )
        elif row["question"] == "can_fixed_segmentation_source_choice_improve_repricing":
            key = (
                f"cutoffs {evidence['cutoff_count']}; roundtrip "
                f"{evidence['all_roundtrip']}; raw wins "
                f"{evidence['all_books_beat_raw']}; reprice wins "
                f"{evidence['aggregate_beats_reprice_cutoff_count']}/"
                f"{evidence['cutoff_count']}; bits "
                f"{evidence['total_bits']:.3f} vs reprice "
                f"{evidence['total_reprice_bits']:.3f}; delta "
                f"{evidence['total_source_choice_minus_reprice_bits']:+.3f}; "
                f"changed sources {evidence['total_changed_sources']}/"
                f"{evidence['total_copy_items']}; segmentation reoptimized "
                f"{not evidence['not_segmentation_reoptimization']}"
            )
        elif row["question"] == "can_global_source_path_improve_fixed_segmentation":
            key = (
                f"cutoffs {evidence['cutoff_count']}; roundtrip "
                f"{evidence['all_roundtrip']}; raw wins "
                f"{evidence['all_books_beat_raw']}; reprice wins "
                f"{evidence['aggregate_beats_reprice_cutoff_count']}/"
                f"{evidence['cutoff_count']}; bits "
                f"{evidence['total_bits']:.3f} vs reprice "
                f"{evidence['total_reprice_bits']:.3f}; delta "
                f"{evidence['total_source_path_minus_reprice_bits']:+.3f}; "
                f"changed sources {evidence['total_changed_sources']}/"
                f"{evidence['total_copy_events']}; defaults/exceptions "
                f"{evidence['total_source_defaults']}/"
                f"{evidence['total_source_exceptions']}; max states "
                f"{evidence['max_state_count']}; segmentation reoptimized "
                f"{not evidence['not_segmentation_reoptimization']}"
            )
        elif row["question"] == "can_full_corpus_source_path_improve_formula_bound":
            key = (
                f"active {evidence['active_total_bits']:.3f}; candidate "
                f"{evidence['candidate_total_bits']:.3f}; gain "
                f"{evidence['candidate_gain_bits']:+.3f}; copy-source "
                f"{evidence['active_copy_source_bits']:.3f} -> "
                f"{evidence['candidate_copy_source_bits']:.3f}; changed "
                f"{evidence['changed_source_count']}/{evidence['copy_event_count']}; "
                f"defaults/exceptions {evidence['source_default_count']}/"
                f"{evidence['source_exception_count']}; max states "
                f"{evidence['max_state_count']}; fixed segmentation "
                f"{evidence['fixed_segmentation']}; fixed lengths "
                f"{evidence['fixed_copy_lengths']}"
            )
        elif row["question"] == "can_single_pair_source_substitution_improve_formula_bound":
            key = (
                f"active {evidence['active_total_bits']:.3f}; candidate "
                f"{evidence['candidate_total_bits']:.3f}; gain "
                f"{evidence['candidate_gain_bits']:+.3f}; copy-source "
                f"{evidence['active_copy_source_bits']:.3f} -> "
                f"{evidence['candidate_copy_source_bits']:.3f}; singles "
                f"{evidence['positive_single_count']}/"
                f"{evidence['single_substitution_count']}; pairs "
                f"{evidence['positive_pair_count']}/"
                f"{evidence['pair_substitution_count']}; best arity "
                f"{evidence['best_arity']}; triples searched "
                f"{evidence['searched_triples_or_higher']}"
            )
        elif row["question"] == "does_second_pass_single_pair_source_substitution_still_improve":
            key = (
                f"active {evidence['active_total_bits']:.6f}; candidate "
                f"{evidence['candidate_total_bits']:.6f}; gain "
                f"{evidence['candidate_gain_bits']:+.6f}; singles "
                f"{evidence['positive_single_count']}/"
                f"{evidence['single_substitution_count']}; pairs "
                f"{evidence['positive_pair_count']}/"
                f"{evidence['pair_substitution_count']}; best arity "
                f"{evidence['best_arity']}; triples searched "
                f"{evidence['searched_triples_or_higher']}"
            )
        elif row["question"] == "does_third_pass_single_pair_source_substitution_still_improve":
            key = (
                f"active {evidence['active_total_bits']:.6f}; candidate "
                f"{evidence['candidate_total_bits']:.6f}; gain "
                f"{evidence['candidate_gain_bits']:+.6f}; singles "
                f"{evidence['positive_single_count']}/"
                f"{evidence['single_substitution_count']}; pairs "
                f"{evidence['positive_pair_count']}/"
                f"{evidence['pair_substitution_count']}; best arity "
                f"{evidence['best_arity']}; triples searched "
                f"{evidence['searched_triples_or_higher']}"
            )
        elif row["question"] == "does_fourth_pass_single_pair_source_substitution_still_improve":
            key = (
                f"active {evidence['active_total_bits']:.6f}; candidate "
                f"{evidence['candidate_total_bits']:.6f}; gain "
                f"{evidence['candidate_gain_bits']:+.6f}; singles "
                f"{evidence['positive_single_count']}/"
                f"{evidence['single_substitution_count']}; pairs "
                f"{evidence['positive_pair_count']}/"
                f"{evidence['pair_substitution_count']}; best arity "
                f"{evidence['best_arity']}; triples searched "
                f"{evidence['searched_triples_or_higher']}"
            )
        elif row["question"] == "is_repeated_local_source_substitution_now_saturated":
            key = (
                f"bound {evidence['current_compression_bound_bits']:.6f}; "
                f"tail gain {evidence['tail_cumulative_gain_bits']:.6f}; "
                f"last positive-pair fraction "
                f"{evidence['last_pass_positive_pair_fraction']:.6f}; "
                f"pairs per gained bit "
                f"{evidence['last_pass_pair_candidates_per_gain_bit']:.3f}; "
                f"selector floor "
                f"{evidence['minimum_pair_selector_floor_bits']:.3f}; "
                f"tail selector floor minus gain "
                f"{evidence['tail_selector_floor_minus_tail_gain_bits']:.3f}; "
                f"saturated {evidence['frontier_saturated']}"
            )
        elif row["question"] == "where_is_the_online_prefix_per_book_frontier":
            key = (
                f"book-bounded raw wins {evidence['book_bounded_online_beats_raw_count']}/"
                f"{evidence['book_count']}; after bootstrap "
                f"{evidence['book_bounded_after_bootstrap_beats_raw_count']}/"
                f"{evidence['after_bootstrap_book_count']}; failures "
                f"{evidence['book_bounded_online_failure_books']}; mean gain "
                f"{evidence['mean_book_bounded_online_gain_vs_raw_bits']:.3f}; "
                f"break-even book {evidence['cumulative_book_bounded_break_even_book']}"
            )
        elif row["question"] == "does_an_explicit_book0_seed_close_the_online_bootstrap_failure":
            key = (
                f"book0 online-raw {evidence['book0_online_minus_raw_bits']:.3f} bits; "
                f"seed wins/ties {evidence['raw_seeded_raw_wins_or_ties']}/70; "
                f"strict wins {evidence['raw_seeded_strict_raw_wins']}/70; "
                f"failures {evidence['raw_seeded_failure_books']}; stream saving "
                f"{evidence['raw_seeded_stream_saving_vs_online_bits']:.3f}"
            )
        elif row["question"] == "does_book0_seed_survive_complete_formula_rescoring":
            key = (
                f"seeded {evidence['seeded_online_formula_bits']:.3f} vs online "
                f"{evidence['online_formula_bits']:.3f}; delta "
                f"{evidence['seeded_online_delta_vs_online_bits']:.3f}; "
                f"book-bounded delta "
                f"{evidence['book_bounded_seeded_delta_vs_online_bits']:.3f}; "
                f"promoted {evidence['promoted_candidate_count']}"
            )
        elif row["question"] == "why_does_seeded_rescore_fail":
            key = (
                f"payload penalty {evidence['seeded_payload_penalty_bits']:.3f}; "
                f"non-payload savings {evidence['seeded_non_payload_savings_bits']:.3f}; "
                f"net {evidence['seeded_delta_vs_online_bits']:.3f}; "
                f"local seed saving {evidence['local_seed_saving_bits']:.3f}"
            )
        elif row["question"] == "can_exception_signaling_rescue_the_book0_seed":
            key = (
                f"zero-cost delta {evidence['zero_cost_full_formula_delta_vs_online_bits']:.3f}; "
                f"required descriptor < {evidence['promotion_threshold_descriptor_bits']:.3f}; "
                f"nonnegative promotes {evidence['nonnegative_descriptor_can_promote']}; "
                f"one-book index delta {evidence['one_book_index_full_delta_bits']:.3f}"
            )
        elif row["question"] == "is_the_online_prefix_book_frontier_numeric_order_unique":
            key = (
                f"numeric after-bootstrap "
                f"{evidence['numeric_after_bootstrap_beats_raw_count']}/"
                f"{evidence['after_bootstrap_book_count']}; perfect controls "
                f"{evidence['orders_with_perfect_after_bootstrap_count']}/"
                f"{evidence['order_count']}; random perfect "
                f"{evidence['random_orders_with_perfect_after_bootstrap_count']}/"
                f"{evidence['random_order_count']}; best mean "
                f"`{evidence['best_after_bootstrap_mean_gain_order']}` "
                f"{evidence['best_after_bootstrap_mean_gain_delta_vs_numeric_bits']:+.3f} bits"
            )
        elif row["question"] == "can_order_frontier_control_orders_promote_a_formula":
            key = (
                f"frontier best `{evidence['frontier_best_total_gain_order']}`; "
                f"full raw best `{evidence['full_formula_best_raw_order']}`; "
                f"full charged best `{evidence['full_formula_best_charged_order']}`; "
                f"promotable {evidence['promotable_order_count']}; random_04 "
                f"{evidence['random_04_frontier_total_delta_vs_numeric_bits']:+.3f} "
                f"frontier vs {evidence['random_04_full_formula_charged_delta_vs_numeric_bits']:+.3f} charged"
            )
        elif row["question"] == "do_simple_source_contexts_rescue_the_cross_op_near_tie":
            key = (
                f"candidate {evidence['cross_op_candidate_delta_bits']:+.3f}; "
                f"source margin {evidence['source_delta_margin_over_break_even_bits']:+.3f}; "
                f"oracle {evidence['no_source_oracle_delta_bits']:+.3f}; "
                f"best context `{evidence['best_non_global_context']}` "
                f"{evidence['best_non_global_context_delta_vs_global_bits']:+.3f}; "
                f"prefix losses {evidence['best_context_prefix_frozen_loss_count']}/"
                f"{evidence['prefix_frozen_split_count']}"
            )
        elif row["question"] == "does_earliest_source_canonicality_remove_decoder_source":
            key = (
                f"earliest {evidence['earliest_source_count']}/"
                f"{evidence['copy_items']}; unique {evidence['unique_source_count']}/"
                f"{evidence['copy_items']}; ambiguous "
                f"{evidence['ambiguous_source_count']}; decoder-computable "
                f"{evidence['earliest_exact_chunk_rule_decoder_computable']}; "
                f"dependency removed "
                f"{evidence['copy_source_dependency_removed_by_canonicality']}; "
                f"default/exception {evidence['default_exception_default_matches']} defaults, "
                f"{evidence['default_exception_exceptions']} exceptions"
            )
        elif row["question"] == "can_state_free_source_defaults_remove_previous_copy_state":
            key = (
                f"required state `{evidence['required_state_key']}`; best state-free "
                f"`{evidence['best_state_free_default']}` "
                f"{evidence['best_state_free_total_penalty_bits']:+.3f} bits; "
                f"prefix losses {evidence['prefix_frozen_loss_count']}/"
                f"{evidence['prefix_frozen_split_count']}; gap min/mean/max "
                f"{evidence['prefix_frozen_gap_bits_min']:.3f}/"
                f"{evidence['prefix_frozen_gap_bits_mean']:.3f}/"
                f"{evidence['prefix_frozen_gap_bits_max']:.3f}; "
                f"canonicality removed dependency "
                f"{evidence['canonicality_removed_source_dependency']}; "
                f"promoted {evidence['state_free_default_promoted']}"
            )
        elif row["question"] == "is_copy_source_selection_decoder_derivable":
            key = (
                f"earliest {evidence['earliest_source_hits']}/"
                f"{evidence['copy_items']}; latest "
                f"{evidence['latest_source_hits']}/{evidence['copy_items']}; "
                f"previous {evidence['previous_source_hits']}/"
                f"{evidence['copy_items']}; prev+len "
                f"{evidence['previous_source_plus_length_hits']}/"
                f"{evidence['copy_items']}; unique/ambiguous "
                f"{evidence['unique_source_candidate_ops']}/"
                f"{evidence['ambiguous_source_candidate_ops']}; random expected "
                f"{evidence['random_candidate_expected_hits']:.3f}; distance "
                f"{evidence['distance_replacement_total_worse_than_active_bits']:+.3f}; "
                f"distance losses frozen/online "
                f"{evidence['distance_prefix_frozen_loss_count']}/"
                f"{evidence['prefix_split_count']}, "
                f"{evidence['distance_prefix_online_loss_count']}/"
                f"{evidence['prefix_split_count']}; state-free "
                f"`{evidence['best_state_free_default']}` "
                f"{evidence['best_state_free_total_penalty_bits']:+.3f}; "
                f"decoder-computable "
                f"{evidence['earliest_exact_chunk_rule_decoder_computable']}; "
                f"dependency removed "
                f"{evidence['copy_source_dependency_removed_by_canonicality']}"
            )
        elif row["question"] == "does_copy_length_midpoint_context_generalize":
            key = (
                f"midpoint gain {evidence['midpoint_gain_vs_global_bits']:.3f} bits; "
                f"rank {evidence['midpoint_boundary_rank']}; best cutoff "
                f"{evidence['best_boundary_cutoff']} is "
                f"{evidence['best_cutoff_delta_vs_midpoint_bits']:.3f} bits better; "
                f"prefix wins {evidence['prefix_frozen_midpoint_win_count']}/"
                f"{evidence['prefix_frozen_split_count']}; frozen gap min/mean/max "
                f"{evidence['prefix_frozen_midpoint_minus_global_bits_min']:.3f}/"
                f"{evidence['prefix_frozen_midpoint_minus_global_bits_mean']:.3f}/"
                f"{evidence['prefix_frozen_midpoint_minus_global_bits_max']:.3f}; "
                f"perm p={evidence['p_permuted_midpoint_gain_ge_observed']:.4f}; "
                f"searched promoted {evidence['searched_boundary_promoted']}"
            )
        elif row["question"] == "is_copy_length_decoder_derived":
            key = (
                f"target-max {evidence['encoder_target_max_match_count']}/"
                f"{evidence['copy_items']} decodable "
                f"{evidence['encoder_target_max_decodable']}; "
                f"decoder max defaults/exceptions "
                f"{evidence['decoder_max_possible_default_count']}/"
                f"{evidence['decoder_max_possible_exception_count']}; "
                f"gain {evidence['candidate_gain_bits']:.3f}; midpoint "
                f"{evidence['midpoint_gain_vs_global_bits']:.3f}, wins "
                f"{evidence['midpoint_prefix_frozen_win_count']}/"
                f"{evidence['midpoint_prefix_frozen_split_count']}; "
                f"recipe copy_length fields "
                f"{evidence['copy_length_fields_retained_in_compact_recipe']}; "
                f"copied digits {evidence['copied_digits_covered']}"
            )
        elif row["question"] == "how_much_literal_payload_is_forced_by_copy_unavailability":
            key = (
                f"forced items {evidence['forced_literal_items_no_copy_candidate']}/"
                f"{evidence['literal_items']}; forced digits "
                f"{evidence['forced_literal_digits_no_copy_candidate']}/"
                f"{evidence['literal_digits']}; optional starts "
                f"{evidence['optional_literal_items_copy_candidate_available']}; "
                f"optional digits {evidence['optional_literal_digits_copy_candidate_available']}; "
                f"in-literal {evidence['in_literal_candidate_repairs_scored']} candidates "
                f"best {evidence['in_literal_best_delta_bits']:+.3f}; cross-op "
                f"{evidence['cross_op_valid_candidate_count']} candidates best "
                f"{evidence['cross_op_best_delta_bits']:+.3f}; source/length penalties "
                f"{evidence['near_tie_copy_source_penalty_bits']:+.3f}/"
                f"{evidence['near_tie_copy_length_penalty_bits']:+.3f}; "
                f"closed {evidence['local_repairs_closed']}"
            )
        elif row["question"] == "can_literal_payload_model_be_simplified_after_availability_gate":
            key = (
                f"active {evidence['active_literal_payload_bits']:.3f} bits, "
                f"{evidence['active_context_count']} contexts; order1 full "
                f"{evidence['order1_full_corpus_delta_vs_order2_bits']:+.3f}, "
                f"online {evidence['order1_online_delta_vs_order2_total_bits']:+.3f}, "
                f"frozen {evidence['order1_frozen_delta_vs_order2_total_bits']:+.3f}; "
                f"order1 frozen wins {evidence['order1_frozen_win_cutoffs']}; "
                f"modal default {evidence['best_modal_default_delta_vs_active_bits']:+.3f}; "
                f"structural `{evidence['best_non_active_structural_label']}` "
                f"{evidence['best_non_active_structural_delta_vs_active_bits']:+.3f}; "
                f"simplifications rejected {evidence['simplifications_rejected']}"
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
            f"- Source state: `{result['decision']['source_state_status']}`.",
            f"- Source selection: `{result['decision']['source_selection_status']}`.",
            f"- Copy-length context: `{result['decision']['copy_length_context_status']}`.",
            f"- Copy-length derivation: `{result['decision']['copy_length_derivation_status']}`.",
            f"- Literal externality: `{result['decision']['literal_externality_status']}`.",
            f"- Literal payload model: `{result['decision']['literal_payload_model_status']}`.",
            f"- Recipe representation: `{result['decision']['recipe_representation_status']}`.",
            f"- Item type boundary: `{result['decision']['item_type_boundary_status']}`.",
            f"- Current active profile: `{result['decision']['current_active_profile_status']}`.",
            f"- Copy source state compression: `{result['decision']['copy_source_state_compression_status']}`.",
            f"- Active reparse feasibility: `{result['decision']['active_reparse_feasibility_status']}`.",
            f"- Source-state reparse prototype: `{result['decision']['source_state_reparse_prototype_status']}`.",
            f"- Multi-cutoff source-state reprice: `{result['decision']['multicutoff_source_state_reprice_status']}`.",
            f"- Source-choice optimizer: `{result['decision']['source_choice_optimizer_status']}`.",
            f"- Global source-path optimizer: `{result['decision']['global_source_path_optimizer_status']}`.",
            f"- Full-corpus source-path formula: `{result['decision']['full_corpus_source_path_formula_status']}`.",
            f"- Source substitution frontier: `{result['decision']['source_substitution_frontier_status']}`.",
            f"- Source substitution second pass: `{result['decision']['source_substitution_second_pass_status']}`.",
            f"- Source substitution third pass: `{result['decision']['source_substitution_third_pass_status']}`.",
            f"- Source substitution fourth pass: `{result['decision']['source_substitution_fourth_pass_status']}`.",
            f"- Source substitution saturation: `{result['decision']['source_substitution_saturation_status']}`.",
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
