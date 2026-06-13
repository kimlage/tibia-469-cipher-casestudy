#!/usr/bin/env python3
"""Q65: heldout role gate for Book 27 payload/context hold."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

TARGET_BOOK = "27"
CONTROL_BOOKS = ["67", "2", "57", "42"]
SOURCE_SAFEGUARDS = [
    "PARADOX_1_PLUS_1_KEYS",
    "THREAT_I_EYESTALK_MAGIC_COMMAND_DEAD",
    "THREAT_II_RESEARCH_EXPERIMENTS",
    "THREAT_III_MIND_BODY_SOUL_EXPERIMENTS",
]

CONTRASTS = [
    {
        "contrast_id": "Q65_PAIR_27_VS_67",
        "target": "27",
        "control": "67",
        "contrast_axis": "CONTEXT_HOLD_VS_HANDOFF_EDGE",
        "expected_difference": "Book 27 is ready context route without edge; Book 67 is exact-contig handoff edge.",
    },
    {
        "contrast_id": "Q65_PAIR_27_VS_2",
        "target": "27",
        "control": "2",
        "contrast_axis": "CONTEXT_HOLD_VS_SLOT_TARGET",
        "expected_difference": "Book 27 stays phase/context; Book 2 continues into mixed slot target.",
    },
    {
        "contrast_id": "Q65_PAIR_27_VS_57",
        "target": "27",
        "control": "57",
        "contrast_axis": "READY_CONTEXT_VS_WEAK_AUDIT",
        "expected_difference": "Book 27 is ready EVIEFIIN->VN/C68/TIIN route; Book 57 is weak audit surface.",
    },
    {
        "contrast_id": "Q65_PAIR_27_VS_42",
        "target": "27",
        "control": "42",
        "contrast_axis": "READY_CONTEXT_VS_BOUNDARY_AUDIT",
        "expected_difference": "Book 27 is ready context route; Book 42 is boundary/surface audit control.",
    },
    {
        "contrast_id": "Q65_SOURCE_FIREWALL",
        "target": "27",
        "control": "sources",
        "contrast_axis": "SOURCE_REGISTER_NOT_DICTIONARY",
        "expected_difference": "Threat and Paradox sources support register/operator constraints, not dictionary meanings.",
    },
]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q65_payload_context_hold_heldout_role_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q60_run_id INTEGER NOT NULL,
            q59_run_id INTEGER NOT NULL,
            q58_run_id INTEGER NOT NULL,
            q55_run_id INTEGER NOT NULL,
            q54_run_id INTEGER NOT NULL,
            q53_run_id INTEGER NOT NULL,
            q52_run_id INTEGER NOT NULL,
            q50_run_id INTEGER NOT NULL,
            q61_run_id INTEGER NOT NULL,
            q62_run_id INTEGER NOT NULL,
            q64_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            target_book_count INTEGER NOT NULL,
            control_book_count INTEGER NOT NULL,
            ready_context_target_count INTEGER NOT NULL,
            missing_edge_count INTEGER NOT NULL,
            slot_handoff_control_count INTEGER NOT NULL,
            audit_control_count INTEGER NOT NULL,
            source_safeguard_count INTEGER NOT NULL,
            contrast_count INTEGER NOT NULL,
            passing_contrast_count INTEGER NOT NULL,
            heldout_role_accept_count INTEGER NOT NULL,
            stop_continue_resolved_count INTEGER NOT NULL,
            lexical_ready_count INTEGER NOT NULL,
            direct_gloss_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            role_human_version TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q65_payload_context_hold_heldout_role_v1_books (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            book_class TEXT NOT NULL,
            q54_phrase_profile TEXT NOT NULL,
            q54_edge_status TEXT NOT NULL,
            q52_c86_profile TEXT NOT NULL,
            q53_chain_profile TEXT NOT NULL,
            q50_c68_profile TEXT NOT NULL,
            q59_route_role TEXT NOT NULL,
            q62_role_verdict TEXT NOT NULL,
            q64_role_verdict TEXT NOT NULL,
            ready_context_signal INTEGER NOT NULL,
            edge_or_slot_signal INTEGER NOT NULL,
            audit_control_signal INTEGER NOT NULL,
            heldout_role_signal INTEGER NOT NULL,
            role_verdict TEXT NOT NULL,
            blocked_claim TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        );

        CREATE TABLE IF NOT EXISTS human_q65_payload_context_hold_heldout_role_v1_contrasts (
            run_id INTEGER NOT NULL,
            contrast_id TEXT NOT NULL,
            target TEXT NOT NULL,
            control TEXT NOT NULL,
            contrast_axis TEXT NOT NULL,
            expected_difference TEXT NOT NULL,
            observed_difference TEXT NOT NULL,
            contrast_status TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, contrast_id)
        );

        CREATE TABLE IF NOT EXISTS human_q65_payload_context_hold_heldout_role_v1_sources (
            run_id INTEGER NOT NULL,
            source_id TEXT NOT NULL,
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


def load_by_book(conn: sqlite3.Connection, table: str, run_id: int) -> dict[str, sqlite3.Row]:
    rows = conn.execute(f"SELECT * FROM {table} WHERE run_id=?", (run_id,)).fetchall()
    return {str(row["bookid"]): row for row in rows}


def load_q60_candidate(conn: sqlite3.Connection, q60_run_id: int) -> sqlite3.Row:
    row = conn.execute(
        """
        SELECT *
        FROM human_q60_component_role_promotion_queue_v1_candidates
        WHERE run_id=? AND candidate_id='Q60_C05_PAYLOAD_CONTEXT_HOLD_ROLE'
        """,
        (q60_run_id,),
    ).fetchone()
    if row is None:
        raise RuntimeError("missing Q60 payload/context hold candidate")
    return row


def load_q58_target_result(conn: sqlite3.Connection, q58_run_id: int) -> sqlite3.Row:
    row = conn.execute(
        """
        SELECT *
        FROM human_q58_execute_remaining_contrasts_firewall_v1_results
        WHERE run_id=? AND test_id='Q56_T05_PAYLOAD_CONTEXT_HOLD'
        """,
        (q58_run_id,),
    ).fetchone()
    if row is None:
        raise RuntimeError("missing Q58 payload/context hold result")
    return row


def load_sources(conn: sqlite3.Connection, q55_run_id: int) -> dict[str, sqlite3.Row]:
    placeholders = ",".join("?" for _ in SOURCE_SAFEGUARDS)
    rows = conn.execute(
        f"""
        SELECT *
        FROM human_q55_source_parallel_audit_q54_v1_sources
        WHERE run_id=? AND source_id IN ({placeholders})
        """,
        (q55_run_id, *SOURCE_SAFEGUARDS),
    ).fetchall()
    by_source = {str(row["source_id"]): row for row in rows}
    missing = [source_id for source_id in SOURCE_SAFEGUARDS if source_id not in by_source]
    if missing:
        raise RuntimeError(f"missing source safeguards: {missing}")
    return by_source


def book_class(bookid: str) -> str:
    if bookid == "27":
        return "HELDOUT_PAYLOAD_CONTEXT_TARGET"
    if bookid == "67":
        return "HANDOFF_EDGE_CONTROL"
    if bookid == "2":
        return "SLOT_TARGET_CONTROL"
    if bookid == "57":
        return "WEAK_AUDIT_CONTROL"
    if bookid == "42":
        return "BOUNDARY_AUDIT_CONTROL"
    return "OTHER"


def classify_book(
    bookid: str,
    q54_books: dict[str, sqlite3.Row],
    q53_books: dict[str, sqlite3.Row],
    q52_books: dict[str, sqlite3.Row],
    q50_books: dict[str, sqlite3.Row],
    q59_books: dict[str, sqlite3.Row],
    q62_books: dict[str, sqlite3.Row],
    q64_books: dict[str, sqlite3.Row],
) -> dict[str, object]:
    q54 = q54_books.get(bookid)
    q53 = q53_books.get(bookid)
    q52 = q52_books.get(bookid)
    q50 = q50_books.get(bookid)
    q59 = q59_books.get(bookid)
    q62 = q62_books.get(bookid)
    q64 = q64_books.get(bookid)
    q54_profile = str(q54["phrase_profile"]) if q54 is not None else "NO_Q54_PROFILE"
    q54_edge_status = str(q54["edge_confirmation_status"]) if q54 is not None else "NO_Q54_EDGE"
    q52_profile = str(q52["c86_profile"]) if q52 is not None else "NO_Q52_C86"
    q53_profile = str(q53["chain_profile"]) if q53 is not None else "NO_Q53_CHAIN"
    q50_profile = str(q50["c68_profile"]) if q50 is not None else "NO_Q50_C68"
    q59_role = str(q59["route_role"]) if q59 is not None else "NO_Q59_ROUTE"
    q62_verdict = str(q62["role_verdict"]) if q62 is not None else "NO_Q62_VERDICT"
    q64_verdict = str(q64["role_verdict"]) if q64 is not None else "NO_Q64_VERDICT"
    ready_context_signal = int(
        bookid == "27"
        and q52_profile == "C86_READY_VN_C68_TIIN_CONTEXT"
        and q53_profile == "SUPPORTED_CONTEXT_CHAIN"
        and q50_profile == "C68_PHASE_CONTEXT_ONLY"
        and q54_edge_status == "NO_DIRECT_EDGE_CONFIRMATION"
    )
    edge_or_slot_signal = int(
        (bookid == "67" and q54_edge_status == "EDGE_CONFIRMED")
        or (bookid == "2" and q53_profile == "SUPPORTED_CONTEXT_TO_SLOT_CHAIN")
    )
    audit_control_signal = int(
        (bookid == "57" and "AUDIT" in q52_profile)
        or (bookid == "42" and "AUDIT" in q53_profile)
    )
    heldout_role_signal = int(bookid == "27" and ready_context_signal == 1 and q59_role == "HELDOUT_PAYLOAD_CONTEXT_HOLD")
    if heldout_role_signal:
        verdict = "HELDOUT_PAYLOAD_CONTEXT_HOLD_ACCEPT_MODERATE_ROLE"
    elif bookid == "67":
        verdict = "HANDOFF_EDGE_CONTROL_BLOCKS_HOLD_AS_EDGE"
    elif bookid == "2":
        verdict = "SLOT_TARGET_CONTROL_BLOCKS_HOLD_AS_SLOT"
    elif bookid == "57":
        verdict = "WEAK_AUDIT_CONTROL_BLOCKS_READY_HELDOUT"
    elif bookid == "42":
        verdict = "BOUNDARY_AUDIT_CONTROL_BLOCKS_READY_HELDOUT"
    else:
        verdict = "REQUIRES_REVIEW"
    return {
        "bookid": bookid,
        "book_class": book_class(bookid),
        "q54_phrase_profile": q54_profile,
        "q54_edge_status": q54_edge_status,
        "q52_c86_profile": q52_profile,
        "q53_chain_profile": q53_profile,
        "q50_c68_profile": q50_profile,
        "q59_route_role": q59_role,
        "q62_role_verdict": q62_verdict,
        "q64_role_verdict": q64_verdict,
        "ready_context_signal": ready_context_signal,
        "edge_or_slot_signal": edge_or_slot_signal,
        "audit_control_signal": audit_control_signal,
        "heldout_role_signal": heldout_role_signal,
        "role_verdict": verdict,
        "blocked_claim": "Heldout payload/context role only; do not translate as command, dead, soul, necromancy, transformation, or stop punctuation.",
        "evidence": {
            "q54": dict(q54) if q54 is not None else None,
            "q53": dict(q53) if q53 is not None else None,
            "q52": dict(q52) if q52 is not None else None,
            "q50": dict(q50) if q50 is not None else None,
            "q59": dict(q59) if q59 is not None else None,
            "q62": dict(q62) if q62 is not None else None,
            "q64": dict(q64) if q64 is not None else None,
        },
    }


def contrast_status(
    contrast: dict[str, str],
    classified: dict[str, dict[str, object]],
    sources: dict[str, sqlite3.Row],
) -> tuple[str, str, dict[str, object]]:
    if contrast["contrast_axis"] == "SOURCE_REGISTER_NOT_DICTIONARY":
        all_blocked = all(str(row["blocked_inference"]).strip() for row in sources.values())
        observed = "; ".join(f"{sid}:{sources[sid]['blocked_inference']}" for sid in SOURCE_SAFEGUARDS)
        status = "CONTRAST_PASSES_HELDOUT_SOURCE_FIREWALL_NO_GLOSS" if all_blocked else "CONTRAST_REQUIRES_REVIEW"
        return status, observed, {"sources": {sid: dict(row) for sid, row in sources.items()}}

    target = classified[contrast["target"]]
    control = classified[contrast["control"]]
    target_ok = int(target["heldout_role_signal"]) == 1
    if contrast["contrast_axis"] == "CONTEXT_HOLD_VS_HANDOFF_EDGE":
        passes = target_ok and control["bookid"] == "67" and int(control["edge_or_slot_signal"]) == 1
    elif contrast["contrast_axis"] == "CONTEXT_HOLD_VS_SLOT_TARGET":
        passes = target_ok and control["bookid"] == "2" and int(control["edge_or_slot_signal"]) == 1
    elif contrast["contrast_axis"] == "READY_CONTEXT_VS_WEAK_AUDIT":
        passes = target_ok and control["bookid"] == "57" and int(control["audit_control_signal"]) == 1
    elif contrast["contrast_axis"] == "READY_CONTEXT_VS_BOUNDARY_AUDIT":
        passes = target_ok and control["bookid"] == "42" and int(control["audit_control_signal"]) == 1
    else:
        passes = False
    observed = (
        f"{contrast['target']}={target['q52_c86_profile']}/{target['q53_chain_profile']}/{target['q54_edge_status']}/{target['q59_route_role']} "
        f"vs {contrast['control']}={control['q52_c86_profile']}/{control['q53_chain_profile']}/{control['q54_edge_status']}/{control['q59_route_role']}"
    )
    status = "CONTRAST_PASSES_HELDOUT_ROLE_NO_GLOSS" if passes else "CONTRAST_REQUIRES_REVIEW"
    return status, observed, {"target": target, "control": control}


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q60 = latest_row(conn, "human_q60_component_role_promotion_queue_v1_runs")
    q59 = latest_row(conn, "human_q59_consolidated_shadow_backbone_v1_runs")
    q58 = latest_row(conn, "human_q58_execute_remaining_contrasts_firewall_v1_runs")
    q55 = latest_row(conn, "human_q55_source_parallel_audit_q54_v1_runs")
    q54 = latest_row(conn, "human_q54_supported_chain_phrase_layer_v1_runs")
    q53 = latest_row(conn, "human_q53_c86_c68_chain_synthesis_v1_runs")
    q52 = latest_row(conn, "human_q52_c86_book_synthesis_v1_runs")
    q50 = latest_row(conn, "human_q50_c68_book_synthesis_v1_runs")
    q61 = latest_row(conn, "human_q61_c68_naese_slot_role_minimal_pairs_v1_runs")
    q62 = latest_row(conn, "human_q62_c86_vnctiin_context_route_ready_audit_v1_runs")
    q64 = latest_row(conn, "human_q64_edge_67_2_handoff_role_contrast_v1_runs")
    audit = latest_row(conn, "human_translation_completion_audit_v5_runs")

    candidate = load_q60_candidate(conn, int(q60["run_id"]))
    q58_target = load_q58_target_result(conn, int(q58["run_id"]))
    sources = load_sources(conn, int(q55["run_id"]))
    q54_books = load_by_book(conn, "human_q54_supported_chain_phrase_layer_v1_books", int(q54["run_id"]))
    q53_books = load_by_book(conn, "human_q53_c86_c68_chain_synthesis_v1_books", int(q53["run_id"]))
    q52_books = load_by_book(conn, "human_q52_c86_book_synthesis_v1_books", int(q52["run_id"]))
    q50_books = load_by_book(conn, "human_q50_c68_book_synthesis_v1_books", int(q50["run_id"]))
    q59_books = load_by_book(conn, "human_q59_consolidated_shadow_backbone_v1_books", int(q59["run_id"]))
    q62_books = load_by_book(conn, "human_q62_c86_vnctiin_context_route_ready_audit_v1_books", int(q62["run_id"]))
    q64_books = load_by_book(conn, "human_q64_edge_67_2_handoff_role_contrast_v1_books", int(q64["run_id"]))

    all_books = [TARGET_BOOK, *CONTROL_BOOKS]
    classified = {
        bookid: classify_book(bookid, q54_books, q53_books, q52_books, q50_books, q59_books, q62_books, q64_books)
        for bookid in all_books
    }

    contrast_rows = []
    for contrast in CONTRASTS:
        status, observed, evidence = contrast_status(contrast, classified, sources)
        contrast_rows.append({**contrast, "observed_difference": observed, "contrast_status": status, "evidence": evidence})

    ready_context_target_count = int(classified[TARGET_BOOK]["ready_context_signal"])
    missing_edge_count = int(classified[TARGET_BOOK]["q54_edge_status"] == "NO_DIRECT_EDGE_CONFIRMATION")
    slot_handoff_control_count = sum(1 for bookid in ["67", "2"] if int(classified[bookid]["edge_or_slot_signal"]) == 1)
    audit_control_count = sum(1 for bookid in ["57", "42"] if int(classified[bookid]["audit_control_signal"]) == 1)
    source_safeguard_count = len(sources)
    passing_contrast_count = sum(1 for row in contrast_rows if row["contrast_status"].startswith("CONTRAST_PASSES"))
    heldout_role_accept_count = 1 if ready_context_target_count == 1 and passing_contrast_count == len(CONTRASTS) else 0
    stop_continue_resolved_count = 0
    lexical_ready_count = 0
    direct_gloss_count = 0
    canonical_promotion_allowed_count = 0
    role_human_version = (
        "Book27 payload/context-hold role: Book27 is a ready C86/VNCTIIN context route without the observed 67->2 edge or Book2 slot target. "
        "It is accepted as a moderate heldout role, while stop-vs-missing-edge remains unresolved and source-register overreach remains blocked."
    )
    decision = (
        "Q65_PAYLOAD_CONTEXT_HOLD_HELDOUT_ROLE_ACCEPT_MODERATE_OPEN_NO_GLOSS"
        if len(contrast_rows) == 5
        and passing_contrast_count == 5
        and ready_context_target_count == 1
        and missing_edge_count == 1
        and slot_handoff_control_count == 2
        and audit_control_count == 2
        and source_safeguard_count == 4
        and heldout_role_accept_count == 1
        and stop_continue_resolved_count == 0
        and int(q58["accepted_firewall_test_count"]) == 1
        and int(q60["lexical_ready_count"]) == 0
        and int(audit["promoted_gloss_count"]) == 0
        and lexical_ready_count == 0
        and direct_gloss_count == 0
        and canonical_promotion_allowed_count == 0
        else "Q65_PAYLOAD_CONTEXT_HOLD_HELDOUT_ROLE_REQUIRES_REVIEW"
    )
    payload = {
        "question": "Can Book27 payload/context hold be accepted as a heldout functional role?",
        "answer": "Yes, as a moderate heldout role only; stop-vs-missing-edge remains open.",
        "role_human_version": role_human_version,
        "candidate": dict(candidate),
        "q58_target_result": dict(q58_target),
        "blocked_use": "Do not translate Book27 as command, dead, soul, necromancy, transformation, or terminal punctuation.",
        "next_action": "Consolidate Q60/Q61-Q65 role outcomes into a role ledger and residual-risk map.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q65_payload_context_hold_heldout_role_v1_runs (
                created_at, decision, q60_run_id, q59_run_id, q58_run_id,
                q55_run_id, q54_run_id, q53_run_id, q52_run_id, q50_run_id,
                q61_run_id, q62_run_id, q64_run_id, completion_audit_run_id,
                target_book_count, control_book_count, ready_context_target_count,
                missing_edge_count, slot_handoff_control_count,
                audit_control_count, source_safeguard_count, contrast_count,
                passing_contrast_count, heldout_role_accept_count,
                stop_continue_resolved_count, lexical_ready_count,
                direct_gloss_count, canonical_promotion_allowed_count,
                role_human_version, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                int(q60["run_id"]),
                int(q59["run_id"]),
                int(q58["run_id"]),
                int(q55["run_id"]),
                int(q54["run_id"]),
                int(q53["run_id"]),
                int(q52["run_id"]),
                int(q50["run_id"]),
                int(q61["run_id"]),
                int(q62["run_id"]),
                int(q64["run_id"]),
                int(audit["run_id"]),
                1,
                len(CONTROL_BOOKS),
                ready_context_target_count,
                missing_edge_count,
                slot_handoff_control_count,
                audit_control_count,
                source_safeguard_count,
                len(contrast_rows),
                passing_contrast_count,
                heldout_role_accept_count,
                stop_continue_resolved_count,
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
            INSERT INTO human_q65_payload_context_hold_heldout_role_v1_books (
                run_id, bookid, book_class, q54_phrase_profile, q54_edge_status,
                q52_c86_profile, q53_chain_profile, q50_c68_profile,
                q59_route_role, q62_role_verdict, q64_role_verdict,
                ready_context_signal, edge_or_slot_signal, audit_control_signal,
                heldout_role_signal, role_verdict, blocked_claim, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    item["bookid"],
                    item["book_class"],
                    item["q54_phrase_profile"],
                    item["q54_edge_status"],
                    item["q52_c86_profile"],
                    item["q53_chain_profile"],
                    item["q50_c68_profile"],
                    item["q59_route_role"],
                    item["q62_role_verdict"],
                    item["q64_role_verdict"],
                    int(item["ready_context_signal"]),
                    int(item["edge_or_slot_signal"]),
                    int(item["audit_control_signal"]),
                    int(item["heldout_role_signal"]),
                    item["role_verdict"],
                    item["blocked_claim"],
                    j(item["evidence"]),
                )
                for item in classified.values()
            ],
        )
        conn.executemany(
            """
            INSERT INTO human_q65_payload_context_hold_heldout_role_v1_contrasts (
                run_id, contrast_id, target, control, contrast_axis,
                expected_difference, observed_difference, contrast_status,
                evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    row["contrast_id"],
                    row["target"],
                    row["control"],
                    row["contrast_axis"],
                    row["expected_difference"],
                    row["observed_difference"],
                    row["contrast_status"],
                    j(row["evidence"]),
                )
                for row in contrast_rows
            ],
        )
        conn.executemany(
            """
            INSERT INTO human_q65_payload_context_hold_heldout_role_v1_sources (
                run_id, source_id, source_role, source_parallel_use,
                blocked_inference, source_use_status, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    source_id,
                    str(row["source_role"]),
                    str(row["source_parallel_use"]),
                    str(row["blocked_inference"]),
                    "REGISTER_SUPPORT_ONLY_NO_DICTIONARY",
                    j(dict(row)),
                )
                for source_id, row in sorted(sources.items())
            ],
        )

    print(
        j(
            {
                "run_id": run_id,
                "decision": decision,
                "target_book_count": 1,
                "control_book_count": len(CONTROL_BOOKS),
                "ready_context_target_count": ready_context_target_count,
                "missing_edge_count": missing_edge_count,
                "slot_handoff_control_count": slot_handoff_control_count,
                "audit_control_count": audit_control_count,
                "source_safeguard_count": source_safeguard_count,
                "contrast_count": len(contrast_rows),
                "passing_contrast_count": passing_contrast_count,
                "heldout_role_accept_count": heldout_role_accept_count,
                "stop_continue_resolved_count": stop_continue_resolved_count,
                "lexical_ready_count": lexical_ready_count,
                "direct_gloss_count": direct_gloss_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
            }
        )
    )


if __name__ == "__main__":
    main()
