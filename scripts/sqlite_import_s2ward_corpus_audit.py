#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import sqlite3
from pathlib import Path
from typing import Any

DB_DEFAULT = "./data/bonelord_operational.sqlite"
ROOT_DEFAULT = "./tmp/external_corpus/s2ward_469/469-main"


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


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
    root = Path(args.root)
    books = [digits_only(x) for x in load_json(root / "books.json")]
    sorted_with_kharos = [digits_only(x) for x in load_json(root / "data/books_sorted_unique_with_kharos.json")]

    con = sqlite3.connect(args.db)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.executescript(
        """
        create table if not exists s2ward_corpus_audit_runs(
            run_id integer primary key autoincrement,
            created_at text not null,
            source_root text not null,
            books_count integer not null,
            sorted_with_kharos_count integer not null,
            exact_book_match_count integer not null,
            new_sorted_sequence_count integer not null,
            decision text not null,
            next_action text not null,
            payload_json text not null
        );
        create table if not exists s2ward_corpus_audit_items(
            run_id integer not null,
            source_set text not null,
            source_index integer not null,
            sequence_digits text not null,
            sequence_len integer not null,
            exact_sheet_bookid text,
            best_sheet_bookid text,
            best_lcs_len integer not null,
            best_lcs_text text not null,
            candidate_status text not null,
            evidence_json text not null,
            primary key(run_id, source_set, source_index)
        );
        """
    )
    sheet = [
        {"bookid": str(row["bookid"]), "digits": digits_only(str(row["digits"]))}
        for row in cur.execute("select bookid, digits from sheet__books order by cast(bookid as int)").fetchall()
    ]
    exact_by_digits: dict[str, list[str]] = {}
    for item in sheet:
        exact_by_digits.setdefault(item["digits"], []).append(item["bookid"])

    def classify(source_set: str, seqs: list[str]) -> list[dict[str, Any]]:
        out = []
        for idx, seq in enumerate(seqs):
            exact = exact_by_digits.get(seq, [])
            best = {"bookid": None, "lcs_len": 0, "lcs_text": ""}
            for item in sheet:
                lcs_len, lcs_text = longest_common_substring(seq, item["digits"])
                if lcs_len > best["lcs_len"]:
                    best = {"bookid": item["bookid"], "lcs_len": lcs_len, "lcs_text": lcs_text}
            status = "EXACT_SHEET_BOOK_DUPLICATE" if exact else "NEW_OR_REARRANGED_SEQUENCE_AUDIT_ONLY"
            if not exact and best["lcs_len"] >= min(40, len(seq)):
                status = "NEW_SEQUENCE_WITH_STRONG_SHEET_OVERLAP_AUDIT_ONLY"
            out.append(
                {
                    "source_set": source_set,
                    "source_index": idx,
                    "sequence_digits": seq,
                    "sequence_len": len(seq),
                    "exact_sheet_bookid": ",".join(exact) if exact else None,
                    "best_sheet_bookid": best["bookid"],
                    "best_lcs_len": best["lcs_len"],
                    "best_lcs_text": best["lcs_text"],
                    "candidate_status": status,
                }
            )
        return out

    items = classify("books_json", books) + classify("sorted_unique_with_kharos", sorted_with_kharos)
    exact_count = sum(1 for item in items if item["source_set"] == "books_json" and item["exact_sheet_bookid"])
    new_sorted = [item for item in items if item["source_set"] == "sorted_unique_with_kharos" and not item["exact_sheet_bookid"]]
    kharos_like = sorted(new_sorted, key=lambda item: (item["sequence_len"], item["best_lcs_len"]), reverse=True)[:10]
    decision = "S2WARD_CORPUS_IMPORTED_AUDIT_ONLY_NO_GLOSS"
    next_action = "Review new/rearranged s2ward sequences only as structural artifacts; no semantic promotion without exact meaning source."
    payload = {
        "root": str(root),
        "top_new_sorted_or_kharos": [
            {
                "source_index": item["source_index"],
                "sequence_len": item["sequence_len"],
                "best_sheet_bookid": item["best_sheet_bookid"],
                "best_lcs_len": item["best_lcs_len"],
                "candidate_status": item["candidate_status"],
                "preview": item["sequence_digits"][:100],
            }
            for item in kharos_like
        ],
    }
    cur.execute(
        "insert into s2ward_corpus_audit_runs(created_at,source_root,books_count,sorted_with_kharos_count,exact_book_match_count,new_sorted_sequence_count,decision,next_action,payload_json) values (?,?,?,?,?,?,?,?,?)",
        (now(), str(root), len(books), len(sorted_with_kharos), exact_count, len(new_sorted), decision, next_action, j(payload)),
    )
    run_id = cur.lastrowid
    for item in items:
        cur.execute(
            "insert into s2ward_corpus_audit_items(run_id,source_set,source_index,sequence_digits,sequence_len,exact_sheet_bookid,best_sheet_bookid,best_lcs_len,best_lcs_text,candidate_status,evidence_json) values (?,?,?,?,?,?,?,?,?,?,?)",
            (
                run_id,
                item["source_set"],
                item["source_index"],
                item["sequence_digits"],
                item["sequence_len"],
                item["exact_sheet_bookid"],
                item["best_sheet_bookid"],
                item["best_lcs_len"],
                item["best_lcs_text"],
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
                "books_count": len(books),
                "sorted_with_kharos_count": len(sorted_with_kharos),
                "exact_book_match_count": exact_count,
                "new_sorted_sequence_count": len(new_sorted),
                "top_new_sorted_or_kharos": payload["top_new_sorted_or_kharos"],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
