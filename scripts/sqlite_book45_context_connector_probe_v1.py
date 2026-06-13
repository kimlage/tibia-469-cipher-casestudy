#!/usr/bin/env python3
"""Probe book45 as R02/context connector support, not full slot bridge."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3

from sqlite_operational_grammar_reconstruction_probe import DB, classify_states, edge_score, load_books
from sqlite_literal_overlap_frontier_rank_v1 import longest_common_substring

POSITIVES = {"51": "R02_SLOT_BRIDGE", "53": "R02_SLOT_BRIDGE", "46": "CONTEXT_CONNECTOR"}
NEGATIVES = {"2": "NAESE_SLOT_NO_CONNECTOR", "22": "NAESE_SLOT_NO_CONNECTOR", "65": "R20_CONNECTOR_ENDPOINT", "17": "C86_VINVIN_BRANCH"}


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main() -> None:
    conn=sqlite3.connect(DB, timeout=30)
    conn.row_factory=sqlite3.Row
    conn.execute('PRAGMA busy_timeout=30000')
    conn.execute('''CREATE TABLE IF NOT EXISTS book45_context_connector_probe_v1_runs (run_id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL, decision TEXT NOT NULL, best_positive_lcs INTEGER NOT NULL, best_negative_lcs INTEGER NOT NULL, has_connector_node INTEGER NOT NULL, has_naese_node INTEGER NOT NULL, payload_json TEXT NOT NULL)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS book45_context_connector_probe_v1_items (run_id INTEGER NOT NULL, anchor_bookid TEXT NOT NULL, role TEXT NOT NULL, anchor_role TEXT NOT NULL, lcs_len INTEGER NOT NULL, lcs_text TEXT NOT NULL, edge_score_json TEXT NOT NULL, PRIMARY KEY(run_id, anchor_bookid, role))''')
    books=load_books(conn)
    states={bookid:classify_states(book) for bookid,book in books.items()}
    rows=[]
    for anchor,role in POSITIVES.items():
        lcs=longest_common_substring(books['45'].literal, books[anchor].literal)
        p=edge_score(books['45'], books[anchor], states)
        rows.append({'anchor':anchor,'role':'positive','anchor_role':role,'lcs':lcs,'payload':p})
    for anchor,role in NEGATIVES.items():
        lcs=longest_common_substring(books['45'].literal, books[anchor].literal)
        p=edge_score(books['45'], books[anchor], states)
        rows.append({'anchor':anchor,'role':'negative','anchor_role':role,'lcs':lcs,'payload':p})
    best_pos=max((r for r in rows if r['role']=='positive'), key=lambda r:len(r['lcs']))
    best_neg=max((r for r in rows if r['role']=='negative'), key=lambda r:len(r['lcs']))
    nodes=set(books['45'].accepted)|set(books['45'].audit)|set(books['45'].scoped)
    has_connector=int('TVAETRFEVAST_TRVEIIVNTBB_CONTEXT_CONNECTOR' in nodes)
    has_naese=int(any('NAESE' in n for n in nodes))
    if len(best_pos['lcs']) >= 50 and has_connector and not has_naese:
        decision='BOOK45_PROMOTE_R02_CONTEXT_CONNECTOR_RELATED_NO_GLOSS'
    elif len(best_pos['lcs']) >= 40 and has_connector:
        decision='BOOK45_AUDIT_CONTEXT_CONNECTOR'
    else:
        decision='BOOK45_KEEP_UNRESOLVED'
    cur=conn.execute('''INSERT INTO book45_context_connector_probe_v1_runs (created_at,decision,best_positive_lcs,best_negative_lcs,has_connector_node,has_naese_node,payload_json) VALUES (?,?,?,?,?,?,?)''',(
        now(),decision,len(best_pos['lcs']),len(best_neg['lcs']),has_connector,has_naese,json.dumps({'best_positive':best_pos['anchor'],'best_negative':best_neg['anchor']},sort_keys=True)
    ))
    run_id=int(cur.lastrowid)
    for r in rows:
        conn.execute('''INSERT INTO book45_context_connector_probe_v1_items (run_id,anchor_bookid,role,anchor_role,lcs_len,lcs_text,edge_score_json) VALUES (?,?,?,?,?,?,?)''',(run_id,r['anchor'],r['role'],r['anchor_role'],len(r['lcs']),r['lcs'],json.dumps(r['payload'],sort_keys=True)))
    conn.commit()
    print(json.dumps({'run_id':run_id,'decision':decision,'best_positive':best_pos['anchor'],'best_positive_lcs':len(best_pos['lcs']),'best_negative':best_neg['anchor'],'best_negative_lcs':len(best_neg['lcs']),'has_connector_node':bool(has_connector),'has_naese_node':bool(has_naese)},ensure_ascii=False))


if __name__=='__main__':
    main()
