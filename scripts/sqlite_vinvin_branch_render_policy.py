#!/usr/bin/env python3
"""Materialize VINVIN branch render policy without semantic gloss."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


DB_PATH = Path(__file__).resolve().parents[1] / "data" / "bonelord_operational.sqlite"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        create table if not exists vinvin_branch_render_policy_runs (
            run_id integer primary key,
            created_at text not null,
            decision text not null,
            branch_count integer not null,
            structural_branch_count integer not null,
            negative_control_count integer not null,
            payload_json text not null
        );

        create table if not exists vinvin_branch_render_policy_items (
            run_id integer not null,
            suffix_class text not null,
            source_branch_status text not null,
            render_status text not null,
            gloss_allowed integer not null,
            occurrence_count integer not null,
            book_count integer not null,
            contig_supported_count integer not null,
            partial_or_negative_count integer not null,
            render_label text not null,
            next_action text not null,
            evidence_json text not null,
            primary key (run_id, suffix_class)
        );
        """
    )

    run_id = conn.execute("select coalesce(max(run_id), 0) + 1 from vinvin_branch_render_policy_runs").fetchone()[0]
    source_run_id = conn.execute("select max(run_id) from vinvin_branch_subfunction_items").fetchone()[0]
    rows = list(
        conn.execute(
            """
            select suffix_class, occurrence_count, book_count, contig_supported_count,
                   o23_relation_count, partial_or_negative_count, branch_score,
                   branch_status, next_action, books_json
            from vinvin_branch_subfunction_items
            where run_id = ?
            order by branch_score desc
            """,
            (source_run_id,),
        )
    )

    structural = 0
    negative = 0
    for row in rows:
        if row["branch_status"] == "SUBFUNCTION_READY":
            render_status = "STRUCTURAL_BRANCH_RENDER_NO_GLOSS"
            render_label = f"<VINVIN_BRANCH:{row['suffix_class']}>"
            next_action = "use_as_structural_branch_boundary_and_contrast_control"
            structural += 1
        else:
            render_status = "NEGATIVE_FRAGMENT_CONTROL_NO_GLOSS"
            render_label = f"<VINVIN_FRAGMENT_CONTROL:{row['suffix_class']}>"
            next_action = "prevent_surface_fragment_promotion"
            negative += 1

        conn.execute(
            """
            insert into vinvin_branch_render_policy_items
            (run_id, suffix_class, source_branch_status, render_status, gloss_allowed,
             occurrence_count, book_count, contig_supported_count, partial_or_negative_count,
             render_label, next_action, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                row["suffix_class"],
                row["branch_status"],
                render_status,
                0,
                row["occurrence_count"],
                row["book_count"],
                row["contig_supported_count"],
                row["partial_or_negative_count"],
                render_label,
                next_action,
                json.dumps(
                    {
                        "o23_relation_count": row["o23_relation_count"],
                        "branch_score": row["branch_score"],
                        "books_json": row["books_json"],
                        "source_next_action": row["next_action"],
                    },
                    ensure_ascii=False,
                ),
            ),
        )

    decision = "VINVIN_BRANCHES_MATERIALIZED_AS_STRUCTURAL_RENDER_NO_GLOSS"
    conn.execute(
        """
        insert into vinvin_branch_render_policy_runs
        (run_id, created_at, decision, branch_count, structural_branch_count,
         negative_control_count, payload_json)
        values (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            now_iso(),
            decision,
            len(rows),
            structural,
            negative,
            json.dumps({"source_run_id": source_run_id}, ensure_ascii=False),
        ),
    )
    conn.commit()

    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "branch_count": len(rows),
                "structural_branch_count": structural,
                "negative_control_count": negative,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
