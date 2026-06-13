#!/usr/bin/env python3
"""Probe token-level transforms for accepted structural pairs/contigs."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"


PAIRS = [
    ("VINVIN_R20_BRANCH", "29", "65"),
    ("VINVIN_C86_BRANCH", "52", "62"),
    ("NAESE_R02_SLOT_BRIDGE", "51", "53"),
    ("O23_ENDPOINT_PAYLOAD", "13", "38"),
    ("ZERO_PAIR_TRUNCATION", "20", "54"),
    ("ZERO_PAIR_FAST_BEIE", "25", "39"),
    ("TAILBETFTE_HANDOFF", "35", "67"),
]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def lcs_len(a: list[str], b: list[str]) -> int:
    prev = [0] * (len(b) + 1)
    for x in a:
        cur = [0]
        for j, y in enumerate(b, 1):
            cur.append(prev[j - 1] + 1 if x == y else max(prev[j], cur[-1]))
        prev = cur
    return prev[-1]


def common_prefix(a: list[str], b: list[str]) -> int:
    n = 0
    for x, y in zip(a, b):
        if x != y:
            break
        n += 1
    return n


def common_suffix(a: list[str], b: list[str]) -> int:
    n = 0
    for x, y in zip(reversed(a), reversed(b)):
        if x != y:
            break
        n += 1
    return n


def classify(a: list[str], b: list[str]) -> tuple[str, dict]:
    lcs = lcs_len(a, b)
    pref = common_prefix(a, b)
    suff = common_suffix(a, b)
    shorter = min(len(a), len(b))
    containment = lcs / max(1, shorter)
    if pref >= 10 and containment >= 0.75:
        status = "PREFIX_CONTINUATION_OR_TRUNCATION"
    elif suff >= 10 and containment >= 0.75:
        status = "SUFFIX_CONTINUATION_OR_TRUNCATION"
    elif containment >= 0.75:
        status = "INTERNAL_SHARED_CORE_BRANCH_VARIANT"
    elif containment >= 0.55:
        status = "PARTIAL_SHARED_CORE"
    else:
        status = "WEAK_TOKEN_TRANSFORM"
    return status, {
        "len_a": len(a),
        "len_b": len(b),
        "lcs_len": lcs,
        "lcs_over_shorter": round(containment, 4),
        "common_prefix": pref,
        "common_suffix": suff,
        "a_head": "".join(a[:18]),
        "b_head": "".join(b[:18]),
        "a_tail": "".join(a[-18:]),
        "b_tail": "".join(b[-18:]),
    }


def main() -> None:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS structural_pair_transform_probe_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            strong_count INTEGER NOT NULL,
            weak_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS structural_pair_transform_probe_items (
            run_id INTEGER NOT NULL,
            pair_id TEXT NOT NULL,
            book_a TEXT NOT NULL,
            book_b TEXT NOT NULL,
            status TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, pair_id)
        )
        """
    )
    tokens = {}
    for row in conn.execute(
        "SELECT bookid, tokens_json FROM row0_variant_book_tokens WHERE run_id=(SELECT max(run_id) FROM row0_variant_frontier_runs)"
    ):
        tokens[str(row["bookid"])] = json.loads(row["tokens_json"])

    results = []
    for pair_id, a_id, b_id in PAIRS:
        status, evidence = classify(tokens[a_id], tokens[b_id])
        results.append((pair_id, a_id, b_id, status, evidence))
    strong = sum(1 for r in results if r[3] != "WEAK_TOKEN_TRANSFORM")
    weak = len(results) - strong
    decision = "PAIR_TRANSFORMS_SUPPORT_STRUCTURAL_RELATIONS_NO_GLOSS" if strong else "PAIR_TRANSFORMS_WEAK"
    cur = conn.execute(
        """
        INSERT INTO structural_pair_transform_probe_runs
        (created_at, decision, strong_count, weak_count, payload_json)
        VALUES (?, ?, ?, ?, ?)
        """,
        (now(), decision, strong, weak, json.dumps({"pairs": [p[0] for p in PAIRS]}, sort_keys=True)),
    )
    run_id = int(cur.lastrowid)
    for pair_id, a_id, b_id, status, evidence in results:
        conn.execute(
            """
            INSERT INTO structural_pair_transform_probe_items
            (run_id, pair_id, book_a, book_b, status, evidence_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (run_id, pair_id, a_id, b_id, status, json.dumps(evidence, sort_keys=True)),
        )
    conn.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "strong_count": strong,
                "weak_count": weak,
                "results": [
                    {
                        "pair_id": pair_id,
                        "book_a": a_id,
                        "book_b": b_id,
                        "status": status,
                        **evidence,
                    }
                    for pair_id, a_id, b_id, status, evidence in results
                ],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
