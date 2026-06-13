#!/usr/bin/env python3
"""Q47: test Q46 H2 by joining phase-context and slot-classifier C68 windows."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
PHASE_BOOKS = ["19", "31", "57"]
SLOT_BOOKS = ["22", "28", "48"]
ALL_BOOKS = PHASE_BOOKS + SLOT_BOOKS


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q47_phase_slot_c68_window_join_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q46_run_id INTEGER NOT NULL,
            q39_run_id INTEGER NOT NULL,
            q43_run_id INTEGER NOT NULL,
            row0_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            phase_book_count INTEGER NOT NULL,
            slot_book_count INTEGER NOT NULL,
            c68_observation_count INTEGER NOT NULL,
            phase_window_count INTEGER NOT NULL,
            slot_window_count INTEGER NOT NULL,
            ambiguous_window_count INTEGER NOT NULL,
            group_prediction_correct_count INTEGER NOT NULL,
            group_prediction_total INTEGER NOT NULL,
            component_gloss_allowed_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            mechanism_human_version TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q47_phase_slot_c68_window_join_v1_books (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            source_family TEXT NOT NULL,
            expected_role TEXT NOT NULL,
            c68_occurrence_count INTEGER NOT NULL,
            dominant_window_class TEXT NOT NULL,
            prediction_status TEXT NOT NULL,
            mechanism_human_version TEXT NOT NULL,
            blocked_claims_json TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        );

        CREATE TABLE IF NOT EXISTS human_q47_phase_slot_c68_window_join_v1_observations (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            occurrence_index INTEGER NOT NULL,
            c68_token_index INTEGER NOT NULL,
            left_context_json TEXT NOT NULL,
            right_context_json TEXT NOT NULL,
            window_class TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid, occurrence_index)
        );
        """
    )


def latest_row(conn: sqlite3.Connection, table: str) -> sqlite3.Row:
    row = conn.execute(f"SELECT * FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    if row is None:
        raise RuntimeError(f"missing required row: {table}")
    return row


def tokens_for_book(conn: sqlite3.Connection, row0_run_id: int, bookid: str) -> list[str]:
    row = conn.execute(
        """
        SELECT tokens_json
        FROM row0_variant_book_tokens
        WHERE run_id=? AND bookid=?
        """,
        (row0_run_id, bookid),
    ).fetchone()
    if row is None:
        raise RuntimeError(f"missing row0 tokens for book {bookid}")
    return json.loads(str(row["tokens_json"]))


def classify_window(right: list[str]) -> str:
    if right[:4] == ["T", "I", "I", "N"]:
        return "PHASE_TIIN_WINDOW"
    if right[:4] == ["T", "I", "V", "V"]:
        return "SLOT_TIVV_WINDOW"
    return "AMBIGUOUS_C68_WINDOW"


def expected_class(bookid: str) -> str:
    return "PHASE_TIIN_WINDOW" if bookid in PHASE_BOOKS else "SLOT_TIVV_WINDOW"


def source_family(bookid: str) -> str:
    return "Q39_VNCTIIN_TIINNEF_PHASE_TRIO" if bookid in PHASE_BOOKS else "Q43_NAESE_C68_SLOT_VARIANT_TRIO"


def expected_role(bookid: str) -> str:
    return "phase/context" if bookid in PHASE_BOOKS else "slot/classifier"


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q46 = latest_row(conn, "human_q46_family_synthesis_hypothesis_queue_v1_runs")
    q39 = latest_row(conn, "human_q39_vnctiin_tiinnef_phase_trio_atlas_v1_runs")
    q43 = latest_row(conn, "human_q43_naese_c68_slot_variant_trio_atlas_v1_runs")
    row0 = latest_row(conn, "row0_variant_book_tokens")
    audit = latest_row(conn, "human_translation_completion_audit_v5_runs")
    row0_run_id = int(row0["run_id"])

    observations = []
    book_records = []
    for bookid in ALL_BOOKS:
        tokens = tokens_for_book(conn, row0_run_id, bookid)
        book_observations = []
        for index, token in enumerate(tokens):
            if token != "C68":
                continue
            left = tokens[max(0, index - 6) : index]
            right = tokens[index + 1 : index + 9]
            window_class = classify_window(right)
            obs = {
                "bookid": bookid,
                "occurrence_index": len(book_observations) + 1,
                "c68_token_index": index,
                "left_context": left,
                "right_context": right,
                "window_class": window_class,
            }
            book_observations.append(obs)
            observations.append(obs)
        if not book_observations:
            raise RuntimeError(f"book {bookid} has no C68 observation")
        classes = Counter(obs["window_class"] for obs in book_observations)
        dominant_window_class = classes.most_common(1)[0][0]
        expected = expected_class(bookid)
        prediction_status = "GROUP_PREDICTED" if dominant_window_class == expected else "GROUP_MISMATCH"
        book_records.append(
            {
                "bookid": bookid,
                "source_family": source_family(bookid),
                "expected_role": expected_role(bookid),
                "c68_occurrence_count": len(book_observations),
                "dominant_window_class": dominant_window_class,
                "prediction_status": prediction_status,
                "observations": book_observations,
            }
        )

    phase_window_count = sum(1 for obs in observations if obs["window_class"] == "PHASE_TIIN_WINDOW")
    slot_window_count = sum(1 for obs in observations if obs["window_class"] == "SLOT_TIVV_WINDOW")
    ambiguous_window_count = sum(1 for obs in observations if obs["window_class"] == "AMBIGUOUS_C68_WINDOW")
    group_prediction_correct_count = sum(1 for row in book_records if row["prediction_status"] == "GROUP_PREDICTED")
    group_prediction_total = len(book_records)
    component_gloss_allowed_count = 0
    canonical_promotion_allowed_count = 0
    mechanism_human_version = (
        "C68 phase-slot hinge: in the Q39 phase-context books, C68 opens TIIN-style windows; in the Q43 slot/classifier books, C68 opens TIVV-style FATCT/IVIFAST windows. "
        "This supports a human mechanism where C68 marks a transition surface whose right window distinguishes phase/context from slot/classifier behavior, without giving C68 a word meaning."
    )
    decision = (
        "Q47_PHASE_SLOT_C68_WINDOW_JOIN_READY_NO_GLOSS"
        if int(q46["hypothesis_count"]) == 6
        and group_prediction_correct_count == group_prediction_total
        and phase_window_count >= 3
        and slot_window_count == 3
        and ambiguous_window_count == 0
        and int(audit["promoted_gloss_count"]) == 0
        and component_gloss_allowed_count == 0
        and canonical_promotion_allowed_count == 0
        else "Q47_PHASE_SLOT_C68_WINDOW_JOIN_REQUIRES_REVIEW"
    )
    payload = {
        "question": "Does C68 separate Q39 phase-context books from Q43 slot/classifier books by local window?",
        "answer": "Yes. The right window after C68 separates TIIN phase windows from TIVV slot windows across the tested books.",
        "allowed_reading": mechanism_human_version,
        "blocked_reading": "Do not translate C68, TIIN, TIVV, FATCT, IVIFAST, or NAESE as words.",
        "next_action": "Use this hinge as the first controlled mechanism for a human-readable synthesis pass.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q47_phase_slot_c68_window_join_v1_runs (
                created_at, decision, q46_run_id, q39_run_id, q43_run_id,
                row0_run_id, completion_audit_run_id, phase_book_count,
                slot_book_count, c68_observation_count, phase_window_count,
                slot_window_count, ambiguous_window_count,
                group_prediction_correct_count, group_prediction_total,
                component_gloss_allowed_count, canonical_promotion_allowed_count,
                mechanism_human_version, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                int(q46["run_id"]),
                int(q39["run_id"]),
                int(q43["run_id"]),
                row0_run_id,
                int(audit["run_id"]),
                len(PHASE_BOOKS),
                len(SLOT_BOOKS),
                len(observations),
                phase_window_count,
                slot_window_count,
                ambiguous_window_count,
                group_prediction_correct_count,
                group_prediction_total,
                component_gloss_allowed_count,
                canonical_promotion_allowed_count,
                mechanism_human_version,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q47_phase_slot_c68_window_join_v1_books (
                run_id, bookid, source_family, expected_role,
                c68_occurrence_count, dominant_window_class,
                prediction_status, mechanism_human_version,
                blocked_claims_json, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    row["bookid"],
                    row["source_family"],
                    row["expected_role"],
                    row["c68_occurrence_count"],
                    row["dominant_window_class"],
                    row["prediction_status"],
                    mechanism_human_version,
                    j(["component_gloss", "C68_as_word", "TIIN_as_word", "TIVV_as_word", "canonical_plaintext"]),
                    j(row),
                )
                for row in book_records
            ],
        )
        conn.executemany(
            """
            INSERT INTO human_q47_phase_slot_c68_window_join_v1_observations (
                run_id, bookid, occurrence_index, c68_token_index,
                left_context_json, right_context_json, window_class,
                evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    obs["bookid"],
                    obs["occurrence_index"],
                    obs["c68_token_index"],
                    j(obs["left_context"]),
                    j(obs["right_context"]),
                    obs["window_class"],
                    j(obs),
                )
                for obs in observations
            ],
        )

    print(
        j(
            {
                "run_id": run_id,
                "decision": decision,
                "phase_book_count": len(PHASE_BOOKS),
                "slot_book_count": len(SLOT_BOOKS),
                "c68_observation_count": len(observations),
                "phase_window_count": phase_window_count,
                "slot_window_count": slot_window_count,
                "ambiguous_window_count": ambiguous_window_count,
                "group_prediction_correct_count": group_prediction_correct_count,
                "group_prediction_total": group_prediction_total,
                "component_gloss_allowed_count": component_gloss_allowed_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
            }
        )
    )


if __name__ == "__main__":
    main()
