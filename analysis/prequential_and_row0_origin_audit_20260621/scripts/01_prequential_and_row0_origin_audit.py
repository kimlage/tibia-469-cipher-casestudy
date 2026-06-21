from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

LEGACY_SCRIPT = (
    ROOT
    / "analysis"
    / "authorial_mechanism_20260620"
    / "scripts"
    / "125_prequential_and_row0_origin_audit.py"
)
LEGACY_RESULT = (
    ROOT
    / "analysis"
    / "authorial_mechanism_20260620"
    / "reports"
    / "test_results"
    / "125_prequential_and_row0_origin_audit.json"
)
OCC_STREAMS = ROOT / "analysis" / "audit_20260609" / "homophone_channel" / "occ_streams.json"
BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
ITEM_TYPE_OP_SHAPE_GATE = (
    ROOT
    / "analysis"
    / "prequential_and_row0_origin_audit_20260621"
    / "reports"
    / "test_results"
    / "33_item_type_op_shape_boundary_gate.json"
)
CURRENT_ACTIVE_PROFILE_GATE = (
    ROOT
    / "analysis"
    / "prequential_and_row0_origin_audit_20260621"
    / "reports"
    / "test_results"
    / "34_current_active_profile_boundary_gate.json"
)
COPY_SOURCE_STATE_COMPRESSION_GATE = (
    ROOT
    / "analysis"
    / "prequential_and_row0_origin_audit_20260621"
    / "reports"
    / "test_results"
    / "35_copy_source_state_compression_gate.json"
)
ACTIVE_REPARSE_FEASIBILITY_GATE = (
    ROOT
    / "analysis"
    / "prequential_and_row0_origin_audit_20260621"
    / "reports"
    / "test_results"
    / "36_active_reparse_feasibility_after_state_compression_gate.json"
)
CUTOFF60_SOURCE_STATE_REPARSE_PROTOTYPE_GATE = (
    ROOT
    / "analysis"
    / "prequential_and_row0_origin_audit_20260621"
    / "reports"
    / "test_results"
    / "37_cutoff60_source_state_reparse_prototype_gate.json"
)
MULTICUTOFF_SOURCE_STATE_REPARSE_REPRICE_GATE = (
    ROOT
    / "analysis"
    / "prequential_and_row0_origin_audit_20260621"
    / "reports"
    / "test_results"
    / "38_multicutoff_source_state_reparse_reprice_gate.json"
)
MULTICUTOFF_SOURCE_CHOICE_OPTIMIZER_GATE = (
    ROOT
    / "analysis"
    / "prequential_and_row0_origin_audit_20260621"
    / "reports"
    / "test_results"
    / "39_multicutoff_source_choice_optimizer_gate.json"
)
MULTICUTOFF_GLOBAL_SOURCE_PATH_OPTIMIZER_GATE = (
    ROOT
    / "analysis"
    / "prequential_and_row0_origin_audit_20260621"
    / "reports"
    / "test_results"
    / "40_multicutoff_global_source_path_optimizer_gate.json"
)
FULL_CORPUS_SOURCE_PATH_FORMULA_GATE = (
    ROOT
    / "analysis"
    / "prequential_and_row0_origin_audit_20260621"
    / "reports"
    / "test_results"
    / "41_full_corpus_source_path_formula_gate.json"
)
FULL_CORPUS_SOURCE_SUBSTITUTION_FRONTIER_GATE = (
    ROOT
    / "analysis"
    / "prequential_and_row0_origin_audit_20260621"
    / "reports"
    / "test_results"
    / "42_full_corpus_source_substitution_frontier_gate.json"
)
FULL_CORPUS_SOURCE_SUBSTITUTION_SECOND_PASS_GATE = (
    ROOT
    / "analysis"
    / "prequential_and_row0_origin_audit_20260621"
    / "reports"
    / "test_results"
    / "43_full_corpus_source_substitution_second_pass_gate.json"
)
FULL_CORPUS_SOURCE_SUBSTITUTION_THIRD_PASS_GATE = (
    ROOT
    / "analysis"
    / "prequential_and_row0_origin_audit_20260621"
    / "reports"
    / "test_results"
    / "44_full_corpus_source_substitution_third_pass_gate.json"
)
FULL_CORPUS_SOURCE_SUBSTITUTION_FOURTH_PASS_GATE = (
    ROOT
    / "analysis"
    / "prequential_and_row0_origin_audit_20260621"
    / "reports"
    / "test_results"
    / "45_full_corpus_source_substitution_fourth_pass_gate.json"
)
SOURCE_SUBSTITUTION_SATURATION_AUDIT = (
    ROOT
    / "analysis"
    / "prequential_and_row0_origin_audit_20260621"
    / "reports"
    / "test_results"
    / "46_source_substitution_saturation_audit.json"
)
ROW0_PARALLEL_PROVENANCE_BRIDGE_AUDIT = (
    ROOT
    / "analysis"
    / "prequential_and_row0_origin_audit_20260621"
    / "reports"
    / "test_results"
    / "47_row0_parallel_provenance_bridge_audit.json"
)
CURRENT_FORMULA_DEPENDENCY_SCOREBOARD = (
    ROOT
    / "analysis"
    / "prequential_and_row0_origin_audit_20260621"
    / "reports"
    / "test_results"
    / "48_current_formula_dependency_scoreboard.json"
)
SOURCE_LENGTH_JOINT_DERIVABILITY_AUDIT = (
    ROOT
    / "analysis"
    / "prequential_and_row0_origin_audit_20260621"
    / "reports"
    / "test_results"
    / "49_source_length_joint_derivability_audit.json"
)
SOURCE_CANONICALITY_TRADEOFF_AUDIT = (
    ROOT
    / "analysis"
    / "prequential_and_row0_origin_audit_20260621"
    / "reports"
    / "test_results"
    / "50_source_canonicality_tradeoff_audit.json"
)
COPY_LENGTH_SEGMENTATION_EXCEPTION_AUDIT = (
    ROOT
    / "analysis"
    / "prequential_and_row0_origin_audit_20260621"
    / "reports"
    / "test_results"
    / "51_copy_length_segmentation_exception_audit.json"
)
TARGETMAX_RESEGMENTATION_CANDIDATE_AUDIT = (
    ROOT
    / "analysis"
    / "prequential_and_row0_origin_audit_20260621"
    / "reports"
    / "test_results"
    / "52_targetmax_resegmentation_candidate_audit.json"
)

SCOPE_COMPRESSION_BOUND_BITS = 8558.666806283434
KNOWN_LATER_COMPRESSION_ONLY_BOUND_BITS = 8343.061944935467


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("legacy_prequential_row0_audit", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = (len(ordered) - 1) * q
    lower = int(math.floor(index))
    upper = int(math.ceil(index))
    if lower == upper:
        return ordered[lower]
    return ordered[lower] * (upper - index) + ordered[upper] * (index - lower)


def summary(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {"n": 0, "min": None, "median": None, "mean": None, "max": None}
    return {
        "n": len(values),
        "min": min(values),
        "median": percentile(values, 0.5),
        "mean": sum(values) / len(values),
        "max": max(values),
    }


def split_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    online = [float(row["aggregate"]["test_online_gain_vs_uniform_bits"]) for row in rows]
    frozen = [float(row["aggregate"]["test_frozen_gain_vs_uniform_bits"]) for row in rows]
    gaps = [float(row["aggregate"]["online_train_test_gap_bits_per_event"]) for row in rows]
    failures = [
        {
            "label": row["label"],
            "online_gain_vs_uniform_bits": row["aggregate"]["test_online_gain_vs_uniform_bits"],
            "frozen_gain_vs_uniform_bits": row["aggregate"]["test_frozen_gain_vs_uniform_bits"],
        }
        for row in rows
        if row["aggregate"]["test_online_gain_vs_uniform_bits"] <= 0
        or row["aggregate"]["test_frozen_gain_vs_uniform_bits"] <= 0
    ]
    return {
        "split_count": len(rows),
        "online_gain_vs_uniform_bits": summary(online),
        "frozen_gain_vs_uniform_bits": summary(frozen),
        "train_test_gap_bits_per_event": summary(gaps),
        "nonpositive_gain_failures": failures,
    }


def ablation_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_component: dict[str, list[float]] = {
        "copy_length": [],
        "literal_payload": [],
        "item_type": [],
    }
    for row in rows:
        online_total = float(row["aggregate"]["test_online_bits"])
        ablated = row["test_component_ablation_totals_bits"]
        by_component["copy_length"].append(float(ablated["copy_length_uniform_only"]) - online_total)
        by_component["literal_payload"].append(float(ablated["literal_payload_uniform_only"]) - online_total)
        by_component["item_type"].append(float(ablated["item_type_uniform_only"]) - online_total)
    return {component: summary(values) for component, values in by_component.items()}


def parameter_stability(rows: list[dict[str, Any]]) -> dict[str, Any]:
    parameter_rows = [
        row["parameter_stability"]["declared_parameters_frozen"]
        for row in rows
    ]
    first = parameter_rows[0] if parameter_rows else {}
    coverage: dict[str, dict[str, int]] = {}
    for component, key in [
        ("copy_length", "copy_length_context_coverage"),
        ("literal_payload", "literal_payload_context_coverage"),
        ("item_type", "item_type_context_coverage"),
    ]:
        missing = sum(
            int(row["parameter_stability"][key]["missing_context_events"])
            for row in rows
        )
        present = sum(
            int(row["parameter_stability"][key]["present_context_events"])
            for row in rows
        )
        coverage[component] = {
            "present_context_events": present,
            "missing_context_events": missing,
        }
    return {
        "parameters_identical_across_splits": all(row == first for row in parameter_rows),
        "declared_parameters": first,
        "context_coverage_total": coverage,
    }


def row0_substrate_facts() -> dict[str, Any]:
    occ = load_json(OCC_STREAMS)
    books = load_json(BOOKS_DIGITS)
    codes = sorted({code for values in occ["class_sizes"].values() for code in values})
    all_codes = {f"{index:02d}" for index in range(100)}
    return {
        "source_occ_streams": rel(OCC_STREAMS),
        "source_books_digits": rel(BOOKS_DIGITS),
        "book_count": len(books),
        "row0_symbol_count": len(occ["class_sizes"]),
        "class_code_count": len(codes),
        "missing_two_digit_codes": sorted(all_codes - set(codes)),
        "class_sizes": {key: len(value) for key, value in sorted(occ["class_sizes"].items())},
        "full_duplicate_book_count": len(occ.get("full_dup_books", [])),
        "note": (
            "These committed artifacts verify the code-class substrate used by the "
            "mechanical audits; they do not derive the 10x10 pair-cell labels."
        ),
    }


def assert_analysis_boundary(name: str, data: dict[str, Any]) -> None:
    if data.get("translation_delta") != "NONE":
        raise RuntimeError(f"{name} changed translation boundary")
    if data.get("case_reopened", False) is not False:
        raise RuntimeError(f"{name} reopened case")
    if data.get("plaintext_claim", False) is not False:
        raise RuntimeError(f"{name} introduced plaintext")


def make_result(legacy: dict[str, Any]) -> dict[str, Any]:
    item_type_gate = load_json(ITEM_TYPE_OP_SHAPE_GATE)
    assert_analysis_boundary("item_type_op_shape_boundary_gate", item_type_gate)
    active_profile_gate = load_json(CURRENT_ACTIVE_PROFILE_GATE)
    assert_analysis_boundary("current_active_profile_boundary_gate", active_profile_gate)
    state_compression_gate = load_json(COPY_SOURCE_STATE_COMPRESSION_GATE)
    assert_analysis_boundary("copy_source_state_compression_gate", state_compression_gate)
    active_reparse_feasibility_gate = load_json(ACTIVE_REPARSE_FEASIBILITY_GATE)
    assert_analysis_boundary(
        "active_reparse_feasibility_after_state_compression_gate",
        active_reparse_feasibility_gate,
    )
    source_state_reparse_prototype_gate = load_json(
        CUTOFF60_SOURCE_STATE_REPARSE_PROTOTYPE_GATE
    )
    assert_analysis_boundary(
        "cutoff60_source_state_reparse_prototype_gate",
        source_state_reparse_prototype_gate,
    )
    multicutoff_source_state_reprice_gate = load_json(
        MULTICUTOFF_SOURCE_STATE_REPARSE_REPRICE_GATE
    )
    assert_analysis_boundary(
        "multicutoff_source_state_reparse_reprice_gate",
        multicutoff_source_state_reprice_gate,
    )
    source_choice_optimizer_gate = load_json(MULTICUTOFF_SOURCE_CHOICE_OPTIMIZER_GATE)
    assert_analysis_boundary(
        "multicutoff_source_choice_optimizer_gate",
        source_choice_optimizer_gate,
    )
    global_source_path_optimizer_gate = load_json(
        MULTICUTOFF_GLOBAL_SOURCE_PATH_OPTIMIZER_GATE
    )
    assert_analysis_boundary(
        "multicutoff_global_source_path_optimizer_gate",
        global_source_path_optimizer_gate,
    )
    full_corpus_source_path_formula_gate = load_json(
        FULL_CORPUS_SOURCE_PATH_FORMULA_GATE
    )
    assert_analysis_boundary(
        "full_corpus_source_path_formula_gate",
        full_corpus_source_path_formula_gate,
    )
    full_corpus_source_substitution_frontier_gate = load_json(
        FULL_CORPUS_SOURCE_SUBSTITUTION_FRONTIER_GATE
    )
    assert_analysis_boundary(
        "full_corpus_source_substitution_frontier_gate",
        full_corpus_source_substitution_frontier_gate,
    )
    full_corpus_source_substitution_second_pass_gate = load_json(
        FULL_CORPUS_SOURCE_SUBSTITUTION_SECOND_PASS_GATE
    )
    assert_analysis_boundary(
        "full_corpus_source_substitution_second_pass_gate",
        full_corpus_source_substitution_second_pass_gate,
    )
    full_corpus_source_substitution_third_pass_gate = load_json(
        FULL_CORPUS_SOURCE_SUBSTITUTION_THIRD_PASS_GATE
    )
    assert_analysis_boundary(
        "full_corpus_source_substitution_third_pass_gate",
        full_corpus_source_substitution_third_pass_gate,
    )
    full_corpus_source_substitution_fourth_pass_gate = load_json(
        FULL_CORPUS_SOURCE_SUBSTITUTION_FOURTH_PASS_GATE
    )
    assert_analysis_boundary(
        "full_corpus_source_substitution_fourth_pass_gate",
        full_corpus_source_substitution_fourth_pass_gate,
    )
    source_substitution_saturation = load_json(SOURCE_SUBSTITUTION_SATURATION_AUDIT)
    assert_analysis_boundary(
        "source_substitution_saturation_audit",
        source_substitution_saturation,
    )
    row0_parallel_provenance_bridge = load_json(ROW0_PARALLEL_PROVENANCE_BRIDGE_AUDIT)
    assert_analysis_boundary(
        "row0_parallel_provenance_bridge_audit",
        row0_parallel_provenance_bridge,
    )
    current_formula_dependency_scoreboard = load_json(CURRENT_FORMULA_DEPENDENCY_SCOREBOARD)
    assert_analysis_boundary(
        "current_formula_dependency_scoreboard",
        current_formula_dependency_scoreboard,
    )
    source_length_joint_derivability = load_json(SOURCE_LENGTH_JOINT_DERIVABILITY_AUDIT)
    assert_analysis_boundary(
        "source_length_joint_derivability_audit",
        source_length_joint_derivability,
    )
    source_canonicality_tradeoff = load_json(SOURCE_CANONICALITY_TRADEOFF_AUDIT)
    assert_analysis_boundary(
        "source_canonicality_tradeoff_audit",
        source_canonicality_tradeoff,
    )
    copy_length_segmentation_exception = load_json(
        COPY_LENGTH_SEGMENTATION_EXCEPTION_AUDIT
    )
    assert_analysis_boundary(
        "copy_length_segmentation_exception_audit",
        copy_length_segmentation_exception,
    )
    targetmax_resegmentation_candidate = load_json(
        TARGETMAX_RESEGMENTATION_CANDIDATE_AUDIT
    )
    assert_analysis_boundary(
        "targetmax_resegmentation_candidate_audit",
        targetmax_resegmentation_candidate,
    )

    predictive = legacy["predictive_validation"]
    prefix = predictive["prefix_future_suffix_splits"]
    blocks = predictive["contiguous_block_holdouts"]
    families = predictive["public_bookcase_family_holdouts"]
    random_controls = predictive["random_train_set_controls"]

    family_failures = split_summary(families)["nonpositive_gain_failures"]
    prefix_failures = split_summary(prefix)["nonpositive_gain_failures"]
    block_failures = split_summary(blocks)["nonpositive_gain_failures"]
    if prefix_failures:
        predictive_class = "posthoc_compressor_warning_prefix_holdout_failed"
    elif family_failures:
        predictive_class = "predictive_signal_partial_not_generation_method"
    elif block_failures:
        predictive_class = "predictive_signal_partial_block_instability"
    else:
        predictive_class = "predictive_signal_retained_but_recipe_still_posthoc"

    return {
        "schema": "prequential_and_row0_origin_audit_20260621.v1",
        "classification": "analysis_only_falsifiable_audit_row0_origin_exogenous",
        "translation_delta": "NONE",
        "plaintext_claim": False,
        "case_reopened": False,
        "scope": {
            "scope_compression_bound_bits": SCOPE_COMPRESSION_BOUND_BITS,
            "source_formula": legacy["source_formula"],
            "known_later_compression_only_bound_bits_not_used_as_generation_claim": (
                KNOWN_LATER_COMPRESSION_ONLY_BOUND_BITS
            ),
            "current_active_compression_bound_bits": active_profile_gate["summary"][
                "active_compression_bound_bits"
            ],
            "reason_later_bound_not_used_here": (
                "The requested method change freezes the 8558.667-bit formula as "
                "the predictive-validation target and stops treating later "
                "compression-only micro-improvements as generation evidence."
            ),
            "fixed_recipe_limitation": (
                "All predictive tests keep the full-corpus LZ recipe fixed. "
                "They validate learned component scoring, not recipe discovery."
            ),
        },
        "active_component_reproduction": legacy["active_component_reproduction"],
        "predictive_validation": {
            "classification": predictive_class,
            "prefix_future_suffix": {
                "summary": split_summary(prefix),
                "rows": prefix,
            },
            "contiguous_block_holdouts": {
                "summary": split_summary(blocks),
                "rows": blocks,
            },
            "public_bookcase_family_holdouts": {
                "summary": split_summary(families),
                "rows": families,
            },
            "randomized_order_controls": random_controls,
            "component_ablation_prefix_splits": ablation_summary(prefix),
            "parameter_stability_prefix_splits": parameter_stability(prefix),
            "failure_rule": (
                "If prefix holdout gains vanish, classify as posthoc compressor. "
                "Family failures downgrade the result to partial predictive signal, "
                "not an authorial generation method."
            ),
        },
        "row0_origin": {
            "classification": "row0_origin_remains_exogenous",
            "substrate_facts": row0_substrate_facts(),
            "what_row0_explains": legacy["row0_origin"]["what_row0_explains"],
            "what_remains_exogenous": legacy["row0_origin"]["what_remains_exogenous"],
            "hypotheses": legacy["row0_origin"]["hypotheses"],
            "promoted_row0_origin_formula_count": 0,
        },
        "item_type_op_shape_boundary": {
            "classification": item_type_gate["classification"],
            "source": rel(ITEM_TYPE_OP_SHAPE_GATE),
            "summary": item_type_gate["summary"],
            "decision": item_type_gate["decision"],
        },
        "current_active_profile_boundary": {
            "classification": active_profile_gate["classification"],
            "source": rel(CURRENT_ACTIVE_PROFILE_GATE),
            "summary": active_profile_gate["summary"],
            "decision": active_profile_gate["decision"],
        },
        "copy_source_state_compression": {
            "classification": state_compression_gate["classification"],
            "source": rel(COPY_SOURCE_STATE_COMPRESSION_GATE),
            "summary": state_compression_gate["summary"],
            "decision": state_compression_gate["decision"],
        },
        "active_reparse_feasibility_after_state_compression": {
            "classification": active_reparse_feasibility_gate["classification"],
            "source": rel(ACTIVE_REPARSE_FEASIBILITY_GATE),
            "summary": active_reparse_feasibility_gate["summary"],
            "decision": active_reparse_feasibility_gate["decision"],
        },
        "cutoff60_source_state_reparse_prototype": {
            "classification": source_state_reparse_prototype_gate["classification"],
            "source": rel(CUTOFF60_SOURCE_STATE_REPARSE_PROTOTYPE_GATE),
            "summary": source_state_reparse_prototype_gate["summary"],
            "scope": source_state_reparse_prototype_gate["scope"],
            "decision": source_state_reparse_prototype_gate["decision"],
        },
        "multicutoff_source_state_reparse_reprice": {
            "classification": multicutoff_source_state_reprice_gate["classification"],
            "source": rel(MULTICUTOFF_SOURCE_STATE_REPARSE_REPRICE_GATE),
            "summary": multicutoff_source_state_reprice_gate["summary"],
            "scope": multicutoff_source_state_reprice_gate["scope"],
            "decision": multicutoff_source_state_reprice_gate["decision"],
        },
        "multicutoff_source_choice_optimizer": {
            "classification": source_choice_optimizer_gate["classification"],
            "source": rel(MULTICUTOFF_SOURCE_CHOICE_OPTIMIZER_GATE),
            "summary": source_choice_optimizer_gate["summary"],
            "scope": source_choice_optimizer_gate["scope"],
            "decision": source_choice_optimizer_gate["decision"],
        },
        "multicutoff_global_source_path_optimizer": {
            "classification": global_source_path_optimizer_gate["classification"],
            "source": rel(MULTICUTOFF_GLOBAL_SOURCE_PATH_OPTIMIZER_GATE),
            "summary": global_source_path_optimizer_gate["summary"],
            "scope": global_source_path_optimizer_gate["scope"],
            "decision": global_source_path_optimizer_gate["decision"],
        },
        "full_corpus_source_path_formula": {
            "classification": full_corpus_source_path_formula_gate["classification"],
            "source": rel(FULL_CORPUS_SOURCE_PATH_FORMULA_GATE),
            "summary": full_corpus_source_path_formula_gate["summary"],
            "scope": full_corpus_source_path_formula_gate["scope"],
            "decision": full_corpus_source_path_formula_gate["decision"],
            "candidate_output_formula": full_corpus_source_path_formula_gate[
                "candidate_output_formula"
            ],
        },
        "full_corpus_source_substitution_frontier": {
            "classification": full_corpus_source_substitution_frontier_gate[
                "classification"
            ],
            "source": rel(FULL_CORPUS_SOURCE_SUBSTITUTION_FRONTIER_GATE),
            "summary": full_corpus_source_substitution_frontier_gate["summary"],
            "scope": full_corpus_source_substitution_frontier_gate["scope"],
            "decision": full_corpus_source_substitution_frontier_gate["decision"],
            "candidate_output_formula": full_corpus_source_substitution_frontier_gate[
                "candidate_output_formula"
            ],
        },
        "full_corpus_source_substitution_second_pass": {
            "classification": full_corpus_source_substitution_second_pass_gate[
                "classification"
            ],
            "source": rel(FULL_CORPUS_SOURCE_SUBSTITUTION_SECOND_PASS_GATE),
            "summary": full_corpus_source_substitution_second_pass_gate["summary"],
            "scope": full_corpus_source_substitution_second_pass_gate["scope"],
            "decision": full_corpus_source_substitution_second_pass_gate["decision"],
            "candidate_output_formula": full_corpus_source_substitution_second_pass_gate[
                "candidate_output_formula"
            ],
        },
        "full_corpus_source_substitution_third_pass": {
            "classification": full_corpus_source_substitution_third_pass_gate[
                "classification"
            ],
            "source": rel(FULL_CORPUS_SOURCE_SUBSTITUTION_THIRD_PASS_GATE),
            "summary": full_corpus_source_substitution_third_pass_gate["summary"],
            "scope": full_corpus_source_substitution_third_pass_gate["scope"],
            "decision": full_corpus_source_substitution_third_pass_gate["decision"],
            "candidate_output_formula": full_corpus_source_substitution_third_pass_gate[
                "candidate_output_formula"
            ],
        },
        "full_corpus_source_substitution_fourth_pass": {
            "classification": full_corpus_source_substitution_fourth_pass_gate[
                "classification"
            ],
            "source": rel(FULL_CORPUS_SOURCE_SUBSTITUTION_FOURTH_PASS_GATE),
            "summary": full_corpus_source_substitution_fourth_pass_gate["summary"],
            "scope": full_corpus_source_substitution_fourth_pass_gate["scope"],
            "decision": full_corpus_source_substitution_fourth_pass_gate["decision"],
            "candidate_output_formula": full_corpus_source_substitution_fourth_pass_gate[
                "candidate_output_formula"
            ],
        },
        "source_substitution_saturation": {
            "classification": source_substitution_saturation["classification"],
            "source": rel(SOURCE_SUBSTITUTION_SATURATION_AUDIT),
            "summary": source_substitution_saturation["summary"],
            "scope": source_substitution_saturation["scope"],
            "decision": source_substitution_saturation["decision"],
        },
        "row0_parallel_provenance_bridge": {
            "classification": row0_parallel_provenance_bridge["classification"],
            "source": rel(ROW0_PARALLEL_PROVENANCE_BRIDGE_AUDIT),
            "summary": row0_parallel_provenance_bridge["summary"],
            "decision": row0_parallel_provenance_bridge["decision"],
        },
        "current_formula_dependency_scoreboard": {
            "classification": current_formula_dependency_scoreboard["classification"],
            "source": rel(CURRENT_FORMULA_DEPENDENCY_SCOREBOARD),
            "current_formula": current_formula_dependency_scoreboard["current_formula"],
            "rows": current_formula_dependency_scoreboard["rows"],
            "summary": current_formula_dependency_scoreboard["summary"],
            "decision": current_formula_dependency_scoreboard["decision"],
        },
        "source_length_joint_derivability": {
            "classification": source_length_joint_derivability["classification"],
            "source": rel(SOURCE_LENGTH_JOINT_DERIVABILITY_AUDIT),
            "scope": source_length_joint_derivability["scope"],
            "summary": source_length_joint_derivability["summary"],
            "hypotheses": source_length_joint_derivability["hypotheses"],
            "decision": source_length_joint_derivability["decision"],
        },
        "source_canonicality_tradeoff": {
            "classification": source_canonicality_tradeoff["classification"],
            "source": rel(SOURCE_CANONICALITY_TRADEOFF_AUDIT),
            "scope": source_canonicality_tradeoff["scope"],
            "summary": source_canonicality_tradeoff["summary"],
            "noncanonical_current_sources": source_canonicality_tradeoff[
                "noncanonical_current_sources"
            ],
            "decision": source_canonicality_tradeoff["decision"],
        },
        "copy_length_segmentation_exception": {
            "classification": copy_length_segmentation_exception["classification"],
            "source": rel(COPY_LENGTH_SEGMENTATION_EXCEPTION_AUDIT),
            "scope": copy_length_segmentation_exception["scope"],
            "summary": copy_length_segmentation_exception["summary"],
            "exception_rows": copy_length_segmentation_exception["exception_rows"],
            "decision": copy_length_segmentation_exception["decision"],
        },
        "targetmax_resegmentation_candidate": {
            "classification": targetmax_resegmentation_candidate["classification"],
            "source": rel(TARGETMAX_RESEGMENTATION_CANDIDATE_AUDIT),
            "scope": targetmax_resegmentation_candidate["scope"],
            "summary": targetmax_resegmentation_candidate["summary"],
            "decision": targetmax_resegmentation_candidate["decision"],
        },
        "progress_criterion": {
            "counts_as_progress": [
                "Prefix/block/family holdout validation or falsification.",
                "A clearer ad-hoc dependency ledger for the fixed LZ recipe and row0.",
                "Controlled rejection of row0-origin hypotheses with algorithm, cost, coverage, contradictions, and controls.",
            ],
            "does_not_count_as_progress": [
                "Number of scripts or test rows.",
                "Compression-only bit reductions without holdout or structural value.",
                "Any semantic projection unsupported by CipSoft/in-game evidence.",
            ],
        },
        "decision": {
            "compression_bound_status": "8558.667 bits is the frozen validation scope, not final authorial method.",
            "generation_explanation_status": predictive_class,
            "source_state_status": "path_dependent_previous_copy_state_retained",
            "source_selection_status": "encoder_canonical_decoder_dependency_retained",
            "copy_length_context_status": "midpoint_context_retained_searched_cutoff_rejected",
            "copy_length_derivation_status": "partly_decodable_dependency_retained",
            "literal_externality_status": "reduced_not_removed_local_repairs_rejected",
            "literal_payload_model_status": "active_order2_retained_simplifications_rejected",
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
            "row0_parallel_provenance_status": "project_layers_traced_but_cipsoft_origin_untraced",
            "current_formula_dependency_status": "structural_source_length_parser_is_next_mainline",
            "source_length_joint_derivability_status": "joint_encoder_regularities_confirmed_decoder_dependency_retained",
            "source_canonicality_tradeoff_status": "all_earliest_profile_costed_not_promoted",
            "copy_length_segmentation_exception_status": "target_max_exceptions_are_partial_next_op_intrusions",
            "targetmax_resegmentation_candidate_status": "local_proxy_improvements_unpromoted",
            "row0_origin_status": "exogenous_under_current_evidence",
            "translation_or_plaintext_status": "NONE",
        },
    }


def render_markdown(
    result: dict[str, Any],
    *,
    audit_link_prefix: str,
    family_failure_link: str,
    component_selector_link: str,
    recipe_externality_link: str,
    recipe_reparse_matrix_link: str,
    recipe_family_holdout_link: str,
    recipe_family_loss_decomposition_link: str,
    family_holdout_address_space_link: str,
    family_holdout_address_corrected_scoreboard_link: str,
    family_holdout_no_test_carryover_link: str,
    leave_one_book_out_no_self_link: str,
    leave_one_book_out_source_attribution_link: str,
    leave_one_book_out_book_bounded_source_link: str,
    leave_one_book_out_family_excluded_source_link: str,
    online_prefix_book_frontier_link: str,
    online_bootstrap_seed_policy_link: str,
    seeded_online_formula_rescore_link: str,
    seeded_rescore_loss_decomposition_link: str,
    seed_exception_signal_cost_link: str,
    online_order_frontier_controls_link: str,
    order_frontier_promotion_gate_link: str,
    recipe_representation_dependency_gate_link: str,
    item_type_op_shape_boundary_gate_link: str,
    current_active_profile_boundary_gate_link: str,
    copy_source_state_compression_gate_link: str,
    active_reparse_feasibility_gate_link: str,
    cutoff60_source_state_reparse_prototype_gate_link: str,
    multicutoff_source_state_reparse_reprice_gate_link: str,
    multicutoff_source_choice_optimizer_gate_link: str,
    multicutoff_global_source_path_optimizer_gate_link: str,
    full_corpus_source_path_formula_gate_link: str,
    full_corpus_source_substitution_frontier_gate_link: str,
    full_corpus_source_substitution_second_pass_gate_link: str,
    full_corpus_source_substitution_third_pass_gate_link: str,
    full_corpus_source_substitution_fourth_pass_gate_link: str,
    source_substitution_saturation_audit_link: str,
    source_blocker_structural_context_gate_link: str,
    source_canonicality_decodability_gate_link: str,
    source_state_dependency_gate_link: str,
    source_selection_derivation_boundary_gate_link: str,
    copy_length_midpoint_context_gate_link: str,
    copy_length_derivation_boundary_gate_link: str,
    literal_copy_availability_gate_link: str,
    literal_payload_model_gate_link: str,
    current_formula_dependency_scoreboard_link: str,
    source_length_joint_derivability_audit_link: str,
    source_canonicality_tradeoff_audit_link: str,
    copy_length_segmentation_exception_audit_link: str,
    targetmax_resegmentation_candidate_audit_link: str,
    row0_requirement_link: str,
    row0_parallel_provenance_bridge_link: str,
) -> str:
    prefix = result["predictive_validation"]["prefix_future_suffix"]["rows"]
    random_controls = result["predictive_validation"]["randomized_order_controls"]
    block_summary = result["predictive_validation"]["contiguous_block_holdouts"]["summary"]
    family_summary = result["predictive_validation"]["public_bookcase_family_holdouts"]["summary"]
    ablations = result["predictive_validation"]["component_ablation_prefix_splits"]
    params = result["predictive_validation"]["parameter_stability_prefix_splits"]
    item_type_boundary = result["item_type_op_shape_boundary"]["summary"]
    active_profile_boundary = result["current_active_profile_boundary"]["summary"]
    state_compression = result["copy_source_state_compression"]["summary"]
    reparse_feasibility = result[
        "active_reparse_feasibility_after_state_compression"
    ]["summary"]
    source_reparse_prototype = result["cutoff60_source_state_reparse_prototype"][
        "summary"
    ]
    source_reparse_aggregate = source_reparse_prototype["aggregate"]
    multicutoff_source_reprice = result["multicutoff_source_state_reparse_reprice"][
        "summary"
    ]
    source_choice_optimizer = result["multicutoff_source_choice_optimizer"]["summary"]
    global_source_path = result["multicutoff_global_source_path_optimizer"]["summary"]
    full_corpus_source_path = result["full_corpus_source_path_formula"]["summary"]
    source_substitution_frontier = result["full_corpus_source_substitution_frontier"][
        "summary"
    ]
    source_substitution_second_pass = result[
        "full_corpus_source_substitution_second_pass"
    ]["summary"]
    source_substitution_third_pass = result[
        "full_corpus_source_substitution_third_pass"
    ]["summary"]
    source_substitution_fourth_pass = result[
        "full_corpus_source_substitution_fourth_pass"
    ]["summary"]
    source_substitution_saturation = result["source_substitution_saturation"][
        "summary"
    ]
    row0_parallel_provenance = result["row0_parallel_provenance_bridge"]["summary"]
    current_dependency = result["current_formula_dependency_scoreboard"]
    current_dependency_summary = current_dependency["summary"]
    current_dependency_counts = current_dependency["current_formula"][
        "dependency_counts"
    ]
    source_length_joint = result["source_length_joint_derivability"]["summary"]
    source_canonicality_tradeoff = result["source_canonicality_tradeoff"][
        "summary"
    ]
    copy_length_segmentation = result["copy_length_segmentation_exception"][
        "summary"
    ]
    targetmax_resegmentation = result["targetmax_resegmentation_candidate"][
        "summary"
    ]

    lines = [
        "# Prequential and Row0 Origin Audit",
        "",
        "Classification: `analysis_only_falsifiable_audit_row0_origin_exogenous`",
        "Translation delta: `NONE`",
        "",
        "## Scope",
        "",
        f"- Frozen validation compression bound: `{result['scope']['scope_compression_bound_bits']:.3f}` bits",
        f"- Later compression-only bound recorded but not used as generation evidence: `{result['scope']['known_later_compression_only_bound_bits_not_used_as_generation_claim']:.3f}` bits",
        "- No plaintext, translation, or case-reopening claim is made.",
        "- Limitation: the LZ recipe is fixed from the full corpus; this audit tests learned component scoring, not recipe discovery.",
            "",
            "## Predictive Validation",
            "",
        f"Predictive classification: `{result['predictive_validation']['classification']}`",
        "",
        "| Split | Train books | Test books | Train bits | Test online bits | Test frozen bits | Uniform bits | Online gain | Frozen gain | Gap/event |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in prefix:
        agg = row["aggregate"]
        lines.append(
            f"| `{row['label']}` | `{len(row['train_books'])}` | `{len(row['test_books'])}` | "
            f"`{agg['train_bits']:.3f}` | `{agg['test_online_bits']:.3f}` | "
            f"`{agg['test_frozen_bits']:.3f}` | `{agg['test_uniform_bits']:.3f}` | "
            f"`{agg['test_online_gain_vs_uniform_bits']:.3f}` | "
            f"`{agg['test_frozen_gain_vs_uniform_bits']:.3f}` | "
            f"`{agg['online_train_test_gap_bits_per_event']:.4f}` |"
        )

    lines.extend(
        [
            "",
            "### Baselines And Controls",
            "",
            f"- Prefix online gain summary: `{result['predictive_validation']['prefix_future_suffix']['summary']['online_gain_vs_uniform_bits']}`",
            f"- Prefix frozen gain summary: `{result['predictive_validation']['prefix_future_suffix']['summary']['frozen_gain_vs_uniform_bits']}`",
            f"- Contiguous block online summary: `{block_summary['online_gain_vs_uniform_bits']}`",
            f"- Public-bookcase family online summary: `{family_summary['online_gain_vs_uniform_bits']}`",
            f"- Public-bookcase family nonpositive failures: `{family_summary['nonpositive_gain_failures']}`",
            "",
            "| Cutoff | Observed prefix online gain | Random median gain | p(random >= observed) |",
            "|---:|---:|---:|---:|",
        ]
    )
    for row in random_controls:
        lines.append(
            f"| `{row['cutoff']}` | `{row['observed_prefix_online_gain_vs_uniform_bits']:.3f}` | "
            f"`{row['random_gain_summary_bits']['median']:.3f}` | "
            f"`{row['p_random_gain_ge_observed']:.4f}` |"
        )

    lines.extend(
        [
            "",
            "### Component Ablations",
            "",
            "Values are bits saved by the learned component over replacing only that component with a uniform code on prefix holdouts.",
            "",
            "| Component | Min | Median | Mean | Max |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for component, row in ablations.items():
        lines.append(
            f"| `{component}` | `{row['min']:.3f}` | `{row['median']:.3f}` | "
            f"`{row['mean']:.3f}` | `{row['max']:.3f}` |"
        )

    lines.extend(
        [
            "",
            "### Parameter Stability",
            "",
            f"- Parameters identical across prefix splits: `{params['parameters_identical_across_splits']}`",
            f"- Declared parameters: `{params['declared_parameters']}`",
            f"- Context coverage totals: `{params['context_coverage_total']}`",
            "",
            "Interpretation: prefix and contiguous-block tests retain positive advantage over uniform, but the family split has nonpositive failures. The result is therefore predictive signal only, not a final generation method.",
            "",
            "### Family Failure Follow-Up",
            "",
            "A follow-up failure audit decomposes the three public-bookcase family failures.",
            "They are component/sample-size stress cases rather than a new row0-origin signal:",
            "`hellgate_public_bookcase_33` and `hellgate_public_bookcase_8` are copy-only",
            "failures dominated by copy-length underperformance, while",
            "`hellgate_public_bookcase_6` is online-positive but frozen-negative because the",
            "item-type component loses to uniform under frozen counts.",
            f"See [02_family_holdout_failure_audit.md]({family_failure_link}).",
            "",
            "### Component Selector Follow-Up",
            "",
            "A train-CV component selector then asks whether those failures can be rescued",
            "without seeing the held-out family. For every public-bookcase family, inner",
            "training-family validation keeps all three active components. The selector",
            "therefore leaves the same failures in place; only a heldout oracle improves the",
            "ledger, so no component fallback is promoted.",
            f"See [03_train_cv_component_selector_audit.md]({component_selector_link}).",
            "",
            "### Recipe Externality Follow-Up",
            "",
            "A recipe-externality audit then quantifies the main remaining limitation of",
            "the prequential evidence. Of the `8558.667`-bit validation scope,",
            "`4285.876` bits (`50.076%`) are the prequentially scored copy-length,",
            "literal-payload, and item-type components, while `4272.791` bits",
            "(`49.924%`) remain fixed recipe or non-learned ledger: fixed bits,",
            "literal structure without payload, and copy addresses. The code path",
            "confirms that train/test splits score event rows extracted from the full",
            "formula before splitting; they do not discover held-out literal/copy",
            "segmentation or copy source addresses.",
            f"See [04_recipe_externality_audit.md]({recipe_externality_link}).",
            "",
            "### Recipe Reparse Evidence Matrix",
            "",
            "A follow-up evidence matrix then checks whether the later deterministic",
            "reparse audits actually reduce that fixed-recipe externality. They do:",
            "deterministic reparse roundtrips all future suffixes at cutoffs",
            "`10/20/35/50/60` and beats the active suffix recipe under frozen counts.",
            "Content controls are also weaker. The boundary remains partial because",
            "train-set controls show random same-size training inventories can match",
            "or exceed the numeric prefix: single-cutoff `50` gives `p=0.1538`, and",
            "the multi-cutoff control loses to the random-train mean at cutoff `60`.",
            f"See [06_recipe_reparse_evidence_matrix.md]({recipe_reparse_matrix_link}).",
            "",
            "### Recipe Reparse Family Holdout",
            "",
            "A public-bookcase family holdout then tests whether deterministic recipe",
            "discovery fails on the same family axis where component-only scoring had",
            "failures. It does not: reparse beats raw digits for `19/19` families and",
            "for `3/3` component-failure families. It beats the active frozen recipe in",
            "`14/19` families, so the active full-corpus recipe still has local wins and",
            "the generation explanation remains partial.",
            f"See [08_recipe_reparse_family_holdout.md]({recipe_family_holdout_link}).",
            "",
            "### Recipe Reparse Family Loss Decomposition",
            "",
            "The five families where reparse does not beat the active frozen recipe",
            "are then decomposed by charged component. All five still roundtrip and",
            "still beat raw digits. Four losses are dominated by copy-address bits,",
            "with identical literal/copy inventory against the active recipe; one is",
            "an exact tie. This localizes the remaining active-recipe advantage",
            "without promoting a new generation formula.",
            f"See [09_recipe_reparse_family_loss_decomposition.md]({recipe_family_loss_decomposition_link}).",
            "",
            "### Family Holdout Address Space Audit",
            "",
            "A same-coordinate address audit then checks whether those copy-address",
            "losses are real recipe losses. They are not: when the active recipe is",
            "rebased into the same holdout coordinate system used by the reparse,",
            "all five families roundtrip and the mean copy-address delta falls from",
            "`4.667` bits to approximately `0.000` bits under a `0.001` bit epsilon.",
            "The prior active-recipe local wins were therefore an address-space",
            "comparison artifact, not a reparse failure.",
            f"See [10_family_holdout_address_space_audit.md]({family_holdout_address_space_link}).",
            "",
            "### Address-Corrected Family Scoreboard",
            "",
            "Applying the same correction to all public-bookcase family holdouts",
            "changes the active comparison from `15/19` beat-or-tie families before",
            "correction to `19/19` after correction. Reparse still beats raw digits",
            "in `19/19` families, and the mean reparse-minus-active gap moves from",
            "`-139.959` to `-161.381` bits. This is stronger predictive recipe",
            "evidence, still not row0 derivation or semantics.",
            f"See [11_family_holdout_address_corrected_scoreboard.md]({family_holdout_address_corrected_scoreboard_link}).",
            "",
            "### No-Test-Carryover Family Holdout",
            "",
            "A stricter variant then removes cross-book carryover inside each held-out",
            "family. Each held-out book is parsed from the training-complement",
            "inventory alone. The result still roundtrips `19/19` families and beats",
            "raw digit coding in `19/19`, with mean gain `1054.570` bits versus raw.",
            "This shows the family signal does not depend on letting earlier held-out",
            "books feed later held-out books.",
            f"See [12_family_holdout_no_test_carryover_audit.md]({family_holdout_no_test_carryover_link}).",
            "",
            "### Leave-One-Book-Out No-Self Audit",
            "",
            "At singleton granularity, every book is then held out individually and",
            "reparsed from the other `69` books only. All `70/70` books roundtrip and",
            "beat raw digit coding; mean gain is `469.307` bits and the weakest gain",
            "is still `96.055` bits. This confirms item-level mechanical redundancy,",
            "while still not proving an authorial order because the inventory is the",
            "full complement of other books.",
            f"See [13_leave_one_book_out_no_self_audit.md]({leave_one_book_out_no_self_link}).",
            "",
            "### Leave-One-Book-Out Source Attribution",
            "",
            "The singleton result is then expanded into a source atlas. Across `70`",
            "singleton reparses there are `189` copy items and `11062` copied digits.",
            "The copied digits are attributable to concrete source books or, rarely,",
            "the already-emitted current prefix (`8` digits, share `0.000723`). The",
            "important caveat is explicit: `3001` copied digits (`0.271289`) cross",
            "artificial source-book boundaries created by concatenating the complement",
            "inventory without separators.",
            f"See [14_leave_one_book_out_source_attribution_audit.md]({leave_one_book_out_source_attribution_link}).",
            "",
            "### Book-Bounded Singleton Source Audit",
            "",
            "The boundary caveat is then tested directly by forbidding copy sources",
            "from crossing source-book boundaries. The singleton result survives:",
            "`70/70` books roundtrip and beat raw digit coding, mean gain remains",
            "`464.898` bits, and the mean penalty versus the unbounded singleton",
            "parser is only `4.409` bits.",
            f"See [15_leave_one_book_out_book_bounded_source_audit.md]({leave_one_book_out_book_bounded_source_link}).",
            "",
            "### Family-Excluded Singleton Source Audit",
            "",
            "The same singleton setup is then made stricter for public-bookcase",
            "families: when a target book has a known family label, all books in that",
            "same family are removed from both frozen train counts and copy sources.",
            "The result still roundtrips `70/70` books, beats raw digit coding in",
            "`70/70`, and the family-labeled subset beats raw in `46/46`. Mean gain",
            "is `460.251` bits, minimum gain is `56.053` bits, and the maximum penalty",
            "versus the book-bounded singleton parser is `119.076` bits. This reduces",
            "same-family memorization as an explanation for the singleton signal,",
            "while still not promoting a final authorial method.",
            f"See [16_leave_one_book_out_family_excluded_source_audit.md]({leave_one_book_out_family_excluded_source_link}).",
            "",
            "### Online Prefix Book Frontier Audit",
            "",
            "Finally, the deterministic online parser is decomposed at per-book",
            "granularity under the true numeric-prefix constraint: book `n` can use",
            "only books `< n` as external inventory. The book-bounded variant",
            "roundtrips `70/70`, beats raw digit coding in `69/70`, and the only",
            "failure is book `0`, before any prior-book inventory exists. After that",
            "bootstrap, it beats raw in `69/69` books; the cumulative book-bounded",
            "gain crosses break-even at book `2`. Mean book-bounded online gain is",
            "`419.761` bits. This strengthens sequential mechanical generation",
            "evidence while keeping the bootstrap caveat explicit.",
            f"See [17_online_prefix_book_frontier_audit.md]({online_prefix_book_frontier_link}).",
            "",
            "### Online Bootstrap Seed Policy Audit",
            "",
            "The bootstrap caveat is then tested directly as an accounting policy.",
            "Book `0` costs `488.857` bits under the online parser and `478.358`",
            "bits as a raw uniform seed, so the online cold start is `10.499` bits",
            "worse than raw. Charging book `0` as one explicit raw seed leaves books",
            "`1-69` unchanged and gives `70/70` wins-or-ties against raw, with",
            "`69/70` strict wins and no local failures. This closes the local",
            "bootstrap failure as a seed-policy issue, but is not promoted as a new",
            "compression bound or authorial proof.",
            f"See [18_online_bootstrap_seed_policy_audit.md]({online_bootstrap_seed_policy_link}).",
            "",
            "### Seeded Online Formula Rescore Audit",
            "",
            "The seed policy is then converted back into actual formula recipes and",
            "rescored under the complete active ledger. The result rejects promotion:",
            "the existing online formula remains `8343.062` bits, while replacing",
            "book `0` with one literal seed gives `8344.041` bits (`+0.979`). A",
            "book-bounded seeded variant is much worse at `8648.260` bits",
            "(`+305.198`). The seed is therefore retained only as bootstrap",
            "accounting, not as a new full-formula compression bound.",
            f"See [19_seeded_online_formula_rescore_audit.md]({seeded_online_formula_rescore_link}).",
            "",
            "### Seeded Rescore Loss Decomposition",
            "",
            "The rescore rejection is then decomposed by component. The seeded",
            "formula does save non-payload costs (`36.842` bits), but it adds a",
            "`37.821`-bit literal-payload penalty, leaving the formula `0.979` bits",
            "worse than online. In the book-bounded seeded variant, the largest",
            "penalty is copy address (`136.412` bits). This explains why the seed",
            "can close the local cold-start ledger while still failing complete",
            "formula scoring.",
            f"See [20_seeded_rescore_loss_decomposition.md]({seeded_rescore_loss_decomposition_link}).",
            "",
            "### Seed Exception Signal Cost Audit",
            "",
            "The last seed fallback is tested as an exception-signaling problem. Even",
            "the best-case zero-cost deterministic fallback is `+0.979` bits worse",
            "than the existing online formula. A one-book exception index would make",
            "the delta `+7.108` bits, and a bitmask would make it `+70.979` bits.",
            "Promotion would require a negative descriptor cost (`< -0.979` bits),",
            "so the seed exception cannot become a promoted formula under any",
            "nonnegative signaling cost.",
            f"See [21_seed_exception_signal_cost_audit.md]({seed_exception_signal_cost_link}).",
            "",
            "### Online Order Frontier Controls",
            "",
            "The per-book online frontier is then tested against the same order",
            "families used by the aggregate order-control audit. Numeric order still",
            "beats raw digit coding in `69/69` books after its first bootstrap",
            "position, but that criterion is not unique: `10/11` tested orders have",
            "perfect after-bootstrap raw wins, including `6/6` seeded random orders.",
            "The best after-bootstrap mean-gain and total-gain order is `random_04`,",
            "at `+0.549` bits versus numeric mean after-bootstrap gain and `+61.452`",
            "bits versus numeric total gain. This keeps the online frontier as",
            "predictive-parser evidence but rejects the stronger claim that the",
            "per-book frontier proves numeric book order.",
            f"See [22_online_order_frontier_controls.md]({online_order_frontier_controls_link}).",
            "",
            "### Order Frontier Promotion Gate",
            "",
            "The non-unique order-frontier result is then checked against the",
            "complete formula ledger. The local frontier winner, `random_04`, is",
            "`+61.452` bits better than numeric on book-bounded frontier total, but",
            "it is `+188.584` bits worse under the complete online formula before",
            "order cost and `+521.038` bits worse after the arbitrary permutation",
            "descriptor. No tested non-numeric order is promotable under a",
            "nonnegative descriptor. The frontier metric is therefore retained as",
            "a predictive diagnostic, not a compression-bound promotion score.",
            f"See [23_order_frontier_promotion_gate.md]({order_frontier_promotion_gate_link}).",
            "",
            "### Recipe Representation Dependency Gate",
            "",
            "The compact online recipe representation is then audited as a dependency",
            "ledger. Book `length`, copy `target_start`, literal `length`, and op",
            "`type` are derivable representation artifacts: removing `70 + 261 +",
            "87 + 348` fields preserves `8343.062` bits and `70/70` roundtrip.",
            "The recipe JSON shrinks from `24355` bytes to `12633` bytes. The",
            "remaining declared operation-level dependencies are still literal",
            "text (`87` fields / `857` digits), copy source (`261` fields), and",
            "copy length (`261` fields).",
            f"See [30_recipe_representation_dependency_gate.md]({recipe_representation_dependency_gate_link}).",
            "",
            "### Item Type Op Shape Boundary Gate",
            "",
            "The item-type boundary is then separated into two layers. The",
            "split-only forced-rule item-type model remains part of the generation",
            "profile: it moved the old formula from `8561.792` to `8558.667` bits,",
            f"for a `{item_type_boundary['split_only_gain_bits']:.3f}`-bit gain",
            f"(`{item_type_boundary['split_only_conservative_gain_bits']:.3f}` bits",
            "under the conservative extra-declaration check), and alpha `2` remains",
            f"best with alpha `1` `{item_type_boundary['nearest_alpha1_delta_bits']:.3f}`",
            "bits worse. But explicit recipe op `type` fields are not a separate",
            f"compact dependency: `{item_type_boundary['op_type_fields_removed']}`",
            "fields are derivable from operation shape, with literal/copy-shaped",
            f"ops `{item_type_boundary['literal_shape_ops']}`/",
            f"`{item_type_boundary['copy_shape_ops']}`, zero score delta, and",
            "`70/70` roundtrip.",
            f"See [33_item_type_op_shape_boundary_gate.md]({item_type_op_shape_boundary_gate_link}).",
            "",
            "### Current Active Profile Boundary Gate",
            "",
            "A current-active-profile gate then aligns the older frozen validation",
            "scope with the latest active mechanical ledger. The active bound is",
            f"`{active_profile_boundary['active_compression_bound_bits']:.3f}` bits:",
            "copy-length default/exception first moved the formula to",
            f"`{active_profile_boundary['copy_length_default_exception_bits']:.3f}`",
            f"bits, and copy-source default/exception moved it to",
            f"`{active_profile_boundary['copy_source_default_exception_bits']:.3f}`",
            "bits. The full active learned streams cover",
            f"`{active_profile_boundary['learned_component_stream_share_pct']:.3f}%`",
            "of the bound and have positive frozen gain in every tested prefix,",
            "block, and public-bookcase family split; the family frozen minimum is",
            f"`{active_profile_boundary['active_family_gain_summary']['frozen_min_gain_bits']:.3f}`",
            "bits. The gate does not prove recipe discovery: exact active reparse",
            "requires state",
            f"`{active_profile_boundary['active_reparse_state_key_required']}`,",
            "and the best state-free replacement is",
            f"`{active_profile_boundary['best_state_free_worse_than_active_total_bits']:.3f}`",
            "bits worse.",
            f"See [34_current_active_profile_boundary_gate.md]({current_active_profile_boundary_gate_link}).",
            "",
            "### Copy Source State Compression Gate",
            "",
            "The source-state blocker is then sharpened. The active source",
            "default was previously described as needing previous source and",
            "previous length, but the cost rule only uses their sum. The gate",
            "therefore replaces",
            f"`{state_compression['previous_pair_state_key']}` with",
            f"`{state_compression['compressed_state_key']}` for source-cost",
            "classification. It preserves the same default/exception stream",
            f"(`{state_compression['source_default_stream_bits']:.3f}` bits,",
            f"`{state_compression['end_default_hits']}` defaults,",
            f"`{state_compression['end_exception_hits']}` exceptions,",
            f"`{state_compression['end_default_mismatch_count']}` mismatches)",
            "and reduces the aggregate candidate-state proxy from",
            f"`{state_compression['total_pair_state_proxy']}` to",
            f"`{state_compression['total_end_state_proxy']}`",
            f"(`{state_compression['total_end_proxy_reduction_pct']:.3f}%`).",
            "This is a real state simplification, not a parser promotion.",
            f"See [35_copy_source_state_compression_gate.md]({copy_source_state_compression_gate_link}).",
            "",
            "### Active Reparse Feasibility After State Compression Gate",
            "",
            "A follow-up feasibility gate then asks whether that state compression",
            "changes the implementation frontier for exact active reparse. It does",
            "for the source-state dimension: every tested book-level end-state proxy",
            "falls below one million, the worst book-level proxy is",
            f"`{reparse_feasibility['max_book_end_state_proxy']}`, and cutoff `60`",
            "has",
            f"`{reparse_feasibility['cutoff60_books_below_250k']}`/",
            f"`{reparse_feasibility['cutoff60_book_count']}` books below `250000`.",
            "The aggregate source-state proxy still remains",
            f"`{reparse_feasibility['total_end_proxy_multiplier_over_old_reparse']:.1f}x`",
            "the old frozen-count DP state count, and the gate does not solve the",
            "full active objective, adaptive counts, tie-breaking, copy source",
            "selection, copy length declaration, literal payload, or item-type",
            "dependencies. It is a prototype frontier, not a parser promotion.",
            f"See [36_active_reparse_feasibility_after_state_compression_gate.md]({active_reparse_feasibility_gate_link}).",
            "",
            "### Cutoff 60 Source-State Reparse Prototype Gate",
            "",
            "A cutoff-60 prototype then executes the cheaper operational step:",
            "deterministic reparse recipes are repriced with the active",
            "`previous_copy_end` default/exception source ledger. The result",
            f"roundtrips `{source_reparse_prototype['roundtrip_book_count']}`/",
            f"`{source_reparse_prototype['book_count']}` held-out books, beats",
            f"raw digit coding in `{source_reparse_prototype['beats_raw_book_count']}`/",
            f"`{source_reparse_prototype['book_count']}`, and is",
            f"`{source_reparse_aggregate['source_state_minus_uniform_address_bits']:+.3f}`",
            "bits versus the old uniform-address reparse comparator in aggregate.",
            "Only",
            f"`{source_reparse_prototype['beats_uniform_address_reparse_book_count']}`/",
            f"`{source_reparse_prototype['book_count']}` books improve individually,",
            "and no source-state recipe reoptimization is performed.",
            f"See [37_cutoff60_source_state_reparse_prototype_gate.md]({cutoff60_source_state_reparse_prototype_gate_link}).",
            "",
            "### Multi-Cutoff Source-State Reparse Reprice Gate",
            "",
            "The same source-state repricing then generalizes across all standard",
            "prefix cutoffs `10/20/35/50/60`. Every cutoff roundtrips, every",
            "held-out book remains positive against raw digit coding, and the",
            "active `previous_copy_end` source ledger beats uniform-address reparse",
            "in aggregate at",
            f"`{multicutoff_source_reprice['aggregate_beats_uniform_cutoff_count']}`/",
            f"`{multicutoff_source_reprice['cutoff_count']}` cutoffs. Total",
            "aggregate delta across the five suffix evaluations is",
            f"`{multicutoff_source_reprice['total_source_state_minus_uniform_address_bits']:+.3f}`",
            "bits. This is still repricing of deterministic recipes, not",
            "source-state-aware recipe reoptimization.",
            f"See [38_multicutoff_source_state_reparse_reprice_gate.md]({multicutoff_source_state_reparse_reprice_gate_link}).",
            "",
            "### Multi-Cutoff Source Choice Optimizer Gate",
            "",
            "A fixed-segmentation source-choice optimizer then tests whether the",
            "same copied chunks can be sourced more cheaply without changing",
            "segmentation or copy lengths. It finds no cheaper local substitutions:",
            f"`{source_choice_optimizer['total_changed_sources']}`/",
            f"`{source_choice_optimizer['total_copy_items']}` sources change,",
            "and optimized-minus-repriced cost is",
            f"`{source_choice_optimizer['total_source_choice_minus_reprice_bits']:+.3f}`",
            "bits. This closes the simple source-only improvement path; future",
            "source-state work needs segmentation, copy-length, or global path-state",
            "optimization.",
            f"See [39_multicutoff_source_choice_optimizer_gate.md]({multicutoff_source_choice_optimizer_gate_link}).",
            "",
            "### Multi-Cutoff Global Source Path Optimizer Gate",
            "",
            "A global source-path DP then tests the stronger fixed-segmentation",
            "hypothesis: a locally worse source may be chosen if its",
            "`previous_copy_end` state makes later copies cheaper. This does improve",
            "the fixed deterministic recipes. It changes",
            f"`{global_source_path['total_changed_sources']}`/",
            f"`{global_source_path['total_copy_events']}` sources, beats the",
            "repriced ledger in",
            f"`{global_source_path['aggregate_beats_reprice_cutoff_count']}`/",
            f"`{global_source_path['cutoff_count']}` cutoffs, and totals",
            f"`{global_source_path['total_source_path_minus_reprice_bits']:+.3f}`",
            "bits versus repricing. Max DP state count is only",
            f"`{global_source_path['max_state_count']}`. Segmentation and copy",
            "lengths remain fixed, so this is a partial source-path optimizer rather",
            "than a full active parser.",
            f"See [40_multicutoff_global_source_path_optimizer_gate.md]({multicutoff_global_source_path_optimizer_gate_link}).",
            "",
            "### Full-Corpus Source Path Formula Gate",
            "",
            "The same source-path idea is then tested as a full-corpus fixed-recipe",
            "formula improvement. The exact DP is used only to propose same-chunk",
            "source substitutions; the candidate is accepted only after the real",
            "adaptive source default/exception stream is rescored. It improves the",
            "active formula from",
            f"`{full_corpus_source_path['active_total_bits']:.3f}` to",
            f"`{full_corpus_source_path['candidate_total_bits']:.3f}` bits, a",
            f"gain of `{full_corpus_source_path['candidate_gain_bits']:+.3f}` bits,",
            "by changing",
            f"`{full_corpus_source_path['changed_source_count']}`/",
            f"`{full_corpus_source_path['copy_event_count']}` sources. The",
            "copy-source ledger drops from",
            f"`{full_corpus_source_path['active_copy_source_bits']:.3f}` to",
            f"`{full_corpus_source_path['candidate_copy_source_bits']:.3f}` bits.",
            "Segmentation and copy lengths remain fixed.",
            f"See [41_full_corpus_source_path_formula_gate.md]({full_corpus_source_path_formula_gate_link}).",
            "",
            "### Full-Corpus Source Substitution Frontier Gate",
            "",
            "The promoted fixed-recipe source-path formula is then checked for a",
            "local single/pair substitution frontier. Every same-chunk legal source",
            "single and pair is rescored under the full adaptive source stream. The",
            "best pair changes two source positions and improves the bound from",
            f"`{source_substitution_frontier['active_total_bits']:.3f}` to",
            f"`{source_substitution_frontier['candidate_total_bits']:.3f}` bits,",
            "a gain of",
            f"`{source_substitution_frontier['candidate_gain_bits']:+.3f}` bits.",
            "The gate searches",
            f"`{source_substitution_frontier['single_substitution_count']}` singles",
            "and",
            f"`{source_substitution_frontier['pair_substitution_count']}` pairs;",
            "triples and higher-order substitutions remain outside this frontier.",
            f"See [42_full_corpus_source_substitution_frontier_gate.md]({full_corpus_source_substitution_frontier_gate_link}).",
            "",
            "### Full-Corpus Source Substitution Second-Pass Gate",
            "",
            "The same single/pair frontier is rerun on the promoted source-substitution",
            "formula. It still finds a positive pair, but only a microscopic one:",
            f"`{source_substitution_second_pass['active_total_bits']:.6f}` to",
            f"`{source_substitution_second_pass['candidate_total_bits']:.6f}` bits,",
            "a gain of",
            f"`{source_substitution_second_pass['candidate_gain_bits']:+.6f}` bits.",
            "This updates the compression bound but does not strengthen the generation",
            "explanation; triples and higher-order substitutions remain outside this gate.",
            f"See [43_full_corpus_source_substitution_second_pass_gate.md]({full_corpus_source_substitution_second_pass_gate_link}).",
            "",
            "### Full-Corpus Source Substitution Third-Pass Gate",
            "",
            "A third pass over the same single/pair frontier still finds a positive",
            "pair, but the gain shrinks again:",
            f"`{source_substitution_third_pass['active_total_bits']:.6f}` to",
            f"`{source_substitution_third_pass['candidate_total_bits']:.6f}` bits,",
            "a gain of",
            f"`{source_substitution_third_pass['candidate_gain_bits']:+.6f}` bits.",
            "This reinforces that the local source frontier is entering saturation;",
            "it remains only a compression-bound update.",
            f"See [44_full_corpus_source_substitution_third_pass_gate.md]({full_corpus_source_substitution_third_pass_gate_link}).",
            "",
            "### Full-Corpus Source Substitution Fourth-Pass Gate",
            "",
            "A fourth pass over the same single/pair frontier still finds a positive",
            "pair, but the gain shrinks again:",
            f"`{source_substitution_fourth_pass['active_total_bits']:.6f}` to",
            f"`{source_substitution_fourth_pass['candidate_total_bits']:.6f}` bits,",
            "a gain of",
            f"`{source_substitution_fourth_pass['candidate_gain_bits']:+.6f}` bits.",
            "This is compression-bound bookkeeping and local source-frontier",
            "saturation, not new generation evidence.",
            f"See [45_full_corpus_source_substitution_fourth_pass_gate.md]({full_corpus_source_substitution_fourth_pass_gate_link}).",
            "",
            "### Source Substitution Saturation Audit",
            "",
            "The source-substitution series is then converted into an explicit",
            "stop-rule audit. The last three pass gains sum to only",
            f"`{source_substitution_saturation['tail_cumulative_gain_bits']:.6f}` bits,",
            "and the last pass has positive pairs in only",
            f"`{source_substitution_saturation['last_pass_positive_pair_fraction']:.6f}`",
            "of searched pair candidates. A minimum pair-selector floor is",
            f"`{source_substitution_saturation['minimum_pair_selector_floor_bits']:.3f}`",
            "bits, dwarfing the latest unpriced gain. The local same-chunk source",
            "frontier is therefore saturated as a mainline path; future progress",
            "needs structure, holdout prediction, or row0-origin evidence.",
            f"See [46_source_substitution_saturation_audit.md]({source_substitution_saturation_audit_link}).",
            "",
            "### Source Blocker Structural Context Gate",
            "",
            "The remaining cross-op optional-literal near tie is then tested as a",
            "source-cost blocker. The candidate is only `+0.027` bits worse than",
            "active, and a source-free oracle would be `-11.209` bits better, but",
            "that oracle is not decodable because it removes the required copy-source",
            "choice. The best tested simple source context, `book_half`, is still",
            "`+5.872` bits worse than the global source prior and loses in `5/5`",
            "prefix-frozen splits. This localizes the next source frontier: a future",
            "advance needs a new source derivation or representation, not a simple",
            "declared context split.",
            f"See [24_source_blocker_structural_context_gate.md]({source_blocker_structural_context_gate_link}).",
            "",
            "### Source Canonicality Decodability Gate",
            "",
            "The strongest source-derivation clue is then separated from decoder",
            "requirements. Every declared copy source is the earliest legal",
            "occurrence of the copied chunk (`261/261`), but only `123/261` source",
            "choices are unique at the declared length and `138/261` are ambiguous.",
            "More importantly, the earliest-exact-chunk rule depends on the future",
            "target chunk, which the decoder does not know until source and length",
            "are resolved. Source canonicality is therefore retained as encoder",
            "regularity, while the decodable default/exception source ledger remains",
            "the valid source representation.",
            f"See [25_source_canonicality_decodability_gate.md]({source_canonicality_decodability_gate_link}).",
            "",
            "### Source State Dependency Gate",
            "",
            "A final source-state gate then checks whether the active previous-copy",
            "source/length dependency can be removed by a decoder-computable",
            "state-free default. It cannot under the tested rules. The exact active",
            "reparse still needs state key",
            "`(book_pos, previous_item, previous_copy_source, previous_copy_length)`,",
            "and the best state-free rule, `state_free_back_current_length`, is",
            "`+15.186` bits worse on the full source ledger. It also loses all",
            "`5/5` prefix-frozen checks, with gap min/mean/max `7.652` /",
            "`14.615` / `22.840` bits. This keeps source state as a real",
            "generation-boundary dependency, not a removable tie-break.",
            f"See [26_source_state_dependency_gate.md]({source_state_dependency_gate_link}).",
            "",
            "### Source Selection Derivation Boundary Gate",
            "",
            "The source-selection boundary is then consolidated across canonicality,",
            "negative controls, distance coding, and state-free defaults. All",
            "`261/261` copy sources are earliest legal exact-chunk sources, while",
            "latest source matches only `123/261`, previous source `0/261`, and",
            "previous-source-plus-length `5/261`; random candidate choice expects",
            "`169.473` hits. But the earliest rule depends on future target text,",
            "so it is not decoder-computable. Backward-distance source coding is",
            "`+25.551` bits worse and loses all prefix frozen and online splits,",
            "and the best state-free default remains `+15.186` bits worse. Copy",
            "source is therefore canonical but still declared.",
            f"See [31_source_selection_derivation_boundary_gate.md]({source_selection_derivation_boundary_gate_link}).",
            "",
            "### Copy Length Midpoint Context Gate",
            "",
            "The copy-length context is then checked as a positive generalization",
            "case. The active natural midpoint split, `book_id < 35`, beats the",
            "global copy-length context by `13.839` bits, ranks `2` among all",
            "one-cut boundaries, wins all `5/5` prefix-frozen future-suffix checks,",
            "and passes book-id permutation controls (`p=0.0033`). The best searched",
            "cutoff, `37`, is only `0.256` bits better than midpoint, so it is not",
            "promoted as a new boundary. This strengthens one learned mechanical",
            "component while leaving the full recipe and row0 origin unchanged.",
            f"See [27_copy_length_midpoint_context_gate.md]({copy_length_midpoint_context_gate_link}).",
            "",
            "### Copy Length Derivation Boundary Gate",
            "",
            "The copy-length dependency is then separated into encoder-only and",
            "decoder-valid pieces. The high-coverage target-max rule matches",
            "`238/261` copy lengths, but it is not decodable because it needs",
            "future target text. The retained decoder-valid model is",
            "`decoder_max_possible` default plus adaptive exceptions: `60`",
            "defaults and `201` exceptions, with `136.884` bits of upstream gain.",
            "The midpoint context is supported, but the compact recipe still",
            "declares `261` copy-length fields covering `10406` copied digits.",
            f"See [32_copy_length_derivation_boundary_gate.md]({copy_length_derivation_boundary_gate_link}).",
            "",
            "### Literal Copy Availability Gate",
            "",
            "The literal payload is then separated into forced literals and residual",
            "parser choices. Most literal operations are forced by copy",
            "unavailability: `73/87` literal starts and `760/857` literal digits",
            "have no legal `min_len` copy candidate. The optional frontier is",
            "localized to `14` starts and `97` digits. Simple in-literal copy",
            "repairs score `74` candidates and remain at least `+1.180` bits worse;",
            "cross-op repairs score `465` candidates and the best is still",
            "`+0.027` bits worse. The near tie saves literal/item bits but pays",
            "`+11.237` copy-source and `+1.639` copy-length bits, so literal",
            "externality is reduced but not removed.",
            f"See [28_literal_copy_availability_gate.md]({literal_copy_availability_gate_link}).",
            "",
            "### Literal Payload Model Gate",
            "",
            "After forced literal availability is separated, the residual literal",
            "payload model still cannot be simplified under the tested controls.",
            "The current order-2 previous-emitted-digit categorical model costs",
            "`2613.661` bits over `857` literal digits. Order-1 wins some",
            "intermediate frozen splits, but is `+95.968` bits worse on the full",
            "corpus, `+47.346` bits worse in aggregate online prefix totals, and",
            "`+28.609` bits worse in aggregate frozen prefix totals. The best",
            "modal default/exception candidate is `+38.049` bits worse, and the",
            "best non-active structural context is `+19.159` bits worse. The",
            "payload dependency is therefore retained, not removed.",
            f"See [29_literal_payload_model_gate.md]({literal_payload_model_gate_link}).",
            "",
            "### Current Formula Dependency Scoreboard",
            "",
            "The current formula dependency scoreboard then re-counts the latest",
            "local-source-bound formula directly. It roundtrips `70/70` books with",
            f"`{current_dependency_counts['op_count']}` ops:",
            f"`{current_dependency_counts['literal_op_count']}` literals and",
            f"`{current_dependency_counts['copy_op_count']}` copies. It still",
            "declares literal payload, copy source, and copy length. Copy-source",
            "selection was encoder-canonical before the later source-substitution",
            "passes, but the latest formula now needs a joint source/length check",
            "because some substitutions trade canonicality for source-stream cost.",
            "Copy length is partly decodable but still carries exceptions; literal payload is",
            "mostly forced and downstream of source/length choices. The next",
            "mainline mechanical test should therefore be a structural",
            "decoder-known source/length parser or objective, not another local",
            "same-chunk source edit.",
            f"See [48_current_formula_dependency_scoreboard.md]({current_formula_dependency_scoreboard_link}).",
            "",
            "### Source-Length Joint Derivability Audit",
            "",
            "The joint audit then tests source and length as one dependency rather",
            "than two independent ledgers. It finds that the latest source-substituted",
            "formula no longer preserves the earlier `261/261` all-earliest source",
            "pattern: current earliest coverage is",
            f"`{source_length_joint['earliest_source_hits_at_declared_length']}`/",
            f"`{source_length_joint['copy_event_count']}`, a",
            f"`{source_length_joint['source_substitution_non_earliest_delta_vs_prior_boundary']}`",
            "event delta from the prior boundary. Target-max length remains strong",
            f"at `{source_length_joint['encoder_target_max_length_hits_after_declared_source']}`/",
            f"`{source_length_joint['copy_event_count']}`, and joint",
            "earliest+target-max covers",
            f"`{source_length_joint['joint_encoder_earliest_target_max_hits']}`/",
            f"`{source_length_joint['copy_event_count']}`, but both rules need",
            "future target text and are encoder-oracle only. The decoder-valid",
            "declared-source plus decoder-max rule covers only",
            f"`{source_length_joint['joint_declared_source_decoder_max_hits']}`/",
            f"`{source_length_joint['copy_event_count']}` copy events, while",
            "a state-only previous-end+decoder-max rule covers",
            f"`{source_length_joint['joint_previous_end_decoder_max_hits']}`/",
            f"`{source_length_joint['copy_event_count']}`. Source and length",
            "therefore remain declared dependencies; the structural-parser target",
            "is sharper, but no formula or bound is promoted.",
            f"See [49_source_length_joint_derivability_audit.md]({source_length_joint_derivability_audit_link}).",
            "",
            "### Source Canonicality Tradeoff Audit",
            "",
            "The canonicality tradeoff audit then prices the simpler all-earliest",
            "source explanation profile against the current lower compression bound.",
            "Restoring all copy sources to the earliest legal occurrence repairs",
            f"`{source_canonicality_tradeoff['current_non_earliest_count']}`",
            "non-earliest events and returns source coverage to all-earliest, but",
            "raises the total from",
            f"`{source_canonicality_tradeoff['current_total_bits']:.6f}` to",
            f"`{source_canonicality_tradeoff['all_earliest_total_bits']:.6f}`",
            "bits, a delta of",
            f"`{source_canonicality_tradeoff['all_earliest_delta_vs_current_bits']:+.6f}`",
            "bits. This exactly separates ledgers: the current formula remains the",
            "compression bound, while the all-earliest variant is the cleaner",
            "generation-explanation profile. The all-latest negative control is",
            f"`{source_canonicality_tradeoff['all_latest_delta_vs_current_bits']:+.6f}`",
            "bits worse than current.",
            f"See [50_source_canonicality_tradeoff_audit.md]({source_canonicality_tradeoff_audit_link}).",
            "",
            "### Copy Length Segmentation Exception Audit",
            "",
            "The copy-length side then gets the same structural treatment. The",
            "target-max length rule still matches",
            f"`{copy_length_segmentation['target_max_match_count']}`/",
            f"`{copy_length_segmentation['copy_event_count']}` copy events,",
            "but the",
            f"`{copy_length_segmentation['target_max_exception_count']}`",
            "exceptions are not clean absorbable suffixes. In every exception,",
            "extending to target-max enters exactly one following operation and",
            "stops inside it; it absorbs `0` whole following ops and reaches book",
            "end `0` times. The slack totals",
            f"`{copy_length_segmentation['target_max_slack_digits_total']}`",
            "digits, mostly into following copy ops",
            f"`{copy_length_segmentation['covered_following_digits_by_type']}`.",
            "This makes copy-length progress a resegmentation problem, not a",
            "scalar default problem.",
            f"See [51_copy_length_segmentation_exception_audit.md]({copy_length_segmentation_exception_audit_link}).",
            "",
            "### Target-Max Resegmentation Candidate Audit",
            "",
            "The next gate then applies that rewrite locally: extend the copy to",
            "target-max and trim the following operation. It tests",
            f"`{targetmax_resegmentation['candidate_count']}` candidates across",
            f"`{targetmax_resegmentation['exception_count']}` exceptions.",
            f"`{targetmax_resegmentation['valid_candidate_count']}` candidates",
            "roundtrip and score under the compatible component proxy, and",
            f"`{targetmax_resegmentation['improving_proxy_candidate_count']}`",
            "are proxy improvements. The best proxy candidate is",
            f"`{targetmax_resegmentation['best_proxy_delta_bits']:+.6f}` bits",
            "at book",
            f"`{targetmax_resegmentation['best_candidate']['book']}` op",
            f"`{targetmax_resegmentation['best_candidate']['op_index']}`",
            "using",
            f"`{targetmax_resegmentation['best_candidate']['mode']}`.",
            "This is not a promoted compression bound: the proxy lacks the exact",
            "current source-substitution ledger. It opens the next concrete path:",
            "an exact bound scorer or joint reparse objective for target-max",
            "resegmentation.",
            f"See [52_targetmax_resegmentation_candidate_audit.md]({targetmax_resegmentation_candidate_audit_link}).",
            "",
            "## Row0 Origin Boundary",
            "",
            f"Row0 classification: `{result['row0_origin']['classification']}`",
            "",
            "### What Row0 Explains",
        ]
    )
    for item in result["row0_origin"]["what_row0_explains"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("### What Remains Exogenous")
    for item in result["row0_origin"]["what_remains_exogenous"]:
        lines.append(f"- {item}")

    substrate = result["row0_origin"]["substrate_facts"]
    lines.extend(
        [
            "",
            "### Substrate Facts",
            "",
            f"- Books in committed digit corpus: `{substrate['book_count']}`",
            f"- Row0 symbols: `{substrate['row0_symbol_count']}`",
            f"- Class codes represented: `{substrate['class_code_count']}`",
            f"- Missing two-digit codes from class map: `{substrate['missing_two_digit_codes']}`",
            f"- Sources: [`occ_streams.json`]({audit_link_prefix}/homophone_channel/occ_streams.json), [`books_digits.json`]({audit_link_prefix}/books_digits.json)",
            "",
            "### Origin Hypotheses",
            "",
            "| Hypothesis | Status | Coverage | Cost | Contradictions / controls |",
            "|---|---|---|---:|---|",
        ]
    )
    for row in result["row0_origin"]["hypotheses"]:
        cost = row["descriptive_cost_bits"]
        cost_text = f"{cost:.3f}" if isinstance(cost, (int, float)) else str(cost)
        lines.append(
            f"| `{row['hypothesis']}` | `{row['status']}` | {row['coverage']} | "
            f"{cost_text} | {row['contradictions']}; controls `{row['negative_controls']}` |"
        )

    lines.extend(
        [
            "",
            "### Row0 Requirement Matrix Follow-Up",
            "",
            "A requirement-matrix follow-up forces all six requested row0-origin families",
            "through the same checklist: algorithm, descriptive cost, coverage,",
            "contradictions, negative controls, and random/permuted comparison. All six",
            "families have explicit entries; promoted row0-origin formulas remain `0`.",
            "Lookup baselines are `160.521` bits given inventory, `209.405` bits for the",
            "direct symbol alphabet, and `214.879` bits for the direct observed-label",
            "alphabet.",
            f"See [05_row0_hypothesis_requirement_audit.md]({row0_requirement_link}).",
            "",
            "### Row0 Parallel Provenance Bridge",
            "",
            "The independent row0-origin parallel front is then bridged back into",
            "this audit. It traces local project provenance through workbook, import,",
            "reconstruction, and audit layers, but still leaves CipSoft/authorial",
            "origin untraced. Its paid-anchor gate confirms the boundary: all",
            "worksheet anchors have a nominal",
            f"`{row0_parallel_provenance['all_anchors_nominal_reduction_bits']:.3f}`",
            "bit reduction, but after explicit pair+label costs they are",
            f"`{row0_parallel_provenance['all_anchors_explicit_pair_label_net_bits']:.3f}`",
            "bits versus lookup. Rare singleton anchors have nominal signal",
            f"`{row0_parallel_provenance['rare_singletons_nominal_reduction_bits']:.3f}`",
            "bits but net to",
            f"`{row0_parallel_provenance['rare_singletons_explicit_pair_label_net_bits']:.3f}`",
            "after paying label data. Ordered-surface asymmetry remains a real",
            "mechanical clue, not a label-origin formula.",
            f"See [47_row0_parallel_provenance_bridge_audit.md]({row0_parallel_provenance_bridge_link}).",
            "",
            "## Decision",
            "",
            "- `8558.667` bits remains a frozen validation scope here, not a final authorial method.",
            "- The learned component signal survives prefix and block holdout but fails some family holdouts, so it is not promoted beyond partial predictive structure.",
            "- The full-corpus fixed-recipe limitation is partially reduced by deterministic reparse evidence; after same-coordinate address correction, public-bookcase family reparse beats or ties the active family recipe in `19/19` families, a no-test-carryover variant still beats raw in `19/19`, singleton leave-one-book-out reparsing beats raw in `70/70`, singleton copy sources are attributed, the signal survives book-bounded and same-family-excluded source constraints, the online previous-books-only frontier is positive after the bootstrap book, and a raw book-0 seed policy closes the remaining local failure but fails complete-formula promotion because literal-payload cost dominates and any exception signal would require negative cost.",
            "- Source-state simplification is rejected: canonicality is encoder-side only, and state-free source defaults lose to the active previous-copy source/length default in the full ledger and every tested prefix-frozen split.",
            "- Copy-source selection is encoder-canonical but not decoder-derived: earliest-source hits `261/261`, while distance and state-free replacements lose.",
            "- Copy-length midpoint context is retained as a generalizing natural split; the searched cutoff `37` is rejected as ad-hoc for only `0.256` bits over midpoint.",
            "- Copy length is partly remodeled but not derived: target-max is encoder-only, and the compact recipe still declares all `261` copy lengths.",
            "- Literal externality is reduced but not removed: most literal payload is forced by copy unavailability, and the residual local repair families are worse under the active ledger.",
            "- The literal payload model remains order-2 previous-emitted-digit context: order-1, modal default/exception coding, and simple structural contexts all fail as replacements.",
            f"- The current formula dependency scoreboard maps the retained declarations on the latest formula: `{current_dependency_counts['literal_op_count']}` literal payload fields, `{current_dependency_counts['copy_op_count']}` copy-source fields, and `{current_dependency_counts['copy_op_count']}` copy-length fields; it prioritizes a structural source/length parser before more literal or item-type work.",
            "- Recipe representation artifacts are removed without changing the score: book length, copy target start, literal length, and op type are derivable; literal text, copy source, and copy length remain declared.",
            "- Item-type split-only remains a retained generation-profile stream, while compact recipe op `type` fields are derivable from operation shape.",
            "- The current active `8177.317`-bit profile has positive frozen gain on every tested prefix, block, and public-bookcase family split, but recipe discovery remains blocked by path-dependent copy-source state.",
            "- Copy-source state is compressed from previous `(source, length)` to `previous_copy_end`, preserving the active default/exception ledger and reducing the candidate-state proxy, but no active parser is promoted.",
            "- After that compression, every tested book-level source-state proxy is below one million and the late-cutoff frontier is smaller, so a book-local active-source prototype is now plausible by proxy; the complete active parser is still unpromoted.",
            "- Cutoff-60 deterministic reparse recipes can be repriced with the active `previous_copy_end` source ledger: `10/10` roundtrip, `10/10` raw wins, and `-10.241` aggregate bits versus uniform-address reparse, but only `4/10` books improve individually and no recipe is reoptimized.",
            "- Multi-cutoff source-state repricing generalizes that aggregate signal across cutoffs `10/20/35/50/60`: `5/5` cutoffs improve versus uniform-address reparse, totaling `-112.968` bits, while still not reoptimizing recipes.",
            "- Fixed-segmentation source-choice optimization finds `0/514` cheaper source substitutions, so the simple source-only improvement path is closed under the immediate `previous_copy_end` cost.",
            "- Global fixed-segmentation source-path optimization improves the repriced ledger by `-42.359` bits, changing `10/514` sources with max DP state count `14`; segmentation and copy lengths remain fixed.",
            "- Full-corpus fixed-recipe source-path optimization survives adaptive rescore and lowers the active bound from `8177.317` to `8162.412` bits by changing `2/261` source positions; segmentation and copy lengths remain fixed.",
            "- Full-corpus single/pair source-substitution frontier search lowers the active bound from `8162.412` to `8160.827` bits; triples and higher-order substitutions remain unsearched.",
            "- A second single/pair source-substitution pass finds only a microscopic `+0.000671` bit gain, lowering the active bound to `8160.826421`; this is a compression-bound update, not stronger generation evidence.",
            "- A third single/pair source-substitution pass finds another microscopic `+0.000503` bit gain, lowering the active bound to `8160.825917`; local source substitutions are saturating.",
            "- A fourth single/pair source-substitution pass finds another microscopic `+0.000310` bit gain, lowering the active bound to `8160.825608`; local source substitutions are saturating.",
            "- The source-substitution saturation audit freezes repeated same-chunk local source edits as no longer mainline: the last three gains sum to `0.001484` bits and are dwarfed by selector-cost sanity checks.",
            "- All requested row0-origin hypothesis families have been checklist-audited; none passes as an origin formula.",
            "- The row0 parallel provenance bridge traces workbook/import/reconstruction/audit layers but leaves CipSoft origin untraced; paid worksheet anchors do not beat lookup once pair and label costs are charged.",
            "- `row0` continues exogenous: the active book generator assumes the table rather than deriving it.",
            "- No translation, plaintext, or case reopening is introduced.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    legacy_module = load_module(LEGACY_SCRIPT)
    legacy_module.main()
    legacy = load_json(LEGACY_RESULT)
    if abs(float(legacy["compression_bound_bits_confirmed"]) - SCOPE_COMPRESSION_BOUND_BITS) > 1e-6:
        raise RuntimeError("legacy audit no longer matches frozen 8558.667-bit scope")
    result = make_result(legacy)

    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    result_path = TEST_RESULTS / "01_prequential_and_row0_origin_audit.json"
    report_path = TEST_RESULTS / "01_prequential_and_row0_origin_audit.md"
    final_report_path = REPORTS / "prequential_and_row0_origin_audit.md"

    result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(
        render_markdown(
            result,
            audit_link_prefix="../../../audit_20260609",
            family_failure_link="02_family_holdout_failure_audit.md",
            component_selector_link="03_train_cv_component_selector_audit.md",
            recipe_externality_link="04_recipe_externality_audit.md",
            recipe_reparse_matrix_link="06_recipe_reparse_evidence_matrix.md",
            recipe_family_holdout_link="08_recipe_reparse_family_holdout.md",
            recipe_family_loss_decomposition_link="09_recipe_reparse_family_loss_decomposition.md",
            family_holdout_address_space_link="10_family_holdout_address_space_audit.md",
            family_holdout_address_corrected_scoreboard_link="11_family_holdout_address_corrected_scoreboard.md",
            family_holdout_no_test_carryover_link="12_family_holdout_no_test_carryover_audit.md",
            leave_one_book_out_no_self_link="13_leave_one_book_out_no_self_audit.md",
            leave_one_book_out_source_attribution_link=(
                "14_leave_one_book_out_source_attribution_audit.md"
            ),
            leave_one_book_out_book_bounded_source_link=(
                "15_leave_one_book_out_book_bounded_source_audit.md"
            ),
            leave_one_book_out_family_excluded_source_link=(
                "16_leave_one_book_out_family_excluded_source_audit.md"
            ),
            online_prefix_book_frontier_link="17_online_prefix_book_frontier_audit.md",
            online_bootstrap_seed_policy_link="18_online_bootstrap_seed_policy_audit.md",
            seeded_online_formula_rescore_link="19_seeded_online_formula_rescore_audit.md",
            seeded_rescore_loss_decomposition_link=(
                "20_seeded_rescore_loss_decomposition.md"
            ),
            seed_exception_signal_cost_link="21_seed_exception_signal_cost_audit.md",
            online_order_frontier_controls_link="22_online_order_frontier_controls.md",
            order_frontier_promotion_gate_link="23_order_frontier_promotion_gate.md",
            recipe_representation_dependency_gate_link=(
                "30_recipe_representation_dependency_gate.md"
            ),
            item_type_op_shape_boundary_gate_link=(
                "33_item_type_op_shape_boundary_gate.md"
            ),
            current_active_profile_boundary_gate_link=(
                "34_current_active_profile_boundary_gate.md"
            ),
            copy_source_state_compression_gate_link=(
                "35_copy_source_state_compression_gate.md"
            ),
            active_reparse_feasibility_gate_link=(
                "36_active_reparse_feasibility_after_state_compression_gate.md"
            ),
            cutoff60_source_state_reparse_prototype_gate_link=(
                "37_cutoff60_source_state_reparse_prototype_gate.md"
            ),
            multicutoff_source_state_reparse_reprice_gate_link=(
                "38_multicutoff_source_state_reparse_reprice_gate.md"
            ),
            multicutoff_source_choice_optimizer_gate_link=(
                "39_multicutoff_source_choice_optimizer_gate.md"
            ),
            multicutoff_global_source_path_optimizer_gate_link=(
                "40_multicutoff_global_source_path_optimizer_gate.md"
            ),
            full_corpus_source_path_formula_gate_link=(
                "41_full_corpus_source_path_formula_gate.md"
            ),
            full_corpus_source_substitution_frontier_gate_link=(
                "42_full_corpus_source_substitution_frontier_gate.md"
            ),
            full_corpus_source_substitution_second_pass_gate_link=(
                "43_full_corpus_source_substitution_second_pass_gate.md"
            ),
            full_corpus_source_substitution_third_pass_gate_link=(
                "44_full_corpus_source_substitution_third_pass_gate.md"
            ),
            full_corpus_source_substitution_fourth_pass_gate_link=(
                "45_full_corpus_source_substitution_fourth_pass_gate.md"
            ),
            source_substitution_saturation_audit_link=(
                "46_source_substitution_saturation_audit.md"
            ),
            source_blocker_structural_context_gate_link=(
                "24_source_blocker_structural_context_gate.md"
            ),
            source_canonicality_decodability_gate_link=(
                "25_source_canonicality_decodability_gate.md"
            ),
            source_state_dependency_gate_link="26_source_state_dependency_gate.md",
            source_selection_derivation_boundary_gate_link=(
                "31_source_selection_derivation_boundary_gate.md"
            ),
            copy_length_midpoint_context_gate_link=(
                "27_copy_length_midpoint_context_gate.md"
            ),
            copy_length_derivation_boundary_gate_link=(
                "32_copy_length_derivation_boundary_gate.md"
            ),
            literal_copy_availability_gate_link="28_literal_copy_availability_gate.md",
            literal_payload_model_gate_link="29_literal_payload_model_gate.md",
            current_formula_dependency_scoreboard_link=(
                "48_current_formula_dependency_scoreboard.md"
            ),
            source_length_joint_derivability_audit_link=(
                "49_source_length_joint_derivability_audit.md"
            ),
            source_canonicality_tradeoff_audit_link=(
                "50_source_canonicality_tradeoff_audit.md"
            ),
            copy_length_segmentation_exception_audit_link=(
                "51_copy_length_segmentation_exception_audit.md"
            ),
            targetmax_resegmentation_candidate_audit_link=(
                "52_targetmax_resegmentation_candidate_audit.md"
            ),
            row0_requirement_link="05_row0_hypothesis_requirement_audit.md",
            row0_parallel_provenance_bridge_link=(
                "47_row0_parallel_provenance_bridge_audit.md"
            ),
        ),
        encoding="utf-8",
    )
    final_report_path.write_text(
        render_markdown(
            result,
            audit_link_prefix="../../audit_20260609",
            family_failure_link="test_results/02_family_holdout_failure_audit.md",
            component_selector_link="test_results/03_train_cv_component_selector_audit.md",
            recipe_externality_link="test_results/04_recipe_externality_audit.md",
            recipe_reparse_matrix_link="test_results/06_recipe_reparse_evidence_matrix.md",
            recipe_family_holdout_link="test_results/08_recipe_reparse_family_holdout.md",
            recipe_family_loss_decomposition_link="test_results/09_recipe_reparse_family_loss_decomposition.md",
            family_holdout_address_space_link="test_results/10_family_holdout_address_space_audit.md",
            family_holdout_address_corrected_scoreboard_link=(
                "test_results/11_family_holdout_address_corrected_scoreboard.md"
            ),
            family_holdout_no_test_carryover_link=(
                "test_results/12_family_holdout_no_test_carryover_audit.md"
            ),
            leave_one_book_out_no_self_link="test_results/13_leave_one_book_out_no_self_audit.md",
            leave_one_book_out_source_attribution_link=(
                "test_results/14_leave_one_book_out_source_attribution_audit.md"
            ),
            leave_one_book_out_book_bounded_source_link=(
                "test_results/15_leave_one_book_out_book_bounded_source_audit.md"
            ),
            leave_one_book_out_family_excluded_source_link=(
                "test_results/16_leave_one_book_out_family_excluded_source_audit.md"
            ),
            online_prefix_book_frontier_link=(
                "test_results/17_online_prefix_book_frontier_audit.md"
            ),
            online_bootstrap_seed_policy_link=(
                "test_results/18_online_bootstrap_seed_policy_audit.md"
            ),
            seeded_online_formula_rescore_link=(
                "test_results/19_seeded_online_formula_rescore_audit.md"
            ),
            seeded_rescore_loss_decomposition_link=(
                "test_results/20_seeded_rescore_loss_decomposition.md"
            ),
            seed_exception_signal_cost_link=(
                "test_results/21_seed_exception_signal_cost_audit.md"
            ),
            online_order_frontier_controls_link=(
                "test_results/22_online_order_frontier_controls.md"
            ),
            order_frontier_promotion_gate_link=(
                "test_results/23_order_frontier_promotion_gate.md"
            ),
            recipe_representation_dependency_gate_link=(
                "test_results/30_recipe_representation_dependency_gate.md"
            ),
            item_type_op_shape_boundary_gate_link=(
                "test_results/33_item_type_op_shape_boundary_gate.md"
            ),
            current_active_profile_boundary_gate_link=(
                "test_results/34_current_active_profile_boundary_gate.md"
            ),
            copy_source_state_compression_gate_link=(
                "test_results/35_copy_source_state_compression_gate.md"
            ),
            active_reparse_feasibility_gate_link=(
                "test_results/36_active_reparse_feasibility_after_state_compression_gate.md"
            ),
            cutoff60_source_state_reparse_prototype_gate_link=(
                "test_results/37_cutoff60_source_state_reparse_prototype_gate.md"
            ),
            multicutoff_source_state_reparse_reprice_gate_link=(
                "test_results/38_multicutoff_source_state_reparse_reprice_gate.md"
            ),
            multicutoff_source_choice_optimizer_gate_link=(
                "test_results/39_multicutoff_source_choice_optimizer_gate.md"
            ),
            multicutoff_global_source_path_optimizer_gate_link=(
                "test_results/40_multicutoff_global_source_path_optimizer_gate.md"
            ),
            full_corpus_source_path_formula_gate_link=(
                "test_results/41_full_corpus_source_path_formula_gate.md"
            ),
            full_corpus_source_substitution_frontier_gate_link=(
                "test_results/42_full_corpus_source_substitution_frontier_gate.md"
            ),
            full_corpus_source_substitution_second_pass_gate_link=(
                "test_results/43_full_corpus_source_substitution_second_pass_gate.md"
            ),
            full_corpus_source_substitution_third_pass_gate_link=(
                "test_results/44_full_corpus_source_substitution_third_pass_gate.md"
            ),
            full_corpus_source_substitution_fourth_pass_gate_link=(
                "test_results/45_full_corpus_source_substitution_fourth_pass_gate.md"
            ),
            source_substitution_saturation_audit_link=(
                "test_results/46_source_substitution_saturation_audit.md"
            ),
            source_blocker_structural_context_gate_link=(
                "test_results/24_source_blocker_structural_context_gate.md"
            ),
            source_canonicality_decodability_gate_link=(
                "test_results/25_source_canonicality_decodability_gate.md"
            ),
            source_state_dependency_gate_link=(
                "test_results/26_source_state_dependency_gate.md"
            ),
            source_selection_derivation_boundary_gate_link=(
                "test_results/31_source_selection_derivation_boundary_gate.md"
            ),
            copy_length_midpoint_context_gate_link=(
                "test_results/27_copy_length_midpoint_context_gate.md"
            ),
            copy_length_derivation_boundary_gate_link=(
                "test_results/32_copy_length_derivation_boundary_gate.md"
            ),
            literal_copy_availability_gate_link=(
                "test_results/28_literal_copy_availability_gate.md"
            ),
            literal_payload_model_gate_link=(
                "test_results/29_literal_payload_model_gate.md"
            ),
            current_formula_dependency_scoreboard_link=(
                "test_results/48_current_formula_dependency_scoreboard.md"
            ),
            source_length_joint_derivability_audit_link=(
                "test_results/49_source_length_joint_derivability_audit.md"
            ),
            source_canonicality_tradeoff_audit_link=(
                "test_results/50_source_canonicality_tradeoff_audit.md"
            ),
            copy_length_segmentation_exception_audit_link=(
                "test_results/51_copy_length_segmentation_exception_audit.md"
            ),
            targetmax_resegmentation_candidate_audit_link=(
                "test_results/52_targetmax_resegmentation_candidate_audit.md"
            ),
            row0_requirement_link="test_results/05_row0_hypothesis_requirement_audit.md",
            row0_parallel_provenance_bridge_link=(
                "test_results/47_row0_parallel_provenance_bridge_audit.md"
            ),
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
