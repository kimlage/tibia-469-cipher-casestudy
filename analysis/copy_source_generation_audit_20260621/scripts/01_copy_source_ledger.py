from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

PREQ = ROOT / "analysis" / "prequential_and_row0_origin_audit_20260621"
PREQ_RESULTS = PREQ / "reports" / "test_results"
GATE91_SCRIPT = PREQ / "scripts" / "91_full_source_exposure_audit.py"
GATE99 = PREQ_RESULTS / "99_exact_skeleton_dependency_ledger.json"
BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"

OUT_STEM = "01_copy_source_ledger"
SEED_BOOKS = list(range(10))
CANONICAL_CUTOFF = 10
CANONICAL_POLICY = "earliest_source"


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


def reconstruct_canonical_ops() -> dict[int, list[dict[str, Any]]]:
    gate91 = load_module("gate91_for_copy_source_ledger", GATE91_SCRIPT)
    captured_ops: dict[str, list[dict[str, Any]]] = {}
    original_compact_signature = gate91.compact_signature

    def capture_compact_signature(ops: list[dict[str, Any]]) -> str:
        signature = original_compact_signature(ops)
        previous = captured_ops.get(signature)
        if previous is not None and previous != ops:
            raise RuntimeError({"type": "signature_collision", "signature": signature})
        captured_ops[signature] = json.loads(json.dumps(ops))
        return signature

    gate91.compact_signature = capture_compact_signature
    gate86 = gate91.load_module("gate86_for_copy_source_ledger", gate91.GATE86_SCRIPT)
    gate82 = gate86.load_module("gate82_for_copy_source_ledger", gate86.GATE82_SCRIPT)
    gate77 = gate82.load_module("gate77_for_copy_source_ledger", gate82.GATE77_SCRIPT)
    rows = gate91.run_cutoff(
        CANONICAL_CUTOFF,
        gate77,
        gate82,
        policy=CANONICAL_POLICY,
    )
    result: dict[int, list[dict[str, Any]]] = {}
    for row in rows:
        result[int(row["book"])] = captured_ops[row["signature"]]
    return result


def matching_sources(emitted: str, chunk: str) -> list[int]:
    length = len(chunk)
    return [
        source
        for source in range(0, len(emitted) - length + 1)
        if emitted[source : source + length] == chunk
    ]


def extract_rows(
    ops_by_book: dict[int, list[dict[str, Any]]],
    books: dict[int, str],
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    emitted = "".join(books[book] for book in SEED_BOOKS)
    previous_source: int | None = None
    previous_end: int | None = None
    copy_rows: list[dict[str, Any]] = []
    serializable_ops: dict[str, list[dict[str, Any]]] = {}
    for book in sorted(ops_by_book):
        target = books[book]
        rendered = []
        serializable_ops[str(book)] = []
        for op_index, op in enumerate(ops_by_book[book]):
            start = int(op["target_start"])
            length = int(op["length"])
            target_chunk = target[start : start + length]
            if len(target_chunk) != length:
                raise RuntimeError({"book": book, "op_index": op_index, "type": "short_target"})
            if op["type"] == "literal":
                rendered.append(target_chunk)
                emitted += target_chunk
                serializable_ops[str(book)].append(
                    {
                        "type": "literal",
                        "target_start": start,
                        "length": length,
                        "forced": bool(op["forced"]),
                        "payload": target_chunk,
                    }
                )
                continue

            source = int(op["source"])
            chunk = emitted[source : source + length]
            if chunk != target_chunk:
                raise RuntimeError(
                    {
                        "book": book,
                        "op_index": op_index,
                        "type": "canonical_copy_mismatch",
                    }
                )
            legal_source_count = len(emitted) - length + 1
            matches = matching_sources(emitted, target_chunk)
            if source not in matches:
                raise RuntimeError({"book": book, "op_index": op_index, "type": "source_not_match"})
            row = {
                "book": book,
                "op_index": op_index,
                "target_start": start,
                "length": length,
                "forced": bool(op["forced"]),
                "available_len": len(emitted),
                "legal_source_count": legal_source_count,
                "canonical_source": source,
                "canonical_end": source + length,
                "matching_sources": matches,
                "matching_source_count": len(matches),
                "earliest_matching_source": matches[0],
                "latest_matching_source": matches[-1],
                "canonical_matching_rank": matches.index(source),
                "previous_source": previous_source,
                "previous_end": previous_end,
                "source_is_earliest_matching": source == matches[0],
                "source_is_latest_matching": source == matches[-1],
                "source_is_previous_source": previous_source == source,
                "source_is_previous_end": previous_end == source,
                "source_ends_at_previous_end": (
                    previous_end is not None and source + length == previous_end
                ),
                "target_chunk": target_chunk,
            }
            copy_rows.append(row)
            rendered.append(chunk)
            emitted += chunk
            serializable_ops[str(book)].append(
                {
                    "type": "copy",
                    "target_start": start,
                    "length": length,
                    "forced": bool(op["forced"]),
                    "source": source,
                }
            )
            previous_source = source
            previous_end = source + length
        if "".join(rendered) != target:
            raise RuntimeError({"book": book, "type": "book_roundtrip_failed"})
    return copy_rows, serializable_ops


def make_result() -> dict[str, Any]:
    gate99 = load_json(GATE99)
    assert_boundary("exact_skeleton_dependency_ledger", gate99)
    ops_by_book = reconstruct_canonical_ops()
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    rows, serializable_ops = extract_rows(ops_by_book, books)
    matching_counts = [int(row["matching_source_count"]) for row in rows]
    rank_bits = sum(math.log2(count) for count in matching_counts)
    source_bits = sum(math.log2(int(row["legal_source_count"])) for row in rows)
    summary = {
        "book_count": len(ops_by_book),
        "copy_event_count": len(rows),
        "total_matching_sources": sum(matching_counts),
        "min_matching_sources": min(matching_counts),
        "median_matching_sources": sorted(matching_counts)[len(matching_counts) // 2],
        "max_matching_sources": max(matching_counts),
        "single_matching_source_events": sum(1 for count in matching_counts if count == 1),
        "multi_matching_source_events": sum(1 for count in matching_counts if count > 1),
        "canonical_earliest_matching_events": sum(
            1 for row in rows if row["source_is_earliest_matching"]
        ),
        "canonical_latest_matching_events": sum(
            1 for row in rows if row["source_is_latest_matching"]
        ),
        "canonical_previous_source_events": sum(
            1 for row in rows if row["source_is_previous_source"]
        ),
        "canonical_previous_end_events": sum(
            1 for row in rows if row["source_is_previous_end"]
        ),
        "canonical_ends_at_previous_end_events": sum(
            1 for row in rows if row["source_ends_at_previous_end"]
        ),
        "oracle_rank_bits_among_matching_sources": rank_bits,
        "raw_absolute_source_bits": source_bits,
        "interpretation": (
            "This ledger grants the exact skeleton and literal payload, then maps "
            "the remaining copy-source dependency. Matching-source counts are "
            "diagnostic controls; using them to choose a source is target-aware."
        ),
    }
    return {
        "schema": "copy_source_ledger.v1",
        "classification": "copy_source_ledger_audit_only",
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "gate99_exact_skeleton_dependency_ledger": rel(GATE99),
            "gate91_full_source_exposure_script": rel(GATE91_SCRIPT),
            "books_digits": rel(BOOKS_DIGITS),
        },
        "scope": {
            "analysis_only": True,
            "exact_skeleton_granted": True,
            "literal_payload_granted": True,
            "copy_sources_not_granted": True,
            "matching_source_controls_are_target_aware": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
        },
        "summary": summary,
        "copy_rows": rows,
        "canonical_ops_by_book": serializable_ops,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": "copy_source_dependency_mapped",
            "copy_source_status": "external_after_skeleton_and_literal_payload",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / f"{OUT_STEM}.json"
    md_path = TEST_RESULTS / f"{OUT_STEM}.md"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    s = result["summary"]
    lines = [
        "# Copy Source Ledger",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Grant the exact source-free skeleton and literal payload, then map the",
        "remaining copy-source dependency.",
        "",
        "## Summary",
        "",
        f"- Copy events: `{s['copy_event_count']}`.",
        f"- Total matching sources under oracle target chunks: `{s['total_matching_sources']}`.",
        f"- Matching sources min/median/max: `{s['min_matching_sources']}` / `{s['median_matching_sources']}` / `{s['max_matching_sources']}`.",
        f"- Single-source events: `{s['single_matching_source_events']}`.",
        f"- Multi-source events: `{s['multi_matching_source_events']}`.",
        f"- Canonical earliest/latest matching events: `{s['canonical_earliest_matching_events']}` / `{s['canonical_latest_matching_events']}`.",
        f"- Canonical previous-source events: `{s['canonical_previous_source_events']}`.",
        f"- Canonical previous-end events: `{s['canonical_previous_end_events']}`.",
        f"- Source ending at previous end events: `{s['canonical_ends_at_previous_end_events']}`.",
        f"- Oracle rank bits among matching sources: `{s['oracle_rank_bits_among_matching_sources']:.3f}`.",
        f"- Raw absolute source bits: `{s['raw_absolute_source_bits']:.3f}`.",
        "",
        "## Decision",
        "",
        f"- {s['interpretation']}",
        "- No copy-source generator is promoted by this ledger.",
        "- Compression bound is unchanged.",
        "- Row0 remains exogenous and unchanged.",
        "- No plaintext, translation, semantic reading, or case reopening is introduced.",
    ]
    md_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    result = make_result()
    write_result(result)
    print(json.dumps(result["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
