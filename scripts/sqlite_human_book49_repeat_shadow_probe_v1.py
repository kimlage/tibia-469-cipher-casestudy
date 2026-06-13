#!/usr/bin/env python3
"""Test Book49's human shadow reading as a self-contained repeat formula."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
TARGET = "49"
CONTROL = "55"


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ngrams(tokens: list[str], n: int) -> list[tuple[str, ...]]:
    return [tuple(tokens[i : i + n]) for i in range(0, len(tokens) - n + 1)]


def repeat_metrics(tokens: list[str]) -> dict[str, Any]:
    repeated: list[dict[str, Any]] = []
    covered: set[int] = set()
    for n in range(3, 9):
        grams = ngrams(tokens, n)
        counts = Counter(grams)
        for gram, count in counts.items():
            if count > 1:
                positions = [i for i, candidate in enumerate(grams) if candidate == gram]
                for pos in positions:
                    covered.update(range(pos, pos + n))
                repeated.append(
                    {
                        "n": n,
                        "gram": "".join(gram),
                        "token_gram": list(gram),
                        "count": count,
                        "positions": positions,
                    }
                )
    return {
        "token_count": len(tokens),
        "repeated_ngram_count": len(repeated),
        "coverage": round(len(covered) / len(tokens), 4) if tokens else 0.0,
        "covered_positions": sorted(covered),
        "top_repeats": sorted(repeated, key=lambda item: (-item["n"], -item["count"], item["gram"]))[:20],
    }


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_book49_repeat_shadow_probe_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            target_bookid TEXT NOT NULL,
            target_repeat_coverage REAL NOT NULL,
            target_repeat_rank INTEGER NOT NULL,
            control_bookid TEXT NOT NULL,
            control_repeat_coverage REAL NOT NULL,
            final_tag_present INTEGER NOT NULL,
            accepted_human_gloss_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_book49_repeat_shadow_probe_v1_items (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            token_count INTEGER NOT NULL,
            repeated_ngram_count INTEGER NOT NULL,
            repeated_token_coverage REAL NOT NULL,
            repeat_rank INTEGER NOT NULL,
            final_tag_present INTEGER NOT NULL,
            classification TEXT NOT NULL,
            shadow_implication TEXT NOT NULL,
            next_action TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        );
        """
    )


def final_tag_map(conn: sqlite3.Connection) -> dict[str, str]:
    rows = conn.execute(
        """
        SELECT bookid, functional_tags_json
        FROM final_honest_reading_v19_books
        WHERE run_id=(SELECT max(run_id) FROM final_honest_reading_v19_books)
        """
    ).fetchall()
    return {str(row["bookid"]): str(row["functional_tags_json"] or "") for row in rows}


def classify(bookid: str, metrics: dict[str, Any], rank: int, tag_text: str) -> tuple[str, str, str]:
    has_target_tag = "SELF_CONTAINED_REPEAT_FORMULA" in tag_text
    has_internal_repeat = "INTERNAL_REPEAT" in tag_text or "repeat" in tag_text.lower()
    if bookid == TARGET and has_target_tag and metrics["coverage"] >= 0.55:
        return (
            "SELF_CONTAINED_REPEAT_FORMULA_SUPPORTED",
            "Supports the Book49 shadow reading as a closed repeat/formula register, not narrative prose.",
            "Use as formula/refrain witness; compare against Book55 repeat control before drafting stronger wording.",
        )
    if bookid == CONTROL and has_internal_repeat:
        return (
            "INTERNAL_REPEAT_CONTROL",
            "Book55 provides a repeat/variant control, but not the same self-contained Book49 register.",
            "Use as negative/contrast control for repeat does not equal same function.",
        )
    if metrics["coverage"] >= 0.55:
        return (
            "HIGH_REPEAT_CONTROL",
            "High repetition exists outside Book49; avoid making repeat alone semantic.",
            "Use as repeat control before strengthening Book49 prose.",
        )
    return (
        "LOW_OR_MID_REPEAT_BACKGROUND",
        "Background repetition level; no human reading implication.",
        "Keep as corpus background.",
    )


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    rows = conn.execute(
        """
        SELECT bookid, tokens_json, symbol_text
        FROM row0_variant_book_tokens
        WHERE run_id=(SELECT max(run_id) FROM row0_variant_book_tokens)
        """
    ).fetchall()
    tag_text = final_tag_map(conn)
    records = []
    for row in rows:
        tokens = json.loads(row["tokens_json"] or "[]")
        metrics = repeat_metrics(tokens)
        records.append(
            {
                "bookid": str(row["bookid"]),
                "symbol_text": str(row["symbol_text"]),
                **metrics,
                "final_tag_text": tag_text.get(str(row["bookid"]), ""),
            }
        )
    ranked = sorted(records, key=lambda item: (-item["coverage"], -item["repeated_ngram_count"], int(item["bookid"])))
    rank_by_book = {item["bookid"]: idx + 1 for idx, item in enumerate(ranked)}
    target = next(item for item in records if item["bookid"] == TARGET)
    control = next(item for item in records if item["bookid"] == CONTROL)
    target_tag_present = 1 if "SELF_CONTAINED_REPEAT_FORMULA" in target["final_tag_text"] else 0
    if target_tag_present and target["coverage"] >= 0.55 and rank_by_book[TARGET] <= 20:
        decision = "BOOK49_REPEAT_SHADOW_SUPPORTED_NO_GLOSS"
    elif target_tag_present:
        decision = "BOOK49_REPEAT_SHADOW_PARTIAL_SUPPORT_NO_GLOSS"
    else:
        decision = "BOOK49_REPEAT_SHADOW_NEEDS_REVISION"
    payload = {
        "target": {k: target[k] for k in ("bookid", "symbol_text", "token_count", "repeated_ngram_count", "coverage")},
        "control": {k: control[k] for k in ("bookid", "symbol_text", "token_count", "repeated_ngram_count", "coverage")},
        "top_repeat_books": [
            {
                "bookid": item["bookid"],
                "coverage": item["coverage"],
                "repeated_ngram_count": item["repeated_ngram_count"],
            }
            for item in ranked[:12]
        ],
        "principle": "repeat supports register/function only, not lexical translation",
    }
    cur = conn.execute(
        """
        INSERT INTO human_book49_repeat_shadow_probe_v1_runs
        (created_at, decision, target_bookid, target_repeat_coverage,
         target_repeat_rank, control_bookid, control_repeat_coverage,
         final_tag_present, accepted_human_gloss_count, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            now(),
            decision,
            TARGET,
            target["coverage"],
            rank_by_book[TARGET],
            CONTROL,
            control["coverage"],
            target_tag_present,
            0,
            json.dumps(payload, ensure_ascii=False, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)
    for item in ranked[:12]:
        rank = rank_by_book[item["bookid"]]
        classification, implication, next_action = classify(item["bookid"], item, rank, item["final_tag_text"])
        conn.execute(
            """
            INSERT INTO human_book49_repeat_shadow_probe_v1_items
            (run_id, bookid, token_count, repeated_ngram_count,
             repeated_token_coverage, repeat_rank, final_tag_present,
             classification, shadow_implication, next_action, evidence_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                item["bookid"],
                item["token_count"],
                item["repeated_ngram_count"],
                item["coverage"],
                rank,
                1 if item["final_tag_text"] else 0,
                classification,
                implication,
                next_action,
                json.dumps(
                    {
                        "symbol_text": item["symbol_text"],
                        "top_repeats": item["top_repeats"],
                        "covered_positions": item["covered_positions"],
                        "final_tag_text": item["final_tag_text"],
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                ),
            ),
        )

    conn.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "target_repeat_coverage": target["coverage"],
                "target_repeat_rank": rank_by_book[TARGET],
                "control_repeat_coverage": control["coverage"],
                "accepted_human_gloss_count": 0,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
