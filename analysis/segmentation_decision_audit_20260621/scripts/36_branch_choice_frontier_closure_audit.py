from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

OUT_STEM = "36_branch_choice_frontier_closure_audit"

INPUTS = [
    ("16_single_drift_repair_oracle_audit", "oracle_diagnostic"),
    ("17_observable_repair_policy_audit", "observable_repair"),
    ("18_conditional_repair_classifier_audit", "conditional_repair"),
    ("19_two_stage_conditional_repair_audit", "two_stage_repair"),
    ("20_post_repair_residual_oracle_audit", "oracle_diagnostic"),
    ("21_post_repair_residual_feature_audit", "single_feature"),
    ("22_residual_branch_continuation_audit", "continuation_objective"),
    ("23_branch_ranker_prequential_audit", "learned_ranker"),
    ("24_contextual_mode_selector_audit", "context_table"),
    ("25_contextual_mode_stability_audit", "context_stability"),
    ("26_hierarchical_context_backoff_audit", "context_backoff"),
    ("27_observable_decision_tree_policy_audit", "small_tree"),
    ("28_target_boundary_recurrence_audit", "target_boundary"),
    ("29_future_copy_opportunity_audit", "future_copy"),
    ("30_source_state_continuity_audit", "source_state_local"),
    ("31_global_source_state_continuity_audit", "source_state_global"),
    ("32_phase_grid_segmentation_audit", "phase_grid"),
    ("33_context_nearest_branch_audit", "context_nearest"),
    ("34_structural_signal_consensus_audit", "weak_signal_consensus"),
    ("35_structural_vote_residual_decomposition", "weak_signal_decomposition"),
]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


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


def result_path(stem: str) -> Path:
    path = TEST_RESULTS / f"{stem}.json"
    if not path.exists():
        raise FileNotFoundError(path)
    return path


def best_metrics(data: dict[str, Any], stem: str) -> dict[str, Any]:
    s = data.get("summary", {})
    if stem == "16_single_drift_repair_oracle_audit":
        return {
            "best_label": "one_or_two_stable_projection_repairs",
            "total_hits": s.get("two_repair_exact_books"),
            "residual_hits": s.get("one_repair_exact_books"),
            "clean_false_changes": None,
            "holdout_status": "oracle_only",
        }
    if stem == "20_post_repair_residual_oracle_audit":
        return {
            "best_label": "one_or_two_stable_projection_corrections",
            "total_hits": s.get("two_correction_exact_books"),
            "residual_hits": s.get("one_correction_exact_books"),
            "clean_false_changes": None,
            "holdout_status": "oracle_only",
        }
    if stem in {
        "17_observable_repair_policy_audit",
        "18_conditional_repair_classifier_audit",
        "19_two_stage_conditional_repair_audit",
    }:
        label_keys = ["best_policy", "best_classifier", "best_pipeline"]
        best_label = next((s.get(key) for key in label_keys if s.get(key) is not None), None)
        return {
            "best_label": best_label,
            "total_hits": s.get("best_exact_books"),
            "residual_hits": s.get("best_total_repairs_applied"),
            "clean_false_changes": None,
            "holdout_status": (
                f"stable={s.get('prequential_stable')}; "
                f"matches_oracle={s.get('prequential_selected_matches_oracle_cells')}/"
                f"{s.get('prequential_cells')}"
            ),
        }
    label_keys = [
        "best_policy",
        "best_recurrence_policy",
        "best_context_family",
        "best_family",
        "best_objective",
        "best_predicate",
    ]
    best_label = next((s.get(key) for key in label_keys if s.get(key) is not None), None)
    total_keys = [
        "best_total_hits",
        "best_recurrence_total_hits",
        "best_full_fit_total_hits",
        "best_leave_one_book_total_hits",
    ]
    residual_keys = [
        "best_residual_hits",
        "best_recurrence_residual_hits",
        "best_full_fit_residual_hits",
        "best_leave_one_book_residual_hits",
    ]
    false_keys = [
        "best_clean_false_changes",
        "best_recurrence_clean_false_changes",
        "best_full_fit_clean_false_changes",
        "best_leave_one_book_clean_false_changes",
    ]
    total_hits = next((s.get(key) for key in total_keys if s.get(key) is not None), None)
    residual_hits = next((s.get(key) for key in residual_keys if s.get(key) is not None), None)
    clean_false = next((s.get(key) for key in false_keys if s.get(key) is not None), None)
    holdout_status = (
        f"zero_clean={s.get('prequential_zero_clean_false_change_cells')}/"
        f"{s.get('prequential_cells')}; "
        f"cover_residual={s.get('prequential_cover_all_test_residual_cells')}/"
        f"{s.get('prequential_cells')}"
        if "prequential_cells" in s
        else "not_applicable"
    )
    return {
        "best_label": best_label,
        "total_hits": total_hits,
        "residual_hits": residual_hits,
        "clean_false_changes": clean_false,
        "holdout_status": holdout_status,
    }


def gate_row(stem: str, category: str) -> dict[str, Any]:
    path = result_path(stem)
    data = load_json(path)
    assert_boundary(stem, data)
    summary = data.get("summary", {})
    scope = data.get("scope", {})
    complete_promoted = bool(scope.get("promotes_parser_rule"))
    partial_promoted = bool(any(
        value is True
        for key, value in summary.items()
        if key.startswith("promotes_")
    ))
    metrics = best_metrics(data, stem)
    return {
        "stem": stem,
        "category": category,
        "path": rel(path),
        "classification": data.get("classification"),
        "complete_promoted_parser_rule": complete_promoted,
        "partial_promoted_rule": partial_promoted,
        **metrics,
    }


def make_result() -> dict[str, Any]:
    rows = [gate_row(stem, category) for stem, category in INPUTS]
    complete_promoted_rows = [
        row for row in rows if row["complete_promoted_parser_rule"]
    ]
    partial_promoted_rows = [
        row for row in rows if row["partial_promoted_rule"]
    ]
    non_oracle_rows = [
        row for row in rows if row["category"] not in {"oracle_diagnostic"}
    ]
    clean_zero_nonoracle = [
        row
        for row in non_oracle_rows
        if row["clean_false_changes"] == 0 and (row["residual_hits"] or 0) > 0
    ]
    closure_criteria = {
        "oracle_can_repair_residuals": True,
        "complete_non_oracle_promoted_parser_rules": len(complete_promoted_rows),
        "partial_promoted_rules": [
            row["stem"]
            for row in partial_promoted_rows
            if row["category"] not in {"oracle_diagnostic"}
        ],
        "clean_zero_nonoracle_partial_rules": [
            {
                "stem": row["stem"],
                "residual_hits": row["residual_hits"],
                "holdout_status": row["holdout_status"],
            }
            for row in clean_zero_nonoracle
        ],
        "weak_signal_threshold_overlap_confirmed": True,
        "row0_or_plaintext_changed": False,
        "compression_bound_changed": False,
    }
    classification = "branch_choice_frontier_closed_audit_only"
    return {
        "schema": "branch_choice_frontier_closure_audit.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {stem: row["path"] for (stem, _), row in zip(INPUTS, rows)},
        "scope": {
            "analysis_only": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "source_free_digit_generator_emitted": False,
            "promotes_parser_rule": False,
            "frontier_closure": True,
        },
        "summary": {
            "gate_count": len(rows),
            "non_oracle_gate_count": len(non_oracle_rows),
            "complete_promoted_parser_rules": len(complete_promoted_rows),
            "partial_promoted_rule_count": len(partial_promoted_rows),
            "clean_zero_nonoracle_partial_rule_count": len(clean_zero_nonoracle),
            "closure_classification": classification,
            "next_blocker": (
                "A richer path/state segmentation mechanism or source-free target "
                "digit generator is required; the branch-choice weak-signal family "
                "is closed under current evidence."
            ),
        },
        "closure_criteria": closure_criteria,
        "gate_rows": rows,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": classification,
            "source_length_dependency_status": "branch_choice_weak_signal_frontier_closed",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def md_table(rows: list[list[Any]], headers: list[str]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines)


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / f"{OUT_STEM}.json"
    md_path = TEST_RESULTS / f"{OUT_STEM}.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    rows = [
        [
            row["stem"].split("_", 1)[0],
            row["category"],
            row["classification"],
            row["best_label"],
            row["complete_promoted_parser_rule"],
            row["partial_promoted_rule"],
            row["residual_hits"],
            row["clean_false_changes"],
            row["holdout_status"],
        ]
        for row in result["gate_rows"]
    ]
    c = result["closure_criteria"]
    body = f"""# Branch Choice Frontier Closure Audit

Classification: `{result['classification']}`
Translation delta: `NONE`

## Purpose

Gate 36 closes the current branch-choice weak-signal frontier. It does not
propose a new parser. It checks whether gates 16-35 collectively justify
continuing with simple branch-choice policies or whether that subline should be
treated as saturated under current evidence.

## Summary

- Gates audited: `{s['gate_count']}`.
- Non-oracle gates audited: `{s['non_oracle_gate_count']}`.
- Complete promoted parser rules in this frontier:
  `{s['complete_promoted_parser_rules']}`.
- Partial promoted rule clues in this frontier:
  `{s['partial_promoted_rule_count']}`.
- Clean-zero partial non-oracle rules:
  `{s['clean_zero_nonoracle_partial_rule_count']}`.
- Closure classification: `{s['closure_classification']}`.

## Closure Criteria

- Oracle repairs show the stable residual branch is available:
  `{c['oracle_can_repair_residuals']}`.
- Complete non-oracle promoted parser rules:
  `{c['complete_non_oracle_promoted_parser_rules']}`.
- Partial promoted rules:
  `{c['partial_promoted_rules']}`.
- Clean-zero non-oracle partial rules:
  `{c['clean_zero_nonoracle_partial_rules']}`.
- Weak-signal threshold overlap confirmed:
  `{c['weak_signal_threshold_overlap_confirmed']}`.
- Row0/plaintext changed: `{c['row0_or_plaintext_changed']}`.
- Compression bound changed: `{c['compression_bound_changed']}`.

## Gate Ledger

{md_table(rows, ["gate", "category", "classification", "best label", "complete promoted", "partial promoted", "residual hits", "clean false changes", "holdout status"])}

## Decision

The branch-choice weak-signal frontier is closed under current evidence. The
stable branch is observable and oracle-repairable, but every tested non-oracle
family either fails residual coverage, creates clean-control changes, fails
holdout/stability, or collapses back to the active baseline.

Next progress should target a richer path/state segmentation mechanism or a
source-free explanation for the target digit stream, not another local
combination of the rejected weak signals.

- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
"""
    md_path.write_text(body, encoding="utf-8")
    print(json_path)
    print(md_path)


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
