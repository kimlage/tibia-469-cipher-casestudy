#!/usr/bin/env python3
"""Local split policy for R-phase residuals in the final flagged set."""

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
        create table if not exists rphase_local_split_policy_runs (
            run_id integer primary key,
            created_at text not null,
            decision text not null,
            source_btii_projected_run_id integer not null,
            recovered_book_count integer not null,
            residual_preserved_book_count integer not null,
            payload_json text not null
        );

        create table if not exists rphase_local_split_policy_items (
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

    run_id = conn.execute("select coalesce(max(run_id), 0) + 1 from rphase_local_split_policy_runs").fetchone()[0]
    projected_run_id = conn.execute("select max(run_id) from projected_semantic_safety_btii_items").fetchone()[0]

    recovered = []
    residual = []
    for row in conn.execute(
        """
        select bookid, projected_text
        from projected_semantic_safety_btii_items
        where run_id = ? and projected_clean = 0
        order by cast(bookid as integer)
        """,
        (projected_run_id,),
    ):
        text = row["projected_text"] or ""
        has_r02_ready = "TRVEIIVNTBB" in text
        has_livrn_micro = "LIVRN" in text
        has_btii = "BTIIALBENEIENVNSBVN" in text or "NSBVN*V" in text or "ATFNAASTTNBEEILEEIEFFIFTLEITELB" in text
        has_f01_f05 = "<F01>" in text or "<F05>" in text

        if has_r02_ready and not has_livrn_micro and not has_btii and not has_f01_f05:
            status = "R02_PHASE_FRAME_DISPLAY_SAFE_NO_GLOSS"
            action = "render_r02_bridge_as_phase_frame"
            recovered.append(row["bookid"])
        elif has_livrn_micro:
            status = "PRESERVE_LIVRN_MICRO_CONTEXT_NO_GLOSS"
            action = "keep_livrn_micro_blocked_until_edge_support"
            residual.append(row["bookid"])
        elif has_r02_ready:
            status = "R02_PHASE_WITH_OTHER_RESIDUALS_NO_GLOSS"
            action = "split_r02_but_preserve_other_residuals"
            residual.append(row["bookid"])
        else:
            status = "NO_RPHASE_RECOVERY"
            action = "defer_to_other_residual_family"

        if status != "NO_RPHASE_RECOVERY":
            conn.execute(
                """
                insert into rphase_local_split_policy_items
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
                            "has_r02_ready": has_r02_ready,
                            "has_livrn_micro": has_livrn_micro,
                            "has_btii": has_btii,
                            "has_f01_f05": has_f01_f05,
                        },
                        ensure_ascii=False,
                    ),
                ),
            )

    decision = "RPHASE_LOCAL_SPLIT_POLICY_READY_NO_GLOSS"
    conn.execute(
        """
        insert into rphase_local_split_policy_runs
        (run_id, created_at, decision, source_btii_projected_run_id,
         recovered_book_count, residual_preserved_book_count, payload_json)
        values (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            now_iso(),
            decision,
            projected_run_id,
            len(recovered),
            len(set(residual)),
            json.dumps({"recovered_books": recovered, "residual_books": sorted(set(residual), key=int)}, ensure_ascii=False),
        ),
    )
    conn.commit()

    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "recovered_book_count": len(recovered),
                "residual_preserved_book_count": len(set(residual)),
                "recovered_books": recovered,
                "residual_books": sorted(set(residual), key=int),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
