#!/usr/bin/env python3
"""Q79: execute Q67 global source firewall negative control."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

PROBE_ID = "Q67_P06_GLOBAL_SOURCE_FIREWALL_NEGATIVE_CONTROL"

FIREWALL_CANDIDATES = [
    {
        "candidate_id": "Q79_C01_BENNA_MATHEMAGIC",
        "source_layer": "Q68",
        "claim_type": "MATHEMAGIC_OPERATOR",
        "candidate_use": "method/operator pressure for BENNA formula handoff",
        "exact_source_sequence": 0,
        "exact_meaning_relation": 0,
        "allowed_layer": "SHADOW_METHOD_ONLY",
        "firewall_result": "BLOCK_CANONICAL_PROMOTION_METHOD_ONLY",
    },
    {
        "candidate_id": "Q79_C02_BOOK27_STOP_CONTINUE",
        "source_layer": "Q69_Q73_Q74",
        "claim_type": "STRUCTURAL_MISSING_EDGE",
        "candidate_use": "27->67 as a missing-edge candidate for Book27 continuation",
        "exact_source_sequence": 0,
        "exact_meaning_relation": 0,
        "allowed_layer": "SHADOW_STRUCTURAL_CANDIDATE_ONLY",
        "firewall_result": "BLOCK_CANONICAL_PROMOTION_UNCONFIRMED_EDGE",
    },
    {
        "candidate_id": "Q79_C03_C68_NAESE_SLOT",
        "source_layer": "Q75",
        "claim_type": "FUNCTIONAL_SLOT_ROLE",
        "candidate_use": "C68/NAESE as slot/classifier role",
        "exact_source_sequence": 0,
        "exact_meaning_relation": 0,
        "allowed_layer": "SHADOW_FUNCTIONAL_ROLE_ONLY",
        "firewall_result": "BLOCK_CANONICAL_PROMOTION_NO_DICTIONARY",
    },
    {
        "candidate_id": "Q79_C04_C86_VNCTIIN_CONTEXT",
        "source_layer": "Q76",
        "claim_type": "FUNCTIONAL_CONTEXT_ROUTE",
        "candidate_use": "C86/VNCTIIN as context-route role with command/research register",
        "exact_source_sequence": 0,
        "exact_meaning_relation": 0,
        "allowed_layer": "SHADOW_FUNCTIONAL_ROLE_ONLY",
        "firewall_result": "BLOCK_CANONICAL_PROMOTION_NO_DICTIONARY",
    },
    {
        "candidate_id": "Q79_C05_EDGE_67_2_PATH",
        "source_layer": "Q78",
        "claim_type": "PHRASE_PATH_SOURCE_CONTINUITY",
        "candidate_use": "35->67->2 as a source-compatible packet/phrase path",
        "exact_source_sequence": 0,
        "exact_meaning_relation": 0,
        "allowed_layer": "SHADOW_PACKET_PATH_ONLY",
        "firewall_result": "BLOCK_SENTENCE_TRANSLATION_NO_EXACT_PHRASE",
    },
]

FIREWALL_TESTS = [
    {
        "test_id": "Q79_T01_EXACT_SOURCE_SEQUENCE_REQUIREMENT",
        "test_class": "PROMOTION_REQUIREMENT",
        "test_result": "FAILS_FOR_ALL_CANDIDATES_BLOCKS_PROMOTION",
        "interpretation": "No candidate supplies exact source sequence plus source-provided meaning.",
    },
    {
        "test_id": "Q79_T02_REGISTER_NOT_DICTIONARY",
        "test_class": "SOURCE_OVERREACH_CONTROL",
        "test_result": "PASSES_FIREWALL",
        "interpretation": "Threat, Beware, Great Calculator, and Mathemagica references constrain register/method only.",
    },
    {
        "test_id": "Q79_T03_STRUCTURAL_NOT_PLAINTEXT",
        "test_class": "STRUCTURAL_OVERREACH_CONTROL",
        "test_result": "PASSES_FIREWALL",
        "interpretation": "Accepted edges and contigs stay structural/shadow unless exact phrase evidence appears.",
    },
    {
        "test_id": "Q79_T04_CONTROL_FAILURES_REQUIRED",
        "test_class": "CONTRAST_CONTROL_REQUIREMENT",
        "test_result": "PASSES_FIREWALL",
        "interpretation": "C86/C68 roles, 67->2, and 27->67 keep explicit controls and failed controls.",
    },
    {
        "test_id": "Q79_T05_COMPLETION_AUDIT_PROMOTED_GLOSS_ZERO",
        "test_class": "COMPLETION_AUDIT_CONTROL",
        "test_result": "PASSES_FIREWALL",
        "interpretation": "The completion audit still reports zero promoted glosses.",
    },
]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q79_global_source_firewall_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q67_run_id INTEGER NOT NULL,
            q77_run_id INTEGER NOT NULL,
            q78_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            probe_id TEXT NOT NULL,
            candidate_count INTEGER NOT NULL,
            candidate_blocked_promotion_count INTEGER NOT NULL,
            exact_source_sequence_count INTEGER NOT NULL,
            exact_meaning_relation_count INTEGER NOT NULL,
            allowed_shadow_candidate_count INTEGER NOT NULL,
            test_count INTEGER NOT NULL,
            passing_firewall_test_count INTEGER NOT NULL,
            failing_promotion_requirement_count INTEGER NOT NULL,
            lexical_ready_count INTEGER NOT NULL,
            direct_gloss_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            firewall_human_version TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q79_global_source_firewall_v1_candidates (
            run_id INTEGER NOT NULL,
            candidate_id TEXT NOT NULL,
            source_layer TEXT NOT NULL,
            claim_type TEXT NOT NULL,
            candidate_use TEXT NOT NULL,
            exact_source_sequence INTEGER NOT NULL,
            exact_meaning_relation INTEGER NOT NULL,
            allowed_layer TEXT NOT NULL,
            firewall_result TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, candidate_id)
        );

        CREATE TABLE IF NOT EXISTS human_q79_global_source_firewall_v1_sources (
            run_id INTEGER NOT NULL,
            source_id TEXT NOT NULL,
            source_role TEXT NOT NULL,
            source_parallel_use TEXT NOT NULL,
            blocked_inference TEXT NOT NULL,
            source_use_status TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, source_id)
        );

        CREATE TABLE IF NOT EXISTS human_q79_global_source_firewall_v1_tests (
            run_id INTEGER NOT NULL,
            test_id TEXT NOT NULL,
            test_class TEXT NOT NULL,
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


def q67_probe(conn: sqlite3.Connection, q67_run_id: int) -> sqlite3.Row:
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


def q67_sources(conn: sqlite3.Connection, q67_run_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT *
        FROM human_q67_lexical_anchor_probe_queue_v1_sources
        WHERE run_id=?
        ORDER BY source_id
        """,
        (q67_run_id,),
    ).fetchall()


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q67 = latest_row(conn, "human_q67_lexical_anchor_probe_queue_v1_runs")
    q77 = latest_row(conn, "human_q77_high_priority_probe_synthesis_v1_runs")
    q78 = latest_row(conn, "human_q78_edge_67_2_source_continuity_v1_runs")
    audit = latest_row(conn, "human_translation_completion_audit_v5_runs")
    probe = q67_probe(conn, int(q67["run_id"]))
    sources = q67_sources(conn, int(q67["run_id"]))

    candidate_count = len(FIREWALL_CANDIDATES)
    candidate_blocked_promotion_count = sum(
        1 for row in FIREWALL_CANDIDATES if row["firewall_result"].startswith("BLOCK_")
    )
    exact_source_sequence_count = sum(int(row["exact_source_sequence"]) for row in FIREWALL_CANDIDATES)
    exact_meaning_relation_count = sum(int(row["exact_meaning_relation"]) for row in FIREWALL_CANDIDATES)
    allowed_shadow_candidate_count = sum(1 for row in FIREWALL_CANDIDATES if row["allowed_layer"].startswith("SHADOW_"))
    test_count = len(FIREWALL_TESTS)
    passing_firewall_test_count = sum(1 for row in FIREWALL_TESTS if row["test_result"].endswith("FIREWALL"))
    failing_promotion_requirement_count = sum(1 for row in FIREWALL_TESTS if row["test_result"].startswith("FAILS_"))
    lexical_ready_count = 0
    direct_gloss_count = 0
    canonical_promotion_allowed_count = 0
    firewall_human_version = (
        "Q79 global source firewall closes the Q67 queue: the current candidates can be used as "
        "human-shadow method, structural, functional, or packet-path readings, but none has the "
        "exact in-game sequence-plus-meaning relation required for lexical or canonical promotion."
    )
    decision = (
        "Q79_GLOBAL_SOURCE_FIREWALL_PASS_BLOCKS_ALL_PROMOTIONS_NO_GLOSS"
        if str(probe["probe_id"]) == PROBE_ID
        and candidate_count == 5
        and candidate_blocked_promotion_count == 5
        and exact_source_sequence_count == 0
        and exact_meaning_relation_count == 0
        and allowed_shadow_candidate_count == 5
        and test_count == 5
        and passing_firewall_test_count == 4
        and failing_promotion_requirement_count == 1
        and int(q77["canonical_promotion_allowed_count"]) == 0
        and int(q78["canonical_promotion_allowed_count"]) == 0
        and int(audit["promoted_gloss_count"]) == 0
        else "Q79_GLOBAL_SOURCE_FIREWALL_REQUIRES_REVIEW"
    )
    payload = {
        "question": str(probe["search_question"]),
        "answer": firewall_human_version,
        "required_evidence": str(probe["required_evidence"]),
        "rejection_rule": str(probe["rejection_rule"]),
        "next_action": "Build the next human-readable shadow packet around 35->67->2 and heldout 27->67, clearly marked as non-canonical.",
        "blocked_use": "No candidate from Q67-Q78 may be reported as source-backed plaintext.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q79_global_source_firewall_v1_runs (
                created_at, decision, q67_run_id, q77_run_id, q78_run_id,
                completion_audit_run_id, probe_id, candidate_count,
                candidate_blocked_promotion_count, exact_source_sequence_count,
                exact_meaning_relation_count, allowed_shadow_candidate_count,
                test_count, passing_firewall_test_count,
                failing_promotion_requirement_count, lexical_ready_count,
                direct_gloss_count, canonical_promotion_allowed_count,
                firewall_human_version, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                int(q67["run_id"]),
                int(q77["run_id"]),
                int(q78["run_id"]),
                int(audit["run_id"]),
                PROBE_ID,
                candidate_count,
                candidate_blocked_promotion_count,
                exact_source_sequence_count,
                exact_meaning_relation_count,
                allowed_shadow_candidate_count,
                test_count,
                passing_firewall_test_count,
                failing_promotion_requirement_count,
                lexical_ready_count,
                direct_gloss_count,
                canonical_promotion_allowed_count,
                firewall_human_version,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q79_global_source_firewall_v1_candidates (
                run_id, candidate_id, source_layer, claim_type, candidate_use,
                exact_source_sequence, exact_meaning_relation, allowed_layer,
                firewall_result, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    row["candidate_id"],
                    row["source_layer"],
                    row["claim_type"],
                    row["candidate_use"],
                    int(row["exact_source_sequence"]),
                    int(row["exact_meaning_relation"]),
                    row["allowed_layer"],
                    row["firewall_result"],
                    j(row),
                )
                for row in FIREWALL_CANDIDATES
            ],
        )
        conn.executemany(
            """
            INSERT INTO human_q79_global_source_firewall_v1_sources (
                run_id, source_id, source_role, source_parallel_use,
                blocked_inference, source_use_status, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    str(row["source_id"]),
                    str(row["source_role"]),
                    str(row["source_parallel_use"]),
                    str(row["blocked_inference"]),
                    str(row["source_use_status"]),
                    j(dict(row)),
                )
                for row in sources
            ],
        )
        conn.executemany(
            """
            INSERT INTO human_q79_global_source_firewall_v1_tests (
                run_id, test_id, test_class, test_result,
                interpretation, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    row["test_id"],
                    row["test_class"],
                    row["test_result"],
                    row["interpretation"],
                    j(row),
                )
                for row in FIREWALL_TESTS
            ],
        )

    print(
        j(
            {
                "run_id": run_id,
                "decision": decision,
                "probe_id": PROBE_ID,
                "candidate_count": candidate_count,
                "candidate_blocked_promotion_count": candidate_blocked_promotion_count,
                "exact_source_sequence_count": exact_source_sequence_count,
                "exact_meaning_relation_count": exact_meaning_relation_count,
                "allowed_shadow_candidate_count": allowed_shadow_candidate_count,
                "passing_firewall_test_count": passing_firewall_test_count,
                "failing_promotion_requirement_count": failing_promotion_requirement_count,
                "lexical_ready_count": lexical_ready_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
            }
        )
    )


if __name__ == "__main__":
    main()
