#!/usr/bin/env python3
"""Q80: build controlled human-shadow packet versions for 35->67->2 and 27->67."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

PRIMARY_BOOKS = ["35", "67", "2"]
HELDOUT_BOOKS = ["27", "67", "2"]

PACKET_SPECS = [
    {
        "packet_id": "Q80_P01_PRIMARY_35_67_2",
        "sequence": "35->67->2",
        "packet_class": "PRIMARY_HUMAN_SHADOW_PACKET",
        "confidence_tier": "STRONG_FUNCTIONAL_PACKET_NO_GLOSS",
        "books": PRIMARY_BOOKS,
        "version_en": (
            "The formula body routes the context; the handoff prepares the classifier slot; "
            "the selected context enters the classifier slot."
        ),
        "version_pt": (
            "O corpo da formula encaminha o contexto; a passagem prepara o slot classificador; "
            "o contexto selecionado entra no slot classificador."
        ),
        "status": "ACCEPT_HUMAN_SHADOW_PACKET_NOT_CANONICAL",
        "promotion_block": "No exact source gives plaintext for 35->67->2 or any component gloss.",
        "next_action": "Use as the main readable packet spine for source search and contrastive controls.",
    },
    {
        "packet_id": "Q80_P02_HELDOUT_27_67_2",
        "sequence": "27->67->2",
        "packet_class": "HELDOUT_EXTENSION_CANDIDATE",
        "confidence_tier": "MODERATE_STRUCTURAL_CANDIDATE_NO_GLOSS",
        "books": HELDOUT_BOOKS,
        "version_en": (
            "If 27->67 is confirmed, the payload corridor holds the selected context open before "
            "the handoff prepares the classifier slot and the selected context enters that slot."
        ),
        "version_pt": (
            "Se 27->67 for confirmado, o corredor de carga mantem aberto o contexto selecionado "
            "antes da passagem preparar o slot classificador e o contexto selecionado entrar nesse slot."
        ),
        "status": "KEEP_CONDITIONAL_SHADOW_EXTENSION_UNCONFIRMED",
        "promotion_block": "27->67 has no imported contig confirmation, source resolution, or external exact hit.",
        "next_action": "Seek independent contig reconstruction or exact in-game source support before using as more than heldout.",
    },
]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q80_packet_shadow_versions_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q59_run_id INTEGER NOT NULL,
            q73_run_id INTEGER NOT NULL,
            q74_run_id INTEGER NOT NULL,
            q78_run_id INTEGER NOT NULL,
            q79_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            packet_version_count INTEGER NOT NULL,
            accepted_primary_packet_count INTEGER NOT NULL,
            conditional_heldout_packet_count INTEGER NOT NULL,
            source_anchor_count INTEGER NOT NULL,
            exact_source_sequence_count INTEGER NOT NULL,
            exact_meaning_relation_count INTEGER NOT NULL,
            confirmed_edge_extension_count INTEGER NOT NULL,
            lexical_ready_count INTEGER NOT NULL,
            direct_gloss_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            synthesis_en TEXT NOT NULL,
            synthesis_pt TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q80_packet_shadow_versions_v1_packets (
            run_id INTEGER NOT NULL,
            packet_id TEXT NOT NULL,
            sequence TEXT NOT NULL,
            packet_class TEXT NOT NULL,
            confidence_tier TEXT NOT NULL,
            book_sequence_json TEXT NOT NULL,
            version_en TEXT NOT NULL,
            version_pt TEXT NOT NULL,
            status TEXT NOT NULL,
            promotion_block TEXT NOT NULL,
            next_action TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, packet_id)
        );

        CREATE TABLE IF NOT EXISTS human_q80_packet_shadow_versions_v1_book_roles (
            run_id INTEGER NOT NULL,
            packet_id TEXT NOT NULL,
            bookid TEXT NOT NULL,
            route_role TEXT NOT NULL,
            shadow_version_en TEXT NOT NULL,
            shadow_version_pt TEXT NOT NULL,
            residual_risk TEXT NOT NULL,
            q78_edge_condition_status TEXT NOT NULL,
            q78_control_result TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, packet_id, bookid)
        );

        CREATE TABLE IF NOT EXISTS human_q80_packet_shadow_versions_v1_source_rules (
            run_id INTEGER NOT NULL,
            source_id TEXT NOT NULL,
            source_role TEXT NOT NULL,
            allowed_use TEXT NOT NULL,
            blocked_inference TEXT NOT NULL,
            source_rule_status TEXT NOT NULL,
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


def load_q59_books(conn: sqlite3.Connection, q59_run_id: int) -> dict[str, sqlite3.Row]:
    rows = conn.execute(
        """
        SELECT *
        FROM human_q59_consolidated_shadow_backbone_v1_books
        WHERE run_id=?
        """,
        (q59_run_id,),
    ).fetchall()
    return {str(row["bookid"]): row for row in rows}


def load_q78_controls(conn: sqlite3.Connection, q78_run_id: int) -> dict[str, sqlite3.Row]:
    rows = conn.execute(
        """
        SELECT *
        FROM human_q78_edge_67_2_source_continuity_v1_controls
        WHERE run_id=?
        """,
        (q78_run_id,),
    ).fetchall()
    return {str(row["bookid"]): row for row in rows}


def load_q79_sources(conn: sqlite3.Connection, q79_run_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT *
        FROM human_q79_global_source_firewall_v1_sources
        WHERE run_id=?
        ORDER BY source_id
        """,
        (q79_run_id,),
    ).fetchall()


def book_evidence(
    bookid: str,
    q59_books: dict[str, sqlite3.Row],
    q78_controls: dict[str, sqlite3.Row],
) -> dict[str, object]:
    q59 = q59_books.get(bookid)
    q78 = q78_controls.get(bookid)
    if q59 is None:
        raise RuntimeError(f"missing Q59 book row: {bookid}")
    if q78 is None and bookid in {"35", "67", "2", "27"}:
        raise RuntimeError(f"missing Q78 control row: {bookid}")
    return {
        "bookid": bookid,
        "route_role": str(q59["route_role"]),
        "shadow_version_en": str(q59["shadow_version_en"]),
        "shadow_version_pt": str(q59["shadow_version_pt"]),
        "residual_risk": str(q59["residual_risk"]),
        "q78_edge_condition_status": str(q78["edge_condition_status"]) if q78 is not None else "NO_Q78_CONTROL",
        "q78_control_result": str(q78["control_result"]) if q78 is not None else "NO_Q78_CONTROL",
        "q59": dict(q59),
        "q78": dict(q78) if q78 is not None else None,
    }


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q59 = latest_row(conn, "human_q59_consolidated_shadow_backbone_v1_runs")
    q73 = latest_row(conn, "human_q73_book27_to_67_confirmation_gate_v1_runs")
    q74 = latest_row(conn, "human_q74_book27_to_67_external_exact_search_audit_v1_runs")
    q78 = latest_row(conn, "human_q78_edge_67_2_source_continuity_v1_runs")
    q79 = latest_row(conn, "human_q79_global_source_firewall_v1_runs")
    audit = latest_row(conn, "human_translation_completion_audit_v5_runs")

    q59_books = load_q59_books(conn, int(q59["run_id"]))
    q78_controls = load_q78_controls(conn, int(q78["run_id"]))
    q79_sources = load_q79_sources(conn, int(q79["run_id"]))

    packet_rows = []
    book_role_rows = []
    for spec in PACKET_SPECS:
        books = [book_evidence(bookid, q59_books, q78_controls) for bookid in spec["books"]]
        packet_rows.append(
            {
                **spec,
                "evidence": {
                    "q59_decision": str(q59["decision"]),
                    "q73_decision": str(q73["decision"]),
                    "q74_decision": str(q74["decision"]),
                    "q78_decision": str(q78["decision"]),
                    "q79_decision": str(q79["decision"]),
                    "books": books,
                },
            }
        )
        for book in books:
            book_role_rows.append({**book, "packet_id": spec["packet_id"]})

    packet_version_count = len(packet_rows)
    accepted_primary_packet_count = sum(
        1 for row in packet_rows if row["status"] == "ACCEPT_HUMAN_SHADOW_PACKET_NOT_CANONICAL"
    )
    conditional_heldout_packet_count = sum(
        1 for row in packet_rows if row["status"] == "KEEP_CONDITIONAL_SHADOW_EXTENSION_UNCONFIRMED"
    )
    source_anchor_count = len(q79_sources)
    exact_source_sequence_count = int(q79["exact_source_sequence_count"])
    exact_meaning_relation_count = int(q79["exact_meaning_relation_count"])
    confirmed_edge_extension_count = int(q73["confirmed_edge_count"])
    lexical_ready_count = 0
    direct_gloss_count = 0
    canonical_promotion_allowed_count = 0
    synthesis_en = (
        "Controlled human-shadow reading: 35->67->2 is the current primary packet: formula routes "
        "context, handoff prepares the classifier slot, and selected context enters that slot. "
        "27->67->2 is only a conditional heldout extension."
    )
    synthesis_pt = (
        "Leitura humana-sombra controlada: 35->67->2 e o pacote primario atual: a formula encaminha "
        "o contexto, a passagem prepara o slot classificador, e o contexto selecionado entra nesse slot. "
        "27->67->2 fica apenas como extensao heldout condicional."
    )
    decision = (
        "Q80_PACKET_SHADOW_VERSIONS_READY_PRIMARY_35_67_2_HELDOUT_27_67_NO_GLOSS"
        if packet_version_count == 2
        and accepted_primary_packet_count == 1
        and conditional_heldout_packet_count == 1
        and source_anchor_count >= 8
        and exact_source_sequence_count == 0
        and exact_meaning_relation_count == 0
        and confirmed_edge_extension_count == 0
        and int(q78["canonical_promotion_allowed_count"]) == 0
        and int(q79["canonical_promotion_allowed_count"]) == 0
        and int(audit["promoted_gloss_count"]) == 0
        else "Q80_PACKET_SHADOW_VERSIONS_REQUIRES_REVIEW"
    )
    payload = {
        "question": "What human-readable versions can be used after Q77-Q79 without violating the source firewall?",
        "answer_en": synthesis_en,
        "answer_pt": synthesis_pt,
        "blocked_use": "Do not report these packet versions as canonical plaintext or source-backed dictionary gloss.",
        "next_action": "Use Q80 packet versions to search for exact in-game anchors and to build controlled book-by-book shadow exports.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q80_packet_shadow_versions_v1_runs (
                created_at, decision, q59_run_id, q73_run_id, q74_run_id,
                q78_run_id, q79_run_id, completion_audit_run_id,
                packet_version_count, accepted_primary_packet_count,
                conditional_heldout_packet_count, source_anchor_count,
                exact_source_sequence_count, exact_meaning_relation_count,
                confirmed_edge_extension_count, lexical_ready_count,
                direct_gloss_count, canonical_promotion_allowed_count,
                synthesis_en, synthesis_pt, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                int(q59["run_id"]),
                int(q73["run_id"]),
                int(q74["run_id"]),
                int(q78["run_id"]),
                int(q79["run_id"]),
                int(audit["run_id"]),
                packet_version_count,
                accepted_primary_packet_count,
                conditional_heldout_packet_count,
                source_anchor_count,
                exact_source_sequence_count,
                exact_meaning_relation_count,
                confirmed_edge_extension_count,
                lexical_ready_count,
                direct_gloss_count,
                canonical_promotion_allowed_count,
                synthesis_en,
                synthesis_pt,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q80_packet_shadow_versions_v1_packets (
                run_id, packet_id, sequence, packet_class, confidence_tier,
                book_sequence_json, version_en, version_pt, status,
                promotion_block, next_action, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    row["packet_id"],
                    row["sequence"],
                    row["packet_class"],
                    row["confidence_tier"],
                    j(row["books"]),
                    row["version_en"],
                    row["version_pt"],
                    row["status"],
                    row["promotion_block"],
                    row["next_action"],
                    j(row["evidence"]),
                )
                for row in packet_rows
            ],
        )
        conn.executemany(
            """
            INSERT INTO human_q80_packet_shadow_versions_v1_book_roles (
                run_id, packet_id, bookid, route_role, shadow_version_en,
                shadow_version_pt, residual_risk, q78_edge_condition_status,
                q78_control_result, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    row["packet_id"],
                    row["bookid"],
                    row["route_role"],
                    row["shadow_version_en"],
                    row["shadow_version_pt"],
                    row["residual_risk"],
                    row["q78_edge_condition_status"],
                    row["q78_control_result"],
                    j({"q59": row["q59"], "q78": row["q78"]}),
                )
                for row in book_role_rows
            ],
        )
        conn.executemany(
            """
            INSERT INTO human_q80_packet_shadow_versions_v1_source_rules (
                run_id, source_id, source_role, allowed_use,
                blocked_inference, source_rule_status, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    str(row["source_id"]),
                    str(row["source_role"]),
                    str(row["source_parallel_use"]),
                    str(row["blocked_inference"]),
                    "SOURCE_ANCHOR_ALLOWED_AS_REGISTER_OR_METHOD_ONLY",
                    j(dict(row)),
                )
                for row in q79_sources
            ],
        )

    print(
        j(
            {
                "run_id": run_id,
                "decision": decision,
                "packet_version_count": packet_version_count,
                "accepted_primary_packet_count": accepted_primary_packet_count,
                "conditional_heldout_packet_count": conditional_heldout_packet_count,
                "source_anchor_count": source_anchor_count,
                "exact_source_sequence_count": exact_source_sequence_count,
                "exact_meaning_relation_count": exact_meaning_relation_count,
                "confirmed_edge_extension_count": confirmed_edge_extension_count,
                "lexical_ready_count": lexical_ready_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
            }
        )
    )


if __name__ == "__main__":
    main()
