#!/usr/bin/env python3
"""Classify SQLite tables/columns for no-gloss functional row0 use."""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "bonelord_operational.sqlite"

ALLOW_TABLES = {
    "row0_variant_book_tokens",
    "row0_base_book_items",
    "row0_code_symbol_probe_books",
    "row0_code_symbol_counts",
    "row0_symbol_code_counts",
    "row0_variant_token_counts",
    "row0_variant_ngram_items",
    "row0_function_registry",
    "row0_function_evidence",
    "row0_function_policy_items",
    "contig_max_overlap_items",
    "contig_max_overlap_edges",
}

MASK_ONLY_TABLES = {
    "semantic_blocked_phrases",
    "semantic_formula_families",
    "semantic_known_unresolved_slots",
    "semantic_constraint_registry",
}

MECHANICAL_SHEET_COLUMNS = {
    "bookid",
    "digits",
    "digitslen",
    "decodedbase",
    "basecontigid",
    "basecontig",
    "booksinorder",
    "length",
    "numbooks",
    "tokencount",
}

DANGEROUS_COLUMN_FRAGMENTS = (
    "translation",
    "readable",
    "semantic",
    "english",
    "gloss",
    "german",
    "spanish",
    "shadow",
    "replacement",
    "hypothesis",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def jdump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS functional_source_guard_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            table_count INTEGER NOT NULL,
            column_count INTEGER NOT NULL,
            allowed_column_count INTEGER NOT NULL,
            mask_only_column_count INTEGER NOT NULL,
            forbidden_column_count INTEGER NOT NULL,
            check_column_count INTEGER NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS functional_source_guard_items (
            run_id INTEGER NOT NULL,
            table_name TEXT NOT NULL,
            column_name TEXT NOT NULL,
            source_class TEXT NOT NULL,
            reason TEXT NOT NULL,
            allowed_for_functional_view INTEGER NOT NULL,
            allowed_for_masking_only INTEGER NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, table_name, column_name)
        );
        """
    )


def classify(table_name: str, column_name: str) -> tuple[str, str, bool, bool]:
    lower_table = table_name.lower()
    lower_col = column_name.lower()
    if table_name in ALLOW_TABLES:
        if any(fragment in lower_col for fragment in DANGEROUS_COLUMN_FRAGMENTS):
            return "CHECK_ALLOWED_TABLE_DANGEROUS_COLUMN", "allowlisted table but column name is semantically risky", False, True
        return "ALLOW_ROW0_FUNCTIONAL", "allowlisted mechanical/functional row0 source", True, False
    if table_name in MASK_ONLY_TABLES:
        return "ALLOW_MASK_ONLY", "semantic table allowed only for blocking/masking, never gloss", False, True
    if lower_table.startswith("sheet__"):
        if lower_col in MECHANICAL_SHEET_COLUMNS:
            return "ALLOW_IMPORTED_MECHANICAL_FIELD", "legacy import mechanical field only", True, False
        if any(fragment in lower_col for fragment in DANGEROUS_COLUMN_FRAGMENTS):
            return "FORBIDDEN_LEGACY_SEMANTIC_COLUMN", "legacy workbook semantic/translation/gloss column", False, False
        return "CHECK_LEGACY_IMPORT_COLUMN", "legacy import column not explicitly allowlisted", False, False
    if lower_table.startswith("german_"):
        return "FORBIDDEN_EXTERNAL_GERMAN", "external German/MHG candidate layer", False, False
    if lower_table.startswith("external_"):
        return "FORBIDDEN_EXTERNAL_CONTEXT", "external context/candidate layer cannot assign function", False, False
    if lower_table.startswith("canonical_candidate_"):
        return "FORBIDDEN_CANDIDATE_GLOSS", "candidate gloss layer", False, False
    if lower_table.startswith("translation_"):
        return "FORBIDDEN_TRANSLATION_AUDIT", "translation/audit layer", False, False
    if lower_table == "safe_book_translations":
        return "FORBIDDEN_SAFE_DISPLAY", "display-only translation layer", False, False
    if "shadow" in lower_table and "translation" in lower_table:
        return "FORBIDDEN_SHADOW_DISPLAY", "shadow/display translation layer", False, False
    if lower_table.startswith("semantic_"):
        return "FORBIDDEN_SEMANTIC_GENERATIVE", "semantic generative/hypothesis layer", False, False
    if any(fragment in lower_col for fragment in DANGEROUS_COLUMN_FRAGMENTS):
        return "FORBIDDEN_DANGEROUS_COLUMN", "column name suggests gloss/translation/semantic hypothesis", False, False
    return "CHECK_UNKNOWN_SOURCE", "not allowlisted for functional view", False, False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)

    tables = [
        row["name"]
        for row in conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type='table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        ).fetchall()
    ]
    rows: list[tuple[str, str, str, str, bool, bool]] = []
    for table in tables:
        for col in conn.execute(f"PRAGMA table_info({table})").fetchall():
            source_class, reason, allowed, mask_only = classify(table, col["name"])
            rows.append((table, col["name"], source_class, reason, allowed, mask_only))

    allowed_count = sum(1 for row in rows if row[4])
    mask_count = sum(1 for row in rows if row[5])
    forbidden_count = sum(1 for row in rows if row[2].startswith("FORBIDDEN"))
    check_count = sum(1 for row in rows if row[2].startswith("CHECK"))

    cur = conn.execute(
        """
        INSERT INTO functional_source_guard_runs
            (created_at, table_count, column_count, allowed_column_count,
             mask_only_column_count, forbidden_column_count, check_column_count,
             decision, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            utc_now(),
            len(tables),
            len(rows),
            allowed_count,
            mask_count,
            forbidden_count,
            check_count,
            "FUNCTIONAL_SOURCE_GUARD_READY",
            jdump({"policy": "allowlist_row0_no_gloss", "gloss_allowed": False}),
        ),
    )
    run_id = int(cur.lastrowid)
    for table, col, source_class, reason, allowed, mask_only in rows:
        conn.execute(
            """
            INSERT INTO functional_source_guard_items
                (run_id, table_name, column_name, source_class, reason,
                 allowed_for_functional_view, allowed_for_masking_only, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, table, col, source_class, reason, int(allowed), int(mask_only), "{}"),
        )
    conn.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": "FUNCTIONAL_SOURCE_GUARD_READY",
                "table_count": len(tables),
                "column_count": len(rows),
                "allowed_column_count": allowed_count,
                "mask_only_column_count": mask_count,
                "forbidden_column_count": forbidden_count,
                "check_column_count": check_count,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
