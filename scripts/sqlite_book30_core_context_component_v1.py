#!/usr/bin/env python3
"""Promote BOOK30_CORE_CONTEXT family as related functional component if internally stable."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3

from sqlite_operational_grammar_reconstruction_probe import DB, load_books
from sqlite_literal_overlap_frontier_rank_v1 import longest_common_substring

GROUP = ["12", "21", "26", "30"]
NEGATIVE = {"2": "NAESE_SLOT", "13": "O23_ENDPOINT", "62": "C86_BRANCH", "58": "BENNA_DISPLAY"}


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def nodes_for(book):
    return set(book.accepted)|set(book.audit)|set(book.scoped)


def main() -> None:
    conn=sqlite3.connect(DB, timeout=30)
    conn.row_factory=sqlite3.Row
    conn.execute('PRAGMA busy_timeout=30000')
    conn.execute('''CREATE TABLE IF NOT EXISTS book30_core_context_component_v1_runs (run_id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL, decision TEXT NOT NULL, promoted_count INTEGER NOT NULL, audit_count INTEGER NOT NULL, min_internal_lcs INTEGER NOT NULL, max_negative_lcs INTEGER NOT NULL, payload_json TEXT NOT NULL)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS book30_core_context_component_v1_items (run_id INTEGER NOT NULL, bookid TEXT NOT NULL, status TEXT NOT NULL, proposed_role TEXT NOT NULL, best_internal_anchor TEXT NOT NULL, best_internal_lcs INTEGER NOT NULL, best_negative_anchor TEXT NOT NULL, best_negative_lcs INTEGER NOT NULL, evidence_json TEXT NOT NULL, PRIMARY KEY(run_id, bookid))''')
    books=load_books(conn)
    rows=[]
    for bookid in GROUP:
        internal=[]
        for other in GROUP:
            if other==bookid: continue
            l=longest_common_substring(books[bookid].literal, books[other].literal)
            internal.append((len(l),other,l))
        negatives=[]
        for a,r in NEGATIVE.items():
            l=longest_common_substring(books[bookid].literal, books[a].literal)
            negatives.append((len(l),a,r,l))
        bi=max(internal); bn=max(negatives)
        nodes=nodes_for(books[bookid])
        if 'BOOK30_CORE_CONTEXT' in nodes and bi[0] >= 45 and bn[0] <= 25:
            status='PROMOTE_BOOK30_CORE_CONTEXT_COMPONENT_NO_GLOSS'; role='BOOK30_CORE_CONTEXT_COMPONENT'
        elif 'BOOK30_CORE_CONTEXT' in nodes and bi[0] >= 35:
            status='AUDIT_BOOK30_CORE_CONTEXT_COMPONENT'; role='BOOK30_CORE_CONTEXT_AUDIT'
        else:
            status='KEEP_UNRESOLVED'; role='BOOK30_CONTEXT_UNPROVEN'
        rows.append({'bookid':bookid,'status':status,'role':role,'bi':bi,'bn':bn,'nodes':sorted(nodes)})
    promoted=sum(1 for r in rows if r['status'].startswith('PROMOTE'))
    audit=len(rows)-promoted
    decision='BOOK30_CORE_CONTEXT_COMPONENT_PROMOTED' if promoted==len(GROUP) else 'BOOK30_CORE_CONTEXT_COMPONENT_PARTIAL_OR_AUDIT'
    cur=conn.execute('''INSERT INTO book30_core_context_component_v1_runs (created_at,decision,promoted_count,audit_count,min_internal_lcs,max_negative_lcs,payload_json) VALUES (?,?,?,?,?,?,?)''',(now(),decision,promoted,audit,min(r['bi'][0] for r in rows),max(r['bn'][0] for r in rows),json.dumps({'group':GROUP,'negative':NEGATIVE},sort_keys=True)))
    run_id=int(cur.lastrowid)
    for r in rows:
        conn.execute('''INSERT INTO book30_core_context_component_v1_items (run_id,bookid,status,proposed_role,best_internal_anchor,best_internal_lcs,best_negative_anchor,best_negative_lcs,evidence_json) VALUES (?,?,?,?,?,?,?,?,?)''',(run_id,r['bookid'],r['status'],r['role'],r['bi'][1],r['bi'][0],r['bn'][1],r['bn'][0],json.dumps({'nodes':r['nodes'],'internal_lcs':r['bi'][2],'negative_lcs':r['bn'][3]},sort_keys=True)))
    conn.commit()
    print(json.dumps({'run_id':run_id,'decision':decision,'promoted_count':promoted,'audit_count':audit,'min_internal_lcs':min(r['bi'][0] for r in rows),'max_negative_lcs':max(r['bn'][0] for r in rows),'items':[{'bookid':r['bookid'],'status':r['status'],'internal_anchor':r['bi'][1],'internal_lcs':r['bi'][0],'negative_anchor':r['bn'][1],'negative_lcs':r['bn'][0]} for r in rows]},ensure_ascii=False))


if __name__=='__main__':
    main()
