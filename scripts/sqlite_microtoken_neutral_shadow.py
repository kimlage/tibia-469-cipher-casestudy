#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sqlite3
from collections import Counter
from datetime import UTC, datetime
from typing import Any


DEFAULT_DB = "./data/bonelord_operational.sqlite"
DEFAULT_RULES = {
    "fasten I eye of I you've far": "fasten <MICROSEQ:IEIEFI+IVFA>",
    "fasten I eye of I": "fasten <MICROSEQ:IEIEFI>",
    "fasten I eye of": "fasten <MICROSEQ:IEIEF>",
    "I eye of I you've far": "<MICROSEQ:IEIEFI+IVFA>",
    "I eye of I": "<MICROSEQ:IEIEFI>",
    "I eye of": "<MICROSEQ:IEIEF>",
    "eye of I": "<MICROSEQ:EIEFI>",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Neutralize high-risk microtoken formula phrases in a shadow layer")
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--record", action="store_true")
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


def latest_best_shadow(conn: sqlite3.Connection) -> tuple[int | None, list[sqlite3.Row]]:
    run_id = latest_run_id(conn, "best_shadow_book_runs")
    if run_id is None:
        return None, []
    rows = conn.execute(
        """
        SELECT bookid, best_shadow_text, safe_blocked_hit_count, suspect_neutral_hit_count
        FROM best_shadow_book_translations
        WHERE run_id = ?
        ORDER BY CAST(bookid AS INTEGER)
        """,
        (run_id,),
    ).fetchall()
    return run_id, rows


def anomaly_baseline(conn: sqlite3.Connection) -> dict[str, Any]:
    row = conn.execute(
        "SELECT run_id FROM semantic_anomaly_audit_runs "
        "WHERE source='best_shadow' ORDER BY run_id DESC LIMIT 1"
    ).fetchone()
    run_id = int(row["run_id"]) if row else latest_run_id(conn, "semantic_anomaly_audit_runs")
    if run_id is None:
        return {}
    rows = conn.execute(
        """
        SELECT phrase, hit_count, book_count, score
        FROM semantic_anomaly_audit_items
        WHERE run_id = ?
          AND phrase IN ('eye of i', 'i eye of', 'i eye of i', 'fasten i eye of',
                         'fasten i eye of i', 'fasten i eye of i you''ve',
                         'fasten i eye of i you''ve far')
        """,
        (run_id,),
    ).fetchall()
    return {
        str(row["phrase"]): {
            "hit_count": int(row["hit_count"] or 0),
            "book_count": int(row["book_count"] or 0),
            "score": int(row["score"] or 0),
        }
        for row in rows
    }


def apply_rules(text: str) -> tuple[str, list[dict[str, Any]]]:
    output = str(text or "")
    hits: list[dict[str, Any]] = []
    for phrase, replacement in sorted(DEFAULT_RULES.items(), key=lambda item: -len(item[0])):
        pattern = re.compile(rf"(?<![A-Za-z]){re.escape(phrase)}(?![A-Za-z])", re.IGNORECASE)
        count = len(pattern.findall(output))
        if not count:
            continue
        output = pattern.sub(replacement, output)
        hits.append(
            {
                "from": phrase,
                "to": replacement,
                "count": count,
                "reason": "neutralize microtoken formula without demoting component anchors globally",
            }
        )
    return output, hits


def count_phrases(items: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    phrase_stats: dict[str, dict[str, int]] = {}
    for phrase in {key.lower() for key in DEFAULT_RULES} | {"eye of i", "i eye of", "i eye of i"}:
        pattern = re.compile(rf"(?<![A-Za-z]){re.escape(phrase)}(?![A-Za-z])", re.IGNORECASE)
        hit_count = 0
        books = set()
        for item in items:
            count = len(pattern.findall(str(item["microtoken_neutral_text"] or "")))
            if count:
                hit_count += count
                books.add(item["bookid"])
        phrase_stats[phrase] = {"hit_count": hit_count, "book_count": len(books)}
    return phrase_stats


def build_payload(conn: sqlite3.Connection) -> dict[str, Any]:
    best_run_id, rows = latest_best_shadow(conn)
    baseline = anomaly_baseline(conn)
    items: list[dict[str, Any]] = []
    totals: Counter[str] = Counter()
    for row in rows:
        neutral_text, hits = apply_rules(str(row["best_shadow_text"] or ""))
        totals["book_count"] += 1
        if hits:
            totals["books_changed"] += 1
        totals["hit_count"] += sum(int(hit["count"]) for hit in hits)
        unresolved = int(row["safe_blocked_hit_count"] or 0)
        suspect = int(row["suspect_neutral_hit_count"] or 0)
        if unresolved or suspect:
            totals["books_with_unresolved_or_suspect"] += 1
        items.append(
            {
                "bookid": str(row["bookid"]),
                "best_shadow_text": str(row["best_shadow_text"] or ""),
                "microtoken_neutral_text": neutral_text,
                "safe_blocked_hit_count": unresolved,
                "suspect_neutral_hit_count": suspect,
                "hits": hits,
            }
        )
    after = count_phrases(items)
    comparisons: dict[str, Any] = {}
    for phrase, before in baseline.items():
        after_stats = after.get(phrase, {"hit_count": 0, "book_count": 0})
        comparisons[phrase] = {
            "before": before,
            "after": after_stats,
            "hit_delta": after_stats["hit_count"] - before["hit_count"],
            "book_delta": after_stats["book_count"] - before["book_count"],
        }
    clean = totals["book_count"] - totals["books_with_unresolved_or_suspect"]
    return {
        "summary": {
            "best_shadow_run_id": best_run_id,
            "rule_count": len(DEFAULT_RULES),
            "book_count": totals["book_count"],
            "books_changed": totals["books_changed"],
            "hit_count": totals["hit_count"],
            "books_with_unresolved_or_suspect": totals["books_with_unresolved_or_suspect"],
            "microtoken_neutral_clean_pct": round(100.0 * clean / totals["book_count"], 2) if totals["book_count"] else 0.0,
            "comparisons": comparisons,
            "interpretation": "Microtoken-neutral shadow is an audit/readability layer; it does not demote anchors globally.",
        },
        "items": items,
        "rules": DEFAULT_RULES,
    }


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS microtoken_neutral_shadow_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            best_shadow_run_id INTEGER,
            rule_count INTEGER NOT NULL,
            book_count INTEGER NOT NULL,
            books_changed INTEGER NOT NULL,
            hit_count INTEGER NOT NULL,
            books_with_unresolved_or_suspect INTEGER NOT NULL,
            microtoken_neutral_clean_pct REAL NOT NULL,
            comparisons_json TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS microtoken_neutral_shadow_translations (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            best_shadow_text TEXT NOT NULL,
            microtoken_neutral_text TEXT NOT NULL,
            safe_blocked_hit_count INTEGER NOT NULL,
            suspect_neutral_hit_count INTEGER NOT NULL,
            hits_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        );
        """
    )


def record(conn: sqlite3.Connection, payload: dict[str, Any]) -> int:
    ensure_schema(conn)
    summary = payload["summary"]
    created_at = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    cur = conn.execute(
        """
        INSERT INTO microtoken_neutral_shadow_runs (
            created_at, best_shadow_run_id, rule_count, book_count, books_changed,
            hit_count, books_with_unresolved_or_suspect, microtoken_neutral_clean_pct,
            comparisons_json, payload_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            created_at,
            summary["best_shadow_run_id"],
            summary["rule_count"],
            summary["book_count"],
            summary["books_changed"],
            summary["hit_count"],
            summary["books_with_unresolved_or_suspect"],
            summary["microtoken_neutral_clean_pct"],
            json.dumps(summary["comparisons"], ensure_ascii=True, sort_keys=True),
            json.dumps({**summary, "rules": payload["rules"]}, ensure_ascii=True, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)
    for item in payload["items"]:
        conn.execute(
            """
            INSERT INTO microtoken_neutral_shadow_translations (
                run_id, bookid, best_shadow_text, microtoken_neutral_text,
                safe_blocked_hit_count, suspect_neutral_hit_count, hits_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                item["bookid"],
                item["best_shadow_text"],
                item["microtoken_neutral_text"],
                item["safe_blocked_hit_count"],
                item["suspect_neutral_hit_count"],
                json.dumps(item["hits"], ensure_ascii=True, sort_keys=True),
            ),
        )
    conn.commit()
    return run_id


def main() -> int:
    args = parse_args()
    conn = connect(args.db)
    try:
        payload = build_payload(conn)
        run_id = record(conn, payload) if args.record else None
    finally:
        conn.close()
    changed = [item for item in payload["items"] if item["hits"]]
    print(
        json.dumps(
            {
                **payload["summary"],
                "recorded_run_id": run_id,
                "sample_changed": changed[:12],
            },
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
