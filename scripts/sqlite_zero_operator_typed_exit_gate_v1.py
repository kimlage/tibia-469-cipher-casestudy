#!/usr/bin/env python3
"""Classify *00 exits as typed operator transitions and test current residuals."""
from __future__ import annotations

import json
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
TARGETS = ("6", "7", "14", "32", "34", "36", "41", "49")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def classify_exit(tokens, i):
    right = tokens[i + 1:i + 8]
    left = tokens[max(0, i - 5):i]
    if right[:2] == ["V", "N"] and len(right) > 2 and right[2] == "C68":
        return "ZERO_EXIT_VN_C68_CONTEXT"
    if right[:2] == ["I", "C86"]:
        return "ZERO_EXIT_I_C86_OPERATOR"
    if right[:3] == ["V", "T", "L"] or "R20" in right[:5]:
        return "ZERO_EXIT_VTL_R20_BRANCH"
    if right[:2] == ["I", "F"] or (right and right[0] == "O23") or "O23" in right[:4]:
        return "ZERO_EXIT_IFAI_O23_SCOPE"
    if right[:3] == ["V", "A", "E"] or "FNAAST" in right[:6]:
        return "ZERO_EXIT_VAE_FNAAST_DISPLAY"
    if right[:4] == ["N", "A", "E", "S"] or "NAESE" in right[:4]:
        return "ZERO_EXIT_NAESE_SLOT"
    if right[:2] == ["A", "N"]:
        return "ZERO_EXIT_ANIV_CONTINUATION"
    if "LTAST" in left or "LTAST" in right:
        return "ZERO_EXIT_LTAST_ADJACENT"
    return "ZERO_EXIT_OTHER"


def main() -> None:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.executescript("""
    create table if not exists zero_operator_typed_exit_gate_v1_runs (
        run_id integer primary key autoincrement,
        created_at text not null,
        decision text not null,
        total_zero_count integer not null,
        residual_zero_count integer not null,
        promoted_count integer not null,
        held_count integer not null,
        accepted_prose_gloss_count integer not null,
        summary_json text not null
    );
    create table if not exists zero_operator_typed_exit_gate_v1_occurrences (
        run_id integer not null,
        bookid text not null,
        zero_index integer not null,
        token_pos integer not null,
        exit_type text not null,
        left_context text not null,
        right_context text not null,
        is_residual integer not null,
        evidence_json text not null,
        primary key (run_id, bookid, zero_index)
    );
    create table if not exists zero_operator_typed_exit_gate_v1_book_decisions (
        run_id integer not null,
        bookid text not null,
        gate_status text not null,
        proposed_label text not null,
        promotion_allowed integer not null,
        prose_gloss_allowed integer not null,
        exit_types text not null,
        reason text not null,
        next_action text not null,
        evidence_json text not null,
        primary key (run_id, bookid)
    );
    """)
    latest_read = conn.execute("select max(run_id) as run_id from honest_full_functional_reading_v1_books").fetchone()["run_id"]
    readings = {r["bookid"]: dict(r) for r in conn.execute("select * from honest_full_functional_reading_v1_books where run_id=?", (latest_read,))}
    rows = list(conn.execute("select bookid, tokens_json, symbol_text from row0_variant_book_tokens order by bookid+0"))
    occs = []
    by_book = defaultdict(list)
    accepted_exit_counts = Counter()
    for row in rows:
        bookid = row["bookid"]
        tokens = json.loads(row["tokens_json"])
        for i, tok in enumerate(tokens):
            if tok != "*00":
                continue
            et = classify_exit(tokens, i)
            occ = {
                "bookid": bookid,
                "idx": len(by_book[bookid]) + 1,
                "pos": i,
                "exit_type": et,
                "left": " ".join(tokens[max(0, i - 6):i]),
                "right": " ".join(tokens[i + 1:i + 8]),
                "is_residual": int(bookid in TARGETS),
                "reading": readings.get(bookid),
            }
            by_book[bookid].append(occ)
            occs.append(occ)
            if readings.get(bookid, {}).get("status") in ("FUNCTIONAL_CORE", "FUNCTIONAL_RELATED"):
                accepted_exit_counts[et] += 1

    decisions = []
    for bookid in TARGETS:
        exits = by_book.get(bookid, [])
        exit_types = [o["exit_type"] for o in exits]
        type_counts = Counter(exit_types)
        if not exits:
            status = "NO_ZERO_OPERATOR_IN_CURRENT_ROW0"
            label = "NO_ZERO_EXIT_CLASS"
            promote = 0
            reason = "No *00 operator in current row0 path; this gate cannot classify the book."
            next_action = "Use other evidence only."
        elif bookid == "14" and "ZERO_EXIT_LTAST_ADJACENT" in exit_types:
            status = "PROMOTE_ZERO_LTAST_SLOT_BOUNDARY_NO_GLOSS"
            label = "ZERO_LTAST_SLOT_BOUNDARY_FRAGMENT"
            promote = 1
            reason = "Zero exits are LTAST-adjacent and match accepted formula/continuation mechanics; structural boundary only."
            next_action = "Promote as related structural boundary; no gloss and no full LTAST semantic claim."
        elif bookid == "34" and ("ZERO_EXIT_ANIV_CONTINUATION" in exit_types or "ZERO_EXIT_I_C86_OPERATOR" in exit_types):
            status = "PROMOTE_ZERO_ANIV_BRANCH_TAIL_BOUNDARY_NO_GLOSS"
            label = "ZERO_ANIV_BRANCH_TAIL_BOUNDARY"
            promote = 1
            reason = "Zero exits split ANIV/branch-tail material into typed continuation boundaries; structural only."
            next_action = "Promote as branch-tail boundary; no operator-family promotion."
        elif bookid == "41" and any(et in exit_types for et in ("ZERO_EXIT_IFAI_O23_SCOPE", "ZERO_EXIT_OTHER")):
            status = "HOLD_ZERO_CONTEXT_FRAGMENT_WEAK"
            label = "ZERO_CONTEXT_FRAGMENT_AUDIT"
            promote = 0
            reason = "Zero exits do not cleanly separate from O23/context fragment ambiguity."
            next_action = "Keep audit-only until stronger selector evidence appears."
        elif all(et == "ZERO_EXIT_VAE_FNAAST_DISPLAY" for et in exit_types) or bookid in ("32", "36"):
            status = "HOLD_ZERO_DISPLAY_EXIT_NO_GLOSS"
            label = "ZERO_DISPLAY_EXIT_CONTROL"
            promote = 0
            reason = "Zero exit is display/FNAAST-like and already known as display/control, not payload."
            next_action = "Use as display negative/control only."
        else:
            status = "HOLD_ZERO_EXIT_NOT_PROMOTABLE"
            label = "ZERO_EXIT_AUDIT"
            promote = 0
            reason = "Zero exit typing does not give a safe structural promotion."
            next_action = "Hold."
        evidence = {"occurrences": exits, "exit_type_counts": dict(type_counts), "accepted_exit_counts": dict(accepted_exit_counts)}
        decisions.append((bookid, status, label, promote, 0, ",".join(sorted(type_counts)) or "NONE", reason, next_action, json.dumps(evidence, ensure_ascii=False, sort_keys=True)))

    promoted = sum(d[3] for d in decisions)
    summary = {"accepted_exit_counts": dict(accepted_exit_counts), "target_books": list(TARGETS), "promoted_books": [d[0] for d in decisions if d[3]], "principle": "*00 exit type is structural only"}
    cur = conn.execute("insert into zero_operator_typed_exit_gate_v1_runs (created_at,decision,total_zero_count,residual_zero_count,promoted_count,held_count,accepted_prose_gloss_count,summary_json) values (?,?,?,?,?,?,?,?)", (utc_now(), "ZERO_OPERATOR_TYPED_EXIT_STRUCTURAL_GATE_NO_GLOSS", len(occs), sum(o["is_residual"] for o in occs), promoted, len(decisions)-promoted, 0, json.dumps(summary, ensure_ascii=False, sort_keys=True)))
    run_id = cur.lastrowid
    for o in occs:
        conn.execute("insert into zero_operator_typed_exit_gate_v1_occurrences values (?,?,?,?,?,?,?,?,?)", (run_id, o["bookid"], o["idx"], o["pos"], o["exit_type"], o["left"], o["right"], o["is_residual"], json.dumps(o, ensure_ascii=False, sort_keys=True)))
    for d in decisions:
        conn.execute("insert into zero_operator_typed_exit_gate_v1_book_decisions values (?,?,?,?,?,?,?,?,?,?)", (run_id, *d))
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": "ZERO_OPERATOR_TYPED_EXIT_STRUCTURAL_GATE_NO_GLOSS", "promoted_count": promoted, "promoted_books": [d[0] for d in decisions if d[3]], "held_books": [d[0] for d in decisions if not d[3]], "accepted_prose_gloss_count": 0}, ensure_ascii=False))

if __name__ == "__main__":
    main()
