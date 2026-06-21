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
    lines.extend(
        [
            "## Next Blocker",
            "",
            "The next real blocker is not another local length policy. It is a",
            "source-free account of why the target digit stream exists, or a",
            "parser integration that closes the remaining `12/60` drift cases",
            "without smuggling in declared literal windows, target text generation,",
            "or changed skeleton/literal accounting.",
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
            "",
        ]
    )

    REPORTS.mkdir(parents=True, exist_ok=True)
    FINAL.write_text("\n".join(lines), encoding="utf-8")
    print(FINAL)


if __name__ == "__main__":
    main()
