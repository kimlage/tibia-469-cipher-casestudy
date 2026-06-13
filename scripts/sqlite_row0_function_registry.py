#!/usr/bin/env python3
"""Build/update a functional registry for row0 evidence without plaintext gloss."""

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
        CREATE TABLE IF NOT EXISTS row0_function_registry_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            function_count INTEGER NOT NULL,
            strong_count INTEGER NOT NULL,
            ready_count INTEGER NOT NULL,
            context_frame_count INTEGER NOT NULL,
            audit_only_count INTEGER NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS row0_function_registry (
            registry_run_id INTEGER NOT NULL,
            function_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            family TEXT NOT NULL,
            function_label TEXT NOT NULL,
            function_kind TEXT NOT NULL,
            status TEXT NOT NULL,
            scope TEXT NOT NULL,
            hard_decode_action TEXT NOT NULL,
            gloss_allowed INTEGER NOT NULL DEFAULT 0,
            occurrence_count INTEGER,
            book_count INTEGER,
            confidence_score REAL,
            confidence_class TEXT NOT NULL,
            current_decision TEXT NOT NULL,
            next_action TEXT NOT NULL,
            promotion_gate TEXT NOT NULL,
            abandon_gate TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            contradiction_json TEXT NOT NULL DEFAULT '{}',
            payload_json TEXT NOT NULL,
            PRIMARY KEY (registry_run_id, function_id)
        );

        CREATE TABLE IF NOT EXISTS row0_function_evidence (
            registry_run_id INTEGER NOT NULL,
            evidence_id INTEGER NOT NULL,
            function_id TEXT NOT NULL,
            source_table TEXT NOT NULL,
            source_run_id INTEGER,
            source_item_key TEXT,
            evidence_kind TEXT NOT NULL,
            metric_name TEXT,
            metric_value TEXT,
            summary TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (registry_run_id, evidence_id)
        );
        """
    )


def latest(conn: sqlite3.Connection, table: str) -> sqlite3.Row | None:
    try:
        return conn.execute(f"SELECT * FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    except sqlite3.OperationalError:
        return None


def insert_function(
    conn: sqlite3.Connection,
    registry_run_id: int,
    now: str,
    *,
    function_id: str,
    family: str,
    function_label: str,
    function_kind: str,
    status: str,
    scope: str,
    hard_decode_action: str,
    occurrence_count: int | None,
    book_count: int | None,
    confidence_score: float,
    confidence_class: str,
    current_decision: str,
    next_action: str,
    promotion_gate: str,
    abandon_gate: str,
    evidence: dict[str, Any],
    contradiction: dict[str, Any] | None = None,
    payload: dict[str, Any] | None = None,
) -> None:
    conn.execute(
        """
        INSERT INTO row0_function_registry
            (registry_run_id, function_id, created_at, updated_at, family, function_label,
             function_kind, status, scope, hard_decode_action, gloss_allowed,
             occurrence_count, book_count, confidence_score, confidence_class,
             current_decision, next_action, promotion_gate, abandon_gate,
             evidence_json, contradiction_json, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            registry_run_id,
            function_id,
            now,
            now,
            family,
            function_label,
            function_kind,
            status,
            scope,
            hard_decode_action,
            occurrence_count,
            book_count,
            confidence_score,
            confidence_class,
            current_decision,
            next_action,
            promotion_gate,
            abandon_gate,
            jdump(evidence),
            jdump(contradiction or {}),
            jdump(payload or {}),
        ),
    )


def add_evidence(
    conn: sqlite3.Connection,
    registry_run_id: int,
    evidence_id: int,
    function_id: str,
    source_table: str,
    source_run_id: int | None,
    evidence_kind: str,
    summary: str,
    metric_name: str | None = None,
    metric_value: str | None = None,
    source_item_key: str | None = None,
    payload: dict[str, Any] | None = None,
) -> int:
    conn.execute(
        """
        INSERT INTO row0_function_evidence
            (registry_run_id, evidence_id, function_id, source_table, source_run_id,
             source_item_key, evidence_kind, metric_name, metric_value, summary, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            registry_run_id,
            evidence_id,
            function_id,
            source_table,
            source_run_id,
            source_item_key,
            evidence_kind,
            metric_name,
            metric_value,
            summary,
            jdump(payload or {}),
        ),
    )
    return evidence_id + 1


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)
    now = utc_now()

    source = {
        "row0": latest(conn, "row0_code_symbol_probe_runs"),
        "star": latest(conn, "star_boundary_probe_runs"),
        "ltast": latest(conn, "ltast_boundary_probe_runs"),
        "benna": latest(conn, "benna_concordance_probe_runs"),
        "naese": latest(conn, "naese_ivifast_slot_probe_runs"),
        "variant": latest(conn, "variant_frame_probe_runs"),
        "vinvin": latest(conn, "vinvin_vtlr_cross_contig_probe_runs"),
    }

    cur = conn.execute(
        """
        INSERT INTO row0_function_registry_runs
            (created_at, function_count, strong_count, ready_count,
             context_frame_count, audit_only_count, decision, payload_json)
        VALUES (?, 0, 0, 0, 0, 0, ?, ?)
        """,
        (now, "PENDING", "{}"),
    )
    run_id = int(cur.lastrowid)

    row0 = source["row0"]
    if row0:
        insert_function(
            conn,
            run_id,
            now,
            function_id="ROW0_CODE_SYMBOL",
            family="row0_core",
            function_label="code_symbol_reconstruction",
            function_kind="validated_mechanical_substrate",
            status="VALIDATED_MECHANICAL",
            scope="all_books",
            hard_decode_action="use_as_primary_mechanical_stream",
            occurrence_count=int(row0["total_base_symbols"]),
            book_count=int(row0["valid_books"]),
            confidence_score=1.0 if int(row0["conflicting_codes"]) == 0 else 0.5,
            confidence_class="strong",
            current_decision=row0["decision"],
            next_action="build_functional_layer_on_row0_only",
            promotion_gate="already mechanical substrate; no plaintext gloss",
            abandon_gate="any code-symbol conflict or invalid book appears",
            evidence=dict(row0),
        )
    star = source["star"]
    if star:
        insert_function(
            conn,
            run_id,
            now,
            function_id="STAR_00",
            family="star_boundary",
            function_label="boundary_or_scope_operator",
            function_kind="boundary_operator",
            status="FUNCTION_STRONG",
            scope="row0_symbol_stream",
            hard_decode_action="segment_boundary_operator",
            occurrence_count=int(star["star_count"]),
            book_count=int(star["star_books"]),
            confidence_score=0.95,
            confidence_class="strong",
            current_decision=star["decision"],
            next_action="use_for_segmentation_not_translation",
            promotion_gate="preserve as operator with no gloss",
            abandon_gate="contexts become random under variant-aware audit",
            evidence=dict(star),
        )
    ltast = source["ltast"]
    if ltast:
        insert_function(
            conn,
            run_id,
            now,
            function_id="LTAST_TAIL",
            family="ltast_boundary",
            function_label="boundary_continuation_tail",
            function_kind="continuation_operator",
            status="FUNCTION_STRONG",
            scope="template_tail_crossing",
            hard_decode_action="mark_tail_continuation_after_boundary",
            occurrence_count=int(ltast["tail_count"]),
            book_count=int(ltast["tail_count"]),
            confidence_score=float(ltast["score"]) / 100.0,
            confidence_class="strong",
            current_decision=ltast["decision"],
            next_action="use_as boundary continuation control",
            promotion_gate="pair_coverage/delta/right_context remain invariant",
            abandon_gate="unpaired tails become dominant",
            evidence=dict(ltast),
        )
    benna = source["benna"]
    if benna:
        insert_function(
            conn,
            run_id,
            now,
            function_id="BENNA_FORMULA",
            family="benna",
            function_label="concordance_anchor_formula_bridge",
            function_kind="formula_frame",
            status="FUNCTION_READY",
            scope="prefix_suffix_concordance",
            hard_decode_action="classify_concordance_context",
            occurrence_count=int(benna["occurrence_count"]),
            book_count=int(benna["book_count"]),
            confidence_score=0.82,
            confidence_class="ready",
            current_decision=benna["decision"],
            next_action="contrast_core_vs_ltast_tail",
            promotion_gate="core/suffix concordance survives holdout",
            abandon_gate="classes collapse into unrelated suffixes",
            evidence=dict(benna),
        )
    naese = source["naese"]
    if naese:
        insert_function(
            conn,
            run_id,
            now,
            function_id="NAESE_IVIFAST",
            family="naese_ivifast",
            function_label="slot_template_anchor",
            function_kind="slot_anchor",
            status="FUNCTION_READY",
            scope="slot_family_c68_dominant",
            hard_decode_action="classify_slots_before_function_inference",
            occurrence_count=int(naese["occurrence_count"]),
            book_count=int(naese["book_count"]),
            confidence_score=0.80,
            confidence_class="ready",
            current_decision=naese["decision"],
            next_action="compare_clean_exemplars_against_suffix_variants",
            promotion_gate="slot classes reduce contradiction without gloss",
            abandon_gate="prefix/suffix classes become random",
            evidence=dict(naese),
        )
    variant = source["variant"]
    if variant:
        frame_rows = conn.execute(
            """
            SELECT frame_key, role_class, occurrence_count, book_count, next_action
            FROM variant_frame_items
            WHERE run_id=?
            ORDER BY frame_key
            """,
            (int(variant["run_id"]),),
        ).fetchall()
        for row in frame_rows:
            status = "AUDIT_ONLY" if row["role_class"] == "singleton_audit_only" else "CONTEXT_FRAME"
            score = 0.2 if status == "AUDIT_ONLY" else min(0.75, 0.45 + (int(row["book_count"]) / 40.0))
            insert_function(
                conn,
                run_id,
                now,
                function_id=f"FRAME_{row['frame_key']}",
                family="variant_frames",
                function_label=row["frame_key"].lower(),
                function_kind=row["role_class"],
                status=status,
                scope="local_variant_frame",
                hard_decode_action="preserve_variant_frame_no_global_symbol_gloss",
                occurrence_count=int(row["occurrence_count"]),
                book_count=int(row["book_count"]),
                confidence_score=score,
                confidence_class="audit" if status == "AUDIT_ONLY" else "context",
                current_decision="VARIANT_LOCAL_FRAMES_READY",
                next_action=row["next_action"],
                promotion_gate="only as local frame, never as global symbol meaning",
                abandon_gate="singleton/no recurrence or conflict with stronger frame",
                evidence=dict(row),
            )
    vinvin = source["vinvin"]
    if vinvin:
        status = (
            "FUNCTION_READY"
            if vinvin["decision"] == "VINVIN_VTLR_CROSS_CONTIG_FUNCTION_CANDIDATE"
            else "DISTRIBUTED_TEMPLATE"
        )
        insert_function(
            conn,
            run_id,
            now,
            function_id="VINVIN_VTLR",
            family="vinvin_vtlr",
            function_label="cross_contig_distributed_function_candidate",
            function_kind="distributed_template_or_function_frame",
            status=status,
            scope="cross_contig_overlap_frame",
            hard_decode_action="contrast_suffix_branches_under_contig_support",
            occurrence_count=int(vinvin["occurrence_count"]),
            book_count=int(vinvin["book_count"]),
            confidence_score=0.84 if status == "FUNCTION_READY" else 0.65,
            confidence_class="ready" if status == "FUNCTION_READY" else "template",
            current_decision=vinvin["decision"],
            next_action="contrast_suffix_branches_and_negative_controls",
            promotion_gate="suffix branches controlled across independent contigs",
            abandon_gate="suffixes random or explained by larger formula only",
            evidence=dict(vinvin),
        )

    evidence_id = 1
    for function in conn.execute("SELECT function_id, evidence_json FROM row0_function_registry WHERE registry_run_id=?", (run_id,)):
        evidence = json.loads(function["evidence_json"] or "{}")
        source_run_id = evidence.get("run_id")
        evidence_id = add_evidence(
            conn,
            run_id,
            evidence_id,
            function["function_id"],
            source_table="mixed_probe_sources",
            source_run_id=int(source_run_id) if isinstance(source_run_id, int) else None,
            evidence_kind="registry_snapshot",
            metric_name="summary",
            metric_value=function["function_id"],
            summary=f"Functional registry snapshot for {function['function_id']}",
            payload=evidence,
        )

    counts = conn.execute(
        """
        SELECT
          COUNT(*) AS function_count,
          SUM(status='FUNCTION_STRONG') AS strong_count,
          SUM(status='FUNCTION_READY') AS ready_count,
          SUM(status='CONTEXT_FRAME') AS context_frame_count,
          SUM(status='AUDIT_ONLY') AS audit_only_count
        FROM row0_function_registry
        WHERE registry_run_id=?
        """,
        (run_id,),
    ).fetchone()
    conn.execute(
        """
        UPDATE row0_function_registry_runs
        SET function_count=?,
            strong_count=?,
            ready_count=?,
            context_frame_count=?,
            audit_only_count=?,
            decision=?,
            payload_json=?
        WHERE run_id=?
        """,
        (
            int(counts["function_count"]),
            int(counts["strong_count"] or 0),
            int(counts["ready_count"] or 0),
            int(counts["context_frame_count"] or 0),
            int(counts["audit_only_count"] or 0),
            "ROW0_FUNCTION_REGISTRY_READY",
            jdump({"gloss_allowed": False, "registry_semantics": "functional roles only"}),
            run_id,
        ),
    )
    conn.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": "ROW0_FUNCTION_REGISTRY_READY",
                "function_count": int(counts["function_count"]),
                "strong_count": int(counts["strong_count"] or 0),
                "ready_count": int(counts["ready_count"] or 0),
                "context_frame_count": int(counts["context_frame_count"] or 0),
                "audit_only_count": int(counts["audit_only_count"] or 0),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
