#!/usr/bin/env python3
"""Validate Hellgate external numeric refs against row0 code streams."""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "bonelord_operational.sqlite"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def jdump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS hellgate_external_roundtrip_probe_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_code_symbol_run_id INTEGER NOT NULL,
            source_export_id INTEGER NOT NULL,
            ref_count INTEGER NOT NULL,
            exact_roundtrip_count INTEGER NOT NULL,
            strong_anchor_count INTEGER NOT NULL,
            weak_anchor_count INTEGER NOT NULL,
            mismatch_count INTEGER NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS hellgate_external_roundtrip_items (
            run_id INTEGER NOT NULL,
            refname TEXT NOT NULL,
            bookid TEXT NOT NULL,
            digitslen INTEGER NOT NULL,
            row0_digitslen INTEGER,
            exact_digits_match INTEGER NOT NULL,
            exact_decodedbase_match INTEGER NOT NULL,
            row0_valid INTEGER NOT NULL,
            insertedzeros INTEGER,
            omitted_count INTEGER,
            endpoint_start_token TEXT,
            endpoint_end_token TEXT,
            anchor_strength TEXT NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, refname, bookid)
        );
        """
    )


def one(conn: sqlite3.Connection, sql: str) -> sqlite3.Row:
    row = conn.execute(sql).fetchone()
    if row is None:
        raise SystemExit(f"missing required row: {sql}")
    return row


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)

    code_run_id = int(one(conn, "SELECT MAX(run_id) AS run_id FROM row0_code_symbol_probe_runs")["run_id"])
    export_id = int(one(conn, "SELECT MAX(__export_id) AS export_id FROM sheet__externalrefs_v115")["export_id"])
    refs = conn.execute(
        """
        SELECT refname, digitssanitized, digitslen, inbooks_bookids, decodedbase
        FROM sheet__externalrefs_v115
        WHERE __export_id=?
          AND lower(refname) LIKE 'hellgatebook_%'
        ORDER BY refname, inbooks_bookids
        """,
        (export_id,),
    ).fetchall()

    cur = conn.execute(
        """
        INSERT INTO hellgate_external_roundtrip_probe_runs
            (created_at, source_code_symbol_run_id, source_export_id, ref_count,
             exact_roundtrip_count, strong_anchor_count, weak_anchor_count,
             mismatch_count, decision, payload_json)
        VALUES (?, ?, ?, ?, 0, 0, 0, 0, ?, ?)
        """,
        (utc_now(), code_run_id, export_id, len(refs), "PENDING", "{}"),
    )
    run_id = int(cur.lastrowid)

    exact_count = 0
    strong_count = 0
    weak_count = 0
    mismatch_count = 0
    summaries: list[dict[str, Any]] = []

    for ref in refs:
        bookid = str(ref["inbooks_bookids"] or "").strip()
        row0 = conn.execute(
            """
            SELECT *
            FROM row0_code_symbol_probe_books
            WHERE run_id=? AND bookid=?
            """,
            (code_run_id, bookid),
        ).fetchone()
        if row0 is None:
            exact_digits = 0
            exact_base = 0
            valid = 0
            insertedzeros = None
            omitted_count = None
            row0_digitslen = None
            start_token = None
            end_token = None
        else:
            reconstructed = (row0["reconstructed_code_stream"] or "").replace(" ", "")
            exact_digits = int(reconstructed == (ref["digitssanitized"] or ""))
            exact_base = int((row0["decodedbase"] or "") == (ref["decodedbase"] or ""))
            valid = int(row0["valid"])
            insertedzeros = int(row0["insertedzeros"])
            omitted_count = len(json.loads(row0["omitted_codes_json"] or "[]"))
            row0_digitslen = int(row0["digitslen"])
            decoded = row0["decodedbase"] or ""
            start_token = decoded[:1]
            end_token = decoded[-1:] if decoded else None
        if exact_digits and exact_base and valid:
            exact_count += 1
        else:
            mismatch_count += 1
        if exact_digits and exact_base and valid and insertedzeros == 0 and omitted_count == 0 and int(ref["digitslen"] or 0) >= 100:
            strength = "STRONG_EXTERNAL_MECHANICAL_ANCHOR"
            strong_count += 1
        elif exact_digits and exact_base and valid:
            strength = "WEAK_EXTERNAL_MECHANICAL_ANCHOR"
            weak_count += 1
        else:
            strength = "MISMATCH_OR_INCOMPLETE"
        item_decision = "MECHANICAL_CONTOUR_VALIDATED_NO_GLOSS" if strength != "MISMATCH_OR_INCOMPLETE" else "EXTERNAL_ROUNDTRIP_MISMATCH"
        summary = {
            "refname": ref["refname"],
            "bookid": bookid,
            "digitslen": int(ref["digitslen"] or 0),
            "anchor_strength": strength,
            "exact_digits_match": bool(exact_digits),
            "exact_decodedbase_match": bool(exact_base),
        }
        summaries.append(summary)
        conn.execute(
            """
            INSERT INTO hellgate_external_roundtrip_items
                (run_id, refname, bookid, digitslen, row0_digitslen,
                 exact_digits_match, exact_decodedbase_match, row0_valid,
                 insertedzeros, omitted_count, endpoint_start_token,
                 endpoint_end_token, anchor_strength, decision, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                ref["refname"],
                bookid,
                int(ref["digitslen"] or 0),
                row0_digitslen,
                exact_digits,
                exact_base,
                valid,
                insertedzeros,
                omitted_count,
                start_token,
                end_token,
                strength,
                item_decision,
                jdump(summary),
            ),
        )

    decision = "HELLGATE_EXTERNAL_CONTOURS_VALIDATED" if mismatch_count == 0 and exact_count > 0 else "HELLGATE_EXTERNAL_CONTOUR_MISMATCHES"
    conn.execute(
        """
        UPDATE hellgate_external_roundtrip_probe_runs
        SET exact_roundtrip_count=?,
            strong_anchor_count=?,
            weak_anchor_count=?,
            mismatch_count=?,
            decision=?,
            payload_json=?
        WHERE run_id=?
        """,
        (exact_count, strong_count, weak_count, mismatch_count, decision, jdump({"summaries": summaries, "gloss_allowed": False}), run_id),
    )
    conn.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "ref_count": len(refs),
                "exact_roundtrip_count": exact_count,
                "strong_anchor_count": strong_count,
                "weak_anchor_count": weak_count,
                "mismatch_count": mismatch_count,
                "summaries": summaries,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
