#!/usr/bin/env python3
"""Q67: build a lexical-anchor probe queue from the Q66 role ledger."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

PROBE_SPECS = [
    {
        "probe_id": "Q67_P01_C68_NAESE_SLOT_EXACT_SOURCE",
        "role_id": "C68_NAESE_SLOT",
        "probe_family": "LEXICAL_EXACT_SOURCE",
        "source_ids": ["THREAT_III_MIND_BODY_SOUL_EXPERIMENTS", "PARADOX_1_PLUS_1_KEYS"],
        "priority": "HIGH",
        "search_question": (
            "Is there an in-game text or quest mechanic that gives an exact sequence-level "
            "meaning for the C68/NAESE slot/classifier window?"
        ),
        "required_evidence": (
            "An exact Bonelord sequence, book/quest provenance, and a source-provided meaning "
            "or mechanically forced value that separates slot/classifier from phase/context controls."
        ),
        "rejection_rule": (
            "Reject mappings such as NAESE/C68 = soul, mind, body, monster, or key unless the "
            "same exact sequence and contrast are present in-game."
        ),
        "expected_failure_mode": "Source lore supports experimental register but not exact word meaning.",
        "next_action": "Search exact 469 subsequences beside Threat III and Paradox mechanics; keep Book31/57/42 controls active.",
    },
    {
        "probe_id": "Q67_P02_C86_VNCTIIN_CONTEXT_COMMAND_CONTROL",
        "role_id": "C86_VNCTIIN_CONTEXT",
        "probe_family": "REGISTER_TO_LEXICAL_FIREWALL",
        "source_ids": ["THREAT_I_EYESTALK_MAGIC_COMMAND_DEAD", "THREAT_II_RESEARCH_EXPERIMENTS"],
        "priority": "HIGH",
        "search_question": (
            "Can command/control/research lore distinguish C86/VNCTIIN context-route from "
            "surface-audit controls without turning lore words into dictionary glosses?"
        ),
        "required_evidence": (
            "A direct in-game relation between a C86/VNCTIIN-bearing sequence and a specific "
            "control/research action, plus negative controls for C86 audit surfaces."
        ),
        "rejection_rule": (
            "Reject C86/VNCTIIN = command, dead, eye, necromancy, research, payload, or context "
            "unless the exact phrase-plus-meaning relation is sourced."
        ),
        "expected_failure_mode": "Quest/book register is strong but does not name the sequence.",
        "next_action": "Use ready books 2/10/27/35/67 versus audit controls 5/31/42/57 as the search frame.",
    },
    {
        "probe_id": "Q67_P03_BENNA_FORMULA_MATHEMAGIC_OPERATOR",
        "role_id": "BENNA_FORMULA",
        "probe_family": "MATHEMAGIC_OPERATOR_ANCHOR",
        "source_ids": ["AWB_469_LANGUAGE_MATHEMAGIC", "BEWARE_LANGUAGE_MATH_NUMERIC_BOOKS", "PARADOX_1_PLUS_1_KEYS"],
        "priority": "HIGH",
        "search_question": (
            "Can Mathemagica or numeric Bonelord-language sources provide a repeatable operator "
            "model for BENNA formula handoff?"
        ),
        "required_evidence": (
            "A repeatable operator rule that predicts BENNA-bearing formula handoff against Book5 "
            "and non-formula controls, preferably with exact in-game wording or mechanic provenance."
        ),
        "rejection_rule": (
            "Reject 1/13/49/94 or other mathemagic values as a dictionary unless they predict the "
            "BENNA role and fail the controls."
        ),
        "expected_failure_mode": "Mathemagic explains method pressure but not BENNA lexical content.",
        "next_action": "Treat Book35/10 as targets and Book5/31/57 as mandatory falsifiers for any operator rule.",
    },
    {
        "probe_id": "Q67_P04_EDGE_67_2_PHRASE_PATH_CONTINUITY",
        "role_id": "EDGE_67_2",
        "probe_family": "PHRASE_PATH_SOURCE_CONTINUITY",
        "source_ids": ["GREAT_CALCULATOR_GATHER_LANGUAGE", "BEWARE_LANGUAGE_MATH_NUMERIC_BOOKS"],
        "priority": "MEDIUM",
        "search_question": (
            "Does any in-game source explain a compiled or gathered-language packet that would make "
            "35->67->2 a phrase path rather than only a structural contig?"
        ),
        "required_evidence": (
            "A source-backed continuity rule or exact phrase parallel showing why 67->2 hands off "
            "into Book2, with Book27/35/42 failing the same edge condition."
        ),
        "rejection_rule": "Reject any sentence translation of Book67 or Book2 that is not tied to the exact edge.",
        "expected_failure_mode": "Corpus-assembly sources support packet structure but not phrase plaintext.",
        "next_action": "Use the exact contig 35->67->2 as the source-search spine and keep Book27 as heldout control.",
    },
    {
        "probe_id": "Q67_P05_BOOK27_STOP_VS_CONTINUATION",
        "role_id": "PAYLOAD_CONTEXT_HELDOUT",
        "probe_family": "HELDOUT_STOP_CONTINUE_GATE",
        "source_ids": [
            "THREAT_I_EYESTALK_MAGIC_COMMAND_DEAD",
            "THREAT_II_RESEARCH_EXPERIMENTS",
            "THREAT_III_MIND_BODY_SOUL_EXPERIMENTS",
        ],
        "priority": "HIGH",
        "search_question": "Does Book27 stop in payload/context hold, or does it lack the observed 67->2 continuation?",
        "required_evidence": (
            "A contrast or source relation that decides endpoint versus missing continuation without "
            "promoting a command/dead/soul/transformation gloss."
        ),
        "rejection_rule": "Reject endpoint, command, necromancy, or transformation readings without an exact contrast.",
        "expected_failure_mode": "Book27 remains useful as heldout context but cannot be strengthened.",
        "next_action": "Search for Book27-near sequences or source parallels that predict absence or presence of a next edge.",
    },
    {
        "probe_id": "Q67_P06_GLOBAL_SOURCE_FIREWALL_NEGATIVE_CONTROL",
        "role_id": "ALL_Q66_ROLES",
        "probe_family": "SOURCE_FIREWALL_NEGATIVE_CONTROL",
        "source_ids": [
            "AWB_469_LANGUAGE_MATHEMAGIC",
            "BEWARE_LANGUAGE_MATH_NUMERIC_BOOKS",
            "BEWARE_UNSPEAKABLE_RITUALS_UNDEAD_ARMY",
            "GREAT_CALCULATOR_GATHER_LANGUAGE",
            "PARADOX_1_PLUS_1_KEYS",
            "THREAT_I_EYESTALK_MAGIC_COMMAND_DEAD",
            "THREAT_II_RESEARCH_EXPERIMENTS",
            "THREAT_III_MIND_BODY_SOUL_EXPERIMENTS",
        ],
        "priority": "HARD_GATE",
        "search_question": "Does a candidate use source lore as register only, or does it smuggle in a dictionary gloss?",
        "required_evidence": (
            "Every lexical candidate must name the exact source, exact sequence, provenance, accepted controls, "
            "failed controls, and contradiction audit before promotion."
        ),
        "rejection_rule": "Reject every candidate whose evidence is only plausible lore, translation vibe, or register fit.",
        "expected_failure_mode": "Most candidates remain shadow/search prompts rather than lexical promotions.",
        "next_action": "Run this as a hard gate before any future lexical or canonical promotion package.",
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
        CREATE TABLE IF NOT EXISTS human_q67_lexical_anchor_probe_queue_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q66_run_id INTEGER NOT NULL,
            q55_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            role_count INTEGER NOT NULL,
            source_count INTEGER NOT NULL,
            probe_count INTEGER NOT NULL,
            high_priority_probe_count INTEGER NOT NULL,
            hard_gate_probe_count INTEGER NOT NULL,
            exact_sequence_required_count INTEGER NOT NULL,
            no_dictionary_firewall_count INTEGER NOT NULL,
            lexical_ready_count INTEGER NOT NULL,
            direct_gloss_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            queue_human_version TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q67_lexical_anchor_probe_queue_v1_probes (
            run_id INTEGER NOT NULL,
            probe_id TEXT NOT NULL,
            role_id TEXT NOT NULL,
            functional_label TEXT NOT NULL,
            role_strength TEXT NOT NULL,
            probe_family TEXT NOT NULL,
            priority TEXT NOT NULL,
            source_ids_json TEXT NOT NULL,
            source_urls_json TEXT NOT NULL,
            search_question TEXT NOT NULL,
            required_evidence TEXT NOT NULL,
            rejection_rule TEXT NOT NULL,
            expected_failure_mode TEXT NOT NULL,
            lexical_claim_allowed INTEGER NOT NULL,
            canonical_promotion_allowed INTEGER NOT NULL,
            probe_status TEXT NOT NULL,
            next_action TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, probe_id)
        );

        CREATE TABLE IF NOT EXISTS human_q67_lexical_anchor_probe_queue_v1_sources (
            run_id INTEGER NOT NULL,
            source_id TEXT NOT NULL,
            source_url TEXT NOT NULL,
            source_role TEXT NOT NULL,
            source_parallel_use TEXT NOT NULL,
            blocked_inference TEXT NOT NULL,
            source_use_status TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, source_id)
        );
        """
    )


def latest_row(conn: sqlite3.Connection, table: str) -> sqlite3.Row:
    row = conn.execute(f"SELECT * FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    if row is None:
        raise RuntimeError(f"missing required row: {table}")
    return row


def load_q66_roles(conn: sqlite3.Connection, q66_run_id: int) -> dict[str, sqlite3.Row]:
    rows = conn.execute(
        """
        SELECT *
        FROM human_q66_component_role_ledger_v1_roles
        WHERE run_id=?
        """,
        (q66_run_id,),
    ).fetchall()
    roles = {str(row["role_id"]): row for row in rows}
    roles["ALL_Q66_ROLES"] = sqlite3.Row  # sentinel checked separately
    return roles


def load_q55_sources(conn: sqlite3.Connection, q55_run_id: int) -> dict[str, sqlite3.Row]:
    rows = conn.execute(
        """
        SELECT *
        FROM human_q55_source_parallel_audit_q54_v1_sources
        WHERE run_id=?
        """,
        (q55_run_id,),
    ).fetchall()
    return {str(row["source_id"]): row for row in rows}


def role_details(role_id: str, roles: dict[str, sqlite3.Row]) -> tuple[str, str]:
    if role_id == "ALL_Q66_ROLES":
        return "all_q66_roles", "HARD_GATE_ALL_ROLES"
    role = roles.get(role_id)
    if role is None:
        raise RuntimeError(f"missing Q66 role: {role_id}")
    return str(role["functional_label"]), str(role["role_strength"])


def build_probe_rows(roles: dict[str, sqlite3.Row], sources: dict[str, sqlite3.Row]) -> list[dict[str, object]]:
    rows = []
    for spec in PROBE_SPECS:
        role_id = str(spec["role_id"])
        functional_label, role_strength = role_details(role_id, roles)
        missing_sources = [source_id for source_id in spec["source_ids"] if source_id not in sources]
        if missing_sources:
            raise RuntimeError(f"missing source ids for {spec['probe_id']}: {missing_sources}")
        source_rows = [sources[source_id] for source_id in spec["source_ids"]]
        role_evidence = None if role_id == "ALL_Q66_ROLES" else brief(
            roles[role_id],
            [
                "role_id",
                "component_family",
                "functional_label",
                "role_strength",
                "functional_accept_status",
                "lexical_status",
                "canonical_status",
                "residual_risk",
                "next_probe",
            ],
        )
        rows.append(
            {
                "probe_id": spec["probe_id"],
                "role_id": role_id,
                "functional_label": functional_label,
                "role_strength": role_strength,
                "probe_family": spec["probe_family"],
                "priority": spec["priority"],
                "source_ids": spec["source_ids"],
                "source_urls": sorted({str(row["source_url"]) for row in source_rows}),
                "search_question": spec["search_question"],
                "required_evidence": spec["required_evidence"],
                "rejection_rule": spec["rejection_rule"],
                "expected_failure_mode": spec["expected_failure_mode"],
                "lexical_claim_allowed": 0,
                "canonical_promotion_allowed": 0,
                "probe_status": "QUEUED_REQUIRES_EXACT_SEQUENCE_NO_GLOSS",
                "next_action": spec["next_action"],
                "evidence": {
                    "role": role_evidence,
                    "sources": [
                        brief(
                            row,
                            [
                                "source_id",
                                "source_url",
                                "source_role",
                                "source_claim",
                                "source_parallel_use",
                                "blocked_inference",
                                "web_check_status",
                            ],
                        )
                        for row in source_rows
                    ],
                },
            }
        )
    return rows


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q66 = latest_row(conn, "human_q66_component_role_ledger_v1_runs")
    q55 = latest_row(conn, "human_q55_source_parallel_audit_q54_v1_runs")
    audit = latest_row(conn, "human_translation_completion_audit_v5_runs")
    roles = load_q66_roles(conn, int(q66["run_id"]))
    sources = load_q55_sources(conn, int(q55["run_id"]))
    probe_rows = build_probe_rows(roles, sources)

    role_count = int(q66["role_target_count"])
    source_count = len({source_id for probe in probe_rows for source_id in probe["source_ids"]})
    probe_count = len(probe_rows)
    high_priority_probe_count = sum(1 for probe in probe_rows if probe["priority"] == "HIGH")
    hard_gate_probe_count = sum(1 for probe in probe_rows if probe["priority"] == "HARD_GATE")
    exact_sequence_required_count = probe_count
    no_dictionary_firewall_count = probe_count
    lexical_ready_count = 0
    direct_gloss_count = 0
    canonical_promotion_allowed_count = 0
    queue_human_version = (
        "Q67 lexical-anchor queue: the next work is not to invent prose, but to test six "
        "source-anchored probes. Each probe requires exact sequence/provenance evidence and "
        "keeps Mathemagica, Great Calculator, and Bonelord lore as register constraints unless "
        "a hard in-game phrase relation appears."
    )
    decision = (
        "Q67_LEXICAL_ANCHOR_PROBE_QUEUE_READY_6_PROBES_NO_GLOSS"
        if role_count == 5
        and source_count == 8
        and probe_count == 6
        and high_priority_probe_count == 4
        and hard_gate_probe_count == 1
        and exact_sequence_required_count == 6
        and no_dictionary_firewall_count == 6
        and int(q66["functional_role_accepted_count"]) == 5
        and int(q66["lexical_ready_count"]) == 0
        and int(q66["canonical_promotion_allowed_count"]) == 0
        and int(audit["promoted_gloss_count"]) == 0
        and lexical_ready_count == 0
        and direct_gloss_count == 0
        and canonical_promotion_allowed_count == 0
        else "Q67_LEXICAL_ANCHOR_PROBE_QUEUE_REQUIRES_REVIEW"
    )
    payload = {
        "question": "What should be tested next to move from functional roles toward lexical translation?",
        "answer": queue_human_version,
        "blocked_use": "No probe permits lexical or canonical promotion until exact sequence evidence is found.",
        "next_action": "Execute the high-priority probes, starting with BENNA/Mathemagica and Book27 stop-vs-continuation.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q67_lexical_anchor_probe_queue_v1_runs (
                created_at, decision, q66_run_id, q55_run_id,
                completion_audit_run_id, role_count, source_count, probe_count,
                high_priority_probe_count, hard_gate_probe_count,
                exact_sequence_required_count, no_dictionary_firewall_count,
                lexical_ready_count, direct_gloss_count,
                canonical_promotion_allowed_count, queue_human_version, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                int(q66["run_id"]),
                int(q55["run_id"]),
                int(audit["run_id"]),
                role_count,
                source_count,
                probe_count,
                high_priority_probe_count,
                hard_gate_probe_count,
                exact_sequence_required_count,
                no_dictionary_firewall_count,
                lexical_ready_count,
                direct_gloss_count,
                canonical_promotion_allowed_count,
                queue_human_version,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q67_lexical_anchor_probe_queue_v1_probes (
                run_id, probe_id, role_id, functional_label, role_strength,
                probe_family, priority, source_ids_json, source_urls_json,
                search_question, required_evidence, rejection_rule,
                expected_failure_mode, lexical_claim_allowed,
                canonical_promotion_allowed, probe_status, next_action,
                evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    row["probe_id"],
                    row["role_id"],
                    row["functional_label"],
                    row["role_strength"],
                    row["probe_family"],
                    row["priority"],
                    j(row["source_ids"]),
                    j(row["source_urls"]),
                    row["search_question"],
                    row["required_evidence"],
                    row["rejection_rule"],
                    row["expected_failure_mode"],
                    int(row["lexical_claim_allowed"]),
                    int(row["canonical_promotion_allowed"]),
                    row["probe_status"],
                    row["next_action"],
                    j(row["evidence"]),
                )
                for row in probe_rows
            ],
        )
        conn.executemany(
            """
            INSERT INTO human_q67_lexical_anchor_probe_queue_v1_sources (
                run_id, source_id, source_url, source_role,
                source_parallel_use, blocked_inference,
                source_use_status, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    source_id,
                    str(row["source_url"]),
                    str(row["source_role"]),
                    str(row["source_parallel_use"]),
                    str(row["blocked_inference"]),
                    "REGISTER_CONSTRAINT_OR_SEARCH_TARGET_NO_DICTIONARY",
                    j(
                        brief(
                            row,
                            [
                                "source_id",
                                "source_origin",
                                "source_origin_run_id",
                                "source_url",
                                "source_role",
                                "source_claim",
                                "source_parallel_use",
                                "web_check_status",
                                "allowed_inference",
                                "blocked_inference",
                            ],
                        )
                    ),
                )
                for source_id, row in sorted(sources.items())
                if source_id in {source_id for probe in probe_rows for source_id in probe["source_ids"]}
            ],
        )

    print(
        j(
            {
                "run_id": run_id,
                "decision": decision,
                "role_count": role_count,
                "source_count": source_count,
                "probe_count": probe_count,
                "high_priority_probe_count": high_priority_probe_count,
                "hard_gate_probe_count": hard_gate_probe_count,
                "exact_sequence_required_count": exact_sequence_required_count,
                "no_dictionary_firewall_count": no_dictionary_firewall_count,
                "lexical_ready_count": lexical_ready_count,
                "direct_gloss_count": direct_gloss_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
            }
        )
    )


if __name__ == "__main__":
    main()
