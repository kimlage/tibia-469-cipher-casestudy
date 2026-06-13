#!/usr/bin/env python3
"""Test the Book7 human shadow claim as a phase-continuity bridge."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

TARGET_BOOKS = ["6", "7", "19", "31", "57"]
COMPONENTS = ["NEIAAETTA", "TIINNEF", "VNCTIIN", "BENNA"]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_book7_phase_shadow_probe_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            target_count INTEGER NOT NULL,
            bridge_book_count INTEGER NOT NULL,
            continuity_only_count INTEGER NOT NULL,
            phase_context_count INTEGER NOT NULL,
            accepted_human_gloss_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_book7_phase_shadow_probe_v1_items (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            symbol_text TEXT NOT NULL,
            component_hits_json TEXT NOT NULL,
            classification TEXT NOT NULL,
            shadow_implication TEXT NOT NULL,
            next_action TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        );
        """
    )


def classify(hits: dict[str, int]) -> tuple[str, str, str]:
    has_neia = hits["NEIAAETTA"] >= 0
    has_tiinnef = hits["TIINNEF"] >= 0
    has_vnctiin = hits["VNCTIIN"] >= 0
    has_benna = hits["BENNA"] >= 0
    if has_neia and has_tiinnef and not has_vnctiin:
        return (
            "PHASE_BRIDGE_CONTINUITY_TO_ANCHOR",
            "Supports the Book7 shadow reading as a bridge from continuity into phase anchor.",
            "Use Book 7 as the positive bridge witness; compare directionality with 6 and 19/31/57.",
        )
    if has_neia and not has_tiinnef:
        return (
            "CONTINUITY_ONLY_CONTROL",
            "Continuity marker without phase anchor; useful control for Book 7.",
            "Use as NEIAAETTA-only control.",
        )
    if has_tiinnef and has_vnctiin:
        return (
            "PHASE_CONTEXT_CONTROL",
            "Phase anchor embedded in VNCTIIN/context family; useful held-out control.",
            "Use as TIINNEF+VNCTIIN control.",
        )
    if has_benna:
        return (
            "BENNA_ADJACENT_CONTROL",
            "BENNA adjacent but not the Book7 bridge shape.",
            "Keep as formula/context control only.",
        )
    return (
        "UNCLASSIFIED_PHASE_CONTROL",
        "Does not match expected phase/continuity split.",
        "Inspect manually before using for human paraphrase.",
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
    records = []
    for row in rows:
        text = str(row["symbol_text"])
        hits = {component: text.find(component) for component in COMPONENTS}
        classification, implication, next_action = classify(hits)
        records.append(
            {
                "bookid": str(row["bookid"]),
                "symbol_text": text,
                "hits": hits,
                "classification": classification,
                "implication": implication,
                "next_action": next_action,
            }
        )

    bridge_count = sum(1 for row in records if row["classification"] == "PHASE_BRIDGE_CONTINUITY_TO_ANCHOR")
    continuity_only_count = sum(1 for row in records if row["classification"] == "CONTINUITY_ONLY_CONTROL")
    phase_context_count = sum(1 for row in records if row["classification"] == "PHASE_CONTEXT_CONTROL")
    if bridge_count == 1 and continuity_only_count >= 1 and phase_context_count >= 1:
        decision = "BOOK7_PHASE_SHADOW_BRIDGE_SUPPORTED_NO_GLOSS"
    elif bridge_count:
        decision = "BOOK7_PHASE_SHADOW_BRIDGE_PARTIAL_SUPPORT_NO_GLOSS"
    else:
        decision = "BOOK7_PHASE_SHADOW_BRIDGE_NOT_SUPPORTED"
    payload = {
        "target_books": TARGET_BOOKS,
        "components": COMPONENTS,
        "principle": "phase/continuity support only; no lexical translation",
    }
    cur = conn.execute(
        """
        INSERT INTO human_book7_phase_shadow_probe_v1_runs
        (created_at, decision, target_count, bridge_book_count,
         continuity_only_count, phase_context_count, accepted_human_gloss_count,
         payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            now(),
            decision,
            len(records),
            bridge_count,
            continuity_only_count,
            phase_context_count,
            0,
            json.dumps(payload, ensure_ascii=False, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)
    for row in records:
        conn.execute(
            """
            INSERT INTO human_book7_phase_shadow_probe_v1_items
            (run_id, bookid, symbol_text, component_hits_json, classification,
             shadow_implication, next_action, evidence_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                row["bookid"],
                row["symbol_text"],
                json.dumps(row["hits"], ensure_ascii=False, sort_keys=True),
                row["classification"],
                row["implication"],
                row["next_action"],
                json.dumps({"bridge_count": bridge_count, "phase_context_count": phase_context_count}, ensure_ascii=False, sort_keys=True),
            ),
        )

    conn.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "target_count": len(records),
                "bridge_book_count": bridge_count,
                "continuity_only_count": continuity_only_count,
                "phase_context_count": phase_context_count,
                "accepted_human_gloss_count": 0,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
