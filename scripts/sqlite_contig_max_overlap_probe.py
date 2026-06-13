#!/usr/bin/env python3
"""Validate row0 books against imported contigs by maximal suffix/prefix overlap."""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "bonelord_operational.sqlite"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def jdump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS contig_max_overlap_probe_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_code_symbol_run_id INTEGER NOT NULL,
            source_export_id INTEGER NOT NULL,
            contig_count INTEGER NOT NULL,
            exact_reconstruction_count INTEGER NOT NULL,
            mismatch_count INTEGER NOT NULL,
            total_overlap_symbols INTEGER NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS contig_max_overlap_items (
            run_id INTEGER NOT NULL,
            basecontigid TEXT NOT NULL,
            booksinorder TEXT NOT NULL,
            expected_length INTEGER NOT NULL,
            reconstructed_length INTEGER NOT NULL,
            exact_match INTEGER NOT NULL,
            prefix_match_len INTEGER NOT NULL,
            suffix_match_len INTEGER NOT NULL,
            transition_count INTEGER NOT NULL,
            total_overlap_symbols INTEGER NOT NULL,
            min_overlap_symbols INTEGER NOT NULL,
            max_overlap_symbols INTEGER NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, basecontigid)
        );

        CREATE TABLE IF NOT EXISTS contig_max_overlap_edges (
            run_id INTEGER NOT NULL,
            basecontigid TEXT NOT NULL,
            edge_index INTEGER NOT NULL,
            left_bookid TEXT NOT NULL,
            right_bookid TEXT NOT NULL,
            overlap_symbols INTEGER NOT NULL,
            overlap_text TEXT NOT NULL,
            PRIMARY KEY (run_id, basecontigid, edge_index)
        );
        """
    )


def one(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> sqlite3.Row:
    row = conn.execute(sql, params).fetchone()
    if row is None:
        raise SystemExit(f"missing required row for query: {sql}")
    return row


def max_overlap(left: str, right: str) -> int:
    limit = min(len(left), len(right))
    for size in range(limit, -1, -1):
        if left.endswith(right[:size]):
            return size
    return 0


def common_prefix_len(a: str, b: str) -> int:
    limit = min(len(a), len(b))
    for idx in range(limit):
        if a[idx] != b[idx]:
            return idx
    return limit


def common_suffix_len(a: str, b: str) -> int:
    limit = min(len(a), len(b))
    for idx in range(1, limit + 1):
        if a[-idx] != b[-idx]:
            return idx - 1
    return limit


def parse_books(value: str) -> list[str]:
    return [part.strip() for part in (value or "").split("->") if part.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)

    source_run_id = int(one(conn, "SELECT run_id FROM row0_code_symbol_probe_runs ORDER BY run_id DESC LIMIT 1")["run_id"])
    export_id = int(one(conn, "SELECT MAX(__export_id) AS export_id FROM sheet__contigs")["export_id"])
    book_rows = conn.execute(
        """
        SELECT bookid, decodedbase
        FROM row0_code_symbol_probe_books
        WHERE run_id=? AND valid=1
        """,
        (source_run_id,),
    ).fetchall()
    books = {str(row["bookid"]): row["decodedbase"] or "" for row in book_rows}
    contigs = conn.execute(
        """
        SELECT basecontigid, booksinorder, basecontig
        FROM sheet__contigs
        WHERE __export_id=?
        ORDER BY CAST(basecontigid AS INTEGER)
        """,
        (export_id,),
    ).fetchall()

    run_cur = conn.execute(
        """
        INSERT INTO contig_max_overlap_probe_runs
            (created_at, source_code_symbol_run_id, source_export_id, contig_count,
             exact_reconstruction_count, mismatch_count, total_overlap_symbols, decision, payload_json)
        VALUES (?, ?, ?, ?, 0, 0, 0, ?, ?)
        """,
        (utc_now(), source_run_id, export_id, len(contigs), "PENDING", "{}"),
    )
    run_id = int(run_cur.lastrowid)

    exact_count = 0
    total_overlap_all = 0
    summaries: list[dict[str, Any]] = []

    for contig in contigs:
        basecontigid = str(contig["basecontigid"])
        expected = contig["basecontig"] or ""
        order = parse_books(contig["booksinorder"] or "")
        if not order:
            reconstructed = ""
            edges: list[dict[str, Any]] = []
        else:
            missing = [bookid for bookid in order if bookid not in books]
            if missing:
                raise SystemExit(f"missing books for contig {basecontigid}: {missing}")
            reconstructed = books[order[0]]
            edges = []
            for edge_index, (left_bookid, right_bookid) in enumerate(zip(order, order[1:]), start=1):
                right_text = books[right_bookid]
                overlap = max_overlap(reconstructed, right_text)
                overlap_text = right_text[:overlap]
                reconstructed += right_text[overlap:]
                edges.append(
                    {
                        "edge_index": edge_index,
                        "left_bookid": left_bookid,
                        "right_bookid": right_bookid,
                        "overlap_symbols": overlap,
                        "overlap_text": overlap_text,
                    }
                )
        exact = int(reconstructed == expected)
        exact_count += exact
        overlaps = [edge["overlap_symbols"] for edge in edges]
        total_overlap = sum(overlaps)
        total_overlap_all += total_overlap
        prefix_len = common_prefix_len(reconstructed, expected)
        suffix_len = common_suffix_len(reconstructed, expected)
        summaries.append(
            {
                "basecontigid": basecontigid,
                "exact_match": bool(exact),
                "expected_length": len(expected),
                "reconstructed_length": len(reconstructed),
                "transition_count": len(edges),
                "total_overlap_symbols": total_overlap,
            }
        )
        conn.execute(
            """
            INSERT INTO contig_max_overlap_items
                (run_id, basecontigid, booksinorder, expected_length, reconstructed_length,
                 exact_match, prefix_match_len, suffix_match_len, transition_count,
                 total_overlap_symbols, min_overlap_symbols, max_overlap_symbols, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                basecontigid,
                contig["booksinorder"] or "",
                len(expected),
                len(reconstructed),
                exact,
                prefix_len,
                suffix_len,
                len(edges),
                total_overlap,
                min(overlaps) if overlaps else 0,
                max(overlaps) if overlaps else 0,
                jdump({"order": order, "summary": summaries[-1]}),
            ),
        )
        for edge in edges:
            conn.execute(
                """
                INSERT INTO contig_max_overlap_edges
                    (run_id, basecontigid, edge_index, left_bookid, right_bookid,
                     overlap_symbols, overlap_text)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    basecontigid,
                    edge["edge_index"],
                    edge["left_bookid"],
                    edge["right_bookid"],
                    edge["overlap_symbols"],
                    edge["overlap_text"],
                ),
            )

    mismatch_count = len(contigs) - exact_count
    decision = "CONTIG_OVERLAP_VALIDATED" if mismatch_count == 0 else "CONTIG_OVERLAP_MISMATCHES_FOUND"
    conn.execute(
        """
        UPDATE contig_max_overlap_probe_runs
        SET exact_reconstruction_count=?,
            mismatch_count=?,
            total_overlap_symbols=?,
            decision=?,
            payload_json=?
        WHERE run_id=?
        """,
        (
            exact_count,
            mismatch_count,
            total_overlap_all,
            decision,
            jdump({"summaries": summaries}),
            run_id,
        ),
    )
    conn.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "contig_count": len(contigs),
                "exact_reconstruction_count": exact_count,
                "mismatch_count": mismatch_count,
                "total_overlap_symbols": total_overlap_all,
                "summaries": summaries,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
