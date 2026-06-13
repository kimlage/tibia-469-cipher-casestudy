#!/usr/bin/env python3
"""Gate residual display-template concordance against accepted display variants and negative controls."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
TARGETS = ("6", "19", "32", "36")
POS = ("11", "43", "59", "58")
NEG = ("4", "8", "14", "23", "24", "31", "37", "41", "49", "57")
MOTIFS = ("BENNA", "FNAAST", "BTII", "NSBVN", "TNBEE", "LTAST")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def motif_set(s: str):
    return {m for m in MOTIFS if m in s}


def window_score(s: str, anchor: str) -> int:
    score = 0
    for m in MOTIFS:
        if m in s and m in anchor:
            score += 10
            si = s.find(m)
            ai = anchor.find(m)
            score += max(0, 8 - abs(si - ai) // 5)
    return score


def main() -> None:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        create table if not exists display_template_concordance_gate_v1_runs (
            run_id integer primary key autoincrement,
            created_at text not null,
            decision text not null,
            target_count integer not null,
            promoted_count integer not null,
            held_count integer not null,
            accepted_prose_gloss_count integer not null,
            summary_json text not null
        );
        create table if not exists display_template_concordance_gate_v1_items (
            run_id integer not null,
            bookid text not null,
            gate_status text not null,
            proposed_label text not null,
            promotion_allowed integer not null,
            prose_gloss_allowed integer not null,
            best_positive text not null,
            best_positive_score integer not null,
            best_negative text not null,
            best_negative_score integer not null,
            margin integer not null,
            reason text not null,
            next_action text not null,
            evidence_json text not null,
            primary key (run_id, bookid)
        );
        """
    )
    texts = {r["bookid"]: r["symbol_text"] for r in conn.execute("select bookid, symbol_text from row0_variant_book_tokens")}
    items = []
    for bookid in TARGETS:
        text = texts[bookid]
        pos_scores = sorted(((p, window_score(text, texts[p])) for p in POS), key=lambda x: x[1], reverse=True)
        neg_scores = sorted(((n, window_score(text, texts[n])) for n in NEG if n in texts), key=lambda x: x[1], reverse=True)
        bp, bps = pos_scores[0]
        bn, bns = neg_scores[0] if neg_scores else ("NONE", 0)
        margin = bps - bns
        motifs = sorted(motif_set(text))
        if bookid == "36" and bps >= 20 and margin > 10:
            status = "DISPLAY_DRIFT_CONTROL_STABLE_NO_GLOSS"
            label = "BENNA_DISPLAY_DRIFT_CONTROL"
            promote = 0
            reason = "Concords with BENNA display family but existing drift gate makes it display-control only, not semantic function."
            next_action = "Keep as display-control; do not count as functional promotion."
        elif bps >= 20 and margin > 10:
            status = "DISPLAY_TEMPLATE_CONCORDANT_BUT_HELD_NO_GLOSS"
            label = "BENNA_DISPLAY_TEMPLATE_RESIDUE"
            promote = 0
            reason = "Motif concordance exists, but target is residual/display family and lacks independent payload boundary."
            next_action = "Use as negative/control evidence for display grammar only."
        else:
            status = "DISPLAY_TEMPLATE_NOT_CONCORDANT_ENOUGH"
            label = "DISPLAY_RESIDUE_AUDIT"
            promote = 0
            reason = "Positive display similarity does not separate sufficiently from residual negatives."
            next_action = "Hold until boundary concordance independent of display/retext appears."
        evidence = {"motifs": motifs, "positive_scores": pos_scores, "negative_scores": neg_scores, "text": text}
        items.append((bookid, status, label, promote, 0, bp, bps, bn, bns, margin, reason, next_action, json.dumps(evidence, ensure_ascii=False, sort_keys=True)))
    cur = conn.execute(
        """
        insert into display_template_concordance_gate_v1_runs
        (created_at, decision, target_count, promoted_count, held_count, accepted_prose_gloss_count, summary_json)
        values (?, ?, ?, ?, ?, ?, ?)
        """,
        (utc_now(), "DISPLAY_TEMPLATE_CONCORDANCE_HELD_NO_PROMOTION", len(TARGETS), 0, len(TARGETS), 0, json.dumps({"targets": list(TARGETS), "principle": "display concordance is not semantic translation"}, ensure_ascii=False, sort_keys=True)),
    )
    run_id = cur.lastrowid
    for item in items:
        conn.execute(
            """
            insert into display_template_concordance_gate_v1_items
            (run_id, bookid, gate_status, proposed_label, promotion_allowed, prose_gloss_allowed,
             best_positive, best_positive_score, best_negative, best_negative_score, margin,
             reason, next_action, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, *item),
        )
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": "DISPLAY_TEMPLATE_CONCORDANCE_HELD_NO_PROMOTION", "target_count": len(TARGETS), "promoted_count": 0, "accepted_prose_gloss_count": 0, "items": [{"bookid": i[0], "status": i[1], "best_positive": i[5], "best_positive_score": i[6], "best_negative": i[7], "best_negative_score": i[8], "margin": i[9]} for i in items]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
