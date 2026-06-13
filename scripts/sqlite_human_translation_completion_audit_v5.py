#!/usr/bin/env python3
"""Completion audit for human translation atlas v6."""

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
        CREATE TABLE IF NOT EXISTS human_translation_completion_audit_v5_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            atlas_v6_run_id INTEGER NOT NULL,
            total_book_count INTEGER NOT NULL,
            atlas_book_count INTEGER NOT NULL,
            atlas_coverage_pct REAL NOT NULL,
            promoted_gloss_count INTEGER NOT NULL,
            missing_book_count INTEGER NOT NULL,
            blocker_summary_json TEXT NOT NULL,
            objective_checklist_json TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_translation_completion_audit_v5_missing_books (
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

    atlas_run_id = int(conn.execute("SELECT max(run_id) AS run_id FROM human_translation_atlas_v6_items").fetchone()["run_id"])
    books = conn.execute(
        """
        SELECT bookid, functional_tags_json
        FROM final_honest_reading_v19_books
        WHERE run_id=(SELECT max(run_id) FROM final_honest_reading_v19_books)
        ORDER BY CAST(bookid AS INTEGER)
        """
    ).fetchall()
    atlas_rows = conn.execute(
        "SELECT target_id, promotion_status, source_bridge_id, plausible_human_reading FROM human_translation_atlas_v6_items WHERE run_id=?",
        (atlas_run_id,),
    ).fetchall()
    atlas = {str(row["target_id"]): dict(row) for row in atlas_rows}
    missing = [row for row in books if str(row["bookid"]) not in atlas]
    promoted = sum(1 for row in atlas.values() if str(row["promotion_status"]) != "NOT_PROMOTED")
    anchored = sum(1 for row in atlas.values() if str(row["source_bridge_id"]))
    readable = sum(1 for row in atlas.values() if str(row["plausible_human_reading"]).strip())
    coverage = round((len(atlas) / max(1, len(books))) * 100.0, 2)
    checklist = [
        {
            "requirement": "human-readable plausible versions for the 70 book texts",
            "status": "covered_as_shadow",
            "evidence": f"{len(atlas)}/{len(books)} atlas rows have plausible_human_reading",
            "gap": "requires human review and falsification before treating as accepted translation",
        },
        {
            "requirement": "anchor translations in game relationships/books first",
            "status": "covered_as_anchor_bridge",
            "evidence": f"{anchored}/{len(atlas)} atlas rows have source_bridge_id and anchor_ids_json",
            "gap": "some anchors are structural/in-game lore constraints, not phrase-to-meaning keys",
        },
        {
            "requirement": "consider parallel references such as Mathemagica and related quests",
            "status": "covered_as_method_constraint",
            "evidence": "bridge layers use AWB mathemagic, Paradox keys, Honeminas formula, Great Calculator, Chayenne/Knightmare/Avar holdouts",
            "gap": "no official exact phrase-plus-meaning source found for book plaintext",
        },
        {
            "requirement": "consistent and reliable replicable method",
            "status": "covered_as_sqlite_pipeline",
            "evidence": "route -> bridge -> shadow -> atlas -> audit tables are materialized in SQLite",
            "gap": "shadow readings are not canonical decode promotions",
        },
        {
            "requirement": "actual translation solved",
            "status": "not_complete",
            "evidence": f"promoted_gloss_count={promoted}",
            "gap": "no canonical book gloss or accepted plaintext translation has been promoted",
        },
    ]
    if len(atlas) == len(books) and promoted == 0:
        decision = "HUMAN_SHADOW_ATLAS_COMPLETE_CANONICAL_TRANSLATION_UNSOLVED"
    elif len(atlas) == len(books):
        decision = "HUMAN_TRANSLATION_OBJECTIVE_REQUIRES_CANONICAL_REVIEW"
    else:
        decision = "HUMAN_TRANSLATION_OBJECTIVE_NOT_COMPLETE_MISSING_BOOKS"
    blocker_summary = {
        "current_strength": "70/70 anchored human shadow readings are available for review",
        "not_complete_reasons": [
            "shadow atlas is a plausible-reading layer, not accepted plaintext",
            "no canonical book gloss has been promoted",
            "human review and contradiction/falsification gates remain necessary",
        ],
        "next_priority": [
            "review atlas v6 rows by confidence tier",
            "run contradiction audit over all 70 shadow readings",
            "promote only small packages after falsification, not whole-book prose",
        ],
    }
    cur = conn.execute(
        """
        INSERT INTO human_translation_completion_audit_v5_runs
        (created_at, decision, atlas_v6_run_id, total_book_count,
         atlas_book_count, atlas_coverage_pct, promoted_gloss_count,
         missing_book_count, blocker_summary_json, objective_checklist_json,
         payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            json.dumps(checklist, ensure_ascii=False, sort_keys=True),
            json.dumps(
                {
                    "covered_books": sorted(atlas, key=lambda value: int(value)),
                    "anchored_count": anchored,
                    "readable_count": readable,
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
        ),
    )
    run_id = int(cur.lastrowid)
    for row in missing:
        conn.execute(
            """
            INSERT INTO human_translation_completion_audit_v5_missing_books
            (run_id, bookid, functional_tags_json, suggested_route,
             reason_missing, next_action)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                str(row["bookid"]),
                str(row["functional_tags_json"] or ""),
                "R1_INGAME_CONTEXT_CORPUS",
                "missing from atlas v6",
                "add residual route and rerun atlas",
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
                "anchored_count": anchored,
                "readable_count": readable,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
