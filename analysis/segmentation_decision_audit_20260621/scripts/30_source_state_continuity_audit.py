from __future__ import annotations

import importlib.util
import json
import random
from collections import Counter
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

BRANCH_CONTINUATION_SCRIPT = HERE / "scripts" / "22_residual_branch_continuation_audit.py"
FUTURE_COPY = TEST_RESULTS / "29_future_copy_opportunity_audit.json"

OUT_STEM = "30_source_state_continuity_audit"
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
RANDOM_CONTROLS = 50
RANDOM_SEED = 46920260621
BIG_DISTANCE = 10**9


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


def initial_state() -> dict[str, Any]:
    return {
        "has_prev_copy": False,
        "prev_copy_source": None,
        "prev_copy_end": None,
        "prev_copy_length": None,
        "prev_copy_target_start": None,
        "prev_copy_target_end": None,
        "previous_type": "BOS",
        "previous_length": 0,
        "copy_count_so_far": 0,
    }


def update_state(state: dict[str, Any], op: dict[str, Any]) -> None:
    state["previous_type"] = op["type"]
    state["previous_length"] = int(op["length"])
    if op["type"] != "copy":
        return
    source = int(op["source"])
    length = int(op["length"])
    target_start = int(op["target_start"])
    state["has_prev_copy"] = True
    state["prev_copy_source"] = source
    state["prev_copy_end"] = source + length
    state["prev_copy_length"] = length
    state["prev_copy_target_start"] = target_start
    state["prev_copy_target_end"] = target_start + length
    state["copy_count_so_far"] += 1


def branch_features(state: dict[str, Any], branch: dict[str, Any]) -> dict[str, Any]:
    op = branch["op"]
    is_copy = op["type"] == "copy" and op.get("source") is not None
    has_prev = bool(state["has_prev_copy"])
    if not is_copy:
        return {
            "is_copy": False,
            "has_prev_copy": has_prev,
            "source": None,
            "source_end": None,
            "source_delta_abs": BIG_DISTANCE,
            "source_to_prev_end_abs": BIG_DISTANCE,
            "source_end_delta_abs": BIG_DISTANCE,
            "length_delta_abs": BIG_DISTANCE,
            "source_equals_prev_source": False,
            "source_equals_prev_end": False,
            "source_end_equals_prev_end": False,
        }
    source = int(op["source"])
    length = int(op["length"])
    source_end = source + length
    if not has_prev:
        return {
            "is_copy": True,
            "has_prev_copy": False,
            "source": source,
            "source_end": source_end,
            "source_delta_abs": BIG_DISTANCE,
            "source_to_prev_end_abs": BIG_DISTANCE,
            "source_end_delta_abs": BIG_DISTANCE,
            "length_delta_abs": BIG_DISTANCE,
            "source_equals_prev_source": False,
            "source_equals_prev_end": False,
            "source_end_equals_prev_end": False,
        }
    prev_source = int(state["prev_copy_source"])
    prev_end = int(state["prev_copy_end"])
    prev_length = int(state["prev_copy_length"])
    return {
        "is_copy": True,
        "has_prev_copy": True,
        "source": source,
        "source_end": source_end,
        "source_delta_abs": abs(source - prev_source),
        "source_to_prev_end_abs": abs(source - prev_end),
        "source_end_delta_abs": abs(source_end - prev_end),
        "length_delta_abs": abs(length - prev_length),
        "source_equals_prev_source": source == prev_source,
        "source_equals_prev_end": source == prev_end,
        "source_end_equals_prev_end": source_end == prev_end,
    }


def choice_rows(decisions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    state_by_book: dict[int, dict[str, Any]] = {}
    for decision in decisions:
        book = int(decision["book"])
        state = state_by_book.setdefault(book, initial_state())
        branches = [
            {
                "book": book,
                "kind": decision["kind"],
                "branch": branch,
                "features": branch_features(state, branch),
                "state": dict(state),
            }
            for branch in decision["branches"]
        ]
        rows.append({"decision": decision, "state": dict(state), "branches": branches})
        if decision["kind"] == "clean_control":
            update_state(state, decision["active_op"])
    return rows


def policy_functions() -> dict[str, Callable[[dict[str, Any]], tuple[Any, ...]]]:
    return {
        "prefer_same_source": lambda row: (
            row["features"]["has_prev_copy"],
            row["features"]["is_copy"],
            row["features"]["source_equals_prev_source"],
            row["branch"]["is_active"],
            row["branch"]["label"],
        ),
        "prefer_source_at_prev_end": lambda row: (
            row["features"]["has_prev_copy"],
            row["features"]["is_copy"],
            row["features"]["source_equals_prev_end"],
            row["branch"]["is_active"],
            row["branch"]["label"],
        ),
        "prefer_same_source_end": lambda row: (
            row["features"]["has_prev_copy"],
            row["features"]["is_copy"],
            row["features"]["source_end_equals_prev_end"],
            row["branch"]["is_active"],
            row["branch"]["label"],
        ),
        "min_source_delta": lambda row: (
            row["features"]["has_prev_copy"],
            row["features"]["is_copy"],
            -row["features"]["source_delta_abs"],
            row["branch"]["is_active"],
            row["branch"]["label"],
        ),
        "min_source_to_prev_end_delta": lambda row: (
            row["features"]["has_prev_copy"],
            row["features"]["is_copy"],
            -row["features"]["source_to_prev_end_abs"],
            row["branch"]["is_active"],
            row["branch"]["label"],
        ),
        "min_source_end_delta": lambda row: (
            row["features"]["has_prev_copy"],
            row["features"]["is_copy"],
            -row["features"]["source_end_delta_abs"],
            row["branch"]["is_active"],
            row["branch"]["label"],
        ),
        "min_length_delta_after_copy": lambda row: (
            row["features"]["has_prev_copy"],
            row["features"]["is_copy"],
            -row["features"]["length_delta_abs"],
            row["branch"]["is_active"],
            row["branch"]["label"],
        ),
        "prefer_active_control": lambda row: (
            row["branch"]["is_active"],
            row["branch"]["label"],
        ),
    }


def source_state_policy_names() -> list[str]:
    return [name for name in policy_functions() if name != "prefer_active_control"]


def choose_policy(row: dict[str, Any], policy: str) -> dict[str, Any]:
    return max(row["branches"], key=policy_functions()[policy])


def score_policy(rows: list[dict[str, Any]], policy: str) -> dict[str, Any]:
    selected = []
    for row in rows:
        chosen = choose_policy(row, policy)
        decision = row["decision"]
        selected.append(
            {
                "book": decision["book"],
                "kind": decision["kind"],
                "has_prev_copy": row["state"]["has_prev_copy"],
                "chosen_is_stable": chosen["branch"]["is_stable"],
                "chosen_is_active": chosen["branch"]["is_active"],
                "chosen_label": chosen["branch"]["label"],
            }
        )
    residual = [row for row in selected if row["kind"] == "residual_first_drift"]
    clean = [row for row in selected if row["kind"] == "clean_control"]
    eligible = [row for row in selected if row["has_prev_copy"]]
    return {
        "policy": policy,
        "total_hits": sum(1 for row in selected if row["chosen_is_stable"]),
        "total_total": len(selected),
        "eligible_hits": sum(1 for row in eligible if row["chosen_is_stable"]),
        "eligible_total": len(eligible),
        "residual_hits": sum(1 for row in residual if row["chosen_is_stable"]),
        "residual_total": len(residual),
        "eligible_residual_hits": sum(
            1
            for row in residual
            if row["has_prev_copy"] and row["chosen_is_stable"]
        ),
        "eligible_residual_total": sum(1 for row in residual if row["has_prev_copy"]),
        "clean_false_changes": sum(1 for row in clean if not row["chosen_is_stable"]),
        "clean_total": len(clean),
        "residual_miss_books": [
            row["book"] for row in residual if not row["chosen_is_stable"]
        ],
        "selected_label_counts": dict(
            sorted(Counter(row["chosen_label"] for row in selected).items())
        ),
    }


def score_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        row["total_hits"],
        row["residual_hits"],
        row["eligible_residual_hits"],
        -row["clean_false_changes"],
        row["policy"],
    )


def scoreboard(rows: list[dict[str, Any]], policies: list[str]) -> list[dict[str, Any]]:
    scores = [score_policy(rows, policy) for policy in policies]
    return sorted(
        scores,
        key=lambda row: (
            -row["total_hits"],
            -row["residual_hits"],
            -row["eligible_residual_hits"],
            row["clean_false_changes"],
            row["policy"],
        ),
    )


def prequential_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    policies = source_state_policy_names()
    out = []
    for cutoff in PREFIX_CUTOFFS:
        train = [row for row in rows if row["decision"]["book"] < cutoff]
        test = [row for row in rows if row["decision"]["book"] >= cutoff]
        selected = scoreboard(train, policies)[0]
        test_score = score_policy(test, selected["policy"])
        oracle = scoreboard(test, policies)[0]
        out.append(
            {
                "cutoff_book": cutoff,
                "selected_policy": selected["policy"],
                "train_total_hits": selected["total_hits"],
                "train_total": selected["total_total"],
                "train_residual_hits": selected["residual_hits"],
                "train_residual_total": selected["residual_total"],
                "train_clean_false_changes": selected["clean_false_changes"],
                "test_total_hits": test_score["total_hits"],
                "test_total": test_score["total_total"],
                "test_residual_hits": test_score["residual_hits"],
                "test_residual_total": test_score["residual_total"],
                "test_eligible_residual_hits": test_score["eligible_residual_hits"],
                "test_eligible_residual_total": test_score["eligible_residual_total"],
                "test_clean_false_changes": test_score["clean_false_changes"],
                "test_residual_miss_books": test_score["residual_miss_books"],
                "oracle_policy": oracle["policy"],
                "oracle_test_total_hits": oracle["total_hits"],
                "oracle_test_residual_hits": oracle["residual_hits"],
                "oracle_test_clean_false_changes": oracle["clean_false_changes"],
                "selected_matches_oracle_total_hits": (
                    test_score["total_hits"] == oracle["total_hits"]
                ),
            }
        )
    return out


def randomized_feature_control(
    rows: list[dict[str, Any]],
    real_best: dict[str, Any],
) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED)
    policies = source_state_policy_names()
    total_hits = []
    residual_hits = []
    clean_false_changes = []
    for _ in range(RANDOM_CONTROLS):
        randomized = []
        for row in rows:
            copied = {"decision": row["decision"], "state": row["state"], "branches": []}
            feature_pool = [branch["features"] for branch in row["branches"]]
            for branch in row["branches"]:
                copied["branches"].append(
                    {
                        "book": branch["book"],
                        "kind": branch["kind"],
                        "branch": branch["branch"],
                        "features": rng.choice(feature_pool),
                        "state": branch["state"],
                    }
                )
            randomized.append(copied)
        best = max((score_policy(randomized, policy) for policy in policies), key=score_key)
        total_hits.append(best["total_hits"])
        residual_hits.append(best["residual_hits"])
        clean_false_changes.append(best["clean_false_changes"])
    return {
        "controls": RANDOM_CONTROLS,
        "total_hits_min": min(total_hits),
        "total_hits_median": sorted(total_hits)[len(total_hits) // 2],
        "total_hits_max": max(total_hits),
        "residual_hits_max": max(residual_hits),
        "clean_false_changes_min": min(clean_false_changes),
        "p_total_hits_ge_real": (
            sum(1 for value in total_hits if value >= real_best["total_hits"]) + 1
        )
        / (RANDOM_CONTROLS + 1),
        "p_residual_hits_ge_real": (
            sum(1 for value in residual_hits if value >= real_best["residual_hits"]) + 1
        )
        / (RANDOM_CONTROLS + 1),
    }


def make_result() -> dict[str, Any]:
    future_copy = load_json(FUTURE_COPY)
    assert_boundary("future_copy_opportunity_audit", future_copy)
    if future_copy["summary"]["promotes_future_copy_opportunity_policy"]:
        raise RuntimeError("gate30 expects gate29 to be rejected")
    gate22 = load_module("branch_continuation_for_gate30", BRANCH_CONTINUATION_SCRIPT)
    decisions = gate22.collect_decisions()["decisions"]
    rows = choice_rows(decisions)
    active = score_policy(rows, "prefer_active_control")
    scores = scoreboard(rows, source_state_policy_names())
    best = scores[0]
    preq = prequential_rows(rows)
    controls = randomized_feature_control(rows, best)
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
        and eligible_residual_total == residual_total
        and all(row["test_clean_false_changes"] == 0 for row in preq)
        and all(row["test_residual_hits"] == row["test_residual_total"] for row in preq)
    )
    classification = (
        "source_state_continuity_policy_promoted"
        if promotes
        else "source_state_continuity_policy_rejected"
    )
    return {
        "schema": "source_state_continuity_audit.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "branch_continuation_script": rel(BRANCH_CONTINUATION_SCRIPT),
            "future_copy_opportunity_audit": rel(FUTURE_COPY),
        },
        "scope": {
            "analysis_only": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "book_local_state_only": True,
            "target_text_required": True,
            "stable_projection_used_as_training_label": False,
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
            "policy_count": len(source_state_policy_names()),
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
            "promotes_source_state_continuity_policy": promotes,
            "interpretation": (
                "Gate 30 tests whether branch choice follows continuity with the "
                "previous copy source/end/length in the already accepted book-local "
                "prefix path."
            ),
        },
        "active_baseline": active,
        "full_fit_scoreboard": [active] + scores,
        "prequential_rows": preq,
        "randomized_feature_control": controls,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": classification,
            "source_length_dependency_status": "source_state_continuity_rejected"
            if not promotes
            else "source_state_continuity_promoted",
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
    body = f"""# Source State Continuity Audit

Classification: `{result['classification']}`
Translation delta: `NONE`

## Purpose

Gate 30 tests whether the remaining branch choices are explained by continuity
with the previous copy in the already accepted book-local prefix path. The
candidate features are previous source, previous source end, previous copy
length, and proximity to those values.

This is a structural parser test, not a bit sweep and not a row0-origin test.
It does not use the stable branch as a feature.

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
- Best source-state policy: `{s['best_policy']}`.
- Best source-state result: `{s['best_total_hits']}/{s['decision_count']}`,
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

- Promotes source-state continuity parser policy:
  `{s['promotes_source_state_continuity_policy']}`.
- Prequential zero-clean-false-change cells:
  `{s['prequential_zero_clean_false_change_cells']}/{s['prequential_cells']}`.
- Prequential cover-all-test-residual cells:
  `{s['prequential_cover_all_test_residual_cells']}/{s['prequential_cells']}`.
- The test is book-local: it does not claim a cross-book hidden source state.
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
