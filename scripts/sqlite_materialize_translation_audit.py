#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sqlite3
from datetime import UTC, datetime
from typing import Any, Dict, List

from sqlite_snapshot_ref import DEFAULT_SNAPSHOT_NAME, resolve_export_id


DEFAULT_DB = "./data/bonelord_operational.sqlite"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Materialize an audited display layer for current book translations")
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--export-id", type=int, default=None)
    parser.add_argument("--snapshot-name", default=DEFAULT_SNAPSHOT_NAME)
    return parser.parse_args()


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS translation_audit_books (
            export_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            decodedbase TEXT,
            translation_contextenglish_auto TEXT,
            audited_contextenglish TEXT,
            risk_score INTEGER NOT NULL,
            risk_flags_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY (export_id, bookid)
        );
        """
    )


def add_flag(flags: List[Dict[str, str]], code: str, reason: str) -> None:
    flags.append({"code": code, "reason": reason})


def audited_text(decoded: str, context: str, flags: List[Dict[str, str]]) -> str:
    out = context or ""
    decoded_upper = (decoded or "").upper()
    if "VTLRNEFIE" in decoded_upper:
        out = re.sub(r"\bfervently\b", "<VTLRNEFIE?>", out, flags=re.IGNORECASE)
        add_flag(
            flags,
            "VTLRNEFIE_PREFIX_CHILD_CONTRADICTION",
            "VTLRNEFIE appears here; base translation and macro descendants disagree between fervently and unfertile/fay.",
        )
    if "TTNVVN" in decoded_upper:
        out = re.sub(r"\btumtum\b", "<UNK:TTNVVN>", out, flags=re.IGNORECASE)
        add_flag(
            flags,
            "TTNVVN_UNKNOWN_MACRO_LEAK",
            "TTNVVN base was sanitized to <UNK>, but descendant macros may still leak tumtum.",
        )
    if "<UNK>" in out or "<UNK:" in out:
        add_flag(flags, "UNKNOWN_PRESENT", "Audited text still contains unknown token markers.")
    if re.search(r"\bfay\b|\bunfertile\b", out, flags=re.IGNORECASE):
        add_flag(flags, "SURFACE_ANAGRAM_WORD", "Text contains a surface/anagram-like English word that is not semantically confirmed.")
    if "you've no you've no" in out.lower():
        add_flag(flags, "REPEATED_GRAMMAR_ARTIFACT", "Text contains repeated phrase pattern likely caused by macro absorption.")
    return out


def materialize(conn: sqlite3.Connection, export_id: int) -> Dict[str, Any]:
    ensure_schema(conn)
    rows = conn.execute(
        """
        SELECT bookid, decodedbase, translation_contextenglish_auto
        FROM sheet__books
        WHERE __export_id = ?
        ORDER BY CAST(coalesce(bookid, 0) AS INTEGER)
        """,
        (export_id,),
    ).fetchall()
    now = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    summary = {
        "books": 0,
        "flagged_books": 0,
        "risk_histogram": {},
        "flag_counts": {},
    }
    for row in rows:
        flags: List[Dict[str, str]] = []
        decoded = str(row["decodedbase"] or "")
        context = str(row["translation_contextenglish_auto"] or "")
        audited = audited_text(decoded, context, flags)
        risk_score = 0
        for flag in flags:
            risk_score += {
                "VTLRNEFIE_PREFIX_CHILD_CONTRADICTION": 5,
                "TTNVVN_UNKNOWN_MACRO_LEAK": 4,
                "UNKNOWN_PRESENT": 2,
                "SURFACE_ANAGRAM_WORD": 2,
                "REPEATED_GRAMMAR_ARTIFACT": 2,
            }.get(flag["code"], 1)
            summary["flag_counts"][flag["code"]] = summary["flag_counts"].get(flag["code"], 0) + 1
        conn.execute(
            """
            INSERT INTO translation_audit_books (
                export_id, bookid, decodedbase, translation_contextenglish_auto,
                audited_contextenglish, risk_score, risk_flags_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(export_id, bookid) DO UPDATE SET
                decodedbase = excluded.decodedbase,
                translation_contextenglish_auto = excluded.translation_contextenglish_auto,
                audited_contextenglish = excluded.audited_contextenglish,
                risk_score = excluded.risk_score,
                risk_flags_json = excluded.risk_flags_json,
                created_at = excluded.created_at
            """,
            (
                export_id,
                row["bookid"],
                decoded,
                context,
                audited,
                risk_score,
                json.dumps(flags, ensure_ascii=True),
                now,
            ),
        )
        summary["books"] += 1
        if flags:
            summary["flagged_books"] += 1
        key = str(risk_score)
        summary["risk_histogram"][key] = summary["risk_histogram"].get(key, 0) + 1
    conn.commit()
    return summary


def main() -> int:
    args = parse_args()
    conn = connect(args.db)
    try:
        export_id = resolve_export_id(conn, export_id=args.export_id, snapshot_name=args.snapshot_name)
        summary = materialize(conn, export_id)
    finally:
        conn.close()
    print(json.dumps({"export_id": export_id, "summary": summary}, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
