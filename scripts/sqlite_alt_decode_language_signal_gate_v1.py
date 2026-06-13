#!/usr/bin/env python3
"""Audit alternate decoded_text strings for real language signal vs cipher artifact."""
from __future__ import annotations

import json
import math
import re
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
TARGETS = ("6", "7", "14", "32", "36", "41", "49")
COMMON_DE = {"DER", "DIE", "DAS", "UND", "DEN", "EIN", "EINE", "NICHT", "IST", "ICH", "SIE", "MIT", "AUF", "DEM", "DES", "WIR", "DU", "ER"}
COMMON_EN = {"THE", "AND", "ING", "ION", "ENT", "THAT", "WITH", "YOU", "NOT", "FOR", "HAVE"}
VOWELS = set("AEIOU")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def score_language(s: str):
    clean = re.sub(r"[^A-Z?]", "", s.upper())
    if not clean:
        return {"score": 0.0, "reason": "empty", "vowel_ratio": 0.0, "common_hits": []}
    trigrams = [clean[i:i+3] for i in range(len(clean)-2)]
    hits = sorted((COMMON_DE | COMMON_EN).intersection(trigrams))
    vowel_ratio = sum(1 for c in clean if c in VOWELS) / len(clean)
    q_penalty = clean.count("?") / len(clean)
    repeat_penalty = max((v / len(clean) for v in Counter(clean).values()), default=0)
    # Real language-ish only if common trigrams plus reasonable vowel balance and low unknowns.
    score = len(hits) * 8 + max(0, 20 - abs(vowel_ratio - 0.42) * 100) - q_penalty * 40 - repeat_penalty * 20
    return {"score": round(score, 3), "vowel_ratio": round(vowel_ratio, 3), "unknown_ratio": round(q_penalty, 3), "max_char_ratio": round(repeat_penalty, 3), "common_hits": hits}


def main() -> None:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.executescript("""
    create table if not exists alt_decode_language_signal_gate_v1_runs (
        run_id integer primary key autoincrement,
        created_at text not null,
        decision text not null,
        target_count integer not null,
        language_signal_count integer not null,
        rejected_artifact_count integer not null,
        accepted_prose_gloss_count integer not null,
        summary_json text not null
    );
    create table if not exists alt_decode_language_signal_gate_v1_items (
        run_id integer not null,
        bookid text not null,
        path_rank integer not null,
        signal_status text not null,
        language_score real not null,
        prose_gloss_allowed integer not null,
        reason text not null,
        decoded_text text not null,
        evidence_json text not null,
        primary key (run_id, bookid, path_rank)
    );
    """)
    items = []
    for bookid in TARGETS:
        paths = list(conn.execute("select * from row0_path_reconstruction_items where bookid=? order by run_id desc, path_rank", (bookid,)))
        if not paths:
            items.append((bookid, 0, "NO_ALT_DECODE_PATH", 0.0, 0, "No alternate decoded_text path exists for this book.", "", json.dumps({}, sort_keys=True)))
            continue
        for p in paths:
            sig = score_language(p["decoded_text"])
            if sig["score"] >= 35 and len(sig["common_hits"]) >= 3 and sig["unknown_ratio"] <= 0.02:
                status = "POSSIBLE_LANGUAGE_SIGNAL_HOLDOUT"
                reason = "Score is language-like, but still not accepted as translation without exact provenance or roundtrip prediction."
            else:
                status = "REJECT_LANGUAGE_ARTIFACT_NO_GLOSS"
                reason = "Decoded text lacks enough stable common trigrams/vowel/unknown profile; treat as artifact, not translation."
            items.append((bookid, int(p["path_rank"]), status, float(sig["score"]), 0, reason, p["decoded_text"], json.dumps({"path": dict(p), "language_signal": sig}, ensure_ascii=False, sort_keys=True)))
    signal_count = sum(1 for i in items if i[2] == "POSSIBLE_LANGUAGE_SIGNAL_HOLDOUT")
    rejected = sum(1 for i in items if i[2] == "REJECT_LANGUAGE_ARTIFACT_NO_GLOSS")
    summary = {"targets": list(TARGETS), "signal_count": signal_count, "rejected_artifact_count": rejected, "principle": "language-like alternate decodes are not glosses without provenance and prediction"}
    cur = conn.execute("insert into alt_decode_language_signal_gate_v1_runs (created_at,decision,target_count,language_signal_count,rejected_artifact_count,accepted_prose_gloss_count,summary_json) values (?,?,?,?,?,?,?)", (utc_now(), "ALT_DECODE_LANGUAGE_SIGNAL_AUDITED_NO_GLOSS", len(TARGETS), signal_count, rejected, 0, json.dumps(summary, ensure_ascii=False, sort_keys=True)))
    run_id = cur.lastrowid
    for item in items:
        conn.execute("insert into alt_decode_language_signal_gate_v1_items values (?,?,?,?,?,?,?,?,?)", (run_id, *item))
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": "ALT_DECODE_LANGUAGE_SIGNAL_AUDITED_NO_GLOSS", "language_signal_count": signal_count, "rejected_artifact_count": rejected, "accepted_prose_gloss_count": 0, "top_items": sorted([{"bookid": i[0], "path_rank": i[1], "status": i[2], "score": i[3], "decoded_text": i[6][:80]} for i in items], key=lambda x: x["score"], reverse=True)[:8]}, ensure_ascii=False))

if __name__ == "__main__":
    main()
