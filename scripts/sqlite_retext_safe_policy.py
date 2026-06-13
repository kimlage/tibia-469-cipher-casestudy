#!/usr/bin/env python3
"""Materialize a safe no-core-gloss policy for suspect retext items."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


DB_PATH = Path(__file__).resolve().parents[1] / "data" / "bonelord_operational.sqlite"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def bucket(token: str) -> tuple[str, str, str]:
    if token == "TAN":
        return (
            "SAFE_SHADOW_REVERSE_EXTERNAL_CRIB_NO_CORE",
            "use_than_shadow_for_TAN_only",
            "external TAN->THAN crib exists; keep as shadow/display, not core mutation",
        )
    if token in {"ATN", "NTA", "ANT"}:
        return (
            "SAFE_VARIANT_SHADOW_TO_THAN_NO_CORE",
            "use_than_family_shadow_for_variant_only",
            "variant family likely THAN/rotation; not enough for hard core mutation",
        )
    if token in {"IIN", "ETT", "TE"}:
        return (
            "PHRASE_SPECIFIC_SHADOW_ONLY",
            "only_apply_existing_or_new_phrase_specific_rules",
            "microtoken frequency is high; global replacement would overfit",
        )
    if token in {"VTLRNEFIE", "ILTAEN", "NNVETT"}:
        return (
            "NEUTRALIZE_AS_SUSPECT_MARKER",
            "render_suspect_marker_until_independent_evidence",
            "old readable hint is likely semantic overlay and unsafe as prose",
        )
    if token in {"AILBET", "TAILBE", "ILBETA"}:
        return (
            "NEUTRALIZE_TO_MECHANICAL_AUDIT",
            "render_mechanical_albeit_audit_marker_not_played",
            "played is unsupported English retext over mechanical ALBEIT evidence",
        )
    if token in {"NBEEILE", "NELBEEI", "EBENEIL"}:
        return (
            "NEUTRALIZE_BEELINE_BLIMEY_VARIANT",
            "render_variant_suspect_or_display_only",
            "blimey/beeline variants are boundary-sensitive and weak",
        )
    if token in {"EIIVNT", "TNVIEI"}:
        return (
            "NEUTRALIZE_INVITE_DIVINE_UNSTABLE",
            "compare_invite_family_in_shadow_only",
            "divine is unstable and invite survives in boundary-owner evidence",
        )
    return ("REVIEW_ONLY", "manual_review_no_core_mutation", "no safe bucket")


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        create table if not exists retext_safe_policy_runs (
            run_id integer primary key,
            created_at text not null,
            decision text not null,
            item_count integer not null,
            core_mutation_allowed_count integer not null,
            phrase_specific_count integer not null,
            neutralize_count integer not null,
            payload_json text not null
        );

        create table if not exists retext_safe_policy_items (
            run_id integer not null,
            token text not null,
            policy_status text not null,
            recommended_action text not null,
            core_mutation_allowed integer not null,
            gloss_allowed integer not null,
            priority_score integer not null,
            hit_count integer not null,
            book_count integer not null,
            reason text not null,
            evidence_json text not null,
            primary key (run_id, token)
        );
        """
    )

    run_id = conn.execute("select coalesce(max(run_id), 0) + 1 from retext_safe_policy_runs").fetchone()[0]
    rank_run_id = conn.execute("select max(run_id) from retext_suspect_presence_rank_items").fetchone()[0]
    items = list(
        conn.execute(
            """
            select token, decision, confidence, blocked_old_hint, book_count, hit_count,
                   priority_score, recommended_action, evidence_json
            from retext_suspect_presence_rank_items
            where run_id = ?
            order by priority_score desc, token
            """,
            (rank_run_id,),
        )
    )

    phrase_specific = 0
    neutralize = 0
    for item in items:
        status, action, reason = bucket(item["token"])
        if status == "PHRASE_SPECIFIC_SHADOW_ONLY":
            phrase_specific += 1
        if status.startswith("NEUTRALIZE"):
            neutralize += 1
        conn.execute(
            """
            insert into retext_safe_policy_items
            (run_id, token, policy_status, recommended_action, core_mutation_allowed,
             gloss_allowed, priority_score, hit_count, book_count, reason, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                item["token"],
                status,
                action,
                0,
                0,
                item["priority_score"],
                item["hit_count"],
                item["book_count"],
                reason,
                item["evidence_json"],
            ),
        )

    decision = "RETEXT_SAFE_POLICY_READY_NO_CORE_GLOSS"
    conn.execute(
        """
        insert into retext_safe_policy_runs
        (run_id, created_at, decision, item_count, core_mutation_allowed_count,
         phrase_specific_count, neutralize_count, payload_json)
        values (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            now_iso(),
            decision,
            len(items),
            0,
            phrase_specific,
            neutralize,
            json.dumps({"rank_run_id": rank_run_id}, ensure_ascii=False),
        ),
    )
    conn.commit()

    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "item_count": len(items),
                "core_mutation_allowed_count": 0,
                "phrase_specific_count": phrase_specific,
                "neutralize_count": neutralize,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
