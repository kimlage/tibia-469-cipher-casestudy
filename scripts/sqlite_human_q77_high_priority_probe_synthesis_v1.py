#!/usr/bin/env python3
"""Q77: synthesize high-priority Q67 probe outcomes."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

OUTCOME_SPECS = [
    {
        "outcome_id": "Q77_O01_BENNA_MATHEMAGIC",
        "probe_id": "Q67_P03_BENNA_FORMULA_MATHEMAGIC_OPERATOR",
        "source_run": "Q68",
        "role_id": "BENNA_FORMULA",
        "outcome_class": "METHOD_SUPPORT_NO_LEXICAL_PROMOTION",
        "status": "CLOSED_NO_GLOSS_REOPEN_ONLY_WITH_EXACT_SEQUENCE",
        "human_reading_delta": (
            "Mathemagica remains valid method/operator pressure for BENNA formula-handoff, "
            "but no BENNA lexical/operator rule was promoted."
        ),
        "next_action": "Reopen only if an exact BENNA-bearing source relation or predictive operator rule appears.",
    },
    {
        "outcome_id": "Q77_O02_BOOK27_TO_67",
        "probe_id": "Q67_P05_BOOK27_STOP_VS_CONTINUATION",
        "source_run": "Q69_Q70_Q71_Q72_Q73_Q74",
        "role_id": "PAYLOAD_CONTEXT_HELDOUT",
        "outcome_class": "STRUCTURAL_MISSING_EDGE_CANDIDATE_STRENGTHENED",
        "status": "OPEN_HIGH_VALUE_STRUCTURAL_CANDIDATE_NO_GLOSS",
        "human_reading_delta": (
            "Book27 is no longer best treated as an endpoint; it now has a strengthened structural "
            "missing-edge candidate into 67->2, while external/source confirmation remains absent."
        ),
        "next_action": "Use 27->67 as the top structural candidate and seek contig/source confirmation.",
    },
    {
        "outcome_id": "Q77_O03_C68_NAESE_SLOT",
        "probe_id": "Q67_P01_C68_NAESE_SLOT_EXACT_SOURCE",
        "source_run": "Q75",
        "role_id": "C68_NAESE_SLOT",
        "outcome_class": "FUNCTIONAL_ROLE_ONLY_NO_EXACT_SOURCE",
        "status": "CLOSED_NO_GLOSS_REOPEN_ONLY_WITH_EXACT_SEQUENCE",
        "human_reading_delta": (
            "C68/NAESE remains a functional slot/classifier role; no source supports a word meaning "
            "or mechanical slot value."
        ),
        "next_action": "Use as functional shadow only; reject soul/body/key/slot/classifier lexical readings.",
    },
    {
        "outcome_id": "Q77_O04_C86_VNCTIIN_CONTEXT",
        "probe_id": "Q67_P02_C86_VNCTIIN_CONTEXT_COMMAND_CONTROL",
        "source_run": "Q76",
        "role_id": "C86_VNCTIIN_CONTEXT",
        "outcome_class": "REGISTER_SUPPORT_NO_EXACT_SOURCE",
        "status": "CLOSED_NO_GLOSS_REOPEN_ONLY_WITH_EXACT_SEQUENCE",
        "human_reading_delta": (
            "C86/VNCTIIN remains a functional context-route role; Threat I/II support command/research "
            "register but not a phrase meaning."
        ),
        "next_action": "Use Threat I/II as register constraints only; keep ready-vs-audit controls active.",
    },
]

NEXT_FRONTIER = [
    {
        "frontier_id": "Q77_F01_27_TO_67_CONTIG_RECONSTRUCTION",
        "priority": "HIGH",
        "frontier_class": "STRUCTURAL_CONFIRMATION",
        "reason": "Only Q67 high-priority lane that produced a new positive structural candidate.",
        "gate": "Confirm only if independent contig reconstruction or exact source/provenance supports 27->67.",
    },
    {
        "frontier_id": "Q77_F02_EDGE_67_2_SOURCE_CONTINUITY",
        "priority": "MEDIUM",
        "frontier_class": "PHRASE_PATH_SOURCE_CONTINUITY",
        "reason": "Q67 medium probe remains unexecuted and connects to the same 35->67->2 path.",
        "gate": "Require source-backed continuity rule or exact phrase parallel; no sentence translation from edge alone.",
    },
    {
        "frontier_id": "Q77_F03_GLOBAL_SOURCE_FIREWALL",
        "priority": "HARD_GATE",
        "frontier_class": "PROMOTION_FIREWALL",
        "reason": "Q67 hard gate remains the mandatory firewall before any future lexical promotion.",
        "gate": "Every candidate must name exact source, exact sequence, provenance, accepted controls, failed controls, and contradiction audit.",
    },
]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q77_high_priority_probe_synthesis_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q67_run_id INTEGER NOT NULL,
            q68_run_id INTEGER NOT NULL,
            q69_run_id INTEGER NOT NULL,
            q73_run_id INTEGER NOT NULL,
            q74_run_id INTEGER NOT NULL,
            q75_run_id INTEGER NOT NULL,
            q76_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            high_priority_probe_count INTEGER NOT NULL,
            executed_high_priority_probe_count INTEGER NOT NULL,
            exact_source_success_count INTEGER NOT NULL,
            lexical_ready_count INTEGER NOT NULL,
            structural_candidate_strengthened_count INTEGER NOT NULL,
            confirmed_edge_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            open_high_value_frontier_count INTEGER NOT NULL,
            closed_no_gloss_probe_count INTEGER NOT NULL,
            synthesis_human_version TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q77_high_priority_probe_synthesis_v1_outcomes (
            run_id INTEGER NOT NULL,
            outcome_id TEXT NOT NULL,
            probe_id TEXT NOT NULL,
            source_run TEXT NOT NULL,
            role_id TEXT NOT NULL,
            outcome_class TEXT NOT NULL,
            status TEXT NOT NULL,
            human_reading_delta TEXT NOT NULL,
            next_action TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, outcome_id)
        );

        CREATE TABLE IF NOT EXISTS human_q77_high_priority_probe_synthesis_v1_frontier (
            run_id INTEGER NOT NULL,
            frontier_id TEXT NOT NULL,
            priority TEXT NOT NULL,
            frontier_class TEXT NOT NULL,
            reason TEXT NOT NULL,
            gate TEXT NOT NULL,
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


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q67 = latest_row(conn, "human_q67_lexical_anchor_probe_queue_v1_runs")
    q68 = latest_row(conn, "human_q68_benna_mathemagic_operator_check_v1_runs")
    q69 = latest_row(conn, "human_q69_book27_stop_continue_source_check_v1_runs")
    q73 = latest_row(conn, "human_q73_book27_to_67_confirmation_gate_v1_runs")
    q74 = latest_row(conn, "human_q74_book27_to_67_external_exact_search_audit_v1_runs")
    q75 = latest_row(conn, "human_q75_c68_naese_exact_source_check_v1_runs")
    q76 = latest_row(conn, "human_q76_c86_vnctiin_command_control_check_v1_runs")
    audit = latest_row(conn, "human_translation_completion_audit_v5_runs")

    high_priority_probe_count = int(q67["high_priority_probe_count"])
    executed_high_priority_probe_count = 4
    exact_source_success_count = 0
    lexical_ready_count = 0
    structural_candidate_strengthened_count = int(q73["structural_candidate_strengthened_count"])
    confirmed_edge_count = int(q73["confirmed_edge_count"])
    canonical_promotion_allowed_count = 0
    open_high_value_frontier_count = 1
    closed_no_gloss_probe_count = 3
    synthesis_human_version = (
        "Q77 synthesis: all four high-priority Q67 lexical probes are executed. BENNA, C68/NAESE, "
        "and C86/VNCTIIN remain functional/register roles with no exact source gloss. Book27 produced "
        "the only positive advance: a strengthened structural missing-edge candidate 27->67, still "
        "unconfirmed and no-gloss."
    )
    decision = (
        "Q77_HIGH_PRIORITY_PROBE_SYNTHESIS_READY_4_EXECUTED_1_STRUCTURAL_FRONTIER_NO_GLOSS"
        if high_priority_probe_count == 4
        and executed_high_priority_probe_count == 4
        and exact_source_success_count == 0
        and lexical_ready_count == 0
        and structural_candidate_strengthened_count == 1
        and confirmed_edge_count == 0
        and int(q68["lexical_ready_count"]) == 0
        and int(q69["lexical_ready_count"]) == 0
        and int(q74["lexical_ready_count"]) == 0
        and int(q75["lexical_ready_count"]) == 0
        and int(q76["lexical_ready_count"]) == 0
        and int(audit["promoted_gloss_count"]) == 0
        and canonical_promotion_allowed_count == 0
        else "Q77_HIGH_PRIORITY_PROBE_SYNTHESIS_REQUIRES_REVIEW"
    )
    payload = {
        "question": "What did the high-priority Q67 probes establish?",
        "answer": synthesis_human_version,
        "blocked_use": "Do not promote lexical glosses from these probes; only 27->67 advanced structurally.",
        "next_action": "Focus next on 27->67 contig reconstruction or the Q67 medium phrase-path continuity probe.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q77_high_priority_probe_synthesis_v1_runs (
                created_at, decision, q67_run_id, q68_run_id, q69_run_id,
                q73_run_id, q74_run_id, q75_run_id, q76_run_id,
                completion_audit_run_id, high_priority_probe_count,
                executed_high_priority_probe_count, exact_source_success_count,
                lexical_ready_count, structural_candidate_strengthened_count,
                confirmed_edge_count, canonical_promotion_allowed_count,
                open_high_value_frontier_count, closed_no_gloss_probe_count,
                synthesis_human_version, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                int(q67["run_id"]),
                int(q68["run_id"]),
                int(q69["run_id"]),
                int(q73["run_id"]),
                int(q74["run_id"]),
                int(q75["run_id"]),
                int(q76["run_id"]),
                int(audit["run_id"]),
                high_priority_probe_count,
                executed_high_priority_probe_count,
                exact_source_success_count,
                lexical_ready_count,
                structural_candidate_strengthened_count,
                confirmed_edge_count,
                canonical_promotion_allowed_count,
                open_high_value_frontier_count,
                closed_no_gloss_probe_count,
                synthesis_human_version,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q77_high_priority_probe_synthesis_v1_outcomes (
                run_id, outcome_id, probe_id, source_run, role_id,
                outcome_class, status, human_reading_delta,
                next_action, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    spec["outcome_id"],
                    spec["probe_id"],
                    spec["source_run"],
                    spec["role_id"],
                    spec["outcome_class"],
                    spec["status"],
                    spec["human_reading_delta"],
                    spec["next_action"],
                    j({"outcome": spec, "decision": decision}),
                )
                for spec in OUTCOME_SPECS
            ],
        )
        conn.executemany(
            """
            INSERT INTO human_q77_high_priority_probe_synthesis_v1_frontier (
                run_id, frontier_id, priority, frontier_class,
                reason, gate, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    spec["frontier_id"],
                    spec["priority"],
                    spec["frontier_class"],
                    spec["reason"],
                    spec["gate"],
                    j({"frontier": spec, "decision": decision}),
                )
                for spec in NEXT_FRONTIER
            ],
        )

    print(
        j(
            {
                "run_id": run_id,
                "decision": decision,
                "high_priority_probe_count": high_priority_probe_count,
                "executed_high_priority_probe_count": executed_high_priority_probe_count,
                "exact_source_success_count": exact_source_success_count,
                "lexical_ready_count": lexical_ready_count,
                "structural_candidate_strengthened_count": structural_candidate_strengthened_count,
                "confirmed_edge_count": confirmed_edge_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
                "open_high_value_frontier_count": open_high_value_frontier_count,
                "closed_no_gloss_probe_count": closed_no_gloss_probe_count,
            }
        )
    )


if __name__ == "__main__":
    main()
