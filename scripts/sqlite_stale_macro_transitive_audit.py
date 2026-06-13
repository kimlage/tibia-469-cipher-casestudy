#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import UTC, datetime
from typing import Any


DEFAULT_DB = "./data/bonelord_operational.sqlite"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Find macros whose audited render is stale against audited component renders")
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--targets", nargs="+", default=["EBTIIALBENEIENVNSBVN*V", "EBTII"])
    parser.add_argument("--record", action="store_true")
    return parser.parse_args()


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone() is not None


def latest_run_id(conn: sqlite3.Connection, table: str) -> int | None:
    if not table_exists(conn, table):
        return None
    row = conn.execute(f"SELECT run_id FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    return int(row["run_id"]) if row else None


def safe_json(raw: object, default: Any) -> Any:
    if raw in (None, ""):
        return default
    try:
        return json.loads(str(raw))
    except json.JSONDecodeError:
        return default


def load_macro_rows(conn: sqlite3.Connection) -> tuple[int | None, dict[str, dict[str, Any]]]:
    run_id = latest_run_id(conn, "macro_recomposition_audit_runs")
    if run_id is None:
        return None, {}
    rows = conn.execute(
        """
        SELECT token, original_translation, audited_recomposed_translation,
               component_tokens_json, changed
        FROM macro_recomposition_audit
        WHERE run_id = ?
        """,
        (run_id,),
    ).fetchall()
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        out[str(row["token"])] = {
            "token": str(row["token"]),
            "original_translation": str(row["original_translation"] or ""),
            "audited_recomposed_translation": str(row["audited_recomposed_translation"] or ""),
            "components": [str(item) for item in safe_json(row["component_tokens_json"], [])],
            "changed": int(row["changed"] or 0),
        }
    return run_id, out


def glossary_map(conn: sqlite3.Connection) -> dict[str, str]:
    export_row = conn.execute("SELECT MAX(__export_id) AS export_id FROM sheet__glossary").fetchone()
    export_id = export_row["export_id"] if export_row else None
    rows = conn.execute(
        "SELECT token, translation FROM sheet__glossary WHERE __export_id = ?",
        (export_id,),
    ).fetchall()
    return {str(row["token"]): str(row["translation"] or "") for row in rows}


def transitive_render(token: str, macros: dict[str, dict[str, Any]], gloss: dict[str, str], depth: int = 0) -> str:
    if depth > 8:
        return macros.get(token, {}).get("audited_recomposed_translation") or gloss.get(token, f"<MISSING:{token}>")
    row = macros.get(token)
    if not row:
        return gloss.get(token, f"<MISSING:{token}>")
    components = row.get("components") or []
    if not components:
        return row.get("audited_recomposed_translation") or gloss.get(token, f"<MISSING:{token}>")
    parts = [transitive_render(component, macros, gloss, depth + 1) for component in components]
    return " ".join(part for part in parts if part)


def contains_target(row: dict[str, Any], targets: set[str]) -> bool:
    token = str(row["token"])
    components = set(row.get("components") or [])
    return token in targets or bool(components & targets) or any(target in token for target in targets)


def build_payload(conn: sqlite3.Connection, targets: list[str]) -> dict[str, Any]:
    macro_run_id, macros = load_macro_rows(conn)
    gloss = glossary_map(conn)
    target_set = set(targets)
    items: list[dict[str, Any]] = []
    for row in macros.values():
        if not contains_target(row, target_set):
            continue
        audited = str(row["audited_recomposed_translation"] or "")
        transitive = transitive_render(str(row["token"]), macros, gloss)
        stale = audited != transitive
        severity = 0
        reasons: list[str] = []
        if stale:
            severity += 50
            reasons.append("AUDITED_RENDER_DIFFERS_FROM_TRANSITIVE_COMPONENT_RENDER")
        if "hidy" in audited.lower() or "hidy" in str(row["original_translation"]).lower():
            severity += 40
            reasons.append("STALE_HIDY_PRESENT")
        if "enable even" in audited.lower() or "enable even" in str(row["original_translation"]).lower():
            severity += 20
            reasons.append("STALE_ENABLE_EVEN_PRESENT")
        if "<UNK>" in transitive or "<UNK:" in transitive:
            severity += 10
            reasons.append("TRANSITIVE_RENDER_EXPOSES_UNKNOWN")
        item = {
            "token": row["token"],
            "original_translation": row["original_translation"],
            "audited_recomposed_translation": audited,
            "transitive_component_render": transitive,
            "components": row["components"],
            "stale": stale,
            "severity": severity,
            "reasons": reasons,
        }
        if severity:
            if "STALE_HIDY_PRESENT" in reasons:
                item["recommendation"] = "DISPLAY_RECOMPOSE_TRANSITIVE_KEEP_TII_UNKNOWN"
            elif stale:
                item["recommendation"] = "RECOMPOSE_FROM_AUDITED_COMPONENTS"
            else:
                item["recommendation"] = "MONITOR"
            items.append(item)
    items.sort(key=lambda item: (-int(item["severity"]), len(str(item["token"])), str(item["token"])))
    return {
        "macro_recomposition_run_id": macro_run_id,
        "targets": targets,
        "item_count": len(items),
        "items": items,
        "interpretation": "Stale macros should render from audited components in shadow/display; this is not a core lexical promotion.",
    }


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS stale_macro_transitive_audit_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            macro_recomposition_run_id INTEGER,
            targets_json TEXT NOT NULL,
            item_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS stale_macro_transitive_audit_items (
            run_id INTEGER NOT NULL,
            rank INTEGER NOT NULL,
            token TEXT NOT NULL,
            stale INTEGER NOT NULL,
            severity INTEGER NOT NULL,
            recommendation TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, rank)
        );
        """
    )


def record(conn: sqlite3.Connection, payload: dict[str, Any]) -> int:
    ensure_schema(conn)
    created_at = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    cur = conn.execute(
        """
        INSERT INTO stale_macro_transitive_audit_runs (
            created_at, macro_recomposition_run_id, targets_json, item_count, payload_json
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (
            created_at,
            payload["macro_recomposition_run_id"],
            json.dumps(payload["targets"], ensure_ascii=True),
            payload["item_count"],
            json.dumps({k: v for k, v in payload.items() if k != "items"}, ensure_ascii=True, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)
    for rank, item in enumerate(payload["items"], start=1):
        conn.execute(
            """
            INSERT INTO stale_macro_transitive_audit_items (
                run_id, rank, token, stale, severity, recommendation, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                rank,
                item["token"],
                1 if item["stale"] else 0,
                item["severity"],
                item["recommendation"],
                json.dumps(item, ensure_ascii=True, sort_keys=True),
            ),
        )
    conn.commit()
    return run_id


def main() -> int:
    args = parse_args()
    conn = connect(args.db)
    try:
        payload = build_payload(conn, args.targets)
        run_id = record(conn, payload) if args.record else None
    finally:
        conn.close()
    print(
        json.dumps(
            {
                "recorded_run_id": run_id,
                "macro_recomposition_run_id": payload["macro_recomposition_run_id"],
                "item_count": payload["item_count"],
                "top": [
                    {
                        "token": item["token"],
                        "severity": item["severity"],
                        "reasons": item["reasons"],
                        "audited": item["audited_recomposed_translation"],
                        "transitive": item["transitive_component_render"],
                        "recommendation": item["recommendation"],
                    }
                    for item in payload["items"][:20]
                ],
            },
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
