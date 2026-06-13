#!/usr/bin/env python3
"""Promote dead/formula-only masks as display-safe, without semantic gloss."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


DB_PATH = Path(__file__).resolve().parents[1] / "data" / "bonelord_operational.sqlite"
SAFE_MASKS = {"<F03>", "<F04>", "<F06>"}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def mask_count(text: str, mask: str) -> int:
    return (text or "").count(mask)


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        create table if not exists formula_only_mask_promotion_runs (
            run_id integer primary key,
            created_at text not null,
            decision text not null,
            source_cssr_run_id integer not null,
            checked_book_count integer not null,
            recovered_book_count integer not null,
            still_flagged_book_count integer not null,
            blocked_remaining_count integer not null,
            projected_cssr_pct real not null,
            payload_json text not null
        );

        create table if not exists formula_only_mask_promotion_items (
            run_id integer not null,
            bookid text not null,
            source_strict_clean integer not null,
            recovered_by_formula_only_mask integer not null,
            blocked_hit_count integer not null,
            original_formula_hit_count integer not null,
            safe_formula_hit_count integer not null,
            unsafe_formula_hit_count integer not null,
            projected_status text not null,
            projected_text text not null,
            evidence_json text not null,
            primary key (run_id, bookid)
        );
        """
    )

    run_id = conn.execute("select coalesce(max(run_id), 0) + 1 from formula_only_mask_promotion_runs").fetchone()[0]
    cssr_run_id = conn.execute("select max(run_id) from conservative_semantic_safety_items").fetchone()[0]
    rows = list(
        conn.execute(
            """
            select bookid, strict_clean, blocked_hit_count, caution_hit_count,
                   formula_hit_count, unk_hit_count, suspect_hit_count, microseq_hit_count,
                   audit_text
            from conservative_semantic_safety_items
            where run_id = ?
            order by cast(bookid as integer)
            """,
            (cssr_run_id,),
        )
    )

    recovered = 0
    still_flagged = 0
    blocked_remaining = 0
    projected_clean = 0
    for row in rows:
        text = row["audit_text"] or ""
        safe_hits = sum(mask_count(text, mask) for mask in SAFE_MASKS)
        unsafe_formula_hits = max(0, int(row["formula_hit_count"]) - safe_hits)
        hard_risk = (
            int(row["blocked_hit_count"]) > 0
            or int(row["caution_hit_count"]) > 0
            or int(row["unk_hit_count"]) > 0
            or int(row["suspect_hit_count"]) > 0
            or int(row["microseq_hit_count"]) > 0
            or unsafe_formula_hits > 0
        )
        recovered_by_mask = int(row["strict_clean"]) == 0 and not hard_risk and safe_hits > 0
        if recovered_by_mask:
            recovered += 1
        if hard_risk:
            still_flagged += 1
        else:
            projected_clean += 1
        if int(row["blocked_hit_count"]) > 0:
            blocked_remaining += 1

        projected_text = text
        for mask in SAFE_MASKS:
            projected_text = projected_text.replace(mask, f"<DISPLAY_FORMULA:{mask[1:-1]}>")
        status = "PROJECTED_DISPLAY_SAFE_NO_GLOSS" if not hard_risk else "STILL_FLAGGED_NOT_SAFE"
        conn.execute(
            """
            insert into formula_only_mask_promotion_items
            (run_id, bookid, source_strict_clean, recovered_by_formula_only_mask,
             blocked_hit_count, original_formula_hit_count, safe_formula_hit_count,
             unsafe_formula_hit_count, projected_status, projected_text, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                row["bookid"],
                row["strict_clean"],
                1 if recovered_by_mask else 0,
                row["blocked_hit_count"],
                row["formula_hit_count"],
                safe_hits,
                unsafe_formula_hits,
                status,
                projected_text,
                json.dumps({"safe_masks": sorted(SAFE_MASKS)}, ensure_ascii=False),
            ),
        )

    projected_cssr = round(100.0 * projected_clean / len(rows), 2) if rows else 0.0
    decision = "FORMULA_ONLY_MASKS_PROJECT_DISPLAY_SAFE_NO_GLOSS"
    conn.execute(
        """
        insert into formula_only_mask_promotion_runs
        (run_id, created_at, decision, source_cssr_run_id, checked_book_count,
         recovered_book_count, still_flagged_book_count, blocked_remaining_count,
         projected_cssr_pct, payload_json)
        values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            now_iso(),
            decision,
            cssr_run_id,
            len(rows),
            recovered,
            still_flagged,
            blocked_remaining,
            projected_cssr,
            json.dumps({"safe_masks": sorted(SAFE_MASKS)}, ensure_ascii=False),
        ),
    )
    conn.commit()

    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "checked_book_count": len(rows),
                "recovered_book_count": recovered,
                "still_flagged_book_count": still_flagged,
                "blocked_remaining_count": blocked_remaining,
                "projected_cssr_pct": projected_cssr,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
