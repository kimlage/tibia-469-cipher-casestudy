#!/usr/bin/env python3
"""Rank suspect retext constraints by presence in the honest v2 layer."""

from __future__ import annotations

import json
import sqlite3
from collections import defaultdict
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
        create table if not exists retext_suspect_presence_rank_runs (
            run_id integer primary key,
            created_at text not null,
            decision text not null,
            candidate_count integer not null,
            present_count integer not null,
            payload_json text not null
        );

        create table if not exists retext_suspect_presence_rank_items (
            run_id integer not null,
            rank integer not null,
            token text not null,
            decision text not null,
            confidence text not null,
            blocked_old_hint text,
            book_count integer not null,
            hit_count integer not null,
            priority_score integer not null,
            recommended_action text not null,
            evidence_json text not null,
            primary key (run_id, rank)
        );
        """
    )

    run_id = conn.execute("select coalesce(max(run_id), 0) + 1 from retext_suspect_presence_rank_runs").fetchone()[0]
    honest_run_id = conn.execute("select max(run_id) from final_honest_reading_v2_books").fetchone()[0]
    constraints = list(
        conn.execute(
            """
            select token, decision, confidence, blocked_old_hint, reason, reopen_condition
            from semantic_constraint_registry
            where decision like 'SUSPECT_RETEXT%'
            """
        )
    )
    books = list(
        conn.execute(
            "select bookid, honest_text from final_honest_reading_v2_books where run_id=?",
            (honest_run_id,),
        )
    )

    items = []
    confidence_weight = {"HIGH": 40, "MEDIUM_HIGH": 30, "MEDIUM": 20, "MEDIUM_LOW": 10}
    for c in constraints:
        hit_count = 0
        bookids = []
        for b in books:
            hits = (b["honest_text"] or "").count(c["token"])
            if hits:
                hit_count += hits
                bookids.append(b["bookid"])
        if hit_count == 0:
            action = "NO_CURRENT_PRESENCE_MONITOR_ONLY"
        elif c["decision"] == "SUSPECT_RETEXT_OVERFIT":
            action = "NEUTRALIZE_OR_REVERT_IN_SHADOW_NO_CORE_GLOSS"
        else:
            action = "COMPARE_VARIANTS_IN_SHADOW_NO_CORE_GLOSS"
        score = hit_count * 5 + len(set(bookids)) * 8 + confidence_weight.get(c["confidence"], 10)
        items.append(
            {
                "token": c["token"],
                "decision": c["decision"],
                "confidence": c["confidence"],
                "blocked_old_hint": c["blocked_old_hint"],
                "book_count": len(set(bookids)),
                "hit_count": hit_count,
                "priority_score": score,
                "recommended_action": action,
                "evidence": {
                    "bookids": sorted(set(bookids), key=lambda x: int(x) if x.isdigit() else x),
                    "reason": c["reason"],
                    "reopen_condition": c["reopen_condition"],
                },
            }
        )
    items.sort(key=lambda x: (-x["priority_score"], x["token"]))

    present = 0
    for rank, item in enumerate(items, start=1):
        if item["hit_count"]:
            present += 1
        conn.execute(
            """
            insert into retext_suspect_presence_rank_items
            (run_id, rank, token, decision, confidence, blocked_old_hint,
             book_count, hit_count, priority_score, recommended_action, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                rank,
                item["token"],
                item["decision"],
                item["confidence"],
                item["blocked_old_hint"],
                item["book_count"],
                item["hit_count"],
                item["priority_score"],
                item["recommended_action"],
                json.dumps(item["evidence"], ensure_ascii=False),
            ),
        )

    decision = "RETEXT_SUSPECT_PRESENCE_RANK_READY"
    conn.execute(
        """
        insert into retext_suspect_presence_rank_runs
        (run_id, created_at, decision, candidate_count, present_count, payload_json)
        values (?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            now_iso(),
            decision,
            len(items),
            present,
            json.dumps({"honest_v2_run_id": honest_run_id}, ensure_ascii=False),
        ),
    )
    conn.commit()

    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "candidate_count": len(items),
                "present_count": present,
                "top": [
                    {
                        "token": item["token"],
                        "priority_score": item["priority_score"],
                        "hit_count": item["hit_count"],
                        "book_count": item["book_count"],
                    }
                    for item in items[:8]
                ],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
