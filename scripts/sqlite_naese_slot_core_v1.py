#!/usr/bin/env python3
"""NAESE/R02 slot-core audit.

Separates canonical slot core, R02 bridge pair, variants, surface-only mentions,
and weak audit/hybrid cases. Structural only; no human semantic gloss.
"""

from __future__ import annotations

import datetime as dt
import json
import sqlite3

from sqlite_operational_grammar_reconstruction_probe import DB, classify_states, edge_score, load_books

CANONICAL_SLOT = {"2", "22"}
R02_BRIDGE_PAIR = {"51", "53"}
VARIANT_SLOT = {"28", "48"}
CONTEXT_CONNECTOR = {"46"}
HYBRID_AUDIT = {"42"}
WEAK_AUDIT = {"56"}
SURFACE_ONLY = {"5", "9"}
ORDERED_EDGES = {
    ("51", "53"): "R02_BRIDGE_PAIR_CONTIG",
    ("67", "2"): "CONTEXT_PAYLOAD_TO_CANONICAL_SLOT",
}


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def classify_book(bookid: str) -> tuple[str, str, str]:
    if bookid in R02_BRIDGE_PAIR:
        return "ORDERED_CORE", "R02_SLOT_BRIDGE", "R02/TRVEIIVNTBB bridge plus canonical NAESE slot"
    if bookid in CANONICAL_SLOT:
        return "ORDERED_CORE", "CANONICAL_SLOT", "canonical NAESE slot window without R02 bridge"
    if bookid in VARIANT_SLOT:
        return "VARIANT", "NAESE_VARIANT", "variant slot family; structurally related but not ordered core"
    if bookid in CONTEXT_CONNECTOR:
        return "SUPPORT", "CONTEXT_CONNECTOR", "connector carrying R02/NAESE context but not a slot proof by itself"
    if bookid in HYBRID_AUDIT:
        return "QUARANTINED", "BOOK42_HYBRID", "hybrid handoff/weak slot boundary; not a clean NAESE slot"
    if bookid in WEAK_AUDIT:
        return "QUARANTINED", "WEAK_NAESE_AUDIT", "weak NAESE-like tail inside O23/FNAAST control"
    if bookid in SURFACE_ONLY:
        return "QUARANTINED", "SURFACE_ONLY_NAESE", "literal NAESE surface without accepted NAESE structural node"
    return "OUT_OF_SCOPE", "OTHER", "not part of NAESE slot audit"


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS naese_slot_core_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            ordered_core_book_count INTEGER NOT NULL,
            variant_book_count INTEGER NOT NULL,
            quarantined_book_count INTEGER NOT NULL,
            ordered_edge_count INTEGER NOT NULL,
            contradiction_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS naese_slot_core_v1_items (
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
    naese_ids = sorted(
        [bookid for bookid, book in books.items() if any("NAESE" in node or "R02" in node for node in set(book.accepted) | set(book.audit) | set(book.scoped)) or "NAESE" in book.literal],
        key=int,
    )
    book_items = {}
    for bookid in naese_ids:
        status, role, interp = classify_book(bookid)
        if status == "OUT_OF_SCOPE":
            status = "QUARANTINED"
        book_items[bookid] = {"status": status, "role": role, "interpretation": interp, "states": sorted(states[bookid]), "nodes": sorted(set(books[bookid].accepted) | set(books[bookid].audit) | set(books[bookid].scoped))}
    edge_items = {}
    contradictions = []
    for edge, role in ORDERED_EDGES.items():
        payload = edge_score(books[edge[0]], books[edge[1]], states)
        # 67->2 is cross-family context-to-slot; 51->53 is a same-function R02 bridge.
        if role == "R02_BRIDGE_PAIR_CONTIG":
            gate = payload["prior"] >= 0.90 and payload["score"] >= 100
        else:
            gate = (payload["overlap"] >= 30 or payload["prior"] >= 1.0) and payload["score"] >= 90
        status = "ORDERED_EDGE_ACCEPTED_NO_GLOSS" if gate else "ORDERED_EDGE_FAILED_GATE"
        if not gate:
            contradictions.append(f"{edge[0]}->{edge[1]}")
        edge_items[f"{edge[0]}->{edge[1]}"] = {"status": status, "role": role, "interpretation": "accepted NAESE/context structural edge; no human gloss", "evidence": {"score": payload["score"], "overlap": payload["overlap"], "prior": payload["prior"], "transition": payload["transition"]}}
    # Quarantine broad surface and variant cross-edges.
    for source in sorted(naese_ids, key=int):
        for target in sorted(naese_ids, key=int):
            if source == target or (source, target) in ORDERED_EDGES:
                continue
            payload = edge_score(books[source], books[target], states)
            if payload["score"] >= 100 or payload["overlap"] >= 24:
                edge_items.setdefault(f"{source}->{target}", {"status": "QUARANTINED_NAESE_PARALLEL_EDGE", "role": "BROAD_NAESE_PARALLEL_NOT_ORDERED", "interpretation": "NAESE similarity/variant relation is not a continuity or semantic claim", "evidence": {"score": payload["score"], "overlap": payload["overlap"], "prior": payload["prior"], "transition": payload["transition"]}})
    decision = "NAESE_SLOT_CORE_STABLE_VARIANTS_QUARANTINED_NO_GLOSS" if not contradictions else "NAESE_SLOT_CORE_HAS_GATE_FAILURES"
    cur = conn.execute(
        """
        INSERT INTO naese_slot_core_v1_runs
        (created_at, decision, ordered_core_book_count, variant_book_count, quarantined_book_count, ordered_edge_count, contradiction_count, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            now(), decision,
            sum(1 for i in book_items.values() if i["status"] == "ORDERED_CORE"),
            sum(1 for i in book_items.values() if i["status"] == "VARIANT"),
            sum(1 for i in book_items.values() if i["status"] == "QUARANTINED"),
            len(ORDERED_EDGES), len(contradictions),
            json.dumps({"contradictions": contradictions, "ordered_edges": sorted([f"{a}->{b}" for a,b in ORDERED_EDGES])}, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)
    for bookid, item in book_items.items():
        conn.execute("""INSERT INTO naese_slot_core_v1_items (run_id,item_type,item_id,status,role_label,interpretation,evidence_json) VALUES (?,?,?,?,?,?,?)""", (run_id, "book", bookid, item["status"], item["role"], item["interpretation"], json.dumps({"states": item["states"], "nodes": item["nodes"]}, sort_keys=True)))
    for edge, item in edge_items.items():
        conn.execute("""INSERT INTO naese_slot_core_v1_items (run_id,item_type,item_id,status,role_label,interpretation,evidence_json) VALUES (?,?,?,?,?,?,?)""", (run_id, "edge", edge, item["status"], item["role"], item["interpretation"], json.dumps(item["evidence"], sort_keys=True)))
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": decision, "ordered_core_book_count": sum(1 for i in book_items.values() if i["status"] == "ORDERED_CORE"), "variant_book_count": sum(1 for i in book_items.values() if i["status"] == "VARIANT"), "quarantined_book_count": sum(1 for i in book_items.values() if i["status"] == "QUARANTINED"), "ordered_edge_count": len(ORDERED_EDGES), "contradiction_count": len(contradictions)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
