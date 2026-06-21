from __future__ import annotations

import importlib.util
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

SKELETON_SCRIPT = (
    ROOT
    / "analysis"
    / "source_free_skeleton_generation_audit_20260621"
    / "scripts"
    / "02_source_free_skeleton_grammar_gate.py"
)
SKELETON_LEDGER = (
    ROOT
    / "analysis"
    / "source_free_skeleton_generation_audit_20260621"
    / "reports"
    / "test_results"
    / "01_hard_boundary_ledger.json"
)
BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"

OUT_STEM = "01_literal_payload_ledger"
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


def extract_literal_rows() -> tuple[list[dict[str, Any]], dict[int, list[dict[str, Any]]]]:
    skeleton_module = load_module("source_free_skeleton_for_literal_payload", SKELETON_SCRIPT)
    by_book = skeleton_module.reconstruct_canonical_skeleton()
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    emitted = "".join(books[book] for book in SEED_BOOKS)
    rows = []
    previous_literal_payloads: list[str] = []
    for book in sorted(by_book):
        target = books[book]
        for op_index, op in enumerate(by_book[book]):
            start = int(op["target_start"])
            length = int(op["length"])
            chunk = target[start : start + length]
            if len(chunk) != length:
                raise RuntimeError({"book": book, "op_index": op_index, "type": "short_chunk"})
            if op["type"] == "literal":
                previous_occurrence = emitted.find(chunk)
                previous_literal_seen = chunk in previous_literal_payloads
                rows.append(
                    {
                        "book": book,
                        "op_index": op_index,
                        "target_start": start,
                        "length": length,
                        "forced": bool(op["forced"]),
                        "payload": chunk,
                        "previous_occurrence": previous_occurrence,
                        "whole_chunk_seen_before": previous_occurrence != -1,
                        "previous_literal_seen": previous_literal_seen,
                        "digits": list(chunk),
                    }
                )
                previous_literal_payloads.append(chunk)
            emitted += chunk
    return rows, by_book


def digit_entropy_bits(payload: str) -> float:
    counts = Counter(payload)
    total = len(payload)
    return -sum((count / total) * math.log2(count / total) for count in counts.values()) * total


def make_result() -> dict[str, Any]:
    skeleton_ledger = load_json(SKELETON_LEDGER)
    assert_boundary("source_free_skeleton_hard_boundary", skeleton_ledger)
    rows, by_book = extract_literal_rows()
    payload = "".join(row["payload"] for row in rows)
    length_counts = Counter(int(row["length"]) for row in rows)
    payload_counts = Counter(row["payload"] for row in rows)
    repeated_payload_rows = [row for row in rows if payload_counts[row["payload"]] > 1]
    previous_seen_rows = [row for row in rows if row["whole_chunk_seen_before"]]
    previous_literal_rows = [row for row in rows if row["previous_literal_seen"]]
    raw_uniform_bits = len(payload) * math.log2(10)
    empirical_digit_bits = digit_entropy_bits(payload)
    promotes_generator = False
    return {
        "schema": "literal_payload_ledger.v1",
        "classification": "literal_payload_ledger_audit_only",
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "source_free_skeleton_hard_boundary": rel(SKELETON_LEDGER),
            "source_free_skeleton_script": rel(SKELETON_SCRIPT),
            "books_digits": rel(BOOKS_DIGITS),
        },
        "scope": {
            "analysis_only": True,
            "skeleton_granted": True,
            "copy_sources_not_predicted": True,
            "payload_generation_not_promoted": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
        },
        "summary": {
            "book_count": len(by_book),
            "literal_chunk_count": len(rows),
            "literal_digit_count": len(payload),
            "unique_payload_chunks": len(payload_counts),
            "repeated_payload_chunk_rows": len(repeated_payload_rows),
            "repeated_payload_digits": sum(int(row["length"]) for row in repeated_payload_rows),
            "whole_chunk_seen_before_rows": len(previous_seen_rows),
            "whole_chunk_seen_before_digits": sum(int(row["length"]) for row in previous_seen_rows),
            "previous_literal_seen_rows": len(previous_literal_rows),
            "previous_literal_seen_digits": sum(int(row["length"]) for row in previous_literal_rows),
            "length_counts": dict(sorted(length_counts.items())),
            "digit_counts": dict(sorted(Counter(payload).items())),
            "raw_uniform_bits": raw_uniform_bits,
            "empirical_digit_histogram_bits": empirical_digit_bits,
            "empirical_digit_histogram_savings": raw_uniform_bits - empirical_digit_bits,
            "promotes_generator": promotes_generator,
            "interpretation": (
                "This ledger maps literal payload after the exact skeleton is "
                "granted. Repetition and prior occurrence are diagnostic only; "
                "a generator still needs a source-free rule for which payload "
                "digits to emit."
            ),
        },
        "literal_rows": rows,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": "literal_payload_external_mapped",
            "literal_payload_status": "external_after_skeleton",
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
        "# Literal Payload Ledger",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Map the literal payload left external after the exact source-free",
        "skeleton is granted.",
        "",
        "## Summary",
        "",
        f"- Literal chunks: `{s['literal_chunk_count']}`.",
        f"- Literal digits: `{s['literal_digit_count']}`.",
        f"- Unique payload chunks: `{s['unique_payload_chunks']}`.",
        f"- Repeated payload rows/digits: `{s['repeated_payload_chunk_rows']}` / `{s['repeated_payload_digits']}`.",
        f"- Whole chunks seen before in emitted text: `{s['whole_chunk_seen_before_rows']}` / `{s['whole_chunk_seen_before_digits']}` digits.",
        f"- Previous-literal repeats: `{s['previous_literal_seen_rows']}` / `{s['previous_literal_seen_digits']}` digits.",
        f"- Raw uniform payload bits: `{s['raw_uniform_bits']:.3f}`.",
        f"- Empirical digit-histogram savings: `{s['empirical_digit_histogram_savings']:.3f}` bits.",
        "",
        "## Decision",
        "",
        f"- Promotes generator: `{s['promotes_generator']}`.",
        f"- {s['interpretation']}",
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
