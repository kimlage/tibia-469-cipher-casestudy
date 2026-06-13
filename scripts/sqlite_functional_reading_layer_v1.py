#!/usr/bin/env python3
"""Build a partial functional reading layer from accepted semantic constraints.

This is a readable but non-prose layer: it labels books/contigs by accepted
functional roles and keeps unresolved semantic slots explicit.
"""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

ROLE_LABELS = {
    "47": "<BENNA:TEMPLATE_HEAD>",
    "40": "<BENNA:FORMULA_BODY>",
    "58": "<FRAME_FORMULA_OPERATOR>",
    "69": "<BENNA:MIXED_TEMPLATE_FORMULA_HEAD>",
    "35": "<HANDOFF_CONTEXT>",
    "67": "<CONTEXT_PAYLOAD>",
    "2": "<NAESE:CANONICAL_SLOT_OPERATOR>",
    "51": "<R02_SLOT_BRIDGE>",
    "53": "<R02_SLOT_BRIDGE>",
    "29": "<VINVIN_R20_BRANCH_HEAD>",
    "65": "<VINVIN_R20_CONNECTOR_ENDPOINT>",
    "52": "<C86_VINVIN_BRANCH_PAYLOAD>",
    "62": "<C86_VINVIN_BRANCH_ENDPOINT>",
    "13": "<O23_FNAAST_ENDPOINT>",
    "38": "<O23_FNAAST_ENDPOINT>",
}

CONTIG_FUNCTIONS = {
    "0": "<R02_SLOT_BRIDGE> -> <R02_SLOT_BRIDGE>",
    "1": "<FRAME_FORMULA_OPERATOR> -> <HANDOFF_CONTEXT> -> <CONTEXT_PAYLOAD> -> <NAESE:CANONICAL_SLOT_OPERATOR>",
    "2": "<VINVIN_R20_BRANCH_HEAD> -> <VINVIN_R20_CONNECTOR_ENDPOINT>",
    "3": "<C86_VINVIN_BRANCH_PAYLOAD> -> <C86_VINVIN_BRANCH_ENDPOINT>",
    "4": "<O23_FNAAST_ENDPOINT> -> <O23_FNAAST_ENDPOINT>",
    "5": "<BENNA:TEMPLATE_HEAD> -> <BENNA:FORMULA_BODY>",
}


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS functional_reading_layer_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            book_label_count INTEGER NOT NULL,
            contig_label_count INTEGER NOT NULL,
            accepted_prose_gloss_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS functional_reading_layer_v1_items (
            run_id INTEGER NOT NULL,
            item_type TEXT NOT NULL,
            item_id TEXT NOT NULL,
            status TEXT NOT NULL,
            functional_reading TEXT NOT NULL,
            prose_gloss TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, item_type, item_id)
        )
        """
    )
    decision = "FUNCTIONAL_READING_LAYER_PARTIAL_NO_PROSE_GLOSS"
    cur = conn.execute(
        """
        INSERT INTO functional_reading_layer_v1_runs
        (created_at, decision, book_label_count, contig_label_count, accepted_prose_gloss_count, payload_json)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (now(), decision, len(ROLE_LABELS), len(CONTIG_FUNCTIONS), 0, json.dumps({"source_questions": ["Q1_BENNA_FORMULA_FUNCTION", "Q2_HANDOFF_TO_CONTEXT_PAYLOAD"], "warning": "functional labels are not English translation"}, sort_keys=True)),
    )
    run_id = int(cur.lastrowid)
    for bookid, label in sorted(ROLE_LABELS.items(), key=lambda kv: int(kv[0])):
        conn.execute(
            """
            INSERT INTO functional_reading_layer_v1_items
            (run_id, item_type, item_id, status, functional_reading, prose_gloss, evidence_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, "book", bookid, "FUNCTIONAL_LABEL_ACCEPTED_NO_PROSE", label, "<NO_ACCEPTED_HUMAN_GLOSS>", json.dumps({"source": "functional grammar + Q1/Q2 constraints"}, sort_keys=True)),
        )
    for contigid, label in sorted(CONTIG_FUNCTIONS.items(), key=lambda kv: int(kv[0])):
        conn.execute(
            """
            INSERT INTO functional_reading_layer_v1_items
            (run_id, item_type, item_id, status, functional_reading, prose_gloss, evidence_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, "contig", contigid, "FUNCTIONAL_SEQUENCE_ACCEPTED_NO_PROSE", label, "<NO_ACCEPTED_HUMAN_GLOSS>", json.dumps({"source": "functional grammar covers contig edges 8/8"}, sort_keys=True)),
        )
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": decision, "book_label_count": len(ROLE_LABELS), "contig_label_count": len(CONTIG_FUNCTIONS), "accepted_prose_gloss_count": 0}, ensure_ascii=False))


if __name__ == "__main__":
    main()
