#!/usr/bin/env python3
"""Create source bridges for R20/R02 human phase-shadow expansion."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

BRIDGES = [
    {
        "bridge_id": "B_R02_NAESE_SLOT_BRIDGE",
        "target_family": "R02_NAESE_SLOT_BRIDGE",
        "anchor_ids": ["AWB_469_LANGUAGE_MATHEMAGIC", "PARADOX_1_PLUS_1_KEYS"],
        "support_level": "STRUCTURAL_STRONG_PHASE_SLOT_BRIDGE",
        "support_summary": "Books 51/53 pass the R02 bridge gate and carry ordered NAESE/C68 slot mechanics.",
        "blocked_overreach": "Do not translate R02, NAESE, or C68 as words; keep this as a phase-to-slot bridge.",
        "next_probe": "Use Books 51/53 as positive R02 slot controls against 45/46 support and 14 boundary audit.",
    },
    {
        "bridge_id": "B_R02_R20_CONTEXT_CONNECTOR",
        "target_family": "R02_R20_CONTEXT_CONNECTOR",
        "anchor_ids": ["AWB_469_LANGUAGE_MATHEMAGIC", "HONEMINAS_FORMULA_PARALLEL"],
        "support_level": "STRUCTURAL_CONTEXT_CONNECTOR_NO_PROSE",
        "support_summary": "Books 45/46 carry R02/R20 context-connector material; Book45 is related but not a clean NAESE slot proof.",
        "blocked_overreach": "Do not promote connector material as a sentence connective or as a global R meaning.",
        "next_probe": "Contrast 45/46 against 51/53 positives and against 17/65 negative/branch controls.",
    },
    {
        "bridge_id": "B_VINVIN_R20_COVERED_BRANCH",
        "target_family": "VINVIN_R20_COVERED_BRANCH",
        "anchor_ids": ["AWB_469_LANGUAGE_MATHEMAGIC", "PARADOX_1_PLUS_1_KEYS"],
        "support_level": "STRUCTURAL_BRANCH_COVERED_BY_VINVIN",
        "support_summary": "R20_VTLRNEFIE appears as covered branch context inside VINVIN-style branch material.",
        "blocked_overreach": "Do not promote R20_VTLRNEFIE separately when the stronger evidence says VINVIN covers the branch.",
        "next_probe": "Keep 15/16/29/68 as covered-branch controls and compare 61/65 as endpoints with R20 phase block.",
    },
    {
        "bridge_id": "B_R20_PHASE_BLOCK",
        "target_family": "R20_PHASE_BLOCK",
        "anchor_ids": ["AWB_469_LANGUAGE_MATHEMAGIC", "HONEMINAS_FORMULA_PARALLEL"],
        "support_level": "STRUCTURAL_PHASE_BLOCK_NO_GLOSS",
        "support_summary": "R20_VAETRFEVAST is a repeated local phase block, often adjacent to connector or branch material.",
        "blocked_overreach": "Do not treat R20 as a lexical root; preserve the phase-block reading only.",
        "next_probe": "Separate clean R20 phase block, R20+VINVIN endpoint, and R20+LIVRN micro contexts.",
    },
    {
        "bridge_id": "B_R_LIVRN_MICRO_AUDIT",
        "target_family": "R_LIVRN_MICRO_AUDIT",
        "anchor_ids": ["AWB_469_LANGUAGE_MATHEMAGIC", "GREAT_CALCULATOR_GATHER_LANGUAGE"],
        "support_level": "AUDIT_MICRO_CONTEXT_NO_PROMOTION",
        "support_summary": "R02/R20 LIVRN microcontexts are visible but low-support and must stay audit-only.",
        "blocked_overreach": "Do not use LIVRN microcontext to infer R02/R20 meaning or book-level prose.",
        "next_probe": "Hold 58/59/60 as micro controls; only revisit after a stronger edge or in-game parallel appears.",
    },
    {
        "bridge_id": "B_R02_LTAST_BOUNDARY_AUDIT",
        "target_family": "R02_LTAST_BOUNDARY_AUDIT",
        "anchor_ids": ["AWB_469_LANGUAGE_MATHEMAGIC", "CHAYENNE_EXTERNAL_FRAME"],
        "support_level": "WEAK_BOUNDARY_AUDIT_NO_PROMOTION",
        "support_summary": "Book14 has R02 plus zero exits into VNA/LTAST-like boundary material, but the LTAST gate stayed weak.",
        "blocked_overreach": "Do not promote Book14 as an LTAST or R02 translation; keep it as boundary audit evidence.",
        "next_probe": "Reopen Book14 only if a new phase/LTAST control beats the existing weak boundary gate.",
    },
]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_r20_r02_phase_bridge_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            anchor_run_id INTEGER NOT NULL,
            phase_frame_run_id INTEGER NOT NULL,
            phase_gate_run_id INTEGER NOT NULL,
            bridge_count INTEGER NOT NULL,
            promoted_gloss_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_r20_r02_phase_bridge_v1_items (
            run_id INTEGER NOT NULL,
            bridge_id TEXT NOT NULL,
            target_family TEXT NOT NULL,
            anchor_ids_json TEXT NOT NULL,
            support_level TEXT NOT NULL,
            support_summary TEXT NOT NULL,
            blocked_overreach TEXT NOT NULL,
            next_probe TEXT NOT NULL,
            anchor_evidence_json TEXT NOT NULL,
            precheck_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bridge_id)
        );
        """
    )


def max_id(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT max(run_id) AS run_id FROM {table}").fetchone()
    if row is None or row["run_id"] is None:
        raise RuntimeError(f"missing required run: {table}")
    return int(row["run_id"])


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    anchor_run_id = max_id(conn, "human_ingame_anchor_corpus_v1_items")
    phase_frame_run_id = max_id(conn, "r20_r02_phase_frame_items")
    phase_gate_run_id = max_id(conn, "r20_r02_naese_phase_gate_v1_items")
    anchors = {
        row["anchor_id"]: dict(row)
        for row in conn.execute(
            "SELECT * FROM human_ingame_anchor_corpus_v1_items WHERE run_id=?",
            (anchor_run_id,),
        ).fetchall()
    }
    phase_frames = {
        row["frame_key"]: dict(row)
        for row in conn.execute(
            "SELECT * FROM r20_r02_phase_frame_items WHERE run_id=?",
            (phase_frame_run_id,),
        ).fetchall()
    }
    phase_gate = [
        dict(row)
        for row in conn.execute(
            "SELECT * FROM r20_r02_naese_phase_gate_v1_items WHERE run_id=?",
            (phase_gate_run_id,),
        ).fetchall()
    ]
    precheck = {
        "family": "R20/R02 phase",
        "reason_selected": "largest named missing family after atlas v3",
        "prior_failures": [
            "R20/R02 gate held prose promotion",
            "Book14 LTAST boundary gate stayed weak",
            "LIVRN microcontexts stayed audit-only",
        ],
        "expected_failure_mode": "collapsing phase, slot, VINVIN branch, and microcontext into a single prose gloss",
        "why_this_run_is_different": "split bridge rows by surviving structural roles before seeding human readings",
        "phase_frames": phase_frames,
        "phase_gate": phase_gate,
    }

    cur = conn.execute(
        """
        INSERT INTO human_r20_r02_phase_bridge_v1_runs
        (created_at, decision, anchor_run_id, phase_frame_run_id,
         phase_gate_run_id, bridge_count, promoted_gloss_count, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            now(),
            "HUMAN_R20_R02_PHASE_BRIDGES_READY_NO_GLOSS",
            anchor_run_id,
            phase_frame_run_id,
            phase_gate_run_id,
            len(BRIDGES),
            0,
            json.dumps({"principle": "split R02 slot bridge, R20 phase, VINVIN branch, and LIVRN micro before prose"}, ensure_ascii=False, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)
    for bridge in BRIDGES:
        missing = [anchor_id for anchor_id in bridge["anchor_ids"] if anchor_id not in anchors]
        if missing:
            raise RuntimeError(f"missing anchors for {bridge['bridge_id']}: {missing}")
        evidence = {anchor_id: anchors[anchor_id] for anchor_id in bridge["anchor_ids"]}
        conn.execute(
            """
            INSERT INTO human_r20_r02_phase_bridge_v1_items
            (run_id, bridge_id, target_family, anchor_ids_json, support_level,
             support_summary, blocked_overreach, next_probe,
             anchor_evidence_json, precheck_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                bridge["bridge_id"],
                bridge["target_family"],
                json.dumps(bridge["anchor_ids"], ensure_ascii=False, sort_keys=True),
                bridge["support_level"],
                bridge["support_summary"],
                bridge["blocked_overreach"],
                bridge["next_probe"],
                json.dumps(evidence, ensure_ascii=False, sort_keys=True),
                json.dumps(precheck, ensure_ascii=False, sort_keys=True),
            ),
        )

    conn.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": "HUMAN_R20_R02_PHASE_BRIDGES_READY_NO_GLOSS",
                "bridge_count": len(BRIDGES),
                "promoted_gloss_count": 0,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
