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
    lex_run = cur.execute("select max(run_id) from minimal_external_semantic_lexicon_v1_runs").fetchone()[0]
    direct = {
        str(row["key"]): str(row["value"])
        for row in cur.execute(
            "select key,value from minimal_external_semantic_lexicon_v1_items where run_id=? and item_type='code_letter'",
            (lex_run,),
        )
    }
    cur.executescript(
        """
        create table if not exists minimal_lexicon_book_coverage_probe_runs(
            run_id integer primary key autoincrement,
            created_at text not null,
            source_lexicon_run_id integer not null,
            book_count integer not null,
            anomalous_book_count integer not null,
            decision text not null,
            next_action text not null,
            payload_json text not null
        );
        create table if not exists minimal_lexicon_book_coverage_probe_items(
            run_id integer not null,
            bookid text not null,
            token_count integer not null,
            direct_code_hit_count integer not null,
            direct_code_hit_ratio real not null,
            projected_letters text not null,
            candidate_status text not null,
            evidence_json text not null,
            primary key(run_id, bookid)
        );
        """
    )
    results = []
    for row in cur.execute(
        "select bookid,reconstructed_code_stream from row0_code_symbol_probe_books where run_id=(select max(run_id) from row0_code_symbol_probe_runs) order by cast(bookid as int)"
    ):
        codes = str(row["reconstructed_code_stream"]).split()
        letters = [direct.get(code, ".") for code in codes]
        hits = sum(1 for x in letters if x != ".")
        ratio = round(hits / len(codes), 3) if codes else 0.0
        status = "MINIMAL_LEXICON_SPARSE_NO_BOOK_GLOSS"
        if ratio >= 0.35 and hits >= 20:
            status = "MINIMAL_LEXICON_DENSE_BOOK_AUDIT_CANDIDATE"
        results.append(
            {
                "bookid": str(row["bookid"]),
                "token_count": len(codes),
                "direct_code_hit_count": hits,
                "direct_code_hit_ratio": ratio,
                "projected_letters": "".join(letters),
                "candidate_status": status,
            }
        )
    anomalous = [row for row in results if row["candidate_status"].endswith("AUDIT_CANDIDATE")]
    decision = "MINIMAL_LEXICON_BOOK_COVERAGE_HAS_AUDIT_CANDIDATES" if anomalous else "MINIMAL_LEXICON_BOOK_COVERAGE_SPARSE_NO_GLOSS"
    next_action = "Audit dense candidates only; do not translate books from sparse direct-letter coverage."
    cur.execute(
        "insert into minimal_lexicon_book_coverage_probe_runs(created_at,source_lexicon_run_id,book_count,anomalous_book_count,decision,next_action,payload_json) values (?,?,?,?,?,?,?)",
        (now(), lex_run, len(results), len(anomalous), decision, next_action, j({"direct_codes": direct, "top": sorted(results, key=lambda r: r["direct_code_hit_ratio"], reverse=True)[:15]})),
    )
    run_id = cur.lastrowid
    for row in results:
        cur.execute(
            "insert into minimal_lexicon_book_coverage_probe_items(run_id,bookid,token_count,direct_code_hit_count,direct_code_hit_ratio,projected_letters,candidate_status,evidence_json) values (?,?,?,?,?,?,?,?)",
            (run_id, row["bookid"], row["token_count"], row["direct_code_hit_count"], row["direct_code_hit_ratio"], row["projected_letters"], row["candidate_status"], j(row)),
        )
    con.commit()
    print(json.dumps({"run_id": run_id, "decision": decision, "anomalous_book_count": len(anomalous), "top": sorted(results, key=lambda r: r["direct_code_hit_ratio"], reverse=True)[:10]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
