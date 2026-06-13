#!/usr/bin/env python3
"""Roundtrip probe for structural bridges.

Goal: test whether accepted structural bridge classes can be recovered from
role features without using book ids or semantic labels. This still does not
produce human gloss; it only checks whether structural classes are predictive
enough to be a possible bridge substrate.
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


def load_books(conn: sqlite3.Connection) -> dict[str, dict]:
    rows = conn.execute(
        """
        SELECT bookid, accepted_nodes_json, audit_nodes_json, scoped_nodes_json, rejected_nodes_json
        FROM book_structural_reading_v1_items
        WHERE run_id=(SELECT max(run_id) FROM book_structural_reading_v1_runs)
        """
    )
    out = {}
    for row in rows:
        out[str(row["bookid"])] = {
            "accepted": json.loads(row["accepted_nodes_json"] or "[]"),
            "audit": json.loads(row["audit_nodes_json"] or "[]"),
            "scoped": json.loads(row["scoped_nodes_json"] or "[]"),
            "rejected": json.loads(row["rejected_nodes_json"] or "[]"),
        }
    return out


def features(book: dict) -> set[str]:
    fs = set()
    for node in book["accepted"]:
        for key in [
            "BENNA",
            "FNAAST",
            "TAILBETFTE",
            "C86",
            "VNCTIIN",
            "NAESE",
            "R02",
            "R20",
            "VINVIN",
            "O23",
            "BTILBETA",
            "VFETTIIT",
        ]:
            if key in node:
                fs.add(key)
        if "FNAAST_FORMULA_NSBVN_WINDOW" in node or "BENNA_NSBVN_DISPLAY_WINDOW" in node:
            fs.add("FNAAST_FORMULA")
        if "FNAAST_O23_ENDPOINT_WINDOW" in node:
            fs.add("FNAAST_ENDPOINT")
    if book["scoped"]:
        fs.add("SCOPED")
        if any("O23" in node for node in book["scoped"]):
            fs.add("O23_SCOPED")
    if book["rejected"]:
        fs.add("HAS_REJECTED")
    if book["audit"]:
        fs.add("HAS_AUDIT")
    return fs or {"NO_FEATURE"}


def classify(train: dict[str, str], feats: dict[str, set[str]], bookid: str) -> str:
    scores = Counter()
    for other, cls in train.items():
        inter = len(feats[bookid] & feats[other])
        union = len(feats[bookid] | feats[other])
        scores[cls] += inter / max(1, union)
    if not scores:
        return "NONE"
    return scores.most_common(1)[0][0]


def leave_one_out(labels: dict[str, str], feats: dict[str, set[str]]) -> tuple[int, int, list[dict]]:
    correct = 0
    details = []
    for bookid, cls in labels.items():
        train = {b: c for b, c in labels.items() if b != bookid}
        pred = classify(train, feats, bookid)
        ok = pred == cls
        correct += int(ok)
        details.append({"bookid": bookid, "expected": cls, "predicted": pred, "ok": ok, "features": sorted(feats[bookid])})
    return correct, len(labels), details


def main() -> None:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS structural_bridge_roundtrip_probe_runs (
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
        CREATE TABLE IF NOT EXISTS structural_bridge_roundtrip_probe_items (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            expected_class TEXT NOT NULL,
            predicted_class TEXT NOT NULL,
            ok INTEGER NOT NULL,
            features_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        )
        """
    )
    books = load_books(conn)
    labels = {}
    for cls, ids in CLASSES.items():
        for bookid in ids:
            labels[bookid] = cls
    feats = {bookid: features(books[bookid]) for bookid in labels}
    correct, total, details = leave_one_out(labels, feats)
    observed = correct / max(1, total)

    rng = random.Random(469)
    shuffled_values = list(labels.values())
    rng.shuffle(shuffled_values)
    shuffled_labels = dict(zip(labels.keys(), shuffled_values))
    sh_correct, sh_total, _ = leave_one_out(shuffled_labels, feats)
    shuffled = sh_correct / max(1, sh_total)
    lift = observed - shuffled
    if observed >= 0.70 and lift >= 0.20:
        decision = "STRUCTURAL_BRIDGE_ROUNDTRIP_PASSES_NO_HUMAN_GLOSS"
    elif lift > 0:
        decision = "STRUCTURAL_BRIDGE_ROUNDTRIP_WEAK_SIGNAL_AUDIT_ONLY"
    else:
        decision = "STRUCTURAL_BRIDGE_ROUNDTRIP_FAILS"
    cur = conn.execute(
        """
        INSERT INTO structural_bridge_roundtrip_probe_runs
        (created_at, decision, observed_accuracy, shuffled_accuracy, lift, payload_json)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            now(),
            decision,
            round(observed, 4),
            round(shuffled, 4),
            round(lift, 4),
            json.dumps({"classes": {k: sorted(v) for k, v in CLASSES.items()}}, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)
    for d in details:
        conn.execute(
            """
            INSERT INTO structural_bridge_roundtrip_probe_items
            (run_id, bookid, expected_class, predicted_class, ok, features_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (run_id, d["bookid"], d["expected"], d["predicted"], int(d["ok"]), json.dumps(d["features"])),
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
