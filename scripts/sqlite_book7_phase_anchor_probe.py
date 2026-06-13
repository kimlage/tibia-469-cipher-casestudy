#!/usr/bin/env python3
"""Probe book 7 local phase/omission anchors, no gloss."""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "bonelord_operational.sqlite"
PATTERNS = {
    "TIINNEF_PHASE_ANCHOR": ["T", "I", "I", "N", "N", "E", "F"],
    "NEIAAETTA_CONTINUITY": ["N", "E", "I", "A", "A", "E", "T", "T", "A"],
    "AAETTA_SWALLOW_CONTROL": ["A", "A", "E", "T", "T", "A"],
    "NENIIF_SWALLOW_CONTROL": ["N", "E", "N", "I", "I", "F"],
    "EIEINT_SWALLOW_CONTROL": ["E", "I", "E", "I", "N", "T"],
}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def jdump(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def find_positions(tokens: list[str], pattern: list[str]) -> list[int]:
    size = len(pattern)
    return [idx for idx in range(0, len(tokens) - size + 1) if tokens[idx : idx + size] == pattern]


def latest_id(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT run_id FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    if row is None:
        raise SystemExit(f"missing required table data: {table}")
    return int(row[0])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()
    conn = sqlite3.connect(args.db, timeout=30)
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS book7_phase_anchor_probe_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_row0_variant_run_id INTEGER NOT NULL,
            phase_anchor_positive_count INTEGER NOT NULL,
            continuity_positive_count INTEGER NOT NULL,
            swallow_control_count INTEGER NOT NULL,
            local_score REAL NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS book7_phase_anchor_items (
            run_id INTEGER NOT NULL,
            pattern_id TEXT NOT NULL,
            bookid TEXT NOT NULL,
            positions_json TEXT NOT NULL,
            context_status TEXT NOT NULL,
            next_action TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, pattern_id, bookid)
        );
        """
    )
    row0_run_id = latest_id(conn, "row0_variant_frontier_runs")
    rows = conn.execute("SELECT bookid, tokens_json FROM row0_variant_book_tokens WHERE run_id=?", (row0_run_id,)).fetchall()
    tokens_by_book = {str(bookid): json.loads(tokens_json or "[]") for bookid, tokens_json in rows}
    cur = conn.execute(
        """
        INSERT INTO book7_phase_anchor_probe_runs
            (created_at, source_row0_variant_run_id, phase_anchor_positive_count,
             continuity_positive_count, swallow_control_count, local_score, decision, payload_json)
        VALUES (?, ?, 0, 0, 0, 0, ?, ?)
        """,
        (utc_now(), row0_run_id, "PENDING", "{}"),
    )
    run_id = int(cur.lastrowid)
    phase_positive = 0
    continuity_positive = 0
    swallow = 0
    summaries = []
    for pattern_id, pattern in PATTERNS.items():
        for bookid, tokens in tokens_by_book.items():
            positions = find_positions(tokens, pattern)
            if not positions:
                continue
            if pattern_id == "TIINNEF_PHASE_ANCHOR" and bookid in {"7", "57"}:
                status = "PHASE_ANCHOR_POSITIVE"
                next_action = "candidate_phase_omission_anchor_no_gloss"
                phase_positive += 1
            elif pattern_id == "NEIAAETTA_CONTINUITY" and bookid in {"7", "6"}:
                status = "CONTINUITY_POSITIVE"
                next_action = "candidate_local_continuity_anchor_no_gloss"
                continuity_positive += 1
            elif pattern_id.endswith("SWALLOW_CONTROL") and bookid in {"7", "9"}:
                status = "SWALLOW_CONTROL"
                next_action = "block_semantic_promotion_if_candidate_collapses_here"
                swallow += 1
            else:
                status = "OUTSIDE_OR_BACKGROUND_HIT"
                next_action = "keep_as_background_control"
            payload = {"pattern_id": pattern_id, "bookid": bookid, "positions": positions, "gloss_allowed": False}
            summaries.append(payload)
            conn.execute(
                """
                INSERT INTO book7_phase_anchor_items
                    (run_id, pattern_id, bookid, positions_json, context_status, next_action, payload_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (run_id, pattern_id, bookid, jdump(positions), status, next_action, jdump(payload)),
            )
    score = 0.0
    score += min(0.30, phase_positive * 0.10)
    score += min(0.25, continuity_positive * 0.10)
    score += 0.15 if swallow >= 2 else 0.0
    score += 0.10
    score = round(score, 4)
    decision = "BOOK7_PHASE_ANCHORS_AUDIT_READY_NO_GLOSS" if score >= 0.50 else "BOOK7_PHASE_ANCHORS_BACKGROUND_ONLY"
    conn.execute(
        """
        UPDATE book7_phase_anchor_probe_runs
        SET phase_anchor_positive_count=?, continuity_positive_count=?,
            swallow_control_count=?, local_score=?, decision=?, payload_json=?
        WHERE run_id=?
        """,
        (phase_positive, continuity_positive, swallow, score, decision, jdump({"items": summaries, "gloss_allowed": False}), run_id),
    )
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": decision, "phase_anchor_positive_count": phase_positive, "continuity_positive_count": continuity_positive, "swallow_control_count": swallow, "local_score": score, "gloss_allowed": False}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
