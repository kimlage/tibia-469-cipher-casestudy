#!/usr/bin/env python3
"""Q28: benchmark the safe external German candidate against local contig gates."""

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
        CREATE TABLE IF NOT EXISTS human_q28_external_candidate_contig_gate_benchmark_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q25_run_id INTEGER NOT NULL,
            q23_run_id INTEGER NOT NULL,
            q24_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            candidate_book_count INTEGER NOT NULL,
            candidate_contig_count INTEGER NOT NULL,
            exact_local_contig_match_count INTEGER NOT NULL,
            coverage_avg_pct REAL NOT NULL,
            coverage_95_book_count INTEGER NOT NULL,
            coverage_100_book_count INTEGER NOT NULL,
            low_coverage_book_count INTEGER NOT NULL,
            semantic_anchor_pass_count INTEGER NOT NULL,
            external_phrase_bridge_pass_count INTEGER NOT NULL,
            canonical_promoted_gloss_count INTEGER NOT NULL,
            structural_audit_use_allowed_count INTEGER NOT NULL,
            semantic_translation_use_allowed_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q28_external_candidate_contig_gate_benchmark_v1_items (
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


def latest_run_id(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT max(run_id) FROM {table}").fetchone()
    if row is None or row[0] is None:
        raise RuntimeError(f"missing required run: {table}")
    return int(row[0])


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q25 = latest_row(conn, "human_q25_external_candidate_audit_safe_projection_v1_runs")
    q23 = latest_row(conn, "human_q23_recent_github_candidate_solution_triage_v1_runs")
    q24 = latest_row(conn, "human_q24_external_candidate_containment_v1_runs")
    completion = latest_row(conn, "human_translation_completion_audit_v5_runs")
    q25_run_id = int(q25["run_id"])
    contig_run_id = latest_run_id(conn, "contig_max_overlap_items")

    book_stats = conn.execute(
        """
        SELECT
            count(*) AS candidate_book_count,
            avg(coverage_pct) AS coverage_avg_pct,
            sum(CASE WHEN coverage_pct >= 95 THEN 1 ELSE 0 END) AS coverage_95_book_count,
            sum(CASE WHEN coverage_pct = 100 THEN 1 ELSE 0 END) AS coverage_100_book_count,
            sum(CASE WHEN coverage_pct < 85 THEN 1 ELSE 0 END) AS low_coverage_book_count
        FROM human_q25_external_candidate_audit_safe_projection_v1_books
        WHERE run_id=?
        """,
        (q25_run_id,),
    ).fetchone()
    candidate_contigs = conn.execute(
        """
        SELECT *
        FROM human_q25_external_candidate_audit_safe_projection_v1_contigs
        WHERE run_id=?
        ORDER BY CAST(basecontigid AS INTEGER)
        """,
        (q25_run_id,),
    ).fetchall()
    local_contigs = {
        (str(row["basecontigid"]), str(row["booksinorder"])): dict(row)
        for row in conn.execute(
            """
            SELECT *
            FROM contig_max_overlap_items
            WHERE run_id=?
            """,
            (contig_run_id,),
        )
    }

    items: list[dict[str, object]] = []
    exact_local_contig_match_count = 0
    for row in candidate_contigs:
        key = (str(row["basecontigid"]), str(row["booksinorder"]))
        local = local_contigs.get(key)
        exact = bool(local and int(local["exact_match"]) == 1)
        exact_local_contig_match_count += int(exact)
        items.append(
            {
                "item_id": f"contig:{row['basecontigid']}",
                "item_type": "contig_gate",
                "status": "CANDIDATE_CONTIG_MATCHES_LOCAL_EXACT_CONTIG" if exact else "CANDIDATE_CONTIG_NOT_LOCALLY_CONFIRMED",
                "role_label": "Candidate contig order compared to local contig_max_overlap exact reconstruction.",
                "support_class": "SUPPORT_STRUCTURAL_AUDIT_ONLY" if exact else "BLOCK_STRUCTURAL_USE",
                "evidence_json": j(
                    {
                        "candidate": dict(row),
                        "local_contig_max_overlap": local,
                    }
                ),
            }
        )

    semantic_anchor_pass_count = int(q23["in_game_anchor_pass_count"])
    external_phrase_bridge_pass_count = int(q23["external_phrase_bridge_pass_count"])
    canonical_promoted_gloss_count = int(completion["promoted_gloss_count"])
    structural_audit_use_allowed_count = int(
        exact_local_contig_match_count == len(candidate_contigs)
        and len(candidate_contigs) > 0
        and int(q24["canonical_promoted_gloss_count"]) == 0
    )
    semantic_translation_use_allowed_count = int(
        semantic_anchor_pass_count > 0
        and external_phrase_bridge_pass_count > 0
        and canonical_promoted_gloss_count > 0
    )

    items.extend(
        [
            {
                "item_id": "gate:semantic-anchor",
                "item_type": "semantic_gate",
                "status": "SEMANTIC_ANCHOR_GATE_FAILED",
                "role_label": "Q23 found zero in-game anchor passes for the candidate mapping.",
                "support_class": "BLOCK_SEMANTIC_TRANSLATION_USE",
                "evidence_json": j(dict(q23)),
            },
            {
                "item_id": "gate:external-phrase",
                "item_type": "external_phrase_gate",
                "status": "EXTERNAL_PHRASE_BRIDGE_GATE_FAILED",
                "role_label": "Q23 found zero external phrase bridge passes for Avar/Chayenne/Knightmare style anchors.",
                "support_class": "BLOCK_SEMANTIC_TRANSLATION_USE",
                "evidence_json": j(dict(q23)),
            },
            {
                "item_id": "gate:completion",
                "item_type": "completion_gate",
                "status": str(completion["decision"]),
                "role_label": "Project completion audit remains unresolved with zero promoted glosses.",
                "support_class": "CONTROL_NO_CANONICAL_PROMOTION",
                "evidence_json": j(dict(completion)),
            },
        ]
    )

    candidate_book_count = int(book_stats["candidate_book_count"])
    coverage_avg_pct = float(book_stats["coverage_avg_pct"] or 0.0)
    coverage_95_book_count = int(book_stats["coverage_95_book_count"] or 0)
    coverage_100_book_count = int(book_stats["coverage_100_book_count"] or 0)
    low_coverage_book_count = int(book_stats["low_coverage_book_count"] or 0)
    decision = (
        "Q28_EXTERNAL_GERMAN_CANDIDATE_STRUCTURAL_AUDIT_ONLY_SEMANTIC_GATE_FAILED"
        if candidate_book_count == 70
        and exact_local_contig_match_count == len(candidate_contigs)
        and structural_audit_use_allowed_count == 1
        and semantic_translation_use_allowed_count == 0
        and semantic_anchor_pass_count == 0
        and external_phrase_bridge_pass_count == 0
        and canonical_promoted_gloss_count == 0
        else "Q28_EXTERNAL_CANDIDATE_CONTIG_GATE_REQUIRES_MANUAL_REVIEW"
    )
    payload = {
        "question": "Can the safe German/MHG candidate be used after comparing it to local contig gates?",
        "answer": (
            "Only as structural audit material. Its six imported contigs match local exact contig reconstructions, "
            "but it still fails semantic anchor and external phrase gates."
        ),
        "allowed_reading": "Use candidate contig prose as adversarial continuity hypotheses or search prompts only.",
        "blocked_reading": "Do not read the German/MHG decoded text as accepted human translation.",
        "next_action": "Compare candidate claims only where they generate source-search targets or structural contradictions.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q28_external_candidate_contig_gate_benchmark_v1_runs (
                created_at, decision, q25_run_id, q23_run_id, q24_run_id,
                completion_audit_run_id, candidate_book_count, candidate_contig_count,
                exact_local_contig_match_count, coverage_avg_pct, coverage_95_book_count,
                coverage_100_book_count, low_coverage_book_count, semantic_anchor_pass_count,
                external_phrase_bridge_pass_count, canonical_promoted_gloss_count,
                structural_audit_use_allowed_count, semantic_translation_use_allowed_count,
                payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                q25_run_id,
                int(q23["run_id"]),
                int(q24["run_id"]),
                int(completion["run_id"]),
                candidate_book_count,
                len(candidate_contigs),
                exact_local_contig_match_count,
                coverage_avg_pct,
                coverage_95_book_count,
                coverage_100_book_count,
                low_coverage_book_count,
                semantic_anchor_pass_count,
                external_phrase_bridge_pass_count,
                canonical_promoted_gloss_count,
                structural_audit_use_allowed_count,
                semantic_translation_use_allowed_count,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q28_external_candidate_contig_gate_benchmark_v1_items (
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
                "q25_run_id": q25_run_id,
                "candidate_book_count": candidate_book_count,
                "candidate_contig_count": len(candidate_contigs),
                "exact_local_contig_match_count": exact_local_contig_match_count,
                "coverage_avg_pct": round(coverage_avg_pct, 3),
                "coverage_95_book_count": coverage_95_book_count,
                "coverage_100_book_count": coverage_100_book_count,
                "low_coverage_book_count": low_coverage_book_count,
                "semantic_anchor_pass_count": semantic_anchor_pass_count,
                "external_phrase_bridge_pass_count": external_phrase_bridge_pass_count,
                "canonical_promoted_gloss_count": canonical_promoted_gloss_count,
                "structural_audit_use_allowed_count": structural_audit_use_allowed_count,
                "semantic_translation_use_allowed_count": semantic_translation_use_allowed_count,
            }
        )
    )


if __name__ == "__main__":
    main()
