#!/usr/bin/env python3
"""Bridge in-game anchors to current human shadow readings and probes."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"


BRIDGES = [
    {
        "bridge_id": "B_BOOK49_MATH49_REGISTER",
        "target_kind": "book",
        "target_id": "49",
        "anchor_ids": ["PARADOX_1_PLUS_1_KEYS", "AWB_469_LANGUAGE_MATHEMAGIC"],
        "shadow_claim": "Book49 is a self-contained repeat/formula witness and possible register selector.",
        "support_level": "MECHANICAL_PLUS_LORE_OPERATOR",
        "support_summary": "Book49 repeat rank 1 plus mathemagic keys route makes 49 useful as register/formula selector candidate.",
        "blocked_overreach": "49 is not a dictionary key and not a translated phrase.",
        "next_probe": "Compare +49/mod70 relations against repeat/register families and random controls.",
    },
    {
        "bridge_id": "B_BOOK7_PHASE_MATHEMAGIC",
        "target_kind": "book",
        "target_id": "7",
        "anchor_ids": ["AWB_469_LANGUAGE_MATHEMAGIC", "PARADOX_1_PLUS_1_KEYS"],
        "shadow_claim": "Book7 is a phase-continuity bridge rather than independent prose.",
        "support_level": "STRUCTURAL_WITH_METHOD_ANCHOR",
        "support_summary": "Book7 bridges NEIAAETTA continuity to TIINNEF phase controls; mathemagic lore supports operator/phase readings over prose.",
        "blocked_overreach": "No lexical reading for NEIAAETTA or TIINNEF.",
        "next_probe": "Test phase directionality around Books 6/7/19/31/57 and compare with mathemagic operator candidates.",
    },
    {
        "bridge_id": "B_BOOK30_SPINE_GREAT_CALCULATOR",
        "target_kind": "family",
        "target_id": "BOOK30_FAMILY_12_21_26_30",
        "anchor_ids": ["GREAT_CALCULATOR_GATHER_LANGUAGE", "HONEMINAS_FORMULA_PARALLEL"],
        "shadow_claim": "Book30-family readings should be spine/subfamily maps, not linear prose.",
        "support_level": "STRUCTURAL_PLUS_CORPUS_LORE",
        "support_summary": "Only VNSBLFSINNAI is shared by all four target books; Great Calculator/gathering lore supports compiled corpus behavior.",
        "blocked_overreach": "Do not infer a continuous sentence shared by all family books.",
        "next_probe": "Build additional family spine/tail maps and compare against compilation/anthology behavior.",
    },
    {
        "bridge_id": "B_BOOK12_21_NO_O23_IMPORT",
        "target_kind": "family",
        "target_id": "BOOK12_21_SHARED_BASE",
        "anchor_ids": ["GREAT_CALCULATOR_GATHER_LANGUAGE", "AWB_469_LANGUAGE_MATHEMAGIC"],
        "shadow_claim": "Books12/21 share a base with tail extension; endpoint wording must stay structural, not O23-derived.",
        "support_level": "NEGATIVE_CONTROL_PLUS_METHOD_ANCHOR",
        "support_summary": "Books12/21 share 69 symbols but have zero direct O23/ONAF/FNAAST markers; method anchors prefer structural constraints.",
        "blocked_overreach": "Do not import Books13/38 O23 endpoint semantics into Books12/21.",
        "next_probe": "Search TIVNSENI*LAELBEV tail in bridge/R02 families.",
    },
    {
        "bridge_id": "B_BOOK54_PAIR_LOCAL_SPINE",
        "target_kind": "book_pair",
        "target_id": "20/54",
        "anchor_ids": ["AWB_ZERO_TABOO", "AWB_469_LANGUAGE_MATHEMAGIC"],
        "shadow_claim": "Book54 is a shared local-pair spine with own tail, not just a preserved ending.",
        "support_level": "STRUCTURAL_WITH_ZERO_BOUNDARY_CONTEXT",
        "support_summary": "Book20/54 share LTFNTFEIFAIFAINIIETNEEIVN; zero/taboo lore remains only a boundary-context constraint.",
        "blocked_overreach": "Do not read the shared block as a word or as zero/taboo semantics.",
        "next_probe": "Test the shared block against other local-pair/zero-boundary contexts.",
    },
    {
        "bridge_id": "B_CHAYENNE_FRAME_REGISTER",
        "target_kind": "external_frame",
        "target_id": "CHAYENNE_REPLY_TO_BOOKS_8_37_63_66",
        "anchor_ids": ["CHAYENNE_EXTERNAL_FRAME", "AWB_469_LANGUAGE_MATHEMAGIC"],
        "shadow_claim": "Chayenne overlap is a reusable register/frame across branches, not one fixed sentence.",
        "support_level": "EXTERNAL_SHAPE_PLUS_BRANCH_TOPOLOGY",
        "support_summary": "AEFIEIEFIIVFAEATVAT appears in four branch contexts in Books 8/37/63/66.",
        "blocked_overreach": "Do not assign one English meaning to the shared block.",
        "next_probe": "Search for other external phrases that become multi-branch frames in the book corpus.",
    },
    {
        "bridge_id": "B_KNIGHTMARE_NAME_FORMULA_HOLDOUT",
        "target_kind": "external_phrase",
        "target_id": "KNIGHTMARE_PHRASE",
        "anchor_ids": ["KNIGHTMARE_3478_PHRASE", "AWB_SELF_NAME_486486"],
        "shadow_claim": "3478/name-related material should be treated as formula/name holdout.",
        "support_level": "SCOPED_NAME_ANCHOR_HOLDOUT",
        "support_summary": "486486 and 3478 support testing numeric names/formulas without component gloss.",
        "blocked_overreach": "Do not map 3478 to a fixed universal word without exact in-game proof.",
        "next_probe": "Compare 3478/486486/name anchors against row0 name/formula contexts.",
    },
    {
        "bridge_id": "B_AVAR_REGISTER_HOLDOUT",
        "target_kind": "external_phrase",
        "target_id": "AVAR_ORIGINAL_POEM",
        "anchor_ids": ["AVAR_TAR_POEM_REGISTER"],
        "shadow_claim": "Avar Tar is a register/poem comparator, not Hellgate plaintext.",
        "support_level": "REGISTER_HOLDOUT_ONLY",
        "support_summary": "Avar's long numeric poem can test style/register but source semantics are unreliable.",
        "blocked_overreach": "Do not use Avar Tar poem to promote book semantics.",
        "next_probe": "Compare Avar row0 projection against repeat/register profiles only.",
    },
]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_anchor_to_shadow_bridge_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            anchor_run_id INTEGER NOT NULL,
            bridge_count INTEGER NOT NULL,
            target_count INTEGER NOT NULL,
            promoted_gloss_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_anchor_to_shadow_bridge_v1_items (
            run_id INTEGER NOT NULL,
            bridge_id TEXT NOT NULL,
            target_kind TEXT NOT NULL,
            target_id TEXT NOT NULL,
            anchor_ids_json TEXT NOT NULL,
            shadow_claim TEXT NOT NULL,
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
    targets = sorted({item["target_id"] for item in BRIDGES})
    payload = {
        "principle": "bridges identify what an anchor can support and what it cannot support",
        "anchor_run_id": anchor_run_id,
    }
    cur = conn.execute(
        """
        INSERT INTO human_anchor_to_shadow_bridge_v1_runs
        (created_at, decision, anchor_run_id, bridge_count, target_count,
         promoted_gloss_count, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            now(),
            "HUMAN_ANCHOR_TO_SHADOW_BRIDGES_READY_NO_GLOSS",
            anchor_run_id,
            len(BRIDGES),
            len(targets),
            0,
            json.dumps(payload, ensure_ascii=False, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)
    for bridge in BRIDGES:
        missing = [anchor_id for anchor_id in bridge["anchor_ids"] if anchor_id not in anchors]
        if missing:
            raise RuntimeError(f"bridge {bridge['bridge_id']} references missing anchors: {missing}")
        evidence = {anchor_id: anchors[anchor_id] for anchor_id in bridge["anchor_ids"]}
        conn.execute(
            """
            INSERT INTO human_anchor_to_shadow_bridge_v1_items
            (run_id, bridge_id, target_kind, target_id, anchor_ids_json,
             shadow_claim, support_level, support_summary, blocked_overreach,
             next_probe, anchor_evidence_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                bridge["bridge_id"],
                bridge["target_kind"],
                bridge["target_id"],
                json.dumps(bridge["anchor_ids"], ensure_ascii=False, sort_keys=True),
                bridge["shadow_claim"],
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
                "decision": "HUMAN_ANCHOR_TO_SHADOW_BRIDGES_READY_NO_GLOSS",
                "anchor_run_id": anchor_run_id,
                "bridge_count": len(BRIDGES),
                "target_count": len(targets),
                "promoted_gloss_count": 0,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
