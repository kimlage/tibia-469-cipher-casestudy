#!/usr/bin/env python3
"""Local split policy for BTII/NSBVN weak external drift."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


DB_PATH = Path(__file__).resolve().parents[1] / "data" / "bonelord_operational.sqlite"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def residual_flags(text: str) -> dict[str, bool]:
    return {
        "has_f02_or_ltast": "<F02>" in text or "LTASTTNVVN" in text,
        "has_f01": "<F01>" in text,
        "has_f05": "<F05>" in text,
        "has_rphase": "LIVRN" in text or "TRVEIIVNTBB" in text or "VAETRFEVAST" in text,
    }


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        create table if not exists btii_nsbvn_local_split_policy_runs (
            run_id integer primary key,
            created_at text not null,
            decision text not null,
            source_drift_run_id integer not null,
            recovered_book_count integer not null,
            residual_preserved_book_count integer not null,
            payload_json text not null
        );

        create table if not exists btii_nsbvn_local_split_policy_items (
            run_id integer not null,
            bookid text not null,
            split_status text not null,
            gloss_allowed integer not null,
            next_action text not null,
            evidence_json text not null,
            primary key (run_id, bookid)
        );
        """
    )

    run_id = conn.execute("select coalesce(max(run_id), 0) + 1 from btii_nsbvn_local_split_policy_runs").fetchone()[0]
    drift_run_id = conn.execute("select max(run_id) from btii_nsbvn_drift_items").fetchone()[0]
    f02_projected_run_id = conn.execute("select max(run_id) from projected_semantic_safety_f02_items").fetchone()[0]

    projected = {
        row["bookid"]: row["projected_text"] or ""
        for row in conn.execute(
            "select bookid, projected_text from projected_semantic_safety_f02_items where run_id = ?",
            (f02_projected_run_id,),
        )
    }

    recovered = []
    residual = []
    for row in conn.execute(
        """
        select bookid, drift_status, weak_projection_score, weak_projection_status
        from btii_nsbvn_drift_items
        where run_id = ? and in_remaining_blocked = 1
        order by cast(bookid as integer)
        """,
        (drift_run_id,),
    ):
        flags = residual_flags(projected.get(row["bookid"], ""))
        has_residual = any(flags.values())
        if has_residual:
            status = "PRESERVE_RESIDUAL_BLOCKED_CONTEXT_NO_GLOSS"
            action = "mark_btii_as_drift_but_keep_book_flagged_for_other_residuals"
            residual.append(row["bookid"])
        else:
            status = "LOCAL_EXTERNAL_DRIFT_DISPLAY_SAFE_NO_GLOSS"
            action = "allow_btii_nsbvn_as_display_drift_marker_only"
            recovered.append(row["bookid"])

        conn.execute(
            """
            insert into btii_nsbvn_local_split_policy_items
            (run_id, bookid, split_status, gloss_allowed, next_action, evidence_json)
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
                        **flags,
                        "drift_status": row["drift_status"],
                        "weak_projection_score": row["weak_projection_score"],
                        "weak_projection_status": row["weak_projection_status"],
                    },
                    ensure_ascii=False,
                ),
            ),
        )

    decision = "BTII_NSBVN_LOCAL_SPLIT_POLICY_READY_NO_GLOSS"
    conn.execute(
        """
        insert into btii_nsbvn_local_split_policy_runs
        (run_id, created_at, decision, source_drift_run_id, recovered_book_count,
         residual_preserved_book_count, payload_json)
        values (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            now_iso(),
            decision,
            drift_run_id,
            len(recovered),
            len(residual),
            json.dumps({"recovered_books": recovered, "residual_books": residual}, ensure_ascii=False),
        ),
    )
    conn.commit()

    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "recovered_book_count": len(recovered),
                "residual_preserved_book_count": len(residual),
                "recovered_books": recovered,
                "residual_books": residual,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
