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
    con = sqlite3.connect(args.db)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    sheet = [
        {"bookid": str(row["bookid"]), "digits": digits_only(str(row["digits"]))}
        for row in cur.execute("select bookid, digits from sheet__books order by cast(bookid as int)").fetchall()
    ]
    cur.executescript(
        """
        create table if not exists s2ward_rearrange_line_map_runs(
            run_id integer primary key autoincrement,
            created_at text not null,
            line_count integer not null,
            residual_line_count integer not null,
            decision text not null,
            next_action text not null,
            payload_json text not null
        );
        create table if not exists s2ward_rearrange_line_map_items(
            run_id integer not null,
            line_no integer not null,
            label text not null,
            mapped_bookid text,
            extracted_digit_len integer not null,
            lcs_len integer not null,
            lcs_text text not null,
            note text not null,
            is_residual integer not null,
            candidate_status text not null,
            evidence_json text not null,
            primary key(run_id, line_no, label)
        );
        """
    )
    items = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        match = re.match(r"\[(B\d+[A-Z]?)\]\s*(.*)", stripped)
        if not match:
            continue
        label = match.group(1)
        rest = match.group(2)
        digit_part = rest.split("--", 1)[0]
        seq = digits_only(digit_part.replace("+", ""))
        if len(seq) < 20:
            continue
        best = {"bookid": None, "lcs_len": 0, "lcs_text": ""}
        for book in sheet:
            lcs_len, lcs_text = longest_common_substring(seq, book["digits"])
            if lcs_len > best["lcs_len"]:
                best = {"bookid": book["bookid"], "lcs_len": lcs_len, "lcs_text": lcs_text}
        is_residual = 1 if best["bookid"] in {"4", "34", "49"} else 0
        note = stripped[stripped.find("--") + 2 :].strip() if "--" in stripped else ""
        status = "S2WARD_LINE_MAPS_RESIDUAL_AUDIT_ONLY" if is_residual else "S2WARD_LINE_MAPPED"
        if is_residual and best["lcs_len"] < min(60, len(seq)):
            status = "S2WARD_LINE_FRAGMENTARY_RESIDUAL_MATCH_AUDIT_ONLY"
        items.append(
            {
                "line_no": line_no,
                "label": label,
                "mapped_bookid": best["bookid"],
                "extracted_digit_len": len(seq),
                "lcs_len": best["lcs_len"],
                "lcs_text": best["lcs_text"],
                "note": note,
                "is_residual": is_residual,
                "candidate_status": status,
            }
        )
    residuals = [item for item in items if item["is_residual"]]
    decision = "S2WARD_REARRANGE_LINES_CONTAIN_RESIDUAL_NOTES_AUDIT_ONLY" if residuals else "S2WARD_REARRANGE_LINES_NO_RESIDUAL_SIGNAL"
    next_action = "Use residual notes to propose narrow structural probes only; no gloss or promotion from notes alone."
    cur.execute(
        "insert into s2ward_rearrange_line_map_runs(created_at,line_count,residual_line_count,decision,next_action,payload_json) values (?,?,?,?,?,?)",
        (now(), len(items), len(residuals), decision, next_action, j({"residuals": residuals})),
    )
    run_id = cur.lastrowid
    for item in items:
        cur.execute(
            "insert into s2ward_rearrange_line_map_items(run_id,line_no,label,mapped_bookid,extracted_digit_len,lcs_len,lcs_text,note,is_residual,candidate_status,evidence_json) values (?,?,?,?,?,?,?,?,?,?,?)",
            (
                run_id,
                item["line_no"],
                item["label"],
                item["mapped_bookid"],
                item["extracted_digit_len"],
                item["lcs_len"],
                item["lcs_text"],
                item["note"],
                item["is_residual"],
                item["candidate_status"],
                j(item),
            ),
        )
    con.commit()
    print(json.dumps({"run_id": run_id, "decision": decision, "line_count": len(items), "residuals": residuals}, ensure_ascii=False))


if __name__ == "__main__":
    main()
