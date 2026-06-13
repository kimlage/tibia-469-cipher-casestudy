#!/usr/bin/env python3
"""Consolidate residual subagent decisions into SQLite, preserving no-promotion gates."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

DECISIONS = [
    ("4", "AUDIT_ONLY_MIXED_VINVIN_ONAF", "HOLD_QUARANTINE", "Book 4 mixes C86/VINVIN-like material with O23 negative branch; promotion would contaminate VINVIN/ONAF families.", "Run only narrow C86/VINVIN vs O23/ONAF contrast if new evidence appears."),
    ("8", "AUDIT_ONLY_ZERO_MARGIN_HANDOFF_SLOT_TIE", "HOLD_QUARANTINE", "Positive handoff and negative slot scores tie exactly; no discriminator.", "Do not reopen unless a new contrast breaks 10->book vs book->2 tie."),
    ("23", "AUDIT_ONLY_PRE_SLOT_LOW_EVIDENCE", "HOLD_QUARANTINE", "Positive margin exists but overlap is only 1 and no accepted NAESE support.", "Reopen only with literal/accepted NAESE support or materially stronger overlap."),
    ("24", "AUDIT_ONLY_ZERO_MARGIN_HANDOFF_SLOT_TIE", "HOLD_QUARANTINE", "Positive handoff and negative slot scores tie exactly; no discriminator.", "Do not reopen without new mechanical discriminator."),
    ("31", "AUDIT_ONLY_ZERO_MARGIN_HANDOFF_SLOT_TIE", "HOLD_QUARANTINE", "Positive handoff and negative slot scores tie exactly; no discriminator.", "Do not reopen without new contrast separating handoff from slot behavior."),
    ("32", "MANUAL_REVIEW_FORMULA_DISPLAY_RESIDUE", "HOLD_LOW_SIGNAL", "Formula/display proximity against 58/59 is weak; payload transfer rejected; formula mask does not recover book.", "Only residual_context_concordance around FNAAST/TNBEE vs 11/32/43/58/59."),
    ("37", "AUDIT_ONLY_ZERO_MARGIN_HANDOFF_SLOT_TIE", "HOLD_QUARANTINE", "Positive handoff and negative slot scores tie exactly; no discriminator.", "Do not reopen unless a new mechanical run resolves zero-margin conflict."),
    ("41", "AUDIT_ONLY_CONTEXT_FRAGMENT_MODERATE", "HOLD_QUARANTINE", "Moderate 10/35 context fragment but below gate and kept as audit control.", "Do not reopen for promotion without new mechanical contrast."),
    ("57", "AUDIT_ONLY_VNCTIIN_CONTEXT_LOW_MARGIN", "HOLD_QUARANTINE", "VNCTIIN-heavy but margin over handoff alternative is too low.", "Reopen only if VNCTIIN/C86 contrast widens beyond handoff alternative."),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main() -> None:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        create table if not exists agent_residual_decision_consolidation_v1_runs (
            run_id integer primary key autoincrement,
            created_at text not null,
            decision text not null,
            item_count integer not null,
            promote_count integer not null,
            hold_count integer not null,
            accepted_prose_gloss_count integer not null,
            summary_json text not null
        );
        create table if not exists agent_residual_decision_consolidation_v1_items (
            run_id integer not null,
            bookid text not null,
            consolidated_label text not null,
            decision_status text not null,
            promote_allowed integer not null,
            prose_gloss_allowed integer not null,
            reason text not null,
            next_action text not null,
            evidence_json text not null,
            primary key (run_id, bookid)
        );
        """
    )
    summary = {
        "sources": ["subagent_quarantine_lane", "subagent_book4_lane", "subagent_book32_lane"],
        "principle": "agent consolidation records no-promotion decisions; it must not inflate translation metrics",
    }
    cur = conn.execute(
        """
        insert into agent_residual_decision_consolidation_v1_runs
        (created_at, decision, item_count, promote_count, hold_count, accepted_prose_gloss_count, summary_json)
        values (?, ?, ?, ?, ?, ?, ?)
        """,
        (utc_now(), "RESIDUAL_AGENT_DECISIONS_CONSOLIDATED_NO_PROMOTIONS", len(DECISIONS), 0, len(DECISIONS), 0, json.dumps(summary, ensure_ascii=False, sort_keys=True)),
    )
    run_id = cur.lastrowid
    latest_gap = conn.execute("select max(run_id) as run_id from remaining_gap_checkpoint_v1_items").fetchone()["run_id"]
    for bookid, label, status, reason, next_action in DECISIONS:
        gap = conn.execute("select * from remaining_gap_checkpoint_v1_items where run_id=? and bookid=?", (latest_gap, bookid)).fetchone()
        evidence = {"latest_gap": dict(gap) if gap else None, "source": "subagent_consolidated_summary"}
        conn.execute(
            """
            insert into agent_residual_decision_consolidation_v1_items
            (run_id, bookid, consolidated_label, decision_status, promote_allowed, prose_gloss_allowed, reason, next_action, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, bookid, label, status, 0, 0, reason, next_action, json.dumps(evidence, ensure_ascii=False, sort_keys=True)),
        )
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": "RESIDUAL_AGENT_DECISIONS_CONSOLIDATED_NO_PROMOTIONS", "item_count": len(DECISIONS), "promote_count": 0, "accepted_prose_gloss_count": 0}, ensure_ascii=False))


if __name__ == "__main__":
    main()
