from __future__ import annotations

import importlib.util
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

BRANCH_CONTINUATION_SCRIPT = HERE / "scripts" / "22_residual_branch_continuation_audit.py"
CONSENSUS_SCRIPT = HERE / "scripts" / "34_structural_signal_consensus_audit.py"
CONSENSUS_AUDIT = TEST_RESULTS / "34_structural_signal_consensus_audit.json"

OUT_STEM = "35_structural_vote_residual_decomposition"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


def vote_specs() -> list[tuple[str, str]]:
    return [
        ("source_local", "local_min_source_delta"),
        ("source_global", "global_min_source_delta"),
        ("phase_10", "source_mod0_10"),
        ("phase_20", "source_mod0_20"),
        ("future_positions", "max_copy_positions"),
        ("future_window", "max_window_best_len"),
        ("boundary_r8", "max_left_right_r8"),
        ("boundary_multi", "multi_radius_sum"),
    ]


def decompose_row(
    consensus,
    decision: dict[str, Any],
    family_choices: dict[str, list[dict[str, Any]]],
    index: int,
) -> dict[str, Any]:
    row = {"decision": decision}
    stable = consensus.stable_key(row)
    active = consensus.active_key(row)
    votes = []
    key_counts: Counter[tuple[Any, ...]] = Counter()
    family_counts: Counter[str] = Counter()
    for family, key in vote_specs():
        branch = family_choices[key][index]
        branch_key = consensus.branch_key(branch)
        key_counts[branch_key] += 1
        family_counts[family.split("_", 1)[0]] += branch_key == stable
        votes.append(
            {
                "family": family,
                "policy_key": key,
                "votes_stable": branch_key == stable,
                "votes_active": branch_key == active,
                "branch_label": branch["label"],
                "branch_op": branch["op"],
            }
        )
    nonactive_counts = {
        str(key): value for key, value in key_counts.items() if key != active
    }
    top_key, top_count = max(
        ((key, value) for key, value in key_counts.items() if key != active),
        key=lambda item: (item[1], str(item[0])),
        default=(active, 0),
    )
    return {
        "book": decision["book"],
        "target_start": decision["target_start"],
        "stable_index": decision["stable_index"],
        "kind": decision["kind"],
        "drift_class": decision["drift_class"],
        "active_op": decision["active_op"],
        "stable_op": decision["stable_op"],
        "active_support": key_counts[active],
        "stable_support": key_counts[stable],
        "nonactive_top_support": 0 if top_key == active else top_count,
        "top_nonactive_is_stable": top_key == stable,
        "stable_support_by_family": dict(sorted(family_counts.items())),
        "nonactive_vote_counts": nonactive_counts,
        "votes": votes,
    }


def threshold_rows(rows: list[dict[str, Any]], threshold: int) -> dict[str, Any]:
    triggered = [row for row in rows if row["nonactive_top_support"] >= threshold]
    residual = [row for row in rows if row["kind"] == "residual_first_drift"]
    clean = [row for row in rows if row["kind"] == "clean_control"]
    triggered_residual = [
        row for row in triggered if row["kind"] == "residual_first_drift"
    ]
    triggered_clean = [row for row in triggered if row["kind"] == "clean_control"]
    return {
        "threshold": threshold,
        "triggered_total": len(triggered),
        "triggered_residual": len(triggered_residual),
        "triggered_clean": len(triggered_clean),
        "triggered_stable_residual": sum(
            1 for row in triggered_residual if row["top_nonactive_is_stable"]
        ),
        "triggered_false_clean": len(triggered_clean),
        "residual_total": len(residual),
        "clean_total": len(clean),
        "residual_books_triggered": [row["book"] for row in triggered_residual],
        "residual_books_stable_triggered": [
            row["book"] for row in triggered_residual if row["top_nonactive_is_stable"]
        ],
    }


def make_result() -> dict[str, Any]:
    consensus_audit = load_json(CONSENSUS_AUDIT)
    assert_boundary("structural_signal_consensus_audit", consensus_audit)
    if consensus_audit["summary"]["promotes_structural_signal_consensus"]:
        raise RuntimeError("gate35 expects gate34 to be rejected")

    gate22 = load_module("branch_continuation_for_gate35", BRANCH_CONTINUATION_SCRIPT)
    consensus = load_module("consensus_for_gate35", CONSENSUS_SCRIPT)
    decisions = gate22.collect_decisions()["decisions"]
    family_choices = consensus.build_family_choices(decisions)
    rows = [
        decompose_row(consensus, decision, family_choices, index)
        for index, decision in enumerate(decisions)
    ]
    residual_rows = [row for row in rows if row["kind"] == "residual_first_drift"]
    clean_rows = [row for row in rows if row["kind"] == "clean_control"]
    support_hist = Counter(row["stable_support"] for row in residual_rows)
    clean_top_hist = Counter(row["nonactive_top_support"] for row in clean_rows)
    threshold_summary = [threshold_rows(rows, threshold) for threshold in [1, 2, 3, 4]]
    classification = "structural_vote_residual_decomposition_audit_only"
    return {
        "schema": "structural_vote_residual_decomposition.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "branch_continuation_script": rel(BRANCH_CONTINUATION_SCRIPT),
            "consensus_script": rel(CONSENSUS_SCRIPT),
            "consensus_audit": rel(CONSENSUS_AUDIT),
        },
        "scope": {
            "analysis_only": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "vote_count": len(vote_specs()),
            "target_text_required": True,
            "stable_projection_used_as_training_label": False,
            "source_free_digit_generator_emitted": False,
            "promotes_parser_rule": False,
        },
        "summary": {
            "decision_count": len(rows),
            "residual_decision_count": len(residual_rows),
            "clean_control_count": len(clean_rows),
            "vote_count": len(vote_specs()),
            "residual_stable_support_histogram": dict(sorted(support_hist.items())),
            "clean_top_nonactive_support_histogram": dict(sorted(clean_top_hist.items())),
            "residuals_with_stable_support_ge_1": sum(
                1 for row in residual_rows if row["stable_support"] >= 1
            ),
            "residuals_with_stable_support_ge_2": sum(
                1 for row in residual_rows if row["stable_support"] >= 2
            ),
            "residuals_with_stable_support_ge_3": sum(
                1 for row in residual_rows if row["stable_support"] >= 3
            ),
            "clean_rows_with_nonactive_support_ge_2": sum(
                1 for row in clean_rows if row["nonactive_top_support"] >= 2
            ),
            "clean_rows_with_nonactive_support_ge_3": sum(
                1 for row in clean_rows if row["nonactive_top_support"] >= 3
            ),
            "max_residual_stable_support": max(
                row["stable_support"] for row in residual_rows
            ),
            "max_clean_nonactive_support": max(
                row["nonactive_top_support"] for row in clean_rows
            ),
            "promotes_structural_vote_rule": False,
            "interpretation": (
                "Gate 35 decomposes each residual and clean-control decision by "
                "the structural family votes used in gate 34. It audits whether "
                "the rejected weak-signal front has a hidden coherent residual "
                "pattern."
            ),
        },
        "threshold_summary": threshold_summary,
        "residual_rows": residual_rows,
        "representative_clean_risk_rows": [
            row for row in clean_rows if row["nonactive_top_support"] >= 3
        ][:20],
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": classification,
            "source_length_dependency_status": "weak_signal_frontier_decomposed_no_rule",
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
    threshold_rows_md = [
        [
            row["threshold"],
            row["triggered_total"],
            row["triggered_residual"],
            row["triggered_stable_residual"],
            row["triggered_false_clean"],
            row["residual_books_stable_triggered"],
        ]
        for row in result["threshold_summary"]
    ]
    residual_rows_md = [
        [
            row["book"],
            row["target_start"],
            row["drift_class"],
            row["stable_support"],
            row["active_support"],
            row["nonactive_top_support"],
            row["top_nonactive_is_stable"],
            row["stable_support_by_family"],
        ]
        for row in result["residual_rows"]
    ]
    body = f"""# Structural Vote Residual Decomposition

Classification: `{result['classification']}`
Translation delta: `NONE`

## Purpose

Gate 35 decomposes the rejected weak-signal consensus front. Instead of
proposing another policy, it asks whether the residual decisions share a hidden
vote pattern across the structural families already tested:

- local/global source-state continuity;
- phase/grid alignment;
- future-copy opportunity;
- recurrent target boundary.

## Summary

- Decisions: `{s['decision_count']}`.
- Residual first-drift decisions: `{s['residual_decision_count']}`.
- Clean controls: `{s['clean_control_count']}`.
- Structural votes per decision: `{s['vote_count']}`.
- Residual stable-support histogram:
  `{s['residual_stable_support_histogram']}`.
- Clean top-nonactive-support histogram:
  `{s['clean_top_nonactive_support_histogram']}`.
- Residuals with stable support `>=1/2/3`:
  `{s['residuals_with_stable_support_ge_1']}/`
  `{s['residuals_with_stable_support_ge_2']}/`
  `{s['residuals_with_stable_support_ge_3']}`.
- Clean rows with non-active support `>=2/3`:
  `{s['clean_rows_with_nonactive_support_ge_2']}/`
  `{s['clean_rows_with_nonactive_support_ge_3']}`.

## Threshold Diagnostic

{md_table(threshold_rows_md, ["threshold", "triggered total", "triggered residual", "stable residual", "false clean", "stable residual books"])}

## Residual Rows

{md_table(residual_rows_md, ["book", "target_start", "drift_class", "stable support", "active support", "top nonactive support", "top nonactive stable", "stable support by family"])}

## Decision

- Promotes structural vote rule: `{s['promotes_structural_vote_rule']}`.
- The weak-signal front has no hidden clean threshold: residual support and
  clean-control risk overlap.
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
