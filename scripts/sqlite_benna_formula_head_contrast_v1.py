#!/usr/bin/env python3
"""Contrast BENNA formula/template heads after discovering 69->35."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3

from sqlite_operational_grammar_reconstruction_probe import DB, classify_states, edge_score, load_books

FOCUS = ["47", "40", "58", "69", "35"]
EDGES = [("47", "40"), ("58", "35"), ("69", "35"), ("69", "40"), ("58", "69"), ("47", "35")]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def classify_role(bookid: str, states: set[str]) -> tuple[str, str]:
    if bookid == "35":
        return "BENNA_HANDOFF_CONTEXT", "receives formula/display head and continues into context payload"
    if bookid == "40":
        return "BENNA_FORMULA_BODY", "receives template head but does not carry context payload"
    if bookid == "47":
        return "BENNA_TEMPLATE_HEAD", "template-only head into formula body"
    if bookid == "58":
        return "BENNA_DISPLAY_FORMULA_HEAD", "formula/display head into handoff context"
    if bookid == "69":
        return "BENNA_MIXED_TEMPLATE_FORMULA_HEAD", "template plus formula head; alternate path into handoff context"
    if "BENNA_TEMPLATE" in states and "FORMULA_POOL" in states:
        return "BENNA_MIXED_TEMPLATE_FORMULA_HEAD", "mixed template/formula structural role"
    if "BENNA_TEMPLATE" in states:
        return "BENNA_TEMPLATE_HEAD", "template structural role"
    if "FORMULA_POOL" in states:
        return "BENNA_FORMULA_BODY_OR_HEAD", "formula structural role"
    return "OTHER", "outside BENNA focus set"


def main() -> None:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS benna_formula_head_contrast_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            role_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS benna_formula_head_contrast_v1_items (
            run_id INTEGER NOT NULL,
            item_type TEXT NOT NULL,
            item_id TEXT NOT NULL,
            role_label TEXT NOT NULL,
            interpretation TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, item_type, item_id)
        )
        """
    )
    books = load_books(conn)
    states = {bookid: classify_states(book) for bookid, book in books.items()}
    book_roles = {}
    for bookid in FOCUS:
        role, interp = classify_role(bookid, states[bookid])
        book_roles[bookid] = {"role": role, "interpretation": interp, "states": sorted(states[bookid])}
    edge_roles = {}
    for edge in EDGES:
        payload = edge_score(books[edge[0]], books[edge[1]], states)
        if edge == ("58", "35"):
            role = "CANONICAL_DISPLAY_HEAD_TO_CONTEXT"
            interp = "strongest BENNA formula/display route into book35 handoff context"
        elif edge == ("69", "35"):
            role = "ALTERNATE_MIXED_HEAD_TO_CONTEXT"
            interp = "alternate mixed template+formula route into book35; alive no gloss"
        elif edge == ("47", "40"):
            role = "TEMPLATE_HEAD_TO_FORMULA_BODY"
            interp = "separate template-to-formula-body path"
        elif edge == ("69", "40"):
            role = "WEAK_PRIOR_ONLY_TEMPLATE_TO_BODY"
            interp = "structural prior exists but no literal overlap; quarantine"
        elif edge == ("47", "35"):
            role = "WEAK_TEMPLATE_TO_CONTEXT_CONTROL"
            interp = "tests whether template can skip formula body; should remain audit/control unless stronger evidence appears"
        else:
            role = "NEGATIVE_ORIENTATION_CONTROL"
            interp = "reverse/unsupported orientation control"
        edge_roles[f"{edge[0]}->{edge[1]}"] = {"role": role, "interpretation": interp, "score": payload["score"], "overlap": payload["overlap"], "prior": payload["prior"], "transition": payload["transition"]}
    decision = "BENNA_SPLIT_INTO_TEMPLATE_BODY_DISPLAY_AND_MIXED_HEADS_NO_GLOSS"
    cur = conn.execute(
        """
        INSERT INTO benna_formula_head_contrast_v1_runs
        (created_at, decision, role_count, payload_json)
        VALUES (?, ?, ?, ?)
        """,
        (
            now(),
            decision,
            len(set(x["role"] for x in book_roles.values())),
            json.dumps({"book_roles": book_roles, "edge_roles": edge_roles}, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)
    for bookid, payload in book_roles.items():
        conn.execute(
            """
            INSERT INTO benna_formula_head_contrast_v1_items
            (run_id, item_type, item_id, role_label, interpretation, evidence_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (run_id, "book", bookid, payload["role"], payload["interpretation"], json.dumps({"states": payload["states"]}, sort_keys=True)),
        )
    for edge, payload in edge_roles.items():
        conn.execute(
            """
            INSERT INTO benna_formula_head_contrast_v1_items
            (run_id, item_type, item_id, role_label, interpretation, evidence_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                "edge",
                edge,
                payload["role"],
                payload["interpretation"],
                json.dumps({k: payload[k] for k in ("score", "overlap", "prior", "transition")}, sort_keys=True),
            ),
        )
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": decision, "book_roles": book_roles, "edge_roles": edge_roles}, ensure_ascii=False))


if __name__ == "__main__":
    main()
