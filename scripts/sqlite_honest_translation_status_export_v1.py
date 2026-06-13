#!/usr/bin/env python3
"""Create an honest current translation-status layer: functional reading != human prose."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main() -> None:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.executescript("""
    create table if not exists honest_translation_status_export_v1_runs (
        run_id integer primary key autoincrement,
        created_at text not null,
        decision text not null,
        total_books integer not null,
        functional_useful_count integer not null,
        unresolved_or_audit_count integer not null,
        accepted_prose_gloss_count integer not null,
        functional_percent real not null,
        prose_percent real not null,
        summary_json text not null
    );
    create table if not exists honest_translation_status_export_v1_books (
        run_id integer not null,
        bookid text not null,
        status text not null,
        functional_reading text not null,
        human_translation text not null,
        confidence_tier text not null,
        use_in_semantic_translation integer not null,
        blocker text not null,
        source_component text not null,
        evidence_json text not null,
        primary key (run_id, bookid)
    );
    """)
    latest = conn.execute("select max(run_id) as run_id from honest_full_functional_reading_v1_books").fetchone()["run_id"]
    rows = list(conn.execute("select * from honest_full_functional_reading_v1_books where run_id=? order by bookid+0", (latest,)))
    latest_gap = conn.execute("select max(run_id) as run_id from remaining_gap_checkpoint_v1_runs").fetchone()["run_id"]
    gaps = {r["bookid"]: dict(r) for r in conn.execute("select * from remaining_gap_checkpoint_v1_items where run_id=?", (latest_gap,))}
    useful = sum(1 for r in rows if r["status"] in ("FUNCTIONAL_CORE", "FUNCTIONAL_RELATED"))
    
    null_glosses = {"<NO_PROSE_GLOSS>", "<NO_HUMAN_TRANSLATION_ACCEPTED>", "<empty>", "", "<UNRESOLVED>", "<missing>"}
    prose = sum(1 for r in rows if (r["prose_gloss"] or "").strip() not in null_glosses and not (r["prose_gloss"] or "").strip().startswith("<"))
    summary = {
        "latest_honest_run": latest,
        "latest_gap_run": latest_gap,
        "principle": "functional_reading is a mechanical/structural label, not a human translation",
        "remaining_gap_books": sorted(gaps, key=int) if gaps else [],
    }
    cur = conn.execute(
        "insert into honest_translation_status_export_v1_runs (created_at,decision,total_books,functional_useful_count,unresolved_or_audit_count,accepted_prose_gloss_count,functional_percent,prose_percent,summary_json) values (?,?,?,?,?,?,?,?,?)",
        (utc_now(), "HONEST_TRANSLATION_STATUS_EXPORTED_NO_FINAL_GLOSS", len(rows), useful, len(rows)-useful, prose, round(useful / len(rows) * 100, 3), round(prose / len(rows) * 100, 3), json.dumps(summary, ensure_ascii=False, sort_keys=True)),
    )
    run_id = cur.lastrowid
    for r in rows:
        gap = gaps.get(r["bookid"])
        if r["status"] == "FUNCTIONAL_CORE":
            tier = "MECHANICAL_CORE_NO_PROSE"
            use = 0
            blocker = "No accepted human prose gloss; use only as structural anchor."
        elif r["status"] == "FUNCTIONAL_RELATED":
            tier = "MECHANICAL_RELATED_NO_PROSE"
            use = 0
            blocker = "Related structural role only; not a semantic sentence."
        elif r["status"] == "QUARANTINED_OR_AUDIT":
            tier = "AUDIT_OR_CONTROL_NO_PROSE"
            use = 0
            blocker = gap["reason"] if gap else "Audit/control item; no semantic promotion."
        else:
            tier = "UNRESOLVED_NO_PROSE"
            use = 0
            blocker = gap["reason"] if gap else "No reliable function or prose gloss."
        evidence = {"honest_book": dict(r), "current_gap": gap}
        conn.execute(
            "insert into honest_translation_status_export_v1_books values (?,?,?,?,?,?,?,?,?,?)",
            (run_id, r["bookid"], r["status"], r["functional_reading"], "<NO_HUMAN_TRANSLATION_ACCEPTED>", tier, use, blocker, r["source_component"], json.dumps(evidence, ensure_ascii=False, sort_keys=True)),
        )
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": "HONEST_TRANSLATION_STATUS_EXPORTED_NO_FINAL_GLOSS", "total_books": len(rows), "functional_useful_count": useful, "functional_percent": round(useful / len(rows) * 100, 3), "accepted_prose_gloss_count": prose, "prose_percent": round(prose / len(rows) * 100, 3), "remaining_gap_books": sorted(gaps, key=int) if gaps else []}, ensure_ascii=False))

if __name__ == "__main__":
    main()
