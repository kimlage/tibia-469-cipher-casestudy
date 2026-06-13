#!/usr/bin/env python3
"""Q15 audit: local client assets are too old to verify Bonelord Tome sounds."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
CLIENT_DIR = ROOT / "tmp" / "tibia_clients"


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q15_local_client_asset_gap_for_bonelord_tome_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            local_client_artifact_count INTEGER NOT NULL,
            old_client_artifact_count INTEGER NOT NULL,
            modern_client_candidate_count INTEGER NOT NULL,
            existing_old_client_probe_count INTEGER NOT NULL,
            bonelord_tome_verification_possible_count INTEGER NOT NULL,
            promoted_plaintext_gloss_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q15_local_client_asset_gap_for_bonelord_tome_v1_items (
            run_id INTEGER NOT NULL,
            item_id TEXT NOT NULL,
            item_type TEXT NOT NULL,
            status TEXT NOT NULL,
            role_label TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, item_id)
        );
        """
    )


def latest_optional(conn: sqlite3.Connection, table: str) -> sqlite3.Row | None:
    exists = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone()
    if not exists:
        return None
    return conn.execute(f"SELECT * FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()


def latest_id(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT max(run_id) FROM {table}").fetchone()
    if row is None or row[0] is None:
        raise RuntimeError(f"missing required run: {table}")
    return int(row[0])


def classify_artifact(path: Path) -> str:
    text = str(path).lower()
    if "tibia710" in text or "tibia760" in text or "7.10" in text or "7.60" in text:
        return "OLD_CLIENT_PRE_BONELORD_TOME"
    if "1271" in text or "12.71" in text or "2021" in text:
        return "MODERN_CLIENT_CANDIDATE"
    return "UNKNOWN_CLIENT_ARTIFACT"


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q14_run = latest_id(conn, "human_q14_register_bonelord_tome_verification_target_v1_runs")
    q13_run = latest_id(conn, "human_q13_bonelord_tome_source_ladder_projection_v1_runs")
    q14 = conn.execute(
        "SELECT * FROM human_q14_register_bonelord_tome_verification_target_v1_runs WHERE run_id=?",
        (q14_run,),
    ).fetchone()
    q13 = conn.execute(
        "SELECT * FROM human_q13_bonelord_tome_source_ladder_projection_v1_runs WHERE run_id=?",
        (q13_run,),
    ).fetchone()
    old_probe = latest_optional(conn, "old_client_asset_context_probe_runs")
    pic_probe = latest_optional(conn, "tibia760_pic_container_extract_runs")
    font_probe = latest_optional(conn, "tibia710_visual_font_alphabet_sweep_runs")

    artifacts: list[dict[str, object]] = []
    if CLIENT_DIR.exists():
        for path in sorted(CLIENT_DIR.rglob("*")):
            if path.is_file():
                status = classify_artifact(path)
                artifacts.append(
                    {
                        "path": str(path),
                        "size": path.stat().st_size,
                        "status": status,
                    }
                )

    local_client_artifact_count = len(artifacts)
    old_client_artifact_count = sum(1 for item in artifacts if item["status"] == "OLD_CLIENT_PRE_BONELORD_TOME")
    modern_client_candidate_count = sum(1 for item in artifacts if item["status"] == "MODERN_CLIENT_CANDIDATE")
    existing_old_client_probe_count = sum(1 for row in (old_probe, pic_probe, font_probe) if row is not None)
    bonelord_tome_verification_possible_count = int(modern_client_candidate_count > 0)
    promoted_plaintext_gloss_count = 0

    decision = (
        "Q15_LOCAL_CLIENT_ASSETS_CANNOT_VERIFY_BONELORD_TOME_NEED_MODERN_CLIENT_DATA_NO_GLOSS"
        if local_client_artifact_count > 0
        and old_client_artifact_count > 0
        and modern_client_candidate_count == 0
        and bonelord_tome_verification_possible_count == 0
        and promoted_plaintext_gloss_count == 0
        else "Q15_LOCAL_CLIENT_ASSET_GAP_REQUIRES_MANUAL_REVIEW"
    )

    items = [
        {
            "item_id": "target:q14-bonelord-tome-client-sounds",
            "item_type": "open_target",
            "status": "OPEN_TARGET_REQUIRES_MODERN_CLIENT_OR_OFFICIAL_DATA",
            "role_label": "Q14 target cannot be satisfied by current local client assets.",
            "evidence_json": j({"q14": dict(q14) if q14 else None, "q13": dict(q13) if q13 else None}),
        },
        {
            "item_id": "local:client-artifacts",
            "item_type": "local_asset_inventory",
            "status": "ONLY_OLD_OR_UNKNOWN_CLIENT_ARTIFACTS_FOUND",
            "role_label": "Local tmp/tibia_clients inventory contains old Tibia 7.10/7.60 assets and no obvious 12.71+ client data.",
            "evidence_json": j({"client_dir": str(CLIENT_DIR), "artifacts": artifacts}),
        },
        {
            "item_id": "control:old-client-probes",
            "item_type": "old_client_probe_context",
            "status": "OLD_CLIENT_PROBES_EXIST_BUT_DO_NOT_VERIFY_2021_ITEM",
            "role_label": "Existing old-client probes support historical asset work only; they cannot verify Bonelord Tome sounds.",
            "evidence_json": j(
                {
                    "old_client_asset_context": dict(old_probe) if old_probe else None,
                    "tibia760_pic_extract": dict(pic_probe) if pic_probe else None,
                    "tibia710_font_sweep": dict(font_probe) if font_probe else None,
                }
            ),
        },
    ]

    payload = {
        "question": "Can the current local client artifacts verify Bonelord Tome sounds?",
        "answer": "No. The available local client artifacts are old/historical and predate the 2021 Bonelord Tome item.",
        "next_action": "Acquire direct in-client capture, official item data, or trusted modern client-data extraction.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q15_local_client_asset_gap_for_bonelord_tome_v1_runs (
                created_at, decision, local_client_artifact_count,
                old_client_artifact_count, modern_client_candidate_count,
                existing_old_client_probe_count,
                bonelord_tome_verification_possible_count,
                promoted_plaintext_gloss_count, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                local_client_artifact_count,
                old_client_artifact_count,
                modern_client_candidate_count,
                existing_old_client_probe_count,
                bonelord_tome_verification_possible_count,
                promoted_plaintext_gloss_count,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q15_local_client_asset_gap_for_bonelord_tome_v1_items (
                run_id, item_id, item_type, status, role_label, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    item["item_id"],
                    item["item_type"],
                    item["status"],
                    item["role_label"],
                    item["evidence_json"],
                )
                for item in items
            ],
        )

    print(
        j(
            {
                "run_id": run_id,
                "decision": decision,
                "local_client_artifact_count": local_client_artifact_count,
                "old_client_artifact_count": old_client_artifact_count,
                "modern_client_candidate_count": modern_client_candidate_count,
                "existing_old_client_probe_count": existing_old_client_probe_count,
                "bonelord_tome_verification_possible_count": bonelord_tome_verification_possible_count,
                "promoted_plaintext_gloss_count": promoted_plaintext_gloss_count,
            }
        )
    )


if __name__ == "__main__":
    main()
