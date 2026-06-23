#!/usr/bin/env python3
"""Design minimal clean-surface capture batches for the v9 protocol.

This script does not integrate a source. It turns the current clean-topology
contract into an acquisition plan: which canonical books should be captured
first if a user/official/licensed object-layer surface becomes available.
"""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "primary_surface_acquisition_packet_20260623"
OUT_DIR = FRONT / "reports" / "test_results"
BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
MINIMAL_LEDGER = ROOT / "analysis" / "minimal_external_tape_program_audit_20260622" / "reports" / "test_results" / "02_unified_external_tape_ledger.json"

CSV_OUT = OUT_DIR / "03_minimal_capture_design.csv"
JSON_OUT = OUT_DIR / "03_minimal_capture_design.json"
MD_OUT = OUT_DIR / "03_minimal_capture_design.md"
FINAL_OUT = FRONT / "reports" / "final_primary_surface_acquisition_packet.md"

PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
MIN_TOTAL_MATCHED_BOOKS = 20
MIN_DERIVED_MATCHED_BOOKS = 10
MIN_SPLITS = 3
REQUIRED_CAPTURE_FIELDS = [
    "source_id",
    "source_rights",
    "source_version_or_date",
    "book_text_or_exact_prefix",
    "x",
    "y",
    "z",
    "container_or_bookcase_id",
    "slot_or_read_order",
    "capture_method",
]


def load_json(path: Path) -> Any:
    with path.open() as f:
        return json.load(f)


def book_stats() -> dict[int, dict[str, Any]]:
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    ledger = load_json(MINIMAL_LEDGER)["ledger_rows"]
    by_book: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in ledger:
        by_book[int(row["book"])].append(row)

    stats: dict[int, dict[str, Any]] = {}
    for book, digits in books.items():
        rows = by_book.get(book, [])
        op_counts = Counter(row["op_type"] for row in rows)
        coarse_counts = Counter(row["coarse_type_length_bucket"] for row in rows)
        stats[book] = {
            "book": book,
            "book_length": len(digits),
            "canonical_prefix_32": digits[:32],
            "is_seed": book < 10,
            "derived_op_count": len(rows),
            "copy_ops": op_counts.get("copy", 0),
            "literal_ops": op_counts.get("literal", 0),
            "coarse_symbol_count": len(coarse_counts),
            "v9_external_bits_in_book": round(sum(float(row["total_external_bits_charged_here"]) for row in rows), 6),
        }
    return stats


def derived_decade(book: int) -> int:
    return (book // 10) * 10


def possible_prefix_splits(books: list[int]) -> list[str]:
    derived_books = sorted(book for book in books if book >= 10)
    splits = []
    for cutoff in PREFIX_CUTOFFS:
        train = [book for book in derived_books if book < cutoff]
        test = [book for book in derived_books if book >= cutoff]
        if len(train) >= 2 and len(test) >= 2:
            splits.append(f"prefix_{cutoff}")
    return splits


def coverage_summary(label: str, books: list[int], stats: dict[int, dict[str, Any]]) -> dict[str, Any]:
    unique_books = sorted(set(books))
    derived_books = [book for book in unique_books if book >= 10]
    splits = possible_prefix_splits(unique_books)
    return {
        "batch": label,
        "book_count": len(unique_books),
        "derived_book_count": len(derived_books),
        "seed_book_count": len([book for book in unique_books if book < 10]),
        "projected_joined_v9_ops": sum(stats[book]["derived_op_count"] for book in derived_books),
        "projected_v9_external_bits_covered": round(sum(stats[book]["v9_external_bits_in_book"] for book in derived_books), 6),
        "possible_prefix_splits": splits,
        "meets_protocol_floor": (
            len(unique_books) >= MIN_TOTAL_MATCHED_BOOKS
            and len(derived_books) >= MIN_DERIVED_MATCHED_BOOKS
            and len(splits) >= MIN_SPLITS
        ),
    }


def design_batches(stats: dict[int, dict[str, Any]]) -> dict[str, Any]:
    seed_books = list(range(10))
    derived_books = [book for book in range(10, 70)]
    selected: set[int] = set(seed_books)

    balanced_derived: list[int] = []
    for decade in [10, 20, 30, 40, 50, 60]:
        candidates = [book for book in derived_books if derived_decade(book) == decade]
        candidates.sort(key=lambda book: (-stats[book]["v9_external_bits_in_book"], book))
        balanced_derived.extend(candidates[:2])
    selected.update(balanced_derived)

    remaining_by_signal = [book for book in derived_books if book not in selected]
    remaining_by_signal.sort(key=lambda book: (-stats[book]["v9_external_bits_in_book"], book))
    extension = remaining_by_signal[:8]
    selected_with_extension = sorted(selected | set(extension))

    all_remaining = [book for book in range(70) if book not in selected_with_extension]

    batches = {
        "balanced_v9_probe_22_books": sorted(seed_books + balanced_derived),
        "high_signal_extension_30_books": selected_with_extension,
        "full_followup_remaining_40_books": all_remaining,
    }
    summaries = {label: coverage_summary(label, books, stats) for label, books in batches.items()}
    return {"batches": batches, "summaries": summaries}


def write_csv(stats: dict[int, dict[str, Any]], batches: dict[str, list[int]]) -> None:
    priority: dict[int, tuple[str, int]] = {}
    for index, book in enumerate(batches["balanced_v9_probe_22_books"], start=1):
        priority[book] = ("balanced_v9_probe_22_books", index)
    extension_only = [book for book in batches["high_signal_extension_30_books"] if book not in priority]
    for index, book in enumerate(extension_only, start=1):
        priority[book] = ("high_signal_extension_30_books", index)
    for index, book in enumerate(batches["full_followup_remaining_40_books"], start=1):
        priority[book] = ("full_followup_remaining_40_books", index)

    fields = [
        "canonical_book",
        "capture_batch",
        "batch_order",
        "rationale",
        "book_length",
        "canonical_prefix_32",
        "derived_op_count",
        "copy_ops",
        "literal_ops",
        "coarse_symbol_count",
        "v9_external_bits_in_book",
    ] + REQUIRED_CAPTURE_FIELDS
    with CSV_OUT.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for book in range(70):
            batch, order = priority[book]
            rationale = (
                "seed payload/context capture"
                if book < 10
                else "balanced decade high-signal derived book"
                if batch == "balanced_v9_probe_22_books"
                else "high residual-signal extension"
                if batch == "high_signal_extension_30_books"
                else "full coverage follow-up"
            )
            row = {
                "canonical_book": book,
                "capture_batch": batch,
                "batch_order": order,
                "rationale": rationale,
                **stats[book],
            }
            for field in REQUIRED_CAPTURE_FIELDS:
                row[field] = "" if field != "book_text_or_exact_prefix" else stats[book]["canonical_prefix_32"]
            writer.writerow({field: row.get(field, "") for field in fields})


def write_markdown(data: dict[str, Any]) -> None:
    lines = [
        "# Minimal Capture Design",
        "",
        f"Classification: `{data['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        "This is an acquisition design for a future rights-clean object-layer capture.",
        "It does not integrate a source and does not change v9, row0, plaintext, translation, semantics, or compression_bound.",
        "",
        "The recommended first useful batch is `balanced_v9_probe_22_books`: all seed books `0..9` plus two high-signal derived books from each decade bucket `10s..60s`.",
        "That batch is designed to satisfy the current protocol floor while preserving prefix-holdout splits across the corpus.",
        "",
        "## Batch Coverage",
        "",
        "| Batch | Books | Derived | Joined v9 ops | Prefix splits | Meets floor |",
        "| --- | ---: | ---: | ---: | --- | --- |",
    ]
    for label, summary in data["batch_summaries"].items():
        split_text = ", ".join(summary["possible_prefix_splits"])
        lines.append(
            f"| `{label}` | {summary['book_count']} | {summary['derived_book_count']} | "
            f"{summary['projected_joined_v9_ops']} | {split_text} | `{summary['meets_protocol_floor']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "`minimal_capture_design_ready_no_source_integrated`.",
            "",
            "Progress still requires filling object/container/slot/order and rights fields from a clean primary or authorized source.",
            "The design only reduces acquisition ambiguity; it does not reduce the decoder ledger until real data is supplied and passes v9 holdout/permutation controls.",
            "",
            "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        ]
    )
    MD_OUT.write_text("\n".join(lines) + "\n")


def append_final() -> None:
    report = FINAL_OUT.read_text()
    marker = "## Minimal Capture Design"
    if marker in report:
        return
    addition = [
        "",
        marker,
        "",
        "A minimal capture design now prioritizes an incremental clean object-layer acquisition instead of requiring all 70 books up front.",
        "The first recommended batch is `balanced_v9_probe_22_books`: all seed books plus two high-signal derived books per decade bucket, giving `12` derived books and `5` possible prefix splits under the current protocol floor.",
        "This is an acquisition plan only: no source is integrated and v9 reduction remains `0.0` bits.",
        "",
        "- [03_minimal_capture_design.py](../scripts/03_minimal_capture_design.py)",
        "- [03_minimal_capture_design.csv](test_results/03_minimal_capture_design.csv)",
        "- [03_minimal_capture_design.json](test_results/03_minimal_capture_design.json)",
        "- [03_minimal_capture_design.md](test_results/03_minimal_capture_design.md)",
    ]
    FINAL_OUT.write_text(report.rstrip() + "\n" + "\n".join(addition) + "\n")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stats = book_stats()
    designed = design_batches(stats)
    write_csv(stats, designed["batches"])
    data = {
        "schema": "minimal_capture_design.v1",
        "scope": "analysis_only_primary_surface_acquisition_design",
        "classification": "minimal_capture_design_ready_no_source_integrated",
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "translation_delta": "NONE",
        "plaintext_claim": False,
        "case_reopened": False,
        "row0_status": "unchanged_exogenous",
        "compression_bound_status": "unchanged",
        "protocol_floor": {
            "min_total_matched_books": MIN_TOTAL_MATCHED_BOOKS,
            "min_derived_matched_books": MIN_DERIVED_MATCHED_BOOKS,
            "min_splits": MIN_SPLITS,
            "prefix_cutoffs": PREFIX_CUTOFFS,
        },
        "required_capture_fields": REQUIRED_CAPTURE_FIELDS,
        "batches": designed["batches"],
        "batch_summaries": designed["summaries"],
        "decision": {
            "external_surface_integrated": False,
            "v9_reduction_bits": 0.0,
            "next_step": "capture the balanced_v9_probe_22_books batch from a clean object-layer source, then run the v9 protocol",
        },
    }
    JSON_OUT.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    write_markdown(data)
    append_final()
    print(json.dumps(data["batch_summaries"]["balanced_v9_probe_22_books"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
