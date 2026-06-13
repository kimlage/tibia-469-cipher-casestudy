#!/usr/bin/env python3
"""Create a human-readable atlas from shadow readings, anchors, and probes."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"


TARGET_TO_BRIDGE = {
    "49": "B_BOOK49_MATH49_REGISTER",
    "7": "B_BOOK7_PHASE_MATHEMAGIC",
    "12": "B_BOOK12_21_NO_O23_IMPORT",
    "21": "B_BOOK12_21_NO_O23_IMPORT",
    "26": "B_BOOK30_SPINE_GREAT_CALCULATOR",
    "30": "B_BOOK30_SPINE_GREAT_CALCULATOR",
    "54": "B_BOOK54_PAIR_LOCAL_SPINE",
}


PROBE_BY_BOOK = {
    "49": "human_book49_repeat_shadow_probe_v1",
    "7": "human_book7_phase_shadow_probe_v1",
    "12": "human_book12_21_tail_shadow_probe_v1 + human_book30_family_shadow_probe_v1",
    "21": "human_book12_21_tail_shadow_probe_v1 + human_book30_family_shadow_probe_v1",
    "26": "human_book30_family_shadow_probe_v1",
    "30": "human_book30_family_shadow_probe_v1",
    "54": "human_book54_pair_shadow_probe_v1",
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
        CREATE TABLE IF NOT EXISTS human_translation_atlas_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            shadow_run_id INTEGER NOT NULL,
            bridge_run_id INTEGER NOT NULL,
            item_count INTEGER NOT NULL,
            anchored_item_count INTEGER NOT NULL,
            ready_for_human_review_count INTEGER NOT NULL,
            promoted_gloss_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_translation_atlas_v1_items (
            run_id INTEGER NOT NULL,
            target_id TEXT NOT NULL,
            target_kind TEXT NOT NULL,
            likely_speech_act TEXT NOT NULL,
            plausible_human_reading TEXT NOT NULL,
            confidence_tier TEXT NOT NULL,
            source_bridge_id TEXT NOT NULL,
            anchor_ids_json TEXT NOT NULL,
            support_level TEXT NOT NULL,
            support_summary TEXT NOT NULL,
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


def confidence_for(bookid: str, bridge: dict[str, object] | None) -> str:
    if bookid in {"49", "7", "54"}:
        return "STRUCTURAL_STRONG_SHADOW"
    if bookid in {"12", "21"}:
        return "STRUCTURAL_STRONG_WITH_NEGATIVE_ENDPOINT_CONTROL"
    if bookid in {"26", "30"}:
        return "STRUCTURAL_MODERATE_FAMILY_SPINE"
    if bridge:
        return "ANCHORED_SHADOW"
    return "UNANCHORED_REVIEW_REQUIRED"


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    shadow_run_id = max_id(conn, "human_shadow_reading_v1_items")
    bridge_run_id = max_id(conn, "human_anchor_to_shadow_bridge_v1_items")
    bridge_rows = {
        row["bridge_id"]: dict(row)
        for row in conn.execute(
            "SELECT * FROM human_anchor_to_shadow_bridge_v1_items WHERE run_id=?",
            (bridge_run_id,),
        ).fetchall()
    }
    shadow_rows = conn.execute(
        """
        SELECT *
        FROM human_shadow_reading_v1_items
        WHERE run_id=?
        ORDER BY CAST(bookid AS INTEGER)
        """,
        (shadow_run_id,),
    ).fetchall()
    prepared = []
    for row in shadow_rows:
        bookid = str(row["bookid"])
        bridge_id = TARGET_TO_BRIDGE.get(bookid, "")
        bridge = bridge_rows.get(bridge_id) if bridge_id else None
        anchor_ids = parse_json(bridge["anchor_ids_json"], []) if bridge else []
        blocked_claims = parse_json(row["blocked_claims_json"], [])
        support_level = str(bridge["support_level"]) if bridge else "NO_BRIDGE"
        support_summary = str(bridge["support_summary"]) if bridge else "No source bridge found."
        blocked_overreach = str(bridge["blocked_overreach"]) if bridge else "Do not use until anchored."
        confidence = confidence_for(bookid, bridge)
        atlas_next_probe = str(bridge["next_probe"]) if bridge else str(row["next_probe"])
        prepared.append(
            {
                "target_id": bookid,
                "target_kind": "book",
                "likely_speech_act": row["likely_speech_act"],
                "plausible_human_reading": row["human_paraphrase"],
                "confidence_tier": confidence,
                "source_bridge_id": bridge_id,
                "anchor_ids_json": json.dumps(anchor_ids, ensure_ascii=False, sort_keys=True),
                "support_level": support_level,
                "support_summary": support_summary,
                "blocked_claims_json": json.dumps(blocked_claims, ensure_ascii=False, sort_keys=True),
                "blocked_overreach": blocked_overreach,
                "falsifier": row["falsifier"],
                "next_probe": atlas_next_probe,
                "probe_evidence": PROBE_BY_BOOK.get(bookid, "human_shadow_contradiction_check_v1"),
                "promotion_status": row["canonical_promotion_status"],
                "evidence_json": json.dumps(
                    {
                        "shadow_run_id": shadow_run_id,
                        "bridge_run_id": bridge_run_id,
                        "shadow_route_id": row["route_id"],
                        "shadow_candidate_status": row["candidate_status"],
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                ),
            }
        )

    anchored = sum(1 for item in prepared if item["source_bridge_id"])
    ready = sum(1 for item in prepared if item["promotion_status"] == "NOT_PROMOTED" and item["source_bridge_id"])
    payload = {
        "principle": "atlas is for human review and next-probe selection; it is not a canonical translation layer",
        "shadow_run_id": shadow_run_id,
        "bridge_run_id": bridge_run_id,
    }
    cur = conn.execute(
        """
        INSERT INTO human_translation_atlas_v1_runs
        (created_at, decision, shadow_run_id, bridge_run_id, item_count,
         anchored_item_count, ready_for_human_review_count, promoted_gloss_count,
         payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            now(),
            "HUMAN_TRANSLATION_ATLAS_READY_SHADOW_REVIEW_ONLY",
            shadow_run_id,
            bridge_run_id,
            len(prepared),
            anchored,
            ready,
            0,
            json.dumps(payload, ensure_ascii=False, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)
    for item in prepared:
        conn.execute(
            """
            INSERT INTO human_translation_atlas_v1_items
            (run_id, target_id, target_kind, likely_speech_act,
             plausible_human_reading, confidence_tier, source_bridge_id,
             anchor_ids_json, support_level, support_summary,
             blocked_claims_json, blocked_overreach, falsifier, next_probe,
             probe_evidence, promotion_status, evidence_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                item["target_id"],
                item["target_kind"],
                item["likely_speech_act"],
                item["plausible_human_reading"],
                item["confidence_tier"],
                item["source_bridge_id"],
                item["anchor_ids_json"],
                item["support_level"],
                item["support_summary"],
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
                "decision": "HUMAN_TRANSLATION_ATLAS_READY_SHADOW_REVIEW_ONLY",
                "item_count": len(prepared),
                "anchored_item_count": anchored,
                "ready_for_human_review_count": ready,
                "promoted_gloss_count": 0,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
