#!/usr/bin/env python3
"""Contain the final residual books 58/59 as unresolved micro-context, no gloss."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


DB_PATH = Path(__file__).resolve().parents[1] / "data" / "bonelord_operational.sqlite"
TARGET_BOOKS = ["58", "59"]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        create table if not exists final_residual_containment_runs (
            run_id integer primary key,
            created_at text not null,
            decision text not null,
            contained_book_count integer not null,
            semantic_gloss_allowed_count integer not null,
            payload_json text not null
        );

        create table if not exists final_residual_containment_items (
            run_id integer not null,
            bookid text not null,
            containment_status text not null,
            gloss_allowed integer not null,
            next_action text not null,
            evidence_json text not null,
            primary key (run_id, bookid)
        );
        """
    )

    run_id = conn.execute("select coalesce(max(run_id), 0) + 1 from final_residual_containment_runs").fetchone()[0]
    source_run_id = conn.execute("select max(run_id) from projected_semantic_safety_f01_f05_items").fetchone()[0]

    edge = conn.execute(
        """
        select classification, holdout_score, policy_flags_json, masked_overlap
        from overlap_formula_holdout_edge_items
        where run_id = (select max(run_id) from overlap_formula_holdout_edge_items)
          and edge_id = '1:1:58->35'
        """
    ).fetchone()

    contained = 0
    for row in conn.execute(
        f"""
        select bookid, projected_text
        from projected_semantic_safety_f01_f05_items
        where run_id = ? and bookid in ({','.join('?' for _ in TARGET_BOOKS)})
        order by cast(bookid as integer)
        """,
        (source_run_id, *TARGET_BOOKS),
    ):
        text = row["projected_text"] or ""
        has_livrn = "LIVRN" in text
        has_btii = "BTIIALBENEIENVNSBVN" in text or "NSBVN*V" in text or "ATFNAASTTNBEEILEEIEFFIFTLEITELB" in text
        has_f02 = "<F02>" in text or "LTASTTNVVN" in text
        status = "CONTAINED_UNRESOLVED_FORMULA_MICRO_CONTEXT_NO_GLOSS"
        action = "render_as_contained_residual_micro_context_not_translation"
        contained += 1
        conn.execute(
            """
            insert into final_residual_containment_items
            (run_id, bookid, containment_status, gloss_allowed, next_action, evidence_json)
            values (?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                row["bookid"],
                status,
                0,
                action,
                json.dumps(
                    {
                        "has_livrn": has_livrn,
                        "has_btii": has_btii,
                        "has_f02_or_ltast": has_f02,
                        "edge_58_35": dict(edge) if edge else None,
                        "reason": "all remaining signals are formula/dead edge, weak external drift, or low-support micro-context",
                    },
                    ensure_ascii=False,
                ),
            ),
        )

    decision = "FINAL_RESIDUALS_CONTAINED_AS_UNRESOLVED_NO_GLOSS"
    conn.execute(
        """
        insert into final_residual_containment_runs
        (run_id, created_at, decision, contained_book_count,
         semantic_gloss_allowed_count, payload_json)
        values (?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            now_iso(),
            decision,
            contained,
            0,
            json.dumps({"target_books": TARGET_BOOKS, "source_run_id": source_run_id}, ensure_ascii=False),
        ),
    )
    conn.commit()

    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "contained_book_count": contained,
                "semantic_gloss_allowed_count": 0,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
