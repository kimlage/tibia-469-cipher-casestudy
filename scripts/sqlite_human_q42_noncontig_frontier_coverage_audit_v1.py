#!/usr/bin/env python3
"""Q42: audit coverage of the six Q37 non-contig frontiers."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

FRONTIER_TABLES = {
    "BOOK30_FAMILY_SPINE_PACKET": "human_q38_book30_family_noncontig_atlas_v1_runs",
    "VNCTIIN_TIINNEF_PHASE_TRIO": "human_q39_vnctiin_tiinnef_phase_trio_atlas_v1_runs",
    "C86_VINVIN_BRANCH_TRIO": "human_q40_c86_vinvin_branch_trio_atlas_v1_runs",
    "BTII_NSBVN_ATFNAAST_DISPLAY_TRIO": "human_q41_display_drift_trio_atlas_v1_runs",
}


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q42_noncontig_frontier_coverage_audit_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q37_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            q37_frontier_count INTEGER NOT NULL,
            atlas_ready_frontier_count INTEGER NOT NULL,
            pending_frontier_count INTEGER NOT NULL,
            q37_selected_book_count INTEGER NOT NULL,
            atlas_ready_book_count INTEGER NOT NULL,
            pending_book_count INTEGER NOT NULL,
            component_gloss_allowed_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q42_noncontig_frontier_coverage_audit_v1_items (
            run_id INTEGER NOT NULL,
            frontier_id TEXT NOT NULL,
            priority INTEGER NOT NULL,
            bookids_json TEXT NOT NULL,
            book_count INTEGER NOT NULL,
            coverage_status TEXT NOT NULL,
            atlas_table TEXT NOT NULL,
            next_action TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, frontier_id)
        );
        """
    )


def latest_row(conn: sqlite3.Connection, table: str) -> sqlite3.Row:
    row = conn.execute(f"SELECT * FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    if row is None:
        raise RuntimeError(f"missing required row: {table}")
    return row


def table_has_run(conn: sqlite3.Connection, table: str) -> bool:
    exists = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone()
    if not exists:
        return False
    row = conn.execute(f"SELECT max(run_id) FROM {table}").fetchone()
    return row is not None and row[0] is not None


def next_action(frontier_id: str, coverage_status: str) -> str:
    if coverage_status == "ATLAS_READY_NO_GLOSS":
        return "Keep as human-shadow atlas entry; use for book-level integration."
    if frontier_id == "NAESE_C68_SLOT_VARIANT_TRIO":
        return "Run NAESE/C68 slot variant atlas probe for books 22/28/48."
    if frontier_id == "CHAYENNE_REGISTER_FRAME_SET":
        return "Run Chayenne register-frame atlas probe for books 8/37/63/66 with strict external quarantine."
    return "Review frontier manually."


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q37 = latest_row(conn, "human_q37_noncontig_frontier_selection_v1_runs")
    audit = latest_row(conn, "human_translation_completion_audit_v5_runs")
    q37_run_id = int(q37["run_id"])
    frontiers = list(
        conn.execute(
            """
            SELECT *
            FROM human_q37_noncontig_frontier_selection_v1_items
            WHERE run_id=?
            ORDER BY priority
            """,
            (q37_run_id,),
        )
    )

    items = []
    atlas_ready_book_count = 0
    pending_book_count = 0
    for row in frontiers:
        frontier_id = str(row["frontier_id"])
        atlas_table = FRONTIER_TABLES.get(frontier_id, "")
        ready = bool(atlas_table and table_has_run(conn, atlas_table))
        coverage_status = "ATLAS_READY_NO_GLOSS" if ready else "PENDING_FRONTIER"
        book_count = int(row["book_count"])
        if ready:
            atlas_ready_book_count += book_count
        else:
            pending_book_count += book_count
        items.append(
            {
                "frontier_id": frontier_id,
                "priority": int(row["priority"]),
                "bookids": json.loads(str(row["bookids_json"])),
                "book_count": book_count,
                "coverage_status": coverage_status,
                "atlas_table": atlas_table,
                "next_action": next_action(frontier_id, coverage_status),
                "evidence": {"q37_item": dict(row), "atlas_table": atlas_table},
            }
        )

    atlas_ready_frontier_count = sum(1 for item in items if item["coverage_status"] == "ATLAS_READY_NO_GLOSS")
    pending_frontier_count = len(items) - atlas_ready_frontier_count
    component_gloss_allowed_count = 0
    canonical_promotion_allowed_count = 0
    decision = (
        "Q42_NONCONTIG_FRONTIER_COVERAGE_AUDIT_4_OF_6_READY_2_PENDING_NO_GLOSS"
        if len(items) == 6
        and atlas_ready_frontier_count == 4
        and pending_frontier_count == 2
        and atlas_ready_book_count == 13
        and pending_book_count == 7
        and int(audit["promoted_gloss_count"]) == 0
        and component_gloss_allowed_count == 0
        and canonical_promotion_allowed_count == 0
        else "Q42_NONCONTIG_FRONTIER_COVERAGE_AUDIT_REQUIRES_REVIEW"
    )
    payload = {
        "question": "How much of the Q37 non-contig frontier queue is now converted into atlas entries?",
        "answer": "Four of six frontier families are ready, covering 13 of 20 selected non-contig books.",
        "pending_frontiers": [
            item["frontier_id"] for item in items if item["coverage_status"] == "PENDING_FRONTIER"
        ],
        "blocked_use": "Coverage audit does not promote glosses or plaintext.",
        "next_action": "Run the NAESE/C68 slot variant trio next, then Chayenne register frame.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q42_noncontig_frontier_coverage_audit_v1_runs (
                created_at, decision, q37_run_id, completion_audit_run_id,
                q37_frontier_count, atlas_ready_frontier_count,
                pending_frontier_count, q37_selected_book_count,
                atlas_ready_book_count, pending_book_count,
                component_gloss_allowed_count, canonical_promotion_allowed_count,
                payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                q37_run_id,
                int(audit["run_id"]),
                len(items),
                atlas_ready_frontier_count,
                pending_frontier_count,
                int(q37["selected_book_count"]),
                atlas_ready_book_count,
                pending_book_count,
                component_gloss_allowed_count,
                canonical_promotion_allowed_count,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q42_noncontig_frontier_coverage_audit_v1_items (
                run_id, frontier_id, priority, bookids_json, book_count,
                coverage_status, atlas_table, next_action, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    str(item["frontier_id"]),
                    int(item["priority"]),
                    j(item["bookids"]),
                    int(item["book_count"]),
                    str(item["coverage_status"]),
                    str(item["atlas_table"]),
                    str(item["next_action"]),
                    j(item["evidence"]),
                )
                for item in items
            ],
        )

    print(
        j(
            {
                "run_id": run_id,
                "decision": decision,
                "q37_frontier_count": len(items),
                "atlas_ready_frontier_count": atlas_ready_frontier_count,
                "pending_frontier_count": pending_frontier_count,
                "atlas_ready_book_count": atlas_ready_book_count,
                "pending_book_count": pending_book_count,
                "component_gloss_allowed_count": component_gloss_allowed_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
            }
        )
    )


if __name__ == "__main__":
    main()
