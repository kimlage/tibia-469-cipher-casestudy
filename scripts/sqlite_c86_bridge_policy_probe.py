#!/usr/bin/env python3
"""Score C86 payload branches as bridges to downstream row0 frames, no gloss."""

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


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def jdump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS c86_bridge_policy_probe_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_c86_refined_run_id INTEGER NOT NULL,
            branch_count INTEGER NOT NULL,
            promoted_branch_count INTEGER NOT NULL,
            audit_branch_count INTEGER NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS c86_bridge_policy_items (
            run_id INTEGER NOT NULL,
            branch_id TEXT NOT NULL,
            payload_class TEXT NOT NULL,
            occurrence_count INTEGER NOT NULL,
            book_count INTEGER NOT NULL,
            edge_supported_occurrence_count INTEGER NOT NULL,
            edge_ref_count INTEGER NOT NULL,
            downstream_frame TEXT NOT NULL,
            bridge_score REAL NOT NULL,
            branch_status TEXT NOT NULL,
            next_action TEXT NOT NULL,
            books_json TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, branch_id)
        );
        """
    )


def latest_id(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT run_id FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    if row is None:
        raise SystemExit(f"missing required table data: {table}")
    return int(row["run_id"])


def branch_id(payload_class: str) -> str:
    if payload_class == "EVIEFIIN_TO_VN_C68_TIIN_PAYLOAD":
        return "C86_BRANCH_EVIEFIIN_TO_VN_C68_TIIN"
    if payload_class == "EBFAI_STAR_VL_TO_VINVIN_PAYLOAD":
        return "C86_BRANCH_EBFAI_STAR_VL_TO_VINVIN"
    return f"C86_BRANCH_{payload_class}"


def downstream(payload_class: str) -> str:
    if payload_class == "EVIEFIIN_TO_VN_C68_TIIN_PAYLOAD":
        return "FRAME_C68_VNCTIIN_FAMILY"
    if payload_class == "EBFAI_STAR_VL_TO_VINVIN_PAYLOAD":
        return "VINVIN_VTLR"
    if "C68" in payload_class:
        return "FRAME_C68_CONTEXT"
    return "UNKNOWN_OR_LOCAL_PAYLOAD"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)

    source_run_id = latest_id(conn, "c86_contig_refined_probe_runs")
    rows = conn.execute(
        """
        SELECT *
        FROM c86_contig_refined_items
        WHERE run_id=?
        ORDER BY payload_class, CAST(bookid AS INTEGER), token_index
        """,
        (source_run_id,),
    ).fetchall()

    grouped: dict[str, list[sqlite3.Row]] = defaultdict(list)
    for row in rows:
        grouped[row["payload_class"]].append(row)

    cur = conn.execute(
        """
        INSERT INTO c86_bridge_policy_probe_runs
            (created_at, source_c86_refined_run_id, branch_count,
             promoted_branch_count, audit_branch_count, decision, payload_json)
        VALUES (?, ?, ?, 0, 0, ?, ?)
        """,
        (utc_now(), source_run_id, len(grouped), "PENDING", "{}"),
    )
    run_id = int(cur.lastrowid)

    promoted = 0
    audit = 0
    summaries: list[dict[str, Any]] = []
    for payload_class, items in sorted(grouped.items()):
        books = sorted({str(row["bookid"]) for row in items}, key=lambda value: int(value) if value.isdigit() else value)
        edge_items = [row for row in items if row["edge_support"] == "EDGE_SUPPORTED"]
        edge_refs = sorted({ref for row in edge_items for ref in str(row["edge_refs"]).split(",") if ref})
        target = downstream(payload_class)
        score = 0.0
        score += min(0.25, len(items) * 0.05)
        score += min(0.20, len(books) * 0.04)
        score += min(0.25, len(edge_items) * 0.08)
        score += min(0.20, len(edge_refs) * 0.10)
        score += 0.10 if target in {"FRAME_C68_VNCTIIN_FAMILY", "VINVIN_VTLR"} else 0.0
        if payload_class in {"EVIEFIIN_TO_VN_C68_TIIN_PAYLOAD", "EBFAI_STAR_VL_TO_VINVIN_PAYLOAD"} and score >= 0.70:
            status = "BRIDGE_SUBFUNCTION_READY"
            next_action = "materialize_bridge_subfunction_no_gloss"
            promoted += 1
        elif edge_items:
            status = "EDGE_SUPPORTED_CONTEXT"
            next_action = "keep_as_context_until_more_edges"
            audit += 1
        else:
            status = "AUDIT_OR_SURFACE_PAYLOAD"
            next_action = "do_not_promote_without_edge_support"
            audit += 1
        evidence = {
            "payload_class": payload_class,
            "occurrence_count": len(items),
            "books": books,
            "edge_supported_occurrence_count": len(edge_items),
            "edge_refs": edge_refs,
            "downstream_frame": target,
            "gloss_allowed": False,
        }
        summaries.append({"branch_id": branch_id(payload_class), "status": status, "score": round(score, 4), **evidence})
        conn.execute(
            """
            INSERT INTO c86_bridge_policy_items
                (run_id, branch_id, payload_class, occurrence_count, book_count,
                 edge_supported_occurrence_count, edge_ref_count, downstream_frame,
                 bridge_score, branch_status, next_action, books_json,
                 evidence_json, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                branch_id(payload_class),
                payload_class,
                len(items),
                len(books),
                len(edge_items),
                len(edge_refs),
                target,
                score,
                status,
                next_action,
                jdump(books),
                jdump(evidence),
                jdump({"gloss_allowed": False, "evidence": evidence}),
            ),
        )

    decision = "C86_BRIDGE_SUBFUNCTIONS_READY" if promoted >= 2 else "C86_BRIDGE_SUBFUNCTIONS_PARTIAL"
    conn.execute(
        """
        UPDATE c86_bridge_policy_probe_runs
        SET promoted_branch_count=?,
            audit_branch_count=?,
            decision=?,
            payload_json=?
        WHERE run_id=?
        """,
        (promoted, audit, decision, jdump({"items": summaries, "gloss_allowed": False}), run_id),
    )
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": decision, "promoted_branch_count": promoted, "audit_branch_count": audit, "items": summaries, "gloss_allowed": False}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
