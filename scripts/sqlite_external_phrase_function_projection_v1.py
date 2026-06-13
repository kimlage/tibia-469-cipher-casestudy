#!/usr/bin/env python3
"""Project external numeric phrases onto current functional frame vocabulary without accepting plaintext."""
from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
PHRASES = [
    ("KNIGHTMARE_PHRASE", "3478 67 90871 97664 3466 0 345"),
    ("CHAYENNE_REPLY_A", "114514519485611451908304576512282177"),
    ("CHAYENNE_REPLY_B", "6612527570584"),
    ("POLL_SEQUENCE", "663 902073 7223 67538 467 80097"),
]


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def split_codes(raw: str):
    return [x for x in re.split(r"[ ;]+", raw.strip()) if x]


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.executescript("""
    create table if not exists external_phrase_function_projection_v1_runs (
        run_id integer primary key autoincrement,
        created_at text not null,
        decision text not null,
        phrase_count integer not null,
        in_corpus_projection_count integer not null,
        accepted_plaintext_count integer not null,
        summary_json text not null
    );
    create table if not exists external_phrase_function_projection_v1_items (
        run_id integer not null,
        phrase_id text not null,
        raw_sequence text not null,
        projection_status text not null,
        known_unit_count integer not null,
        unknown_unit_count integer not null,
        projected_units_json text not null,
        prose_gloss_allowed integer not null,
        reason text not null,
        evidence_json text not null,
        primary key (run_id, phrase_id)
    );
    """)
    # Known external scoped/audit units from minimal lexicon, plus current benchmark weak baseline.
    lex = {}
    for r in conn.execute("select * from minimal_external_semantic_lexicon_v1_items"):
        seq = r["sequence"] if "sequence" in r.keys() else r[2]
        val = r["value"] if "value" in r.keys() else r[3]
        tier = r["tier"] if "tier" in r.keys() else r[5]
        lex[str(seq)] = {"value": val, "tier": tier, "source": "minimal_external_semantic_lexicon"}
    lex.update({"486486": {"value": "WRINKLED_BONELORD_SELF_NAME", "tier": "SCOPED_LORE"}, "1": {"value": "TIBIA", "tier": "SCOPED_LORE"}, "0": {"value": "OBSCENE_NUMBER", "tier": "SCOPED_LORE"}, "469": {"value": "BONELORD_LANGUAGE", "tier": "SCOPED_LORE"}})
    items = []
    for pid, raw in PHRASES:
        units = split_codes(raw)
        projected = []
        known = 0
        for u in units:
            if u in lex:
                known += 1
                projected.append({"unit": u, "status": "KNOWN_SCOPED_OR_AUDIT", **lex[u]})
            else:
                projected.append({"unit": u, "status": "UNKNOWN_NO_FUNCTION_PROJECTION"})
        unknown = len(units) - known
        if unknown == 0 and units:
            status = "FULLY_PROJECTED_BUT_NOT_PLAINTEXT"
            reason = "All units have scoped/audit projection, but not human plaintext or book function."
            in_corpus = 1
        elif known > 0:
            status = "PARTIAL_EXTERNAL_PROJECTION_ONLY"
            reason = "Some units project to scoped/audit hints, but unknown units block functional/plaintext interpretation."
            in_corpus = 0
        else:
            status = "NO_FUNCTION_PROJECTION"
            reason = "No units project to accepted functional/plaintext vocabulary."
            in_corpus = 0
        items.append((pid, raw, status, known, unknown, json.dumps(projected, ensure_ascii=False, sort_keys=True), 0, reason, json.dumps({"units": units, "lexicon_hits": projected}, ensure_ascii=False, sort_keys=True), in_corpus))
    in_count = sum(i[-1] for i in items)
    summary = {"phrases": [p[0] for p in PHRASES], "principle": "external projection can support C4 only if it predicts full phrase, not partial hints"}
    cur = conn.execute("insert into external_phrase_function_projection_v1_runs values (null,?,?,?,?,?,?)", (utc_now(), "EXTERNAL_PHRASE_FUNCTION_PROJECTION_NO_PLAINTEXT", len(items), in_count, 0, json.dumps(summary, ensure_ascii=False, sort_keys=True)))
    run_id = cur.lastrowid
    for item in items:
        conn.execute("insert into external_phrase_function_projection_v1_items values (?,?,?,?,?,?,?,?,?,?)", (run_id, *item[:-1]))
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": "EXTERNAL_PHRASE_FUNCTION_PROJECTION_NO_PLAINTEXT", "phrase_count": len(items), "in_corpus_projection_count": in_count, "accepted_plaintext_count": 0, "items": [{"phrase_id": i[0], "status": i[2], "known": i[3], "unknown": i[4]} for i in items]}, ensure_ascii=False))

if __name__ == "__main__":
    main()
