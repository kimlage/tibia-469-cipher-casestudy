from __future__ import annotations

import importlib.util
import json
import random
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

BRANCH_CONTINUATION_SCRIPT = HERE / "scripts" / "22_residual_branch_continuation_audit.py"
GLOBAL_SOURCE_STATE = TEST_RESULTS / "31_global_source_state_continuity_audit.json"

OUT_STEM = "32_phase_grid_segmentation_audit"
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
CYCLES = [2, 3, 4, 5, 8, 10, 16, 20]
RANDOM_CONTROLS = 50
RANDOM_SEED = 46920260621


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


def branch_boundary(branch: dict[str, Any]) -> int:
    op = branch["op"]
    return int(op["target_start"]) + int(op["length"])


def phase_features(branch: dict[str, Any]) -> dict[str, Any]:
    op = branch["op"]
    target_start = int(op["target_start"])
    length = int(op["length"])
    boundary = target_start + length
    source = op.get("source")
    is_copy = op["type"] == "copy" and source is not None
    source_int = None if source is None else int(source)
    source_end = None if source_int is None else source_int + length
    features: dict[str, Any] = {
        "is_copy": is_copy,
        "target_start": target_start,
        "length": length,
        "boundary": boundary,
        "source": source_int,
        "source_end": source_end,
    }
    for cycle in CYCLES:
        features[f"boundary_mod0_{cycle}"] = boundary % cycle == 0
        features[f"length_mod0_{cycle}"] = length % cycle == 0
        features[f"target_start_mod0_{cycle}"] = target_start % cycle == 0
        if not is_copy:
            features[f"source_mod0_{cycle}"] = False
            features[f"source_end_mod0_{cycle}"] = False
            features[f"source_matches_target_start_phase_{cycle}"] = False
            features[f"source_end_matches_boundary_phase_{cycle}"] = False
            features[f"source_matches_boundary_phase_{cycle}"] = False
        else:
            assert source_int is not None and source_end is not None
            features[f"source_mod0_{cycle}"] = source_int % cycle == 0
            features[f"source_end_mod0_{cycle}"] = source_end % cycle == 0
            features[f"source_matches_target_start_phase_{cycle}"] = (
                source_int % cycle == target_start % cycle
            )
            features[f"source_end_matches_boundary_phase_{cycle}"] = (
                source_end % cycle == boundary % cycle
            )
            features[f"source_matches_boundary_phase_{cycle}"] = (
                source_int % cycle == boundary % cycle
            )
    return features


def policy_specs() -> list[dict[str, Any]]:
    specs = []
    for cycle in CYCLES:
        for feature in [
            "boundary_mod0",
            "length_mod0",
            "target_start_mod0",
            "source_mod0",
            "source_end_mod0",
            "source_matches_target_start_phase",
            "source_end_matches_boundary_phase",
            "source_matches_boundary_phase",
        ]:
            specs.append(
                {
                    "policy": f"{feature}_{cycle}",
                    "cycle": cycle,
                    "feature": f"{feature}_{cycle}",
                }
            )
    return specs


def policy_names() -> list[str]:
    return [spec["policy"] for spec in policy_specs()]


def choice_rows(decisions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for decision in decisions:
        branches = [
            {
                "book": decision["book"],
                "kind": decision["kind"],
                "branch": branch,
                "features": phase_features(branch),
            }
            for branch in decision["branches"]
        ]
        rows.append({"decision": decision, "branches": branches})
    return rows


def score_tuple(row: dict[str, Any], policy: str) -> tuple[Any, ...]:
    if policy == "prefer_active_control":
        return (row["branch"]["is_active"], row["branch"]["label"])
    value = bool(row["features"][policy])
    return (
        value,
        row["branch"]["is_active"],
        -int(row["branch"]["op"]["length"]),
        row["branch"]["label"],
    )


def choose_policy(row: dict[str, Any], policy: str) -> dict[str, Any]:
    return max(row["branches"], key=lambda branch: score_tuple(branch, policy))


def score_policy(rows: list[dict[str, Any]], policy: str) -> dict[str, Any]:
    selected = []
    for row in rows:
        chosen = choose_policy(row, policy)
        decision = row["decision"]
        selected.append(
            {
                "book": decision["book"],
                "kind": decision["kind"],
                "chosen_is_stable": chosen["branch"]["is_stable"],
                "chosen_is_active": chosen["branch"]["is_active"],
                "chosen_label": chosen["branch"]["label"],
            }
        )
    residual = [row for row in selected if row["kind"] == "residual_first_drift"]
    clean = [row for row in selected if row["kind"] == "clean_control"]
    return {
        "policy": policy,
        "total_hits": sum(1 for row in selected if row["chosen_is_stable"]),
        "total_total": len(selected),
        "residual_hits": sum(1 for row in residual if row["chosen_is_stable"]),
        "residual_total": len(residual),
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
            row["clean_false_changes"],
            row["policy"],
        ),
    )


def prequential_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    policies = policy_names()
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
    policies = policy_names()
    total_hits = []
    residual_hits = []
    clean_false_changes = []
    for _ in range(RANDOM_CONTROLS):
        randomized = []
        for row in rows:
            copied = {"decision": row["decision"], "branches": []}
            feature_pool = [branch["features"] for branch in row["branches"]]
            for branch in row["branches"]:
                copied["branches"].append(
                    {
                        "book": branch["book"],
                        "kind": branch["kind"],
                        "branch": branch["branch"],
                        "features": rng.choice(feature_pool),
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
    global_source_state = load_json(GLOBAL_SOURCE_STATE)
    assert_boundary("global_source_state_continuity_audit", global_source_state)
    if global_source_state["summary"]["promotes_global_source_state_continuity_policy"]:
        raise RuntimeError("gate32 expects gate31 to be rejected")
    gate22 = load_module("branch_continuation_for_gate32", BRANCH_CONTINUATION_SCRIPT)
    decisions = gate22.collect_decisions()["decisions"]
    rows = choice_rows(decisions)
    active = score_policy(rows, "prefer_active_control")
    scores = scoreboard(rows, policy_names())
    best = scores[0]
    preq = prequential_rows(rows)
    controls = randomized_feature_control(rows, best)
    residual_total = sum(1 for row in decisions if row["kind"] == "residual_first_drift")
    promotes = (
        best["residual_hits"] == residual_total
        and best["clean_false_changes"] == 0
        and all(row["test_clean_false_changes"] == 0 for row in preq)
        and all(row["test_residual_hits"] == row["test_residual_total"] for row in preq)
    )
    classification = (
        "phase_grid_segmentation_policy_promoted"
        if promotes
        else "phase_grid_segmentation_policy_rejected"
    )
    return {
        "schema": "phase_grid_segmentation_audit.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "branch_continuation_script": rel(BRANCH_CONTINUATION_SCRIPT),
            "global_source_state_audit": rel(GLOBAL_SOURCE_STATE),
        },
        "scope": {
            "analysis_only": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "cycle_set": CYCLES,
            "policy_count": len(policy_names()),
            "target_text_required": True,
            "stable_projection_used_as_training_label": False,
            "source_free_digit_generator_emitted": False,
            "promotes_parser_rule": promotes,
        },
        "summary": {
            "decision_count": len(decisions),
            "residual_decision_count": residual_total,
            "clean_control_count": len(decisions) - residual_total,
            "cycles": CYCLES,
            "policy_count": len(policy_names()),
            "active_baseline_total_hits": active["total_hits"],
            "active_baseline_residual_hits": active["residual_hits"],
            "active_baseline_clean_false_changes": active["clean_false_changes"],
            "best_policy": best["policy"],
            "best_total_hits": best["total_hits"],
            "best_residual_hits": best["residual_hits"],
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
            "promotes_phase_grid_policy": promotes,
            "interpretation": (
                "Gate 32 tests whether branch choice follows simple phase/grid "
                "constraints over target boundary, length, source, source end, "
                "and source-target alignment."
            ),
        },
        "active_baseline": active,
        "full_fit_scoreboard": [active] + scores,
        "prequential_rows": preq,
        "randomized_feature_control": controls,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": classification,
            "source_length_dependency_status": "phase_grid_segmentation_rejected"
            if not promotes
            else "phase_grid_segmentation_promoted",
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
            f"{row['residual_hits']}/{row['residual_total']}",
            row["clean_false_changes"],
            row["residual_miss_books"],
        ]
        for row in result["full_fit_scoreboard"][:12]
    ]
    preq_rows = [
        [
            row["cutoff_book"],
            row["selected_policy"],
            f"{row['train_total_hits']}/{row['train_total']}",
            f"{row['test_total_hits']}/{row['test_total']}",
            f"{row['test_residual_hits']}/{row['test_residual_total']}",
            row["test_clean_false_changes"],
            row["selected_matches_oracle_total_hits"],
        ]
        for row in result["prequential_rows"]
    ]
    c = result["randomized_feature_control"]
    body = f"""# Phase Grid Segmentation Audit

Classification: `{result['classification']}`
Translation delta: `NONE`

## Purpose

Gate 32 tests whether residual branch choices are explained by a simple
phase/grid constraint over target boundaries, operation lengths, copy sources,
copy source ends, or source-target phase alignment. Cycles tested:
`{s['cycles']}`.

This is a structural parser test, not a bit sweep, row0-origin test, plaintext
claim, or semantic read.

## Summary

- Decisions: `{s['decision_count']}`.
- Residual first-drift decisions: `{s['residual_decision_count']}`.
- Clean controls: `{s['clean_control_count']}`.
- Phase/grid policies tested: `{s['policy_count']}`.
- Active baseline: `{s['active_baseline_total_hits']}/{s['decision_count']}`,
  residual `{s['active_baseline_residual_hits']}/{s['residual_decision_count']}`,
  clean false changes `{s['active_baseline_clean_false_changes']}`.
- Best phase/grid policy: `{s['best_policy']}`.
- Best phase/grid result: `{s['best_total_hits']}/{s['decision_count']}`,
  residual `{s['best_residual_hits']}/{s['residual_decision_count']}`,
  clean false changes `{s['best_clean_false_changes']}`.

## Full-Fit Policies

{md_table(full_rows, ["policy", "total hits", "residual hits", "clean false changes", "residual misses"])}

## Prefix/Holdout

{md_table(preq_rows, ["cutoff", "selected policy", "train hits", "test hits", "test residual hits", "test clean false changes", "matches oracle"])}

## Randomized Feature Control

- Controls: `{c['controls']}`.
- Total-hit range under per-decision shuffled phase features:
  `{c['total_hits_min']}..{c['total_hits_max']}`.
- Median total hits under controls: `{c['total_hits_median']}`.
- Max residual hits under controls: `{c['residual_hits_max']}`.
- Minimum clean false changes under controls: `{c['clean_false_changes_min']}`.
- `p(total_hits >= real_best)`: `{c['p_total_hits_ge_real']:.6f}`.
- `p(residual_hits >= real_best)`: `{c['p_residual_hits_ge_real']:.6f}`.

## Decision

- Promotes phase/grid parser policy: `{s['promotes_phase_grid_policy']}`.
- Prequential zero-clean-false-change cells:
  `{s['prequential_zero_clean_false_change_cells']}/{s['prequential_cells']}`.
- Prequential cover-all-test-residual cells:
  `{s['prequential_cover_all_test_residual_cells']}/{s['prequential_cells']}`.
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
