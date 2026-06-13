#!/usr/bin/env python3
"""Contrast remaining variant families VFETTIIT/VTLRNEFIE and BTILBETA/FNAAST/R20."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3

from sqlite_operational_grammar_reconstruction_probe import DB, load_books
from sqlite_literal_overlap_frontier_rank_v1 import longest_common_substring

FAMILIES = {
    "VFETTIIT_VTLRNEFIE_VARIANT_COMPONENT": ["15", "16", "55"],
    "BTILBETA_FNAAST_R20_WEAK_COMPONENT": ["60", "64"],
}
NEGATIVE_ANCHORS = {"29": "R20_BRANCH_HEAD", "52": "C86_BRANCH", "62": "C86_BRANCH", "65": "R20_CONNECTOR_ENDPOINT", "58": "BENNA_DISPLAY"}


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def nodes_for(book):
    return set(book.accepted)|set(book.audit)|set(book.scoped)


def main() -> None:
    conn=sqlite3.connect(DB, timeout=30)
    conn.row_factory=sqlite3.Row
    conn.execute('PRAGMA busy_timeout=30000')
    conn.execute('''CREATE TABLE IF NOT EXISTS variant_family_contrast_v1_runs (run_id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL, decision TEXT NOT NULL, promoted_count INTEGER NOT NULL, audit_count INTEGER NOT NULL, payload_json TEXT NOT NULL)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS variant_family_contrast_v1_items (run_id INTEGER NOT NULL, bookid TEXT NOT NULL, family_id TEXT NOT NULL, status TEXT NOT NULL, proposed_role TEXT NOT NULL, best_internal_anchor TEXT NOT NULL, best_internal_lcs INTEGER NOT NULL, best_negative_anchor TEXT NOT NULL, best_negative_lcs INTEGER NOT NULL, evidence_json TEXT NOT NULL, PRIMARY KEY(run_id, bookid))''')
    books=load_books(conn)
    rows=[]
    for family, ids in FAMILIES.items():
        for bookid in ids:
            internals=[]
            for other in ids:
                if other==bookid: continue
                l=longest_common_substring(books[bookid].literal, books[other].literal)
                internals.append((len(l),other,l))
            negatives=[]
            for a,r in NEGATIVE_ANCHORS.items():
                l=longest_common_substring(books[bookid].literal, books[a].literal)
                negatives.append((len(l),a,r,l))
            bi=max(internals) if internals else (0,'NONE','')
            bn=max(negatives)
            nodes=nodes_for(books[bookid])
            if family == 'VFETTIIT_VTLRNEFIE_VARIANT_COMPONENT':
                has_node='VFETTIIT_UNIQUE_VARIANT_FAMILY' in nodes
                min_lcs=35
            else:
                has_node='BTILBETA_FNAAST_UNIQUE_PAIR' in nodes
                min_lcs=35
            if has_node and bi[0] >= min_lcs and (bi[0]-bn[0]) >= 10:
                status='PROMOTE_VARIANT_FAMILY_COMPONENT_NO_GLOSS'; role=family
            elif has_node and bi[0] >= 20:
                status='AUDIT_VARIANT_FAMILY_LOW_MARGIN'; role=family + '_AUDIT'
            else:
                status='KEEP_QUARANTINED'; role='VARIANT_FAMILY_UNPROVEN'
            rows.append({'bookid':bookid,'family':family,'status':status,'role':role,'bi':bi,'bn':bn,'nodes':sorted(nodes)})
    promoted=sum(1 for r in rows if r['status'].startswith('PROMOTE'))
    audit=len(rows)-promoted
    decision='VARIANT_FAMILY_CONTRAST_PARTIAL_PROMOTION' if promoted else 'VARIANT_FAMILY_CONTRAST_AUDIT_ONLY'
    cur=conn.execute('''INSERT INTO variant_family_contrast_v1_runs (created_at,decision,promoted_count,audit_count,payload_json) VALUES (?,?,?,?,?)''',(now(),decision,promoted,audit,json.dumps({'families':FAMILIES,'negative_anchors':NEGATIVE_ANCHORS},sort_keys=True)))
    run_id=int(cur.lastrowid)
    for r in rows:
        conn.execute('''INSERT INTO variant_family_contrast_v1_items (run_id,bookid,family_id,status,proposed_role,best_internal_anchor,best_internal_lcs,best_negative_anchor,best_negative_lcs,evidence_json) VALUES (?,?,?,?,?,?,?,?,?,?)''',(run_id,r['bookid'],r['family'],r['status'],r['role'],r['bi'][1],r['bi'][0],r['bn'][1],r['bn'][0],json.dumps({'nodes':r['nodes'],'internal_lcs':r['bi'][2],'negative_lcs':r['bn'][3]},sort_keys=True)))
    conn.commit()
    print(json.dumps({'run_id':run_id,'decision':decision,'promoted_count':promoted,'audit_count':audit,'items':[{'bookid':r['bookid'],'family':r['family'],'status':r['status'],'role':r['role'],'internal_anchor':r['bi'][1],'internal_lcs':r['bi'][0],'negative_anchor':r['bn'][1],'negative_lcs':r['bn'][0]} for r in rows]},ensure_ascii=False))


if __name__=='__main__':
    main()
