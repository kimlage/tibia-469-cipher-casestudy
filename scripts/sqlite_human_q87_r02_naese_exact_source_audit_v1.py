#!/usr/bin/env python3
"""Q87: exact-source audit for Q82 T04 R02/NAESE slot bridge."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
TARGET_ID = "Q82_T04_R02_NAESE_SLOT_BRIDGE"

WEB_QUERIES = [
    {
        "query_id": "Q87_WEB_01",
        "query_text": '"FIVNANI" "ANIVVENINTEIN"',
        "result_status": "NO_RELEVANT_EXACT_SOURCE_HIT",
        "notes": "No exact source hit for the Book51 R02 bridge prefix.",
    },
    {
        "query_id": "Q87_WEB_02",
        "query_text": '"ANIVVENINTEIN" "NAESESTIENFATCT"',
        "result_status": "NO_RELEVANT_EXACT_SOURCE_HIT",
        "notes": "No exact source tying the R02 prefix to the NAESE/C68 slot window.",
    },
    {
        "query_id": "Q87_WEB_03",
        "query_text": '"TRVEIIVNTBB" "NAESE"',
        "result_status": "NO_RELEVANT_EXACT_SOURCE_HIT",
        "notes": "No exact source hit for TRVEIIVNTBB with NAESE.",
    },
    {
        "query_id": "Q87_WEB_04",
        "query_text": '"INTEINLFSEITVAETRFEVASTFFFEEINBLEIIFFTRVEIIVNTBB"',
        "result_status": "NO_RELEVANT_EXACT_SOURCE_HIT",
        "notes": "No exact source hit for the Book53 R02/R20 bridge prefix.",
    },
    {
        "query_id": "Q87_WEB_05",
        "query_text": '"FIVNANI*ANIVVENINTEINLFSEITVAETRFEVAST"',
        "result_status": "NO_RELEVANT_EXACT_SOURCE_HIT",
        "notes": "No exact source hit for the star-delimited Book51 opening.",
    },
    {
        "query_id": "Q87_WEB_06",
        "query_text": '"ANIVVENINTEINLFSEITVAETRFEVAST" "Tibia"',
        "result_status": "NO_RELEVANT_EXACT_SOURCE_HIT",
        "notes": "No Tibia source hit for the R02/R20 phase string.",
    },
    {
        "query_id": "Q87_WEB_07",
        "query_text": '"R02" "NAESE" "Tibia"',
        "result_status": "FALSE_POSITIVES_NO_TARGET_SOURCE",
        "notes": "No target evidence for a Tibia R02/NAESE source relation.",
    },
    {
        "query_id": "Q87_WEB_08",
        "query_text": 'site:tibia.com "ANIVVENINTEIN"',
        "result_status": "NO_OFFICIAL_EXACT_HIT",
        "notes": "No official tibia.com exact hit for ANIVVENINTEIN.",
    },
]

SOURCE_CHECKS = [
    {
        "source_id": "R02_NAESE_SLOT_BRIDGE_PRIOR_GATE",
        "source_url": "sqlite:r02_naese_slot_bridge_v1_runs",
        "source_result": "STRUCTURAL_BRIDGE_PASS_NO_PROSE",
        "support_value": "Books 51/53 pass R02_TRVEIIVNTBB_TO_NAESE_SLOT_BRIDGE.",
        "blocked_inference": "The gate promotes a structural bridge only; it does not give an R02, TRVEIIVNTBB, or NAESE word meaning.",
    },
    {
        "source_id": "Q61_C68_NAESE_MINIMAL_PAIRS",
        "source_url": "sqlite:human_q61_c68_naese_slot_role_minimal_pairs_v1_runs",
        "source_result": "FUNCTIONAL_SLOT_ROLE_ACCEPTED_NO_GLOSS",
        "support_value": "Minimal pairs separate slot/classifier windows from phase/context and boundary controls.",
        "blocked_inference": "No C68, NAESE, slot, or classifier word gloss is promoted.",
    },
    {
        "source_id": "Q75_C68_NAESE_EXACT_SOURCE_CHECK",
        "source_url": "sqlite:human_q75_c68_naese_exact_source_check_v1_sources",
        "source_result": "NO_EXACT_C68_NAESE_GLOSS",
        "support_value": "Q75 blocks exact-source promotion for C68/NAESE independently.",
        "blocked_inference": "Do not map C68/NAESE to soul, mind, body, undead, monster, key, slot, or classifier as words.",
    },
    {
        "source_id": "HUMAN_R20_R02_PHASE_BRIDGE",
        "source_url": "sqlite:human_r20_r02_phase_bridge_v1_runs",
        "source_result": "PHASE_BRIDGES_READY_NO_GLOSS",
        "support_value": "R20/R02 phase material is split into bridge, connector, branch, and micro-context families.",
        "blocked_inference": "Do not collapse phase, slot, VINVIN branch, and micro-context into one prose meaning.",
    },
    {
        "source_id": "AWB_469_LANGUAGE_MATHEMAGIC",
        "source_url": "https://tibia.fandom.com/wiki/A_Wrinkled_Bonelord/Transcripts",
        "source_result": "METHOD_SUPPORT_NO_R02_NAESE_SEQUENCE",
        "support_value": "AWB supports numeric/mathemagical processing as a method constraint.",
        "blocked_inference": "Does not identify ANIVVENINTEIN, TRVEIIVNTBB, R02, or NAESE meaning.",
    },
    {
        "source_id": "THREAT_I_COMMAND_REGISTER",
        "source_url": "https://tibia.fandom.com/wiki/The_Bonelord_Threat_I_%28Book%29",
        "source_result": "COMMAND_REGISTER_SUPPORT_NO_SEQUENCE",
        "support_value": "Threat I can support a command/control register around Bonelord lore.",
        "blocked_inference": "No exact R02/NAESE sequence and no source-provided phase-to-slot meaning.",
    },
    {
        "source_id": "THREAT_III_TRANSFORMATION_REGISTER",
        "source_url": "https://www.tibiawiki.com.br/wiki/The_Bonelord_Threat_III_%28Book%29",
        "source_result": "TRANSFORMATION_REGISTER_SUPPORT_NO_SEQUENCE",
        "support_value": "Threat III supports transformation/slot/payload register pressure.",
        "blocked_inference": "Does not map R02/TRVEIIVNTBB/NAESE to soul, mind, body, monster, or formula semantics.",
    },
]

TESTS = [
    {
        "test_id": "Q87_T01_WEB_EXACT_SEQUENCE",
        "test_result": "FAILS_EXACT_SOURCE_REQUIREMENT",
        "interpretation": "No web query found exact R02/NAESE bridge sequence plus meaning/provenance.",
    },
    {
        "test_id": "Q87_T02_PRIOR_BRIDGE_GATE",
        "test_result": "PRESERVE_STRUCTURAL_BRIDGE_ONLY",
        "interpretation": "The prior R02/NAESE gate remains valid for shadow reading but not prose promotion.",
    },
    {
        "test_id": "Q87_T03_SLOT_MINIMAL_PAIRS",
        "test_result": "PRESERVE_FUNCTIONAL_SLOT_ROLE_NO_GLOSS",
        "interpretation": "Q61 supports the slot role through contrasts while blocking word-level meanings.",
    },
    {
        "test_id": "Q87_T04_LOCAL_CONTROLS",
        "test_result": "PRESERVE_CONTROLS",
        "interpretation": "Books 45/46 remain connectors and Book14 remains weak boundary audit, not clean slot proof.",
    },
    {
        "test_id": "Q87_T05_PROMOTION_FIREWALL",
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
        CREATE TABLE IF NOT EXISTS human_q87_r02_naese_exact_source_audit_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q82_run_id INTEGER NOT NULL,
            q61_run_id INTEGER NOT NULL,
            q75_run_id INTEGER NOT NULL,
            r02_gate_run_id INTEGER NOT NULL,
            r20_r02_bridge_run_id INTEGER NOT NULL,
            r20_r02_shadow_run_id INTEGER NOT NULL,
            q81_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            target_id TEXT NOT NULL,
            target_book_count INTEGER NOT NULL,
            control_book_count INTEGER NOT NULL,
            web_query_count INTEGER NOT NULL,
            web_exact_target_hit_count INTEGER NOT NULL,
            official_exact_target_hit_count INTEGER NOT NULL,
            source_check_count INTEGER NOT NULL,
            method_support_source_count INTEGER NOT NULL,
            exact_source_sequence_count INTEGER NOT NULL,
            exact_meaning_relation_count INTEGER NOT NULL,
            structural_bridge_pass_count INTEGER NOT NULL,
            slot_functional_accept_count INTEGER NOT NULL,
            lexical_ready_count INTEGER NOT NULL,
            direct_gloss_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            target_status TEXT NOT NULL,
            result_human_version TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q87_r02_naese_exact_source_audit_v1_queries (
            run_id INTEGER NOT NULL,
            query_id TEXT NOT NULL,
            query_text TEXT NOT NULL,
            result_status TEXT NOT NULL,
            notes TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, query_id)
        );

        CREATE TABLE IF NOT EXISTS human_q87_r02_naese_exact_source_audit_v1_sources (
            run_id INTEGER NOT NULL,
            source_id TEXT NOT NULL,
            source_url TEXT NOT NULL,
            source_result TEXT NOT NULL,
            support_value TEXT NOT NULL,
            blocked_inference TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, source_id)
        );

        CREATE TABLE IF NOT EXISTS human_q87_r02_naese_exact_source_audit_v1_books (
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

        CREATE TABLE IF NOT EXISTS human_q87_r02_naese_exact_source_audit_v1_controls (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            subfamily TEXT NOT NULL,
            likely_speech_act TEXT NOT NULL,
            plausible_human_reading TEXT NOT NULL,
            confidence_tier TEXT NOT NULL,
            control_result TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        );

        CREATE TABLE IF NOT EXISTS human_q87_r02_naese_exact_source_audit_v1_tests (
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


def load_controls(conn: sqlite3.Connection, shadow_run_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT *
        FROM human_r20_r02_phase_shadow_v1_items
        WHERE run_id=? AND bookid IN ('14', '45', '46')
        ORDER BY CAST(bookid AS INTEGER)
        """,
        (shadow_run_id,),
    ).fetchall()


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q82 = latest_row(conn, "human_q82_exact_source_target_queue_v1_runs")
    q61 = latest_row(conn, "human_q61_c68_naese_slot_role_minimal_pairs_v1_runs")
    q75 = latest_row(conn, "human_q75_c68_naese_exact_source_check_v1_runs")
    r02_gate = latest_row(conn, "r02_naese_slot_bridge_v1_runs")
    r20_bridge = latest_row(conn, "human_r20_r02_phase_bridge_v1_runs")
    r20_shadow = latest_row(conn, "human_r20_r02_phase_shadow_v1_runs")
    q81 = latest_row(conn, "human_q81_controlled_shadow_export_v1_runs")
    completion = latest_row(conn, "human_translation_completion_audit_v5_runs")
    target = load_target(conn, int(q82["run_id"]))
    books = load_books(conn, int(q82["run_id"]))
    controls = load_controls(conn, int(r20_shadow["run_id"]))

    target_book_count = len(books)
    control_book_count = len(controls)
    web_query_count = len(WEB_QUERIES)
    web_exact_target_hit_count = 0
    official_exact_target_hit_count = 0
    source_check_count = len(SOURCE_CHECKS)
    method_support_source_count = len(SOURCE_CHECKS)
    exact_source_sequence_count = 0
    exact_meaning_relation_count = 0
    structural_bridge_pass_count = int(r02_gate["positive_pass_count"])
    slot_functional_accept_count = int(q61["functional_role_accept_count"])
    lexical_ready_count = 0
    direct_gloss_count = 0
    canonical_promotion_allowed_count = 0
    target_status = "SOURCE_AUDITED_STRONG_STRUCTURAL_BRIDGE_NO_PROMOTION"
    result_human_version = (
        "Q87 preserves Books 51/53 as a strong R02 phase-to-NAESE/C68 slot bridge. "
        "The bridge is useful for human shadow reading and local contrast, but no checked source "
        "provides the exact R02/NAESE sequence with a source-provided meaning."
    )
    decision = (
        "Q87_R02_NAESE_EXACT_SOURCE_AUDIT_STRUCTURAL_BRIDGE_SUPPORT_NO_EXACT_SOURCE_NO_GLOSS"
        if target_book_count == 2
        and control_book_count == 3
        and web_query_count == 8
        and web_exact_target_hit_count == 0
        and official_exact_target_hit_count == 0
        and source_check_count == 7
        and exact_source_sequence_count == 0
        and exact_meaning_relation_count == 0
        and structural_bridge_pass_count == 2
        and slot_functional_accept_count == 1
        and int(q75["lexical_ready_count"]) == 0
        and int(q81["promoted_gloss_count"]) == 0
        and int(completion["promoted_gloss_count"]) == 0
        else "Q87_R02_NAESE_EXACT_SOURCE_AUDIT_REQUIRES_REVIEW"
    )
    payload = {
        "question": str(target["search_question"]),
        "answer": result_human_version,
        "acceptance_gate": str(target["acceptance_gate"]),
        "rejection_rule": str(target["rejection_rule"]),
        "local_controls": {
            "14": "weak R02/LTAST boundary audit",
            "45": "R02/R20 context connector",
            "46": "R02/R20 context connector",
        },
        "next_action": "Keep Q82 T04 as strongest phase-to-slot shadow; move to medium target Q82_T07 Book7 phase/Mathemagica route.",
        "blocked_use": "Do not translate R02, R20, TRVEIIVNTBB, ANIVVENINTEIN, C68, NAESE, FATCT, IVIFAST, slot, or bridge as words.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q87_r02_naese_exact_source_audit_v1_runs (
                created_at, decision, q82_run_id, q61_run_id, q75_run_id,
                r02_gate_run_id, r20_r02_bridge_run_id, r20_r02_shadow_run_id,
                q81_run_id, completion_audit_run_id, target_id,
                target_book_count, control_book_count, web_query_count,
                web_exact_target_hit_count, official_exact_target_hit_count,
                source_check_count, method_support_source_count,
                exact_source_sequence_count, exact_meaning_relation_count,
                structural_bridge_pass_count, slot_functional_accept_count,
                lexical_ready_count, direct_gloss_count,
                canonical_promotion_allowed_count, target_status,
                result_human_version, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                int(q82["run_id"]),
                int(q61["run_id"]),
                int(q75["run_id"]),
                int(r02_gate["run_id"]),
                int(r20_bridge["run_id"]),
                int(r20_shadow["run_id"]),
                int(q81["run_id"]),
                int(completion["run_id"]),
                TARGET_ID,
                target_book_count,
                control_book_count,
                web_query_count,
                web_exact_target_hit_count,
                official_exact_target_hit_count,
                source_check_count,
                method_support_source_count,
                exact_source_sequence_count,
                exact_meaning_relation_count,
                structural_bridge_pass_count,
                slot_functional_accept_count,
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
            INSERT INTO human_q87_r02_naese_exact_source_audit_v1_queries (
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
            INSERT INTO human_q87_r02_naese_exact_source_audit_v1_sources (
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
            INSERT INTO human_q87_r02_naese_exact_source_audit_v1_books (
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
                    "PRESERVE_R02_NAESE_PHASE_SLOT_BRIDGE_SHADOW_ONLY",
                    j(dict(row)),
                )
                for row in books
            ],
        )
        conn.executemany(
            """
            INSERT INTO human_q87_r02_naese_exact_source_audit_v1_controls (
                run_id, bookid, subfamily, likely_speech_act,
                plausible_human_reading, confidence_tier, control_result, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    str(row["bookid"]),
                    str(row["subfamily"]),
                    str(row["likely_speech_act"]),
                    str(row["plausible_human_reading"]),
                    str(row["confidence_tier"]),
                    "PRESERVE_AS_LOCAL_CONTROL_NOT_SLOT_PROOF",
                    j(dict(row)),
                )
                for row in controls
            ],
        )
        conn.executemany(
            """
            INSERT INTO human_q87_r02_naese_exact_source_audit_v1_tests (
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
                "control_book_count": control_book_count,
                "web_query_count": web_query_count,
                "web_exact_target_hit_count": web_exact_target_hit_count,
                "official_exact_target_hit_count": official_exact_target_hit_count,
                "source_check_count": source_check_count,
                "method_support_source_count": method_support_source_count,
                "exact_source_sequence_count": exact_source_sequence_count,
                "exact_meaning_relation_count": exact_meaning_relation_count,
                "structural_bridge_pass_count": structural_bridge_pass_count,
                "slot_functional_accept_count": slot_functional_accept_count,
                "lexical_ready_count": lexical_ready_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
            }
        )
    )


if __name__ == "__main__":
    main()
