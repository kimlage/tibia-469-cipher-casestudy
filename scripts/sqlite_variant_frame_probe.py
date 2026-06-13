#!/usr/bin/env python3
"""Materialize local frames for C/R/O row0 variants before semantic promotion."""

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
    ("C86_ICE_OPERATOR_OPEN", ["*00", "I", "C86", "E"], "operator_payload_right"),
    ("C68_VNCTIIN_FAMILY", ["V", "N", "C68", "T", "I", "I", "N"], "family_marker"),
    ("C68_NCTIIN_FAMILY", ["N", "C68", "T", "I", "I", "N"], "family_marker"),
    ("C68_FATCT_SLOT", ["F", "A", "T", "C68", "T"], "slot_marker"),
    ("R20_VTLRNEFIE_BLOCK", ["V", "T", "L", "R20", "N", "E", "F", "I", "E"], "block_formula"),
    ("R20_VAETRFEVAST_BLOCK", ["V", "A", "E", "T", "R20", "F", "E", "V", "A", "S", "T"], "block_formula"),
    ("R02_TRVEIIVNTBB_BRIDGE", ["T", "R02", "V", "E", "I", "I", "V", "N", "T", "B", "B"], "bridge_formula"),
    ("R20_LIVRN_MICRO", ["L", "I", "V", "R20", "N"], "microfamily"),
    ("R02_LIVRN_MICRO", ["L", "I", "V", "R02", "N"], "microfamily"),
    ("O23_ONAF_FAMILY", ["O23", "N", "A", "F"], "supported_minor_family"),
    ("O32_SINGLETON", ["O32"], "singleton_audit_only"),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def jdump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS variant_frame_probe_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_variant_run_id INTEGER NOT NULL,
            frame_count INTEGER NOT NULL,
            observed_frame_count INTEGER NOT NULL,
            total_occurrence_count INTEGER NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS variant_frame_items (
            run_id INTEGER NOT NULL,
            frame_key TEXT NOT NULL,
            frame_tokens_json TEXT NOT NULL,
            role_class TEXT NOT NULL,
            occurrence_count INTEGER NOT NULL,
            book_count INTEGER NOT NULL,
            books_json TEXT NOT NULL,
            left_context_json TEXT NOT NULL,
            right_context_json TEXT NOT NULL,
            next_action TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, frame_key)
        );

        CREATE TABLE IF NOT EXISTS variant_frame_occurrence_items (
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


def find_frame(tokens: list[str], frame: list[str]) -> list[int]:
    starts: list[int] = []
    size = len(frame)
    for idx in range(0, len(tokens) - size + 1):
        if tokens[idx : idx + size] == frame:
            starts.append(idx)
    return starts


def action_for(frame_key: str, count: int) -> str:
    if frame_key == "O32_SINGLETON":
        return "preserve_do_not_promote"
    if count == 0:
        return "not_observed_in_current_variant_corpus"
    if frame_key.startswith("C86_"):
        return "treat_as_operator_with_right_payload"
    if frame_key.startswith("C68_"):
        return "treat_as_context_frame_not_global_C"
    if frame_key.startswith("R20_") or frame_key.startswith("R02_"):
        return "treat_as_phase_frame_not_global_R"
    return "audit_context_before_gloss"


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

    frame_data: dict[str, dict[str, Any]] = {}
    occurrences: list[dict[str, Any]] = []
    for frame_key, frame_tokens, role in FRAMES:
        frame_data[frame_key] = {
            "frame_tokens": frame_tokens,
            "role": role,
            "count": 0,
            "books": set(),
            "left": Counter(),
            "right": Counter(),
        }
        for row in rows:
            tokens = json.loads(row["tokens_json"] or "[]")
            starts = find_frame(tokens, frame_tokens)
            for occurrence_index, start in enumerate(starts, start=1):
                end = start + len(frame_tokens)
                left = " ".join(tokens[max(0, start - 8) : start])
                right = " ".join(tokens[end : min(len(tokens), end + 8)])
                frame_text = " ".join(frame_tokens)
                frame_data[frame_key]["count"] += 1
                frame_data[frame_key]["books"].add(str(row["bookid"]))
                frame_data[frame_key]["left"][left] += 1
                frame_data[frame_key]["right"][right] += 1
                occurrences.append(
                    {
                        "frame_key": frame_key,
                        "bookid": str(row["bookid"]),
                        "occurrence_index": occurrence_index,
                        "start_pos": start + 1,
                        "left": left,
                        "frame_text": frame_text,
                        "right": right,
                    }
                )

    observed = sum(1 for data in frame_data.values() if data["count"] > 0)
    total = sum(int(data["count"]) for data in frame_data.values())
    cur = conn.execute(
        """
        INSERT INTO variant_frame_probe_runs
            (created_at, source_variant_run_id, frame_count, observed_frame_count,
             total_occurrence_count, decision, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            utc_now(),
            variant_run_id,
            len(FRAMES),
            observed,
            total,
            "VARIANT_LOCAL_FRAMES_READY",
            jdump({"semantic_gloss_assigned": False, "purpose": "reduce contradiction before gloss"}),
        ),
    )
    run_id = int(cur.lastrowid)

    for frame_key, data in frame_data.items():
        count = int(data["count"])
        action = action_for(frame_key, count)
        conn.execute(
            """
            INSERT INTO variant_frame_items
                (run_id, frame_key, frame_tokens_json, role_class, occurrence_count,
                 book_count, books_json, left_context_json, right_context_json,
                 next_action, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                frame_key,
                jdump(data["frame_tokens"]),
                data["role"],
                count,
                len(data["books"]),
                jdump(sorted(data["books"], key=lambda value: int(value) if value.isdigit() else value)),
                jdump(data["left"].most_common(10)),
                jdump(data["right"].most_common(10)),
                action,
                "{}",
            ),
        )

    for occurrence in occurrences:
        conn.execute(
            """
            INSERT INTO variant_frame_occurrence_items
                (run_id, frame_key, bookid, occurrence_index, start_pos,
                 left_context, frame_text, right_context, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                occurrence["frame_key"],
                occurrence["bookid"],
                occurrence["occurrence_index"],
                occurrence["start_pos"],
                occurrence["left"],
                occurrence["frame_text"],
                occurrence["right"],
                "{}",
            ),
        )

    conn.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": "VARIANT_LOCAL_FRAMES_READY",
                "frame_count": len(FRAMES),
                "observed_frame_count": observed,
                "total_occurrence_count": total,
                "frames": [
                    {
                        "frame_key": key,
                        "occurrence_count": int(data["count"]),
                        "book_count": len(data["books"]),
                        "role_class": data["role"],
                    }
                    for key, data in frame_data.items()
                ],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
