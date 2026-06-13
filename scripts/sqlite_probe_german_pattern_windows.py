#!/usr/bin/env python3
"""Probe token windows for high-priority German candidate patterns."""

from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "bonelord_operational.sqlite"


PATTERNS = [
    ("sand_home_frame", ["SAND", "IM", "MIN", "HEIME"], "formula_sand_home"),
    ("ruin", ["RUIN"], "formula_ruin_rune"),
    ("rune", ["RUNE"], "formula_ruin_rune"),
    ("runen", ["RUNEN"], "formula_ruin_rune"),
    ("hehl", ["HEHL"], "formula_hechl"),
    ("hel", ["HEL"], "formula_hechl"),
    ("hechl", ["{HECHL}"], "formula_hechl"),
    ("hechelt", ["HECHELT"], "formula_hechl"),
    ("nnr_tag_nd", ["NNR", "TAG", "ND"], "formula_nnr_tag_nd"),
    ("thenaeut", ["THENAEUT"], "formula_thenaeut"),
    ("ei_gen_hehl", ["EI", "GEN", "HEHL"], "formula_ei_gen_hehl"),
    ("ei_gen_hel", ["EI", "GEN", "HEL"], "formula_ei_gen_hehl"),
    ("reder_koenig", ["REDER", "KOENIG"], "demoted_anchor_reder_koenig"),
    ("weichstein", ["WEICHSTEIN"], "demoted_anchor_weichstein"),
    ("orangenstrasse", ["ORANGENSTRASSE"], "demoted_anchor_orangenstrasse"),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def jdump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS german_pattern_window_probe_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_canonical_run_id INTEGER NOT NULL,
            source_policy_run_id INTEGER,
            pattern_count INTEGER NOT NULL,
            occurrence_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS german_pattern_window_probe_items (
            run_id INTEGER NOT NULL,
            pattern_key TEXT NOT NULL,
            family_key TEXT NOT NULL,
            occurrence_count INTEGER NOT NULL,
            book_count INTEGER NOT NULL,
            top_left_json TEXT NOT NULL,
            top_right_json TEXT NOT NULL,
            top_full_window_json TEXT NOT NULL,
            stability_score REAL NOT NULL,
            operational_decision TEXT NOT NULL,
            next_test TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, pattern_key)
        );

        CREATE TABLE IF NOT EXISTS german_pattern_window_probe_occurrences (
            run_id INTEGER NOT NULL,
            pattern_key TEXT NOT NULL,
            bookid TEXT NOT NULL,
            token_index INTEGER NOT NULL,
            left_window TEXT NOT NULL,
            pattern_text TEXT NOT NULL,
            right_window TEXT NOT NULL,
            full_window TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );
        """
    )


def one(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> sqlite3.Row:
    row = conn.execute(sql, params).fetchone()
    if row is None:
        raise SystemExit(f"missing required row for query: {sql}")
    return row


def find_pattern(tokens: list[str], pattern: list[str]) -> list[int]:
    hits: list[int] = []
    n = len(pattern)
    for idx in range(0, len(tokens) - n + 1):
        if tokens[idx : idx + n] == pattern:
            hits.append(idx)
    return hits


def decision_for(pattern_key: str, occurrences: int, stability: float) -> tuple[str, str]:
    if occurrences == 0:
        return "ABSENT", "drop_from_frontier_if_no_materialization"
    if pattern_key in {"orangenstrasse", "reder_koenig", "weichstein"}:
        return "INTERNAL_CLUSTER_ONLY_NOT_LORE_ANCHOR", "window_stability_without_external_promotion"
    if pattern_key in {"hehl", "hel", "hechl", "hechelt"}:
        return "FAMILY_CANDIDATE_WITH_OVERMERGE_RISK", "temporary_family_fold_shadow"
    if pattern_key in {"ruin", "rune", "runen"}:
        return "KEEP_DISTINCT_LEXEME", "neighbor_distribution_no_auto_merge"
    if stability >= 0.55 and occurrences >= 3:
        return "FORMULA_CANDIDATE", "expand_to_larger_repeated_frame"
    return "LOCAL_PATTERN_CANDIDATE", "manual_context_compare"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)

    canonical = one(conn, "SELECT * FROM canonical_candidate_runs ORDER BY run_id DESC LIMIT 1")
    policy = conn.execute("SELECT * FROM german_semantic_policy_runs ORDER BY run_id DESC LIMIT 1").fetchone()
    books = conn.execute(
        """
        SELECT bookid, decoded_primary
        FROM canonical_candidate_books
        WHERE run_id=?
        ORDER BY CAST(bookid AS INTEGER)
        """,
        (canonical["run_id"],),
    ).fetchall()

    cur = conn.execute(
        """
        INSERT INTO german_pattern_window_probe_runs
            (created_at, source_canonical_run_id, source_policy_run_id,
             pattern_count, occurrence_count, payload_json)
        VALUES (?, ?, ?, ?, 0, ?)
        """,
        (
            utc_now(),
            canonical["run_id"],
            policy["run_id"] if policy else None,
            len(PATTERNS),
            jdump({"window_radius": 5, "source": "canonical decoded_primary"}),
        ),
    )
    run_id = int(cur.lastrowid)

    total_occurrences = 0
    for pattern_key, pattern_tokens, family_key in PATTERNS:
        left_counter: Counter[str] = Counter()
        right_counter: Counter[str] = Counter()
        full_counter: Counter[str] = Counter()
        bookids: set[str] = set()
        occurrences = 0
        for row in books:
            text = row["decoded_primary"] or ""
            tokens = text.split()
            for idx in find_pattern(tokens, pattern_tokens):
                occurrences += 1
                total_occurrences += 1
                bookids.add(str(row["bookid"]))
                left = " ".join(tokens[max(0, idx - 5) : idx])
                right = " ".join(tokens[idx + len(pattern_tokens) : idx + len(pattern_tokens) + 5])
                full = " ".join(tokens[max(0, idx - 5) : idx + len(pattern_tokens) + 5])
                left_counter[left] += 1
                right_counter[right] += 1
                full_counter[full] += 1
                conn.execute(
                    """
                    INSERT INTO german_pattern_window_probe_occurrences
                        (run_id, pattern_key, bookid, token_index, left_window,
                         pattern_text, right_window, full_window, payload_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        run_id,
                        pattern_key,
                        str(row["bookid"]),
                        idx,
                        left,
                        " ".join(pattern_tokens),
                        right,
                        full,
                        "{}",
                    ),
                )
        top_left = left_counter.most_common(5)
        top_right = right_counter.most_common(5)
        top_full = full_counter.most_common(8)
        if occurrences:
            left_share = top_left[0][1] / occurrences if top_left else 0.0
            right_share = top_right[0][1] / occurrences if top_right else 0.0
            full_share = top_full[0][1] / occurrences if top_full else 0.0
            stability = round((left_share + right_share + full_share) / 3.0, 4)
        else:
            stability = 0.0
        decision, next_test = decision_for(pattern_key, occurrences, stability)
        conn.execute(
            """
            INSERT INTO german_pattern_window_probe_items
                (run_id, pattern_key, family_key, occurrence_count, book_count,
                 top_left_json, top_right_json, top_full_window_json,
                 stability_score, operational_decision, next_test, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                pattern_key,
                family_key,
                occurrences,
                len(bookids),
                jdump(top_left),
                jdump(top_right),
                jdump(top_full),
                stability,
                decision,
                next_test,
                jdump({"pattern_tokens": pattern_tokens, "bookids": sorted(bookids, key=lambda x: int(x) if x.isdigit() else x)}),
            ),
        )

    conn.execute(
        "UPDATE german_pattern_window_probe_runs SET occurrence_count=? WHERE run_id=?",
        (total_occurrences, run_id),
    )
    conn.commit()

    top = conn.execute(
        """
        SELECT pattern_key, occurrence_count, book_count, stability_score,
               operational_decision, next_test
        FROM german_pattern_window_probe_items
        WHERE run_id=?
        ORDER BY stability_score DESC, occurrence_count DESC, pattern_key
        LIMIT 15
        """,
        (run_id,),
    ).fetchall()
    print(
        json.dumps(
            {
                "probe_run_id": run_id,
                "source_canonical_run_id": int(canonical["run_id"]),
                "pattern_count": len(PATTERNS),
                "occurrence_count": total_occurrences,
                "top_patterns": [dict(row) for row in top],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
