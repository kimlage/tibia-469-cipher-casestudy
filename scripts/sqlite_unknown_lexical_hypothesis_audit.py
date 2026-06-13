#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sqlite3
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


DEFAULT_DB = "./data/bonelord_operational.sqlite"
DEFAULT_WORDLIST = "/usr/share/dict/words"

UNKNOWN_RE = re.compile(r"<UNK:([^>]+)>")
WORD_RE = re.compile(r"[A-Za-z<>:]+")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit unresolved named unknowns against conservative lexical/mechanical hypotheses"
    )
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--wordlist", default=DEFAULT_WORDLIST)
    parser.add_argument("--record", action="store_true")
    parser.add_argument("--context", type=int, default=56)
    parser.add_argument("--limit", type=int, default=50)
    return parser.parse_args()


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone() is not None


def table_columns(conn: sqlite3.Connection, table: str) -> list[str]:
    if not table_exists(conn, table):
        return []
    return [str(row["name"]) for row in conn.execute(f"PRAGMA table_info({table})").fetchall()]


def latest_run_id(conn: sqlite3.Connection, table: str) -> int | None:
    if not table_exists(conn, table):
        return None
    row = conn.execute(f"SELECT run_id FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    return int(row["run_id"]) if row else None


def load_words(path: str) -> list[str]:
    word_path = Path(path)
    if not word_path.exists():
        return []
    words: set[str] = set()
    for raw in word_path.read_text(errors="ignore").splitlines():
        word = re.sub(r"[^a-z]", "", raw.lower())
        if 2 <= len(word) <= 14:
            words.add(word)
    return sorted(words)


def alpha(text: object) -> str:
    return re.sub(r"[^a-z]", "", str(text or "").lower())


def norm_uvm(text: str) -> str:
    value = alpha(text)
    return value.translate(str.maketrans({"u": "v", "w": "v", "m": "n"}))


def norm_tii_rough(text: str) -> str:
    value = alpha(text)
    value = value.replace("h", "")
    return value.translate(str.maketrans({"d": "t", "e": "i", "y": "i"}))


def sig(text: str) -> str:
    return "".join(sorted(text))


def context_slice(text: str, start: int, end: int, radius: int) -> str:
    lo = max(0, start - radius)
    hi = min(len(text), end + radius)
    return re.sub(r"\s+", " ", text[lo:hi]).strip()


def source_translations(conn: sqlite3.Connection) -> tuple[str, int | None, list[sqlite3.Row]]:
    best_run = latest_run_id(conn, "best_shadow_book_runs")
    if best_run is not None and table_exists(conn, "best_shadow_book_translations"):
        rows = conn.execute(
            """
            SELECT bookid, best_shadow_text AS text
            FROM best_shadow_book_translations
            WHERE run_id = ?
            ORDER BY CAST(bookid AS INTEGER)
            """,
            (best_run,),
        ).fetchall()
        return "best_shadow_book_translations", best_run, rows

    safe_run = latest_run_id(conn, "safe_book_translation_runs")
    if safe_run is not None and table_exists(conn, "safe_book_translations"):
        rows = conn.execute(
            """
            SELECT bookid, safe_text AS text
            FROM safe_book_translations
            WHERE run_id = ?
            ORDER BY CAST(bookid AS INTEGER)
            """,
            (safe_run,),
        ).fetchall()
        return "safe_book_translations", safe_run, rows

    return "none", None, []


def collect_unknowns(rows: list[sqlite3.Row], radius: int) -> dict[str, dict[str, Any]]:
    buckets: dict[str, dict[str, Any]] = {}
    for row in rows:
        bookid = str(row["bookid"])
        text = str(row["text"] or "")
        for match in UNKNOWN_RE.finditer(text):
            token = match.group(1)
            bucket = buckets.setdefault(
                token,
                {
                    "token": token,
                    "hit_count": 0,
                    "books": set(),
                    "contexts": [],
                    "left_words": Counter(),
                    "right_words": Counter(),
                },
            )
            bucket["hit_count"] += 1
            bucket["books"].add(bookid)
            if len(bucket["contexts"]) < 16:
                bucket["contexts"].append(
                    {
                        "bookid": bookid,
                        "context": context_slice(text, match.start(), match.end(), radius),
                    }
                )
            left = text[max(0, match.start() - 80) : match.start()]
            right = text[match.end() : min(len(text), match.end() + 80)]
            left_tokens = [item.lower() for item in WORD_RE.findall(left)]
            right_tokens = [item.lower() for item in WORD_RE.findall(right)]
            if left_tokens:
                bucket["left_words"][left_tokens[-1]] += 1
            if right_tokens:
                bucket["right_words"][right_tokens[0]] += 1

    for bucket in buckets.values():
        bucket["books"] = sorted(bucket["books"], key=lambda value: int(value) if value.isdigit() else value)
        bucket["book_count"] = len(bucket["books"])
        bucket["left_words"] = bucket["left_words"].most_common(8)
        bucket["right_words"] = bucket["right_words"].most_common(8)
    return buckets


def latest_glossary_payload(conn: sqlite3.Connection, token: str) -> dict[str, Any]:
    if not table_exists(conn, "sheet__glossary"):
        return {}
    row = conn.execute(
        """
        SELECT token, translation, tokentype, confidence, evidenceclass_v127,
               evidencescore_v127, totalocc, bookcount, notes
        FROM sheet__glossary
        WHERE token = ?
        ORDER BY __export_id DESC
        LIMIT 1
        """,
        (token,),
    ).fetchone()
    return dict(row) if row else {}


def constraint_payload(conn: sqlite3.Connection, token: str) -> dict[str, Any]:
    if not table_exists(conn, "semantic_constraint_registry"):
        return {}
    cols = table_columns(conn, "semantic_constraint_registry")
    if "token" not in cols:
        return {}
    row = conn.execute("SELECT * FROM semantic_constraint_registry WHERE token = ? ORDER BY rowid DESC LIMIT 1", (token,)).fetchone()
    return dict(row) if row else {}


def old_hint(payloads: list[dict[str, Any]]) -> str:
    candidate_fields = (
        "old_word_hint",
        "blocked_old_hint",
        "blocked_word",
        "blocked_translation",
        "rejected_translation",
        "translation",
        "chosen_variant",
    )
    for payload in payloads:
        for field in candidate_fields:
            value = str(payload.get(field) or "").strip()
            if value and not value.startswith("<"):
                return value
    for payload in payloads:
        notes = str(payload.get("notes") or "")
        match = re.search(r"\b(tumtum|hidy|fervently|played|daniel|divine)\b", notes, flags=re.IGNORECASE)
        if match:
            return match.group(1).lower()
    return ""


def candidates_for_token(token: str, words: list[str]) -> dict[str, Any]:
    token_norm = alpha(token)
    exact_uvm: list[str] = []
    rough: dict[str, list[str]] = defaultdict(list)

    target_uvm = sig(norm_uvm(token_norm))
    target_exact_len = len(norm_uvm(token_norm))
    for word in words:
        word_uvm = norm_uvm(word)
        if len(word_uvm) == target_exact_len and sig(word_uvm) == target_uvm:
            exact_uvm.append(word)

    rough_targets: dict[str, str] = {
        f"{token_norm}": sig(token_norm),
        f"i+{token_norm}": sig("i" + token_norm),
        f"{token_norm}+i": sig(token_norm + "i"),
    }
    for word in words:
        word_rough = norm_tii_rough(word)
        if not (2 <= len(word_rough) <= len(token_norm) + 1):
            continue
        word_sig = sig(word_rough)
        for target_name, target_sig in rough_targets.items():
            if word_sig == target_sig:
                rough[target_name].append(word)

    return {
        "exact_uvm_anagram": sorted(exact_uvm),
        "rough_tii_family": {key: sorted(value) for key, value in sorted(rough.items())},
    }


def recommendation(token: str, hint: str, in_wordlist: bool, candidates: dict[str, Any], context: dict[str, Any]) -> str:
    exact = candidates["exact_uvm_anagram"]
    rough = [word for values in candidates["rough_tii_family"].values() for word in values]
    right_words = dict(context.get("right_words") or [])
    left_words = dict(context.get("left_words") or [])

    if token == "TTNVVN" and len(exact) == 1:
        return "KEEP_UNKNOWN_WITH_MECHANICAL_HINT_ONLY"
    if token == "TII":
        return "RUN_PHRASE_OR_FUSION_AUDIT_FOR_EBTII"
    if hint and not in_wordlist and (rough or exact):
        return "REJECT_OLD_HINT_AND_AUDIT_ALTERNATES"
    if exact and len(exact) <= 3:
        return "MANUAL_CONTEXT_DISAMBIGUATION_REQUIRED"
    if left_words or right_words:
        return "KEEP_UNKNOWN_AND_AUDIT_CONTEXT_PATTERN"
    return "KEEP_UNKNOWN"


def build_payload(conn: sqlite3.Connection, words: list[str], radius: int, limit: int) -> dict[str, Any]:
    source_table, source_run_id, rows = source_translations(conn)
    unknowns = collect_unknowns(rows, radius)
    items: list[dict[str, Any]] = []
    wordset = set(words)

    for token, context in unknowns.items():
        glossary = latest_glossary_payload(conn, token)
        constraint = constraint_payload(conn, token)
        hint = old_hint([constraint, glossary])
        candidates = candidates_for_token(token, words)
        rough_candidates = sorted({word for values in candidates["rough_tii_family"].values() for word in values})
        item = {
            "token": token,
            "hit_count": int(context["hit_count"]),
            "book_count": int(context["book_count"]),
            "books": context["books"],
            "old_hint": hint,
            "old_hint_in_wordlist": bool(hint and alpha(hint) in wordset),
            "exact_mech_candidate_count": len(candidates["exact_uvm_anagram"]),
            "rough_candidate_count": len(rough_candidates),
            "top_candidates": {
                "exact_uvm_anagram": candidates["exact_uvm_anagram"][:20],
                "rough_tii_family": {key: value[:20] for key, value in candidates["rough_tii_family"].items()},
            },
            "context_summary": {
                "left_words": context["left_words"],
                "right_words": context["right_words"],
                "sample_contexts": context["contexts"][:8],
            },
            "glossary": glossary,
            "constraint": constraint,
        }
        item["recommendation"] = recommendation(token, hint, item["old_hint_in_wordlist"], candidates, item["context_summary"])
        item["priority_score"] = item["hit_count"] * 10 + item["book_count"] * 7
        items.append(item)

    items.sort(key=lambda item: (-int(item["priority_score"]), str(item["token"])))
    return {
        "source_table": source_table,
        "source_run_id": source_run_id,
        "token_count": len(items),
        "wordlist": str(DEFAULT_WORDLIST),
        "items": items[:limit],
        "interpretation": (
            "Lexical candidates are hypothesis evidence only. They are not promoted unless they survive "
            "context, boundary, and contradiction checks."
        ),
    }


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS unknown_lexical_hypothesis_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_table TEXT NOT NULL,
            source_run_id INTEGER,
            token_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS unknown_lexical_hypothesis_items (
            run_id INTEGER NOT NULL,
            rank INTEGER NOT NULL,
            token TEXT NOT NULL,
            hit_count INTEGER NOT NULL,
            book_count INTEGER NOT NULL,
            old_hint TEXT,
            old_hint_in_wordlist INTEGER NOT NULL,
            exact_mech_candidate_count INTEGER NOT NULL,
            rough_candidate_count INTEGER NOT NULL,
            top_candidates_json TEXT NOT NULL,
            context_summary_json TEXT NOT NULL,
            recommendation TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, rank)
        );
        """
    )


def record(conn: sqlite3.Connection, payload: dict[str, Any]) -> int:
    ensure_schema(conn)
    created_at = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    cur = conn.execute(
        """
        INSERT INTO unknown_lexical_hypothesis_runs (
            created_at, source_table, source_run_id, token_count, payload_json
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (
            created_at,
            payload["source_table"],
            payload["source_run_id"],
            payload["token_count"],
            json.dumps({k: v for k, v in payload.items() if k != "items"}, ensure_ascii=True, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)
    for rank, item in enumerate(payload["items"], start=1):
        conn.execute(
            """
            INSERT INTO unknown_lexical_hypothesis_items (
                run_id, rank, token, hit_count, book_count, old_hint,
                old_hint_in_wordlist, exact_mech_candidate_count,
                rough_candidate_count, top_candidates_json, context_summary_json,
                recommendation, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                rank,
                item["token"],
                item["hit_count"],
                item["book_count"],
                item["old_hint"],
                1 if item["old_hint_in_wordlist"] else 0,
                item["exact_mech_candidate_count"],
                item["rough_candidate_count"],
                json.dumps(item["top_candidates"], ensure_ascii=True, sort_keys=True),
                json.dumps(item["context_summary"], ensure_ascii=True, sort_keys=True),
                item["recommendation"],
                json.dumps(item, ensure_ascii=True, sort_keys=True),
            ),
        )
    conn.commit()
    return run_id


def main() -> int:
    args = parse_args()
    words = load_words(args.wordlist)
    conn = connect(args.db)
    try:
        payload = build_payload(conn, words, args.context, args.limit)
        run_id = record(conn, payload) if args.record else None
    finally:
        conn.close()

    summary = {
        "recorded_run_id": run_id,
        "source_table": payload["source_table"],
        "source_run_id": payload["source_run_id"],
        "token_count": payload["token_count"],
        "items": [
            {
                "token": item["token"],
                "hits": item["hit_count"],
                "books": item["book_count"],
                "old_hint": item["old_hint"],
                "old_hint_in_wordlist": item["old_hint_in_wordlist"],
                "exact_mech": item["top_candidates"]["exact_uvm_anagram"],
                "rough_candidate_count": item["rough_candidate_count"],
                "recommendation": item["recommendation"],
            }
            for item in payload["items"]
        ],
    }
    print(json.dumps(summary, ensure_ascii=True, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
