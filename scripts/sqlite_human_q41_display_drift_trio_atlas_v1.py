#!/usr/bin/env python3
"""Q41: consolidate BTII/NSBVN/ATFNAAST display-drift trio."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
TARGET_BOOKS = ["11", "32", "43"]

SOURCE_BRIDGES = [
    {
        "bridge_id": "BTII_DISPLAY_DRIFT_GATE",
        "source_url": "sqlite:btii_display_drift_gate_items",
        "allowed_inference": "BTII/NSBVN/ATFNAAST is usable as book-scoped display-drift marker only.",
        "blocked_inference": "No family-wide or lexical promotion for BTII, NSBVN, or ATFNAAST.",
    },
    {
        "bridge_id": "Q10_BOOK32_36_DISPLAY_PAYLOAD_INDEPENDENCE_REJECTED",
        "source_url": "sqlite:human_q10_book32_36_display_payload_independence_audit_v1_runs",
        "allowed_inference": "Book32 belongs to display/control evidence, not independent payload.",
        "blocked_inference": "Do not translate Book32/36 as prose or payload.",
    },
    {
        "bridge_id": "BEWARE_LANGUAGE_MATH_NUMERIC_BOOKS",
        "source_url": "https://tibia.fandom.com/wiki/Beware_of_the_Bonelords_%28Book%29",
        "allowed_inference": "Numeric/mathematical language allows display/formula control material.",
        "blocked_inference": "Mathematical framing is not a dictionary.",
    },
    {
        "bridge_id": "GREAT_CALCULATOR_COMPILED_LANGUAGE",
        "source_url": "https://www.tibiawiki.com.br/wiki/You_Cannot_Even_Imagine_%28Book%29",
        "allowed_inference": "Compiled-corpus lore supports keeping formula fragments as controls.",
        "blocked_inference": "Do not infer direct phrase meaning.",
    },
]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q41_display_drift_trio_atlas_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q37_run_id INTEGER NOT NULL,
            q10_run_id INTEGER NOT NULL,
            display_drift_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            target_book_count INTEGER NOT NULL,
            source_bridge_count INTEGER NOT NULL,
            display_drift_count INTEGER NOT NULL,
            residual_blocked_context_count INTEGER NOT NULL,
            display_only_count INTEGER NOT NULL,
            lexical_gloss_allowed_count INTEGER NOT NULL,
            family_wide_promotion_allowed_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            family_human_version TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q41_display_drift_trio_atlas_v1_books (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            drift_status TEXT NOT NULL,
            split_status TEXT NOT NULL,
            q36_plausible_human_reading TEXT NOT NULL,
            functional_label TEXT NOT NULL,
            family_human_version TEXT NOT NULL,
            source_bridge_ids_json TEXT NOT NULL,
            translation_use TEXT NOT NULL,
            blocked_claims_json TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        );

        CREATE TABLE IF NOT EXISTS human_q41_display_drift_trio_atlas_v1_sources (
            run_id INTEGER NOT NULL,
            bridge_id TEXT NOT NULL,
            source_url TEXT NOT NULL,
            allowed_inference TEXT NOT NULL,
            blocked_inference TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bridge_id)
        );
        """
    )


def latest_row(conn: sqlite3.Connection, table: str) -> sqlite3.Row:
    row = conn.execute(f"SELECT * FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    if row is None:
        raise RuntimeError(f"missing required row: {table}")
    return row


def latest_run_id(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT max(run_id) FROM {table}").fetchone()
    if row is None or row[0] is None:
        raise RuntimeError(f"missing required run: {table}")
    return int(row[0])


def q36_book(conn: sqlite3.Connection, bookid: str) -> sqlite3.Row:
    row = conn.execute(
        """
        SELECT *
        FROM human_q36_book_contig_shadow_integration_v1_items
        WHERE run_id=(SELECT max(run_id) FROM human_q36_book_contig_shadow_integration_v1_items)
          AND bookid=?
        """,
        (bookid,),
    ).fetchone()
    if row is None:
        raise RuntimeError(f"missing Q36 book {bookid}")
    return row


def drift_items(conn: sqlite3.Connection, run_id: int) -> dict[str, sqlite3.Row]:
    return {
        str(row["bookid"]): row
        for row in conn.execute(
            """
            SELECT *
            FROM btii_display_drift_gate_items
            WHERE run_id=? AND bookid IN ('11','32','43')
            """,
            (run_id,),
        )
    }


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q37 = latest_row(conn, "human_q37_noncontig_frontier_selection_v1_runs")
    q10 = latest_row(conn, "human_q10_book32_36_display_payload_independence_audit_v1_runs")
    drift_run_id = latest_run_id(conn, "btii_display_drift_gate_items")
    audit = latest_row(conn, "human_translation_completion_audit_v5_runs")
    drift_by_book = drift_items(conn, drift_run_id)
    missing = [bookid for bookid in TARGET_BOOKS if bookid not in drift_by_book]
    if missing:
        raise RuntimeError(f"missing display drift items: {missing}")

    q36_rows = [q36_book(conn, bookid) for bookid in TARGET_BOOKS]
    display_drift_count = sum(
        1 for row in drift_by_book.values() if str(row["decision"]) == "BTII_NSBVN_ATFNAAST_BLOCK_DISPLAY_DRIFT_NO_GLOSS"
    )
    residual_blocked_context_count = sum(
        1 for row in drift_by_book.values() if "RESIDUAL_BLOCKED_CONTEXT" in str(row["drift_status"])
    )
    display_only_count = sum(
        1 for row in drift_by_book.values() if str(row["drift_status"]) == "WEAK_EXTERNAL_DRIFT_DISPLAY_ONLY_NO_GLOSS"
    )
    lexical_gloss_allowed_count = sum(int(row["lexical_gloss_allowed"]) for row in drift_by_book.values())
    family_wide_promotion_allowed_count = sum(int(row["family_wide_promotion_allowed"]) for row in drift_by_book.values())
    canonical_promotion_allowed_count = 0
    family_human_version = (
        "BTII/NSBVN/ATFNAAST display-drift trio: Books 11, 32, and 43 repeat a book-scoped display/formula drift marker. "
        "Books 11 and 32 still carry residual-blocked context; Book 43 is display-only. The trio should stabilize the display layer and prevent false prose, not translate payload."
    )
    decision = (
        "Q41_DISPLAY_DRIFT_TRIO_ATLAS_READY_NO_GLOSS"
        if len(q36_rows) == 3
        and display_drift_count == 3
        and residual_blocked_context_count == 2
        and display_only_count == 1
        and lexical_gloss_allowed_count == 0
        and family_wide_promotion_allowed_count == 0
        and int(q10["promoted_plaintext_gloss_count"]) == 0
        and int(audit["promoted_gloss_count"]) == 0
        and canonical_promotion_allowed_count == 0
        else "Q41_DISPLAY_DRIFT_TRIO_ATLAS_REQUIRES_REVIEW"
    )
    payload = {
        "question": "Can Q37 priority 4 be consolidated as a display-only human shadow family?",
        "answer": "Yes. The trio stabilizes display/formula drift and blocks false prose.",
        "allowed_reading": family_human_version,
        "blocked_reading": "No payload, sentence translation, family-wide promotion, or lexical gloss for BTII/NSBVN/ATFNAAST.",
        "next_action": "Use the trio as a negative control when evaluating formula-handoff candidates.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q41_display_drift_trio_atlas_v1_runs (
                created_at, decision, q37_run_id, q10_run_id,
                display_drift_run_id, completion_audit_run_id,
                target_book_count, source_bridge_count, display_drift_count,
                residual_blocked_context_count, display_only_count,
                lexical_gloss_allowed_count, family_wide_promotion_allowed_count,
                canonical_promotion_allowed_count, family_human_version,
                payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                int(q37["run_id"]),
                int(q10["run_id"]),
                drift_run_id,
                int(audit["run_id"]),
                len(TARGET_BOOKS),
                len(SOURCE_BRIDGES),
                display_drift_count,
                residual_blocked_context_count,
                display_only_count,
                lexical_gloss_allowed_count,
                family_wide_promotion_allowed_count,
                canonical_promotion_allowed_count,
                family_human_version,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q41_display_drift_trio_atlas_v1_books (
                run_id, bookid, drift_status, split_status,
                q36_plausible_human_reading, functional_label,
                family_human_version, source_bridge_ids_json, translation_use,
                blocked_claims_json, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    str(row["bookid"]),
                    str(drift_by_book[str(row["bookid"])]["drift_status"]),
                    str(drift_by_book[str(row["bookid"])]["split_status"] or ""),
                    str(row["plausible_human_reading"]),
                    str(drift_by_book[str(row["bookid"])]["functional_label"]),
                    family_human_version,
                    j([source["bridge_id"] for source in SOURCE_BRIDGES]),
                    "display-only human shadow control; not payload or plaintext",
                    j(["component_gloss", "sentence_translation", "payload_translation", "family_wide_promotion"]),
                    j({"q36_book": dict(row), "display_drift": dict(drift_by_book[str(row["bookid"])])}),
                )
                for row in q36_rows
            ],
        )
        conn.executemany(
            """
            INSERT INTO human_q41_display_drift_trio_atlas_v1_sources (
                run_id, bridge_id, source_url, allowed_inference,
                blocked_inference, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    str(source["bridge_id"]),
                    str(source["source_url"]),
                    str(source["allowed_inference"]),
                    str(source["blocked_inference"]),
                    j(source),
                )
                for source in SOURCE_BRIDGES
            ],
        )

    print(
        j(
            {
                "run_id": run_id,
                "decision": decision,
                "target_book_count": len(TARGET_BOOKS),
                "source_bridge_count": len(SOURCE_BRIDGES),
                "display_drift_count": display_drift_count,
                "residual_blocked_context_count": residual_blocked_context_count,
                "display_only_count": display_only_count,
                "lexical_gloss_allowed_count": lexical_gloss_allowed_count,
                "family_wide_promotion_allowed_count": family_wide_promotion_allowed_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
            }
        )
    )


if __name__ == "__main__":
    main()
