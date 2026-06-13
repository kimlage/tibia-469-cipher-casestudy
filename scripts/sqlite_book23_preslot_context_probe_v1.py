#!/usr/bin/env python3
"""Probe book23 as pre-slot/context-to-slot candidate, not direct NAESE slot."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3

from sqlite_operational_grammar_reconstruction_probe import DB, classify_states, edge_score, load_books

POSITIVES = {"2": "CANONICAL_SLOT", "22": "CANONICAL_SLOT", "51": "R02_SLOT_BRIDGE", "53": "R02_SLOT_BRIDGE"}
NEGATIVES = {"28": "NAESE_VARIANT", "48": "NAESE_VARIANT", "42": "HYBRID_AUDIT", "56": "WEAK_AUDIT"}


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute('''CREATE TABLE IF NOT EXISTS book23_preslot_context_probe_v1_runs (run_id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL, decision TEXT NOT NULL, positive_margin REAL NOT NULL, has_literal_naese INTEGER NOT NULL, has_accepted_naese_node INTEGER NOT NULL, payload_json TEXT NOT NULL)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS book23_preslot_context_probe_v1_items (run_id INTEGER NOT NULL, edge TEXT NOT NULL, role TEXT NOT NULL, anchor_role TEXT NOT NULL, score REAL NOT NULL, overlap INTEGER NOT NULL, prior REAL NOT NULL, transition_json TEXT NOT NULL, evidence_json TEXT NOT NULL, PRIMARY KEY(run_id, edge))''')
    books = load_books(conn)
    states = {bookid: classify_states(book) for bookid, book in books.items()}
    rows = []
    for anchor, role in POSITIVES.items():
        for edge in [("23", anchor), (anchor, "23")]:
            p = edge_score(books[edge[0]], books[edge[1]], states)
            rows.append({"edge": edge, "role": "positive", "anchor_role": role, "payload": p})
    for anchor, role in NEGATIVES.items():
        for edge in [("23", anchor), (anchor, "23")]:
            p = edge_score(books[edge[0]], books[edge[1]], states)
            rows.append({"edge": edge, "role": "negative", "anchor_role": role, "payload": p})
    best_pos = max((r for r in rows if r["role"] == "positive"), key=lambda r: (r["payload"]["score"], r["payload"]["overlap"]))
    best_neg = max((r for r in rows if r["role"] == "negative"), key=lambda r: (r["payload"]["score"], r["payload"]["overlap"]))
    margin = float(best_pos["payload"]["score"]) - float(best_neg["payload"]["score"])
    literal = books["23"].literal
    has_literal_naese = int("NAESE" in literal)
    has_accepted_naese = int(any("NAESE" in node for node in books["23"].accepted))
    if best_pos["payload"]["score"] >= 110 and margin >= 20 and not has_accepted_naese:
        decision = "BOOK23_PROMOTE_PRE_SLOT_CONTEXT_NO_GLOSS"
    elif best_pos["payload"]["score"] >= 100 and not has_accepted_naese:
        decision = "BOOK23_AUDIT_PRE_SLOT_CONTEXT_LOW_EVIDENCE"
    else:
        decision = "BOOK23_KEEP_UNRESOLVED"
    cur = conn.execute('''INSERT INTO book23_preslot_context_probe_v1_runs (created_at,decision,positive_margin,has_literal_naese,has_accepted_naese_node,payload_json) VALUES (?,?,?,?,?,?)''',(
        now(), decision, round(margin,4), has_literal_naese, has_accepted_naese, json.dumps({"best_positive": f"{best_pos['edge'][0]}->{best_pos['edge'][1]}", "best_negative": f"{best_neg['edge'][0]}->{best_neg['edge'][1]}", "literal_len": len(literal)}, sort_keys=True)
    ))
    run_id = int(cur.lastrowid)
    for r in rows:
        p = r["payload"]
        conn.execute('''INSERT INTO book23_preslot_context_probe_v1_items (run_id,edge,role,anchor_role,score,overlap,prior,transition_json,evidence_json) VALUES (?,?,?,?,?,?,?,?,?)''',(
            run_id, f"{r['edge'][0]}->{r['edge'][1]}", r["role"], r["anchor_role"], p["score"], p["overlap"], p["prior"], json.dumps(p["transition"], sort_keys=True), json.dumps({"shared_nodes": p["shared_nodes"]}, sort_keys=True)
        ))
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": decision, "best_positive": f"{best_pos['edge'][0]}->{best_pos['edge'][1]}", "best_positive_score": best_pos["payload"]["score"], "best_positive_overlap": best_pos["payload"]["overlap"], "best_negative": f"{best_neg['edge'][0]}->{best_neg['edge'][1]}", "best_negative_score": best_neg["payload"]["score"], "margin": round(margin,4), "has_literal_naese": bool(has_literal_naese), "has_accepted_naese_node": bool(has_accepted_naese)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
