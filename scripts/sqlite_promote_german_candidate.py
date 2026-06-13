#!/usr/bin/env python3
"""Promote the validated German/MHG candidate into SQL canonical candidate tables.

This is deliberately non-destructive:
- the old English-oriented shadow line remains archived in SQLite;
- the German layer becomes the active operational candidate, not final truth;
- low-coverage books and unknown groups stay visible as audit debt.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "bonelord_operational.sqlite"
SOURCE_URL = "https://github.com/arturoornelasb/tibia-bonelord-469-cipher"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def jdump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def one(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> sqlite3.Row:
    row = conn.execute(sql, params).fetchone()
    if row is None:
        raise SystemExit(f"missing required row for query: {sql}")
    return row


def scalar(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> Any:
    return one(conn, sql, params)[0]


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS canonical_lineage_runs (
            lineage_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            label TEXT NOT NULL UNIQUE,
            status TEXT NOT NULL,
            source_kind TEXT NOT NULL,
            source_ref TEXT NOT NULL,
            rationale TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS canonical_candidate_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            label TEXT NOT NULL,
            lineage_id INTEGER NOT NULL,
            german_candidate_run_id INTEGER NOT NULL,
            validation_run_id INTEGER NOT NULL,
            status TEXT NOT NULL,
            book_count INTEGER NOT NULL,
            contig_count INTEGER NOT NULL,
            pair_coverage_pct REAL NOT NULL,
            unmapped_pairs INTEGER NOT NULL,
            exact_digit_index_matches INTEGER NOT NULL,
            avg_coverage_pct REAL NOT NULL,
            min_coverage_pct REAL NOT NULL,
            low_coverage_books INTEGER NOT NULL,
            unknown_brace_groups INTEGER NOT NULL,
            promotion_decision TEXT NOT NULL,
            gates_json TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS canonical_candidate_books (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            digit_len INTEGER NOT NULL,
            coverage_pct REAL,
            unknown_brace_count INTEGER NOT NULL,
            promotion_status TEXT NOT NULL,
            decoded_primary TEXT,
            english_gloss TEXT,
            spanish_gloss TEXT,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        );

        CREATE TABLE IF NOT EXISTS canonical_candidate_contigs (
            run_id INTEGER NOT NULL,
            basecontigid TEXT NOT NULL,
            booksinorder TEXT NOT NULL,
            coverage_avg_pct REAL,
            decoded_primary TEXT NOT NULL,
            english_gloss TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, basecontigid)
        );

        CREATE TABLE IF NOT EXISTS canonical_candidate_validation (
            run_id INTEGER PRIMARY KEY,
            validation_run_id INTEGER NOT NULL,
            total_digits INTEGER NOT NULL,
            odd_length_books INTEGER NOT NULL,
            total_pairs INTEGER NOT NULL,
            mapped_pairs INTEGER NOT NULL,
            unmapped_pairs INTEGER NOT NULL,
            unique_pairs INTEGER NOT NULL,
            unique_unmapped_pairs INTEGER NOT NULL,
            pair_coverage_pct REAL NOT NULL,
            digit_pair_coverage_pct REAL NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_canonical_candidate_runs_label
            ON canonical_candidate_runs(label, created_at);
        CREATE INDEX IF NOT EXISTS idx_canonical_candidate_books_status
            ON canonical_candidate_books(run_id, promotion_status, coverage_pct);
        """
    )


def upsert_lineage(
    conn: sqlite3.Connection,
    *,
    label: str,
    status: str,
    source_kind: str,
    source_ref: str,
    rationale: str,
    payload: dict[str, Any],
) -> int:
    now = utc_now()
    conn.execute(
        """
        INSERT INTO canonical_lineage_runs
            (created_at, label, status, source_kind, source_ref, rationale, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(label) DO UPDATE SET
            created_at=excluded.created_at,
            status=excluded.status,
            source_kind=excluded.source_kind,
            source_ref=excluded.source_ref,
            rationale=excluded.rationale,
            payload_json=excluded.payload_json
        """,
        (now, label, status, source_kind, source_ref, rationale, jdump(payload)),
    )
    return int(scalar(conn, "SELECT lineage_id FROM canonical_lineage_runs WHERE label=?", (label,)))


def count_brace_groups(text: str | None) -> int:
    if not text:
        return 0
    return len(re.findall(r"\{[^{}]*\}", text))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--label", default="german_mhg_arturoornelasb_v1")
    parser.add_argument("--low-coverage-threshold", type=float, default=85.0)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)

    german_run = one(
        conn,
        """
        SELECT *
        FROM german_candidate_runs
        ORDER BY run_id DESC
        LIMIT 1
        """,
    )
    validation = one(
        conn,
        """
        SELECT *
        FROM external_candidate_validation_runs
        WHERE run_id=?
        """,
        (german_run["validation_run_id"],),
    )

    old_lineage_id = upsert_lineage(
        conn,
        label="english_overfit_v1",
        status="ARCHIVED_REJECTED_AS_CANONICAL",
        source_kind="sqlite_shadow_pipeline",
        source_ref="semantic_shadow_book_runs + formula/microtoken shadows",
        rationale=(
            "Arquivada como linha histórica: produziu texto legível em inglês, "
            "mas acumulou contradições semânticas e não preserva uma mecânica "
            "canônica confiável para todos os livros."
        ),
        payload={
            "use": "audit_only",
            "do_not_use_for": ["canonical_decode", "semantic_progress_score"],
        },
    )
    new_lineage_id = upsert_lineage(
        conn,
        label=args.label,
        status="ACTIVE_OPERATIONAL_CANDIDATE",
        source_kind="external_candidate_solution",
        source_ref=SOURCE_URL,
        rationale=(
            "Promovida como candidato operacional porque casa 70/70 livros por "
            "índice e stream de dígitos, tem 100% de cobertura por pares usados "
            "e zero pares não mapeados. Ainda não é prova semântica final."
        ),
        payload={
            "archived_lineage_id": old_lineage_id,
            "primary_layer": "decoded_german",
            "display_layers": ["english_gloss", "spanish_gloss"],
        },
    )

    books = conn.execute(
        """
        SELECT *
        FROM german_candidate_books
        WHERE run_id=?
        ORDER BY CAST(bookid AS INTEGER)
        """,
        (german_run["run_id"],),
    ).fetchall()
    contigs = conn.execute(
        """
        SELECT *
        FROM german_candidate_contigs
        WHERE run_id=?
        ORDER BY CAST(basecontigid AS INTEGER)
        """,
        (german_run["run_id"],),
    ).fetchall()

    unknown_total = sum(count_brace_groups(row["decoded_german"]) for row in books)
    low_coverage = sum(
        1 for row in books if row["coverage_pct"] is not None and float(row["coverage_pct"]) < args.low_coverage_threshold
    )
    digit_pair_coverage_pct = (
        float(validation["mapped_pairs"]) * 2.0 / float(validation["total_digits"]) * 100.0
        if int(validation["total_digits"]) > 0
        else 0.0
    )
    gates = {
        "exact_digit_index_matches": int(german_run["exact_digit_index_matches"]) == 70,
        "book_count_70": int(german_run["book_count"]) == 70,
        "pair_coverage_100": float(validation["pair_coverage_pct"]) == 100.0,
        "unmapped_pairs_zero": int(validation["unmapped_pairs"]) == 0,
        "known_semantic_debt_visible": unknown_total > 0 or low_coverage > 0,
    }
    promotion_decision = (
        "PROMOTE_AS_ACTIVE_CANDIDATE_WITH_SEMANTIC_DEBT"
        if all(gates[k] for k in ["exact_digit_index_matches", "book_count_70", "pair_coverage_100", "unmapped_pairs_zero"])
        else "DO_NOT_PROMOTE"
    )

    cur = conn.execute(
        """
        INSERT INTO canonical_candidate_runs
            (created_at, label, lineage_id, german_candidate_run_id, validation_run_id,
             status, book_count, contig_count, pair_coverage_pct, unmapped_pairs,
             exact_digit_index_matches, avg_coverage_pct, min_coverage_pct,
             low_coverage_books, unknown_brace_groups, promotion_decision,
             gates_json, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            utc_now(),
            args.label,
            new_lineage_id,
            german_run["run_id"],
            validation["run_id"],
            "ACTIVE_OPERATIONAL_CANDIDATE",
            german_run["book_count"],
            german_run["contig_count"],
            validation["pair_coverage_pct"],
            validation["unmapped_pairs"],
            german_run["exact_digit_index_matches"],
            german_run["avg_coverage_pct"],
            german_run["min_coverage_pct"],
            low_coverage,
            unknown_total,
            promotion_decision,
            jdump(gates),
            jdump(
                {
                    "source": SOURCE_URL,
                    "note": "Decoded German/MHG is the primary mechanical layer. English/Spanish remain interpretive glosses.",
                }
            ),
        ),
    )
    canonical_run_id = int(cur.lastrowid)

    for row in books:
        unknown_count = count_brace_groups(row["decoded_german"])
        coverage = row["coverage_pct"]
        promotion_status = "PROMOTE"
        if coverage is not None and float(coverage) < args.low_coverage_threshold:
            promotion_status = "PROMOTE_WITH_CAUTION_LOW_COVERAGE"
        if unknown_count > 0 and promotion_status == "PROMOTE":
            promotion_status = "PROMOTE_WITH_VISIBLE_UNKNOWNS"
        conn.execute(
            """
            INSERT INTO canonical_candidate_books
                (run_id, bookid, digit_len, coverage_pct, unknown_brace_count,
                 promotion_status, decoded_primary, english_gloss, spanish_gloss, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                canonical_run_id,
                row["bookid"],
                row["digit_len"],
                row["coverage_pct"],
                unknown_count,
                promotion_status,
                row["decoded_german"],
                row["english"],
                row["spanish"],
                row["payload_json"],
            ),
        )

    for row in contigs:
        conn.execute(
            """
            INSERT INTO canonical_candidate_contigs
                (run_id, basecontigid, booksinorder, coverage_avg_pct,
                 decoded_primary, english_gloss, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                canonical_run_id,
                row["basecontigid"],
                row["booksinorder"],
                row["coverage_avg_pct"],
                row["decoded_german"],
                row["english"],
                row["payload_json"],
            ),
        )

    conn.execute(
        """
        INSERT INTO canonical_candidate_validation
            (run_id, validation_run_id, total_digits, odd_length_books, total_pairs,
             mapped_pairs, unmapped_pairs, unique_pairs, unique_unmapped_pairs,
             pair_coverage_pct, digit_pair_coverage_pct, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            canonical_run_id,
            validation["run_id"],
            validation["total_digits"],
            validation["odd_length_books"],
            validation["total_pairs"],
            validation["mapped_pairs"],
            validation["unmapped_pairs"],
            validation["unique_pairs"],
            validation["unique_unmapped_pairs"],
            validation["pair_coverage_pct"],
            digit_pair_coverage_pct,
            validation["payload_json"],
        ),
    )
    conn.commit()

    print(
        json.dumps(
            {
                "canonical_run_id": canonical_run_id,
                "label": args.label,
                "status": "ACTIVE_OPERATIONAL_CANDIDATE",
                "promotion_decision": promotion_decision,
                "book_count": int(german_run["book_count"]),
                "contig_count": int(german_run["contig_count"]),
                "pair_coverage_pct": float(validation["pair_coverage_pct"]),
                "digit_pair_coverage_pct": round(digit_pair_coverage_pct, 4),
                "unmapped_pairs": int(validation["unmapped_pairs"]),
                "odd_length_books": int(validation["odd_length_books"]),
                "low_coverage_books": low_coverage,
                "unknown_brace_groups": unknown_total,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
