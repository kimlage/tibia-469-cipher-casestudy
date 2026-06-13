#!/usr/bin/env python3
"""Q3 probe: does Book49 support calibration/operator-reset, or only register/control?"""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
BOOK = "49"


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q3_book49_register_function_probe_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            target_bookid TEXT NOT NULL,
            support_count INTEGER NOT NULL,
            control_count INTEGER NOT NULL,
            missing_required_evidence_count INTEGER NOT NULL,
            calibration_context_count INTEGER NOT NULL,
            operator_reset_context_count INTEGER NOT NULL,
            promoted_plaintext_gloss_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q3_book49_register_function_probe_v1_items (
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


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    self_run = latest_id(conn, "book49_selfcontainment_gate_runs")
    repeat_run = latest_id(conn, "human_book49_repeat_shadow_probe_v1_runs")
    residual_run = latest_id(conn, "book49_residual_negative_probe_runs")
    audit_run = latest_id(conn, "book49_audit_context_policy_runs")
    pkg_run = latest_id(conn, "human_promotion_pkg7_book49_repeat_register_falsification_v1_runs")
    math_run = latest_id(conn, "human_mathemagic_shadow_synthesis_v1_runs")
    plus49_run = latest_id(conn, "mathemagic_plus49_wide_frontier_probe_v1_runs")
    window_run = latest_id(conn, "mathemagic_49_94_window_probe_v1_runs")
    matrix_run = latest_id(conn, "post_mathemagic_book_evidence_matrix_v1_runs")
    frontier_run = latest_id(conn, "post_mathemagic_frontier_selection_v1_runs")
    s2ward_run = latest_id(conn, "s2ward_rearrange_line_map_runs")

    items: list[dict[str, object]] = []

    self_row = one(
        conn,
        """
        SELECT *
        FROM book49_selfcontainment_gate_runs
        WHERE run_id=? AND bookid=?
        """,
        (self_run, BOOK),
    )
    if not self_row:
        raise RuntimeError("missing Book49 selfcontainment row")
    self_support = int(self_row["external_note_present"]) == 1 and float(self_row["repeated_token_coverage"]) >= 0.55
    items.append(
        item(
            "support:selfcontainment",
            "positive_or_control",
            "book49_selfcontainment_gate_runs",
            f"run={self_run}:book={BOOK}",
            "PASS_SELF_CONTAINED_REPEAT_FORMULA" if self_support else "FAIL_SELF_CONTAINMENT",
            "self-contained repeat/register formula",
            "SUPPORT_REGISTER_CONTROL_NOT_CALIBRATION",
            dict(self_row),
        )
    )

    repeat_target = one(
        conn,
        """
        SELECT *
        FROM human_book49_repeat_shadow_probe_v1_items
        WHERE run_id=? AND bookid=?
        """,
        (repeat_run, BOOK),
    )
    if not repeat_target:
        raise RuntimeError("missing Book49 repeat target")
    items.append(
        item(
            "support:repeat-rank",
            "positive_or_control",
            "human_book49_repeat_shadow_probe_v1_items",
            f"run={repeat_run}:book={BOOK}",
            "PASS_REPEAT_RANK_1_NO_GLOSS" if int(repeat_target["repeat_rank"]) == 1 else "FAIL_REPEAT_RANK",
            "rank-1 repeat/register witness",
            "SUPPORT_REGISTER_CONTROL_NOT_CALIBRATION",
            dict(repeat_target),
        )
    )

    repeat_controls = all_rows(
        conn,
        """
        SELECT bookid, repeated_token_coverage, repeat_rank, classification, shadow_implication
        FROM human_book49_repeat_shadow_probe_v1_items
        WHERE run_id=? AND bookid<>? AND repeated_token_coverage>=0.55
        ORDER BY repeat_rank
        """,
        (repeat_run, BOOK),
    )
    for row in repeat_controls[:10]:
        items.append(
            item(
                f"control:high-repeat:{row['bookid']}",
                "control",
                "human_book49_repeat_shadow_probe_v1_items",
                f"run={repeat_run}:book={row['bookid']}",
                str(row["classification"]),
                "high repetition exists outside Book49",
                "CONTROL_REPEAT_ALONE_NOT_SEMANTIC",
                dict(row),
            )
        )

    residual_rows = all_rows(
        conn,
        """
        SELECT pattern_id, bookid, residual_status, next_action, positions_json
        FROM book49_residual_negative_items
        WHERE run_id=? AND (bookid=? OR residual_status='CONTROL_REPETITION_HIT')
        ORDER BY residual_status DESC, bookid, pattern_id
        """,
        (residual_run, BOOK),
    )
    for row in residual_rows[:16]:
        support_class = (
            "CONTROL_RESIDUAL_COMPONENTS_HELD"
            if str(row["residual_status"]) == "BOOK49_RESIDUAL_HIT"
            else "CONTROL_COMPONENTS_REPEAT_OUTSIDE_BOOK49"
        )
        items.append(
            item(
                f"control:residual:{row['bookid']}:{row['pattern_id']}",
                "control",
                "book49_residual_negative_items",
                f"run={residual_run}:book={row['bookid']}:{row['pattern_id']}",
                str(row["residual_status"]),
                "O32/NEEI/EEILEE/LEII components remain audit-only",
                support_class,
                dict(row),
            )
        )

    audit_row = one(
        conn,
        """
        SELECT *
        FROM book49_audit_context_policy_items
        WHERE run_id=?
        """,
        (audit_run,),
    )
    if audit_row:
        items.append(
            item(
                "control:audit-context",
                "control",
                "book49_audit_context_policy_items",
                f"run={audit_run}:{audit_row['context_id']}",
                str(audit_row["policy_status"]),
                "residual audit context blocks component gloss",
                "CONTROL_AUDIT_ONLY",
                dict(audit_row),
            )
        )

    pkg_row = one(
        conn,
        """
        SELECT decision, positive_pass_count, control_pass_count, control_warn_count,
               control_fail_count, promoted_functional_label_count,
               promoted_plaintext_gloss_count, payload_json
        FROM human_promotion_pkg7_book49_repeat_register_falsification_v1_runs
        WHERE run_id=?
        """,
        (pkg_run,),
    )
    if pkg_row:
        items.append(
            item(
                "support:pkg7-promotion",
                "positive_or_control",
                "human_promotion_pkg7_book49_repeat_register_falsification_v1_runs",
                f"run={pkg_run}",
                str(pkg_row["decision"]),
                "promoted human-functional repeat/register label",
                "SUPPORT_FUNCTIONAL_LABEL_NO_GLOSS",
                dict(pkg_row),
            )
        )

    math_row = one(
        conn,
        """
        SELECT hypothesis_id, operator_or_anchor, status, implication, next_probe, rejection_rule
        FROM human_mathemagic_shadow_synthesis_v1_items
        WHERE run_id=? AND hypothesis_id='MATH_49_REGISTER_SELECTOR_NOT_DICTIONARY'
        """,
        (math_run,),
    )
    if math_row:
        items.append(
            item(
                "held:mathemagic-hypothesis",
                "held",
                "human_mathemagic_shadow_synthesis_v1_items",
                f"run={math_run}:MATH_49_REGISTER_SELECTOR_NOT_DICTIONARY",
                str(math_row["status"]),
                "Mathemagic 49 is active hypothesis, not evidence of reset semantics",
                "HELD_REQUIRES_HELDOUT_IMPROVEMENT",
                dict(math_row),
            )
        )

    plus49_row = one(
        conn,
        """
        SELECT *
        FROM mathemagic_plus49_wide_frontier_probe_v1_items
        WHERE run_id=? AND offset_value=49 AND direction='plus_mod70'
        """,
        (plus49_run,),
    )
    if plus49_row:
        items.append(
            item(
                "held:plus49-top-selector",
                "held",
                "mathemagic_plus49_wide_frontier_probe_v1_items",
                f"run={plus49_run}:offset=49:plus",
                str(plus49_row["status"]),
                "+49/mod70 is audit selector but tied with controls",
                "HELD_MATHEMAGIC_SELECTOR_NOT_RESET",
                dict(plus49_row),
            )
        )

    for label in ("target_49", "target_-49", "target_24"):
        row = one(
            conn,
            """
            SELECT *
            FROM mathemagic_49_94_window_probe_v1_items
            WHERE run_id=? AND offset_label=?
            """,
            (window_run, label),
        )
        if row:
            items.append(
                item(
                    f"held:window:{label}",
                    "held",
                    "mathemagic_49_94_window_probe_v1_items",
                    f"run={window_run}:{label}",
                    str(row["status"]),
                    "49/94 window is ranking signal only",
                    "HELD_OR_CONTROL_MATHEMAGIC_WINDOW",
                    dict(row),
                )
            )

    matrix_row = one(
        conn,
        """
        SELECT *
        FROM post_mathemagic_book_evidence_matrix_v1_items
        WHERE run_id=? AND bookid=?
        """,
        (matrix_run, BOOK),
    )
    if matrix_row:
        items.append(
            item(
                "support:post-math-selector-control",
                "positive_or_control",
                "post_mathemagic_book_evidence_matrix_v1_items",
                f"run={matrix_run}:book={BOOK}",
                str(matrix_row["status"]),
                str(matrix_row["functional_reading"]),
                "SUPPORT_SELECTOR_CONTROL_BUT_NO_POST_MATH_SIGNAL",
                dict(matrix_row),
            )
        )

    frontier_row = one(
        conn,
        """
        SELECT *
        FROM post_mathemagic_frontier_selection_v1_items
        WHERE run_id=? AND bookid=?
        """,
        (frontier_run, BOOK),
    )
    if frontier_row:
        items.append(
            item(
                "held:post-math-frontier",
                "held",
                "post_mathemagic_frontier_selection_v1_items",
                f"run={frontier_run}:book={BOOK}",
                str(frontier_row["post_math_status"]),
                str(frontier_row["math_relation_status"]),
                "HELD_ALIVE_NON_C86_FRONTIER_NOT_CALIBRATION",
                dict(frontier_row),
            )
        )

    s2ward_row = one(
        conn,
        """
        SELECT line_no, label, mapped_bookid, extracted_digit_len, lcs_len,
               note, is_residual, candidate_status
        FROM s2ward_rearrange_line_map_items
        WHERE run_id=? AND mapped_bookid=?
        """,
        (s2ward_run, BOOK),
    )
    if s2ward_row:
        items.append(
            item(
                "support:s2ward-selfcontainment",
                "positive_or_control",
                "s2ward_rearrange_line_map_items",
                f"run={s2ward_run}:line={s2ward_row['line_no']}:label={s2ward_row['label']}",
                str(s2ward_row["candidate_status"]),
                "external corpus line marks Book49 selfcontainment",
                "SUPPORT_EXTERNAL_CORPUS_STRUCTURE_AUDIT_ONLY",
                dict(s2ward_row),
            )
        )

    missing_items = [
        (
            "missing:book-location",
            "book location or shelf-neighborhood evidence",
            "No source in the operational DB currently links Book49 placement/neighbors to calibration/operator-reset.",
        ),
        (
            "missing:independent-register-parallel",
            "independent repeated-register parallel",
            "High-repeat controls exist, but none independently attest calibration/reset function for Book49.",
        ),
        (
            "missing:operator-reset-context",
            "explicit operator-reset or calibration context",
            "No in-game/NPC/quest text currently says this Book49 pattern performs reset/calibration.",
        ),
    ]
    for item_id, role, note in missing_items:
        items.append(
            item(
                item_id,
                "missing_required_evidence",
                "human_functional_promotion_synthesis_v1_next_questions",
                "Q3_BOOK49_REGISTER_FUNCTION",
                "MISSING_REQUIRED_EVIDENCE",
                role,
                "MISSING_BLOCKS_CALIBRATION_RESET_CLAIM",
                {"note": note, "bookid": BOOK},
            )
        )

    support_count = sum(1 for row in items if row["support_class"].startswith("SUPPORT"))
    control_count = sum(1 for row in items if row["support_class"].startswith("CONTROL"))
    missing_count = sum(1 for row in items if row["item_type"] == "missing_required_evidence")
    calibration_context_count = 0
    operator_reset_context_count = 0
    promoted_plaintext_gloss_count = 0
    decision = (
        "Q3_BOOK49_REGISTER_CONTROL_ONLY_CALIBRATION_RESET_NOT_SUPPORTED_NO_GLOSS"
        if support_count >= 4
        and control_count >= 4
        and missing_count > 0
        and calibration_context_count == 0
        and operator_reset_context_count == 0
        and promoted_plaintext_gloss_count == 0
        else "Q3_BOOK49_REQUIRES_MANUAL_REVIEW"
    )

    payload = {
        "question": "Does Book49's self-contained repeat/register pattern correlate with calibration/operator-reset use in in-game context?",
        "answer": "No. It supports a register/control label, but not calibration or operator-reset in game context.",
        "allowed_reading": "Book49 is a self-contained repeat/register formula and selector/control witness.",
        "blocked_reading": "Book49 is not a calibration/reset instruction, chant, spell, refrain, dictionary key, or translated sentence.",
        "next_probe": "Either find book-location/neighborhood evidence, or test Q4/Q5 instead of strengthening Book49 prose.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q3_book49_register_function_probe_v1_runs (
                created_at, decision, target_bookid, support_count, control_count,
                missing_required_evidence_count, calibration_context_count,
                operator_reset_context_count, promoted_plaintext_gloss_count, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                BOOK,
                support_count,
                control_count,
                missing_count,
                calibration_context_count,
                operator_reset_context_count,
                promoted_plaintext_gloss_count,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q3_book49_register_function_probe_v1_items (
                run_id, item_id, item_type, source_table, source_key, status,
                role_label, support_class, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    row["item_id"],
                    row["item_type"],
                    row["source_table"],
                    row["source_key"],
                    row["status"],
                    row["role_label"],
                    row["support_class"],
                    row["evidence_json"],
                )
                for row in items
            ],
        )

    print(
        j(
            {
                "run_id": run_id,
                "decision": decision,
                "target_bookid": BOOK,
                "support_count": support_count,
                "control_count": control_count,
                "missing_required_evidence_count": missing_count,
                "calibration_context_count": calibration_context_count,
                "operator_reset_context_count": operator_reset_context_count,
                "promoted_plaintext_gloss_count": promoted_plaintext_gloss_count,
            }
        )
    )


if __name__ == "__main__":
    main()
