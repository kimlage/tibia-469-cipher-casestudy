from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

STATE_COMPRESSION_GATE = TEST_RESULTS / "35_copy_source_state_compression_gate.json"
ACTIVE_STATE_BOUNDARY = (
    ROOT
    / "analysis"
    / "authorial_mechanism_20260620"
    / "reports"
    / "test_results"
    / "146_active_reparse_state_boundary_audit.json"
)
GATE35_SCRIPT = HERE / "scripts" / "35_copy_source_state_compression_gate.py"

SOURCE_STATE_THRESHOLDS = [100_000, 250_000, 1_000_000]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
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
    if decision.get("translation_or_plaintext_status", "NONE") != "NONE":
        raise RuntimeError(f"{name} introduced plaintext status")
    if decision.get("row0_origin_status") not in {None, "unchanged_exogenous"}:
        raise RuntimeError(f"{name} changed row0 origin")


def graph_frontier_rows() -> list[dict[str, Any]]:
    gate35 = load_module("gate35_copy_source_state_compression", GATE35_SCRIPT)
    compile134 = gate35.load_module("op_type_compile_134", gate35.COMPILE_134)
    audit126 = gate35.load_module("audit_126", gate35.AUDIT_126)
    formula = compile134.normalize_ops(gate35.load_json(gate35.SOURCE_FORMULA))
    books = {str(key): value for key, value in gate35.load_json(gate35.BOOKS_DIGITS).items()}

    rows = []
    for cutoff in gate35.PREFIX_CUTOFFS:
        graph_rows = gate35.candidate_graph_stats(formula, books, audit126, cutoff=cutoff)
        rows.append(
            {
                "cutoff": cutoff,
                "book_count": len(graph_rows),
                "old_reparse_state_count": sum(row["old_reparse_state_count"] for row in graph_rows),
                "pair_state_proxy": sum(row["pair_state_proxy"] for row in graph_rows),
                "end_state_proxy": sum(row["end_state_proxy"] for row in graph_rows),
                "max_book_pair_state_proxy": max(row["pair_state_proxy"] for row in graph_rows),
                "max_book_end_state_proxy": max(row["end_state_proxy"] for row in graph_rows),
                "books_at_or_below_thresholds": {
                    str(threshold): sum(
                        1 for row in graph_rows if row["end_state_proxy"] <= threshold
                    )
                    for threshold in SOURCE_STATE_THRESHOLDS
                },
                "largest_books_by_end_state_proxy": sorted(
                    graph_rows,
                    key=lambda row: row["end_state_proxy"],
                    reverse=True,
                )[:5],
            }
        )
    return rows


def make_result() -> dict[str, Any]:
    state_compression = load_json(STATE_COMPRESSION_GATE)
    active_state = load_json(ACTIVE_STATE_BOUNDARY)
    assert_boundary("copy_source_state_compression_gate", state_compression)
    assert_boundary("active_reparse_state_boundary", active_state)

    if not state_compression["summary"]["state_compression_valid"]:
        raise RuntimeError("state compression was not valid")
    if state_compression["summary"]["parser_promoted"]:
        raise RuntimeError("unexpected parser promotion in input gate")

    frontier_rows = graph_frontier_rows()
    total_old = sum(row["old_reparse_state_count"] for row in frontier_rows)
    total_pair = sum(row["pair_state_proxy"] for row in frontier_rows)
    total_end = sum(row["end_state_proxy"] for row in frontier_rows)
    max_book_end = max(row["max_book_end_state_proxy"] for row in frontier_rows)
    min_cutoff_all_books_below_1m = min(
        row["cutoff"]
        for row in frontier_rows
        if row["books_at_or_below_thresholds"]["1000000"] == row["book_count"]
    )
    cutoff60 = next(row for row in frontier_rows if row["cutoff"] == 60)

    enriched_rows = []
    by_cutoff = {
        row["cutoff"]: row
        for row in state_compression["summary"]["cutoff_rows"]
    }
    for row in frontier_rows:
        prior = by_cutoff[row["cutoff"]]
        active_path = prior["active_recipe_path"]
        enriched = dict(row)
        enriched["pair_proxy_multiplier_over_old_reparse"] = (
            row["pair_state_proxy"] / row["old_reparse_state_count"]
        )
        enriched["end_proxy_multiplier_over_old_reparse"] = (
            row["end_state_proxy"] / row["old_reparse_state_count"]
        )
        enriched["pair_to_end_proxy_reduction_pct"] = (
            100.0
            * (row["pair_state_proxy"] - row["end_state_proxy"])
            / row["pair_state_proxy"]
        )
        enriched["active_recipe_path_pair_states"] = active_path["pair_state_count"]
        enriched["active_recipe_path_end_states"] = active_path["end_state_count"]
        enriched["active_recipe_path_pair_to_end_ratio"] = active_path[
            "pair_to_end_state_ratio"
        ]
        enriched_rows.append(enriched)

    all_books_under_1m = all(
        row["books_at_or_below_thresholds"]["1000000"] == row["book_count"]
        for row in frontier_rows
    )
    classification = (
        "source_state_frontier_reduced_parser_still_unpromoted"
        if all_books_under_1m
        else "source_state_frontier_still_has_book_level_proxy_blockers"
    )

    return {
        "schema": "active_reparse_feasibility_after_state_compression_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "copy_source_state_compression_gate": rel(STATE_COMPRESSION_GATE),
            "active_reparse_state_boundary": rel(ACTIVE_STATE_BOUNDARY),
            "gate35_script_reused_for_candidate_graphs": rel(GATE35_SCRIPT),
        },
        "summary": {
            "old_state_key": active_state["scope"]["old_reparse_state_key"],
            "pre_compression_required_state_key": active_state["scope"][
                "active_reparse_state_key_required"
            ],
            "compressed_source_state_key": state_compression["summary"][
                "compressed_state_key"
            ],
            "source_default_stream_bits": state_compression["summary"][
                "source_default_stream_bits"
            ],
            "source_default_count": state_compression["summary"]["source_default_count"],
            "source_exception_count": state_compression["summary"][
                "source_exception_count"
            ],
            "end_default_mismatch_count": state_compression["summary"][
                "end_default_mismatch_count"
            ],
            "total_old_reparse_state_count": total_old,
            "total_pair_state_proxy": total_pair,
            "total_end_state_proxy": total_end,
            "total_pair_proxy_multiplier_over_old_reparse": total_pair / total_old,
            "total_end_proxy_multiplier_over_old_reparse": total_end / total_old,
            "total_pair_to_end_proxy_reduction_pct": (
                100.0 * (total_pair - total_end) / total_pair
            ),
            "max_book_end_state_proxy": max_book_end,
            "all_books_below_1m_end_state_proxy": all_books_under_1m,
            "min_cutoff_all_books_below_1m_end_state_proxy": min_cutoff_all_books_below_1m,
            "cutoff60_max_book_end_state_proxy": cutoff60["max_book_end_state_proxy"],
            "cutoff60_books_below_250k": cutoff60["books_at_or_below_thresholds"][
                "250000"
            ],
            "cutoff60_book_count": cutoff60["book_count"],
            "frontier_rows": enriched_rows,
            "parser_promoted": False,
            "recipe_discovery_removed": False,
            "source_state_dimension_result": (
                "compressed previous-copy-end state makes source-state book-local "
                "prototypes tractable by proxy, but this gate does not implement "
                "or promote a complete active parser"
            ),
            "remaining_blockers": [
                "The DP still has to reproduce the full active objective, not only source-default classification.",
                "Literal payload, item type, copy length, copy source, and copy length selection remain recipe/ledger dependencies.",
                "Adaptive-count and tie-breaking behavior must be specified in any promoted active parser.",
                "Row0/table origin remains entirely outside this source-state question.",
            ],
        },
        "decision": {
            "source_state_feasibility_status": "source_state_dimension_reduced_book_local_prototype_plausible",
            "recipe_discovery_status": "not_removed_parser_not_promoted",
            "compression_bound_status": "unchanged_8177_317_active_bound",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / "36_active_reparse_feasibility_after_state_compression_gate.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    rows = s["frontier_rows"]
    lines = [
        "# Active Reparse Feasibility After State Compression Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 35 proved that active copy-source defaults only need",
        "`previous_copy_end`, not the full previous `(source, length)` pair.",
        "This gate asks what that buys operationally for exact active reparse,",
        "and where the parser boundary still remains.",
        "",
        "## Summary",
        "",
        f"- Old reparse state key: `{s['old_state_key']}`.",
        f"- Pre-compression required source state: `{s['pre_compression_required_state_key']}`.",
        f"- Compressed source state: `{s['compressed_source_state_key']}`.",
        f"- Source default stream preserved: `{s['source_default_stream_bits']:.3f}` bits.",
        f"- Default/exception counts: `{s['source_default_count']}` / `{s['source_exception_count']}`.",
        f"- End-default mismatches: `{s['end_default_mismatch_count']}`.",
        f"- Aggregate proxy: `{s['total_pair_state_proxy']}` -> `{s['total_end_state_proxy']}`.",
        f"- Aggregate proxy reduction: `{s['total_pair_to_end_proxy_reduction_pct']:.3f}%`.",
        f"- End-state proxy remains `{s['total_end_proxy_multiplier_over_old_reparse']:.1f}x` the old DP state count.",
        f"- Max book-level end-state proxy: `{s['max_book_end_state_proxy']}`.",
        f"- All tested suffix books are below `1,000,000` end-state proxy: `{s['all_books_below_1m_end_state_proxy']}`.",
        f"- Cutoff 60 has `{s['cutoff60_books_below_250k']}/{s['cutoff60_book_count']}` books below `250,000` end-state proxy.",
        "",
        "## Prefix Frontier",
        "",
        "| Cutoff | Books | Old states | Pair proxy | End proxy | End/old | Max book end proxy | <=100k | <=250k | <=1m |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        thresholds = row["books_at_or_below_thresholds"]
        lines.append(
            f"| `{row['cutoff']}` | `{row['book_count']}` | "
            f"`{row['old_reparse_state_count']}` | `{row['pair_state_proxy']}` | "
            f"`{row['end_state_proxy']}` | "
            f"`{row['end_proxy_multiplier_over_old_reparse']:.1f}` | "
            f"`{row['max_book_end_state_proxy']}` | `{thresholds['100000']}` | "
            f"`{thresholds['250000']}` | `{thresholds['1000000']}` |"
        )

    lines.extend(
        [
            "",
            "## Largest Book-Level End-State Proxies",
            "",
            "| Cutoff | Book | End proxy | Pair proxy | Old states | Distinct end states | Reduction |",
            "|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in rows:
        for book in row["largest_books_by_end_state_proxy"][:3]:
            lines.append(
                f"| `{row['cutoff']}` | `{book['book']}` | "
                f"`{book['end_state_proxy']}` | `{book['pair_state_proxy']}` | "
                f"`{book['old_reparse_state_count']}` | "
                f"`{book['distinct_candidate_end_states']}` | "
                f"`{book['end_proxy_reduction_pct']:.3f}%` |"
            )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The source-state dimension is no longer the same hard blocker it was in",
            "gate 146: every tested book-level source-state proxy falls below one",
            "million after compression to `previous_copy_end`, and the late cutoff",
            "frontier is substantially smaller. That is enough to justify a future",
            "book-local prototype.",
            "",
            "It is not enough to promote exact active reparse. The end-state proxy is",
            "still hundreds of times larger than the old frozen-count DP, and this",
            "gate does not solve adaptive counts, tie-breaking, copy source",
            "selection, copy length declaration, literal payload, or item-type",
            "ledger dependencies.",
            "",
            "## Boundary",
            "",
            "- No compression-bound change is introduced.",
            "- No parser or recipe-discovery promotion is introduced.",
            "- Row0 origin remains unchanged and exogenous.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        ]
    )
    (TEST_RESULTS / "36_active_reparse_feasibility_after_state_compression_gate.md").write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
