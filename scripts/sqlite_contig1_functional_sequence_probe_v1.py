#!/usr/bin/env python3
"""Probe Q2: functional sequence for contig1 without prose gloss."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

SEQUENCES = {
    "canonical_contig1": ["58", "35", "67", "2"],
    "shadow_handoff_a": ["10", "67", "2"],
    "shadow_payload_a": ["35", "27"],
    "direct_skip_control": ["58", "2"],
    "formula_to_payload_control": ["58", "67"],
}

EXPECTED_ROLE_BY_BOOK = {
    "58": "FRAME_FORMULA_OPERATOR",
    "35": "HANDOFF_CONTEXT",
    "67": "CONTEXT_PAYLOAD",
    "2": "CANONICAL_SLOT",
    "10": "HANDOFF_CONTEXT_SHADOW",
    "27": "CONTEXT_PAYLOAD_SHADOW",
}

EXPECTED_TRANSITIONS = {
    "58->35": "FRAME_TO_HANDOFF",
    "35->67": "HANDOFF_TO_PAYLOAD",
    "67->2": "PAYLOAD_TO_SLOT",
    "10->67": "SHADOW_HANDOFF_TO_PAYLOAD",
    "35->27": "HANDOFF_TO_PAYLOAD_SHADOW",
}

NEGATIVE_TRANSITIONS = {"58->2", "58->67"}


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_edge_status(conn: sqlite3.Connection) -> dict[str, str]:
    run_id = conn.execute("SELECT max(run_id) FROM functional_grammar_synthesis_v1_runs").fetchone()[0]
    out = {}
    for row in conn.execute("SELECT item_id,status FROM functional_grammar_synthesis_v1_items WHERE run_id=? AND item_type='edge'", (run_id,)):
        out[str(row["item_id"])] = str(row["status"])
    return out


def evaluate_sequence(name: str, seq: list[str], edge_status: dict[str, str]) -> dict:
    roles = [EXPECTED_ROLE_BY_BOOK.get(book, "UNKNOWN") for book in seq]
    edges = [f"{a}->{b}" for a, b in zip(seq, seq[1:])]
    accepted = []
    rejected = []
    unresolved = []
    for edge in edges:
        if edge in EXPECTED_TRANSITIONS and edge_status.get(edge, "").startswith("ACCEPTED"):
            accepted.append(edge)
        elif edge in NEGATIVE_TRANSITIONS:
            rejected.append(edge)
        else:
            unresolved.append(edge)
    if name == "canonical_contig1" and len(accepted) == 3 and not unresolved:
        status = "CANONICAL_SEQUENCE_ACCEPTED_NO_PROSE"
    elif name.startswith("shadow") and accepted and not unresolved:
        status = "SHADOW_SEQUENCE_COMPATIBLE_NO_PROSE"
    elif rejected and not accepted:
        status = "NEGATIVE_CONTROL_REJECTED"
    else:
        status = "SEQUENCE_UNRESOLVED_OR_PARTIAL"
    return {"name": name, "sequence": seq, "roles": roles, "edges": edges, "accepted": accepted, "rejected": rejected, "unresolved": unresolved, "status": status}


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS contig1_functional_sequence_probe_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            canonical_edge_accept_count INTEGER NOT NULL,
            negative_control_reject_count INTEGER NOT NULL,
            accepted_prose_gloss INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS contig1_functional_sequence_probe_v1_items (
            run_id INTEGER NOT NULL,
            sequence_id TEXT NOT NULL,
            status TEXT NOT NULL,
            sequence_json TEXT NOT NULL,
            roles_json TEXT NOT NULL,
            accepted_edges_json TEXT NOT NULL,
            rejected_edges_json TEXT NOT NULL,
            unresolved_edges_json TEXT NOT NULL,
            PRIMARY KEY (run_id, sequence_id)
        )
        """
    )
    edge_status = load_edge_status(conn)
    results = [evaluate_sequence(name, seq, edge_status) for name, seq in SEQUENCES.items()]
    canonical = next(r for r in results if r["name"] == "canonical_contig1")
    negative_reject_count = sum(1 for r in results if r["status"] == "NEGATIVE_CONTROL_REJECTED")
    if canonical["status"] == "CANONICAL_SEQUENCE_ACCEPTED_NO_PROSE" and negative_reject_count == 2:
        decision = "Q2_FRAME_HANDOFF_PAYLOAD_SLOT_SEQUENCE_ACCEPTED_NO_PROSE_GLOSS"
    else:
        decision = "Q2_SEQUENCE_REMAINS_PARTIAL"
    cur = conn.execute(
        """
        INSERT INTO contig1_functional_sequence_probe_v1_runs
        (created_at, decision, canonical_edge_accept_count, negative_control_reject_count, accepted_prose_gloss, payload_json)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (now(), decision, len(canonical["accepted"]), negative_reject_count, 0, json.dumps({"expected_transitions": EXPECTED_TRANSITIONS, "negative_transitions": sorted(NEGATIVE_TRANSITIONS)}, sort_keys=True)),
    )
    run_id = int(cur.lastrowid)
    for r in results:
        conn.execute(
            """
            INSERT INTO contig1_functional_sequence_probe_v1_items
            (run_id, sequence_id, status, sequence_json, roles_json, accepted_edges_json, rejected_edges_json, unresolved_edges_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, r["name"], r["status"], json.dumps(r["sequence"], sort_keys=True), json.dumps(r["roles"], sort_keys=True), json.dumps(r["accepted"], sort_keys=True), json.dumps(r["rejected"], sort_keys=True), json.dumps(r["unresolved"], sort_keys=True)),
        )
    conn.execute(
        """
        INSERT OR REPLACE INTO semantic_question_result_v1_items
        (run_id, question_id, status, answer_type, answer_label, accepted_prose_gloss, evidence_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (run_id, "Q2_HANDOFF_TO_CONTEXT_PAYLOAD", decision, "FUNCTIONAL_SEQUENCE_CONSTRAINT", "FRAME_FORMULA_OPERATOR -> HANDOFF_CONTEXT -> CONTEXT_PAYLOAD -> CANONICAL_SLOT", 0, json.dumps({"canonical_edges": canonical["accepted"], "negative_control_reject_count": negative_reject_count}, sort_keys=True)),
    )
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": decision, "canonical_roles": canonical["roles"], "canonical_edges": canonical["accepted"], "negative_control_reject_count": negative_reject_count, "accepted_prose_gloss": 0}, ensure_ascii=False))


if __name__ == "__main__":
    main()
