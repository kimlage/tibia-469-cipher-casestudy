#!/usr/bin/env python3
"""Test abstract semantic-function hypotheses for C68 dual subframes without human gloss."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
BOOKS = ("2", "8", "19", "23", "24", "27", "57", "67")
HYPOTHESES = [
    ("H_C68_CONTEXT_THEN_SLOT", "C68 has separable context and slot subframes: VN/TIIN context vs FAT/TIV slot."),
    ("H_C68_SINGLE_OPERATOR", "All C68 occurrences share one generic operator function."),
    ("H_C68_HANDOFF_CONTEXT", "C68 primarily marks context handoff after C86/VNCTIIN."),
    ("H_C68_NAESE_SLOT_BODY", "FAT/TIV C68 instances are NAESE slot-body payloads."),
]


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def get_decisions(conn):
    latest = conn.execute("select max(run_id) as run_id from c68_subframe_split_gate_v1_book_decisions").fetchone()["run_id"]
    return {r["bookid"]: dict(r) for r in conn.execute("select * from c68_subframe_split_gate_v1_book_decisions where run_id=?", (latest,))}


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.executescript("""
    create table if not exists c68_semantic_function_hypothesis_v1_runs (
        run_id integer primary key autoincrement,
        created_at text not null,
        decision text not null,
        hypothesis_count integer not null,
        accepted_function_count integer not null,
        accepted_prose_gloss_count integer not null,
        summary_json text not null
    );
    create table if not exists c68_semantic_function_hypothesis_v1_items (
        run_id integer not null,
        hypothesis_id text not null,
        hypothesis text not null,
        status text not null,
        support_score integer not null,
        support_total integer not null,
        prose_gloss_allowed integer not null,
        reason text not null,
        evidence_json text not null,
        primary key (run_id, hypothesis_id)
    );
    """)
    dec = get_decisions(conn)
    # Occurrence-level counts provide evidence for context vs slot split.
    latest_occ = conn.execute("select max(run_id) as run_id from c68_subframe_split_gate_v1_occurrences").fetchone()["run_id"]
    occs = [dict(r) for r in conn.execute("select * from c68_subframe_split_gate_v1_occurrences where run_id=? and bookid in (%s)" % ",".join("?" for _ in BOOKS), (latest_occ, *BOOKS))]
    context_count = sum(1 for o in occs if o["subframe"] == "C68_VN_TIIN_CONTEXT_SUBFRAME")
    slot_count = sum(1 for o in occs if o["subframe"] == "C68_FAT_TIV_SLOT_SUBFRAME")
    weak_count = sum(1 for o in occs if "WEAK" in o["subframe"] or "UNCLASSIFIED" in o["subframe"])
    items = []
    for hid, hyp in HYPOTHESES:
        if hid == "H_C68_CONTEXT_THEN_SLOT":
            score = context_count + slot_count
            if context_count >= 4 and slot_count >= 2:
                status = "ACCEPT_ABSTRACT_FUNCTION_NO_PROSE"
                reason = "Both VN/TIIN context and FAT/TIV slot subframes recur and are separable; accepted as abstract dual-subframe function."
            else:
                status = "REJECT_OR_HOLD_NOT_PREDICTIVE"
                reason = "Dual-subframe recurrence insufficient."
        elif hid == "H_C68_SINGLE_OPERATOR":
            score = len(occs) - weak_count
            status = "REJECT_OVERBROAD_COLLAPSES_SUBFRAMES"
            reason = "Single-operator hypothesis collapses separable C68 subframes and would create contradictions."
        elif hid == "H_C68_HANDOFF_CONTEXT":
            score = context_count
            status = "PARTIAL_CONTEXT_ONLY_NO_PROSE" if context_count >= 4 else "REJECT_OR_HOLD_NOT_PREDICTIVE"
            reason = "Context handoff explains VN/TIIN subframe only, not FAT/TIV slot instances."
        else:
            score = slot_count
            status = "PARTIAL_SLOT_ONLY_NO_PROSE" if slot_count >= 2 else "REJECT_OR_HOLD_NOT_PREDICTIVE"
            reason = "Slot-body explains FAT/TIV subframe only, not VN/TIIN context instances."
        evidence = {"book_decisions": dec, "occurrences": occs, "context_count": context_count, "slot_count": slot_count, "weak_count": weak_count}
        items.append((hid, hyp, status, score, len(occs), 0, reason, json.dumps(evidence, ensure_ascii=False, sort_keys=True)))
    accepted = sum(1 for i in items if i[2] == "ACCEPT_ABSTRACT_FUNCTION_NO_PROSE")
    summary = {"books": list(BOOKS), "accepted_abstract_functions": [i[0] for i in items if i[2] == "ACCEPT_ABSTRACT_FUNCTION_NO_PROSE"], "principle": "abstract C68 split is not human prose"}
    cur = conn.execute("insert into c68_semantic_function_hypothesis_v1_runs values (null,?,?,?,?,?,?)", (utc_now(), "C68_ABSTRACT_FUNCTION_TESTED_NO_PROSE", len(HYPOTHESES), accepted, 0, json.dumps(summary, ensure_ascii=False, sort_keys=True)))
    run_id = cur.lastrowid
    for item in items:
        conn.execute("insert into c68_semantic_function_hypothesis_v1_items values (?,?,?,?,?,?,?,?,?)", (run_id, *item))
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": "C68_ABSTRACT_FUNCTION_TESTED_NO_PROSE", "accepted_function_count": accepted, "accepted_functions": [i[0] for i in items if i[2] == "ACCEPT_ABSTRACT_FUNCTION_NO_PROSE"], "accepted_prose_gloss_count": 0}, ensure_ascii=False))

if __name__ == "__main__":
    main()
