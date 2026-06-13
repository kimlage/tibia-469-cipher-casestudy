#!/usr/bin/env python3
"""VINVIN/C86/R20 branch-core audit.

Separates ordered branch edges from C86/VNCTIIN context payloads, VFETTIIT variants,
and negative/mixed controls. Structural only; no human semantic gloss.
"""

from __future__ import annotations

import datetime as dt
import json
import sqlite3

from sqlite_operational_grammar_reconstruction_probe import DB, classify_states, edge_score, load_books

R20_BRANCH = {"29", "61", "65"}
C86_VINVIN_BRANCH = {"3", "17", "52", "62"}
C86_VNCTIIN_CONTEXT = {"2", "10", "27", "35", "67"}
C86_SURFACE = {"44"}
NEGATIVE_CONTROL = {"68"}
MIXED_AUDIT = {"4"}
VFETTIIT_VARIANT = {"15", "16"}
ORDERED_EDGES = {
    ("29", "65"): "VINVIN_R20_TO_CONNECTOR_CONTIG",
    ("52", "62"): "C86_VINVIN_PAYLOAD_PAIR_CONTIG",
    ("3", "17"): "C86_VINVIN_VARIANT_CHAIN_HEAD",
    ("17", "62"): "C86_VINVIN_VARIANT_CHAIN_ENDPOINT",
}


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def classify_book(bookid: str) -> tuple[str, str, str]:
    if bookid in R20_BRANCH:
        role = "R20_CONNECTOR_ENDPOINT" if bookid == "65" else "R20_BRANCH_HEAD"
        return "ORDERED_CORE", role, "VINVIN/R20 branch; 65 adds long connector"
    if bookid in C86_VINVIN_BRANCH:
        return "ORDERED_CORE", "C86_VINVIN_BRANCH_PAYLOAD", "C86/VINVIN payload branch"
    if bookid in C86_VNCTIIN_CONTEXT:
        return "RELATED_CONTEXT", "C86_VNCTIIN_CONTEXT_PAYLOAD", "C86 operator in VNCTIIN context, not VINVIN branch"
    if bookid in C86_SURFACE:
        return "QUARANTINED", "C86_SURFACE_FRAGMENT", "C86/VINVIN-like surface without accepted branch role"
    if bookid in NEGATIVE_CONTROL:
        return "QUARANTINED", "VINVIN_NEGATIVE_CONTROL", "negative/control window; not promoted to ordered branch"
    if bookid in MIXED_AUDIT:
        return "AUDIT_ONLY", "MIXED_VINVIN_ONAF", "mixed VINVIN/ONAF audit case"
    if bookid in VFETTIIT_VARIANT:
        return "AUDIT_ONLY", "VFETTIIT_VTLRNEFIE_VARIANT", "moderate VTLRNEFIE/VFETTIIT variant outside core"
    return "OUT_OF_SCOPE", "OTHER", "not part of VINVIN branch audit"


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS vinvin_branch_core_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            ordered_core_book_count INTEGER NOT NULL,
            related_context_book_count INTEGER NOT NULL,
            quarantined_book_count INTEGER NOT NULL,
            ordered_edge_count INTEGER NOT NULL,
            contradiction_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS vinvin_branch_core_v1_items (
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
    focus_ids = sorted(
        [bookid for bookid, book in books.items() if any(x in node for node in set(book.accepted) | set(book.audit) | set(book.scoped) for x in ("VINVIN", "C86", "R20", "VFETTIIT", "VTLRNEFIE")) or "VINVIN" in book.literal or "VTLRNEFIE" in book.literal],
        key=int,
    )
    book_items = {}
    for bookid in focus_ids:
        status, role, interp = classify_book(bookid)
        if status == "OUT_OF_SCOPE":
            status = "QUARANTINED"
        book_items[bookid] = {"status": status, "role": role, "interpretation": interp, "states": sorted(states[bookid]), "nodes": sorted(set(books[bookid].accepted) | set(books[bookid].audit) | set(books[bookid].scoped))}
    edge_items = {}
    contradictions = []
    for edge, role in ORDERED_EDGES.items():
        payload = edge_score(books[edge[0]], books[edge[1]], states)
        # VINVIN edges can be confirmed by either literal overlap or strong same-branch functional prior.
        gate = payload["score"] >= 90 and (payload["overlap"] >= 8 or payload["prior"] >= 0.86)
        status = "ORDERED_EDGE_ACCEPTED_NO_GLOSS" if gate else "ORDERED_EDGE_FAILED_GATE"
        if not gate:
            contradictions.append(f"{edge[0]}->{edge[1]}")
        edge_items[f"{edge[0]}->{edge[1]}"] = {"status": status, "role": role, "interpretation": "accepted VINVIN branch structural edge; no human gloss", "evidence": {"score": payload["score"], "overlap": payload["overlap"], "prior": payload["prior"], "transition": payload["transition"]}}
    for source in sorted(focus_ids, key=int):
        for target in sorted(focus_ids, key=int):
            if source == target or (source, target) in ORDERED_EDGES:
                continue
            payload = edge_score(books[source], books[target], states)
            if payload["score"] >= 100 or payload["overlap"] >= 24:
                edge_items.setdefault(f"{source}->{target}", {"status": "QUARANTINED_VINVIN_PARALLEL_EDGE", "role": "BROAD_VINVIN_OR_C86_PARALLEL_NOT_ORDERED", "interpretation": "branch similarity is not a continuity or semantic claim", "evidence": {"score": payload["score"], "overlap": payload["overlap"], "prior": payload["prior"], "transition": payload["transition"]}})
    decision = "VINVIN_BRANCH_CORE_STABLE_PARALLELS_QUARANTINED_NO_GLOSS" if not contradictions else "VINVIN_BRANCH_CORE_HAS_GATE_FAILURES"
    cur = conn.execute(
        """
        INSERT INTO vinvin_branch_core_v1_runs
        (created_at, decision, ordered_core_book_count, related_context_book_count, quarantined_book_count, ordered_edge_count, contradiction_count, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (now(), decision, sum(1 for i in book_items.values() if i["status"] == "ORDERED_CORE"), sum(1 for i in book_items.values() if i["status"] == "RELATED_CONTEXT"), sum(1 for i in book_items.values() if i["status"] in {"QUARANTINED", "AUDIT_ONLY"}), len(ORDERED_EDGES), len(contradictions), json.dumps({"contradictions": contradictions, "ordered_edges": sorted([f"{a}->{b}" for a,b in ORDERED_EDGES])}, sort_keys=True)),
    )
    run_id = int(cur.lastrowid)
    for bookid, item in book_items.items():
        conn.execute("""INSERT INTO vinvin_branch_core_v1_items (run_id,item_type,item_id,status,role_label,interpretation,evidence_json) VALUES (?,?,?,?,?,?,?)""", (run_id, "book", bookid, item["status"], item["role"], item["interpretation"], json.dumps({"states": item["states"], "nodes": item["nodes"]}, sort_keys=True)))
    for edge, item in edge_items.items():
        conn.execute("""INSERT INTO vinvin_branch_core_v1_items (run_id,item_type,item_id,status,role_label,interpretation,evidence_json) VALUES (?,?,?,?,?,?,?)""", (run_id, "edge", edge, item["status"], item["role"], item["interpretation"], json.dumps(item["evidence"], sort_keys=True)))
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": decision, "ordered_core_book_count": sum(1 for i in book_items.values() if i["status"] == "ORDERED_CORE"), "related_context_book_count": sum(1 for i in book_items.values() if i["status"] == "RELATED_CONTEXT"), "quarantined_or_audit_book_count": sum(1 for i in book_items.values() if i["status"] in {"QUARANTINED", "AUDIT_ONLY"}), "ordered_edge_count": len(ORDERED_EDGES), "contradiction_count": len(contradictions), "contradictions": contradictions}, ensure_ascii=False))


if __name__ == "__main__":
    main()
