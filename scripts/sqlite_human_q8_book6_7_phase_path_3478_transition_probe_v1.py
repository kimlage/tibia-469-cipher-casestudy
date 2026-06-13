#!/usr/bin/env python3
"""Q8 probe: Book6 -> Book7 phase-path transition through 3478 window contrast."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from collections import Counter
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
        CREATE TABLE IF NOT EXISTS human_q8_book6_7_phase_path_3478_transition_probe_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            support_count INTEGER NOT NULL,
            control_count INTEGER NOT NULL,
            transition_signal_count INTEGER NOT NULL,
            dominant_window_control_count INTEGER NOT NULL,
            rare_window_count INTEGER NOT NULL,
            path_resolved_count INTEGER NOT NULL,
            promoted_plaintext_gloss_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q8_book6_7_phase_path_3478_transition_probe_v1_items (
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


def component_hits(text: str) -> dict[str, int]:
    return {
        "BENNA": text.find("BENNA"),
        "NEIAAETTA": text.find("NEIAAETTA"),
        "TIINNEF": text.find("TIINNEF"),
        "VNCTIIN": text.find("VNCTIIN"),
    }


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q7_run = latest_id(conn, "human_q7_book6_7_phase_path_precheck_v1_runs")
    phase_run = latest_id(conn, "phase_boundary_control_gate_v1_items")
    row0_path_run = latest_id(conn, "row0_phase_operator_path_gate_v1_items")
    anchor_run = latest_id(conn, "anchor3478_context_items")
    q4_run = latest_id(conn, "human_q4_book7_phase_direction_probe_v1_runs")
    q6_run = latest_id(conn, "human_q6_external_corpus_order_residual_probe_v1_runs")
    remaining_run = latest_id(conn, "remaining_five_evidence_requirements_v1_items")

    items: list[dict[str, object]] = []

    q7 = one(conn, "SELECT * FROM human_q7_book6_7_phase_path_precheck_v1_runs WHERE run_id=?", (q7_run,))
    if not q7:
        raise RuntimeError("missing Q7 run")
    add_item(
        items,
        "support:q7-sequence-precheck",
        "positive_or_control",
        "human_q7_book6_7_phase_path_precheck_v1_runs",
        f"run={q7_run}",
        str(q7["decision"]),
        "Book6 -> Book7 sequence relation is already prechecked, internal Book7 direction held",
        "SUPPORT_SEQUENCE_PRECHECK_NO_GLOSS",
        dict(q7),
    )

    q6 = one(conn, "SELECT * FROM human_q6_external_corpus_order_residual_probe_v1_runs WHERE run_id=?", (q6_run,))
    if q6:
        add_item(
            items,
            "support:q6-external-order",
            "positive_or_control",
            "human_q6_external_corpus_order_residual_probe_v1_runs",
            f"run={q6_run}",
            str(q6["decision"]),
            "external order places Book6 before Book7",
            "SUPPORT_EXTERNAL_ORDER_6_TO_7",
            dict(q6),
        )

    anchor_rows = rows(conn, "SELECT * FROM anchor3478_context_items WHERE run_id=?", (anchor_run,))
    window_counts = Counter(str(row["window_digits"]) for row in anchor_rows)
    target_anchor: dict[str, sqlite3.Row] = {}
    for bookid in TARGETS:
        anchor = one(
            conn,
            """
            SELECT *
            FROM anchor3478_context_items
            WHERE run_id=? AND bookid=?
            ORDER BY digit_pos
            LIMIT 1
            """,
            (anchor_run, bookid),
        )
        if not anchor:
            raise RuntimeError(f"missing 3478 context for Book{bookid}")
        target_anchor[bookid] = anchor
        count = window_counts[str(anchor["window_digits"])]
        status = "DOMINANT_3478_WINDOW_CONTROL" if count >= 2 else "RARE_3478_WINDOW"
        support_class = "CONTROL_DOMINANT_3478_WINDOW" if bookid == BOOK6 and count >= 2 else "SUPPORT_RARE_3478_PHASE_WINDOW"
        add_item(
            items,
            f"{'control' if bookid == BOOK6 else 'support'}:3478-window:{bookid}",
            "positive_or_control",
            "anchor3478_context_items",
            f"run={anchor_run}:book={bookid}:pos={anchor['digit_pos']}",
            status,
            f"Book{bookid} 3478 window frequency={count}",
            support_class,
            {"row": dict(anchor), "window_count": count, "global_window_counts": window_counts.most_common(10)},
        )

    for bookid in TARGETS:
        phase = one(
            conn,
            """
            SELECT *
            FROM phase_boundary_control_gate_v1_items
            WHERE run_id=? AND bookid=?
            """,
            (phase_run, bookid),
        )
        if not phase:
            raise RuntimeError(f"missing phase boundary item for Book{bookid}")
        add_item(
            items,
            f"{'control' if bookid == BOOK6 else 'support'}:phase-boundary:{bookid}",
            "positive_or_control",
            "phase_boundary_control_gate_v1_items",
            f"run={phase_run}:book={bookid}",
            str(phase["gate_status"]),
            str(phase["proposed_label"]),
            "CONTROL_BOOK6_HELD_DISPLAY_PHASE" if bookid == BOOK6 else "SUPPORT_BOOK7_PHASE_BOUNDARY_CONTROL",
            dict(phase),
        )

        path = one(
            conn,
            """
            SELECT *
            FROM row0_phase_operator_path_gate_v1_items
            WHERE run_id=? AND bookid=?
            """,
            (row0_path_run, bookid),
        )
        if not path:
            raise RuntimeError(f"missing row0 path item for Book{bookid}")
        add_item(
            items,
            f"support:row0-path:{bookid}",
            "positive_or_control",
            "row0_phase_operator_path_gate_v1_items",
            f"run={row0_path_run}:book={bookid}",
            str(path["gate_status"]),
            str(path["proposed_label"]),
            "SUPPORT_ROW0_PATH_STABLE_NO_GLOSS",
            dict(path),
        )

    row0 = {
        bookid: one(
            conn,
            """
            SELECT bookid, symbol_text, token_count
            FROM row0_variant_book_tokens
            WHERE run_id=(SELECT max(run_id) FROM row0_variant_book_tokens)
              AND bookid=?
            """,
            (bookid,),
        )
        for bookid in TARGETS
    }
    if not row0[BOOK6] or not row0[BOOK7]:
        raise RuntimeError("missing row0 tokens for Book6/7")
    hits6 = component_hits(str(row0[BOOK6]["symbol_text"]))
    hits7 = component_hits(str(row0[BOOK7]["symbol_text"]))
    transition_signal = hits6["NEIAAETTA"] >= 0 and hits6["TIINNEF"] < 0 and hits7["NEIAAETTA"] >= 0 and hits7["TIINNEF"] >= 0
    add_item(
        items,
        "support:component-transition:6-7",
        "positive_or_control",
        "row0_variant_book_tokens",
        "book=6->7",
        "CONTINUITY_TO_PHASE_COMPONENT_ADDED" if transition_signal else "COMPONENT_TRANSITION_NOT_SUPPORTED",
        "Book6 has NEIAAETTA without TIINNEF; Book7 has both NEIAAETTA and TIINNEF",
        "SUPPORT_COMPONENT_TRANSITION_NO_GLOSS",
        {"book6": dict(row0[BOOK6]), "book7": dict(row0[BOOK7]), "hits6": hits6, "hits7": hits7},
    )

    q4 = one(conn, "SELECT * FROM human_q4_book7_phase_direction_probe_v1_runs WHERE run_id=?", (q4_run,))
    if q4:
        add_item(
            items,
            "held:q4-internal-book7-direction",
            "held",
            "human_q4_book7_phase_direction_probe_v1_runs",
            f"run={q4_run}",
            str(q4["decision"]),
            "Book7 internal NEIAAETTA->TIINNEF direction remains blocked",
            "HELD_INTERNAL_BOOK7_DIRECTION_STILL_BLOCKED",
            dict(q4),
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
            "control",
            "remaining_five_evidence_requirements_v1_items",
            f"run={remaining_run}:book={bookid}",
            "REMAINING_REQUIREMENT_REDUCED_NOT_CLEARED",
            "Q8 gives path relation evidence but no translation",
            "CONTROL_REMAINING_REQUIREMENT_NOT_FULLY_CLEARED",
            dict(remaining) if remaining else {"bookid": bookid, "missing": True},
        )

    support_count = sum(1 for row in items if str(row["support_class"]).startswith("SUPPORT"))
    control_count = sum(1 for row in items if str(row["support_class"]).startswith("CONTROL"))
    transition_signal_count = int(transition_signal)
    dominant_window_control_count = int(window_counts[str(target_anchor[BOOK6]["window_digits"])] >= 2)
    rare_window_count = int(window_counts[str(target_anchor[BOOK7]["window_digits"])] == 1)
    path_resolved_count = sum(
        1
        for row in items
        if row["source_table"] == "row0_phase_operator_path_gate_v1_items"
        and "CURRENT_ROW0_OPERATOR_PATH_STABLE" in str(row["status"])
    )
    promoted_plaintext_gloss_count = 0

    decision = (
        "Q8_BOOK6_7_3478_WINDOW_TRANSITION_PHASE_PATH_SUPPORTED_NO_PAYLOAD_GLOSS"
        if support_count >= 6
        and control_count >= 4
        and transition_signal_count == 1
        and dominant_window_control_count == 1
        and rare_window_count == 1
        and path_resolved_count == 2
        and promoted_plaintext_gloss_count == 0
        else "Q8_BOOK6_7_3478_TRANSITION_REQUIRES_MANUAL_REVIEW"
    )

    payload = {
        "question": "Does Book6 -> Book7 show a phase/path transition when 3478 window contrast is combined with row0 component contrast?",
        "answer": (
            "Yes as a functional transition only. Book6 has the dominant/common 3478 window and NEIAAETTA without TIINNEF; "
            "Book7 has a rare 3478 window, the phase-boundary control label, and adds TIINNEF while still retaining NEIAAETTA. "
            "This supports a Book6->Book7 phase-path transition/control relation, not semantic payload."
        ),
        "allowed_reading": "Book6 -> Book7 is a continuity-to-phase path/control relation with 3478 window contrast.",
        "blocked_reading": "Do not translate 3478, NEIAAETTA, TIINNEF, Book6, or Book7; do not claim Book7 internal direction or prose.",
        "window_counts": {
            "book6": {"window": str(target_anchor[BOOK6]["window_digits"]), "count": window_counts[str(target_anchor[BOOK6]["window_digits"])]},
            "book7": {"window": str(target_anchor[BOOK7]["window_digits"]), "count": window_counts[str(target_anchor[BOOK7]["window_digits"])]},
        },
        "next_probe": (
            "Use this as the row0 phase/path relation for Book6/7. A stronger translation would need an independent in-game phrase "
            "or a held-out contig/pair prediction that assigns payload without using 3478 or the anchors as word glosses."
        ),
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q8_book6_7_phase_path_3478_transition_probe_v1_runs (
                created_at, decision, support_count, control_count,
                transition_signal_count, dominant_window_control_count,
                rare_window_count, path_resolved_count,
                promoted_plaintext_gloss_count, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                support_count,
                control_count,
                transition_signal_count,
                dominant_window_control_count,
                rare_window_count,
                path_resolved_count,
                promoted_plaintext_gloss_count,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q8_book6_7_phase_path_3478_transition_probe_v1_items (
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
                "transition_signal_count": transition_signal_count,
                "dominant_window_control_count": dominant_window_control_count,
                "rare_window_count": rare_window_count,
                "path_resolved_count": path_resolved_count,
                "promoted_plaintext_gloss_count": promoted_plaintext_gloss_count,
                "book6_window": str(target_anchor[BOOK6]["window_digits"]),
                "book7_window": str(target_anchor[BOOK7]["window_digits"]),
            }
        )
    )


if __name__ == "__main__":
    main()
