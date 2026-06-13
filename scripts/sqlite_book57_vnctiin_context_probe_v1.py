#!/usr/bin/env python3
"""Probe book57 as VNCTIIN pure/expanded context, not C86 payload."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3

from sqlite_operational_grammar_reconstruction_probe import DB, classify_states, edge_score, load_books

POSITIVES = {"27": "C86_VNCTIIN_CONTEXT_PAYLOAD", "67": "C86_VNCTIIN_CONTEXT_PAYLOAD", "35": "HANDOFF_CONTEXT"}
NEGATIVES = {"2": "NAESE_SLOT", "62": "C86_VINVIN_BRANCH", "13": "O23_ENDPOINT", "38": "O23_ENDPOINT", "10": "HANDOFF_CONTEXT_FULL"}


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def token_count(text: str, token: str) -> int:
    return text.count(token)


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute('''CREATE TABLE IF NOT EXISTS book57_vnctiin_context_probe_v1_runs (run_id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL, decision TEXT NOT NULL, positive_margin REAL NOT NULL, vnctiin_count INTEGER NOT NULL, c86_payload_absent INTEGER NOT NULL, payload_json TEXT NOT NULL)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS book57_vnctiin_context_probe_v1_items (run_id INTEGER NOT NULL, edge TEXT NOT NULL, role TEXT NOT NULL, anchor_role TEXT NOT NULL, score REAL NOT NULL, overlap INTEGER NOT NULL, prior REAL NOT NULL, transition_json TEXT NOT NULL, evidence_json TEXT NOT NULL, PRIMARY KEY(run_id, edge))''')
    books = load_books(conn)
    states = {bookid: classify_states(book) for bookid, book in books.items()}
    rows = []
    for anchor, role in POSITIVES.items():
        for edge in [(anchor, "57"), ("57", anchor)]:
            payload = edge_score(books[edge[0]], books[edge[1]], states)
            rows.append({"edge": edge, "role": "positive", "anchor_role": role, "payload": payload})
    for anchor, role in NEGATIVES.items():
        for edge in [(anchor, "57"), ("57", anchor)]:
            payload = edge_score(books[edge[0]], books[edge[1]], states)
            rows.append({"edge": edge, "role": "negative", "anchor_role": role, "payload": payload})
    best_pos = max((r for r in rows if r["role"] == "positive"), key=lambda r: (r["payload"]["score"], r["payload"]["overlap"]))
    best_neg = max((r for r in rows if r["role"] == "negative"), key=lambda r: (r["payload"]["score"], r["payload"]["overlap"]))
    margin = float(best_pos["payload"]["score"]) - float(best_neg["payload"]["score"])
    literal = books["57"].literal
    vnctiin_count = token_count(literal, "VNCTIIN") + token_count(literal, "VNN") + token_count(literal, "NCTIIN")
    c86_absent = int("ICE" not in literal and "C86" not in "".join(books["57"].accepted))
    # Promote only as pure VNCTIIN context if it is not better explained by slot/endpoint/branch and lacks C86 payload markers.
    if best_pos["payload"]["score"] >= 110 and margin >= 10 and c86_absent:
        decision = "BOOK57_PROMOTE_VNCTIIN_EXPANDED_CONTEXT_NO_GLOSS"
    elif best_pos["payload"]["score"] >= 110 and c86_absent:
        decision = "BOOK57_AUDIT_VNCTIIN_CONTEXT_LOW_MARGIN"
    else:
        decision = "BOOK57_KEEP_UNRESOLVED"
    cur = conn.execute('''INSERT INTO book57_vnctiin_context_probe_v1_runs (created_at,decision,positive_margin,vnctiin_count,c86_payload_absent,payload_json) VALUES (?,?,?,?,?,?)''',(
        now(), decision, round(margin,4), vnctiin_count, c86_absent, json.dumps({"best_positive": f"{best_pos['edge'][0]}->{best_pos['edge'][1]}", "best_negative": f"{best_neg['edge'][0]}->{best_neg['edge'][1]}", "literal_len": len(literal)}, sort_keys=True)
    ))
    run_id = int(cur.lastrowid)
    for r in rows:
        p = r["payload"]
        conn.execute('''INSERT INTO book57_vnctiin_context_probe_v1_items (run_id,edge,role,anchor_role,score,overlap,prior,transition_json,evidence_json) VALUES (?,?,?,?,?,?,?,?,?)''',(
            run_id, f"{r['edge'][0]}->{r['edge'][1]}", r["role"], r["anchor_role"], p["score"], p["overlap"], p["prior"], json.dumps(p["transition"], sort_keys=True), json.dumps({"shared_nodes": p["shared_nodes"]}, sort_keys=True)
        ))
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": decision, "best_positive": f"{best_pos['edge'][0]}->{best_pos['edge'][1]}", "best_positive_score": best_pos["payload"]["score"], "best_negative": f"{best_neg['edge'][0]}->{best_neg['edge'][1]}", "best_negative_score": best_neg["payload"]["score"], "margin": round(margin,4), "vnctiin_count": vnctiin_count, "c86_payload_absent": bool(c86_absent)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
