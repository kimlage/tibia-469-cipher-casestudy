#!/usr/bin/env python3
"""Reassess blocked F01/F05 contexts after F02 boundary acceptance."""

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
        create table if not exists f01_f05_reassessment_after_f02_runs (
            run_id integer primary key,
            created_at text not null,
            decision text not null,
            source_rphase_projected_run_id integer not null,
            recovered_book_count integer not null,
            residual_preserved_book_count integer not null,
            payload_json text not null
        );

        create table if not exists f01_f05_reassessment_after_f02_items (
            run_id integer not null,
            bookid text not null,
            reassessment_status text not null,
            gloss_allowed integer not null,
            next_action text not null,
            evidence_json text not null,
            primary key (run_id, bookid)
        );
        """
    )

    run_id = conn.execute("select coalesce(max(run_id), 0) + 1 from f01_f05_reassessment_after_f02_runs").fetchone()[0]
    projected_run_id = conn.execute("select max(run_id) from projected_semantic_safety_rphase_items").fetchone()[0]

    # Use the F02 split evidence as the authoritative residual view where present.
    f02_text = {
        row["bookid"]: row["projected_text"]
        for row in conn.execute(
            "select bookid, projected_text from f02_boundary_split_items where run_id=(select max(run_id) from f02_boundary_split_items)"
        )
    }

    recovered = []
    residual = []
    for row in conn.execute(
        """
        select bookid, projected_text
        from projected_semantic_safety_rphase_items
        where run_id = ? and projected_clean = 0 and (projected_text like '%<F01>%' or projected_text like '%<F05>%')
        order by cast(bookid as integer)
        """,
        (projected_run_id,),
    ):
        text = f02_text.get(row["bookid"], row["projected_text"] or "")
        has_f01 = "<F01>" in text
        has_f05 = "<F05>" in text
        has_boundary = "<BOUNDARY:LTAST_TTNVVN>" in text or "LTASTTNVVN" in text or "<F02>" in text
        has_btii = "BTIIALBENEIENVNSBVN" in text or "NSBVN*V" in text or "ATFNAASTTNBEEILEEIEFFIFTLEITELB" in text
        has_livrn = "LIVRN" in text
        has_rphase = "TRVEIIVNTBB" in text or "VAETRFEVAST" in text

        if (has_f01 or has_f05) and not has_btii and not has_livrn and not has_rphase:
            status = "LOCAL_FORMULA_WITH_ACCEPTED_BOUNDARY_DISPLAY_SAFE_NO_GLOSS"
            action = "render_f01_f05_as_local_formula_marker_with_boundary"
            recovered.append(row["bookid"])
        else:
            status = "PRESERVE_RESIDUAL_CONTEXT_NO_GLOSS"
            action = "keep_flagged_for_non_f01_f05_residual"
            residual.append(row["bookid"])

        conn.execute(
            """
            insert into f01_f05_reassessment_after_f02_items
            (run_id, bookid, reassessment_status, gloss_allowed, next_action, evidence_json)
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
                        "has_f01": has_f01,
                        "has_f05": has_f05,
                        "has_boundary": has_boundary,
                        "has_btii": has_btii,
                        "has_livrn": has_livrn,
                        "has_rphase": has_rphase,
                        "text": text,
                    },
                    ensure_ascii=False,
                ),
            ),
        )

    decision = "F01_F05_REASSESSED_AFTER_F02_READY_NO_GLOSS"
    conn.execute(
        """
        insert into f01_f05_reassessment_after_f02_runs
        (run_id, created_at, decision, source_rphase_projected_run_id,
         recovered_book_count, residual_preserved_book_count, payload_json)
        values (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            now_iso(),
            decision,
            projected_run_id,
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
