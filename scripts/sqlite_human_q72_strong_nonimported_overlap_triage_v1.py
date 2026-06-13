#!/usr/bin/env python3
"""Q72: triage strong non-imported row0 overlaps from Q71."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
TARGET_PAIR = ("27", "67")


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q72_strong_nonimported_overlap_triage_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q71_run_id INTEGER NOT NULL,
            q70_run_id INTEGER NOT NULL,
            q69_run_id INTEGER NOT NULL,
            q36_run_id INTEGER NOT NULL,
            atlas_v6_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            strong_nonimported_pair_count INTEGER NOT NULL,
            target_pair_count INTEGER NOT NULL,
            known_local_or_variant_background_count INTEGER NOT NULL,
            imported_to_noncontig_background_count INTEGER NOT NULL,
            noncontig_to_imported_background_count INTEGER NOT NULL,
            live_missing_edge_candidate_count INTEGER NOT NULL,
            confirmed_missing_edge_count INTEGER NOT NULL,
            target_candidate_status TEXT NOT NULL,
            lexical_ready_count INTEGER NOT NULL,
            direct_gloss_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            result_human_version TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q72_strong_nonimported_overlap_triage_v1_pairs (
            run_id INTEGER NOT NULL,
            nonimported_rank INTEGER NOT NULL,
            left_bookid TEXT NOT NULL,
            right_bookid TEXT NOT NULL,
            overlap_tokens INTEGER NOT NULL,
            left_contig_status TEXT NOT NULL,
            right_contig_status TEXT NOT NULL,
            left_stratum TEXT NOT NULL,
            right_stratum TEXT NOT NULL,
            left_bridge_id TEXT NOT NULL,
            right_bridge_id TEXT NOT NULL,
            triage_class TEXT NOT NULL,
            triage_status TEXT NOT NULL,
            next_action TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, nonimported_rank, left_bookid, right_bookid)
        );
        """
    )


def latest_row(conn: sqlite3.Connection, table: str) -> sqlite3.Row:
    row = conn.execute(f"SELECT * FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    if row is None:
        raise RuntimeError(f"missing required row: {table}")
    return row


def load_q36(conn: sqlite3.Connection, q36_run_id: int) -> dict[str, sqlite3.Row]:
    rows = conn.execute(
        """
        SELECT bookid, compiled_stratum, likely_speech_act, contig_status,
               basecontigid, contig_booksinorder, priority_class, promotion_status
        FROM human_q36_book_contig_shadow_integration_v1_items
        WHERE run_id=?
        """,
        (q36_run_id,),
    ).fetchall()
    return {str(row["bookid"]): row for row in rows}


def load_atlas(conn: sqlite3.Connection, atlas_run_id: int) -> dict[str, sqlite3.Row]:
    rows = conn.execute(
        """
        SELECT target_id, confidence_tier, source_bridge_id, likely_speech_act,
               support_level, promotion_status
        FROM human_translation_atlas_v6_items
        WHERE run_id=? AND target_kind='book'
        """,
        (atlas_run_id,),
    ).fetchall()
    return {str(row["target_id"]): row for row in rows}


def strong_nonimported_pairs(conn: sqlite3.Connection, q71_run_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT nonimported_rank, left_bookid, right_bookid, overlap_tokens,
               overlap_token_text, pair_class
        FROM human_q71_book27_to_67_false_overlap_gate_v1_background
        WHERE run_id=? AND imported_contig_edge=0 AND overlap_tokens >= 34
        ORDER BY nonimported_rank
        """,
        (q71_run_id,),
    ).fetchall()


def has_no_exact_contig(row: sqlite3.Row) -> bool:
    return str(row["contig_status"]) == "NO_EXACT_CONTIG_SHADOW"


def has_exact_contig(row: sqlite3.Row) -> bool:
    return str(row["contig_status"]) == "EXACT_CONTIG_SHADOW_AVAILABLE"


def classify_pair(
    pair: sqlite3.Row,
    left_q36: sqlite3.Row,
    right_q36: sqlite3.Row,
    left_atlas: sqlite3.Row,
    right_atlas: sqlite3.Row,
) -> tuple[str, str, str]:
    left = str(pair["left_bookid"])
    right = str(pair["right_bookid"])
    if (left, right) == TARGET_PAIR:
        return (
            "TARGET_STRONG_LOCAL_CONTINUATION_CANDIDATE",
            "LIVE_UNCONFIRMED_CANDIDATE_NO_GLOSS",
            "Run a dedicated 27->67 confirmation gate with contig reconstruction, not source prose.",
        )
    if has_exact_contig(left_q36) and has_no_exact_contig(right_q36):
        return (
            "IMPORTED_TO_NONCONTIG_VARIANT_BACKGROUND",
            "BACKGROUND_NOT_CONFIRMED_EDGE",
            "Use as false-overlap background unless the right book gains independent contig evidence.",
        )
    if has_no_exact_contig(left_q36) and has_exact_contig(right_q36):
        if str(left_atlas["source_bridge_id"]) == "B_BENNA_FORMULA_BODY":
            return (
                "KNOWN_LOCAL_FORMULA_CONTROL_TO_IMPORTED_BACKGROUND",
                "KNOWN_NO_EDGE_CONTROL",
                "Keep as BENNA local-control background; do not reopen as contig without new evidence.",
            )
        return (
            "NONCONTIG_TO_IMPORTED_VARIANT_BACKGROUND",
            "BACKGROUND_NOT_CONFIRMED_EDGE",
            "Use as candidate background; require independent contig or source evidence before promotion.",
        )
    if has_no_exact_contig(left_q36) and has_no_exact_contig(right_q36):
        if str(left_atlas["source_bridge_id"]) == str(right_atlas["source_bridge_id"]):
            return (
                "KNOWN_SAME_BRIDGE_NONCONTIG_BACKGROUND",
                "BACKGROUND_NOT_CONFIRMED_EDGE",
                "Keep as same-bridge variant background; no edge promotion.",
            )
        return (
            "NONCONTIG_TO_NONCONTIG_BACKGROUND",
            "BACKGROUND_NOT_CONFIRMED_EDGE",
            "Hold for later family-level triage.",
        )
    return (
        "UNCLASSIFIED_STRONG_NONIMPORTED_OVERLAP",
        "REQUIRES_REVIEW",
        "Inspect manually before using as a control.",
    )


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q71 = latest_row(conn, "human_q71_book27_to_67_false_overlap_gate_v1_runs")
    q70 = latest_row(conn, "human_q70_book27_sequence_neighbor_scan_v1_runs")
    q69 = latest_row(conn, "human_q69_book27_stop_continue_source_check_v1_runs")
    q36 = latest_row(conn, "human_q36_book_contig_shadow_integration_v1_runs")
    audit = latest_row(conn, "human_translation_completion_audit_v5_runs")
    q36_items = load_q36(conn, int(q36["run_id"]))
    atlas_items = load_atlas(conn, int(audit["atlas_v6_run_id"]))
    pairs = strong_nonimported_pairs(conn, int(q71["run_id"]))

    pair_rows = []
    for pair in pairs:
        left = str(pair["left_bookid"])
        right = str(pair["right_bookid"])
        left_q36 = q36_items[left]
        right_q36 = q36_items[right]
        left_atlas = atlas_items[left]
        right_atlas = atlas_items[right]
        triage_class, triage_status, next_action = classify_pair(pair, left_q36, right_q36, left_atlas, right_atlas)
        pair_rows.append(
            {
                "nonimported_rank": int(pair["nonimported_rank"]),
                "left_bookid": left,
                "right_bookid": right,
                "overlap_tokens": int(pair["overlap_tokens"]),
                "left_contig_status": str(left_q36["contig_status"]),
                "right_contig_status": str(right_q36["contig_status"]),
                "left_stratum": str(left_q36["compiled_stratum"]),
                "right_stratum": str(right_q36["compiled_stratum"]),
                "left_bridge_id": str(left_atlas["source_bridge_id"]),
                "right_bridge_id": str(right_atlas["source_bridge_id"]),
                "triage_class": triage_class,
                "triage_status": triage_status,
                "next_action": next_action,
                "evidence": {
                    "q71_pair": dict(pair),
                    "left_q36": dict(left_q36),
                    "right_q36": dict(right_q36),
                    "left_atlas": dict(left_atlas),
                    "right_atlas": dict(right_atlas),
                },
            }
        )

    strong_nonimported_pair_count = len(pair_rows)
    target_pair_count = sum(1 for row in pair_rows if row["triage_class"] == "TARGET_STRONG_LOCAL_CONTINUATION_CANDIDATE")
    known_local_or_variant_background_count = sum(
        1
        for row in pair_rows
        if row["triage_class"]
        in {
            "KNOWN_LOCAL_FORMULA_CONTROL_TO_IMPORTED_BACKGROUND",
            "KNOWN_SAME_BRIDGE_NONCONTIG_BACKGROUND",
            "IMPORTED_TO_NONCONTIG_VARIANT_BACKGROUND",
            "NONCONTIG_TO_IMPORTED_VARIANT_BACKGROUND",
            "NONCONTIG_TO_NONCONTIG_BACKGROUND",
        }
    )
    imported_to_noncontig_background_count = sum(
        1 for row in pair_rows if row["triage_class"] == "IMPORTED_TO_NONCONTIG_VARIANT_BACKGROUND"
    )
    noncontig_to_imported_background_count = sum(
        1
        for row in pair_rows
        if row["triage_class"]
        in {"NONCONTIG_TO_IMPORTED_VARIANT_BACKGROUND", "KNOWN_LOCAL_FORMULA_CONTROL_TO_IMPORTED_BACKGROUND"}
    )
    live_missing_edge_candidate_count = target_pair_count
    confirmed_missing_edge_count = 0
    target_candidate_status = "LIVE_UNCONFIRMED_CANDIDATE_NO_GLOSS"
    lexical_ready_count = 0
    direct_gloss_count = 0
    canonical_promotion_allowed_count = 0

    result_human_version = (
        "Q72 triages the seven strong non-imported overlaps from Q71: six are background or known "
        "variant/control overlaps under existing q36/atlas statuses, while 27->67 remains the only "
        "live missing-edge candidate. It is still unconfirmed and carries no gloss."
    )
    decision = (
        "Q72_STRONG_NONIMPORTED_OVERLAP_TRIAGE_27_TO_67_ONLY_LIVE_CANDIDATE_NO_GLOSS"
        if strong_nonimported_pair_count == 7
        and target_pair_count == 1
        and known_local_or_variant_background_count == 6
        and imported_to_noncontig_background_count == 2
        and noncontig_to_imported_background_count == 3
        and live_missing_edge_candidate_count == 1
        and confirmed_missing_edge_count == 0
        and int(q71["continuation_candidate_count"]) == 1
        and int(q71["continuation_confirmed_count"]) == 0
        and int(q70["continuation_candidate_count"]) == 1
        and int(q69["stop_resolved_count"]) == 0
        and int(q69["continuation_resolved_count"]) == 0
        and int(audit["promoted_gloss_count"]) == 0
        and lexical_ready_count == 0
        and direct_gloss_count == 0
        and canonical_promotion_allowed_count == 0
        else "Q72_STRONG_NONIMPORTED_OVERLAP_TRIAGE_REQUIRES_REVIEW"
    )
    payload = {
        "question": "Are the stronger non-imported overlaps missing contigs or false-overlap background?",
        "answer": result_human_version,
        "blocked_use": "Do not confirm 27->67 or any other non-imported overlap from row0 overlap alone.",
        "next_action": "Run a focused confirmation gate for 27->67 now that stronger backgrounds are classified.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q72_strong_nonimported_overlap_triage_v1_runs (
                created_at, decision, q71_run_id, q70_run_id, q69_run_id,
                q36_run_id, atlas_v6_run_id, completion_audit_run_id,
                strong_nonimported_pair_count, target_pair_count,
                known_local_or_variant_background_count,
                imported_to_noncontig_background_count,
                noncontig_to_imported_background_count,
                live_missing_edge_candidate_count, confirmed_missing_edge_count,
                target_candidate_status, lexical_ready_count, direct_gloss_count,
                canonical_promotion_allowed_count, result_human_version,
                payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                int(q71["run_id"]),
                int(q70["run_id"]),
                int(q69["run_id"]),
                int(q36["run_id"]),
                int(audit["atlas_v6_run_id"]),
                int(audit["run_id"]),
                strong_nonimported_pair_count,
                target_pair_count,
                known_local_or_variant_background_count,
                imported_to_noncontig_background_count,
                noncontig_to_imported_background_count,
                live_missing_edge_candidate_count,
                confirmed_missing_edge_count,
                target_candidate_status,
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
            INSERT INTO human_q72_strong_nonimported_overlap_triage_v1_pairs (
                run_id, nonimported_rank, left_bookid, right_bookid,
                overlap_tokens, left_contig_status, right_contig_status,
                left_stratum, right_stratum, left_bridge_id, right_bridge_id,
                triage_class, triage_status, next_action, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    row["nonimported_rank"],
                    row["left_bookid"],
                    row["right_bookid"],
                    row["overlap_tokens"],
                    row["left_contig_status"],
                    row["right_contig_status"],
                    row["left_stratum"],
                    row["right_stratum"],
                    row["left_bridge_id"],
                    row["right_bridge_id"],
                    row["triage_class"],
                    row["triage_status"],
                    row["next_action"],
                    j(row["evidence"]),
                )
                for row in pair_rows
            ],
        )

    print(
        j(
            {
                "run_id": run_id,
                "decision": decision,
                "strong_nonimported_pair_count": strong_nonimported_pair_count,
                "target_pair_count": target_pair_count,
                "known_local_or_variant_background_count": known_local_or_variant_background_count,
                "imported_to_noncontig_background_count": imported_to_noncontig_background_count,
                "noncontig_to_imported_background_count": noncontig_to_imported_background_count,
                "live_missing_edge_candidate_count": live_missing_edge_candidate_count,
                "confirmed_missing_edge_count": confirmed_missing_edge_count,
                "target_candidate_status": target_candidate_status,
                "lexical_ready_count": lexical_ready_count,
                "direct_gloss_count": direct_gloss_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
            }
        )
    )


if __name__ == "__main__":
    main()
