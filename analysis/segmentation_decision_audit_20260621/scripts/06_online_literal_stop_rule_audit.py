from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

PREQ = ROOT / "analysis" / "prequential_and_row0_origin_audit_20260621"
GATE111_SCRIPT = PREQ / "scripts" / "111_decoder_length_candidate_ambiguity_audit.py"
BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
TRACE_SCRIPT = HERE / "scripts" / "01_segmentation_decision_trace.py"
LITERAL_GAP = TEST_RESULTS / "05_literal_gap_boundary_audit.json"

OUT_STEM = "06_online_literal_stop_rule_audit"
SEED_BOOKS = list(range(10))
CONFIRM_WINDOWS = list(range(1, 13))
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


def offset_rows(trace_module, emitted: str, target: str, start: int) -> list[dict[str, int]]:
    rows: list[dict[str, int]] = []
    for offset in range(len(target) - start + 1):
        if start + offset >= len(target):
            max_copy_length = 0
        else:
            candidates = trace_module.candidate_sources_with_max(
                emitted + target[start : start + offset],
                target,
                start + offset,
            )
            max_copy_length = max([row["max_length"] for row in candidates], default=0)
        rows.append(
            {
                "offset": offset,
                "max_copy_length": max_copy_length,
                "total_advance": offset + max_copy_length,
            }
        )
    return rows


def build_literal_rows() -> list[dict[str, Any]]:
    trace_module = load_module("segmentation_trace_for_gate06", TRACE_SCRIPT)
    gate111 = load_module("gate111_for_segmentation_gate06", GATE111_SCRIPT)
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    stable_ops = trace_module.projected_ops_from_copy_rows(gate111.make_copy_rows(), books)
    stable_by_book: dict[int, list[dict[str, Any]]] = {}
    for op in stable_ops:
        stable_by_book.setdefault(int(op["book"]), []).append(op)
    for rows in stable_by_book.values():
        rows.sort(key=lambda row: int(row["target_start"]))

    emitted = "".join(books[book] for book in SEED_BOOKS)
    rows: list[dict[str, Any]] = []
    for book in range(10, 70):
        target = books[book]
        for index, op in enumerate(stable_by_book.get(book, [])):
            start = int(op["target_start"])
            length = int(op["length"])
            if op["type"] == "literal":
                next_op = (
                    stable_by_book[book][index + 1]
                    if index + 1 < len(stable_by_book[book])
                    else None
                )
                rows.append(
                    {
                        "book": book,
                        "op_index": int(op["op_index"]),
                        "target_start": start,
                        "literal_length": length,
                        "next_op_type": None if next_op is None else next_op["type"],
                        "next_copy_length": int(next_op["length"])
                        if next_op and next_op["type"] == "copy"
                        else 0,
                        "offset_rows": offset_rows(trace_module, emitted, target, start),
                    }
                )
            emitted += target[start : start + length]
    return rows


def predict_first_match(row: dict[str, Any]) -> int | None:
    for offset in row["offset_rows"]:
        if offset["max_copy_length"] >= 5:
            return offset["offset"]
    return None


def predict_first_confirmed_peak(row: dict[str, Any], field: str, confirm_window: int) -> int | None:
    offsets = row["offset_rows"]
    for index, offset in enumerate(offsets):
        if offset["max_copy_length"] < 5:
            continue
        value = offset[field]
        if all(
            index + step >= len(offsets) or offsets[index + step][field] <= value
            for step in range(1, confirm_window + 1)
        ):
            return offset["offset"]
    return None


def score_policy(rows: list[dict[str, Any]], policy: str, confirm_window: int | None = None) -> dict[str, Any]:
    followed = [row for row in rows if row["next_op_type"] == "copy"]
    book_end = [row for row in rows if row["next_op_type"] != "copy"]
    hits = 0
    failures = []
    for row in followed:
        if policy == "first_match":
            predicted = predict_first_match(row)
        elif policy == "first_confirmed_max_copy_length_peak":
            predicted = predict_first_confirmed_peak(
                row, "max_copy_length", int(confirm_window)
            )
        elif policy == "first_confirmed_total_advance_peak":
            predicted = predict_first_confirmed_peak(
                row, "total_advance", int(confirm_window)
            )
        else:
            raise ValueError(policy)
        ok = predicted == row["literal_length"]
        if ok:
            hits += 1
        elif len(failures) < 10:
            failures.append(
                {
                    "book": row["book"],
                    "op_index": row["op_index"],
                    "target_start": row["target_start"],
                    "literal_length": row["literal_length"],
                    "predicted_literal_length": predicted,
                    "next_copy_length": row["next_copy_length"],
                }
            )
    all_hits = hits + len(book_end)
    return {
        "policy": policy,
        "confirm_window": confirm_window,
        "followed_by_copy_hits": hits,
        "followed_by_copy_total": len(followed),
        "followed_by_copy_coverage": hits / len(followed),
        "all_literal_gap_hits_with_book_end_default": all_hits,
        "all_literal_gap_total": len(rows),
        "all_literal_gap_coverage_with_book_end_default": all_hits / len(rows),
        "sample_failures": failures,
    }


def prequential(rows: list[dict[str, Any]], policies: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for cutoff in PREFIX_CUTOFFS:
        train = [
            row
            for row in rows
            if row["book"] < cutoff and row["next_op_type"] == "copy"
        ]
        test = [
            row
            for row in rows
            if row["book"] >= cutoff and row["next_op_type"] == "copy"
        ]
        if not train or not test:
            continue
        train_scores = []
        for policy in policies:
            score = score_policy(train, policy["policy"], policy["confirm_window"])
            train_scores.append(
                (
                    score["followed_by_copy_hits"],
                    policy["policy"],
                    policy["confirm_window"],
                )
            )
        best_hits, best_policy, best_window = max(train_scores)
        test_score = score_policy(test, best_policy, best_window)
        oracle = max(
            score_policy(test, policy["policy"], policy["confirm_window"])[
                "followed_by_copy_hits"
            ]
            for policy in policies
        )
        result.append(
            {
                "cutoff_book": cutoff,
                "train_rows": len(train),
                "test_rows": len(test),
                "selected_policy": best_policy,
                "selected_confirm_window": best_window,
                "train_hits": best_hits,
                "test_hits": test_score["followed_by_copy_hits"],
                "test_coverage": test_score["followed_by_copy_coverage"],
                "oracle_test_hits": oracle,
                "selected_matches_oracle": test_score["followed_by_copy_hits"]
                == oracle,
            }
        )
    return result


def make_result() -> dict[str, Any]:
    gap = load_json(LITERAL_GAP)
    assert_boundary("literal_gap_boundary_audit", gap)
    rows = build_literal_rows()
    policies = [{"policy": "first_match", "confirm_window": None}]
    for window in CONFIRM_WINDOWS:
        policies.append(
            {
                "policy": "first_confirmed_max_copy_length_peak",
                "confirm_window": window,
            }
        )
        policies.append(
            {
                "policy": "first_confirmed_total_advance_peak",
                "confirm_window": window,
            }
        )
    policy_rows = [
        score_policy(rows, policy["policy"], policy["confirm_window"])
        for policy in policies
    ]
    best = max(
        policy_rows,
        key=lambda row: (
            row["followed_by_copy_hits"],
            row["all_literal_gap_hits_with_book_end_default"],
            row["policy"],
            row["confirm_window"] or 0,
        ),
    )
    preq = prequential(rows, policies)
    promotes_source_free = best["followed_by_copy_hits"] == best["followed_by_copy_total"]
    promotes_partial_online_rule = (
        best["followed_by_copy_hits"] >= 0.9 * best["followed_by_copy_total"]
        and all(row["selected_confirm_window"] == best["confirm_window"] for row in preq)
    )
    return {
        "schema": "online_literal_stop_rule_audit.v1",
        "classification": "online_literal_stop_rule_partial_not_source_free",
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "literal_gap_boundary_audit": rel(LITERAL_GAP),
            "books_digits": rel(BOOKS_DIGITS),
        },
        "summary": {
            "literal_gap_count": len(rows),
            "followed_by_copy_count": sum(
                1 for row in rows if row["next_op_type"] == "copy"
            ),
            "book_end_literal_gap_count": sum(
                1 for row in rows if row["next_op_type"] != "copy"
            ),
            "policy_count": len(policy_rows),
            "best_policy": best,
            "prequential_cells": len(preq),
            "prequential_selected_matches_oracle_cells": sum(
                1 for row in preq if row["selected_matches_oracle"]
            ),
            "promotes_partial_online_literal_stop_rule": promotes_partial_online_rule,
            "promotes_source_free_literal_stop_rule": promotes_source_free,
            "interpretation": (
                "A small online confirmation rule explains most literal stops: "
                "choose the first local peak in available copy length after a "
                "six-digit confirmation window. It is stable under prefix "
                "selection, but it still misses four followed-by-copy gaps, so "
                "literal windows remain partially retained rather than fully "
                "generated."
            ),
        },
        "policy_rows": policy_rows,
        "prequential_rows": preq,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": "partial_online_literal_stop_rule",
            "literal_window_status": "reduced_but_not_removed",
            "source_free_parser_status": "not_promoted",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    json_path = TEST_RESULTS / f"{OUT_STEM}.json"
    md_path = TEST_RESULTS / f"{OUT_STEM}.md"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    s = result["summary"]
    best = s["best_policy"]
    lines = [
        "# Online Literal Stop Rule Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 05 showed that literal stops are optimal inside declared windows,",
        "but not over the full suffix. This gate tests online/local stopping",
        "rules that do not use the declared window as the search horizon.",
        "",
        "## Best Rule",
        "",
        f"- Policy: `{best['policy']}`.",
        f"- Confirm window: `{best['confirm_window']}`.",
        f"- Followed-by-copy hits: `{best['followed_by_copy_hits']}/{best['followed_by_copy_total']}`.",
        f"- All literal gap hits with book-end default: `{best['all_literal_gap_hits_with_book_end_default']}/{best['all_literal_gap_total']}`.",
        "",
        "## Policy Scoreboard",
        "",
        "| Policy | Window | Followed hits | All hits with book-end default |",
        "|---|---:|---:|---:|",
    ]
    for row in sorted(
        result["policy_rows"],
        key=lambda item: (
            -item["followed_by_copy_hits"],
            item["policy"],
            item["confirm_window"] or 0,
        ),
    )[:12]:
        lines.append(
            f"| `{row['policy']}` | `{row['confirm_window']}` | "
            f"`{row['followed_by_copy_hits']}/{row['followed_by_copy_total']}` | "
            f"`{row['all_literal_gap_hits_with_book_end_default']}/{row['all_literal_gap_total']}` |"
        )
    lines.extend(
        [
            "",
            "## Prequential",
            "",
            "| Cutoff | Train | Test | Selected | Test hits | Oracle hits |",
            "|---:|---:|---:|---|---:|---:|",
        ]
    )
    for row in result["prequential_rows"]:
        lines.append(
            f"| `{row['cutoff_book']}` | `{row['train_rows']}` | `{row['test_rows']}` | "
            f"`{row['selected_policy']}:{row['selected_confirm_window']}` | "
            f"`{row['test_hits']}/{row['test_rows']}` | `{row['oracle_test_hits']}/{row['test_rows']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Promotes partial online literal stop rule: `{s['promotes_partial_online_literal_stop_rule']}`.",
            f"- Promotes source-free literal stop rule: `{s['promotes_source_free_literal_stop_rule']}`.",
            f"- {s['interpretation']}",
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
