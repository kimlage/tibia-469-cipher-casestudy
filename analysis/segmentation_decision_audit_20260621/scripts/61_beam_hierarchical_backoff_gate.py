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
BEAM_STABILITY = TEST_RESULTS / "60_beam_selector_stability_gate.json"

OUT_STEM = "61_beam_hierarchical_backoff_gate"
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


ContextFn = Callable[[dict[str, Any]], str]


def majority_rank(rows: list[dict[str, Any]]) -> int:
    if not rows:
        return 1
    counts = Counter(int(row["stable_rank"]) for row in rows)
    return min(counts, key=lambda rank: (-counts[rank], rank))


def hierarchy_families(gate59) -> dict[str, list[tuple[str, ContextFn]]]:
    ctx = gate59.context_families()
    return {
        "global_to_beam_combo": [
            ("global", ctx["global"]),
            ("active_type", ctx["active_type"]),
            ("active_shape", ctx["active_shape"]),
            ("beam_context_combo", ctx["beam_context_combo"]),
        ],
        "position_to_beam_combo": [
            ("global", ctx["global"]),
            ("position", ctx["position"]),
            ("position_x_active_type", ctx["position_x_active_type"]),
            ("position_x_active_shape", ctx["position_x_active_shape"]),
            ("beam_context_combo", ctx["beam_context_combo"]),
        ],
        "top_shape_to_beam_combo": [
            ("global", ctx["global"]),
            ("top1_shape", ctx["top1_shape"]),
            ("top1_x_active_shape", ctx["top1_x_active_shape"]),
            ("top2_signature", ctx["top2_signature"]),
            ("beam_context_combo", ctx["beam_context_combo"]),
        ],
        "active_branch_to_beam_combo": [
            ("global", ctx["global"]),
            ("active_type", ctx["active_type"]),
            ("active_len_x_branch_count", ctx["active_len_x_branch_count"]),
            ("op_index_x_active_shape", ctx["op_index_x_active_shape"]),
            ("beam_context_combo", ctx["beam_context_combo"]),
        ],
        "compact_top_signature": [
            ("global", ctx["global"]),
            ("top1_shape", ctx["top1_shape"]),
            ("top2_signature", ctx["top2_signature"]),
        ],
        "compact_position_active": [
            ("global", ctx["global"]),
            ("position_x_active_type", ctx["position_x_active_type"]),
            ("position_x_active_shape", ctx["position_x_active_shape"]),
        ],
    }


def train_backoff(
    rows: list[dict[str, Any]],
    family: str,
    levels: list[tuple[str, ContextFn]],
    min_support: int,
) -> dict[str, Any]:
    fallback = majority_rank(rows)
    trained_levels = []
    for level_name, fn in levels:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            grouped[fn(row)].append(row)
        mapping = {
            context: {
                "rank": majority_rank(values),
                "support": len(values),
            }
            for context, values in grouped.items()
            if len(values) >= min_support
        }
        trained_levels.append(
            {
                "level": level_name,
                "mapping": mapping,
            }
        )
    return {
        "family": family,
        "min_support": min_support,
        "fallback_rank": fallback,
        "levels": trained_levels,
    }


def select_rank(
    selector: dict[str, Any],
    levels: list[tuple[str, ContextFn]],
    row: dict[str, Any],
) -> tuple[int, str, int]:
    for trained, (_level_name, fn) in reversed(list(zip(selector["levels"], levels))):
        context = fn(row)
        match = trained["mapping"].get(context)
        if match is not None:
            return int(match["rank"]), trained["level"], int(match["support"])
    return int(selector["fallback_rank"]), "fallback", 0


def evaluate_selector(
    gate59,
    rows: list[dict[str, Any]],
    selector: dict[str, Any],
    levels: list[tuple[str, ContextFn]],
) -> dict[str, Any]:
    scored = []
    for row in rows:
        rank, level, support = select_rank(selector, levels, row)
        hit = gate59.selected_is_stable(row, rank)
        scored.append(
            {
                "book": row["book"],
                "kind": row["kind"],
                "drift_class": row["drift_class"],
                "stable_rank": row["stable_rank"],
                "predicted_rank": rank,
                "selected_level": level,
                "selected_support": support,
                "hit": hit,
            }
        )
    residual = [row for row in scored if row["kind"] == "residual_first_drift"]
    clean = [row for row in scored if row["kind"] == "clean_control"]
    context_count = sum(len(level["mapping"]) for level in selector["levels"])
    return {
        "family": selector["family"],
        "min_support": selector["min_support"],
        "context_count": context_count,
        "total_hits": sum(1 for row in scored if row["hit"]),
        "total_total": len(scored),
        "residual_hits": sum(1 for row in residual if row["hit"]),
        "residual_total": len(residual),
        "clean_hits": sum(1 for row in clean if row["hit"]),
        "clean_total": len(clean),
        "clean_false_changes": sum(1 for row in clean if not row["hit"]),
        "fallback_rows": sum(1 for row in scored if row["selected_level"] == "fallback"),
        "residual_miss_books": [
            row["book"] for row in residual if not row["hit"]
        ],
        "selected_level_counts": dict(
            sorted(Counter(row["selected_level"] for row in scored).items())
        ),
        "rows": scored,
    }


def score_cost(
    row: dict[str, Any],
    baseline_lookup_bits: float,
    beam_width: int,
    family_count: int,
    threshold_count: int,
) -> dict[str, Any]:
    correction_count = row["total_total"] - row["total_hits"]
    table_bits = row["context_count"] * math.log2(beam_width)
    selector_bits = math.log2(family_count) + math.log2(threshold_count)
    correction_bits = log2_comb(row["total_total"], correction_count)
    correction_rank_bits = correction_count * math.log2(beam_width)
    total_bits = selector_bits + table_bits + correction_bits + correction_rank_bits
    return {
        **{key: value for key, value in row.items() if key != "rows"},
        "selector_bits": selector_bits,
        "table_bits": table_bits,
        "correction_count": correction_count,
        "correction_bits": correction_bits,
        "correction_rank_bits": correction_rank_bits,
        "total_bits_with_table_and_corrections": total_bits,
        "net_vs_lookup_bits": total_bits - baseline_lookup_bits,
    }


def score_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        row["total_hits"],
        row["residual_hits"],
        -row["clean_false_changes"],
        -row["context_count"],
        -row["min_support"],
        row["family"],
    )


def full_fit_scoreboard(
    gate59,
    rows: list[dict[str, Any]],
    families: dict[str, list[tuple[str, ContextFn]]],
    baseline_lookup_bits: float,
    beam_width: int,
) -> list[dict[str, Any]]:
    scored = []
    for family, levels in families.items():
        for threshold in SUPPORT_THRESHOLDS:
            selector = train_backoff(rows, family, levels, threshold)
            score = evaluate_selector(gate59, rows, selector, levels)
            scored.append(
                score_cost(
                    score,
                    baseline_lookup_bits,
                    beam_width,
                    len(families),
                    len(SUPPORT_THRESHOLDS),
                )
            )
    scored.sort(key=score_key, reverse=True)
    return scored


def prequential_rows(
    gate59,
    rows: list[dict[str, Any]],
    families: dict[str, list[tuple[str, ContextFn]]],
) -> list[dict[str, Any]]:
    result = []
    for cutoff in PREFIX_CUTOFFS:
        train = [row for row in rows if row["book"] < cutoff]
        test = [row for row in rows if row["book"] >= cutoff]
        train_scores = []
        trained = []
        for family, levels in families.items():
            for threshold in SUPPORT_THRESHOLDS:
                selector = train_backoff(train, family, levels, threshold)
                score = evaluate_selector(gate59, train, selector, levels)
                train_scores.append(score)
                trained.append((family, levels, threshold, selector))
        selected = max(train_scores, key=score_key)
        selected_tuple = next(
            item
            for item in trained
            if item[0] == selected["family"] and item[2] == selected["min_support"]
        )
        _family, selected_levels, _threshold, selected_selector = selected_tuple
        test_score = evaluate_selector(gate59, test, selected_selector, selected_levels)
        oracle_scores = []
        for family, levels, threshold, selector in trained:
            score = evaluate_selector(gate59, test, selector, levels)
            oracle_scores.append(score)
        oracle = max(oracle_scores, key=score_key)
        result.append(
            {
                "cutoff_book": cutoff,
                "selected_family": selected["family"],
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
                "oracle_family": oracle["family"],
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


def make_result() -> dict[str, Any]:
    gate60 = load_json(BEAM_STABILITY)
    assert_boundary("beam_selector_stability_gate", gate60)
    if gate60["classification"] != "beam_selector_stability_weak_fullfit_not_promoted":
        raise RuntimeError("gate61 expects gate60 stability rejection")

    gate59 = load_module("gate59_for_gate61", BEAM_SELECTOR_SCRIPT)
    gate22 = load_module("gate22_for_gate61", BRANCH_CONTINUATION_SCRIPT)
    decisions = gate22.collect_decisions()["decisions"]
    objective = gate60["inputs"]["beam_rank_selector_gate"]
    gate59_json = load_json(TEST_RESULTS / "59_beam_rank_selector_gate.json")
    beam_objective = gate59_json["summary"]["objective"]
    beam_width = int(gate59_json["summary"]["beam_width"])
    rows = gate59.build_rows(gate22, decisions, beam_objective, beam_width)
    families = hierarchy_families(gate59)
    baseline_lookup_bits = float(gate59_json["summary"]["baseline_lookup_bits"])

    scoreboard = full_fit_scoreboard(
        gate59, rows, families, baseline_lookup_bits, beam_width
    )
    best = scoreboard[0]
    preq = prequential_rows(gate59, rows, families)
    promotes = (
        best["total_hits"] == best["total_total"]
        and best["net_vs_lookup_bits"] <= 0
        and all(row["test_total_hits"] == row["test_total"] for row in preq)
    )
    weak = (
        best["residual_hits"] >= gate60["summary"]["best_residual_hits"]
        and best["clean_false_changes"] <= gate60["summary"]["best_clean_false_changes"]
    )
    classification = (
        "beam_hierarchical_backoff_promoted"
        if promotes
        else "beam_hierarchical_backoff_weak_fullfit_not_promoted"
        if weak
        else "beam_hierarchical_backoff_rejected"
    )

    return {
        "schema": "beam_hierarchical_backoff_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "beam_selector_stability_gate": rel(BEAM_STABILITY),
            "beam_rank_selector_gate": gate60["inputs"]["beam_rank_selector_gate"],
        },
        "scope": {
            "analysis_only": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "target_text_required": True,
            "stable_projection_used_as_label_only": True,
            "declared_literal_windows_granted": False,
            "source_free_digit_generator_emitted": False,
            "tests_hierarchical_backoff_selector": True,
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
            "beam_objective": beam_objective,
            "beam_width": beam_width,
            "family_count": len(families),
            "support_thresholds": SUPPORT_THRESHOLDS,
            "best_family": best["family"],
            "best_min_support": best["min_support"],
            "best_total_hits": best["total_hits"],
            "best_total_total": best["total_total"],
            "best_residual_hits": best["residual_hits"],
            "best_residual_total": best["residual_total"],
            "best_clean_false_changes": best["clean_false_changes"],
            "best_context_count": best["context_count"],
            "best_net_vs_lookup_bits": best["net_vs_lookup_bits"],
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
            "promotes_hierarchical_backoff": promotes,
            "weak_hierarchical_backoff_clue": weak,
            "interpretation": (
                "Gate 61 tests whether hierarchical backoff over observable "
                "beam contexts can stabilize the gate59 selector without "
                "depending on singleton contexts."
            ),
        },
        "scoreboard": scoreboard,
        "prequential_rows": preq,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": classification,
            "source_length_dependency_status": "beam_hierarchical_backoff_not_promoted"
            if not promotes
            else "beam_hierarchical_backoff_promoted",
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
        "# Beam Hierarchical Backoff Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 61 tests whether hierarchical backoff over observable beam",
        "contexts can stabilize the gate-59 selector without relying on",
        "singleton `beam_context_combo` rows.",
        "",
        "## Summary",
        "",
        f"- Families tested: `{s['family_count']}`.",
        f"- Support thresholds: `{s['support_thresholds']}`.",
        f"- Best family: `{s['best_family']}`.",
        f"- Best min support: `{s['best_min_support']}`.",
        f"- Best total hits: `{s['best_total_hits']}/{s['best_total_total']}`.",
        f"- Best residual hits: `{s['best_residual_hits']}/{s['best_residual_total']}`.",
        f"- Best clean false changes: `{s['best_clean_false_changes']}`.",
        f"- Best context count: `{s['best_context_count']}`.",
        f"- Best net vs lookup: `{s['best_net_vs_lookup_bits']:.3f}` bits.",
        f"- Prefix/holdout cover-all cells: `{s['prequential_cover_all_test_cells']}/{s['prequential_cells']}`.",
        f"- Prefix/holdout cover-all-residual cells: `{s['prequential_cover_all_residual_cells']}/{s['prequential_cells']}`.",
        f"- Prefix/holdout zero-clean-false-change cells: `{s['prequential_zero_clean_false_change_cells']}/{s['prequential_cells']}`.",
        "",
        "## Scoreboard",
        "",
        "| Family | Min support | Hits | Residual hits | Clean false changes | Contexts | Net vs lookup |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in result["scoreboard"][:15]:
        lines.append(
            f"| `{row['family']}` | `{row['min_support']}` | "
            f"`{row['total_hits']}/{row['total_total']}` | "
            f"`{row['residual_hits']}/{row['residual_total']}` | "
            f"`{row['clean_false_changes']}` | `{row['context_count']}` | "
            f"`{row['net_vs_lookup_bits']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Prefix/Holdout",
            "",
            "| Cutoff | Family | Min support | Test hits | Test residual hits | Test clean false changes | Oracle family |",
            "| ---: | --- | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in result["prequential_rows"]:
        lines.append(
            f"| `{row['cutoff_book']}` | `{row['selected_family']}` | "
            f"`{row['selected_min_support']}` | "
            f"`{row['test_total_hits']}/{row['test_total']}` | "
            f"`{row['test_residual_hits']}/{row['test_residual_total']}` | "
            f"`{row['test_clean_false_changes']}` | `{row['oracle_family']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Promotes hierarchical backoff: `{s['promotes_hierarchical_backoff']}`.",
            f"- Weak hierarchical backoff clue: `{s['weak_hierarchical_backoff_clue']}`.",
            "- Hierarchical backoff does not turn the beam selector into a",
            "  promoted parser. Its best row ties the unstable full-fit table",
            "  and still needs support `1`; prefix/holdout does not cover all",
            "  held-out decisions.",
            "- Compression bound is unchanged.",
            "- Row0 remains exogenous and unchanged.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
            "",
        ]
    )
    md_path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    write_result(make_result())
