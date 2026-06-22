#!/usr/bin/env python3
"""Integration harness for rights-clean topology metadata against v9.

Given a clean topology CSV, this script matches rows to canonical 469 books,
checks coverage, and prepares controlled v9 stream tests. It is intentionally
strict: if coverage or schema is insufficient, it reports the blocker instead
of pretending that a public list or a one-row template can reduce v9.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis/external_authoring_surface_acquisition_audit_20260622"
OUT_DIR = FRONT / "reports/test_results"
DEFAULT_INPUT = OUT_DIR / "04_clean_topology_contract_template.csv"
BOOKS_DIGITS = ROOT / "analysis/audit_20260609/books_digits.json"
MINIMAL_LEDGER = ROOT / "analysis/minimal_external_tape_program_audit_20260622/reports/test_results/02_unified_external_tape_ledger.json"
ONLINE_X64 = ROOT / "analysis/online_x64_coarse_control_program_audit_20260622/reports/test_results/01_online_x64_coarse_control_program_gate.json"
FINAL_REPORT = FRONT / "reports/final_external_authoring_surface_acquisition_audit.md"


REQUIRED_FIELDS = [
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
FORBIDDEN_RIGHTS_MARKERS = ["", "unknown", "leak", "leaked", "proprietary_leak"]
MIN_TOTAL_MATCHED_BOOKS = 20
MIN_DERIVED_MATCHED_BOOKS = 10


def load_json(path: Path) -> Any:
    with path.open() as f:
        return json.load(f)


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def validate_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if not rows:
        return [{"line": 1, "field": "*", "error": "no_rows"}]
    header = rows[0].keys()
    for field in REQUIRED_FIELDS:
        if field not in header:
            errors.append({"line": 1, "field": field, "error": "missing_required_column"})
    if errors:
        return errors
    for index, row in enumerate(rows, start=2):
        for field in REQUIRED_FIELDS:
            if not str(row.get(field, "")).strip():
                errors.append({"line": index, "field": field, "error": "blank_required_field"})
        rights = str(row.get("source_rights", "")).strip().lower()
        if rights in FORBIDDEN_RIGHTS_MARKERS or "leak" in rights:
            errors.append({"line": index, "field": "source_rights", "error": "unacceptable_rights_marker"})
        for coord in ["x", "y", "z"]:
            try:
                int(str(row.get(coord, "")).strip())
            except ValueError:
                errors.append({"line": index, "field": coord, "error": "coordinate_not_integer"})
        try:
            int(str(row.get("slot_or_read_order", "")).strip())
        except ValueError:
            errors.append({"line": index, "field": "slot_or_read_order", "error": "slot_not_integer"})
    return errors


def match_books(rows: list[dict[str, str]], books: dict[str, str]) -> list[dict[str, Any]]:
    matches = []
    for index, row in enumerate(rows, start=2):
        prefix = "".join(ch for ch in row.get("book_text_or_exact_prefix", "") if ch.isdigit())
        matched = [
            int(book)
            for book, digits in books.items()
            if prefix and (digits == prefix or digits.startswith(prefix))
        ]
        matches.append(
            {
                "line": index,
                "prefix": prefix,
                "matched_books": sorted(matched),
                "match_status": "unique" if len(matched) == 1 else "ambiguous" if matched else "unmatched",
                "row": row,
            }
        )
    return matches


def build_topology_by_book(matches: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    topology: dict[int, dict[str, Any]] = {}
    for match in matches:
        if match["match_status"] != "unique":
            continue
        row = match["row"]
        book = match["matched_books"][0]
        topology[book] = {
            "book": book,
            "x": int(row["x"]),
            "y": int(row["y"]),
            "z": int(row["z"]),
            "container": row["container_or_bookcase_id"],
            "slot": int(row["slot_or_read_order"]),
            "source_id": row["source_id"],
            "capture_method": row["capture_method"],
        }
    return topology


def entropy_bits(counts: Counter[str]) -> float:
    total = sum(counts.values())
    if total == 0:
        return 0.0
    return -sum(n * math.log2(n / total) for n in counts.values() if n)


def categorical_feature_score(rows: list[dict[str, Any]], feature: str, target: str) -> dict[str, Any]:
    """Small train/test-safe codec scaffold.

    Current runs generally stop before this because clean topology coverage is
    absent. When coverage exists, this gives a conservative in-sample diagnostic
    with a model-cost placeholder; later gates should add prefix/family holdout.
    """

    usable = [r for r in rows if r.get(feature) is not None and r.get(target) is not None]
    global_counts = Counter(str(r[target]) for r in usable)
    global_bits = entropy_bits(global_counts)
    grouped: dict[str, Counter[str]] = defaultdict(Counter)
    for row in usable:
        grouped[str(row[feature])][str(row[target])] += 1
    feature_bits = sum(entropy_bits(counter) for counter in grouped.values())
    model_cost = math.log2(max(1, len(grouped) + 1))
    return {
        "usable_rows": len(usable),
        "feature": feature,
        "target": target,
        "global_bits": global_bits,
        "feature_bits_before_model": feature_bits,
        "model_cost_placeholder_bits": model_cost,
        "saving_after_placeholder": global_bits - feature_bits - model_cost,
        "promotable": False,
        "promotion_blocker": "diagnostic_only_requires_prefix_or_family_holdout",
    }


def build_joined_rows(topology_by_book: dict[int, dict[str, Any]]) -> list[dict[str, Any]]:
    minimal = load_json(MINIMAL_LEDGER)
    joined = []
    for row in minimal["ledger_rows"]:
        book = int(row["book"])
        topo = topology_by_book.get(book)
        if topo is None:
            continue
        joined.append(
            {
                "book": book,
                "op_index": row["op_index"],
                "coarse_control": row["coarse_type_length_bucket"],
                "op_type": row["op_type"],
                "copy_hint_rank_bucket": row.get("copy_hint_rank_bucket"),
                "container": topo["container"],
                "slot": topo["slot"],
                "coord_bucket": f"{topo['x']//10}:{topo['y']//10}:{topo['z']}",
            }
        )
    return joined


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(DEFAULT_INPUT), help="Clean topology CSV path")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = ROOT / input_path

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    books = load_json(BOOKS_DIGITS)
    rows = load_csv(input_path)
    validation_errors = validate_rows(rows)
    matches = [] if validation_errors else match_books(rows, books)
    topology_by_book = build_topology_by_book(matches)
    matched_books = sorted(topology_by_book)
    derived_matched_books = [book for book in matched_books if book >= 10]

    coverage_ok = (
        len(matched_books) >= MIN_TOTAL_MATCHED_BOOKS
        and len(derived_matched_books) >= MIN_DERIVED_MATCHED_BOOKS
    )
    joined_rows = build_joined_rows(topology_by_book) if coverage_ok else []

    diagnostics = []
    if joined_rows:
        for feature in ["container", "slot", "coord_bucket"]:
            for target in ["coarse_control", "op_type", "copy_hint_rank_bucket"]:
                diagnostics.append(categorical_feature_score(joined_rows, feature, target))

    result: dict[str, Any] = {
        "schema": "clean_topology_v9_integration_harness.v1",
        "scope": "analysis_only_clean_topology_v9_integration_harness",
        "classification": "clean_topology_v9_harness_ready_no_current_source_integrated",
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "translation_delta": "NONE",
        "plaintext_claim": False,
        "case_reopened": False,
        "row0_status": "unchanged_exogenous",
        "compression_bound_status": "unchanged",
        "input_csv": str(input_path.relative_to(ROOT)),
        "minimum_coverage": {
            "total_matched_books": MIN_TOTAL_MATCHED_BOOKS,
            "derived_matched_books": MIN_DERIVED_MATCHED_BOOKS,
        },
        "validation_errors": validation_errors,
        "match_summary": {
            "input_rows": len(rows),
            "unique_matches": sum(1 for match in matches if match["match_status"] == "unique"),
            "ambiguous_matches": sum(1 for match in matches if match["match_status"] == "ambiguous"),
            "unmatched": sum(1 for match in matches if match["match_status"] == "unmatched"),
            "matched_books": matched_books,
            "derived_matched_books": derived_matched_books,
        },
        "coverage_ok": coverage_ok,
        "joined_v9_rows": len(joined_rows),
        "diagnostics": diagnostics,
        "decision": {
            "external_surface_integrated": False,
            "v9_reduction_bits": 0.0,
            "reason": "coverage_insufficient" if not coverage_ok else "diagnostic_only_no_promoted_holdout",
            "next_step": "provide a rights-clean CSV with enough uniquely matched books to run v9 topology controls",
        },
    }

    json_path = OUT_DIR / "05_clean_topology_v9_integration_harness.json"
    md_path = OUT_DIR / "05_clean_topology_v9_integration_harness.md"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    lines: list[str] = []
    lines.append("# Clean Topology v9 Integration Harness")
    lines.append("")
    lines.append("Classification: `clean_topology_v9_harness_ready_no_current_source_integrated`")
    lines.append("Translation delta: `NONE`")
    lines.append("Plaintext claim: `False`")
    lines.append("Case reopened: `False`")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(
        "The harness can now match a rights-clean topology CSV to canonical 469 books and join it to v9 operation streams."
    )
    lines.append("")
    lines.append(
        f"Current input `{result['input_csv']}` has `{result['match_summary']['unique_matches']}` unique match(es), "
        f"`{len(derived_matched_books)}` derived-book match(es), and `{joined_rows and len(joined_rows) or 0}` joined v9 rows."
    )
    lines.append("")
    lines.append(
        f"Coverage threshold is `{MIN_TOTAL_MATCHED_BOOKS}` total books and `{MIN_DERIVED_MATCHED_BOOKS}` derived books, so this run does not integrate a source into v9."
    )
    lines.append("")
    lines.append("## Decision")
    lines.append("")
    lines.append("No external topology source is integrated. Net v9 reduction: `0.0` bits.")
    lines.append("")
    lines.append("A future rights-clean CSV can be passed to this harness with `--input` and then tested against v9 streams.")
    lines.append("")
    lines.append("`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.")
    md_path.write_text("\n".join(lines) + "\n")

    report = FINAL_REPORT.read_text() if FINAL_REPORT.exists() else ""
    marker = "## Clean Topology v9 Integration Harness"
    if marker not in report:
        addition = [
            "",
            marker,
            "",
            "A v9 integration harness now matches rights-clean topology CSV rows to canonical books and prepares topology feature tests against v9 operation streams.",
            f"The current template input has `{result['match_summary']['unique_matches']}` unique match and does not meet coverage thresholds, so no source is integrated.",
            "No v9 reduction is claimed.",
            "",
            "- [05_clean_topology_v9_integration_harness.py](../scripts/05_clean_topology_v9_integration_harness.py)",
            "- [05_clean_topology_v9_integration_harness.json](test_results/05_clean_topology_v9_integration_harness.json)",
            "- [05_clean_topology_v9_integration_harness.md](test_results/05_clean_topology_v9_integration_harness.md)",
        ]
        FINAL_REPORT.write_text(report.rstrip() + "\n" + "\n".join(addition) + "\n")


if __name__ == "__main__":
    main()
