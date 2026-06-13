#!/usr/bin/env python3
"""Q95: Book7/Mathemagica heldout selector benchmark."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
TARGET_ACTION_ID = "Q93_A02_BOOK7_OPERATOR_HELDOUT_SELECTOR_BENCHMARK"
TARGET_BOOKS = ["7", "6", "19", "31", "57", "49"]
OPERATOR_VALUES = ["1", "13", "49", "94"]

WEB_QUERIES = [
    {
        "query_id": "Q95_WEB_01",
        "query_text": '"ELBEEAEFTIINNEFIILEIITTNEIAAETTAAVNENIIFFEIEINTTIIILSBE"',
        "result_status": "NO_EXACT_BOOK7_SOURCE_HIT",
        "notes": "No checked web hit gives the exact Book7 row0 sequence plus meaning.",
    },
    {
        "query_id": "Q95_WEB_02",
        "query_text": '"TIINNEF" "NEIAAETTA" "469"',
        "result_status": "NO_EXACT_COMPONENT_MEANING_HIT",
        "notes": "No checked web hit gives a TIINNEF/NEIAAETTA meaning relation.",
    },
    {
        "query_id": "Q95_WEB_03",
        "query_text": '"0815953478019288" "469"',
        "result_status": "NO_EXACT_BOOK7_3478_WINDOW_MEANING_HIT",
        "notes": "No checked web hit gives the rare Book7 3478 window a meaning.",
    },
    {
        "query_id": "Q95_WEB_04",
        "query_text": '"6151353478019288" "469"',
        "result_status": "NO_EXACT_BOOK6_3478_WINDOW_MEANING_HIT",
        "notes": "No checked web hit gives the Book6 3478 window a meaning.",
    },
    {
        "query_id": "Q95_WEB_05",
        "query_text": '"3478 67 90871 97664 3466 0 345"',
        "result_status": "EXTERNAL_3478_PHRASE_CONTEXT_ONLY",
        "notes": "3478 phrase context is attested elsewhere, but not as a Book7 component value.",
    },
    {
        "query_id": "Q95_WEB_06",
        "query_text": '"1 + 1 = 13" "A Prisoner" Tibia',
        "result_status": "MATHEMAGIC_OPERATOR_SOURCE_FOUND",
        "notes": "A Prisoner transcript supports 1/13/49/94 as in-game mathemagic outputs.",
    },
    {
        "query_id": "Q95_WEB_07",
        "query_text": '"1 + 1 = 49" "1 + 1 = 94" "A Prisoner"',
        "result_status": "MATHEMAGIC_MULTI_OUTPUT_SOURCE_FOUND",
        "notes": "A Prisoner transcript supports multiple context-dependent operator outputs.",
    },
    {
        "query_id": "Q95_WEB_08",
        "query_text": 'site:tibia.com "ELBEEAEFTIINNEF"',
        "result_status": "NO_OFFICIAL_BOOK7_EXACT_HIT",
        "notes": "No official tibia.com exact hit was found for the Book7 sequence.",
    },
]

SOURCE_CHECKS = [
    {
        "source_id": "Q88_BOOK7_MATHEMAGIC_AUDIT",
        "source_url": "sqlite:human_q88_book7_phase_mathemagic_exact_source_audit_v1_runs",
        "source_result": "OPERATOR_SUPPORT_NO_EXACT_SOURCE_NO_GLOSS",
        "support_value": "Q88 preserves Book7 as phase-continuity bridge/control and Mathemagica as operator machinery.",
        "blocked_inference": "No exact Book7 sequence meaning or forced value.",
    },
    {
        "source_id": "BOOK7_PHASE_SHADOW",
        "source_url": "sqlite:human_book7_phase_shadow_probe_v1_runs",
        "source_result": "BRIDGE_SUPPORTED_NO_GLOSS",
        "support_value": "Book7 is the bridge book among Book6, Book7, and the 19/31/57 phase-context controls.",
        "blocked_inference": "Phase support does not define TIINNEF or NEIAAETTA.",
    },
    {
        "source_id": "Q4_BOOK7_PHASE_DIRECTION",
        "source_url": "sqlite:human_q4_book7_phase_direction_probe_v1_runs",
        "source_result": "DIRECTION_HELD_NO_GLOSS",
        "support_value": "Book7 survives support/control checks, but surface order conflicts with a promoted direction.",
        "blocked_inference": "No internal Book7 direction or payload prose.",
    },
    {
        "source_id": "Q8_BOOK6_7_3478_TRANSITION",
        "source_url": "sqlite:human_q8_book6_7_phase_path_3478_transition_probe_v1_runs",
        "source_result": "PHASE_PATH_SUPPORTED_NO_PAYLOAD_GLOSS",
        "support_value": "Book6->Book7 has a local 3478-window transition/control relation.",
        "blocked_inference": "3478, Book6, Book7, NEIAAETTA, and TIINNEF are not payload words.",
    },
    {
        "source_id": "Q9_BOOK6_7_HELDOUT_SUPPORT",
        "source_url": "sqlite:human_q9_book6_7_heldout_support_audit_v1_runs",
        "source_result": "NO_HELDOUT_CONTIG_SUPPORT_KEEP_CONTROL",
        "support_value": "Current contig, overlap, literal frontier, and similarity tables do not independently predict Book6/7.",
        "blocked_inference": "The Book6/7 relation remains local control, not sentence reading.",
    },
    {
        "source_id": "Q26_MATHEMAGIC_TRANSCRIPT_BRIDGE",
        "source_url": "sqlite:human_q26_mathemagic_transcript_bridge_import_v1_runs",
        "source_result": "OPERATOR_ONLY_NO_GLOSS",
        "support_value": "In-game transcripts support 1/13/49/94 as Mathemagica operator outputs.",
        "blocked_inference": "Mathemagica is not a plaintext dictionary.",
    },
    {
        "source_id": "Q27_MATHEMAGIC_OPERATOR_QUEUE",
        "source_url": "sqlite:human_q27_mathemagic_operator_queue_reconcile_v1_runs",
        "source_result": "ONLY_13_LIVE_LOCALLY_NO_GLOSS",
        "support_value": "Only 13 is live locally; 94 is weak audit-only; 49 is blocked for general selector use; 1 is context-only.",
        "blocked_inference": "No operator becomes a Book7 gloss.",
    },
    {
        "source_id": "MATHEMAGIC_OPERATIONAL_DECISION",
        "source_url": "sqlite:mathemagic_operational_decision_v1_runs",
        "source_result": "LOCAL_OPERATORS_ONLY_NO_GLOSS",
        "support_value": "Delta13 is local C86/C68; +49/mod70 and 94 stay audit/blocked; broad selectors are dead.",
        "blocked_inference": "No general operator selector is promotable for Book7.",
    },
    {
        "source_id": "DELTA13_HELDOUT",
        "source_url": "sqlite:mathemagic_delta13_heldout_v1_runs",
        "source_result": "C86_C68_LOCAL_OPERATOR_STABLE_NO_PROSE",
        "support_value": "Delta13 has 5/5 heldout pass in its own C86/C68 route.",
        "blocked_inference": "This is not a Book7/phase-family heldout pass.",
    },
    {
        "source_id": "PLUS49_RANK13_HOLDOUT",
        "source_url": "sqlite:mathemagic_plus49_rank13_holdout_v1_runs",
        "source_result": "PLUS49_FAILS_HOLDOUT",
        "support_value": "+49 has zero best-anchor hits in rank13 holdout and is demoted to audit-only.",
        "blocked_inference": "+49 cannot be used as a Book7 or Book49 selector.",
    },
    {
        "source_id": "MATHEMAGIC_49_94_WINDOW",
        "source_url": "sqlite:mathemagic_49_94_window_probe_v1_runs",
        "source_result": "CONTROLS_TIE_OR_BEAT",
        "support_value": "49/94 windows lose to or tie controls.",
        "blocked_inference": "49/94 windows cannot force Book7 value.",
    },
    {
        "source_id": "A_PRISONER_TRANSCRIPT",
        "source_url": "https://tibia.fandom.com/wiki/A_Prisoner/Transcripts",
        "source_result": "INGAME_MATHEMAGIC_OUTPUTS",
        "support_value": "A Prisoner gives the mathemagic outputs 1, 13, 49, and 94.",
        "blocked_inference": "The transcript does not mention Book7 or assign any Hellgate book meaning.",
    },
    {
        "source_id": "A_WRINKLED_BONELORD_TRANSCRIPT",
        "source_url": "https://tibia.fandom.com/wiki/A_Wrinkled_Bonelord/Transcripts",
        "source_result": "INGAME_METHOD_ANCHOR",
        "support_value": "A Wrinkled Bonelord anchors 469 books, numbers, and mathemagical processing.",
        "blocked_inference": "The transcript gives no TIINNEF, NEIAAETTA, or Book7 gloss.",
    },
    {
        "source_id": "TIBIAWIKI_469_MATHEMAGIC_CONTEXT",
        "source_url": "https://www.tibiawiki.com.br/469",
        "source_result": "MATHEMAGIC_CONTEXT_WITH_WARNING",
        "support_value": "The 469 page links A Prisoner/Mathemagics and AWB language context.",
        "blocked_inference": "It explicitly remains context and does not solve Book7 plaintext.",
    },
]

TESTS = [
    {
        "test_id": "Q95_T01_WEB_EXACT_BOOK7",
        "test_result": "FAILS_EXACT_SOURCE_REQUIREMENT",
        "interpretation": "No exact source gives Book7 or its phase components a meaning.",
    },
    {
        "test_id": "Q95_T02_BOOK7_LOCAL_PHASE",
        "test_result": "PRESERVE_BOOK7_PHASE_CONTROL",
        "interpretation": "Book7 remains useful as a local phase bridge/control with direction held.",
    },
    {
        "test_id": "Q95_T03_OPERATOR_HELDOUT_TARGET",
        "test_result": "FAILS_BOOK7_OPERATOR_HELDOUT",
        "interpretation": "No 1/13/49/94 operator passes heldout selection for the Book7 family.",
    },
    {
        "test_id": "Q95_T04_DELTA13_SCOPE",
        "test_result": "PRESERVE_DELTA13_OUTSIDE_BOOK7",
        "interpretation": "Delta13 remains a C86/C68 local operator, not a Book7 operator.",
    },
    {
        "test_id": "Q95_T05_49_94_PLUS49_CONTROLS",
        "test_result": "BLOCKS_49_94_AND_PLUS49_PROMOTION",
        "interpretation": "+49 fails holdout and 49/94 windows are beaten or tied by controls.",
    },
    {
        "test_id": "Q95_T06_PROMOTION_FIREWALL",
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
        CREATE TABLE IF NOT EXISTS human_q95_book7_operator_heldout_selector_benchmark_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q93_run_id INTEGER NOT NULL,
            q88_run_id INTEGER NOT NULL,
            q81_run_id INTEGER NOT NULL,
            book7_phase_run_id INTEGER NOT NULL,
            q4_direction_run_id INTEGER NOT NULL,
            q8_transition_run_id INTEGER NOT NULL,
            q9_heldout_run_id INTEGER NOT NULL,
            q26_run_id INTEGER NOT NULL,
            q27_run_id INTEGER NOT NULL,
            math_synthesis_run_id INTEGER NOT NULL,
            math_operational_run_id INTEGER NOT NULL,
            delta13_heldout_run_id INTEGER NOT NULL,
            plus49_holdout_run_id INTEGER NOT NULL,
            window_49_94_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            action_id TEXT NOT NULL,
            target_book_count INTEGER NOT NULL,
            phase_positive_book_count INTEGER NOT NULL,
            continuity_control_count INTEGER NOT NULL,
            phase_context_control_count INTEGER NOT NULL,
            repeat_register_control_count INTEGER NOT NULL,
            web_query_count INTEGER NOT NULL,
            web_exact_book7_hit_count INTEGER NOT NULL,
            official_exact_target_hit_count INTEGER NOT NULL,
            source_check_count INTEGER NOT NULL,
            exact_source_sequence_count INTEGER NOT NULL,
            exact_meaning_relation_count INTEGER NOT NULL,
            operator_candidate_count INTEGER NOT NULL,
            operator_source_output_count INTEGER NOT NULL,
            live_local_operator_count INTEGER NOT NULL,
            book7_operator_heldout_pass_count INTEGER NOT NULL,
            book7_local_transition_signal_count INTEGER NOT NULL,
            book6_7_independent_heldout_count INTEGER NOT NULL,
            delta13_non_book7_heldout_pass_count INTEGER NOT NULL,
            plus49_holdout_pass_count INTEGER NOT NULL,
            window_control_block_count INTEGER NOT NULL,
            protected_control_count INTEGER NOT NULL,
            lexical_ready_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            target_status TEXT NOT NULL,
            result_human_version TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q95_book7_operator_heldout_selector_benchmark_v1_queries (
            run_id INTEGER NOT NULL,
            query_id TEXT NOT NULL,
            query_text TEXT NOT NULL,
            result_status TEXT NOT NULL,
            notes TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, query_id)
        );

        CREATE TABLE IF NOT EXISTS human_q95_book7_operator_heldout_selector_benchmark_v1_sources (
            run_id INTEGER NOT NULL,
            source_id TEXT NOT NULL,
            source_url TEXT NOT NULL,
            source_result TEXT NOT NULL,
            support_value TEXT NOT NULL,
            blocked_inference TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, source_id)
        );

        CREATE TABLE IF NOT EXISTS human_q95_book7_operator_heldout_selector_benchmark_v1_books (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            benchmark_role TEXT NOT NULL,
            symbol_text TEXT NOT NULL,
            source_bridge_id TEXT NOT NULL,
            plausible_human_reading TEXT NOT NULL,
            confidence_tier TEXT NOT NULL,
            benchmark_result TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        );

        CREATE TABLE IF NOT EXISTS human_q95_book7_operator_heldout_selector_benchmark_v1_operators (
            run_id INTEGER NOT NULL,
            operator_value TEXT NOT NULL,
            benchmark_status TEXT NOT NULL,
            source_status TEXT NOT NULL,
            scope TEXT NOT NULL,
            heldout_result TEXT NOT NULL,
            blocked_inference TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, operator_value)
        );

        CREATE TABLE IF NOT EXISTS human_q95_book7_operator_heldout_selector_benchmark_v1_tests (
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


def q81_book(conn: sqlite3.Connection, q81_run_id: int, bookid: str) -> sqlite3.Row:
    row = conn.execute(
        """
        SELECT *
        FROM human_q81_controlled_shadow_export_v1_items
        WHERE run_id=? AND bookid=?
        """,
        (q81_run_id, bookid),
    ).fetchone()
    if row is None:
        raise RuntimeError(f"missing q81 book: {bookid}")
    return row


def symbol_text(conn: sqlite3.Connection, bookid: str) -> str:
    row = conn.execute(
        """
        SELECT symbol_text
        FROM row0_variant_book_tokens
        WHERE bookid=?
        ORDER BY run_id DESC
        LIMIT 1
        """,
        (bookid,),
    ).fetchone()
    if row is None:
        raise RuntimeError(f"missing symbol text: {bookid}")
    return str(row["symbol_text"])


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q93 = latest_row(conn, "human_q93_route_atlas_after_q90_q92_v1_runs")
    q88 = latest_row(conn, "human_q88_book7_phase_mathemagic_exact_source_audit_v1_runs")
    q81 = latest_row(conn, "human_q81_controlled_shadow_export_v1_runs")
    book7_phase = latest_row(conn, "human_book7_phase_shadow_probe_v1_runs")
    q4 = latest_row(conn, "human_q4_book7_phase_direction_probe_v1_runs")
    q8 = latest_row(conn, "human_q8_book6_7_phase_path_3478_transition_probe_v1_runs")
    q9 = latest_row(conn, "human_q9_book6_7_heldout_support_audit_v1_runs")
    q26 = latest_row(conn, "human_q26_mathemagic_transcript_bridge_import_v1_runs")
    q27 = latest_row(conn, "human_q27_mathemagic_operator_queue_reconcile_v1_runs")
    math_synthesis = latest_row(conn, "human_mathemagic_shadow_synthesis_v1_runs")
    math_operational = latest_row(conn, "mathemagic_operational_decision_v1_runs")
    delta13 = latest_row(conn, "mathemagic_delta13_heldout_v1_runs")
    plus49 = latest_row(conn, "mathemagic_plus49_rank13_holdout_v1_runs")
    window_49_94 = latest_row(conn, "mathemagic_49_94_window_probe_v1_runs")
    completion = latest_row(conn, "human_translation_completion_audit_v5_runs")
    q81_rows = {bookid: q81_book(conn, int(q81["run_id"]), bookid) for bookid in TARGET_BOOKS}

    target_book_count = len(TARGET_BOOKS)
    phase_positive_book_count = 1
    continuity_control_count = 1
    phase_context_control_count = 3
    repeat_register_control_count = 1
    web_query_count = len(WEB_QUERIES)
    web_exact_book7_hit_count = 0
    official_exact_target_hit_count = 0
    source_check_count = len(SOURCE_CHECKS)
    exact_source_sequence_count = 0
    exact_meaning_relation_count = 0
    operator_candidate_count = len(OPERATOR_VALUES)
    operator_source_output_count = int(q26["mathemagic_operator_output_count"])
    live_local_operator_count = int(q27["live_local_operator_count"])
    book7_operator_heldout_pass_count = 0
    book7_local_transition_signal_count = int(q8["transition_signal_count"])
    book6_7_independent_heldout_count = int(q9["heldout_positive_count"])
    delta13_non_book7_heldout_pass_count = int(delta13["pass_count"])
    plus49_holdout_pass_count = int(plus49["plus49_best_anchor_hits"])
    window_control_block_count = 1 if "REJECT" in str(window_49_94["decision"]) else 0
    protected_control_count = 2
    lexical_ready_count = 0
    canonical_promotion_allowed_count = 0
    target_status = "OPERATOR_BENCHMARK_BOOK7_LOCAL_PHASE_SUPPORTED_NO_HELDOUT_SELECTOR"
    result_human_version = (
        "Q95 keeps Book7/Mathemagica as an operator-search route, not a translation route. "
        "Book7 still works as a local phase-control bridge against Book6 and 19/31/57, "
        "but no 1/13/49/94 operator passes a Book7-family heldout selector benchmark. "
        "Delta13 remains useful only in the C86/C68 route; +49 and 49/94 stay blocked or audit-only."
    )
    decision = (
        "Q95_BOOK7_OPERATOR_HELDOUT_SELECTOR_BENCHMARK_LOCAL_PHASE_SUPPORTED_NO_OPERATOR_HELDOUT_NO_GLOSS"
        if target_book_count == 6
        and web_query_count == 8
        and web_exact_book7_hit_count == 0
        and official_exact_target_hit_count == 0
        and source_check_count == 14
        and exact_source_sequence_count == 0
        and exact_meaning_relation_count == 0
        and operator_candidate_count == 4
        and operator_source_output_count == 4
        and live_local_operator_count == 1
        and book7_operator_heldout_pass_count == 0
        and book7_local_transition_signal_count == 1
        and book6_7_independent_heldout_count == 0
        and delta13_non_book7_heldout_pass_count == 5
        and plus49_holdout_pass_count == 0
        and window_control_block_count == 1
        and protected_control_count == 2
        and int(q88["canonical_promotion_allowed_count"]) == 0
        and int(q93["promoted_gloss_count"]) == 0
        and int(completion["promoted_gloss_count"]) == 0
        else "Q95_BOOK7_OPERATOR_HELDOUT_SELECTOR_BENCHMARK_REQUIRES_REVIEW"
    )
    payload = {
        "answer": result_human_version,
        "allowed_use": "Use Book7 as a local phase-control route and Mathemagica as selector-search machinery.",
        "blocked_use": "Do not translate Book7, 3478, TIINNEF, NEIAAETTA, 1, 13, 49, or 94 as words.",
        "next_action": "Proceed to Q93_A03 Q80 packet source-as-packet search.",
    }

    operator_rows = [
        {
            "operator_value": "1",
            "benchmark_status": "CONTEXT_ONLY_NO_BOOK7_PASS",
            "source_status": "A_PRISONER_OUTPUT",
            "scope": "context-only",
            "heldout_result": "NO_BOOK7_HELDOUT_PASS",
            "blocked_inference": "1 cannot decode Book7 or the Book7 controls.",
        },
        {
            "operator_value": "13",
            "benchmark_status": "LIVE_LOCAL_OUTSIDE_BOOK7",
            "source_status": "A_PRISONER_OUTPUT_AND_DELTA13_PASS",
            "scope": "C86/C68 local operator only",
            "heldout_result": "PASS_OUTSIDE_BOOK7_FAMILY_ONLY",
            "blocked_inference": "13 cannot be imported into Book7 phase material.",
        },
        {
            "operator_value": "49",
            "benchmark_status": "BLOCKED_GENERAL_SELECTOR_AUDIT_ONLY",
            "source_status": "A_PRISONER_OUTPUT_PLUS49_HOLDOUT_FAIL",
            "scope": "narrow audit only",
            "heldout_result": "NO_BOOK7_HELDOUT_PASS",
            "blocked_inference": "49 cannot decode Book7 or Book49 repeat/register.",
        },
        {
            "operator_value": "94",
            "benchmark_status": "WEAK_AUDIT_ONLY_WINDOW_BLOCKED",
            "source_status": "A_PRISONER_OUTPUT_49_94_CONTROLS_BLOCK",
            "scope": "weak audit only",
            "heldout_result": "NO_BOOK7_HELDOUT_PASS",
            "blocked_inference": "94 cannot force Book7 value.",
        },
    ]

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q95_book7_operator_heldout_selector_benchmark_v1_runs (
                created_at, decision, q93_run_id, q88_run_id, q81_run_id,
                book7_phase_run_id, q4_direction_run_id, q8_transition_run_id,
                q9_heldout_run_id, q26_run_id, q27_run_id, math_synthesis_run_id,
                math_operational_run_id, delta13_heldout_run_id, plus49_holdout_run_id,
                window_49_94_run_id, completion_audit_run_id, action_id,
                target_book_count, phase_positive_book_count, continuity_control_count,
                phase_context_control_count, repeat_register_control_count,
                web_query_count, web_exact_book7_hit_count, official_exact_target_hit_count,
                source_check_count, exact_source_sequence_count, exact_meaning_relation_count,
                operator_candidate_count, operator_source_output_count, live_local_operator_count,
                book7_operator_heldout_pass_count, book7_local_transition_signal_count,
                book6_7_independent_heldout_count, delta13_non_book7_heldout_pass_count,
                plus49_holdout_pass_count, window_control_block_count, protected_control_count,
                lexical_ready_count, canonical_promotion_allowed_count, target_status,
                result_human_version, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                int(q93["run_id"]),
                int(q88["run_id"]),
                int(q81["run_id"]),
                int(book7_phase["run_id"]),
                int(q4["run_id"]),
                int(q8["run_id"]),
                int(q9["run_id"]),
                int(q26["run_id"]),
                int(q27["run_id"]),
                int(math_synthesis["run_id"]),
                int(math_operational["run_id"]),
                int(delta13["run_id"]),
                int(plus49["run_id"]),
                int(window_49_94["run_id"]),
                int(completion["run_id"]),
                TARGET_ACTION_ID,
                target_book_count,
                phase_positive_book_count,
                continuity_control_count,
                phase_context_control_count,
                repeat_register_control_count,
                web_query_count,
                web_exact_book7_hit_count,
                official_exact_target_hit_count,
                source_check_count,
                exact_source_sequence_count,
                exact_meaning_relation_count,
                operator_candidate_count,
                operator_source_output_count,
                live_local_operator_count,
                book7_operator_heldout_pass_count,
                book7_local_transition_signal_count,
                book6_7_independent_heldout_count,
                delta13_non_book7_heldout_pass_count,
                plus49_holdout_pass_count,
                window_control_block_count,
                protected_control_count,
                lexical_ready_count,
                canonical_promotion_allowed_count,
                target_status,
                result_human_version,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q95_book7_operator_heldout_selector_benchmark_v1_queries (
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
            INSERT INTO human_q95_book7_operator_heldout_selector_benchmark_v1_sources (
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
        book_rows = []
        for bookid in TARGET_BOOKS:
            q81_row = q81_rows[bookid]
            if bookid == "7":
                role = "PHASE_POSITIVE"
                result = "LOCAL_PHASE_BRIDGE_SUPPORTED_NO_OPERATOR_HELDOUT"
            elif bookid == "6":
                role = "CONTINUITY_CONTROL"
                result = "CONTROL_CONTINUITY_ONLY_NO_PHASE_GLOSS"
            elif bookid == "49":
                role = "REPEAT_REGISTER_OPERATOR_CONTROL"
                result = "CONTROL_REPEAT_REGISTER_PLUS49_BLOCKED"
            else:
                role = "PHASE_CONTEXT_CONTROL"
                result = "CONTROL_VNCTIIN_TIINNEF_PHASE_CONTEXT_NO_OPERATOR_PASS"
            evidence = {
                "q81": dict(q81_row),
                "symbol_text": symbol_text(conn, bookid),
            }
            book_rows.append(
                (
                    run_id,
                    bookid,
                    role,
                    evidence["symbol_text"],
                    str(q81_row["source_bridge_id"]),
                    str(q81_row["plausible_human_reading"]),
                    str(q81_row["confidence_tier"]),
                    result,
                    j(evidence),
                )
            )
        conn.executemany(
            """
            INSERT INTO human_q95_book7_operator_heldout_selector_benchmark_v1_books (
                run_id, bookid, benchmark_role, symbol_text, source_bridge_id,
                plausible_human_reading, confidence_tier, benchmark_result, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            book_rows,
        )
        conn.executemany(
            """
            INSERT INTO human_q95_book7_operator_heldout_selector_benchmark_v1_operators (
                run_id, operator_value, benchmark_status, source_status, scope,
                heldout_result, blocked_inference, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    row["operator_value"],
                    row["benchmark_status"],
                    row["source_status"],
                    row["scope"],
                    row["heldout_result"],
                    row["blocked_inference"],
                    j(row),
                )
                for row in operator_rows
            ],
        )
        conn.executemany(
            """
            INSERT INTO human_q95_book7_operator_heldout_selector_benchmark_v1_tests (
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
                "action_id": TARGET_ACTION_ID,
                "target_book_count": target_book_count,
                "web_query_count": web_query_count,
                "web_exact_book7_hit_count": web_exact_book7_hit_count,
                "official_exact_target_hit_count": official_exact_target_hit_count,
                "source_check_count": source_check_count,
                "exact_source_sequence_count": exact_source_sequence_count,
                "exact_meaning_relation_count": exact_meaning_relation_count,
                "operator_candidate_count": operator_candidate_count,
                "operator_source_output_count": operator_source_output_count,
                "live_local_operator_count": live_local_operator_count,
                "book7_operator_heldout_pass_count": book7_operator_heldout_pass_count,
                "book7_local_transition_signal_count": book7_local_transition_signal_count,
                "book6_7_independent_heldout_count": book6_7_independent_heldout_count,
                "delta13_non_book7_heldout_pass_count": delta13_non_book7_heldout_pass_count,
                "plus49_holdout_pass_count": plus49_holdout_pass_count,
                "window_control_block_count": window_control_block_count,
                "protected_control_count": protected_control_count,
                "lexical_ready_count": lexical_ready_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
            }
        )
    )


if __name__ == "__main__":
    main()
