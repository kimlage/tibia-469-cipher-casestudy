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


FRONTIER = [
    {
        "rank": 1,
        "frontier_id": "PARADOX_TOWER_MATHEMAGIC_MODEL",
        "lane": "mechanical_semantic_bridge",
        "reason_selected": "In-game NPC states 469 relies on mathemagic; current functional layer is complete but has no meaning.",
        "why_not_repeated": "Not a base-N/charset retry; tests algebraic constraints from in-game math lore against functional templates.",
        "success_gate": "Predicts at least one held-out external numeric phrase or book functional class without using English shadow text.",
        "abandon_gate": "Only fits known functional tags post hoc or requires arbitrary operator choices.",
        "status": "OPEN",
    },
    {
        "rank": 2,
        "frontier_id": "EXPLICIT_SEQUENCE_MEANING_SOURCE_ONLY",
        "lane": "external_research",
        "reason_selected": "Only route that can safely raise semantic_gloss_pct.",
        "why_not_repeated": "Now excludes co-utterance pages and forum speculation already classified as holdout/rejected.",
        "success_gate": "Source explicitly says sequence X means phrase Y or gives reproducible official solution/provenance.",
        "abandon_gate": "Lists numeric and human voice lines together without stating translation.",
        "status": "OPEN",
    },
    {
        "rank": 3,
        "frontier_id": "FUNCTIONAL_TAG_TO_LORE_ROLE_CONTRAST",
        "lane": "semantic_audit",
        "reason_selected": "All 70 books now have functional tags; compare tag distribution to known Hellgate/library/lore roles without assigning words.",
        "why_not_repeated": "Targets role-level semantic constraints, not phrase gloss or English hallucination.",
        "success_gate": "Identifies a role constraint that predicts held-out book groupings or external corpus placement.",
        "abandon_gate": "Only produces plausible prose labels with no predictive test.",
        "status": "OPEN",
    },
    {
        "rank": 4,
        "frontier_id": "OLD_CLIENT_ASSET_TEXT_AND_MAP_CONTEXT",
        "lane": "artifact_context",
        "reason_selected": "We obtained old clients and extracted PICs, but have not mined DAT/map/book placement context from assets.",
        "why_not_repeated": "Not charset/base-N; uses world placement/context artifacts if reproducibly extractable.",
        "success_gate": "Reconstructs location/context metadata that constrains book order or semantic role independently.",
        "abandon_gate": "Client assets do not contain relevant map/book placement data or extraction is unverifiable.",
        "status": "OPEN",
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
        create table if not exists semantic_non_circular_frontier_v2_runs(
            run_id integer primary key autoincrement,
            created_at text not null,
            frontier_count integer not null,
            decision text not null,
            next_action text not null,
            payload_json text not null
        );
        create table if not exists semantic_non_circular_frontier_v2_items(
            run_id integer not null,
            rank integer not null,
            frontier_id text not null,
            lane text not null,
            reason_selected text not null,
            why_not_repeated text not null,
            success_gate text not null,
            abandon_gate text not null,
            status text not null,
            evidence_json text not null,
            primary key(run_id, rank)
        );
        """
    )
    decision = "SEMANTIC_FRONTIER_V2_READY_FUNCTIONAL_COMPLETE_GLOSS_ZERO"
    next_action = "Run rank 1 and rank 3 in parallel; keep rank 2 as strict external search; do not use co-utterance as gloss."
    cur.execute(
        "insert into semantic_non_circular_frontier_v2_runs(created_at,frontier_count,decision,next_action,payload_json) values (?,?,?,?,?)",
        (now(), len(FRONTIER), decision, next_action, j({"frontier": FRONTIER})),
    )
    run_id = cur.lastrowid
    for row in FRONTIER:
        cur.execute(
            "insert into semantic_non_circular_frontier_v2_items(run_id,rank,frontier_id,lane,reason_selected,why_not_repeated,success_gate,abandon_gate,status,evidence_json) values (?,?,?,?,?,?,?,?,?,?)",
            (run_id, row["rank"], row["frontier_id"], row["lane"], row["reason_selected"], row["why_not_repeated"], row["success_gate"], row["abandon_gate"], row["status"], j(row)),
        )
    con.commit()
    print(json.dumps({"run_id": run_id, "decision": decision, "next_action": next_action, "frontier": FRONTIER}, ensure_ascii=False))


if __name__ == "__main__":
    main()
