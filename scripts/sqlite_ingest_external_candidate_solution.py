#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "bonelord_operational.sqlite"
REPO = "https://github.com/arturoornelasb/tibia-bonelord-469-cipher"
RAW = "https://raw.githubusercontent.com/arturoornelasb/tibia-bonelord-469-cipher/master"


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def fetch_text(url: str) -> str:
    with urllib.request.urlopen(url, timeout=30) as resp:
        return resp.read().decode("utf-8")


def connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS external_candidate_solution_runs (
          run_id INTEGER PRIMARY KEY AUTOINCREMENT,
          created_at TEXT NOT NULL,
          source_name TEXT NOT NULL,
          repo_url TEXT NOT NULL,
          mapping_count INTEGER NOT NULL,
          book_count INTEGER NOT NULL,
          narrative_book_count INTEGER NOT NULL,
          exact_digit_index_matches INTEGER NOT NULL,
          exact_digit_any_matches INTEGER NOT NULL,
          payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS external_candidate_solution_mapping (
          run_id INTEGER NOT NULL,
          code TEXT NOT NULL,
          letter TEXT NOT NULL,
          PRIMARY KEY (run_id, code)
        );

        CREATE TABLE IF NOT EXISTS external_candidate_solution_books (
          run_id INTEGER NOT NULL,
          external_book_id INTEGER NOT NULL,
          local_bookid TEXT,
          exact_index_match INTEGER NOT NULL,
          exact_any_match INTEGER NOT NULL,
          digit_len INTEGER NOT NULL,
          local_digit_len INTEGER,
          coverage_pct REAL,
          decoded_chars INTEGER,
          decoded_german TEXT,
          english TEXT,
          spanish TEXT,
          payload_json TEXT NOT NULL,
          PRIMARY KEY (run_id, external_book_id)
        );
        """
    )


def normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def parse_narrative(text: str) -> dict[int, dict[str, Any]]:
    pattern = re.compile(
        r"### Book\s+(\d+)\s+\((\d+)%\s+\|\s+(\d+)\s+chars\)\s+"
        r"\*\*Decoded German:\*\*\s*>\s*(.*?)\s+"
        r"\*\*English:\*\*\s*>\s*(.*?)\s+"
        r"\*\*Espanol:\*\*\s*>\s*(.*?)(?=\s+---\s+### Book|\s+---\s+##|\Z)",
        re.DOTALL,
    )
    parsed: dict[int, dict[str, Any]] = {}
    for match in pattern.finditer(text):
        book_id = int(match.group(1))
        parsed[book_id] = {
            "coverage_pct": float(match.group(2)),
            "decoded_chars": int(match.group(3)),
            "decoded_german": normalize_ws(match.group(4)),
            "english": normalize_ws(match.group(5)),
            "spanish": normalize_ws(match.group(6)),
        }
    return parsed


def local_digits(conn: sqlite3.Connection) -> dict[str, str]:
    rows = conn.execute(
        """
        SELECT bookid, digits
        FROM sheet__books
        WHERE __export_id=(SELECT MAX(__export_id) FROM sheet__books)
        ORDER BY CAST(bookid AS INTEGER)
        """
    ).fetchall()
    return {str(row["bookid"]): re.sub(r"\D+", "", str(row["digits"] or "")) for row in rows}


def ingest(conn: sqlite3.Connection) -> dict[str, Any]:
    ensure_schema(conn)
    mapping_url = f"{RAW}/data/mapping_v7.json"
    books_url = f"{RAW}/data/books.json"
    narrative_url = f"{RAW}/docs/narrative_translation.md"
    mapping = json.loads(fetch_text(mapping_url))
    books = json.loads(fetch_text(books_url))
    narrative_text = fetch_text(narrative_url)
    narrative = parse_narrative(narrative_text)
    local = local_digits(conn)
    reverse_local: dict[str, list[str]] = {}
    for bookid, digits in local.items():
        reverse_local.setdefault(digits, []).append(bookid)

    rows: list[dict[str, Any]] = []
    index_matches = 0
    any_matches = 0
    for idx, digits in enumerate(books):
        digits = re.sub(r"\D+", "", str(digits))
        local_bookid = str(idx) if str(idx) in local else None
        exact_index = int(local_bookid is not None and local.get(local_bookid) == digits)
        any_match_ids = reverse_local.get(digits, [])
        exact_any = int(bool(any_match_ids))
        if exact_index:
            index_matches += 1
        if exact_any:
            any_matches += 1
        n = narrative.get(idx, {})
        rows.append(
            {
                "external_book_id": idx,
                "local_bookid": local_bookid if exact_index else (any_match_ids[0] if any_match_ids else local_bookid),
                "exact_index_match": exact_index,
                "exact_any_match": exact_any,
                "digit_len": len(digits),
                "local_digit_len": len(local.get(str(idx), "")) if str(idx) in local else None,
                "coverage_pct": n.get("coverage_pct"),
                "decoded_chars": n.get("decoded_chars"),
                "decoded_german": n.get("decoded_german"),
                "english": n.get("english"),
                "spanish": n.get("spanish"),
                "payload": {
                    "external_digit_prefix": digits[:40],
                    "external_digit_suffix": digits[-40:],
                    "local_same_index_digit_prefix": local.get(str(idx), "")[:40],
                    "mapping_source": mapping_url,
                    "books_source": books_url,
                    "narrative_source": narrative_url,
                },
            }
        )

    cur = conn.execute(
        """
        INSERT INTO external_candidate_solution_runs (
          created_at, source_name, repo_url, mapping_count, book_count, narrative_book_count,
          exact_digit_index_matches, exact_digit_any_matches, payload_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            now(),
            "arturoornelasb/tibia-bonelord-469-cipher",
            REPO,
            len(mapping),
            len(books),
            len(narrative),
            index_matches,
            any_matches,
            json.dumps(
                {
                    "mapping_url": mapping_url,
                    "books_url": books_url,
                    "narrative_url": narrative_url,
                    "claim": "Homophonic two-digit substitution, German/MHG, external candidate solution.",
                },
                ensure_ascii=True,
                sort_keys=True,
            ),
        ),
    )
    run_id = int(cur.lastrowid)
    for code, letter in sorted(mapping.items()):
        conn.execute(
            "INSERT INTO external_candidate_solution_mapping (run_id, code, letter) VALUES (?, ?, ?)",
            (run_id, str(code), str(letter)),
        )
    for row in rows:
        conn.execute(
            """
            INSERT INTO external_candidate_solution_books (
              run_id, external_book_id, local_bookid, exact_index_match, exact_any_match,
              digit_len, local_digit_len, coverage_pct, decoded_chars, decoded_german,
              english, spanish, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                row["external_book_id"],
                row["local_bookid"],
                row["exact_index_match"],
                row["exact_any_match"],
                row["digit_len"],
                row["local_digit_len"],
                row["coverage_pct"],
                row["decoded_chars"],
                row["decoded_german"],
                row["english"],
                row["spanish"],
                json.dumps(row["payload"], ensure_ascii=True, sort_keys=True),
            ),
        )
    conn.commit()
    return {
        "recorded_run_id": run_id,
        "source_name": "arturoornelasb/tibia-bonelord-469-cipher",
        "repo_url": REPO,
        "mapping_count": len(mapping),
        "book_count": len(books),
        "narrative_book_count": len(narrative),
        "exact_digit_index_matches": index_matches,
        "exact_digit_any_matches": any_matches,
        "sample_books": [
            {
                "external_book_id": row["external_book_id"],
                "local_bookid": row["local_bookid"],
                "exact_index_match": row["exact_index_match"],
                "digit_len": row["digit_len"],
                "coverage_pct": row["coverage_pct"],
                "english": row["english"],
            }
            for row in rows[:8]
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DB_PATH)
    args = parser.parse_args()
    with connect(args.db) as conn:
        result = ingest(conn)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
