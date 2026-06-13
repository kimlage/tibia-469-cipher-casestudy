#!/usr/bin/env python3
"""Null-control validation for possible language-like alternate decodes."""
from __future__ import annotations

import json
import random
import re
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
COMMON = {"DER", "DIE", "DAS", "UND", "DEN", "EIN", "EIN", "ICH", "SIE", "MIT", "THE", "AND", "ING", "ION", "ENT", "EST", "SCH", "END"}
VOWELS = set("AEIOU")


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def score(s: str) -> float:
    clean = re.sub(r"[^A-Z?]", "", s.upper())
    if not clean:
        return 0.0
    trigrams = [clean[i:i+3] for i in range(len(clean)-2)]
    hits = len(COMMON.intersection(trigrams))
    vowel_ratio = sum(1 for c in clean if c in VOWELS) / len(clean)
    q = clean.count("?") / len(clean)
    repeat = max(Counter(clean).values()) / len(clean)
    return round(hits * 8 + max(0, 20 - abs(vowel_ratio - 0.42) * 100) - q * 40 - repeat * 20, 3)


def shuffled_scores(text: str, n=100):
    chars = list(text)
    out = []
    for seed in range(n):
        rng = random.Random(seed)
        tmp = chars[:]
        rng.shuffle(tmp)
        out.append(score("".join(tmp)))
    return out


def pct_rank(value, population):
    if not population:
        return 1.0
    return sum(1 for x in population if x <= value) / len(population)


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.executescript("""
    create table if not exists alt_decode_null_control_v1_runs (
        run_id integer primary key autoincrement,
        created_at text not null,
        decision text not null,
        candidate_count integer not null,
        survives_null_count integer not null,
        accepted_prose_gloss_count integer not null,
        summary_json text not null
    );
    create table if not exists alt_decode_null_control_v1_items (
        run_id integer not null,
        bookid text not null,
        path_rank integer not null,
        null_status text not null,
        language_score real not null,
        corpus_percentile real not null,
        shuffle_percentile real not null,
        prose_gloss_allowed integer not null,
        reason text not null,
        evidence_json text not null,
        primary key (run_id, bookid, path_rank)
    );
    """)
    all_paths = list(conn.execute("select bookid,path_rank,decoded_text from row0_path_reconstruction_items"))
    corpus_scores = [score(r["decoded_text"]) for r in all_paths if r["decoded_text"]]
    candidates = list(conn.execute("select * from alt_decode_language_signal_gate_v1_items where run_id=(select max(run_id) from alt_decode_language_signal_gate_v1_items) and signal_status='POSSIBLE_LANGUAGE_SIGNAL_HOLDOUT'"))
    items = []
    for c in candidates:
        s = float(c["language_score"])
        sh = shuffled_scores(c["decoded_text"])
        cp = pct_rank(s, corpus_scores)
        sp = pct_rank(s, sh)
        if cp >= 0.85 and sp >= 0.95:
            status = "SURVIVES_NULL_AS_LANGUAGE_LIKE_HOLDOUT"
            reason = "Decode is high relative to corpus and deterministic shuffles, but still lacks provenance/predictive translation; holdout only."
        else:
            status = "REJECT_NULL_NOT_DISTINCT_ENOUGH"
            reason = "Decode does not separate strongly enough from corpus/shuffle baseline."
        evidence = {"candidate": dict(c), "corpus_scores": corpus_scores, "shuffle_scores": sh, "corpus_percentile": cp, "shuffle_percentile": sp}
        items.append((c["bookid"], int(c["path_rank"]), status, s, round(cp, 3), round(sp, 3), 0, reason, json.dumps(evidence, ensure_ascii=False, sort_keys=True)))
    survives = sum(1 for i in items if i[2] == "SURVIVES_NULL_AS_LANGUAGE_LIKE_HOLDOUT")
    summary = {"candidate_count": len(items), "survives_null_count": survives, "principle": "surviving language-like text is a research holdout, not accepted translation"}
    cur = conn.execute("insert into alt_decode_null_control_v1_runs (created_at,decision,candidate_count,survives_null_count,accepted_prose_gloss_count,summary_json) values (?,?,?,?,?,?)", (utc_now(), "ALT_DECODE_NULL_CONTROL_COMPLETED_NO_GLOSS", len(items), survives, 0, json.dumps(summary, ensure_ascii=False, sort_keys=True)))
    run_id = cur.lastrowid
    for item in items:
        conn.execute("insert into alt_decode_null_control_v1_items values (?,?,?,?,?,?,?,?,?,?)", (run_id, *item))
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": "ALT_DECODE_NULL_CONTROL_COMPLETED_NO_GLOSS", "candidate_count": len(items), "survives_null_count": survives, "accepted_prose_gloss_count": 0, "items": [{"bookid": i[0], "path_rank": i[1], "status": i[2], "score": i[3], "corpus_percentile": i[4], "shuffle_percentile": i[5]} for i in items]}, ensure_ascii=False))

if __name__ == "__main__":
    main()
