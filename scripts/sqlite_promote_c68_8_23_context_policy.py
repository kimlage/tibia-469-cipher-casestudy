#!/usr/bin/env python3
"""Materialize local C68 context alignment for books 8/23, no global C68 gloss."""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "bonelord_operational.sqlite"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def jdump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS c68_8_23_context_policy_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS c68_8_23_context_policy_items (
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db, timeout=30)
    ensure_schema(conn)
    evidence = {
        "books": ["8", "23"],
        "shared_context": "E I L T A E N E E I V N C68 T I I N N",
        "policy_scope": "local_c68_context_alignment_not_global_c68",
        "supports": ["C68_VNCTIIN_or_TIINN_context", "book23_naese_fatct_tail_context"],
        "blocks": ["global_C68_gloss", "plaintext_translation"],
        "gloss_allowed": False,
    }
    cur = conn.execute(
        """
        INSERT INTO c68_8_23_context_policy_runs
            (created_at, decision, payload_json)
        VALUES (?, ?, ?)
        """,
        (utc_now(), "C68_8_23_CONTEXT_POLICY_READY", jdump({"evidence": evidence, "gloss_allowed": False})),
    )
    run_id = int(cur.lastrowid)
    conn.execute(
        """
        INSERT INTO c68_8_23_context_policy_items
            (run_id, context_id, policy_status, policy_confidence,
             books_json, evidence_json, next_action, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            "LOCAL_PAIR_8_23_C68_CONTEXT_ALIGNMENT",
            "LOCAL_CONTEXT_READY",
            0.63,
            jdump(["8", "23"]),
            jdump(evidence),
            "use_as_local_c68_context_no_global_c68_no_gloss",
            jdump({"evidence": evidence, "gloss_allowed": False}),
        ),
    )
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": "C68_8_23_CONTEXT_POLICY_READY", "context_id": "LOCAL_PAIR_8_23_C68_CONTEXT_ALIGNMENT", "policy_status": "LOCAL_CONTEXT_READY", "policy_confidence": 0.63, "gloss_allowed": False}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
