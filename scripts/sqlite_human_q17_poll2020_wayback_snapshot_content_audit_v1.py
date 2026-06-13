#!/usr/bin/env python3
"""Q17 audit: Wayback snapshots for poll 2020 option C contain no usable poll content."""

from __future__ import annotations

import datetime as dt
import json
import re
import sqlite3
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

ORIGINAL_URL = "https://www.tibia.com/community/?subtopic=polls&page=show&questionaireid=1009"
SNAPSHOTS = ["20211119130214", "20231106140612", "20241204164805"]
EXACT_SEQUENCE = "663 902073 7223 67538 467 80097"
QUESTION_TEXT = "When the veils of shrouded truths are lifted, who can stand?"


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def clean_html(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", text)


def fetch_snapshot(timestamp: str) -> dict[str, object]:
    url = f"https://web.archive.org/web/{timestamp}id_/{ORIGINAL_URL}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            html = resp.read().decode("utf-8", "replace")
            text = clean_html(html)
            return {
                "timestamp": timestamp,
                "url": url,
                "ok": True,
                "status": getattr(resp, "status", None),
                "length": len(html),
                "has_exact_sequence": EXACT_SEQUENCE in text,
                "has_question_text": QUESTION_TEXT in text,
                "has_deepling_option": "BOQOT" in text,
                "content_preview": text[:500],
            }
    except Exception as exc:
        return {
            "timestamp": timestamp,
            "url": url,
            "ok": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q17_poll2020_wayback_snapshot_content_audit_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q16_run_id INTEGER NOT NULL,
            snapshot_count INTEGER NOT NULL,
            snapshot_fetch_success_count INTEGER NOT NULL,
            exact_content_hit_count INTEGER NOT NULL,
            question_content_hit_count INTEGER NOT NULL,
            primary_context_resolved_count INTEGER NOT NULL,
            promoted_plaintext_gloss_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q17_poll2020_wayback_snapshot_content_audit_v1_items (
            run_id INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            snapshot_url TEXT NOT NULL,
            status TEXT NOT NULL,
            support_class TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, timestamp)
        );
        """
    )


def latest_id(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT max(run_id) FROM {table}").fetchone()
    if row is None or row[0] is None:
        raise RuntimeError(f"missing required run: {table}")
    return int(row[0])


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q16_run_id = latest_id(conn, "human_q16_poll2020_primary_context_access_audit_v1_runs")
    results = [fetch_snapshot(ts) for ts in SNAPSHOTS]

    snapshot_count = len(results)
    snapshot_fetch_success_count = sum(1 for row in results if row.get("ok"))
    exact_content_hit_count = sum(1 for row in results if row.get("has_exact_sequence"))
    question_content_hit_count = sum(1 for row in results if row.get("has_question_text"))
    primary_context_resolved_count = int(exact_content_hit_count > 0 and question_content_hit_count > 0)
    promoted_plaintext_gloss_count = 0

    decision = (
        "Q17_POLL_2020_WAYBACK_SNAPSHOTS_NO_CONTENT_TARGET_REMAINS_OPEN_NO_GLOSS"
        if snapshot_count == len(SNAPSHOTS)
        and snapshot_fetch_success_count >= 1
        and exact_content_hit_count == 0
        and question_content_hit_count == 0
        and primary_context_resolved_count == 0
        and promoted_plaintext_gloss_count == 0
        else "Q17_POLL_2020_WAYBACK_SNAPSHOT_AUDIT_REQUIRES_MANUAL_REVIEW"
    )

    payload = {
        "question": "Do the currently discovered Wayback snapshots contain the 2020 poll question and option C sequence?",
        "answer": "No. The snapshots fetch, but none contains the exact 469 option C sequence or the poll question text.",
        "next_action": "Keep POLL_2020_OPTION_C open; search alternate archives or authenticated/primary contexts.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q17_poll2020_wayback_snapshot_content_audit_v1_runs (
                created_at, decision, q16_run_id, snapshot_count,
                snapshot_fetch_success_count, exact_content_hit_count,
                question_content_hit_count, primary_context_resolved_count,
                promoted_plaintext_gloss_count, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                q16_run_id,
                snapshot_count,
                snapshot_fetch_success_count,
                exact_content_hit_count,
                question_content_hit_count,
                primary_context_resolved_count,
                promoted_plaintext_gloss_count,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q17_poll2020_wayback_snapshot_content_audit_v1_items (
                run_id, timestamp, snapshot_url, status, support_class, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    str(row["timestamp"]),
                    str(row["url"]),
                    "SNAPSHOT_FETCHED_WITHOUT_POLL_CONTENT" if row.get("ok") else "SNAPSHOT_FETCH_FAILED",
                    "BLOCK_NO_PRIMARY_POLL_CONTENT" if not (row.get("has_exact_sequence") and row.get("has_question_text")) else "PRIMARY_CONTEXT_MATCH",
                    j(row),
                )
                for row in results
            ],
        )

    print(
        j(
            {
                "run_id": run_id,
                "decision": decision,
                "q16_run_id": q16_run_id,
                "snapshot_count": snapshot_count,
                "snapshot_fetch_success_count": snapshot_fetch_success_count,
                "exact_content_hit_count": exact_content_hit_count,
                "question_content_hit_count": question_content_hit_count,
                "primary_context_resolved_count": primary_context_resolved_count,
                "promoted_plaintext_gloss_count": promoted_plaintext_gloss_count,
            }
        )
    )


if __name__ == "__main__":
    main()
