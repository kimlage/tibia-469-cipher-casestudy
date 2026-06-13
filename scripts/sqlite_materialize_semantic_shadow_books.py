#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sqlite3
from collections import Counter
from datetime import UTC, datetime
from typing import Any, Dict, List


DEFAULT_DB = "./data/bonelord_operational.sqlite"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Materialize a shadow reading layer with suspect semantic retexts neutralized")
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--record", action="store_true")
    parser.add_argument("--max-output-books", type=int, default=20)
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


def latest_constraints(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    if not table_exists(conn, "semantic_constraint_registry"):
        return []
    rows = conn.execute(
        """
        SELECT token, decision, confidence, blocked_old_hint, reason, reopen_condition, payload_json
        FROM semantic_constraint_registry
        WHERE constraint_id IN (
            SELECT max(constraint_id)
            FROM semantic_constraint_registry
            GROUP BY token
        )
        ORDER BY token
        """
    ).fetchall()
    return [dict(row) for row in rows]


def glossary_translations(conn: sqlite3.Connection) -> Dict[str, str]:
    rows = conn.execute(
        """
        SELECT token, translation
        FROM sheet__glossary
        WHERE __export_id = 2
          AND token IS NOT NULL
        """
    ).fetchall()
    return {str(row["token"]): str(row["translation"] or "") for row in rows}


def build_rules(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    glossary = glossary_translations(conn)
    rules: List[Dict[str, Any]] = []
    for constraint in latest_constraints(conn):
        decision = str(constraint["decision"] or "")
        if not decision.startswith("SUSPECT_"):
            continue
        token = str(constraint["token"])
        phrase = str(constraint.get("blocked_old_hint") or glossary.get(token) or "").strip()
        if not phrase or phrase.lower().startswith("<unk"):
            continue
        marker = f"<SUSPECT:{token}>"
        payload = safe_json(constraint.get("payload_json"), {})
        rules.append(
            {
                "token": token,
                "phrase": phrase,
                "marker": marker,
                "decision": decision,
                "confidence": constraint.get("confidence"),
                "reason": constraint.get("reason"),
                "payload": payload,
            }
        )
    rules.sort(key=lambda item: (-len(item["phrase"]), item["phrase"]))
    return rules


def apply_rules(text: str, rules: List[Dict[str, Any]]) -> tuple[str, List[Dict[str, Any]]]:
    output = str(text or "")
    hits: List[Dict[str, Any]] = []
    for rule in rules:
        phrase = rule["phrase"]
        pattern = re.compile(rf"(?<![A-Za-z]){re.escape(phrase)}(?![A-Za-z])", re.IGNORECASE)
        count = len(pattern.findall(output))
        if not count:
            continue
        output = pattern.sub(rule["marker"], output)
        hits.append(
            {
                "token": rule["token"],
                "phrase": phrase,
                "replacement": rule["marker"],
                "count": count,
                "decision": rule["decision"],
                "confidence": rule["confidence"],
                "reason": rule["reason"],
            }
        )
    return output, hits


def materialize(conn: sqlite3.Connection, rules: List[Dict[str, Any]]) -> Dict[str, Any]:
    safe_run_id = latest_run_id(conn, "safe_book_translation_runs")
    if safe_run_id is None:
        raise RuntimeError("safe_book_translation_runs has no rows")
    rows = conn.execute(
        """
        SELECT bookid, safe_text, source_text, strictplus_text, macrocompressed_text,
               blocked_hit_count, caution_hit_count, risk_score, hits_json
        FROM safe_book_translations
        WHERE run_id = ?
        ORDER BY CAST(bookid AS INTEGER)
        """,
        (safe_run_id,),
    ).fetchall()
    items: List[Dict[str, Any]] = []
    totals: Counter[str] = Counter()
    for row in rows:
        shadow_text, hits = apply_rules(str(row["safe_text"] or ""), rules)
        totals["book_count"] += 1
        if hits:
            totals["books_with_shadow_hits"] += 1
        totals["shadow_hit_count"] += sum(int(hit["count"]) for hit in hits)
        items.append(
            {
                "bookid": str(row["bookid"]),
                "safe_text": row["safe_text"],
                "shadow_text": shadow_text,
                "source_text": row["source_text"],
                "strictplus_text": row["strictplus_text"],
                "macrocompressed_text": row["macrocompressed_text"],
                "safe_blocked_hit_count": int(row["blocked_hit_count"] or 0),
                "safe_caution_hit_count": int(row["caution_hit_count"] or 0),
                "safe_risk_score": int(row["risk_score"] or 0),
                "safe_hits": safe_json(row["hits_json"], []),
                "shadow_hits": hits,
            }
        )
    clean_books = sum(1 for item in items if not item["safe_blocked_hit_count"] and not item["shadow_hits"])
    shadow_clean_pct = round(100.0 * clean_books / totals["book_count"], 2) if totals["book_count"] else 0.0
    return {
        "summary": {
            "safe_book_run_id": safe_run_id,
            "book_count": totals["book_count"],
            "rule_count": len(rules),
            "books_with_shadow_hits": totals["books_with_shadow_hits"],
            "shadow_hit_count": totals["shadow_hit_count"],
            "shadow_clean_pct": shadow_clean_pct,
            "interpretation": "Shadow layer neutralizes suspect semantic retexts; it is an anti-overfit reading view, not a decode-core mutation.",
        },
        "items": items,
        "rules": rules,
    }


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS semantic_shadow_book_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            safe_book_run_id INTEGER NOT NULL,
            book_count INTEGER NOT NULL,
            rule_count INTEGER NOT NULL,
            books_with_shadow_hits INTEGER NOT NULL,
            shadow_hit_count INTEGER NOT NULL,
            shadow_clean_pct REAL NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS semantic_shadow_book_translations (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            safe_text TEXT,
            shadow_text TEXT,
            safe_blocked_hit_count INTEGER NOT NULL,
            safe_caution_hit_count INTEGER NOT NULL,
            safe_risk_score INTEGER NOT NULL,
            shadow_hits_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        );
        """
    )


def record(conn: sqlite3.Connection, payload: Dict[str, Any]) -> int:
    ensure_schema(conn)
    summary = payload["summary"]
    created_at = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    cur = conn.execute(
        """
        INSERT INTO semantic_shadow_book_runs (
            created_at, safe_book_run_id, book_count, rule_count, books_with_shadow_hits,
            shadow_hit_count, shadow_clean_pct, payload_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            created_at,
            summary["safe_book_run_id"],
            summary["book_count"],
            summary["rule_count"],
            summary["books_with_shadow_hits"],
            summary["shadow_hit_count"],
            summary["shadow_clean_pct"],
            json.dumps({**summary, "rules": payload["rules"]}, ensure_ascii=True, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)
    for item in payload["items"]:
        conn.execute(
            """
            INSERT INTO semantic_shadow_book_translations (
                run_id, bookid, safe_text, shadow_text, safe_blocked_hit_count,
                safe_caution_hit_count, safe_risk_score, shadow_hits_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                item["bookid"],
                item["safe_text"],
                item["shadow_text"],
                item["safe_blocked_hit_count"],
                item["safe_caution_hit_count"],
                item["safe_risk_score"],
                json.dumps(item["shadow_hits"], ensure_ascii=True, sort_keys=True),
            ),
        )
    conn.commit()
    return run_id


def main() -> int:
    args = parse_args()
    conn = connect(args.db)
    try:
        rules = build_rules(conn)
        payload = materialize(conn, rules)
        run_id = record(conn, payload) if args.record else None
    finally:
        conn.close()
    sample = sorted(
        payload["items"],
        key=lambda item: (-sum(hit["count"] for hit in item["shadow_hits"]), int(item["bookid"])),
    )[: args.max_output_books]
    print(
        json.dumps(
            {
                **payload["summary"],
                "recorded_run_id": run_id,
                "rules": payload["rules"],
                "sample_books": sample,
            },
            ensure_ascii=True,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
