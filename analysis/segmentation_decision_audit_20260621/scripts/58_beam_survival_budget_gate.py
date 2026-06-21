from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

BRANCH_CONTINUATION_SCRIPT = (
    HERE / "scripts" / "22_residual_branch_continuation_audit.py"
)
BRANCH_CONTINUATION = TEST_RESULTS / "22_residual_branch_continuation_audit.json"
LATENT_PATH_STATE_BUDGET = TEST_RESULTS / "57_latent_path_state_budget_gate.json"

OUT_STEM = "58_beam_survival_budget_gate"
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
BEAM_WIDTHS = [1, 2, 3, 5, 8, 10, 20]


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


def stable_rank(gate22, decision: dict[str, Any], objective: str) -> int:
    ordered = sorted(decision["branches"], key=gate22.OBJECTIVES[objective])
    for index, branch in enumerate(ordered, start=1):
        if branch["is_stable"]:
            return index
    raise RuntimeError(
        {
            "type": "stable_branch_not_observable",
            "book": decision["book"],
            "target_start": decision["target_start"],
            "objective": objective,
        }
    )


def rank_rows(gate22, decisions: list[dict[str, Any]], objective: str) -> list[dict[str, Any]]:
    rows = []
    for decision in decisions:
        rank = stable_rank(gate22, decision, objective)
        rows.append(
            {
                "book": int(decision["book"]),
                "target_start": int(decision["target_start"]),
                "kind": decision["kind"],
                "drift_class": decision["drift_class"],
                "branch_count": len(decision["branches"]),
                "stable_rank": rank,
                "active_op": decision["active_op"],
                "stable_op": decision["stable_op"],
            }
        )
    return rows


def summarize_objective(
    gate22, decisions: list[dict[str, Any]], objective: str
) -> dict[str, Any]:
    rows = rank_rows(gate22, decisions, objective)
    residual = [row for row in rows if row["kind"] == "residual_first_drift"]
    clean = [row for row in rows if row["kind"] == "clean_control"]
    residual_ranks = [row["stable_rank"] for row in residual]
    clean_ranks = [row["stable_rank"] for row in clean]
    all_ranks = residual_ranks + clean_ranks
    topk_rows = []
    for width in BEAM_WIDTHS:
        topk_rows.append(
            {
                "beam_width": width,
                "residual_survived": sum(1 for rank in residual_ranks if rank <= width),
                "residual_total": len(residual_ranks),
                "clean_survived": sum(1 for rank in clean_ranks if rank <= width),
                "clean_total": len(clean_ranks),
                "all_survived": sum(1 for rank in all_ranks if rank <= width),
                "all_total": len(all_ranks),
            }
        )
    residual_fixed_width = max(residual_ranks, default=0)
    all_fixed_width = max(all_ranks, default=0)
    return {
        "objective": objective,
        "residual_max_rank": residual_fixed_width,
        "clean_max_rank": max(clean_ranks, default=0),
        "all_max_rank": all_fixed_width,
        "residual_top1": sum(1 for rank in residual_ranks if rank == 1),
        "clean_top1": sum(1 for rank in clean_ranks if rank == 1),
        "residual_total": len(residual_ranks),
        "clean_total": len(clean_ranks),
        "residual_rank_bits_lower_bound": sum(math.log2(rank) for rank in residual_ranks),
        "residual_fixed_width_bits": 0.0
        if not residual_ranks
        else len(residual_ranks) * math.log2(residual_fixed_width),
        "all_fixed_width_bits": 0.0
        if not all_ranks
        else len(all_ranks) * math.log2(all_fixed_width),
        "topk_rows": topk_rows,
        "residual_rows": residual,
    }


def select_objective_for_train(
    gate22, train: list[dict[str, Any]], objectives: list[str]
) -> dict[str, Any]:
    scored = [summarize_objective(gate22, train, objective) for objective in objectives]
    return min(
        scored,
        key=lambda row: (
            row["all_max_rank"],
            row["residual_max_rank"],
            -row["residual_top1"],
            -row["clean_top1"],
            row["objective"],
        ),
    )


def prequential_rows(gate22, decisions: list[dict[str, Any]], objectives: list[str]) -> list[dict[str, Any]]:
    rows = []
    for cutoff in PREFIX_CUTOFFS:
        train = [row for row in decisions if int(row["book"]) < cutoff]
        test = [row for row in decisions if int(row["book"]) >= cutoff]
        selected = select_objective_for_train(gate22, train, objectives)
        train_width = selected["all_max_rank"]
        test_summary = summarize_objective(gate22, test, selected["objective"])
        rows.append(
            {
                "cutoff_book": cutoff,
                "selected_objective": selected["objective"],
                "train_all_beam_width": train_width,
                "train_residual_beam_width": selected["residual_max_rank"],
                "test_all_max_rank": test_summary["all_max_rank"],
                "test_residual_max_rank": test_summary["residual_max_rank"],
                "test_all_survived_at_train_width": test_summary["all_max_rank"]
                <= train_width,
                "test_residual_survived_at_train_width": test_summary[
                    "residual_max_rank"
                ]
                <= train_width,
                "test_residual_top1": test_summary["residual_top1"],
                "test_residual_total": test_summary["residual_total"],
                "test_clean_top1": test_summary["clean_top1"],
                "test_clean_total": test_summary["clean_total"],
            }
        )
    return rows


def make_result() -> dict[str, Any]:
    gate22_json = load_json(BRANCH_CONTINUATION)
    gate57 = load_json(LATENT_PATH_STATE_BUDGET)
    assert_boundary("residual_branch_continuation_audit", gate22_json)
    assert_boundary("latent_path_state_budget_gate", gate57)
    if gate22_json["classification"] != "residual_branch_continuation_objectives_rejected":
        raise RuntimeError("gate58 expects gate22 direct branch choice to be rejected")
    if gate57["classification"] != "latent_path_state_budget_rejected_lookup_repackaging":
        raise RuntimeError("gate58 expects gate57 latent budget to reject lookup repackaging")

    gate22 = load_module("gate22_for_gate58", BRANCH_CONTINUATION_SCRIPT)
    decisions = gate22.collect_decisions()["decisions"]
    objectives = [
        name for name in gate22.OBJECTIVES if not name.startswith("oracle_")
    ]
    objective_rows = [
        summarize_objective(gate22, decisions, objective) for objective in objectives
    ]
    objective_rows.sort(
        key=lambda row: (
            row["all_max_rank"],
            row["residual_max_rank"],
            row["residual_fixed_width_bits"],
            row["objective"],
        )
    )
    best = objective_rows[0]
    preq = prequential_rows(gate22, decisions, objectives)

    objective_id_bits = math.log2(len(objectives))
    fixed_width_model_bits = (
        gate57["summary"]["site_bits"]
        + objective_id_bits
        + best["residual_fixed_width_bits"]
    )
    rank_lower_bound_bits = (
        gate57["summary"]["site_bits"]
        + objective_id_bits
        + best["residual_rank_bits_lower_bound"]
    )
    baseline_bits = gate57["summary"]["baseline_lookup_bits"]

    promotes = (
        best["all_max_rank"] == 1
        and all(row["test_all_max_rank"] == 1 for row in preq)
    )
    weak_clue = (
        best["all_max_rank"] <= 5
        and all(row["test_all_survived_at_train_width"] for row in preq)
        and all(row["test_residual_survived_at_train_width"] for row in preq)
    )
    classification = (
        "beam_survival_parser_promoted"
        if promotes
        else "beam_survival_weak_path_state_clue_not_promoted"
        if weak_clue
        else "beam_survival_budget_rejected"
    )

    return {
        "schema": "beam_survival_budget_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "residual_branch_continuation_audit": rel(BRANCH_CONTINUATION),
            "latent_path_state_budget_gate": rel(LATENT_PATH_STATE_BUDGET),
        },
        "scope": {
            "analysis_only": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "target_text_required": True,
            "stable_projection_used_as_label_only": True,
            "declared_literal_windows_granted": False,
            "source_free_digit_generator_emitted": False,
            "tests_survival_not_selection": True,
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
            "objective_count": len(objectives),
            "beam_widths_tested": BEAM_WIDTHS,
            "best_objective": best["objective"],
            "best_all_max_rank": best["all_max_rank"],
            "best_residual_max_rank": best["residual_max_rank"],
            "best_clean_max_rank": best["clean_max_rank"],
            "best_residual_top1": best["residual_top1"],
            "best_clean_top1": best["clean_top1"],
            "prequential_cells": len(preq),
            "prequential_all_survived_at_train_width_cells": sum(
                1 for row in preq if row["test_all_survived_at_train_width"]
            ),
            "prequential_residual_survived_at_train_width_cells": sum(
                1 for row in preq if row["test_residual_survived_at_train_width"]
            ),
            "baseline_lookup_bits": baseline_bits,
            "objective_id_bits": objective_id_bits,
            "fixed_width_model_bits": fixed_width_model_bits,
            "fixed_width_net_vs_lookup_bits": fixed_width_model_bits - baseline_bits,
            "rank_lower_bound_bits": rank_lower_bound_bits,
            "rank_lower_bound_net_vs_lookup_bits": rank_lower_bound_bits
            - baseline_bits,
            "promotes_beam_parser": promotes,
            "weak_beam_survival_clue": weak_clue,
            "interpretation": (
                "This gate tests whether the stable residual choices at least "
                "survive inside a small observable beam after direct branch "
                "selection failed. Beam survival is weaker than a parser: it "
                "keeps the right branch available but still needs a downstream "
                "selection mechanism or paid residual choices."
            ),
        },
        "objective_scoreboard": [
            {
                key: value
                for key, value in row.items()
                if key not in {"residual_rows"}
            }
            for row in objective_rows
        ],
        "prequential_rows": preq,
        "best_residual_rows": best["residual_rows"],
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": classification,
            "source_length_dependency_status": "small_beam_survival_only_not_selection"
            if weak_clue and not promotes
            else "beam_parser_promoted"
            if promotes
            else "beam_survival_rejected",
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
        "# Beam Survival Budget Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 58 asks a narrower path-state question after direct branch",
        "selection, rankers, context tables, observable signatures, and latent",
        "lookup pricing failed: does the stable branch at least remain inside",
        "a small observable beam? This is a survival test, not a promoted",
        "selection rule.",
        "",
        "## Summary",
        "",
        f"- Decisions: `{s['decision_count']}`.",
        f"- Residual decisions: `{s['residual_decision_count']}`.",
        f"- Clean controls: `{s['clean_control_count']}`.",
        f"- Objectives tested: `{s['objective_count']}`.",
        f"- Best objective: `{s['best_objective']}`.",
        f"- Best all-decision beam width: `{s['best_all_max_rank']}`.",
        f"- Best residual beam width: `{s['best_residual_max_rank']}`.",
        f"- Residual top-1 choices under best objective: `{s['best_residual_top1']}/{s['residual_decision_count']}`.",
        f"- Clean top-1 choices under best objective: `{s['best_clean_top1']}/{s['clean_control_count']}`.",
        f"- Prefix/holdout all-survival cells at train width: `{s['prequential_all_survived_at_train_width_cells']}/{s['prequential_cells']}`.",
        f"- Prefix/holdout residual-survival cells at train width: `{s['prequential_residual_survived_at_train_width_cells']}/{s['prequential_cells']}`.",
        f"- Fixed-width model bits after site/objective cost: `{s['fixed_width_model_bits']:.3f}`.",
        f"- Fixed-width net vs residual lookup: `{s['fixed_width_net_vs_lookup_bits']:.3f}`.",
        f"- Rank lower bound bits after site/objective cost: `{s['rank_lower_bound_bits']:.3f}`.",
        f"- Rank lower bound net vs residual lookup: `{s['rank_lower_bound_net_vs_lookup_bits']:.3f}`.",
        "",
        "## Objective Scoreboard",
        "",
        "| Objective | All max rank | Residual max rank | Clean max rank | Residual top1 | Clean top1 | Fixed-width bits |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in result["objective_scoreboard"]:
        lines.append(
            f"| `{row['objective']}` | `{row['all_max_rank']}` | "
            f"`{row['residual_max_rank']}` | `{row['clean_max_rank']}` | "
            f"`{row['residual_top1']}/{row['residual_total']}` | "
            f"`{row['clean_top1']}/{row['clean_total']}` | "
            f"`{row['residual_fixed_width_bits']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Prefix/Holdout",
            "",
            "| Cutoff | Objective | Train beam | Test all max rank | Test residual max rank | Test all survives | Test residual survives |",
            "| ---: | --- | ---: | ---: | ---: | --- | --- |",
        ]
    )
    for row in result["prequential_rows"]:
        lines.append(
            f"| `{row['cutoff_book']}` | `{row['selected_objective']}` | "
            f"`{row['train_all_beam_width']}` | `{row['test_all_max_rank']}` | "
            f"`{row['test_residual_max_rank']}` | "
            f"`{row['test_all_survived_at_train_width']}` | "
            f"`{row['test_residual_survived_at_train_width']}` |"
        )
    lines.extend(
        [
            "",
            "## Residual Rows Under Best Objective",
            "",
            "| Book | Target | Class | Branches | Stable rank | Active | Stable |",
            "| ---: | ---: | --- | ---: | ---: | --- | --- |",
        ]
    )
    for row in result["best_residual_rows"]:
        lines.append(
            f"| `{row['book']}` | `{row['target_start']}` | "
            f"`{row['drift_class']}` | `{row['branch_count']}` | "
            f"`{row['stable_rank']}` | `{row['active_op']}` | "
            f"`{row['stable_op']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Promotes beam parser: `{s['promotes_beam_parser']}`.",
            f"- Weak beam-survival clue: `{s['weak_beam_survival_clue']}`.",
            "- Small-beam survival is real but weaker than generation: a width-5",
            "  beam can keep the stable branch alive under the best objective,",
            "  but the top-1 branch still fails residual choices and a fixed-width",
            "  paid model is worse than the residual lookup.",
            "- The rank lower bound is marked diagnostic only because it assumes",
            "  site/rank knowledge rather than a downstream selector.",
            "- Compression bound is unchanged.",
            "- Row0 remains exogenous and unchanged.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
            "",
        ]
    )
    md_path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    write_result(make_result())
