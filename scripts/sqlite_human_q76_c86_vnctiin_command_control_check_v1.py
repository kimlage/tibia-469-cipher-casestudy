#!/usr/bin/env python3
"""Q76: execute Q67 C86/VNCTIIN command-control exact-source check."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
PROBE_ID = "Q67_P02_C86_VNCTIIN_CONTEXT_COMMAND_CONTROL"

WEB_QUERIES = [
    '"VNCTIIN" "Tibia"',
    '"CEVIEFIINI" "Tibia"',
    '"EVIEFIIN" "Tibia" "Bonelord"',
    '"C86" "VNCTIIN" "Bonelord"',
]

SOURCE_FACTS = [
    {
        "source_id": "THREAT_I_EYESTALK_MAGIC_COMMAND_DEAD",
        "source_url": "https://www.tibiawiki.com.br/wiki/The_Bonelord_Threat_I_%28Book%29",
        "observed_claim": (
            "Threat I supports a command/control register: Bonelords use eyestalk magic, necromancy, "
            "and undead legions as commanded forces."
        ),
        "register_support": "COMMAND_CONTROL_NECROMANCY_REGISTER_SUPPORT",
        "exact_c86_vnctiin_sequence_support": "NO_EXACT_C86_VNCTIIN_SEQUENCE",
        "mechanical_value_support": "NO_CONTEXT_ROUTE_MECHANICAL_VALUE",
        "lexical_support": "NO_C86_VNCTIIN_LEXICAL_SUPPORT",
        "blocked_inference": "Do not translate C86/VNCTIIN as command, dead, eye, necromancy, or victory.",
    },
    {
        "source_id": "THREAT_II_RESEARCH_EXPERIMENTS",
        "source_url": "https://tibia.fandom.com/wiki/The_Bonelord_Threat_II_%28Book%29",
        "observed_claim": (
            "Threat II supports research/experiment register after Bonelord decline, especially efforts "
            "to improve innate powers and master undead."
        ),
        "register_support": "RESEARCH_EXPERIMENT_REGISTER_SUPPORT",
        "exact_c86_vnctiin_sequence_support": "NO_EXACT_C86_VNCTIIN_SEQUENCE",
        "mechanical_value_support": "NO_CONTEXT_ROUTE_MECHANICAL_VALUE",
        "lexical_support": "NO_C86_VNCTIIN_LEXICAL_SUPPORT",
        "blocked_inference": "Do not translate C86/VNCTIIN as research, experiment, power, undead mastery, payload, or context.",
    },
]

TEST_SPECS = [
    {
        "test_id": "Q76_T01_EXACT_C86_VNCTIIN_WEB_HIT",
        "requirement": "Find an exact external occurrence of C86/VNCTIIN-bearing sequence tied to meaning.",
        "observed_result": "Exact web queries for VNCTIIN, CEVIEFIINI, EVIEFIIN, and C86/VNCTIIN returned no exact source hit.",
        "test_status": "FAILS_EXACT_SOURCE_REQUIREMENT",
    },
    {
        "test_id": "Q76_T02_THREAT_I_COMMAND_FIREWALL",
        "requirement": "Threat I may support command/control register but not direct C86/VNCTIIN terms.",
        "observed_result": "Threat I supports command/control/necromancy register only; no exact C86/VNCTIIN phrase-plus-meaning relation.",
        "test_status": "PASSES_COMMAND_FIREWALL_NO_DICTIONARY",
    },
    {
        "test_id": "Q76_T03_THREAT_II_RESEARCH_FIREWALL",
        "requirement": "Threat II may support research/experiment register but not direct C86/VNCTIIN terms.",
        "observed_result": "Threat II supports research/experiment register only; no context-route mechanical value.",
        "test_status": "PASSES_RESEARCH_FIREWALL_NO_DICTIONARY",
    },
    {
        "test_id": "Q76_T04_Q62_READY_VS_AUDIT_PRESERVED",
        "requirement": "Q62 ready-vs-audit role must stay functional-only if no exact source is found.",
        "observed_result": "Q62 accepted context-route role with lexical_ready=0 and direct_gloss=0.",
        "test_status": "PASSES_FUNCTIONAL_ROLE_PRESERVED_NO_GLOSS",
    },
    {
        "test_id": "Q76_T05_SURFACE_AUDIT_CONTROLS_BLOCK_OVERREACH",
        "requirement": "C86/VNCTIIN-like surfaces must not promote if audit controls fail ready route.",
        "observed_result": "Books 5/31/42/57 remain audit/phase/surface controls, while 2/10/27/35/67 are ready route targets.",
        "test_status": "PASSES_AUDIT_CONTROL_FIREWALL",
    },
]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q76_c86_vnctiin_command_control_check_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q67_run_id INTEGER NOT NULL,
            q62_run_id INTEGER NOT NULL,
            q55_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            probe_id TEXT NOT NULL,
            web_query_count INTEGER NOT NULL,
            exact_context_web_hit_count INTEGER NOT NULL,
            source_check_count INTEGER NOT NULL,
            register_support_source_count INTEGER NOT NULL,
            exact_c86_vnctiin_sequence_source_count INTEGER NOT NULL,
            context_route_mechanical_value_count INTEGER NOT NULL,
            firewall_pass_count INTEGER NOT NULL,
            functional_role_preserved_count INTEGER NOT NULL,
            ready_target_count INTEGER NOT NULL,
            audit_control_count INTEGER NOT NULL,
            lexical_ready_count INTEGER NOT NULL,
            direct_gloss_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            result_human_version TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q76_c86_vnctiin_command_control_check_v1_sources (
            run_id INTEGER NOT NULL,
            source_id TEXT NOT NULL,
            source_url TEXT NOT NULL,
            observed_claim TEXT NOT NULL,
            register_support TEXT NOT NULL,
            exact_c86_vnctiin_sequence_support TEXT NOT NULL,
            mechanical_value_support TEXT NOT NULL,
            lexical_support TEXT NOT NULL,
            blocked_inference TEXT NOT NULL,
            source_status TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, source_id)
        );

        CREATE TABLE IF NOT EXISTS human_q76_c86_vnctiin_command_control_check_v1_tests (
            run_id INTEGER NOT NULL,
            test_id TEXT NOT NULL,
            requirement TEXT NOT NULL,
            observed_result TEXT NOT NULL,
            test_status TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, test_id)
        );

        CREATE TABLE IF NOT EXISTS human_q76_c86_vnctiin_command_control_check_v1_queries (
            run_id INTEGER NOT NULL,
            query_id TEXT NOT NULL,
            query_text TEXT NOT NULL,
            exact_context_web_hit_count INTEGER NOT NULL,
            query_status TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, query_id)
        );
        """
    )


def latest_row(conn: sqlite3.Connection, table: str) -> sqlite3.Row:
    row = conn.execute(f"SELECT * FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    if row is None:
        raise RuntimeError(f"missing required row: {table}")
    return row


def q62_counts(conn: sqlite3.Connection, q62_run_id: int) -> tuple[int, int]:
    rows = conn.execute(
        """
        SELECT book_class
        FROM human_q62_c86_vnctiin_context_route_ready_audit_v1_books
        WHERE run_id=?
        """,
        (q62_run_id,),
    ).fetchall()
    ready = sum(1 for row in rows if "READY_CONTEXT_ROUTE_TARGET" == str(row["book_class"]))
    audit = sum(1 for row in rows if "CONTROL" in str(row["book_class"]))
    return ready, audit


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q67 = latest_row(conn, "human_q67_lexical_anchor_probe_queue_v1_runs")
    q62 = latest_row(conn, "human_q62_c86_vnctiin_context_route_ready_audit_v1_runs")
    q55 = latest_row(conn, "human_q55_source_parallel_audit_q54_v1_runs")
    audit = latest_row(conn, "human_translation_completion_audit_v5_runs")
    ready_target_count, audit_control_count = q62_counts(conn, int(q62["run_id"]))

    web_query_count = len(WEB_QUERIES)
    exact_context_web_hit_count = 0
    source_check_count = len(SOURCE_FACTS)
    register_support_source_count = 2
    exact_c86_vnctiin_sequence_source_count = 0
    context_route_mechanical_value_count = 0
    firewall_pass_count = sum(1 for test in TEST_SPECS if "FIREWALL" in test["test_status"])
    functional_role_preserved_count = 1
    lexical_ready_count = 0
    direct_gloss_count = 0
    canonical_promotion_allowed_count = 0
    result_human_version = (
        "Q76 finds strong command/control and research/experiment register support for C86/VNCTIIN context-route searches, "
        "but no exact C86/VNCTIIN-bearing source, mechanical value, or lexical gloss. Q62 remains a functional ready-vs-audit "
        "role only."
    )
    decision = (
        "Q76_C86_VNCTIIN_COMMAND_CONTROL_CHECK_REGISTER_SUPPORT_NO_EXACT_GLOSS"
        if web_query_count == 4
        and exact_context_web_hit_count == 0
        and source_check_count == 2
        and register_support_source_count == 2
        and exact_c86_vnctiin_sequence_source_count == 0
        and context_route_mechanical_value_count == 0
        and firewall_pass_count == 3
        and functional_role_preserved_count == 1
        and ready_target_count == 5
        and audit_control_count == 4
        and int(q62["functional_role_accept_count"]) == 1
        and int(q62["lexical_ready_count"]) == 0
        and int(q62["direct_gloss_count"]) == 0
        and int(q67["lexical_ready_count"]) == 0
        and int(audit["promoted_gloss_count"]) == 0
        and lexical_ready_count == 0
        and direct_gloss_count == 0
        and canonical_promotion_allowed_count == 0
        else "Q76_C86_VNCTIIN_COMMAND_CONTROL_CHECK_REQUIRES_REVIEW"
    )
    payload = {
        "question": "Is there exact source support for C86/VNCTIIN command/control or research meaning?",
        "answer": result_human_version,
        "web_queries": WEB_QUERIES,
        "blocked_use": "Do not translate C86/VNCTIIN as command, dead, eye, necromancy, research, payload, or context.",
        "next_action": "Keep Q62 as functional context-route; use Threat I/II only as register constraints for future exact-source search.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q76_c86_vnctiin_command_control_check_v1_runs (
                created_at, decision, q67_run_id, q62_run_id, q55_run_id,
                completion_audit_run_id, probe_id, web_query_count,
                exact_context_web_hit_count, source_check_count,
                register_support_source_count, exact_c86_vnctiin_sequence_source_count,
                context_route_mechanical_value_count, firewall_pass_count,
                functional_role_preserved_count, ready_target_count, audit_control_count,
                lexical_ready_count, direct_gloss_count,
                canonical_promotion_allowed_count, result_human_version,
                payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                int(q67["run_id"]),
                int(q62["run_id"]),
                int(q55["run_id"]),
                int(audit["run_id"]),
                PROBE_ID,
                web_query_count,
                exact_context_web_hit_count,
                source_check_count,
                register_support_source_count,
                exact_c86_vnctiin_sequence_source_count,
                context_route_mechanical_value_count,
                firewall_pass_count,
                functional_role_preserved_count,
                ready_target_count,
                audit_control_count,
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
            INSERT INTO human_q76_c86_vnctiin_command_control_check_v1_queries (
                run_id, query_id, query_text, exact_context_web_hit_count,
                query_status, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    f"Q76_WEB_{idx:02d}",
                    query,
                    0,
                    "NO_EXACT_CONTEXT_WEB_HIT",
                    j({"query": query, "exact_context_web_hit_count": 0}),
                )
                for idx, query in enumerate(WEB_QUERIES, start=1)
            ],
        )
        conn.executemany(
            """
            INSERT INTO human_q76_c86_vnctiin_command_control_check_v1_sources (
                run_id, source_id, source_url, observed_claim,
                register_support, exact_c86_vnctiin_sequence_support,
                mechanical_value_support, lexical_support, blocked_inference,
                source_status, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    source["source_id"],
                    source["source_url"],
                    source["observed_claim"],
                    source["register_support"],
                    source["exact_c86_vnctiin_sequence_support"],
                    source["mechanical_value_support"],
                    source["lexical_support"],
                    source["blocked_inference"],
                    "REGISTER_SUPPORT_ONLY_NO_EXACT_CONTEXT_GLOSS",
                    j(source),
                )
                for source in SOURCE_FACTS
            ],
        )
        conn.executemany(
            """
            INSERT INTO human_q76_c86_vnctiin_command_control_check_v1_tests (
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
                "web_query_count": web_query_count,
                "exact_context_web_hit_count": exact_context_web_hit_count,
                "source_check_count": source_check_count,
                "register_support_source_count": register_support_source_count,
                "exact_c86_vnctiin_sequence_source_count": exact_c86_vnctiin_sequence_source_count,
                "context_route_mechanical_value_count": context_route_mechanical_value_count,
                "firewall_pass_count": firewall_pass_count,
                "functional_role_preserved_count": functional_role_preserved_count,
                "ready_target_count": ready_target_count,
                "audit_control_count": audit_control_count,
                "lexical_ready_count": lexical_ready_count,
                "direct_gloss_count": direct_gloss_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
            }
        )
    )


if __name__ == "__main__":
    main()
