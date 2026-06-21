from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

BRANCH_CONTINUATION_SCRIPT = HERE / "scripts" / "22_residual_branch_continuation_audit.py"
LOCAL_SOURCE_STATE_SCRIPT = HERE / "scripts" / "30_source_state_continuity_audit.py"
LOCAL_SOURCE_STATE = TEST_RESULTS / "30_source_state_continuity_audit.json"

OUT_STEM = "31_global_source_state_continuity_audit"


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


def op_key(op: dict[str, Any]) -> tuple[int, int]:
    return int(op["book"]), int(op["target_start"])


def stable_state_before_decisions(gate22, gate30) -> dict[tuple[int, int], dict[str, Any]]:
    trace_module = gate22.load_module("segmentation_trace_for_gate31", gate22.TRACE_SCRIPT)
    gate111 = gate22.load_module("gate111_for_segmentation_gate31", gate22.GATE111_SCRIPT)
    books = {int(key): value for key, value in gate22.load_json(gate22.BOOKS_DIGITS).items()}
    projected_ops = trace_module.projected_ops_from_copy_rows(
        gate111.make_copy_rows(), books
    )
    stable_by_book: dict[int, list[dict[str, Any]]] = {}
    for op in projected_ops:
        stable_by_book.setdefault(int(op["book"]), []).append(op)
    for rows in stable_by_book.values():
        rows.sort(key=lambda row: int(row["target_start"]))

    state = gate30.initial_state()
    state_before: dict[tuple[int, int], dict[str, Any]] = {}
    for book in range(10, 70):
        for stable_index, op in enumerate(stable_by_book[book]):
            normalized = {
                "type": op["type"],
                "book": book,
                "target_start": int(op["target_start"]),
                "length": int(op["length"]),
                "source": op["source"],
            }
            state_before[(book, stable_index)] = dict(state)
            gate30.update_state(state, normalized)
    return state_before


def choice_rows(
    decisions: list[dict[str, Any]],
    state_before: dict[tuple[int, int], dict[str, Any]],
    gate30,
) -> list[dict[str, Any]]:
    rows = []
    for decision in decisions:
        key = (int(decision["book"]), int(decision["stable_index"]))
        if key not in state_before:
            raise RuntimeError(f"missing stable state for {key}")
        state = state_before[key]
        branches = [
            {
                "book": int(decision["book"]),
                "kind": decision["kind"],
                "branch": branch,
                "features": gate30.branch_features(state, branch),
                "state": dict(state),
            }
            for branch in decision["branches"]
        ]
        rows.append({"decision": decision, "state": dict(state), "branches": branches})
    return rows


def make_result() -> dict[str, Any]:
    local_source_state = load_json(LOCAL_SOURCE_STATE)
    assert_boundary("source_state_continuity_audit", local_source_state)
    if local_source_state["summary"]["promotes_source_state_continuity_policy"]:
        raise RuntimeError("gate31 expects gate30 to be rejected")

    gate22 = load_module("branch_continuation_for_gate31", BRANCH_CONTINUATION_SCRIPT)
    gate30 = load_module("local_source_state_for_gate31", LOCAL_SOURCE_STATE_SCRIPT)
    decisions = gate22.collect_decisions()["decisions"]
    state_before = stable_state_before_decisions(gate22, gate30)
    rows = choice_rows(decisions, state_before, gate30)
    active = gate30.score_policy(rows, "prefer_active_control")
    scores = gate30.scoreboard(rows, gate30.source_state_policy_names())
    best = scores[0]
    preq = gate30.prequential_rows(rows)
    controls = gate30.randomized_feature_control(rows, best)
    residual_total = sum(1 for row in decisions if row["kind"] == "residual_first_drift")
    eligible_residual_total = sum(
        1
        for row in rows
        if row["decision"]["kind"] == "residual_first_drift"
        and row["state"]["has_prev_copy"]
    )
    promotes = (
        best["residual_hits"] == residual_total
        and best["clean_false_changes"] == 0
        and all(row["test_clean_false_changes"] == 0 for row in preq)
        and all(row["test_residual_hits"] == row["test_residual_total"] for row in preq)
    )
    classification = (
        "global_source_state_continuity_policy_promoted"
        if promotes
        else "global_source_state_continuity_policy_rejected"
    )
    return {
        "schema": "global_source_state_continuity_audit.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "branch_continuation_script": rel(BRANCH_CONTINUATION_SCRIPT),
            "local_source_state_script": rel(LOCAL_SOURCE_STATE_SCRIPT),
            "local_source_state_audit": rel(LOCAL_SOURCE_STATE),
        },
        "scope": {
            "analysis_only": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "global_carryover_state": True,
            "oracle_stable_history_required": True,
            "target_text_required": True,
            "stable_projection_used_as_current_decision_feature": False,
            "source_free_digit_generator_emitted": False,
            "promotes_parser_rule": promotes,
        },
        "summary": {
            "decision_count": len(decisions),
            "residual_decision_count": residual_total,
            "clean_control_count": len(decisions) - residual_total,
            "eligible_prev_copy_decisions": sum(
                1 for row in rows if row["state"]["has_prev_copy"]
            ),
            "eligible_prev_copy_residual_decisions": eligible_residual_total,
            "policy_count": len(gate30.source_state_policy_names()),
            "active_baseline_total_hits": active["total_hits"],
            "active_baseline_residual_hits": active["residual_hits"],
            "active_baseline_clean_false_changes": active["clean_false_changes"],
            "best_policy": best["policy"],
            "best_total_hits": best["total_hits"],
            "best_eligible_hits": best["eligible_hits"],
            "best_eligible_total": best["eligible_total"],
            "best_residual_hits": best["residual_hits"],
            "best_eligible_residual_hits": best["eligible_residual_hits"],
            "best_eligible_residual_total": best["eligible_residual_total"],
            "best_clean_false_changes": best["clean_false_changes"],
            "prequential_cells": len(preq),
            "prequential_zero_clean_false_change_cells": sum(
                1 for row in preq if row["test_clean_false_changes"] == 0
            ),
            "prequential_cover_all_test_residual_cells": sum(
                1
                for row in preq
                if row["test_residual_hits"] == row["test_residual_total"]
            ),
            "prequential_selected_matches_oracle_cells": sum(
                1 for row in preq if row["selected_matches_oracle_total_hits"]
            ),
            "promotes_global_source_state_continuity_policy": promotes,
            "interpretation": (
                "Gate 31 grants full stable-projection history as a global "
                "previous-copy state and tests whether current branch choice "
                "then follows source/source-end/length continuity."
            ),
        },
        "active_baseline": active,
        "full_fit_scoreboard": [active] + scores,
        "prequential_rows": preq,
        "randomized_feature_control": controls,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": classification,
            "source_length_dependency_status": "global_source_state_continuity_rejected"
            if not promotes
            else "global_source_state_continuity_promoted",
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
    full_rows = [
        [
            row["policy"],
            f"{row['total_hits']}/{row['total_total']}",
            f"{row['eligible_hits']}/{row['eligible_total']}",
            f"{row['residual_hits']}/{row['residual_total']}",
            f"{row['eligible_residual_hits']}/{row['eligible_residual_total']}",
            row["clean_false_changes"],
            row["residual_miss_books"],
        ]
        for row in result["full_fit_scoreboard"][:8]
    ]
    preq_rows = [
        [
            row["cutoff_book"],
            row["selected_policy"],
            f"{row['train_total_hits']}/{row['train_total']}",
            f"{row['test_total_hits']}/{row['test_total']}",
            f"{row['test_residual_hits']}/{row['test_residual_total']}",
            f"{row['test_eligible_residual_hits']}/{row['test_eligible_residual_total']}",
            row["test_clean_false_changes"],
            row["selected_matches_oracle_total_hits"],
        ]
        for row in result["prequential_rows"]
    ]
    c = result["randomized_feature_control"]
    body = f"""# Global Source State Continuity Audit

Classification: `{result['classification']}`
Translation delta: `NONE`

## Purpose

Gate 31 tests the carryover version of the source-state hypothesis. Unlike gate
30, the previous-copy state is not reset at each book. It is built by replaying
the full stable projection before the current decision, then candidate branches
are scored by source/source-end/length continuity.

This is an intentionally favorable upper-bound test for the hypothesis: the
history state is granted from the stable projection. It is not a source-free
generator and not a row0-origin test.

## Summary

- Decisions: `{s['decision_count']}`.
- Residual first-drift decisions: `{s['residual_decision_count']}`.
- Clean controls: `{s['clean_control_count']}`.
- Decisions with previous-copy state: `{s['eligible_prev_copy_decisions']}`.
- Residual decisions with previous-copy state:
  `{s['eligible_prev_copy_residual_decisions']}/{s['residual_decision_count']}`.
- Source-state policies tested: `{s['policy_count']}`.
- Active baseline: `{s['active_baseline_total_hits']}/{s['decision_count']}`,
  residual `{s['active_baseline_residual_hits']}/{s['residual_decision_count']}`,
  clean false changes `{s['active_baseline_clean_false_changes']}`.
- Best global source-state policy: `{s['best_policy']}`.
- Best result: `{s['best_total_hits']}/{s['decision_count']}`,
  eligible `{s['best_eligible_hits']}/{s['best_eligible_total']}`,
  residual `{s['best_residual_hits']}/{s['residual_decision_count']}`,
  eligible residual
  `{s['best_eligible_residual_hits']}/{s['best_eligible_residual_total']}`,
  clean false changes `{s['best_clean_false_changes']}`.

## Full-Fit Policies

{md_table(full_rows, ["policy", "total hits", "eligible hits", "residual hits", "eligible residual hits", "clean false changes", "residual misses"])}

## Prefix/Holdout

{md_table(preq_rows, ["cutoff", "selected policy", "train hits", "test hits", "test residual hits", "test eligible residual hits", "test clean false changes", "matches oracle"])}

## Randomized Feature Control

- Controls: `{c['controls']}`.
- Total-hit range under per-decision shuffled source-state features:
  `{c['total_hits_min']}..{c['total_hits_max']}`.
- Median total hits under controls: `{c['total_hits_median']}`.
- Max residual hits under controls: `{c['residual_hits_max']}`.
- Minimum clean false changes under controls: `{c['clean_false_changes_min']}`.
- `p(total_hits >= real_best)`: `{c['p_total_hits_ge_real']:.6f}`.
- `p(residual_hits >= real_best)`: `{c['p_residual_hits_ge_real']:.6f}`.

## Decision

- Promotes global source-state continuity parser policy:
  `{s['promotes_global_source_state_continuity_policy']}`.
- Prequential zero-clean-false-change cells:
  `{s['prequential_zero_clean_false_change_cells']}/{s['prequential_cells']}`.
- Prequential cover-all-test-residual cells:
  `{s['prequential_cover_all_test_residual_cells']}/{s['prequential_cells']}`.
- The test grants stable-projection history, so any positive result would still
  need a source-free way to obtain that state.
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
