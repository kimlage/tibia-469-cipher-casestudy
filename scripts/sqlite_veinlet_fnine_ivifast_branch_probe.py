#!/usr/bin/env python3
"""Audit the singleton VEINLET_FNINE_IVIFAST branch against sibling controls."""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "bonelord_operational.sqlite"
FRAME = ["O23", "N", "A", "F", "I", "E", "I"]
FNINE = ["V", "E", "I", "N", "L", "E", "T", "F", "N", "I", "N", "E"]
TIBEI = ["V", "E", "I", "N", "L", "E", "T", "T", "I", "B", "E", "I"]
FNAAST = ["V", "E", "I", "N", "L", "E", "T", "F", "N", "A", "A", "S", "T"]
IVIFAST = ["I", "V", "I", "F", "A", "S", "T"]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def jdump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS veinlet_fnine_ivifast_branch_probe_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_variant_run_id INTEGER NOT NULL,
            source_o23_branch_run_id INTEGER,
            source_naese_run_id INTEGER,
            fnine_count INTEGER NOT NULL,
            tibei_sibling_count INTEGER NOT NULL,
            fnaast_hellgate_count INTEGER NOT NULL,
            fnine_has_ivifast_tail INTEGER NOT NULL,
            fnine_overlaps_naese_books INTEGER NOT NULL,
            contrast_score REAL NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS veinlet_fnine_ivifast_branch_items (
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


def collect(tokens: list[str], branch: list[str]) -> list[int]:
    full = FRAME + branch
    return find_frame(tokens, full)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)

    variant_run_id = latest_id(conn, "row0_variant_frontier_runs")
    branch_run_id = latest_optional_id(conn, "o23_onaf_payload_branch_negative_probe_runs")
    naese_run_id = latest_optional_id(conn, "naese_ivifast_slot_probe_runs")
    naese_books = set()
    if naese_run_id is not None:
        naese_books = {
            str(row["bookid"])
            for row in conn.execute("SELECT DISTINCT bookid FROM naese_ivifast_slot_items WHERE run_id=?", (naese_run_id,))
        }
    rows = conn.execute(
        """
        SELECT bookid, tokens_json
        FROM row0_variant_book_tokens
        WHERE run_id=?
        ORDER BY CAST(bookid AS INTEGER)
        """,
        (variant_run_id,),
    ).fetchall()

    items = []
    fnine_count = 0
    tibei_count = 0
    fnaast_count = 0
    fnine_has_ivifast_tail = 0
    fnine_overlap_naese = 0
    for row in rows:
        bookid = str(row["bookid"])
        tokens = json.loads(row["tokens_json"] or "[]")
        for start in collect(tokens, FNINE):
            end = start + len(FRAME) + len(FNINE)
            right = tokens[end : min(len(tokens), end + 16)]
            fnine_count += 1
            has_ivifast = int(bool(find_frame(right, IVIFAST)) or right[: len(IVIFAST)] == IVIFAST)
            fnine_has_ivifast_tail += has_ivifast
            fnine_overlap_naese += int(bookid in naese_books)
            items.append((bookid, start, "VEINLET_FNINE_IVIFAST", FNINE, right, "audit_singleton_branch_with_ivifast_control"))
        for start in collect(tokens, TIBEI):
            end = start + len(FRAME) + len(TIBEI)
            right = tokens[end : min(len(tokens), end + 16)]
            tibei_count += 1
            items.append((bookid, start, "VEINLET_TIBEI_SHORT_SIBLING", TIBEI, right, "sibling_negative_control"))
        for start in collect(tokens, FNAAST):
            end = start + len(FRAME) + len(FNAAST)
            right = tokens[end : min(len(tokens), end + 16)]
            fnaast_count += 1
            items.append((bookid, start, "VEINLET_FNAAST_HELLGATE_CONTROL", FNAAST, right, "hellgate_branch_control"))

    contrast_score = 0.0
    contrast_score += 0.20 if fnine_count == 1 else 0.0
    contrast_score += 0.15 if tibei_count >= 1 else 0.0
    contrast_score += 0.15 if fnaast_count == 2 else 0.0
    contrast_score += 0.20 if fnine_has_ivifast_tail else 0.0
    contrast_score += 0.10 if fnine_overlap_naese else 0.0
    contrast_score += 0.20 if fnine_count == 1 and tibei_count == 1 and fnaast_count == 2 else 0.0
    if contrast_score >= 0.75 and fnine_count > 1:
        decision = "VEINLET_FNINE_IVIFAST_BRANCH_READY"
    elif contrast_score >= 0.60:
        decision = "VEINLET_FNINE_IVIFAST_SINGLETON_AUDITABLE"
    else:
        decision = "VEINLET_FNINE_IVIFAST_AUDIT_ONLY"

    cur = conn.execute(
        """
        INSERT INTO veinlet_fnine_ivifast_branch_probe_runs
            (created_at, source_variant_run_id, source_o23_branch_run_id,
             source_naese_run_id, fnine_count, tibei_sibling_count,
             fnaast_hellgate_count, fnine_has_ivifast_tail,
             fnine_overlaps_naese_books, contrast_score, decision, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            utc_now(),
            variant_run_id,
            branch_run_id,
            naese_run_id,
            fnine_count,
            tibei_count,
            fnaast_count,
            fnine_has_ivifast_tail,
            fnine_overlap_naese,
            contrast_score,
            decision,
            jdump({"gloss_allowed": False}),
        ),
    )
    run_id = int(cur.lastrowid)
    for idx, (bookid, start, branch_class, payload, right, action) in enumerate(items, start=1):
        conn.execute(
            """
            INSERT INTO veinlet_fnine_ivifast_branch_items
                (run_id, item_key, item_type, bookid, start_pos, branch_class,
                 frame_text, payload_text, right_context, next_action, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                f"{idx}:{bookid}:{start + 1}:{branch_class}",
                "branch_occurrence",
                bookid,
                start + 1,
                branch_class,
                " ".join(FRAME),
                " ".join(payload),
                " ".join(right),
                action,
                "{}",
            ),
        )
    conn.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "fnine_count": fnine_count,
                "tibei_sibling_count": tibei_count,
                "fnaast_hellgate_count": fnaast_count,
                "fnine_has_ivifast_tail": bool(fnine_has_ivifast_tail),
                "fnine_overlaps_naese_books": fnine_overlap_naese,
                "contrast_score": round(contrast_score, 4),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
