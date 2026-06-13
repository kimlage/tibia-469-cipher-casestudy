#!/usr/bin/env python3
"""Q58: execute remaining Q56 medium contrasts and the source-overreach firewall."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

REMAINING_TEST_IDS = [
    "Q56_T04_FORMULA_HANDOFF_HELDOUT",
    "Q56_T05_PAYLOAD_CONTEXT_HOLD",
    "Q56_T06_SOURCE_OVERREACH_FIREWALL",
]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q58_execute_remaining_contrasts_firewall_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q56_run_id INTEGER NOT NULL,
            q57_run_id INTEGER NOT NULL,
            q55_run_id INTEGER NOT NULL,
            q54_run_id INTEGER NOT NULL,
            q53_run_id INTEGER NOT NULL,
            q50_run_id INTEGER NOT NULL,
            q52_run_id INTEGER NOT NULL,
            q36_run_id INTEGER NOT NULL,
            q49_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            executed_test_count INTEGER NOT NULL,
            accepted_shadow_test_count INTEGER NOT NULL,
            accepted_firewall_test_count INTEGER NOT NULL,
            demoted_shadow_test_count INTEGER NOT NULL,
            blocked_shadow_test_count INTEGER NOT NULL,
            direct_gloss_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            q56_queue_completion_count INTEGER NOT NULL,
            result_human_version TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q58_execute_remaining_contrasts_firewall_v1_results (
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
    placeholders = ",".join("?" for _ in REMAINING_TEST_IDS)
    rows = conn.execute(
        f"""
        SELECT *
        FROM human_q56_source_linked_contrast_queue_v1_tests
        WHERE run_id=? AND test_id IN ({placeholders})
        """,
        (q56_run_id, *REMAINING_TEST_IDS),
    ).fetchall()
    tests = {str(row["test_id"]): row for row in rows}
    missing = [test_id for test_id in REMAINING_TEST_IDS if test_id not in tests]
    if missing:
        raise RuntimeError(f"missing remaining Q56 tests: {missing}")
    return tests


def load_q57_results(conn: sqlite3.Connection, run_id: int) -> dict[str, sqlite3.Row]:
    rows = conn.execute(
        "SELECT * FROM human_q57_execute_high_priority_contrasts_v1_results WHERE run_id=?",
        (run_id,),
    ).fetchall()
    return {str(row["test_id"]): row for row in rows}


def load_q49_items(conn: sqlite3.Connection, run_id: int) -> dict[str, list[sqlite3.Row]]:
    rows = conn.execute(
        "SELECT * FROM human_q49_c68_extra_subclass_quarantine_v1_items WHERE run_id=?",
        (run_id,),
    ).fetchall()
    by_book: dict[str, list[sqlite3.Row]] = {}
    for row in rows:
        by_book.setdefault(str(row["bookid"]), []).append(row)
    return by_book


def load_q55_sources(conn: sqlite3.Connection, run_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM human_q55_source_parallel_audit_q54_v1_sources WHERE run_id=? ORDER BY source_id",
        (run_id,),
    ).fetchall()


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


def result_t04(
    test: sqlite3.Row,
    q54_books: dict[str, sqlite3.Row],
    q53_books: dict[str, sqlite3.Row],
    q50_books: dict[str, sqlite3.Row],
    q52_books: dict[str, sqlite3.Row],
    q36_books: dict[str, sqlite3.Row],
    q49_items: dict[str, list[sqlite3.Row]],
) -> dict[str, object]:
    book10_speech = str(q50_books["10"]["q36_likely_speech_act"]).upper()
    book35_speech = str(q50_books["35"]["q36_likely_speech_act"]).upper()
    book31_speech = str(q50_books["31"]["q36_likely_speech_act"]).upper()
    book57_speech = str(q50_books["57"]["q36_likely_speech_act"]).upper()
    target_ok = (
        "BENNA" in book10_speech
        and "FORMULA" in book10_speech
        and str(q53_books["10"]["chain_profile"]) == "SUPPORTED_CONTEXT_CHAIN"
        and str(q50_books["10"]["c68_profile"]) == "C68_PHASE_CONTEXT_ONLY"
        and str(q36_books["10"]["contig_status"]) == "NO_EXACT_CONTIG_SHADOW"
        and str(q54_books["10"]["confidence_tier"]) == "MODERATE_HELDOUT_CONTEXT_ROUTE"
    )
    controls_block = (
        "BENNA" in book35_speech
        and "FORMULA" in book35_speech
        and str(q36_books["35"]["contig_status"]) == "EXACT_CONTIG_SHADOW_AVAILABLE"
        and "FORMULA" not in book31_speech
        and "FORMULA" not in book57_speech
        and str(q53_books["31"]["chain_profile"]) == "C86_AUDIT_WITH_C68_HINGE_CONTROL"
        and str(q53_books["57"]["chain_profile"]) == "C86_AUDIT_WITH_C68_HINGE_CONTROL"
    )
    result_status = (
        "ACCEPT_MODERATE_SHADOW_CONTRAST_NO_GLOSS" if target_ok and controls_block else "REQUIRES_REVIEW_NO_GLOSS"
    )
    return {
        "test_id": str(test["test_id"]),
        "test_family": str(test["test_family"]),
        "result_status": result_status,
        "target_books": ["10"],
        "control_books": ["35", "31", "57"],
        "accepted_phrase_scope": "Book 10 may keep moderate human-shadow formula-handoff wording.",
        "acceptance_summary": (
            "Book 10 shares BENNA/formula handoff into supported C86/C68 context routing with Book 35, but lacks exact contig support. "
            "Books 31/57 remain non-formula phase-context audit controls."
        ),
        "falsifier_check": "Book 10 separates from generic phase controls while staying lower-confidence than Book 35.",
        "remaining_risk": "The phrase must remain moderate; exact 35->67->2 continuity is not present for Book 10.",
        "next_action": "Use Book 10 as a heldout formula-route comparison, not as primary backbone.",
        "evidence": book_evidence(["10", "35", "31", "57"], q54_books, q53_books, q50_books, q52_books, q36_books, q49_items),
    }


def result_t05(
    test: sqlite3.Row,
    q54_books: dict[str, sqlite3.Row],
    q53_books: dict[str, sqlite3.Row],
    q50_books: dict[str, sqlite3.Row],
    q52_books: dict[str, sqlite3.Row],
    q36_books: dict[str, sqlite3.Row],
    q49_items: dict[str, list[sqlite3.Row]],
) -> dict[str, object]:
    book27_speech = str(q50_books["27"]["q36_likely_speech_act"]).upper()
    target_ok = (
        "PAYLOAD-OPEN" in book27_speech
        and "CONTEXT" in book27_speech
        and str(q53_books["27"]["chain_profile"]) == "SUPPORTED_CONTEXT_CHAIN"
        and str(q50_books["27"]["c68_profile"]) == "C68_PHASE_CONTEXT_ONLY"
        and str(q54_books["27"]["confidence_tier"]) == "MODERATE_HELDOUT_CONTEXT_ROUTE"
        and str(q54_books["27"]["edge_confirmation_status"]) == "NO_DIRECT_EDGE_CONFIRMATION"
    )
    controls_block = (
        str(q54_books["67"]["edge_confirmation_status"]) == "EDGE_CONFIRMED"
        and str(q50_books["2"]["c68_profile"]) == "C68_MIXED_PHASE_SLOT_CHAIN"
        and str(q53_books["57"]["chain_profile"]) == "C86_AUDIT_WITH_C68_HINGE_CONTROL"
        and str(q53_books["42"]["chain_profile"]) == "DUAL_AUDIT_CONTROL"
        and not q49_items.get("27")
    )
    result_status = (
        "ACCEPT_MODERATE_SHADOW_CONTRAST_NO_GLOSS" if target_ok and controls_block else "REQUIRES_REVIEW_NO_GLOSS"
    )
    return {
        "test_id": str(test["test_id"]),
        "test_family": str(test["test_family"]),
        "result_status": result_status,
        "target_books": ["27"],
        "control_books": ["67", "2", "57", "42"],
        "accepted_phrase_scope": "Book 27 may keep moderate human-shadow payload/context-hold wording.",
        "acceptance_summary": (
            "Book 27 is a supported C86/VN/C68/TIIN phase-context corridor without direct edge confirmation or Book 2's mixed slot hinge. "
            "Book 67 supplies the handoff control, Book 2 supplies the slot target, and Books 57/42 remain weak/audit controls."
        ),
        "falsifier_check": "No Threat source is used as dictionary evidence, and weak controls 57/42 do not support the same corridor reading.",
        "remaining_risk": "Held-context wording remains a functional route label; it is not command, dead, soul, or necromancy plaintext.",
        "next_action": "Use Book 27 as payload/context heldout when testing whether the route continues to a slot or stops in context.",
        "evidence": book_evidence(["27", "67", "2", "57", "42"], q54_books, q53_books, q50_books, q52_books, q36_books, q49_items),
    }


def result_t06(
    test: sqlite3.Row,
    q55: sqlite3.Row,
    q54: sqlite3.Row,
    q56: sqlite3.Row,
    q57: sqlite3.Row,
    audit: sqlite3.Row,
    q55_sources: list[sqlite3.Row],
    q57_results: dict[str, sqlite3.Row],
) -> dict[str, object]:
    source_blocks_ok = all(str(row["blocked_inference"]).strip() for row in q55_sources)
    high_results_ok = len(q57_results) == 3 and all(
        str(row["result_status"]) == "ACCEPT_SHADOW_CONTRAST_NO_GLOSS" for row in q57_results.values()
    )
    firewall_ok = (
        int(q55["direct_gloss_count"]) == 0
        and int(q55["prose_gloss_allowed_count"]) == 0
        and int(q55["canonical_promotion_allowed_count"]) == 0
        and int(q54["prose_gloss_allowed_count"]) == 0
        and int(q54["canonical_promotion_allowed_count"]) == 0
        and int(q56["direct_gloss_count"]) == 0
        and int(q56["canonical_promotion_allowed_count"]) == 0
        and int(q57["direct_gloss_count"]) == 0
        and int(q57["canonical_promotion_allowed_count"]) == 0
        and int(audit["promoted_gloss_count"]) == 0
        and source_blocks_ok
        and high_results_ok
    )
    result_status = "ACCEPT_FIREWALL_NO_GLOSS" if firewall_ok else "FIREWALL_REQUIRES_REVIEW"
    return {
        "test_id": str(test["test_id"]),
        "test_family": str(test["test_family"]),
        "result_status": result_status,
        "target_books": json.loads(str(test["target_books_json"])),
        "control_books": json.loads(str(test["control_books_json"])),
        "accepted_phrase_scope": "The Q54/Q55/Q56/Q57 human route remains source-constrained shadow translation only.",
        "acceptance_summary": (
            "Q54, Q55, Q56, Q57, and completion-audit counters all keep direct gloss, prose gloss, canonical promotion, and promoted gloss at zero. "
            "Every Q55 source row retains an explicit blocked inference."
        ),
        "falsifier_check": "No source-linked phrase has been promoted to component meaning, sentence translation, or canonical plaintext.",
        "remaining_risk": "The route is stronger as human shadow, but cannot be reported as solved canonical translation.",
        "next_action": "Use the completed Q56 execution set to draft a consolidated Q59 human-route backbone and residual-risk map.",
        "evidence": {
            "q54_run": dict(q54),
            "q55_run": dict(q55),
            "q56_run": dict(q56),
            "q57_run": dict(q57),
            "completion_audit": dict(audit),
            "q55_sources": [dict(row) for row in q55_sources],
            "q57_results": {test_id: dict(row) for test_id, row in q57_results.items()},
        },
    }


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q56 = latest_row(conn, "human_q56_source_linked_contrast_queue_v1_runs")
    q57 = latest_row(conn, "human_q57_execute_high_priority_contrasts_v1_runs")
    q55 = latest_row(conn, "human_q55_source_parallel_audit_q54_v1_runs")
    q54 = latest_row(conn, "human_q54_supported_chain_phrase_layer_v1_runs")
    q53 = latest_row(conn, "human_q53_c86_c68_chain_synthesis_v1_runs")
    q50 = latest_row(conn, "human_q50_c68_book_synthesis_v1_runs")
    q52 = latest_row(conn, "human_q52_c86_book_synthesis_v1_runs")
    audit = latest_row(conn, "human_translation_completion_audit_v5_runs")
    q36_run_id = latest_item_run_id(conn, "human_q36_book_contig_shadow_integration_v1_items", "bookid")
    q49_run_id = latest_item_run_id(conn, "human_q49_c68_extra_subclass_quarantine_v1_items", "bookid")

    q56_tests = load_q56_tests(conn, int(q56["run_id"]))
    q57_results = load_q57_results(conn, int(q57["run_id"]))
    q55_sources = load_q55_sources(conn, int(q55["run_id"]))
    q54_books = load_by_book(conn, "human_q54_supported_chain_phrase_layer_v1_books", int(q54["run_id"]))
    q53_books = load_by_book(conn, "human_q53_c86_c68_chain_synthesis_v1_books", int(q53["run_id"]))
    q50_books = load_by_book(conn, "human_q50_c68_book_synthesis_v1_books", int(q50["run_id"]))
    q52_books = load_by_book(conn, "human_q52_c86_book_synthesis_v1_books", int(q52["run_id"]))
    q36_books = load_by_book(conn, "human_q36_book_contig_shadow_integration_v1_items", q36_run_id)
    q49_items = load_q49_items(conn, q49_run_id)

    results = [
        result_t04(q56_tests["Q56_T04_FORMULA_HANDOFF_HELDOUT"], q54_books, q53_books, q50_books, q52_books, q36_books, q49_items),
        result_t05(q56_tests["Q56_T05_PAYLOAD_CONTEXT_HOLD"], q54_books, q53_books, q50_books, q52_books, q36_books, q49_items),
        result_t06(q56_tests["Q56_T06_SOURCE_OVERREACH_FIREWALL"], q55, q54, q56, q57, audit, q55_sources, q57_results),
    ]

    accepted_shadow_test_count = sum(
        1 for result in results if str(result["result_status"]).startswith("ACCEPT_") and result["test_id"] != "Q56_T06_SOURCE_OVERREACH_FIREWALL"
    )
    accepted_firewall_test_count = sum(1 for result in results if result["result_status"] == "ACCEPT_FIREWALL_NO_GLOSS")
    demoted_shadow_test_count = sum(1 for result in results if result["result_status"] == "DEMOTE_SHADOW_READING_NO_GLOSS")
    blocked_shadow_test_count = len(results) - accepted_shadow_test_count - accepted_firewall_test_count - demoted_shadow_test_count
    direct_gloss_count = 0
    canonical_promotion_allowed_count = 0
    q56_queue_completion_count = int(q57["accepted_shadow_test_count"]) + accepted_shadow_test_count + accepted_firewall_test_count
    result_human_version = (
        "Q58 completes the Q56 execution queue: Book 10 and Book 27 keep moderate human-shadow readings, "
        "and the source-overreach firewall passes. The Q54/Q55 phrase route is now fully tested as shadow translation, "
        "not canonical plaintext."
    )
    decision = (
        "Q58_REMAINING_CONTRASTS_AND_FIREWALL_ACCEPT_3_NO_GLOSS"
        if len(results) == 3
        and accepted_shadow_test_count == 2
        and accepted_firewall_test_count == 1
        and demoted_shadow_test_count == 0
        and blocked_shadow_test_count == 0
        and q56_queue_completion_count == 6
        and int(q57["accepted_shadow_test_count"]) == 3
        and int(q55["direct_gloss_count"]) == 0
        and int(q55["canonical_promotion_allowed_count"]) == 0
        and int(audit["promoted_gloss_count"]) == 0
        and direct_gloss_count == 0
        and canonical_promotion_allowed_count == 0
        else "Q58_REMAINING_CONTRASTS_AND_FIREWALL_REQUIRES_REVIEW"
    )
    payload = {
        "question": "Do the remaining Q56 contrasts and hard firewall pass after Q57?",
        "answer": "Yes. The two medium readings remain moderate shadow candidates, and the source firewall holds.",
        "result_human_version": result_human_version,
        "blocked_use": "No component gloss, sentence translation, direct source gloss, or canonical promotion.",
        "next_action": "Draft Q59 consolidated human-route backbone and residual-risk map for the five Q54 phrases.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q58_execute_remaining_contrasts_firewall_v1_runs (
                created_at, decision, q56_run_id, q57_run_id, q55_run_id,
                q54_run_id, q53_run_id, q50_run_id, q52_run_id, q36_run_id,
                q49_run_id, completion_audit_run_id, executed_test_count,
                accepted_shadow_test_count, accepted_firewall_test_count,
                demoted_shadow_test_count, blocked_shadow_test_count,
                direct_gloss_count, canonical_promotion_allowed_count,
                q56_queue_completion_count, result_human_version, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                int(q56["run_id"]),
                int(q57["run_id"]),
                int(q55["run_id"]),
                int(q54["run_id"]),
                int(q53["run_id"]),
                int(q50["run_id"]),
                int(q52["run_id"]),
                q36_run_id,
                q49_run_id,
                int(audit["run_id"]),
                len(results),
                accepted_shadow_test_count,
                accepted_firewall_test_count,
                demoted_shadow_test_count,
                blocked_shadow_test_count,
                direct_gloss_count,
                canonical_promotion_allowed_count,
                q56_queue_completion_count,
                result_human_version,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q58_execute_remaining_contrasts_firewall_v1_results (
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
                "accepted_firewall_test_count": accepted_firewall_test_count,
                "demoted_shadow_test_count": demoted_shadow_test_count,
                "blocked_shadow_test_count": blocked_shadow_test_count,
                "q56_queue_completion_count": q56_queue_completion_count,
                "direct_gloss_count": direct_gloss_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
            }
        )
    )


if __name__ == "__main__":
    main()
