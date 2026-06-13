#!/usr/bin/env python3
"""Q74: audit exact external/source search for Book27->67 sequences."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

SEARCH_TERMS = [
    "LFSENSTAEFIEIEFIIVFATFTFNLIBEITEITAILBETFTE",
    "ITEITAILBETFTE*ICEVIEFIINI*VNCTIIN",
    "VNCTIINNVETTAFSETBASEFA",
    "CEVIEFIINI*VNCTIIN",
]

WEB_QUERIES = [
    '"LFSENSTAEFIEIEFIIVFATFTFNLIBEITEITAILBETFTE" Tibia',
    '"ITEITAILBETFTE" "CEVIEFIINI" Tibia',
    '"VNCTIIN" "TAILBETFTE" "Tibia"',
    '"CEVIEFIINI" "VNCTIIN" "NAESE"',
]

LOCAL_MATCHES = [
    {
        "path": "data/exports/functional_row0/functional_row0_contigs.jsonl",
        "source_class": "INTERNAL_EXPORT",
        "match_role": "contains canonical functional row0 contig export 58->35->67->2",
        "external_support": 0,
    },
    {
        "path": "data/exports/functional_row0/functional_row0_books.jsonl",
        "source_class": "INTERNAL_EXPORT",
        "match_role": "contains internal functional row0 book exports for 2/10/27/35/67",
        "external_support": 0,
    },
    {
        "path": "data/exports/functional_row0/functional_row0_contigs.txt",
        "source_class": "INTERNAL_EXPORT",
        "match_role": "contains internal collapsed contig text",
        "external_support": 0,
    },
    {
        "path": "scripts/sqlite_tailbetfte_suffix_frame_gate.py",
        "source_class": "INTERNAL_SCRIPT",
        "match_role": "contains prior local gate term for TAILBETFTE/C86 context",
        "external_support": 0,
    },
]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q74_book27_to_67_external_exact_search_audit_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q73_run_id INTEGER NOT NULL,
            q67_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            target_edge TEXT NOT NULL,
            web_query_count INTEGER NOT NULL,
            web_exact_external_hit_count INTEGER NOT NULL,
            local_search_term_count INTEGER NOT NULL,
            local_match_path_count INTEGER NOT NULL,
            local_external_support_count INTEGER NOT NULL,
            internal_only_match_count INTEGER NOT NULL,
            external_sequence_confirmation_count INTEGER NOT NULL,
            source_resolution_count INTEGER NOT NULL,
            candidate_status_preserved_count INTEGER NOT NULL,
            lexical_ready_count INTEGER NOT NULL,
            direct_gloss_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            result_human_version TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q74_book27_to_67_external_exact_search_audit_v1_matches (
            run_id INTEGER NOT NULL,
            match_id TEXT NOT NULL,
            path TEXT NOT NULL,
            source_class TEXT NOT NULL,
            match_role TEXT NOT NULL,
            external_support INTEGER NOT NULL,
            match_status TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, match_id)
        );

        CREATE TABLE IF NOT EXISTS human_q74_book27_to_67_external_exact_search_audit_v1_queries (
            run_id INTEGER NOT NULL,
            query_id TEXT NOT NULL,
            query_text TEXT NOT NULL,
            exact_external_hit_count INTEGER NOT NULL,
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

    q73 = latest_row(conn, "human_q73_book27_to_67_confirmation_gate_v1_runs")
    q67 = latest_row(conn, "human_q67_lexical_anchor_probe_queue_v1_runs")
    audit = latest_row(conn, "human_translation_completion_audit_v5_runs")

    web_query_count = len(WEB_QUERIES)
    web_exact_external_hit_count = 0
    local_search_term_count = len(SEARCH_TERMS)
    local_match_path_count = len(LOCAL_MATCHES)
    local_external_support_count = sum(item["external_support"] for item in LOCAL_MATCHES)
    internal_only_match_count = sum(1 for item in LOCAL_MATCHES if item["external_support"] == 0)
    external_sequence_confirmation_count = 0
    source_resolution_count = 0
    candidate_status_preserved_count = 1
    lexical_ready_count = 0
    direct_gloss_count = 0
    canonical_promotion_allowed_count = 0
    result_human_version = (
        "Q74 finds no exact external web/source confirmation for 27->67 or its key Book27/67 sequence terms. "
        "Local exact matches are internal exports or scripts only, so Q73's structural candidate status is preserved "
        "without source resolution, gloss, or canonical promotion."
    )
    decision = (
        "Q74_27_TO_67_EXTERNAL_EXACT_SEARCH_NO_EXTERNAL_CONFIRMATION_NO_GLOSS"
        if web_query_count == 4
        and web_exact_external_hit_count == 0
        and local_search_term_count == 4
        and local_match_path_count == 4
        and local_external_support_count == 0
        and internal_only_match_count == 4
        and external_sequence_confirmation_count == 0
        and source_resolution_count == 0
        and int(q73["structural_candidate_strengthened_count"]) == 1
        and int(q73["confirmed_edge_count"]) == 0
        and int(q67["lexical_ready_count"]) == 0
        and int(audit["promoted_gloss_count"]) == 0
        and lexical_ready_count == 0
        and direct_gloss_count == 0
        and canonical_promotion_allowed_count == 0
        else "Q74_27_TO_67_EXTERNAL_EXACT_SEARCH_REQUIRES_REVIEW"
    )
    payload = {
        "question": "Does exact online/local source search confirm 27->67 externally?",
        "answer": result_human_version,
        "search_terms": SEARCH_TERMS,
        "web_queries": WEB_QUERIES,
        "blocked_use": "Do not treat internal exports as independent external source support.",
        "next_action": "Use 27->67 as structural shadow only; continue looking for external source/provenance separately.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q74_book27_to_67_external_exact_search_audit_v1_runs (
                created_at, decision, q73_run_id, q67_run_id,
                completion_audit_run_id, target_edge, web_query_count,
                web_exact_external_hit_count, local_search_term_count,
                local_match_path_count, local_external_support_count,
                internal_only_match_count, external_sequence_confirmation_count,
                source_resolution_count, candidate_status_preserved_count,
                lexical_ready_count, direct_gloss_count,
                canonical_promotion_allowed_count, result_human_version,
                payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                int(q73["run_id"]),
                int(q67["run_id"]),
                int(audit["run_id"]),
                str(q73["target_edge"]),
                web_query_count,
                web_exact_external_hit_count,
                local_search_term_count,
                local_match_path_count,
                local_external_support_count,
                internal_only_match_count,
                external_sequence_confirmation_count,
                source_resolution_count,
                candidate_status_preserved_count,
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
            INSERT INTO human_q74_book27_to_67_external_exact_search_audit_v1_queries (
                run_id, query_id, query_text, exact_external_hit_count,
                query_status, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    f"Q74_WEB_{idx:02d}",
                    query,
                    0,
                    "NO_EXACT_EXTERNAL_WEB_HIT",
                    j({"query": query, "exact_external_hit_count": 0}),
                )
                for idx, query in enumerate(WEB_QUERIES, start=1)
            ],
        )
        conn.executemany(
            """
            INSERT INTO human_q74_book27_to_67_external_exact_search_audit_v1_matches (
                run_id, match_id, path, source_class, match_role,
                external_support, match_status, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    f"Q74_LOCAL_{idx:02d}",
                    item["path"],
                    item["source_class"],
                    item["match_role"],
                    item["external_support"],
                    "INTERNAL_ONLY_NOT_EXTERNAL_SOURCE",
                    j(item),
                )
                for idx, item in enumerate(LOCAL_MATCHES, start=1)
            ],
        )

    print(
        j(
            {
                "run_id": run_id,
                "decision": decision,
                "target_edge": str(q73["target_edge"]),
                "web_query_count": web_query_count,
                "web_exact_external_hit_count": web_exact_external_hit_count,
                "local_search_term_count": local_search_term_count,
                "local_match_path_count": local_match_path_count,
                "local_external_support_count": local_external_support_count,
                "internal_only_match_count": internal_only_match_count,
                "external_sequence_confirmation_count": external_sequence_confirmation_count,
                "source_resolution_count": source_resolution_count,
                "candidate_status_preserved_count": candidate_status_preserved_count,
                "lexical_ready_count": lexical_ready_count,
                "direct_gloss_count": direct_gloss_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
            }
        )
    )


if __name__ == "__main__":
    main()
