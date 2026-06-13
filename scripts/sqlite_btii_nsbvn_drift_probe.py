#!/usr/bin/env python3
"""Classify BTII/NSBVN/ATFNAAST residuals as external-alignment drift or live payload."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


DB_PATH = Path(__file__).resolve().parents[1] / "data" / "bonelord_operational.sqlite"
NEEDLES = ["BTIIALBENEIENVNSBVN", "NSBVN*V", "ATFNAASTTNBEEILEEIEFFIFTLEITELB"]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        create table if not exists btii_nsbvn_drift_probe_runs (
            run_id integer primary key,
            created_at text not null,
            decision text not null,
            hit_book_count integer not null,
            weak_external_projection_count integer not null,
            remaining_projected_blocked_count integer not null,
            display_safe_candidate_count integer not null,
            payload_json text not null
        );

        create table if not exists btii_nsbvn_drift_items (
            run_id integer not null,
            bookid text not null,
            hit_count integer not null,
            in_remaining_blocked integer not null,
            weak_projection_score real,
            weak_projection_status text,
            drift_status text not null,
            gloss_allowed integer not null,
            next_action text not null,
            evidence_json text not null,
            primary key (run_id, bookid)
        );
        """
    )

    run_id = conn.execute("select coalesce(max(run_id), 0) + 1 from btii_nsbvn_drift_probe_runs").fetchone()[0]
    projected_run_id = conn.execute("select max(run_id) from projected_semantic_safety_items").fetchone()[0]
    token_run_id = conn.execute("select max(run_id) from row0_variant_book_tokens").fetchone()[0]
    projection_run_id = conn.execute("select max(run_id) from external_anchor_projection_items").fetchone()[0]

    weak_projection = {
        row["bookid"]: row
        for row in conn.execute(
            """
            select bookid, score, projection_status, raw_window
            from external_anchor_projection_items
            where run_id = ? and anchor_token = 'NSBVN*V'
            """,
            (projection_run_id,),
        )
    }

    remaining_blocked = {
        row["bookid"]
        for row in conn.execute(
            """
            select bookid
            from projected_semantic_safety_items
            where run_id = ? and projected_clean = 0
            """,
            (projected_run_id,),
        )
    }

    hit_books = []
    weak_count = 0
    remaining_count = 0
    display_safe = 0
    for row in conn.execute(
        """
        select bookid, symbol_text
        from row0_variant_book_tokens
        where run_id = ?
        order by cast(bookid as integer)
        """,
        (token_run_id,),
    ):
        text = row["symbol_text"] or ""
        hit_count = sum(text.count(needle) for needle in NEEDLES)
        if hit_count == 0:
            continue
        bookid = row["bookid"]
        hit_books.append(bookid)
        projection = weak_projection.get(bookid)
        has_weak_projection = bool(projection and "WEAK_SINGLE_ANCHOR" in projection["projection_status"])
        if has_weak_projection:
            weak_count += 1
        in_remaining = bookid in remaining_blocked
        if in_remaining:
            remaining_count += 1

        if has_weak_projection and not in_remaining:
            status = "WEAK_EXTERNAL_DRIFT_DISPLAY_ONLY_NO_GLOSS"
            action = "keep_as_external_alignment_drift_control"
            display_safe += 1
        elif has_weak_projection and in_remaining:
            status = "WEAK_EXTERNAL_DRIFT_WITH_RESIDUAL_BLOCKED_CONTEXT"
            action = "split_drift_marker_but_preserve_residual_blocked_context"
        elif in_remaining:
            status = "INTERNAL_RESIDUAL_BLOCKED_CONTEXT"
            action = "preserve_as_blocked_until_independent_split"
        else:
            status = "INTERNAL_FORMULA_DRIFT_DISPLAY_ONLY_NO_GLOSS"
            action = "keep_as_display_formula_drift"
            display_safe += 1

        conn.execute(
            """
            insert into btii_nsbvn_drift_items
            (run_id, bookid, hit_count, in_remaining_blocked, weak_projection_score,
             weak_projection_status, drift_status, gloss_allowed, next_action, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                bookid,
                hit_count,
                1 if in_remaining else 0,
                projection["score"] if projection else None,
                projection["projection_status"] if projection else None,
                status,
                0,
                action,
                json.dumps(
                    {
                        "needles": NEEDLES,
                        "raw_window": projection["raw_window"] if projection else None,
                    },
                    ensure_ascii=False,
                ),
            ),
        )

    decision = "BTII_NSBVN_CLASSIFIED_AS_WEAK_EXTERNAL_DRIFT_NO_GLOSS"
    if remaining_count:
        decision = "BTII_NSBVN_DRIFT_SPLIT_REQUIRED_WITH_RESIDUAL_BLOCKS_NO_GLOSS"

    conn.execute(
        """
        insert into btii_nsbvn_drift_probe_runs
        (run_id, created_at, decision, hit_book_count, weak_external_projection_count,
         remaining_projected_blocked_count, display_safe_candidate_count, payload_json)
        values (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            now_iso(),
            decision,
            len(hit_books),
            weak_count,
            remaining_count,
            display_safe,
            json.dumps(
                {
                    "hit_books": sorted(hit_books, key=int),
                    "projected_run_id": projected_run_id,
                    "projection_run_id": projection_run_id,
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
                "hit_book_count": len(hit_books),
                "weak_external_projection_count": weak_count,
                "remaining_projected_blocked_count": remaining_count,
                "display_safe_candidate_count": display_safe,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
