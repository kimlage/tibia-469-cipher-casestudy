#!/usr/bin/env python3
"""Reassess hybrid/audit books 42/56/41 as related hybrid functions where safe."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3

from sqlite_operational_grammar_reconstruction_probe import DB, load_books
from sqlite_literal_overlap_frontier_rank_v1 import longest_common_substring

ITEMS = ["42", "56", "41"]
ANCHORS = {
    "NAESE": {"2": "NAESE_SLOT", "22": "NAESE_SLOT"},
    "CONTEXT": {"10": "HANDOFF_CONTEXT", "27": "CONTEXT_PAYLOAD", "35": "HANDOFF_CONTEXT", "67": "CONTEXT_PAYLOAD"},
    "O23": {"13": "O23_ENDPOINT", "38": "O23_ENDPOINT"},
}
NEGATIVE = {"62": "C86_BRANCH", "58": "BENNA_DISPLAY"}


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def nodes_for(book):
    return set(book.accepted)|set(book.audit)|set(book.scoped)


def best(book, anchors, books):
    vals=[]
    for a,r in anchors.items():
        l=longest_common_substring(book.literal, books[a].literal)
        vals.append((len(l),a,r,l))
    return max(vals)


def main() -> None:
    conn=sqlite3.connect(DB, timeout=30)
    conn.row_factory=sqlite3.Row
    conn.execute('PRAGMA busy_timeout=30000')
    conn.execute('''CREATE TABLE IF NOT EXISTS hybrid_quarantine_reassessment_v1_runs (run_id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL, decision TEXT NOT NULL, promoted_count INTEGER NOT NULL, audit_count INTEGER NOT NULL, payload_json TEXT NOT NULL)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS hybrid_quarantine_reassessment_v1_items (run_id INTEGER NOT NULL, bookid TEXT NOT NULL, status TEXT NOT NULL, proposed_role TEXT NOT NULL, best_primary_anchor TEXT NOT NULL, best_primary_lcs INTEGER NOT NULL, best_secondary_anchor TEXT NOT NULL, best_secondary_lcs INTEGER NOT NULL, best_negative_anchor TEXT NOT NULL, best_negative_lcs INTEGER NOT NULL, evidence_json TEXT NOT NULL, PRIMARY KEY(run_id, bookid))''')
    books=load_books(conn)
    rows=[]
    for bookid in ITEMS:
        nodes=nodes_for(books[bookid])
        bna=best(books[bookid], ANCHORS['NAESE'], books)
        bcx=best(books[bookid], ANCHORS['CONTEXT'], books)
        bo=best(books[bookid], ANCHORS['O23'], books)
        bn=best(books[bookid], NEGATIVE, books)
        if bookid=='42' and 'NAESE_WEAK_AUDIT_42_56' in nodes and bna[0] >= 33 and bcx[0] >= 27 and bn[0] <= 20:
            status='PROMOTE_CONTEXT_TO_WEAK_NAESE_HYBRID_NO_GLOSS'; role='CONTEXT_TO_WEAK_NAESE_HYBRID'; primary=bna; secondary=bcx
        elif bookid=='56' and 'NAESE_WEAK_AUDIT_42_56' in nodes and 'FNAAST_O23_ENDPOINT_WINDOW' in nodes and bo[0] >= 32 and bna[0] >= 27 and bn[0] <= 20:
            status='PROMOTE_O23_ENDPOINT_WITH_WEAK_NAESE_TAIL_NO_GLOSS'; role='O23_ENDPOINT_WITH_WEAK_NAESE_TAIL'; primary=bo; secondary=bna
        elif bookid=='41' and bcx[0] >= 32 and bn[0] <= 20:
            status='AUDIT_CONTEXT_FRAGMENT_MODERATE_NO_PROMOTION'; role='CONTEXT_FRAGMENT_AUDIT'; primary=bcx; secondary=bna
        else:
            status='KEEP_QUARANTINED_OR_UNRESOLVED'; role='HYBRID_UNPROVEN'; primary=max([bna,bcx,bo]); secondary=bn
        rows.append({'bookid':bookid,'status':status,'role':role,'primary':primary,'secondary':secondary,'negative':bn,'nodes':sorted(nodes),'all':{'naese':bna,'context':bcx,'o23':bo}})
    promoted=sum(1 for r in rows if r['status'].startswith('PROMOTE'))
    audit=len(rows)-promoted
    decision='HYBRID_QUARANTINE_PARTIAL_PROMOTION' if promoted else 'HYBRID_QUARANTINE_AUDIT_ONLY'
    cur=conn.execute('''INSERT INTO hybrid_quarantine_reassessment_v1_runs (created_at,decision,promoted_count,audit_count,payload_json) VALUES (?,?,?,?,?)''',(now(),decision,promoted,audit,json.dumps({'items':ITEMS},sort_keys=True)))
    run_id=int(cur.lastrowid)
    for r in rows:
        conn.execute('''INSERT INTO hybrid_quarantine_reassessment_v1_items (run_id,bookid,status,proposed_role,best_primary_anchor,best_primary_lcs,best_secondary_anchor,best_secondary_lcs,best_negative_anchor,best_negative_lcs,evidence_json) VALUES (?,?,?,?,?,?,?,?,?,?,?)''',(run_id,r['bookid'],r['status'],r['role'],r['primary'][1],r['primary'][0],r['secondary'][1],r['secondary'][0],r['negative'][1],r['negative'][0],json.dumps({'nodes':r['nodes'],'primary_lcs':r['primary'][3],'secondary_lcs':r['secondary'][3],'negative_lcs':r['negative'][3]},sort_keys=True)))
    conn.commit()
    print(json.dumps({'run_id':run_id,'decision':decision,'promoted_count':promoted,'audit_count':audit,'items':[{'bookid':r['bookid'],'status':r['status'],'role':r['role'],'primary_anchor':r['primary'][1],'primary_lcs':r['primary'][0],'secondary_anchor':r['secondary'][1],'secondary_lcs':r['secondary'][0],'negative_lcs':r['negative'][0]} for r in rows]},ensure_ascii=False))


if __name__=='__main__':
    main()
