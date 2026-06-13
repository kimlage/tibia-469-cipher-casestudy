#!/usr/bin/env python3
"""Classify the row0 NAESE/IVIFAST template into slot families.

This is a SQL-native, anti-hallucination probe. It does not assign English
meaning. It only records mechanically repeated prefix/suffix environments around
the strongest current row0 semantic-function candidate.
"""

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
ANCHOR = "IVIFASTFNEIEINTA"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def jdump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS naese_ivifast_slot_probe_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_variant_run_id INTEGER NOT NULL,
            source_template_slot_run_id INTEGER,
            anchor TEXT NOT NULL,
            occurrence_count INTEGER NOT NULL,
            book_count INTEGER NOT NULL,
            prefix_class_count_json TEXT NOT NULL,
            suffix_class_count_json TEXT NOT NULL,
            pair_class_count_json TEXT NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS naese_ivifast_slot_items (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            occurrence_index INTEGER NOT NULL,
            start_pos INTEGER NOT NULL,
            position_class TEXT NOT NULL,
            prefix_class TEXT NOT NULL,
            suffix_class TEXT NOT NULL,
            left_symbol_context TEXT NOT NULL,
            anchor_symbol_text TEXT NOT NULL,
            right_symbol_context TEXT NOT NULL,
            left_token_context TEXT NOT NULL,
            anchor_token_text TEXT NOT NULL,
            right_token_context TEXT NOT NULL,
            next_action TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid, occurrence_index)
        );
        """
    )


def latest_id(conn: sqlite3.Connection, table: str, column: str = "run_id") -> int:
    row = conn.execute(f"SELECT {column} AS id FROM {table} ORDER BY {column} DESC LIMIT 1").fetchone()
    if row is None:
        raise SystemExit(f"missing required table data: {table}")
    return int(row["id"])


def latest_optional_id(conn: sqlite3.Connection, table: str, column: str = "run_id") -> int | None:
    row = conn.execute(f"SELECT {column} AS id FROM {table} ORDER BY {column} DESC LIMIT 1").fetchone()
    return int(row["id"]) if row else None


def find_all(text: str, needle: str) -> list[int]:
    starts: list[int] = []
    idx = 0
    while True:
        pos = text.find(needle, idx)
        if pos < 0:
            return starts
        starts.append(pos)
        idx = pos + 1


def position_class(text: str, start: int, end: int) -> str:
    if "*" not in text:
        return "whole_book_no_star"
    before = text.rfind("*", 0, start)
    after = text.find("*", end)
    if before < 0:
        return "before_first_star"
    if after < 0:
        return "after_last_star"
    return "between_stars"


def classify_prefix(left_symbol: str, left_tokens: list[str]) -> str:
    left_token_text = " ".join(left_tokens)
    if "NAESESTIENFATCTIVVTISETE" in left_symbol[-40:]:
        if "C68" in left_token_text:
            return "NAESE_TCT_DOMINANT_C68"
        return "NAESE_TCT_DOMINANT"
    if "ENTEEAEISETE" in left_symbol[-32:]:
        return "ENTEEAE"
    if "INTEEAEISETE" in left_symbol[-32:]:
        return "INTEEAE"
    if "NIVVENININ" in left_symbol[-32:]:
        return "NIVVENININ"
    if "NAESE" in left_symbol[-40:]:
        return "NAESE_OTHER"
    return "OTHER_PREFIX"


def classify_suffix(right_symbol: str, right_tokens: list[str]) -> str:
    right_token_text = " ".join(right_tokens[:14])
    if right_symbol.startswith("AETTAEFTEI*") or right_token_text.startswith("A E T T A E F T E I *00"):
        return "AETTAEFTEI_STAR"
    if right_symbol.startswith("AETTAEFTNE"):
        return "AETTAEFTNE"
    if right_symbol.startswith("AETTAENSNCEI"):
        return "AETTAENSNCEI"
    if right_symbol.startswith("AFINLFSENSTA"):
        return "AFINLFSENSTA"
    if right_symbol.startswith("AET"):
        return "AET_TRUNC_OR_OTHER"
    return "OTHER_SUFFIX"


def next_action(prefix_class: str, suffix_class: str) -> str:
    if prefix_class.startswith("NAESE_TCT") and suffix_class == "AETTAEFTEI_STAR":
        return "clean_template_exemplar_for_function_inference"
    if prefix_class.startswith("NAESE_TCT"):
        return "compare_suffix_variant_against_clean_template"
    if suffix_class == "AETTAEFTEI_STAR":
        return "compare_prefix_variant_against_clean_template"
    return "rare_variant_audit_only"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)

    variant_run_id = latest_id(conn, "row0_variant_frontier_runs")
    template_run_id = latest_optional_id(conn, "template_slot_probe_runs")
    rows = conn.execute(
        """
        SELECT bookid, symbol_text, token_text, tokens_json
        FROM row0_variant_book_tokens
        WHERE run_id=?
        ORDER BY CAST(bookid AS INTEGER)
        """,
        (variant_run_id,),
    ).fetchall()

    items: list[dict[str, Any]] = []
    prefix_counts: Counter[str] = Counter()
    suffix_counts: Counter[str] = Counter()
    pair_counts: Counter[str] = Counter()
    books = set()

    for row in rows:
        symbol_text = row["symbol_text"] or ""
        tokens = json.loads(row["tokens_json"] or "[]")
        if len(tokens) != len(symbol_text):
            raise SystemExit(f"token/symbol alignment mismatch for book {row['bookid']}")
        for occurrence_index, start in enumerate(find_all(symbol_text, ANCHOR), start=1):
            end = start + len(ANCHOR)
            left_symbol = symbol_text[max(0, start - 48) : start]
            right_symbol = symbol_text[end : min(len(symbol_text), end + 48)]
            left_tokens = tokens[max(0, start - 48) : start]
            anchor_tokens = tokens[start:end]
            right_tokens = tokens[end : min(len(tokens), end + 48)]
            prefix_class = classify_prefix(left_symbol, left_tokens)
            suffix_class = classify_suffix(right_symbol, right_tokens)
            pair_class = f"{prefix_class}__{suffix_class}"
            prefix_counts[prefix_class] += 1
            suffix_counts[suffix_class] += 1
            pair_counts[pair_class] += 1
            books.add(str(row["bookid"]))
            items.append(
                {
                    "bookid": str(row["bookid"]),
                    "occurrence_index": occurrence_index,
                    "start_pos": start + 1,
                    "position_class": position_class(symbol_text, start, end),
                    "prefix_class": prefix_class,
                    "suffix_class": suffix_class,
                    "left_symbol_context": left_symbol,
                    "right_symbol_context": right_symbol,
                    "left_token_context": " ".join(left_tokens),
                    "anchor_token_text": " ".join(anchor_tokens),
                    "right_token_context": " ".join(right_tokens),
                    "next_action": next_action(prefix_class, suffix_class),
                }
            )

    decision = "NAESE_IVIFAST_SLOT_CLASSES_READY" if items else "NAESE_IVIFAST_ANCHOR_NOT_FOUND"
    cur = conn.execute(
        """
        INSERT INTO naese_ivifast_slot_probe_runs
            (created_at, source_variant_run_id, source_template_slot_run_id, anchor,
             occurrence_count, book_count, prefix_class_count_json, suffix_class_count_json,
             pair_class_count_json, decision, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            utc_now(),
            variant_run_id,
            template_run_id,
            ANCHOR,
            len(items),
            len(books),
            jdump(prefix_counts.most_common()),
            jdump(suffix_counts.most_common()),
            jdump(pair_counts.most_common()),
            decision,
            jdump(
                {
                    "purpose": "mechanical slot classification before any semantic gloss",
                    "anti_hallucination": "no plaintext meaning assigned",
                    "clean_exemplar_count": sum(
                        1
                        for item in items
                        if item["next_action"] == "clean_template_exemplar_for_function_inference"
                    ),
                }
            ),
        ),
    )
    run_id = int(cur.lastrowid)

    for item in items:
        conn.execute(
            """
            INSERT INTO naese_ivifast_slot_items
                (run_id, bookid, occurrence_index, start_pos, position_class,
                 prefix_class, suffix_class, left_symbol_context, anchor_symbol_text,
                 right_symbol_context, left_token_context, anchor_token_text,
                 right_token_context, next_action, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                item["bookid"],
                item["occurrence_index"],
                item["start_pos"],
                item["position_class"],
                item["prefix_class"],
                item["suffix_class"],
                item["left_symbol_context"],
                ANCHOR,
                item["right_symbol_context"],
                item["left_token_context"],
                item["anchor_token_text"],
                item["right_token_context"],
                item["next_action"],
                "{}",
            ),
        )

    conn.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "occurrence_count": len(items),
                "book_count": len(books),
                "prefix_classes": prefix_counts.most_common(),
                "suffix_classes": suffix_counts.most_common(),
                "pair_classes": pair_counts.most_common(),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
