#!/usr/bin/env python3
"""Q83: execute exact-source audit for Q82 T01 BENNA->C86/VNCTIIN."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
TARGET_ID = "Q82_T01_BENNA_C86_VNCTIIN_FORMULA_HANDOFF"

WEB_QUERIES = [
    {
        "query_id": "Q83_WEB_01",
        "query_text": '"LEITELBENNA" "Tibia"',
        "result_status": "NO_RELEVANT_EXACT_SOURCE_HIT",
        "notes": "No independent source page binding LEITELBENNA to meaning.",
    },
    {
        "query_id": "Q83_WEB_02",
        "query_text": '"TAILBETFTE" "VNCTIIN"',
        "result_status": "NO_RELEVANT_EXACT_SOURCE_HIT",
        "notes": "No web result with the handoff suffix and VNCTIIN context.",
    },
    {
        "query_id": "Q83_WEB_03",
        "query_text": '"LEITELBENNAIFIININSBASTFNENIIFINI"',
        "result_status": "NO_RELEVANT_EXACT_SOURCE_HIT",
        "notes": "No exact long BENNA body hit outside local/internal artifacts.",
    },
    {
        "query_id": "Q83_WEB_04",
        "query_text": '"BENNA" "VNCTIIN"',
        "result_status": "NO_RELEVANT_EXACT_SOURCE_HIT",
        "notes": "Search returns no target-level Tibia source relation.",
    },
    {
        "query_id": "Q83_WEB_05",
        "query_text": '"BENNA" "469" "Tibia"',
        "result_status": "FALSE_POSITIVES_NO_TARGET_SOURCE",
        "notes": "False positives and unrelated BENNA occurrences; no 469 sequence meaning.",
    },
    {
        "query_id": "Q83_WEB_06",
        "query_text": '"LTAST" "Tibia" "469"',
        "result_status": "NO_RELEVANT_EXACT_SOURCE_HIT",
        "notes": "No exact LTAST target relation in public search.",
    },
    {
        "query_id": "Q83_WEB_07",
        "query_text": '"VNCTIIN" "469"',
        "result_status": "NO_PROMOTABLE_TARGET_RELATION",
        "notes": "No source links VNCTIIN to the BENNA handoff target as meaning.",
    },
    {
        "query_id": "Q83_WEB_08",
        "query_text": 'site:tibia.com "BENNA" "469"',
        "result_status": "NO_OFFICIAL_EXACT_HIT",
        "notes": "No official tibia.com exact hit for BENNA/469 target relation.",
    },
]

SOURCE_CHECKS = [
    {
        "source_id": "AWB_469_LANGUAGE_MATHEMAGIC",
        "source_url": "https://tibia.fandom.com/wiki/A_Wrinkled_Bonelord/Transcripts",
        "source_result": "METHOD_SUPPORT_NO_TARGET_SEQUENCE",
        "support_value": "A Wrinkled Bonelord links 469 to numbers, mathematics, and mathemagical processing.",
        "blocked_inference": "Does not mention BENNA, LTAST, TAILBETFTE, VNCTIIN handoff, Book10, or Book35 meaning.",
    },
    {
        "source_id": "BEWARE_LANGUAGE_MATH_NUMERIC_BOOKS",
        "source_url": "https://tibia.fandom.com/wiki/Beware_of_the_Bonelords_%28Book%29",
        "source_result": "REGISTER_SUPPORT_NO_TARGET_SEQUENCE",
        "support_value": "Beware frames Bonelord native language as blinking/numeric/mathematical and books as complex numeric code.",
        "blocked_inference": "Does not identify the BENNA formula body, C86/VNCTIIN, or any handoff semantics.",
    },
    {
        "source_id": "HONEMINAS_FORMULA_PARALLEL",
        "source_url": "https://www.tibiawiki.com.br/Honeminas_Formula",
        "source_result": "FORMULA_MODE_SUPPORT_NO_TARGET_LINK",
        "support_value": "Honeminas supplies an in-game formula discourse mode tied to magic/world structure.",
        "blocked_inference": "No mechanical or lore link from Honeminas formula notation to the BENNA handoff sequence.",
    },
    {
        "source_id": "PARADOX_1_PLUS_1_KEYS",
        "source_url": "https://www.tibia-wiki.net/wiki/Paradox_Tower_Quest/Spoiler",
        "source_result": "OPERATOR_MODE_SUPPORT_NO_TARGET_SEQUENCE",
        "support_value": "Paradox/Mathemagics supports context-dependent weird operator reasoning.",
        "blocked_inference": "No exact BENNA/LTAST/TAILBETFTE/VNCTIIN relation or predictive rule.",
    },
    {
        "source_id": "TIBIAWIKI_BR_469_SYNTHESIS",
        "source_url": "https://www.tibiawiki.com.br/469",
        "source_result": "SECONDARY_SYNTHESIS_SUPPORT_NO_TARGET_SEQUENCE",
        "support_value": "The 469 page collects in-game references: Chayenne, Avar Tar, AWB, mathemagics, Great Calculator, and Rosetta leads.",
        "blocked_inference": "It explicitly does not prove a solid translation claim for the target sequence.",
    },
]

TESTS = [
    {
        "test_id": "Q83_T01_WEB_EXACT_SEQUENCE",
        "test_result": "FAILS_EXACT_SOURCE_REQUIREMENT",
        "interpretation": "No web query found exact target sequence plus meaning/provenance.",
    },
    {
        "test_id": "Q83_T02_SOURCE_METHOD_FIREWALL",
        "test_result": "PASSES_METHOD_SUPPORT_ONLY",
        "interpretation": "AWB, Beware, Honeminas, Paradox, and 469 support method/register only.",
    },
    {
        "test_id": "Q83_T03_BOOK10_35_STRUCTURAL_STATUS",
        "test_result": "PRESERVE_SHADOW_HANDOFF_ONLY",
        "interpretation": "Books 10/35 remain structural formula handoff candidates, not translated prose.",
    },
    {
        "test_id": "Q83_T04_PROMOTION_FIREWALL",
        "test_result": "PASSES_BLOCK_PROMOTION",
        "interpretation": "Q79 and completion audit keep promoted_gloss_count at zero.",
    },
]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q83_benna_c86_exact_source_audit_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q82_run_id INTEGER NOT NULL,
            q79_run_id INTEGER NOT NULL,
            q81_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            target_id TEXT NOT NULL,
            target_book_count INTEGER NOT NULL,
            web_query_count INTEGER NOT NULL,
            web_exact_target_hit_count INTEGER NOT NULL,
            official_exact_target_hit_count INTEGER NOT NULL,
            source_check_count INTEGER NOT NULL,
            method_support_source_count INTEGER NOT NULL,
            exact_source_sequence_count INTEGER NOT NULL,
            exact_meaning_relation_count INTEGER NOT NULL,
            lexical_ready_count INTEGER NOT NULL,
            direct_gloss_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            target_status TEXT NOT NULL,
            result_human_version TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q83_benna_c86_exact_source_audit_v1_queries (
            run_id INTEGER NOT NULL,
            query_id TEXT NOT NULL,
            query_text TEXT NOT NULL,
            result_status TEXT NOT NULL,
            notes TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, query_id)
        );

        CREATE TABLE IF NOT EXISTS human_q83_benna_c86_exact_source_audit_v1_sources (
            run_id INTEGER NOT NULL,
            source_id TEXT NOT NULL,
            source_url TEXT NOT NULL,
            source_result TEXT NOT NULL,
            support_value TEXT NOT NULL,
            blocked_inference TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, source_id)
        );

        CREATE TABLE IF NOT EXISTS human_q83_benna_c86_exact_source_audit_v1_books (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            symbol_text TEXT NOT NULL,
            likely_speech_act TEXT NOT NULL,
            plausible_human_reading TEXT NOT NULL,
            target_result TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        );

        CREATE TABLE IF NOT EXISTS human_q83_benna_c86_exact_source_audit_v1_tests (
            run_id INTEGER NOT NULL,
            test_id TEXT NOT NULL,
            test_result TEXT NOT NULL,
            interpretation TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, test_id)
        );
        """
    )


def latest_row(conn: sqlite3.Connection, table: str) -> sqlite3.Row:
    row = conn.execute(f"SELECT * FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    if row is None:
        raise RuntimeError(f"missing required row: {table}")
    return row


def load_target(conn: sqlite3.Connection, q82_run_id: int) -> sqlite3.Row:
    row = conn.execute(
        """
        SELECT *
        FROM human_q82_exact_source_target_queue_v1_targets
        WHERE run_id=? AND target_id=?
        """,
        (q82_run_id, TARGET_ID),
    ).fetchone()
    if row is None:
        raise RuntimeError(f"missing Q82 target {TARGET_ID}")
    return row


def load_books(conn: sqlite3.Connection, q82_run_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT *
        FROM human_q82_exact_source_target_queue_v1_books
        WHERE run_id=? AND target_id=?
        ORDER BY CAST(bookid AS INTEGER)
        """,
        (q82_run_id, TARGET_ID),
    ).fetchall()


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q82 = latest_row(conn, "human_q82_exact_source_target_queue_v1_runs")
    q79 = latest_row(conn, "human_q79_global_source_firewall_v1_runs")
    q81 = latest_row(conn, "human_q81_controlled_shadow_export_v1_runs")
    completion = latest_row(conn, "human_translation_completion_audit_v5_runs")
    target = load_target(conn, int(q82["run_id"]))
    books = load_books(conn, int(q82["run_id"]))

    target_book_count = len(books)
    web_query_count = len(WEB_QUERIES)
    web_exact_target_hit_count = 0
    official_exact_target_hit_count = 0
    source_check_count = len(SOURCE_CHECKS)
    method_support_source_count = len(SOURCE_CHECKS)
    exact_source_sequence_count = 0
    exact_meaning_relation_count = 0
    lexical_ready_count = 0
    direct_gloss_count = 0
    canonical_promotion_allowed_count = 0
    target_status = "SOURCE_AUDITED_METHOD_SUPPORT_ONLY_NO_PROMOTION"
    result_human_version = (
        "Q83 finds no exact source for BENNA->C86/VNCTIIN handoff. The target keeps strong "
        "structural/method support, but AWB, Beware, Honeminas, Paradox, and 469 synthesis do "
        "not provide the exact target sequence or a meaning relation."
    )
    decision = (
        "Q83_BENNA_C86_EXACT_SOURCE_AUDIT_METHOD_SUPPORT_NO_EXACT_SOURCE_NO_GLOSS"
        if target_book_count == 2
        and web_query_count == 8
        and web_exact_target_hit_count == 0
        and official_exact_target_hit_count == 0
        and source_check_count == 5
        and exact_source_sequence_count == 0
        and exact_meaning_relation_count == 0
        and int(q79["canonical_promotion_allowed_count"]) == 0
        and int(q81["promoted_gloss_count"]) == 0
        and int(completion["promoted_gloss_count"]) == 0
        else "Q83_BENNA_C86_EXACT_SOURCE_AUDIT_REQUIRES_REVIEW"
    )
    payload = {
        "question": str(target["search_question"]),
        "answer": result_human_version,
        "acceptance_gate": str(target["acceptance_gate"]),
        "rejection_rule": str(target["rejection_rule"]),
        "next_action": "Keep Q82 T01 as shadow-only; execute Q82 T02 C86/VNCTIIN payload corridor next.",
        "blocked_use": "Do not promote BENNA, LTAST, TAILBETFTE, C86, or VNCTIIN as lexical words.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q83_benna_c86_exact_source_audit_v1_runs (
                created_at, decision, q82_run_id, q79_run_id, q81_run_id,
                completion_audit_run_id, target_id, target_book_count,
                web_query_count, web_exact_target_hit_count,
                official_exact_target_hit_count, source_check_count,
                method_support_source_count, exact_source_sequence_count,
                exact_meaning_relation_count, lexical_ready_count,
                direct_gloss_count, canonical_promotion_allowed_count,
                target_status, result_human_version, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                int(q82["run_id"]),
                int(q79["run_id"]),
                int(q81["run_id"]),
                int(completion["run_id"]),
                TARGET_ID,
                target_book_count,
                web_query_count,
                web_exact_target_hit_count,
                official_exact_target_hit_count,
                source_check_count,
                method_support_source_count,
                exact_source_sequence_count,
                exact_meaning_relation_count,
                lexical_ready_count,
                direct_gloss_count,
                canonical_promotion_allowed_count,
                target_status,
                result_human_version,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q83_benna_c86_exact_source_audit_v1_queries (
                run_id, query_id, query_text, result_status, notes, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (run_id, row["query_id"], row["query_text"], row["result_status"], row["notes"], j(row))
                for row in WEB_QUERIES
            ],
        )
        conn.executemany(
            """
            INSERT INTO human_q83_benna_c86_exact_source_audit_v1_sources (
                run_id, source_id, source_url, source_result,
                support_value, blocked_inference, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    row["source_id"],
                    row["source_url"],
                    row["source_result"],
                    row["support_value"],
                    row["blocked_inference"],
                    j(row),
                )
                for row in SOURCE_CHECKS
            ],
        )
        conn.executemany(
            """
            INSERT INTO human_q83_benna_c86_exact_source_audit_v1_books (
                run_id, bookid, symbol_text, likely_speech_act,
                plausible_human_reading, target_result, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    str(row["bookid"]),
                    str(row["symbol_text"]),
                    str(row["likely_speech_act"]),
                    str(row["plausible_human_reading"]),
                    "PRESERVE_STRUCTURAL_FORMULA_HANDOFF_SHADOW_ONLY",
                    j(dict(row)),
                )
                for row in books
            ],
        )
        conn.executemany(
            """
            INSERT INTO human_q83_benna_c86_exact_source_audit_v1_tests (
                run_id, test_id, test_result, interpretation, evidence_json
            ) VALUES (?, ?, ?, ?, ?)
            """,
            [
                (run_id, row["test_id"], row["test_result"], row["interpretation"], j(row))
                for row in TESTS
            ],
        )

    print(
        j(
            {
                "run_id": run_id,
                "decision": decision,
                "target_id": TARGET_ID,
                "target_book_count": target_book_count,
                "web_query_count": web_query_count,
                "web_exact_target_hit_count": web_exact_target_hit_count,
                "official_exact_target_hit_count": official_exact_target_hit_count,
                "source_check_count": source_check_count,
                "method_support_source_count": method_support_source_count,
                "exact_source_sequence_count": exact_source_sequence_count,
                "exact_meaning_relation_count": exact_meaning_relation_count,
                "lexical_ready_count": lexical_ready_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
            }
        )
    )


if __name__ == "__main__":
    main()
