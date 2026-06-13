#!/usr/bin/env python3
"""Seed human shadow readings for missing C86/VNCTIIN-family books."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
TARGETS = ["2", "3", "13", "17", "19", "23", "24", "27", "31", "44", "52", "57", "62", "67"]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_json(value: str | None, fallback):
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def tag_ids(tags_json: str) -> set[str]:
    tags = parse_json(tags_json, [])
    ids: set[str] = set()
    for tag in tags:
        if isinstance(tag, dict):
            ids.add(str(tag.get("tag_id", "")))
    return ids


def classify(bookid: str, tags_json: str) -> dict[str, str]:
    ids = tag_ids(tags_json)
    has_c86 = "C86_PAYLOAD_OPERATOR" in ids
    has_vn = "VNCTIIN_CONTEXT_FRAME" in ids
    has_tail = "TAILBETFTE_SUFFIX_FRAME" in ids
    has_benna = "BENNA_FORMULA_BRIDGE" in ids
    has_naese = "NAESE_C68_FATCT_LOCAL_SLOT" in ids
    has_o23 = "O23_ONAF_VEINLETFNAAST_PAYLOAD_CONTEXT" in ids
    has_tiinnef = "BOOK7_TIINNEF_PHASE_ANCHOR" in ids
    has_vinvin = "VINVIN_BRANCH_SUBFUNCTION" in ids or "VINVIN_NEGATIVE_CONTROL" in ids
    if has_o23:
        return {
            "subfamily": "O23_VNCTIIN_ENDPOINT",
            "bridge_id": "B_O23_VNCTIIN_ENDPOINT_CONTEXT",
            "likely_speech_act": "VNCTIIN context with direct O23 endpoint payload",
            "reading": "A VNCTIIN-context line that enters the direct O23/ONAF/VEINLETFNAAST endpoint branch; keep this separate from Book12/21 terminal readings.",
            "confidence": "STRUCTURAL_STRONG_ENDPOINT_CONTROL",
        }
    if has_c86 and has_vn:
        qualifiers = []
        if has_benna:
            qualifiers.append("BENNA formula handoff")
        if has_tail:
            qualifiers.append("TAILBETFTE suffix")
        if has_naese:
            qualifiers.append("NAESE/C68 slot")
        detail = ", ".join(qualifiers) if qualifiers else "clean payload corridor"
        return {
            "subfamily": "C86_VNCTIIN_PAYLOAD",
            "bridge_id": "B_C86_VNCTIIN_PAYLOAD_CORRIDOR",
            "likely_speech_act": f"C86 payload-open into VNCTIIN/C68 context ({detail})",
            "reading": f"A C86 payload-opening line into the VNCTIIN/C68 context corridor, with {detail}; this is a corridor/slot transition, not a sentence gloss.",
            "confidence": "STRUCTURAL_STRONG_PAYLOAD_CONTEXT",
        }
    if has_c86 and has_vinvin:
        return {
            "subfamily": "C86_VINVIN_VTLR_BRANCH",
            "bridge_id": "B_C86_VINVIN_BRANCH",
            "likely_speech_act": "C86 payload-open into VINVIN/VTLR branch",
            "reading": "A C86-opened VINVIN/VTLR branch line, likely a branch/phase selector rather than VNCTIIN context prose.",
            "confidence": "STRUCTURAL_MODERATE_BRANCH_CONTROL",
        }
    if has_vn and has_tiinnef:
        return {
            "subfamily": "VNCTIIN_PHASE_CONTEXT",
            "bridge_id": "B_VNCTIIN_PHASE_CONTEXT",
            "likely_speech_act": "VNCTIIN context carrying TIINNEF phase anchor",
            "reading": "A VNCTIIN context line carrying a TIINNEF phase anchor, useful as a phase-context control for the Book7 bridge.",
            "confidence": "STRUCTURAL_STRONG_PHASE_CONTEXT",
        }
    if has_vn:
        return {
            "subfamily": "VNCTIIN_CONTEXT_ONLY",
            "bridge_id": "B_VNCTIIN_PHASE_CONTEXT",
            "likely_speech_act": "VNCTIIN context-only line",
            "reading": "A VNCTIIN context-only line without C86 payload-open evidence; keep it as context frame rather than payload prose.",
            "confidence": "STRUCTURAL_MODERATE_CONTEXT_CONTROL",
        }
    return {
        "subfamily": "C86_VNCTIIN_UNCLASSIFIED",
        "bridge_id": "B_C86_VNCTIIN_PAYLOAD_CORRIDOR",
        "likely_speech_act": "unclassified C86/VNCTIIN-family line",
        "reading": "An unclassified C86/VNCTIIN-family line requiring manual split before stronger human reading.",
        "confidence": "STRUCTURAL_AUDIT_ONLY",
    }


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_c86_vnctiin_shadow_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            bridge_run_id INTEGER NOT NULL,
            item_count INTEGER NOT NULL,
            subfamily_count INTEGER NOT NULL,
            canonical_promotion_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_c86_vnctiin_shadow_v1_items (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            subfamily TEXT NOT NULL,
            likely_speech_act TEXT NOT NULL,
            plausible_human_reading TEXT NOT NULL,
            confidence_tier TEXT NOT NULL,
            source_bridge_id TEXT NOT NULL,
            anchor_ids_json TEXT NOT NULL,
            support_level TEXT NOT NULL,
            blocked_claims_json TEXT NOT NULL,
            blocked_overreach TEXT NOT NULL,
            falsifier TEXT NOT NULL,
            next_probe TEXT NOT NULL,
            promotion_status TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        );
        """
    )


def max_id(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT max(run_id) AS run_id FROM {table}").fetchone()
    if row is None or row["run_id"] is None:
        raise RuntimeError(f"missing required run: {table}")
    return int(row["run_id"])


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    bridge_run_id = max_id(conn, "human_c86_vnctiin_bridge_v1_items")
    bridges = {
        row["bridge_id"]: dict(row)
        for row in conn.execute(
            "SELECT * FROM human_c86_vnctiin_bridge_v1_items WHERE run_id=?",
            (bridge_run_id,),
        ).fetchall()
    }
    placeholders = ",".join("?" for _ in TARGETS)
    books = conn.execute(
        f"""
        SELECT b.bookid, b.functional_tags_json, b.honest_text, t.symbol_text
        FROM final_honest_reading_v19_books b
        JOIN row0_variant_book_tokens t
          ON t.bookid=b.bookid
         AND t.run_id=(SELECT max(run_id) FROM row0_variant_book_tokens)
        WHERE b.run_id=(SELECT max(run_id) FROM final_honest_reading_v19_books)
          AND b.bookid IN ({placeholders})
        ORDER BY CAST(b.bookid AS INTEGER)
        """,
        tuple(TARGETS),
    ).fetchall()
    prepared = []
    for row in books:
        cls = classify(str(row["bookid"]), str(row["functional_tags_json"]))
        bridge = bridges[cls["bridge_id"]]
        blockers = [
            "No lexical gloss is promoted for C86, VNCTIIN, VINVIN, or O23 components.",
            bridge["blocked_overreach"],
        ]
        prepared.append(
            {
                "bookid": str(row["bookid"]),
                "subfamily": cls["subfamily"],
                "likely_speech_act": cls["likely_speech_act"],
                "reading": cls["reading"],
                "confidence": cls["confidence"],
                "bridge": bridge,
                "blocked_claims": blockers,
                "falsifier": f"If Book {row['bookid']} fails the {cls['subfamily']} controls or collapses into another subfamily, revise the reading.",
                "next_probe": bridge["next_probe"],
                "evidence": {
                    "functional_tags_json": row["functional_tags_json"],
                    "honest_text": row["honest_text"],
                    "symbol_text": row["symbol_text"],
                },
            }
        )

    subfamilies = sorted({item["subfamily"] for item in prepared})
    cur = conn.execute(
        """
        INSERT INTO human_c86_vnctiin_shadow_v1_runs
        (created_at, decision, bridge_run_id, item_count, subfamily_count,
         canonical_promotion_count, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            now(),
            "HUMAN_C86_VNCTIIN_SHADOW_READY_NOT_PROMOTED",
            bridge_run_id,
            len(prepared),
            len(subfamilies),
            0,
            json.dumps({"subfamilies": subfamilies}, ensure_ascii=False, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)
    for item in prepared:
        bridge = item["bridge"]
        conn.execute(
            """
            INSERT INTO human_c86_vnctiin_shadow_v1_items
            (run_id, bookid, subfamily, likely_speech_act,
             plausible_human_reading, confidence_tier, source_bridge_id,
             anchor_ids_json, support_level, blocked_claims_json,
             blocked_overreach, falsifier, next_probe, promotion_status,
             evidence_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                item["bookid"],
                item["subfamily"],
                item["likely_speech_act"],
                item["reading"],
                item["confidence"],
                bridge["bridge_id"],
                bridge["anchor_ids_json"],
                bridge["support_level"],
                json.dumps(item["blocked_claims"], ensure_ascii=False, sort_keys=True),
                bridge["blocked_overreach"],
                item["falsifier"],
                item["next_probe"],
                "NOT_PROMOTED",
                json.dumps(item["evidence"], ensure_ascii=False, sort_keys=True),
            ),
        )

    conn.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": "HUMAN_C86_VNCTIIN_SHADOW_READY_NOT_PROMOTED",
                "item_count": len(prepared),
                "subfamily_count": len(subfamilies),
                "canonical_promotion_count": 0,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
