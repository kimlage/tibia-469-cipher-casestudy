#!/usr/bin/env python3
"""Compare aggregate C86 role vs split C86 subfamilies.

Analysis-only. The split is useful only if the subfamilies are more predictive
than aggregate C86 for known contig edges and structural variant families.
"""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from itertools import combinations
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def lcs_len(a: list[str], b: list[str]) -> int:
    prev = [0] * (len(b) + 1)
    for x in a:
        cur = [0]
        for j, y in enumerate(b, 1):
            cur.append(prev[j - 1] + 1 if x == y else max(prev[j], cur[-1]))
        prev = cur
    return prev[-1]


def edge_set(conn: sqlite3.Connection) -> set[tuple[str, str]]:
    out = set()
    for row in conn.execute(
        "SELECT booksinorder FROM sheet__contigs WHERE __export_id=(SELECT max(__export_id) FROM sheet__contigs)"
    ):
        order = [x.strip() for x in (row["booksinorder"] or "").split("->") if x.strip()]
        for a, b in zip(order, order[1:]):
            out.add(tuple(sorted((a, b), key=lambda x: int(x))))
    return out


def metrics(name: str, books: list[str], tokens: dict[str, list[str]], known_edges: set[tuple[str, str]]) -> dict:
    pairs = []
    for a, b in combinations(sorted(books, key=lambda x: int(x)), 2):
        ratio = lcs_len(tokens[a], tokens[b]) / max(1, min(len(tokens[a]), len(tokens[b])))
        is_edge = tuple(sorted((a, b), key=lambda x: int(x))) in known_edges
        pairs.append({"a": a, "b": b, "ratio": round(ratio, 4), "known_edge": is_edge})
    high = [p for p in pairs if p["ratio"] >= 0.82]
    edge_hits = sum(1 for p in high if p["known_edge"])
    precision = edge_hits / max(1, len(high))
    avg_ratio = sum(p["ratio"] for p in pairs) / max(1, len(pairs))
    return {
        "family": name,
        "book_count": len(books),
        "pair_count": len(pairs),
        "high_overlap_pair_count": len(high),
        "known_edge_hits": edge_hits,
        "high_overlap_edge_precision": round(precision, 4),
        "avg_pair_lcs_ratio": round(avg_ratio, 4),
        "high_pairs": sorted(high, key=lambda p: (-p["known_edge"], -p["ratio"], int(p["a"]), int(p["b"]))),
    }


def main() -> None:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS c86_subfamily_predictiveness_probe_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            aggregate_precision REAL NOT NULL,
            split_weighted_precision REAL NOT NULL,
            payload_json TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS c86_subfamily_predictiveness_probe_items (
            run_id INTEGER NOT NULL,
            family_id TEXT NOT NULL,
            status TEXT NOT NULL,
            book_count INTEGER NOT NULL,
            high_overlap_pair_count INTEGER NOT NULL,
            known_edge_hits INTEGER NOT NULL,
            precision REAL NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, family_id)
        )
        """
    )
    tokens = {
        str(r["bookid"]): json.loads(r["tokens_json"])
        for r in conn.execute(
            "SELECT bookid, tokens_json FROM row0_variant_book_tokens WHERE run_id=(SELECT max(run_id) FROM row0_variant_frontier_runs)"
        )
    }
    known_edges = edge_set(conn)
    subfamilies = {
        row["subfamily_id"]: json.loads(row["books_json"])
        for row in conn.execute(
            "SELECT subfamily_id, books_json FROM c86_subfamily_split_v1_items WHERE run_id=(SELECT max(run_id) FROM c86_subfamily_split_v1_runs)"
        )
    }
    aggregate = sorted({b for books in subfamilies.values() for b in books}, key=lambda x: int(x))
    results = [metrics("C86_AGGREGATE", aggregate, tokens, known_edges)]
    for name, books in subfamilies.items():
        results.append(metrics(name, books, tokens, known_edges))

    agg = results[0]
    split_high = sum(r["high_overlap_pair_count"] for r in results[1:])
    split_hits = sum(r["known_edge_hits"] for r in results[1:])
    split_precision = split_hits / max(1, split_high)
    aggregate_precision = agg["known_edge_hits"] / max(1, agg["high_overlap_pair_count"])
    eps = 1e-6
    if split_precision > aggregate_precision + eps and split_hits >= agg["known_edge_hits"]:
        decision = "C86_SPLIT_IMPROVES_EDGE_SPECIFICITY_KEEP_NO_GLOSS"
    elif abs(split_precision - aggregate_precision) <= eps and split_hits >= agg["known_edge_hits"]:
        decision = "C86_SPLIT_TIES_EDGE_SPECIFICITY_KEEP_FOR_CONTRADICTION_REDUCTION_NO_GLOSS"
    else:
        decision = "C86_SPLIT_NOT_PREDICTIVE_DEMOTE_TO_AUDIT"

    cur = conn.execute(
        """
        INSERT INTO c86_subfamily_predictiveness_probe_runs
        (created_at, decision, aggregate_precision, split_weighted_precision, payload_json)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            now(),
            decision,
            aggregate_precision,
            round(split_precision, 4),
            json.dumps({"aggregate_books": aggregate}, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)
    for r in results:
        if r["family"] == "C86_AGGREGATE":
            status = "BASELINE_AGGREGATE"
        elif decision.startswith("C86_SPLIT_NOT"):
            status = "DEMOTE_SUBFAMILY_AUDIT_ONLY"
        else:
            status = "KEEP_SUBFAMILY_NO_GLOSS"
        conn.execute(
            """
            INSERT INTO c86_subfamily_predictiveness_probe_items
            (run_id, family_id, status, book_count, high_overlap_pair_count, known_edge_hits, precision, evidence_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                r["family"],
                status,
                r["book_count"],
                r["high_overlap_pair_count"],
                r["known_edge_hits"],
                r["high_overlap_edge_precision"],
                json.dumps(r, sort_keys=True),
            ),
        )
    conn.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "aggregate_precision": aggregate_precision,
                "split_weighted_precision": round(split_precision, 4),
                "results": results,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
