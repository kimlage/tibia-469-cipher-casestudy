from __future__ import annotations

import copy
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
BRANCH_CONTINUATION = TEST_RESULTS / "22_residual_branch_continuation_audit.json"

OUT_STEM = "27_observable_decision_tree_policy_audit"
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
MAX_DEPTHS = [1, 2, 3]
MIN_LEAF_SIZES = [1, 2, 5]
PERMUTATION_CONTROLS = 30
RANDOM_SEED = 46920260621


Predicate = tuple[str, Callable[[dict[str, Any]], bool]]


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


def op_type(decision: dict[str, Any], objective: str, gate22) -> str:
    branch = choose_branch(gate22, decision, objective)
    return branch["op"]["type"]


def branch_count_bucket(count: int) -> str:
    if count <= 10:
        return "few"
    if count <= 20:
        return "mid"
    return "many"


def objective_names(gate22) -> list[str]:
    return ["active_branch"] + [
        name for name in gate22.OBJECTIVES if not name.startswith("oracle_")
    ]


def annotate_objective_indices(gate22, decisions: list[dict[str, Any]]) -> None:
    for decision in decisions:
        objective_index: dict[str, int] = {}
        for objective in objective_names(gate22):
            if objective == "active_branch":
                for index, branch in enumerate(decision["branches"]):
                    if branch["is_active"]:
                        objective_index[objective] = index
                        break
                else:
                    raise RuntimeError(
                        {"type": "missing_active_branch", "book": decision["book"]}
                    )
            else:
                objective_index[objective] = min(
                    range(len(decision["branches"])),
                    key=lambda index, objective=objective: gate22.OBJECTIVES[objective](
                        decision["branches"][index]
                    ),
                )
        decision["_objective_index"] = objective_index


def choose_branch(gate22, decision: dict[str, Any], objective: str) -> dict[str, Any]:
    if "_objective_index" in decision:
        return decision["branches"][decision["_objective_index"][objective]]
    if objective == "active_branch":
        for branch in decision["branches"]:
            if branch["is_active"]:
                return branch
        raise RuntimeError({"type": "missing_active_branch", "book": decision["book"]})
    chosen = gate22.choose_branch(decision, objective)
    if chosen is None:
        raise RuntimeError({"type": "missing_branch", "book": decision["book"]})
    return chosen


def score_objective(
    gate22,
    decisions: list[dict[str, Any]],
    objective: str,
) -> dict[str, Any]:
    rows = []
    for decision in decisions:
        chosen = choose_branch(gate22, decision, objective)
        rows.append(
            {
                "book": decision["book"],
                "kind": decision["kind"],
                "chosen_is_stable": chosen["is_stable"],
                "chosen_is_active": chosen["is_active"],
                "objective": objective,
            }
        )
    return score_rows(rows)


def score_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    residual = [row for row in rows if row["kind"] == "residual_first_drift"]
    clean = [row for row in rows if row["kind"] == "clean_control"]
    return {
        "total_hits": sum(1 for row in rows if row["chosen_is_stable"]),
        "total_total": len(rows),
        "residual_hits": sum(1 for row in residual if row["chosen_is_stable"]),
        "residual_total": len(residual),
        "clean_hits": sum(1 for row in clean if row["chosen_is_stable"]),
        "clean_total": len(clean),
        "clean_false_changes": sum(1 for row in clean if not row["chosen_is_stable"]),
        "residual_miss_books": [
            row["book"] for row in residual if not row["chosen_is_stable"]
        ],
    }


def score_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        row["total_hits"],
        row["residual_hits"],
        -row["clean_false_changes"],
    )


def best_leaf_objective(gate22, decisions: list[dict[str, Any]]) -> str:
    scores = [
        {
            "objective": objective,
            **score_objective(gate22, decisions, objective),
        }
        for objective in objective_names(gate22)
    ]
    return max(
        scores,
        key=lambda row: (
            row["total_hits"],
            row["residual_hits"],
            -row["clean_false_changes"],
            row["objective"],
        ),
    )["objective"]


def branch_for_objective(gate22, decision: dict[str, Any], objective: str) -> dict[str, Any]:
    return choose_branch(gate22, decision, objective)


def feature_predicates(gate22) -> list[Predicate]:
    def active_branch(decision: dict[str, Any]) -> dict[str, Any]:
        return branch_for_objective(gate22, decision, "active_branch")

    predicates: list[Predicate] = [
        ("book_start", lambda row: row["target_start"] == 0),
        ("internal", lambda row: row["target_start"] > 0),
        ("first_op", lambda row: row["stable_index"] == 0),
        ("later_op", lambda row: row["stable_index"] > 0),
        ("active_literal", lambda row: row["active_op"]["type"] == "literal"),
        ("active_copy", lambda row: row["active_op"]["type"] == "copy"),
        ("baseline_literal", lambda row: row["baseline_op"]["type"] == "literal"),
        ("baseline_copy", lambda row: row["baseline_op"]["type"] == "copy"),
        ("active_equals_baseline", lambda row: row["active_op"] == row["baseline_op"]),
        ("branch_count_few", lambda row: len(row["branches"]) <= 10),
        ("branch_count_mid_or_less", lambda row: len(row["branches"]) <= 20),
        ("branch_count_many", lambda row: len(row["branches"]) > 20),
        (
            "active_branch_has_literal_stop_label",
            lambda row: "literal_stop" in active_branch(row)["label"],
        ),
        (
            "active_branch_has_immediate_copy_label",
            lambda row: "immediate_copy" in active_branch(row)["label"],
        ),
    ]
    for value in [1, 3, 5, 8, 13, 21, 34, 55]:
        predicates.extend(
            [
                (
                    f"active_len_le{value}",
                    lambda row, value=value: int(row["active_op"]["length"]) <= value,
                ),
                (
                    f"active_len_ge{value}",
                    lambda row, value=value: int(row["active_op"]["length"]) >= value,
                ),
            ]
        )
    for objective in [
        "balanced_ops_literals",
        "max_suffix_copy_digits",
        "min_suffix_literals",
        "max_suffix_copy_count",
        "min_suffix_ops",
    ]:
        predicates.extend(
            [
                (
                    f"{objective}_differs_from_active",
                    lambda row, objective=objective: not branch_for_objective(
                        gate22, row, objective
                    )["is_active"],
                ),
                (
                    f"{objective}_chooses_copy",
                    lambda row, objective=objective: op_type(row, objective, gate22)
                    == "copy",
                ),
                (
                    f"{objective}_chooses_literal",
                    lambda row, objective=objective: op_type(row, objective, gate22)
                    == "literal",
                ),
            ]
        )
    return predicates


def leaf(objective: str) -> dict[str, Any]:
    return {"type": "leaf", "objective": objective}


def predict(tree: dict[str, Any], decision: dict[str, Any], predicates: dict[str, Callable[[dict[str, Any]], bool]]) -> str:
    node = tree
    while node["type"] != "leaf":
        branch = "true" if predicates[node["predicate"]](decision) else "false"
        node = node[branch]
    return node["objective"]


def tree_rows(
    gate22,
    tree: dict[str, Any],
    decisions: list[dict[str, Any]],
    predicate_map: dict[str, Callable[[dict[str, Any]], bool]],
) -> list[dict[str, Any]]:
    rows = []
    for decision in decisions:
        objective = predict(tree, decision, predicate_map)
        chosen = choose_branch(gate22, decision, objective)
        rows.append(
            {
                "book": decision["book"],
                "kind": decision["kind"],
                "objective": objective,
                "chosen_is_stable": chosen["is_stable"],
                "chosen_is_active": chosen["is_active"],
            }
        )
    return rows


def evaluate_tree(
    gate22,
    tree: dict[str, Any],
    decisions: list[dict[str, Any]],
    predicate_map: dict[str, Callable[[dict[str, Any]], bool]],
) -> dict[str, Any]:
    rows = tree_rows(gate22, tree, decisions, predicate_map)
    score = score_rows(rows)
    score["objective_counts"] = dict(
        sorted(Counter(row["objective"] for row in rows).items())
    )
    return score


def tree_size(tree: dict[str, Any]) -> int:
    if tree["type"] == "leaf":
        return 1
    return 1 + tree_size(tree["true"]) + tree_size(tree["false"])


def tree_depth(tree: dict[str, Any]) -> int:
    if tree["type"] == "leaf":
        return 0
    return 1 + max(tree_depth(tree["true"]), tree_depth(tree["false"]))


def build_tree(
    gate22,
    decisions: list[dict[str, Any]],
    predicates: list[Predicate],
    max_depth: int,
    min_leaf_size: int,
) -> dict[str, Any]:
    objective = best_leaf_objective(gate22, decisions)
    base = leaf(objective)
    predicate_map = dict(predicates)
    base_score = evaluate_tree(gate22, base, decisions, predicate_map)
    if max_depth <= 0 or len(decisions) < 2 * min_leaf_size:
        return base

    best_predicate: tuple[str, Callable[[dict[str, Any]], bool]] | None = None
    best_partitions: tuple[list[dict[str, Any]], list[dict[str, Any]]] | None = None
    best_candidate: dict[str, Any] | None = None
    best_score = base_score
    for name, fn in predicates:
        true_rows = [row for row in decisions if fn(row)]
        false_rows = [row for row in decisions if not fn(row)]
        if len(true_rows) < min_leaf_size or len(false_rows) < min_leaf_size:
            continue
        candidate = {
            "type": "node",
            "predicate": name,
            "true": leaf(best_leaf_objective(gate22, true_rows)),
            "false": leaf(best_leaf_objective(gate22, false_rows)),
        }
        score = evaluate_tree(gate22, candidate, decisions, predicate_map)
        if (
            score_key(score),
            -tree_size(candidate),
            name,
        ) > (
            score_key(best_score),
            -tree_size(best_candidate)
            if best_candidate is not None
            else -tree_size(base),
            best_candidate["predicate"]
            if best_candidate is not None and best_candidate["type"] == "node"
            else "",
        ):
            best_predicate = (name, fn)
            best_partitions = (true_rows, false_rows)
            best_candidate = candidate
            best_score = score
    if (
        best_predicate is None
        or best_partitions is None
        or best_candidate is None
        or score_key(best_score) <= score_key(base_score)
    ):
        return base
    name, _fn = best_predicate
    true_rows, false_rows = best_partitions
    return {
        "type": "node",
        "predicate": name,
        "true": build_tree(
            gate22,
            true_rows,
            predicates,
            max_depth - 1,
            min_leaf_size,
        ),
        "false": build_tree(
            gate22,
            false_rows,
            predicates,
            max_depth - 1,
            min_leaf_size,
        ),
    }


def train_grid(
    gate22,
    decisions: list[dict[str, Any]],
    predicates: list[Predicate],
) -> list[dict[str, Any]]:
    predicate_map = dict(predicates)
    rows = []
    for max_depth in MAX_DEPTHS:
        for min_leaf_size in MIN_LEAF_SIZES:
            tree = build_tree(gate22, decisions, predicates, max_depth, min_leaf_size)
            score = evaluate_tree(gate22, tree, decisions, predicate_map)
            rows.append(
                {
                    "max_depth": max_depth,
                    "min_leaf_size": min_leaf_size,
                    "actual_depth": tree_depth(tree),
                    "node_count": tree_size(tree),
                    "tree": tree,
                    "score": score,
                }
            )
    rows.sort(
        key=lambda row: (
            -row["score"]["total_hits"],
            -row["score"]["residual_hits"],
            row["score"]["clean_false_changes"],
            row["node_count"],
            row["max_depth"],
            row["min_leaf_size"],
        )
    )
    return rows


def prequential_rows(
    gate22,
    decisions: list[dict[str, Any]],
    predicates: list[Predicate],
) -> list[dict[str, Any]]:
    predicate_map = dict(predicates)
    rows = []
    for cutoff in PREFIX_CUTOFFS:
        train = [row for row in decisions if row["book"] < cutoff]
        test = [row for row in decisions if row["book"] >= cutoff]
        train_grid_rows = train_grid(gate22, train, predicates)
        selected = train_grid_rows[0]
        test_score = evaluate_tree(gate22, selected["tree"], test, predicate_map)
        test_oracle = train_grid(gate22, test, predicates)[0]
        rows.append(
            {
                "cutoff_book": cutoff,
                "selected_max_depth": selected["max_depth"],
                "selected_min_leaf_size": selected["min_leaf_size"],
                "selected_actual_depth": selected["actual_depth"],
                "selected_node_count": selected["node_count"],
                "train_total_hits": selected["score"]["total_hits"],
                "train_total": selected["score"]["total_total"],
                "train_residual_hits": selected["score"]["residual_hits"],
                "train_residual_total": selected["score"]["residual_total"],
                "train_clean_false_changes": selected["score"]["clean_false_changes"],
                "test_total_hits": test_score["total_hits"],
                "test_total": test_score["total_total"],
                "test_residual_hits": test_score["residual_hits"],
                "test_residual_total": test_score["residual_total"],
                "test_clean_false_changes": test_score["clean_false_changes"],
                "test_residual_miss_books": test_score["residual_miss_books"],
                "oracle_test_total_hits": test_oracle["score"]["total_hits"],
                "oracle_test_residual_hits": test_oracle["score"]["residual_hits"],
                "oracle_test_clean_false_changes": test_oracle["score"]["clean_false_changes"],
                "selected_matches_oracle_total_hits": (
                    test_score["total_hits"] == test_oracle["score"]["total_hits"]
                ),
            }
        )
    return rows


def randomize_stable_labels(
    decisions: list[dict[str, Any]],
    rng: random.Random,
) -> list[dict[str, Any]]:
    out = copy.deepcopy(decisions)
    for decision in out:
        if not decision["branches"]:
            continue
        selected = rng.randrange(len(decision["branches"]))
        for index, branch in enumerate(decision["branches"]):
            branch["is_stable"] = index == selected
    return out


def permutation_control(
    gate22,
    decisions: list[dict[str, Any]],
    predicates: list[Predicate],
    real_best: dict[str, Any],
) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED)
    total_hits: list[int] = []
    residual_hits: list[int] = []
    clean_false_changes: list[int] = []
    node_counts: list[int] = []
    for _ in range(PERMUTATION_CONTROLS):
        permuted = randomize_stable_labels(decisions, rng)
        best = train_grid(gate22, permuted, predicates)[0]
        score = best["score"]
        total_hits.append(score["total_hits"])
        residual_hits.append(score["residual_hits"])
        clean_false_changes.append(score["clean_false_changes"])
        node_counts.append(best["node_count"])
    return {
        "controls": PERMUTATION_CONTROLS,
        "total_hits_min": min(total_hits),
        "total_hits_median": sorted(total_hits)[len(total_hits) // 2],
        "total_hits_max": max(total_hits),
        "residual_hits_max": max(residual_hits),
        "clean_false_changes_min": min(clean_false_changes),
        "node_count_median": sorted(node_counts)[len(node_counts) // 2],
        "p_total_hits_ge_real": (
            sum(1 for value in total_hits if value >= real_best["score"]["total_hits"]) + 1
        )
        / (PERMUTATION_CONTROLS + 1),
        "p_residual_hits_ge_real": (
            sum(
                1
                for value in residual_hits
                if value >= real_best["score"]["residual_hits"]
            )
            + 1
        )
        / (PERMUTATION_CONTROLS + 1),
    }


def compact_tree(tree: dict[str, Any]) -> dict[str, Any]:
    if tree["type"] == "leaf":
        return {"leaf": tree["objective"]}
    return {
        "if": tree["predicate"],
        "then": compact_tree(tree["true"]),
        "else": compact_tree(tree["false"]),
    }


def make_result() -> dict[str, Any]:
    branch_continuation = load_json(BRANCH_CONTINUATION)
    assert_boundary("residual_branch_continuation_audit", branch_continuation)
    if branch_continuation["summary"]["promotes_branch_continuation_rule"]:
        raise RuntimeError("gate27 expects gate22 to be rejected")

    gate22 = load_module("branch_continuation_for_gate27", BRANCH_CONTINUATION_SCRIPT)
    decisions = gate22.collect_decisions()["decisions"]
    annotate_objective_indices(gate22, decisions)
    predicates = feature_predicates(gate22)
    residual_decisions = [
        row for row in decisions if row["kind"] == "residual_first_drift"
    ]
    clean_decisions = [row for row in decisions if row["kind"] == "clean_control"]
    baseline_score = score_objective(gate22, decisions, "active_branch")
    full_grid = train_grid(gate22, decisions, predicates)
    best = full_grid[0]
    preq = prequential_rows(gate22, decisions, predicates)
    controls = permutation_control(gate22, decisions, predicates, best)
    promotes = (
        best["score"]["residual_hits"] == len(residual_decisions)
        and best["score"]["clean_false_changes"] == 0
        and all(row["test_clean_false_changes"] == 0 for row in preq)
        and all(row["test_residual_hits"] == row["test_residual_total"] for row in preq)
        and controls["p_total_hits_ge_real"] <= 0.05
    )
    classification = (
        "observable_decision_tree_policy_promoted"
        if promotes
        else "observable_decision_tree_policy_rejected"
    )
    return {
        "schema": "observable_decision_tree_policy_audit.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "branch_continuation_audit": rel(BRANCH_CONTINUATION),
            "branch_continuation_script": rel(BRANCH_CONTINUATION_SCRIPT),
        },
        "scope": {
            "analysis_only": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "target_text_required": True,
            "stable_projection_used_as_training_label": True,
            "stable_projection_used_as_feature": False,
            "source_free_digit_generator_emitted": False,
            "promotes_parser_rule": promotes,
        },
        "summary": {
            "decision_count": len(decisions),
            "residual_decision_count": len(residual_decisions),
            "clean_control_count": len(clean_decisions),
            "predicate_count": len(predicates),
            "tree_grid_size": len(full_grid),
            "active_baseline_total_hits": baseline_score["total_hits"],
            "active_baseline_residual_hits": baseline_score["residual_hits"],
            "active_baseline_clean_false_changes": baseline_score[
                "clean_false_changes"
            ],
            "best_total_hits": best["score"]["total_hits"],
            "best_residual_hits": best["score"]["residual_hits"],
            "best_clean_false_changes": best["score"]["clean_false_changes"],
            "best_depth": best["actual_depth"],
            "best_node_count": best["node_count"],
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
            "promotes_observable_tree_policy": promotes,
            "interpretation": (
                "Gate 27 allows a small observable decision tree to choose among "
                "non-oracle branch-continuation objectives. This is a stronger "
                "finite-state parser test than single predicates or flat context "
                "tables, but it still trains only on stable-projection labels."
            ),
        },
        "best_tree": {
            "max_depth": best["max_depth"],
            "min_leaf_size": best["min_leaf_size"],
            "actual_depth": best["actual_depth"],
            "node_count": best["node_count"],
            "tree": compact_tree(best["tree"]),
            "score": best["score"],
        },
        "top_grid_rows": [
            {
                "max_depth": row["max_depth"],
                "min_leaf_size": row["min_leaf_size"],
                "actual_depth": row["actual_depth"],
                "node_count": row["node_count"],
                "total_hits": row["score"]["total_hits"],
                "residual_hits": row["score"]["residual_hits"],
                "clean_false_changes": row["score"]["clean_false_changes"],
                "objective_counts": row["score"]["objective_counts"],
                "residual_miss_books": row["score"]["residual_miss_books"],
            }
            for row in full_grid[:12]
        ],
        "prequential_rows": preq,
        "permutation_control": controls,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": classification,
            "source_length_dependency_status": "observable_decision_tree_policy_rejected"
            if not promotes
            else "observable_decision_tree_policy_promoted",
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
    grid_rows = [
        [
            row["max_depth"],
            row["min_leaf_size"],
            row["actual_depth"],
            row["node_count"],
            f"{row['total_hits']}/234",
            f"{row['residual_hits']}/10",
            row["clean_false_changes"],
            row["residual_miss_books"],
        ]
        for row in result["top_grid_rows"][:8]
    ]
    preq_rows = [
        [
            row["cutoff_book"],
            row["selected_max_depth"],
            row["selected_min_leaf_size"],
            f"{row['train_total_hits']}/{row['train_total']}",
            f"{row['test_total_hits']}/{row['test_total']}",
            f"{row['test_residual_hits']}/{row['test_residual_total']}",
            row["test_clean_false_changes"],
            row["selected_matches_oracle_total_hits"],
        ]
        for row in result["prequential_rows"]
    ]
    c = result["permutation_control"]
    body = f"""# Observable Decision Tree Policy Audit

Classification: `{result['classification']}`
Translation delta: `NONE`

## Purpose

Gate 27 tests whether the post-repair residual branch choice can be generated
by a small observable decision tree rather than by a flat context table, single
feature flag, or learned linear ranker. Each leaf chooses one non-oracle
branch-continuation objective. Stable projection labels are used for training
and evaluation only, not as tree features.

## Summary

- Decisions: `{s['decision_count']}`.
- Residual first-drift decisions: `{s['residual_decision_count']}`.
- Clean controls: `{s['clean_control_count']}`.
- Observable predicates: `{s['predicate_count']}`.
- Tree grid size: `{s['tree_grid_size']}`.
- Active baseline: `{s['active_baseline_total_hits']}/234`, residual
  `{s['active_baseline_residual_hits']}/10`, clean false changes
  `{s['active_baseline_clean_false_changes']}`.
- Best tree: `{s['best_total_hits']}/234`, residual
  `{s['best_residual_hits']}/10`, clean false changes
  `{s['best_clean_false_changes']}`, depth `{s['best_depth']}`, nodes
  `{s['best_node_count']}`.

## Full-Fit Grid

{md_table(grid_rows, ["max depth", "min leaf", "actual depth", "nodes", "total hits", "residual hits", "clean false changes", "residual misses"])}

Best tree:

```json
{json.dumps(result['best_tree']['tree'], indent=2, sort_keys=True)}
```

## Prefix/Holdout

{md_table(preq_rows, ["cutoff", "depth", "min leaf", "train hits", "test hits", "test residual hits", "test clean false changes", "matches oracle"])}

## Permutation Control

- Controls: `{c['controls']}`.
- Total-hit range under random stable-branch labels:
  `{c['total_hits_min']}..{c['total_hits_max']}`.
- Median total hits under controls: `{c['total_hits_median']}`.
- Max residual hits under controls: `{c['residual_hits_max']}`.
- Minimum clean false changes under controls: `{c['clean_false_changes_min']}`.
- `p(total_hits >= real_best)`: `{c['p_total_hits_ge_real']:.6f}`.
- `p(residual_hits >= real_best)`: `{c['p_residual_hits_ge_real']:.6f}`.

## Decision

- Promotes observable decision-tree parser policy:
  `{s['promotes_observable_tree_policy']}`.
- Prequential zero-clean-false-change cells:
  `{s['prequential_zero_clean_false_change_cells']}/{s['prequential_cells']}`.
- Prequential cover-all-test-residual cells:
  `{s['prequential_cover_all_test_residual_cells']}/{s['prequential_cells']}`.
- Gate 27 is stronger than the previous single-feature/context checks, but it
  still fails the promotion gate if residual recovery requires false clean-control
  changes or does not survive prefix/holdout selection.
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
