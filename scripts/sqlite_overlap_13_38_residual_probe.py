#!/usr/bin/env python3
"""Probe the live residual overlap edge 13->38 after formula masking.

The key question is whether the residual is new payload or a composition of
known structural families (O23/ONAF + NAESE/IVIFAST + local bridge). This probe
counts reusable segments across the row0 corpus and records an audit-only
classification. It does not assign semantic gloss.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


DB_PATH = Path(__file__).resolve().parents[1] / "data" / "bonelord_operational.sqlite"
TARGET_EDGE = "4:1:13->38"


SEGMENTS = [
    ("O23_ONAF_PREFIX", "ONAFIEI"),
    ("O23_EXTENDED_PREFIX", "ONAFIEIVEINLETFNAASTVA"),
    ("LOCAL_ENTEEAE_BRIDGE", "FENTEEAEISETE"),
    ("NAESE_IVIFAST_ANCHOR", "IVIFASTFNEIEINTA"),
    ("AETTA_SUFFIX", "AETTA"),
    ("FULL_RESIDUAL", "ONAFIEIVEINLETFNAASTVAFENTEEAEISETEIVIFASTFNEIEINTAAETTA"),
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def count_substring(text: str, needle: str) -> int:
    count = start = 0
    while True:
        pos = text.find(needle, start)
        if pos < 0:
            return count
        count += 1
        start = pos + 1


def classify_segment(segment_id: str, book_count: int, hit_count: int) -> str:
    if segment_id == "FULL_RESIDUAL":
        return "EDGE_SPECIFIC_COMPOSITE" if hit_count <= 2 else "REPEATED_FULL_PAYLOAD_CANDIDATE"
    if book_count >= 4:
        return "REUSABLE_STRUCTURAL_FAMILY"
    if book_count >= 2:
        return "LOCAL_BRIDGE_OR_VARIANT"
    return "EDGE_LOCAL_ONLY"


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        create table if not exists overlap_13_38_residual_probe_runs (
            run_id integer primary key,
            created_at text not null,
            decision text not null,
            segment_count integer not null,
            reusable_segment_count integer not null,
            local_segment_count integer not null,
            payload_candidate_count integer not null,
            payload_json text not null
        );

        create table if not exists overlap_13_38_residual_segment_items (
            run_id integer not null,
            segment_id text not null,
            segment_text text not null,
            hit_count integer not null,
            book_count integer not null,
            bookids_json text not null,
            segment_status text not null,
            evidence_json text not null,
            primary key (run_id, segment_id)
        );
        """
    )

    run_id = conn.execute("select coalesce(max(run_id), 0) + 1 from overlap_13_38_residual_probe_runs").fetchone()[0]
    row0_run_id = conn.execute("select max(run_id) from row0_variant_book_tokens").fetchone()[0]
    holdout_run_id = conn.execute("select max(run_id) from overlap_formula_holdout_edge_items").fetchone()[0]
    edge = conn.execute(
        """
        select edge_id, left_bookid, right_bookid, masked_overlap, classification, holdout_score
        from overlap_formula_holdout_edge_items
        where run_id = ? and edge_id = ?
        """,
        (holdout_run_id, TARGET_EDGE),
    ).fetchone()
    if not edge:
        raise SystemExit(f"missing target edge {TARGET_EDGE}")

    books = list(
        conn.execute(
            """
            select bookid, symbol_text
            from row0_variant_book_tokens
            where run_id = ?
            order by cast(bookid as integer)
            """,
            (row0_run_id,),
        )
    )

    reusable = local = payload_candidates = 0
    items = []
    for segment_id, segment_text in SEGMENTS:
        bookids = []
        hit_count = 0
        examples = []
        for book in books:
            hits = count_substring(book["symbol_text"], segment_text)
            if hits:
                hit_count += hits
                bookids.append(book["bookid"])
                if len(examples) < 8:
                    examples.append({"bookid": book["bookid"], "hits": hits})
        status = classify_segment(segment_id, len(bookids), hit_count)
        if status == "REUSABLE_STRUCTURAL_FAMILY":
            reusable += 1
        elif status == "REPEATED_FULL_PAYLOAD_CANDIDATE":
            payload_candidates += 1
        else:
            local += 1
        items.append((segment_id, segment_text, hit_count, bookids, status, examples))

        conn.execute(
            """
            insert into overlap_13_38_residual_segment_items
            (run_id, segment_id, segment_text, hit_count, book_count, bookids_json,
             segment_status, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                segment_id,
                segment_text,
                hit_count,
                len(bookids),
                json.dumps(bookids),
                status,
                json.dumps({"examples": examples}, ensure_ascii=False),
            ),
        )

    full_status = next(item[4] for item in items if item[0] == "FULL_RESIDUAL")
    if payload_candidates:
        decision = "OVERLAP_13_38_HAS_REPEATED_PAYLOAD_CANDIDATE_NO_GLOSS"
    elif full_status == "EDGE_SPECIFIC_COMPOSITE" and reusable >= 2:
        decision = "OVERLAP_13_38_IS_STRUCTURAL_COMPOSITE_NO_GLOSS"
    else:
        decision = "OVERLAP_13_38_REMAINS_AUDIT_ONLY_NO_GLOSS"

    conn.execute(
        """
        insert into overlap_13_38_residual_probe_runs
        (run_id, created_at, decision, segment_count, reusable_segment_count,
         local_segment_count, payload_candidate_count, payload_json)
        values (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            now_iso(),
            decision,
            len(SEGMENTS),
            reusable,
            local,
            payload_candidates,
            json.dumps(
                {
                    "row0_run_id": row0_run_id,
                    "holdout_run_id": holdout_run_id,
                    "target_edge": dict(edge),
                },
                ensure_ascii=False,
            ),
        ),
    )
    conn.commit()

    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "segment_count": len(SEGMENTS),
                "reusable_segment_count": reusable,
                "local_segment_count": local,
                "payload_candidate_count": payload_candidates,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
