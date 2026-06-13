#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sqlite3
from collections import Counter
from datetime import UTC, datetime
from typing import Any


DEFAULT_DB = "./data/bonelord_operational.sqlite"
WORD_RE = re.compile(r"[A-Za-z']+")
STOPWORDS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "be",
    "but",
    "by",
    "for",
    "from",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "to",
    "was",
    "were",
    "with",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Project external anchor context onto local raw windows")
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--anchor", default="sunburn")
    parser.add_argument("--source-title", default="Experimentation on Vampires (Book)")
    parser.add_argument("--raw-radius", type=int, default=70)
    parser.add_argument("--external-radius", type=int, default=18)
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


def words(text: str) -> list[str]:
    return [word.lower() for word in WORD_RE.findall(text or "")]


def content_words(text: str) -> set[str]:
    return {word for word in words(text) if len(word) > 3 and word not in STOPWORDS}


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


def anchor_tokens(rows: list[sqlite3.Row], anchor: str) -> list[str]:
    anchor_l = anchor.lower()
    tokens = [
        str(row["token"])
        for row in rows
        if str(row["translation"] or "").lower() == anchor_l
    ]
    tokens.sort(key=lambda token: (-len(token), token))
    return tokens


def greedy_segment(raw: str, rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    i = 0
    segments: list[dict[str, Any]] = []
    while i < len(raw):
        hit = None
        for row in rows:
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


def latest_book_sources(conn: sqlite3.Connection) -> dict[str, str]:
    export_row = conn.execute("SELECT MAX(__export_id) AS export_id FROM sheet__books").fetchone()
    export_id = export_row["export_id"] if export_row else None
    rows = conn.execute(
        "SELECT bookid, decodedbase FROM sheet__books WHERE __export_id = ?",
        (export_id,),
    ).fetchall()
    return {str(row["bookid"]): str(row["decodedbase"] or "") for row in rows}


def latest_best_shadow_rows(conn: sqlite3.Connection) -> tuple[int | None, list[sqlite3.Row]]:
    run_id = latest_run_id(conn, "best_shadow_book_runs")
    if run_id is None:
        return None, []
    rows = conn.execute(
        """
        SELECT bookid, best_shadow_text
        FROM best_shadow_book_translations
        WHERE run_id = ?
        ORDER BY CAST(bookid AS INTEGER)
        """,
        (run_id,),
    ).fetchall()
    return run_id, rows


def source_text(conn: sqlite3.Connection, title: str) -> tuple[str, str]:
    row = conn.execute(
        """
        SELECT source_url, text
        FROM external_corpus_sources
        WHERE title = ?
        ORDER BY source_id DESC
        LIMIT 1
        """,
        (title,),
    ).fetchone()
    if not row:
        return "", ""
    return str(row["source_url"] or ""), str(row["text"] or "")


def external_windows(text: str, anchor: str, radius: int) -> list[str]:
    tokens = words(text)
    out: list[str] = []
    for idx, token in enumerate(tokens):
        if token != anchor.lower():
            continue
        lo = max(0, idx - radius)
        hi = min(len(tokens), idx + radius + 1)
        out.append(" ".join(tokens[lo:hi]))
    return out


def classify(overlap_terms: list[str], anchor: str, local_text: str, external_text: str) -> str:
    non_anchor = [term for term in overlap_terms if term != anchor.lower()]
    if non_anchor:
        return "ANCHOR_PLUS_CONTEXT_OVERLAP"
    if anchor.lower() in overlap_terms:
        if "regenerate" in external_text and "regenerate" not in local_text:
            return "WEAK_SINGLE_ANCHOR_ONLY_EXTERNAL_CONTEXT_NOT_RECOVERED"
        return "WEAK_SINGLE_ANCHOR_ONLY"
    return "NO_MEANINGFUL_ALIGNMENT"


def build_payload(conn: sqlite3.Connection, anchor: str, title: str, raw_radius: int, external_radius: int) -> dict[str, Any]:
    gloss = glossary_rows(conn)
    anchors = anchor_tokens(gloss, anchor)
    best_run_id, best_rows = latest_best_shadow_rows(conn)
    book_sources = latest_book_sources(conn)
    source_url, ext_text = source_text(conn, title)
    ext_windows = external_windows(ext_text, anchor, external_radius)
    best_by_book = {str(row["bookid"]): str(row["best_shadow_text"] or "") for row in best_rows}
    items: list[dict[str, Any]] = []
    for bookid, raw in book_sources.items():
        for anchor_token in anchors:
            start = 0
            while True:
                idx = raw.find(anchor_token, start)
                if idx < 0:
                    break
                local_raw = raw[max(0, idx - raw_radius) : min(len(raw), idx + len(anchor_token) + raw_radius)]
                post_raw = raw[idx : min(len(raw), idx + len(anchor_token) + raw_radius)]
                segments = greedy_segment(post_raw, gloss)[:24]
                projected = " ".join(str(seg["translation"]) for seg in segments)
                local_context = best_by_book.get(bookid, "")
                local_terms = content_words(projected + " " + local_context)
                best_overlap: list[str] = []
                best_ext = ""
                best_score = 0.0
                for ext_window in ext_windows:
                    ext_terms = content_words(ext_window)
                    overlap = sorted(local_terms & ext_terms)
                    score = round(len(overlap) / max(1, len(local_terms | ext_terms)) + 0.15 * len(overlap), 4)
                    if score > best_score:
                        best_score = score
                        best_overlap = overlap
                        best_ext = ext_window
                status = classify(best_overlap, anchor, projected.lower(), best_ext.lower())
                items.append(
                    {
                        "bookid": bookid,
                        "anchor_token": anchor_token,
                        "raw_window": local_raw,
                        "post_anchor_raw": post_raw,
                        "projected_translation": projected,
                        "segments": segments,
                        "external_context": best_ext,
                        "overlap_terms": best_overlap,
                        "score": best_score,
                        "projection_status": status,
                    }
                )
                start = idx + len(anchor_token)
    items.sort(key=lambda item: (-float(item["score"]), int(item["bookid"]), item["anchor_token"]))
    status_counts = Counter(str(item["projection_status"]) for item in items)
    return {
        "best_shadow_run_id": best_run_id,
        "source_title": title,
        "source_url": source_url,
        "anchor": anchor,
        "anchor_tokens": anchors,
        "item_count": len(items),
        "status_counts": dict(status_counts),
        "items": items,
        "interpretation": (
            "Projection tests whether an external anchor recovers surrounding context. Single-anchor-only matches "
            "are useful as weak anchors but are not translation evidence for surrounding words."
        ),
    }


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS external_anchor_projection_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            best_shadow_run_id INTEGER,
            source_title TEXT NOT NULL,
            source_url TEXT NOT NULL,
            anchor TEXT NOT NULL,
            item_count INTEGER NOT NULL,
            status_counts_json TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS external_anchor_projection_items (
            run_id INTEGER NOT NULL,
            rank INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            anchor_token TEXT NOT NULL,
            score REAL NOT NULL,
            projection_status TEXT NOT NULL,
            raw_window TEXT NOT NULL,
            projected_translation TEXT NOT NULL,
            external_context TEXT NOT NULL,
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
        INSERT INTO external_anchor_projection_runs (
            created_at, best_shadow_run_id, source_title, source_url, anchor,
            item_count, status_counts_json, payload_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            created_at,
            payload["best_shadow_run_id"],
            payload["source_title"],
            payload["source_url"],
            payload["anchor"],
            payload["item_count"],
            json.dumps(payload["status_counts"], ensure_ascii=True, sort_keys=True),
            json.dumps({k: v for k, v in payload.items() if k != "items"}, ensure_ascii=True, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)
    for rank, item in enumerate(payload["items"], start=1):
        conn.execute(
            """
            INSERT INTO external_anchor_projection_items (
                run_id, rank, bookid, anchor_token, score, projection_status,
                raw_window, projected_translation, external_context, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                rank,
                item["bookid"],
                item["anchor_token"],
                item["score"],
                item["projection_status"],
                item["raw_window"],
                item["projected_translation"],
                item["external_context"],
                json.dumps(item, ensure_ascii=True, sort_keys=True),
            ),
        )
    conn.commit()
    return run_id


def main() -> int:
    args = parse_args()
    conn = connect(args.db)
    try:
        payload = build_payload(conn, args.anchor, args.source_title, args.raw_radius, args.external_radius)
        run_id = record(conn, payload) if args.record else None
    finally:
        conn.close()
    print(
        json.dumps(
            {
                "recorded_run_id": run_id,
                "best_shadow_run_id": payload["best_shadow_run_id"],
                "source_title": payload["source_title"],
                "anchor": payload["anchor"],
                "anchor_tokens": payload["anchor_tokens"],
                "item_count": payload["item_count"],
                "status_counts": payload["status_counts"],
                "top": [
                    {
                        "bookid": item["bookid"],
                        "score": item["score"],
                        "status": item["projection_status"],
                        "projected_translation": item["projected_translation"],
                        "overlap_terms": item["overlap_terms"],
                    }
                    for item in payload["items"][:12]
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
