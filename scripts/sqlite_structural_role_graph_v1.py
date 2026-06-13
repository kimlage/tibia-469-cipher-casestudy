#!/usr/bin/env python3
"""Materialize structural role graph edges from the no-gloss role registry."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def split_contig_books(booksinorder: str) -> list[str]:
    return [x.strip() for x in (booksinorder or "").split("->") if x.strip()]


def main() -> None:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS structural_role_graph_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            node_count INTEGER NOT NULL,
            edge_count INTEGER NOT NULL,
            semantic_gloss_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS structural_role_graph_v1_edges (
            run_id INTEGER NOT NULL,
            edge_id TEXT NOT NULL,
            source_type TEXT NOT NULL,
            source_id TEXT NOT NULL,
            relation TEXT NOT NULL,
            target_type TEXT NOT NULL,
            target_id TEXT NOT NULL,
            confidence REAL NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, edge_id)
        )
        """
    )

    registry_run = conn.execute("SELECT max(run_id) FROM structural_role_registry_v1_runs").fetchone()[0]
    roles = conn.execute(
        "SELECT role_id, status, role_type, books_json, role_description FROM structural_role_registry_v1_items WHERE run_id=?",
        (registry_run,),
    ).fetchall()

    clusters = {
        str(r["bookid"]): str(r["clusterid"])
        for r in conn.execute(
            "SELECT bookid, clusterid FROM sheet__books WHERE __export_id=(SELECT max(__export_id) FROM sheet__books)"
        )
    }
    contig_positions = []
    for row in conn.execute(
        "SELECT basecontigid, booksinorder FROM sheet__contigs WHERE __export_id=(SELECT max(__export_id) FROM sheet__contigs)"
    ):
        order = split_contig_books(row["booksinorder"])
        for pos, bookid in enumerate(order, 1):
            contig_positions.append((str(row["basecontigid"]), bookid, pos, order))

    npc_rows = []
    try:
        npc_rows = conn.execute(
            "SELECT phrase_id, refname, promotion_status, inbooks_bookids FROM npc_phrase_anchors WHERE coalesce(inbooks_bookids,'')!=''"
        ).fetchall()
    except sqlite3.OperationalError:
        npc_rows = []

    edges = []
    for role in roles:
        role_id = role["role_id"]
        books = json.loads(role["books_json"] or "[]")
        for bookid in books:
            edges.append(
                {
                    "source_type": "role",
                    "source_id": role_id,
                    "relation": "CONSTRAINS_BOOK",
                    "target_type": "book",
                    "target_id": str(bookid),
                    "confidence": 0.8 if role["status"].startswith("ACCEPTED") else 0.65,
                    "evidence": {"role_type": role["role_type"], "status": role["status"]},
                }
            )
            if str(bookid) in clusters:
                edges.append(
                    {
                        "source_type": "role",
                        "source_id": role_id,
                        "relation": "MAPS_TO_CLUSTER",
                        "target_type": "cluster",
                        "target_id": clusters[str(bookid)],
                        "confidence": 0.65,
                        "evidence": {"bookid": str(bookid), "role_type": role["role_type"]},
                    }
                )
        for contig_id, bookid, pos, order in contig_positions:
            if bookid in books:
                edges.append(
                    {
                        "source_type": "role",
                        "source_id": role_id,
                        "relation": "HITS_CONTIG_POSITION",
                        "target_type": "contig_position",
                        "target_id": f"{contig_id}:{bookid}@{pos}",
                        "confidence": 0.75,
                        "evidence": {"contig_id": contig_id, "bookid": bookid, "position": pos, "order": order},
                    }
                )
        for npc in npc_rows:
            npc_books = {x.strip() for x in (npc["inbooks_bookids"] or "").split(",") if x.strip()}
            overlap = sorted(set(books) & npc_books, key=lambda x: int(x))
            if overlap:
                edges.append(
                    {
                        "source_type": "role",
                        "source_id": role_id,
                        "relation": "OVERLAPS_NPC_ANCHOR",
                        "target_type": "npc_phrase",
                        "target_id": str(npc["phrase_id"]),
                        "confidence": 0.55,
                        "evidence": {
                            "refname": npc["refname"],
                            "promotion_status": npc["promotion_status"],
                            "overlap_books": overlap,
                        },
                    }
                )

    cur = conn.execute(
        """
        INSERT INTO structural_role_graph_v1_runs
        (created_at, decision, node_count, edge_count, semantic_gloss_count, payload_json)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            now(),
            "STRUCTURAL_ROLE_GRAPH_CREATED_NO_SEMANTIC_GLOSS",
            len(roles),
            len(edges),
            0,
            json.dumps({"registry_run": registry_run}, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)
    for idx, edge in enumerate(edges, 1):
        edge_id = f"E{idx:04d}"
        conn.execute(
            """
            INSERT INTO structural_role_graph_v1_edges
            (run_id, edge_id, source_type, source_id, relation, target_type, target_id, confidence, evidence_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                edge_id,
                edge["source_type"],
                edge["source_id"],
                edge["relation"],
                edge["target_type"],
                edge["target_id"],
                edge["confidence"],
                json.dumps(edge["evidence"], sort_keys=True),
            ),
        )
    conn.commit()
    summary = conn.execute(
        """
        SELECT source_id, relation, count(*) AS n
        FROM structural_role_graph_v1_edges
        WHERE run_id=?
        GROUP BY source_id, relation
        ORDER BY source_id, relation
        """,
        (run_id,),
    ).fetchall()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": "STRUCTURAL_ROLE_GRAPH_CREATED_NO_SEMANTIC_GLOSS",
                "node_count": len(roles),
                "edge_count": len(edges),
                "summary": [dict(r) for r in summary],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
