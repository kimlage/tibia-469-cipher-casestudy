#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List

from sqlite_dead_branch_rules import matching_dead_rules
from sqlite_semantic_family_report import book_contexts, glossary_variants, summarize_contradictions
from sqlite_snapshot_ref import DEFAULT_SNAPSHOT_NAME, resolve_export_id


DEFAULT_DB = "./data/bonelord_operational.sqlite"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rank token families by semantic contradiction under the operational SQLite DB")
    parser.add_argument("--db", default=DEFAULT_DB, help="Operational SQLite DB")
    parser.add_argument("--export-id", type=int, default=None, help="Specific export_id")
    parser.add_argument("--snapshot-name", default=DEFAULT_SNAPSHOT_NAME, help="Named snapshot ref to use")
    parser.add_argument("--pool", type=int, default=80, help="How many high-footprint glossary tokens to inspect")
    parser.add_argument("--top", type=int, default=15, help="How many ranked families to print")
    parser.add_argument("--min-len", type=int, default=6)
    parser.add_argument("--min-bookcount", type=int, default=2)
    parser.add_argument("--out", default=None, help="Optional JSON output path")
    parser.add_argument("--record", action="store_true", help="Persist the ranked frontier into the operational DB")
    return parser.parse_args()


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def seed_tokens(conn: sqlite3.Connection, export_id: int, min_len: int, min_bookcount: int, pool: int) -> List[sqlite3.Row]:
    return conn.execute(
        """
        SELECT
            token,
            translation,
            totalocc,
            bookcount,
            evidenceclass_v127,
            notes
        FROM sheet__glossary
        WHERE __export_id = ?
          AND length(coalesce(token, '')) >= ?
          AND CAST(coalesce(bookcount, 0) AS INTEGER) >= ?
        ORDER BY
            CAST(coalesce(bookcount, 0) AS INTEGER) DESC,
            CAST(coalesce(totalocc, 0) AS INTEGER) DESC,
            length(coalesce(token, '')) DESC
        LIMIT ?
        """,
        (export_id, min_len, min_bookcount, pool),
    ).fetchall()


def score_family(conn: sqlite3.Connection, export_id: int, row: sqlite3.Row) -> Dict[str, Any]:
    token = str(row["token"] or "").strip()
    variants = glossary_variants(conn, export_id, [token], 80)
    books = book_contexts(conn, export_id, [token], 80)
    summary = summarize_contradictions(variants, books)
    known_dead = [rule.label for rule in matching_dead_rules((token,))]
    prefix_contradictions = len(summary["prefix_contradictions"])
    distinct = int(summary["distinct_translation_count"])
    variant_count = len(variants)
    book_count = len(books)
    unk_pressure = sum(count for word, count in summary["top_context_words"] if word == "unk")
    circular_pressure = sum(
        count
        for word, count in summary["top_variant_words"]
        if word in {"fay", "tumtum", "fervently", "unfertile"}
    )
    score = (
        prefix_contradictions * 35
        + book_count * 8
        + min(variant_count, 50)
        + distinct * 2
        + unk_pressure * 4
        + circular_pressure
    )
    if known_dead:
        score -= 100
    return {
        "token": token,
        "translation": row["translation"],
        "bookcount": row["bookcount"],
        "totalocc": row["totalocc"],
        "evidence": row["evidenceclass_v127"],
        "score": score,
        "known_dead_rules": known_dead,
        "counts": {
            "variants": variant_count,
            "book_contexts": book_count,
            "distinct_translations": distinct,
            "prefix_contradictions": prefix_contradictions,
            "unk_pressure": unk_pressure,
            "circular_pressure": circular_pressure,
        },
        "top_context_words": summary["top_context_words"][:12],
        "prefix_contradictions": summary["prefix_contradictions"][:5],
        "recommended_action": "ABANDON_WITHOUT_NEW_MECHANICAL_REASON" if known_dead else "REVIEW",
    }


def record_frontier(conn: sqlite3.Connection, export_id: int, ranked: List[Dict[str, Any]], top: int) -> int:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS semantic_frontier_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            export_id INTEGER NOT NULL,
            item_count INTEGER NOT NULL,
            note TEXT
        );

        CREATE TABLE IF NOT EXISTS semantic_frontier_items (
            run_id INTEGER NOT NULL,
            rank INTEGER NOT NULL,
            token TEXT NOT NULL,
            translation TEXT,
            score REAL NOT NULL,
            recommended_action TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, rank)
        );
        """
    )
    created_at = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    cur = conn.execute(
        """
        INSERT INTO semantic_frontier_runs (created_at, export_id, item_count, note)
        VALUES (?, ?, ?, ?)
        """,
        (created_at, export_id, min(top, len(ranked)), "semantic contradiction rank"),
    )
    run_id = int(cur.lastrowid)
    for idx, item in enumerate(ranked[:top], start=1):
        conn.execute(
            """
            INSERT INTO semantic_frontier_items (
                run_id, rank, token, translation, score, recommended_action, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                idx,
                item["token"],
                item.get("translation"),
                item["score"],
                item["recommended_action"],
                json.dumps(item, ensure_ascii=True, sort_keys=True),
            ),
        )
    conn.commit()
    return run_id


def main() -> int:
    args = parse_args()
    conn = connect(args.db)
    try:
        export_id = resolve_export_id(conn, export_id=args.export_id, snapshot_name=args.snapshot_name)
        ranked = [score_family(conn, export_id, row) for row in seed_tokens(conn, export_id, args.min_len, args.min_bookcount, args.pool)]
        ranked.sort(key=lambda item: (item["recommended_action"] != "REVIEW", -item["score"], str(item["token"])))
        run_id = record_frontier(conn, export_id, ranked, args.top) if args.record else None
    finally:
        conn.close()

    payload = {
        "export_id": export_id,
        "pool": args.pool,
        "top": args.top,
        "recorded_run_id": run_id,
        "ranked": ranked[: args.top],
    }
    text = json.dumps(payload, ensure_ascii=True, indent=2)
    if args.out:
        out_path = Path(args.out).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
