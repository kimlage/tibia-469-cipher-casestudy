#!/usr/bin/env python3
"""Reassess BENNA display/formula quarantines as related variants."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3

from sqlite_operational_grammar_reconstruction_probe import DB, load_books
from sqlite_literal_overlap_frontier_rank_v1 import longest_common_substring

DISPLAY_GROUP = ["11", "43", "59"]
FORMULA_GROUP = ["50"]
DISPLAY_ANCHORS = {"58": "BENNA_DISPLAY_FORMULA_HEAD"}
FORMULA_ANCHORS = {"9": "NAESE_BENNA_COMPOSITE", "69": "BENNA_MIXED_HEAD", "40": "BENNA_FORMULA_BODY", "47": "BENNA_TEMPLATE_HEAD"}
NEGATIVE = {"2": "NAESE_SLOT", "62": "C86_BRANCH", "13": "O23_ENDPOINT"}


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def best_lcs(book, anchors, books):
    vals=[]
    for a,r in anchors.items():
        l=longest_common_substring(book.literal, books[a].literal)
        vals.append((len(l),a,r,l))
    return max(vals)


def nodes_for(book):
    return set(book.accepted)|set(book.audit)|set(book.scoped)


def main() -> None:
    conn=sqlite3.connect(DB, timeout=30)
    conn.row_factory=sqlite3.Row
    conn.execute('PRAGMA busy_timeout=30000')
    conn.execute('''CREATE TABLE IF NOT EXISTS benna_display_variant_reassessment_v1_runs (run_id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL, decision TEXT NOT NULL, promoted_count INTEGER NOT NULL, audit_count INTEGER NOT NULL, payload_json TEXT NOT NULL)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS benna_display_variant_reassessment_v1_items (run_id INTEGER NOT NULL, bookid TEXT NOT NULL, status TEXT NOT NULL, proposed_role TEXT NOT NULL, best_positive_anchor TEXT NOT NULL, best_positive_lcs INTEGER NOT NULL, best_negative_anchor TEXT NOT NULL, best_negative_lcs INTEGER NOT NULL, evidence_json TEXT NOT NULL, PRIMARY KEY(run_id, bookid))''')
    books=load_books(conn)
    rows=[]
    for bookid in DISPLAY_GROUP:
        bp=best_lcs(books[bookid], DISPLAY_ANCHORS, books); bn=best_lcs(books[bookid], NEGATIVE, books)
        nodes=nodes_for(books[bookid])
        if 'BENNA_NSBVN_DISPLAY_WINDOW' in nodes and bp[0] >= 60 and (bp[0]-bn[0]) >= 35:
            status='PROMOTE_BENNA_DISPLAY_WINDOW_VARIANT_NO_GLOSS'; role='BENNA_DISPLAY_WINDOW_VARIANT'
        else:
            status='AUDIT_BENNA_DISPLAY_WINDOW_VARIANT'; role='BENNA_DISPLAY_WINDOW_AUDIT'
        rows.append({'bookid':bookid,'status':status,'role':role,'bp':bp,'bn':bn,'nodes':sorted(nodes)})
    for bookid in FORMULA_GROUP:
        bp=best_lcs(books[bookid], FORMULA_ANCHORS, books); bn=best_lcs(books[bookid], NEGATIVE, books)
        nodes=nodes_for(books[bookid])
        if 'BENNA_FORMULA_BRIDGE' in nodes and bp[0] >= 60 and (bp[0]-bn[0]) >= 35:
            status='PROMOTE_BENNA_FORMULA_COMPOSITE_VARIANT_NO_GLOSS'; role='BENNA_FORMULA_COMPOSITE_VARIANT'
        elif 'BENNA_FORMULA_BRIDGE' in nodes and bp[0] >= 45:
            status='PROMOTE_BENNA_FORMULA_BODY_VARIANT_NO_GLOSS'; role='BENNA_FORMULA_BODY_VARIANT'
        else:
            status='AUDIT_BENNA_FORMULA_VARIANT'; role='BENNA_FORMULA_AUDIT'
        rows.append({'bookid':bookid,'status':status,'role':role,'bp':bp,'bn':bn,'nodes':sorted(nodes)})
    promoted=sum(1 for r in rows if r['status'].startswith('PROMOTE'))
    audit=len(rows)-promoted
    decision='BENNA_DISPLAY_VARIANTS_PARTIAL_PROMOTION' if promoted else 'BENNA_DISPLAY_VARIANTS_AUDIT_ONLY'
    cur=conn.execute('''INSERT INTO benna_display_variant_reassessment_v1_runs (created_at,decision,promoted_count,audit_count,payload_json) VALUES (?,?,?,?,?)''',(now(),decision,promoted,audit,json.dumps({'display_group':DISPLAY_GROUP,'formula_group':FORMULA_GROUP},sort_keys=True)))
    run_id=int(cur.lastrowid)
    for r in rows:
        conn.execute('''INSERT INTO benna_display_variant_reassessment_v1_items (run_id,bookid,status,proposed_role,best_positive_anchor,best_positive_lcs,best_negative_anchor,best_negative_lcs,evidence_json) VALUES (?,?,?,?,?,?,?,?,?)''',(run_id,r['bookid'],r['status'],r['role'],r['bp'][1],r['bp'][0],r['bn'][1],r['bn'][0],json.dumps({'nodes':r['nodes'],'positive_lcs':r['bp'][3],'negative_lcs':r['bn'][3]},sort_keys=True)))
    conn.commit()
    print(json.dumps({'run_id':run_id,'decision':decision,'promoted_count':promoted,'audit_count':audit,'items':[{'bookid':r['bookid'],'status':r['status'],'role':r['role'],'positive_anchor':r['bp'][1],'positive_lcs':r['bp'][0],'negative_anchor':r['bn'][1],'negative_lcs':r['bn'][0]} for r in rows]},ensure_ascii=False))


if __name__=='__main__':
    main()
