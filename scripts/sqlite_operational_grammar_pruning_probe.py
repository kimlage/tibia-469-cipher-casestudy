#!/usr/bin/env python3
"""Prune the operational grammar edge graph.

This is the second stage after reconstruction. It searches small, auditable edge
selection policies and records the best policy that preserves contig-edge recall
while reducing false positives. This remains a structural probe, not a semantic
gloss generator.
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
    evaluate,
    load_books,
    load_target_edges,
)


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def select_edges(scores: dict[tuple[str, str], dict], *, top_k: int, min_prior: float, min_overlap: int, min_score: float) -> set[tuple[str, str]]:
    by_source: dict[str, list[tuple[tuple[str, str], dict]]] = {}
    for edge, payload in scores.items():
        if payload["prior"] < min_prior:
            continue
        if payload["overlap"] < min_overlap:
            continue
        if payload["score"] < min_score:
            continue
        by_source.setdefault(edge[0], []).append((edge, payload))
    selected: set[tuple[str, str]] = set()
    for items in by_source.values():
        items.sort(key=lambda item: (-item[1]["score"], -item[1]["overlap"], int(item[0][1])))
        selected.update(edge for edge, _ in items[:top_k])
    return selected


def main() -> None:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS operational_grammar_pruning_probe_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            best_policy_json TEXT NOT NULL,
            best_precision REAL NOT NULL,
            best_recall REAL NOT NULL,
            best_f1 REAL NOT NULL,
            best_edge_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS operational_grammar_pruning_probe_items (
            run_id INTEGER NOT NULL,
            policy_id TEXT NOT NULL,
            top_k INTEGER NOT NULL,
            min_prior REAL NOT NULL,
            min_overlap INTEGER NOT NULL,
            min_score REAL NOT NULL,
            precision REAL NOT NULL,
            recall REAL NOT NULL,
            f1 REAL NOT NULL,
            edge_count INTEGER NOT NULL,
            hit_count INTEGER NOT NULL,
            missing_json TEXT NOT NULL,
            PRIMARY KEY (run_id, policy_id)
        )
        """
    )

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

    policies = []
    for top_k in (1, 2, 3):
        for min_prior in (0.0, 0.58, 0.64, 0.72, 0.86, 0.92, 1.0):
            for min_overlap in (0, 4, 8, 12, 16, 20, 24, 32):
                for min_score in (0.0, 80.0, 100.0, 110.0, 120.0, 130.0, 145.0):
                    edges = select_edges(scores, top_k=top_k, min_prior=min_prior, min_overlap=min_overlap, min_score=min_score)
                    metrics = evaluate(edges, target_edges)
                    policies.append(
                        {
                            "top_k": top_k,
                            "min_prior": min_prior,
                            "min_overlap": min_overlap,
                            "min_score": min_score,
                            "edges": edges,
                            "metrics": metrics,
                        }
                    )

    # Prefer high recall first, then fewer edges / higher precision. This avoids
    # optimizing into an attractive but lossy local minimum.
    best = max(
        policies,
        key=lambda p: (
            p["metrics"]["recall"],
            p["metrics"]["f1"],
            p["metrics"]["precision"],
            -len(p["edges"]),
        ),
    )
    best_metrics = best["metrics"]
    if best_metrics["recall"] == 1.0 and best_metrics["precision"] >= 0.20:
        decision = "PRUNED_GRAMMAR_RETAINS_FULL_RECALL_WITH_LOWER_NOISE"
    elif best_metrics["recall"] >= 0.75:
        decision = "PRUNED_GRAMMAR_USEFUL_BUT_STILL_NOISY"
    else:
        decision = "PRUNING_LOSES_TOO_MUCH_CONTIG_STRUCTURE"

    best_policy = {
        "top_k": best["top_k"],
        "min_prior": best["min_prior"],
        "min_overlap": best["min_overlap"],
        "min_score": best["min_score"],
    }
    cur = conn.execute(
        """
        INSERT INTO operational_grammar_pruning_probe_runs
        (created_at, decision, best_policy_json, best_precision, best_recall, best_f1, best_edge_count, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            now(),
            decision,
            json.dumps(best_policy, sort_keys=True),
            best_metrics["precision"],
            best_metrics["recall"],
            best_metrics["f1"],
            len(best["edges"]),
            json.dumps(
                {
                    "hits": best_metrics["hits"],
                    "missing": best_metrics["missing"],
                    "target_edges": [f"{a}->{b}" for a, b in sorted(target_edges, key=lambda e: (int(e[0]), int(e[1])))],
                    "selected_edges": [f"{a}->{b}" for a, b in sorted(best["edges"], key=lambda e: (int(e[0]), int(e[1])))],
                },
                sort_keys=True,
            ),
        ),
    )
    run_id = int(cur.lastrowid)

    for idx, policy in enumerate(sorted(policies, key=lambda p: (-p["metrics"]["recall"], -p["metrics"]["f1"], len(p["edges"])))[:50], start=1):
        m = policy["metrics"]
        conn.execute(
            """
            INSERT INTO operational_grammar_pruning_probe_items
            (run_id, policy_id, top_k, min_prior, min_overlap, min_score, precision, recall, f1, edge_count, hit_count, missing_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                f"policy_{idx:02d}",
                policy["top_k"],
                policy["min_prior"],
                policy["min_overlap"],
                policy["min_score"],
                m["precision"],
                m["recall"],
                m["f1"],
                len(policy["edges"]),
                len(m["hits"]),
                json.dumps(m["missing"], sort_keys=True),
            ),
        )
    conn.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "best_policy": best_policy,
                "precision": best_metrics["precision"],
                "recall": best_metrics["recall"],
                "f1": best_metrics["f1"],
                "edge_count": len(best["edges"]),
                "hits": best_metrics["hits"],
                "missing": best_metrics["missing"],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
