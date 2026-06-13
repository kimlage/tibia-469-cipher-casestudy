#!/usr/bin/env python3
"""Classify BENNA formula prefix/suffix concordance in row0 variant tokens."""

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
ANCHOR = "BENNA"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def jdump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS benna_concordance_probe_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_variant_run_id INTEGER NOT NULL,
            anchor TEXT NOT NULL,
            occurrence_count INTEGER NOT NULL,
            book_count INTEGER NOT NULL,
            prefix_class_count_json TEXT NOT NULL,
            suffix_class_count_json TEXT NOT NULL,
            pair_class_count_json TEXT NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS benna_concordance_items (
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


def latest_id(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT run_id FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    if row is None:
        raise SystemExit(f"missing required table data: {table}")
    return int(row["run_id"])


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


def classify_prefix(left_symbol: str) -> str:
    suffix = left_symbol[-24:]
    if suffix.endswith("EFFIFTLEITEL"):
        return "EFFIFTLEITEL"
    if suffix.endswith("FFIFTLEITEL"):
        return "FFIFTLEITEL"
    if suffix.endswith("FIFTLEITEL"):
        return "FIFTLEITEL"
    if suffix.endswith("LEITEL"):
        return "LEITEL"
    return "OTHER_PREFIX"


def classify_suffix(right_symbol: str) -> str:
    if right_symbol.startswith("IFIININSBASTFNENIIFINI*LTASTTN"):
        return "IFIININS_BAST_FNENIIFINI_STAR_LTASTTN"
    if right_symbol.startswith("IFIININSBASTFNENIIFINI"):
        return "IFIININS_BAST_FNENIIFINI"
    if right_symbol.startswith("IFIININSBAST"):
        return "IFIININS_BAST"
    if right_symbol.startswith("IFIININ"):
        return "IFIININ_PARTIAL"
    return "OTHER_SUFFIX"


def next_action(prefix_class: str, suffix_class: str) -> str:
    if prefix_class != "OTHER_PREFIX" and suffix_class == "IFIININS_BAST_FNENIIFINI_STAR_LTASTTN":
        return "clean_formula_bridge_candidate"
    if prefix_class != "OTHER_PREFIX":
        return "prefix_stable_suffix_variant"
    if suffix_class.startswith("IFIIN"):
        return "suffix_stable_prefix_variant"
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
        SELECT bookid, symbol_text, tokens_json
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
        text = row["symbol_text"] or ""
        tokens = json.loads(row["tokens_json"] or "[]")
        for occurrence_index, start in enumerate(find_all(text, ANCHOR), start=1):
            end = start + len(ANCHOR)
            left_symbol = text[max(0, start - 48) : start]
            right_symbol = text[end : min(len(text), end + 56)]
            left_tokens = tokens[max(0, start - 48) : start]
            anchor_tokens = tokens[start:end]
            right_tokens = tokens[end : min(len(tokens), end + 56)]
            prefix_class = classify_prefix(left_symbol)
            suffix_class = classify_suffix(right_symbol)
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
                    "position_class": position_class(text, start, end),
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

    clean_count = sum(1 for item in items if item["next_action"] == "clean_formula_bridge_candidate")
    decision = "BENNA_CONCORDANCE_READY" if clean_count else "BENNA_CONCORDANCE_WEAK"
    cur = conn.execute(
        """
        INSERT INTO benna_concordance_probe_runs
            (created_at, source_variant_run_id, anchor, occurrence_count, book_count,
             prefix_class_count_json, suffix_class_count_json, pair_class_count_json,
             decision, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            utc_now(),
            variant_run_id,
            ANCHOR,
            len(items),
            len(books),
            jdump(prefix_counts.most_common()),
            jdump(suffix_counts.most_common()),
            jdump(pair_counts.most_common()),
            decision,
            jdump({"clean_formula_bridge_count": clean_count, "semantic_gloss_assigned": False}),
        ),
    )
    run_id = int(cur.lastrowid)
    for item in items:
        conn.execute(
            """
            INSERT INTO benna_concordance_items
                (run_id, bookid, occurrence_index, start_pos, position_class, prefix_class,
                 suffix_class, left_symbol_context, anchor_symbol_text, right_symbol_context,
                 left_token_context, anchor_token_text, right_token_context, next_action, payload_json)
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
