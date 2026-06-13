#!/usr/bin/env python3
"""Run negative controls for the VINVINSTAE -> *00 VTLR20 frame."""

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

FRAMES = [
    {
        "frame_key": "POS_VINVINSTAE_OP_VTLR20",
        "frame_class": "positive",
        "tokens": ["V", "I", "N", "V", "I", "N", "S", "T", "A", "E", "*00", "V", "T", "L", "R20", "N", "E", "F", "I", "E"],
    },
    {
        "frame_key": "NEG_IFTINSTAE_OP_VTLR20",
        "frame_class": "same_suffix_negative",
        "tokens": ["I", "F", "T", "I", "N", "S", "T", "A", "E", "*00", "V", "T", "L", "R20", "N", "E", "F", "I", "E"],
    },
    {
        "frame_key": "CTRL_ENIIFINI_OP_LTASTTN",
        "frame_class": "operator_formula_control",
        "tokens": ["E", "N", "I", "I", "F", "I", "N", "I", "*00", "L", "T", "A", "S", "T", "T", "N"],
    },
    {
        "frame_key": "CTRL_NIIFINI_OP_LTASTTN",
        "frame_class": "operator_formula_control",
        "tokens": ["N", "I", "I", "F", "I", "N", "I", "*00", "L", "T", "A", "S", "T", "T", "N"],
    },
    {
        "frame_key": "CTRL_OP_LTASTTNVVN",
        "frame_class": "operator_formula_control",
        "tokens": ["*00", "L", "T", "A", "S", "T", "T", "N", "V", "V", "N"],
    },
    {
        "frame_key": "CTRL_FIININS",
        "frame_class": "known_formula_control",
        "tokens": ["F", "I", "I", "N", "I", "N", "S"],
    },
    {
        "frame_key": "CTRL_NSTAEFIEIEF",
        "frame_class": "known_formula_control",
        "tokens": ["N", "S", "T", "A", "E", "F", "I", "E", "I", "E", "F"],
    },
    {
        "frame_key": "CTRL_ASTFNE",
        "frame_class": "known_formula_control",
        "tokens": ["A", "S", "T", "F", "N", "E"],
    },
]

OVERLAP_POSITIVE_BOOKS = {"29", "65", "52", "62"}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def jdump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS vinvin_negative_control_probe_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_variant_run_id INTEGER NOT NULL,
            source_vinvin_run_id INTEGER,
            positive_occurrence_count INTEGER NOT NULL,
            positive_book_count INTEGER NOT NULL,
            negative_occurrence_count INTEGER NOT NULL,
            negative_book_count INTEGER NOT NULL,
            non_overlap_positive_book_count INTEGER NOT NULL,
            strongest_control_key TEXT NOT NULL,
            strongest_control_occurrence_count INTEGER NOT NULL,
            separation_score REAL NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS vinvin_negative_control_frame_items (
            run_id INTEGER NOT NULL,
            frame_key TEXT NOT NULL,
            frame_class TEXT NOT NULL,
            frame_tokens_json TEXT NOT NULL,
            occurrence_count INTEGER NOT NULL,
            book_count INTEGER NOT NULL,
            books_json TEXT NOT NULL,
            overlap_positive_book_count INTEGER NOT NULL,
            non_overlap_book_count INTEGER NOT NULL,
            left_context_json TEXT NOT NULL,
            right_context_json TEXT NOT NULL,
            score REAL NOT NULL,
            next_action TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, frame_key)
        );

        CREATE TABLE IF NOT EXISTS vinvin_negative_control_occurrence_items (
            run_id INTEGER NOT NULL,
            frame_key TEXT NOT NULL,
            bookid TEXT NOT NULL,
            occurrence_index INTEGER NOT NULL,
            start_pos INTEGER NOT NULL,
            left_context TEXT NOT NULL,
            frame_text TEXT NOT NULL,
            right_context TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, frame_key, bookid, occurrence_index)
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


def find_frame(tokens: list[str], frame: list[str]) -> list[int]:
    starts: list[int] = []
    size = len(frame)
    for idx in range(0, len(tokens) - size + 1):
        if tokens[idx : idx + size] == frame:
            starts.append(idx)
    return starts


def sorted_books(books: set[str]) -> list[str]:
    return sorted(books, key=lambda value: int(value) if value.isdigit() else value)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)

    variant_run_id = latest_id(conn, "row0_variant_frontier_runs")
    vinvin_run_id = latest_optional_id(conn, "vinvin_vtlr_cross_contig_probe_runs")
    rows = conn.execute(
        """
        SELECT bookid, tokens_json
        FROM row0_variant_book_tokens
        WHERE run_id=?
        ORDER BY CAST(bookid AS INTEGER)
        """,
        (variant_run_id,),
    ).fetchall()

    frame_data: dict[str, dict[str, Any]] = {}
    occurrences: list[dict[str, Any]] = []
    for frame in FRAMES:
        frame_key = frame["frame_key"]
        data = {
            "frame_class": frame["frame_class"],
            "tokens": frame["tokens"],
            "occurrence_count": 0,
            "books": set(),
            "left": Counter(),
            "right": Counter(),
        }
        for row in rows:
            bookid = str(row["bookid"])
            tokens = json.loads(row["tokens_json"] or "[]")
            starts = find_frame(tokens, frame["tokens"])
            for occurrence_index, start in enumerate(starts, start=1):
                end = start + len(frame["tokens"])
                left = " ".join(tokens[max(0, start - 10) : start])
                right = " ".join(tokens[end : min(len(tokens), end + 10)])
                data["occurrence_count"] += 1
                data["books"].add(bookid)
                data["left"][left] += 1
                data["right"][right] += 1
                occurrences.append(
                    {
                        "frame_key": frame_key,
                        "bookid": bookid,
                        "occurrence_index": occurrence_index,
                        "start_pos": start + 1,
                        "left": left,
                        "frame_text": " ".join(frame["tokens"]),
                        "right": right,
                    }
                )
        frame_data[frame_key] = data

    positive = frame_data["POS_VINVINSTAE_OP_VTLR20"]
    negative = frame_data["NEG_IFTINSTAE_OP_VTLR20"]
    control_items = [
        (key, data)
        for key, data in frame_data.items()
        if data["frame_class"] in {"operator_formula_control", "known_formula_control"}
    ]
    strongest_control_key, strongest_control = max(
        control_items,
        key=lambda item: (int(item[1]["occurrence_count"]), len(item[1]["books"])),
    )
    positive_books = set(positive["books"])
    non_overlap_positive_books = positive_books - OVERLAP_POSITIVE_BOOKS
    positive_count = int(positive["occurrence_count"])
    negative_count = int(negative["occurrence_count"])
    strongest_count = int(strongest_control["occurrence_count"])
    separation_score = 0.0
    if positive_count:
        separation_score += min(1.0, len(non_overlap_positive_books) / 5.0) * 0.35
        separation_score += max(0.0, (positive_count - negative_count) / positive_count) * 0.30
        separation_score += 0.20 if strongest_count > positive_count else 0.0
        separation_score += 0.15 if negative_count <= 2 else 0.0

    if positive_count >= 8 and len(non_overlap_positive_books) >= 5 and negative_count <= 2:
        decision = "VINVINSTAE_OP_VTLR20_SURVIVES_NEGATIVE_CONTROL"
    elif positive_count >= 5 and negative_count <= positive_count:
        decision = "VINVINSTAE_OP_VTLR20_KEEP_FUNCTION_READY_NOT_STRONG"
    else:
        decision = "VINVINSTAE_OP_VTLR20_AUDIT_ONLY"

    cur = conn.execute(
        """
        INSERT INTO vinvin_negative_control_probe_runs
            (created_at, source_variant_run_id, source_vinvin_run_id,
             positive_occurrence_count, positive_book_count,
             negative_occurrence_count, negative_book_count,
             non_overlap_positive_book_count, strongest_control_key,
             strongest_control_occurrence_count, separation_score, decision, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            utc_now(),
            variant_run_id,
            vinvin_run_id,
            positive_count,
            len(positive_books),
            negative_count,
            len(negative["books"]),
            len(non_overlap_positive_books),
            strongest_control_key,
            strongest_count,
            separation_score,
            decision,
            jdump(
                {
                    "positive_books": sorted_books(positive_books),
                    "non_overlap_positive_books": sorted_books(non_overlap_positive_books),
                    "overlap_positive_books": sorted_books(positive_books & OVERLAP_POSITIVE_BOOKS),
                    "negative_books": sorted_books(set(negative["books"])),
                    "gloss_allowed": False,
                }
            ),
        ),
    )
    run_id = int(cur.lastrowid)

    for frame in FRAMES:
        frame_key = frame["frame_key"]
        data = frame_data[frame_key]
        books = set(data["books"])
        overlap_book_count = len(books & OVERLAP_POSITIVE_BOOKS)
        non_overlap_book_count = len(books - OVERLAP_POSITIVE_BOOKS)
        if frame_key == "POS_VINVINSTAE_OP_VTLR20":
            next_action = "keep_function_ready_pending_suffix_branch_semantics"
        elif frame_key == "NEG_IFTINSTAE_OP_VTLR20":
            next_action = "use_as_primary_negative_control"
        elif int(data["occurrence_count"]) >= positive_count:
            next_action = "formula_control_stronger_than_positive_do_not_promote_literal"
        else:
            next_action = "formula_control_reference"
        score = float(data["occurrence_count"]) + (0.1 * len(books))
        conn.execute(
            """
            INSERT INTO vinvin_negative_control_frame_items
                (run_id, frame_key, frame_class, frame_tokens_json, occurrence_count,
                 book_count, books_json, overlap_positive_book_count, non_overlap_book_count,
                 left_context_json, right_context_json, score, next_action, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                frame_key,
                data["frame_class"],
                jdump(frame["tokens"]),
                int(data["occurrence_count"]),
                len(books),
                jdump(sorted_books(books)),
                overlap_book_count,
                non_overlap_book_count,
                jdump(data["left"].most_common(8)),
                jdump(data["right"].most_common(8)),
                score,
                next_action,
                "{}",
            ),
        )

    for item in occurrences:
        conn.execute(
            """
            INSERT INTO vinvin_negative_control_occurrence_items
                (run_id, frame_key, bookid, occurrence_index, start_pos,
                 left_context, frame_text, right_context, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                item["frame_key"],
                item["bookid"],
                item["occurrence_index"],
                item["start_pos"],
                item["left"],
                item["frame_text"],
                item["right"],
                "{}",
            ),
        )

    conn.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "positive_occurrence_count": positive_count,
                "positive_book_count": len(positive_books),
                "negative_occurrence_count": negative_count,
                "negative_book_count": len(negative["books"]),
                "non_overlap_positive_book_count": len(non_overlap_positive_books),
                "strongest_control_key": strongest_control_key,
                "strongest_control_occurrence_count": strongest_count,
                "separation_score": round(separation_score, 4),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
