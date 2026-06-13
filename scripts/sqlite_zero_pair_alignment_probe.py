#!/usr/bin/env python3
"""Pair alignment probes for zero/low functional coverage clusters, no gloss."""

from __future__ import annotations

import argparse
import difflib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "bonelord_operational.sqlite"
PAIRS = {
    "PAIR_20_54_NIIE_EIVN": ("20", "54"),
    "PAIR_60_64_R20_LIVRN": ("60", "64"),
    "PAIR_25_39_FAST_BEIE": ("25", "39"),
    "C68_8_23_CONTEXT": ("8", "23"),
}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def jdump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS zero_pair_alignment_probe_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_row0_variant_run_id INTEGER NOT NULL,
            pair_count INTEGER NOT NULL,
            ready_pair_count INTEGER NOT NULL,
            audit_pair_count INTEGER NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS zero_pair_alignment_items (
            run_id INTEGER NOT NULL,
            pair_id TEXT NOT NULL,
            left_bookid TEXT NOT NULL,
            right_bookid TEXT NOT NULL,
            left_token_count INTEGER NOT NULL,
            right_token_count INTEGER NOT NULL,
            lcs_len INTEGER NOT NULL,
            lcs_ratio_shorter REAL NOT NULL,
            lcs_ratio_longer REAL NOT NULL,
            alignment_status TEXT NOT NULL,
            next_action TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, pair_id)
        );
        """
    )


def latest_id(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT run_id FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    if row is None:
        raise SystemExit(f"missing required table data: {table}")
    return int(row["run_id"])


def lcs_blocks(a: list[str], b: list[str]) -> list[dict[str, int]]:
    matcher = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    return [{"a": m.a, "b": m.b, "size": m.size} for m in matcher.get_matching_blocks() if m.size]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db, timeout=30)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)
    row0_run_id = latest_id(conn, "row0_variant_frontier_runs")
    rows = conn.execute("SELECT bookid, tokens_json FROM row0_variant_book_tokens WHERE run_id=?", (row0_run_id,)).fetchall()
    tokens_by_book = {str(row["bookid"]): json.loads(row["tokens_json"] or "[]") for row in rows}

    cur = conn.execute(
        """
        INSERT INTO zero_pair_alignment_probe_runs
            (created_at, source_row0_variant_run_id, pair_count, ready_pair_count, audit_pair_count, decision, payload_json)
        VALUES (?, ?, ?, 0, 0, ?, ?)
        """,
        (utc_now(), row0_run_id, len(PAIRS), "PENDING", "{}"),
    )
    run_id = int(cur.lastrowid)
    ready = 0
    audit = 0
    summaries: list[dict[str, Any]] = []
    for pair_id, (left_id, right_id) in PAIRS.items():
        left = tokens_by_book[left_id]
        right = tokens_by_book[right_id]
        blocks = lcs_blocks(left, right)
        lcs_len = sum(block["size"] for block in blocks)
        shorter = min(len(left), len(right))
        longer = max(len(left), len(right))
        ratio_short = round(lcs_len / max(1, shorter), 4)
        ratio_long = round(lcs_len / max(1, longer), 4)
        long_blocks = [block for block in blocks if block["size"] >= 4]
        if pair_id == "PAIR_60_64_R20_LIVRN" and ratio_short >= 0.45:
            status = "PAIR_PHASE_ALIGNMENT_READY"
            next_action = "materialize_r20_livrn_pair_context_no_global_r"
            ready += 1
        elif pair_id == "PAIR_20_54_NIIE_EIVN" and ratio_short >= 0.50:
            status = "PAIR_TRUNCATION_ALIGNMENT_READY"
            next_action = "materialize_20_54_pair_context_no_gloss"
            ready += 1
        elif pair_id == "PAIR_25_39_FAST_BEIE" and ratio_short >= 0.50:
            status = "PAIR_MICROTEMPLATE_READY"
            next_action = "materialize_fast_beie_microtemplate_no_gloss"
            ready += 1
        elif pair_id == "C68_8_23_CONTEXT" and ratio_short >= 0.35:
            status = "PAIR_CONTEXT_ALIGNMENT"
            next_action = "keep_as_c68_context_alignment_no_global_c"
            audit += 1
        else:
            status = "PAIR_AUDIT_ONLY"
            next_action = "keep_as_similarity_control"
            audit += 1
        evidence = {
            "pair_id": pair_id,
            "left_bookid": left_id,
            "right_bookid": right_id,
            "lcs_blocks": long_blocks[:20],
            "gloss_allowed": False,
        }
        summary = {
            "pair_id": pair_id,
            "status": status,
            "lcs_len": lcs_len,
            "lcs_ratio_shorter": ratio_short,
            "lcs_ratio_longer": ratio_long,
        }
        summaries.append(summary)
        conn.execute(
            """
            INSERT INTO zero_pair_alignment_items
                (run_id, pair_id, left_bookid, right_bookid, left_token_count,
                 right_token_count, lcs_len, lcs_ratio_shorter, lcs_ratio_longer,
                 alignment_status, next_action, evidence_json, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                pair_id,
                left_id,
                right_id,
                len(left),
                len(right),
                lcs_len,
                ratio_short,
                ratio_long,
                status,
                next_action,
                jdump(evidence),
                jdump({"summary": summary, "evidence": evidence, "gloss_allowed": False}),
            ),
        )

    decision = "ZERO_PAIR_ALIGNMENTS_READY" if ready else "ZERO_PAIR_ALIGNMENTS_AUDIT_ONLY"
    conn.execute(
        """
        UPDATE zero_pair_alignment_probe_runs
        SET ready_pair_count=?, audit_pair_count=?, decision=?, payload_json=?
        WHERE run_id=?
        """,
        (ready, audit, decision, jdump({"pairs": summaries, "gloss_allowed": False}), run_id),
    )
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": decision, "ready_pair_count": ready, "audit_pair_count": audit, "pairs": summaries, "gloss_allowed": False}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
