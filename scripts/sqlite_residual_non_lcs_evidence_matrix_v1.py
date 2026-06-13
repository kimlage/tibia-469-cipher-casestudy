#!/usr/bin/env python3
"""Build non-LCS evidence matrix for current residual books."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def table_exists(conn, name: str) -> bool:
    return conn.execute("select 1 from sqlite_master where type='table' and name=?", (name,)).fetchone() is not None


def main() -> None:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        create table if not exists residual_non_lcs_evidence_matrix_v1_runs (
            run_id integer primary key autoincrement,
            created_at text not null,
            decision text not null,
            residual_count integer not null,
            non_lcs_open_count integer not null,
            blocked_count integer not null,
            summary_json text not null
        );
        create table if not exists residual_non_lcs_evidence_matrix_v1_items (
            run_id integer not null,
            bookid text not null,
            current_status text not null,
            current_reading text not null,
            next_method text not null,
            has_3478 integer not null,
            has_contig_support integer not null,
            has_external_exact_book_hit integer not null,
            non_lcs_status text not null,
            recommendation text not null,
            evidence_json text not null,
            primary key (run_id, bookid)
        );
        """
    )
    latest_gap = conn.execute("select max(run_id) as run_id from remaining_gap_checkpoint_v1_items").fetchone()["run_id"]
    gaps = list(conn.execute("select * from remaining_gap_checkpoint_v1_items where run_id=? order by bookid+0", (latest_gap,)))

    items = []
    for g in gaps:
        bookid = g["bookid"]
        a3478 = conn.execute("select * from anchor3478_context_items where bookid=? order by run_id desc limit 1", (bookid,)).fetchone() if table_exists(conn, "anchor3478_context_items") else None
        contig = conn.execute("select * from final_residual_contig_support_probe_items where bookid=? order by run_id desc limit 1", (bookid,)).fetchone() if table_exists(conn, "final_residual_contig_support_probe_items") else None
        external_hit = 0
        external_rows = []
        if table_exists(conn, "confirmed_external_row0_projection_items"):
            for r in conn.execute("select phrase_id, exact_book_hits_json, projection_status from confirmed_external_row0_projection_items order by run_id desc"):
                hits = json.loads(r["exact_book_hits_json"] or "[]")
                if str(bookid) in {str(x) for x in hits}:
                    external_hit = 1
                    external_rows.append(dict(r))
        has_contig = int(bool(contig and int(contig["in_contig_path"] or 0)))
        has_3478 = int(bool(a3478))
        if external_hit:
            status = "OPEN_EXTERNAL_EXACT_BOOK_HIT"
            rec = "inspect external phrase provenance against exact book hit before any promotion"
        elif has_contig:
            status = "OPEN_CONTIG_SUPPORTED"
            rec = "use contig edge/path evidence as next non-circular lane"
        elif has_3478:
            status = "HOLD_3478_MIXED_WINDOW_NO_GLOSS"
            rec = "3478 window exists but is mixed/context-only; use as boundary control, not gloss"
        else:
            status = "BLOCKED_NO_NON_LCS_EVIDENCE"
            rec = "do not reopen until external exact, contig edge, or new parse split appears"
        evidence = {
            "gap": dict(g),
            "anchor3478": dict(a3478) if a3478 else None,
            "contig_support": dict(contig) if contig else None,
            "external_hits": external_rows,
        }
        items.append({
            "bookid": bookid,
            "current_status": g["current_status"],
            "current_reading": g["current_reading"],
            "next_method": g["next_method"],
            "has_3478": has_3478,
            "has_contig_support": has_contig,
            "has_external_exact_book_hit": external_hit,
            "non_lcs_status": status,
            "recommendation": rec,
            "evidence_json": json.dumps(evidence, ensure_ascii=False, sort_keys=True),
        })
    open_count = sum(1 for i in items if i["non_lcs_status"].startswith("OPEN"))
    summary = {
        "latest_gap_run": latest_gap,
        "status_counts": {},
    }
    for item in items:
        summary["status_counts"][item["non_lcs_status"]] = summary["status_counts"].get(item["non_lcs_status"], 0) + 1
    cur = conn.execute(
        """
        insert into residual_non_lcs_evidence_matrix_v1_runs
        (created_at, decision, residual_count, non_lcs_open_count, blocked_count, summary_json)
        values (?, ?, ?, ?, ?, ?)
        """,
        (utc_now(), "RESIDUAL_NON_LCS_EVIDENCE_MATRIX_BUILT", len(items), open_count, len(items)-open_count, json.dumps(summary, ensure_ascii=False, sort_keys=True)),
    )
    run_id = cur.lastrowid
    for item in items:
        conn.execute(
            """
            insert into residual_non_lcs_evidence_matrix_v1_items
            (run_id, bookid, current_status, current_reading, next_method, has_3478,
             has_contig_support, has_external_exact_book_hit, non_lcs_status, recommendation, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, item["bookid"], item["current_status"], item["current_reading"], item["next_method"], item["has_3478"], item["has_contig_support"], item["has_external_exact_book_hit"], item["non_lcs_status"], item["recommendation"], item["evidence_json"]),
        )
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": "RESIDUAL_NON_LCS_EVIDENCE_MATRIX_BUILT", "residual_count": len(items), "non_lcs_open_count": open_count, "blocked_count": len(items)-open_count, "summary": summary}, ensure_ascii=False))


if __name__ == "__main__":
    main()
