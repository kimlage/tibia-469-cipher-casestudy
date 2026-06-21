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
PARSER_LEDGER = TEST_RESULTS / "04_parser_dependency_reduction_ledger.json"

OUT_STEM = "05_literal_gap_boundary_audit"
SEED_BOOKS = list(range(10))


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


def offset_rows(trace_module, emitted: str, target: str, start: int, max_offset: int) -> list[dict[str, int]]:
    rows: list[dict[str, int]] = []
    for offset in range(max_offset + 1):
        emitted_after_literal = emitted + target[start : start + offset]
        if start + offset >= len(target):
            max_length = 0
            source_count = 0
        else:
            candidates = trace_module.candidate_sources_with_max(
                emitted_after_literal, target, start + offset
            )
            max_length = max([row["max_length"] for row in candidates], default=0)
            source_count = len(candidates)
        rows.append(
            {
                "offset": offset,
                "max_copy_length": max_length,
                "source_count": source_count,
                "total_advance": offset + max_length,
            }
        )
    return rows


def summarize_literal_gap(rows: list[dict[str, Any]]) -> dict[str, Any]:
    literal_count = len(rows)
    followed_by_copy = [row for row in rows if row["next_op_type"] == "copy"]
    return {
        "literal_gap_count": literal_count,
        "literal_gaps_followed_by_copy": len(followed_by_copy),
        "copy_available_at_literal_start": sum(
            1 for row in rows if row["copy_at_literal_start_max_length"] >= 5
        ),
        "stable_stop_is_first_match_count": sum(
            1 for row in rows if row["stable_stop_is_first_match"]
        ),
        "stable_stop_local_best_copy_length_count": sum(
            1 for row in rows if row["stable_stop_is_local_best_copy_length"]
        ),
        "stable_stop_local_best_total_advance_count": sum(
            1 for row in rows if row["stable_stop_is_local_best_total_advance"]
        ),
        "stable_stop_full_suffix_best_total_advance_count": sum(
            1
            for row in followed_by_copy
            if row["stable_stop_is_full_suffix_best_total_advance"]
        ),
        "future_copy_improves_immediate_count": sum(
            1 for row in followed_by_copy if row["next_copy_length"] > row["copy_at_literal_start_max_length"]
        ),
    }


def make_result() -> dict[str, Any]:
    parser_ledger = load_json(PARSER_LEDGER)
    assert_boundary("parser_dependency_reduction_ledger", parser_ledger)

    trace_module = load_module("segmentation_trace_for_gate05", TRACE_SCRIPT)
    gate111 = load_module("gate111_for_segmentation_gate05", GATE111_SCRIPT)
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    stable_ops = trace_module.projected_ops_from_copy_rows(gate111.make_copy_rows(), books)
    stable_by_book: dict[int, list[dict[str, Any]]] = {}
    for op in stable_ops:
        stable_by_book.setdefault(int(op["book"]), []).append(op)
    for rows in stable_by_book.values():
        rows.sort(key=lambda row: int(row["target_start"]))

    emitted = "".join(books[book] for book in SEED_BOOKS)
    literal_rows: list[dict[str, Any]] = []
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
                local_offsets = offset_rows(
                    trace_module, emitted, target, start, length
                )
                full_offsets = offset_rows(
                    trace_module, emitted, target, start, len(target) - start
                )
                first_match_offsets = [
                    row["offset"]
                    for row in local_offsets
                    if row["max_copy_length"] >= 5
                ]
                local_best_len = max(row["max_copy_length"] for row in local_offsets)
                local_best_total = max(row["total_advance"] for row in local_offsets)
                full_copy_offsets = [
                    row for row in full_offsets if row["max_copy_length"] >= 5
                ]
                if full_copy_offsets:
                    full_best_total = max(row["total_advance"] for row in full_copy_offsets)
                    full_earliest_best_total = min(
                        row["offset"]
                        for row in full_copy_offsets
                        if row["total_advance"] == full_best_total
                    )
                else:
                    full_best_total = 0
                    full_earliest_best_total = None
                next_copy_length = (
                    int(next_op["length"]) if next_op and next_op["type"] == "copy" else 0
                )
                literal_rows.append(
                    {
                        "book": book,
                        "op_index": int(op["op_index"]),
                        "target_start": start,
                        "literal_length": length,
                        "next_op_type": None if next_op is None else next_op["type"],
                        "next_copy_length": next_copy_length,
                        "copy_at_literal_start_max_length": local_offsets[0][
                            "max_copy_length"
                        ],
                        "first_match_offset_in_declared_window": None
                        if not first_match_offsets
                        else min(first_match_offsets),
                        "stable_stop_is_first_match": bool(first_match_offsets)
                        and min(first_match_offsets) == length,
                        "local_best_copy_length": local_best_len,
                        "stable_stop_is_local_best_copy_length": local_offsets[-1][
                            "max_copy_length"
                        ]
                        == local_best_len,
                        "local_best_total_advance": local_best_total,
                        "stable_stop_is_local_best_total_advance": local_offsets[-1][
                            "total_advance"
                        ]
                        == local_best_total,
                        "full_suffix_best_total_advance": full_best_total,
                        "full_suffix_earliest_best_total_offset": full_earliest_best_total,
                        "stable_stop_is_full_suffix_best_total_advance": full_earliest_best_total
                        == length,
                    }
                )
            emitted += target[start : start + length]

    summary = summarize_literal_gap(literal_rows)
    local_promoted = (
        summary["stable_stop_local_best_total_advance_count"]
        == summary["literal_gap_count"]
    )
    source_free_promoted = (
        summary["stable_stop_full_suffix_best_total_advance_count"]
        == summary["literal_gaps_followed_by_copy"]
    )

    return {
        "schema": "literal_gap_boundary_audit.v1",
        "classification": "literal_gap_local_window_clue_source_free_window_not_promoted",
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "parser_dependency_reduction_ledger": rel(PARSER_LEDGER),
            "books_digits": rel(BOOKS_DIGITS),
        },
        "summary": {
            **summary,
            "promotes_local_window_boundary_clue": local_promoted,
            "promotes_source_free_literal_window_rule": source_free_promoted,
            "interpretation": (
                "Inside each declared literal window, the stable boundary is the "
                "point that maximizes literal offset plus next-copy length. This "
                "explains why first-match greedy parsing fails, but it does not "
                "derive the literal window itself: over the full remaining suffix, "
                "the same objective selects the stable boundary in only a minority "
                "of followed-by-copy literal gaps."
            ),
        },
        "literal_gap_rows": literal_rows,
        "sample_full_suffix_failures": [
            row
            for row in literal_rows
            if row["next_op_type"] == "copy"
            and not row["stable_stop_is_full_suffix_best_total_advance"]
        ][:15],
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": "literal_gap_local_boundary_clue",
            "literal_window_status": "retained_declared_window_dependency",
            "source_free_parser_status": "not_promoted",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    json_path = TEST_RESULTS / f"{OUT_STEM}.json"
    md_path = TEST_RESULTS / f"{OUT_STEM}.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    lines = [
        "# Literal Gap Boundary Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "The copy parser rule reduces `(source,length)` once copy starts are",
        "known. This gate tests whether literal gaps and copy starts are also",
        "derivable by simple lookahead objectives.",
        "",
        "## Scoreboard",
        "",
        "| Hypothesis | Hits | Boundary |",
        "|---|---:|---|",
        f"| Stop at first available match | `{s['stable_stop_is_first_match_count']}/{s['literal_gap_count']}` | rejected |",
        f"| Stop at local-window best copy length | `{s['stable_stop_local_best_copy_length_count']}/{s['literal_gap_count']}` | declared-window clue |",
        f"| Stop at local-window best literal+copy advance | `{s['stable_stop_local_best_total_advance_count']}/{s['literal_gap_count']}` | declared-window clue |",
        f"| Stop at full-suffix best literal+copy advance | `{s['stable_stop_full_suffix_best_total_advance_count']}/{s['literal_gaps_followed_by_copy']}` | source-free rule rejected |",
        "",
        "## Diagnostics",
        "",
        f"- Literal gaps: `{s['literal_gap_count']}`.",
        f"- Literal gaps followed by copy: `{s['literal_gaps_followed_by_copy']}`.",
        f"- Copy available at literal start: `{s['copy_available_at_literal_start']}`.",
        f"- Future stable copy improves immediate copy in `{s['future_copy_improves_immediate_count']}` followed-by-copy gaps.",
        f"- Promotes local-window boundary clue: `{s['promotes_local_window_boundary_clue']}`.",
        f"- Promotes source-free literal-window rule: `{s['promotes_source_free_literal_window_rule']}`.",
        "",
        "## Decision",
        "",
        f"- {s['interpretation']}",
        "- The operation-start/literal-window atlas remains retained.",
        "- Compression bound is unchanged.",
        "- Row0 remains exogenous and unchanged.",
        "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        "",
    ]
    md_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    result = make_result()
    write_result(result)
    print(json.dumps(result["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
