#!/usr/bin/env python3
"""Rank unresolved books by proximity to accepted functional grammar roles."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

from sqlite_operational_grammar_reconstruction_probe import DB, classify_states, edge_score, load_books


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def latest_run(conn: sqlite3.Connection, table: str) -> int:
    return int(conn.execute(f"SELECT max(run_id) FROM {table}").fetchone()[0])


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS unresolved_function_frontier_rank_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            unresolved_count INTEGER NOT NULL,
            top_candidate_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS unresolved_function_frontier_rank_v1_items (
            run_id INTEGER NOT NULL,
            rank INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            score REAL NOT NULL,
            best_anchor_bookid TEXT NOT NULL,
            best_anchor_role TEXT NOT NULL,
            best_direction TEXT NOT NULL,
            recommendation TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        )
        """
    )
    reading_run = latest_run(conn, "honest_full_functional_reading_v1_runs")
    grammar_books = {
        str(r["bookid"]): r
        for r in conn.execute(
            "SELECT bookid,status,functional_reading FROM honest_full_functional_reading_v1_books WHERE run_id=? AND status IN ('FUNCTIONAL_CORE','FUNCTIONAL_RELATED')",
            (reading_run,),
        )
    }
    quarantine_run = conn.execute("SELECT max(run_id) FROM frontier_audit_quarantine_v1_runs").fetchone()[0] if conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='frontier_audit_quarantine_v1_runs'").fetchone() else None
    quarantined = set()
    if quarantine_run is not None:
        quarantined = {str(r["bookid"]) for r in conn.execute("SELECT bookid FROM frontier_audit_quarantine_v1_items WHERE run_id=?", (quarantine_run,))}
    unresolved = [
        str(r["bookid"])
        for r in conn.execute(
            "SELECT bookid FROM honest_full_functional_reading_v1_books WHERE run_id=? AND status='UNRESOLVED_FUNCTION' ORDER BY CAST(bookid AS INT)",
            (reading_run,),
        )
        if str(r["bookid"]) not in quarantined
    ]
    books = load_books(conn)
    states = {bookid: classify_states(book) for bookid, book in books.items()}
    ranked = []
    for bookid in unresolved:
        best = None
        for anchor, anchor_row in grammar_books.items():
            out_payload = edge_score(books[bookid], books[anchor], states)
            in_payload = edge_score(books[anchor], books[bookid], states)
            candidates = [("outgoing", out_payload), ("incoming", in_payload)]
            for direction, payload in candidates:
                composite = float(payload["score"]) + min(int(payload["overlap"]), 40) * 0.5 + float(payload["prior"]) * 10
                item = (composite, direction, anchor, str(anchor_row["functional_reading"]), payload)
                if best is None or item[0] > best[0]:
                    best = item
        assert best is not None
        score, direction, anchor, role, payload = best
        if score >= 130:
            rec = "HIGH_PRIORITY_PROMOTION_PROBE"
        elif score >= 100:
            rec = "MEDIUM_PRIORITY_CONTRAST_PROBE"
        else:
            rec = "LOW_PRIORITY_KEEP_UNRESOLVED"
        ranked.append({"bookid": bookid, "score": round(score, 4), "direction": direction, "anchor": anchor, "role": role, "payload": payload, "recommendation": rec})
    ranked.sort(key=lambda r: (-r["score"], int(r["bookid"])))
    decision = "UNRESOLVED_FUNCTION_FRONTIER_RANKED"
    cur = conn.execute(
        """
        INSERT INTO unresolved_function_frontier_rank_v1_runs
        (created_at, decision, unresolved_count, top_candidate_count, payload_json)
        VALUES (?, ?, ?, ?, ?)
        """,
        (now(), decision, len(unresolved), sum(1 for r in ranked if r["recommendation"] != "LOW_PRIORITY_KEEP_UNRESOLVED"), json.dumps({"reading_run": reading_run, "excluded_frontier_quarantine": sorted(quarantined, key=int) if quarantined else []}, sort_keys=True)),
    )
    run_id = int(cur.lastrowid)
    for idx, r in enumerate(ranked, start=1):
        conn.execute(
            """
            INSERT INTO unresolved_function_frontier_rank_v1_items
            (run_id, rank, bookid, score, best_anchor_bookid, best_anchor_role, best_direction, recommendation, evidence_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, idx, r["bookid"], r["score"], r["anchor"], r["role"], r["direction"], r["recommendation"], json.dumps({"edge_score": r["payload"]}, sort_keys=True)),
        )
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": decision, "unresolved_count": len(unresolved), "top_candidates": [{"rank": i+1, "bookid": r["bookid"], "score": r["score"], "anchor": r["anchor"], "role": r["role"], "direction": r["direction"], "recommendation": r["recommendation"]} for i, r in enumerate(ranked[:10])]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
