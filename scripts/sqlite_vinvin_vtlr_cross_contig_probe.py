#!/usr/bin/env python3
"""Probe the cross-contig VINVIN/VTLR frame without assigning plaintext gloss."""

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
ANCHOR_SYMBOL = "VEVINVINSTAE*VTLRNEFIEAIFAIFAIF"
ANCHOR_TOKENS = [
    "V",
    "E",
    "V",
    "I",
    "N",
    "V",
    "I",
    "N",
    "S",
    "T",
    "A",
    "E",
    "*00",
    "V",
    "T",
    "L",
    "R20",
    "N",
    "E",
    "F",
    "I",
    "E",
    "A",
    "I",
    "F",
    "A",
    "I",
    "F",
    "A",
    "I",
    "F",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def jdump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS vinvin_vtlr_cross_contig_probe_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_variant_run_id INTEGER NOT NULL,
            source_contig_overlap_run_id INTEGER,
            anchor_symbol TEXT NOT NULL,
            occurrence_count INTEGER NOT NULL,
            book_count INTEGER NOT NULL,
            contig_edge_support_count INTEGER NOT NULL,
            suffix_class_count_json TEXT NOT NULL,
            prefix_class_count_json TEXT NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS vinvin_vtlr_cross_contig_items (
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
            contig_support_json TEXT NOT NULL,
            next_action TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid, occurrence_index)
        );

        CREATE TABLE IF NOT EXISTS vinvin_vtlr_contig_edge_support_items (
            run_id INTEGER NOT NULL,
            basecontigid TEXT NOT NULL,
            edge_index INTEGER NOT NULL,
            left_bookid TEXT NOT NULL,
            right_bookid TEXT NOT NULL,
            overlap_symbols INTEGER NOT NULL,
            anchor_offset_in_overlap INTEGER NOT NULL,
            support_class TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, basecontigid, edge_index)
        );
        """
    )


def latest_id(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT run_id FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    if row is None:
        raise SystemExit(f"missing required table data: {table}")
    return int(row["run_id"])


def latest_optional_id(conn: sqlite3.Connection, table: str) -> int | None:
    row = conn.execute(f"SELECT run_id FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    return int(row["run_id"]) if row else None


def find_all(text: str, needle: str) -> list[int]:
    starts: list[int] = []
    idx = 0
    while True:
        pos = text.find(needle, idx)
        if pos < 0:
            return starts
        starts.append(pos)
        idx = pos + 1


def find_token_frame(tokens: list[str], frame: list[str]) -> list[int]:
    starts: list[int] = []
    size = len(frame)
    for idx in range(0, len(tokens) - size + 1):
        if tokens[idx : idx + size] == frame:
            starts.append(idx)
    return starts


def position_class(symbol_text: str, start: int, end: int) -> str:
    anchor = symbol_text[start:end]
    if "*" in anchor:
        return "star_crossing_core"
    if "*" not in symbol_text:
        return "whole_book_no_star"
    before = symbol_text.rfind("*", 0, start)
    after = symbol_text.find("*", end)
    if before < 0:
        return "before_first_star"
    if after < 0:
        return "after_last_star"
    return "between_stars"


def classify_prefix(left_symbol: str) -> str:
    if left_symbol.endswith("VLVEEII"):
        return "VLVEEII_LEFT"
    if left_symbol.endswith("BFAI*"):
        return "BFAI_STAR_LEFT"
    if left_symbol.endswith("EBFAI*"):
        return "EBFAI_STAR_LEFT"
    if left_symbol.endswith("IIVE"):
        return "IIVE_LEFT"
    return "OTHER_PREFIX"


def classify_suffix(right_symbol: str) -> str:
    if right_symbol.startswith("INEIIVNSENI*LEAENT"):
        return "INEIIVNSENI_STAR_LEAENT"
    if right_symbol.startswith("INEIIVNSENI"):
        return "INEIIVNSENI"
    if right_symbol.startswith("TIFAVONAFIEI"):
        return "TIFAVONAFIEI"
    if right_symbol.startswith("TIFA"):
        return "TIFA"
    if right_symbol.startswith("INE"):
        return "INE"
    return "OTHER_SUFFIX"


def next_action(suffix_class: str, contig_support_count: int) -> str:
    if contig_support_count >= 2 and suffix_class in {"INEIIVNSENI_STAR_LEAENT", "TIFAVONAFIEI"}:
        return "cross_contig_function_candidate"
    if suffix_class in {"INEIIVNSENI_STAR_LEAENT", "TIFAVONAFIEI"}:
        return "suffix_branch_candidate"
    return "formula_or_local_audit"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)

    variant_run_id = latest_id(conn, "row0_variant_frontier_runs")
    contig_run_id = latest_optional_id(conn, "contig_max_overlap_probe_runs")

    contig_support: list[dict[str, Any]] = []
    if contig_run_id is not None:
        edge_rows = conn.execute(
            """
            SELECT basecontigid, edge_index, left_bookid, right_bookid,
                   overlap_symbols, overlap_text
            FROM contig_max_overlap_edges
            WHERE run_id=?
            ORDER BY CAST(basecontigid AS INTEGER), edge_index
            """,
            (contig_run_id,),
        ).fetchall()
        for row in edge_rows:
            offset = (row["overlap_text"] or "").find(ANCHOR_SYMBOL)
            if offset >= 0:
                contig_support.append(
                    {
                        "basecontigid": str(row["basecontigid"]),
                        "edge_index": int(row["edge_index"]),
                        "left_bookid": str(row["left_bookid"]),
                        "right_bookid": str(row["right_bookid"]),
                        "overlap_symbols": int(row["overlap_symbols"]),
                        "anchor_offset_in_overlap": offset + 1,
                        "support_class": "anchor_inside_validated_overlap",
                    }
                )

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
    books = set()
    suffix_counts: Counter[str] = Counter()
    prefix_counts: Counter[str] = Counter()

    for row in rows:
        symbol_text = row["symbol_text"] or ""
        tokens = json.loads(row["tokens_json"] or "[]")
        symbol_starts = find_all(symbol_text, ANCHOR_SYMBOL)
        token_starts = set(find_token_frame(tokens, ANCHOR_TOKENS))
        for occurrence_index, start in enumerate(symbol_starts, start=1):
            end = start + len(ANCHOR_SYMBOL)
            token_aligned = start in token_starts
            if not token_aligned:
                raise SystemExit(f"variant token alignment failed for book {row['bookid']} at {start + 1}")
            left_symbol = symbol_text[max(0, start - 48) : start]
            right_symbol = symbol_text[end : min(len(symbol_text), end + 56)]
            left_tokens = tokens[max(0, start - 48) : start]
            right_tokens = tokens[end : min(len(tokens), end + 56)]
            prefix_class = classify_prefix(left_symbol)
            suffix_class = classify_suffix(right_symbol)
            prefix_counts[prefix_class] += 1
            suffix_counts[suffix_class] += 1
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
                    "anchor_token_text": " ".join(ANCHOR_TOKENS),
                    "right_token_context": " ".join(right_tokens),
                    "next_action": next_action(suffix_class, len(contig_support)),
                }
            )

    strong_suffixes = sum(
        count for suffix, count in suffix_counts.items() if suffix in {"INEIIVNSENI_STAR_LEAENT", "TIFAVONAFIEI"}
    )
    if len(contig_support) >= 2 and strong_suffixes >= 2:
        decision = "VINVIN_VTLR_CROSS_CONTIG_FUNCTION_CANDIDATE"
    elif items:
        decision = "VINVIN_VTLR_FORMULA_FRAME_ONLY"
    else:
        decision = "VINVIN_VTLR_ANCHOR_NOT_FOUND"

    cur = conn.execute(
        """
        INSERT INTO vinvin_vtlr_cross_contig_probe_runs
            (created_at, source_variant_run_id, source_contig_overlap_run_id,
             anchor_symbol, occurrence_count, book_count, contig_edge_support_count,
             suffix_class_count_json, prefix_class_count_json, decision, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            utc_now(),
            variant_run_id,
            contig_run_id,
            ANCHOR_SYMBOL,
            len(items),
            len(books),
            len(contig_support),
            jdump(suffix_counts.most_common()),
            jdump(prefix_counts.most_common()),
            decision,
            jdump(
                {
                    "semantic_gloss_assigned": False,
                    "anchor_tokens": ANCHOR_TOKENS,
                    "contig_support": contig_support,
                    "interpretation": "candidate functional frame if suffix branches remain controlled",
                }
            ),
        ),
    )
    run_id = int(cur.lastrowid)

    for support in contig_support:
        conn.execute(
            """
            INSERT INTO vinvin_vtlr_contig_edge_support_items
                (run_id, basecontigid, edge_index, left_bookid, right_bookid,
                 overlap_symbols, anchor_offset_in_overlap, support_class, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                support["basecontigid"],
                support["edge_index"],
                support["left_bookid"],
                support["right_bookid"],
                support["overlap_symbols"],
                support["anchor_offset_in_overlap"],
                support["support_class"],
                "{}",
            ),
        )

    support_by_book = Counter()
    for support in contig_support:
        support_by_book[support["left_bookid"]] += 1
        support_by_book[support["right_bookid"]] += 1

    for item in items:
        book_support = [
            support
            for support in contig_support
            if support["left_bookid"] == item["bookid"] or support["right_bookid"] == item["bookid"]
        ]
        conn.execute(
            """
            INSERT INTO vinvin_vtlr_cross_contig_items
                (run_id, bookid, occurrence_index, start_pos, position_class,
                 prefix_class, suffix_class, left_symbol_context, anchor_symbol_text,
                 right_symbol_context, left_token_context, anchor_token_text,
                 right_token_context, contig_support_json, next_action, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                ANCHOR_SYMBOL,
                item["right_symbol_context"],
                item["left_token_context"],
                item["anchor_token_text"],
                item["right_token_context"],
                jdump(book_support),
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
                "contig_edge_support_count": len(contig_support),
                "suffix_classes": suffix_counts.most_common(),
                "prefix_classes": prefix_counts.most_common(),
                "contig_support": contig_support,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
