#!/usr/bin/env python3
"""Score LTAST/ENIIFINI*LTASTTN as a boundary/continuation operator."""

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


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def jdump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS ltast_boundary_probe_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_template_slot_run_id INTEGER NOT NULL,
            crossing_count INTEGER NOT NULL,
            tail_count INTEGER NOT NULL,
            paired_count INTEGER NOT NULL,
            tail_without_crossing_count INTEGER NOT NULL,
            pair_coverage REAL NOT NULL,
            delta_invariance REAL NOT NULL,
            right_context_identity REAL NOT NULL,
            score INTEGER NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS ltast_boundary_pair_items (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            crossing_start_pos INTEGER NOT NULL,
            tail_start_pos INTEGER NOT NULL,
            delta_start INTEGER NOT NULL,
            crossing_position_class TEXT NOT NULL,
            tail_position_class TEXT NOT NULL,
            crossing_left_context TEXT NOT NULL,
            crossing_right_context TEXT NOT NULL,
            tail_right_context TEXT NOT NULL,
            right_context_identical INTEGER NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid, crossing_start_pos, tail_start_pos)
        );

        CREATE TABLE IF NOT EXISTS ltast_boundary_tail_unpaired_items (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            tail_start_pos INTEGER NOT NULL,
            tail_position_class TEXT NOT NULL,
            left_context TEXT NOT NULL,
            right_context TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid, tail_start_pos)
        );
        """
    )


def latest_id(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT run_id FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    if row is None:
        raise SystemExit(f"missing required table data: {table}")
    return int(row["run_id"])


def pct(numerator: int, denominator: int) -> float:
    return float(numerator) / float(denominator) if denominator else 0.0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)

    source_run_id = latest_id(conn, "template_slot_probe_runs")
    occurrences = conn.execute(
        """
        SELECT family_key, bookid, start_pos, position_class, left_context, right_context
        FROM template_slot_occurrence_items
        WHERE run_id=?
          AND family_key IN ('LTAST_TAIL', 'STAR_CROSSING_ENIIFINI_LTASTTN')
        ORDER BY CAST(bookid AS INTEGER), start_pos
        """,
        (source_run_id,),
    ).fetchall()

    crossings = [row for row in occurrences if row["family_key"] == "STAR_CROSSING_ENIIFINI_LTASTTN"]
    tails = [row for row in occurrences if row["family_key"] == "LTAST_TAIL"]
    crossing_by_book = {}
    for row in crossings:
        crossing_by_book.setdefault(str(row["bookid"]), []).append(row)

    pairs = []
    unpaired_tails = []
    for tail in tails:
        bookid = str(tail["bookid"])
        candidates = crossing_by_book.get(bookid, [])
        paired = False
        for crossing in candidates:
            delta = int(tail["start_pos"]) - int(crossing["start_pos"])
            if delta == 9:
                pairs.append((crossing, tail, delta))
                paired = True
        if not paired:
            unpaired_tails.append(tail)

    delta_ok = sum(1 for _, _, delta in pairs if delta == 9)
    right_identity = sum(1 for crossing, tail, _ in pairs if (crossing["right_context"] or "") == (tail["right_context"] or ""))
    pair_coverage = pct(len(pairs), len(crossings))
    delta_invariance = pct(delta_ok, len(pairs))
    right_context_identity = pct(right_identity, len(pairs))

    score = 0
    if pair_coverage >= 0.90:
        score += 30
    if delta_invariance >= 0.95:
        score += 25
    if right_context_identity >= 0.90:
        score += 20
    if pct(len(unpaired_tails), len(tails)) <= 0.15:
        score += 15
    score += 10
    if score >= 85:
        decision = "LTAST_BOUNDARY_CONTINUATION_STRONG"
    elif score >= 70:
        decision = "LTAST_BOUNDARY_CONTINUATION_PROBABLE"
    elif score >= 50:
        decision = "LTAST_FORMULA_NOT_OPERATOR"
    else:
        decision = "LTAST_WEAK_OR_LOCAL_PATTERN"

    cur = conn.execute(
        """
        INSERT INTO ltast_boundary_probe_runs
            (created_at, source_template_slot_run_id, crossing_count, tail_count,
             paired_count, tail_without_crossing_count, pair_coverage,
             delta_invariance, right_context_identity, score, decision, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            utc_now(),
            source_run_id,
            len(crossings),
            len(tails),
            len(pairs),
            len(unpaired_tails),
            pair_coverage,
            delta_invariance,
            right_context_identity,
            score,
            decision,
            jdump(
                {
                    "interpretation": "boundary handoff, not lexical meaning",
                    "position_classes": Counter(
                        [f"crossing:{row['position_class']}" for row in crossings]
                        + [f"tail:{row['position_class']}" for row in tails]
                    ).most_common(),
                }
            ),
        ),
    )
    run_id = int(cur.lastrowid)

    for crossing, tail, delta in pairs:
        identical = int((crossing["right_context"] or "") == (tail["right_context"] or ""))
        conn.execute(
            """
            INSERT INTO ltast_boundary_pair_items
                (run_id, bookid, crossing_start_pos, tail_start_pos, delta_start,
                 crossing_position_class, tail_position_class, crossing_left_context,
                 crossing_right_context, tail_right_context, right_context_identical,
                 payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                str(tail["bookid"]),
                int(crossing["start_pos"]),
                int(tail["start_pos"]),
                delta,
                crossing["position_class"],
                tail["position_class"],
                crossing["left_context"] or "",
                crossing["right_context"] or "",
                tail["right_context"] or "",
                identical,
                "{}",
            ),
        )

    for tail in unpaired_tails:
        conn.execute(
            """
            INSERT INTO ltast_boundary_tail_unpaired_items
                (run_id, bookid, tail_start_pos, tail_position_class, left_context,
                 right_context, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                str(tail["bookid"]),
                int(tail["start_pos"]),
                tail["position_class"],
                tail["left_context"] or "",
                tail["right_context"] or "",
                "{}",
            ),
        )

    conn.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "score": score,
                "crossing_count": len(crossings),
                "tail_count": len(tails),
                "paired_count": len(pairs),
                "tail_without_crossing_count": len(unpaired_tails),
                "pair_coverage": pair_coverage,
                "delta_invariance": delta_invariance,
                "right_context_identity": right_context_identity,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
