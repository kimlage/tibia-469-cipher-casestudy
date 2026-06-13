#!/usr/bin/env python3
"""Materialize conservative row0 subfunction policy from branch probes."""

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


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS row0_subfunction_policy_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_vinvin_branch_run_id INTEGER NOT NULL,
            source_leaent_run_id INTEGER NOT NULL,
            promoted_count INTEGER NOT NULL,
            audit_count INTEGER NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS row0_subfunction_policy_items (
            run_id INTEGER NOT NULL,
            subfunction_id TEXT NOT NULL,
            parent_function_id TEXT NOT NULL,
            policy_status TEXT NOT NULL,
            policy_confidence REAL NOT NULL,
            gloss_allowed INTEGER NOT NULL,
            evidence_summary TEXT NOT NULL,
            promotion_gate TEXT NOT NULL,
            abandon_gate TEXT NOT NULL,
            next_action TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, subfunction_id)
        );
        """
    )


def latest_id(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT run_id FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    if row is None:
        raise SystemExit(f"missing required table data: {table}")
    return int(row["run_id"])


def add_item(
    conn: sqlite3.Connection,
    run_id: int,
    subfunction_id: str,
    status: str,
    confidence: float,
    summary: str,
    evidence: dict[str, Any],
    next_action: str,
) -> None:
    conn.execute(
        """
        INSERT INTO row0_subfunction_policy_items
            (run_id, subfunction_id, parent_function_id, policy_status,
             policy_confidence, gloss_allowed, evidence_summary,
             promotion_gate, abandon_gate, next_action, evidence_json, payload_json)
        VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            subfunction_id,
            "VINVIN_VTLR",
            status,
            confidence,
            summary,
            "direct_or_contrastive_mechanical_support_and_no_gloss",
            "edge_loss_or_contrast_collapse_or_semantic_contradiction",
            next_action,
            jdump(evidence),
            jdump({"gloss_allowed": False, "evidence": evidence}),
        ),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)

    branch_run_id = latest_id(conn, "vinvin_branch_subfunction_probe_runs")
    leaent_run_id = latest_id(conn, "vinvin_leaent_vs_leafi_probe_runs")
    branch_rows = conn.execute(
        """
        SELECT *
        FROM vinvin_branch_subfunction_items
        WHERE run_id=?
        ORDER BY suffix_class
        """,
        (branch_run_id,),
    ).fetchall()
    leaent_run = conn.execute(
        """
        SELECT *
        FROM vinvin_leaent_vs_leafi_probe_runs
        WHERE run_id=?
        """,
        (leaent_run_id,),
    ).fetchone()

    cur = conn.execute(
        """
        INSERT INTO row0_subfunction_policy_runs
            (created_at, source_vinvin_branch_run_id, source_leaent_run_id,
             promoted_count, audit_count, decision, payload_json)
        VALUES (?, ?, ?, 0, 0, ?, ?)
        """,
        (utc_now(), branch_run_id, leaent_run_id, "PENDING", "{}"),
    )
    run_id = int(cur.lastrowid)

    promoted = 0
    audit = 0
    summaries: list[dict[str, Any]] = []
    by_suffix = {row["suffix_class"]: row for row in branch_rows}

    leaent_evidence = dict(json.loads(leaent_run["payload_json"] or "{}"))
    if leaent_run["decision"] == "LEAENT_BRANCH_READY_SURFACE61_LIMITED_NO_GLOSS":
        promoted += 1
        evidence = {
            "source_leaent_run_id": leaent_run_id,
            "decision": leaent_run["decision"],
            "contrast_score": float(leaent_run["contrast_score"]),
            "leaent_occurrence_count": int(leaent_run["leaent_occurrence_count"]),
            "leafi_occurrence_count": int(leaent_run["leafi_occurrence_count"]),
            "leaent_direct_edge_count": int(leaent_run["leaent_direct_edge_count"]),
            "leafi_direct_edge_count": int(leaent_run["leafi_direct_edge_count"]),
            "details": leaent_evidence,
        }
        add_item(
            conn,
            run_id,
            "VINVIN_BRANCH_INEIIVNSENI_STAR_LEAENT",
            "SUBFUNCTION_READY",
            0.86,
            "LEAENT branch survives LEAFI negative contrast; direct edge support is present but book 61 remains surface-only.",
            evidence,
            "render_as_vinvin_subfunction_no_plaintext",
        )
        summaries.append({"subfunction_id": "VINVIN_BRANCH_INEIIVNSENI_STAR_LEAENT", "status": "SUBFUNCTION_READY", "confidence": 0.86})

    tifav = by_suffix.get("TIFAVONAFIEI")
    if tifav and tifav["branch_status"] == "SUBFUNCTION_READY":
        promoted += 1
        evidence = {
            "source_vinvin_branch_run_id": branch_run_id,
            "suffix_class": "TIFAVONAFIEI",
            "branch_score": float(tifav["branch_score"]),
            "occurrence_count": int(tifav["occurrence_count"]),
            "book_count": int(tifav["book_count"]),
            "contig_supported_count": int(tifav["contig_supported_count"]),
            "o23_relation_count": int(tifav["o23_relation_count"]),
            "books": json.loads(tifav["books_json"] or "[]"),
        }
        add_item(
            conn,
            run_id,
            "VINVIN_BRANCH_TIFAVONAFIEI",
            "SUBFUNCTION_READY",
            0.84,
            "TIFAVONAFIEI branch is supported by contig 52->62 and embeds the independent O23_ONAF frame.",
            evidence,
            "render_as_vinvin_o23_subfunction_no_plaintext",
        )
        summaries.append({"subfunction_id": "VINVIN_BRANCH_TIFAVONAFIEI", "status": "SUBFUNCTION_READY", "confidence": 0.84})

    for suffix in ("INEIIVNSENI", "TIFA"):
        row = by_suffix.get(suffix)
        if not row:
            continue
        audit += 1
        subfunction_id = f"VINVIN_BRANCH_{suffix}_AUDIT"
        evidence = {
            "source_vinvin_branch_run_id": branch_run_id,
            "suffix_class": suffix,
            "branch_score": float(row["branch_score"]),
            "occurrence_count": int(row["occurrence_count"]),
            "book_count": int(row["book_count"]),
            "contig_supported_count": int(row["contig_supported_count"]),
            "books": json.loads(row["books_json"] or "[]"),
        }
        add_item(
            conn,
            run_id,
            subfunction_id,
            "AUDIT_OR_NEGATIVE_CONTROL",
            0.35,
            f"{suffix} remains a local/partial branch and should not be promoted.",
            evidence,
            "keep_as_negative_control",
        )
        summaries.append({"subfunction_id": subfunction_id, "status": "AUDIT_OR_NEGATIVE_CONTROL", "confidence": 0.35})

    decision = "ROW0_SUBFUNCTION_POLICY_READY" if promoted >= 2 else "ROW0_SUBFUNCTION_POLICY_PARTIAL"
    conn.execute(
        """
        UPDATE row0_subfunction_policy_runs
        SET promoted_count=?,
            audit_count=?,
            decision=?,
            payload_json=?
        WHERE run_id=?
        """,
        (promoted, audit, decision, jdump({"items": summaries, "gloss_allowed": False}), run_id),
    )
    conn.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "promoted_count": promoted,
                "audit_count": audit,
                "gloss_allowed": False,
                "items": summaries,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
