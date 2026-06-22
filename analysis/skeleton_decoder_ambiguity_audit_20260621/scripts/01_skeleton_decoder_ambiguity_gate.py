from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path
from statistics import mean, median
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
SKELETON_SCRIPT = (
    ROOT
    / "analysis"
    / "source_free_skeleton_generation_audit_20260621"
    / "scripts"
    / "02_source_free_skeleton_grammar_gate.py"
)
GATE98 = (
    ROOT
    / "analysis"
    / "prequential_and_row0_origin_audit_20260621"
    / "reports"
    / "test_results"
    / "98_full_source_exact_skeleton_invariance.json"
)
GATE99 = (
    ROOT
    / "analysis"
    / "prequential_and_row0_origin_audit_20260621"
    / "reports"
    / "test_results"
    / "99_exact_skeleton_dependency_ledger.json"
)

OUT_STEM = "01_skeleton_decoder_ambiguity_gate"
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


def reconstruct_skeleton() -> dict[int, list[dict[str, Any]]]:
    module = load_module("source_free_skeleton_for_decoder_ambiguity", SKELETON_SCRIPT)
    return module.reconstruct_canonical_skeleton()


def find_occurrences(haystack: str, needle: str) -> list[int]:
    out: list[int] = []
    start = 0
    while True:
        index = haystack.find(needle, start)
        if index < 0:
            return out
        out.append(index)
        start = index + 1


def safe_log2(value: int) -> float:
    if value <= 1:
        return 0.0
    return math.log2(value)


def summarize_numeric(values: list[int]) -> dict[str, Any]:
    if not values:
        return {"min": 0, "median": 0, "mean": 0.0, "max": 0}
    return {
        "min": min(values),
        "median": median(values),
        "mean": mean(values),
        "max": max(values),
    }


def make_rows(
    books: dict[int, str],
    skeleton_by_book: dict[int, list[dict[str, Any]]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    copy_rows: list[dict[str, Any]] = []
    literal_rows: list[dict[str, Any]] = []
    emitted = "".join(books[index] for index in SEED_BOOKS)
    for book in sorted(skeleton_by_book):
        if book < 10:
            continue
        target = books[book]
        local_emitted = ""
        for op_index, op in enumerate(skeleton_by_book[book]):
            target_start = int(op["target_start"])
            length = int(op["length"])
            available = emitted + local_emitted
            if len(local_emitted) != target_start:
                raise RuntimeError(
                    {
                        "book": book,
                        "op_index": op_index,
                        "expected_target_start": target_start,
                        "actual_local_emitted": len(local_emitted),
                    }
                )
            chunk = target[target_start : target_start + length]
            if len(chunk) != length:
                raise RuntimeError({"book": book, "op_index": op_index, "length": length})
            if op["type"] == "literal":
                literal_rows.append(
                    {
                        "book": book,
                        "op_index": op_index,
                        "target_start": target_start,
                        "length": length,
                        "payload_digits": length,
                        "payload_log10_choices": length,
                    }
                )
                local_emitted += chunk
                continue
            if op["type"] != "copy":
                raise RuntimeError(op)

            legal_source_count = max(0, len(available) - length + 1)
            matching_sources = find_occurrences(available, chunk)
            if not matching_sources:
                raise RuntimeError(
                    {
                        "book": book,
                        "op_index": op_index,
                        "target_start": target_start,
                        "length": length,
                        "type": "copy_without_matching_source",
                    }
                )
            copy_rows.append(
                {
                    "book": book,
                    "op_index": op_index,
                    "target_start": target_start,
                    "global_target_start": len(emitted) + target_start,
                    "length": length,
                    "legal_source_count_without_target_oracle": legal_source_count,
                    "matching_source_count_if_target_chunk_granted": len(matching_sources),
                    "matching_source_min": min(matching_sources),
                    "matching_source_max": max(matching_sources),
                    "legal_source_log2_choices": safe_log2(legal_source_count),
                    "target_oracle_matching_source_log2_choices": safe_log2(
                        len(matching_sources)
                    ),
                    "target_oracle_unique_source": len(matching_sources) == 1,
                }
            )
            local_emitted += chunk
        if local_emitted != target:
            raise RuntimeError({"book": book, "type": "book_roundtrip_failed"})
        emitted += target
    return copy_rows, literal_rows


def write_markdown(out: Path, data: dict[str, Any]) -> None:
    s = data["summary"]
    lines = [
        "# Skeleton Decoder Ambiguity Gate",
        "",
        f"Classification: `{data['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Grant the exact source-free operation skeleton and measure what a decoder",
        "still cannot emit without copy-source choices and literal payload.",
        "",
        "## Summary",
        "",
        f"- Books tested: `{s['book_count']}`.",
        f"- Skeleton operations/copies/literals: `{s['operation_count']}` / `{s['copy_count']}` / `{s['literal_run_count']}`.",
        f"- Copied/literal digits: `{s['copied_digits']}` / `{s['literal_digits']}`.",
        f"- Seed payload digits granted operationally: `{s['seed_payload_digits']}`.",
        f"- Legal source branching lower bound: `{s['legal_source_log2_total']:.3f}` bits.",
        f"- Literal payload branching: `{s['literal_payload_log2_total']:.3f}` bits.",
        f"- Combined decoder ambiguity lower bound after skeleton: `{s['combined_decoder_ambiguity_log2_lower_bound']:.3f}` bits.",
        f"- Equivalent lower-bound decimal choices: `10^{s['combined_decoder_ambiguity_log10_lower_bound']:.3f}`.",
        f"- Copy events with unique target-oracle source: `{s['target_oracle_unique_source_count']}/{s['copy_count']}`.",
        f"- Target-oracle source-choice residual: `{s['target_oracle_matching_source_log2_total']:.3f}` bits.",
        "",
        "## Source Candidate Counts",
        "",
        "| Metric | Legal source count | Target-oracle matching source count |",
        "| --- | ---: | ---: |",
        f"| Min | `{s['legal_source_count_stats']['min']}` | `{s['matching_source_count_stats']['min']}` |",
        f"| Median | `{s['legal_source_count_stats']['median']}` | `{s['matching_source_count_stats']['median']}` |",
        f"| Mean | `{s['legal_source_count_stats']['mean']:.3f}` | `{s['matching_source_count_stats']['mean']:.3f}` |",
        f"| Max | `{s['legal_source_count_stats']['max']}` | `{s['matching_source_count_stats']['max']}` |",
        "",
        "## Decision",
        "",
        f"- Promotes skeleton decoder generator: `{s['promotes_skeleton_decoder_generator']}`.",
        "- The exact skeleton is a stable atlas, but it is not enough for decoder-side generation.",
        "- Literal payload and copy-source choice remain external dependencies.",
        "- The target-oracle matching-source row is diagnostic only; using it as a rule would depend on the future target chunk.",
        "- Compression bound is unchanged.",
        "- Row0 remains exogenous and unchanged.",
        "- No plaintext, translation, semantic reading, or case reopening is introduced.",
    ]
    out.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    gate98 = load_json(GATE98)
    gate99 = load_json(GATE99)
    assert_boundary("full_source_exact_skeleton_invariance", gate98)
    assert_boundary("exact_skeleton_dependency_ledger", gate99)
    if gate98["classification"] != "source_free_skeleton_exactly_invariant":
        raise RuntimeError("gate98 did not prove skeleton invariance")
    if gate99["classification"] != "exact_skeleton_dependency_ledger_atlas_only":
        raise RuntimeError("gate99 did not keep skeleton as atlas-only")

    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    skeleton_by_book = reconstruct_skeleton()
    copy_rows, literal_rows = make_rows(books, skeleton_by_book)

    legal_counts = [int(row["legal_source_count_without_target_oracle"]) for row in copy_rows]
    matching_counts = [
        int(row["matching_source_count_if_target_chunk_granted"]) for row in copy_rows
    ]
    literal_digits = sum(int(row["payload_digits"]) for row in literal_rows)
    copied_digits = sum(int(row["length"]) for row in copy_rows)
    legal_source_log2_total = sum(
        float(row["legal_source_log2_choices"]) for row in copy_rows
    )
    literal_payload_log2_total = literal_digits * math.log2(10)
    target_oracle_matching_source_log2_total = sum(
        float(row["target_oracle_matching_source_log2_choices"]) for row in copy_rows
    )
    combined = legal_source_log2_total + literal_payload_log2_total
    seed_payload_digits = sum(len(books[index]) for index in SEED_BOOKS)

    summary = {
        "book_count": len([book for book in skeleton_by_book if book >= 10]),
        "seed_books": SEED_BOOKS,
        "seed_payload_digits": seed_payload_digits,
        "operation_count": sum(len(ops) for book, ops in skeleton_by_book.items() if book >= 10),
        "copy_count": len(copy_rows),
        "literal_run_count": len(literal_rows),
        "copied_digits": copied_digits,
        "literal_digits": literal_digits,
        "legal_source_count_stats": summarize_numeric(legal_counts),
        "matching_source_count_stats": summarize_numeric(matching_counts),
        "legal_source_log2_total": legal_source_log2_total,
        "literal_payload_log2_total": literal_payload_log2_total,
        "combined_decoder_ambiguity_log2_lower_bound": combined,
        "combined_decoder_ambiguity_log10_lower_bound": combined / math.log2(10),
        "target_oracle_unique_source_count": sum(
            1 for row in copy_rows if row["target_oracle_unique_source"]
        ),
        "target_oracle_matching_source_log2_total": target_oracle_matching_source_log2_total,
        "promotes_skeleton_decoder_generator": False,
        "interpretation": (
            "Even when the exact source-free skeleton is granted, a decoder "
            "still needs literal payload and copy-source information. Legal "
            "source branching measures decoder ambiguity without a target oracle; "
            "matching-source counts are diagnostic only because they grant the "
            "future target chunk."
        ),
    }
    data = {
        "schema": "skeleton_decoder_ambiguity_gate.v1",
        "classification": "skeleton_decoder_ambiguity_blocks_generator",
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "source_free_skeleton_script": rel(SKELETON_SCRIPT),
            "gate98_full_source_exact_skeleton_invariance": rel(GATE98),
            "gate99_exact_skeleton_dependency_ledger": rel(GATE99),
        },
        "scope": {
            "analysis_only": True,
            "compression_bound_changed": False,
            "new_formula_emitted": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
            "target_oracle_matching_sources_are_diagnostic_only": True,
        },
        "summary": summary,
        "copy_rows": copy_rows,
        "literal_rows": literal_rows,
        "decision": {
            "skeleton_status": "stable_source_free_atlas_not_decoder_generator",
            "source_dependency_status": "retained_declared_dependency",
            "literal_payload_status": "retained_declared_dependency",
            "compression_bound_status": "unchanged_8154_676268",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_out = TEST_RESULTS / f"{OUT_STEM}.json"
    md_out = TEST_RESULTS / f"{OUT_STEM}.md"
    json_out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(md_out, data)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
