#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import sqlite3
from typing import Any

DB_DEFAULT = "./data/bonelord_operational.sqlite"


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


FINDINGS = [
    {
        "finding_id": "WRINKLED_BEHOLDER_NPC_SCRIPT_LEAK_TORG",
        "source_type": "provenance",
        "strength": "STRONG_PROVENANCE_ONLY",
        "url": "https://torg.pl/tibia/354198-wyciek-cipsoftu-2-npc.html",
        "exact_sequences": ["1", "469", "486486"],
        "claim": "Old NPC script dump preserves A Wrinkled Beholder/Bonelord context and known holdouts.",
        "acceptance": "AUDIT_ONLY_NO_GLOSS",
        "gloss_allowed": 0,
        "reason": "Confirms provenance of known holdouts but provides no new sequence+meaning pair for book translation.",
    },
    {
        "finding_id": "TIBIAWIKI_WRINKLED_BONELORD_TRANSCRIPT",
        "source_type": "provenance",
        "strength": "STRONG_PROVENANCE_ONLY",
        "url": "https://tibia.fandom.com/wiki/A_Wrinkled_Bonelord/Transcripts",
        "exact_sequences": ["1", "469", "486486"],
        "claim": "Current public transcript confirms known Wrinkled Bonelord holdouts.",
        "acceptance": "AUDIT_ONLY_NO_GLOSS",
        "gloss_allowed": 0,
        "reason": "Useful for holdout verification only; no phrase/book meaning.",
    },
    {
        "finding_id": "CHAYENNE_2009_EXTERNAL_SEQUENCES",
        "source_type": "provenance",
        "strength": "STRONG_SEQUENCE_ONLY",
        "url": "https://forum.portaltibia.com.br/topic/11420-entrevista-com-chayenne/",
        "exact_sequences": ["114514519485611451908304576512282177", "6612527570584"],
        "claim": "Public interview preserves exact external 469-like sequences.",
        "acceptance": "AUDIT_ONLY_NO_GLOSS",
        "gloss_allowed": 0,
        "reason": "Sequence provenance is useful, but no explicit meaning accompanies the sequence.",
    },
    {
        "finding_id": "KNIGHTMARE_BONELORD_TOME_SEQUENCE",
        "source_type": "provenance",
        "strength": "STRONG_SEQUENCE_ONLY",
        "url": "https://tibia.fandom.com/wiki/Bonelord_Tome",
        "exact_sequences": ["3478 67 90871 97664 3466 0 345!"],
        "claim": "Bonelord Tome/Knightmare material preserves a known external phrase.",
        "acceptance": "AUDIT_ONLY_NO_GLOSS",
        "gloss_allowed": 0,
        "reason": "No explicit reliable meaning; do not promote 3478 or phrase-level gloss.",
    },
    {
        "finding_id": "TIBIABR_ATTACHMENT_2445_BLIN_PARTIAL",
        "source_type": "forum_speculation",
        "strength": "REJECTED_SPECULATIVE",
        "url": "https://forums.tibiabr.com/printthread.php?pp=10&t=511342",
        "exact_sequences": ["486"],
        "claim": "Old forum thread proposes a partial 486 -> blin derivation.",
        "acceptance": "REJECTED_NO_PROMOTION",
        "gloss_allowed": 0,
        "reason": "Speculative, partial, manually fit, and conflicts with the explicit NOT Blinky clue.",
    },
    {
        "finding_id": "S2WARD_469_CORPUS_ALIGNMENT",
        "source_type": "tooling_corpus",
        "strength": "REPRODUCIBLE_CORPUS_ONLY",
        "url": "https://github.com/s2ward/469",
        "exact_sequences": [],
        "claim": "Reproducible public corpus/tooling for comparison.",
        "acceptance": "AUDIT_ONLY_NO_GLOSS",
        "gloss_allowed": 0,
        "reason": "Can support alignment or corpus checks, but does not provide validated sequence+meaning.",
    },
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=DB_DEFAULT)
    args = parser.parse_args()
    con = sqlite3.connect(args.db)
    cur = con.cursor()
    cur.executescript(
        """
        create table if not exists external_archive_audit_finding_runs(
            run_id integer primary key autoincrement,
            created_at text not null,
            finding_count integer not null,
            gloss_allowed_count integer not null,
            decision text not null,
            next_action text not null,
            payload_json text not null
        );
        create table if not exists external_archive_audit_findings(
            run_id integer not null,
            finding_id text not null,
            source_type text not null,
            strength text not null,
            url text not null,
            exact_sequences_json text not null,
            claim text not null,
            acceptance text not null,
            gloss_allowed integer not null,
            reason text not null,
            evidence_json text not null,
            primary key(run_id, finding_id)
        );
        """
    )
    gloss_count = sum(int(item["gloss_allowed"]) for item in FINDINGS)
    decision = "EXTERNAL_ARCHIVE_AUDIT_ONLY_NO_SEMANTIC_PROMOTION"
    next_action = "Use these sources only as provenance/holdouts; continue with structural or new artifact hypotheses."
    cur.execute(
        "insert into external_archive_audit_finding_runs(created_at,finding_count,gloss_allowed_count,decision,next_action,payload_json) values (?,?,?,?,?,?)",
        (now(), len(FINDINGS), gloss_count, decision, next_action, j({"findings": FINDINGS})),
    )
    run_id = cur.lastrowid
    for item in FINDINGS:
        cur.execute(
            "insert into external_archive_audit_findings(run_id,finding_id,source_type,strength,url,exact_sequences_json,claim,acceptance,gloss_allowed,reason,evidence_json) values (?,?,?,?,?,?,?,?,?,?,?)",
            (
                run_id,
                item["finding_id"],
                item["source_type"],
                item["strength"],
                item["url"],
                j(item["exact_sequences"]),
                item["claim"],
                item["acceptance"],
                item["gloss_allowed"],
                item["reason"],
                j(item),
            ),
        )
    con.commit()
    print(json.dumps({"run_id": run_id, "decision": decision, "finding_count": len(FINDINGS), "gloss_allowed_count": gloss_count}, ensure_ascii=False))


if __name__ == "__main__":
    main()
