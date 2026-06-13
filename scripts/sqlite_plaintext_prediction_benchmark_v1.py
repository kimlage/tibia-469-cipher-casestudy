#!/usr/bin/env python3
"""Create a benchmark contract for accepting future human plaintext translations."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

BENCHMARKS = [
    ("B1_KNIGHTMARE_PHRASE", "external_phrase", "3478 67 90871 97664 3466 0 345", "Must predict a coherent plaintext for the exact phrase and explain why TibiaWiki/Knightmare provenance lacks explicit meaning.", "hard_holdout"),
    ("B2_CHAYENNE_REPLY", "external_phrase", "114514519485611451908304576512282177;6612527570584", "Must produce stable parse/plaintext for Chayenne sequence without using speculative fan mapping.", "hard_holdout"),
    ("B3_POLL_SEQUENCE", "external_phrase", "663 902073 7223 67538 467 80097", "Must decode poll sequence and match independent context if any is found.", "hard_holdout"),
    ("B4_BENNA_LTAST_BOOKS", "book_family", "0,9,10,33,35,66", "Plaintext must assign consistent semantics to BENNA/LTAST/handoff frames across all support books.", "internal_consistency"),
    ("B5_C68_DUAL_SUBFRAMES", "book_family", "2,8,19,23,24,27,57,67", "Plaintext must preserve C68 VN/TIIN vs FAT/TIV subframe distinction.", "internal_consistency"),
    ("B6_DISPLAY_CONTROLS", "negative_control", "6,32,36", "Plaintext must not hallucinate payload where display-tail/control gates found none.", "negative_control"),
    ("B7_O32_CONTROL", "negative_control", "49", "Plaintext must preserve O32 as singleton control and not merge with O23.", "negative_control"),
]


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main():
    conn = sqlite3.connect(DB)
    conn.executescript("""
    create table if not exists plaintext_prediction_benchmark_v1_runs (
        run_id integer primary key autoincrement,
        created_at text not null,
        decision text not null,
        benchmark_count integer not null,
        passing_decoder_count integer not null,
        accepted_prose_gloss_count integer not null,
        summary_json text not null
    );
    create table if not exists plaintext_prediction_benchmark_v1_items (
        run_id integer not null,
        benchmark_id text not null,
        benchmark_type text not null,
        target text not null,
        acceptance_requirement text not null,
        benchmark_tier text not null,
        current_status text not null,
        evidence_json text not null,
        primary key (run_id, benchmark_id)
    );
    """)
    summary = {"purpose": "future plaintext candidate must pass these before any prose gloss is accepted", "current_passing_decoder_count": 0}
    cur = conn.execute("insert into plaintext_prediction_benchmark_v1_runs values (null,?,?,?,?,?,?)", (utc_now(), "PLAINTEXT_ACCEPTANCE_BENCHMARK_CREATED_NO_DECODER_PASSES", len(BENCHMARKS), 0, 0, json.dumps(summary, ensure_ascii=False, sort_keys=True)))
    run_id = cur.lastrowid
    for bid, btype, target, req, tier in BENCHMARKS:
        conn.execute("insert into plaintext_prediction_benchmark_v1_items values (?,?,?,?,?,?,?,?)", (run_id, bid, btype, target, req, tier, "OPEN_NO_DECODER_PASSES", json.dumps({"source": "current structural/semantic audit"}, ensure_ascii=False, sort_keys=True)))
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": "PLAINTEXT_ACCEPTANCE_BENCHMARK_CREATED_NO_DECODER_PASSES", "benchmark_count": len(BENCHMARKS), "passing_decoder_count": 0, "accepted_prose_gloss_count": 0}, ensure_ascii=False))

if __name__ == "__main__":
    main()
