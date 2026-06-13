#!/usr/bin/env python3
"""Test the Book30-family human shadow claim against row0 components.

The seeded shadow readings describe Books 12/21/26/30 as a shared Book30-family
core with different prefix/tail behavior. This probe checks that claim directly:
which components are actually shared, where the shared spine appears, and which
parts require rephrasing before any human interpretation gets stronger.
"""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

TARGET_BOOKS = ["12", "21", "26", "30"]
COMPONENTS = [
    "TAESESTIEN",
    "VNSBLFSINNAI",
    "FALVNALVEEIIV",
    "VIEITAIFASIATFTEIEFIINI",
    "VNAIFEEIIET",
    "NSETIEFIEIEFIIN",
    "TIVNSENI",
    "LAELBEV",
    "FLEEIIFTEI",
    "NBLIBEIEFSEENEIEN",
]
SPINE = "VNSBLFSINNAI"


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_book30_family_shadow_probe_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            target_count INTEGER NOT NULL,
            shared_all_component_count INTEGER NOT NULL,
            partial_component_count INTEGER NOT NULL,
            accepted_human_gloss_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_book30_family_shadow_probe_v1_items (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            symbol_text TEXT NOT NULL,
            component_hits_json TEXT NOT NULL,
            spine_pos INTEGER,
            prefix_before_spine TEXT NOT NULL,
            suffix_after_spine TEXT NOT NULL,
            classification TEXT NOT NULL,
            shadow_implication TEXT NOT NULL,
            next_action TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        );

        CREATE TABLE IF NOT EXISTS human_book30_family_shadow_probe_v1_components (
            run_id INTEGER NOT NULL,
            component TEXT NOT NULL,
            hit_count INTEGER NOT NULL,
            books_json TEXT NOT NULL,
            component_status TEXT NOT NULL,
            implication TEXT NOT NULL,
            PRIMARY KEY (run_id, component)
        );
        """
    )


def classify_book(bookid: str, hits: dict[str, int], prefix: str, suffix: str) -> tuple[str, str, str]:
    has_taese = hits.get("TAESESTIEN", -1) >= 0
    has_tail = hits.get("VNAIFEEIIET", -1) >= 0
    has_long_tail = hits.get("VIEITAIFASIATFTEIEFIINI", -1) >= 0
    if bookid == "30":
        return (
            "SPINE_PLUS_TAESESTIEN_ALT_TAIL",
            "Book 30 is not the full long-tail centroid; it is a spine+TAESESTIEN alternate-tail witness.",
            "Revise prose from 'central full formula' to 'alternate Book30-family spine witness'.",
        )
    if has_taese and has_tail and has_long_tail:
        return (
            "LONG_TAIL_SPINE_WITH_TAESESTIEN",
            "Supports a compact/extended long-tail reading inside the family.",
            "Use as positive control for long-tail spine behavior.",
        )
    if has_tail and has_long_tail:
        return (
            "LONG_TAIL_SPINE_WITH_BRANCH_PREFIX",
            "Supports branch-prefix transition into the shared spine/tail, but not the TAESESTIEN subcomponent.",
            "Keep branch/prefix language; do not call TAESESTIEN universal.",
        )
    return (
        "SPINE_ONLY_OR_UNEXPECTED",
        "Only the shared spine is clear; stronger family prose is not supported.",
        "Demote or inspect manually before using in human paraphrase.",
    )


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    placeholders = ",".join("?" for _ in TARGET_BOOKS)
    rows = conn.execute(
        f"""
        SELECT bookid, symbol_text
        FROM row0_variant_book_tokens
        WHERE run_id=(SELECT max(run_id) FROM row0_variant_book_tokens)
          AND bookid IN ({placeholders})
        ORDER BY CAST(bookid AS INTEGER)
        """,
        tuple(TARGET_BOOKS),
    ).fetchall()
    by_book = {str(row["bookid"]): str(row["symbol_text"]) for row in rows}
    missing_books = [bookid for bookid in TARGET_BOOKS if bookid not in by_book]
    if missing_books:
        raise RuntimeError(f"missing target books in row0 layer: {missing_books}")

    component_books: dict[str, list[str]] = {component: [] for component in COMPONENTS}
    book_records = []
    for bookid in TARGET_BOOKS:
        text = by_book[bookid]
        hits = {component: text.find(component) for component in COMPONENTS}
        for component, pos in hits.items():
            if pos >= 0:
                component_books[component].append(bookid)
        spine_pos = text.find(SPINE)
        prefix = text[:spine_pos] if spine_pos >= 0 else text
        suffix = text[spine_pos + len(SPINE) :] if spine_pos >= 0 else ""
        classification, implication, next_action = classify_book(bookid, hits, prefix, suffix)
        book_records.append(
            {
                "bookid": bookid,
                "symbol_text": text,
                "hits": hits,
                "spine_pos": spine_pos,
                "prefix": prefix,
                "suffix": suffix,
                "classification": classification,
                "implication": implication,
                "next_action": next_action,
            }
        )

    shared_all = [component for component, books in component_books.items() if len(books) == len(TARGET_BOOKS)]
    partial = [component for component, books in component_books.items() if 0 < len(books) < len(TARGET_BOOKS)]
    if shared_all == [SPINE]:
        decision = "BOOK30_SHADOW_SPINE_CONFIRMED_CORE_LANGUAGE_NEEDS_TIGHTENING"
    elif SPINE in shared_all:
        decision = "BOOK30_SHADOW_MULTI_COMPONENT_CORE_CONFIRMED"
    else:
        decision = "BOOK30_SHADOW_CORE_CLAIM_WEAK_OR_CONTRADICTED"
    payload = {
        "target_books": TARGET_BOOKS,
        "components": COMPONENTS,
        "shared_all": shared_all,
        "partial_components": partial,
        "principle": "support family/spine claims, not human plaintext",
    }
    cur = conn.execute(
        """
        INSERT INTO human_book30_family_shadow_probe_v1_runs
        (created_at, decision, target_count, shared_all_component_count,
         partial_component_count, accepted_human_gloss_count, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            now(),
            decision,
            len(TARGET_BOOKS),
            len(shared_all),
            len(partial),
            0,
            json.dumps(payload, ensure_ascii=False, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)

    for component in COMPONENTS:
        books = component_books[component]
        if len(books) == len(TARGET_BOOKS):
            status = "SHARED_BY_ALL_TARGET_BOOKS"
            implication = "safe to describe as family spine/component, not as plaintext"
        elif books:
            status = "PARTIAL_COMPONENT"
            implication = "use to distinguish subfamilies, prefixes, and tails"
        else:
            status = "ABSENT_FROM_TARGETS"
            implication = "not part of this Book30-family shadow probe"
        conn.execute(
            """
            INSERT INTO human_book30_family_shadow_probe_v1_components
            (run_id, component, hit_count, books_json, component_status, implication)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                component,
                len(books),
                json.dumps(books, ensure_ascii=False, sort_keys=True),
                status,
                implication,
            ),
        )

    for rec in book_records:
        conn.execute(
            """
            INSERT INTO human_book30_family_shadow_probe_v1_items
            (run_id, bookid, symbol_text, component_hits_json, spine_pos,
             prefix_before_spine, suffix_after_spine, classification,
             shadow_implication, next_action, evidence_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                rec["bookid"],
                rec["symbol_text"],
                json.dumps(rec["hits"], ensure_ascii=False, sort_keys=True),
                rec["spine_pos"],
                rec["prefix"],
                rec["suffix"],
                rec["classification"],
                rec["implication"],
                rec["next_action"],
                json.dumps({"shared_all": shared_all, "partial_components": partial}, ensure_ascii=False, sort_keys=True),
            ),
        )

    conn.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "target_count": len(TARGET_BOOKS),
                "shared_all": shared_all,
                "partial_component_count": len(partial),
                "accepted_human_gloss_count": 0,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
