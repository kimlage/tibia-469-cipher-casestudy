#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import UTC, datetime
from typing import Any, Dict, List


DEFAULT_DB = "./data/bonelord_operational.sqlite"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rank macro consistency families by observed book impact")
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--record", action="store_true")
    parser.add_argument("--limit", type=int, default=40)
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


def safe_json(raw: object, default: Any) -> Any:
    if raw in (None, ""):
        return default
    try:
        return json.loads(str(raw))
    except json.JSONDecodeError:
        return default


def useful_term(term: object) -> str | None:
    text = " ".join(str(term or "").lower().split())
    if not text:
        return None
    if len(text) < 4:
        return None
    if text in {"this", "that", "with", "from", "into", "than", "you've", "<unk>"}:
        return None
    return text


def book_hits_for_terms(conn: sqlite3.Connection, terms: List[str]) -> Dict[str, Any]:
    safe_run = latest_run_id(conn, "safe_book_translation_runs")
    terms = [term for term in (useful_term(term) for term in terms) if term]
    if safe_run is None or not terms:
        return {"book_count": 0, "hit_count": 0, "books": []}
    rows = conn.execute(
        """
        SELECT bookid, source_text, safe_text, strictplus_text, macrocompressed_text
        FROM safe_book_translations
        WHERE run_id = ?
        """,
        (safe_run,),
    ).fetchall()
    hit_count = 0
    books: set[str] = set()
    for row in rows:
        haystack = " ".join(
            str(row[key] or "")
            for key in ("source_text", "safe_text", "strictplus_text", "macrocompressed_text")
        ).lower()
        local = sum(haystack.count(term) for term in terms)
        if local:
            hit_count += local
            books.add(str(row["bookid"]))
    return {
        "safe_book_run_id": safe_run,
        "book_count": len(books),
        "hit_count": hit_count,
        "books": sorted(books, key=lambda value: int(value) if value.isdigit() else value),
    }


def rank(conn: sqlite3.Connection, limit: int) -> Dict[str, Any]:
    run_id = latest_run_id(conn, "macro_consistency_audit_runs")
    if run_id is None:
        return {"macro_consistency_run_id": None, "items": []}
    rows = conn.execute(
        """
        SELECT rank, base_token, base_translation, severity, reason, payload_json
        FROM macro_consistency_violations
        WHERE run_id = ?
        ORDER BY rank
        LIMIT ?
        """,
        (run_id, limit),
    ).fetchall()
    items: List[Dict[str, Any]] = []
    for row in rows:
        payload = safe_json(row["payload_json"], {})
        child_tokens = [str(child.get("token") or "") for child in payload.get("children", []) if isinstance(child, dict)]
        child_translations = [
            str(child.get("translation") or "")
            for child in payload.get("children", [])
            if isinstance(child, dict)
        ]
        terms = [str(row["base_translation"] or ""), *child_translations]
        impact = book_hits_for_terms(conn, terms)
        item = {
            "rank": int(row["rank"]),
            "base_token": row["base_token"],
            "base_translation": row["base_translation"],
            "severity": int(row["severity"] or 0),
            "reason": row["reason"],
            "child_count": int(payload.get("child_count") or 0),
            "child_tokens": child_tokens[:20],
            "impact_terms": [term for term in (useful_term(term) for term in terms) if term][:20],
            "book_impact": impact,
        }
        item["priority_score"] = int(row["severity"] or 0) + impact["book_count"] * 8 + impact["hit_count"] * 3
        if impact["book_count"] == 0:
            item["recommended_action"] = "LOW_VISIBLE_IMPACT_AUDIT_LATER"
        elif "unknown" in str(row["reason"]).lower():
            item["recommended_action"] = "KEEP_UNKNOWN_OR_EXTERNAL_ONLY"
        else:
            item["recommended_action"] = "RECOMPOSE_CHILDREN_OR_RETARGET_BASE"
        items.append(item)
    items.sort(key=lambda item: (-item["priority_score"], item["rank"]))
    return {
        "macro_consistency_run_id": run_id,
        "family_count": len(items),
        "items": items,
        "interpretation": "This ranks semantic inconsistency by both severity and visible safe-book impact.",
    }


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS macro_family_impact_rank_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            macro_consistency_run_id INTEGER,
            family_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS macro_family_impact_rank_items (
            run_id INTEGER NOT NULL,
            rank INTEGER NOT NULL,
            base_token TEXT NOT NULL,
            base_translation TEXT,
            severity INTEGER NOT NULL,
            book_count INTEGER NOT NULL,
            hit_count INTEGER NOT NULL,
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
        INSERT INTO macro_family_impact_rank_runs (
            created_at, macro_consistency_run_id, family_count, payload_json
        ) VALUES (?, ?, ?, ?)
        """,
        (
            created_at,
            payload["macro_consistency_run_id"],
            payload["family_count"],
            json.dumps({k: v for k, v in payload.items() if k != "items"}, ensure_ascii=True, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)
    for idx, item in enumerate(payload["items"], start=1):
        conn.execute(
            """
            INSERT INTO macro_family_impact_rank_items (
                run_id, rank, base_token, base_translation, severity,
                book_count, hit_count, priority_score, recommended_action, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                idx,
                item["base_token"],
                item["base_translation"],
                item["severity"],
                item["book_impact"]["book_count"],
                item["book_impact"]["hit_count"],
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
        payload = rank(conn, args.limit)
        run_id = record(conn, payload) if args.record else None
    finally:
        conn.close()
    print(json.dumps({**payload, "recorded_run_id": run_id}, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
