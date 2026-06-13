#!/usr/bin/env python3
"""Operational grammar reconstruction probe for Bonelord row0 structure.

This probe asks a narrow question: can the current SQL-native structural layer
predict known contig adjacencies from book-internal evidence alone?

It intentionally does not use contig order while scoring candidate edges. The
known contigs are loaded only at the end as an evaluation target. Passing this
supports a real operational grammar layer; it still does not create human
semantic gloss.
"""

from __future__ import annotations

import datetime as dt
import json
import random
import sqlite3
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
DISCORD_CHANNEL = "0"


@dataclass(frozen=True)
class Book:
    bookid: str
    accepted: tuple[str, ...]
    audit: tuple[str, ...]
    scoped: tuple[str, ...]
    literal: str


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json_list(value: str) -> tuple[str, ...]:
    try:
        parsed = json.loads(value or "[]")
    except json.JSONDecodeError:
        return ()
    return tuple(str(x) for x in parsed if x is not None)


def classify_states(book: Book) -> set[str]:
    nodes = set(book.accepted) | set(book.audit) | set(book.scoped)
    states: set[str] = set()
    if "BENNA_IAVNALLBEE_TEMPLATE_WINDOW" in nodes:
        states.add("BENNA_TEMPLATE")
    if "BENNA_FORMULA_BRIDGE" in nodes or "FNAAST_FORMULA_NSBVN_WINDOW" in nodes or "BENNA_NSBVN_DISPLAY_WINDOW" in nodes:
        states.add("FORMULA_POOL")
    if "TAILBETFTE_SUFFIX_FRAME" in nodes:
        states.add("HANDOFF_CONTEXT")
    if "VNCTIIN_CONTEXT_FRAME" in nodes or "C86_VNCTIIN_CONTEXT_PAYLOAD" in nodes:
        states.add("CONTEXT_PAYLOAD")
    if "NAESE_CANONICAL_SLOT_WINDOW" in nodes or "NAESE_C68_FATCT_CANONICAL_SLOT_CORE" in nodes:
        states.add("NAESE_SLOT")
    if "R02_TRVEIIVNTBB_BRIDGE" in nodes:
        states.add("R02_SLOT_BRIDGE")
    if "VINVIN_BRANCH_SUBFUNCTION" in nodes and "R20_VAETRFEVAST_BLOCK" in nodes:
        states.add("VINVIN_R20_BRANCH")
    if "C86_VINVIN_BRANCH_PAYLOAD" in nodes or "C86_VINVIN_3_17_62_WITH_52_62_EDGE" in nodes:
        states.add("C86_VINVIN_BRANCH")
    if "FNAAST_O23_ENDPOINT_WINDOW" in nodes or "O23_ONAF_VEINLETFNAAST_PAYLOAD_CONTEXT" in nodes:
        states.add("O23_ENDPOINT")
    if "UNIQUE_SIGNATURE_BOOK_42" in nodes or "NAESE_WEAK_AUDIT_42_56" in nodes:
        states.add("BOOK42_HYBRID_BOUNDARY")
    if not states:
        states.add("OTHER")
    return states


TRANSITION_PRIORS: dict[tuple[str, str], float] = {
    ("BENNA_TEMPLATE", "FORMULA_POOL"): 1.0,
    ("FORMULA_POOL", "HANDOFF_CONTEXT"): 1.0,
    ("FORMULA_POOL", "CONTEXT_PAYLOAD"): 0.72,
    ("HANDOFF_CONTEXT", "CONTEXT_PAYLOAD"): 1.0,
    ("CONTEXT_PAYLOAD", "NAESE_SLOT"): 1.0,
    ("CONTEXT_PAYLOAD", "BOOK42_HYBRID_BOUNDARY"): 0.65,
    ("BOOK42_HYBRID_BOUNDARY", "NAESE_SLOT"): 0.58,
    ("NAESE_SLOT", "NAESE_SLOT"): 0.86,
    ("R02_SLOT_BRIDGE", "R02_SLOT_BRIDGE"): 0.92,
    ("R02_SLOT_BRIDGE", "NAESE_SLOT"): 0.78,
    ("NAESE_SLOT", "R02_SLOT_BRIDGE"): 0.78,
    ("VINVIN_R20_BRANCH", "VINVIN_R20_BRANCH"): 0.86,
    ("VINVIN_R20_BRANCH", "C86_VINVIN_BRANCH"): 0.64,
    ("C86_VINVIN_BRANCH", "C86_VINVIN_BRANCH"): 0.94,
    ("O23_ENDPOINT", "O23_ENDPOINT"): 0.92,
}


def max_suffix_prefix_overlap(left: str, right: str, max_len: int = 80) -> int:
    limit = min(len(left), len(right), max_len)
    best = 0
    for size in range(1, limit + 1):
        if left[-size:] == right[:size]:
            best = size
    return best


def state_prior(left_states: set[str], right_states: set[str]) -> tuple[float, tuple[str, str] | None]:
    best_score = 0.0
    best_pair = None
    for left in left_states:
        for right in right_states:
            score = TRANSITION_PRIORS.get((left, right), 0.0)
            if score > best_score:
                best_score = score
                best_pair = (left, right)
    return best_score, best_pair


def edge_score(left: Book, right: Book, states: dict[str, set[str]]) -> dict:
    overlap = max_suffix_prefix_overlap(left.literal, right.literal)
    prior, transition = state_prior(states[left.bookid], states[right.bookid])
    shared_nodes = len((set(left.accepted) | set(left.audit) | set(left.scoped)) & (set(right.accepted) | set(right.audit) | set(right.scoped)))
    # Structural prior gates the edge; raw overlap and shared nodes rank within compatible states.
    score = (prior * 100.0) + min(overlap, 60) + min(shared_nodes, 5) * 4.0
    if prior <= 0:
        score = min(overlap, 60) * 0.35 + min(shared_nodes, 5)
    return {
        "score": round(score, 4),
        "overlap": overlap,
        "prior": prior,
        "transition": list(transition) if transition else None,
        "shared_nodes": shared_nodes,
    }


def load_books(conn: sqlite3.Connection) -> dict[str, Book]:
    run_id = conn.execute("SELECT max(run_id) FROM book_structural_reading_v1_runs").fetchone()[0]
    rows = conn.execute(
        """
        SELECT bookid, accepted_nodes_json, audit_nodes_json, scoped_nodes_json, literal_text
        FROM book_structural_reading_v1_items
        WHERE run_id=?
        """,
        (run_id,),
    ).fetchall()
    return {
        str(r["bookid"]): Book(
            bookid=str(r["bookid"]),
            accepted=load_json_list(r["accepted_nodes_json"]),
            audit=load_json_list(r["audit_nodes_json"]),
            scoped=load_json_list(r["scoped_nodes_json"]),
            literal=str(r["literal_text"] or ""),
        )
        for r in rows
    }


def load_target_edges(conn: sqlite3.Connection) -> set[tuple[str, str]]:
    run_id = conn.execute("SELECT max(run_id) FROM contig_structural_narrative_v1_runs").fetchone()[0]
    edges: set[tuple[str, str]] = set()
    for row in conn.execute(
        "SELECT booksinorder FROM contig_structural_narrative_v1_items WHERE run_id=?", (run_id,)
    ):
        ids = [part.strip() for part in str(row["booksinorder"]).split("->") if part.strip()]
        edges.update(zip(ids, ids[1:]))
    return edges


def top_edges_for_sources(scores: dict[tuple[str, str], dict], top_n: int = 3) -> set[tuple[str, str]]:
    by_source: dict[str, list[tuple[tuple[str, str], dict]]] = {}
    for edge, payload in scores.items():
        by_source.setdefault(edge[0], []).append((edge, payload))
    selected: set[tuple[str, str]] = set()
    for items in by_source.values():
        items.sort(key=lambda item: (-item[1]["score"], -item[1]["overlap"], int(item[0][1])))
        selected.update(edge for edge, _ in items[:top_n])
    return selected


def evaluate(predicted_edges: set[tuple[str, str]], target_edges: set[tuple[str, str]]) -> dict:
    hits = sorted(predicted_edges & target_edges, key=lambda e: (int(e[0]), int(e[1])))
    missing = sorted(target_edges - predicted_edges, key=lambda e: (int(e[0]), int(e[1])))
    false_positive_count = len(predicted_edges - target_edges)
    precision = len(hits) / max(1, len(predicted_edges))
    recall = len(hits) / max(1, len(target_edges))
    f1 = 2 * precision * recall / max(0.000001, precision + recall)
    return {
        "hits": [f"{a}->{b}" for a, b in hits],
        "missing": [f"{a}->{b}" for a, b in missing],
        "false_positive_count": false_positive_count,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
    }


def shuffled_recall(books: dict[str, Book], target_edges: set[tuple[str, str]], predicted_count_by_source: dict[str, int]) -> float:
    rng = random.Random(469)
    ids = sorted(books.keys(), key=int)
    fake: set[tuple[str, str]] = set()
    for source, count in predicted_count_by_source.items():
        choices = [x for x in ids if x != source]
        rng.shuffle(choices)
        for target in choices[:count]:
            fake.add((source, target))
    return len(fake & target_edges) / max(1, len(target_edges))


def decision_for(metrics: dict, shuffled: float) -> str:
    recall = float(metrics["recall"])
    if recall >= 0.75 and recall - shuffled >= 0.35:
        return "OPERATIONAL_GRAMMAR_RECONSTRUCTS_CONTIG_EDGES_NO_HUMAN_GLOSS"
    if recall >= 0.50 and recall > shuffled:
        return "OPERATIONAL_GRAMMAR_PARTIAL_SIGNAL_AUDIT_ONLY"
    return "OPERATIONAL_GRAMMAR_INSUFFICIENT_CONTIG_RECONSTRUCTION"


def main() -> None:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS operational_grammar_reconstruction_probe_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            predicted_edge_count INTEGER NOT NULL,
            target_edge_count INTEGER NOT NULL,
            hit_count INTEGER NOT NULL,
            recall REAL NOT NULL,
            shuffled_recall REAL NOT NULL,
            payload_json TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS operational_grammar_reconstruction_probe_items (
            run_id INTEGER NOT NULL,
            source_bookid TEXT NOT NULL,
            target_bookid TEXT NOT NULL,
            predicted INTEGER NOT NULL,
            target INTEGER NOT NULL,
            score REAL NOT NULL,
            overlap INTEGER NOT NULL,
            prior REAL NOT NULL,
            transition_json TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, source_bookid, target_bookid)
        )
        """
    )

    books = load_books(conn)
    states = {bookid: classify_states(book) for bookid, book in books.items()}
    target_edges = load_target_edges(conn)
    scores: dict[tuple[str, str], dict] = {}
    for left_id, left in books.items():
        for right_id, right in books.items():
            if left_id == right_id:
                continue
            payload = edge_score(left, right, states)
            if payload["prior"] > 0 or payload["overlap"] >= 12:
                scores[(left_id, right_id)] = payload

    predicted_edges = top_edges_for_sources(scores, top_n=3)
    predicted_count_by_source: dict[str, int] = {}
    for source, _ in predicted_edges:
        predicted_count_by_source[source] = predicted_count_by_source.get(source, 0) + 1
    metrics = evaluate(predicted_edges, target_edges)
    shuffle = shuffled_recall(books, target_edges, predicted_count_by_source)
    decision = decision_for(metrics, shuffle)

    payload = {
        "method": "state-compatible row0 suffix-prefix graph; contigs used only for final evaluation",
        "states_by_book": {k: sorted(v) for k, v in states.items()},
        "target_edges": [f"{a}->{b}" for a, b in sorted(target_edges, key=lambda e: (int(e[0]), int(e[1])))],
        "metrics": metrics,
    }
    cur = conn.execute(
        """
        INSERT INTO operational_grammar_reconstruction_probe_runs
        (created_at, decision, predicted_edge_count, target_edge_count, hit_count, recall, shuffled_recall, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            now(),
            decision,
            len(predicted_edges),
            len(target_edges),
            len(metrics["hits"]),
            metrics["recall"],
            round(shuffle, 4),
            json.dumps(payload, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)

    interesting = set(predicted_edges) | set(target_edges)
    for edge in sorted(interesting, key=lambda e: (int(e[0]), int(e[1]))):
        payload = scores.get(edge) or edge_score(books[edge[0]], books[edge[1]], states)
        conn.execute(
            """
            INSERT INTO operational_grammar_reconstruction_probe_items
            (run_id, source_bookid, target_bookid, predicted, target, score, overlap, prior, transition_json, evidence_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                edge[0],
                edge[1],
                int(edge in predicted_edges),
                int(edge in target_edges),
                payload["score"],
                payload["overlap"],
                payload["prior"],
                json.dumps(payload["transition"], sort_keys=True),
                json.dumps(
                    {
                        "source_states": sorted(states[edge[0]]),
                        "target_states": sorted(states[edge[1]]),
                        "shared_nodes": payload["shared_nodes"],
                    },
                    sort_keys=True,
                ),
            ),
        )
    conn.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "predicted_edge_count": len(predicted_edges),
                "target_edge_count": len(target_edges),
                "hit_count": len(metrics["hits"]),
                "recall": metrics["recall"],
                "precision": metrics["precision"],
                "f1": metrics["f1"],
                "shuffled_recall": round(shuffle, 4),
                "hits": metrics["hits"],
                "missing": metrics["missing"],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
