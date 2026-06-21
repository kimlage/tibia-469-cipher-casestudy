from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"
AUTHORIAL = ROOT / "analysis" / "authorial_mechanism_20260620"

FINAL_FORMULA = (
    AUTHORIAL
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_targetmax_saturated_source_substitution_second_pass_partial_boundary_shift_second_pass_formula_469.json"
)
BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
AUDIT_126 = AUTHORIAL / "scripts" / "126_prequential_recipe_reparse_audit.py"
GATE71 = TEST_RESULTS / "71_final_formula_dependency_refresh_gate.json"

PREFIX_CUTOFFS = [10, 20, 35, 50, 60]
THRESHOLDS = [100_000, 250_000, 1_000_000, 5_000_000]


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


def candidate_graph_stats(
    *,
    formula: dict[str, Any],
    books: dict[str, str],
    audit126,
    cutoff: int,
) -> list[dict[str, Any]]:
    min_len = int(formula["policy"]["min_len"])
    available = "".join(books[str(book)] for book in range(cutoff))
    rows = []
    for book in range(cutoff, 70):
        text = books[str(book)]
        matches = audit126.precompute_matches(text, available, min_len)
        candidate_pairs = {
            (source, length)
            for row in matches
            for source, length, _length_index in row
        }
        candidate_ends = {source + length for source, length in candidate_pairs}
        old_dp_state_count = (len(text) + 1) * 3
        pair_proxy = old_dp_state_count * max(1, len(candidate_pairs))
        end_proxy = old_dp_state_count * max(1, len(candidate_ends))
        copy_candidate_edges = sum(len(row) for row in matches)
        positions_with_copy_candidates = sum(1 for row in matches if row)
        # The active DP iterates previous-item and previous-end domains and scans
        # all copy candidates at each position. This proxy is intentionally
        # conservative and independent of Python implementation details.
        copy_transition_proxy = 3 * max(1, len(candidate_ends)) * copy_candidate_edges
        rows.append(
            {
                "book": book,
                "book_digits": len(text),
                "positions_with_copy_candidates": positions_with_copy_candidates,
                "copy_candidate_edges": copy_candidate_edges,
                "distinct_candidate_pair_states": len(candidate_pairs),
                "distinct_candidate_end_states": len(candidate_ends),
                "candidate_pair_to_end_delta": len(candidate_pairs) - len(candidate_ends),
                "old_reparse_state_count": old_dp_state_count,
                "pair_state_proxy": pair_proxy,
                "end_state_proxy": end_proxy,
                "copy_transition_proxy": copy_transition_proxy,
                "end_proxy_reduction": pair_proxy - end_proxy,
                "end_proxy_reduction_pct": (
                    100.0 * (pair_proxy - end_proxy) / pair_proxy if pair_proxy else 0.0
                ),
            }
        )
        available += text
    return rows


def cutoff_summary(rows: list[dict[str, Any]], cutoff: int) -> dict[str, Any]:
    total_pair = sum(row["pair_state_proxy"] for row in rows)
    total_end = sum(row["end_state_proxy"] for row in rows)
    total_old = sum(row["old_reparse_state_count"] for row in rows)
    total_transition = sum(row["copy_transition_proxy"] for row in rows)
    return {
        "cutoff": cutoff,
        "book_count": len(rows),
        "old_reparse_state_count": total_old,
        "pair_state_proxy": total_pair,
        "end_state_proxy": total_end,
        "copy_transition_proxy": total_transition,
        "end_proxy_multiplier_over_old_reparse": total_end / total_old,
        "copy_transition_multiplier_over_old_reparse": total_transition / total_old,
        "end_proxy_reduction_pct": (
            100.0 * (total_pair - total_end) / total_pair if total_pair else 0.0
        ),
        "books_at_or_below_thresholds": {
            str(threshold): sum(1 for row in rows if row["end_state_proxy"] <= threshold)
            for threshold in THRESHOLDS
        },
        "max_book_end_state_proxy": max(row["end_state_proxy"] for row in rows),
        "max_book_copy_transition_proxy": max(
            row["copy_transition_proxy"] for row in rows
        ),
        "largest_books_by_end_state_proxy": sorted(
            rows,
            key=lambda row: row["end_state_proxy"],
            reverse=True,
        )[:5],
        "largest_books_by_transition_proxy": sorted(
            rows,
            key=lambda row: row["copy_transition_proxy"],
            reverse=True,
        )[:5],
    }


def make_result() -> dict[str, Any]:
    gate71 = load_json(GATE71)
    assert_boundary("final_formula_dependency_refresh_gate", gate71)
    audit126 = load_module("audit126", AUDIT_126)
    formula = load_json(FINAL_FORMULA)
    books = {str(k): v for k, v in load_json(BOOKS_DIGITS).items()}

    cutoff_rows = []
    book_rows_by_cutoff = {}
    for cutoff in PREFIX_CUTOFFS:
        rows = candidate_graph_stats(
            formula=formula,
            books=books,
            audit126=audit126,
            cutoff=cutoff,
        )
        cutoff_rows.append(cutoff_summary(rows, cutoff))
        book_rows_by_cutoff[str(cutoff)] = rows

    total_old = sum(row["old_reparse_state_count"] for row in cutoff_rows)
    total_end = sum(row["end_state_proxy"] for row in cutoff_rows)
    total_transition = sum(row["copy_transition_proxy"] for row in cutoff_rows)
    cutoff60 = next(row for row in cutoff_rows if row["cutoff"] == 60)
    all_books_under_1m = all(
        row["books_at_or_below_thresholds"]["1000000"] == row["book_count"]
        for row in cutoff_rows
    )
    all_books_under_5m = all(
        row["books_at_or_below_thresholds"]["5000000"] == row["book_count"]
        for row in cutoff_rows
    )
    classification = (
        "final_source_length_parser_feasible_by_proxy_not_tractable_full_suffix"
        if all_books_under_1m
        else "final_source_length_parser_has_proxy_blockers"
    )
    interpretation = (
        "Compression to previous_copy_end keeps all per-book end-state proxies "
        "below one million, but the transition proxy is still hundreds to "
        "thousands of times the old frozen-count DP. A full suffix parser should "
        "be built with per-book pruning/caching or decomposed by hard books, not "
        "run as one naive cutoff-60 DP."
    )

    return {
        "schema": "final_source_length_parser_feasibility_audit.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "final_formula": rel(FINAL_FORMULA),
            "books_digits": rel(BOOKS_DIGITS),
            "audit126": rel(AUDIT_126),
            "gate71": rel(GATE71),
        },
        "scope": {
            "analysis_only": True,
            "compression_bound_changed": False,
            "new_formula_emitted": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
            "tested_cutoffs": PREFIX_CUTOFFS,
        },
        "summary": {
            "total_old_reparse_state_count": total_old,
            "total_end_state_proxy": total_end,
            "total_copy_transition_proxy": total_transition,
            "total_end_proxy_multiplier_over_old_reparse": total_end / total_old,
            "total_copy_transition_multiplier_over_old_reparse": (
                total_transition / total_old
            ),
            "all_books_below_1m_end_state_proxy": all_books_under_1m,
            "all_books_below_5m_end_state_proxy": all_books_under_5m,
            "cutoff60_max_book_end_state_proxy": cutoff60["max_book_end_state_proxy"],
            "cutoff60_max_book_copy_transition_proxy": cutoff60[
                "max_book_copy_transition_proxy"
            ],
            "cutoff60_books_below_250k": cutoff60["books_at_or_below_thresholds"][
                "250000"
            ],
            "cutoff60_book_count": cutoff60["book_count"],
            "cutoff_rows": cutoff_rows,
            "hardest_books_by_transition_proxy": sorted(
                [
                    {**book_row, "cutoff": int(cutoff)}
                    for cutoff, rows in book_rows_by_cutoff.items()
                    for book_row in rows
                ],
                key=lambda row: row["copy_transition_proxy"],
                reverse=True,
            )[:12],
            "interpretation": interpretation,
            "next_parser_requirements": [
                "Per-book active DP with progress counters and state pruning.",
                "Memoized source-default bits by previous_end and legal_source_count.",
                "Transition pruning before attempting a whole suffix parser.",
                "Separate promotion gate only if roundtrip, cost, and boundary invariants pass.",
            ],
        },
        "book_rows_by_cutoff": book_rows_by_cutoff,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "source_length_parser_status": "feasible_by_state_proxy_but_transition_heavy",
            "generation_explanation_status": "next_work_is_pruned_source_length_parser",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / "72_final_source_length_parser_feasibility_audit.json"
    md_path = TEST_RESULTS / "72_final_source_length_parser_feasibility_audit.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    lines = [
        "# Final Source/Length Parser Feasibility Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 71 showed that the final formula still needs a source/length parser.",
        "This audit recomputes candidate-state and transition proxies on the",
        "current `8154.676268`-bit formula to decide how to attack that parser",
        "without running an unbounded suffix DP.",
        "",
        "## Summary",
        "",
        f"- Total old frozen-count DP states: `{s['total_old_reparse_state_count']}`.",
        f"- Total previous-end state proxy: `{s['total_end_state_proxy']}`.",
        f"- Total copy-transition proxy: `{s['total_copy_transition_proxy']}`.",
        f"- End-state proxy multiplier over old DP: `{s['total_end_proxy_multiplier_over_old_reparse']:.1f}x`.",
        f"- Transition proxy multiplier over old DP: `{s['total_copy_transition_multiplier_over_old_reparse']:.1f}x`.",
        f"- All books below `1,000,000` end-state proxy: `{s['all_books_below_1m_end_state_proxy']}`.",
        f"- Cutoff 60 max book end-state proxy: `{s['cutoff60_max_book_end_state_proxy']}`.",
        f"- Cutoff 60 max book transition proxy: `{s['cutoff60_max_book_copy_transition_proxy']}`.",
        f"- Cutoff 60 books below `250,000` end-state proxy: `{s['cutoff60_books_below_250k']}/{s['cutoff60_book_count']}`.",
        "",
        "## Prefix Frontier",
        "",
        "| Cutoff | Books | Old states | End proxy | Transition proxy | End/old | Transition/old | <=250k | <=1m | Max transition |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in s["cutoff_rows"]:
        thresholds = row["books_at_or_below_thresholds"]
        lines.append(
            f"| `{row['cutoff']}` | `{row['book_count']}` | "
            f"`{row['old_reparse_state_count']}` | `{row['end_state_proxy']}` | "
            f"`{row['copy_transition_proxy']}` | "
            f"`{row['end_proxy_multiplier_over_old_reparse']:.1f}` | "
            f"`{row['copy_transition_multiplier_over_old_reparse']:.1f}` | "
            f"`{thresholds['250000']}` | `{thresholds['1000000']}` | "
            f"`{row['max_book_copy_transition_proxy']}` |"
        )

    lines.extend(
        [
            "",
            "## Hardest Books By Transition Proxy",
            "",
            "| Cutoff | Book | Digits | End proxy | Transition proxy | Copy edges | Distinct end states |",
            "|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in s["hardest_books_by_transition_proxy"]:
        lines.append(
            f"| `{row['cutoff']}` | `{row['book']}` | `{row['book_digits']}` | "
            f"`{row['end_state_proxy']}` | `{row['copy_transition_proxy']}` | "
            f"`{row['copy_candidate_edges']}` | `{row['distinct_candidate_end_states']}` |"
        )

    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- {s['interpretation']}",
            "- No compression-bound change is introduced.",
            "- No parser or recipe-discovery promotion is introduced.",
            "- Row0 remains unchanged and exogenous.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        ]
    )
    md_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
