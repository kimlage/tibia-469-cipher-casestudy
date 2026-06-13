#!/usr/bin/env python3
"""Test whether preserved code-symbol variants act as selectors versus collapsed base symbols."""
from __future__ import annotations

import json
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
TARGETS = ("6", "7", "14", "32", "36", "41", "49")
SELECTOR_PREFIXES = ("C", "O", "R")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def base(tok: str) -> str:
    if tok in ("C68", "C86"):
        return "C"
    if tok in ("O23", "O32"):
        return "O"
    if tok in ("R02", "R20"):
        return "R"
    return tok


def selector_tokens(tokens):
    return [t for t in tokens if t in ("C68", "C86", "O23", "O32", "R02", "R20")]


def contexts(tokens):
    out = []
    for i, t in enumerate(tokens):
        if t in ("C68", "C86", "O23", "O32", "R02", "R20"):
            left = "".join(tokens[max(0, i - 3):i])
            right = "".join(tokens[i + 1:i + 4])
            out.append((t, left, right, base(t)))
    return out


def main() -> None:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.executescript("""
    create table if not exists code_variant_selector_gate_v1_runs (
        run_id integer primary key autoincrement,
        created_at text not null,
        decision text not null,
        selector_occurrence_count integer not null,
        selector_variant_count integer not null,
        promoted_count integer not null,
        accepted_prose_gloss_count integer not null,
        summary_json text not null
    );
    create table if not exists code_variant_selector_gate_v1_items (
        run_id integer not null,
        bookid text not null,
        gate_status text not null,
        proposed_label text not null,
        promotion_allowed integer not null,
        prose_gloss_allowed integer not null,
        selectors text not null,
        collapsed_bases text not null,
        reason text not null,
        next_action text not null,
        evidence_json text not null,
        primary key (run_id, bookid)
    );
    """)

    rows = list(conn.execute("select bookid, tokens_json, symbol_text from row0_variant_book_tokens order by bookid+0"))
    all_contexts = []
    for r in rows:
        toks = json.loads(r["tokens_json"])
        for c in contexts(toks):
            all_contexts.append((r["bookid"], *c))

    variant_counts = Counter(c[1] for c in all_contexts)
    base_to_variants = defaultdict(set)
    for _, tok, _, _, b in all_contexts:
        base_to_variants[b].add(tok)

    decisions = []
    for bookid in TARGETS:
        row = conn.execute("select * from row0_variant_book_tokens where bookid=?", (bookid,)).fetchone()
        toks = json.loads(row["tokens_json"])
        sels = selector_tokens(toks)
        bases = [base(s) for s in sels]
        ctxs = contexts(toks)
        if "O32" in sels:
            status = "PROMOTE_O32_SELECTOR_CONTROL_NO_GLOSS"
            label = "O32_SINGLETON_SELECTOR_CONTROL"
            promote = 1
            reason = "O32 is the only O32 selector occurrence and collapses destructively into O-base O23 family; preserve as singleton control selector."
            next_action = "Do not merge with O23; no lexical gloss."
        elif sels and any(len(base_to_variants[base(s)]) > 1 for s in sels):
            status = "HOLD_VARIANT_SELECTOR_CONTEXT_ONLY"
            label = "CODE_VARIANT_SELECTOR_CONTEXT"
            promote = 0
            reason = "Book contains preserved selectors, but no new stable role beyond existing residual label."
            next_action = "Use selectors as constraints for future parse tests only."
        else:
            status = "NO_SELECTOR_EVIDENCE"
            label = "NO_CODE_VARIANT_SELECTOR"
            promote = 0
            reason = "No preserved selector variant evidence in current row0 path."
            next_action = "Use other gates."
        evidence = {"selectors": sels, "bases": bases, "contexts": ctxs, "global_variant_counts": dict(variant_counts), "base_to_variants": {k: sorted(v) for k, v in base_to_variants.items()}}
        decisions.append((bookid, status, label, promote, 0, ",".join(sels) or "NONE", ",".join(bases) or "NONE", reason, next_action, json.dumps(evidence, ensure_ascii=False, sort_keys=True)))

    promoted = sum(d[3] for d in decisions)
    summary = {"variant_counts": dict(variant_counts), "base_to_variants": {k: sorted(v) for k, v in base_to_variants.items()}, "promoted_books": [d[0] for d in decisions if d[3]], "principle": "variant selectors are structural constraints only"}
    cur = conn.execute("insert into code_variant_selector_gate_v1_runs (created_at,decision,selector_occurrence_count,selector_variant_count,promoted_count,accepted_prose_gloss_count,summary_json) values (?,?,?,?,?,?,?)", (utc_now(), "CODE_VARIANT_SELECTOR_STRUCTURAL_GATE_NO_GLOSS", len(all_contexts), len(variant_counts), promoted, 0, json.dumps(summary, ensure_ascii=False, sort_keys=True)))
    run_id = cur.lastrowid
    for d in decisions:
        conn.execute("insert into code_variant_selector_gate_v1_items values (?,?,?,?,?,?,?,?,?,?,?)", (run_id, *d))
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": "CODE_VARIANT_SELECTOR_STRUCTURAL_GATE_NO_GLOSS", "promoted_count": promoted, "promoted_books": [d[0] for d in decisions if d[3]], "held_books": [d[0] for d in decisions if not d[3]], "accepted_prose_gloss_count": 0, "summary": summary}, ensure_ascii=False))

if __name__ == "__main__":
    main()
