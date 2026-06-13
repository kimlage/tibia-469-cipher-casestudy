#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Sequence

from sqlite_dead_branch_rules import matching_dead_rules
from sqlite_probe_registry import init_schema as init_probe_registry_schema
from sqlite_snapshot_ref import DEFAULT_SNAPSHOT_NAME, resolve_export_id


DEFAULT_DB = "./data/bonelord_operational.sqlite"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SQLite-first gate before any new confirmation lane")
    parser.add_argument("--db", default=DEFAULT_DB, help="SQLite DB path")
    parser.add_argument("--export-id", type=int, default=None, help="Specific snapshot export_id")
    parser.add_argument("--snapshot-name", default=DEFAULT_SNAPSHOT_NAME, help="Named snapshot ref to use")
    parser.add_argument("--family", required=True, help="Candidate family id")
    parser.add_argument("--search", action="append", required=True, help="One or more raw search terms")
    parser.add_argument("--limit", type=int, default=20, help="Max hits per sheet family")
    return parser.parse_args()


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def latest_export_id(
    conn: sqlite3.Connection,
    export_id: int | None = None,
    snapshot_name: str = DEFAULT_SNAPSHOT_NAME,
) -> int:
    return resolve_export_id(conn, export_id=export_id, snapshot_name=snapshot_name)


def probe_stats(conn: sqlite3.Connection, family: str, searches: Sequence[str]) -> Dict[str, object]:
    row = conn.execute(
        """
        SELECT
            COUNT(*) AS runs,
            SUM(CASE WHEN outcome = 'DP_UNUSED' THEN 1 ELSE 0 END) AS dp_unused,
            SUM(CASE WHEN outcome = 'GT_HARD_FAIL' THEN 1 ELSE 0 END) AS gt_hard_fail,
            SUM(CASE WHEN outcome = 'NO_OP' THEN 1 ELSE 0 END) AS no_op,
            SUM(CASE WHEN outcome = 'STALLED_NO_CHECKPOINT' THEN 1 ELSE 0 END) AS stalled,
            MAX(created_at) AS last_seen
        FROM probe_runs
        WHERE family = ?
        """,
        (family,),
    ).fetchone()
    out = dict(row)
    out["runs"] = int(out["runs"] or 0)
    out["dp_unused"] = int(out["dp_unused"] or 0)
    out["gt_hard_fail"] = int(out["gt_hard_fail"] or 0)
    out["no_op"] = int(out["no_op"] or 0)
    out["stalled"] = int(out["stalled"] or 0)
    out["dead"] = (
        out["dp_unused"] >= 2
        or out["gt_hard_fail"] >= 2
        or out["no_op"] >= 2
        or out["stalled"] >= 2
    )
    known_dead = matching_dead_rules((family, *searches))
    out["known_dead_rules"] = [rule.label for rule in known_dead]
    if known_dead:
        out["dead"] = True
    return out


def hits_for_table(
    conn: sqlite3.Connection,
    table: str,
    field: str,
    searches: Sequence[str],
    export_id: int,
    limit: int,
) -> List[Dict[str, object]]:
    out: List[Dict[str, object]] = []
    for search in searches:
        rows = conn.execute(
            f"""
            SELECT __row_index AS row_index, "{field}" AS value
            FROM "{table}"
            WHERE __export_id = ?
              AND "{field}" IS NOT NULL
              AND "{field}" LIKE ?
            ORDER BY __row_index
            LIMIT ?
            """,
            (export_id, f"%{search}%", limit),
        ).fetchall()
        for row in rows:
            out.append(
                {
                    "search": search,
                    "sheet": table.replace("sheet__", ""),
                    "row_index": row["row_index"],
                    "field": field,
                    "value": row["value"],
                }
            )
    return out


def main() -> int:
    args = parse_args()
    conn = connect(args.db)
    try:
        init_probe_registry_schema(conn)
        export_id = latest_export_id(conn, export_id=args.export_id, snapshot_name=args.snapshot_name)
        stats = probe_stats(conn, args.family, args.search)
        appearances = {
            "books": hits_for_table(conn, "sheet__books", "decodedbase", args.search, export_id, args.limit),
            "contigs": hits_for_table(conn, "sheet__contigs", "translation_strictplus_v108", args.search, export_id, args.limit),
            "glossary": hits_for_table(conn, "sheet__glossary", "token", args.search, export_id, args.limit),
            "externalrefs_v115": hits_for_table(conn, "sheet__externalrefs_v115", "decodedbase", args.search, export_id, args.limit),
        }

        reasons: List[str] = []
        decision = "REVIEW"
        if stats["dead"]:
            decision = "ABANDON"
            reasons.append("family already dead by registry thresholds")
        if stats.get("known_dead_rules"):
            reasons.append("matches known dead branch rules: " + ",".join(stats["known_dead_rules"]))
        book_hits = len(appearances["books"])
        contig_hits = len(appearances["contigs"])
        glossary_hits = len(appearances["glossary"])
        external_hits = len(appearances["externalrefs_v115"])
        if book_hits == 0 and contig_hits == 0 and glossary_hits == 0 and external_hits == 0:
            if decision != "ABANDON":
                decision = "REVIEW"
            reasons.append("no strong SQLite or external footprint found")
        else:
            reasons.append("family has SQLite footprint and can justify a narrow confirmation lane")
        if stats["stalled"] > 0:
            reasons.append("prior stalled-no-checkpoint outcome requires a materially different mechanical reason")

        print(
            json.dumps(
                {
                    "family": args.family,
                    "searches": list(args.search),
                    "export_id": export_id,
                    "probe_stats": stats,
                    "where_it_appears": appearances,
                    "recommended_action": decision,
                    "why": reasons,
                },
                ensure_ascii=True,
                indent=2,
            )
        )
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
