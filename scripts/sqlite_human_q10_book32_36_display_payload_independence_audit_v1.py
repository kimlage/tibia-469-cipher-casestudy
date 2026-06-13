#!/usr/bin/env python3
"""Q10 audit: Book32/36 display-tail masking versus independent payload."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

TARGETS = ("32", "36")


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q10_book32_36_display_payload_independence_audit_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            target_count INTEGER NOT NULL,
            display_tail_hold_count INTEGER NOT NULL,
            closure_control_count INTEGER NOT NULL,
            external_separation_count INTEGER NOT NULL,
            book_scoped_drift_count INTEGER NOT NULL,
            heldout_payload_count INTEGER NOT NULL,
            promoted_plaintext_gloss_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q10_book32_36_display_payload_independence_audit_v1_items (
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


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q6_run = latest_id(conn, "human_q6_external_corpus_order_residual_probe_v1_runs")
    display_tail_run = latest_id(conn, "display_tail_masking_gate_v1_items")
    closure_run = latest_id(conn, "final_display_control_closure_gate_v1_items")
    drift_run = latest_id(conn, "btii_display_drift_gate_items")
    concordance_run = latest_id(conn, "display_template_concordance_gate_v1_items")
    remaining_run = latest_id(conn, "remaining_five_evidence_requirements_v1_items")
    book32_formula_run = latest_id(conn, "book32_formula_display_probe_v1_runs")

    items: list[dict[str, object]] = []

    q6 = one(
        conn,
        "SELECT * FROM human_q6_external_corpus_order_residual_probe_v1_runs WHERE run_id=?",
        (q6_run,),
    )
    if not q6:
        raise RuntimeError("missing Q6 run")
    q6_relation = one(
        conn,
        """
        SELECT *
        FROM human_q6_external_corpus_order_residual_probe_v1_items
        WHERE run_id=? AND item_id='control:external-order:32-36-separated'
        """,
        (q6_run,),
    )
    add_item(
        items,
        "control:q6-external-32-36-separated",
        "external_order_control",
        "human_q6_external_corpus_order_residual_probe_v1_items",
        f"run={q6_run}:control:external-order:32-36-separated",
        str(q6_relation["status"]) if q6_relation else "MISSING_Q6_32_36_SEPARATION_ITEM",
        "Book32/36 do not gain a physical/order pair argument from the external corpus",
        "CONTROL_EXTERNAL_ORDER_SEPARATES_DISPLAY_RESIDUALS",
        {"q6_run": dict(q6), "q6_relation": dict(q6_relation) if q6_relation else None},
    )

    book32_formula = one(
        conn,
        "SELECT * FROM book32_formula_display_probe_v1_runs WHERE run_id=?",
        (book32_formula_run,),
    )
    add_item(
        items,
        "control:book32-formula-display",
        "formula_display_control",
        "book32_formula_display_probe_v1_runs",
        f"run={book32_formula_run}",
        str(book32_formula["decision"]) if book32_formula else "MISSING_BOOK32_FORMULA_RUN",
        "Book32 formula/display probe rejects independent payload promotion",
        "CONTROL_BOOK32_FORMULA_DISPLAY_NO_GLOSS",
        dict(book32_formula) if book32_formula else {"missing": True},
    )

    display_tail_hold_count = 0
    closure_control_count = 0
    book_scoped_drift_count = 0
    heldout_payload_count = 0

    for bookid in TARGETS:
        row0 = one(
            conn,
            """
            SELECT bookid, token_count, symbol_text
            FROM row0_variant_book_tokens
            WHERE run_id=(SELECT max(run_id) FROM row0_variant_book_tokens)
              AND bookid=?
            """,
            (bookid,),
        )
        tail = one(
            conn,
            """
            SELECT *
            FROM display_tail_masking_gate_v1_items
            WHERE run_id=? AND bookid=?
            """,
            (display_tail_run, bookid),
        )
        closure = one(
            conn,
            """
            SELECT *
            FROM final_display_control_closure_gate_v1_items
            WHERE run_id=? AND bookid=?
            """,
            (closure_run, bookid),
        )
        drift = one(
            conn,
            """
            SELECT *
            FROM btii_display_drift_gate_items
            WHERE run_id=? AND bookid=?
            """,
            (drift_run, bookid),
        )
        concordance = one(
            conn,
            """
            SELECT *
            FROM display_template_concordance_gate_v1_items
            WHERE run_id=? AND bookid=?
            """,
            (concordance_run, bookid),
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

        tail_holds = bool(tail and tail["gate_status"] == "HOLD_DISPLAY_TAIL_ONLY_NO_PAYLOAD" and int(tail["promotion_allowed"]) == 0)
        closure_control = bool(
            closure
            and int(closure["close_as_functional_control"]) == 1
            and int(closure["semantic_promotion_allowed"]) == 0
            and int(closure["prose_gloss_allowed"]) == 0
        )
        drift_control = bool(
            drift
            and "DISPLAY_DRIFT" in str(drift["decision"])
            and int(drift["family_wide_promotion_allowed"]) == 0
            and int(drift["lexical_gloss_allowed"]) == 0
        )
        concordance_allows_payload = bool(
            concordance
            and (int(concordance["promotion_allowed"]) == 1 or int(concordance["prose_gloss_allowed"]) == 1)
        )
        tail_allows_payload = bool(tail and (int(tail["promotion_allowed"]) == 1 or int(tail["prose_gloss_allowed"]) == 1))
        closure_allows_payload = bool(
            closure
            and (int(closure["semantic_promotion_allowed"]) == 1 or int(closure["prose_gloss_allowed"]) == 1)
        )
        drift_allows_payload = bool(
            drift and (int(drift["family_wide_promotion_allowed"]) == 1 or int(drift["lexical_gloss_allowed"]) == 1)
        )

        display_tail_hold_count += int(tail_holds)
        closure_control_count += int(closure_control)
        book_scoped_drift_count += int(drift_control)
        heldout_payload_count += int(
            concordance_allows_payload or tail_allows_payload or closure_allows_payload or drift_allows_payload
        )

        add_item(
            items,
            f"control:display-tail:{bookid}",
            "display_tail_mask",
            "display_tail_masking_gate_v1_items",
            f"run={display_tail_run}:book={bookid}",
            str(tail["gate_status"]) if tail else "MISSING_DISPLAY_TAIL_ITEM",
            "Display tail masks cleanly and leaves no independent payload",
            "CONTROL_DISPLAY_TAIL_NO_PAYLOAD" if tail_holds else "REVIEW_DISPLAY_TAIL_PAYLOAD_POSSIBLE",
            {"row0": dict(row0) if row0 else None, "display_tail": dict(tail) if tail else None},
        )
        add_item(
            items,
            f"control:closure:{bookid}",
            "display_control_closure",
            "final_display_control_closure_gate_v1_items",
            f"run={closure_run}:book={bookid}",
            str(closure["closure_status"]) if closure else "MISSING_CLOSURE_ITEM",
            "Existing closure gate closes this book as display control only",
            "CONTROL_CLOSED_AS_DISPLAY_ONLY_NO_PAYLOAD" if closure_control else "REVIEW_CLOSURE_PAYLOAD_POSSIBLE",
            dict(closure) if closure else {"bookid": bookid, "missing": True},
        )
        add_item(
            items,
            f"control:btii-drift:{bookid}",
            "display_drift_gate",
            "btii_display_drift_gate_items",
            f"run={drift_run}:book={bookid}",
            str(drift["decision"]) if drift else "MISSING_BTII_DRIFT_ITEM",
            "BTII/NSBVN/ATFNAAST drift is book-scoped display, not family-wide payload",
            "CONTROL_BOOK_SCOPED_DISPLAY_DRIFT_NO_GLOSS" if drift_control else "REVIEW_BTII_DRIFT_PAYLOAD_POSSIBLE",
            dict(drift) if drift else {"bookid": bookid, "missing": True},
        )
        add_item(
            items,
            f"control:display-concordance:{bookid}",
            "display_concordance_gate",
            "display_template_concordance_gate_v1_items",
            f"run={concordance_run}:book={bookid}",
            str(concordance["gate_status"]) if concordance else "MISSING_DISPLAY_CONCORDANCE_ITEM",
            "Display-template concordance is held as no-gloss evidence",
            "CONTROL_DISPLAY_CONCORDANCE_HELD_NO_GLOSS" if not concordance_allows_payload else "REVIEW_DISPLAY_CONCORDANCE_PAYLOAD_POSSIBLE",
            dict(concordance) if concordance else {"bookid": bookid, "missing": True},
        )
        add_item(
            items,
            f"control:remaining-requirement:{bookid}",
            "remaining_requirement",
            "remaining_five_evidence_requirements_v1_items",
            f"run={remaining_run}:book={bookid}",
            "REMAINING_REQUIREMENT_STILL_NEEDS_NEW_EVIDENCE",
            "Q10 says current display evidence is exhausted; reopen only with new independent payload evidence",
            "CONTROL_CURRENT_EVIDENCE_EXHAUSTED",
            dict(remaining) if remaining else {"bookid": bookid, "missing": True},
        )

    external_separation_count = int(q6 and int(q6["display_separation_count"]) == 1 and q6_relation is not None)
    promoted_plaintext_gloss_count = 0

    decision = (
        "Q10_BOOK32_36_DISPLAY_PAYLOAD_INDEPENDENCE_REJECTED_CLOSE_CONTROL_NO_GLOSS"
        if display_tail_hold_count == len(TARGETS)
        and closure_control_count == len(TARGETS)
        and external_separation_count == 1
        and book_scoped_drift_count == len(TARGETS)
        and heldout_payload_count == 0
        and promoted_plaintext_gloss_count == 0
        else "Q10_BOOK32_36_DISPLAY_PAYLOAD_AUDIT_REQUIRES_MANUAL_REVIEW"
    )

    payload = {
        "question": "Do Book32 and Book36 contain independent payload after display-tail masking and display-drift controls?",
        "answer": (
            "No with the current evidence. Q6 separates the two in external order, display-tail masking leaves no independent payload, "
            "BTII/NSBVN drift is book-scoped display only, and the final display-control closure gate already closes both as controls."
        ),
        "allowed_reading": "Book32 and Book36 can be used as display/control evidence for the formula/display family.",
        "blocked_reading": "Do not translate Book32/36 as prose and do not promote BENNA, BTII, NSBVN, FNAAST, or the shared tail as payload here.",
        "method_implication": "Do not spend another current-table confirmation lane on Book32/36 unless a new external artifact or in-game phrase supplies independent payload.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q10_book32_36_display_payload_independence_audit_v1_runs (
                created_at, decision, target_count, display_tail_hold_count,
                closure_control_count, external_separation_count,
                book_scoped_drift_count, heldout_payload_count,
                promoted_plaintext_gloss_count, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                len(TARGETS),
                display_tail_hold_count,
                closure_control_count,
                external_separation_count,
                book_scoped_drift_count,
                heldout_payload_count,
                promoted_plaintext_gloss_count,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q10_book32_36_display_payload_independence_audit_v1_items (
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
                "target_count": len(TARGETS),
                "display_tail_hold_count": display_tail_hold_count,
                "closure_control_count": closure_control_count,
                "external_separation_count": external_separation_count,
                "book_scoped_drift_count": book_scoped_drift_count,
                "heldout_payload_count": heldout_payload_count,
                "promoted_plaintext_gloss_count": promoted_plaintext_gloss_count,
            }
        )
    )


if __name__ == "__main__":
    main()
