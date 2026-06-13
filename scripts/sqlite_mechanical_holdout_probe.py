#!/usr/bin/env python3
"""Language-free holdout probe for phase/segmentation candidates.

This test avoids German words, formulas, and narrative gloss. It uses repeated
digit windows only:
- split repeated windows into train/holdout by window key;
- learn the consensus decoded signature per window from train occurrences;
- measure holdout conflicts for windows seen in train;
- compare candidate phase modes and negative controls.
"""

from __future__ import annotations

import argparse
import json
import random
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "bonelord_operational.sqlite"

MODES = [
    "all_offset_0",
    "all_offset_1",
    "odd_offset_1_even_0",
    "odd_offset_0_even_1",
    "bookid_parity",
    "bookid_inverse_parity",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def jdump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS mechanical_holdout_probe_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_german_run_id INTEGER NOT NULL,
            window_digits INTEGER NOT NULL,
            split_seed INTEGER NOT NULL,
            holdout_fraction REAL NOT NULL,
            mode_count INTEGER NOT NULL,
            best_mode TEXT NOT NULL,
            best_holdout_consistency REAL NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS mechanical_holdout_probe_items (
            run_id INTEGER NOT NULL,
            mode_key TEXT NOT NULL,
            control_kind TEXT NOT NULL,
            repeated_window_count INTEGER NOT NULL,
            train_window_count INTEGER NOT NULL,
            holdout_window_count INTEGER NOT NULL,
            holdout_occurrences INTEGER NOT NULL,
            exact_match_occurrences INTEGER NOT NULL,
            conflict_occurrences INTEGER NOT NULL,
            unseen_holdout_windows INTEGER NOT NULL,
            holdout_consistency REAL NOT NULL,
            consensus_entropy REAL NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, mode_key, control_kind)
        );
        """
    )


def one(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> sqlite3.Row:
    row = conn.execute(sql, params).fetchone()
    if row is None:
        raise SystemExit(f"missing required row for query: {sql}")
    return row


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


def decode_window(window: str, mapping: dict[str, str], absolute_start: int, offset: int) -> str:
    chars: list[str] = []
    first = 0
    while (absolute_start + first - offset) % 2 != 0 and first < len(window):
        first += 1
    for idx in range(first, len(window) - 1, 2):
        chars.append(mapping.get(window[idx : idx + 2], "?"))
    return "".join(chars)


def build_occurrences(
    books: list[sqlite3.Row],
    mapping: dict[str, str],
    mode: str,
    window_digits: int,
) -> dict[str, list[tuple[str, int, str]]]:
    buckets: dict[str, list[tuple[str, int, str]]] = defaultdict(list)
    for row in books:
        bookid = str(row["bookid"])
        digits = row["digits"]
        offset = offset_for(mode, bookid, digits)
        for start in range(0, len(digits) - window_digits + 1):
            window = digits[start : start + window_digits]
            decoded = decode_window(window, mapping, start, offset)
            buckets[window].append((bookid, start, decoded))
    return buckets


def evaluate_buckets(
    buckets: dict[str, list[tuple[str, int, str]]],
    rng: random.Random,
    holdout_fraction: float,
    min_occurrences: int,
) -> dict[str, Any]:
    repeated = {k: v for k, v in buckets.items() if len(v) >= min_occurrences}
    consensus: dict[str, str] = {}
    holdout_by_key: dict[str, list[tuple[str, int, str]]] = {}
    entropy_parts: list[float] = []
    train_window_count = 0
    holdout_window_count = 0
    for key, occs in repeated.items():
        shuffled = list(occs)
        rng.shuffle(shuffled)
        holdout_size = max(1, int(round(len(shuffled) * holdout_fraction)))
        if holdout_size >= len(shuffled):
            holdout_size = len(shuffled) - 1
        holdout = shuffled[:holdout_size]
        train = shuffled[holdout_size:]
        if not train or not holdout:
            continue
        train_window_count += 1
        holdout_window_count += 1
        holdout_by_key[key] = holdout
        counts = Counter(decoded for _, _, decoded in train)
        total = sum(counts.values())
        consensus[key] = counts.most_common(1)[0][0]
        if total:
            entropy_parts.append(1.0 - counts.most_common(1)[0][1] / total)

    exact = 0
    conflict = 0
    unseen = 0
    holdout_occ = 0
    for key, holdout in holdout_by_key.items():
        if key not in consensus:
            unseen += 1
            continue
        for _, _, decoded in holdout:
            holdout_occ += 1
            if decoded == consensus[key]:
                exact += 1
            else:
                conflict += 1

    consistency = exact / max(1, exact + conflict) * 100.0
    consensus_entropy = sum(entropy_parts) / max(1, len(entropy_parts)) * 100.0
    return {
        "repeated_window_count": len(repeated),
        "train_window_count": train_window_count,
        "holdout_window_count": holdout_window_count,
        "holdout_occurrences": holdout_occ,
        "exact_match_occurrences": exact,
        "conflict_occurrences": conflict,
        "unseen_holdout_windows": unseen,
        "holdout_consistency": round(consistency, 6),
        "consensus_entropy": round(consensus_entropy, 6),
    }


def negative_shuffle_decoded(
    buckets: dict[str, list[tuple[str, int, str]]],
    rng: random.Random,
) -> dict[str, list[tuple[str, int, str]]]:
    all_decoded = [decoded for occs in buckets.values() for _, _, decoded in occs]
    rng.shuffle(all_decoded)
    idx = 0
    out: dict[str, list[tuple[str, int, str]]] = {}
    for key, occs in buckets.items():
        new_occs = []
        for bookid, start, _ in occs:
            new_occs.append((bookid, start, all_decoded[idx]))
            idx += 1
        out[key] = new_occs
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--window-digits", type=int, default=16)
    parser.add_argument("--seed", type=int, default=469)
    parser.add_argument("--holdout-fraction", type=float, default=0.30)
    parser.add_argument("--min-occurrences", type=int, default=3)
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
    books = conn.execute(
        """
        SELECT CAST(bookid AS TEXT) AS bookid, MAX(digits) AS digits
        FROM sheet__books
        WHERE bookid IS NOT NULL
        GROUP BY CAST(bookid AS INTEGER)
        ORDER BY CAST(bookid AS INTEGER)
        """
    ).fetchall()

    rows: list[dict[str, Any]] = []
    for mode in MODES:
        buckets = build_occurrences(books, mapping, mode, args.window_digits)
        stable_seed = sum((idx + 1) * ord(ch) for idx, ch in enumerate(mode))
        result = evaluate_buckets(
            buckets,
            random.Random(args.seed + stable_seed),
            args.holdout_fraction,
            args.min_occurrences,
        )
        rows.append({"mode_key": mode, "control_kind": "observed", **result})
        neg = evaluate_buckets(
            negative_shuffle_decoded(buckets, random.Random(args.seed + 1000 + stable_seed)),
            random.Random(args.seed + 2000 + stable_seed),
            args.holdout_fraction,
            args.min_occurrences,
        )
        rows.append({"mode_key": mode, "control_kind": "decoded_shuffle_negative", **neg})

    observed_rows = [row for row in rows if row["control_kind"] == "observed"]
    best = max(observed_rows, key=lambda x: (x["holdout_consistency"], -x["consensus_entropy"]))
    best_neg = max(
        (row for row in rows if row["control_kind"] != "observed"),
        key=lambda x: x["holdout_consistency"],
    )
    decision = "WEAK_NO_PROMOTION"
    if best["holdout_consistency"] >= best_neg["holdout_consistency"] + 10.0 and best["holdout_consistency"] >= 70.0:
        decision = "SURVIVES_MECHANICAL_HOLDOUT"
    elif best["holdout_consistency"] > best_neg["holdout_consistency"]:
        decision = "PARTIAL_SIGNAL_NEEDS_STRONGER_HOLDOUT"

    cur = conn.execute(
        """
        INSERT INTO mechanical_holdout_probe_runs
            (created_at, source_german_run_id, window_digits, split_seed,
             holdout_fraction, mode_count, best_mode, best_holdout_consistency,
             decision, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            utc_now(),
            german["run_id"],
            args.window_digits,
            args.seed,
            args.holdout_fraction,
            len(MODES),
            best["mode_key"],
            best["holdout_consistency"],
            decision,
            jdump({"min_occurrences": args.min_occurrences, "negative_best": best_neg}),
        ),
    )
    run_id = int(cur.lastrowid)
    for row in rows:
        item_decision = "BEST_OBSERVED" if row["control_kind"] == "observed" and row["mode_key"] == best["mode_key"] else "COMPARE"
        conn.execute(
            """
            INSERT INTO mechanical_holdout_probe_items
                (run_id, mode_key, control_kind, repeated_window_count,
                 train_window_count, holdout_window_count, holdout_occurrences,
                 exact_match_occurrences, conflict_occurrences, unseen_holdout_windows,
                 holdout_consistency, consensus_entropy, decision, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                row["mode_key"],
                row["control_kind"],
                row["repeated_window_count"],
                row["train_window_count"],
                row["holdout_window_count"],
                row["holdout_occurrences"],
                row["exact_match_occurrences"],
                row["conflict_occurrences"],
                row["unseen_holdout_windows"],
                row["holdout_consistency"],
                row["consensus_entropy"],
                item_decision,
                "{}",
            ),
        )
    conn.commit()

    print(
        json.dumps(
            {
                "mechanical_holdout_run_id": run_id,
                "window_digits": args.window_digits,
                "decision": decision,
                "best_mode": best["mode_key"],
                "best_holdout_consistency": best["holdout_consistency"],
                "negative_best": {
                    "mode_key": best_neg["mode_key"],
                    "control_kind": best_neg["control_kind"],
                    "holdout_consistency": best_neg["holdout_consistency"],
                },
                "observed": sorted(
                    [
                        {
                            "mode_key": row["mode_key"],
                            "holdout_consistency": row["holdout_consistency"],
                            "conflict_occurrences": row["conflict_occurrences"],
                            "consensus_entropy": row["consensus_entropy"],
                        }
                        for row in observed_rows
                    ],
                    key=lambda x: -x["holdout_consistency"],
                ),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
