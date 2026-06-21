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
BEAM_SURVIVAL = TEST_RESULTS / "58_beam_survival_budget_gate.json"
RESIDUAL_PATCH_PROGRAM = TEST_RESULTS / "62_residual_patch_program_gate.json"

OUT_STEM = "63_beam_markov_state_selector_gate"
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
BOS_RANK = 0


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


def ordered_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda row: (int(row["book"]), int(row["stable_index"])))


def previous_stable_rank(rows: list[dict[str, Any]], index: int) -> int:
    if index == 0 or int(rows[index - 1]["book"]) != int(rows[index]["book"]):
        return BOS_RANK
    return int(rows[index - 1]["stable_rank"])


ContextFn = Callable[[dict[str, Any], int], str]


def context_families() -> dict[str, ContextFn]:
    return {
        "global": lambda row, prev: "global",
        "prev_rank": lambda row, prev: f"prev={prev}",
        "prev_rank_x_active_type": lambda row, prev: (
            f"prev={prev}|active_type={row['active_type']}"
        ),
        "prev_rank_x_active_shape": lambda row, prev: (
            f"prev={prev}|active_shape={row['active_shape']}"
        ),
        "prev_rank_x_position": lambda row, prev: (
            f"prev={prev}|target={row['target_bucket']}"
        ),
        "prev_rank_x_top1_shape": lambda row, prev: (
            f"prev={prev}|top1={row['top1_shape']}"
        ),
        "prev_rank_x_top2_signature": lambda row, prev: (
            f"prev={prev}|top1={row['top1_shape']}|top2={row['top2_shape']}"
        ),
        "prev_rank_x_beam_combo": lambda row, prev: (
            f"prev={prev}|target={row['target_bucket']}|"
            f"active={row['active_shape']}|top1={row['top1_shape']}|"
            f"branches={row['branch_count_bucket']}"
        ),
    }


def majority_rank(rows: list[dict[str, Any]]) -> int:
    if not rows:
        return 1
    counts = Counter(int(row["stable_rank"]) for row in rows)
    return min(counts, key=lambda rank: (-counts[rank], rank))


def train_selector(
    rows: list[dict[str, Any]],
    context_name: str,
    context_fn: ContextFn,
) -> dict[str, Any]:
    ordered = ordered_rows(rows)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for index, row in enumerate(ordered):
        grouped[context_fn(row, previous_stable_rank(ordered, index))].append(row)
    mapping = {context: majority_rank(values) for context, values in grouped.items()}
    return {
        "context_name": context_name,
        "fallback_rank": majority_rank(ordered),
        "mapping": mapping,
        "context_count": len(mapping),
    }


def select_rank(
    selector: dict[str, Any],
    context_fn: ContextFn,
    row: dict[str, Any],
    previous_rank: int,
) -> int:
    context = context_fn(row, previous_rank)
    return int(selector["mapping"].get(context, selector["fallback_rank"]))


def evaluate_selector(
    gate59,
    rows: list[dict[str, Any]],
    selector: dict[str, Any],
    context_fn: ContextFn,
    mode: str,
) -> dict[str, Any]:
    ordered = ordered_rows(rows)
    scored = []
    previous_predicted_rank = BOS_RANK
    previous_book = None
    for index, row in enumerate(ordered):
        if previous_book != int(row["book"]):
            previous_predicted_rank = BOS_RANK
        if mode == "teacher_forced":
            previous_rank = previous_stable_rank(ordered, index)
        elif mode == "free_run":
            previous_rank = previous_predicted_rank
        else:
            raise RuntimeError(f"unknown evaluation mode {mode}")
        rank = select_rank(selector, context_fn, row, previous_rank)
        hit = gate59.selected_is_stable(row, rank)
        scored.append(
            {
                "book": row["book"],
                "kind": row["kind"],
                "drift_class": row["drift_class"],
                "stable_rank": row["stable_rank"],
                "previous_rank": previous_rank,
                "predicted_rank": rank,
                "hit": hit,
            }
        )
        previous_predicted_rank = rank
        previous_book = int(row["book"])
    residual = [row for row in scored if row["kind"] == "residual_first_drift"]
    clean = [row for row in scored if row["kind"] == "clean_control"]
    return {
        "context_name": selector["context_name"],
        "mode": mode,
        "context_count": selector["context_count"],
        "total_hits": sum(1 for row in scored if row["hit"]),
        "total_total": len(scored),
        "residual_hits": sum(1 for row in residual if row["hit"]),
        "residual_total": len(residual),
        "clean_hits": sum(1 for row in clean if row["hit"]),
        "clean_total": len(clean),
        "clean_false_changes": sum(1 for row in clean if not row["hit"]),
        "residual_miss_books": [
            row["book"] for row in residual if not row["hit"]
        ],
        "selected_rank_counts": dict(
            sorted(Counter(row["predicted_rank"] for row in scored).items())
        ),
        "rows": scored,
    }


def score_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        row["total_hits"],
        row["residual_hits"],
        -row["clean_false_changes"],
        -row["context_count"],
        row["context_name"],
    )


def full_fit_scoreboard(
    gate59,
    rows: list[dict[str, Any]],
    contexts: dict[str, ContextFn],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    teacher_scores = []
    free_scores = []
    for name, fn in contexts.items():
        selector = train_selector(rows, name, fn)
        teacher_scores.append(
            evaluate_selector(gate59, rows, selector, fn, "teacher_forced")
        )
        free_scores.append(evaluate_selector(gate59, rows, selector, fn, "free_run"))
    teacher_scores.sort(key=score_key, reverse=True)
    free_scores.sort(key=score_key, reverse=True)
    return teacher_scores, free_scores


def prequential_rows(
    gate59,
    rows: list[dict[str, Any]],
    contexts: dict[str, ContextFn],
) -> list[dict[str, Any]]:
    result = []
    for cutoff in PREFIX_CUTOFFS:
        train = [row for row in rows if int(row["book"]) < cutoff]
        test = [row for row in rows if int(row["book"]) >= cutoff]
        trained = []
        for name, fn in contexts.items():
            selector = train_selector(train, name, fn)
            train_score = evaluate_selector(gate59, train, selector, fn, "free_run")
            trained.append((name, fn, selector, train_score))
        selected_name, selected_fn, selected_selector, selected_train = max(
            trained, key=lambda item: score_key(item[3])
        )
        test_score = evaluate_selector(
            gate59, test, selected_selector, selected_fn, "free_run"
        )
        oracle_scores = [
            evaluate_selector(gate59, test, selector, fn, "free_run")
            for _name, fn, selector, _train_score in trained
        ]
        oracle = max(oracle_scores, key=score_key)
        result.append(
            {
                "cutoff_book": cutoff,
                "selected_context": selected_name,
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
                "oracle_context": oracle["context_name"],
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


def priced_score(
    row: dict[str, Any],
    baseline_lookup_bits: float,
    beam_width: int,
    context_family_count: int,
) -> dict[str, Any]:
    correction_count = row["total_total"] - row["total_hits"]
    selector_bits = math.log2(context_family_count)
    table_bits = row["context_count"] * math.log2(beam_width)
    correction_bits = log2_comb(row["total_total"], correction_count)
    correction_rank_bits = correction_count * math.log2(beam_width)
    total = selector_bits + table_bits + correction_bits + correction_rank_bits
    return {
        **{key: value for key, value in row.items() if key != "rows"},
        "selector_bits": selector_bits,
        "table_bits": table_bits,
        "correction_count": correction_count,
        "correction_bits": correction_bits,
        "correction_rank_bits": correction_rank_bits,
        "total_bits_with_table_and_corrections": total,
        "net_vs_lookup_bits": total - baseline_lookup_bits,
    }


def make_result() -> dict[str, Any]:
    gate58 = load_json(BEAM_SURVIVAL)
    gate62 = load_json(RESIDUAL_PATCH_PROGRAM)
    assert_boundary("beam_survival_budget_gate", gate58)
    assert_boundary("residual_patch_program_gate", gate62)
    if gate62["classification"] != "residual_patch_program_weak_macro_not_promoted":
        raise RuntimeError("gate63 expects gate62 to leave patch program unpromoted")

    gate22 = load_module("gate22_for_gate63", BRANCH_CONTINUATION_SCRIPT)
    gate59 = load_module("gate59_for_gate63", BEAM_SELECTOR_SCRIPT)
    decisions = gate22.collect_decisions()["decisions"]
    objective = gate58["summary"]["best_objective"]
    beam_width = int(gate58["summary"]["best_all_max_rank"])
    rows = gate59.build_rows(gate22, decisions, objective, beam_width)
    contexts = context_families()
    teacher_scores, free_scores = full_fit_scoreboard(gate59, rows, contexts)
    best_teacher = teacher_scores[0]
    best_free = free_scores[0]
    preq = prequential_rows(gate59, rows, contexts)
    baseline_lookup_bits = float(gate62["summary"]["baseline_lookup_bits"])
    priced = priced_score(best_free, baseline_lookup_bits, beam_width, len(contexts))
    top1_total = gate58["summary"]["best_clean_top1"] + gate58["summary"][
        "best_residual_top1"
    ]

    promotes = (
        best_free["total_hits"] == best_free["total_total"]
        and all(row["test_total_hits"] == row["test_total"] for row in preq)
        and priced["net_vs_lookup_bits"] < 0
    )
    weak = (
        best_free["total_hits"] > top1_total
        and best_free["clean_false_changes"] <= 5
    )
    classification = (
        "beam_markov_state_selector_promoted"
        if promotes
        else "beam_markov_state_selector_weak_not_promoted"
        if weak
        else "beam_markov_state_selector_rejected"
    )

    return {
        "schema": "beam_markov_state_selector_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "beam_survival_budget_gate": rel(BEAM_SURVIVAL),
            "residual_patch_program_gate": rel(RESIDUAL_PATCH_PROGRAM),
            "residual_branch_continuation_script": rel(BRANCH_CONTINUATION_SCRIPT),
        },
        "scope": {
            "analysis_only": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "target_text_required": True,
            "stable_projection_used_as_train_label_only": True,
            "free_run_required_for_promotion": True,
            "teacher_forced_is_diagnostic_only": True,
            "declared_literal_windows_granted": False,
            "source_free_digit_generator_emitted": False,
            "tests_latent_markov_selector_not_bit_sweep": True,
            "promotes_parser_rule": promotes,
        },
        "summary": {
            "decision_count": len(rows),
            "residual_decision_count": sum(
                1 for row in rows if row["kind"] == "residual_first_drift"
            ),
            "clean_control_count": sum(
                1 for row in rows if row["kind"] == "clean_control"
            ),
            "objective": objective,
            "beam_width": beam_width,
            "context_family_count": len(contexts),
            "best_teacher_context": best_teacher["context_name"],
            "best_teacher_total_hits": best_teacher["total_hits"],
            "best_teacher_residual_hits": best_teacher["residual_hits"],
            "best_teacher_clean_false_changes": best_teacher["clean_false_changes"],
            "best_free_context": best_free["context_name"],
            "best_free_context_count": best_free["context_count"],
            "best_free_total_hits": best_free["total_hits"],
            "best_free_total_total": best_free["total_total"],
            "best_free_residual_hits": best_free["residual_hits"],
            "best_free_residual_total": best_free["residual_total"],
            "best_free_clean_false_changes": best_free["clean_false_changes"],
            "top1_total_hits": top1_total,
            "top1_residual_hits": gate58["summary"]["best_residual_top1"],
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
            "best_free_total_bits_with_table_and_corrections": priced[
                "total_bits_with_table_and_corrections"
            ],
            "best_free_net_vs_lookup_bits": priced["net_vs_lookup_bits"],
            "baseline_lookup_bits": baseline_lookup_bits,
            "promotes_markov_state_selector": promotes,
            "weak_markov_state_selector_clue": weak,
            "interpretation": (
                "This gate tests a small sequential selector over the surviving "
                "beam ranks. Teacher-forced state is diagnostic; promotion "
                "requires free-run state to generalize under prefix/holdout."
            ),
        },
        "teacher_forced_scoreboard": [
            {key: value for key, value in row.items() if key != "rows"}
            for row in teacher_scores
        ],
        "free_run_scoreboard": [
            {key: value for key, value in row.items() if key != "rows"}
            for row in free_scores
        ],
        "priced_best_free_run": priced,
        "prequential_rows": preq,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": classification,
            "source_length_dependency_status": "markov_state_selector_not_promoted",
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
        "# Beam Markov State Selector Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 63 tests whether the missing downstream selector is a small",
        "sequential state rule over beam ranks. It is stricter than a full-fit",
        "context table: teacher-forced state is diagnostic only, and promotion",
        "requires free-run state to hold under prefix/holdout.",
        "",
        "## Summary",
        "",
        f"- Decisions: `{s['decision_count']}`.",
        f"- Residual decisions: `{s['residual_decision_count']}`.",
        f"- Clean controls: `{s['clean_control_count']}`.",
        f"- Beam width: `{s['beam_width']}`.",
        f"- Context families: `{s['context_family_count']}`.",
        f"- Best teacher-forced context: `{s['best_teacher_context']}`.",
        f"- Best teacher-forced hits: `{s['best_teacher_total_hits']}/{s['decision_count']}` with `{s['best_teacher_residual_hits']}/{s['residual_decision_count']}` residual hits.",
        f"- Best free-run context: `{s['best_free_context']}`.",
        f"- Best free-run hits: `{s['best_free_total_hits']}/{s['best_free_total_total']}`.",
        f"- Best free-run residual hits: `{s['best_free_residual_hits']}/{s['best_free_residual_total']}`.",
        f"- Best free-run clean false changes: `{s['best_free_clean_false_changes']}`.",
        f"- Top-1 beam baseline hits: `{s['top1_total_hits']}/{s['decision_count']}` with `{s['top1_residual_hits']}/{s['residual_decision_count']}` residual hits.",
        f"- Prefix/holdout cover-all cells: `{s['prequential_cover_all_test_cells']}/{s['prequential_cells']}`.",
        f"- Prefix/holdout cover-all-residual cells: `{s['prequential_cover_all_residual_cells']}/{s['prequential_cells']}`.",
        f"- Prefix/holdout zero-clean-false-change cells: `{s['prequential_zero_clean_false_change_cells']}/{s['prequential_cells']}`.",
        f"- Best free-run net vs lookup: `{s['best_free_net_vs_lookup_bits']:.3f}` bits.",
        "",
        "## Free-Run Scoreboard",
        "",
        "| Context | Hits | Residual hits | Clean false changes | Contexts |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for row in result["free_run_scoreboard"]:
        lines.append(
            f"| `{row['context_name']}` | `{row['total_hits']}/{row['total_total']}` | "
            f"`{row['residual_hits']}/{row['residual_total']}` | "
            f"`{row['clean_false_changes']}` | `{row['context_count']}` |"
        )
    lines.extend(
        [
            "",
            "## Prefix/Holdout",
            "",
            "| Cutoff | Context | Test hits | Test residual hits | Test clean false changes | Oracle context |",
            "| ---: | --- | ---: | ---: | ---: | --- |",
        ]
    )
    for row in result["prequential_rows"]:
        lines.append(
            f"| `{row['cutoff_book']}` | `{row['selected_context']}` | "
            f"`{row['test_total_hits']}/{row['test_total']}` | "
            f"`{row['test_residual_hits']}/{row['test_residual_total']}` | "
            f"`{row['test_clean_false_changes']}` | `{row['oracle_context']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Promotes Markov state selector: `{s['promotes_markov_state_selector']}`.",
            f"- Weak Markov state selector clue: `{s['weak_markov_state_selector_clue']}`.",
            "- The free-run state selector does not become a parser rule. If it",
            "  cannot predict the next rank from its own previous rank under",
            "  holdout, it is just another fitted label table.",
            "- Compression bound is unchanged.",
            "- Row0 remains exogenous and unchanged.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
            "",
        ]
    )
    md_path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    write_result(make_result())
