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
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    key_compare = cur.execute("select run_id, agreement, decision from tibiasecrets_key_table_compare_runs order by run_id desc limit 1").fetchone()
    cur.executescript(
        """
        create table if not exists literal_homophonic_books_v1_runs(
            run_id integer primary key autoincrement,
            created_at text not null,
            source_row0_run_id integer not null,
            source_key_compare_run_id integer not null,
            book_count integer not null,
            semantic_gloss_count integer not null,
            decision text not null,
            next_action text not null,
            payload_json text not null
        );
        create table if not exists literal_homophonic_books_v1(
            run_id integer not null,
            bookid text not null,
            literal_text text not null,
            token_count integer not null,
            semantic_status text not null,
            evidence_json text not null,
            primary key(run_id, bookid)
        );
        """
    )
    row0_run = cur.execute("select max(run_id) from row0_variant_frontier_runs").fetchone()[0]
    rows = cur.execute(
        "select bookid, symbol_text, token_count, tokens_json from row0_variant_book_tokens where run_id=? order by cast(bookid as int)",
        (row0_run,),
    ).fetchall()
    decision = "LITERAL_HOMOPHONIC_BOOK_LAYER_CREATED_NOT_SEMANTIC_TRANSLATION"
    next_action = "Use literal layer for segmentation and external alignment only; do not present as final English translation."
    cur.execute(
        "insert into literal_homophonic_books_v1_runs(created_at,source_row0_run_id,source_key_compare_run_id,book_count,semantic_gloss_count,decision,next_action,payload_json) values (?,?,?,?,?,?,?,?)",
        (
            now(),
            row0_run,
            key_compare["run_id"] if key_compare else 0,
            len(rows),
            0,
            decision,
            next_action,
            j({"key_compare": dict(key_compare) if key_compare else None, "semantic_policy": "literal homophonic symbols are not prose/gloss"}),
        ),
    )
    run_id = cur.lastrowid
    for row in rows:
        cur.execute(
            "insert into literal_homophonic_books_v1(run_id,bookid,literal_text,token_count,semantic_status,evidence_json) values (?,?,?,?,?,?)",
            (
                run_id,
                row["bookid"],
                row["symbol_text"],
                row["token_count"],
                "LITERAL_HOMOPHONIC_NOT_SEMANTIC_GLOSS",
                j({"source": "row0_variant_book_tokens", "tokens_json": row["tokens_json"]}),
            ),
        )
    con.commit()
    print(json.dumps({"run_id": run_id, "decision": decision, "book_count": len(rows), "semantic_gloss_count": 0}, ensure_ascii=False))


if __name__ == "__main__":
    main()
