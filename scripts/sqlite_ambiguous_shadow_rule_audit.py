#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sqlite3
from collections import Counter, defaultdict
from datetime import UTC, datetime
from typing import Any, Dict, List


DEFAULT_DB = "./data/bonelord_operational.sqlite"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Find token-specific safe shadow rules for ambiguous display words")
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--record", action="store_true")
    parser.add_argument("--max-rules-per-token", type=int, default=25)
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


def normalize_phrase(text: object) -> str:
    text = re.sub(r"\s+", " ", str(text or "").strip())
    return text


def phrase_key(text: object) -> str:
    text = normalize_phrase(text).lower()
    text = re.sub(r"[^a-z0-9<>*']+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def useful_phrase(text: str) -> bool:
    if not text:
        return False
    words = re.findall(r"[A-Za-z<>*']+", text)
    if len(words) < 2:
        return False
    if len(words) > 10:
        return False
    if text.startswith("<MISSING:"):
        return False
    return True


def latest_decisions(conn: sqlite3.Connection) -> Dict[str, Dict[str, Any]]:
    if not table_exists(conn, "semantic_variant_decisions"):
        return {}
    rows = conn.execute(
        """
        SELECT d.*, g.translation AS current_translation
        FROM semantic_variant_decisions d
        JOIN (
            SELECT token, max(decision_id) AS decision_id
            FROM semantic_variant_decisions
            GROUP BY token
        ) latest
          ON latest.decision_id = d.decision_id
        LEFT JOIN sheet__glossary g
          ON g.__export_id = 2
         AND g.token = d.token
        """
    ).fetchall()
    return {str(row["token"]): dict(row) for row in rows}


def translation_siblings(conn: sqlite3.Connection) -> Dict[str, List[str]]:
    rows = conn.execute(
        """
        SELECT token, translation
        FROM sheet__glossary
        WHERE __export_id = 2
          AND translation IS NOT NULL
          AND translation != ''
        """
    ).fetchall()
    siblings: Dict[str, List[str]] = defaultdict(list)
    for row in rows:
        siblings[str(row["translation"]).lower()].append(str(row["token"]))
    return siblings


def recomposition_rows(conn: sqlite3.Connection) -> List[sqlite3.Row]:
    run_id = latest_run_id(conn, "macro_recomposition_audit_runs")
    if run_id is None:
        return []
    return conn.execute(
        """
        SELECT token, original_translation, audited_recomposed_translation, component_tokens_json, changed
        FROM macro_recomposition_audit
        WHERE run_id = ?
        """,
        (run_id,),
    ).fetchall()


def latest_safe_books(conn: sqlite3.Connection) -> List[sqlite3.Row]:
    run_id = latest_run_id(conn, "safe_book_translation_runs")
    if run_id is None:
        return []
    return conn.execute(
        """
        SELECT bookid, safe_text
        FROM safe_book_translations
        WHERE run_id = ?
        """,
        (run_id,),
    ).fetchall()


def phrase_occurrences(books: List[sqlite3.Row], phrase: str) -> tuple[int, int]:
    pattern = re.compile(rf"(?<![A-Za-z]){re.escape(phrase)}(?![A-Za-z])", re.IGNORECASE)
    hit_count = 0
    book_count = 0
    for row in books:
        count = len(pattern.findall(str(row["safe_text"] or "")))
        if count:
            book_count += 1
            hit_count += count
    return book_count, hit_count


def build_rules(conn: sqlite3.Connection, max_rules_per_token: int) -> Dict[str, Any]:
    decisions = latest_decisions(conn)
    siblings_by_translation = translation_siblings(conn)
    rows = recomposition_rows(conn)
    books = latest_safe_books(conn)
    component_phrase_owners: Dict[str, set[str]] = defaultdict(set)
    row_items: List[Dict[str, Any]] = []
    for row in rows:
        components = [str(item) for item in safe_json(row["component_tokens_json"], [])]
        phrase = normalize_phrase(row["audited_recomposed_translation"])
        if not useful_phrase(phrase):
            continue
        for component in set(components):
            component_phrase_owners[phrase_key(phrase)].add(component)
        row_items.append(
            {
                "token": str(row["token"]),
                "phrase": phrase,
                "original": normalize_phrase(row["original_translation"]),
                "components": components,
                "changed": int(row["changed"] or 0),
            }
        )

    output_items: List[Dict[str, Any]] = []
    for token, decision in decisions.items():
        current = str(decision.get("current_translation") or "")
        chosen = str(decision.get("chosen_variant") or "")
        if not current or not chosen or current == chosen:
            continue
        siblings = siblings_by_translation.get(current.lower(), [])
        if len(siblings) <= 1:
            continue
        candidate_rules: List[Dict[str, Any]] = []
        for item in row_items:
            if token not in item["components"]:
                continue
            phrase = item["phrase"]
            if current.lower() not in phrase.lower():
                continue
            phrase_owners = component_phrase_owners.get(phrase_key(phrase), set())
            sibling_owners = sorted(owner for owner in phrase_owners if owner in siblings and owner != token)
            if sibling_owners:
                safety = "COLLIDES_WITH_SIBLING_COMPONENT"
            else:
                safety = "TOKEN_SPECIFIC_CANDIDATE"
            book_count, hit_count = phrase_occurrences(books, phrase)
            if hit_count == 0:
                continue
            replacement = re.sub(rf"(?<![A-Za-z]){re.escape(current)}(?![A-Za-z])", chosen, phrase, flags=re.IGNORECASE)
            candidate_rules.append(
                {
                    "token": token,
                    "current": current,
                    "chosen": chosen,
                    "phrase": phrase,
                    "replacement": replacement,
                    "book_count": book_count,
                    "hit_count": hit_count,
                    "safety": safety,
                    "sibling_owners": sibling_owners,
                    "components": item["components"],
                    "source_macro": item["token"],
                    "original": item["original"],
                }
            )
        candidate_rules.sort(
            key=lambda rule: (
                rule["safety"] != "TOKEN_SPECIFIC_CANDIDATE",
                -rule["hit_count"],
                -len(rule["phrase"]),
                rule["phrase"],
            )
        )
        output_items.append(
            {
                "token": token,
                "current": current,
                "chosen": chosen,
                "sibling_tokens": sorted(siblings),
                "candidate_count": len(candidate_rules),
                "accepted_count": sum(1 for rule in candidate_rules if rule["safety"] == "TOKEN_SPECIFIC_CANDIDATE"),
                "rules": candidate_rules[:max_rules_per_token],
            }
        )
    return {
        "item_count": len(output_items),
        "items": output_items,
        "interpretation": "Rules marked TOKEN_SPECIFIC_CANDIDATE can be applied to ambiguous words without replacing sibling-token readings globally.",
    }


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS ambiguous_shadow_rule_audit_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            item_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS ambiguous_shadow_rule_audit_items (
            run_id INTEGER NOT NULL,
            rank INTEGER NOT NULL,
            token TEXT NOT NULL,
            current TEXT NOT NULL,
            chosen TEXT NOT NULL,
            candidate_count INTEGER NOT NULL,
            accepted_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, rank)
        );
        """
    )


def record(conn: sqlite3.Connection, payload: Dict[str, Any]) -> int:
    ensure_schema(conn)
    created_at = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    cur = conn.execute(
        "INSERT INTO ambiguous_shadow_rule_audit_runs (created_at, item_count, payload_json) VALUES (?, ?, ?)",
        (created_at, payload["item_count"], json.dumps({"interpretation": payload["interpretation"]}, ensure_ascii=True)),
    )
    run_id = int(cur.lastrowid)
    for rank, item in enumerate(payload["items"], start=1):
        conn.execute(
            """
            INSERT INTO ambiguous_shadow_rule_audit_items (
                run_id, rank, token, current, chosen, candidate_count, accepted_count, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                rank,
                item["token"],
                item["current"],
                item["chosen"],
                item["candidate_count"],
                item["accepted_count"],
                json.dumps(item, ensure_ascii=True, sort_keys=True),
            ),
        )
    conn.commit()
    return run_id


def main() -> int:
    args = parse_args()
    conn = connect(args.db)
    try:
        payload = build_rules(conn, args.max_rules_per_token)
        run_id = record(conn, payload) if args.record else None
    finally:
        conn.close()
    print(json.dumps({**payload, "recorded_run_id": run_id}, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
