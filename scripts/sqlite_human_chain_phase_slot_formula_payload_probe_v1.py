#!/usr/bin/env python3
"""Probe Q1: promoted phase/slot -> formula -> payload chain as a system."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
CHAIN_BOOKS = ["51", "53", "5", "9", "10", "35", "27", "67", "2"]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_chain_phase_slot_formula_payload_probe_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            source_synthesis_run_id INTEGER NOT NULL,
            chain_book_count INTEGER NOT NULL,
            promoted_cluster_book_count INTEGER NOT NULL,
            positive_stage_count INTEGER NOT NULL,
            positive_edge_count INTEGER NOT NULL,
            held_interface_count INTEGER NOT NULL,
            control_fail_count INTEGER NOT NULL,
            promoted_plaintext_gloss_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_chain_phase_slot_formula_payload_probe_v1_items (
            run_id INTEGER NOT NULL,
            item_id TEXT NOT NULL,
            item_type TEXT NOT NULL,
            bookid TEXT NOT NULL,
            status TEXT NOT NULL,
            role_label TEXT NOT NULL,
            support_class TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, item_id)
        );

        CREATE TABLE IF NOT EXISTS human_chain_phase_slot_formula_payload_probe_v1_edges (
            run_id INTEGER NOT NULL,
            edge_id TEXT NOT NULL,
            left_bookid TEXT NOT NULL,
            right_bookid TEXT NOT NULL,
            edge_status TEXT NOT NULL,
            edge_role TEXT NOT NULL,
            edge_strength TEXT NOT NULL,
            plaintext_gloss_allowed INTEGER NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, edge_id)
        );
        """
    )


def latest_id(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT max(run_id) FROM {table}").fetchone()
    if row is None or row[0] is None:
        raise RuntimeError(f"missing required run: {table}")
    return int(row[0])


def one(conn: sqlite3.Connection, sql: str, params: tuple[object, ...] = ()) -> sqlite3.Row | None:
    return conn.execute(sql, params).fetchone()


def all_rows(conn: sqlite3.Connection, sql: str, params: tuple[object, ...] = ()) -> list[sqlite3.Row]:
    return list(conn.execute(sql, params).fetchall())


def item(
    item_id: str,
    item_type: str,
    bookid: str,
    status: str,
    role_label: str,
    support_class: str,
    evidence: object,
) -> dict[str, object]:
    return {
        "item_id": item_id,
        "item_type": item_type,
        "bookid": bookid,
        "status": status,
        "role_label": role_label,
        "support_class": support_class,
        "evidence_json": json.dumps(evidence, ensure_ascii=False, sort_keys=True),
    }


def edge(
    edge_id: str,
    left_bookid: str,
    right_bookid: str,
    edge_status: str,
    edge_role: str,
    edge_strength: str,
    evidence: object,
) -> dict[str, object]:
    return {
        "edge_id": edge_id,
        "left_bookid": left_bookid,
        "right_bookid": right_bookid,
        "edge_status": edge_status,
        "edge_role": edge_role,
        "edge_strength": edge_strength,
        "plaintext_gloss_allowed": 0,
        "evidence_json": json.dumps(evidence, ensure_ascii=False, sort_keys=True),
    }


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    synthesis_run = latest_id(conn, "human_functional_promotion_synthesis_v1_runs")
    q2_seq_run = latest_id(conn, "q2_handoff_state_sequence_v1_items")
    q2_matrix_run = latest_id(conn, "q2_handoff_context_payload_matrix_v1_items")
    contig_run = latest_id(conn, "contig_max_overlap_edges")
    contig_stage_run = latest_id(conn, "contig1_handoff_corridor_v1_items")
    phase_run = latest_id(conn, "r20_r02_naese_phase_gate_v1_items")
    composite_run = latest_id(conn, "naese_benna_composite_probe_v1_items")

    items: list[dict[str, object]] = []
    edges: list[dict[str, object]] = []

    promoted_rows = all_rows(
        conn,
        """
        SELECT bookid, package_id, functional_label, book_specific_note,
               lexical_gloss_allowed, plaintext_gloss_allowed, evidence_json
        FROM human_functional_promotion_synthesis_v1_items
        WHERE run_id=? AND cluster='PHASE_SLOT_TO_FORMULA_CHAIN'
        ORDER BY CAST(bookid AS INT)
        """,
        (synthesis_run,),
    )
    promoted_books = {str(row["bookid"]) for row in promoted_rows}
    for row in promoted_rows:
        items.append(
            item(
                f"synthesis:{row['bookid']}",
                "promoted_stage",
                str(row["bookid"]),
                "PROMOTED_HUMAN_FUNCTIONAL_NO_GLOSS",
                str(row["functional_label"]),
                "POSITIVE_SYNTHESIS_STAGE",
                dict(row),
            )
        )

    for row in all_rows(
        conn,
        """
        SELECT bookid, gate_status, observed_frame, expected_class,
               naese_status, evidence_json
        FROM r20_r02_naese_phase_gate_v1_items
        WHERE run_id=? AND bookid IN ('51','53')
        ORDER BY CAST(bookid AS INT)
        """,
        (phase_run,),
    ):
        items.append(
            item(
                f"phase-slot:{row['bookid']}",
                "positive_stage",
                str(row["bookid"]),
                str(row["gate_status"]),
                str(row["naese_status"]),
                "POSITIVE_R02_NAESE_SLOT_INTERFACE",
                dict(row),
            )
        )

    for row in all_rows(
        conn,
        """
        SELECT bookid, status, proposed_role, best_naese_anchor,
               best_benna_anchor, evidence_json
        FROM naese_benna_composite_probe_v1_items
        WHERE run_id=? AND bookid IN ('5','9')
        ORDER BY CAST(bookid AS INT)
        """,
        (composite_run,),
    ):
        items.append(
            item(
                f"slot-formula:{row['bookid']}",
                "positive_stage",
                str(row["bookid"]),
                str(row["status"]),
                str(row["proposed_role"]),
                "POSITIVE_NAESE_BENNA_INTERFACE",
                dict(row),
            )
        )

    for row in all_rows(
        conn,
        """
        SELECT bookid, q2_role, source_component, functional_reading,
               promotion_allowed, gloss_allowed, evidence_json
        FROM q2_handoff_context_payload_matrix_v1_items
        WHERE run_id=? AND bookid IN ('2','10','27','35','67')
        ORDER BY CAST(bookid AS INT)
        """,
        (q2_matrix_run,),
    ):
        items.append(
            item(
                f"q2-matrix:{row['bookid']}",
                "positive_stage",
                str(row["bookid"]),
                str(row["q2_role"]),
                str(row["functional_reading"]),
                "POSITIVE_Q2_DOWNSTREAM_STAGE",
                dict(row),
            )
        )

    contig_edges = {
        (str(row["left_bookid"]), str(row["right_bookid"])): row
        for row in all_rows(
            conn,
            """
            SELECT basecontigid, edge_index, left_bookid, right_bookid,
                   overlap_symbols, overlap_text
            FROM contig_max_overlap_edges
            WHERE run_id=?
            """,
            (contig_run,),
        )
    }
    if ("51", "53") in contig_edges:
        row = contig_edges[("51", "53")]
        edges.append(
            edge(
                "contig:51->53",
                "51",
                "53",
                "HELD_DIRECTIONAL_EDGE_NO_GLOSS",
                "R02/NAESE pair overlap exists but package direction remains blocked",
                "HELD_INTERFACE",
                dict(row),
            )
        )
    for left, right, role in (
        ("58", "35", "upstream BENNA/LTAST support into canonical handoff source"),
        ("35", "67", "canonical handoff to context-payload bridge"),
        ("67", "2", "canonical context-payload bridge to payload-slot exit"),
    ):
        if (left, right) in contig_edges:
            row = contig_edges[(left, right)]
            edges.append(
                edge(
                    f"contig:{left}->{right}",
                    left,
                    right,
                    "ACCEPT_ORDERED_STRUCTURAL_EDGE_NO_GLOSS",
                    role,
                    "POSITIVE_ORDERED_DOWNSTREAM_EDGE",
                    dict(row),
                )
            )

    for path_id in ("CANONICAL_35_67_2", "SHADOW_10_27_2"):
        rows = all_rows(
            conn,
            """
            SELECT path_id, step_order, bookid, state_label, q2_role,
                   evidence_signal, allowed_inference, blocked_inference,
                   promotion_allowed, gloss_allowed, evidence_json
            FROM q2_handoff_state_sequence_v1_items
            WHERE run_id=? AND path_id=?
            ORDER BY step_order
            """,
            (q2_seq_run, path_id),
        )
        for prev, curr in zip(rows, rows[1:]):
            edges.append(
                edge(
                    f"q2:{path_id}:{prev['bookid']}->{curr['bookid']}",
                    str(prev["bookid"]),
                    str(curr["bookid"]),
                    "ACCEPT_Q2_SEQUENCE_EDGE_NO_GLOSS",
                    f"{prev['q2_role']} -> {curr['q2_role']}",
                    "POSITIVE_ORDERED_DOWNSTREAM_EDGE",
                    {"left": dict(prev), "right": dict(curr)},
                )
            )

    for left, right, role in (
        ("53", "5", "R02/NAESE slot bridge to NAESE/BENNA composite"),
        ("9", "10", "NAESE/BENNA composite to BENNA/C86 handoff"),
    ):
        edges.append(
            edge(
                f"held-interface:{left}->{right}",
                left,
                right,
                "HELD_NO_DIRECT_ORDERED_EDGE",
                role,
                "HELD_INTERFACE",
                {
                    "reason": "package-level functional adjacency exists, but no direct contig/Q2 edge currently promotes this as an ordered transition",
                    "plaintext_allowed": 0,
                },
            )
        )

    for row in all_rows(
        conn,
        """
        SELECT bookid, contig_position, role_bundle, inferred_stage,
               status, evidence_json
        FROM contig1_handoff_corridor_v1_items
        WHERE run_id=? AND bookid IN ('2','35','67')
        ORDER BY contig_position
        """,
        (contig_stage_run,),
    ):
        items.append(
            item(
                f"contig-stage:{row['bookid']}",
                "positive_stage",
                str(row["bookid"]),
                str(row["status"]),
                str(row["inferred_stage"]),
                "POSITIVE_CANONICAL_CONTIG_STAGE",
                dict(row),
            )
        )

    positive_stage_count = sum(1 for record in items if str(record["support_class"]).startswith("POSITIVE"))
    positive_edge_count = sum(1 for record in edges if str(record["edge_strength"]).startswith("POSITIVE"))
    held_interface_count = sum(1 for record in edges if str(record["edge_strength"]) == "HELD_INTERFACE")
    control_fail_count = 0
    plaintext_count = 0

    if promoted_books == set(CHAIN_BOOKS) and positive_edge_count >= 5 and held_interface_count >= 2:
        decision = "CHAIN_DOWNSTREAM_ROUTE_CONFIRMED_UPSTREAM_INTERFACES_HELD_NO_GLOSS"
    else:
        decision = "CHAIN_SYSTEM_INCOMPLETE_KEEP_REVIEW"

    cur = conn.execute(
        """
        INSERT INTO human_chain_phase_slot_formula_payload_probe_v1_runs
        (created_at, decision, source_synthesis_run_id, chain_book_count,
         promoted_cluster_book_count, positive_stage_count, positive_edge_count,
         held_interface_count, control_fail_count, promoted_plaintext_gloss_count,
         payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            now(),
            decision,
            synthesis_run,
            len(CHAIN_BOOKS),
            len(promoted_books),
            positive_stage_count,
            positive_edge_count,
            held_interface_count,
            control_fail_count,
            plaintext_count,
            json.dumps(
                {
                    "chain_books": CHAIN_BOOKS,
                    "interpretation": "downstream handoff/payload route is ordered; upstream phase-slot and slot-formula interfaces are functional but not a full ordered prose chain",
                    "blocked_overreach": [
                        "Do not translate stage labels as words.",
                        "Do not claim 51/53 -> 5/9 -> 10/35 is a fully ordered contig/prose path.",
                        "Do not convert Q2 paths into English sentence translations.",
                    ],
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
        ),
    )
    run_id = int(cur.lastrowid)

    for record in items:
        conn.execute(
            """
            INSERT INTO human_chain_phase_slot_formula_payload_probe_v1_items
            (run_id, item_id, item_type, bookid, status, role_label,
             support_class, evidence_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                record["item_id"],
                record["item_type"],
                record["bookid"],
                record["status"],
                record["role_label"],
                record["support_class"],
                record["evidence_json"],
            ),
        )

    for record in edges:
        conn.execute(
            """
            INSERT INTO human_chain_phase_slot_formula_payload_probe_v1_edges
            (run_id, edge_id, left_bookid, right_bookid, edge_status,
             edge_role, edge_strength, plaintext_gloss_allowed, evidence_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                record["edge_id"],
                record["left_bookid"],
                record["right_bookid"],
                record["edge_status"],
                record["edge_role"],
                record["edge_strength"],
                record["plaintext_gloss_allowed"],
                record["evidence_json"],
            ),
        )

    conn.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "chain_book_count": len(CHAIN_BOOKS),
                "promoted_cluster_book_count": len(promoted_books),
                "positive_stage_count": positive_stage_count,
                "positive_edge_count": positive_edge_count,
                "held_interface_count": held_interface_count,
                "control_fail_count": control_fail_count,
                "promoted_plaintext_gloss_count": plaintext_count,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
