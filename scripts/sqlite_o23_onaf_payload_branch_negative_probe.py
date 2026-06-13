#!/usr/bin/env python3
"""Validate O23_ONAFIEI payload branches and hard negatives, without gloss."""

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
FRAME = ["O23", "N", "A", "F", "I", "E", "I"]
VEINLET = ["V", "E", "I", "N", "L", "E", "T"]
FNAAST = ["F", "N", "A", "A", "S", "T"]
EXACT_PAYLOAD = VEINLET + FNAAST


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def jdump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS o23_onaf_payload_branch_negative_probe_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_variant_run_id INTEGER NOT NULL,
            source_o23_payload_run_id INTEGER,
            frame_occurrence_count INTEGER NOT NULL,
            frame_book_count INTEGER NOT NULL,
            exact_payload_count INTEGER NOT NULL,
            exact_payload_book_count INTEGER NOT NULL,
            hard_negative_o23_count INTEGER NOT NULL,
            fnaast_without_full_prefix_count INTEGER NOT NULL,
            branch_class_count_json TEXT NOT NULL,
            branch_specificity_score REAL NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS o23_onaf_payload_branch_negative_items (
            run_id INTEGER NOT NULL,
            item_key TEXT NOT NULL,
            item_type TEXT NOT NULL,
            bookid TEXT NOT NULL,
            start_pos INTEGER NOT NULL,
            branch_class TEXT NOT NULL,
            frame_text TEXT NOT NULL,
            payload_text TEXT NOT NULL,
            right_context TEXT NOT NULL,
            next_action TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, item_key)
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
    starts = []
    size = len(frame)
    for idx in range(0, len(tokens) - size + 1):
        if tokens[idx : idx + size] == frame:
            starts.append(idx)
    return starts


def classify_payload(tokens: list[str], payload_start: int) -> tuple[str, list[str]]:
    after = tokens[payload_start:]
    if after[: len(EXACT_PAYLOAD)] == EXACT_PAYLOAD:
        return "VEINLET_FNAAST_HELLGATE", EXACT_PAYLOAD
    if after[:7] == ["V", "E", "I", "N", "L", "E", "T"]:
        if after[7:11] == ["T", "I", "B", "E"]:
            return "VEINLET_TIBEI_SHORT", after[:11]
        if after[7:12] == ["F", "N", "I", "N", "E"]:
            return "VEINLET_FNINE_IVIFAST", after[:12]
        return "VEINLET_OTHER", after[:12]
    if not after:
        return "ONAF_TERMINAL", []
    if after[:4] == ["V", "E", "E", "I"]:
        return "ONAF_VEEI_VINVIN_BRANCH", after[:8]
    return "OTHER_PAYLOAD", after[:12]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)

    variant_run_id = latest_id(conn, "row0_variant_frontier_runs")
    payload_run_id = latest_optional_id(conn, "o23_onaf_payload_contrast_probe_runs")
    rows = conn.execute(
        """
        SELECT bookid, tokens_json
        FROM row0_variant_book_tokens
        WHERE run_id=?
        ORDER BY CAST(bookid AS INTEGER)
        """,
        (variant_run_id,),
    ).fetchall()

    frame_items: list[dict[str, Any]] = []
    hard_negative_o23: list[dict[str, Any]] = []
    fnaast_negatives: list[dict[str, Any]] = []
    frame_books = set()
    exact_payload_books = set()
    branch_counts: Counter[str] = Counter()

    for row in rows:
        bookid = str(row["bookid"])
        tokens = json.loads(row["tokens_json"] or "[]")
        frame_starts = find_frame(tokens, FRAME)
        frame_start_set = set(frame_starts)
        for start in frame_starts:
            payload_start = start + len(FRAME)
            branch_class, payload = classify_payload(tokens, payload_start)
            branch_counts[branch_class] += 1
            frame_books.add(bookid)
            if branch_class == "VEINLET_FNAAST_HELLGATE":
                exact_payload_books.add(bookid)
            frame_items.append(
                {
                    "bookid": bookid,
                    "start_pos": start + 1,
                    "branch_class": branch_class,
                    "payload": payload,
                    "right": tokens[payload_start + len(payload) : min(len(tokens), payload_start + len(payload) + 12)],
                }
            )
        for idx, token in enumerate(tokens):
            if token == "O23" and idx not in frame_start_set:
                hard_negative_o23.append(
                    {
                        "bookid": bookid,
                        "start_pos": idx + 1,
                        "right": tokens[idx + 1 : min(len(tokens), idx + 12)],
                    }
                )
        for idx in find_frame(tokens, FNAAST):
            expected_start = idx - len(VEINLET) - len(FRAME)
            has_full_prefix = expected_start >= 0 and tokens[expected_start : expected_start + len(FRAME) + len(VEINLET)] == FRAME + VEINLET
            if not has_full_prefix:
                fnaast_negatives.append(
                    {
                        "bookid": bookid,
                        "start_pos": idx + 1,
                        "left": tokens[max(0, idx - 12) : idx],
                        "right": tokens[idx + len(FNAAST) : min(len(tokens), idx + len(FNAAST) + 12)],
                    }
                )

    exact_payload_count = branch_counts["VEINLET_FNAAST_HELLGATE"]
    hard_negative_count = len(hard_negative_o23)
    fnaast_negative_count = len(fnaast_negatives)
    score = 0.0
    score += 0.20 if len(frame_books) >= 6 else min(0.20, len(frame_books) * 0.03)
    score += 0.25 if exact_payload_count == 2 and exact_payload_books == {"13", "38"} else 0.0
    score += max(0.0, 0.20 - hard_negative_count * 0.03)
    score += max(0.0, 0.20 - fnaast_negative_count * 0.02)
    score += 0.15 if {"VEINLET_TIBEI_SHORT", "VEINLET_FNINE_IVIFAST", "ONAF_TERMINAL", "ONAF_VEEI_VINVIN_BRANCH"} & set(branch_counts) else 0.0

    if score >= 0.80:
        decision = "O23_ONAF_PAYLOAD_BRANCHES_READY_NO_GLOSS"
    elif score >= 0.60:
        decision = "O23_ONAF_PAYLOAD_BRANCHES_CONTEXT_ONLY"
    else:
        decision = "O23_ONAF_PAYLOAD_BRANCHES_AUDIT_ONLY"

    cur = conn.execute(
        """
        INSERT INTO o23_onaf_payload_branch_negative_probe_runs
            (created_at, source_variant_run_id, source_o23_payload_run_id,
             frame_occurrence_count, frame_book_count, exact_payload_count,
             exact_payload_book_count, hard_negative_o23_count,
             fnaast_without_full_prefix_count, branch_class_count_json,
             branch_specificity_score, decision, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            utc_now(),
            variant_run_id,
            payload_run_id,
            len(frame_items),
            len(frame_books),
            exact_payload_count,
            len(exact_payload_books),
            hard_negative_count,
            fnaast_negative_count,
            jdump(branch_counts.most_common()),
            score,
            decision,
            jdump({"gloss_allowed": False, "exact_payload_books": sorted(exact_payload_books, key=int)}),
        ),
    )
    run_id = int(cur.lastrowid)

    for idx, item in enumerate(frame_items, start=1):
        conn.execute(
            """
            INSERT INTO o23_onaf_payload_branch_negative_items
                (run_id, item_key, item_type, bookid, start_pos, branch_class,
                 frame_text, payload_text, right_context, next_action, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                f"FRAME:{idx}:{item['bookid']}:{item['start_pos']}",
                "o23_onaf_payload_branch",
                item["bookid"],
                item["start_pos"],
                item["branch_class"],
                " ".join(FRAME),
                " ".join(item["payload"]),
                " ".join(item["right"]),
                "classify_payload_branch_no_gloss",
                "{}",
            ),
        )
    for idx, item in enumerate(hard_negative_o23[:25], start=1):
        conn.execute(
            """
            INSERT INTO o23_onaf_payload_branch_negative_items
                (run_id, item_key, item_type, bookid, start_pos, branch_class,
                 frame_text, payload_text, right_context, next_action, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                f"NEG_O23:{idx}:{item['bookid']}:{item['start_pos']}",
                "hard_negative_o23_without_onafiei",
                item["bookid"],
                item["start_pos"],
                "O23_WITHOUT_ONAFIEI",
                "O23",
                "",
                " ".join(item["right"]),
                "block_o23_alone_generalization",
                "{}",
            ),
        )
    for idx, item in enumerate(fnaast_negatives[:25], start=1):
        conn.execute(
            """
            INSERT INTO o23_onaf_payload_branch_negative_items
                (run_id, item_key, item_type, bookid, start_pos, branch_class,
                 frame_text, payload_text, right_context, next_action, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                f"NEG_FNAAST:{idx}:{item['bookid']}:{item['start_pos']}",
                "fnaast_without_full_o23_veinlet_prefix",
                item["bookid"],
                item["start_pos"],
                "FNAAST_WITHOUT_FULL_PREFIX",
                "",
                " ".join(FNAAST),
                " ".join(item["right"]),
                "block_fnaast_alone_generalization",
                jdump({"left_context": " ".join(item["left"])}),
            ),
        )
    conn.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "frame_occurrence_count": len(frame_items),
                "frame_book_count": len(frame_books),
                "exact_payload_count": exact_payload_count,
                "exact_payload_book_count": len(exact_payload_books),
                "hard_negative_o23_count": hard_negative_count,
                "fnaast_without_full_prefix_count": fnaast_negative_count,
                "branch_classes": branch_counts.most_common(),
                "branch_specificity_score": round(score, 4),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
