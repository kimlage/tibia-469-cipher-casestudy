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
    cur.executescript(
        """
        create table if not exists s2ward_residual_fragment_coverage_gate_runs(
            run_id integer primary key autoincrement,
            created_at text not null,
            accepted_count integer not null,
            blocked_count integer not null,
            decision text not null,
            next_action text not null,
            payload_json text not null
        );
        create table if not exists s2ward_residual_fragment_coverage_gate_items(
            run_id integer not null,
            bookid text not null,
            token_count integer not null,
            fragment_count integer not null,
            covered_token_count integer not null,
            covered_ratio real not null,
            recurrent_fragment_count integer not null,
            degenerate_fragment_count integer not null,
            s2ward_note text not null,
            recommended_tag text not null,
            decision text not null,
            evidence_json text not null,
            primary key(run_id, bookid)
        );
        """
    )
    latest_frag_run = cur.execute("select max(run_id) from s2ward_residual_fragment_probe_runs").fetchone()[0]
    latest_line_run = cur.execute("select max(run_id) from s2ward_rearrange_line_map_runs").fetchone()[0]
    results = []
    for bookid in ["4", "34"]:
        book = cur.execute(
            """
            select v.tokens_json, v.symbol_text, b.digits
            from row0_variant_book_tokens v
            join sheet__books b on cast(b.bookid as text)=cast(v.bookid as text)
            where v.run_id=(select max(run_id) from row0_variant_frontier_runs) and v.bookid=?
            """,
            (bookid,),
        ).fetchone()
        tokens = json.loads(book["tokens_json"])
        raw_digits = "".join(ch for ch in str(book["digits"]) if ch.isdigit())
        covered = set()
        fragments = cur.execute(
            """
            select fragment, row0_symbol_text, candidate_status
            from s2ward_residual_fragment_probe_items
            where run_id=? and bookid=?
            """,
            (latest_frag_run, bookid),
        ).fetchall()
        for frag in fragments:
            text = str(frag["fragment"])
            if not text:
                continue
            start = 0
            while True:
                idx = raw_digits.find(text, start)
                if idx < 0:
                    break
                covered.update(range(idx, idx + len(text)))
                start = idx + 1
        note_rows = cur.execute(
            "select label, note from s2ward_rearrange_line_map_items where run_id=? and mapped_bookid=? order by line_no",
            (latest_line_run, bookid),
        ).fetchall()
        note = " | ".join(f"{r['label']}: {r['note']}" for r in note_rows)
        recurrent = sum(1 for frag in fragments if "RECURRENT" in str(frag["candidate_status"]))
        degenerate = sum(1 for frag in fragments if "DEGENERATE" in str(frag["candidate_status"]))
        ratio = round(len(covered) / len(raw_digits), 3) if raw_digits else 0.0
        if bookid == "4" and ratio >= 0.80 and "469" in note:
            tag = "LANGUAGE_LABEL_METAFORMULA_469_AUDIT_SAFE"
            decision = "ACCEPT_FUNCTIONAL_TAG_NO_GLOSS"
        elif bookid == "34" and ratio >= 0.55 and recurrent >= 3:
            tag = "SCRAMBLED_RECURRENT_FRAGMENT_ASSEMBLY_AUDIT_SAFE"
            decision = "ACCEPT_FUNCTIONAL_TAG_NO_GLOSS"
        else:
            tag = ""
            decision = "BLOCK_FUNCTIONAL_TAG_INSUFFICIENT_SUPPORT"
        results.append(
            {
                "bookid": bookid,
                "token_count": len(tokens),
                "fragment_count": len(fragments),
                "covered_token_count": len(covered),
                "covered_ratio": ratio,
                "recurrent_fragment_count": recurrent,
                "degenerate_fragment_count": degenerate,
                "s2ward_note": note,
                "recommended_tag": tag,
                "decision": decision,
                "covered_positions": sorted(covered),
            }
        )
    accepted = sum(1 for row in results if row["recommended_tag"])
    blocked = len(results) - accepted
    decision = "S2WARD_RESIDUAL_COVERAGE_GATE_ACCEPTS_FUNCTIONAL_TAGS" if accepted else "S2WARD_RESIDUAL_COVERAGE_GATE_BLOCKS_ALL"
    next_action = "Promote accepted tags to final_honest_reading_v18 with gloss_allowed=0." if accepted else "Keep residuals blocked."
    cur.execute(
        "insert into s2ward_residual_fragment_coverage_gate_runs(created_at,accepted_count,blocked_count,decision,next_action,payload_json) values (?,?,?,?,?,?)",
        (now(), accepted, blocked, decision, next_action, j({"results": results})),
    )
    run_id = cur.lastrowid
    for row in results:
        cur.execute(
            "insert into s2ward_residual_fragment_coverage_gate_items(run_id,bookid,token_count,fragment_count,covered_token_count,covered_ratio,recurrent_fragment_count,degenerate_fragment_count,s2ward_note,recommended_tag,decision,evidence_json) values (?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                run_id,
                row["bookid"],
                row["token_count"],
                row["fragment_count"],
                row["covered_token_count"],
                row["covered_ratio"],
                row["recurrent_fragment_count"],
                row["degenerate_fragment_count"],
                row["s2ward_note"],
                row["recommended_tag"],
                row["decision"],
                j(row),
            ),
        )
    con.commit()
    print(json.dumps({"run_id": run_id, "decision": decision, "accepted": accepted, "items": results}, ensure_ascii=False))


if __name__ == "__main__":
    main()
