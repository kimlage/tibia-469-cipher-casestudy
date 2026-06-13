#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sqlite3
from collections import Counter
from datetime import UTC, datetime
from typing import Any, Dict, List

from sqlite_snapshot_ref import DEFAULT_SNAPSHOT_NAME, resolve_export_id


DEFAULT_DB = "./data/bonelord_operational.sqlite"

STOP_PHRASES = {
    "a",
    "i",
    "of",
    "to",
    "in",
    "no",
    "be",
    "we",
    "me",
    "you",
    "the",
    "and",
    "is",
    "as",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Materialize conservative safe book translations from SQLite gates")
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--export-id", type=int, default=None)
    parser.add_argument("--snapshot-name", default=DEFAULT_SNAPSHOT_NAME)
    parser.add_argument("--record", action="store_true")
    parser.add_argument("--max-output-books", type=int, default=20)
    return parser.parse_args()


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (table,)).fetchone()
    return row is not None


def latest_gate_run_id(conn: sqlite3.Connection) -> int | None:
    if not table_exists(conn, "translation_stability_gate_runs"):
        return None
    row = conn.execute("SELECT run_id FROM translation_stability_gate_runs ORDER BY run_id DESC LIMIT 1").fetchone()
    return int(row["run_id"]) if row else None


def safe_json(raw: object, default: Any) -> Any:
    if raw in (None, ""):
        return default
    try:
        return json.loads(str(raw))
    except json.JSONDecodeError:
        return default


def phrase_words(text: str) -> List[str]:
    return re.findall(r"[A-Za-z<>*']+", text)


def normalize_phrase(text: object) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip())


def replacement_candidate(text: object) -> str | None:
    phrase = normalize_phrase(text)
    if not phrase:
        return None
    if len(phrase) > 80:
        return None
    lower = phrase.lower()
    words = [word.lower() for word in phrase_words(phrase)]
    if len(words) > 8:
        return None
    if lower in STOP_PHRASES:
        return None
    if len(phrase) < 7 and not any(marker in phrase for marker in ("<UNK>", "<", "*")):
        return None
    if len(words) == 1 and words[0] in STOP_PHRASES:
        return None
    return phrase


def load_replacements(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    gate_run_id = latest_gate_run_id(conn)
    if gate_run_id is None:
        return []
    rows = conn.execute(
        """
        SELECT token, item_kind, family_token, decision, risk_score, reasons_json,
               current_translation, audited_translation, recomposed_translation
        FROM translation_stability_gate_items
        WHERE run_id = ?
          AND (
            (decision = 'BLOCKED' AND risk_score >= 7)
            OR (
              item_kind = 'MACRO'
              AND risk_score >= 5
              AND reasons_json LIKE '%STALE_RECOMPOSED_MACRO%'
            )
          )
        """,
        (gate_run_id,),
    ).fetchall()
    seen: set[tuple[str, str, str]] = set()
    replacements: List[Dict[str, Any]] = []
    for row in rows:
        for field in ("current_translation", "audited_translation", "recomposed_translation"):
            phrase = replacement_candidate(row[field])
            if phrase is None:
                continue
            key = (phrase.lower(), str(row["decision"]), str(row["token"]))
            if key in seen:
                continue
            seen.add(key)
            replacements.append(
                {
                    "phrase": phrase,
                    "token": str(row["token"]),
                    "item_kind": str(row["item_kind"]),
                    "family_token": row["family_token"],
                    "decision": str(row["decision"]),
                    "risk_score": int(row["risk_score"] or 0),
                    "reasons": safe_json(row["reasons_json"], []),
                    "gate_run_id": gate_run_id,
                }
            )
    replacements.sort(key=lambda item: (-len(item["phrase"]), -int(item["risk_score"]), item["phrase"]))
    return replacements


def marker_for(item: Dict[str, Any]) -> str:
    annotated = item.get("annotated_safe_phrase")
    if annotated:
        return str(annotated)
    prefix = "BLOCKED" if item["decision"] == "BLOCKED" else "CAUTION"
    return f"<{prefix}:{item['token']}>"


def apply_replacements(text: str, replacements: List[Dict[str, Any]]) -> tuple[str, List[Dict[str, Any]]]:
    output = str(text or "")
    hits: List[Dict[str, Any]] = []
    for item in replacements:
        if item["decision"] == "CAUTION" and not item.get("annotated_safe_phrase"):
            continue
        phrase = item["phrase"]
        escaped = re.escape(phrase)
        pattern = re.compile(rf"(?<![A-Za-z]){escaped}(?![A-Za-z])", re.IGNORECASE)
        count = len(pattern.findall(output))
        if count == 0:
            continue
        replacement = marker_for(item)
        output = pattern.sub(replacement, output)
        hit = {key: item[key] for key in ("phrase", "token", "item_kind", "family_token", "decision", "risk_score")}
        hit["count"] = count
        hit["replacement"] = replacement
        hit["reasons"] = item["reasons"]
        if "display_mode" in item:
            hit["display_mode"] = item["display_mode"]
        hits.append(hit)
    return output, hits


def materialize(conn: sqlite3.Connection, export_id: int, replacements: List[Dict[str, Any]]) -> Dict[str, Any]:
    active_replacement_count = sum(
        1 for item in replacements if item["decision"] != "CAUTION" or item.get("annotated_safe_phrase")
    )
    rows = conn.execute(
        """
        SELECT bookid, digits, translation_contextenglish_auto, translation_english_auto,
               translation_strictplus_v108, translation_macrocompressed_auto
        FROM sheet__books
        WHERE __export_id = ?
        ORDER BY CAST(bookid AS INTEGER)
        """,
        (export_id,),
    ).fetchall()
    items: List[Dict[str, Any]] = []
    totals: Counter[str] = Counter()
    for row in rows:
        original = str(row["translation_contextenglish_auto"] or row["translation_english_auto"] or row["translation_strictplus_v108"] or "")
        safe_text, hits = apply_replacements(original, replacements)
        decision_counts = Counter(
            hit["decision"]
            for hit in hits
            for _ in range(int(hit["count"]))
            if hit.get("display_mode") != "AUDITED_RECOMPOSED"
        )
        display_recomposed_count = sum(
            int(hit["count"]) for hit in hits if hit.get("display_mode") == "AUDITED_RECOMPOSED"
        )
        blocked = int(decision_counts["BLOCKED"])
        caution = int(decision_counts["CAUTION"])
        risk_score = min(100, blocked * 7 + caution * 3)
        item = {
            "export_id": export_id,
            "bookid": str(row["bookid"]),
            "source_text": original,
            "safe_text": safe_text,
            "strictplus_text": row["translation_strictplus_v108"],
            "macrocompressed_text": row["translation_macrocompressed_auto"],
            "blocked_hit_count": blocked,
            "caution_hit_count": caution,
            "display_recomposed_hit_count": display_recomposed_count,
            "risk_score": risk_score,
            "hits": hits,
        }
        totals["book_count"] += 1
        if blocked:
            totals["books_with_blocked"] += 1
        if caution:
            totals["books_with_caution"] += 1
        totals["blocked_hit_count"] += blocked
        totals["caution_hit_count"] += caution
        totals["display_recomposed_hit_count"] += display_recomposed_count
        items.append(item)
    clean_books = sum(1 for item in items if not item["blocked_hit_count"] and not item["caution_hit_count"])
    safe_read_pct = round(100.0 * clean_books / totals["book_count"], 2) if totals["book_count"] else 0.0
    return {
        "summary": {
            "export_id": export_id,
            "book_count": totals["book_count"],
            "books_with_blocked": totals["books_with_blocked"],
            "books_with_caution": totals["books_with_caution"],
            "blocked_hit_count": totals["blocked_hit_count"],
            "caution_hit_count": totals["caution_hit_count"],
            "display_recomposed_hit_count": totals["display_recomposed_hit_count"],
            "safe_book_clean_pct": safe_read_pct,
            "replacement_count": active_replacement_count,
            "candidate_replacement_count": len(replacements),
            "interpretation": "Safe text masks high-risk stale macro phrases; it is for audit/readability, not a decode-core mutation.",
        },
        "items": items,
    }


def unknown_annotations(conn: sqlite3.Connection) -> Dict[str, str]:
    if not table_exists(conn, "unknown_base_decision_runs") or not table_exists(conn, "unknown_base_decisions"):
        return {}
    run_id = latest_gate_run_id_for_table(conn, "unknown_base_decision_runs")
    if run_id is None:
        return {}
    rows = conn.execute(
        """
        SELECT token
        FROM unknown_base_decisions
        WHERE run_id = ?
          AND decision = 'KEEP_UNKNOWN'
        """,
        (run_id,),
    ).fetchall()
    return {str(row["token"]): f"<UNK:{row['token']}>" for row in rows if row["token"] is not None}


def latest_gate_run_id_for_table(conn: sqlite3.Connection, table: str) -> int | None:
    if not table_exists(conn, table):
        return None
    row = conn.execute(f"SELECT run_id FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    return int(row["run_id"]) if row else None


def annotate_unknown_phrase(conn: sqlite3.Connection, replacements: List[Dict[str, Any]]) -> None:
    annotations = unknown_annotations(conn)
    if not annotations:
        return
    recomposition_run_id = latest_gate_run_id_for_table(conn, "macro_recomposition_audit_runs")
    if recomposition_run_id is None or not table_exists(conn, "macro_recomposition_audit"):
        return
    rows = conn.execute(
        """
        SELECT token, audited_recomposed_translation, component_tokens_json
        FROM macro_recomposition_audit
        WHERE run_id = ?
        """,
        (recomposition_run_id,),
    ).fetchall()
    by_token = {str(row["token"]): row for row in rows if row["token"] is not None}
    for item in replacements:
        row = by_token.get(str(item["token"]))
        if not row:
            continue
        components = safe_json(row["component_tokens_json"], [])
        text = str(row["audited_recomposed_translation"] or item["phrase"])
        for component in components:
            component = str(component)
            if component in annotations:
                text = text.replace("<UNK>", annotations[component], 1)
        if "<UNK:" in text:
            item["annotated_safe_phrase"] = text
            item["display_mode"] = "UNKNOWN_COMPONENT_ANNOTATED"


def annotate_recomposed_phrase(conn: sqlite3.Connection, replacements: List[Dict[str, Any]]) -> None:
    recomposition_run_id = latest_gate_run_id_for_table(conn, "macro_recomposition_audit_runs")
    if recomposition_run_id is None or not table_exists(conn, "macro_recomposition_audit"):
        return
    rows = conn.execute(
        """
        SELECT token, audited_recomposed_translation, missing_components_json, changed
        FROM macro_recomposition_audit
        WHERE run_id = ?
        """,
        (recomposition_run_id,),
    ).fetchall()
    by_token = {str(row["token"]): row for row in rows if row["token"] is not None}
    for item in replacements:
        row = by_token.get(str(item["token"]))
        if not row or int(row["changed"] or 0) != 1:
            continue
        if safe_json(row["missing_components_json"], []):
            continue
        candidate = replacement_candidate(row["audited_recomposed_translation"])
        if candidate is None:
            continue
        if "<MISSING:" in candidate:
            continue
        if candidate.lower() == normalize_phrase(item["phrase"]).lower():
            continue
        item["annotated_safe_phrase"] = candidate
        item["display_mode"] = "AUDITED_RECOMPOSED"


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS safe_book_translation_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            export_id INTEGER NOT NULL,
            book_count INTEGER NOT NULL,
            books_with_blocked INTEGER NOT NULL,
            books_with_caution INTEGER NOT NULL,
            blocked_hit_count INTEGER NOT NULL,
            caution_hit_count INTEGER NOT NULL,
            safe_book_clean_pct REAL NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS safe_book_translations (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            source_text TEXT,
            safe_text TEXT,
            strictplus_text TEXT,
            macrocompressed_text TEXT,
            blocked_hit_count INTEGER NOT NULL,
            caution_hit_count INTEGER NOT NULL,
            risk_score INTEGER NOT NULL,
            hits_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        );
        """
    )


def record(conn: sqlite3.Connection, payload: Dict[str, Any]) -> int:
    ensure_schema(conn)
    summary = payload["summary"]
    created_at = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    cur = conn.execute(
        """
        INSERT INTO safe_book_translation_runs (
            created_at, export_id, book_count, books_with_blocked, books_with_caution,
            blocked_hit_count, caution_hit_count, safe_book_clean_pct, payload_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            created_at,
            summary["export_id"],
            summary["book_count"],
            summary["books_with_blocked"],
            summary["books_with_caution"],
            summary["blocked_hit_count"],
            summary["caution_hit_count"],
            summary["safe_book_clean_pct"],
            json.dumps(summary, ensure_ascii=True, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)
    for item in payload["items"]:
        conn.execute(
            """
            INSERT INTO safe_book_translations (
                run_id, bookid, source_text, safe_text, strictplus_text, macrocompressed_text,
                blocked_hit_count, caution_hit_count, risk_score, hits_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                item["bookid"],
                item["source_text"],
                item["safe_text"],
                item["strictplus_text"],
                item["macrocompressed_text"],
                item["blocked_hit_count"],
                item["caution_hit_count"],
                item["risk_score"],
                json.dumps(item["hits"], ensure_ascii=True, sort_keys=True),
            ),
        )
    conn.commit()
    return run_id


def main() -> int:
    args = parse_args()
    conn = connect(args.db)
    try:
        export_id = resolve_export_id(conn, export_id=args.export_id, snapshot_name=args.snapshot_name)
        replacements = load_replacements(conn)
        annotate_recomposed_phrase(conn, replacements)
        annotate_unknown_phrase(conn, replacements)
        payload = materialize(conn, export_id, replacements)
        run_id = record(conn, payload) if args.record else None
    finally:
        conn.close()
    sample = sorted(payload["items"], key=lambda item: (-item["risk_score"], int(item["bookid"])))[: args.max_output_books]
    print(
        json.dumps(
            {
                **payload["summary"],
                "recorded_run_id": run_id,
                "sample_books": sample,
            },
            ensure_ascii=True,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
