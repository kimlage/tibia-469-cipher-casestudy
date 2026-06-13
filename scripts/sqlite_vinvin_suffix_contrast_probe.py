#!/usr/bin/env python3
"""Contrast VINVIN/VTLR suffix branches, especially TIFAVONAFIEI vs INEIIVNSENI."""

from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "bonelord_operational.sqlite"
PREFIX = ["V", "I", "N", "V", "I", "N", "S", "T", "A", "E", "*00", "V", "T", "L", "R20", "N", "E", "F", "I", "E", "A", "I", "F", "A", "I", "F", "A", "I", "F"]
SUFFIX_CLASSES = {
    "TIFAVONAFIEI": ["T", "I", "F", "A", "V", "O23", "N", "A", "F", "I", "E", "I"],
    "INEIIVNSENI_STAR_LEAENT": ["I", "N", "E", "I", "I", "V", "N", "S", "E", "N", "I", "*00", "L", "E", "A", "E", "N", "T"],
    "INEIIVNSENI": ["I", "N", "E", "I", "I", "V", "N", "S", "E", "N", "I"],
    "TIFA": ["T", "I", "F", "A"],
}
PRIMARY_CONTIG_EDGES = {
    "TIFAVONAFIEI": {("3", 1, "52", "62")},
    "INEIIVNSENI_STAR_LEAENT": {("2", 1, "29", "65")},
}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def jdump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS vinvin_suffix_contrast_probe_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_variant_run_id INTEGER NOT NULL,
            source_contig_overlap_run_id INTEGER NOT NULL,
            source_o23_run_id INTEGER,
            total_occurrence_count INTEGER NOT NULL,
            suffix_class_count_json TEXT NOT NULL,
            contig_supported_class_count INTEGER NOT NULL,
            o23_suffix_count INTEGER NOT NULL,
            negative_same_operator_count INTEGER NOT NULL,
            branch_score REAL NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS vinvin_suffix_contrast_items (
            run_id INTEGER NOT NULL,
            item_key TEXT NOT NULL,
            bookid TEXT NOT NULL,
            start_pos INTEGER NOT NULL,
            suffix_class TEXT NOT NULL,
            contig_support_class TEXT NOT NULL,
            left_context TEXT NOT NULL,
            operator_text TEXT NOT NULL,
            suffix_text TEXT NOT NULL,
            right_context TEXT NOT NULL,
            relation_to_o23 TEXT NOT NULL,
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


def latest_optional_id(conn: sqlite3.Connection, table: str) -> int | None:
    row = conn.execute(f"SELECT run_id FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    return int(row["run_id"]) if row else None


def find_frame(tokens: list[str], frame: list[str]) -> list[int]:
    starts = []
    size = len(frame)
    for idx in range(0, len(tokens) - size + 1):
        if tokens[idx : idx + size] == frame:
            starts.append(idx)
    return starts


def suffix_class(tokens: list[str], pos: int) -> tuple[str, list[str]]:
    for name, suffix in sorted(SUFFIX_CLASSES.items(), key=lambda item: len(item[1]), reverse=True):
        end = pos + len(suffix)
        if tokens[pos:end] == suffix:
            return name, suffix
    return "OTHER_SUFFIX", tokens[pos : min(len(tokens), pos + 12)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)

    variant_run_id = latest_id(conn, "row0_variant_frontier_runs")
    contig_run_id = latest_id(conn, "contig_max_overlap_probe_runs")
    o23_run_id = latest_optional_id(conn, "o23_onaf_hellgate_holdout_probe_runs")
    rows = conn.execute(
        """
        SELECT bookid, tokens_json
        FROM row0_variant_book_tokens
        WHERE run_id=?
        ORDER BY CAST(bookid AS INTEGER)
        """,
        (variant_run_id,),
    ).fetchall()
    contig_edges = conn.execute(
        """
        SELECT basecontigid, edge_index, left_bookid, right_bookid
        FROM contig_max_overlap_edges
        WHERE run_id=?
        """,
        (contig_run_id,),
    ).fetchall()
    edge_support = {(str(row["basecontigid"]), int(row["edge_index"]), str(row["left_bookid"]), str(row["right_bookid"])) for row in contig_edges}

    items = []
    suffix_counts: Counter[str] = Counter()
    negative_same_operator = 0
    o23_suffix_count = 0
    contig_supported_classes = set()

    for row in rows:
        bookid = str(row["bookid"])
        tokens = json.loads(row["tokens_json"] or "[]")
        starts = find_frame(tokens, PREFIX)
        for start in starts:
            suffix_pos = start + len(PREFIX)
            sclass, stokens = suffix_class(tokens, suffix_pos)
            suffix_counts[sclass] += 1
            if sclass == "TIFAVONAFIEI":
                o23_suffix_count += 1
            relation = "contains_o23_onaf_suffix" if sclass == "TIFAVONAFIEI" else "no_o23_suffix"
            support_class = "no_contig_edge_support"
            for cls, expected_edges in PRIMARY_CONTIG_EDGES.items():
                if sclass == cls and expected_edges & edge_support:
                    support_class = "primary_contig_edge_supported"
                    contig_supported_classes.add(sclass)
            items.append(
                {
                    "bookid": bookid,
                    "start_pos": start + 1,
                    "suffix_class": sclass,
                    "contig_support_class": support_class,
                    "left_context": " ".join(tokens[max(0, start - 8) : start]),
                    "operator_text": " ".join(PREFIX),
                    "suffix_text": " ".join(stokens),
                    "right_context": " ".join(tokens[suffix_pos + len(stokens) : min(len(tokens), suffix_pos + len(stokens) + 10)]),
                    "relation_to_o23": relation,
                }
            )
        neg_starts = find_frame(tokens, ["I", "F", "T", "I", "N", "S", "T", "A", "E", "*00", "V", "T", "L", "R20", "N", "E", "F", "I", "E"])
        negative_same_operator += len(neg_starts)

    branch_score = 0.0
    branch_score += min(0.35, len(contig_supported_classes) * 0.175)
    branch_score += 0.20 if suffix_counts["TIFAVONAFIEI"] >= 2 else 0.0
    branch_score += 0.15 if suffix_counts["INEIIVNSENI_STAR_LEAENT"] >= 1 else 0.0
    branch_score += 0.15 if o23_suffix_count > 0 else 0.0
    branch_score += max(0.0, 0.15 - negative_same_operator * 0.03)
    if branch_score >= 0.75:
        decision = "VINVIN_SUFFIX_BRANCHES_FUNCTION_READY"
    elif branch_score >= 0.55:
        decision = "VINVIN_SUFFIX_BRANCHES_CONTEXT_ONLY"
    else:
        decision = "VINVIN_SUFFIX_BRANCHES_AUDIT_ONLY"

    cur = conn.execute(
        """
        INSERT INTO vinvin_suffix_contrast_probe_runs
            (created_at, source_variant_run_id, source_contig_overlap_run_id,
             source_o23_run_id, total_occurrence_count, suffix_class_count_json,
             contig_supported_class_count, o23_suffix_count,
             negative_same_operator_count, branch_score, decision, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            utc_now(),
            variant_run_id,
            contig_run_id,
            o23_run_id,
            len(items),
            jdump(suffix_counts.most_common()),
            len(contig_supported_classes),
            o23_suffix_count,
            negative_same_operator,
            branch_score,
            decision,
            jdump({"contig_supported_classes": sorted(contig_supported_classes), "gloss_allowed": False}),
        ),
    )
    run_id = int(cur.lastrowid)
    for idx, item in enumerate(items, start=1):
        if item["suffix_class"] == "TIFAVONAFIEI":
            action = "test_o23_onaf_as_suffix_continuation_no_gloss"
        elif item["suffix_class"].startswith("INEIIVNSENI"):
            action = "test_inei_branch_as_alternate_continuation_no_gloss"
        else:
            action = "audit_other_suffix"
        conn.execute(
            """
            INSERT INTO vinvin_suffix_contrast_items
                (run_id, item_key, bookid, start_pos, suffix_class,
                 contig_support_class, left_context, operator_text, suffix_text,
                 right_context, relation_to_o23, next_action, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                f"{idx}:{item['bookid']}:{item['start_pos']}",
                item["bookid"],
                item["start_pos"],
                item["suffix_class"],
                item["contig_support_class"],
                item["left_context"],
                item["operator_text"],
                item["suffix_text"],
                item["right_context"],
                item["relation_to_o23"],
                action,
                "{}",
            ),
        )
    conn.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "total_occurrence_count": len(items),
                "suffix_classes": suffix_counts.most_common(),
                "contig_supported_class_count": len(contig_supported_classes),
                "o23_suffix_count": o23_suffix_count,
                "negative_same_operator_count": negative_same_operator,
                "branch_score": round(branch_score, 4),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
