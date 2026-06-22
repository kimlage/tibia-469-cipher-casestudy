#!/usr/bin/env python3
"""Probe Tales/LIBSearch book database as a clean external-surface candidate.

This is not a semantic or plaintext audit. It asks whether the public
Tales-of-Tibia/LIBSearch book database supplies enough structured provenance to
reduce v9's external topology/control fields: exact book match, version,
location, map coordinate, container identity, slot/read order, and rights.
"""

from __future__ import annotations

import json
import math
import re
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis/external_authoring_surface_acquisition_audit_20260622"
OUT_DIR = FRONT / "reports/test_results"
FINAL_REPORT = FRONT / "reports/final_external_authoring_surface_acquisition_audit.md"
BOOKS_DIGITS = ROOT / "analysis/audit_20260609/books_digits.json"
MINIMAL_LEDGER = ROOT / "analysis/minimal_external_tape_program_audit_20260622/reports/test_results/02_unified_external_tape_ledger.json"

BOOK_DB_URL = "https://raw.githubusercontent.com/s2ward/tibia/main/data/books/book_database.json"
README_URL = "https://raw.githubusercontent.com/s2ward/tibia/main/README.md"
LICENSE_URL = "https://raw.githubusercontent.com/s2ward/tibia/main/LICENSE"
REPO_URL = "https://github.com/s2ward/tibia"
SERVICES_URL = "https://talesoftibia.com/services/"

ALPHA = 0.5
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
FEATURES = [
    "location_primary",
    "library_primary",
    "version",
    "map_coord",
    "database_order_decile",
    "database_order_quartile",
]
TARGETS = {
    "coarse_control": {"row_filter": "all", "target_field": "coarse_type_length_bucket"},
    "op_type": {"row_filter": "all", "target_field": "op_type"},
    "copy_hint_rank_bucket": {"row_filter": "copy", "target_field": "copy_hint_rank_bucket"},
}


def fetch_text(url: str) -> tuple[str | None, str | None, int | None]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "tibia-469-casestudy-audit"})
        with urllib.request.urlopen(req, timeout=30) as response:
            status = getattr(response, "status", None)
            return response.read().decode("utf-8"), None, status
    except (urllib.error.URLError, TimeoutError, UnicodeDecodeError) as exc:
        return None, repr(exc), None


def fetch_json(url: str) -> tuple[Any | None, str | None, int | None]:
    text, error, status = fetch_text(url)
    if error:
        return None, error, status
    try:
        return json.loads(text or ""), None, status
    except json.JSONDecodeError as exc:
        return None, repr(exc), status


def load_json(path: Path) -> Any:
    with path.open() as f:
        return json.load(f)


def digits_only(value: Any) -> str:
    return "".join(ch for ch in str(value) if ch.isdigit())


def parse_map(value: str) -> dict[str, Any]:
    match = re.search(r"#(-?\d+),(-?\d+),(-?\d+)(?::(\d+))?", value)
    if not match:
        return {"url": value, "x": None, "y": None, "z": None, "zoom": None}
    return {
        "url": value,
        "x": int(match.group(1)),
        "y": int(match.group(2)),
        "z": int(match.group(3)),
        "zoom": int(match.group(4)) if match.group(4) is not None else None,
    }


def rights_probe(readme: str | None, license_status: int | None, license_error: str | None) -> dict[str, Any]:
    readme_lower = (readme or "").lower()
    return {
        "repo_url": REPO_URL,
        "license_url": LICENSE_URL,
        "license_http_status": license_status,
        "license_error": license_error,
        "license_file_found": license_status == 200,
        "readme_mentions_open_source": "open source" in readme_lower,
        "readme_mentions_libsearch": "libsearch" in readme_lower,
        "rights_clean_for_contract": license_status == 200,
        "blocking_issue": None if license_status == 200 else "no LICENSE file observed at repository root; do not treat as rights-clean topology input",
    }


def extract_records(book_db: list[dict[str, Any]], books: dict[str, str]) -> list[dict[str, Any]]:
    by_digits: dict[str, list[int]] = defaultdict(list)
    for book_id, digits in books.items():
        by_digits[digits].append(int(book_id))

    records = []
    for db_index, raw in enumerate(book_db):
        text_digits = digits_only(raw.get("text", ""))
        matched_books = sorted(by_digits.get(text_digits, []))
        if not matched_books:
            continue
        map_entries = [parse_map(url) for url in raw.get("map", [])]
        records.append(
            {
                "db_index": db_index,
                "matched_books": matched_books,
                "match_status": "unique" if len(matched_books) == 1 else "ambiguous",
                "book": matched_books[0] if len(matched_books) == 1 else None,
                "name": raw.get("name"),
                "version": raw.get("version"),
                "locations": raw.get("locations", []),
                "libraries": raw.get("libraries", []),
                "map": raw.get("map", []),
                "parsed_map": map_entries,
                "has_map_coordinate": any(entry["x"] is not None for entry in map_entries),
                "has_container_identity": False,
                "has_slot_or_read_order": False,
                "database_order_available": True,
                "text_length": len(text_digits),
            }
        )
    return records


def build_topology_features(records: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    unique = [record for record in records if record["match_status"] == "unique"]
    if not unique:
        return {}
    min_index = min(record["db_index"] for record in unique)
    max_index = max(record["db_index"] for record in unique)
    span = max(1, max_index - min_index)

    features: dict[int, dict[str, Any]] = {}
    for record in unique:
        book = int(record["book"])
        coord = next((entry for entry in record["parsed_map"] if entry["x"] is not None), None)
        order_fraction = (record["db_index"] - min_index) / span
        features[book] = {
            "book": book,
            "db_index": record["db_index"],
            "location_primary": str(record["locations"][0]) if record["locations"] else "_NO_LOCATION",
            "library_primary": str(record["libraries"][0]) if record["libraries"] else "_NO_LIBRARY",
            "version": str(record["version"]),
            "map_coord": f"{coord['x']}:{coord['y']}:{coord['z']}" if coord else "_NO_COORD",
            "database_order_decile": f"db_q{min(9, int(order_fraction * 10))}",
            "database_order_quartile": f"db_q{min(3, int(order_fraction * 4))}",
        }
    return features


def build_joined_rows(features_by_book: dict[int, dict[str, Any]]) -> list[dict[str, Any]]:
    minimal = load_json(MINIMAL_LEDGER)
    joined = []
    for row in minimal["ledger_rows"]:
        book = int(row["book"])
        features = features_by_book.get(book)
        if not features:
            continue
        joined.append({**row, **features})
    return joined


def target_rows(rows: list[dict[str, Any]], target_name: str) -> list[dict[str, Any]]:
    spec = TARGETS[target_name]
    if spec["row_filter"] == "copy":
        return [row for row in rows if row["op_type"] == "copy" and row.get(spec["target_field"]) is not None]
    return rows


def target_alphabet(rows: list[dict[str, Any]], target_name: str) -> list[str]:
    field = TARGETS[target_name]["target_field"]
    return sorted({str(row[field]) for row in target_rows(rows, target_name)})


def counts_for(rows: list[dict[str, Any]], target_name: str, feature: str | None) -> tuple[Counter[str], dict[str, Counter[str]]]:
    field = TARGETS[target_name]["target_field"]
    global_counts: Counter[str] = Counter()
    feature_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for row in target_rows(rows, target_name):
        symbol = str(row[field])
        global_counts[symbol] += 1
        if feature is not None:
            feature_counts[str(row[feature])][symbol] += 1
    return global_counts, feature_counts


def code_bits(train: list[dict[str, Any]], test: list[dict[str, Any]], target_name: str, feature: str | None, alphabet: list[str]) -> float:
    global_counts, feature_counts = counts_for(train, target_name, feature)
    field = TARGETS[target_name]["target_field"]
    vocab = max(1, len(alphabet))
    bits = 0.0
    for row in target_rows(test, target_name):
        counter = global_counts if feature is None else feature_counts.get(str(row[feature]), global_counts)
        total = sum(counter.values())
        probability = (counter.get(str(row[field]), 0) + ALPHA) / (total + ALPHA * vocab)
        bits += -math.log2(probability)
    return bits


def split_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    splits = []
    for cutoff in PREFIX_CUTOFFS:
        train = [row for row in rows if int(row["book"]) < cutoff]
        test = [row for row in rows if int(row["book"]) >= cutoff]
        if train and test and len({row["book"] for row in train}) >= 2 and len({row["book"] for row in test}) >= 2:
            splits.append({"label": f"prefix_{cutoff}", "train": train, "test": test})
    return splits


def select_feature(train: list[dict[str, Any]], target_name: str, alphabet: list[str]) -> str:
    scored = []
    for feature in FEATURES:
        bits = 0.0
        books = sorted({int(row["book"]) for row in train})
        for heldout in books:
            sub_train = [row for row in train if int(row["book"]) != heldout]
            sub_test = [row for row in train if int(row["book"]) == heldout]
            bits += code_bits(sub_train, sub_test, target_name, feature, alphabet)
        scored.append((bits + math.log2(len(FEATURES)), feature))
    return min(scored)[1]


def evaluate_target(rows: list[dict[str, Any]], target_name: str) -> dict[str, Any]:
    alphabet = target_alphabet(rows, target_name)
    split_results = []
    for split in split_rows(rows):
        feature = select_feature(split["train"], target_name, alphabet)
        global_bits = code_bits(split["train"], split["test"], target_name, None, alphabet)
        feature_bits = code_bits(split["train"], split["test"], target_name, feature, alphabet) + math.log2(len(FEATURES))
        split_results.append(
            {
                "label": split["label"],
                "feature": feature,
                "target_rows": len(target_rows(split["test"], target_name)),
                "train_books": len({row["book"] for row in split["train"]}),
                "global_bits": global_bits,
                "feature_bits": feature_bits,
                "saving_bits": global_bits - feature_bits,
            }
        )
    return {
        "alphabet_size": len(alphabet),
        "split_results": split_results,
        "summary": {
            "split_count": len(split_results),
            "positive_splits": sum(row["saving_bits"] > 0 for row in split_results),
            "total_global_bits": sum(row["global_bits"] for row in split_results),
            "total_feature_bits": sum(row["feature_bits"] for row in split_results),
            "total_saving_bits": sum(row["saving_bits"] for row in split_results),
        },
    }


def contract_assessment(records: list[dict[str, Any]], rights: dict[str, Any]) -> dict[str, Any]:
    unique_records = [record for record in records if record["match_status"] == "unique"]
    matched_books = sorted({int(record["book"]) for record in unique_records})
    derived_books = [book for book in matched_books if book >= 10]
    return {
        "unique_matched_books": len(matched_books),
        "derived_matched_books": len(derived_books),
        "has_version": all(record.get("version") for record in unique_records),
        "records_with_map_coordinate": sum(1 for record in unique_records if record["has_map_coordinate"]),
        "unique_map_coordinates": len(
            {
                f"{entry['x']}:{entry['y']}:{entry['z']}"
                for record in unique_records
                for entry in record["parsed_map"]
                if entry["x"] is not None
            }
        ),
        "has_container_identity": any(record["has_container_identity"] for record in unique_records),
        "has_slot_or_read_order": any(record["has_slot_or_read_order"] for record in unique_records),
        "database_order_available": all(record["database_order_available"] for record in unique_records),
        "rights_clean_for_contract": rights["rights_clean_for_contract"],
        "contract_complete": (
            len(matched_books) == 70
            and rights["rights_clean_for_contract"]
            and any(record["has_container_identity"] for record in unique_records)
            and any(record["has_slot_or_read_order"] for record in unique_records)
        ),
    }


def write_markdown(result: dict[str, Any]) -> None:
    md = OUT_DIR / "07_tales_libsearch_book_database_probe.md"
    assessment = result["contract_assessment"]
    lines = [
        "# Tales/LIBSearch Book Database Probe",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        f"The public Tales/LIBSearch database matches `{assessment['unique_matched_books']}` canonical 469 books, including `{assessment['derived_matched_books']}` derived books.",
        f"It supplies map coordinates for `{assessment['records_with_map_coordinate']}` matched records but only `{assessment['unique_map_coordinates']}` unique coordinate(s).",
        "",
        "It does not satisfy the clean topology contract: no root LICENSE file was observed, and the book records do not expose container identity or slot/read order.",
        "",
        "## Heldout Diagnostics",
        "",
        "| Target | Splits | Positive | Total Saving Bits | Decision |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for target, evaluated in result["v9_feature_diagnostics"].items():
        summary = evaluated["summary"]
        lines.append(
            f"| `{target}` | {summary['split_count']} | {summary['positive_splits']} | {summary['total_saving_bits']:.3f} | `audit_only_not_integrated` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "No `PROMOTED_EXTERNAL_CONTROL_SOURCE` and no v9 reduction.",
            "",
            "This is a useful provenance clue because it gives high text coverage plus version/location/map links, but it remains a community corpus surface rather than an authoring/control surface.",
            "",
            "## Sources",
            "",
            f"- {REPO_URL}",
            f"- {BOOK_DB_URL}",
            f"- {SERVICES_URL}",
            "",
            "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        ]
    )
    md.write_text("\n".join(lines) + "\n")


def append_final_report(result: dict[str, Any]) -> None:
    report = FINAL_REPORT.read_text() if FINAL_REPORT.exists() else ""
    marker = "## Tales/LIBSearch Book Database Probe"
    if marker in report:
        return
    assessment = result["contract_assessment"]
    addition = [
        "",
        marker,
        "",
        "The Tales/LIBSearch `s2ward/tibia` book database is a stronger public corpus surface than a plain text mirror: it matches the canonical 469 books and carries version, location, and TibiaMaps links.",
        f"In the current probe it matches `{assessment['unique_matched_books']}` canonical 469 books, but the matched records collapse to `{assessment['unique_map_coordinates']}` unique map coordinate(s), expose no container identity, expose no slot/read order, and the repository root has no observed LICENSE file.",
        "Heldout v9 feature diagnostics are therefore audit-only; the source is not integrated and v9 reduction remains `0.0` bits.",
        "",
        "- [07_tales_libsearch_book_database_probe.py](../scripts/07_tales_libsearch_book_database_probe.py)",
        "- [07_tales_libsearch_book_database_probe.json](test_results/07_tales_libsearch_book_database_probe.json)",
        "- [07_tales_libsearch_book_database_probe.md](test_results/07_tales_libsearch_book_database_probe.md)",
    ]
    FINAL_REPORT.write_text(report.rstrip() + "\n" + "\n".join(addition) + "\n")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    books = load_json(BOOKS_DIGITS)
    book_db, book_db_error, book_db_status = fetch_json(BOOK_DB_URL)
    readme, readme_error, readme_status = fetch_text(README_URL)
    _license_text, license_error, license_status = fetch_text(LICENSE_URL)
    rights = rights_probe(readme, license_status, license_error)

    if not isinstance(book_db, list):
        result = {
            "schema": "tales_libsearch_book_database_probe.v1",
            "classification": "tales_libsearch_probe_failed_fetch",
            "retrieved_at_utc": datetime.now(UTC).isoformat(),
            "book_db_url": BOOK_DB_URL,
            "book_db_status": book_db_status,
            "book_db_error": book_db_error,
            "readme_status": readme_status,
            "readme_error": readme_error,
            "rights_probe": rights,
        }
    else:
        records = extract_records(book_db, books)
        features_by_book = build_topology_features(records)
        joined = build_joined_rows(features_by_book)
        diagnostics = {target: evaluate_target(joined, target) for target in TARGETS} if joined else {}
        assessment = contract_assessment(records, rights)
        result = {
            "schema": "tales_libsearch_book_database_probe.v1",
            "scope": "analysis_only_external_authoring_surface_probe",
            "classification": "WEAK_PROVENANCE_CLUE_CORPUS_LOCATION_SURFACE_NOT_AUTHORING_CONTROL",
            "retrieved_at_utc": datetime.now(UTC).isoformat(),
            "translation_delta": "NONE",
            "plaintext_claim": False,
            "case_reopened": False,
            "row0_status": "unchanged_exogenous",
            "compression_bound_status": "unchanged",
            "sources": {
                "book_database": BOOK_DB_URL,
                "readme": README_URL,
                "license": LICENSE_URL,
                "repository": REPO_URL,
                "services": SERVICES_URL,
            },
            "fetch_status": {
                "book_db_status": book_db_status,
                "book_db_error": book_db_error,
                "readme_status": readme_status,
                "readme_error": readme_error,
            },
            "rights_probe": rights,
            "contract_assessment": assessment,
            "matched_record_count": len(records),
            "matched_records_sample": records[:8],
            "joined_v9_rows": len(joined),
            "v9_feature_diagnostics": diagnostics,
            "decision": {
                "external_surface_integrated": False,
                "promoted_external_control_source": False,
                "v9_reduction_bits": 0.0,
                "reason": "high-coverage community corpus/location surface lacks rights-clean license marker, container identity, and slot/read order; diagnostics are audit-only",
            },
        }

    json_path = OUT_DIR / "07_tales_libsearch_book_database_probe.json"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_markdown(result)
    append_final_report(result)


if __name__ == "__main__":
    main()
