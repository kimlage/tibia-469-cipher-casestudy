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
    parser = argparse.ArgumentParser(description="Materialize audited glossary translations without mutating decode state")
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
        CREATE TABLE IF NOT EXISTS translation_audit_glossary (
            export_id INTEGER NOT NULL,
            token TEXT NOT NULL,
            original_translation TEXT,
            audited_translation TEXT,
            risk_score INTEGER NOT NULL,
            risk_flags_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY (export_id, token)
        );
        """
    )


def add_flag(flags: List[Dict[str, str]], code: str, reason: str) -> None:
    flags.append({"code": code, "reason": reason})


def audit_translation(token: str, translation: str, flags: List[Dict[str, str]]) -> str:
    token_upper = token.upper()
    out = translation or ""

    if token_upper.startswith("VTLRNEFIE") and "unfertile" in out.lower():
        out = re.sub(r"\bunfertile\b", "<VTLRNEFIE?>", out, flags=re.IGNORECASE)
        out = re.sub(r"\bfay\b", "<AIF?>", out, flags=re.IGNORECASE)
        add_flag(
            flags,
            "VTLRNEFIE_STALE_CHILD_TRANSLATION",
            "Child macro preserves old unfertile/fay render while base VTLRNEFIE currently renders as fervently.",
        )

    if "TTNVVN" in token_upper and "tumtum" in out.lower():
        out = re.sub(r"\btumtum\b", "<UNK:TTNVVN>", out, flags=re.IGNORECASE)
        add_flag(
            flags,
            "TTNVVN_UNKNOWN_MACRO_LEAK",
            "Base TTNVVN is sanitized as <UNK>, but this macro still leaks tumtum.",
        )

    if "<UNK>" in out or "<UNK:" in out:
        add_flag(flags, "UNKNOWN_PRESENT", "Audited glossary translation contains unknown marker.")

    if re.search(r"\bunfertile\b|\bfay\b|\btumtum\b", out, flags=re.IGNORECASE):
        add_flag(flags, "SURFACE_WORD_REMAINS", "Audited translation still contains a known surface/hallucination-prone word.")

    return out


def materialize(conn: sqlite3.Connection, export_id: int) -> Dict[str, Any]:
    ensure_schema(conn)
    rows = conn.execute(
        """
        SELECT token, translation
        FROM sheet__glossary
        WHERE __export_id = ?
          AND token IS NOT NULL
          AND translation IS NOT NULL
        ORDER BY __row_index
        """,
        (export_id,),
    ).fetchall()
    now = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    summary: Dict[str, Any] = {
        "terms": 0,
        "flagged_terms": 0,
        "changed_terms": 0,
        "flag_counts": {},
    }
    weights = {
        "VTLRNEFIE_STALE_CHILD_TRANSLATION": 5,
        "TTNVVN_UNKNOWN_MACRO_LEAK": 5,
        "UNKNOWN_PRESENT": 2,
        "SURFACE_WORD_REMAINS": 2,
    }
    for row in rows:
        token = str(row["token"] or "")
        translation = str(row["translation"] or "")
        flags: List[Dict[str, str]] = []
        audited = audit_translation(token, translation, flags)
        risk = 0
        for flag in flags:
            risk += weights.get(flag["code"], 1)
            summary["flag_counts"][flag["code"]] = summary["flag_counts"].get(flag["code"], 0) + 1
        conn.execute(
            """
            INSERT INTO translation_audit_glossary (
                export_id, token, original_translation, audited_translation,
                risk_score, risk_flags_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(export_id, token) DO UPDATE SET
                original_translation = excluded.original_translation,
                audited_translation = excluded.audited_translation,
                risk_score = excluded.risk_score,
                risk_flags_json = excluded.risk_flags_json,
                created_at = excluded.created_at
            """,
            (export_id, token, translation, audited, risk, json.dumps(flags, ensure_ascii=True), now),
        )
        summary["terms"] += 1
        if flags:
            summary["flagged_terms"] += 1
        if audited != translation:
            summary["changed_terms"] += 1
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
