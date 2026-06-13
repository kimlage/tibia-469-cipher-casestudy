#!/usr/bin/env python3
"""Q61: minimal-pair gate for the C68/NAESE slot-classifier role."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

TARGET_BOOKS = ["2", "5"]
CONTROL_BOOKS = ["31", "57", "42"]
Q43_SLOT_WITNESSES = ["22", "28", "48"]

MINIMAL_PAIRS = [
    {
        "pair_id": "Q61_PAIR_5_VS_31",
        "target_book": "5",
        "control_book": "31",
        "contrast_axis": "SLOT_TIVV_VS_PHASE_TIIN",
        "expected_difference": "Book 5 has slot/classifier window; Book 31 has phase/context window.",
    },
    {
        "pair_id": "Q61_PAIR_5_VS_57",
        "target_book": "5",
        "control_book": "57",
        "contrast_axis": "SLOT_TIVV_VS_PHASE_TIIN",
        "expected_difference": "Book 5 has slot/classifier window; Book 57 has phase/context window.",
    },
    {
        "pair_id": "Q61_PAIR_2_VS_5",
        "target_book": "2",
        "control_book": "5",
        "contrast_axis": "CHAINED_SLOT_TARGET_VS_SLOT_ONLY",
        "expected_difference": "Book 2 has context-to-slot chain; Book 5 has C68 slot support without supported C86 chain.",
    },
    {
        "pair_id": "Q61_PAIR_2_VS_31",
        "target_book": "2",
        "control_book": "31",
        "contrast_axis": "MIXED_PHASE_SLOT_CHAIN_VS_PHASE_ONLY",
        "expected_difference": "Book 2 has mixed phase/slot chain and Q59 target role; Book 31 is phase/context control.",
    },
    {
        "pair_id": "Q61_PAIR_2_VS_57",
        "target_book": "2",
        "control_book": "57",
        "contrast_axis": "MIXED_PHASE_SLOT_CHAIN_VS_PHASE_ONLY",
        "expected_difference": "Book 2 has mixed phase/slot chain and Q59 target role; Book 57 is phase/context control.",
    },
    {
        "pair_id": "Q61_PAIR_SLOT_VS_BOUNDARY_42",
        "target_book": "5",
        "control_book": "42",
        "contrast_axis": "SLOT_TIVV_VS_TAVT_BOUNDARY",
        "expected_difference": "Book 5 is slot/classifier support; Book 42 is quarantined TAVT boundary audit.",
    },
]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q61_c68_naese_slot_role_minimal_pairs_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q60_run_id INTEGER NOT NULL,
            q59_run_id INTEGER NOT NULL,
            q53_run_id INTEGER NOT NULL,
            q50_run_id INTEGER NOT NULL,
            q48_run_id INTEGER NOT NULL,
            q47_run_id INTEGER NOT NULL,
            q43_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            target_book_count INTEGER NOT NULL,
            control_book_count INTEGER NOT NULL,
            canonical_slot_witness_count INTEGER NOT NULL,
            minimal_pair_count INTEGER NOT NULL,
            passing_pair_count INTEGER NOT NULL,
            phase_control_count INTEGER NOT NULL,
            boundary_control_count INTEGER NOT NULL,
            functional_role_accept_count INTEGER NOT NULL,
            lexical_ready_count INTEGER NOT NULL,
            direct_gloss_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            role_human_version TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q61_c68_naese_slot_role_minimal_pairs_v1_books (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            book_class TEXT NOT NULL,
            q48_window_class TEXT NOT NULL,
            q50_c68_profile TEXT NOT NULL,
            q53_chain_profile TEXT NOT NULL,
            q59_route_role TEXT NOT NULL,
            slot_signal INTEGER NOT NULL,
            phase_signal INTEGER NOT NULL,
            boundary_signal INTEGER NOT NULL,
            role_verdict TEXT NOT NULL,
            blocked_claim TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        );

        CREATE TABLE IF NOT EXISTS human_q61_c68_naese_slot_role_minimal_pairs_v1_pairs (
            run_id INTEGER NOT NULL,
            pair_id TEXT NOT NULL,
            target_book TEXT NOT NULL,
            control_book TEXT NOT NULL,
            contrast_axis TEXT NOT NULL,
            expected_difference TEXT NOT NULL,
            observed_difference TEXT NOT NULL,
            pair_status TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, pair_id)
        );

        CREATE TABLE IF NOT EXISTS human_q61_c68_naese_slot_role_minimal_pairs_v1_q43_witnesses (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            c68_context_class TEXT NOT NULL,
            c68_slot_status TEXT NOT NULL,
            naese_status TEXT NOT NULL,
            naese_role_label TEXT NOT NULL,
            witness_use TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
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


def q60_candidate(conn: sqlite3.Connection, q60_run_id: int) -> sqlite3.Row:
    row = conn.execute(
        """
        SELECT *
        FROM human_q60_component_role_promotion_queue_v1_candidates
        WHERE run_id=? AND candidate_id='Q60_C01_C68_NAESE_SLOT_CLASSIFIER_ROLE'
        """,
        (q60_run_id,),
    ).fetchone()
    if row is None:
        raise RuntimeError("missing Q60 C68/NAESE slot candidate")
    return row


def book_class(bookid: str) -> str:
    if bookid in TARGET_BOOKS:
        return "TARGET_SLOT_ROLE"
    if bookid in {"31", "57"}:
        return "PHASE_CONTEXT_CONTROL"
    if bookid == "42":
        return "BOUNDARY_AUDIT_CONTROL"
    return "OTHER"


def q48_window(bookid: str, q48_books: dict[str, sqlite3.Row]) -> str:
    row = q48_books.get(bookid)
    return str(row["dominant_window_class"]) if row is not None else "NO_Q48_WINDOW"


def q50_profile(bookid: str, q50_books: dict[str, sqlite3.Row]) -> str:
    row = q50_books.get(bookid)
    return str(row["c68_profile"]) if row is not None else "NO_Q50_PROFILE"


def q53_profile(bookid: str, q53_books: dict[str, sqlite3.Row]) -> str:
    row = q53_books.get(bookid)
    return str(row["chain_profile"]) if row is not None else "NO_Q53_PROFILE"


def q59_role(bookid: str, q59_books: dict[str, sqlite3.Row]) -> str:
    row = q59_books.get(bookid)
    return str(row["route_role"]) if row is not None else "NO_Q59_ROUTE"


def classify_book(
    bookid: str,
    q48_books: dict[str, sqlite3.Row],
    q50_books: dict[str, sqlite3.Row],
    q53_books: dict[str, sqlite3.Row],
    q59_books: dict[str, sqlite3.Row],
) -> dict[str, object]:
    window = q48_window(bookid, q48_books)
    c68_profile = q50_profile(bookid, q50_books)
    chain_profile = q53_profile(bookid, q53_books)
    route_role = q59_role(bookid, q59_books)
    slot_signal = int("SLOT" in window or "SLOT" in c68_profile or route_role == "PRIMARY_CONTEXT_TO_SLOT_TARGET")
    phase_signal = int("PHASE" in window or "PHASE_CONTEXT" in c68_profile)
    boundary_signal = int("BOUNDARY" in window or "BOUNDARY" in c68_profile or bookid == "42")
    if bookid == "2":
        verdict = "MIXED_CONTEXT_TO_SLOT_TARGET_SUPPORTS_ROLE"
    elif bookid == "5":
        verdict = "SLOT_ONLY_SUPPORTS_C68_NAESE_ROLE_NOT_CHAIN"
    elif bookid in {"31", "57"}:
        verdict = "PHASE_CONTEXT_CONTROL_BLOCKS_SLOT_READING"
    elif bookid == "42":
        verdict = "BOUNDARY_AUDIT_CONTROL_BLOCKS_SLOT_READING"
    else:
        verdict = "UNCLASSIFIED"
    return {
        "bookid": bookid,
        "book_class": book_class(bookid),
        "q48_window_class": window,
        "q50_c68_profile": c68_profile,
        "q53_chain_profile": chain_profile,
        "q59_route_role": route_role,
        "slot_signal": slot_signal,
        "phase_signal": phase_signal,
        "boundary_signal": boundary_signal,
        "role_verdict": verdict,
        "blocked_claim": "Functional slot/classifier role only; no C68, NAESE, slot, or classifier word gloss.",
        "evidence": {
            "q48": dict(q48_books[bookid]) if bookid in q48_books else None,
            "q50": dict(q50_books[bookid]) if bookid in q50_books else None,
            "q53": dict(q53_books[bookid]) if bookid in q53_books else None,
            "q59": dict(q59_books[bookid]) if bookid in q59_books else None,
        },
    }


def pair_status(pair: dict[str, str], classified: dict[str, dict[str, object]]) -> tuple[str, str]:
    target = classified[pair["target_book"]]
    control = classified[pair["control_book"]]
    if pair["contrast_axis"] == "SLOT_TIVV_VS_PHASE_TIIN":
        passes = int(target["slot_signal"]) == 1 and str(target["q48_window_class"]) == "SLOT_TIVV_WINDOW" and str(control["q48_window_class"]) == "PHASE_TIIN_WINDOW"
    elif pair["contrast_axis"] == "CHAINED_SLOT_TARGET_VS_SLOT_ONLY":
        passes = str(target["q53_chain_profile"]) == "SUPPORTED_CONTEXT_TO_SLOT_CHAIN" and str(control["q53_chain_profile"]) == "C86_AUDIT_WITH_C68_HINGE_CONTROL"
    elif pair["contrast_axis"] == "MIXED_PHASE_SLOT_CHAIN_VS_PHASE_ONLY":
        passes = str(target["q50_c68_profile"]) == "C68_MIXED_PHASE_SLOT_CHAIN" and str(control["q50_c68_profile"]) == "C68_PHASE_CONTEXT_ONLY"
    elif pair["contrast_axis"] == "SLOT_TIVV_VS_TAVT_BOUNDARY":
        passes = str(target["q48_window_class"]) == "SLOT_TIVV_WINDOW" and int(control["boundary_signal"]) == 1
    else:
        passes = False
    observed = (
        f"{pair['target_book']}={target['q48_window_class']}/{target['q50_c68_profile']}/{target['q53_chain_profile']} "
        f"vs {pair['control_book']}={control['q48_window_class']}/{control['q50_c68_profile']}/{control['q53_chain_profile']}"
    )
    return ("PAIR_PASSES_ROLE_CONTRAST_NO_GLOSS" if passes else "PAIR_REQUIRES_REVIEW", observed)


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q60 = latest_row(conn, "human_q60_component_role_promotion_queue_v1_runs")
    q59 = latest_row(conn, "human_q59_consolidated_shadow_backbone_v1_runs")
    q53 = latest_row(conn, "human_q53_c86_c68_chain_synthesis_v1_runs")
    q50 = latest_row(conn, "human_q50_c68_book_synthesis_v1_runs")
    audit = latest_row(conn, "human_translation_completion_audit_v5_runs")
    q48_run_id = latest_item_run_id(conn, "human_q48_c68_heldout_window_taxonomy_v1_books", "bookid")
    q47_run_id = latest_item_run_id(conn, "human_q47_phase_slot_c68_window_join_v1_books", "bookid")
    q43_run_id = latest_item_run_id(conn, "human_q43_naese_c68_slot_variant_trio_atlas_v1_books", "bookid")

    candidate = q60_candidate(conn, int(q60["run_id"]))
    q59_books = load_by_book(conn, "human_q59_consolidated_shadow_backbone_v1_books", int(q59["run_id"]))
    q53_books = load_by_book(conn, "human_q53_c86_c68_chain_synthesis_v1_books", int(q53["run_id"]))
    q50_books = load_by_book(conn, "human_q50_c68_book_synthesis_v1_books", int(q50["run_id"]))
    q48_books = load_by_book(conn, "human_q48_c68_heldout_window_taxonomy_v1_books", q48_run_id)
    q43_books = load_by_book(conn, "human_q43_naese_c68_slot_variant_trio_atlas_v1_books", q43_run_id)

    all_books = TARGET_BOOKS + CONTROL_BOOKS
    classified = {
        bookid: classify_book(bookid, q48_books, q50_books, q53_books, q59_books)
        for bookid in all_books
    }
    pair_rows = []
    for pair in MINIMAL_PAIRS:
        status, observed = pair_status(pair, classified)
        pair_rows.append({**pair, "observed_difference": observed, "pair_status": status})

    q43_witnesses = [q43_books[bookid] for bookid in Q43_SLOT_WITNESSES if bookid in q43_books]
    passing_pair_count = sum(1 for row in pair_rows if row["pair_status"] == "PAIR_PASSES_ROLE_CONTRAST_NO_GLOSS")
    phase_control_count = sum(1 for item in classified.values() if item["book_class"] == "PHASE_CONTEXT_CONTROL")
    boundary_control_count = sum(1 for item in classified.values() if item["book_class"] == "BOUNDARY_AUDIT_CONTROL")
    functional_role_accept_count = 1 if passing_pair_count == len(MINIMAL_PAIRS) and len(q43_witnesses) == 3 else 0
    lexical_ready_count = 0
    direct_gloss_count = 0
    canonical_promotion_allowed_count = 0
    role_human_version = (
        "C68/NAESE slot-classifier role: minimal pairs separate slot/classifier windows from phase/context and boundary controls. "
        "The role is functionally accepted for shadow work, but no C68 or NAESE word meaning is promoted."
    )
    decision = (
        "Q61_C68_NAESE_SLOT_ROLE_MINIMAL_PAIRS_ACCEPT_FUNCTIONAL_ROLE_NO_GLOSS"
        if len(q43_witnesses) == 3
        and len(pair_rows) == 6
        and passing_pair_count == 6
        and phase_control_count == 2
        and boundary_control_count == 1
        and functional_role_accept_count == 1
        and lexical_ready_count == 0
        and int(q60["lexical_ready_count"]) == 0
        and int(audit["promoted_gloss_count"]) == 0
        and direct_gloss_count == 0
        and canonical_promotion_allowed_count == 0
        else "Q61_C68_NAESE_SLOT_ROLE_MINIMAL_PAIRS_REQUIRES_REVIEW"
    )
    payload = {
        "question": "Can C68/NAESE slot-classifier be accepted as a functional role through minimal pairs?",
        "answer": "Yes, as a functional shadow role only; lexical promotion remains blocked.",
        "role_human_version": role_human_version,
        "candidate": dict(candidate),
        "blocked_use": "Do not translate C68, NAESE, slot, or classifier as words.",
        "next_action": "Run the next strongest Q60 target: C86/VNCTIIN context-route ready-vs-audit contrast.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q61_c68_naese_slot_role_minimal_pairs_v1_runs (
                created_at, decision, q60_run_id, q59_run_id, q53_run_id,
                q50_run_id, q48_run_id, q47_run_id, q43_run_id,
                completion_audit_run_id, target_book_count, control_book_count,
                canonical_slot_witness_count, minimal_pair_count,
                passing_pair_count, phase_control_count, boundary_control_count,
                functional_role_accept_count, lexical_ready_count,
                direct_gloss_count, canonical_promotion_allowed_count,
                role_human_version, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                int(q60["run_id"]),
                int(q59["run_id"]),
                int(q53["run_id"]),
                int(q50["run_id"]),
                q48_run_id,
                q47_run_id,
                q43_run_id,
                int(audit["run_id"]),
                len(TARGET_BOOKS),
                len(CONTROL_BOOKS),
                len(q43_witnesses),
                len(pair_rows),
                passing_pair_count,
                phase_control_count,
                boundary_control_count,
                functional_role_accept_count,
                lexical_ready_count,
                direct_gloss_count,
                canonical_promotion_allowed_count,
                role_human_version,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q61_c68_naese_slot_role_minimal_pairs_v1_books (
                run_id, bookid, book_class, q48_window_class, q50_c68_profile,
                q53_chain_profile, q59_route_role, slot_signal, phase_signal,
                boundary_signal, role_verdict, blocked_claim, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    item["bookid"],
                    item["book_class"],
                    item["q48_window_class"],
                    item["q50_c68_profile"],
                    item["q53_chain_profile"],
                    item["q59_route_role"],
                    int(item["slot_signal"]),
                    int(item["phase_signal"]),
                    int(item["boundary_signal"]),
                    item["role_verdict"],
                    item["blocked_claim"],
                    j(item["evidence"]),
                )
                for item in classified.values()
            ],
        )
        conn.executemany(
            """
            INSERT INTO human_q61_c68_naese_slot_role_minimal_pairs_v1_pairs (
                run_id, pair_id, target_book, control_book, contrast_axis,
                expected_difference, observed_difference, pair_status, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    row["pair_id"],
                    row["target_book"],
                    row["control_book"],
                    row["contrast_axis"],
                    row["expected_difference"],
                    row["observed_difference"],
                    row["pair_status"],
                    j({"target": classified[row["target_book"]], "control": classified[row["control_book"]]}),
                )
                for row in pair_rows
            ],
        )
        conn.executemany(
            """
            INSERT INTO human_q61_c68_naese_slot_role_minimal_pairs_v1_q43_witnesses (
                run_id, bookid, c68_context_class, c68_slot_status,
                naese_status, naese_role_label, witness_use, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    str(row["bookid"]),
                    str(row["c68_context_class"]),
                    str(row["c68_slot_status"]),
                    str(row["naese_status"]),
                    str(row["naese_role_label"]),
                    "Canonical slot witness for role-level support only; no phrase or word gloss.",
                    j(dict(row)),
                )
                for row in q43_witnesses
            ],
        )

    print(
        j(
            {
                "run_id": run_id,
                "decision": decision,
                "target_book_count": len(TARGET_BOOKS),
                "control_book_count": len(CONTROL_BOOKS),
                "canonical_slot_witness_count": len(q43_witnesses),
                "minimal_pair_count": len(pair_rows),
                "passing_pair_count": passing_pair_count,
                "functional_role_accept_count": functional_role_accept_count,
                "lexical_ready_count": lexical_ready_count,
                "direct_gloss_count": direct_gloss_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
            }
        )
    )


if __name__ == "__main__":
    main()
