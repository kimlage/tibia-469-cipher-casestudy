#!/usr/bin/env python3
"""Reclassify the external German/MHG solution as a shadow/audit hypothesis.

Earlier materialization promoted it as an operational candidate because the
pair-level mechanics were strong. Subsequent audits found high semantic
overfit/contamination risk, so this script appends an explicit reclassification
without deleting any data.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "bonelord_operational.sqlite"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def jdump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def one(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> sqlite3.Row:
    row = conn.execute(sql, params).fetchone()
    if row is None:
        raise SystemExit(f"missing required row for query: {sql}")
    return row


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS external_hypothesis_reclassification_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            hypothesis_key TEXT NOT NULL,
            source_canonical_run_id INTEGER,
            source_german_run_id INTEGER NOT NULL,
            old_status TEXT,
            new_status TEXT NOT NULL,
            mechanical_confidence TEXT NOT NULL,
            semantic_confidence TEXT NOT NULL,
            overfit_risk TEXT NOT NULL,
            decision TEXT NOT NULL,
            reason TEXT NOT NULL,
            required_next_tests_json TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );
        """
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)

    german = one(conn, "SELECT * FROM german_candidate_runs ORDER BY run_id DESC LIMIT 1")
    canonical = conn.execute("SELECT * FROM canonical_candidate_runs ORDER BY run_id DESC LIMIT 1").fetchone()
    old_status = canonical["status"] if canonical else german["status"]

    required = [
        "holdout_by_book_without_manual_gloss",
        "random_baseline_same_letter_capacity",
        "phase_offset_test_for_odd_books",
        "unvalidated_code_33_w_audit",
        "anchor_demotion_enforced",
        "formula_level_tests_without_token_gloss",
    ]

    conn.execute(
        """
        INSERT INTO external_hypothesis_reclassification_runs
            (created_at, hypothesis_key, source_canonical_run_id, source_german_run_id,
             old_status, new_status, mechanical_confidence, semantic_confidence,
             overfit_risk, decision, reason, required_next_tests_json, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            utc_now(),
            "external_hypothesis_arturoornelasb_2026_03",
            canonical["run_id"] if canonical else None,
            german["run_id"],
            old_status,
            "SHADOW_AUDIT_MECHANICAL_CANDIDATE",
            "MEDIUM_HIGH",
            "LOW_MEDIUM",
            "MEDIUM_HIGH",
            "RECLASSIFY_FROM_ACTIVE_OPERATIONAL_TO_SHADOW_AUDIT",
            (
                "Pair-level mechanics are strong, but the German/English semantic "
                "solution shows manual insertion, anagram/fixup degrees of freedom, "
                "unconfirmed lore anchors and interpretive English glosses. Keep as "
                "shadow hypothesis until blind tests beat baselines."
            ),
            jdump(required),
            jdump(
                {
                    "preserve_tables": [
                        "german_candidate_*",
                        "canonical_candidate_*",
                        "german_semantic_*",
                    ],
                    "do_not_use_for": ["final_translation_claim", "semantic_solved_status"],
                    "use_for": ["mechanical_tests", "baseline_comparison", "formula_probe"],
                }
            ),
        ),
    )
    if canonical:
        conn.execute(
            """
            UPDATE canonical_candidate_runs
            SET status=?,
                promotion_decision=?,
                payload_json=?
            WHERE run_id=?
            """,
            (
                "SHADOW_AUDIT_MECHANICAL_CANDIDATE",
                "RETRACT_ACTIVE_PROMOTION_PENDING_BLIND_VALIDATION",
                jdump(
                    {
                        "source": "external hypothesis reclassification",
                        "reason": "semantic overfit/contamination risk",
                        "primary_decode_usable_for_shadow_tests": True,
                    }
                ),
                canonical["run_id"],
            ),
        )
    conn.execute(
        """
        UPDATE canonical_lineage_runs
        SET status=?,
            rationale=?,
            payload_json=?
        WHERE label=?
        """,
        (
            "SHADOW_AUDIT_MECHANICAL_CANDIDATE",
            "Reclassified after external-method audit: mechanically serious, semantically unproven.",
            jdump({"requires_blind_validation": True, "do_not_claim_solved": True}),
            "german_mhg_arturoornelasb_v1",
        ),
    )
    conn.commit()

    print(
        json.dumps(
            {
                "hypothesis_key": "external_hypothesis_arturoornelasb_2026_03",
                "source_german_run_id": int(german["run_id"]),
                "source_canonical_run_id": int(canonical["run_id"]) if canonical else None,
                "old_status": old_status,
                "new_status": "SHADOW_AUDIT_MECHANICAL_CANDIDATE",
                "required_next_tests": required,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
