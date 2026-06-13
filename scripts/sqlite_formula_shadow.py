#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


DB_PATH = Path(__file__).resolve().parents[1] / "data" / "bonelord_operational.sqlite"

PATTERNS = [
    (
        re.compile(r"\binfinite fasten infinity last <UNK:TTNVVN>\b", re.IGNORECASE),
        "<FORMULA:INFINITE_FASTEN_INFINITY_LAST+UNK_TTNVVN>",
        "formula family with known unresolved TTNVVN slot",
    ),
    (
        re.compile(r"\binfinite fasten infinity last\b", re.IGNORECASE),
        "<FORMULA:INFINITE_FASTEN_INFINITY_LAST>",
        "formula family without visible TTNVVN slot",
    ),
    (
        re.compile(r"\bfasten infinity last <UNK:TTNVVN>\b", re.IGNORECASE),
        "<FORMULA:FASTEN_INFINITY_LAST+UNK_TTNVVN>",
        "formula family with known unresolved TTNVVN slot",
    ),
    (
        re.compile(r"\bfasten infinity last\b", re.IGNORECASE),
        "<FORMULA:FASTEN_INFINITY_LAST>",
        "formula family without visible TTNVVN slot",
    ),
]

FUNCTION_WORDS = {
    "a",
    "an",
    "and",
    "as",
    "be",
    "but",
    "by",
    "for",
    "from",
    "i",
    "if",
    "in",
    "into",
    "is",
    "it",
    "me",
    "my",
    "no",
    "not",
    "of",
    "on",
    "or",
    "so",
    "than",
    "the",
    "their",
    "they",
    "to",
    "we",
    "with",
    "you",
    "you've",
}

WEIRD_WORDS = {
    "belittle",
    "blimey",
    "fasten",
    "infinity",
    "infinite",
    "intenable",
    "sestine",
    "unfertile",
}


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS formula_shadow_runs (
          run_id INTEGER PRIMARY KEY AUTOINCREMENT,
          created_at TEXT NOT NULL,
          source_run_id INTEGER NOT NULL,
          source_table TEXT NOT NULL,
          book_count INTEGER NOT NULL,
          books_changed INTEGER NOT NULL,
          hit_count INTEGER NOT NULL,
          anomaly_count INTEGER NOT NULL,
          top_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS formula_shadow_translations (
          run_id INTEGER NOT NULL,
          bookid TEXT NOT NULL,
          source_text TEXT NOT NULL,
          formula_shadow_text TEXT NOT NULL,
          hits_json TEXT NOT NULL,
          PRIMARY KEY (run_id, bookid)
        );

        CREATE TABLE IF NOT EXISTS formula_shadow_anomaly_items (
          run_id INTEGER NOT NULL,
          rank INTEGER NOT NULL,
          phrase TEXT NOT NULL,
          n INTEGER NOT NULL,
          hit_count INTEGER NOT NULL,
          book_count INTEGER NOT NULL,
          score INTEGER NOT NULL,
          recommendation TEXT NOT NULL,
          payload_json TEXT NOT NULL,
          PRIMARY KEY (run_id, rank)
        );
        """
    )


def latest_source(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT MAX(run_id) AS run_id FROM microtoken_neutral_shadow_runs").fetchone()
    if not row or row["run_id"] is None:
        raise SystemExit("no microtoken neutral shadow run found")
    return int(row["run_id"])


def normalize(text: str) -> list[str]:
    text = text.lower()
    text = re.sub(r"<formula:[^>]+>", " formula_marker ", text)
    text = re.sub(r"<microseq:[^>]+>", " microseq_marker ", text)
    text = re.sub(r"<unk:[^>]+>", " unknown_marker ", text)
    text = re.sub(r"[^a-z0-9_'*]+", " ", text)
    return [tok for tok in text.split() if tok]


def score_phrase(tokens: tuple[str, ...], hit_count: int, book_count: int) -> tuple[int, str, dict[str, object]]:
    function_count = sum(1 for tok in tokens if tok in FUNCTION_WORDS)
    weird = [tok for tok in tokens if tok in WEIRD_WORDS]
    marker_count = sum(1 for tok in tokens if tok.endswith("_marker"))
    repeated_function_score = sum(
        1 for a, b in zip(tokens, tokens[1:]) if a == b and a in FUNCTION_WORDS
    )
    function_ratio = function_count / len(tokens)
    score = hit_count * 10 + book_count * 10
    if weird:
        score += 18
    if function_ratio >= 0.6:
        score += 12
    if repeated_function_score:
        score += 10 * repeated_function_score
    if marker_count:
        score -= 20 * marker_count
    if len(tokens) > 5:
        score -= 10
    if weird:
        recommendation = "CONTRADICTION_REDUCTION_REVIEW"
    elif repeated_function_score or function_ratio >= 0.6:
        recommendation = "SEGMENTATION_OR_STOPWORD_DRIFT_REVIEW"
    else:
        recommendation = "LOW_PRIORITY"
    details = {
        "function_count": function_count,
        "function_ratio": round(function_ratio, 3),
        "marker_count": marker_count,
        "repeated_function_score": repeated_function_score,
        "weird_words": weird,
    }
    return score, recommendation, details


def anomaly_top(rows: list[dict[str, object]], limit: int) -> list[dict[str, object]]:
    counts: Counter[tuple[str, ...]] = Counter()
    books: dict[tuple[str, ...], set[str]] = defaultdict(set)
    examples: dict[tuple[str, ...], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        tokens = normalize(str(row["formula_shadow_text"]))
        bookid = str(row["bookid"])
        for n in range(3, 8):
            for idx in range(0, max(0, len(tokens) - n + 1)):
                gram = tuple(tokens[idx : idx + n])
                if "formula_marker" in gram or "microseq_marker" in gram or "unknown_marker" in gram:
                    continue
                counts[gram] += 1
                books[gram].add(bookid)
                if len(examples[gram]) < 8:
                    start = max(0, idx - 3)
                    end = min(len(tokens), idx + n + 4)
                    examples[gram].append({"bookid": bookid, "context": " ".join(tokens[start:end])})

    ranked: list[dict[str, object]] = []
    for gram, hit_count in counts.items():
        book_count = len(books[gram])
        if hit_count < 6 or book_count < 6:
            continue
        score, recommendation, details = score_phrase(gram, hit_count, book_count)
        phrase = " ".join(gram)
        ranked.append(
            {
                "phrase": phrase,
                "n": len(gram),
                "hit_count": hit_count,
                "book_count": book_count,
                "score": score,
                "recommendation": recommendation,
                "payload": {
                    "phrase": phrase,
                    "n": len(gram),
                    "hit_count": hit_count,
                    "book_count": book_count,
                    "books": sorted(books[gram], key=lambda x: int(x) if x.isdigit() else x),
                    "details": details,
                    "examples": examples[gram],
                },
            }
        )
    ranked.sort(key=lambda item: (-int(item["score"]), -int(item["hit_count"]), item["phrase"]))
    return ranked[:limit]


def materialize(conn: sqlite3.Connection, limit: int) -> dict[str, object]:
    ensure_schema(conn)
    source_run_id = latest_source(conn)
    source_rows = conn.execute(
        """
        SELECT bookid, microtoken_neutral_text AS text
        FROM microtoken_neutral_shadow_translations
        WHERE run_id=?
        ORDER BY CAST(bookid AS INTEGER)
        """,
        (source_run_id,),
    ).fetchall()

    rows: list[dict[str, object]] = []
    books_changed = 0
    hit_count = 0
    for row in source_rows:
        text = str(row["text"])
        hits: list[dict[str, object]] = []
        new_text = text
        for pattern, replacement, reason in PATTERNS:
            new_text, count = pattern.subn(replacement, new_text)
            if count:
                hit_count += count
                hits.append(
                    {
                        "from": pattern.pattern,
                        "to": replacement,
                        "count": count,
                        "reason": reason,
                    }
                )
        if new_text != text:
            books_changed += 1
        rows.append(
            {
                "bookid": str(row["bookid"]),
                "source_text": text,
                "formula_shadow_text": new_text,
                "hits": hits,
            }
        )

    top = anomaly_top(rows, limit)
    cur = conn.execute(
        """
        INSERT INTO formula_shadow_runs (
          created_at, source_run_id, source_table, book_count, books_changed,
          hit_count, anomaly_count, top_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            now(),
            source_run_id,
            "microtoken_neutral_shadow_translations",
            len(rows),
            books_changed,
            hit_count,
            len(top),
            json.dumps(top, ensure_ascii=True, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)
    for row in rows:
        conn.execute(
            """
            INSERT INTO formula_shadow_translations (
              run_id, bookid, source_text, formula_shadow_text, hits_json
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                run_id,
                row["bookid"],
                row["source_text"],
                row["formula_shadow_text"],
                json.dumps(row["hits"], ensure_ascii=True, sort_keys=True),
            ),
        )
    for idx, item in enumerate(top, start=1):
        conn.execute(
            """
            INSERT INTO formula_shadow_anomaly_items (
              run_id, rank, phrase, n, hit_count, book_count, score, recommendation, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                idx,
                item["phrase"],
                int(item["n"]),
                int(item["hit_count"]),
                int(item["book_count"]),
                int(item["score"]),
                item["recommendation"],
                json.dumps(item["payload"], ensure_ascii=True, sort_keys=True),
            ),
        )
    conn.commit()
    return {
        "recorded_run_id": run_id,
        "source_run_id": source_run_id,
        "book_count": len(rows),
        "books_changed": books_changed,
        "hit_count": hit_count,
        "top": [
            {
                "rank": idx,
                "phrase": item["phrase"],
                "hit_count": item["hit_count"],
                "book_count": item["book_count"],
                "score": item["score"],
                "recommendation": item["recommendation"],
            }
            for idx, item in enumerate(top[:20], start=1)
        ],
        "sample_changed": [
            {
                "bookid": row["bookid"],
                "hits": row["hits"],
                "formula_shadow_text": row["formula_shadow_text"],
            }
            for row in rows
            if row["hits"]
        ][:8],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DB_PATH)
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args()

    with connect(args.db) as conn:
        result = materialize(conn, args.limit)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
