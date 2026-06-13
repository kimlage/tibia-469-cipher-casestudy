#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sqlite3
from collections import Counter, defaultdict
from datetime import UTC, datetime
from typing import Any


DEFAULT_DB = "./data/bonelord_operational.sqlite"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Cluster repeated raw formula windows around target tokens/patterns")
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--targets", nargs="+", default=["EBTII", "NSTAEFIEIEF"])
    parser.add_argument("--radius", type=int, default=48)
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


def glossary_rows(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    export_row = conn.execute("SELECT MAX(__export_id) AS export_id FROM sheet__glossary").fetchone()
    export_id = export_row["export_id"] if export_row else None
    return conn.execute(
        """
        SELECT token, translation, tokentype, confidence, evidenceclass_v127, notes
        FROM sheet__glossary
        WHERE __export_id = ?
          AND token IS NOT NULL
          AND token != ''
        ORDER BY length(token) DESC, token
        """,
        (export_id,),
    ).fetchall()


def source_books(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    export_row = conn.execute("SELECT MAX(__export_id) AS export_id FROM sheet__books").fetchone()
    export_id = export_row["export_id"] if export_row else None
    return conn.execute(
        """
        SELECT bookid, decodedbase, translation_contextenglish_auto
        FROM sheet__books
        WHERE __export_id = ?
        ORDER BY CAST(bookid AS INTEGER)
        """,
        (export_id,),
    ).fetchall()


def best_shadow_by_book(conn: sqlite3.Connection) -> tuple[int | None, dict[str, str]]:
    run_id = latest_run_id(conn, "best_shadow_book_runs")
    if run_id is None:
        return None, {}
    rows = conn.execute(
        "SELECT bookid, best_shadow_text FROM best_shadow_book_translations WHERE run_id = ?",
        (run_id,),
    ).fetchall()
    return run_id, {str(row["bookid"]): str(row["best_shadow_text"] or "") for row in rows}


def safe_json(raw: object, default: Any) -> Any:
    if raw in (None, ""):
        return default
    try:
        return json.loads(str(raw))
    except json.JSONDecodeError:
        return default


def macro_owners(conn: sqlite3.Connection, target: str) -> list[dict[str, Any]]:
    run_id = latest_run_id(conn, "macro_recomposition_audit_runs")
    if run_id is None:
        return []
    rows = conn.execute(
        """
        SELECT token, original_translation, audited_recomposed_translation, component_tokens_json, changed
        FROM macro_recomposition_audit
        WHERE run_id = ?
          AND (token LIKE ? OR component_tokens_json LIKE ?)
        ORDER BY length(token), token
        LIMIT 80
        """,
        (run_id, f"%{target}%", f"%{target}%"),
    ).fetchall()
    return [
        {
            "token": str(row["token"]),
            "original_translation": str(row["original_translation"] or ""),
            "audited_recomposed_translation": str(row["audited_recomposed_translation"] or ""),
            "components": safe_json(row["component_tokens_json"], []),
            "changed": int(row["changed"] or 0),
        }
        for row in rows
    ]


def greedy_segment(raw: str, gloss: list[sqlite3.Row], max_segments: int = 28) -> list[dict[str, Any]]:
    i = 0
    segments: list[dict[str, Any]] = []
    while i < len(raw) and len(segments) < max_segments:
        hit = None
        for row in gloss:
            token = str(row["token"])
            if raw.startswith(token, i):
                hit = row
                break
        if hit is None:
            segments.append({"token": raw[i], "translation": "<RAW>", "evidence": "", "confidence": ""})
            i += 1
            continue
        segments.append(
            {
                "token": str(hit["token"]),
                "translation": str(hit["translation"] or ""),
                "evidence": str(hit["evidenceclass_v127"] or ""),
                "confidence": str(hit["confidence"] or ""),
            }
        )
        i += len(str(hit["token"]))
    return segments


def semantic_flags(text: str) -> list[str]:
    lowered = text.lower()
    flags: list[str] = []
    if "<unk:" in lowered:
        flags.append("HAS_UNKNOWN")
    if " a a " in f" {lowered} ":
        flags.append("REPEATED_ARTICLE")
    if " i eye of" in f" {lowered} " or "eye of i" in f" {lowered} ":
        flags.append("MICROTOKEN_DRIFT")
    if "enable never sunburn" in lowered or "enable even sunburn" in lowered:
        flags.append("SUNBURN_FORMULA")
    if "infinite fasten infinity" in lowered:
        flags.append("INFINITE_FORMULA")
    return flags


def build_payload(conn: sqlite3.Connection, targets: list[str], radius: int) -> dict[str, Any]:
    gloss = glossary_rows(conn)
    books = source_books(conn)
    best_run_id, shadow = best_shadow_by_book(conn)
    items: list[dict[str, Any]] = []
    for target in targets:
        windows: list[dict[str, Any]] = []
        cluster_counter: Counter[str] = Counter()
        segment_counter: Counter[str] = Counter()
        for book in books:
            bookid = str(book["bookid"])
            raw = str(book["decodedbase"] or "")
            start = 0
            while True:
                idx = raw.find(target, start)
                if idx < 0:
                    break
                raw_window = raw[max(0, idx - radius) : min(len(raw), idx + len(target) + radius)]
                target_forward = raw[idx : min(len(raw), idx + len(target) + radius)]
                segments = greedy_segment(target_forward, gloss)
                projection = " ".join(str(seg["translation"]) for seg in segments)
                cluster_key = raw[idx : min(len(raw), idx + len(target) + 28)]
                cluster_counter[cluster_key] += 1
                for seg in segments[:10]:
                    segment_counter[str(seg["token"])] += 1
                windows.append(
                    {
                        "bookid": bookid,
                        "raw_window": raw_window,
                        "target_forward_raw": target_forward,
                        "projection": projection,
                        "segments": segments,
                        "best_shadow_context": shadow.get(bookid, ""),
                        "semantic_flags": semantic_flags(projection + " " + shadow.get(bookid, "")),
                    }
                )
                start = idx + len(target)
        flags = Counter(flag for window in windows for flag in window["semantic_flags"])
        status = "DEAD_NO_OCCURRENCES"
        if windows:
            status = "OPEN_REPEATED_FORMULA" if len(windows) >= 3 else "OPEN_LOW_SUPPORT"
        if flags.get("MICROTOKEN_DRIFT", 0) >= 3:
            status = "OPEN_MICROTOKEN_BOUNDARY_DRIFT"
        if flags.get("SUNBURN_FORMULA", 0) >= 3:
            status = "OPEN_SUNBURN_FORMULA_DRIFT"
        item = {
            "target": target,
            "hit_count": len(windows),
            "book_count": len({window["bookid"] for window in windows}),
            "status": status,
            "top_raw_clusters": cluster_counter.most_common(12),
            "top_segment_tokens": segment_counter.most_common(16),
            "semantic_flag_counts": dict(flags),
            "macro_owners": macro_owners(conn, target),
            "windows": windows[:20],
        }
        if status == "OPEN_SUNBURN_FORMULA_DRIFT":
            item["next_action"] = "Audit phrase/fusion around target and adjacent sunburn macro; do not promote unknown from external single-anchor match."
        elif status == "OPEN_MICROTOKEN_BOUNDARY_DRIFT":
            item["next_action"] = "Audit microtoken components as formula-local markers; avoid global demotion."
        elif status == "OPEN_REPEATED_FORMULA":
            item["next_action"] = "Compare repeated raw clusters against macro owners and semantic anomaly queue."
        elif status == "OPEN_LOW_SUPPORT":
            item["next_action"] = "Keep as low-support frontier unless linked to a higher-priority formula."
        else:
            item["next_action"] = "No local work."
        items.append(item)
    return {
        "best_shadow_run_id": best_run_id,
        "targets": targets,
        "radius": radius,
        "item_count": len(items),
        "items": items,
        "interpretation": "Formula-family clusters expose whether a frontier is a repeated structural problem or a one-off lexical gap.",
    }


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS formula_family_cluster_audit_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            best_shadow_run_id INTEGER,
            targets_json TEXT NOT NULL,
            item_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS formula_family_cluster_audit_items (
            run_id INTEGER NOT NULL,
            rank INTEGER NOT NULL,
            target TEXT NOT NULL,
            hit_count INTEGER NOT NULL,
            book_count INTEGER NOT NULL,
            status TEXT NOT NULL,
            semantic_flag_counts_json TEXT NOT NULL,
            next_action TEXT NOT NULL,
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
        INSERT INTO formula_family_cluster_audit_runs (
            created_at, best_shadow_run_id, targets_json, item_count, payload_json
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (
            created_at,
            payload["best_shadow_run_id"],
            json.dumps(payload["targets"], ensure_ascii=True),
            payload["item_count"],
            json.dumps({k: v for k, v in payload.items() if k != "items"}, ensure_ascii=True, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)
    for rank, item in enumerate(payload["items"], start=1):
        conn.execute(
            """
            INSERT INTO formula_family_cluster_audit_items (
                run_id, rank, target, hit_count, book_count, status,
                semantic_flag_counts_json, next_action, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                rank,
                item["target"],
                item["hit_count"],
                item["book_count"],
                item["status"],
                json.dumps(item["semantic_flag_counts"], ensure_ascii=True, sort_keys=True),
                item["next_action"],
                json.dumps(item, ensure_ascii=True, sort_keys=True),
            ),
        )
    conn.commit()
    return run_id


def main() -> int:
    args = parse_args()
    conn = connect(args.db)
    try:
        payload = build_payload(conn, args.targets, args.radius)
        run_id = record(conn, payload) if args.record else None
    finally:
        conn.close()
    print(
        json.dumps(
            {
                "recorded_run_id": run_id,
                "best_shadow_run_id": payload["best_shadow_run_id"],
                "items": [
                    {
                        "target": item["target"],
                        "hits": item["hit_count"],
                        "books": item["book_count"],
                        "status": item["status"],
                        "flags": item["semantic_flag_counts"],
                        "top_raw_clusters": item["top_raw_clusters"][:4],
                        "next_action": item["next_action"],
                    }
                    for item in payload["items"]
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
