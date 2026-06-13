#!/usr/bin/env python3
"""Q56: turn Q55 source-linked phrase readings into falsifiable contrast tests."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"


CONTRAST_TESTS = [
    {
        "test_id": "Q56_T01_CONTEXT_TO_SLOT_CLASSIFIER",
        "test_family": "CONTEXT_TO_SLOT_CLASSIFIER",
        "priority": "HIGH",
        "target_books": ["2"],
        "control_books": ["5", "42"],
        "quarantine_control_books": ["42"],
        "source_ids": [
            "AWB_469_LANGUAGE_MATHEMAGIC",
            "GREAT_CALCULATOR_GATHER_LANGUAGE",
            "PARADOX_1_PLUS_1_KEYS",
            "BEWARE_LANGUAGE_MATH_NUMERIC_BOOKS",
            "THREAT_II_RESEARCH_EXPERIMENTS",
            "THREAT_III_MIND_BODY_SOUL_EXPERIMENTS",
        ],
        "contrast_question": (
            "Does Book 2 require both the supported C86 EVIEFIIN context selector and the C68 mixed phase/slot hinge "
            "before the human phrase can say selected context -> classifier slot?"
        ),
        "acceptance_signal": (
            "Book 2 remains the only Q54 target with SUPPORTED_CONTEXT_TO_SLOT_CHAIN and C68_MIXED_PHASE_SLOT_CHAIN; "
            "Book 5 shows C68 slot material alone is insufficient, and Book 42 remains a dual audit boundary control."
        ),
        "falsification_signal": (
            "If Book 5 or Book 42 can support the same context-to-slot reading without C86 edge support, the word "
            "'selected' or the classifier route is overfit and must be demoted."
        ),
        "next_action": "Run a focused Book2 vs Book5/42 contrast on C86 support and C68 slot/phase hinge behavior.",
    },
    {
        "test_id": "Q56_T02_67_TO_2_HANDOFF_EDGE",
        "test_family": "HANDOFF_EDGE_TO_SLOT",
        "priority": "HIGH",
        "target_books": ["67", "2"],
        "control_books": ["27", "35", "42"],
        "quarantine_control_books": ["42"],
        "source_ids": [
            "AWB_469_LANGUAGE_MATHEMAGIC",
            "GREAT_CALCULATOR_GATHER_LANGUAGE",
            "BEWARE_LANGUAGE_MATH_NUMERIC_BOOKS",
            "BEWARE_UNSPEAKABLE_RITUALS_UNDEAD_ARMY",
            "THREAT_II_RESEARCH_EXPERIMENTS",
            "THREAT_III_MIND_BODY_SOUL_EXPERIMENTS",
        ],
        "contrast_question": (
            "Does Book 67 function as the immediate context handoff into Book 2's classifier slot rather than as a "
            "standalone payload sentence?"
        ),
        "acceptance_signal": (
            "Book 67 stays in the supported C86/C68 context route and Book 2 uniquely continues into the mixed "
            "phase/slot chain; ritual/research sources support handoff register only."
        ),
        "falsification_signal": (
            "If Book 67 behaves as terminal, exit, or a complete standalone clause, or if Book 2 loses the slot hinge, "
            "the 67->2 phrase handoff must be demoted."
        ),
        "next_action": "Compare the 67->2 edge against Book27 corridor behavior and Book35 upstream formula routing.",
    },
    {
        "test_id": "Q56_T03_FORMULA_TO_CONTEXT_CONTIG",
        "test_family": "FORMULA_TO_CONTEXT_CONTIG",
        "priority": "HIGH",
        "target_books": ["35"],
        "control_books": ["10", "31", "57", "5"],
        "quarantine_control_books": [],
        "source_ids": [
            "AWB_469_LANGUAGE_MATHEMAGIC",
            "GREAT_CALCULATOR_GATHER_LANGUAGE",
            "PARADOX_1_PLUS_1_KEYS",
            "BEWARE_LANGUAGE_MATH_NUMERIC_BOOKS",
            "BEWARE_UNSPEAKABLE_RITUALS_UNDEAD_ARMY",
            "THREAT_II_RESEARCH_EXPERIMENTS",
        ],
        "contrast_question": (
            "Is Book 35 specifically a formula body handing context toward the supported classifier path, rather than "
            "generic phase/context prose?"
        ),
        "acceptance_signal": (
            "Book 35 keeps BENNA/formula-concordance structure plus supported C86/C68 context routing and exact contig "
            "placement before 67->2; Books 31/57 remain phase-context controls without formula handoff."
        ),
        "falsification_signal": (
            "If Books 31/57 support the same formula-to-context reading without formula evidence, or Book 5's "
            "slot-to-formula flow matches Book 35, the phrase wording is too broad."
        ),
        "next_action": "Contrast Book35 against Book10 as heldout and Books31/57 as non-formula phase controls.",
    },
    {
        "test_id": "Q56_T04_FORMULA_HANDOFF_HELDOUT",
        "test_family": "FORMULA_HANDOFF_HELDOUT",
        "priority": "MEDIUM",
        "target_books": ["10"],
        "control_books": ["35", "31", "57"],
        "quarantine_control_books": [],
        "source_ids": [
            "AWB_469_LANGUAGE_MATHEMAGIC",
            "PARADOX_1_PLUS_1_KEYS",
            "BEWARE_LANGUAGE_MATH_NUMERIC_BOOKS",
            "BEWARE_UNSPEAKABLE_RITUALS_UNDEAD_ARMY",
            "THREAT_II_RESEARCH_EXPERIMENTS",
        ],
        "contrast_question": (
            "Can Book 10 keep a moderate formula-handoff reading when it lacks Book 35's exact contig-edge support?"
        ),
        "acceptance_signal": (
            "Book 10 shares formula/concordance -> supported C86/C68 context routing with Book 35, but remains lower "
            "confidence because it is held out from the exact 35->67->2 edge."
        ),
        "falsification_signal": (
            "If Book 10 cannot be mechanically separated from generic phase controls, its phrase should be reduced to "
            "context routing with no formula handoff wording."
        ),
        "next_action": "Score Book10 against Book35 features and against Books31/57 phase-only controls.",
    },
    {
        "test_id": "Q56_T05_PAYLOAD_CONTEXT_HOLD",
        "test_family": "PAYLOAD_CONTEXT_HOLD",
        "priority": "MEDIUM",
        "target_books": ["27"],
        "control_books": ["67", "2", "57", "42"],
        "quarantine_control_books": ["42"],
        "source_ids": [
            "AWB_469_LANGUAGE_MATHEMAGIC",
            "GREAT_CALCULATOR_GATHER_LANGUAGE",
            "PARADOX_1_PLUS_1_KEYS",
            "THREAT_I_EYESTALK_MAGIC_COMMAND_DEAD",
            "THREAT_II_RESEARCH_EXPERIMENTS",
            "THREAT_III_MIND_BODY_SOUL_EXPERIMENTS",
        ],
        "contrast_question": (
            "Does Book 27 hold a selected payload/context corridor open, without becoming a direct command, dead, "
            "soul, or necromancy gloss?"
        ),
        "acceptance_signal": (
            "Book 27 remains a supported C86/VN/C68/TIIN context route with phase-context C68, but does not continue "
            "into Book2's slot hinge or Book67's immediate handoff edge."
        ),
        "falsification_signal": (
            "If Threat I/III sources are needed as dictionary meanings, or if weak controls 57/42 support the same "
            "corridor reading, the held-context phrase is overclaimed."
        ),
        "next_action": "Search for payload/context contrasts that distinguish hold-open route from command/control overreach.",
    },
    {
        "test_id": "Q56_T06_SOURCE_OVERREACH_FIREWALL",
        "test_family": "SOURCE_OVERREACH_FIREWALL",
        "priority": "HARD_GATE",
        "target_books": ["2", "10", "27", "35", "67"],
        "control_books": ["5", "31", "42", "57", "23", "56"],
        "quarantine_control_books": ["23", "42", "56"],
        "source_ids": [
            "AWB_469_LANGUAGE_MATHEMAGIC",
            "GREAT_CALCULATOR_GATHER_LANGUAGE",
            "PARADOX_1_PLUS_1_KEYS",
            "BEWARE_LANGUAGE_MATH_NUMERIC_BOOKS",
            "BEWARE_UNSPEAKABLE_RITUALS_UNDEAD_ARMY",
            "THREAT_I_EYESTALK_MAGIC_COMMAND_DEAD",
            "THREAT_II_RESEARCH_EXPERIMENTS",
            "THREAT_III_MIND_BODY_SOUL_EXPERIMENTS",
        ],
        "contrast_question": (
            "Does every Q54/Q55 human phrase remain a source-constrained shadow route instead of a dictionary or "
            "canonical sentence translation?"
        ),
        "acceptance_signal": (
            "All source links remain method/register support; Q55 direct_gloss_count, prose_gloss_allowed_count, and "
            "canonical_promotion_allowed_count stay zero; completion audit promoted_gloss_count stays zero."
        ),
        "falsification_signal": (
            "Any component gloss, sentence gloss, or canonical plaintext derived directly from Q55 sources fails the "
            "firewall and must be quarantined before further synthesis."
        ),
        "next_action": "Run after each future phrase synthesis before promoting any human wording.",
    },
]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q56_source_linked_contrast_queue_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q55_run_id INTEGER NOT NULL,
            q53_run_id INTEGER NOT NULL,
            q50_run_id INTEGER NOT NULL,
            q52_run_id INTEGER NOT NULL,
            q49_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            contrast_test_count INTEGER NOT NULL,
            high_priority_test_count INTEGER NOT NULL,
            medium_priority_test_count INTEGER NOT NULL,
            hard_gate_test_count INTEGER NOT NULL,
            target_book_count INTEGER NOT NULL,
            control_book_count INTEGER NOT NULL,
            source_link_count INTEGER NOT NULL,
            direct_gloss_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            queue_human_version TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q56_source_linked_contrast_queue_v1_tests (
            run_id INTEGER NOT NULL,
            test_id TEXT NOT NULL,
            test_family TEXT NOT NULL,
            priority TEXT NOT NULL,
            target_books_json TEXT NOT NULL,
            control_books_json TEXT NOT NULL,
            quarantine_control_books_json TEXT NOT NULL,
            source_ids_json TEXT NOT NULL,
            phrase_readings_json TEXT NOT NULL,
            contrast_question TEXT NOT NULL,
            acceptance_signal TEXT NOT NULL,
            falsification_signal TEXT NOT NULL,
            current_status TEXT NOT NULL,
            allowed_inference TEXT NOT NULL,
            blocked_overreach TEXT NOT NULL,
            next_action TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, test_id)
        );
        """
    )


def latest_row(conn: sqlite3.Connection, table: str) -> sqlite3.Row:
    row = conn.execute(f"SELECT * FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    if row is None:
        raise RuntimeError(f"missing required row: {table}")
    return row


def latest_item_run_id(conn: sqlite3.Connection, table: str, id_column: str) -> int:
    row = conn.execute(f"SELECT max(run_id) AS run_id FROM {table} WHERE {id_column} IS NOT NULL").fetchone()
    if row is None or row["run_id"] is None:
        raise RuntimeError(f"missing required item run: {table}")
    return int(row["run_id"])


def load_by_book(conn: sqlite3.Connection, table: str, run_id: int) -> dict[str, sqlite3.Row]:
    rows = conn.execute(f"SELECT * FROM {table} WHERE run_id=?", (run_id,)).fetchall()
    return {str(row["bookid"]): row for row in rows}


def load_q55_sources(conn: sqlite3.Connection, q55_run_id: int) -> dict[str, sqlite3.Row]:
    rows = conn.execute(
        "SELECT * FROM human_q55_source_parallel_audit_q54_v1_sources WHERE run_id=?",
        (q55_run_id,),
    ).fetchall()
    return {str(row["source_id"]): row for row in rows}


def phrase_readings(test: dict[str, object], q55_books: dict[str, sqlite3.Row]) -> dict[str, str]:
    readings = {}
    for bookid in test["target_books"]:  # type: ignore[index]
        row = q55_books.get(str(bookid))
        if row is not None:
            readings[str(bookid)] = str(row["phrase_functional_version"])
    return readings


def evidence_for_books(
    bookids: list[str],
    q55_books: dict[str, sqlite3.Row],
    q53_books: dict[str, sqlite3.Row],
    q50_books: dict[str, sqlite3.Row],
    q52_books: dict[str, sqlite3.Row],
    q49_items: dict[str, list[sqlite3.Row]],
) -> dict[str, object]:
    evidence: dict[str, object] = {}
    for bookid in bookids:
        evidence[bookid] = {
            "q55": dict(q55_books[bookid]) if bookid in q55_books else None,
            "q53": dict(q53_books[bookid]) if bookid in q53_books else None,
            "q50": dict(q50_books[bookid]) if bookid in q50_books else None,
            "q52": dict(q52_books[bookid]) if bookid in q52_books else None,
            "q49_quarantine": [dict(row) for row in q49_items.get(bookid, [])],
        }
    return evidence


def load_q49_items(conn: sqlite3.Connection, q49_run_id: int) -> dict[str, list[sqlite3.Row]]:
    rows = conn.execute(
        "SELECT * FROM human_q49_c68_extra_subclass_quarantine_v1_items WHERE run_id=?",
        (q49_run_id,),
    ).fetchall()
    by_book: dict[str, list[sqlite3.Row]] = {}
    for row in rows:
        by_book.setdefault(str(row["bookid"]), []).append(row)
    return by_book


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q55 = latest_row(conn, "human_q55_source_parallel_audit_q54_v1_runs")
    q53 = latest_row(conn, "human_q53_c86_c68_chain_synthesis_v1_runs")
    q50 = latest_row(conn, "human_q50_c68_book_synthesis_v1_runs")
    q52 = latest_row(conn, "human_q52_c86_book_synthesis_v1_runs")
    audit = latest_row(conn, "human_translation_completion_audit_v5_runs")
    q49_run_id = latest_item_run_id(conn, "human_q49_c68_extra_subclass_quarantine_v1_items", "bookid")

    q55_books = load_by_book(conn, "human_q55_source_parallel_audit_q54_v1_books", int(q55["run_id"]))
    q53_books = load_by_book(conn, "human_q53_c86_c68_chain_synthesis_v1_books", int(q53["run_id"]))
    q50_books = load_by_book(conn, "human_q50_c68_book_synthesis_v1_books", int(q50["run_id"]))
    q52_books = load_by_book(conn, "human_q52_c86_book_synthesis_v1_books", int(q52["run_id"]))
    q49_items = load_q49_items(conn, q49_run_id)
    q55_sources = load_q55_sources(conn, int(q55["run_id"]))

    prepared = []
    for test in CONTRAST_TESTS:
        target_books = [str(bookid) for bookid in test["target_books"]]
        control_books = [str(bookid) for bookid in test["control_books"]]
        quarantine_control_books = [str(bookid) for bookid in test["quarantine_control_books"]]
        source_ids = [str(source_id) for source_id in test["source_ids"]]

        missing_targets = [bookid for bookid in target_books if bookid not in q55_books]
        missing_sources = [source_id for source_id in source_ids if source_id not in q55_sources]
        if missing_targets:
            raise RuntimeError(f"{test['test_id']} missing Q55 target books: {missing_targets}")
        if missing_sources:
            raise RuntimeError(f"{test['test_id']} missing Q55 sources: {missing_sources}")

        all_books = sorted(set(target_books + control_books + quarantine_control_books), key=lambda value: int(value))
        status = (
            "READY_FOR_HUMAN_CONTRAST_NO_GLOSS"
            if all(bookid in q53_books or bookid in q50_books or bookid in q52_books or bookid in q49_items for bookid in all_books)
            else "READY_WITH_PARTIAL_CONTROL_EVIDENCE_NO_GLOSS"
        )
        prepared.append(
            {
                **test,
                "target_books": target_books,
                "control_books": control_books,
                "quarantine_control_books": quarantine_control_books,
                "source_ids": source_ids,
                "phrase_readings": phrase_readings(test, q55_books),
                "current_status": status,
                "allowed_inference": (
                    "Use this row as a falsifiable human-shadow contrast test; it may rank or demote phrase wording."
                ),
                "blocked_overreach": (
                    "No component gloss, direct source gloss, sentence translation, or canonical promotion is allowed."
                ),
                "evidence": {
                    "books": evidence_for_books(all_books, q55_books, q53_books, q50_books, q52_books, q49_items),
                    "sources": {source_id: dict(q55_sources[source_id]) for source_id in source_ids},
                    "q55_run": dict(q55),
                    "completion_audit": dict(audit),
                },
            }
        )

    priorities = [str(item["priority"]) for item in prepared]
    high_priority_test_count = priorities.count("HIGH")
    medium_priority_test_count = priorities.count("MEDIUM")
    hard_gate_test_count = priorities.count("HARD_GATE")
    target_book_count = len(sorted({bookid for item in prepared for bookid in item["target_books"]}))
    control_book_count = len(sorted({bookid for item in prepared for bookid in item["control_books"]}))
    source_link_count = sum(len(item["source_ids"]) for item in prepared)
    direct_gloss_count = 0
    canonical_promotion_allowed_count = 0
    queue_human_version = (
        "Q56 contrast queue: Q54/Q55 phrase candidates are now expressed as six falsifiable tests over target books, "
        "controls, quarantine controls, and source-register links. Passing these tests can strengthen human shadow "
        "wording, but cannot promote a canonical translation."
    )
    decision = (
        "Q56_SOURCE_LINKED_CONTRAST_QUEUE_READY_6_TESTS_NO_GLOSS"
        if len(prepared) == 6
        and high_priority_test_count == 3
        and medium_priority_test_count == 2
        and hard_gate_test_count == 1
        and target_book_count == 5
        and control_book_count >= 6
        and source_link_count >= 35
        and int(q55["direct_gloss_count"]) == 0
        and int(q55["canonical_promotion_allowed_count"]) == 0
        and int(audit["promoted_gloss_count"]) == 0
        and direct_gloss_count == 0
        and canonical_promotion_allowed_count == 0
        else "Q56_SOURCE_LINKED_CONTRAST_QUEUE_REQUIRES_REVIEW"
    )
    payload = {
        "question": "How can Q55 source-linked phrase readings be tested without turning them into invented prose?",
        "answer": "Represent each reading as a contrast test with explicit controls, acceptance signals, and falsifiers.",
        "queue_human_version": queue_human_version,
        "blocked_use": "No queued test grants component meaning or canonical sentence translation.",
        "next_action": "Execute T01/T02/T03 first because they test the strongest Book2, 67->2, and Book35 backbone.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q56_source_linked_contrast_queue_v1_runs (
                created_at, decision, q55_run_id, q53_run_id, q50_run_id,
                q52_run_id, q49_run_id, completion_audit_run_id,
                contrast_test_count, high_priority_test_count,
                medium_priority_test_count, hard_gate_test_count,
                target_book_count, control_book_count, source_link_count,
                direct_gloss_count, canonical_promotion_allowed_count,
                queue_human_version, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                int(q55["run_id"]),
                int(q53["run_id"]),
                int(q50["run_id"]),
                int(q52["run_id"]),
                q49_run_id,
                int(audit["run_id"]),
                len(prepared),
                high_priority_test_count,
                medium_priority_test_count,
                hard_gate_test_count,
                target_book_count,
                control_book_count,
                source_link_count,
                direct_gloss_count,
                canonical_promotion_allowed_count,
                queue_human_version,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q56_source_linked_contrast_queue_v1_tests (
                run_id, test_id, test_family, priority, target_books_json,
                control_books_json, quarantine_control_books_json, source_ids_json,
                phrase_readings_json, contrast_question, acceptance_signal,
                falsification_signal, current_status, allowed_inference,
                blocked_overreach, next_action, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    str(item["test_id"]),
                    str(item["test_family"]),
                    str(item["priority"]),
                    j(item["target_books"]),
                    j(item["control_books"]),
                    j(item["quarantine_control_books"]),
                    j(item["source_ids"]),
                    j(item["phrase_readings"]),
                    str(item["contrast_question"]),
                    str(item["acceptance_signal"]),
                    str(item["falsification_signal"]),
                    str(item["current_status"]),
                    str(item["allowed_inference"]),
                    str(item["blocked_overreach"]),
                    str(item["next_action"]),
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
                "contrast_test_count": len(prepared),
                "high_priority_test_count": high_priority_test_count,
                "medium_priority_test_count": medium_priority_test_count,
                "hard_gate_test_count": hard_gate_test_count,
                "target_book_count": target_book_count,
                "control_book_count": control_book_count,
                "source_link_count": source_link_count,
                "direct_gloss_count": direct_gloss_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
            }
        )
    )


if __name__ == "__main__":
    main()
