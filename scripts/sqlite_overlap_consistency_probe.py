#!/usr/bin/env python3
"""Probe repeated digit-window consistency under candidate phase modes.

If books are overlapping fragments, repeated digit windows should decode to the
same letter windows under the correct mechanical phase more often than under
bad phases. This script measures that without using semantic gloss.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "bonelord_operational.sqlite"


MODES = [
    "all_offset_0",
    "all_offset_1",
    "odd_offset_1_even_0",
    "odd_offset_0_even_1",
    "bookid_parity",
    "bookid_inverse_parity",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def jdump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def one(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> sqlite3.Row:
    row = conn.execute(sql, params).fetchone()
    if row is None:
        raise SystemExit(f"missing required row for query: {sql}")
    return row


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS overlap_consistency_probe_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_german_run_id INTEGER NOT NULL,
            window_digits INTEGER NOT NULL,
            min_occurrences INTEGER NOT NULL,
            mode_count INTEGER NOT NULL,
            best_mode TEXT NOT NULL,
            best_consistency_score REAL NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS overlap_consistency_probe_items (
            run_id INTEGER NOT NULL,
            mode_key TEXT NOT NULL,
            repeated_windows INTEGER NOT NULL,
            repeated_occurrences INTEGER NOT NULL,
            consistent_windows INTEGER NOT NULL,
            inconsistent_windows INTEGER NOT NULL,
            consistency_score REAL NOT NULL,
            top_inconsistent_json TEXT NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, mode_key)
        );
        """
    )


def offset_for(mode: str, bookid: str, digits: str) -> int:
    if mode == "all_offset_0":
        return 0
    if mode == "all_offset_1":
        return 1
    if mode == "odd_offset_1_even_0":
        return 1 if len(digits) % 2 else 0
    if mode == "odd_offset_0_even_1":
        return 0 if len(digits) % 2 else 1
    if mode == "bookid_parity":
        return int(bookid) % 2
    if mode == "bookid_inverse_parity":
        return 1 - (int(bookid) % 2)
    raise ValueError(mode)


def decode_window(window: str, mapping: dict[str, str], absolute_start: int, offset: int) -> str:
    # Decode only pairs whose local positions align to the chosen offset.
    chars: list[str] = []
    local_start = absolute_start
    first = 0
    while (local_start + first - offset) % 2 != 0 and first < len(window):
        first += 1
    for idx in range(first, len(window) - 1, 2):
        pair = window[idx : idx + 2]
        chars.append(mapping.get(pair, "?"))
    return "".join(chars)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--window-digits", type=int, default=12)
    parser.add_argument("--min-occurrences", type=int, default=2)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)

    german = one(conn, "SELECT * FROM german_candidate_runs ORDER BY run_id DESC LIMIT 1")
    mapping = {
        row["code"]: row["letter"]
        for row in conn.execute(
            "SELECT code, letter FROM external_candidate_solution_mapping WHERE run_id=?",
            (german["candidate_solution_run_id"],),
        )
    }
    books = conn.execute(
        """
        SELECT CAST(bookid AS TEXT) AS bookid, MAX(digits) AS digits
        FROM sheet__books
        WHERE bookid IS NOT NULL
        GROUP BY CAST(bookid AS INTEGER)
        ORDER BY CAST(bookid AS INTEGER)
        """
    ).fetchall()

    mode_results: list[dict[str, Any]] = []
    for mode in MODES:
        buckets: dict[str, list[tuple[str, int, str]]] = defaultdict(list)
        for row in books:
            bookid = str(row["bookid"])
            digits = row["digits"]
            offset = offset_for(mode, bookid, digits)
            for start in range(0, len(digits) - args.window_digits + 1):
                window = digits[start : start + args.window_digits]
                decoded = decode_window(window, mapping, start, offset)
                buckets[window].append((bookid, start, decoded))
        repeated = {k: v for k, v in buckets.items() if len(v) >= args.min_occurrences}
        consistent = 0
        inconsistent = 0
        repeated_occurrences = 0
        top_inconsistent: list[dict[str, Any]] = []
        for window, occs in repeated.items():
            repeated_occurrences += len(occs)
            decoded_set = {decoded for _, _, decoded in occs}
            if len(decoded_set) == 1:
                consistent += 1
            else:
                inconsistent += 1
                if len(top_inconsistent) < 12:
                    top_inconsistent.append(
                        {
                            "window": window,
                            "occurrences": [
                                {"bookid": bookid, "start": start, "decoded": decoded}
                                for bookid, start, decoded in occs[:6]
                            ],
                        }
                    )
        score = consistent / max(1, consistent + inconsistent) * 100.0
        mode_results.append(
            {
                "mode_key": mode,
                "repeated_windows": len(repeated),
                "repeated_occurrences": repeated_occurrences,
                "consistent_windows": consistent,
                "inconsistent_windows": inconsistent,
                "consistency_score": round(score, 6),
                "top_inconsistent": top_inconsistent,
            }
        )

    best = max(mode_results, key=lambda x: (x["consistency_score"], x["repeated_windows"]))
    cur = conn.execute(
        """
        INSERT INTO overlap_consistency_probe_runs
            (created_at, source_german_run_id, window_digits, min_occurrences,
             mode_count, best_mode, best_consistency_score, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            utc_now(),
            german["run_id"],
            args.window_digits,
            args.min_occurrences,
            len(MODES),
            best["mode_key"],
            best["consistency_score"],
            jdump({"purpose": "phase validation via repeated digit-window consistency"}),
        ),
    )
    run_id = int(cur.lastrowid)
    for result in mode_results:
        decision = "BEST_OVERLAP_MODE" if result["mode_key"] == best["mode_key"] else "COMPARE_ONLY"
        conn.execute(
            """
            INSERT INTO overlap_consistency_probe_items
                (run_id, mode_key, repeated_windows, repeated_occurrences,
                 consistent_windows, inconsistent_windows, consistency_score,
                 top_inconsistent_json, decision, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                result["mode_key"],
                result["repeated_windows"],
                result["repeated_occurrences"],
                result["consistent_windows"],
                result["inconsistent_windows"],
                result["consistency_score"],
                jdump(result["top_inconsistent"]),
                decision,
                "{}",
            ),
        )
    conn.commit()

    print(
        json.dumps(
            {
                "overlap_probe_run_id": run_id,
                "window_digits": args.window_digits,
                "best_mode": best["mode_key"],
                "best_consistency_score": best["consistency_score"],
                "modes": [
                    {
                        "mode_key": r["mode_key"],
                        "repeated_windows": r["repeated_windows"],
                        "consistent_windows": r["consistent_windows"],
                        "inconsistent_windows": r["inconsistent_windows"],
                        "consistency_score": r["consistency_score"],
                    }
                    for r in sorted(mode_results, key=lambda x: (-x["consistency_score"], x["mode_key"]))
                ],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
