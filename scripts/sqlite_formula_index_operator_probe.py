#!/usr/bin/env python3
"""Test whether formula contexts predict contig positions better than controls."""

from __future__ import annotations

import datetime as dt
import json
import random
import re
import sqlite3
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

FORMULAS = {
    "BENNA_FORMULA": "BENNA",
    "LTAST_TAIL": "LTAST",
    "VNCTIIN_FRAME": "VNCTIIN",
    "C86_PAYLOAD": "C86",
    "NAESE_SLOT": "NAESE",
}


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def code_signature(tokens: list[str]) -> str:
    codes = [t for t in tokens if re.search(r"\d", t)]
    return "+".join(codes) if codes else "NO_CODE"


def split_contigs(conn: sqlite3.Connection) -> dict[str, tuple[str, int]]:
    pos = {}
    for row in conn.execute(
        "SELECT basecontigid, booksinorder FROM sheet__contigs WHERE __export_id=(SELECT max(__export_id) FROM sheet__contigs)"
    ):
        order = [x.strip() for x in (row["booksinorder"] or "").split("->") if x.strip()]
        for i, bookid in enumerate(order, 1):
            pos[str(bookid)] = (str(row["basecontigid"]), i)
    return pos


def purity(rows: list[dict], key: str) -> float:
    grouped = defaultdict(list)
    for row in rows:
        grouped[row[key]].append(row["target"])
    if not grouped:
        return 0.0
    correct = 0
    total = 0
    for vals in grouped.values():
        counts = defaultdict(int)
        for v in vals:
            counts[v] += 1
        correct += max(counts.values())
        total += len(vals)
    return correct / max(1, total)


def main() -> None:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS formula_index_operator_probe_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            accepted_formula_count INTEGER NOT NULL,
            rejected_formula_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS formula_index_operator_probe_items (
            run_id INTEGER NOT NULL,
            formula_id TEXT NOT NULL,
            status TEXT NOT NULL,
            occurrence_count INTEGER NOT NULL,
            observed_purity REAL NOT NULL,
            shuffled_purity REAL NOT NULL,
            lift REAL NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, formula_id)
        )
        """
    )

    role_books = defaultdict(set)
    for row in conn.execute(
        "SELECT role_id, books_json FROM structural_role_registry_v1_items WHERE run_id=(SELECT max(run_id) FROM structural_role_registry_v1_runs)"
    ):
        for book in json.loads(row["books_json"] or "[]"):
            role_books[str(book)].add(row["role_id"])

    contig_pos = split_contigs(conn)
    books = []
    for row in conn.execute(
        "SELECT bookid, tokens_json, symbol_text FROM row0_variant_book_tokens WHERE run_id=(SELECT max(run_id) FROM row0_variant_frontier_runs)"
    ):
        bookid = str(row["bookid"])
        tokens = json.loads(row["tokens_json"])
        roles = sorted(role_books.get(bookid, set()))
        contig, pos = contig_pos.get(bookid, ("NO_CONTIG", 0))
        books.append({"bookid": bookid, "tokens": tokens, "symbol_text": row["symbol_text"], "roles": roles, "target": f"{contig}:{pos}"})

    rng = random.Random(469)
    results = []
    for formula_id, needle in FORMULAS.items():
        rows = []
        for book in books:
            if needle not in book["symbol_text"]:
                continue
            sig = code_signature(book["tokens"])
            role_sig = "+".join(book["roles"][:4]) if book["roles"] else "NO_ROLE"
            rows.append(
                {
                    "bookid": book["bookid"],
                    "feature": f"{sig}|{role_sig}",
                    "target": book["target"],
                    "roles": book["roles"],
                }
            )
        observed = purity(rows, "feature")
        shuffled_rows = [dict(r) for r in rows]
        targets = [r["target"] for r in shuffled_rows]
        rng.shuffle(targets)
        for row, target in zip(shuffled_rows, targets):
            row["target"] = target
        shuffled = purity(shuffled_rows, "feature")
        lift = observed - shuffled
        if len(rows) >= 4 and lift >= 0.15 and observed >= 0.65:
            status = "ACCEPT_FORMULA_INDEX_OPERATOR_NO_GLOSS"
        elif len(rows) >= 4 and lift > 0.0:
            status = "WEAK_FORMULA_INDEX_SIGNAL_AUDIT_ONLY"
        else:
            status = "REJECT_FORMULA_INDEX_SIGNAL"
        results.append(
            {
                "formula_id": formula_id,
                "status": status,
                "occurrence_count": len(rows),
                "observed_purity": round(observed, 4),
                "shuffled_purity": round(shuffled, 4),
                "lift": round(lift, 4),
                "examples": rows[:12],
            }
        )

    accepted = sum(1 for r in results if r["status"].startswith("ACCEPT"))
    rejected = len(results) - accepted
    decision = "FORMULA_INDEX_OPERATOR_ACCEPTED_FOR_SOME_CORES_NO_GLOSS" if accepted else "FORMULA_INDEX_OPERATOR_NOT_SUPPORTED"
    cur = conn.execute(
        """
        INSERT INTO formula_index_operator_probe_runs
        (created_at, decision, accepted_formula_count, rejected_formula_count, payload_json)
        VALUES (?, ?, ?, ?, ?)
        """,
        (now(), decision, accepted, rejected, json.dumps({"shuffle_seed": 469}, sort_keys=True)),
    )
    run_id = int(cur.lastrowid)
    for r in results:
        conn.execute(
            """
            INSERT INTO formula_index_operator_probe_items
            (run_id, formula_id, status, occurrence_count, observed_purity, shuffled_purity, lift, evidence_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                r["formula_id"],
                r["status"],
                r["occurrence_count"],
                r["observed_purity"],
                r["shuffled_purity"],
                r["lift"],
                json.dumps({"examples": r["examples"]}, sort_keys=True),
            ),
        )
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": decision, "results": results}, ensure_ascii=False))


if __name__ == "__main__":
    main()
