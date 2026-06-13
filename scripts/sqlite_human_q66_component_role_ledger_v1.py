#!/usr/bin/env python3
"""Q66: consolidate Q60-Q65 functional-role outcomes into one ledger."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

ROLE_SPECS = [
    {
        "role_id": "C68_NAESE_SLOT",
        "component_family": "C68_NAESE_SLOT",
        "q60_candidate_id": "Q60_C01_C68_NAESE_SLOT_CLASSIFIER_ROLE",
        "evidence_source": "Q61",
        "source_table": "human_q61_c68_naese_slot_role_minimal_pairs_v1_runs",
        "role_strength": "STRONG_FUNCTIONAL_ROLE_ACCEPTED",
        "target_books": ["2", "5"],
        "support_books": ["2", "5"],
        "control_books": ["31", "57", "42"],
        "functional_accept_status": "ACCEPTED_BY_MINIMAL_PAIRS",
        "lexical_status": "LEXICAL_BLOCKED",
        "canonical_status": "NO_CANONICAL_PROMOTION",
        "human_version": (
            "C68/NAESE slot-classifier role is accepted as a functional shadow role "
            "where local route evidence supplies slot context."
        ),
        "residual_risk": "Functional slot/classifier labels are not Bonelord word meanings.",
        "next_probe": "Seek exact in-game phrase support or surface-independent slot labels before lexical promotion.",
    },
    {
        "role_id": "C86_VNCTIIN_CONTEXT",
        "component_family": "C86_VNCTIIN_CONTEXT",
        "q60_candidate_id": "Q60_C02_C86_VNCTIIN_CONTEXT_ROUTE_ROLE",
        "evidence_source": "Q62",
        "source_table": "human_q62_c86_vnctiin_context_route_ready_audit_v1_runs",
        "role_strength": "STRONG_FUNCTIONAL_ROLE_ACCEPTED",
        "target_books": ["2", "10", "27", "35", "67"],
        "support_books": ["2", "10", "27", "35", "67"],
        "control_books": ["5", "31", "42", "57"],
        "functional_accept_status": "ACCEPTED_BY_READY_VS_AUDIT_CONTRAST",
        "lexical_status": "LEXICAL_BLOCKED",
        "canonical_status": "NO_CANONICAL_PROMOTION",
        "human_version": (
            "C86/VNCTIIN context-route role is accepted as a functional shadow role "
            "for ready EVIEFIIN->VN/C68/TIIN route books."
        ),
        "residual_risk": "Context/payload/route are register labels, not dictionary glosses.",
        "next_probe": "Search for in-game source parallels that distinguish route context from surface-audit controls.",
    },
    {
        "role_id": "BENNA_FORMULA",
        "component_family": "BENNA_FORMULA",
        "q60_candidate_id": "Q60_C03_BENNA_FORMULA_HANDOFF_ROLE",
        "evidence_source": "Q63",
        "source_table": "human_q63_benna_formula_handoff_directional_contrast_v1_runs",
        "role_strength": "STRONG_FUNCTIONAL_ROLE_ACCEPTED",
        "target_books": ["35", "10"],
        "support_books": ["35", "10"],
        "control_books": ["5", "31", "57"],
        "functional_accept_status": "ACCEPTED_BY_DIRECTIONAL_CONTRAST",
        "lexical_status": "LEXICAL_BLOCKED",
        "canonical_status": "NO_CANONICAL_PROMOTION",
        "human_version": (
            "BENNA formula-handoff role is accepted where clean formula body and context "
            "handoff evidence align."
        ),
        "residual_risk": "Book5 proves BENNA-like material alone is not enough for handoff or lexical meaning.",
        "next_probe": "Look for exact formula/register source support and keep Book5 as a negative control.",
    },
    {
        "role_id": "EDGE_67_2",
        "component_family": "EDGE_67_2",
        "q60_candidate_id": "Q60_C04_EDGE_67_2_HANDOFF_ROLE",
        "evidence_source": "Q64",
        "source_table": "human_q64_edge_67_2_handoff_role_contrast_v1_runs",
        "role_strength": "STRONG_EDGE_ROLE_ACCEPTED",
        "target_books": ["67", "2"],
        "support_books": ["35", "67", "2"],
        "control_books": ["27", "35", "42"],
        "functional_accept_status": "ACCEPTED_BY_EDGE_AND_PATH_CONTRAST",
        "lexical_status": "LEXICAL_BLOCKED",
        "canonical_status": "NO_CANONICAL_PROMOTION",
        "human_version": (
            "The 67->2 handoff edge is accepted as a functional phrase-path role "
            "from context handoff into the Book2 slot target."
        ),
        "residual_risk": "The edge is not sentence plaintext and does not translate Book67 by itself.",
        "next_probe": "Use 35->67->2 as a phrase-path control for future source-continuity searches.",
    },
    {
        "role_id": "PAYLOAD_CONTEXT_HELDOUT",
        "component_family": "PAYLOAD_CONTEXT_HELDOUT",
        "q60_candidate_id": "Q60_C05_PAYLOAD_CONTEXT_HOLD_ROLE",
        "evidence_source": "Q65",
        "source_table": "human_q65_payload_context_hold_heldout_role_v1_runs",
        "role_strength": "MODERATE_HELDOUT_ROLE_ACCEPTED_OPEN",
        "target_books": ["27"],
        "support_books": ["27"],
        "control_books": ["67", "2", "57", "42"],
        "functional_accept_status": "ACCEPTED_AS_MODERATE_HELDOUT",
        "lexical_status": "LEXICAL_BLOCKED",
        "canonical_status": "NO_CANONICAL_PROMOTION",
        "human_version": (
            "Book27 payload/context-hold role is accepted as a moderate heldout role "
            "without resolving stop versus missing edge."
        ),
        "residual_risk": "Stop-vs-continue remains unresolved; do not read it as command, dead, soul, or necromancy.",
        "next_probe": "Find a contrast that decides whether Book27 stops in context or simply lacks the observed 67->2 edge.",
    },
]

RISK_SPECS = [
    {
        "risk_id": "FUNCTIONAL_LABELS_NOT_WORDS",
        "risk_class": "LEXICAL_BLOCKER",
        "risk_status": "OPEN",
        "consequence": "Accepted roles support human shadow phrasing but not Bonelord word meanings.",
        "next_action": "Keep role labels separate from canonical glosses until exact phrase evidence appears.",
    },
    {
        "risk_id": "SOURCE_REGISTER_NOT_DICTIONARY",
        "risk_class": "SOURCE_FIREWALL",
        "risk_status": "OPEN_CONTROLLED",
        "consequence": "Mathemagic, Great Calculator, and threat lore can constrain register but cannot decode words alone.",
        "next_action": "Use sources as search constraints and negative controls, not as direct dictionary entries.",
    },
    {
        "risk_id": "BOOK27_STOP_CONTINUE_OPEN",
        "risk_class": "HELDOUT_AMBIGUITY",
        "risk_status": "OPEN",
        "consequence": "Book27 can remain a payload/context hold without proving an endpoint or missing continuation.",
        "next_action": "Prioritize a stop-vs-missing-edge contrast before strengthening Book27.",
    },
    {
        "risk_id": "CANONICAL_TRANSLATION_UNSOLVED",
        "risk_class": "GOAL_BLOCKER",
        "risk_status": "OPEN",
        "consequence": "The project has a usable human shadow ledger, but no promoted canonical plaintext.",
        "next_action": "Promote only small packages after exact in-game anchoring and contradiction audit.",
    },
]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def brief(row: sqlite3.Row, columns: list[str]) -> dict[str, object]:
    return {column: row[column] for column in columns if column in row.keys()}


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q66_component_role_ledger_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q60_run_id INTEGER NOT NULL,
            q61_run_id INTEGER NOT NULL,
            q62_run_id INTEGER NOT NULL,
            q63_run_id INTEGER NOT NULL,
            q64_run_id INTEGER NOT NULL,
            q65_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            role_target_count INTEGER NOT NULL,
            functional_role_accepted_count INTEGER NOT NULL,
            strong_functional_role_count INTEGER NOT NULL,
            moderate_heldout_role_count INTEGER NOT NULL,
            lexical_ready_count INTEGER NOT NULL,
            direct_gloss_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            open_risk_count INTEGER NOT NULL,
            ledger_human_version TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q66_component_role_ledger_v1_roles (
            run_id INTEGER NOT NULL,
            role_id TEXT NOT NULL,
            component_family TEXT NOT NULL,
            functional_label TEXT NOT NULL,
            evidence_source TEXT NOT NULL,
            evidence_run_id INTEGER NOT NULL,
            q60_candidate_id TEXT NOT NULL,
            q60_evidence_strength TEXT NOT NULL,
            q60_role_status TEXT NOT NULL,
            role_strength TEXT NOT NULL,
            target_books_json TEXT NOT NULL,
            support_books_json TEXT NOT NULL,
            control_books_json TEXT NOT NULL,
            functional_accept_status TEXT NOT NULL,
            lexical_status TEXT NOT NULL,
            canonical_status TEXT NOT NULL,
            human_version TEXT NOT NULL,
            residual_risk TEXT NOT NULL,
            next_probe TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, role_id)
        );

        CREATE TABLE IF NOT EXISTS human_q66_component_role_ledger_v1_risks (
            run_id INTEGER NOT NULL,
            risk_id TEXT NOT NULL,
            risk_class TEXT NOT NULL,
            risk_status TEXT NOT NULL,
            consequence TEXT NOT NULL,
            next_action TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, risk_id)
        );
        """
    )


def latest_row(conn: sqlite3.Connection, table: str) -> sqlite3.Row:
    row = conn.execute(f"SELECT * FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    if row is None:
        raise RuntimeError(f"missing required row: {table}")
    return row


def load_q60_candidates(conn: sqlite3.Connection, q60_run_id: int) -> dict[str, sqlite3.Row]:
    rows = conn.execute(
        """
        SELECT *
        FROM human_q60_component_role_promotion_queue_v1_candidates
        WHERE run_id=?
        """,
        (q60_run_id,),
    ).fetchall()
    return {str(row["candidate_id"]): row for row in rows}


def role_accepts(spec: dict[str, object], evidence_run: sqlite3.Row) -> bool:
    source = str(spec["evidence_source"])
    if source in {"Q61", "Q62", "Q63"}:
        return int(evidence_run["functional_role_accept_count"]) == 1
    if source == "Q64":
        return int(evidence_run["functional_edge_accept_count"]) == 1 and int(evidence_run["phrase_path_accept_count"]) == 1
    if source == "Q65":
        return int(evidence_run["heldout_role_accept_count"]) == 1 and int(evidence_run["stop_continue_resolved_count"]) == 0
    return False


def build_role_rows(
    q60_candidates: dict[str, sqlite3.Row],
    evidence_runs: dict[str, sqlite3.Row],
) -> list[dict[str, object]]:
    roles = []
    for spec in ROLE_SPECS:
        candidate = q60_candidates.get(str(spec["q60_candidate_id"]))
        if candidate is None:
            raise RuntimeError(f"missing Q60 candidate: {spec['q60_candidate_id']}")
        evidence_run = evidence_runs[str(spec["evidence_source"])]
        accepted = role_accepts(spec, evidence_run)
        lexical_clear = int(evidence_run["lexical_ready_count"]) == 0 and int(evidence_run["direct_gloss_count"]) == 0
        canonical_clear = int(evidence_run["canonical_promotion_allowed_count"]) == 0
        roles.append(
            {
                "role_id": spec["role_id"],
                "component_family": spec["component_family"],
                "functional_label": candidate["functional_label"],
                "evidence_source": spec["evidence_source"],
                "evidence_run_id": int(evidence_run["run_id"]),
                "q60_candidate_id": spec["q60_candidate_id"],
                "q60_evidence_strength": candidate["evidence_strength"],
                "q60_role_status": candidate["current_role_status"],
                "role_strength": spec["role_strength"] if accepted and lexical_clear and canonical_clear else "ROLE_REQUIRES_REVIEW",
                "target_books": spec["target_books"],
                "support_books": spec["support_books"],
                "control_books": spec["control_books"],
                "functional_accept_status": spec["functional_accept_status"] if accepted else "REQUIRES_REVIEW",
                "lexical_status": spec["lexical_status"] if lexical_clear else "LEXICAL_REQUIRES_REVIEW",
                "canonical_status": spec["canonical_status"] if canonical_clear else "CANONICAL_REQUIRES_REVIEW",
                "human_version": spec["human_version"],
                "residual_risk": spec["residual_risk"],
                "next_probe": spec["next_probe"],
                "evidence": {
                    "q60_candidate": brief(
                        candidate,
                        [
                            "candidate_id",
                            "functional_label",
                            "component_family",
                            "evidence_strength",
                            "current_role_status",
                            "plausible_shadow_definition",
                            "blocked_lexical_claim",
                            "required_promotion_gate",
                            "next_probe",
                        ],
                    ),
                    "evidence_run": brief(
                        evidence_run,
                        [
                            "run_id",
                            "decision",
                            "functional_role_accept_count",
                            "functional_edge_accept_count",
                            "phrase_path_accept_count",
                            "heldout_role_accept_count",
                            "stop_continue_resolved_count",
                            "lexical_ready_count",
                            "direct_gloss_count",
                            "canonical_promotion_allowed_count",
                        ],
                    ),
                },
            }
        )
    return roles


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q60 = latest_row(conn, "human_q60_component_role_promotion_queue_v1_runs")
    q61 = latest_row(conn, "human_q61_c68_naese_slot_role_minimal_pairs_v1_runs")
    q62 = latest_row(conn, "human_q62_c86_vnctiin_context_route_ready_audit_v1_runs")
    q63 = latest_row(conn, "human_q63_benna_formula_handoff_directional_contrast_v1_runs")
    q64 = latest_row(conn, "human_q64_edge_67_2_handoff_role_contrast_v1_runs")
    q65 = latest_row(conn, "human_q65_payload_context_hold_heldout_role_v1_runs")
    audit = latest_row(conn, "human_translation_completion_audit_v5_runs")

    q60_candidates = load_q60_candidates(conn, int(q60["run_id"]))
    evidence_runs = {"Q61": q61, "Q62": q62, "Q63": q63, "Q64": q64, "Q65": q65}
    role_rows = build_role_rows(q60_candidates, evidence_runs)

    role_target_count = len(role_rows)
    functional_role_accepted_count = sum(1 for row in role_rows if row["functional_accept_status"] != "REQUIRES_REVIEW")
    strong_functional_role_count = sum(1 for row in role_rows if str(row["role_strength"]).startswith("STRONG"))
    moderate_heldout_role_count = sum(1 for row in role_rows if str(row["role_strength"]).startswith("MODERATE"))
    lexical_ready_count = sum(1 for row in role_rows if row["lexical_status"] != "LEXICAL_BLOCKED")
    direct_gloss_count = sum(int(run["direct_gloss_count"]) for run in evidence_runs.values())
    canonical_promotion_allowed_count = sum(int(run["canonical_promotion_allowed_count"]) for run in evidence_runs.values())
    open_risk_count = sum(1 for risk in RISK_SPECS if str(risk["risk_status"]).startswith("OPEN"))
    ledger_human_version = (
        "Q66 ledger: five Q60 targets now have tested functional roles for human shadow work. "
        "C68/NAESE slot, C86/VNCTIIN route, BENNA formula handoff, and 67->2 edge are strong; "
        "Book27 payload/context hold is moderate and still open. None are lexical word meanings, "
        "and no canonical plaintext is promoted."
    )
    decision = (
        "Q66_COMPONENT_ROLE_LEDGER_READY_5_ROLES_NO_GLOSS"
        if role_target_count == 5
        and functional_role_accepted_count == 5
        and strong_functional_role_count == 4
        and moderate_heldout_role_count == 1
        and lexical_ready_count == 0
        and direct_gloss_count == 0
        and canonical_promotion_allowed_count == 0
        and int(q60["candidate_count"]) == 5
        and int(q60["strong_role_candidate_count"]) == 4
        and int(q60["moderate_role_candidate_count"]) == 1
        and int(q60["lexical_ready_count"]) == 0
        and int(q65["stop_continue_resolved_count"]) == 0
        and int(audit["promoted_gloss_count"]) == 0
        else "Q66_COMPONENT_ROLE_LEDGER_REQUIRES_REVIEW"
    )
    payload = {
        "question": "What did Q60-Q65 actually establish?",
        "answer": ledger_human_version,
        "blocked_use": "Do not treat functional role labels as decoded Bonelord words or promoted book plaintext.",
        "next_action": "Use the ledger to select exact-source, stop-vs-continue, and lexical-falsification probes.",
        "source_run_decisions": {
            "q60": q60["decision"],
            "q61": q61["decision"],
            "q62": q62["decision"],
            "q63": q63["decision"],
            "q64": q64["decision"],
            "q65": q65["decision"],
            "completion_audit": audit["decision"],
        },
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q66_component_role_ledger_v1_runs (
                created_at, decision, q60_run_id, q61_run_id, q62_run_id,
                q63_run_id, q64_run_id, q65_run_id, completion_audit_run_id,
                role_target_count, functional_role_accepted_count,
                strong_functional_role_count, moderate_heldout_role_count,
                lexical_ready_count, direct_gloss_count,
                canonical_promotion_allowed_count, open_risk_count,
                ledger_human_version, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                int(q60["run_id"]),
                int(q61["run_id"]),
                int(q62["run_id"]),
                int(q63["run_id"]),
                int(q64["run_id"]),
                int(q65["run_id"]),
                int(audit["run_id"]),
                role_target_count,
                functional_role_accepted_count,
                strong_functional_role_count,
                moderate_heldout_role_count,
                lexical_ready_count,
                direct_gloss_count,
                canonical_promotion_allowed_count,
                open_risk_count,
                ledger_human_version,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q66_component_role_ledger_v1_roles (
                run_id, role_id, component_family, functional_label,
                evidence_source, evidence_run_id, q60_candidate_id,
                q60_evidence_strength, q60_role_status, role_strength,
                target_books_json, support_books_json, control_books_json,
                functional_accept_status, lexical_status, canonical_status,
                human_version, residual_risk, next_probe, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    row["role_id"],
                    row["component_family"],
                    row["functional_label"],
                    row["evidence_source"],
                    row["evidence_run_id"],
                    row["q60_candidate_id"],
                    row["q60_evidence_strength"],
                    row["q60_role_status"],
                    row["role_strength"],
                    j(row["target_books"]),
                    j(row["support_books"]),
                    j(row["control_books"]),
                    row["functional_accept_status"],
                    row["lexical_status"],
                    row["canonical_status"],
                    row["human_version"],
                    row["residual_risk"],
                    row["next_probe"],
                    j(row["evidence"]),
                )
                for row in role_rows
            ],
        )
        conn.executemany(
            """
            INSERT INTO human_q66_component_role_ledger_v1_risks (
                run_id, risk_id, risk_class, risk_status, consequence,
                next_action, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    risk["risk_id"],
                    risk["risk_class"],
                    risk["risk_status"],
                    risk["consequence"],
                    risk["next_action"],
                    j({"risk": risk, "ledger_decision": decision}),
                )
                for risk in RISK_SPECS
            ],
        )

    print(
        j(
            {
                "run_id": run_id,
                "decision": decision,
                "role_target_count": role_target_count,
                "functional_role_accepted_count": functional_role_accepted_count,
                "strong_functional_role_count": strong_functional_role_count,
                "moderate_heldout_role_count": moderate_heldout_role_count,
                "lexical_ready_count": lexical_ready_count,
                "direct_gloss_count": direct_gloss_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
                "open_risk_count": open_risk_count,
            }
        )
    )


if __name__ == "__main__":
    main()
