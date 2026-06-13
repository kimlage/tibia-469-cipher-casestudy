#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

from sqlite_snapshot_ref import DEFAULT_SNAPSHOT_NAME, resolve_export_id


DEFAULT_DB = "./data/bonelord_operational.sqlite"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a SQL-native semantic contradiction report for a token family")
    parser.add_argument("--db", default=DEFAULT_DB, help="Operational SQLite DB")
    parser.add_argument("--export-id", type=int, default=None, help="Specific export_id")
    parser.add_argument("--snapshot-name", default=DEFAULT_SNAPSHOT_NAME, help="Named snapshot ref to use")
    parser.add_argument("--family", required=True, help="Human-readable family label")
    parser.add_argument("--search", action="append", required=True, help="Raw code token or substring to inspect")
    parser.add_argument("--limit", type=int, default=40, help="Max rows per section")
    parser.add_argument("--out", default=None, help="Optional JSON output path")
    return parser.parse_args()


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def row_dict(row: sqlite3.Row, fields: Sequence[str]) -> Dict[str, Any]:
    keys = set(row.keys())
    return {field: row[field] if field in keys else None for field in fields}


def like_any_clause(field: str, searches: Sequence[str]) -> tuple[str, List[str]]:
    clause = " OR ".join([f'upper(coalesce("{field}", "")) LIKE ?' for _ in searches])
    params = [f"%{search.upper()}%" for search in searches]
    return f"({clause})", params


def glossary_variants(conn: sqlite3.Connection, export_id: int, searches: Sequence[str], limit: int) -> List[Dict[str, Any]]:
    clause, params = like_any_clause("token", searches)
    rows = conn.execute(
        f"""
        SELECT
            token,
            translation,
            totalocc,
            bookcount,
            contigcount,
            evidenceclass_v127,
            evidencesources_v127,
            notes
        FROM sheet__glossary
        WHERE __export_id = ?
          AND {clause}
        ORDER BY
            CAST(coalesce(bookcount, 0) AS INTEGER) DESC,
            CAST(coalesce(totalocc, 0) AS INTEGER) DESC,
            length(coalesce(token, '')) ASC
        LIMIT ?
        """,
        (export_id, *params, limit),
    ).fetchall()
    return [
        row_dict(
            row,
            (
                "token",
                "translation",
                "totalocc",
                "bookcount",
                "contigcount",
                "evidenceclass_v127",
                "evidencesources_v127",
                "notes",
            ),
        )
        for row in rows
    ]


def book_contexts(conn: sqlite3.Connection, export_id: int, searches: Sequence[str], limit: int) -> List[Dict[str, Any]]:
    clause, params = like_any_clause("decodedbase", searches)
    rows = conn.execute(
        f"""
        SELECT
            bookid,
            decodedbase,
            translation_strictplus_v108,
            translation_semantic_auto,
            translation_english_auto,
            translation_contextenglish_auto
        FROM sheet__books
        WHERE __export_id = ?
          AND {clause}
        ORDER BY CAST(coalesce(bookid, 0) AS INTEGER)
        LIMIT ?
        """,
        (export_id, *params, limit),
    ).fetchall()
    return [
        row_dict(
            row,
            (
                "bookid",
                "decodedbase",
                "translation_strictplus_v108",
                "translation_semantic_auto",
                "translation_english_auto",
                "translation_contextenglish_auto",
            ),
        )
        for row in rows
    ]


def external_contexts(conn: sqlite3.Connection, export_id: int, searches: Sequence[str], limit: int) -> List[Dict[str, Any]]:
    clause, params = like_any_clause("decodedbase", searches)
    rows = conn.execute(
        f"""
        SELECT
            refname,
            type,
            source,
            decodedbase,
            dp_strictplus,
            codestreamdp_readable_v119,
            codestreamdp_lossless_v119
        FROM sheet__externalrefs_v115
        WHERE __export_id = ?
          AND {clause}
        ORDER BY __row_index
        LIMIT ?
        """,
        (export_id, *params, limit),
    ).fetchall()
    return [
        row_dict(
            row,
            (
                "refname",
                "type",
                "source",
                "decodedbase",
                "dp_strictplus",
                "codestreamdp_readable_v119",
                "codestreamdp_lossless_v119",
            ),
        )
        for row in rows
    ]


def words(text: object) -> List[str]:
    return re.findall(r"[a-z]+", str(text or "").lower())


def summarize_contradictions(variants: Sequence[Dict[str, Any]], books: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    translation_by_token = {
        str(item.get("token") or ""): str(item.get("translation") or "").strip()
        for item in variants
        if str(item.get("token") or "").strip()
    }
    translation_counts = Counter(value for value in translation_by_token.values() if value)
    word_counts = Counter()
    for value in translation_by_token.values():
        word_counts.update(words(value))

    repeated_book_words = Counter()
    for row in books:
        repeated_book_words.update(words(row.get("translation_contextenglish_auto")))

    prefix_groups: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    ordered_tokens = sorted(translation_by_token, key=len)
    for token in ordered_tokens:
        for base in ordered_tokens:
            if token == base:
                continue
            if len(base) < 4:
                continue
            if token.startswith(base):
                prefix_groups[base].append(
                    {
                        "token": token,
                        "translation": translation_by_token[token],
                        "suffix": token[len(base) :],
                    }
                )
                break

    suspicious = []
    for base, children in prefix_groups.items():
        base_translation = translation_by_token.get(base, "")
        child_translations = sorted({child["translation"] for child in children if child["translation"]})
        if base_translation and child_translations and any(base_translation not in child for child in child_translations):
            suspicious.append(
                {
                    "base_token": base,
                    "base_translation": base_translation,
                    "child_count": len(children),
                    "child_translations": child_translations[:12],
                    "reason": "prefix family has child translations that do not preserve the base meaning",
                }
            )

    return {
        "distinct_translation_count": len(translation_counts),
        "top_variant_translations": translation_counts.most_common(20),
        "top_variant_words": word_counts.most_common(30),
        "top_context_words": repeated_book_words.most_common(30),
        "prefix_contradictions": suspicious[:20],
    }


def build_report(conn: sqlite3.Connection, args: argparse.Namespace) -> Dict[str, Any]:
    export_id = resolve_export_id(conn, export_id=args.export_id, snapshot_name=args.snapshot_name)
    variants = glossary_variants(conn, export_id, args.search, args.limit)
    books = book_contexts(conn, export_id, args.search, args.limit)
    externals = external_contexts(conn, export_id, args.search, args.limit)
    return {
        "family": args.family,
        "searches": args.search,
        "export_id": export_id,
        "counts": {
            "glossary_variants": len(variants),
            "book_contexts": len(books),
            "external_contexts": len(externals),
        },
        "semantic_contradiction_summary": summarize_contradictions(variants, books),
        "glossary_variants": variants,
        "book_contexts": books,
        "external_contexts": externals,
    }


def main() -> int:
    args = parse_args()
    conn = connect(args.db)
    try:
        report = build_report(conn, args)
    finally:
        conn.close()

    text = json.dumps(report, ensure_ascii=True, indent=2)
    if args.out:
        out_path = Path(args.out).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
