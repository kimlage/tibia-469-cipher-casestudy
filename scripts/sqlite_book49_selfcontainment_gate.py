#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import sqlite3
from collections import Counter
from typing import Any

DB_DEFAULT = "./data/bonelord_operational.sqlite"


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ngrams(tokens: list[str], n: int) -> list[tuple[str, ...]]:
    return [tuple(tokens[i : i + n]) for i in range(0, len(tokens) - n + 1)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=DB_DEFAULT)
    args = parser.parse_args()
    con = sqlite3.connect(args.db)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.executescript(
        """
        create table if not exists book49_selfcontainment_gate_runs(
            run_id integer primary key autoincrement,
            created_at text not null,
            bookid text not null,
            token_count integer not null,
            repeated_ngram_count integer not null,
            repeated_token_coverage real not null,
            external_note_present integer not null,
            decision text not null,
            functional_tag text not null,
            next_action text not null,
            payload_json text not null
        );
        """
    )
    row = cur.execute(
        """
        select tokens_json, symbol_text
        from row0_variant_book_tokens
        where run_id=(select max(run_id) from row0_variant_frontier_runs) and bookid='49'
        """
    ).fetchone()
    if not row:
        raise SystemExit("missing row0_variant_book_tokens for book 49")
    tokens = json.loads(row["tokens_json"])
    repeated = []
    covered = set()
    for n in range(3, 9):
        counts = Counter(ngrams(tokens, n))
        for gram, count in counts.items():
            if count > 1:
                positions = [i for i, candidate in enumerate(ngrams(tokens, n)) if candidate == gram]
                for pos in positions:
                    covered.update(range(pos, pos + n))
                repeated.append({"n": n, "gram": "".join(gram), "token_gram": list(gram), "count": count, "positions": positions})
    coverage = round(len(covered) / len(tokens), 3) if tokens else 0.0
    note = cur.execute(
        """
        select count(*) as c
        from s2ward_rearrange_line_map_items
        where run_id=(select max(run_id) from s2ward_rearrange_line_map_runs)
          and mapped_bookid='49'
          and lower(note) like '%selfcontainment%'
        """
    ).fetchone()["c"]
    external_note_present = 1 if note else 0
    decision = "BOOK49_SELF_CONTAINED_REPEAT_FORMULA_ACCEPT_AUDIT_SAFE" if coverage >= 0.55 and external_note_present else "BOOK49_SELF_CONTAINMENT_NOT_ENOUGH_FOR_TAG"
    tag = "SELF_CONTAINED_REPEAT_FORMULA_AUDIT_SAFE" if decision.endswith("ACCEPT_AUDIT_SAFE") else ""
    next_action = "Promote functional tag only; keep gloss disallowed." if tag else "Keep book49 blocked until stronger evidence."
    payload = {
        "symbol_text": row["symbol_text"],
        "repeated_ngrams": sorted(repeated, key=lambda item: (-item["n"], -item["count"], item["gram"]))[:50],
        "covered_positions": sorted(covered),
        "external_note_present": external_note_present,
    }
    cur.execute(
        "insert into book49_selfcontainment_gate_runs(created_at,bookid,token_count,repeated_ngram_count,repeated_token_coverage,external_note_present,decision,functional_tag,next_action,payload_json) values (?,?,?,?,?,?,?,?,?,?)",
        (now(), "49", len(tokens), len(repeated), coverage, external_note_present, decision, tag, next_action, j(payload)),
    )
    run_id = cur.lastrowid
    con.commit()
    print(json.dumps({"run_id": run_id, "decision": decision, "functional_tag": tag, "token_count": len(tokens), "repeated_ngram_count": len(repeated), "coverage": coverage, "external_note_present": external_note_present, "top": payload["repeated_ngrams"][:10]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
