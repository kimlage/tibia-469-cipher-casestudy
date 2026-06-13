#!/usr/bin/env python3
"""Q89: synthesize human translation routes after Q86-Q88 source audits."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

ROUTES = [
    {
        "route_id": "Q89_R01_R02_NAESE_PHASE_SLOT_BRIDGE",
        "rank": 1,
        "source_run": "human_q87_r02_naese_exact_source_audit_v1_runs",
        "status": "ALIVE_PRIMARY_HUMAN_ROUTE",
        "route_type": "local structural bridge",
        "books": ["51", "53"],
        "human_version": "R02/TRVEIIVNTBB phase material carries into the NAESE/C68 slot frame.",
        "why_ranked_here": "Strongest local controls: 2/2 structural bridge passes and one accepted slot role.",
        "promotion_block": "No exact source sequence plus meaning; no R02, TRVEIIVNTBB, NAESE, C68, FATCT, IVIFAST, slot, or bridge gloss.",
        "next_action": "Use 51/53 as positive controls; test 45/46/14 as local negatives before any phrase-level prose.",
    },
    {
        "route_id": "Q89_R02_BOOK7_MATHEMAGIC_OPERATOR_ROUTE",
        "rank": 2,
        "source_run": "human_q88_book7_phase_mathemagic_exact_source_audit_v1_runs",
        "status": "ALIVE_OPERATOR_DISCOVERY_ROUTE",
        "route_type": "operator/selector route",
        "books": ["7"],
        "human_version": "Book7 carries phase continuity through a local phase anchor; Mathemagica guides operator tests.",
        "why_ranked_here": "Book7 has 9 bridge supports, 3478 transition support, 4 Mathemagica outputs, and 2 exact 3478 phrase sources.",
        "promotion_block": "No exact Book7 sequence plus meaning and no official/client source for a forced value.",
        "next_action": "Use Mathemagica as selector machinery for heldout operator tests, especially 3478 windows and 1/13/49/94 routes.",
    },
    {
        "route_id": "Q89_R03_Q80_CONTROLLED_PACKET_SHADOW",
        "rank": 3,
        "source_run": "human_q80_packet_shadow_versions_v1_runs",
        "status": "ALIVE_READABLE_PACKET_SHADOW",
        "route_type": "multi-book packet reading",
        "books": ["35", "67", "2"],
        "human_version": "Formula routes context, handoff prepares the classifier slot, and selected context enters that slot.",
        "why_ranked_here": "Best readable packet across Q77-Q80, but both critical promotion routes failed exact-source audit in Q83/Q84.",
        "promotion_block": "Q83/Q84/Q85 block canonical promotion; source anchors are method/register only.",
        "next_action": "Use only as a controlled human-shadow packet while searching exact in-game source relations.",
    },
    {
        "route_id": "Q89_R04_NAESE_BENNA_COMPOSITE",
        "rank": 4,
        "source_run": "human_q86_naese_benna_exact_source_audit_v1_runs",
        "status": "HELD_COMPOSITE_SHADOW",
        "route_type": "slot-to-formula composite",
        "books": ["5", "9"],
        "human_version": "NAESE/C68 slot material appears to flow into BENNA formula material.",
        "why_ranked_here": "Useful composite shape, but Q75/Q68/Q86 preserve zero slot mechanical value and zero BENNA operator rule.",
        "promotion_block": "No exact source sequence plus meaning and no independent slot or formula value.",
        "next_action": "Reopen only if a new exact NAESE/BENNA source or predictive operator rule appears.",
    },
    {
        "route_id": "Q89_R05_REMAINING_MEDIUM_TARGETS",
        "rank": 5,
        "source_run": "human_q82_exact_source_target_queue_v1_targets",
        "status": "NEXT_FRONTIER",
        "route_type": "unclosed exact-source targets",
        "books": ["49", "54", "8", "37", "66"],
        "human_version": "Book49/math49, Book54 local pair/spine, and Chayenne/register frame remain as controlled next probes.",
        "why_ranked_here": "After Q86-Q88, these are the best remaining source-audit opportunities in Q82.",
        "promotion_block": "No route may promote without exact sequence, provenance, source-provided meaning or forced value, and failed controls.",
        "next_action": "Audit Book49 first, because Paradox/49/94 and Great Calculator references may produce operator constraints.",
    },
]

ACTIONS = [
    {
        "action_id": "Q89_A01_BOOK49_MATH49_EXACT_SOURCE_AUDIT",
        "priority": 1,
        "target_id": "Q82_T05_BOOK49_MATH49_REGISTER",
        "reason": "Book49 is the next best operator-linked target after Book7/Mathemagica.",
        "acceptance_gate": "Exact in-game/source sequence plus meaning or mechanically forced value; failed controls.",
        "expected_failure_mode": "49 becomes a tempting Paradox/Mathemagica key without predicting local book behavior.",
    },
    {
        "action_id": "Q89_A02_BOOK54_PAIR_LOCAL_SPINE_AUDIT",
        "priority": 2,
        "target_id": "Q82_T06_BOOK54_PAIR_LOCAL_SPINE",
        "reason": "Book54 may expose a local pair/spine relation after phase and operator routes are separated.",
        "acceptance_gate": "A local pair/spine rule that predicts heldout text better than the shadow baseline.",
        "expected_failure_mode": "Local similarity reads like prose but fails controls outside the pair.",
    },
    {
        "action_id": "Q89_A03_CHAYENNE_FRAME_REGISTER_AUDIT",
        "priority": 3,
        "target_id": "Q82_T08_CHAYENNE_FRAME_REGISTER",
        "reason": "Chayenne/register frames may help with external-shape hypotheses but carry high external-frame risk.",
        "acceptance_gate": "In-game anchoring must dominate; external frame only supports, never promotes.",
        "expected_failure_mode": "External naming/shape match contaminates in-game evidence.",
    },
    {
        "action_id": "Q89_A04_HUMAN_ROUTE_EXPORT",
        "priority": 4,
        "target_id": "HUMAN_ROUTE_ATLAS",
        "reason": "The translator needs a readable route map rather than a flat 70-book shadow.",
        "acceptance_gate": "Every book grouped by route, status, allowed reading, blocked gloss, and next exact-source target.",
        "expected_failure_mode": "Readable prose hides which claims are only shadow.",
    },
]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q89_route_synthesis_after_q86_q88_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q80_run_id INTEGER NOT NULL,
            q85_run_id INTEGER NOT NULL,
            q86_run_id INTEGER NOT NULL,
            q87_run_id INTEGER NOT NULL,
            q88_run_id INTEGER NOT NULL,
            q82_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            route_count INTEGER NOT NULL,
            alive_route_count INTEGER NOT NULL,
            next_action_count INTEGER NOT NULL,
            promoted_gloss_count INTEGER NOT NULL,
            canonical_translation_solved_count INTEGER NOT NULL,
            top_route_id TEXT NOT NULL,
            next_target_id TEXT NOT NULL,
            synthesis_pt TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q89_route_synthesis_after_q86_q88_v1_routes (
            run_id INTEGER NOT NULL,
            route_id TEXT NOT NULL,
            rank INTEGER NOT NULL,
            source_run TEXT NOT NULL,
            status TEXT NOT NULL,
            route_type TEXT NOT NULL,
            books_json TEXT NOT NULL,
            human_version TEXT NOT NULL,
            why_ranked_here TEXT NOT NULL,
            promotion_block TEXT NOT NULL,
            next_action TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, route_id)
        );

        CREATE TABLE IF NOT EXISTS human_q89_route_synthesis_after_q86_q88_v1_actions (
            run_id INTEGER NOT NULL,
            action_id TEXT NOT NULL,
            priority INTEGER NOT NULL,
            target_id TEXT NOT NULL,
            reason TEXT NOT NULL,
            acceptance_gate TEXT NOT NULL,
            expected_failure_mode TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, action_id)
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
    q85 = latest_row(conn, "human_q85_critical_source_audit_synthesis_v1_runs")
    q86 = latest_row(conn, "human_q86_naese_benna_exact_source_audit_v1_runs")
    q87 = latest_row(conn, "human_q87_r02_naese_exact_source_audit_v1_runs")
    q88 = latest_row(conn, "human_q88_book7_phase_mathemagic_exact_source_audit_v1_runs")
    q82 = latest_row(conn, "human_q82_exact_source_target_queue_v1_runs")
    completion = latest_row(conn, "human_translation_completion_audit_v5_runs")

    route_count = len(ROUTES)
    alive_route_count = sum(1 for route in ROUTES if route["status"].startswith("ALIVE"))
    next_action_count = len(ACTIONS)
    promoted_gloss_count = int(completion["promoted_gloss_count"])
    canonical_translation_solved_count = 0
    top_route_id = ROUTES[0]["route_id"]
    next_target_id = ACTIONS[0]["target_id"]
    synthesis_pt = (
        "Sintese Q89: a melhor rota humana atual e R02/NAESE como ponte fase->slot; "
        "Book7/Mathemagica vira rota de operadores/seletores; Q80 fica como pacote legivel controlado; "
        "NAESE/BENNA permanece sombra composta. Nenhuma vira gloss canonico. Proximo alvo: Book49/math49."
    )
    decision = (
        "Q89_HUMAN_ROUTE_SYNTHESIS_READY_NEXT_BOOK49_MATH49_NO_CANONICAL_GLOSS"
        if route_count == 5
        and alive_route_count == 3
        and next_action_count == 4
        and promoted_gloss_count == 0
        and int(q80["canonical_promotion_allowed_count"]) == 0
        and int(q85["canonical_promotion_allowed_count"]) == 0
        and int(q86["canonical_promotion_allowed_count"]) == 0
        and int(q87["canonical_promotion_allowed_count"]) == 0
        and int(q88["canonical_promotion_allowed_count"]) == 0
        else "Q89_HUMAN_ROUTE_SYNTHESIS_REQUIRES_REVIEW"
    )
    payload = {
        "top_route": top_route_id,
        "next_target": next_target_id,
        "translation_status": str(completion["decision"]),
        "guardrail": "Human versions are route-level shadows unless exact source sequence plus meaning passes.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q89_route_synthesis_after_q86_q88_v1_runs (
                created_at, decision, q80_run_id, q85_run_id, q86_run_id,
                q87_run_id, q88_run_id, q82_run_id, completion_audit_run_id,
                route_count, alive_route_count, next_action_count,
                promoted_gloss_count, canonical_translation_solved_count,
                top_route_id, next_target_id, synthesis_pt, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                int(q80["run_id"]),
                int(q85["run_id"]),
                int(q86["run_id"]),
                int(q87["run_id"]),
                int(q88["run_id"]),
                int(q82["run_id"]),
                int(completion["run_id"]),
                route_count,
                alive_route_count,
                next_action_count,
                promoted_gloss_count,
                canonical_translation_solved_count,
                top_route_id,
                next_target_id,
                synthesis_pt,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q89_route_synthesis_after_q86_q88_v1_routes (
                run_id, route_id, rank, source_run, status, route_type, books_json,
                human_version, why_ranked_here, promotion_block, next_action, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    route["route_id"],
                    int(route["rank"]),
                    route["source_run"],
                    route["status"],
                    route["route_type"],
                    j(route["books"]),
                    route["human_version"],
                    route["why_ranked_here"],
                    route["promotion_block"],
                    route["next_action"],
                    j(route),
                )
                for route in ROUTES
            ],
        )
        conn.executemany(
            """
            INSERT INTO human_q89_route_synthesis_after_q86_q88_v1_actions (
                run_id, action_id, priority, target_id, reason,
                acceptance_gate, expected_failure_mode, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    action["action_id"],
                    int(action["priority"]),
                    action["target_id"],
                    action["reason"],
                    action["acceptance_gate"],
                    action["expected_failure_mode"],
                    j(action),
                )
                for action in ACTIONS
            ],
        )

    print(
        j(
            {
                "run_id": run_id,
                "decision": decision,
                "route_count": route_count,
                "alive_route_count": alive_route_count,
                "next_action_count": next_action_count,
                "promoted_gloss_count": promoted_gloss_count,
                "top_route_id": top_route_id,
                "next_target_id": next_target_id,
            }
        )
    )


if __name__ == "__main__":
    main()
