#!/usr/bin/env python3
"""Create a compact convergence state snapshot for the current SQLite state."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


DB_PATH = Path(__file__).resolve().parents[1] / "data" / "bonelord_operational.sqlite"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def scalar(conn: sqlite3.Connection, sql: str, default=None):
    row = conn.execute(sql).fetchone()
    return row[0] if row and row[0] is not None else default


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        create table if not exists convergence_state_snapshot_runs (
            run_id integer primary key,
            created_at text not null,
            decision text not null,
            operational_coverage_pct real not null,
            semantic_gloss_pct real not null,
            functional_class_count integer not null,
            retext_policy_count integer not null,
            accepted_external_semantic_anchor_count integer not null,
            open_target_count integer not null,
            payload_json text not null
        );
        """
    )

    run_id = scalar(conn, "select coalesce(max(run_id), 0) + 1 from convergence_state_snapshot_runs", 1)
    honest = conn.execute(
        """
        select operational_coverage_pct, semantic_gloss_pct, phase_slot_contained_book_count, unresolved_book_count
        from final_honest_reading_v2_runs
        order by run_id desc limit 1
        """
    ).fetchone()
    functional_class_count = scalar(
        conn,
        "select functional_class_count from internal_functional_semantic_model_runs order by run_id desc limit 1",
        0,
    )
    retext_policy_count = scalar(
        conn,
        "select item_count from retext_safe_policy_runs order by run_id desc limit 1",
        0,
    )
    accepted_external = scalar(
        conn,
        "select accepted_semantic_anchor_count from external_semantic_anchor_search_runs order by run_id desc limit 1",
        0,
    )
    open_targets = scalar(
        conn,
        "select live_target_count from semantic_evidence_target_v3_runs order by run_id desc limit 1",
        0,
    )
    decision = "CONVERGENCE_STATE_FUNCTIONAL_COMPLETE_LEXICAL_UNSOLVED"
    conn.execute(
        """
        insert into convergence_state_snapshot_runs
        (run_id, created_at, decision, operational_coverage_pct, semantic_gloss_pct,
         functional_class_count, retext_policy_count, accepted_external_semantic_anchor_count,
         open_target_count, payload_json)
        values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            now_iso(),
            decision,
            float(honest["operational_coverage_pct"] if honest else 0.0),
            float(honest["semantic_gloss_pct"] if honest else 0.0),
            int(functional_class_count),
            int(retext_policy_count),
            int(accepted_external),
            int(open_targets),
            json.dumps(
                {
                    "phase_slot_contained_book_count": honest["phase_slot_contained_book_count"] if honest else None,
                    "unresolved_book_count": honest["unresolved_book_count"] if honest else None,
                    "next": "external source discovery or new primary evidence required for lexical semantics",
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
                "operational_coverage_pct": float(honest["operational_coverage_pct"] if honest else 0.0),
                "semantic_gloss_pct": float(honest["semantic_gloss_pct"] if honest else 0.0),
                "functional_class_count": int(functional_class_count),
                "retext_policy_count": int(retext_policy_count),
                "accepted_external_semantic_anchor_count": int(accepted_external),
                "open_target_count": int(open_targets),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
