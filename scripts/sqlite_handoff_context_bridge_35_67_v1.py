#!/usr/bin/env python3
"""Probe missing functional grammar edge 35->67.

This edge is the only contig transition not covered by functional_grammar_synthesis_v1.
It tests whether book35 handoff/context legitimately bridges into book67 C86/VNCTIIN
payload, without assigning human semantics.
"""

from __future__ import annotations

import datetime as dt
import json
import sqlite3

from sqlite_operational_grammar_reconstruction_probe import DB, classify_states, edge_score, load_books, max_suffix_prefix_overlap

TARGET = ("35", "67")
CONTROLS = [("10", "67"), ("35", "27"), ("58", "67"), ("69", "67"), ("35", "2"), ("67", "2")]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def lcs_len(a: str, b: str) -> int:
    best = 0
    prev = [0] * (len(b) + 1)
    for ca in a:
        cur = [0]
        for j, cb in enumerate(b, start=1):
            val = prev[j - 1] + 1 if ca == cb else 0
            cur.append(val)
            if val > best:
                best = val
        prev = cur
    return best


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS handoff_context_bridge_35_67_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            target_score REAL NOT NULL,
            target_overlap INTEGER NOT NULL,
            best_control_score REAL NOT NULL,
            payload_json TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS handoff_context_bridge_35_67_v1_items (
            run_id INTEGER NOT NULL,
            edge TEXT NOT NULL,
            role TEXT NOT NULL,
            status TEXT NOT NULL,
            score REAL NOT NULL,
            overlap INTEGER NOT NULL,
            lcs INTEGER NOT NULL,
            prior REAL NOT NULL,
            transition_json TEXT NOT NULL,
            states_json TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
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
        lcs = lcs_len(books[edge[0]].literal, books[edge[1]].literal)
        role = "target" if edge == TARGET else "control"
        details.append({"edge": edge, "role": role, "payload": payload, "lcs": lcs, "states": {"source": sorted(states[edge[0]]), "target": sorted(states[edge[1]])}})
    target = next(d for d in details if d["role"] == "target")
    controls = [d for d in details if d["role"] == "control"]
    best_control_score = max(float(d["payload"]["score"]) for d in controls)
    # Accept if target has direct suffix-prefix continuity and expected state progression.
    target_states = target["states"]
    has_expected_progression = "HANDOFF_CONTEXT" in target_states["source"] and "CONTEXT_PAYLOAD" in target_states["target"]
    target_score = float(target["payload"]["score"])
    target_overlap = int(target["payload"]["overlap"])
    if has_expected_progression and target_overlap >= 24 and target_score >= 100:
        decision = "HANDOFF_CONTEXT_35_TO_67_ACCEPTED_NO_GLOSS"
    elif has_expected_progression and target_score >= 90:
        decision = "HANDOFF_CONTEXT_35_TO_67_WEAK_AUDIT_ONLY"
    else:
        decision = "HANDOFF_CONTEXT_35_TO_67_REJECTED"
    cur = conn.execute(
        """
        INSERT INTO handoff_context_bridge_35_67_v1_runs
        (created_at, decision, target_score, target_overlap, best_control_score, payload_json)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (now(), decision, target_score, target_overlap, best_control_score, json.dumps({"interpretation": "tests missing BENNA/context to C86/VNCTIIN payload bridge; no gloss", "controls": [f"{a}->{b}" for a,b in CONTROLS]}, sort_keys=True)),
    )
    run_id = int(cur.lastrowid)
    for d in details:
        edge = f"{d['edge'][0]}->{d['edge'][1]}"
        p = d["payload"]
        status = "TARGET_ACCEPTED" if d["role"] == "target" and decision.startswith("HANDOFF_CONTEXT_35_TO_67_ACCEPTED") else ("TARGET_NOT_ACCEPTED" if d["role"] == "target" else "CONTROL")
        conn.execute(
            """
            INSERT INTO handoff_context_bridge_35_67_v1_items
            (run_id, edge, role, status, score, overlap, lcs, prior, transition_json, states_json, evidence_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, edge, d["role"], status, p["score"], p["overlap"], d["lcs"], p["prior"], json.dumps(p["transition"], sort_keys=True), json.dumps(d["states"], sort_keys=True), json.dumps({"expected_progression": "HANDOFF_CONTEXT -> CONTEXT_PAYLOAD"}, sort_keys=True)),
        )
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": decision, "target_score": target_score, "target_overlap": target_overlap, "best_control_score": best_control_score, "details": [{"edge": f"{d['edge'][0]}->{d['edge'][1]}", "role": d["role"], "score": d["payload"]["score"], "overlap": d["payload"]["overlap"], "lcs": d["lcs"], "transition": d["payload"]["transition"]} for d in details]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
