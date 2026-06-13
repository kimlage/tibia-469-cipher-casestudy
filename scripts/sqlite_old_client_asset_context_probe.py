#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import sqlite3
import subprocess
from pathlib import Path
from typing import Any

DB_DEFAULT = "./data/bonelord_operational.sqlite"
APP_DIR = Path("./tmp/tibia_clients/tibia760_inno/app")


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def strings_hits(path: Path, patterns: list[str]) -> list[str]:
    proc = subprocess.run(["strings", "-a", str(path)], text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
    hits = []
    for line in proc.stdout.splitlines():
        low = line.lower()
        if any(p in low for p in patterns):
            hits.append(line)
    return hits[:200]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=DB_DEFAULT)
    args = parser.parse_args()
    patterns = ["bonelord", "beholder", "hellgate", "469", "wrinkled", "paradox", "book", "language"]
    strong_patterns = ["bonelord", "beholder", "hellgate", "469", "wrinkled", "paradox"]
    files = sorted(APP_DIR.glob("*"))
    evidence = {}
    relevant = 0
    for path in files:
        if path.is_file():
            hits = strings_hits(path, patterns)
            if hits:
                relevant += sum(1 for h in hits if any(p in h.lower() for p in strong_patterns))
            evidence[path.name] = {"size": path.stat().st_size, "hits": hits}
    con = sqlite3.connect(args.db)
    cur = con.cursor()
    cur.executescript(
        """
        create table if not exists old_client_asset_context_probe_runs(
            run_id integer primary key autoincrement,
            created_at text not null,
            client_dir text not null,
            file_count integer not null,
            world_context_hit_count integer not null,
            decision text not null,
            next_action text not null,
            payload_json text not null
        );
        """
    )
    decision = "OLD_CLIENT_STATIC_ASSETS_NO_STRONG_WORLD_469_CONTEXT" if relevant == 0 else "OLD_CLIENT_STATIC_ASSETS_HAVE_WORLD_CONTEXT_HITS"
    next_action = "Do not pursue static client asset route without map/server/content artifact." if relevant == 0 else "Inspect world-context hits manually before any promotion."
    cur.execute(
        "insert into old_client_asset_context_probe_runs(created_at,client_dir,file_count,world_context_hit_count,decision,next_action,payload_json) values (?,?,?,?,?,?,?)",
        (now(), str(APP_DIR), len(files), relevant, decision, next_action, j({"patterns": patterns, "files": evidence})),
    )
    run_id = cur.lastrowid
    con.commit()
    print(json.dumps({"run_id": run_id, "decision": decision, "world_context_hit_count": relevant, "next_action": next_action}, ensure_ascii=False))


if __name__ == "__main__":
    main()
