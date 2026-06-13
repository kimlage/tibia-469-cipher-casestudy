#!/usr/bin/env python3
"""Split F02/LTAST/TTNVVN as boundary operator vs remaining blocked tail."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


DB_PATH = Path(__file__).resolve().parents[1] / "data" / "bonelord_operational.sqlite"
TARGET_BOOKS = ["0", "9", "10", "14", "33", "35", "37", "58", "59", "66", "69"]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def classify(text: str) -> tuple[str, str, dict]:
    has_f02 = "<F02>" in text
    has_ltast = "LTASTTNVVN" in text or "LTASTTNVVNNF" in text
    has_benna = "LEITELBENNA" in text or "FIININS" in text or "NIIFINI*" in text
    has_f01 = "<F01>" in text
    has_f05 = "<F05>" in text
    has_btii = "BTIIALBENEIENVNSBVN" in text or "ATFNAASTTNBEEILEEIEFFIFTLEITELB" in text
    has_rphase = "LIVRN" in text or "TRVEIIVNTBB" in text or "VAETRFEVAST" in text

    if (has_f02 or has_ltast) and not (has_f01 or has_f05 or has_btii or has_rphase):
        status = "BOUNDARY_OPERATOR_ONLY_CANDIDATE_NO_GLOSS"
        action = "render_ltast_ttnvvn_as_boundary_operator"
    elif has_f02 or has_ltast:
        status = "BOUNDARY_OPERATOR_WITH_RESIDUAL_BLOCKED_CONTEXT"
        action = "split_boundary_but_preserve_residual_blocked_context"
    else:
        status = "NO_F02_BOUNDARY_SIGNAL"
        action = "defer_to_other_blocked_family"
    return status, action, {
        "has_f02": has_f02,
        "has_ltast": has_ltast,
        "has_benna": has_benna,
        "has_f01": has_f01,
        "has_f05": has_f05,
        "has_btii": has_btii,
        "has_rphase": has_rphase,
    }


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        create table if not exists f02_boundary_split_probe_runs (
            run_id integer primary key,
            created_at text not null,
            decision text not null,
            checked_book_count integer not null,
            boundary_only_count integer not null,
            residual_blocked_count integer not null,
            no_signal_count integer not null,
            payload_json text not null
        );

        create table if not exists f02_boundary_split_items (
            run_id integer not null,
            bookid text not null,
            split_status text not null,
            gloss_allowed integer not null,
            next_action text not null,
            projected_text text not null,
            evidence_json text not null,
            primary key (run_id, bookid)
        );
        """
    )

    run_id = conn.execute("select coalesce(max(run_id), 0) + 1 from f02_boundary_split_probe_runs").fetchone()[0]
    projected_run_id = conn.execute("select max(run_id) from projected_semantic_safety_items").fetchone()[0]
    rows = list(
        conn.execute(
            f"""
            select bookid, audit_text
            from projected_semantic_safety_items
            where run_id = ? and bookid in ({','.join('?' for _ in TARGET_BOOKS)})
            order by cast(bookid as integer)
            """,
            (projected_run_id, *TARGET_BOOKS),
        )
    )

    boundary_only = residual = no_signal = 0
    for row in rows:
        text = row["audit_text"] or ""
        status, action, flags = classify(text)
        projected = (
            text.replace("<F02>", "<BOUNDARY:LTAST_TTNVVN>")
            .replace("LTASTTNVVNNF", "<BOUNDARY:LTAST_TTNVVN>NF")
            .replace("LTASTTNVVN", "<BOUNDARY:LTAST_TTNVVN>")
        )
        if status == "BOUNDARY_OPERATOR_ONLY_CANDIDATE_NO_GLOSS":
            boundary_only += 1
        elif status == "BOUNDARY_OPERATOR_WITH_RESIDUAL_BLOCKED_CONTEXT":
            residual += 1
        else:
            no_signal += 1
        conn.execute(
            """
            insert into f02_boundary_split_items
            (run_id, bookid, split_status, gloss_allowed, next_action, projected_text, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                row["bookid"],
                status,
                0,
                action,
                projected,
                json.dumps(flags, ensure_ascii=False),
            ),
        )

    decision = "F02_SPLIT_BOUNDARY_OPERATOR_WITH_RESIDUAL_BLOCKS_NO_GLOSS"
    if boundary_only and residual == 0:
        decision = "F02_SPLIT_BOUNDARY_OPERATOR_ONLY_NO_GLOSS"
    elif boundary_only == 0:
        decision = "F02_REMAINS_RESIDUAL_BLOCKED_NO_GLOSS"

    conn.execute(
        """
        insert into f02_boundary_split_probe_runs
        (run_id, created_at, decision, checked_book_count, boundary_only_count,
         residual_blocked_count, no_signal_count, payload_json)
        values (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            now_iso(),
            decision,
            len(rows),
            boundary_only,
            residual,
            no_signal,
            json.dumps({"projected_run_id": projected_run_id, "target_books": TARGET_BOOKS}, ensure_ascii=False),
        ),
    )
    conn.commit()

    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "checked_book_count": len(rows),
                "boundary_only_count": boundary_only,
                "residual_blocked_count": residual,
                "no_signal_count": no_signal,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
