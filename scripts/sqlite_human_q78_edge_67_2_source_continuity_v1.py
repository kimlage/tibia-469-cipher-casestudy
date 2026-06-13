#!/usr/bin/env python3
"""Q78: execute Q67 edge 67->2 phrase-path source continuity probe."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

PROBE_ID = "Q67_P04_EDGE_67_2_PHRASE_PATH_CONTINUITY"

SOURCE_CHECKS = [
    {
        "source_id": "GREAT_CALCULATOR_GATHER_LANGUAGE",
        "source_url": "https://www.tibiawiki.com.br/wiki/You_Cannot_Even_Imagine_%28Book%29",
        "web_ref": "2026-05-11 web check, lines 43-52",
        "continuity_value": "Supports assembled/compiled Bonelord-language material as a corpus-structure model.",
        "blocked_inference": "Does not name Book67, Book2, 67->2, or any exact 469 phrase meaning.",
        "source_result": "PASSES_METHOD_SUPPORT_NO_EXACT_EDGE",
    },
    {
        "source_id": "BEWARE_LANGUAGE_MATH_NUMERIC_BOOKS",
        "source_url": "https://tibia.fandom.com/wiki/Beware_of_the_Bonelords_%28Book%29",
        "web_ref": "2026-05-11 web check, lines 303-310",
        "continuity_value": "Supports numeric/mathematical language and numeric Bonelord books as the right search register.",
        "blocked_inference": "Does not identify 67->2, 35->67->2, or a specific plaintext relation.",
        "source_result": "PASSES_METHOD_SUPPORT_NO_EXACT_EDGE",
    },
]

WEB_QUERIES = [
    {
        "query_id": "Q78_WEB_01",
        "query_text": '"67->2" "Bonelord"',
        "result_status": "NO_EXACT_EDGE_HIT",
        "notes": "No relevant in-game or wiki result for the literal edge.",
    },
    {
        "query_id": "Q78_WEB_02",
        "query_text": '"Book 67" "Book 2" "469" "Tibia"',
        "result_status": "NO_EXACT_EDGE_HIT",
        "notes": "No result that binds Book67 to Book2 as a sourced phrase path.",
    },
    {
        "query_id": "Q78_WEB_03",
        "query_text": '"CEVIEFIINI" "VNCTIIN"',
        "result_status": "NO_EXACT_SEQUENCE_HIT",
        "notes": "No independent exact-source hit for the Book2 C86/VNCTIIN phrase fragment.",
    },
    {
        "query_id": "Q78_WEB_04",
        "query_text": '"Tibia" "35->67->2"',
        "result_status": "NO_EXACT_PATH_HIT",
        "notes": "No independent exact-source hit for the structural path notation.",
    },
]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q78_edge_67_2_source_continuity_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q67_run_id INTEGER NOT NULL,
            q64_run_id INTEGER NOT NULL,
            q55_run_id INTEGER NOT NULL,
            q59_run_id INTEGER NOT NULL,
            q77_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            probe_id TEXT NOT NULL,
            local_phrase_path_accept_count INTEGER NOT NULL,
            q64_passing_contrast_count INTEGER NOT NULL,
            q64_control_edge_fail_count INTEGER NOT NULL,
            source_check_count INTEGER NOT NULL,
            source_method_support_count INTEGER NOT NULL,
            exact_edge_source_count INTEGER NOT NULL,
            exact_phrase_parallel_count INTEGER NOT NULL,
            web_exact_hit_count INTEGER NOT NULL,
            lexical_ready_count INTEGER NOT NULL,
            direct_gloss_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            continuity_human_version TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q78_edge_67_2_source_continuity_v1_sources (
            run_id INTEGER NOT NULL,
            source_id TEXT NOT NULL,
            source_url TEXT NOT NULL,
            web_ref TEXT NOT NULL,
            continuity_value TEXT NOT NULL,
            blocked_inference TEXT NOT NULL,
            source_result TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, source_id)
        );

        CREATE TABLE IF NOT EXISTS human_q78_edge_67_2_source_continuity_v1_controls (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            book_class TEXT NOT NULL,
            q54_edge_status TEXT NOT NULL,
            q36_contig_status TEXT NOT NULL,
            q59_route_role TEXT NOT NULL,
            edge_condition_status TEXT NOT NULL,
            continuity_role TEXT NOT NULL,
            control_result TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        );

        CREATE TABLE IF NOT EXISTS human_q78_edge_67_2_source_continuity_v1_queries (
            run_id INTEGER NOT NULL,
            query_id TEXT NOT NULL,
            query_text TEXT NOT NULL,
            result_status TEXT NOT NULL,
            notes TEXT NOT NULL,
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


def q55_sources(conn: sqlite3.Connection, q55_run_id: int) -> dict[str, sqlite3.Row]:
    rows = conn.execute(
        """
        SELECT *
        FROM human_q55_source_parallel_audit_q54_v1_sources
        WHERE run_id=?
        """,
        (q55_run_id,),
    ).fetchall()
    return {str(row["source_id"]): row for row in rows}


def q64_books(conn: sqlite3.Connection, q64_run_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT *
        FROM human_q64_edge_67_2_handoff_role_contrast_v1_books
        WHERE run_id=? AND bookid IN ('2', '27', '35', '42', '67')
        ORDER BY CAST(bookid AS INTEGER)
        """,
        (q64_run_id,),
    ).fetchall()


def control_status(row: sqlite3.Row) -> tuple[str, str, str]:
    bookid = str(row["bookid"])
    edge_status = str(row["q54_edge_status"])
    contig_status = str(row["q36_contig_status"])
    route_role = str(row["q59_route_role"])
    if bookid == "67" and edge_status == "EDGE_CONFIRMED":
        return (
            "EDGE_CONDITION_PASSES_TARGET",
            "handoff edge inside 35->67->2",
            "TARGET_SUPPORTS_CONTINUITY",
        )
    if bookid == "2" and edge_status == "EDGE_CONFIRMED":
        return (
            "EDGE_CONDITION_PASSES_RECEIVER",
            "slot/classifier target receiving handoff",
            "TARGET_SUPPORTS_CONTINUITY",
        )
    if bookid == "35" and contig_status == "EXACT_CONTIG_SHADOW_AVAILABLE" and edge_status != "EDGE_CONFIRMED":
        return (
            "EDGE_CONDITION_FAILS_UPSTREAM_CONTROL",
            "upstream formula/context route, not 67->2 edge",
            "CONTROL_FAILS_SAME_EDGE_CONDITION",
        )
    if bookid == "27" and edge_status != "EDGE_CONFIRMED":
        return (
            "EDGE_CONDITION_FAILS_HELDOUT_CONTROL",
            "heldout payload/context control",
            "CONTROL_FAILS_SAME_EDGE_CONDITION",
        )
    if bookid == "42" and edge_status != "EDGE_CONFIRMED":
        return (
            "EDGE_CONDITION_FAILS_BOUNDARY_CONTROL",
            "boundary/audit control",
            "CONTROL_FAILS_SAME_EDGE_CONDITION",
        )
    return (
        "EDGE_CONDITION_REQUIRES_REVIEW",
        f"unclassified route role: {route_role}",
        "CONTROL_REQUIRES_REVIEW",
    )


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q67 = latest_row(conn, "human_q67_lexical_anchor_probe_queue_v1_runs")
    q64 = latest_row(conn, "human_q64_edge_67_2_handoff_role_contrast_v1_runs")
    q55 = latest_row(conn, "human_q55_source_parallel_audit_q54_v1_runs")
    q59 = latest_row(conn, "human_q59_consolidated_shadow_backbone_v1_runs")
    q77 = latest_row(conn, "human_q77_high_priority_probe_synthesis_v1_runs")
    audit = latest_row(conn, "human_translation_completion_audit_v5_runs")

    probe = q67_probe(conn, int(q67["run_id"]))
    sources_by_id = q55_sources(conn, int(q55["run_id"]))
    q64_book_rows = q64_books(conn, int(q64["run_id"]))
    source_rows = []
    for spec in SOURCE_CHECKS:
        source = sources_by_id.get(spec["source_id"])
        if source is None:
            raise RuntimeError(f"missing source: {spec['source_id']}")
        source_rows.append({**spec, "q55_source": dict(source)})

    control_rows = []
    for row in q64_book_rows:
        edge_condition_status, continuity_role, control_result = control_status(row)
        control_rows.append(
            {
                "bookid": str(row["bookid"]),
                "book_class": str(row["book_class"]),
                "q54_edge_status": str(row["q54_edge_status"]),
                "q36_contig_status": str(row["q36_contig_status"]),
                "q59_route_role": str(row["q59_route_role"]),
                "edge_condition_status": edge_condition_status,
                "continuity_role": continuity_role,
                "control_result": control_result,
                "evidence": dict(row),
            }
        )

    local_phrase_path_accept_count = int(q64["phrase_path_accept_count"])
    q64_passing_contrast_count = int(q64["passing_contrast_count"])
    q64_control_edge_fail_count = sum(
        1 for row in control_rows if row["control_result"] == "CONTROL_FAILS_SAME_EDGE_CONDITION"
    )
    source_check_count = len(source_rows)
    source_method_support_count = sum(
        1 for row in source_rows if row["source_result"] == "PASSES_METHOD_SUPPORT_NO_EXACT_EDGE"
    )
    exact_edge_source_count = 0
    exact_phrase_parallel_count = 0
    web_exact_hit_count = 0
    lexical_ready_count = 0
    direct_gloss_count = 0
    canonical_promotion_allowed_count = 0
    continuity_human_version = (
        "Q78 supports 35->67->2 as a source-compatible phrase path only: Q64 accepts the local "
        "67->2 handoff and its controls, while Great Calculator and Beware support assembled, "
        "numeric/mathematical Bonelord-language material. No checked source names the 67->2 edge, "
        "the 35->67->2 path, or an exact plaintext meaning."
    )
    decision = (
        "Q78_EDGE_67_2_SOURCE_CONTINUITY_METHOD_SUPPORT_NO_EXACT_PHRASE_NO_GLOSS"
        if str(probe["probe_id"]) == PROBE_ID
        and local_phrase_path_accept_count == 1
        and q64_passing_contrast_count == 5
        and q64_control_edge_fail_count == 3
        and source_check_count == 2
        and source_method_support_count == 2
        and exact_edge_source_count == 0
        and exact_phrase_parallel_count == 0
        and web_exact_hit_count == 0
        and int(q59["canonical_promotion_allowed_count"]) == 0
        and int(q77["canonical_promotion_allowed_count"]) == 0
        and int(audit["promoted_gloss_count"]) == 0
        else "Q78_EDGE_67_2_SOURCE_CONTINUITY_REQUIRES_REVIEW"
    )
    payload = {
        "question": str(probe["search_question"]),
        "answer": continuity_human_version,
        "required_evidence": str(probe["required_evidence"]),
        "rejection_rule": str(probe["rejection_rule"]),
        "next_action": "Use 35->67->2 as a human-shadow packet path, then run the global source firewall before any lexical claim.",
        "blocked_use": "Do not translate Book67 or Book2 as a sentence from this continuity evidence.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q78_edge_67_2_source_continuity_v1_runs (
                created_at, decision, q67_run_id, q64_run_id, q55_run_id,
                q59_run_id, q77_run_id, completion_audit_run_id, probe_id,
                local_phrase_path_accept_count, q64_passing_contrast_count,
                q64_control_edge_fail_count, source_check_count,
                source_method_support_count, exact_edge_source_count,
                exact_phrase_parallel_count, web_exact_hit_count,
                lexical_ready_count, direct_gloss_count,
                canonical_promotion_allowed_count, continuity_human_version,
                payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                int(q67["run_id"]),
                int(q64["run_id"]),
                int(q55["run_id"]),
                int(q59["run_id"]),
                int(q77["run_id"]),
                int(audit["run_id"]),
                PROBE_ID,
                local_phrase_path_accept_count,
                q64_passing_contrast_count,
                q64_control_edge_fail_count,
                source_check_count,
                source_method_support_count,
                exact_edge_source_count,
                exact_phrase_parallel_count,
                web_exact_hit_count,
                lexical_ready_count,
                direct_gloss_count,
                canonical_promotion_allowed_count,
                continuity_human_version,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q78_edge_67_2_source_continuity_v1_sources (
                run_id, source_id, source_url, web_ref, continuity_value,
                blocked_inference, source_result, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    row["source_id"],
                    row["source_url"],
                    row["web_ref"],
                    row["continuity_value"],
                    row["blocked_inference"],
                    row["source_result"],
                    j(row),
                )
                for row in source_rows
            ],
        )
        conn.executemany(
            """
            INSERT INTO human_q78_edge_67_2_source_continuity_v1_controls (
                run_id, bookid, book_class, q54_edge_status,
                q36_contig_status, q59_route_role, edge_condition_status,
                continuity_role, control_result, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    row["bookid"],
                    row["book_class"],
                    row["q54_edge_status"],
                    row["q36_contig_status"],
                    row["q59_route_role"],
                    row["edge_condition_status"],
                    row["continuity_role"],
                    row["control_result"],
                    j(row["evidence"]),
                )
                for row in control_rows
            ],
        )
        conn.executemany(
            """
            INSERT INTO human_q78_edge_67_2_source_continuity_v1_queries (
                run_id, query_id, query_text, result_status, notes, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    row["query_id"],
                    row["query_text"],
                    row["result_status"],
                    row["notes"],
                    j(row),
                )
                for row in WEB_QUERIES
            ],
        )

    print(
        j(
            {
                "run_id": run_id,
                "decision": decision,
                "probe_id": PROBE_ID,
                "local_phrase_path_accept_count": local_phrase_path_accept_count,
                "q64_passing_contrast_count": q64_passing_contrast_count,
                "q64_control_edge_fail_count": q64_control_edge_fail_count,
                "source_method_support_count": source_method_support_count,
                "exact_edge_source_count": exact_edge_source_count,
                "exact_phrase_parallel_count": exact_phrase_parallel_count,
                "web_exact_hit_count": web_exact_hit_count,
                "lexical_ready_count": lexical_ready_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
            }
        )
    )


if __name__ == "__main__":
    main()
