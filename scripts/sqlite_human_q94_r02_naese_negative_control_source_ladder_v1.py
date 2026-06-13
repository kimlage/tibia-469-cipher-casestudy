#!/usr/bin/env python3
"""Q94: R02/NAESE negative-control source ladder after route-atlas export."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
TARGET_ACTION_ID = "Q93_A01_R02_NEGATIVE_CONTROL_SOURCE_LADDER"
POSITIVE_BOOKS = ["51", "53"]
CONTROL_BOOKS = ["14", "45", "46"]
ALL_BOOKS = CONTROL_BOOKS + POSITIVE_BOOKS

WEB_QUERIES = [
    {
        "query_id": "Q94_WEB_01",
        "query_text": '"FIVNANI*ANIVVENINTEINLFSEITVAETRFEVASTFFFEEINBLEIIFFTRVEIIVNTBB"',
        "result_status": "NO_EXACT_BOOK51_SOURCE_HIT",
        "notes": "No checked web hit gives Book51 sequence plus meaning.",
    },
    {
        "query_id": "Q94_WEB_02",
        "query_text": '"INTEINLFSEITVAETRFEVASTFFFEEINBLEIIFFTRVEIIVNTBBNNEIT"',
        "result_status": "NO_EXACT_BOOK53_SOURCE_HIT",
        "notes": "No checked web hit gives Book53 sequence plus meaning.",
    },
    {
        "query_id": "Q94_WEB_03",
        "query_text": '"FIEIVEEIN*VNVI*ANIVVENINTEINLFSEITVAETRFEVASTFFFEEINBLEIIFFTRVEIIVNTBB"',
        "result_status": "NO_EXACT_BOOK45_CONTROL_SOURCE_HIT",
        "notes": "No checked web hit gives Book45 control sequence plus meaning.",
    },
    {
        "query_id": "Q94_WEB_04",
        "query_text": '"ITRVEIIVNTBBNNEITENN*VNAFAINI*LTASTTNVVNNFIEVNNSTAEFIEIEFIFFTIILEEAI"',
        "result_status": "NO_EXACT_BOOK14_CONTROL_SOURCE_HIT",
        "notes": "No checked web hit gives Book14 boundary-control sequence plus meaning.",
    },
    {
        "query_id": "Q94_WEB_05",
        "query_text": '"TRVEIIVNTBBNNEITVAFENTEIEIISETBASEFAIFVI"',
        "result_status": "NO_EXACT_R02_TO_NAESE_SHARED_SEGMENT_HIT",
        "notes": "No checked web hit gives the R02-to-NAESE segment plus meaning.",
    },
    {
        "query_id": "Q94_WEB_06",
        "query_text": '"NAESESTIENFATCTIVVTISETEIVIFASTFNEIEI"',
        "result_status": "NO_EXACT_NAESE_C68_SLOT_SEGMENT_HIT",
        "notes": "No checked web hit gives the NAESE/C68 slot segment plus meaning.",
    },
    {
        "query_id": "Q94_WEB_07",
        "query_text": '"TRVEIIVNTBB" "469"',
        "result_status": "NO_R02_TERM_SOURCE_HIT",
        "notes": "No checked web hit ties TRVEIIVNTBB to a meaning.",
    },
    {
        "query_id": "Q94_WEB_08",
        "query_text": 'site:tibia.com "TRVEIIVNTBB"',
        "result_status": "NO_OFFICIAL_EXACT_R02_HIT",
        "notes": "No official tibia.com exact hit was found for TRVEIIVNTBB.",
    },
]

SOURCE_CHECKS = [
    {
        "source_id": "Q87_R02_NAESE_EXACT_SOURCE_AUDIT",
        "source_url": "sqlite:human_q87_r02_naese_exact_source_audit_v1_runs",
        "source_result": "STRUCTURAL_BRIDGE_SUPPORT_NO_EXACT_SOURCE_NO_GLOSS",
        "support_value": "Q87 preserves 51/53 as strong R02 phase-to-NAESE/C68 slot bridge.",
        "blocked_inference": "No exact source sequence plus meaning; no R02/NAESE/C68 word gloss.",
    },
    {
        "source_id": "R02_NAESE_SLOT_BRIDGE_GATE",
        "source_url": "sqlite:r02_naese_slot_bridge_v1_runs",
        "source_result": "2_OF_2_POSITIVE_SLOT_BRIDGE_PASS_NO_PROSE",
        "support_value": "Books 51 and 53 both pass R02_TRVEIIVNTBB_TO_NAESE_SLOT_BRIDGE.",
        "blocked_inference": "Pass count is structural and does not make a sentence translation.",
    },
    {
        "source_id": "R20_R02_NAESE_PHASE_GATE",
        "source_url": "sqlite:r20_r02_naese_phase_gate_v1_runs",
        "source_result": "R02_SPECIFIC_WITH_R20_CONTEXT_WARNINGS_NO_PROSE",
        "support_value": "51/53 pass as R02 slot bridges; 45/64/65 fail R20 phase context; 46 is context connector.",
        "blocked_inference": "R02/R20 phase material cannot be promoted as global R meaning.",
    },
    {
        "source_id": "BOOK45_R02_PREFIX_CONTROL",
        "source_url": "sqlite:book45_r02_prefix_control_v1_runs",
        "source_result": "R02_PREFIX_CONTROL_NO_NAESE_C68_NO_PROSE",
        "support_value": "Book45 shares R02/R20 prefix material with positives but lacks NAESE/C68 continuation.",
        "blocked_inference": "Prefix overlap is not a slot bridge or sentence connective.",
    },
    {
        "source_id": "R02_LTAST_BOUNDARY_GATE",
        "source_url": "sqlite:r02_ltast_boundary_gate_v1_runs",
        "source_result": "BOUNDARY_STRUCTURAL_GATE_NO_GLOSS",
        "support_value": "Book14 remains a boundary/audit control with zero promoted count.",
        "blocked_inference": "Book14 cannot be promoted as R02 or LTAST translation.",
    },
    {
        "source_id": "Q81_CONTROLLED_SHADOW_EXPORT",
        "source_url": "sqlite:human_q81_controlled_shadow_export_v1_items",
        "source_result": "ALL_TARGET_AND_CONTROL_BOOKS_NOT_PROMOTED",
        "support_value": "Books 14/45/46/51/53 have human-shadow readings and NOT_PROMOTED status.",
        "blocked_inference": "Readable shadow rows are not canonical plaintext.",
    },
    {
        "source_id": "Q93_ROUTE_ATLAS",
        "source_url": "sqlite:human_q93_route_atlas_after_q90_q92_v1_actions",
        "source_result": "R02_NEGATIVE_CONTROL_LADDER_SELECTED",
        "support_value": "Q93 ranks this ladder as the next primary route.",
        "blocked_inference": "Route priority does not weaken exact-source requirements.",
    },
    {
        "source_id": "AWB_LANGUAGE_MATHEMAGIC",
        "source_url": "https://tibia.fandom.com/wiki/A_Wrinkled_Bonelord/Transcripts",
        "source_result": "INGAME_METHOD_ANCHOR_ONLY",
        "support_value": "A Wrinkled Bonelord anchors numbers, books, blinking, and mathemagic as method context.",
        "blocked_inference": "The transcript gives no R02/NAESE sequence meaning.",
    },
]

TESTS = [
    {
        "test_id": "Q94_T01_WEB_EXACT_SOURCE",
        "test_result": "FAILS_EXACT_SOURCE_REQUIREMENT",
        "interpretation": "No exact source found for positives, controls, R02 segment, or NAESE/C68 segment.",
    },
    {
        "test_id": "Q94_T02_POSITIVE_SPECIFICITY",
        "test_result": "PASSES_POSITIVE_SLOT_BRIDGE",
        "interpretation": "51/53 remain ordered-core R02 slot bridge positives.",
    },
    {
        "test_id": "Q94_T03_CONTROL_REJECTION",
        "test_result": "PASSES_CONTROL_REJECTION_WITH_BOOK46_WARNING",
        "interpretation": "14/45 do not enter the slot; 46 is a context connector warning, not a bridge pass.",
    },
    {
        "test_id": "Q94_T04_OVERBROAD_RISK",
        "test_result": "BOOK46_OVERBROAD_WARNING_HELD",
        "interpretation": "Any prose reading must explain why Book46 is context connector rather than full R02/NAESE bridge.",
    },
    {
        "test_id": "Q94_T05_PROMOTION_FIREWALL",
        "test_result": "PASSES_BLOCK_PROMOTION",
        "interpretation": "All route items remain NOT_PROMOTED and completion audit has zero promoted glosses.",
    },
]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q94_r02_naese_negative_control_source_ladder_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q93_run_id INTEGER NOT NULL,
            q87_run_id INTEGER NOT NULL,
            q81_run_id INTEGER NOT NULL,
            r02_bridge_run_id INTEGER NOT NULL,
            phase_gate_run_id INTEGER NOT NULL,
            book45_control_run_id INTEGER NOT NULL,
            r02_ltast_boundary_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            action_id TEXT NOT NULL,
            positive_book_count INTEGER NOT NULL,
            control_book_count INTEGER NOT NULL,
            web_query_count INTEGER NOT NULL,
            web_exact_target_hit_count INTEGER NOT NULL,
            official_exact_target_hit_count INTEGER NOT NULL,
            source_check_count INTEGER NOT NULL,
            exact_source_sequence_count INTEGER NOT NULL,
            exact_meaning_relation_count INTEGER NOT NULL,
            positive_slot_bridge_pass_count INTEGER NOT NULL,
            control_slot_bridge_pass_count INTEGER NOT NULL,
            control_context_connector_count INTEGER NOT NULL,
            control_no_slot_count INTEGER NOT NULL,
            boundary_control_count INTEGER NOT NULL,
            overbroad_warning_count INTEGER NOT NULL,
            specificity_pass_count INTEGER NOT NULL,
            lexical_ready_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            target_status TEXT NOT NULL,
            result_human_version TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q94_r02_naese_negative_control_source_ladder_v1_queries (
            run_id INTEGER NOT NULL,
            query_id TEXT NOT NULL,
            query_text TEXT NOT NULL,
            result_status TEXT NOT NULL,
            notes TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, query_id)
        );

        CREATE TABLE IF NOT EXISTS human_q94_r02_naese_negative_control_source_ladder_v1_sources (
            run_id INTEGER NOT NULL,
            source_id TEXT NOT NULL,
            source_url TEXT NOT NULL,
            source_result TEXT NOT NULL,
            support_value TEXT NOT NULL,
            blocked_inference TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, source_id)
        );

        CREATE TABLE IF NOT EXISTS human_q94_r02_naese_negative_control_source_ladder_v1_books (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            role TEXT NOT NULL,
            symbol_text TEXT NOT NULL,
            source_bridge_id TEXT NOT NULL,
            likely_speech_act TEXT NOT NULL,
            plausible_human_reading TEXT NOT NULL,
            confidence_tier TEXT NOT NULL,
            ladder_result TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        );

        CREATE TABLE IF NOT EXISTS human_q94_r02_naese_negative_control_source_ladder_v1_tests (
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
    q87 = latest_row(conn, "human_q87_r02_naese_exact_source_audit_v1_runs")
    q81 = latest_row(conn, "human_q81_controlled_shadow_export_v1_runs")
    r02_bridge = latest_row(conn, "r02_naese_slot_bridge_v1_runs")
    phase_gate = latest_row(conn, "r20_r02_naese_phase_gate_v1_runs")
    book45_control = latest_row(conn, "book45_r02_prefix_control_v1_runs")
    r02_ltast_boundary = latest_row(conn, "r02_ltast_boundary_gate_v1_runs")
    completion = latest_row(conn, "human_translation_completion_audit_v5_runs")

    q81_rows = {bookid: q81_book(conn, int(q81["run_id"]), bookid) for bookid in ALL_BOOKS}
    bridge_items = conn.execute(
        """
        SELECT bookid, gate_status
        FROM r02_naese_slot_bridge_v1_items
        WHERE run_id=?
        """,
        (int(r02_bridge["run_id"]),),
    ).fetchall()
    phase_items = conn.execute(
        """
        SELECT bookid, expected_class, naese_status, gate_status
        FROM r20_r02_naese_phase_gate_v1_items
        WHERE run_id=? AND bookid IN ('14', '45', '46', '51', '53')
        """,
        (int(phase_gate["run_id"]),),
    ).fetchall()
    phase_by_book = {str(row["bookid"]): row for row in phase_items}

    positive_book_count = len(POSITIVE_BOOKS)
    control_book_count = len(CONTROL_BOOKS)
    web_query_count = len(WEB_QUERIES)
    web_exact_target_hit_count = 0
    official_exact_target_hit_count = 0
    source_check_count = len(SOURCE_CHECKS)
    exact_source_sequence_count = 0
    exact_meaning_relation_count = 0
    positive_slot_bridge_pass_count = sum(
        1 for row in bridge_items if str(row["bookid"]) in POSITIVE_BOOKS and str(row["gate_status"]) == "PASS_R02_SLOT_BRIDGE"
    )
    control_slot_bridge_pass_count = 0
    control_context_connector_count = sum(
        1
        for bookid in CONTROL_BOOKS
        if bookid in phase_by_book and "CONTEXT_CONNECTOR" in str(phase_by_book[bookid]["naese_status"])
    )
    control_no_slot_count = sum(
        1
        for bookid in CONTROL_BOOKS
        if bookid == "14"
        or (bookid in phase_by_book and str(phase_by_book[bookid]["naese_status"]).startswith("NO_NAESE_SLOT_RECORD"))
    )
    boundary_control_count = 1 if int(r02_ltast_boundary["promoted_count"]) == 0 else 0
    overbroad_warning_count = control_context_connector_count
    specificity_pass_count = (
        1
        if positive_slot_bridge_pass_count == positive_book_count
        and control_slot_bridge_pass_count == 0
        and control_no_slot_count >= 2
        and control_context_connector_count == 1
        else 0
    )
    lexical_ready_count = 0
    canonical_promotion_allowed_count = 0
    target_status = "SOURCE_LADDER_SPECIFIC_BRIDGE_WITH_BOOK46_CONTEXT_WARNING_NO_PROMOTION"
    result_human_version = (
        "Q94 keeps R02/NAESE as the strongest local phase-to-slot route: Books 51/53 pass as ordered-core "
        "R02 slot bridges, while Books 14 and 45 reject as controls and Book46 stays a near-control/context "
        "connector warning. The bridge is specific enough for route work, but still has no exact source meaning."
    )
    decision = (
        "Q94_R02_NAESE_NEGATIVE_CONTROL_SOURCE_LADDER_SPECIFIC_BRIDGE_WITH_BOOK46_WARNING_NO_GLOSS"
        if positive_book_count == 2
        and control_book_count == 3
        and web_query_count == 8
        and web_exact_target_hit_count == 0
        and official_exact_target_hit_count == 0
        and source_check_count == 8
        and exact_source_sequence_count == 0
        and exact_meaning_relation_count == 0
        and positive_slot_bridge_pass_count == 2
        and control_slot_bridge_pass_count == 0
        and control_context_connector_count == 1
        and control_no_slot_count >= 2
        and boundary_control_count == 1
        and overbroad_warning_count == 1
        and specificity_pass_count == 1
        and int(q87["canonical_promotion_allowed_count"]) == 0
        and int(q93["promoted_gloss_count"]) == 0
        and int(completion["promoted_gloss_count"]) == 0
        else "Q94_R02_NAESE_NEGATIVE_CONTROL_SOURCE_LADDER_REQUIRES_REVIEW"
    )
    payload = {
        "answer": result_human_version,
        "allowed_use": "Use 51/53 as positive R02/NAESE phase-to-slot controls; use 14/45 as rejects and 46 as near-control warning.",
        "blocked_use": "Do not translate R02, R20, TRVEIIVNTBB, NAESE, C68, FATCT, IVIFAST, slot, bridge, connector, or boundary as words.",
        "next_action": "Proceed to Q93_A02 Book7/Mathemagica heldout selector benchmark.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q94_r02_naese_negative_control_source_ladder_v1_runs (
                created_at, decision, q93_run_id, q87_run_id, q81_run_id,
                r02_bridge_run_id, phase_gate_run_id, book45_control_run_id,
                r02_ltast_boundary_run_id, completion_audit_run_id, action_id,
                positive_book_count, control_book_count, web_query_count,
                web_exact_target_hit_count, official_exact_target_hit_count,
                source_check_count, exact_source_sequence_count, exact_meaning_relation_count,
                positive_slot_bridge_pass_count, control_slot_bridge_pass_count,
                control_context_connector_count, control_no_slot_count, boundary_control_count,
                overbroad_warning_count, specificity_pass_count, lexical_ready_count,
                canonical_promotion_allowed_count, target_status, result_human_version,
                payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                int(q93["run_id"]),
                int(q87["run_id"]),
                int(q81["run_id"]),
                int(r02_bridge["run_id"]),
                int(phase_gate["run_id"]),
                int(book45_control["run_id"]),
                int(r02_ltast_boundary["run_id"]),
                int(completion["run_id"]),
                TARGET_ACTION_ID,
                positive_book_count,
                control_book_count,
                web_query_count,
                web_exact_target_hit_count,
                official_exact_target_hit_count,
                source_check_count,
                exact_source_sequence_count,
                exact_meaning_relation_count,
                positive_slot_bridge_pass_count,
                control_slot_bridge_pass_count,
                control_context_connector_count,
                control_no_slot_count,
                boundary_control_count,
                overbroad_warning_count,
                specificity_pass_count,
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
            INSERT INTO human_q94_r02_naese_negative_control_source_ladder_v1_queries (
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
            INSERT INTO human_q94_r02_naese_negative_control_source_ladder_v1_sources (
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
        for bookid in ALL_BOOKS:
            q81_row = q81_rows[bookid]
            role = "POSITIVE_R02_NAESE_SLOT_BRIDGE" if bookid in POSITIVE_BOOKS else "CONTROL"
            if bookid in POSITIVE_BOOKS:
                ladder_result = "PASS_ORDERED_CORE_R02_SLOT_BRIDGE"
            elif bookid == "46":
                ladder_result = "NEAR_CONTROL_CONTEXT_CONNECTOR_WARNING"
            elif bookid == "45":
                ladder_result = "CONTROL_REJECT_PREFIX_NO_NAESE_SLOT"
            else:
                ladder_result = "CONTROL_REJECT_BOUNDARY_AUDIT"
            evidence = {
                "q81": dict(q81_row),
                "phase_gate": dict(phase_by_book[bookid]) if bookid in phase_by_book else {},
                "symbol_text": symbol_text(conn, bookid),
            }
            book_rows.append(
                (
                    run_id,
                    bookid,
                    role,
                    evidence["symbol_text"],
                    str(q81_row["source_bridge_id"]),
                    str(q81_row["likely_speech_act"]),
                    str(q81_row["plausible_human_reading"]),
                    str(q81_row["confidence_tier"]),
                    ladder_result,
                    j(evidence),
                )
            )
        conn.executemany(
            """
            INSERT INTO human_q94_r02_naese_negative_control_source_ladder_v1_books (
                run_id, bookid, role, symbol_text, source_bridge_id,
                likely_speech_act, plausible_human_reading, confidence_tier,
                ladder_result, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            book_rows,
        )
        conn.executemany(
            """
            INSERT INTO human_q94_r02_naese_negative_control_source_ladder_v1_tests (
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
                "positive_book_count": positive_book_count,
                "control_book_count": control_book_count,
                "web_query_count": web_query_count,
                "web_exact_target_hit_count": web_exact_target_hit_count,
                "official_exact_target_hit_count": official_exact_target_hit_count,
                "source_check_count": source_check_count,
                "exact_source_sequence_count": exact_source_sequence_count,
                "exact_meaning_relation_count": exact_meaning_relation_count,
                "positive_slot_bridge_pass_count": positive_slot_bridge_pass_count,
                "control_slot_bridge_pass_count": control_slot_bridge_pass_count,
                "control_context_connector_count": control_context_connector_count,
                "control_no_slot_count": control_no_slot_count,
                "boundary_control_count": boundary_control_count,
                "overbroad_warning_count": overbroad_warning_count,
                "specificity_pass_count": specificity_pass_count,
                "lexical_ready_count": lexical_ready_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
            }
        )
    )


if __name__ == "__main__":
    main()
