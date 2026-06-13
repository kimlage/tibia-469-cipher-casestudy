#!/usr/bin/env python3
"""Completion audit for human translation atlas v5."""

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
        CREATE TABLE IF NOT EXISTS human_translation_completion_audit_v4_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            atlas_v5_run_id INTEGER NOT NULL,
            total_book_count INTEGER NOT NULL,
            atlas_book_count INTEGER NOT NULL,
            atlas_coverage_pct REAL NOT NULL,
            promoted_gloss_count INTEGER NOT NULL,
            missing_book_count INTEGER NOT NULL,
            blocker_summary_json TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_translation_completion_audit_v4_missing_books (
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


def reason_for(tags: str) -> tuple[str, str]:
    if "LTAST_TTNVVN_BOUNDARY_OPERATOR" in tags:
        return ("R5_PLAUSIBLE_PROSE_SHADOW", "LTAST/TTNVVN boundary residual needs human route")
    if "ZERO_PAIR_LOCAL_PAIR" in tags:
        return ("R5_PLAUSIBLE_PROSE_SHADOW", "local-pair residual needs pair shadow reading")
    if "O23_ONAF_VEINLETFNAAST_PAYLOAD_CONTEXT" in tags or "BOOK56_CLEAN_COMPONENT_WITH_BOOK38" in tags:
        return ("R5_PLAUSIBLE_PROSE_SHADOW", "O23/FNAAST endpoint or Book38 component residual needs route")
    if "BTII_NSBVN_ATFNAAST_DISPLAY_DRIFT" in tags:
        return ("R1_INGAME_CONTEXT_CORPUS", "display-drift residual needs audit-only shadow route")
    if "RESIDUAL_TEMPLATE_TO_" in tags:
        return ("R1_INGAME_CONTEXT_CORPUS", "residual template alignment needs cluster shadow route")
    if "CHAYENNE_NEAR_VARIANT" in tags:
        return ("R2_NPC_PHRASE_STYLE_COMPARATOR", "Chayenne near-variant residual needs frame route")
    if "BOOK7_NEIAAETTA_CONTINUITY" in tags:
        return ("R5_PLAUSIBLE_PROSE_SHADOW", "NEIAAETTA continuity-only residual needs phase-control route")
    if "469_MARKER" in tags:
        return ("R1_INGAME_CONTEXT_CORPUS", "469 marker/metaformula residual needs special route")
    if "UNIQUE_PREFIX_HEADER" in tags:
        return ("R1_INGAME_CONTEXT_CORPUS", "unique/scrambled header residual needs special route")
    if "BOOK55_INTERNAL_REPEAT_VARIANT" in tags:
        return ("R5_PLAUSIBLE_PROSE_SHADOW", "Book55 internal repeat residual needs repeat route")
    return ("R1_INGAME_CONTEXT_CORPUS", "unassigned residual needs human route")


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    atlas_run_id = int(conn.execute("SELECT max(run_id) AS run_id FROM human_translation_atlas_v5_items").fetchone()["run_id"])
    books = conn.execute(
        """
        SELECT bookid, functional_tags_json
        FROM final_honest_reading_v19_books
        WHERE run_id=(SELECT max(run_id) FROM final_honest_reading_v19_books)
        ORDER BY CAST(bookid AS INTEGER)
        """
    ).fetchall()
    atlas = {
        str(row["target_id"]): str(row["promotion_status"])
        for row in conn.execute(
            "SELECT target_id, promotion_status FROM human_translation_atlas_v5_items WHERE run_id=?",
            (atlas_run_id,),
        ).fetchall()
    }
    missing = [row for row in books if str(row["bookid"]) not in atlas]
    promoted = sum(1 for status in atlas.values() if status != "NOT_PROMOTED")
    coverage = round((len(atlas) / max(1, len(books))) * 100.0, 2)
    decision = "HUMAN_TRANSLATION_OBJECTIVE_NOT_COMPLETE_ATLAS_V5_EXPAND_RESIDUAL_ROUTES"
    blocker_summary = {
        "current_strength": "51 anchored shadow readings after adding BENNA/formula and NAESE/C68 slot families",
        "remaining_priority": ["residual route assignment", "display-drift audit", "local-pair and endpoint residuals"],
        "not_complete_reasons": [
            "atlas still covers less than all 70 books",
            "no canonical book gloss has been promoted",
        ],
    }
    cur = conn.execute(
        """
        INSERT INTO human_translation_completion_audit_v4_runs
        (created_at, decision, atlas_v5_run_id, total_book_count,
         atlas_book_count, atlas_coverage_pct, promoted_gloss_count,
         missing_book_count, blocker_summary_json, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            now(),
            decision,
            atlas_run_id,
            len(books),
            len(atlas),
            coverage,
            promoted,
            len(missing),
            json.dumps(blocker_summary, ensure_ascii=False, sort_keys=True),
            json.dumps({"covered_books": sorted(atlas, key=lambda value: int(value))}, ensure_ascii=False, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)
    for row in missing:
        tags = str(row["functional_tags_json"] or "")
        route, reason = reason_for(tags)
        conn.execute(
            """
            INSERT INTO human_translation_completion_audit_v4_missing_books
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
                "create residual bridge before adding prose-like shadow reading",
            ),
        )

    conn.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "total_book_count": len(books),
                "atlas_book_count": len(atlas),
                "atlas_coverage_pct": coverage,
                "missing_book_count": len(missing),
                "promoted_gloss_count": promoted,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
