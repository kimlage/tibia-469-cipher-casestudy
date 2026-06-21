from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

GATE50_SCRIPT = HERE / "scripts" / "50_source_interval_context_gate.py"
GATE50_RESULT = TEST_RESULTS / "50_source_interval_context_gate.json"

OUT_STEM = "51_source_interval_precision_gate"
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


def op_key(op: dict[str, Any]) -> tuple[Any, ...]:
    return (op["type"], int(op["target_start"]), int(op["length"]), op.get("source"))


def active_branch(row: dict[str, Any]) -> dict[str, Any]:
    for branch in row["branches"]:
        if branch["branch"]["is_active"]:
            return branch
    raise RuntimeError("missing active branch")


def flatten_policy_features(
    source_module,
    base: dict[str, Any],
    policy: str,
) -> dict[str, Any]:
    chosen = source_module.choose(base, policy)
    active = active_branch(base)
    branch = chosen["branch"]
    active_op = base["active_op"]
    chosen_op = branch["op"]
    features = chosen["features"]
    copy_branch_count = sum(
        1 for item in base["branches"] if item["branch"]["op"]["type"] == "copy"
    )
    literal_branch_count = len(base["branches"]) - copy_branch_count
    radius = features.get("radius_features", {})
    out = {
        "book": int(base["book"]),
        "target_start": int(base["target_start"]),
        "stable_index": int(base["stable_index"]),
        "kind": base["kind"],
        "drift_class": base["drift_class"],
        "policy": policy,
        "chosen_is_stable": bool(branch["is_stable"]),
        "chosen_is_active": bool(branch["is_active"]),
        "chosen_type": chosen_op["type"],
        "active_type": active_op["type"],
        "chosen_is_copy": chosen_op["type"] == "copy",
        "active_is_copy": active_op["type"] == "copy",
        "changes_active": op_key(chosen_op) != op_key(active_op),
        "changes_type": chosen_op["type"] != active_op["type"],
        "changes_length": int(chosen_op["length"]) != int(active_op["length"]),
        "chosen_length": int(chosen_op["length"]),
        "active_length": int(active_op["length"]),
        "length_delta_abs": abs(int(chosen_op["length"]) - int(active_op["length"])),
        "branch_count": len(base["branches"]),
        "copy_branch_count": copy_branch_count,
        "literal_branch_count": literal_branch_count,
        "payload_occurrences": int(features["payload_occurrences"]),
        "source_target_start_distance": int(features["source_target_start_distance"]),
        "source_target_end_distance": int(features["source_target_end_distance"]),
        "source_target_interval_distance": int(
            features["source_target_interval_distance"]
        ),
        "max_source_context_recurrence": int(
            features["max_source_context_recurrence"]
        ),
        "min_source_context_recurrence": int(
            features["min_source_context_recurrence"]
        ),
    }
    for key in ["2", "4", "8"]:
        values = radius.get(key, {})
        out[f"r{key}_start_distance"] = int(values.get("start_distance", 10**9))
        out[f"r{key}_end_distance"] = int(values.get("end_distance", 10**9))
        out[f"r{key}_interval_distance"] = int(values.get("interval_distance", 10**9))
        out[f"r{key}_context_recurrence"] = int(
            values.get("start_recurrence", 0) + values.get("end_recurrence", 0)
        )
    return out


def build_rows() -> list[dict[str, Any]]:
    source_module = load_module("source_interval_for_gate51", GATE50_SCRIPT)
    base_rows = source_module.build_choice_rows()
    rows = []
    for base in base_rows:
        for policy in source_module.candidate_policy_names():
            rows.append(flatten_policy_features(source_module, base, policy))
    return rows


def make_predicates(rows: list[dict[str, Any]]) -> list[Predicate]:
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
        "policy",
        "chosen_type",
        "active_type",
        "chosen_is_copy",
        "active_is_copy",
        "changes_active",
        "changes_type",
        "changes_length",
        "drift_class",
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


def rows_for_policy(rows: list[dict[str, Any]], policy: str) -> list[dict[str, Any]]:
    return [row for row in rows if row["policy"] == policy]


def score_rule(rows: list[dict[str, Any]], predicate: Predicate) -> dict[str, Any]:
    name, fn = predicate
    selected = [row for row in rows if fn(row)]
    residual = [row for row in rows if row["kind"] == "residual_first_drift"]
    clean = [row for row in rows if row["kind"] == "clean_control"]
    residual_hits = sum(
        1 for row in selected if row["kind"] == "residual_first_drift" and row["chosen_is_stable"]
    )
    residual_false = sum(
        1
        for row in selected
        if row["kind"] == "residual_first_drift" and not row["chosen_is_stable"]
    )
    clean_false_changes = sum(
        1 for row in selected if row["kind"] == "clean_control" and not row["chosen_is_stable"]
    )
    clean_safe_selected = sum(
        1 for row in selected if row["kind"] == "clean_control" and row["chosen_is_stable"]
    )
    return {
        "predicate": name,
        "selected_count": len(selected),
        "residual_hits": residual_hits,
        "residual_false": residual_false,
        "residual_total": len(residual),
        "clean_false_changes": clean_false_changes,
        "clean_safe_selected": clean_safe_selected,
        "clean_total": len(clean),
        "residual_miss_books": [
            row["book"]
            for row in residual
            if not any(
                fn(candidate)
                and candidate["chosen_is_stable"]
                and candidate["book"] == row["book"]
                and candidate["stable_index"] == row["stable_index"]
                for candidate in selected
            )
        ],
    }


def score_key(score: dict[str, Any]) -> tuple[Any, ...]:
    return (
        score["residual_hits"],
        -score["clean_false_changes"],
        -score["residual_false"],
        -score["selected_count"],
        score["predicate"],
    )


def combine(left: Predicate, right: Predicate) -> Predicate:
    left_name, left_fn = left
    right_name, right_fn = right
    return (
        f"{left_name}__and__{right_name}",
        lambda row, left_fn=left_fn, right_fn=right_fn: left_fn(row) and right_fn(row),
    )


def score_policy_rules(
    all_rows: list[dict[str, Any]], policy: str, predicates: list[Predicate]
) -> list[dict[str, Any]]:
    rows = rows_for_policy(all_rows, policy)
    singles = [score_rule(rows, predicate) for predicate in predicates]
    top_predicates = [
        predicates[index]
        for index, _score in sorted(
            enumerate(singles), key=lambda item: score_key(item[1]), reverse=True
        )[:PAIR_CANDIDATE_LIMIT]
    ]
    pair_scores = []
    for i, left in enumerate(top_predicates):
        for right in top_predicates[i + 1 :]:
            pair_scores.append(score_rule(rows, combine(left, right)))
    out = singles + pair_scores
    for score in out:
        score["policy"] = policy
    return out


def full_scoreboard(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[Predicate]]:
    predicates = make_predicates(rows)
    policies = sorted({row["policy"] for row in rows})
    scores = []
    for policy in policies:
        scores.extend(score_policy_rules(rows, policy, predicates))
    scores.sort(key=score_key, reverse=True)
    return scores, predicates


def prequential(rows: list[dict[str, Any]], predicates: list[Predicate]) -> list[dict[str, Any]]:
    out = []
    policies = sorted({row["policy"] for row in rows})
    for cutoff in PREFIX_CUTOFFS:
        train = [row for row in rows if row["book"] < cutoff]
        test = [row for row in rows if row["book"] >= cutoff]
        train_scores = []
        for policy in policies:
            policy_rows = rows_for_policy(train, policy)
            for predicate in predicates:
                score = score_rule(policy_rows, predicate)
                score["policy"] = policy
                train_scores.append(score)
        selected = max(train_scores, key=score_key)
        test_policy_rows = rows_for_policy(test, selected["policy"])
        selected_predicate = next(
            predicate
            for predicate in predicates
            if predicate[0] == selected["predicate"]
        )
        test_score = score_rule(test_policy_rows, selected_predicate)
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
    gate50 = load_json(GATE50_RESULT)
    assert_boundary("source_interval_context_gate", gate50)
    if gate50["classification"] != "source_interval_context_weak_clue_not_promoted":
        raise RuntimeError("gate51 expects gate50 weak-clue state")
    rows = build_rows()
    scoreboard, predicates = full_scoreboard(rows)
    best = scoreboard[0]
    zero_fp = [row for row in scoreboard if row["clean_false_changes"] == 0]
    best_zero_fp = zero_fp[0] if zero_fp else None
    preq = prequential(rows, predicates)
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
        classification = "source_interval_precision_rule_promoted"
    elif best_zero_fp is not None and best_zero_fp["residual_hits"] > 0:
        classification = "source_interval_precision_weak_clue_not_promoted"
    else:
        classification = "source_interval_precision_rejected"
    return {
        "schema": "source_interval_precision_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "source_interval_context_gate": rel(GATE50_RESULT),
            "source_interval_context_script": rel(GATE50_SCRIPT),
        },
        "scope": {
            "analysis_only": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "target_text_required": True,
            "source_free_digit_generator_emitted": False,
            "promotes_parser_rule": promotes,
            "tests_precision_gating_of_source_interval_signal": True,
        },
        "summary": {
            "decision_policy_rows": len(rows),
            "policy_count": len({row["policy"] for row in rows}),
            "predicate_count": len(predicates),
            "scored_rule_count": len(scoreboard),
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
            "promotes_source_interval_precision_rule": promotes,
            "interpretation": (
                "Gate 51 asks whether the gate-50 source-interval weak clue "
                "can be converted into a precise repair rule by observable "
                "predicates. Full-fit pair predicates are diagnostic; "
                "prequential selection uses single predicates to avoid "
                "smuggling residual-site lookup."
            ),
        },
        "scoreboard_top": scoreboard[:30],
        "best_zero_fp_score": best_zero_fp,
        "prequential_rows": preq,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": classification,
            "source_length_dependency_status": "source_interval_precision_tested",
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
        "# Source Interval Precision Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 51 tests whether the gate-50 source-interval weak clue can",
        "be made precise. A source-interval policy may repair a decision",
        "only when an observable predicate fires; otherwise the active",
        "parser branch is retained.",
        "",
        "## Summary",
        "",
        f"- Policy-decision rows: `{s['decision_policy_rows']}`.",
        f"- Policies: `{s['policy_count']}`.",
        f"- Predicates: `{s['predicate_count']}`.",
        f"- Scored rules: `{s['scored_rule_count']}`.",
        f"- Best rule: `{s['best_policy']}` / `{s['best_predicate']}`.",
        f"- Best residual hits: `{s['best_residual_hits']}/{s['best_residual_total']}`.",
        f"- Best clean false changes: `{s['best_clean_false_changes']}`.",
        f"- Best residual false repairs: `{s['best_residual_false']}`.",
        f"- Best zero-FP rule: `{s['best_zero_fp_policy']}` / `{s['best_zero_fp_predicate']}`.",
        f"- Best zero-FP residual hits: `{s['best_zero_fp_residual_hits']}/{s['best_zero_fp_residual_total']}`.",
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
            f"- Promotes source-interval precision rule: `{s['promotes_source_interval_precision_rule']}`.",
            f"- Prequential cover-all-residual cells: `{s['prequential_cover_all_residual_cells']}/{s['prequential_cells_with_residuals']}`.",
            f"- Prequential zero-clean-false-change cells: `{s['prequential_zero_clean_false_change_cells']}/{s['prequential_cells']}`.",
            f"- {s['interpretation']}",
            "- The source-interval signal does not convert into a clean parser rule.",
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
