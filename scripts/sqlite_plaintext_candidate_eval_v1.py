#!/usr/bin/env python3
"""Evaluate plaintext decoder candidates against the acceptance benchmark."""
from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

# Candidate intentionally limited to already-known weak/scoped hints.
# It should fail; the purpose is an auditable baseline for future candidates.
CANDIDATE_ID = "baseline_scoped_hint_decoder_v1"
CANDIDATE_DESC = "Uses only currently known scoped/audit hints; expected to fail plaintext acceptance."
WEAK_WORDS = {
    "3478": "BE",
    "67": "A",
    "7223": "SO",
}
LORE_ANCHORS = {
    "486486": "WRINKLED_BONELORD_SELF_NAME",
    "1": "TIBIA_SCOPE_ANCHOR",
    "0": "OBSCENE_NUMBER_SCOPE_ANCHOR",
    "469": "BONELORD_LANGUAGE_SCOPE_ANCHOR",
}


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def decode_sequence(seq: str) -> str:
    parts = re.split(r"([ ;!,.]+)", seq.strip())
    out = []
    for p in parts:
        if not p or re.fullmatch(r"[ ;!,.]+", p):
            out.append(p)
        elif p in WEAK_WORDS:
            out.append(WEAK_WORDS[p])
        elif p in LORE_ANCHORS:
            out.append(f"<{LORE_ANCHORS[p]}>")
        else:
            out.append(f"<UNK:{p}>")
    return "".join(out)


def eval_benchmark(row: sqlite3.Row):
    bid = row["benchmark_id"]
    target = row["target"]
    btype = row["benchmark_type"]
    decoded = decode_sequence(target) if btype == "external_phrase" else "<NO_BOOK_PROSE_DECODER>"
    if btype == "external_phrase":
        unknown_count = decoded.count("<UNK:")
        if unknown_count == 0 and "<" not in decoded:
            status = "PASS"
            reason = "External phrase decoded without unknowns or scoped placeholders."
        else:
            status = "FAIL"
            reason = "External phrase still contains unknowns/scoped placeholders; not plaintext."
    elif btype == "negative_control":
        status = "PASS"
        reason = "Candidate does not hallucinate payload for negative controls."
    else:
        status = "FAIL"
        reason = "Candidate provides no book-family semantic mapping."
    return status, decoded, reason


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.executescript("""
    create table if not exists plaintext_candidate_eval_v1_runs (
        run_id integer primary key autoincrement,
        created_at text not null,
        candidate_id text not null,
        candidate_description text not null,
        decision text not null,
        benchmark_count integer not null,
        passed_count integer not null,
        failed_count integer not null,
        accepted_prose_gloss_count integer not null,
        summary_json text not null
    );
    create table if not exists plaintext_candidate_eval_v1_items (
        run_id integer not null,
        candidate_id text not null,
        benchmark_id text not null,
        benchmark_type text not null,
        target text not null,
        status text not null,
        decoded_output text not null,
        reason text not null,
        evidence_json text not null,
        primary key (run_id, candidate_id, benchmark_id)
    );
    """)
    latest_bench = conn.execute("select max(run_id) as run_id from plaintext_prediction_benchmark_v1_items").fetchone()["run_id"]
    benches = list(conn.execute("select * from plaintext_prediction_benchmark_v1_items where run_id=? order by benchmark_id", (latest_bench,)))
    results = []
    for b in benches:
        status, decoded, reason = eval_benchmark(b)
        results.append((b, status, decoded, reason))
    passed = sum(1 for _, st, _, _ in results if st == "PASS")
    failed = len(results) - passed
    decision = "CANDIDATE_REJECTED_NO_PLAINTEXT" if failed else "CANDIDATE_ACCEPTED"
    summary = {
        "weak_words": WEAK_WORDS,
        "lore_anchors": LORE_ANCHORS,
        "pass_rate": f"{passed}/{len(results)}",
        "principle": "scoped/audit hints cannot become prose without benchmark coverage",
    }
    cur = conn.execute(
        "insert into plaintext_candidate_eval_v1_runs values (null,?,?,?,?,?,?,?,?,?)",
        (utc_now(), CANDIDATE_ID, CANDIDATE_DESC, decision, len(results), passed, failed, 0, json.dumps(summary, ensure_ascii=False, sort_keys=True)),
    )
    run_id = cur.lastrowid
    for b, status, decoded, reason in results:
        conn.execute(
            "insert into plaintext_candidate_eval_v1_items values (?,?,?,?,?,?,?,?,?)",
            (run_id, CANDIDATE_ID, b["benchmark_id"], b["benchmark_type"], b["target"], status, decoded, reason, json.dumps(dict(b), ensure_ascii=False, sort_keys=True)),
        )
    conn.commit()
    print(json.dumps({"run_id": run_id, "candidate_id": CANDIDATE_ID, "decision": decision, "benchmark_count": len(results), "passed_count": passed, "failed_count": failed, "accepted_prose_gloss_count": 0, "failed_benchmarks": [b["benchmark_id"] for b, st, _, _ in results if st == "FAIL"]}, ensure_ascii=False))

if __name__ == "__main__":
    main()
