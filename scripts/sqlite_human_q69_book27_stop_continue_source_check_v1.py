#!/usr/bin/env python3
"""Q69: execute Q67 Book27 stop-vs-continuation source check."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

PROBE_ID = "Q67_P05_BOOK27_STOP_VS_CONTINUATION"
SOURCE_FACTS = [
    {
        "source_id": "THREAT_I_EYESTALK_MAGIC_COMMAND_DEAD",
        "source_url": "https://www.tibiawiki.com.br/wiki/The_Bonelord_Threat_I_%28Book%29",
        "observed_claim": (
            "Threat I frames Bonelords as eyestalk magic users with command/control and dead-minion context."
        ),
        "register_support": "COMMAND_CONTROL_REGISTER_SUPPORT",
        "stop_support": "NO_EXACT_BOOK27_STOP_EVIDENCE",
        "continuation_support": "NO_EXACT_BOOK27_CONTINUATION_EVIDENCE",
        "lexical_support": "NO_BOOK27_LEXICAL_SUPPORT",
        "blocked_inference": "Do not translate Book27 as command, dead, eye, necromancy, or victory.",
    },
    {
        "source_id": "THREAT_II_RESEARCH_EXPERIMENTS",
        "source_url": "https://tibia.fandom.com/wiki/The_Bonelord_Threat_II_%28Book%29",
        "observed_claim": (
            "Threat II gives research/experiment framing for Bonelord attempts to improve or restore power."
        ),
        "register_support": "RESEARCH_EXPERIMENT_REGISTER_SUPPORT",
        "stop_support": "NO_EXACT_BOOK27_STOP_EVIDENCE",
        "continuation_support": "NO_EXACT_BOOK27_CONTINUATION_EVIDENCE",
        "lexical_support": "NO_BOOK27_LEXICAL_SUPPORT",
        "blocked_inference": "Do not turn research/experiment register into a Book27 endpoint.",
    },
    {
        "source_id": "THREAT_III_MIND_BODY_SOUL_EXPERIMENTS",
        "source_url": "https://www.tibiawiki.com.br/wiki/The_Bonelord_Threat_III_%28Book%29",
        "observed_claim": (
            "Threat III describes soul, mind, body, living/dead experiments and a creature acting without direct control."
        ),
        "register_support": "TRANSFORMATION_PAYLOAD_REGISTER_SUPPORT",
        "stop_support": "NO_EXACT_BOOK27_STOP_EVIDENCE",
        "continuation_support": "NO_EXACT_BOOK27_CONTINUATION_EVIDENCE",
        "lexical_support": "NO_BOOK27_LEXICAL_SUPPORT",
        "blocked_inference": "Do not map Book27 or C68/NAESE/C86/VNCTIIN to soul, mind, body, monster, or no-control without exact contrast.",
    },
]

TEST_SPECS = [
    {
        "test_id": "Q69_T01_EXACT_BOOK27_SEQUENCE",
        "requirement": "A source must identify Book27 or an exact Book27-bearing sequence.",
        "observed_result": "No checked Threat source identifies Book27 or its exact 469 sequence.",
        "test_status": "FAILS_STOP_CONTINUE_RESOLUTION_REQUIREMENT",
    },
    {
        "test_id": "Q69_T02_STOP_ENDPOINT_SUPPORT",
        "requirement": "A source must predict Book27 as an endpoint or completed context hold.",
        "observed_result": "The sources give register context, but no endpoint rule for Book27.",
        "test_status": "FAILS_STOP_ENDPOINT_REQUIREMENT",
    },
    {
        "test_id": "Q69_T03_MISSING_CONTINUATION_SUPPORT",
        "requirement": "A source must predict that Book27 lacks the observed 67->2 continuation.",
        "observed_result": "No checked source predicts absence or presence of the next edge.",
        "test_status": "FAILS_CONTINUATION_REQUIREMENT",
    },
    {
        "test_id": "Q69_T04_THREAT_REGISTER_FIREWALL",
        "requirement": "Threat lore may constrain register but must not become a dictionary.",
        "observed_result": "All Threat sources remain register/search support only.",
        "test_status": "PASSES_FIREWALL_NO_DICTIONARY",
    },
    {
        "test_id": "Q69_T05_Q65_HELDOUT_STATUS_PRESERVED",
        "requirement": "Q65 moderate heldout status must stay unchanged unless stop or continuation is resolved.",
        "observed_result": "Book27 remains ready context with no direct edge and stop-vs-missing-edge unresolved.",
        "test_status": "PASSES_HELDOUT_STATUS_PRESERVED",
    },
]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q69_book27_stop_continue_source_check_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q67_run_id INTEGER NOT NULL,
            q65_run_id INTEGER NOT NULL,
            q55_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            probe_id TEXT NOT NULL,
            source_check_count INTEGER NOT NULL,
            register_support_source_count INTEGER NOT NULL,
            exact_book27_sequence_source_count INTEGER NOT NULL,
            stop_resolved_count INTEGER NOT NULL,
            continuation_resolved_count INTEGER NOT NULL,
            firewall_pass_count INTEGER NOT NULL,
            heldout_status_preserved_count INTEGER NOT NULL,
            lexical_ready_count INTEGER NOT NULL,
            direct_gloss_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            result_human_version TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q69_book27_stop_continue_source_check_v1_sources (
            run_id INTEGER NOT NULL,
            source_id TEXT NOT NULL,
            source_url TEXT NOT NULL,
            observed_claim TEXT NOT NULL,
            register_support TEXT NOT NULL,
            stop_support TEXT NOT NULL,
            continuation_support TEXT NOT NULL,
            lexical_support TEXT NOT NULL,
            blocked_inference TEXT NOT NULL,
            source_status TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, source_id)
        );

        CREATE TABLE IF NOT EXISTS human_q69_book27_stop_continue_source_check_v1_tests (
            run_id INTEGER NOT NULL,
            test_id TEXT NOT NULL,
            requirement TEXT NOT NULL,
            observed_result TEXT NOT NULL,
            test_status TEXT NOT NULL,
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


def latest_probe(conn: sqlite3.Connection, q67_run_id: int) -> sqlite3.Row:
    row = conn.execute(
        """
        SELECT *
        FROM human_q67_lexical_anchor_probe_queue_v1_probes
        WHERE run_id=? AND probe_id=?
        """,
        (q67_run_id, PROBE_ID),
    ).fetchone()
    if row is None:
        raise RuntimeError(f"missing Q67 probe: {PROBE_ID}")
    return row


def q65_book27(conn: sqlite3.Connection, q65_run_id: int) -> sqlite3.Row:
    row = conn.execute(
        """
        SELECT *
        FROM human_q65_payload_context_hold_heldout_role_v1_books
        WHERE run_id=? AND bookid='27'
        """,
        (q65_run_id,),
    ).fetchone()
    if row is None:
        raise RuntimeError("missing Q65 Book27 row")
    return row


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q67 = latest_row(conn, "human_q67_lexical_anchor_probe_queue_v1_runs")
    q65 = latest_row(conn, "human_q65_payload_context_hold_heldout_role_v1_runs")
    q55 = latest_row(conn, "human_q55_source_parallel_audit_q54_v1_runs")
    audit = latest_row(conn, "human_translation_completion_audit_v5_runs")
    probe = latest_probe(conn, int(q67["run_id"]))
    book27 = q65_book27(conn, int(q65["run_id"]))

    source_check_count = len(SOURCE_FACTS)
    register_support_source_count = sum(1 for source in SOURCE_FACTS if source["register_support"].endswith("_SUPPORT"))
    exact_book27_sequence_source_count = 0
    stop_resolved_count = 0
    continuation_resolved_count = 0
    firewall_pass_count = sum(1 for test in TEST_SPECS if test["test_status"].startswith("PASSES_FIREWALL"))
    heldout_status_preserved_count = sum(1 for test in TEST_SPECS if test["test_status"] == "PASSES_HELDOUT_STATUS_PRESERVED")
    lexical_ready_count = 0
    direct_gloss_count = 0
    canonical_promotion_allowed_count = 0
    result_human_version = (
        "Q69 keeps Book27 as a moderate payload/context-heldout: Threat I/II/III provide useful "
        "command, research, and transformation register pressure, but none gives exact Book27 sequence "
        "evidence or decides endpoint versus missing 67->2 continuation."
    )
    decision = (
        "Q69_BOOK27_STOP_CONTINUE_SOURCE_CHECK_REMAINS_OPEN_NO_GLOSS"
        if source_check_count == 3
        and register_support_source_count == 3
        and exact_book27_sequence_source_count == 0
        and stop_resolved_count == 0
        and continuation_resolved_count == 0
        and firewall_pass_count == 1
        and heldout_status_preserved_count == 1
        and int(q65["heldout_role_accept_count"]) == 1
        and int(q65["stop_continue_resolved_count"]) == 0
        and str(book27["role_verdict"]) == "HELDOUT_PAYLOAD_CONTEXT_HOLD_ACCEPT_MODERATE_ROLE"
        and int(q67["lexical_ready_count"]) == 0
        and int(audit["promoted_gloss_count"]) == 0
        and lexical_ready_count == 0
        and direct_gloss_count == 0
        and canonical_promotion_allowed_count == 0
        else "Q69_BOOK27_STOP_CONTINUE_SOURCE_CHECK_REQUIRES_REVIEW"
    )
    payload = {
        "question": "Does Book27 stop in payload/context hold, or does it lack the observed 67->2 continuation?",
        "answer": result_human_version,
        "probe": dict(probe),
        "book27": dict(book27),
        "blocked_use": "Do not translate Book27 as command, necromancy, soul, body, monster, endpoint, or punctuation.",
        "next_action": "Move from source-register search to sequence-neighbor search around Book27 and possible missing edges.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q69_book27_stop_continue_source_check_v1_runs (
                created_at, decision, q67_run_id, q65_run_id, q55_run_id,
                completion_audit_run_id, probe_id, source_check_count,
                register_support_source_count, exact_book27_sequence_source_count,
                stop_resolved_count, continuation_resolved_count,
                firewall_pass_count, heldout_status_preserved_count,
                lexical_ready_count, direct_gloss_count,
                canonical_promotion_allowed_count, result_human_version,
                payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                int(q67["run_id"]),
                int(q65["run_id"]),
                int(q55["run_id"]),
                int(audit["run_id"]),
                PROBE_ID,
                source_check_count,
                register_support_source_count,
                exact_book27_sequence_source_count,
                stop_resolved_count,
                continuation_resolved_count,
                firewall_pass_count,
                heldout_status_preserved_count,
                lexical_ready_count,
                direct_gloss_count,
                canonical_promotion_allowed_count,
                result_human_version,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q69_book27_stop_continue_source_check_v1_sources (
                run_id, source_id, source_url, observed_claim,
                register_support, stop_support, continuation_support,
                lexical_support, blocked_inference, source_status,
                evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    source["source_id"],
                    source["source_url"],
                    source["observed_claim"],
                    source["register_support"],
                    source["stop_support"],
                    source["continuation_support"],
                    source["lexical_support"],
                    source["blocked_inference"],
                    "REGISTER_SUPPORT_ONLY_STOP_CONTINUE_OPEN",
                    j(source),
                )
                for source in SOURCE_FACTS
            ],
        )
        conn.executemany(
            """
            INSERT INTO human_q69_book27_stop_continue_source_check_v1_tests (
                run_id, test_id, requirement, observed_result,
                test_status, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    test["test_id"],
                    test["requirement"],
                    test["observed_result"],
                    test["test_status"],
                    j({"test": test, "decision": decision}),
                )
                for test in TEST_SPECS
            ],
        )

    print(
        j(
            {
                "run_id": run_id,
                "decision": decision,
                "probe_id": PROBE_ID,
                "source_check_count": source_check_count,
                "register_support_source_count": register_support_source_count,
                "exact_book27_sequence_source_count": exact_book27_sequence_source_count,
                "stop_resolved_count": stop_resolved_count,
                "continuation_resolved_count": continuation_resolved_count,
                "firewall_pass_count": firewall_pass_count,
                "heldout_status_preserved_count": heldout_status_preserved_count,
                "lexical_ready_count": lexical_ready_count,
                "direct_gloss_count": direct_gloss_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
            }
        )
    )


if __name__ == "__main__":
    main()
