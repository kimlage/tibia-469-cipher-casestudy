#!/usr/bin/env python3
"""Q88: exact-source audit for Q82 T07 Book7 phase/Mathemagica route."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
TARGET_ID = "Q82_T07_BOOK7_PHASE_MATHEMAGIC"

WEB_QUERIES = [
    {
        "query_id": "Q88_WEB_01",
        "query_text": '"ELBEEAEFTIINNEFIILEIITTNEIAAETTA"',
        "result_status": "NO_RELEVANT_EXACT_SOURCE_HIT",
        "notes": "No exact source hit for the Book7 phase string.",
    },
    {
        "query_id": "Q88_WEB_02",
        "query_text": '"TIINNEF" "NEIAAETTA" "Tibia"',
        "result_status": "NO_RELEVANT_EXACT_SOURCE_HIT",
        "notes": "No source ties TIINNEF/NEIAAETTA to a meaning or forced operator.",
    },
    {
        "query_id": "Q88_WEB_03",
        "query_text": '"ELBEEAEF" "TIINNEF"',
        "result_status": "NO_RELEVANT_EXACT_SOURCE_HIT",
        "notes": "No exact source hit for the Book7 opening component.",
    },
    {
        "query_id": "Q88_WEB_04",
        "query_text": '"NEIAAETTA" "PARADOX"',
        "result_status": "NO_RELEVANT_EXACT_SOURCE_HIT",
        "notes": "No Paradox-linked source for the Book7 component.",
    },
    {
        "query_id": "Q88_WEB_05",
        "query_text": '"ELBEEAEFTIINNEFIILEIITTNEIAAETTAAVNENIIFFEIEINTTIIILSBE"',
        "result_status": "NO_RELEVANT_EXACT_SOURCE_HIT",
        "notes": "No exact source hit for the full Book7 row0 text.",
    },
    {
        "query_id": "Q88_WEB_06",
        "query_text": 'site:tibia.com "TIINNEF"',
        "result_status": "NO_OFFICIAL_EXACT_HIT",
        "notes": "No official tibia.com exact hit for TIINNEF.",
    },
    {
        "query_id": "Q88_WEB_07",
        "query_text": 'site:tibiawiki.com.br "NEIAAETTA"',
        "result_status": "NO_WIKI_EXACT_TARGET_HIT",
        "notes": "No TibiaWiki BR exact target hit for NEIAAETTA.",
    },
    {
        "query_id": "Q88_WEB_08",
        "query_text": '"Book 7" "469" "TIINNEF"',
        "result_status": "NO_RELEVANT_EXACT_SOURCE_HIT",
        "notes": "No target source tying Book7/TIINNEF to a meaning relation.",
    },
]

SOURCE_CHECKS = [
    {
        "source_id": "Q4_BOOK7_PHASE_DIRECTION",
        "source_url": "sqlite:human_q4_book7_phase_direction_probe_v1_runs",
        "source_result": "PHASE_BRIDGE_CONFIRMED_DIRECTION_HELD_NO_GLOSS",
        "support_value": "Book7 combines TIINNEF and NEIAAETTA and survives local bridge/control tests.",
        "blocked_inference": "Direction and payload remain held; no Book7 sentence or component gloss.",
    },
    {
        "source_id": "Q8_BOOK6_7_3478_TRANSITION",
        "source_url": "sqlite:human_q8_book6_7_phase_path_3478_transition_probe_v1_runs",
        "source_result": "PHASE_PATH_SUPPORTED_NO_PAYLOAD_GLOSS",
        "support_value": "Book6->Book7 gains a 3478-window transition/control relation.",
        "blocked_inference": "3478, NEIAAETTA, TIINNEF, Book6, and Book7 are not translated as payload.",
    },
    {
        "source_id": "Q9_HELDOUT_SUPPORT_AUDIT",
        "source_url": "sqlite:human_q9_book6_7_heldout_support_audit_v1_runs",
        "source_result": "NO_HELDOUT_CONTIG_SUPPORT_KEEP_CONTROL_NO_GLOSS",
        "support_value": "Q9 preserves the transition as a local control after heldout checks.",
        "blocked_inference": "No independent contig, overlap, literal frontier, or similarity support promotes a sentence reading.",
    },
    {
        "source_id": "Q26_MATHEMAGIC_TRANSCRIPT_BRIDGE",
        "source_url": "sqlite:human_q26_mathemagic_transcript_bridge_import_v1_runs",
        "source_result": "OPERATOR_ONLY_NO_GLOSS",
        "support_value": "Exact transcript/imported sources support Mathemagica as an operator route.",
        "blocked_inference": "Mathemagica is not a plaintext dictionary or phrase translation.",
    },
    {
        "source_id": "Q27_MATHEMAGIC_OPERATOR_QUEUE",
        "source_url": "sqlite:human_q27_mathemagic_operator_queue_reconcile_v1_runs",
        "source_result": "OPERATORS_RECONCILED_NO_GLOSS",
        "support_value": "Four operator candidates are reconciled with one live-local and one weak-audit selector.",
        "blocked_inference": "No operator is promoted as a plaintext word or Book7 gloss.",
    },
    {
        "source_id": "HUMAN_MATHEMAGIC_SYNTHESIS",
        "source_url": "sqlite:human_mathemagic_shadow_synthesis_v1_runs",
        "source_result": "OPERATORS_NOT_PLAINTEXT",
        "support_value": "Mathemagic is retained as hypothesis machinery for operators, selectors, and frames.",
        "blocked_inference": "No accepted human gloss comes from Mathemagic alone.",
    },
    {
        "source_id": "Q31_BONELORD_TOME_3478_486486",
        "source_url": "sqlite:human_q31_bonelord_tome_provenance_bridge_v1_runs",
        "source_result": "QUESTION_ORACLE_FRAME_NO_COMPONENT_GLOSS",
        "support_value": "Bonelord Tome source ladder strengthens 3478/486486 as a phrase/oracle frame.",
        "blocked_inference": "No component gloss for 3478, 486486, or Book7 phase components.",
    },
    {
        "source_id": "AWB_469_LANGUAGE_MATHEMAGIC",
        "source_url": "https://tibia.fandom.com/wiki/A_Wrinkled_Bonelord/Transcripts",
        "source_result": "METHOD_SUPPORT_NO_BOOK7_SEQUENCE",
        "support_value": "AWB supports numeric/mathemagical processing as a method constraint.",
        "blocked_inference": "Does not identify TIINNEF, NEIAAETTA, 3478, or Book7 meaning.",
    },
    {
        "source_id": "PARADOX_MATHEMAGIC_OPERATOR_KEYS",
        "source_url": "https://www.tibia-wiki.net/wiki/Paradox_Tower_Quest/Spoiler",
        "source_result": "OPERATOR_KEY_SUPPORT_NO_BOOK7_SEQUENCE",
        "support_value": "Paradox/Mintwallin mathemagics supports context-dependent operator outputs.",
        "blocked_inference": "The 1/13/49/94 style keys do not provide a Book7 dictionary or phase payload.",
    },
    {
        "source_id": "TIBIASECRETS_HELLGATE_AVERAGE_ROUTE",
        "source_url": "https://www.tibiasecrets.com/article166",
        "source_result": "EXTERNAL_METHOD_PRESSURE_ONLY",
        "support_value": "The external 469 article supports non-trivial numeric/statistical pressure around Hellgate texts.",
        "blocked_inference": "External method pressure is not in-game anchoring and cannot promote a Book7 gloss.",
    },
]

TESTS = [
    {
        "test_id": "Q88_T01_WEB_EXACT_SEQUENCE",
        "test_result": "FAILS_EXACT_SOURCE_REQUIREMENT",
        "interpretation": "No web query found exact Book7 phase sequence plus meaning/provenance.",
    },
    {
        "test_id": "Q88_T02_BOOK7_LOCAL_BRIDGE",
        "test_result": "PRESERVE_LOCAL_BRIDGE_DIRECTION_HELD",
        "interpretation": "Book7 remains a phase-continuity bridge/control, but internal direction and payload stay held.",
    },
    {
        "test_id": "Q88_T03_MATHEMAGIC_OPERATOR_MODE",
        "test_result": "PRESERVE_OPERATOR_MODE_NO_DICTIONARY",
        "interpretation": "Mathemagica supports operator/selector search, not word substitution.",
    },
    {
        "test_id": "Q88_T04_3478_FRAME",
        "test_result": "PRESERVE_3478_ORACLE_FRAME_NO_COMPONENT_GLOSS",
        "interpretation": "3478/486486 can prioritize phrase-level tests, not Book7 component meanings.",
    },
    {
        "test_id": "Q88_T05_PROMOTION_FIREWALL",
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
        CREATE TABLE IF NOT EXISTS human_q88_book7_phase_mathemagic_exact_source_audit_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q82_run_id INTEGER NOT NULL,
            q4_run_id INTEGER NOT NULL,
            q8_run_id INTEGER NOT NULL,
            q9_run_id INTEGER NOT NULL,
            q26_run_id INTEGER NOT NULL,
            q27_run_id INTEGER NOT NULL,
            mathemagic_synthesis_run_id INTEGER NOT NULL,
            q31_run_id INTEGER NOT NULL,
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
            book7_bridge_support_count INTEGER NOT NULL,
            held_direction_count INTEGER NOT NULL,
            transition_signal_count INTEGER NOT NULL,
            heldout_positive_count INTEGER NOT NULL,
            mathemagic_operator_output_count INTEGER NOT NULL,
            live_local_operator_count INTEGER NOT NULL,
            exact_3478_phrase_source_count INTEGER NOT NULL,
            client_or_official_data_source_count INTEGER NOT NULL,
            lexical_ready_count INTEGER NOT NULL,
            direct_gloss_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            target_status TEXT NOT NULL,
            result_human_version TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q88_book7_phase_mathemagic_exact_source_audit_v1_queries (
            run_id INTEGER NOT NULL,
            query_id TEXT NOT NULL,
            query_text TEXT NOT NULL,
            result_status TEXT NOT NULL,
            notes TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, query_id)
        );

        CREATE TABLE IF NOT EXISTS human_q88_book7_phase_mathemagic_exact_source_audit_v1_sources (
            run_id INTEGER NOT NULL,
            source_id TEXT NOT NULL,
            source_url TEXT NOT NULL,
            source_result TEXT NOT NULL,
            support_value TEXT NOT NULL,
            blocked_inference TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, source_id)
        );

        CREATE TABLE IF NOT EXISTS human_q88_book7_phase_mathemagic_exact_source_audit_v1_books (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            symbol_text TEXT NOT NULL,
            likely_speech_act TEXT NOT NULL,
            plausible_human_reading TEXT NOT NULL,
            confidence_tier TEXT NOT NULL,
            target_result TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        );

        CREATE TABLE IF NOT EXISTS human_q88_book7_phase_mathemagic_exact_source_audit_v1_tests (
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
    q4 = latest_row(conn, "human_q4_book7_phase_direction_probe_v1_runs")
    q8 = latest_row(conn, "human_q8_book6_7_phase_path_3478_transition_probe_v1_runs")
    q9 = latest_row(conn, "human_q9_book6_7_heldout_support_audit_v1_runs")
    q26 = latest_row(conn, "human_q26_mathemagic_transcript_bridge_import_v1_runs")
    q27 = latest_row(conn, "human_q27_mathemagic_operator_queue_reconcile_v1_runs")
    mathemagic_synthesis = latest_row(conn, "human_mathemagic_shadow_synthesis_v1_runs")
    q31 = latest_row(conn, "human_q31_bonelord_tome_provenance_bridge_v1_runs")
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
    book7_bridge_support_count = int(q4["support_count"])
    held_direction_count = int(q4["held_direction_count"])
    transition_signal_count = int(q8["transition_signal_count"])
    heldout_positive_count = int(q9["heldout_positive_count"])
    mathemagic_operator_output_count = int(q26["mathemagic_operator_output_count"])
    live_local_operator_count = int(q27["live_local_operator_count"])
    exact_3478_phrase_source_count = int(q31["exact_3478_phrase_source_count"])
    client_or_official_data_source_count = int(q31["client_or_official_data_source_count"])
    lexical_ready_count = 0
    direct_gloss_count = 0
    canonical_promotion_allowed_count = 0
    target_status = "SOURCE_AUDITED_OPERATOR_SUPPORT_ONLY_NO_PROMOTION"
    result_human_version = (
        "Q88 preserves Book7 as a phase-continuity bridge/control supported by local 3478 contrast "
        "and Mathemagica as operator machinery. The route improves human search strategy, but no checked "
        "source provides the exact Book7 sequence with a source-provided meaning or forced value."
    )
    decision = (
        "Q88_BOOK7_PHASE_MATHEMAGIC_EXACT_SOURCE_AUDIT_OPERATOR_SUPPORT_NO_EXACT_SOURCE_NO_GLOSS"
        if target_book_count == 1
        and web_query_count == 8
        and web_exact_target_hit_count == 0
        and official_exact_target_hit_count == 0
        and source_check_count == 10
        and exact_source_sequence_count == 0
        and exact_meaning_relation_count == 0
        and book7_bridge_support_count >= 1
        and held_direction_count >= 1
        and transition_signal_count == 1
        and heldout_positive_count == 0
        and mathemagic_operator_output_count == 4
        and live_local_operator_count == 1
        and exact_3478_phrase_source_count >= 2
        and client_or_official_data_source_count == 0
        and int(q81["promoted_gloss_count"]) == 0
        and int(completion["promoted_gloss_count"]) == 0
        else "Q88_BOOK7_PHASE_MATHEMAGIC_EXACT_SOURCE_AUDIT_REQUIRES_REVIEW"
    )
    payload = {
        "question": str(target["search_question"]),
        "answer": result_human_version,
        "acceptance_gate": str(target["acceptance_gate"]),
        "rejection_rule": str(target["rejection_rule"]),
        "operator_route": "Use Mathemagica to search selector/fase rules, not word meanings.",
        "next_action": "Generate a source-anchored human synthesis that ranks Q87 R02/NAESE, Q88 Book7/Mathemagica, and Q80 packet as separate reading routes.",
        "blocked_use": "Do not translate Book7, 3478, NEIAAETTA, TIINNEF, Mathemagica keys, or Paradox outputs as words.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q88_book7_phase_mathemagic_exact_source_audit_v1_runs (
                created_at, decision, q82_run_id, q4_run_id, q8_run_id,
                q9_run_id, q26_run_id, q27_run_id,
                mathemagic_synthesis_run_id, q31_run_id,
                q81_run_id, completion_audit_run_id, target_id,
                target_book_count, web_query_count, web_exact_target_hit_count,
                official_exact_target_hit_count, source_check_count,
                method_support_source_count, exact_source_sequence_count,
                exact_meaning_relation_count, book7_bridge_support_count,
                held_direction_count, transition_signal_count,
                heldout_positive_count, mathemagic_operator_output_count,
                live_local_operator_count, exact_3478_phrase_source_count,
                client_or_official_data_source_count, lexical_ready_count,
                direct_gloss_count, canonical_promotion_allowed_count,
                target_status, result_human_version, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                int(q82["run_id"]),
                int(q4["run_id"]),
                int(q8["run_id"]),
                int(q9["run_id"]),
                int(q26["run_id"]),
                int(q27["run_id"]),
                int(mathemagic_synthesis["run_id"]),
                int(q31["run_id"]),
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
                book7_bridge_support_count,
                held_direction_count,
                transition_signal_count,
                heldout_positive_count,
                mathemagic_operator_output_count,
                live_local_operator_count,
                exact_3478_phrase_source_count,
                client_or_official_data_source_count,
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
            INSERT INTO human_q88_book7_phase_mathemagic_exact_source_audit_v1_queries (
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
            INSERT INTO human_q88_book7_phase_mathemagic_exact_source_audit_v1_sources (
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
            INSERT INTO human_q88_book7_phase_mathemagic_exact_source_audit_v1_books (
                run_id, bookid, symbol_text, likely_speech_act,
                plausible_human_reading, confidence_tier, target_result, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    str(row["bookid"]),
                    str(row["symbol_text"]),
                    str(row["likely_speech_act"]),
                    str(row["plausible_human_reading"]),
                    str(row["confidence_tier"]),
                    "PRESERVE_BOOK7_PHASE_MATHEMAGIC_SHADOW_ONLY",
                    j(dict(row)),
                )
                for row in books
            ],
        )
        conn.executemany(
            """
            INSERT INTO human_q88_book7_phase_mathemagic_exact_source_audit_v1_tests (
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
                "book7_bridge_support_count": book7_bridge_support_count,
                "held_direction_count": held_direction_count,
                "transition_signal_count": transition_signal_count,
                "heldout_positive_count": heldout_positive_count,
                "mathemagic_operator_output_count": mathemagic_operator_output_count,
                "live_local_operator_count": live_local_operator_count,
                "exact_3478_phrase_source_count": exact_3478_phrase_source_count,
                "client_or_official_data_source_count": client_or_official_data_source_count,
                "lexical_ready_count": lexical_ready_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
            }
        )
    )


if __name__ == "__main__":
    main()
