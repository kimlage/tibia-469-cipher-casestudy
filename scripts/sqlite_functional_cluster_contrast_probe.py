#!/usr/bin/env python3
"""Rank functional tag clusters by internal literal coherence vs controls.

This is analysis-only. It does not promote translations or mutate decode core.
It writes a reproducible probe result into SQLite so follow-up lanes can choose
families with real contrast instead of reopening broad formula clusters.
"""

from __future__ import annotations

import datetime as dt
import itertools
import json
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"


def now() -> str:
    return dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def ngrams(text: str, n: int = 4) -> set[str]:
    clean = "".join(ch for ch in text if ch.strip())
    if len(clean) < n:
        return {clean} if clean else set()
    return {clean[i : i + n] for i in range(len(clean) - n + 1)}


def jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def mean(vals: list[float]) -> float:
    return sum(vals) / len(vals) if vals else 0.0


def pairs(xs: list[str]) -> list[tuple[str, str]]:
    return list(itertools.combinations(sorted(set(xs), key=lambda x: int(x)), 2))


def load(conn: sqlite3.Connection) -> tuple[dict[str, str], dict[str, list[dict]]]:
    literals = {
        str(row["bookid"]): row["literal_text"]
        for row in conn.execute(
            "SELECT bookid, literal_text FROM literal_homophonic_books_v1 WHERE run_id=(SELECT max(run_id) FROM literal_homophonic_books_v1_runs)"
        )
    }
    tag_rows = conn.execute(
        "SELECT bookid, functional_tags_json FROM final_honest_reading_v19_books WHERE run_id=(SELECT max(run_id) FROM final_honest_reading_v19_runs)"
    ).fetchall()
    by_tag: dict[str, list[dict]] = defaultdict(list)
    for row in tag_rows:
        bookid = str(row["bookid"])
        for tag in json.loads(row["functional_tags_json"] or "[]"):
            if isinstance(tag, str):
                tag = {"tag_id": tag, "label": tag, "source": "string_tag"}
            elif not isinstance(tag, dict):
                tag = {"tag_id": "UNKNOWN", "label": repr(tag), "source": "unknown_tag_shape"}
            tag_id = tag.get("tag_id") or tag.get("label") or "UNKNOWN"
            by_tag[tag_id].append(
                {
                    "bookid": bookid,
                    "label": tag.get("label", ""),
                    "source": tag.get("source", ""),
                    "confidence": tag.get("confidence"),
                }
            )
    return literals, by_tag


def cluster_metrics(tag_id: str, rows: list[dict], literals: dict[str, str]) -> dict:
    books = sorted({r["bookid"] for r in rows}, key=lambda x: int(x))
    all_books = sorted(literals, key=lambda x: int(x))
    outside = [b for b in all_books if b not in books]
    book_grams = {b: ngrams(literals[b], 4) for b in all_books}

    inside_pairs = pairs(books)
    inside_sim = mean([jaccard(book_grams[a], book_grams[b]) for a, b in inside_pairs])

    control_vals: list[float] = []
    for i, b in enumerate(books):
        if not outside:
            continue
        c = outside[(int(b) + i * 7) % len(outside)]
        control_vals.append(jaccard(book_grams[b], book_grams[c]))
    control_sim = mean(control_vals)

    tag_counter = Counter()
    outside_counter = Counter()
    for b in books:
        tag_counter.update(book_grams[b])
    for b in outside:
        outside_counter.update(book_grams[b])

    distinctive = []
    for gram, count in tag_counter.items():
        in_rate = count / max(1, len(books))
        out_rate = outside_counter.get(gram, 0) / max(1, len(outside))
        lift = in_rate - out_rate
        if in_rate >= 0.4 and lift > 0.25:
            distinctive.append((gram, round(in_rate, 3), round(out_rate, 3), round(lift, 3)))
    distinctive.sort(key=lambda x: (-x[3], -x[1], x[0]))

    size = len(books)
    coherence_lift = inside_sim - control_sim
    distinctive_count = len(distinctive)
    if size > 20:
        decision = "BROAD_FORMULA_CLUSTER_LOW_SEMANTIC_PRIORITY"
    elif distinctive_count >= 5 and coherence_lift > 0.02:
        decision = "ALIVE_FOR_CONTRASTIVE_SEMANTIC_TEST"
    elif distinctive_count >= 3:
        decision = "ALIVE_BUT_NEEDS_STRONGER_CONTROL"
    else:
        decision = "WEAK_CONTRAST_DO_NOT_PROMOTE"

    labels = Counter(r["label"] for r in rows if r.get("label"))
    sources = Counter(r["source"] for r in rows if r.get("source"))
    return {
        "tag_id": tag_id,
        "book_count": size,
        "books": books,
        "inside_ngram_jaccard": round(inside_sim, 4),
        "control_ngram_jaccard": round(control_sim, 4),
        "coherence_lift": round(coherence_lift, 4),
        "distinctive_ngram_count": distinctive_count,
        "top_distinctive_ngrams": distinctive[:12],
        "dominant_label": labels.most_common(1)[0][0] if labels else "",
        "dominant_source": sources.most_common(1)[0][0] if sources else "",
        "decision": decision,
    }


def main() -> None:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS functional_cluster_contrast_probe_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            alive_count INTEGER NOT NULL,
            weak_count INTEGER NOT NULL,
            broad_formula_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS functional_cluster_contrast_probe_items (
            run_id INTEGER NOT NULL,
            rank INTEGER NOT NULL,
            tag_id TEXT NOT NULL,
            book_count INTEGER NOT NULL,
            decision TEXT NOT NULL,
            coherence_lift REAL NOT NULL,
            distinctive_ngram_count INTEGER NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, rank)
        )
        """
    )

    literals, by_tag = load(conn)
    metrics = [cluster_metrics(tag_id, rows, literals) for tag_id, rows in by_tag.items()]
    metrics.sort(
        key=lambda m: (
            m["decision"] != "ALIVE_FOR_CONTRASTIVE_SEMANTIC_TEST",
            -m["distinctive_ngram_count"],
            -m["coherence_lift"],
            m["book_count"],
            m["tag_id"],
        )
    )
    alive = sum(1 for m in metrics if m["decision"].startswith("ALIVE"))
    broad = sum(1 for m in metrics if m["decision"].startswith("BROAD"))
    weak = len(metrics) - alive - broad
    decision = "CONTRASTIVE_CLUSTERS_AVAILABLE_NO_GLOSS_PROMOTION" if alive else "NO_CONTRASTIVE_CLUSTER_AVAILABLE"

    cur = conn.execute(
        """
        INSERT INTO functional_cluster_contrast_probe_runs
        (created_at, decision, alive_count, weak_count, broad_formula_count, payload_json)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            now(),
            decision,
            alive,
            weak,
            broad,
            json.dumps({"source": "final_honest_reading_v19 + literal_homophonic_books_v1"}, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)
    for rank, m in enumerate(metrics, 1):
        conn.execute(
            """
            INSERT INTO functional_cluster_contrast_probe_items
            (run_id, rank, tag_id, book_count, decision, coherence_lift, distinctive_ngram_count, evidence_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                rank,
                m["tag_id"],
                m["book_count"],
                m["decision"],
                m["coherence_lift"],
                m["distinctive_ngram_count"],
                json.dumps(m, sort_keys=True),
            ),
        )
    conn.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "alive_count": alive,
                "weak_count": weak,
                "broad_formula_count": broad,
                "top": metrics[:8],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
