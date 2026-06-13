#!/usr/bin/env python3
"""Q59: consolidate the fully tested Q54/Q55/Q56 route into a shadow backbone."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

BOOK_ORDER = ["35", "67", "2", "10", "27"]

BOOK_RENDERINGS = {
    "35": {
        "route_role": "PRIMARY_UPSTREAM_FORMULA_CONTEXT_ROUTE",
        "route_position": 1,
        "route_class": "PRIMARY_BACKBONE",
        "shadow_version_pt": "O corpo da formula encaminha o contexto para o caminho classificador.",
        "shadow_version_en": "The formula body hands context toward the classifier path.",
        "confidence_band": "STRONG_SHADOW",
        "accepted_test_ids": ["Q56_T03_FORMULA_TO_CONTEXT_CONTIG"],
        "residual_risk": "BENNA/formula-body wording is functional only; no BENNA lexical gloss is promoted.",
        "next_validation": "Test 35->67 continuity as a phrase transition before any broader book-level prose.",
    },
    "67": {
        "route_role": "PRIMARY_HANDOFF_EDGE",
        "route_position": 2,
        "route_class": "PRIMARY_BACKBONE",
        "shadow_version_pt": "A passagem de contexto prepara o slot classificador.",
        "shadow_version_en": "The context handoff prepares the classifier slot.",
        "confidence_band": "STRONG_SHADOW",
        "accepted_test_ids": ["Q56_T02_67_TO_2_HANDOFF_EDGE"],
        "residual_risk": "The handoff is an edge role only; Book 67 is not translated as a standalone sentence.",
        "next_validation": "Keep 67->2 as the immediate edge control for any classifier-slot synthesis.",
    },
    "2": {
        "route_role": "PRIMARY_CONTEXT_TO_SLOT_TARGET",
        "route_position": 3,
        "route_class": "PRIMARY_BACKBONE",
        "shadow_version_pt": "O contexto selecionado entra no slot classificador.",
        "shadow_version_en": "The selected context is handed into the classifier slot.",
        "confidence_band": "STRONG_SHADOW",
        "accepted_test_ids": ["Q56_T01_CONTEXT_TO_SLOT_CLASSIFIER", "Q56_T02_67_TO_2_HANDOFF_EDGE"],
        "residual_risk": "Classifier/slot remains a functional label; no C68/NAESE component gloss is promoted.",
        "next_validation": "Run a later NAESE/C68 slot-control audit before any canonical wording.",
    },
    "10": {
        "route_role": "HELDOUT_FORMULA_HANDOFF_VARIANT",
        "route_position": 4,
        "route_class": "HELDOUT_VARIANT",
        "shadow_version_pt": "A formula faz a passagem para o roteamento de contexto.",
        "shadow_version_en": "The formula hands off into context routing.",
        "confidence_band": "MODERATE_SHADOW",
        "accepted_test_ids": ["Q56_T04_FORMULA_HANDOFF_HELDOUT"],
        "residual_risk": "Exact 35->67->2 continuity is absent, so Book 10 cannot be primary backbone.",
        "next_validation": "Use as a heldout comparison against Book 35, not as the route spine.",
    },
    "27": {
        "route_role": "HELDOUT_PAYLOAD_CONTEXT_HOLD",
        "route_position": 5,
        "route_class": "HELDOUT_VARIANT",
        "shadow_version_pt": "O corredor de carga mantem aberto o contexto selecionado.",
        "shadow_version_en": "The payload corridor holds the selected context open.",
        "confidence_band": "MODERATE_SHADOW",
        "accepted_test_ids": ["Q56_T05_PAYLOAD_CONTEXT_HOLD"],
        "residual_risk": "Payload/context-hold is not command, dead, soul, necromancy, or transformation plaintext.",
        "next_validation": "Use as a heldout stop/continue contrast for payload routes.",
    },
}


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q59_consolidated_shadow_backbone_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q54_run_id INTEGER NOT NULL,
            q55_run_id INTEGER NOT NULL,
            q56_run_id INTEGER NOT NULL,
            q57_run_id INTEGER NOT NULL,
            q58_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            phrase_book_count INTEGER NOT NULL,
            primary_backbone_count INTEGER NOT NULL,
            heldout_variant_count INTEGER NOT NULL,
            accepted_shadow_phrase_count INTEGER NOT NULL,
            accepted_firewall_count INTEGER NOT NULL,
            source_anchor_count INTEGER NOT NULL,
            q56_queue_completion_count INTEGER NOT NULL,
            direct_gloss_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            consolidated_shadow_pt TEXT NOT NULL,
            consolidated_shadow_en TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q59_consolidated_shadow_backbone_v1_books (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            route_position INTEGER NOT NULL,
            route_role TEXT NOT NULL,
            route_class TEXT NOT NULL,
            confidence_band TEXT NOT NULL,
            shadow_version_pt TEXT NOT NULL,
            shadow_version_en TEXT NOT NULL,
            accepted_test_ids_json TEXT NOT NULL,
            source_ids_json TEXT NOT NULL,
            residual_risk TEXT NOT NULL,
            next_validation TEXT NOT NULL,
            promotion_status TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        );

        CREATE TABLE IF NOT EXISTS human_q59_consolidated_shadow_backbone_v1_risks (
            run_id INTEGER NOT NULL,
            risk_id TEXT NOT NULL,
            risk_class TEXT NOT NULL,
            applies_to_books_json TEXT NOT NULL,
            risk_statement TEXT NOT NULL,
            mitigation TEXT NOT NULL,
            promotion_blocker INTEGER NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, risk_id)
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


def load_results(conn: sqlite3.Connection, table: str, run_id: int) -> dict[str, sqlite3.Row]:
    rows = conn.execute(f"SELECT * FROM {table} WHERE run_id=?", (run_id,)).fetchall()
    return {str(row["test_id"]): row for row in rows}


def load_sources(conn: sqlite3.Connection, q55_run_id: int) -> dict[str, sqlite3.Row]:
    rows = conn.execute(
        "SELECT * FROM human_q55_source_parallel_audit_q54_v1_sources WHERE run_id=?",
        (q55_run_id,),
    ).fetchall()
    return {str(row["source_id"]): row for row in rows}


def result_for_tests(test_ids: list[str], q57_results: dict[str, sqlite3.Row], q58_results: dict[str, sqlite3.Row]) -> dict[str, object]:
    output: dict[str, object] = {}
    for test_id in test_ids:
        row = q57_results.get(test_id) or q58_results.get(test_id)
        if row is None:
            raise RuntimeError(f"missing accepted contrast result: {test_id}")
        output[test_id] = dict(row)
    return output


def build_risks(
    q54: sqlite3.Row,
    q55: sqlite3.Row,
    q56: sqlite3.Row,
    q57: sqlite3.Row,
    q58: sqlite3.Row,
    audit: sqlite3.Row,
) -> list[dict[str, object]]:
    return [
        {
            "risk_id": "Q59_RISK_FUNCTIONAL_LABELS_NOT_WORDS",
            "risk_class": "COMPONENT_GLOSS_BLOCKER",
            "applies_to_books": ["2", "10", "27", "35", "67"],
            "risk_statement": "Terms like formula, context, payload, handoff, slot, and classifier are functional route labels, not decoded Bonelord words.",
            "mitigation": "Keep direct_gloss_count and canonical promotion counters at zero until component-level contrasts pass.",
            "promotion_blocker": 1,
            "evidence": {
                "q54": dict(q54),
                "q55": dict(q55),
                "q56": dict(q56),
                "q57": dict(q57),
                "q58": dict(q58),
            },
        },
        {
            "risk_id": "Q59_RISK_SOURCE_REGISTER_NOT_DICTIONARY",
            "risk_class": "SOURCE_OVERREACH_BLOCKER",
            "applies_to_books": ["2", "10", "27", "35", "67"],
            "risk_statement": "Mathemagic, ritual, research, control, and transformation sources constrain register only; they do not give a dictionary.",
            "mitigation": "Preserve Q58 firewall status and re-run it before any new phrase synthesis.",
            "promotion_blocker": 1,
            "evidence": {"q55": dict(q55), "q58": dict(q58)},
        },
        {
            "risk_id": "Q59_RISK_CANONICAL_UNSOLVED",
            "risk_class": "CANONICAL_STATUS_BLOCKER",
            "applies_to_books": ["0-69"],
            "risk_statement": "The human-shadow atlas has 70/70 coverage, but no promoted gloss exists.",
            "mitigation": "Report this as a tested human route only while completion audit promoted_gloss_count remains zero.",
            "promotion_blocker": 1,
            "evidence": {"completion_audit": dict(audit)},
        },
    ]


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q54 = latest_row(conn, "human_q54_supported_chain_phrase_layer_v1_runs")
    q55 = latest_row(conn, "human_q55_source_parallel_audit_q54_v1_runs")
    q56 = latest_row(conn, "human_q56_source_linked_contrast_queue_v1_runs")
    q57 = latest_row(conn, "human_q57_execute_high_priority_contrasts_v1_runs")
    q58 = latest_row(conn, "human_q58_execute_remaining_contrasts_firewall_v1_runs")
    audit = latest_row(conn, "human_translation_completion_audit_v5_runs")

    q55_books = load_by_book(conn, "human_q55_source_parallel_audit_q54_v1_books", int(q55["run_id"]))
    q57_results = load_results(conn, "human_q57_execute_high_priority_contrasts_v1_results", int(q57["run_id"]))
    q58_results = load_results(conn, "human_q58_execute_remaining_contrasts_firewall_v1_results", int(q58["run_id"]))
    sources = load_sources(conn, int(q55["run_id"]))

    missing_books = [bookid for bookid in BOOK_ORDER if bookid not in q55_books]
    if missing_books:
        raise RuntimeError(f"missing Q55 phrase books: {missing_books}")

    prepared_books = []
    for bookid in BOOK_ORDER:
        rendering = BOOK_RENDERINGS[bookid]
        source_ids = json.loads(str(q55_books[bookid]["source_ids_json"]))
        prepared_books.append(
            {
                "bookid": bookid,
                **rendering,
                "source_ids": source_ids,
                "promotion_status": "HUMAN_SHADOW_ACCEPTED_NOT_CANONICAL",
                "evidence": {
                    "q55_book": dict(q55_books[bookid]),
                    "accepted_results": result_for_tests(rendering["accepted_test_ids"], q57_results, q58_results),
                    "sources": {source_id: dict(sources[source_id]) for source_id in source_ids},
                },
            }
        )

    primary_backbone_count = sum(1 for item in prepared_books if item["route_class"] == "PRIMARY_BACKBONE")
    heldout_variant_count = sum(1 for item in prepared_books if item["route_class"] == "HELDOUT_VARIANT")
    accepted_shadow_phrase_count = int(q57["accepted_shadow_test_count"]) + int(q58["accepted_shadow_test_count"])
    accepted_firewall_count = int(q58["accepted_firewall_test_count"])
    source_anchor_count = len(sources)
    q56_queue_completion_count = int(q58["q56_queue_completion_count"])
    direct_gloss_count = 0
    canonical_promotion_allowed_count = 0
    consolidated_shadow_pt = (
        "Rota humana testada: a formula encaminha o contexto, a passagem prepara o slot classificador, "
        "e o contexto selecionado entra no slot. Book 10 fica como variante moderada de formula->contexto; "
        "Book 27 fica como variante moderada de corredor payload/contexto."
    )
    consolidated_shadow_en = (
        "Tested human route: the formula routes context, the handoff prepares the classifier slot, "
        "and the selected context enters the slot. Book 10 remains a moderate formula->context variant; "
        "Book 27 remains a moderate payload/context corridor variant."
    )
    risks = build_risks(q54, q55, q56, q57, q58, audit)
    promotion_blocker_count = sum(int(risk["promotion_blocker"]) for risk in risks)

    decision = (
        "Q59_CONSOLIDATED_SHADOW_BACKBONE_READY_5_PHRASES_NO_GLOSS"
        if len(prepared_books) == 5
        and primary_backbone_count == 3
        and heldout_variant_count == 2
        and accepted_shadow_phrase_count == 5
        and accepted_firewall_count == 1
        and source_anchor_count == 8
        and q56_queue_completion_count == 6
        and promotion_blocker_count == 3
        and int(q55["direct_gloss_count"]) == 0
        and int(q58["direct_gloss_count"]) == 0
        and int(audit["promoted_gloss_count"]) == 0
        and direct_gloss_count == 0
        and canonical_promotion_allowed_count == 0
        else "Q59_CONSOLIDATED_SHADOW_BACKBONE_REQUIRES_REVIEW"
    )
    payload = {
        "question": "What is the consolidated tested human route after Q54-Q58?",
        "answer": "A five-phrase shadow backbone with three primary steps and two moderate heldouts, all source-anchored and firewall-protected.",
        "consolidated_shadow_pt": consolidated_shadow_pt,
        "consolidated_shadow_en": consolidated_shadow_en,
        "blocked_use": "Do not report as canonical translation; do not promote component glosses.",
        "next_action": "Use this backbone to look for exact phrase-continuity evidence or component-level controls.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q59_consolidated_shadow_backbone_v1_runs (
                created_at, decision, q54_run_id, q55_run_id, q56_run_id,
                q57_run_id, q58_run_id, completion_audit_run_id,
                phrase_book_count, primary_backbone_count, heldout_variant_count,
                accepted_shadow_phrase_count, accepted_firewall_count,
                source_anchor_count, q56_queue_completion_count,
                direct_gloss_count, canonical_promotion_allowed_count,
                consolidated_shadow_pt, consolidated_shadow_en, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                int(q54["run_id"]),
                int(q55["run_id"]),
                int(q56["run_id"]),
                int(q57["run_id"]),
                int(q58["run_id"]),
                int(audit["run_id"]),
                len(prepared_books),
                primary_backbone_count,
                heldout_variant_count,
                accepted_shadow_phrase_count,
                accepted_firewall_count,
                source_anchor_count,
                q56_queue_completion_count,
                direct_gloss_count,
                canonical_promotion_allowed_count,
                consolidated_shadow_pt,
                consolidated_shadow_en,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q59_consolidated_shadow_backbone_v1_books (
                run_id, bookid, route_position, route_role, route_class,
                confidence_band, shadow_version_pt, shadow_version_en,
                accepted_test_ids_json, source_ids_json, residual_risk,
                next_validation, promotion_status, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    item["bookid"],
                    int(item["route_position"]),
                    str(item["route_role"]),
                    str(item["route_class"]),
                    str(item["confidence_band"]),
                    str(item["shadow_version_pt"]),
                    str(item["shadow_version_en"]),
                    j(item["accepted_test_ids"]),
                    j(item["source_ids"]),
                    str(item["residual_risk"]),
                    str(item["next_validation"]),
                    str(item["promotion_status"]),
                    j(item["evidence"]),
                )
                for item in prepared_books
            ],
        )
        conn.executemany(
            """
            INSERT INTO human_q59_consolidated_shadow_backbone_v1_risks (
                run_id, risk_id, risk_class, applies_to_books_json,
                risk_statement, mitigation, promotion_blocker, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    str(risk["risk_id"]),
                    str(risk["risk_class"]),
                    j(risk["applies_to_books"]),
                    str(risk["risk_statement"]),
                    str(risk["mitigation"]),
                    int(risk["promotion_blocker"]),
                    j(risk["evidence"]),
                )
                for risk in risks
            ],
        )

    print(
        j(
            {
                "run_id": run_id,
                "decision": decision,
                "phrase_book_count": len(prepared_books),
                "primary_backbone_count": primary_backbone_count,
                "heldout_variant_count": heldout_variant_count,
                "accepted_shadow_phrase_count": accepted_shadow_phrase_count,
                "accepted_firewall_count": accepted_firewall_count,
                "source_anchor_count": source_anchor_count,
                "q56_queue_completion_count": q56_queue_completion_count,
                "direct_gloss_count": direct_gloss_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
            }
        )
    )


if __name__ == "__main__":
    main()
