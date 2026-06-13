#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import UTC, datetime
from typing import Any, Dict, List


DEFAULT_DB = "./data/bonelord_operational.sqlite"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a SQL-native review queue for high-impact semantic base translations")
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--record", action="store_true")
    parser.add_argument("--limit", type=int, default=30)
    return parser.parse_args()


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone() is not None


def safe_json(raw: object, default: Any) -> Any:
    if raw in (None, ""):
        return default
    try:
        return json.loads(str(raw))
    except json.JSONDecodeError:
        return default


def latest_run_id(conn: sqlite3.Connection, table: str) -> int | None:
    if not table_exists(conn, table):
        return None
    row = conn.execute(f"SELECT run_id FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    return int(row["run_id"]) if row else None


def latest_constraints(conn: sqlite3.Connection) -> Dict[str, Dict[str, Any]]:
    if not table_exists(conn, "semantic_constraint_registry"):
        return {}
    rows = conn.execute(
        """
        SELECT token, decision, confidence, blocked_old_hint, reason, reopen_condition, payload_json
        FROM semantic_constraint_registry
        WHERE constraint_id IN (
            SELECT max(constraint_id)
            FROM semantic_constraint_registry
            GROUP BY token
        )
        """
    ).fetchall()
    return {str(row["token"]): dict(row) for row in rows}


def classify(row: sqlite3.Row, constraint: Dict[str, Any] | None) -> tuple[str, str, str]:
    token = str(row["base_token"])
    translation = str(row["base_translation"] or "")
    notes = str(row["notes"] or "").lower()
    if constraint:
        decision = str(constraint["decision"] or "")
        if decision.startswith("KEEP_NAMED_UNKNOWN"):
            return (
                "NamedUnknownConstraint",
                "BLOCK_SEMANTIC_PROMOTION",
                f"Semantic constraint says {decision}; reopen only with independent evidence.",
            )
        if decision.startswith("SUSPECT_"):
            return (
                "SuspectRetext",
                "NEUTRALIZE_OR_SHADOW_COMPARE",
                f"Semantic constraint says {decision}; do not treat current wording as solved.",
            )
        if decision.startswith("CAUTIOUS_") or decision.startswith("LOCAL_DISPLAY"):
            return (
                "CautiousLocalReading",
                "KEEP_CAUTION_NOT_HARD_ANCHOR",
                f"Semantic constraint says {decision}; keep display reading but not as hard external truth.",
            )
        if decision.startswith("BASE_ALIVE"):
            return (
                "BaseAliveStaleChildren",
                "RECOMPOSE_STALE_CHILDREN",
                f"Semantic constraint says {decision}; base is alive, child macros need cleanup.",
            )
    if "<unk" in translation.lower():
        return (
            "UnknownBase",
            "SEARCH_EXTERNAL_OR_KEEP_NAMED_UNKNOWN",
            "Base is unresolved in current safe reading.",
        )
    if "retext" in notes:
        return (
            "RetextAudit",
            "AUDIT_RETEXT_EVIDENCE",
            "Base translation was changed by semantic/English retext; verify it is not a fluent overfit.",
        )
    if str(row["recommended_action"] or "") == "RECOMPOSE_CHILDREN_OR_RETARGET_BASE":
        return (
            "BaseOrChildStaleAudit",
            "SEPARATE_BASE_FROM_STALE_CHILDREN",
            "Current issue may be stale descendants rather than an incorrect base.",
        )
    return (
        "CoordinatorReview",
        "REVIEW",
        "High-impact base needs coordinator classification.",
    )


def build_queue(conn: sqlite3.Connection, limit: int) -> Dict[str, Any]:
    impact_run_id = latest_run_id(conn, "macro_family_impact_rank_runs")
    constraints = latest_constraints(conn)
    if impact_run_id is None:
        return {"impact_run_id": None, "queue_count": 0, "items": []}
    rows = conn.execute(
        """
        SELECT
            m.rank,
            m.base_token,
            m.base_translation,
            m.severity,
            m.book_count,
            m.hit_count,
            m.priority_score,
            m.recommended_action,
            m.payload_json,
            g.tokentype,
            g.confidence,
            g.evidenceclass_v127,
            g.evidencescore_v127,
            g.totalocc,
            g.bookcount,
            g.notes
        FROM macro_family_impact_rank_items m
        LEFT JOIN sheet__glossary g
          ON g.__export_id = 2
         AND g.token = m.base_token
        WHERE m.run_id = ?
        ORDER BY m.priority_score DESC, m.rank
        LIMIT ?
        """,
        (impact_run_id, limit),
    ).fetchall()
    items: List[Dict[str, Any]] = []
    for row in rows:
        token = str(row["base_token"])
        constraint = constraints.get(token)
        lane, action, reason = classify(row, constraint)
        payload = safe_json(row["payload_json"], {})
        precheck = {
            "family": token,
            "reason_selected": f"{token}={row['base_translation']} affects {row['book_count']} book(s), {row['hit_count']} visible hit(s), priority={row['priority_score']}.",
            "prior_failures": str(row["notes"] or "")[:500],
            "expected_failure_mode": reason,
            "why_this_run_is_different": "Selected from SQL semantic impact ranking after prefix-only macro false positives were removed.",
        }
        item = {
            "rank": len(items) + 1,
            "impact_rank": int(row["rank"]),
            "token": token,
            "translation": row["base_translation"],
            "lane": lane,
            "status": "OPEN",
            "priority_score": int(row["priority_score"] or 0),
            "recommended_action": action,
            "precheck": precheck,
            "constraint": constraint,
            "glossary": {
                "tokentype": row["tokentype"],
                "confidence": row["confidence"],
                "evidenceclass_v127": row["evidenceclass_v127"],
                "evidencescore_v127": row["evidencescore_v127"],
                "totalocc": row["totalocc"],
                "bookcount": row["bookcount"],
                "notes": row["notes"],
            },
            "impact": payload,
        }
        items.append(item)
    return {
        "impact_run_id": impact_run_id,
        "queue_count": len(items),
        "items": items,
        "interpretation": "Semantic base queue separates unknown constraints, retext audits, and stale-child cleanup. It does not mutate decode core.",
    }


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS semantic_base_review_queue_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            impact_run_id INTEGER,
            queue_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS semantic_base_review_queue_items (
            run_id INTEGER NOT NULL,
            rank INTEGER NOT NULL,
            impact_rank INTEGER NOT NULL,
            token TEXT NOT NULL,
            translation TEXT,
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
        INSERT INTO semantic_base_review_queue_runs (created_at, impact_run_id, queue_count, payload_json)
        VALUES (?, ?, ?, ?)
        """,
        (
            created_at,
            payload["impact_run_id"],
            payload["queue_count"],
            json.dumps({k: v for k, v in payload.items() if k != "items"}, ensure_ascii=True, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)
    for item in payload["items"]:
        conn.execute(
            """
            INSERT INTO semantic_base_review_queue_items (
                run_id, rank, impact_rank, token, translation, lane, status,
                priority_score, recommended_action, precheck_json, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                item["rank"],
                item["impact_rank"],
                item["token"],
                item["translation"],
                item["lane"],
                item["status"],
                item["priority_score"],
                item["recommended_action"],
                json.dumps(item["precheck"], ensure_ascii=True, sort_keys=True),
                json.dumps(item, ensure_ascii=True, sort_keys=True),
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
