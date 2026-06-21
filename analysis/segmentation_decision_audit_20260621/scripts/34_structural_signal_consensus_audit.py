from __future__ import annotations

import importlib.util
import json
import random
from collections import Counter
from itertools import product
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

BRANCH_CONTINUATION_SCRIPT = HERE / "scripts" / "22_residual_branch_continuation_audit.py"
TARGET_BOUNDARY_SCRIPT = HERE / "scripts" / "28_target_boundary_recurrence_audit.py"
FUTURE_COPY_SCRIPT = HERE / "scripts" / "29_future_copy_opportunity_audit.py"
SOURCE_STATE_SCRIPT = HERE / "scripts" / "30_source_state_continuity_audit.py"
GLOBAL_SOURCE_STATE_SCRIPT = HERE / "scripts" / "31_global_source_state_continuity_audit.py"
PHASE_GRID_SCRIPT = HERE / "scripts" / "32_phase_grid_segmentation_audit.py"
CONTEXT_NEAREST = TEST_RESULTS / "33_context_nearest_branch_audit.json"

OUT_STEM = "34_structural_signal_consensus_audit"
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
RANDOM_CONTROLS = 100
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


def op_key(op: dict[str, Any]) -> tuple[Any, ...]:
    return (op["type"], int(op["target_start"]), int(op["length"]), op.get("source"))


def branch_key(branch: dict[str, Any]) -> tuple[Any, ...]:
    return op_key(branch["op"])


def active_branch(row: dict[str, Any]) -> dict[str, Any]:
    for branch in row["decision"]["branches"]:
        if branch["is_active"]:
            return branch
    raise RuntimeError("missing active branch")


def stable_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return op_key(row["decision"]["stable_op"])


def active_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return branch_key(active_branch(row))


def branch_by_key(row: dict[str, Any], key: tuple[Any, ...]) -> dict[str, Any] | None:
    for branch in row["decision"]["branches"]:
        if branch_key(branch) == key:
            return branch
    return None


def policy_label(config: dict[str, Any]) -> str:
    return (
        f"k{config['threshold']}:"
        f"source={config['source_policy']}:"
        f"phase={config['phase_policy']}:"
        f"future={config['future_policy']}:"
        f"boundary={config['boundary_policy']}"
    )


def config_grid() -> list[dict[str, Any]]:
    configs = []
    for source_policy, phase_policy, future_policy, boundary_policy, threshold in product(
        ["local_min_source_delta", "global_min_source_delta"],
        ["source_mod0_10", "source_mod0_20"],
        ["max_copy_positions", "max_window_best_len"],
        ["max_left_right_r8", "multi_radius_sum"],
        [2, 3, 4],
    ):
        configs.append(
            {
                "source_policy": source_policy,
                "phase_policy": phase_policy,
                "future_policy": future_policy,
                "boundary_policy": boundary_policy,
                "threshold": threshold,
            }
        )
    return configs


def build_family_choices(decisions: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    gate28 = load_module("target_boundary_for_gate34", TARGET_BOUNDARY_SCRIPT)
    gate29 = load_module("future_copy_for_gate34", FUTURE_COPY_SCRIPT)
    gate30 = load_module("source_state_for_gate34", SOURCE_STATE_SCRIPT)
    gate31 = load_module("global_source_state_for_gate34", GLOBAL_SOURCE_STATE_SCRIPT)
    gate32 = load_module("phase_grid_for_gate34", PHASE_GRID_SCRIPT)

    books = gate29.load_books()
    full_counts = gate28.substring_counts(
        books,
        sorted(books),
        {radius for radius in gate28.RADII} | {2 * radius for radius in gate28.RADII},
    )
    prefixes = gate29.previous_prefixes_for_cutoff(books)

    source_local_rows = gate30.choice_rows(decisions)
    state_before = gate31.stable_state_before_decisions(
        load_module("branch_continuation_for_gate34_state", BRANCH_CONTINUATION_SCRIPT),
        gate30,
    )
    source_global_rows = gate31.choice_rows(decisions, state_before, gate30)
    phase_rows = gate32.choice_rows(decisions)
    future_rows = gate29.choice_rows(books, prefixes, decisions)
    boundary_rows = gate28.choice_rows(books, full_counts, decisions)

    out: dict[str, list[dict[str, Any]]] = {
        "local_min_source_delta": [],
        "global_min_source_delta": [],
        "source_mod0_10": [],
        "source_mod0_20": [],
        "max_copy_positions": [],
        "max_window_best_len": [],
        "max_left_right_r8": [],
        "multi_radius_sum": [],
    }
    for index, decision in enumerate(decisions):
        out["local_min_source_delta"].append(
            gate30.choose_policy(source_local_rows[index], "min_source_delta")["branch"]
        )
        out["global_min_source_delta"].append(
            gate30.choose_policy(source_global_rows[index], "min_source_delta")["branch"]
        )
        out["source_mod0_10"].append(
            gate32.choose_policy(phase_rows[index], "source_mod0_10")["branch"]
        )
        out["source_mod0_20"].append(
            gate32.choose_policy(phase_rows[index], "source_mod0_20")["branch"]
        )
        out["max_copy_positions"].append(
            gate29.choose_policy(future_rows[index], "max_copy_positions")["branch"]
        )
        out["max_window_best_len"].append(
            gate29.choose_policy(future_rows[index], "max_window_best_len")["branch"]
        )
        out["max_left_right_r8"].append(
            gate28.choose_policy(boundary_rows[index], "max_left_right_r8")["branch"]
        )
        out["multi_radius_sum"].append(
            gate28.choose_policy(boundary_rows[index], "multi_radius_sum")["branch"]
        )
    return out


def chosen_key_for_config(
    row: dict[str, Any],
    index: int,
    family_choices: dict[str, list[dict[str, Any]]],
    config: dict[str, Any],
) -> tuple[Any, ...]:
    votes = [
        family_choices[config["source_policy"]][index],
        family_choices[config["phase_policy"]][index],
        family_choices[config["future_policy"]][index],
        family_choices[config["boundary_policy"]][index],
    ]
    active = active_key(row)
    counts: Counter[tuple[Any, ...]] = Counter(
        branch_key(branch) for branch in votes if branch_key(branch) != active
    )
    if not counts:
        return active
    key, count = max(
        counts.items(),
        key=lambda item: (
            item[1],
            branch_by_key(row, item[0])["is_active"] if branch_by_key(row, item[0]) else False,
            str(item[0]),
        ),
    )
    if count >= int(config["threshold"]):
        return key
    return active


def score_config(
    decisions: list[dict[str, Any]],
    family_choices: dict[str, list[dict[str, Any]]],
    config: dict[str, Any],
    indices: list[int] | None = None,
) -> dict[str, Any]:
    if indices is None:
        indices = list(range(len(decisions)))
    selected = []
    for index in indices:
        row = {"decision": decisions[index]}
        key = chosen_key_for_config(row, index, family_choices, config)
        branch = branch_by_key(row, key)
        selected.append(
            {
                "book": decisions[index]["book"],
                "kind": decisions[index]["kind"],
                "chosen_is_stable": key == stable_key(row),
                "chosen_is_active": key == active_key(row),
                "chosen_label": None if branch is None else branch["label"],
            }
        )
    residual = [row for row in selected if row["kind"] == "residual_first_drift"]
    clean = [row for row in selected if row["kind"] == "clean_control"]
    return {
        "policy": policy_label(config),
        "config": config,
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
            sorted(
                Counter(row["chosen_label"] for row in selected).items(),
                key=lambda item: str(item[0]),
            )
        ),
    }


def active_score(decisions: list[dict[str, Any]], indices: list[int] | None = None) -> dict[str, Any]:
    if indices is None:
        indices = list(range(len(decisions)))
    selected = []
    for index in indices:
        row = {"decision": decisions[index]}
        key = active_key(row)
        selected.append(
            {
                "book": decisions[index]["book"],
                "kind": decisions[index]["kind"],
                "chosen_is_stable": key == stable_key(row),
                "chosen_label": branch_by_key(row, key)["label"],
            }
        )
    residual = [row for row in selected if row["kind"] == "residual_first_drift"]
    clean = [row for row in selected if row["kind"] == "clean_control"]
    return {
        "policy": "prefer_active_control",
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


def scoreboard(
    decisions: list[dict[str, Any]],
    family_choices: dict[str, list[dict[str, Any]]],
    indices: list[int] | None = None,
) -> list[dict[str, Any]]:
    scores = [
        score_config(decisions, family_choices, config, indices)
        for config in config_grid()
    ]
    return sorted(
        scores,
        key=lambda row: (
            -row["total_hits"],
            -row["residual_hits"],
            row["clean_false_changes"],
            row["policy"],
        ),
    )


def prequential_rows(
    decisions: list[dict[str, Any]],
    family_choices: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    rows = []
    for cutoff in PREFIX_CUTOFFS:
        train_indices = [
            index for index, row in enumerate(decisions) if int(row["book"]) < cutoff
        ]
        test_indices = [
            index for index, row in enumerate(decisions) if int(row["book"]) >= cutoff
        ]
        train_scores = scoreboard(decisions, family_choices, train_indices)
        selected = train_scores[0]
        test_score = score_config(
            decisions,
            family_choices,
            selected["config"],
            test_indices,
        )
        oracle = scoreboard(decisions, family_choices, test_indices)[0]
        rows.append(
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
    return rows


def shuffled_family_control(
    decisions: list[dict[str, Any]],
    family_choices: dict[str, list[dict[str, Any]]],
    real_best: dict[str, Any],
) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED)
    total_hits = []
    residual_hits = []
    clean_false_changes = []
    keys = list(family_choices)
    for _ in range(RANDOM_CONTROLS):
        shuffled: dict[str, list[dict[str, Any]]] = {}
        for key in keys:
            values = list(family_choices[key])
            rng.shuffle(values)
            shuffled[key] = values
        best = max(scoreboard(decisions, shuffled), key=score_key)
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
    context_nearest = load_json(CONTEXT_NEAREST)
    assert_boundary("context_nearest_branch_audit", context_nearest)
    if context_nearest["summary"]["promotes_context_nearest_policy"]:
        raise RuntimeError("gate34 expects gate33 to be rejected")
    gate22 = load_module("branch_continuation_for_gate34", BRANCH_CONTINUATION_SCRIPT)
    decisions = gate22.collect_decisions()["decisions"]
    family_choices = build_family_choices(decisions)
    active = active_score(decisions)
    scores = scoreboard(decisions, family_choices)
    best = scores[0]
    preq = prequential_rows(decisions, family_choices)
    controls = shuffled_family_control(decisions, family_choices, best)
    residual_total = sum(1 for row in decisions if row["kind"] == "residual_first_drift")
    promotes = (
        best["residual_hits"] == residual_total
        and best["clean_false_changes"] == 0
        and all(row["test_clean_false_changes"] == 0 for row in preq)
        and all(row["test_residual_hits"] == row["test_residual_total"] for row in preq)
    )
    classification = (
        "structural_signal_consensus_policy_promoted"
        if promotes
        else "structural_signal_consensus_policy_rejected"
    )
    return {
        "schema": "structural_signal_consensus_audit.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "branch_continuation_script": rel(BRANCH_CONTINUATION_SCRIPT),
            "target_boundary_script": rel(TARGET_BOUNDARY_SCRIPT),
            "future_copy_script": rel(FUTURE_COPY_SCRIPT),
            "source_state_script": rel(SOURCE_STATE_SCRIPT),
            "global_source_state_script": rel(GLOBAL_SOURCE_STATE_SCRIPT),
            "phase_grid_script": rel(PHASE_GRID_SCRIPT),
            "context_nearest_audit": rel(CONTEXT_NEAREST),
        },
        "scope": {
            "analysis_only": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "family_count": 4,
            "config_count": len(config_grid()),
            "target_text_required": True,
            "stable_projection_used_as_training_label": False,
            "source_free_digit_generator_emitted": False,
            "promotes_parser_rule": promotes,
        },
        "summary": {
            "decision_count": len(decisions),
            "residual_decision_count": residual_total,
            "clean_control_count": len(decisions) - residual_total,
            "family_count": 4,
            "config_count": len(config_grid()),
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
            "promotes_structural_signal_consensus": promotes,
            "interpretation": (
                "Gate 34 tests whether independent weak structural signals become "
                "usable only when multiple families agree on the same non-active "
                "branch."
            ),
        },
        "active_baseline": active,
        "full_fit_scoreboard": [active] + scores,
        "prequential_rows": preq,
        "shuffled_family_control": controls,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": classification,
            "source_length_dependency_status": "structural_signal_consensus_rejected"
            if not promotes
            else "structural_signal_consensus_promoted",
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
        for row in result["full_fit_scoreboard"][:10]
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
    c = result["shuffled_family_control"]
    body = f"""# Structural Signal Consensus Audit

Classification: `{result['classification']}`
Translation delta: `NONE`

## Purpose

Gate 34 tests whether weak structural signals become useful only when they
agree. Four families vote on the current candidate branches:

- source-state continuity;
- phase/grid alignment;
- near-future copy opportunity;
- recurrent target boundary.

The consensus rule keeps the active branch unless at least `k` families choose
the same non-active branch. This is a parser decision test, not a bit sweep.

## Summary

- Decisions: `{s['decision_count']}`.
- Residual first-drift decisions: `{s['residual_decision_count']}`.
- Clean controls: `{s['clean_control_count']}`.
- Signal families: `{s['family_count']}`.
- Consensus configs tested: `{s['config_count']}`.
- Active baseline: `{s['active_baseline_total_hits']}/{s['decision_count']}`,
  residual `{s['active_baseline_residual_hits']}/{s['residual_decision_count']}`,
  clean false changes `{s['active_baseline_clean_false_changes']}`.
- Best consensus policy: `{s['best_policy']}`.
- Best consensus result: `{s['best_total_hits']}/{s['decision_count']}`,
  residual `{s['best_residual_hits']}/{s['residual_decision_count']}`,
  clean false changes `{s['best_clean_false_changes']}`.

## Full-Fit Policies

{md_table(full_rows, ["policy", "total hits", "residual hits", "clean false changes", "residual misses"])}

## Prefix/Holdout

{md_table(preq_rows, ["cutoff", "selected policy", "train hits", "test hits", "test residual hits", "test clean false changes", "matches oracle"])}

## Shuffled Family Control

- Controls: `{c['controls']}`.
- Total-hit range under shuffled family votes:
  `{c['total_hits_min']}..{c['total_hits_max']}`.
- Median total hits under controls: `{c['total_hits_median']}`.
- Max residual hits under controls: `{c['residual_hits_max']}`.
- Minimum clean false changes under controls: `{c['clean_false_changes_min']}`.
- `p(total_hits >= real_best)`: `{c['p_total_hits_ge_real']:.6f}`.
- `p(residual_hits >= real_best)`: `{c['p_residual_hits_ge_real']:.6f}`.

## Decision

- Promotes structural-signal consensus parser policy:
  `{s['promotes_structural_signal_consensus']}`.
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
