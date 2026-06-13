#!/usr/bin/env python3
"""Q60: queue component-role promotion targets from the Q59 shadow backbone."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

ROLE_CANDIDATES = [
    {
        "candidate_id": "Q60_C01_C68_NAESE_SLOT_CLASSIFIER_ROLE",
        "functional_label": "slot_classifier",
        "component_family": "C68_NAESE_SLOT",
        "target_books": ["2", "5"],
        "control_books": ["31", "57", "42"],
        "evidence_strength": "STRONG_ROLE_READY",
        "current_role_status": "ROLE_PROMOTION_CANDIDATE_LEXICAL_BLOCKED",
        "plausible_shadow_definition": (
            "C68/NAESE participates in slot/classifier transitions when the surrounding route supplies slot context."
        ),
        "blocked_lexical_claim": "Do not translate C68, NAESE, slot, or classifier as a Bonelord word.",
        "required_promotion_gate": (
            "Find minimal contrasts separating C68 phase/context windows from C68/NAESE slot windows without relying on English route labels."
        ),
        "next_probe": "Build a minimal-pair table for Book2, Book5, Book31, Book57, and Book42.",
    },
    {
        "candidate_id": "Q60_C02_C86_VNCTIIN_CONTEXT_ROUTE_ROLE",
        "functional_label": "context_route",
        "component_family": "C86_VNCTIIN_CONTEXT",
        "target_books": ["2", "10", "27", "35", "67"],
        "control_books": ["5", "31", "42", "57"],
        "evidence_strength": "STRONG_ROLE_READY",
        "current_role_status": "ROLE_PROMOTION_CANDIDATE_LEXICAL_BLOCKED",
        "plausible_shadow_definition": (
            "C86/VNCTIIN marks a context/payload route in the Q59 backbone and heldout variants."
        ),
        "blocked_lexical_claim": "Do not translate C86, VNCTIIN, context, payload, or route as a Bonelord word.",
        "required_promotion_gate": (
            "Contrast supported EVIEFIIN->VN/C68/TIIN routes against C86 audit surfaces and phase-only residues."
        ),
        "next_probe": "Run a C86 ready-vs-audit contrast over Books 2/10/27/35/67 versus 5/31/42/57.",
    },
    {
        "candidate_id": "Q60_C03_BENNA_FORMULA_HANDOFF_ROLE",
        "functional_label": "formula_handoff",
        "component_family": "BENNA_FORMULA",
        "target_books": ["35", "10"],
        "control_books": ["5", "31", "57"],
        "evidence_strength": "STRONG_ROLE_READY",
        "current_role_status": "ROLE_PROMOTION_CANDIDATE_LEXICAL_BLOCKED",
        "plausible_shadow_definition": (
            "BENNA-bearing formula bodies can hand off into context routing, with Book35 primary and Book10 heldout."
        ),
        "blocked_lexical_claim": "Do not translate BENNA, formula, body, or handoff as a Bonelord word.",
        "required_promotion_gate": (
            "Separate formula-to-context flow from Book5 slot-to-BENNA flow and from non-formula phase controls."
        ),
        "next_probe": "Run a directional BENNA contrast for Books 35/10 against Book5 and phase controls 31/57.",
    },
    {
        "candidate_id": "Q60_C04_EDGE_67_2_HANDOFF_ROLE",
        "functional_label": "handoff_edge",
        "component_family": "EDGE_67_2",
        "target_books": ["67", "2"],
        "control_books": ["27", "35", "42"],
        "evidence_strength": "STRONG_EDGE_READY",
        "current_role_status": "PHRASE_EDGE_PROMOTION_CANDIDATE_LEXICAL_BLOCKED",
        "plausible_shadow_definition": (
            "The 67->2 edge behaves as a context handoff into the Book2 slot/classifier target."
        ),
        "blocked_lexical_claim": "Do not translate the edge as a sentence or a fixed word sequence.",
        "required_promotion_gate": (
            "Show that 67->2 continuity is not reproduced by Book27, Book35, or Book42 controls."
        ),
        "next_probe": "Use exact-contig and edge evidence to test whether 35->67->2 can be read as one phrase path.",
    },
    {
        "candidate_id": "Q60_C05_PAYLOAD_CONTEXT_HOLD_ROLE",
        "functional_label": "payload_context_hold",
        "component_family": "PAYLOAD_CONTEXT_HELDOUT",
        "target_books": ["27"],
        "control_books": ["67", "2", "57", "42"],
        "evidence_strength": "MODERATE_ROLE_READY",
        "current_role_status": "HELDOUT_ROLE_CANDIDATE_LEXICAL_BLOCKED",
        "plausible_shadow_definition": (
            "Book27 behaves like a payload/context corridor that stays open without continuing into the immediate slot edge."
        ),
        "blocked_lexical_claim": "Do not translate payload/context hold as command, dead, soul, necromancy, or transformation.",
        "required_promotion_gate": (
            "Find a contrast showing whether Book27 stops in context or simply lacks the observed 67->2 edge."
        ),
        "next_probe": "Test Book27 against Book67->2 and weak controls 57/42 as a stop/continue contrast.",
    },
]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q60_component_role_promotion_queue_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q59_run_id INTEGER NOT NULL,
            q58_run_id INTEGER NOT NULL,
            q57_run_id INTEGER NOT NULL,
            q53_run_id INTEGER NOT NULL,
            q50_run_id INTEGER NOT NULL,
            q52_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            candidate_count INTEGER NOT NULL,
            strong_role_candidate_count INTEGER NOT NULL,
            moderate_role_candidate_count INTEGER NOT NULL,
            lexical_ready_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            direct_gloss_count INTEGER NOT NULL,
            queue_human_version TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q60_component_role_promotion_queue_v1_candidates (
            run_id INTEGER NOT NULL,
            candidate_id TEXT NOT NULL,
            functional_label TEXT NOT NULL,
            component_family TEXT NOT NULL,
            target_books_json TEXT NOT NULL,
            control_books_json TEXT NOT NULL,
            evidence_strength TEXT NOT NULL,
            current_role_status TEXT NOT NULL,
            plausible_shadow_definition TEXT NOT NULL,
            blocked_lexical_claim TEXT NOT NULL,
            required_promotion_gate TEXT NOT NULL,
            next_probe TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, candidate_id)
        );
        """
    )


def latest_row(conn: sqlite3.Connection, table: str) -> sqlite3.Row:
    row = conn.execute(f"SELECT * FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    if row is None:
        raise RuntimeError(f"missing required row: {table}")
    return row


def load_by_book(conn: sqlite3.Connection, table: str, run_id: int) -> dict[str, sqlite3.Row]:
    rows = conn.execute(f"SELECT * FROM {table} WHERE run_id=?", (run_id,)).fetchall()
    return {str(row["bookid"]): row for row in rows}


def evidence_for_books(
    bookids: list[str],
    q59_books: dict[str, sqlite3.Row],
    q53_books: dict[str, sqlite3.Row],
    q50_books: dict[str, sqlite3.Row],
    q52_books: dict[str, sqlite3.Row],
) -> dict[str, object]:
    return {
        bookid: {
            "q59": dict(q59_books[bookid]) if bookid in q59_books else None,
            "q53": dict(q53_books[bookid]) if bookid in q53_books else None,
            "q50": dict(q50_books[bookid]) if bookid in q50_books else None,
            "q52": dict(q52_books[bookid]) if bookid in q52_books else None,
        }
        for bookid in bookids
    }


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q59 = latest_row(conn, "human_q59_consolidated_shadow_backbone_v1_runs")
    q58 = latest_row(conn, "human_q58_execute_remaining_contrasts_firewall_v1_runs")
    q57 = latest_row(conn, "human_q57_execute_high_priority_contrasts_v1_runs")
    q53 = latest_row(conn, "human_q53_c86_c68_chain_synthesis_v1_runs")
    q50 = latest_row(conn, "human_q50_c68_book_synthesis_v1_runs")
    q52 = latest_row(conn, "human_q52_c86_book_synthesis_v1_runs")
    audit = latest_row(conn, "human_translation_completion_audit_v5_runs")

    q59_books = load_by_book(conn, "human_q59_consolidated_shadow_backbone_v1_books", int(q59["run_id"]))
    q53_books = load_by_book(conn, "human_q53_c86_c68_chain_synthesis_v1_books", int(q53["run_id"]))
    q50_books = load_by_book(conn, "human_q50_c68_book_synthesis_v1_books", int(q50["run_id"]))
    q52_books = load_by_book(conn, "human_q52_c86_book_synthesis_v1_books", int(q52["run_id"]))

    prepared = []
    for candidate in ROLE_CANDIDATES:
        target_books = [str(bookid) for bookid in candidate["target_books"]]
        control_books = [str(bookid) for bookid in candidate["control_books"]]
        all_books = sorted(set(target_books + control_books), key=lambda value: int(value))
        prepared.append(
            {
                **candidate,
                "target_books": target_books,
                "control_books": control_books,
                "evidence": {
                    "books": evidence_for_books(all_books, q59_books, q53_books, q50_books, q52_books),
                    "q59_run": dict(q59),
                    "q58_run": dict(q58),
                    "q57_run": dict(q57),
                    "completion_audit": dict(audit),
                },
            }
        )

    strong_role_candidate_count = sum(1 for item in prepared if str(item["evidence_strength"]).startswith("STRONG"))
    moderate_role_candidate_count = sum(1 for item in prepared if str(item["evidence_strength"]).startswith("MODERATE"))
    lexical_ready_count = 0
    canonical_promotion_allowed_count = 0
    direct_gloss_count = 0
    queue_human_version = (
        "Q60 converts the tested Q59 shadow backbone into five component-role promotion targets. "
        "All are role-ready targets for future contrast work, but lexical promotion remains blocked."
    )
    decision = (
        "Q60_COMPONENT_ROLE_PROMOTION_QUEUE_READY_5_TARGETS_NO_GLOSS"
        if len(prepared) == 5
        and strong_role_candidate_count == 4
        and moderate_role_candidate_count == 1
        and lexical_ready_count == 0
        and int(q59["accepted_shadow_phrase_count"]) == 5
        and int(q58["accepted_firewall_test_count"]) == 1
        and int(audit["promoted_gloss_count"]) == 0
        and direct_gloss_count == 0
        and canonical_promotion_allowed_count == 0
        else "Q60_COMPONENT_ROLE_PROMOTION_QUEUE_REQUIRES_REVIEW"
    )
    payload = {
        "question": "Which Q59 functional labels can become the next component-role promotion targets?",
        "answer": "Five role targets are ready for contrast work, but none is lexical-ready.",
        "queue_human_version": queue_human_version,
        "blocked_use": "No candidate is a word gloss or canonical translation.",
        "next_action": "Execute the strongest minimal-pair probes for C68/NAESE slot and C86/VNCTIIN context route.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q60_component_role_promotion_queue_v1_runs (
                created_at, decision, q59_run_id, q58_run_id, q57_run_id,
                q53_run_id, q50_run_id, q52_run_id, completion_audit_run_id,
                candidate_count, strong_role_candidate_count,
                moderate_role_candidate_count, lexical_ready_count,
                canonical_promotion_allowed_count, direct_gloss_count,
                queue_human_version, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                int(q59["run_id"]),
                int(q58["run_id"]),
                int(q57["run_id"]),
                int(q53["run_id"]),
                int(q50["run_id"]),
                int(q52["run_id"]),
                int(audit["run_id"]),
                len(prepared),
                strong_role_candidate_count,
                moderate_role_candidate_count,
                lexical_ready_count,
                canonical_promotion_allowed_count,
                direct_gloss_count,
                queue_human_version,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q60_component_role_promotion_queue_v1_candidates (
                run_id, candidate_id, functional_label, component_family,
                target_books_json, control_books_json, evidence_strength,
                current_role_status, plausible_shadow_definition,
                blocked_lexical_claim, required_promotion_gate, next_probe,
                evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    str(item["candidate_id"]),
                    str(item["functional_label"]),
                    str(item["component_family"]),
                    j(item["target_books"]),
                    j(item["control_books"]),
                    str(item["evidence_strength"]),
                    str(item["current_role_status"]),
                    str(item["plausible_shadow_definition"]),
                    str(item["blocked_lexical_claim"]),
                    str(item["required_promotion_gate"]),
                    str(item["next_probe"]),
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
                "candidate_count": len(prepared),
                "strong_role_candidate_count": strong_role_candidate_count,
                "moderate_role_candidate_count": moderate_role_candidate_count,
                "lexical_ready_count": lexical_ready_count,
                "direct_gloss_count": direct_gloss_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
            }
        )
    )


if __name__ == "__main__":
    main()
