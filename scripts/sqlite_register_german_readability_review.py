#!/usr/bin/env python3
"""Register manual/agent readability review for stabilized German candidate."""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "bonelord_operational.sqlite"


FOCUS_DECISIONS = [
    ("formula_sand_home", "ALIVE_FORMULAIC", ["11", "32", "36", "43", "58", "59"], "Strongest repeated frame; use 11/32/43 as clean exemplars."),
    ("formula_ruin_rune", "ALIVE_SUSPECT", ["0", "6", "9", "22", "37", "47", "58", "59", "69"], "Real repeated motif, but English gloss is inflated; keep RUIN/RUNE distinct."),
    ("book49_block", "DEAD_OR_OVERFIT", ["49"], "Worst coverage, many unresolved groups; treat as segmentation/alignment problem before semantics."),
    ("book30_opening_formula", "NEXT_MECHANICAL_TEST", ["30"], "Possible formula but too opaque for translation; inspect structure first."),
    ("formula_rr_in_rh", "DEAD_OR_OVERFIT", ["20", "54"], "Dominated by suspect markers; not semantically legible."),
    ("book55_final_nominal", "SUSPECT", ["55"], "German-like surface but critical nominal lacuna remains unresolved."),
    ("formula_nnr_tag_nd", "NEXT_MECHANICAL_TEST", ["6", "7"], "Repeated ritual/time-like slot but NNR/ND remain microtoken suspects."),
    ("formula_hechl", "SUSPECT", ["28", "64"], "Terminal/boundary-like repetition, not enough for gloss."),
    ("formula_ei_gen_hehl", "SUSPECT", ["34"], "Possible formula; concealment gloss is display-level only."),
    ("formula_thenaeut", "ALIVE_NAME_SUSPECT_SEMANTICS", ["12", "21", "24", "26", "30"], "Useful entity-like token; semantics still suspect."),
]

BOOK_CLASSES = {
    "ALIVE": ["11", "12", "22", "32", "43", "69"],
    "SUSPECT": ["0", "9", "21", "24", "26", "28", "34", "36", "37", "47", "55", "58", "59", "64"],
    "DEAD_OR_OVERFIT": ["20", "49", "54"],
    "NEXT_MECHANICAL_TEST": ["6", "7", "30"],
}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def jdump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def one(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> sqlite3.Row:
    row = conn.execute(sql, params).fetchone()
    if row is None:
        raise SystemExit(f"missing required row for query: {sql}")
    return row


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS german_readability_review_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_canonical_run_id INTEGER NOT NULL,
            source_policy_run_id INTEGER,
            source_adjusted_frontier_run_id INTEGER,
            focus_count INTEGER NOT NULL,
            alive_books INTEGER NOT NULL,
            suspect_books INTEGER NOT NULL,
            dead_or_overfit_books INTEGER NOT NULL,
            next_mechanical_books INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS german_readability_focus_items (
            run_id INTEGER NOT NULL,
            focus_key TEXT NOT NULL,
            readability_decision TEXT NOT NULL,
            bookids_json TEXT NOT NULL,
            note TEXT NOT NULL,
            next_action TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, focus_key)
        );

        CREATE TABLE IF NOT EXISTS german_readability_book_items (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            readability_class TEXT NOT NULL,
            coverage_pct REAL,
            unknown_brace_count INTEGER,
            policy_hit_count INTEGER,
            short_sample TEXT,
            next_action TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        );
        """
    )


def next_action_for(decision: str) -> str:
    if decision == "ALIVE_FORMULAIC":
        return "expand_repeated_frame_and_compare_clean_exemplars"
    if decision == "ALIVE_SUSPECT":
        return "neighbor_distribution_before_semantic_gloss"
    if decision == "DEAD_OR_OVERFIT":
        return "mechanical_resegmentation_or_exclude_from_semantic_progress"
    if decision == "NEXT_MECHANICAL_TEST":
        return "pair_boundary_and_variant_test_before_gloss"
    if decision == "ALIVE_NAME_SUSPECT_SEMANTICS":
        return "entity_cluster_stability_no_external_lore_promotion"
    return "manual_context_compare"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)

    canonical = one(conn, "SELECT * FROM canonical_candidate_runs ORDER BY run_id DESC LIMIT 1")
    policy = conn.execute("SELECT * FROM german_semantic_policy_runs ORDER BY run_id DESC LIMIT 1").fetchone()
    frontier = conn.execute("SELECT * FROM german_semantic_frontier_adjusted_runs ORDER BY run_id DESC LIMIT 1").fetchone()
    cur = conn.execute(
        """
        INSERT INTO german_readability_review_runs
            (created_at, source_canonical_run_id, source_policy_run_id,
             source_adjusted_frontier_run_id, focus_count, alive_books,
             suspect_books, dead_or_overfit_books, next_mechanical_books, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            utc_now(),
            canonical["run_id"],
            policy["run_id"] if policy else None,
            frontier["run_id"] if frontier else None,
            len(FOCUS_DECISIONS),
            len(BOOK_CLASSES["ALIVE"]),
            len(BOOK_CLASSES["SUSPECT"]),
            len(BOOK_CLASSES["DEAD_OR_OVERFIT"]),
            len(BOOK_CLASSES["NEXT_MECHANICAL_TEST"]),
            jdump({"source": "agent semantic readability review", "principle": "do not count German-like collation as solved"}),
        ),
    )
    run_id = int(cur.lastrowid)

    for focus_key, decision, bookids, note in FOCUS_DECISIONS:
        conn.execute(
            """
            INSERT INTO german_readability_focus_items
                (run_id, focus_key, readability_decision, bookids_json,
                 note, next_action, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, focus_key, decision, jdump(bookids), note, next_action_for(decision), "{}"),
        )

    stabilized = {}
    if policy:
        for row in conn.execute(
            """
            SELECT *
            FROM german_semantic_stabilized_books
            WHERE run_id=?
            """,
            (policy["run_id"],),
        ):
            stabilized[str(row["bookid"])] = row

    for cls, bookids in BOOK_CLASSES.items():
        for bookid in bookids:
            row = stabilized.get(bookid)
            if cls == "ALIVE":
                next_action = "use_as_clean_exemplar_for_pattern_comparison"
            elif cls == "SUSPECT":
                next_action = "keep_in_frontier_but_require_pattern_support"
            elif cls == "DEAD_OR_OVERFIT":
                next_action = "do_not_use_for_semantic_progress_until_resegmented"
            else:
                next_action = "run_mechanical_boundary_test_before_translation"
            conn.execute(
                """
                INSERT INTO german_readability_book_items
                    (run_id, bookid, readability_class, coverage_pct,
                     unknown_brace_count, policy_hit_count, short_sample,
                     next_action, payload_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    bookid,
                    cls,
                    row["coverage_pct"] if row else None,
                    row["unknown_brace_count"] if row else None,
                    row["policy_hit_count"] if row else None,
                    (row["stabilized_display"][:220] if row and row["stabilized_display"] else None),
                    next_action,
                    "{}",
                ),
            )

    conn.commit()
    print(
        json.dumps(
            {
                "readability_run_id": run_id,
                "source_canonical_run_id": int(canonical["run_id"]),
                "focus_count": len(FOCUS_DECISIONS),
                "classes": {k: len(v) for k, v in BOOK_CLASSES.items()},
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
