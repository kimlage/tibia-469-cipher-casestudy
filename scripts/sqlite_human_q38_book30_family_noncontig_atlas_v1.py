#!/usr/bin/env python3
"""Q38: consolidate Book30-family as the first non-contig family atlas entry."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
TARGET_BOOKS = ["12", "21", "26", "30"]

BOOK_HUMAN_VERSIONS = {
    "12": "A compact long-tail spine witness: it preserves TAESESTIEN and the shared VNSBLFSINNAI spine inside the long-tail subfamily.",
    "21": "A long-tail spine witness with a bridge/tail extension: it preserves the Book12 base and adds TIVNSENI/LAELBEV-style tail material.",
    "26": "A branch-prefixed long-tail witness: it carries the shared VNSBLFSINNAI spine and long-tail form without the TAESESTIEN subcomponent.",
    "30": "An alternate-tail family witness: it preserves TAESESTIEN and the shared VNSBLFSINNAI spine but diverges from the long-tail form.",
}

SOURCE_BRIDGES = [
    {
        "bridge_id": "GREAT_CALCULATOR_COMPILED_LANGUAGE",
        "source_url": "https://www.tibiawiki.com.br/wiki/You_Cannot_Even_Imagine_%28Book%29",
        "allowed_inference": "The family can be read as compiled/gathered formula-spine material.",
        "blocked_inference": "No direct 469 phrase meaning follows from the Great Calculator book.",
    },
    {
        "bridge_id": "BEWARE_LANGUAGE_MATH_NUMERIC_BOOKS",
        "source_url": "https://tibia.fandom.com/wiki/Beware_of_the_Bonelords_%28Book%29",
        "allowed_inference": "Repeated symbolic spines are compatible with mathematical book language.",
        "blocked_inference": "Do not translate the spine as a word or sentence.",
    },
    {
        "bridge_id": "AWB_COMPLEX_FORMULA_SUBJECTIVE_VIEWER",
        "source_url": "https://tibia.fandom.com/wiki/A_Wrinkled_Bonelord/Transcripts",
        "allowed_inference": "Variant tails and prefixes can be treated as formula variants in human shadow.",
        "blocked_inference": "Do not claim the Book30 family encodes the race name.",
    },
]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q38_book30_family_noncontig_atlas_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q37_run_id INTEGER NOT NULL,
            book30_probe_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            target_book_count INTEGER NOT NULL,
            source_bridge_count INTEGER NOT NULL,
            shared_all_component_count INTEGER NOT NULL,
            partial_component_count INTEGER NOT NULL,
            family_human_version_count INTEGER NOT NULL,
            component_gloss_allowed_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            family_human_version TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q38_book30_family_noncontig_atlas_v1_books (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            classification TEXT NOT NULL,
            q30_plausible_human_reading TEXT NOT NULL,
            family_human_version TEXT NOT NULL,
            shared_spine TEXT NOT NULL,
            partial_components_json TEXT NOT NULL,
            source_bridge_ids_json TEXT NOT NULL,
            translation_use TEXT NOT NULL,
            blocked_claims_json TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        );

        CREATE TABLE IF NOT EXISTS human_q38_book30_family_noncontig_atlas_v1_components (
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


def latest_row(conn: sqlite3.Connection, table: str) -> sqlite3.Row:
    row = conn.execute(f"SELECT * FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    if row is None:
        raise RuntimeError(f"missing required row: {table}")
    return row


def load_q30_book(conn: sqlite3.Connection, bookid: str) -> sqlite3.Row:
    row = conn.execute(
        """
        SELECT *
        FROM human_q30_great_calculator_compiled_corpus_spine_map_v1_books
        WHERE run_id=(SELECT max(run_id) FROM human_q30_great_calculator_compiled_corpus_spine_map_v1_books)
          AND bookid=?
        """,
        (bookid,),
    ).fetchone()
    if row is None:
        raise RuntimeError(f"missing Q30 book {bookid}")
    return row


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q37 = latest_row(conn, "human_q37_noncontig_frontier_selection_v1_runs")
    book30 = latest_row(conn, "human_book30_family_shadow_probe_v1_runs")
    audit = latest_row(conn, "human_translation_completion_audit_v5_runs")
    book30_run_id = int(book30["run_id"])

    probe_items = {
        str(row["bookid"]): row
        for row in conn.execute(
            """
            SELECT *
            FROM human_book30_family_shadow_probe_v1_items
            WHERE run_id=?
            """,
            (book30_run_id,),
        )
    }
    components = list(
        conn.execute(
            """
            SELECT *
            FROM human_book30_family_shadow_probe_v1_components
            WHERE run_id=?
            ORDER BY component
            """,
            (book30_run_id,),
        )
    )
    missing = [bookid for bookid in TARGET_BOOKS if bookid not in probe_items]
    if missing:
        raise RuntimeError(f"missing Book30 probe items: {missing}")

    shared_all = [row for row in components if row["component_status"] == "SHARED_BY_ALL_TARGET_BOOKS"]
    partial = [row for row in components if row["component_status"] == "PARTIAL_COMPONENT"]
    family_human_version = (
        "Book30-family human shadow: a compiled formula-spine family built around shared VNSBLFSINNAI. "
        "Books 12 and 21 are long-tail witnesses with TAESESTIEN, Book 26 is a branch-prefixed long-tail witness without TAESESTIEN, "
        "and Book 30 is a TAESESTIEN alternate-tail witness. This is a family/spine reading, not prose."
    )
    component_gloss_allowed_count = 0
    canonical_promotion_allowed_count = 0
    decision = (
        "Q38_BOOK30_FAMILY_NONCONTIG_ATLAS_READY_NO_GLOSS"
        if len(shared_all) == 1
        and str(shared_all[0]["component"]) == "VNSBLFSINNAI"
        and len(partial) == 9
        and int(book30["accepted_human_gloss_count"]) == 0
        and int(audit["promoted_gloss_count"]) == 0
        and component_gloss_allowed_count == 0
        and canonical_promotion_allowed_count == 0
        else "Q38_BOOK30_FAMILY_NONCONTIG_ATLAS_REQUIRES_REVIEW"
    )
    payload = {
        "question": "Can the priority-1 non-contig Book30 family become a human shadow atlas entry?",
        "answer": "Yes, as a formula-spine family centered only on VNSBLFSINNAI.",
        "allowed_reading": family_human_version,
        "blocked_reading": "No sentence translation and no component gloss for VNSBLFSINNAI, TAESESTIEN, tails, or prefixes.",
        "next_action": "Use this as the model for remaining non-contig family atlas probes.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q38_book30_family_noncontig_atlas_v1_runs (
                created_at, decision, q37_run_id, book30_probe_run_id,
                completion_audit_run_id, target_book_count,
                source_bridge_count, shared_all_component_count,
                partial_component_count, family_human_version_count,
                component_gloss_allowed_count, canonical_promotion_allowed_count,
                family_human_version, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                int(q37["run_id"]),
                book30_run_id,
                int(audit["run_id"]),
                len(TARGET_BOOKS),
                len(SOURCE_BRIDGES),
                len(shared_all),
                len(partial),
                len(TARGET_BOOKS),
                component_gloss_allowed_count,
                canonical_promotion_allowed_count,
                family_human_version,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q38_book30_family_noncontig_atlas_v1_books (
                run_id, bookid, classification, q30_plausible_human_reading,
                family_human_version, shared_spine, partial_components_json,
                source_bridge_ids_json, translation_use, blocked_claims_json,
                evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    bookid,
                    str(probe_items[bookid]["classification"]),
                    str(load_q30_book(conn, bookid)["plausible_human_reading"]),
                    BOOK_HUMAN_VERSIONS[bookid],
                    "VNSBLFSINNAI",
                    j([dict(row) for row in partial if bookid in json.loads(str(row["books_json"]))]),
                    j([source["bridge_id"] for source in SOURCE_BRIDGES]),
                    "human non-contig family shadow only; not canonical plaintext",
                    j(["component_gloss", "sentence_translation", "race_name_decoding", "endpoint_meaning"]),
                    j(
                        {
                            "book30_probe_item": dict(probe_items[bookid]),
                            "source_bridges": SOURCE_BRIDGES,
                        }
                    ),
                )
                for bookid in TARGET_BOOKS
            ],
        )
        conn.executemany(
            """
            INSERT INTO human_q38_book30_family_noncontig_atlas_v1_components (
                run_id, component, hit_count, books_json, component_status,
                implication
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    str(row["component"]),
                    int(row["hit_count"]),
                    str(row["books_json"]),
                    str(row["component_status"]),
                    str(row["implication"]),
                )
                for row in components
            ],
        )

    print(
        j(
            {
                "run_id": run_id,
                "decision": decision,
                "target_book_count": len(TARGET_BOOKS),
                "source_bridge_count": len(SOURCE_BRIDGES),
                "shared_all_component_count": len(shared_all),
                "shared_all_components": [str(row["component"]) for row in shared_all],
                "partial_component_count": len(partial),
                "component_gloss_allowed_count": component_gloss_allowed_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
            }
        )
    )


if __name__ == "__main__":
    main()
