#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import sqlite3
from pathlib import Path
from typing import Any

DB_DEFAULT = "./data/bonelord_operational.sqlite"
TMP = Path("./tmp")


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


RESULTS = [
    {
        "frontier_id": "FUNCTIONAL_TAG_TO_LORE_ROLE_CONTRAST",
        "status": "ALIVE_AS_CONSTRAINT_PROBE_NO_GLOSS",
        "result_summary": "v19 functional tags predict instrumental/contextual clusters but not semantic lore gloss.",
        "accepted_gloss": 0,
        "next_action": "Use PHASE_FRAME and BRANCH_SELECTOR+PHASE_FRAME as shortlist/control axes.",
        "artifacts": [
            "./tmp/functional_tag_to_lore_role_contrast_probe.sql",
            "./tmp/functional_tag_to_lore_role_contrast_probe.md",
        ],
    },
    {
        "frontier_id": "PARADOX_TOWER_MATHEMAGIC_MODEL",
        "status": "CURRENT_FORMULATION_FAILS_CONTROLS_NO_GLOSS",
        "result_summary": "1/13/49/94 fits tetranacci seeds 1,1,1,1 but book-level functional tag prediction does not beat modular controls.",
        "accepted_gloss": 0,
        "next_action": "Reopen only as row0-local marker/delta constraint against controls; otherwise abandon.",
        "artifacts": [
            "./tmp/paradox_tower_mathemagic_probe.sql",
            "./tmp/paradox_tower_mathemagic_probe.md",
            "./tmp/paradox_tower_mathemagic_probe.out",
        ],
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
        create table if not exists semantic_frontier_v2_result_runs(
            run_id integer primary key autoincrement,
            created_at text not null,
            result_count integer not null,
            accepted_gloss_count integer not null,
            decision text not null,
            next_action text not null,
            payload_json text not null
        );
        create table if not exists semantic_frontier_v2_result_items(
            run_id integer not null,
            frontier_id text not null,
            status text not null,
            result_summary text not null,
            accepted_gloss integer not null,
            next_action text not null,
            artifacts_json text not null,
            evidence_json text not null,
            primary key(run_id, frontier_id)
        );
        """
    )
    enriched = []
    for item in RESULTS:
        excerpts = {}
        for artifact in item["artifacts"]:
            path = Path(artifact)
            excerpts[path.name] = read(path)[:4000]
        enriched.append({**item, "artifact_excerpts": excerpts})
    accepted = sum(item["accepted_gloss"] for item in RESULTS)
    decision = "SEMANTIC_FRONTIER_V2_BATCH_NO_GLOSS_PROMOTION"
    next_action = "Run row0-local tetranacci marker probe or old-client map/context asset probe; keep semantic_gloss_pct at 0."
    cur.execute(
        "insert into semantic_frontier_v2_result_runs(created_at,result_count,accepted_gloss_count,decision,next_action,payload_json) values (?,?,?,?,?,?)",
        (now(), len(RESULTS), accepted, decision, next_action, j({"results": enriched})),
    )
    run_id = cur.lastrowid
    for item in enriched:
        cur.execute(
            "insert into semantic_frontier_v2_result_items(run_id,frontier_id,status,result_summary,accepted_gloss,next_action,artifacts_json,evidence_json) values (?,?,?,?,?,?,?,?)",
            (run_id, item["frontier_id"], item["status"], item["result_summary"], item["accepted_gloss"], item["next_action"], j(item["artifacts"]), j(item)),
        )
    con.commit()
    print(json.dumps({"run_id": run_id, "decision": decision, "accepted_gloss_count": accepted, "next_action": next_action}, ensure_ascii=False))


if __name__ == "__main__":
    main()
