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
        create table if not exists realots_tarball_policy_runs(
            run_id integer primary key autoincrement,
            created_at text not null,
            source_url text not null,
            source_claim text not null,
            policy_status text not null,
            decision text not null,
            next_action text not null,
            payload_json text not null
        );
        """
    )
    source_url = "https://otland.net/threads/7-7-realots-7-7-cipsoft-files-virgin.244562/"
    source_claim = "Public OTLand thread describes tibia-game.tarball.tar.gz as original CipSoft/Zanera server distribution."
    policy_status = "DO_NOT_DOWNLOAD_LEAKED_PROPRIETARY_ARCHIVE"
    decision = "REALOTS_TARBALL_LEAD_REQUIRES_AUTHORIZED_ARTIFACT"
    next_action = "Continue with public/open sources only; ingest this lane only if an authorized/legal artifact is provided."
    payload = {
        "source_url": source_url,
        "source_claim": source_claim,
        "why_relevant": "Could contain server/map/content context or the alleged number-list file mentioned in public discussions.",
        "why_blocked": "Archive is described as leaked proprietary server distribution; not suitable for automatic download/redistribution.",
    }
    cur.execute(
        "insert into realots_tarball_policy_runs(created_at,source_url,source_claim,policy_status,decision,next_action,payload_json) values (?,?,?,?,?,?,?)",
        (now(), source_url, source_claim, policy_status, decision, next_action, j(payload)),
    )
    con.commit()
    print(json.dumps({"run_id": cur.lastrowid, "decision": decision, "policy_status": policy_status, "next_action": next_action}, ensure_ascii=False))


if __name__ == "__main__":
    main()
