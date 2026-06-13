#!/usr/bin/env python3
"""Q92: exact-source audit for Q82 T08 Chayenne-frame register route."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
TARGET_ID = "Q82_T08_CHAYENNE_FRAME_REGISTER"

WEB_QUERIES = [
    {
        "query_id": "Q92_WEB_01",
        "query_text": '"FNSTAEFIEIEFIIVFAEATVATEBENEILTAENEEIVNCTIIN"',
        "result_status": "NO_EXACT_BOOK8_SOURCE_HIT",
        "notes": "No checked web/official hit gives the exact Book8 row0 sequence plus provenance and meaning.",
    },
    {
        "query_id": "Q92_WEB_02",
        "query_text": '"ENIIFINI*LTASTTNVVNNFIEVNNSTAEFIEIEFIIVFAEATVATEBE"',
        "result_status": "NO_EXACT_BOOK37_SOURCE_HIT",
        "notes": "No checked web/official hit gives the exact Book37 row0 sequence plus provenance and meaning.",
    },
    {
        "query_id": "Q92_WEB_03",
        "query_text": '"LEITELBENNAIFIININSBASTFNENIIFINI" "CHAYENNE"',
        "result_status": "NO_EXACT_BOOK66_SOURCE_HIT",
        "notes": "No checked web/official hit ties the Book66 BENNA/LTAST context to a Chayenne meaning.",
    },
    {
        "query_id": "Q92_WEB_04",
        "query_text": '"AEFIEIEFIIVFAEATVAT" "Tibia"',
        "result_status": "NO_EXACT_SHARED_BLOCK_GLOSS_HIT",
        "notes": "The projected Chayenne row0 shape remains locally attested, not externally glossed.",
    },
    {
        "query_id": "Q92_WEB_05",
        "query_text": '"114514519485611451908304576512282177" "6612527570584"',
        "result_status": "EXACT_CHAYENNE_SEQUENCE_ATTESTED_NO_GLOSS",
        "notes": "Portal Tibia, TibiaWiki BR, s2ward, and forum mirrors attest the Chayenne reply but do not give an explicit meaning.",
    },
    {
        "query_id": "Q92_WEB_06",
        "query_text": 'site:tibia.com "114514519485611451908304576512282177"',
        "result_status": "NO_OFFICIAL_TIBIA_COM_EXACT_HIT",
        "notes": "No tibia.com result was found for the exact Chayenne reply in the checked search.",
    },
    {
        "query_id": "Q92_WEB_07",
        "query_text": '"E sobre a linguagem dos Beholders" "Chayenne"',
        "result_status": "PRIMARY_INTERVIEW_CONTEXT_FOUND",
        "notes": "Portal Tibia interview has the question context and the exact Chayenne reply.",
    },
    {
        "query_id": "Q92_WEB_08",
        "query_text": '"Avar Tar" "bonelord language" "29639 46781"',
        "result_status": "INGAME_SPOKEN_HOLDOUT_FOUND_NO_TARGET_GLOSS",
        "notes": "Avar Tar transcript is an in-game 469-adjacent spoken holdout, but it does not gloss Books 8/37/66.",
    },
]

SOURCE_CHECKS = [
    {
        "source_id": "PORTALTIBIA_CHAYENNE_2009_PRIMARY",
        "source_url": "https://forum.portaltibia.com.br/topic/11420-entrevista-com-chayenne/",
        "source_result": "PRIMARY_INTERVIEW_EXACT_REPLY_NO_GLOSS",
        "support_value": "The May 15, 2009 Portal Tibia interview records the exact Chayenne reply to a bonelord-language question.",
        "blocked_inference": "Primary provenance is not an in-game book gloss and does not explain the phrase.",
    },
    {
        "source_id": "TIBIAWIKI_469_CHAYENNE_CONTEXT",
        "source_url": "https://www.tibiawiki.com.br/469",
        "source_result": "COMMUNITY_INDEX_EXACT_CHAYENNE_AND_RELATED_469_CONTEXT",
        "support_value": "The 469 page links Chayenne, Knightmare, Avar Tar, Wyrdin, and mathemagics as related clue context.",
        "blocked_inference": "The page does not translate the Chayenne reply or the Book8/37/66 frame.",
    },
    {
        "source_id": "A_WRINKLED_BONELORD_TRANSCRIPT",
        "source_url": "https://tibia.fandom.com/wiki/A_Wrinkled_Bonelord/Transcripts",
        "source_result": "INGAME_METHOD_ANCHOR_LANGUAGE_MATHEMAGIC",
        "support_value": "A Wrinkled Bonelord ties 469 to books, numbers, blinking, and mathemagic in-game.",
        "blocked_inference": "It does not map the Chayenne frame to English or identify Books 8/37/66.",
    },
    {
        "source_id": "AVAR_TAR_TRANSCRIPT",
        "source_url": "https://tibia.fandom.com/wiki/Avar_Tar/Transcripts",
        "source_result": "INGAME_SPOKEN_HOLDOUT_NO_TARGET_RELATION",
        "support_value": "Avar Tar gives an in-game bonelord-language poem response.",
        "blocked_inference": "The poem is not an exact Book8/37/66 source and does not explain the Chayenne frame.",
    },
    {
        "source_id": "CHAYENNE_EXTERNAL_SHAPE_GATE",
        "source_url": "sqlite:chayenne_external_shape_gate_runs",
        "source_result": "EXTERNAL_SHAPE_FRAME_CONFIRMED_NO_GLOSS",
        "support_value": "The shared block AEFIEIEFIIVFAEATVAT is accepted across books 8/37/63/66 as a frame.",
        "blocked_inference": "The gate explicitly blocks explicit meaning and lexical gloss.",
    },
    {
        "source_id": "Q2_CHAYENNE_EXPLICIT_GLOSS_AUDIT",
        "source_url": "sqlite:human_q2_chayenne_explicit_gloss_live_audit_v1_runs",
        "source_result": "EXACT_SEQUENCE_ATTESTED_FRAME_ONLY",
        "support_value": "Four checked sources attest the exact Chayenne sequence, while explicit gloss count remains zero.",
        "blocked_inference": "Attested sequence/context cannot be promoted to plaintext.",
    },
    {
        "source_id": "Q44_CHAYENNE_REGISTER_FRAME_ATLAS",
        "source_url": "sqlite:human_q44_chayenne_register_frame_atlas_v1_runs",
        "source_result": "REGISTER_FRAME_ATLAS_READY_NO_GLOSS",
        "support_value": "Books 8/37/63/66 carry the frame through distinct internal contexts.",
        "blocked_inference": "The atlas blocks a Chayenne phrase translation, shared-block gloss, and one fixed sentence.",
    },
    {
        "source_id": "PKG8_CHAYENNE_FUNCTIONAL_FALSIFICATION",
        "source_url": "sqlite:human_promotion_pkg8_chayenne_frame_branch_falsification_v1_runs",
        "source_result": "FUNCTIONAL_BRANCH_LABEL_PROMOTED_NO_PLAINTEXT",
        "support_value": "Books 8/37/66 support a functional branch/register label; Book63 stays audit-held.",
        "blocked_inference": "No component gloss, Chayenne phrase translation, or Book63 promotion is allowed.",
    },
    {
        "source_id": "CHAYENNE_PRIMARY_SOURCE_SEARCH",
        "source_url": "sqlite:chayenne_primary_source_search_v1_runs",
        "source_result": "SOURCES_ATTEST_SEQUENCE_NO_EXPLICIT_GLOSS",
        "support_value": "Earlier primary-source search found source attestation but no explicit gloss.",
        "blocked_inference": "Community speculation and context do not promote plaintext.",
    },
    {
        "source_id": "CHAYENNE_EXACT_NEAR_CONTRAST",
        "source_url": "sqlite:chayenne_exact_near_contrast_v1_runs",
        "source_result": "STRUCTURE_PROMOTED_NO_PROSE",
        "support_value": "Exact and near Chayenne blocks support structural branch topology with controls.",
        "blocked_inference": "Near/exact contrast blocks lexical prose promotion.",
    },
    {
        "source_id": "CHAYENNE_ROLE_BRIDGE_GATE",
        "source_url": "sqlite:chayenne_role_bridge_gate_v1_runs",
        "source_result": "CONTEXT_AND_HANDOFF_BRIDGE_NO_PLAINTEXT",
        "support_value": "The shape bridges context and handoff grammar roles.",
        "blocked_inference": "Mixed role support is structural, not plaintext.",
    },
    {
        "source_id": "CHAYENNE_TOPOLOGY_PROBE",
        "source_url": "sqlite:chayenne_shape_topology_probe_runs",
        "source_result": "TOPOLOGY_READY_NO_GLOSS",
        "support_value": "The shape spans multiple branches.",
        "blocked_inference": "Multi-branch topology rules out a single fixed sentence without extra evidence.",
    },
]

TESTS = [
    {
        "test_id": "Q92_T01_WEB_EXACT_BOOK_SEQUENCES",
        "test_result": "FAILS_EXACT_BOOK_SOURCE_REQUIREMENT",
        "interpretation": "No checked web/official source gives exact Book8/37/66 sequence plus meaning.",
    },
    {
        "test_id": "Q92_T02_PRIMARY_CHAYENNE_REPLY",
        "test_result": "PRESERVE_EXTERNAL_PROVENANCE_ONLY",
        "interpretation": "The Portal Tibia interview is strong provenance for the Chayenne reply, but not an in-game book gloss.",
    },
    {
        "test_id": "Q92_T03_INGAME_CONTEXT_ANCHORS",
        "test_result": "PRESERVE_METHOD_CONTEXT_NO_TARGET_GLOSS",
        "interpretation": "AWB and Avar Tar anchor method/context inside the game without translating the target books.",
    },
    {
        "test_id": "Q92_T04_BRANCH_TOPOLOGY",
        "test_result": "PRESERVE_REGISTER_FRAME_LABEL",
        "interpretation": "Books 8/37/66 keep a Chayenne-frame branch label; Book63 remains audit-only.",
    },
    {
        "test_id": "Q92_T05_EXTERNAL_FRAME_FIREWALL",
        "test_result": "BLOCKS_EXTERNAL_SHAPE_TO_PLAINTEXT",
        "interpretation": "External Chayenne shape cannot be imported as English prose.",
    },
    {
        "test_id": "Q92_T06_PROMOTION_FIREWALL",
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
        CREATE TABLE IF NOT EXISTS human_q92_chayenne_frame_register_exact_source_audit_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q82_run_id INTEGER NOT NULL,
            q2_gloss_run_id INTEGER NOT NULL,
            q44_run_id INTEGER NOT NULL,
            external_shape_gate_run_id INTEGER NOT NULL,
            primary_source_run_id INTEGER NOT NULL,
            exact_near_run_id INTEGER NOT NULL,
            role_bridge_run_id INTEGER NOT NULL,
            topology_run_id INTEGER NOT NULL,
            pkg8_run_id INTEGER NOT NULL,
            q81_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            target_id TEXT NOT NULL,
            target_book_count INTEGER NOT NULL,
            target_family TEXT NOT NULL,
            web_query_count INTEGER NOT NULL,
            web_primary_chayenne_hit_count INTEGER NOT NULL,
            web_exact_book_sequence_hit_count INTEGER NOT NULL,
            official_exact_target_hit_count INTEGER NOT NULL,
            source_check_count INTEGER NOT NULL,
            exact_chayenne_sequence_attested_count INTEGER NOT NULL,
            q44_frame_book_count INTEGER NOT NULL,
            external_shape_accepted_book_count INTEGER NOT NULL,
            target_branch_book_count INTEGER NOT NULL,
            audit_held_book_count INTEGER NOT NULL,
            exact_book_sequence_count INTEGER NOT NULL,
            exact_meaning_relation_count INTEGER NOT NULL,
            explicit_gloss_count INTEGER NOT NULL,
            functional_label_count INTEGER NOT NULL,
            component_gloss_allowed_count INTEGER NOT NULL,
            lexical_ready_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            target_status TEXT NOT NULL,
            result_human_version TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q92_chayenne_frame_register_exact_source_audit_v1_queries (
            run_id INTEGER NOT NULL,
            query_id TEXT NOT NULL,
            query_text TEXT NOT NULL,
            result_status TEXT NOT NULL,
            notes TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, query_id)
        );

        CREATE TABLE IF NOT EXISTS human_q92_chayenne_frame_register_exact_source_audit_v1_sources (
            run_id INTEGER NOT NULL,
            source_id TEXT NOT NULL,
            source_url TEXT NOT NULL,
            source_result TEXT NOT NULL,
            support_value TEXT NOT NULL,
            blocked_inference TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, source_id)
        );

        CREATE TABLE IF NOT EXISTS human_q92_chayenne_frame_register_exact_source_audit_v1_books (
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

        CREATE TABLE IF NOT EXISTS human_q92_chayenne_frame_register_exact_source_audit_v1_tests (
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
        raise RuntimeError(f"missing required target: {TARGET_ID}")
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
    q2_gloss = latest_row(conn, "human_q2_chayenne_explicit_gloss_live_audit_v1_runs")
    q44 = latest_row(conn, "human_q44_chayenne_register_frame_atlas_v1_runs")
    external_gate = latest_row(conn, "chayenne_external_shape_gate_runs")
    primary_source = latest_row(conn, "chayenne_primary_source_search_v1_runs")
    exact_near = latest_row(conn, "chayenne_exact_near_contrast_v1_runs")
    role_bridge = latest_row(conn, "chayenne_role_bridge_gate_v1_runs")
    topology = latest_row(conn, "chayenne_shape_topology_probe_runs")
    pkg8 = latest_row(conn, "human_promotion_pkg8_chayenne_frame_branch_falsification_v1_runs")
    q81 = latest_row(conn, "human_q81_controlled_shadow_export_v1_runs")
    completion = latest_row(conn, "human_translation_completion_audit_v5_runs")
    target = load_target(conn, int(q82["run_id"]))
    books = load_books(conn, int(q82["run_id"]))

    target_book_count = len(books)
    web_query_count = len(WEB_QUERIES)
    web_primary_chayenne_hit_count = 1
    web_exact_book_sequence_hit_count = 0
    official_exact_target_hit_count = 0
    source_check_count = len(SOURCE_CHECKS)
    exact_chayenne_sequence_attested_count = int(q2_gloss["exact_sequence_attested_count"])
    q44_frame_book_count = int(q44["target_book_count"])
    external_shape_accepted_book_count = int(external_gate["accepted_book_count"])
    target_branch_book_count = len(json.loads(str(pkg8["candidate_books_json"])))
    audit_held_book_count = max(0, q44_frame_book_count - target_branch_book_count)
    exact_book_sequence_count = 0
    exact_meaning_relation_count = 0
    explicit_gloss_count = int(q2_gloss["explicit_gloss_count"])
    functional_label_count = int(pkg8["promoted_functional_label_count"])
    component_gloss_allowed_count = int(q44["component_gloss_allowed_count"])
    lexical_ready_count = 0
    canonical_promotion_allowed_count = 0
    target_status = "SOURCE_AUDITED_EXTERNAL_FRAME_SUPPORT_NO_BOOK_GLOSS"
    result_human_version = (
        "Q92 preserves Books 8/37/66 as a Chayenne-frame/register branch set: "
        "Book8 is the clean VNCTIIN context branch, Book37 is the LTAST-to-VNCTIIN handoff, "
        "and Book66 is the BENNA/LTAST formula branch carrying the same external frame. "
        "The Chayenne interview is strong external provenance, but no checked source gives "
        "an exact Book8/37/66 sequence plus meaning, so no plaintext is promotable."
    )
    decision = (
        "Q92_CHAYENNE_FRAME_REGISTER_EXACT_SOURCE_AUDIT_EXTERNAL_FRAME_SUPPORT_NO_EXACT_BOOK_GLOSS"
        if target_book_count == 3
        and str(target["target_family"]) == "CHAYENNE_FRAME_REGISTER"
        and web_query_count == 8
        and web_primary_chayenne_hit_count == 1
        and web_exact_book_sequence_hit_count == 0
        and official_exact_target_hit_count == 0
        and source_check_count == 12
        and exact_chayenne_sequence_attested_count >= 4
        and q44_frame_book_count == 4
        and external_shape_accepted_book_count == 4
        and target_branch_book_count == 3
        and audit_held_book_count == 1
        and exact_book_sequence_count == 0
        and exact_meaning_relation_count == 0
        and explicit_gloss_count == 0
        and functional_label_count == 1
        and component_gloss_allowed_count == 0
        and int(external_gate["lexical_gloss_allowed"]) == 0
        and int(primary_source["plaintext_promotable_count"]) == 0
        and int(exact_near["accepted_prose_gloss_count"]) == 0
        and int(role_bridge["accepted_prose_gloss_count"]) == 0
        and int(q81["promoted_gloss_count"]) == 0
        and int(completion["promoted_gloss_count"]) == 0
        else "Q92_CHAYENNE_FRAME_REGISTER_EXACT_SOURCE_AUDIT_REQUIRES_REVIEW"
    )
    payload = {
        "answer": result_human_version,
        "allowed_use": "Use Chayenne as a source-quarantined register/frame witness and branch label for Books 8/37/66.",
        "blocked_use": "Do not translate AEFIEIEFIIVFAEATVAT, the Chayenne reply, or Books 8/37/66 as plaintext.",
        "next_action": "Export the human route atlas with Q90/Q91/Q92 blockers integrated, then rank the next non-Q82 exact-source route.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q92_chayenne_frame_register_exact_source_audit_v1_runs (
                created_at, decision, q82_run_id, q2_gloss_run_id, q44_run_id,
                external_shape_gate_run_id, primary_source_run_id, exact_near_run_id,
                role_bridge_run_id, topology_run_id, pkg8_run_id, q81_run_id,
                completion_audit_run_id, target_id, target_book_count, target_family,
                web_query_count, web_primary_chayenne_hit_count,
                web_exact_book_sequence_hit_count, official_exact_target_hit_count,
                source_check_count, exact_chayenne_sequence_attested_count,
                q44_frame_book_count, external_shape_accepted_book_count,
                target_branch_book_count, audit_held_book_count,
                exact_book_sequence_count, exact_meaning_relation_count,
                explicit_gloss_count, functional_label_count,
                component_gloss_allowed_count, lexical_ready_count,
                canonical_promotion_allowed_count, target_status,
                result_human_version, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                int(q82["run_id"]),
                int(q2_gloss["run_id"]),
                int(q44["run_id"]),
                int(external_gate["run_id"]),
                int(primary_source["run_id"]),
                int(exact_near["run_id"]),
                int(role_bridge["run_id"]),
                int(topology["run_id"]),
                int(pkg8["run_id"]),
                int(q81["run_id"]),
                int(completion["run_id"]),
                TARGET_ID,
                target_book_count,
                str(target["target_family"]),
                web_query_count,
                web_primary_chayenne_hit_count,
                web_exact_book_sequence_hit_count,
                official_exact_target_hit_count,
                source_check_count,
                exact_chayenne_sequence_attested_count,
                q44_frame_book_count,
                external_shape_accepted_book_count,
                target_branch_book_count,
                audit_held_book_count,
                exact_book_sequence_count,
                exact_meaning_relation_count,
                explicit_gloss_count,
                functional_label_count,
                component_gloss_allowed_count,
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
            INSERT INTO human_q92_chayenne_frame_register_exact_source_audit_v1_queries (
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
            INSERT INTO human_q92_chayenne_frame_register_exact_source_audit_v1_sources (
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
            INSERT INTO human_q92_chayenne_frame_register_exact_source_audit_v1_books (
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
                    "PRESERVE_CHAYENNE_FRAME_BRANCH_LABEL_NO_PLAINTEXT",
                    j(dict(row)),
                )
                for row in books
            ],
        )
        conn.executemany(
            """
            INSERT INTO human_q92_chayenne_frame_register_exact_source_audit_v1_tests (
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
                "web_primary_chayenne_hit_count": web_primary_chayenne_hit_count,
                "web_exact_book_sequence_hit_count": web_exact_book_sequence_hit_count,
                "official_exact_target_hit_count": official_exact_target_hit_count,
                "source_check_count": source_check_count,
                "exact_chayenne_sequence_attested_count": exact_chayenne_sequence_attested_count,
                "q44_frame_book_count": q44_frame_book_count,
                "external_shape_accepted_book_count": external_shape_accepted_book_count,
                "target_branch_book_count": target_branch_book_count,
                "audit_held_book_count": audit_held_book_count,
                "exact_book_sequence_count": exact_book_sequence_count,
                "exact_meaning_relation_count": exact_meaning_relation_count,
                "explicit_gloss_count": explicit_gloss_count,
                "functional_label_count": functional_label_count,
                "component_gloss_allowed_count": component_gloss_allowed_count,
                "lexical_ready_count": lexical_ready_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
            }
        )
    )


if __name__ == "__main__":
    main()
