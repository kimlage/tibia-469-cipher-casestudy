#!/usr/bin/env python3
"""Persist current web-audit result for 469/Bonelord external claims."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
ITEMS = [
    ("tibiawiki_469", "https://tibia.fandom.com/wiki/469", "CONTEXT_ONLY_NO_SOLID_PROOF", "States 469 is Bonelord language and notes many claimed translations lack solid proof; no exact book plaintext."),
    ("tibiaqa_how_to_speak_469", "https://www.tibiaqa.com/9729/how-to-speak-bonelord-language-469", "CONTEXT_ONLY_NO_DECODER", "Discussion says there is no clear clue for speaking 469; mentions math/key theories but no proven book gloss."),
    ("tibiasecrets_article160", "https://tibiasecrets.com/article160", "RESEARCH_THEORY_NO_EXACT_GLOSS", "Research overview/theories; no accepted exact sequence plus explicit plaintext for books."),
    ("s2ward_469", "https://github.com/s2ward/469", "SCOPED_LORE_ANCHORS_ONLY", "Useful corpus/lore anchors such as 486486/1/0/469; not book-promotable plaintext."),
    ("reddit_recent_claims", "https://www.reddit.com/r/TibiaMMO/search/?q=469%20bonelord&restrict_sr=1", "REJECT_UNVERIFIED_OR_DISCUSSION", "Recent Reddit claims/discussions do not satisfy exact sequence plus explicit provenance gate."),
]


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main():
    conn = sqlite3.connect(DB)
    conn.executescript("""
    create table if not exists external_current_web_audit_v1_runs (
        run_id integer primary key autoincrement,
        created_at text not null,
        decision text not null,
        source_count integer not null,
        accepted_book_plaintext_count integer not null,
        accepted_prose_gloss_count integer not null,
        summary_json text not null
    );
    create table if not exists external_current_web_audit_v1_items (
        run_id integer not null,
        source_id text not null,
        source_url text not null,
        audit_status text not null,
        finding text not null,
        book_promotion_allowed integer not null,
        prose_gloss_allowed integer not null,
        evidence_json text not null,
        primary key (run_id, source_id)
    );
    """)
    summary = {"acceptance_gate": "exact sequence plus explicit meaning/provenance", "result": "no current web source found that changes book/plaintext classifications"}
    cur = conn.execute("insert into external_current_web_audit_v1_runs values (null,?,?,?,?,?,?)", (utc_now(), "CURRENT_WEB_AUDIT_NO_BOOK_PLAINTEXT_PROMOTION", len(ITEMS), 0, 0, json.dumps(summary, ensure_ascii=False, sort_keys=True)))
    run_id = cur.lastrowid
    for source_id, url, status, finding in ITEMS:
        conn.execute("insert into external_current_web_audit_v1_items values (?,?,?,?,?,?,?,?)", (run_id, source_id, url, status, finding, 0, 0, json.dumps({"wording": "summarized web search result; no long quotes"}, ensure_ascii=False, sort_keys=True)))
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": "CURRENT_WEB_AUDIT_NO_BOOK_PLAINTEXT_PROMOTION", "source_count": len(ITEMS), "accepted_book_plaintext_count": 0, "accepted_prose_gloss_count": 0}, ensure_ascii=False))

if __name__ == "__main__":
    main()
