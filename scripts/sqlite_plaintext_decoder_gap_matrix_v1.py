#!/usr/bin/env python3
"""Build missing-unit matrix for the next plaintext decoder attempt."""
from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def tokens(target: str):
    return [x for x in re.split(r"[ ;!,.]+", target.strip()) if x]


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.executescript("""
    create table if not exists plaintext_decoder_gap_matrix_v1_runs (
        run_id integer primary key autoincrement,
        created_at text not null,
        decision text not null,
        missing_external_unit_count integer not null,
        missing_internal_family_count integer not null,
        summary_json text not null
    );
    create table if not exists plaintext_decoder_gap_matrix_v1_items (
        run_id integer not null,
        gap_id text not null,
        gap_type text not null,
        target_unit text not null,
        required_capability text not null,
        current_blocker text not null,
        evidence_json text not null,
        primary key (run_id, gap_id)
    );
    """)
    latest_eval = conn.execute("select max(run_id) as run_id from plaintext_candidate_eval_v1_items").fetchone()["run_id"]
    failed = list(conn.execute("select * from plaintext_candidate_eval_v1_items where run_id=? and status='FAIL' order by benchmark_id", (latest_eval,)))
    known = {"3478", "67", "7223", "486486", "1", "0", "469"}
    items = []
    idx = 1
    for f in failed:
        if f["benchmark_type"] == "external_phrase":
            for t in tokens(f["target"]):
                if t not in known:
                    items.append((f"E{idx:03d}", "external_sequence_unit", t, "Assign plaintext or compositional parse that predicts the full external phrase.", f"Unknown in failed benchmark {f['benchmark_id']}", json.dumps(dict(f), ensure_ascii=False, sort_keys=True)))
                    idx += 1
        elif f["benchmark_type"] == "book_family":
            items.append((f"I{idx:03d}", "internal_family_semantics", f["target"], "Map functional frame family to stable human semantics across all listed books.", f"No semantic mapping for {f['benchmark_id']}", json.dumps(dict(f), ensure_ascii=False, sort_keys=True)))
            idx += 1
    ext_count = sum(1 for i in items if i[1] == "external_sequence_unit")
    int_count = sum(1 for i in items if i[1] == "internal_family_semantics")
    summary = {"source_eval_run": latest_eval, "principle": "next decoder must cover missing units compositionally, not by isolated guesses"}
    cur = conn.execute("insert into plaintext_decoder_gap_matrix_v1_runs values (null,?,?,?,?,?)", (utc_now(), "PLAINTEXT_DECODER_GAP_MATRIX_BUILT", ext_count, int_count, json.dumps(summary, ensure_ascii=False, sort_keys=True)))
    run_id = cur.lastrowid
    for item in items:
        conn.execute("insert into plaintext_decoder_gap_matrix_v1_items values (?,?,?,?,?,?,?)", (run_id, *item))
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": "PLAINTEXT_DECODER_GAP_MATRIX_BUILT", "missing_external_unit_count": ext_count, "missing_internal_family_count": int_count, "total_gap_units": len(items)}, ensure_ascii=False))

if __name__ == "__main__":
    main()
