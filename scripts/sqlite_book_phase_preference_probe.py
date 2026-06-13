#!/usr/bin/env python3
"""Score offset 0 vs offset 1 per book for the homophonic mapping."""

from __future__ import annotations

import argparse
import json
import math
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "bonelord_operational.sqlite"

COMMON_TRIGRAMS = {
    "DER",
    "DIE",
    "UND",
    "ICH",
    "SCH",
    "EIN",
    "NDE",
    "DEN",
    "GEN",
    "STE",
    "TEN",
    "CHT",
    "TER",
    "ENE",
    "ERE",
    "UNG",
    "HEI",
    "EID",
    "RUN",
    "SIE",
    "IST",
    "ORT",
}

FORMULAS = [
    "SANDIMMINHEIME",
    "DIEURALTESTEIN",
    "ISTSCHAUNRUIN",
    "REDERKOENIG",
    "ORANGENSTRASSE",
    "WEICHSTEIN",
    "THENAEUT",
    "RUNEMANIER",
    "RUNENEID",
    "DIENSTORT",
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
        CREATE TABLE IF NOT EXISTS book_phase_preference_probe_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_german_run_id INTEGER NOT NULL,
            preferred_offset0_books INTEGER NOT NULL,
            preferred_offset1_books INTEGER NOT NULL,
            tied_books INTEGER NOT NULL,
            avg_abs_margin REAL NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS book_phase_preference_probe_items (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            digit_len INTEGER NOT NULL,
            terminal_digit TEXT,
            offset0_score REAL NOT NULL,
            offset1_score REAL NOT NULL,
            score_margin REAL NOT NULL,
            preferred_offset INTEGER NOT NULL,
            confidence TEXT NOT NULL,
            offset0_text TEXT NOT NULL,
            offset1_text TEXT NOT NULL,
            offset0_formulas_json TEXT NOT NULL,
            offset1_formulas_json TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        );
        """
    )


def decode(digits: str, mapping: dict[str, str], offset: int) -> str:
    chars = []
    usable = digits[offset:]
    for idx in range(0, len(usable) - 1, 2):
        chars.append(mapping.get(usable[idx : idx + 2], "?"))
    return "".join(chars)


def score(text: str) -> tuple[float, list[str], dict[str, Any]]:
    trigrams = [text[i : i + 3] for i in range(len(text) - 2)]
    tri_hits = sum(1 for tri in trigrams if tri in COMMON_TRIGRAMS)
    tri_score = tri_hits / max(1, len(trigrams)) * 100.0
    formulas = [formula for formula in FORMULAS if formula in text]
    letters = [ch for ch in text if ch.isalpha()]
    counts = Counter(letters)
    total = len(letters)
    if total:
        vowel_share = sum(counts[ch] for ch in "AEIOU") / total
        e_share = counts["E"] / total
        n_share = counts["N"] / total
        entropy = -sum((c / total) * math.log(c / total) for c in counts.values())
        vowel_component = max(0.0, 1.0 - abs(vowel_share - 0.40)) * 20.0
        e_component = max(0.0, 1.0 - abs(e_share - 0.17)) * 10.0
        n_component = max(0.0, 1.0 - abs(n_share - 0.10)) * 10.0
        entropy_component = entropy * 4.0
    else:
        vowel_share = e_share = n_share = entropy = 0.0
        vowel_component = e_component = n_component = entropy_component = 0.0
    total_score = tri_score * 2.0 + len(formulas) * 18.0 + vowel_component + e_component + n_component + entropy_component
    return (
        round(total_score, 6),
        formulas,
        {
            "trigram_hits": tri_hits,
            "trigram_score": round(tri_score, 6),
            "vowel_share": round(vowel_share, 6),
            "e_share": round(e_share, 6),
            "n_share": round(n_share, 6),
            "entropy": round(entropy, 6),
        },
    )


def confidence(margin: float) -> str:
    abs_margin = abs(margin)
    if abs_margin >= 25:
        return "HIGH"
    if abs_margin >= 12:
        return "MEDIUM"
    if abs_margin >= 5:
        return "LOW"
    return "TIE_OR_WEAK"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)

    german = one(conn, "SELECT * FROM german_candidate_runs ORDER BY run_id DESC LIMIT 1")
    mapping = {
        row["code"]: row["letter"]
        for row in conn.execute(
            "SELECT code, letter FROM external_candidate_solution_mapping WHERE run_id=?",
            (german["candidate_solution_run_id"],),
        )
    }
    rows = conn.execute(
        """
        SELECT CAST(bookid AS TEXT) AS bookid, MAX(digits) AS digits
        FROM sheet__books
        WHERE bookid IS NOT NULL
        GROUP BY CAST(bookid AS INTEGER)
        ORDER BY CAST(bookid AS INTEGER)
        """
    ).fetchall()

    results: list[dict[str, Any]] = []
    for row in rows:
        digits = row["digits"]
        text0 = decode(digits, mapping, 0)
        text1 = decode(digits, mapping, 1)
        score0, formulas0, detail0 = score(text0)
        score1, formulas1, detail1 = score(text1)
        margin = score0 - score1
        preferred = 0 if margin >= 0 else 1
        results.append(
            {
                "bookid": str(row["bookid"]),
                "digit_len": len(digits),
                "terminal_digit": digits[-1] if len(digits) % 2 else None,
                "offset0_score": score0,
                "offset1_score": score1,
                "score_margin": round(margin, 6),
                "preferred_offset": preferred,
                "confidence": confidence(margin),
                "offset0_text": text0,
                "offset1_text": text1,
                "offset0_formulas": formulas0,
                "offset1_formulas": formulas1,
                "detail0": detail0,
                "detail1": detail1,
            }
        )

    pref0 = sum(1 for r in results if r["preferred_offset"] == 0 and r["confidence"] != "TIE_OR_WEAK")
    pref1 = sum(1 for r in results if r["preferred_offset"] == 1 and r["confidence"] != "TIE_OR_WEAK")
    ties = sum(1 for r in results if r["confidence"] == "TIE_OR_WEAK")
    avg_abs = sum(abs(r["score_margin"]) for r in results) / len(results)
    cur = conn.execute(
        """
        INSERT INTO book_phase_preference_probe_runs
            (created_at, source_german_run_id, preferred_offset0_books,
             preferred_offset1_books, tied_books, avg_abs_margin, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            utc_now(),
            german["run_id"],
            pref0,
            pref1,
            ties,
            round(avg_abs, 6),
            jdump({"warning": "book-local heuristic; does not prove phase"}),
        ),
    )
    run_id = int(cur.lastrowid)
    for r in results:
        conn.execute(
            """
            INSERT INTO book_phase_preference_probe_items
                (run_id, bookid, digit_len, terminal_digit, offset0_score,
                 offset1_score, score_margin, preferred_offset, confidence,
                 offset0_text, offset1_text, offset0_formulas_json,
                 offset1_formulas_json, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                r["bookid"],
                r["digit_len"],
                r["terminal_digit"],
                r["offset0_score"],
                r["offset1_score"],
                r["score_margin"],
                r["preferred_offset"],
                r["confidence"],
                r["offset0_text"],
                r["offset1_text"],
                jdump(r["offset0_formulas"]),
                jdump(r["offset1_formulas"]),
                jdump({"offset0": r["detail0"], "offset1": r["detail1"]}),
            ),
        )
    conn.commit()

    print(
        json.dumps(
            {
                "book_phase_run_id": run_id,
                "preferred_offset0_books": pref0,
                "preferred_offset1_books": pref1,
                "tied_books": ties,
                "avg_abs_margin": round(avg_abs, 6),
                "strongest_offset0": [
                    {
                        "bookid": r["bookid"],
                        "margin": r["score_margin"],
                        "confidence": r["confidence"],
                        "formulas": r["offset0_formulas"],
                    }
                    for r in sorted(results, key=lambda x: -x["score_margin"])[:10]
                ],
                "strongest_offset1": [
                    {
                        "bookid": r["bookid"],
                        "margin": r["score_margin"],
                        "confidence": r["confidence"],
                        "formulas": r["offset1_formulas"],
                    }
                    for r in sorted(results, key=lambda x: x["score_margin"])[:10]
                ],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
