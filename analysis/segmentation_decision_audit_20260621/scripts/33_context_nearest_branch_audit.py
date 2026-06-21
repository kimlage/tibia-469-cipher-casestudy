from __future__ import annotations

import importlib.util
import json
import random
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
BRANCH_CONTINUATION_SCRIPT = HERE / "scripts" / "22_residual_branch_continuation_audit.py"
PHASE_GRID = TEST_RESULTS / "32_phase_grid_segmentation_audit.json"

OUT_STEM = "33_context_nearest_branch_audit"
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
WINDOWS = [(4, 8), (8, 8), (8, 12), (12, 12), (16, 16)]
SIGNATURE_MODES = ["action_class", "action_type_length", "action_label_length"]
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


def context_window(target: str, pos: int, left: int, right: int) -> str:
    lhs = target[max(0, pos - left) : pos].rjust(left, "^")
    rhs = target[pos : pos + right].ljust(right, "$")
    return lhs + "|" + rhs


def hamming(left: str, right: str) -> int:
    if len(left) != len(right):
        raise RuntimeError("context lengths differ")
    return sum(1 for a, b in zip(left, right) if a != b)


def stable_branch(decision: dict[str, Any]) -> dict[str, Any]:
    for branch in decision["branches"]:
        if branch["is_stable"]:
            return branch
    raise RuntimeError(
        {
            "type": "missing_stable_observable_branch",
            "book": decision["book"],
            "target_start": decision["target_start"],
        }
    )


def active_branch(row: dict[str, Any]) -> dict[str, Any]:
    for branch in row["branches"]:
        if branch["branch"]["is_active"]:
            return branch
    raise RuntimeError("missing active branch")


def branch_label_class(branch: dict[str, Any]) -> str:
    label = branch["label"]
    if branch["is_active"]:
        return "active"
    if "observable_immediate_copy" in label:
        return "nonactive_immediate_copy"
    if "observable_literal_stop" in label:
        return "nonactive_literal_stop"
    return f"nonactive_{branch['op']['type']}"


def signature_for_branch(branch: dict[str, Any], mode: str) -> dict[str, Any]:
    op = branch["op"]
    base = {
        "mode": mode,
        "class": branch_label_class(branch),
        "type": op["type"],
        "length": int(op["length"]),
    }
    if mode == "action_class":
        return {"mode": mode, "class": base["class"]}
    if mode == "action_type_length":
        return {
            "mode": mode,
            "class": base["class"],
            "type": base["type"],
            "length": base["length"],
        }
    if mode == "action_label_length":
        return {
            "mode": mode,
            "class": base["class"],
            "type": base["type"],
            "length": base["length"],
        }
    raise RuntimeError(f"unknown signature mode {mode}")


def branch_matches_signature(branch: dict[str, Any], signature: dict[str, Any]) -> bool:
    if signature["class"] == "active":
        return branch["is_active"]
    if branch["is_active"]:
        return False
    if branch_label_class(branch) != signature["class"]:
        return False
    if "type" in signature and branch["op"]["type"] != signature["type"]:
        return False
    return True


def choose_by_signature(row: dict[str, Any], signature: dict[str, Any]) -> dict[str, Any]:
    if signature["class"] == "active":
        return active_branch(row)
    candidates = [
        branch for branch in row["branches"] if branch_matches_signature(branch["branch"], signature)
    ]
    if not candidates:
        return active_branch(row)
    if "length" in signature:
        return min(
            candidates,
            key=lambda branch: (
                abs(int(branch["branch"]["op"]["length"]) - int(signature["length"])),
                branch["branch"]["is_active"],
                branch["branch"]["label"],
            ),
        )
    return min(candidates, key=lambda branch: branch["branch"]["label"])


def policy_name(left: int, right: int, mode: str) -> str:
    return f"nearest_context_l{left}_r{right}_{mode}"


def parse_policy(policy: str) -> tuple[int, int, str]:
    prefix = "nearest_context_l"
    if not policy.startswith(prefix):
        raise RuntimeError(f"unknown policy {policy}")
    rest = policy[len(prefix) :]
    left_s, rest = rest.split("_r", 1)
    right_s, mode = rest.split("_", 1)
    return int(left_s), int(right_s), mode


def policy_names() -> list[str]:
    return [policy_name(left, right, mode) for left, right in WINDOWS for mode in SIGNATURE_MODES]


def choice_rows(decisions: list[dict[str, Any]], books: dict[int, str]) -> list[dict[str, Any]]:
    rows = []
    for decision in decisions:
        book = int(decision["book"])
        target = books[book]
        stable = stable_branch(decision)
        contexts = {
            f"{left}:{right}": context_window(
                target, int(decision["target_start"]), left, right
            )
            for left, right in WINDOWS
        }
        row_branches = [
            {
                "book": book,
                "kind": decision["kind"],
                "branch": branch,
            }
            for branch in decision["branches"]
        ]
        rows.append(
            {
                "decision": decision,
                "book": book,
                "kind": decision["kind"],
                "contexts": contexts,
                "stable_signatures": {
                    mode: signature_for_branch(stable, mode)
                    for mode in SIGNATURE_MODES
                },
                "branches": row_branches,
            }
        )
    return rows


def nearest_signature(
    train_rows: list[dict[str, Any]],
    row: dict[str, Any],
    left: int,
    right: int,
    mode: str,
) -> dict[str, Any] | None:
    if not train_rows:
        return None
    key = f"{left}:{right}"
    context = row["contexts"][key]
    nearest = min(
        train_rows,
        key=lambda candidate: (
            hamming(context, candidate["contexts"][key]),
            int(candidate["book"]),
            int(candidate["decision"]["target_start"]),
        ),
    )
    return nearest["stable_signatures"][mode]


def score_policy(
    rows: list[dict[str, Any]],
    policy: str,
    train_for_row,
) -> dict[str, Any]:
    left, right, mode = parse_policy(policy)
    selected = []
    for row in rows:
        train_rows = train_for_row(row)
        signature = nearest_signature(train_rows, row, left, right, mode)
        chosen = active_branch(row) if signature is None else choose_by_signature(row, signature)
        selected.append(
            {
                "book": row["book"],
                "kind": row["kind"],
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


def active_score(rows: list[dict[str, Any]]) -> dict[str, Any]:
    selected = []
    for row in rows:
        chosen = active_branch(row)
        selected.append(
            {
                "book": row["book"],
                "kind": row["kind"],
                "chosen_is_stable": chosen["branch"]["is_stable"],
                "chosen_label": chosen["branch"]["label"],
            }
        )
    residual = [row for row in selected if row["kind"] == "residual_first_drift"]
    clean = [row for row in selected if row["kind"] == "clean_control"]
    return {
        "policy": "prefer_active_control",
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


def scoreboard(rows: list[dict[str, Any]], train_for_row) -> list[dict[str, Any]]:
    scores = [score_policy(rows, policy, train_for_row) for policy in policy_names()]
    return sorted(
        scores,
        key=lambda row: (
            -row["total_hits"],
            -row["residual_hits"],
            row["clean_false_changes"],
            row["policy"],
        ),
    )


def leave_one_book_scoreboard(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return scoreboard(rows, lambda row: [item for item in rows if item["book"] != row["book"]])


def prequential_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for cutoff in PREFIX_CUTOFFS:
        train = [row for row in rows if row["book"] < cutoff]
        test = [row for row in rows if row["book"] >= cutoff]
        train_scores = scoreboard(train, lambda row: [item for item in train if item["book"] != row["book"]])
        selected = train_scores[0]
        test_score = score_policy(test, selected["policy"], lambda _row: train)
        oracle = scoreboard(test, lambda _row: train)[0]
        out.append(
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
    return out


def shuffled_label_control(rows: list[dict[str, Any]], real_best: dict[str, Any]) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED)
    total_hits = []
    residual_hits = []
    clean_false_changes = []
    for _ in range(RANDOM_CONTROLS):
        signatures_by_mode = {
            mode: [row["stable_signatures"][mode] for row in rows]
            for mode in SIGNATURE_MODES
        }
        for values in signatures_by_mode.values():
            rng.shuffle(values)
        shuffled = []
        for index, row in enumerate(rows):
            copied = dict(row)
            copied["stable_signatures"] = {
                mode: signatures_by_mode[mode][index] for mode in SIGNATURE_MODES
            }
            shuffled.append(copied)
        best = max(leave_one_book_scoreboard(shuffled), key=score_key)
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
    phase_grid = load_json(PHASE_GRID)
    assert_boundary("phase_grid_segmentation_audit", phase_grid)
    if phase_grid["summary"]["promotes_phase_grid_policy"]:
        raise RuntimeError("gate33 expects gate32 to be rejected")
    gate22 = load_module("branch_continuation_for_gate33", BRANCH_CONTINUATION_SCRIPT)
    books = load_books()
    decisions = gate22.collect_decisions()["decisions"]
    rows = choice_rows(decisions, books)
    active = active_score(rows)
    scores = leave_one_book_scoreboard(rows)
    best = scores[0]
    preq = prequential_rows(rows)
    controls = shuffled_label_control(rows, best)
    residual_total = sum(1 for row in rows if row["kind"] == "residual_first_drift")
    promotes = (
        best["residual_hits"] == residual_total
        and best["clean_false_changes"] == 0
        and all(row["test_clean_false_changes"] == 0 for row in preq)
        and all(row["test_residual_hits"] == row["test_residual_total"] for row in preq)
    )
    classification = (
        "context_nearest_branch_policy_promoted"
        if promotes
        else "context_nearest_branch_policy_rejected"
    )
    return {
        "schema": "context_nearest_branch_audit.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "branch_continuation_script": rel(BRANCH_CONTINUATION_SCRIPT),
            "phase_grid_audit": rel(PHASE_GRID),
        },
        "scope": {
            "analysis_only": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "target_text_required": True,
            "stable_projection_used_as_training_label": True,
            "stable_projection_used_as_current_decision_feature": False,
            "source_free_digit_generator_emitted": False,
            "promotes_parser_rule": promotes,
        },
        "summary": {
            "decision_count": len(rows),
            "residual_decision_count": residual_total,
            "clean_control_count": len(rows) - residual_total,
            "windows": WINDOWS,
            "signature_modes": SIGNATURE_MODES,
            "policy_count": len(policy_names()),
            "active_baseline_total_hits": active["total_hits"],
            "active_baseline_residual_hits": active["residual_hits"],
            "active_baseline_clean_false_changes": active["clean_false_changes"],
            "best_policy": best["policy"],
            "best_leave_one_book_total_hits": best["total_hits"],
            "best_leave_one_book_residual_hits": best["residual_hits"],
            "best_leave_one_book_clean_false_changes": best["clean_false_changes"],
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
            "promotes_context_nearest_policy": promotes,
            "interpretation": (
                "Gate 33 tests whether raw digit context nearest-neighbor "
                "recurrence can select stable branch actions from prefix/other-book "
                "training decisions."
            ),
        },
        "active_baseline": active,
        "leave_one_book_scoreboard": [active] + scores,
        "prequential_rows": preq,
        "shuffled_label_control": controls,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": classification,
            "source_length_dependency_status": "context_nearest_branch_rejected"
            if not promotes
            else "context_nearest_branch_promoted",
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
        for row in result["leave_one_book_scoreboard"][:10]
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
    c = result["shuffled_label_control"]
    body = f"""# Context Nearest Branch Audit

Classification: `{result['classification']}`
Translation delta: `NONE`

## Purpose

Gate 33 tests whether stable branch choices recur with raw digit context. For
each decision, the policy finds the nearest prior/other-book decision by
target-context Hamming distance and applies that training decision's stable
branch action class to the current candidate branches.

This is a predictive parser test, not a bit sweep. It uses stable branch labels
only in training rows, never as a current-decision feature.

## Summary

- Decisions: `{s['decision_count']}`.
- Residual first-drift decisions: `{s['residual_decision_count']}`.
- Clean controls: `{s['clean_control_count']}`.
- Context windows: `{s['windows']}`.
- Signature modes: `{s['signature_modes']}`.
- Nearest-context policies tested: `{s['policy_count']}`.
- Active baseline: `{s['active_baseline_total_hits']}/{s['decision_count']}`,
  residual `{s['active_baseline_residual_hits']}/{s['residual_decision_count']}`,
  clean false changes `{s['active_baseline_clean_false_changes']}`.
- Best leave-one-book policy: `{s['best_policy']}`.
- Best leave-one-book result:
  `{s['best_leave_one_book_total_hits']}/{s['decision_count']}`,
  residual `{s['best_leave_one_book_residual_hits']}/{s['residual_decision_count']}`,
  clean false changes `{s['best_leave_one_book_clean_false_changes']}`.

## Leave-One-Book Scoreboard

{md_table(full_rows, ["policy", "total hits", "residual hits", "clean false changes", "residual misses"])}

## Prefix/Holdout

{md_table(preq_rows, ["cutoff", "selected policy", "train hits", "test hits", "test residual hits", "test clean false changes", "matches oracle"])}

## Shuffled Label Control

- Controls: `{c['controls']}`.
- Total-hit range under shuffled training action labels:
  `{c['total_hits_min']}..{c['total_hits_max']}`.
- Median total hits under controls: `{c['total_hits_median']}`.
- Max residual hits under controls: `{c['residual_hits_max']}`.
- Minimum clean false changes under controls: `{c['clean_false_changes_min']}`.
- `p(total_hits >= real_best)`: `{c['p_total_hits_ge_real']:.6f}`.
- `p(residual_hits >= real_best)`: `{c['p_residual_hits_ge_real']:.6f}`.

## Decision

- Promotes context-nearest parser policy:
  `{s['promotes_context_nearest_policy']}`.
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
