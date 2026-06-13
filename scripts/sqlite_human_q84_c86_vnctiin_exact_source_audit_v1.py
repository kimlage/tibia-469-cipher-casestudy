#!/usr/bin/env python3
"""Q84: execute exact-source audit for Q82 T02 C86/VNCTIIN payload corridor."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
TARGET_ID = "Q82_T02_C86_VNCTIIN_PAYLOAD_CORRIDOR"

WEB_QUERIES = [
    {
        "query_id": "Q84_WEB_01",
        "query_text": '"CEVIEFIINI" "Tibia"',
        "result_status": "NO_RELEVANT_EXACT_SOURCE_HIT",
        "notes": "No public exact source for the Book2/67 CEVIEFIINI fragment.",
    },
    {
        "query_id": "Q84_WEB_02",
        "query_text": '"VNCTIINNVETTAFSETBASEFAIFVI"',
        "result_status": "NO_RELEVANT_EXACT_SOURCE_HIT",
        "notes": "No public exact source for the Book2/67 VNCTIIN continuation fragment.",
    },
    {
        "query_id": "Q84_WEB_03",
        "query_text": '"ICEVIEFIINI" "VNCTIIN"',
        "result_status": "NO_RELEVANT_EXACT_SOURCE_HIT",
        "notes": "No exact source hit for the Book27/67 handoff fragment.",
    },
    {
        "query_id": "Q84_WEB_04",
        "query_text": '"NAESESTIENFATCTIVVTISETEIVIFAST"',
        "result_status": "NO_RELEVANT_EXACT_SOURCE_HIT",
        "notes": "No exact source hit for the Book2 NAESE/C68 slot fragment.",
    },
    {
        "query_id": "Q84_WEB_05",
        "query_text": '"C86" "VNCTIIN" "Bonelord"',
        "result_status": "NO_RELEVANT_EXACT_SOURCE_HIT",
        "notes": "No source binds C86/VNCTIIN to payload/context meaning.",
    },
    {
        "query_id": "Q84_WEB_06",
        "query_text": '"VNCTIIN" "Tibia"',
        "result_status": "NO_PROMOTABLE_TARGET_RELATION",
        "notes": "No target-level source relation found.",
    },
    {
        "query_id": "Q84_WEB_07",
        "query_text": 'site:tibia.com "VNCTIIN"',
        "result_status": "NO_OFFICIAL_EXACT_HIT",
        "notes": "No official tibia.com exact hit for VNCTIIN.",
    },
    {
        "query_id": "Q84_WEB_08",
        "query_text": 'site:tibiawiki.com.br "CEVIEFIINI"',
        "result_status": "NO_WIKI_EXACT_TARGET_HIT",
        "notes": "No TibiaWiki BR exact hit for CEVIEFIINI.",
    },
]

SOURCE_CHECKS = [
    {
        "source_id": "THREAT_I_EYESTALK_MAGIC_COMMAND_DEAD",
        "source_url": "https://www.tibiawiki.com.br/wiki/The_Bonelord_Threat_I_%28Book%29",
        "source_result": "COMMAND_REGISTER_SUPPORT_NO_TARGET_SEQUENCE",
        "support_value": "Threat I supports command/control/necromancy register for Bonelords.",
        "blocked_inference": "Does not mention C86, VNCTIIN, CEVIEFIINI, TAILBETFTE, or a payload/context value.",
    },
    {
        "source_id": "THREAT_II_RESEARCH_EXPERIMENTS",
        "source_url": "https://tibia.fandom.com/wiki/The_Bonelord_Threat_II_%28Book%29",
        "source_result": "RESEARCH_REGISTER_SUPPORT_NO_TARGET_SEQUENCE",
        "support_value": "Threat II supports research/experiment register for Bonelord attempts to improve powers.",
        "blocked_inference": "Does not provide C86/VNCTIIN sequence support or a context-route value.",
    },
    {
        "source_id": "THREAT_III_MIND_BODY_SOUL_EXPERIMENTS",
        "source_url": "https://www.tibiawiki.com.br/wiki/The_Bonelord_Threat_III_%28Book%29",
        "source_result": "TRANSFORMATION_REGISTER_SUPPORT_NO_TARGET_SEQUENCE",
        "support_value": "Threat III supports transformation/payload register around souls, minds, bodies, dead and living.",
        "blocked_inference": "Does not map C86/VNCTIIN, NAESE, or TAILBETFTE to soul/body/command semantics.",
    },
    {
        "source_id": "AWB_469_LANGUAGE_MATHEMAGIC",
        "source_url": "https://tibia.fandom.com/wiki/A_Wrinkled_Bonelord/Transcripts",
        "source_result": "METHOD_SUPPORT_NO_TARGET_SEQUENCE",
        "support_value": "AWB links 469 to numbers and mathemagical processing.",
        "blocked_inference": "Does not identify C86/VNCTIIN or the Book2/27/67 corridor.",
    },
    {
        "source_id": "BEWARE_LANGUAGE_MATH_NUMERIC_BOOKS",
        "source_url": "https://tibia.fandom.com/wiki/Beware_of_the_Bonelords_%28Book%29",
        "source_result": "LANGUAGE_REGISTER_SUPPORT_NO_TARGET_SEQUENCE",
        "support_value": "Beware supports numeric/mathematical Bonelord language and complex numeric books.",
        "blocked_inference": "Does not provide the exact C86/VNCTIIN sequence or meaning.",
    },
]

TESTS = [
    {
        "test_id": "Q84_T01_WEB_EXACT_SEQUENCE",
        "test_result": "FAILS_EXACT_SOURCE_REQUIREMENT",
        "interpretation": "No web query found exact C86/VNCTIIN sequence plus meaning/provenance.",
    },
    {
        "test_id": "Q84_T02_THREAT_REGISTER_FIREWALL",
        "test_result": "PASSES_REGISTER_SUPPORT_ONLY",
        "interpretation": "Threat I/II/III support command/research/transformation register only.",
    },
    {
        "test_id": "Q84_T03_Q76_PRIOR_RESULT_PRESERVED",
        "test_result": "PRESERVE_Q76_NO_EXACT_GLOSS",
        "interpretation": "Q76 already found zero exact C86/VNCTIIN source and zero context-route mechanical value.",
    },
    {
        "test_id": "Q84_T04_PROMOTION_FIREWALL",
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
        CREATE TABLE IF NOT EXISTS human_q84_c86_vnctiin_exact_source_audit_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q82_run_id INTEGER NOT NULL,
            q76_run_id INTEGER NOT NULL,
            q79_run_id INTEGER NOT NULL,
            q81_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            target_id TEXT NOT NULL,
            target_book_count INTEGER NOT NULL,
            web_query_count INTEGER NOT NULL,
            web_exact_target_hit_count INTEGER NOT NULL,
            official_exact_target_hit_count INTEGER NOT NULL,
            source_check_count INTEGER NOT NULL,
            register_support_source_count INTEGER NOT NULL,
            exact_source_sequence_count INTEGER NOT NULL,
            exact_meaning_relation_count INTEGER NOT NULL,
            context_route_mechanical_value_count INTEGER NOT NULL,
            lexical_ready_count INTEGER NOT NULL,
            direct_gloss_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            target_status TEXT NOT NULL,
            result_human_version TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q84_c86_vnctiin_exact_source_audit_v1_queries (
            run_id INTEGER NOT NULL,
            query_id TEXT NOT NULL,
            query_text TEXT NOT NULL,
            result_status TEXT NOT NULL,
            notes TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, query_id)
        );

        CREATE TABLE IF NOT EXISTS human_q84_c86_vnctiin_exact_source_audit_v1_sources (
            run_id INTEGER NOT NULL,
            source_id TEXT NOT NULL,
            source_url TEXT NOT NULL,
            source_result TEXT NOT NULL,
            support_value TEXT NOT NULL,
            blocked_inference TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, source_id)
        );

        CREATE TABLE IF NOT EXISTS human_q84_c86_vnctiin_exact_source_audit_v1_books (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            symbol_text TEXT NOT NULL,
            likely_speech_act TEXT NOT NULL,
            plausible_human_reading TEXT NOT NULL,
            target_result TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        );

        CREATE TABLE IF NOT EXISTS human_q84_c86_vnctiin_exact_source_audit_v1_tests (
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
    q76 = latest_row(conn, "human_q76_c86_vnctiin_command_control_check_v1_runs")
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
    register_support_source_count = len(SOURCE_CHECKS)
    exact_source_sequence_count = 0
    exact_meaning_relation_count = 0
    context_route_mechanical_value_count = int(q76["context_route_mechanical_value_count"])
    lexical_ready_count = 0
    direct_gloss_count = 0
    canonical_promotion_allowed_count = 0
    target_status = "SOURCE_AUDITED_REGISTER_SUPPORT_ONLY_NO_PROMOTION"
    result_human_version = (
        "Q84 finds no exact source for the C86/VNCTIIN payload corridor. Threat I/II/III, AWB, "
        "and Beware support command/research/transformation/numeric-language register, but no source "
        "gives the exact Book2/27/67 sequences or a payload/context meaning relation."
    )
    decision = (
        "Q84_C86_VNCTIIN_EXACT_SOURCE_AUDIT_REGISTER_SUPPORT_NO_EXACT_SOURCE_NO_GLOSS"
        if target_book_count == 3
        and web_query_count == 8
        and web_exact_target_hit_count == 0
        and official_exact_target_hit_count == 0
        and source_check_count == 5
        and exact_source_sequence_count == 0
        and exact_meaning_relation_count == 0
        and context_route_mechanical_value_count == 0
        and int(q76["lexical_ready_count"]) == 0
        and int(q79["canonical_promotion_allowed_count"]) == 0
        and int(q81["promoted_gloss_count"]) == 0
        and int(completion["promoted_gloss_count"]) == 0
        else "Q84_C86_VNCTIIN_EXACT_SOURCE_AUDIT_REQUIRES_REVIEW"
    )
    payload = {
        "question": str(target["search_question"]),
        "answer": result_human_version,
        "acceptance_gate": str(target["acceptance_gate"]),
        "rejection_rule": str(target["rejection_rule"]),
        "next_action": "Keep Q82 T02 as register-supported shadow only; synthesize Q83+Q84 impact on Q80 packet.",
        "blocked_use": "Do not promote C86, VNCTIIN, TAILBETFTE, NAESE, payload, or context as lexical words.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q84_c86_vnctiin_exact_source_audit_v1_runs (
                created_at, decision, q82_run_id, q76_run_id, q79_run_id,
                q81_run_id, completion_audit_run_id, target_id,
                target_book_count, web_query_count, web_exact_target_hit_count,
                official_exact_target_hit_count, source_check_count,
                register_support_source_count, exact_source_sequence_count,
                exact_meaning_relation_count, context_route_mechanical_value_count,
                lexical_ready_count, direct_gloss_count,
                canonical_promotion_allowed_count, target_status,
                result_human_version, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                int(q82["run_id"]),
                int(q76["run_id"]),
                int(q79["run_id"]),
                int(q81["run_id"]),
                int(completion["run_id"]),
                TARGET_ID,
                target_book_count,
                web_query_count,
                web_exact_target_hit_count,
                official_exact_target_hit_count,
                source_check_count,
                register_support_source_count,
                exact_source_sequence_count,
                exact_meaning_relation_count,
                context_route_mechanical_value_count,
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
            INSERT INTO human_q84_c86_vnctiin_exact_source_audit_v1_queries (
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
            INSERT INTO human_q84_c86_vnctiin_exact_source_audit_v1_sources (
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
            INSERT INTO human_q84_c86_vnctiin_exact_source_audit_v1_books (
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
                    "PRESERVE_C86_VNCTIIN_PAYLOAD_CORRIDOR_SHADOW_ONLY",
                    j(dict(row)),
                )
                for row in books
            ],
        )
        conn.executemany(
            """
            INSERT INTO human_q84_c86_vnctiin_exact_source_audit_v1_tests (
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
                "register_support_source_count": register_support_source_count,
                "exact_source_sequence_count": exact_source_sequence_count,
                "exact_meaning_relation_count": exact_meaning_relation_count,
                "context_route_mechanical_value_count": context_route_mechanical_value_count,
                "lexical_ready_count": lexical_ready_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
            }
        )
    )


if __name__ == "__main__":
    main()
