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
LATENT_LOOKUP = TEST_RESULTS / "41_latent_state_lookup_cost_gate.json"
BEAM_HIERARCHICAL_BACKOFF = TEST_RESULTS / "61_beam_hierarchical_backoff_gate.json"

OUT_STEM = "62_residual_patch_program_gate"
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


def delta_bucket(delta: int) -> str:
    if delta == 0:
        return "same"
    sign = "plus" if delta > 0 else "minus"
    value = abs(delta)
    if value <= 1:
        return f"{sign}1"
    if value <= 3:
        return f"{sign}le3"
    if value <= 8:
        return f"{sign}le8"
    if value <= 20:
        return f"{sign}le20"
    return f"{sign}gt20"


def source_relation(active: dict[str, Any], stable: dict[str, Any]) -> str:
    active_source = active.get("source")
    stable_source = stable.get("source")
    if stable_source is None:
        return "stable_no_source"
    if active_source is None:
        return "source_introduced"
    if int(active_source) == int(stable_source):
        return "same_source"
    return "source_changed"


def patch_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for row in rows:
        active = row["active_op"]
        stable = row["stable_op"]
        length_delta = int(stable["length"]) - int(active["length"])
        macro = row["drift_class"]
        coarse = (
            f"{macro}|active={active['type']}:{length_bucket(int(active['length']))}|"
            f"stable={stable['type']}:{length_bucket(int(stable['length']))}"
        )
        delta = (
            f"{macro}|delta={delta_bucket(length_delta)}|"
            f"source={source_relation(active, stable)}"
        )
        exact = (
            f"{macro}|stable={stable['type']}:{int(stable['length'])}:"
            f"{stable.get('source')}|rank={row['stable_rank']}"
        )
        result.append(
            {
                "book": row["book"],
                "target_start": row["target_start"],
                "drift_class": row["drift_class"],
                "stable_rank": row["stable_rank"],
                "active_shape": row["active_shape"],
                "top1_shape": row["top1_shape"],
                "top2_shape": row["top2_shape"],
                "active_op": active,
                "stable_op": stable,
                "patch_labels": {
                    "macro": macro,
                    "coarse_shape": coarse,
                    "delta_shape": delta,
                    "exact_patch": exact,
                },
            }
        )
    return result


def label_stats(rows: list[dict[str, Any]], mode: str) -> dict[str, Any]:
    counts = Counter(row["patch_labels"][mode] for row in rows)
    return {
        "mode": mode,
        "distinct_labels": len(counts),
        "counts": dict(sorted(counts.items())),
        "largest_class": max(counts.values()) if counts else 0,
        "singletons": sum(1 for value in counts.values() if value == 1),
    }


def universe_cost(
    decision_count: int,
    residual_count: int,
    label_count: int,
    mode_count: int,
) -> dict[str, float]:
    mode_bits = math.log2(mode_count)
    site_bits = log2_comb(decision_count, residual_count)
    label_bits = residual_count * math.log2(max(label_count, 1))
    total = mode_bits + site_bits + label_bits
    return {
        "mode_bits": mode_bits,
        "site_bits": site_bits,
        "label_bits": label_bits,
        "total_bits": total,
    }


Predicate = Callable[[dict[str, Any]], bool]


def predicate_families() -> dict[str, Predicate]:
    return {
        "book_start": lambda row: int(row["target_start"]) == 0,
        "internal": lambda row: int(row["target_start"]) > 0,
        "active_literal": lambda row: row["active_op"]["type"] == "literal",
        "active_copy": lambda row: row["active_op"]["type"] == "copy",
        "top1_copy": lambda row: row["top1_shape"].startswith("immediate_copy:copy"),
        "top1_literal": lambda row: row["top1_shape"].startswith("literal_stop:literal"),
        "active_literal_le3": lambda row: (
            row["active_op"]["type"] == "literal" and int(row["active_op"]["length"]) <= 3
        ),
        "active_literal_le8": lambda row: (
            row["active_op"]["type"] == "literal" and int(row["active_op"]["length"]) <= 8
        ),
        "active_copy_le8": lambda row: (
            row["active_op"]["type"] == "copy" and int(row["active_op"]["length"]) <= 8
        ),
        "target_early_le25": lambda row: int(row["target_start"]) <= 25,
        "target_late_gt50": lambda row: int(row["target_start"]) > 50,
    }


def make_rules(predicates: dict[str, Predicate]) -> list[tuple[str, Predicate]]:
    rules: list[tuple[str, Predicate]] = [("always", lambda row: True)]
    items = list(predicates.items())
    rules.extend(items)
    for i, (left_name, left_fn) in enumerate(items):
        for right_name, right_fn in items[i + 1 :]:
            rules.append(
                (
                    f"{left_name}__and__{right_name}",
                    lambda row, left_fn=left_fn, right_fn=right_fn: (
                        left_fn(row) and right_fn(row)
                    ),
                )
            )
    return rules


def evaluate_detector(
    rows: list[dict[str, Any]],
    rule_name: str,
    rule_fn: Predicate,
) -> dict[str, Any]:
    scored = []
    for row in rows:
        predicted = rule_fn(row)
        actual = row["kind"] == "residual_first_drift"
        scored.append(
            {
                "book": row["book"],
                "kind": row["kind"],
                "predicted": predicted,
                "actual": actual,
                "hit": predicted == actual,
            }
        )
    tp = sum(1 for row in scored if row["predicted"] and row["actual"])
    fp = sum(1 for row in scored if row["predicted"] and not row["actual"])
    fn = sum(1 for row in scored if not row["predicted"] and row["actual"])
    return {
        "rule": rule_name,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": None if tp + fp == 0 else tp / (tp + fp),
        "recall": None if tp + fn == 0 else tp / (tp + fn),
        "predicted_count": tp + fp,
        "scored_rows": scored,
    }


def detector_score_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (row["tp"], -row["fp"], -row["fn"], row["rule"])


def clean_detector_score_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (-row["fp"], row["tp"], -row["fn"], row["rule"])


def best_detector(rows: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    rules = make_rules(predicate_families())
    scored = [evaluate_detector(rows, name, fn) for name, fn in rules]
    scored.sort(key=detector_score_key, reverse=True)
    return scored[0], scored


def prequential_detector_rows(
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rules = make_rules(predicate_families())
    results = []
    for cutoff in PREFIX_CUTOFFS:
        train = [row for row in rows if row["book"] < cutoff]
        test = [row for row in rows if row["book"] >= cutoff]
        train_scores = [evaluate_detector(train, name, fn) for name, fn in rules]
        train_scores.sort(key=detector_score_key, reverse=True)
        selected = train_scores[0]
        selected_fn = dict(rules)[selected["rule"]]
        test_score = evaluate_detector(test, selected["rule"], selected_fn)
        results.append(
            {
                "cutoff_book": cutoff,
                "selected_rule": selected["rule"],
                "train_tp": selected["tp"],
                "train_fp": selected["fp"],
                "train_fn": selected["fn"],
                "test_tp": test_score["tp"],
                "test_fp": test_score["fp"],
                "test_fn": test_score["fn"],
                "test_residual_total": sum(
                    1 for row in test if row["kind"] == "residual_first_drift"
                ),
                "test_clean_total": sum(
                    1 for row in test if row["kind"] == "clean_control"
                ),
            }
        )
    return results


def make_result() -> dict[str, Any]:
    gate58 = load_json(BEAM_SURVIVAL)
    gate41 = load_json(LATENT_LOOKUP)
    gate61 = load_json(BEAM_HIERARCHICAL_BACKOFF)
    assert_boundary("beam_survival_budget_gate", gate58)
    assert_boundary("latent_state_lookup_cost_gate", gate41)
    assert_boundary("beam_hierarchical_backoff_gate", gate61)
    if gate61["classification"] != "beam_hierarchical_backoff_weak_fullfit_not_promoted":
        raise RuntimeError("gate62 expects gate61 to leave selector unpromoted")

    gate22 = load_module("gate22_for_gate62", BRANCH_CONTINUATION_SCRIPT)
    gate59 = load_module("gate59_for_gate62", BEAM_SELECTOR_SCRIPT)
    decisions = gate22.collect_decisions()["decisions"]
    objective = gate58["summary"]["best_objective"]
    beam_width = int(gate58["summary"]["best_all_max_rank"])
    rows = gate59.build_rows(gate22, decisions, objective, beam_width)
    residual_rows = [row for row in rows if row["kind"] == "residual_first_drift"]
    clean_rows = [row for row in rows if row["kind"] == "clean_control"]
    patches = patch_rows(residual_rows)
    label_modes = ["macro", "coarse_shape", "delta_shape", "exact_patch"]
    label_scoreboard = [label_stats(patches, mode) for mode in label_modes]
    baseline_lookup_bits = float(gate41["summary"]["first_drift_lookup_lower_bound_bits"])
    cost_rows = []
    for row in label_scoreboard:
        costs = universe_cost(
            len(rows),
            len(residual_rows),
            int(row["distinct_labels"]),
            len(label_modes),
        )
        cost_rows.append(
            {
                **row,
                **costs,
                "net_vs_lookup_bits": costs["total_bits"] - baseline_lookup_bits,
            }
        )
    cost_rows.sort(key=lambda row: (row["total_bits"], row["distinct_labels"], row["mode"]))
    best_cost = cost_rows[0]

    detector, detector_rows = best_detector(rows)
    zero_fp = max(
        (row for row in detector_rows if row["fp"] == 0),
        key=lambda row: (row["tp"], -row["fn"], row["rule"]),
        default=None,
    )
    clean_first_detector = max(detector_rows, key=clean_detector_score_key)
    preq = prequential_detector_rows(rows)
    detector_site_bits = log2_comb(len(rows), detector["fp"] + detector["fn"])
    detector_error_bits = detector_site_bits + (detector["fp"] + detector["fn"])
    detector_total_bits = (
        math.log2(len(detector_rows))
        + detector_error_bits
        + len(residual_rows) * math.log2(max(best_cost["distinct_labels"], 1))
    )

    promotes = (
        detector["tp"] == len(residual_rows)
        and detector["fp"] == 0
        and best_cost["total_bits"] < baseline_lookup_bits
        and all(row["test_fp"] == 0 and row["test_fn"] == 0 for row in preq)
    )
    weak_macro = best_cost["distinct_labels"] < len(residual_rows)
    classification = (
        "residual_patch_program_promoted"
        if promotes
        else "residual_patch_program_weak_macro_not_promoted"
        if weak_macro
        else "residual_patch_program_rejected"
    )

    return {
        "schema": "residual_patch_program_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "beam_hierarchical_backoff_gate": rel(BEAM_HIERARCHICAL_BACKOFF),
            "latent_lookup_cost_gate": rel(LATENT_LOOKUP),
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
            "tests_patch_program_not_bit_sweep": True,
            "promotes_parser_rule": promotes,
        },
        "summary": {
            "decision_count": len(rows),
            "residual_decision_count": len(residual_rows),
            "clean_control_count": len(clean_rows),
            "label_modes": label_modes,
            "best_patch_mode": best_cost["mode"],
            "best_patch_distinct_labels": best_cost["distinct_labels"],
            "best_patch_singletons": best_cost["singletons"],
            "best_patch_largest_class": best_cost["largest_class"],
            "best_patch_total_bits": best_cost["total_bits"],
            "best_patch_net_vs_lookup_bits": best_cost["net_vs_lookup_bits"],
            "site_bits": best_cost["site_bits"],
            "baseline_lookup_bits": baseline_lookup_bits,
            "detector_rule_count": len(detector_rows),
            "best_detector_rule": detector["rule"],
            "best_detector_tp": detector["tp"],
            "best_detector_fp": detector["fp"],
            "best_detector_fn": detector["fn"],
            "best_detector_precision": detector["precision"],
            "best_detector_recall": detector["recall"],
            "best_zero_fp_detector_rule": None if zero_fp is None else zero_fp["rule"],
            "best_zero_fp_detector_tp": 0 if zero_fp is None else zero_fp["tp"],
            "best_zero_fp_detector_fn": len(residual_rows)
            if zero_fp is None
            else zero_fp["fn"],
            "clean_first_detector_rule": clean_first_detector["rule"],
            "clean_first_detector_tp": clean_first_detector["tp"],
            "clean_first_detector_fp": clean_first_detector["fp"],
            "clean_first_detector_fn": clean_first_detector["fn"],
            "detector_total_bits_with_patch_labels": detector_total_bits,
            "detector_net_vs_lookup_bits": detector_total_bits - baseline_lookup_bits,
            "prequential_cells": len(preq),
            "prequential_zero_fp_cells": sum(1 for row in preq if row["test_fp"] == 0),
            "prequential_zero_fn_cells": sum(1 for row in preq if row["test_fn"] == 0),
            "prequential_exact_detector_cells": sum(
                1 for row in preq if row["test_fp"] == 0 and row["test_fn"] == 0
            ),
            "promotes_patch_program": promotes,
            "weak_macro_patch_clue": weak_macro,
            "interpretation": (
                "This gate asks whether the remaining residual decisions form a "
                "compact patch program rather than ten unrelated stable labels. "
                "Patch labels compress into a few macro classes, but applying "
                "them still requires locating residual sites."
            ),
        },
        "patch_label_scoreboard": cost_rows,
        "best_detector": {
            key: value for key, value in detector.items() if key != "scored_rows"
        },
        "detector_scoreboard_by_residual_coverage": [
            {key: value for key, value in row.items() if key != "scored_rows"}
            for row in detector_rows[:20]
        ],
        "detector_scoreboard_by_clean_priority": [
            {key: value for key, value in row.items() if key != "scored_rows"}
            for row in sorted(detector_rows, key=clean_detector_score_key, reverse=True)[
                :20
            ]
        ],
        "prequential_rows": preq,
        "residual_patch_rows": patches,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": classification,
            "source_length_dependency_status": "patch_macro_weak_site_lookup_not_removed",
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
        "# Residual Patch Program Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 62 tests whether the remaining residual branch choices compress",
        "into a small mechanical patch program. This is not another bit sweep:",
        "it separates patch-label compression from the harder question of where",
        "the patches apply.",
        "",
        "## Summary",
        "",
        f"- Decisions: `{s['decision_count']}`.",
        f"- Residual decisions: `{s['residual_decision_count']}`.",
        f"- Clean controls: `{s['clean_control_count']}`.",
        f"- Best patch mode: `{s['best_patch_mode']}`.",
        f"- Best patch distinct labels: `{s['best_patch_distinct_labels']}`.",
        f"- Best patch singletons: `{s['best_patch_singletons']}`.",
        f"- Best patch largest class: `{s['best_patch_largest_class']}`.",
        f"- Site bits alone: `{s['site_bits']:.3f}`.",
        f"- Best patch program bits: `{s['best_patch_total_bits']:.3f}`.",
        f"- Best patch net vs lookup: `{s['best_patch_net_vs_lookup_bits']:.3f}` bits.",
        f"- Best detector rule: `{s['best_detector_rule']}`.",
        f"- Best detector TP/FP/FN: `{s['best_detector_tp']}/{s['best_detector_fp']}/{s['best_detector_fn']}`.",
        f"- Best zero-FP detector: `{s['best_zero_fp_detector_rule']}` with `{s['best_zero_fp_detector_tp']}` residual hits.",
        f"- Clean-first detector: `{s['clean_first_detector_rule']}` with TP/FP/FN `{s['clean_first_detector_tp']}/{s['clean_first_detector_fp']}/{s['clean_first_detector_fn']}`.",
        f"- Detector+patch net vs lookup: `{s['detector_net_vs_lookup_bits']:.3f}` bits.",
        f"- Prefix/holdout exact detector cells: `{s['prequential_exact_detector_cells']}/{s['prequential_cells']}`.",
        "",
        "## Patch Label Scoreboard",
        "",
        "| Mode | Labels | Singletons | Largest class | Total bits | Net vs lookup |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in result["patch_label_scoreboard"]:
        lines.append(
            f"| `{row['mode']}` | `{row['distinct_labels']}` | "
            f"`{row['singletons']}` | `{row['largest_class']}` | "
            f"`{row['total_bits']:.3f}` | `{row['net_vs_lookup_bits']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Prefix/Holdout Detector",
            "",
            "| Cutoff | Rule | Test TP | Test FP | Test FN |",
            "| ---: | --- | ---: | ---: | ---: |",
        ]
    )
    for row in result["prequential_rows"]:
        lines.append(
            f"| `{row['cutoff_book']}` | `{row['selected_rule']}` | "
            f"`{row['test_tp']}` | `{row['test_fp']}` | `{row['test_fn']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Promotes patch program: `{s['promotes_patch_program']}`.",
            f"- Weak macro-patch clue: `{s['weak_macro_patch_clue']}`.",
            "- The residuals do compress into a few macro patch classes, but",
            "  the site-selection cost dominates. Even the cheapest paid patch",
            "  program is worse than the residual lookup lower bound, and the",
            "  best observable detector has false positives/false negatives.",
            "- This is a useful decomposition of the blocker, not a parser rule.",
            "- Compression bound is unchanged.",
            "- Row0 remains exogenous and unchanged.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
            "",
        ]
    )
    md_path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    write_result(make_result())
