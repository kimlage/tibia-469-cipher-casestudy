#!/usr/bin/env python3
"""Q75: execute Q67 C68/NAESE exact-source check."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
PROBE_ID = "Q67_P01_C68_NAESE_SLOT_EXACT_SOURCE"

WEB_QUERIES = [
    '"NAESE" "Tibia" "Bonelord"',
    '"IVIFAST" "Tibia"',
    '"FATCT" "Tibia" "Bonelord"',
    '"NAESESTIENFATCT"',
]

SOURCE_FACTS = [
    {
        "source_id": "THREAT_III_MIND_BODY_SOUL_EXPERIMENTS",
        "source_url": "https://www.tibiawiki.com.br/wiki/The_Bonelord_Threat_III_%28Book%29",
        "observed_claim": (
            "Threat III supports a transformation/payload register involving souls, minds, bodies, "
            "living/dead switching, and undead experiments."
        ),
        "exact_slot_sequence_support": "NO_EXACT_C68_NAESE_SEQUENCE",
        "mechanical_value_support": "NO_SLOT_MECHANICAL_VALUE",
        "lexical_support": "NO_C68_NAESE_LEXICAL_SUPPORT",
        "blocked_inference": "Do not map NAESE/C68 to soul, mind, body, undead, monster, or transformation without exact contrast.",
    },
    {
        "source_id": "PARADOX_1_PLUS_1_KEYS",
        "source_url": "https://www.tibia-wiki.net/wiki/Paradox_Tower_Quest/Spoiler",
        "observed_claim": (
            "Paradox Tower supports contextual mathemagic/operator values such as the 1+1 answer family, "
            "but not a C68/NAESE slot dictionary."
        ),
        "exact_slot_sequence_support": "NO_EXACT_C68_NAESE_SEQUENCE",
        "mechanical_value_support": "NO_SLOT_MECHANICAL_VALUE",
        "lexical_support": "NO_C68_NAESE_LEXICAL_SUPPORT",
        "blocked_inference": "Do not use 1/13/49/94 as a C68/NAESE key unless it predicts exact slot controls.",
    },
    {
        "source_id": "S2WARD_469_SEQUENCE_METHOD",
        "source_url": "https://github.com/s2ward/469",
        "observed_claim": (
            "s2ward/469 is useful as external method pressure for sequence assembly, Hellgate books, "
            "and mathemagic references, but it is not an in-game exact gloss source for C68/NAESE."
        ),
        "exact_slot_sequence_support": "NO_EXACT_C68_NAESE_SEQUENCE",
        "mechanical_value_support": "METHOD_PRESSURE_ONLY",
        "lexical_support": "NO_C68_NAESE_LEXICAL_SUPPORT",
        "blocked_inference": "Do not use external method notes as canonical in-game anchoring or a slot glossary.",
    },
]

TEST_SPECS = [
    {
        "test_id": "Q75_T01_EXACT_NAESE_C68_WEB_HIT",
        "requirement": "Find an exact external occurrence of NAESE/C68 slot sequence tied to meaning.",
        "observed_result": "Exact web queries for NAESE, IVIFAST, FATCT, and NAESESTIENFATCT returned no exact source hit.",
        "test_status": "FAILS_EXACT_SOURCE_REQUIREMENT",
    },
    {
        "test_id": "Q75_T02_THREAT_III_REGISTER_FIREWALL",
        "requirement": "Threat III may support transformation register but not direct slot terms.",
        "observed_result": "Threat III supports register only; no exact C68/NAESE phrase-plus-meaning relation.",
        "test_status": "PASSES_REGISTER_FIREWALL_NO_DICTIONARY",
    },
    {
        "test_id": "Q75_T03_PARADOX_KEY_FIREWALL",
        "requirement": "Paradox 1+1 keys must not become a C68/NAESE dictionary.",
        "observed_result": "No Paradox value predicts Q61 slot targets against controls.",
        "test_status": "PASSES_MATHEMAGIC_FIREWALL_NO_DICTIONARY",
    },
    {
        "test_id": "Q75_T04_EXTERNAL_METHOD_NOT_CANONICAL_ANCHOR",
        "requirement": "External method notes may guide search but cannot promote a gloss.",
        "observed_result": "s2ward/469 supports sequence-method exploration but not exact in-game slot meaning.",
        "test_status": "PASSES_EXTERNAL_METHOD_CONTAINMENT",
    },
    {
        "test_id": "Q75_T05_Q61_FUNCTIONAL_ROLE_PRESERVED",
        "requirement": "Q61 slot/classifier role remains functional-only if no exact source is found.",
        "observed_result": "Q61 accepted functional role with lexical_ready=0 and direct_gloss=0.",
        "test_status": "PASSES_FUNCTIONAL_ROLE_PRESERVED_NO_GLOSS",
    },
]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q75_c68_naese_exact_source_check_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q67_run_id INTEGER NOT NULL,
            q61_run_id INTEGER NOT NULL,
            q55_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            probe_id TEXT NOT NULL,
            web_query_count INTEGER NOT NULL,
            exact_slot_web_hit_count INTEGER NOT NULL,
            source_check_count INTEGER NOT NULL,
            register_support_source_count INTEGER NOT NULL,
            external_method_source_count INTEGER NOT NULL,
            exact_c68_naese_sequence_source_count INTEGER NOT NULL,
            slot_mechanical_value_count INTEGER NOT NULL,
            firewall_pass_count INTEGER NOT NULL,
            functional_role_preserved_count INTEGER NOT NULL,
            lexical_ready_count INTEGER NOT NULL,
            direct_gloss_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            result_human_version TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q75_c68_naese_exact_source_check_v1_sources (
            run_id INTEGER NOT NULL,
            source_id TEXT NOT NULL,
            source_url TEXT NOT NULL,
            observed_claim TEXT NOT NULL,
            exact_slot_sequence_support TEXT NOT NULL,
            mechanical_value_support TEXT NOT NULL,
            lexical_support TEXT NOT NULL,
            blocked_inference TEXT NOT NULL,
            source_status TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, source_id)
        );

        CREATE TABLE IF NOT EXISTS human_q75_c68_naese_exact_source_check_v1_tests (
            run_id INTEGER NOT NULL,
            test_id TEXT NOT NULL,
            requirement TEXT NOT NULL,
            observed_result TEXT NOT NULL,
            test_status TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, test_id)
        );

        CREATE TABLE IF NOT EXISTS human_q75_c68_naese_exact_source_check_v1_queries (
            run_id INTEGER NOT NULL,
            query_id TEXT NOT NULL,
            query_text TEXT NOT NULL,
            exact_slot_web_hit_count INTEGER NOT NULL,
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


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q67 = latest_row(conn, "human_q67_lexical_anchor_probe_queue_v1_runs")
    q61 = latest_row(conn, "human_q61_c68_naese_slot_role_minimal_pairs_v1_runs")
    q55 = latest_row(conn, "human_q55_source_parallel_audit_q54_v1_runs")
    audit = latest_row(conn, "human_translation_completion_audit_v5_runs")

    web_query_count = len(WEB_QUERIES)
    exact_slot_web_hit_count = 0
    source_check_count = len(SOURCE_FACTS)
    register_support_source_count = 2
    external_method_source_count = 1
    exact_c68_naese_sequence_source_count = 0
    slot_mechanical_value_count = 0
    firewall_pass_count = sum(1 for test in TEST_SPECS if "FIREWALL" in test["test_status"] or "CONTAINMENT" in test["test_status"])
    functional_role_preserved_count = 1
    lexical_ready_count = 0
    direct_gloss_count = 0
    canonical_promotion_allowed_count = 0
    result_human_version = (
        "Q75 finds no exact source or mechanically forced value for C68/NAESE slot meaning. "
        "Threat III and Paradox remain register/operator constraints, while s2ward/469 is useful "
        "external method pressure only. Q61's slot/classifier role remains functional shadow, not a gloss."
    )
    decision = (
        "Q75_C68_NAESE_EXACT_SOURCE_CHECK_NO_EXACT_GLOSS_FUNCTIONAL_ROLE_ONLY"
        if web_query_count == 4
        and exact_slot_web_hit_count == 0
        and source_check_count == 3
        and register_support_source_count == 2
        and external_method_source_count == 1
        and exact_c68_naese_sequence_source_count == 0
        and slot_mechanical_value_count == 0
        and firewall_pass_count == 3
        and functional_role_preserved_count == 1
        and int(q61["functional_role_accept_count"]) == 1
        and int(q61["lexical_ready_count"]) == 0
        and int(q61["direct_gloss_count"]) == 0
        and int(q67["lexical_ready_count"]) == 0
        and int(audit["promoted_gloss_count"]) == 0
        and lexical_ready_count == 0
        and direct_gloss_count == 0
        and canonical_promotion_allowed_count == 0
        else "Q75_C68_NAESE_EXACT_SOURCE_CHECK_REQUIRES_REVIEW"
    )
    payload = {
        "question": "Is there exact source support for C68/NAESE slot meaning?",
        "answer": result_human_version,
        "web_queries": WEB_QUERIES,
        "blocked_use": "Do not translate C68/NAESE as soul, body, key, slot, classifier, or any word.",
        "next_action": "Use Q61 as functional role only; continue source search only with exact-sequence requirements.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q75_c68_naese_exact_source_check_v1_runs (
                created_at, decision, q67_run_id, q61_run_id, q55_run_id,
                completion_audit_run_id, probe_id, web_query_count,
                exact_slot_web_hit_count, source_check_count,
                register_support_source_count, external_method_source_count,
                exact_c68_naese_sequence_source_count, slot_mechanical_value_count,
                firewall_pass_count, functional_role_preserved_count,
                lexical_ready_count, direct_gloss_count,
                canonical_promotion_allowed_count, result_human_version,
                payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                int(q67["run_id"]),
                int(q61["run_id"]),
                int(q55["run_id"]),
                int(audit["run_id"]),
                PROBE_ID,
                web_query_count,
                exact_slot_web_hit_count,
                source_check_count,
                register_support_source_count,
                external_method_source_count,
                exact_c68_naese_sequence_source_count,
                slot_mechanical_value_count,
                firewall_pass_count,
                functional_role_preserved_count,
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
            INSERT INTO human_q75_c68_naese_exact_source_check_v1_queries (
                run_id, query_id, query_text, exact_slot_web_hit_count,
                query_status, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    f"Q75_WEB_{idx:02d}",
                    query,
                    0,
                    "NO_EXACT_SLOT_WEB_HIT",
                    j({"query": query, "exact_slot_web_hit_count": 0}),
                )
                for idx, query in enumerate(WEB_QUERIES, start=1)
            ],
        )
        conn.executemany(
            """
            INSERT INTO human_q75_c68_naese_exact_source_check_v1_sources (
                run_id, source_id, source_url, observed_claim,
                exact_slot_sequence_support, mechanical_value_support,
                lexical_support, blocked_inference, source_status,
                evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    source["source_id"],
                    source["source_url"],
                    source["observed_claim"],
                    source["exact_slot_sequence_support"],
                    source["mechanical_value_support"],
                    source["lexical_support"],
                    source["blocked_inference"],
                    "NO_EXACT_SLOT_GLOSS_SUPPORT",
                    j(source),
                )
                for source in SOURCE_FACTS
            ],
        )
        conn.executemany(
            """
            INSERT INTO human_q75_c68_naese_exact_source_check_v1_tests (
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
                "exact_slot_web_hit_count": exact_slot_web_hit_count,
                "source_check_count": source_check_count,
                "register_support_source_count": register_support_source_count,
                "external_method_source_count": external_method_source_count,
                "exact_c68_naese_sequence_source_count": exact_c68_naese_sequence_source_count,
                "slot_mechanical_value_count": slot_mechanical_value_count,
                "firewall_pass_count": firewall_pass_count,
                "functional_role_preserved_count": functional_role_preserved_count,
                "lexical_ready_count": lexical_ready_count,
                "direct_gloss_count": direct_gloss_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
            }
        )
    )


if __name__ == "__main__":
    main()
