#!/usr/bin/env python3
"""Contrast the LIV _ N micro-frame as a slot pattern, no gloss."""

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
        create table if not exists liv_slot_contrast_probe_runs (
            run_id integer primary key,
            created_at text not null,
            decision text not null,
            occurrence_count integer not null,
            slot_class_count integer not null,
            target_58_59_supported integer not null,
            gloss_allowed integer not null,
            payload_json text not null
        );

        create table if not exists liv_slot_contrast_items (
            run_id integer not null,
            bookid text not null,
            pos integer not null,
            slot_token text,
            right_token text,
            slot_class text not null,
            left_context text not null,
            right_context text not null,
            evidence_json text not null,
            primary key (run_id, bookid, pos)
        );
        """
    )

    run_id = conn.execute("select coalesce(max(run_id), 0) + 1 from liv_slot_contrast_probe_runs").fetchone()[0]
    token_run_id = conn.execute("select max(run_id) from row0_variant_book_tokens").fetchone()[0]

    rows = list(
        conn.execute(
            """
            with tok as (
              select b.bookid, cast(j.key as int) pos, j.value token
              from row0_variant_book_tokens b, json_each(b.tokens_json) j
              where b.run_id = ?
            ),
            hits as (
              select a.bookid, a.pos, d.token as slot_token, e.token as right_token
              from tok a
              join tok b on b.bookid=a.bookid and b.pos=a.pos+1
              join tok c on c.bookid=a.bookid and c.pos=a.pos+2
              left join tok d on d.bookid=a.bookid and d.pos=a.pos+3
              left join tok e on e.bookid=a.bookid and e.pos=a.pos+4
              where a.token='L' and b.token='I' and c.token='V'
            )
            select h.bookid, h.pos, h.slot_token, h.right_token,
                   (select group_concat(token, '') from tok t where t.bookid=h.bookid and t.pos between h.pos-8 and h.pos-1) as left_context,
                   (select group_concat(token, '') from tok t where t.bookid=h.bookid and t.pos between h.pos+5 and h.pos+16) as right_context
            from hits h
            order by cast(h.bookid as integer), h.pos
            """,
            (token_run_id,),
        )
    )

    slot_classes = set()
    target_supported = 0
    for row in rows:
        if row["slot_token"] in {"R02", "R20"} and row["right_token"] == "N":
            slot_class = "LIV_PHASE_SLOT_R_VARIANT"
        elif row["slot_token"] == "L" and row["right_token"] == "N":
            slot_class = "LIV_PHASE_SLOT_L_VARIANT"
        else:
            slot_class = "LIV_IRREGULAR_AUDIT"
        slot_classes.add(slot_class)
        if row["bookid"] in {"58", "59"} and slot_class == "LIV_PHASE_SLOT_R_VARIANT":
            target_supported += 1
        conn.execute(
            """
            insert into liv_slot_contrast_items
            (run_id, bookid, pos, slot_token, right_token, slot_class,
             left_context, right_context, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                row["bookid"],
                row["pos"],
                row["slot_token"],
                row["right_token"],
                slot_class,
                row["left_context"] or "",
                row["right_context"] or "",
                json.dumps({"token_run_id": token_run_id}, ensure_ascii=False),
            ),
        )

    if target_supported == 2 and len(rows) >= 5:
        decision = "LIV_CLASSIFIED_AS_PHASE_SLOT_PATTERN_NO_GLOSS"
    else:
        decision = "LIV_REMAINS_UNRESOLVED_MICRO_CONTEXT_NO_GLOSS"

    conn.execute(
        """
        insert into liv_slot_contrast_probe_runs
        (run_id, created_at, decision, occurrence_count, slot_class_count,
         target_58_59_supported, gloss_allowed, payload_json)
        values (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            now_iso(),
            decision,
            len(rows),
            len(slot_classes),
            target_supported,
            0,
            json.dumps({"token_run_id": token_run_id}, ensure_ascii=False),
        ),
    )
    conn.commit()

    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "occurrence_count": len(rows),
                "slot_class_count": len(slot_classes),
                "target_58_59_supported": target_supported,
                "gloss_allowed": 0,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
