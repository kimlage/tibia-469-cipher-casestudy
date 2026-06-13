#!/usr/bin/env python3
"""Probe BENNA/LTAST boundary books 0/33/66 as handoff-window fragments."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3

from sqlite_operational_grammar_reconstruction_probe import DB, load_books
from sqlite_literal_overlap_frontier_rank_v1 import longest_common_substring

GROUP = ["0", "33", "66"]
HANDOFF = {"10": "HANDOFF_CONTEXT", "35": "HANDOFF_CONTEXT"}
FORMULA = {"58": "DISPLAY_FORMULA_HEAD", "40": "FORMULA_BODY", "69": "MIXED_TEMPLATE_FORMULA_HEAD"}
NEGATIVE = {"2": "NAESE_SLOT", "62": "C86_VINVIN_BRANCH"}


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def nodes_for(book) -> set[str]:
    return set(book.accepted) | set(book.audit) | set(book.scoped)


def main() -> None:
    conn=sqlite3.connect(DB, timeout=30)
    conn.row_factory=sqlite3.Row
    conn.execute('PRAGMA busy_timeout=30000')
    conn.execute('''CREATE TABLE IF NOT EXISTS benna_ltast_handoff_fragment_probe_v1_runs (run_id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL, decision TEXT NOT NULL, promoted_count INTEGER NOT NULL, audit_count INTEGER NOT NULL, payload_json TEXT NOT NULL)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS benna_ltast_handoff_fragment_probe_v1_items (run_id INTEGER NOT NULL, bookid TEXT NOT NULL, status TEXT NOT NULL, proposed_role TEXT NOT NULL, best_handoff_anchor TEXT NOT NULL, best_handoff_lcs INTEGER NOT NULL, best_formula_anchor TEXT NOT NULL, best_formula_lcs INTEGER NOT NULL, best_negative_anchor TEXT NOT NULL, best_negative_lcs INTEGER NOT NULL, evidence_json TEXT NOT NULL, PRIMARY KEY(run_id, bookid))''')
    books=load_books(conn)
    rows=[]
    for bookid in GROUP:
        hand=[]; form=[]; neg=[]
        for a,r in HANDOFF.items():
            l=longest_common_substring(books[bookid].literal,books[a].literal); hand.append((len(l),a,r,l))
        for a,r in FORMULA.items():
            l=longest_common_substring(books[bookid].literal,books[a].literal); form.append((len(l),a,r,l))
        for a,r in NEGATIVE.items():
            l=longest_common_substring(books[bookid].literal,books[a].literal); neg.append((len(l),a,r,l))
        bh=max(hand); bf=max(form); bn=max(neg)
        nodes=nodes_for(books[bookid])
        has_ltast='BENNA_LTAST_BOUNDARY_WINDOW' in nodes
        has_formula='BENNA_FORMULA_BRIDGE' in nodes
        # Promote as related only when handoff overlap is strong and substantially above negatives.
        if has_ltast and bh[0] >= 55 and (bh[0]-bn[0]) >= 35:
            status='PROMOTE_BENNA_LTAST_HANDOFF_WINDOW_FRAGMENT_NO_GLOSS'
            role='BENNA_LTAST_HANDOFF_WINDOW_FRAGMENT'
        elif has_ltast and bh[0] >= 45:
            status='AUDIT_BENNA_LTAST_HANDOFF_WINDOW_FRAGMENT'
            role='BENNA_LTAST_HANDOFF_AUDIT'
        else:
            status='KEEP_QUARANTINED'
            role='BENNA_LTAST_BOUNDARY_QUARANTINE'
        rows.append({'bookid':bookid,'status':status,'role':role,'bh':bh,'bf':bf,'bn':bn,'nodes':sorted(nodes),'has_formula':has_formula})
    promoted=sum(1 for r in rows if r['status'].startswith('PROMOTE'))
    audit=len(rows)-promoted
    decision='BENNA_LTAST_HANDOFF_FRAGMENT_PARTIAL_PROMOTION' if promoted else 'BENNA_LTAST_HANDOFF_FRAGMENT_AUDIT_ONLY'
    cur=conn.execute('''INSERT INTO benna_ltast_handoff_fragment_probe_v1_runs (created_at,decision,promoted_count,audit_count,payload_json) VALUES (?,?,?,?,?)''',(now(),decision,promoted,audit,json.dumps({'group':GROUP,'handoff_anchors':HANDOFF,'formula_anchors':FORMULA,'negative_anchors':NEGATIVE},sort_keys=True)))
    run_id=int(cur.lastrowid)
    for r in rows:
        conn.execute('''INSERT INTO benna_ltast_handoff_fragment_probe_v1_items (run_id,bookid,status,proposed_role,best_handoff_anchor,best_handoff_lcs,best_formula_anchor,best_formula_lcs,best_negative_anchor,best_negative_lcs,evidence_json) VALUES (?,?,?,?,?,?,?,?,?,?,?)''',(run_id,r['bookid'],r['status'],r['role'],r['bh'][1],r['bh'][0],r['bf'][1],r['bf'][0],r['bn'][1],r['bn'][0],json.dumps({'nodes':r['nodes'],'handoff_lcs':r['bh'][3],'formula_lcs':r['bf'][3],'negative_lcs':r['bn'][3],'has_formula_bridge':r['has_formula']},sort_keys=True)))
    conn.commit()
    print(json.dumps({'run_id':run_id,'decision':decision,'promoted_count':promoted,'audit_count':audit,'items':[{'bookid':r['bookid'],'status':r['status'],'role':r['role'],'handoff_anchor':r['bh'][1],'handoff_lcs':r['bh'][0],'formula_anchor':r['bf'][1],'formula_lcs':r['bf'][0],'negative_anchor':r['bn'][1],'negative_lcs':r['bn'][0]} for r in rows]},ensure_ascii=False))


if __name__=='__main__':
    main()
