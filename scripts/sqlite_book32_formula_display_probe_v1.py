#!/usr/bin/env python3
"""Probe book32 as FNAAST/NSBVN formula-display, not VNCTIIN payload."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3

from sqlite_operational_grammar_reconstruction_probe import DB, classify_states, edge_score, load_books

FORMULA_POSITIVES = {"58": "DISPLAY_FORMULA_HEAD", "59": "DISPLAY_PARALLEL", "40": "FORMULA_BODY"}
PAYLOAD_NEGATIVES = {"67": "C86_VNCTIIN_CONTEXT_PAYLOAD", "27": "C86_VNCTIIN_CONTEXT_PAYLOAD", "35": "HANDOFF_CONTEXT", "2": "NAESE_SLOT", "62": "C86_VINVIN_PAYLOAD"}


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def common_substrings(a: str, b: str, min_len: int = 8) -> list[str]:
    out = set()
    for i in range(len(a)):
        for j in range(i + min_len, min(len(a), i + 40) + 1):
            s = a[i:j]
            if s in b:
                out.add(s)
    return sorted(out, key=lambda x: (-len(x), x))[:5]


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute('''CREATE TABLE IF NOT EXISTS book32_formula_display_probe_v1_runs (run_id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL, decision TEXT NOT NULL, formula_margin REAL NOT NULL, payload_margin REAL NOT NULL, payload_rejected INTEGER NOT NULL, payload_json TEXT NOT NULL)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS book32_formula_display_probe_v1_items (run_id INTEGER NOT NULL, edge TEXT NOT NULL, role TEXT NOT NULL, anchor_role TEXT NOT NULL, score REAL NOT NULL, overlap INTEGER NOT NULL, prior REAL NOT NULL, transition_json TEXT NOT NULL, evidence_json TEXT NOT NULL, PRIMARY KEY(run_id, edge))''')
    books = load_books(conn)
    states = {bookid: classify_states(book) for bookid, book in books.items()}
    rows=[]
    for anchor, role in FORMULA_POSITIVES.items():
        for edge in [(anchor,"32"),("32",anchor)]:
            p=edge_score(books[edge[0]],books[edge[1]],states)
            rows.append({"edge":edge,"role":"formula_positive","anchor_role":role,"payload":p,"common":common_substrings(books[edge[0]].literal,books[edge[1]].literal)})
    for anchor, role in PAYLOAD_NEGATIVES.items():
        for edge in [(anchor,"32"),("32",anchor)]:
            p=edge_score(books[edge[0]],books[edge[1]],states)
            rows.append({"edge":edge,"role":"payload_negative","anchor_role":role,"payload":p,"common":common_substrings(books[edge[0]].literal,books[edge[1]].literal)})
    best_formula=max((r for r in rows if r['role']=='formula_positive'), key=lambda r:(r['payload']['score'], r['payload']['overlap'], len(r['common'][0]) if r['common'] else 0))
    best_payload=max((r for r in rows if r['role']=='payload_negative'), key=lambda r:(r['payload']['score'], r['payload']['overlap']))
    formula_margin=float(best_formula['payload']['score'])-float(best_payload['payload']['score'])
    # Payload is rejected if its best evidence is only generic prior/near-zero overlap while formula has literal common substrings.
    payload_rejected=int(best_payload['payload']['overlap'] <= 1 and bool(best_formula['common']))
    if best_formula['payload']['score'] >= 100 and payload_rejected:
        decision='BOOK32_PROMOTE_FNAAST_FORMULA_DISPLAY_AUDIT_NO_GLOSS'
    elif payload_rejected:
        decision='BOOK32_AUDIT_FNAAST_FORMULA_DISPLAY_WEAK'
    else:
        decision='BOOK32_KEEP_UNRESOLVED_PAYLOAD_AMBIGUOUS'
    cur=conn.execute('''INSERT INTO book32_formula_display_probe_v1_runs (created_at,decision,formula_margin,payload_margin,payload_rejected,payload_json) VALUES (?,?,?,?,?,?)''',(
        now(),decision,round(formula_margin,4),round(float(best_payload['payload']['score']),4),payload_rejected,json.dumps({'best_formula':f"{best_formula['edge'][0]}->{best_formula['edge'][1]}",'best_payload':f"{best_payload['edge'][0]}->{best_payload['edge'][1]}",'common_formula':best_formula['common']},sort_keys=True)
    ))
    run_id=int(cur.lastrowid)
    for r in rows:
        p=r['payload']
        conn.execute('''INSERT INTO book32_formula_display_probe_v1_items (run_id,edge,role,anchor_role,score,overlap,prior,transition_json,evidence_json) VALUES (?,?,?,?,?,?,?,?,?)''',(
            run_id,f"{r['edge'][0]}->{r['edge'][1]}",r['role'],r['anchor_role'],p['score'],p['overlap'],p['prior'],json.dumps(p['transition'],sort_keys=True),json.dumps({'shared_nodes':p['shared_nodes'],'common_substrings':r['common']},sort_keys=True)
        ))
    conn.commit()
    print(json.dumps({'run_id':run_id,'decision':decision,'best_formula':f"{best_formula['edge'][0]}->{best_formula['edge'][1]}",'best_formula_score':best_formula['payload']['score'],'best_formula_common':best_formula['common'][:2],'best_payload':f"{best_payload['edge'][0]}->{best_payload['edge'][1]}",'best_payload_score':best_payload['payload']['score'],'best_payload_overlap':best_payload['payload']['overlap'],'payload_rejected':bool(payload_rejected)},ensure_ascii=False))


if __name__=='__main__':
    main()
