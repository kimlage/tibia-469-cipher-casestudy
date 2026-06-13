#!/usr/bin/env python3
"""Classify the remaining projected-unsafe books into blocked formula families."""

from __future__ import annotations

import json
import sqlite3
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


DB_PATH = Path(__file__).resolve().parents[1] / "data" / "bonelord_operational.sqlite"

FAMILIES = [
    ("F02_LTAST_TTNVVN", ["<F02>", "LTASTTNVVN", "LTASTTNVVNNF"]),
    ("BENNA_FIININS_FORMULA", ["LEITELBENNA", "FIININS", "NIIFINI*"]),
    ("BTII_NSBVN_ATFNAAST_BLOCK", ["BTIIALBENEIENVNSBVN", "ATFNAASTTNBEEILEEIEFFIFTLEITELB"]),
    ("F01_LOCAL_SPLIT_BLOCKED", ["<F01>"]),
    ("F05_LOCAL_SPLIT_BLOCKED", ["<F05>"]),
    ("R_PHASE_LIVRN", ["LIVRN", "TRVEIIVNTBB", "VAETRFEVAST"]),
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        create table if not exists remaining_blocked_family_probe_runs (
            run_id integer primary key,
            created_at text not null,
            decision text not null,
            source_projected_run_id integer not null,
            remaining_book_count integer not null,
            family_count integer not null,
            top_family text not null,
            payload_json text not null
        );

        create table if not exists remaining_blocked_family_items (
            run_id integer not null,
            family_id text not null,
            book_count integer not null,
            books_json text not null,
            example_text text not null,
            family_status text not null,
            next_action text not null,
            evidence_json text not null,
            primary key (run_id, family_id)
        );
        """
    )

    run_id = conn.execute("select coalesce(max(run_id), 0) + 1 from remaining_blocked_family_probe_runs").fetchone()[0]
    source_run_id = conn.execute("select max(run_id) from projected_semantic_safety_items").fetchone()[0]
    rows = list(
        conn.execute(
            """
            select bookid, audit_text, blocked_hit_count
            from projected_semantic_safety_items
            where run_id = ? and projected_clean = 0
            order by cast(bookid as integer)
            """,
            (source_run_id,),
        )
    )

    family_books: dict[str, list[str]] = defaultdict(list)
    family_examples: dict[str, str] = {}
    unmatched = []
    for row in rows:
        text = row["audit_text"] or ""
        matched = False
        for family_id, needles in FAMILIES:
            if any(needle in text for needle in needles):
                family_books[family_id].append(row["bookid"])
                family_examples.setdefault(family_id, text)
                matched = True
        if not matched:
            unmatched.append(row["bookid"])

    if unmatched:
        family_books["UNMATCHED_BLOCKED"].extend(unmatched)
        family_examples["UNMATCHED_BLOCKED"] = "unmatched"

    for family_id, books in family_books.items():
        if family_id == "F02_LTAST_TTNVVN":
            status = "LIVE_BOUNDARY_SPLIT_FRONTIER_NO_GLOSS"
            action = "split_ltast_ttnvvn_operator_from_blocked_tail"
        elif family_id == "BTII_NSBVN_ATFNAAST_BLOCK":
            status = "LIVE_EXTERNAL_ALIGNMENT_DRIFT_FRONTIER_NO_GLOSS"
            action = "test_sunburn_alignment_as_formula_drift_not_payload"
        elif family_id in {"F01_LOCAL_SPLIT_BLOCKED", "F05_LOCAL_SPLIT_BLOCKED"}:
            status = "LOCAL_SPLIT_BLOCKED_PRESERVED"
            action = "keep_blocked_context_preserved"
        else:
            status = "AUDIT_ONLY_BLOCKED_FAMILY"
            action = "keep_as_blocked_family_until_independent_split"
        conn.execute(
            """
            insert into remaining_blocked_family_items
            (run_id, family_id, book_count, books_json, example_text, family_status,
             next_action, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                family_id,
                len(set(books)),
                json.dumps(sorted(set(books), key=int), ensure_ascii=False),
                family_examples.get(family_id, ""),
                status,
                action,
                json.dumps({"needles": dict(FAMILIES).get(family_id, [])}, ensure_ascii=False),
            ),
        )

    top_family = max(family_books.items(), key=lambda kv: len(set(kv[1])))[0] if family_books else ""
    decision = "REMAINING_BLOCKED_FAMILIES_CLASSIFIED_NO_GLOSS"
    conn.execute(
        """
        insert into remaining_blocked_family_probe_runs
        (run_id, created_at, decision, source_projected_run_id, remaining_book_count,
         family_count, top_family, payload_json)
        values (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            now_iso(),
            decision,
            source_run_id,
            len(rows),
            len(family_books),
            top_family,
            json.dumps({"unmatched": unmatched}, ensure_ascii=False),
        ),
    )
    conn.commit()

    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "remaining_book_count": len(rows),
                "family_count": len(family_books),
                "top_family": top_family,
                "families": {family: sorted(set(books), key=int) for family, books in family_books.items()},
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
