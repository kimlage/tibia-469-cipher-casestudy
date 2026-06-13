#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


DB_PATH = Path(__file__).resolve().parents[1] / "data" / "bonelord_operational.sqlite"


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS semantic_actionable_frontier_runs (
          run_id INTEGER PRIMARY KEY AUTOINCREMENT,
          created_at TEXT NOT NULL,
          source_anomaly_run_id INTEGER NOT NULL,
          source TEXT NOT NULL,
          actionable_count INTEGER NOT NULL,
          excluded_known_count INTEGER NOT NULL,
          excluded_blocked_count INTEGER NOT NULL DEFAULT 0,
          top_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS semantic_actionable_frontier_items (
          run_id INTEGER NOT NULL,
          action_rank INTEGER NOT NULL,
          source_rank INTEGER NOT NULL,
          phrase TEXT NOT NULL,
          hit_count INTEGER NOT NULL,
          book_count INTEGER NOT NULL,
          score INTEGER NOT NULL,
          recommendation TEXT NOT NULL,
          action_class TEXT NOT NULL,
          reason TEXT NOT NULL,
          payload_json TEXT NOT NULL,
          PRIMARY KEY (run_id, action_rank)
        );
        """
    )
    cols = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(semantic_actionable_frontier_runs)")
    }
    if "excluded_blocked_count" not in cols:
        conn.execute(
            "ALTER TABLE semantic_actionable_frontier_runs "
            "ADD COLUMN excluded_blocked_count INTEGER NOT NULL DEFAULT 0"
        )


def latest_anomaly_run(conn: sqlite3.Connection, source: str) -> sqlite3.Row:
    row = conn.execute(
        """
        SELECT run_id, source
        FROM semantic_anomaly_audit_runs
        WHERE source=?
        ORDER BY run_id DESC
        LIMIT 1
        """,
        (source,),
    ).fetchone()
    if not row:
        raise SystemExit(f"no semantic anomaly run found for source={source!r}")
    return row


def known_slot_markers(conn: sqlite3.Connection) -> list[str]:
    try:
        rows = conn.execute(
            "SELECT slot FROM semantic_known_unresolved_slots WHERE status LIKE 'KNOWN_%'"
        ).fetchall()
    except sqlite3.OperationalError:
        return []
    markers: list[str] = []
    for row in rows:
        slot = str(row["slot"])
        lowered = slot.lower()
        markers.extend([lowered, f"<unk:{lowered}>", f"<suspect:{lowered}>"])
    return sorted(set(markers), key=len, reverse=True)


def blocked_phrase_markers(conn: sqlite3.Connection) -> list[str]:
    try:
        rows = conn.execute("SELECT phrase FROM semantic_blocked_phrases").fetchall()
    except sqlite3.OperationalError:
        return []
    return sorted({str(row["phrase"]).lower() for row in rows}, key=len, reverse=True)


def classify(row: sqlite3.Row, markers: list[str], blocked: list[str]) -> tuple[str, str]:
    phrase = str(row["phrase"]).lower()
    if any(marker in phrase for marker in markers):
        return (
            "KNOWN_UNRESOLVED_SLOT",
            "Known structural unknown; keep visible but do not let it monopolize actionable semantic frontier.",
        )
    if any(marker in phrase for marker in blocked):
        return (
            "BLOCKED_OR_AUDIT_ONLY_BY_DECISION",
            "Already reviewed; blocked from hard promotion or limited to display/audit layer.",
        )
    recommendation = str(row["recommendation"])
    if recommendation in {"CONTRADICTION_REDUCTION_REVIEW", "SEGMENTATION_OR_STOPWORD_DRIFT_REVIEW"}:
        return ("ACTIONABLE_SEMANTIC_CONTRADICTION", "Direct contradiction/segmentation target.")
    if recommendation == "AUDIT_REPEATED_END_FORMULA":
        return ("ACTIONABLE_FORMULA_AUDIT", "Repeated formula not explained by known unresolved slot.")
    if recommendation == "LOW_PRIORITY":
        return ("LOW_PRIORITY_ACTIONABLE", "Actionable only after stronger contradiction targets.")
    return ("ACTIONABLE_REVIEW", "Not blocked by known unresolved slot.")


def build_frontier(conn: sqlite3.Connection, source: str, limit: int) -> dict[str, object]:
    run = latest_anomaly_run(conn, source)
    markers = known_slot_markers(conn)
    blocked = blocked_phrase_markers(conn)
    rows = conn.execute(
        """
        SELECT rank, phrase, hit_count, book_count, score, recommendation, payload_json
        FROM semantic_anomaly_audit_items
        WHERE run_id=?
        ORDER BY rank
        """,
        (int(run["run_id"]),),
    ).fetchall()

    actionable: list[dict[str, object]] = []
    excluded_known = 0
    excluded_blocked = 0
    for row in rows:
        action_class, reason = classify(row, markers, blocked)
        if action_class == "KNOWN_UNRESOLVED_SLOT":
            excluded_known += 1
            continue
        if action_class == "BLOCKED_OR_AUDIT_ONLY_BY_DECISION":
            excluded_blocked += 1
            continue
        actionable.append(
            {
                "source_rank": int(row["rank"]),
                "phrase": row["phrase"],
                "hit_count": int(row["hit_count"]),
                "book_count": int(row["book_count"]),
                "score": int(row["score"]),
                "recommendation": row["recommendation"],
                "action_class": action_class,
                "reason": reason,
                "payload_json": row["payload_json"],
            }
        )

    return {
        "source": source,
        "source_anomaly_run_id": int(run["run_id"]),
        "known_slot_markers": markers,
        "blocked_phrase_markers": blocked,
        "actionable_count": len(actionable),
        "excluded_known_count": excluded_known,
        "excluded_blocked_count": excluded_blocked,
        "top": actionable[:limit],
    }


def record(conn: sqlite3.Connection, result: dict[str, object]) -> int:
    ensure_schema(conn)
    top = list(result["top"])
    cur = conn.execute(
        """
        INSERT INTO semantic_actionable_frontier_runs (
          created_at, source_anomaly_run_id, source, actionable_count,
          excluded_known_count, excluded_blocked_count, top_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            now(),
            int(result["source_anomaly_run_id"]),
            str(result["source"]),
            int(result["actionable_count"]),
            int(result["excluded_known_count"]),
            int(result["excluded_blocked_count"]),
            json.dumps(top, ensure_ascii=True, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)
    for idx, item in enumerate(top, start=1):
        conn.execute(
            """
            INSERT INTO semantic_actionable_frontier_items (
              run_id, action_rank, source_rank, phrase, hit_count, book_count, score,
              recommendation, action_class, reason, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                idx,
                int(item["source_rank"]),
                str(item["phrase"]),
                int(item["hit_count"]),
                int(item["book_count"]),
                int(item["score"]),
                str(item["recommendation"]),
                str(item["action_class"]),
                str(item["reason"]),
                str(item["payload_json"]),
            ),
        )
    conn.commit()
    return run_id


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DB_PATH)
    parser.add_argument("--source", default="microtoken_neutral")
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--record", action="store_true")
    args = parser.parse_args()

    with connect(args.db) as conn:
        result = build_frontier(conn, args.source, args.limit)
        if args.record:
            result["recorded_run_id"] = record(conn, result)
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
