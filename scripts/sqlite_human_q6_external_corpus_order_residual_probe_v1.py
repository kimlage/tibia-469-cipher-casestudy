#!/usr/bin/env python3
"""Q6 probe: external corpus order for remaining residual books, without gloss."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

SOURCE_URL = "https://linguagem469.wordpress.com/wp-content/uploads/2012/01/padrc3b5es469.pdf"
SOURCE_LABEL = "Padroes469 PDF, Livro | Original table"

EXTERNAL_ORDER = [
    {
        "project_bookid": "6",
        "external_book_no": 42,
        "line_ref": "PDF page 1 lines 73-75",
        "digits": "3046484353451586042157651595646190186559537243485625108145042159561513534780192889115191414519889971463646728577511216151800672431427894314454552160199364128191180035611472611",
        "role": "continuity/control residual",
    },
    {
        "project_bookid": "7",
        "external_book_no": 43,
        "line_ref": "PDF page 1 line 76",
        "digits": "8435345158675112167610625140815953478019288911519141451988997146364751352854215765159564619018655953724385",
        "role": "phase-continuity bridge residual",
    },
    {
        "project_bookid": "36",
        "external_book_no": 46,
        "line_ref": "PDF page 1 line 83",
        "digits": "84350819215956151367972783160134515860421585774454519045045347801928895216019979282753724348562510811463646724355460036145191211288830464",
        "role": "display-drift residual",
    },
    {
        "project_bookid": "32",
        "external_book_no": 53,
        "line_ref": "PDF page 1 line 98",
        "digits": "65180099673405792827843508195372434856251081146364672435546003614519121128883046467972783160134515860421585774454519045042159561513534780",
        "role": "display-drift residual",
    },
]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def load_json(value: str | bytes | None, fallback: object) -> object:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q6_external_corpus_order_residual_probe_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            source_url TEXT NOT NULL,
            target_count INTEGER NOT NULL,
            source_match_count INTEGER NOT NULL,
            adjacency_support_count INTEGER NOT NULL,
            display_separation_count INTEGER NOT NULL,
            promoted_plaintext_gloss_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q6_external_corpus_order_residual_probe_v1_items (
            run_id INTEGER NOT NULL,
            item_id TEXT NOT NULL,
            item_type TEXT NOT NULL,
            project_bookid TEXT NOT NULL,
            external_book_no INTEGER NOT NULL,
            status TEXT NOT NULL,
            role_label TEXT NOT NULL,
            support_class TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, item_id)
        );
        """
    )


def latest_id(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT max(run_id) FROM {table}").fetchone()
    if row is None or row[0] is None:
        raise RuntimeError(f"missing required run: {table}")
    return int(row[0])


def one(conn: sqlite3.Connection, sql: str, params: tuple[object, ...] = ()) -> sqlite3.Row | None:
    return conn.execute(sql, params).fetchone()


def item(
    item_id: str,
    item_type: str,
    project_bookid: str,
    external_book_no: int,
    status: str,
    role_label: str,
    support_class: str,
    evidence: object,
) -> dict[str, object]:
    return {
        "item_id": item_id,
        "item_type": item_type,
        "project_bookid": project_bookid,
        "external_book_no": external_book_no,
        "status": status,
        "role_label": role_label,
        "support_class": support_class,
        "evidence_json": j(evidence),
    }


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    remaining_run = latest_id(conn, "remaining_five_evidence_requirements_v1_items")
    q4_run = latest_id(conn, "human_q4_book7_phase_direction_probe_v1_runs")
    q5_run = latest_id(conn, "human_q5_book20_54_local_pair_context_probe_v1_runs")
    display_tail_run = latest_id(conn, "display_tail_masking_gate_v1_items")
    atlas_run = latest_id(conn, "human_translation_atlas_v6_items")

    items: list[dict[str, object]] = []
    source_match_count = 0

    for external in EXTERNAL_ORDER:
        bookid = external["project_bookid"]
        book_row = one(
            conn,
            """
            SELECT bookid, digits, decodedbase
            FROM sheet__books
            WHERE bookid=? AND digits=?
            LIMIT 1
            """,
            (bookid, external["digits"]),
        )
        row0 = one(
            conn,
            """
            SELECT bookid, symbol_text, token_count
            FROM row0_variant_book_tokens
            WHERE run_id=(SELECT max(run_id) FROM row0_variant_book_tokens)
              AND bookid=?
            """,
            (bookid,),
        )
        source_matched = book_row is not None
        source_match_count += int(source_matched)
        items.append(
            item(
                f"external-order:book:{bookid}",
                "external_order_match",
                bookid,
                int(external["external_book_no"]),
                "EXTERNAL_ORDER_MATCHED_PROJECT_BOOK" if source_matched else "EXTERNAL_ORDER_MISMATCH",
                str(external["role"]),
                "SUPPORT_EXTERNAL_CORPUS_ORDER_AUDIT_ONLY",
                {
                    "source_url": SOURCE_URL,
                    "source_label": SOURCE_LABEL,
                    "line_ref": external["line_ref"],
                    "external_book_no": external["external_book_no"],
                    "source_digits": external["digits"],
                    "project_sheet_row": dict(book_row) if book_row else None,
                    "row0": dict(row0) if row0 else None,
                },
            )
        )

    adjacency_support_count = 0
    if source_match_count == len(EXTERNAL_ORDER):
        book6_no = next(row["external_book_no"] for row in EXTERNAL_ORDER if row["project_bookid"] == "6")
        book7_no = next(row["external_book_no"] for row in EXTERNAL_ORDER if row["project_bookid"] == "7")
        adjacency_support_count = int(abs(book6_no - book7_no) == 1)
    items.append(
        item(
            "support:external-order:6-7-adjacent",
            "external_order_relation",
            "6,7",
            42,
            "BOOK6_7_EXTERNAL_CORPUS_ADJACENCY_SUPPORTED" if adjacency_support_count else "BOOK6_7_EXTERNAL_CORPUS_ADJACENCY_NOT_SUPPORTED",
            "Book6/Book7 continuity-to-phase relation has adjacent external corpus order",
            "SUPPORT_BOOK6_7_RELATION_AUDIT_ONLY",
            {
                "book6_external_no": 42,
                "book7_external_no": 43,
                "q4_run_id": q4_run,
                "allowed_inference": "External order can support using Book6 as immediate control for Book7.",
                "blocked_inference": "External order does not translate NEIAAETTA, TIINNEF, 3478, or either book.",
            },
        )
    )

    display_numbers = {
        row["project_bookid"]: int(row["external_book_no"])
        for row in EXTERNAL_ORDER
        if row["project_bookid"] in {"32", "36"}
    }
    display_separation_count = int(abs(display_numbers["32"] - display_numbers["36"]) > 1)
    items.append(
        item(
            "control:external-order:32-36-separated",
            "external_order_relation",
            "32,36",
            46,
            "DISPLAY_RESIDUALS_SEPARATED_IN_EXTERNAL_ORDER" if display_separation_count else "DISPLAY_RESIDUALS_ADJACENT_IN_EXTERNAL_ORDER",
            "Display-drift residuals do not gain a physical/order pair argument from this source",
            "CONTROL_DISPLAY_RESIDUAL_PAIR_OVERCLAIM",
            {
                "book36_external_no": display_numbers["36"],
                "book32_external_no": display_numbers["32"],
                "display_tail_run_id": display_tail_run,
                "allowed_inference": "Books32/36 remain display-tail controls unless independent payload emerges.",
                "blocked_inference": "Do not group Books32/36 as adjacent pair or prose by external order.",
            },
        )
    )

    for bookid in ("6", "7", "32", "36"):
        remaining = one(
            conn,
            """
            SELECT *
            FROM remaining_five_evidence_requirements_v1_items
            WHERE run_id=? AND bookid=?
            """,
            (remaining_run, bookid),
        )
        atlas = one(
            conn,
            """
            SELECT target_id, likely_speech_act, plausible_human_reading,
                   confidence_tier, promotion_status, blocked_claims_json, next_probe
            FROM human_translation_atlas_v6_items
            WHERE run_id=? AND target_id=?
            """,
            (atlas_run, bookid),
        )
        items.append(
            item(
                f"control:remaining-status:{bookid}",
                "remaining_status",
                bookid,
                next(row["external_book_no"] for row in EXTERNAL_ORDER if row["project_bookid"] == bookid),
                "REMAINS_NOT_PROMOTED_NO_GLOSS",
                "remaining-five blocker is not cleared by external order alone",
                "CONTROL_REMAINING_REQUIREMENTS_STILL_ACTIVE",
                {
                    "remaining_run_id": remaining_run,
                    "q5_run_id": q5_run,
                    "remaining": dict(remaining) if remaining else None,
                    "atlas": dict(atlas) if atlas else None,
                },
            )
        )

    promoted_plaintext_gloss_count = 0
    decision = (
        "Q6_EXTERNAL_ORDER_SUPPORTS_BOOK6_7_ADJACENCY_DISPLAY_RESIDUALS_HELD_NO_GLOSS"
        if source_match_count == len(EXTERNAL_ORDER)
        and adjacency_support_count == 1
        and display_separation_count == 1
        and promoted_plaintext_gloss_count == 0
        else "Q6_EXTERNAL_ORDER_REQUIRES_MANUAL_REVIEW"
    )

    payload = {
        "question": "Can external corpus order add an in-game/book-relation constraint to remaining residuals without translating them?",
        "answer": (
            "Yes for Book6/7 as an audit-only relation: the external PDF places the project Book6 text as Livro 42 "
            "and the project Book7 text as Livro 43, which supports treating Book6 as the immediate continuity control "
            "for Book7. No for Books32/36: they appear as Livro 53 and Livro 46, so external order does not add an "
            "adjacent-pair explanation to the display residuals."
        ),
        "allowed_reading": "Book6/7 external-order adjacency is a support/control relation only.",
        "blocked_reading": "No lexical gloss, plaintext sentence, or display-payload promotion is allowed from external order.",
        "source_url": SOURCE_URL,
        "source_label": SOURCE_LABEL,
        "external_order": EXTERNAL_ORDER,
        "next_probe": "Use the Book6/7 adjacency as a narrow row0 phase/path precheck; keep Books32/36 closed as display controls unless new payload evidence appears.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q6_external_corpus_order_residual_probe_v1_runs (
                created_at, decision, source_url, target_count, source_match_count,
                adjacency_support_count, display_separation_count,
                promoted_plaintext_gloss_count, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                SOURCE_URL,
                len(EXTERNAL_ORDER),
                source_match_count,
                adjacency_support_count,
                display_separation_count,
                promoted_plaintext_gloss_count,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q6_external_corpus_order_residual_probe_v1_items (
                run_id, item_id, item_type, project_bookid, external_book_no,
                status, role_label, support_class, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    str(row["item_id"]),
                    str(row["item_type"]),
                    str(row["project_bookid"]),
                    int(row["external_book_no"]),
                    str(row["status"]),
                    str(row["role_label"]),
                    str(row["support_class"]),
                    str(row["evidence_json"]),
                )
                for row in items
            ],
        )

    print(
        j(
            {
                "run_id": run_id,
                "decision": decision,
                "target_count": len(EXTERNAL_ORDER),
                "source_match_count": source_match_count,
                "adjacency_support_count": adjacency_support_count,
                "display_separation_count": display_separation_count,
                "promoted_plaintext_gloss_count": promoted_plaintext_gloss_count,
            }
        )
    )


if __name__ == "__main__":
    main()
