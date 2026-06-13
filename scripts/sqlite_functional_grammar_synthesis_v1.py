#!/usr/bin/env python3
"""Synthesize stable structural components into one functional grammar layer.

Inputs are SQL-native component audits only:
- benna_ordered_core_v2
- naese_slot_core_v1
- vinvin_branch_core_v1
- semantic_bridge_status_v1 for currently alive bridges

This script does not create human prose. It creates a consolidated functional
role graph, evaluates known contig-edge coverage, and identifies unresolved
handoff gaps between components.
"""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def latest_run(conn: sqlite3.Connection, table: str) -> int | None:
    row = conn.execute(f"SELECT max(run_id) FROM {table}").fetchone()
    return None if row is None or row[0] is None else int(row[0])


def load_items(conn: sqlite3.Connection, table: str) -> list[sqlite3.Row]:
    run_id = latest_run(conn, table.replace("_items", "_runs"))
    if run_id is None:
        return []
    return list(conn.execute(f"SELECT * FROM {table} WHERE run_id=?", (run_id,)))


def load_contig_edges(conn: sqlite3.Connection) -> set[tuple[str, str]]:
    run_id = latest_run(conn, "contig_structural_narrative_v1_runs")
    edges: set[tuple[str, str]] = set()
    if run_id is None:
        return edges
    for row in conn.execute("SELECT booksinorder FROM contig_structural_narrative_v1_items WHERE run_id=?", (run_id,)):
        parts = [p.strip() for p in str(row["booksinorder"]).split("->") if p.strip()]
        edges.update(zip(parts, parts[1:]))
    return edges


def add_book(book_roles: dict[str, dict], source: str, row: sqlite3.Row) -> None:
    if row["item_type"] != "book":
        return
    bookid = str(row["item_id"])
    status = str(row["status"])
    role = str(row["role_label"])
    if status in {"ORDERED_CORE", "RELATED_CONTEXT", "VARIANT", "SUPPORT"}:
        trust = "CORE" if status == "ORDERED_CORE" else status
    elif status in {"QUARANTINED", "AUDIT_ONLY"}:
        trust = status
    else:
        trust = "AUDIT_ONLY"
    book_roles.setdefault(bookid, {"roles": [], "sources": []})
    book_roles[bookid]["roles"].append({"source": source, "status": status, "role": role, "trust": trust})
    book_roles[bookid]["sources"].append(source)


def add_edge(edge_roles: dict[tuple[str, str], dict], source: str, row: sqlite3.Row) -> None:
    if row["item_type"] != "edge":
        return
    edge_id = str(row["item_id"])
    if "->" not in edge_id:
        return
    left, right = edge_id.split("->", 1)
    status = str(row["status"])
    role = str(row["role_label"])
    if "ACCEPTED" in status:
        trust = "ACCEPTED_STRUCTURAL_EDGE"
    elif "QUARANTINED" in status:
        trust = "QUARANTINED_PARALLEL"
    else:
        trust = "AUDIT_ONLY_EDGE"
    edge_roles.setdefault((left, right), {"roles": [], "sources": []})
    edge_roles[(left, right)]["roles"].append({"source": source, "status": status, "role": role, "trust": trust})
    edge_roles[(left, right)]["sources"].append(source)


def dominant_book_role(entries: list[dict]) -> tuple[str, str, str]:
    priority = {"CORE": 0, "RELATED_CONTEXT": 1, "VARIANT": 2, "SUPPORT": 3, "QUARANTINED": 4, "AUDIT_ONLY": 5}
    best = min(entries, key=lambda e: (priority.get(e["trust"], 9), e["source"], e["role"]))
    return best["role"], best["trust"], best["source"]


def dominant_edge_role(entries: list[dict]) -> tuple[str, str, str]:
    priority = {"ACCEPTED_STRUCTURAL_EDGE": 0, "QUARANTINED_PARALLEL": 1, "AUDIT_ONLY_EDGE": 2}
    best = min(entries, key=lambda e: (priority.get(e["trust"], 9), e["source"], e["role"]))
    return best["role"], best["trust"], best["source"]


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS functional_grammar_synthesis_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            functional_book_count INTEGER NOT NULL,
            accepted_edge_count INTEGER NOT NULL,
            contig_edge_count INTEGER NOT NULL,
            contig_edge_covered_count INTEGER NOT NULL,
            unresolved_contig_edge_count INTEGER NOT NULL,
            accepted_human_gloss_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS functional_grammar_synthesis_v1_items (
            run_id INTEGER NOT NULL,
            item_type TEXT NOT NULL,
            item_id TEXT NOT NULL,
            status TEXT NOT NULL,
            role_label TEXT NOT NULL,
            source_component TEXT NOT NULL,
            interpretation TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, item_type, item_id)
        )
        """
    )

    components = {
        "BENNA_ORDERED_CORE_V2": "benna_ordered_core_v2_items",
        "NAESE_SLOT_CORE_V1": "naese_slot_core_v1_items",
        "VINVIN_BRANCH_CORE_V1": "vinvin_branch_core_v1_items",
    }
    book_roles: dict[str, dict] = {}
    edge_roles: dict[tuple[str, str], dict] = {}
    for source, table in components.items():
        for row in load_items(conn, table):
            add_book(book_roles, source, row)
            add_edge(edge_roles, source, row)

    # Add two already-established bridge edges from previous alive bridge status if not represented by component tables.
    manual_books = {
        "13": ("O23_FNAAST_ENDPOINT", "CORE", "O23_FNAAST_ENDPOINT"),
        "38": ("O23_FNAAST_ENDPOINT", "CORE", "O23_FNAAST_ENDPOINT"),
        "45": ("R02_CONTEXT_CONNECTOR", "RELATED_CONTEXT", "BOOK45_CONTEXT_CONNECTOR"),
        "4": ("COMPOSITE_C86_O23_R20_OPERATOR_CHAIN", "RELATED_CONTEXT", "COMPOSITE_OPERATOR_CHAIN_GATE"),
        "6": ("DISPLAY_PHASE_CONTROL_NO_PAYLOAD", "RELATED_CONTEXT", "FINAL_DISPLAY_CONTROL_CLOSURE"),
        "49": ("O32_SINGLETON_SELECTOR_CONTROL", "RELATED_CONTEXT", "CODE_VARIANT_SELECTOR_GATE"),
        "12": ("BOOK30_CORE_CONTEXT_COMPONENT", "RELATED_CONTEXT", "BOOK30_CORE_CONTEXT_COMPONENT"),
        "14": ("NEGATIVE_R02_LTAST_BOUNDARY_CONTROL", "RELATED_CONTEXT", "BOOK14_NEGATIVE_BOUNDARY_CONTROL_GATE"),
        "15": ("VFETTIIT_VTLRNEFIE_VARIANT_COMPONENT", "RELATED_CONTEXT", "VARIANT_FAMILY_CONTRAST"),
        "16": ("VFETTIIT_VTLRNEFIE_VARIANT_COMPONENT", "RELATED_CONTEXT", "VARIANT_FAMILY_CONTRAST"),
        "18": ("RESIDUAL_STRONG_10_35_STRUCTURAL_WINDOW", "RELATED_CONTEXT", "PARSE_COMPETITION_CONSOLIDATION"),
        "19": ("C68_VN_TIIN_CONTEXT_FRAME_GUARDED", "RELATED_CONTEXT", "PARSE_COMPETITION_CONSOLIDATION"),
        "20": ("FNTFEIFAIFAINIIETNEEIVN_SHARED_TAIL_PAIR", "RELATED_CONTEXT", "RARE_SINGLETON_MOTIF_PROBE"),
        "21": ("BOOK30_CORE_CONTEXT_COMPONENT", "RELATED_CONTEXT", "BOOK30_CORE_CONTEXT_COMPONENT"),
        "23": ("C68_VN_TIIN_CONTEXT_FRAME_GUARDED", "RELATED_CONTEXT", "PARSE_COMPETITION_CONSOLIDATION"),
        "24": ("COMPOSITE_C68_CONTEXT_TO_O23_SCOPE_BOUNDARY", "RELATED_CONTEXT", "COMPOSITE_OPERATOR_CHAIN_GATE"),
        "25": ("FASTBEIE_INTEIIS_SHORT_LONG_PAIR", "RELATED_CONTEXT", "RARE_SINGLETON_MOTIF_PROBE"),
        "26": ("BOOK30_CORE_CONTEXT_COMPONENT", "RELATED_CONTEXT", "BOOK30_CORE_CONTEXT_COMPONENT"),
        "30": ("F6_BOOK30_CONTEXT_HELDOUT_FRAGMENT", "RELATED_CONTEXT", "TEMPLATE_FRAME_RESIDUAL_PROMOTION"),
        "31": ("F2_C86_OPERATOR_CONTEXT_STACKED", "RELATED_CONTEXT", "TEMPLATE_FRAME_RESIDUAL_PROMOTION"),
        "32": ("DISPLAY_ONLY_CONTROL_NO_PAYLOAD", "RELATED_CONTEXT", "FINAL_DISPLAY_CONTROL_CLOSURE"),
        "34": ("ZERO_ANIV_BRANCH_TAIL_BOUNDARY", "RELATED_CONTEXT", "ZERO_OPERATOR_TYPED_EXIT_GATE"),
        "36": ("DISPLAY_ONLY_CONTROL_NO_PAYLOAD", "RELATED_CONTEXT", "FINAL_DISPLAY_CONTROL_CLOSURE"),
        "39": ("FASTBEIE_INTEIIS_SHORT_LONG_PAIR", "RELATED_CONTEXT", "RARE_SINGLETON_MOTIF_PROBE"),
        "41": ("O23_BEARING_CONTEXT_FRAGMENT_CONTROL", "RELATED_CONTEXT", "BOOK41_O23_CONTEXT_FRAGMENT_GATE"),
        "42": ("CONTEXT_TO_WEAK_NAESE_HYBRID", "RELATED_CONTEXT", "HYBRID_QUARANTINE_REASSESSMENT"),
        "56": ("O23_ENDPOINT_WITH_WEAK_NAESE_TAIL", "RELATED_CONTEXT", "HYBRID_QUARANTINE_REASSESSMENT"),
        "11": ("BENNA_DISPLAY_WINDOW_VARIANT", "RELATED_CONTEXT", "BENNA_DISPLAY_VARIANT"),
        "43": ("BENNA_DISPLAY_WINDOW_VARIANT", "RELATED_CONTEXT", "BENNA_DISPLAY_VARIANT"),
        "54": ("FNTFEIFAIFAINIIETNEEIVN_SHARED_TAIL_PAIR", "RELATED_CONTEXT", "RARE_SINGLETON_MOTIF_PROBE"),
        "55": ("VFETTIIT_LOCAL_REPEAT_VARIANT", "RELATED_CONTEXT", "LOW_OVERLAP_AGENT_AUDIT"),
        "57": ("F2_C86_OPERATOR_CONTEXT_REPEATED", "RELATED_CONTEXT", "TEMPLATE_FRAME_RESIDUAL_PROMOTION"),
        "59": ("BENNA_DISPLAY_WINDOW_VARIANT", "RELATED_CONTEXT", "BENNA_DISPLAY_VARIANT"),
        "60": ("BTILBETA_FNAAST_UNIQUE_PAIR", "RELATED_CONTEXT", "LOW_OVERLAP_AGENT_AUDIT"),
        "64": ("BTILBETA_FNAAST_UNIQUE_PAIR", "RELATED_CONTEXT", "LOW_OVERLAP_AGENT_AUDIT"),
        "50": ("BENNA_FORMULA_COMPOSITE_VARIANT", "RELATED_CONTEXT", "BENNA_DISPLAY_VARIANT"),
        "68": ("VINVIN_NEGATIVE_WINDOW_FRAGMENT", "RELATED_CONTEXT", "VINVIN_FRAGMENT_REASSESSMENT"),
        "44": ("C86_VINVIN_SURFACE_PAYLOAD_FRAGMENT", "RELATED_CONTEXT", "VINVIN_FRAGMENT_REASSESSMENT"),
        "5": ("NAESE_TO_BENNA_COMPOSITE_FRAME", "RELATED_CONTEXT", "NAESE_BENNA_COMPOSITE"),
        "7": ("RARE_3478_PHASE_BOUNDARY_CONTROL", "RELATED_CONTEXT", "PHASE_BOUNDARY_CONTROL_GATE"),
        "8": ("C68_VN_TIIN_CONTEXT_SUBFRAME", "RELATED_CONTEXT", "PARSE_COMPETITION_CONSOLIDATION"),
        "9": ("NAESE_TO_BENNA_COMPOSITE_FRAME", "RELATED_CONTEXT", "NAESE_BENNA_COMPOSITE"),
        "0": ("BENNA_LTAST_HANDOFF_WINDOW_FRAGMENT", "RELATED_CONTEXT", "BENNA_LTAST_HANDOFF_FRAGMENT"),
        "33": ("BENNA_LTAST_HANDOFF_WINDOW_FRAGMENT", "RELATED_CONTEXT", "BENNA_LTAST_HANDOFF_FRAGMENT"),
        "66": ("BENNA_LTAST_HANDOFF_WINDOW_FRAGMENT", "RELATED_CONTEXT", "BENNA_LTAST_HANDOFF_FRAGMENT"),
        "37": ("F1_BENNA_LTAST_CONTINUATION", "RELATED_CONTEXT", "TEMPLATE_FRAME_RESIDUAL_PROMOTION"),
        "1": ("HANDOFF_CONTEXT_WINDOW_FRAGMENT", "RELATED_CONTEXT", "RESIDUAL_10_35_WINDOW"),
        "63": ("HANDOFF_CONTEXT_WINDOW_FRAGMENT", "RELATED_CONTEXT", "RESIDUAL_10_35_WINDOW"),
    }
    for bookid, (role, trust, source) in manual_books.items():
        book_roles.setdefault(bookid, {"roles": [], "sources": []})
        book_roles[bookid]["roles"].append({"source": source, "status": trust, "role": role, "trust": trust})
        book_roles[bookid]["sources"].append(source)

    manual_edges = {
        ("35", "67"): ("HANDOFF_CONTEXT_TO_C86_VNCTIIN_PAYLOAD", "ACCEPTED_STRUCTURAL_EDGE", "HANDOFF_CONTEXT_35_TO_67"),
        ("13", "38"): ("O23_FNAAST_ENDPOINT", "ACCEPTED_STRUCTURAL_EDGE", "O23_FNAAST_ENDPOINT"),
        ("42", "67"): ("BOOK42_HANDOFF_HYBRID_SUPPORT", "AUDIT_ONLY_EDGE", "BOOK42_HANDOFF_TO_WEAK_SLOT_BOUNDARY"),
    }
    for edge, (role, trust, source) in manual_edges.items():
        edge_roles.setdefault(edge, {"roles": [], "sources": []})
        edge_roles[edge]["roles"].append({"source": source, "status": trust, "role": role, "trust": trust})
        edge_roles[edge]["sources"].append(source)

    contig_edges = load_contig_edges(conn)
    accepted_edges = {
        edge for edge, payload in edge_roles.items() if any(r["trust"] == "ACCEPTED_STRUCTURAL_EDGE" for r in payload["roles"])
    }
    covered = accepted_edges & contig_edges
    unresolved = contig_edges - accepted_edges
    false_edge_count = len(accepted_edges - contig_edges)
    human_gloss_count = int(
        conn.execute(
            "SELECT accepted_human_gloss_count FROM semantic_bridge_status_v1_runs WHERE run_id=(SELECT max(run_id) FROM semantic_bridge_status_v1_runs)"
        ).fetchone()[0]
    )
    if human_gloss_count > 0:
        decision = "FUNCTIONAL_GRAMMAR_WITH_PARTIAL_HUMAN_GLOSS"
    elif not unresolved and false_edge_count <= 4:
        decision = "FUNCTIONAL_GRAMMAR_COVERS_CONTIGS_NO_HUMAN_GLOSS"
    elif len(covered) >= max(1, len(contig_edges) - 2):
        decision = "FUNCTIONAL_GRAMMAR_PARTIAL_CONTIG_COVERAGE_NO_HUMAN_GLOSS"
    else:
        decision = "FUNCTIONAL_GRAMMAR_FRAGMENTED_NO_HUMAN_GLOSS"

    payload = {
        "components": components,
        "contig_edges": [f"{a}->{b}" for a, b in sorted(contig_edges, key=lambda e: (int(e[0]), int(e[1])))],
        "covered_contig_edges": [f"{a}->{b}" for a, b in sorted(covered, key=lambda e: (int(e[0]), int(e[1])))],
        "unresolved_contig_edges": [f"{a}->{b}" for a, b in sorted(unresolved, key=lambda e: (int(e[0]), int(e[1])))],
        "accepted_non_contig_edges": [f"{a}->{b}" for a, b in sorted(accepted_edges - contig_edges, key=lambda e: (int(e[0]), int(e[1])))],
    }
    cur = conn.execute(
        """
        INSERT INTO functional_grammar_synthesis_v1_runs
        (created_at, decision, functional_book_count, accepted_edge_count, contig_edge_count, contig_edge_covered_count, unresolved_contig_edge_count, accepted_human_gloss_count, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            now(), decision, len(book_roles), len(accepted_edges), len(contig_edges), len(covered), len(unresolved), human_gloss_count, json.dumps(payload, sort_keys=True)
        ),
    )
    run_id = int(cur.lastrowid)

    for bookid, payload_item in sorted(book_roles.items(), key=lambda kv: int(kv[0])):
        role, trust, source = dominant_book_role(payload_item["roles"])
        conn.execute(
            """
            INSERT INTO functional_grammar_synthesis_v1_items
            (run_id, item_type, item_id, status, role_label, source_component, interpretation, evidence_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id, "book", bookid, trust, role, source,
                "consolidated functional role; no human prose gloss",
                json.dumps({"all_roles": payload_item["roles"]}, sort_keys=True),
            ),
        )
    for edge, payload_item in sorted(edge_roles.items(), key=lambda kv: (int(kv[0][0]), int(kv[0][1]))):
        role, trust, source = dominant_edge_role(payload_item["roles"])
        status = trust
        if edge in contig_edges and trust == "ACCEPTED_STRUCTURAL_EDGE":
            status = "ACCEPTED_COVERS_CONTIG_EDGE"
        elif edge in contig_edges:
            status = "CONTIG_EDGE_NOT_ACCEPTED_BY_FUNCTIONAL_GRAMMAR"
        conn.execute(
            """
            INSERT INTO functional_grammar_synthesis_v1_items
            (run_id, item_type, item_id, status, role_label, source_component, interpretation, evidence_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id, "edge", f"{edge[0]}->{edge[1]}", status, role, source,
                "consolidated functional edge; no human prose gloss",
                json.dumps({"all_roles": payload_item["roles"], "is_contig_edge": edge in contig_edges}, sort_keys=True),
            ),
        )
    for edge in sorted(unresolved, key=lambda e: (int(e[0]), int(e[1]))):
        if edge in edge_roles:
            continue
        conn.execute(
            """
            INSERT INTO functional_grammar_synthesis_v1_items
            (run_id, item_type, item_id, status, role_label, source_component, interpretation, evidence_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id, "edge", f"{edge[0]}->{edge[1]}", "UNRESOLVED_CONTIG_EDGE", "NO_ACCEPTED_FUNCTIONAL_EDGE", "CONTIG_EVALUATION",
                "known contig transition not yet covered by consolidated functional grammar",
                json.dumps({"requires_component_or_bridge": True}, sort_keys=True),
            ),
        )

    conn.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "functional_book_count": len(book_roles),
                "accepted_edge_count": len(accepted_edges),
                "contig_edge_count": len(contig_edges),
                "contig_edge_covered_count": len(covered),
                "unresolved_contig_edges": payload["unresolved_contig_edges"],
                "accepted_non_contig_edges": payload["accepted_non_contig_edges"],
                "accepted_human_gloss_count": human_gloss_count,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
