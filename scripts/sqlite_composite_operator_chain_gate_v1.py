#!/usr/bin/env python3
"""Segment residual composite books at preserved operators/selectors."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
TARGETS = ("4", "24")
SELECTORS = {"C86": "C86_OPERATOR", "C68": "C68_CONTEXT", "O23": "O23_SCOPE", "R20": "R20_CONNECTOR", "R02": "R02_CONNECTOR", "VINVIN": "VINVIN_BRANCH", "VNCTIIN": "VNCTIIN_CONTEXT", "NAESE": "NAESE_SLOT", "BENNA": "BENNA_FORMULA", "FNAAST": "FNAAST_PAYLOAD", "LTAST": "LTAST_CONTINUATION"}


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def segment(tokens):
    points = [i for i, t in enumerate(tokens) if t in SELECTORS or t == "*00"]
    if 0 not in points:
        points = [0] + points
    points = sorted(set(points + [len(tokens)]))
    segs = []
    for a, b in zip(points, points[1:]):
        chunk = tokens[a:b]
        labels = [SELECTORS[t] for t in chunk if t in SELECTORS]
        if labels or "*00" in chunk:
            segs.append({"start": a, "end": b, "text": " ".join(chunk), "labels": labels, "has_zero": "*00" in chunk})
    return segs


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.executescript("""
    create table if not exists composite_operator_chain_gate_v1_runs (
        run_id integer primary key autoincrement,
        created_at text not null,
        decision text not null,
        target_count integer not null,
        promoted_count integer not null,
        held_count integer not null,
        accepted_prose_gloss_count integer not null,
        summary_json text not null
    );
    create table if not exists composite_operator_chain_gate_v1_items (
        run_id integer not null,
        bookid text not null,
        gate_status text not null,
        proposed_label text not null,
        promotion_allowed integer not null,
        prose_gloss_allowed integer not null,
        segment_count integer not null,
        selector_labels text not null,
        reason text not null,
        next_action text not null,
        evidence_json text not null,
        primary key (run_id, bookid)
    );
    """)
    items = []
    for bookid in TARGETS:
        row = conn.execute("select * from row0_variant_book_tokens where bookid=?", (bookid,)).fetchone()
        tokens = json.loads(row["tokens_json"])
        segs = segment(tokens)
        labels = sorted({lab for s in segs for lab in s["labels"]})
        if bookid == "4" and {"C86_OPERATOR", "O23_SCOPE"}.issubset(labels) and any("R20_CONNECTOR" in s["labels"] for s in segs):
            status = "PROMOTE_COMPOSITE_OPERATOR_CHAIN_NO_GLOSS"
            label = "COMPOSITE_C86_O23_R20_OPERATOR_CHAIN"
            promote = 1
            reason = "Segmentation separates C86, O23 and R20 selector zones; treat as composite control chain instead of mixed unresolved unit."
            next_action = "No family-wide promotion; use only as segmented negative/control chain."
        elif bookid == "24" and {"C68_CONTEXT", "O23_SCOPE"}.issubset(labels):
            status = "PROMOTE_COMPOSITE_C68_O23_BOUNDARY_NO_GLOSS"
            label = "COMPOSITE_C68_CONTEXT_TO_O23_SCOPE_BOUNDARY"
            promote = 1
            reason = "Segmentation separates C68 context prefix from O23 scoped branch; resolves prior contamination by keeping boundary explicit."
            next_action = "Promote as composite boundary only; no O23 or C68 global edge promotion."
        else:
            status = "HOLD_COMPOSITE_UNSEPARATED"
            label = "COMPOSITE_AUDIT"
            promote = 0
            reason = "Selector segmentation did not isolate enough typed zones."
            next_action = "Hold."
        evidence = {"tokens": tokens, "segments": segs}
        items.append((bookid, status, label, promote, 0, len(segs), ",".join(labels), reason, next_action, json.dumps(evidence, ensure_ascii=False, sort_keys=True)))
    promoted = sum(i[3] for i in items)
    cur = conn.execute("insert into composite_operator_chain_gate_v1_runs (created_at,decision,target_count,promoted_count,held_count,accepted_prose_gloss_count,summary_json) values (?,?,?,?,?,?,?)", (utc_now(), "COMPOSITE_OPERATOR_CHAIN_STRUCTURAL_NO_GLOSS", len(TARGETS), promoted, len(TARGETS)-promoted, 0, json.dumps({"targets": list(TARGETS), "principle": "segmented operator chains only"}, ensure_ascii=False, sort_keys=True)))
    run_id = cur.lastrowid
    for item in items:
        conn.execute("insert into composite_operator_chain_gate_v1_items values (?,?,?,?,?,?,?,?,?,?,?)", (run_id, *item))
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": "COMPOSITE_OPERATOR_CHAIN_STRUCTURAL_NO_GLOSS", "promoted_count": promoted, "items": [{"bookid": i[0], "status": i[1], "label": i[2], "promote": i[3], "selectors": i[6]} for i in items]}, ensure_ascii=False))

if __name__ == "__main__":
    main()
