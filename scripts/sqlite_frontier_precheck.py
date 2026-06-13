#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from sqlite_probe_registry import init_schema as init_probe_registry_schema
from sqlite_snapshot_ref import DEFAULT_SNAPSHOT_NAME, resolve_export_id


DEFAULT_DB = "./data/bonelord_operational.sqlite"


@dataclass
class Hit:
    sheet: str
    row_index: int
    field: str
    value: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SQLite-first frontier precheck")
    parser.add_argument("--db", default=DEFAULT_DB, help="SQLite snapshot DB")
    parser.add_argument("--export-id", type=int, default=None, help="Specific snapshot export_id")
    parser.add_argument("--snapshot-name", default=DEFAULT_SNAPSHOT_NAME, help="Named snapshot ref to use")
    parser.add_argument("--family", required=True, help="Candidate family / probe family")
    parser.add_argument("--limit", type=int, default=10, help="Max hits to report per sheet")
    parser.add_argument(
        "--search",
        default=None,
        help="Optional raw search string; defaults to family",
    )
    return parser.parse_args()


def normalize_family(text: str) -> str:
    return text.strip().lower()


def latest_export_id(
    conn: sqlite3.Connection,
    export_id: Optional[int] = None,
    snapshot_name: str = DEFAULT_SNAPSHOT_NAME,
) -> int:
    return resolve_export_id(conn, export_id=export_id, snapshot_name=snapshot_name)


def probe_stats(conn: sqlite3.Connection, family: str) -> Dict[str, Any]:
    rows = conn.execute(
        """
        SELECT
            COUNT(*) AS runs,
            SUM(CASE WHEN outcome = 'DP_UNUSED' THEN 1 ELSE 0 END) AS dp_unused,
            SUM(CASE WHEN outcome = 'GT_HARD_FAIL' THEN 1 ELSE 0 END) AS gt_hard_fail,
            SUM(CASE WHEN outcome = 'NO_OP' THEN 1 ELSE 0 END) AS no_op,
            MAX(created_at) AS last_seen,
            MAX(CASE WHEN outcome IS NOT NULL THEN outcome END) AS last_outcome
        FROM probe_runs
        WHERE lower(family) = lower(?)
        """,
        (family,),
    ).fetchone()
    if rows is None:
        return {"runs": 0, "dead": False}
    runs = int(rows["runs"] or 0)
    dp_unused = int(rows["dp_unused"] or 0)
    gt_hard_fail = int(rows["gt_hard_fail"] or 0)
    no_op = int(rows["no_op"] or 0)
    dead = dp_unused >= 2 or gt_hard_fail >= 2 or no_op >= 2
    return {
        "runs": runs,
        "dp_unused": dp_unused,
        "gt_hard_fail": gt_hard_fail,
        "no_op": no_op,
        "last_seen": rows["last_seen"],
        "last_outcome": rows["last_outcome"],
        "dead": dead,
    }


def search_sheet(conn: sqlite3.Connection, export_id: int, sheet: str, columns: Sequence[str], needle: str, limit: int) -> List[Hit]:
    table = f"sheet__{sheet}"
    conds = " OR ".join([f'lower(coalesce("{c}", "")) LIKE ?' for c in columns])
    params = [export_id] + [f"%{needle.lower()}%" for _ in columns]
    rows = conn.execute(
        f"""
        SELECT * FROM "{table}"
        WHERE __export_id = ?
          AND ({conds})
        ORDER BY __row_index
        LIMIT ?
        """,
        (*params, limit),
    ).fetchall()
    hits: List[Hit] = []
    for row in rows:
        for col in columns:
            val = row[col]
            if val is not None and needle.lower() in str(val).lower():
                hits.append(Hit(sheet=sheet, row_index=int(row["__row_index"]), field=col, value=str(val)))
                break
    return hits


def cross_sheet_hits(conn: sqlite3.Connection, export_id: int, needle: str, limit: int) -> Dict[str, List[Dict[str, Any]]]:
    sheets = {
        "books": ["decodedbase", "translation_contextenglish_auto", "translation_english_auto", "translation_semantic_auto"],
        "contigs": ["decodedbase", "translation_contextenglish_auto", "translation_highonly_v123", "translation_strictplus_v108"],
        "glossary": ["token", "translation", "notes", "evidenceclass_v127", "evidencesources_v127"],
        "externalrefs_v115": ["refname", "decodedbase", "dp_strictplus", "source"],
    }
    out: Dict[str, List[Dict[str, Any]]] = {}
    for sheet, cols in sheets.items():
        try:
            hits = search_sheet(conn, export_id, sheet, cols, needle, limit)
        except sqlite3.OperationalError:
            continue
        out[sheet] = [hit.__dict__ for hit in hits]
    return out


def recent_dead_family_info(conn: sqlite3.Connection, family: str) -> Dict[str, Any]:
    rows = conn.execute(
        """
        SELECT * FROM probe_runs
        WHERE lower(family) = lower(?)
        ORDER BY probe_id DESC
        LIMIT 10
        """,
        (family,),
    ).fetchall()
    return {
        "recent_runs": [dict(r) for r in rows],
    }


def why_different(stats: Dict[str, Any], hits: Dict[str, List[Dict[str, Any]]]) -> List[str]:
    reasons: List[str] = []
    if stats["dead"]:
        reasons.append("family already repeated a dead mode in registry")
    if stats["dp_unused"] >= 2:
        reasons.append("repeat of DP_UNUSED would likely be redundant")
    if stats["gt_hard_fail"] >= 2:
        reasons.append("repeat of GT hard fail would likely be redundant")
    if stats["no_op"] >= 2:
        reasons.append("repeat of pure no-op would likely be redundant")

    if hits.get("externalrefs_v115"):
        reasons.append("family appears in external refs, so a new run can target a narrower subfamily or different seam")
    if hits.get("books") or hits.get("contigs") or hits.get("glossary"):
        reasons.append("family has SQLite footprint, so a narrower confirmation lane can differ by boundary or swallow behavior")
    if not any(hits.values()):
        reasons.append("no strong SQLite footprint found, so a new run would need a different search key or exact anchor decomposition")
    return reasons


def main() -> int:
    args = parse_args()
    db_path = Path(args.db)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        init_probe_registry_schema(conn)
        export_id = latest_export_id(conn, export_id=args.export_id, snapshot_name=args.snapshot_name)
        family = args.family
        needle = args.search or family
        stats = probe_stats(conn, family)
        hits = cross_sheet_hits(conn, export_id, needle, args.limit)
        payload = {
            "family": family,
            "search": needle,
            "export_id": export_id,
            "probe_stats": stats,
            "dead": stats["dead"],
            "where_it_appears": hits,
            "why_a_new_run_would_be_different": why_different(stats, hits),
            "recommended_action": "ABANDON" if stats["dead"] else "REVIEW",
        }
        print(json.dumps(payload, ensure_ascii=True, indent=2))
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
