#!/usr/bin/env python3
"""Checkpoint residual unresolved strategy so the loop does not reopen dead lanes blindly."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

DECISIONS = {
    "FRONTIER_QUARANTINED_NEEDS_NEW_EVIDENCE": ("HOLD_UNLESS_NEW_MECHANICAL_EVIDENCE", "Do not reopen old quarantine lanes from LCS/surface recurrence alone."),
    "LOW_OVERLAP_FRAGMENT_AUDIT": ("CONTRAST_ONLY_NOT_LCS", "Only run if a specific operator-crossing or slot split is defined."),
    "DISPLAY_OR_CONTINUITY_AUDIT_REQUIRED": ("DISPLAY_CONTROL_ONLY", "Keep as no-gloss display/continuity controls unless a new accepted-role bridge appears."),
    "RARE_OR_SINGLETON_MOTIF_SEARCH": ("PAIR_OR_CONTROL_ONLY", "Use only structural pairs or negative singleton controls; no lexical promotion."),
    "VARIANT_FAMILY_CONTRAST_REQUIRED": ("VARIANT_SPLIT_REQUIRED", "Promote only book-scoped structural split with negative controls."),
    "MANUAL_REVIEW_LOW_SIGNAL": ("HOLD_LOW_SIGNAL", "Manual review only; no promotion without external exact or internal contrast."),
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main() -> None:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        create table if not exists residual_strategy_checkpoint_v1_runs (
            run_id integer primary key autoincrement,
            created_at text not null,
            decision text not null,
            gap_count integer not null,
            reopen_now_count integer not null,
            hold_count integer not null,
            summary_json text not null
        );
        create table if not exists residual_strategy_checkpoint_v1_items (
            run_id integer not null,
            bookid text not null,
            current_status text not null,
            current_reading text not null,
            next_method text not null,
            strategy_status text not null,
            reopen_now integer not null,
            reason text not null,
            required_new_evidence text not null,
            evidence_json text not null,
            primary key (run_id, bookid)
        );
        """
    )
    latest_gap = conn.execute("select max(run_id) as run_id from remaining_gap_checkpoint_v1_items").fetchone()["run_id"]
    gaps = list(conn.execute("select * from remaining_gap_checkpoint_v1_items where run_id=? order by bookid+0", (latest_gap,)))
    items = []
    for row in gaps:
        status, reason = DECISIONS.get(row["next_method"], ("HOLD_UNCLASSIFIED", "No strategy registered."))
        required = {
            "HOLD_UNLESS_NEW_MECHANICAL_EVIDENCE": "new non-LCS evidence: exact external anchor, contig edge, or contradiction-reducing parse split",
            "CONTRAST_ONLY_NOT_LCS": "specific contrast target and negative control, not generic overlap",
            "DISPLAY_CONTROL_ONLY": "accepted-role bridge that separates display marker from payload",
            "PAIR_OR_CONTROL_ONLY": "clean pair contrast or preserved negative-control function",
            "VARIANT_SPLIT_REQUIRED": "book-scoped variant split with negative control and no family-wide overfit",
            "HOLD_LOW_SIGNAL": "external exact evidence or internal contrast stronger than current formula/display ambiguity",
        }.get(status, "new mechanical evidence")
        # This checkpoint is intentionally conservative: none of these are reopened automatically here.
        items.append({
            "bookid": row["bookid"],
            "current_status": row["current_status"],
            "current_reading": row["current_reading"],
            "next_method": row["next_method"],
            "strategy_status": status,
            "reopen_now": 0,
            "reason": reason,
            "required_new_evidence": required,
            "evidence_json": json.dumps(dict(row), ensure_ascii=False, sort_keys=True),
        })
    summary = {
        "latest_gap_run": latest_gap,
        "method_counts": dict(conn.execute("select next_method, count(*) from remaining_gap_checkpoint_v1_items where run_id=? group by next_method", (latest_gap,)).fetchall()),
        "principle": "residual lanes require mechanically new evidence; no circular LCS reopening",
    }
    cur = conn.execute(
        """
        insert into residual_strategy_checkpoint_v1_runs
        (created_at, decision, gap_count, reopen_now_count, hold_count, summary_json)
        values (?, ?, ?, ?, ?, ?)
        """,
        (utc_now(), "RESIDUAL_FRONTIER_HELD_PENDING_NEW_MECHANICAL_EVIDENCE", len(items), 0, len(items), json.dumps(summary, ensure_ascii=False, sort_keys=True)),
    )
    run_id = cur.lastrowid
    for item in items:
        conn.execute(
            """
            insert into residual_strategy_checkpoint_v1_items
            (run_id, bookid, current_status, current_reading, next_method, strategy_status,
             reopen_now, reason, required_new_evidence, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, item["bookid"], item["current_status"], item["current_reading"], item["next_method"], item["strategy_status"], item["reopen_now"], item["reason"], item["required_new_evidence"], item["evidence_json"]),
        )
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": "RESIDUAL_FRONTIER_HELD_PENDING_NEW_MECHANICAL_EVIDENCE", "gap_count": len(items), "reopen_now_count": 0, "hold_count": len(items), "summary": summary}, ensure_ascii=False))


if __name__ == "__main__":
    main()
