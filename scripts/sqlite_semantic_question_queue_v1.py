#!/usr/bin/env python3
"""Create semantic question queue from the consolidated functional grammar.

This turns structural progress into small, testable semantic questions with
acceptance and rejection criteria. It explicitly does not create prose gloss.
"""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

QUESTIONS = [
    {
        "question_id": "Q1_BENNA_FORMULA_FUNCTION",
        "priority": 1,
        "component": "BENNA_ORDERED_CORE_V2",
        "question": "What discourse function is performed by BENNA template/formula heads before handoff/context?",
        "structural_scope": "47->40, 58->35, 69->35",
        "acceptance_gate": "Must predict why 47 goes to 40 while 58/69 go to 35; must not translate all BENNA books as one phrase.",
        "rejection_gate": "Reject if it assigns a single English word to BENNA or uses quarantined display parallels as proof.",
        "next_probe": "contrast ordered BENNA heads against quarantined display windows 11/36/43/59 and boundary tails 0/33/66",
    },
    {
        "question_id": "Q2_HANDOFF_TO_CONTEXT_PAYLOAD",
        "priority": 2,
        "component": "HANDOFF_CONTEXT_35_TO_67",
        "question": "What functional transition occurs from handoff/context into VNCTIIN/C86 payload?",
        "structural_scope": "35->67->2 plus shadow 10/27",
        "acceptance_gate": "Must explain 35->67 and 67->2 as different transitions, not one continuous English clause.",
        "rejection_gate": "Reject if it skips directly from formula to slot without accounting for payload/context.",
        "next_probe": "derive role sequence labels for contig1 and compare with 10/27 shadows",
    },
    {
        "question_id": "Q3_NAESE_SLOT_MEANING",
        "priority": 3,
        "component": "NAESE_SLOT_CORE_V1",
        "question": "What does the canonical NAESE slot do structurally, and can that role bind to any external/lore meaning?",
        "structural_scope": "51->53, 67->2, variants 28/48, quarantine 42/56 and surface 5/9",
        "acceptance_gate": "Must distinguish R02 bridge, canonical slot, variants, and surface-only NAESE occurrences.",
        "rejection_gate": "Reject if NAESE is translated by surface occurrence alone or if 42/56 are treated as clean slots.",
        "next_probe": "slot contrast using 2/22/51/53 vs 28/48 vs 42/56",
    },
    {
        "question_id": "Q4_VINVIN_BRANCH_SEMANTICS",
        "priority": 4,
        "component": "VINVIN_BRANCH_CORE_V1",
        "question": "What semantic or discourse contrast separates R20/VINVIN branch from C86/VINVIN branch?",
        "structural_scope": "29->65, 52->62, 3->17->62, related C86/VNCTIIN context",
        "acceptance_gate": "Must account for 61->65 rejection and keep C86/VNCTIIN context separate from C86/VINVIN payload.",
        "rejection_gate": "Reject if all VINVIN/C86/VTLRNEFIE occurrences are collapsed into one meaning.",
        "next_probe": "branch contrast matrix: 29/65 vs 52/62 vs 3/17/62 vs 2/10/27/35/67",
    },
    {
        "question_id": "Q5_O23_ENDPOINT_BINDING",
        "priority": 5,
        "component": "O23_FNAAST_ENDPOINT",
        "question": "What endpoint function is shared by 13->38 and excluded from 56?",
        "structural_scope": "13->38 with 56 control",
        "acceptance_gate": "Must keep 56 as related control unless it passes endpoint-specific gate.",
        "rejection_gate": "Reject broad FNAAST translations that swallow formula/display families.",
        "next_probe": "endpoint contrast 13/38 vs 56 and ONAF/FNAAST scoped context",
    },
    {
        "question_id": "Q6_EXTERNAL_EXACT_GLOSS_ROUTE",
        "priority": 6,
        "component": "AUTHORIZED_SOURCE_REQUESTS",
        "question": "Can an authorized source attest exact phrase-to-meaning for any full Bonelord sequence?",
        "structural_scope": "CipSoft/fansite/interview exact sequences only",
        "acceptance_gate": "Requires exact sequence plus meaning/provenance from authorized or strongly evidenced source.",
        "rejection_gate": "Reject paraphrases, fan guesses, cipher keys without exact sequence attestation, and broad lore-only anchors.",
        "next_probe": "send/prepare exact-source requests or search only for exact phrase attestations",
    },
]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS semantic_question_queue_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            question_count INTEGER NOT NULL,
            accepted_human_gloss_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS semantic_question_queue_v1_items (
            run_id INTEGER NOT NULL,
            question_id TEXT NOT NULL,
            priority INTEGER NOT NULL,
            component TEXT NOT NULL,
            status TEXT NOT NULL,
            question TEXT NOT NULL,
            structural_scope TEXT NOT NULL,
            acceptance_gate TEXT NOT NULL,
            rejection_gate TEXT NOT NULL,
            next_probe TEXT NOT NULL,
            PRIMARY KEY (run_id, question_id)
        )
        """
    )
    gloss = int(conn.execute("SELECT accepted_human_gloss_count FROM semantic_bridge_status_v1_runs WHERE run_id=(SELECT max(run_id) FROM semantic_bridge_status_v1_runs)").fetchone()[0])
    decision = "SEMANTIC_QUEUE_READY_NO_HUMAN_GLOSS" if gloss == 0 else "SEMANTIC_QUEUE_READY_WITH_PARTIAL_GLOSS"
    cur = conn.execute(
        """
        INSERT INTO semantic_question_queue_v1_runs
        (created_at, decision, question_count, accepted_human_gloss_count, payload_json)
        VALUES (?, ?, ?, ?, ?)
        """,
        (now(), decision, len(QUESTIONS), gloss, json.dumps({"source": "functional_grammar_synthesis_v1 run2"}, sort_keys=True)),
    )
    run_id = int(cur.lastrowid)
    for q in QUESTIONS:
        conn.execute(
            """
            INSERT INTO semantic_question_queue_v1_items
            (run_id, question_id, priority, component, status, question, structural_scope, acceptance_gate, rejection_gate, next_probe)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, q["question_id"], q["priority"], q["component"], "OPEN_NO_GLOSS", q["question"], q["structural_scope"], q["acceptance_gate"], q["rejection_gate"], q["next_probe"]),
        )
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": decision, "question_count": len(QUESTIONS), "accepted_human_gloss_count": gloss, "top_questions": [q["question_id"] for q in QUESTIONS[:3]]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
