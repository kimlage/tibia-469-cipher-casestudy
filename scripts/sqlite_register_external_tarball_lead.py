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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=DB_DEFAULT)
    args = parser.parse_args()
    con = sqlite3.connect(args.db)
    cur = con.cursor()
    cur.executescript(
        """
        create table if not exists external_tarball_lead_runs(
            run_id integer primary key autoincrement,
            created_at text not null,
            lead_count integer not null,
            accepted_evidence_count integer not null,
            decision text not null,
            next_action text not null,
            payload_json text not null
        );
        create table if not exists external_tarball_leads(
            run_id integer not null,
            lead_id text not null,
            source_url text not null,
            claim text not null,
            counterclaim text not null,
            evidence_status text not null,
            required_next_evidence text not null,
            evidence_json text not null,
            primary key(run_id, lead_id)
        );
        """
    )
    leads = [
        {
            "lead_id": "REDDIT_DINGYPS_TARBALL_NUMBER_LIST",
            "source_url": "https://www.reddit.com/r/TibiaMMO/comments/104v18v/a_serious_approach_to_469/",
            "claim": "A commenter claims a leaked tarball/server-save had a large number-list file relating to 469 books.",
            "counterclaim": "Another commenter says one leaked file was merely spell range data; the claimant says there was another larger file.",
            "evidence_status": "UNVERIFIED_LEAD_NO_GLOSS",
            "required_next_evidence": "Obtain the actual tarball or number-list file, verify provenance, import into SQLite, and test against v19 functional tags/holdouts.",
        }
    ]
    decision = "EXTERNAL_TARBALL_LEAD_REGISTERED_UNVERIFIED"
    next_action = "Search for an accessible copy of the tarball/number-list; do not promote anything from comments alone."
    cur.execute(
        "insert into external_tarball_lead_runs(created_at,lead_count,accepted_evidence_count,decision,next_action,payload_json) values (?,?,?,?,?,?)",
        (now(), len(leads), 0, decision, next_action, j({"leads": leads})),
    )
    run_id = cur.lastrowid
    for lead in leads:
        cur.execute(
            "insert into external_tarball_leads(run_id,lead_id,source_url,claim,counterclaim,evidence_status,required_next_evidence,evidence_json) values (?,?,?,?,?,?,?,?)",
            (run_id, lead["lead_id"], lead["source_url"], lead["claim"], lead["counterclaim"], lead["evidence_status"], lead["required_next_evidence"], j(lead)),
        )
    con.commit()
    print(json.dumps({"run_id": run_id, "decision": decision, "accepted_evidence_count": 0, "next_action": next_action}, ensure_ascii=False))


if __name__ == "__main__":
    main()
