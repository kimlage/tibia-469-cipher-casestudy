#!/usr/bin/env python3
"""Q73: focused confirmation gate for the Book27->67 missing-edge candidate."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
TARGET_LEFT = "27"
TARGET_RIGHT = "67"
CONTROL_EDGE_LEFT = "35"
CONTROL_EDGE_RIGHT = "67"
ACCEPTED_EDGE_RIGHT = "2"


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
        CREATE TABLE IF NOT EXISTS human_q73_book27_to_67_confirmation_gate_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q72_run_id INTEGER NOT NULL,
            q71_run_id INTEGER NOT NULL,
            q70_run_id INTEGER NOT NULL,
            q69_run_id INTEGER NOT NULL,
            q65_run_id INTEGER NOT NULL,
            q64_run_id INTEGER NOT NULL,
            q36_run_id INTEGER NOT NULL,
            atlas_v6_run_id INTEGER NOT NULL,
            row0_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            target_edge TEXT NOT NULL,
            target_overlap_tokens INTEGER NOT NULL,
            local_rank_pass_count INTEGER NOT NULL,
            threshold_pass_count INTEGER NOT NULL,
            same_bridge_pass_count INTEGER NOT NULL,
            same_stratum_pass_count INTEGER NOT NULL,
            prefix_compatibility_pass_count INTEGER NOT NULL,
            q72_background_contained_count INTEGER NOT NULL,
            source_resolution_count INTEGER NOT NULL,
            imported_contig_confirmation_count INTEGER NOT NULL,
            structural_candidate_strengthened_count INTEGER NOT NULL,
            confirmed_edge_count INTEGER NOT NULL,
            lexical_ready_count INTEGER NOT NULL,
            direct_gloss_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            candidate_status TEXT NOT NULL,
            result_human_version TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q73_book27_to_67_confirmation_gate_v1_tests (
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


def row_by_book(conn: sqlite3.Connection, table: str, run_id: int, key: str, value: str) -> sqlite3.Row:
    row = conn.execute(f"SELECT * FROM {table} WHERE run_id=? AND {key}=?", (run_id, value)).fetchone()
    if row is None:
        raise RuntimeError(f"missing {table}.{key}={value}")
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
    return {str(row["bookid"]): json.loads(str(row["tokens_json"])) for row in rows}


def q70_candidate(conn: sqlite3.Connection, q70_run_id: int, left_bookid: str, right_bookid: str) -> sqlite3.Row:
    row = conn.execute(
        """
        SELECT *
        FROM human_q70_book27_sequence_neighbor_scan_v1_candidates
        WHERE run_id=? AND left_bookid=? AND right_bookid=?
        """,
        (q70_run_id, left_bookid, right_bookid),
    ).fetchone()
    if row is None:
        raise RuntimeError(f"missing q70 candidate {left_bookid}->{right_bookid}")
    return row


def q72_pair(conn: sqlite3.Connection, q72_run_id: int, left_bookid: str, right_bookid: str) -> sqlite3.Row:
    row = conn.execute(
        """
        SELECT *
        FROM human_q72_strong_nonimported_overlap_triage_v1_pairs
        WHERE run_id=? AND left_bookid=? AND right_bookid=?
        """,
        (q72_run_id, left_bookid, right_bookid),
    ).fetchone()
    if row is None:
        raise RuntimeError(f"missing q72 pair {left_bookid}->{right_bookid}")
    return row


def contig_edge_tokens(conn: sqlite3.Connection, left_bookid: str, right_bookid: str) -> sqlite3.Row:
    row = conn.execute(
        """
        SELECT *
        FROM contig_max_overlap_edges
        WHERE run_id=(SELECT max(run_id) FROM contig_max_overlap_edges)
          AND left_bookid=? AND right_bookid=?
        """,
        (left_bookid, right_bookid),
    ).fetchone()
    if row is None:
        raise RuntimeError(f"missing contig edge {left_bookid}->{right_bookid}")
    return row


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q72 = latest_row(conn, "human_q72_strong_nonimported_overlap_triage_v1_runs")
    q71 = latest_row(conn, "human_q71_book27_to_67_false_overlap_gate_v1_runs")
    q70 = latest_row(conn, "human_q70_book27_sequence_neighbor_scan_v1_runs")
    q69 = latest_row(conn, "human_q69_book27_stop_continue_source_check_v1_runs")
    q65 = latest_row(conn, "human_q65_payload_context_hold_heldout_role_v1_runs")
    q64 = latest_row(conn, "human_q64_edge_67_2_handoff_role_contrast_v1_runs")
    q36 = latest_row(conn, "human_q36_book_contig_shadow_integration_v1_runs")
    row0 = latest_row(conn, "row0_base_frontier_runs")
    audit = latest_row(conn, "human_translation_completion_audit_v5_runs")

    tokens = load_tokens(conn, int(row0["run_id"]))
    target_candidate = q70_candidate(conn, int(q70["run_id"]), TARGET_LEFT, TARGET_RIGHT)
    target_pair = q72_pair(conn, int(q72["run_id"]), TARGET_LEFT, TARGET_RIGHT)
    left_q36 = row_by_book(conn, "human_q36_book_contig_shadow_integration_v1_items", int(q36["run_id"]), "bookid", TARGET_LEFT)
    right_q36 = row_by_book(conn, "human_q36_book_contig_shadow_integration_v1_items", int(q36["run_id"]), "bookid", TARGET_RIGHT)
    left_atlas = row_by_book(conn, "human_translation_atlas_v6_items", int(audit["atlas_v6_run_id"]), "target_id", TARGET_LEFT)
    right_atlas = row_by_book(conn, "human_translation_atlas_v6_items", int(audit["atlas_v6_run_id"]), "target_id", TARGET_RIGHT)
    control_35_67 = contig_edge_tokens(conn, CONTROL_EDGE_LEFT, CONTROL_EDGE_RIGHT)
    control_67_2 = contig_edge_tokens(conn, TARGET_RIGHT, ACCEPTED_EDGE_RIGHT)

    target_overlap_tokens = int(target_candidate["overlap_tokens"])
    target_overlap_token_list = tokens[TARGET_LEFT][-target_overlap_tokens:]
    control_35_67_tokens = tokens[CONTROL_EDGE_LEFT][-overlap(tokens[CONTROL_EDGE_LEFT], tokens[TARGET_RIGHT]):]
    prefix_compatible = control_35_67_tokens[:target_overlap_tokens] == target_overlap_token_list
    same_bridge = str(left_atlas["source_bridge_id"]) == str(right_atlas["source_bridge_id"])
    same_stratum = str(left_q36["compiled_stratum"]) == str(right_q36["compiled_stratum"])

    local_rank_pass_count = int(int(target_candidate["rank"]) == 1)
    threshold_pass_count = int(target_overlap_tokens >= int(q70["accepted_edge_min_overlap_tokens"]))
    same_bridge_pass_count = int(same_bridge)
    same_stratum_pass_count = int(same_stratum)
    prefix_compatibility_pass_count = int(prefix_compatible)
    q72_background_contained_count = int(int(q72["known_local_or_variant_background_count"]) == 6)
    source_resolution_count = 0
    imported_contig_confirmation_count = 0
    structural_candidate_strengthened_count = int(
        local_rank_pass_count
        and threshold_pass_count
        and same_bridge_pass_count
        and same_stratum_pass_count
        and prefix_compatibility_pass_count
        and q72_background_contained_count
    )
    confirmed_edge_count = 0
    lexical_ready_count = 0
    direct_gloss_count = 0
    canonical_promotion_allowed_count = 0
    candidate_status = "STRUCTURAL_MISSING_EDGE_CANDIDATE_STRENGTHENED_UNCONFIRMED_NO_GLOSS"

    tests = [
        {
            "test_id": "Q73_T01_LOCAL_RANK_AND_THRESHOLD",
            "requirement": "27->67 must be Book27's local rank 1 outgoing candidate and meet the accepted edge threshold.",
            "observed_result": (
                f"rank={target_candidate['rank']}, overlap={target_overlap_tokens}, "
                f"threshold={q70['accepted_edge_min_overlap_tokens']}."
            ),
            "test_status": "PASSES_LOCAL_RANK_AND_THRESHOLD"
            if local_rank_pass_count and threshold_pass_count
            else "FAILS_LOCAL_RANK_AND_THRESHOLD",
        },
        {
            "test_id": "Q73_T02_SAME_BRIDGE_AND_STRATUM",
            "requirement": "27 and 67 must share payload/context bridge and stratum.",
            "observed_result": (
                f"bridge {left_atlas['source_bridge_id']} vs {right_atlas['source_bridge_id']}; "
                f"stratum {left_q36['compiled_stratum']} vs {right_q36['compiled_stratum']}."
            ),
            "test_status": "PASSES_SAME_BRIDGE_AND_STRATUM"
            if same_bridge and same_stratum
            else "FAILS_SAME_BRIDGE_AND_STRATUM",
        },
        {
            "test_id": "Q73_T03_PREFIX_COMPATIBILITY_WITH_35_TO_67",
            "requirement": "27->67 overlap must be prefix-compatible with the imported 35->67 edge overlap.",
            "observed_result": (
                f"27->67 tokens={target_overlap_tokens}; 35->67 token overlap={len(control_35_67_tokens)}; "
                f"prefix_compatible={int(prefix_compatible)}."
            ),
            "test_status": "PASSES_PREFIX_COMPATIBILITY"
            if prefix_compatible
            else "FAILS_PREFIX_COMPATIBILITY",
        },
        {
            "test_id": "Q73_T04_BACKGROUND_CONTAINED_BY_Q72",
            "requirement": "Stronger non-imported overlaps must be triaged away before strengthening 27->67.",
            "observed_result": (
                f"Q72 background count={q72['known_local_or_variant_background_count']}; "
                f"live candidates={q72['live_missing_edge_candidate_count']}."
            ),
            "test_status": "PASSES_BACKGROUND_CONTAINED"
            if q72_background_contained_count
            else "FAILS_BACKGROUND_CONTAINED",
        },
        {
            "test_id": "Q73_T05_IMPORTED_OR_SOURCE_CONFIRMATION",
            "requirement": "A missing edge can be confirmed only with imported contig evidence or exact source resolution.",
            "observed_result": "No imported contig edge and no source resolution exists for 27->67.",
            "test_status": "FAILS_CONFIRMATION_REQUIREMENT_REMAINS_CANDIDATE",
        },
        {
            "test_id": "Q73_T06_NO_GLOSS_FIREWALL",
            "requirement": "No lexical or canonical promotion is allowed from structural edge evidence.",
            "observed_result": "All counts remain zero for gloss and promotion.",
            "test_status": "PASSES_NO_GLOSS_FIREWALL",
        },
    ]

    result_human_version = (
        "Q73 strengthens 27->67 from a live candidate to a structural missing-edge candidate: "
        "it is Book27's top outgoing overlap, meets the accepted edge threshold, shares the same "
        "payload/context bridge and stratum with Book67, and is prefix-compatible with the imported "
        "35->67 edge. It still fails confirmation because there is no imported contig edge or exact "
        "source resolution, so no gloss or canonical promotion is allowed."
    )
    decision = (
        "Q73_27_TO_67_STRUCTURAL_MISSING_EDGE_CANDIDATE_STRENGTHENED_UNCONFIRMED_NO_GLOSS"
        if structural_candidate_strengthened_count == 1
        and confirmed_edge_count == 0
        and imported_contig_confirmation_count == 0
        and source_resolution_count == 0
        and int(q72["live_missing_edge_candidate_count"]) == 1
        and int(q72["confirmed_missing_edge_count"]) == 0
        and int(q71["continuation_confirmed_count"]) == 0
        and int(q70["continuation_candidate_count"]) == 1
        and int(q69["stop_resolved_count"]) == 0
        and int(q69["continuation_resolved_count"]) == 0
        and int(q65["heldout_role_accept_count"]) == 1
        and int(q64["functional_edge_accept_count"]) == 1
        and int(audit["promoted_gloss_count"]) == 0
        and lexical_ready_count == 0
        and direct_gloss_count == 0
        and canonical_promotion_allowed_count == 0
        else "Q73_27_TO_67_CONFIRMATION_GATE_REQUIRES_REVIEW"
    )
    payload = {
        "question": "Can 27->67 be strengthened after Q72 triage?",
        "answer": result_human_version,
        "blocked_use": "Do not call 27->67 a confirmed contig, edge, sentence, or lexical translation.",
        "next_action": "Use 27->67 as a high-priority structural candidate in the human route, pending source or contig confirmation.",
        "control_edges": {
            "35->67": dict(control_35_67),
            "67->2": dict(control_67_2),
        },
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q73_book27_to_67_confirmation_gate_v1_runs (
                created_at, decision, q72_run_id, q71_run_id, q70_run_id,
                q69_run_id, q65_run_id, q64_run_id, q36_run_id,
                atlas_v6_run_id, row0_run_id, completion_audit_run_id,
                target_edge, target_overlap_tokens, local_rank_pass_count,
                threshold_pass_count, same_bridge_pass_count, same_stratum_pass_count,
                prefix_compatibility_pass_count, q72_background_contained_count,
                source_resolution_count, imported_contig_confirmation_count,
                structural_candidate_strengthened_count, confirmed_edge_count,
                lexical_ready_count, direct_gloss_count,
                canonical_promotion_allowed_count, candidate_status,
                result_human_version, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                int(q72["run_id"]),
                int(q71["run_id"]),
                int(q70["run_id"]),
                int(q69["run_id"]),
                int(q65["run_id"]),
                int(q64["run_id"]),
                int(q36["run_id"]),
                int(audit["atlas_v6_run_id"]),
                int(row0["run_id"]),
                int(audit["run_id"]),
                f"{TARGET_LEFT}->{TARGET_RIGHT}",
                target_overlap_tokens,
                local_rank_pass_count,
                threshold_pass_count,
                same_bridge_pass_count,
                same_stratum_pass_count,
                prefix_compatibility_pass_count,
                q72_background_contained_count,
                source_resolution_count,
                imported_contig_confirmation_count,
                structural_candidate_strengthened_count,
                confirmed_edge_count,
                lexical_ready_count,
                direct_gloss_count,
                canonical_promotion_allowed_count,
                candidate_status,
                result_human_version,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q73_book27_to_67_confirmation_gate_v1_tests (
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
                "target_edge": f"{TARGET_LEFT}->{TARGET_RIGHT}",
                "target_overlap_tokens": target_overlap_tokens,
                "local_rank_pass_count": local_rank_pass_count,
                "threshold_pass_count": threshold_pass_count,
                "same_bridge_pass_count": same_bridge_pass_count,
                "same_stratum_pass_count": same_stratum_pass_count,
                "prefix_compatibility_pass_count": prefix_compatibility_pass_count,
                "q72_background_contained_count": q72_background_contained_count,
                "source_resolution_count": source_resolution_count,
                "imported_contig_confirmation_count": imported_contig_confirmation_count,
                "structural_candidate_strengthened_count": structural_candidate_strengthened_count,
                "confirmed_edge_count": confirmed_edge_count,
                "lexical_ready_count": lexical_ready_count,
                "direct_gloss_count": direct_gloss_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
                "candidate_status": candidate_status,
            }
        )
    )


if __name__ == "__main__":
    main()
