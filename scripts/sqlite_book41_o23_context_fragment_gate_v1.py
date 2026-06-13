#!/usr/bin/env python3
"""Test book41 as O23-bearing context fragment without O23 promotion."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
TARGET = "41"
ANCHORS = ("10", "35", "13", "38", "56", "24")


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def lcs(a: str, b: str) -> str:
    prev = [0] * (len(b) + 1)
    best = (0, 0)
    for i, ca in enumerate(a, 1):
        cur = [0] * (len(b) + 1)
        for j, cb in enumerate(b, 1):
            if ca == cb:
                cur[j] = prev[j-1] + 1
                if cur[j] > best[0]:
                    best = (cur[j], i)
        prev = cur
    return a[best[1]-best[0]:best[1]]


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.executescript("""
    create table if not exists book41_o23_context_fragment_gate_v1_runs (
        run_id integer primary key autoincrement,
        created_at text not null,
        decision text not null,
        promoted_count integer not null,
        accepted_prose_gloss_count integer not null,
        summary_json text not null
    );
    create table if not exists book41_o23_context_fragment_gate_v1_items (
        run_id integer not null,
        bookid text not null,
        gate_status text not null,
        proposed_label text not null,
        promotion_allowed integer not null,
        prose_gloss_allowed integer not null,
        best_anchor text not null,
        best_lcs_len integer not null,
        reason text not null,
        next_action text not null,
        evidence_json text not null,
        primary key (run_id, bookid)
    );
    """)
    t = conn.execute("select * from row0_variant_book_tokens where bookid=?", (TARGET,)).fetchone()
    ttoks = json.loads(t["tokens_json"])
    rows = list(conn.execute("select * from row0_variant_book_tokens where bookid in (%s)" % ",".join("?" for _ in ANCHORS), ANCHORS))
    comps = []
    for r in rows:
        common = lcs(t["symbol_text"], r["symbol_text"])
        comps.append({"bookid": r["bookid"], "lcs_len": len(common), "lcs_text": common})
    comps.sort(key=lambda x: x["lcs_len"], reverse=True)
    best = comps[0]
    has_o23 = "O23" in ttoks
    context_like = "L" in ttoks and "F" in ttoks and "S" in ttoks and "T" in ttoks
    if has_o23 and best["lcs_len"] >= 24 and best["bookid"] in ("10", "35", "24"):
        status = "PROMOTE_O23_CONTEXT_FRAGMENT_NO_GLOSS"
        label = "O23_BEARING_CONTEXT_FRAGMENT_CONTROL"
        promote = 1
        reason = "Book41 carries O23 inside a broader context fragment; promote as guarded context control, not O23 endpoint or lexical gloss."
        next_action = "Do not use as O23 family member; use as context-fragment control."
    else:
        status = "HOLD_O23_CONTEXT_FRAGMENT_WEAK"
        label = "O23_CONTEXT_FRAGMENT_AUDIT"
        promote = 0
        reason = "O23/context evidence remains below guarded fragment gate."
        next_action = "Hold until new contrast."
    evidence = {"tokens": ttoks, "comparisons": comps, "has_o23": has_o23, "context_like": context_like}
    cur = conn.execute("insert into book41_o23_context_fragment_gate_v1_runs values (null,?,?,?,?,?)", (utc_now(), "BOOK41_O23_CONTEXT_FRAGMENT_GATE_NO_GLOSS", promote, 0, json.dumps({"target": TARGET, "promoted": bool(promote)}, ensure_ascii=False, sort_keys=True)))
    run_id = cur.lastrowid
    conn.execute("insert into book41_o23_context_fragment_gate_v1_items values (?,?,?,?,?,?,?,?,?,?,?)", (run_id, TARGET, status, label, promote, 0, best["bookid"], best["lcs_len"], reason, next_action, json.dumps(evidence, ensure_ascii=False, sort_keys=True)))
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": "BOOK41_O23_CONTEXT_FRAGMENT_GATE_NO_GLOSS", "promoted_count": promote, "status": status, "best_anchor": best["bookid"], "best_lcs_len": best["lcs_len"], "accepted_prose_gloss_count": 0}, ensure_ascii=False))

if __name__ == "__main__":
    main()
