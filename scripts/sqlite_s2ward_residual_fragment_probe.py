#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import re
import sqlite3
from collections import Counter
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


def build_code_symbol(cur: sqlite3.Cursor) -> dict[str, str]:
    mapping = {}
    for row in cur.execute(
        """
        select code, symbol
        from row0_code_symbol_counts
        where run_id=(select max(run_id) from row0_code_symbol_probe_runs)
        order by code, occurrence_count desc
        """
    ):
        mapping.setdefault(str(row["code"]), str(row["symbol"]))
    return mapping


def greedy_project(fragment: str, mapping: dict[str, str]) -> dict[str, Any]:
    # Greedy is enough here: fragment audit should expose whether the manual
    # bracket starts on known 2-digit boundaries or degenerates into omitted
    # zero codes. It is not a promotion parser.
    i = 0
    tokens = []
    while i < len(fragment):
        two = fragment[i : i + 2]
        if len(two) == 2 and two in mapping:
            tokens.append({"code": two, "symbol": mapping[two], "omitted": 0})
            i += 2
            continue
        one = "0" + fragment[i : i + 1]
        if one in mapping:
            tokens.append({"code": one, "symbol": mapping[one], "omitted": 1})
            i += 1
            continue
        return {"valid": 0, "symbol_text": "", "tokens": tokens, "omitted_ratio": 0.0}
    omitted_ratio = sum(t["omitted"] for t in tokens) / len(tokens) if tokens else 0.0
    return {"valid": 1, "symbol_text": "".join(t["symbol"] for t in tokens), "tokens": tokens, "omitted_ratio": round(omitted_ratio, 3)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=DB_DEFAULT)
    parser.add_argument("--root", default=ROOT_DEFAULT)
    args = parser.parse_args()
    rearrange = (Path(args.root) / "05-rearrange.txt").read_text(encoding="utf-8")
    con = sqlite3.connect(args.db)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.executescript(
        """
        create table if not exists s2ward_residual_fragment_probe_runs(
            run_id integer primary key autoincrement,
            created_at text not null,
            fragment_count integer not null,
            unique_fragment_count integer not null,
            recurrent_fragment_count integer not null,
            decision text not null,
            next_action text not null,
            payload_json text not null
        );
        create table if not exists s2ward_residual_fragment_probe_items(
            run_id integer not null,
            bookid text not null,
            label text not null,
            fragment text not null,
            fragment_len integer not null,
            corpus_occurrences integer not null,
            containing_books_json text not null,
            row0_valid integer not null,
            row0_symbol_text text not null,
            omitted_ratio real not null,
            candidate_status text not null,
            evidence_json text not null,
            primary key(run_id, bookid, label, fragment)
        );
        """
    )
    sheet = [
        {"bookid": str(row["bookid"]), "digits": digits_only(str(row["digits"]))}
        for row in cur.execute("select bookid, digits from sheet__books order by cast(bookid as int)").fetchall()
    ]
    exact_by_digits = {item["digits"]: item["bookid"] for item in sheet}
    mapping = build_code_symbol(cur)
    residual_lines = []
    for line in rearrange.splitlines():
        if not line.strip().startswith("[B"):
            continue
        line_digits = digits_only(line.split("--", 1)[0].replace("+", ""))
        bookid = exact_by_digits.get(line_digits)
        if bookid not in {"4", "34", "49"}:
            # Allow long lines with inserted gaps to map by containment.
            best = None
            for item in sheet:
                if len(line_digits) >= 80 and (line_digits in item["digits"] or item["digits"] in line_digits):
                    best = item["bookid"]
                    break
            bookid = best
        if bookid in {"4", "34", "49"}:
            label = re.match(r"\[(B\d+[A-Z]?)\]", line.strip()).group(1)  # type: ignore[union-attr]
            residual_lines.append({"bookid": bookid, "label": label, "line": line})
    fragments = []
    for item in residual_lines:
        for raw in re.findall(r"\[([^\]]+)\]", item["line"]):
            frag = digits_only(raw)
            if len(frag) < 3:
                continue
            fragments.append({"bookid": item["bookid"], "label": item["label"], "fragment": frag})
    counts = Counter()
    containing: dict[str, set[str]] = {}
    for frag_item in fragments:
        frag = frag_item["fragment"]
        for book in sheet:
            occurrences = book["digits"].count(frag)
            if occurrences:
                counts[frag] += occurrences
                containing.setdefault(frag, set()).add(book["bookid"])
    results = []
    for frag_item in fragments:
        frag = frag_item["fragment"]
        projection = greedy_project(frag, mapping)
        occ = counts.get(frag, 0)
        if projection["valid"] and projection["omitted_ratio"] > 0.35:
            status = "DEGENERATE_ROW0_FRAGMENT_AUDIT_ONLY"
        elif occ == 1:
            status = "UNIQUE_RESIDUAL_FRAGMENT_AUDIT_ONLY"
        elif occ > 1:
            status = "RECURRENT_FRAGMENT_AUDIT_ONLY"
        else:
            status = "FRAGMENT_NOT_FOUND_AFTER_DIGIT_CLEANING"
        results.append({**frag_item, "occ": occ, "books": sorted(containing.get(frag, set()), key=lambda x: int(x)), "projection": projection, "status": status})
    unique_count = sum(1 for row in results if row["occ"] == 1)
    recurrent_count = sum(1 for row in results if row["occ"] > 1)
    decision = "S2WARD_RESIDUAL_FRAGMENTS_MATERIALIZED_AUDIT_ONLY"
    next_action = "Use unique fragments as residual labels and recurrent fragments as structural controls; no gloss."
    cur.execute(
        "insert into s2ward_residual_fragment_probe_runs(created_at,fragment_count,unique_fragment_count,recurrent_fragment_count,decision,next_action,payload_json) values (?,?,?,?,?,?,?)",
        (now(), len(results), unique_count, recurrent_count, decision, next_action, j({"results": results})),
    )
    run_id = cur.lastrowid
    for row in results:
        cur.execute(
            "insert into s2ward_residual_fragment_probe_items(run_id,bookid,label,fragment,fragment_len,corpus_occurrences,containing_books_json,row0_valid,row0_symbol_text,omitted_ratio,candidate_status,evidence_json) values (?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                run_id,
                row["bookid"],
                row["label"],
                row["fragment"],
                len(row["fragment"]),
                row["occ"],
                j(row["books"]),
                row["projection"]["valid"],
                row["projection"]["symbol_text"],
                row["projection"]["omitted_ratio"],
                row["status"],
                j(row),
            ),
        )
    con.commit()
    print(json.dumps({"run_id": run_id, "decision": decision, "fragment_count": len(results), "unique_count": unique_count, "recurrent_count": recurrent_count, "items": results}, ensure_ascii=False))


if __name__ == "__main__":
    main()
