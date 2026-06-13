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


ANCHORS = [
    {
        "anchor_id": "EVIL_EYE_653768764_CO_UTTERANCE",
        "sequence": "653768764",
        "candidate_meaning": "Inferior creatures, bow before my power!",
        "source_urls": [
            "https://tibia.fandom.com/wiki/The_Evil_Eye",
            "https://otland.net/threads/some-bosses-with-rl-tibia.79028/",
        ],
        "evidence_class": "CO_UTTERANCE_NOT_TRANSLATION",
        "acceptance": "HOLDOUT_ONLY_NO_GLOSS",
        "reason": "Sources list both the human phrase and numeric voice line for the same creature, but do not state that one translates the other.",
    },
    {
        "anchor_id": "ELDER_BONELORD_659978_54764_CO_UTTERANCE",
        "sequence": "659978 54764",
        "candidate_meaning": "Let me take a look at you!",
        "source_urls": [
            "https://tibia.fandom.com/wiki/Elder_Bonelord",
            "https://www.tibia-wiki.net/wiki/Elder_Bonelord",
        ],
        "evidence_class": "CO_UTTERANCE_NOT_TRANSLATION",
        "acceptance": "HOLDOUT_ONLY_NO_GLOSS",
        "reason": "Sources list the numeric and human voice lines together, but no explicit pairwise meaning/provenance is stated.",
    },
    {
        "anchor_id": "ELDER_BONELORD_653768764_CO_UTTERANCE",
        "sequence": "653768764",
        "candidate_meaning": "Inferior creatures, bow before my power!",
        "source_urls": [
            "https://tibia.fandom.com/wiki/Elder_Bonelord",
            "https://www.tibia-wiki.net/wiki/Elder_Bonelord",
        ],
        "evidence_class": "CO_UTTERANCE_NOT_TRANSLATION",
        "acceptance": "HOLDOUT_ONLY_NO_GLOSS",
        "reason": "Same co-utterance issue as Evil Eye; useful as external holdout, unsafe as semantic gloss.",
    },
    {
        "anchor_id": "AVAR_TAR_POEM_CO_CONTEXT",
        "sequence": "29639 46781",
        "candidate_meaning": "poem context only",
        "source_urls": [
            "https://tibiasecrets.com/article160",
            "https://www.reddit.com/r/TibiaMMO/comments/rmqgfs",
        ],
        "evidence_class": "SPECULATIVE_CONTEXT_NOT_TRANSLATION",
        "acceptance": "REJECTED_NO_GLOSS",
        "reason": "Avar Tar context is explicitly unreliable/speculative; do not use for book semantics.",
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
        create table if not exists external_phrase_semantic_anchor_reaudit_runs(
            run_id integer primary key autoincrement,
            created_at text not null,
            anchor_count integer not null,
            accepted_gloss_count integer not null,
            holdout_count integer not null,
            rejected_count integer not null,
            decision text not null,
            next_action text not null,
            payload_json text not null
        );
        create table if not exists external_phrase_semantic_anchor_reaudit_items(
            run_id integer not null,
            anchor_id text not null,
            sequence text not null,
            candidate_meaning text not null,
            evidence_class text not null,
            acceptance text not null,
            source_urls_json text not null,
            reason text not null,
            evidence_json text not null,
            primary key(run_id, anchor_id)
        );
        """
    )
    accepted = sum(1 for row in ANCHORS if row["acceptance"] == "ACCEPT_GLOSS")
    holdout = sum(1 for row in ANCHORS if "HOLDOUT" in row["acceptance"])
    rejected = sum(1 for row in ANCHORS if "REJECTED" in row["acceptance"])
    decision = "EXTERNAL_PHRASE_REAUDIT_NO_GLOSS_PROMOTION"
    next_action = "Use co-utterance anchors only as holdouts; require explicit sequence+meaning source before semantic promotion."
    cur.execute(
        "insert into external_phrase_semantic_anchor_reaudit_runs(created_at,anchor_count,accepted_gloss_count,holdout_count,rejected_count,decision,next_action,payload_json) values (?,?,?,?,?,?,?,?)",
        (now(), len(ANCHORS), accepted, holdout, rejected, decision, next_action, j({"anchors": ANCHORS})),
    )
    run_id = cur.lastrowid
    for row in ANCHORS:
        cur.execute(
            "insert into external_phrase_semantic_anchor_reaudit_items(run_id,anchor_id,sequence,candidate_meaning,evidence_class,acceptance,source_urls_json,reason,evidence_json) values (?,?,?,?,?,?,?,?,?)",
            (run_id, row["anchor_id"], row["sequence"], row["candidate_meaning"], row["evidence_class"], row["acceptance"], j(row["source_urls"]), row["reason"], j(row)),
        )
    con.commit()
    print(json.dumps({"run_id": run_id, "decision": decision, "accepted_gloss_count": accepted, "holdout_count": holdout, "rejected_count": rejected}, ensure_ascii=False))


if __name__ == "__main__":
    main()
