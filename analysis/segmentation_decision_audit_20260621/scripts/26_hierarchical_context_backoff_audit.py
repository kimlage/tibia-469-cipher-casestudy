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
CONTEXTUAL_MODE_SCRIPT = HERE / "scripts" / "24_contextual_mode_selector_audit.py"
CONTEXTUAL_STABILITY = TEST_RESULTS / "25_contextual_mode_stability_audit.json"

OUT_STEM = "26_hierarchical_context_backoff_audit"
SUPPORT_THRESHOLDS = [1, 2, 3, 5, 10]
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


def context_by_name(gate24) -> dict[str, Callable[[dict[str, Any]], str]]:
    return {name: fn for name, fn in gate24.context_functions()}


def hierarchy_families() -> list[dict[str, Any]]:
    return [
        {
            "label": "coarse_to_combo",
            "levels": ["global", "start_internal", "op_index", "active_type_len", "context_combo"],
        },
        {
            "label": "start_active_to_combo",
            "levels": ["global", "start_internal", "start_x_active_type", "active_type_len", "context_combo"],
        },
        {
            "label": "length_to_combo",
            "levels": ["global", "active_type", "active_type_len", "index_x_active_len", "context_combo"],
        },
        {
            "label": "branch_to_combo",
            "levels": ["global", "branch_count", "active_type_len", "context_combo"],
        },
    ]


def objective_names(gate22) -> list[str]:
    return ["active_branch"] + [
        name for name in gate22.OBJECTIVES if not name.startswith("oracle_")
    ]


def choose_branch(gate24, gate22, decision: dict[str, Any], objective: str) -> dict[str, Any]:
    if objective == "active_branch":
        return gate24.choose_active(decision)
    chosen = gate22.choose_branch(decision, objective)
    if chosen is None:
        raise RuntimeError({"type": "missing_branch", "book": decision["book"]})
    return chosen


def score_objective(gate24, gate22, decisions: list[dict[str, Any]], objective: str) -> dict[str, Any]:
    rows = []
    for decision in decisions:
        chosen = choose_branch(gate24, gate22, decision, objective)
        rows.append(
            {
                "kind": decision["kind"],
                "chosen_is_stable": chosen["is_stable"],
            }
        )
    residual = [row for row in rows if row["kind"] == "residual_first_drift"]
    clean = [row for row in rows if row["kind"] == "clean_control"]
    return {
        "objective": objective,
        "total_hits": sum(1 for row in rows if row["chosen_is_stable"]),
        "residual_hits": sum(1 for row in residual if row["chosen_is_stable"]),
        "clean_false_changes": sum(1 for row in clean if not row["chosen_is_stable"]),
    }


def best_objective(gate24, gate22, decisions: list[dict[str, Any]]) -> str:
    scores = [
        score_objective(gate24, gate22, decisions, objective)
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


def train_backoff(
    gate24,
    gate22,
    decisions: list[dict[str, Any]],
    contexts: dict[str, Callable[[dict[str, Any]], str]],
    family: dict[str, Any],
    min_support: int,
) -> dict[str, Any]:
    fallback = best_objective(gate24, gate22, decisions)
    levels = []
    for level_name in family["levels"]:
        fn = contexts[level_name]
        buckets: dict[str, list[dict[str, Any]]] = {}
        for decision in decisions:
            buckets.setdefault(fn(decision), []).append(decision)
        level_map = {
            value: {
                "objective": best_objective(gate24, gate22, rows),
                "support": len(rows),
            }
            for value, rows in sorted(buckets.items())
        }
        levels.append({"name": level_name, "mapping": level_map})
    return {
        "family": family["label"],
        "min_support": min_support,
        "levels": levels,
        "fallback": fallback,
    }


def select_objective(
    selector: dict[str, Any],
    contexts: dict[str, Callable[[dict[str, Any]], str]],
    decision: dict[str, Any],
) -> tuple[str, str]:
    for level in reversed(selector["levels"]):
        value = contexts[level["name"]](decision)
        row = level["mapping"].get(value)
        if row is not None and row["support"] >= selector["min_support"]:
            return row["objective"], f"{level['name']}={value}"
    return selector["fallback"], "fallback"


def evaluate_selector(
    gate24,
    gate22,
    decisions: list[dict[str, Any]],
    contexts: dict[str, Callable[[dict[str, Any]], str]],
    selector: dict[str, Any],
) -> dict[str, Any]:
    rows = []
    source_counts: Counter[str] = Counter()
    objective_counts: Counter[str] = Counter()
    for decision in decisions:
        objective, source = select_objective(selector, contexts, decision)
        source_counts[source.split("=")[0]] += 1
        objective_counts[objective] += 1
        chosen = choose_branch(gate24, gate22, decision, objective)
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
        "family": selector["family"],
        "min_support": selector["min_support"],
        "total_hits": sum(1 for row in rows if row["chosen_is_stable"]),
        "total_total": len(rows),
        "residual_hits": sum(1 for row in residual if row["chosen_is_stable"]),
        "residual_total": len(residual),
        "clean_false_changes": sum(1 for row in clean if not row["chosen_is_stable"]),
        "clean_total": len(clean),
        "residual_miss_books": [
            row["book"] for row in residual if not row["chosen_is_stable"]
        ],
        "source_counts": dict(sorted(source_counts.items())),
        "objective_counts": dict(sorted(objective_counts.items())),
    }


def score_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        row["total_hits"],
        row["residual_hits"],
        -row["clean_false_changes"],
        -row["min_support"],
        row["family"],
    )


def prequential_rows(
    gate24,
    gate22,
    decisions: list[dict[str, Any]],
    contexts: dict[str, Callable[[dict[str, Any]], str]],
) -> list[dict[str, Any]]:
    rows = []
    for cutoff in PREFIX_CUTOFFS:
        train = [row for row in decisions if row["book"] < cutoff]
        test = [row for row in decisions if row["book"] >= cutoff]
        candidates = []
        for family in hierarchy_families():
            for min_support in SUPPORT_THRESHOLDS:
                selector = train_backoff(
                    gate24, gate22, train, contexts, family, min_support
                )
                train_score = evaluate_selector(gate24, gate22, train, contexts, selector)
                test_score = evaluate_selector(gate24, gate22, test, contexts, selector)
                candidates.append(
                    {
                        "selector": selector,
                        "train_score": train_score,
                        "test_score": test_score,
                    }
                )
        selected = max(candidates, key=lambda row: score_key(row["train_score"]))
        oracle = max(candidates, key=lambda row: score_key(row["test_score"]))
        train_score = selected["train_score"]
        test_score = selected["test_score"]
        rows.append(
            {
                "cutoff_book": cutoff,
                "selected_family": train_score["family"],
                "selected_min_support": train_score["min_support"],
                "train_total_hits": train_score["total_hits"],
                "train_total": train_score["total_total"],
                "train_residual_hits": train_score["residual_hits"],
                "train_residual_total": train_score["residual_total"],
                "train_clean_false_changes": train_score["clean_false_changes"],
                "test_total_hits": test_score["total_hits"],
                "test_total": test_score["total_total"],
                "test_residual_hits": test_score["residual_hits"],
                "test_residual_total": test_score["residual_total"],
                "test_clean_false_changes": test_score["clean_false_changes"],
                "oracle_family": oracle["test_score"]["family"],
                "oracle_min_support": oracle["test_score"]["min_support"],
                "oracle_test_total_hits": oracle["test_score"]["total_hits"],
                "oracle_test_residual_hits": oracle["test_score"]["residual_hits"],
                "selected_matches_oracle_total_hits": (
                    test_score["total_hits"] == oracle["test_score"]["total_hits"]
                ),
            }
        )
    return rows


def make_result() -> dict[str, Any]:
    stability = load_json(CONTEXTUAL_STABILITY)
    assert_boundary("contextual_mode_stability_audit", stability)
    if stability["summary"]["promotes_contextual_mode_stability"]:
        raise RuntimeError("gate26 expects gate25 to be rejected")

    gate22 = load_module("branch_continuation_for_gate26", BRANCH_CONTINUATION_SCRIPT)
    gate24 = load_module("contextual_mode_for_gate26", CONTEXTUAL_MODE_SCRIPT)
    decisions = gate22.collect_decisions()["decisions"]
    contexts = context_by_name(gate24)

    full_rows = []
    for family in hierarchy_families():
        for min_support in SUPPORT_THRESHOLDS:
            selector = train_backoff(gate24, gate22, decisions, contexts, family, min_support)
            score = evaluate_selector(gate24, gate22, decisions, contexts, selector)
            full_rows.append(score)
    full_rows.sort(key=score_key, reverse=True)
    best = full_rows[0]
    preq = prequential_rows(gate24, gate22, decisions, contexts)
    promotes = (
        best["residual_hits"] == best["residual_total"]
        and best["clean_false_changes"] == 0
        and all(row["test_clean_false_changes"] == 0 for row in preq)
        and all(row["test_residual_hits"] == row["test_residual_total"] for row in preq)
    )
    classification = (
        "hierarchical_context_backoff_promoted"
        if promotes
        else "hierarchical_context_backoff_rejected"
    )
    return {
        "schema": "hierarchical_context_backoff_audit.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "contextual_mode_stability_audit": rel(CONTEXTUAL_STABILITY),
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
            "family_count": len(hierarchy_families()),
            "support_threshold_count": len(SUPPORT_THRESHOLDS),
            "best_family": best["family"],
            "best_min_support": best["min_support"],
            "best_full_fit_total_hits": best["total_hits"],
            "best_full_fit_residual_hits": best["residual_hits"],
            "best_full_fit_clean_false_changes": best["clean_false_changes"],
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
            "promotes_hierarchical_context_backoff": promotes,
            "interpretation": (
                "Gate 26 tests whether gate25 failed only because context_combo "
                "was too sparse. It trains a hierarchy of observable contexts and "
                "backs off to coarser contexts when support is low."
            ),
        },
        "full_fit_scoreboard": full_rows,
        "prequential_rows": preq,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": classification,
            "source_length_dependency_status": "hierarchical_context_backoff_rejected"
            if not promotes
            else "hierarchical_context_backoff_promoted",
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
        "# Hierarchical Context Backoff Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 26 tests whether the gate-25 instability is only a sparsity",
        "problem. It trains observable context hierarchies and backs off to",
        "coarser contexts when support is low.",
        "",
        "## Full-Fit Scoreboard",
        "",
        f"- Families tested: `{s['family_count']}`.",
        f"- Support thresholds: `{s['support_threshold_count']}`.",
        "",
        "| Family | Min support | Total hits | Residual hits | Clean false changes |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in result["full_fit_scoreboard"][:12]:
        lines.append(
            f"| `{row['family']}` | `{row['min_support']}` | "
            f"`{row['total_hits']}/{row['total_total']}` | "
            f"`{row['residual_hits']}/{row['residual_total']}` | "
            f"`{row['clean_false_changes']}` |"
        )
    lines.extend(
        [
            "",
            "## Prefix/Holdout",
            "",
            "| Cutoff | Family | Support | Test hits | Test residual hits | Test clean false changes |",
            "|---:|---|---:|---:|---:|---:|",
        ]
    )
    for row in result["prequential_rows"]:
        lines.append(
            f"| `{row['cutoff_book']}` | `{row['selected_family']}` | "
            f"`{row['selected_min_support']}` | "
            f"`{row['test_total_hits']}/{row['test_total']}` | "
            f"`{row['test_residual_hits']}/{row['test_residual_total']}` | "
            f"`{row['test_clean_false_changes']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Promotes hierarchical context backoff: `{s['promotes_hierarchical_context_backoff']}`.",
            f"- Best full-fit family/support: `{s['best_family']}` / `{s['best_min_support']}`.",
            f"- Best full-fit residual hits: `{s['best_full_fit_residual_hits']}/{s['residual_decision_count']}`.",
            f"- Best full-fit clean false changes: `{s['best_full_fit_clean_false_changes']}`.",
            f"- Prequential zero-clean-false-change cells: `{s['prequential_zero_clean_false_change_cells']}/{s['prequential_cells']}`.",
            f"- Prequential cover-all-test-residual cells: `{s['prequential_cover_all_test_residual_cells']}/{s['prequential_cells']}`.",
            f"- {s['interpretation']}",
            "- Hierarchical backoff does not turn the contextual clue into a stable parser rule.",
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
