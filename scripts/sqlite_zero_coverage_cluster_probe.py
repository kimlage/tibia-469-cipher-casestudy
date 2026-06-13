#!/usr/bin/env python3
"""Probe mechanical clusters in low/zero functional coverage books, no gloss."""

from __future__ import annotations

import argparse
import json
import sqlite3
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "bonelord_operational.sqlite"
TARGET_BOOKS = {"7", "8", "20", "23", "25", "30", "39", "49", "54", "60", "64"}
CLUSTERS = {
    "PAIR_20_54_NIIE_EIVN": {"books": {"20", "54"}, "patterns": [["N", "I", "I", "E"], ["E", "I", "V", "N"], ["T", "F", "N", "T"]]},
    "PAIR_60_64_R20_LIVRN": {"books": {"60", "64"}, "patterns": [["L", "I", "V", "R20", "N"], ["N", "I", "I", "E"], ["B", "T", "I"]]},
    "PAIR_25_39_FAST_BEIE": {"books": {"25", "39"}, "patterns": [["F", "A", "S", "T"], ["B", "E", "I", "E"], ["I", "E", "I", "E"]]},
    "C68_8_23_CONTEXT": {"books": {"8", "23"}, "patterns": [["C68", "T", "I", "I", "N"], ["E", "I", "V", "N"], ["N", "E", "E", "I"]]},
    "NEEI_RESIDUAL_CLUSTER": {"books": {"8", "20", "23", "49", "54"}, "patterns": [["N", "E", "E", "I"]]},
    "BTI_BRIDGE_CLUSTER": {"books": {"30", "39", "60", "64"}, "patterns": [["B", "T", "I"]]},
}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def jdump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS zero_coverage_cluster_probe_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_row0_variant_run_id INTEGER NOT NULL,
            cluster_count INTEGER NOT NULL,
            ready_count INTEGER NOT NULL,
            audit_count INTEGER NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS zero_coverage_cluster_items (
            run_id INTEGER NOT NULL,
            cluster_id TEXT NOT NULL,
            target_book_count INTEGER NOT NULL,
            pattern_count INTEGER NOT NULL,
            hit_count INTEGER NOT NULL,
            target_hit_book_count INTEGER NOT NULL,
            outside_hit_book_count INTEGER NOT NULL,
            exclusivity_score REAL NOT NULL,
            cluster_score REAL NOT NULL,
            cluster_status TEXT NOT NULL,
            next_action TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, cluster_id)
        );
        """
    )


def latest_id(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT run_id FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    if row is None:
        raise SystemExit(f"missing required table data: {table}")
    return int(row["run_id"])


def find_positions(tokens: list[str], pattern: list[str]) -> list[int]:
    size = len(pattern)
    return [idx for idx in range(0, len(tokens) - size + 1) if tokens[idx : idx + size] == pattern]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db, timeout=30)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)
    row0_run_id = latest_id(conn, "row0_variant_frontier_runs")
    rows = conn.execute(
        """
        SELECT bookid, tokens_json
        FROM row0_variant_book_tokens
        WHERE run_id=?
        ORDER BY CAST(bookid AS INTEGER)
        """,
        (row0_run_id,),
    ).fetchall()
    tokens_by_book = {str(row["bookid"]): json.loads(row["tokens_json"] or "[]") for row in rows}

    cur = conn.execute(
        """
        INSERT INTO zero_coverage_cluster_probe_runs
            (created_at, source_row0_variant_run_id, cluster_count, ready_count, audit_count, decision, payload_json)
        VALUES (?, ?, ?, 0, 0, ?, ?)
        """,
        (utc_now(), row0_run_id, len(CLUSTERS), "PENDING", "{}"),
    )
    run_id = int(cur.lastrowid)
    ready = 0
    audit = 0
    summaries: list[dict[str, Any]] = []
    for cluster_id, spec in CLUSTERS.items():
        target_books = set(spec["books"])
        patterns = list(spec["patterns"])
        target_hits: dict[str, list[dict[str, Any]]] = defaultdict(list)
        outside_hits: dict[str, list[dict[str, Any]]] = defaultdict(list)
        hit_count = 0
        for bookid, tokens in tokens_by_book.items():
            for pattern in patterns:
                positions = find_positions(tokens, pattern)
                if not positions:
                    continue
                hit_count += len(positions)
                hit = {"pattern": " ".join(pattern), "positions": positions}
                if bookid in target_books:
                    target_hits[bookid].append(hit)
                else:
                    outside_hits[bookid].append(hit)
        target_hit_books = set(target_hits)
        outside_hit_books = set(outside_hits)
        exclusivity = round(len(target_hit_books) / max(1, len(target_hit_books) + len(outside_hit_books)), 4)
        score = 0.0
        score += min(0.30, len(target_hit_books) * 0.08)
        score += min(0.25, hit_count * 0.025)
        score += min(0.25, len(patterns) * 0.06)
        score += min(0.20, exclusivity * 0.20)
        if cluster_id in {"PAIR_20_54_NIIE_EIVN", "PAIR_60_64_R20_LIVRN", "PAIR_25_39_FAST_BEIE"} and score >= 0.55:
            status = "PAIR_CLUSTER_READY"
            next_action = "run_pair_alignment_probe_no_gloss"
            ready += 1
        elif cluster_id == "C68_8_23_CONTEXT" and score >= 0.50:
            status = "CONTEXT_CLUSTER_READY"
            next_action = "keep_as_c68_context_probe_no_global_c68"
            ready += 1
        else:
            status = "AUDIT_OR_RESIDUAL_CLUSTER"
            next_action = "keep_as_residual_or_negative_control"
            audit += 1
        evidence = {
            "target_books": sorted(target_books, key=lambda item: int(item) if item.isdigit() else item),
            "patterns": [" ".join(pattern) for pattern in patterns],
            "target_hits": target_hits,
            "outside_hit_books": sorted(outside_hit_books, key=lambda item: int(item) if item.isdigit() else item),
            "gloss_allowed": False,
        }
        summary = {
            "cluster_id": cluster_id,
            "status": status,
            "score": round(score, 4),
            "target_hit_book_count": len(target_hit_books),
            "outside_hit_book_count": len(outside_hit_books),
            "exclusivity_score": exclusivity,
        }
        summaries.append(summary)
        conn.execute(
            """
            INSERT INTO zero_coverage_cluster_items
                (run_id, cluster_id, target_book_count, pattern_count, hit_count,
                 target_hit_book_count, outside_hit_book_count, exclusivity_score,
                 cluster_score, cluster_status, next_action, evidence_json, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                cluster_id,
                len(target_books),
                len(patterns),
                hit_count,
                len(target_hit_books),
                len(outside_hit_books),
                exclusivity,
                score,
                status,
                next_action,
                jdump(evidence),
                jdump({"gloss_allowed": False, "summary": summary, "evidence": evidence}),
            ),
        )

    decision = "ZERO_COVERAGE_CLUSTERS_READY" if ready else "ZERO_COVERAGE_CLUSTERS_AUDIT_ONLY"
    conn.execute(
        """
        UPDATE zero_coverage_cluster_probe_runs
        SET ready_count=?, audit_count=?, decision=?, payload_json=?
        WHERE run_id=?
        """,
        (ready, audit, decision, jdump({"clusters": summaries, "gloss_allowed": False}), run_id),
    )
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": decision, "ready_count": ready, "audit_count": audit, "clusters": summaries, "gloss_allowed": False}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
