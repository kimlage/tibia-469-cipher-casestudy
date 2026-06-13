#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import sqlite3
from collections import Counter, defaultdict
from typing import Any

DB_DEFAULT = "./data/bonelord_operational.sqlite"


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def tag_key(tag: Any) -> str:
    if isinstance(tag, str):
        return tag
    if isinstance(tag, dict) and tag.get("tag_id"):
        return str(tag["tag_id"])
    return json.dumps(tag, ensure_ascii=False, sort_keys=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=DB_DEFAULT)
    args = parser.parse_args()
    con = sqlite3.connect(args.db)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.executescript(
        """
        create table if not exists final_honest_reading_v19_tag_distribution_runs(
            run_id integer primary key autoincrement,
            created_at text not null,
            source_v19_run_id integer not null,
            distinct_tag_count integer not null,
            singleton_tag_count integer not null,
            largest_cluster_size integer not null,
            decision text not null,
            next_action text not null,
            payload_json text not null
        );
        create table if not exists final_honest_reading_v19_tag_distribution_items(
            run_id integer not null,
            tag_key text not null,
            book_count integer not null,
            books_json text not null,
            candidate_status text not null,
            evidence_json text not null,
            primary key(run_id, tag_key)
        );
        """
    )
    source_run = cur.execute("select max(run_id) from final_honest_reading_v19_books").fetchone()[0]
    counts = Counter()
    books_by_tag: dict[str, list[str]] = defaultdict(list)
    raw_examples: dict[str, Any] = {}
    for row in cur.execute("select bookid, functional_tags_json from final_honest_reading_v19_books where run_id=?", (source_run,)):
        tags = json.loads(row["functional_tags_json"])
        for tag in tags:
            key = tag_key(tag)
            counts[key] += 1
            books_by_tag[key].append(str(row["bookid"]))
            raw_examples.setdefault(key, tag)
    singleton = sum(1 for _, count in counts.items() if count == 1)
    largest = max(counts.values()) if counts else 0
    decision = "V19_TAG_DISTRIBUTION_READY_FOR_SEMANTIC_CONTRAST"
    next_action = "Use clusters as prediction targets for non-circular semantic/lore constraints."
    payload = {
        "source_v19_run_id": source_run,
        "tags": [
            {"tag_key": key, "count": count, "books": books_by_tag[key], "raw_example": raw_examples[key]}
            for key, count in counts.most_common()
        ],
    }
    cur.execute(
        "insert into final_honest_reading_v19_tag_distribution_runs(created_at,source_v19_run_id,distinct_tag_count,singleton_tag_count,largest_cluster_size,decision,next_action,payload_json) values (?,?,?,?,?,?,?,?)",
        (now(), source_run, len(counts), singleton, largest, decision, next_action, j(payload)),
    )
    run_id = cur.lastrowid
    for key, count in counts.most_common():
        status = "SINGLETON_FUNCTIONAL_TAG" if count == 1 else "CLUSTER_FUNCTIONAL_TAG"
        cur.execute(
            "insert into final_honest_reading_v19_tag_distribution_items(run_id,tag_key,book_count,books_json,candidate_status,evidence_json) values (?,?,?,?,?,?)",
            (run_id, key, count, j(books_by_tag[key]), status, j({"tag_key": key, "count": count, "books": books_by_tag[key], "raw_example": raw_examples[key]})),
        )
    con.commit()
    print(json.dumps({"run_id": run_id, "decision": decision, "distinct_tag_count": len(counts), "singleton_tag_count": singleton, "largest_cluster_size": largest}, ensure_ascii=False))


if __name__ == "__main__":
    main()
