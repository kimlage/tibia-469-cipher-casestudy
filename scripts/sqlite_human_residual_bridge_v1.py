#!/usr/bin/env python3
"""Create source bridges for residual human shadow readings."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

BRIDGES = [
    {
        "bridge_id": "B_RESIDUAL_DISPLAY_DRIFT",
        "target_family": "DISPLAY_DRIFT_RESIDUAL",
        "anchor_ids": ["AWB_469_LANGUAGE_MATHEMAGIC", "GREAT_CALCULATOR_GATHER_LANGUAGE"],
        "support_level": "AUDIT_DISPLAY_DRIFT_NO_PROSE",
        "support_summary": "BTII/NSBVN/ATFNAAST display-drift blocks are book-scoped residuals, not clean lexical witnesses.",
        "blocked_overreach": "Do not turn display-drift blocks into readable English or global FNAAST/BTII meanings.",
        "next_probe": "Use 11/32/36/43 as display-drift audit controls against BENNA and FNAAST formula bodies.",
    },
    {
        "bridge_id": "B_RESIDUAL_LOCAL_PAIR",
        "target_family": "LOCAL_PAIR_RESIDUAL",
        "anchor_ids": ["AWB_469_LANGUAGE_MATHEMAGIC", "GREAT_CALCULATOR_GATHER_LANGUAGE"],
        "support_level": "STRUCTURAL_LOCAL_PAIR_NO_GLOSS",
        "support_summary": "Zero-pair local contexts preserve pair/truncation and FAST/BEIE microtemplate relations.",
        "blocked_overreach": "Do not promote pair alignments as sentence translations.",
        "next_probe": "Keep 20 with Book54 and 25/39 as local-pair controls.",
    },
    {
        "bridge_id": "B_RESIDUAL_TEMPLATE_CLUSTER",
        "target_family": "RESIDUAL_TEMPLATE_CLUSTER",
        "anchor_ids": ["AWB_469_LANGUAGE_MATHEMAGIC", "GREAT_CALCULATOR_GATHER_LANGUAGE"],
        "support_level": "STRUCTURAL_TEMPLATE_ALIGNMENT_NO_GLOSS",
        "support_summary": "Residual template alignments attach books to stronger neighboring templates without proving prose.",
        "blocked_overreach": "Do not copy the neighboring book's reading as a translation.",
        "next_probe": "Contrast 1/18/47 against their matched books and reject copied gloss.",
    },
    {
        "bridge_id": "B_RESIDUAL_LTAST_BOUNDARY",
        "target_family": "LTAST_BOUNDARY_RESIDUAL",
        "anchor_ids": ["AWB_469_LANGUAGE_MATHEMAGIC", "CHAYENNE_EXTERNAL_FRAME"],
        "support_level": "STRUCTURAL_BOUNDARY_OPERATOR_NO_GLOSS",
        "support_summary": "LTAST/TTNVVN appears as boundary/handoff operator and must remain boundary-only.",
        "blocked_overreach": "Do not translate LTAST/TTNVVN or use it as a full sentence boundary gloss.",
        "next_probe": "Use 0/33 as LTAST boundary controls against Chayenne-frame and BENNA-tail books.",
    },
    {
        "bridge_id": "B_RESIDUAL_O23_FNAAST_ENDPOINT",
        "target_family": "O23_FNAAST_ENDPOINT_RESIDUAL",
        "anchor_ids": ["AWB_469_LANGUAGE_MATHEMAGIC", "GREAT_CALCULATOR_GATHER_LANGUAGE"],
        "support_level": "STRUCTURAL_ENDPOINT_COMPONENT_NO_GLOSS",
        "support_summary": "Book38 carries exact O23/ONAF/VEINLETFNAAST endpoint payload; Book56 shares a clean component with it.",
        "blocked_overreach": "Do not import O23 endpoint semantics into books without direct endpoint/component evidence.",
        "next_probe": "Keep 38 as endpoint payload and 56 as clean component/control.",
    },
    {
        "bridge_id": "B_RESIDUAL_469_METAFORMULA",
        "target_family": "469_MARKER_METAFORMULA_RESIDUAL",
        "anchor_ids": ["AWB_SELF_NAME_486486", "AWB_469_LANGUAGE_MATHEMAGIC"],
        "support_level": "SPECIAL_METAFORMULA_AUDIT_NO_GLOSS",
        "support_summary": "Book4 is marked as a 469 language-label or metaformula residual and mixes multiple operator families.",
        "blocked_overreach": "Do not treat the marker as a key that decodes the surrounding mixed surface.",
        "next_probe": "Use Book4 as a special metaformula audit case until an in-game label gives stronger constraints.",
    },
    {
        "bridge_id": "B_RESIDUAL_BOOK55_REPEAT",
        "target_family": "BOOK55_INTERNAL_REPEAT_RESIDUAL",
        "anchor_ids": ["AWB_469_LANGUAGE_MATHEMAGIC", "PARADOX_1_PLUS_1_KEYS"],
        "support_level": "STRUCTURAL_INTERNAL_REPEAT_NO_GLOSS",
        "support_summary": "Book55 has an internal VFETTIITAV repeat/variant frame but no accepted prose reading.",
        "blocked_overreach": "Do not treat the repeat as a refrain translation or dictionary entry.",
        "next_probe": "Use Book55 as internal-repeat control against Book49 repeat formula and local pair books.",
    },
    {
        "bridge_id": "B_RESIDUAL_CHAYENNE_NEAR_VARIANT",
        "target_family": "CHAYENNE_NEAR_VARIANT_RESIDUAL",
        "anchor_ids": ["CHAYENNE_EXTERNAL_FRAME", "AWB_469_LANGUAGE_MATHEMAGIC"],
        "support_level": "STRUCTURAL_NEAR_FRAME_NO_SINGLE_GLOSS",
        "support_summary": "Book41 has a Chayenne near-shape frame, but not an exact phrase translation.",
        "blocked_overreach": "Do not read Book41 as the Chayenne phrase; keep it as a near-frame witness.",
        "next_probe": "Compare Book41 against exact Chayenne-frame books 8/37/63/66.",
    },
    {
        "bridge_id": "B_RESIDUAL_NEIAAETTA_CONTINUITY",
        "target_family": "NEIAAETTA_CONTINUITY_RESIDUAL",
        "anchor_ids": ["AWB_469_LANGUAGE_MATHEMAGIC", "PARADOX_1_PLUS_1_KEYS"],
        "support_level": "STRUCTURAL_CONTINUITY_ONLY_NO_PHASE_GLOSS",
        "support_summary": "Book6 carries NEIAAETTA continuity without the Book7 TIINNEF phase anchor.",
        "blocked_overreach": "Do not import Book7 phase reading into Book6 without the phase anchor.",
        "next_probe": "Use Book6 as continuity-only control for the Book7 phase bridge.",
    },
    {
        "bridge_id": "B_RESIDUAL_UNIQUE_HEADER",
        "target_family": "UNIQUE_SCRAMBLED_HEADER_RESIDUAL",
        "anchor_ids": ["AWB_469_LANGUAGE_MATHEMAGIC", "GREAT_CALCULATOR_GATHER_LANGUAGE"],
        "support_level": "UNIQUE_HEADER_AUDIT_NO_PROMOTION",
        "support_summary": "Book34 has a unique prefix/header signature for scrambled assembly audit.",
        "blocked_overreach": "Do not normalize the unique header into a known family or prose line.",
        "next_probe": "Hold Book34 as a unique-header audit until an assembly relation appears.",
    },
]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_residual_bridge_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            anchor_run_id INTEGER NOT NULL,
            source_audit_run_id INTEGER NOT NULL,
            bridge_count INTEGER NOT NULL,
            promoted_gloss_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_residual_bridge_v1_items (
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
    source_audit_run_id = max_id(conn, "human_translation_completion_audit_v4_missing_books")
    anchors = {
        row["anchor_id"]: dict(row)
        for row in conn.execute(
            "SELECT * FROM human_ingame_anchor_corpus_v1_items WHERE run_id=?",
            (anchor_run_id,),
        ).fetchall()
    }
    missing = [
        dict(row)
        for row in conn.execute(
            "SELECT * FROM human_translation_completion_audit_v4_missing_books WHERE run_id=?",
            (source_audit_run_id,),
        ).fetchall()
    ]
    precheck = {
        "family": "residual human shadow routes",
        "reason_selected": "only books left outside atlas v5",
        "prior_failures": [
            "residuals are heterogeneous and weak for lexical inference",
            "several rows are explicitly audit-only or display-only",
            "some rows are local pair/template controls, not independent prose",
        ],
        "expected_failure_mode": "forcing heterogeneous residual controls into fluent but unsupported translations",
        "why_this_run_is_different": "assign each residual to an audit-safe route and block component gloss",
        "source_audit_missing": missing,
    }
    cur = conn.execute(
        """
        INSERT INTO human_residual_bridge_v1_runs
        (created_at, decision, anchor_run_id, source_audit_run_id,
         bridge_count, promoted_gloss_count, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            now(),
            "HUMAN_RESIDUAL_BRIDGES_READY_NO_GLOSS",
            anchor_run_id,
            source_audit_run_id,
            len(BRIDGES),
            0,
            json.dumps({"principle": "residual readings are route labels plus guarded shadow prose, not decoded plaintext"}, ensure_ascii=False, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)
    for bridge in BRIDGES:
        missing_anchor_ids = [anchor_id for anchor_id in bridge["anchor_ids"] if anchor_id not in anchors]
        if missing_anchor_ids:
            raise RuntimeError(f"missing anchors for {bridge['bridge_id']}: {missing_anchor_ids}")
        evidence = {anchor_id: anchors[anchor_id] for anchor_id in bridge["anchor_ids"]}
        conn.execute(
            """
            INSERT INTO human_residual_bridge_v1_items
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
                "decision": "HUMAN_RESIDUAL_BRIDGES_READY_NO_GLOSS",
                "bridge_count": len(BRIDGES),
                "promoted_gloss_count": 0,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
