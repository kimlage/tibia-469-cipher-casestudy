#!/usr/bin/env python3
"""Seed human shadow readings for the Chayenne-frame books 8/37/63/66."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
BRIDGE_ID = "B_CHAYENNE_FRAME_REGISTER"


READING_BY_BRANCH = {
    "VNCTIIN_CONTEXT_BRANCH": {
        "likely_speech_act": "external register frame embedded in clean VNCTIIN context",
        "plausible_human_reading": "A clean VNCTIIN-context branch that carries the Chayenne external frame as register/context material rather than standalone prose.",
        "confidence_tier": "STRUCTURAL_STRONG_EXTERNAL_FRAME",
    },
    "LTAST_TO_VNCTIIN_BRANCH": {
        "likely_speech_act": "boundary handoff into external register frame",
        "plausible_human_reading": "A boundary-handoff branch where an LTAST/TTNVVN transition leads into the same Chayenne frame and then VNCTIIN context.",
        "confidence_tier": "STRUCTURAL_STRONG_EXTERNAL_FRAME",
    },
    "RESIDUAL_CONTINUATION_BRANCH": {
        "likely_speech_act": "residual continuation carrying external register frame",
        "plausible_human_reading": "A residual-continuation branch that preserves the Chayenne frame, useful as an audit witness but weaker than the clean VNCTIIN branches.",
        "confidence_tier": "STRUCTURAL_MODERATE_AUDIT_FRAME",
    },
    "BENNA_LTAST_FORMULA_BRANCH": {
        "likely_speech_act": "BENNA/LTAST formula branch carrying external register frame",
        "plausible_human_reading": "A formula/boundary branch where the Chayenne frame appears inside a BENNA/LTAST context, supporting register reuse rather than fixed sentence translation.",
        "confidence_tier": "STRUCTURAL_STRONG_FORMULA_FRAME",
    },
}


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_json(value: str | None, fallback):
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_chayenne_branch_shadow_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            chayenne_probe_run_id INTEGER NOT NULL,
            bridge_run_id INTEGER NOT NULL,
            item_count INTEGER NOT NULL,
            branch_count INTEGER NOT NULL,
            canonical_promotion_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_chayenne_branch_shadow_v1_items (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            branch_class TEXT NOT NULL,
            likely_speech_act TEXT NOT NULL,
            plausible_human_reading TEXT NOT NULL,
            confidence_tier TEXT NOT NULL,
            source_bridge_id TEXT NOT NULL,
            anchor_ids_json TEXT NOT NULL,
            support_level TEXT NOT NULL,
            blocked_claims_json TEXT NOT NULL,
            blocked_overreach TEXT NOT NULL,
            falsifier TEXT NOT NULL,
            next_probe TEXT NOT NULL,
            promotion_status TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        );
        """
    )


def max_id(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT max(run_id) AS run_id FROM {table}").fetchone()
    if row is None or row["run_id"] is None:
        raise RuntimeError(f"missing required run: {table}")
    return int(row["run_id"])


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    chayenne_probe_run_id = max_id(conn, "human_chayenne_shape_shadow_probe_v1_items")
    bridge_run_id = max_id(conn, "human_anchor_to_shadow_bridge_v1_items")
    bridge = conn.execute(
        """
        SELECT *
        FROM human_anchor_to_shadow_bridge_v1_items
        WHERE run_id=? AND bridge_id=?
        """,
        (bridge_run_id, BRIDGE_ID),
    ).fetchone()
    if bridge is None:
        raise RuntimeError(f"missing bridge {BRIDGE_ID}")

    rows = conn.execute(
        """
        SELECT *
        FROM human_chayenne_shape_shadow_probe_v1_items
        WHERE run_id=?
        ORDER BY CAST(bookid AS INTEGER)
        """,
        (chayenne_probe_run_id,),
    ).fetchall()
    prepared = []
    for row in rows:
        branch = str(row["branch_class"])
        reading = READING_BY_BRANCH.get(branch)
        if reading is None:
            reading = {
                "likely_speech_act": "unclassified Chayenne-frame branch",
                "plausible_human_reading": "An unclassified branch carrying the Chayenne external frame; keep audit-only until branch support improves.",
                "confidence_tier": "STRUCTURAL_AUDIT_ONLY",
            }
        blockers = parse_json(row["blocked_claims_json"], [])
        prepared.append(
            {
                "bookid": str(row["bookid"]),
                "branch_class": branch,
                **reading,
                "source_bridge_id": BRIDGE_ID,
                "anchor_ids_json": bridge["anchor_ids_json"],
                "support_level": bridge["support_level"],
                "blocked_claims_json": json.dumps(blockers, ensure_ascii=False, sort_keys=True),
                "blocked_overreach": bridge["blocked_overreach"],
                "falsifier": row["falsifier"],
                "next_probe": row["next_probe"],
                "promotion_status": "NOT_PROMOTED",
                "evidence_json": json.dumps(
                    {
                        "chayenne_probe_run_id": chayenne_probe_run_id,
                        "bridge_run_id": bridge_run_id,
                        "block_pos": row["block_pos"],
                        "left_context": row["left_context"],
                        "right_context": row["right_context"],
                        "human_shadow_role": row["human_shadow_role"],
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                ),
            }
        )

    branches = sorted({item["branch_class"] for item in prepared})
    cur = conn.execute(
        """
        INSERT INTO human_chayenne_branch_shadow_v1_runs
        (created_at, decision, chayenne_probe_run_id, bridge_run_id,
         item_count, branch_count, canonical_promotion_count, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            now(),
            "HUMAN_CHAYENNE_BRANCH_SHADOW_READY_NOT_PROMOTED",
            chayenne_probe_run_id,
            bridge_run_id,
            len(prepared),
            len(branches),
            0,
            json.dumps({"branches": branches, "bridge_id": BRIDGE_ID}, ensure_ascii=False, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)
    for item in prepared:
        conn.execute(
            """
            INSERT INTO human_chayenne_branch_shadow_v1_items
            (run_id, bookid, branch_class, likely_speech_act,
             plausible_human_reading, confidence_tier, source_bridge_id,
             anchor_ids_json, support_level, blocked_claims_json,
             blocked_overreach, falsifier, next_probe, promotion_status,
             evidence_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                item["bookid"],
                item["branch_class"],
                item["likely_speech_act"],
                item["plausible_human_reading"],
                item["confidence_tier"],
                item["source_bridge_id"],
                item["anchor_ids_json"],
                item["support_level"],
                item["blocked_claims_json"],
                item["blocked_overreach"],
                item["falsifier"],
                item["next_probe"],
                item["promotion_status"],
                item["evidence_json"],
            ),
        )

    conn.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": "HUMAN_CHAYENNE_BRANCH_SHADOW_READY_NOT_PROMOTED",
                "item_count": len(prepared),
                "branch_count": len(branches),
                "canonical_promotion_count": 0,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
