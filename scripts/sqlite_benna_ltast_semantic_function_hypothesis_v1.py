#!/usr/bin/env python3
"""Test abstract semantic-function hypotheses for BENNA/LTAST family without human gloss."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
BOOKS = ("0", "9", "10", "33", "35", "66")
HYPOTHESES = [
    ("H_BENNA_LTAST_INVOCATION", "BENNA/LTAST is an invocation or ritual opening frame."),
    ("H_BENNA_LTAST_HANDOFF", "BENNA/LTAST is a handoff/continuation operator into following context."),
    ("H_BENNA_LTAST_DISPLAY", "BENNA/LTAST is display/formula surface with no semantic payload."),
    ("H_BENNA_LTAST_DIRECTIONAL_CONTEXT", "BENNA/LTAST marks direction/transition in a context chain."),
]


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def features(text: str):
    return {
        "has_benna": "BENNA" in text,
        "has_ltast": "LTAST" in text,
        "has_aniv_tail": "ANIV" in text,
        "has_vnctiin": "VNCTIIN" in text,
        "has_naese": "NAESE" in text,
        "zero_count": text.count("*"),
        "length": len(text),
    }


def score_hypothesis(hid: str, feats):
    vals = list(feats.values())
    if hid == "H_BENNA_LTAST_HANDOFF":
        # Strong if most instances have LTAST + ANIV tail or context continuation.
        return sum(1 for f in vals if f["has_ltast"] and (f["has_aniv_tail"] or f["has_vnctiin"]))
    if hid == "H_BENNA_LTAST_DISPLAY":
        # Penalize because some instances connect to handoff/context and are not pure display.
        return sum(1 for f in vals if f["has_benna"] and f["has_ltast"] and not f["has_vnctiin"])
    if hid == "H_BENNA_LTAST_INVOCATION":
        return sum(1 for f in vals if f["has_benna"] and f["has_ltast"])
    if hid == "H_BENNA_LTAST_DIRECTIONAL_CONTEXT":
        return sum(1 for f in vals if f["has_ltast"] and f["zero_count"] >= 2)
    return 0


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.executescript("""
    create table if not exists benna_ltast_semantic_function_hypothesis_v1_runs (
        run_id integer primary key autoincrement,
        created_at text not null,
        decision text not null,
        hypothesis_count integer not null,
        accepted_function_count integer not null,
        accepted_prose_gloss_count integer not null,
        summary_json text not null
    );
    create table if not exists benna_ltast_semantic_function_hypothesis_v1_items (
        run_id integer not null,
        hypothesis_id text not null,
        hypothesis text not null,
        status text not null,
        support_score integer not null,
        support_total integer not null,
        prose_gloss_allowed integer not null,
        reason text not null,
        evidence_json text not null,
        primary key (run_id, hypothesis_id)
    );
    """)
    rows = list(conn.execute("select bookid, symbol_text from row0_variant_book_tokens where bookid in (%s)" % ",".join("?" for _ in BOOKS), BOOKS))
    feats = {r["bookid"]: features(r["symbol_text"]) for r in rows}
    items = []
    for hid, hyp in HYPOTHESES:
        sc = score_hypothesis(hid, feats)
        total = len(BOOKS)
        if hid == "H_BENNA_LTAST_HANDOFF" and sc >= 4:
            status = "ACCEPT_ABSTRACT_FUNCTION_NO_PROSE"
            reason = "Most support books use LTAST with ANIV/VNCTIIN continuation; abstract handoff function is defensible, but not plaintext."
        elif hid == "H_BENNA_LTAST_INVOCATION" and sc == total:
            status = "HOLD_TOO_BROAD_FORMULA_LABEL"
            reason = "Broad formula presence is true but too general to be human semantics."
        else:
            status = "REJECT_OR_HOLD_NOT_PREDICTIVE"
            reason = "Hypothesis does not provide enough contrastive predictive value for plaintext."
        items.append((hid, hyp, status, sc, total, 0, reason, json.dumps({"features": feats}, ensure_ascii=False, sort_keys=True)))
    accepted = sum(1 for i in items if i[2] == "ACCEPT_ABSTRACT_FUNCTION_NO_PROSE")
    summary = {"books": list(BOOKS), "accepted_abstract_functions": [i[0] for i in items if i[2] == "ACCEPT_ABSTRACT_FUNCTION_NO_PROSE"], "principle": "abstract function is not human prose"}
    cur = conn.execute("insert into benna_ltast_semantic_function_hypothesis_v1_runs values (null,?,?,?,?,?,?)", (utc_now(), "BENNA_LTAST_ABSTRACT_FUNCTION_TESTED_NO_PROSE", len(HYPOTHESES), accepted, 0, json.dumps(summary, ensure_ascii=False, sort_keys=True)))
    run_id = cur.lastrowid
    for item in items:
        conn.execute("insert into benna_ltast_semantic_function_hypothesis_v1_items values (?,?,?,?,?,?,?,?,?)", (run_id, *item))
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": "BENNA_LTAST_ABSTRACT_FUNCTION_TESTED_NO_PROSE", "accepted_function_count": accepted, "accepted_functions": [i[0] for i in items if i[2] == "ACCEPT_ABSTRACT_FUNCTION_NO_PROSE"], "accepted_prose_gloss_count": 0}, ensure_ascii=False))

if __name__ == "__main__":
    main()
