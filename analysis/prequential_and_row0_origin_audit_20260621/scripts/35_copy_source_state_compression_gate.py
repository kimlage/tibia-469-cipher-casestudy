from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"
AUTHORIAL = ROOT / "analysis" / "authorial_mechanism_20260620"
AUTHORIAL_RESULTS = AUTHORIAL / "reports" / "test_results"

SOURCE_FORMULA = (
    AUTHORIAL
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_default_exception_formula_469.json"
)
BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
COMPILE_134 = AUTHORIAL / "scripts" / "134_op_type_derived_recipe_compile.py"
AUDIT_126 = AUTHORIAL / "scripts" / "126_prequential_recipe_reparse_audit.py"
COPY_SOURCE_DEFAULT = AUTHORIAL_RESULTS / "137_copy_source_default_decodability_audit.json"
ACTIVE_STATE_BOUNDARY = AUTHORIAL_RESULTS / "146_active_reparse_state_boundary_audit.json"
STATE_FREE_DEFAULT = AUTHORIAL_RESULTS / "147_copy_source_state_free_default_audit.json"

PREFIX_CUTOFFS = [10, 20, 35, 50, 60]


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


def assert_boundary(name: str, data: dict[str, Any], *, allow_bound_change: bool = False) -> None:
    if data.get("translation_delta") != "NONE":
        raise RuntimeError(f"{name} changed translation boundary")
    if data.get("case_reopened", False) is not False:
        raise RuntimeError(f"{name} reopened case")
    if data.get("plaintext_claim", False) is not False:
        raise RuntimeError(f"{name} introduced plaintext")
    boundary = data.get("boundary", {})
    decision = data.get("decision", {})
    if boundary.get("semantic_delta", decision.get("semantic_delta", "NONE")) != "NONE":
        raise RuntimeError(f"{name} introduced semantic delta")
    if (
        boundary.get("row0_origin_changed", decision.get("row0_origin_changed", False))
        is not False
    ):
        raise RuntimeError(f"{name} changed row0 origin")
    compression_changed = boundary.get(
        "compression_bound_changed",
        decision.get("compression_bound_changed", False),
    )
    if compression_changed is not False and not allow_bound_change:
        raise RuntimeError(f"{name} changed compression bound")
    if boundary.get("authorial_intent_claim", False) is not False:
        raise RuntimeError(f"{name} introduced authorial intent claim")


def previous_copy_before(formula: dict[str, Any], cutoff: int) -> tuple[int, int] | None:
    previous = None
    for book in map(str, formula["policy"]["book_order"]):
        if int(book) >= cutoff:
            break
        for op in formula["book_recipes"][book]["ops"]:
            if op["type"] == "copy":
                previous = (int(op["source_digit_pos"]), int(op["length"]))
    return previous


def active_path_end_states_for_books(
    formula: dict[str, Any],
    books: dict[str, str],
    *,
    cutoff: int,
) -> dict[str, Any]:
    previous_copy = previous_copy_before(formula, cutoff)
    previous_end = None if previous_copy is None else previous_copy[0] + previous_copy[1]
    previous_item = "BOS"
    pair_states = set()
    end_states = set()
    copy_rows = []
    default_hits = 0
    exception_hits = 0
    mismatch_count = 0

    for book in map(str, formula["policy"]["book_order"]):
        if int(book) < cutoff:
            continue
        position = 0
        for op_index, op in enumerate(formula["book_recipes"][book]["ops"]):
            pair_states.add((int(book), position, previous_item, previous_copy))
            end_states.add((int(book), position, previous_item, previous_end))
            if op["type"] == "copy":
                source = int(op["source_digit_pos"])
                length = int(op["length"])
                emitted_before = sum(len(books[str(prev_book)]) for prev_book in range(int(book))) + position
                legal_source_count = max(1, emitted_before - int(formula["policy"]["min_len"]) + 1)
                if previous_copy is None:
                    pair_default = 0
                else:
                    candidate = previous_copy[0] + previous_copy[1]
                    pair_default = candidate if candidate < legal_source_count else 0
                if previous_end is None:
                    end_default = 0
                else:
                    end_default = previous_end if previous_end < legal_source_count else 0
                if pair_default != end_default:
                    mismatch_count += 1
                if source == end_default:
                    default_hits += 1
                else:
                    exception_hits += 1
                copy_rows.append(
                    {
                        "book": int(book),
                        "op_index": op_index,
                        "book_pos": position,
                        "source_digit_pos": source,
                        "length": length,
                        "previous_pair_state": previous_copy,
                        "previous_end_state": previous_end,
                        "pair_default": pair_default,
                        "end_default": end_default,
                        "source_is_default": source == end_default,
                    }
                )
                previous_copy = (source, length)
                previous_end = source + length
            previous_item = op["type"]
            position += int(op["length"])
    return {
        "pair_state_count": len(pair_states),
        "end_state_count": len(end_states),
        "copy_count": len(copy_rows),
        "pair_to_end_state_delta": len(pair_states) - len(end_states),
        "pair_to_end_state_ratio": len(pair_states) / len(end_states) if end_states else 1.0,
        "distinct_previous_pair_states": len({row["previous_pair_state"] for row in copy_rows}),
        "distinct_previous_end_states": len({row["previous_end_state"] for row in copy_rows}),
        "source_default_hits": default_hits,
        "source_exception_hits": exception_hits,
        "pair_default_end_default_mismatch_count": mismatch_count,
        "sample_copy_rows": copy_rows[:5],
    }


def candidate_graph_stats(
    formula: dict[str, Any],
    books: dict[str, str],
    audit126,
    *,
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
        rows.append(
            {
                "book": book,
                "book_digits": len(text),
                "positions_with_copy_candidates": sum(1 for row in matches if row),
                "copy_candidate_edges": sum(len(row) for row in matches),
                "distinct_candidate_pair_states": len(candidate_pairs),
                "distinct_candidate_end_states": len(candidate_ends),
                "candidate_pair_to_end_delta": len(candidate_pairs) - len(candidate_ends),
                "old_reparse_state_count": old_dp_state_count,
                "pair_state_proxy": pair_proxy,
                "end_state_proxy": end_proxy,
                "end_proxy_reduction": pair_proxy - end_proxy,
                "end_proxy_reduction_pct": (
                    100.0 * (pair_proxy - end_proxy) / pair_proxy if pair_proxy else 0.0
                ),
            }
        )
        available += text
    return rows


def make_result() -> dict[str, Any]:
    compile134 = load_module("op_type_compile_134", COMPILE_134)
    audit126 = load_module("audit_126", AUDIT_126)
    formula = compile134.normalize_ops(load_json(SOURCE_FORMULA))
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}

    source_default = load_json(COPY_SOURCE_DEFAULT)
    active_state = load_json(ACTIVE_STATE_BOUNDARY)
    state_free = load_json(STATE_FREE_DEFAULT)
    assert_boundary("copy_source_default_decodability", source_default, allow_bound_change=True)
    assert_boundary("active_reparse_state_boundary", active_state)
    assert_boundary("copy_source_state_free_default", state_free)

    if source_default["model"]["default_rule"] != "previous copy source plus previous copy length if legal, else 0":
        raise RuntimeError("unexpected source default rule")

    rows = []
    total_pair_proxy = 0
    total_end_proxy = 0
    total_old = 0
    for cutoff in PREFIX_CUTOFFS:
        graph_rows = candidate_graph_stats(formula, books, audit126, cutoff=cutoff)
        active_path = active_path_end_states_for_books(formula, books, cutoff=cutoff)
        pair_proxy = sum(row["pair_state_proxy"] for row in graph_rows)
        end_proxy = sum(row["end_state_proxy"] for row in graph_rows)
        old_count = sum(row["old_reparse_state_count"] for row in graph_rows)
        total_pair_proxy += pair_proxy
        total_end_proxy += end_proxy
        total_old += old_count
        rows.append(
            {
                "cutoff": cutoff,
                "test_books": list(range(cutoff, 70)),
                "candidate_graph_summary": {
                    "books": len(graph_rows),
                    "old_reparse_state_count": old_count,
                    "pair_state_proxy": pair_proxy,
                    "end_state_proxy": end_proxy,
                    "end_proxy_reduction": pair_proxy - end_proxy,
                    "end_proxy_reduction_pct": (
                        100.0 * (pair_proxy - end_proxy) / pair_proxy
                        if pair_proxy
                        else 0.0
                    ),
                    "distinct_candidate_pair_states": sum(
                        row["distinct_candidate_pair_states"] for row in graph_rows
                    ),
                    "distinct_candidate_end_states": sum(
                        row["distinct_candidate_end_states"] for row in graph_rows
                    ),
                    "max_book_end_proxy_reduction_pct": max(
                        row["end_proxy_reduction_pct"] for row in graph_rows
                    ),
                },
                "active_recipe_path": active_path,
                "largest_books_by_end_proxy_reduction": sorted(
                    graph_rows,
                    key=lambda row: row["end_proxy_reduction"],
                    reverse=True,
                )[:5],
            }
        )

    source_rows = source_default["rows"]
    previous_end = None
    mismatch_rows = []
    default_hits = 0
    exception_hits = 0
    for row in source_rows:
        legal_count = int(row["legal_source_count"])
        expected = 0 if previous_end is None else (previous_end if previous_end < legal_count else 0)
        if expected != int(row["previous_source_plus_length_default"]):
            mismatch_rows.append(
                {
                    "book": row["book"],
                    "op_index": row["op_index"],
                    "expected_end_default": expected,
                    "recorded_pair_default": row["previous_source_plus_length_default"],
                }
            )
        if int(row["source_digit_pos"]) == expected:
            default_hits += 1
        else:
            exception_hits += 1
        previous_end = int(row["source_digit_pos"]) + int(row["length"])

    state_compression_valid = (
        not mismatch_rows
        and default_hits == int(source_default["model"]["default_count"])
        and exception_hits == int(source_default["model"]["exception_count"])
    )
    classification = (
        "copy_source_previous_end_state_compression_valid"
        if state_compression_valid
        else "copy_source_previous_end_state_compression_rejected"
    )

    return {
        "schema": "copy_source_state_compression_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "source_formula": rel(SOURCE_FORMULA),
            "books_digits": rel(BOOKS_DIGITS),
            "copy_source_default_decodability": rel(COPY_SOURCE_DEFAULT),
            "active_reparse_state_boundary": rel(ACTIVE_STATE_BOUNDARY),
            "copy_source_state_free_default": rel(STATE_FREE_DEFAULT),
        },
        "summary": {
            "old_state_key": active_state["scope"]["old_reparse_state_key"],
            "previous_pair_state_key": active_state["scope"][
                "active_reparse_state_key_required"
            ],
            "compressed_state_key": "(book_pos, previous_item, previous_copy_end)",
            "source_default_rule": source_default["model"]["default_rule"],
            "source_default_stream_bits": source_default["model"]["stream_bits"],
            "source_default_count": source_default["model"]["default_count"],
            "source_exception_count": source_default["model"]["exception_count"],
            "end_default_mismatch_count": len(mismatch_rows),
            "end_default_hits": default_hits,
            "end_exception_hits": exception_hits,
            "total_pair_state_proxy": total_pair_proxy,
            "total_end_state_proxy": total_end_proxy,
            "total_old_reparse_state_count": total_old,
            "total_end_proxy_reduction": total_pair_proxy - total_end_proxy,
            "total_end_proxy_reduction_pct": (
                100.0 * (total_pair_proxy - total_end_proxy) / total_pair_proxy
                if total_pair_proxy
                else 0.0
            ),
            "cutoff_rows": rows,
            "state_compression_valid": state_compression_valid,
            "recipe_discovery_removed": False,
            "parser_promoted": False,
            "best_state_free_default": state_free["decision"]["best_state_free_name"],
            "best_state_free_worse_than_active_total_bits": state_free["decision"][
                "best_state_free_worse_than_active_total_bits"
            ],
        },
        "decision": {
            "source_state_status": "previous_pair_state_compressed_to_previous_end",
            "recipe_discovery_status": "not_removed_parser_not_promoted",
            "compression_bound_status": "unchanged_8177_317_active_bound",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / "35_copy_source_state_compression_gate.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    cutoff10 = s["cutoff_rows"][0]["candidate_graph_summary"]
    lines = [
        "# Copy Source State Compression Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "The active source default was previously described as depending on",
        "`previous_copy_source` and `previous_copy_length`. This gate tests",
        "whether that state can be compressed to the decoder-equivalent scalar",
        "`previous_copy_end = previous_copy_source + previous_copy_length`",
        "without changing default/exception classification.",
        "",
        "## Summary",
        "",
        f"- Previous pair state key: `{s['previous_pair_state_key']}`.",
        f"- Compressed state key: `{s['compressed_state_key']}`.",
        f"- Source default stream bits preserved: `{s['source_default_stream_bits']:.3f}`.",
        f"- Default/exception counts preserved: `{s['end_default_hits']}` / `{s['end_exception_hits']}`.",
        f"- End-default mismatches: `{s['end_default_mismatch_count']}`.",
        f"- Total candidate state proxy: `{s['total_pair_state_proxy']}` -> `{s['total_end_state_proxy']}`.",
        f"- Total proxy reduction: `{s['total_end_proxy_reduction']}` (`{s['total_end_proxy_reduction_pct']:.3f}%`).",
        f"- Cutoff-10 proxy: `{cutoff10['pair_state_proxy']}` -> `{cutoff10['end_state_proxy']}`.",
        f"- Cutoff-10 proxy reduction: `{cutoff10['end_proxy_reduction']}` (`{cutoff10['end_proxy_reduction_pct']:.3f}%`).",
        f"- Best fully state-free source default remains `{s['best_state_free_default']}`, `{s['best_state_free_worse_than_active_total_bits']:.3f}` bits worse.",
        "",
        "## Interpretation",
        "",
        "The active source default does not need the full previous copy pair for",
        "future source-cost classification; `previous_copy_end` is sufficient.",
        "This reduces the path-state proxy while preserving the same",
        "default/exception ledger. It is still not a complete active parser:",
        "recipe discovery remains unproved, and the state is compressed rather",
        "than eliminated.",
        "",
        "## Boundary",
        "",
        "- No compression-bound change is introduced.",
        "- No parser or recipe-discovery promotion is introduced.",
        "- Row0 origin remains unchanged and exogenous.",
        "- No plaintext, translation, semantic reading, or case reopening is introduced.",
    ]
    (TEST_RESULTS / "35_copy_source_state_compression_gate.md").write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
