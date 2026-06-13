#!/usr/bin/env python3
"""Decide whether final display-only books can be closed as audit/control functional roles."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
TARGETS = ("6", "32", "36")


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.executescript("""
    create table if not exists final_display_control_closure_gate_v1_runs (
        run_id integer primary key autoincrement,
        created_at text not null,
        decision text not null,
        target_count integer not null,
        closed_as_control_count integer not null,
        promoted_semantic_count integer not null,
        accepted_prose_gloss_count integer not null,
        summary_json text not null
    );
    create table if not exists final_display_control_closure_gate_v1_items (
        run_id integer not null,
        bookid text not null,
        closure_status text not null,
        proposed_label text not null,
        close_as_functional_control integer not null,
        semantic_promotion_allowed integer not null,
        prose_gloss_allowed integer not null,
        reason text not null,
        evidence_json text not null,
        primary key (run_id, bookid)
    );
    """)
    items = []
    for bookid in TARGETS:
        display = conn.execute("select * from display_tail_masking_gate_v1_items where run_id=(select max(run_id) from display_tail_masking_gate_v1_items) and bookid=?", (bookid,)).fetchone()
        phase = conn.execute("select * from phase_boundary_control_gate_v1_items where run_id=(select max(run_id) from phase_boundary_control_gate_v1_items) and bookid=?", (bookid,)).fetchone()
        drift = conn.execute("select * from display_template_concordance_gate_v1_items where run_id=(select max(run_id) from display_template_concordance_gate_v1_items) and bookid=?", (bookid,)).fetchone()
        if bookid in ("32", "36") and display and display["gate_status"] == "HOLD_DISPLAY_TAIL_ONLY_NO_PAYLOAD":
            status = "CLOSE_AS_DISPLAY_CONTROL_NO_SEMANTIC_PAYLOAD"
            label = "DISPLAY_ONLY_CONTROL_NO_PAYLOAD"
            close = 1
            reason = "Display-tail masking proves no independent payload after shared display formula; close as functional control, not translation."
        elif bookid == "6" and phase and phase["gate_status"] == "HOLD_3478_DISPLAY_PHASE_CONTROL":
            status = "CLOSE_AS_DISPLAY_PHASE_CONTROL_NO_SEMANTIC_PAYLOAD"
            label = "DISPLAY_PHASE_CONTROL_NO_PAYLOAD"
            close = 1
            reason = "3478/phase evidence plus display-continuity risk makes this a boundary/display control; no semantic payload."
        else:
            status = "KEEP_OPEN_DISPLAY_CONTROL_NOT_PROVEN"
            label = "DISPLAY_CONTROL_UNRESOLVED"
            close = 0
            reason = "Display/control evidence is not strong enough to close even as audit control."
        evidence = {"display_tail": dict(display) if display else None, "phase_boundary": dict(phase) if phase else None, "display_concordance": dict(drift) if drift else None}
        items.append((bookid, status, label, close, 0, 0, reason, json.dumps(evidence, ensure_ascii=False, sort_keys=True)))
    closed = sum(i[3] for i in items)
    summary = {"closed_books": [i[0] for i in items if i[3]], "principle": "closing as functional control reduces unresolved gap but does not create semantic translation"}
    cur = conn.execute("insert into final_display_control_closure_gate_v1_runs values (null,?,?,?,?,?,?,?)", (utc_now(), "FINAL_DISPLAY_CONTROLS_CLOSED_NO_SEMANTIC_PAYLOAD", len(TARGETS), closed, 0, 0, json.dumps(summary, ensure_ascii=False, sort_keys=True)))
    run_id = cur.lastrowid
    for item in items:
        conn.execute("insert into final_display_control_closure_gate_v1_items values (?,?,?,?,?,?,?,?,?)", (run_id, *item))
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": "FINAL_DISPLAY_CONTROLS_CLOSED_NO_SEMANTIC_PAYLOAD", "closed_as_control_count": closed, "closed_books": [i[0] for i in items if i[3]], "accepted_prose_gloss_count": 0}, ensure_ascii=False))

if __name__ == "__main__":
    main()
