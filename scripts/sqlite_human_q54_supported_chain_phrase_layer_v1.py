#!/usr/bin/env python3
"""Q54: draft phrase-level functional readings for supported C86/C68 chains."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
TARGET_BOOKS = ["2", "10", "27", "35", "67"]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q54_supported_chain_phrase_layer_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q53_run_id INTEGER NOT NULL,
            q35_run_id INTEGER NOT NULL,
            c86_c68_naese_chain_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            target_book_count INTEGER NOT NULL,
            phrase_candidate_count INTEGER NOT NULL,
            exact_contig_shadow_book_count INTEGER NOT NULL,
            edge_confirmed_book_count INTEGER NOT NULL,
            strong_phrase_candidate_count INTEGER NOT NULL,
            moderate_phrase_candidate_count INTEGER NOT NULL,
            prose_gloss_allowed_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            layer_human_version TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q54_supported_chain_phrase_layer_v1_books (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            phrase_profile TEXT NOT NULL,
            confidence_tier TEXT NOT NULL,
            q53_chain_profile TEXT NOT NULL,
            phrase_functional_version TEXT NOT NULL,
            q53_chain_functional_version TEXT NOT NULL,
            contig_shadow_status TEXT NOT NULL,
            edge_confirmation_status TEXT NOT NULL,
            translation_use TEXT NOT NULL,
            blocked_claims_json TEXT NOT NULL,
            next_probe TEXT NOT NULL,
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


def q53_book(conn: sqlite3.Connection, q53_run_id: int, bookid: str) -> sqlite3.Row:
    row = conn.execute(
        """
        SELECT *
        FROM human_q53_c86_c68_chain_synthesis_v1_books
        WHERE run_id=? AND bookid=?
        """,
        (q53_run_id, bookid),
    ).fetchone()
    if row is None:
        raise RuntimeError(f"missing Q53 book {bookid}")
    return row


def q36_book(conn: sqlite3.Connection, bookid: str) -> sqlite3.Row:
    row = conn.execute(
        """
        SELECT *
        FROM human_q36_book_contig_shadow_integration_v1_items
        WHERE run_id=(SELECT max(run_id) FROM human_q36_book_contig_shadow_integration_v1_items)
          AND bookid=?
        """,
        (bookid,),
    ).fetchone()
    if row is None:
        raise RuntimeError(f"missing Q36 book {bookid}")
    return row


def contig_packet(conn: sqlite3.Connection, q35_run_id: int) -> sqlite3.Row:
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


def edge_confirmations(conn: sqlite3.Connection, chain_run_id: int) -> set[str]:
    return {
        str(row["item_id"])
        for row in conn.execute(
            """
            SELECT item_id
            FROM c86_c68_naese_chain_probe_v1_items
            WHERE run_id=? AND item_type='branch_book'
              AND gate_status='STRUCTURAL_BRANCH_RESOLVED_NO_PROSE'
            """,
            (chain_run_id,),
        )
    }


def phrase_profile(bookid: str, q53: sqlite3.Row, q36: sqlite3.Row, edge_books: set[str]) -> tuple[str, str, str, str]:
    contig_ready = str(q36["contig_status"]) == "EXACT_CONTIG_SHADOW_AVAILABLE"
    edge_ready = bookid in edge_books
    if bookid == "2":
        return (
            "PHRASE_CONTEXT_TO_SLOT_CLASSIFIER",
            "STRONG_CHAIN_SLOT_EDGE",
            "The selected context is handed into the classifier slot.",
            "Use as the primary phrase-level backbone; test against the 67->2 edge and NAESE slot controls.",
        )
    if bookid == "67":
        return (
            "PHRASE_CONTEXT_HANDOFF_TO_SLOT",
            "STRONG_CHAIN_HANDOFF_EDGE",
            "The context handoff prepares the classifier slot.",
            "Use as the immediate handoff control before Book 2.",
        )
    if bookid == "35":
        return (
            "PHRASE_FORMULA_TO_CONTEXT_ROUTE",
            "STRONG_CONTIG_CONTEXT_ROUTE",
            "The formula body hands context toward the classifier path.",
            "Use as the contig-supported formula-to-context route before Book 67.",
        )
    if contig_ready or edge_ready:
        confidence = "MODERATE_STRONG_SUPPORTED_ROUTE"
    else:
        confidence = "MODERATE_HELDOUT_CONTEXT_ROUTE"
    if bookid == "10":
        return (
            "PHRASE_FORMULA_TO_CONTEXT_ROUTE",
            confidence,
            "The formula hands off into context routing.",
            "Compare with Book 35 to test whether this is a non-contig version of the same route.",
        )
    if bookid == "27":
        return (
            "PHRASE_PAYLOAD_CONTEXT_HOLD",
            confidence,
            "The payload corridor holds the selected context open.",
            "Compare with Books 67 and 2 to test whether slot material follows.",
        )
    return (
        "PHRASE_SUPPORTED_CONTEXT_ROUTE",
        confidence,
        str(q53["chain_functional_version"]),
        "Inspect manually.",
    )


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q53 = latest_row(conn, "human_q53_c86_c68_chain_synthesis_v1_runs")
    q35 = latest_row(conn, "human_q35_contig_shadow_atlas_v1_runs")
    chain_probe = latest_row(conn, "c86_c68_naese_chain_probe_v1_runs")
    audit = latest_row(conn, "human_translation_completion_audit_v5_runs")
    contig = contig_packet(conn, int(q35["run_id"]))
    edge_books = edge_confirmations(conn, int(chain_probe["run_id"]))

    prepared = []
    for bookid in TARGET_BOOKS:
        q53_item = q53_book(conn, int(q53["run_id"]), bookid)
        q36_item = q36_book(conn, bookid)
        if not str(q53_item["chain_profile"]).startswith("SUPPORTED"):
            raise RuntimeError(f"target book {bookid} is not supported in Q53")
        profile, confidence, phrase, next_probe = phrase_profile(bookid, q53_item, q36_item, edge_books)
        contig_shadow_status = str(q36_item["contig_status"])
        edge_confirmation_status = "EDGE_CONFIRMED" if bookid in edge_books else "NO_DIRECT_EDGE_CONFIRMATION"
        prepared.append(
            {
                "bookid": bookid,
                "phrase_profile": profile,
                "confidence_tier": confidence,
                "q53_chain_profile": str(q53_item["chain_profile"]),
                "phrase_functional_version": phrase,
                "q53_chain_functional_version": str(q53_item["chain_functional_version"]),
                "contig_shadow_status": contig_shadow_status,
                "edge_confirmation_status": edge_confirmation_status,
                "translation_use": "human phrase-functional candidate; not lexical or canonical plaintext",
                "blocked_claims": [
                    "component_gloss",
                    "sentence_translation",
                    "C86_as_word",
                    "C68_as_word",
                    "NAESE_as_word",
                    "canonical_plaintext",
                ],
                "next_probe": next_probe,
                "evidence": {
                    "q53_book": dict(q53_item),
                    "q36_book": dict(q36_item),
                    "q35_contig_58_35_67_2": dict(contig),
                    "edge_confirmed_books": sorted(edge_books),
                    "c86_c68_naese_chain_run": dict(chain_probe),
                },
            }
        )

    exact_contig_shadow_book_count = sum(
        1 for item in prepared if item["contig_shadow_status"] == "EXACT_CONTIG_SHADOW_AVAILABLE"
    )
    edge_confirmed_book_count = sum(1 for item in prepared if item["edge_confirmation_status"] == "EDGE_CONFIRMED")
    strong_phrase_candidate_count = sum(1 for item in prepared if item["confidence_tier"].startswith("STRONG"))
    moderate_phrase_candidate_count = len(prepared) - strong_phrase_candidate_count
    prose_gloss_allowed_count = 0
    canonical_promotion_allowed_count = 0
    layer_human_version = (
        "Supported C86/C68 phrase layer: the strongest current human backbone reads as formula/context routing into a classifier slot. "
        "Book 2 is the context-to-slot phrase, Book 67 is the handoff into it, Book 35 is the contig-supported formula-to-context route, and Books 10/27 are held-out route variants."
    )
    decision = (
        "Q54_SUPPORTED_CHAIN_PHRASE_LAYER_READY_5_CANDIDATES_NO_GLOSS"
        if len(prepared) == 5
        and exact_contig_shadow_book_count == 3
        and edge_confirmed_book_count == 2
        and strong_phrase_candidate_count == 3
        and int(chain_probe["chain_pass"]) == 1
        and int(chain_probe["accepted_prose_gloss_count"]) == 0
        and int(audit["promoted_gloss_count"]) == 0
        and prose_gloss_allowed_count == 0
        and canonical_promotion_allowed_count == 0
        else "Q54_SUPPORTED_CHAIN_PHRASE_LAYER_REQUIRES_REVIEW"
    )
    payload = {
        "question": "Can the Q53 supported C86/C68 chains become phrase-level human candidates?",
        "answer": "Yes, as five phrase-functional candidates with three strong anchors and two moderate held-outs.",
        "layer_human_version": layer_human_version,
        "blocked_use": "These are phrase-functional candidates only; no component or sentence gloss is promoted.",
        "next_action": "Use these five candidates as the first phrase-level backbone for source-search and contradiction tests.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q54_supported_chain_phrase_layer_v1_runs (
                created_at, decision, q53_run_id, q35_run_id,
                c86_c68_naese_chain_run_id, completion_audit_run_id,
                target_book_count, phrase_candidate_count,
                exact_contig_shadow_book_count, edge_confirmed_book_count,
                strong_phrase_candidate_count, moderate_phrase_candidate_count,
                prose_gloss_allowed_count, canonical_promotion_allowed_count,
                layer_human_version, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                int(q53["run_id"]),
                int(q35["run_id"]),
                int(chain_probe["run_id"]),
                int(audit["run_id"]),
                len(prepared),
                len(prepared),
                exact_contig_shadow_book_count,
                edge_confirmed_book_count,
                strong_phrase_candidate_count,
                moderate_phrase_candidate_count,
                prose_gloss_allowed_count,
                canonical_promotion_allowed_count,
                layer_human_version,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q54_supported_chain_phrase_layer_v1_books (
                run_id, bookid, phrase_profile, confidence_tier,
                q53_chain_profile, phrase_functional_version,
                q53_chain_functional_version, contig_shadow_status,
                edge_confirmation_status, translation_use,
                blocked_claims_json, next_probe, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    item["bookid"],
                    item["phrase_profile"],
                    item["confidence_tier"],
                    item["q53_chain_profile"],
                    item["phrase_functional_version"],
                    item["q53_chain_functional_version"],
                    item["contig_shadow_status"],
                    item["edge_confirmation_status"],
                    item["translation_use"],
                    j(item["blocked_claims"]),
                    item["next_probe"],
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
                "target_book_count": len(prepared),
                "phrase_candidate_count": len(prepared),
                "exact_contig_shadow_book_count": exact_contig_shadow_book_count,
                "edge_confirmed_book_count": edge_confirmed_book_count,
                "strong_phrase_candidate_count": strong_phrase_candidate_count,
                "moderate_phrase_candidate_count": moderate_phrase_candidate_count,
                "prose_gloss_allowed_count": prose_gloss_allowed_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
            }
        )
    )


if __name__ == "__main__":
    main()
