#!/usr/bin/env python3
"""Q68: execute Q67 BENNA/mathemagic operator source check."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

PROBE_ID = "Q67_P03_BENNA_FORMULA_MATHEMAGIC_OPERATOR"
SOURCE_FACTS = [
    {
        "source_id": "AWB_469_LANGUAGE_MATHEMAGIC",
        "source_url": "https://tibia.fandom.com/wiki/A_Wrinkled_Bonelord/Transcripts",
        "observed_claim": (
            "A Wrinkled Bonelord links 469 to mathemagic, says numbers are essential, "
            "treats Tibia as 1, and describes the race name as a changing complex formula."
        ),
        "operator_support": "STRONG_METHOD_SUPPORT",
        "benna_sequence_support": "NO_EXACT_BENNA_SEQUENCE",
        "lexical_support": "NO_BENNA_LEXICAL_SUPPORT",
        "blocked_inference": "Do not infer BENNA meaning from mathemagic/formula vocabulary alone.",
    },
    {
        "source_id": "BEWARE_LANGUAGE_MATH_NUMERIC_BOOKS",
        "source_url": "https://www.tibiawiki.com.br/wiki/Beware_of_the_Bonelords%21_%28Book%29",
        "observed_claim": (
            "Beware of the Bonelords frames Bonelord language as eye-blink code, language plus mathematics, "
            "and books made only of numbers."
        ),
        "operator_support": "STRONG_REGISTER_SUPPORT",
        "benna_sequence_support": "NO_EXACT_BENNA_SEQUENCE",
        "lexical_support": "NO_BENNA_LEXICAL_SUPPORT",
        "blocked_inference": "Do not translate BENNA or formula handoff from broad language/mathematics lore.",
    },
    {
        "source_id": "PARADOX_1_PLUS_1_KEYS",
        "source_url": "https://tibia.fandom.com/wiki/The_Paradox_Tower_Quest/Spoiler",
        "observed_claim": (
            "Paradox Tower makes mathemagics operational through a player-specific number for 1+1, "
            "then requires that number as a quest answer."
        ),
        "operator_support": "STRONG_OPERATOR_CONTEXT_SUPPORT",
        "benna_sequence_support": "NO_EXACT_BENNA_SEQUENCE",
        "lexical_support": "NO_BENNA_LEXICAL_SUPPORT",
        "blocked_inference": "Do not use 1+1 answers or Paradox keys as a BENNA dictionary.",
    },
]

TEST_SPECS = [
    {
        "test_id": "Q68_T01_EXACT_BENNA_SEQUENCE",
        "requirement": "A source must provide an exact BENNA-bearing sequence or directly identify the sequence.",
        "observed_result": "No checked source names BENNA or an exact BENNA-bearing 469 sequence.",
        "test_status": "FAILS_LEXICAL_PROMOTION_REQUIREMENT",
    },
    {
        "test_id": "Q68_T02_REPEATABLE_OPERATOR_RULE",
        "requirement": "A rule must predict Book35/10 BENNA formula handoff while failing Book5/31/57 controls.",
        "observed_result": "Sources support mathemagic/operator mode, but no rule predicts the Q63 target-control split.",
        "test_status": "FAILS_OPERATOR_PROMOTION_REQUIREMENT",
    },
    {
        "test_id": "Q68_T03_PARADOX_KEY_CONTAINMENT",
        "requirement": "Paradox 1+1 values must remain method/operator evidence unless they predict BENNA role.",
        "observed_result": "Paradox gives a quest-specific answer mechanism, not a BENNA-specific lexical mapping.",
        "test_status": "PASSES_FIREWALL_NO_DICTIONARY",
    },
    {
        "test_id": "Q68_T04_BOOK5_NEGATIVE_CONTROL",
        "requirement": "Any BENNA operator claim must explain why Book5 blocks handoff promotion.",
        "observed_result": "No checked source explains Book5 as a negative control or predicts its residual/template behavior.",
        "test_status": "FAILS_CONTROL_PREDICTION_REQUIREMENT",
    },
]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q68_benna_mathemagic_operator_check_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q67_run_id INTEGER NOT NULL,
            q66_run_id INTEGER NOT NULL,
            q63_run_id INTEGER NOT NULL,
            q55_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            probe_id TEXT NOT NULL,
            source_check_count INTEGER NOT NULL,
            operator_support_source_count INTEGER NOT NULL,
            exact_benna_sequence_source_count INTEGER NOT NULL,
            repeatable_operator_rule_count INTEGER NOT NULL,
            control_prediction_count INTEGER NOT NULL,
            firewall_pass_count INTEGER NOT NULL,
            lexical_ready_count INTEGER NOT NULL,
            direct_gloss_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            result_human_version TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q68_benna_mathemagic_operator_check_v1_sources (
            run_id INTEGER NOT NULL,
            source_id TEXT NOT NULL,
            source_url TEXT NOT NULL,
            observed_claim TEXT NOT NULL,
            operator_support TEXT NOT NULL,
            benna_sequence_support TEXT NOT NULL,
            lexical_support TEXT NOT NULL,
            blocked_inference TEXT NOT NULL,
            source_status TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, source_id)
        );

        CREATE TABLE IF NOT EXISTS human_q68_benna_mathemagic_operator_check_v1_tests (
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


def latest_q63_role(conn: sqlite3.Connection, q63_run_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT
            bookid,
            book_class,
            benna_bridge_decision,
            benna_functional_class,
            benna_role_status,
            benna_dominant_role,
            q59_route_role,
            role_verdict
        FROM human_q63_benna_formula_handoff_directional_contrast_v1_books
        WHERE run_id=?
        ORDER BY bookid
        """,
        (q63_run_id,),
    ).fetchall()


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q67 = latest_row(conn, "human_q67_lexical_anchor_probe_queue_v1_runs")
    q66 = latest_row(conn, "human_q66_component_role_ledger_v1_runs")
    q63 = latest_row(conn, "human_q63_benna_formula_handoff_directional_contrast_v1_runs")
    q55 = latest_row(conn, "human_q55_source_parallel_audit_q54_v1_runs")
    audit = latest_row(conn, "human_translation_completion_audit_v5_runs")
    probe = latest_probe(conn, int(q67["run_id"]))
    q63_books = latest_q63_role(conn, int(q63["run_id"]))

    source_check_count = len(SOURCE_FACTS)
    operator_support_source_count = sum(1 for source in SOURCE_FACTS if "SUPPORT" in source["operator_support"])
    exact_benna_sequence_source_count = sum(1 for source in SOURCE_FACTS if source["benna_sequence_support"] != "NO_EXACT_BENNA_SEQUENCE")
    repeatable_operator_rule_count = 0
    control_prediction_count = 0
    firewall_pass_count = sum(1 for test in TEST_SPECS if test["test_status"].startswith("PASSES_FIREWALL"))
    lexical_ready_count = 0
    direct_gloss_count = 0
    canonical_promotion_allowed_count = 0
    result_human_version = (
        "Q68 accepts Mathemagica as strong method/operator pressure for BENNA formula-handoff searches, "
        "but rejects lexical promotion: no checked source provides an exact BENNA sequence, no repeatable "
        "operator predicts Book35/10 against Book5/31/57 controls, and Paradox 1+1 values remain contained."
    )
    decision = (
        "Q68_BENNA_MATHEMAGIC_OPERATOR_CHECK_METHOD_SUPPORT_NO_LEXICAL_PROMOTION"
        if source_check_count == 3
        and operator_support_source_count == 3
        and exact_benna_sequence_source_count == 0
        and repeatable_operator_rule_count == 0
        and control_prediction_count == 0
        and firewall_pass_count == 1
        and int(q63["functional_role_accept_count"]) == 1
        and int(q63["lexical_ready_count"]) == 0
        and int(q67["lexical_ready_count"]) == 0
        and int(q66["canonical_promotion_allowed_count"]) == 0
        and int(audit["promoted_gloss_count"]) == 0
        and lexical_ready_count == 0
        and direct_gloss_count == 0
        and canonical_promotion_allowed_count == 0
        else "Q68_BENNA_MATHEMAGIC_OPERATOR_CHECK_REQUIRES_REVIEW"
    )
    payload = {
        "question": "Can Mathemagica promote BENNA formula-handoff into a lexical/operator rule?",
        "answer": result_human_version,
        "probe": dict(probe),
        "q63_books": [dict(row) for row in q63_books],
        "blocked_use": "Do not promote BENNA meaning or use Paradox values as a dictionary.",
        "next_action": "Either find an exact BENNA-bearing source relation or move to Book27 stop-vs-continuation.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q68_benna_mathemagic_operator_check_v1_runs (
                created_at, decision, q67_run_id, q66_run_id, q63_run_id,
                q55_run_id, completion_audit_run_id, probe_id,
                source_check_count, operator_support_source_count,
                exact_benna_sequence_source_count, repeatable_operator_rule_count,
                control_prediction_count, firewall_pass_count,
                lexical_ready_count, direct_gloss_count,
                canonical_promotion_allowed_count, result_human_version,
                payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                int(q67["run_id"]),
                int(q66["run_id"]),
                int(q63["run_id"]),
                int(q55["run_id"]),
                int(audit["run_id"]),
                PROBE_ID,
                source_check_count,
                operator_support_source_count,
                exact_benna_sequence_source_count,
                repeatable_operator_rule_count,
                control_prediction_count,
                firewall_pass_count,
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
            INSERT INTO human_q68_benna_mathemagic_operator_check_v1_sources (
                run_id, source_id, source_url, observed_claim,
                operator_support, benna_sequence_support, lexical_support,
                blocked_inference, source_status, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    source["source_id"],
                    source["source_url"],
                    source["observed_claim"],
                    source["operator_support"],
                    source["benna_sequence_support"],
                    source["lexical_support"],
                    source["blocked_inference"],
                    "METHOD_SUPPORT_ONLY_NO_LEXICAL_PROMOTION",
                    j(source),
                )
                for source in SOURCE_FACTS
            ],
        )
        conn.executemany(
            """
            INSERT INTO human_q68_benna_mathemagic_operator_check_v1_tests (
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
                "operator_support_source_count": operator_support_source_count,
                "exact_benna_sequence_source_count": exact_benna_sequence_source_count,
                "repeatable_operator_rule_count": repeatable_operator_rule_count,
                "control_prediction_count": control_prediction_count,
                "firewall_pass_count": firewall_pass_count,
                "lexical_ready_count": lexical_ready_count,
                "direct_gloss_count": direct_gloss_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
            }
        )
    )


if __name__ == "__main__":
    main()
