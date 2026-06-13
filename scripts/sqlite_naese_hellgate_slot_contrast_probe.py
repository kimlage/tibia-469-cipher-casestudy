#!/usr/bin/env python3
"""Contrast NAESE/IVIFAST slots using Hellgate38 and C68 negatives."""

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
CLEAN_BOOKS = {"5", "9", "48", "53"}
CONTROLLED_VARIANT_BOOKS = {"2", "22", "28", "51"}
RARE_BOOKS = {"13", "38", "41", "56"}
HELLGATE_BOOK = "38"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def jdump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS naese_hellgate_slot_contrast_probe_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_naese_run_id INTEGER NOT NULL,
            source_hellgate38_run_id INTEGER,
            source_overlap_holdout_run_id INTEGER,
            clean_count INTEGER NOT NULL,
            controlled_variant_count INTEGER NOT NULL,
            rare_count INTEGER NOT NULL,
            hellgate_supported INTEGER NOT NULL,
            contig_13_38_alive INTEGER NOT NULL,
            c68_negative_occurrence_count INTEGER NOT NULL,
            slot_specificity_score REAL NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS naese_hellgate_slot_contrast_items (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            occurrence_index INTEGER NOT NULL,
            slot_group TEXT NOT NULL,
            prefix_class TEXT NOT NULL,
            suffix_class TEXT NOT NULL,
            position_class TEXT NOT NULL,
            hellgate_relation TEXT NOT NULL,
            contig_relation TEXT NOT NULL,
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


def latest_optional_id(conn: sqlite3.Connection, table: str) -> int | None:
    row = conn.execute(f"SELECT run_id FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    return int(row["run_id"]) if row else None


def slot_group(bookid: str) -> str:
    if bookid in CLEAN_BOOKS:
        return "clean_dominant_slot"
    if bookid in CONTROLLED_VARIANT_BOOKS:
        return "controlled_variant_slot"
    if bookid in RARE_BOOKS:
        return "rare_slot_holdout"
    return "other_slot"


def next_action(group: str, bookid: str) -> str:
    if bookid == HELLGATE_BOOK:
        return "use_as_external_rare_slot_holdout_no_gloss"
    if group == "clean_dominant_slot":
        return "use_as_clean_slot_exemplar_no_gloss"
    if group == "controlled_variant_slot":
        return "compare_suffix_or_prefix_variant_no_gloss"
    return "audit_rare_slot_no_gloss"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)

    naese_run_id = latest_id(conn, "naese_ivifast_slot_probe_runs")
    hellgate_run_id = latest_optional_id(conn, "hellgate38_endpoint_template_probe_runs")
    overlap_run_id = latest_optional_id(conn, "overlap_formula_holdout_probe_runs")
    rows = conn.execute(
        """
        SELECT bookid, occurrence_index, prefix_class, suffix_class,
               position_class, next_action
        FROM naese_ivifast_slot_items
        WHERE run_id=?
        ORDER BY CAST(bookid AS INTEGER), occurrence_index
        """,
        (naese_run_id,),
    ).fetchall()
    c68_neg = conn.execute(
        """
        SELECT COALESCE(SUM(occurrence_count), 0) AS n
        FROM variant_frame_items
        WHERE run_id=(SELECT MAX(run_id) FROM variant_frame_items)
          AND frame_key IN ('C68_NCTIIN_FAMILY', 'C68_VNCTIIN_FAMILY')
        """
    ).fetchone()
    c68_negative_count = int(c68_neg["n"] or 0)
    hellgate_supported = 0
    if hellgate_run_id is not None:
        row = conn.execute(
            """
            SELECT *
            FROM hellgate38_endpoint_template_probe_runs
            WHERE run_id=? AND internal_anchor_found=1
            """,
            (hellgate_run_id,),
        ).fetchone()
        hellgate_supported = int(row is not None)
    contig_alive = 0
    if overlap_run_id is not None:
        row = conn.execute(
            """
            SELECT *
            FROM overlap_formula_holdout_edge_items
            WHERE run_id=?
              AND basecontigid='4'
              AND edge_index=1
              AND classification IN ('ALIVE_WEAK', 'ALIVE_STRONG')
            """,
            (overlap_run_id,),
        ).fetchone()
        contig_alive = int(row is not None)

    group_counts = Counter()
    class_counts = Counter()
    items = []
    for row in rows:
        bookid = str(row["bookid"])
        group = slot_group(bookid)
        group_counts[group] += 1
        class_counts[f"{row['prefix_class']}__{row['suffix_class']}"] += 1
        hellgate_relation = "external_hellgate38_holdout" if bookid == HELLGATE_BOOK and hellgate_supported else "not_external_holdout"
        contig_relation = "contig_13_38_alive" if bookid in {"13", "38"} and contig_alive else "no_contig_holdout"
        items.append(
            {
                "bookid": bookid,
                "occurrence_index": int(row["occurrence_index"]),
                "slot_group": group,
                "prefix_class": row["prefix_class"],
                "suffix_class": row["suffix_class"],
                "position_class": row["position_class"],
                "hellgate_relation": hellgate_relation,
                "contig_relation": contig_relation,
                "next_action": next_action(group, bookid),
            }
        )

    clean_count = group_counts["clean_dominant_slot"]
    controlled_count = group_counts["controlled_variant_slot"]
    rare_count = group_counts["rare_slot_holdout"]
    total = max(1, len(rows))
    slot_specificity_score = 0.0
    slot_specificity_score += min(0.25, clean_count * 0.06)
    slot_specificity_score += min(0.20, controlled_count * 0.05)
    slot_specificity_score += 0.20 if hellgate_supported else 0.0
    slot_specificity_score += 0.15 if contig_alive else 0.0
    slot_specificity_score += max(0.0, 0.20 - (c68_negative_count / max(1, total * 4)) * 0.20)

    if slot_specificity_score >= 0.70 and c68_negative_count <= total * 2:
        decision = "NAESE_IVIFAST_FUNCTION_READY_AFTER_HELLGATE"
    elif hellgate_supported and contig_alive:
        decision = "NAESE_IVIFAST_SLOT_CLASSIFIER_WITH_EXTERNAL_HOLDOUT"
    else:
        decision = "NAESE_IVIFAST_SLOT_CLASSIFIER_ONLY"

    cur = conn.execute(
        """
        INSERT INTO naese_hellgate_slot_contrast_probe_runs
            (created_at, source_naese_run_id, source_hellgate38_run_id,
             source_overlap_holdout_run_id, clean_count, controlled_variant_count,
             rare_count, hellgate_supported, contig_13_38_alive,
             c68_negative_occurrence_count, slot_specificity_score,
             decision, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            utc_now(),
            naese_run_id,
            hellgate_run_id,
            overlap_run_id,
            clean_count,
            controlled_count,
            rare_count,
            hellgate_supported,
            contig_alive,
            c68_negative_count,
            slot_specificity_score,
            decision,
            jdump({"group_counts": group_counts.most_common(), "class_counts": class_counts.most_common(), "gloss_allowed": False}),
        ),
    )
    run_id = int(cur.lastrowid)
    for item in items:
        conn.execute(
            """
            INSERT INTO naese_hellgate_slot_contrast_items
                (run_id, bookid, occurrence_index, slot_group, prefix_class,
                 suffix_class, position_class, hellgate_relation, contig_relation,
                 next_action, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                item["bookid"],
                item["occurrence_index"],
                item["slot_group"],
                item["prefix_class"],
                item["suffix_class"],
                item["position_class"],
                item["hellgate_relation"],
                item["contig_relation"],
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
                "clean_count": clean_count,
                "controlled_variant_count": controlled_count,
                "rare_count": rare_count,
                "hellgate_supported": bool(hellgate_supported),
                "contig_13_38_alive": bool(contig_alive),
                "c68_negative_occurrence_count": c68_negative_count,
                "slot_specificity_score": round(slot_specificity_score, 4),
                "group_counts": group_counts.most_common(),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
