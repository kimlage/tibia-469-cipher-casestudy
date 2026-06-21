from __future__ import annotations

import importlib.util
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

BRANCH_CONTINUATION_SCRIPT = (
    HERE / "scripts" / "22_residual_branch_continuation_audit.py"
)
BEAM_SELECTOR_SCRIPT = HERE / "scripts" / "59_beam_rank_selector_gate.py"
BEAM_SELECTOR = TEST_RESULTS / "59_beam_rank_selector_gate.json"

OUT_STEM = "60_beam_selector_stability_gate"
SUPPORT_THRESHOLDS = [1, 2, 3, 5, 8, 10]
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


def log2_comb(n: int, k: int) -> float:
    if k < 0 or k > n:
        return math.inf
    return math.log2(math.comb(n, k))


def majority_rank(gate59, rows: list[dict[str, Any]]) -> int:
    if not rows:
        return 1
    return gate59.majority_rank(rows)


def pruned_selector(
    gate59,
    rows: list[dict[str, Any]],
    context_name: str,
    context_fn: Callable[[dict[str, Any]], str],
    min_support: int,
) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[context_fn(row)].append(row)
    fallback = majority_rank(gate59, rows)
    mapping = {
        context: majority_rank(gate59, values)
        for context, values in grouped.items()
        if len(values) >= min_support
    }
    return {
        "context_name": context_name,
        "fallback_rank": fallback,
        "mapping": mapping,
        "context_count": len(mapping),
        "min_support": min_support,
        "support_counts": {context: len(values) for context, values in grouped.items()},
    }


def cost_score(
    gate59,
    score: dict[str, Any],
    baseline_lookup_bits: float,
    beam_width: int,
    threshold_count: int,
) -> dict[str, Any]:
    correction_count = score["total_total"] - score["total_hits"]
    table_bits = score["context_count"] * math.log2(beam_width)
    threshold_bits = math.log2(threshold_count)
    correction_bits = log2_comb(score["total_total"], correction_count)
    correction_rank_bits = correction_count * math.log2(beam_width)
    total_bits = threshold_bits + table_bits + correction_bits + correction_rank_bits
    return {
        **{key: value for key, value in score.items() if key != "rows"},
        "threshold_bits": threshold_bits,
        "table_bits": table_bits,
        "correction_count": correction_count,
        "correction_bits": correction_bits,
        "correction_rank_bits": correction_rank_bits,
        "total_bits_with_table_and_corrections": total_bits,
        "net_vs_lookup_bits": total_bits - baseline_lookup_bits,
    }


def threshold_scoreboard(
    gate59,
    rows: list[dict[str, Any]],
    context_name: str,
    context_fn: Callable[[dict[str, Any]], str],
    baseline_lookup_bits: float,
    beam_width: int,
) -> list[dict[str, Any]]:
    scores = []
    for threshold in SUPPORT_THRESHOLDS:
        selector = pruned_selector(gate59, rows, context_name, context_fn, threshold)
        score = gate59.evaluate_selector(rows, selector, context_fn)
        score["min_support"] = threshold
        scores.append(
            cost_score(
                gate59,
                score,
                baseline_lookup_bits,
                beam_width,
                len(SUPPORT_THRESHOLDS),
            )
        )
    scores.sort(
        key=lambda row: (
            -row["total_hits"],
            -row["residual_hits"],
            row["clean_false_changes"],
            row["net_vs_lookup_bits"],
            row["min_support"],
        )
    )
    return scores


def select_threshold_for_train(score_rows: list[dict[str, Any]]) -> dict[str, Any]:
    return max(
        score_rows,
        key=lambda row: (
            row["total_hits"],
            row["residual_hits"],
            -row["clean_false_changes"],
            -row["context_count"],
            -row["min_support"],
        ),
    )


def prequential_rows(
    gate59,
    rows: list[dict[str, Any]],
    context_name: str,
    context_fn: Callable[[dict[str, Any]], str],
) -> list[dict[str, Any]]:
    result = []
    for cutoff in PREFIX_CUTOFFS:
        train = [row for row in rows if row["book"] < cutoff]
        test = [row for row in rows if row["book"] >= cutoff]
        train_scores = []
        for threshold in SUPPORT_THRESHOLDS:
            selector = pruned_selector(
                gate59, train, context_name, context_fn, threshold
            )
            score = gate59.evaluate_selector(train, selector, context_fn)
            score["min_support"] = threshold
            score["selector"] = selector
            train_scores.append(score)
        selected = select_threshold_for_train(train_scores)
        test_score = gate59.evaluate_selector(
            test, selected["selector"], context_fn
        )
        oracle_scores = []
        for threshold in SUPPORT_THRESHOLDS:
            selector = pruned_selector(
                gate59, train, context_name, context_fn, threshold
            )
            score = gate59.evaluate_selector(test, selector, context_fn)
            score["min_support"] = threshold
            oracle_scores.append(score)
        oracle = select_threshold_for_train(oracle_scores)
        result.append(
            {
                "cutoff_book": cutoff,
                "selected_min_support": selected["min_support"],
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
                "test_unseen_contexts": test_score["unseen_contexts"],
                "oracle_min_support": oracle["min_support"],
                "oracle_test_total_hits": oracle["total_hits"],
                "oracle_test_residual_hits": oracle["residual_hits"],
                "selected_matches_oracle": (
                    test_score["total_hits"] == oracle["total_hits"]
                    and test_score["residual_hits"] == oracle["residual_hits"]
                    and test_score["clean_false_changes"]
                    == oracle["clean_false_changes"]
                ),
            }
        )
    return result


def residual_stability_rows(
    gate59,
    rows: list[dict[str, Any]],
    context_name: str,
    context_fn: Callable[[dict[str, Any]], str],
    min_support: int,
) -> list[dict[str, Any]]:
    full_selector = pruned_selector(gate59, rows, context_name, context_fn, min_support)
    result = []
    residual_rows = [row for row in rows if row["kind"] == "residual_first_drift"]
    for row in residual_rows:
        context = context_fn(row)
        full_rank = full_selector["mapping"].get(context, full_selector["fallback_rank"])
        leave_book_train = [candidate for candidate in rows if candidate["book"] != row["book"]]
        leave_book_selector = pruned_selector(
            gate59, leave_book_train, context_name, context_fn, min_support
        )
        leave_book_rank = leave_book_selector["mapping"].get(
            context, leave_book_selector["fallback_rank"]
        )
        leave_context_train = [
            candidate for candidate in rows if context_fn(candidate) != context
        ]
        leave_context_selector = pruned_selector(
            gate59, leave_context_train, context_name, context_fn, min_support
        )
        leave_context_rank = leave_context_selector["mapping"].get(
            context, leave_context_selector["fallback_rank"]
        )
        result.append(
            {
                "book": row["book"],
                "target_start": row["target_start"],
                "drift_class": row["drift_class"],
                "context": context,
                "context_support": full_selector["support_counts"].get(context, 0),
                "stable_rank": row["stable_rank"],
                "full_rank": full_rank,
                "full_hit": gate59.selected_is_stable(row, full_rank),
                "leave_book_rank": leave_book_rank,
                "leave_book_hit": gate59.selected_is_stable(row, leave_book_rank),
                "leave_context_rank": leave_context_rank,
                "leave_context_hit": gate59.selected_is_stable(row, leave_context_rank),
            }
        )
    return result


def make_result() -> dict[str, Any]:
    gate59_json = load_json(BEAM_SELECTOR)
    assert_boundary("beam_rank_selector_gate", gate59_json)
    if gate59_json["classification"] != "beam_rank_selector_weak_clue_not_promoted":
        raise RuntimeError("gate60 expects gate59 weak selector clue")

    gate59 = load_module("gate59_for_gate60", BEAM_SELECTOR_SCRIPT)
    gate22 = load_module("gate22_for_gate60", BRANCH_CONTINUATION_SCRIPT)
    decisions = gate22.collect_decisions()["decisions"]
    objective = gate59_json["summary"]["objective"]
    beam_width = int(gate59_json["summary"]["beam_width"])
    context_name = gate59_json["summary"]["best_context"]
    contexts = gate59.context_families()
    context_fn = contexts[context_name]
    rows = gate59.build_rows(gate22, decisions, objective, beam_width)
    baseline_lookup_bits = float(gate59_json["summary"]["baseline_lookup_bits"])

    thresholds = threshold_scoreboard(
        gate59, rows, context_name, context_fn, baseline_lookup_bits, beam_width
    )
    best_threshold = thresholds[0]
    stability = residual_stability_rows(
        gate59, rows, context_name, context_fn, int(best_threshold["min_support"])
    )
    preq = prequential_rows(gate59, rows, context_name, context_fn)

    leave_book_hits = sum(1 for row in stability if row["leave_book_hit"])
    leave_context_hits = sum(1 for row in stability if row["leave_context_hit"])
    promotes = (
        best_threshold["total_hits"] == best_threshold["total_total"]
        and best_threshold["net_vs_lookup_bits"] <= 0
        and leave_book_hits == len(stability)
        and leave_context_hits == len(stability)
        and all(row["test_total_hits"] == row["test_total"] for row in preq)
    )
    weak = (
        best_threshold["residual_hits"] == best_threshold["residual_total"]
        and (leave_book_hits < len(stability) or leave_context_hits < len(stability))
    )
    classification = (
        "beam_selector_stability_promoted"
        if promotes
        else "beam_selector_stability_weak_fullfit_not_promoted"
        if weak
        else "beam_selector_stability_rejected"
    )

    return {
        "schema": "beam_selector_stability_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "beam_rank_selector_gate": rel(BEAM_SELECTOR),
            "beam_rank_selector_script": rel(BEAM_SELECTOR_SCRIPT),
        },
        "scope": {
            "analysis_only": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "target_text_required": True,
            "stable_projection_used_as_label_only": True,
            "declared_literal_windows_granted": False,
            "source_free_digit_generator_emitted": False,
            "tests_stability_of_beam_selector": True,
            "promotes_parser_rule": promotes,
        },
        "summary": {
            "decision_count": len(rows),
            "residual_decision_count": len(stability),
            "clean_control_count": sum(1 for row in rows if row["kind"] == "clean_control"),
            "context_name": context_name,
            "support_thresholds": SUPPORT_THRESHOLDS,
            "best_min_support": best_threshold["min_support"],
            "best_total_hits": best_threshold["total_hits"],
            "best_total_total": best_threshold["total_total"],
            "best_residual_hits": best_threshold["residual_hits"],
            "best_residual_total": best_threshold["residual_total"],
            "best_clean_false_changes": best_threshold["clean_false_changes"],
            "best_context_count": best_threshold["context_count"],
            "best_net_vs_lookup_bits": best_threshold["net_vs_lookup_bits"],
            "leave_one_book_residual_hits": leave_book_hits,
            "leave_context_out_residual_hits": leave_context_hits,
            "prequential_cells": len(preq),
            "prequential_cover_all_test_cells": sum(
                1 for row in preq if row["test_total_hits"] == row["test_total"]
            ),
            "prequential_cover_all_residual_cells": sum(
                1
                for row in preq
                if row["test_residual_hits"] == row["test_residual_total"]
            ),
            "prequential_zero_clean_false_change_cells": sum(
                1 for row in preq if row["test_clean_false_changes"] == 0
            ),
            "prequential_selected_matches_oracle_cells": sum(
                1 for row in preq if row["selected_matches_oracle"]
            ),
            "promotes_beam_selector_stability": promotes,
            "weak_fullfit_selector_clue": weak,
            "interpretation": (
                "Gate 60 stress-tests the gate59 beam_context_combo selector "
                "by pruning low-support contexts and by leave-one-book and "
                "leave-context-out residual checks."
            ),
        },
        "support_threshold_scoreboard": thresholds,
        "residual_stability_rows": stability,
        "prequential_rows": preq,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": classification,
            "source_length_dependency_status": "beam_selector_fullfit_not_stable"
            if not promotes
            else "beam_selector_stability_promoted",
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
        "# Beam Selector Stability Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 60 stress-tests the gate-59 `beam_context_combo` selector.",
        "It asks whether the full-fit selector survives support pruning,",
        "leave-one-book retraining, leave-context-out retraining, and",
        "prefix/holdout selection.",
        "",
        "## Summary",
        "",
        f"- Context: `{s['context_name']}`.",
        f"- Support thresholds: `{s['support_thresholds']}`.",
        f"- Best min support: `{s['best_min_support']}`.",
        f"- Best total hits: `{s['best_total_hits']}/{s['best_total_total']}`.",
        f"- Best residual hits: `{s['best_residual_hits']}/{s['best_residual_total']}`.",
        f"- Best clean false changes: `{s['best_clean_false_changes']}`.",
        f"- Best context count: `{s['best_context_count']}`.",
        f"- Best net vs lookup: `{s['best_net_vs_lookup_bits']:.3f}` bits.",
        f"- Leave-one-book residual hits: `{s['leave_one_book_residual_hits']}/{s['residual_decision_count']}`.",
        f"- Leave-context-out residual hits: `{s['leave_context_out_residual_hits']}/{s['residual_decision_count']}`.",
        f"- Prefix/holdout cover-all cells: `{s['prequential_cover_all_test_cells']}/{s['prequential_cells']}`.",
        f"- Prefix/holdout cover-all-residual cells: `{s['prequential_cover_all_residual_cells']}/{s['prequential_cells']}`.",
        f"- Prefix/holdout zero-clean-false-change cells: `{s['prequential_zero_clean_false_change_cells']}/{s['prequential_cells']}`.",
        "",
        "## Support Thresholds",
        "",
        "| Min support | Hits | Residual hits | Clean false changes | Contexts | Net vs lookup |",
        "| ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in result["support_threshold_scoreboard"]:
        lines.append(
            f"| `{row['min_support']}` | `{row['total_hits']}/{row['total_total']}` | "
            f"`{row['residual_hits']}/{row['residual_total']}` | "
            f"`{row['clean_false_changes']}` | `{row['context_count']}` | "
            f"`{row['net_vs_lookup_bits']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Residual Stability",
            "",
            "| Book | Target | Class | Support | Stable rank | Full hit | Leave-book hit | Leave-context hit |",
            "| ---: | ---: | --- | ---: | ---: | --- | --- | --- |",
        ]
    )
    for row in result["residual_stability_rows"]:
        lines.append(
            f"| `{row['book']}` | `{row['target_start']}` | "
            f"`{row['drift_class']}` | `{row['context_support']}` | "
            f"`{row['stable_rank']}` | `{row['full_hit']}` | "
            f"`{row['leave_book_hit']}` | `{row['leave_context_hit']}` |"
        )
    lines.extend(
        [
            "",
            "## Prefix/Holdout",
            "",
            "| Cutoff | Min support | Test hits | Test residual hits | Test clean false changes | Oracle min support |",
            "| ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in result["prequential_rows"]:
        lines.append(
            f"| `{row['cutoff_book']}` | `{row['selected_min_support']}` | "
            f"`{row['test_total_hits']}/{row['test_total']}` | "
            f"`{row['test_residual_hits']}/{row['test_residual_total']}` | "
            f"`{row['test_clean_false_changes']}` | "
            f"`{row['oracle_min_support']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Promotes beam selector stability: `{s['promotes_beam_selector_stability']}`.",
            f"- Weak full-fit selector clue: `{s['weak_fullfit_selector_clue']}`.",
            "- The gate-59 full-fit selector does not become a stable parser:",
            "  pruning does not remove the clean false changes, leave-context-out",
            "  support collapses most residuals, and prefix/holdout has no",
            "  cover-all test cell.",
            "- Compression bound is unchanged.",
            "- Row0 remains exogenous and unchanged.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
            "",
        ]
    )
    md_path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    write_result(make_result())
