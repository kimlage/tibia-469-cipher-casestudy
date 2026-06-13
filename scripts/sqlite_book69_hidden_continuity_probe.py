#!/usr/bin/env python3
"""Probe the only high-overlap non-contig edge from pruned grammar audit: 69->35."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3

from sqlite_operational_grammar_reconstruction_probe import DB, classify_states, edge_score, load_books, max_suffix_prefix_overlap

TARGET = ("69", "35")
CONTROLS = [("58", "35"), ("47", "40"), ("69", "40"), ("58", "69")]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def shared_suffix_prefix(left: str, right: str, size: int) -> str:
    if size <= 0:
        return ""
    return left[-size:]


def main() -> None:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS book69_hidden_continuity_probe_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            target_overlap INTEGER NOT NULL,
            best_control_overlap INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS book69_hidden_continuity_probe_items (
            run_id INTEGER NOT NULL,
            edge TEXT NOT NULL,
            role TEXT NOT NULL,
            score REAL NOT NULL,
            overlap INTEGER NOT NULL,
            prior REAL NOT NULL,
            transition_json TEXT NOT NULL,
            states_json TEXT NOT NULL,
            overlap_text TEXT NOT NULL,
            PRIMARY KEY (run_id, edge)
        )
        """
    )
    books = load_books(conn)
    states = {bookid: classify_states(book) for bookid, book in books.items()}
    edges = [TARGET] + CONTROLS
    details = []
    for edge in edges:
        payload = edge_score(books[edge[0]], books[edge[1]], states)
        details.append(
            {
                "edge": edge,
                "role": "target" if edge == TARGET else "control",
                "payload": payload,
                "overlap_text": shared_suffix_prefix(books[edge[0]].literal, books[edge[1]].literal, int(payload["overlap"])),
                "states": {"source": sorted(states[edge[0]]), "target": sorted(states[edge[1]])},
            }
        )
    target_overlap = next(d for d in details if d["role"] == "target")["payload"]["overlap"]
    best_control_overlap = max(d["payload"]["overlap"] for d in details if d["role"] == "control")
    book69_states = states["69"]
    if target_overlap >= 40 and "BENNA_TEMPLATE" in book69_states and "FORMULA_POOL" in states["35"]:
        decision = "BOOK69_ALT_FORMULA_HEAD_TO_35_ALIVE_STRUCTURAL_NO_GLOSS"
    elif target_overlap >= best_control_overlap:
        decision = "BOOK69_35_HIDDEN_CONTINUITY_AUDIT_ONLY"
    else:
        decision = "BOOK69_35_NOT_STRONGER_THAN_CONTROLS"
    cur = conn.execute(
        """
        INSERT INTO book69_hidden_continuity_probe_runs
        (created_at, decision, target_overlap, best_control_overlap, payload_json)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            now(),
            decision,
            int(target_overlap),
            int(best_control_overlap),
            json.dumps(
                {
                    "interpretation": "69 is tested as an alternate formula/template head into book35; no human gloss accepted",
                    "book69_states": sorted(book69_states),
                },
                sort_keys=True,
            ),
        ),
    )
    run_id = int(cur.lastrowid)
    for d in details:
        edge_label = f"{d['edge'][0]}->{d['edge'][1]}"
        p = d["payload"]
        conn.execute(
            """
            INSERT INTO book69_hidden_continuity_probe_items
            (run_id, edge, role, score, overlap, prior, transition_json, states_json, overlap_text)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                edge_label,
                d["role"],
                p["score"],
                p["overlap"],
                p["prior"],
                json.dumps(p["transition"], sort_keys=True),
                json.dumps(d["states"], sort_keys=True),
                d["overlap_text"],
            ),
        )
    conn.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "target_overlap": target_overlap,
                "best_control_overlap": best_control_overlap,
                "details": [
                    {
                        "edge": f"{d['edge'][0]}->{d['edge'][1]}",
                        "role": d["role"],
                        "score": d["payload"]["score"],
                        "overlap": d["payload"]["overlap"],
                        "transition": d["payload"]["transition"],
                        "states": d["states"],
                    }
                    for d in details
                ],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
