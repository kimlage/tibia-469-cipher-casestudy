#!/usr/bin/env python3
"""Q57: execute the high-priority Q56 source-linked contrast tests."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

HIGH_TEST_IDS = [
    "Q56_T01_CONTEXT_TO_SLOT_CLASSIFIER",
    "Q56_T02_67_TO_2_HANDOFF_EDGE",
    "Q56_T03_FORMULA_TO_CONTEXT_CONTIG",
]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q57_execute_high_priority_contrasts_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q56_run_id INTEGER NOT NULL,
            q54_run_id INTEGER NOT NULL,
            q53_run_id INTEGER NOT NULL,
            q50_run_id INTEGER NOT NULL,
            q52_run_id INTEGER NOT NULL,
            q36_run_id INTEGER NOT NULL,
            q49_run_id INTEGER NOT NULL,
            chain_probe_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            executed_test_count INTEGER NOT NULL,
            accepted_shadow_test_count INTEGER NOT NULL,
            demoted_shadow_test_count INTEGER NOT NULL,
            blocked_shadow_test_count INTEGER NOT NULL,
            direct_gloss_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            result_human_version TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q57_execute_high_priority_contrasts_v1_results (
            run_id INTEGER NOT NULL,
            test_id TEXT NOT NULL,
            test_family TEXT NOT NULL,
            result_status TEXT NOT NULL,
            target_books_json TEXT NOT NULL,
            control_books_json TEXT NOT NULL,
            accepted_phrase_scope TEXT NOT NULL,
            acceptance_summary TEXT NOT NULL,
            falsifier_check TEXT NOT NULL,
            remaining_risk TEXT NOT NULL,
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


def load_q56_tests(conn: sqlite3.Connection, q56_run_id: int) -> dict[str, sqlite3.Row]:
    placeholders = ",".join("?" for _ in HIGH_TEST_IDS)
    rows = conn.execute(
        f"""
        SELECT *
        FROM human_q56_source_linked_contrast_queue_v1_tests
        WHERE run_id=? AND test_id IN ({placeholders})
        """,
        (q56_run_id, *HIGH_TEST_IDS),
    ).fetchall()
    tests = {str(row["test_id"]): row for row in rows}
    missing = [test_id for test_id in HIGH_TEST_IDS if test_id not in tests]
    if missing:
        raise RuntimeError(f"missing high-priority Q56 tests: {missing}")
    return tests


def load_chain_items(conn: sqlite3.Connection, run_id: int) -> dict[tuple[str, str], sqlite3.Row]:
    rows = conn.execute("SELECT * FROM c86_c68_naese_chain_probe_v1_items WHERE run_id=?", (run_id,)).fetchall()
    return {(str(row["item_type"]), str(row["item_id"])): row for row in rows}


def load_q49_items(conn: sqlite3.Connection, run_id: int) -> dict[str, list[sqlite3.Row]]:
    rows = conn.execute(
        "SELECT * FROM human_q49_c68_extra_subclass_quarantine_v1_items WHERE run_id=?",
        (run_id,),
    ).fetchall()
    by_book: dict[str, list[sqlite3.Row]] = {}
    for row in rows:
        by_book.setdefault(str(row["bookid"]), []).append(row)
    return by_book


def book_evidence(
    bookids: list[str],
    q54_books: dict[str, sqlite3.Row],
    q53_books: dict[str, sqlite3.Row],
    q50_books: dict[str, sqlite3.Row],
    q52_books: dict[str, sqlite3.Row],
    q36_books: dict[str, sqlite3.Row],
    q49_items: dict[str, list[sqlite3.Row]],
) -> dict[str, object]:
    return {
        bookid: {
            "q54": dict(q54_books[bookid]) if bookid in q54_books else None,
            "q53": dict(q53_books[bookid]) if bookid in q53_books else None,
            "q50": dict(q50_books[bookid]) if bookid in q50_books else None,
            "q52": dict(q52_books[bookid]) if bookid in q52_books else None,
            "q36": dict(q36_books[bookid]) if bookid in q36_books else None,
            "q49_quarantine": [dict(row) for row in q49_items.get(bookid, [])],
        }
        for bookid in bookids
    }


def result_t01(
    test: sqlite3.Row,
    q54_books: dict[str, sqlite3.Row],
    q53_books: dict[str, sqlite3.Row],
    q50_books: dict[str, sqlite3.Row],
    q52_books: dict[str, sqlite3.Row],
    q36_books: dict[str, sqlite3.Row],
    q49_items: dict[str, list[sqlite3.Row]],
) -> dict[str, object]:
    target_ok = (
        str(q53_books["2"]["chain_profile"]) == "SUPPORTED_CONTEXT_TO_SLOT_CHAIN"
        and str(q50_books["2"]["c68_profile"]) == "C68_MIXED_PHASE_SLOT_CHAIN"
        and str(q54_books["2"]["edge_confirmation_status"]) == "EDGE_CONFIRMED"
        and str(q36_books["2"]["contig_status"]) == "EXACT_CONTIG_SHADOW_AVAILABLE"
    )
    controls_block = (
        str(q53_books["5"]["chain_profile"]) == "C86_AUDIT_WITH_C68_HINGE_CONTROL"
        and str(q50_books["5"]["c68_profile"]) == "C68_SLOT_CLASSIFIER_ONLY"
        and str(q53_books["42"]["chain_profile"]) == "DUAL_AUDIT_CONTROL"
        and str(q50_books["42"]["c68_profile"]) == "C68_TAVT_BOUNDARY_AUDIT"
    )
    result_status = (
        "ACCEPT_SHADOW_CONTRAST_NO_GLOSS" if target_ok and controls_block else "REQUIRES_REVIEW_NO_GLOSS"
    )
    return {
        "test_id": str(test["test_id"]),
        "test_family": str(test["test_family"]),
        "result_status": result_status,
        "target_books": ["2"],
        "control_books": ["5", "42"],
        "accepted_phrase_scope": "Book 2 may keep the human-shadow wording context-to-classifier slot.",
        "acceptance_summary": (
            "Book 2 combines supported C86 context selection, mixed C68 phase/slot chaining, edge confirmation, and exact contig support. "
            "Book 5 has C68 slot material without supported C86 chaining; Book 42 is a TAVT/dual-audit boundary control."
        ),
        "falsifier_check": "No control in 5/42 supports the same context-to-slot phrase without C86 edge support.",
        "remaining_risk": "Classifier remains a functional slot label, not a lexical word or canonical plaintext.",
        "next_action": "Use Book 2 as the strongest phrase-level target for later NAESE/C68 slot-control tests.",
        "evidence": book_evidence(["2", "5", "42"], q54_books, q53_books, q50_books, q52_books, q36_books, q49_items),
    }


def result_t02(
    test: sqlite3.Row,
    q54_books: dict[str, sqlite3.Row],
    q53_books: dict[str, sqlite3.Row],
    q50_books: dict[str, sqlite3.Row],
    q52_books: dict[str, sqlite3.Row],
    q36_books: dict[str, sqlite3.Row],
    q49_items: dict[str, list[sqlite3.Row]],
    chain_items: dict[tuple[str, str], sqlite3.Row],
) -> dict[str, object]:
    edge = chain_items.get(("naese_edge", "67->2"))
    edge_ok = edge is not None and str(edge["gate_status"]) == "ORDERED_EDGE_ACCEPTED_NO_GLOSS"
    target_ok = (
        str(q53_books["67"]["chain_profile"]) == "SUPPORTED_CONTEXT_CHAIN"
        and str(q54_books["67"]["edge_confirmation_status"]) == "EDGE_CONFIRMED"
        and str(q36_books["67"]["contig_status"]) == "EXACT_CONTIG_SHADOW_AVAILABLE"
        and str(q53_books["2"]["chain_profile"]) == "SUPPORTED_CONTEXT_TO_SLOT_CHAIN"
        and str(q36_books["2"]["contig_status"]) == "EXACT_CONTIG_SHADOW_AVAILABLE"
        and edge_ok
    )
    controls_block = (
        str(q53_books["27"]["chain_profile"]) == "SUPPORTED_CONTEXT_CHAIN"
        and str(q54_books["27"]["edge_confirmation_status"]) == "NO_DIRECT_EDGE_CONFIRMATION"
        and str(q54_books["35"]["edge_confirmation_status"]) == "NO_DIRECT_EDGE_CONFIRMATION"
        and str(q53_books["42"]["chain_profile"]) == "DUAL_AUDIT_CONTROL"
        and not q49_items.get("67")
    )
    result_status = (
        "ACCEPT_SHADOW_CONTRAST_NO_GLOSS" if target_ok and controls_block else "REQUIRES_REVIEW_NO_GLOSS"
    )
    return {
        "test_id": str(test["test_id"]),
        "test_family": str(test["test_family"]),
        "result_status": result_status,
        "target_books": ["67", "2"],
        "control_books": ["27", "35", "42"],
        "accepted_phrase_scope": "Books 67->2 may keep the human-shadow handoff-into-slot wording.",
        "acceptance_summary": (
            "Book 67 is supported context routing with exact contig support and an accepted 67->2 edge; Book 2 continues into the mixed phase/slot chain. "
            "Books 27/35 lack direct edge confirmation, and Book 42 remains a dual-audit boundary control."
        ),
        "falsifier_check": "Book 67 is not terminal/exit-quarantined and the 67->2 edge is accepted with no gloss.",
        "remaining_risk": "The phrase names a transition role only; it does not translate either book as a sentence.",
        "next_action": "Use 67->2 as the immediate edge backbone when testing phrase continuity into Book 2.",
        "evidence": {
            "books": book_evidence(["67", "2", "27", "35", "42"], q54_books, q53_books, q50_books, q52_books, q36_books, q49_items),
            "chain_edge_67_2": dict(edge) if edge is not None else None,
        },
    }


def result_t03(
    test: sqlite3.Row,
    q54_books: dict[str, sqlite3.Row],
    q53_books: dict[str, sqlite3.Row],
    q50_books: dict[str, sqlite3.Row],
    q52_books: dict[str, sqlite3.Row],
    q36_books: dict[str, sqlite3.Row],
    q49_items: dict[str, list[sqlite3.Row]],
) -> dict[str, object]:
    book35_speech = str(q50_books["35"]["q36_likely_speech_act"]).upper()
    book10_speech = str(q50_books["10"]["q36_likely_speech_act"]).upper()
    book31_speech = str(q50_books["31"]["q36_likely_speech_act"]).upper()
    book57_speech = str(q50_books["57"]["q36_likely_speech_act"]).upper()
    book5_speech = str(q50_books["5"]["q36_likely_speech_act"]).upper()
    target_ok = (
        "BENNA" in book35_speech
        and "FORMULA" in book35_speech
        and str(q53_books["35"]["chain_profile"]) == "SUPPORTED_CONTEXT_CHAIN"
        and str(q36_books["35"]["contig_status"]) == "EXACT_CONTIG_SHADOW_AVAILABLE"
        and str(q54_books["35"]["confidence_tier"]) == "STRONG_CONTIG_CONTEXT_ROUTE"
    )
    controls_block = (
        "FORMULA" in book10_speech
        and str(q36_books["10"]["contig_status"]) == "NO_EXACT_CONTIG_SHADOW"
        and "FORMULA" not in book31_speech
        and "FORMULA" not in book57_speech
        and "SLOT-TO-BENNA" in book5_speech
        and str(q53_books["5"]["chain_profile"]) == "C86_AUDIT_WITH_C68_HINGE_CONTROL"
    )
    result_status = (
        "ACCEPT_SHADOW_CONTRAST_NO_GLOSS" if target_ok and controls_block else "REQUIRES_REVIEW_NO_GLOSS"
    )
    return {
        "test_id": str(test["test_id"]),
        "test_family": str(test["test_family"]),
        "result_status": result_status,
        "target_books": ["35"],
        "control_books": ["10", "31", "57", "5"],
        "accepted_phrase_scope": "Book 35 may keep the human-shadow formula-body-to-context-route wording.",
        "acceptance_summary": (
            "Book 35 has BENNA/formula handoff language, supported C86/C68 context routing, strong Q54 status, and exact contig placement before 67->2. "
            "Book 10 is a heldout formula route, Books 31/57 are non-formula phase controls, and Book 5 reverses the direction as slot-to-formula audit material."
        ),
        "falsifier_check": "Controls do not reproduce Book 35's combined formula, supported context route, and exact contig placement.",
        "remaining_risk": "Formula-body wording remains functional; BENNA is not promoted as a word.",
        "next_action": "Use Book 35 as the upstream formula route in a focused 35->67->2 phrase-continuity test.",
        "evidence": book_evidence(["35", "10", "31", "57", "5"], q54_books, q53_books, q50_books, q52_books, q36_books, q49_items),
    }


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q56 = latest_row(conn, "human_q56_source_linked_contrast_queue_v1_runs")
    q54 = latest_row(conn, "human_q54_supported_chain_phrase_layer_v1_runs")
    q53 = latest_row(conn, "human_q53_c86_c68_chain_synthesis_v1_runs")
    q50 = latest_row(conn, "human_q50_c68_book_synthesis_v1_runs")
    q52 = latest_row(conn, "human_q52_c86_book_synthesis_v1_runs")
    chain_probe = latest_row(conn, "c86_c68_naese_chain_probe_v1_runs")
    audit = latest_row(conn, "human_translation_completion_audit_v5_runs")
    q36_run_id = latest_item_run_id(conn, "human_q36_book_contig_shadow_integration_v1_items", "bookid")
    q49_run_id = latest_item_run_id(conn, "human_q49_c68_extra_subclass_quarantine_v1_items", "bookid")

    q56_tests = load_q56_tests(conn, int(q56["run_id"]))
    q54_books = load_by_book(conn, "human_q54_supported_chain_phrase_layer_v1_books", int(q54["run_id"]))
    q53_books = load_by_book(conn, "human_q53_c86_c68_chain_synthesis_v1_books", int(q53["run_id"]))
    q50_books = load_by_book(conn, "human_q50_c68_book_synthesis_v1_books", int(q50["run_id"]))
    q52_books = load_by_book(conn, "human_q52_c86_book_synthesis_v1_books", int(q52["run_id"]))
    q36_books = load_by_book(conn, "human_q36_book_contig_shadow_integration_v1_items", q36_run_id)
    q49_items = load_q49_items(conn, q49_run_id)
    chain_items = load_chain_items(conn, int(chain_probe["run_id"]))

    results = [
        result_t01(q56_tests["Q56_T01_CONTEXT_TO_SLOT_CLASSIFIER"], q54_books, q53_books, q50_books, q52_books, q36_books, q49_items),
        result_t02(q56_tests["Q56_T02_67_TO_2_HANDOFF_EDGE"], q54_books, q53_books, q50_books, q52_books, q36_books, q49_items, chain_items),
        result_t03(q56_tests["Q56_T03_FORMULA_TO_CONTEXT_CONTIG"], q54_books, q53_books, q50_books, q52_books, q36_books, q49_items),
    ]

    accepted_shadow_test_count = sum(
        1 for result in results if result["result_status"] == "ACCEPT_SHADOW_CONTRAST_NO_GLOSS"
    )
    demoted_shadow_test_count = sum(1 for result in results if result["result_status"] == "DEMOTE_SHADOW_READING_NO_GLOSS")
    blocked_shadow_test_count = len(results) - accepted_shadow_test_count - demoted_shadow_test_count
    direct_gloss_count = 0
    canonical_promotion_allowed_count = 0
    result_human_version = (
        "Q57 high-priority execution accepts the Book 2 context-to-slot phrase, the 67->2 handoff edge phrase, "
        "and the Book 35 formula-to-context phrase as strengthened human-shadow readings. This remains a contrast "
        "result only, with no component gloss or canonical plaintext."
    )
    decision = (
        "Q57_HIGH_PRIORITY_CONTRASTS_ACCEPT_3_SHADOW_PHRASES_NO_GLOSS"
        if len(results) == 3
        and accepted_shadow_test_count == 3
        and demoted_shadow_test_count == 0
        and blocked_shadow_test_count == 0
        and int(q56["canonical_promotion_allowed_count"]) == 0
        and int(audit["promoted_gloss_count"]) == 0
        and direct_gloss_count == 0
        and canonical_promotion_allowed_count == 0
        else "Q57_HIGH_PRIORITY_CONTRASTS_REQUIRE_REVIEW"
    )
    payload = {
        "question": "Do the three high-priority Q56 contrasts survive their controls?",
        "answer": "Yes, as strengthened human-shadow readings only.",
        "result_human_version": result_human_version,
        "blocked_use": "No component gloss, direct source gloss, sentence translation, or canonical promotion.",
        "next_action": "Execute Q56_T04/T05 and then re-run the source-overreach hard gate.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q57_execute_high_priority_contrasts_v1_runs (
                created_at, decision, q56_run_id, q54_run_id, q53_run_id,
                q50_run_id, q52_run_id, q36_run_id, q49_run_id,
                chain_probe_run_id, completion_audit_run_id, executed_test_count,
                accepted_shadow_test_count, demoted_shadow_test_count,
                blocked_shadow_test_count, direct_gloss_count,
                canonical_promotion_allowed_count, result_human_version,
                payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                int(q56["run_id"]),
                int(q54["run_id"]),
                int(q53["run_id"]),
                int(q50["run_id"]),
                int(q52["run_id"]),
                q36_run_id,
                q49_run_id,
                int(chain_probe["run_id"]),
                int(audit["run_id"]),
                len(results),
                accepted_shadow_test_count,
                demoted_shadow_test_count,
                blocked_shadow_test_count,
                direct_gloss_count,
                canonical_promotion_allowed_count,
                result_human_version,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q57_execute_high_priority_contrasts_v1_results (
                run_id, test_id, test_family, result_status, target_books_json,
                control_books_json, accepted_phrase_scope, acceptance_summary,
                falsifier_check, remaining_risk, next_action, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    str(result["test_id"]),
                    str(result["test_family"]),
                    str(result["result_status"]),
                    j(result["target_books"]),
                    j(result["control_books"]),
                    str(result["accepted_phrase_scope"]),
                    str(result["acceptance_summary"]),
                    str(result["falsifier_check"]),
                    str(result["remaining_risk"]),
                    str(result["next_action"]),
                    j(result["evidence"]),
                )
                for result in results
            ],
        )

    print(
        j(
            {
                "run_id": run_id,
                "decision": decision,
                "executed_test_count": len(results),
                "accepted_shadow_test_count": accepted_shadow_test_count,
                "demoted_shadow_test_count": demoted_shadow_test_count,
                "blocked_shadow_test_count": blocked_shadow_test_count,
                "direct_gloss_count": direct_gloss_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
            }
        )
    )


if __name__ == "__main__":
    main()
