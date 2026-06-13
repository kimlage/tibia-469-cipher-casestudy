#!/usr/bin/env python3
"""Choose row0 alternate paths by operator/selector preservation for high-risk residuals."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
TARGETS = ("6", "7", "49")
OPERATORS = ("C68", "C86", "O23", "O32", "R20", "R02", "BENNA", "NAESE", "VINVIN", "FNAAST", "LTAST", "VNCTIIN")


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def score_text(text: str) -> int:
    score = sum(20 for op in OPERATORS if op in text)
    if "BENNA" in text and "LTAST" in text:
        score += 15
    if "O32" in text:
        score += 10
    if "3478" in text:
        score += 5
    # Penalize pseudo-English decoded alternate strings with unknowns if present.
    score -= text.count("?") * 5
    return score


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.executescript("""
    create table if not exists row0_phase_operator_path_gate_v1_runs (
        run_id integer primary key autoincrement,
        created_at text not null,
        decision text not null,
        target_count integer not null,
        path_resolved_count integer not null,
        promoted_count integer not null,
        accepted_prose_gloss_count integer not null,
        summary_json text not null
    );
    create table if not exists row0_phase_operator_path_gate_v1_items (
        run_id integer not null,
        bookid text not null,
        gate_status text not null,
        proposed_label text not null,
        path_resolved integer not null,
        promotion_allowed integer not null,
        prose_gloss_allowed integer not null,
        selected_path_rank integer not null,
        margin integer not null,
        reason text not null,
        next_action text not null,
        evidence_json text not null,
        primary key (run_id, bookid)
    );
    """)
    items = []
    for bookid in TARGETS:
        base = conn.execute("select * from row0_variant_book_tokens where bookid=?", (bookid,)).fetchone()
        paths = list(conn.execute("select * from row0_path_reconstruction_items where bookid=? order by run_id desc, path_rank", (bookid,)))
        om = conn.execute("select * from row0_omission_probe_book_items where bookid=? order by run_id desc limit 1", (bookid,)).fetchone()
        candidates = []
        if base:
            candidates.append((0, score_text(base["symbol_text"]), base["symbol_text"], "CURRENT_ROW0"))
        for p in paths:
            # These decoded_text values are alternate alphabet decodes, not row0 symbols; use only as phase-risk evidence.
            candidates.append((int(p["path_rank"]), score_text(p["decoded_text"]), p["decoded_text"], p["decision"]))
        candidates.sort(key=lambda x: x[1], reverse=True)
        best = candidates[0] if candidates else (-1, 0, "", "NONE")
        second = candidates[1] if len(candidates) > 1 else (-1, -999, "", "NONE")
        margin = best[1] - second[1]
        if bookid == "49":
            status = "PROMOTE_O32_REPEAT_MODE_CONTROL_NO_GLOSS" if "O32" in (base["symbol_text"] if base else "") else "HOLD_O32_PHASE_UNRESOLVED"
            label = "O32_REPEAT_MODE_CONTROL"
            promote = 1 if status.startswith("PROMOTE") else 0
            resolved = 1
            reason = "O32 is singleton inside repetitive formula; classify as mode/control marker, not O23 or lexical atom."
            next_action = "Keep O32 as audit/control selector; no human gloss."
        elif margin >= 15 and best[3] == "CURRENT_ROW0":
            status = "CURRENT_ROW0_OPERATOR_PATH_STABLE_NO_GLOSS"
            label = "ROW0_PHASE_STABLE_CONTROL"
            promote = 0
            resolved = 1
            reason = "Operator-preserving score favors current row0; but no independent structural label emerges."
            next_action = "Hold semantically; use as phase-stable control."
        else:
            status = "ROW0_PHASE_REMAINS_AMBIGUOUS"
            label = "ROW0_PHASE_AUDIT"
            promote = 0
            resolved = 0
            reason = "Operator/selector scoring does not resolve phase strongly enough for promotion."
            next_action = "Do not promote; require stronger path evidence or external/contig support."
        evidence = {"current": dict(base) if base else None, "omission_probe": dict(om) if om else None, "candidates": candidates}
        items.append((bookid, status, label, resolved, promote, 0, best[0], margin, reason, next_action, json.dumps(evidence, ensure_ascii=False, sort_keys=True)))
    promoted = sum(i[4] for i in items)
    resolved = sum(i[3] for i in items)
    cur = conn.execute("insert into row0_phase_operator_path_gate_v1_runs (created_at,decision,target_count,path_resolved_count,promoted_count,accepted_prose_gloss_count,summary_json) values (?,?,?,?,?,?,?)", (utc_now(), "ROW0_PHASE_OPERATOR_PATH_GATED_NO_GLOSS", len(TARGETS), resolved, promoted, 0, json.dumps({"targets": list(TARGETS), "principle": "path/operator classification only"}, ensure_ascii=False, sort_keys=True)))
    run_id = cur.lastrowid
    for item in items:
        conn.execute("insert into row0_phase_operator_path_gate_v1_items values (?,?,?,?,?,?,?,?,?,?,?,?)", (run_id, *item))
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": "ROW0_PHASE_OPERATOR_PATH_GATED_NO_GLOSS", "path_resolved_count": resolved, "promoted_count": promoted, "items": [{"bookid": i[0], "status": i[1], "promote": i[4], "margin": i[7]} for i in items]}, ensure_ascii=False))

if __name__ == "__main__":
    main()
