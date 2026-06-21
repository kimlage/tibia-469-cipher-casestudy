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
TARGET_BOUNDARY = TEST_RESULTS / "28_target_boundary_recurrence_audit.json"

OUT_STEM = "29_future_copy_opportunity_audit"
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
LOOKAHEAD = 12
MIN_COPY_LEN = 5
RANDOM_CONTROLS = 30
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


def previous_books_prefix(books: dict[int, str], book: int) -> str:
    return "".join(books[index] for index in range(book))


def max_copy_at(books: dict[int, str], previous_prefix: str, book: int, pos: int) -> dict[str, int]:
    target = books[book]
    if pos >= len(target):
        return {"max_len": 0, "candidate_count": 0}
    emitted = previous_prefix + target[:pos]
    remaining = min(len(target) - pos, LOOKAHEAD + MIN_COPY_LEN)
    for length in range(remaining, MIN_COPY_LEN - 1, -1):
        needle = target[pos : pos + length]
        if emitted.find(needle) >= 0:
            return {"max_len": length, "candidate_count": emitted.count(needle)}
    return {"max_len": 0, "candidate_count": 0}


def branch_boundary(branch: dict[str, Any]) -> int:
    return int(branch["op"]["target_start"]) + int(branch["op"]["length"])


def opportunity_features(
    books: dict[int, str],
    previous_prefix_by_book: dict[int, str],
    decision: dict[str, Any],
    branch: dict[str, Any],
) -> dict[str, Any]:
    book = int(decision["book"])
    target = books[book]
    boundary = branch_boundary(branch)
    previous_prefix = previous_prefix_by_book[book]
    rows = []
    for offset in range(0, min(LOOKAHEAD, len(target) - boundary) + 1):
        pos = boundary + offset
        row = max_copy_at(books, previous_prefix, book, pos)
        rows.append({"offset": offset, **row})
    copy_rows = [row for row in rows if row["max_len"] >= MIN_COPY_LEN]
    immediate = rows[0] if rows else {"max_len": 0, "candidate_count": 0}
    best = max(rows, key=lambda row: (row["max_len"], -row["offset"])) if rows else immediate
    first_available = next((row for row in rows if row["max_len"] >= MIN_COPY_LEN), None)
    return {
        "boundary": boundary,
        "remaining": len(target) - boundary,
        "immediate_max_len": immediate["max_len"],
        "immediate_candidate_count": immediate["candidate_count"],
        "window_best_len": best["max_len"],
        "window_best_offset": best["offset"],
        "window_sum_len": sum(row["max_len"] for row in rows),
        "window_copy_positions": len(copy_rows),
        "first_available_offset": None if first_available is None else first_available["offset"],
        "first_available_len": 0 if first_available is None else first_available["max_len"],
    }


def policy_functions() -> dict[str, Callable[[dict[str, Any]], tuple[Any, ...]]]:
    return {
        "max_immediate_len": lambda row: (
            row["features"]["immediate_max_len"],
            row["features"]["immediate_candidate_count"],
            row["branch"]["is_active"],
            -int(row["branch"]["op"]["length"]),
            row["branch"]["label"],
        ),
        "max_window_best_len": lambda row: (
            row["features"]["window_best_len"],
            -row["features"]["window_best_offset"],
            row["features"]["window_sum_len"],
            row["branch"]["is_active"],
            row["branch"]["label"],
        ),
        "max_window_sum_len": lambda row: (
            row["features"]["window_sum_len"],
            row["features"]["window_best_len"],
            row["branch"]["is_active"],
            row["branch"]["label"],
        ),
        "max_copy_positions": lambda row: (
            row["features"]["window_copy_positions"],
            row["features"]["window_best_len"],
            row["branch"]["is_active"],
            row["branch"]["label"],
        ),
        "min_first_available_offset": lambda row: (
            9999
            if row["features"]["first_available_offset"] is None
            else -row["features"]["first_available_offset"],
            row["features"]["first_available_len"],
            row["branch"]["is_active"],
            row["branch"]["label"],
        ),
        "prefer_active_control": lambda row: (
            row["branch"]["is_active"],
            row["branch"]["label"],
        ),
    }


def opportunity_policy_names() -> list[str]:
    return [name for name in policy_functions() if name != "prefer_active_control"]


def choice_rows(
    books: dict[int, str],
    previous_prefix_by_book: dict[int, str],
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
                    "features": opportunity_features(
                        books, previous_prefix_by_book, decision, branch
                    ),
                }
            )
        rows.append({"decision": decision, "branches": branch_rows})
    return rows


def choose_policy(row: dict[str, Any], policy: str) -> dict[str, Any]:
    return max(row["branches"], key=policy_functions()[policy])


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


def scoreboard(rows: list[dict[str, Any]], policies: list[str]) -> list[dict[str, Any]]:
    scores = [score_policy(rows, policy) for policy in policies]
    return sorted(
        scores,
        key=lambda row: (
            -row["total_hits"],
            -row["residual_hits"],
            row["clean_false_changes"],
            row["policy"],
        ),
    )


def previous_prefixes_for_cutoff(books: dict[int, str], cutoff: int | None = None) -> dict[int, str]:
    out = {}
    for book in sorted(books):
        if cutoff is None:
            out[book] = previous_books_prefix(books, book)
        else:
            out[book] = "".join(books[index] for index in range(min(book, cutoff)))
    return out


def prequential_rows(
    books: dict[int, str],
    decisions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    policies = opportunity_policy_names()
    for cutoff in PREFIX_CUTOFFS:
        train = [row for row in decisions if row["book"] < cutoff]
        test = [row for row in decisions if row["book"] >= cutoff]
        prefixes = previous_prefixes_for_cutoff(books, cutoff)
        train_rows = choice_rows(books, prefixes, train)
        test_rows = choice_rows(books, prefixes, test)
        train_scores = scoreboard(train_rows, policies)
        selected = train_scores[0]
        test_score = score_policy(test_rows, selected["policy"])
        oracle = scoreboard(test_rows, policies)[0]
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
    rows: list[dict[str, Any]],
    real_best: dict[str, Any],
) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED)
    policies = opportunity_policy_names()
    total_hits = []
    residual_hits = []
    clean_false_changes = []
    for _ in range(RANDOM_CONTROLS):
        randomized = []
        for row in rows:
            copied = {"decision": row["decision"], "branches": []}
            feature_pool = [branch["features"] for branch in row["branches"]]
            for branch in row["branches"]:
                copied["branches"].append(
                    {
                        "book": branch["book"],
                        "kind": branch["kind"],
                        "branch": branch["branch"],
                        "features": rng.choice(feature_pool),
                    }
                )
            randomized.append(copied)
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
    target_boundary = load_json(TARGET_BOUNDARY)
    assert_boundary("target_boundary_recurrence_audit", target_boundary)
    if target_boundary["summary"]["promotes_target_boundary_recurrence_policy"]:
        raise RuntimeError("gate29 expects gate28 to be rejected")
    gate22 = load_module("branch_continuation_for_gate29", BRANCH_CONTINUATION_SCRIPT)
    books = load_books()
    decisions = gate22.collect_decisions()["decisions"]
    prefixes = previous_prefixes_for_cutoff(books)
    rows = choice_rows(books, prefixes, decisions)
    active = score_policy(rows, "prefer_active_control")
    scores = scoreboard(rows, opportunity_policy_names())
    best = scores[0]
    preq = prequential_rows(books, decisions)
    controls = random_boundary_control(rows, best)
    residual_total = sum(1 for row in decisions if row["kind"] == "residual_first_drift")
    promotes = (
        best["residual_hits"] == residual_total
        and best["clean_false_changes"] == 0
        and all(row["test_clean_false_changes"] == 0 for row in preq)
        and all(row["test_residual_hits"] == row["test_residual_total"] for row in preq)
    )
    classification = (
        "future_copy_opportunity_policy_promoted"
        if promotes
        else "future_copy_opportunity_policy_rejected"
    )
    return {
        "schema": "future_copy_opportunity_audit.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "branch_continuation_script": rel(BRANCH_CONTINUATION_SCRIPT),
            "target_boundary_recurrence_audit": rel(TARGET_BOUNDARY),
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
            "lookahead": LOOKAHEAD,
            "policy_count": len(opportunity_policy_names()),
            "active_baseline_total_hits": active["total_hits"],
            "active_baseline_residual_hits": active["residual_hits"],
            "active_baseline_clean_false_changes": active["clean_false_changes"],
            "best_policy": best["policy"],
            "best_total_hits": best["total_hits"],
            "best_residual_hits": best["residual_hits"],
            "best_clean_false_changes": best["clean_false_changes"],
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
            "promotes_future_copy_opportunity_policy": promotes,
            "interpretation": (
                "Gate 29 tests whether branch choice is explained by preserving "
                "or creating near-future copy opportunities after the branch "
                "boundary."
            ),
        },
        "active_baseline": active,
        "full_fit_scoreboard": [active] + scores,
        "prequential_rows": preq,
        "randomized_feature_control": controls,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": classification,
            "source_length_dependency_status": "future_copy_opportunity_rejected"
            if not promotes
            else "future_copy_opportunity_promoted",
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
    c = result["randomized_feature_control"]
    body = f"""# Future Copy Opportunity Audit

Classification: `{result['classification']}`
Translation delta: `NONE`

## Purpose

Gate 29 tests whether residual branch choices are explained by preserving or
creating near-future copy opportunities. Each branch boundary is scored by copy
availability at the boundary and within the next `{s['lookahead']}` target
positions.

This is a structural parser test, not a bit sweep. It asks whether choosing the
stable branch can be inferred from the copy-opportunity landscape without using
the stable projection as a feature.

## Summary

- Decisions: `{s['decision_count']}`.
- Residual first-drift decisions: `{s['residual_decision_count']}`.
- Clean controls: `{s['clean_control_count']}`.
- Opportunity policies tested: `{s['policy_count']}`.
- Active baseline: `{s['active_baseline_total_hits']}/{s['decision_count']}`,
  residual `{s['active_baseline_residual_hits']}/{s['residual_decision_count']}`,
  clean false changes `{s['active_baseline_clean_false_changes']}`.
- Best opportunity policy: `{s['best_policy']}`.
- Best opportunity result: `{s['best_total_hits']}/{s['decision_count']}`,
  residual `{s['best_residual_hits']}/{s['residual_decision_count']}`,
  clean false changes `{s['best_clean_false_changes']}`.

## Full-Fit Policies

{md_table(full_rows, ["policy", "total hits", "residual hits", "clean false changes", "residual misses"])}

## Prefix/Holdout

{md_table(preq_rows, ["cutoff", "selected policy", "train hits", "test hits", "test residual hits", "test clean false changes", "matches oracle"])}

## Randomized Feature Control

- Controls: `{c['controls']}`.
- Total-hit range under per-decision shuffled opportunity features:
  `{c['total_hits_min']}..{c['total_hits_max']}`.
- Median total hits under controls: `{c['total_hits_median']}`.
- Max residual hits under controls: `{c['residual_hits_max']}`.
- Minimum clean false changes under controls: `{c['clean_false_changes_min']}`.
- `p(total_hits >= real_best)`: `{c['p_total_hits_ge_real']:.6f}`.
- `p(residual_hits >= real_best)`: `{c['p_residual_hits_ge_real']:.6f}`.

## Decision

- Promotes future-copy-opportunity parser policy:
  `{s['promotes_future_copy_opportunity_policy']}`.
- Prequential zero-clean-false-change cells:
  `{s['prequential_zero_clean_false_change_cells']}/{s['prequential_cells']}`.
- Prequential cover-all-test-residual cells:
  `{s['prequential_cover_all_test_residual_cells']}/{s['prequential_cells']}`.
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
