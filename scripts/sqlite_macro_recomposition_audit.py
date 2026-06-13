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
COMPOSITION_RE = re.compile(r"Composition tokens:\s*(.+?)(?:\.|;|$)", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Recompose macro translations from current component translations")
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--export-id", type=int, default=None)
    parser.add_argument("--snapshot-name", default=DEFAULT_SNAPSHOT_NAME)
    parser.add_argument("--record", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    return parser.parse_args()


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS macro_recomposition_audit_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            export_id INTEGER NOT NULL,
            macro_count INTEGER NOT NULL,
            changed_count INTEGER NOT NULL,
            missing_component_count INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS macro_recomposition_audit (
            run_id INTEGER NOT NULL,
            token TEXT NOT NULL,
            original_translation TEXT,
            recomposed_translation TEXT,
            audited_recomposed_translation TEXT,
            component_tokens_json TEXT NOT NULL,
            missing_components_json TEXT NOT NULL,
            changed INTEGER NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, token)
        );
        """
    )


def composition_tokens(notes: str) -> List[str]:
    match = COMPOSITION_RE.search(notes or "")
    if not match:
        return []
    raw = match.group(1).strip()
    return [part.strip() for part in raw.split("+") if part.strip()]


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def load_translation_maps(conn: sqlite3.Connection, export_id: int) -> tuple[Dict[str, str], Dict[str, str]]:
    base_rows = conn.execute(
        "SELECT token, translation FROM sheet__glossary WHERE __export_id = ?",
        (export_id,),
    ).fetchall()
    base = {str(row["token"]): str(row["translation"] or "") for row in base_rows if row["token"] is not None}
    audit_rows = conn.execute(
        "SELECT token, audited_translation FROM translation_audit_glossary WHERE export_id = ?",
        (export_id,),
    ).fetchall()
    audited = {str(row["token"]): str(row["audited_translation"] or "") for row in audit_rows if row["token"] is not None}
    return base, audited


def macro_rows(conn: sqlite3.Connection, export_id: int, limit: int) -> List[sqlite3.Row]:
    sql = """
        SELECT token, translation, tokentype, evidenceclass_v127, evidencesources_v127, notes, totalocc, bookcount
        FROM sheet__glossary
        WHERE __export_id = ?
          AND notes LIKE '%Composition tokens:%'
        ORDER BY CAST(coalesce(bookcount, 0) AS INTEGER) DESC,
                 CAST(coalesce(totalocc, 0) AS INTEGER) DESC,
                 length(token) ASC
    """
    params: tuple[Any, ...]
    if limit > 0:
        sql += " LIMIT ?"
        params = (export_id, limit)
    else:
        params = (export_id,)
    return conn.execute(sql, params).fetchall()


def recompose(row: sqlite3.Row, base: Dict[str, str], audited: Dict[str, str]) -> Dict[str, Any]:
    components = composition_tokens(str(row["notes"] or ""))
    recomposed_parts: List[str] = []
    audited_parts: List[str] = []
    missing: List[str] = []
    for component in components:
        if component in base:
            recomposed_parts.append(base[component])
            audited_parts.append(audited.get(component, base[component]))
        else:
            recomposed_parts.append(f"<MISSING:{component}>")
            audited_parts.append(f"<MISSING:{component}>")
            missing.append(component)
    original = normalize_space(str(row["translation"] or ""))
    recomposed = normalize_space(" ".join(recomposed_parts))
    audited_recomposed = normalize_space(" ".join(audited_parts))
    changed = original.lower() != audited_recomposed.lower()
    return {
        "token": row["token"],
        "original_translation": original,
        "recomposed_translation": recomposed,
        "audited_recomposed_translation": audited_recomposed,
        "component_tokens": components,
        "missing_components": missing,
        "changed": changed,
        "tokentype": row["tokentype"],
        "evidence": row["evidenceclass_v127"],
        "bookcount": row["bookcount"],
        "totalocc": row["totalocc"],
    }


def run(conn: sqlite3.Connection, export_id: int, limit: int) -> List[Dict[str, Any]]:
    base, audited = load_translation_maps(conn, export_id)
    rows = macro_rows(conn, export_id, limit)
    items = [recompose(row, base, audited) for row in rows]
    items.sort(
        key=lambda item: (
            not item["changed"],
            len(item["missing_components"]),
            -int(str(item.get("bookcount") or "0").split(".")[0] or 0),
            str(item["token"]),
        )
    )
    return items


def record(conn: sqlite3.Connection, export_id: int, items: List[Dict[str, Any]]) -> int:
    ensure_schema(conn)
    created_at = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    changed_count = sum(1 for item in items if item["changed"])
    missing_count = sum(len(item["missing_components"]) for item in items)
    cur = conn.execute(
        """
        INSERT INTO macro_recomposition_audit_runs (
            created_at, export_id, macro_count, changed_count, missing_component_count
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (created_at, export_id, len(items), changed_count, missing_count),
    )
    run_id = int(cur.lastrowid)
    for item in items:
        conn.execute(
            """
            INSERT INTO macro_recomposition_audit (
                run_id, token, original_translation, recomposed_translation, audited_recomposed_translation,
                component_tokens_json, missing_components_json, changed, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                item["token"],
                item["original_translation"],
                item["recomposed_translation"],
                item["audited_recomposed_translation"],
                json.dumps(item["component_tokens"], ensure_ascii=True),
                json.dumps(item["missing_components"], ensure_ascii=True),
                1 if item["changed"] else 0,
                json.dumps(item, ensure_ascii=True, sort_keys=True),
            ),
        )
    conn.commit()
    return run_id


def main() -> int:
    args = parse_args()
    conn = connect(args.db)
    try:
        export_id = resolve_export_id(conn, export_id=args.export_id, snapshot_name=args.snapshot_name)
        items = run(conn, export_id, args.limit)
        run_id = record(conn, export_id, items) if args.record else None
    finally:
        conn.close()

    payload = {
        "export_id": export_id,
        "recorded_run_id": run_id,
        "macro_count": len(items),
        "changed_count": sum(1 for item in items if item["changed"]),
        "missing_component_count": sum(len(item["missing_components"]) for item in items),
        "top_changed": [item for item in items if item["changed"]][:40],
    }
    print(json.dumps(payload, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
