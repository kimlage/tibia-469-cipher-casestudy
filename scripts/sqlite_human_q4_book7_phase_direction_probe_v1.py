#!/usr/bin/env python3
"""Q4 probe: Book7 phase bridge versus directional/prose overclaim."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

TARGET_BOOK = "7"
CONTINUITY_CONTROL_BOOK = "6"
PHASE_CONTEXT_CONTROL_BOOKS = ("19", "31", "57")
SWALLOW_PATTERNS = ("AAETTA_SWALLOW_CONTROL", "EIEINT_SWALLOW_CONTROL", "NENIIF_SWALLOW_CONTROL")
KEY_COMPONENTS = ("NEIAAETTA", "TIINNEF", "VNCTIIN", "BENNA")


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
        CREATE TABLE IF NOT EXISTS human_q4_book7_phase_direction_probe_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            target_bookid TEXT NOT NULL,
            support_count INTEGER NOT NULL,
            control_count INTEGER NOT NULL,
            held_direction_count INTEGER NOT NULL,
            surface_order_conflict_count INTEGER NOT NULL,
            swallow_control_count INTEGER NOT NULL,
            promoted_plaintext_gloss_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q4_book7_phase_direction_probe_v1_items (
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


def all_rows(conn: sqlite3.Connection, sql: str, params: tuple[object, ...] = ()) -> list[sqlite3.Row]:
    return list(conn.execute(sql, params).fetchall())


def item(
    item_id: str,
    item_type: str,
    source_table: str,
    source_key: str,
    status: str,
    role_label: str,
    support_class: str,
    evidence: object,
) -> dict[str, object]:
    return {
        "item_id": item_id,
        "item_type": item_type,
        "source_table": source_table,
        "source_key": source_key,
        "status": status,
        "role_label": role_label,
        "support_class": support_class,
        "evidence_json": j(evidence),
    }


def positions_from_anchor(row: sqlite3.Row | None) -> list[int]:
    if not row:
        return []
    parsed = load_json(str(row["positions_json"]), [])
    if not isinstance(parsed, list):
        return []
    return [int(pos) for pos in parsed if isinstance(pos, int) or str(pos).isdigit()]


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q_run = latest_id(conn, "human_functional_promotion_synthesis_v1_next_questions")
    phase_probe_run = latest_id(conn, "book7_phase_anchor_probe_runs")
    phase_anchor_run = latest_id(conn, "book7_phase_anchor_items")
    phase_gate_run = latest_id(conn, "book7_phase_continuity_gate_items")
    human_shadow_run = latest_id(conn, "human_book7_phase_shadow_probe_v1_items")
    pkg6_run = latest_id(conn, "human_promotion_pkg6_book7_phase_bridge_falsification_v1_runs")

    items: list[dict[str, object]] = []

    q_row = one(
        conn,
        """
        SELECT *
        FROM human_functional_promotion_synthesis_v1_next_questions
        WHERE run_id=? AND question_id='Q4_BOOK7_PHASE_DIRECTION'
        """,
        (q_run,),
    )
    if not q_row:
        raise RuntimeError("missing Q4 next question")
    items.append(
        item(
            "precheck:q4-question",
            "precheck",
            "human_functional_promotion_synthesis_v1_next_questions",
            f"run={q_run}:Q4_BOOK7_PHASE_DIRECTION",
            "PRECHECK_READY",
            "directional contrast required before any prose claim",
            "SUPPORT_SQLITE_SELECTION",
            dict(q_row),
        )
    )

    probe_summary = one(
        conn,
        """
        SELECT run_id, decision, phase_anchor_positive_count, continuity_positive_count,
               swallow_control_count, local_score, payload_json
        FROM book7_phase_anchor_probe_runs
        WHERE run_id=?
        """,
        (phase_probe_run,),
    )
    if not probe_summary:
        raise RuntimeError("missing Book7 phase anchor probe summary")
    items.append(
        item(
            "support:phase-anchor-summary",
            "positive_or_control",
            "book7_phase_anchor_probe_runs",
            f"run={phase_probe_run}",
            str(probe_summary["decision"]),
            "phase-anchor and continuity split exists with swallow controls",
            "SUPPORT_BRIDGE_NOT_RANDOM_COOCCURRENCE",
            dict(probe_summary),
        )
    )

    target_shadow = one(
        conn,
        """
        SELECT *
        FROM human_book7_phase_shadow_probe_v1_items
        WHERE run_id=? AND bookid=?
        """,
        (human_shadow_run, TARGET_BOOK),
    )
    if not target_shadow:
        raise RuntimeError("missing Book7 human shadow row")
    target_hits = load_json(str(target_shadow["component_hits_json"]), {})
    if not isinstance(target_hits, dict):
        target_hits = {}
    items.append(
        item(
            "support:book7-composite-shape",
            "positive_or_control",
            "human_book7_phase_shadow_probe_v1_items",
            f"run={human_shadow_run}:book={TARGET_BOOK}",
            str(target_shadow["classification"]),
            "Book7 combines TIINNEF and NEIAAETTA without VNCTIIN",
            "SUPPORT_BOOK7_BRIDGE_SHAPE",
            dict(target_shadow),
        )
    )

    pkg6_run_row = one(
        conn,
        """
        SELECT decision, positive_pass_count, control_pass_count, control_warn_count,
               control_fail_count, promoted_functional_label_count,
               promoted_plaintext_gloss_count, payload_json
        FROM human_promotion_pkg6_book7_phase_bridge_falsification_v1_runs
        WHERE run_id=?
        """,
        (pkg6_run,),
    )
    if not pkg6_run_row:
        raise RuntimeError("missing package 6 run")
    items.append(
        item(
            "support:pkg6-promoted-functional-label",
            "positive_or_control",
            "human_promotion_pkg6_book7_phase_bridge_falsification_v1_runs",
            f"run={pkg6_run}",
            str(pkg6_run_row["decision"]),
            "Book7 functional bridge label survived package falsification",
            "SUPPORT_FUNCTIONAL_LABEL_NO_GLOSS",
            dict(pkg6_run_row),
        )
    )

    pkg6_decision = one(
        conn,
        """
        SELECT *
        FROM human_promotion_pkg6_book7_phase_bridge_falsification_v1_decisions
        WHERE run_id=? AND decision_id='PKG6_BOOK7_PHASE_CONTINUITY_BRIDGE_LABEL'
        """,
        (pkg6_run,),
    )
    if pkg6_decision:
        items.append(
            item(
                "support:pkg6-decision-scope",
                "positive_or_control",
                "human_promotion_pkg6_book7_phase_bridge_falsification_v1_decisions",
                f"run={pkg6_run}:PKG6_BOOK7_PHASE_CONTINUITY_BRIDGE_LABEL",
                str(pkg6_decision["decision"]),
                "scope is Book7 only, with Book6 and Books19/31/57 as controls",
                "SUPPORT_SCOPE_CONTROL_NO_GLOSS",
                dict(pkg6_decision),
            )
        )

    for pattern_id in ("NEIAAETTA_CONTINUITY", "TIINNEF_PHASE_ANCHOR"):
        anchor = one(
            conn,
            """
            SELECT *
            FROM book7_phase_anchor_items
            WHERE run_id=? AND bookid=? AND pattern_id=?
            """,
            (phase_anchor_run, TARGET_BOOK, pattern_id),
        )
        if not anchor:
            raise RuntimeError(f"missing Book7 anchor item: {pattern_id}")
        items.append(
            item(
                f"support:book7-anchor:{pattern_id}",
                "positive_or_control",
                "book7_phase_anchor_items",
                f"run={phase_anchor_run}:book={TARGET_BOOK}:{pattern_id}",
                str(anchor["context_status"]),
                f"Book7 {pattern_id} position evidence",
                "SUPPORT_BOOK7_COMPONENT_POSITION_NO_GLOSS",
                dict(anchor),
            )
        )

        gate = one(
            conn,
            """
            SELECT *
            FROM book7_phase_continuity_gate_items
            WHERE run_id=? AND bookid=? AND pattern_id=?
            """,
            (phase_gate_run, TARGET_BOOK, pattern_id),
        )
        if gate:
            items.append(
                item(
                    f"support:book7-gate:{pattern_id}",
                    "positive_or_control",
                    "book7_phase_continuity_gate_items",
                    f"run={phase_gate_run}:book={TARGET_BOOK}:{pattern_id}",
                    str(gate["decision"]),
                    str(gate["functional_label"]),
                    "SUPPORT_GATE_LABEL_NO_LEXICAL_GLOSS",
                    dict(gate),
                )
            )

    control6 = one(
        conn,
        """
        SELECT *
        FROM human_book7_phase_shadow_probe_v1_items
        WHERE run_id=? AND bookid=?
        """,
        (human_shadow_run, CONTINUITY_CONTROL_BOOK),
    )
    if not control6:
        raise RuntimeError("missing Book6 continuity control")
    items.append(
        item(
            "control:book6-continuity-only",
            "control",
            "human_book7_phase_shadow_probe_v1_items",
            f"run={human_shadow_run}:book={CONTINUITY_CONTROL_BOOK}",
            str(control6["classification"]),
            "NEIAAETTA can occur without TIINNEF, so Book7 is not inherited by Book6",
            "CONTROL_CONTINUITY_ONLY_NOT_BOOK7_BRIDGE",
            dict(control6),
        )
    )

    for bookid in PHASE_CONTEXT_CONTROL_BOOKS:
        control = one(
            conn,
            """
            SELECT *
            FROM human_book7_phase_shadow_probe_v1_items
            WHERE run_id=? AND bookid=?
            """,
            (human_shadow_run, bookid),
        )
        if not control:
            raise RuntimeError(f"missing phase-context control Book{bookid}")
        items.append(
            item(
                f"control:phase-context:{bookid}",
                "control",
                "human_book7_phase_shadow_probe_v1_items",
                f"run={human_shadow_run}:book={bookid}",
                str(control["classification"]),
                "TIINNEF+VNCTIIN context is not the same Book7 bridge shape",
                "CONTROL_PHASE_CONTEXT_NOT_BOOK7_BRIDGE",
                dict(control),
            )
        )

    swallow_rows = all_rows(
        conn,
        """
        SELECT *
        FROM book7_phase_anchor_items
        WHERE run_id=? AND bookid=? AND pattern_id IN (?, ?, ?)
        ORDER BY pattern_id
        """,
        (phase_anchor_run, TARGET_BOOK, *SWALLOW_PATTERNS),
    )
    for row in swallow_rows:
        items.append(
            item(
                f"control:book7-swallow:{row['pattern_id']}",
                "control",
                "book7_phase_anchor_items",
                f"run={phase_anchor_run}:book={TARGET_BOOK}:{row['pattern_id']}",
                str(row["context_status"]),
                "Book7 local component is a swallow/superset control, not a word",
                "CONTROL_SWALLOW_SUPERSET_BLOCKS_WORD_GLOSS",
                dict(row),
            )
        )

    ti_anchor = one(
        conn,
        """
        SELECT *
        FROM book7_phase_anchor_items
        WHERE run_id=? AND bookid=? AND pattern_id='TIINNEF_PHASE_ANCHOR'
        """,
        (phase_anchor_run, TARGET_BOOK),
    )
    neia_anchor = one(
        conn,
        """
        SELECT *
        FROM book7_phase_anchor_items
        WHERE run_id=? AND bookid=? AND pattern_id='NEIAAETTA_CONTINUITY'
        """,
        (phase_anchor_run, TARGET_BOOK),
    )
    ti_positions = positions_from_anchor(ti_anchor)
    neia_positions = positions_from_anchor(neia_anchor)
    ti_pos = min(ti_positions) if ti_positions else -1
    neia_pos = min(neia_positions) if neia_positions else -1
    surface_order_conflict = int(ti_pos >= 0 and neia_pos >= 0 and ti_pos < neia_pos)
    items.append(
        item(
            "held:surface-order-direction",
            "held_direction",
            "book7_phase_anchor_items",
            f"run={phase_anchor_run}:book={TARGET_BOOK}:TIINNEF@{ti_pos}:NEIAAETTA@{neia_pos}",
            "DIRECTION_HELD_SURFACE_ORDER_REVERSES_CLAIM" if surface_order_conflict else "DIRECTION_NOT_BLOCKED_BY_SURFACE_ORDER",
            "surface order cannot prove NEIAAETTA into TIINNEF direction",
            "HELD_DIRECTIONAL_CLAIM_NOT_PROMOTED",
            {
                "bookid": TARGET_BOOK,
                "tiinnef_positions": ti_positions,
                "neiaaetta_positions": neia_positions,
                "surface_order_observation": "TIINNEF occurs before NEIAAETTA in Book7",
                "directional_claim_blocked": bool(surface_order_conflict),
            },
        )
    )

    if pkg6_decision:
        notes = load_json(str(pkg6_decision["subtype_notes_json"]), {})
        blocked_claims = load_json(str(pkg6_decision["blocked_claims_json"]), [])
        items.append(
            item(
                "held:high-row0-phase-risk",
                "held_direction",
                "human_promotion_pkg6_book7_phase_bridge_falsification_v1_decisions",
                f"run={pkg6_run}:PKG6_BOOK7_PHASE_CONTINUITY_BRIDGE_LABEL",
                "HIGH_ROW0_PHASE_RISK_HELD",
                "phase risk remains active; bridge label is functional only",
                "HELD_PHASE_RISK_BLOCKS_PROSE_DIRECTION",
                {"subtype_notes": notes, "blocked_claims": blocked_claims},
            )
        )

    support_count = sum(1 for row in items if str(row["support_class"]).startswith("SUPPORT"))
    control_count = sum(1 for row in items if str(row["support_class"]).startswith("CONTROL"))
    held_direction_count = sum(1 for row in items if str(row["support_class"]).startswith("HELD"))
    swallow_control_count = len(swallow_rows)
    promoted_plaintext_gloss_count = int(pkg6_run_row["promoted_plaintext_gloss_count"])

    decision = (
        "Q4_BOOK7_PHASE_BRIDGE_CONFIRMED_DIRECTION_HELD_NO_GLOSS"
        if support_count >= 6
        and control_count >= 5
        and held_direction_count >= 1
        and surface_order_conflict == 1
        and promoted_plaintext_gloss_count == 0
        else "Q4_BOOK7_PHASE_DIRECTION_REQUIRES_MANUAL_REVIEW"
    )

    payload = {
        "question": "Does Book7 directionally bridge NEIAAETTA continuity into TIINNEF phase, or is it just local co-occurrence?",
        "answer": (
            "Book7 is stronger than simple local co-occurrence because it is the inspected row that combines "
            "NEIAAETTA continuity and TIINNEF phase-anchor evidence without the VNCTIIN context of Books19/31/57. "
            "However, the directional claim NEIAAETTA into TIINNEF is held, because the observed Book7 surface order "
            "has TIINNEF before NEIAAETTA."
        ),
        "allowed_reading": "Book7 phase-continuity bridge / bridge-control label, functional only.",
        "blocked_reading": "No lexical gloss for NEIAAETTA, TIINNEF, VNCTIIN, BENNA, 3478, or the Book7 sentence.",
        "surface_order": {
            "TIINNEF": ti_positions,
            "NEIAAETTA": neia_positions,
            "directional_claim_status": "held_not_promoted",
        },
        "controls": {
            "Book6": "continuity-only control",
            "Books19_31_57": "TIINNEF+VNCTIIN phase-context controls",
            "Book7_swallow_controls": list(SWALLOW_PATTERNS),
        },
        "next_probe": "Use Book7 as a bridge/control in the human shadow layer; do not write prose until an independent in-game anchor resolves direction.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q4_book7_phase_direction_probe_v1_runs (
                created_at, decision, target_bookid, support_count, control_count,
                held_direction_count, surface_order_conflict_count, swallow_control_count,
                promoted_plaintext_gloss_count, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                TARGET_BOOK,
                support_count,
                control_count,
                held_direction_count,
                surface_order_conflict,
                swallow_control_count,
                promoted_plaintext_gloss_count,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q4_book7_phase_direction_probe_v1_items (
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
                "target_bookid": TARGET_BOOK,
                "support_count": support_count,
                "control_count": control_count,
                "held_direction_count": held_direction_count,
                "surface_order_conflict_count": surface_order_conflict,
                "swallow_control_count": swallow_control_count,
                "promoted_plaintext_gloss_count": promoted_plaintext_gloss_count,
                "surface_order": {"TIINNEF": ti_positions, "NEIAAETTA": neia_positions},
            }
        )
    )


if __name__ == "__main__":
    main()
