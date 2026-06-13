#!/usr/bin/env python3
"""BENNA ordered-core model v2.

Converts the failed broad propagation into a stricter operational rule:
BENNA has a small ordered core and a larger quarantined display/parallel shell.
No human semantic gloss is accepted.
"""

from __future__ import annotations

import datetime as dt
import json
import sqlite3

from sqlite_operational_grammar_reconstruction_probe import DB, classify_states, edge_score, load_books

ORDERED_CORE_EDGES = {
    ("47", "40"): "TEMPLATE_HEAD_TO_FORMULA_BODY",
    ("58", "35"): "DISPLAY_FORMULA_HEAD_TO_HANDOFF_CONTEXT",
    ("69", "35"): "MIXED_TEMPLATE_FORMULA_HEAD_TO_HANDOFF_CONTEXT",
}
QUARANTINED_DISPLAY_BOOKS = {"11", "36", "43", "59"}
BOUNDARY_TAIL_BOOKS = {"0", "33", "66"}
HANDOFF_CONTEXT_BOOKS = {"10", "35"}
TEMPLATE_BOOKS = {"5", "47"}
FORMULA_CORE_BOOKS = {"9", "40", "50", "58", "69"}
AUDIT_ONLY_BOOKS = {"6"}
UNCLASSIFIED_SURFACE_BOOKS = {"19"}


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def classify_book(bookid: str) -> tuple[str, str, str]:
    if bookid in AUDIT_ONLY_BOOKS:
        return "AUDIT_ONLY", "BOOK6_CONTINUITY_AUDIT", "unique/audit continuity signal; not part of ordered core"
    if bookid in QUARANTINED_DISPLAY_BOOKS:
        return "QUARANTINED", "DISPLAY_PARALLEL", "display/window parallel; not an ordered continuity claim"
    if bookid in BOUNDARY_TAIL_BOOKS:
        return "QUARANTINED", "BOUNDARY_TAIL_PARALLEL", "LTAST tail/boundary parallel; not enough to order by itself"
    if bookid in HANDOFF_CONTEXT_BOOKS:
        return "ORDERED_CORE", "HANDOFF_CONTEXT", "receives formula head and can continue into context payload"
    if bookid == "69":
        return "ORDERED_CORE", "MIXED_TEMPLATE_FORMULA_HEAD", "alternate template+formula head into handoff context"
    if bookid == "58":
        return "ORDERED_CORE", "DISPLAY_FORMULA_HEAD", "canonical display/formula head into handoff context"
    if bookid == "47":
        return "ORDERED_CORE", "TEMPLATE_HEAD", "template head into formula body"
    if bookid == "40":
        return "ORDERED_CORE", "FORMULA_BODY", "formula body after template head"
    if bookid in TEMPLATE_BOOKS:
        return "QUARANTINED", "TEMPLATE_PARALLEL", "template-like book without accepted ordered edge"
    if bookid in FORMULA_CORE_BOOKS:
        return "QUARANTINED", "FORMULA_PARALLEL", "formula-like book without accepted ordered edge"
    if bookid in UNCLASSIFIED_SURFACE_BOOKS:
        return "QUARANTINED", "SURFACE_BENNA_CONTEXT", "BENNA surface inside context frame; no ordered role"
    return "OUT_OF_SCOPE", "OTHER", "not a BENNA v2 book"


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS benna_ordered_core_v2_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            ordered_core_book_count INTEGER NOT NULL,
            quarantined_book_count INTEGER NOT NULL,
            ordered_edge_count INTEGER NOT NULL,
            contradiction_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS benna_ordered_core_v2_items (
            run_id INTEGER NOT NULL,
            item_type TEXT NOT NULL,
            item_id TEXT NOT NULL,
            status TEXT NOT NULL,
            role_label TEXT NOT NULL,
            interpretation TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, item_type, item_id)
        )
        """
    )
    books = load_books(conn)
    states = {bookid: classify_states(book) for bookid, book in books.items()}
    benna_ids = sorted(
        [bookid for bookid, book in books.items() if any("BENNA" in node for node in set(book.accepted) | set(book.audit) | set(book.scoped)) or "BENNA" in book.literal],
        key=int,
    )
    book_items = {}
    for bookid in benna_ids:
        status, role, interp = classify_book(bookid)
        if status == "OUT_OF_SCOPE":
            status = "QUARANTINED"
        book_items[bookid] = {
            "status": status,
            "role": role,
            "interpretation": interp,
            "states": sorted(states[bookid]),
            "nodes": sorted(set(books[bookid].accepted) | set(books[bookid].audit) | set(books[bookid].scoped)),
        }

    edge_items = {}
    contradictions = []
    for edge, role in ORDERED_CORE_EDGES.items():
        payload = edge_score(books[edge[0]], books[edge[1]], states)
        if payload["score"] < 100 or payload["overlap"] < 30:
            contradictions.append(f"{edge[0]}->{edge[1]}")
            status = "ORDERED_EDGE_FAILED_GATE"
        else:
            status = "ORDERED_EDGE_ACCEPTED_NO_GLOSS"
        edge_items[f"{edge[0]}->{edge[1]}"] = {
            "status": status,
            "role": role,
            "interpretation": "accepted as ordered BENNA structural edge; no human gloss",
            "evidence": {"score": payload["score"], "overlap": payload["overlap"], "prior": payload["prior"], "transition": payload["transition"]},
        }

    # Explicitly record the broad false-positive families so later agents do not reopen them as semantic gloss.
    for source in sorted(TEMPLATE_BOOKS | FORMULA_CORE_BOOKS | QUARANTINED_DISPLAY_BOOKS | BOUNDARY_TAIL_BOOKS, key=int):
        for target in sorted(QUARANTINED_DISPLAY_BOOKS | BOUNDARY_TAIL_BOOKS | HANDOFF_CONTEXT_BOOKS, key=int):
            edge = (source, target)
            edge_key = f"{source}->{target}"
            if edge in ORDERED_CORE_EDGES or source == target or source not in books or target not in books:
                continue
            payload = edge_score(books[source], books[target], states)
            if payload["score"] >= 100 or payload["overlap"] >= 24:
                edge_items[edge_key] = {
                    "status": "QUARANTINED_PARALLEL_EDGE",
                    "role": "BROAD_BENNA_PARALLEL_NOT_ORDERED",
                    "interpretation": "broad BENNA similarity is explicitly not a continuity or semantic claim",
                    "evidence": {"score": payload["score"], "overlap": payload["overlap"], "prior": payload["prior"], "transition": payload["transition"]},
                }

    decision = "BENNA_ORDERED_CORE_STABLE_BROAD_PARALLELS_QUARANTINED_NO_GLOSS" if not contradictions else "BENNA_ORDERED_CORE_HAS_GATE_FAILURES"
    cur = conn.execute(
        """
        INSERT INTO benna_ordered_core_v2_runs
        (created_at, decision, ordered_core_book_count, quarantined_book_count, ordered_edge_count, contradiction_count, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            now(),
            decision,
            sum(1 for item in book_items.values() if item["status"] == "ORDERED_CORE"),
            sum(1 for item in book_items.values() if item["status"] == "QUARANTINED"),
            len(ORDERED_CORE_EDGES),
            len(contradictions),
            json.dumps({"contradictions": contradictions, "ordered_core_edges": sorted([f"{a}->{b}" for a, b in ORDERED_CORE_EDGES])}, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)
    for bookid, item in book_items.items():
        conn.execute(
            """
            INSERT INTO benna_ordered_core_v2_items
            (run_id, item_type, item_id, status, role_label, interpretation, evidence_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, "book", bookid, item["status"], item["role"], item["interpretation"], json.dumps({"states": item["states"], "nodes": item["nodes"]}, sort_keys=True)),
        )
    for edge_key, item in edge_items.items():
        conn.execute(
            """
            INSERT INTO benna_ordered_core_v2_items
            (run_id, item_type, item_id, status, role_label, interpretation, evidence_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, "edge", edge_key, item["status"], item["role"], item["interpretation"], json.dumps(item["evidence"], sort_keys=True)),
        )
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": decision, "ordered_core_book_count": sum(1 for item in book_items.values() if item["status"] == "ORDERED_CORE"), "quarantined_book_count": sum(1 for item in book_items.values() if item["status"] == "QUARANTINED"), "ordered_edge_count": len(ORDERED_CORE_EDGES), "contradiction_count": len(contradictions)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
