#!/usr/bin/env python3
"""Rank unresolved/quarantined-audit books using long literal substring evidence.

This complements the structural-prior frontier rank. It is designed to catch
cases like book32 where long formula overlap was stronger than generic edge prior.
"""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

from sqlite_operational_grammar_reconstruction_probe import DB, load_books


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def latest_run(conn: sqlite3.Connection, table: str) -> int:
    return int(conn.execute(f"SELECT max(run_id) FROM {table}").fetchone()[0])


def longest_common_substring(a: str, b: str) -> str:
    best = ""
    prev = [0] * (len(b) + 1)
    for i, ca in enumerate(a, start=1):
        cur = [0]
        for j, cb in enumerate(b, start=1):
            val = prev[j - 1] + 1 if ca == cb else 0
            cur.append(val)
            if val > len(best):
                best = a[i - val:i]
        prev = cur
    return best


def classify_recommendation(lcs_len: int, anchor_status: str, source_status: str) -> str:
    if lcs_len >= 36 and anchor_status == "FUNCTIONAL_CORE":
        return "HIGH_LITERAL_OVERLAP_CORE_CONTRAST_PROBE"
    if lcs_len >= 36:
        return "MEDIUM_LITERAL_OVERLAP_RELATED_CONTRAST_PROBE"
    if lcs_len >= 24 and source_status == "UNRESOLVED_FUNCTION":
        return "MEDIUM_LITERAL_OVERLAP_UNRESOLVED_PROBE"
    if lcs_len >= 18:
        return "LOW_LITERAL_OVERLAP_AUDIT"
    return "IGNORE_WEAK_LITERAL_OVERLAP"


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute('''CREATE TABLE IF NOT EXISTS literal_overlap_frontier_rank_v1_runs (run_id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL, decision TEXT NOT NULL, candidate_count INTEGER NOT NULL, actionable_count INTEGER NOT NULL, payload_json TEXT NOT NULL)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS literal_overlap_frontier_rank_v1_items (run_id INTEGER NOT NULL, rank INTEGER NOT NULL, bookid TEXT NOT NULL, book_status TEXT NOT NULL, anchor_bookid TEXT NOT NULL, anchor_status TEXT NOT NULL, anchor_reading TEXT NOT NULL, lcs_len INTEGER NOT NULL, lcs_text TEXT NOT NULL, recommendation TEXT NOT NULL, evidence_json TEXT NOT NULL, PRIMARY KEY(run_id, bookid, anchor_bookid))''')
    reading_run = latest_run(conn, "honest_full_functional_reading_v1_runs")
    books = load_books(conn)
    readings = {str(r['bookid']): r for r in conn.execute('SELECT * FROM honest_full_functional_reading_v1_books WHERE run_id=?', (reading_run,))}
    quarantine_run = conn.execute("SELECT max(run_id) FROM frontier_audit_quarantine_v1_runs").fetchone()[0] if conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='frontier_audit_quarantine_v1_runs'").fetchone() else None
    quarantined_frontier = set()
    if quarantine_run is not None:
        quarantined_frontier = {str(r['bookid']) for r in conn.execute("SELECT bookid FROM frontier_audit_quarantine_v1_items WHERE run_id=?", (quarantine_run,))}
    sources = [b for b, r in readings.items() if r['status'] in ('UNRESOLVED_FUNCTION','QUARANTINED_OR_AUDIT') and b not in quarantined_frontier]
    anchors = [b for b, r in readings.items() if r['status'] in ('FUNCTIONAL_CORE','FUNCTIONAL_RELATED')]
    candidates=[]
    for bookid in sources:
        for anchor in anchors:
            if bookid == anchor:
                continue
            lcs = longest_common_substring(books[bookid].literal, books[anchor].literal)
            rec = classify_recommendation(len(lcs), str(readings[anchor]['status']), str(readings[bookid]['status']))
            if rec == 'IGNORE_WEAK_LITERAL_OVERLAP':
                continue
            candidates.append({
                'bookid': bookid,
                'book_status': str(readings[bookid]['status']),
                'anchor': anchor,
                'anchor_status': str(readings[anchor]['status']),
                'anchor_reading': str(readings[anchor]['functional_reading']),
                'lcs_len': len(lcs),
                'lcs_text': lcs,
                'recommendation': rec,
            })
    candidates.sort(key=lambda r: (-r['lcs_len'], r['book_status'], int(r['bookid']), int(r['anchor'])))
    decision='LITERAL_OVERLAP_FRONTIER_RANKED'
    actionable=sum(1 for r in candidates if not r['recommendation'].startswith('LOW'))
    cur=conn.execute('''INSERT INTO literal_overlap_frontier_rank_v1_runs (created_at,decision,candidate_count,actionable_count,payload_json) VALUES (?,?,?,?,?)''',(now(),decision,len(candidates),actionable,json.dumps({'reading_run':reading_run,'min_lcs':18,'excluded_frontier_quarantine':sorted(quarantined_frontier, key=int)},sort_keys=True)))
    run_id=int(cur.lastrowid)
    for idx,r in enumerate(candidates, start=1):
        conn.execute('''INSERT INTO literal_overlap_frontier_rank_v1_items (run_id,rank,bookid,book_status,anchor_bookid,anchor_status,anchor_reading,lcs_len,lcs_text,recommendation,evidence_json) VALUES (?,?,?,?,?,?,?,?,?,?,?)''',(
            run_id,idx,r['bookid'],r['book_status'],r['anchor'],r['anchor_status'],r['anchor_reading'],r['lcs_len'],r['lcs_text'],r['recommendation'],json.dumps({'lcs_preview':r['lcs_text'][:80]},sort_keys=True)
        ))
    conn.commit()
    print(json.dumps({'run_id':run_id,'decision':decision,'candidate_count':len(candidates),'actionable_count':actionable,'top_candidates':[{'rank':i+1,'bookid':r['bookid'],'book_status':r['book_status'],'anchor':r['anchor'],'anchor_reading':r['anchor_reading'],'lcs_len':r['lcs_len'],'recommendation':r['recommendation'],'lcs_text':r['lcs_text'][:60]} for i,r in enumerate(candidates[:12])]},ensure_ascii=False))


if __name__=='__main__':
    main()
