#!/usr/bin/env python3
"""Refresh target queue after Hellgate and retext decisions."""

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
        create table if not exists semantic_evidence_target_v3_runs (
            run_id integer primary key,
            created_at text not null,
            decision text not null,
            target_count integer not null,
            live_target_count integer not null,
            payload_json text not null
        );

        create table if not exists semantic_evidence_target_v3_items (
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

    run_id = conn.execute("select coalesce(max(run_id), 0) + 1 from semantic_evidence_target_v3_runs").fetchone()[0]
    hellgate_decision_run = conn.execute("select max(run_id) from hellgate_semantic_extension_decision_runs").fetchone()[0]
    retext_policy_run = conn.execute("select max(run_id) from retext_safe_policy_runs").fetchone()[0]
    final_v2_run = conn.execute("select max(run_id) from final_honest_reading_v2_runs").fetchone()[0]

    targets = [
        {
            "target_id": "NEW_EXTERNAL_SEMANTIC_ANCHOR_SEARCH",
            "family": "EXTERNAL_SOURCE_DISCOVERY",
            "lane": "RESEARCH_TO_SQLITE",
            "status": "OPEN",
            "priority_score": 100,
            "evidence_question": "Can we find source-attested natural-language meaning tied to exact 469 sequences, not just copied numeric text?",
            "expected_failure_mode": "Most sources repeat numeric strings or speculative translations without primary evidence.",
            "acceptance_gate": "Only accept if source gives exact sequence plus meaning/provenance, then ingest into SQLite as audit-only until contrast passes.",
            "precheck": {"final_honest_v2_run_id": final_v2_run},
        },
        {
            "target_id": "CONTRASTIVE_SEMANTIC_MODEL_SEARCH",
            "family": "INTERNAL_CONTRASTIVE_SEMANTICS",
            "lane": "SQL_CONTRASTIVE_MODEL",
            "status": "OPEN",
            "priority_score": 86,
            "evidence_question": "Can internal structural classes form semantic oppositions without lexical gloss?",
            "expected_failure_mode": "May only produce functional roles such as slot/boundary/formula, not plaintext.",
            "acceptance_gate": "Accept only relations that survive negative controls and predict held-out structural class; no English token gloss.",
            "precheck": {},
        },
        {
            "target_id": "HELLGATE_LONG_ANCHOR_SEMANTIC_EXTENSION",
            "family": "HELLGATE_LONG_ANCHORS",
            "lane": "EXTERNAL_LONG_ANCHOR",
            "status": "MATERIALIZED_STRUCTURAL_ONLY_NO_GLOSS",
            "priority_score": 65,
            "evidence_question": "Monitor Hellgate anchors for future source-attested meaning.",
            "expected_failure_mode": "Current evidence is structural-only.",
            "acceptance_gate": "Reopen only with source-attested natural-language meaning tied to exact full sequence.",
            "precheck": {"hellgate_decision_run_id": hellgate_decision_run},
        },
        {
            "target_id": "RETEXT_SUSPECT_CONTRADICTION_REDUCTION",
            "family": "SUSPECT_RETEXT_CONSTRAINTS",
            "lane": "ANTI_HALLUCINATION_RETEXT_AUDIT",
            "status": "MATERIALIZED_SAFE_POLICY_NO_CORE_GLOSS",
            "priority_score": 62,
            "evidence_question": "Monitor safe retext policy against future anomaly runs.",
            "expected_failure_mode": "Display consistency only; no semantic translation.",
            "acceptance_gate": "Reopen only if anomaly score increases or new phrase-specific safe rule is needed.",
            "precheck": {"retext_policy_run_id": retext_policy_run},
        },
        {
            "target_id": "BTII_NSBVN_WEAK_EXTERNAL_DRIFT",
            "family": "BTII_NSBVN_ATFNAAST",
            "lane": "WEAK_EXTERNAL_ANCHOR_AUDIT",
            "status": "QUARANTINED",
            "priority_score": 35,
            "evidence_question": "Can NSBVN*V/sunburn be upgraded from weak projection?",
            "expected_failure_mode": "Likely remains weak projection/circular English drift.",
            "acceptance_gate": "Requires external phrase-level context recovery or independent source.",
            "precheck": {},
        },
    ]
    targets.sort(key=lambda item: (-item["priority_score"], item["target_id"]))

    for rank, target in enumerate(targets, start=1):
        conn.execute(
            """
            insert into semantic_evidence_target_v3_items
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

    live = sum(1 for item in targets if item["status"] == "OPEN")
    decision = "SEMANTIC_EVIDENCE_TARGET_QUEUE_V3_READY"
    conn.execute(
        """
        insert into semantic_evidence_target_v3_runs
        (run_id, created_at, decision, target_count, live_target_count, payload_json)
        values (?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            now_iso(),
            decision,
            len(targets),
            live,
            json.dumps({"final_honest_v2_run_id": final_v2_run}, ensure_ascii=False),
        ),
    )
    conn.commit()

    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "target_count": len(targets),
                "live_target_count": live,
                "top_targets": [
                    {"target_id": item["target_id"], "status": item["status"], "priority_score": item["priority_score"]}
                    for item in targets[:3]
                ],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
