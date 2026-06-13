#!/usr/bin/env python3
"""Negative controls for functional tags as structural role constraints.

This pass is SQLite-native and analysis-only. It asks whether a functional tag
is specific within held-out clusters and contig neighborhoods. Passing here does
not create English gloss; it only qualifies a tag as a structural constraint
usable by later semantic work.
"""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"


TARGET_TAGS = {
    "BOOK30_CORE_CONTEXT",
    "O23_ONAF_VEINLETFNAAST_PAYLOAD_CONTEXT",
    "ZERO_PAIR_LOCAL_PAIR_20_54_TRUNCATION_ALIGNMENT",
    "ZERO_PAIR_LOCAL_PAIR_25_39_FAST_BEIE_MICROTEMPLATE",
    "C86_PAYLOAD_OPERATOR",
    "VNCTIIN_CONTEXT_FRAME",
    "BENNA_FORMULA_BRIDGE",
    "TAILBETFTE_SUFFIX_FRAME",
    "VINVIN_BRANCH_SUBFUNCTION",
    "R20_R02_PHASE_FRAME",
    "NAESE_C68_FATCT_LOCAL_SLOT",
}


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_tag(value: str) -> str:
    try:
        if isinstance(value, str) and value.strip().startswith("{"):
            obj = json.loads(value)
            if isinstance(obj, dict):
                return obj.get("tag_id") or obj.get("label") or value
    except Exception:
        pass
    return value


def split_contig_books(booksinorder: str) -> list[str]:
    return [x.strip() for x in (booksinorder or "").split("->") if x.strip()]


def main() -> None:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS structural_role_negative_control_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            accepted_constraint_count INTEGER NOT NULL,
            broad_or_failed_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS structural_role_negative_control_items (
            run_id INTEGER NOT NULL,
            tag_id TEXT NOT NULL,
            status TEXT NOT NULL,
            tag_book_count INTEGER NOT NULL,
            cluster_specificity REAL NOT NULL,
            contig_local_specificity REAL NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, tag_id)
        )
        """
    )

    tag_books: dict[str, set[str]] = defaultdict(set)
    book_tags: dict[str, set[str]] = defaultdict(set)
    for row in conn.execute(
        """
        SELECT b.bookid, j.value AS tag_value
        FROM final_honest_reading_v19_books b, json_each(b.functional_tags_json) j
        WHERE b.run_id=(SELECT max(run_id) FROM final_honest_reading_v19_runs)
        """
    ):
        bookid = str(row["bookid"])
        tag = parse_tag(row["tag_value"])
        tag_books[tag].add(bookid)
        book_tags[bookid].add(tag)

    clusters: dict[str, str] = {}
    cluster_books: dict[str, set[str]] = defaultdict(set)
    for row in conn.execute(
        """
        SELECT bookid, clusterid
        FROM sheet__books
        WHERE __export_id=(SELECT max(__export_id) FROM sheet__books)
        """
    ):
        bookid = str(row["bookid"])
        clusterid = str(row["clusterid"])
        clusters[bookid] = clusterid
        cluster_books[clusterid].add(bookid)

    contigs = []
    for row in conn.execute(
        """
        SELECT basecontigid, booksinorder
        FROM sheet__contigs
        WHERE __export_id=(SELECT max(__export_id) FROM sheet__contigs)
        """
    ):
        contigs.append((str(row["basecontigid"]), split_contig_books(row["booksinorder"])))

    items = []
    for tag in sorted(TARGET_TAGS):
        books = tag_books.get(tag, set())
        if not books:
            items.append(
                {
                    "tag_id": tag,
                    "status": "MISSING_TAG_NO_CONSTRAINT",
                    "tag_book_count": 0,
                    "cluster_specificity": 0.0,
                    "contig_local_specificity": 0.0,
                    "evidence": {"reason": "tag not present in final_honest_reading_v19"},
                }
            )
            continue

        same_cluster_universe = set()
        for book in books:
            cid = clusters.get(book)
            if cid is not None:
                same_cluster_universe.update(cluster_books[cid])
        cluster_specificity = len(books & same_cluster_universe) / max(1, len(same_cluster_universe))

        neighborhood = set()
        contig_hits = []
        for contig_id, order in contigs:
            hit_positions = [i for i, b in enumerate(order) if b in books]
            if not hit_positions:
                continue
            for pos in hit_positions:
                for j in range(max(0, pos - 1), min(len(order), pos + 2)):
                    neighborhood.add(order[j])
            contig_hits.append(
                {
                    "contig_id": contig_id,
                    "hits": [f"{order[i]}@{i+1}" for i in hit_positions],
                    "order": order,
                }
            )
        contig_local_specificity = len(books & neighborhood) / max(1, len(neighborhood))

        if tag in {
            "BOOK30_CORE_CONTEXT",
            "O23_ONAF_VEINLETFNAAST_PAYLOAD_CONTEXT",
            "ZERO_PAIR_LOCAL_PAIR_20_54_TRUNCATION_ALIGNMENT",
            "ZERO_PAIR_LOCAL_PAIR_25_39_FAST_BEIE_MICROTEMPLATE",
        } and cluster_specificity >= 0.95:
            status = "ACCEPT_HELDOUT_CLUSTER_ROLE_CONSTRAINT_NO_GLOSS"
        elif tag in {
            "BENNA_FORMULA_BRIDGE",
            "TAILBETFTE_SUFFIX_FRAME",
            "VINVIN_BRANCH_SUBFUNCTION",
            "C86_PAYLOAD_OPERATOR",
            "VNCTIIN_CONTEXT_FRAME",
        } and contig_local_specificity >= 0.45:
            status = "ACCEPT_CONTIG_LOCAL_ROLE_CONSTRAINT_NO_GLOSS"
        elif tag == "R20_R02_PHASE_FRAME":
            status = "BROAD_PHASE_MARKER_AUDIT_ONLY"
        else:
            status = "FAILED_NEGATIVE_CONTROL_OR_TOO_BROAD"

        items.append(
            {
                "tag_id": tag,
                "status": status,
                "tag_book_count": len(books),
                "cluster_specificity": round(cluster_specificity, 4),
                "contig_local_specificity": round(contig_local_specificity, 4),
                "evidence": {
                    "books": sorted(books, key=lambda x: int(x)),
                    "same_cluster_universe": sorted(same_cluster_universe, key=lambda x: int(x))[:80],
                    "contig_neighborhood": sorted(neighborhood, key=lambda x: int(x)),
                    "contig_hits": contig_hits,
                },
            }
        )

    accepted = sum(1 for i in items if i["status"].startswith("ACCEPT"))
    failed = len(items) - accepted
    decision = "STRUCTURAL_ROLE_CONSTRAINTS_ACCEPTED_NO_GLOSS" if accepted else "NO_STRUCTURAL_ROLE_CONSTRAINT_ACCEPTED"
    cur = conn.execute(
        """
        INSERT INTO structural_role_negative_control_runs
        (created_at, decision, accepted_constraint_count, broad_or_failed_count, payload_json)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            now(),
            decision,
            accepted,
            failed,
            json.dumps({"source": "functional-role subagent result + SQL negative controls"}, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)
    for item in items:
        conn.execute(
            """
            INSERT INTO structural_role_negative_control_items
            (run_id, tag_id, status, tag_book_count, cluster_specificity, contig_local_specificity, evidence_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                item["tag_id"],
                item["status"],
                item["tag_book_count"],
                item["cluster_specificity"],
                item["contig_local_specificity"],
                json.dumps(item["evidence"], sort_keys=True),
            ),
        )
    conn.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "accepted_constraint_count": accepted,
                "broad_or_failed_count": failed,
                "items": items,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
