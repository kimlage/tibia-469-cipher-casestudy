#!/usr/bin/env python3
"""Promote only contradiction-reducing residual template-frame classifications, no gloss."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

PROMOTE = [
    ("31", "F2_C86_OPERATOR_CONTEXT_STACKED", "RELATED_CONTEXT", "Repeated C86/C68/VNCTIIN context-frame composition; resolves handoff/slot tie as stacked context frame, no lexical gloss."),
    ("57", "F2_C86_OPERATOR_CONTEXT_REPEATED", "RELATED_CONTEXT", "Multi C86/C68/VNCTIIN pattern; resolves VNCTIIN context as repeated frame composition, no lexical gloss."),
    ("37", "F1_BENNA_LTAST_CONTINUATION", "RELATED_CONTEXT", "BENNA/LTAST continuation with C68/context tail; classify as formula-slot continuation, no lexical gloss."),
    ("30", "F6_BOOK30_CONTEXT_HELDOUT_FRAGMENT", "RELATED_CONTEXT", "Held-out Book30 context fragment under F6 frame; function still contextual, no lexical gloss."),
]
HOLD = [
    ("32", "F7_FNAAST_DISPLAY_WINDOW_HELD", "DISPLAY_FORMULA_RESIDUE", "Clean display window but no independent payload; held as formula/display residue."),
    ("14", "F1_LTAST_SLOT_AUDIT", "WEAK_AUDIT", "LTAST slot only; insufficient for promotion."),
    ("19", "BENNA_C86_SURFACE_AUDIT", "WEAK_AUDIT", "Quarantined BENNA plus C86 context; audit/control only."),
    ("23", "F3_NAESE_C68_TAIL_AUDIT", "WEAK_AUDIT", "Weak NAESE/C68 tail; insufficient accepted NAESE support."),
    ("24", "COMPOSITE_BOUNDARY_AMBIGUITY", "WEAK_AUDIT", "Mixed O23, Book30 and C86 traces; composite-boundary ambiguity."),
    ("34", "F4_VINVIN_BRANCH_TAIL_AUDIT", "WEAK_AUDIT", "Weak VINVIN/LEAFI exit trace; branch-tail audit only."),
    ("4", "MIXED_VINVIN_ONAF_NEGATIVE_CONTROL", "NEGATIVE_CONTROL", "Mixed VINVIN/O23/C86 negative/control parse, not clean residual resolution."),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main() -> None:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        create table if not exists template_frame_residual_promotion_v1_runs (
            run_id integer primary key autoincrement,
            created_at text not null,
            decision text not null,
            promoted_count integer not null,
            held_count integer not null,
            accepted_prose_gloss_count integer not null,
            summary_json text not null
        );
        create table if not exists template_frame_residual_promotion_v1_items (
            run_id integer not null,
            bookid text not null,
            frame_label text not null,
            decision_status text not null,
            promote_allowed integer not null,
            prose_gloss_allowed integer not null,
            reason text not null,
            evidence_json text not null,
            primary key (run_id, bookid)
        );
        """
    )
    latest_gap = conn.execute("select max(run_id) as run_id from remaining_gap_checkpoint_v1_items").fetchone()["run_id"]
    summary = {
        "source": "template grammar subagent + local concordance gates",
        "promoted_books": [x[0] for x in PROMOTE],
        "held_books": [x[0] for x in HOLD],
        "principle": "promotions are structural related-context only, not human prose",
    }
    cur = conn.execute(
        """
        insert into template_frame_residual_promotion_v1_runs
        (created_at, decision, promoted_count, held_count, accepted_prose_gloss_count, summary_json)
        values (?, ?, ?, ?, ?, ?)
        """,
        (utc_now(), "TEMPLATE_FRAME_RESIDUAL_STRUCTURAL_PROMOTION_NO_GLOSS", len(PROMOTE), len(HOLD), 0, json.dumps(summary, ensure_ascii=False, sort_keys=True)),
    )
    run_id = cur.lastrowid
    for bookid, label, status, reason in PROMOTE:
        gap = conn.execute("select * from remaining_gap_checkpoint_v1_items where run_id=? and bookid=?", (latest_gap, bookid)).fetchone()
        conn.execute(
            """
            insert into template_frame_residual_promotion_v1_items
            (run_id, bookid, frame_label, decision_status, promote_allowed, prose_gloss_allowed, reason, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, bookid, label, status, 1, 0, reason, json.dumps({"gap": dict(gap) if gap else None}, ensure_ascii=False, sort_keys=True)),
        )
    for bookid, label, status, reason in HOLD:
        gap = conn.execute("select * from remaining_gap_checkpoint_v1_items where run_id=? and bookid=?", (latest_gap, bookid)).fetchone()
        conn.execute(
            """
            insert into template_frame_residual_promotion_v1_items
            (run_id, bookid, frame_label, decision_status, promote_allowed, prose_gloss_allowed, reason, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, bookid, label, status, 0, 0, reason, json.dumps({"gap": dict(gap) if gap else None}, ensure_ascii=False, sort_keys=True)),
        )
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": "TEMPLATE_FRAME_RESIDUAL_STRUCTURAL_PROMOTION_NO_GLOSS", "promoted_count": len(PROMOTE), "held_count": len(HOLD), "accepted_prose_gloss_count": 0, "promoted_books": [x[0] for x in PROMOTE]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
