#!/usr/bin/env python3
"""Consolidate parse-competition decisions with C68 gate conflicts resolved conservatively."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

PROMOTE = [
    ("18", "RESIDUAL_STRONG_10_35_STRUCTURAL_WINDOW", "Strong 10/35 residual window via LIBEITEITAILBETFTE*IC86; structural only."),
    ("19", "C68_VN_TIIN_CONTEXT_FRAME_GUARDED", "C68/VNCTIIN context frame; BENNA-looking tail is surface/context; no 19->2 edge promotion."),
    ("23", "C68_VN_TIIN_CONTEXT_FRAME_GUARDED", "C68/VNCTIIN context frame; negative NAESE support insufficient; no ordered contig promotion."),
    ("8", "C68_VN_TIIN_CONTEXT_SUBFRAME", "C68 gate classifies single VN/TIIN context subframe; structural only."),
]
HOLD = [
    ("24", "C68_O23_COMPOSITE_BOUNDARY_HELD", "C68 frame exists but O23/scoped-control contamination remains unresolved."),
    ("4", "MIXED_C86_O23_R20_HELD", "Composite C86/O23/R20 control; not clean enough."),
    ("6", "BENNA_SURFACE_DEAD_THIS_LANE", "BENNA-like surface ties broad negative control."),
    ("14", "LTAST_SLOT_AUDIT_HELD", "LTAST/context window only; promotion disallowed."),
    ("34", "PLAIN_INTERNAL_RESIDUAL_HELD", "Branch-tail overlap lacks operator promotion carrier."),
    ("36", "DISPLAY_ONLY_HELD", "Display-window evidence only; no structural promotion."),
]


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.executescript("""
    create table if not exists parse_competition_consolidation_v1_runs (
        run_id integer primary key autoincrement,
        created_at text not null,
        decision text not null,
        promoted_count integer not null,
        held_count integer not null,
        accepted_prose_gloss_count integer not null,
        summary_json text not null
    );
    create table if not exists parse_competition_consolidation_v1_items (
        run_id integer not null,
        bookid text not null,
        label text not null,
        decision_status text not null,
        promotion_allowed integer not null,
        prose_gloss_allowed integer not null,
        reason text not null,
        evidence_json text not null,
        primary key (run_id, bookid)
    );
    """)
    latest_gap = conn.execute("select max(run_id) as run_id from remaining_gap_checkpoint_v1_items").fetchone()["run_id"]
    summary = {"promoted_books": [x[0] for x in PROMOTE], "held_books": [x[0] for x in HOLD], "conflict_resolution": "book24 held despite C68 gate because parse competition shows O23 contamination", "principle": "structural frame only; no plaintext"}
    cur = conn.execute("insert into parse_competition_consolidation_v1_runs (created_at,decision,promoted_count,held_count,accepted_prose_gloss_count,summary_json) values (?,?,?,?,?,?)", (utc_now(), "PARSE_COMPETITION_STRUCTURAL_PROMOTION_NO_GLOSS", len(PROMOTE), len(HOLD), 0, json.dumps(summary, ensure_ascii=False, sort_keys=True)))
    run_id = cur.lastrowid
    for bookid, label, reason in PROMOTE:
        gap = conn.execute("select * from remaining_gap_checkpoint_v1_items where run_id=? and bookid=?", (latest_gap, bookid)).fetchone()
        conn.execute("insert into parse_competition_consolidation_v1_items values (?,?,?,?,?,?,?,?)", (run_id, bookid, label, "PROMOTE_RELATED_STRUCTURAL", 1, 0, reason, json.dumps({"gap": dict(gap) if gap else None}, ensure_ascii=False, sort_keys=True)))
    for bookid, label, reason in HOLD:
        gap = conn.execute("select * from remaining_gap_checkpoint_v1_items where run_id=? and bookid=?", (latest_gap, bookid)).fetchone()
        conn.execute("insert into parse_competition_consolidation_v1_items values (?,?,?,?,?,?,?,?)", (run_id, bookid, label, "HOLD", 0, 0, reason, json.dumps({"gap": dict(gap) if gap else None}, ensure_ascii=False, sort_keys=True)))
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": "PARSE_COMPETITION_STRUCTURAL_PROMOTION_NO_GLOSS", **summary, "accepted_prose_gloss_count": 0}, ensure_ascii=False))

if __name__ == "__main__":
    main()
