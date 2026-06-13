#!/usr/bin/env python3
"""Split same-symbol row0 codes by context/family."""

from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "bonelord_operational.sqlite"

TARGETS = {
    "O": ["23", "32"],
    "R": ["20", "02"],
    "C": ["68", "86"],
}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def jdump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS code_variant_split_probe_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_code_symbol_run_id INTEGER NOT NULL,
            target_symbol_count INTEGER NOT NULL,
            occurrence_count INTEGER NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS code_variant_split_items (
            run_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            code TEXT NOT NULL,
            occurrence_count INTEGER NOT NULL,
            book_count INTEGER NOT NULL,
            left1_json TEXT NOT NULL,
            right1_json TEXT NOT NULL,
            left2_json TEXT NOT NULL,
            right2_json TEXT NOT NULL,
            position_class_json TEXT NOT NULL,
            family_hits_json TEXT NOT NULL,
            likely_variant_role TEXT NOT NULL,
            PRIMARY KEY (run_id, symbol, code)
        );
        """
    )


def one(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> sqlite3.Row:
    row = conn.execute(sql, params).fetchone()
    if row is None:
        raise SystemExit(f"missing required row for query: {sql}")
    return row


def position_class(text: str, idx: int) -> str:
    if idx == 0:
        return "book_start"
    if idx == len(text) - 1:
        return "book_end"
    before = text.rfind("*", 0, idx)
    after = text.find("*", idx + 1)
    if before < 0 and after < 0:
        return "no_star_book"
    if before < 0:
        return "before_first_star"
    if after < 0:
        return "after_last_star"
    return "between_stars"


def family_hits(context: str) -> list[str]:
    families = []
    for key in [
        "VTLRNEFIE",
        "VAETRFE",
        "TRVE",
        "LIVRN",
        "VNCTIIN",
        "NCTIIN",
        "FATCT",
        "ICE",
        "ONAF",
        "VONA",
    ]:
        if key in context:
            families.append(key)
    return families


def role(symbol: str, code: str, occ: int, fam_counts: Counter[str]) -> str:
    if symbol == "O" and code == "32":
        return "singleton_variant_requires_audit"
    if fam_counts:
        return "family_restricted_variant"
    if occ <= 3:
        return "rare_context_variant"
    return "distributed_variant"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)
    source = one(conn, "SELECT * FROM row0_code_symbol_probe_runs ORDER BY run_id DESC LIMIT 1")
    books = conn.execute(
        """
        SELECT bookid, decodedbase, reconstructed_code_stream
        FROM row0_code_symbol_probe_books
        WHERE run_id=? AND valid=1
        ORDER BY CAST(bookid AS INTEGER)
        """,
        (source["run_id"],),
    ).fetchall()

    cur = conn.execute(
        """
        INSERT INTO code_variant_split_probe_runs
            (created_at, source_code_symbol_run_id, target_symbol_count,
             occurrence_count, decision, payload_json)
        VALUES (?, ?, ?, 0, ?, ?)
        """,
        (utc_now(), source["run_id"], len(TARGETS), "PENDING", "{}"),
    )
    run_id = int(cur.lastrowid)
    total = 0

    buckets: dict[tuple[str, str], dict[str, Any]] = {}
    for sym, codes in TARGETS.items():
        for code in codes:
            buckets[(sym, code)] = {
                "occ": 0,
                "books": set(),
                "left1": Counter(),
                "right1": Counter(),
                "left2": Counter(),
                "right2": Counter(),
                "pclasses": Counter(),
                "families": Counter(),
            }

    for row in books:
        text = row["decodedbase"] or ""
        codes = (row["reconstructed_code_stream"] or "").split()
        for idx, (ch, code) in enumerate(zip(text, codes)):
            key = (ch, code)
            if key not in buckets:
                continue
            b = buckets[key]
            b["occ"] += 1
            total += 1
            b["books"].add(str(row["bookid"]))
            if idx > 0:
                b["left1"][text[idx - 1]] += 1
            if idx + 1 < len(text):
                b["right1"][text[idx + 1]] += 1
            if idx > 1:
                b["left2"][text[idx - 2 : idx]] += 1
            if idx + 2 < len(text):
                b["right2"][text[idx + 1 : idx + 3]] += 1
            b["pclasses"][position_class(text, idx)] += 1
            ctx = text[max(0, idx - 12) : min(len(text), idx + 13)]
            for fam in family_hits(ctx):
                b["families"][fam] += 1

    for (sym, code), b in buckets.items():
        conn.execute(
            """
            INSERT INTO code_variant_split_items
                (run_id, symbol, code, occurrence_count, book_count,
                 left1_json, right1_json, left2_json, right2_json,
                 position_class_json, family_hits_json, likely_variant_role)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                sym,
                code,
                b["occ"],
                len(b["books"]),
                jdump(b["left1"].most_common(20)),
                jdump(b["right1"].most_common(20)),
                jdump(b["left2"].most_common(20)),
                jdump(b["right2"].most_common(20)),
                jdump(b["pclasses"].most_common()),
                jdump(b["families"].most_common()),
                role(sym, code, b["occ"], b["families"]),
            ),
        )

    conn.execute(
        """
        UPDATE code_variant_split_probe_runs
        SET occurrence_count=?,
            decision=?,
            payload_json=?
        WHERE run_id=?
        """,
        (total, "CODE_VARIANT_SPLITS_READY", jdump({"targets": TARGETS}), run_id),
    )
    conn.commit()

    rows = conn.execute(
        """
        SELECT symbol, code, occurrence_count, book_count, left1_json,
               right1_json, position_class_json, family_hits_json, likely_variant_role
        FROM code_variant_split_items
        WHERE run_id=?
        ORDER BY symbol, occurrence_count DESC
        """,
        (run_id,),
    ).fetchall()
    print(
        json.dumps(
            {
                "code_variant_split_run_id": run_id,
                "occurrence_count": total,
                "items": [dict(row) for row in rows],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
