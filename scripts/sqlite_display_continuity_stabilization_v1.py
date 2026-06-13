#!/usr/bin/env python3
"""Stabilize display/continuity audit cases without promoting them as semantic readings."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
TARGETS = ("6", "19", "36")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def qone(conn: sqlite3.Connection, sql: str, args=()):
    return conn.execute(sql, args).fetchone()


def main() -> None:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        create table if not exists display_continuity_stabilization_v1_runs (
            run_id integer primary key autoincrement,
            created_at text not null,
            decision text not null,
            target_count integer not null,
            stabilized_count integer not null,
            promoted_count integer not null,
            accepted_prose_gloss_count integer not null,
            summary_json text not null
        );
        create table if not exists display_continuity_stabilization_v1_items (
            run_id integer not null,
            bookid text not null,
            current_status text not null,
            current_reading text not null,
            stabilization_status text not null,
            semantic_promotion_allowed integer not null,
            prose_gloss_allowed integer not null,
            dominant_anchor text not null,
            overlap_len integer not null,
            reason text not null,
            next_action text not null,
            evidence_json text not null,
            primary key (run_id, bookid)
        );
        """
    )

    latest_gap_run = qone(conn, "select max(run_id) as run_id from remaining_gap_checkpoint_v1_items")["run_id"]
    latest_reading_run = qone(conn, "select max(run_id) as run_id from honest_full_functional_reading_v1_books")["run_id"]

    items = []
    for bookid in TARGETS:
        gap = qone(
            conn,
            """
            select * from remaining_gap_checkpoint_v1_items
            where run_id=? and bookid=?
            """,
            (latest_gap_run, bookid),
        )
        reading = qone(
            conn,
            """
            select * from honest_full_functional_reading_v1_books
            where run_id=? and bookid=?
            """,
            (latest_reading_run, bookid),
        )
        token = qone(conn, "select symbol_text, token_count from row0_variant_book_tokens where bookid=?", (bookid,))
        drift = qone(
            conn,
            """
            select * from btii_display_drift_gate_items
            where bookid=? order by run_id desc limit 1
            """,
            (bookid,),
        )

        current_status = reading["status"] if reading else "MISSING"
        current_reading = reading["functional_reading"] if reading else "<missing>"
        anchor = gap["best_overlap_anchor"] if gap else "NONE"
        overlap_len = int(gap["best_overlap_len"] if gap else 0)

        if bookid == "36" and drift:
            stabilization_status = "STABILIZED_DISPLAY_DRIFT_CONTROL_NO_GLOSS"
            reason = "BTII/NSBVN/ATFNAAST display drift is book-scoped and already gated as no-gloss; keep as display control, not semantic reading."
            next_action = "Do not promote semantically; use only as negative/control evidence for display-formula families."
        elif bookid == "19":
            stabilization_status = "STABILIZED_SURFACE_BENNA_CONTEXT_NO_GLOSS"
            reason = "Overlaps handoff/context material but remains surface BENNA context below related-function gate; no independent role."
            next_action = "Keep quarantined until a contrastive contig or external exact anchor separates payload from surface formula."
        else:
            stabilization_status = "STABILIZED_CONTINUITY_AUDIT_NO_ANCHOR"
            reason = "No dominant overlap anchor in remaining-gap checkpoint; likely continuity/display audit case without promotable function."
            next_action = "Do not spend confirmation lane unless new SQLite precheck finds a mechanically different anchor."

        evidence = {
            "latest_gap_run": latest_gap_run,
            "latest_reading_run": latest_reading_run,
            "gap": dict(gap) if gap else None,
            "reading": dict(reading) if reading else None,
            "row0": dict(token) if token else None,
            "display_drift_gate": dict(drift) if drift else None,
        }
        items.append(
            {
                "bookid": bookid,
                "current_status": current_status,
                "current_reading": current_reading,
                "stabilization_status": stabilization_status,
                "semantic_promotion_allowed": 0,
                "prose_gloss_allowed": 0,
                "dominant_anchor": anchor or "NONE",
                "overlap_len": overlap_len,
                "reason": reason,
                "next_action": next_action,
                "evidence_json": json.dumps(evidence, ensure_ascii=False, sort_keys=True),
            }
        )

    summary = {
        "targets": list(TARGETS),
        "stabilized": len(items),
        "semantic_promotions": 0,
        "accepted_prose_glosses": 0,
        "principle": "display/continuity stabilization reduces false positives but does not count as translation progress",
    }
    cur = conn.execute(
        """
        insert into display_continuity_stabilization_v1_runs
        (created_at, decision, target_count, stabilized_count, promoted_count, accepted_prose_gloss_count, summary_json)
        values (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            utc_now(),
            "DISPLAY_CONTINUITY_STABILIZED_NO_SEMANTIC_PROMOTION",
            len(TARGETS),
            len(items),
            0,
            0,
            json.dumps(summary, ensure_ascii=False, sort_keys=True),
        ),
    )
    run_id = cur.lastrowid
    for item in items:
        conn.execute(
            """
            insert into display_continuity_stabilization_v1_items
            (run_id, bookid, current_status, current_reading, stabilization_status,
             semantic_promotion_allowed, prose_gloss_allowed, dominant_anchor, overlap_len,
             reason, next_action, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                item["bookid"],
                item["current_status"],
                item["current_reading"],
                item["stabilization_status"],
                item["semantic_promotion_allowed"],
                item["prose_gloss_allowed"],
                item["dominant_anchor"],
                item["overlap_len"],
                item["reason"],
                item["next_action"],
                item["evidence_json"],
            ),
        )
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": "DISPLAY_CONTINUITY_STABILIZED_NO_SEMANTIC_PROMOTION", **summary}, ensure_ascii=False))


if __name__ == "__main__":
    main()
