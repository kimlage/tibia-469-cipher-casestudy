#!/usr/bin/env python3
"""Run blind-ish validation probes for the external German homophonic mapping.

Current probes:
- random baseline preserving letter capacities;
- phase/offset comparison;
- unvalidated code audit.

This is intentionally statistical/mechanical, not semantic prose generation.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "bonelord_operational.sqlite"


GERMAN_COMMON = {
    "DER",
    "DIE",
    "DAS",
    "UND",
    "IST",
    "ICH",
    "NICHT",
    "EIN",
    "EINE",
    "DEN",
    "DEM",
    "DES",
    "IM",
    "IN",
    "ER",
    "SIE",
    "WIR",
    "NUR",
    "ZU",
    "MIT",
    "AN",
    "AUF",
    "GEN",
    "SEIN",
    "SEINE",
    "ORT",
    "HAND",
    "TAG",
    "NACHT",
    "TOT",
    "TOD",
    "RUNE",
    "RUNEN",
    "RUIN",
    "STEIN",
    "WORT",
    "EID",
    "DIENST",
    "TREU",
    "ALT",
    "ALTES",
    "URALTE",
    "SAND",
    "HEIME",
    "FINDEN",
}

COMMON_BIGRAMS = {
    "CH",
    "ER",
    "EN",
    "IN",
    "EI",
    "IE",
    "ND",
    "DE",
    "TE",
    "GE",
    "ES",
    "ST",
    "UN",
    "RE",
    "AN",
    "DI",
    "SC",
    "HE",
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
        CREATE TABLE IF NOT EXISTS german_blind_validation_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_german_run_id INTEGER NOT NULL,
            source_validation_run_id INTEGER NOT NULL,
            random_trials INTEGER NOT NULL,
            real_score REAL NOT NULL,
            random_mean REAL NOT NULL,
            random_std REAL NOT NULL,
            random_best REAL NOT NULL,
            real_percentile REAL NOT NULL,
            phase0_score REAL NOT NULL,
            phase1_score REAL NOT NULL,
            phase_margin REAL NOT NULL,
            unvalidated_codes_json TEXT NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );
        """
    )


def decode_pairs(digits: str, mapping: dict[str, str], offset: int = 0) -> str:
    out: list[str] = []
    usable = digits[offset:]
    for idx in range(0, len(usable) - 1, 2):
        pair = usable[idx : idx + 2]
        out.append(mapping.get(pair, "?"))
    return "".join(out)


def score_text(text: str) -> float:
    if not text:
        return 0.0
    letters = [ch for ch in text if ch.isalpha()]
    if not letters:
        return 0.0
    letter_counts = Counter(letters)
    total = len(letters)
    vowel_share = sum(letter_counts[ch] for ch in "AEIOU") / total
    e_share = letter_counts["E"] / total
    n_share = letter_counts["N"] / total
    entropy = -sum((c / total) * math.log(c / total) for c in letter_counts.values())
    bigrams = [text[i : i + 2] for i in range(len(text) - 1)]
    common_bigram_hits = sum(1 for bg in bigrams if bg in COMMON_BIGRAMS)
    bigram_score = common_bigram_hits / max(1, len(bigrams))
    token_bonus = 0.0
    spaced = " ".join(text.split("?"))
    for token in GERMAN_COMMON:
        token_bonus += spaced.count(token) * min(1.0, len(token) / 5.0)
    token_bonus /= max(1.0, len(text) / 20.0)
    vowel_penalty = abs(vowel_share - 0.40)
    e_penalty = abs(e_share - 0.17)
    n_penalty = abs(n_share - 0.10)
    return round(
        100.0 * (0.35 * bigram_score + 0.25 * token_bonus + 0.20 * (1.0 - vowel_penalty) + 0.10 * (1.0 - e_penalty) + 0.10 * (1.0 - n_penalty))
        + entropy,
        6,
    )


def score_corpus(digit_rows: list[str], mapping: dict[str, str], offset: int = 0) -> float:
    text = " ".join(decode_pairs(d, mapping, offset=offset) for d in digit_rows)
    return score_text(text)


def shuffled_mapping(mapping: dict[str, str], rng: random.Random) -> dict[str, str]:
    codes = list(mapping.keys())
    letters = [mapping[code] for code in codes]
    rng.shuffle(letters)
    return dict(zip(codes, letters))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--trials", type=int, default=500)
    parser.add_argument("--seed", type=int, default=469)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)

    german = one(conn, "SELECT * FROM german_candidate_runs ORDER BY run_id DESC LIMIT 1")
    validation = one(conn, "SELECT * FROM external_candidate_validation_runs WHERE run_id=?", (german["validation_run_id"],))
    mapping_rows = conn.execute(
        """
        SELECT code, letter
        FROM external_candidate_solution_mapping
        WHERE run_id=?
        ORDER BY code
        """,
        (german["candidate_solution_run_id"],),
    ).fetchall()
    mapping = {row["code"]: row["letter"] for row in mapping_rows}
    digit_rows = [
        row["digits"]
        for row in conn.execute(
            """
            SELECT digits
            FROM sheet__books
            WHERE bookid IS NOT NULL
            GROUP BY CAST(bookid AS INTEGER)
            ORDER BY CAST(bookid AS INTEGER)
            """
        )
        if row["digits"]
    ]

    real_score = score_corpus(digit_rows, mapping, offset=0)
    phase1_score = score_corpus(digit_rows, mapping, offset=1)
    rng = random.Random(args.seed)
    random_scores = [score_corpus(digit_rows, shuffled_mapping(mapping, rng), offset=0) for _ in range(args.trials)]
    random_mean = sum(random_scores) / len(random_scores)
    random_var = sum((x - random_mean) ** 2 for x in random_scores) / len(random_scores)
    random_std = math.sqrt(random_var)
    random_best = max(random_scores)
    below = sum(1 for score in random_scores if score < real_score)
    percentile = below / len(random_scores) * 100.0

    observed_pairs = set()
    for digits in digit_rows:
        for idx in range(0, len(digits) - 1, 2):
            observed_pairs.add(digits[idx : idx + 2])
    unvalidated = sorted(code for code in mapping if code not in observed_pairs)
    unmapped_observed = sorted(pair for pair in observed_pairs if pair not in mapping)

    if percentile >= 99.0 and real_score > random_best and real_score > phase1_score * 1.05:
        decision = "SURVIVES_INITIAL_BLIND_BASELINES"
    elif percentile >= 95.0 and real_score > phase1_score:
        decision = "PARTIAL_SIGNAL_NEEDS_STRONGER_TESTS"
    else:
        decision = "FAILS_OR_WEAK_INITIAL_BLIND_BASELINES"

    conn.execute(
        """
        INSERT INTO german_blind_validation_runs
            (created_at, source_german_run_id, source_validation_run_id, random_trials,
             real_score, random_mean, random_std, random_best, real_percentile,
             phase0_score, phase1_score, phase_margin, unvalidated_codes_json,
             decision, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            utc_now(),
            german["run_id"],
            validation["run_id"],
            args.trials,
            real_score,
            random_mean,
            random_std,
            random_best,
            percentile,
            real_score,
            phase1_score,
            real_score - phase1_score,
            jdump({"mapped_unused": unvalidated, "observed_unmapped": unmapped_observed}),
            decision,
            jdump({"score_is_lightweight": True, "seed": args.seed}),
        ),
    )
    conn.commit()

    print(
        json.dumps(
            {
                "decision": decision,
                "real_score": real_score,
                "random_trials": args.trials,
                "random_mean": round(random_mean, 6),
                "random_std": round(random_std, 6),
                "random_best": random_best,
                "real_percentile": round(percentile, 2),
                "phase0_score": real_score,
                "phase1_score": phase1_score,
                "phase_margin": round(real_score - phase1_score, 6),
                "unvalidated_codes": {"mapped_unused": unvalidated, "observed_unmapped": unmapped_observed},
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
