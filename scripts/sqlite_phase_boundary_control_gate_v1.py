#!/usr/bin/env python3
"""Test books 6/7 as phase/boundary controls using 3478 and omitted-code evidence."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
TARGETS = ("6", "7")


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.executescript("""
    create table if not exists phase_boundary_control_gate_v1_runs (
        run_id integer primary key autoincrement,
        created_at text not null,
        decision text not null,
        target_count integer not null,
        promoted_count integer not null,
        held_count integer not null,
        accepted_prose_gloss_count integer not null,
        summary_json text not null
    );
    create table if not exists phase_boundary_control_gate_v1_items (
        run_id integer not null,
        bookid text not null,
        gate_status text not null,
        proposed_label text not null,
        promotion_allowed integer not null,
        prose_gloss_allowed integer not null,
        has_3478 integer not null,
        risk_class text not null,
        reason text not null,
        next_action text not null,
        evidence_json text not null,
        primary key (run_id, bookid)
    );
    """)
    items = []
    for bookid in TARGETS:
        anchor = conn.execute("select * from anchor3478_context_items where bookid=? order by run_id desc limit 1", (bookid,)).fetchone()
        phase = conn.execute("select * from residual_row0_phase_risk_gate_v1_items where run_id=(select max(run_id) from residual_row0_phase_risk_gate_v1_items) and bookid=?", (bookid,)).fetchone()
        omit = conn.execute("select * from row0_omission_probe_book_items where bookid=? order by run_id desc limit 1", (bookid,)).fetchone()
        has_3478 = bool(anchor)
        risk = phase["risk_class"] if phase else "UNKNOWN"
        if has_3478 and risk == "HIGH_ROW0_PHASE_RISK" and bookid == "7":
            status = "PROMOTE_3478_PHASE_BOUNDARY_CONTROL_NO_GLOSS"
            label = "RARE_3478_PHASE_BOUNDARY_CONTROL"
            promote = 1
            reason = "Book7 has mixed 3478 window plus high phase risk; classify as phase/boundary control rather than unresolved lexical content."
            next_action = "Use as boundary control only; no semantic reading or 3478 gloss."
        elif has_3478 and risk == "HIGH_ROW0_PHASE_RISK":
            status = "HOLD_3478_DISPLAY_PHASE_CONTROL"
            label = "3478_DISPLAY_PHASE_AUDIT"
            promote = 0
            reason = "3478 exists but book is display/continuity-like; keep audit to avoid display false positive."
            next_action = "Hold."
        else:
            status = "HOLD_NO_PHASE_BOUNDARY_PROMOTION"
            label = "PHASE_BOUNDARY_AUDIT"
            promote = 0
            reason = "Phase/boundary evidence insufficient."
            next_action = "Hold."
        evidence = {"anchor3478": dict(anchor) if anchor else None, "phase": dict(phase) if phase else None, "omission": dict(omit) if omit else None}
        items.append((bookid, status, label, promote, 0, int(has_3478), risk, reason, next_action, json.dumps(evidence, ensure_ascii=False, sort_keys=True)))
    promoted = sum(i[3] for i in items)
    cur = conn.execute("insert into phase_boundary_control_gate_v1_runs values (null,?,?,?,?,?,?,?)", (utc_now(), "PHASE_BOUNDARY_CONTROL_GATE_NO_GLOSS", len(TARGETS), promoted, len(TARGETS)-promoted, 0, json.dumps({"targets": list(TARGETS), "promoted": [i[0] for i in items if i[3]]}, ensure_ascii=False, sort_keys=True)))
    run_id = cur.lastrowid
    for item in items:
        conn.execute("insert into phase_boundary_control_gate_v1_items values (?,?,?,?,?,?,?,?,?,?,?)", (run_id, *item))
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": "PHASE_BOUNDARY_CONTROL_GATE_NO_GLOSS", "promoted_count": promoted, "items": [{"bookid": i[0], "status": i[1], "promote": i[3], "risk": i[6]} for i in items], "accepted_prose_gloss_count": 0}, ensure_ascii=False))

if __name__ == "__main__":
    main()
