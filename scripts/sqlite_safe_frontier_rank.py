#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any, Dict, List


DEFAULT_DB = "./data/bonelord_operational.sqlite"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rank translation blockers from safe book materialization")
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--record", action="store_true")
    parser.add_argument("--limit", type=int, default=30)
    return parser.parse_args()


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def latest_run_id(conn: sqlite3.Connection, table: str) -> int | None:
    exists = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone()
    if not exists:
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


def classify_action(item: Dict[str, Any]) -> str:
    reason_codes = {str(reason.get("code") or "") for reason in item.get("reasons", []) if isinstance(reason, dict)}
    token = str(item["token"])
    if "UNKNOWN_BASE_FLUENT_CHILD" in reason_codes or token.startswith("TTNVVN"):
        return "RESOLVE_UNKNOWN_BASE_FIRST"
    if "CHILD_BASE_MISMATCH" in reason_codes:
        return "AUDIT_BOUNDARY_OR_STALE_CHILD"
    if "STALE_RECOMPOSED_MACRO" in reason_codes:
        return "RECOMPOSE_OR_MASK_ONLY"
    return "MANUAL_SEMANTIC_AUDIT"


def rank(conn: sqlite3.Connection, limit: int) -> Dict[str, Any]:
    run_id = latest_run_id(conn, "safe_book_translation_runs")
    if run_id is None:
        return {"safe_book_run_id": None, "items": []}
    rows = conn.execute(
        """
        SELECT bookid, hits_json
        FROM safe_book_translations
        WHERE run_id = ?
        """,
        (run_id,),
    ).fetchall()
    buckets: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        for hit in safe_json(row["hits_json"], []):
            token = str(hit.get("token") or "")
            if not token:
                continue
            bucket = buckets.setdefault(
                token,
                {
                    "token": token,
                    "family_token": hit.get("family_token"),
                    "item_kind": hit.get("item_kind"),
                    "decision": hit.get("decision"),
                    "phrases": defaultdict(int),
                    "books": set(),
                    "hit_count": 0,
                    "max_risk_score": int(hit.get("risk_score") or 0),
                    "reasons": hit.get("reasons") or [],
                },
            )
            count = int(hit.get("count") or 0)
            bucket["phrases"][str(hit.get("phrase") or "")] += count
            bucket["books"].add(str(row["bookid"]))
            bucket["hit_count"] += count
            bucket["max_risk_score"] = max(int(bucket["max_risk_score"]), int(hit.get("risk_score") or 0))
    items: List[Dict[str, Any]] = []
    for bucket in buckets.values():
        item = {
            "token": bucket["token"],
            "family_token": bucket["family_token"],
            "item_kind": bucket["item_kind"],
            "decision": bucket["decision"],
            "book_count": len(bucket["books"]),
            "books": sorted(bucket["books"], key=lambda value: int(value) if value.isdigit() else value),
            "hit_count": int(bucket["hit_count"]),
            "max_risk_score": int(bucket["max_risk_score"]),
            "phrases": dict(sorted(bucket["phrases"].items(), key=lambda pair: (-pair[1], pair[0]))),
            "reasons": bucket["reasons"],
        }
        item["priority_score"] = item["hit_count"] * 10 + item["book_count"] * 7 + item["max_risk_score"]
        item["recommended_action"] = classify_action(item)
        items.append(item)
    items.sort(key=lambda item: (-item["priority_score"], -item["book_count"], item["token"]))
    return {
        "safe_book_run_id": run_id,
        "frontier_count": len(items),
        "items": items[:limit],
        "interpretation": "Prioritize high-hit blockers that affect many books and have clear failure modes.",
    }


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS safe_frontier_rank_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            safe_book_run_id INTEGER,
            frontier_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS safe_frontier_rank_items (
            run_id INTEGER NOT NULL,
            rank INTEGER NOT NULL,
            token TEXT NOT NULL,
            family_token TEXT,
            item_kind TEXT,
            decision TEXT,
            book_count INTEGER NOT NULL,
            hit_count INTEGER NOT NULL,
            max_risk_score INTEGER NOT NULL,
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
        INSERT INTO safe_frontier_rank_runs (created_at, safe_book_run_id, frontier_count, payload_json)
        VALUES (?, ?, ?, ?)
        """,
        (
            created_at,
            payload["safe_book_run_id"],
            payload["frontier_count"],
            json.dumps({k: v for k, v in payload.items() if k != "items"}, ensure_ascii=True, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)
    for idx, item in enumerate(payload["items"], start=1):
        conn.execute(
            """
            INSERT INTO safe_frontier_rank_items (
                run_id, rank, token, family_token, item_kind, decision, book_count, hit_count,
                max_risk_score, priority_score, recommended_action, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                idx,
                item["token"],
                item["family_token"],
                item["item_kind"],
                item["decision"],
                item["book_count"],
                item["hit_count"],
                item["max_risk_score"],
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
