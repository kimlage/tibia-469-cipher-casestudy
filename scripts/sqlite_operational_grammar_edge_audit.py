#!/usr/bin/env python3
"""Audit pruned operational grammar edges.

Classifies selected non-contig edges so the next convergence loop can focus on
specific structural ambiguity instead of reopening broad heuristics.
"""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

from sqlite_operational_grammar_reconstruction_probe import (
    DB,
    classify_states,
    edge_score,
    load_books,
    load_target_edges,
)
from sqlite_operational_grammar_pruning_probe import select_edges


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def classify_edge(edge: tuple[str, str], payload: dict, target_edges: set[tuple[str, str]], states: dict[str, set[str]]) -> tuple[str, str]:
    if edge in target_edges:
        return "KNOWN_CONTIG_EDGE", "preserve_as_positive_structural_continuity"
    left_states = states[edge[0]]
    right_states = states[edge[1]]
    overlap = int(payload["overlap"])
    prior = float(payload["prior"])
    if overlap >= 40:
        return "HIGH_LITERAL_OVERLAP_NONCONTIG", "audit_as_possible_hidden_or_transitive_continuity"
    if left_states & right_states and prior >= 0.86:
        return "SAME_FAMILY_PARALLEL", "quarantine_as_family_parallel_not_ordered_contig"
    if prior >= 1.0 and overlap < 8:
        return "PRIOR_ONLY_LOW_OVERLAP", "downweight_unless_independent_evidence_appears"
    if "FORMULA_POOL" in left_states and ("HANDOFF_CONTEXT" in right_states or "CONTEXT_PAYLOAD" in right_states):
        return "FORMULA_TO_CONTEXT_CANDIDATE", "keep_as_structural_bridge_candidate_no_gloss"
    if "VINVIN_R20_BRANCH" in left_states and "C86_VINVIN_BRANCH" in right_states:
        return "VINVIN_BRANCH_CROSSOVER", "keep_for_branch_semantic_contrast"
    if "CONTEXT_PAYLOAD" in left_states and "NAESE_SLOT" in right_states:
        return "CONTEXT_TO_SLOT_CANDIDATE", "keep_for_slot_function_contrast"
    return "OTHER_STRUCTURAL_PARALLEL", "quarantine_until_more_specific_mechanical_reason"


def main() -> None:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS operational_grammar_edge_audit_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_pruning_run_id INTEGER NOT NULL,
            selected_edge_count INTEGER NOT NULL,
            known_edge_count INTEGER NOT NULL,
            audit_edge_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS operational_grammar_edge_audit_v1_items (
            run_id INTEGER NOT NULL,
            source_bookid TEXT NOT NULL,
            target_bookid TEXT NOT NULL,
            edge_label TEXT NOT NULL,
            next_action TEXT NOT NULL,
            score REAL NOT NULL,
            overlap INTEGER NOT NULL,
            prior REAL NOT NULL,
            transition_json TEXT NOT NULL,
            states_json TEXT NOT NULL,
            PRIMARY KEY (run_id, source_bookid, target_bookid)
        )
        """
    )
    pruning = conn.execute(
        """
        SELECT run_id, best_policy_json FROM operational_grammar_pruning_probe_runs
        WHERE run_id=(SELECT max(run_id) FROM operational_grammar_pruning_probe_runs)
        """
    ).fetchone()
    policy = json.loads(pruning["best_policy_json"])
    books = load_books(conn)
    states = {bookid: classify_states(book) for bookid, book in books.items()}
    target_edges = load_target_edges(conn)
    scores: dict[tuple[str, str], dict] = {}
    for left_id, left in books.items():
        for right_id, right in books.items():
            if left_id == right_id:
                continue
            payload = edge_score(left, right, states)
            if payload["prior"] > 0 or payload["overlap"] >= 12:
                scores[(left_id, right_id)] = payload
    selected = select_edges(
        scores,
        top_k=int(policy["top_k"]),
        min_prior=float(policy["min_prior"]),
        min_overlap=int(policy["min_overlap"]),
        min_score=float(policy["min_score"]),
    )
    labels: dict[str, int] = {}
    rows = []
    for edge in sorted(selected, key=lambda e: (int(e[0]), int(e[1]))):
        payload = scores[edge]
        label, next_action = classify_edge(edge, payload, target_edges, states)
        labels[label] = labels.get(label, 0) + 1
        rows.append((edge, payload, label, next_action))
    cur = conn.execute(
        """
        INSERT INTO operational_grammar_edge_audit_v1_runs
        (created_at, source_pruning_run_id, selected_edge_count, known_edge_count, audit_edge_count, payload_json)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            now(),
            int(pruning["run_id"]),
            len(selected),
            sum(1 for edge in selected if edge in target_edges),
            sum(1 for edge in selected if edge not in target_edges),
            json.dumps({"label_counts": labels, "policy": policy}, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)
    for edge, payload, label, next_action in rows:
        conn.execute(
            """
            INSERT INTO operational_grammar_edge_audit_v1_items
            (run_id, source_bookid, target_bookid, edge_label, next_action, score, overlap, prior, transition_json, states_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                edge[0],
                edge[1],
                label,
                next_action,
                payload["score"],
                payload["overlap"],
                payload["prior"],
                json.dumps(payload["transition"], sort_keys=True),
                json.dumps({"source": sorted(states[edge[0]]), "target": sorted(states[edge[1]])}, sort_keys=True),
            ),
        )
    conn.commit()
    prioritized = [
        f"{a}->{b}:{label}"
        for (a, b), payload, label, _ in rows
        if label in {"HIGH_LITERAL_OVERLAP_NONCONTIG", "FORMULA_TO_CONTEXT_CANDIDATE", "VINVIN_BRANCH_CROSSOVER", "CONTEXT_TO_SLOT_CANDIDATE"}
    ][:12]
    print(
        json.dumps(
            {
                "run_id": run_id,
                "source_pruning_run_id": int(pruning["run_id"]),
                "selected_edge_count": len(selected),
                "known_edge_count": sum(1 for edge in selected if edge in target_edges),
                "audit_edge_count": sum(1 for edge in selected if edge not in target_edges),
                "label_counts": labels,
                "prioritized_next_edges": prioritized,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
