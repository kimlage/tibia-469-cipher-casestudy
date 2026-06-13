#!/usr/bin/env python3
"""Isolate F01/F05 partial formula masks across safe vs blocked contexts."""

from __future__ import annotations

import json
import sqlite3
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


DB_PATH = Path(__file__).resolve().parents[1] / "data" / "bonelord_operational.sqlite"
TARGET_MASKS = ["<F01>", "<F05>"]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def contexts(text: str, mask: str, radius: int = 24) -> list[dict]:
    out = []
    start = 0
    while True:
        pos = text.find(mask, start)
        if pos < 0:
            return out
        out.append(
            {
                "left": text[max(0, pos - radius) : pos],
                "right": text[pos + len(mask) : pos + len(mask) + radius],
                "pos": pos,
            }
        )
        start = pos + len(mask)


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        create table if not exists f01_f05_edge_isolation_probe_runs (
            run_id integer primary key,
            created_at text not null,
            decision text not null,
            mask_count integer not null,
            display_safe_mask_count integer not null,
            mixed_mask_count integer not null,
            blocked_only_mask_count integer not null,
            payload_json text not null
        );

        create table if not exists f01_f05_edge_isolation_items (
            run_id integer not null,
            mask_id text not null,
            occurrence_count integer not null,
            formula_only_book_count integer not null,
            blocked_book_count integer not null,
            left_context_classes_json text not null,
            right_context_classes_json text not null,
            isolation_status text not null,
            next_action text not null,
            evidence_json text not null,
            primary key (run_id, mask_id)
        );
        """
    )

    run_id = conn.execute("select coalesce(max(run_id), 0) + 1 from f01_f05_edge_isolation_probe_runs").fetchone()[0]
    source_run_id = conn.execute("select max(run_id) from conservative_semantic_safety_items").fetchone()[0]
    rows = list(
        conn.execute(
            """
            select bookid, blocked_hit_count, audit_text
            from conservative_semantic_safety_items
            where run_id = ?
            order by cast(bookid as integer)
            """,
            (source_run_id,),
        )
    )

    display_safe = mixed = blocked_only = 0
    for mask in TARGET_MASKS:
        occ = 0
        formula_only_books = set()
        blocked_books = set()
        left_classes: dict[str, int] = defaultdict(int)
        right_classes: dict[str, int] = defaultdict(int)
        examples = []
        for row in rows:
            hits = contexts(row["audit_text"] or "", mask)
            if not hits:
                continue
            occ += len(hits)
            if int(row["blocked_hit_count"]) > 0:
                blocked_books.add(row["bookid"])
            else:
                formula_only_books.add(row["bookid"])
            for hit in hits:
                left_key = hit["left"][-12:]
                right_key = hit["right"][:12]
                left_classes[left_key] += 1
                right_classes[right_key] += 1
                if len(examples) < 8:
                    examples.append({"bookid": row["bookid"], **hit})

        if formula_only_books and not blocked_books:
            status = "DISPLAY_SAFE_FORMULA_ONLY_NO_GLOSS"
            action = "promote_as_display_formula_only"
            display_safe += 1
        elif formula_only_books and blocked_books:
            status = "MIXED_CONTEXT_REQUIRES_EDGE_SPLIT_NO_GLOSS"
            action = "split_formula_only_context_from_blocked_context"
            mixed += 1
        else:
            status = "BLOCKED_ONLY_NO_PROMOTION"
            action = "keep_blocked"
            blocked_only += 1

        conn.execute(
            """
            insert into f01_f05_edge_isolation_items
            (run_id, mask_id, occurrence_count, formula_only_book_count, blocked_book_count,
             left_context_classes_json, right_context_classes_json, isolation_status,
             next_action, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                mask,
                occ,
                len(formula_only_books),
                len(blocked_books),
                json.dumps(dict(sorted(left_classes.items(), key=lambda kv: (-kv[1], kv[0]))), ensure_ascii=False),
                json.dumps(dict(sorted(right_classes.items(), key=lambda kv: (-kv[1], kv[0]))), ensure_ascii=False),
                status,
                action,
                json.dumps(
                    {
                        "formula_only_books": sorted(formula_only_books, key=int),
                        "blocked_books": sorted(blocked_books, key=int),
                        "examples": examples,
                    },
                    ensure_ascii=False,
                ),
            ),
        )

    decision = "F01_F05_MIXED_EDGE_SPLIT_REQUIRED_NO_GLOSS"
    if mixed == 0 and display_safe:
        decision = "F01_F05_DISPLAY_SAFE_NO_GLOSS"
    elif display_safe == 0 and mixed == 0:
        decision = "F01_F05_BLOCKED_NO_PROMOTION"

    conn.execute(
        """
        insert into f01_f05_edge_isolation_probe_runs
        (run_id, created_at, decision, mask_count, display_safe_mask_count,
         mixed_mask_count, blocked_only_mask_count, payload_json)
        values (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            now_iso(),
            decision,
            len(TARGET_MASKS),
            display_safe,
            mixed,
            blocked_only,
            json.dumps({"source_cssr_run_id": source_run_id}, ensure_ascii=False),
        ),
    )
    conn.commit()

    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "mask_count": len(TARGET_MASKS),
                "display_safe_mask_count": display_safe,
                "mixed_mask_count": mixed,
                "blocked_only_mask_count": blocked_only,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
