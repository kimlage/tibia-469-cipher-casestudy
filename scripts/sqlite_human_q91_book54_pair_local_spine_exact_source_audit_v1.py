#!/usr/bin/env python3
"""Q91: exact-source audit for Q82 T06 Book54 local-pair spine route."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
TARGET_ID = "Q82_T06_BOOK54_PAIR_LOCAL_SPINE"

WEB_QUERIES = [
    {
        "query_id": "Q91_WEB_01",
        "query_text": '"FLTFNTFEIFAIFAINIIETNEEIVNALN"',
        "result_status": "NO_RELEVANT_EXACT_SOURCE_HIT",
        "notes": "No exact web hit for the full Book54 row0 text.",
    },
    {
        "query_id": "Q91_WEB_02",
        "query_text": '"LTFNTFEIFAIFAINIIETNEEIVN" "Tibia"',
        "result_status": "NO_RELEVANT_EXACT_SOURCE_HIT",
        "notes": "No exact source hit for the Book20/54 shared block.",
    },
    {
        "query_id": "Q91_WEB_03",
        "query_text": '"Book 54" "469" "LTFNTFE"',
        "result_status": "NO_TARGET_SOURCE_HIT",
        "notes": "No source-backed Book54/LTFNTFE meaning relation.",
    },
    {
        "query_id": "Q91_WEB_04",
        "query_text": '"Book 20" "Book 54" "469"',
        "result_status": "NO_INDEPENDENT_PAIR_SOURCE",
        "notes": "No independent in-game pair convention source found.",
    },
    {
        "query_id": "Q91_WEB_05",
        "query_text": 'site:tibia.com "FLTFNTFE"',
        "result_status": "NO_OFFICIAL_EXACT_HIT",
        "notes": "No official tibia.com exact hit for FLTFNTFE.",
    },
    {
        "query_id": "Q91_WEB_06",
        "query_text": 'site:tibiawiki.com.br "LTFNTFEIFAIFAINIIETNEEIVN"',
        "result_status": "NO_WIKI_EXACT_TARGET_HIT",
        "notes": "No TibiaWiki BR exact target hit for the shared spine.",
    },
]

SOURCE_CHECKS = [
    {
        "source_id": "BOOK54_PAIR_SHADOW",
        "source_url": "sqlite:human_book54_pair_shadow_probe_v1_runs",
        "source_result": "SHARED_CORE_WITH_OWN_TAIL_NO_GLOSS",
        "support_value": "Book20/54 share a 25-symbol block; Book54 coverage is 0.8621 of shorter row.",
        "blocked_inference": "Shared block, prefix, and tail are not lexical words or sentence prose.",
    },
    {
        "source_id": "BOOK20_54_LOCAL_PAIR_CONTEXT",
        "source_url": "sqlite:human_q5_book20_54_local_pair_context_probe_v1_runs",
        "source_result": "SAME_LIBRARY_NOT_PHYSICALLY_ADJACENT",
        "support_value": "Pair has same-library support and external location sources.",
        "blocked_inference": "No physical adjacency and no independent in-game pair convention.",
    },
    {
        "source_id": "PKG5_BOOK54_LOCAL_PAIR_FALSIFICATION",
        "source_url": "sqlite:human_promotion_pkg5_book54_local_pair_falsification_v1_runs",
        "source_result": "FUNCTIONAL_LOCAL_PAIR_LABEL_NO_GLOSS",
        "support_value": "Functional local-pair/shared-spine label survived package checks.",
        "blocked_inference": "The package explicitly blocks plaintext and shared-block word glosses.",
    },
    {
        "source_id": "ZERO_PAIR_LOCAL_CONTEXT_GATE",
        "source_url": "sqlite:zero_pair_local_context_gate_runs",
        "source_result": "LOCAL_CONTEXT_READY_NO_GLOSS",
        "support_value": "Zero-pair local contexts provide accepted pair controls with no lexical gloss.",
        "blocked_inference": "Zero-boundary or local-pair context cannot import taboo/semantic value.",
    },
    {
        "source_id": "GREAT_CALCULATOR_COMPILED_CORPUS_SPINES",
        "source_url": "sqlite:human_q30_great_calculator_compiled_corpus_spine_map_v1_runs",
        "source_result": "COMPILED_CORPUS_SPINE_MODEL_SUPPORT",
        "support_value": "Compiled-corpus model makes spine/pair readings method-compatible.",
        "blocked_inference": "Method compatibility is not an exact Book54 meaning source.",
    },
    {
        "source_id": "RESIDUAL_LOCAL_PAIR_BRIDGE",
        "source_url": "sqlite:human_residual_bridge_v1_items",
        "source_result": "LOCAL_PAIR_RESIDUAL_SUPPORT_NO_GLOSS",
        "support_value": "Residual bridge keeps 20/54 and related pairs as local-pair controls.",
        "blocked_inference": "Local pair/template controls are not independent prose.",
    },
    {
        "source_id": "TIBIASECRETS_HELLGATE_AVERAGE_ROUTE",
        "source_url": "https://www.tibiasecrets.com/article166",
        "source_result": "EXTERNAL_NUMERIC_METHOD_PRESSURE_ONLY",
        "support_value": "External arithmetic/average work supports non-linear book relationships.",
        "blocked_inference": "External method pressure cannot promote Book54 or the shared spine.",
    },
    {
        "source_id": "S2WARD_469_CORPUS",
        "source_url": "https://github.com/s2ward/469",
        "source_result": "EXTERNAL_CORPUS_STRUCTURE_SUPPORT_ONLY",
        "support_value": "External corpus work supports book/spine comparison as a research method.",
        "blocked_inference": "External corpus comparison is not an in-game exact meaning source.",
    },
]

TESTS = [
    {
        "test_id": "Q91_T01_WEB_EXACT_BOOK54_SEQUENCE",
        "test_result": "FAILS_EXACT_SOURCE_REQUIREMENT",
        "interpretation": "No web query found exact Book54/shared-spine sequence plus meaning/provenance.",
    },
    {
        "test_id": "Q91_T02_LOCAL_PAIR_MECHANICS",
        "test_result": "PRESERVE_FUNCTIONAL_PAIR_LABEL",
        "interpretation": "Book54/20 local-pair spine remains structurally strong.",
    },
    {
        "test_id": "Q91_T03_LOCATION_CONTEXT",
        "test_result": "SAME_LIBRARY_ONLY_NOT_ADJACENT",
        "interpretation": "Location context supports same library, but not physical adjacency or a pair convention.",
    },
    {
        "test_id": "Q91_T04_ZERO_PAIR_CONTEXT",
        "test_result": "PRESERVE_CONTEXT_NO_SEMANTIC_IMPORT",
        "interpretation": "Zero-boundary/local-pair contexts remain controls, not semantics.",
    },
    {
        "test_id": "Q91_T05_PROMOTION_FIREWALL",
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
        CREATE TABLE IF NOT EXISTS human_q91_book54_pair_local_spine_exact_source_audit_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q82_run_id INTEGER NOT NULL,
            book54_pair_run_id INTEGER NOT NULL,
            q5_pair_context_run_id INTEGER NOT NULL,
            pkg5_run_id INTEGER NOT NULL,
            zero_pair_gate_run_id INTEGER NOT NULL,
            q81_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            target_id TEXT NOT NULL,
            target_book_count INTEGER NOT NULL,
            web_query_count INTEGER NOT NULL,
            web_exact_target_hit_count INTEGER NOT NULL,
            official_exact_target_hit_count INTEGER NOT NULL,
            source_check_count INTEGER NOT NULL,
            exact_source_sequence_count INTEGER NOT NULL,
            exact_meaning_relation_count INTEGER NOT NULL,
            shared_block_length INTEGER NOT NULL,
            lcs_ratio_shorter REAL NOT NULL,
            same_library_count INTEGER NOT NULL,
            physical_adjacency_count INTEGER NOT NULL,
            independent_pair_convention_count INTEGER NOT NULL,
            promoted_functional_label_count INTEGER NOT NULL,
            lexical_ready_count INTEGER NOT NULL,
            direct_gloss_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            target_status TEXT NOT NULL,
            result_human_version TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q91_book54_pair_local_spine_exact_source_audit_v1_queries (
            run_id INTEGER NOT NULL,
            query_id TEXT NOT NULL,
            query_text TEXT NOT NULL,
            result_status TEXT NOT NULL,
            notes TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, query_id)
        );

        CREATE TABLE IF NOT EXISTS human_q91_book54_pair_local_spine_exact_source_audit_v1_sources (
            run_id INTEGER NOT NULL,
            source_id TEXT NOT NULL,
            source_url TEXT NOT NULL,
            source_result TEXT NOT NULL,
            support_value TEXT NOT NULL,
            blocked_inference TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, source_id)
        );

        CREATE TABLE IF NOT EXISTS human_q91_book54_pair_local_spine_exact_source_audit_v1_books (
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

        CREATE TABLE IF NOT EXISTS human_q91_book54_pair_local_spine_exact_source_audit_v1_tests (
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
    book54_pair = latest_row(conn, "human_book54_pair_shadow_probe_v1_runs")
    q5_context = latest_row(conn, "human_q5_book20_54_local_pair_context_probe_v1_runs")
    pkg5 = latest_row(conn, "human_promotion_pkg5_book54_local_pair_falsification_v1_runs")
    zero_pair_gate = latest_row(conn, "zero_pair_local_context_gate_runs")
    q81 = latest_row(conn, "human_q81_controlled_shadow_export_v1_runs")
    completion = latest_row(conn, "human_translation_completion_audit_v5_runs")
    books = load_books(conn, int(q82["run_id"]))

    target_book_count = len(books)
    web_query_count = len(WEB_QUERIES)
    web_exact_target_hit_count = 0
    official_exact_target_hit_count = 0
    source_check_count = len(SOURCE_CHECKS)
    exact_source_sequence_count = 0
    exact_meaning_relation_count = 0
    shared_block_length = int(book54_pair["lcs_len"])
    lcs_ratio_shorter = float(book54_pair["lcs_ratio_shorter"])
    same_library_count = int(q5_context["same_library_count"])
    physical_adjacency_count = int(q5_context["physical_adjacency_count"])
    independent_pair_convention_count = int(q5_context["independent_ingame_pair_convention_count"])
    promoted_functional_label_count = int(pkg5["promoted_functional_label_count"])
    lexical_ready_count = 0
    direct_gloss_count = 0
    canonical_promotion_allowed_count = 0
    target_status = "SOURCE_AUDITED_LOCAL_PAIR_SUPPORT_NO_PROMOTION"
    result_human_version = (
        "Q91 preserves Book54 as the shorter member of a Book20/54 local pair with a shared spine. "
        "The local mechanics are strong, but no checked source confirms the pair outside local alignment "
        "or gives the shared block a meaning."
    )
    decision = (
        "Q91_BOOK54_PAIR_LOCAL_SPINE_EXACT_SOURCE_AUDIT_LOCAL_PAIR_SUPPORT_NO_EXACT_SOURCE_NO_GLOSS"
        if target_book_count == 1
        and web_query_count == 6
        and web_exact_target_hit_count == 0
        and official_exact_target_hit_count == 0
        and source_check_count == 8
        and exact_source_sequence_count == 0
        and exact_meaning_relation_count == 0
        and shared_block_length == 25
        and lcs_ratio_shorter >= 0.86
        and same_library_count >= 1
        and physical_adjacency_count == 0
        and independent_pair_convention_count == 0
        and promoted_functional_label_count == 1
        and int(zero_pair_gate["lexical_gloss_allowed"]) == 0
        and int(q81["promoted_gloss_count"]) == 0
        and int(completion["promoted_gloss_count"]) == 0
        else "Q91_BOOK54_PAIR_LOCAL_SPINE_EXACT_SOURCE_AUDIT_REQUIRES_REVIEW"
    )
    payload = {
        "answer": result_human_version,
        "allowed_use": "Use Book54 as a local-pair/shared-spine human shadow and control.",
        "blocked_use": "Do not translate FLTFNTFE, shared spine, prefix F, tail ALN, zero, pair, or spine as words.",
        "next_action": "Move to Q82_T08_CHAYENNE_FRAME_REGISTER with external-frame firewall active.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q91_book54_pair_local_spine_exact_source_audit_v1_runs (
                created_at, decision, q82_run_id, book54_pair_run_id,
                q5_pair_context_run_id, pkg5_run_id, zero_pair_gate_run_id,
                q81_run_id, completion_audit_run_id, target_id,
                target_book_count, web_query_count, web_exact_target_hit_count,
                official_exact_target_hit_count, source_check_count,
                exact_source_sequence_count, exact_meaning_relation_count,
                shared_block_length, lcs_ratio_shorter, same_library_count,
                physical_adjacency_count, independent_pair_convention_count,
                promoted_functional_label_count, lexical_ready_count,
                direct_gloss_count, canonical_promotion_allowed_count,
                target_status, result_human_version, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                int(q82["run_id"]),
                int(book54_pair["run_id"]),
                int(q5_context["run_id"]),
                int(pkg5["run_id"]),
                int(zero_pair_gate["run_id"]),
                int(q81["run_id"]),
                int(completion["run_id"]),
                TARGET_ID,
                target_book_count,
                web_query_count,
                web_exact_target_hit_count,
                official_exact_target_hit_count,
                source_check_count,
                exact_source_sequence_count,
                exact_meaning_relation_count,
                shared_block_length,
                lcs_ratio_shorter,
                same_library_count,
                physical_adjacency_count,
                independent_pair_convention_count,
                promoted_functional_label_count,
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
            INSERT INTO human_q91_book54_pair_local_spine_exact_source_audit_v1_queries (
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
            INSERT INTO human_q91_book54_pair_local_spine_exact_source_audit_v1_sources (
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
            INSERT INTO human_q91_book54_pair_local_spine_exact_source_audit_v1_books (
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
                    "PRESERVE_BOOK54_LOCAL_PAIR_SPINE_SHADOW_ONLY",
                    j(dict(row)),
                )
                for row in books
            ],
        )
        conn.executemany(
            """
            INSERT INTO human_q91_book54_pair_local_spine_exact_source_audit_v1_tests (
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
                "web_exact_target_hit_count": web_exact_target_hit_count,
                "official_exact_target_hit_count": official_exact_target_hit_count,
                "source_check_count": source_check_count,
                "exact_source_sequence_count": exact_source_sequence_count,
                "exact_meaning_relation_count": exact_meaning_relation_count,
                "shared_block_length": shared_block_length,
                "lcs_ratio_shorter": lcs_ratio_shorter,
                "same_library_count": same_library_count,
                "physical_adjacency_count": physical_adjacency_count,
                "independent_pair_convention_count": independent_pair_convention_count,
                "promoted_functional_label_count": promoted_functional_label_count,
                "lexical_ready_count": lexical_ready_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
            }
        )
    )


if __name__ == "__main__":
    main()
