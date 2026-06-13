#!/usr/bin/env python3
"""Q62: ready-vs-audit gate for the C86/VNCTIIN context-route role."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

TARGET_BOOKS = ["2", "10", "27", "35", "67"]
CONTROL_BOOKS = ["5", "31", "42", "57"]

CONTRASTS = [
    {
        "contrast_id": "Q62_PAIR_2_VS_5",
        "target_book": "2",
        "control_book": "5",
        "contrast_axis": "READY_CONTEXT_ROUTE_VS_ETIE_RESIDUAL",
        "expected_difference": "Book 2 is ready VN/C68/TIIN context route; Book 5 is ETIE residual audit.",
    },
    {
        "contrast_id": "Q62_PAIR_10_VS_31",
        "target_book": "10",
        "control_book": "31",
        "contrast_axis": "READY_FORMULA_CONTEXT_VS_EILTAEN_LOCAL",
        "expected_difference": "Book 10 is ready formula->context route; Book 31 is EILTAEN local audit.",
    },
    {
        "contrast_id": "Q62_PAIR_27_VS_57",
        "target_book": "27",
        "control_book": "57",
        "contrast_axis": "READY_PAYLOAD_CONTEXT_VS_EEN_WEAK",
        "expected_difference": "Book 27 is ready payload/context route; Book 57 is weak EEN/C68 audit.",
    },
    {
        "contrast_id": "Q62_PAIR_67_VS_42",
        "target_book": "67",
        "control_book": "42",
        "contrast_axis": "READY_EVIEFIIN_CONTEXT_VS_EVIEFIIN_SURFACE_AUDIT",
        "expected_difference": "Book 67 is ready EVIEFIIN->VN/C68/TIIN context route; Book 42 is EVIEFIIN surface audit.",
    },
    {
        "contrast_id": "Q62_PAIR_35_VS_5",
        "target_book": "35",
        "control_book": "5",
        "contrast_axis": "READY_FORMULA_CONTEXT_VS_SLOT_TO_FORMULA_AUDIT",
        "expected_difference": "Book 35 is formula->context route; Book 5 is slot-to-formula with unsupported C86.",
    },
]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q62_c86_vnctiin_context_route_ready_audit_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q60_run_id INTEGER NOT NULL,
            q59_run_id INTEGER NOT NULL,
            q53_run_id INTEGER NOT NULL,
            q52_run_id INTEGER NOT NULL,
            q51_run_id INTEGER NOT NULL,
            chain_probe_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            target_book_count INTEGER NOT NULL,
            control_book_count INTEGER NOT NULL,
            ready_target_count INTEGER NOT NULL,
            audit_control_count INTEGER NOT NULL,
            surface_audit_control_count INTEGER NOT NULL,
            contrast_count INTEGER NOT NULL,
            passing_contrast_count INTEGER NOT NULL,
            functional_role_accept_count INTEGER NOT NULL,
            lexical_ready_count INTEGER NOT NULL,
            direct_gloss_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            role_human_version TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q62_c86_vnctiin_context_route_ready_audit_v1_books (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            book_class TEXT NOT NULL,
            q51_window_class TEXT NOT NULL,
            q51_branch_id TEXT NOT NULL,
            q51_payload_decision TEXT NOT NULL,
            q52_c86_profile TEXT NOT NULL,
            q53_chain_profile TEXT NOT NULL,
            q59_route_role TEXT NOT NULL,
            ready_signal INTEGER NOT NULL,
            audit_signal INTEGER NOT NULL,
            role_verdict TEXT NOT NULL,
            blocked_claim TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        );

        CREATE TABLE IF NOT EXISTS human_q62_c86_vnctiin_context_route_ready_audit_v1_contrasts (
            run_id INTEGER NOT NULL,
            contrast_id TEXT NOT NULL,
            target_book TEXT NOT NULL,
            control_book TEXT NOT NULL,
            contrast_axis TEXT NOT NULL,
            expected_difference TEXT NOT NULL,
            observed_difference TEXT NOT NULL,
            contrast_status TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, contrast_id)
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
        WHERE run_id=? AND candidate_id='Q60_C02_C86_VNCTIIN_CONTEXT_ROUTE_ROLE'
        """,
        (q60_run_id,),
    ).fetchone()
    if row is None:
        raise RuntimeError("missing Q60 C86/VNCTIIN context-route candidate")
    return row


def load_chain_items(conn: sqlite3.Connection, run_id: int) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM c86_c68_naese_chain_probe_v1_items WHERE run_id=?", (run_id,)).fetchall()


def book_class(bookid: str) -> str:
    if bookid in TARGET_BOOKS:
        return "READY_CONTEXT_ROUTE_TARGET"
    if bookid == "42":
        return "EVIEFIIN_SURFACE_AUDIT_CONTROL"
    return "AUDIT_SURFACE_CONTROL"


def classify_book(
    bookid: str,
    q51_books: dict[str, sqlite3.Row],
    q52_books: dict[str, sqlite3.Row],
    q53_books: dict[str, sqlite3.Row],
    q59_books: dict[str, sqlite3.Row],
) -> dict[str, object]:
    q51 = q51_books[bookid]
    q52 = q52_books[bookid]
    q53 = q53_books[bookid]
    q59 = q59_books.get(bookid)
    payload_decision = str(q51["payload_gate_decision"])
    c86_profile = str(q52["c86_profile"])
    chain_profile = str(q53["chain_profile"])
    ready_signal = int(
        payload_decision == "PAYLOAD_BRANCH_FUNCTION_READY_NO_GLOSS"
        and c86_profile == "C86_READY_VN_C68_TIIN_CONTEXT"
        and chain_profile.startswith("SUPPORTED_CONTEXT")
    )
    audit_signal = int(payload_decision == "AUDIT_OR_SURFACE_CONTEXT_NO_PROMOTION" or "AUDIT" in c86_profile)
    if ready_signal:
        verdict = "READY_VN_C68_TIIN_CONTEXT_ROUTE_SUPPORTS_ROLE"
    elif bookid == "42":
        verdict = "EVIEFIIN_SURFACE_AUDIT_BLOCKS_CONTEXT_ROUTE_PROMOTION"
    else:
        verdict = "AUDIT_SURFACE_CONTROL_BLOCKS_CONTEXT_ROUTE_PROMOTION"
    return {
        "bookid": bookid,
        "book_class": book_class(bookid),
        "q51_window_class": str(q51["window_class"]),
        "q51_branch_id": str(q51["payload_gate_branch_id"]),
        "q51_payload_decision": payload_decision,
        "q52_c86_profile": c86_profile,
        "q53_chain_profile": chain_profile,
        "q59_route_role": str(q59["route_role"]) if q59 is not None else "NO_Q59_ROUTE",
        "ready_signal": ready_signal,
        "audit_signal": audit_signal,
        "role_verdict": verdict,
        "blocked_claim": "Functional context-route role only; no C86, VNCTIIN, context, payload, or route word gloss.",
        "evidence": {
            "q51": dict(q51),
            "q52": dict(q52),
            "q53": dict(q53),
            "q59": dict(q59) if q59 is not None else None,
        },
    }


def contrast_status(contrast: dict[str, str], classified: dict[str, dict[str, object]]) -> tuple[str, str]:
    target = classified[contrast["target_book"]]
    control = classified[contrast["control_book"]]
    target_ready = int(target["ready_signal"]) == 1
    control_audit = int(control["audit_signal"]) == 1
    if contrast["contrast_axis"] == "READY_EVIEFIIN_CONTEXT_VS_EVIEFIIN_SURFACE_AUDIT":
        passes = (
            target_ready
            and control_audit
            and str(target["q51_window_class"]) == "C86_EVIEFIIN_CONTEXT_WINDOW"
            and str(control["q51_window_class"]) == "C86_EVIEFIIN_CONTEXT_WINDOW"
            and str(target["q51_branch_id"]) == "C86_BRANCH_EVIEFIIN_TO_VN_C68_TIIN"
            and str(control["q51_branch_id"]) == "C86_BRANCH_EVIEFIIN_PAYLOAD"
        )
    else:
        passes = target_ready and control_audit and str(target["q51_branch_id"]) == "C86_BRANCH_EVIEFIIN_TO_VN_C68_TIIN"
    observed = (
        f"{contrast['target_book']}={target['q51_window_class']}/{target['q51_branch_id']}/{target['q51_payload_decision']} "
        f"vs {contrast['control_book']}={control['q51_window_class']}/{control['q51_branch_id']}/{control['q51_payload_decision']}"
    )
    return ("CONTRAST_PASSES_READY_VS_AUDIT_NO_GLOSS" if passes else "CONTRAST_REQUIRES_REVIEW", observed)


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q60 = latest_row(conn, "human_q60_component_role_promotion_queue_v1_runs")
    q59 = latest_row(conn, "human_q59_consolidated_shadow_backbone_v1_runs")
    q53 = latest_row(conn, "human_q53_c86_c68_chain_synthesis_v1_runs")
    q52 = latest_row(conn, "human_q52_c86_book_synthesis_v1_runs")
    chain_probe = latest_row(conn, "c86_c68_naese_chain_probe_v1_runs")
    audit = latest_row(conn, "human_translation_completion_audit_v5_runs")
    q51_run_id = latest_item_run_id(conn, "human_q51_c86_window_taxonomy_v1_books", "bookid")

    candidate = q60_candidate(conn, int(q60["run_id"]))
    q59_books = load_by_book(conn, "human_q59_consolidated_shadow_backbone_v1_books", int(q59["run_id"]))
    q53_books = load_by_book(conn, "human_q53_c86_c68_chain_synthesis_v1_books", int(q53["run_id"]))
    q52_books = load_by_book(conn, "human_q52_c86_book_synthesis_v1_books", int(q52["run_id"]))
    q51_books = load_by_book(conn, "human_q51_c86_window_taxonomy_v1_books", q51_run_id)
    chain_items = load_chain_items(conn, int(chain_probe["run_id"]))

    all_books = TARGET_BOOKS + CONTROL_BOOKS
    classified = {
        bookid: classify_book(bookid, q51_books, q52_books, q53_books, q59_books)
        for bookid in all_books
    }

    contrast_rows = []
    for contrast in CONTRASTS:
        status, observed = contrast_status(contrast, classified)
        contrast_rows.append({**contrast, "observed_difference": observed, "contrast_status": status})

    ready_target_count = sum(1 for bookid in TARGET_BOOKS if int(classified[bookid]["ready_signal"]) == 1)
    audit_control_count = sum(1 for bookid in CONTROL_BOOKS if int(classified[bookid]["audit_signal"]) == 1)
    surface_audit_control_count = sum(1 for bookid in CONTROL_BOOKS if classified[bookid]["book_class"] == "EVIEFIIN_SURFACE_AUDIT_CONTROL")
    passing_contrast_count = sum(1 for row in contrast_rows if row["contrast_status"] == "CONTRAST_PASSES_READY_VS_AUDIT_NO_GLOSS")
    functional_role_accept_count = 1 if ready_target_count == 5 and audit_control_count == 4 and passing_contrast_count == 5 else 0
    lexical_ready_count = 0
    direct_gloss_count = 0
    canonical_promotion_allowed_count = 0
    role_human_version = (
        "C86/VNCTIIN context-route role: ready books share EVIEFIIN->VN/C68/TIIN context routing, while audit controls "
        "remain residual, local, weak, or surface-only. The role is functionally accepted for shadow work, but no C86 or VNCTIIN word meaning is promoted."
    )
    decision = (
        "Q62_C86_VNCTIIN_CONTEXT_ROUTE_READY_AUDIT_ACCEPT_FUNCTIONAL_ROLE_NO_GLOSS"
        if len(contrast_rows) == 5
        and passing_contrast_count == 5
        and ready_target_count == 5
        and audit_control_count == 4
        and surface_audit_control_count == 1
        and functional_role_accept_count == 1
        and lexical_ready_count == 0
        and int(q60["lexical_ready_count"]) == 0
        and int(audit["promoted_gloss_count"]) == 0
        and direct_gloss_count == 0
        and canonical_promotion_allowed_count == 0
        else "Q62_C86_VNCTIIN_CONTEXT_ROUTE_READY_AUDIT_REQUIRES_REVIEW"
    )
    payload = {
        "question": "Can C86/VNCTIIN context-route be accepted as a functional role through ready-vs-audit contrasts?",
        "answer": "Yes, as a functional shadow role only; lexical promotion remains blocked.",
        "role_human_version": role_human_version,
        "candidate": dict(candidate),
        "chain_probe_items": [dict(row) for row in chain_items],
        "blocked_use": "Do not translate C86, VNCTIIN, context, payload, or route as words.",
        "next_action": "Run the next Q60 target: BENNA formula-handoff directional contrast.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q62_c86_vnctiin_context_route_ready_audit_v1_runs (
                created_at, decision, q60_run_id, q59_run_id, q53_run_id,
                q52_run_id, q51_run_id, chain_probe_run_id,
                completion_audit_run_id, target_book_count, control_book_count,
                ready_target_count, audit_control_count, surface_audit_control_count,
                contrast_count, passing_contrast_count, functional_role_accept_count,
                lexical_ready_count, direct_gloss_count,
                canonical_promotion_allowed_count, role_human_version, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                int(q60["run_id"]),
                int(q59["run_id"]),
                int(q53["run_id"]),
                int(q52["run_id"]),
                q51_run_id,
                int(chain_probe["run_id"]),
                int(audit["run_id"]),
                len(TARGET_BOOKS),
                len(CONTROL_BOOKS),
                ready_target_count,
                audit_control_count,
                surface_audit_control_count,
                len(contrast_rows),
                passing_contrast_count,
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
            INSERT INTO human_q62_c86_vnctiin_context_route_ready_audit_v1_books (
                run_id, bookid, book_class, q51_window_class, q51_branch_id,
                q51_payload_decision, q52_c86_profile, q53_chain_profile,
                q59_route_role, ready_signal, audit_signal, role_verdict,
                blocked_claim, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    item["bookid"],
                    item["book_class"],
                    item["q51_window_class"],
                    item["q51_branch_id"],
                    item["q51_payload_decision"],
                    item["q52_c86_profile"],
                    item["q53_chain_profile"],
                    item["q59_route_role"],
                    int(item["ready_signal"]),
                    int(item["audit_signal"]),
                    item["role_verdict"],
                    item["blocked_claim"],
                    j(item["evidence"]),
                )
                for item in classified.values()
            ],
        )
        conn.executemany(
            """
            INSERT INTO human_q62_c86_vnctiin_context_route_ready_audit_v1_contrasts (
                run_id, contrast_id, target_book, control_book, contrast_axis,
                expected_difference, observed_difference, contrast_status,
                evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    row["contrast_id"],
                    row["target_book"],
                    row["control_book"],
                    row["contrast_axis"],
                    row["expected_difference"],
                    row["observed_difference"],
                    row["contrast_status"],
                    j({"target": classified[row["target_book"]], "control": classified[row["control_book"]]}),
                )
                for row in contrast_rows
            ],
        )

    print(
        j(
            {
                "run_id": run_id,
                "decision": decision,
                "target_book_count": len(TARGET_BOOKS),
                "control_book_count": len(CONTROL_BOOKS),
                "ready_target_count": ready_target_count,
                "audit_control_count": audit_control_count,
                "surface_audit_control_count": surface_audit_control_count,
                "contrast_count": len(contrast_rows),
                "passing_contrast_count": passing_contrast_count,
                "functional_role_accept_count": functional_role_accept_count,
                "lexical_ready_count": lexical_ready_count,
                "direct_gloss_count": direct_gloss_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
            }
        )
    )


if __name__ == "__main__":
    main()
