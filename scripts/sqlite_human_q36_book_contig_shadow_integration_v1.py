#!/usr/bin/env python3
"""Q36: integrate the contig shadow atlas back into the 70-book human atlas."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

HIGH_PRIORITY_NONCONTIG_STRATA = {
    "PAYLOAD_CONTEXT_CORRIDOR",
    "FORMULA_HANDOFF_PACKET",
    "BRANCH_PHASE_CONTROL_PACKET",
    "SLOT_CLASSIFIER_PACKET",
    "FAMILY_SPINE_PACKET",
    "COMPOSITE_SLOT_FORMULA_PACKET",
}


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q36_book_contig_shadow_integration_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q30_run_id INTEGER NOT NULL,
            q35_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            book_count INTEGER NOT NULL,
            contig_shadow_book_count INTEGER NOT NULL,
            noncontig_book_count INTEGER NOT NULL,
            high_priority_noncontig_count INTEGER NOT NULL,
            weak_contig_book_count INTEGER NOT NULL,
            component_gloss_allowed_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q36_book_contig_shadow_integration_v1_items (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            compiled_stratum TEXT NOT NULL,
            source_layer TEXT NOT NULL,
            likely_speech_act TEXT NOT NULL,
            plausible_human_reading TEXT NOT NULL,
            contig_status TEXT NOT NULL,
            basecontigid TEXT NOT NULL,
            contig_booksinorder TEXT NOT NULL,
            contig_human_functional_version TEXT NOT NULL,
            priority_class TEXT NOT NULL,
            next_action TEXT NOT NULL,
            promotion_status TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        );
        """
    )


def latest_row(conn: sqlite3.Connection, table: str) -> sqlite3.Row:
    row = conn.execute(f"SELECT * FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    if row is None:
        raise RuntimeError(f"missing required row: {table}")
    return row


def q35_book_map(conn: sqlite3.Connection, q35_run_id: int) -> dict[str, sqlite3.Row]:
    mapping: dict[str, sqlite3.Row] = {}
    for row in conn.execute(
        """
        SELECT *
        FROM human_q35_contig_shadow_atlas_v1_items
        WHERE run_id=?
        """,
        (q35_run_id,),
    ):
        for bookid in str(row["booksinorder"]).split("->"):
            mapping[bookid] = row
    return mapping


def next_action(compiled_stratum: str, contig: sqlite3.Row | None) -> tuple[str, str]:
    if contig is not None:
        confidence = str(contig["confidence"])
        if "WEAK" in confidence or "SCOPED" in confidence:
            return (
                "CONTIG_SHADOW_WEAK_REVIEW",
                "Use the contig version only as a quarantined endpoint clue; search exact source evidence before strengthening.",
            )
        return (
            "CONTIG_SHADOW_READY",
            "Use the contig functional version as the local human shadow reading and source-search context.",
        )
    if compiled_stratum in HIGH_PRIORITY_NONCONTIG_STRATA:
        return (
            "NEXT_FRONTIER_NONCONTIG_HIGH_PRIORITY",
            "Build a family/pair/source bridge probe for this stratum before drafting a standalone human version.",
        )
    return (
        "NEXT_FRONTIER_NONCONTIG_LOW_PRIORITY",
        "Keep as residual compiled fragment until a stronger family, pair, or source bridge appears.",
    )


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q30 = latest_row(conn, "human_q30_great_calculator_compiled_corpus_spine_map_v1_runs")
    q35 = latest_row(conn, "human_q35_contig_shadow_atlas_v1_runs")
    audit = latest_row(conn, "human_translation_completion_audit_v5_runs")
    q30_run_id = int(q30["run_id"])
    q35_run_id = int(q35["run_id"])

    contig_by_book = q35_book_map(conn, q35_run_id)
    q30_books = list(
        conn.execute(
            """
            SELECT *
            FROM human_q30_great_calculator_compiled_corpus_spine_map_v1_books
            WHERE run_id=?
            ORDER BY CAST(bookid AS INTEGER)
            """,
            (q30_run_id,),
        )
    )

    items: list[dict[str, object]] = []
    for book in q30_books:
        bookid = str(book["bookid"])
        contig = contig_by_book.get(bookid)
        priority_class, action = next_action(str(book["compiled_stratum"]), contig)
        items.append(
            {
                "bookid": bookid,
                "compiled_stratum": str(book["compiled_stratum"]),
                "source_layer": str(book["source_layer"]),
                "likely_speech_act": str(book["likely_speech_act"]),
                "plausible_human_reading": str(book["plausible_human_reading"]),
                "contig_status": "EXACT_CONTIG_SHADOW_AVAILABLE" if contig is not None else "NO_EXACT_CONTIG_SHADOW",
                "basecontigid": str(contig["basecontigid"]) if contig is not None else "",
                "contig_booksinorder": str(contig["booksinorder"]) if contig is not None else "",
                "contig_human_functional_version": str(contig["human_functional_version"]) if contig is not None else "",
                "priority_class": priority_class,
                "next_action": action,
                "promotion_status": "NOT_PROMOTED_NO_COMPONENT_GLOSS",
                "evidence": {
                    "q30_book": dict(book),
                    "q35_contig": dict(contig) if contig is not None else None,
                },
            }
        )

    contig_shadow_book_count = sum(1 for item in items if item["contig_status"] == "EXACT_CONTIG_SHADOW_AVAILABLE")
    noncontig_book_count = len(items) - contig_shadow_book_count
    high_priority_noncontig_count = sum(
        1 for item in items if item["priority_class"] == "NEXT_FRONTIER_NONCONTIG_HIGH_PRIORITY"
    )
    weak_contig_book_count = sum(1 for item in items if item["priority_class"] == "CONTIG_SHADOW_WEAK_REVIEW")
    component_gloss_allowed_count = 0
    canonical_promotion_allowed_count = 0
    decision = (
        "Q36_BOOK_CONTIG_SHADOW_INTEGRATION_READY_NEXT_FRONTIER_SELECTED_NO_GLOSS"
        if len(items) == 70
        and contig_shadow_book_count == 14
        and noncontig_book_count == 56
        and int(audit["promoted_gloss_count"]) == 0
        and component_gloss_allowed_count == 0
        and canonical_promotion_allowed_count == 0
        else "Q36_BOOK_CONTIG_SHADOW_INTEGRATION_REQUIRES_REVIEW"
    )
    payload = {
        "question": "How much of the 70-book human atlas is now covered by exact contig shadow versions?",
        "answer": "14 books have exact contig shadow context; 56 books need non-contig family, pair, or source-bridge work.",
        "allowed_use": "Use this table to pick the next human translation frontier by book and stratum.",
        "blocked_use": "Do not count contig context as canonical gloss or complete translation.",
        "next_action": "Prioritize high-priority non-contig books by recurring stratum, starting with families that already have source bridges.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q36_book_contig_shadow_integration_v1_runs (
                created_at, decision, q30_run_id, q35_run_id,
                completion_audit_run_id, book_count, contig_shadow_book_count,
                noncontig_book_count, high_priority_noncontig_count,
                weak_contig_book_count, component_gloss_allowed_count,
                canonical_promotion_allowed_count, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                q30_run_id,
                q35_run_id,
                int(audit["run_id"]),
                len(items),
                contig_shadow_book_count,
                noncontig_book_count,
                high_priority_noncontig_count,
                weak_contig_book_count,
                component_gloss_allowed_count,
                canonical_promotion_allowed_count,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q36_book_contig_shadow_integration_v1_items (
                run_id, bookid, compiled_stratum, source_layer,
                likely_speech_act, plausible_human_reading, contig_status,
                basecontigid, contig_booksinorder,
                contig_human_functional_version, priority_class,
                next_action, promotion_status, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    str(item["bookid"]),
                    str(item["compiled_stratum"]),
                    str(item["source_layer"]),
                    str(item["likely_speech_act"]),
                    str(item["plausible_human_reading"]),
                    str(item["contig_status"]),
                    str(item["basecontigid"]),
                    str(item["contig_booksinorder"]),
                    str(item["contig_human_functional_version"]),
                    str(item["priority_class"]),
                    str(item["next_action"]),
                    str(item["promotion_status"]),
                    j(item["evidence"]),
                )
                for item in items
            ],
        )

    print(
        j(
            {
                "run_id": run_id,
                "decision": decision,
                "book_count": len(items),
                "contig_shadow_book_count": contig_shadow_book_count,
                "noncontig_book_count": noncontig_book_count,
                "high_priority_noncontig_count": high_priority_noncontig_count,
                "weak_contig_book_count": weak_contig_book_count,
                "component_gloss_allowed_count": component_gloss_allowed_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
            }
        )
    )


if __name__ == "__main__":
    main()
