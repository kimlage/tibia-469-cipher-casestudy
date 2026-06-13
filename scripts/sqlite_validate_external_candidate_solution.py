#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "bonelord_operational.sqlite"


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS external_candidate_validation_runs (
          run_id INTEGER PRIMARY KEY AUTOINCREMENT,
          created_at TEXT NOT NULL,
          candidate_run_id INTEGER NOT NULL,
          book_count INTEGER NOT NULL,
          mapping_count INTEGER NOT NULL,
          total_digits INTEGER NOT NULL,
          odd_length_books INTEGER NOT NULL,
          total_pairs INTEGER NOT NULL,
          mapped_pairs INTEGER NOT NULL,
          unmapped_pairs INTEGER NOT NULL,
          unique_pairs INTEGER NOT NULL,
          unique_unmapped_pairs INTEGER NOT NULL,
          pair_coverage_pct REAL NOT NULL,
          payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS external_candidate_validation_books (
          run_id INTEGER NOT NULL,
          bookid TEXT NOT NULL,
          digit_len INTEGER NOT NULL,
          odd_length INTEGER NOT NULL,
          pair_count INTEGER NOT NULL,
          mapped_pair_count INTEGER NOT NULL,
          unmapped_pair_count INTEGER NOT NULL,
          unmapped_pairs_json TEXT NOT NULL,
          decoded_letters TEXT NOT NULL,
          PRIMARY KEY (run_id, bookid)
        );
        """
    )


def latest_candidate_run(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT MAX(run_id) AS run_id FROM external_candidate_solution_runs").fetchone()
    if not row or row["run_id"] is None:
        raise SystemExit("no external candidate solution run found")
    return int(row["run_id"])


def validate(conn: sqlite3.Connection, candidate_run_id: int | None = None) -> dict[str, object]:
    ensure_schema(conn)
    if candidate_run_id is None:
        candidate_run_id = latest_candidate_run(conn)
    mapping = {
        str(row["code"]): str(row["letter"])
        for row in conn.execute(
            "SELECT code, letter FROM external_candidate_solution_mapping WHERE run_id=?",
            (candidate_run_id,),
        )
    }
    rows = conn.execute(
        """
        SELECT b.bookid, b.digits
        FROM sheet__books b
        WHERE b.__export_id=(SELECT MAX(__export_id) FROM sheet__books)
        ORDER BY CAST(b.bookid AS INTEGER)
        """
    ).fetchall()

    book_results = []
    pair_counter: Counter[str] = Counter()
    unmapped_counter: Counter[str] = Counter()
    total_digits = 0
    total_pairs = 0
    mapped_pairs = 0
    unmapped_pairs = 0
    odd_books = 0
    for row in rows:
        digits = re.sub(r"\D+", "", str(row["digits"] or ""))
        total_digits += len(digits)
        odd = len(digits) % 2
        odd_books += odd
        pairs = [digits[i : i + 2] for i in range(0, len(digits) - 1, 2)]
        decoded = []
        local_unmapped = []
        for pair in pairs:
            pair_counter[pair] += 1
            if pair in mapping:
                mapped_pairs += 1
                decoded.append(mapping[pair])
            else:
                unmapped_pairs += 1
                unmapped_counter[pair] += 1
                local_unmapped.append(pair)
                decoded.append("?")
        total_pairs += len(pairs)
        book_results.append(
            {
                "bookid": str(row["bookid"]),
                "digit_len": len(digits),
                "odd_length": odd,
                "pair_count": len(pairs),
                "mapped_pair_count": len(pairs) - len(local_unmapped),
                "unmapped_pair_count": len(local_unmapped),
                "unmapped_pairs": sorted(Counter(local_unmapped).items()),
                "decoded_letters": "".join(decoded),
            }
        )

    pair_coverage_pct = round(100.0 * mapped_pairs / total_pairs, 4) if total_pairs else 0.0
    cur = conn.execute(
        """
        INSERT INTO external_candidate_validation_runs (
          created_at, candidate_run_id, book_count, mapping_count, total_digits,
          odd_length_books, total_pairs, mapped_pairs, unmapped_pairs,
          unique_pairs, unique_unmapped_pairs, pair_coverage_pct, payload_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            now(),
            candidate_run_id,
            len(rows),
            len(mapping),
            total_digits,
            odd_books,
            total_pairs,
            mapped_pairs,
            unmapped_pairs,
            len(pair_counter),
            len(unmapped_counter),
            pair_coverage_pct,
            json.dumps(
                {
                    "top_pairs": pair_counter.most_common(20),
                    "unmapped_pairs": unmapped_counter.most_common(),
                },
                ensure_ascii=True,
                sort_keys=True,
            ),
        ),
    )
    run_id = int(cur.lastrowid)
    for item in book_results:
        conn.execute(
            """
            INSERT INTO external_candidate_validation_books (
              run_id, bookid, digit_len, odd_length, pair_count, mapped_pair_count,
              unmapped_pair_count, unmapped_pairs_json, decoded_letters
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                item["bookid"],
                item["digit_len"],
                item["odd_length"],
                item["pair_count"],
                item["mapped_pair_count"],
                item["unmapped_pair_count"],
                json.dumps(item["unmapped_pairs"], ensure_ascii=True),
                item["decoded_letters"],
            ),
        )
    conn.commit()
    return {
        "recorded_run_id": run_id,
        "candidate_run_id": candidate_run_id,
        "book_count": len(rows),
        "mapping_count": len(mapping),
        "total_digits": total_digits,
        "odd_length_books": odd_books,
        "total_pairs": total_pairs,
        "mapped_pairs": mapped_pairs,
        "unmapped_pairs": unmapped_pairs,
        "unique_pairs": len(pair_counter),
        "unique_unmapped_pairs": len(unmapped_counter),
        "pair_coverage_pct": pair_coverage_pct,
        "unmapped_pairs_top": unmapped_counter.most_common(20),
        "odd_bookids": [item["bookid"] for item in book_results if item["odd_length"]],
        "sample_decoded": [
            {
                "bookid": item["bookid"],
                "decoded_letters": item["decoded_letters"][:120],
                "unmapped_pair_count": item["unmapped_pair_count"],
            }
            for item in book_results[:8]
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DB_PATH)
    parser.add_argument("--candidate-run-id", type=int)
    args = parser.parse_args()
    with connect(args.db) as conn:
        result = validate(conn, args.candidate_run_id)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
