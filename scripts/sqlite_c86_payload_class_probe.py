#!/usr/bin/env python3
"""Classify C86 right-payload families without assigning plaintext."""

from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter, defaultdict
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
        CREATE TABLE IF NOT EXISTS c86_payload_class_probe_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_row0_variant_run_id INTEGER NOT NULL,
            source_contig_overlap_run_id INTEGER NOT NULL,
            occurrence_count INTEGER NOT NULL,
            book_count INTEGER NOT NULL,
            class_count INTEGER NOT NULL,
            contig_supported_count INTEGER NOT NULL,
            specificity_score REAL NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS c86_payload_class_items (
            run_id INTEGER NOT NULL,
            item_key TEXT NOT NULL,
            bookid TEXT NOT NULL,
            token_index INTEGER NOT NULL,
            left_context TEXT NOT NULL,
            right_context TEXT NOT NULL,
            payload_class TEXT NOT NULL,
            contig_support_class TEXT NOT NULL,
            branch_status TEXT NOT NULL,
            next_action TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, item_key)
        );
        """
    )


def latest_id(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT run_id FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    if row is None:
        raise SystemExit(f"missing required table data: {table}")
    return int(row["run_id"])


def classify_payload(right: list[str]) -> str:
    if right[:7] == ["E", "B", "F", "A", "I", "*00", "V"]:
        return "EBFAI_STAR_VL_PAYLOAD"
    if right[:8] == ["E", "V", "I", "E", "F", "I", "I", "N"]:
        return "EVIEFIIN_PAYLOAD"
    if right[:7] == ["E", "I", "L", "T", "A", "E", "N"]:
        return "EILTAEN_PAYLOAD"
    if right[:8] == ["E", "E", "N", "C68", "T", "I", "I", "N"]:
        return "EEN_C68_TIIN_PAYLOAD"
    if right[:8] == ["F", "F", "E", "E", "E", "F", "F", "I"]:
        return "FFEEEFFI_PAYLOAD"
    if right[:8] == ["E", "T", "I", "E", "I", "V", "I", "E"]:
        return "ETIEIVIE_PAYLOAD"
    if not right:
        return "TERMINAL_C86"
    return "OTHER_PAYLOAD"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)

    row0_run_id = latest_id(conn, "row0_variant_frontier_runs")
    contig_run_id = latest_id(conn, "contig_max_overlap_probe_runs")
    rows = conn.execute(
        """
        SELECT bookid, tokens_json
        FROM row0_variant_book_tokens
        WHERE run_id=?
        ORDER BY CAST(bookid AS INTEGER)
        """,
        (row0_run_id,),
    ).fetchall()
    edges = conn.execute(
        """
        SELECT left_bookid, right_bookid, overlap_text
        FROM contig_max_overlap_edges
        WHERE run_id=?
        """,
        (contig_run_id,),
    ).fetchall()

    edge_books_by_class: dict[str, set[str]] = defaultdict(set)
    for edge in edges:
        overlap_tokens = str(edge["overlap_text"]).split()
        for idx, token in enumerate(overlap_tokens):
            if token != "C86":
                continue
            payload_class = classify_payload(overlap_tokens[idx + 1 : idx + 9])
            edge_books_by_class[payload_class].update({str(edge["left_bookid"]), str(edge["right_bookid"])})

    cur = conn.execute(
        """
        INSERT INTO c86_payload_class_probe_runs
            (created_at, source_row0_variant_run_id, source_contig_overlap_run_id,
             occurrence_count, book_count, class_count, contig_supported_count,
             specificity_score, decision, payload_json)
        VALUES (?, ?, ?, 0, 0, 0, 0, 0, ?, ?)
        """,
        (utc_now(), row0_run_id, contig_run_id, "PENDING", "{}"),
    )
    run_id = int(cur.lastrowid)

    class_counts: Counter[str] = Counter()
    books: set[str] = set()
    supported = 0
    item_summaries: list[dict[str, Any]] = []
    for row in rows:
        bookid = str(row["bookid"])
        tokens = json.loads(row["tokens_json"] or "[]")
        for idx, token in enumerate(tokens):
            if token != "C86":
                continue
            right = tokens[idx + 1 : idx + 9]
            left = tokens[max(0, idx - 8) : idx]
            payload_class = classify_payload(right)
            class_counts[payload_class] += 1
            books.add(bookid)
            has_edge = bookid in edge_books_by_class.get(payload_class, set())
            if has_edge:
                supported += 1
            if payload_class in {"EBFAI_STAR_VL_PAYLOAD", "EVIEFIIN_PAYLOAD"} and has_edge:
                status = "PAYLOAD_CLASS_READY"
                next_action = "contrast_payload_family_before_subfunction_promotion"
            elif payload_class == "TERMINAL_C86":
                status = "AUDIT_TERMINAL"
                next_action = "keep_as_terminal_negative"
            else:
                status = "CONTEXT_PAYLOAD_CLASS"
                next_action = "keep_as_payload_context"
            payload = {
                "bookid": bookid,
                "token_index": idx,
                "payload_class": payload_class,
                "edge_supported": has_edge,
                "gloss_allowed": False,
            }
            item_summaries.append(payload)
            conn.execute(
                """
                INSERT INTO c86_payload_class_items
                    (run_id, item_key, bookid, token_index, left_context, right_context,
                     payload_class, contig_support_class, branch_status, next_action, payload_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    f"{bookid}:{idx}",
                    bookid,
                    idx,
                    " ".join(left),
                    " ".join(right),
                    payload_class,
                    "CONTIG_EDGE_CLASS_SUPPORT" if has_edge else "NO_DIRECT_CONTIG_EDGE_CLASS_SUPPORT",
                    status,
                    next_action,
                    jdump(payload),
                ),
            )

    dominant = class_counts.most_common()
    ready_classes = sum(1 for cls, count in class_counts.items() if count >= 3 and edge_books_by_class.get(cls))
    specificity_score = round(min(0.45, len(books) * 0.02) + min(0.35, ready_classes * 0.15) + min(0.20, supported * 0.03), 4)
    decision = "C86_PAYLOAD_CLASSES_READY_FOR_CONTRAST" if specificity_score >= 0.70 and ready_classes >= 2 else "C86_PAYLOAD_CLASSES_CONTEXT_ONLY"
    payload = {
        "class_counts": dominant,
        "edge_books_by_class": {key: sorted(value, key=lambda item: int(item) if item.isdigit() else item) for key, value in edge_books_by_class.items()},
        "items": item_summaries,
        "gloss_allowed": False,
    }
    conn.execute(
        """
        UPDATE c86_payload_class_probe_runs
        SET occurrence_count=?,
            book_count=?,
            class_count=?,
            contig_supported_count=?,
            specificity_score=?,
            decision=?,
            payload_json=?
        WHERE run_id=?
        """,
        (sum(class_counts.values()), len(books), len(class_counts), supported, specificity_score, decision, jdump(payload), run_id),
    )
    conn.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "occurrence_count": sum(class_counts.values()),
                "book_count": len(books),
                "class_count": len(class_counts),
                "contig_supported_count": supported,
                "specificity_score": specificity_score,
                "class_counts": dominant,
                "gloss_allowed": False,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
