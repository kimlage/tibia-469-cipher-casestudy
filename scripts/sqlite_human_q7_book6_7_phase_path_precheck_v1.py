#!/usr/bin/env python3
"""Q7 precheck: Book6 -> Book7 sequence relation versus Book7 internal direction."""

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


def load_json(value: str | bytes | None, fallback: object) -> object:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q7_book6_7_phase_path_precheck_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            support_count INTEGER NOT NULL,
            control_count INTEGER NOT NULL,
            book_order_direction_support_count INTEGER NOT NULL,
            internal_direction_held_count INTEGER NOT NULL,
            promoted_plaintext_gloss_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q7_book6_7_phase_path_precheck_v1_items (
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


def one(conn: sqlite3.Connection, sql: str, params: tuple[object, ...] = ()) -> sqlite3.Row | None:
    return conn.execute(sql, params).fetchone()


def add_item(
    rows: list[dict[str, object]],
    item_id: str,
    item_type: str,
    source_table: str,
    source_key: str,
    status: str,
    role_label: str,
    support_class: str,
    evidence: object,
) -> None:
    rows.append(
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


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q4_run = latest_id(conn, "human_q4_book7_phase_direction_probe_v1_runs")
    q6_run = latest_id(conn, "human_q6_external_corpus_order_residual_probe_v1_runs")
    shadow_run = latest_id(conn, "human_book7_phase_shadow_probe_v1_items")
    remaining_run = latest_id(conn, "remaining_five_evidence_requirements_v1_items")

    items: list[dict[str, object]] = []

    q6 = one(
        conn,
        """
        SELECT *
        FROM human_q6_external_corpus_order_residual_probe_v1_runs
        WHERE run_id=?
        """,
        (q6_run,),
    )
    if not q6:
        raise RuntimeError("missing Q6 run")
    add_item(
        items,
        "support:q6-external-order",
        "positive_or_control",
        "human_q6_external_corpus_order_residual_probe_v1_runs",
        f"run={q6_run}",
        str(q6["decision"]),
        "external order supports Book6/7 adjacency audit-only",
        "SUPPORT_BOOK_ORDER_DIRECTION_6_TO_7",
        dict(q6),
    )

    q6_relation = one(
        conn,
        """
        SELECT *
        FROM human_q6_external_corpus_order_residual_probe_v1_items
        WHERE run_id=? AND item_id='support:external-order:6-7-adjacent'
        """,
        (q6_run,),
    )
    if not q6_relation:
        raise RuntimeError("missing Q6 6/7 relation item")
    add_item(
        items,
        "support:q6-6-7-relation",
        "positive_or_control",
        "human_q6_external_corpus_order_residual_probe_v1_items",
        f"run={q6_run}:support:external-order:6-7-adjacent",
        str(q6_relation["status"]),
        str(q6_relation["role_label"]),
        "SUPPORT_BOOK6_TO_BOOK7_SEQUENCE_CONTROL",
        dict(q6_relation),
    )

    q4 = one(
        conn,
        """
        SELECT *
        FROM human_q4_book7_phase_direction_probe_v1_runs
        WHERE run_id=?
        """,
        (q4_run,),
    )
    if not q4:
        raise RuntimeError("missing Q4 run")
    add_item(
        items,
        "held:q4-book7-internal-direction",
        "held_direction",
        "human_q4_book7_phase_direction_probe_v1_runs",
        f"run={q4_run}",
        str(q4["decision"]),
        "Book7 internal surface order still blocks NEIAAETTA into TIINNEF claim",
        "HELD_INTERNAL_BOOK7_DIRECTION_NOT_PROMOTED",
        dict(q4),
    )

    for bookid in ("6", "7"):
        shadow = one(
            conn,
            """
            SELECT *
            FROM human_book7_phase_shadow_probe_v1_items
            WHERE run_id=? AND bookid=?
            """,
            (shadow_run, bookid),
        )
        if not shadow:
            raise RuntimeError(f"missing shadow row for Book{bookid}")
        hits = load_json(str(shadow["component_hits_json"]), {})
        add_item(
            items,
            f"support:shadow:{bookid}",
            "positive_or_control",
            "human_book7_phase_shadow_probe_v1_items",
            f"run={shadow_run}:book={bookid}",
            str(shadow["classification"]),
            str(shadow["shadow_implication"]),
            "SUPPORT_CONTINUITY_TO_PHASE_SEQUENCE" if bookid == "7" else "SUPPORT_CONTINUITY_ONLY_CONTROL",
            {"row": dict(shadow), "component_hits": hits},
        )

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
            f"control:remaining:{bookid}",
            "control",
            "remaining_five_evidence_requirements_v1_items",
            f"run={remaining_run}:book={bookid}",
            "REMAINING_REQUIREMENT_STILL_ACTIVE",
            "external order does not clear row0 phase/path requirement",
            "CONTROL_REQUIREMENT_STILL_OPEN",
            dict(remaining) if remaining else {"bookid": bookid, "missing": True},
        )

    support_count = sum(1 for row in items if str(row["support_class"]).startswith("SUPPORT"))
    control_count = sum(1 for row in items if str(row["support_class"]).startswith("CONTROL"))
    book_order_direction_support_count = 1 if q6 and int(q6["adjacency_support_count"]) == 1 else 0
    internal_direction_held_count = 1 if q4 and int(q4["surface_order_conflict_count"]) == 1 else 0
    promoted_plaintext_gloss_count = 0

    decision = (
        "Q7_BOOK6_TO_BOOK7_SEQUENCE_SUPPORTED_INTERNAL_BOOK7_DIRECTION_HELD_NO_GLOSS"
        if support_count >= 4
        and control_count >= 2
        and book_order_direction_support_count == 1
        and internal_direction_held_count == 1
        and promoted_plaintext_gloss_count == 0
        else "Q7_BOOK6_7_PHASE_PATH_REQUIRES_MANUAL_REVIEW"
    )

    payload = {
        "question": "Can Book6 -> Book7 be used as a directional sequence relation while keeping Book7 internal direction held?",
        "answer": (
            "Yes. External corpus order supports Book6 before Book7 as an audit-only sequence relation, "
            "and the internal shadow split supports Book6 as continuity-only control versus Book7 as phase bridge. "
            "But Q4 still blocks the internal Book7 claim that NEIAAETTA directionally becomes TIINNEF."
        ),
        "allowed_reading": "Book6 -> Book7 is a sequence/control relation for phase-path testing.",
        "blocked_reading": "Do not translate Book6, Book7, NEIAAETTA, TIINNEF, or 3478; do not promote Book7 internal surface direction.",
        "next_probe": "Use Book6 -> Book7 as the narrow precheck for row0 phase/path disambiguation with operator selectors and 3478 boundary controls.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q7_book6_7_phase_path_precheck_v1_runs (
                created_at, decision, support_count, control_count,
                book_order_direction_support_count, internal_direction_held_count,
                promoted_plaintext_gloss_count, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                support_count,
                control_count,
                book_order_direction_support_count,
                internal_direction_held_count,
                promoted_plaintext_gloss_count,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q7_book6_7_phase_path_precheck_v1_items (
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
                "support_count": support_count,
                "control_count": control_count,
                "book_order_direction_support_count": book_order_direction_support_count,
                "internal_direction_held_count": internal_direction_held_count,
                "promoted_plaintext_gloss_count": promoted_plaintext_gloss_count,
            }
        )
    )


if __name__ == "__main__":
    main()
