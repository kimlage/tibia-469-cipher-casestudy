#!/usr/bin/env python3
"""Q64: functional edge-role gate for the 67->2 handoff."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

TARGET_BOOKS = ["67", "2"]
CONTROL_BOOKS = ["27", "35", "42"]
CONTEXT_PATH_BOOKS = ["35", "67", "2"]

CONTRASTS = [
    {
        "contrast_id": "Q64_EDGE_67_2_ACCEPTED",
        "target": "67->2",
        "control": "no_edge",
        "contrast_axis": "ACCEPTED_EDGE_VS_NO_EDGE",
        "expected_difference": "The 67->2 edge is explicitly accepted in the chain probe; controls have no direct edge acceptance.",
    },
    {
        "contrast_id": "Q64_PAIR_67_VS_27",
        "target": "67",
        "control": "27",
        "contrast_axis": "HANDOFF_EDGE_VS_CONTEXT_HELDOUT",
        "expected_difference": "Book 67 has edge confirmation and exact contig support; Book 27 is heldout context without direct edge.",
    },
    {
        "contrast_id": "Q64_PAIR_67_VS_35",
        "target": "67",
        "control": "35",
        "contrast_axis": "HANDOFF_EDGE_VS_UPSTREAM_FORMULA",
        "expected_difference": "Book 67 is the handoff edge; Book 35 is upstream formula/context route and lacks direct edge confirmation.",
    },
    {
        "contrast_id": "Q64_PAIR_67_VS_42",
        "target": "67",
        "control": "42",
        "contrast_axis": "HANDOFF_EDGE_VS_BOUNDARY_AUDIT",
        "expected_difference": "Book 67 is supported and edge-confirmed; Book 42 is dual-audit boundary control.",
    },
    {
        "contrast_id": "Q64_PATH_35_67_2",
        "target": "35->67->2",
        "control": "non_path_controls",
        "contrast_axis": "EXACT_PATH_FORMULA_HANDOFF_SLOT",
        "expected_difference": "The exact contig path has formula route -> handoff edge -> slot target; controls do not reproduce the path.",
    },
]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q64_edge_67_2_handoff_role_contrast_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q60_run_id INTEGER NOT NULL,
            q59_run_id INTEGER NOT NULL,
            q57_run_id INTEGER NOT NULL,
            q54_run_id INTEGER NOT NULL,
            q53_run_id INTEGER NOT NULL,
            q35_run_id INTEGER NOT NULL,
            q36_run_id INTEGER NOT NULL,
            chain_probe_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            target_book_count INTEGER NOT NULL,
            control_book_count INTEGER NOT NULL,
            exact_path_book_count INTEGER NOT NULL,
            accepted_edge_count INTEGER NOT NULL,
            contrast_count INTEGER NOT NULL,
            passing_contrast_count INTEGER NOT NULL,
            functional_edge_accept_count INTEGER NOT NULL,
            phrase_path_accept_count INTEGER NOT NULL,
            lexical_ready_count INTEGER NOT NULL,
            direct_gloss_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            edge_human_version TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q64_edge_67_2_handoff_role_contrast_v1_books (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            book_class TEXT NOT NULL,
            q54_phrase_profile TEXT NOT NULL,
            q54_edge_status TEXT NOT NULL,
            q36_contig_status TEXT NOT NULL,
            q53_chain_profile TEXT NOT NULL,
            q59_route_role TEXT NOT NULL,
            handoff_edge_signal INTEGER NOT NULL,
            slot_target_signal INTEGER NOT NULL,
            upstream_formula_signal INTEGER NOT NULL,
            control_block_signal INTEGER NOT NULL,
            role_verdict TEXT NOT NULL,
            blocked_claim TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        );

        CREATE TABLE IF NOT EXISTS human_q64_edge_67_2_handoff_role_contrast_v1_contrasts (
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


def load_chain_items(conn: sqlite3.Connection, run_id: int) -> dict[tuple[str, str], sqlite3.Row]:
    rows = conn.execute("SELECT * FROM c86_c68_naese_chain_probe_v1_items WHERE run_id=?", (run_id,)).fetchall()
    return {(str(row["item_type"]), str(row["item_id"])): row for row in rows}


def q60_candidate(conn: sqlite3.Connection, q60_run_id: int) -> sqlite3.Row:
    row = conn.execute(
        """
        SELECT *
        FROM human_q60_component_role_promotion_queue_v1_candidates
        WHERE run_id=? AND candidate_id='Q60_C04_EDGE_67_2_HANDOFF_ROLE'
        """,
        (q60_run_id,),
    ).fetchone()
    if row is None:
        raise RuntimeError("missing Q60 edge 67->2 candidate")
    return row


def load_q57_edge_result(conn: sqlite3.Connection, q57_run_id: int) -> sqlite3.Row:
    row = conn.execute(
        """
        SELECT *
        FROM human_q57_execute_high_priority_contrasts_v1_results
        WHERE run_id=? AND test_id='Q56_T02_67_TO_2_HANDOFF_EDGE'
        """,
        (q57_run_id,),
    ).fetchone()
    if row is None:
        raise RuntimeError("missing Q57 edge 67->2 result")
    return row


def load_contig(conn: sqlite3.Connection, q35_run_id: int) -> sqlite3.Row:
    row = conn.execute(
        """
        SELECT *
        FROM human_q35_contig_shadow_atlas_v1_items
        WHERE run_id=? AND booksinorder='58->35->67->2'
        """,
        (q35_run_id,),
    ).fetchone()
    if row is None:
        raise RuntimeError("missing Q35 contig 58->35->67->2")
    return row


def book_class(bookid: str) -> str:
    if bookid == "67":
        return "HANDOFF_EDGE_TARGET"
    if bookid == "2":
        return "SLOT_TARGET"
    if bookid == "35":
        return "UPSTREAM_FORMULA_CONTROL"
    if bookid == "27":
        return "HELDOUT_CONTEXT_CONTROL"
    if bookid == "42":
        return "BOUNDARY_AUDIT_CONTROL"
    return "OTHER"


def classify_book(
    bookid: str,
    q54_books: dict[str, sqlite3.Row],
    q53_books: dict[str, sqlite3.Row],
    q36_books: dict[str, sqlite3.Row],
    q59_books: dict[str, sqlite3.Row],
) -> dict[str, object]:
    q54 = q54_books.get(bookid)
    q53 = q53_books.get(bookid)
    q36 = q36_books.get(bookid)
    q59 = q59_books.get(bookid)
    q54_profile = str(q54["phrase_profile"]) if q54 is not None else "NO_Q54_PROFILE"
    q54_edge_status = str(q54["edge_confirmation_status"]) if q54 is not None else "NO_Q54_EDGE"
    q36_contig_status = str(q36["contig_status"]) if q36 is not None else "NO_Q36_CONTIG"
    q53_chain_profile = str(q53["chain_profile"]) if q53 is not None else "NO_Q53_CHAIN"
    q59_route_role = str(q59["route_role"]) if q59 is not None else "NO_Q59_ROUTE"
    handoff_edge_signal = int(bookid == "67" and q54_edge_status == "EDGE_CONFIRMED" and q36_contig_status == "EXACT_CONTIG_SHADOW_AVAILABLE")
    slot_target_signal = int(bookid == "2" and q53_chain_profile == "SUPPORTED_CONTEXT_TO_SLOT_CHAIN" and q54_edge_status == "EDGE_CONFIRMED")
    upstream_formula_signal = int(bookid == "35" and q36_contig_status == "EXACT_CONTIG_SHADOW_AVAILABLE" and q54_edge_status == "NO_DIRECT_EDGE_CONFIRMATION")
    control_block_signal = int(bookid in {"27", "35", "42"} and q54_edge_status != "EDGE_CONFIRMED")
    if handoff_edge_signal:
        verdict = "HANDOFF_EDGE_TARGET_SUPPORTS_ROLE"
    elif slot_target_signal:
        verdict = "SLOT_TARGET_RECEIVES_HANDOFF"
    elif bookid == "35":
        verdict = "UPSTREAM_FORMULA_ROUTE_NOT_EDGE_TARGET"
    elif bookid == "27":
        verdict = "HELDOUT_CONTEXT_ROUTE_BLOCKS_EDGE_REPLICATION"
    elif bookid == "42":
        verdict = "BOUNDARY_AUDIT_BLOCKS_EDGE_REPLICATION"
    else:
        verdict = "REQUIRES_REVIEW"
    return {
        "bookid": bookid,
        "book_class": book_class(bookid),
        "q54_phrase_profile": q54_profile,
        "q54_edge_status": q54_edge_status,
        "q36_contig_status": q36_contig_status,
        "q53_chain_profile": q53_chain_profile,
        "q59_route_role": q59_route_role,
        "handoff_edge_signal": handoff_edge_signal,
        "slot_target_signal": slot_target_signal,
        "upstream_formula_signal": upstream_formula_signal,
        "control_block_signal": control_block_signal,
        "role_verdict": verdict,
        "blocked_claim": "Functional edge role only; do not translate 67->2 as a sentence or fixed word sequence.",
        "evidence": {
            "q54": dict(q54) if q54 is not None else None,
            "q53": dict(q53) if q53 is not None else None,
            "q36": dict(q36) if q36 is not None else None,
            "q59": dict(q59) if q59 is not None else None,
        },
    }


def contrast_status(
    contrast: dict[str, str],
    classified: dict[str, dict[str, object]],
    edge: sqlite3.Row | None,
    q57_edge: sqlite3.Row,
    contig: sqlite3.Row,
) -> tuple[str, str, dict[str, object]]:
    if contrast["contrast_axis"] == "ACCEPTED_EDGE_VS_NO_EDGE":
        edge_ok = edge is not None and str(edge["gate_status"]) == "ORDERED_EDGE_ACCEPTED_NO_GLOSS"
        q57_ok = str(q57_edge["result_status"]) == "ACCEPT_SHADOW_CONTRAST_NO_GLOSS"
        passes = edge_ok and q57_ok
        observed = f"67->2_edge={str(edge['gate_status']) if edge is not None else 'MISSING'}; q57={q57_edge['result_status']}"
        evidence = {"chain_edge": dict(edge) if edge is not None else None, "q57_edge": dict(q57_edge)}
    elif contrast["contrast_axis"] == "EXACT_PATH_FORMULA_HANDOFF_SLOT":
        path_ok = str(contig["booksinorder"]) == "58->35->67->2"
        roles_ok = (
            classified["35"]["q59_route_role"] == "PRIMARY_UPSTREAM_FORMULA_CONTEXT_ROUTE"
            and classified["67"]["q59_route_role"] == "PRIMARY_HANDOFF_EDGE"
            and classified["2"]["q59_route_role"] == "PRIMARY_CONTEXT_TO_SLOT_TARGET"
        )
        passes = path_ok and roles_ok
        observed = f"path={contig['booksinorder']}; roles=35:{classified['35']['q59_route_role']} 67:{classified['67']['q59_route_role']} 2:{classified['2']['q59_route_role']}"
        evidence = {"contig": dict(contig), "path_books": {bookid: classified[bookid] for bookid in CONTEXT_PATH_BOOKS}}
    else:
        target = classified[contrast["target"]]
        control = classified[contrast["control"]]
        if contrast["contrast_axis"] == "HANDOFF_EDGE_VS_CONTEXT_HELDOUT":
            passes = int(target["handoff_edge_signal"]) == 1 and int(control["control_block_signal"]) == 1 and control["bookid"] == "27"
        elif contrast["contrast_axis"] == "HANDOFF_EDGE_VS_UPSTREAM_FORMULA":
            passes = int(target["handoff_edge_signal"]) == 1 and int(control["upstream_formula_signal"]) == 1
        elif contrast["contrast_axis"] == "HANDOFF_EDGE_VS_BOUNDARY_AUDIT":
            passes = int(target["handoff_edge_signal"]) == 1 and int(control["control_block_signal"]) == 1 and control["bookid"] == "42"
        else:
            passes = False
        observed = (
            f"{contrast['target']}={target['q54_edge_status']}/{target['q36_contig_status']}/{target['q59_route_role']} "
            f"vs {contrast['control']}={control['q54_edge_status']}/{control['q36_contig_status']}/{control['q59_route_role']}"
        )
        evidence = {"target": target, "control": control}
    return ("CONTRAST_PASSES_EDGE_HANDOFF_NO_GLOSS" if passes else "CONTRAST_REQUIRES_REVIEW", observed, evidence)


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q60 = latest_row(conn, "human_q60_component_role_promotion_queue_v1_runs")
    q59 = latest_row(conn, "human_q59_consolidated_shadow_backbone_v1_runs")
    q57 = latest_row(conn, "human_q57_execute_high_priority_contrasts_v1_runs")
    q54 = latest_row(conn, "human_q54_supported_chain_phrase_layer_v1_runs")
    q53 = latest_row(conn, "human_q53_c86_c68_chain_synthesis_v1_runs")
    q35 = latest_row(conn, "human_q35_contig_shadow_atlas_v1_runs")
    chain_probe = latest_row(conn, "c86_c68_naese_chain_probe_v1_runs")
    audit = latest_row(conn, "human_translation_completion_audit_v5_runs")
    q36_run_id = latest_item_run_id(conn, "human_q36_book_contig_shadow_integration_v1_items", "bookid")

    candidate = q60_candidate(conn, int(q60["run_id"]))
    q57_edge = load_q57_edge_result(conn, int(q57["run_id"]))
    contig = load_contig(conn, int(q35["run_id"]))
    chain_items = load_chain_items(conn, int(chain_probe["run_id"]))
    edge = chain_items.get(("naese_edge", "67->2"))
    q54_books = load_by_book(conn, "human_q54_supported_chain_phrase_layer_v1_books", int(q54["run_id"]))
    q53_books = load_by_book(conn, "human_q53_c86_c68_chain_synthesis_v1_books", int(q53["run_id"]))
    q36_books = load_by_book(conn, "human_q36_book_contig_shadow_integration_v1_items", q36_run_id)
    q59_books = load_by_book(conn, "human_q59_consolidated_shadow_backbone_v1_books", int(q59["run_id"]))

    all_books = ["67", "2", *CONTROL_BOOKS]
    classified = {
        bookid: classify_book(bookid, q54_books, q53_books, q36_books, q59_books)
        for bookid in all_books
    }

    contrast_rows = []
    for contrast in CONTRASTS:
        status, observed, evidence = contrast_status(contrast, classified, edge, q57_edge, contig)
        contrast_rows.append({**contrast, "observed_difference": observed, "contrast_status": status, "evidence": evidence})

    exact_path_book_count = sum(1 for bookid in CONTEXT_PATH_BOOKS if classified[bookid]["q36_contig_status"] == "EXACT_CONTIG_SHADOW_AVAILABLE")
    accepted_edge_count = 1 if edge is not None and str(edge["gate_status"]) == "ORDERED_EDGE_ACCEPTED_NO_GLOSS" else 0
    passing_contrast_count = sum(1 for row in contrast_rows if row["contrast_status"] == "CONTRAST_PASSES_EDGE_HANDOFF_NO_GLOSS")
    functional_edge_accept_count = 1 if accepted_edge_count == 1 and passing_contrast_count == len(CONTRASTS) else 0
    phrase_path_accept_count = 1 if exact_path_book_count == 3 and functional_edge_accept_count == 1 else 0
    lexical_ready_count = 0
    direct_gloss_count = 0
    canonical_promotion_allowed_count = 0
    edge_human_version = (
        "67->2 handoff edge role: exact contig evidence and accepted edge status support Book 67 as the handoff into Book 2's slot target. "
        "Books 27, 35, and 42 do not reproduce the same continuity. This is an edge/phrase-path role only, not sentence plaintext."
    )
    decision = (
        "Q64_EDGE_67_2_HANDOFF_ROLE_ACCEPT_FUNCTIONAL_EDGE_NO_GLOSS"
        if len(contrast_rows) == 5
        and passing_contrast_count == 5
        and exact_path_book_count == 3
        and accepted_edge_count == 1
        and functional_edge_accept_count == 1
        and phrase_path_accept_count == 1
        and int(q60["lexical_ready_count"]) == 0
        and int(audit["promoted_gloss_count"]) == 0
        and lexical_ready_count == 0
        and direct_gloss_count == 0
        and canonical_promotion_allowed_count == 0
        else "Q64_EDGE_67_2_HANDOFF_ROLE_REQUIRES_REVIEW"
    )
    payload = {
        "question": "Can the 67->2 edge be accepted as a functional handoff role?",
        "answer": "Yes, as a functional phrase-edge role only; lexical and sentence promotion remain blocked.",
        "edge_human_version": edge_human_version,
        "candidate": dict(candidate),
        "blocked_use": "Do not translate 67->2 as a sentence or fixed lexical sequence.",
        "next_action": "Run the remaining Q60 target: Book27 payload/context hold as a heldout stop/continue role.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q64_edge_67_2_handoff_role_contrast_v1_runs (
                created_at, decision, q60_run_id, q59_run_id, q57_run_id,
                q54_run_id, q53_run_id, q35_run_id, q36_run_id,
                chain_probe_run_id, completion_audit_run_id, target_book_count,
                control_book_count, exact_path_book_count, accepted_edge_count,
                contrast_count, passing_contrast_count, functional_edge_accept_count,
                phrase_path_accept_count, lexical_ready_count, direct_gloss_count,
                canonical_promotion_allowed_count, edge_human_version, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                int(q60["run_id"]),
                int(q59["run_id"]),
                int(q57["run_id"]),
                int(q54["run_id"]),
                int(q53["run_id"]),
                int(q35["run_id"]),
                q36_run_id,
                int(chain_probe["run_id"]),
                int(audit["run_id"]),
                len(TARGET_BOOKS),
                len(CONTROL_BOOKS),
                exact_path_book_count,
                accepted_edge_count,
                len(contrast_rows),
                passing_contrast_count,
                functional_edge_accept_count,
                phrase_path_accept_count,
                lexical_ready_count,
                direct_gloss_count,
                canonical_promotion_allowed_count,
                edge_human_version,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q64_edge_67_2_handoff_role_contrast_v1_books (
                run_id, bookid, book_class, q54_phrase_profile,
                q54_edge_status, q36_contig_status, q53_chain_profile,
                q59_route_role, handoff_edge_signal, slot_target_signal,
                upstream_formula_signal, control_block_signal, role_verdict,
                blocked_claim, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    item["bookid"],
                    item["book_class"],
                    item["q54_phrase_profile"],
                    item["q54_edge_status"],
                    item["q36_contig_status"],
                    item["q53_chain_profile"],
                    item["q59_route_role"],
                    int(item["handoff_edge_signal"]),
                    int(item["slot_target_signal"]),
                    int(item["upstream_formula_signal"]),
                    int(item["control_block_signal"]),
                    item["role_verdict"],
                    item["blocked_claim"],
                    j(item["evidence"]),
                )
                for item in classified.values()
            ],
        )
        conn.executemany(
            """
            INSERT INTO human_q64_edge_67_2_handoff_role_contrast_v1_contrasts (
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

    print(
        j(
            {
                "run_id": run_id,
                "decision": decision,
                "target_book_count": len(TARGET_BOOKS),
                "control_book_count": len(CONTROL_BOOKS),
                "exact_path_book_count": exact_path_book_count,
                "accepted_edge_count": accepted_edge_count,
                "contrast_count": len(contrast_rows),
                "passing_contrast_count": passing_contrast_count,
                "functional_edge_accept_count": functional_edge_accept_count,
                "phrase_path_accept_count": phrase_path_accept_count,
                "lexical_ready_count": lexical_ready_count,
                "direct_gloss_count": direct_gloss_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
            }
        )
    )


if __name__ == "__main__":
    main()
