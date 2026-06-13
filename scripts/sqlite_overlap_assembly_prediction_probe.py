#!/usr/bin/env python3
"""Predict local assembly edges from token overlap without using contig labels."""

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


def main() -> None:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS overlap_assembly_prediction_probe_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            known_contig_edge_hits INTEGER NOT NULL,
            predicted_edge_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS overlap_assembly_prediction_probe_items (
            run_id INTEGER NOT NULL,
            rank INTEGER NOT NULL,
            book_a TEXT NOT NULL,
            book_b TEXT NOT NULL,
            lcs_ratio REAL NOT NULL,
            known_contig_edge INTEGER NOT NULL,
            shared_roles_json TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, rank)
        )
        """
    )

    tokens = {
        str(r["bookid"]): json.loads(r["tokens_json"])
        for r in conn.execute(
            "SELECT bookid, tokens_json FROM row0_variant_book_tokens WHERE run_id=(SELECT max(run_id) FROM row0_variant_frontier_runs)"
        )
    }
    role_books = {}
    for row in conn.execute(
        "SELECT role_id, books_json FROM structural_role_registry_v1_items WHERE run_id=(SELECT max(run_id) FROM structural_role_registry_v1_runs)"
    ):
        for book in json.loads(row["books_json"] or "[]"):
            role_books.setdefault(str(book), set()).add(row["role_id"])

    known_edges = set()
    for row in conn.execute(
        "SELECT booksinorder FROM sheet__contigs WHERE __export_id=(SELECT max(__export_id) FROM sheet__contigs)"
    ):
        order = [x.strip() for x in (row["booksinorder"] or "").split("->") if x.strip()]
        for a, b in zip(order, order[1:]):
            known_edges.add(tuple(sorted((a, b), key=lambda x: int(x))))

    scored = []
    for a, b in combinations(sorted(tokens, key=lambda x: int(x)), 2):
        shorter = min(len(tokens[a]), len(tokens[b]))
        ratio = lcs_len(tokens[a], tokens[b]) / max(1, shorter)
        if ratio < 0.82:
            continue
        shared_roles = sorted(role_books.get(a, set()) & role_books.get(b, set()))
        if not shared_roles and ratio < 0.9:
            continue
        edge = tuple(sorted((a, b), key=lambda x: int(x)))
        scored.append(
            {
                "book_a": a,
                "book_b": b,
                "lcs_ratio": round(ratio, 4),
                "known_contig_edge": 1 if edge in known_edges else 0,
                "shared_roles": shared_roles,
                "evidence": {
                    "len_a": len(tokens[a]),
                    "len_b": len(tokens[b]),
                    "shared_role_count": len(shared_roles),
                },
            }
        )
    scored.sort(key=lambda x: (-x["known_contig_edge"], -x["lcs_ratio"], -len(x["shared_roles"]), int(x["book_a"]), int(x["book_b"])))
    top = scored[:40]
    hits = sum(x["known_contig_edge"] for x in top)
    decision = "OVERLAP_PREDICTS_KNOWN_AND_CANDIDATE_ASSEMBLY_EDGES" if hits else "OVERLAP_NO_KNOWN_CONTIG_SIGNAL"
    cur = conn.execute(
        """
        INSERT INTO overlap_assembly_prediction_probe_runs
        (created_at, decision, known_contig_edge_hits, predicted_edge_count, payload_json)
        VALUES (?, ?, ?, ?, ?)
        """,
        (now(), decision, hits, len(top), json.dumps({"threshold": "lcs_ratio>=0.82 with role filter"}, sort_keys=True)),
    )
    run_id = int(cur.lastrowid)
    for rank, item in enumerate(top, 1):
        conn.execute(
            """
            INSERT INTO overlap_assembly_prediction_probe_items
            (run_id, rank, book_a, book_b, lcs_ratio, known_contig_edge, shared_roles_json, evidence_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                rank,
                item["book_a"],
                item["book_b"],
                item["lcs_ratio"],
                item["known_contig_edge"],
                json.dumps(item["shared_roles"]),
                json.dumps(item["evidence"], sort_keys=True),
            ),
        )
    conn.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "known_contig_edge_hits": hits,
                "predicted_edge_count": len(top),
                "top": top[:20],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
