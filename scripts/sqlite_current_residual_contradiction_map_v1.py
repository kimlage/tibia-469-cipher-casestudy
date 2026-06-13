#!/usr/bin/env python3
"""Map current residual contradictions and supersede stale residual decisions."""
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
        create table if not exists current_residual_contradiction_map_v1_runs (
            run_id integer primary key autoincrement,
            created_at text not null,
            decision text not null,
            current_gap_count integer not null,
            stale_decision_superseded_count integer not null,
            active_blocked_count integer not null,
            summary_json text not null
        );
        create table if not exists current_residual_contradiction_map_v1_items (
            run_id integer not null,
            bookid text not null,
            current_state text not null,
            current_reading text not null,
            stale_decision text not null,
            contradiction_status text not null,
            next_action text not null,
            evidence_json text not null,
            primary key (run_id, bookid)
        );
        """
    )
    latest_read = conn.execute("select max(run_id) as run_id from honest_full_functional_reading_v1_books").fetchone()["run_id"]
    latest_gap = conn.execute("select max(run_id) as run_id from remaining_gap_checkpoint_v1_items").fetchone()["run_id"]
    latest_agent = conn.execute("select max(run_id) as run_id from agent_residual_decision_consolidation_v1_items").fetchone()["run_id"]
    readings = {r["bookid"]: dict(r) for r in conn.execute("select * from honest_full_functional_reading_v1_books where run_id=?", (latest_read,))}
    gaps = {r["bookid"]: dict(r) for r in conn.execute("select * from remaining_gap_checkpoint_v1_items where run_id=?", (latest_gap,))}
    stale = {r["bookid"]: dict(r) for r in conn.execute("select * from agent_residual_decision_consolidation_v1_items where run_id=?", (latest_agent,))}
    books = sorted(set(gaps) | set(stale), key=lambda x: int(x))
    items = []
    for bookid in books:
        cur = readings.get(bookid, {})
        st = stale.get(bookid)
        is_gap = bookid in gaps
        if st and not is_gap and cur.get("status") in ("FUNCTIONAL_CORE", "FUNCTIONAL_RELATED"):
            cstatus = "STALE_HOLD_SUPERSEDED_BY_TEMPLATE_PROMOTION"
            next_action = "Use latest functional reading; retain stale hold only as historical evidence."
        elif is_gap:
            cstatus = "ACTIVE_RESIDUAL_BLOCKED"
            next_action = gaps[bookid].get("reason", "Keep blocked until new evidence.")
        else:
            cstatus = "HISTORICAL_ONLY"
            next_action = "No current residual action."
        evidence = {"latest_reading_run": latest_read, "latest_gap_run": latest_gap, "current_reading": cur, "current_gap": gaps.get(bookid), "stale_agent_decision": st}
        items.append((bookid, cur.get("status", "MISSING"), cur.get("functional_reading", "<missing>"), st.get("consolidated_label", "NONE") if st else "NONE", cstatus, next_action, json.dumps(evidence, ensure_ascii=False, sort_keys=True)))
    superseded = sum(1 for i in items if i[4] == "STALE_HOLD_SUPERSEDED_BY_TEMPLATE_PROMOTION")
    active = sum(1 for i in items if i[4] == "ACTIVE_RESIDUAL_BLOCKED")
    summary = {"latest_reading_run": latest_read, "latest_gap_run": latest_gap, "superseded_books": [i[0] for i in items if i[4] == "STALE_HOLD_SUPERSEDED_BY_TEMPLATE_PROMOTION"], "active_residual_books": [i[0] for i in items if i[4] == "ACTIVE_RESIDUAL_BLOCKED"]}
    cur = conn.execute(
        """
        insert into current_residual_contradiction_map_v1_runs
        (created_at, decision, current_gap_count, stale_decision_superseded_count, active_blocked_count, summary_json)
        values (?, ?, ?, ?, ?, ?)
        """,
        (utc_now(), "CURRENT_RESIDUAL_MAP_BUILT_STALE_HOLDS_SUPERSEDED", len(gaps), superseded, active, json.dumps(summary, ensure_ascii=False, sort_keys=True)),
    )
    run_id = cur.lastrowid
    for item in items:
        conn.execute(
            """
            insert into current_residual_contradiction_map_v1_items
            (run_id, bookid, current_state, current_reading, stale_decision, contradiction_status, next_action, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, *item),
        )
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": "CURRENT_RESIDUAL_MAP_BUILT_STALE_HOLDS_SUPERSEDED", "current_gap_count": len(gaps), "stale_decision_superseded_count": superseded, "active_blocked_count": active, "summary": summary}, ensure_ascii=False))


if __name__ == "__main__":
    main()
