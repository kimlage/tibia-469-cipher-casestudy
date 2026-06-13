#!/usr/bin/env python3
"""Q46: synthesize covered non-contig families into testable human hypotheses."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

FAMILY_ATLASES = {
    "BOOK30_FAMILY_SPINE_PACKET": {
        "atlas_table": "human_q38_book30_family_noncontig_atlas_v1_runs",
        "synthesis_role": "compiled formula-spine witness",
        "hypothesis_id": "H1_COMPILED_FORMULA_SPINE_AS_DOCUMENT_STRUCTURE",
        "hypothesis": "Recurring non-contig spines may mark compiled formula packets rather than word sequences.",
        "next_probe": "Compare VNSBLFSINNAI and TAESESTIEN tail behavior against non-target high-priority packets.",
        "accept_gate": "A held-out family preserves spine/tail roles without increasing contradiction count or gloss leakage.",
        "reject_gate": "Tail variants behave randomly or require assigning unsupported word meanings.",
    },
    "VNCTIIN_TIINNEF_PHASE_TRIO": {
        "atlas_table": "human_q39_vnctiin_tiinnef_phase_trio_atlas_v1_runs",
        "synthesis_role": "phase-context machinery",
        "hypothesis_id": "H2_PHASE_CONTEXT_BEFORE_SLOT_CLASSIFICATION",
        "hypothesis": "VNCTIIN/TIINNEF contexts may prepare or switch phase before later slot/classifier frames.",
        "next_probe": "Join Q39 phase-context books with Q43 NAESE/C68 slot books through shared C68/VNCTIIN neighborhoods.",
        "accept_gate": "Phase controls predict slot-window placement better than continuity-only controls.",
        "reject_gate": "Phase labels fail on held-out VNCTIIN books or collapse into generic context wording.",
    },
    "C86_VINVIN_BRANCH_TRIO": {
        "atlas_table": "human_q40_c86_vinvin_branch_trio_atlas_v1_runs",
        "synthesis_role": "selector/branch payload machinery",
        "hypothesis_id": "H3_BRANCH_SELECTOR_PAYLOAD_CHAIN",
        "hypothesis": "C86-opened VINVIN/VTLR/R20 shapes may select branch payload contexts outside exact contigs.",
        "next_probe": "Contrast C86/VINVIN books against Chayenne and NAESE families where C86/C68 sits near frame boundaries.",
        "accept_gate": "Selector behavior reduces ambiguity in at least one held-out branch without creating prose.",
        "reject_gate": "C86/VINVIN cannot distinguish branch payload from generic formula continuation.",
    },
    "BTII_NSBVN_ATFNAAST_DISPLAY_TRIO": {
        "atlas_table": "human_q41_display_drift_trio_atlas_v1_runs",
        "synthesis_role": "display/formula drift mask",
        "hypothesis_id": "H4_DISPLAY_DRIFT_MASK_BEFORE_PROSE",
        "hypothesis": "Some repeated residues are display or formula drift and must be masked before human prose is attempted.",
        "next_probe": "Apply display-only masks to residual books, then re-rank remaining human-readable surfaces.",
        "accept_gate": "Masking lowers fake clean prose and leaves fewer contradiction-heavy residuals.",
        "reject_gate": "Masking removes useful branch or slot evidence needed by Q39-Q44 comparators.",
    },
    "NAESE_C68_SLOT_VARIANT_TRIO": {
        "atlas_table": "human_q43_naese_c68_slot_variant_trio_atlas_v1_runs",
        "synthesis_role": "slot/classifier variant machinery",
        "hypothesis_id": "H5_SLOT_CLASSIFIER_VARIANT_CONTROL",
        "hypothesis": "NAESE/C68/FATCT surfaces may classify or bind variable units instead of spelling a word.",
        "next_probe": "Use Book 22 as ordered-core control and Books 28/48 as variant windows against C68-near residuals.",
        "accept_gate": "Ordered-core versus variant-window behavior predicts held-out C68 placement without component gloss.",
        "reject_gate": "Variants require collapsing into a single NAESE/C68 word meaning.",
    },
    "CHAYENNE_REGISTER_FRAME_SET": {
        "atlas_table": "human_q44_chayenne_register_frame_atlas_v1_runs",
        "synthesis_role": "external register-frame holdout",
        "hypothesis_id": "H6_EXTERNAL_REGISTER_FRAME_HOLDOUT",
        "hypothesis": "External 469 phrases can constrain reusable register frames while remaining quarantined from plaintext translation.",
        "next_probe": "Use Chayenne-frame books as holdouts for branch/register behavior and keep Book 63 as residual audit control.",
        "accept_gate": "The external frame continues to split by internal branch context and never needs an explicit Chayenne gloss.",
        "reject_gate": "A trusted primary source supplies an exact Chayenne sequence with explicit meaning that contradicts frame-only use.",
    },
}


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q46_family_synthesis_hypothesis_queue_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q45_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            atlas_family_count INTEGER NOT NULL,
            hypothesis_count INTEGER NOT NULL,
            source_quarantined_count INTEGER NOT NULL,
            component_gloss_allowed_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q46_family_synthesis_hypothesis_queue_v1_items (
            run_id INTEGER NOT NULL,
            priority INTEGER NOT NULL,
            frontier_id TEXT NOT NULL,
            bookids_json TEXT NOT NULL,
            atlas_table TEXT NOT NULL,
            atlas_run_id INTEGER NOT NULL,
            atlas_decision TEXT NOT NULL,
            synthesis_role TEXT NOT NULL,
            family_human_version TEXT NOT NULL,
            hypothesis_id TEXT NOT NULL,
            hypothesis TEXT NOT NULL,
            next_probe TEXT NOT NULL,
            accept_gate TEXT NOT NULL,
            reject_gate TEXT NOT NULL,
            blocked_claims_json TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, frontier_id)
        );
        """
    )


def latest_row(conn: sqlite3.Connection, table: str) -> sqlite3.Row:
    row = conn.execute(f"SELECT * FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    if row is None:
        raise RuntimeError(f"missing required row: {table}")
    return row


def atlas_run(conn: sqlite3.Connection, table: str) -> sqlite3.Row:
    row = conn.execute(
        f"SELECT run_id, decision, family_human_version, payload_json FROM {table} ORDER BY run_id DESC LIMIT 1"
    ).fetchone()
    if row is None:
        raise RuntimeError(f"missing atlas run: {table}")
    return row


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q45 = latest_row(conn, "human_q45_noncontig_frontier_coverage_complete_audit_v1_runs")
    audit = latest_row(conn, "human_translation_completion_audit_v5_runs")
    q45_items = list(
        conn.execute(
            """
            SELECT *
            FROM human_q45_noncontig_frontier_coverage_complete_audit_v1_items
            WHERE run_id=?
            ORDER BY priority
            """,
            (int(q45["run_id"]),),
        )
    )

    prepared = []
    for row in q45_items:
        frontier_id = str(row["frontier_id"])
        config = FAMILY_ATLASES.get(frontier_id)
        if config is None:
            raise RuntimeError(f"missing synthesis config for frontier {frontier_id}")
        atlas = atlas_run(conn, str(config["atlas_table"]))
        prepared.append(
            {
                "priority": int(row["priority"]),
                "frontier_id": frontier_id,
                "bookids": json.loads(str(row["bookids_json"])),
                "atlas_table": str(config["atlas_table"]),
                "atlas_run_id": int(atlas["run_id"]),
                "atlas_decision": str(atlas["decision"]),
                "synthesis_role": str(config["synthesis_role"]),
                "family_human_version": str(atlas["family_human_version"]),
                "hypothesis_id": str(config["hypothesis_id"]),
                "hypothesis": str(config["hypothesis"]),
                "next_probe": str(config["next_probe"]),
                "accept_gate": str(config["accept_gate"]),
                "reject_gate": str(config["reject_gate"]),
                "blocked_claims": [
                    "component_gloss",
                    "canonical_plaintext",
                    "single_sentence_translation",
                    "unsupported_external_import",
                ],
                "evidence": {
                    "q45_item": dict(row),
                    "atlas_run": dict(atlas),
                },
            }
        )

    source_quarantined_count = sum(
        1 for item in prepared if "external" in item["hypothesis"].lower() or "Chayenne" in item["family_human_version"]
    )
    component_gloss_allowed_count = 0
    canonical_promotion_allowed_count = 0
    decision = (
        "Q46_HUMAN_FAMILY_SYNTHESIS_HYPOTHESIS_QUEUE_READY_NO_GLOSS"
        if int(q45["atlas_ready_frontier_count"]) == 6
        and int(q45["pending_frontier_count"]) == 0
        and len(prepared) == 6
        and int(audit["promoted_gloss_count"]) == 0
        and component_gloss_allowed_count == 0
        and canonical_promotion_allowed_count == 0
        else "Q46_HUMAN_FAMILY_SYNTHESIS_HYPOTHESIS_QUEUE_REQUIRES_REVIEW"
    )
    payload = {
        "question": "What new source-anchored ideas become available after full Q37 coverage?",
        "answer": "Six controlled hypothesis lanes are ready for the next human translation pass.",
        "hypothesis_ids": [item["hypothesis_id"] for item in prepared],
        "blocked_use": "This queue ranks human-readable experiments; it does not promote component glosses.",
        "next_action": "Run one synthesis/probe lane at a time, starting with the phase-context to slot-classifier join.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q46_family_synthesis_hypothesis_queue_v1_runs (
                created_at, decision, q45_run_id, completion_audit_run_id,
                atlas_family_count, hypothesis_count, source_quarantined_count,
                component_gloss_allowed_count, canonical_promotion_allowed_count,
                payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                int(q45["run_id"]),
                int(audit["run_id"]),
                len(prepared),
                len(prepared),
                source_quarantined_count,
                component_gloss_allowed_count,
                canonical_promotion_allowed_count,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q46_family_synthesis_hypothesis_queue_v1_items (
                run_id, priority, frontier_id, bookids_json, atlas_table,
                atlas_run_id, atlas_decision, synthesis_role,
                family_human_version, hypothesis_id, hypothesis,
                next_probe, accept_gate, reject_gate, blocked_claims_json,
                evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    item["priority"],
                    item["frontier_id"],
                    j(item["bookids"]),
                    item["atlas_table"],
                    item["atlas_run_id"],
                    item["atlas_decision"],
                    item["synthesis_role"],
                    item["family_human_version"],
                    item["hypothesis_id"],
                    item["hypothesis"],
                    item["next_probe"],
                    item["accept_gate"],
                    item["reject_gate"],
                    j(item["blocked_claims"]),
                    j(item["evidence"]),
                )
                for item in prepared
            ],
        )

    print(
        j(
            {
                "run_id": run_id,
                "decision": decision,
                "atlas_family_count": len(prepared),
                "hypothesis_count": len(prepared),
                "source_quarantined_count": source_quarantined_count,
                "component_gloss_allowed_count": component_gloss_allowed_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
                "next_action": "phase-context to slot-classifier join",
            }
        )
    )


if __name__ == "__main__":
    main()
