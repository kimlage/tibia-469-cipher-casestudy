#!/usr/bin/env python3
"""Apply a conservative policy layer over the row0 function registry."""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "bonelord_operational.sqlite"

POLICY = {
    "ROW0_CODE_SYMBOL": (
        "VALIDATED_MECHANICAL",
        1.00,
        "keep",
        "primary mechanical substrate, 70/70 valid and zero conflicts",
    ),
    "STAR_00": (
        "FUNCTION_STRONG",
        0.95,
        "keep_structural_only",
        "strong boundary/operator evidence; never plaintext",
    ),
    "LTAST_TAIL": (
        "FUNCTION_STRONG",
        0.93,
        "keep_paired_continuation_only",
        "perfect paired invariant, but one orphan tail and formula drift risk",
    ),
    "BENNA_FORMULA": (
        "FORMULA_CONTEXT",
        0.68,
        "downgrade_from_ready",
        "useful formula bridge, but not independent semantic function",
    ),
    "NAESE_IVIFAST": (
        "SLOT_CLASSIFIER",
        0.66,
        "downgrade_from_ready",
        "slot classes are useful; clean exemplars are only 4/12",
    ),
    "VINVIN_VTLR": (
        "FORMULA_CONTEXT",
        0.60,
        "downgrade_from_ready",
        "negative control favorable, but stronger formula controls and VTLR drift risk remain",
    ),
}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def jdump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS row0_function_policy_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_registry_run_id INTEGER NOT NULL,
            item_count INTEGER NOT NULL,
            downgraded_count INTEGER NOT NULL,
            strong_count INTEGER NOT NULL,
            formula_context_count INTEGER NOT NULL,
            slot_classifier_count INTEGER NOT NULL,
            context_frame_count INTEGER NOT NULL,
            audit_only_count INTEGER NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS row0_function_policy_items (
            run_id INTEGER NOT NULL,
            function_id TEXT NOT NULL,
            original_status TEXT NOT NULL,
            policy_status TEXT NOT NULL,
            original_confidence REAL,
            policy_confidence REAL NOT NULL,
            policy_decision TEXT NOT NULL,
            policy_reason TEXT NOT NULL,
            gloss_allowed INTEGER NOT NULL,
            hard_decode_action TEXT NOT NULL,
            next_action TEXT NOT NULL,
            promotion_gate TEXT NOT NULL,
            abandon_gate TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, function_id)
        );
        """
    )


def latest_registry_run(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT MAX(registry_run_id) AS run_id FROM row0_function_registry").fetchone()
    if row is None or row["run_id"] is None:
        raise SystemExit("missing row0_function_registry data")
    return int(row["run_id"])


def default_policy(row: sqlite3.Row) -> tuple[str, float, str, str]:
    if row["status"] == "AUDIT_ONLY":
        return "AUDIT_ONLY", 0.20, "keep_audit_only", "audit-only singleton or weak frame"
    if row["status"] == "CONTEXT_FRAME":
        return "CONTEXT_FRAME", min(float(row["confidence_score"] or 0.55), 0.75), "keep_context_frame", "local frame only, no global symbol gloss"
    return row["status"], float(row["confidence_score"] or 0.50), "keep_default", "no special policy override"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)

    source_run_id = latest_registry_run(conn)
    rows = conn.execute(
        """
        SELECT *
        FROM row0_function_registry
        WHERE registry_run_id=?
        ORDER BY function_id
        """,
        (source_run_id,),
    ).fetchall()

    cur = conn.execute(
        """
        INSERT INTO row0_function_policy_runs
            (created_at, source_registry_run_id, item_count, downgraded_count,
             strong_count, formula_context_count, slot_classifier_count,
             context_frame_count, audit_only_count, decision, payload_json)
        VALUES (?, ?, 0, 0, 0, 0, 0, 0, 0, ?, ?)
        """,
        (utc_now(), source_run_id, "PENDING", "{}"),
    )
    run_id = int(cur.lastrowid)

    downgraded = 0
    status_counts: dict[str, int] = {}
    for row in rows:
        function_id = row["function_id"]
        policy_status, policy_confidence, policy_decision, policy_reason = POLICY.get(function_id, default_policy(row))
        if policy_status != row["status"]:
            downgraded += 1
        status_counts[policy_status] = status_counts.get(policy_status, 0) + 1
        conn.execute(
            """
            INSERT INTO row0_function_policy_items
                (run_id, function_id, original_status, policy_status,
                 original_confidence, policy_confidence, policy_decision,
                 policy_reason, gloss_allowed, hard_decode_action, next_action,
                 promotion_gate, abandon_gate, evidence_json, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                function_id,
                row["status"],
                policy_status,
                row["confidence_score"],
                policy_confidence,
                policy_decision,
                policy_reason,
                int(row["gloss_allowed"]),
                row["hard_decode_action"],
                row["next_action"],
                row["promotion_gate"],
                row["abandon_gate"],
                row["evidence_json"],
                jdump({"source_registry_run_id": source_run_id}),
            ),
        )

    conn.execute(
        """
        UPDATE row0_function_policy_runs
        SET item_count=?,
            downgraded_count=?,
            strong_count=?,
            formula_context_count=?,
            slot_classifier_count=?,
            context_frame_count=?,
            audit_only_count=?,
            decision=?,
            payload_json=?
        WHERE run_id=?
        """,
        (
            len(rows),
            downgraded,
            status_counts.get("FUNCTION_STRONG", 0),
            status_counts.get("FORMULA_CONTEXT", 0),
            status_counts.get("SLOT_CLASSIFIER", 0),
            status_counts.get("CONTEXT_FRAME", 0),
            status_counts.get("AUDIT_ONLY", 0),
            "ROW0_FUNCTION_POLICY_APPLIED",
            jdump({"policy": "conservative_no_gloss", "gloss_allowed": False}),
            run_id,
        ),
    )
    conn.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": "ROW0_FUNCTION_POLICY_APPLIED",
                "item_count": len(rows),
                "downgraded_count": downgraded,
                "status_counts": status_counts,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
