#!/usr/bin/env python3
"""Audit TibiaSecrets article160 as speculative external semantic hypothesis."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


DB_PATH = Path(__file__).resolve().parents[1] / "data" / "bonelord_operational.sqlite"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        create table if not exists tibiasecrets_article160_audit_runs (
            run_id integer primary key,
            created_at text not null,
            decision text not null,
            claim_count integer not null,
            accepted_semantic_anchor_count integer not null,
            speculative_count integer not null,
            payload_json text not null
        );

        create table if not exists tibiasecrets_article160_audit_items (
            run_id integer not null,
            claim_id text not null,
            source_url text not null,
            claim_type text not null,
            exact_sequence text,
            claimed_meaning text,
            source_status text not null,
            accept_as_semantic_anchor integer not null,
            audit_status text not null,
            reason text not null,
            payload_json text not null,
            primary key (run_id, claim_id)
        );
        """
    )

    run_id = conn.execute("select coalesce(max(run_id), 0) + 1 from tibiasecrets_article160_audit_runs").fetchone()[0]
    claims = [
        {
            "claim_id": "ARTICLE160_BOOK39_INTERPRETATION",
            "claim_type": "community_interpretation",
            "exact_sequence": "57652197278943151911851911801894452197278894383435081243485",
            "claimed_meaning": "You should be fast, but keep your eyes open, set by boots, and you'll need to weigh fifteen statues.",
            "source_status": "COMMUNITY_CONTEST_ARTICLE",
            "audit_status": "SPECULATIVE_NO_PROMOTION",
            "reason": "Article itself frames the interpretation as tentative; no primary source ties this natural-language meaning to the exact sequence.",
        },
        {
            "claim_id": "ARTICLE160_NARCISSIST_PATTERN",
            "claim_type": "pattern_hypothesis",
            "exact_sequence": "62792068657272657261",
            "claimed_meaning": "NARCISSIST or NARCISSISM pattern candidate",
            "source_status": "COMMUNITY_PATTERN_ANALYSIS",
            "audit_status": "PATTERN_ONLY_NO_PROMOTION",
            "reason": "Useful as cipher-style hypothesis, but not source-attested meaning and not Hellgate book corpus.",
        },
        {
            "claim_id": "ARTICLE160_HOMOPHONIC_CIPHER",
            "claim_type": "method_hypothesis",
            "exact_sequence": "",
            "claimed_meaning": "469 may be a homophonic substitution cipher rather than a language.",
            "source_status": "COMMUNITY_METHOD_HYPOTHESIS",
            "audit_status": "METHOD_CANDIDATE_AUDIT_ONLY",
            "reason": "Method may inspire probes, but does not validate lexical mappings.",
        },
    ]

    accepted = speculative = 0
    for claim in claims:
        accept = 0
        if "SPECULATIVE" in claim["audit_status"] or "PATTERN" in claim["audit_status"] or "METHOD" in claim["audit_status"]:
            speculative += 1
        conn.execute(
            """
            insert into tibiasecrets_article160_audit_items
            (run_id, claim_id, source_url, claim_type, exact_sequence,
             claimed_meaning, source_status, accept_as_semantic_anchor,
             audit_status, reason, payload_json)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                claim["claim_id"],
                "https://tibiasecrets.com/article160",
                claim["claim_type"],
                claim["exact_sequence"],
                claim["claimed_meaning"],
                claim["source_status"],
                accept,
                claim["audit_status"],
                claim["reason"],
                json.dumps({"source_lines": "article160 lines 40-82 and 326-338 in web audit"}, ensure_ascii=False),
            ),
        )

    decision = "TIBIASECRETS_ARTICLE160_SPECULATIVE_AUDIT_ONLY"
    conn.execute(
        """
        insert into tibiasecrets_article160_audit_runs
        (run_id, created_at, decision, claim_count, accepted_semantic_anchor_count,
         speculative_count, payload_json)
        values (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            now_iso(),
            decision,
            len(claims),
            accepted,
            speculative,
            json.dumps({"acceptance_gate": "primary or source-attested exact sequence plus meaning"}, ensure_ascii=False),
        ),
    )
    conn.commit()

    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "claim_count": len(claims),
                "accepted_semantic_anchor_count": accepted,
                "speculative_count": speculative,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
