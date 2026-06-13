#!/usr/bin/env python3
"""Q90: exact-source audit for Q82 T05 Book49/math49 register route."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
TARGET_ID = "Q82_T05_BOOK49_MATH49_REGISTER"

WEB_QUERIES = [
    {
        "query_id": "Q90_WEB_01",
        "query_text": '"IAENNEENINOEENEEILEENEENINFEEILEIILEEEEILEENEEINFEFFTENEEINF"',
        "result_status": "NO_RELEVANT_EXACT_SOURCE_HIT",
        "notes": "No exact web hit for the full Book49 row0 text.",
    },
    {
        "query_id": "Q90_WEB_02",
        "query_text": '"IAENNEEN" "Tibia"',
        "result_status": "NO_RELEVANT_EXACT_SOURCE_HIT",
        "notes": "No exact in-game/source hit for the Book49 opening component.",
    },
    {
        "query_id": "Q90_WEB_03",
        "query_text": '"NEEN" "IAEN" "469"',
        "result_status": "NO_TARGET_SOURCE_HIT",
        "notes": "No Book49 source relation; generic/noisy matches only.",
    },
    {
        "query_id": "Q90_WEB_04",
        "query_text": '"Book 49" "469" "Tibia"',
        "result_status": "NO_EXACT_BOOK49_SEQUENCE_MEANING",
        "notes": "Finds broad 469 discussions, not an exact Book49 sequence plus meaning.",
    },
    {
        "query_id": "Q90_WEB_05",
        "query_text": '"1 + 1 = 49" "A Prisoner" Tibia',
        "result_status": "MATHEMAGIC_49_SOURCE_ONLY",
        "notes": "A Prisoner transcript supports 49 as a Mathemagica output, not a Book49 gloss.",
    },
    {
        "query_id": "Q90_WEB_06",
        "query_text": '"49" "Bonelord" "Great Calculator"',
        "result_status": "METHOD_PRESSURE_NO_BOOK49_MEANING",
        "notes": "Great Calculator references support assembled-language/method pressure only.",
    },
    {
        "query_id": "Q90_WEB_07",
        "query_text": 'site:tibia.com "IAENNEEN"',
        "result_status": "NO_OFFICIAL_EXACT_HIT",
        "notes": "No official tibia.com exact hit for IAENNEEN.",
    },
    {
        "query_id": "Q90_WEB_08",
        "query_text": 'site:tibiawiki.com.br "IAENNEEN"',
        "result_status": "NO_WIKI_EXACT_TARGET_HIT",
        "notes": "No TibiaWiki BR exact Book49 target hit.",
    },
]

SOURCE_CHECKS = [
    {
        "source_id": "BOOK49_SELFCONTAINMENT_GATE",
        "source_url": "sqlite:book49_selfcontainment_gate_runs",
        "source_result": "SELF_CONTAINED_REPEAT_FORMULA_AUDIT_SAFE",
        "support_value": "Book49 has repeated-token coverage 0.85 and an audit-safe self-contained repeat tag.",
        "blocked_inference": "Functional repeat/register tag only; no word, sentence, spell, chant, calibration, or reset gloss.",
    },
    {
        "source_id": "BOOK49_REPEAT_SHADOW",
        "source_url": "sqlite:human_book49_repeat_shadow_probe_v1_runs",
        "source_result": "BOOK49_REPEAT_SHADOW_SUPPORTED_NO_GLOSS",
        "support_value": "Book49 is repeat-rank 1; Book55 is the main repeat control.",
        "blocked_inference": "Repeat rank does not make the line narrative prose or a 49 dictionary key.",
    },
    {
        "source_id": "BOOK49_RESIDUAL_NEGATIVE",
        "source_url": "sqlite:book49_residual_negative_probe_runs",
        "source_result": "BOOK49_RESIDUAL_AUDIT_ONLY_NO_GLOSS",
        "support_value": "Book49 residual motifs exist, but controls also hit across other books.",
        "blocked_inference": "O32/NEEI/residual components stay audit-only and cannot become words.",
    },
    {
        "source_id": "Q3_BOOK49_REGISTER_FUNCTION",
        "source_url": "sqlite:human_q3_book49_register_function_probe_v1_runs",
        "source_result": "CONTROL_ONLY_CALIBRATION_RESET_NOT_SUPPORTED",
        "support_value": "Book49 can be a self-contained repeat/register formula and selector/control witness.",
        "blocked_inference": "No calibration context and no operator-reset context support.",
    },
    {
        "source_id": "MATHEMAGIC_PLUS49_WIDE_FRONTIER",
        "source_url": "sqlite:mathemagic_plus49_wide_frontier_probe_v1_runs",
        "source_result": "PLUS49_SELECTOR_AUDIT_ONLY",
        "support_value": "+49/mod70 ranked first in one wide frontier audit with two best-anchor hits.",
        "blocked_inference": "+49 remains a structural selector only and does not become Book49 meaning.",
    },
    {
        "source_id": "MATHEMAGIC_PLUS49_RANK13_HOLDOUT",
        "source_url": "sqlite:mathemagic_plus49_rank13_holdout_v1_runs",
        "source_result": "PLUS49_FAILS_HOLDOUT_DEMOTE_TO_AUDIT_ONLY",
        "support_value": "+49 fails rank13 holdout with zero plus49 best-anchor hits.",
        "blocked_inference": "Do not use +49 as a general decoding key or prose rule.",
    },
    {
        "source_id": "MATHEMAGIC_49_94_WINDOW",
        "source_url": "sqlite:mathemagic_49_94_window_probe_v1_runs",
        "source_result": "REJECT_CONTROLS_TIE_OR_BEAT",
        "support_value": "49/94 window target score is beaten by control_50.",
        "blocked_inference": "49/94 windows cannot promote a Book49 operator meaning.",
    },
    {
        "source_id": "MATHEMAGIC_BOOK_MOD70_SENTINEL",
        "source_url": "sqlite:mathemagic_book_mod70_sentinel_v1_runs",
        "source_result": "AUDIT_ONLY_O32_GUARDRAIL_NO_SELECTOR_PROMOTION",
        "support_value": "Book/mod70 sentinel stays audit-only with O32 guardrail.",
        "blocked_inference": "No mod70 selector promotion for Book49.",
    },
    {
        "source_id": "Q26_MATHEMAGIC_TRANSCRIPT_BRIDGE",
        "source_url": "sqlite:human_q26_mathemagic_transcript_bridge_import_v1_runs",
        "source_result": "OPERATOR_ONLY_NO_GLOSS",
        "support_value": "Transcripts support Mathemagica as operator route with four outputs.",
        "blocked_inference": "Mathemagica is not a plaintext dictionary or Book49 phrase translation.",
    },
    {
        "source_id": "Q27_MATHEMAGIC_OPERATOR_QUEUE",
        "source_url": "sqlite:human_q27_mathemagic_operator_queue_reconcile_v1_runs",
        "source_result": "OPERATORS_RECONCILED_NO_GLOSS",
        "support_value": "Operator candidates are live/weak/dead/untested, but no plaintext allowed.",
        "blocked_inference": "No operator is promoted as a word or Book49 gloss.",
    },
    {
        "source_id": "A_PRISONER_MATHEMAGICS_TRANSCRIPT",
        "source_url": "https://tibia.fandom.com/wiki/A_Prisoner/Transcripts",
        "source_result": "INGAME_TRANSCRIPT_1_PLUS_1_49_NO_BOOK49_LINK",
        "support_value": "A Prisoner transcript explicitly includes 1 + 1 = 49 as one Mathemagica output.",
        "blocked_inference": "The transcript does not mention Book49, IAEN/NEEN, repeat registers, or a 469 book meaning.",
    },
    {
        "source_id": "PARADOX_TOWER_QUEST_SPOILER",
        "source_url": "https://www.tibia-wiki.net/wiki/Paradox_Tower_Quest/Spoiler",
        "source_result": "QUEST_CONTEXT_SUPPORT_NO_BOOK49_LINK",
        "support_value": "Paradox route gives the Mathemagica lesson context and the prisoner number step.",
        "blocked_inference": "Quest walkthrough context is not a Book49 source or forced value.",
    },
    {
        "source_id": "S2WARD_GREAT_CALCULATOR_CORPUS",
        "source_url": "https://github.com/s2ward/469",
        "source_result": "EXTERNAL_CORPUS_METHOD_SUPPORT_ONLY",
        "support_value": "External corpus work links Great Calculator and assembled-language hypotheses.",
        "blocked_inference": "External corpus/method support does not anchor Book49 meaning in game.",
    },
    {
        "source_id": "TIBIASECRETS_HELLGATE_AVERAGE_ROUTE",
        "source_url": "https://www.tibiasecrets.com/article166",
        "source_result": "EXTERNAL_NUMERIC_METHOD_PRESSURE_ONLY",
        "support_value": "The article supports numeric/average pressure across Hellgate books.",
        "blocked_inference": "External arithmetic pressure cannot promote Book49's IAEN/NEEN sequence.",
    },
]

TESTS = [
    {
        "test_id": "Q90_T01_WEB_EXACT_BOOK49_SEQUENCE",
        "test_result": "FAILS_EXACT_SOURCE_REQUIREMENT",
        "interpretation": "No web query found exact Book49 sequence plus meaning/provenance.",
    },
    {
        "test_id": "Q90_T02_49_MATHEMAGIC_SOURCE",
        "test_result": "SUPPORTS_OPERATOR_PRESSURE_ONLY",
        "interpretation": "A Prisoner proves 49 is a Mathemagica output, not that Book49 means anything lexical.",
    },
    {
        "test_id": "Q90_T03_INTERNAL_REPEAT_GATE",
        "test_result": "PRESERVE_REPEAT_REGISTER_SHADOW",
        "interpretation": "Book49 remains the self-contained repeat/register witness.",
    },
    {
        "test_id": "Q90_T04_PLUS49_CONTROLS",
        "test_result": "FAILS_PROMOTION_CONTROLS",
        "interpretation": "+49 survives only as audit selector after holdout/control failures.",
    },
    {
        "test_id": "Q90_T05_CALIBRATION_RESET_GATE",
        "test_result": "FAILS_CALIBRATION_RESET_PROMOTION",
        "interpretation": "No calibration or operator-reset context is present.",
    },
    {
        "test_id": "Q90_T06_PROMOTION_FIREWALL",
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
        CREATE TABLE IF NOT EXISTS human_q90_book49_math49_exact_source_audit_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q82_run_id INTEGER NOT NULL,
            selfcontainment_run_id INTEGER NOT NULL,
            repeat_shadow_run_id INTEGER NOT NULL,
            residual_negative_run_id INTEGER NOT NULL,
            q3_book49_run_id INTEGER NOT NULL,
            plus49_wide_run_id INTEGER NOT NULL,
            plus49_holdout_run_id INTEGER NOT NULL,
            window_49_94_run_id INTEGER NOT NULL,
            mod70_sentinel_run_id INTEGER NOT NULL,
            q26_run_id INTEGER NOT NULL,
            q27_run_id INTEGER NOT NULL,
            q81_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            target_id TEXT NOT NULL,
            target_book_count INTEGER NOT NULL,
            web_query_count INTEGER NOT NULL,
            web_exact_book49_sequence_hit_count INTEGER NOT NULL,
            official_exact_target_hit_count INTEGER NOT NULL,
            source_check_count INTEGER NOT NULL,
            mathemagic_49_source_count INTEGER NOT NULL,
            exact_book49_sequence_count INTEGER NOT NULL,
            exact_meaning_relation_count INTEGER NOT NULL,
            selfcontainment_support_count INTEGER NOT NULL,
            repeat_rank INTEGER NOT NULL,
            repeat_control_count INTEGER NOT NULL,
            residual_control_hit_book_count INTEGER NOT NULL,
            plus49_selector_audit_count INTEGER NOT NULL,
            plus49_holdout_pass_count INTEGER NOT NULL,
            window_control_block_count INTEGER NOT NULL,
            calibration_context_count INTEGER NOT NULL,
            operator_reset_context_count INTEGER NOT NULL,
            lexical_ready_count INTEGER NOT NULL,
            direct_gloss_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            target_status TEXT NOT NULL,
            result_human_version TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q90_book49_math49_exact_source_audit_v1_queries (
            run_id INTEGER NOT NULL,
            query_id TEXT NOT NULL,
            query_text TEXT NOT NULL,
            result_status TEXT NOT NULL,
            notes TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, query_id)
        );

        CREATE TABLE IF NOT EXISTS human_q90_book49_math49_exact_source_audit_v1_sources (
            run_id INTEGER NOT NULL,
            source_id TEXT NOT NULL,
            source_url TEXT NOT NULL,
            source_result TEXT NOT NULL,
            support_value TEXT NOT NULL,
            blocked_inference TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, source_id)
        );

        CREATE TABLE IF NOT EXISTS human_q90_book49_math49_exact_source_audit_v1_books (
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

        CREATE TABLE IF NOT EXISTS human_q90_book49_math49_exact_source_audit_v1_tests (
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
    selfcontainment = latest_row(conn, "book49_selfcontainment_gate_runs")
    repeat_shadow = latest_row(conn, "human_book49_repeat_shadow_probe_v1_runs")
    residual_negative = latest_row(conn, "book49_residual_negative_probe_runs")
    q3 = latest_row(conn, "human_q3_book49_register_function_probe_v1_runs")
    plus49_wide = latest_row(conn, "mathemagic_plus49_wide_frontier_probe_v1_runs")
    plus49_holdout = latest_row(conn, "mathemagic_plus49_rank13_holdout_v1_runs")
    window_49_94 = latest_row(conn, "mathemagic_49_94_window_probe_v1_runs")
    mod70_sentinel = latest_row(conn, "mathemagic_book_mod70_sentinel_v1_runs")
    q26 = latest_row(conn, "human_q26_mathemagic_transcript_bridge_import_v1_runs")
    q27 = latest_row(conn, "human_q27_mathemagic_operator_queue_reconcile_v1_runs")
    q81 = latest_row(conn, "human_q81_controlled_shadow_export_v1_runs")
    completion = latest_row(conn, "human_translation_completion_audit_v5_runs")
    books = load_books(conn, int(q82["run_id"]))

    target_book_count = len(books)
    web_query_count = len(WEB_QUERIES)
    web_exact_book49_sequence_hit_count = 0
    official_exact_target_hit_count = 0
    source_check_count = len(SOURCE_CHECKS)
    mathemagic_49_source_count = 2
    exact_book49_sequence_count = 0
    exact_meaning_relation_count = 0
    selfcontainment_support_count = 1 if int(selfcontainment["external_note_present"]) == 1 else 0
    repeat_rank = int(repeat_shadow["target_repeat_rank"])
    repeat_control_count = 1
    residual_control_hit_book_count = int(residual_negative["control_hit_book_count"])
    plus49_selector_audit_count = 1 if int(plus49_wide["plus49_rank"]) == 1 else 0
    plus49_holdout_pass_count = int(plus49_holdout["plus49_best_anchor_hits"])
    window_control_block_count = 1 if int(window_49_94["control_best_score"]) > int(window_49_94["target_best_score"]) else 0
    calibration_context_count = int(q3["calibration_context_count"])
    operator_reset_context_count = int(q3["operator_reset_context_count"])
    lexical_ready_count = 0
    direct_gloss_count = 0
    canonical_promotion_allowed_count = 0
    target_status = "SOURCE_AUDITED_REPEAT_REGISTER_AND_49_OPERATOR_SUPPORT_NO_PROMOTION"
    result_human_version = (
        "Q90 preserves Book49 as a self-contained repeat/register formula and confirms that 49 is a real "
        "Mathemagica output. The two facts do not yet join: no checked source gives Book49's IAEN/NEEN "
        "sequence a meaning, and +49/mod70 fails promotion controls."
    )
    decision = (
        "Q90_BOOK49_MATH49_EXACT_SOURCE_AUDIT_OPERATOR_PRESSURE_NO_EXACT_BOOK49_GLOSS"
        if target_book_count == 1
        and web_query_count == 8
        and web_exact_book49_sequence_hit_count == 0
        and official_exact_target_hit_count == 0
        and source_check_count == 14
        and mathemagic_49_source_count >= 2
        and exact_book49_sequence_count == 0
        and exact_meaning_relation_count == 0
        and selfcontainment_support_count == 1
        and repeat_rank == 1
        and plus49_selector_audit_count == 1
        and plus49_holdout_pass_count == 0
        and window_control_block_count == 1
        and calibration_context_count == 0
        and operator_reset_context_count == 0
        and int(q26["direct_plaintext_gloss_count"]) == 0
        and int(q27["plaintext_allowed_count"]) == 0
        and int(q81["promoted_gloss_count"]) == 0
        and int(completion["promoted_gloss_count"]) == 0
        else "Q90_BOOK49_MATH49_EXACT_SOURCE_AUDIT_REQUIRES_REVIEW"
    )
    payload = {
        "answer": result_human_version,
        "operator_route": "49 is valid Mathemagica pressure, but Book49 needs predictive local behavior before promotion.",
        "blocked_use": "Do not translate IAEN, NEEN, O32, NEEI, 49, +49, mod70, repeat, chant, calibration, or reset as words.",
        "next_action": "Move to Q82_T06_BOOK54_PAIR_LOCAL_SPINE unless a new exact Book49 source or heldout +49 predictive win appears.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q90_book49_math49_exact_source_audit_v1_runs (
                created_at, decision, q82_run_id, selfcontainment_run_id,
                repeat_shadow_run_id, residual_negative_run_id, q3_book49_run_id,
                plus49_wide_run_id, plus49_holdout_run_id, window_49_94_run_id,
                mod70_sentinel_run_id, q26_run_id, q27_run_id,
                q81_run_id, completion_audit_run_id, target_id,
                target_book_count, web_query_count, web_exact_book49_sequence_hit_count,
                official_exact_target_hit_count, source_check_count,
                mathemagic_49_source_count, exact_book49_sequence_count,
                exact_meaning_relation_count, selfcontainment_support_count,
                repeat_rank, repeat_control_count, residual_control_hit_book_count,
                plus49_selector_audit_count, plus49_holdout_pass_count,
                window_control_block_count, calibration_context_count,
                operator_reset_context_count, lexical_ready_count, direct_gloss_count,
                canonical_promotion_allowed_count, target_status,
                result_human_version, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                int(q82["run_id"]),
                int(selfcontainment["run_id"]),
                int(repeat_shadow["run_id"]),
                int(residual_negative["run_id"]),
                int(q3["run_id"]),
                int(plus49_wide["run_id"]),
                int(plus49_holdout["run_id"]),
                int(window_49_94["run_id"]),
                int(mod70_sentinel["run_id"]),
                int(q26["run_id"]),
                int(q27["run_id"]),
                int(q81["run_id"]),
                int(completion["run_id"]),
                TARGET_ID,
                target_book_count,
                web_query_count,
                web_exact_book49_sequence_hit_count,
                official_exact_target_hit_count,
                source_check_count,
                mathemagic_49_source_count,
                exact_book49_sequence_count,
                exact_meaning_relation_count,
                selfcontainment_support_count,
                repeat_rank,
                repeat_control_count,
                residual_control_hit_book_count,
                plus49_selector_audit_count,
                plus49_holdout_pass_count,
                window_control_block_count,
                calibration_context_count,
                operator_reset_context_count,
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
            INSERT INTO human_q90_book49_math49_exact_source_audit_v1_queries (
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
            INSERT INTO human_q90_book49_math49_exact_source_audit_v1_sources (
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
            INSERT INTO human_q90_book49_math49_exact_source_audit_v1_books (
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
                    "PRESERVE_BOOK49_MATH49_REPEAT_REGISTER_SHADOW_ONLY",
                    j(dict(row)),
                )
                for row in books
            ],
        )
        conn.executemany(
            """
            INSERT INTO human_q90_book49_math49_exact_source_audit_v1_tests (
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
                "web_exact_book49_sequence_hit_count": web_exact_book49_sequence_hit_count,
                "official_exact_target_hit_count": official_exact_target_hit_count,
                "source_check_count": source_check_count,
                "mathemagic_49_source_count": mathemagic_49_source_count,
                "exact_book49_sequence_count": exact_book49_sequence_count,
                "exact_meaning_relation_count": exact_meaning_relation_count,
                "selfcontainment_support_count": selfcontainment_support_count,
                "repeat_rank": repeat_rank,
                "plus49_selector_audit_count": plus49_selector_audit_count,
                "plus49_holdout_pass_count": plus49_holdout_pass_count,
                "window_control_block_count": window_control_block_count,
                "lexical_ready_count": lexical_ready_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
            }
        )
    )


if __name__ == "__main__":
    main()
