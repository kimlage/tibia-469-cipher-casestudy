#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sqlite3
from collections import Counter, defaultdict
from datetime import UTC, datetime
from typing import Any


DEFAULT_DB = "./data/bonelord_operational.sqlite"

TOKEN_RE = re.compile(r"<[^>]+>|[A-Za-z']+")
FUNCTION_WORDS = {
    "a",
    "an",
    "and",
    "as",
    "be",
    "do",
    "far",
    "for",
    "from",
    "i",
    "if",
    "in",
    "into",
    "is",
    "it",
    "le",
    "lo",
    "me",
    "no",
    "of",
    "oft",
    "or",
    "so",
    "than",
    "the",
    "to",
    "we",
    "with",
    "you",
    "you've",
    "yet",
}
WEIRD_WORDS = {
    "beeline",
    "belittle",
    "blimey",
    "enable",
    "fasten",
    "incentive",
    "infinite",
    "infinity",
    "intenable",
    "invict",
    "jelly",
    "ore",
    "sestine",
    "sunburn",
    "unfertile",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rank repeated semantic anomaly phrases in best-shadow translations")
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--record", action="store_true")
    parser.add_argument("--min-n", type=int, default=3)
    parser.add_argument("--max-n", type=int, default=9)
    parser.add_argument("--limit", type=int, default=80)
    parser.add_argument(
        "--source",
        choices=["best_shadow", "microtoken_neutral"],
        default="best_shadow",
        help="translation layer to audit",
    )
    return parser.parse_args()


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone() is not None


def latest_run_id(conn: sqlite3.Connection, table: str) -> int | None:
    if not table_exists(conn, table):
        return None
    row = conn.execute(f"SELECT run_id FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    return int(row["run_id"]) if row else None


def latest_translation_rows(conn: sqlite3.Connection, source: str) -> tuple[int | None, str, list[sqlite3.Row]]:
    if source == "microtoken_neutral":
        run_id = latest_run_id(conn, "microtoken_neutral_shadow_runs")
        if run_id is None:
            return None, "microtoken_neutral_shadow_translations", []
        rows = conn.execute(
            """
            SELECT bookid, microtoken_neutral_text AS best_shadow_text
            FROM microtoken_neutral_shadow_translations
            WHERE run_id = ?
            ORDER BY CAST(bookid AS INTEGER)
            """,
            (run_id,),
        ).fetchall()
        return run_id, "microtoken_neutral_shadow_translations", rows

    run_id = latest_run_id(conn, "best_shadow_book_runs")
    if run_id is None:
        return None, "best_shadow_book_translations", []
    rows = conn.execute(
        """
        SELECT bookid, best_shadow_text
        FROM best_shadow_book_translations
        WHERE run_id = ?
        ORDER BY CAST(bookid AS INTEGER)
        """,
        (run_id,),
    ).fetchall()
    return run_id, "best_shadow_book_translations", rows


def normalize_token(token: str) -> str:
    if token.startswith("<") and token.endswith(">"):
        return token
    return token.lower()


def tokenize(text: str) -> list[str]:
    return [normalize_token(token) for token in TOKEN_RE.findall(text or "")]


def phrase_key(tokens: list[str]) -> str:
    return " ".join(tokens)


def score_phrase(tokens: list[str], hit_count: int, book_count: int) -> tuple[int, dict[str, Any]]:
    unknown_count = sum(1 for token in tokens if token.startswith("<UNK:") or token.startswith("<SUSPECT:"))
    marker_count = sum(1 for token in tokens if token.startswith("<") and token.endswith(">") and not token.startswith("<UNK:"))
    weird_count = sum(1 for token in tokens if token in WEIRD_WORDS)
    function_count = sum(1 for token in tokens if token in FUNCTION_WORDS)
    short_run_penalty = sum(1 for token in tokens if len(token) <= 2 and token not in {"i", "a"})
    function_ratio = function_count / max(1, len(tokens))
    repeated_function_score = max(0, function_count - len(set(token for token in tokens if token in FUNCTION_WORDS)))
    score = (
        hit_count * 8
        + book_count * 12
        + unknown_count * 45
        + weird_count * 18
        + repeated_function_score * 10
        + short_run_penalty * 4
        + (12 if function_ratio >= 0.65 and len(tokens) >= 5 else 0)
        - marker_count * 3
    )
    details = {
        "unknown_count": unknown_count,
        "marker_count": marker_count,
        "weird_words": [token for token in tokens if token in WEIRD_WORDS],
        "function_count": function_count,
        "function_ratio": round(function_ratio, 3),
        "repeated_function_score": repeated_function_score,
    }
    return score, details


def recommendation(tokens: list[str], details: dict[str, Any]) -> str:
    phrase = " ".join(tokens)
    if details["unknown_count"]:
        if "enable" in phrase and "sunburn" in phrase:
            return "AUDIT_EBTII_FORMULA_AND_COMPONENT_CHAIN"
        if "last" in phrase and "fine" in phrase:
            return "AUDIT_TTNVVN_FORMULA_SLOT"
        return "RESOLVE_NAMED_UNKNOWN_OR_OWNER_MACRO"
    if "enable" in phrase and "sunburn" in phrase:
        return "AUDIT_COMPONENT_TRANSLATION_CHAIN"
    if "infinite" in phrase and "infinity" in phrase:
        return "AUDIT_REPEATED_END_FORMULA"
    if details["weird_words"]:
        return "CONTRADICTION_REDUCTION_REVIEW"
    if details["function_ratio"] >= 0.65:
        return "SEGMENTATION_OR_STOPWORD_DRIFT_REVIEW"
    return "LOW_PRIORITY"


def build_payload(conn: sqlite3.Connection, min_n: int, max_n: int, limit: int, source: str) -> dict[str, Any]:
    best_run_id, source_table, rows = latest_translation_rows(conn, source)
    buckets: dict[str, dict[str, Any]] = {}
    for row in rows:
        bookid = str(row["bookid"])
        tokens = tokenize(str(row["best_shadow_text"] or ""))
        seen_in_book: set[str] = set()
        for n in range(min_n, max_n + 1):
            if len(tokens) < n:
                continue
            for idx in range(0, len(tokens) - n + 1):
                gram = tokens[idx : idx + n]
                if all(token in FUNCTION_WORDS for token in gram) and n < 5:
                    continue
                key = phrase_key(gram)
                bucket = buckets.setdefault(
                    key,
                    {
                        "phrase": key,
                        "tokens": gram,
                        "hit_count": 0,
                        "books": set(),
                        "examples": [],
                    },
                )
                bucket["hit_count"] += 1
                seen_in_book.add(key)
                if len(bucket["examples"]) < 8:
                    lo = max(0, idx - 4)
                    hi = min(len(tokens), idx + n + 4)
                    bucket["examples"].append({"bookid": bookid, "context": phrase_key(tokens[lo:hi])})
        for key in seen_in_book:
            buckets[key]["books"].add(bookid)

    items: list[dict[str, Any]] = []
    for bucket in buckets.values():
        hit_count = int(bucket["hit_count"])
        book_count = len(bucket["books"])
        if hit_count < 2 and book_count < 2:
            continue
        score, details = score_phrase(bucket["tokens"], hit_count, book_count)
        if score < 35:
            continue
        item = {
            "phrase": bucket["phrase"],
            "n": len(bucket["tokens"]),
            "hit_count": hit_count,
            "book_count": book_count,
            "books": sorted(bucket["books"], key=lambda value: int(value) if value.isdigit() else value),
            "score": score,
            "details": details,
            "examples": bucket["examples"],
        }
        item["recommendation"] = recommendation(bucket["tokens"], details)
        items.append(item)

    items.sort(key=lambda item: (-int(item["score"]), -int(item["book_count"]), -int(item["hit_count"]), item["phrase"]))
    return {
        "best_shadow_run_id": best_run_id,
        "source": source,
        "source_table": source_table,
        "item_count": len(items),
        "items": items[:limit],
        "interpretation": (
            "High-ranked phrases are not proposed translations; they are recurring semantic contradictions or "
            "formula slots that should drive the next hypothesis search."
        ),
    }


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS semantic_anomaly_audit_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            best_shadow_run_id INTEGER,
            source TEXT NOT NULL DEFAULT 'best_shadow',
            source_table TEXT NOT NULL DEFAULT 'best_shadow_book_translations',
            item_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS semantic_anomaly_audit_items (
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

    cols = [str(row["name"]) for row in conn.execute("PRAGMA table_info(semantic_anomaly_audit_runs)").fetchall()]
    if "source" not in cols:
        conn.execute("ALTER TABLE semantic_anomaly_audit_runs ADD COLUMN source TEXT NOT NULL DEFAULT 'best_shadow'")
    if "source_table" not in cols:
        conn.execute(
            "ALTER TABLE semantic_anomaly_audit_runs ADD COLUMN source_table TEXT NOT NULL DEFAULT 'best_shadow_book_translations'"
        )


def record(conn: sqlite3.Connection, payload: dict[str, Any]) -> int:
    ensure_schema(conn)
    created_at = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    cur = conn.execute(
        """
        INSERT INTO semantic_anomaly_audit_runs (
            created_at, best_shadow_run_id, source, source_table, item_count, payload_json
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            created_at,
            payload["best_shadow_run_id"],
            payload["source"],
            payload["source_table"],
            payload["item_count"],
            json.dumps({k: v for k, v in payload.items() if k != "items"}, ensure_ascii=True, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)
    for rank, item in enumerate(payload["items"], start=1):
        conn.execute(
            """
            INSERT INTO semantic_anomaly_audit_items (
                run_id, rank, phrase, n, hit_count, book_count, score,
                recommendation, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                rank,
                item["phrase"],
                item["n"],
                item["hit_count"],
                item["book_count"],
                item["score"],
                item["recommendation"],
                json.dumps(item, ensure_ascii=True, sort_keys=True),
            ),
        )
    conn.commit()
    return run_id


def main() -> int:
    args = parse_args()
    conn = connect(args.db)
    try:
        payload = build_payload(conn, args.min_n, args.max_n, args.limit, args.source)
        run_id = record(conn, payload) if args.record else None
    finally:
        conn.close()

    print(
        json.dumps(
            {
                "recorded_run_id": run_id,
                "best_shadow_run_id": payload["best_shadow_run_id"],
                "source": payload["source"],
                "source_table": payload["source_table"],
                "item_count": payload["item_count"],
                "top": [
                    {
                        "rank": idx,
                        "phrase": item["phrase"],
                        "hits": item["hit_count"],
                        "books": item["book_count"],
                        "score": item["score"],
                        "recommendation": item["recommendation"],
                    }
                    for idx, item in enumerate(payload["items"][:20], start=1)
                ],
            },
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
