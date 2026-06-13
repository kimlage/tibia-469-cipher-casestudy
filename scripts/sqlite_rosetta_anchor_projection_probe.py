#!/usr/bin/env python3
"""Project external rosetta digit-word anchors into the row0 book corpus.

This is an audit-only probe. It does not promote semantic glosses. The goal is
to decide whether external NPC digit-word anchors are mechanically compatible
with the canonical row0 code-symbol model or only useful as quarantined lore.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


DB_PATH = Path(__file__).resolve().parents[1] / "data" / "bonelord_operational.sqlite"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def compact_code_stream(stream: str) -> str:
    return "".join(stream.split())


def count_substring(text: str, needle: str) -> int:
    if not text or not needle:
        return 0
    count = start = 0
    while True:
        pos = text.find(needle, start)
        if pos < 0:
            return count
        count += 1
        start = pos + 1


def code_boundary_hits(stream: str, needle: str) -> int:
    """Count hits where the needle starts and ends on 2-digit code boundaries."""
    if not stream or not needle or len(needle) % 2:
        return 0
    count = 0
    start = 0
    while True:
        pos = stream.find(needle, start)
        if pos < 0:
            return count
        if pos % 2 == 0 and (pos + len(needle)) % 2 == 0:
            count += 1
        start = pos + 1


def classify(anchor: dict, direct_books: int, direct_hits: int, aligned_hits: int, crossed_hits: int) -> str:
    promotion_allowed = int(anchor.get("book_promotion_allowed") or 0)
    strength = anchor.get("strength") or ""
    digits = anchor["digits"]
    if direct_hits == 0 and aligned_hits == 0:
        return "OUT_OF_BOOK_CORPUS"
    if aligned_hits > 0 and promotion_allowed and strength == "HARD_EXTERNAL_PHRASE":
        return "MECHANICALLY_COMPATIBLE_AUDIT_ONLY"
    if aligned_hits > 0:
        return "ALIGNED_BUT_QUARANTINED"
    if crossed_hits > 0 or direct_hits > 0:
        if len(digits) % 2:
            return "CROSSES_ROW0_CODE_BOUNDARIES_AUDIT_ONLY"
        return "DIRECT_DIGIT_ONLY_NOT_ROW0_CONFIRMED"
    if direct_books > 10:
        return "COMMON_NUMERIC_FRAGMENT_AUDIT_ONLY"
    return "NO_PROMOTION_SIGNAL"


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    conn.executescript(
        """
        create table if not exists rosetta_anchor_projection_probe_runs (
            run_id integer primary key,
            created_at text not null,
            decision text not null,
            anchor_count integer not null,
            compatible_count integer not null,
            quarantined_count integer not null,
            out_of_corpus_count integer not null,
            payload_json text not null
        );

        create table if not exists rosetta_anchor_projection_items (
            run_id integer not null,
            anchor_id text not null,
            digits text not null,
            word text not null,
            phrase_id text,
            refname text,
            strength text not null,
            promotion_status text not null,
            book_promotion_allowed integer not null,
            direct_digit_book_count integer not null,
            direct_digit_hit_count integer not null,
            aligned_codestream_book_count integer not null,
            aligned_codestream_hit_count integer not null,
            crossed_boundary_hit_count integer not null,
            projection_status text not null,
            evidence_json text not null,
            primary key (run_id, anchor_id)
        );
        """
    )

    run_id = (conn.execute("select coalesce(max(run_id), 0) + 1 from rosetta_anchor_projection_probe_runs").fetchone()[0])

    npc_run_id = conn.execute("select max(run_id) from npc_wordcode_anchors").fetchone()[0]
    row0_run_id = conn.execute("select max(run_id) from row0_code_symbol_probe_books").fetchone()[0]
    export_id = conn.execute("select max(__export_id) from sheet__books").fetchone()[0]

    anchors = [
        dict(row)
        for row in conn.execute(
            """
            select anchor_id, digits, word, phrase_id, refname, strength, promotion_status,
                   book_promotion_allowed, notes
            from npc_wordcode_anchors
            where run_id = ?
            order by anchor_id
            """,
            (npc_run_id,),
        )
    ]

    books = [
        dict(row)
        for row in conn.execute(
            """
            select b.bookid, b.digits, r.reconstructed_code_stream
            from sheet__books b
            join row0_code_symbol_probe_books r on r.bookid = b.bookid
            where b.__export_id = ? and r.run_id = ?
            order by cast(b.bookid as integer)
            """,
            (export_id, row0_run_id),
        )
    ]

    compatible = quarantined = out_of_corpus = 0
    for anchor in anchors:
        digits = anchor["digits"]
        direct_books = direct_hits = aligned_books = aligned_hits = crossed_hits = 0
        examples = []
        for book in books:
            direct = count_substring(book["digits"], digits)
            compact = compact_code_stream(book["reconstructed_code_stream"])
            aligned = code_boundary_hits(compact, digits)
            crossed = count_substring(compact, digits) - aligned
            if direct:
                direct_books += 1
                direct_hits += direct
            if aligned:
                aligned_books += 1
                aligned_hits += aligned
            if crossed:
                crossed_hits += crossed
            if (direct or aligned or crossed) and len(examples) < 5:
                examples.append(
                    {
                        "bookid": book["bookid"],
                        "direct_hits": direct,
                        "aligned_hits": aligned,
                        "crossed_hits": crossed,
                    }
                )

        status = classify(anchor, direct_books, direct_hits, aligned_hits, crossed_hits)
        if status == "MECHANICALLY_COMPATIBLE_AUDIT_ONLY":
            compatible += 1
        elif status == "OUT_OF_BOOK_CORPUS":
            out_of_corpus += 1
        else:
            quarantined += 1

        conn.execute(
            """
            insert into rosetta_anchor_projection_items
            (run_id, anchor_id, digits, word, phrase_id, refname, strength, promotion_status,
             book_promotion_allowed, direct_digit_book_count, direct_digit_hit_count,
             aligned_codestream_book_count, aligned_codestream_hit_count,
             crossed_boundary_hit_count, projection_status, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                anchor["anchor_id"],
                digits,
                anchor["word"],
                anchor["phrase_id"],
                anchor["refname"],
                anchor["strength"],
                anchor["promotion_status"],
                int(anchor["book_promotion_allowed"] or 0),
                direct_books,
                direct_hits,
                aligned_books,
                aligned_hits,
                crossed_hits,
                status,
                json.dumps({"examples": examples, "notes": anchor.get("notes")}, ensure_ascii=False),
            ),
        )

    decision = "ROSETTA_ANCHORS_QUARANTINED_NO_BOOK_GLOSS"
    if compatible:
        decision = "ROSETTA_ANCHORS_HAVE_ROW0_COMPATIBLE_AUDIT_SIGNALS_NO_GLOSS"

    conn.execute(
        """
        insert into rosetta_anchor_projection_probe_runs
        (run_id, created_at, decision, anchor_count, compatible_count, quarantined_count,
         out_of_corpus_count, payload_json)
        values (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            now_iso(),
            decision,
            len(anchors),
            compatible,
            quarantined,
            out_of_corpus,
            json.dumps({"npc_run_id": npc_run_id, "row0_run_id": row0_run_id, "export_id": export_id}),
        ),
    )
    conn.commit()

    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "anchor_count": len(anchors),
                "compatible_count": compatible,
                "quarantined_count": quarantined,
                "out_of_corpus_count": out_of_corpus,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
