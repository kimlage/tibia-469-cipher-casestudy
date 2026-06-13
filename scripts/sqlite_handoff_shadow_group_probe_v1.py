#!/usr/bin/env python3
"""Probe unresolved books 8/24/31/37 as a handoff/context shadow group."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

from sqlite_operational_grammar_reconstruction_probe import DB, classify_states, edge_score, load_books

GROUP = ["8", "24", "31", "37"]
ANCHORS = ["10", "35"]
NEGATIVE_ANCHORS = ["40", "58", "2", "62"]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def lcs_len(a: str, b: str) -> int:
    best = 0
    prev = [0] * (len(b) + 1)
    for ca in a:
        cur = [0]
        for j, cb in enumerate(b, start=1):
            val = prev[j - 1] + 1 if ca == cb else 0
            cur.append(val)
            best = max(best, val)
        prev = cur
    return best


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS handoff_shadow_group_probe_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            group_size INTEGER NOT NULL,
            promoted_count INTEGER NOT NULL,
            quarantined_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS handoff_shadow_group_probe_v1_items (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            status TEXT NOT NULL,
            proposed_role TEXT NOT NULL,
            best_positive_anchor TEXT NOT NULL,
            best_positive_score REAL NOT NULL,
            best_negative_anchor TEXT NOT NULL,
            best_negative_score REAL NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        )
        """
    )
    books = load_books(conn)
    states = {bookid: classify_states(book) for bookid, book in books.items()}
    rows = []
    for bookid in GROUP:
        pos = []
        neg = []
        for anchor in ANCHORS:
            incoming = edge_score(books[anchor], books[bookid], states)
            outgoing = edge_score(books[bookid], books[anchor], states)
            pos.append((incoming["score"], f"{anchor}->{bookid}", incoming, lcs_len(books[anchor].literal, books[bookid].literal)))
            pos.append((outgoing["score"], f"{bookid}->{anchor}", outgoing, lcs_len(books[bookid].literal, books[anchor].literal)))
        for anchor in NEGATIVE_ANCHORS:
            incoming = edge_score(books[anchor], books[bookid], states)
            outgoing = edge_score(books[bookid], books[anchor], states)
            neg.append((incoming["score"], f"{anchor}->{bookid}", incoming, lcs_len(books[anchor].literal, books[bookid].literal)))
            neg.append((outgoing["score"], f"{bookid}->{anchor}", outgoing, lcs_len(books[bookid].literal, books[anchor].literal)))
        best_pos = max(pos, key=lambda x: (x[0], x[3]))
        best_neg = max(neg, key=lambda x: (x[0], x[3]))
        margin = float(best_pos[0]) - float(best_neg[0])
        # These books are allowed as handoff shadows only if they are closer to handoff anchors than negative anchors.
        if best_pos[0] >= 100 and margin >= 20:
            status = "PROMOTE_HANDOFF_CONTEXT_SHADOW_NO_GLOSS"
            role = "HANDOFF_CONTEXT_SHADOW"
        elif best_pos[0] >= 100:
            status = "AUDIT_HANDOFF_LIKE_BUT_LOW_MARGIN"
            role = "HANDOFF_CONTEXT_AUDIT"
        else:
            status = "KEEP_UNRESOLVED"
            role = "UNRESOLVED_FUNCTION"
        rows.append({"bookid": bookid, "status": status, "role": role, "best_pos": best_pos, "best_neg": best_neg, "margin": margin})
    promoted = sum(1 for r in rows if r["status"] == "PROMOTE_HANDOFF_CONTEXT_SHADOW_NO_GLOSS")
    quarantined = len(rows) - promoted
    decision = "HANDOFF_SHADOW_GROUP_PARTIAL_PROMOTION" if promoted else "HANDOFF_SHADOW_GROUP_NOT_PROMOTED"
    cur = conn.execute(
        """
        INSERT INTO handoff_shadow_group_probe_v1_runs
        (created_at, decision, group_size, promoted_count, quarantined_count, payload_json)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (now(), decision, len(rows), promoted, quarantined, json.dumps({"group": GROUP, "positive_anchors": ANCHORS, "negative_anchors": NEGATIVE_ANCHORS}, sort_keys=True)),
    )
    run_id = int(cur.lastrowid)
    for r in rows:
        conn.execute(
            """
            INSERT INTO handoff_shadow_group_probe_v1_items
            (run_id, bookid, status, proposed_role, best_positive_anchor, best_positive_score, best_negative_anchor, best_negative_score, evidence_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, r["bookid"], r["status"], r["role"], r["best_pos"][1], r["best_pos"][0], r["best_neg"][1], r["best_neg"][0], json.dumps({"margin": r["margin"], "positive_payload": r["best_pos"][2], "negative_payload": r["best_neg"][2], "positive_lcs": r["best_pos"][3], "negative_lcs": r["best_neg"][3]}, sort_keys=True)),
        )
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": decision, "promoted_count": promoted, "quarantined_count": quarantined, "items": [{"bookid": r["bookid"], "status": r["status"], "role": r["role"], "best_positive": r["best_pos"][1], "best_positive_score": r["best_pos"][0], "best_negative": r["best_neg"][1], "best_negative_score": r["best_neg"][0], "margin": round(r["margin"], 4)} for r in rows]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
