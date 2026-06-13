#!/usr/bin/env python3
"""Create source bridges for the combined NAESE/C68 slot and BENNA formula expansion."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

BRIDGES = [
    {
        "bridge_id": "B_NAESE_BENNA_COMPOSITE",
        "target_family": "NAESE_BENNA_COMPOSITE_FRAME",
        "anchor_ids": ["AWB_469_LANGUAGE_MATHEMAGIC", "HONEMINAS_FORMULA_PARALLEL"],
        "support_level": "STRUCTURAL_COMPOSITE_SLOT_TO_FORMULA_NO_GLOSS",
        "support_summary": "Books 5/9 have both NAESE-side and BENNA-side support, with negatives rejected.",
        "blocked_overreach": "Do not translate NAESE or BENNA as words; keep the reading as a slot-to-formula composite frame.",
        "next_probe": "Use Books 5/9 as composite controls against clean NAESE slots, BENNA formula bodies, and O23/C86 negatives.",
    },
    {
        "bridge_id": "B_NAESE_CANONICAL_SLOT",
        "target_family": "NAESE_CANONICAL_SLOT",
        "anchor_ids": ["AWB_469_LANGUAGE_MATHEMAGIC", "GREAT_CALCULATOR_GATHER_LANGUAGE"],
        "support_level": "STRUCTURAL_SLOT_CLASSIFIER_WITH_HOLDOUT",
        "support_summary": "NAESE/C68/FATCT survives as a local slot classifier with external holdout support, but no prose gloss.",
        "blocked_overreach": "Do not promote a broad NAESE meaning; canonical windows remain structural slot windows.",
        "next_probe": "Keep Book22 as clean slot witness and compare against variants 28/48 plus weak hybrid Book42.",
    },
    {
        "bridge_id": "B_NAESE_VARIANT_WINDOW",
        "target_family": "NAESE_VARIANT_WINDOW",
        "anchor_ids": ["AWB_469_LANGUAGE_MATHEMAGIC", "GREAT_CALCULATOR_GATHER_LANGUAGE"],
        "support_level": "STRUCTURAL_VARIANT_WINDOW_NO_PROSE",
        "support_summary": "Books 28/48 form a contained NAESE variant window; related to canonical slot but not edge-supported.",
        "blocked_overreach": "Do not collapse variant windows into the canonical slot or assign phrase-level translation.",
        "next_probe": "Use 28/48 as variant controls for the NAESE slot family.",
    },
    {
        "bridge_id": "B_NAESE_WEAK_HYBRID_AUDIT",
        "target_family": "NAESE_WEAK_HYBRID_AUDIT",
        "anchor_ids": ["AWB_469_LANGUAGE_MATHEMAGIC", "GREAT_CALCULATOR_GATHER_LANGUAGE"],
        "support_level": "WEAK_SLOT_HYBRID_AUDIT_NO_PROMOTION",
        "support_summary": "Book42 is a hybrid handoff/weak slot boundary and stays audit-only.",
        "blocked_overreach": "Do not treat weak or mixed NAESE surfaces as clean slot witnesses.",
        "next_probe": "Hold Book42 until a stronger branch or slot control resolves the hybrid boundary.",
    },
    {
        "bridge_id": "B_BENNA_C86_VNCTIIN_FORMULA_HANDOFF",
        "target_family": "BENNA_C86_VNCTIIN_FORMULA_HANDOFF",
        "anchor_ids": ["AWB_469_LANGUAGE_MATHEMAGIC", "HONEMINAS_FORMULA_PARALLEL", "CHAYENNE_EXTERNAL_FRAME"],
        "support_level": "STRUCTURAL_FORMULA_HANDOFF_TO_CONTEXT",
        "support_summary": "Books 10/35 combine clean BENNA+LTAST formula tail evidence with C86/VNCTIIN context handoff.",
        "blocked_overreach": "Do not turn BENNA, C86, VNCTIIN, or LTAST into lexical words; keep the handoff structural.",
        "next_probe": "Contrast 10/35 against clean BENNA local bodies and C86/VNCTIIN payload corridor books.",
    },
    {
        "bridge_id": "B_BENNA_FORMULA_BODY",
        "target_family": "BENNA_FORMULA_BODY",
        "anchor_ids": ["AWB_469_LANGUAGE_MATHEMAGIC", "HONEMINAS_FORMULA_PARALLEL"],
        "support_level": "STRUCTURAL_FORMULA_BODY_NO_GLOSS",
        "support_summary": "Books 40/50/69 are BENNA formula body/local controls; Book69 is explicitly non-contig local evidence.",
        "blocked_overreach": "Do not infer a contig edge or plaintext formula from clean BENNA body evidence.",
        "next_probe": "Use 40/50/69 as formula-body controls and keep Book69 local unless a real edge appears.",
    },
]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_slot_formula_bridge_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            anchor_run_id INTEGER NOT NULL,
            benna_bridge_run_id INTEGER NOT NULL,
            c68_slot_run_id INTEGER NOT NULL,
            naese_core_run_id INTEGER NOT NULL,
            bridge_count INTEGER NOT NULL,
            promoted_gloss_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_slot_formula_bridge_v1_items (
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


def latest_optional(conn: sqlite3.Connection, table: str) -> int | None:
    row = conn.execute(f"SELECT max(run_id) AS run_id FROM {table}").fetchone()
    if row is None or row["run_id"] is None:
        return None
    return int(row["run_id"])


def rows(conn: sqlite3.Connection, sql: str, params: tuple[object, ...]) -> list[dict[str, object]]:
    return [dict(row) for row in conn.execute(sql, params).fetchall()]


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    anchor_run_id = max_id(conn, "human_ingame_anchor_corpus_v1_items")
    benna_bridge_run_id = max_id(conn, "benna_formula_bridge_gate_items")
    c68_slot_run_id = max_id(conn, "c68_fatct_slot_items")
    naese_core_run_id = max_id(conn, "naese_slot_core_v1_items")
    naese_benna_run_id = latest_optional(conn, "naese_benna_composite_probe_v1_items")
    benna_display_run_id = latest_optional(conn, "benna_display_variant_reassessment_v1_items")
    benna_69_run_id = latest_optional(conn, "benna_69_edge_resolution_v1_items")
    naese_subfamily_run_id = latest_optional(conn, "naese_slot_subfamily_v1_items")
    fnaast_naese_run_id = latest_optional(conn, "fnaast_naese_variant_narrow_promotions_v1_items")

    anchors = {
        row["anchor_id"]: dict(row)
        for row in conn.execute(
            "SELECT * FROM human_ingame_anchor_corpus_v1_items WHERE run_id=?",
            (anchor_run_id,),
        ).fetchall()
    }
    precheck = {
        "family": "BENNA/formula plus NAESE/C68 slot",
        "reason_selected": "largest named families remaining after atlas v4",
        "prior_failures": [
            "NAESE broad meaning rejected; slot classifier only",
            "BENNA formula bridge is formula-only; no lexical gloss",
            "Book42 weak/hybrid held as audit-only",
            "Book69 held local/non-contig despite clean BENNA evidence",
        ],
        "expected_failure_mode": "turning slot or formula frames into literal English prose",
        "why_this_run_is_different": "seed one combined layer so overlapping Book5/9 evidence is not split into conflicting readings",
        "benna_formula_bridge": rows(conn, "SELECT * FROM benna_formula_bridge_gate_items WHERE run_id=?", (benna_bridge_run_id,)),
        "c68_slot": rows(conn, "SELECT * FROM c68_fatct_slot_items WHERE run_id=?", (c68_slot_run_id,)),
        "naese_core": rows(conn, "SELECT * FROM naese_slot_core_v1_items WHERE run_id=?", (naese_core_run_id,)),
        "naese_benna_run_id": naese_benna_run_id,
        "benna_display_run_id": benna_display_run_id,
        "benna_69_run_id": benna_69_run_id,
        "naese_subfamily_run_id": naese_subfamily_run_id,
        "fnaast_naese_run_id": fnaast_naese_run_id,
    }

    cur = conn.execute(
        """
        INSERT INTO human_slot_formula_bridge_v1_runs
        (created_at, decision, anchor_run_id, benna_bridge_run_id,
         c68_slot_run_id, naese_core_run_id, bridge_count,
         promoted_gloss_count, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            now(),
            "HUMAN_SLOT_FORMULA_BRIDGES_READY_NO_GLOSS",
            anchor_run_id,
            benna_bridge_run_id,
            c68_slot_run_id,
            naese_core_run_id,
            len(BRIDGES),
            0,
            json.dumps({"principle": "slot/formula composite readings stay structural and shadow-only"}, ensure_ascii=False, sort_keys=True),
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
            INSERT INTO human_slot_formula_bridge_v1_items
            (run_id, bridge_id, target_family, anchor_ids_json,
             support_level, support_summary, blocked_overreach,
             next_probe, anchor_evidence_json, precheck_json)
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
                "decision": "HUMAN_SLOT_FORMULA_BRIDGES_READY_NO_GLOSS",
                "bridge_count": len(BRIDGES),
                "promoted_gloss_count": 0,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
