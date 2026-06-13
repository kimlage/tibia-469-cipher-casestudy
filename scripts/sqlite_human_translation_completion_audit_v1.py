#!/usr/bin/env python3
"""Audit how far the human-translation shadow layer is from the objective."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_translation_completion_audit_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            total_book_count INTEGER NOT NULL,
            atlas_book_count INTEGER NOT NULL,
            atlas_coverage_pct REAL NOT NULL,
            promoted_gloss_count INTEGER NOT NULL,
            missing_book_count INTEGER NOT NULL,
            blocker_summary_json TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_translation_completion_audit_v1_missing_books (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            functional_tags_json TEXT NOT NULL,
            suggested_route TEXT NOT NULL,
            reason_missing TEXT NOT NULL,
            next_action TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        );
        """
    )


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    books = conn.execute(
        """
        SELECT bookid, functional_tags_json
        FROM final_honest_reading_v19_books
        WHERE run_id=(SELECT max(run_id) FROM final_honest_reading_v19_books)
        ORDER BY CAST(bookid AS INTEGER)
        """
    ).fetchall()
    atlas_run = conn.execute("SELECT max(run_id) AS run_id FROM human_translation_atlas_v2_items").fetchone()["run_id"]
    atlas = conn.execute(
        """
        SELECT target_id, promotion_status
        FROM human_translation_atlas_v2_items
        WHERE run_id=?
        """,
        (atlas_run,),
    ).fetchall()
    atlas_books = {str(row["target_id"]): str(row["promotion_status"]) for row in atlas}
    missing = [row for row in books if str(row["bookid"]) not in atlas_books]
    promoted = sum(1 for status in atlas_books.values() if status != "NOT_PROMOTED")
    coverage = round((len(atlas_books) / max(1, len(books))) * 100.0, 2)

    blocker_summary = {
        "not_complete_reasons": [
            "human shadow atlas covers only a subset of books",
            "no canonical book gloss has been promoted",
            "external exact phrase-to-meaning source remains absent",
        ],
        "current_strength": "11 anchored shadow readings with source bridges and probes",
    }
    decision = "HUMAN_TRANSLATION_OBJECTIVE_NOT_COMPLETE_EXPAND_ATLAS"
    payload = {
        "atlas_run_id": atlas_run,
        "covered_books": sorted(atlas_books, key=lambda value: int(value)),
        "principle": "completion requires human-readable coverage for all target texts plus stronger promotion gates",
    }
    cur = conn.execute(
        """
        INSERT INTO human_translation_completion_audit_v1_runs
        (created_at, decision, total_book_count, atlas_book_count,
         atlas_coverage_pct, promoted_gloss_count, missing_book_count,
         blocker_summary_json, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            now(),
            decision,
            len(books),
            len(atlas_books),
            coverage,
            promoted,
            len(missing),
            json.dumps(blocker_summary, ensure_ascii=False, sort_keys=True),
            json.dumps(payload, ensure_ascii=False, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)
    for row in missing:
        tags = str(row["functional_tags_json"] or "")
        if "BENNA_FORMULA_BRIDGE" in tags:
            route = "R5_PLAUSIBLE_PROSE_SHADOW + R3_MATHEMAGIC_OPERATOR_GRID"
            reason = "BENNA/formula family not yet converted to human shadow reading"
        elif "C86_PAYLOAD_OPERATOR" in tags or "VNCTIIN_CONTEXT_FRAME" in tags:
            route = "R2_NPC_PHRASE_STYLE_COMPARATOR + R5_PLAUSIBLE_PROSE_SHADOW"
            reason = "C86/VNCTIIN family needs context/payload shadow split"
        elif "R20_R02_PHASE_FRAME" in tags:
            route = "R5_PLAUSIBLE_PROSE_SHADOW"
            reason = "R20/R02 phase family needs bridge/phase shadow reading"
        elif "NAESE_C68_FATCT_LOCAL_SLOT" in tags:
            route = "R5_PLAUSIBLE_PROSE_SHADOW"
            reason = "NAESE/C68 slot family needs slot shadow reading"
        else:
            route = "R1_INGAME_CONTEXT_CORPUS"
            reason = "no targeted human shadow route assigned yet"
        conn.execute(
            """
            INSERT INTO human_translation_completion_audit_v1_missing_books
            (run_id, bookid, functional_tags_json, suggested_route,
             reason_missing, next_action)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                str(row["bookid"]),
                tags,
                route,
                reason,
                "select next family by cluster size and anchor strength; seed shadow reading only after source bridge exists",
            ),
        )

    conn.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "total_book_count": len(books),
                "atlas_book_count": len(atlas_books),
                "atlas_coverage_pct": coverage,
                "missing_book_count": len(missing),
                "promoted_gloss_count": promoted,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
