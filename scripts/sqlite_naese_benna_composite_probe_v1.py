#!/usr/bin/env python3
"""Probe books 5/9 as NAESE-to-BENNA composite frames."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3

from sqlite_operational_grammar_reconstruction_probe import DB, load_books
from sqlite_literal_overlap_frontier_rank_v1 import longest_common_substring

GROUP = ["5", "9"]
NAESE_ANCHORS = {"53": "R02_SLOT_BRIDGE", "2": "NAESE_SLOT", "22": "NAESE_SLOT"}
BENNA_ANCHORS = {"47": "BENNA_TEMPLATE_HEAD", "69": "BENNA_MIXED_HEAD", "40": "BENNA_FORMULA_BODY", "58": "BENNA_DISPLAY_HEAD"}
NEGATIVE = {"13": "O23_ENDPOINT", "62": "C86_VINVIN_BRANCH"}


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main() -> None:
    conn=sqlite3.connect(DB, timeout=30)
    conn.row_factory=sqlite3.Row
    conn.execute('PRAGMA busy_timeout=30000')
    conn.execute('''CREATE TABLE IF NOT EXISTS naese_benna_composite_probe_v1_runs (run_id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL, decision TEXT NOT NULL, promoted_count INTEGER NOT NULL, audit_count INTEGER NOT NULL, payload_json TEXT NOT NULL)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS naese_benna_composite_probe_v1_items (run_id INTEGER NOT NULL, bookid TEXT NOT NULL, status TEXT NOT NULL, proposed_role TEXT NOT NULL, best_naese_anchor TEXT NOT NULL, best_naese_lcs INTEGER NOT NULL, best_benna_anchor TEXT NOT NULL, best_benna_lcs INTEGER NOT NULL, best_negative_anchor TEXT NOT NULL, best_negative_lcs INTEGER NOT NULL, evidence_json TEXT NOT NULL, PRIMARY KEY(run_id, bookid))''')
    books=load_books(conn)
    rows=[]
    for bookid in GROUP:
        na=[]; be=[]; ne=[]
        for a,r in NAESE_ANCHORS.items():
            l=longest_common_substring(books[bookid].literal, books[a].literal); na.append((len(l),a,r,l))
        for a,r in BENNA_ANCHORS.items():
            l=longest_common_substring(books[bookid].literal, books[a].literal); be.append((len(l),a,r,l))
        for a,r in NEGATIVE.items():
            l=longest_common_substring(books[bookid].literal, books[a].literal); ne.append((len(l),a,r,l))
        bn=max(na); bb=max(be); bg=max(ne)
        # Composite requires strong evidence for both NAESE-side and BENNA-side segments.
        if bn[0] >= 55 and bb[0] >= 48 and bg[0] < min(bn[0], bb[0]) - 20:
            status='PROMOTE_NAESE_TO_BENNA_COMPOSITE_FRAME_NO_GLOSS'
            role='NAESE_TO_BENNA_COMPOSITE_FRAME'
        elif bn[0] >= 45 and bb[0] >= 35:
            status='AUDIT_NAESE_TO_BENNA_COMPOSITE_FRAME'
            role='NAESE_TO_BENNA_COMPOSITE_AUDIT'
        else:
            status='KEEP_QUARANTINED'
            role='COMPOSITE_UNPROVEN'
        rows.append({'bookid':bookid,'status':status,'role':role,'bn':bn,'bb':bb,'bg':bg})
    promoted=sum(1 for r in rows if r['status'].startswith('PROMOTE'))
    audit=len(rows)-promoted
    decision='NAESE_BENNA_COMPOSITE_PARTIAL_PROMOTION' if promoted else 'NAESE_BENNA_COMPOSITE_AUDIT_ONLY'
    cur=conn.execute('''INSERT INTO naese_benna_composite_probe_v1_runs (created_at,decision,promoted_count,audit_count,payload_json) VALUES (?,?,?,?,?)''',(now(),decision,promoted,audit,json.dumps({'group':GROUP,'naese_anchors':NAESE_ANCHORS,'benna_anchors':BENNA_ANCHORS,'negative':NEGATIVE},sort_keys=True)))
    run_id=int(cur.lastrowid)
    for r in rows:
        conn.execute('''INSERT INTO naese_benna_composite_probe_v1_items (run_id,bookid,status,proposed_role,best_naese_anchor,best_naese_lcs,best_benna_anchor,best_benna_lcs,best_negative_anchor,best_negative_lcs,evidence_json) VALUES (?,?,?,?,?,?,?,?,?,?,?)''',(run_id,r['bookid'],r['status'],r['role'],r['bn'][1],r['bn'][0],r['bb'][1],r['bb'][0],r['bg'][1],r['bg'][0],json.dumps({'naese_lcs':r['bn'][3],'benna_lcs':r['bb'][3],'negative_lcs':r['bg'][3]},sort_keys=True)))
    conn.commit()
    print(json.dumps({'run_id':run_id,'decision':decision,'promoted_count':promoted,'audit_count':audit,'items':[{'bookid':r['bookid'],'status':r['status'],'role':r['role'],'naese_anchor':r['bn'][1],'naese_lcs':r['bn'][0],'benna_anchor':r['bb'][1],'benna_lcs':r['bb'][0],'negative_anchor':r['bg'][1],'negative_lcs':r['bg'][0]} for r in rows]},ensure_ascii=False))


if __name__=='__main__':
    main()
