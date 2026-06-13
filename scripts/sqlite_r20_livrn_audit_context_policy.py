#!/usr/bin/env python3
"""Materialize R20/R02 LIVRN as audit context for coverage, not promotion."""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "bonelord_operational.sqlite"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def jdump(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()
    conn = sqlite3.connect(args.db, timeout=30)
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS r20_livrn_audit_context_policy_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS r20_livrn_audit_context_policy_items (
            run_id INTEGER NOT NULL,
            context_id TEXT NOT NULL,
            policy_status TEXT NOT NULL,
            policy_confidence REAL NOT NULL,
            books_json TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            next_action TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, context_id)
        );
        """
    )
    evidence = {
        "books": ["60", "64"],
        "context": "L I V R20 N",
        "policy_scope": "audit_context_only_not_function_ready",
        "reason": "R20_LIVRN_MICRO has 2 occurrences and no enough contrast for promotion",
        "gloss_allowed": False,
    }
    cur = conn.execute(
        "INSERT INTO r20_livrn_audit_context_policy_runs (created_at, decision, payload_json) VALUES (?, ?, ?)",
        (utc_now(), "R20_LIVRN_AUDIT_CONTEXT_READY", jdump({"evidence": evidence, "gloss_allowed": False})),
    )
    run_id = int(cur.lastrowid)
    conn.execute(
        """
        INSERT INTO r20_livrn_audit_context_policy_items
            (run_id, context_id, policy_status, policy_confidence, books_json,
             evidence_json, next_action, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            "AUDIT_R20_LIVRN_MICRO_CONTEXT",
            "AUDIT_CONTEXT",
            0.42,
            jdump(["60", "64"]),
            jdump(evidence),
            "use_for_coverage_only_do_not_promote_r20_livrn",
            jdump({"evidence": evidence, "gloss_allowed": False}),
        ),
    )
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": "R20_LIVRN_AUDIT_CONTEXT_READY", "context_id": "AUDIT_R20_LIVRN_MICRO_CONTEXT", "policy_status": "AUDIT_CONTEXT", "policy_confidence": 0.42, "gloss_allowed": False}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
