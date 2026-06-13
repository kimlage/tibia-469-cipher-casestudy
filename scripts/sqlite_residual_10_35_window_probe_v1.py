#!/usr/bin/env python3
"""Probe residual 10/35 windows as handoff-context window fragments."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3

from sqlite_operational_grammar_reconstruction_probe import DB, load_books
from sqlite_literal_overlap_frontier_rank_v1 import longest_common_substring

GROUP = ["1", "63", "41"]
CORE_ANCHORS = {"10": "HANDOFF_CONTEXT", "35": "HANDOFF_CONTEXT", "27": "C86_VNCTIIN_CONTEXT_PAYLOAD"}
NEGATIVE_ANCHORS = {"2": "NAESE_SLOT", "58": "FRAME_FORMULA_OPERATOR", "62": "C86_VINVIN_BRANCH"}


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def nodes_for(book) -> set[str]:
    return set(book.accepted) | set(book.audit) | set(book.scoped)


def main() -> None:
    conn=sqlite3.connect(DB, timeout=30)
    conn.row_factory=sqlite3.Row
    conn.execute('PRAGMA busy_timeout=30000')
    conn.execute('''CREATE TABLE IF NOT EXISTS residual_10_35_window_probe_v1_runs (run_id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL, decision TEXT NOT NULL, promoted_count INTEGER NOT NULL, audit_count INTEGER NOT NULL, payload_json TEXT NOT NULL)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS residual_10_35_window_probe_v1_items (run_id INTEGER NOT NULL, bookid TEXT NOT NULL, status TEXT NOT NULL, proposed_role TEXT NOT NULL, best_positive_anchor TEXT NOT NULL, best_positive_lcs INTEGER NOT NULL, best_negative_anchor TEXT NOT NULL, best_negative_lcs INTEGER NOT NULL, evidence_json TEXT NOT NULL, PRIMARY KEY(run_id, bookid))''')
    books=load_books(conn)
    rows=[]
    for bookid in GROUP:
        positives=[]
        negatives=[]
        for anchor, role in CORE_ANCHORS.items():
            lcs=longest_common_substring(books[bookid].literal, books[anchor].literal)
            positives.append((len(lcs),anchor,role,lcs))
        for anchor, role in NEGATIVE_ANCHORS.items():
            lcs=longest_common_substring(books[bookid].literal, books[anchor].literal)
            negatives.append((len(lcs),anchor,role,lcs))
        best_pos=max(positives)
        best_neg=max(negatives)
        nodes=nodes_for(books[bookid])
        has_strong='RESIDUAL_STRONG_10_35_WINDOWS' in nodes
        has_moderate='RESIDUAL_MODERATE_FORMULA_WINDOWS' in nodes
        margin=best_pos[0]-best_neg[0]
        if has_strong and best_pos[0] >= 36 and margin >= 15:
            status='PROMOTE_HANDOFF_CONTEXT_WINDOW_FRAGMENT_NO_GLOSS'
            role='HANDOFF_CONTEXT_WINDOW_FRAGMENT'
        elif (has_strong or has_moderate) and best_pos[0] >= 30:
            status='AUDIT_HANDOFF_CONTEXT_WINDOW_FRAGMENT'
            role='HANDOFF_CONTEXT_WINDOW_AUDIT'
        else:
            status='KEEP_UNRESOLVED'
            role='UNRESOLVED_FUNCTION'
        rows.append({'bookid':bookid,'status':status,'role':role,'best_pos':best_pos,'best_neg':best_neg,'nodes':sorted(nodes),'margin':margin})
    promoted=sum(1 for r in rows if r['status'].startswith('PROMOTE'))
    audit=len(rows)-promoted
    decision='RESIDUAL_10_35_WINDOW_PARTIAL_PROMOTION' if promoted else 'RESIDUAL_10_35_WINDOW_AUDIT_ONLY'
    cur=conn.execute('''INSERT INTO residual_10_35_window_probe_v1_runs (created_at,decision,promoted_count,audit_count,payload_json) VALUES (?,?,?,?,?)''',(now(),decision,promoted,audit,json.dumps({'group':GROUP,'core_anchors':CORE_ANCHORS,'negative_anchors':NEGATIVE_ANCHORS},sort_keys=True)))
    run_id=int(cur.lastrowid)
    for r in rows:
        conn.execute('''INSERT INTO residual_10_35_window_probe_v1_items (run_id,bookid,status,proposed_role,best_positive_anchor,best_positive_lcs,best_negative_anchor,best_negative_lcs,evidence_json) VALUES (?,?,?,?,?,?,?,?,?)''',(run_id,r['bookid'],r['status'],r['role'],r['best_pos'][1],r['best_pos'][0],r['best_neg'][1],r['best_neg'][0],json.dumps({'nodes':r['nodes'],'margin':r['margin'],'positive_lcs':r['best_pos'][3],'negative_lcs':r['best_neg'][3]},sort_keys=True)))
    conn.commit()
    print(json.dumps({'run_id':run_id,'decision':decision,'promoted_count':promoted,'audit_count':audit,'items':[{'bookid':r['bookid'],'status':r['status'],'role':r['role'],'best_positive':r['best_pos'][1],'best_positive_lcs':r['best_pos'][0],'best_negative':r['best_neg'][1],'best_negative_lcs':r['best_neg'][0],'margin':r['margin']} for r in rows]},ensure_ascii=False))


if __name__=='__main__':
    main()
