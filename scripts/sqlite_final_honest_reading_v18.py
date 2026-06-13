#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import sqlite3
from typing import Any

DB_DEFAULT = "./data/bonelord_operational.sqlite"
BOOK4_TAG = "469_MARKER_LANGUAGE_LABEL_OR_METAFORMULA_RESIDUAL_AUDIT_SAFE"


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
        create table if not exists final_honest_reading_v18_runs(
            run_id integer primary key autoincrement,
            created_at text not null,
            source_v17_run_id integer not null,
            added_tag_count integer not null,
            functionally_tagged_count integer not null,
            gloss_allowed_count integer not null,
            blocked_book34 integer not null,
            decision text not null,
            next_action text not null,
            payload_json text not null
        );
        create table if not exists final_honest_reading_v18_books(
            run_id integer not null,
            bookid text not null,
            reading_status text not null,
            audit_covered integer not null,
            gloss_allowed integer not null,
            functional_tag_count integer not null,
            added_v18_tag_count integer not null,
            functional_tags_json text not null,
            honest_text text not null,
            evidence_json text not null,
            primary key(run_id, bookid)
        );
        """
    )
    source_run = cur.execute("select max(run_id) from final_honest_reading_v17_books").fetchone()[0]
    rows = cur.execute("select * from final_honest_reading_v17_books where run_id=? order by cast(bookid as int)", (source_run,)).fetchall()
    coverage_run = cur.execute("select max(run_id) from s2ward_residual_fragment_coverage_gate_runs").fetchone()[0]
    out = []
    added = 0
    for row in rows:
        tags = json.loads(row["functional_tags_json"])
        evidence = json.loads(row["evidence_json"])
        added_here = 0
        if row["bookid"] == "4" and BOOK4_TAG not in tags:
            tags.append(BOOK4_TAG)
            added_here = 1
            added += 1
            evidence = {
                **evidence,
                "v18_added_tags": [BOOK4_TAG],
                "s2ward_residual_fragment_coverage_gate_run_id": coverage_run,
                "book4_external_note": "s2ward B71 maps 140/140 to Book 4 and is annotated 469; functional no-gloss only",
                "gloss_policy": "no semantic gloss promoted",
            }
        if row["bookid"] == "34":
            evidence = {
                **evidence,
                "v18_blocked_candidate_tags": ["SCRAMBLED_RECURRENT_FRAGMENT_ASSEMBLY_AUDIT_SAFE"],
                "book34_block_reason": "raw digit coverage conflicts with stronger symbolic/control audit; Books 17 and 68 share the core recurrent material",
                "gloss_policy": "no semantic gloss promoted",
            }
        out.append(
            {
                "bookid": row["bookid"],
                "reading_status": "AUDIT_SAFE_FUNCTIONAL_READING_NO_GLOSS" if tags and not row["gloss_allowed"] else row["reading_status"],
                "audit_covered": row["audit_covered"],
                "gloss_allowed": row["gloss_allowed"],
                "functional_tag_count": len(tags),
                "added_v18_tag_count": added_here,
                "functional_tags_json": j(tags),
                "honest_text": row["honest_text"],
                "evidence_json": j(evidence),
            }
        )
    tagged = sum(1 for row in out if row["functional_tag_count"] > 0)
    gloss = sum(1 for row in out if row["gloss_allowed"])
    decision = "FINAL_HONEST_READING_V18_BOOK4_PROMOTED_BOOK34_BLOCKED_NO_GLOSS"
    next_action = "Book34 remains the only no-function residual; continue with stronger ordered assembly/boundary controls or external exact source."
    cur.execute(
        "insert into final_honest_reading_v18_runs(created_at,source_v17_run_id,added_tag_count,functionally_tagged_count,gloss_allowed_count,blocked_book34,decision,next_action,payload_json) values (?,?,?,?,?,?,?,?,?)",
        (
            now(),
            source_run,
            added,
            tagged,
            gloss,
            1,
            decision,
            next_action,
            j({"book4_tag": BOOK4_TAG, "book34_blocked": True, "coverage_gate_run_id": coverage_run}),
        ),
    )
    run_id = cur.lastrowid
    for row in out:
        cur.execute(
            "insert into final_honest_reading_v18_books(run_id,bookid,reading_status,audit_covered,gloss_allowed,functional_tag_count,added_v18_tag_count,functional_tags_json,honest_text,evidence_json) values (?,?,?,?,?,?,?,?,?,?)",
            (
                run_id,
                row["bookid"],
                row["reading_status"],
                row["audit_covered"],
                row["gloss_allowed"],
                row["functional_tag_count"],
                row["added_v18_tag_count"],
                row["functional_tags_json"],
                row["honest_text"],
                row["evidence_json"],
            ),
        )
    con.commit()
    print(json.dumps({"run_id": run_id, "decision": decision, "added_tag_count": added, "functionally_tagged_count": tagged, "functionally_tagged_pct": round(tagged / len(out) * 100, 3), "gloss_allowed_count": gloss, "remaining_untagged": [row["bookid"] for row in out if row["functional_tag_count"] == 0]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
