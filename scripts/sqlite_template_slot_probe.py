#!/usr/bin/env python3
"""Register and align priority row0 template families."""

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

FAMILIES = [
    {
        "family_key": "STAR_CROSSING_ENIIFINI_LTASTTN",
        "anchor": "ENIIFINI*LTASTTN",
        "core": "BASTFNENIIFINI*LTASTTN",
        "classification": "star_crossing_formula",
        "next_test": "align_tail_variants_after_LTASTTN",
    },
    {
        "family_key": "BENNA_FORMULA",
        "anchor": "BENNA",
        "core": "BENNA",
        "classification": "distributed_template_anchor",
        "next_test": "prefix_suffix_concordance",
    },
    {
        "family_key": "NAESE_IVIFAST_TEMPLATE",
        "anchor": "IVIFASTFNEIEINTA",
        "core": "NAESESTIENFATCTIVVTISETEIVIFASTFNEIEINTA",
        "classification": "distributed_template",
        "next_test": "align_prefix_suffix_variants",
    },
    {
        "family_key": "LTAST_TAIL",
        "anchor": "LTASTTN",
        "core": "LTASTTN",
        "classification": "boundary_tail_template",
        "next_test": "classify_tail_variants",
    },
]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def jdump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS template_slot_probe_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_code_symbol_run_id INTEGER NOT NULL,
            source_bpe_run_id INTEGER,
            family_count INTEGER NOT NULL,
            occurrence_count INTEGER NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS template_slot_family_items (
            run_id INTEGER NOT NULL,
            family_key TEXT NOT NULL,
            anchor TEXT NOT NULL,
            core TEXT NOT NULL,
            classification TEXT NOT NULL,
            occurrence_count INTEGER NOT NULL,
            book_count INTEGER NOT NULL,
            position_classes_json TEXT NOT NULL,
            prefix_variants_json TEXT NOT NULL,
            suffix_variants_json TEXT NOT NULL,
            next_test TEXT NOT NULL,
            PRIMARY KEY (run_id, family_key)
        );

        CREATE TABLE IF NOT EXISTS template_slot_occurrence_items (
            run_id INTEGER NOT NULL,
            family_key TEXT NOT NULL,
            bookid TEXT NOT NULL,
            occurrence_index INTEGER NOT NULL,
            start_pos INTEGER NOT NULL,
            position_class TEXT NOT NULL,
            left_context TEXT NOT NULL,
            anchor_text TEXT NOT NULL,
            right_context TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, family_key, bookid, occurrence_index)
        );
        """
    )


def one(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> sqlite3.Row:
    row = conn.execute(sql, params).fetchone()
    if row is None:
        raise SystemExit(f"missing required row for query: {sql}")
    return row


def position_class(text: str, start: int, end: int) -> str:
    if "*" not in text:
        return "whole_book_no_star"
    before = text.rfind("*", 0, start)
    after = text.find("*", end)
    if before < 0:
        return "before_first_star"
    if after < 0:
        return "after_last_star"
    return "between_stars"


def find_all(text: str, needle: str) -> list[int]:
    starts = []
    idx = 0
    while True:
        pos = text.find(needle, idx)
        if pos < 0:
            break
        starts.append(pos)
        idx = pos + 1
    return starts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)

    source = one(conn, "SELECT * FROM row0_code_symbol_probe_runs ORDER BY run_id DESC LIMIT 1")
    bpe = conn.execute("SELECT * FROM internal_bpe_mdl_runs ORDER BY run_id DESC LIMIT 1").fetchone()
    books = conn.execute(
        """
        SELECT bookid, decodedbase
        FROM row0_code_symbol_probe_books
        WHERE run_id=? AND valid=1
        ORDER BY CAST(bookid AS INTEGER)
        """,
        (source["run_id"],),
    ).fetchall()

    cur = conn.execute(
        """
        INSERT INTO template_slot_probe_runs
            (created_at, source_code_symbol_run_id, source_bpe_run_id,
             family_count, occurrence_count, decision, payload_json)
        VALUES (?, ?, ?, ?, 0, ?, ?)
        """,
        (
            utc_now(),
            source["run_id"],
            bpe["run_id"] if bpe else None,
            len(FAMILIES),
            "PENDING",
            "{}",
        ),
    )
    run_id = int(cur.lastrowid)
    total_occ = 0

    for fam in FAMILIES:
        occurrences = []
        pos_classes = Counter()
        prefix_variants = Counter()
        suffix_variants = Counter()
        bookids = set()
        for row in books:
            text = row["decodedbase"] or ""
            for occ_idx, start in enumerate(find_all(text, fam["anchor"]), start=1):
                end = start + len(fam["anchor"])
                pclass = position_class(text, start, end)
                left = text[max(0, start - 40) : start]
                right = text[end : min(len(text), end + 40)]
                prefix = left[-12:]
                suffix = right[:12]
                pos_classes[pclass] += 1
                prefix_variants[prefix] += 1
                suffix_variants[suffix] += 1
                bookids.add(str(row["bookid"]))
                occurrences.append(
                    {
                        "bookid": str(row["bookid"]),
                        "occurrence_index": occ_idx,
                        "start_pos": start + 1,
                        "position_class": pclass,
                        "left_context": left,
                        "right_context": right,
                    }
                )
        for occ in occurrences:
            conn.execute(
                """
                INSERT INTO template_slot_occurrence_items
                    (run_id, family_key, bookid, occurrence_index, start_pos,
                     position_class, left_context, anchor_text, right_context, payload_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    fam["family_key"],
                    occ["bookid"],
                    occ["occurrence_index"],
                    occ["start_pos"],
                    occ["position_class"],
                    occ["left_context"],
                    fam["anchor"],
                    occ["right_context"],
                    "{}",
                ),
            )
        conn.execute(
            """
            INSERT INTO template_slot_family_items
                (run_id, family_key, anchor, core, classification,
                 occurrence_count, book_count, position_classes_json,
                 prefix_variants_json, suffix_variants_json, next_test)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                fam["family_key"],
                fam["anchor"],
                fam["core"],
                fam["classification"],
                len(occurrences),
                len(bookids),
                jdump(pos_classes.most_common()),
                jdump(prefix_variants.most_common(12)),
                jdump(suffix_variants.most_common(12)),
                fam["next_test"],
            ),
        )
        total_occ += len(occurrences)

    conn.execute(
        """
        UPDATE template_slot_probe_runs
        SET occurrence_count=?,
            decision=?,
            payload_json=?
        WHERE run_id=?
        """,
        (
            total_occ,
            "TEMPLATE_SLOT_FRONTIER_READY",
            jdump({"families": [f["family_key"] for f in FAMILIES]}),
            run_id,
        ),
    )
    conn.commit()

    rows = conn.execute(
        """
        SELECT family_key, anchor, classification, occurrence_count, book_count,
               position_classes_json, prefix_variants_json, suffix_variants_json, next_test
        FROM template_slot_family_items
        WHERE run_id=?
        ORDER BY occurrence_count DESC
        """,
        (run_id,),
    ).fetchall()
    print(
        json.dumps(
            {
                "template_slot_run_id": run_id,
                "family_count": len(FAMILIES),
                "occurrence_count": total_occ,
                "families": [dict(row) for row in rows],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
