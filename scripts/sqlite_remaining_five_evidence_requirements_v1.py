#!/usr/bin/env python3
"""Persist exact evidence requirements for the five active non-translated residual books."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
REQ = {
    "6": ("DISPLAY_CONTINUITY_PHASE", "Need row0 phase/path resolution plus a non-display payload boundary; current BENNA/display surface is not enough."),
    "7": ("RARE_PHASE_CONTINUITY", "Need a clean pair/family contrast or phase-resolved operator boundary; current rare motifs are surface-continuity only."),
    "14": ("R02_LTAST_WEAK_BOUNDARY", "Need R02/LTAST boundary test that beats phase ambiguity and negative controls; latest gate failed."),
    "32": ("FNAAST_DISPLAY_LOW_SIGNAL", "Need payload behavior independent of FNAAST/TNBEE display window; current formula/display evidence is held."),
    "36": ("DISPLAY_DRIFT_CONTROL", "Need proof that BENNA/NSBVN display drift carries structural payload; current evidence is display-control only."),
}


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.executescript("""
    create table if not exists remaining_five_evidence_requirements_v1_runs (
        run_id integer primary key autoincrement,
        created_at text not null,
        decision text not null,
        item_count integer not null,
        immediately_actionable_count integer not null,
        accepted_prose_gloss_count integer not null,
        summary_json text not null
    );
    create table if not exists remaining_five_evidence_requirements_v1_items (
        run_id integer not null,
        bookid text not null,
        blocker_class text not null,
        required_evidence text not null,
        immediately_actionable integer not null,
        safest_next_probe text not null,
        evidence_json text not null,
        primary key (run_id, bookid)
    );
    """)
    latest_status = conn.execute("select max(run_id) as run_id from honest_translation_status_export_v1_books").fetchone()["run_id"]
    items = []
    for bookid, (klass, req) in REQ.items():
        status = conn.execute("select * from honest_translation_status_export_v1_books where run_id=? and bookid=?", (latest_status, bookid)).fetchone()
        if bookid in ("6", "7"):
            next_probe = "row0 phase/path disambiguation using operator selectors and 3478 boundary controls"
            actionable = 1
        elif bookid in ("32", "36"):
            next_probe = "display-tail masking with held-out payload prediction; promote only if independent payload emerges"
            actionable = 1
        elif bookid == "14":
            next_probe = "no immediate rerun; R02/LTAST gate already failed unless new phase evidence appears"
            actionable = 0
        else:
            next_probe = "hold"
            actionable = 0
        evidence = {"current_status": dict(status) if status else None}
        items.append((bookid, klass, req, actionable, next_probe, json.dumps(evidence, ensure_ascii=False, sort_keys=True)))
    actionable_count = sum(i[3] for i in items)
    summary = {"remaining_books": sorted(REQ, key=int), "actionable_books": [i[0] for i in items if i[3]], "principle": "each remaining book requires evidence stronger than surface similarity"}
    cur = conn.execute("insert into remaining_five_evidence_requirements_v1_runs values (null,?,?,?,?,?,?)", (utc_now(), "REMAINING_FIVE_REQUIRE_NEW_EVIDENCE", len(items), actionable_count, 0, json.dumps(summary, ensure_ascii=False, sort_keys=True)))
    run_id = cur.lastrowid
    for item in items:
        conn.execute("insert into remaining_five_evidence_requirements_v1_items values (?,?,?,?,?,?,?)", (run_id, *item))
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": "REMAINING_FIVE_REQUIRE_NEW_EVIDENCE", "item_count": len(items), "immediately_actionable_count": actionable_count, "accepted_prose_gloss_count": 0, "actionable_books": [i[0] for i in items if i[3]]}, ensure_ascii=False))

if __name__ == "__main__":
    main()
