#!/usr/bin/env python3
"""Q49: quarantine Q48 extra C68 subclasses instead of forcing prose."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
EXTRA_CLASSES = {"TAVT_BOUNDARY_WINDOW", "E_EXIT_WINDOW", "TERMINAL_C68_WINDOW"}


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q49_c68_extra_subclass_quarantine_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q48_run_id INTEGER NOT NULL,
            q36_run_id INTEGER NOT NULL,
            c68_subframe_run_id INTEGER NOT NULL,
            c68_dual_partition_run_id INTEGER NOT NULL,
            c68_firewall_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            target_book_count INTEGER NOT NULL,
            extra_observation_count INTEGER NOT NULL,
            subclass_count INTEGER NOT NULL,
            prior_unclassified_count INTEGER NOT NULL,
            prior_held_count INTEGER NOT NULL,
            promoted_extra_subclass_count INTEGER NOT NULL,
            prose_gloss_allowed_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            family_human_version TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q49_c68_extra_subclass_quarantine_v1_items (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            occurrence_index INTEGER NOT NULL,
            q48_window_class TEXT NOT NULL,
            subclass_label TEXT NOT NULL,
            q36_compiled_stratum TEXT NOT NULL,
            q36_likely_speech_act TEXT NOT NULL,
            prior_subframe TEXT NOT NULL,
            prior_operational_status TEXT NOT NULL,
            quarantine_status TEXT NOT NULL,
            human_use TEXT NOT NULL,
            blocked_claims_json TEXT NOT NULL,
            next_action TEXT NOT NULL,
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


def latest_run_id(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT max(run_id) FROM {table}").fetchone()
    if row is None or row[0] is None:
        raise RuntimeError(f"missing required run: {table}")
    return int(row[0])


def q36_book(conn: sqlite3.Connection, run_id: int, bookid: str) -> sqlite3.Row:
    row = conn.execute(
        """
        SELECT *
        FROM human_q36_book_contig_shadow_integration_v1_items
        WHERE run_id=? AND bookid=?
        """,
        (run_id, bookid),
    ).fetchone()
    if row is None:
        raise RuntimeError(f"missing Q36 book {bookid}")
    return row


def subframe_occurrence(conn: sqlite3.Connection, run_id: int, bookid: str, occurrence_index: int) -> sqlite3.Row:
    row = conn.execute(
        """
        SELECT *
        FROM c68_subframe_split_gate_v1_occurrences
        WHERE run_id=? AND bookid=? AND occurrence_index=?
        """,
        (run_id, bookid, occurrence_index),
    ).fetchone()
    if row is None:
        raise RuntimeError(f"missing C68 subframe occurrence {bookid}/{occurrence_index}")
    return row


def dual_occurrence(conn: sqlite3.Connection, run_id: int, bookid: str, occurrence_index: int) -> sqlite3.Row:
    row = conn.execute(
        """
        SELECT *
        FROM c68_dual_subframe_mathemagic_partition_v1_items
        WHERE run_id=? AND bookid=? AND occurrence_index=?
        """,
        (run_id, bookid, occurrence_index),
    ).fetchone()
    if row is None:
        raise RuntimeError(f"missing C68 dual occurrence {bookid}/{occurrence_index}")
    return row


def subclass_label(window_class: str) -> str:
    if window_class == "TAVT_BOUNDARY_WINDOW":
        return "C68_TAVT_BOUNDARY_SUBCLASS"
    if window_class == "E_EXIT_WINDOW":
        return "C68_E_EXIT_SUBCLASS"
    if window_class == "TERMINAL_C68_WINDOW":
        return "C68_TERMINAL_SUBCLASS"
    return "C68_EXTRA_SUBCLASS"


def human_use(window_class: str) -> str:
    if window_class == "TAVT_BOUNDARY_WINDOW":
        return "Use as boundary/continuation audit evidence only; do not fold into phase or slot hinge."
    if window_class == "E_EXIT_WINDOW":
        return "Use as exit/sidecar audit evidence only; compare with residual compiled fragments before any promotion."
    if window_class == "TERMINAL_C68_WINDOW":
        return "Use as terminal/truncation evidence only; it marks an evidence limit, not a translated ending."
    return "Use as extra C68 audit evidence only."


def next_action(window_class: str) -> str:
    if window_class == "TAVT_BOUNDARY_WINDOW":
        return "Compare Book42 TAVT boundary against LTAST/TAVT continuation controls."
    if window_class == "E_EXIT_WINDOW":
        return "Compare Book56 E-exit windows against endpoint and clean-component witnesses."
    if window_class == "TERMINAL_C68_WINDOW":
        return "Keep terminal C68 as truncation/limit until a source bridge explains terminal placement."
    return "Keep quarantined."


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q48 = latest_row(conn, "human_q48_c68_heldout_window_taxonomy_v1_runs")
    q36_run_id = latest_run_id(conn, "human_q36_book_contig_shadow_integration_v1_items")
    c68_subframe_run_id = latest_run_id(conn, "c68_subframe_split_gate_v1_runs")
    c68_dual_run_id = latest_run_id(conn, "c68_dual_subframe_mathemagic_partition_v1_runs")
    c68_firewall = latest_row(conn, "c68_typed_exit_subframe_firewall_v1_runs")
    audit = latest_row(conn, "human_translation_completion_audit_v5_runs")

    q48_extras = list(
        conn.execute(
            """
            SELECT *
            FROM human_q48_c68_heldout_window_taxonomy_v1_observations
            WHERE run_id=? AND split='HELDOUT'
              AND window_class IN ('TAVT_BOUNDARY_WINDOW','E_EXIT_WINDOW','TERMINAL_C68_WINDOW')
            ORDER BY CAST(bookid AS INTEGER), occurrence_index
            """,
            (int(q48["run_id"]),),
        )
    )
    if not q48_extras:
        raise RuntimeError("missing Q48 extra C68 subclasses")

    prepared = []
    for row in q48_extras:
        bookid = str(row["bookid"])
        occurrence_index = int(row["occurrence_index"])
        q36 = q36_book(conn, q36_run_id, bookid)
        subframe = subframe_occurrence(conn, c68_subframe_run_id, bookid, occurrence_index)
        dual = dual_occurrence(conn, c68_dual_run_id, bookid, occurrence_index)
        window_class = str(row["window_class"])
        prepared.append(
            {
                "bookid": bookid,
                "occurrence_index": occurrence_index,
                "q48_window_class": window_class,
                "subclass_label": subclass_label(window_class),
                "q36_compiled_stratum": str(q36["compiled_stratum"]),
                "q36_likely_speech_act": str(q36["likely_speech_act"]),
                "prior_subframe": str(subframe["subframe"]),
                "prior_operational_status": str(dual["operational_status"]),
                "quarantine_status": "QUARANTINED_EXTRA_C68_SUBCLASS_NO_GLOSS",
                "human_use": human_use(window_class),
                "blocked_claims": [
                    "C68_as_word",
                    "forced_phase_slot_fit",
                    "extra_subclass_promotion",
                    "terminal_means_ending",
                    "canonical_plaintext",
                ],
                "next_action": next_action(window_class),
                "evidence": {
                    "q48_observation": dict(row),
                    "q36_book": dict(q36),
                    "c68_subframe_occurrence": dict(subframe),
                    "c68_dual_occurrence": dict(dual),
                },
            }
        )

    prior_unclassified_count = sum(1 for item in prepared if item["prior_subframe"] == "C68_UNCLASSIFIED_CONTEXT")
    prior_held_count = sum(1 for item in prepared if item["prior_operational_status"] == "AUDIT_OR_BOUNDARY_CONTROL_HELD")
    subclass_count = len({item["subclass_label"] for item in prepared})
    promoted_extra_subclass_count = 0
    prose_gloss_allowed_count = 0
    canonical_promotion_allowed_count = 0
    family_human_version = (
        "C68 extra-subclass quarantine: the Q48 extra windows are not failures of the phase-slot hinge and not new prose. "
        "Book42 supplies a TAVT boundary subclass, Book56 supplies E-exit plus terminal subclasses, and Book23 supplies a mixed phase-plus-terminal composition. "
        "All remain audit-only until a separate source bridge explains their placement."
    )
    decision = (
        "Q49_C68_EXTRA_SUBCLASSES_QUARANTINED_NO_GLOSS"
        if int(q48["heldout_extra_class_count"]) == len(prepared) == 5
        and subclass_count == 3
        and prior_unclassified_count == 5
        and prior_held_count == 5
        and int(c68_firewall["decision"].find("NO_GLOSS") >= 0) == 1
        and int(audit["promoted_gloss_count"]) == 0
        and promoted_extra_subclass_count == 0
        and prose_gloss_allowed_count == 0
        and canonical_promotion_allowed_count == 0
        else "Q49_C68_EXTRA_SUBCLASSES_REQUIRES_REVIEW"
    )
    payload = {
        "question": "Can Q48 extra C68 classes be explained without forcing them into the phase-slot hinge?",
        "answer": "Yes. They are already prior-held unclassified contexts and should become quarantined subclasses.",
        "allowed_reading": family_human_version,
        "blocked_reading": "No C68 word meaning, no forced TIIN/TIVV fit, no prose from terminal or E-exit windows.",
        "next_action": "Run separate narrow probes for TAVT boundary and Book56 E-exit if they become high-priority.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q49_c68_extra_subclass_quarantine_v1_runs (
                created_at, decision, q48_run_id, q36_run_id,
                c68_subframe_run_id, c68_dual_partition_run_id,
                c68_firewall_run_id, completion_audit_run_id,
                target_book_count, extra_observation_count, subclass_count,
                prior_unclassified_count, prior_held_count,
                promoted_extra_subclass_count, prose_gloss_allowed_count,
                canonical_promotion_allowed_count, family_human_version,
                payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                int(q48["run_id"]),
                q36_run_id,
                c68_subframe_run_id,
                c68_dual_run_id,
                int(c68_firewall["run_id"]),
                int(audit["run_id"]),
                len({item["bookid"] for item in prepared}),
                len(prepared),
                subclass_count,
                prior_unclassified_count,
                prior_held_count,
                promoted_extra_subclass_count,
                prose_gloss_allowed_count,
                canonical_promotion_allowed_count,
                family_human_version,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q49_c68_extra_subclass_quarantine_v1_items (
                run_id, bookid, occurrence_index, q48_window_class,
                subclass_label, q36_compiled_stratum,
                q36_likely_speech_act, prior_subframe,
                prior_operational_status, quarantine_status, human_use,
                blocked_claims_json, next_action, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    item["bookid"],
                    item["occurrence_index"],
                    item["q48_window_class"],
                    item["subclass_label"],
                    item["q36_compiled_stratum"],
                    item["q36_likely_speech_act"],
                    item["prior_subframe"],
                    item["prior_operational_status"],
                    item["quarantine_status"],
                    item["human_use"],
                    j(item["blocked_claims"]),
                    item["next_action"],
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
                "target_book_count": len({item["bookid"] for item in prepared}),
                "extra_observation_count": len(prepared),
                "subclass_count": subclass_count,
                "prior_unclassified_count": prior_unclassified_count,
                "prior_held_count": prior_held_count,
                "promoted_extra_subclass_count": promoted_extra_subclass_count,
                "prose_gloss_allowed_count": prose_gloss_allowed_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
            }
        )
    )


if __name__ == "__main__":
    main()
