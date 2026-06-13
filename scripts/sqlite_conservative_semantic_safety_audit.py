#!/usr/bin/env python3
"""Compute conservative semantic safety rate (CSSR) for the 469 corpus.

CSSR intentionally penalizes uncertainty markers. A book is "strict clean" only
when it has no blocked/caution hits and no visible formula/unknown/suspect/
microsequence markers in the current audit display layer.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


DB_PATH = Path(__file__).resolve().parents[1] / "data" / "bonelord_operational.sqlite"


MARKERS = {
    "formula": "<FORMULA:",
    "unk": "<UNK:",
    "suspect": "<SUSPECT:",
    "microseq": "<MICROSEQ:",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def count_marker(text: str, marker: str) -> int:
    return (text or "").count(marker)


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        create table if not exists conservative_semantic_safety_runs (
            run_id integer primary key,
            created_at text not null,
            decision text not null,
            book_count integer not null,
            strict_clean_book_count integer not null,
            cssr_pct real not null,
            flagged_book_count integer not null,
            blocked_book_count integer not null,
            caution_book_count integer not null,
            formula_book_count integer not null,
            unk_book_count integer not null,
            suspect_book_count integer not null,
            microseq_book_count integer not null,
            payload_json text not null
        );

        create table if not exists conservative_semantic_safety_items (
            run_id integer not null,
            bookid text not null,
            strict_clean integer not null,
            blocked_hit_count integer not null,
            caution_hit_count integer not null,
            formula_hit_count integer not null,
            unk_hit_count integer not null,
            suspect_hit_count integer not null,
            microseq_hit_count integer not null,
            safety_status text not null,
            audit_text text,
            evidence_json text not null,
            primary key (run_id, bookid)
        );
        """
    )

    run_id = conn.execute("select coalesce(max(run_id), 0) + 1 from conservative_semantic_safety_runs").fetchone()[0]
    safe_run_id = conn.execute("select max(run_id) from safe_book_translation_runs").fetchone()[0]
    best_run_id = conn.execute("select max(run_id) from best_shadow_book_runs").fetchone()[0]
    formula_run_id = conn.execute("select max(run_id) from formula_mask_book_items").fetchone()[0]

    rows = list(
        conn.execute(
            """
            select
                s.bookid,
                coalesce(b.best_shadow_text, s.safe_text, s.source_text, '') as base_text,
                s.blocked_hit_count,
                s.caution_hit_count,
                coalesce(f.masked_occurrences, 0) as formula_mask_count,
                coalesce(f.masked_text, b.best_shadow_text, s.safe_text, s.source_text, '') as audit_text
            from safe_book_translations s
            left join best_shadow_book_translations b
              on b.bookid = s.bookid and b.run_id = ?
            left join formula_mask_book_items f
              on f.bookid = s.bookid and f.run_id = ?
            where s.run_id = ?
            order by cast(s.bookid as integer)
            """,
            (best_run_id, formula_run_id, safe_run_id),
        )
    )

    totals = {
        "strict_clean": 0,
        "flagged": 0,
        "blocked": 0,
        "caution": 0,
        "formula": 0,
        "unk": 0,
        "suspect": 0,
        "microseq": 0,
    }

    for row in rows:
        audit_text = row["audit_text"] or row["base_text"] or ""
        marker_counts = {name: count_marker(audit_text, marker) for name, marker in MARKERS.items()}
        formula_hits = int(row["formula_mask_count"] or 0) + marker_counts["formula"]
        blocked = int(row["blocked_hit_count"] or 0)
        caution = int(row["caution_hit_count"] or 0)
        unk = marker_counts["unk"]
        suspect = marker_counts["suspect"]
        microseq = marker_counts["microseq"]

        flags = {
            "blocked": blocked > 0,
            "caution": caution > 0,
            "formula": formula_hits > 0,
            "unk": unk > 0,
            "suspect": suspect > 0,
            "microseq": microseq > 0,
        }
        strict_clean = not any(flags.values())
        if strict_clean:
            totals["strict_clean"] += 1
        else:
            totals["flagged"] += 1
        for key, active in flags.items():
            if active:
                totals[key] += 1

        status = "STRICT_CLEAN_AUDIT_LAYER" if strict_clean else "FLAGGED_NOT_SEMANTICALLY_SAFE"
        conn.execute(
            """
            insert into conservative_semantic_safety_items
            (run_id, bookid, strict_clean, blocked_hit_count, caution_hit_count,
             formula_hit_count, unk_hit_count, suspect_hit_count, microseq_hit_count,
             safety_status, audit_text, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                row["bookid"],
                1 if strict_clean else 0,
                blocked,
                caution,
                formula_hits,
                unk,
                suspect,
                microseq,
                status,
                audit_text,
                json.dumps({"flags": flags}, ensure_ascii=False),
            ),
        )

    book_count = len(rows)
    cssr = round(100.0 * totals["strict_clean"] / book_count, 2) if book_count else 0.0
    decision = "SEMANTIC_SAFETY_PARTIAL_NOT_FINAL_TRANSLATION"
    if cssr == 100.0:
        decision = "SEMANTIC_SAFETY_FULL_AUDIT_CLEAN_REQUIRES_EXTERNAL_CONFIRMATION"

    conn.execute(
        """
        insert into conservative_semantic_safety_runs
        (run_id, created_at, decision, book_count, strict_clean_book_count, cssr_pct,
         flagged_book_count, blocked_book_count, caution_book_count, formula_book_count,
         unk_book_count, suspect_book_count, microseq_book_count, payload_json)
        values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            now_iso(),
            decision,
            book_count,
            totals["strict_clean"],
            cssr,
            totals["flagged"],
            totals["blocked"],
            totals["caution"],
            totals["formula"],
            totals["unk"],
            totals["suspect"],
            totals["microseq"],
            json.dumps(
                {
                    "safe_run_id": safe_run_id,
                    "best_shadow_run_id": best_run_id,
                    "formula_mask_run_id": formula_run_id,
                    "definition": "books without blocked/caution and without FORMULA/UNK/SUSPECT/MICROSEQ markers",
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
                "book_count": book_count,
                "strict_clean_book_count": totals["strict_clean"],
                "cssr_pct": cssr,
                "flagged_book_count": totals["flagged"],
                "blocked_book_count": totals["blocked"],
                "caution_book_count": totals["caution"],
                "formula_book_count": totals["formula"],
                "unk_book_count": totals["unk"],
                "suspect_book_count": totals["suspect"],
                "microseq_book_count": totals["microseq"],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
