#!/usr/bin/env python3
"""Reassess quarantined VINVIN/C86 books 68/44 as related fragments."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3

from sqlite_operational_grammar_reconstruction_probe import DB, load_books
from sqlite_literal_overlap_frontier_rank_v1 import longest_common_substring

GROUP = ["68", "44"]
C86_ANCHORS = {"3": "C86_PAYLOAD_BRANCH", "17": "C86_PAYLOAD_BRANCH", "52": "C86_PAYLOAD_BRANCH", "62": "C86_PAYLOAD_BRANCH"}
R20_ANCHORS = {"29": "R20_BRANCH_HEAD", "65": "R20_CONNECTOR_ENDPOINT"}
NEGATIVE = {"2": "NAESE_SLOT", "58": "BENNA_DISPLAY"}


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def nodes_for(book) -> set[str]:
    return set(book.accepted) | set(book.audit) | set(book.scoped)


def best_lcs(book, anchors, books):
    vals=[]
    for a,r in anchors.items():
        l=longest_common_substring(book.literal, books[a].literal)
        vals.append((len(l),a,r,l))
    return max(vals)


def main() -> None:
    conn=sqlite3.connect(DB, timeout=30)
    conn.row_factory=sqlite3.Row
    conn.execute('PRAGMA busy_timeout=30000')
    conn.execute('''CREATE TABLE IF NOT EXISTS vinvin_fragment_reassessment_v1_runs (run_id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL, decision TEXT NOT NULL, promoted_count INTEGER NOT NULL, audit_count INTEGER NOT NULL, payload_json TEXT NOT NULL)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS vinvin_fragment_reassessment_v1_items (run_id INTEGER NOT NULL, bookid TEXT NOT NULL, status TEXT NOT NULL, proposed_role TEXT NOT NULL, best_c86_anchor TEXT NOT NULL, best_c86_lcs INTEGER NOT NULL, best_r20_anchor TEXT NOT NULL, best_r20_lcs INTEGER NOT NULL, best_negative_anchor TEXT NOT NULL, best_negative_lcs INTEGER NOT NULL, evidence_json TEXT NOT NULL, PRIMARY KEY(run_id, bookid))''')
    books=load_books(conn)
    rows=[]
    for bookid in GROUP:
        bc=best_lcs(books[bookid], C86_ANCHORS, books)
        br=best_lcs(books[bookid], R20_ANCHORS, books)
        bn=best_lcs(books[bookid], NEGATIVE, books)
        nodes=nodes_for(books[bookid])
        if bookid == '44' and 'C86_PAYLOAD_OPERATOR' in nodes and bc[0] >= 50 and (bc[0]-bn[0]) >= 35:
            status='PROMOTE_C86_VINVIN_SURFACE_PAYLOAD_FRAGMENT_NO_GLOSS'
            role='C86_VINVIN_SURFACE_PAYLOAD_FRAGMENT'
        elif bookid == '68' and 'BOOK68_IN_17_VINVIN_NEGATIVE_WINDOW' in nodes and bc[0] >= 60 and (bc[0]-bn[0]) >= 35:
            status='PROMOTE_VINVIN_NEGATIVE_WINDOW_FRAGMENT_NO_GLOSS'
            role='VINVIN_NEGATIVE_WINDOW_FRAGMENT'
        elif bc[0] >= 45:
            status='AUDIT_VINVIN_FRAGMENT'
            role='VINVIN_FRAGMENT_AUDIT'
        else:
            status='KEEP_QUARANTINED'
            role='VINVIN_FRAGMENT_QUARANTINE'
        rows.append({'bookid':bookid,'status':status,'role':role,'bc':bc,'br':br,'bn':bn,'nodes':sorted(nodes)})
    promoted=sum(1 for r in rows if r['status'].startswith('PROMOTE'))
    audit=len(rows)-promoted
    decision='VINVIN_FRAGMENT_REASSESSMENT_PARTIAL_PROMOTION' if promoted else 'VINVIN_FRAGMENT_REASSESSMENT_AUDIT_ONLY'
    cur=conn.execute('''INSERT INTO vinvin_fragment_reassessment_v1_runs (created_at,decision,promoted_count,audit_count,payload_json) VALUES (?,?,?,?,?)''',(now(),decision,promoted,audit,json.dumps({'group':GROUP},sort_keys=True)))
    run_id=int(cur.lastrowid)
    for r in rows:
        conn.execute('''INSERT INTO vinvin_fragment_reassessment_v1_items (run_id,bookid,status,proposed_role,best_c86_anchor,best_c86_lcs,best_r20_anchor,best_r20_lcs,best_negative_anchor,best_negative_lcs,evidence_json) VALUES (?,?,?,?,?,?,?,?,?,?,?)''',(run_id,r['bookid'],r['status'],r['role'],r['bc'][1],r['bc'][0],r['br'][1],r['br'][0],r['bn'][1],r['bn'][0],json.dumps({'nodes':r['nodes'],'c86_lcs':r['bc'][3],'r20_lcs':r['br'][3],'negative_lcs':r['bn'][3]},sort_keys=True)))
    conn.commit()
    print(json.dumps({'run_id':run_id,'decision':decision,'promoted_count':promoted,'audit_count':audit,'items':[{'bookid':r['bookid'],'status':r['status'],'role':r['role'],'c86_anchor':r['bc'][1],'c86_lcs':r['bc'][0],'r20_anchor':r['br'][1],'r20_lcs':r['br'][0],'negative_lcs':r['bn'][0]} for r in rows]},ensure_ascii=False))


if __name__=='__main__':
    main()
