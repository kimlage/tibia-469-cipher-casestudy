#!/usr/bin/env python3
"""Audit long external Hellgate book anchors against row0 reconstruction."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


DB_PATH = Path(__file__).resolve().parents[1] / "data" / "bonelord_operational.sqlite"
TARGETS = ["HellgateBook_2364672119", "HellgateBook_5765219727"]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def compact(stream: str) -> str:
    return "".join((stream or "").split())


def find_hit(haystack: str, needle: str) -> tuple[int, int]:
    pos = haystack.find(needle)
    return pos, pos + len(needle) if pos >= 0 else -1


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        create table if not exists hellgate_long_anchor_probe_runs (
            run_id integer primary key,
            created_at text not null,
            decision text not null,
            anchor_count integer not null,
            exact_book_anchor_count integer not null,
            row0_aligned_count integer not null,
            continuation_candidate_count integer not null,
            payload_json text not null
        );

        create table if not exists hellgate_long_anchor_items (
            run_id integer not null,
            refname text not null,
            source text not null,
            expected_bookid text not null,
            digits_len integer not null,
            exact_digit_hit integer not null,
            direct_digit_start integer,
            direct_digit_end integer,
            row0_code_hit integer not null,
            row0_code_start integer,
            row0_code_end integer,
            symbol_window text not null,
            token_window text not null,
            anchor_status text not null,
            evidence_json text not null,
            primary key (run_id, refname)
        );
        """
    )

    run_id = conn.execute("select coalesce(max(run_id), 0) + 1 from hellgate_long_anchor_probe_runs").fetchone()[0]
    export_id = conn.execute("select max(__export_id) from sheet__externalrefs_v115").fetchone()[0]
    row0_probe_run = conn.execute("select max(run_id) from row0_code_symbol_probe_books").fetchone()[0]
    row0_token_run = conn.execute("select max(run_id) from row0_variant_book_tokens").fetchone()[0]

    exact_count = row0_aligned = continuation = 0
    items = []
    for ref in TARGETS:
        ext = conn.execute(
            """
            select refname, source, digitssanitized, digitslen, inbooks_bookids
            from sheet__externalrefs_v115
            where __export_id = ? and refname = ?
            order by __row_index
            limit 1
            """,
            (export_id, ref),
        ).fetchone()
        if not ext:
            continue
        bookid = (ext["inbooks_bookids"] or "").split(",")[0].strip()
        book = conn.execute(
            """
            select b.digits, r.reconstructed_code_stream, t.symbol_text, t.token_text
            from sheet__books b
            join row0_code_symbol_probe_books r on r.bookid = b.bookid and r.run_id = ?
            join row0_variant_book_tokens t on t.bookid = b.bookid and t.run_id = ?
            where b.__export_id = ? and b.bookid = ?
            """,
            (row0_probe_run, row0_token_run, export_id, bookid),
        ).fetchone()
        if not book:
            continue

        digits = ext["digitssanitized"]
        d_start, d_end = find_hit(book["digits"], digits)
        code_stream = compact(book["reconstructed_code_stream"])
        c_start, c_end = find_hit(code_stream, digits)
        exact_digit_hit = d_start >= 0
        row0_code_hit = c_start >= 0 and c_start % 2 == 0 and c_end % 2 == 0
        if exact_digit_hit:
            exact_count += 1
        if row0_code_hit:
            row0_aligned += 1
        if exact_digit_hit and not row0_code_hit:
            continuation += 1

        # For a direct book anchor, the whole book is the safest audit window.
        symbol_window = book["symbol_text"]
        token_window = book["token_text"]
        if row0_code_hit:
            status = "EXACT_LONG_BOOK_ANCHOR_ROW0_ALIGNED_NO_GLOSS"
        elif exact_digit_hit:
            status = "EXACT_LONG_BOOK_ANCHOR_DIGIT_ONLY_BOUNDARY_AUDIT_NO_GLOSS"
        else:
            status = "LONG_ANCHOR_NOT_FOUND_IN_EXPECTED_BOOK"

        item = {
            "refname": ext["refname"],
            "source": ext["source"],
            "expected_bookid": bookid,
            "digits_len": int(ext["digitslen"]),
            "exact_digit_hit": exact_digit_hit,
            "direct_digit_start": d_start,
            "direct_digit_end": d_end,
            "row0_code_hit": row0_code_hit,
            "row0_code_start": c_start,
            "row0_code_end": c_end,
            "symbol_window": symbol_window,
            "token_window": token_window,
            "anchor_status": status,
        }
        items.append(item)
        conn.execute(
            """
            insert into hellgate_long_anchor_items
            (run_id, refname, source, expected_bookid, digits_len, exact_digit_hit,
             direct_digit_start, direct_digit_end, row0_code_hit, row0_code_start,
             row0_code_end, symbol_window, token_window, anchor_status, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                item["refname"],
                item["source"],
                item["expected_bookid"],
                item["digits_len"],
                1 if item["exact_digit_hit"] else 0,
                item["direct_digit_start"],
                item["direct_digit_end"],
                1 if item["row0_code_hit"] else 0,
                item["row0_code_start"],
                item["row0_code_end"],
                item["symbol_window"],
                item["token_window"],
                item["anchor_status"],
                json.dumps(
                    {
                        "row0_probe_run": row0_probe_run,
                        "row0_token_run": row0_token_run,
                    },
                    ensure_ascii=False,
                ),
            ),
        )

    decision = "HELLGATE_LONG_ANCHORS_READY_AS_BOUNDARY_CONTROLS_NO_GLOSS"
    if row0_aligned == len(items) and items:
        decision = "HELLGATE_LONG_ANCHORS_ROW0_ALIGNED_NO_GLOSS"
    elif exact_count == 0:
        decision = "HELLGATE_LONG_ANCHORS_NOT_CONFIRMED"

    conn.execute(
        """
        insert into hellgate_long_anchor_probe_runs
        (run_id, created_at, decision, anchor_count, exact_book_anchor_count,
         row0_aligned_count, continuation_candidate_count, payload_json)
        values (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            now_iso(),
            decision,
            len(items),
            exact_count,
            row0_aligned,
            continuation,
            json.dumps({"targets": TARGETS, "export_id": export_id}, ensure_ascii=False),
        ),
    )
    conn.commit()

    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "anchor_count": len(items),
                "exact_book_anchor_count": exact_count,
                "row0_aligned_count": row0_aligned,
                "continuation_candidate_count": continuation,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
