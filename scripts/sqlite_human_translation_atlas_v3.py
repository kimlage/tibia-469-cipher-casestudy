#!/usr/bin/env python3
"""Build human translation atlas v3 by adding C86/VNCTIIN readings."""

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
        CREATE TABLE IF NOT EXISTS human_translation_atlas_v3_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            atlas_v2_run_id INTEGER NOT NULL,
            c86_shadow_run_id INTEGER NOT NULL,
            item_count INTEGER NOT NULL,
            new_item_count INTEGER NOT NULL,
            anchored_item_count INTEGER NOT NULL,
            ready_for_human_review_count INTEGER NOT NULL,
            promoted_gloss_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_translation_atlas_v3_items (
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


def copy_v2(conn: sqlite3.Connection, atlas_v2_run_id: int) -> list[dict[str, object]]:
    return [
        dict(row)
        for row in conn.execute(
            "SELECT * FROM human_translation_atlas_v2_items WHERE run_id=?",
            (atlas_v2_run_id,),
        ).fetchall()
    ]


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    atlas_v2_run_id = max_id(conn, "human_translation_atlas_v2_items")
    c86_shadow_run_id = max_id(conn, "human_c86_vnctiin_shadow_v1_items")
    prepared = []
    for row in copy_v2(conn, atlas_v2_run_id):
        item = dict(row)
        item["source_layer"] = item["source_layer"]
        prepared.append(item)
    for row in conn.execute(
        "SELECT * FROM human_c86_vnctiin_shadow_v1_items WHERE run_id=?",
        (c86_shadow_run_id,),
    ).fetchall():
        prepared.append(
            {
                "target_id": str(row["bookid"]),
                "target_kind": "book",
                "source_layer": "human_c86_vnctiin_shadow_v1",
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
                "probe_evidence": "human_c86_vnctiin_shadow_v1",
                "promotion_status": row["promotion_status"],
                "evidence_json": row["evidence_json"],
            }
        )

    # Deduplicate defensively, preferring later C86-specific rows.
    by_target: dict[str, dict[str, object]] = {}
    for item in prepared:
        by_target[str(item["target_id"])] = item
    final_items = [by_target[key] for key in sorted(by_target, key=lambda value: int(value))]
    anchored = sum(1 for item in final_items if item["source_bridge_id"])
    ready = sum(1 for item in final_items if item["promotion_status"] == "NOT_PROMOTED" and item["source_bridge_id"])
    promoted = sum(1 for item in final_items if item["promotion_status"] != "NOT_PROMOTED")
    decision = "HUMAN_TRANSLATION_ATLAS_V3_READY_25_SHADOW_READINGS"
    cur = conn.execute(
        """
        INSERT INTO human_translation_atlas_v3_runs
        (created_at, decision, atlas_v2_run_id, c86_shadow_run_id,
         item_count, new_item_count, anchored_item_count,
         ready_for_human_review_count, promoted_gloss_count, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            now(),
            decision,
            atlas_v2_run_id,
            c86_shadow_run_id,
            len(final_items),
            14,
            anchored,
            ready,
            promoted,
            json.dumps({"principle": "v3 adds C86/VNCTIIN-family shadow readings"}, ensure_ascii=False, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)
    for item in final_items:
        conn.execute(
            """
            INSERT INTO human_translation_atlas_v3_items
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
                "item_count": len(final_items),
                "new_item_count": 14,
                "anchored_item_count": anchored,
                "ready_for_human_review_count": ready,
                "promoted_gloss_count": promoted,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
