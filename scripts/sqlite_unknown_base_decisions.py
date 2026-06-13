#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter
from datetime import UTC, datetime
from typing import Any, Dict, List

from sqlite_snapshot_ref import DEFAULT_SNAPSHOT_NAME, resolve_export_id


DEFAULT_DB = "./data/bonelord_operational.sqlite"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Materialize decisions for unknown base tokens")
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--export-id", type=int, default=None)
    parser.add_argument("--snapshot-name", default=DEFAULT_SNAPSHOT_NAME)
    parser.add_argument("--record", action="store_true")
    parser.add_argument("--max-output-items", type=int, default=40)
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


def glossary_unknowns(conn: sqlite3.Connection, export_id: int) -> List[Dict[str, Any]]:
    if not table_exists(conn, "sheet__glossary"):
        return []
    rows = conn.execute(
        """
        SELECT token, translation, tokentype, confidence, evidenceclass_v127, evidencescore_v127,
               totalocc, bookcount, notes
        FROM sheet__glossary
        WHERE __export_id = ?
          AND translation LIKE '%<UNK>%'
        ORDER BY CAST(bookcount AS INTEGER) DESC, token
        """,
        (export_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def codeword_for(conn: sqlite3.Connection, export_id: int, token: str) -> List[Dict[str, Any]]:
    if not table_exists(conn, "sheet__codewordmap_auto"):
        return []
    rows = conn.execute(
        """
        SELECT code, topword, topwordcount, totalcount, topshare, baselineword, candidatewords
        FROM sheet__codewordmap_auto
        WHERE __export_id = ?
          AND token = ?
        ORDER BY CAST(totalcount AS INTEGER) DESC
        """,
        (export_id, token),
    ).fetchall()
    return [dict(row) for row in rows]


def promotion_summary(conn: sqlite3.Connection, export_id: int, token: str, old_word_hint: str | None) -> Dict[str, Any]:
    if not table_exists(conn, "sheet__candidatepromotions"):
        return {"count": 0, "decisions": {}, "recent": []}
    pattern_token = f"%{token}%"
    params: tuple[Any, ...]
    if old_word_hint:
        params = (export_id, pattern_token, f"%{old_word_hint}%")
        where = "token LIKE ? OR translation LIKE ?"
    else:
        params = (export_id, pattern_token)
        where = "token LIKE ?"
    rows = conn.execute(
        f"""
        SELECT iteration, token, translation, evidenceclass, totalocc, decision, reason
        FROM sheet__candidatepromotions
        WHERE __export_id = ?
          AND ({where})
        ORDER BY CAST(iteration AS INTEGER) DESC
        LIMIT 40
        """,
        params,
    ).fetchall()
    decisions = Counter(str(row["decision"] or "") for row in rows)
    return {
        "count": len(rows),
        "decisions": dict(decisions),
        "recent": [dict(row) for row in rows[:12]],
    }


def external_support(conn: sqlite3.Connection, export_id: int, token: str, old_word_hint: str | None) -> Dict[str, Any]:
    if not table_exists(conn, "sheet__externalrefs_v115"):
        return {"count": 0, "refs": []}
    if not old_word_hint:
        return {"count": 0, "refs": []}
    rows = conn.execute(
        """
        SELECT refname, digitssanitized, dp_strictplus, codestreamdp_concat_readable_v120,
               inbooks_count, inbooks_bookids
        FROM sheet__externalrefs_v115
        WHERE __export_id = ?
          AND (
            dp_strictplus LIKE ?
            OR codestreamdp_concat_readable_v120 LIKE ?
          )
        """,
        (export_id, f"%{old_word_hint}%", f"%{old_word_hint}%"),
    ).fetchall()
    return {"count": len(rows), "refs": [dict(row) for row in rows]}


def safe_book_impact(conn: sqlite3.Connection, token: str) -> Dict[str, Any]:
    run_id = latest_run_id(conn, "safe_book_translation_runs")
    if run_id is None or not table_exists(conn, "safe_book_translations"):
        return {"book_count": 0, "hit_count": 0, "books": []}
    rows = conn.execute(
        """
        SELECT bookid, hits_json
        FROM safe_book_translations
        WHERE run_id = ?
          AND hits_json LIKE ?
        """,
        (run_id, f"%{token}%"),
    ).fetchall()
    hit_count = 0
    books: List[str] = []
    for row in rows:
        for hit in safe_json(row["hits_json"], []):
            if hit.get("token") == token or token in str(hit.get("phrase") or ""):
                hit_count += int(hit.get("count") or 0)
                books.append(str(row["bookid"]))
    return {
        "safe_book_run_id": run_id,
        "book_count": len(set(books)),
        "hit_count": hit_count,
        "books": sorted(set(books), key=lambda value: int(value) if value.isdigit() else value),
    }


def infer_old_hint(row: Dict[str, Any]) -> str | None:
    notes = str(row.get("notes") or "").lower()
    if "tumtum" in notes:
        return "tumtum"
    if "hidy" in notes:
        return "hidy"
    return None


def decide(item: Dict[str, Any]) -> Dict[str, Any]:
    old_hint = item["old_word_hint"]
    codewords = item["codeword_map"]
    external = item["external_support"]
    promotions = item["promotion_summary"]
    evidence = str(item["glossary"].get("evidenceclass_v127") or "")
    if old_hint and evidence != "HARD_EXTERNAL":
        decision = "KEEP_UNKNOWN"
        confidence = "HIGH"
        if external["count"]:
            reason = (
                f"{item['token']} keeps unknown: old hint {old_hint!r} appears only in decoded/model output "
                "for external refs, not as independent source translation."
            )
        else:
            reason = f"{item['token']} has no external support for old hint {old_hint!r}; current evidence keeps it unknown."
    elif codewords and all(str(row.get("topword")).lower() in {"<unk>", "<unknown>"} for row in codewords):
        decision = "KEEP_UNKNOWN"
        confidence = "HIGH"
        reason = "Codeword map unanimously resolves this token as unknown."
    else:
        decision = "MANUAL_REVIEW"
        confidence = "LOW"
        reason = "Insufficient evidence for either resolution or permanent unknown."
    if promotions["decisions"].get("PROMOTE", 0) and decision == "KEEP_UNKNOWN":
        reason += " Historical macro promotions are ignored because they are stale display/composition, not base resolution."
    return {"decision": decision, "confidence": confidence, "reason": reason}


def compute(conn: sqlite3.Connection, export_id: int) -> Dict[str, Any]:
    items: List[Dict[str, Any]] = []
    for row in glossary_unknowns(conn, export_id):
        token = str(row["token"])
        old_hint = infer_old_hint(row)
        item = {
            "token": token,
            "old_word_hint": old_hint,
            "glossary": row,
            "codeword_map": codeword_for(conn, export_id, token),
            "promotion_summary": promotion_summary(conn, export_id, token, old_hint),
            "external_support": external_support(conn, export_id, token, old_hint),
            "safe_book_impact": safe_book_impact(conn, token),
        }
        item["decision_payload"] = decide(item)
        items.append(item)
    decision_counts = Counter(item["decision_payload"]["decision"] for item in items)
    return {
        "export_id": export_id,
        "unknown_count": len(items),
        "decision_counts": dict(decision_counts),
        "items": items,
        "interpretation": "Unknown bases remain unknown unless external or hard structural evidence resolves them; stale fluent macros are not evidence.",
    }


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS unknown_base_decision_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            export_id INTEGER NOT NULL,
            unknown_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS unknown_base_decisions (
            run_id INTEGER NOT NULL,
            token TEXT NOT NULL,
            decision TEXT NOT NULL,
            confidence TEXT NOT NULL,
            old_word_hint TEXT,
            book_count INTEGER NOT NULL,
            hit_count INTEGER NOT NULL,
            reason TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, token)
        );
        """
    )


def record(conn: sqlite3.Connection, payload: Dict[str, Any]) -> int:
    ensure_schema(conn)
    created_at = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    cur = conn.execute(
        """
        INSERT INTO unknown_base_decision_runs (created_at, export_id, unknown_count, payload_json)
        VALUES (?, ?, ?, ?)
        """,
        (
            created_at,
            payload["export_id"],
            payload["unknown_count"],
            json.dumps({k: v for k, v in payload.items() if k != "items"}, ensure_ascii=True, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)
    for item in payload["items"]:
        decision = item["decision_payload"]
        impact = item["safe_book_impact"]
        conn.execute(
            """
            INSERT INTO unknown_base_decisions (
                run_id, token, decision, confidence, old_word_hint, book_count, hit_count,
                reason, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                item["token"],
                decision["decision"],
                decision["confidence"],
                item["old_word_hint"],
                int(impact["book_count"]),
                int(impact["hit_count"]),
                decision["reason"],
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
        payload = compute(conn, export_id)
        run_id = record(conn, payload) if args.record else None
    finally:
        conn.close()
    ranked = sorted(
        payload["items"],
        key=lambda item: (-int(item["safe_book_impact"]["hit_count"]), -int(item["glossary"].get("bookcount") or 0), item["token"]),
    )
    ranked = ranked[: args.max_output_items]
    print(
        json.dumps(
            {
                "export_id": payload["export_id"],
                "recorded_run_id": run_id,
                "unknown_count": payload["unknown_count"],
                "decision_counts": payload["decision_counts"],
                "items": ranked,
                "interpretation": payload["interpretation"],
            },
            ensure_ascii=True,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
