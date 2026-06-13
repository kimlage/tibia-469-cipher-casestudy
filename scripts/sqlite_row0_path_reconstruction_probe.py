#!/usr/bin/env python3
"""Enumerate row0 reinsertion paths and score reconstructed pair streams."""

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


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def jdump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS row0_path_reconstruction_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_row0_probe_run_id INTEGER,
            source_german_run_id INTEGER NOT NULL,
            target_books INTEGER NOT NULL,
            path_candidates INTEGER NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS row0_path_reconstruction_items (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            path_rank INTEGER NOT NULL,
            omit_pattern_1based TEXT NOT NULL,
            reconstructed_digits TEXT NOT NULL,
            reconstructed_len INTEGER NOT NULL,
            pair_count INTEGER NOT NULL,
            unmapped_pairs INTEGER NOT NULL,
            unused_pair_count INTEGER NOT NULL,
            decoded_text TEXT NOT NULL,
            decoded_entropy REAL NOT NULL,
            repeated_pair_score REAL NOT NULL,
            consistency_score REAL NOT NULL,
            selected INTEGER NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid, path_rank)
        );

        CREATE INDEX IF NOT EXISTS idx_row0_path_reconstruction_selected
            ON row0_path_reconstruction_items(run_id, selected, consistency_score DESC);
        """
    )


def one(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> sqlite3.Row:
    row = conn.execute(sql, params).fetchone()
    if row is None:
        raise SystemExit(f"missing required row for query: {sql}")
    return row


def parse_patterns(raw: str | None, fallback: str | None) -> list[list[int]]:
    source = raw or fallback or ""
    patterns = []
    for part in source.split("|"):
        nums = [int(x.strip()) for x in part.split(",") if x.strip().isdigit()]
        if nums:
            patterns.append(nums)
    return patterns


def reconstruct(digits: str, omitted_positions: list[int]) -> str:
    out = list(digits)
    # Positions are 1-based in reconstructed/base stream. Insert in ascending
    # order adjusted by prior insertions into the observed string.
    inserted = 0
    for pos in sorted(omitted_positions):
        idx = max(0, min(len(out), pos - 1))
        out.insert(idx, "0")
        inserted += 1
    return "".join(out)


def decode_pairs(digits: str, mapping: dict[str, str]) -> tuple[str, int, int]:
    chars: list[str] = []
    unmapped = 0
    unused_zero_pairs = 0
    for idx in range(0, len(digits) - 1, 2):
        pair = digits[idx : idx + 2]
        ch = mapping.get(pair)
        if ch is None:
            unmapped += 1
            chars.append("?")
        else:
            chars.append(ch)
        if pair in {"07", "32", "33"}:
            unused_zero_pairs += 1
    return "".join(chars), unmapped, unused_zero_pairs


def entropy_score(text: str) -> float:
    if not text:
        return 0.0
    counts = Counter(text)
    total = len(text)
    top_share = counts.most_common(1)[0][1] / total
    return round((1.0 - top_share) * 100.0, 6)


def pair_repeat_score(digits: str) -> float:
    pairs = [digits[i : i + 2] for i in range(0, len(digits) - 1, 2)]
    if not pairs:
        return 0.0
    counts = Counter(pairs)
    repeated = sum(c for c in counts.values() if c > 1)
    return round(repeated / len(pairs) * 100.0, 6)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--only-risk", action="store_true")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)

    german = one(conn, "SELECT * FROM german_candidate_runs ORDER BY run_id DESC LIMIT 1")
    row0_run = conn.execute("SELECT * FROM row0_omission_probe_runs ORDER BY run_id DESC LIMIT 1").fetchone()
    mapping = {
        row["code"]: row["letter"]
        for row in conn.execute(
            "SELECT code, letter FROM external_candidate_solution_mapping WHERE run_id=?",
            (german["candidate_solution_run_id"],),
        )
    }
    where = "WHERE CAST(m.pathcount AS INTEGER) > 1 OR CAST(m.insertedzeros AS INTEGER) > 0" if args.only_risk else ""
    rows = conn.execute(
        f"""
        SELECT m.*, b.digits
        FROM sheet__booksdigitmodel_v118 m
        JOIN (
            SELECT CAST(bookid AS TEXT) AS bookid, MAX(digits) AS digits
            FROM sheet__books
            WHERE bookid IS NOT NULL
            GROUP BY CAST(bookid AS INTEGER)
        ) b USING (bookid)
        {where}
        ORDER BY CAST(m.pathcount AS INTEGER) DESC,
                 CAST(m.insertedzeros AS INTEGER) DESC,
                 CAST(m.bookid AS INTEGER)
        LIMIT ?
        """,
        (args.limit,),
    ).fetchall()

    cur = conn.execute(
        """
        INSERT INTO row0_path_reconstruction_runs
            (created_at, source_row0_probe_run_id, source_german_run_id,
             target_books, path_candidates, decision, payload_json)
        VALUES (?, ?, ?, ?, 0, ?, ?)
        """,
        (
            utc_now(),
            row0_run["run_id"] if row0_run else None,
            german["run_id"],
            len(rows),
            "PENDING",
            jdump({"limit": args.limit, "only_risk": args.only_risk}),
        ),
    )
    run_id = int(cur.lastrowid)
    total_paths = 0
    selected_summary = []
    for row in rows:
        patterns = parse_patterns(row["altomitpatterns_1based"], row["omitidxs_1based"])
        if not patterns and int(row["insertedzeros"] or 0) == 0:
            patterns = [[]]
        candidates = []
        for idx, pattern in enumerate(patterns, start=1):
            rec = reconstruct(row["digits"], pattern)
            decoded, unmapped, unused = decode_pairs(rec, mapping)
            ent = entropy_score(decoded)
            repeat = pair_repeat_score(rec)
            # Structural score only: full even reconstruction, no unmapped pairs,
            # stable letter distribution, and not relying on corpus-unvalidated pairs.
            even_bonus = 25.0 if len(rec) % 2 == 0 else -50.0
            score = even_bonus + ent * 0.45 + repeat * 0.15 - unmapped * 10.0 - unused * 2.0
            candidates.append(
                {
                    "path_rank": idx,
                    "pattern": pattern,
                    "rec": rec,
                    "decoded": decoded,
                    "unmapped": unmapped,
                    "unused": unused,
                    "ent": ent,
                    "repeat": repeat,
                    "score": round(score, 6),
                }
            )
        if not candidates:
            continue
        best_score = max(c["score"] for c in candidates)
        for cand in candidates:
            selected = 1 if cand["score"] == best_score else 0
            if selected:
                selected_summary.append(
                    {
                        "bookid": str(row["bookid"]),
                        "path_rank": cand["path_rank"],
                        "score": cand["score"],
                        "unmapped": cand["unmapped"],
                        "unused": cand["unused"],
                    }
                )
            total_paths += 1
            conn.execute(
                """
                INSERT INTO row0_path_reconstruction_items
                    (run_id, bookid, path_rank, omit_pattern_1based,
                     reconstructed_digits, reconstructed_len, pair_count,
                     unmapped_pairs, unused_pair_count, decoded_text,
                     decoded_entropy, repeated_pair_score, consistency_score,
                     selected, decision, payload_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    str(row["bookid"]),
                    cand["path_rank"],
                    ",".join(str(x) for x in cand["pattern"]),
                    cand["rec"],
                    len(cand["rec"]),
                    len(cand["rec"]) // 2,
                    cand["unmapped"],
                    cand["unused"],
                    cand["decoded"],
                    cand["ent"],
                    cand["repeat"],
                    cand["score"],
                    selected,
                    "SELECTED_BY_STRUCTURAL_SCORE" if selected else "ALTERNATE_PATH",
                    jdump({"insertedzeros": row["insertedzeros"], "pathcount": row["pathcount"]}),
                ),
            )
    conn.execute(
        """
        UPDATE row0_path_reconstruction_runs
        SET path_candidates=?,
            decision=?,
            payload_json=?
        WHERE run_id=?
        """,
        (
            total_paths,
            "ROW0_PATHS_ENUMERATED_FOR_STRUCTURAL_SCORING",
            jdump({"selected_summary": selected_summary[:20]}),
            run_id,
        ),
    )
    conn.commit()

    top = conn.execute(
        """
        SELECT bookid, path_rank, reconstructed_len, pair_count, unmapped_pairs,
               unused_pair_count, decoded_entropy, repeated_pair_score,
               consistency_score, selected, substr(decoded_text, 1, 80) AS decoded_sample
        FROM row0_path_reconstruction_items
        WHERE run_id=? AND selected=1
        ORDER BY consistency_score DESC, CAST(bookid AS INTEGER)
        LIMIT 20
        """,
        (run_id,),
    ).fetchall()
    print(
        json.dumps(
            {
                "row0_path_run_id": run_id,
                "target_books": len(rows),
                "path_candidates": total_paths,
                "decision": "ROW0_PATHS_ENUMERATED_FOR_STRUCTURAL_SCORING",
                "selected": [dict(row) for row in top],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
