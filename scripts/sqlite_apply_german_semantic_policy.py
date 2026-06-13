#!/usr/bin/env python3
"""Apply a conservative semantic policy to the German/MHG candidate.

This creates a display/audit layer. It does not mutate the primary decoded
German text and it does not invent final English translations.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "bonelord_operational.sqlite"


RULES = [
    {
        "rule_key": "join_wi_nd_unruh",
        "class": "mechanical_join",
        "pattern": r"\bWI ND UNRUH\b",
        "replacement": "WIND UNRUH",
        "confidence": "MEDIUM_HIGH",
        "rationale": "WI ND UNRUH is better treated as WIND UNRUH than as separate words.",
    },
    {
        "rule_key": "oede_lexical_safe",
        "class": "lexical_safe",
        "pattern": r"\bOEDE\b",
        "replacement": "OEDE[wasteland?]",
        "confidence": "MEDIUM_HIGH",
        "rationale": "OEDE is plausible German Oede/oede, desolation or wasteland.",
    },
    {
        "rule_key": "wisten_conditional",
        "class": "lexical_conditional",
        "pattern": r"\bWISTEN\b",
        "replacement": "WISTEN[knew?]",
        "confidence": "MEDIUM",
        "rationale": "WISTEN is plausible wissen/wussten only in verbal contexts.",
    },
    {
        "rule_key": "schardt_name_only",
        "class": "display_name_only",
        "pattern": r"\bSCHARDT\b",
        "replacement": "<NAME:SCHARDT>",
        "confidence": "MEDIUM",
        "rationale": "SCHARDT is likely a proper name/toponym, not a common word.",
    },
    {
        "rule_key": "thenaeut_name_unknown",
        "class": "display_name_only",
        "pattern": r"\bTHENAEUT\b",
        "replacement": "<NAME?:THENAEUT>",
        "confidence": "LOW_MEDIUM",
        "rationale": "THENAEUT lacks a defensible German reading; preserve as entity/unknown.",
    },
    {
        "rule_key": "nnr_unknown",
        "class": "suspect_microtoken",
        "pattern": r"\bNNR\b",
        "replacement": "<UNK:NNR>",
        "confidence": "HIGH",
        "rationale": "NNR has no plausible German reading in current contexts.",
    },
    {
        "rule_key": "tee_suspect",
        "class": "suspect_microtoken",
        "pattern": r"\bTEE\b",
        "replacement": "<SUSPECT:TEE>",
        "confidence": "HIGH",
        "rationale": "TEE as tea is semantically/anachronistically suspect here.",
    },
    {
        "rule_key": "sce_suspect",
        "class": "suspect_microtoken",
        "pattern": r"\bSCE\b",
        "replacement": "<SUSPECT:SCE>",
        "confidence": "MEDIUM_HIGH",
        "rationale": "SCE may be a sch-/sche fragment but should not be glossed freely.",
    },
    {
        "rule_key": "nd_isolated_microseq",
        "class": "suspect_microtoken",
        "pattern": r"\bND\b",
        "replacement": "<MICROSEQ:ND>",
        "confidence": "MEDIUM",
        "rationale": "ND isolated is not a stable word; it may be a fragment of UND or another split.",
    },
    {
        "rule_key": "hehl_cautious",
        "class": "lexical_conditional",
        "pattern": r"\bHEHL\b",
        "replacement": "HEHL[concealment?]",
        "confidence": "LOW_MEDIUM",
        "rationale": "HEHL is plausible concealment but syntactically unstable in repeated formulas.",
    },
]


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
        CREATE TABLE IF NOT EXISTS german_semantic_policy_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_canonical_run_id INTEGER NOT NULL,
            rule_count INTEGER NOT NULL,
            affected_books INTEGER NOT NULL,
            total_replacements INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS german_semantic_policy_rules (
            run_id INTEGER NOT NULL,
            rule_key TEXT NOT NULL,
            rule_class TEXT NOT NULL,
            pattern TEXT NOT NULL,
            replacement TEXT NOT NULL,
            confidence TEXT NOT NULL,
            rationale TEXT NOT NULL,
            hit_count INTEGER NOT NULL,
            PRIMARY KEY (run_id, rule_key)
        );

        CREATE TABLE IF NOT EXISTS german_semantic_stabilized_books (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            source_canonical_run_id INTEGER NOT NULL,
            coverage_pct REAL,
            unknown_brace_count INTEGER NOT NULL,
            policy_hit_count INTEGER NOT NULL,
            decoded_primary TEXT NOT NULL,
            stabilized_display TEXT NOT NULL,
            english_gloss_original TEXT,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        );

        CREATE INDEX IF NOT EXISTS idx_german_semantic_stabilized_books_hits
            ON german_semantic_stabilized_books(run_id, policy_hit_count DESC, coverage_pct);
        """
    )


def apply_rules(text: str) -> tuple[str, dict[str, int]]:
    out = text
    hits: dict[str, int] = {}
    for rule in RULES:
        out, count = re.subn(rule["pattern"], rule["replacement"], out)
        hits[rule["rule_key"]] = count
    return out, hits


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)

    canonical = one(conn, "SELECT * FROM canonical_candidate_runs ORDER BY run_id DESC LIMIT 1")
    books = conn.execute(
        """
        SELECT *
        FROM canonical_candidate_books
        WHERE run_id=?
        ORDER BY CAST(bookid AS INTEGER)
        """,
        (canonical["run_id"],),
    ).fetchall()

    cur = conn.execute(
        """
        INSERT INTO german_semantic_policy_runs
            (created_at, source_canonical_run_id, rule_count, affected_books,
             total_replacements, payload_json)
        VALUES (?, ?, ?, 0, 0, ?)
        """,
        (
            utc_now(),
            canonical["run_id"],
            len(RULES),
            jdump(
                {
                    "policy": "anti_hallucination_display_layer",
                    "primary_decode_unchanged": True,
                    "source": "Beauvoir linguistic audit",
                }
            ),
        ),
    )
    run_id = int(cur.lastrowid)

    rule_totals = {rule["rule_key"]: 0 for rule in RULES}
    affected_books = 0
    total_replacements = 0
    for row in books:
        primary = row["decoded_primary"] or ""
        stabilized, hits = apply_rules(primary)
        hit_count = sum(hits.values())
        if hit_count:
            affected_books += 1
            total_replacements += hit_count
        for key, count in hits.items():
            rule_totals[key] += count
        conn.execute(
            """
            INSERT INTO german_semantic_stabilized_books
                (run_id, bookid, source_canonical_run_id, coverage_pct,
                 unknown_brace_count, policy_hit_count, decoded_primary,
                 stabilized_display, english_gloss_original, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                row["bookid"],
                canonical["run_id"],
                row["coverage_pct"],
                row["unknown_brace_count"],
                hit_count,
                primary,
                stabilized,
                row["english_gloss"],
                jdump({"rule_hits": hits}),
            ),
        )

    for rule in RULES:
        conn.execute(
            """
            INSERT INTO german_semantic_policy_rules
                (run_id, rule_key, rule_class, pattern, replacement,
                 confidence, rationale, hit_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                rule["rule_key"],
                rule["class"],
                rule["pattern"],
                rule["replacement"],
                rule["confidence"],
                rule["rationale"],
                rule_totals[rule["rule_key"]],
            ),
        )

    conn.execute(
        """
        UPDATE german_semantic_policy_runs
        SET affected_books=?, total_replacements=?
        WHERE run_id=?
        """,
        (affected_books, total_replacements, run_id),
    )
    conn.commit()

    top_books = conn.execute(
        """
        SELECT bookid, coverage_pct, policy_hit_count, substr(stabilized_display, 1, 180) AS sample
        FROM german_semantic_stabilized_books
        WHERE run_id=?
        ORDER BY policy_hit_count DESC, coverage_pct ASC
        LIMIT 12
        """,
        (run_id,),
    ).fetchall()
    print(
        json.dumps(
            {
                "policy_run_id": run_id,
                "source_canonical_run_id": int(canonical["run_id"]),
                "rule_count": len(RULES),
                "affected_books": affected_books,
                "total_replacements": total_replacements,
                "rule_totals": rule_totals,
                "top_books": [dict(row) for row in top_books],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
