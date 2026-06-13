#!/usr/bin/env python3
"""Try to reconstruct contig/stage order from bridge grammar features.

This probe converts current mechanical bridges into ordered stage labels and
asks whether nearest-stage ordering can recover known contig order without
using the contig order itself during labeling. It is still no-gloss.
"""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"


STAGE_ORDER = {
    "FORMULA_HEAD": 0,
    "FORMULA_HANDOFF_CONTEXT": 1,
    "HANDOFF_CONTEXT": 2,
    "CONTEXT_SLOT": 3,
    "NAESE_R02_PAIR": 4,
    "VINVIN_BRANCH": 5,
    "C86_VINVIN_BRANCH": 6,
    "O23_ENDPOINT": 7,
    "BENNA_TEMPLATE": 8,
    "HYBRID_BOUNDARY": 9,
    "RESIDUAL": 99,
}


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def classify(nodes: list[str], scoped: list[str], audit: list[str], rejected: list[str]) -> str:
    joined = " ".join(nodes)
    if "BOOK42_HANDOFF" in joined:
        return "HYBRID_BOUNDARY"
    if "NAESE_C68_FATCT_CANONICAL_SLOT_CORE" in joined and "R02_TRVEIIVNTBB_BRIDGE" in joined:
        return "NAESE_R02_PAIR"
    if "FNAAST_O23_ENDPOINT_WINDOW" in joined and scoped:
        return "O23_ENDPOINT"
    if "C86_VINVIN_BRANCH_PAYLOAD" in joined:
        return "C86_VINVIN_BRANCH"
    if "VINVIN_BRANCH_SUBFUNCTION" in joined:
        return "VINVIN_BRANCH"
    if "C86_VNCTIIN_CONTEXT_PAYLOAD" in joined and "NAESE_CANONICAL_SLOT_WINDOW" in joined:
        return "CONTEXT_SLOT"
    if "TAILBETFTE_SUFFIX_FRAME" in joined and "C86_VNCTIIN_CONTEXT_PAYLOAD" in joined and "BENNA_FORMULA_BRIDGE" in joined:
        return "FORMULA_HANDOFF_CONTEXT"
    if "TAILBETFTE_SUFFIX_FRAME" in joined and "C86_VNCTIIN_CONTEXT_PAYLOAD" in joined:
        return "HANDOFF_CONTEXT"
    if "BENNA_IAVNALLBEE_TEMPLATE_WINDOW" in joined:
        return "BENNA_TEMPLATE"
    if "BENNA" in joined or "FNAAST_FORMULA_NSBVN_WINDOW" in joined:
        return "FORMULA_HEAD"
    return "RESIDUAL"


def main() -> None:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS bridge_grammar_reconstruction_probe_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            exact_order_count INTEGER NOT NULL,
            contig_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS bridge_grammar_reconstruction_probe_items (
            run_id INTEGER NOT NULL,
            basecontigid TEXT NOT NULL,
            status TEXT NOT NULL,
            expected_order TEXT NOT NULL,
            predicted_order TEXT NOT NULL,
            stage_sequence_json TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, basecontigid)
        )
        """
    )

    book_rows = {
        str(r["bookid"]): r
        for r in conn.execute(
            """
            SELECT bookid, accepted_nodes_json, audit_nodes_json, scoped_nodes_json, rejected_nodes_json
            FROM book_structural_reading_v1_items
            WHERE run_id=(SELECT max(run_id) FROM book_structural_reading_v1_runs)
            """
        )
    }
    stages = {}
    for bookid, row in book_rows.items():
        nodes = json.loads(row["accepted_nodes_json"] or "[]")
        audit = json.loads(row["audit_nodes_json"] or "[]")
        scoped = json.loads(row["scoped_nodes_json"] or "[]")
        rejected = json.loads(row["rejected_nodes_json"] or "[]")
        stage = classify(nodes, scoped, audit, rejected)
        stages[bookid] = stage

    results = []
    for row in conn.execute(
        "SELECT basecontigid, booksinorder FROM sheet__contigs WHERE __export_id=(SELECT max(__export_id) FROM sheet__contigs)"
    ):
        contig_id = str(row["basecontigid"])
        expected = [x.strip() for x in (row["booksinorder"] or "").split("->") if x.strip()]
        predicted = sorted(expected, key=lambda b: (STAGE_ORDER.get(stages[b], 99), int(b)))
        status = "EXACT_ORDER_RECOVERED" if predicted == expected else "ORDER_NOT_RECOVERED"
        results.append(
            {
                "basecontigid": contig_id,
                "status": status,
                "expected": expected,
                "predicted": predicted,
                "stage_sequence": [{"bookid": b, "stage": stages[b], "rank": STAGE_ORDER.get(stages[b], 99)} for b in expected],
            }
        )

    exact = sum(1 for r in results if r["status"] == "EXACT_ORDER_RECOVERED")
    if exact >= 4:
        decision = "BRIDGE_GRAMMAR_RECOVERS_MOST_CONTIG_ORDER_NO_GLOSS"
    elif exact > 0:
        decision = "BRIDGE_GRAMMAR_PARTIAL_ORDER_SIGNAL_AUDIT_ONLY"
    else:
        decision = "BRIDGE_GRAMMAR_ORDER_RECOVERY_FAILS"
    cur = conn.execute(
        """
        INSERT INTO bridge_grammar_reconstruction_probe_runs
        (created_at, decision, exact_order_count, contig_count, payload_json)
        VALUES (?, ?, ?, ?, ?)
        """,
        (now(), decision, exact, len(results), json.dumps({"stage_order": STAGE_ORDER}, sort_keys=True)),
    )
    run_id = int(cur.lastrowid)
    for r in results:
        conn.execute(
            """
            INSERT INTO bridge_grammar_reconstruction_probe_items
            (run_id, basecontigid, status, expected_order, predicted_order, stage_sequence_json, evidence_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                r["basecontigid"],
                r["status"],
                "->".join(r["expected"]),
                "->".join(r["predicted"]),
                json.dumps(r["stage_sequence"], sort_keys=True),
                json.dumps({"no_gloss": True}, sort_keys=True),
            ),
        )
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": decision, "exact_order_count": exact, "contig_count": len(results), "results": results}, ensure_ascii=False))


if __name__ == "__main__":
    main()
