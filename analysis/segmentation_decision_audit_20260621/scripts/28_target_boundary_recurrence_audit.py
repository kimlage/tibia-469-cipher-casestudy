from __future__ import annotations

import importlib.util
import json
import random
from collections import Counter
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
BRANCH_CONTINUATION_SCRIPT = HERE / "scripts" / "22_residual_branch_continuation_audit.py"
TREE_POLICY = TEST_RESULTS / "27_observable_decision_tree_policy_audit.json"

OUT_STEM = "28_target_boundary_recurrence_audit"
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
RADII = [2, 3, 4, 6, 8]
RANDOM_CONTROLS = 200
RANDOM_SEED = 46920260621


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


def load_books() -> dict[int, str]:
    return {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}


def substring_counts(books: dict[int, str], book_ids: list[int], lengths: set[int]) -> dict[int, Counter[str]]:
    counts: dict[int, Counter[str]] = {length: Counter() for length in lengths}
    for book_id in book_ids:
        text = books[book_id]
        for length in lengths:
            if length <= 0 or len(text) < length:
                continue
            for pos in range(0, len(text) - length + 1):
                counts[length][text[pos : pos + length]] += 1
    return counts


def branch_boundary(branch: dict[str, Any]) -> int:
    return int(branch["op"]["target_start"]) + int(branch["op"]["length"])


def boundary_features(
    books: dict[int, str],
    counts: dict[int, Counter[str]],
    decision: dict[str, Any],
    branch: dict[str, Any],
) -> dict[str, Any]:
    text = books[int(decision["book"])]
    boundary = branch_boundary(branch)
    values: dict[str, Any] = {
        "boundary": boundary,
        "at_book_start": boundary == 0,
        "at_book_end": boundary == len(text),
    }
    for radius in RADII:
        left = text[max(0, boundary - radius) : boundary]
        right = text[boundary : min(len(text), boundary + radius)]
        around = text[max(0, boundary - radius) : min(len(text), boundary + radius)]
        values[f"left_{radius}_count"] = counts.get(len(left), Counter()).get(left, 0) if len(left) == radius else 0
        values[f"right_{radius}_count"] = counts.get(len(right), Counter()).get(right, 0) if len(right) == radius else 0
        values[f"around_{radius}_count"] = (
            counts.get(len(around), Counter()).get(around, 0)
            if len(around) == 2 * radius
            else 0
        )
    return values


def policy_functions() -> dict[str, Callable[[dict[str, Any]], tuple[Any, ...]]]:
    out: dict[str, Callable[[dict[str, Any]], tuple[Any, ...]]] = {}
    for radius in RADII:
        out[f"max_around_r{radius}"] = (
            lambda row, radius=radius: (
                row["features"][f"around_{radius}_count"],
                row["features"][f"left_{radius}_count"]
                + row["features"][f"right_{radius}_count"],
                row["branch"]["is_active"],
                -int(row["branch"]["op"]["length"]),
                row["branch"]["label"],
            )
        )
        out[f"max_left_right_r{radius}"] = (
            lambda row, radius=radius: (
                row["features"][f"left_{radius}_count"]
                + row["features"][f"right_{radius}_count"],
                row["features"][f"around_{radius}_count"],
                row["branch"]["is_active"],
                -int(row["branch"]["op"]["length"]),
                row["branch"]["label"],
            )
        )
    out["multi_radius_sum"] = lambda row: (
        sum(row["features"][f"around_{radius}_count"] for radius in RADII)
        + sum(
            row["features"][f"left_{radius}_count"]
            + row["features"][f"right_{radius}_count"]
            for radius in RADII
        ),
        row["branch"]["is_active"],
        -int(row["branch"]["op"]["length"]),
        row["branch"]["label"],
    )
    out["prefer_active_control"] = lambda row: (
        row["branch"]["is_active"],
        row["branch"]["label"],
    )
    return out


def recurrence_policy_names() -> list[str]:
    return [name for name in policy_functions() if name != "prefer_active_control"]


def choice_rows(
    books: dict[int, str],
    counts: dict[int, Counter[str]],
    decisions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for decision in decisions:
        branch_rows = []
        for branch in decision["branches"]:
            branch_rows.append(
                {
                    "book": decision["book"],
                    "kind": decision["kind"],
                    "branch": branch,
                    "features": boundary_features(books, counts, decision, branch),
                }
            )
        rows.append({"decision": decision, "branches": branch_rows})
    return rows


def choose_policy(row: dict[str, Any], policy: str) -> dict[str, Any]:
    fn = policy_functions()[policy]
    return max(row["branches"], key=fn)


def score_policy(rows: list[dict[str, Any]], policy: str) -> dict[str, Any]:
    selected = []
    for row in rows:
        chosen = choose_policy(row, policy)
        decision = row["decision"]
        selected.append(
            {
                "book": decision["book"],
                "kind": decision["kind"],
                "chosen_is_stable": chosen["branch"]["is_stable"],
                "chosen_is_active": chosen["branch"]["is_active"],
                "chosen_label": chosen["branch"]["label"],
                "boundary": chosen["features"]["boundary"],
            }
        )
    residual = [row for row in selected if row["kind"] == "residual_first_drift"]
    clean = [row for row in selected if row["kind"] == "clean_control"]
    return {
        "policy": policy,
        "total_hits": sum(1 for row in selected if row["chosen_is_stable"]),
        "total_total": len(selected),
        "residual_hits": sum(1 for row in residual if row["chosen_is_stable"]),
        "residual_total": len(residual),
        "clean_false_changes": sum(1 for row in clean if not row["chosen_is_stable"]),
        "clean_total": len(clean),
        "residual_miss_books": [
            row["book"] for row in residual if not row["chosen_is_stable"]
        ],
        "selected_label_counts": dict(
            sorted(Counter(row["chosen_label"] for row in selected).items())
        ),
    }


def score_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        row["total_hits"],
        row["residual_hits"],
        -row["clean_false_changes"],
        row["policy"],
    )


def full_fit_scoreboard(
    rows: list[dict[str, Any]],
    policies: list[str] | None = None,
) -> list[dict[str, Any]]:
    if policies is None:
        policies = list(policy_functions())
    scores = [score_policy(rows, policy) for policy in policies]
    return sorted(scores, key=lambda row: (-row["total_hits"], -row["residual_hits"], row["clean_false_changes"], row["policy"]))


def prequential_rows(
    books: dict[int, str],
    decisions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for cutoff in PREFIX_CUTOFFS:
        train_decisions = [row for row in decisions if row["book"] < cutoff]
        test_decisions = [row for row in decisions if row["book"] >= cutoff]
        counts = substring_counts(
            books,
            list(range(cutoff)),
            {radius for radius in RADII} | {2 * radius for radius in RADII},
        )
        train_rows = choice_rows(books, counts, train_decisions)
        test_rows = choice_rows(books, counts, test_decisions)
        train_scores = full_fit_scoreboard(train_rows, recurrence_policy_names())
        selected = train_scores[0]
        test_score = score_policy(test_rows, selected["policy"])
        oracle = full_fit_scoreboard(test_rows, recurrence_policy_names())[0]
        rows.append(
            {
                "cutoff_book": cutoff,
                "selected_policy": selected["policy"],
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
                "test_residual_miss_books": test_score["residual_miss_books"],
                "oracle_policy": oracle["policy"],
                "oracle_test_total_hits": oracle["total_hits"],
                "oracle_test_residual_hits": oracle["residual_hits"],
                "oracle_test_clean_false_changes": oracle["clean_false_changes"],
                "selected_matches_oracle_total_hits": (
                    test_score["total_hits"] == oracle["total_hits"]
                ),
            }
        )
    return rows


def random_boundary_control(
    books: dict[int, str],
    counts: dict[int, Counter[str]],
    decisions: list[dict[str, Any]],
    real_best: dict[str, Any],
) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED)
    policies = recurrence_policy_names()
    total_hits: list[int] = []
    residual_hits: list[int] = []
    clean_false_changes: list[int] = []
    for _ in range(RANDOM_CONTROLS):
        randomized = []
        for decision in decisions:
            text_len = len(books[int(decision["book"])])
            branch_rows = []
            for branch in decision["branches"]:
                fake = json.loads(json.dumps(branch))
                fake["op"]["length"] = max(1, rng.randrange(1, text_len + 1) - int(decision["target_start"]))
                if int(decision["target_start"]) + int(fake["op"]["length"]) > text_len:
                    fake["op"]["length"] = text_len - int(decision["target_start"])
                branch_rows.append(
                    {
                        "book": decision["book"],
                        "kind": decision["kind"],
                        "branch": fake,
                        "features": boundary_features(books, counts, decision, fake),
                    }
                )
            randomized.append({"decision": decision, "branches": branch_rows})
        best = max((score_policy(randomized, policy) for policy in policies), key=score_key)
        total_hits.append(best["total_hits"])
        residual_hits.append(best["residual_hits"])
        clean_false_changes.append(best["clean_false_changes"])
    return {
        "controls": RANDOM_CONTROLS,
        "total_hits_min": min(total_hits),
        "total_hits_median": sorted(total_hits)[len(total_hits) // 2],
        "total_hits_max": max(total_hits),
        "residual_hits_max": max(residual_hits),
        "clean_false_changes_min": min(clean_false_changes),
        "p_total_hits_ge_real": (
            sum(1 for value in total_hits if value >= real_best["total_hits"]) + 1
        )
        / (RANDOM_CONTROLS + 1),
        "p_residual_hits_ge_real": (
            sum(1 for value in residual_hits if value >= real_best["residual_hits"]) + 1
        )
        / (RANDOM_CONTROLS + 1),
    }


def make_result() -> dict[str, Any]:
    tree_policy = load_json(TREE_POLICY)
    assert_boundary("observable_decision_tree_policy_audit", tree_policy)
    if tree_policy["summary"]["promotes_observable_tree_policy"]:
        raise RuntimeError("gate28 expects gate27 to be rejected")
    gate22 = load_module("branch_continuation_for_gate28", BRANCH_CONTINUATION_SCRIPT)
    books = load_books()
    decisions = gate22.collect_decisions()["decisions"]
    lengths = {radius for radius in RADII} | {2 * radius for radius in RADII}
    full_counts = substring_counts(books, sorted(books), lengths)
    full_rows = choice_rows(books, full_counts, decisions)
    scoreboard = full_fit_scoreboard(full_rows)
    active_baseline = score_policy(full_rows, "prefer_active_control")
    recurrence_scoreboard = full_fit_scoreboard(full_rows, recurrence_policy_names())
    best = recurrence_scoreboard[0]
    preq = prequential_rows(books, decisions)
    controls = random_boundary_control(books, full_counts, decisions, best)
    residual_total = sum(1 for row in decisions if row["kind"] == "residual_first_drift")
    promotes = (
        best["residual_hits"] == residual_total
        and best["clean_false_changes"] == 0
        and all(row["test_clean_false_changes"] == 0 for row in preq)
        and all(row["test_residual_hits"] == row["test_residual_total"] for row in preq)
    )
    classification = (
        "target_boundary_recurrence_policy_promoted"
        if promotes
        else "target_boundary_recurrence_policy_rejected"
    )
    return {
        "schema": "target_boundary_recurrence_audit.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "branch_continuation_script": rel(BRANCH_CONTINUATION_SCRIPT),
            "observable_decision_tree_policy_audit": rel(TREE_POLICY),
        },
        "scope": {
            "analysis_only": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "target_text_required": True,
            "stable_projection_used_as_training_label": False,
            "source_free_digit_generator_emitted": False,
            "promotes_parser_rule": promotes,
        },
        "summary": {
            "decision_count": len(decisions),
            "residual_decision_count": residual_total,
            "clean_control_count": len(decisions) - residual_total,
            "policy_count": len(recurrence_policy_names()),
            "radii": RADII,
            "active_baseline_total_hits": active_baseline["total_hits"],
            "active_baseline_residual_hits": active_baseline["residual_hits"],
            "active_baseline_clean_false_changes": active_baseline[
                "clean_false_changes"
            ],
            "best_recurrence_policy": best["policy"],
            "best_recurrence_total_hits": best["total_hits"],
            "best_recurrence_residual_hits": best["residual_hits"],
            "best_recurrence_clean_false_changes": best["clean_false_changes"],
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
            "promotes_target_boundary_recurrence_policy": promotes,
            "interpretation": (
                "Gate 28 tests whether branch choices preserve more recurrent "
                "target-side boundaries. Full-fit counts use the whole corpus as "
                "an optimistic diagnostic; prefix rows rebuild counts from train "
                "books only."
            ),
        },
        "active_baseline": active_baseline,
        "full_fit_scoreboard": [active_baseline] + recurrence_scoreboard,
        "prequential_rows": preq,
        "random_boundary_control": controls,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": classification,
            "source_length_dependency_status": "target_boundary_recurrence_rejected"
            if not promotes
            else "target_boundary_recurrence_promoted",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def md_table(rows: list[list[Any]], headers: list[str]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines)


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / f"{OUT_STEM}.json"
    md_path = TEST_RESULTS / f"{OUT_STEM}.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    full_rows = [
        [
            row["policy"],
            f"{row['total_hits']}/{row['total_total']}",
            f"{row['residual_hits']}/{row['residual_total']}",
            row["clean_false_changes"],
            row["residual_miss_books"],
        ]
        for row in result["full_fit_scoreboard"][:8]
    ]
    preq_rows = [
        [
            row["cutoff_book"],
            row["selected_policy"],
            f"{row['train_total_hits']}/{row['train_total']}",
            f"{row['test_total_hits']}/{row['test_total']}",
            f"{row['test_residual_hits']}/{row['test_residual_total']}",
            row["test_clean_false_changes"],
            row["selected_matches_oracle_total_hits"],
        ]
        for row in result["prequential_rows"]
    ]
    c = result["random_boundary_control"]
    body = f"""# Target Boundary Recurrence Audit

Classification: `{result['classification']}`
Translation delta: `NONE`

## Purpose

Gate 28 tests one of the original structural segmentation hypotheses: branch
choices might preserve recurrent target-side chunk boundaries. Each candidate
branch defines a next boundary at `target_start + length`; policies choose the
branch whose boundary has the most recurrent raw digit context.

Full-fit rows are optimistic diagnostics. Prefix/holdout rows rebuild recurrence
counts from prefix books only before scoring future books.

## Summary

- Decisions: `{s['decision_count']}`.
- Residual first-drift decisions: `{s['residual_decision_count']}`.
- Clean controls: `{s['clean_control_count']}`.
- Recurrence policies tested: `{s['policy_count']}`.
- Radii: `{s['radii']}`.
- Active baseline: `{s['active_baseline_total_hits']}/{s['decision_count']}`,
  residual `{s['active_baseline_residual_hits']}/{s['residual_decision_count']}`,
  clean false changes `{s['active_baseline_clean_false_changes']}`.
- Best recurrence policy: `{s['best_recurrence_policy']}`.
- Best recurrence result: `{s['best_recurrence_total_hits']}/{s['decision_count']}`,
  residual `{s['best_recurrence_residual_hits']}/{s['residual_decision_count']}`,
  clean false changes `{s['best_recurrence_clean_false_changes']}`.

## Full-Fit Policies

{md_table(full_rows, ["policy", "total hits", "residual hits", "clean false changes", "residual misses"])}

## Prefix/Holdout

{md_table(preq_rows, ["cutoff", "selected policy", "train hits", "test hits", "test residual hits", "test clean false changes", "matches oracle"])}

## Random Boundary Control

- Controls: `{c['controls']}`.
- Total-hit range under random branch boundaries:
  `{c['total_hits_min']}..{c['total_hits_max']}`.
- Median total hits under controls: `{c['total_hits_median']}`.
- Max residual hits under controls: `{c['residual_hits_max']}`.
- Minimum clean false changes under controls: `{c['clean_false_changes_min']}`.
- `p(total_hits >= real_best)`: `{c['p_total_hits_ge_real']:.6f}`.
- `p(residual_hits >= real_best)`: `{c['p_residual_hits_ge_real']:.6f}`.

## Decision

- Promotes target-boundary recurrence parser policy:
  `{s['promotes_target_boundary_recurrence_policy']}`.
- Prequential zero-clean-false-change cells:
  `{s['prequential_zero_clean_false_change_cells']}/{s['prequential_cells']}`.
- Prequential cover-all-test-residual cells:
  `{s['prequential_cover_all_test_residual_cells']}/{s['prequential_cells']}`.
- This gate tests a structural boundary-reuse idea, not a bit sweep.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
"""
    md_path.write_text(body, encoding="utf-8")
    print(json_path)
    print(md_path)


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
