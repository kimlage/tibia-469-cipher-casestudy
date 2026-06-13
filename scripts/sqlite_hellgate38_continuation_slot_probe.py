#!/usr/bin/env python3
"""Probe Hellgate 38 as continuation/slot evidence, no gloss."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


DB_PATH = Path(__file__).resolve().parents[1] / "data" / "bonelord_operational.sqlite"
FRAME = "ONAFIEI"
SLOT = "IVIFASTFNEIEINTA"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        create table if not exists hellgate38_continuation_slot_probe_runs (
            run_id integer primary key,
            created_at text not null,
            decision text not null,
            frame_occurrence_count integer not null,
            frame_book_count integer not null,
            slot_supported_count integer not null,
            external_holdout_supported integer not null,
            gloss_allowed integer not null,
            payload_json text not null
        );

        create table if not exists hellgate38_continuation_slot_items (
            run_id integer not null,
            bookid text not null,
            frame_pos integer not null,
            has_slot integer not null,
            is_hellgate38 integer not null,
            continuation_class text not null,
            left_context text not null,
            frame_window text not null,
            right_context text not null,
            evidence_json text not null,
            primary key (run_id, bookid, frame_pos)
        );
        """
    )

    run_id = conn.execute("select coalesce(max(run_id), 0) + 1 from hellgate38_continuation_slot_probe_runs").fetchone()[0]
    token_run_id = conn.execute("select max(run_id) from row0_variant_book_tokens").fetchone()[0]
    hellgate38 = conn.execute(
        """
        select row0_code_hit, anchor_status
        from hellgate_long_anchor_items
        where run_id=(select max(run_id) from hellgate_long_anchor_items)
          and expected_bookid='38'
        """
    ).fetchone()

    occ = 0
    books = set()
    slot_supported = 0
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
        start = 0
        while True:
            pos = text.find(FRAME, start)
            if pos < 0:
                break
            occ += 1
            books.add(row["bookid"])
            right = text[pos + len(FRAME) : pos + len(FRAME) + 80]
            has_slot = SLOT in right
            if has_slot:
                slot_supported += 1
                continuation = "O23_ONAF_TO_IVIFAST_SLOT_CONTINUATION"
            else:
                continuation = "O23_ONAF_WITHOUT_IVIFAST_SLOT"
            conn.execute(
                """
                insert into hellgate38_continuation_slot_items
                (run_id, bookid, frame_pos, has_slot, is_hellgate38,
                 continuation_class, left_context, frame_window, right_context, evidence_json)
                values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    row["bookid"],
                    pos,
                    1 if has_slot else 0,
                    1 if row["bookid"] == "38" else 0,
                    continuation,
                    text[max(0, pos - 24) : pos],
                    text[pos : pos + len(FRAME)],
                    right,
                    json.dumps({"slot": SLOT}, ensure_ascii=False),
                ),
            )
            start = pos + 1

    external_supported = 1 if hellgate38 and int(hellgate38["row0_code_hit"]) else 0
    if external_supported and slot_supported >= 2:
        decision = "HELLGATE38_SUPPORTS_O23_ONAF_TO_IVIFAST_SLOT_NO_GLOSS"
    else:
        decision = "HELLGATE38_CONTINUATION_REMAINS_AUDIT_ONLY_NO_GLOSS"

    conn.execute(
        """
        insert into hellgate38_continuation_slot_probe_runs
        (run_id, created_at, decision, frame_occurrence_count, frame_book_count,
         slot_supported_count, external_holdout_supported, gloss_allowed, payload_json)
        values (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            now_iso(),
            decision,
            occ,
            len(books),
            slot_supported,
            external_supported,
            0,
            json.dumps({"frame": FRAME, "slot": SLOT, "token_run_id": token_run_id}, ensure_ascii=False),
        ),
    )
    conn.commit()

    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "frame_occurrence_count": occ,
                "frame_book_count": len(books),
                "slot_supported_count": slot_supported,
                "external_holdout_supported": external_supported,
                "gloss_allowed": 0,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
