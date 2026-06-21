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
