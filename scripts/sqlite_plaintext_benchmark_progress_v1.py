#!/usr/bin/env python3
"""Track partial progress on plaintext benchmarks without accepting prose."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.executescript("""
    create table if not exists plaintext_benchmark_progress_v1_runs (
        run_id integer primary key autoincrement,
        created_at text not null,
        decision text not null,
        benchmark_count integer not null,
        partial_count integer not null,
        passed_plaintext_count integer not null,
        summary_json text not null
    );
    create table if not exists plaintext_benchmark_progress_v1_items (
        run_id integer not null,
        benchmark_id text not null,
        progress_status text not null,
        plaintext_passed integer not null,
        partial_evidence text not null,
        missing_for_plaintext text not null,
        evidence_json text not null,
        primary key (run_id, benchmark_id)
    );
    """)
    latest_bench = conn.execute("select max(run_id) as run_id from plaintext_prediction_benchmark_v1_items").fetchone()["run_id"]
    benches = list(conn.execute("select * from plaintext_prediction_benchmark_v1_items where run_id=? order by benchmark_id", (latest_bench,)))
    benna = conn.execute("select * from benna_ltast_semantic_function_hypothesis_v1_runs order by run_id desc limit 1").fetchone()
    items = []
    for b in benches:
        bid = b["benchmark_id"]
        if bid == "B4_BENNA_LTAST_BOOKS" and benna and int(benna["accepted_function_count"]) > 0:
            status = "PARTIAL_ABSTRACT_FUNCTION_ACCEPTED_NO_PROSE"
            partial = "BENNA/LTAST accepted as abstract handoff/continuation function."
            missing = "Need human-readable semantics that predicts books and external phrases without contradiction."
        else:
            status = "OPEN_NO_PLAINTEXT_PROGRESS"
            partial = "No accepted plaintext progress."
            missing = b["acceptance_requirement"]
        items.append((bid, status, 0, partial, missing, json.dumps(dict(b), ensure_ascii=False, sort_keys=True)))
    partial_count = sum(1 for i in items if i[1].startswith("PARTIAL"))
    summary = {"partial_benchmarks": [i[0] for i in items if i[1].startswith("PARTIAL")], "passed_plaintext_count": 0}
    cur = conn.execute("insert into plaintext_benchmark_progress_v1_runs values (null,?,?,?,?,?,?)", (utc_now(), "PLAINTEXT_BENCHMARK_PROGRESS_UPDATED_NO_PROSE", len(items), partial_count, 0, json.dumps(summary, ensure_ascii=False, sort_keys=True)))
    run_id = cur.lastrowid
    for item in items:
        conn.execute("insert into plaintext_benchmark_progress_v1_items values (?,?,?,?,?,?,?)", (run_id, *item))
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": "PLAINTEXT_BENCHMARK_PROGRESS_UPDATED_NO_PROSE", "partial_count": partial_count, "passed_plaintext_count": 0, "partial_benchmarks": [i[0] for i in items if i[1].startswith("PARTIAL")]}, ensure_ascii=False))

if __name__ == "__main__":
    main()
