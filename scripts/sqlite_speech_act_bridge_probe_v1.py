#!/usr/bin/env python3
"""Probe whether abstract functions can map to speech-act labels that predict external phrases."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
CANDIDATES = [
    ("SA_HANDOFF_CONTINUATION", "handoff/continuation", ["BENNA_LTAST_HANDOFF", "C68_CONTEXT_HANDOFF"]),
    ("SA_DISPLAY_FORMULA", "display/formula marker", ["DISPLAY_ONLY_CONTROL", "FNAAST_DISPLAY"]),
    ("SA_BOUNDARY_CONTROL", "boundary/control marker", ["3478_PHASE_BOUNDARY", "O32_SELECTOR_CONTROL"]),
    ("SA_CONTEXT_FRAME", "context frame", ["C68_VN_TIIN_CONTEXT", "VNCTIIN_CONTEXT"]),
]


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.executescript("""
    create table if not exists speech_act_bridge_probe_v1_runs (
        run_id integer primary key autoincrement,
        created_at text not null,
        decision text not null,
        candidate_count integer not null,
        accepted_bridge_count integer not null,
        accepted_prose_gloss_count integer not null,
        summary_json text not null
    );
    create table if not exists speech_act_bridge_probe_v1_items (
        run_id integer not null,
        speech_act_id text not null,
        speech_act_label text not null,
        status text not null,
        external_prediction_supported integer not null,
        prose_gloss_allowed integer not null,
        reason text not null,
        evidence_json text not null,
        primary key (run_id, speech_act_id)
    );
    """)
    # Current external benchmark has no decoder passing; therefore no speech act can be accepted as plaintext bridge yet.
    latest_eval = conn.execute("select max(run_id) as run_id from plaintext_candidate_eval_v1_runs").fetchone()["run_id"]
    eval_run = conn.execute("select * from plaintext_candidate_eval_v1_runs where run_id=?", (latest_eval,)).fetchone()
    items = []
    for sid, label, funcs in CANDIDATES:
        if int(eval_run["passed_count"]) >= 5:
            status = "ACCEPT_SPEECH_ACT_BRIDGE_NO_PROSE"
            supported = 1
            reason = "External benchmarks support enough predictions for abstract speech act bridge."
        else:
            status = "HOLD_NO_EXTERNAL_PREDICTION"
            supported = 0
            reason = "Abstract function does not yet predict external phrases; cannot become speech-act/plaintext bridge."
        items.append((sid, label, status, supported, 0, reason, json.dumps({"functions": funcs, "latest_candidate_eval": dict(eval_run)}, ensure_ascii=False, sort_keys=True)))
    accepted = sum(i[3] for i in items)
    summary = {"candidate_eval_run": latest_eval, "principle": "speech-act labels require external prediction support"}
    cur = conn.execute("insert into speech_act_bridge_probe_v1_runs values (null,?,?,?,?,?,?)", (utc_now(), "SPEECH_ACT_BRIDGE_HELD_NO_EXTERNAL_PREDICTION", len(items), accepted, 0, json.dumps(summary, ensure_ascii=False, sort_keys=True)))
    run_id = cur.lastrowid
    for item in items:
        conn.execute("insert into speech_act_bridge_probe_v1_items values (?,?,?,?,?,?,?,?)", (run_id, *item))
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": "SPEECH_ACT_BRIDGE_HELD_NO_EXTERNAL_PREDICTION", "accepted_bridge_count": accepted, "accepted_prose_gloss_count": 0}, ensure_ascii=False))

if __name__ == "__main__":
    main()
