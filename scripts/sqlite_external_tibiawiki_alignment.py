#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import urllib.parse
import urllib.request
from collections import Counter
from datetime import UTC, datetime
from typing import Any

from bs4 import BeautifulSoup


DEFAULT_DB = "./data/bonelord_operational.sqlite"
API_URL = "https://tibia.fandom.com/api.php"
SEED_PAGES = {
    "Experimentation on Vampires (Book)": "https://tibia.fandom.com/wiki/Experimentation_on_Vampires_%28Book%29",
}
WORD_RE = re.compile(r"[A-Za-z']+")
STOPWORDS = {
    "a",
    "about",
    "an",
    "and",
    "as",
    "at",
    "be",
    "but",
    "by",
    "for",
    "from",
    "had",
    "has",
    "have",
    "in",
    "into",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "their",
    "them",
    "to",
    "was",
    "were",
    "with",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest selected TibiaWiki book text and align against best-shadow books")
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--record", action="store_true")
    parser.add_argument("--context-words", type=int, default=12)
    parser.add_argument("--category", default="Category:Books in Thais Jail Library")
    parser.add_argument("--max-pages", type=int, default=40)
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


def fetch_page_html(title: str) -> str:
    query = urllib.parse.urlencode({"action": "parse", "page": title, "prop": "text", "format": "json"})
    req = urllib.request.Request(
        f"{API_URL}?{query}",
        headers={"User-Agent": "469-sargam-local-alignment/1.0"},
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return str(payload["parse"]["text"]["*"])


def fetch_category_pages(category: str, max_pages: int) -> dict[str, str]:
    if not category or max_pages <= 0:
        return {}
    pages: dict[str, str] = {}
    cmcontinue = None
    while len(pages) < max_pages:
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": category,
            "cmlimit": min(50, max_pages - len(pages)),
            "format": "json",
        }
        if cmcontinue:
            params["cmcontinue"] = cmcontinue
        query = urllib.parse.urlencode(params)
        req = urllib.request.Request(f"{API_URL}?{query}", headers={"User-Agent": "469-sargam-local-alignment/1.0"})
        with urllib.request.urlopen(req, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
        for member in payload.get("query", {}).get("categorymembers", []):
            title = str(member.get("title") or "")
            if not title.endswith("(Book)"):
                continue
            path = urllib.parse.quote(title.replace(" ", "_"), safe="()_")
            pages[title] = f"https://tibia.fandom.com/wiki/{path}"
        cmcontinue = payload.get("continue", {}).get("cmcontinue")
        if not cmcontinue:
            break
    return pages


def extract_book_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "table", "sup"]):
        tag.decompose()
    blocks = [block.get_text(" ", strip=True) for block in soup.find_all("blockquote")]
    blocks = [block for block in blocks if len(block.split()) >= 20]
    if blocks:
        return "\n".join(blocks)
    text = soup.get_text("\n", strip=True)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS external_corpus_sources (
            source_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            title TEXT NOT NULL,
            source_url TEXT NOT NULL,
            text TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS external_alignment_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            best_shadow_run_id INTEGER,
            source_count INTEGER NOT NULL,
            alignment_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS external_alignment_items (
            run_id INTEGER NOT NULL,
            rank INTEGER NOT NULL,
            source_title TEXT NOT NULL,
            source_url TEXT NOT NULL,
            bookid TEXT NOT NULL,
            anchor TEXT NOT NULL,
            score REAL NOT NULL,
            local_context TEXT NOT NULL,
            external_context TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, rank)
        );
        """
    )


def ingest_sources(conn: sqlite3.Connection, category: str, max_pages: int) -> list[dict[str, Any]]:
    ensure_schema(conn)
    out: list[dict[str, Any]] = []
    pages = dict(SEED_PAGES)
    pages.update(fetch_category_pages(category, max_pages))
    for title, source_url in pages.items():
        row = conn.execute(
            """
            SELECT source_id, title, source_url, text
            FROM external_corpus_sources
            WHERE title = ?
            ORDER BY source_id DESC
            LIMIT 1
            """,
            (title,),
        ).fetchone()
        if row:
            out.append(dict(row))
            continue
        html = fetch_page_html(title)
        text = extract_book_text(html)
        created_at = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
        cur = conn.execute(
            """
            INSERT INTO external_corpus_sources (created_at, title, source_url, text, payload_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                created_at,
                title,
                source_url,
                text,
                json.dumps({"source": "TibiaWiki/Fandom MediaWiki API"}, ensure_ascii=True, sort_keys=True),
            ),
        )
        out.append({"source_id": int(cur.lastrowid), "title": title, "source_url": source_url, "text": text})
    conn.commit()
    return out


def latest_best_shadow(conn: sqlite3.Connection) -> tuple[int | None, list[sqlite3.Row]]:
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


def words(text: str) -> list[str]:
    return [word.lower() for word in WORD_RE.findall(text or "")]


def content_words(text: str) -> set[str]:
    return {word for word in words(text) if len(word) > 3 and word not in STOPWORDS}


def windows_around_anchor(text: str, anchor: str, radius: int) -> list[str]:
    tokens = words(text)
    out: list[str] = []
    for idx, token in enumerate(tokens):
        if token != anchor:
            continue
        lo = max(0, idx - radius)
        hi = min(len(tokens), idx + radius + 1)
        out.append(" ".join(tokens[lo:hi]))
    return out


def align(sources: list[dict[str, Any]], best_rows: list[sqlite3.Row], radius: int) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for source in sources:
        source_text = str(source["text"] or "")
        source_terms = content_words(source_text)
        source_counts = Counter(words(source_text))
        for row in best_rows:
            local_text = str(row["best_shadow_text"] or "")
            local_terms = content_words(local_text)
            anchors = sorted((source_terms & local_terms), key=lambda term: (source_counts[term], term))
            for anchor in anchors[:12]:
                local_windows = windows_around_anchor(local_text, anchor, radius)
                external_windows = windows_around_anchor(source_text, anchor, radius)
                for local_window in local_windows[:4]:
                    local_set = content_words(local_window)
                    for external_window in external_windows[:4]:
                        external_set = content_words(external_window)
                        union = local_set | external_set
                        overlap = len(local_set & external_set) / max(1, len(union))
                        score = round(overlap + 0.15 * len(local_set & external_set), 4)
                        if anchor in {"sunburn", "vampires", "blood", "regenerate", "regeneration"}:
                            score = round(score + 0.4, 4)
                        if score < 0.45:
                            continue
                        items.append(
                            {
                                "source_title": source["title"],
                                "source_url": source["source_url"],
                                "bookid": str(row["bookid"]),
                                "anchor": anchor,
                                "score": score,
                                "local_context": local_window,
                                "external_context": external_window,
                                "overlap_terms": sorted(local_set & external_set),
                            }
                        )
    items.sort(key=lambda item: (-float(item["score"]), item["source_title"], int(item["bookid"]), item["anchor"]))
    return items


def record(conn: sqlite3.Connection, best_shadow_run_id: int | None, sources: list[dict[str, Any]], items: list[dict[str, Any]]) -> int:
    ensure_schema(conn)
    created_at = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    cur = conn.execute(
        """
        INSERT INTO external_alignment_runs (
            created_at, best_shadow_run_id, source_count, alignment_count, payload_json
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (
            created_at,
            best_shadow_run_id,
            len(sources),
            len(items),
            json.dumps({"source_titles": [source["title"] for source in sources]}, ensure_ascii=True, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)
    for rank, item in enumerate(items, start=1):
        conn.execute(
            """
            INSERT INTO external_alignment_items (
                run_id, rank, source_title, source_url, bookid, anchor, score,
                local_context, external_context, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                rank,
                item["source_title"],
                item["source_url"],
                item["bookid"],
                item["anchor"],
                item["score"],
                item["local_context"],
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
        sources = ingest_sources(conn, args.category, args.max_pages)
        best_run_id, best_rows = latest_best_shadow(conn)
        items = align(sources, best_rows, args.context_words)
        run_id = record(conn, best_run_id, sources, items) if args.record else None
    finally:
        conn.close()
    print(
        json.dumps(
            {
                "recorded_run_id": run_id,
                "best_shadow_run_id": best_run_id,
                "source_count": len(sources),
                "alignment_count": len(items),
                "top": items[:20],
            },
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
