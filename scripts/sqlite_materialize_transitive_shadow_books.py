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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply stale macro transitive display corrections to best-shadow books")
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--record", action="store_true")
    parser.add_argument("--max-rules", type=int, default=120)
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


def safe_json(raw: object, default: Any) -> Any:
    if raw in (None, ""):
        return default
    try:
        return json.loads(str(raw))
    except json.JSONDecodeError:
        return default


def latest_stale_rules(conn: sqlite3.Connection, max_rules: int) -> tuple[int | None, list[dict[str, Any]]]:
    run_id = latest_run_id(conn, "stale_macro_transitive_audit_runs")
    if run_id is None:
        return None, []
    rows = conn.execute(
        """
        SELECT payload_json
        FROM stale_macro_transitive_audit_items
        WHERE run_id = ?
          AND recommendation IN ('DISPLAY_RECOMPOSE_TRANSITIVE_KEEP_TII_UNKNOWN', 'RECOMPOSE_FROM_AUDITED_COMPONENTS')
        ORDER BY severity DESC, length(token) DESC, token
        LIMIT ?
        """,
        (run_id, max_rules),
    ).fetchall()
    rules: list[dict[str, Any]] = []
    for row in rows:
        payload = safe_json(row["payload_json"], {})
        original = str(payload.get("original_translation") or "")
        audited = str(payload.get("audited_recomposed_translation") or "")
        transitive = str(payload.get("transitive_component_render") or "")
        if not transitive:
            continue
        for phrase in [audited, original]:
            if not phrase or phrase == transitive:
                continue
            rules.append(
                {
                    "token": payload.get("token"),
                    "phrase": phrase,
                    "replacement": transitive,
                    "recommendation": payload.get("recommendation"),
                    "severity": payload.get("severity"),
                    "reasons": payload.get("reasons"),
                }
            )
    unique: dict[tuple[str, str], dict[str, Any]] = {}
    for rule in rules:
        unique[(str(rule["phrase"]), str(rule["replacement"]))] = rule
    out = list(unique.values())
    out.sort(key=lambda rule: (-len(str(rule["phrase"])), -int(rule.get("severity") or 0), str(rule.get("token") or "")))
    return run_id, out


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


def apply_rules(text: str, rules: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
    output = str(text or "")
    hits: list[dict[str, Any]] = []
    for rule in rules:
        phrase = str(rule["phrase"])
        replacement = str(rule["replacement"])
        pattern = re.compile(rf"(?<![A-Za-z]){re.escape(phrase)}(?![A-Za-z])", re.IGNORECASE)
        count = len(pattern.findall(output))
        if not count:
            continue
        output = pattern.sub(replacement, output)
        hits.append(
            {
                "token": rule.get("token"),
                "from": phrase,
                "to": replacement,
                "count": count,
                "severity": rule.get("severity"),
                "reasons": rule.get("reasons"),
                "apply_mode": "TRANSITIVE_STALE_MACRO_DISPLAY",
            }
        )
    return output, hits


def build_payload(conn: sqlite3.Connection, max_rules: int) -> dict[str, Any]:
    stale_run_id, rules = latest_stale_rules(conn, max_rules)
    best_run_id, rows = latest_best_shadow(conn)
    items: list[dict[str, Any]] = []
    totals: Counter[str] = Counter()
    for row in rows:
        text, hits = apply_rules(str(row["best_shadow_text"] or ""), rules)
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
                "transitive_shadow_text": text,
                "safe_blocked_hit_count": unresolved,
                "suspect_neutral_hit_count": suspect,
                "hits": hits,
            }
        )
    clean = totals["book_count"] - totals["books_with_unresolved_or_suspect"]
    return {
        "summary": {
            "best_shadow_run_id": best_run_id,
            "stale_macro_transitive_audit_run_id": stale_run_id,
            "rule_count": len(rules),
            "book_count": totals["book_count"],
            "books_changed": totals["books_changed"],
            "hit_count": totals["hit_count"],
            "books_with_unresolved_or_suspect": totals["books_with_unresolved_or_suspect"],
            "transitive_shadow_clean_pct": round(100.0 * clean / totals["book_count"], 2) if totals["book_count"] else 0.0,
            "interpretation": "Transitive shadow fixes stale macro display only; it does not promote unknown lexical values.",
        },
        "rules": rules,
        "items": items,
    }


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS transitive_shadow_book_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            best_shadow_run_id INTEGER,
            stale_macro_transitive_audit_run_id INTEGER,
            rule_count INTEGER NOT NULL,
            book_count INTEGER NOT NULL,
            books_changed INTEGER NOT NULL,
            hit_count INTEGER NOT NULL,
            books_with_unresolved_or_suspect INTEGER NOT NULL,
            transitive_shadow_clean_pct REAL NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS transitive_shadow_book_translations (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            best_shadow_text TEXT NOT NULL,
            transitive_shadow_text TEXT NOT NULL,
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
        INSERT INTO transitive_shadow_book_runs (
            created_at, best_shadow_run_id, stale_macro_transitive_audit_run_id,
            rule_count, book_count, books_changed, hit_count,
            books_with_unresolved_or_suspect, transitive_shadow_clean_pct, payload_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            created_at,
            summary["best_shadow_run_id"],
            summary["stale_macro_transitive_audit_run_id"],
            summary["rule_count"],
            summary["book_count"],
            summary["books_changed"],
            summary["hit_count"],
            summary["books_with_unresolved_or_suspect"],
            summary["transitive_shadow_clean_pct"],
            json.dumps({**summary, "rules": payload["rules"]}, ensure_ascii=True, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)
    for item in payload["items"]:
        conn.execute(
            """
            INSERT INTO transitive_shadow_book_translations (
                run_id, bookid, best_shadow_text, transitive_shadow_text,
                safe_blocked_hit_count, suspect_neutral_hit_count, hits_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                item["bookid"],
                item["best_shadow_text"],
                item["transitive_shadow_text"],
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
        payload = build_payload(conn, args.max_rules)
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
