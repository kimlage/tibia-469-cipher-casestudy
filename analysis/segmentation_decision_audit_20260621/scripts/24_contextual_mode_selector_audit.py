from __future__ import annotations

import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

BRANCH_CONTINUATION_SCRIPT = HERE / "scripts" / "22_residual_branch_continuation_audit.py"
BRANCH_RANKER = TEST_RESULTS / "23_branch_ranker_prequential_audit.json"

OUT_STEM = "24_contextual_mode_selector_audit"
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]


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


def op_equals(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return (
        left["type"] == right["type"]
        and int(left["target_start"]) == int(right["target_start"])
        and int(left["length"]) == int(right["length"])
        and left.get("source") == right.get("source")
    )


def branch_count_bucket(decision: dict[str, Any]) -> str:
    count = len(decision["branches"])
    if count <= 10:
        return "few"
    if count <= 20:
        return "mid"
    return "many"


def length_bucket(length: int) -> str:
    if length <= 1:
        return "len1"
    if length <= 5:
        return "len2_5"
    if length <= 8:
        return "len6_8"
    if length <= 20:
        return "len9_20"
    return "len_gt20"


ContextFn = tuple[str, Callable[[dict[str, Any]], str]]


def context_functions() -> list[ContextFn]:
    return [
        ("global", lambda row: "all"),
        ("start_internal", lambda row: "start" if row["target_start"] == 0 else "internal"),
        ("op_index", lambda row: "first_op" if row["stable_index"] == 0 else "later_op"),
        (
            "active_type",
            lambda row: row["active_op"]["type"],
        ),
        (
            "active_type_len",
            lambda row: f"{row['active_op']['type']}:{length_bucket(int(row['active_op']['length']))}",
        ),
        (
            "baseline_to_active",
            lambda row: f"{row['baseline_op']['type']}->{row['active_op']['type']}",
        ),
        (
            "branch_count",
            branch_count_bucket,
        ),
        (
            "start_x_active_type",
            lambda row: (
                ("start" if row["target_start"] == 0 else "internal")
                + ":"
                + row["active_op"]["type"]
            ),
        ),
        (
            "index_x_active_len",
            lambda row: (
                ("first_op" if row["stable_index"] == 0 else "later_op")
                + ":"
                + length_bucket(int(row["active_op"]["length"]))
            ),
        ),
        (
            "context_combo",
            lambda row: ":".join(
                [
                    "start" if row["target_start"] == 0 else "internal",
                    "first_op" if row["stable_index"] == 0 else "later_op",
                    row["active_op"]["type"],
                    length_bucket(int(row["active_op"]["length"])),
                    branch_count_bucket(row),
                ]
            ),
        ),
    ]


def choose_active(decision: dict[str, Any]) -> dict[str, Any]:
    for branch in decision["branches"]:
        if branch["is_active"]:
            return branch
    raise RuntimeError({"type": "missing_active_branch", "book": decision["book"]})


def objective_names(gate22) -> list[str]:
    return ["active_branch"] + [
        name for name in gate22.OBJECTIVES if not name.startswith("oracle_")
    ]


def choose_branch(gate22, decision: dict[str, Any], objective: str) -> dict[str, Any]:
    if objective == "active_branch":
        return choose_active(decision)
    chosen = gate22.choose_branch(decision, objective)
    if chosen is None:
        raise RuntimeError({"type": "missing_branch", "book": decision["book"]})
    return chosen


def score_decisions(gate22, decisions: list[dict[str, Any]], objective: str) -> dict[str, Any]:
    rows = []
    for decision in decisions:
        chosen = choose_branch(gate22, decision, objective)
        rows.append(
            {
                "book": decision["book"],
                "kind": decision["kind"],
                "chosen_is_stable": chosen["is_stable"],
            }
        )
    residual = [row for row in rows if row["kind"] == "residual_first_drift"]
    clean = [row for row in rows if row["kind"] == "clean_control"]
    return {
        "objective": objective,
        "total_hits": sum(1 for row in rows if row["chosen_is_stable"]),
        "total_total": len(rows),
        "residual_hits": sum(1 for row in residual if row["chosen_is_stable"]),
        "residual_total": len(residual),
        "clean_false_changes": sum(1 for row in clean if not row["chosen_is_stable"]),
        "clean_total": len(clean),
    }


def best_objective(gate22, decisions: list[dict[str, Any]]) -> str:
    scores = [
        score_decisions(gate22, decisions, objective)
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


def train_selector(
    gate22,
    decisions: list[dict[str, Any]],
    context_name: str,
    context_fn: Callable[[dict[str, Any]], str],
) -> dict[str, Any]:
    fallback = best_objective(gate22, decisions)
    contexts: dict[str, list[dict[str, Any]]] = {}
    for decision in decisions:
        contexts.setdefault(context_fn(decision), []).append(decision)
    mapping = {
        key: best_objective(gate22, rows)
        for key, rows in sorted(contexts.items())
    }
    return {
        "context_name": context_name,
        "fallback": fallback,
        "mapping": mapping,
    }


def evaluate_selector(
    gate22,
    decisions: list[dict[str, Any]],
    selector: dict[str, Any],
    context_fn: Callable[[dict[str, Any]], str],
) -> dict[str, Any]:
    rows = []
    objective_counts: Counter[str] = Counter()
    for decision in decisions:
        context_value = context_fn(decision)
        objective = selector["mapping"].get(context_value, selector["fallback"])
        objective_counts[objective] += 1
        chosen = choose_branch(gate22, decision, objective)
        rows.append(
            {
                "book": decision["book"],
                "kind": decision["kind"],
                "chosen_is_stable": chosen["is_stable"],
                "objective": objective,
                "context_value": context_value,
            }
        )
    residual = [row for row in rows if row["kind"] == "residual_first_drift"]
    clean = [row for row in rows if row["kind"] == "clean_control"]
    return {
        "context_name": selector["context_name"],
        "total_hits": sum(1 for row in rows if row["chosen_is_stable"]),
        "total_total": len(rows),
        "residual_hits": sum(1 for row in residual if row["chosen_is_stable"]),
        "residual_total": len(residual),
        "clean_false_changes": sum(1 for row in clean if not row["chosen_is_stable"]),
        "clean_total": len(clean),
        "objective_counts": dict(sorted(objective_counts.items())),
        "residual_miss_books": [
            row["book"] for row in residual if not row["chosen_is_stable"]
        ],
        "unseen_context_count": sum(
            1
            for decision in decisions
            if context_fn(decision) not in selector["mapping"]
        ),
    }


def selector_score_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        row["total_hits"],
        row["residual_hits"],
        -row["clean_false_changes"],
        -row["unseen_context_count"],
        row["context_name"],
    )


def prequential_rows(gate22, decisions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    contexts = context_functions()
    for cutoff in PREFIX_CUTOFFS:
        train = [row for row in decisions if row["book"] < cutoff]
        test = [row for row in decisions if row["book"] >= cutoff]
        trained = [
            (
                context_name,
                context_fn,
                train_selector(gate22, train, context_name, context_fn),
            )
            for context_name, context_fn in contexts
        ]
        train_scores = [
            evaluate_selector(gate22, train, selector, context_fn)
            for context_name, context_fn, selector in trained
        ]
        selected_train = max(train_scores, key=selector_score_key)
        selected_context_fn = dict(contexts)[selected_train["context_name"]]
        selected_selector = next(
            selector
            for context_name, context_fn, selector in trained
            if context_name == selected_train["context_name"]
        )
        test_score = evaluate_selector(
            gate22, test, selected_selector, selected_context_fn
        )
        oracle_scores = [
            evaluate_selector(gate22, test, selector, context_fn)
            for context_name, context_fn, selector in trained
        ]
        oracle = max(oracle_scores, key=selector_score_key)
        rows.append(
            {
                "cutoff_book": cutoff,
                "selected_context": selected_train["context_name"],
                "train_total_hits": selected_train["total_hits"],
                "train_total": selected_train["total_total"],
                "train_residual_hits": selected_train["residual_hits"],
                "train_residual_total": selected_train["residual_total"],
                "train_clean_false_changes": selected_train["clean_false_changes"],
                "test_total_hits": test_score["total_hits"],
                "test_total": test_score["total_total"],
                "test_residual_hits": test_score["residual_hits"],
                "test_residual_total": test_score["residual_total"],
                "test_clean_false_changes": test_score["clean_false_changes"],
                "test_unseen_context_count": test_score["unseen_context_count"],
                "oracle_context": oracle["context_name"],
                "oracle_test_total_hits": oracle["total_hits"],
                "oracle_test_residual_hits": oracle["residual_hits"],
                "selected_matches_oracle_total_hits": (
                    test_score["total_hits"] == oracle["total_hits"]
                ),
            }
        )
    return rows


def make_result() -> dict[str, Any]:
    ranker = load_json(BRANCH_RANKER)
    assert_boundary("branch_ranker_prequential_audit", ranker)
    if ranker["summary"]["promotes_branch_ranker"]:
        raise RuntimeError("gate24 expects gate23 to be rejected")

    gate22 = load_module("branch_continuation_for_gate24", BRANCH_CONTINUATION_SCRIPT)
    decisions = gate22.collect_decisions()["decisions"]
    contexts = context_functions()
    full_rows = []
    for context_name, context_fn in contexts:
        selector = train_selector(gate22, decisions, context_name, context_fn)
        score = evaluate_selector(gate22, decisions, selector, context_fn)
        score["context_value_count"] = len(selector["mapping"])
        score["mapping"] = selector["mapping"]
        full_rows.append(score)
    full_rows.sort(key=selector_score_key, reverse=True)
    baseline = score_decisions(gate22, decisions, "active_branch")
    preq = prequential_rows(gate22, decisions)
    best = full_rows[0]
    promotes = (
        best["residual_hits"] == best["residual_total"]
        and best["clean_false_changes"] == 0
        and all(row["test_clean_false_changes"] == 0 for row in preq)
        and all(row["test_residual_hits"] == row["test_residual_total"] for row in preq)
    )
    classification = (
        "contextual_mode_selector_promoted"
        if promotes
        else "contextual_mode_selector_rejected"
    )
    return {
        "schema": "contextual_mode_selector_audit.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "branch_ranker_prequential_audit": rel(BRANCH_RANKER),
        },
        "scope": {
            "analysis_only": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "target_text_required": True,
            "stable_projection_used_as_training_label": True,
            "declared_literal_windows_granted": False,
            "source_free_digit_generator_emitted": False,
            "promotes_parser_rule": promotes,
        },
        "summary": {
            "decision_count": len(decisions),
            "residual_decision_count": sum(
                1 for row in decisions if row["kind"] == "residual_first_drift"
            ),
            "clean_control_count": sum(
                1 for row in decisions if row["kind"] == "clean_control"
            ),
            "context_family_count": len(contexts),
            "best_context_family": best["context_name"],
            "best_full_fit_total_hits": best["total_hits"],
            "best_full_fit_residual_hits": best["residual_hits"],
            "best_full_fit_clean_false_changes": best["clean_false_changes"],
            "active_baseline_total_hits": baseline["total_hits"],
            "active_baseline_residual_hits": baseline["residual_hits"],
            "active_baseline_clean_false_changes": baseline["clean_false_changes"],
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
            "promotes_contextual_mode_selector": promotes,
            "interpretation": (
                "Gate 24 tests a finite observable state table: each context "
                "family learns which non-oracle branch objective to use from "
                "prefix stable labels, then is evaluated on suffix books."
            ),
        },
        "active_baseline_score": baseline,
        "full_fit_scoreboard": [
            {
                "context_name": row["context_name"],
                "context_value_count": row["context_value_count"],
                "total_hits": row["total_hits"],
                "residual_hits": row["residual_hits"],
                "clean_false_changes": row["clean_false_changes"],
                "objective_counts": row["objective_counts"],
                "residual_miss_books": row["residual_miss_books"],
            }
            for row in full_rows
        ],
        "best_mapping": best["mapping"],
        "prequential_rows": preq,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": classification,
            "source_length_dependency_status": "contextual_mode_selector_rejected"
            if not promotes
            else "contextual_mode_selector_promoted",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / f"{OUT_STEM}.json"
    md_path = TEST_RESULTS / f"{OUT_STEM}.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    lines = [
        "# Contextual Mode Selector Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 24 tests whether the missing path-state choice is a small",
        "finite mode table: observable context chooses one non-oracle branch",
        "objective. The table is learned from prefix/stable labels and",
        "evaluated on future books.",
        "",
        "## Full-Fit Scoreboard",
        "",
        f"- Decisions: `{s['decision_count']}`.",
        f"- Context families: `{s['context_family_count']}`.",
        "",
        "| Context family | Contexts | Total hits | Residual hits | Clean false changes |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in result["full_fit_scoreboard"]:
        lines.append(
            f"| `{row['context_name']}` | `{row['context_value_count']}` | "
            f"`{row['total_hits']}/{s['decision_count']}` | "
            f"`{row['residual_hits']}/{s['residual_decision_count']}` | "
            f"`{row['clean_false_changes']}` |"
        )
    lines.extend(
        [
            "",
            "## Prefix/Holdout",
            "",
            "| Cutoff | Selected context | Test hits | Test residual hits | Test clean false changes | Unseen contexts |",
            "|---:|---|---:|---:|---:|---:|",
        ]
    )
    for row in result["prequential_rows"]:
        lines.append(
            f"| `{row['cutoff_book']}` | `{row['selected_context']}` | "
            f"`{row['test_total_hits']}/{row['test_total']}` | "
            f"`{row['test_residual_hits']}/{row['test_residual_total']}` | "
            f"`{row['test_clean_false_changes']}` | "
            f"`{row['test_unseen_context_count']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Promotes contextual mode selector: `{s['promotes_contextual_mode_selector']}`.",
            f"- Active baseline total/residual hits: `{s['active_baseline_total_hits']}/{s['decision_count']}` and `{s['active_baseline_residual_hits']}/{s['residual_decision_count']}`.",
            f"- Best full-fit context: `{s['best_context_family']}`.",
            f"- Best full-fit residual hits: `{s['best_full_fit_residual_hits']}/{s['residual_decision_count']}`.",
            f"- Best full-fit clean false changes: `{s['best_full_fit_clean_false_changes']}`.",
            f"- Prequential zero-clean-false-change cells: `{s['prequential_zero_clean_false_change_cells']}/{s['prequential_cells']}`.",
            f"- Prequential cover-all-test-residual cells: `{s['prequential_cover_all_test_residual_cells']}/{s['prequential_cells']}`.",
            f"- {s['interpretation']}",
            "- The finite context selector does not become a generative parser.",
            "- Compression bound is unchanged.",
            "- Row0 remains exogenous and unchanged.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
            "",
        ]
    )
    md_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    result = make_result()
    write_result(result)
    print(json.dumps(result["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
