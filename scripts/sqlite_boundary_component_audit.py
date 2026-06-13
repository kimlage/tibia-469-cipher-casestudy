#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter
from datetime import UTC, datetime
from typing import Any, Dict, List


DEFAULT_DB = "./data/bonelord_operational.sqlite"
DEFAULT_TARGETS = (
    "IIVNT",
    "EIIVNT",
    "TNVIEI",
    "EIIVNTBB",
    "EEINBLE",
    "NBEEILE",
    "NELBEEI",
    "NELBEEILE",
    "EBENEIL",
    "LE",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit boundary ownership with exact component-token evidence")
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--record", action="store_true")
    parser.add_argument("--targets", nargs="*", default=list(DEFAULT_TARGETS))
    parser.add_argument("--max-examples", type=int, default=12)
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


def glossary_rows(conn: sqlite3.Connection, targets: List[str]) -> Dict[str, Dict[str, Any]]:
    placeholders = ",".join("?" for _ in targets)
    rows = conn.execute(
        f"""
        SELECT token, translation, tokentype, confidence, evidenceclass_v127,
               totalocc, bookcount, contigcount, notes
        FROM sheet__glossary
        WHERE __export_id = 2
          AND token IN ({placeholders})
        """,
        tuple(targets),
    ).fetchall()
    return {str(row["token"]): dict(row) for row in rows}


def latest_variant_decisions(conn: sqlite3.Connection) -> Dict[str, Dict[str, Any]]:
    if not table_exists(conn, "semantic_variant_decisions"):
        return {}
    rows = conn.execute(
        """
        SELECT d.*
        FROM semantic_variant_decisions d
        JOIN (
            SELECT token, max(decision_id) AS decision_id
            FROM semantic_variant_decisions
            GROUP BY token
        ) latest
          ON latest.decision_id = d.decision_id
        """
    ).fetchall()
    return {str(row["token"]): dict(row) for row in rows}


def latest_constraints(conn: sqlite3.Connection) -> Dict[str, Dict[str, Any]]:
    if not table_exists(conn, "semantic_constraint_registry"):
        return {}
    rows = conn.execute(
        """
        SELECT c.*
        FROM semantic_constraint_registry c
        JOIN (
            SELECT token, max(constraint_id) AS constraint_id
            FROM semantic_constraint_registry
            GROUP BY token
        ) latest
          ON latest.constraint_id = c.constraint_id
        """
    ).fetchall()
    return {str(row["token"]): dict(row) for row in rows}


def recomposition_rows(conn: sqlite3.Connection) -> List[sqlite3.Row]:
    run_id = latest_run_id(conn, "macro_recomposition_audit_runs")
    if run_id is None:
        return []
    return conn.execute(
        """
        SELECT token, original_translation, audited_recomposed_translation,
               component_tokens_json, changed
        FROM macro_recomposition_audit
        WHERE run_id = ?
        """,
        (run_id,),
    ).fetchall()


def classify_target(target: str, rows: List[sqlite3.Row], max_examples: int) -> Dict[str, Any]:
    counts: Counter[str] = Counter()
    exact_examples: List[Dict[str, Any]] = []
    substring_examples: List[Dict[str, Any]] = []
    startswith_examples: List[Dict[str, Any]] = []
    stale_examples: List[Dict[str, Any]] = []
    for row in rows:
        token = str(row["token"])
        components = [str(part) for part in safe_json(row["component_tokens_json"], [])]
        exact = target in components
        substring = target in token
        startswith = token.startswith(target) and token != target
        if exact:
            counts["exact_component_count"] += 1
            if int(row["changed"] or 0):
                counts["exact_component_changed_count"] += 1
                if len(stale_examples) < max_examples:
                    stale_examples.append(example(row, components))
            if len(exact_examples) < max_examples:
                exact_examples.append(example(row, components))
        if substring and not exact:
            counts["substring_without_exact_count"] += 1
            if len(substring_examples) < max_examples:
                substring_examples.append(example(row, components))
        if startswith and not exact:
            counts["prefix_without_exact_count"] += 1
            if len(startswith_examples) < max_examples:
                startswith_examples.append(example(row, components))
    if counts["exact_component_count"] > counts["substring_without_exact_count"]:
        boundary_status = "EXACT_COMPONENT_OWNER"
    elif counts["exact_component_count"] and counts["substring_without_exact_count"]:
        boundary_status = "MIXED_OWNER_AND_SUBSTRING_NOISE"
    elif counts["exact_component_count"]:
        boundary_status = "NARROW_EXACT_COMPONENT"
    elif counts["substring_without_exact_count"]:
        boundary_status = "SUBSTRING_ONLY_OR_SWALLOWED"
    else:
        boundary_status = "NO_MACRO_COMPONENT_EVIDENCE"
    return {
        "target": target,
        "boundary_status": boundary_status,
        **counts,
        "exact_examples": exact_examples,
        "substring_examples": substring_examples,
        "prefix_examples": startswith_examples,
        "stale_examples": stale_examples,
    }


def example(row: sqlite3.Row, components: List[str]) -> Dict[str, Any]:
    return {
        "token": row["token"],
        "original_translation": row["original_translation"],
        "audited_recomposed_translation": row["audited_recomposed_translation"],
        "changed": int(row["changed"] or 0),
        "components": components,
    }


def audit(conn: sqlite3.Connection, targets: List[str], max_examples: int) -> Dict[str, Any]:
    rows = recomposition_rows(conn)
    glossary = glossary_rows(conn, targets)
    decisions = latest_variant_decisions(conn)
    constraints = latest_constraints(conn)
    items: List[Dict[str, Any]] = []
    for target in targets:
        item = classify_target(target, rows, max_examples)
        item["glossary"] = glossary.get(target)
        item["variant_decision"] = decisions.get(target)
        item["semantic_constraint"] = constraints.get(target)
        items.append(item)
    items.sort(
        key=lambda item: (
            -int(item.get("exact_component_count") or 0),
            -int(item.get("substring_without_exact_count") or 0),
            str(item["target"]),
        )
    )
    return {
        "target_count": len(targets),
        "macro_recomposition_row_count": len(rows),
        "items": items,
        "interpretation": "Exact component ownership is stronger than textual prefix/substring evidence for boundary decisions.",
    }


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS boundary_component_audit_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            target_count INTEGER NOT NULL,
            macro_recomposition_row_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS boundary_component_audit_items (
            run_id INTEGER NOT NULL,
            rank INTEGER NOT NULL,
            target TEXT NOT NULL,
            boundary_status TEXT NOT NULL,
            exact_component_count INTEGER NOT NULL,
            exact_component_changed_count INTEGER NOT NULL,
            substring_without_exact_count INTEGER NOT NULL,
            prefix_without_exact_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, rank)
        );
        """
    )


def record(conn: sqlite3.Connection, payload: Dict[str, Any]) -> int:
    ensure_schema(conn)
    created_at = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    cur = conn.execute(
        """
        INSERT INTO boundary_component_audit_runs (
            created_at, target_count, macro_recomposition_row_count, payload_json
        ) VALUES (?, ?, ?, ?)
        """,
        (
            created_at,
            payload["target_count"],
            payload["macro_recomposition_row_count"],
            json.dumps({k: v for k, v in payload.items() if k != "items"}, ensure_ascii=True, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)
    for rank, item in enumerate(payload["items"], start=1):
        conn.execute(
            """
            INSERT INTO boundary_component_audit_items (
                run_id, rank, target, boundary_status, exact_component_count,
                exact_component_changed_count, substring_without_exact_count,
                prefix_without_exact_count, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                rank,
                item["target"],
                item["boundary_status"],
                int(item.get("exact_component_count") or 0),
                int(item.get("exact_component_changed_count") or 0),
                int(item.get("substring_without_exact_count") or 0),
                int(item.get("prefix_without_exact_count") or 0),
                json.dumps(item, ensure_ascii=True, sort_keys=True),
            ),
        )
    conn.commit()
    return run_id


def main() -> int:
    args = parse_args()
    conn = connect(args.db)
    try:
        payload = audit(conn, [str(target) for target in args.targets], args.max_examples)
        run_id = record(conn, payload) if args.record else None
    finally:
        conn.close()
    print(json.dumps({**payload, "recorded_run_id": run_id}, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
