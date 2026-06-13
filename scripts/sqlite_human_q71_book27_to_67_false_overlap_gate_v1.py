#!/usr/bin/env python3
"""Q71: gate the Book27->67 candidate against global false-overlap background."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

TARGET_LEFT = "27"
TARGET_RIGHT = "67"
STRONG_THRESHOLD = 34
BACKGROUND_LIMIT = 25


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
        CREATE TABLE IF NOT EXISTS human_q71_book27_to_67_false_overlap_gate_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q70_run_id INTEGER NOT NULL,
            q69_run_id INTEGER NOT NULL,
            row0_run_id INTEGER NOT NULL,
            contig_overlap_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            target_left_bookid TEXT NOT NULL,
            target_right_bookid TEXT NOT NULL,
            target_overlap_tokens INTEGER NOT NULL,
            global_directed_pair_count INTEGER NOT NULL,
            positive_overlap_pair_count INTEGER NOT NULL,
            strong_threshold_tokens INTEGER NOT NULL,
            strong_overlap_pair_count INTEGER NOT NULL,
            strong_imported_edge_count INTEGER NOT NULL,
            strong_nonimported_pair_count INTEGER NOT NULL,
            stronger_nonimported_pair_count INTEGER NOT NULL,
            target_global_rank INTEGER NOT NULL,
            target_nonimported_rank INTEGER NOT NULL,
            target_local_outgoing_rank INTEGER NOT NULL,
            false_overlap_risk_count INTEGER NOT NULL,
            continuation_confirmed_count INTEGER NOT NULL,
            continuation_candidate_count INTEGER NOT NULL,
            endpoint_support_count INTEGER NOT NULL,
            lexical_ready_count INTEGER NOT NULL,
            direct_gloss_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            result_human_version TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q71_book27_to_67_false_overlap_gate_v1_background (
            run_id INTEGER NOT NULL,
            global_rank INTEGER NOT NULL,
            nonimported_rank INTEGER NOT NULL,
            left_bookid TEXT NOT NULL,
            right_bookid TEXT NOT NULL,
            overlap_tokens INTEGER NOT NULL,
            overlap_token_text TEXT NOT NULL,
            imported_contig_edge INTEGER NOT NULL,
            pair_class TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, global_rank, left_bookid, right_bookid)
        );

        CREATE TABLE IF NOT EXISTS human_q71_book27_to_67_false_overlap_gate_v1_tests (
            run_id INTEGER NOT NULL,
            test_id TEXT NOT NULL,
            requirement TEXT NOT NULL,
            observed_result TEXT NOT NULL,
            test_status TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, test_id)
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


def pair_class(left_bookid: str, right_bookid: str, imported: bool, overlap_tokens: int) -> str:
    if left_bookid == TARGET_LEFT and right_bookid == TARGET_RIGHT:
        return "TARGET_27_TO_67"
    if imported:
        return "IMPORTED_CONTIG_EDGE"
    if overlap_tokens >= STRONG_THRESHOLD:
        return "NONIMPORTED_STRONG_OVERLAP_BACKGROUND"
    return "WEAK_OR_BACKGROUND_OVERLAP"


def build_pairs(tokens: dict[str, list[str]], edge_set: set[tuple[str, str]]) -> list[dict[str, object]]:
    pairs: list[dict[str, object]] = []
    for left_bookid, left_tokens in tokens.items():
        for right_bookid, right_tokens in tokens.items():
            if left_bookid == right_bookid:
                continue
            size = overlap(left_tokens, right_tokens)
            if size == 0:
                continue
            imported = (left_bookid, right_bookid) in edge_set
            pairs.append(
                {
                    "left_bookid": left_bookid,
                    "right_bookid": right_bookid,
                    "overlap_tokens": size,
                    "overlap_token_text": " ".join(left_tokens[-size:]),
                    "imported_contig_edge": int(imported),
                    "pair_class": pair_class(left_bookid, right_bookid, imported, size),
                    "left_token_count": len(left_tokens),
                    "right_token_count": len(right_tokens),
                }
            )
    return sorted(
        pairs,
        key=lambda row: (
            -int(row["overlap_tokens"]),
            int(row["left_bookid"]) if str(row["left_bookid"]).isdigit() else str(row["left_bookid"]),
            int(row["right_bookid"]) if str(row["right_bookid"]).isdigit() else str(row["right_bookid"]),
        ),
    )


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q70 = latest_row(conn, "human_q70_book27_sequence_neighbor_scan_v1_runs")
    q69 = latest_row(conn, "human_q69_book27_stop_continue_source_check_v1_runs")
    row0 = latest_row(conn, "row0_base_frontier_runs")
    contig_overlap = latest_row(conn, "contig_max_overlap_probe_runs")
    audit = latest_row(conn, "human_translation_completion_audit_v5_runs")

    tokens = load_tokens(conn, int(row0["run_id"]))
    edge_set = imported_edges(conn, int(contig_overlap["run_id"]))
    pairs = build_pairs(tokens, edge_set)
    target_index = next(
        i for i, row in enumerate(pairs, start=1)
        if row["left_bookid"] == TARGET_LEFT and row["right_bookid"] == TARGET_RIGHT
    )
    target = pairs[target_index - 1]
    nonimported_pairs = [row for row in pairs if int(row["imported_contig_edge"]) == 0]
    target_nonimported_rank = next(
        i for i, row in enumerate(nonimported_pairs, start=1)
        if row["left_bookid"] == TARGET_LEFT and row["right_bookid"] == TARGET_RIGHT
    )
    target_local_outgoing = [
        row for row in pairs if row["left_bookid"] == TARGET_LEFT
    ]
    target_local_outgoing.sort(
        key=lambda row: (
            -int(row["overlap_tokens"]),
            int(row["right_bookid"]) if str(row["right_bookid"]).isdigit() else str(row["right_bookid"]),
        )
    )
    target_local_outgoing_rank = next(
        i for i, row in enumerate(target_local_outgoing, start=1)
        if row["right_bookid"] == TARGET_RIGHT
    )

    global_directed_pair_count = len(tokens) * (len(tokens) - 1)
    positive_overlap_pair_count = len(pairs)
    strong_pairs = [row for row in pairs if int(row["overlap_tokens"]) >= STRONG_THRESHOLD]
    strong_imported_edge_count = sum(1 for row in strong_pairs if int(row["imported_contig_edge"]) == 1)
    strong_nonimported_pair_count = sum(1 for row in strong_pairs if int(row["imported_contig_edge"]) == 0)
    stronger_nonimported_pair_count = sum(
        1
        for row in nonimported_pairs
        if int(row["overlap_tokens"]) > int(target["overlap_tokens"])
    )
    false_overlap_risk_count = 1 if stronger_nonimported_pair_count > 0 else 0
    continuation_confirmed_count = 0
    continuation_candidate_count = 1
    endpoint_support_count = 0
    lexical_ready_count = 0
    direct_gloss_count = 0
    canonical_promotion_allowed_count = 0

    tests = [
        {
            "test_id": "Q71_T01_TARGET_LOCAL_RANK",
            "requirement": "27->67 must be Book27's strongest outgoing row0 neighbor.",
            "observed_result": f"27->67 local outgoing rank is {target_local_outgoing_rank}.",
            "test_status": "PASSES_LOCAL_CONTINUATION_SIGNAL" if target_local_outgoing_rank == 1 else "FAILS_LOCAL_CONTINUATION_SIGNAL",
        },
        {
            "test_id": "Q71_T02_ACCEPTED_EDGE_THRESHOLD",
            "requirement": "27->67 must meet or beat the accepted contig-edge overlap threshold.",
            "observed_result": f"27->67 has {target['overlap_tokens']} tokens versus threshold {STRONG_THRESHOLD}.",
            "test_status": "PASSES_ACCEPTED_EDGE_THRESHOLD"
            if int(target["overlap_tokens"]) >= STRONG_THRESHOLD
            else "FAILS_ACCEPTED_EDGE_THRESHOLD",
        },
        {
            "test_id": "Q71_T03_GLOBAL_FALSE_OVERLAP_BACKGROUND",
            "requirement": "27->67 must not be treated as confirmed if stronger non-imported overlaps exist.",
            "observed_result": f"Stronger non-imported overlaps: {stronger_nonimported_pair_count}.",
            "test_status": "FAILS_GLOBAL_CONFIRMATION_HAS_FALSE_OVERLAP_RISK"
            if stronger_nonimported_pair_count > 0
            else "PASSES_GLOBAL_CONFIRMATION_NO_STRONGER_BACKGROUND",
        },
        {
            "test_id": "Q71_T04_IMPORTED_CONTIG_REQUIREMENT",
            "requirement": "27->67 must be an imported/validated contig edge before promotion.",
            "observed_result": f"27->67 imported_contig_edge={target['imported_contig_edge']}.",
            "test_status": "FAILS_IMPORTED_CONTIG_REQUIREMENT"
            if int(target["imported_contig_edge"]) == 0
            else "PASSES_IMPORTED_CONTIG_REQUIREMENT",
        },
        {
            "test_id": "Q71_T05_NO_GLOSS_FIREWALL",
            "requirement": "No lexical or canonical promotion is allowed from overlap alone.",
            "observed_result": "Overlap evidence is structural only.",
            "test_status": "PASSES_NO_GLOSS_FIREWALL",
        },
    ]

    result_human_version = (
        "Q71 confirms 27->67 as Book27's strongest local continuation signal and equal to the "
        "accepted 67->2 overlap threshold, but it fails global confirmation: there are stronger "
        "non-imported overlaps in the corpus and 27->67 is not an imported contig edge. Keep it as "
        "a strong unconfirmed continuation candidate, not a promoted edge or translation."
    )
    decision = (
        "Q71_27_TO_67_FALSE_OVERLAP_GATE_STRONG_LOCAL_GLOBAL_UNCONFIRMED_NO_GLOSS"
        if int(target["overlap_tokens"]) == STRONG_THRESHOLD
        and target_local_outgoing_rank == 1
        and target_nonimported_rank == 7
        and strong_nonimported_pair_count == 7
        and stronger_nonimported_pair_count == 6
        and strong_imported_edge_count == 7
        and int(target["imported_contig_edge"]) == 0
        and false_overlap_risk_count == 1
        and continuation_confirmed_count == 0
        and continuation_candidate_count == 1
        and endpoint_support_count == 0
        and int(q70["continuation_candidate_count"]) == 1
        and int(q69["stop_resolved_count"]) == 0
        and int(q69["continuation_resolved_count"]) == 0
        and int(audit["promoted_gloss_count"]) == 0
        and lexical_ready_count == 0
        and direct_gloss_count == 0
        and canonical_promotion_allowed_count == 0
        else "Q71_27_TO_67_FALSE_OVERLAP_GATE_REQUIRES_REVIEW"
    )
    payload = {
        "question": "Does global overlap background confirm or weaken the 27->67 continuation candidate?",
        "answer": result_human_version,
        "blocked_use": "Do not treat 27->67 as a confirmed contig edge or sentence translation.",
        "next_action": "Classify stronger non-imported overlaps to separate true missing contigs from false overlap backgrounds.",
    }

    background_rows = []
    nonimported_seen = 0
    for global_rank, row in enumerate(pairs[:BACKGROUND_LIMIT], start=1):
        if int(row["imported_contig_edge"]) == 0:
            nonimported_seen += 1
            nonimported_rank = nonimported_seen
        else:
            nonimported_rank = 0
        background_rows.append(
            (
                global_rank,
                nonimported_rank,
                row["left_bookid"],
                row["right_bookid"],
                int(row["overlap_tokens"]),
                row["overlap_token_text"],
                int(row["imported_contig_edge"]),
                row["pair_class"],
                j(
                    {
                        "left_token_count": row["left_token_count"],
                        "right_token_count": row["right_token_count"],
                        "strong_threshold_tokens": STRONG_THRESHOLD,
                    }
                ),
            )
        )

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q71_book27_to_67_false_overlap_gate_v1_runs (
                created_at, decision, q70_run_id, q69_run_id, row0_run_id,
                contig_overlap_run_id, completion_audit_run_id,
                target_left_bookid, target_right_bookid,
                target_overlap_tokens, global_directed_pair_count,
                positive_overlap_pair_count, strong_threshold_tokens,
                strong_overlap_pair_count, strong_imported_edge_count,
                strong_nonimported_pair_count, stronger_nonimported_pair_count,
                target_global_rank, target_nonimported_rank,
                target_local_outgoing_rank, false_overlap_risk_count,
                continuation_confirmed_count, continuation_candidate_count,
                endpoint_support_count, lexical_ready_count, direct_gloss_count,
                canonical_promotion_allowed_count, result_human_version,
                payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                int(q70["run_id"]),
                int(q69["run_id"]),
                int(row0["run_id"]),
                int(contig_overlap["run_id"]),
                int(audit["run_id"]),
                TARGET_LEFT,
                TARGET_RIGHT,
                int(target["overlap_tokens"]),
                global_directed_pair_count,
                positive_overlap_pair_count,
                STRONG_THRESHOLD,
                len(strong_pairs),
                strong_imported_edge_count,
                strong_nonimported_pair_count,
                stronger_nonimported_pair_count,
                target_index,
                target_nonimported_rank,
                target_local_outgoing_rank,
                false_overlap_risk_count,
                continuation_confirmed_count,
                continuation_candidate_count,
                endpoint_support_count,
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
            INSERT INTO human_q71_book27_to_67_false_overlap_gate_v1_background (
                run_id, global_rank, nonimported_rank, left_bookid,
                right_bookid, overlap_tokens, overlap_token_text,
                imported_contig_edge, pair_class, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [(run_id, *row) for row in background_rows],
        )
        conn.executemany(
            """
            INSERT INTO human_q71_book27_to_67_false_overlap_gate_v1_tests (
                run_id, test_id, requirement, observed_result,
                test_status, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    test["test_id"],
                    test["requirement"],
                    test["observed_result"],
                    test["test_status"],
                    j({"test": test, "decision": decision}),
                )
                for test in tests
            ],
        )

    print(
        j(
            {
                "run_id": run_id,
                "decision": decision,
                "target_overlap_tokens": int(target["overlap_tokens"]),
                "global_directed_pair_count": global_directed_pair_count,
                "positive_overlap_pair_count": positive_overlap_pair_count,
                "strong_overlap_pair_count": len(strong_pairs),
                "strong_imported_edge_count": strong_imported_edge_count,
                "strong_nonimported_pair_count": strong_nonimported_pair_count,
                "stronger_nonimported_pair_count": stronger_nonimported_pair_count,
                "target_global_rank": target_index,
                "target_nonimported_rank": target_nonimported_rank,
                "target_local_outgoing_rank": target_local_outgoing_rank,
                "false_overlap_risk_count": false_overlap_risk_count,
                "continuation_confirmed_count": continuation_confirmed_count,
                "continuation_candidate_count": continuation_candidate_count,
                "lexical_ready_count": lexical_ready_count,
                "direct_gloss_count": direct_gloss_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
            }
        )
    )


if __name__ == "__main__":
    main()
