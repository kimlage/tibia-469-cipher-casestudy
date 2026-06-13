#!/usr/bin/env python3
"""Synthesize Mathemagic operators with the human shadow route.

This keeps Mathemagic in the workflow as a source of selectors/operators and
guards against turning 1/13/49/94 into a plaintext dictionary.
"""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_mathemagic_shadow_synthesis_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            mathemagic_decision_run_id INTEGER NOT NULL,
            structural_synthesis_run_id INTEGER NOT NULL,
            hypothesis_count INTEGER NOT NULL,
            active_test_count INTEGER NOT NULL,
            guardrail_count INTEGER NOT NULL,
            accepted_human_gloss_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_mathemagic_shadow_synthesis_v1_items (
            run_id INTEGER NOT NULL,
            hypothesis_id TEXT NOT NULL,
            operator_or_anchor TEXT NOT NULL,
            human_shadow_evidence TEXT NOT NULL,
            status TEXT NOT NULL,
            implication TEXT NOT NULL,
            next_probe TEXT NOT NULL,
            rejection_rule TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, hypothesis_id)
        );
        """
    )


def max_id(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT max(run_id) AS run_id FROM {table}").fetchone()
    if row is None or row["run_id"] is None:
        raise RuntimeError(f"missing required run: {table}")
    return int(row["run_id"])


def fetch_one(conn: sqlite3.Connection, sql: str, params=()) -> dict[str, object]:
    row = conn.execute(sql, params).fetchone()
    if row is None:
        return {}
    return dict(row)


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    math_run_id = max_id(conn, "mathemagic_operational_decision_v1_runs")
    structural_run_id = max_id(conn, "mathemagic_structural_operator_synthesis_v1_runs")
    book49 = fetch_one(
        conn,
        "SELECT * FROM human_book49_repeat_shadow_probe_v1_runs ORDER BY run_id DESC LIMIT 1",
    )
    chayenne = fetch_one(
        conn,
        "SELECT * FROM human_chayenne_shape_shadow_probe_v1_runs ORDER BY run_id DESC LIMIT 1",
    )
    book30 = fetch_one(
        conn,
        "SELECT * FROM human_book30_family_shadow_probe_v1_runs ORDER BY run_id DESC LIMIT 1",
    )
    book12_21 = fetch_one(
        conn,
        "SELECT * FROM human_book12_21_tail_shadow_probe_v1_runs ORDER BY run_id DESC LIMIT 1",
    )
    frontier49 = fetch_one(
        conn,
        """
        SELECT *
        FROM post_mathemagic_frontier_selection_v1_items
        WHERE run_id=(SELECT max(run_id) FROM post_mathemagic_frontier_selection_v1_items)
          AND bookid='49'
        """,
    )

    hypotheses = [
        {
            "hypothesis_id": "MATH_49_REGISTER_SELECTOR_NOT_DICTIONARY",
            "operator_or_anchor": "+49/mod70 and Book49",
            "human_shadow_evidence": "Book49 is the corpus rank-1 repeat/formula witness; post-mathemagic links Book49 to Book28/NAESE variant as non-C86 frontier.",
            "status": "ACTIVE_TEST",
            "implication": "49 may be useful as a register/formula selector, but not as a word key or direct plaintext method.",
            "next_probe": "Compare +49/mod70-linked books against repeat/formula/register controls; require held-out improvement before any stronger claim.",
            "rejection_rule": "Reject if +49 relations do not predict repeat/register/function better than random or if they require prose gloss.",
            "evidence": {"book49": book49, "frontier49": frontier49},
        },
        {
            "hypothesis_id": "MATH_13_DELTA_LOCAL_GUARDRAIL",
            "operator_or_anchor": "13/delta13",
            "human_shadow_evidence": "Operational decision keeps 13 as local C86/C68 delta; Book12/21 tail probe has no direct O23 markers and should not import broad numeric semantics.",
            "status": "GUARDRAIL",
            "implication": "13 remains a local structural operator only; do not use it to translate endpoint/tail prose.",
            "next_probe": "Apply delta13 only inside C86/C68 vetted contexts and compare against controls before any human reading expansion.",
            "rejection_rule": "Reject broad 13 interpretations that cross families without improving held-out structural predictions.",
            "evidence": {"book12_21": book12_21},
        },
        {
            "hypothesis_id": "MATH_94_24_AUDIT_SELECTOR",
            "operator_or_anchor": "94->24",
            "human_shadow_evidence": "Mathemagic operational decision keeps 94->24 as audit/live-narrow selector pending falsification.",
            "status": "ACTIVE_TEST",
            "implication": "94->24 can rank candidates, but cannot produce human prose alone.",
            "next_probe": "Build a 94->24 candidate list and require non-circular in-game/functional improvement for any shadow reading.",
            "rejection_rule": "Reject if 94->24 only creates plausible stories or no local text/function change.",
            "evidence": {},
        },
        {
            "hypothesis_id": "MATHEMAGIC_REGISTER_FRAME_BRANCHING",
            "operator_or_anchor": "Chayenne external shape frame",
            "human_shadow_evidence": "The Chayenne block appears across four branches in v19: VNCTIIN, LTAST->VNCTIIN, residual continuation, BENNA/LTAST.",
            "status": "ACTIVE_TEST",
            "implication": "External mathemagic-like 469 may behave as a reusable register/frame, not a single fixed sentence.",
            "next_probe": "Search other external/NPC phrases for reusable shape frames that branch into multiple internal functions.",
            "rejection_rule": "Reject single-gloss readings for external frames that split across incompatible internal branches.",
            "evidence": {"chayenne": chayenne},
        },
        {
            "hypothesis_id": "MATHEMAGIC_SPINES_NOT_LINEAR_PROSE",
            "operator_or_anchor": "Book30 spine and formula families",
            "human_shadow_evidence": "Book30 family shares only VNSBLFSINNAI across 12/21/26/30; the rest is partial components and tails.",
            "status": "GUARDRAIL",
            "implication": "Human prose must describe spines/subfamilies first; continuous sentence translation is overfit.",
            "next_probe": "Convert more families into spine/tail/branch maps before drafting longer prose.",
            "rejection_rule": "Reject paraphrases that require all books in a family to share a full sentence core.",
            "evidence": {"book30": book30},
        },
    ]

    active_count = sum(1 for item in hypotheses if item["status"] == "ACTIVE_TEST")
    guardrail_count = sum(1 for item in hypotheses if item["status"] == "GUARDRAIL")
    decision = "HUMAN_MATHEMAGIC_SYNTHESIS_READY_OPERATORS_NOT_PLAINTEXT"
    payload = {
        "principle": "Mathemagic is operational hypothesis machinery, not a dictionary",
        "source_math_run_id": math_run_id,
        "source_structural_run_id": structural_run_id,
    }
    cur = conn.execute(
        """
        INSERT INTO human_mathemagic_shadow_synthesis_v1_runs
        (created_at, decision, mathemagic_decision_run_id,
         structural_synthesis_run_id, hypothesis_count, active_test_count,
         guardrail_count, accepted_human_gloss_count, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            now(),
            decision,
            math_run_id,
            structural_run_id,
            len(hypotheses),
            active_count,
            guardrail_count,
            0,
            json.dumps(payload, ensure_ascii=False, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)
    for item in hypotheses:
        conn.execute(
            """
            INSERT INTO human_mathemagic_shadow_synthesis_v1_items
            (run_id, hypothesis_id, operator_or_anchor, human_shadow_evidence,
             status, implication, next_probe, rejection_rule, evidence_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                item["hypothesis_id"],
                item["operator_or_anchor"],
                item["human_shadow_evidence"],
                item["status"],
                item["implication"],
                item["next_probe"],
                item["rejection_rule"],
                json.dumps(item["evidence"], ensure_ascii=False, sort_keys=True),
            ),
        )

    conn.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "hypothesis_count": len(hypotheses),
                "active_test_count": active_count,
                "guardrail_count": guardrail_count,
                "accepted_human_gloss_count": 0,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
