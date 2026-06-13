#!/usr/bin/env python3
"""Q11 retriage: residual frontier after Q9/Q10 current-table closures."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q11_residual_frontier_retriage_after_q9_q10_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            remaining_item_count INTEGER NOT NULL,
            remaining_actionable_count INTEGER NOT NULL,
            current_table_exhausted_count INTEGER NOT NULL,
            local_sqlite_rerun_candidate_count INTEGER NOT NULL,
            new_external_or_ingame_evidence_required_count INTEGER NOT NULL,
            promoted_plaintext_gloss_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q11_residual_frontier_retriage_after_q9_q10_v1_items (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            prior_blocker_class TEXT NOT NULL,
            retriage_status TEXT NOT NULL,
            local_sqlite_rerun_allowed INTEGER NOT NULL,
            new_evidence_required INTEGER NOT NULL,
            safest_next_route TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        );
        """
    )


def latest_id(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT max(run_id) FROM {table}").fetchone()
    if row is None or row[0] is None:
        raise RuntimeError(f"missing required run: {table}")
    return int(row[0])


def optional_latest_id(conn: sqlite3.Connection, table: str) -> int | None:
    exists = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone()
    if not exists:
        return None
    row = conn.execute(f"SELECT max(run_id) FROM {table}").fetchone()
    if row is None or row[0] is None:
        return None
    return int(row[0])


def one(conn: sqlite3.Connection, sql: str, params: tuple[object, ...] = ()) -> sqlite3.Row | None:
    return conn.execute(sql, params).fetchone()


def rows(conn: sqlite3.Connection, sql: str, params: tuple[object, ...] = ()) -> list[sqlite3.Row]:
    return list(conn.execute(sql, params).fetchall())


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    remaining_run = latest_id(conn, "remaining_five_evidence_requirements_v1_items")
    q9_run = latest_id(conn, "human_q9_book6_7_heldout_support_audit_v1_runs")
    q10_run = latest_id(conn, "human_q10_book32_36_display_payload_independence_audit_v1_runs")
    completion_run = latest_id(conn, "human_translation_completion_audit_v5_runs")
    mathemagic_run = optional_latest_id(conn, "human_mathemagic_shadow_synthesis_v1_runs")

    q9 = one(
        conn,
        "SELECT * FROM human_q9_book6_7_heldout_support_audit_v1_runs WHERE run_id=?",
        (q9_run,),
    )
    q10 = one(
        conn,
        "SELECT * FROM human_q10_book32_36_display_payload_independence_audit_v1_runs WHERE run_id=?",
        (q10_run,),
    )
    completion = one(
        conn,
        "SELECT * FROM human_translation_completion_audit_v5_runs WHERE run_id=?",
        (completion_run,),
    )
    mathemagic = (
        one(conn, "SELECT * FROM human_mathemagic_shadow_synthesis_v1_runs WHERE run_id=?", (mathemagic_run,))
        if mathemagic_run is not None
        else None
    )

    remaining = rows(
        conn,
        """
        SELECT *
        FROM remaining_five_evidence_requirements_v1_items
        WHERE run_id=?
        ORDER BY CAST(bookid AS INTEGER)
        """,
        (remaining_run,),
    )
    if not remaining:
        raise RuntimeError("missing remaining-five rows")

    items: list[dict[str, object]] = []
    for row in remaining:
        bookid = str(row["bookid"])
        blocker = str(row["blocker_class"])
        evidence: dict[str, object] = {
            "remaining_run": remaining_run,
            "remaining": dict(row),
            "completion_run": dict(completion) if completion else None,
        }

        if bookid in {"6", "7"}:
            status = "CURRENT_TABLE_ROUTE_EXHAUSTED_BY_Q9_KEEP_CONTROL_NO_GLOSS"
            rerun_allowed = 0
            new_required = 1
            next_route = (
                "Seek a new independent in-game phrase, external artifact, or semantic anchor for Book6/7; "
                "do not rerun current contig/overlap/literal/similarity confirmation."
            )
            evidence["q9"] = dict(q9) if q9 else None
        elif bookid in {"32", "36"}:
            status = "CURRENT_TABLE_ROUTE_EXHAUSTED_BY_Q10_CLOSE_DISPLAY_CONTROL_NO_GLOSS"
            rerun_allowed = 0
            new_required = 1
            next_route = (
                "Seek a new independent payload boundary or in-game phrase for display residuals; "
                "do not rerun current display-tail/drift/concordance confirmation."
            )
            evidence["q10"] = dict(q10) if q10 else None
        elif bookid == "14":
            status = "HELD_R02_LTAST_NO_IMMEDIATE_RERUN"
            rerun_allowed = 0
            new_required = 1
            next_route = "Hold unless new R02/LTAST phase evidence beats the failed weak boundary gate."
        else:
            status = "UNCLASSIFIED_REMAINING_REVIEW"
            rerun_allowed = int(row["immediately_actionable"])
            new_required = 1
            next_route = str(row["safest_next_probe"])

        items.append(
            {
                "bookid": bookid,
                "prior_blocker_class": blocker,
                "retriage_status": status,
                "local_sqlite_rerun_allowed": rerun_allowed,
                "new_evidence_required": new_required,
                "safest_next_route": next_route,
                "evidence_json": j(evidence),
            }
        )

    remaining_item_count = len(items)
    remaining_actionable_count = sum(int(row["immediately_actionable"]) for row in remaining)
    current_table_exhausted_count = sum(1 for item in items if str(item["retriage_status"]).startswith("CURRENT_TABLE_ROUTE_EXHAUSTED"))
    local_sqlite_rerun_candidate_count = sum(int(item["local_sqlite_rerun_allowed"]) for item in items)
    new_external_or_ingame_evidence_required_count = sum(int(item["new_evidence_required"]) for item in items)
    promoted_plaintext_gloss_count = int(completion["promoted_gloss_count"]) if completion else 0

    decision = (
        "Q11_CURRENT_TABLE_FRONTIER_EXHAUSTED_NEED_NEW_INGAME_OR_EXTERNAL_ANCHORS_NO_GLOSS"
        if remaining_item_count == 5
        and current_table_exhausted_count == 4
        and local_sqlite_rerun_candidate_count == 0
        and new_external_or_ingame_evidence_required_count == 5
        and promoted_plaintext_gloss_count == 0
        else "Q11_RESIDUAL_FRONTIER_RETRIAGE_REQUIRES_MANUAL_REVIEW"
    )

    payload = {
        "question": "After Q9 and Q10, what residual work remains that is not just repeating current SQLite evidence?",
        "answer": (
            "The current local SQLite confirmation frontier is exhausted. Books 6/7 are useful controls but lack held-out pair support; "
            "Books 32/36 are closed as display controls; Book14 remains held until new R02/LTAST phase evidence appears."
        ),
        "next_routes": [
            "Build or import new in-game anchor evidence from books, NPC lines, quest text, or exact external captures.",
            "Use Mathemagic only as operator/selector machinery, not as a plaintext dictionary.",
            "Reopen local probes only after a new artifact changes the evidence graph.",
        ],
        "mathemagic_context": dict(mathemagic) if mathemagic else None,
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q11_residual_frontier_retriage_after_q9_q10_v1_runs (
                created_at, decision, remaining_item_count, remaining_actionable_count,
                current_table_exhausted_count, local_sqlite_rerun_candidate_count,
                new_external_or_ingame_evidence_required_count, promoted_plaintext_gloss_count,
                payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                remaining_item_count,
                remaining_actionable_count,
                current_table_exhausted_count,
                local_sqlite_rerun_candidate_count,
                new_external_or_ingame_evidence_required_count,
                promoted_plaintext_gloss_count,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q11_residual_frontier_retriage_after_q9_q10_v1_items (
                run_id, bookid, prior_blocker_class, retriage_status,
                local_sqlite_rerun_allowed, new_evidence_required,
                safest_next_route, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    str(item["bookid"]),
                    str(item["prior_blocker_class"]),
                    str(item["retriage_status"]),
                    int(item["local_sqlite_rerun_allowed"]),
                    int(item["new_evidence_required"]),
                    str(item["safest_next_route"]),
                    str(item["evidence_json"]),
                )
                for item in items
            ],
        )

    print(
        j(
            {
                "run_id": run_id,
                "decision": decision,
                "remaining_item_count": remaining_item_count,
                "remaining_actionable_count": remaining_actionable_count,
                "current_table_exhausted_count": current_table_exhausted_count,
                "local_sqlite_rerun_candidate_count": local_sqlite_rerun_candidate_count,
                "new_external_or_ingame_evidence_required_count": new_external_or_ingame_evidence_required_count,
                "promoted_plaintext_gloss_count": promoted_plaintext_gloss_count,
            }
        )
    )


if __name__ == "__main__":
    main()
