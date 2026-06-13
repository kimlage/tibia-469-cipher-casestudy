#!/usr/bin/env python3
"""Classify current residuals by row0 phase/omission risk before semantic work."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main() -> None:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        create table if not exists residual_row0_phase_risk_gate_v1_runs (
            run_id integer primary key autoincrement,
            created_at text not null,
            decision text not null,
            residual_count integer not null,
            high_risk_count integer not null,
            alternate_path_count integer not null,
            semantic_hold_count integer not null,
            summary_json text not null
        );
        create table if not exists residual_row0_phase_risk_gate_v1_items (
            run_id integer not null,
            bookid text not null,
            risk_class text not null,
            pathcount integer not null,
            insertedzeros integer not null,
            phase_confidence text not null,
            phase_score_margin real,
            semantic_action_allowed integer not null,
            mechanical_next_action text not null,
            evidence_json text not null,
            primary key (run_id, bookid)
        );
        """
    )
    latest_gap = conn.execute("select max(run_id) as run_id from remaining_gap_checkpoint_v1_items").fetchone()["run_id"]
    residuals = [r["bookid"] for r in conn.execute("select bookid from remaining_gap_checkpoint_v1_items where run_id=? order by bookid+0", (latest_gap,))]
    items = []
    for bookid in residuals:
        r = conn.execute("select * from row0_omission_probe_book_items where bookid=? order by run_id desc limit 1", (bookid,)).fetchone()
        paths = list(conn.execute("select * from row0_path_reconstruction_items where bookid=? order by run_id desc, path_rank", (bookid,)))
        if not r:
            continue
        risk = r["risk_class"]
        pathcount = int(r["pathcount"])
        if risk == "HIGH_ROW0_PHASE_RISK" or pathcount > 1:
            semantic_allowed = 0
            next_action = "Resolve row0 phase/path ambiguity before semantic promotion."
        elif risk == "MEDIUM_ROW0_PHASE_RISK":
            semantic_allowed = 0
            next_action = "Use only as mechanical audit/control unless independent evidence confirms path."
        else:
            semantic_allowed = 1
            next_action = "Row0 phase is not the primary blocker; seek grammar/external evidence."
        evidence = {"omission_probe": dict(r), "paths": [dict(p) for p in paths]}
        items.append((bookid, risk, pathcount, int(r["insertedzeros"]), r["phase_confidence"] or "", r["phase_score_margin"], semantic_allowed, next_action, json.dumps(evidence, ensure_ascii=False, sort_keys=True)))
    high = sum(1 for i in items if i[1] == "HIGH_ROW0_PHASE_RISK")
    alt = sum(1 for i in items if i[2] > 1)
    hold = sum(1 for i in items if i[6] == 0)
    summary = {"high_risk_books": [i[0] for i in items if i[1] == "HIGH_ROW0_PHASE_RISK"], "alternate_path_books": [i[0] for i in items if i[2] > 1], "semantic_hold_books": [i[0] for i in items if i[6] == 0]}
    cur = conn.execute(
        """
        insert into residual_row0_phase_risk_gate_v1_runs
        (created_at, decision, residual_count, high_risk_count, alternate_path_count, semantic_hold_count, summary_json)
        values (?, ?, ?, ?, ?, ?, ?)
        """,
        (utc_now(), "RESIDUAL_ROW0_PHASE_RISK_GATED_BEFORE_SEMANTICS", len(items), high, alt, hold, json.dumps(summary, ensure_ascii=False, sort_keys=True)),
    )
    run_id = cur.lastrowid
    for item in items:
        conn.execute(
            """
            insert into residual_row0_phase_risk_gate_v1_items
            (run_id, bookid, risk_class, pathcount, insertedzeros, phase_confidence,
             phase_score_margin, semantic_action_allowed, mechanical_next_action, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, *item),
        )
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": "RESIDUAL_ROW0_PHASE_RISK_GATED_BEFORE_SEMANTICS", "residual_count": len(items), "high_risk_count": high, "alternate_path_count": alt, "semantic_hold_count": hold, "summary": summary}, ensure_ascii=False))


if __name__ == "__main__":
    main()
