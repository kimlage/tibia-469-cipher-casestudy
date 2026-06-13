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
        create table if not exists tibia_org_wayback_attempt_runs(
            run_id integer primary key autoincrement,
            created_at text not null,
            query_url text not null,
            usable_snapshot_count integer not null,
            decision text not null,
            next_action text not null,
            payload_json text not null
        );
        """
    )
    query = "https://web.archive.org/cdx?url=tibia.org/*&from=2010&to=2019&output=json&fl=timestamp,original,statuscode,mimetype,digest&filter=statuscode:200&collapse=digest"
    payload = {
        "observed_cdx_rows": [
            ["20101129121852", "http://tibia.org/favicon.ico", "200", "image/x-icon"],
            ["20100106184403", "http://www.tibia.org/robots.txt", "200", "text/plain"],
            ["20110625233112", "http://www.tibia.org/robots.txt", "200", "text/plain"],
        ],
        "limitation": "No archived HTML page containing the hidden poem was recovered through this CDX query.",
    }
    decision = "TIBIA_ORG_PRIMARY_HTML_NOT_RECOVERED_KEEP_MICRO_ANCHOR_PROVISIONAL"
    next_action = "Search alternate archives or direct citations; keep NARCISSIST as secondary-source provisional micro anchor."
    cur.execute(
        "insert into tibia_org_wayback_attempt_runs(created_at,query_url,usable_snapshot_count,decision,next_action,payload_json) values (?,?,?,?,?,?)",
        (now(), query, 0, decision, next_action, j(payload)),
    )
    con.commit()
    print(json.dumps({"run_id": cur.lastrowid, "decision": decision, "usable_snapshot_count": 0}, ensure_ascii=False))


if __name__ == "__main__":
    main()
