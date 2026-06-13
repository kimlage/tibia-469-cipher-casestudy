#!/usr/bin/env python3
"""Q20: compare original Avar Tar poem with Tibia.org variant at the replacement slot."""

from __future__ import annotations

import datetime as dt
import json
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

ORIGINAL_WORD = "63378129"
VARIANT_WORD = "62792068657272657261"
EXPECTED_ORIGINAL_DECODE = "VAIN"
EXPECTED_VARIANT_DECODE = "NARCISSIST"

ORIGINAL_WORDS = [
    "29639",
    "46781",
    "9063376290",
    "3222011",
    "677",
    "80322429",
    "67538",
    "14805394",
    "6880326",
    "677",
    ORIGINAL_WORD,
    "337011",
    "72683",
    "149630",
    "4378",
    "453",
    "639",
    "578300",
    "986372",
    "2953639",
]
VARIANT_WORDS = [
    "29639",
    "46781",
    "9063376290",
    "3222011",
    "677",
    "80322429",
    "67538",
    "14805394",
    "6880326",
    "677",
    VARIANT_WORD,
    "337011",
    "72683",
    "149630",
    "4378",
    "453",
    "639",
    "578300",
    "986372",
    "2953639",
]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def pairs(raw: str) -> list[str]:
    digits = re.sub(r"\D", "", raw)
    if len(digits) % 2:
        digits = "0" + digits
    return [digits[i : i + 2] for i in range(0, len(digits), 2)]


def decode_word(raw: str, mapping: dict[str, str]) -> str:
    return "".join(mapping.get(pair, "?") for pair in pairs(raw))


def decode_words(words: list[str], mapping: dict[str, str]) -> list[str]:
    return [decode_word(word, mapping) for word in words]


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q20_avar_variant_slot_microanchor_audit_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q19_run_id INTEGER NOT NULL,
            replacement_slot_index INTEGER NOT NULL,
            unchanged_word_count INTEGER NOT NULL,
            original_slot_decode_match_count INTEGER NOT NULL,
            variant_slot_decode_match_count INTEGER NOT NULL,
            primary_archive_sequence_confirmed_count INTEGER NOT NULL,
            external_micro_anchor_count INTEGER NOT NULL,
            book_promotion_allowed_count INTEGER NOT NULL,
            promoted_plaintext_gloss_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q20_avar_variant_slot_microanchor_audit_v1_items (
            run_id INTEGER NOT NULL,
            item_id TEXT NOT NULL,
            item_type TEXT NOT NULL,
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


def add_item(
    out: list[dict[str, object]],
    item_id: str,
    item_type: str,
    status: str,
    role_label: str,
    support_class: str,
    evidence: object,
) -> None:
    out.append(
        {
            "item_id": item_id,
            "item_type": item_type,
            "status": status,
            "role_label": role_label,
            "support_class": support_class,
            "evidence_json": j(evidence),
        }
    )


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q19_run_id = latest_id(conn, "human_q19_tibia_org_avar_variant_wayback_confirmation_v1_runs")
    q19 = conn.execute(
        "SELECT * FROM human_q19_tibia_org_avar_variant_wayback_confirmation_v1_runs WHERE run_id=?",
        (q19_run_id,),
    ).fetchone()
    micro_run_id = latest_id(conn, "narcissist_micro_anchor_runs")
    micro = conn.execute(
        "SELECT * FROM narcissist_micro_anchor_runs WHERE run_id=?",
        (micro_run_id,),
    ).fetchone()
    original_projection = conn.execute(
        """
        SELECT *
        FROM confirmed_external_row0_projection_items
        WHERE run_id=(SELECT max(run_id) FROM confirmed_external_row0_projection_items)
          AND phrase_id='AVAR_ORIGINAL_POEM'
        """,
    ).fetchone()

    mapping = {
        str(row["code"]): str(row["symbol"])
        for row in conn.execute(
            """
            SELECT code, symbol
            FROM row0_code_symbol_counts
            WHERE run_id=(SELECT max(run_id) FROM row0_code_symbol_counts)
            """
        )
    }
    original_decoded = decode_words(ORIGINAL_WORDS, mapping)
    variant_decoded = decode_words(VARIANT_WORDS, mapping)

    differing_slots = [
        index
        for index, (left, right) in enumerate(zip(ORIGINAL_WORDS, VARIANT_WORDS), start=1)
        if left != right
    ]
    replacement_slot_index = differing_slots[0] if len(differing_slots) == 1 else -1
    unchanged_word_count = sum(1 for left, right in zip(ORIGINAL_WORDS, VARIANT_WORDS) if left == right)
    original_slot_decode = decode_word(ORIGINAL_WORD, mapping)
    variant_slot_decode = decode_word(VARIANT_WORD, mapping)
    original_slot_decode_match_count = int(original_slot_decode == EXPECTED_ORIGINAL_DECODE)
    variant_slot_decode_match_count = int(variant_slot_decode == EXPECTED_VARIANT_DECODE)
    primary_archive_sequence_confirmed_count = int(
        q19 is not None and int(q19["wayback_full_variant_hit_count"]) == 1
    )
    external_micro_anchor_count = int(
        micro is not None
        and str(micro["decoded_by_row0"]) == EXPECTED_VARIANT_DECODE
        and int(micro["exact_match"]) == 1
    )
    book_promotion_allowed_count = 0
    promoted_plaintext_gloss_count = 0

    items: list[dict[str, object]] = []
    add_item(
        items,
        "delta:single-slot-replacement",
        "slot_delta",
        "SINGLE_REPLACEMENT_SLOT_CONFIRMED" if replacement_slot_index > 0 else "REPLACEMENT_SLOT_AMBIGUOUS",
        "Original Avar poem and Tibia.org variant differ only at one word slot.",
        "SUPPORT_PHRASE_SLOT_REPLACEMENT",
        {
            "replacement_slot_index": replacement_slot_index,
            "original_word": ORIGINAL_WORD,
            "variant_word": VARIANT_WORD,
            "unchanged_word_count": unchanged_word_count,
            "original_words": ORIGINAL_WORDS,
            "variant_words": VARIANT_WORDS,
        },
    )
    add_item(
        items,
        "decode:original-slot",
        "row0_slot_decode",
        "ORIGINAL_SLOT_DECODES_TO_VAIN" if original_slot_decode_match_count else "ORIGINAL_SLOT_DECODE_MISMATCH",
        "Original Avar word at the replacement slot decodes under row0 as VAIN.",
        "SUPPORT_ORIGINAL_SLOT_ROW0_DECODE",
        {"word": ORIGINAL_WORD, "pairs": pairs(ORIGINAL_WORD), "decoded": original_slot_decode},
    )
    add_item(
        items,
        "decode:variant-slot",
        "row0_slot_decode",
        "VARIANT_SLOT_DECODES_TO_NARCISSIST" if variant_slot_decode_match_count else "VARIANT_SLOT_DECODE_MISMATCH",
        "Tibia.org replacement word decodes under row0 as NARCISSIST.",
        "SUPPORT_PRIMARY_VARIANT_MICROANCHOR",
        {"word": VARIANT_WORD, "pairs": pairs(VARIANT_WORD), "decoded": variant_slot_decode, "micro_anchor": dict(micro) if micro else None},
    )
    add_item(
        items,
        "control:q19-primary-archive",
        "primary_archive_control",
        str(q19["decision"]) if q19 else "MISSING_Q19",
        "Q19 confirms the Avar variant sequence in a primary archived Tibia.org HTML comment.",
        "SUPPORT_PRIMARY_ARCHIVE_SEQUENCE_CONTEXT",
        dict(q19) if q19 else {"missing": True},
    )
    add_item(
        items,
        "control:no-book-promotion",
        "promotion_control",
        "MICROANCHOR_EXTERNAL_ONLY_NO_BOOK_PROMOTION",
        "Slot-level evidence is external phrase scaffolding and not Hellgate book prose.",
        "CONTROL_NO_BOOK_GLOSS",
        {
            "original_projection": dict(original_projection) if original_projection else None,
            "original_decoded_words": original_decoded,
            "variant_decoded_words": variant_decoded,
        },
    )

    decision = (
        "Q20_AVAR_VARIANT_SLOT_REPLACEMENT_CONFIRMS_PRIMARY_NARCISSIST_MICROANCHOR_NO_BOOK_GLOSS"
        if replacement_slot_index == 11
        and unchanged_word_count == 19
        and original_slot_decode_match_count == 1
        and variant_slot_decode_match_count == 1
        and primary_archive_sequence_confirmed_count == 1
        and external_micro_anchor_count == 1
        and book_promotion_allowed_count == 0
        and promoted_plaintext_gloss_count == 0
        else "Q20_AVAR_VARIANT_SLOT_MICROANCHOR_REQUIRES_MANUAL_REVIEW"
    )

    payload = {
        "question": "What does the Tibia.org Avar variant change relative to the original Avar Tar poem?",
        "answer": (
            "It changes one word slot: the original row0 projection has VAIN, while the archived Tibia.org variant has NARCISSIST. "
            "This is a strong external micro-anchor and phrase-slot scaffold, not a book translation."
        ),
        "allowed_reading": "Use NARCISSIST as a primary archived external micro-anchor and compare phrase slots.",
        "blocked_reading": "Do not promote the full Avar poem, NARCISSISM alternative, or any Hellgate book prose from this alone.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q20_avar_variant_slot_microanchor_audit_v1_runs (
                created_at, decision, q19_run_id, replacement_slot_index,
                unchanged_word_count, original_slot_decode_match_count,
                variant_slot_decode_match_count, primary_archive_sequence_confirmed_count,
                external_micro_anchor_count, book_promotion_allowed_count,
                promoted_plaintext_gloss_count, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                q19_run_id,
                replacement_slot_index,
                unchanged_word_count,
                original_slot_decode_match_count,
                variant_slot_decode_match_count,
                primary_archive_sequence_confirmed_count,
                external_micro_anchor_count,
                book_promotion_allowed_count,
                promoted_plaintext_gloss_count,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q20_avar_variant_slot_microanchor_audit_v1_items (
                run_id, item_id, item_type, status, role_label, support_class,
                evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    str(row["item_id"]),
                    str(row["item_type"]),
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
                "q19_run_id": q19_run_id,
                "replacement_slot_index": replacement_slot_index,
                "unchanged_word_count": unchanged_word_count,
                "original_slot_decode": original_slot_decode,
                "variant_slot_decode": variant_slot_decode,
                "primary_archive_sequence_confirmed_count": primary_archive_sequence_confirmed_count,
                "external_micro_anchor_count": external_micro_anchor_count,
                "book_promotion_allowed_count": book_promotion_allowed_count,
                "promoted_plaintext_gloss_count": promoted_plaintext_gloss_count,
            }
        )
    )


if __name__ == "__main__":
    main()
