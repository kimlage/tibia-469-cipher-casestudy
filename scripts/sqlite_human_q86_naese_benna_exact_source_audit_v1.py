#!/usr/bin/env python3
"""Q86: execute exact-source audit for Q82 T03 NAESE/BENNA composite."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
TARGET_ID = "Q82_T03_NAESE_BENNA_COMPOSITE"

WEB_QUERIES = [
    {
        "query_id": "Q86_WEB_01",
        "query_text": '"NAESESTIENFATCTIVVTISETEIVIFAST"',
        "result_status": "NO_RELEVANT_EXACT_SOURCE_HIT",
        "notes": "No exact source hit for the NAESE/C68 slot fragment.",
    },
    {
        "query_id": "Q86_WEB_02",
        "query_text": '"FATCTIVVTISETEIVIFAST" "BENNA"',
        "result_status": "NO_RELEVANT_EXACT_SOURCE_HIT",
        "notes": "No exact source linking the slot tail to BENNA.",
    },
    {
        "query_id": "Q86_WEB_03",
        "query_text": '"NAESE" "BENNA" "Tibia"',
        "result_status": "FALSE_POSITIVES_NO_TARGET_SOURCE",
        "notes": "Returns unrelated/generated-name false positives, not Tibia target evidence.",
    },
    {
        "query_id": "Q86_WEB_04",
        "query_text": '"ILSBEIINIAVNALLBEEILEEIEFFIFTLEITELBENNA"',
        "result_status": "NO_RELEVANT_EXACT_SOURCE_HIT",
        "notes": "No exact composite bridge source hit.",
    },
    {
        "query_id": "Q86_WEB_05",
        "query_text": '"SEEIISETBASEFAIFVI"',
        "result_status": "NO_RELEVANT_EXACT_SOURCE_HIT",
        "notes": "No exact source hit for Book5 prefix.",
    },
    {
        "query_id": "Q86_WEB_06",
        "query_text": '"IVIFASTFNEIEINTAAETTAEFTEI"',
        "result_status": "NO_RELEVANT_EXACT_SOURCE_HIT",
        "notes": "No exact source hit for shared NAESE slot continuation.",
    },
    {
        "query_id": "Q86_WEB_07",
        "query_text": 'site:tibia.com "NAESE"',
        "result_status": "NO_OFFICIAL_EXACT_HIT",
        "notes": "No official tibia.com exact hit for NAESE.",
    },
    {
        "query_id": "Q86_WEB_08",
        "query_text": 'site:tibiawiki.com.br "NAESESTIENFATCT"',
        "result_status": "NO_WIKI_EXACT_TARGET_HIT",
        "notes": "No TibiaWiki BR exact hit for NAESESTIENFATCT.",
    },
]

SOURCE_CHECKS = [
    {
        "source_id": "Q75_C68_NAESE_SOURCE_CHECK",
        "source_url": "sqlite:human_q75_c68_naese_exact_source_check_v1_sources",
        "source_result": "NAESE_SLOT_FUNCTIONAL_ONLY_NO_EXACT_GLOSS",
        "support_value": "Q75 checked Threat III, Paradox, and s2ward/method pressure for C68/NAESE.",
        "blocked_inference": "No source provides exact C68/NAESE sequence, slot value, or lexical support.",
    },
    {
        "source_id": "Q68_BENNA_MATHEMAGIC_SOURCE_CHECK",
        "source_url": "sqlite:human_q68_benna_mathemagic_operator_check_v1_sources",
        "source_result": "BENNA_METHOD_SUPPORT_ONLY_NO_EXACT_GLOSS",
        "support_value": "Q68 checked AWB, Beware, and Paradox for BENNA/operator support.",
        "blocked_inference": "No source provides exact BENNA sequence, operator rule, or lexical support.",
    },
    {
        "source_id": "AWB_469_LANGUAGE_MATHEMAGIC",
        "source_url": "https://tibia.fandom.com/wiki/A_Wrinkled_Bonelord/Transcripts",
        "source_result": "METHOD_SUPPORT_NO_COMPOSITE_SEQUENCE",
        "support_value": "AWB supports mathemagical/numeric processing as the right method family.",
        "blocked_inference": "Does not identify NAESE/BENNA composite flow or a meaning relation.",
    },
    {
        "source_id": "HONEMINAS_FORMULA_PARALLEL",
        "source_url": "https://www.tibiawiki.com.br/Honeminas_Formula",
        "source_result": "FORMULA_MODE_SUPPORT_NO_COMPOSITE_LINK",
        "support_value": "Honeminas supports formulaic language as an in-game discourse mode.",
        "blocked_inference": "No link from Honeminas formula to NAESE/BENNA composite target.",
    },
    {
        "source_id": "THREAT_III_MIND_BODY_SOUL_EXPERIMENTS",
        "source_url": "https://www.tibiawiki.com.br/wiki/The_Bonelord_Threat_III_%28Book%29",
        "source_result": "TRANSFORMATION_REGISTER_SUPPORT_NO_COMPOSITE_SEQUENCE",
        "support_value": "Threat III supports transformation/slot/payload register.",
        "blocked_inference": "Does not map NAESE/C68/BENNA to soul, mind, body, monster, or formula semantics.",
    },
]

TESTS = [
    {
        "test_id": "Q86_T01_WEB_EXACT_SEQUENCE",
        "test_result": "FAILS_EXACT_SOURCE_REQUIREMENT",
        "interpretation": "No web query found exact NAESE/BENNA composite sequence plus meaning/provenance.",
    },
    {
        "test_id": "Q86_T02_PRIOR_NAESE_AND_BENNA_FIREWALL",
        "test_result": "PRESERVE_Q75_Q68_NO_EXACT_GLOSS",
        "interpretation": "Q75 and Q68 already block NAESE and BENNA lexical promotion independently.",
    },
    {
        "test_id": "Q86_T03_COMPOSITE_STATUS",
        "test_result": "PRESERVE_COMPOSITE_SHADOW_ONLY",
        "interpretation": "Books 5/9 remain slot-to-formula composite shadows, not prose.",
    },
    {
        "test_id": "Q86_T04_PROMOTION_FIREWALL",
        "test_result": "PASSES_BLOCK_PROMOTION",
        "interpretation": "Completion audit keeps promoted_gloss_count at zero.",
    },
]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q86_naese_benna_exact_source_audit_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q82_run_id INTEGER NOT NULL,
            q75_run_id INTEGER NOT NULL,
            q68_run_id INTEGER NOT NULL,
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
            slot_mechanical_value_count INTEGER NOT NULL,
            benna_operator_rule_count INTEGER NOT NULL,
            lexical_ready_count INTEGER NOT NULL,
            direct_gloss_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            target_status TEXT NOT NULL,
            result_human_version TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q86_naese_benna_exact_source_audit_v1_queries (
            run_id INTEGER NOT NULL,
            query_id TEXT NOT NULL,
            query_text TEXT NOT NULL,
            result_status TEXT NOT NULL,
            notes TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, query_id)
        );

        CREATE TABLE IF NOT EXISTS human_q86_naese_benna_exact_source_audit_v1_sources (
            run_id INTEGER NOT NULL,
            source_id TEXT NOT NULL,
            source_url TEXT NOT NULL,
            source_result TEXT NOT NULL,
            support_value TEXT NOT NULL,
            blocked_inference TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, source_id)
        );

        CREATE TABLE IF NOT EXISTS human_q86_naese_benna_exact_source_audit_v1_books (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            symbol_text TEXT NOT NULL,
            likely_speech_act TEXT NOT NULL,
            plausible_human_reading TEXT NOT NULL,
            target_result TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        );

        CREATE TABLE IF NOT EXISTS human_q86_naese_benna_exact_source_audit_v1_tests (
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
    q75 = latest_row(conn, "human_q75_c68_naese_exact_source_check_v1_runs")
    q68 = latest_row(conn, "human_q68_benna_mathemagic_operator_check_v1_runs")
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
    slot_mechanical_value_count = int(q75["slot_mechanical_value_count"])
    benna_operator_rule_count = int(q68["repeatable_operator_rule_count"])
    lexical_ready_count = 0
    direct_gloss_count = 0
    canonical_promotion_allowed_count = 0
    target_status = "SOURCE_AUDITED_METHOD_SUPPORT_ONLY_NO_PROMOTION"
    result_human_version = (
        "Q86 finds no exact source for the NAESE/BENNA composite. Books 5/9 remain useful as "
        "slot-to-formula composite shadows, but prior Q75/Q68 gates still block NAESE, C68, and BENNA "
        "as lexical or mechanical values."
    )
    decision = (
        "Q86_NAESE_BENNA_EXACT_SOURCE_AUDIT_METHOD_SUPPORT_NO_EXACT_SOURCE_NO_GLOSS"
        if target_book_count == 2
        and web_query_count == 8
        and web_exact_target_hit_count == 0
        and official_exact_target_hit_count == 0
        and source_check_count == 5
        and exact_source_sequence_count == 0
        and exact_meaning_relation_count == 0
        and slot_mechanical_value_count == 0
        and benna_operator_rule_count == 0
        and int(q75["lexical_ready_count"]) == 0
        and int(q68["lexical_ready_count"]) == 0
        and int(q81["promoted_gloss_count"]) == 0
        and int(completion["promoted_gloss_count"]) == 0
        else "Q86_NAESE_BENNA_EXACT_SOURCE_AUDIT_REQUIRES_REVIEW"
    )
    payload = {
        "question": str(target["search_question"]),
        "answer": result_human_version,
        "acceptance_gate": str(target["acceptance_gate"]),
        "rejection_rule": str(target["rejection_rule"]),
        "next_action": "Keep Q82 T03 as high-value shadow; execute Q82 T04 R02/NAESE slot bridge next.",
        "blocked_use": "Do not promote NAESE, C68, FATCT, IVIFAST, BENNA, formula, or slot as lexical words.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q86_naese_benna_exact_source_audit_v1_runs (
                created_at, decision, q82_run_id, q75_run_id, q68_run_id,
                q81_run_id, completion_audit_run_id, target_id,
                target_book_count, web_query_count, web_exact_target_hit_count,
                official_exact_target_hit_count, source_check_count,
                method_support_source_count, exact_source_sequence_count,
                exact_meaning_relation_count, slot_mechanical_value_count,
                benna_operator_rule_count, lexical_ready_count, direct_gloss_count,
                canonical_promotion_allowed_count, target_status,
                result_human_version, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                int(q82["run_id"]),
                int(q75["run_id"]),
                int(q68["run_id"]),
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
                slot_mechanical_value_count,
                benna_operator_rule_count,
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
            INSERT INTO human_q86_naese_benna_exact_source_audit_v1_queries (
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
            INSERT INTO human_q86_naese_benna_exact_source_audit_v1_sources (
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
            INSERT INTO human_q86_naese_benna_exact_source_audit_v1_books (
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
                    "PRESERVE_NAESE_BENNA_COMPOSITE_SHADOW_ONLY",
                    j(dict(row)),
                )
                for row in books
            ],
        )
        conn.executemany(
            """
            INSERT INTO human_q86_naese_benna_exact_source_audit_v1_tests (
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
                "slot_mechanical_value_count": slot_mechanical_value_count,
                "benna_operator_rule_count": benna_operator_rule_count,
                "lexical_ready_count": lexical_ready_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
            }
        )
    )


if __name__ == "__main__":
    main()
