#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import sqlite3
from typing import Any

DB_DEFAULT = "./data/bonelord_operational.sqlite"
TAG = "SELF_CONTAINED_REPEAT_FORMULA_AUDIT_SAFE"


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
    cur.executescript(
        """
        create table if not exists final_honest_reading_v17_runs(
            run_id integer primary key autoincrement,
            created_at text not null,
            source_v16_run_id integer not null,
            added_tag_count integer not null,
            functionally_tagged_count integer not null,
            gloss_allowed_count integer not null,
            decision text not null,
            next_action text not null,
            payload_json text not null
        );
        create table if not exists final_honest_reading_v17_books(
            run_id integer not null,
            bookid text not null,
            reading_status text not null,
            audit_covered integer not null,
            gloss_allowed integer not null,
            functional_tag_count integer not null,
            added_v17_tag_count integer not null,
            functional_tags_json text not null,
            honest_text text not null,
            evidence_json text not null,
            primary key(run_id, bookid)
        );
        """
    )
    source_run = cur.execute("select max(run_id) from final_honest_reading_v16_books").fetchone()[0]
    gate = cur.execute("select run_id, decision, functional_tag, payload_json from book49_selfcontainment_gate_runs order by run_id desc limit 1").fetchone()
    if not gate or gate["functional_tag"] != TAG:
        raise SystemExit("missing accepted book49 selfcontainment gate")
    rows = cur.execute("select * from final_honest_reading_v16_books where run_id=? order by cast(bookid as int)", (source_run,)).fetchall()
    out = []
    added = 0
    for row in rows:
        tags = json.loads(row["functional_tags_json"])
        evidence = json.loads(row["evidence_json"])
        added_here = 0
        if row["bookid"] == "49" and TAG not in tags:
            tags.append(TAG)
            added_here = 1
            added += 1
            evidence = {
                **evidence,
                "v17_added_tags": [TAG],
                "book49_selfcontainment_gate_run_id": gate["run_id"],
                "book49_selfcontainment_decision": gate["decision"],
                "gloss_policy": "functional tag only; gloss remains disallowed",
            }
        out.append(
            {
                "bookid": row["bookid"],
                "reading_status": "AUDIT_SAFE_FUNCTIONAL_READING_NO_GLOSS" if tags and not row["gloss_allowed"] else row["reading_status"],
                "audit_covered": row["audit_covered"],
                "gloss_allowed": row["gloss_allowed"],
                "functional_tag_count": len(tags),
                "added_v17_tag_count": added_here,
                "functional_tags_json": j(tags),
                "honest_text": row["honest_text"],
                "evidence_json": j(evidence),
            }
        )
    tagged = sum(1 for row in out if row["functional_tag_count"] > 0)
    gloss = sum(1 for row in out if row["gloss_allowed"])
    decision = "FINAL_HONEST_READING_V17_BOOK49_FUNCTIONAL_TAG_PROMOTED_NO_GLOSS"
    next_action = "Continue with book4/book34 structural gates; semantic_gloss remains zero."
    cur.execute(
        "insert into final_honest_reading_v17_runs(created_at,source_v16_run_id,added_tag_count,functionally_tagged_count,gloss_allowed_count,decision,next_action,payload_json) values (?,?,?,?,?,?,?,?)",
        (
            now(),
            source_run,
            added,
            tagged,
            gloss,
            decision,
            next_action,
            j({"book49_gate_run_id": gate["run_id"], "tag": TAG}),
        ),
    )
    run_id = cur.lastrowid
    for row in out:
        cur.execute(
            "insert into final_honest_reading_v17_books(run_id,bookid,reading_status,audit_covered,gloss_allowed,functional_tag_count,added_v17_tag_count,functional_tags_json,honest_text,evidence_json) values (?,?,?,?,?,?,?,?,?,?)",
            (
                run_id,
                row["bookid"],
                row["reading_status"],
                row["audit_covered"],
                row["gloss_allowed"],
                row["functional_tag_count"],
                row["added_v17_tag_count"],
                row["functional_tags_json"],
                row["honest_text"],
                row["evidence_json"],
            ),
        )
    con.commit()
    print(json.dumps({"run_id": run_id, "decision": decision, "added_tag_count": added, "functionally_tagged_count": tagged, "functionally_tagged_pct": round(tagged / len(out) * 100, 3), "gloss_allowed_count": gloss}, ensure_ascii=False))


if __name__ == "__main__":
    main()
