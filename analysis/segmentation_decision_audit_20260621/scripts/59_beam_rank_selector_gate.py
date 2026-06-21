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
BEAM_SURVIVAL_SCRIPT = HERE / "scripts" / "58_beam_survival_budget_gate.py"
BEAM_SURVIVAL = TEST_RESULTS / "58_beam_survival_budget_gate.json"

OUT_STEM = "59_beam_rank_selector_gate"
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


def length_bucket(length: int) -> str:
    if length <= 1:
        return "le1"
    if length <= 3:
        return "le3"
    if length <= 5:
        return "le5"
    if length <= 8:
        return "le8"
    if length <= 13:
        return "le13"
    if length <= 20:
        return "le20"
    return "gt20"


def count_bucket(count: int) -> str:
    if count <= 5:
        return "le5"
    if count <= 10:
        return "le10"
    if count <= 20:
        return "le20"
    return "gt20"


def target_bucket(target_start: int) -> str:
    if target_start == 0:
        return "book_start"
    if target_start <= 20:
        return "early"
    if target_start <= 80:
        return "middle"
    return "late"


def op_shape(op: dict[str, Any] | None) -> str:
    if op is None:
        return "none"
    return f"{op['type']}:{length_bucket(int(op['length']))}"


def label_class(label: str) -> str:
    if "active_parser" in label:
        return "active"
    if "immediate_copy" in label:
        return "immediate_copy"
    if "literal_stop" in label:
        return "literal_stop"
    return "other"


def branch_shape(branch: dict[str, Any] | None) -> str:
    if branch is None:
        return "none"
    return f"{label_class(branch['label'])}:{op_shape(branch['op'])}"


def stable_rank_in_beam(
    gate22,
    decision: dict[str, Any],
    objective: str,
    beam_width: int,
) -> int:
    ranked = sorted(decision["branches"], key=gate22.OBJECTIVES[objective])
    beam = ranked[:beam_width]
    for index, branch in enumerate(beam, start=1):
        if branch["is_stable"]:
            return index
    raise RuntimeError(
        {
            "type": "stable_not_in_beam",
            "book": decision["book"],
            "target_start": decision["target_start"],
            "objective": objective,
            "beam_width": beam_width,
        }
    )


def selected_is_stable(row: dict[str, Any], rank: int) -> bool:
    beam_size = int(row["beam_size"])
    selected_rank = min(rank, beam_size)
    return selected_rank == int(row["stable_rank"])


def build_rows(gate22, decisions: list[dict[str, Any]], objective: str, beam_width: int) -> list[dict[str, Any]]:
    rows = []
    for decision in decisions:
        ranked = sorted(decision["branches"], key=gate22.OBJECTIVES[objective])
        beam = ranked[:beam_width]
        active = decision["active_op"]
        stable_rank = stable_rank_in_beam(gate22, decision, objective, beam_width)
        top1 = beam[0] if beam else None
        top2 = beam[1] if len(beam) > 1 else None
        rows.append(
            {
                "book": int(decision["book"]),
                "target_start": int(decision["target_start"]),
                "stable_index": int(decision["stable_index"]),
                "kind": decision["kind"],
                "drift_class": decision["drift_class"],
                "active_shape": op_shape(active),
                "active_type": active["type"],
                "active_length_bucket": length_bucket(int(active["length"])),
                "target_bucket": target_bucket(int(decision["target_start"])),
                "op_index_bucket": count_bucket(int(decision["stable_index"]) + 1),
                "branch_count_bucket": count_bucket(len(decision["branches"])),
                "beam_size": len(beam),
                "top1_shape": branch_shape(top1),
                "top2_shape": branch_shape(top2),
                "top1_type": None if top1 is None else top1["op"]["type"],
                "top1_label_class": "none" if top1 is None else label_class(top1["label"]),
                "stable_rank": stable_rank,
                "stable_op": decision["stable_op"],
                "active_op": active,
            }
        )
    return rows


ContextFn = Callable[[dict[str, Any]], str]


def context_families() -> dict[str, ContextFn]:
    return {
        "global": lambda row: "global",
        "active_type": lambda row: row["active_type"],
        "active_shape": lambda row: row["active_shape"],
        "position": lambda row: row["target_bucket"],
        "position_x_active_type": lambda row: (
            f"{row['target_bucket']}|{row['active_type']}"
        ),
        "position_x_active_shape": lambda row: (
            f"{row['target_bucket']}|{row['active_shape']}"
        ),
        "active_len_x_branch_count": lambda row: (
            f"{row['active_length_bucket']}|{row['branch_count_bucket']}"
        ),
        "op_index_x_active_shape": lambda row: (
            f"{row['op_index_bucket']}|{row['active_shape']}"
        ),
        "top1_shape": lambda row: row["top1_shape"],
        "top1_x_active_shape": lambda row: (
            f"{row['top1_shape']}|{row['active_shape']}"
        ),
        "top2_signature": lambda row: f"{row['top1_shape']}|{row['top2_shape']}",
        "beam_context_combo": lambda row: (
            f"{row['target_bucket']}|{row['active_shape']}|"
            f"{row['top1_shape']}|{row['branch_count_bucket']}"
        ),
    }


def majority_rank(rows: list[dict[str, Any]]) -> int:
    counts = Counter(int(row["stable_rank"]) for row in rows)
    return min(counts, key=lambda rank: (-counts[rank], rank))


def train_selector(rows: list[dict[str, Any]], context_name: str, context_fn: ContextFn) -> dict[str, Any]:
    fallback = majority_rank(rows)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[context_fn(row)].append(row)
    mapping = {context: majority_rank(values) for context, values in grouped.items()}
    return {
        "context_name": context_name,
        "fallback_rank": fallback,
        "mapping": mapping,
        "context_count": len(mapping),
    }


def evaluate_selector(
    rows: list[dict[str, Any]],
    selector: dict[str, Any],
    context_fn: ContextFn,
) -> dict[str, Any]:
    scored = []
    for row in rows:
        context = context_fn(row)
        rank = selector["mapping"].get(context, selector["fallback_rank"])
        hit = selected_is_stable(row, rank)
        scored.append(
            {
                "book": row["book"],
                "kind": row["kind"],
                "drift_class": row["drift_class"],
                "stable_rank": row["stable_rank"],
                "predicted_rank": rank,
                "hit": hit,
            }
        )
    residual = [row for row in scored if row["kind"] == "residual_first_drift"]
    clean = [row for row in scored if row["kind"] == "clean_control"]
    return {
        "context_name": selector["context_name"],
        "context_count": selector["context_count"],
        "total_hits": sum(1 for row in scored if row["hit"]),
        "total_total": len(scored),
        "residual_hits": sum(1 for row in residual if row["hit"]),
        "residual_total": len(residual),
        "clean_hits": sum(1 for row in clean if row["hit"]),
        "clean_total": len(clean),
        "clean_false_changes": sum(1 for row in clean if not row["hit"]),
        "unseen_contexts": sum(
            1
            for row in rows
            if context_fn(row) not in selector["mapping"]
        ),
        "residual_miss_books": [
            row["book"] for row in residual if not row["hit"]
        ],
        "clean_false_change_books_sample": sorted(
            {row["book"] for row in clean if not row["hit"]}
        )[:20],
        "rows": scored,
    }


def score_key(score: dict[str, Any]) -> tuple[Any, ...]:
    return (
        score["total_hits"],
        score["residual_hits"],
        -score["clean_false_changes"],
        -score["context_count"],
        score["context_name"],
    )


def prequential_rows(rows: list[dict[str, Any]], contexts: dict[str, ContextFn]) -> list[dict[str, Any]]:
    result = []
    for cutoff in PREFIX_CUTOFFS:
        train = [row for row in rows if row["book"] < cutoff]
        test = [row for row in rows if row["book"] >= cutoff]
        trained = [
            (
                name,
                fn,
                train_selector(train, name, fn),
            )
            for name, fn in contexts.items()
        ]
        train_scores = [
            evaluate_selector(train, selector, fn)
            for name, fn, selector in trained
        ]
        selected_score = max(train_scores, key=score_key)
        selected_name = selected_score["context_name"]
        selected_fn, selected_selector = next(
            (fn, selector)
            for name, fn, selector in trained
            if name == selected_name
        )
        test_score = evaluate_selector(test, selected_selector, selected_fn)
        oracle_scores = [
            evaluate_selector(test, selector, fn)
            for _name, fn, selector in trained
        ]
        oracle = max(oracle_scores, key=score_key)
        result.append(
            {
                "cutoff_book": cutoff,
                "selected_context": selected_name,
                "train_total_hits": selected_score["total_hits"],
                "train_total": selected_score["total_total"],
                "train_residual_hits": selected_score["residual_hits"],
                "train_residual_total": selected_score["residual_total"],
                "train_clean_false_changes": selected_score["clean_false_changes"],
                "test_total_hits": test_score["total_hits"],
                "test_total": test_score["total_total"],
                "test_residual_hits": test_score["residual_hits"],
                "test_residual_total": test_score["residual_total"],
                "test_clean_false_changes": test_score["clean_false_changes"],
                "test_unseen_contexts": test_score["unseen_contexts"],
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


def make_result() -> dict[str, Any]:
    gate58 = load_json(BEAM_SURVIVAL)
    assert_boundary("beam_survival_budget_gate", gate58)
    if gate58["classification"] != "beam_survival_weak_path_state_clue_not_promoted":
        raise RuntimeError("gate59 expects gate58 weak beam survival")

    gate22 = load_module("gate22_for_gate59", BRANCH_CONTINUATION_SCRIPT)
    gate58_module = load_module("gate58_for_gate59", BEAM_SURVIVAL_SCRIPT)
    decisions = gate22.collect_decisions()["decisions"]
    objective = gate58["summary"]["best_objective"]
    beam_width = int(gate58["summary"]["best_all_max_rank"])
    rows = build_rows(gate22, decisions, objective, beam_width)
    contexts = context_families()

    full_rows = []
    for name, fn in contexts.items():
        selector = train_selector(rows, name, fn)
        score = evaluate_selector(rows, selector, fn)
        score["mapping"] = selector["mapping"]
        full_rows.append(score)
    full_rows.sort(key=score_key, reverse=True)
    best = full_rows[0]
    preq = prequential_rows(rows, contexts)

    selector_id_bits = math.log2(len(contexts))
    correction_count = best["total_total"] - best["total_hits"]
    correction_site_bits = log2_comb(best["total_total"], correction_count)
    rank_label_bits = correction_count * math.log2(beam_width)
    full_fit_context_table_bits = best["context_count"] * math.log2(beam_width)
    optimistic_selector_bits = selector_id_bits + correction_site_bits + rank_label_bits
    full_fit_selector_bits = optimistic_selector_bits + full_fit_context_table_bits
    baseline_lookup_bits = float(gate58["summary"]["baseline_lookup_bits"])

    promotes = (
        best["total_hits"] == best["total_total"]
        and all(row["test_total_hits"] == row["test_total"] for row in preq)
    )
    weak = (
        best["total_hits"] > gate58["summary"]["best_clean_top1"]
        + gate58["summary"]["best_residual_top1"]
        and best["clean_false_changes"] <= 5
    )
    classification = (
        "beam_rank_selector_promoted"
        if promotes
        else "beam_rank_selector_weak_clue_not_promoted"
        if weak
        else "beam_rank_selector_rejected"
    )

    return {
        "schema": "beam_rank_selector_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "beam_survival_budget_gate": rel(BEAM_SURVIVAL),
            "residual_branch_continuation_script": rel(BRANCH_CONTINUATION_SCRIPT),
        },
        "scope": {
            "analysis_only": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "target_text_required": True,
            "stable_projection_used_as_label_only": True,
            "declared_literal_windows_granted": False,
            "source_free_digit_generator_emitted": False,
            "tests_beam_selector_not_beam_survival": True,
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
            "best_context": best["context_name"],
            "best_context_count": best["context_count"],
            "best_total_hits": best["total_hits"],
            "best_total_total": best["total_total"],
            "best_residual_hits": best["residual_hits"],
            "best_residual_total": best["residual_total"],
            "best_clean_false_changes": best["clean_false_changes"],
            "top1_total_hits": gate58["summary"]["best_clean_top1"]
            + gate58["summary"]["best_residual_top1"],
            "top1_residual_hits": gate58["summary"]["best_residual_top1"],
            "top1_clean_hits": gate58["summary"]["best_clean_top1"],
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
            "selector_id_bits": selector_id_bits,
            "full_fit_context_table_bits": full_fit_context_table_bits,
            "correction_count": correction_count,
            "optimistic_selector_bits_without_table": optimistic_selector_bits,
            "optimistic_selector_net_vs_lookup_bits": optimistic_selector_bits
            - baseline_lookup_bits,
            "full_fit_selector_bits_with_table_and_corrections": full_fit_selector_bits,
            "full_fit_selector_net_vs_lookup_bits": full_fit_selector_bits
            - baseline_lookup_bits,
            "baseline_lookup_bits": baseline_lookup_bits,
            "promotes_beam_rank_selector": promotes,
            "weak_beam_rank_selector_clue": weak,
            "interpretation": (
                "This gate tests the downstream selector required by gate58. "
                "It learns observable context-to-rank mappings inside the "
                "surviving width-5 beam and evaluates them under prefix/holdout."
            ),
        },
        "full_fit_scoreboard": [
            {
                key: value
                for key, value in row.items()
                if key not in {"rows", "mapping"}
            }
            for row in full_rows
        ],
        "best_mapping": best["mapping"],
        "prequential_rows": preq,
        "best_rows": best["rows"],
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": classification,
            "source_length_dependency_status": "beam_survival_selector_rejected"
            if not promotes
            else "beam_rank_selector_promoted",
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
        "# Beam Rank Selector Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 59 tests the selector that gate 58 left missing. Gate 58 showed",
        "that a width-5 beam can preserve the stable branch; this gate asks",
        "whether observable prefix-trained context mappings can choose the",
        "right rank inside that beam.",
        "",
        "## Summary",
        "",
        f"- Objective: `{s['objective']}`.",
        f"- Beam width: `{s['beam_width']}`.",
        f"- Decisions: `{s['decision_count']}`.",
        f"- Residual decisions: `{s['residual_decision_count']}`.",
        f"- Clean controls: `{s['clean_control_count']}`.",
        f"- Context families: `{s['context_family_count']}`.",
        f"- Best context: `{s['best_context']}`.",
        f"- Best total hits: `{s['best_total_hits']}/{s['best_total_total']}`.",
        f"- Best residual hits: `{s['best_residual_hits']}/{s['best_residual_total']}`.",
        f"- Best clean false changes: `{s['best_clean_false_changes']}`.",
        f"- Top-1 beam baseline: `{s['top1_total_hits']}/{s['decision_count']}` with `{s['top1_residual_hits']}/{s['residual_decision_count']}` residual hits.",
        f"- Prefix/holdout cover-all cells: `{s['prequential_cover_all_test_cells']}/{s['prequential_cells']}`.",
        f"- Prefix/holdout cover-all-residual cells: `{s['prequential_cover_all_residual_cells']}/{s['prequential_cells']}`.",
        f"- Prefix/holdout zero-clean-false-change cells: `{s['prequential_zero_clean_false_change_cells']}/{s['prequential_cells']}`.",
        f"- Optimistic selector without table cost: `{s['optimistic_selector_bits_without_table']:.3f}` bits.",
        f"- Optimistic selector net vs residual lookup: `{s['optimistic_selector_net_vs_lookup_bits']:.3f}` bits.",
        f"- Full-fit context table cost: `{s['full_fit_context_table_bits']:.3f}` bits.",
        f"- Full-fit selector with table/corrections: `{s['full_fit_selector_bits_with_table_and_corrections']:.3f}` bits.",
        f"- Full-fit selector net vs residual lookup: `{s['full_fit_selector_net_vs_lookup_bits']:.3f}` bits.",
        "",
        "## Full-Fit Scoreboard",
        "",
        "| Context | Hits | Residual hits | Clean false changes | Contexts |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for row in result["full_fit_scoreboard"][:12]:
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
            f"- Promotes beam rank selector: `{s['promotes_beam_rank_selector']}`.",
            f"- Weak beam rank selector clue: `{s['weak_beam_rank_selector_clue']}`.",
            "- The selector improves neither into an exact parser nor into a",
            "  stable replacement for residual lookup. The best full-fit context",
            "  resolves all residuals but changes clean controls; after paying",
            "  the context->rank table it is worse than lookup, and prefix/holdout",
            "  never covers every held-out test decision.",
            "- Compression bound is unchanged.",
            "- Row0 remains exogenous and unchanged.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
            "",
        ]
    )
    md_path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    write_result(make_result())
