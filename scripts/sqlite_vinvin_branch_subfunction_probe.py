#!/usr/bin/env python3
"""Score VINVIN/VTLR suffix branches as subfunctions, without gloss."""

from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "bonelord_operational.sqlite"
PROMOTABLE = {"INEIIVNSENI_STAR_LEAENT", "TIFAVONAFIEI"}
PARTIAL_OR_AUDIT = {"INEIIVNSENI", "TIFA", "OTHER_SUFFIX"}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def jdump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS vinvin_branch_subfunction_probe_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_vinvin_suffix_run_id INTEGER NOT NULL,
            branch_count INTEGER NOT NULL,
            promotable_branch_count INTEGER NOT NULL,
            audit_branch_count INTEGER NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS vinvin_branch_subfunction_items (
            run_id INTEGER NOT NULL,
            suffix_class TEXT NOT NULL,
            occurrence_count INTEGER NOT NULL,
            book_count INTEGER NOT NULL,
            contig_supported_count INTEGER NOT NULL,
            o23_relation_count INTEGER NOT NULL,
            partial_or_negative_count INTEGER NOT NULL,
            branch_score REAL NOT NULL,
            branch_status TEXT NOT NULL,
            next_action TEXT NOT NULL,
            books_json TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, suffix_class)
        );
        """
    )


def latest_id(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT run_id FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    if row is None:
        raise SystemExit(f"missing required table data: {table}")
    return int(row["run_id"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)

    source_run_id = latest_id(conn, "vinvin_suffix_contrast_probe_runs")
    rows = conn.execute(
        """
        SELECT *
        FROM vinvin_suffix_contrast_items
        WHERE run_id=?
        ORDER BY suffix_class, CAST(bookid AS INTEGER), start_pos
        """,
        (source_run_id,),
    ).fetchall()

    by_suffix: dict[str, list[sqlite3.Row]] = defaultdict(list)
    for row in rows:
        by_suffix[row["suffix_class"]].append(row)

    cur = conn.execute(
        """
        INSERT INTO vinvin_branch_subfunction_probe_runs
            (created_at, source_vinvin_suffix_run_id, branch_count,
             promotable_branch_count, audit_branch_count, decision, payload_json)
        VALUES (?, ?, ?, 0, 0, ?, ?)
        """,
        (utc_now(), source_run_id, len(by_suffix), "PENDING", "{}"),
    )
    run_id = int(cur.lastrowid)

    promotable_count = 0
    audit_count = 0
    branch_summaries: list[dict[str, Any]] = []
    for suffix, items in sorted(by_suffix.items()):
        books = sorted({str(row["bookid"]) for row in items}, key=lambda value: int(value) if value.isdigit() else value)
        contig_supported = sum(1 for row in items if row["contig_support_class"] == "primary_contig_edge_supported")
        o23_relation = sum(1 for row in items if row["relation_to_o23"] == "contains_o23_onaf_suffix")
        partial_negative = 0
        if suffix in {"TIFA", "INEIIVNSENI", "OTHER_SUFFIX"}:
            partial_negative = len(items)
        score = 0.0
        score += min(0.25, len(items) * 0.08)
        score += min(0.25, len(books) * 0.08)
        score += 0.25 if contig_supported else 0.0
        score += 0.15 if suffix == "TIFAVONAFIEI" and o23_relation else 0.0
        score += 0.10 if suffix == "INEIIVNSENI_STAR_LEAENT" else 0.0
        score -= min(0.30, partial_negative * 0.10)
        if suffix in PROMOTABLE and score >= 0.65:
            status = "SUBFUNCTION_READY"
            next_action = "track_as_vinvin_branch_subfunction_no_gloss"
            promotable_count += 1
        elif suffix in PARTIAL_OR_AUDIT:
            status = "AUDIT_OR_PARTIAL_BRANCH"
            next_action = "keep_as_negative_or_partial_control"
            audit_count += 1
        else:
            status = "CONTEXT_BRANCH"
            next_action = "keep_as_context_branch"
        summary = {
            "suffix_class": suffix,
            "occurrence_count": len(items),
            "book_count": len(books),
            "contig_supported_count": contig_supported,
            "o23_relation_count": o23_relation,
            "partial_or_negative_count": partial_negative,
            "branch_score": round(score, 4),
            "branch_status": status,
            "books": books,
        }
        branch_summaries.append(summary)
        conn.execute(
            """
            INSERT INTO vinvin_branch_subfunction_items
                (run_id, suffix_class, occurrence_count, book_count,
                 contig_supported_count, o23_relation_count,
                 partial_or_negative_count, branch_score, branch_status,
                 next_action, books_json, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                suffix,
                len(items),
                len(books),
                contig_supported,
                o23_relation,
                partial_negative,
                score,
                status,
                next_action,
                jdump(books),
                jdump(summary),
            ),
        )

    decision = "VINVIN_BRANCH_SUBFUNCTIONS_READY" if promotable_count >= 2 else "VINVIN_BRANCH_SUBFUNCTIONS_PARTIAL"
    conn.execute(
        """
        UPDATE vinvin_branch_subfunction_probe_runs
        SET promotable_branch_count=?,
            audit_branch_count=?,
            decision=?,
            payload_json=?
        WHERE run_id=?
        """,
        (promotable_count, audit_count, decision, jdump({"branches": branch_summaries, "gloss_allowed": False}), run_id),
    )
    conn.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "branch_count": len(by_suffix),
                "promotable_branch_count": promotable_count,
                "audit_branch_count": audit_count,
                "branches": branch_summaries,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
