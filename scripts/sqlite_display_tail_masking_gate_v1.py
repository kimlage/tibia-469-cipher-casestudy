#!/usr/bin/env python3
"""Mask shared display tails in books 32/36 and test whether independent payload remains."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
TARGETS = ("32", "36")
DISPLAY_TAIL = "ALBENEIENVNSBVN*VAENFFATFN"


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.executescript("""
    create table if not exists display_tail_masking_gate_v1_runs (
        run_id integer primary key autoincrement,
        created_at text not null,
        decision text not null,
        target_count integer not null,
        promoted_count integer not null,
        held_count integer not null,
        accepted_prose_gloss_count integer not null,
        summary_json text not null
    );
    create table if not exists display_tail_masking_gate_v1_items (
        run_id integer not null,
        bookid text not null,
        gate_status text not null,
        proposed_label text not null,
        promotion_allowed integer not null,
        prose_gloss_allowed integer not null,
        masked_tail_found integer not null,
        residual_text text not null,
        reason text not null,
        next_action text not null,
        evidence_json text not null,
        primary key (run_id, bookid)
    );
    """)
    items = []
    for bookid in TARGETS:
        row = conn.execute("select * from row0_variant_book_tokens where bookid=?", (bookid,)).fetchone()
        text = row["symbol_text"]
        found = DISPLAY_TAIL in text
        residual = text.replace(DISPLAY_TAIL, "<DISPLAY_TAIL>") if found else text
        # Promotion only if residual contains a non-display accepted operator not already explained by display/FNAAST.
        non_display_signal = any(x in residual for x in ("C68", "C86", "O23", "R20", "R02", "NAESE", "VINVIN", "VNCTIIN"))
        if found and not non_display_signal:
            status = "HOLD_DISPLAY_TAIL_ONLY_NO_PAYLOAD"
            label = "DISPLAY_TAIL_CONTROL_ONLY"
            promote = 0
            reason = "After masking the shared display tail, no independent operator/payload remains."
            next_action = "Keep as display control; do not promote."
        elif found and non_display_signal:
            status = "PROMOTE_DISPLAY_TAIL_WITH_INDEPENDENT_PAYLOAD_NO_GLOSS"
            label = "DISPLAY_TAIL_WITH_PAYLOAD_BOUNDARY"
            promote = 1
            reason = "Shared display tail masks cleanly and residual retains independent operator/payload signal."
            next_action = "Promote only as structural boundary, no gloss."
        else:
            status = "HOLD_DISPLAY_TAIL_NOT_FOUND"
            label = "DISPLAY_TAIL_AUDIT"
            promote = 0
            reason = "Expected shared display tail was not found exactly."
            next_action = "Hold."
        evidence = {"symbol_text": text, "display_tail": DISPLAY_TAIL, "residual": residual, "non_display_signal": non_display_signal}
        items.append((bookid, status, label, promote, 0, int(found), residual, reason, next_action, json.dumps(evidence, ensure_ascii=False, sort_keys=True)))
    promoted = sum(i[3] for i in items)
    cur = conn.execute("insert into display_tail_masking_gate_v1_runs values (null,?,?,?,?,?,?,?)", (utc_now(), "DISPLAY_TAIL_MASKING_GATE_NO_GLOSS", len(TARGETS), promoted, len(TARGETS)-promoted, 0, json.dumps({"targets": list(TARGETS), "promoted": [i[0] for i in items if i[3]]}, ensure_ascii=False, sort_keys=True)))
    run_id = cur.lastrowid
    for item in items:
        conn.execute("insert into display_tail_masking_gate_v1_items values (?,?,?,?,?,?,?,?,?,?,?)", (run_id, *item))
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": "DISPLAY_TAIL_MASKING_GATE_NO_GLOSS", "promoted_count": promoted, "items": [{"bookid": i[0], "status": i[1], "promote": i[3], "masked_tail_found": i[5], "residual_text": i[6][:80]} for i in items], "accepted_prose_gloss_count": 0}, ensure_ascii=False))

if __name__ == "__main__":
    main()
