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


def longest_common_substring(a: str, b: str) -> tuple[int, str]:
    prev = [0] * (len(b) + 1)
    best_len = 0
    best_end = 0
    for i, ca in enumerate(a, 1):
        cur = [0] * (len(b) + 1)
        for k, cb in enumerate(b, 1):
            if ca == cb:
                cur[k] = prev[k - 1] + 1
                if cur[k] > best_len:
                    best_len = cur[k]
                    best_end = i
        prev = cur
    return best_len, a[best_end - best_len : best_end]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=DB_DEFAULT)
    parser.add_argument("--root", default=ROOT_DEFAULT)
    args = parser.parse_args()
    text = (Path(args.root) / "05-rearrange.txt").read_text(encoding="utf-8")
    b63_line = next((line for line in text.splitlines() if line.strip().startswith("[B63]")), "")
    main_part = re.sub(r"^\s*\[B63\]\s*", "", b63_line).split("--", 1)[0]
    b63_main_digits = digits_only(main_part.replace("+", ""))
    bracket_fragments = [digits_only(raw) for raw in re.findall(r"\[([^\]]+)\]", b63_line) if len(digits_only(raw)) >= 3]

    con = sqlite3.connect(args.db)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.executescript(
        """
        create table if not exists book34_ordered_assembly_control_gate_runs(
            run_id integer primary key autoincrement,
            created_at text not null,
            b63_main_len integer not null,
            book34_len integer not null,
            book34_prefix_match integer not null,
            control_max_lcs_ratio real not null,
            fragment_specific_count integer not null,
            decision text not null,
            next_action text not null,
            payload_json text not null
        );
        """
    )
    books = {
        str(row["bookid"]): digits_only(str(row["digits"]))
        for row in cur.execute("select bookid, digits from sheet__books where cast(bookid as int) in (17,34,68) group by bookid").fetchall()
    }
    book34 = books["34"]
    prefix_match = 1 if b63_main_digits.startswith(book34) else 0
    controls = []
    for bookid in ["17", "68"]:
        lcs_len, lcs_text = longest_common_substring(b63_main_digits, books[bookid])
        controls.append({"bookid": bookid, "book_len": len(books[bookid]), "lcs_len": lcs_len, "lcs_ratio": round(lcs_len / len(book34), 3), "lcs_text": lcs_text[:120]})
    control_max = max(item["lcs_ratio"] for item in controls)
    fragment_specific = 0
    fragment_evidence = []
    for frag in bracket_fragments:
        in34 = frag in book34
        in_controls = [bookid for bookid in ["17", "68"] if frag in books[bookid]]
        if in34 and not in_controls:
            fragment_specific += 1
        fragment_evidence.append({"fragment": frag, "in_book34": in34, "in_controls": in_controls})
    if prefix_match and control_max < 0.5 and fragment_specific >= 2:
        decision = "BOOK34_ORDERED_ASSEMBLY_ACCEPT_FUNCTIONAL_TAG_NO_GLOSS"
        next_action = "Promote ordered scrambled assembly functional tag."
    else:
        decision = "BOOK34_ORDERED_ASSEMBLY_BLOCKED_BY_CONTROLS"
        next_action = "Keep Book34 blocked; require stronger boundary-specific or external exact evidence."
    payload = {
        "b63_line": b63_line,
        "b63_main_digits": b63_main_digits,
        "book34_digits": book34,
        "controls": controls,
        "fragments": fragment_evidence,
    }
    cur.execute(
        "insert into book34_ordered_assembly_control_gate_runs(created_at,b63_main_len,book34_len,book34_prefix_match,control_max_lcs_ratio,fragment_specific_count,decision,next_action,payload_json) values (?,?,?,?,?,?,?,?,?)",
        (now(), len(b63_main_digits), len(book34), prefix_match, control_max, fragment_specific, decision, next_action, j(payload)),
    )
    run_id = cur.lastrowid
    con.commit()
    print(json.dumps({"run_id": run_id, "decision": decision, "b63_main_len": len(b63_main_digits), "book34_len": len(book34), "book34_prefix_match": prefix_match, "control_max_lcs_ratio": control_max, "fragment_specific_count": fragment_specific, "controls": controls, "fragments": fragment_evidence}, ensure_ascii=False))


if __name__ == "__main__":
    main()
