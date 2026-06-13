#!/usr/bin/env python3
"""Refresh semantic evidence targets after final honest reading v2."""

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
        create table if not exists semantic_evidence_target_v2_runs (
            run_id integer primary key,
            created_at text not null,
            decision text not null,
            target_count integer not null,
            live_target_count integer not null,
            payload_json text not null
        );

        create table if not exists semantic_evidence_target_v2_items (
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

    run_id = conn.execute("select coalesce(max(run_id), 0) + 1 from semantic_evidence_target_v2_runs").fetchone()[0]
    v2_run_id = conn.execute("select max(run_id) from final_honest_reading_v2_runs").fetchone()[0]
    liv_run_id = conn.execute("select max(run_id) from liv_slot_contrast_probe_runs").fetchone()[0]
    hellgate38_run_id = conn.execute("select max(run_id) from hellgate38_continuation_slot_probe_runs").fetchone()[0]
    hellgate39_run_id = conn.execute("select max(run_id) from hellgate39_formula_holdout_probe_runs").fetchone()[0]

    retext_constraints = [
        dict(row)
        for row in conn.execute(
            """
            select token, decision, confidence, blocked_old_hint, reason, reopen_condition
            from semantic_constraint_registry
            where decision like 'SUSPECT_RETEXT%'
            order by case confidence when 'HIGH' then 1 when 'MEDIUM_HIGH' then 2 else 3 end, token
            limit 12
            """
        )
    ]

    targets = [
        {
            "target_id": "HELLGATE_LONG_ANCHOR_SEMANTIC_EXTENSION",
            "family": "HELLGATE_LONG_ANCHORS",
            "lane": "EXTERNAL_LONG_ANCHOR",
            "status": "OPEN",
            "priority_score": 96,
            "evidence_question": "Can Hellgate38/39 constraints create testable semantic relations beyond slot/boundary classification?",
            "expected_failure_mode": "Likely remains structural only; external book identity is not natural-language meaning.",
            "acceptance_gate": "Requires source-attested meaning or contrastive relation across independent external anchors; no token gloss from local fit.",
            "precheck": {"hellgate38_run_id": hellgate38_run_id, "hellgate39_run_id": hellgate39_run_id},
        },
        {
            "target_id": "RETEXT_SUSPECT_CONTRADICTION_REDUCTION",
            "family": "SUSPECT_RETEXT_CONSTRAINTS",
            "lane": "ANTI_HALLUCINATION_RETEXT_AUDIT",
            "status": "OPEN",
            "priority_score": 88,
            "evidence_question": "Can suspect English retexts be reversed or neutralized to reduce contradiction without inventing semantics?",
            "expected_failure_mode": "May only improve display consistency, not reveal language meaning.",
            "acceptance_gate": "Accept only if blind/contrastive anomaly score falls and final honest layer remains fully covered.",
            "precheck": {"constraints": retext_constraints},
        },
        {
            "target_id": "LIV_PHASE_SLOT_MONITOR",
            "family": "LIV_PHASE_SLOT",
            "lane": "STRUCTURAL_SEMANTIC_BRIDGE",
            "status": "MATERIALIZED_NO_GLOSS",
            "priority_score": 60,
            "evidence_question": "Monitor LIV_R02/R20/L slot pattern for future external evidence.",
            "expected_failure_mode": "No semantic payload; only structural phase slot.",
            "acceptance_gate": "Reopen only with independent phrase-level anchor or new edge support.",
            "precheck": {"liv_run_id": liv_run_id},
        },
        {
            "target_id": "BTII_NSBVN_WEAK_EXTERNAL_DRIFT",
            "family": "BTII_NSBVN_ATFNAAST",
            "lane": "WEAK_EXTERNAL_ANCHOR_AUDIT",
            "status": "QUARANTINED",
            "priority_score": 45,
            "evidence_question": "Can NSBVN*V/sunburn be upgraded from weak projection to real semantic anchor?",
            "expected_failure_mode": "Current evidence remains weak single-anchor projection.",
            "acceptance_gate": "Requires external phrase-level context recovery or independent source.",
            "precheck": {},
        },
    ]
    targets.sort(key=lambda item: (-item["priority_score"], item["target_id"]))

    for rank, target in enumerate(targets, start=1):
        conn.execute(
            """
            insert into semantic_evidence_target_v2_items
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
    decision = "SEMANTIC_EVIDENCE_TARGET_QUEUE_V2_READY"
    conn.execute(
        """
        insert into semantic_evidence_target_v2_runs
        (run_id, created_at, decision, target_count, live_target_count, payload_json)
        values (?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            now_iso(),
            decision,
            len(targets),
            live_count,
            json.dumps({"final_honest_v2_run_id": v2_run_id}, ensure_ascii=False),
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
