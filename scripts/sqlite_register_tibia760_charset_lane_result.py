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


def row(cur: sqlite3.Cursor, sql: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    got = cur.execute(sql, params).fetchone()
    return dict(got) if got else None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=DB_DEFAULT)
    args = parser.parse_args()

    con = sqlite3.connect(args.db)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    slot_run = row(
        cur,
        "select run_id, created_at, alphabet_len, item_count, strong_count, decision, next_action from tibia760_visual_slot_base_sweep_runs order by run_id desc limit 1",
    )
    artifact_run = row(
        cur,
        "select run_id, created_at, image_count, decision, next_action from tibia760_pic_container_extract_runs order by run_id desc limit 1",
    )
    if not slot_run:
        raise SystemExit("missing tibia760_visual_slot_base_sweep_runs")

    cur.executescript(
        """
        create table if not exists tibia760_charset_lane_resolution_runs(
            run_id integer primary key autoincrement,
            created_at text not null,
            source_slot_run_id integer not null,
            source_artifact_run_id integer,
            status text not null,
            result_summary text not null,
            blocked_reason text not null,
            next_action text not null,
            evidence_json text not null
        );
        """
    )

    status = "CHARSET_ROUTE_CLOSED_NO_TRANSLATION_SIGNAL"
    result_summary = (
        "Tibia 7.60 artifact was obtained and Tibia.pic font/image pages were extracted; visual slot alphabet 32..255 was tested against books and external sequences."
    )
    blocked_reason = (
        "The authentic visual-slot base-N sweep produced zero strong readable candidates; top hits are short accidental fragments without common-word/provenance support."
    )
    next_action = "Do not reopen BASE_N_WITH_AUTHENTIC_TIBIA_CHARSET unless a new artifact changes slot order or adds a non-base transform with independent holdout evidence."
    evidence = {
        "artifact_run": artifact_run,
        "slot_run": slot_run,
        "source_artifacts": [
            "./tmp/tibia_clients/tibia760.tgz",
            "./tmp/tibia_clients/tibia760.exe",
            "./tmp/tibia_clients/tibia760_extracted/image_02_256x128.png",
            "./tmp/tibia_clients/tibia760_extracted/image_07_256x128.png",
        ],
    }

    cur.execute(
        "insert into tibia760_charset_lane_resolution_runs(created_at,source_slot_run_id,source_artifact_run_id,status,result_summary,blocked_reason,next_action,evidence_json) values (?,?,?,?,?,?,?,?)",
        (
            now(),
            slot_run["run_id"],
            artifact_run["run_id"] if artifact_run else None,
            status,
            result_summary,
            blocked_reason,
            next_action,
            j(evidence),
        ),
    )
    run_id = cur.lastrowid
    con.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "status": status,
                "source_slot_run_id": slot_run["run_id"],
                "source_artifact_run_id": artifact_run["run_id"] if artifact_run else None,
                "next_action": next_action,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
