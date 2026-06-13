#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import UTC, datetime
from typing import Any, Dict, List

from sqlite_snapshot_ref import DEFAULT_SNAPSHOT_NAME, resolve_export_id


DEFAULT_DB = "./data/bonelord_operational.sqlite"

KNOWN_PHRASES = [
    {
        "phrase_id": "NPC-Elder2-653768764",
        "refname": "Elder2",
        "digits": "653768764",
        "expected_text": "look at you",
        "strength": "HARD_EXTERNAL_PHRASE",
        "scope": "external_npc_only",
        "promotion_status": "ACTIVE_QUARANTINE",
        "notes": "The Evil Eye/Elder phrase anchor; must not promote to book decoder.",
    },
    {
        "phrase_id": "NPC-Elder1-65997854764",
        "refname": "Elder1",
        "digits": "65997854764",
        "expected_text": "let me see you",
        "strength": "SOFT_LEGACY_PHRASE",
        "scope": "external_npc_only",
        "promotion_status": "SOFT_QUARANTINE",
        "notes": "Legacy/local phrase anchor; keep soft until independently confirmed.",
    },
    {
        "phrase_id": "NPC-AWB2-UNKNOWN",
        "refname": "AWB2",
        "digits": None,
        "expected_text": None,
        "strength": "UNTRANSLATED_EXTERNAL_NPC",
        "scope": "external_npc_only",
        "promotion_status": "PENDING_SOURCE_TRANSLATION",
        "notes": "Contains 764 support but inbooks_count > 0; cannot yield new word anchors without external translation.",
    },
    {
        "phrase_id": "NPC-AWB1-UNKNOWN",
        "refname": "AWB1",
        "digits": None,
        "expected_text": None,
        "strength": "UNTRANSLATED_EXTERNAL_NPC",
        "scope": "external_npc_only",
        "promotion_status": "PENDING_SOURCE_TRANSLATION",
        "notes": "NPC utterance candidate; no current rosetta overlap.",
    },
    {
        "phrase_id": "NPC-AWB-ID",
        "refname": "AWB_ID",
        "digits": None,
        "expected_text": None,
        "strength": "NPC_IDENTIFIER",
        "scope": "external_npc_only",
        "promotion_status": "ENTITY_QUARANTINE",
        "notes": "Entity/identifier candidate, not lexical wordcode.",
    },
    {
        "phrase_id": "NPC-Knightmare1-UNKNOWN",
        "refname": "Knightmare1",
        "digits": None,
        "expected_text": None,
        "strength": "UNTRANSLATED_EXTERNAL_NPC",
        "scope": "external_npc_only",
        "promotion_status": "PENDING_SOURCE_LOOKUP",
        "notes": "External-only NPC utterance; useful holdout if translation is found.",
    },
    {
        "phrase_id": "NPC-AvarTarPoem-HOLDOUT",
        "refname": "AvarTarPoem",
        "digits": None,
        "expected_text": None,
        "strength": "EXTERNAL_NPC_HOLDOUT",
        "scope": "external_npc_only",
        "promotion_status": "HOLDOUT_NO_PROMOTION",
        "notes": "Long external NPC/poem sequence; holdout for later consistency, not promotion.",
    },
]

NEGATIVE_SOURCE_KEYWORDS = {
    "TORG_2009_CRITIQUE": "NEGATIVE_CONTROL",
    "OTLAND_2026_PIC": "METHOD_SEQUENCE_CANDIDATE",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Materialize NPC wordcode quarantine tables")
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--export-id", type=int, default=None)
    parser.add_argument("--snapshot-name", default=DEFAULT_SNAPSHOT_NAME)
    parser.add_argument("--record", action="store_true")
    return parser.parse_args()


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone() is not None


def safe_int(value: object) -> int:
    try:
        return int(float(str(value or "0")))
    except ValueError:
        return 0


def fetch_external_ref(conn: sqlite3.Connection, export_id: int, refname: str) -> Dict[str, Any] | None:
    if not table_exists(conn, "sheet__externalrefs_v115"):
        return None
    row = conn.execute(
        """
        SELECT refname, type, source, numerictext, digitssanitized, inbooks_count,
               inbooks_bookids, dp_strictplus, codestreamdp_concat_readable_v120
        FROM sheet__externalrefs_v115
        WHERE __export_id = ?
          AND refname = ?
        LIMIT 1
        """,
        (export_id, refname),
    ).fetchone()
    return dict(row) if row else None


def source_hit_count(conn: sqlite3.Connection, export_id: int, digits: str) -> tuple[int, List[str]]:
    if not digits or not table_exists(conn, "sheet__externalsourcedigithits_v472"):
        return 0, []
    rows = conn.execute(
        """
        SELECT DISTINCT sourceid
        FROM sheet__externalsourcedigithits_v472
        WHERE __export_id = ?
          AND digitsrun = ?
        """,
        (export_id, digits),
    ).fetchall()
    source_ids = sorted(str(row["sourceid"]) for row in rows if row["sourceid"] is not None)
    return len(source_ids), source_ids


def build_phrase_anchors(conn: sqlite3.Connection, export_id: int) -> List[Dict[str, Any]]:
    phrases: List[Dict[str, Any]] = []
    for phrase in KNOWN_PHRASES:
        row = fetch_external_ref(conn, export_id, phrase["refname"])
        digits = phrase["digits"] or (row or {}).get("digitssanitized")
        source_hits, source_ids = source_hit_count(conn, export_id, str(digits or ""))
        verified_count = 1 + source_hits if row and phrase["expected_text"] else source_hits
        inbooks_count = safe_int((row or {}).get("inbooks_count"))
        contaminates_books = bool(inbooks_count > 0)
        promotion_status = phrase["promotion_status"]
        if contaminates_books and promotion_status not in {"HOLDOUT_NO_PROMOTION", "ENTITY_QUARANTINE"}:
            promotion_status = "QUARANTINE_INBOOKS_OVERLAP"
        phrases.append(
            {
                **phrase,
                "digits": digits,
                "numerictext": (row or {}).get("numerictext"),
                "type": (row or {}).get("type"),
                "source": (row or {}).get("source"),
                "inbooks_count": inbooks_count,
                "inbooks_bookids": (row or {}).get("inbooks_bookids"),
                "observed_dp": (row or {}).get("dp_strictplus"),
                "observed_codestream": (row or {}).get("codestreamdp_concat_readable_v120"),
                "verified_count": verified_count,
                "source_ids": source_ids,
                "contaminates_books": contaminates_books,
                "promotion_status": promotion_status,
            }
        )
    return phrases


def build_word_anchors(conn: sqlite3.Connection, export_id: int, phrases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not table_exists(conn, "rosetta_digit_word_anchors"):
        return []
    phrase_by_legacy_id = {
        "evil_eye_653768764": "NPC-Elder2-653768764",
        "elder_65997854764": "NPC-Elder1-65997854764",
    }
    phrase_meta = {phrase["phrase_id"]: phrase for phrase in phrases}
    rows = conn.execute(
        """
        SELECT anchor_id, mode, digits, word, phrase_anchor_id, strength, source, notes
        FROM rosetta_digit_word_anchors
        ORDER BY phrase_anchor_id, anchor_id
        """
    ).fetchall()
    anchors: List[Dict[str, Any]] = []
    for row in rows:
        phrase_id = phrase_by_legacy_id.get(str(row["phrase_anchor_id"]), str(row["phrase_anchor_id"]))
        phrase = phrase_meta.get(phrase_id, {})
        strength = str(row["strength"] or "")
        if phrase_id == "NPC-Elder2-653768764":
            promotion_status = "HARD_EXTERNAL_NPC_ONLY"
        elif phrase_id == "NPC-Elder1-65997854764":
            promotion_status = "SOFT_EXTERNAL_NPC_ONLY"
        else:
            promotion_status = "QUARANTINE_ONLY"
        anchors.append(
            {
                "anchor_id": row["anchor_id"],
                "digits": row["digits"],
                "word": row["word"],
                "phrase_id": phrase_id,
                "refname": phrase.get("refname"),
                "source_ids": phrase.get("source_ids", []),
                "strength": strength,
                "scope": "external_npc_only",
                "promotion_status": promotion_status,
                "book_promotion_allowed": 0,
                "notes": row["notes"],
            }
        )
    return anchors


def build_sequence_frontier(conn: sqlite3.Connection, export_id: int, phrases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    frontier: List[Dict[str, Any]] = []
    for phrase in phrases:
        if phrase["expected_text"]:
            continue
        frontier.append(
            {
                "sequence_id": phrase["phrase_id"],
                "refname": phrase["refname"],
                "digits": phrase["digits"],
                "sequence_kind": phrase["strength"],
                "status": phrase["promotion_status"],
                "reason": phrase["notes"],
                "inbooks_count": phrase["inbooks_count"],
                "source_ids": phrase["source_ids"],
                "payload": phrase,
            }
        )
    if table_exists(conn, "sheet__externalrefcandidates_v472"):
        rows = conn.execute(
            """
            SELECT __row_index, digitsrun, hitkind, inbookscount, inbooksbookids,
                   sourceids, urls, priority, notes
            FROM sheet__externalrefcandidates_v472
            WHERE __export_id = ?
              AND digitsrun IS NOT NULL
            ORDER BY __row_index
            """,
            (export_id,),
        ).fetchall()
        for row in rows:
            sourceids = str(row["sourceids"] or "")
            marker = None
            for key, value in NEGATIVE_SOURCE_KEYWORDS.items():
                if key in sourceids:
                    marker = value
                    break
            if marker is None:
                continue
            frontier.append(
                {
                    "sequence_id": f"EXTSEQ-{row['__row_index']}",
                    "refname": None,
                    "digits": row["digitsrun"],
                    "sequence_kind": marker,
                    "status": "AUXILIARY_NOT_GT",
                    "reason": row["notes"],
                    "inbooks_count": safe_int(row["inbookscount"]),
                    "source_ids": [source for source in sourceids.split(",") if source],
                    "payload": dict(row),
                }
            )
    return frontier


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS npc_wordcode_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            export_id INTEGER NOT NULL,
            phrase_count INTEGER NOT NULL,
            word_anchor_count INTEGER NOT NULL,
            frontier_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS npc_phrase_anchors (
            run_id INTEGER NOT NULL,
            phrase_id TEXT NOT NULL,
            refname TEXT,
            digits TEXT,
            expected_text TEXT,
            strength TEXT NOT NULL,
            scope TEXT NOT NULL,
            promotion_status TEXT NOT NULL,
            verified_count INTEGER NOT NULL,
            contaminates_books INTEGER NOT NULL,
            inbooks_count INTEGER NOT NULL,
            inbooks_bookids TEXT,
            source_ids_json TEXT NOT NULL,
            observed_dp TEXT,
            observed_codestream TEXT,
            notes TEXT,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, phrase_id)
        );

        CREATE TABLE IF NOT EXISTS npc_wordcode_anchors (
            run_id INTEGER NOT NULL,
            anchor_id TEXT NOT NULL,
            digits TEXT NOT NULL,
            word TEXT NOT NULL,
            phrase_id TEXT,
            refname TEXT,
            strength TEXT NOT NULL,
            scope TEXT NOT NULL,
            promotion_status TEXT NOT NULL,
            book_promotion_allowed INTEGER NOT NULL,
            source_ids_json TEXT NOT NULL,
            notes TEXT,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, anchor_id)
        );

        CREATE TABLE IF NOT EXISTS npc_sequence_frontier (
            run_id INTEGER NOT NULL,
            sequence_id TEXT NOT NULL,
            refname TEXT,
            digits TEXT,
            sequence_kind TEXT NOT NULL,
            status TEXT NOT NULL,
            reason TEXT,
            inbooks_count INTEGER NOT NULL,
            source_ids_json TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, sequence_id)
        );
        """
    )


def record(conn: sqlite3.Connection, export_id: int, phrases: List[Dict[str, Any]], words: List[Dict[str, Any]], frontier: List[Dict[str, Any]]) -> int:
    ensure_schema(conn)
    created_at = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    summary = {
        "export_id": export_id,
        "phrase_count": len(phrases),
        "word_anchor_count": len(words),
        "frontier_count": len(frontier),
        "hard_external_word_anchors": sum(1 for item in words if item["promotion_status"] == "HARD_EXTERNAL_NPC_ONLY"),
        "soft_external_word_anchors": sum(1 for item in words if item["promotion_status"] == "SOFT_EXTERNAL_NPC_ONLY"),
        "book_promotion_allowed": sum(int(item["book_promotion_allowed"]) for item in words),
        "interpretation": "NPC wordcode anchors are quarantined with scope external_npc_only and cannot feed the book decoder.",
    }
    cur = conn.execute(
        """
        INSERT INTO npc_wordcode_runs (
            created_at, export_id, phrase_count, word_anchor_count, frontier_count, payload_json
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (created_at, export_id, len(phrases), len(words), len(frontier), json.dumps(summary, ensure_ascii=True, sort_keys=True)),
    )
    run_id = int(cur.lastrowid)
    for item in phrases:
        conn.execute(
            """
            INSERT INTO npc_phrase_anchors (
                run_id, phrase_id, refname, digits, expected_text, strength, scope, promotion_status,
                verified_count, contaminates_books, inbooks_count, inbooks_bookids, source_ids_json,
                observed_dp, observed_codestream, notes, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                item["phrase_id"],
                item["refname"],
                item["digits"],
                item["expected_text"],
                item["strength"],
                item["scope"],
                item["promotion_status"],
                int(item["verified_count"]),
                int(bool(item["contaminates_books"])),
                int(item["inbooks_count"]),
                item["inbooks_bookids"],
                json.dumps(item["source_ids"], ensure_ascii=True, sort_keys=True),
                item["observed_dp"],
                item["observed_codestream"],
                item["notes"],
                json.dumps(item, ensure_ascii=True, sort_keys=True),
            ),
        )
    for item in words:
        conn.execute(
            """
            INSERT INTO npc_wordcode_anchors (
                run_id, anchor_id, digits, word, phrase_id, refname, strength, scope,
                promotion_status, book_promotion_allowed, source_ids_json, notes, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                item["anchor_id"],
                item["digits"],
                item["word"],
                item["phrase_id"],
                item["refname"],
                item["strength"],
                item["scope"],
                item["promotion_status"],
                int(item["book_promotion_allowed"]),
                json.dumps(item["source_ids"], ensure_ascii=True, sort_keys=True),
                item["notes"],
                json.dumps(item, ensure_ascii=True, sort_keys=True),
            ),
        )
    for item in frontier:
        conn.execute(
            """
            INSERT INTO npc_sequence_frontier (
                run_id, sequence_id, refname, digits, sequence_kind, status, reason,
                inbooks_count, source_ids_json, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                item["sequence_id"],
                item["refname"],
                item["digits"],
                item["sequence_kind"],
                item["status"],
                item["reason"],
                int(item["inbooks_count"]),
                json.dumps(item["source_ids"], ensure_ascii=True, sort_keys=True),
                json.dumps(item["payload"], ensure_ascii=True, sort_keys=True),
            ),
        )
    conn.commit()
    return run_id


def main() -> int:
    args = parse_args()
    conn = connect(args.db)
    try:
        export_id = resolve_export_id(conn, export_id=args.export_id, snapshot_name=args.snapshot_name)
        phrases = build_phrase_anchors(conn, export_id)
        words = build_word_anchors(conn, export_id, phrases)
        frontier = build_sequence_frontier(conn, export_id, phrases)
        run_id = record(conn, export_id, phrases, words, frontier) if args.record else None
    finally:
        conn.close()
    output = {
        "export_id": export_id,
        "recorded_run_id": run_id,
        "phrase_count": len(phrases),
        "word_anchor_count": len(words),
        "frontier_count": len(frontier),
        "book_promotion_allowed": sum(int(item["book_promotion_allowed"]) for item in words),
        "phrases": phrases,
        "word_anchors": words,
        "frontier": frontier,
    }
    print(json.dumps(output, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
