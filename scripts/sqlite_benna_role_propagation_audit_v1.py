#!/usr/bin/env python3
"""Propagate BENNA functional roles to all BENNA-bearing books and audit contradictions.

The purpose is to test whether the BENNA role split is stable beyond the seed
books 47/40/58/69/35. This creates a no-gloss structural audit layer only.
"""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

from sqlite_operational_grammar_reconstruction_probe import DB, classify_states, edge_score, load_books

BENNA_NODE_TO_ROLE = {
    "BENNA_IAVNALLBEE_TEMPLATE_WINDOW": "TEMPLATE_HEAD",
    "BENNA_FORMULA_BRIDGE": "FORMULA_CORE",
    "BENNA_LTAST_BOUNDARY_WINDOW": "LTAST_BOUNDARY_TAIL",
    "BENNA_NSBVN_DISPLAY_WINDOW": "DISPLAY_WINDOW",
    "BENNA_BOOK6_CONTINUITY_AUDIT": "CONTINUITY_AUDIT",
}

ROLE_EXPECTED_TRANSITIONS = {
    "TEMPLATE_HEAD": {"FORMULA_CORE", "FORMULA_BODY", "HANDOFF_CONTEXT", "MIXED_TEMPLATE_FORMULA"},
    "FORMULA_CORE": {"HANDOFF_CONTEXT", "FORMULA_BODY", "CONTEXT_PAYLOAD", "LTAST_BOUNDARY_TAIL"},
    "DISPLAY_WINDOW": {"FORMULA_CORE", "HANDOFF_CONTEXT", "LTAST_BOUNDARY_TAIL"},
    "LTAST_BOUNDARY_TAIL": {"HANDOFF_CONTEXT", "CONTEXT_PAYLOAD", "NAESE_SLOT", "LTAST_BOUNDARY_TAIL"},
    "MIXED_TEMPLATE_FORMULA": {"HANDOFF_CONTEXT", "FORMULA_BODY", "CONTEXT_PAYLOAD"},
}


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def roles_for_book(bookid: str, book, states: set[str]) -> set[str]:
    nodes = set(book.accepted) | set(book.audit) | set(book.scoped)
    roles = {role for node, role in BENNA_NODE_TO_ROLE.items() if node in nodes}
    if "BENNA_TEMPLATE" in states and "FORMULA_POOL" in states:
        roles.add("MIXED_TEMPLATE_FORMULA")
    elif "BENNA_TEMPLATE" in states:
        roles.add("TEMPLATE_HEAD")
    if "FORMULA_POOL" in states and "HANDOFF_CONTEXT" in states:
        roles.add("HANDOFF_CONTEXT")
    elif "FORMULA_POOL" in states and roles == {"FORMULA_CORE"}:
        roles.add("FORMULA_BODY")
    if "CONTEXT_PAYLOAD" in states:
        roles.add("CONTEXT_PAYLOAD")
    if "NAESE_SLOT" in states:
        roles.add("NAESE_SLOT")
    return roles


def dominant_role(roles: set[str]) -> str:
    priority = [
        "MIXED_TEMPLATE_FORMULA",
        "HANDOFF_CONTEXT",
        "TEMPLATE_HEAD",
        "DISPLAY_WINDOW",
        "FORMULA_BODY",
        "FORMULA_CORE",
        "LTAST_BOUNDARY_TAIL",
        "CONTEXT_PAYLOAD",
        "NAESE_SLOT",
        "CONTINUITY_AUDIT",
    ]
    for role in priority:
        if role in roles:
            return role
    return "OTHER"


def classify_book_status(bookid: str, roles: set[str]) -> tuple[str, str]:
    if "CONTINUITY_AUDIT" in roles:
        return "AUDIT_ONLY", "book carries BENNA continuity signal but is already marked unique/audit"
    if {"TEMPLATE_HEAD", "FORMULA_CORE", "LTAST_BOUNDARY_TAIL"}.issubset(roles):
        return "MIXED_HEAD_ALIVE", "template + formula + LTAST tail; compatible with alternate head behavior"
    if "HANDOFF_CONTEXT" in roles and "CONTEXT_PAYLOAD" in roles:
        return "HANDOFF_CONTEXT_ALIVE", "formula core continues into payload/context"
    if "DISPLAY_WINDOW" in roles and "LTAST_BOUNDARY_TAIL" in roles:
        return "DISPLAY_TAIL_ALIVE", "display/formula window with LTAST tail"
    if "TEMPLATE_HEAD" in roles and "FORMULA_CORE" not in roles:
        return "TEMPLATE_HEAD_ALIVE", "template head without full formula core"
    if "FORMULA_CORE" in roles:
        return "FORMULA_CORE_ALIVE", "formula core without accepted context payload"
    if "LTAST_BOUNDARY_TAIL" in roles:
        return "BOUNDARY_TAIL_ALIVE", "LTAST boundary/tail only"
    return "UNCLASSIFIED", "BENNA surface appears but no accepted BENNA role captured"


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS benna_role_propagation_audit_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            benna_book_count INTEGER NOT NULL,
            contradiction_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS benna_role_propagation_audit_v1_items (
            run_id INTEGER NOT NULL,
            item_type TEXT NOT NULL,
            item_id TEXT NOT NULL,
            status TEXT NOT NULL,
            dominant_role TEXT NOT NULL,
            roles_json TEXT NOT NULL,
            interpretation TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, item_type, item_id)
        )
        """
    )
    books = load_books(conn)
    states = {bookid: classify_states(book) for bookid, book in books.items()}
    benna_books = {}
    for bookid, book in books.items():
        nodes = set(book.accepted) | set(book.audit) | set(book.scoped)
        if any("BENNA" in node for node in nodes) or "BENNA" in book.literal:
            roles = roles_for_book(bookid, book, states[bookid])
            status, interp = classify_book_status(bookid, roles)
            benna_books[bookid] = {
                "roles": sorted(roles),
                "dominant": dominant_role(roles),
                "status": status,
                "interpretation": interp,
                "nodes": sorted(nodes),
            }

    edge_items = {}
    contradictions = []
    ids = sorted(benna_books, key=int)
    for left in ids:
        for right in ids:
            if left == right:
                continue
            payload = edge_score(books[left], books[right], states)
            if payload["score"] < 100 and payload["overlap"] < 24:
                continue
            left_dom = benna_books[left]["dominant"]
            right_roles = set(benna_books[right]["roles"])
            expected = ROLE_EXPECTED_TRANSITIONS.get(left_dom, set())
            compatible = bool(expected & right_roles) or payload["overlap"] >= 40
            status = "COMPATIBLE_EDGE" if compatible else "CONTRADICTION_EDGE"
            if status == "CONTRADICTION_EDGE":
                contradictions.append(f"{left}->{right}")
            edge_items[f"{left}->{right}"] = {
                "status": status,
                "dominant_role": f"{left_dom}->{benna_books[right]['dominant']}",
                "roles": {"source": benna_books[left]["roles"], "target": benna_books[right]["roles"]},
                "interpretation": "BENNA role transition is compatible" if compatible else "BENNA role transition lacks role compatibility and should be quarantined",
                "evidence": {"score": payload["score"], "overlap": payload["overlap"], "prior": payload["prior"], "transition": payload["transition"]},
            }

    if not contradictions:
        decision = "BENNA_ROLE_PROPAGATION_STABLE_NO_CONTRADICTIONS_NO_GLOSS"
    elif len(contradictions) <= 3:
        decision = "BENNA_ROLE_PROPAGATION_MOSTLY_STABLE_WITH_AUDIT_EDGES"
    else:
        decision = "BENNA_ROLE_PROPAGATION_UNSTABLE_REQUIRES_REWORK"

    cur = conn.execute(
        """
        INSERT INTO benna_role_propagation_audit_v1_runs
        (created_at, decision, benna_book_count, contradiction_count, payload_json)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            now(),
            decision,
            len(benna_books),
            len(contradictions),
            json.dumps({"contradictions": contradictions, "role_counts": {role: sum(1 for b in benna_books.values() if role in b["roles"]) for role in sorted({r for b in benna_books.values() for r in b["roles"]})}}, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)
    for bookid, item in benna_books.items():
        conn.execute(
            """
            INSERT INTO benna_role_propagation_audit_v1_items
            (run_id, item_type, item_id, status, dominant_role, roles_json, interpretation, evidence_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, "book", bookid, item["status"], item["dominant"], json.dumps(item["roles"], sort_keys=True), item["interpretation"], json.dumps({"nodes": item["nodes"]}, sort_keys=True)),
        )
    for edge, item in edge_items.items():
        conn.execute(
            """
            INSERT INTO benna_role_propagation_audit_v1_items
            (run_id, item_type, item_id, status, dominant_role, roles_json, interpretation, evidence_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, "edge", edge, item["status"], item["dominant_role"], json.dumps(item["roles"], sort_keys=True), item["interpretation"], json.dumps(item["evidence"], sort_keys=True)),
        )
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": decision, "benna_book_count": len(benna_books), "contradiction_count": len(contradictions), "contradictions": contradictions, "book_status_counts": {status: sum(1 for b in benna_books.values() if b["status"] == status) for status in sorted({b["status"] for b in benna_books.values()})}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
