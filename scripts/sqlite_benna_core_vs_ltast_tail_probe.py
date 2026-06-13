#!/usr/bin/env python3
"""Contrast BENNA core against LTAST tail and the current residual target.

This probe keeps gloss disabled. It asks whether BENNA explains the current
semantic residue as a functional/formula bridge with boundary tail behavior.
"""

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
RESIDUAL_LABEL = "i_lo_eye"
RESIDUAL_BOOKS = {"5", "9", "11", "16", "43", "47", "50", "59", "69"}
BENNA_RESIDUAL_BOOKS = {"5", "9", "11", "43", "47", "50", "59", "69"}
PRIMARY_NEGATIVE_BOOKS = {"16"}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def jdump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS benna_core_vs_ltast_tail_probe_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_benna_run_id INTEGER NOT NULL,
            source_ltast_run_id INTEGER,
            residual_label TEXT NOT NULL,
            residual_book_count INTEGER NOT NULL,
            benna_residual_book_count INTEGER NOT NULL,
            negative_book_count INTEGER NOT NULL,
            clean_bridge_count INTEGER NOT NULL,
            suffix_variant_count INTEGER NOT NULL,
            ltast_tail_link_count INTEGER NOT NULL,
            other_suffix_count INTEGER NOT NULL,
            separation_score REAL NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS benna_core_vs_ltast_tail_items (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            occurrence_index INTEGER NOT NULL,
            target_class TEXT NOT NULL,
            prefix_class TEXT NOT NULL,
            suffix_class TEXT NOT NULL,
            benna_next_action TEXT NOT NULL,
            has_ltast_tail INTEGER NOT NULL,
            has_strong_boundary_tail INTEGER NOT NULL,
            left_symbol_context TEXT NOT NULL,
            right_symbol_context TEXT NOT NULL,
            functional_class TEXT NOT NULL,
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


def target_class(bookid: str) -> str:
    if bookid in BENNA_RESIDUAL_BOOKS:
        return "benna_residual_positive"
    if bookid in PRIMARY_NEGATIVE_BOOKS:
        return "primary_negative_residual_without_benna"
    if bookid in RESIDUAL_BOOKS:
        return "residual_other"
    return "benna_non_residual"


def functional_class(row: sqlite3.Row, has_ltast_tail: bool) -> str:
    if row["next_action"] == "clean_formula_bridge_candidate" and has_ltast_tail:
        return "clean_bridge_with_tail"
    if row["next_action"] == "clean_formula_bridge_candidate":
        return "clean_bridge_no_tail"
    if has_ltast_tail:
        return "suffix_variant_with_tail"
    if row["suffix_class"] == "OTHER_SUFFIX":
        return "other_suffix_variant"
    return "prefix_stable_suffix_variant"


def next_action(fclass: str, tclass: str) -> str:
    if tclass == "primary_negative_residual_without_benna":
        return "negative_control_no_benna_marker"
    if fclass == "clean_bridge_with_tail":
        return "mark_residue_as_formula_boundary_bridge_candidate"
    if fclass == "suffix_variant_with_tail":
        return "mark_residue_as_suffix_tail_variant_candidate"
    if fclass == "other_suffix_variant":
        return "keep_residue_unresolved_or_variant"
    return "keep_as_benna_formula_without_gloss"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)

    benna_run_id = latest_id(conn, "benna_concordance_probe_runs")
    ltast_run_id = latest_optional_id(conn, "ltast_boundary_probe_runs")
    rows = conn.execute(
        """
        SELECT bookid, occurrence_index, prefix_class, suffix_class, next_action,
               left_symbol_context, right_symbol_context
        FROM benna_concordance_items
        WHERE run_id=?
        ORDER BY CAST(bookid AS INTEGER), occurrence_index
        """,
        (benna_run_id,),
    ).fetchall()
    ltast_books = set()
    if ltast_run_id is not None:
        ltast_rows = conn.execute(
            """
            SELECT DISTINCT bookid
            FROM ltast_boundary_pair_items
            WHERE run_id=?
            """,
            (ltast_run_id,),
        ).fetchall()
        ltast_books = {str(row["bookid"]) for row in ltast_rows}

    items: list[dict[str, Any]] = []
    class_counts: Counter[str] = Counter()
    clean_bridge_count = 0
    suffix_variant_count = 0
    ltast_tail_link_count = 0
    other_suffix_count = 0

    for row in rows:
        bookid = str(row["bookid"])
        tclass = target_class(bookid)
        has_ltast_tail = "LTASTTN" in (row["right_symbol_context"] or "") or bookid in ltast_books
        has_strong_boundary_tail = bookid in ltast_books
        fclass = functional_class(row, has_ltast_tail)
        class_counts[f"{tclass}__{fclass}"] += 1
        clean_bridge_count += int(fclass == "clean_bridge_with_tail" or fclass == "clean_bridge_no_tail")
        suffix_variant_count += int(fclass == "suffix_variant_with_tail" or fclass == "prefix_stable_suffix_variant")
        ltast_tail_link_count += int(has_ltast_tail)
        other_suffix_count += int(fclass == "other_suffix_variant")
        items.append(
            {
                "bookid": bookid,
                "occurrence_index": int(row["occurrence_index"]),
                "target_class": tclass,
                "prefix_class": row["prefix_class"],
                "suffix_class": row["suffix_class"],
                "benna_next_action": row["next_action"],
                "has_ltast_tail": int(has_ltast_tail),
                "has_strong_boundary_tail": int(has_strong_boundary_tail),
                "left_symbol_context": row["left_symbol_context"] or "",
                "right_symbol_context": row["right_symbol_context"] or "",
                "functional_class": fclass,
                "next_action": next_action(fclass, tclass),
            }
        )

    positive_items = [item for item in items if item["target_class"] == "benna_residual_positive"]
    clean_positive = sum(1 for item in positive_items if item["functional_class"] == "clean_bridge_with_tail")
    tail_positive = sum(1 for item in positive_items if item["has_ltast_tail"])
    other_positive = sum(1 for item in positive_items if item["functional_class"] == "other_suffix_variant")
    negative_separated = len(PRIMARY_NEGATIVE_BOOKS)
    separation_score = 0.0
    if BENNA_RESIDUAL_BOOKS:
        separation_score += (len({item["bookid"] for item in positive_items}) / len(BENNA_RESIDUAL_BOOKS)) * 0.30
        separation_score += (tail_positive / max(1, len(positive_items))) * 0.25
        separation_score += (clean_positive / max(1, len(positive_items))) * 0.20
        separation_score += negative_separated * 0.15
        separation_score += max(0.0, 1.0 - (other_positive / max(1, len(positive_items)))) * 0.10

    if separation_score >= 0.70 and len(positive_items) >= 8:
        decision = "BENNA_EXPLAINS_RESIDUAL_AS_FUNCTIONAL_BRIDGE"
    elif len(positive_items) >= 5:
        decision = "BENNA_PARTIAL_RESIDUAL_BRIDGE_KEEP_READY"
    else:
        decision = "BENNA_DOES_NOT_EXPLAIN_RESIDUAL"

    cur = conn.execute(
        """
        INSERT INTO benna_core_vs_ltast_tail_probe_runs
            (created_at, source_benna_run_id, source_ltast_run_id, residual_label,
             residual_book_count, benna_residual_book_count, negative_book_count,
             clean_bridge_count, suffix_variant_count, ltast_tail_link_count,
             other_suffix_count, separation_score, decision, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            utc_now(),
            benna_run_id,
            ltast_run_id,
            RESIDUAL_LABEL,
            len(RESIDUAL_BOOKS),
            len({item["bookid"] for item in positive_items}),
            len(PRIMARY_NEGATIVE_BOOKS),
            clean_bridge_count,
            suffix_variant_count,
            ltast_tail_link_count,
            other_suffix_count,
            separation_score,
            decision,
            jdump(
                {
                    "residual_books": sorted(RESIDUAL_BOOKS, key=int),
                    "benna_residual_books": sorted(BENNA_RESIDUAL_BOOKS, key=int),
                    "primary_negative_books": sorted(PRIMARY_NEGATIVE_BOOKS, key=int),
                    "class_counts": class_counts.most_common(),
                    "gloss_allowed": False,
                }
            ),
        ),
    )
    run_id = int(cur.lastrowid)

    for item in items:
        conn.execute(
            """
            INSERT INTO benna_core_vs_ltast_tail_items
                (run_id, bookid, occurrence_index, target_class, prefix_class, suffix_class,
                 benna_next_action, has_ltast_tail, has_strong_boundary_tail,
                 left_symbol_context, right_symbol_context, functional_class,
                 next_action, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                item["bookid"],
                item["occurrence_index"],
                item["target_class"],
                item["prefix_class"],
                item["suffix_class"],
                item["benna_next_action"],
                item["has_ltast_tail"],
                item["has_strong_boundary_tail"],
                item["left_symbol_context"],
                item["right_symbol_context"],
                item["functional_class"],
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
                "residual_book_count": len(RESIDUAL_BOOKS),
                "benna_residual_book_count": len({item["bookid"] for item in positive_items}),
                "negative_book_count": len(PRIMARY_NEGATIVE_BOOKS),
                "clean_bridge_count": clean_bridge_count,
                "suffix_variant_count": suffix_variant_count,
                "ltast_tail_link_count": ltast_tail_link_count,
                "other_suffix_count": other_suffix_count,
                "separation_score": round(separation_score, 4),
                "class_counts": class_counts.most_common(),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
