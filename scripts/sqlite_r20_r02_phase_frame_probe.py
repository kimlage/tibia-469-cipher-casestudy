#!/usr/bin/env python3
"""Classify R20/R02 phase frames with contig support, without gloss."""

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
        CREATE TABLE IF NOT EXISTS r20_r02_phase_frame_probe_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_variant_frame_run_id INTEGER NOT NULL,
            source_contig_overlap_run_id INTEGER NOT NULL,
            frame_count INTEGER NOT NULL,
            promoted_count INTEGER NOT NULL,
            audit_count INTEGER NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS r20_r02_phase_frame_items (
            run_id INTEGER NOT NULL,
            frame_key TEXT NOT NULL,
            occurrence_count INTEGER NOT NULL,
            book_count INTEGER NOT NULL,
            canonical_context_count INTEGER NOT NULL,
            edge_supported_count INTEGER NOT NULL,
            phase_score REAL NOT NULL,
            phase_status TEXT NOT NULL,
            next_action TEXT NOT NULL,
            books_json TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, frame_key)
        );
        """
    )


def latest_id(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT run_id FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    if row is None:
        raise SystemExit(f"missing required table data: {table}")
    return int(row["run_id"])


def canonical_context(frame_key: str, left: str, right: str) -> bool:
    if frame_key == "R20_VTLRNEFIE_BLOCK":
        return left == "V I N S T A E *00" and right == "A I F A I F A I"
    if frame_key == "R20_VAETRFEVAST_BLOCK":
        return right == "F F F E E I N B"
    if frame_key == "R02_TRVEIIVNTBB_BRIDGE":
        return left == "N B L E I I F F" and right.startswith("N N E I T")
    if frame_key in {"R02_LIVRN_MICRO", "R20_LIVRN_MICRO"}:
        return left.endswith("E I N B L E I I") or left.endswith("I I N B L E I I")
    return False


def edge_hit(frame_key: str, overlap: str) -> bool:
    compact = overlap.replace(" ", "")
    if frame_key == "R20_VTLRNEFIE_BLOCK":
        return "VTLRNEFIE" in compact
    if frame_key == "R20_VAETRFEVAST_BLOCK":
        return "VAETRFEVAST" in compact
    if frame_key == "R02_TRVEIIVNTBB_BRIDGE":
        return "TRVEIIVNTBB" in compact
    if frame_key in {"R02_LIVRN_MICRO", "R20_LIVRN_MICRO"}:
        return "LIVRN" in compact
    return False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db, timeout=30)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)

    variant_run_id = latest_id(conn, "variant_frame_probe_runs")
    contig_run_id = latest_id(conn, "contig_max_overlap_probe_runs")
    frames = [
        "R20_VTLRNEFIE_BLOCK",
        "R20_VAETRFEVAST_BLOCK",
        "R02_TRVEIIVNTBB_BRIDGE",
        "R02_LIVRN_MICRO",
        "R20_LIVRN_MICRO",
    ]
    rows = conn.execute(
        f"""
        SELECT *
        FROM variant_frame_occurrence_items
        WHERE run_id=? AND frame_key IN ({','.join('?' for _ in frames)})
        ORDER BY frame_key, CAST(bookid AS INTEGER), start_pos
        """,
        (variant_run_id, *frames),
    ).fetchall()
    edges = conn.execute(
        """
        SELECT basecontigid, edge_index, left_bookid, right_bookid, overlap_text
        FROM contig_max_overlap_edges
        WHERE run_id=?
        """,
        (contig_run_id,),
    ).fetchall()

    edge_books_by_frame: dict[str, set[str]] = defaultdict(set)
    edge_refs_by_frame: dict[str, list[str]] = defaultdict(list)
    for frame in frames:
        for edge in edges:
            if edge_hit(frame, str(edge["overlap_text"])):
                ref = f'{edge["basecontigid"]}:{edge["edge_index"]}:{edge["left_bookid"]}->{edge["right_bookid"]}'
                edge_refs_by_frame[frame].append(ref)
                edge_books_by_frame[frame].update({str(edge["left_bookid"]), str(edge["right_bookid"])})

    grouped: dict[str, list[sqlite3.Row]] = defaultdict(list)
    for row in rows:
        grouped[row["frame_key"]].append(row)

    cur = conn.execute(
        """
        INSERT INTO r20_r02_phase_frame_probe_runs
            (created_at, source_variant_frame_run_id, source_contig_overlap_run_id,
             frame_count, promoted_count, audit_count, decision, payload_json)
        VALUES (?, ?, ?, ?, 0, 0, ?, ?)
        """,
        (utc_now(), variant_run_id, contig_run_id, len(grouped), "PENDING", "{}"),
    )
    run_id = int(cur.lastrowid)

    promoted = 0
    audit = 0
    summaries: list[dict[str, Any]] = []
    for frame, items in sorted(grouped.items()):
        books = sorted({str(row["bookid"]) for row in items}, key=lambda value: int(value) if value.isdigit() else value)
        canonical = sum(1 for row in items if canonical_context(frame, row["left_context"], row["right_context"]))
        edge_books = edge_books_by_frame.get(frame, set())
        edge_supported = sum(1 for row in items if str(row["bookid"]) in edge_books)
        score = 0.0
        score += min(0.25, len(items) * 0.035)
        score += min(0.20, len(books) * 0.025)
        score += min(0.25, canonical * 0.04)
        score += min(0.25, edge_supported * 0.08)
        if frame == "R20_VTLRNEFIE_BLOCK":
            score -= 0.20
        if frame in {"R02_LIVRN_MICRO", "R20_LIVRN_MICRO"}:
            score -= 0.15
        if frame in {"R20_VAETRFEVAST_BLOCK", "R02_TRVEIIVNTBB_BRIDGE"} and score >= 0.70:
            status = "PHASE_FRAME_READY"
            next_action = "promote_as_phase_frame_no_gloss"
            promoted += 1
        elif frame == "R20_VTLRNEFIE_BLOCK":
            status = "COVERED_BY_VINVIN_CONTEXT"
            next_action = "keep_under_vinvin_do_not_promote_separately"
            audit += 1
        else:
            status = "AUDIT_OR_MICRO_CONTEXT"
            next_action = "keep_as_context_until_more_edge_support"
            audit += 1
        evidence = {
            "frame_key": frame,
            "occurrence_count": len(items),
            "books": books,
            "canonical_context_count": canonical,
            "edge_supported_count": edge_supported,
            "edge_refs": edge_refs_by_frame.get(frame, []),
            "gloss_allowed": False,
        }
        summaries.append({"frame_key": frame, "status": status, "score": round(score, 4), **evidence})
        conn.execute(
            """
            INSERT INTO r20_r02_phase_frame_items
                (run_id, frame_key, occurrence_count, book_count,
                 canonical_context_count, edge_supported_count, phase_score,
                 phase_status, next_action, books_json, evidence_json, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                frame,
                len(items),
                len(books),
                canonical,
                edge_supported,
                score,
                status,
                next_action,
                jdump(books),
                jdump(evidence),
                jdump({"gloss_allowed": False, "evidence": evidence}),
            ),
        )

    decision = "R20_R02_PHASE_FRAMES_READY" if promoted else "R20_R02_PHASE_FRAMES_CONTEXT_ONLY"
    conn.execute(
        """
        UPDATE r20_r02_phase_frame_probe_runs
        SET promoted_count=?,
            audit_count=?,
            decision=?,
            payload_json=?
        WHERE run_id=?
        """,
        (promoted, audit, decision, jdump({"items": summaries, "gloss_allowed": False}), run_id),
    )
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": decision, "promoted_count": promoted, "audit_count": audit, "items": summaries, "gloss_allowed": False}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
