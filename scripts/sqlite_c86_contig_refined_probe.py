#!/usr/bin/env python3
"""Refine C86 payload evidence using tokenized books on validated contig edges."""

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
        CREATE TABLE IF NOT EXISTS c86_contig_refined_probe_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_row0_variant_run_id INTEGER NOT NULL,
            source_contig_overlap_run_id INTEGER NOT NULL,
            c86_occurrence_count INTEGER NOT NULL,
            c86_book_count INTEGER NOT NULL,
            edge_supported_occurrence_count INTEGER NOT NULL,
            edge_supported_class_count INTEGER NOT NULL,
            refined_score REAL NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS c86_contig_refined_items (
            run_id INTEGER NOT NULL,
            item_key TEXT NOT NULL,
            bookid TEXT NOT NULL,
            token_index INTEGER NOT NULL,
            payload_class TEXT NOT NULL,
            edge_support TEXT NOT NULL,
            edge_refs TEXT NOT NULL,
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


def classify_payload(tokens: list[str], idx: int) -> str:
    right = tokens[idx + 1 : idx + 30]
    if right[:7] == ["E", "B", "F", "A", "I", "*00", "V"] and "VINVIN" in "".join(right):
        return "EBFAI_STAR_VL_TO_VINVIN_PAYLOAD"
    if right[:7] == ["E", "B", "F", "A", "I", "*00", "V"]:
        return "EBFAI_STAR_VL_PAYLOAD"
    if right[:8] == ["E", "V", "I", "E", "F", "I", "I", "N"] and "C68" in right[:20]:
        return "EVIEFIIN_TO_VN_C68_TIIN_PAYLOAD"
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
    book_rows = conn.execute(
        """
        SELECT bookid, tokens_json
        FROM row0_variant_book_tokens
        WHERE run_id=?
        ORDER BY CAST(bookid AS INTEGER)
        """,
        (row0_run_id,),
    ).fetchall()
    edge_rows = conn.execute(
        """
        SELECT basecontigid, edge_index, left_bookid, right_bookid
        FROM contig_max_overlap_edges
        WHERE run_id=?
        ORDER BY basecontigid, edge_index
        """,
        (contig_run_id,),
    ).fetchall()

    tokens_by_book = {str(row["bookid"]): json.loads(row["tokens_json"] or "[]") for row in book_rows}
    edge_refs_by_book: dict[str, list[str]] = defaultdict(list)
    edge_pairs = []
    for edge in edge_rows:
        left = str(edge["left_bookid"])
        right = str(edge["right_bookid"])
        ref = f'{edge["basecontigid"]}:{edge["edge_index"]}:{left}->{right}'
        edge_refs_by_book[left].append(ref)
        edge_refs_by_book[right].append(ref)
        edge_pairs.append((ref, left, right))

    pair_classes: dict[str, set[str]] = defaultdict(set)
    for ref, left, right in edge_pairs:
        for bookid in (left, right):
            tokens = tokens_by_book.get(bookid, [])
            for idx, token in enumerate(tokens):
                if token == "C86":
                    pair_classes[ref].add(classify_payload(tokens, idx))

    supported_classes_by_ref = {ref: classes for ref, classes in pair_classes.items() if len(classes) >= 1}
    class_edge_refs: dict[str, set[str]] = defaultdict(set)
    for ref, classes in supported_classes_by_ref.items():
        for cls in classes:
            class_edge_refs[cls].add(ref)

    cur = conn.execute(
        """
        INSERT INTO c86_contig_refined_probe_runs
            (created_at, source_row0_variant_run_id, source_contig_overlap_run_id,
             c86_occurrence_count, c86_book_count, edge_supported_occurrence_count,
             edge_supported_class_count, refined_score, decision, payload_json)
        VALUES (?, ?, ?, 0, 0, 0, 0, 0, ?, ?)
        """,
        (utc_now(), row0_run_id, contig_run_id, "PENDING", "{}"),
    )
    run_id = int(cur.lastrowid)

    c86_books: set[str] = set()
    class_counts: Counter[str] = Counter()
    edge_supported_occurrences = 0
    items: list[dict[str, Any]] = []
    for bookid, tokens in tokens_by_book.items():
        for idx, token in enumerate(tokens):
            if token != "C86":
                continue
            cls = classify_payload(tokens, idx)
            class_counts[cls] += 1
            c86_books.add(bookid)
            refs = [ref for ref in edge_refs_by_book.get(bookid, []) if cls in pair_classes.get(ref, set())]
            edge_supported = bool(refs)
            if edge_supported:
                edge_supported_occurrences += 1
            if cls in {"EVIEFIIN_TO_VN_C68_TIIN_PAYLOAD", "EBFAI_STAR_VL_TO_VINVIN_PAYLOAD"} and edge_supported:
                status = "PAYLOAD_BRANCH_READY"
                next_action = "promote_as_c86_payload_subbranch_no_gloss_after_policy_step"
            elif edge_supported:
                status = "EDGE_SUPPORTED_CONTEXT"
                next_action = "keep_as_context_payload"
            else:
                status = "UNSUPPORTED_CONTEXT"
                next_action = "keep_as_negative_or_surface_context"
            payload = {
                "bookid": bookid,
                "token_index": idx,
                "payload_class": cls,
                "edge_refs": refs,
                "gloss_allowed": False,
            }
            items.append(payload)
            conn.execute(
                """
                INSERT INTO c86_contig_refined_items
                    (run_id, item_key, bookid, token_index, payload_class,
                     edge_support, edge_refs, branch_status, next_action, payload_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    f"{bookid}:{idx}",
                    bookid,
                    idx,
                    cls,
                    "EDGE_SUPPORTED" if edge_supported else "NO_EDGE_SUPPORT",
                    ",".join(refs),
                    status,
                    next_action,
                    jdump(payload),
                ),
            )

    edge_supported_class_count = sum(1 for cls, refs in class_edge_refs.items() if refs)
    ready_class_count = sum(1 for cls in {"EVIEFIIN_TO_VN_C68_TIIN_PAYLOAD", "EBFAI_STAR_VL_TO_VINVIN_PAYLOAD"} if class_edge_refs.get(cls))
    refined_score = round(
        min(0.25, len(c86_books) * 0.015)
        + min(0.25, edge_supported_occurrences * 0.04)
        + min(0.30, ready_class_count * 0.15)
        + min(0.20, edge_supported_class_count * 0.04),
        4,
    )
    decision = "C86_OPERATOR_PAYLOAD_BRANCHES_READY_NO_GLOSS" if refined_score >= 0.70 and ready_class_count >= 2 else "C86_OPERATOR_PAYLOAD_PARTIAL_CONTEXT"
    payload = {
        "class_counts": class_counts.most_common(),
        "class_edge_refs": {key: sorted(value) for key, value in class_edge_refs.items()},
        "items": items,
        "gloss_allowed": False,
    }
    conn.execute(
        """
        UPDATE c86_contig_refined_probe_runs
        SET c86_occurrence_count=?,
            c86_book_count=?,
            edge_supported_occurrence_count=?,
            edge_supported_class_count=?,
            refined_score=?,
            decision=?,
            payload_json=?
        WHERE run_id=?
        """,
        (
            sum(class_counts.values()),
            len(c86_books),
            edge_supported_occurrences,
            edge_supported_class_count,
            refined_score,
            decision,
            jdump(payload),
            run_id,
        ),
    )
    conn.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "refined_score": refined_score,
                "c86_occurrence_count": sum(class_counts.values()),
                "c86_book_count": len(c86_books),
                "edge_supported_occurrence_count": edge_supported_occurrences,
                "edge_supported_class_count": edge_supported_class_count,
                "class_counts": class_counts.most_common(),
                "gloss_allowed": False,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
