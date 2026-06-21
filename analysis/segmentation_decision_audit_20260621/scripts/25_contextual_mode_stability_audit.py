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
CONTEXTUAL_MODE = TEST_RESULTS / "24_contextual_mode_selector_audit.json"

OUT_STEM = "25_contextual_mode_stability_audit"
ACTIVE_CONTEXT = "context_combo"
SUPPORT_THRESHOLDS = [1, 2, 3, 5, 10]


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


def get_context_fn(gate24) -> Callable[[dict[str, Any]], str]:
    by_name = {name: fn for name, fn in gate24.context_functions()}
    return by_name[ACTIVE_CONTEXT]


def pruned_selector(
    gate24,
    gate22,
    decisions: list[dict[str, Any]],
    context_fn: Callable[[dict[str, Any]], str],
    min_support: int,
) -> dict[str, Any]:
    selector = gate24.train_selector(gate22, decisions, ACTIVE_CONTEXT, context_fn)
    contexts: Counter[str] = Counter(context_fn(row) for row in decisions)
    selector["mapping"] = {
        key: objective
        for key, objective in selector["mapping"].items()
        if contexts[key] >= min_support
    }
    selector["min_support"] = min_support
    selector["context_supports"] = dict(sorted(contexts.items()))
    return selector


def evaluate_pruned(
    gate24,
    gate22,
    decisions: list[dict[str, Any]],
    context_fn: Callable[[dict[str, Any]], str],
    min_support: int,
) -> dict[str, Any]:
    selector = pruned_selector(gate24, gate22, decisions, context_fn, min_support)
    score = gate24.evaluate_selector(gate22, decisions, selector, context_fn)
    score["min_support"] = min_support
    score["mapped_context_count"] = len(selector["mapping"])
    return score


def selected_branch(gate24, gate22, decision: dict[str, Any], objective: str) -> dict[str, Any]:
    return gate24.choose_branch(gate22, decision, objective)


def residual_stability_rows(
    gate24,
    gate22,
    decisions: list[dict[str, Any]],
    context_fn: Callable[[dict[str, Any]], str],
) -> list[dict[str, Any]]:
    full_selector = gate24.train_selector(gate22, decisions, ACTIVE_CONTEXT, context_fn)
    context_supports = Counter(context_fn(row) for row in decisions)
    context_residual_supports = Counter(
        context_fn(row) for row in decisions if row["kind"] == "residual_first_drift"
    )
    context_clean_supports = Counter(
        context_fn(row) for row in decisions if row["kind"] == "clean_control"
    )
    rows = []
    for decision in [row for row in decisions if row["kind"] == "residual_first_drift"]:
        context_value = context_fn(decision)
        full_objective = full_selector["mapping"].get(
            context_value, full_selector["fallback"]
        )
        full_branch = selected_branch(gate24, gate22, decision, full_objective)

        leave_book_train = [
            row for row in decisions if int(row["book"]) != int(decision["book"])
        ]
        leave_book_selector = gate24.train_selector(
            gate22, leave_book_train, ACTIVE_CONTEXT, context_fn
        )
        leave_book_objective = leave_book_selector["mapping"].get(
            context_value, leave_book_selector["fallback"]
        )
        leave_book_branch = selected_branch(
            gate24, gate22, decision, leave_book_objective
        )

        leave_context_train = [
            row for row in decisions if context_fn(row) != context_value
        ]
        leave_context_selector = gate24.train_selector(
            gate22, leave_context_train, ACTIVE_CONTEXT, context_fn
        )
        leave_context_objective = leave_context_selector["mapping"].get(
            context_value, leave_context_selector["fallback"]
        )
        leave_context_branch = selected_branch(
            gate24, gate22, decision, leave_context_objective
        )
        rows.append(
            {
                "book": decision["book"],
                "target_start": decision["target_start"],
                "drift_class": decision["drift_class"],
                "context_value": context_value,
                "context_support": context_supports[context_value],
                "context_residual_support": context_residual_supports[context_value],
                "context_clean_support": context_clean_supports[context_value],
                "full_objective": full_objective,
                "full_hit": full_branch["is_stable"],
                "leave_book_objective": leave_book_objective,
                "leave_book_hit": leave_book_branch["is_stable"],
                "leave_context_objective": leave_context_objective,
                "leave_context_hit": leave_context_branch["is_stable"],
            }
        )
    return rows


def make_result() -> dict[str, Any]:
    contextual_mode = load_json(CONTEXTUAL_MODE)
    assert_boundary("contextual_mode_selector_audit", contextual_mode)
    if contextual_mode["summary"]["promotes_contextual_mode_selector"]:
        raise RuntimeError("gate25 expects gate24 to be rejected")

    gate22 = load_module("branch_continuation_for_gate25", BRANCH_CONTINUATION_SCRIPT)
    gate24 = load_module("contextual_mode_for_gate25", CONTEXTUAL_MODE_SCRIPT)
    decisions = gate22.collect_decisions()["decisions"]
    context_fn = get_context_fn(gate24)
    full_score = evaluate_pruned(gate24, gate22, decisions, context_fn, min_support=1)
    support_scores = [
        evaluate_pruned(gate24, gate22, decisions, context_fn, threshold)
        for threshold in SUPPORT_THRESHOLDS
    ]
    residual_rows = residual_stability_rows(gate24, gate22, decisions, context_fn)
    full_hits = sum(1 for row in residual_rows if row["full_hit"])
    leave_book_hits = sum(1 for row in residual_rows if row["leave_book_hit"])
    leave_context_hits = sum(1 for row in residual_rows if row["leave_context_hit"])
    promoted = (
        full_hits == len(residual_rows)
        and leave_book_hits == len(residual_rows)
        and full_score["clean_false_changes"] == 0
    )
    classification = (
        "contextual_mode_stability_promoted"
        if promoted
        else "contextual_mode_stability_rejected"
    )
    return {
        "schema": "contextual_mode_stability_audit.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "contextual_mode_selector_audit": rel(CONTEXTUAL_MODE),
        },
        "scope": {
            "analysis_only": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "target_text_required": True,
            "stable_projection_used_as_training_label": True,
            "declared_literal_windows_granted": False,
            "source_free_digit_generator_emitted": False,
            "promotes_parser_rule": promoted,
        },
        "summary": {
            "active_context_family": ACTIVE_CONTEXT,
            "decision_count": len(decisions),
            "residual_decision_count": len(residual_rows),
            "full_fit_residual_hits": full_hits,
            "full_fit_clean_false_changes": full_score["clean_false_changes"],
            "leave_one_book_residual_hits": leave_book_hits,
            "leave_context_out_residual_hits": leave_context_hits,
            "support_threshold_count": len(SUPPORT_THRESHOLDS),
            "best_supported_threshold": max(
                support_scores,
                key=lambda row: (
                    row["residual_hits"],
                    -row["clean_false_changes"],
                    row["total_hits"],
                    -row["min_support"],
                ),
            )["min_support"],
            "promotes_contextual_mode_stability": promoted,
            "interpretation": (
                "Gate 25 stress-tests the gate24 context_combo clue by pruning "
                "low-support contexts and by leave-one-book / leave-context-out "
                "retraining. Stable labels are used only to train/evaluate the "
                "mode table."
            ),
        },
        "support_threshold_scoreboard": [
            {
                "min_support": row["min_support"],
                "mapped_context_count": row["mapped_context_count"],
                "total_hits": row["total_hits"],
                "residual_hits": row["residual_hits"],
                "clean_false_changes": row["clean_false_changes"],
                "residual_miss_books": row["residual_miss_books"],
            }
            for row in support_scores
        ],
        "residual_stability_rows": residual_rows,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": classification,
            "source_length_dependency_status": "contextual_mode_stability_rejected"
            if not promoted
            else "contextual_mode_stability_promoted",
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
        "# Contextual Mode Stability Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 25 stress-tests the gate-24 `context_combo` clue. It asks",
        "whether the full-fit `5/10` residual gain survives support pruning,",
        "leave-one-book retraining, and leave-context-out retraining.",
        "",
        "## Support Thresholds",
        "",
        "| Min support | Mapped contexts | Total hits | Residual hits | Clean false changes |",
        "|---:|---:|---:|---:|---:|",
    ]
    for row in result["support_threshold_scoreboard"]:
        lines.append(
            f"| `{row['min_support']}` | `{row['mapped_context_count']}` | "
            f"`{row['total_hits']}/{s['decision_count']}` | "
            f"`{row['residual_hits']}/{s['residual_decision_count']}` | "
            f"`{row['clean_false_changes']}` |"
        )
    lines.extend(
        [
            "",
            "## Residual Stability",
            "",
            "| Book | Class | Context support | Full hit | Leave-book hit | Leave-context hit |",
            "|---:|---|---:|---|---|---|",
        ]
    )
    for row in result["residual_stability_rows"]:
        lines.append(
            f"| `{row['book']}` | `{row['drift_class']}` | "
            f"`{row['context_support']}` | `{row['full_hit']}` | "
            f"`{row['leave_book_hit']}` | `{row['leave_context_hit']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Promotes contextual mode stability: `{s['promotes_contextual_mode_stability']}`.",
            f"- Full-fit residual hits: `{s['full_fit_residual_hits']}/{s['residual_decision_count']}`.",
            f"- Leave-one-book residual hits: `{s['leave_one_book_residual_hits']}/{s['residual_decision_count']}`.",
            f"- Leave-context-out residual hits: `{s['leave_context_out_residual_hits']}/{s['residual_decision_count']}`.",
            f"- Full-fit clean false changes: `{s['full_fit_clean_false_changes']}`.",
            f"- {s['interpretation']}",
            "- The context signal remains a weak full-fit clue, not a stable parser rule.",
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
