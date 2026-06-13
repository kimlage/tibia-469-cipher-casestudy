#!/usr/bin/env python3
"""Test book14 as R02-prefixed LTAST boundary fragment against accepted LTAST frames."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

SUPPORT = ("0", "9", "10", "33", "35", "66")
TARGET = "14"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def has_seq(tokens, seq):
    n = len(seq)
    return any(tokens[i:i+n] == seq for i in range(len(tokens) - n + 1))


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


def main() -> None:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.executescript("""
    create table if not exists r02_ltast_boundary_gate_v1_runs (
        run_id integer primary key autoincrement,
        created_at text not null,
        decision text not null,
        promoted_count integer not null,
        accepted_prose_gloss_count integer not null,
        summary_json text not null
    );
    create table if not exists r02_ltast_boundary_gate_v1_items (
        run_id integer not null,
        bookid text not null,
        gate_status text not null,
        proposed_label text not null,
        promotion_allowed integer not null,
        prose_gloss_allowed integer not null,
        best_support_book text not null,
        best_lcs_len integer not null,
        reason text not null,
        next_action text not null,
        evidence_json text not null,
        primary key (run_id, bookid)
    );
    """)
    target = conn.execute("select * from row0_variant_book_tokens where bookid=?", (TARGET,)).fetchone()
    ttoks = json.loads(target["tokens_json"])
    support_rows = list(conn.execute("select * from row0_variant_book_tokens where bookid in (%s)" % ",".join("?" for _ in SUPPORT), SUPPORT))
    comparisons = []
    for row in support_rows:
        common = lcs(target["symbol_text"], row["symbol_text"])
        comparisons.append({"bookid": row["bookid"], "lcs_len": len(common), "lcs_text": common})
    comparisons.sort(key=lambda x: x["lcs_len"], reverse=True)
    best = comparisons[0]
    has_r02 = "R02" in ttoks
    has_ltast = "LTAST" in ttoks
    has_zero_ltast = has_seq(ttoks, ["*00", "L", "T", "A", "S", "T"])
    has_vna_zero = has_seq(ttoks, ["*00", "V", "N", "A"])
    if has_r02 and has_ltast and has_zero_ltast and has_vna_zero and best["lcs_len"] >= 18:
        status = "PROMOTE_R02_LTAST_BOUNDARY_FRAGMENT_NO_GLOSS"
        label = "R02_PREFACED_LTAST_BOUNDARY_FRAGMENT"
        promote = 1
        reason = "Book14 has R02 prefix plus two typed zero exits into VNA and LTAST, matching accepted LTAST boundary mechanics without claiming prose."
        next_action = "Promote as related structural boundary only; do not promote R02 semantics or LTAST gloss."
    else:
        status = "HOLD_R02_LTAST_BOUNDARY_WEAK"
        label = "R02_LTAST_AUDIT"
        promote = 0
        reason = "R02/LTAST evidence does not clear structural boundary gate."
        next_action = "Hold."
    evidence = {"target_tokens": ttoks, "comparisons": comparisons, "has_r02": has_r02, "has_ltast": has_ltast, "has_zero_ltast": has_zero_ltast, "has_vna_zero": has_vna_zero}
    cur = conn.execute("insert into r02_ltast_boundary_gate_v1_runs (created_at,decision,promoted_count,accepted_prose_gloss_count,summary_json) values (?,?,?,?,?)", (utc_now(), "R02_LTAST_BOUNDARY_STRUCTURAL_GATE_NO_GLOSS", promote, 0, json.dumps({"target": TARGET, "promoted": bool(promote), "principle": "boundary only"}, ensure_ascii=False, sort_keys=True)))
    run_id = cur.lastrowid
    conn.execute("insert into r02_ltast_boundary_gate_v1_items values (?,?,?,?,?,?,?,?,?,?,?)", (run_id, TARGET, status, label, promote, 0, best["bookid"], best["lcs_len"], reason, next_action, json.dumps(evidence, ensure_ascii=False, sort_keys=True)))
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": "R02_LTAST_BOUNDARY_STRUCTURAL_GATE_NO_GLOSS", "promoted_count": promote, "bookid": TARGET, "status": status, "best_support_book": best["bookid"], "best_lcs_len": best["lcs_len"], "accepted_prose_gloss_count": 0}, ensure_ascii=False))

if __name__ == "__main__":
    main()
