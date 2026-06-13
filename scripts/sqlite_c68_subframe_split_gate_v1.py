#!/usr/bin/env python3
"""Classify C68 into mechanical subframes using local row0 token context."""
from __future__ import annotations

import json
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
TARGETS = {"8", "19", "23", "24", "41", "57"}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def classify(tokens, i):
    left2 = tokens[max(0, i - 2):i]
    right4 = tokens[i + 1:i + 5]
    left3 = tokens[max(0, i - 3):i]
    if left2 == ["V", "N"] and right4[:3] == ["T", "I", "I"]:
        return "C68_VN_TIIN_CONTEXT_SUBFRAME"
    if left3 == ["F", "A", "T"] and right4[:3] == ["T", "I", "V"]:
        return "C68_FAT_TIV_SLOT_SUBFRAME"
    if right4[:3] == ["T", "I", "I"]:
        return "C68_TIIN_CONTEXT_WEAK"
    if right4[:3] == ["T", "I", "V"]:
        return "C68_TIV_SLOT_WEAK"
    return "C68_UNCLASSIFIED_CONTEXT"


def main() -> None:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        create table if not exists c68_subframe_split_gate_v1_runs (
            run_id integer primary key autoincrement,
            created_at text not null,
            decision text not null,
            occurrence_count integer not null,
            target_occurrence_count integer not null,
            separable_count integer not null,
            promoted_book_count integer not null,
            accepted_prose_gloss_count integer not null,
            summary_json text not null
        );
        create table if not exists c68_subframe_split_gate_v1_occurrences (
            run_id integer not null,
            bookid text not null,
            occurrence_index integer not null,
            token_pos integer not null,
            subframe text not null,
            left_context text not null,
            right_context text not null,
            target_book integer not null,
            promotion_allowed integer not null,
            reason text not null,
            evidence_json text not null,
            primary key (run_id, bookid, occurrence_index)
        );
        create table if not exists c68_subframe_split_gate_v1_book_decisions (
            run_id integer not null,
            bookid text not null,
            book_status text not null,
            proposed_label text not null,
            promotion_allowed integer not null,
            prose_gloss_allowed integer not null,
            reason text not null,
            next_action text not null,
            evidence_json text not null,
            primary key (run_id, bookid)
        );
        """
    )
    rows = list(conn.execute("select bookid, tokens_json from row0_variant_book_tokens order by bookid+0"))
    occs = []
    by_book = {}
    for r in rows:
        tokens = json.loads(r["tokens_json"])
        book_occs = []
        for i, tok in enumerate(tokens):
            if tok == "C68":
                sub = classify(tokens, i)
                occ = {
                    "bookid": r["bookid"],
                    "idx": len(book_occs) + 1,
                    "pos": i,
                    "subframe": sub,
                    "left": " ".join(tokens[max(0, i - 6):i]),
                    "right": " ".join(tokens[i + 1:i + 7]),
                    "target": int(r["bookid"] in TARGETS),
                    "promote": 0,
                    "reason": "C68 occurrence classified mechanically; no prose gloss.",
                    "evidence": {"tokens_window": tokens[max(0, i - 6):i + 7]},
                }
                book_occs.append(occ)
                occs.append(occ)
        if book_occs:
            by_book[r["bookid"]] = book_occs

    decisions = []
    for bookid in sorted(TARGETS, key=int):
        bos = by_book.get(bookid, [])
        subframes = [o["subframe"] for o in bos]
        counts = Counter(subframes)
        if not bos:
            status = "NO_C68_OCCURRENCE_CURRENT_ROW0"
            label = "NO_C68_SUBFRAME"
            promote = 0
            reason = "No C68 occurrence in current row0 path."
            next_action = "Do not use C68 split for this book."
        elif set(subframes).issubset({"C68_VN_TIIN_CONTEXT_SUBFRAME", "C68_TIIN_CONTEXT_WEAK"}) and len(bos) == 1:
            status = "PROMOTE_C68_CONTEXT_SUBFRAME_NO_GLOSS"
            label = "C68_VN_TIIN_CONTEXT_SUBFRAME"
            promote = 1
            reason = "Single C68 occurrence matches VN/TIIN context subframe and reduces handoff-slot ambiguity."
            next_action = "Promote only as related structural context subframe; no human gloss."
        elif "C68_FAT_TIV_SLOT_SUBFRAME" in subframes and "C68_VN_TIIN_CONTEXT_SUBFRAME" in subframes:
            status = "PROMOTE_C68_DUAL_SUBFRAME_COMPOSITION_NO_GLOSS"
            label = "C68_DUAL_CONTEXT_AND_SLOT_SUBFRAMES"
            promote = 1
            reason = "Book contains both separable C68 context and FAT/TIV slot subframes; resolves overfiring of a single C68 label."
            next_action = "Promote as composite structural C68 parse; no human gloss."
        elif "C68_VN_TIIN_CONTEXT_SUBFRAME" in subframes and len(bos) > 1:
            status = "PROMOTE_C68_REPEATED_CONTEXT_COMPOSITION_NO_GLOSS"
            label = "C68_REPEATED_CONTEXT_SUBFRAME"
            promote = 1
            reason = "Multiple C68 occurrences include VN/TIIN context subframe; treat as repeated context composition."
            next_action = "Promote as related structural composition; no human gloss."
        else:
            status = "HOLD_C68_WEAK_OR_CONFLICTING"
            label = "C68_AUDIT_WEAK"
            promote = 0
            reason = "C68 occurrence does not cleanly separate into accepted subframes."
            next_action = "Hold until row0 path or additional selector evidence improves."
        decisions.append({"bookid": bookid, "status": status, "label": label, "promote": promote, "reason": reason, "next_action": next_action, "evidence": {"occurrences": bos, "subframe_counts": dict(counts)}})

    promoted_books = [d["bookid"] for d in decisions if d["promote"]]
    summary = {"subframe_counts": dict(Counter(o["subframe"] for o in occs)), "target_books": sorted(TARGETS, key=int), "promoted_books": promoted_books, "principle": "C68 split is structural only, not lexical translation"}
    cur = conn.execute(
        """
        insert into c68_subframe_split_gate_v1_runs
        (created_at, decision, occurrence_count, target_occurrence_count, separable_count, promoted_book_count, accepted_prose_gloss_count, summary_json)
        values (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (utc_now(), "C68_SUBFRAME_SPLIT_STRUCTURAL_NO_GLOSS", len(occs), sum(o["target"] for o in occs), sum(1 for o in occs if o["subframe"] != "C68_UNCLASSIFIED_CONTEXT"), len(promoted_books), 0, json.dumps(summary, ensure_ascii=False, sort_keys=True)),
    )
    run_id = cur.lastrowid
    for o in occs:
        conn.execute(
            """
            insert into c68_subframe_split_gate_v1_occurrences
            (run_id, bookid, occurrence_index, token_pos, subframe, left_context, right_context,
             target_book, promotion_allowed, reason, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, o["bookid"], o["idx"], o["pos"], o["subframe"], o["left"], o["right"], o["target"], o["promote"], o["reason"], json.dumps(o["evidence"], ensure_ascii=False, sort_keys=True)),
        )
    for d in decisions:
        conn.execute(
            """
            insert into c68_subframe_split_gate_v1_book_decisions
            (run_id, bookid, book_status, proposed_label, promotion_allowed, prose_gloss_allowed, reason, next_action, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, d["bookid"], d["status"], d["label"], d["promote"], 0, d["reason"], d["next_action"], json.dumps(d["evidence"], ensure_ascii=False, sort_keys=True)),
        )
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": "C68_SUBFRAME_SPLIT_STRUCTURAL_NO_GLOSS", "promoted_book_count": len(promoted_books), "promoted_books": promoted_books, "summary": summary}, ensure_ascii=False))


if __name__ == "__main__":
    main()
