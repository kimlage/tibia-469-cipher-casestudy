#!/usr/bin/env python3
"""Q27: reconcile transcript-backed Mathemagic operators with existing tests."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

OPERATORS = ["1", "13", "49", "94"]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q27_mathemagic_operator_queue_reconcile_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q26_run_id INTEGER NOT NULL,
            operational_decision_run_id INTEGER NOT NULL,
            operator_count INTEGER NOT NULL,
            live_local_operator_count INTEGER NOT NULL,
            weak_audit_selector_count INTEGER NOT NULL,
            dead_or_blocked_count INTEGER NOT NULL,
            untested_context_count INTEGER NOT NULL,
            plaintext_allowed_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q27_mathemagic_operator_queue_reconcile_v1_items (
            run_id INTEGER NOT NULL,
            operator_value TEXT NOT NULL,
            source_status TEXT NOT NULL,
            current_status TEXT NOT NULL,
            allowed_scope TEXT NOT NULL,
            plaintext_allowed INTEGER NOT NULL,
            canonical_promotion_allowed INTEGER NOT NULL,
            next_probe TEXT NOT NULL,
            rejection_rule TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, operator_value)
        );
        """
    )


def latest_run_id(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT max(run_id) FROM {table}").fetchone()
    if row is None or row[0] is None:
        raise RuntimeError(f"missing required run: {table}")
    return int(row[0])


def op_decisions(conn: sqlite3.Connection, run_id: int) -> dict[str, dict[str, object]]:
    rows = conn.execute(
        """
        SELECT *
        FROM mathemagic_operational_decision_v1_items
        WHERE run_id=?
        """,
        (run_id,),
    ).fetchall()
    return {str(row["hypothesis_id"]): dict(row) for row in rows}


def build_items(decisions: dict[str, dict[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "operator_value": "1",
            "source_status": "TRANSCRIPT_ATTESTED_OUTPUT_AND_AWB_TIBIA_ANCHOR",
            "current_status": "CONTEXT_ONLY_UNTESTED_AS_SELECTOR",
            "allowed_scope": "world/name/formula context; do not read as lexical word",
            "plaintext_allowed": 0,
            "canonical_promotion_allowed": 0,
            "next_probe": "Test only as world/identity/boundary context when an independent source introduces a matching target.",
            "rejection_rule": "Reject any use of 1 as universal plaintext or book dictionary entry.",
            "evidence": {
                "q26_output": "1",
                "awb_anchor": "Tibia=1",
                "existing_operational_decision": None,
            },
        },
        {
            "operator_value": "13",
            "source_status": "TRANSCRIPT_ATTESTED_OUTPUT",
            "current_status": "LIVE_LOCAL_OPERATOR_ONLY",
            "allowed_scope": "C86/C68 local delta and secondary audit selector only",
            "plaintext_allowed": 0,
            "canonical_promotion_allowed": 0,
            "next_probe": "Use inside vetted C86/C68 contexts; require held-out pass before any broader selector use.",
            "rejection_rule": "Reject broad 13 interpretations outside local family evidence.",
            "evidence": {
                "primary": decisions.get("DELTA13_C86_TO_C68"),
                "secondary": decisions.get("MOD70_13_TO_BOOK13"),
            },
        },
        {
            "operator_value": "49",
            "source_status": "TRANSCRIPT_ATTESTED_OUTPUT",
            "current_status": "DEAD_FOR_GENERAL_SELECTOR_PROMOTION_AUDIT_ONLY",
            "allowed_scope": "narrow audit note only; no general selector",
            "plaintext_allowed": 0,
            "canonical_promotion_allowed": 0,
            "next_probe": "Reopen only with a new independent holdout that changes the evidence graph.",
            "rejection_rule": "Reject +49 as general selector because current wide/rank holdouts failed.",
            "evidence": {
                "primary": decisions.get("PLUS49_MOD70_FRONTIER_SELECTOR"),
                "related": decisions.get("MOD70_469_TO_BOOK49"),
            },
        },
        {
            "operator_value": "94",
            "source_status": "TRANSCRIPT_ATTESTED_OUTPUT",
            "current_status": "WEAK_AUDIT_SELECTOR_ONLY",
            "allowed_scope": "94->24 audit selector pending independent book24 structure",
            "plaintext_allowed": 0,
            "canonical_promotion_allowed": 0,
            "next_probe": "Retest only if Book24 gains independent promoted structure or external source support.",
            "rejection_rule": "Reject if 94->24 only ranks plausible stories or lacks non-circular improvement.",
            "evidence": {
                "primary": decisions.get("MOD70_94_TO_BOOK24"),
            },
        },
    ]


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q26_run_id = latest_run_id(conn, "human_q26_mathemagic_transcript_bridge_import_v1_runs")
    op_run_id = latest_run_id(conn, "mathemagic_operational_decision_v1_items")
    decisions = op_decisions(conn, op_run_id)
    items = build_items(decisions)

    live_local_operator_count = sum(1 for item in items if item["current_status"] == "LIVE_LOCAL_OPERATOR_ONLY")
    weak_audit_selector_count = sum(1 for item in items if "WEAK_AUDIT" in item["current_status"])
    dead_or_blocked_count = sum(1 for item in items if "DEAD" in item["current_status"] or "BLOCKED" in item["current_status"])
    untested_context_count = sum(1 for item in items if "UNTESTED" in item["current_status"])
    plaintext_allowed_count = sum(int(item["plaintext_allowed"]) for item in items)
    canonical_promotion_allowed_count = sum(int(item["canonical_promotion_allowed"]) for item in items)
    decision = (
        "Q27_MATHEMAGIC_OPERATOR_QUEUE_RECONCILED_NO_GLOSS"
        if len(items) == len(OPERATORS)
        and plaintext_allowed_count == 0
        and canonical_promotion_allowed_count == 0
        and live_local_operator_count == 1
        and weak_audit_selector_count == 1
        and dead_or_blocked_count == 1
        and untested_context_count == 1
        else "Q27_MATHEMAGIC_OPERATOR_QUEUE_REQUIRES_MANUAL_REVIEW"
    )
    payload = {
        "question": "After exact transcript import, which Mathemagic operators remain live?",
        "answer": "Only 13 is live locally; 94 is weak audit-only; 49 is blocked for general selector use; 1 is context-only.",
        "operator_values": OPERATORS,
        "blocked_reading": "No Mathemagic operator is a plaintext word or book gloss.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q27_mathemagic_operator_queue_reconcile_v1_runs (
                created_at, decision, q26_run_id, operational_decision_run_id,
                operator_count, live_local_operator_count, weak_audit_selector_count,
                dead_or_blocked_count, untested_context_count, plaintext_allowed_count,
                canonical_promotion_allowed_count, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                q26_run_id,
                op_run_id,
                len(items),
                live_local_operator_count,
                weak_audit_selector_count,
                dead_or_blocked_count,
                untested_context_count,
                plaintext_allowed_count,
                canonical_promotion_allowed_count,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q27_mathemagic_operator_queue_reconcile_v1_items (
                run_id, operator_value, source_status, current_status,
                allowed_scope, plaintext_allowed, canonical_promotion_allowed,
                next_probe, rejection_rule, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    str(item["operator_value"]),
                    str(item["source_status"]),
                    str(item["current_status"]),
                    str(item["allowed_scope"]),
                    int(item["plaintext_allowed"]),
                    int(item["canonical_promotion_allowed"]),
                    str(item["next_probe"]),
                    str(item["rejection_rule"]),
                    j(item["evidence"]),
                )
                for item in items
            ],
        )

    print(
        j(
            {
                "run_id": run_id,
                "decision": decision,
                "q26_run_id": q26_run_id,
                "operational_decision_run_id": op_run_id,
                "operator_count": len(items),
                "live_local_operator_count": live_local_operator_count,
                "weak_audit_selector_count": weak_audit_selector_count,
                "dead_or_blocked_count": dead_or_blocked_count,
                "untested_context_count": untested_context_count,
                "plaintext_allowed_count": plaintext_allowed_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
            }
        )
    )


if __name__ == "__main__":
    main()
