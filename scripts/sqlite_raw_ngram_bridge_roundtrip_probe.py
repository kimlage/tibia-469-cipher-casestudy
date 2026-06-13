#!/usr/bin/env python3
"""Roundtrip bridge classes from raw row0 n-grams only.

This is independent from the role-name classifier. It uses character n-grams
from literal row0 text and a leave-one-out nearest-centroid classifier.
Passing this test supports the mechanical bridge substrate; it still does not
produce human semantic gloss.
"""

from __future__ import annotations

import datetime as dt
import json
import random
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"


CLASSES = {
    "CONTIG1_FORMULA_TO_SLOT": {"58", "35", "67", "2", "10", "27"},
    "VINVIN_C86_R20_BRANCH_SPLIT": {"29", "65", "61", "52", "62", "3", "17", "68"},
    "NAESE_R02_SLOT_BRIDGE": {"51", "53", "22", "28", "48", "42"},
    "O23_FNAAST_ENDPOINT": {"13", "38", "56"},
}


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ngrams(text: str, n: int) -> set[str]:
    if len(text) < n:
        return {text} if text else set()
    return {text[i : i + n] for i in range(len(text) - n + 1)}


def features(text: str) -> set[str]:
    out = set()
    for n in (4, 5, 6, 7, 8):
        out.update(f"{n}:{g}" for g in ngrams(text, n))
    return out or {"EMPTY"}


def jaccard(a: set[str], b: set[str]) -> float:
    return len(a & b) / max(1, len(a | b))


def classify(train: dict[str, str], feats: dict[str, set[str]], bookid: str) -> str:
    scores = Counter()
    for other, cls in train.items():
        scores[cls] += jaccard(feats[bookid], feats[other])
    return scores.most_common(1)[0][0] if scores else "NONE"


def evaluate(labels: dict[str, str], feats: dict[str, set[str]]) -> tuple[float, list[dict]]:
    details = []
    ok_count = 0
    for bookid, expected in labels.items():
        train = {b: c for b, c in labels.items() if b != bookid}
        predicted = classify(train, feats, bookid)
        ok = predicted == expected
        ok_count += int(ok)
        details.append({"bookid": bookid, "expected": expected, "predicted": predicted, "ok": ok})
    return ok_count / max(1, len(labels)), details


def main() -> None:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS raw_ngram_bridge_roundtrip_probe_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            observed_accuracy REAL NOT NULL,
            shuffled_accuracy REAL NOT NULL,
            lift REAL NOT NULL,
            payload_json TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS raw_ngram_bridge_roundtrip_probe_items (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            expected_class TEXT NOT NULL,
            predicted_class TEXT NOT NULL,
            ok INTEGER NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        )
        """
    )
    literals = {
        str(r["bookid"]): r["literal_text"]
        for r in conn.execute(
            "SELECT bookid, literal_text FROM literal_homophonic_books_v1 WHERE run_id=(SELECT max(run_id) FROM literal_homophonic_books_v1_runs)"
        )
    }
    labels = {}
    for cls, ids in CLASSES.items():
        for bookid in ids:
            labels[bookid] = cls
    feats = {bookid: features(literals[bookid]) for bookid in labels}
    observed, details = evaluate(labels, feats)

    rng = random.Random(469)
    shuffled_values = list(labels.values())
    rng.shuffle(shuffled_values)
    shuffled_labels = dict(zip(labels.keys(), shuffled_values))
    shuffled, _ = evaluate(shuffled_labels, feats)
    lift = observed - shuffled
    if observed >= 0.70 and lift >= 0.20:
        decision = "RAW_NGRAM_BRIDGE_ROUNDTRIP_PASSES_NO_HUMAN_GLOSS"
    elif lift > 0:
        decision = "RAW_NGRAM_BRIDGE_ROUNDTRIP_WEAK_SIGNAL_AUDIT_ONLY"
    else:
        decision = "RAW_NGRAM_BRIDGE_ROUNDTRIP_FAILS"

    cur = conn.execute(
        """
        INSERT INTO raw_ngram_bridge_roundtrip_probe_runs
        (created_at, decision, observed_accuracy, shuffled_accuracy, lift, payload_json)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            now(),
            decision,
            round(observed, 4),
            round(shuffled, 4),
            round(lift, 4),
            json.dumps({"feature": "literal row0 char ngrams 4..8", "classes": {k: sorted(v) for k, v in CLASSES.items()}}, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)
    for d in details:
        conn.execute(
            """
            INSERT INTO raw_ngram_bridge_roundtrip_probe_items
            (run_id, bookid, expected_class, predicted_class, ok, evidence_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                d["bookid"],
                d["expected"],
                d["predicted"],
                int(d["ok"]),
                json.dumps({"literal_len": len(literals[d["bookid"]]), "feature_count": len(feats[d["bookid"]])}, sort_keys=True),
            ),
        )
    conn.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "observed_accuracy": round(observed, 4),
                "shuffled_accuracy": round(shuffled, 4),
                "lift": round(lift, 4),
                "details": details,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
