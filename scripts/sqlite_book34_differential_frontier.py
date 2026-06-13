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


def digits_only(value: str) -> str:
    return "".join(ch for ch in value if ch.isdigit())


def maximal_absent_spans(target: str, controls: list[str]) -> list[dict[str, Any]]:
    absent = [not any(target[i : i + 1] in c for c in controls) for i in range(len(target))]
    # Character absence is too strict for digits. Instead mark positions covered
    # by any control substring of length >=8; gaps are differential seams.
    covered = [False] * len(target)
    for n in range(8, min(40, len(target)) + 1):
        for i in range(0, len(target) - n + 1):
            frag = target[i : i + n]
            if any(frag in c for c in controls):
                for k in range(i, i + n):
                    covered[k] = True
    spans = []
    start = None
    for idx, is_covered in enumerate(covered + [True]):
        if not is_covered and start is None:
            start = idx
        elif is_covered and start is not None:
            frag = target[start:idx]
            if len(frag) >= 3:
                spans.append({"start": start, "end": idx, "fragment": frag, "len": len(frag)})
            start = None
    return spans


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=DB_DEFAULT)
    args = parser.parse_args()
    con = sqlite3.connect(args.db)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.executescript(
        """
        create table if not exists book34_differential_frontier_runs(
            run_id integer primary key autoincrement,
            created_at text not null,
            seam_count integer not null,
            unique_seam_count integer not null,
            decision text not null,
            next_action text not null,
            payload_json text not null
        );
        create table if not exists book34_differential_frontier_items(
            run_id integer not null,
            seam_rank integer not null,
            start_pos integer not null,
            end_pos integer not null,
            fragment text not null,
            fragment_len integer not null,
            corpus_occurrences integer not null,
            containing_books_json text not null,
            candidate_status text not null,
            evidence_json text not null,
            primary key(run_id, seam_rank)
        );
        """
    )
    books = {
        str(row["bookid"]): digits_only(str(row["digits"]))
        for row in cur.execute("select bookid, digits from sheet__books group by bookid").fetchall()
    }
    target = books["34"]
    controls = [books["17"], books["68"]]
    seams = maximal_absent_spans(target, controls)
    results = []
    for seam in seams:
        frag = seam["fragment"]
        containing = [bookid for bookid, digits in books.items() if frag in digits]
        occ = sum(digits.count(frag) for digits in books.values())
        status = "BOOK34_DIFFERENTIAL_UNIQUE_SEAM" if containing == ["34"] else "BOOK34_DIFFERENTIAL_SEAM_RECURRENT"
        results.append({**seam, "corpus_occurrences": occ, "containing_books": containing, "candidate_status": status})
    results.sort(key=lambda row: (-row["len"], row["start"]))
    unique = sum(1 for row in results if row["candidate_status"] == "BOOK34_DIFFERENTIAL_UNIQUE_SEAM")
    decision = "BOOK34_HAS_DIFFERENTIAL_SEAMS_AUDIT_ONLY" if results else "BOOK34_NO_DIFFERENTIAL_SEAMS_VS_CONTROLS"
    next_action = "Use only unique seams for next boundary-function probe; no gloss."
    cur.execute(
        "insert into book34_differential_frontier_runs(created_at,seam_count,unique_seam_count,decision,next_action,payload_json) values (?,?,?,?,?,?)",
        (now(), len(results), unique, decision, next_action, j({"results": results, "controls": ["17", "68"]})),
    )
    run_id = cur.lastrowid
    for rank, row in enumerate(results, start=1):
        cur.execute(
            "insert into book34_differential_frontier_items(run_id,seam_rank,start_pos,end_pos,fragment,fragment_len,corpus_occurrences,containing_books_json,candidate_status,evidence_json) values (?,?,?,?,?,?,?,?,?,?)",
            (run_id, rank, row["start"], row["end"], row["fragment"], row["len"], row["corpus_occurrences"], j(row["containing_books"]), row["candidate_status"], j(row)),
        )
    con.commit()
    print(json.dumps({"run_id": run_id, "decision": decision, "seam_count": len(results), "unique_seam_count": unique, "items": results[:20]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
