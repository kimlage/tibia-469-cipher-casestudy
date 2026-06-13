#!/usr/bin/env python3
"""Q96: Q80 packet source-as-packet audit after Book7 operator closure."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
TARGET_ACTION_ID = "Q93_A03_Q80_PACKET_SOURCE_AS_PACKET"
PACKET_BOOKS = ["35", "67", "2", "27", "10"]

WEB_QUERIES = [
    {
        "query_id": "Q96_WEB_01",
        "query_text": '"FIFTLEITELBENNAIFIININSBASTFNENIIFINI"',
        "result_status": "NO_EXACT_BOOK35_SOURCE_HIT",
        "notes": "No checked web hit gives exact Book35 sequence plus meaning.",
    },
    {
        "query_id": "Q96_WEB_02",
        "query_text": '"ITEITAILBETFTE*ICEVIEFIINI*VNCTIINNVETTAFSETBASEFA"',
        "result_status": "NO_EXACT_BOOK67_SOURCE_HIT",
        "notes": "No checked web hit gives exact Book67 sequence plus meaning.",
    },
    {
        "query_id": "Q96_WEB_03",
        "query_text": '"CEVIEFIINI*VNCTIINNVETTAFSETBASEFAIFVI"',
        "result_status": "NO_EXACT_BOOK2_SOURCE_HIT",
        "notes": "No checked web hit gives exact Book2 sequence plus meaning.",
    },
    {
        "query_id": "Q96_WEB_04",
        "query_text": '"LFSENSTAEFIEIEFIIVFATFTFNLIBEITEITAILBETFTE"',
        "result_status": "NO_EXACT_BOOK27_SOURCE_HIT",
        "notes": "No checked web hit gives exact Book27 sequence plus meaning.",
    },
    {
        "query_id": "Q96_WEB_05",
        "query_text": '"BENNAIFIININSBASTFNENIIFINI" "TAILBETFTE"',
        "result_status": "NO_EXACT_BENNA_TAILBETFTE_PACKET_HIT",
        "notes": "No checked web hit gives BENNA/TAILBETFTE packet relation plus meaning.",
    },
    {
        "query_id": "Q96_WEB_06",
        "query_text": '"CEVIEFIINI" "VNCTIIN" "NAESE"',
        "result_status": "NO_EXACT_PAYLOAD_SLOT_PACKET_HIT",
        "notes": "No checked web hit gives CEVIEFIINI/VNCTIIN/NAESE payload relation plus meaning.",
    },
    {
        "query_id": "Q96_WEB_07",
        "query_text": '"You Cannot Even Imagine" "great calculator" "bonelords language"',
        "result_status": "INGAME_CORPUS_ASSEMBLY_SOURCE_FOUND",
        "notes": "The in-game book supports a Great Calculator/corpus assembly frame, not the exact packet meaning.",
    },
    {
        "query_id": "Q96_WEB_08",
        "query_text": '"Beware of the Bonelords" "not only a language" "mathematics"',
        "result_status": "INGAME_LANGUAGE_MATHEMATICS_SOURCE_FOUND",
        "notes": "Beware supports 469 as language plus mathematics, not the exact packet meaning.",
    },
    {
        "query_id": "Q96_WEB_09",
        "query_text": '"Book 35" "Book 67" "Hellgate" "averages"',
        "result_status": "EXTERNAL_METHOD_PRESSURE_ONLY",
        "notes": "TibiaSecrets/s2ward-style external analyses support corpus/arithmetic pressure, not packet plaintext.",
    },
    {
        "query_id": "Q96_WEB_10",
        "query_text": 'site:tibia.com "CEVIEFIINI"',
        "result_status": "NO_OFFICIAL_EXACT_PACKET_HIT",
        "notes": "No official tibia.com exact hit was found for CEVIEFIINI.",
    },
]

SOURCE_CHECKS = [
    {
        "source_id": "Q80_PACKET_SHADOW",
        "source_url": "sqlite:human_q80_packet_shadow_versions_v1_runs",
        "source_result": "PRIMARY_35_67_2_HELDOUT_27_67_NO_GLOSS",
        "support_value": "Q80 gives 35->67->2 as primary packet and 27->67->2 as conditional heldout extension.",
        "blocked_inference": "Q80 explicitly has zero exact source sequences, zero meaning relations, and zero promotions.",
    },
    {
        "source_id": "Q83_BENNA_C86_SOURCE_AUDIT",
        "source_url": "sqlite:human_q83_benna_c86_exact_source_audit_v1_runs",
        "source_result": "METHOD_SUPPORT_NO_EXACT_SOURCE_NO_GLOSS",
        "support_value": "BENNA->C86/VNCTIIN has method support but no exact source hit.",
        "blocked_inference": "Formula handoff cannot become plaintext.",
    },
    {
        "source_id": "Q84_C86_VNCTIIN_SOURCE_AUDIT",
        "source_url": "sqlite:human_q84_c86_vnctiin_exact_source_audit_v1_runs",
        "source_result": "REGISTER_SUPPORT_NO_EXACT_SOURCE_NO_GLOSS",
        "support_value": "C86/VNCTIIN payload corridor has register support but no exact source hit.",
        "blocked_inference": "Payload/context corridor cannot become plaintext.",
    },
    {
        "source_id": "Q85_CRITICAL_SYNTHESIS",
        "source_url": "sqlite:human_q85_critical_source_audit_synthesis_v1_runs",
        "source_result": "Q80_SHADOW_STABLE_PROMOTION_BLOCKED",
        "support_value": "Both critical exact-source targets failed promotion gates while Q80 remains useful shadow.",
        "blocked_inference": "Packet readability cannot override failed exact-source components.",
    },
    {
        "source_id": "Q73_27_TO_67_STRUCTURAL_EDGE",
        "source_url": "sqlite:human_q73_book27_to_67_confirmation_gate_v1_runs",
        "source_result": "STRUCTURAL_MISSING_EDGE_STRENGTHENED_UNCONFIRMED",
        "support_value": "27->67 is strengthened as a structural candidate but lacks source or contig confirmation.",
        "blocked_inference": "27->67 cannot be called a confirmed edge or sentence.",
    },
    {
        "source_id": "Q74_27_TO_67_EXTERNAL_SEARCH",
        "source_url": "sqlite:human_q74_book27_to_67_external_exact_search_audit_v1_runs",
        "source_result": "NO_EXTERNAL_CONFIRMATION_NO_GLOSS",
        "support_value": "Exact online/local search found no independent external confirmation for 27->67.",
        "blocked_inference": "Internal matches are not independent source support.",
    },
    {
        "source_id": "Q78_67_2_SOURCE_CONTINUITY",
        "source_url": "sqlite:human_q78_edge_67_2_source_continuity_v1_runs",
        "source_result": "METHOD_SUPPORT_NO_EXACT_PHRASE_NO_GLOSS",
        "support_value": "35->67->2 is source-compatible as a phrase path only; exact edge and exact phrase parallels are zero.",
        "blocked_inference": "Book67 or Book2 cannot be translated from continuity evidence.",
    },
    {
        "source_id": "Q79_GLOBAL_SOURCE_FIREWALL",
        "source_url": "sqlite:human_q79_global_source_firewall_v1_runs",
        "source_result": "BLOCKS_ALL_PROMOTIONS_NO_GLOSS",
        "support_value": "All Q67-Q78 candidates are allowed as shadow only and blocked from promotion.",
        "blocked_inference": "No packet candidate is source-backed plaintext.",
    },
    {
        "source_id": "YOU_CANNOT_EVEN_IMAGINE_BOOK",
        "source_url": "https://www.tibiawiki.com.br/wiki/You_Cannot_Even_Imagine_%28Book%29",
        "source_result": "INGAME_GREAT_CALCULATOR_ASSEMBLY_ANCHOR",
        "support_value": "The book says the Great Calculator assembled the bonelords language.",
        "blocked_inference": "Corpus assembly lore does not identify the packet path or its meaning.",
    },
    {
        "source_id": "BEWARE_OF_THE_BONELORDS_BOOK",
        "source_url": "https://www.tibiawiki.com.br/wiki/Beware_of_the_Bonelords%21_%28Book%29",
        "source_result": "INGAME_LANGUAGE_PLUS_MATHEMATICS_ANCHOR",
        "support_value": "Beware frames bonelord language as code and mathematics.",
        "blocked_inference": "General language/math lore does not translate 35/67/2.",
    },
    {
        "source_id": "TIBIASECRETS_HELLGATE_AVERAGES",
        "source_url": "https://www.tibiasecrets.com/article166",
        "source_result": "EXTERNAL_ARITHMETIC_CORPUS_PRESSURE_ONLY",
        "support_value": "External averages work highlights Book35/67 arithmetic/corpus behavior.",
        "blocked_inference": "External arithmetic pressure is not an in-game exact packet meaning.",
    },
    {
        "source_id": "S2WARD_469_CORPUS",
        "source_url": "https://github.com/s2ward/469",
        "source_result": "EXTERNAL_CORPUS_ALIGNMENT_SUPPORT_ONLY",
        "support_value": "External corpus/alignment work supports treating books as assembled sequence material.",
        "blocked_inference": "External alignment does not provide source-backed plaintext.",
    },
    {
        "source_id": "A_WRINKLED_BONELORD_TRANSCRIPT",
        "source_url": "https://tibia.fandom.com/wiki/A_Wrinkled_Bonelord/Transcripts",
        "source_result": "INGAME_METHOD_ANCHOR_ONLY",
        "support_value": "AWB links 469, numbers, books, and mathemagical processing.",
        "blocked_inference": "AWB gives no exact 35/67/2 packet meaning.",
    },
]

TESTS = [
    {
        "test_id": "Q96_T01_WEB_EXACT_PACKET",
        "test_result": "FAILS_EXACT_SOURCE_REQUIREMENT",
        "interpretation": "No exact source gives 35/67/2, 27/67/2, or 10/35 packet meaning.",
    },
    {
        "test_id": "Q96_T02_COMPONENT_AUDITS",
        "test_result": "COMPONENTS_BLOCK_PROMOTION",
        "interpretation": "Q83 and Q84 block separate component promotion.",
    },
    {
        "test_id": "Q96_T03_PACKET_LEVEL_REASSESSMENT",
        "test_result": "PRESERVE_PACKET_SHADOW_ONLY",
        "interpretation": "Packet-level reading remains useful but does not add exact source evidence.",
    },
    {
        "test_id": "Q96_T04_HELDOUT_EDGE",
        "test_result": "27_TO_67_STRUCTURAL_UNCONFIRMED",
        "interpretation": "Heldout 27->67 is strengthened locally but source-unconfirmed.",
    },
    {
        "test_id": "Q96_T05_SOURCE_FIREWALL",
        "test_result": "PASSES_GLOBAL_FIREWALL",
        "interpretation": "Q79 blocks all Q67-Q78 promotions.",
    },
    {
        "test_id": "Q96_T06_PROMOTION_FIREWALL",
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
        CREATE TABLE IF NOT EXISTS human_q96_q80_packet_source_as_packet_audit_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q93_run_id INTEGER NOT NULL,
            q80_run_id INTEGER NOT NULL,
            q83_run_id INTEGER NOT NULL,
            q84_run_id INTEGER NOT NULL,
            q85_run_id INTEGER NOT NULL,
            q73_run_id INTEGER NOT NULL,
            q74_run_id INTEGER NOT NULL,
            q78_run_id INTEGER NOT NULL,
            q79_run_id INTEGER NOT NULL,
            q81_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            action_id TEXT NOT NULL,
            packet_book_count INTEGER NOT NULL,
            primary_path_book_count INTEGER NOT NULL,
            heldout_path_book_count INTEGER NOT NULL,
            sibling_formula_control_count INTEGER NOT NULL,
            web_query_count INTEGER NOT NULL,
            web_exact_packet_hit_count INTEGER NOT NULL,
            official_exact_target_hit_count INTEGER NOT NULL,
            source_check_count INTEGER NOT NULL,
            exact_source_sequence_count INTEGER NOT NULL,
            exact_meaning_relation_count INTEGER NOT NULL,
            q80_packet_version_count INTEGER NOT NULL,
            accepted_primary_packet_count INTEGER NOT NULL,
            conditional_heldout_packet_count INTEGER NOT NULL,
            component_exact_source_hit_count INTEGER NOT NULL,
            packet_level_exact_source_hit_count INTEGER NOT NULL,
            packet_method_support_count INTEGER NOT NULL,
            structural_edge_candidate_count INTEGER NOT NULL,
            confirmed_edge_count INTEGER NOT NULL,
            source_resolution_count INTEGER NOT NULL,
            firewall_blocked_candidate_count INTEGER NOT NULL,
            lexical_ready_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            target_status TEXT NOT NULL,
            result_human_version TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q96_q80_packet_source_as_packet_audit_v1_queries (
            run_id INTEGER NOT NULL,
            query_id TEXT NOT NULL,
            query_text TEXT NOT NULL,
            result_status TEXT NOT NULL,
            notes TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, query_id)
        );

        CREATE TABLE IF NOT EXISTS human_q96_q80_packet_source_as_packet_audit_v1_sources (
            run_id INTEGER NOT NULL,
            source_id TEXT NOT NULL,
            source_url TEXT NOT NULL,
            source_result TEXT NOT NULL,
            support_value TEXT NOT NULL,
            blocked_inference TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, source_id)
        );

        CREATE TABLE IF NOT EXISTS human_q96_q80_packet_source_as_packet_audit_v1_books (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            packet_role TEXT NOT NULL,
            symbol_text TEXT NOT NULL,
            source_bridge_id TEXT NOT NULL,
            plausible_human_reading TEXT NOT NULL,
            confidence_tier TEXT NOT NULL,
            packet_result TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        );

        CREATE TABLE IF NOT EXISTS human_q96_q80_packet_source_as_packet_audit_v1_tests (
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
    q80 = latest_row(conn, "human_q80_packet_shadow_versions_v1_runs")
    q83 = latest_row(conn, "human_q83_benna_c86_exact_source_audit_v1_runs")
    q84 = latest_row(conn, "human_q84_c86_vnctiin_exact_source_audit_v1_runs")
    q85 = latest_row(conn, "human_q85_critical_source_audit_synthesis_v1_runs")
    q73 = latest_row(conn, "human_q73_book27_to_67_confirmation_gate_v1_runs")
    q74 = latest_row(conn, "human_q74_book27_to_67_external_exact_search_audit_v1_runs")
    q78 = latest_row(conn, "human_q78_edge_67_2_source_continuity_v1_runs")
    q79 = latest_row(conn, "human_q79_global_source_firewall_v1_runs")
    q81 = latest_row(conn, "human_q81_controlled_shadow_export_v1_runs")
    completion = latest_row(conn, "human_translation_completion_audit_v5_runs")
    q81_rows = {bookid: q81_book(conn, int(q81["run_id"]), bookid) for bookid in PACKET_BOOKS}

    packet_book_count = len(PACKET_BOOKS)
    primary_path_book_count = 3
    heldout_path_book_count = 3
    sibling_formula_control_count = 2
    web_query_count = len(WEB_QUERIES)
    web_exact_packet_hit_count = 0
    official_exact_target_hit_count = 0
    source_check_count = len(SOURCE_CHECKS)
    exact_source_sequence_count = 0
    exact_meaning_relation_count = 0
    q80_packet_version_count = int(q80["packet_version_count"])
    accepted_primary_packet_count = int(q80["accepted_primary_packet_count"])
    conditional_heldout_packet_count = int(q80["conditional_heldout_packet_count"])
    component_exact_source_hit_count = int(q83["web_exact_target_hit_count"]) + int(q84["web_exact_target_hit_count"])
    packet_level_exact_source_hit_count = int(q78["web_exact_hit_count"])
    packet_method_support_count = int(q78["source_method_support_count"])
    structural_edge_candidate_count = int(q73["structural_candidate_strengthened_count"])
    confirmed_edge_count = int(q73["confirmed_edge_count"])
    source_resolution_count = int(q73["source_resolution_count"]) + int(q74["source_resolution_count"])
    firewall_blocked_candidate_count = int(q79["candidate_blocked_promotion_count"])
    lexical_ready_count = 0
    canonical_promotion_allowed_count = 0
    target_status = "PACKET_LEVEL_SOURCE_AUDITED_METHOD_SUPPORT_NO_EXACT_PACKET_GLOSS"
    result_human_version = (
        "Q96 preserves Q80 as a packet-level human shadow: 35->67->2 is still the primary "
        "formula-handoff to payload/context path, 27->67->2 is a conditional heldout extension, "
        "and 10/35 are sibling formula-handoff controls. Treating the route as a packet does not "
        "recover exact source evidence: component audits, packet continuity, and global firewall all "
        "keep lexical/canonical promotion blocked."
    )
    decision = (
        "Q96_Q80_PACKET_SOURCE_AS_PACKET_AUDIT_PACKET_PATH_SUPPORT_NO_EXACT_SOURCE_NO_GLOSS"
        if packet_book_count == 5
        and web_query_count == 10
        and web_exact_packet_hit_count == 0
        and official_exact_target_hit_count == 0
        and source_check_count == 13
        and exact_source_sequence_count == 0
        and exact_meaning_relation_count == 0
        and q80_packet_version_count == 2
        and accepted_primary_packet_count == 1
        and conditional_heldout_packet_count == 1
        and component_exact_source_hit_count == 0
        and packet_level_exact_source_hit_count == 0
        and packet_method_support_count == 2
        and structural_edge_candidate_count == 1
        and confirmed_edge_count == 0
        and source_resolution_count == 0
        and firewall_blocked_candidate_count == 5
        and int(q85["q80_packet_promotion_allowed_count"]) == 0
        and int(q93["promoted_gloss_count"]) == 0
        and int(completion["promoted_gloss_count"]) == 0
        else "Q96_Q80_PACKET_SOURCE_AS_PACKET_AUDIT_REQUIRES_REVIEW"
    )
    payload = {
        "answer": result_human_version,
        "allowed_use": "Use Q80 as a packet-level human shadow and source-search route.",
        "blocked_use": "Do not translate BENNA, C86, VNCTIIN, NAESE, TAILBETFTE, Book35, Book67, Book2, Book27, or the packet as plaintext.",
        "next_action": "Proceed to Q93_A04 Book30/Great Calculator corpus route.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q96_q80_packet_source_as_packet_audit_v1_runs (
                created_at, decision, q93_run_id, q80_run_id, q83_run_id,
                q84_run_id, q85_run_id, q73_run_id, q74_run_id, q78_run_id,
                q79_run_id, q81_run_id, completion_audit_run_id, action_id,
                packet_book_count, primary_path_book_count, heldout_path_book_count,
                sibling_formula_control_count, web_query_count, web_exact_packet_hit_count,
                official_exact_target_hit_count, source_check_count,
                exact_source_sequence_count, exact_meaning_relation_count,
                q80_packet_version_count, accepted_primary_packet_count,
                conditional_heldout_packet_count, component_exact_source_hit_count,
                packet_level_exact_source_hit_count, packet_method_support_count,
                structural_edge_candidate_count, confirmed_edge_count, source_resolution_count,
                firewall_blocked_candidate_count, lexical_ready_count,
                canonical_promotion_allowed_count, target_status, result_human_version,
                payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                int(q93["run_id"]),
                int(q80["run_id"]),
                int(q83["run_id"]),
                int(q84["run_id"]),
                int(q85["run_id"]),
                int(q73["run_id"]),
                int(q74["run_id"]),
                int(q78["run_id"]),
                int(q79["run_id"]),
                int(q81["run_id"]),
                int(completion["run_id"]),
                TARGET_ACTION_ID,
                packet_book_count,
                primary_path_book_count,
                heldout_path_book_count,
                sibling_formula_control_count,
                web_query_count,
                web_exact_packet_hit_count,
                official_exact_target_hit_count,
                source_check_count,
                exact_source_sequence_count,
                exact_meaning_relation_count,
                q80_packet_version_count,
                accepted_primary_packet_count,
                conditional_heldout_packet_count,
                component_exact_source_hit_count,
                packet_level_exact_source_hit_count,
                packet_method_support_count,
                structural_edge_candidate_count,
                confirmed_edge_count,
                source_resolution_count,
                firewall_blocked_candidate_count,
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
            INSERT INTO human_q96_q80_packet_source_as_packet_audit_v1_queries (
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
            INSERT INTO human_q96_q80_packet_source_as_packet_audit_v1_sources (
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
        for bookid in PACKET_BOOKS:
            q81_row = q81_rows[bookid]
            if bookid == "35":
                role = "PRIMARY_FORMULA_HANDOFF_START"
                result = "PRIMARY_PACKET_COMPONENT_SHADOW_ONLY"
            elif bookid == "67":
                role = "PRIMARY_AND_HELDOUT_PACKET_HANDOFF"
                result = "LOCAL_EDGE_COMPONENT_SHADOW_ONLY"
            elif bookid == "2":
                role = "PRIMARY_AND_HELDOUT_PAYLOAD_ENTRY"
                result = "PAYLOAD_CONTEXT_ENTRY_SHADOW_ONLY"
            elif bookid == "27":
                role = "HELDOUT_EXTENSION_START"
                result = "STRUCTURAL_MISSING_EDGE_CANDIDATE_UNCONFIRMED"
            else:
                role = "SIBLING_FORMULA_HANDOFF_CONTROL"
                result = "FORMULA_HANDOFF_CONTROL_SHADOW_ONLY"
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
            INSERT INTO human_q96_q80_packet_source_as_packet_audit_v1_books (
                run_id, bookid, packet_role, symbol_text, source_bridge_id,
                plausible_human_reading, confidence_tier, packet_result, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            book_rows,
        )
        conn.executemany(
            """
            INSERT INTO human_q96_q80_packet_source_as_packet_audit_v1_tests (
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
                "packet_book_count": packet_book_count,
                "web_query_count": web_query_count,
                "web_exact_packet_hit_count": web_exact_packet_hit_count,
                "official_exact_target_hit_count": official_exact_target_hit_count,
                "source_check_count": source_check_count,
                "exact_source_sequence_count": exact_source_sequence_count,
                "exact_meaning_relation_count": exact_meaning_relation_count,
                "q80_packet_version_count": q80_packet_version_count,
                "accepted_primary_packet_count": accepted_primary_packet_count,
                "conditional_heldout_packet_count": conditional_heldout_packet_count,
                "component_exact_source_hit_count": component_exact_source_hit_count,
                "packet_level_exact_source_hit_count": packet_level_exact_source_hit_count,
                "packet_method_support_count": packet_method_support_count,
                "structural_edge_candidate_count": structural_edge_candidate_count,
                "confirmed_edge_count": confirmed_edge_count,
                "source_resolution_count": source_resolution_count,
                "firewall_blocked_candidate_count": firewall_blocked_candidate_count,
                "lexical_ready_count": lexical_ready_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
            }
        )
    )


if __name__ == "__main__":
    main()
