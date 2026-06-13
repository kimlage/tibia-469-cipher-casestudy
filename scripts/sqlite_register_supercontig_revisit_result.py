#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import sqlite3
from pathlib import Path
from typing import Any

DB_DEFAULT = "./data/bonelord_operational.sqlite"
TMP = Path("./tmp")


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def read_text(name: str) -> str:
    path = TMP / name
    return path.read_text(encoding="utf-8") if path.exists() else ""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=DB_DEFAULT)
    args = parser.parse_args()

    artifacts = {
        "precheck_md": str(TMP / "book_order_supercontig_revisit_precheck.md"),
        "probes_md": str(TMP / "book_order_supercontig_revisit_probes.md"),
        "endpoint_probe_md": str(TMP / "book_order_supercontig_revisit_endpoint_probe.md"),
        "precheck_sql": str(TMP / "book_order_supercontig_revisit_precheck.sql"),
        "probes_sql": str(TMP / "book_order_supercontig_revisit_probes.sql"),
        "endpoint_probe_sql": str(TMP / "book_order_supercontig_revisit_endpoint_probe.sql"),
    }
    evidence = {
        "artifacts": artifacts,
        "precheck_excerpt": read_text("book_order_supercontig_revisit_precheck.md")[:6000],
        "probes_excerpt": read_text("book_order_supercontig_revisit_probes.md")[:6000],
        "endpoint_excerpt": read_text("book_order_supercontig_revisit_endpoint_probe.md")[:6000],
        "key_metrics": {
            "target_books": ["4", "34", "49"],
            "numeric_neighbor_edges": {
                "3->4": 0,
                "4->5": 0,
                "33->34": 0,
                "34->35": 0,
                "48->49": 0,
                "49->50": 0,
            },
            "best_directional_overlaps": {
                "2->4": 3,
                "67->34": 2,
                "49->28": 5,
            },
            "validated_contig_membership_for_targets": 0,
            "validated_edge_touching_targets": 0,
        },
    }

    con = sqlite3.connect(args.db)
    cur = con.cursor()
    cur.executescript(
        """
        create table if not exists supercontig_revisit_resolution_runs(
            run_id integer primary key autoincrement,
            created_at text not null,
            status text not null,
            observed_outcome text not null,
            dead_or_alive text not null,
            next_action text not null,
            evidence_json text not null
        );
        """
    )
    status = "BOOK_ORDER_SUPERCONTIG_SIMPLE_ROUTE_DEAD"
    observed = "Numeric-order adjacency and endpoint insertion failed for books 4/34/49; no validated contig or edge touches the residuals."
    dead_or_alive = "DEAD_UNTIL_NEW_MECHANICAL_EVIDENCE"
    next_action = "Do not reopen simple book-order/supercontig route without new corpus row0, imported contig, or exact external sequence evidence."
    cur.execute(
        "insert into supercontig_revisit_resolution_runs(created_at,status,observed_outcome,dead_or_alive,next_action,evidence_json) values (?,?,?,?,?,?)",
        (now(), status, observed, dead_or_alive, next_action, j(evidence)),
    )
    run_id = cur.lastrowid
    con.commit()
    print(json.dumps({"run_id": run_id, "status": status, "dead_or_alive": dead_or_alive, "next_action": next_action}, ensure_ascii=False))


if __name__ == "__main__":
    main()
