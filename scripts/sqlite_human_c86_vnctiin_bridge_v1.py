#!/usr/bin/env python3
"""Create source bridges for C86/VNCTIIN human shadow expansion."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

BRIDGES = [
    {
        "bridge_id": "B_C86_VNCTIIN_PAYLOAD_CORRIDOR",
        "target_family": "C86_VNCTIIN_PAYLOAD",
        "anchor_ids": ["AWB_469_LANGUAGE_MATHEMAGIC", "CHAYENNE_EXTERNAL_FRAME"],
        "support_level": "STRUCTURAL_PAYLOAD_WITH_EXTERNAL_CONTEXT_FRAME",
        "support_summary": "C86 opens payload corridors into VNCTIIN/C68 context; Chayenne confirms VNCTIIN can host external register frames.",
        "blocked_overreach": "Do not translate C86 or VNCTIIN as words; keep payload/context roles separate.",
        "next_probe": "Split C86/VNCTIIN payload books by BENNA, TAILBETFTE, NAESE, and clean context controls.",
    },
    {
        "bridge_id": "B_C86_VINVIN_BRANCH",
        "target_family": "C86_VINVIN_VTLR_BRANCH",
        "anchor_ids": ["AWB_469_LANGUAGE_MATHEMAGIC", "PARADOX_1_PLUS_1_KEYS"],
        "support_level": "STRUCTURAL_BRANCH_WITH_OPERATOR_GUARDRAIL",
        "support_summary": "C86 also opens VINVIN/VTLR branches; mathemagic remains an operator guardrail, not prose.",
        "blocked_overreach": "Do not collapse VINVIN/VTLR branch books into VNCTIIN context readings.",
        "next_probe": "Contrast VINVIN/VTLR branch books against C86/VNCTIIN payload books and R20/R02 phase controls.",
    },
    {
        "bridge_id": "B_VNCTIIN_PHASE_CONTEXT",
        "target_family": "VNCTIIN_PHASE_CONTEXT",
        "anchor_ids": ["AWB_469_LANGUAGE_MATHEMAGIC", "CHAYENNE_EXTERNAL_FRAME"],
        "support_level": "STRUCTURAL_CONTEXT_WITH_PHASE_CONTROL",
        "support_summary": "VNCTIIN appears as context frame and can carry TIINNEF phase anchors or Chayenne-style frame material.",
        "blocked_overreach": "Do not treat VNCTIIN-only books as payload-open books unless C86 is present.",
        "next_probe": "Separate VNCTIIN-only context, VNCTIIN+TIINNEF phase, and Chayenne-frame VNCTIIN contexts.",
    },
    {
        "bridge_id": "B_O23_VNCTIIN_ENDPOINT_CONTEXT",
        "target_family": "O23_VNCTIIN_ENDPOINT",
        "anchor_ids": ["AWB_469_LANGUAGE_MATHEMAGIC", "GREAT_CALCULATOR_GATHER_LANGUAGE"],
        "support_level": "STRUCTURAL_ENDPOINT_WITH_NEGATIVE_CONTROL",
        "support_summary": "Book13 combines VNCTIIN context with direct O23/ONAF/VEINLETFNAAST endpoint payload; Books12/21 lack those markers.",
        "blocked_overreach": "Do not import O23 endpoint semantics into books without direct O23/ONAF/FNAAST markers.",
        "next_probe": "Use Books13/38 as direct endpoint controls and keep Books12/21 terminal readings separate.",
    },
]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_c86_vnctiin_bridge_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            anchor_run_id INTEGER NOT NULL,
            bridge_count INTEGER NOT NULL,
            promoted_gloss_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_c86_vnctiin_bridge_v1_items (
            run_id INTEGER NOT NULL,
            bridge_id TEXT NOT NULL,
            target_family TEXT NOT NULL,
            anchor_ids_json TEXT NOT NULL,
            support_level TEXT NOT NULL,
            support_summary TEXT NOT NULL,
            blocked_overreach TEXT NOT NULL,
            next_probe TEXT NOT NULL,
            anchor_evidence_json TEXT NOT NULL,
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
    anchors = {
        row["anchor_id"]: dict(row)
        for row in conn.execute(
            "SELECT * FROM human_ingame_anchor_corpus_v1_items WHERE run_id=?",
            (anchor_run_id,),
        ).fetchall()
    }
    cur = conn.execute(
        """
        INSERT INTO human_c86_vnctiin_bridge_v1_runs
        (created_at, decision, anchor_run_id, bridge_count,
         promoted_gloss_count, payload_json)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            now(),
            "HUMAN_C86_VNCTIIN_BRIDGES_READY_NO_GLOSS",
            anchor_run_id,
            len(BRIDGES),
            0,
            json.dumps({"principle": "split context/payload/branch/endpoint before prose"}, ensure_ascii=False, sort_keys=True),
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
            INSERT INTO human_c86_vnctiin_bridge_v1_items
            (run_id, bridge_id, target_family, anchor_ids_json,
             support_level, support_summary, blocked_overreach,
             next_probe, anchor_evidence_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            ),
        )

    conn.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": "HUMAN_C86_VNCTIIN_BRIDGES_READY_NO_GLOSS",
                "bridge_count": len(BRIDGES),
                "promoted_gloss_count": 0,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
