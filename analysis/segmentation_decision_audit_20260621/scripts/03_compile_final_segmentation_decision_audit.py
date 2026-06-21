from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

TRACE = TEST_RESULTS / "01_segmentation_decision_trace.json"
STRUCTURAL = TEST_RESULTS / "02_structural_segmentation_hypothesis_audit.json"
DEPENDENCY = TEST_RESULTS / "04_parser_dependency_reduction_ledger.json"
LITERAL_GAP = TEST_RESULTS / "05_literal_gap_boundary_audit.json"
ONLINE_LITERAL = TEST_RESULTS / "06_online_literal_stop_rule_audit.json"
LITERAL_EXCEPTION = TEST_RESULTS / "07_literal_stop_exception_topology_audit.json"
INTEGRATED_ONLINE = TEST_RESULTS / "08_integrated_online_literal_parser_audit.json"
POLICY_DRIFT = TEST_RESULTS / "09_integrated_parser_policy_and_drift_audit.json"
OVERRIDE = TEST_RESULTS / "10_integrated_parser_override_audit.json"
PEAK_STRENGTH = TEST_RESULTS / "11_integrated_parser_peak_strength_audit.json"
RESIDUAL_CONTEXT = TEST_RESULTS / "12_integrated_parser_residual_context_audit.json"
GLOBAL_OBJECTIVE = TEST_RESULTS / "13_global_objective_parser_audit.json"
FEATURE_WEIGHTED = TEST_RESULTS / "14_feature_weighted_global_parser_audit.json"
SOURCE_BOUNDARY = TEST_RESULTS / "15_source_boundary_alignment_audit.json"
DRIFT_REPAIR = TEST_RESULTS / "16_single_drift_repair_oracle_audit.json"
OBSERVABLE_REPAIR = TEST_RESULTS / "17_observable_repair_policy_audit.json"
CONDITIONAL_REPAIR = TEST_RESULTS / "18_conditional_repair_classifier_audit.json"
TWO_STAGE_REPAIR = TEST_RESULTS / "19_two_stage_conditional_repair_audit.json"
POST_REPAIR_ORACLE = TEST_RESULTS / "20_post_repair_residual_oracle_audit.json"
RESIDUAL_FEATURE = TEST_RESULTS / "21_post_repair_residual_feature_audit.json"
BRANCH_CONTINUATION = TEST_RESULTS / "22_residual_branch_continuation_audit.json"
BRANCH_RANKER = TEST_RESULTS / "23_branch_ranker_prequential_audit.json"
CONTEXTUAL_MODE = TEST_RESULTS / "24_contextual_mode_selector_audit.json"
CONTEXTUAL_STABILITY = TEST_RESULTS / "25_contextual_mode_stability_audit.json"
HIERARCHICAL_BACKOFF = TEST_RESULTS / "26_hierarchical_context_backoff_audit.json"
OBSERVABLE_TREE = TEST_RESULTS / "27_observable_decision_tree_policy_audit.json"
TARGET_BOUNDARY = TEST_RESULTS / "28_target_boundary_recurrence_audit.json"
FUTURE_COPY = TEST_RESULTS / "29_future_copy_opportunity_audit.json"
SOURCE_STATE = TEST_RESULTS / "30_source_state_continuity_audit.json"
GLOBAL_SOURCE_STATE = TEST_RESULTS / "31_global_source_state_continuity_audit.json"
PHASE_GRID = TEST_RESULTS / "32_phase_grid_segmentation_audit.json"
CONTEXT_NEAREST = TEST_RESULTS / "33_context_nearest_branch_audit.json"
FINAL = REPORTS / "final_segmentation_decision_audit.md"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def assert_boundary(name: str, data: dict[str, Any]) -> None:
    if data.get("translation_delta") != "NONE":
        raise RuntimeError(f"{name} changed translation boundary")
    if data.get("case_reopened", False) is not False:
        raise RuntimeError(f"{name} reopened case")
    if data.get("plaintext_claim", False) is not False:
        raise RuntimeError(f"{name} introduced plaintext")
    decision = data.get("decision", {})
    if decision.get("row0_origin_status") not in {
        None,
        "unchanged_exogenous",
        "exogenous_under_current_evidence",
    }:
        raise RuntimeError(f"{name} changed row0 origin")
    if decision.get("translation_or_plaintext_status", "NONE") != "NONE":
        raise RuntimeError(f"{name} introduced translation/plaintext")


def main() -> None:
    trace = load_json(TRACE)
    structural = load_json(STRUCTURAL)
    dependency = load_json(DEPENDENCY) if DEPENDENCY.exists() else None
    literal_gap = load_json(LITERAL_GAP) if LITERAL_GAP.exists() else None
    online_literal = load_json(ONLINE_LITERAL) if ONLINE_LITERAL.exists() else None
    literal_exception = (
        load_json(LITERAL_EXCEPTION) if LITERAL_EXCEPTION.exists() else None
    )
    integrated_online = (
        load_json(INTEGRATED_ONLINE) if INTEGRATED_ONLINE.exists() else None
    )
    policy_drift = load_json(POLICY_DRIFT) if POLICY_DRIFT.exists() else None
    override = load_json(OVERRIDE) if OVERRIDE.exists() else None
    peak_strength = load_json(PEAK_STRENGTH) if PEAK_STRENGTH.exists() else None
    residual_context = (
        load_json(RESIDUAL_CONTEXT) if RESIDUAL_CONTEXT.exists() else None
    )
    global_objective = (
        load_json(GLOBAL_OBJECTIVE) if GLOBAL_OBJECTIVE.exists() else None
    )
    feature_weighted = (
        load_json(FEATURE_WEIGHTED) if FEATURE_WEIGHTED.exists() else None
    )
    source_boundary = load_json(SOURCE_BOUNDARY) if SOURCE_BOUNDARY.exists() else None
    drift_repair = load_json(DRIFT_REPAIR) if DRIFT_REPAIR.exists() else None
    observable_repair = (
        load_json(OBSERVABLE_REPAIR) if OBSERVABLE_REPAIR.exists() else None
    )
    conditional_repair = (
        load_json(CONDITIONAL_REPAIR) if CONDITIONAL_REPAIR.exists() else None
    )
    two_stage_repair = (
        load_json(TWO_STAGE_REPAIR) if TWO_STAGE_REPAIR.exists() else None
    )
    post_repair_oracle = (
        load_json(POST_REPAIR_ORACLE) if POST_REPAIR_ORACLE.exists() else None
    )
    residual_feature = (
        load_json(RESIDUAL_FEATURE) if RESIDUAL_FEATURE.exists() else None
    )
    branch_continuation = (
        load_json(BRANCH_CONTINUATION) if BRANCH_CONTINUATION.exists() else None
    )
    branch_ranker = load_json(BRANCH_RANKER) if BRANCH_RANKER.exists() else None
    contextual_mode = (
        load_json(CONTEXTUAL_MODE) if CONTEXTUAL_MODE.exists() else None
    )
    contextual_stability = (
        load_json(CONTEXTUAL_STABILITY) if CONTEXTUAL_STABILITY.exists() else None
    )
    hierarchical_backoff = (
        load_json(HIERARCHICAL_BACKOFF) if HIERARCHICAL_BACKOFF.exists() else None
    )
    observable_tree = load_json(OBSERVABLE_TREE) if OBSERVABLE_TREE.exists() else None
    target_boundary = load_json(TARGET_BOUNDARY) if TARGET_BOUNDARY.exists() else None
    future_copy = load_json(FUTURE_COPY) if FUTURE_COPY.exists() else None
    source_state = load_json(SOURCE_STATE) if SOURCE_STATE.exists() else None
    global_source_state = (
        load_json(GLOBAL_SOURCE_STATE) if GLOBAL_SOURCE_STATE.exists() else None
    )
    phase_grid = load_json(PHASE_GRID) if PHASE_GRID.exists() else None
    context_nearest = (
        load_json(CONTEXT_NEAREST) if CONTEXT_NEAREST.exists() else None
    )
    assert_boundary("segmentation_decision_trace", trace)
    assert_boundary("structural_segmentation_hypothesis", structural)
    if dependency is not None:
        assert_boundary("parser_dependency_reduction_ledger", dependency)
    if literal_gap is not None:
        assert_boundary("literal_gap_boundary_audit", literal_gap)
    if online_literal is not None:
        assert_boundary("online_literal_stop_rule_audit", online_literal)
    if literal_exception is not None:
        assert_boundary("literal_stop_exception_topology_audit", literal_exception)
    if integrated_online is not None:
        assert_boundary("integrated_online_literal_parser_audit", integrated_online)
    if policy_drift is not None:
        assert_boundary("integrated_parser_policy_and_drift_audit", policy_drift)
    if override is not None:
        assert_boundary("integrated_parser_override_audit", override)
    if peak_strength is not None:
        assert_boundary("integrated_parser_peak_strength_audit", peak_strength)
    if residual_context is not None:
        assert_boundary("integrated_parser_residual_context_audit", residual_context)
    if global_objective is not None:
        assert_boundary("global_objective_parser_audit", global_objective)
    if feature_weighted is not None:
        assert_boundary("feature_weighted_global_parser_audit", feature_weighted)
    if source_boundary is not None:
        assert_boundary("source_boundary_alignment_audit", source_boundary)
    if drift_repair is not None:
        assert_boundary("single_drift_repair_oracle_audit", drift_repair)
    if observable_repair is not None:
        assert_boundary("observable_repair_policy_audit", observable_repair)
    if conditional_repair is not None:
        assert_boundary("conditional_repair_classifier_audit", conditional_repair)
    if two_stage_repair is not None:
        assert_boundary("two_stage_conditional_repair_audit", two_stage_repair)
    if post_repair_oracle is not None:
        assert_boundary("post_repair_residual_oracle_audit", post_repair_oracle)
    if residual_feature is not None:
        assert_boundary("post_repair_residual_feature_audit", residual_feature)
    if branch_continuation is not None:
        assert_boundary("residual_branch_continuation_audit", branch_continuation)
    if branch_ranker is not None:
        assert_boundary("branch_ranker_prequential_audit", branch_ranker)
    if contextual_mode is not None:
        assert_boundary("contextual_mode_selector_audit", contextual_mode)
    if contextual_stability is not None:
        assert_boundary("contextual_mode_stability_audit", contextual_stability)
    if hierarchical_backoff is not None:
        assert_boundary("hierarchical_context_backoff_audit", hierarchical_backoff)
    if observable_tree is not None:
        assert_boundary("observable_decision_tree_policy_audit", observable_tree)
    if target_boundary is not None:
        assert_boundary("target_boundary_recurrence_audit", target_boundary)
    if future_copy is not None:
        assert_boundary("future_copy_opportunity_audit", future_copy)
    if source_state is not None:
        assert_boundary("source_state_continuity_audit", source_state)
    if global_source_state is not None:
        assert_boundary("global_source_state_continuity_audit", global_source_state)
    if phase_grid is not None:
        assert_boundary("phase_grid_segmentation_audit", phase_grid)
    if context_nearest is not None:
        assert_boundary("context_nearest_branch_audit", context_nearest)

    ts = trace["summary"]
    ss = structural["summary"]
    exception_rows = structural["exception_rows"]
    dep_ledger = None if dependency is None else dependency["ledger"]
    greedy = None if dependency is None else dependency["full_greedy_parser_control"]
    gap_summary = None if literal_gap is None else literal_gap["summary"]
    online_summary = None if online_literal is None else online_literal["summary"]
    exception_summary = (
        None if literal_exception is None else literal_exception["summary"]
    )
    integrated_summary = (
        None if integrated_online is None else integrated_online["summary"]
    )
    policy_drift_summary = None if policy_drift is None else policy_drift["summary"]
    override_summary = None if override is None else override["summary"]
    peak_summary = None if peak_strength is None else peak_strength["summary"]
    residual_context_summary = (
        None if residual_context is None else residual_context["summary"]
    )
    global_objective_summary = (
        None if global_objective is None else global_objective["summary"]
    )
    feature_weighted_summary = (
        None if feature_weighted is None else feature_weighted["summary"]
    )
    source_boundary_summary = (
        None if source_boundary is None else source_boundary["summary"]
    )
    drift_repair_summary = None if drift_repair is None else drift_repair["summary"]
    observable_repair_summary = (
        None if observable_repair is None else observable_repair["summary"]
    )
    conditional_repair_summary = (
        None if conditional_repair is None else conditional_repair["summary"]
    )
    two_stage_repair_summary = (
        None if two_stage_repair is None else two_stage_repair["summary"]
    )
    post_repair_oracle_summary = (
        None if post_repair_oracle is None else post_repair_oracle["summary"]
    )
    residual_feature_summary = (
        None if residual_feature is None else residual_feature["summary"]
    )
    branch_continuation_summary = (
        None if branch_continuation is None else branch_continuation["summary"]
    )
    branch_ranker_summary = (
        None if branch_ranker is None else branch_ranker["summary"]
    )
    contextual_mode_summary = (
        None if contextual_mode is None else contextual_mode["summary"]
    )
    contextual_stability_summary = (
        None if contextual_stability is None else contextual_stability["summary"]
    )
    hierarchical_backoff_summary = (
        None if hierarchical_backoff is None else hierarchical_backoff["summary"]
    )
    observable_tree_summary = (
        None if observable_tree is None else observable_tree["summary"]
    )
    target_boundary_summary = (
        None if target_boundary is None else target_boundary["summary"]
    )
    future_copy_summary = None if future_copy is None else future_copy["summary"]
    source_state_summary = None if source_state is None else source_state["summary"]
    global_source_state_summary = (
        None if global_source_state is None else global_source_state["summary"]
    )
    phase_grid_summary = None if phase_grid is None else phase_grid["summary"]
    context_nearest_summary = (
        None if context_nearest is None else context_nearest["summary"]
    )

    lines = [
        "# Final Segmentation Decision Audit",
        "",
        "Status: `analysis_only`",
        "Classification: `PROMOTED_MECHANICAL_SEGMENTATION_CLUE` for parser segmentation; `AUDIT_ONLY` for source-free generation.",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Row0 origin: `unchanged_exogenous`",
        "Compression bound: `unchanged_8154_676268`",
        "",
        "## Question",
        "",
        "Can the retained `(source,length)` decisions be explained as a",
        "mechanical segmentation/parser rule rather than another local bit",
        "sweep?",
        "",
        "## Main Result",
        "",
        "On the stable copy projection used by the recent length gates, the rule",
        "`choose the longest previous target match; break source ties by earliest source`",
        f"recovers `{ss['target_text_global_longest_pair_hits']}/{ss['target_text_global_longest_pair_total']}`",
        "copy pairs.",
        "",
        "This is a real mechanical parser clue: it sharply reduces the declared",
        "`(source,length)` dependency for copy segmentation when the target book",
        "text is being parsed. It is not a source-free generator for the 70 books,",
        "because it still requires the target suffix as input and has one",
        "exception.",
        "",
        "## Trace Coverage",
        "",
        f"- Reference skeleton operations: `{ts['reference_skeleton_operation_count']}`.",
        f"- Stable-projection operations traced: `{ts['stable_projection_operation_count']}`.",
        f"- Copy decisions traced: `{ts['copy_count']}`.",
        f"- Candidate pair median: `{ts['candidate_pair_count_summary']['median']:.3f}`.",
        f"- Candidate pair max: `{ts['candidate_pair_count_summary']['max']}`.",
        f"- Declared copy equals source-local target max: `{ts['declared_is_max_count']}/{ts['copy_count']}`.",
        f"- Stable-projection literal gaps: `{ts['stable_projection_literal_gap_count']}` "
        f"with `{ts['stable_projection_literal_digit_count']}` literal digits.",
        "",
        "The stable projection has one more literal gap than the reference",
        "skeleton ledger (`54` vs `53`) and one fewer literal digit (`265` vs",
        "`266`). This report therefore treats the finding as a copy-segmentation",
        "parser clue, not a replacement for the full skeleton ledger.",
        "",
        "## Structural Hypotheses",
        "",
        "| Hypothesis | Result | Boundary |",
        "|---|---:|---|",
        f"| Longest previous target match + earliest source | `{ss['best_source_tie_policy_hits']}/{ss['copy_count']}` | parser clue, target-text-aware |",
        f"| Random source among global-max matches | expected `{ss['random_global_max_source_expected_hits']:.3f}/{ss['copy_count']}` | negative control |",
        f"| Unique global-max source forcing | `{ss['unique_global_max_source_rows']}/{ss['copy_count']}` rows | partial only |",
        f"| Recurrent next boundary preserved | `{ss['recurrent_boundary_hits']}/{ss['copy_count']}` | weak clue, not sufficient |",
        f"| Stop before max protects literal payload | `{ss['literal_payload_protection_hits']}/{ss['copy_count']}` | rejected |",
        "",
        "## Exception",
        "",
        "| Book | Op | Projection copy | Declared length | Max length | Candidate pairs | Declared boundary pairs | Max boundary pairs |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in exception_rows:
        lines.append(
            f"| `{row['book']}` | `{row['op_index']}` | `{row['projection_copy_index']}` | "
            f"`{row['declared_length']}` | `{row['all_source_max_length']}` | "
            f"`{row['candidate_pair_count']}` | "
            f"`{row['declared_boundary_candidate_pair_count']}` | "
            f"`{row['max_boundary_candidate_pair_count']}` |"
        )

    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- Found a strong target-text-aware parser rule for copy segmentation.",
            "- Did not find a source-free generation rule for the book digits.",
            "- Reduced the practical copy `(source,length)` blocker to: target text must be available, stable projection must be accepted, and one exception remains.",
            "- Rejected the literal-payload-protection shortcut and weakened recurrent-boundary explanations.",
            "- Compression bound is unchanged.",
            "- Row0 remains exogenous and unchanged.",
            "- No plaintext, translation, fan gloss, semantic reading, or case reopening is introduced.",
            "",
        ]
    )
    if dep_ledger is not None and greedy is not None:
        base = dep_ledger["baseline_exact_skeleton"]
        parser = dep_ledger["target_text_parser_projection"]
        delta = dep_ledger["delta_vs_exact_skeleton"]
        lines.extend(
            [
                "## Dependency Reduction Ledger",
                "",
                "| Representation | Operation/skeleton records | Literal chunks | Copy/source exception records | Parser rule records | Total materialized records |",
                "|---|---:|---:|---:|---:|---:|",
                f"| Exact skeleton ledger | `{base['skeleton_atlas_records']}` | `{base['literal_payload_chunks']}` | `{base['copy_source_fields']}` | `0` | `{base['total_materialized_records']}` |",
                f"| Target-text parser projection | `{parser['stable_projection_operation_records']}` | `{parser['literal_payload_chunks']}` | `{parser['copy_exception_records']}` | `{parser['parser_rule_records']}` | `{parser['total_materialized_records']}` |",
                "",
                f"- Materialized record delta: `{delta['materialized_record_delta']}`.",
                f"- Conditional copy `(source,length)` fields removed: `{delta['copy_pair_fields_removed_conditionally']}`.",
                f"- Full greedy source-free parser exact books: `{greedy['exact_book_count']}/{greedy['tested_books']}`.",
                f"- Full greedy mismatch books: `{greedy['mismatch_books']}`.",
                "",
                "The dependency reduction is therefore real but conditional. It needs",
                "target text and the stable projection's copy starts; it does not derive",
                "the full operation sequence source-free.",
                "",
            ]
        )
    if gap_summary is not None:
        lines.extend(
            [
                "## Literal Gap Boundary",
                "",
                "| Hypothesis | Result | Boundary |",
                "|---|---:|---|",
                f"| Stop at first available match | `{gap_summary['stable_stop_is_first_match_count']}/{gap_summary['literal_gap_count']}` | rejected |",
                f"| Stop at local-window best literal+copy advance | `{gap_summary['stable_stop_local_best_total_advance_count']}/{gap_summary['literal_gap_count']}` | declared-window clue |",
                f"| Stop at full-suffix best literal+copy advance | `{gap_summary['stable_stop_full_suffix_best_total_advance_count']}/{gap_summary['literal_gaps_followed_by_copy']}` | source-free rule rejected |",
                "",
                f"- Copy was already available at literal start in `{gap_summary['copy_available_at_literal_start']}` gaps.",
                f"- Future stable copy improves immediate copy in `{gap_summary['future_copy_improves_immediate_count']}` followed-by-copy gaps.",
                "",
                "This explains why first-match greedy parsing fails: stable literal gaps",
                "often wait for a better next copy. But the explanation is still",
                "conditioned on the declared literal window; it does not derive that",
                "window source-free.",
                "",
            ]
        )
    if online_summary is not None:
        best = online_summary["best_policy"]
        lines.extend(
            [
                "## Online Literal Stop Rule",
                "",
                "| Rule | Result | Boundary |",
                "|---|---:|---|",
                f"| First confirmed max-copy local peak, window `{best['confirm_window']}` | `{best['followed_by_copy_hits']}/{best['followed_by_copy_total']}` followed-by-copy gaps | partial online clue |",
                f"| Same rule plus book-end default | `{best['all_literal_gap_hits_with_book_end_default']}/{best['all_literal_gap_total']}` literal gaps | partial parser rule |",
                "",
                f"- Prequential cells: `{online_summary['prequential_cells']}`.",
                f"- Selected policy matches suffix oracle in `{online_summary['prequential_selected_matches_oracle_cells']}/{online_summary['prequential_cells']}` cells.",
                f"- Promotes source-free literal stop rule: `{online_summary['promotes_source_free_literal_stop_rule']}`.",
                "",
                "This reduces the literal-window blocker further: most starts are now",
                "explained by an online local-peak rule, but four followed-by-copy gaps",
                "remain exceptions.",
                "",
            ]
        )
    if exception_summary is not None:
        best_flag = exception_summary["best_source_free_exception_flag"]
        lines.extend(
            [
                "## Literal Stop Exception Topology",
                "",
                f"- Exception count: `{exception_summary['exception_count']}`.",
                f"- Exception classes: `{exception_summary['exception_classes']}`.",
                f"- Best source-free exception flag: `{best_flag['predicate']}` "
                f"with recall `{best_flag['recall']:.3f}` and "
                f"`{best_flag['false_positive_ok_rows']}` false positives.",
                f"- Promotes exception rule: `{exception_summary['promotes_exception_rule']}`.",
                "",
                "The residual exceptions are heterogeneous; no source-free exception",
                "flag isolates all four without false positives.",
                "",
            ]
        )
    if integrated_summary is not None:
        lines.extend(
            [
                "## Integrated Online Parser",
                "",
                "The online stop rule was then frozen and run as an end-to-end",
                "target-text-aware parser, without granting declared literal windows",
                "or copy starts.",
                "",
                "| Parser | Exact books | Operations | Literal digits | Boundary |",
                "|---|---:|---:|---:|---|",
                f"| Full greedy control | `{integrated_summary['full_greedy_exact_books']}/{integrated_summary['tested_books']}` | n/a | n/a | earlier control |",
                f"| Integrated online stop + longest copy | `{integrated_summary['exact_book_count']}/{integrated_summary['tested_books']}` | `{integrated_summary['predicted_operation_count']}` vs stable `{integrated_summary['stable_projection_operation_count']}` | `{integrated_summary['predicted_literal_digit_count']}` vs stable `{integrated_summary['stable_literal_digit_count']}` | partial parser, not promoted |",
                "",
                f"- Exact-book delta vs full greedy: `{integrated_summary['exact_books_delta_vs_full_greedy']}`.",
                f"- Mismatch books: `{integrated_summary['mismatch_books']}`.",
                "",
                "This is a real parser improvement over first-match greedy, but it",
                "still drifts in `14/60` books and over-literalizes the stable",
                "projection. The integrated parser therefore reduces the segmentation",
                "blocker but does not replace the retained operation-start ledger or",
                "emit a source-free generator.",
                "",
            ]
        )
    if policy_drift_summary is not None:
        lines.extend(
            [
                "## Integrated Parser Policy Frontier",
                "",
                "A follow-up gate retuned the same local-peak stop family as an",
                "integrated parser, rather than scoring stops inside known literal",
                "windows.",
                "",
                "| Policy | Exact books | Drift books | Boundary |",
                "|---|---:|---:|---|",
                f"| First-match greedy | `{policy_drift_summary['first_match_exact_books']}/60` | `21` | rejected baseline |",
                f"| Gate-08 active `{policy_drift_summary['active_policy']}` | `{policy_drift_summary['active_exact_books']}/60` | `{60 - policy_drift_summary['active_exact_books']}` | partial parser |",
                f"| Best prefix-stable `{policy_drift_summary['best_policy']}` | `{policy_drift_summary['best_exact_books']}/60` | `{60 - policy_drift_summary['best_exact_books']}` | partial, not promoted |",
                "",
                f"- Prequential selected policy matches suffix oracle in `{policy_drift_summary['prequential_selected_matches_oracle_cells']}/{policy_drift_summary['prequential_cells']}` cells.",
                f"- Best-policy drift classes: `{policy_drift_summary['best_drift_class_counts']}`.",
                "",
                "The window-5 policy is a real integrated-parser improvement and is",
                "stable under prefix policy selection, but it still leaves `12/60`",
                "books mismatched. The remaining topology mixes missed book-start",
                "copies, missed internal copies, literal understops, and one copy",
                "length drift, so the local-peak family is not a complete",
                "segmentation mechanism.",
                "",
            ]
        )
    if override_summary is not None:
        lines.extend(
            [
                "## Immediate-Copy Override Control",
                "",
                "The next obvious structural rescue is to override the local-peak",
                "wait rule when a strong copy is already available. Gate 10 tests",
                "book-start, internal, and any-position immediate-copy overrides",
                "across thresholds `5..20`.",
                "",
                "| Family | Best exact books | Selected by prefix? | Boundary |",
                "|---|---:|---|---|",
                f"| No override baseline | `{override_summary['baseline_exact_books']}/60` | yes | retained |",
                f"| Immediate-copy overrides | `{override_summary['best_exact_books']}/60` | `{override_summary['prequential_selected_matches_oracle_cells']}/{override_summary['prequential_cells']}` oracle cells | rejected |",
                "",
                f"- Best policy: `{override_summary['best_policy']}`.",
                f"- Exact-book improvement vs baseline: `{override_summary['exact_improvement_vs_baseline']}`.",
                "",
                "The override family does not improve the parser. In the problematic",
                "middle prefix cells it overfits train books and loses held-out",
                "suffix books, especially through false book-start copies. The",
                "remaining segmentation blocker is therefore not a simple",
                "immediate-copy/missed-copy threshold.",
                "",
            ]
        )
    if peak_summary is not None:
        lines.extend(
            [
                "## Peak-Strength Control",
                "",
                "The opposite rescue is to wait for a stronger local peak before",
                "ending a literal run, aiming to fix literal-understop drifts.",
                "",
                "| Family | Best exact books | Boundary |",
                "|---|---:|---|",
                f"| Window-5 baseline | `{peak_summary['baseline_exact_books']}/60` | retained |",
                f"| Minimum peak strength | `{peak_summary['best_exact_books']}/60` | rejected |",
                "",
                f"- Best policy: `{peak_summary['best_policy']}`.",
                f"- Exact-book improvement vs baseline: `{peak_summary['exact_improvement_vs_baseline']}`.",
                f"- Prequential selected policy matches suffix oracle in `{peak_summary['prequential_selected_matches_oracle_cells']}/{peak_summary['prequential_cells']}` cells.",
                "",
                "Raising the minimum accepted peak does not improve exact coverage.",
                "The first alternate threshold, `min_peak_len6`, ties `48/60` but",
                "increases literal digits and turns some understops into missed-copy",
                "and overstop failures; larger thresholds degrade sharply. The",
                "remaining literal-understop cases are therefore not solved by a",
                "simple weak-peak filter.",
                "",
            ]
        )
    if residual_context_summary is not None:
        best = residual_context_summary["best_predicate"]
        lines.extend(
            [
                "## Residual Context Predicate Control",
                "",
                "After local-threshold rescues failed, gate 12 asks whether simple",
                "observable parser-state predicates can identify the remaining",
                "first-drift decisions well enough to become correction rules.",
                "",
                "| Predicate family | Best result | Boundary |",
                "|---|---|---|",
                f"| `{best['predicate']}` | TP/FP/FN `{best['tp']}/{best['fp']}/{best['fn']}`, precision `{best['precision']:.3f}`, recall `{best['recall']:.3f}` | rejected |",
                "",
                f"- Decision rows: `{residual_context_summary['decision_rows']}`.",
                f"- Error rows: `{residual_context_summary['error_rows']}`.",
                f"- Predicate count: `{residual_context_summary['predicate_count']}`.",
                f"- Prequential selected predicate matches suffix oracle in `{residual_context_summary['prequential_selected_matches_oracle_cells']}/{residual_context_summary['prequential_cells']}` cells.",
                "",
                "The best simple flag, `peak_len_le5`, catches only `4/12` residual",
                "errors and also flags clean decisions. Broader predicates catch more",
                "errors only by creating many false positives. The remaining drift",
                "therefore looks like a mixed path/state problem rather than a",
                "single observable local context rule.",
                "",
            ]
        )
    if global_objective_summary is not None:
        lines.extend(
            [
                "## Global Objective Parser Control",
                "",
                "Gate 13 tests a broader path-state hypothesis: dynamic programming",
                "per book under simple global objectives over operations, literal",
                "mass, and copy mass, without declared operation starts.",
                "",
                "| Parser family | Best exact books | Boundary |",
                "|---|---:|---|",
                f"| Window-5 local parser | `{global_objective_summary['baseline_window5_exact_books']}/60` | retained baseline |",
                f"| Simple global objectives | `{global_objective_summary['best_exact_books']}/60` | rejected |",
                "",
                f"- Best objective: `{global_objective_summary['best_objective']}`.",
                f"- Exact-book delta vs window5: `{global_objective_summary['exact_improvement_vs_window5']}`.",
                f"- Prequential selected objective matches suffix oracle in `{global_objective_summary['prequential_selected_matches_oracle_cells']}/{global_objective_summary['prequential_cells']}` cells.",
                "",
                "The global DP objectives are stable but wrong: the best reaches only",
                "`23/60`, far below the `48/60` local-parser baseline. Simple",
                "global minimization of ops, literals, copies, or copy mass therefore",
                "does not explain the retained stable segmentation. Any next path-state",
                "model needs a richer learned or structural cost, not a crude global",
                "objective.",
                "",
            ]
        )
    if feature_weighted_summary is not None:
        lines.extend(
            [
                "## Feature-Weighted Global Parser Control",
                "",
                "Gate 14 tests whether a small structural cost can rescue the global",
                "DP approach: literal mass, copy base cost, copy-length reward,",
                "short-copy penalty, and book-start-copy penalty.",
                "",
                "| Parser family | Best exact books | Boundary |",
                "|---|---:|---|",
                f"| Window-5 local parser | `{feature_weighted_summary['baseline_window5_exact_books']}/60` | retained baseline |",
                f"| Feature-weighted DP profiles | `{feature_weighted_summary['best_exact_books']}/60` | rejected |",
                "",
                f"- Best profile: `{feature_weighted_summary['best_profile']}`.",
                f"- Exact-book delta vs window5: `{feature_weighted_summary['exact_improvement_vs_window5']}`.",
                f"- Prequential selected profile matches suffix oracle in `{feature_weighted_summary['prequential_selected_matches_oracle_cells']}/{feature_weighted_summary['prequential_cells']}` cells.",
                "",
                "The richer cost family improves over crude objectives only slightly",
                "(`26/60` vs `23/60`) and remains far below the local `window5`",
                "parser. A small linear feature cost over obvious copy/literal",
                "features is therefore not the missing segmentation mechanism.",
                "",
            ]
        )
    if source_boundary_summary is not None:
        lines.extend(
            [
                "## Source Boundary Alignment Control",
                "",
                "Gate 15 tests the structural block/chunk hypothesis that copies",
                "reuse already segmented source-side operation chunks.",
                "",
                "| Boundary measure | Hits |",
                "|---|---:|",
                f"| Source starts on prior operation boundary | `{source_boundary_summary['source_start_on_operation_boundary']}/{source_boundary_summary['copy_count']}` |",
                f"| Source ends on prior operation boundary | `{source_boundary_summary['source_end_on_operation_boundary']}/{source_boundary_summary['copy_count']}` |",
                f"| Source interval equals one prior chunk | `{source_boundary_summary['source_interval_equals_single_prior_chunk']}/{source_boundary_summary['copy_count']}` |",
                "",
                f"- Best boundary-aware source tie policy: `{source_boundary_summary['best_boundary_policy']}` with `{source_boundary_summary['best_boundary_policy_hits']}/{source_boundary_summary['copy_count']}` hits.",
                f"- Lift vs existing earliest-source rule: `{source_boundary_summary['boundary_policy_lift_vs_earliest']}`.",
                "",
                "Source-side chunk boundaries do not explain the retained",
                "segmentation. Boundary-aware tie-breakers are worse than the",
                "existing earliest-source global-max rule, so the block-copy",
                "hypothesis is rejected as a generation mechanism.",
                "",
            ]
        )
    if drift_repair_summary is not None:
        lines.extend(
            [
                "## Single-Drift Repair Oracle",
                "",
                "Gate 16 asks whether the `12/60` integrated-parser drift",
                "books are first-decision failures or deeper path failures.",
                "It grants a stable-projection oracle only as a diagnostic",
                "repair, then resumes the same `window5` parser.",
                "",
                "| Oracle correction budget | Exact books | Residual repairs |",
                "|---:|---:|---:|",
            ]
        )
        for row in drift_repair["budget_scoreboard"]:
            lines.append(
                f"| `{row['correction_budget']}` | `{row['exact_books']}/60` | "
                f"`{row['residual_repairs_vs_baseline']}` |"
            )
        lines.extend(
            [
                "",
                f"- One oracle correction repairs `{drift_repair_summary['one_correction_repair_count']}/12` residual books.",
                f"- Two oracle corrections repair all `12/12` residual books.",
                f"- Full-oracle correction histogram: `{drift_repair_summary['full_oracle_correction_count_histogram']}`.",
                "",
                "This is an important blocker localization: most remaining",
                "parser failures are isolated first-drift decisions, not",
                "long unstable paths. It is still not a promoted rule because",
                "the correction itself is chosen from the stable projection.",
                "",
            ]
        )
    if observable_repair_summary is not None:
        lines.extend(
            [
                "## Observable Repair Policy Control",
                "",
                "Gate 17 tests whether the gate-16 oracle repairs can be",
                "replaced by small observable parser actions: immediate-copy",
                "forcing, book-start/internal copy forcing, next-peak literal",
                "delay, short-copy literal substitution, copy shortening by one,",
                "and one combined policy.",
                "",
                "| Policy family | Exact books | Boundary |",
                "|---|---:|---|",
                f"| Baseline `window5` | `{observable_repair_summary['baseline_exact_books']}/60` | retained |",
                f"| Best observable repair policy `{observable_repair_summary['best_policy']}` | `{observable_repair_summary['best_exact_books']}/60` | rejected |",
                "",
                f"- Exact delta vs baseline: `{observable_repair_summary['exact_delta_vs_baseline']}`.",
                f"- Prequential selected matches oracle cells: `{observable_repair_summary['prequential_selected_matches_oracle_cells']}/{observable_repair_summary['prequential_cells']}`.",
                "",
                "The first-drift oracle map does not yet convert into a small",
                "observable repair rule. The baseline remains the best policy,",
                "and train-selected repair actions overfit in the middle prefix",
                "splits.",
                "",
            ]
        )
    if conditional_repair_summary is not None:
        lines.extend(
            [
                "## Conditional Repair Classifier",
                "",
                "Gate 18 tests a restricted classifier family: one observable",
                "predicate plus one observable repair action, applied end-to-end",
                "and selected under prefix/holdout.",
                "",
                "| Parser | Exact books | Boundary |",
                "|---|---:|---|",
                f"| Baseline `window5` | `{conditional_repair_summary['baseline_exact_books']}/60` | retained baseline |",
                f"| Best conditional classifier `{conditional_repair_summary['best_classifier']}` | `{conditional_repair_summary['best_exact_books']}/60` | partial, not promoted |",
                "",
                f"- Exact delta vs baseline: `{conditional_repair_summary['exact_delta_vs_baseline']}`.",
                f"- Repairs applied by best classifier: `{conditional_repair_summary['best_total_repairs_applied']}`.",
                f"- Prequential selected matches oracle cells: `{conditional_repair_summary['prequential_selected_matches_oracle_cells']}/{conditional_repair_summary['prequential_cells']}`.",
                f"- Remaining mismatch books: `{conditional_repair_summary['best_mismatch_books']}`.",
                "",
                "This is the first non-oracle repair classifier in this front",
                "to improve the integrated parser under prefix-stable selection.",
                "It narrows the residual literal-understop class, but it still",
                "leaves ten mixed drift books and therefore does not promote a",
                "complete segmentation mechanism.",
                "",
            ]
        )
    if two_stage_repair_summary is not None:
        lines.extend(
            [
                "## Two-Stage Conditional Repair Control",
                "",
                "Gate 19 keeps the gate-18 classifier as first stage and tests",
                "whether one additional observable predicate-action rule can",
                "close more of the remaining drift.",
                "",
                "| Pipeline | Exact books | Boundary |",
                "|---|---:|---|",
                f"| Active first stage `{two_stage_repair_summary['active_first_stage']}` | `{two_stage_repair_summary['active_exact_books']}/60` | retained |",
                f"| Best two-stage pipeline `{two_stage_repair_summary['best_pipeline']}` | `{two_stage_repair_summary['best_exact_books']}/60` | rejected as second-stage gain |",
                "",
                f"- Exact delta vs active first stage: `{two_stage_repair_summary['exact_delta_vs_active']}`.",
                f"- Prequential selected matches oracle cells: `{two_stage_repair_summary['prequential_selected_matches_oracle_cells']}/{two_stage_repair_summary['prequential_cells']}`.",
                "",
                "A second simple observable rule does not improve the parser.",
                "The best pipeline is still the single gate-18 classifier, and",
                "train-selected second-stage repairs overfit in the middle",
                "prefix splits.",
                "",
            ]
        )
    if post_repair_oracle_summary is not None:
        lines.extend(
            [
                "## Post-Repair Residual Oracle",
                "",
                "Gate 20 keeps the gate-18 non-oracle classifier active,",
                "then grants stable-projection repairs only as a diagnostic",
                "upper bound for the remaining drift books.",
                "",
                "| Oracle correction budget | Exact books | Residual repairs |",
                "|---:|---:|---:|",
            ]
        )
        for row in post_repair_oracle["budget_scoreboard"]:
            lines.append(
                f"| `{row['correction_budget']}` | `{row['exact_books']}/60` | "
                f"`{row['residual_repairs_vs_active']}` |"
            )
        lines.extend(
            [
                "",
                f"- One oracle correction repairs `{post_repair_oracle_summary['one_correction_repair_count']}/{post_repair_oracle_summary['residual_book_count']}` residual books.",
                f"- Two oracle corrections repair all `{post_repair_oracle_summary['residual_book_count']}/{post_repair_oracle_summary['residual_book_count']}` residual books.",
                f"- Full-oracle correction histogram: `{post_repair_oracle_summary['full_oracle_correction_count_histogram']}`.",
                f"- First-oracle correction classes: `{post_repair_oracle_summary['first_oracle_correction_drift_classes']}`.",
                "",
                "The remaining drift is still mostly first-decision local",
                "under an oracle view: only book `20` needs two corrections.",
                "This narrows the next classifier target, but does not promote",
                "a parser because the repair choices come from the stable",
                "projection.",
                "",
            ]
        )
    if residual_feature_summary is not None:
        lines.extend(
            [
                "## Post-Repair Residual Feature Screen",
                "",
                "Gate 21 asks whether the gate-20 residual oracle map has a",
                "non-oracle observable feature signature. The ten first residual",
                "drifts are scored as positives against active-parser aligned",
                "decisions before any drift as negative controls.",
                "",
                "| Screen | Result | Boundary |",
                "|---|---:|---|",
                f"| Best overall predicate `{residual_feature_summary['best_overall_predicate']}` | TP/FP/FN `{residual_feature_summary['best_overall_tp_fp_fn']['tp']}/{residual_feature_summary['best_overall_tp_fp_fn']['fp']}/{residual_feature_summary['best_overall_tp_fp_fn']['fn']}` | rejected |",
                f"| Best zero-FP predicate `{residual_feature_summary['best_zero_fp_predicate']}` | `{residual_feature_summary['best_zero_fp_tp']}/{residual_feature_summary['residual_book_count']}` residuals | too narrow |",
                f"| Full zero-FP detector | `{residual_feature_summary['full_zero_fp_detector']}` | absent |",
                "",
                f"- Clean decision controls: `{residual_feature_summary['clean_decision_control_count']}`.",
                f"- Predicates tested: `{residual_feature_summary['predicate_count']}`.",
                f"- Prequential zero-test-FP cells: `{residual_feature_summary['prequential_zero_test_fp_cells']}/{residual_feature_summary['prequential_cells']}`.",
                f"- Prequential cover-all-test-residual cells: `{residual_feature_summary['prequential_cover_all_test_residual_cells']}/{residual_feature_summary['prequential_cells']}`.",
                "",
                "The residual errors are not separated by a simple feature flag.",
                "The missed-copy subset is visible as an opportunity class, but",
                "the same signature fires on already-correct parser decisions.",
                "The remaining blocker therefore remains a richer path/state",
                "segmentation rule rather than a single residual predicate.",
                "",
            ]
        )
    if branch_continuation_summary is not None:
        lines.extend(
            [
                "## Residual Branch Continuation Control",
                "",
                "Gate 22 tests the next path-state hypothesis: maybe the",
                "stable residual operation is selected by how the active",
                "parser continues after a forced first branch. Non-oracle",
                "objectives may select only observable local branches; the",
                "stable projection is used only as the evaluation label.",
                "",
                "| Objective | Residual hits | Clean false changes | Boundary |",
                "|---|---:|---:|---|",
                f"| Oracle stable-prefix diagnostic | `{branch_continuation_summary['oracle_residual_hits']}/{branch_continuation_summary['residual_decision_count']}` | `{branch_continuation_summary['oracle_clean_false_changes']}` | label-only upper bound |",
                f"| Best non-oracle `{branch_continuation_summary['best_non_oracle_objective']}` | `{branch_continuation_summary['best_non_oracle_residual_hits']}/{branch_continuation_summary['residual_decision_count']}` | `{branch_continuation_summary['best_non_oracle_clean_false_changes']}` | rejected |",
                "",
                f"- Residual stable operations available as observable candidates: `{branch_continuation_summary['residual_stable_observable_candidates']}/{branch_continuation_summary['residual_decision_count']}`.",
                f"- Clean controls: `{branch_continuation_summary['clean_control_count']}`.",
                f"- Prequential zero-clean-false-change cells: `{branch_continuation_summary['prequential_zero_clean_false_change_cells']}/{branch_continuation_summary['prequential_cells']}`.",
                f"- Prequential cover-all-test-residual cells: `{branch_continuation_summary['prequential_cover_all_test_residual_cells']}/{branch_continuation_summary['prequential_cells']}`.",
                "",
                "The branch grammar is broad enough to include every stable",
                "residual operation, but simple continuation objectives still",
                "fail: the best non-oracle objective repairs only part of the",
                "residual set and changes already-correct controls. The missing",
                "mechanism is therefore not just a first-branch objective over",
                "operation count, literal mass, or copied mass.",
                "",
            ]
        )
    if branch_ranker_summary is not None:
        lines.extend(
            [
                "## Branch Ranker Prequential Control",
                "",
                "Gate 23 tests whether a small pairwise branch ranker can learn",
                "the missing path/state preference from prefix books. The ranker",
                "uses observable branch and continuation features; stable",
                "projection is used only as the train/evaluation label.",
                "",
                "| Model | Total hits | Residual hits | Clean false changes | Boundary |",
                "|---|---:|---:|---:|---|",
                f"| Active branch baseline | `{branch_ranker_summary['baseline_active_total_hits']}/{branch_ranker_summary['decision_count']}` | `{branch_ranker_summary['baseline_active_residual_hits']}/{branch_ranker_summary['residual_decision_count']}` | `{branch_ranker_summary['baseline_active_clean_false_changes']}` | retained control |",
                f"| Best full-fit ranker `{branch_ranker_summary['best_full_fit_mode']}` | `{branch_ranker_summary['full_fit_total_hits']}/{branch_ranker_summary['decision_count']}` | `{branch_ranker_summary['full_fit_residual_hits']}/{branch_ranker_summary['residual_decision_count']}` | `{branch_ranker_summary['full_fit_clean_false_changes']}` | rejected |",
                "",
                f"- Training modes: `{branch_ranker_summary['training_modes']}`.",
                f"- Prequential zero-clean-false-change cells: `{branch_ranker_summary['prequential_zero_clean_false_change_cells']}/{branch_ranker_summary['prequential_cells']}`.",
                f"- Prequential cover-all-test-residual cells: `{branch_ranker_summary['prequential_cover_all_test_residual_cells']}/{branch_ranker_summary['prequential_cells']}`.",
                "",
                "The learned ranker does not improve the retained active parser.",
                "Modes that preserve clean controls still miss all residuals,",
                "while residual-only weighting can hit some residual branches",
                "only by destroying the clean-control path. This rejects a",
                "small learned branch ranker as the missing generative parser.",
                "",
            ]
        )
    if contextual_mode_summary is not None:
        lines.extend(
            [
                "## Contextual Mode Selector Control",
                "",
                "Gate 24 tests a finite observable state table: each context",
                "family learns which non-oracle branch objective to use from",
                "stable labels, then is evaluated under prefix/holdout.",
                "",
                "| Selector | Total hits | Residual hits | Clean false changes | Boundary |",
                "|---|---:|---:|---:|---|",
                f"| Active branch baseline | `{contextual_mode_summary['active_baseline_total_hits']}/{contextual_mode_summary['decision_count']}` | `{contextual_mode_summary['active_baseline_residual_hits']}/{contextual_mode_summary['residual_decision_count']}` | `{contextual_mode_summary['active_baseline_clean_false_changes']}` | retained control |",
                f"| Best full-fit context `{contextual_mode_summary['best_context_family']}` | `{contextual_mode_summary['best_full_fit_total_hits']}/{contextual_mode_summary['decision_count']}` | `{contextual_mode_summary['best_full_fit_residual_hits']}/{contextual_mode_summary['residual_decision_count']}` | `{contextual_mode_summary['best_full_fit_clean_false_changes']}` | weak full-fit clue only |",
                "",
                f"- Context families tested: `{contextual_mode_summary['context_family_count']}`.",
                f"- Prequential zero-clean-false-change cells: `{contextual_mode_summary['prequential_zero_clean_false_change_cells']}/{contextual_mode_summary['prequential_cells']}`.",
                f"- Prequential cover-all-test-residual cells: `{contextual_mode_summary['prequential_cover_all_test_residual_cells']}/{contextual_mode_summary['prequential_cells']}`.",
                f"- Prequential selected matches oracle cells: `{contextual_mode_summary['prequential_selected_matches_oracle_cells']}/{contextual_mode_summary['prequential_cells']}`.",
                "",
                "A finite context table shows a real full-corpus signal:",
                "the best observable context resolves half of the residuals",
                "without false clean-control changes. It is still not promoted",
                "because the same selector is not prefix/holdout stable and",
                "does not cover future residuals reliably.",
                "",
            ]
        )
    if contextual_stability_summary is not None:
        lines.extend(
            [
                "## Contextual Mode Stability Control",
                "",
                "Gate 25 stress-tests the gate-24 `context_combo` full-fit",
                "signal with support pruning, leave-one-book retraining, and",
                "leave-context-out retraining.",
                "",
                "| Test | Residual hits | Clean false changes | Boundary |",
                "|---|---:|---:|---|",
                f"| Full-fit `context_combo` | `{contextual_stability_summary['full_fit_residual_hits']}/{contextual_stability_summary['residual_decision_count']}` | `{contextual_stability_summary['full_fit_clean_false_changes']}` | weak clue |",
                f"| Leave-one-book | `{contextual_stability_summary['leave_one_book_residual_hits']}/{contextual_stability_summary['residual_decision_count']}` | n/a | rejected |",
                f"| Leave-context-out | `{contextual_stability_summary['leave_context_out_residual_hits']}/{contextual_stability_summary['residual_decision_count']}` | n/a | rejected |",
                "",
                f"- Best supported threshold: `{contextual_stability_summary['best_supported_threshold']}`.",
                f"- Support thresholds tested: `{contextual_stability_summary['support_threshold_count']}`.",
                "",
                "The apparent context signal is not stable: most of the full-fit",
                "residual repairs disappear when the held-out book is removed",
                "from training or when low-support buckets are pruned. This",
                "reclassifies the context table as a weak post-hoc clue, not",
                "a generative parser rule.",
                "",
            ]
        )
    if hierarchical_backoff_summary is not None:
        lines.extend(
            [
                "## Hierarchical Context Backoff Control",
                "",
                "Gate 26 tests whether the gate-25 failure was only context",
                "sparsity. It trains observable context hierarchies and backs",
                "off to coarser modes when support is low.",
                "",
                "| Selector | Total hits | Residual hits | Clean false changes | Boundary |",
                "|---|---:|---:|---:|---|",
                f"| Best full-fit backoff `{hierarchical_backoff_summary['best_family']}` support `{hierarchical_backoff_summary['best_min_support']}` | `{hierarchical_backoff_summary['best_full_fit_total_hits']}/{hierarchical_backoff_summary['decision_count']}` | `{hierarchical_backoff_summary['best_full_fit_residual_hits']}/{hierarchical_backoff_summary['residual_decision_count']}` | `{hierarchical_backoff_summary['best_full_fit_clean_false_changes']}` | weak full-fit clue only |",
                "",
                f"- Families tested: `{hierarchical_backoff_summary['family_count']}`.",
                f"- Support thresholds tested: `{hierarchical_backoff_summary['support_threshold_count']}`.",
                f"- Prequential zero-clean-false-change cells: `{hierarchical_backoff_summary['prequential_zero_clean_false_change_cells']}/{hierarchical_backoff_summary['prequential_cells']}`.",
                f"- Prequential cover-all-test-residual cells: `{hierarchical_backoff_summary['prequential_cover_all_test_residual_cells']}/{hierarchical_backoff_summary['prequential_cells']}`.",
                f"- Prequential selected matches oracle cells: `{hierarchical_backoff_summary['prequential_selected_matches_oracle_cells']}/{hierarchical_backoff_summary['prequential_cells']}`.",
                "",
                "Backoff does not rescue the contextual mode family. It keeps",
                "the same full-fit ceiling but its held-out residual gains come",
                "with false clean-control changes, so it is not a generative",
                "parser rule.",
                "",
            ]
        )
    if observable_tree_summary is not None:
        lines.extend(
            [
                "## Observable Decision Tree Policy Control",
                "",
                "Gate 27 tests whether the same residual branch choices need a",
                "flat context table, or whether a small observable decision tree",
                "over branch/position predicates can select a non-oracle continuation",
                "objective.",
                "",
                "| Parser | Total hits | Residual hits | Clean false changes | Boundary |",
                "|---|---:|---:|---:|---|",
                f"| Active branch baseline | `{observable_tree_summary['active_baseline_total_hits']}/{observable_tree_summary['decision_count']}` | `{observable_tree_summary['active_baseline_residual_hits']}/{observable_tree_summary['residual_decision_count']}` | `{observable_tree_summary['active_baseline_clean_false_changes']}` | retained control |",
                f"| Best observable tree | `{observable_tree_summary['best_total_hits']}/{observable_tree_summary['decision_count']}` | `{observable_tree_summary['best_residual_hits']}/{observable_tree_summary['residual_decision_count']}` | `{observable_tree_summary['best_clean_false_changes']}` | rejected |",
                "",
                f"- Observable predicates tested: `{observable_tree_summary['predicate_count']}`.",
                f"- Best tree depth/nodes: `{observable_tree_summary['best_depth']}` / `{observable_tree_summary['best_node_count']}`.",
                f"- Prequential zero-clean-false-change cells: `{observable_tree_summary['prequential_zero_clean_false_change_cells']}/{observable_tree_summary['prequential_cells']}`.",
                f"- Prequential cover-all-test-residual cells: `{observable_tree_summary['prequential_cover_all_test_residual_cells']}/{observable_tree_summary['prequential_cells']}`.",
                "",
                "The tree gives a stronger full-fit separator than the active baseline",
                "without changing clean controls, but it recovers only `4/10`",
                "residuals and recovers `0` held-out residuals in every split that",
                "contains residuals. This rejects a small observable finite-state",
                "decision tree as the missing parser.",
                "",
            ]
        )
    if target_boundary_summary is not None:
        lines.extend(
            [
                "## Target Boundary Recurrence Control",
                "",
                "Gate 28 tests whether branch choices preserve more recurrent",
                "target-side chunk boundaries. Each branch defines a next boundary",
                "at `target_start + length`; recurrence policies score raw digit",
                "context around that boundary.",
                "",
                "| Policy | Total hits | Residual hits | Clean false changes | Boundary |",
                "|---|---:|---:|---:|---|",
                f"| Active branch baseline | `{target_boundary_summary['active_baseline_total_hits']}/{target_boundary_summary['decision_count']}` | `{target_boundary_summary['active_baseline_residual_hits']}/{target_boundary_summary['residual_decision_count']}` | `{target_boundary_summary['active_baseline_clean_false_changes']}` | retained control |",
                f"| Best recurrence policy `{target_boundary_summary['best_recurrence_policy']}` | `{target_boundary_summary['best_recurrence_total_hits']}/{target_boundary_summary['decision_count']}` | `{target_boundary_summary['best_recurrence_residual_hits']}/{target_boundary_summary['residual_decision_count']}` | `{target_boundary_summary['best_recurrence_clean_false_changes']}` | rejected |",
                "",
                f"- Recurrence policies tested: `{target_boundary_summary['policy_count']}`.",
                f"- Radii tested: `{target_boundary_summary['radii']}`.",
                f"- Prequential zero-clean-false-change cells: `{target_boundary_summary['prequential_zero_clean_false_change_cells']}/{target_boundary_summary['prequential_cells']}`.",
                f"- Prequential cover-all-test-residual cells: `{target_boundary_summary['prequential_cover_all_test_residual_cells']}/{target_boundary_summary['prequential_cells']}`.",
                "",
                "Target-side boundary recurrence is not the missing segmentation",
                "rule. The best recurrence policy gets only `1/10` residuals,",
                "changes `194` clean controls, and is worse than random-boundary",
                "controls on total hits.",
                "",
            ]
        )
    if future_copy_summary is not None:
        lines.extend(
            [
                "## Future Copy Opportunity Control",
                "",
                "Gate 29 tests whether branch choices preserve or create",
                "near-future copy opportunities. Each branch is scored by copy",
                "availability at its boundary and within a short lookahead window.",
                "",
                "| Policy | Total hits | Residual hits | Clean false changes | Boundary |",
                "|---|---:|---:|---:|---|",
                f"| Active branch baseline | `{future_copy_summary['active_baseline_total_hits']}/{future_copy_summary['decision_count']}` | `{future_copy_summary['active_baseline_residual_hits']}/{future_copy_summary['residual_decision_count']}` | `{future_copy_summary['active_baseline_clean_false_changes']}` | retained control |",
                f"| Best opportunity policy `{future_copy_summary['best_policy']}` | `{future_copy_summary['best_total_hits']}/{future_copy_summary['decision_count']}` | `{future_copy_summary['best_residual_hits']}/{future_copy_summary['residual_decision_count']}` | `{future_copy_summary['best_clean_false_changes']}` | rejected |",
                "",
                f"- Lookahead positions: `{future_copy_summary['lookahead']}`.",
                f"- Opportunity policies tested: `{future_copy_summary['policy_count']}`.",
                f"- Prequential zero-clean-false-change cells: `{future_copy_summary['prequential_zero_clean_false_change_cells']}/{future_copy_summary['prequential_cells']}`.",
                f"- Prequential cover-all-test-residual cells: `{future_copy_summary['prequential_cover_all_test_residual_cells']}/{future_copy_summary['prequential_cells']}`.",
                "",
                "Near-future copy opportunity does not explain the residual branch",
                "choices. The best policy catches only `2/10` residuals and changes",
                "`130` clean controls, while randomized feature controls do better",
                "on total hits.",
                "",
            ]
        )
    if source_state_summary is not None:
        lines.extend(
            [
                "## Source State Continuity Control",
                "",
                "Gate 30 tests whether branch choices preserve continuity with",
                "the previous copy in the accepted book-local prefix path: same",
                "source, source at previous source end, same source end, or",
                "minimum source/length deltas.",
                "",
                "| Policy | Total hits | Residual hits | Clean false changes | Boundary |",
                "|---|---:|---:|---:|---|",
                f"| Active branch baseline | `{source_state_summary['active_baseline_total_hits']}/{source_state_summary['decision_count']}` | `{source_state_summary['active_baseline_residual_hits']}/{source_state_summary['residual_decision_count']}` | `{source_state_summary['active_baseline_clean_false_changes']}` | retained control |",
                f"| Best source-state policy `{source_state_summary['best_policy']}` | `{source_state_summary['best_total_hits']}/{source_state_summary['decision_count']}` | `{source_state_summary['best_residual_hits']}/{source_state_summary['residual_decision_count']}` | `{source_state_summary['best_clean_false_changes']}` | rejected |",
                "",
                f"- Decisions with previous-copy state: `{source_state_summary['eligible_prev_copy_decisions']}`.",
                f"- Residual decisions with previous-copy state: `{source_state_summary['eligible_prev_copy_residual_decisions']}/{source_state_summary['residual_decision_count']}`.",
                f"- Best eligible residual hits: `{source_state_summary['best_eligible_residual_hits']}/{source_state_summary['best_eligible_residual_total']}`.",
                f"- Prequential zero-clean-false-change cells: `{source_state_summary['prequential_zero_clean_false_change_cells']}/{source_state_summary['prequential_cells']}`.",
                f"- Prequential cover-all-test-residual cells: `{source_state_summary['prequential_cover_all_test_residual_cells']}/{source_state_summary['prequential_cells']}`.",
                "",
                "Book-local source-state continuity is not the missing parser",
                "rule. It is stronger than shuffled source-state controls and",
                "does catch some residuals, but the gain is bought by changing",
                "clean decisions and it fails the clean holdout gate.",
                "",
            ]
        )
    if global_source_state_summary is not None:
        lines.extend(
            [
                "## Global Source State Continuity Upper Bound",
                "",
                "Gate 31 grants a stronger version of the source-state hypothesis:",
                "the previous-copy state is carried across books and is built from",
                "the full stable-projection history before each decision. Candidate",
                "branches are still scored only by source/source-end/length",
                "continuity.",
                "",
                "| Policy | Total hits | Residual hits | Clean false changes | Boundary |",
                "|---|---:|---:|---:|---|",
                f"| Active branch baseline | `{global_source_state_summary['active_baseline_total_hits']}/{global_source_state_summary['decision_count']}` | `{global_source_state_summary['active_baseline_residual_hits']}/{global_source_state_summary['residual_decision_count']}` | `{global_source_state_summary['active_baseline_clean_false_changes']}` | retained control |",
                f"| Best global source-state policy `{global_source_state_summary['best_policy']}` | `{global_source_state_summary['best_total_hits']}/{global_source_state_summary['decision_count']}` | `{global_source_state_summary['best_residual_hits']}/{global_source_state_summary['residual_decision_count']}` | `{global_source_state_summary['best_clean_false_changes']}` | rejected upper bound |",
                "",
                f"- Residual decisions with previous-copy state: `{global_source_state_summary['eligible_prev_copy_residual_decisions']}/{global_source_state_summary['residual_decision_count']}`.",
                f"- Best eligible residual hits: `{global_source_state_summary['best_eligible_residual_hits']}/{global_source_state_summary['best_eligible_residual_total']}`.",
                f"- Prequential zero-clean-false-change cells: `{global_source_state_summary['prequential_zero_clean_false_change_cells']}/{global_source_state_summary['prequential_cells']}`.",
                f"- Prequential cover-all-test-residual cells: `{global_source_state_summary['prequential_cover_all_test_residual_cells']}/{global_source_state_summary['prequential_cells']}`.",
                "",
                "Even with stable-projection history granted, source-state continuity",
                "does not become a parser rule: it catches some residuals but still",
                "changes clean decisions and fails the clean holdout gate.",
                "",
            ]
        )
    if phase_grid_summary is not None:
        lines.extend(
            [
                "## Phase/Grid Segmentation Control",
                "",
                "Gate 32 tests whether branch choices preserve a simple cycle",
                "or grid phase over target boundary, operation length, source,",
                "source end, or source-target alignment. Cycles tested are",
                "`2/3/4/5/8/10/16/20`.",
                "",
                "| Policy | Total hits | Residual hits | Clean false changes | Boundary |",
                "|---|---:|---:|---:|---|",
                f"| Active branch baseline | `{phase_grid_summary['active_baseline_total_hits']}/{phase_grid_summary['decision_count']}` | `{phase_grid_summary['active_baseline_residual_hits']}/{phase_grid_summary['residual_decision_count']}` | `{phase_grid_summary['active_baseline_clean_false_changes']}` | retained control |",
                f"| Best phase/grid policy `{phase_grid_summary['best_policy']}` | `{phase_grid_summary['best_total_hits']}/{phase_grid_summary['decision_count']}` | `{phase_grid_summary['best_residual_hits']}/{phase_grid_summary['residual_decision_count']}` | `{phase_grid_summary['best_clean_false_changes']}` | weak full-fit clue, rejected rule |",
                "",
                f"- Phase/grid policies tested: `{phase_grid_summary['policy_count']}`.",
                f"- Prequential zero-clean-false-change cells: `{phase_grid_summary['prequential_zero_clean_false_change_cells']}/{phase_grid_summary['prequential_cells']}`.",
                f"- Prequential cover-all-test-residual cells: `{phase_grid_summary['prequential_cover_all_test_residual_cells']}/{phase_grid_summary['prequential_cells']}`.",
                f"- Prequential selected matches oracle cells: `{phase_grid_summary['prequential_selected_matches_oracle_cells']}/{phase_grid_summary['prequential_cells']}`.",
                "",
                "The `source_mod0_10/20` family gives a one-residual full-fit",
                "clue without false clean-control changes, but it does not",
                "generalize under prefix/holdout and leaves `9/10` residuals",
                "unexplained. Phase/grid alignment is therefore not the missing",
                "segmentation parser.",
                "",
            ]
        )
    if context_nearest_summary is not None:
        lines.extend(
            [
                "## Context Nearest-Branch Control",
                "",
                "Gate 33 tests whether stable branch actions recur with raw",
                "digit context. Each policy finds the nearest prior or other-book",
                "decision by target-context Hamming distance and applies that",
                "training row's stable branch action class to the current branch",
                "set.",
                "",
                "| Policy | Total hits | Residual hits | Clean false changes | Boundary |",
                "|---|---:|---:|---:|---|",
                f"| Active branch baseline | `{context_nearest_summary['active_baseline_total_hits']}/{context_nearest_summary['decision_count']}` | `{context_nearest_summary['active_baseline_residual_hits']}/{context_nearest_summary['residual_decision_count']}` | `{context_nearest_summary['active_baseline_clean_false_changes']}` | retained control |",
                f"| Best leave-one-book nearest policy `{context_nearest_summary['best_policy']}` | `{context_nearest_summary['best_leave_one_book_total_hits']}/{context_nearest_summary['decision_count']}` | `{context_nearest_summary['best_leave_one_book_residual_hits']}/{context_nearest_summary['residual_decision_count']}` | `{context_nearest_summary['best_leave_one_book_clean_false_changes']}` | rejected |",
                "",
                f"- Nearest-context policies tested: `{context_nearest_summary['policy_count']}`.",
                f"- Prequential zero-clean-false-change cells: `{context_nearest_summary['prequential_zero_clean_false_change_cells']}/{context_nearest_summary['prequential_cells']}`.",
                f"- Prequential cover-all-test-residual cells: `{context_nearest_summary['prequential_cover_all_test_residual_cells']}/{context_nearest_summary['prequential_cells']}`.",
                f"- Prequential selected matches oracle cells: `{context_nearest_summary['prequential_selected_matches_oracle_cells']}/{context_nearest_summary['prequential_cells']}`.",
                "",
                "Raw digit context nearest-neighbor recurrence does not explain",
                "the branch decisions. It is worse than the active baseline,",
                "recovers `0/10` residuals, and shuffled training labels match",
                "or exceed it.",
                "",
            ]
        )
    lines.extend(
        [
            "## Next Blocker",
            "",
            "The next real blocker is not another local length policy or",
            "a single residual feature flag, and not a simple first-branch",
            "continuation objective or small prefix-trained branch ranker.",
            "A finite context table has weak full-fit signal, but stability",
            "tests collapse it under leave-one-book/context controls. The",
            "hierarchical backoff variant still fails clean holdout, and a",
            "small observable decision tree still misses held-out residuals.",
            "Target-side boundary recurrence and near-future copy opportunity",
            "are also rejected. Book-local source-state continuity is rejected",
            "as well, and even the global carryover source-state upper bound",
            "fails clean holdout. A simple phase/grid rule gives only a weak",
            "one-residual full-fit clue. Raw context nearest-neighbor recurrence",
            "is also rejected. The remaining blocker is a richer path/state",
            "segmentation account for why the parser waits, copies, or",
            "understops at the remaining mixed residual sites, or a source-free",
            "account of why the target digit stream exists.",
            "Any promoted parser must close the residual drift without",
            "smuggling in declared literal windows, target text generation,",
            "or the stable projection as an oracle.",
            "",
            "## Sources",
            "",
            "- [Segmentation decision trace](test_results/01_segmentation_decision_trace.md)",
            "- [Structural segmentation hypothesis audit](test_results/02_structural_segmentation_hypothesis_audit.md)",
            "- [Parser dependency reduction ledger](test_results/04_parser_dependency_reduction_ledger.md)",
            "- [Literal gap boundary audit](test_results/05_literal_gap_boundary_audit.md)",
            "- [Online literal stop rule audit](test_results/06_online_literal_stop_rule_audit.md)",
            "- [Literal stop exception topology audit](test_results/07_literal_stop_exception_topology_audit.md)",
            "- [Integrated online literal parser audit](test_results/08_integrated_online_literal_parser_audit.md)",
            "- [Integrated parser policy and drift audit](test_results/09_integrated_parser_policy_and_drift_audit.md)",
            "- [Integrated parser override audit](test_results/10_integrated_parser_override_audit.md)",
            "- [Integrated parser peak strength audit](test_results/11_integrated_parser_peak_strength_audit.md)",
            "- [Integrated parser residual context audit](test_results/12_integrated_parser_residual_context_audit.md)",
            "- [Global objective parser audit](test_results/13_global_objective_parser_audit.md)",
            "- [Feature weighted global parser audit](test_results/14_feature_weighted_global_parser_audit.md)",
            "- [Source boundary alignment audit](test_results/15_source_boundary_alignment_audit.md)",
            "- [Single drift repair oracle audit](test_results/16_single_drift_repair_oracle_audit.md)",
            "- [Observable repair policy audit](test_results/17_observable_repair_policy_audit.md)",
            "- [Conditional repair classifier audit](test_results/18_conditional_repair_classifier_audit.md)",
            "- [Two-stage conditional repair audit](test_results/19_two_stage_conditional_repair_audit.md)",
            "- [Post-repair residual oracle audit](test_results/20_post_repair_residual_oracle_audit.md)",
            "- [Post-repair residual feature audit](test_results/21_post_repair_residual_feature_audit.md)",
            "- [Residual branch continuation audit](test_results/22_residual_branch_continuation_audit.md)",
            "- [Branch ranker prequential audit](test_results/23_branch_ranker_prequential_audit.md)",
            "- [Contextual mode selector audit](test_results/24_contextual_mode_selector_audit.md)",
            "- [Contextual mode stability audit](test_results/25_contextual_mode_stability_audit.md)",
            "- [Hierarchical context backoff audit](test_results/26_hierarchical_context_backoff_audit.md)",
            "- [Observable decision tree policy audit](test_results/27_observable_decision_tree_policy_audit.md)",
            "- [Target boundary recurrence audit](test_results/28_target_boundary_recurrence_audit.md)",
            "- [Future copy opportunity audit](test_results/29_future_copy_opportunity_audit.md)",
            "- [Source state continuity audit](test_results/30_source_state_continuity_audit.md)",
            "- [Global source state continuity audit](test_results/31_global_source_state_continuity_audit.md)",
            "- [Phase grid segmentation audit](test_results/32_phase_grid_segmentation_audit.md)",
            "- [Context nearest branch audit](test_results/33_context_nearest_branch_audit.md)",
            "",
        ]
    )

    REPORTS.mkdir(parents=True, exist_ok=True)
    FINAL.write_text("\n".join(lines), encoding="utf-8")
    print(FINAL)


if __name__ == "__main__":
    main()
