#!/usr/bin/env python3
"""Checkpoint remaining unresolved/audit books after overlap frontier exhaustion."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def latest_run(conn: sqlite3.Connection, table: str) -> int:
    return int(conn.execute(f"SELECT max(run_id) FROM {table}").fetchone()[0])


def classify_next(bookid: str, status: str, reading: str) -> tuple[str, str]:
    if bookid in {"7", "20", "25", "39", "49", "54"}:
        return "RARE_OR_SINGLETON_MOTIF_SEARCH", "low-overlap unresolved; use motif/BPE/rare-symbol context, not family overlap"
    if bookid in {"14", "18", "30", "34"}:
        return "LOW_OVERLAP_FRAGMENT_AUDIT", "some weak literal overlap exists but below promotion gate"
    if bookid in {"8", "23", "24", "31", "37", "41", "57"}:
        return "FRONTIER_QUARANTINED_NEEDS_NEW_EVIDENCE", "already tested or ambiguous; reopen only with new mechanical evidence"
    if bookid in {"4", "15", "16", "55", "60", "64"}:
        return "VARIANT_FAMILY_CONTRAST_REQUIRED", "audit/variant family needs contrastive variant model rather than overlap promotion"
    if bookid in {"6", "19", "36"}:
        return "DISPLAY_OR_CONTINUITY_AUDIT_REQUIRED", "surface/display or continuity audit remains below related-function gate"
    return "MANUAL_REVIEW_LOW_SIGNAL", "no current actionable evidence"


def main() -> None:
    conn=sqlite3.connect(DB, timeout=30)
    conn.row_factory=sqlite3.Row
    conn.execute('PRAGMA busy_timeout=30000')
    conn.execute('''CREATE TABLE IF NOT EXISTS remaining_gap_checkpoint_v1_runs (run_id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL, decision TEXT NOT NULL, total_gap_count INTEGER NOT NULL, unresolved_count INTEGER NOT NULL, audit_count INTEGER NOT NULL, actionable_overlap_count INTEGER NOT NULL, accepted_prose_gloss_count INTEGER NOT NULL, payload_json TEXT NOT NULL)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS remaining_gap_checkpoint_v1_items (run_id INTEGER NOT NULL, bookid TEXT NOT NULL, current_status TEXT NOT NULL, current_reading TEXT NOT NULL, next_method TEXT NOT NULL, reason TEXT NOT NULL, best_overlap_anchor TEXT NOT NULL, best_overlap_len INTEGER NOT NULL, evidence_json TEXT NOT NULL, PRIMARY KEY(run_id, bookid))''')
    reading_run=latest_run(conn,'honest_full_functional_reading_v1_runs')
    overlap_run=latest_run(conn,'literal_overlap_frontier_rank_v1_runs')
    rows=list(conn.execute("SELECT bookid,status,functional_reading,evidence_json FROM honest_full_functional_reading_v1_books WHERE run_id=? AND status IN ('UNRESOLVED_FUNCTION','QUARANTINED_OR_AUDIT') ORDER BY status, CAST(bookid AS INT)",(reading_run,)))
    best_overlap={}
    for r in conn.execute('SELECT bookid, anchor_bookid, anchor_reading, lcs_len, lcs_text FROM literal_overlap_frontier_rank_v1_items WHERE run_id=? ORDER BY rank',(overlap_run,)):
        best_overlap.setdefault(str(r['bookid']), r)
    actionable=sum(1 for r in best_overlap.values() if int(r['lcs_len']) >= 30)
    decision='REMAINING_GAPS_CHECKPOINTED_OVERLAP_EXHAUSTED'
    cur=conn.execute('''INSERT INTO remaining_gap_checkpoint_v1_runs (created_at,decision,total_gap_count,unresolved_count,audit_count,actionable_overlap_count,accepted_prose_gloss_count,payload_json) VALUES (?,?,?,?,?,?,?,?)''',(now(),decision,len(rows),sum(1 for r in rows if r['status']=='UNRESOLVED_FUNCTION'),sum(1 for r in rows if r['status']=='QUARANTINED_OR_AUDIT'),actionable,0,json.dumps({'reading_run':reading_run,'overlap_run':overlap_run},sort_keys=True)))
    run_id=int(cur.lastrowid)
    method_counts={}
    for r in rows:
        bookid=str(r['bookid']); method, reason=classify_next(bookid,str(r['status']),str(r['functional_reading']))
        method_counts[method]=method_counts.get(method,0)+1
        ov=best_overlap.get(bookid)
        anchor='NONE'; olen=0; ev={'current_evidence':r['evidence_json']}
        if ov:
            anchor=f"{ov['anchor_bookid']}:{ov['anchor_reading']}"; olen=int(ov['lcs_len']); ev['best_overlap']={'anchor_bookid':ov['anchor_bookid'],'anchor_reading':ov['anchor_reading'],'lcs_len':olen,'lcs_text':ov['lcs_text']}
        conn.execute('''INSERT INTO remaining_gap_checkpoint_v1_items (run_id,bookid,current_status,current_reading,next_method,reason,best_overlap_anchor,best_overlap_len,evidence_json) VALUES (?,?,?,?,?,?,?,?,?)''',(run_id,bookid,str(r['status']),str(r['functional_reading']),method,reason,anchor,olen,json.dumps(ev,sort_keys=True)))
    conn.execute('UPDATE remaining_gap_checkpoint_v1_runs SET payload_json=? WHERE run_id=?',(json.dumps({'reading_run':reading_run,'overlap_run':overlap_run,'method_counts':method_counts},sort_keys=True),run_id))
    conn.commit()
    print(json.dumps({'run_id':run_id,'decision':decision,'total_gap_count':len(rows),'unresolved_count':sum(1 for r in rows if r['status']=='UNRESOLVED_FUNCTION'),'audit_count':sum(1 for r in rows if r['status']=='QUARANTINED_OR_AUDIT'),'method_counts':method_counts,'accepted_prose_gloss_count':0},ensure_ascii=False))


if __name__=='__main__':
    main()
