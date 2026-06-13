#!/usr/bin/env python3
"""Q37: select precise non-contig human-translation frontiers after Q36."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

FRONTIERS = [
    {
        "frontier_id": "BOOK30_FAMILY_SPINE_PACKET",
        "priority": 1,
        "bookids": ["12", "21", "26", "30"],
        "selection_reason": "Small coherent family with explicit shared VNSBLFSINNAI/TAESESTIEN spine behavior and Great Calculator compiled-corpus support.",
        "source_bridge": "GREAT_CALCULATOR_COMPILED_LANGUAGE",
        "next_probe": "Promote the existing Book30-family shadow material into a unified non-contig family atlas entry.",
        "expected_failure_mode": "Overstating family spine as sentence prose or endpoint meaning.",
    },
    {
        "frontier_id": "VNCTIIN_TIINNEF_PHASE_TRIO",
        "priority": 2,
        "bookids": ["19", "31", "57"],
        "selection_reason": "Three non-contig VNCTIIN context books carry TIINNEF phase anchor and can test Book7 phase continuity without using 3478 as gloss.",
        "source_bridge": "AWB_LANGUAGE_MATHEMAGIC_PROCESSING",
        "next_probe": "Build a phase-context trio probe and compare with Book7/phase material while blocking 3478 component gloss.",
        "expected_failure_mode": "Collapsing TIINNEF into a word meaning or importing Book7 semantics.",
    },
    {
        "frontier_id": "C86_VINVIN_BRANCH_TRIO",
        "priority": 3,
        "bookids": ["3", "17", "44"],
        "selection_reason": "Three non-contig C86-opened VINVIN/VTLR branch lines mirror Q33 branch logic without exact contig edges.",
        "source_bridge": "AWB_COMPLEX_FORMULA_SUBJECTIVE_VIEWER",
        "next_probe": "Test whether Q33 branch/variant formula bridge generalizes to non-contig C86/VINVIN branch witnesses.",
        "expected_failure_mode": "Treating C86/VINVIN as lexical payload instead of branch/selector behavior.",
    },
    {
        "frontier_id": "BTII_NSBVN_ATFNAAST_DISPLAY_TRIO",
        "priority": 4,
        "bookids": ["11", "32", "43"],
        "selection_reason": "Three repeated display-drift formula blocks can be consolidated as display/formula controls before they pollute prose.",
        "source_bridge": "BEWARE_LANGUAGE_MATH_NUMERIC_BOOKS",
        "next_probe": "Create a display-only stabilization entry that explains repeated BTII/NSBVN/ATFNAAST behavior without prose.",
        "expected_failure_mode": "Mistaking display drift for human-readable message text.",
    },
    {
        "frontier_id": "NAESE_C68_SLOT_VARIANT_TRIO",
        "priority": 5,
        "bookids": ["22", "28", "48"],
        "selection_reason": "Canonical NAESE/C68 slot classifier plus two controlled variant windows can extend the slot model beyond exact contigs.",
        "source_bridge": "BEWARE_BLINKING_CODE_VARIABLE_UNIT",
        "next_probe": "Compare slot stability and changed surrounds; accept only classifier behavior, not NAESE word meaning.",
        "expected_failure_mode": "Promoting NAESE/C68 as a semantic word pair.",
    },
    {
        "frontier_id": "CHAYENNE_REGISTER_FRAME_SET",
        "priority": 6,
        "bookids": ["8", "37", "63", "66"],
        "selection_reason": "External Chayenne frame appears across different internal contexts and is useful for register behavior, but must stay source-quarantined.",
        "source_bridge": "CHAYENNE_EXTERNAL_REGISTER_FRAME",
        "next_probe": "Unify Chayenne-frame books as register/context witnesses and block direct phrase translation.",
        "expected_failure_mode": "Using Chayenne external phrase as a dictionary for Hellgate books.",
    },
]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q37_noncontig_frontier_selection_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q36_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            candidate_frontier_count INTEGER NOT NULL,
            selected_frontier_count INTEGER NOT NULL,
            selected_book_count INTEGER NOT NULL,
            contig_shadow_book_count INTEGER NOT NULL,
            noncontig_book_count INTEGER NOT NULL,
            component_gloss_allowed_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q37_noncontig_frontier_selection_v1_items (
            run_id INTEGER NOT NULL,
            frontier_id TEXT NOT NULL,
            priority INTEGER NOT NULL,
            bookids_json TEXT NOT NULL,
            book_count INTEGER NOT NULL,
            compiled_strata_json TEXT NOT NULL,
            source_layers_json TEXT NOT NULL,
            selection_reason TEXT NOT NULL,
            source_bridge TEXT NOT NULL,
            next_probe TEXT NOT NULL,
            expected_failure_mode TEXT NOT NULL,
            gate TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, frontier_id)
        );
        """
    )


def latest_row(conn: sqlite3.Connection, table: str) -> sqlite3.Row:
    row = conn.execute(f"SELECT * FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    if row is None:
        raise RuntimeError(f"missing required row: {table}")
    return row


def q36_books(conn: sqlite3.Connection, q36_run_id: int) -> dict[str, sqlite3.Row]:
    return {
        str(row["bookid"]): row
        for row in conn.execute(
            """
            SELECT *
            FROM human_q36_book_contig_shadow_integration_v1_items
            WHERE run_id=?
            """,
            (q36_run_id,),
        )
    }


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q36 = latest_row(conn, "human_q36_book_contig_shadow_integration_v1_runs")
    audit = latest_row(conn, "human_translation_completion_audit_v5_runs")
    q36_run_id = int(q36["run_id"])
    books = q36_books(conn, q36_run_id)

    items: list[dict[str, object]] = []
    selected_bookids: set[str] = set()
    for frontier in FRONTIERS:
        missing = [bookid for bookid in frontier["bookids"] if bookid not in books]
        if missing:
            raise RuntimeError(f"missing Q36 books for {frontier['frontier_id']}: {missing}")
        rows = [books[bookid] for bookid in frontier["bookids"]]
        contig_hits = [row for row in rows if row["contig_status"] == "EXACT_CONTIG_SHADOW_AVAILABLE"]
        if contig_hits:
            raise RuntimeError(f"frontier contains contig-covered books: {frontier['frontier_id']}")
        selected_bookids.update(frontier["bookids"])
        items.append(
            {
                **frontier,
                "book_count": len(frontier["bookids"]),
                "compiled_strata": sorted({str(row["compiled_stratum"]) for row in rows}),
                "source_layers": sorted({str(row["source_layer"]) for row in rows}),
                "gate": "SOURCE_BRIDGE_OR_FAMILY_CONTRAST_REQUIRED_NO_COMPONENT_GLOSS",
                "evidence": {"q36_books": [dict(row) for row in rows]},
            }
        )

    component_gloss_allowed_count = 0
    canonical_promotion_allowed_count = 0
    decision = (
        "Q37_NONCONTIG_FRONTIER_SELECTION_READY_6_FAMILIES_NO_GLOSS"
        if len(items) == 6
        and len(selected_bookids) == 20
        and int(q36["noncontig_book_count"]) == 56
        and int(audit["promoted_gloss_count"]) == 0
        and component_gloss_allowed_count == 0
        and canonical_promotion_allowed_count == 0
        else "Q37_NONCONTIG_FRONTIER_SELECTION_REQUIRES_REVIEW"
    )
    payload = {
        "question": "Which non-contig families should be explored next for human translation?",
        "answer": "Six precise families are selected, covering 20 non-contig books without touching exact-contig books.",
        "selection_principle": "Prefer small recurring families with existing source bridges or strong internal contrast.",
        "blocked_use": "Do not draft standalone sentence translations from this queue.",
        "next_action": "Run the priority-1 Book30-family atlas consolidation first.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q37_noncontig_frontier_selection_v1_runs (
                created_at, decision, q36_run_id, completion_audit_run_id,
                candidate_frontier_count, selected_frontier_count,
                selected_book_count, contig_shadow_book_count,
                noncontig_book_count, component_gloss_allowed_count,
                canonical_promotion_allowed_count, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                q36_run_id,
                int(audit["run_id"]),
                len(FRONTIERS),
                len(items),
                len(selected_bookids),
                int(q36["contig_shadow_book_count"]),
                int(q36["noncontig_book_count"]),
                component_gloss_allowed_count,
                canonical_promotion_allowed_count,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q37_noncontig_frontier_selection_v1_items (
                run_id, frontier_id, priority, bookids_json, book_count,
                compiled_strata_json, source_layers_json, selection_reason,
                source_bridge, next_probe, expected_failure_mode, gate,
                evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    str(item["frontier_id"]),
                    int(item["priority"]),
                    j(item["bookids"]),
                    int(item["book_count"]),
                    j(item["compiled_strata"]),
                    j(item["source_layers"]),
                    str(item["selection_reason"]),
                    str(item["source_bridge"]),
                    str(item["next_probe"]),
                    str(item["expected_failure_mode"]),
                    str(item["gate"]),
                    j(item["evidence"]),
                )
                for item in items
            ],
        )

    print(
        j(
            {
                "run_id": run_id,
                "decision": decision,
                "selected_frontier_count": len(items),
                "selected_book_count": len(selected_bookids),
                "contig_shadow_book_count": int(q36["contig_shadow_book_count"]),
                "noncontig_book_count": int(q36["noncontig_book_count"]),
                "component_gloss_allowed_count": component_gloss_allowed_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
                "priorities": [item["frontier_id"] for item in sorted(items, key=lambda value: value["priority"])],
            }
        )
    )


if __name__ == "__main__":
    main()
