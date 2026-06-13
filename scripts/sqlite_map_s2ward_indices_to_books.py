#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import re
import sqlite3
from pathlib import Path
from typing import Any

DB_DEFAULT = "./data/bonelord_operational.sqlite"
ROOT_DEFAULT = "./tmp/external_corpus/s2ward_469/469-main"


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def digits_only(value: str) -> str:
    return "".join(ch for ch in value if ch.isdigit())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=DB_DEFAULT)
    parser.add_argument("--root", default=ROOT_DEFAULT)
    args = parser.parse_args()
    root = Path(args.root)
    books = [digits_only(x) for x in json.loads((root / "books.json").read_text(encoding="utf-8"))]
    rearrange = (root / "05-rearrange.txt").read_text(encoding="utf-8")

    notes_by_index: dict[int, list[str]] = {}
    for line in rearrange.splitlines():
        match = re.match(r"\[B\s*(\d+)[A-Z]?\]", line.strip())
        if not match:
            continue
        idx = int(match.group(1))
        note = line.strip()
        if "--" in note or "special" in note.lower() or "scramb" in note.lower() or "self" in note.lower() or "469" in note:
            notes_by_index.setdefault(idx, []).append(note[:500])

    con = sqlite3.connect(args.db)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.executescript(
        """
        create table if not exists s2ward_index_book_map_runs(
            run_id integer primary key autoincrement,
            created_at text not null,
            mapped_count integer not null,
            noted_count integer not null,
            residual_note_count integer not null,
            decision text not null,
            next_action text not null,
            payload_json text not null
        );
        create table if not exists s2ward_index_book_map_items(
            run_id integer not null,
            s2ward_index integer not null,
            bookid text,
            sequence_len integer not null,
            notes_json text not null,
            is_residual integer not null,
            candidate_status text not null,
            evidence_json text not null,
            primary key(run_id, s2ward_index)
        );
        """
    )
    exact = {
        digits_only(str(row["digits"])): str(row["bookid"])
        for row in cur.execute("select bookid, digits from sheet__books").fetchall()
    }
    items = []
    for idx, seq in enumerate(books, start=1):
        bookid = exact.get(seq)
        notes = notes_by_index.get(idx, [])
        is_residual = 1 if bookid in {"4", "34", "49"} else 0
        status = "RESIDUAL_HAS_S2WARD_REARRANGE_NOTE_AUDIT_ONLY" if is_residual and notes else "S2WARD_INDEX_MAPPED"
        if is_residual and not notes:
            status = "RESIDUAL_MAPPED_NO_S2WARD_SPECIAL_NOTE"
        items.append(
            {
                "s2ward_index": idx,
                "bookid": bookid,
                "sequence_len": len(seq),
                "notes": notes,
                "is_residual": is_residual,
                "candidate_status": status,
            }
        )
    residual_notes = [item for item in items if item["is_residual"] and item["notes"]]
    decision = "S2WARD_NOTES_MAP_TO_RESIDUALS_AUDIT_ONLY" if residual_notes else "S2WARD_NOTES_NO_RESIDUAL_BREAKTHROUGH"
    next_action = "Use s2ward residual notes as hypothesis labels only; require SQL probe before any structural promotion."
    cur.execute(
        "insert into s2ward_index_book_map_runs(created_at,mapped_count,noted_count,residual_note_count,decision,next_action,payload_json) values (?,?,?,?,?,?,?)",
        (
            now(),
            sum(1 for item in items if item["bookid"]),
            sum(1 for item in items if item["notes"]),
            len(residual_notes),
            decision,
            next_action,
            j({"residual_notes": residual_notes, "notes_by_index": notes_by_index}),
        ),
    )
    run_id = cur.lastrowid
    for item in items:
        cur.execute(
            "insert into s2ward_index_book_map_items(run_id,s2ward_index,bookid,sequence_len,notes_json,is_residual,candidate_status,evidence_json) values (?,?,?,?,?,?,?,?)",
            (
                run_id,
                item["s2ward_index"],
                item["bookid"],
                item["sequence_len"],
                j(item["notes"]),
                item["is_residual"],
                item["candidate_status"],
                j(item),
            ),
        )
    con.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "mapped_count": sum(1 for item in items if item["bookid"]),
                "noted_count": sum(1 for item in items if item["notes"]),
                "residual_notes": residual_notes,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
