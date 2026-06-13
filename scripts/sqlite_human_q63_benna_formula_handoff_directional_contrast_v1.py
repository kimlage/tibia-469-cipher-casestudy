#!/usr/bin/env python3
"""Q63: directional contrast for the BENNA formula-handoff role."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

TARGET_BOOKS = ["35", "10"]
CONTROL_BOOKS = ["5", "31", "57"]
SUPPORT_EDGES = ["58->35", "69->35", "47->35"]

CONTRASTS = [
    {
        "contrast_id": "Q63_PAIR_35_VS_5",
        "target_book": "35",
        "control_book": "5",
        "contrast_axis": "FORMULA_TO_CONTEXT_VS_SLOT_TO_FORMULA",
        "expected_difference": "Book 35 is BENNA formula handoff into context; Book 5 is slot-to-BENNA residual/template control.",
    },
    {
        "contrast_id": "Q63_PAIR_35_VS_31",
        "target_book": "35",
        "control_book": "31",
        "contrast_axis": "FORMULA_HANDOFF_VS_PHASE_CONTEXT",
        "expected_difference": "Book 35 has BENNA formula handoff; Book 31 has phase/context without BENNA formula evidence.",
    },
    {
        "contrast_id": "Q63_PAIR_35_VS_57",
        "target_book": "35",
        "control_book": "57",
        "contrast_axis": "FORMULA_HANDOFF_VS_PHASE_CONTEXT",
        "expected_difference": "Book 35 has BENNA formula handoff; Book 57 has phase/context without BENNA formula evidence.",
    },
    {
        "contrast_id": "Q63_PAIR_10_VS_35",
        "target_book": "10",
        "control_book": "35",
        "contrast_axis": "HELDOUT_FORMULA_ROUTE_VS_PRIMARY_BACKBONE",
        "expected_difference": "Book 10 shares formula handoff mechanics but remains heldout; Book 35 is primary contig backbone.",
    },
    {
        "contrast_id": "Q63_PAIR_10_VS_31",
        "target_book": "10",
        "control_book": "31",
        "contrast_axis": "HELDOUT_FORMULA_HANDOFF_VS_PHASE_CONTEXT",
        "expected_difference": "Book 10 has heldout BENNA formula handoff; Book 31 is non-formula phase/context control.",
    },
]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q63_benna_formula_handoff_directional_contrast_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q60_run_id INTEGER NOT NULL,
            q59_run_id INTEGER NOT NULL,
            q53_run_id INTEGER NOT NULL,
            q50_run_id INTEGER NOT NULL,
            benna_bridge_run_id INTEGER NOT NULL,
            benna_role_run_id INTEGER NOT NULL,
            benna_semantic_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            target_book_count INTEGER NOT NULL,
            control_book_count INTEGER NOT NULL,
            clean_formula_target_count INTEGER NOT NULL,
            residual_control_count INTEGER NOT NULL,
            non_formula_control_count INTEGER NOT NULL,
            support_edge_count INTEGER NOT NULL,
            contrast_count INTEGER NOT NULL,
            passing_contrast_count INTEGER NOT NULL,
            functional_role_accept_count INTEGER NOT NULL,
            lexical_ready_count INTEGER NOT NULL,
            direct_gloss_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            role_human_version TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q63_benna_formula_handoff_directional_contrast_v1_books (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            book_class TEXT NOT NULL,
            q50_speech_act TEXT NOT NULL,
            q53_chain_profile TEXT NOT NULL,
            q59_route_role TEXT NOT NULL,
            benna_bridge_decision TEXT NOT NULL,
            benna_functional_class TEXT NOT NULL,
            benna_role_status TEXT NOT NULL,
            benna_dominant_role TEXT NOT NULL,
            formula_handoff_signal INTEGER NOT NULL,
            residual_or_template_signal INTEGER NOT NULL,
            non_formula_control_signal INTEGER NOT NULL,
            role_verdict TEXT NOT NULL,
            blocked_claim TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        );

        CREATE TABLE IF NOT EXISTS human_q63_benna_formula_handoff_directional_contrast_v1_contrasts (
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

        CREATE TABLE IF NOT EXISTS human_q63_benna_formula_handoff_directional_contrast_v1_edges (
            run_id INTEGER NOT NULL,
            edge_id TEXT NOT NULL,
            status TEXT NOT NULL,
            dominant_role TEXT NOT NULL,
            interpretation TEXT NOT NULL,
            edge_use TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, edge_id)
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


def load_benna_role_items(conn: sqlite3.Connection, run_id: int) -> dict[tuple[str, str], sqlite3.Row]:
    rows = conn.execute(
        "SELECT * FROM benna_role_propagation_audit_v1_items WHERE run_id=?",
        (run_id,),
    ).fetchall()
    return {(str(row["item_type"]), str(row["item_id"])): row for row in rows}


def load_semantic_best(conn: sqlite3.Connection, run_id: int) -> sqlite3.Row:
    row = conn.execute(
        """
        SELECT *
        FROM benna_semantic_function_probe_v1_items
        WHERE run_id=? AND hypothesis_id='BENNA_AS_FORMULAIC_FRAME_OPERATOR'
        """,
        (run_id,),
    ).fetchone()
    if row is None:
        raise RuntimeError("missing BENNA_AS_FORMULAIC_FRAME_OPERATOR semantic row")
    return row


def q60_candidate(conn: sqlite3.Connection, q60_run_id: int) -> sqlite3.Row:
    row = conn.execute(
        """
        SELECT *
        FROM human_q60_component_role_promotion_queue_v1_candidates
        WHERE run_id=? AND candidate_id='Q60_C03_BENNA_FORMULA_HANDOFF_ROLE'
        """,
        (q60_run_id,),
    ).fetchone()
    if row is None:
        raise RuntimeError("missing Q60 BENNA formula-handoff candidate")
    return row


def book_class(bookid: str) -> str:
    if bookid == "35":
        return "PRIMARY_FORMULA_HANDOFF_TARGET"
    if bookid == "10":
        return "HELDOUT_FORMULA_HANDOFF_TARGET"
    if bookid == "5":
        return "RESIDUAL_SLOT_TO_FORMULA_CONTROL"
    return "NON_FORMULA_PHASE_CONTEXT_CONTROL"


def classify_book(
    bookid: str,
    q50_books: dict[str, sqlite3.Row],
    q53_books: dict[str, sqlite3.Row],
    q59_books: dict[str, sqlite3.Row],
    benna_bridge_books: dict[str, sqlite3.Row],
    benna_role_items: dict[tuple[str, str], sqlite3.Row],
) -> dict[str, object]:
    q50 = q50_books[bookid]
    q53 = q53_books[bookid]
    q59 = q59_books.get(bookid)
    bridge = benna_bridge_books.get(bookid)
    role = benna_role_items.get(("book", bookid))
    bridge_decision = str(bridge["decision"]) if bridge is not None else "NO_BENNA_BRIDGE_ROW"
    functional_class = str(bridge["functional_class"]) if bridge is not None else "NO_BENNA_FUNCTIONAL_CLASS"
    role_status = str(role["status"]) if role is not None else "NO_BENNA_ROLE_ROW"
    dominant_role = str(role["dominant_role"]) if role is not None else "NO_BENNA_ROLE"
    speech = str(q50["q36_likely_speech_act"])
    formula_handoff_signal = int(
        bridge_decision == "BENNA_FORMULA_BRIDGE_CLEAN_WITH_TAIL_NO_GLOSS"
        and role_status == "HANDOFF_CONTEXT_ALIVE"
        and dominant_role == "HANDOFF_CONTEXT"
        and str(q53["chain_profile"]).startswith("SUPPORTED_CONTEXT")
    )
    residual_or_template_signal = int(
        "RESIDUAL" in bridge_decision
        or "VARIANT" in bridge_decision
        or dominant_role == "TEMPLATE_HEAD"
        or role_status == "TEMPLATE_HEAD_ALIVE"
    )
    non_formula_control_signal = int(bridge is None and role is None and "BENNA" not in speech.upper())
    if formula_handoff_signal and bookid == "35":
        verdict = "PRIMARY_BENNA_FORMULA_HANDOFF_SUPPORTS_ROLE"
    elif formula_handoff_signal and bookid == "10":
        verdict = "HELDOUT_BENNA_FORMULA_HANDOFF_SUPPORTS_MODERATE_ROLE"
    elif residual_or_template_signal:
        verdict = "RESIDUAL_OR_TEMPLATE_CONTROL_BLOCKS_HANDOFF_PROMOTION"
    elif non_formula_control_signal:
        verdict = "NON_FORMULA_CONTROL_BLOCKS_HANDOFF_PROMOTION"
    else:
        verdict = "REQUIRES_REVIEW"
    return {
        "bookid": bookid,
        "book_class": book_class(bookid),
        "q50_speech_act": speech,
        "q53_chain_profile": str(q53["chain_profile"]),
        "q59_route_role": str(q59["route_role"]) if q59 is not None else "NO_Q59_ROUTE",
        "benna_bridge_decision": bridge_decision,
        "benna_functional_class": functional_class,
        "benna_role_status": role_status,
        "benna_dominant_role": dominant_role,
        "formula_handoff_signal": formula_handoff_signal,
        "residual_or_template_signal": residual_or_template_signal,
        "non_formula_control_signal": non_formula_control_signal,
        "role_verdict": verdict,
        "blocked_claim": "Functional formula-handoff role only; no BENNA, formula, body, or handoff word gloss.",
        "evidence": {
            "q50": dict(q50),
            "q53": dict(q53),
            "q59": dict(q59) if q59 is not None else None,
            "benna_bridge": dict(bridge) if bridge is not None else None,
            "benna_role": dict(role) if role is not None else None,
        },
    }


def contrast_status(contrast: dict[str, str], classified: dict[str, dict[str, object]]) -> tuple[str, str]:
    target = classified[contrast["target_book"]]
    control = classified[contrast["control_book"]]
    target_handoff = int(target["formula_handoff_signal"]) == 1
    if contrast["contrast_axis"] == "HELDOUT_FORMULA_ROUTE_VS_PRIMARY_BACKBONE":
        passes = (
            target_handoff
            and int(control["formula_handoff_signal"]) == 1
            and str(target["book_class"]) == "HELDOUT_FORMULA_HANDOFF_TARGET"
            and str(control["book_class"]) == "PRIMARY_FORMULA_HANDOFF_TARGET"
        )
    elif contrast["contrast_axis"] == "FORMULA_TO_CONTEXT_VS_SLOT_TO_FORMULA":
        passes = target_handoff and int(control["residual_or_template_signal"]) == 1
    else:
        passes = target_handoff and int(control["non_formula_control_signal"]) == 1
    observed = (
        f"{contrast['target_book']}={target['benna_bridge_decision']}/{target['benna_role_status']}/{target['q53_chain_profile']} "
        f"vs {contrast['control_book']}={control['benna_bridge_decision']}/{control['benna_role_status']}/{control['q53_chain_profile']}"
    )
    return ("CONTRAST_PASSES_DIRECTIONAL_BENNA_ROLE_NO_GLOSS" if passes else "CONTRAST_REQUIRES_REVIEW", observed)


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
    benna_bridge_run_id = latest_item_run_id(conn, "benna_formula_bridge_gate_items", "bookid")
    benna_role_run_id = latest_item_run_id(conn, "benna_role_propagation_audit_v1_items", "item_id")
    benna_semantic_run_id = latest_item_run_id(conn, "benna_semantic_function_probe_v1_items", "hypothesis_id")

    candidate = q60_candidate(conn, int(q60["run_id"]))
    semantic_best = load_semantic_best(conn, benna_semantic_run_id)
    q59_books = load_by_book(conn, "human_q59_consolidated_shadow_backbone_v1_books", int(q59["run_id"]))
    q53_books = load_by_book(conn, "human_q53_c86_c68_chain_synthesis_v1_books", int(q53["run_id"]))
    q50_books = load_by_book(conn, "human_q50_c68_book_synthesis_v1_books", int(q50["run_id"]))
    benna_bridge_books = load_by_book(conn, "benna_formula_bridge_gate_items", benna_bridge_run_id)
    benna_role_items = load_benna_role_items(conn, benna_role_run_id)

    all_books = TARGET_BOOKS + CONTROL_BOOKS
    classified = {
        bookid: classify_book(bookid, q50_books, q53_books, q59_books, benna_bridge_books, benna_role_items)
        for bookid in all_books
    }

    contrast_rows = []
    for contrast in CONTRASTS:
        status, observed = contrast_status(contrast, classified)
        contrast_rows.append({**contrast, "observed_difference": observed, "contrast_status": status})

    edge_rows = []
    for edge_id in SUPPORT_EDGES:
        row = benna_role_items.get(("edge", edge_id))
        if row is not None:
            edge_rows.append(row)

    clean_formula_target_count = sum(1 for bookid in TARGET_BOOKS if int(classified[bookid]["formula_handoff_signal"]) == 1)
    residual_control_count = sum(1 for bookid in CONTROL_BOOKS if int(classified[bookid]["residual_or_template_signal"]) == 1)
    non_formula_control_count = sum(1 for bookid in CONTROL_BOOKS if int(classified[bookid]["non_formula_control_signal"]) == 1)
    support_edge_count = sum(1 for row in edge_rows if str(row["status"]) == "COMPATIBLE_EDGE")
    passing_contrast_count = sum(1 for row in contrast_rows if row["contrast_status"] == "CONTRAST_PASSES_DIRECTIONAL_BENNA_ROLE_NO_GLOSS")
    functional_role_accept_count = 1 if clean_formula_target_count == 2 and passing_contrast_count == len(CONTRASTS) and support_edge_count >= 2 else 0
    lexical_ready_count = 0
    direct_gloss_count = 0
    canonical_promotion_allowed_count = 0
    role_human_version = (
        "BENNA formula-handoff role: Books 35 and 10 carry clean BENNA formula bridge with handoff-context role, "
        "while Book 5 is residual/template slot-to-formula control and Books 31/57 are non-formula phase controls. "
        "The role is functionally accepted for shadow work, but no BENNA word meaning is promoted."
    )
    decision = (
        "Q63_BENNA_FORMULA_HANDOFF_DIRECTIONAL_CONTRAST_ACCEPT_FUNCTIONAL_ROLE_NO_GLOSS"
        if len(contrast_rows) == 5
        and passing_contrast_count == 5
        and clean_formula_target_count == 2
        and residual_control_count == 1
        and non_formula_control_count == 2
        and support_edge_count >= 2
        and functional_role_accept_count == 1
        and str(semantic_best["status"]) == "BEST"
        and int(q60["lexical_ready_count"]) == 0
        and int(audit["promoted_gloss_count"]) == 0
        and lexical_ready_count == 0
        and direct_gloss_count == 0
        and canonical_promotion_allowed_count == 0
        else "Q63_BENNA_FORMULA_HANDOFF_DIRECTIONAL_CONTRAST_REQUIRES_REVIEW"
    )
    payload = {
        "question": "Can BENNA formula-handoff be accepted as a functional role through directional contrasts?",
        "answer": "Yes, as a functional shadow role only; lexical promotion remains blocked.",
        "role_human_version": role_human_version,
        "candidate": dict(candidate),
        "semantic_best": dict(semantic_best),
        "blocked_use": "Do not translate BENNA, formula, body, or handoff as words.",
        "next_action": "Run Q60_C04 edge 67->2 handoff as the next phrase-edge role target.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q63_benna_formula_handoff_directional_contrast_v1_runs (
                created_at, decision, q60_run_id, q59_run_id, q53_run_id,
                q50_run_id, benna_bridge_run_id, benna_role_run_id,
                benna_semantic_run_id, completion_audit_run_id,
                target_book_count, control_book_count, clean_formula_target_count,
                residual_control_count, non_formula_control_count,
                support_edge_count, contrast_count, passing_contrast_count,
                functional_role_accept_count, lexical_ready_count,
                direct_gloss_count, canonical_promotion_allowed_count,
                role_human_version, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                int(q60["run_id"]),
                int(q59["run_id"]),
                int(q53["run_id"]),
                int(q50["run_id"]),
                benna_bridge_run_id,
                benna_role_run_id,
                benna_semantic_run_id,
                int(audit["run_id"]),
                len(TARGET_BOOKS),
                len(CONTROL_BOOKS),
                clean_formula_target_count,
                residual_control_count,
                non_formula_control_count,
                support_edge_count,
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
            INSERT INTO human_q63_benna_formula_handoff_directional_contrast_v1_books (
                run_id, bookid, book_class, q50_speech_act, q53_chain_profile,
                q59_route_role, benna_bridge_decision, benna_functional_class,
                benna_role_status, benna_dominant_role, formula_handoff_signal,
                residual_or_template_signal, non_formula_control_signal,
                role_verdict, blocked_claim, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    item["bookid"],
                    item["book_class"],
                    item["q50_speech_act"],
                    item["q53_chain_profile"],
                    item["q59_route_role"],
                    item["benna_bridge_decision"],
                    item["benna_functional_class"],
                    item["benna_role_status"],
                    item["benna_dominant_role"],
                    int(item["formula_handoff_signal"]),
                    int(item["residual_or_template_signal"]),
                    int(item["non_formula_control_signal"]),
                    item["role_verdict"],
                    item["blocked_claim"],
                    j(item["evidence"]),
                )
                for item in classified.values()
            ],
        )
        conn.executemany(
            """
            INSERT INTO human_q63_benna_formula_handoff_directional_contrast_v1_contrasts (
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
        conn.executemany(
            """
            INSERT INTO human_q63_benna_formula_handoff_directional_contrast_v1_edges (
                run_id, edge_id, status, dominant_role, interpretation,
                edge_use, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    str(row["item_id"]),
                    str(row["status"]),
                    str(row["dominant_role"]),
                    str(row["interpretation"]),
                    "Directional support for formula/display head into handoff context; no lexical gloss.",
                    j(dict(row)),
                )
                for row in edge_rows
            ],
        )

    print(
        j(
            {
                "run_id": run_id,
                "decision": decision,
                "target_book_count": len(TARGET_BOOKS),
                "control_book_count": len(CONTROL_BOOKS),
                "clean_formula_target_count": clean_formula_target_count,
                "residual_control_count": residual_control_count,
                "non_formula_control_count": non_formula_control_count,
                "support_edge_count": support_edge_count,
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
