#!/usr/bin/env python3
"""Record an external semantic anchor search round.

This round records web/source findings as SQLite audit evidence. It does not
promote any source to semantic truth unless it contains exact 469 sequence plus
source-attested natural-language meaning.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


DB_PATH = Path(__file__).resolve().parents[1] / "data" / "bonelord_operational.sqlite"


FINDINGS = [
    {
        "source_id": "TIBIAWIKI_469_UNSOLVED",
        "url": "https://tibia.fandom.com/wiki/469",
        "source_type": "wiki_context",
        "claim": "469 is Bonelord language; many claimed translations lack solid proof.",
        "exact_sequence": "",
        "meaning_claim": "",
        "evidence_status": "NO_SEMANTIC_ANCHOR_CONTEXT_ONLY",
        "risk": "context source, not a translation",
    },
    {
        "source_id": "TIBIAWIKI_BOOK_2364672119",
        "url": "https://tibia.fandom.com/wiki/2364672119_(Book)",
        "source_type": "book_text",
        "claim": "Provides exact Hellgate book text for 2364672119.",
        "exact_sequence": "23646721191180035765135347830464679727839673405792827585765125275705845217652197278304648765159564611414519889975159537243485612783020",
        "meaning_claim": "",
        "evidence_status": "EXACT_SEQUENCE_NO_MEANING",
        "risk": "identity only; no semantic gloss",
    },
    {
        "source_id": "TIBIAWIKI_BOOK_5765219727",
        "url": "https://tibia.fandom.com/wiki/5765219727_(Book)",
        "source_type": "book_text",
        "claim": "Provides exact/related Hellgate book page for 5765219727.",
        "exact_sequence": "5765219727",
        "meaning_claim": "",
        "evidence_status": "EXACT_SEQUENCE_NO_MEANING",
        "risk": "identity only; no semantic gloss",
    },
    {
        "source_id": "REDDIT_ULTIMATE_THEORY_2020",
        "url": "https://www.reddit.com/r/TibiaMMO/comments/jyg46w",
        "source_type": "community_hypothesis",
        "claim": "Community theory includes Chayenne quote and many numeric concatenations.",
        "exact_sequence": "",
        "meaning_claim": "speculative",
        "evidence_status": "SPECULATIVE_NO_PROMOTION",
        "risk": "secondary/community hypothesis; likely circular or unverifiable",
    },
    {
        "source_id": "REDDIT_CODES_UNSOLVED",
        "url": "https://www.reddit.com/r/codes/comments/xtbmyl",
        "source_type": "community_hypothesis",
        "claim": "Discusses 469 as unsolved and possible numeric patterns.",
        "exact_sequence": "",
        "meaning_claim": "speculative",
        "evidence_status": "SPECULATIVE_NO_PROMOTION",
        "risk": "pattern discussion, not source-attested translation",
    },
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        create table if not exists external_semantic_anchor_search_runs (
            run_id integer primary key,
            created_at text not null,
            decision text not null,
            source_count integer not null,
            accepted_semantic_anchor_count integer not null,
            exact_sequence_only_count integer not null,
            speculative_count integer not null,
            payload_json text not null
        );

        create table if not exists external_semantic_anchor_search_items (
            run_id integer not null,
            source_id text not null,
            url text not null,
            source_type text not null,
            claim text not null,
            exact_sequence text,
            meaning_claim text,
            evidence_status text not null,
            accept_as_semantic_anchor integer not null,
            risk text not null,
            payload_json text not null,
            primary key (run_id, source_id)
        );
        """
    )

    run_id = conn.execute("select coalesce(max(run_id), 0) + 1 from external_semantic_anchor_search_runs").fetchone()[0]
    accepted = exact_only = speculative = 0
    for finding in FINDINGS:
        accept = 1 if finding["evidence_status"] == "ACCEPTED_SEMANTIC_ANCHOR" else 0
        if accept:
            accepted += 1
        if finding["evidence_status"] == "EXACT_SEQUENCE_NO_MEANING":
            exact_only += 1
        if "SPECULATIVE" in finding["evidence_status"]:
            speculative += 1
        conn.execute(
            """
            insert into external_semantic_anchor_search_items
            (run_id, source_id, url, source_type, claim, exact_sequence,
             meaning_claim, evidence_status, accept_as_semantic_anchor, risk, payload_json)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                finding["source_id"],
                finding["url"],
                finding["source_type"],
                finding["claim"],
                finding["exact_sequence"],
                finding["meaning_claim"],
                finding["evidence_status"],
                accept,
                finding["risk"],
                json.dumps({"search_round": "2026-04-28"}, ensure_ascii=False),
            ),
        )

    decision = "EXTERNAL_SEARCH_FOUND_NO_ACCEPTABLE_SEMANTIC_ANCHOR"
    conn.execute(
        """
        insert into external_semantic_anchor_search_runs
        (run_id, created_at, decision, source_count, accepted_semantic_anchor_count,
         exact_sequence_only_count, speculative_count, payload_json)
        values (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            now_iso(),
            decision,
            len(FINDINGS),
            accepted,
            exact_only,
            speculative,
            json.dumps({"acceptance_gate": "exact sequence plus source-attested natural-language meaning"}, ensure_ascii=False),
        ),
    )
    conn.commit()

    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "source_count": len(FINDINGS),
                "accepted_semantic_anchor_count": accepted,
                "exact_sequence_only_count": exact_only,
                "speculative_count": speculative,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
