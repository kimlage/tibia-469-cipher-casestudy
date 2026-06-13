#!/usr/bin/env python3
"""Q39: consolidate the VNCTIIN/TIINNEF phase trio as a non-contig atlas entry."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
TARGET_BOOKS = ["19", "31", "57"]
CONTROL_BOOKS = ["6", "7"]

SOURCE_BRIDGES = [
    {
        "bridge_id": "AWB_LANGUAGE_MATHEMAGIC_PROCESSING",
        "source_url": "https://tibia.fandom.com/wiki/A_Wrinkled_Bonelord/Transcripts",
        "source_claim": "Bonelord language relies on mathemagic and needs fast calculation to decipher even basic texts.",
        "allowed_inference": "Use VNCTIIN/TIINNEF as phase/context machinery to be processed, not read as direct prose.",
        "blocked_inference": "Do not translate TIINNEF, VNCTIIN, or C68 as words.",
    },
    {
        "bridge_id": "AWB_COMPLEX_FORMULA_SUBJECTIVE_VIEWER",
        "source_url": "https://tibia.fandom.com/wiki/A_Wrinkled_Bonelord/Transcripts",
        "source_claim": "Bonelord self-naming is a complex formula that changes for the subjective viewer.",
        "allowed_inference": "Treat phase anchors as formula/viewer/selector behavior candidates.",
        "blocked_inference": "Do not claim these books encode the race name.",
    },
    {
        "bridge_id": "BEWARE_VARIABLE_BLINK_UNIT",
        "source_url": "https://tibia.fandom.com/wiki/Beware_of_the_Bonelords_%28Book%29",
        "source_claim": "A blink can mean syllable, letter, or word; the language is also mathematics.",
        "allowed_inference": "Keep the unit size of TIINNEF/VNCTIIN flexible and contrastive.",
        "blocked_inference": "Do not decide whether TIINNEF is syllable, letter, word, phase, or marker by intuition.",
    },
    {
        "bridge_id": "BOOK7_PHASE_SHADOW_BRIDGE",
        "source_url": "sqlite:human_book7_phase_shadow_probe_v1",
        "source_claim": "Book7 bridges NEIAAETTA continuity into TIINNEF phase anchor; Books 19/31/57 are held-out VNCTIIN+TIINNEF controls.",
        "allowed_inference": "Use Book7 as a local bridge/control only.",
        "blocked_inference": "Do not import Book7 or 3478 semantics into the trio.",
    },
]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q39_vnctiin_tiinnef_phase_trio_atlas_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q37_run_id INTEGER NOT NULL,
            book7_phase_run_id INTEGER NOT NULL,
            q8_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            target_book_count INTEGER NOT NULL,
            control_book_count INTEGER NOT NULL,
            source_bridge_count INTEGER NOT NULL,
            phase_context_count INTEGER NOT NULL,
            bridge_control_count INTEGER NOT NULL,
            continuity_control_count INTEGER NOT NULL,
            component_gloss_allowed_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            family_human_version TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q39_vnctiin_tiinnef_phase_trio_atlas_v1_books (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            classification TEXT NOT NULL,
            q36_plausible_human_reading TEXT NOT NULL,
            family_human_version TEXT NOT NULL,
            row0_markers_json TEXT NOT NULL,
            source_bridge_ids_json TEXT NOT NULL,
            translation_use TEXT NOT NULL,
            blocked_claims_json TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        );

        CREATE TABLE IF NOT EXISTS human_q39_vnctiin_tiinnef_phase_trio_atlas_v1_controls (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            classification TEXT NOT NULL,
            shadow_implication TEXT NOT NULL,
            control_use TEXT NOT NULL,
            blocked_claims_json TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        );

        CREATE TABLE IF NOT EXISTS human_q39_vnctiin_tiinnef_phase_trio_atlas_v1_sources (
            run_id INTEGER NOT NULL,
            bridge_id TEXT NOT NULL,
            source_url TEXT NOT NULL,
            source_claim TEXT NOT NULL,
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


def book7_items(conn: sqlite3.Connection, run_id: int) -> dict[str, sqlite3.Row]:
    return {
        str(row["bookid"]): row
        for row in conn.execute(
            """
            SELECT *
            FROM human_book7_phase_shadow_probe_v1_items
            WHERE run_id=?
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
    book7_run = latest_row(conn, "human_book7_phase_shadow_probe_v1_runs")
    q8_run_id = latest_run_id(conn, "human_q8_book6_7_phase_path_3478_transition_probe_v1_runs")
    q8_run = conn.execute(
        "SELECT * FROM human_q8_book6_7_phase_path_3478_transition_probe_v1_runs WHERE run_id=?",
        (q8_run_id,),
    ).fetchone()
    audit = latest_row(conn, "human_translation_completion_audit_v5_runs")
    book7_by_book = book7_items(conn, int(book7_run["run_id"]))

    missing = [bookid for bookid in TARGET_BOOKS + CONTROL_BOOKS if bookid not in book7_by_book]
    if missing:
        raise RuntimeError(f"missing Book7 phase probe items: {missing}")

    target_rows = [q36_book(conn, bookid) for bookid in TARGET_BOOKS]
    phase_context_count = sum(
        1 for bookid in TARGET_BOOKS if book7_by_book[bookid]["classification"] == "PHASE_CONTEXT_CONTROL"
    )
    bridge_control_count = sum(
        1 for bookid in CONTROL_BOOKS if book7_by_book[bookid]["classification"] == "PHASE_BRIDGE_CONTINUITY_TO_ANCHOR"
    )
    continuity_control_count = sum(
        1 for bookid in CONTROL_BOOKS if book7_by_book[bookid]["classification"] == "CONTINUITY_ONLY_CONTROL"
    )
    family_human_version = (
        "VNCTIIN/TIINNEF phase-context trio: Books 19, 31, and 57 carry TIINNEF inside a VNCTIIN/C68 context frame. "
        "Compared with Book 6 as continuity-only control and Book 7 as continuity-to-phase bridge, the trio behaves as held-out phase-context evidence. "
        "It should be read as phase/context machinery under mathemagic, not as plaintext."
    )
    component_gloss_allowed_count = 0
    canonical_promotion_allowed_count = 0
    decision = (
        "Q39_VNCTIIN_TIINNEF_PHASE_TRIO_ATLAS_READY_NO_GLOSS"
        if len(target_rows) == 3
        and phase_context_count == 3
        and bridge_control_count == 1
        and continuity_control_count == 1
        and int(book7_run["accepted_human_gloss_count"]) == 0
        and int(q8_run["promoted_plaintext_gloss_count"]) == 0
        and int(audit["promoted_gloss_count"]) == 0
        and component_gloss_allowed_count == 0
        and canonical_promotion_allowed_count == 0
        else "Q39_VNCTIIN_TIINNEF_PHASE_TRIO_ATLAS_REQUIRES_REVIEW"
    )
    payload = {
        "question": "Can Q37 priority 2 become a human shadow atlas entry?",
        "answer": "Yes, as held-out VNCTIIN/TIINNEF phase-context evidence controlled by Book6/Book7.",
        "allowed_reading": family_human_version,
        "blocked_reading": "No word gloss for VNCTIIN, TIINNEF, C68, NEIAAETTA, 3478, Book7, or the trio.",
        "next_action": "Use this as the model for phase-context families before any phrase-level translation attempt.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q39_vnctiin_tiinnef_phase_trio_atlas_v1_runs (
                created_at, decision, q37_run_id, book7_phase_run_id,
                q8_run_id, completion_audit_run_id, target_book_count,
                control_book_count, source_bridge_count, phase_context_count,
                bridge_control_count, continuity_control_count,
                component_gloss_allowed_count, canonical_promotion_allowed_count,
                family_human_version, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                int(q37["run_id"]),
                int(book7_run["run_id"]),
                q8_run_id,
                int(audit["run_id"]),
                len(TARGET_BOOKS),
                len(CONTROL_BOOKS),
                len(SOURCE_BRIDGES),
                phase_context_count,
                bridge_control_count,
                continuity_control_count,
                component_gloss_allowed_count,
                canonical_promotion_allowed_count,
                family_human_version,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q39_vnctiin_tiinnef_phase_trio_atlas_v1_books (
                run_id, bookid, classification, q36_plausible_human_reading,
                family_human_version, row0_markers_json, source_bridge_ids_json,
                translation_use, blocked_claims_json, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    str(row["bookid"]),
                    str(book7_by_book[str(row["bookid"])]["classification"]),
                    str(row["plausible_human_reading"]),
                    family_human_version,
                    str(json.loads(str(row["evidence_json"]))["q30_book"]["row0_markers_json"]),
                    j([source["bridge_id"] for source in SOURCE_BRIDGES]),
                    "human non-contig phase-context shadow only; not canonical plaintext",
                    j(["component_gloss", "sentence_translation", "3478_gloss", "TIINNEF_as_word", "VNCTIIN_as_word"]),
                    j({"q36_book": dict(row), "book7_phase_item": dict(book7_by_book[str(row["bookid"])])}),
                )
                for row in target_rows
            ],
        )
        conn.executemany(
            """
            INSERT INTO human_q39_vnctiin_tiinnef_phase_trio_atlas_v1_controls (
                run_id, bookid, classification, shadow_implication, control_use,
                blocked_claims_json, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    bookid,
                    str(book7_by_book[bookid]["classification"]),
                    str(book7_by_book[bookid]["shadow_implication"]),
                    (
                        "Book6 continuity-only negative/control"
                        if bookid == "6"
                        else "Book7 continuity-to-phase positive bridge; 3478 remains no-gloss"
                    ),
                    j(["component_gloss", "sentence_translation", "3478_gloss", "NEIAAETTA_as_word", "TIINNEF_as_word"]),
                    j({"book7_phase_item": dict(book7_by_book[bookid]), "q8_run": dict(q8_run)}),
                )
                for bookid in CONTROL_BOOKS
            ],
        )
        conn.executemany(
            """
            INSERT INTO human_q39_vnctiin_tiinnef_phase_trio_atlas_v1_sources (
                run_id, bridge_id, source_url, source_claim, allowed_inference,
                blocked_inference, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    str(source["bridge_id"]),
                    str(source["source_url"]),
                    str(source["source_claim"]),
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
                "control_book_count": len(CONTROL_BOOKS),
                "source_bridge_count": len(SOURCE_BRIDGES),
                "phase_context_count": phase_context_count,
                "bridge_control_count": bridge_control_count,
                "continuity_control_count": continuity_control_count,
                "component_gloss_allowed_count": component_gloss_allowed_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
            }
        )
    )


if __name__ == "__main__":
    main()
