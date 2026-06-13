#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sqlite3
from collections import Counter, defaultdict
from datetime import UTC, datetime
from typing import Any, Dict, List

from sqlite_snapshot_ref import DEFAULT_SNAPSHOT_NAME, resolve_export_id


DEFAULT_DB = "./data/bonelord_operational.sqlite"
UNKNOWN_RE = re.compile(r"<UNK:([^>]+)>")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rank named unknown surfaces in safe book translations")
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--export-id", type=int, default=None)
    parser.add_argument("--snapshot-name", default=DEFAULT_SNAPSHOT_NAME)
    parser.add_argument("--record", action="store_true")
    parser.add_argument("--context", type=int, default=40)
    parser.add_argument("--limit", type=int, default=50)
    return parser.parse_args()


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone() is not None


def latest_run_id(conn: sqlite3.Connection, table: str) -> int | None:
    if not table_exists(conn, table):
        return None
    row = conn.execute(f"SELECT run_id FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    return int(row["run_id"]) if row else None


def context(text: str, start: int, end: int, radius: int) -> str:
    lo = max(0, start - radius)
    hi = min(len(text), end + radius)
    return text[lo:hi]


def glossary_payload(conn: sqlite3.Connection, export_id: int, token: str) -> Dict[str, Any]:
    row = conn.execute(
        """
        SELECT token, translation, tokentype, confidence, evidenceclass_v127, evidencescore_v127,
               totalocc, bookcount, notes
        FROM sheet__glossary
        WHERE __export_id = ?
          AND token = ?
        LIMIT 1
        """,
        (export_id, token),
    ).fetchone()
    return dict(row) if row else {}


def decision_payload(conn: sqlite3.Connection, token: str) -> Dict[str, Any]:
    run_id = latest_run_id(conn, "unknown_base_decision_runs")
    if run_id is None or not table_exists(conn, "unknown_base_decisions"):
        return {}
    row = conn.execute(
        """
        SELECT decision, confidence, old_word_hint, reason
        FROM unknown_base_decisions
        WHERE run_id = ?
          AND token = ?
        LIMIT 1
        """,
        (run_id, token),
    ).fetchone()
    return dict(row) if row else {}


def rank(conn: sqlite3.Connection, export_id: int, radius: int, limit: int) -> Dict[str, Any]:
    safe_run_id = latest_run_id(conn, "safe_book_translation_runs")
    if safe_run_id is None:
        return {"safe_book_run_id": None, "items": []}
    rows = conn.execute(
        """
        SELECT bookid, safe_text
        FROM safe_book_translations
        WHERE run_id = ?
        ORDER BY CAST(bookid AS INTEGER)
        """,
        (safe_run_id,),
    ).fetchall()
    buckets: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        text = str(row["safe_text"] or "")
        for match in UNKNOWN_RE.finditer(text):
            token = match.group(1)
            bucket = buckets.setdefault(
                token,
                {
                    "token": token,
                    "hit_count": 0,
                    "books": set(),
                    "contexts": [],
                },
            )
            bucket["hit_count"] += 1
            bucket["books"].add(str(row["bookid"]))
            if len(bucket["contexts"]) < 12:
                bucket["contexts"].append(
                    {
                        "bookid": str(row["bookid"]),
                        "context": context(text, match.start(), match.end(), radius),
                    }
                )
    items: List[Dict[str, Any]] = []
    for bucket in buckets.values():
        token = bucket["token"]
        item = {
            "token": token,
            "hit_count": int(bucket["hit_count"]),
            "book_count": len(bucket["books"]),
            "books": sorted(bucket["books"], key=lambda value: int(value) if value.isdigit() else value),
            "contexts": bucket["contexts"],
            "glossary": glossary_payload(conn, export_id, token),
            "decision": decision_payload(conn, token),
        }
        item["priority_score"] = item["hit_count"] * 10 + item["book_count"] * 7
        if item["decision"].get("decision") == "KEEP_UNKNOWN":
            item["recommended_action"] = "SEARCH_EXTERNAL_OR_KEEP_NAMED_UNKNOWN"
        else:
            item["recommended_action"] = "RUN_UNKNOWN_BASE_DECISION"
        items.append(item)
    items.sort(key=lambda item: (-item["priority_score"], item["token"]))
    return {
        "safe_book_run_id": safe_run_id,
        "unknown_surface_count": len(items),
        "items": items[:limit],
        "interpretation": "Named unknowns are not hallucination; they are unresolved lexical bases that need independent evidence.",
    }


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS unknown_surface_rank_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            safe_book_run_id INTEGER,
            unknown_surface_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS unknown_surface_rank_items (
            run_id INTEGER NOT NULL,
            rank INTEGER NOT NULL,
            token TEXT NOT NULL,
            hit_count INTEGER NOT NULL,
            book_count INTEGER NOT NULL,
            priority_score INTEGER NOT NULL,
            recommended_action TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, rank)
        );
        """
    )


def record(conn: sqlite3.Connection, payload: Dict[str, Any]) -> int:
    ensure_schema(conn)
    created_at = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    cur = conn.execute(
        """
        INSERT INTO unknown_surface_rank_runs (
            created_at, safe_book_run_id, unknown_surface_count, payload_json
        ) VALUES (?, ?, ?, ?)
        """,
        (
            created_at,
            payload["safe_book_run_id"],
            payload["unknown_surface_count"],
            json.dumps({k: v for k, v in payload.items() if k != "items"}, ensure_ascii=True, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)
    for idx, item in enumerate(payload["items"], start=1):
        conn.execute(
            """
            INSERT INTO unknown_surface_rank_items (
                run_id, rank, token, hit_count, book_count, priority_score,
                recommended_action, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                idx,
                item["token"],
                item["hit_count"],
                item["book_count"],
                item["priority_score"],
                item["recommended_action"],
                json.dumps(item, ensure_ascii=True, sort_keys=True),
            ),
        )
    conn.commit()
    return run_id


def main() -> int:
    args = parse_args()
    conn = connect(args.db)
    try:
        export_id = resolve_export_id(conn, export_id=args.export_id, snapshot_name=args.snapshot_name)
        payload = rank(conn, export_id, args.context, args.limit)
        run_id = record(conn, payload) if args.record else None
    finally:
        conn.close()
    print(json.dumps({**payload, "recorded_run_id": run_id}, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
