#!/usr/bin/env python3
"""Probe Q5: O23/FNAAST endpoint function without prose gloss."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

EXPECTED_ACCEPT = {"13->38"}
EXPECTED_REJECT = {"56->38", "13->56", "38->56", "56->13", "58->56", "59->56"}

HYPOTHESES = [
    {
        "hypothesis_id": "O23_AS_BROAD_FNAAST",
        "function_label": "broad FNAAST/O23 family endpoint everywhere",
        "expected_accept": EXPECTED_ACCEPT | EXPECTED_REJECT,
        "expected_reject": set(),
        "status_if_best": "REJECT_BROAD_FNAAST_SWALLOWS_CONTROLS",
    },
    {
        "hypothesis_id": "O23_AS_SCOPED_ENDPOINT",
        "function_label": "scoped endpoint operator excluding weak/control FNAAST cases",
        "expected_accept": EXPECTED_ACCEPT,
        "expected_reject": EXPECTED_REJECT,
        "status_if_best": "ACCEPT_SCOPED_ENDPOINT_NO_PROSE_GLOSS",
    },
    {
        "hypothesis_id": "O23_AS_WEAK_NAESE_TAIL",
        "function_label": "weak NAESE/FNAAST tail family",
        "expected_accept": {"56->38", "13->38"},
        "expected_reject": EXPECTED_REJECT - {"56->38"},
        "status_if_best": "REJECT_WEAK_TAIL_MISUSES_56_CONTROL",
    },
]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_truth(conn: sqlite3.Connection) -> dict[str, str]:
    truth = {edge: "REJECT" for edge in EXPECTED_REJECT}
    truth["13->38"] = "ACCEPT"
    return truth


def evaluate(h: dict, truth: dict[str, str]) -> dict:
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
    ordered_recall = len([e for e in EXPECTED_ACCEPT if e in h["expected_accept"] and truth.get(e) == "ACCEPT"]) / len(EXPECTED_ACCEPT)
    reject_rate = len([e for e in EXPECTED_REJECT if e in h["expected_reject"] and truth.get(e, "REJECT") == "REJECT"]) / len(EXPECTED_REJECT)
    return {"hypothesis_id": h["hypothesis_id"], "function_label": h["function_label"], "accuracy": round(correct / max(1, len(edges)), 4), "ordered_recall": round(ordered_recall, 4), "negative_rejection": round(reject_rate, 4), "wrong": wrong, "candidate_status": h["status_if_best"]}


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS o23_endpoint_function_probe_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            best_hypothesis_id TEXT NOT NULL,
            ordered_recall REAL NOT NULL,
            negative_rejection REAL NOT NULL,
            accepted_prose_gloss INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS o23_endpoint_function_probe_v1_items (
            run_id INTEGER NOT NULL,
            hypothesis_id TEXT NOT NULL,
            status TEXT NOT NULL,
            function_label TEXT NOT NULL,
            accuracy REAL NOT NULL,
            ordered_recall REAL NOT NULL,
            negative_rejection REAL NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, hypothesis_id)
        )
        """
    )
    truth = load_truth(conn)
    results = [evaluate(h, truth) for h in HYPOTHESES]
    best = max(results, key=lambda r: (r["ordered_recall"], r["negative_rejection"], r["accuracy"]))
    if best["hypothesis_id"] == "O23_AS_SCOPED_ENDPOINT" and best["ordered_recall"] == 1.0 and best["negative_rejection"] == 1.0:
        decision = "Q5_O23_SCOPED_ENDPOINT_ACCEPTED_NO_PROSE_GLOSS"
    else:
        decision = "Q5_O23_ENDPOINT_REMAINS_BLOCKED"
    cur = conn.execute(
        """
        INSERT INTO o23_endpoint_function_probe_v1_runs
        (created_at, decision, best_hypothesis_id, ordered_recall, negative_rejection, accepted_prose_gloss, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (now(), decision, best["hypothesis_id"], best["ordered_recall"], best["negative_rejection"], 0, json.dumps({"truth_edges": truth, "best": best}, sort_keys=True)),
    )
    run_id = int(cur.lastrowid)
    for result in results:
        conn.execute(
            """
            INSERT INTO o23_endpoint_function_probe_v1_items
            (run_id, hypothesis_id, status, function_label, accuracy, ordered_recall, negative_rejection, evidence_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, result["hypothesis_id"], "BEST" if result["hypothesis_id"] == best["hypothesis_id"] else "REJECTED_OR_WEAKER", result["function_label"], result["accuracy"], result["ordered_recall"], result["negative_rejection"], json.dumps({"wrong": result["wrong"], "candidate_status": result["candidate_status"]}, sort_keys=True)),
        )
    conn.execute(
        """
        INSERT OR REPLACE INTO semantic_question_result_v1_items
        (run_id, question_id, status, answer_type, answer_label, accepted_prose_gloss, evidence_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (run_id, "Q5_O23_ENDPOINT_BINDING", decision, "FUNCTIONAL_SEMANTIC_CONSTRAINT", best["function_label"], 0, json.dumps({"best_hypothesis_id": best["hypothesis_id"], "ordered_recall": best["ordered_recall"], "negative_rejection": best["negative_rejection"]}, sort_keys=True)),
    )
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": decision, "best_hypothesis_id": best["hypothesis_id"], "function_label": best["function_label"], "ordered_recall": best["ordered_recall"], "negative_rejection": best["negative_rejection"], "accepted_prose_gloss": 0}, ensure_ascii=False))


if __name__ == "__main__":
    main()
