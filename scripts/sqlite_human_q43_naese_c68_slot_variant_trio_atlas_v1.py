#!/usr/bin/env python3
"""Q43: consolidate NAESE/C68 slot-variant trio as a non-contig atlas entry."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
TARGET_BOOKS = ["22", "28", "48"]
ANALOGUE_CONTIGS = ["0", "1"]

SOURCE_BRIDGES = [
    {
        "bridge_id": "C68_FATCT_SLOT_GATE",
        "source_url": "sqlite:c68_fatct_slot_items",
        "allowed_inference": "Use FATC68T context as a structural slot/classifier frame.",
        "blocked_inference": "Do not translate C68, FATCT, or the frame as words.",
    },
    {
        "bridge_id": "NAESE_SLOT_CORE_GATE",
        "source_url": "sqlite:naese_slot_core_v1_items",
        "allowed_inference": "Separate ordered NAESE core from variant slot windows.",
        "blocked_inference": "Do not collapse variants into the canonical slot or assign phrase meaning.",
    },
    {
        "bridge_id": "Q35_CONTIG_SLOT_ANALOGUES",
        "source_url": "sqlite:human_q35_contig_shadow_atlas_v1_items",
        "allowed_inference": "Use exact contigs with NAESE slot/bridge structure as analogues.",
        "blocked_inference": "Do not import contig prose or component meanings into non-contig books.",
    },
    {
        "bridge_id": "BEWARE_VARIABLE_BLINK_UNIT",
        "source_url": "https://tibia.fandom.com/wiki/Beware_of_the_Bonelords_%28Book%29",
        "allowed_inference": "Bonelord units can vary in size; slot behavior may not be word-like.",
        "blocked_inference": "Do not decide syllable/letter/word value without contrastive proof.",
    },
    {
        "bridge_id": "AWB_LANGUAGE_MATHEMAGIC_PROCESSING",
        "source_url": "https://tibia.fandom.com/wiki/A_Wrinkled_Bonelord/Transcripts",
        "allowed_inference": "Treat slot frames as mathemagic processing surfaces.",
        "blocked_inference": "Do not promote a mathemagic dictionary key.",
    },
]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q43_naese_c68_slot_variant_trio_atlas_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q37_run_id INTEGER NOT NULL,
            q35_run_id INTEGER NOT NULL,
            c68_slot_run_id INTEGER NOT NULL,
            naese_core_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            target_book_count INTEGER NOT NULL,
            source_bridge_count INTEGER NOT NULL,
            analogue_contig_count INTEGER NOT NULL,
            c68_canonical_surface_count INTEGER NOT NULL,
            naese_ordered_core_count INTEGER NOT NULL,
            variant_window_count INTEGER NOT NULL,
            edge_support_count INTEGER NOT NULL,
            component_gloss_allowed_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            family_human_version TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q43_naese_c68_slot_variant_trio_atlas_v1_books (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            q36_likely_speech_act TEXT NOT NULL,
            q36_plausible_human_reading TEXT NOT NULL,
            c68_context_class TEXT NOT NULL,
            c68_slot_status TEXT NOT NULL,
            naese_status TEXT NOT NULL,
            naese_role_label TEXT NOT NULL,
            family_human_version TEXT NOT NULL,
            source_bridge_ids_json TEXT NOT NULL,
            translation_use TEXT NOT NULL,
            blocked_claims_json TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        );

        CREATE TABLE IF NOT EXISTS human_q43_naese_c68_slot_variant_trio_atlas_v1_analogues (
            run_id INTEGER NOT NULL,
            basecontigid TEXT NOT NULL,
            booksinorder TEXT NOT NULL,
            human_functional_version TEXT NOT NULL,
            analogue_use TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, basecontigid)
        );

        CREATE TABLE IF NOT EXISTS human_q43_naese_c68_slot_variant_trio_atlas_v1_sources (
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


def c68_items(conn: sqlite3.Connection, run_id: int) -> dict[str, sqlite3.Row]:
    return {
        str(row["bookid"]): row
        for row in conn.execute(
            """
            SELECT *
            FROM c68_fatct_slot_items
            WHERE run_id=? AND bookid IN ('22','28','48')
            """,
            (run_id,),
        )
    }


def naese_items(conn: sqlite3.Connection, run_id: int) -> dict[str, sqlite3.Row]:
    return {
        str(row["item_id"]): row
        for row in conn.execute(
            """
            SELECT *
            FROM naese_slot_core_v1_items
            WHERE run_id=? AND item_type='book' AND item_id IN ('22','28','48')
            """,
            (run_id,),
        )
    }


def q35_analogues(conn: sqlite3.Connection, run_id: int) -> list[sqlite3.Row]:
    placeholders = ",".join("?" for _ in ANALOGUE_CONTIGS)
    return list(
        conn.execute(
            f"""
            SELECT *
            FROM human_q35_contig_shadow_atlas_v1_items
            WHERE run_id=? AND basecontigid IN ({placeholders})
            ORDER BY CAST(basecontigid AS INTEGER)
            """,
            (run_id, *ANALOGUE_CONTIGS),
        )
    )


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q37 = latest_row(conn, "human_q37_noncontig_frontier_selection_v1_runs")
    q35 = latest_row(conn, "human_q35_contig_shadow_atlas_v1_runs")
    audit = latest_row(conn, "human_translation_completion_audit_v5_runs")
    c68_run_id = latest_run_id(conn, "c68_fatct_slot_items")
    naese_run_id = latest_run_id(conn, "naese_slot_core_v1_items")
    c68_by_book = c68_items(conn, c68_run_id)
    naese_by_book = naese_items(conn, naese_run_id)
    analogues = q35_analogues(conn, int(q35["run_id"]))

    missing = [bookid for bookid in TARGET_BOOKS if bookid not in c68_by_book or bookid not in naese_by_book]
    if missing:
        raise RuntimeError(f"missing slot evidence for books: {missing}")
    q36_rows = [q36_book(conn, bookid) for bookid in TARGET_BOOKS]
    c68_canonical_surface_count = sum(
        1 for row in c68_by_book.values() if str(row["context_class"]) == "CANONICAL_NAESE_FATCT_SLOT"
    )
    naese_ordered_core_count = sum(
        1 for row in naese_by_book.values() if str(row["status"]) == "ORDERED_CORE"
    )
    variant_window_count = sum(
        1 for row in naese_by_book.values() if str(row["status"]) == "VARIANT"
    )
    edge_support_count = sum(1 for row in c68_by_book.values() if str(row["edge_support"]) != "NO_EDGE_SUPPORT")
    component_gloss_allowed_count = sum(
        1 for row in c68_by_book.values() if json.loads(str(row["payload_json"])).get("gloss_allowed") is True
    )
    canonical_promotion_allowed_count = 0
    family_human_version = (
        "NAESE/C68 slot-variant trio: Book 22 is the ordered canonical slot witness, while Books 28 and 48 are controlled variant windows around the same FATC68T slot frame. "
        "The trio should be read as classifier/slot machinery under mathemagic and variable-unit language, not as a phrase translation."
    )
    decision = (
        "Q43_NAESE_C68_SLOT_VARIANT_TRIO_ATLAS_READY_NO_GLOSS"
        if len(q36_rows) == 3
        and len(analogues) == 2
        and c68_canonical_surface_count == 2
        and naese_ordered_core_count == 1
        and variant_window_count == 2
        and edge_support_count == 0
        and int(audit["promoted_gloss_count"]) == 0
        and component_gloss_allowed_count == 0
        and canonical_promotion_allowed_count == 0
        else "Q43_NAESE_C68_SLOT_VARIANT_TRIO_ATLAS_REQUIRES_REVIEW"
    )
    payload = {
        "question": "Can Q37 priority 5 become a non-contig slot/classifier atlas entry?",
        "answer": "Yes, as canonical slot plus controlled variant windows, with no gloss.",
        "allowed_reading": family_human_version,
        "blocked_reading": "No word gloss for NAESE, C68, FATCT, IVIFAST, slot, or any target book.",
        "next_action": "Use this trio as a classifier/slot control before comparing Chayenne register-frame books.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q43_naese_c68_slot_variant_trio_atlas_v1_runs (
                created_at, decision, q37_run_id, q35_run_id, c68_slot_run_id,
                naese_core_run_id, completion_audit_run_id, target_book_count,
                source_bridge_count, analogue_contig_count,
                c68_canonical_surface_count, naese_ordered_core_count,
                variant_window_count, edge_support_count,
                component_gloss_allowed_count, canonical_promotion_allowed_count,
                family_human_version, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                int(q37["run_id"]),
                int(q35["run_id"]),
                c68_run_id,
                naese_run_id,
                int(audit["run_id"]),
                len(TARGET_BOOKS),
                len(SOURCE_BRIDGES),
                len(analogues),
                c68_canonical_surface_count,
                naese_ordered_core_count,
                variant_window_count,
                edge_support_count,
                component_gloss_allowed_count,
                canonical_promotion_allowed_count,
                family_human_version,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q43_naese_c68_slot_variant_trio_atlas_v1_books (
                run_id, bookid, q36_likely_speech_act,
                q36_plausible_human_reading, c68_context_class,
                c68_slot_status, naese_status, naese_role_label,
                family_human_version, source_bridge_ids_json,
                translation_use, blocked_claims_json, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    str(row["bookid"]),
                    str(row["likely_speech_act"]),
                    str(row["plausible_human_reading"]),
                    str(c68_by_book[str(row["bookid"])]["context_class"]),
                    str(c68_by_book[str(row["bookid"])]["slot_status"]),
                    str(naese_by_book[str(row["bookid"])]["status"]),
                    str(naese_by_book[str(row["bookid"])]["role_label"]),
                    family_human_version,
                    j([source["bridge_id"] for source in SOURCE_BRIDGES]),
                    "human non-contig slot/classifier atlas only; not canonical plaintext",
                    j(["component_gloss", "sentence_translation", "NAESE_as_word", "C68_as_word", "FATCT_as_word", "slot_phrase_translation"]),
                    j(
                        {
                            "q36_book": dict(row),
                            "c68_fatct_slot": dict(c68_by_book[str(row["bookid"])]),
                            "naese_slot_core": dict(naese_by_book[str(row["bookid"])]),
                        }
                    ),
                )
                for row in q36_rows
            ],
        )
        conn.executemany(
            """
            INSERT INTO human_q43_naese_c68_slot_variant_trio_atlas_v1_analogues (
                run_id, basecontigid, booksinorder, human_functional_version,
                analogue_use, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    str(row["basecontigid"]),
                    str(row["booksinorder"]),
                    str(row["human_functional_version"]),
                    "exact-contig slot/classifier analogue; no semantic promotion",
                    j({"q35_contig": dict(row)}),
                )
                for row in analogues
            ],
        )
        conn.executemany(
            """
            INSERT INTO human_q43_naese_c68_slot_variant_trio_atlas_v1_sources (
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
                "analogue_contig_count": len(analogues),
                "c68_canonical_surface_count": c68_canonical_surface_count,
                "naese_ordered_core_count": naese_ordered_core_count,
                "variant_window_count": variant_window_count,
                "edge_support_count": edge_support_count,
                "component_gloss_allowed_count": component_gloss_allowed_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
            }
        )
    )


if __name__ == "__main__":
    main()
