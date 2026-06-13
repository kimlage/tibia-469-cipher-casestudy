#!/usr/bin/env python3
"""Test NAESE/IVIFAST specificity against generic C68 frames."""

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
        CREATE TABLE IF NOT EXISTS naese_c68_negative_control_probe_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_naese_run_id INTEGER NOT NULL,
            source_variant_frame_run_id INTEGER NOT NULL,
            clean_exemplar_count INTEGER NOT NULL,
            controlled_variant_count INTEGER NOT NULL,
            rare_variant_count INTEGER NOT NULL,
            c68_negative_frame_count INTEGER NOT NULL,
            c68_negative_occurrence_count INTEGER NOT NULL,
            specificity_score REAL NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS naese_c68_negative_control_items (
            run_id INTEGER NOT NULL,
            item_key TEXT NOT NULL,
            item_type TEXT NOT NULL,
            bookid TEXT,
            class_name TEXT NOT NULL,
            occurrence_count INTEGER NOT NULL,
            book_count INTEGER NOT NULL,
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)

    naese_run_id = latest_id(conn, "naese_ivifast_slot_probe_runs")
    variant_run_id = latest_id(conn, "variant_frame_probe_runs")

    naese_rows = conn.execute(
        """
        SELECT bookid, prefix_class, suffix_class, next_action
        FROM naese_ivifast_slot_items
        WHERE run_id=?
        ORDER BY CAST(bookid AS INTEGER)
        """,
        (naese_run_id,),
    ).fetchall()
    variant_rows = conn.execute(
        """
        SELECT frame_key, occurrence_count, book_count, role_class, next_action
        FROM variant_frame_items
        WHERE run_id=?
          AND frame_key IN ('C68_NCTIIN_FAMILY', 'C68_VNCTIIN_FAMILY', 'C68_FATCT_SLOT')
        ORDER BY frame_key
        """,
        (variant_run_id,),
    ).fetchall()

    counts = Counter(row["next_action"] for row in naese_rows)
    clean_count = counts["clean_template_exemplar_for_function_inference"]
    controlled_count = counts["compare_suffix_variant_against_clean_template"] + counts["compare_prefix_variant_against_clean_template"]
    rare_count = counts["rare_variant_audit_only"]
    negative_occ = sum(int(row["occurrence_count"]) for row in variant_rows if row["frame_key"] in {"C68_NCTIIN_FAMILY", "C68_VNCTIIN_FAMILY"})
    negative_frames = sum(1 for row in variant_rows if row["frame_key"] in {"C68_NCTIIN_FAMILY", "C68_VNCTIIN_FAMILY"})

    clean_ratio = clean_count / max(1, len(naese_rows))
    controlled_ratio = (clean_count + controlled_count) / max(1, len(naese_rows))
    negative_pressure = min(1.0, negative_occ / max(1, len(naese_rows) * 2))
    specificity_score = (clean_ratio * 0.35) + (controlled_ratio * 0.35) + ((1.0 - negative_pressure) * 0.20) + (0.10 if rare_count <= 4 else 0.0)

    if specificity_score >= 0.70 and clean_count >= 6:
        decision = "NAESE_FUNCTION_CANDIDATE_SPECIFIC"
    elif controlled_ratio >= 0.60:
        decision = "NAESE_SLOT_CLASSIFIER_ONLY"
    else:
        decision = "NAESE_AUDIT_ONLY_C68_TOO_BROAD"

    cur = conn.execute(
        """
        INSERT INTO naese_c68_negative_control_probe_runs
            (created_at, source_naese_run_id, source_variant_frame_run_id,
             clean_exemplar_count, controlled_variant_count, rare_variant_count,
             c68_negative_frame_count, c68_negative_occurrence_count,
             specificity_score, decision, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            utc_now(),
            naese_run_id,
            variant_run_id,
            clean_count,
            controlled_count,
            rare_count,
            negative_frames,
            negative_occ,
            specificity_score,
            decision,
            jdump({"gloss_allowed": False, "naese_action_counts": counts.most_common()}),
        ),
    )
    run_id = int(cur.lastrowid)

    for row in naese_rows:
        key = f"NAESE:{row['bookid']}:{row['prefix_class']}:{row['suffix_class']}"
        conn.execute(
            """
            INSERT INTO naese_c68_negative_control_items
                (run_id, item_key, item_type, bookid, class_name,
                 occurrence_count, book_count, next_action, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                key,
                "naese_occurrence",
                str(row["bookid"]),
                f"{row['prefix_class']}__{row['suffix_class']}",
                1,
                1,
                row["next_action"],
                "{}",
            ),
        )
    for row in variant_rows:
        conn.execute(
            """
            INSERT INTO naese_c68_negative_control_items
                (run_id, item_key, item_type, bookid, class_name,
                 occurrence_count, book_count, next_action, payload_json)
            VALUES (?, ?, ?, NULL, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                f"C68_NEG:{row['frame_key']}",
                "c68_negative_frame",
                row["frame_key"],
                int(row["occurrence_count"]),
                int(row["book_count"]),
                row["next_action"],
                jdump({"role_class": row["role_class"]}),
            ),
        )

    conn.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "clean_exemplar_count": clean_count,
                "controlled_variant_count": controlled_count,
                "rare_variant_count": rare_count,
                "c68_negative_frame_count": negative_frames,
                "c68_negative_occurrence_count": negative_occ,
                "specificity_score": round(specificity_score, 4),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
