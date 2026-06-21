from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

GATE51_SCRIPT = HERE / "scripts" / "51_source_interval_precision_gate.py"
GATE51_RESULT = TEST_RESULTS / "51_source_interval_precision_gate.json"

OUT_STEM = "52_source_interval_observable_precision_gate"
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
PAIR_CANDIDATE_LIMIT = 40


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


def make_observable_predicates(rows: list[dict[str, Any]]) -> list[Predicate]:
    numeric_keys = [
        "target_start",
        "stable_index",
        "chosen_length",
        "active_length",
        "length_delta_abs",
        "branch_count",
        "copy_branch_count",
        "literal_branch_count",
        "payload_occurrences",
        "source_target_start_distance",
        "source_target_end_distance",
        "source_target_interval_distance",
        "max_source_context_recurrence",
        "min_source_context_recurrence",
        "r2_start_distance",
        "r2_end_distance",
        "r2_interval_distance",
        "r2_context_recurrence",
        "r4_start_distance",
        "r4_end_distance",
        "r4_interval_distance",
        "r4_context_recurrence",
        "r8_start_distance",
        "r8_end_distance",
        "r8_interval_distance",
        "r8_context_recurrence",
    ]
    categorical_keys = [
        "chosen_type",
        "active_type",
        "chosen_is_copy",
        "active_is_copy",
        "changes_active",
        "changes_type",
        "changes_length",
    ]
    predicates: list[Predicate] = []
    for key in numeric_keys:
        values = sorted({row[key] for row in rows if row[key] is not None})
        for value in values:
            predicates.append(
                (
                    f"{key}_le_{value}",
                    lambda row, key=key, value=value: row[key] <= value,
                )
            )
            predicates.append(
                (
                    f"{key}_ge_{value}",
                    lambda row, key=key, value=value: row[key] >= value,
                )
            )
    for key in categorical_keys:
        values = sorted({row[key] for row in rows}, key=lambda value: str(value))
        for value in values:
            label = str(value).replace(" ", "_")
            predicates.append(
                (
                    f"{key}_eq_{label}",
                    lambda row, key=key, value=value: row[key] == value,
                )
            )
    return predicates


def score_policy_rules(gate51, rows: list[dict[str, Any]], policy: str, predicates: list[Predicate]) -> list[dict[str, Any]]:
    policy_rows = gate51.rows_for_policy(rows, policy)
    singles = [gate51.score_rule(policy_rows, predicate) for predicate in predicates]
    top_predicates = [
        predicates[index]
        for index, _score in sorted(
            enumerate(singles), key=lambda item: gate51.score_key(item[1]), reverse=True
        )[:PAIR_CANDIDATE_LIMIT]
    ]
    pair_scores = []
    for i, left in enumerate(top_predicates):
        for right in top_predicates[i + 1 :]:
            pair_scores.append(gate51.score_rule(policy_rows, gate51.combine(left, right)))
    scores = singles + pair_scores
    for score in scores:
        score["policy"] = policy
    return scores


def full_scoreboard(gate51, rows: list[dict[str, Any]], predicates: list[Predicate]) -> list[dict[str, Any]]:
    scores = []
    for policy in sorted({row["policy"] for row in rows}):
        scores.extend(score_policy_rules(gate51, rows, policy, predicates))
    return sorted(scores, key=gate51.score_key, reverse=True)


def prequential(gate51, rows: list[dict[str, Any]], predicates: list[Predicate]) -> list[dict[str, Any]]:
    out = []
    policies = sorted({row["policy"] for row in rows})
    for cutoff in PREFIX_CUTOFFS:
        train = [row for row in rows if row["book"] < cutoff]
        test = [row for row in rows if row["book"] >= cutoff]
        train_scores = []
        for policy in policies:
            policy_rows = gate51.rows_for_policy(train, policy)
            for predicate in predicates:
                score = gate51.score_rule(policy_rows, predicate)
                score["policy"] = policy
                train_scores.append(score)
        selected = max(train_scores, key=gate51.score_key)
        selected_predicate = next(
            predicate for predicate in predicates if predicate[0] == selected["predicate"]
        )
        test_score = gate51.score_rule(
            gate51.rows_for_policy(test, selected["policy"]), selected_predicate
        )
        out.append(
            {
                "cutoff_book": cutoff,
                "selected_policy": selected["policy"],
                "selected_predicate": selected["predicate"],
                "train_residual_hits": selected["residual_hits"],
                "train_residual_total": selected["residual_total"],
                "train_clean_false_changes": selected["clean_false_changes"],
                "test_residual_hits": test_score["residual_hits"],
                "test_residual_total": test_score["residual_total"],
                "test_clean_false_changes": test_score["clean_false_changes"],
                "test_residual_false": test_score["residual_false"],
            }
        )
    return out


def make_result() -> dict[str, Any]:
    gate51_result = load_json(GATE51_RESULT)
    assert_boundary("source_interval_precision_gate", gate51_result)
    if gate51_result["classification"] != "source_interval_precision_weak_clue_not_promoted":
        raise RuntimeError("gate52 expects gate51 weak-clue state")
    gate51 = load_module("source_interval_precision_for_gate52", GATE51_SCRIPT)
    rows = gate51.build_rows()
    predicates = make_observable_predicates(rows)
    scoreboard = full_scoreboard(gate51, rows, predicates)
    best = scoreboard[0]
    zero_fp = [row for row in scoreboard if row["clean_false_changes"] == 0]
    best_zero_fp = zero_fp[0] if zero_fp else None
    preq = prequential(gate51, rows, predicates)
    cells_with_residuals = sum(1 for row in preq if row["test_residual_total"] > 0)
    cells_cover_all = sum(
        1
        for row in preq
        if row["test_residual_total"] > 0
        and row["test_residual_hits"] == row["test_residual_total"]
    )
    zero_clean_cells = sum(
        1 for row in preq if row["test_clean_false_changes"] == 0
    )
    promotes = (
        best_zero_fp is not None
        and best_zero_fp["residual_hits"] == best_zero_fp["residual_total"]
        and cells_cover_all == cells_with_residuals
        and zero_clean_cells == len(preq)
    )
    if promotes:
        classification = "source_interval_observable_precision_rule_promoted"
    elif best_zero_fp is not None and best_zero_fp["residual_hits"] > 0:
        classification = "source_interval_observable_precision_weak_clue_not_promoted"
    else:
        classification = "source_interval_observable_precision_rejected"
    prior = gate51_result["summary"]
    return {
        "schema": "source_interval_observable_precision_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "source_interval_precision_gate": rel(GATE51_RESULT),
            "source_interval_precision_script": rel(GATE51_SCRIPT),
        },
        "scope": {
            "analysis_only": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "target_text_required": True,
            "source_free_digit_generator_emitted": False,
            "promotes_parser_rule": promotes,
            "excludes_drift_class_predicates": True,
            "tests_observable_precision_only": True,
        },
        "summary": {
            "decision_policy_rows": len(rows),
            "policy_count": len({row["policy"] for row in rows}),
            "observable_predicate_count": len(predicates),
            "scored_rule_count": len(scoreboard),
            "prior_best_zero_fp_predicate": prior["best_zero_fp_predicate"],
            "prior_best_zero_fp_residual_hits": prior["best_zero_fp_residual_hits"],
            "best_policy": best["policy"],
            "best_predicate": best["predicate"],
            "best_residual_hits": best["residual_hits"],
            "best_residual_total": best["residual_total"],
            "best_clean_false_changes": best["clean_false_changes"],
            "best_residual_false": best["residual_false"],
            "best_zero_fp_policy": None if best_zero_fp is None else best_zero_fp["policy"],
            "best_zero_fp_predicate": None if best_zero_fp is None else best_zero_fp["predicate"],
            "best_zero_fp_residual_hits": 0 if best_zero_fp is None else best_zero_fp["residual_hits"],
            "best_zero_fp_residual_total": 0 if best_zero_fp is None else best_zero_fp["residual_total"],
            "prequential_cells": len(preq),
            "prequential_cells_with_residuals": cells_with_residuals,
            "prequential_cover_all_residual_cells": cells_cover_all,
            "prequential_zero_clean_false_change_cells": zero_clean_cells,
            "promotes_source_interval_observable_precision_rule": promotes,
            "interpretation": (
                "Gate 52 corrects gate 51 by excluding drift_class and other "
                "diagnostic labels from the precision predicates. It asks "
                "whether the source-interval signal has a genuinely observable "
                "safe firing condition."
            ),
        },
        "scoreboard_top": scoreboard[:30],
        "best_zero_fp_score": best_zero_fp,
        "prequential_rows": preq,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": classification,
            "source_length_dependency_status": "observable_source_interval_precision_tested",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / f"{OUT_STEM}.json"
    md_path = TEST_RESULTS / f"{OUT_STEM}.md"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    s = result["summary"]
    lines = [
        "# Source Interval Observable Precision Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 52 corrects the gate-51 precision screen by removing",
        "`drift_class` and any diagnostic post-difference label from the",
        "predicate family. The question is whether the source-interval",
        "signal has a genuinely observable safe firing condition.",
        "",
        "## Summary",
        "",
        f"- Policy-decision rows: `{s['decision_policy_rows']}`.",
        f"- Policies: `{s['policy_count']}`.",
        f"- Observable predicates: `{s['observable_predicate_count']}`.",
        f"- Scored rules: `{s['scored_rule_count']}`.",
        f"- Prior zero-FP predicate: `{s['prior_best_zero_fp_predicate']}`.",
        f"- Prior zero-FP residual hits: `{s['prior_best_zero_fp_residual_hits']}/10`.",
        f"- Best observable rule: `{s['best_policy']}` / `{s['best_predicate']}`.",
        f"- Best observable residual hits: `{s['best_residual_hits']}/{s['best_residual_total']}`.",
        f"- Best observable clean false changes: `{s['best_clean_false_changes']}`.",
        f"- Best observable zero-FP rule: `{s['best_zero_fp_policy']}` / `{s['best_zero_fp_predicate']}`.",
        f"- Best observable zero-FP residual hits: `{s['best_zero_fp_residual_hits']}/{s['best_zero_fp_residual_total']}`.",
        "",
        "## Scoreboard",
        "",
        "| Policy | Predicate | Residual hits | Clean false changes | Residual false | Selected |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in result["scoreboard_top"][:15]:
        lines.append(
            f"| `{row['policy']}` | `{row['predicate']}` | "
            f"`{row['residual_hits']}/{row['residual_total']}` | "
            f"`{row['clean_false_changes']}` | `{row['residual_false']}` | "
            f"`{row['selected_count']}` |"
        )
    lines.extend(
        [
            "",
            "## Prefix/Holdout",
            "",
            "| Cutoff | Policy | Predicate | Test residual hits | Test clean false changes | Test residual false |",
            "|---:|---|---|---:|---:|---:|",
        ]
    )
    for row in result["prequential_rows"]:
        lines.append(
            f"| `{row['cutoff_book']}` | `{row['selected_policy']}` | "
            f"`{row['selected_predicate']}` | "
            f"`{row['test_residual_hits']}/{row['test_residual_total']}` | "
            f"`{row['test_clean_false_changes']}` | `{row['test_residual_false']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Promotes observable source-interval precision rule: `{s['promotes_source_interval_observable_precision_rule']}`.",
            f"- Prequential cover-all-residual cells: `{s['prequential_cover_all_residual_cells']}/{s['prequential_cells_with_residuals']}`.",
            f"- Prequential zero-clean-false-change cells: `{s['prequential_zero_clean_false_change_cells']}/{s['prequential_cells']}`.",
            f"- {s['interpretation']}",
            "- The source-interval signal still does not convert into a clean observable parser rule.",
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
