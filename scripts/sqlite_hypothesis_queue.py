#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import UTC, datetime
from typing import Any, Dict, List


DEFAULT_DB = "./data/bonelord_operational.sqlite"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a SQL-native hypothesis work queue from ranked frontiers")
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--record", action="store_true")
    parser.add_argument("--limit", type=int, default=12)
    return parser.parse_args()


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone() is not None


def latest_rank_run_id(conn: sqlite3.Connection) -> int | None:
    if not table_exists(conn, "safe_frontier_rank_runs"):
        return None
    row = conn.execute("SELECT run_id FROM safe_frontier_rank_runs ORDER BY run_id DESC LIMIT 1").fetchone()
    return int(row["run_id"]) if row else None


def safe_json(raw: object, default: Any) -> Any:
    if raw in (None, ""):
        return default
    try:
        return json.loads(str(raw))
    except json.JSONDecodeError:
        return default


def classify_lane(action: str, token: str, family: str | None) -> str:
    if action == "RESOLVE_UNKNOWN_BASE_FIRST" or token.startswith("TTNVVN"):
        return "UnknownBase"
    if action == "AUDIT_BOUNDARY_OR_STALE_CHILD":
        return "StructuralSemantic"
    if action == "RECOMPOSE_OR_MASK_ONLY":
        return "DisplayOnlyStabilization"
    if family:
        return "SemanticAudit"
    return "CoordinatorReview"


def build_precheck(item: Dict[str, Any]) -> Dict[str, Any]:
    token = item["token"]
    family = item.get("family_token")
    action = item["recommended_action"]
    phrase = next(iter(item.get("phrases", {}).keys()), "")
    if action == "RESOLVE_UNKNOWN_BASE_FIRST":
        expected_failure = "Child macro is fluent while base is unknown; any readable phrase may be inherited hallucination."
        why_different = "Queue starts from safe-book contamination count, not from mechanical promotion score."
        prior = "Stability gate blocks unknown-base fluent children; external phrase anchors are separate NPC mode."
    elif action == "AUDIT_BOUNDARY_OR_STALE_CHILD":
        expected_failure = "Boundary or stale child macro may preserve old component semantics instead of current base."
        why_different = "The family is selected because it contaminates current safe-book text across multiple books."
        prior = "Macro consistency and recomposition audits already flagged child/base mismatch."
    else:
        expected_failure = "Phrase should remain masked unless recomposition produces a stable non-contradictory reading."
        why_different = "This is display-layer stabilization only; no decode-core promotion is assumed."
        prior = "Recomposition audit changed the macro output or exposed unknown components."
    return {
        "family": family or token,
        "reason_selected": f"{token} blocks {item['book_count']} book(s), {item['hit_count']} hit(s), phrase={phrase!r}.",
        "prior_failures": prior,
        "expected_failure_mode": expected_failure,
        "why_this_run_is_different": why_different,
    }


def build_queue(conn: sqlite3.Connection, limit: int) -> Dict[str, Any]:
    rank_run_id = latest_rank_run_id(conn)
    if rank_run_id is None:
        return {"rank_run_id": None, "items": []}
    rows = conn.execute(
        """
        SELECT rank, token, family_token, item_kind, decision, book_count, hit_count,
               max_risk_score, priority_score, recommended_action, payload_json
        FROM safe_frontier_rank_items
        WHERE run_id = ?
        ORDER BY rank
        LIMIT ?
        """,
        (rank_run_id, limit),
    ).fetchall()
    items: List[Dict[str, Any]] = []
    for row in rows:
        payload = safe_json(row["payload_json"], {})
        item = {
            "rank": int(row["rank"]),
            "token": str(row["token"]),
            "family_token": row["family_token"],
            "item_kind": row["item_kind"],
            "decision": row["decision"],
            "book_count": int(row["book_count"] or 0),
            "hit_count": int(row["hit_count"] or 0),
            "max_risk_score": int(row["max_risk_score"] or 0),
            "priority_score": int(row["priority_score"] or 0),
            "recommended_action": row["recommended_action"],
            "lane": classify_lane(str(row["recommended_action"]), str(row["token"]), row["family_token"]),
            "status": "OPEN",
            "precheck": build_precheck({**payload, "token": row["token"], "family_token": row["family_token"], "recommended_action": row["recommended_action"]}),
            "payload": payload,
        }
        items.append(item)
    return {
        "rank_run_id": rank_run_id,
        "queue_count": len(items),
        "items": items,
        "interpretation": "This queue is the coordinator-facing source for next hypothesis lanes; it does not mutate decode core.",
    }


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS hypothesis_queue_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            rank_run_id INTEGER,
            queue_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS hypothesis_queue_items (
            run_id INTEGER NOT NULL,
            rank INTEGER NOT NULL,
            token TEXT NOT NULL,
            family_token TEXT,
            lane TEXT NOT NULL,
            status TEXT NOT NULL,
            priority_score INTEGER NOT NULL,
            recommended_action TEXT NOT NULL,
            precheck_json TEXT NOT NULL,
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
        INSERT INTO hypothesis_queue_runs (created_at, rank_run_id, queue_count, payload_json)
        VALUES (?, ?, ?, ?)
        """,
        (
            created_at,
            payload["rank_run_id"],
            payload["queue_count"],
            json.dumps({k: v for k, v in payload.items() if k != "items"}, ensure_ascii=True, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)
    for item in payload["items"]:
        conn.execute(
            """
            INSERT INTO hypothesis_queue_items (
                run_id, rank, token, family_token, lane, status,
                priority_score, recommended_action, precheck_json, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                item["rank"],
                item["token"],
                item["family_token"],
                item["lane"],
                item["status"],
                item["priority_score"],
                item["recommended_action"],
                json.dumps(item["precheck"], ensure_ascii=True, sort_keys=True),
                json.dumps(item["payload"], ensure_ascii=True, sort_keys=True),
            ),
        )
    conn.commit()
    return run_id


def main() -> int:
    args = parse_args()
    conn = connect(args.db)
    try:
        payload = build_queue(conn, args.limit)
        run_id = record(conn, payload) if args.record else None
    finally:
        conn.close()
    print(json.dumps({**payload, "recorded_run_id": run_id}, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
