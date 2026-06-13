#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sqlite3
from collections import Counter
from datetime import UTC, datetime
from typing import Any, Dict, List


DEFAULT_DB = "./data/bonelord_operational.sqlite"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Materialize a shadow layer replacing suspect retexts with mechanical provenance words")
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--record", action="store_true")
    parser.add_argument("--max-output-books", type=int, default=20)
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


def variant_items(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    run_id = latest_run_id(conn, "semantic_variant_compare_runs")
    if run_id is None:
        return []
    rows = conn.execute(
        """
        SELECT token, current, mechanical, recommended_action, payload_json
        FROM semantic_variant_compare_items
        WHERE run_id = ?
          AND mechanical IS NOT NULL
        ORDER BY length(current) DESC, token
        """,
        (run_id,),
    ).fetchall()
    items: List[Dict[str, Any]] = []
    for row in rows:
        payload = safe_json(row["payload_json"], {})
        items.append(
            {
                "token": str(row["token"]),
                "current": str(row["current"]),
                "mechanical": str(row["mechanical"]),
                "recommended_action": str(row["recommended_action"]),
                "variant_payload": payload,
            }
        )
    return items


def apply_items(text: str, items: List[Dict[str, Any]]) -> tuple[str, List[Dict[str, Any]]]:
    output = str(text or "")
    hits: List[Dict[str, Any]] = []
    for item in items:
        pattern = re.compile(rf"(?<![A-Za-z]){re.escape(item['current'])}(?![A-Za-z])", re.IGNORECASE)
        count = len(pattern.findall(output))
        if not count:
            continue
        output = pattern.sub(item["mechanical"], output)
        hits.append(
            {
                "token": item["token"],
                "current": item["current"],
                "mechanical": item["mechanical"],
                "count": count,
                "recommended_action": item["recommended_action"],
            }
        )
    return output, hits


def materialize(conn: sqlite3.Connection, items: List[Dict[str, Any]]) -> Dict[str, Any]:
    safe_run_id = latest_run_id(conn, "safe_book_translation_runs")
    if safe_run_id is None:
        raise RuntimeError("safe_book_translation_runs has no rows")
    rows = conn.execute(
        """
        SELECT bookid, safe_text, blocked_hit_count, caution_hit_count, risk_score
        FROM safe_book_translations
        WHERE run_id = ?
        ORDER BY CAST(bookid AS INTEGER)
        """,
        (safe_run_id,),
    ).fetchall()
    output_items: List[Dict[str, Any]] = []
    totals: Counter[str] = Counter()
    for row in rows:
        mechanical_text, hits = apply_items(str(row["safe_text"] or ""), items)
        totals["book_count"] += 1
        if hits:
            totals["books_with_mechanical_hits"] += 1
        totals["mechanical_hit_count"] += sum(int(hit["count"]) for hit in hits)
        output_items.append(
            {
                "bookid": str(row["bookid"]),
                "safe_text": row["safe_text"],
                "mechanical_shadow_text": mechanical_text,
                "safe_blocked_hit_count": int(row["blocked_hit_count"] or 0),
                "safe_caution_hit_count": int(row["caution_hit_count"] or 0),
                "safe_risk_score": int(row["risk_score"] or 0),
                "mechanical_hits": hits,
            }
        )
    clean_books = sum(1 for item in output_items if not item["safe_blocked_hit_count"] and not item["mechanical_hits"])
    mechanical_clean_pct = round(100.0 * clean_books / totals["book_count"], 2) if totals["book_count"] else 0.0
    return {
        "summary": {
            "safe_book_run_id": safe_run_id,
            "book_count": totals["book_count"],
            "rule_count": len(items),
            "books_with_mechanical_hits": totals["books_with_mechanical_hits"],
            "mechanical_hit_count": totals["mechanical_hit_count"],
            "mechanical_clean_pct": mechanical_clean_pct,
            "interpretation": "Mechanical shadow replaces suspect semantic retexts with mechanical provenance words for comparison only.",
        },
        "items": output_items,
        "rules": items,
    }


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS mechanical_shadow_book_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            safe_book_run_id INTEGER NOT NULL,
            book_count INTEGER NOT NULL,
            rule_count INTEGER NOT NULL,
            books_with_mechanical_hits INTEGER NOT NULL,
            mechanical_hit_count INTEGER NOT NULL,
            mechanical_clean_pct REAL NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS mechanical_shadow_book_translations (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            safe_text TEXT,
            mechanical_shadow_text TEXT,
            safe_blocked_hit_count INTEGER NOT NULL,
            safe_caution_hit_count INTEGER NOT NULL,
            safe_risk_score INTEGER NOT NULL,
            mechanical_hits_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        );
        """
    )


def record(conn: sqlite3.Connection, payload: Dict[str, Any]) -> int:
    ensure_schema(conn)
    summary = payload["summary"]
    created_at = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    cur = conn.execute(
        """
        INSERT INTO mechanical_shadow_book_runs (
            created_at, safe_book_run_id, book_count, rule_count,
            books_with_mechanical_hits, mechanical_hit_count, mechanical_clean_pct, payload_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            created_at,
            summary["safe_book_run_id"],
            summary["book_count"],
            summary["rule_count"],
            summary["books_with_mechanical_hits"],
            summary["mechanical_hit_count"],
            summary["mechanical_clean_pct"],
            json.dumps({**summary, "rules": payload["rules"]}, ensure_ascii=True, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)
    for item in payload["items"]:
        conn.execute(
            """
            INSERT INTO mechanical_shadow_book_translations (
                run_id, bookid, safe_text, mechanical_shadow_text,
                safe_blocked_hit_count, safe_caution_hit_count, safe_risk_score,
                mechanical_hits_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                item["bookid"],
                item["safe_text"],
                item["mechanical_shadow_text"],
                item["safe_blocked_hit_count"],
                item["safe_caution_hit_count"],
                item["safe_risk_score"],
                json.dumps(item["mechanical_hits"], ensure_ascii=True, sort_keys=True),
            ),
        )
    conn.commit()
    return run_id


def main() -> int:
    args = parse_args()
    conn = connect(args.db)
    try:
        rules = variant_items(conn)
        payload = materialize(conn, rules)
        run_id = record(conn, payload) if args.record else None
    finally:
        conn.close()
    sample = sorted(
        payload["items"],
        key=lambda item: (-sum(hit["count"] for hit in item["mechanical_hits"]), int(item["bookid"])),
    )[: args.max_output_books]
    print(
        json.dumps(
            {
                **payload["summary"],
                "recorded_run_id": run_id,
                "rules": payload["rules"],
                "sample_books": sample,
            },
            ensure_ascii=True,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
