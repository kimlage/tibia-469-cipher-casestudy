#!/usr/bin/env python3
"""Register and smoke-test the mathemagic four-key hypothesis: 1,13,49,94."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
KEYS = [1, 13, 49, 94]
SEQUENCES = {
    "POLL_C": [663, 902073, 7223, 67538, 467, 80097],
    "KNIGHTMARE": [3478, 67, 90871, 97664, 3466, 0, 345],
}


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def dsum(n: int) -> int:
    return sum(int(c) for c in str(abs(n)))


def dr(n: int) -> int:
    s = dsum(n)
    while s >= 10:
        s = dsum(s)
    return s


def transform(seq, key, mode):
    if mode == "mod_key":
        return [n % key if key else None for n in seq]
    if mode == "digit_sum_times_key_root":
        return [dr(dsum(n) * key) for n in seq]
    if mode == "plus_key_digit_root":
        return [dr(n + key) for n in seq]
    if mode == "times_key_digit_root":
        return [dr(n * key) for n in seq]
    raise ValueError(mode)


def main():
    conn = sqlite3.connect(DB)
    conn.executescript("""
    create table if not exists mathemagic_four_key_hypothesis_v1_runs (
        run_id integer primary key autoincrement,
        created_at text not null,
        decision text not null,
        key_count integer not null,
        transform_count integer not null,
        candidate_pass_count integer not null,
        accepted_plaintext_count integer not null,
        summary_json text not null
    );
    create table if not exists mathemagic_four_key_hypothesis_v1_items (
        run_id integer not null,
        sequence_id text not null,
        key_value integer not null,
        transform_mode text not null,
        output_json text not null,
        test_status text not null,
        reason text not null,
        evidence_json text not null,
        primary key (run_id, sequence_id, key_value, transform_mode)
    );
    """)
    modes = ["mod_key", "digit_sum_times_key_root", "plus_key_digit_root", "times_key_digit_root"]
    items = []
    for sid, seq in SEQUENCES.items():
        for key in KEYS:
            for mode in modes:
                out = transform(seq, key, mode)
                # Smoke-test only: a useful key should produce structured non-constant output and explain known scoped hints.
                unique = len(set(out)) if out else 0
                if mode == "mod_key" and key == 1:
                    status = "REJECT_DEGENERATE_ALL_ZERO"
                    reason = "Modulo 1 destroys all information."
                elif unique <= 2:
                    status = "REJECT_LOW_INFORMATION"
                    reason = "Output has too little variation to act as decoder key."
                elif mode.endswith("digit_root") and all(1 <= x <= 9 for x in out):
                    status = "HOLD_NUMERIC_FEATURE_ONLY"
                    reason = "Produces bounded numeric features, but no mapping to plaintext or benchmark pass."
                else:
                    status = "HOLD_UNINTERPRETED_TRANSFORM"
                    reason = "Transform preserves variation but has no accepted semantic mapping."
                items.append((sid, key, mode, json.dumps(out), status, reason, json.dumps({"input": seq, "keys": KEYS}, ensure_ascii=False, sort_keys=True)))
    pass_count = sum(1 for i in items if i[4].startswith("PASS"))
    summary = {
        "keys": KEYS,
        "sources": {
            "paradox_tower_mathemagic": "1+1 result reported as 1,13,49,94 in Tibia/Paradox Tower sources",
            "poll_c": "15.04.2020 poll option C external 469 sequence",
        },
        "principle": "four keys are hypothesis features, not plaintext",
    }
    cur = conn.execute("insert into mathemagic_four_key_hypothesis_v1_runs values (null,?,?,?,?,?,?,?)", (utc_now(), "MATHEMAGIC_FOUR_KEYS_SMOKE_TESTED_NO_PLAINTEXT", len(KEYS), len(items), pass_count, 0, json.dumps(summary, ensure_ascii=False, sort_keys=True)))
    run_id = cur.lastrowid
    for item in items:
        conn.execute("insert into mathemagic_four_key_hypothesis_v1_items values (?,?,?,?,?,?,?,?)", (run_id, *item))
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": "MATHEMAGIC_FOUR_KEYS_SMOKE_TESTED_NO_PLAINTEXT", "key_count": len(KEYS), "transform_count": len(items), "candidate_pass_count": pass_count, "accepted_plaintext_count": 0}, ensure_ascii=False))

if __name__ == "__main__":
    main()
