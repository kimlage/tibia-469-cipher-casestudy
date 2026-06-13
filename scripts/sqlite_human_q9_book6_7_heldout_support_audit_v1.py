#!/usr/bin/env python3
"""Q9 audit: held-out support for the Book6 -> Book7 transition relation."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

BOOK6 = "6"
BOOK7 = "7"
TARGETS = (BOOK6, BOOK7)


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q9_book6_7_heldout_support_audit_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            prior_transition_support_count INTEGER NOT NULL,
            heldout_positive_count INTEGER NOT NULL,
            weak_singleton_support_count INTEGER NOT NULL,
            no_contig_edge_count INTEGER NOT NULL,
            no_overlap_prediction_count INTEGER NOT NULL,
            no_literal_frontier_count INTEGER NOT NULL,
            no_similarity_support_count INTEGER NOT NULL,
            promoted_plaintext_gloss_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q9_book6_7_heldout_support_audit_v1_items (
            run_id INTEGER NOT NULL,
            item_id TEXT NOT NULL,
            item_type TEXT NOT NULL,
            source_table TEXT NOT NULL,
            source_key TEXT NOT NULL,
            status TEXT NOT NULL,
            role_label TEXT NOT NULL,
            support_class TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, item_id)
        );
        """
    )


def latest_id(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT max(run_id) FROM {table}").fetchone()
    if row is None or row[0] is None:
        raise RuntimeError(f"missing required run: {table}")
    return int(row[0])


def max_value(conn: sqlite3.Connection, table: str, column: str) -> int:
    row = conn.execute(f"SELECT max({column}) FROM {table}").fetchone()
    if row is None or row[0] is None:
        raise RuntimeError(f"missing required max({column}): {table}")
    return int(row[0])


def one(conn: sqlite3.Connection, sql: str, params: tuple[object, ...] = ()) -> sqlite3.Row | None:
    return conn.execute(sql, params).fetchone()


def rows(conn: sqlite3.Connection, sql: str, params: tuple[object, ...] = ()) -> list[sqlite3.Row]:
    return list(conn.execute(sql, params).fetchall())


def add_item(
    out: list[dict[str, object]],
    item_id: str,
    item_type: str,
    source_table: str,
    source_key: str,
    status: str,
    role_label: str,
    support_class: str,
    evidence: object,
) -> None:
    out.append(
        {
            "item_id": item_id,
            "item_type": item_type,
            "source_table": source_table,
            "source_key": source_key,
            "status": status,
            "role_label": role_label,
            "support_class": support_class,
            "evidence_json": j(evidence),
        }
    )


def parse_booksinorder(value: str) -> list[str]:
    return [part.strip() for part in value.split("->") if part.strip()]


def direct_6_7_pair(a: str, b: str) -> bool:
    return (a, b) in {(BOOK6, BOOK7), (BOOK7, BOOK6)}


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q8_run = latest_id(conn, "human_q8_book6_7_phase_path_3478_transition_probe_v1_runs")
    q7_run = latest_id(conn, "human_q7_book6_7_phase_path_precheck_v1_runs")
    q6_run = latest_id(conn, "human_q6_external_corpus_order_residual_probe_v1_runs")
    remaining_run = latest_id(conn, "remaining_five_evidence_requirements_v1_items")
    contig_export = max_value(conn, "sheet__contigs", "__export_id")
    contig_edge_run = latest_id(conn, "contig_max_overlap_edges")
    overlap_prediction_run = latest_id(conn, "overlap_assembly_prediction_probe_items")
    literal_frontier_run = latest_id(conn, "literal_overlap_frontier_rank_v1_items")
    residual_similarity_run = latest_id(conn, "residual_book_similarity_probe_items")
    rare_singleton_run = latest_id(conn, "rare_singleton_motif_probe_v1_items")

    items: list[dict[str, object]] = []

    for item_id, source_table, source_key, role_label in (
        (
            "prior:q8-transition",
            "human_q8_book6_7_phase_path_3478_transition_probe_v1_runs",
            f"run={q8_run}",
            "Q8 local phase/path transition support remains valid",
        ),
        (
            "prior:q7-sequence",
            "human_q7_book6_7_phase_path_precheck_v1_runs",
            f"run={q7_run}",
            "Q7 sequence precheck remains valid",
        ),
        (
            "prior:q6-external-order",
            "human_q6_external_corpus_order_residual_probe_v1_runs",
            f"run={q6_run}",
            "Q6 external order support remains audit-only",
        ),
    ):
        run_table = source_table
        run_id = int(source_key.split("=")[1])
        row = one(conn, f"SELECT * FROM {run_table} WHERE run_id=?", (run_id,))
        if not row:
            raise RuntimeError(f"missing prior support row: {source_table} {source_key}")
        add_item(
            items,
            item_id,
            "prior_transition_support",
            source_table,
            source_key,
            str(row["decision"]),
            role_label,
            "PRIOR_TRANSITION_SUPPORT_NOT_HELDOUT_PAYLOAD",
            dict(row),
        )

    contigs = rows(
        conn,
        """
        SELECT __export_id, basecontigid, length, numbooks, booksinorder
        FROM sheet__contigs
        WHERE __export_id=?
        ORDER BY basecontigid
        """,
        (contig_export,),
    )
    contig_involving: list[dict[str, object]] = []
    direct_contig_edges: list[dict[str, object]] = []
    for row in contigs:
        order = parse_booksinorder(str(row["booksinorder"]))
        if any(book in TARGETS for book in order):
            contig_involving.append({"row": dict(row), "parsed_order": order})
        for left, right in zip(order, order[1:]):
            if direct_6_7_pair(left, right):
                direct_contig_edges.append({"row": dict(row), "left": left, "right": right})
    add_item(
        items,
        "block:sheet-contigs-no-6-7-edge",
        "heldout_contig_audit",
        "sheet__contigs",
        f"__export_id={contig_export}",
        "NO_SHEET_CONTIG_MEMBERSHIP_OR_DIRECT_EDGE_FOR_6_7" if not contig_involving else "SHEET_CONTIGS_INVOLVE_6_OR_7_REVIEW",
        "Current imported contigs do not independently connect Book6 and Book7",
        "BLOCK_NO_IMPORTED_CONTIG_SUPPORT" if not direct_contig_edges else "HELDOUT_POSITIVE_IMPORTED_CONTIG_EDGE",
        {
            "total_contigs": len(contigs),
            "contigs_involving_6_or_7": contig_involving,
            "direct_6_7_edges": direct_contig_edges,
            "booksinorder_values": [str(row["booksinorder"]) for row in contigs],
        },
    )

    edge_rows = rows(
        conn,
        """
        SELECT *
        FROM contig_max_overlap_edges
        WHERE run_id=?
          AND (left_bookid IN (?, ?) OR right_bookid IN (?, ?))
        ORDER BY basecontigid, edge_index
        """,
        (contig_edge_run, BOOK6, BOOK7, BOOK6, BOOK7),
    )
    direct_overlap_edges = [
        dict(row)
        for row in edge_rows
        if direct_6_7_pair(str(row["left_bookid"]), str(row["right_bookid"]))
    ]
    add_item(
        items,
        "block:contig-max-overlap-no-6-7-edge",
        "heldout_overlap_edge_audit",
        "contig_max_overlap_edges",
        f"run={contig_edge_run}",
        "NO_CONTIG_MAX_OVERLAP_EDGE_FOR_6_7" if not direct_overlap_edges else "CONTIG_MAX_OVERLAP_EDGE_FOUND_FOR_6_7",
        "Max-overlap contig reconstruction gives no independent Book6/7 edge",
        "BLOCK_NO_CONTIG_MAX_OVERLAP_EDGE" if not direct_overlap_edges else "HELDOUT_POSITIVE_CONTIG_MAX_OVERLAP_EDGE",
        {"edges_involving_6_or_7": [dict(row) for row in edge_rows], "direct_6_7_edges": direct_overlap_edges},
    )

    prediction_rows = rows(
        conn,
        """
        SELECT *
        FROM overlap_assembly_prediction_probe_items
        WHERE run_id=?
          AND (book_a IN (?, ?) OR book_b IN (?, ?))
        ORDER BY rank
        """,
        (overlap_prediction_run, BOOK6, BOOK7, BOOK6, BOOK7),
    )
    direct_predictions = [
        dict(row)
        for row in prediction_rows
        if direct_6_7_pair(str(row["book_a"]), str(row["book_b"]))
    ]
    add_item(
        items,
        "block:overlap-assembly-no-6-7-prediction",
        "heldout_overlap_prediction_audit",
        "overlap_assembly_prediction_probe_items",
        f"run={overlap_prediction_run}",
        "NO_OVERLAP_ASSEMBLY_PREDICTION_FOR_6_7" if not direct_predictions else "OVERLAP_ASSEMBLY_PREDICTION_FOUND_FOR_6_7",
        "Overlap assembly does not independently predict Book6/7 as a pair",
        "BLOCK_NO_OVERLAP_ASSEMBLY_PREDICTION" if not direct_predictions else "HELDOUT_POSITIVE_OVERLAP_ASSEMBLY_PREDICTION",
        {"predictions_involving_6_or_7": [dict(row) for row in prediction_rows], "direct_6_7_predictions": direct_predictions},
    )

    literal_rows = rows(
        conn,
        """
        SELECT *
        FROM literal_overlap_frontier_rank_v1_items
        WHERE run_id=?
          AND (bookid IN (?, ?) OR anchor_bookid IN (?, ?))
        ORDER BY rank
        """,
        (literal_frontier_run, BOOK6, BOOK7, BOOK6, BOOK7),
    )
    direct_literal = [
        dict(row)
        for row in literal_rows
        if direct_6_7_pair(str(row["bookid"]), str(row["anchor_bookid"]))
    ]
    add_item(
        items,
        "block:literal-frontier-no-6-7-pair",
        "heldout_literal_frontier_audit",
        "literal_overlap_frontier_rank_v1_items",
        f"run={literal_frontier_run}",
        "NO_LITERAL_OVERLAP_FRONTIER_PAIR_FOR_6_7" if not direct_literal else "LITERAL_OVERLAP_FRONTIER_PAIR_FOUND_FOR_6_7",
        "Literal overlap frontier gives no independent Book6/7 pair",
        "BLOCK_NO_LITERAL_OVERLAP_FRONTIER_PAIR" if not direct_literal else "HELDOUT_POSITIVE_LITERAL_OVERLAP_FRONTIER_PAIR",
        {"literal_rows_involving_6_or_7": [dict(row) for row in literal_rows], "direct_6_7_rows": direct_literal},
    )

    similarity_rows = rows(
        conn,
        """
        SELECT *
        FROM residual_book_similarity_probe_items
        WHERE run_id=?
          AND (residual_bookid IN (?, ?) OR matched_bookid IN (?, ?))
        ORDER BY residual_bookid, lcs_ratio_shorter DESC, lcs_len DESC
        """,
        (residual_similarity_run, BOOK6, BOOK7, BOOK6, BOOK7),
    )
    direct_similarity = [
        dict(row)
        for row in similarity_rows
        if direct_6_7_pair(str(row["residual_bookid"]), str(row["matched_bookid"]))
    ]
    add_item(
        items,
        "block:residual-similarity-no-6-7-pair",
        "heldout_similarity_audit",
        "residual_book_similarity_probe_items",
        f"run={residual_similarity_run}",
        "NO_RESIDUAL_SIMILARITY_PAIR_FOR_6_7" if not direct_similarity else "RESIDUAL_SIMILARITY_PAIR_FOUND_FOR_6_7",
        "Residual similarity table gives no independent Book6/7 pair support",
        "BLOCK_NO_RESIDUAL_SIMILARITY_SUPPORT" if not direct_similarity else "HELDOUT_POSITIVE_RESIDUAL_SIMILARITY_SUPPORT",
        {"similarity_rows_involving_6_or_7": [dict(row) for row in similarity_rows], "direct_6_7_rows": direct_similarity},
    )

    singleton = one(
        conn,
        """
        SELECT *
        FROM rare_singleton_motif_probe_v1_items
        WHERE run_id=? AND bookid=? AND best_anchor=?
        """,
        (rare_singleton_run, BOOK7, BOOK6),
    )
    add_item(
        items,
        "weak:rare-singleton-book7-to-book6",
        "weak_surface_support",
        "rare_singleton_motif_probe_v1_items",
        f"run={rare_singleton_run}:book=7:anchor=6",
        str(singleton["probe_status"]) if singleton else "NO_RARE_SINGLETON_BOOK7_TO_BOOK6_ROW",
        "Book7 has only weak NEIAAETTA surface LCS to Book6",
        "WEAK_SINGLETON_SURFACE_LCS_SUPPORT_NOT_PAYLOAD" if singleton else "BLOCK_NO_RARE_SINGLETON_SUPPORT",
        dict(singleton) if singleton else {"bookid": BOOK7, "best_anchor": BOOK6, "missing": True},
    )

    for bookid in TARGETS:
        remaining = one(
            conn,
            """
            SELECT *
            FROM remaining_five_evidence_requirements_v1_items
            WHERE run_id=? AND bookid=?
            """,
            (remaining_run, bookid),
        )
        add_item(
            items,
            f"control:remaining-requirement:{bookid}",
            "remaining_requirement",
            "remaining_five_evidence_requirements_v1_items",
            f"run={remaining_run}:book={bookid}",
            "REMAINING_REQUIREMENT_STILL_ACTIVE_AFTER_Q9",
            "Q9 audits held-out support but does not translate or clear the residual requirement",
            "CONTROL_REQUIREMENT_STILL_OPEN",
            dict(remaining) if remaining else {"bookid": bookid, "missing": True},
        )

    prior_transition_support_count = sum(
        1 for row in items if str(row["support_class"]).startswith("PRIOR_TRANSITION_SUPPORT")
    )
    heldout_positive_count = sum(
        1 for row in items if str(row["support_class"]).startswith("HELDOUT_POSITIVE")
    )
    weak_singleton_support_count = sum(
        1 for row in items if str(row["support_class"]).startswith("WEAK_SINGLETON")
    )
    no_contig_edge_count = int(not direct_contig_edges and not direct_overlap_edges)
    no_overlap_prediction_count = int(not direct_predictions)
    no_literal_frontier_count = int(not direct_literal)
    no_similarity_support_count = int(not direct_similarity)
    promoted_plaintext_gloss_count = 0

    decision = (
        "Q9_BOOK6_7_TRANSITION_NO_HELDOUT_CONTIG_SUPPORT_KEEP_CONTROL_NO_GLOSS"
        if prior_transition_support_count >= 3
        and heldout_positive_count == 0
        and weak_singleton_support_count == 1
        and no_contig_edge_count == 1
        and no_overlap_prediction_count == 1
        and no_literal_frontier_count == 1
        and no_similarity_support_count == 1
        and promoted_plaintext_gloss_count == 0
        else "Q9_BOOK6_7_HELDOUT_SUPPORT_REQUIRES_MANUAL_REVIEW"
    )

    payload = {
        "question": "Does the Book6 -> Book7 transition from Q8 have independent held-out contig, overlap, or similarity support?",
        "answer": (
            "No. Q8 remains useful as a local transition-control relation, supported by Q7/Q6 and the 3478 window contrast, "
            "but current held-out contig, overlap assembly, literal frontier, and residual similarity tables do not independently "
            "predict Book6/Book7 as a pair. The only extra relation is a weak Book7-to-Book6 singleton LCS over NEIAAETTA, which is not payload."
        ),
        "allowed_reading": "Keep Book6 -> Book7 as a local continuity-to-phase control relation.",
        "blocked_reading": "Do not promote a sentence-level translation or lexical gloss for Book6, Book7, 3478, NEIAAETTA, or TIINNEF.",
        "method_implication": (
            "The next useful evidence must come from a new independent in-game phrase, a new imported artifact that creates a real 6/7 edge, "
            "or a separate semantic anchor; repeating contig/overlap confirmation with the current tables is a dead branch."
        ),
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q9_book6_7_heldout_support_audit_v1_runs (
                created_at, decision, prior_transition_support_count,
                heldout_positive_count, weak_singleton_support_count,
                no_contig_edge_count, no_overlap_prediction_count,
                no_literal_frontier_count, no_similarity_support_count,
                promoted_plaintext_gloss_count, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                prior_transition_support_count,
                heldout_positive_count,
                weak_singleton_support_count,
                no_contig_edge_count,
                no_overlap_prediction_count,
                no_literal_frontier_count,
                no_similarity_support_count,
                promoted_plaintext_gloss_count,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q9_book6_7_heldout_support_audit_v1_items (
                run_id, item_id, item_type, source_table, source_key, status,
                role_label, support_class, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    str(row["item_id"]),
                    str(row["item_type"]),
                    str(row["source_table"]),
                    str(row["source_key"]),
                    str(row["status"]),
                    str(row["role_label"]),
                    str(row["support_class"]),
                    str(row["evidence_json"]),
                )
                for row in items
            ],
        )

    print(
        j(
            {
                "run_id": run_id,
                "decision": decision,
                "prior_transition_support_count": prior_transition_support_count,
                "heldout_positive_count": heldout_positive_count,
                "weak_singleton_support_count": weak_singleton_support_count,
                "no_contig_edge_count": no_contig_edge_count,
                "no_overlap_prediction_count": no_overlap_prediction_count,
                "no_literal_frontier_count": no_literal_frontier_count,
                "no_similarity_support_count": no_similarity_support_count,
                "promoted_plaintext_gloss_count": promoted_plaintext_gloss_count,
            }
        )
    )


if __name__ == "__main__":
    main()
