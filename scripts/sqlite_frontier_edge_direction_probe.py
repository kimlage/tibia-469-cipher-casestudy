#!/usr/bin/env python3
"""Classify frontier overlap edges as directional assembly or containment."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"


FRONTIER_EDGES = [
    ("10_27", "10", "27"),
    ("27_35", "27", "35"),
    ("10_35", "10", "35"),
    ("35_67", "35", "67"),
    ("67_2", "67", "2"),
    ("61_65", "61", "65"),
    ("3_17", "3", "17"),
    ("17_62", "17", "62"),
]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def lcs_matrix(a: list[str], b: list[str]) -> list[list[int]]:
    dp = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i, x in enumerate(a, 1):
        for j, y in enumerate(b, 1):
            dp[i][j] = dp[i - 1][j - 1] + 1 if x == y else max(dp[i - 1][j], dp[i][j - 1])
    return dp


def lcs_alignment(a: list[str], b: list[str]) -> tuple[int, list[int], list[int]]:
    dp = lcs_matrix(a, b)
    i, j = len(a), len(b)
    ai: list[int] = []
    bj: list[int] = []
    while i > 0 and j > 0:
        if a[i - 1] == b[j - 1]:
            ai.append(i - 1)
            bj.append(j - 1)
            i -= 1
            j -= 1
        elif dp[i - 1][j] >= dp[i][j - 1]:
            i -= 1
        else:
            j -= 1
    ai.reverse()
    bj.reverse()
    return dp[-1][-1], ai, bj


def classify(a: list[str], b: list[str]) -> tuple[str, dict]:
    lcs, ai, bj = lcs_alignment(a, b)
    shorter = min(len(a), len(b))
    ratio = lcs / max(1, shorter)
    if not ai or not bj:
        return "NO_SHARED_CORE", {"lcs": lcs, "lcs_over_shorter": round(ratio, 4)}

    a_left = ai[0]
    a_right = len(a) - ai[-1] - 1
    b_left = bj[0]
    b_right = len(b) - bj[-1] - 1
    a_extra = len(a) - lcs
    b_extra = len(b) - lcs

    if ratio >= 0.98 and (a_extra == 0 or b_extra == 0):
        status = "PURE_CONTAINMENT_WINDOW"
    elif ratio >= 0.82 and a_left <= 3 and b_left <= 3 and abs(a_right - b_right) > 8:
        status = "SHARED_HEAD_WITH_DIVERGENT_TAIL"
    elif ratio >= 0.82 and abs(a_left - b_left) > 8:
        status = "SHIFTED_INTERNAL_WINDOW"
    elif ratio >= 0.82:
        status = "HIGH_OVERLAP_VARIANT"
    elif ratio >= 0.65:
        status = "PARTIAL_OVERLAP_VARIANT"
    else:
        status = "WEAK_OVERLAP"

    return status, {
        "len_a": len(a),
        "len_b": len(b),
        "lcs": lcs,
        "lcs_over_shorter": round(ratio, 4),
        "a_extra": a_extra,
        "b_extra": b_extra,
        "a_left_unmatched": a_left,
        "b_left_unmatched": b_left,
        "a_right_unmatched": a_right,
        "b_right_unmatched": b_right,
        "a_unmatched_head": "".join(a[: min(a_left, 24)]),
        "b_unmatched_head": "".join(b[: min(b_left, 24)]),
        "a_unmatched_tail": "".join(a[len(a) - min(a_right, 24) :]) if a_right else "",
        "b_unmatched_tail": "".join(b[len(b) - min(b_right, 24) :]) if b_right else "",
    }


def main() -> None:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS frontier_edge_direction_probe_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            directional_count INTEGER NOT NULL,
            containment_count INTEGER NOT NULL,
            weak_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS frontier_edge_direction_probe_items (
            run_id INTEGER NOT NULL,
            edge_id TEXT NOT NULL,
            book_a TEXT NOT NULL,
            book_b TEXT NOT NULL,
            status TEXT NOT NULL,
            promotion_status TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, edge_id)
        )
        """
    )
    tokens = {
        str(r["bookid"]): json.loads(r["tokens_json"])
        for r in conn.execute(
            "SELECT bookid, tokens_json FROM row0_variant_book_tokens WHERE run_id=(SELECT max(run_id) FROM row0_variant_frontier_runs)"
        )
    }
    results = []
    for edge_id, a_id, b_id in FRONTIER_EDGES:
        status, evidence = classify(tokens[a_id], tokens[b_id])
        if status == "PURE_CONTAINMENT_WINDOW":
            promotion = "NO_PROMOTE_CONTAINMENT_ONLY"
        elif status in {"SHIFTED_INTERNAL_WINDOW", "SHARED_HEAD_WITH_DIVERGENT_TAIL", "HIGH_OVERLAP_VARIANT"}:
            promotion = "PROMOTE_STRUCTURAL_VARIANT_CANDIDATE_NO_GLOSS"
        elif status == "PARTIAL_OVERLAP_VARIANT":
            promotion = "AUDIT_ONLY_PARTIAL_VARIANT"
        else:
            promotion = "REJECT_WEAK_EDGE"
        results.append((edge_id, a_id, b_id, status, promotion, evidence))

    directional = sum(1 for r in results if r[4].startswith("PROMOTE"))
    containment = sum(1 for r in results if r[4] == "NO_PROMOTE_CONTAINMENT_ONLY")
    weak = len(results) - directional - containment
    decision = "DIRECTIONAL_FRONTIER_VARIANTS_FOUND_NO_GLOSS" if directional else "FRONTIER_ONLY_CONTAINMENT_OR_WEAK"
    cur = conn.execute(
        """
        INSERT INTO frontier_edge_direction_probe_runs
        (created_at, decision, directional_count, containment_count, weak_count, payload_json)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (now(), decision, directional, containment, weak, json.dumps({"edges": [e[0] for e in FRONTIER_EDGES]}, sort_keys=True)),
    )
    run_id = int(cur.lastrowid)
    for edge_id, a_id, b_id, status, promotion, evidence in results:
        conn.execute(
            """
            INSERT INTO frontier_edge_direction_probe_items
            (run_id, edge_id, book_a, book_b, status, promotion_status, evidence_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, edge_id, a_id, b_id, status, promotion, json.dumps(evidence, sort_keys=True)),
        )
    conn.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "directional_count": directional,
                "containment_count": containment,
                "weak_count": weak,
                "results": [
                    {
                        "edge_id": edge_id,
                        "book_a": a_id,
                        "book_b": b_id,
                        "status": status,
                        "promotion_status": promotion,
                        **evidence,
                    }
                    for edge_id, a_id, b_id, status, promotion, evidence in results
                ],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
