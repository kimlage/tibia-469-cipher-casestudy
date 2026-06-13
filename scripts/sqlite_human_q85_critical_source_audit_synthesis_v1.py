#!/usr/bin/env python3
"""Q85: synthesize Q83/Q84 critical exact-source audit impact on Q80."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

ITEMS = [
    {
        "item_id": "Q85_I01_BENNA_C86_HANDOFF",
        "source_run": "Q83",
        "q82_target_id": "Q82_T01_BENNA_C86_VNCTIIN_FORMULA_HANDOFF",
        "impact_class": "CRITICAL_TARGET_AUDITED_NEGATIVE_EXACT_SOURCE",
        "shadow_status": "KEEP_STRUCTURAL_METHOD_SHADOW",
        "promotion_status": "BLOCK_PROMOTION_NO_EXACT_SEQUENCE_MEANING",
        "next_action": "Do not reopen without a new exact BENNA/LTAST/TAILBETFTE/VNCTIIN source or predictive operator rule.",
    },
    {
        "item_id": "Q85_I02_C86_VNCTIIN_CORRIDOR",
        "source_run": "Q84",
        "q82_target_id": "Q82_T02_C86_VNCTIIN_PAYLOAD_CORRIDOR",
        "impact_class": "CRITICAL_TARGET_AUDITED_NEGATIVE_EXACT_SOURCE",
        "shadow_status": "KEEP_REGISTER_SUPPORTED_PAYLOAD_CORRIDOR_SHADOW",
        "promotion_status": "BLOCK_PROMOTION_NO_EXACT_SEQUENCE_MEANING",
        "next_action": "Do not reopen without exact CEVIEFIINI/VNCTIIN/TAILBETFTE/NAESE source relation or mechanical value.",
    },
    {
        "item_id": "Q85_I03_Q80_PACKET",
        "source_run": "Q80_Q83_Q84",
        "q82_target_id": "Q80_PACKET",
        "impact_class": "PACKET_STABLE_AS_READABLE_SHADOW_PROMOTION_BLOCKED",
        "shadow_status": "KEEP_PRIMARY_35_67_2_AND_HELDOUT_27_67_2",
        "promotion_status": "BLOCK_CANONICAL_PACKET_PROMOTION",
        "next_action": "Use Q80 for human review/search; execute Q82 high targets next rather than promoting the packet.",
    },
]

NEXT_TARGETS = [
    {
        "target_id": "Q82_T03_NAESE_BENNA_COMPOSITE",
        "priority": "HIGH",
        "reason": "It may test whether slot material flows into BENNA formula body independently of the failed critical packet promotion.",
    },
    {
        "target_id": "Q82_T04_R02_NAESE_SLOT_BRIDGE",
        "priority": "HIGH",
        "reason": "It may provide an alternate phase-to-slot bridge that does not depend on C86/VNCTIIN payload promotion.",
    },
    {
        "target_id": "Q82_T07_BOOK7_PHASE_MATHEMAGIC",
        "priority": "MEDIUM",
        "reason": "It preserves Mathemagica as a route for operator discovery after BENNA/C86 exact-source failure.",
    },
]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q85_critical_source_audit_synthesis_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q80_run_id INTEGER NOT NULL,
            q82_run_id INTEGER NOT NULL,
            q83_run_id INTEGER NOT NULL,
            q84_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            critical_target_count INTEGER NOT NULL,
            audited_critical_target_count INTEGER NOT NULL,
            critical_exact_source_hit_count INTEGER NOT NULL,
            critical_exact_meaning_relation_count INTEGER NOT NULL,
            q80_shadow_packet_preserved_count INTEGER NOT NULL,
            q80_packet_promotion_allowed_count INTEGER NOT NULL,
            next_high_target_count INTEGER NOT NULL,
            lexical_ready_count INTEGER NOT NULL,
            direct_gloss_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            synthesis_human_version TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q85_critical_source_audit_synthesis_v1_items (
            run_id INTEGER NOT NULL,
            item_id TEXT NOT NULL,
            source_run TEXT NOT NULL,
            q82_target_id TEXT NOT NULL,
            impact_class TEXT NOT NULL,
            shadow_status TEXT NOT NULL,
            promotion_status TEXT NOT NULL,
            next_action TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, item_id)
        );

        CREATE TABLE IF NOT EXISTS human_q85_critical_source_audit_synthesis_v1_next_targets (
            run_id INTEGER NOT NULL,
            target_id TEXT NOT NULL,
            priority TEXT NOT NULL,
            reason TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, target_id)
        );
        """
    )


def latest_row(conn: sqlite3.Connection, table: str) -> sqlite3.Row:
    row = conn.execute(f"SELECT * FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    if row is None:
        raise RuntimeError(f"missing required row: {table}")
    return row


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q80 = latest_row(conn, "human_q80_packet_shadow_versions_v1_runs")
    q82 = latest_row(conn, "human_q82_exact_source_target_queue_v1_runs")
    q83 = latest_row(conn, "human_q83_benna_c86_exact_source_audit_v1_runs")
    q84 = latest_row(conn, "human_q84_c86_vnctiin_exact_source_audit_v1_runs")
    completion = latest_row(conn, "human_translation_completion_audit_v5_runs")

    critical_target_count = int(q82["critical_target_count"])
    audited_critical_target_count = 2
    critical_exact_source_hit_count = int(q83["web_exact_target_hit_count"]) + int(q84["web_exact_target_hit_count"])
    critical_exact_meaning_relation_count = int(q83["exact_meaning_relation_count"]) + int(q84["exact_meaning_relation_count"])
    q80_shadow_packet_preserved_count = int(q80["accepted_primary_packet_count"]) + int(q80["conditional_heldout_packet_count"])
    q80_packet_promotion_allowed_count = 0
    next_high_target_count = len([target for target in NEXT_TARGETS if target["priority"] == "HIGH"])
    lexical_ready_count = 0
    direct_gloss_count = 0
    canonical_promotion_allowed_count = 0
    synthesis_human_version = (
        "Q85: both critical exact-source targets failed promotion gates. Q80 remains the best controlled "
        "human-shadow packet, but it is explicitly blocked from canonical or lexical promotion. Next work "
        "should move to Q82 high targets, not re-run the critical targets without new evidence."
    )
    decision = (
        "Q85_CRITICAL_SOURCE_AUDIT_SYNTHESIS_Q80_SHADOW_STABLE_PROMOTION_BLOCKED"
        if critical_target_count == 2
        and audited_critical_target_count == 2
        and critical_exact_source_hit_count == 0
        and critical_exact_meaning_relation_count == 0
        and q80_shadow_packet_preserved_count == 2
        and q80_packet_promotion_allowed_count == 0
        and next_high_target_count == 2
        and int(completion["promoted_gloss_count"]) == 0
        else "Q85_CRITICAL_SOURCE_AUDIT_SYNTHESIS_REQUIRES_REVIEW"
    )
    payload = {
        "question": "What is the impact of Q83/Q84 on the Q80 packet and next translation route?",
        "answer": synthesis_human_version,
        "blocked_use": "Do not promote Q80 or its critical components as plaintext.",
        "next_action": "Execute Q82 high targets T03/T04, then reassess whether a non-C86 route can provide exact-source leverage.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q85_critical_source_audit_synthesis_v1_runs (
                created_at, decision, q80_run_id, q82_run_id, q83_run_id,
                q84_run_id, completion_audit_run_id, critical_target_count,
                audited_critical_target_count, critical_exact_source_hit_count,
                critical_exact_meaning_relation_count, q80_shadow_packet_preserved_count,
                q80_packet_promotion_allowed_count, next_high_target_count,
                lexical_ready_count, direct_gloss_count,
                canonical_promotion_allowed_count, synthesis_human_version,
                payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                int(q80["run_id"]),
                int(q82["run_id"]),
                int(q83["run_id"]),
                int(q84["run_id"]),
                int(completion["run_id"]),
                critical_target_count,
                audited_critical_target_count,
                critical_exact_source_hit_count,
                critical_exact_meaning_relation_count,
                q80_shadow_packet_preserved_count,
                q80_packet_promotion_allowed_count,
                next_high_target_count,
                lexical_ready_count,
                direct_gloss_count,
                canonical_promotion_allowed_count,
                synthesis_human_version,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q85_critical_source_audit_synthesis_v1_items (
                run_id, item_id, source_run, q82_target_id, impact_class,
                shadow_status, promotion_status, next_action, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    row["item_id"],
                    row["source_run"],
                    row["q82_target_id"],
                    row["impact_class"],
                    row["shadow_status"],
                    row["promotion_status"],
                    row["next_action"],
                    j(row),
                )
                for row in ITEMS
            ],
        )
        conn.executemany(
            """
            INSERT INTO human_q85_critical_source_audit_synthesis_v1_next_targets (
                run_id, target_id, priority, reason, evidence_json
            ) VALUES (?, ?, ?, ?, ?)
            """,
            [
                (run_id, row["target_id"], row["priority"], row["reason"], j(row))
                for row in NEXT_TARGETS
            ],
        )

    print(
        j(
            {
                "run_id": run_id,
                "decision": decision,
                "critical_target_count": critical_target_count,
                "audited_critical_target_count": audited_critical_target_count,
                "critical_exact_source_hit_count": critical_exact_source_hit_count,
                "critical_exact_meaning_relation_count": critical_exact_meaning_relation_count,
                "q80_shadow_packet_preserved_count": q80_shadow_packet_preserved_count,
                "q80_packet_promotion_allowed_count": q80_packet_promotion_allowed_count,
                "next_high_target_count": next_high_target_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
            }
        )
    )


if __name__ == "__main__":
    main()
