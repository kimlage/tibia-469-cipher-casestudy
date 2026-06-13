#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sqlite3
from datetime import UTC, datetime
from typing import Any, Dict, List

from sqlite_snapshot_ref import DEFAULT_SNAPSHOT_NAME, resolve_export_id


DEFAULT_DB = "./data/bonelord_operational.sqlite"

DEFAULT_ANCHORS = [
    {
        "anchor_id": "evil_eye_653768764",
        "digits": "653768764",
        "expected_core": "look at you",
        "expected_full": "Let me take a look at you",
        "source_label": "TibiaWiki The Evil Eye + local old_attempts source_content",
        "source_url": "https://tibia.fandom.com/wiki/The_Evil_Eye",
        "strength": "HARD_EXTERNAL_PHRASE",
    },
    {
        "anchor_id": "elder_65997854764",
        "digits": "65997854764",
        "expected_core": "let me see you",
        "expected_full": "let me see you",
        "source_label": "local old_attempts source_content/books_frequency_translated",
        "source_url": "archive/old_attempts_2024/source_content.md",
        "strength": "SOFT_LEGACY_PHRASE",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit known external phrase anchors against current ExternalRefs decoding")
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--export-id", type=int, default=None)
    parser.add_argument("--snapshot-name", default=DEFAULT_SNAPSHOT_NAME)
    parser.add_argument("--record", action="store_true")
    return parser.parse_args()


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def words(text: object) -> set[str]:
    stop = {"a", "an", "at", "me", "the", "to"}
    raw = re.findall(r"[a-z]+", str(text or "").lower())
    norm = []
    for word in raw:
        if word == "youve":
            word = "you"
        if word == "you":
            norm.append(word)
        elif word not in stop:
            norm.append(word)
    return set(norm)


def score_overlap(expected: str, observed: str) -> Dict[str, Any]:
    expected_words = words(expected)
    observed_words = words(observed)
    overlap = sorted(expected_words & observed_words)
    missing = sorted(expected_words - observed_words)
    extra = sorted(observed_words - expected_words)
    score = round(100.0 * len(overlap) / len(expected_words), 2) if expected_words else 0.0
    return {
        "score_pct": score,
        "expected_words": sorted(expected_words),
        "observed_words": sorted(observed_words),
        "overlap": overlap,
        "missing": missing,
        "extra": extra,
    }


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS external_phrase_anchor_audit_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            export_id INTEGER NOT NULL,
            anchor_count INTEGER NOT NULL,
            mismatch_count INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS external_phrase_anchor_audit (
            run_id INTEGER NOT NULL,
            anchor_id TEXT NOT NULL,
            digits TEXT NOT NULL,
            refname TEXT,
            expected_core TEXT NOT NULL,
            observed_dp TEXT,
            observed_codestream TEXT,
            best_score_pct REAL NOT NULL,
            status TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, anchor_id)
        );
        """
    )


def audit_anchor(conn: sqlite3.Connection, export_id: int, anchor: Dict[str, str]) -> Dict[str, Any]:
    row = conn.execute(
        """
        SELECT
            refname,
            type,
            source,
            numerictext,
            digitssanitized,
            decodedbase,
            dp_strictplus,
            codestreambase_v120,
            codestreamdp_concat_readable_v120
        FROM sheet__externalrefs_v115
        WHERE __export_id = ?
          AND digitssanitized = ?
        LIMIT 1
        """,
        (export_id, anchor["digits"]),
    ).fetchone()
    if row is None:
        return {
            **anchor,
            "status": "MISSING_REF",
            "best_score_pct": 0.0,
            "row": None,
            "dp_overlap": score_overlap(anchor["expected_core"], ""),
            "codestream_overlap": score_overlap(anchor["expected_core"], ""),
        }
    row_d = dict(row)
    dp_overlap = score_overlap(anchor["expected_core"], row_d.get("dp_strictplus"))
    cs_overlap = score_overlap(anchor["expected_core"], row_d.get("codestreamdp_concat_readable_v120"))
    best = max(dp_overlap["score_pct"], cs_overlap["score_pct"])
    status = "PASS" if best >= 75.0 else "MISMATCH"
    return {
        **anchor,
        "status": status,
        "best_score_pct": best,
        "row": row_d,
        "dp_overlap": dp_overlap,
        "codestream_overlap": cs_overlap,
    }


def record(conn: sqlite3.Connection, export_id: int, items: List[Dict[str, Any]]) -> int:
    ensure_schema(conn)
    created_at = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    mismatch_count = sum(1 for item in items if item["status"] != "PASS")
    cur = conn.execute(
        """
        INSERT INTO external_phrase_anchor_audit_runs (created_at, export_id, anchor_count, mismatch_count)
        VALUES (?, ?, ?, ?)
        """,
        (created_at, export_id, len(items), mismatch_count),
    )
    run_id = int(cur.lastrowid)
    for item in items:
        row = item.get("row") or {}
        conn.execute(
            """
            INSERT INTO external_phrase_anchor_audit (
                run_id, anchor_id, digits, refname, expected_core,
                observed_dp, observed_codestream, best_score_pct, status, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                item["anchor_id"],
                item["digits"],
                row.get("refname"),
                item["expected_core"],
                row.get("dp_strictplus"),
                row.get("codestreamdp_concat_readable_v120"),
                item["best_score_pct"],
                item["status"],
                json.dumps(item, ensure_ascii=True, sort_keys=True),
            ),
        )
    conn.commit()
    return run_id


def main() -> int:
    args = parse_args()
    conn = connect(args.db)
    try:
        export_id = resolve_export_id(conn, export_id=args.export_id, snapshot_name=args.snapshot_name)
        items = [audit_anchor(conn, export_id, anchor) for anchor in DEFAULT_ANCHORS]
        run_id = record(conn, export_id, items) if args.record else None
    finally:
        conn.close()
    print(
        json.dumps(
            {
                "export_id": export_id,
                "recorded_run_id": run_id,
                "anchor_count": len(items),
                "mismatch_count": sum(1 for item in items if item["status"] != "PASS"),
                "anchors": items,
            },
            ensure_ascii=True,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
