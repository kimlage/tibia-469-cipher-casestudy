#!/usr/bin/env python3
"""Contrast row0 code variants that share the same base symbol."""

from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "bonelord_operational.sqlite"
TARGETS = {
    ("C", "68"): "C68",
    ("C", "86"): "C86",
    ("R", "20"): "R20",
    ("R", "02"): "R02",
    ("O", "23"): "O23",
    ("O", "32"): "O32",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def jdump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS variant_contrast_probe_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_variant_run_id INTEGER NOT NULL,
            target_count INTEGER NOT NULL,
            contrast_group_count INTEGER NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS variant_contrast_items (
            run_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            code TEXT NOT NULL,
            token_label TEXT NOT NULL,
            occurrence_count INTEGER NOT NULL,
            book_count INTEGER NOT NULL,
            left2_json TEXT NOT NULL,
            right2_json TEXT NOT NULL,
            containing_ngrams_json TEXT NOT NULL,
            role_class TEXT NOT NULL,
            next_action TEXT NOT NULL,
            PRIMARY KEY (run_id, symbol, code)
        );
        """
    )


def latest_id(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT run_id FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    if row is None:
        raise SystemExit(f"missing required table data: {table}")
    return int(row["run_id"])


def role_class(symbol: str, code: str, occurrence_count: int, book_count: int) -> str:
    if symbol == "O" and code == "32":
        return "singleton_audit_only"
    if book_count >= 15 and occurrence_count >= 15:
        return "stable_variant"
    if book_count >= 8:
        return "supported_minor_variant"
    return "weak_variant"


def next_action(symbol: str, code: str, role: str) -> str:
    if role == "singleton_audit_only":
        return "preserve_do_not_promote"
    if symbol == "C" and code == "68":
        return "contrast_against_C86_in_NCTIIN_FATCT"
    if symbol == "C" and code == "86":
        return "contrast_against_C68_in_ICE"
    if symbol == "R" and code == "20":
        return "contrast_against_R02_in_VTLRNEFIE_VAETRFE"
    if symbol == "R" and code == "02":
        return "contrast_against_R20_in_TRVE_LIVRN"
    if symbol == "O" and code == "23":
        return "contrast_against_singleton_O32_only_for_audit"
    return "audit_only"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)
    variant_run_id = latest_id(conn, "row0_variant_frontier_runs")
    rows = conn.execute(
        """
        SELECT bookid, tokens_json
        FROM row0_variant_book_tokens
        WHERE run_id=?
        ORDER BY CAST(bookid AS INTEGER)
        """,
        (variant_run_id,),
    ).fetchall()

    counts: Counter[tuple[str, str]] = Counter()
    books: dict[tuple[str, str], set[str]] = defaultdict(set)
    left2: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    right2: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    containing: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)

    for row in rows:
        tokens = json.loads(row["tokens_json"] or "[]")
        bookid = str(row["bookid"])
        for idx, token in enumerate(tokens):
            parsed = None
            for (symbol, code), label in TARGETS.items():
                if token == label:
                    parsed = (symbol, code)
                    break
            if parsed is None:
                continue
            counts[parsed] += 1
            books[parsed].add(bookid)
            left2[parsed][str(tokens[max(0, idx - 2) : idx])] += 1
            right2[parsed][str(tokens[idx + 1 : min(len(tokens), idx + 3)])] += 1
            for size in (3, 4, 5, 6):
                start_min = max(0, idx - size + 1)
                start_max = min(idx, len(tokens) - size)
                for start in range(start_min, start_max + 1):
                    ngram = " ".join(tokens[start : start + size])
                    containing[parsed][ngram] += 1

    cur = conn.execute(
        """
        INSERT INTO variant_contrast_probe_runs
            (created_at, source_variant_run_id, target_count, contrast_group_count, decision, payload_json)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            utc_now(),
            variant_run_id,
            len(TARGETS),
            3,
            "VARIANT_CONTRAST_READY",
            jdump({"groups": {"C": ["68", "86"], "R": ["20", "02"], "O": ["23", "32"]}}),
        ),
    )
    run_id = int(cur.lastrowid)

    outputs = []
    for (symbol, code), label in TARGETS.items():
        occ = counts[(symbol, code)]
        bcount = len(books[(symbol, code)])
        role = role_class(symbol, code, occ, bcount)
        action = next_action(symbol, code, role)
        output = {
            "symbol": symbol,
            "code": code,
            "token_label": label,
            "occurrence_count": occ,
            "book_count": bcount,
            "role_class": role,
            "next_action": action,
        }
        outputs.append(output)
        conn.execute(
            """
            INSERT INTO variant_contrast_items
                (run_id, symbol, code, token_label, occurrence_count, book_count,
                 left2_json, right2_json, containing_ngrams_json, role_class, next_action)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                symbol,
                code,
                label,
                occ,
                bcount,
                jdump(left2[(symbol, code)].most_common(12)),
                jdump(right2[(symbol, code)].most_common(12)),
                jdump(containing[(symbol, code)].most_common(20)),
                role,
                action,
            ),
        )

    conn.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": "VARIANT_CONTRAST_READY",
                "items": outputs,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
