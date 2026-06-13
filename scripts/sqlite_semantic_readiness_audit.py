#!/usr/bin/env python3
"""Classify current row0 functional layer for controlled semantic attempts."""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "bonelord_operational.sqlite"

GLOSS_CANDIDATE: set[str] = set()
STRUCTURAL_ONLY = {
    "FRAME_O23_ONAF_FAMILY",
    "VINVIN_VTLR",
    "FRAME_C86_ICE_OPERATOR_OPEN",
    "FRAME_R20_VAETRFEVAST_BLOCK",
    "FRAME_R02_TRVEIIVNTBB_BRIDGE",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def jdump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS semantic_readiness_audit_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_policy_run_id INTEGER NOT NULL,
            item_count INTEGER NOT NULL,
            gloss_candidate_count INTEGER NOT NULL,
            structural_only_count INTEGER NOT NULL,
            audit_only_count INTEGER NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS semantic_readiness_audit_items (
            run_id INTEGER NOT NULL,
            item_id TEXT NOT NULL,
            item_source TEXT NOT NULL,
            mechanical_status TEXT NOT NULL,
            semantic_readiness TEXT NOT NULL,
            confidence REAL NOT NULL,
            gloss_allowed INTEGER NOT NULL,
            reason TEXT NOT NULL,
            next_action TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, item_id, item_source)
        );
        """
    )


def latest_id(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT run_id FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    if row is None:
        return 0
    return int(row["run_id"])


def add_item(
    conn: sqlite3.Connection,
    run_id: int,
    item_id: str,
    source: str,
    mechanical_status: str,
    readiness: str,
    confidence: float,
    gloss_allowed: bool,
    reason: str,
    next_action: str,
    evidence: dict[str, Any],
) -> None:
    storage_item_id = f"{source}:{item_id}"
    conn.execute(
        """
        INSERT INTO semantic_readiness_audit_items
            (run_id, item_id, item_source, mechanical_status, semantic_readiness,
             confidence, gloss_allowed, reason, next_action, evidence_json, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            storage_item_id,
            source,
            mechanical_status,
            readiness,
            confidence,
            1 if gloss_allowed else 0,
            reason,
            next_action,
            jdump(evidence),
            jdump({"evidence": evidence, "gloss_allowed": gloss_allowed}),
        ),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db, timeout=30)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)

    policy_run_id = latest_id(conn, "row0_function_policy_runs")
    blocked_count = conn.execute("SELECT COUNT(*) AS n FROM semantic_blocked_phrases").fetchone()["n"]
    policy_rows = conn.execute(
        """
        SELECT *
        FROM row0_function_policy_items
        ORDER BY function_id
        """
    ).fetchall()
    cur = conn.execute(
        """
        INSERT INTO semantic_readiness_audit_runs
            (created_at, source_policy_run_id, item_count, gloss_candidate_count,
             structural_only_count, audit_only_count, decision, payload_json)
        VALUES (?, ?, 0, 0, 0, 0, ?, ?)
        """,
        (utc_now(), policy_run_id, "PENDING", "{}"),
    )
    run_id = int(cur.lastrowid)
    gloss_candidate = 0
    structural_only = 0
    audit_only = 0

    for row in policy_rows:
        fid = row["function_id"]
        status = row["policy_status"]
        conf = float(row["policy_confidence"])
        evidence = {
            "function_id": fid,
            "mechanical_status": status,
            "policy_confidence": conf,
            "policy_gloss_allowed": bool(row["gloss_allowed"]),
            "blocked_phrase_count": int(blocked_count),
        }
        if fid in STRUCTURAL_ONLY or status in {"FUNCTION_STRONG", "FUNCTION_READY", "SLOT_CLASSIFIER", "FORMULA_CONTEXT", "CONTEXT_FRAME"}:
            readiness = "STRUCTURAL_ONLY_NO_GLOSS"
            gloss = False
            reason = "mechanically useful but not semantically grounded; old shadow layers contain blocked phrase drift"
            next_action = "use_for_segmentation_and_contradiction_reduction_only"
            structural_only += 1
        else:
            readiness = "AUDIT_ONLY_NO_GLOSS"
            gloss = False
            reason = "audit/mechanical preservation only"
            next_action = "do_not_use_for_translation_claim"
            audit_only += 1
        add_item(conn, run_id, fid, "row0_function_policy_items", status, readiness, conf, gloss, reason, next_action, evidence)

    for table, key_col in [
        ("row0_subfunction_policy_items", "subfunction_id"),
        ("zero_pair_context_policy_items", "context_id"),
        ("book30_split_context_policy_items", "context_id"),
        ("c68_8_23_context_policy_items", "context_id"),
        ("r20_livrn_audit_context_policy_items", "context_id"),
        ("book7_audit_context_policy_items", "context_id"),
        ("book49_audit_context_policy_items", "context_id"),
    ]:
        exists = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone()
        if not exists:
            continue
        table_run = latest_id(conn, table.replace("_items", "_runs"))
        rows = conn.execute(f"SELECT * FROM {table} WHERE run_id=?", (table_run,)).fetchall()
        for row in rows:
            item_id = row[key_col]
            status = row["policy_status"]
            conf_col = "policy_confidence"
            conf = float(row[conf_col]) if conf_col in row.keys() else 0.5
            if status == "LOCAL_CONTEXT_READY":
                readiness = "LOCAL_CONTEXT_ONLY_NO_GLOSS"
                structural_only += 1
            else:
                readiness = "AUDIT_ONLY_NO_GLOSS"
                audit_only += 1
            evidence = {"table": table, "item_id": item_id, "policy_status": status, "policy_confidence": conf}
            add_item(
                conn,
                run_id,
                item_id,
                table,
                status,
                readiness,
                conf,
                False,
                "local/audit context supports coverage but not semantic translation",
                "use_as_alignment_or_audit_context_only",
                evidence,
            )

    total = gloss_candidate + structural_only + audit_only
    decision = "SEMANTIC_READINESS_AUDIT_READY_NO_FINAL_TRANSLATION"
    conn.execute(
        """
        UPDATE semantic_readiness_audit_runs
        SET item_count=?,
            gloss_candidate_count=?,
            structural_only_count=?,
            audit_only_count=?,
            decision=?,
            payload_json=?
        WHERE run_id=?
        """,
        (
            total,
            gloss_candidate,
            structural_only,
            audit_only,
            decision,
            jdump({"blocked_phrase_count": int(blocked_count), "gloss_allowed_default": False}),
            run_id,
        ),
    )
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": decision, "item_count": total, "gloss_candidate_count": gloss_candidate, "structural_only_count": structural_only, "audit_only_count": audit_only, "blocked_phrase_count": int(blocked_count), "gloss_allowed_default": False}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
