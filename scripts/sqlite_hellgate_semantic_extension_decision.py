#!/usr/bin/env python3
"""Decide whether Hellgate long anchors support semantic extension."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


DB_PATH = Path(__file__).resolve().parents[1] / "data" / "bonelord_operational.sqlite"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        create table if not exists hellgate_semantic_extension_decision_runs (
            run_id integer primary key,
            created_at text not null,
            decision text not null,
            structural_support_count integer not null,
            semantic_support_count integer not null,
            gloss_allowed integer not null,
            reopen_condition text not null,
            payload_json text not null
        );

        create table if not exists hellgate_semantic_extension_decision_items (
            run_id integer not null,
            evidence_id text not null,
            evidence_status text not null,
            supports_structure integer not null,
            supports_semantics integer not null,
            gloss_allowed integer not null,
            reason text not null,
            payload_json text not null,
            primary key (run_id, evidence_id)
        );
        """
    )
    run_id = conn.execute("select coalesce(max(run_id), 0) + 1 from hellgate_semantic_extension_decision_runs").fetchone()[0]

    evidence = []
    h38 = conn.execute(
        "select decision, frame_occurrence_count, slot_supported_count, external_holdout_supported from hellgate38_continuation_slot_probe_runs order by run_id desc limit 1"
    ).fetchone()
    h39 = conn.execute(
        "select decision, exact_external_hit, row0_code_hit, fast_family_hit_count, formula_family_hit_count from hellgate39_formula_holdout_probe_runs order by run_id desc limit 1"
    ).fetchone()
    o23 = conn.execute(
        "select decision, frame_occurrence_count, independent_support_count, negative_o23_count, specificity_score from o23_onaf_hellgate_holdout_probe_runs order by run_id desc limit 1"
    ).fetchone()
    naese = conn.execute(
        "select decision, clean_count, controlled_variant_count, rare_count, hellgate_supported, slot_specificity_score from naese_hellgate_slot_contrast_probe_runs order by run_id desc limit 1"
    ).fetchone()

    evidence.append(
        (
            "HELLGATE38_CONTINUATION_SLOT",
            "STRUCTURAL_SLOT_SUPPORT_NO_GLOSS",
            1,
            0,
            "Hellgate38 supports O23/ONAF to IVIFAST slot continuity, but not natural-language meaning.",
            dict(h38) if h38 else {},
        )
    )
    evidence.append(
        (
            "HELLGATE39_FORMULA_HOLDOUT",
            "FORMULA_HOLDOUT_NO_GLOSS",
            1,
            0,
            "Hellgate39 is externally real but not row0-code aligned; classify as formula/audit holdout.",
            dict(h39) if h39 else {},
        )
    )
    evidence.append(
        (
            "O23_ONAF_FRAME",
            "COMPOSITE_FRAME_SPECIFIC_NO_O23_GLOSS",
            1,
            0,
            "O23/ONAF frame is specific, with negative O23 controls preventing general O23 gloss.",
            dict(o23) if o23 else {},
        )
    )
    evidence.append(
        (
            "NAESE_IVIFAST_SLOT",
            "SLOT_CLASSIFIER_WITH_EXTERNAL_HOLDOUT_NO_GLOSS",
            1,
            0,
            "NAESE/IVIFAST is a slot classifier with external holdout support; no lexical meaning.",
            dict(naese) if naese else {},
        )
    )

    structural = semantic = 0
    for evidence_id, status, supports_structure, supports_semantics, reason, payload in evidence:
        structural += supports_structure
        semantic += supports_semantics
        conn.execute(
            """
            insert into hellgate_semantic_extension_decision_items
            (run_id, evidence_id, evidence_status, supports_structure,
             supports_semantics, gloss_allowed, reason, payload_json)
            values (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                evidence_id,
                status,
                supports_structure,
                supports_semantics,
                0,
                reason,
                json.dumps(payload, ensure_ascii=False),
            ),
        )

    decision = "HELLGATE_ANCHORS_STRUCTURAL_ONLY_NO_SEMANTIC_EXTENSION"
    reopen = "Reopen only with source-attested natural-language meaning tied to the exact full sequence or independent contrastive semantic relation."
    conn.execute(
        """
        insert into hellgate_semantic_extension_decision_runs
        (run_id, created_at, decision, structural_support_count, semantic_support_count,
         gloss_allowed, reopen_condition, payload_json)
        values (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            now_iso(),
            decision,
            structural,
            semantic,
            0,
            reopen,
            json.dumps({"evidence_count": len(evidence)}, ensure_ascii=False),
        ),
    )
    conn.commit()

    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "structural_support_count": structural,
                "semantic_support_count": semantic,
                "gloss_allowed": 0,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
