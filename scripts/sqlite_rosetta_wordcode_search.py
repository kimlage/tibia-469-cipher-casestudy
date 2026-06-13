#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import UTC, datetime
from typing import Any, Dict, Iterable, List

from sqlite_snapshot_ref import DEFAULT_SNAPSHOT_NAME, resolve_export_id


DEFAULT_DB = "./data/bonelord_operational.sqlite"

PHRASE_ANCHORS = [
    {
        "phrase_anchor_id": "evil_eye_653768764",
        "digits": "653768764",
        "segments": ["653", "768", "764"],
        "expected": "look at you",
        "strength": "HARD_EXTERNAL_PHRASE",
    },
    {
        "phrase_anchor_id": "elder_65997854764",
        "digits": "65997854764",
        "segments": ["659", "978", "54", "764"],
        "expected": "let me see you",
        "strength": "SOFT_LEGACY_PHRASE",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Search Rosetta digit-word anchors across SQLite operational state")
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--export-id", type=int, default=None)
    parser.add_argument("--snapshot-name", default=DEFAULT_SNAPSHOT_NAME)
    parser.add_argument("--record", action="store_true")
    parser.add_argument("--context", type=int, default=14)
    parser.add_argument("--max-output-occurrences", type=int, default=80)
    return parser.parse_args()


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table,),
    ).fetchone()
    return row is not None


def column_names(conn: sqlite3.Connection, table: str) -> set[str]:
    if not table_exists(conn, table):
        return set()
    return {str(row["name"]).lower() for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}


def fetch_anchors(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    if not table_exists(conn, "rosetta_digit_word_anchors"):
        return []
    rows = conn.execute(
        """
        SELECT anchor_id, mode, digits, word, phrase_anchor_id, strength, source, notes
        FROM rosetta_digit_word_anchors
        ORDER BY phrase_anchor_id, anchor_id
        """
    ).fetchall()
    return [dict(row) for row in rows]


def contains_positions(text: object, needle: str) -> List[int]:
    haystack = str(text or "")
    if not needle:
        return []
    starts: List[int] = []
    pos = haystack.find(needle)
    while pos >= 0:
        starts.append(pos)
        pos = haystack.find(needle, pos + 1)
    return starts


def digits_context(text: object, start: int, needle: str, radius: int) -> str:
    haystack = str(text or "")
    lo = max(0, start - radius)
    hi = min(len(haystack), start + len(needle) + radius)
    return haystack[lo:hi]


def add_occurrence(
    occurrences: List[Dict[str, Any]],
    *,
    phrase_anchor_id: str | None,
    anchor_id: str | None,
    mode: str,
    digits: str,
    word: str | None,
    phrase_expected: str | None,
    location_kind: str,
    source_table: str,
    source_key: str,
    match_kind: str,
    context_digits: str,
    observed_text: str | None,
    refname: str | None = None,
    bookid: str | None = None,
    source_id: str | None = None,
    inbooks_count: str | None = None,
    payload: Dict[str, Any] | None = None,
) -> None:
    occurrences.append(
        {
            "phrase_anchor_id": phrase_anchor_id,
            "anchor_id": anchor_id,
            "mode": mode,
            "digits": digits,
            "word": word,
            "phrase_expected": phrase_expected,
            "location_kind": location_kind,
            "source_table": source_table,
            "source_key": source_key,
            "match_kind": match_kind,
            "refname": refname,
            "bookid": bookid,
            "source_id": source_id,
            "inbooks_count": inbooks_count,
            "context_digits": context_digits,
            "observed_text": observed_text,
            "payload": payload or {},
        }
    )


def observed_book_text(row: sqlite3.Row) -> str:
    parts = [
        row["translation_contextenglish_auto"],
        row["translation_english_auto"],
        row["translation_strictplus_v108"],
    ]
    return " | ".join(str(part) for part in parts if part not in (None, ""))


def observed_external_text(row: sqlite3.Row) -> str:
    parts = [
        row["dp_strictplus"],
        row["codestreamdp_concat_readable_v120"],
        row["decodedbase"],
        row["codestreambase_v120"],
    ]
    return " | ".join(str(part) for part in parts if part not in (None, ""))


def phrase_by_id() -> Dict[str, Dict[str, Any]]:
    return {phrase["phrase_anchor_id"]: phrase for phrase in PHRASE_ANCHORS}


def search_books(conn: sqlite3.Connection, export_id: int, anchors: List[Dict[str, Any]], context: int) -> List[Dict[str, Any]]:
    occurrences: List[Dict[str, Any]] = []
    if not table_exists(conn, "sheet__books"):
        return occurrences
    rows = conn.execute(
        """
        SELECT bookid, digits, translation_contextenglish_auto, translation_english_auto, translation_strictplus_v108
        FROM sheet__books
        WHERE __export_id = ?
          AND digits IS NOT NULL
        ORDER BY CAST(bookid AS INTEGER)
        """,
        (export_id,),
    ).fetchall()
    phrase_lookup = phrase_by_id()
    for row in rows:
        source_key = f"Book:{row['bookid']}"
        for phrase in PHRASE_ANCHORS:
            for start in contains_positions(row["digits"], phrase["digits"]):
                add_occurrence(
                    occurrences,
                    phrase_anchor_id=phrase["phrase_anchor_id"],
                    anchor_id=None,
                    mode="NPC_SPEECH_WORDCODE",
                    digits=phrase["digits"],
                    word=None,
                    phrase_expected=phrase["expected"],
                    location_kind="book",
                    source_table="sheet__books",
                    source_key=source_key,
                    match_kind="PHRASE_CONTAINS",
                    bookid=str(row["bookid"]),
                    context_digits=digits_context(row["digits"], start, phrase["digits"], context),
                    observed_text=observed_book_text(row),
                    payload={"strength": phrase["strength"]},
                )
        for anchor in anchors:
            phrase = phrase_lookup.get(str(anchor["phrase_anchor_id"]))
            for start in contains_positions(row["digits"], str(anchor["digits"])):
                add_occurrence(
                    occurrences,
                    phrase_anchor_id=anchor["phrase_anchor_id"],
                    anchor_id=anchor["anchor_id"],
                    mode=anchor["mode"],
                    digits=anchor["digits"],
                    word=anchor["word"],
                    phrase_expected=phrase["expected"] if phrase else None,
                    location_kind="book",
                    source_table="sheet__books",
                    source_key=source_key,
                    match_kind="SEGMENT_CONTAINS",
                    bookid=str(row["bookid"]),
                    context_digits=digits_context(row["digits"], start, str(anchor["digits"]), context),
                    observed_text=observed_book_text(row),
                    payload={"strength": anchor["strength"], "source": anchor["source"]},
                )
    return occurrences


def search_external_refs(conn: sqlite3.Connection, export_id: int, anchors: List[Dict[str, Any]], context: int) -> List[Dict[str, Any]]:
    occurrences: List[Dict[str, Any]] = []
    if not table_exists(conn, "sheet__externalrefs_v115"):
        return occurrences
    rows = conn.execute(
        """
        SELECT refname, type, source, numerictext, digitssanitized, inbooks_count, inbooks_bookids,
               decodedbase, dp_strictplus, codestreambase_v120, codestreamdp_concat_readable_v120
        FROM sheet__externalrefs_v115
        WHERE __export_id = ?
          AND digitssanitized IS NOT NULL
        ORDER BY __row_index
        """,
        (export_id,),
    ).fetchall()
    phrase_lookup = phrase_by_id()
    for row in rows:
        source_key = f"ExternalRef:{row['refname']}"
        for phrase in PHRASE_ANCHORS:
            for start in contains_positions(row["digitssanitized"], phrase["digits"]):
                match_kind = "PHRASE_EXACT" if str(row["digitssanitized"]) == phrase["digits"] else "PHRASE_CONTAINS"
                add_occurrence(
                    occurrences,
                    phrase_anchor_id=phrase["phrase_anchor_id"],
                    anchor_id=None,
                    mode="NPC_SPEECH_WORDCODE",
                    digits=phrase["digits"],
                    word=None,
                    phrase_expected=phrase["expected"],
                    location_kind="external_ref",
                    source_table="sheet__externalrefs_v115",
                    source_key=source_key,
                    match_kind=match_kind,
                    refname=str(row["refname"]),
                    inbooks_count=str(row["inbooks_count"] or ""),
                    context_digits=digits_context(row["digitssanitized"], start, phrase["digits"], context),
                    observed_text=observed_external_text(row),
                    payload={"type": row["type"], "source": row["source"], "inbooks_bookids": row["inbooks_bookids"]},
                )
        for anchor in anchors:
            phrase = phrase_lookup.get(str(anchor["phrase_anchor_id"]))
            for start in contains_positions(row["digitssanitized"], str(anchor["digits"])):
                match_kind = "SEGMENT_EXACT" if str(row["digitssanitized"]) == str(anchor["digits"]) else "SEGMENT_CONTAINS"
                add_occurrence(
                    occurrences,
                    phrase_anchor_id=anchor["phrase_anchor_id"],
                    anchor_id=anchor["anchor_id"],
                    mode=anchor["mode"],
                    digits=anchor["digits"],
                    word=anchor["word"],
                    phrase_expected=phrase["expected"] if phrase else None,
                    location_kind="external_ref",
                    source_table="sheet__externalrefs_v115",
                    source_key=source_key,
                    match_kind=match_kind,
                    refname=str(row["refname"]),
                    inbooks_count=str(row["inbooks_count"] or ""),
                    context_digits=digits_context(row["digitssanitized"], start, str(anchor["digits"]), context),
                    observed_text=observed_external_text(row),
                    payload={"strength": anchor["strength"], "source": row["source"], "inbooks_bookids": row["inbooks_bookids"]},
                )
    return occurrences


def search_digit_run_table(
    conn: sqlite3.Connection,
    export_id: int,
    table: str,
    digits_column: str,
    anchors: List[Dict[str, Any]],
    context: int,
    location_kind: str,
) -> List[Dict[str, Any]]:
    occurrences: List[Dict[str, Any]] = []
    cols = column_names(conn, table)
    if digits_column.lower() not in cols:
        return occurrences
    select_cols = ["__row_index", digits_column]
    for optional in ("sourceid", "url", "refname", "hitkind", "inbookscount", "inbooksbookids", "sourceids", "urls", "priority", "notes"):
        if optional in cols:
            select_cols.append(optional)
    rows = conn.execute(
        f"""
        SELECT {', '.join(select_cols)}
        FROM {table}
        WHERE __export_id = ?
          AND {digits_column} IS NOT NULL
        ORDER BY __row_index
        """,
        (export_id,),
    ).fetchall()
    phrase_lookup = phrase_by_id()
    for row in rows:
        run_digits = row[digits_column]
        source_key = f"{table}:{row['__row_index']}"
        source_id = str(row["sourceid"]) if "sourceid" in row.keys() and row["sourceid"] is not None else None
        refname = str(row["refname"]) if "refname" in row.keys() and row["refname"] is not None else None
        inbooks_count = None
        if "inbookscount" in row.keys():
            inbooks_count = str(row["inbookscount"] or "")
        for phrase in PHRASE_ANCHORS:
            for start in contains_positions(run_digits, phrase["digits"]):
                match_kind = "PHRASE_EXACT" if str(run_digits) == phrase["digits"] else "PHRASE_CONTAINS"
                add_occurrence(
                    occurrences,
                    phrase_anchor_id=phrase["phrase_anchor_id"],
                    anchor_id=None,
                    mode="NPC_SPEECH_WORDCODE",
                    digits=phrase["digits"],
                    word=None,
                    phrase_expected=phrase["expected"],
                    location_kind=location_kind,
                    source_table=table,
                    source_key=source_key,
                    match_kind=match_kind,
                    refname=refname,
                    source_id=source_id,
                    inbooks_count=inbooks_count,
                    context_digits=digits_context(run_digits, start, phrase["digits"], context),
                    observed_text=str(row["notes"]) if "notes" in row.keys() and row["notes"] is not None else None,
                    payload={key: row[key] for key in row.keys() if key not in {"__row_index", digits_column}},
                )
        for anchor in anchors:
            phrase = phrase_lookup.get(str(anchor["phrase_anchor_id"]))
            for start in contains_positions(run_digits, str(anchor["digits"])):
                match_kind = "SEGMENT_EXACT" if str(run_digits) == str(anchor["digits"]) else "SEGMENT_CONTAINS"
                add_occurrence(
                    occurrences,
                    phrase_anchor_id=anchor["phrase_anchor_id"],
                    anchor_id=anchor["anchor_id"],
                    mode=anchor["mode"],
                    digits=anchor["digits"],
                    word=anchor["word"],
                    phrase_expected=phrase["expected"] if phrase else None,
                    location_kind=location_kind,
                    source_table=table,
                    source_key=source_key,
                    match_kind=match_kind,
                    refname=refname,
                    source_id=source_id,
                    inbooks_count=inbooks_count,
                    context_digits=digits_context(run_digits, start, str(anchor["digits"]), context),
                    observed_text=str(row["notes"]) if "notes" in row.keys() and row["notes"] is not None else None,
                    payload={key: row[key] for key in row.keys() if key not in {"__row_index", digits_column}},
                )
    return occurrences


def search_group_candidates(conn: sqlite3.Connection, export_id: int, anchors: List[Dict[str, Any]], context: int) -> List[Dict[str, Any]]:
    occurrences: List[Dict[str, Any]] = []
    table = "sheet__codestreamcandidates_v119"
    cols = column_names(conn, table)
    if "digitsgroup" not in cols:
        return occurrences
    rows = conn.execute(
        """
        SELECT __row_index, refname, groupindex, digitsgroup, base, dp_readable, dp_lossless
        FROM sheet__codestreamcandidates_v119
        WHERE __export_id = ?
          AND digitsgroup IS NOT NULL
        ORDER BY __row_index
        """,
        (export_id,),
    ).fetchall()
    phrase_lookup = phrase_by_id()
    for row in rows:
        for anchor in anchors:
            phrase = phrase_lookup.get(str(anchor["phrase_anchor_id"]))
            for start in contains_positions(row["digitsgroup"], str(anchor["digits"])):
                add_occurrence(
                    occurrences,
                    phrase_anchor_id=anchor["phrase_anchor_id"],
                    anchor_id=anchor["anchor_id"],
                    mode=anchor["mode"],
                    digits=anchor["digits"],
                    word=anchor["word"],
                    phrase_expected=phrase["expected"] if phrase else None,
                    location_kind="external_group_candidate",
                    source_table=table,
                    source_key=f"{table}:{row['__row_index']}",
                    match_kind="SEGMENT_EXACT" if str(row["digitsgroup"]) == str(anchor["digits"]) else "SEGMENT_CONTAINS",
                    refname=str(row["refname"]),
                    context_digits=digits_context(row["digitsgroup"], start, str(anchor["digits"]), context),
                    observed_text=" | ".join(str(row[key]) for key in ("base", "dp_readable", "dp_lossless") if row[key] not in (None, "")),
                    payload={"groupindex": row["groupindex"]},
                )
    return occurrences


def summarize(anchors: List[Dict[str, Any]], occurrences: List[Dict[str, Any]], export_id: int) -> Dict[str, Any]:
    def count(location: str | None = None, match_prefix: str | None = None, table: str | None = None) -> int:
        total = 0
        for occ in occurrences:
            if location is not None and occ["location_kind"] != location:
                continue
            if table is not None and occ["source_table"] != table:
                continue
            if match_prefix is not None and not str(occ["match_kind"]).startswith(match_prefix):
                continue
            total += 1
        return total

    book_phrase = count(location="book", match_prefix="PHRASE")
    external_phrase = sum(
        1
        for occ in occurrences
        if occ["location_kind"] != "book" and str(occ["match_kind"]).startswith("PHRASE")
    )
    book_segment = count(location="book", match_prefix="SEGMENT")
    external_segment = sum(
        1
        for occ in occurrences
        if occ["location_kind"] != "book" and str(occ["match_kind"]).startswith("SEGMENT")
    )
    source_hits = count(table="sheet__externalsourcedigithits_v472")
    candidates = count(table="sheet__externalrefcandidates_v472")

    phrase_summary: Dict[str, Dict[str, Any]] = {}
    for phrase in PHRASE_ANCHORS:
        phrase_occ = [occ for occ in occurrences if occ["phrase_anchor_id"] == phrase["phrase_anchor_id"]]
        phrase_summary[phrase["phrase_anchor_id"]] = {
            "digits": phrase["digits"],
            "expected": phrase["expected"],
            "strength": phrase["strength"],
            "book_phrase_occurrences": sum(1 for occ in phrase_occ if occ["location_kind"] == "book" and str(occ["match_kind"]).startswith("PHRASE")),
            "external_phrase_occurrences": sum(1 for occ in phrase_occ if occ["location_kind"] != "book" and str(occ["match_kind"]).startswith("PHRASE")),
            "book_segment_occurrences": sum(1 for occ in phrase_occ if occ["location_kind"] == "book" and str(occ["match_kind"]).startswith("SEGMENT")),
            "external_segment_occurrences": sum(1 for occ in phrase_occ if occ["location_kind"] != "book" and str(occ["match_kind"]).startswith("SEGMENT")),
        }

    phrase_count = len(PHRASE_ANCHORS)
    if external_phrase >= phrase_count and book_phrase == 0:
        conclusion = "SEPARATE_NPC_SPEECH_WORDCODE_LIKELY"
        mode_evidence_pct = 100.0
    elif external_phrase > 0 and book_phrase > 0:
        conclusion = "MIXED_OR_SHARED_MODE_REQUIRES_SEGMENTATION"
        mode_evidence_pct = 45.0
    elif external_phrase > 0:
        conclusion = "PARTIAL_EXTERNAL_WORDCODE_EVIDENCE"
        mode_evidence_pct = 60.0
    else:
        conclusion = "INSUFFICIENT_WORDCODE_EVIDENCE"
        mode_evidence_pct = 0.0

    return {
        "export_id": export_id,
        "anchor_count": len(anchors),
        "phrase_count": phrase_count,
        "book_segment_occurrences": book_segment,
        "book_phrase_occurrences": book_phrase,
        "external_segment_occurrences": external_segment,
        "external_phrase_occurrences": external_phrase,
        "source_hit_occurrences": source_hits,
        "candidate_occurrences": candidates,
        "mode_evidence_pct": mode_evidence_pct,
        "conclusion": conclusion,
        "phrase_summary": phrase_summary,
        "interpretation": "Phrase-level matches are strong evidence; isolated segment substring hits in book digit streams are noisy and should not be treated as translation proof.",
    }


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS rosetta_wordcode_search_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            export_id INTEGER NOT NULL,
            anchor_count INTEGER NOT NULL,
            phrase_count INTEGER NOT NULL,
            book_segment_occurrences INTEGER NOT NULL,
            book_phrase_occurrences INTEGER NOT NULL,
            external_segment_occurrences INTEGER NOT NULL,
            external_phrase_occurrences INTEGER NOT NULL,
            source_hit_occurrences INTEGER NOT NULL,
            candidate_occurrences INTEGER NOT NULL,
            mode_evidence_pct REAL NOT NULL,
            conclusion TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS rosetta_wordcode_occurrences (
            occurrence_id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
            phrase_anchor_id TEXT,
            anchor_id TEXT,
            mode TEXT NOT NULL,
            digits TEXT NOT NULL,
            word TEXT,
            phrase_expected TEXT,
            location_kind TEXT NOT NULL,
            source_table TEXT NOT NULL,
            source_key TEXT,
            match_kind TEXT NOT NULL,
            refname TEXT,
            bookid TEXT,
            source_id TEXT,
            inbooks_count TEXT,
            context_digits TEXT,
            observed_text TEXT,
            payload_json TEXT NOT NULL
        );
        """
    )


def record(conn: sqlite3.Connection, summary: Dict[str, Any], occurrences: List[Dict[str, Any]]) -> int:
    ensure_schema(conn)
    created_at = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    cur = conn.execute(
        """
        INSERT INTO rosetta_wordcode_search_runs (
            created_at, export_id, anchor_count, phrase_count,
            book_segment_occurrences, book_phrase_occurrences,
            external_segment_occurrences, external_phrase_occurrences,
            source_hit_occurrences, candidate_occurrences,
            mode_evidence_pct, conclusion, payload_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            created_at,
            summary["export_id"],
            summary["anchor_count"],
            summary["phrase_count"],
            summary["book_segment_occurrences"],
            summary["book_phrase_occurrences"],
            summary["external_segment_occurrences"],
            summary["external_phrase_occurrences"],
            summary["source_hit_occurrences"],
            summary["candidate_occurrences"],
            summary["mode_evidence_pct"],
            summary["conclusion"],
            json.dumps(summary, ensure_ascii=True, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)
    for occ in occurrences:
        conn.execute(
            """
            INSERT INTO rosetta_wordcode_occurrences (
                run_id, phrase_anchor_id, anchor_id, mode, digits, word, phrase_expected,
                location_kind, source_table, source_key, match_kind, refname, bookid,
                source_id, inbooks_count, context_digits, observed_text, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                occ["phrase_anchor_id"],
                occ["anchor_id"],
                occ["mode"],
                occ["digits"],
                occ["word"],
                occ["phrase_expected"],
                occ["location_kind"],
                occ["source_table"],
                occ["source_key"],
                occ["match_kind"],
                occ["refname"],
                occ["bookid"],
                occ["source_id"],
                occ["inbooks_count"],
                occ["context_digits"],
                occ["observed_text"],
                json.dumps(occ["payload"], ensure_ascii=True, sort_keys=True),
            ),
        )
    conn.commit()
    return run_id


def sorted_occurrences_for_output(occurrences: Iterable[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
    priority = {
        "PHRASE_EXACT": 0,
        "PHRASE_CONTAINS": 1,
        "SEGMENT_EXACT": 2,
        "SEGMENT_CONTAINS": 3,
    }
    ordered = sorted(
        occurrences,
        key=lambda occ: (
            priority.get(str(occ["match_kind"]), 9),
            0 if occ["location_kind"] != "book" else 1,
            str(occ["phrase_anchor_id"] or ""),
            str(occ["source_key"] or ""),
        ),
    )
    return ordered[:limit]


def main() -> int:
    args = parse_args()
    conn = connect(args.db)
    try:
        export_id = resolve_export_id(conn, export_id=args.export_id, snapshot_name=args.snapshot_name)
        anchors = fetch_anchors(conn)
        occurrences: List[Dict[str, Any]] = []
        occurrences.extend(search_books(conn, export_id, anchors, args.context))
        occurrences.extend(search_external_refs(conn, export_id, anchors, args.context))
        occurrences.extend(
            search_digit_run_table(
                conn,
                export_id,
                "sheet__externalsourcedigithits_v472",
                "digitsrun",
                anchors,
                args.context,
                "external_source_hit",
            )
        )
        occurrences.extend(
            search_digit_run_table(
                conn,
                export_id,
                "sheet__externalrefcandidates_v472",
                "digitsrun",
                anchors,
                args.context,
                "external_ref_candidate",
            )
        )
        occurrences.extend(search_group_candidates(conn, export_id, anchors, args.context))
        summary = summarize(anchors, occurrences, export_id)
        run_id = record(conn, summary, occurrences) if args.record else None
    finally:
        conn.close()

    output = {
        **summary,
        "recorded_run_id": run_id,
        "occurrence_count": len(occurrences),
        "sample_occurrences": sorted_occurrences_for_output(occurrences, args.max_output_occurrences),
    }
    print(json.dumps(output, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
