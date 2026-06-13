#!/usr/bin/env python3
"""Probe phase/segmentation alternatives for the 2-digit homophonic hypothesis."""

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

FORMULAS = [
    "SANDIMMINHEIME",
    "DIEURALTESTEIN",
    "ISTSCHAUNRUIN",
    "REDERKOENIG",
    "ORANGENSTRASSE",
    "WEICHSTEIN",
    "THENAEUT",
    "RUNE",
    "RUIN",
    "EID",
    "DIENSTORT",
]

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
        CREATE TABLE IF NOT EXISTS phase_segmentation_probe_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_german_run_id INTEGER NOT NULL,
            source_validation_run_id INTEGER NOT NULL,
            candidate_count INTEGER NOT NULL,
            best_candidate_key TEXT NOT NULL,
            best_total_score REAL NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS phase_segmentation_probe_items (
            run_id INTEGER NOT NULL,
            candidate_key TEXT NOT NULL,
            offset_mode TEXT NOT NULL,
            book_count INTEGER NOT NULL,
            decoded_letters INTEGER NOT NULL,
            unknown_pairs INTEGER NOT NULL,
            terminal_singletons INTEGER NOT NULL,
            trigram_score REAL NOT NULL,
            formula_hits INTEGER NOT NULL,
            formula_books_json TEXT NOT NULL,
            vowel_score REAL NOT NULL,
            entropy_score REAL NOT NULL,
            total_score REAL NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, candidate_key)
        );
        """
    )


def decode(digits: str, mapping: dict[str, str], offset: int) -> tuple[str, int, int]:
    usable = digits[offset:]
    chars: list[str] = []
    unknown = 0
    for idx in range(0, len(usable) - 1, 2):
        pair = usable[idx : idx + 2]
        ch = mapping.get(pair, "?")
        if ch == "?":
            unknown += 1
        chars.append(ch)
    terminal = len(usable) % 2
    return "".join(chars), unknown, terminal


def score_candidate(book_texts: dict[str, str]) -> dict[str, Any]:
    corpus = " ".join(book_texts.values())
    letters = [ch for ch in corpus if ch.isalpha()]
    total = len(letters)
    if total == 0:
        return {
            "trigram_score": 0.0,
            "formula_hits": 0,
            "formula_books": {},
            "vowel_score": 0.0,
            "entropy_score": 0.0,
            "total_score": 0.0,
        }
    trigrams = [corpus[i : i + 3] for i in range(len(corpus) - 2)]
    trigram_hits = sum(1 for tri in trigrams if tri in COMMON_TRIGRAMS)
    trigram_score = trigram_hits / max(1, len(trigrams)) * 100.0
    formula_books: dict[str, list[str]] = {}
    formula_hits = 0
    for formula in FORMULAS:
        hits = [bookid for bookid, text in book_texts.items() if formula in text]
        if hits:
            formula_books[formula] = hits
            formula_hits += len(hits)
    counts = Counter(letters)
    vowel_share = sum(counts[ch] for ch in "AEIOU") / total
    vowel_score = max(0.0, 100.0 - abs(vowel_share - 0.40) * 250.0)
    entropy = -sum((c / total) * math.log(c / total) for c in counts.values())
    entropy_score = entropy * 20.0
    total_score = trigram_score * 2.0 + formula_hits * 3.0 + vowel_score * 0.30 + entropy_score * 0.25
    return {
        "trigram_score": round(trigram_score, 6),
        "formula_hits": formula_hits,
        "formula_books": formula_books,
        "vowel_score": round(vowel_score, 6),
        "entropy_score": round(entropy_score, 6),
        "total_score": round(total_score, 6),
    }


def offset_for(mode: str, bookid: str, digits: str) -> int:
    if mode == "all_offset_0":
        return 0
    if mode == "all_offset_1":
        return 1
    if mode == "odd_offset_1_even_0":
        return 1 if len(digits) % 2 else 0
    if mode == "odd_offset_0_even_1":
        return 0 if len(digits) % 2 else 1
    if mode == "bookid_parity":
        return int(bookid) % 2
    if mode == "bookid_inverse_parity":
        return 1 - (int(bookid) % 2)
    raise ValueError(mode)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)

    german = one(conn, "SELECT * FROM german_candidate_runs ORDER BY run_id DESC LIMIT 1")
    validation = one(conn, "SELECT * FROM external_candidate_validation_runs WHERE run_id=?", (german["validation_run_id"],))
    mapping = {
        row["code"]: row["letter"]
        for row in conn.execute(
            "SELECT code, letter FROM external_candidate_solution_mapping WHERE run_id=?",
            (german["candidate_solution_run_id"],),
        )
    }
    rows = conn.execute(
        """
        SELECT CAST(bookid AS INTEGER) AS bookid_int, CAST(bookid AS TEXT) AS bookid, MAX(digits) AS digits
        FROM sheet__books
        WHERE bookid IS NOT NULL
        GROUP BY CAST(bookid AS INTEGER)
        ORDER BY CAST(bookid AS INTEGER)
        """
    ).fetchall()

    modes = [
        "all_offset_0",
        "all_offset_1",
        "odd_offset_1_even_0",
        "odd_offset_0_even_1",
        "bookid_parity",
        "bookid_inverse_parity",
    ]
    candidates: list[dict[str, Any]] = []
    for mode in modes:
        texts: dict[str, str] = {}
        unknown_pairs = 0
        terminal_singletons = 0
        decoded_letters = 0
        for row in rows:
            offset = offset_for(mode, str(row["bookid"]), row["digits"])
            text, unk, terminal = decode(row["digits"], mapping, offset)
            texts[str(row["bookid"])] = text
            unknown_pairs += unk
            terminal_singletons += terminal
            decoded_letters += len(text)
        scores = score_candidate(texts)
        candidates.append(
            {
                "candidate_key": mode,
                "offset_mode": mode,
                "book_count": len(rows),
                "decoded_letters": decoded_letters,
                "unknown_pairs": unknown_pairs,
                "terminal_singletons": terminal_singletons,
                **scores,
            }
        )

    best = max(candidates, key=lambda x: x["total_score"])
    cur = conn.execute(
        """
        INSERT INTO phase_segmentation_probe_runs
            (created_at, source_german_run_id, source_validation_run_id,
             candidate_count, best_candidate_key, best_total_score, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            utc_now(),
            german["run_id"],
            validation["run_id"],
            len(candidates),
            best["candidate_key"],
            best["total_score"],
            jdump({"warning": "lightweight heuristic; use for prioritization only"}),
        ),
    )
    run_id = int(cur.lastrowid)
    for cand in candidates:
        if cand["candidate_key"] == best["candidate_key"]:
            decision = "BEST_LIGHTWEIGHT_PHASE"
        elif cand["candidate_key"] == "all_offset_0":
            decision = "EXTERNAL_BASELINE_PHASE"
        else:
            decision = "COMPARE_ONLY"
        conn.execute(
            """
            INSERT INTO phase_segmentation_probe_items
                (run_id, candidate_key, offset_mode, book_count, decoded_letters,
                 unknown_pairs, terminal_singletons, trigram_score, formula_hits,
                 formula_books_json, vowel_score, entropy_score, total_score,
                 decision, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                cand["candidate_key"],
                cand["offset_mode"],
                cand["book_count"],
                cand["decoded_letters"],
                cand["unknown_pairs"],
                cand["terminal_singletons"],
                cand["trigram_score"],
                cand["formula_hits"],
                jdump(cand["formula_books"]),
                cand["vowel_score"],
                cand["entropy_score"],
                cand["total_score"],
                decision,
                "{}",
            ),
        )
    conn.commit()

    print(
        json.dumps(
            {
                "phase_probe_run_id": run_id,
                "best_candidate_key": best["candidate_key"],
                "best_total_score": best["total_score"],
                "candidates": [
                    {
                        "candidate_key": cand["candidate_key"],
                        "total_score": cand["total_score"],
                        "formula_hits": cand["formula_hits"],
                        "trigram_score": cand["trigram_score"],
                        "unknown_pairs": cand["unknown_pairs"],
                        "terminal_singletons": cand["terminal_singletons"],
                    }
                    for cand in sorted(candidates, key=lambda x: -x["total_score"])
                ],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
