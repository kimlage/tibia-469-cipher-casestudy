#!/usr/bin/env python3
"""Probe Q1: BENNA formula function without prose gloss.

A candidate function is accepted only as a functional-semantic constraint if it
predicts the ordered BENNA edges and rejects broad quarantined parallels. This
is not a human translation; it is a testable role-to-function bridge.
"""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

ORDERED_EXPECTED = {"47->40", "58->35", "69->35"}
QUARANTINE_SHOULD_REJECT = {
    "69->40", "47->35", "5->11", "5->36", "5->43", "5->59",
    "47->11", "47->36", "47->43", "47->59", "69->11", "69->36", "69->43", "69->59", "69->66",
}

HYPOTHESES = [
    {
        "hypothesis_id": "BENNA_AS_SINGLE_LEXEME",
        "function_label": "single lexical meaning for all BENNA surfaces",
        "expected_accept": ORDERED_EXPECTED | QUARANTINE_SHOULD_REJECT,
        "expected_reject": set(),
        "status_if_best": "REJECT_SINGLE_LEXEME_OVERGENERALIZES",
    },
    {
        "hypothesis_id": "BENNA_AS_FORMULAIC_FRAME_OPERATOR",
        "function_label": "formulaic frame operator with typed exits",
        "expected_accept": ORDERED_EXPECTED,
        "expected_reject": QUARANTINE_SHOULD_REJECT,
        "status_if_best": "ACCEPT_FUNCTIONAL_BRIDGE_NO_PROSE_GLOSS",
    },
    {
        "hypothesis_id": "BENNA_AS_DISPLAY_ONLY",
        "function_label": "display/window marker only",
        "expected_accept": {"58->35"},
        "expected_reject": (ORDERED_EXPECTED - {"58->35"}) | QUARANTINE_SHOULD_REJECT,
        "status_if_best": "REJECT_DISPLAY_ONLY_MISSES_TEMPLATE_AND_MIXED_HEADS",
    },
    {
        "hypothesis_id": "BENNA_AS_TEMPLATE_ONLY",
        "function_label": "template marker only",
        "expected_accept": {"47->40", "69->35"},
        "expected_reject": (ORDERED_EXPECTED - {"47->40", "69->35"}) | QUARANTINE_SHOULD_REJECT,
        "status_if_best": "REJECT_TEMPLATE_ONLY_MISSES_DISPLAY_HEAD",
    },
]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_edge_truth(conn: sqlite3.Connection) -> dict[str, str]:
    run_id = conn.execute("SELECT max(run_id) FROM benna_ordered_core_v2_runs").fetchone()[0]
    truth: dict[str, str] = {}
    for row in conn.execute("SELECT item_id,status FROM benna_ordered_core_v2_items WHERE run_id=? AND item_type='edge'", (run_id,)):
        edge = str(row["item_id"])
        status = str(row["status"])
        if status == "ORDERED_EDGE_ACCEPTED_NO_GLOSS":
            truth[edge] = "ACCEPT"
        elif status == "QUARANTINED_PARALLEL_EDGE":
            truth[edge] = "REJECT"
    return truth


def evaluate_hypothesis(h: dict, truth: dict[str, str]) -> dict:
    edges = sorted(set(truth) | set(h["expected_accept"]) | set(h["expected_reject"]))
    correct = 0
    wrong = []
    for edge in edges:
        expected = "ACCEPT" if edge in h["expected_accept"] else "REJECT"
        actual = truth.get(edge, "REJECT")
        if expected == actual:
            correct += 1
        else:
            wrong.append({"edge": edge, "expected": expected, "actual": actual})
    accuracy = correct / max(1, len(edges))
    ordered_recall = len([e for e in ORDERED_EXPECTED if e in h["expected_accept"] and truth.get(e) == "ACCEPT"]) / len(ORDERED_EXPECTED)
    quarantine_rejection = len([e for e in QUARANTINE_SHOULD_REJECT if e in h["expected_reject"] and truth.get(e, "REJECT") == "REJECT"]) / len(QUARANTINE_SHOULD_REJECT)
    return {
        "hypothesis_id": h["hypothesis_id"],
        "function_label": h["function_label"],
        "accuracy": round(accuracy, 4),
        "ordered_recall": round(ordered_recall, 4),
        "quarantine_rejection": round(quarantine_rejection, 4),
        "wrong": wrong,
        "candidate_status": h["status_if_best"],
    }


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS benna_semantic_function_probe_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            best_hypothesis_id TEXT NOT NULL,
            ordered_recall REAL NOT NULL,
            quarantine_rejection REAL NOT NULL,
            accepted_prose_gloss INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS benna_semantic_function_probe_v1_items (
            run_id INTEGER NOT NULL,
            hypothesis_id TEXT NOT NULL,
            status TEXT NOT NULL,
            function_label TEXT NOT NULL,
            accuracy REAL NOT NULL,
            ordered_recall REAL NOT NULL,
            quarantine_rejection REAL NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, hypothesis_id)
        )
        """
    )
    truth = load_edge_truth(conn)
    results = [evaluate_hypothesis(h, truth) for h in HYPOTHESES]
    best = max(results, key=lambda r: (r["ordered_recall"], r["quarantine_rejection"], r["accuracy"]))
    if best["hypothesis_id"] == "BENNA_AS_FORMULAIC_FRAME_OPERATOR" and best["ordered_recall"] == 1.0 and best["quarantine_rejection"] == 1.0:
        decision = "Q1_BENNA_FUNCTIONAL_BRIDGE_ACCEPTED_NO_PROSE_GLOSS"
    else:
        decision = "Q1_BENNA_FUNCTION_REMAINS_BLOCKED"
    cur = conn.execute(
        """
        INSERT INTO benna_semantic_function_probe_v1_runs
        (created_at, decision, best_hypothesis_id, ordered_recall, quarantine_rejection, accepted_prose_gloss, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            now(), decision, best["hypothesis_id"], best["ordered_recall"], best["quarantine_rejection"], 0,
            json.dumps({"truth_edges": truth, "best": best}, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)
    for result in results:
        status = "BEST" if result["hypothesis_id"] == best["hypothesis_id"] else "REJECTED_OR_WEAKER"
        conn.execute(
            """
            INSERT INTO benna_semantic_function_probe_v1_items
            (run_id, hypothesis_id, status, function_label, accuracy, ordered_recall, quarantine_rejection, evidence_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id, result["hypothesis_id"], status, result["function_label"], result["accuracy"], result["ordered_recall"], result["quarantine_rejection"],
                json.dumps({"wrong": result["wrong"], "candidate_status": result["candidate_status"]}, sort_keys=True),
            ),
        )
    # Mark Q1 as partially answered in a derived result table, not by overwriting the queue.
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS semantic_question_result_v1_items (
            run_id INTEGER NOT NULL,
            question_id TEXT NOT NULL,
            status TEXT NOT NULL,
            answer_type TEXT NOT NULL,
            answer_label TEXT NOT NULL,
            accepted_prose_gloss INTEGER NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, question_id)
        )
        """
    )
    conn.execute(
        """
        INSERT INTO semantic_question_result_v1_items
        (run_id, question_id, status, answer_type, answer_label, accepted_prose_gloss, evidence_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id, "Q1_BENNA_FORMULA_FUNCTION", decision, "FUNCTIONAL_SEMANTIC_CONSTRAINT", best["function_label"], 0,
            json.dumps({"best_hypothesis_id": best["hypothesis_id"], "ordered_recall": best["ordered_recall"], "quarantine_rejection": best["quarantine_rejection"]}, sort_keys=True),
        ),
    )
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": decision, "best_hypothesis_id": best["hypothesis_id"], "function_label": best["function_label"], "ordered_recall": best["ordered_recall"], "quarantine_rejection": best["quarantine_rejection"], "accepted_prose_gloss": 0}, ensure_ascii=False))


if __name__ == "__main__":
    main()
