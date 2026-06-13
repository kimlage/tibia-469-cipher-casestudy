#!/usr/bin/env python3
"""Decide whether book14 can be closed as a negative boundary-control, not a semantic role."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
TARGET = "14"


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.executescript("""
    create table if not exists book14_negative_boundary_control_gate_v1_runs (
        run_id integer primary key autoincrement,
        created_at text not null,
        decision text not null,
        closed_count integer not null,
        semantic_promotion_count integer not null,
        accepted_prose_gloss_count integer not null,
        summary_json text not null
    );
    create table if not exists book14_negative_boundary_control_gate_v1_items (
        run_id integer not null,
        bookid text not null,
        gate_status text not null,
        proposed_label text not null,
        close_as_functional_control integer not null,
        semantic_promotion_allowed integer not null,
        prose_gloss_allowed integer not null,
        reason text not null,
        evidence_json text not null,
        primary key (run_id, bookid)
    );
    """)
    r02 = conn.execute("select * from r02_ltast_boundary_gate_v1_items where run_id=(select max(run_id) from r02_ltast_boundary_gate_v1_items) and bookid=?", (TARGET,)).fetchone()
    zero = conn.execute("select * from zero_operator_typed_exit_gate_v1_book_decisions where run_id=(select max(run_id) from zero_operator_typed_exit_gate_v1_book_decisions) and bookid=?", (TARGET,)).fetchone()
    phase = conn.execute("select * from residual_row0_phase_risk_gate_v1_items where run_id=(select max(run_id) from residual_row0_phase_risk_gate_v1_items) and bookid=?", (TARGET,)).fetchone()
    alt = conn.execute("select * from alt_decode_null_control_v1_items where run_id=(select max(run_id) from alt_decode_null_control_v1_items) and bookid=? order by path_rank limit 1", (TARGET,)).fetchone()
    if r02 and r02["gate_status"] == "HOLD_R02_LTAST_BOUNDARY_WEAK" and phase and phase["risk_class"] == "MEDIUM_ROW0_PHASE_RISK" and alt and alt["null_status"] == "REJECT_NULL_NOT_DISTINCT_ENOUGH":
        status = "CLOSE_AS_NEGATIVE_R02_LTAST_BOUNDARY_CONTROL_NO_GLOSS"
        label = "NEGATIVE_R02_LTAST_BOUNDARY_CONTROL"
        close = 1
        reason = "Book14 repeatedly fails promotion gates but has stable evidence as a negative/control case for R02/LTAST boundary and phase ambiguity; close as control, not semantic function."
    else:
        status = "KEEP_OPEN_BOOK14_NOT_CONTROL_PROVEN"
        label = "BOOK14_UNRESOLVED"
        close = 0
        reason = "Evidence is insufficient even for negative-control closure."
    evidence = {"r02_ltast": dict(r02) if r02 else None, "zero_exit": dict(zero) if zero else None, "phase": dict(phase) if phase else None, "alt_decode_null": dict(alt) if alt else None}
    cur = conn.execute("insert into book14_negative_boundary_control_gate_v1_runs values (null,?,?,?,?,?,?)", (utc_now(), "BOOK14_NEGATIVE_BOUNDARY_CONTROL_GATE_NO_GLOSS", close, 0, 0, json.dumps({"bookid": TARGET, "closed": bool(close)}, ensure_ascii=False, sort_keys=True)))
    run_id = cur.lastrowid
    conn.execute("insert into book14_negative_boundary_control_gate_v1_items values (?,?,?,?,?,?,?,?,?)", (run_id, TARGET, status, label, close, 0, 0, reason, json.dumps(evidence, ensure_ascii=False, sort_keys=True)))
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": "BOOK14_NEGATIVE_BOUNDARY_CONTROL_GATE_NO_GLOSS", "closed_count": close, "status": status, "accepted_prose_gloss_count": 0}, ensure_ascii=False))

if __name__ == "__main__":
    main()
