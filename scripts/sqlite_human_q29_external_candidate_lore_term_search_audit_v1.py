#!/usr/bin/env python3
"""Q29: audit candidate German/MHG lore terms against source-search gates."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

CANDIDATE_TERMS = [
    {
        "term": "SALZBERG",
        "term_class": "candidate_proper_noun",
        "candidate_claim": "King/Speaker-King Salzberg",
        "web_query": '"SALZBERG" "Tibia"',
        "web_result_status": "NO_RELEVANT_TIBIA_LORE_HIT_FOUND_CURRENT_SEARCH",
    },
    {
        "term": "ORANGENSTRASSE",
        "term_class": "candidate_proper_noun",
        "candidate_claim": "Orange Street / Orangenstrasse",
        "web_query": '"ORANGENSTRASSE" "Tibia"',
        "web_result_status": "NO_RELEVANT_TIBIA_LORE_HIT_FOUND_CURRENT_SEARCH",
    },
    {
        "term": "WEICHSTEIN",
        "term_class": "candidate_proper_noun",
        "candidate_claim": "Soft Stone / Weichstein",
        "web_query": '"WEICHSTEIN" "Tibia"',
        "web_result_status": "NO_RELEVANT_TIBIA_LORE_HIT_FOUND_CURRENT_SEARCH",
    },
    {
        "term": "GOTTDIENER",
        "term_class": "candidate_proper_noun",
        "candidate_claim": "God's Servant / Gottdiener",
        "web_query": '"GOTTDIENER" "Tibia"',
        "web_result_status": "NO_RELEVANT_TIBIA_LORE_HIT_FOUND_CURRENT_SEARCH",
    },
    {
        "term": "SCHARDT",
        "term_class": "candidate_proper_noun",
        "candidate_claim": "Schardt place/name",
        "web_query": '"SCHARDT" "Tibia"',
        "web_result_status": "NO_RELEVANT_TIBIA_LORE_HIT_FOUND_CURRENT_SEARCH",
    },
    {
        "term": "THENAEUT",
        "term_class": "candidate_unsolved_name",
        "candidate_claim": "Unsolved proper noun in candidate",
        "web_query": '"THENAEUT" "Tibia"',
        "web_result_status": "NO_RELEVANT_TIBIA_LORE_HIT_FOUND_CURRENT_SEARCH",
    },
    {
        "term": "LGTNELGZ",
        "term_class": "candidate_unsolved_name",
        "candidate_claim": "Unsolved proper noun in candidate",
        "web_query": '"LGTNELGZ" "Tibia"',
        "web_result_status": "NO_RELEVANT_TIBIA_LORE_HIT_FOUND_CURRENT_SEARCH",
    },
]

LOCAL_SEARCH_TABLES = [
    ("external_corpus_sources", ["title", "text", "payload_json"]),
    ("human_ingame_anchor_corpus_v1_items", ["anchor_id", "claim_summary", "allowed_inference", "blocked_inference", "risk"]),
    ("human_external_phrase_corpus_v1_items", ["phrase_id", "source_label", "in_game_anchor", "candidate_use", "evidence_json"]),
    ("human_q26_mathemagic_transcript_bridge_import_v1_items", ["item_id", "role_label", "evidence_json"]),
]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q29_external_candidate_lore_term_search_audit_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q28_run_id INTEGER NOT NULL,
            term_count INTEGER NOT NULL,
            local_source_hit_count INTEGER NOT NULL,
            broad_web_relevant_hit_count INTEGER NOT NULL,
            source_anchor_pass_count INTEGER NOT NULL,
            candidate_lore_bridge_pass_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q29_external_candidate_lore_term_search_audit_v1_items (
            run_id INTEGER NOT NULL,
            term TEXT NOT NULL,
            term_class TEXT NOT NULL,
            status TEXT NOT NULL,
            candidate_claim TEXT NOT NULL,
            local_hits_json TEXT NOT NULL,
            web_query TEXT NOT NULL,
            web_result_status TEXT NOT NULL,
            next_action TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, term)
        );
        """
    )


def latest_run_id(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT max(run_id) FROM {table}").fetchone()
    if row is None or row[0] is None:
        raise RuntimeError(f"missing required run: {table}")
    return int(row[0])


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return (
        conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (table,),
        ).fetchone()
        is not None
    )


def local_hits(conn: sqlite3.Connection, term: str) -> list[dict[str, object]]:
    hits: list[dict[str, object]] = []
    pattern = f"%{term}%"
    for table, columns in LOCAL_SEARCH_TABLES:
        if not table_exists(conn, table):
            continue
        predicates = " OR ".join([f"upper({column}) LIKE upper(?)" for column in columns])
        sql = f"SELECT rowid AS rowid, * FROM {table} WHERE {predicates} LIMIT 5"
        rows = conn.execute(sql, tuple(pattern for _ in columns)).fetchall()
        for row in rows:
            hits.append({"table": table, "rowid": row["rowid"], "row": dict(row)})
    return hits


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q28_run_id = latest_run_id(conn, "human_q28_external_candidate_contig_gate_benchmark_v1_runs")
    item_rows = []
    local_source_hit_count = 0
    broad_web_relevant_hit_count = 0
    for item in CANDIDATE_TERMS:
        hits = local_hits(conn, item["term"])
        local_source_hit_count += len(hits)
        web_hit = int(item["web_result_status"] != "NO_RELEVANT_TIBIA_LORE_HIT_FOUND_CURRENT_SEARCH")
        broad_web_relevant_hit_count += web_hit
        status = (
            "CANDIDATE_TERM_HAS_SOURCE_HIT_REVIEW_REQUIRED"
            if hits or web_hit
            else "CANDIDATE_TERM_UNANCHORED_IN_CURRENT_SOURCE_SEARCH"
        )
        item_rows.append(
            {
                **item,
                "status": status,
                "local_hits_json": j(hits),
                "next_action": (
                    "review source hit before any stronger use"
                    if hits or web_hit
                    else "keep term as candidate-only; do not use as lore anchor"
                ),
                "evidence_json": j(
                    {
                        "local_search_tables": [table for table, _ in LOCAL_SEARCH_TABLES],
                        "local_hit_count": len(hits),
                        "web_result_status": item["web_result_status"],
                    }
                ),
            }
        )

    source_anchor_pass_count = int(local_source_hit_count > 0 or broad_web_relevant_hit_count > 0)
    candidate_lore_bridge_pass_count = 0
    canonical_promotion_allowed_count = 0
    decision = (
        "Q29_EXTERNAL_CANDIDATE_LORE_TERMS_UNANCHORED_KEEP_AUDIT_ONLY"
        if len(item_rows) == len(CANDIDATE_TERMS)
        and local_source_hit_count == 0
        and broad_web_relevant_hit_count == 0
        and source_anchor_pass_count == 0
        and candidate_lore_bridge_pass_count == 0
        and canonical_promotion_allowed_count == 0
        else "Q29_EXTERNAL_CANDIDATE_LORE_TERM_SEARCH_REQUIRES_MANUAL_REVIEW"
    )
    payload = {
        "question": "Do the German/MHG candidate's strongest names/terms anchor to current Tibia sources?",
        "answer": "No. Current local source tables and broad web searches found no relevant Tibia lore hits for the checked terms.",
        "blocked_reading": "Do not use candidate proper nouns as in-game anchors.",
        "next_action": "Only reopen a term if an exact in-game book/NPC/quest source contains it or a clear cognate with provenance.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q29_external_candidate_lore_term_search_audit_v1_runs (
                created_at, decision, q28_run_id, term_count,
                local_source_hit_count, broad_web_relevant_hit_count,
                source_anchor_pass_count, candidate_lore_bridge_pass_count,
                canonical_promotion_allowed_count, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                q28_run_id,
                len(item_rows),
                local_source_hit_count,
                broad_web_relevant_hit_count,
                source_anchor_pass_count,
                candidate_lore_bridge_pass_count,
                canonical_promotion_allowed_count,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q29_external_candidate_lore_term_search_audit_v1_items (
                run_id, term, term_class, status, candidate_claim,
                local_hits_json, web_query, web_result_status, next_action,
                evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    str(row["term"]),
                    str(row["term_class"]),
                    str(row["status"]),
                    str(row["candidate_claim"]),
                    str(row["local_hits_json"]),
                    str(row["web_query"]),
                    str(row["web_result_status"]),
                    str(row["next_action"]),
                    str(row["evidence_json"]),
                )
                for row in item_rows
            ],
        )

    print(
        j(
            {
                "run_id": run_id,
                "decision": decision,
                "q28_run_id": q28_run_id,
                "term_count": len(item_rows),
                "local_source_hit_count": local_source_hit_count,
                "broad_web_relevant_hit_count": broad_web_relevant_hit_count,
                "source_anchor_pass_count": source_anchor_pass_count,
                "candidate_lore_bridge_pass_count": candidate_lore_bridge_pass_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
            }
        )
    )


if __name__ == "__main__":
    main()
