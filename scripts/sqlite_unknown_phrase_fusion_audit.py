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
UNKNOWN_RE = re.compile(r"<UNK:([^>]+)>")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit unresolved unknowns as phrase/fusion/boundary problems")
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--record", action="store_true")
    parser.add_argument("--raw-context", type=int, default=18)
    parser.add_argument("--text-context", type=int, default=70)
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


def compact(text: object) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def latest_best_shadow_rows(conn: sqlite3.Connection) -> tuple[int | None, list[sqlite3.Row]]:
    run_id = latest_run_id(conn, "best_shadow_book_runs")
    if run_id is None:
        return None, []
    rows = conn.execute(
        """
        SELECT bookid, best_shadow_text
        FROM best_shadow_book_translations
        WHERE run_id = ?
        ORDER BY CAST(bookid AS INTEGER)
        """,
        (run_id,),
    ).fetchall()
    return run_id, rows


def latest_book_sources(conn: sqlite3.Connection) -> dict[str, sqlite3.Row]:
    if not table_exists(conn, "sheet__books"):
        return {}
    export_row = conn.execute("SELECT MAX(__export_id) AS export_id FROM sheet__books").fetchone()
    export_id = export_row["export_id"] if export_row else None
    rows = conn.execute(
        """
        SELECT bookid, decodedbase, translation_strictplus_v108, translation_contextenglish_auto
        FROM sheet__books
        WHERE __export_id = ?
        """,
        (export_id,),
    ).fetchall()
    return {str(row["bookid"]): row for row in rows}


def latest_macro_rows(conn: sqlite3.Connection) -> list[sqlite3.Row]:
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


def glossary_row(conn: sqlite3.Connection, token: str) -> dict[str, Any]:
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


def unknown_contexts(rows: list[sqlite3.Row], radius: int) -> dict[str, dict[str, Any]]:
    buckets: dict[str, dict[str, Any]] = {}
    for row in rows:
        bookid = str(row["bookid"])
        text = str(row["best_shadow_text"] or "")
        for match in UNKNOWN_RE.finditer(text):
            token = match.group(1)
            bucket = buckets.setdefault(token, {"hit_count": 0, "books": set(), "text_contexts": []})
            bucket["hit_count"] += 1
            bucket["books"].add(bookid)
            if len(bucket["text_contexts"]) < 16:
                bucket["text_contexts"].append(
                    {
                        "bookid": bookid,
                        "context": compact(text[max(0, match.start() - radius) : min(len(text), match.end() + radius)]),
                    }
                )
    for bucket in buckets.values():
        bucket["books"] = sorted(bucket["books"], key=lambda value: int(value) if value.isdigit() else value)
        bucket["book_count"] = len(bucket["books"])
    return buckets


def raw_windows_for_token(
    token: str,
    books: list[str],
    sources: dict[str, sqlite3.Row],
    radius: int,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    pattern = re.compile(re.escape(token))
    for bookid in books:
        row = sources.get(bookid)
        raw = str(row["decodedbase"] if row else "")
        for match in pattern.finditer(raw):
            out.append(
                {
                    "bookid": bookid,
                    "raw_window": raw[max(0, match.start() - radius) : min(len(raw), match.end() + radius)],
                    "left": raw[max(0, match.start() - radius) : match.start()],
                    "right": raw[match.end() : min(len(raw), match.end() + radius)],
                }
            )
    return out


def macro_owners(token: str, macro_rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    owners: list[dict[str, Any]] = []
    for row in macro_rows:
        components = [str(item) for item in safe_json(row["component_tokens_json"], [])]
        macro_token = str(row["token"])
        if token not in components and token not in macro_token:
            continue
        owners.append(
            {
                "token": macro_token,
                "contains_as_component": token in components,
                "contains_as_substring": token in macro_token,
                "components": components,
                "original_translation": compact(row["original_translation"]),
                "audited_recomposed_translation": compact(row["audited_recomposed_translation"]),
                "changed": int(row["changed"] or 0),
            }
        )
    owners.sort(
        key=lambda item: (
            not item["contains_as_component"],
            len(item["token"]),
            item["token"],
        )
    )
    return owners


def repeated_raw_prefixes(raw_windows: list[dict[str, Any]]) -> list[tuple[str, int]]:
    counts: Counter[str] = Counter()
    for item in raw_windows:
        window = str(item["raw_window"])
        counts[window[:32]] += 1
    return counts.most_common(10)


def classify(token: str, item: dict[str, Any]) -> str:
    owners = item["macro_owners"]
    exact_component = [owner for owner in owners if owner["contains_as_component"]]
    raw_prefixes = dict(item["repeated_raw_prefixes"])

    if token == "TII":
        if any(owner["token"] == "EBTII" for owner in exact_component):
            return "FREEZE_BASE_AND_AUDIT_EBTII_PHRASE_FAMILY"
        return "FREEZE_BASE_AND_AUDIT_TII_BOUNDARIES"
    if token == "TTNVVN":
        if any("LTAS" in key or "NFIE" in key for key in raw_prefixes):
            return "KEEP_FORMULA_SLOT_WITH_MECHANICAL_HINT_ONLY"
        return "KEEP_UNKNOWN_WITH_FORMULA_CONTEXT"
    if exact_component:
        return "AUDIT_MACRO_OWNER_BEFORE_BASE_TRANSLATION"
    return "KEEP_UNKNOWN_AND_SEARCH_RAW_FORMULA"


def build_payload(conn: sqlite3.Connection, raw_radius: int, text_radius: int) -> dict[str, Any]:
    best_run_id, best_rows = latest_best_shadow_rows(conn)
    sources = latest_book_sources(conn)
    macros = latest_macro_rows(conn)
    unknowns = unknown_contexts(best_rows, text_radius)

    items: list[dict[str, Any]] = []
    for token, context in unknowns.items():
        raw_windows = raw_windows_for_token(token, context["books"], sources, raw_radius)
        owners = macro_owners(token, macros)
        item = {
            "token": token,
            "hit_count": context["hit_count"],
            "book_count": context["book_count"],
            "books": context["books"],
            "text_contexts": context["text_contexts"],
            "raw_windows": raw_windows[:20],
            "repeated_raw_prefixes": repeated_raw_prefixes(raw_windows),
            "macro_owners": owners[:40],
            "glossary": glossary_row(conn, token),
        }
        item["recommendation"] = classify(token, item)
        item["priority_score"] = item["hit_count"] * 10 + item["book_count"] * 7 + len(owners)
        items.append(item)

    items.sort(key=lambda item: (-int(item["priority_score"]), str(item["token"])))
    return {
        "best_shadow_run_id": best_run_id,
        "token_count": len(items),
        "items": items,
        "interpretation": (
            "If an unknown is repeatedly embedded in a stable macro or formula, audit the macro/family before "
            "choosing an isolated lexical value."
        ),
    }


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS unknown_phrase_fusion_audit_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            best_shadow_run_id INTEGER,
            token_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS unknown_phrase_fusion_audit_items (
            run_id INTEGER NOT NULL,
            rank INTEGER NOT NULL,
            token TEXT NOT NULL,
            hit_count INTEGER NOT NULL,
            book_count INTEGER NOT NULL,
            macro_owner_count INTEGER NOT NULL,
            recommendation TEXT NOT NULL,
            repeated_raw_prefixes_json TEXT NOT NULL,
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
        INSERT INTO unknown_phrase_fusion_audit_runs (
            created_at, best_shadow_run_id, token_count, payload_json
        ) VALUES (?, ?, ?, ?)
        """,
        (
            created_at,
            payload["best_shadow_run_id"],
            payload["token_count"],
            json.dumps({k: v for k, v in payload.items() if k != "items"}, ensure_ascii=True, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)
    for rank, item in enumerate(payload["items"], start=1):
        conn.execute(
            """
            INSERT INTO unknown_phrase_fusion_audit_items (
                run_id, rank, token, hit_count, book_count, macro_owner_count,
                recommendation, repeated_raw_prefixes_json, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                rank,
                item["token"],
                item["hit_count"],
                item["book_count"],
                len(item["macro_owners"]),
                item["recommendation"],
                json.dumps(item["repeated_raw_prefixes"], ensure_ascii=True, sort_keys=True),
                json.dumps(item, ensure_ascii=True, sort_keys=True),
            ),
        )
    conn.commit()
    return run_id


def main() -> int:
    args = parse_args()
    conn = connect(args.db)
    try:
        payload = build_payload(conn, args.raw_context, args.text_context)
        run_id = record(conn, payload) if args.record else None
    finally:
        conn.close()

    print(
        json.dumps(
            {
                "recorded_run_id": run_id,
                "best_shadow_run_id": payload["best_shadow_run_id"],
                "token_count": payload["token_count"],
                "items": [
                    {
                        "token": item["token"],
                        "hits": item["hit_count"],
                        "books": item["book_count"],
                        "macro_owner_count": len(item["macro_owners"]),
                        "top_raw_prefixes": item["repeated_raw_prefixes"][:3],
                        "recommendation": item["recommendation"],
                    }
                    for item in payload["items"]
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
