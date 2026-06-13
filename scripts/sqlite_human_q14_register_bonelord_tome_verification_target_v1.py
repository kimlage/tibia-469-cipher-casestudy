#!/usr/bin/env python3
"""Q14: register Bonelord Tome client/official sound verification as an open target."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

TARGET = {
    "target_id": "BONELORD_TOME_CLIENT_SOUNDS",
    "target_class": "client_or_official_item_sound",
    "exact_sequence": "3478 67 90871 97664 3466 0 345;486486",
    "current_status": "OPEN_NEEDS_CLIENT_OR_OFFICIAL_ITEM_SOUND_VERIFICATION",
    "priority": 1,
    "required_evidence": (
        "direct in-client capture, official item data, or trusted client-data extraction showing Bonelord Tome sounds "
        "with 3478 phrase and 486486 answer/attention line"
    ),
    "next_action": (
        "verify sounds directly; if verified, keep phrase/name/formula scope and do not promote component/book gloss without explicit meaning"
    ),
    "payload": {
        "source_q13": "Bonelord Tome source ladder found secondary sound attestation but no direct official/client sound source",
        "acceptance_gate": "exact item sound source plus provenance; explicit meaning required for semantic promotion",
    },
}


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS external_semantic_open_target_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            target_count INTEGER NOT NULL,
            high_priority_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS external_semantic_open_targets (
            run_id INTEGER NOT NULL,
            target_id TEXT NOT NULL,
            target_class TEXT NOT NULL,
            exact_sequence TEXT NOT NULL,
            current_status TEXT NOT NULL,
            priority INTEGER NOT NULL,
            required_evidence TEXT NOT NULL,
            next_action TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, target_id)
        );

        CREATE TABLE IF NOT EXISTS human_q14_register_bonelord_tome_verification_target_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            source_open_target_run_id INTEGER NOT NULL,
            new_open_target_run_id INTEGER NOT NULL,
            previous_target_count INTEGER NOT NULL,
            new_target_count INTEGER NOT NULL,
            high_priority_count INTEGER NOT NULL,
            promoted_plaintext_gloss_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q14_register_bonelord_tome_verification_target_v1_items (
            run_id INTEGER NOT NULL,
            target_id TEXT NOT NULL,
            registration_status TEXT NOT NULL,
            priority INTEGER NOT NULL,
            required_evidence TEXT NOT NULL,
            next_action TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, target_id)
        );
        """
    )


def latest_id(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT max(run_id) FROM {table}").fetchone()
    if row is None or row[0] is None:
        raise RuntimeError(f"missing required run: {table}")
    return int(row[0])


def rows(conn: sqlite3.Connection, sql: str, params: tuple[object, ...] = ()) -> list[sqlite3.Row]:
    return list(conn.execute(sql, params).fetchall())


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    source_open_target_run_id = latest_id(conn, "external_semantic_open_target_runs")
    q13_run_id = latest_id(conn, "human_q13_bonelord_tome_source_ladder_projection_v1_runs")
    source_rows = rows(
        conn,
        """
        SELECT *
        FROM external_semantic_open_targets
        WHERE run_id=?
        ORDER BY priority, target_id
        """,
        (source_open_target_run_id,),
    )

    merged: dict[str, dict[str, object]] = {str(row["target_id"]): dict(row) for row in source_rows}
    previous_target_count = len(merged)
    merged[TARGET["target_id"]] = {
        "target_id": TARGET["target_id"],
        "target_class": TARGET["target_class"],
        "exact_sequence": TARGET["exact_sequence"],
        "current_status": TARGET["current_status"],
        "priority": TARGET["priority"],
        "required_evidence": TARGET["required_evidence"],
        "next_action": TARGET["next_action"],
        "payload_json": j({**TARGET["payload"], "q13_run_id": q13_run_id}),
    }

    ordered = sorted(merged.values(), key=lambda row: (int(row["priority"]), str(row["target_id"])))
    new_target_count = len(ordered)
    high_priority_count = sum(1 for row in ordered if int(row["priority"]) == 1)
    promoted_plaintext_gloss_count = 0

    decision = (
        "Q14_BONELORD_TOME_CLIENT_SOUND_VERIFICATION_TARGET_REGISTERED_NO_GLOSS"
        if new_target_count >= previous_target_count
        and TARGET["target_id"] in merged
        and promoted_plaintext_gloss_count == 0
        else "Q14_BONELORD_TOME_TARGET_REGISTRATION_REQUIRES_MANUAL_REVIEW"
    )

    payload = {
        "purpose": "semantic unlock backlog after Q13; not promotion",
        "added_or_updated_target": TARGET["target_id"],
        "source_q13_run_id": q13_run_id,
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO external_semantic_open_target_runs (
                created_at, decision, target_count, high_priority_count, payload_json
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                now(),
                "EXTERNAL_SEMANTIC_OPEN_TARGETS_REGISTERED_AFTER_BONELORD_TOME_Q13",
                new_target_count,
                high_priority_count,
                j(payload),
            ),
        )
        new_open_target_run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO external_semantic_open_targets (
                run_id, target_id, target_class, exact_sequence, current_status,
                priority, required_evidence, next_action, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    new_open_target_run_id,
                    str(row["target_id"]),
                    str(row["target_class"]),
                    str(row["exact_sequence"]),
                    str(row["current_status"]),
                    int(row["priority"]),
                    str(row["required_evidence"]),
                    str(row["next_action"]),
                    str(row["payload_json"]),
                )
                for row in ordered
            ],
        )

        cur = conn.execute(
            """
            INSERT INTO human_q14_register_bonelord_tome_verification_target_v1_runs (
                created_at, decision, source_open_target_run_id,
                new_open_target_run_id, previous_target_count, new_target_count,
                high_priority_count, promoted_plaintext_gloss_count, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                source_open_target_run_id,
                new_open_target_run_id,
                previous_target_count,
                new_target_count,
                high_priority_count,
                promoted_plaintext_gloss_count,
                j(payload),
            ),
        )
        q14_run_id = int(cur.lastrowid)
        conn.execute(
            """
            INSERT INTO human_q14_register_bonelord_tome_verification_target_v1_items (
                run_id, target_id, registration_status, priority,
                required_evidence, next_action, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                q14_run_id,
                TARGET["target_id"],
                "REGISTERED_OPEN_TARGET_NO_GLOSS",
                int(TARGET["priority"]),
                str(TARGET["required_evidence"]),
                str(TARGET["next_action"]),
                j({**TARGET["payload"], "q13_run_id": q13_run_id, "new_open_target_run_id": new_open_target_run_id}),
            ),
        )

    print(
        j(
            {
                "run_id": q14_run_id,
                "decision": decision,
                "source_open_target_run_id": source_open_target_run_id,
                "new_open_target_run_id": new_open_target_run_id,
                "previous_target_count": previous_target_count,
                "new_target_count": new_target_count,
                "high_priority_count": high_priority_count,
                "promoted_plaintext_gloss_count": promoted_plaintext_gloss_count,
            }
        )
    )


if __name__ == "__main__":
    main()
