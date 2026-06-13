#!/usr/bin/env python3
"""Build a post-honest-layer queue for real semantic evidence targets."""

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
        create table if not exists semantic_evidence_target_runs (
            run_id integer primary key,
            created_at text not null,
            decision text not null,
            target_count integer not null,
            live_target_count integer not null,
            payload_json text not null
        );

        create table if not exists semantic_evidence_target_items (
            run_id integer not null,
            rank integer not null,
            target_id text not null,
            family text not null,
            lane text not null,
            status text not null,
            priority_score integer not null,
            evidence_question text not null,
            expected_failure_mode text not null,
            acceptance_gate text not null,
            precheck_json text not null,
            primary key (run_id, rank)
        );
        """
    )

    run_id = conn.execute("select coalesce(max(run_id), 0) + 1 from semantic_evidence_target_runs").fetchone()[0]
    final_run_id = conn.execute("select max(run_id) from final_honest_reading_runs").fetchone()[0]
    contained = list(
        conn.execute(
            "select bookid, evidence_json from final_honest_reading_books where run_id=? and reading_status like 'CONTAINED%'",
            (final_run_id,),
        )
    )
    hellgate = list(
        conn.execute(
            "select refname, expected_bookid, digits_len, row0_code_hit, anchor_status from hellgate_long_anchor_items where run_id=(select max(run_id) from hellgate_long_anchor_items)"
        )
    )
    constraints = list(
        conn.execute(
            """
            select token, decision, confidence, blocked_old_hint, reason, reopen_condition
            from semantic_constraint_registry
            where decision like 'SUSPECT_RETEXT%' or decision = 'KEEP_NAMED_UNKNOWN'
            order by case confidence when 'HIGH' then 1 when 'MEDIUM_HIGH' then 2 else 3 end, token
            limit 8
            """
        )
    )

    targets: list[dict] = [
        {
            "target_id": "LIVRN_FINAL_RESIDUAL_58_59",
            "family": "LIVRN_MICRO_CONTEXT",
            "lane": "STRUCTURAL_SEMANTIC_BRIDGE",
            "status": "OPEN",
            "priority_score": 100,
            "evidence_question": "Can LIVRN be independently classified as a boundary/slot/operator rather than payload in books 58/59?",
            "expected_failure_mode": "Only two occurrences, zero edge support; likely remains unresolved micro-context.",
            "acceptance_gate": "Requires an independent non-58/59 occurrence, contig edge support, or external phrase-level anchor; no gloss from local fit.",
            "precheck": {"contained_books": [dict(row) for row in contained]},
        },
        {
            "target_id": "HELLGATE_LONG_ANCHOR_38_39_SEMANTIC_TEST",
            "family": "HELLGATE_LONG_ANCHORS",
            "lane": "EXTERNAL_LONG_ANCHOR",
            "status": "OPEN",
            "priority_score": 92,
            "evidence_question": "Can long external Hellgate anchors yield semantic constraints beyond mechanical alignment?",
            "expected_failure_mode": "They prove book text identity, not meaning; row0 alignment may not translate.",
            "acceptance_gate": "Requires a source with natural-language meaning tied to the same full sequence or a contrastive relation across independent anchors.",
            "precheck": {"hellgate_anchors": [dict(row) for row in hellgate]},
        },
        {
            "target_id": "BTII_NSBVN_WEAK_EXTERNAL_DRIFT",
            "family": "BTII_NSBVN_ATFNAAST",
            "lane": "WEAK_EXTERNAL_ANCHOR_AUDIT",
            "status": "QUARANTINED",
            "priority_score": 70,
            "evidence_question": "Can NSBVN*V/sunburn be upgraded from weak projection to real semantic anchor?",
            "expected_failure_mode": "Current evidence is weak single-anchor projection and circular English drift.",
            "acceptance_gate": "Requires external phrase-level context recovery or independent source; substring/projection score is insufficient.",
            "precheck": {},
        },
        {
            "target_id": "RETEXT_SUSPECT_REOPEN_SET",
            "family": "SUSPECT_RETEXT_CONSTRAINTS",
            "lane": "ANTI_HALLUCINATION_RETEXT_AUDIT",
            "status": "OPEN",
            "priority_score": 64,
            "evidence_question": "Which suspect English retexts can be reversed or constrained to reduce semantic contradiction?",
            "expected_failure_mode": "May improve consistency without creating meaning; risk of overfitting old anagram hints.",
            "acceptance_gate": "Only accept if contradiction decreases under blind/contrastive contexts and no hard/soft GT regressions.",
            "precheck": {"constraints": [dict(row) for row in constraints]},
        },
        {
            "target_id": "ROSETTA_NUMERIC_EXTERNAL_RECHECK",
            "family": "ROSETTA_NUMERIC_ANCHORS",
            "lane": "EXTERNAL_ANCHOR_AUDIT",
            "status": "QUARANTINED",
            "priority_score": 40,
            "evidence_question": "Can numeric external anchors produce phrase-level book alignment instead of short substring hits?",
            "expected_failure_mode": "Known anchors are NPC-only, too short, or absent from books.",
            "acceptance_gate": "Reopen only with phrase-level book overlap and source independence.",
            "precheck": {},
        },
    ]
    targets.sort(key=lambda item: (-item["priority_score"], item["target_id"]))

    for rank, target in enumerate(targets, start=1):
        conn.execute(
            """
            insert into semantic_evidence_target_items
            (run_id, rank, target_id, family, lane, status, priority_score,
             evidence_question, expected_failure_mode, acceptance_gate, precheck_json)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                rank,
                target["target_id"],
                target["family"],
                target["lane"],
                target["status"],
                target["priority_score"],
                target["evidence_question"],
                target["expected_failure_mode"],
                target["acceptance_gate"],
                json.dumps(target["precheck"], ensure_ascii=False),
            ),
        )

    live_count = sum(1 for target in targets if target["status"] == "OPEN")
    decision = "SEMANTIC_EVIDENCE_TARGET_QUEUE_READY_POST_HONEST_LAYER"
    conn.execute(
        """
        insert into semantic_evidence_target_runs
        (run_id, created_at, decision, target_count, live_target_count, payload_json)
        values (?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            now_iso(),
            decision,
            len(targets),
            live_count,
            json.dumps({"final_honest_run_id": final_run_id}, ensure_ascii=False),
        ),
    )
    conn.commit()

    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "target_count": len(targets),
                "live_target_count": live_count,
                "top_targets": [
                    {"target_id": item["target_id"], "priority_score": item["priority_score"], "status": item["status"]}
                    for item in targets[:3]
                ],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
