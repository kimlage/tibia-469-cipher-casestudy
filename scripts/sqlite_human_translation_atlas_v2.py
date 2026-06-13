#!/usr/bin/env python3
"""Build a broader human translation atlas including Chayenne branch books."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_translation_atlas_v2_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            atlas_v1_run_id INTEGER NOT NULL,
            chayenne_branch_run_id INTEGER NOT NULL,
            item_count INTEGER NOT NULL,
            new_item_count INTEGER NOT NULL,
            anchored_item_count INTEGER NOT NULL,
            ready_for_human_review_count INTEGER NOT NULL,
            promoted_gloss_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_translation_atlas_v2_items (
            run_id INTEGER NOT NULL,
            target_id TEXT NOT NULL,
            target_kind TEXT NOT NULL,
            source_layer TEXT NOT NULL,
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
            probe_evidence TEXT NOT NULL,
            promotion_status TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, target_id)
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

    atlas_v1_run_id = max_id(conn, "human_translation_atlas_v1_items")
    chayenne_branch_run_id = max_id(conn, "human_chayenne_branch_shadow_v1_items")
    prepared: list[dict[str, object]] = []
    for row in conn.execute(
        """
        SELECT *
        FROM human_translation_atlas_v1_items
        WHERE run_id=?
        ORDER BY CAST(target_id AS INTEGER)
        """,
        (atlas_v1_run_id,),
    ).fetchall():
        prepared.append(
            {
                "target_id": str(row["target_id"]),
                "target_kind": str(row["target_kind"]),
                "source_layer": "human_translation_atlas_v1",
                "likely_speech_act": row["likely_speech_act"],
                "plausible_human_reading": row["plausible_human_reading"],
                "confidence_tier": row["confidence_tier"],
                "source_bridge_id": row["source_bridge_id"],
                "anchor_ids_json": row["anchor_ids_json"],
                "support_level": row["support_level"],
                "blocked_claims_json": row["blocked_claims_json"],
                "blocked_overreach": row["blocked_overreach"],
                "falsifier": row["falsifier"],
                "next_probe": row["next_probe"],
                "probe_evidence": row["probe_evidence"],
                "promotion_status": row["promotion_status"],
                "evidence_json": row["evidence_json"],
            }
        )
    for row in conn.execute(
        """
        SELECT *
        FROM human_chayenne_branch_shadow_v1_items
        WHERE run_id=?
        ORDER BY CAST(bookid AS INTEGER)
        """,
        (chayenne_branch_run_id,),
    ).fetchall():
        prepared.append(
            {
                "target_id": str(row["bookid"]),
                "target_kind": "book",
                "source_layer": "human_chayenne_branch_shadow_v1",
                "likely_speech_act": row["likely_speech_act"],
                "plausible_human_reading": row["plausible_human_reading"],
                "confidence_tier": row["confidence_tier"],
                "source_bridge_id": row["source_bridge_id"],
                "anchor_ids_json": row["anchor_ids_json"],
                "support_level": row["support_level"],
                "blocked_claims_json": row["blocked_claims_json"],
                "blocked_overreach": row["blocked_overreach"],
                "falsifier": row["falsifier"],
                "next_probe": row["next_probe"],
                "probe_evidence": "human_chayenne_shape_shadow_probe_v1",
                "promotion_status": row["promotion_status"],
                "evidence_json": row["evidence_json"],
            }
        )

    anchored = sum(1 for item in prepared if item["source_bridge_id"])
    ready = sum(1 for item in prepared if item["promotion_status"] == "NOT_PROMOTED" and item["source_bridge_id"])
    promoted = sum(1 for item in prepared if item["promotion_status"] != "NOT_PROMOTED")
    decision = "HUMAN_TRANSLATION_ATLAS_V2_READY_11_SHADOW_READINGS"
    payload = {
        "principle": "v2 expands the human atlas with external-frame branch books; still shadow only",
        "atlas_v1_run_id": atlas_v1_run_id,
        "chayenne_branch_run_id": chayenne_branch_run_id,
    }
    cur = conn.execute(
        """
        INSERT INTO human_translation_atlas_v2_runs
        (created_at, decision, atlas_v1_run_id, chayenne_branch_run_id,
         item_count, new_item_count, anchored_item_count,
         ready_for_human_review_count, promoted_gloss_count, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            now(),
            decision,
            atlas_v1_run_id,
            chayenne_branch_run_id,
            len(prepared),
            4,
            anchored,
            ready,
            promoted,
            json.dumps(payload, ensure_ascii=False, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)
    for item in prepared:
        conn.execute(
            """
            INSERT INTO human_translation_atlas_v2_items
            (run_id, target_id, target_kind, source_layer,
             likely_speech_act, plausible_human_reading, confidence_tier,
             source_bridge_id, anchor_ids_json, support_level,
             blocked_claims_json, blocked_overreach, falsifier, next_probe,
             probe_evidence, promotion_status, evidence_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                item["target_id"],
                item["target_kind"],
                item["source_layer"],
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
                item["probe_evidence"],
                item["promotion_status"],
                item["evidence_json"],
            ),
        )

    conn.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "item_count": len(prepared),
                "new_item_count": 4,
                "anchored_item_count": anchored,
                "ready_for_human_review_count": ready,
                "promoted_gloss_count": promoted,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
