#!/usr/bin/env python3
"""Q24: contain the imported external German candidate as audit-only."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q24_external_candidate_containment_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q23_run_id INTEGER NOT NULL,
            external_candidate_run_id INTEGER NOT NULL,
            candidate_book_count INTEGER NOT NULL,
            candidate_contig_count INTEGER NOT NULL,
            candidate_promote_wording_count INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            canonical_promoted_gloss_count INTEGER NOT NULL,
            canonical_contamination_detected_count INTEGER NOT NULL,
            label_fix_required_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q24_external_candidate_containment_v1_items (
            run_id INTEGER NOT NULL,
            item_id TEXT NOT NULL,
            item_type TEXT NOT NULL,
            status TEXT NOT NULL,
            role_label TEXT NOT NULL,
            support_class TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, item_id)
        );
        """
    )


def latest_row(conn: sqlite3.Connection, table: str) -> sqlite3.Row:
    row = conn.execute(f"SELECT * FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    if row is None:
        raise RuntimeError(f"missing required table/run: {table}")
    return row


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q23 = latest_row(conn, "human_q23_recent_github_candidate_solution_triage_v1_runs")
    external_run = latest_row(conn, "external_candidate_solution_runs")
    completion = latest_row(conn, "human_translation_completion_audit_v5_runs")

    candidate_run_id = int(external_run["run_id"])
    candidate_book_count = int(
        conn.execute(
            "SELECT count(*) FROM canonical_candidate_books WHERE run_id=?",
            (candidate_run_id,),
        ).fetchone()[0]
    )
    candidate_contig_count = int(
        conn.execute(
            "SELECT count(*) FROM canonical_candidate_contigs WHERE run_id=?",
            (candidate_run_id,),
        ).fetchone()[0]
    )
    candidate_promote_wording_count = int(
        conn.execute(
            """
            SELECT count(*)
            FROM canonical_candidate_books
            WHERE run_id=? AND promotion_status LIKE 'PROMOTE%'
            """,
            (candidate_run_id,),
        ).fetchone()[0]
    )
    canonical_promoted_gloss_count = int(completion["promoted_gloss_count"])
    canonical_contamination_detected_count = int(canonical_promoted_gloss_count > 0)
    label_fix_required_count = int(candidate_promote_wording_count > 0)

    decision = (
        "Q24_EXTERNAL_GERMAN_CANDIDATE_CONTAINED_AS_AUDIT_ONLY_LABEL_FIX_REQUIRED_NO_PROMOTION"
        if candidate_book_count == 70
        and candidate_contig_count >= 1
        and candidate_promote_wording_count > 0
        and canonical_promoted_gloss_count == 0
        and canonical_contamination_detected_count == 0
        else "Q24_EXTERNAL_CANDIDATE_CONTAINMENT_REQUIRES_MANUAL_REVIEW"
    )

    items = [
        {
            "item_id": "candidate:existing-import",
            "item_type": "existing_candidate_import",
            "status": "EXTERNAL_CANDIDATE_ALREADY_IMPORTED",
            "role_label": "The recent German/MHG candidate already has local candidate tables.",
            "support_class": "SUPPORT_AUDIT_BENCHMARK_EXISTS",
            "evidence_json": j(
                {
                    "external_candidate_run": dict(external_run),
                    "candidate_book_count": candidate_book_count,
                    "candidate_contig_count": candidate_contig_count,
                }
            ),
        },
        {
            "item_id": "control:promote-wording",
            "item_type": "label_control",
            "status": "PROMOTE_WORDING_PRESENT_IN_CANDIDATE_TABLE",
            "role_label": "Candidate-local status labels use PROMOTE wording and must not be read as canonical promotion.",
            "support_class": "CONTROL_LABEL_FIX_REQUIRED",
            "evidence_json": j(
                {
                    "candidate_promote_wording_count": candidate_promote_wording_count,
                    "affected_table": "canonical_candidate_books",
                }
            ),
        },
        {
            "item_id": "control:completion-audit",
            "item_type": "completion_control",
            "status": str(completion["decision"]),
            "role_label": "The real completion audit still reports zero promoted glosses.",
            "support_class": "CONTROL_NO_CANONICAL_PROMOTION",
            "evidence_json": j(dict(completion)),
        },
        {
            "item_id": "policy:containment",
            "item_type": "containment_policy",
            "status": "AUDIT_ONLY_BENCHMARK_NO_HUMAN_SHADOW_IMPORT",
            "role_label": "External candidate translations cannot enter the human shadow layer until they pass anchor gates.",
            "support_class": "CONTROL_NO_PROMOTION",
            "evidence_json": j(
                {
                    "q23_decision": str(q23["decision"]),
                    "canonical_contamination_detected_count": canonical_contamination_detected_count,
                    "label_fix_required_count": label_fix_required_count,
                    "next_action": "Create a safe candidate benchmark view/table with AUDIT_ONLY labels before further comparison.",
                }
            ),
        },
    ]

    payload = {
        "question": "Did the imported external German candidate become a canonical or human-shadow translation?",
        "answer": (
            "No. It is present in local candidate tables, but the completion audit still has zero promoted glosses. "
            "However, candidate-local PROMOTE labels are misleading and require a containment/label-fix layer."
        ),
        "allowed_reading": "Use existing candidate rows only as audit benchmark data.",
        "blocked_reading": "Do not treat canonical_candidate_books.promotion_status as project canonical promotion.",
        "next_action": "Materialize an AUDIT_ONLY-safe candidate view/table before running comparisons.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q24_external_candidate_containment_v1_runs (
                created_at, decision, q23_run_id, external_candidate_run_id,
                candidate_book_count, candidate_contig_count,
                candidate_promote_wording_count, completion_audit_run_id,
                canonical_promoted_gloss_count, canonical_contamination_detected_count,
                label_fix_required_count, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                int(q23["run_id"]),
                candidate_run_id,
                candidate_book_count,
                candidate_contig_count,
                candidate_promote_wording_count,
                int(completion["run_id"]),
                canonical_promoted_gloss_count,
                canonical_contamination_detected_count,
                label_fix_required_count,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q24_external_candidate_containment_v1_items (
                run_id, item_id, item_type, status, role_label, support_class,
                evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    str(item["item_id"]),
                    str(item["item_type"]),
                    str(item["status"]),
                    str(item["role_label"]),
                    str(item["support_class"]),
                    str(item["evidence_json"]),
                )
                for item in items
            ],
        )

    print(
        j(
            {
                "run_id": run_id,
                "decision": decision,
                "q23_run_id": int(q23["run_id"]),
                "external_candidate_run_id": candidate_run_id,
                "candidate_book_count": candidate_book_count,
                "candidate_contig_count": candidate_contig_count,
                "candidate_promote_wording_count": candidate_promote_wording_count,
                "completion_audit_run_id": int(completion["run_id"]),
                "canonical_promoted_gloss_count": canonical_promoted_gloss_count,
                "canonical_contamination_detected_count": canonical_contamination_detected_count,
                "label_fix_required_count": label_fix_required_count,
            }
        )
    )


if __name__ == "__main__":
    main()
