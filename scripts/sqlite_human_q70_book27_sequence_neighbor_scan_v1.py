#!/usr/bin/env python3
"""Q70: scan row0 sequence neighbors for Book27 stop-vs-continuation."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

TARGET_BOOK = "27"
CONTROL_EDGES = [("58", "35"), ("35", "67"), ("67", "2")]
CONTROL_PAIRS = [("27", "67"), ("27", "2"), ("35", "27"), ("10", "27")]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def overlap(left: list[str], right: list[str]) -> int:
    for size in range(min(len(left), len(right)), 0, -1):
        if left[-size:] == right[:size]:
            return size
    return 0


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q70_book27_sequence_neighbor_scan_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q69_run_id INTEGER NOT NULL,
            q65_run_id INTEGER NOT NULL,
            q64_run_id INTEGER NOT NULL,
            row0_run_id INTEGER NOT NULL,
            contig_overlap_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            target_bookid TEXT NOT NULL,
            scanned_book_count INTEGER NOT NULL,
            outgoing_candidate_count INTEGER NOT NULL,
            incoming_candidate_count INTEGER NOT NULL,
            top_outgoing_bookid TEXT NOT NULL,
            top_outgoing_overlap_tokens INTEGER NOT NULL,
            accepted_edge_min_overlap_tokens INTEGER NOT NULL,
            accepted_edge_match_or_better_count INTEGER NOT NULL,
            imported_contig_edge_count INTEGER NOT NULL,
            continuation_candidate_count INTEGER NOT NULL,
            endpoint_support_count INTEGER NOT NULL,
            stop_continue_resolved_count INTEGER NOT NULL,
            lexical_ready_count INTEGER NOT NULL,
            direct_gloss_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            result_human_version TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q70_book27_sequence_neighbor_scan_v1_candidates (
            run_id INTEGER NOT NULL,
            rank INTEGER NOT NULL,
            direction TEXT NOT NULL,
            left_bookid TEXT NOT NULL,
            right_bookid TEXT NOT NULL,
            overlap_tokens INTEGER NOT NULL,
            overlap_token_text TEXT NOT NULL,
            relation_class TEXT NOT NULL,
            candidate_status TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, direction, rank, left_bookid, right_bookid)
        );

        CREATE TABLE IF NOT EXISTS human_q70_book27_sequence_neighbor_scan_v1_controls (
            run_id INTEGER NOT NULL,
            left_bookid TEXT NOT NULL,
            right_bookid TEXT NOT NULL,
            overlap_tokens INTEGER NOT NULL,
            overlap_token_text TEXT NOT NULL,
            imported_contig_edge INTEGER NOT NULL,
            control_status TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, left_bookid, right_bookid)
        );
        """
    )


def latest_row(conn: sqlite3.Connection, table: str) -> sqlite3.Row:
    row = conn.execute(f"SELECT * FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    if row is None:
        raise RuntimeError(f"missing required row: {table}")
    return row


def load_tokens(conn: sqlite3.Connection, row0_run_id: int) -> dict[str, list[str]]:
    rows = conn.execute(
        """
        SELECT bookid, tokens_json
        FROM row0_variant_book_tokens
        WHERE run_id=?
        """,
        (row0_run_id,),
    ).fetchall()
    if not rows:
        raise RuntimeError("row0_variant_book_tokens is empty")
    return {str(row["bookid"]): json.loads(str(row["tokens_json"])) for row in rows}


def imported_edges(conn: sqlite3.Connection, overlap_run_id: int) -> set[tuple[str, str]]:
    rows = conn.execute(
        """
        SELECT left_bookid, right_bookid
        FROM contig_max_overlap_edges
        WHERE run_id=?
        """,
        (overlap_run_id,),
    ).fetchall()
    return {(str(row["left_bookid"]), str(row["right_bookid"])) for row in rows}


def pair_overlap(tokens: dict[str, list[str]], left_bookid: str, right_bookid: str) -> tuple[int, list[str]]:
    size = overlap(tokens[left_bookid], tokens[right_bookid])
    return size, tokens[left_bookid][-size:] if size else []


def relation_class(
    left_bookid: str,
    right_bookid: str,
    overlap_tokens: int,
    accepted_edge_min_overlap_tokens: int,
    imported: bool,
) -> str:
    if imported:
        return "IMPORTED_CONTIG_EDGE"
    if left_bookid == TARGET_BOOK and overlap_tokens >= accepted_edge_min_overlap_tokens:
        return "TARGET_OUTGOING_CONTINUATION_CANDIDATE"
    if right_bookid == TARGET_BOOK and overlap_tokens > 0:
        return "TARGET_INCOMING_CANDIDATE"
    if left_bookid == TARGET_BOOK and overlap_tokens > 0:
        return "TARGET_WEAK_OUTGOING_OVERLAP"
    return "CONTROL_OR_BACKGROUND_OVERLAP"


def candidate_status(relation: str) -> str:
    if relation == "TARGET_OUTGOING_CONTINUATION_CANDIDATE":
        return "CONTINUATION_CANDIDATE_UNCONFIRMED_NO_GLOSS"
    if relation == "TARGET_WEAK_OUTGOING_OVERLAP":
        return "WEAK_OVERLAP_CONTROL_NO_PROMOTION"
    if relation == "TARGET_INCOMING_CANDIDATE":
        return "INCOMING_CANDIDATE_REQUIRES_REVIEW"
    if relation == "IMPORTED_CONTIG_EDGE":
        return "CONFIRMED_CONTROL_EDGE"
    return "BACKGROUND_CONTROL"


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q69 = latest_row(conn, "human_q69_book27_stop_continue_source_check_v1_runs")
    q65 = latest_row(conn, "human_q65_payload_context_hold_heldout_role_v1_runs")
    q64 = latest_row(conn, "human_q64_edge_67_2_handoff_role_contrast_v1_runs")
    row0 = latest_row(conn, "row0_base_frontier_runs")
    contig_overlap = latest_row(conn, "contig_max_overlap_probe_runs")
    audit = latest_row(conn, "human_translation_completion_audit_v5_runs")
    tokens = load_tokens(conn, int(row0["run_id"]))
    edge_set = imported_edges(conn, int(contig_overlap["run_id"]))

    control_overlap_tokens = [
        pair_overlap(tokens, left_bookid, right_bookid)[0] for left_bookid, right_bookid in CONTROL_EDGES
    ]
    accepted_edge_min_overlap_tokens = min(control_overlap_tokens)

    outgoing = []
    incoming = []
    for bookid in sorted(tokens, key=lambda value: int(value) if value.isdigit() else value):
        if bookid == TARGET_BOOK:
            continue
        out_size, out_tokens = pair_overlap(tokens, TARGET_BOOK, bookid)
        if out_size:
            outgoing.append((TARGET_BOOK, bookid, out_size, out_tokens))
        in_size, in_tokens = pair_overlap(tokens, bookid, TARGET_BOOK)
        if in_size:
            incoming.append((bookid, TARGET_BOOK, in_size, in_tokens))

    outgoing.sort(key=lambda row: (-row[2], int(row[1]) if row[1].isdigit() else row[1]))
    incoming.sort(key=lambda row: (-row[2], int(row[0]) if row[0].isdigit() else row[0]))
    top_outgoing = outgoing[0] if outgoing else (TARGET_BOOK, "", 0, [])
    top_incoming_overlap = incoming[0][2] if incoming else 0
    accepted_edge_match_or_better_count = sum(1 for row in outgoing if row[2] >= accepted_edge_min_overlap_tokens)
    imported_contig_edge_count = 1 if (top_outgoing[0], top_outgoing[1]) in edge_set else 0
    continuation_candidate_count = 1 if (
        top_outgoing[1] == "67"
        and top_outgoing[2] >= accepted_edge_min_overlap_tokens
        and imported_contig_edge_count == 0
    ) else 0
    endpoint_support_count = 1 if not outgoing else 0
    stop_continue_resolved_count = 0
    lexical_ready_count = 0
    direct_gloss_count = 0
    canonical_promotion_allowed_count = 0

    result_human_version = (
        "Q70 finds a strong unconfirmed continuation candidate for Book27: its best outgoing row0 "
        "suffix-prefix overlap is 27->67 with 34 tokens, equal to the accepted 67->2 control-edge "
        "overlap and stronger than 27->2. Because 27->67 is not an imported contig edge and no source "
        "resolved the relation, Book27 remains open, but endpoint readings are now mechanically weaker."
    )
    decision = (
        "Q70_BOOK27_SEQUENCE_NEIGHBOR_SCAN_FINDS_27_TO_67_CANDIDATE_NO_GLOSS"
        if continuation_candidate_count == 1
        and top_outgoing[1] == "67"
        and top_outgoing[2] == 34
        and accepted_edge_min_overlap_tokens == 34
        and accepted_edge_match_or_better_count == 1
        and imported_contig_edge_count == 0
        and endpoint_support_count == 0
        and top_incoming_overlap == 0
        and int(q69["stop_resolved_count"]) == 0
        and int(q69["continuation_resolved_count"]) == 0
        and int(q65["heldout_role_accept_count"]) == 1
        and int(audit["promoted_gloss_count"]) == 0
        and lexical_ready_count == 0
        and direct_gloss_count == 0
        and canonical_promotion_allowed_count == 0
        else "Q70_BOOK27_SEQUENCE_NEIGHBOR_SCAN_REQUIRES_REVIEW"
    )
    payload = {
        "question": "Does row0 sequence-neighbor evidence favor Book27 endpoint or missing continuation?",
        "answer": result_human_version,
        "blocked_use": "Do not promote 27->67 as confirmed contig or translate Book27 as an endpoint.",
        "next_action": "Run a confirmation gate for 27->67 against contig controls and false-overlap backgrounds.",
        "control_edges": CONTROL_EDGES,
    }

    def row_for(rank: int, direction: str, left_bookid: str, right_bookid: str, size: int, toks: list[str]) -> tuple:
        imported = (left_bookid, right_bookid) in edge_set
        relation = relation_class(left_bookid, right_bookid, size, accepted_edge_min_overlap_tokens, imported)
        return (
            rank,
            direction,
            left_bookid,
            right_bookid,
            size,
            " ".join(toks),
            relation,
            candidate_status(relation),
            j(
                {
                    "imported_contig_edge": imported,
                    "accepted_edge_min_overlap_tokens": accepted_edge_min_overlap_tokens,
                    "left_token_count": len(tokens[left_bookid]),
                    "right_token_count": len(tokens[right_bookid]),
                }
            ),
        )

    candidate_rows = []
    for rank, item in enumerate(outgoing[:10], start=1):
        candidate_rows.append(row_for(rank, "OUTGOING", *item))
    for rank, item in enumerate(incoming[:10], start=1):
        candidate_rows.append(row_for(rank, "INCOMING", *item))

    control_rows = []
    for left_bookid, right_bookid in [*CONTROL_EDGES, *CONTROL_PAIRS]:
        size, toks = pair_overlap(tokens, left_bookid, right_bookid)
        imported = (left_bookid, right_bookid) in edge_set
        status = "IMPORTED_CONTROL_EDGE" if imported else "NON_IMPORTED_CONTROL_OR_CANDIDATE"
        control_rows.append(
            (
                left_bookid,
                right_bookid,
                size,
                " ".join(toks),
                int(imported),
                status,
                j(
                    {
                        "relation_class": relation_class(
                            left_bookid, right_bookid, size, accepted_edge_min_overlap_tokens, imported
                        ),
                        "accepted_edge_min_overlap_tokens": accepted_edge_min_overlap_tokens,
                    }
                ),
            )
        )

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q70_book27_sequence_neighbor_scan_v1_runs (
                created_at, decision, q69_run_id, q65_run_id, q64_run_id,
                row0_run_id, contig_overlap_run_id, completion_audit_run_id,
                target_bookid, scanned_book_count, outgoing_candidate_count,
                incoming_candidate_count, top_outgoing_bookid,
                top_outgoing_overlap_tokens, accepted_edge_min_overlap_tokens,
                accepted_edge_match_or_better_count, imported_contig_edge_count,
                continuation_candidate_count, endpoint_support_count,
                stop_continue_resolved_count, lexical_ready_count,
                direct_gloss_count, canonical_promotion_allowed_count,
                result_human_version, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                int(q69["run_id"]),
                int(q65["run_id"]),
                int(q64["run_id"]),
                int(row0["run_id"]),
                int(contig_overlap["run_id"]),
                int(audit["run_id"]),
                TARGET_BOOK,
                len(tokens),
                len(outgoing),
                len(incoming),
                top_outgoing[1],
                top_outgoing[2],
                accepted_edge_min_overlap_tokens,
                accepted_edge_match_or_better_count,
                imported_contig_edge_count,
                continuation_candidate_count,
                endpoint_support_count,
                stop_continue_resolved_count,
                lexical_ready_count,
                direct_gloss_count,
                canonical_promotion_allowed_count,
                result_human_version,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q70_book27_sequence_neighbor_scan_v1_candidates (
                run_id, rank, direction, left_bookid, right_bookid,
                overlap_tokens, overlap_token_text, relation_class,
                candidate_status, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [(run_id, *row) for row in candidate_rows],
        )
        conn.executemany(
            """
            INSERT INTO human_q70_book27_sequence_neighbor_scan_v1_controls (
                run_id, left_bookid, right_bookid, overlap_tokens,
                overlap_token_text, imported_contig_edge, control_status,
                evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [(run_id, *row) for row in control_rows],
        )

    print(
        j(
            {
                "run_id": run_id,
                "decision": decision,
                "target_bookid": TARGET_BOOK,
                "scanned_book_count": len(tokens),
                "outgoing_candidate_count": len(outgoing),
                "incoming_candidate_count": len(incoming),
                "top_outgoing_bookid": top_outgoing[1],
                "top_outgoing_overlap_tokens": top_outgoing[2],
                "accepted_edge_min_overlap_tokens": accepted_edge_min_overlap_tokens,
                "accepted_edge_match_or_better_count": accepted_edge_match_or_better_count,
                "imported_contig_edge_count": imported_contig_edge_count,
                "continuation_candidate_count": continuation_candidate_count,
                "endpoint_support_count": endpoint_support_count,
                "stop_continue_resolved_count": stop_continue_resolved_count,
                "lexical_ready_count": lexical_ready_count,
                "direct_gloss_count": direct_gloss_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
            }
        )
    )


if __name__ == "__main__":
    main()
