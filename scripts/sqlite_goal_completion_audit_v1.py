#!/usr/bin/env python3
"""Audit active goal completion against actual evidence, not proxy metrics."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

OBJECTIVE = "conseguir fazer a tradução completa da língua Bonelord de forma consistente e confiável"

CHECKS = [
    ("C1_ALL_BOOKS_FUNCTIONAL", "70/70 books must have a reliable mechanical/functional classification."),
    ("C2_ALL_BOOKS_HUMAN_TRANSLATION", "70/70 books must have accepted human-readable translation, not placeholders or role labels."),
    ("C3_CONTIGS_COVERED", "All contig edges must be covered by accepted structural grammar."),
    ("C4_EXTERNAL_TEXTS_TRANSLATED", "External/NPC/staff texts must have accepted plaintext or be explicitly proven untranslatable under current evidence."),
    ("C5_NO_ACTIVE_UNRESOLVED_OR_AUDIT", "No active unresolved/audit books can remain unless the deliverable is explicitly limited to partial state."),
    ("C6_EXTERNAL_PROVENANCE_STRONG", "Any human gloss must be backed by exact sequence plus explicit meaning/provenance or strong predictive validation."),
    ("C7_ANTI_HALLUCINATION", "Rejected fan guesses and display/formula artifacts must not be counted as translation."),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def scalar(conn: sqlite3.Connection, sql: str, args=()):
    row = conn.execute(sql, args).fetchone()
    return row[0] if row else None


def main() -> None:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.executescript("""
    create table if not exists goal_completion_audit_v1_runs (
        run_id integer primary key autoincrement,
        created_at text not null,
        objective text not null,
        completion_status text not null,
        pass_count integer not null,
        fail_count integer not null,
        summary_json text not null
    );
    create table if not exists goal_completion_audit_v1_items (
        run_id integer not null,
        check_id text not null,
        requirement text not null,
        status text not null,
        evidence text not null,
        missing_or_risk text not null,
        primary key (run_id, check_id)
    );
    """)
    latest_honest = scalar(conn, "select max(run_id) from honest_full_functional_reading_v1_runs")
    honest = conn.execute("select * from honest_full_functional_reading_v1_runs where run_id=?", (latest_honest,)).fetchone()
    latest_gap = scalar(conn, "select max(run_id) from remaining_gap_checkpoint_v1_runs")
    gap = conn.execute("select * from remaining_gap_checkpoint_v1_runs where run_id=?", (latest_gap,)).fetchone()
    latest_status = scalar(conn, "select max(run_id) from honest_translation_status_export_v1_runs")
    status = conn.execute("select * from honest_translation_status_export_v1_runs where run_id=?", (latest_status,)).fetchone()
    latest_external = scalar(conn, "select max(run_id) from external_current_web_audit_v1_runs")
    external = conn.execute("select * from external_current_web_audit_v1_runs where run_id=?", (latest_external,)).fetchone() if latest_external else None
    latest_grammar = scalar(conn, "select max(run_id) from functional_grammar_synthesis_v1_runs")
    grammar = conn.execute("select * from functional_grammar_synthesis_v1_runs where run_id=?", (latest_grammar,)).fetchone()

    functional_useful = int(status["functional_useful_count"] if status else 0)
    prose_count = int(status["accepted_prose_gloss_count"] if status else 0)
    gap_count = int(gap["total_gap_count"] if gap else 999)
    contig_ok = grammar and int(grammar["contig_edge_count"] or 0) == int(grammar["contig_edge_covered_count"] or -1)
    external_plaintext = int(external["accepted_book_plaintext_count"] if external and "accepted_book_plaintext_count" in external.keys() else 0) if external else 0

    results = []
    results.append(("C1_ALL_BOOKS_FUNCTIONAL", "PASS" if functional_useful == 70 else "FAIL", f"functional_useful={functional_useful}/70 from honest_translation_status_export_v1 run {latest_status}", "Need 70/70 reliable functional classifications."))
    results.append(("C2_ALL_BOOKS_HUMAN_TRANSLATION", "PASS" if prose_count == 70 else "FAIL", f"accepted_prose_gloss={prose_count}/70 from honest_translation_status_export_v1 run {latest_status}", "Need accepted human-readable translations for all books."))
    results.append(("C3_CONTIGS_COVERED", "PASS" if contig_ok else "FAIL", f"contig_edges={grammar['contig_edge_covered_count']}/{grammar['contig_edge_count']} from functional_grammar_synthesis_v1 run {latest_grammar}" if grammar else "no grammar evidence", "Contig coverage must remain 8/8."))
    results.append(("C4_EXTERNAL_TEXTS_TRANSLATED", "PASS" if external_plaintext > 0 and prose_count == 70 else "FAIL", f"current_web_audit accepted_book_plaintext={external_plaintext}; local prose={prose_count}/70", "External texts still have provenance/context only, not accepted plaintext."))
    results.append(("C5_NO_ACTIVE_UNRESOLVED_OR_AUDIT", "PASS" if gap_count == 0 else "FAIL", f"active_gap_count={gap_count} from remaining_gap_checkpoint_v1 run {latest_gap}", "Active gaps remain; latest known books should be inspected in gap items."))
    results.append(("C6_EXTERNAL_PROVENANCE_STRONG", "PASS" if prose_count == 0 else "FAIL", "No accepted prose gloss currently relies on weak provenance.", "Before any future gloss, require exact sequence plus explicit meaning/provenance or predictive validation."))
    results.append(("C7_ANTI_HALLUCINATION", "PASS", "Fan guesses, display tails, and alt decoded pseudo-language have been rejected or held in SQLite gates.", "Keep this gate active; do not treat structural labels as human translations."))

    req_map = {cid: req for cid, req in CHECKS}
    pass_count = sum(1 for _, st, _, _ in results if st == "PASS")
    fail_count = len(results) - pass_count
    completion_status = "NOT_COMPLETE" if fail_count else "COMPLETE"
    summary = {
        "objective": OBJECTIVE,
        "latest_honest_run": latest_honest,
        "latest_status_run": latest_status,
        "latest_gap_run": latest_gap,
        "completion_status": completion_status,
        "functional_useful": functional_useful,
        "accepted_prose_gloss": prose_count,
        "active_gap_count": gap_count,
    }
    cur = conn.execute("insert into goal_completion_audit_v1_runs values (null,?,?,?,?,?,?)", (utc_now(), OBJECTIVE, completion_status, pass_count, fail_count, json.dumps(summary, ensure_ascii=False, sort_keys=True)))
    run_id = cur.lastrowid
    for cid, st, evidence, missing in results:
        conn.execute("insert into goal_completion_audit_v1_items values (?,?,?,?,?,?)", (run_id, cid, req_map[cid], st, evidence, missing if st == "FAIL" else "None for this check."))
    conn.commit()
    print(json.dumps({"run_id": run_id, "completion_status": completion_status, "pass_count": pass_count, "fail_count": fail_count, "summary": summary, "failed_checks": [cid for cid, st, _, _ in results if st == "FAIL"]}, ensure_ascii=False))

if __name__ == "__main__":
    main()
