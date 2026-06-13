#!/usr/bin/env python3
"""Classify remaining residuals as terminal limits unless new evidence appears."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

LABELS = {
    "6": ("TERMINAL_DISPLAY_CONTINUITY_PHASE_RISK", "High row0 phase risk plus display/continuity; no safe structural promotion."),
    "7": ("TERMINAL_PHASE_RARE_CONTINUITY", "High row0 phase risk and rare/continuity motifs; no stable function."),
    "14": ("TERMINAL_LTAST_SLOT_PHASE_RISK", "LTAST slot evidence exists but row0 phase/path ambiguity blocks promotion."),
    "32": ("TERMINAL_FORMULA_DISPLAY_LOW_SIGNAL", "FNAAST/display formula evidence only; payload transfer rejected."),
    "34": ("TERMINAL_BRANCH_TAIL_INTERNAL_RESIDUAL", "VINVIN/LEAFI branch-tail resemblance lacks operator carrier and has phase risk."),
    "36": ("TERMINAL_DISPLAY_DRIFT_CONTROL", "Display drift/control only; no semantic or structural payload."),
    "41": ("TERMINAL_CONTEXT_FRAGMENT_MODERATE", "Moderate context fragment; kept as audit control without new mechanical contrast."),
    "49": ("TERMINAL_O32_REPEAT_PHASE_RISK", "O32/repetition singleton with high row0 phase/path ambiguity; no O23 merge."),
}


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.executescript("""
    create table if not exists terminal_residual_limit_v1_runs (
        run_id integer primary key autoincrement,
        created_at text not null,
        decision text not null,
        item_count integer not null,
        promoted_count integer not null,
        accepted_prose_gloss_count integer not null,
        summary_json text not null
    );
    create table if not exists terminal_residual_limit_v1_items (
        run_id integer not null,
        bookid text not null,
        terminal_label text not null,
        promotion_allowed integer not null,
        prose_gloss_allowed integer not null,
        reason text not null,
        required_new_evidence text not null,
        evidence_json text not null,
        primary key (run_id, bookid)
    );
    """)
    latest_gap = conn.execute("select max(run_id) as run_id from remaining_gap_checkpoint_v1_items").fetchone()["run_id"]
    latest_honest = conn.execute("select max(run_id) as run_id from honest_full_functional_reading_v1_books").fetchone()["run_id"]
    items = []
    for bookid, (label, reason) in LABELS.items():
        gap = conn.execute("select * from remaining_gap_checkpoint_v1_items where run_id=? and bookid=?", (latest_gap, bookid)).fetchone()
        reading = conn.execute("select * from honest_full_functional_reading_v1_books where run_id=? and bookid=?", (latest_honest, bookid)).fetchone()
        phase = conn.execute("select * from residual_row0_phase_risk_gate_v1_items where run_id=(select max(run_id) from residual_row0_phase_risk_gate_v1_items) and bookid=?", (bookid,)).fetchone()
        non_lcs = conn.execute("select * from residual_non_lcs_evidence_matrix_v1_items where run_id=(select max(run_id) from residual_non_lcs_evidence_matrix_v1_items) and bookid=?", (bookid,)).fetchone()
        required = "external exact meaning/provenance, contig edge support, or row0 phase/path resolution with selector-preserving improvement"
        evidence = {"gap": dict(gap) if gap else None, "reading": dict(reading) if reading else None, "phase": dict(phase) if phase else None, "non_lcs": dict(non_lcs) if non_lcs else None}
        items.append((bookid, label, 0, 0, reason, required, json.dumps(evidence, ensure_ascii=False, sort_keys=True)))
    summary = {"terminal_books": sorted(LABELS, key=int), "principle": "terminal means current evidence limit, not puzzle solved; reopen only with materially new evidence"}
    cur = conn.execute("insert into terminal_residual_limit_v1_runs (created_at,decision,item_count,promoted_count,accepted_prose_gloss_count,summary_json) values (?,?,?,?,?,?)", (utc_now(), "CURRENT_RESIDUALS_TERMINAL_LIMIT_NO_PROMOTION", len(items), 0, 0, json.dumps(summary, ensure_ascii=False, sort_keys=True)))
    run_id = cur.lastrowid
    for item in items:
        conn.execute("insert into terminal_residual_limit_v1_items values (?,?,?,?,?,?,?,?)", (run_id, *item))
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": "CURRENT_RESIDUALS_TERMINAL_LIMIT_NO_PROMOTION", "item_count": len(items), "promoted_count": 0, "accepted_prose_gloss_count": 0, "terminal_books": sorted(LABELS, key=int)}, ensure_ascii=False))

if __name__ == "__main__":
    main()
