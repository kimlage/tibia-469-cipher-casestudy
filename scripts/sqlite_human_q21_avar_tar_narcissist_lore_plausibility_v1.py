#!/usr/bin/env python3
"""Q21: test whether the Avar VAIN->NARCISSIST slot is plausible as character lore."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

EXPECTED_Q20_DECISION = (
    "Q20_AVAR_VARIANT_SLOT_REPLACEMENT_CONFIRMS_PRIMARY_NARCISSIST_MICROANCHOR_NO_BOOK_GLOSS"
)

SOURCES = [
    {
        "source_id": "tibia_fandom_avar_transcript",
        "url": "https://tibia.fandom.com/wiki/Avar_Tar/Transcripts",
        "source_type": "in_game_transcript",
        "status": "TRANSCRIPT_CONTEXT_CONFIRMED",
        "role_label": "Avar Tar direct transcript links self-glorifying persona with the Bonelord language poem.",
        "support_class": "SUPPORT_PERSONA_AND_POEM_CONTEXT",
        "self_aggrandizing_hits": [
            "slayer of monsters",
            "saviour of princesses",
            "greatest hero in Tibia",
            "seen it all and done it all",
            "Demons know and fear my name",
        ],
        "bonelord_language_hits": [
            "Avar Tar gives the numeric poem when asked about bonelord language."
        ],
        "explicit_semantic_binding_hits": [],
    },
    {
        "source_id": "tibiasecrets_avar_transcript",
        "url": "https://tibiasecrets.com/Avar-Tar",
        "source_type": "transcript_mirror",
        "status": "TRANSCRIPT_MIRROR_CONFIRMS_CONTEXT",
        "role_label": "Independent transcript mirror repeats the same boastful register and the same poem slot.",
        "support_class": "SUPPORT_TRANSCRIPT_MIRROR",
        "self_aggrandizing_hits": [
            "hero like me",
            "greatest hero in Tibia",
            "slayer of monsters",
            "saviour of princesses",
            "seen it all and done it all",
        ],
        "bonelord_language_hits": [
            "Mirror records the same original poem with 63378129 at slot 11."
        ],
        "explicit_semantic_binding_hits": [],
    },
    {
        "source_id": "tibiaqa_avar_reliability_discussion",
        "url": "https://www.tibiaqa.com/25041/is-avar-tar-lying-about-his-stories",
        "source_type": "community_lore_audit",
        "status": "COMMUNITY_DISCUSSION_IDENTIFIES_AVAR_RELIABILITY_AND_VARIANT_SLOT",
        "role_label": "Community audit frames Avar Tar as unreliable and records the old-web variant slot replacement.",
        "support_class": "SUPPORT_RELIABILITY_CONTEXT_AND_VARIANT_DISCUSSION",
        "self_aggrandizing_hits": [
            "discussion argues his stories are exaggerated or unreliable",
        ],
        "bonelord_language_hits": [
            "discussion compares Avar Tar poem to reliable 469 examples",
            "discussion records 62792068657272657261 replacing 63378129",
        ],
        "explicit_semantic_binding_hits": [],
    },
]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q21_avar_tar_narcissist_lore_plausibility_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q20_run_id INTEGER NOT NULL,
            lore_source_count INTEGER NOT NULL,
            self_aggrandizing_context_count INTEGER NOT NULL,
            bonelord_language_context_count INTEGER NOT NULL,
            explicit_semantic_binding_count INTEGER NOT NULL,
            character_slot_plausibility_count INTEGER NOT NULL,
            book_promotion_allowed_count INTEGER NOT NULL,
            promoted_plaintext_gloss_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q21_avar_tar_narcissist_lore_plausibility_v1_items (
            run_id INTEGER NOT NULL,
            item_id TEXT NOT NULL,
            source_type TEXT NOT NULL,
            status TEXT NOT NULL,
            role_label TEXT NOT NULL,
            support_class TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, item_id)
        );
        """
    )


def latest_q20(conn: sqlite3.Connection) -> sqlite3.Row:
    row = conn.execute(
        """
        SELECT *
        FROM human_q20_avar_variant_slot_microanchor_audit_v1_runs
        ORDER BY run_id DESC
        LIMIT 1
        """
    ).fetchone()
    if row is None:
        raise RuntimeError("missing Q20 run; run sqlite_human_q20_avar_variant_slot_microanchor_audit_v1.py first")
    return row


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q20 = latest_q20(conn)
    q20_ok = str(q20["decision"]) == EXPECTED_Q20_DECISION
    q20_slot_ok = (
        int(q20["replacement_slot_index"]) == 11
        and int(q20["unchanged_word_count"]) == 19
        and int(q20["original_slot_decode_match_count"]) == 1
        and int(q20["variant_slot_decode_match_count"]) == 1
        and int(q20["book_promotion_allowed_count"]) == 0
        and int(q20["promoted_plaintext_gloss_count"]) == 0
    )

    lore_source_count = len(SOURCES)
    self_aggrandizing_context_count = sum(
        1 for source in SOURCES if source["self_aggrandizing_hits"]
    )
    bonelord_language_context_count = sum(
        1 for source in SOURCES if source["bonelord_language_hits"]
    )
    explicit_semantic_binding_count = sum(
        len(source["explicit_semantic_binding_hits"]) for source in SOURCES
    )
    character_slot_plausibility_count = int(
        q20_ok
        and q20_slot_ok
        and self_aggrandizing_context_count >= 2
        and bonelord_language_context_count >= 2
        and explicit_semantic_binding_count == 0
    )
    book_promotion_allowed_count = 0
    promoted_plaintext_gloss_count = 0

    items = [
        {
            "item_id": f"source:{source['source_id']}",
            "source_type": source["source_type"],
            "status": source["status"],
            "role_label": source["role_label"],
            "support_class": source["support_class"],
            "evidence_json": j(source),
        }
        for source in SOURCES
    ]
    items.append(
        {
            "item_id": "control:q20-slot-delta",
            "source_type": "sqlite_prior_run",
            "status": "Q20_SLOT_DELTA_USABLE_AS_CONTEXT" if q20_ok and q20_slot_ok else "Q20_SLOT_DELTA_NOT_READY",
            "role_label": "Q20 supplies the single-slot VAIN to NARCISSIST replacement scaffold.",
            "support_class": "SUPPORT_EXTERNAL_MICROANCHOR_CONTEXT",
            "evidence_json": j(dict(q20)),
        }
    )
    items.append(
        {
            "item_id": "control:no-semantic-promotion",
            "source_type": "promotion_control",
            "status": "NO_EXPLICIT_SOURCE_BINDING_NO_BOOK_GLOSS",
            "role_label": "The lore context explains why the slot may be intentional, not what any book sentence means.",
            "support_class": "CONTROL_NO_BOOK_GLOSS",
            "evidence_json": j(
                {
                    "explicit_semantic_binding_count": explicit_semantic_binding_count,
                    "book_promotion_allowed_count": book_promotion_allowed_count,
                    "promoted_plaintext_gloss_count": promoted_plaintext_gloss_count,
                }
            ),
        }
    )

    decision = (
        "Q21_AVAR_TAR_NARCISSIST_LORE_PLAUSIBLE_CHARACTER_SLOT_NO_BOOK_GLOSS"
        if character_slot_plausibility_count == 1
        and book_promotion_allowed_count == 0
        and promoted_plaintext_gloss_count == 0
        else "Q21_AVAR_TAR_NARCISSIST_LORE_REQUIRES_MANUAL_REVIEW"
    )
    payload = {
        "question": "Does the Q20 VAIN->NARCISSIST slot make human/lore sense for Avar Tar?",
        "answer": (
            "Yes, as a character/register hypothesis only. Avar Tar's transcript repeatedly frames him as boastful, "
            "so replacing VAIN with NARCISSIST in the same external phrase slot is plausible as a persona or joke "
            "signal. No source explicitly binds the number to that English meaning, and no book gloss is promoted."
        ),
        "allowed_reading": (
            "Use Avar Tar as a human shadow persona/register comparator and as a target for further source search."
        ),
        "blocked_reading": (
            "Do not treat this as a solved Avar poem, a promoted NARCISSIST lexeme, or Hellgate book plaintext."
        ),
        "next_action": (
            "Search for other in-game/editorial variants where a 469 phrase is modified in a semantically themed context."
        ),
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q21_avar_tar_narcissist_lore_plausibility_v1_runs (
                created_at, decision, q20_run_id, lore_source_count,
                self_aggrandizing_context_count, bonelord_language_context_count,
                explicit_semantic_binding_count, character_slot_plausibility_count,
                book_promotion_allowed_count, promoted_plaintext_gloss_count,
                payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                int(q20["run_id"]),
                lore_source_count,
                self_aggrandizing_context_count,
                bonelord_language_context_count,
                explicit_semantic_binding_count,
                character_slot_plausibility_count,
                book_promotion_allowed_count,
                promoted_plaintext_gloss_count,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q21_avar_tar_narcissist_lore_plausibility_v1_items (
                run_id, item_id, source_type, status, role_label, support_class,
                evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    str(row["item_id"]),
                    str(row["source_type"]),
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
                "q20_run_id": int(q20["run_id"]),
                "lore_source_count": lore_source_count,
                "self_aggrandizing_context_count": self_aggrandizing_context_count,
                "bonelord_language_context_count": bonelord_language_context_count,
                "explicit_semantic_binding_count": explicit_semantic_binding_count,
                "character_slot_plausibility_count": character_slot_plausibility_count,
                "book_promotion_allowed_count": book_promotion_allowed_count,
                "promoted_plaintext_gloss_count": promoted_plaintext_gloss_count,
            }
        )
    )


if __name__ == "__main__":
    main()
