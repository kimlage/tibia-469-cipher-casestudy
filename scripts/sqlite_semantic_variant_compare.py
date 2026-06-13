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
    parser = argparse.ArgumentParser(description="Compare current/neutral/mechanical variants for suspect semantic bases")
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


def safe_json(raw: object, default: Any) -> Any:
    if raw in (None, ""):
        return default
    try:
        return json.loads(str(raw))
    except json.JSONDecodeError:
        return default


def latest_suspect_constraints(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT token, decision, confidence, blocked_old_hint, reason, payload_json
        FROM semantic_constraint_registry
        WHERE constraint_id IN (
            SELECT max(constraint_id)
            FROM semantic_constraint_registry
            GROUP BY token
        )
          AND decision LIKE 'SUSPECT%'
        ORDER BY token
        """
    ).fetchall()
    return [dict(row) for row in rows]


def glossary(conn: sqlite3.Connection) -> Dict[str, sqlite3.Row]:
    rows = conn.execute(
        """
        SELECT token, translation, notes, totalocc, bookcount, evidenceclass_v127
        FROM sheet__glossary
        WHERE __export_id = 2
        """
    ).fetchall()
    return {str(row["token"]): row for row in rows if row["token"] is not None}


def mechanical_phrase(constraint: Dict[str, Any], notes: str) -> str | None:
    payload = safe_json(constraint.get("payload_json"), {})
    provenance = payload.get("mechanical_provenance")
    if provenance:
        return str(provenance).lower()
    lower = notes.lower()
    for pattern in (
        r"anagram(?:-variant)? of ([a-z]+)",
        r"unique anagram(?: \([^)]*\))? of ([a-z]+)",
        r"old ([a-z]+)",
    ):
        match = re.search(pattern, lower)
        if match:
            return match.group(1).lower()
    return None


def words(text: str) -> List[str]:
    return re.findall(r"[a-z]+|<suspect:[^>]+>|<unk:[^>]+>|<unk>", text.lower())


BAD_CONTEXT_BIGRAMS = {
    "a a",
    "a no",
    "no a",
    "we no",
    "you've i",
    "i a",
    "i i",
    "to a",
    "of of",
}


def phrase_score(text: str) -> int:
    tokens = words(text)
    if not tokens:
        return 0
    score = 0
    for idx, token in enumerate(tokens):
        if token.startswith("<suspect:") or token.startswith("<unk"):
            score -= 4
        if idx:
            bigram = f"{tokens[idx - 1]} {token}"
            if bigram in BAD_CONTEXT_BIGRAMS:
                score -= 1
            if tokens[idx - 1] == token and token not in {"no", "i", "a"}:
                score -= 1
    return score


def context_window(text: str, phrase: str, radius: int = 7) -> List[str]:
    tokens = text.split()
    contexts: List[str] = []
    phrase_lower = phrase.lower()
    for idx, token in enumerate(tokens):
        clean = re.sub(r"^[^A-Za-z<]+|[^A-Za-z>]+$", "", token).lower()
        if clean != phrase_lower:
            continue
        start = max(0, idx - radius)
        end = min(len(tokens), idx + radius + 1)
        contexts.append(" ".join(tokens[start:end]))
    return contexts


def replace_word(text: str, old: str, new: str) -> str:
    return re.sub(rf"(?<![A-Za-z]){re.escape(old)}(?![A-Za-z])", new, text, flags=re.IGNORECASE)


def compare(conn: sqlite3.Connection) -> Dict[str, Any]:
    safe_run_id = latest_run_id(conn, "safe_book_translation_runs")
    if safe_run_id is None:
        raise RuntimeError("safe_book_translation_runs has no rows")
    rows = conn.execute(
        """
        SELECT bookid, safe_text
        FROM safe_book_translations
        WHERE run_id = ?
        ORDER BY CAST(bookid AS INTEGER)
        """,
        (safe_run_id,),
    ).fetchall()
    books = [(str(row["bookid"]), str(row["safe_text"] or "")) for row in rows]
    g = glossary(conn)
    items: List[Dict[str, Any]] = []
    for constraint in latest_suspect_constraints(conn):
        token = str(constraint["token"])
        row = g.get(token)
        current = str(row["translation"] if row else constraint.get("blocked_old_hint") or "")
        if not current or current.startswith("<"):
            continue
        mechanical = mechanical_phrase(constraint, str(row["notes"] if row else ""))
        neutral = f"<SUSPECT:{token}>"
        current_contexts: List[Dict[str, Any]] = []
        counts = Counter()
        score_delta_mechanical = 0
        score_delta_neutral = 0
        for bookid, text in books:
            contexts = context_window(text, current)
            if not contexts:
                continue
            counts["book_count"] += 1
            counts["hit_count"] += len(contexts)
            for context in contexts[:5]:
                neutral_context = replace_word(context, current, neutral)
                mechanical_context = replace_word(context, current, mechanical) if mechanical else ""
                current_score = phrase_score(context)
                neutral_score = phrase_score(neutral_context)
                mechanical_score = phrase_score(mechanical_context) if mechanical else -999
                score_delta_neutral += neutral_score - current_score
                if mechanical:
                    score_delta_mechanical += mechanical_score - current_score
                current_contexts.append(
                    {
                        "bookid": bookid,
                        "current": context,
                        "neutral": neutral_context,
                        "mechanical": mechanical_context or None,
                        "scores": {
                            "current": current_score,
                            "neutral": neutral_score,
                            "mechanical": mechanical_score if mechanical else None,
                        },
                    }
                )
        if not counts["hit_count"]:
            continue
        if mechanical and score_delta_mechanical >= score_delta_neutral:
            recommended = "MECHANICAL_SHADOW_COMPARE"
        else:
            recommended = "NEUTRALIZE_IN_SAFE_READING"
        items.append(
            {
                "token": token,
                "current": current,
                "mechanical": mechanical,
                "neutral": neutral,
                "decision": constraint["decision"],
                "confidence": constraint["confidence"],
                "book_count": counts["book_count"],
                "hit_count": counts["hit_count"],
                "score_delta_neutral": score_delta_neutral,
                "score_delta_mechanical": score_delta_mechanical if mechanical else None,
                "recommended_action": recommended,
                "reason": constraint["reason"],
                "contexts": current_contexts[:12],
            }
        )
    items.sort(key=lambda item: (-item["hit_count"], -item["book_count"], item["token"]))
    return {
        "safe_book_run_id": safe_run_id,
        "item_count": len(items),
        "items": items,
        "interpretation": "Heuristic variant comparison only; candidates require human/agent semantic review before decode-core mutation.",
    }


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS semantic_variant_compare_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            safe_book_run_id INTEGER NOT NULL,
            item_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS semantic_variant_compare_items (
            run_id INTEGER NOT NULL,
            rank INTEGER NOT NULL,
            token TEXT NOT NULL,
            current TEXT NOT NULL,
            mechanical TEXT,
            neutral TEXT NOT NULL,
            book_count INTEGER NOT NULL,
            hit_count INTEGER NOT NULL,
            recommended_action TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, rank)
        );
        """
    )


def record(conn: sqlite3.Connection, payload: Dict[str, Any]) -> int:
    ensure_schema(conn)
    created_at = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    cur = conn.execute(
        """
        INSERT INTO semantic_variant_compare_runs (created_at, safe_book_run_id, item_count, payload_json)
        VALUES (?, ?, ?, ?)
        """,
        (
            created_at,
            payload["safe_book_run_id"],
            payload["item_count"],
            json.dumps({k: v for k, v in payload.items() if k != "items"}, ensure_ascii=True, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)
    for rank, item in enumerate(payload["items"], start=1):
        conn.execute(
            """
            INSERT INTO semantic_variant_compare_items (
                run_id, rank, token, current, mechanical, neutral,
                book_count, hit_count, recommended_action, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                rank,
                item["token"],
                item["current"],
                item["mechanical"],
                item["neutral"],
                item["book_count"],
                item["hit_count"],
                item["recommended_action"],
                json.dumps(item, ensure_ascii=True, sort_keys=True),
            ),
        )
    conn.commit()
    return run_id


def main() -> int:
    args = parse_args()
    conn = connect(args.db)
    try:
        payload = compare(conn)
        run_id = record(conn, payload) if args.record else None
    finally:
        conn.close()
    print(json.dumps({**payload, "recorded_run_id": run_id}, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
