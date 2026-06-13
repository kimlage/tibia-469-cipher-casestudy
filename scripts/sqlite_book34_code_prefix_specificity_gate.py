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


def contains_ngram(seq: list[str], gram: tuple[str, ...]) -> bool:
    n = len(gram)
    return any(tuple(seq[i : i + n]) == gram for i in range(0, len(seq) - n + 1))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=DB_DEFAULT)
    args = parser.parse_args()
    con = sqlite3.connect(args.db)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.executescript(
        """
        create table if not exists book34_code_prefix_specificity_gate_runs(
            run_id integer primary key autoincrement,
            created_at text not null,
            best_unique_code_prefix_len integer not null,
            best_unique_symbol_prefix_len integer not null,
            code_prefix_owners_json text not null,
            symbol_prefix_owners_json text not null,
            decision text not null,
            recommended_tag text not null,
            next_action text not null,
            payload_json text not null
        );
        """
    )
    code_rows = cur.execute(
        """
        select bookid, reconstructed_code_stream, decodedbase
        from row0_code_symbol_probe_books
        where run_id=(select max(run_id) from row0_code_symbol_probe_runs)
        order by cast(bookid as int)
        """
    ).fetchall()
    code_by_book = {str(row["bookid"]): str(row["reconstructed_code_stream"]).split() for row in code_rows}
    symbol_by_book = {str(row["bookid"]): list(str(row["decodedbase"])) for row in code_rows}
    target_codes = code_by_book["34"]
    target_symbols = symbol_by_book["34"]
    code_results = []
    symbol_results = []
    for n in range(3, min(25, len(target_codes)) + 1):
        gram = tuple(target_codes[:n])
        owners = [bookid for bookid, seq in code_by_book.items() if contains_ngram(seq, gram)]
        code_results.append({"n": n, "gram": list(gram), "owners": owners, "owner_count": len(owners)})
    for n in range(3, min(25, len(target_symbols)) + 1):
        gram = tuple(target_symbols[:n])
        owners = [bookid for bookid, seq in symbol_by_book.items() if contains_ngram(seq, gram)]
        symbol_results.append({"n": n, "gram": "".join(gram), "owners": owners, "owner_count": len(owners)})
    unique_code = [row for row in code_results if row["owners"] == ["34"]]
    unique_symbol = [row for row in symbol_results if row["owners"] == ["34"]]
    best_code_len = max((row["n"] for row in unique_code), default=0)
    best_symbol_len = max((row["n"] for row in unique_symbol), default=0)
    if best_code_len >= 5 and best_symbol_len >= 5:
        decision = "BOOK34_UNIQUE_PREFIX_HEADER_ACCEPT_FUNCTIONAL_NO_GLOSS"
        tag = "UNIQUE_PREFIX_HEADER_FOR_SCRAMBLED_ASSEMBLY_AUDIT_SAFE"
        next_action = "Promote Book34 functional tag only; keep semantic gloss disallowed."
    else:
        decision = "BOOK34_UNIQUE_PREFIX_HEADER_BLOCKED"
        tag = ""
        next_action = "Keep Book34 blocked; unique prefix is not strong enough at code/symbol level."
    payload = {
        "book34_code_prefix": target_codes[:25],
        "book34_symbol_prefix": "".join(target_symbols[:25]),
        "code_results": code_results,
        "symbol_results": symbol_results,
    }
    cur.execute(
        "insert into book34_code_prefix_specificity_gate_runs(created_at,best_unique_code_prefix_len,best_unique_symbol_prefix_len,code_prefix_owners_json,symbol_prefix_owners_json,decision,recommended_tag,next_action,payload_json) values (?,?,?,?,?,?,?,?,?)",
        (
            now(),
            best_code_len,
            best_symbol_len,
            j(code_results[:12]),
            j(symbol_results[:12]),
            decision,
            tag,
            next_action,
            j(payload),
        ),
    )
    run_id = cur.lastrowid
    con.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "recommended_tag": tag,
                "best_unique_code_prefix_len": best_code_len,
                "best_unique_symbol_prefix_len": best_symbol_len,
                "code_prefix_sample": code_results[:12],
                "symbol_prefix_sample": symbol_results[:12],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
