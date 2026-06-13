#!/usr/bin/env python3
"""Materialize a no-gloss policy for the NAESE/IVIFAST slot family."""

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
        create table if not exists naese_slot_policy_runs (
            run_id integer primary key,
            created_at text not null,
            decision text not null,
            occurrence_count integer not null,
            clean_exemplar_count integer not null,
            variant_count integer not null,
            promoted_boundary_count integer not null,
            audit_only_count integer not null,
            payload_json text not null
        );

        create table if not exists naese_slot_policy_items (
            run_id integer not null,
            bookid text not null,
            occurrence_index integer not null,
            prefix_class text not null,
            suffix_class text not null,
            position_class text not null,
            policy_status text not null,
            gloss_allowed integer not null,
            next_action text not null,
            evidence_json text not null,
            primary key (run_id, bookid, occurrence_index)
        );
        """
    )

    run_id = conn.execute("select coalesce(max(run_id), 0) + 1 from naese_slot_policy_runs").fetchone()[0]
    source_run_id = conn.execute("select max(run_id) from naese_ivifast_slot_items").fetchone()[0]
    rows = list(
        conn.execute(
            """
            select bookid, occurrence_index, prefix_class, suffix_class, position_class,
                   left_symbol_context, anchor_symbol_text, right_symbol_context, next_action
            from naese_ivifast_slot_items
            where run_id = ?
            order by cast(bookid as integer), occurrence_index
            """,
            (source_run_id,),
        )
    )

    clean_count = 0
    variant_count = 0
    promoted = 0
    audit_only = 0
    for row in rows:
        clean = row["next_action"] == "clean_template_exemplar_for_function_inference"
        if clean:
            clean_count += 1
            status = "PROMOTED_SLOT_BOUNDARY_NO_GLOSS"
            action = "use_as_naese_ivifast_clean_slot_boundary"
            promoted += 1
        else:
            variant_count += 1
            status = "VARIANT_AUDIT_ONLY_NO_GLOSS"
            action = "keep_variant_out_of_function_promotion"
            audit_only += 1

        conn.execute(
            """
            insert into naese_slot_policy_items
            (run_id, bookid, occurrence_index, prefix_class, suffix_class, position_class,
             policy_status, gloss_allowed, next_action, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                row["bookid"],
                row["occurrence_index"],
                row["prefix_class"],
                row["suffix_class"],
                row["position_class"],
                status,
                0,
                action,
                json.dumps(
                    {
                        "left_symbol_context": row["left_symbol_context"],
                        "anchor_symbol_text": row["anchor_symbol_text"],
                        "right_symbol_context": row["right_symbol_context"],
                        "source_next_action": row["next_action"],
                    },
                    ensure_ascii=False,
                ),
            ),
        )

    if clean_count >= 4 and variant_count > 0:
        decision = "NAESE_IVIFAST_PROMOTED_AS_SLOT_BOUNDARY_VARIANTS_AUDIT_ONLY_NO_GLOSS"
    elif clean_count >= 4:
        decision = "NAESE_IVIFAST_PROMOTED_AS_SLOT_BOUNDARY_NO_GLOSS"
    else:
        decision = "NAESE_IVIFAST_REMAINS_AUDIT_ONLY_NO_GLOSS"

    conn.execute(
        """
        insert into naese_slot_policy_runs
        (run_id, created_at, decision, occurrence_count, clean_exemplar_count,
         variant_count, promoted_boundary_count, audit_only_count, payload_json)
        values (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            now_iso(),
            decision,
            len(rows),
            clean_count,
            variant_count,
            promoted,
            audit_only,
            json.dumps({"source_run_id": source_run_id}, ensure_ascii=False),
        ),
    )
    conn.commit()

    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "occurrence_count": len(rows),
                "clean_exemplar_count": clean_count,
                "variant_count": variant_count,
                "promoted_boundary_count": promoted,
                "audit_only_count": audit_only,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
