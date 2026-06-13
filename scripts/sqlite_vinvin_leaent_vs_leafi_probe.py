#!/usr/bin/env python3
"""Contrast VINVIN/VTLR LEAENT and LEAFI branches, without gloss."""

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


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def jdump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS vinvin_leaent_vs_leafi_probe_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_vinvin_suffix_run_id INTEGER NOT NULL,
            source_contig_overlap_run_id INTEGER NOT NULL,
            leaent_occurrence_count INTEGER NOT NULL,
            leafi_occurrence_count INTEGER NOT NULL,
            leaent_direct_edge_count INTEGER NOT NULL,
            leafi_direct_edge_count INTEGER NOT NULL,
            contrast_score REAL NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS vinvin_leaent_vs_leafi_items (
            run_id INTEGER NOT NULL,
            branch_key TEXT NOT NULL,
            bookid TEXT NOT NULL,
            suffix_class TEXT NOT NULL,
            start_pos INTEGER NOT NULL,
            contig_support_class TEXT NOT NULL,
            direct_edge_support TEXT NOT NULL,
            branch_status TEXT NOT NULL,
            next_action TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, branch_key, bookid, start_pos)
        );
        """
    )


def latest_id(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT run_id FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    if row is None:
        raise SystemExit(f"missing required table data: {table}")
    return int(row["run_id"])


def branch_key(row: sqlite3.Row) -> str:
    suffix = str(row["suffix_class"])
    if suffix == "INEIIVNSENI_STAR_LEAENT":
        return "VINVIN_BRANCH_INEIIVNSENI_STAR_LEAENT"
    if suffix == "INEIIVNSENI":
        text = f'{row["suffix_text"]}{row["right_context"]}'.replace(" ", "")
        if "LEAFI" in text:
            return "VINVIN_BRANCH_INEIIVNSENI_STAR_LEAFI"
        return "VINVIN_BRANCH_INEIIVNSENI_NO_LEAENT"
    return f"VINVIN_BRANCH_{suffix}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)

    suffix_run_id = latest_id(conn, "vinvin_suffix_contrast_probe_runs")
    contig_run_id = latest_id(conn, "contig_max_overlap_probe_runs")
    suffix_rows = conn.execute(
        """
        SELECT *
        FROM vinvin_suffix_contrast_items
        WHERE run_id=?
          AND suffix_class IN ('INEIIVNSENI_STAR_LEAENT', 'INEIIVNSENI')
        ORDER BY suffix_class, CAST(bookid AS INTEGER), start_pos
        """,
        (suffix_run_id,),
    ).fetchall()
    contig_edges = conn.execute(
        """
        SELECT *
        FROM contig_max_overlap_edges
        WHERE run_id=?
        ORDER BY basecontigid, edge_index
        """,
        (contig_run_id,),
    ).fetchall()

    direct_edge_books: dict[str, set[str]] = defaultdict(set)
    for edge in contig_edges:
        overlap = str(edge["overlap_text"])
        left = str(edge["left_bookid"])
        right = str(edge["right_bookid"])
        if "INEIIVNSENI*LEAENT" in overlap:
            direct_edge_books["VINVIN_BRANCH_INEIIVNSENI_STAR_LEAENT"].update({left, right})
        if "INEIIVNSENI*LEAFI" in overlap:
            direct_edge_books["VINVIN_BRANCH_INEIIVNSENI_STAR_LEAFI"].update({left, right})

    cur = conn.execute(
        """
        INSERT INTO vinvin_leaent_vs_leafi_probe_runs
            (created_at, source_vinvin_suffix_run_id, source_contig_overlap_run_id,
             leaent_occurrence_count, leafi_occurrence_count,
             leaent_direct_edge_count, leafi_direct_edge_count,
             contrast_score, decision, payload_json)
        VALUES (?, ?, ?, 0, 0, 0, 0, 0, ?, ?)
        """,
        (utc_now(), suffix_run_id, contig_run_id, "PENDING", "{}"),
    )
    run_id = int(cur.lastrowid)

    grouped: dict[str, list[sqlite3.Row]] = defaultdict(list)
    for row in suffix_rows:
        grouped[branch_key(row)].append(row)

    item_summaries: list[dict[str, Any]] = []
    for key, rows in sorted(grouped.items()):
        direct_books = direct_edge_books.get(key, set())
        for row in rows:
            bookid = str(row["bookid"])
            has_direct = bookid in direct_books
            if key == "VINVIN_BRANCH_INEIIVNSENI_STAR_LEAENT":
                status = "SUBFUNCTION_READY_DIRECT_OR_SURFACE"
                next_action = "promote_branch_only_no_gloss_if_policy_accepts"
            elif key == "VINVIN_BRANCH_INEIIVNSENI_STAR_LEAFI":
                status = "NEGATIVE_CONTRAST_BRANCH"
                next_action = "keep_as_leafi_negative_control"
            else:
                status = "AUDIT_BRANCH"
                next_action = "keep_as_unpromoted_local_alternation"
            payload = {
                "branch_key": key,
                "bookid": bookid,
                "suffix_class": row["suffix_class"],
                "direct_edge_books": sorted(direct_books, key=lambda value: int(value) if value.isdigit() else value),
                "direct_edge_supported": has_direct,
                "surface_support_only": key == "VINVIN_BRANCH_INEIIVNSENI_STAR_LEAENT" and not has_direct,
                "gloss_allowed": False,
            }
            item_summaries.append(payload)
            conn.execute(
                """
                INSERT INTO vinvin_leaent_vs_leafi_items
                    (run_id, branch_key, bookid, suffix_class, start_pos,
                     contig_support_class, direct_edge_support, branch_status,
                     next_action, payload_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    key,
                    bookid,
                    row["suffix_class"],
                    int(row["start_pos"]),
                    row["contig_support_class"],
                    "DIRECT_EDGE" if has_direct else "NO_DIRECT_EDGE",
                    status,
                    next_action,
                    jdump(payload),
                ),
            )

    leaent_items = grouped.get("VINVIN_BRANCH_INEIIVNSENI_STAR_LEAENT", [])
    leafi_items = grouped.get("VINVIN_BRANCH_INEIIVNSENI_STAR_LEAFI", [])
    leaent_direct = len(direct_edge_books.get("VINVIN_BRANCH_INEIIVNSENI_STAR_LEAENT", set()))
    leafi_direct = len(direct_edge_books.get("VINVIN_BRANCH_INEIIVNSENI_STAR_LEAFI", set()))
    contrast_score = 0.0
    contrast_score += min(0.30, len(leaent_items) * 0.10)
    contrast_score += min(0.30, len({row["bookid"] for row in leaent_items}) * 0.10)
    contrast_score += 0.25 if leaent_direct >= 2 else 0.10 if leaent_direct else 0.0
    contrast_score += 0.10 if leafi_items and leafi_direct == 0 else 0.0
    contrast_score -= 0.20 if leafi_direct else 0.0
    contrast_score = round(contrast_score, 4)
    decision = (
        "LEAENT_BRANCH_READY_SURFACE61_LIMITED_NO_GLOSS"
        if contrast_score >= 0.75 and leaent_direct >= 2 and len(leafi_items) >= 1 and leafi_direct == 0
        else "LEAENT_BRANCH_PARTIAL_OR_NEEDS_MORE_CONTRAST"
    )
    payload = {
        "gloss_allowed": False,
        "leaent_books": sorted({str(row["bookid"]) for row in leaent_items}, key=lambda value: int(value) if value.isdigit() else value),
        "leafi_books": sorted({str(row["bookid"]) for row in leafi_items}, key=lambda value: int(value) if value.isdigit() else value),
        "leaent_direct_edge_books": sorted(direct_edge_books.get("VINVIN_BRANCH_INEIIVNSENI_STAR_LEAENT", set()), key=lambda value: int(value) if value.isdigit() else value),
        "leafi_direct_edge_books": sorted(direct_edge_books.get("VINVIN_BRANCH_INEIIVNSENI_STAR_LEAFI", set()), key=lambda value: int(value) if value.isdigit() else value),
        "items": item_summaries,
    }
    conn.execute(
        """
        UPDATE vinvin_leaent_vs_leafi_probe_runs
        SET leaent_occurrence_count=?,
            leafi_occurrence_count=?,
            leaent_direct_edge_count=?,
            leafi_direct_edge_count=?,
            contrast_score=?,
            decision=?,
            payload_json=?
        WHERE run_id=?
        """,
        (
            len(leaent_items),
            len(leafi_items),
            leaent_direct,
            leafi_direct,
            contrast_score,
            decision,
            jdump(payload),
            run_id,
        ),
    )
    conn.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "contrast_score": contrast_score,
                "leaent_occurrence_count": len(leaent_items),
                "leafi_occurrence_count": len(leafi_items),
                "leaent_direct_edge_count": leaent_direct,
                "leafi_direct_edge_count": leafi_direct,
                "gloss_allowed": False,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
