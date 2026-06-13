#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
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
        CREATE TABLE IF NOT EXISTS german_candidate_runs (
          run_id INTEGER PRIMARY KEY AUTOINCREMENT,
          created_at TEXT NOT NULL,
          candidate_solution_run_id INTEGER NOT NULL,
          validation_run_id INTEGER NOT NULL,
          book_count INTEGER NOT NULL,
          contig_count INTEGER NOT NULL,
          avg_coverage_pct REAL NOT NULL,
          min_coverage_pct REAL NOT NULL,
          exact_digit_index_matches INTEGER NOT NULL,
          pair_coverage_pct REAL NOT NULL,
          status TEXT NOT NULL,
          payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS german_candidate_books (
          run_id INTEGER NOT NULL,
          bookid TEXT NOT NULL,
          digit_len INTEGER NOT NULL,
          coverage_pct REAL,
          decoded_chars INTEGER,
          decoded_german TEXT,
          english TEXT,
          spanish TEXT,
          payload_json TEXT NOT NULL,
          PRIMARY KEY (run_id, bookid)
        );

        CREATE TABLE IF NOT EXISTS german_candidate_contigs (
          run_id INTEGER NOT NULL,
          basecontigid TEXT NOT NULL,
          booksinorder TEXT NOT NULL,
          coverage_avg_pct REAL,
          decoded_german TEXT NOT NULL,
          english TEXT NOT NULL,
          payload_json TEXT NOT NULL,
          PRIMARY KEY (run_id, basecontigid)
        );
        """
    )


def latest(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT MAX(run_id) AS run_id FROM {table}").fetchone()
    if not row or row["run_id"] is None:
        raise SystemExit(f"no rows in {table}")
    return int(row["run_id"])


def materialize(conn: sqlite3.Connection) -> dict[str, object]:
    ensure_schema(conn)
    candidate_run_id = latest(conn, "external_candidate_solution_runs")
    validation_run_id = latest(conn, "external_candidate_validation_runs")
    candidate_run = conn.execute(
        "SELECT * FROM external_candidate_solution_runs WHERE run_id=?",
        (candidate_run_id,),
    ).fetchone()
    validation_run = conn.execute(
        "SELECT * FROM external_candidate_validation_runs WHERE run_id=?",
        (validation_run_id,),
    ).fetchone()
    books = conn.execute(
        """
        SELECT *
        FROM external_candidate_solution_books
        WHERE run_id=?
        ORDER BY external_book_id
        """,
        (candidate_run_id,),
    ).fetchall()
    coverages = [float(row["coverage_pct"]) for row in books if row["coverage_pct"] is not None]
    avg_cov = round(sum(coverages) / len(coverages), 2) if coverages else 0.0
    min_cov = round(min(coverages), 2) if coverages else 0.0
    status = "GERMAN_CANDIDATE_PRIMARY_VALIDATED" if (
        int(candidate_run["exact_digit_index_matches"]) == 70
        and float(validation_run["pair_coverage_pct"]) == 100.0
    ) else "GERMAN_CANDIDATE_NEEDS_REVIEW"
    cur = conn.execute(
        """
        INSERT INTO german_candidate_runs (
          created_at, candidate_solution_run_id, validation_run_id, book_count,
          contig_count, avg_coverage_pct, min_coverage_pct, exact_digit_index_matches,
          pair_coverage_pct, status, payload_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            now(),
            candidate_run_id,
            validation_run_id,
            len(books),
            0,
            avg_cov,
            min_cov,
            int(candidate_run["exact_digit_index_matches"]),
            float(validation_run["pair_coverage_pct"]),
            status,
            json.dumps(
                {
                    "source": candidate_run["repo_url"],
                    "interpretation": "Primary candidate layer; not final proof of intended plaintext.",
                },
                ensure_ascii=True,
                sort_keys=True,
            ),
        ),
    )
    run_id = int(cur.lastrowid)
    by_bookid = {}
    for row in books:
        bookid = str(row["local_bookid"] if row["local_bookid"] is not None else row["external_book_id"])
        by_bookid[bookid] = row
        conn.execute(
            """
            INSERT INTO german_candidate_books (
              run_id, bookid, digit_len, coverage_pct, decoded_chars,
              decoded_german, english, spanish, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                bookid,
                int(row["digit_len"]),
                row["coverage_pct"],
                row["decoded_chars"],
                row["decoded_german"],
                row["english"],
                row["spanish"],
                row["payload_json"],
            ),
        )

    contigs = conn.execute(
        """
        SELECT basecontigid, booksinorder
        FROM sheet__contigs
        WHERE __export_id=(SELECT MAX(__export_id) FROM sheet__contigs)
        ORDER BY CAST(basecontigid AS INTEGER)
        """
    ).fetchall()
    contig_count = 0
    for contig in contigs:
        bookids = [part.strip() for part in str(contig["booksinorder"] or "").split("->") if part.strip()]
        rows = [by_bookid[bookid] for bookid in bookids if bookid in by_bookid]
        if not rows:
            continue
        contig_count += 1
        covs = [float(row["coverage_pct"]) for row in rows if row["coverage_pct"] is not None]
        conn.execute(
            """
            INSERT INTO german_candidate_contigs (
              run_id, basecontigid, booksinorder, coverage_avg_pct,
              decoded_german, english, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                str(contig["basecontigid"]),
                "->".join(bookids),
                round(sum(covs) / len(covs), 2) if covs else None,
                "\n".join(str(row["decoded_german"] or "") for row in rows),
                "\n".join(str(row["english"] or "") for row in rows),
                json.dumps({"bookids": bookids}, ensure_ascii=True, sort_keys=True),
            ),
        )
    conn.execute("UPDATE german_candidate_runs SET contig_count=? WHERE run_id=?", (contig_count, run_id))
    conn.commit()
    return {
        "recorded_run_id": run_id,
        "status": status,
        "book_count": len(books),
        "contig_count": contig_count,
        "avg_coverage_pct": avg_cov,
        "min_coverage_pct": min_cov,
        "exact_digit_index_matches": int(candidate_run["exact_digit_index_matches"]),
        "pair_coverage_pct": float(validation_run["pair_coverage_pct"]),
        "sample_books": [
            {
                "bookid": str(row["local_bookid"]),
                "coverage_pct": row["coverage_pct"],
                "english": row["english"],
            }
            for row in books[:8]
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DB_PATH)
    args = parser.parse_args()
    with connect(args.db) as conn:
        result = materialize(conn)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
