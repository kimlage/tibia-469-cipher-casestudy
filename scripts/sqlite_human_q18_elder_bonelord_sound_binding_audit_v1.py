#!/usr/bin/env python3
"""Q18 audit: Elder Bonelord numeric sounds versus semantic word binding."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

SOURCES = [
    {
        "source_id": "FANDOM_ELDER_BONELORD",
        "source_url": "https://tibia.fandom.com/wiki/Elder_Bonelord",
        "source_tier": "secondary_creature_page",
        "status": "LISTS_ENGLISH_AND_NUMERIC_CREATURE_SOUNDS",
        "sounds": ["Inferior creatures, bow before my power!", "Let me take a look at you!", "659978 54764!", "653768764!"],
        "risk": "lists creature sounds together, but does not assert word-by-word translation",
    },
    {
        "source_id": "TIBIAWIKI_BR_ELDER_BONELORD",
        "source_url": "https://www.tibiawiki.com.br/wiki/Elder_Bonelord",
        "source_tier": "secondary_creature_page",
        "status": "LISTS_ENGLISH_AND_NUMERIC_CREATURE_SOUNDS",
        "sounds": ["Inferior creatures, bow before my power!", "Let me take a look at you!", "659978 54764!", "653768764!"],
        "risk": "independent wiki attestation of sounds, not semantic binding",
    },
    {
        "source_id": "TIBIA_WIKI_NET_ELDER_BONELORD",
        "source_url": "https://www.tibia-wiki.net/wiki/Elder_Bonelord",
        "source_tier": "secondary_creature_page",
        "status": "LISTS_NUMERIC_CREATURE_SOUNDS_WITH_LIMITED_ENGLISH_CONTEXT",
        "sounds": ["Inferior creatures, bow before my power!", "659978 54764!", "653768764!"],
        "risk": "confirms numeric sounds but does not give translation",
    },
    {
        "source_id": "TIBIAQA_AVAR_TAR_THREAD",
        "source_url": "https://www.tibiaqa.com/25041/is-avar-tar-lying-about-his-stories",
        "source_tier": "community_lore_context",
        "status": "TREATS_ELDER_BONELORD_SOUNDS_AS_RELIABLE_469_SPEECH",
        "sounds": ["659978 54764!", "653768764!"],
        "risk": "community interpretation; not a source of explicit meaning",
    },
]

TARGET_SOUNDS = ["659978 54764", "653768764"]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q18_elder_bonelord_sound_binding_audit_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            source_count INTEGER NOT NULL,
            numeric_sound_attestation_count INTEGER NOT NULL,
            shared_creature_voice_context_count INTEGER NOT NULL,
            explicit_semantic_binding_count INTEGER NOT NULL,
            npc_phrase_quarantine_count INTEGER NOT NULL,
            rosetta_book_promotion_allowed_count INTEGER NOT NULL,
            promoted_plaintext_gloss_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q18_elder_bonelord_sound_binding_audit_v1_items (
            run_id INTEGER NOT NULL,
            item_id TEXT NOT NULL,
            item_type TEXT NOT NULL,
            source_table TEXT NOT NULL,
            source_key TEXT NOT NULL,
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


def rows(conn: sqlite3.Connection, sql: str, params: tuple[object, ...] = ()) -> list[sqlite3.Row]:
    return list(conn.execute(sql, params).fetchall())


def add_item(
    out: list[dict[str, object]],
    item_id: str,
    item_type: str,
    source_table: str,
    source_key: str,
    status: str,
    role_label: str,
    support_class: str,
    evidence: object,
) -> None:
    out.append(
        {
            "item_id": item_id,
            "item_type": item_type,
            "source_table": source_table,
            "source_key": source_key,
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

    open_target_run = latest_id(conn, "external_semantic_open_target_runs")
    npc_phrase_run = latest_id(conn, "npc_phrase_anchors")
    rosetta_run = latest_id(conn, "rosetta_anchor_projection_items")

    open_target = conn.execute(
        """
        SELECT *
        FROM external_semantic_open_targets
        WHERE run_id=? AND target_id='ELDER_BONELORD_SOUNDS'
        """,
        (open_target_run,),
    ).fetchone()
    elder_phrases = rows(
        conn,
        """
        SELECT *
        FROM npc_phrase_anchors
        WHERE run_id=? AND phrase_id IN ('NPC-Elder1-65997854764', 'NPC-Elder2-653768764')
        ORDER BY phrase_id
        """,
        (npc_phrase_run,),
    )
    elder_rosetta = rows(
        conn,
        """
        SELECT *
        FROM rosetta_anchor_projection_items
        WHERE run_id=? AND anchor_id IN ('RDW-54-see', 'RDW-653-look', 'RDW-659-let', 'RDW-764-you-a', 'RDW-764-you-b', 'RDW-768-at', 'RDW-978-me')
        ORDER BY anchor_id
        """,
        (rosetta_run,),
    )

    items: list[dict[str, object]] = []
    for source in SOURCES:
        has_all_numeric = all(any(sound in entry for entry in source["sounds"]) for sound in TARGET_SOUNDS)
        add_item(
            items,
            f"source:{source['source_id']}",
            "source_sound_attestation",
            "web_source_audit",
            str(source["source_url"]),
            str(source["status"]),
            "Elder Bonelord numeric sounds are attested as creature/NPC voice lines.",
            "SUPPORT_NUMERIC_SOUND_ATTESTATION_NO_TRANSLATION" if has_all_numeric else "SUPPORT_PARTIAL_SOUND_ATTESTATION_NO_TRANSLATION",
            source,
        )

    add_item(
        items,
        "target:elder-bonelord-open-target",
        "external_open_target",
        "external_semantic_open_targets",
        f"run={open_target_run}:ELDER_BONELORD_SOUNDS",
        str(open_target["current_status"]) if open_target else "MISSING_OPEN_TARGET",
        "Open target requires explicit source binding numeric shouts to English meaning.",
        "CONTROL_TARGET_REMAINS_OPEN",
        dict(open_target) if open_target else {"missing": True},
    )

    for row in elder_phrases:
        add_item(
            items,
            f"npc-phrase:{row['phrase_id']}",
            "npc_phrase_quarantine",
            "npc_phrase_anchors",
            f"run={npc_phrase_run}:{row['phrase_id']}",
            str(row["promotion_status"]),
            "Existing NPC phrase anchor is external-only and cannot promote book semantics.",
            "CONTROL_NPC_PHRASE_QUARANTINED_NO_BOOK_GLOSS",
            dict(row),
        )

    for row in elder_rosetta:
        add_item(
            items,
            f"rosetta:{row['anchor_id']}",
            "rosetta_projection_control",
            "rosetta_anchor_projection_items",
            f"run={rosetta_run}:{row['anchor_id']}",
            str(row["projection_status"]),
            "Existing wordcode projection remains external/quarantined or out-of-corpus.",
            "CONTROL_ROSETTA_WORDCODE_NO_BOOK_PROMOTION",
            dict(row),
        )

    source_count = len(SOURCES)
    numeric_sound_attestation_count = sum(
        1
        for source in SOURCES
        if all(any(sound in entry for entry in source["sounds"]) for sound in TARGET_SOUNDS)
    )
    shared_creature_voice_context_count = sum(
        1
        for source in SOURCES
        if any("Let me take a look at you!" == entry for entry in source["sounds"])
        and any("653768764!" == entry for entry in source["sounds"])
    )
    explicit_semantic_binding_count = 0
    npc_phrase_quarantine_count = sum(
        1
        for row in elder_phrases
        if str(row["scope"]) == "external_npc_only"
        and str(row["promotion_status"]) in {"SOFT_QUARANTINE", "ACTIVE_QUARANTINE", "HOLDOUT_NO_PROMOTION"}
        and int(row["contaminates_books"]) == 0
    )
    rosetta_book_promotion_allowed_count = sum(int(row["book_promotion_allowed"]) for row in elder_rosetta)
    promoted_plaintext_gloss_count = 0

    decision = (
        "Q18_ELDER_BONELORD_SOUNDS_ATTESTED_NO_SEMANTIC_BINDING_KEEP_NPC_QUARANTINE_NO_GLOSS"
        if source_count >= 4
        and numeric_sound_attestation_count >= 3
        and shared_creature_voice_context_count >= 2
        and explicit_semantic_binding_count == 0
        and npc_phrase_quarantine_count >= 2
        and rosetta_book_promotion_allowed_count == 0
        and promoted_plaintext_gloss_count == 0
        else "Q18_ELDER_BONELORD_SOUND_BINDING_REQUIRES_MANUAL_REVIEW"
    )

    payload = {
        "question": "Do Elder Bonelord sounds provide explicit semantic binding for 659978/54764/653/768/764?",
        "answer": (
            "No. Multiple sources attest the numeric sounds as Elder Bonelord voice lines, and some pages place them near English creature sounds, "
            "but none provides an explicit one-to-one semantic binding. Existing NPC and rosetta layers therefore remain quarantined."
        ),
        "allowed_reading": "Use Elder Bonelord sounds as reliable external/in-game speech holdouts and register evidence.",
        "blocked_reading": "Do not promote 653=look, 768=at, 764=you, 659=let, 978=me, or 54=see into book glosses from these sources.",
        "next_probe": "Search primary creature data or historical official fan-wiki history for explicit semantic binding; otherwise keep as speech register only.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q18_elder_bonelord_sound_binding_audit_v1_runs (
                created_at, decision, source_count,
                numeric_sound_attestation_count, shared_creature_voice_context_count,
                explicit_semantic_binding_count, npc_phrase_quarantine_count,
                rosetta_book_promotion_allowed_count, promoted_plaintext_gloss_count,
                payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                source_count,
                numeric_sound_attestation_count,
                shared_creature_voice_context_count,
                explicit_semantic_binding_count,
                npc_phrase_quarantine_count,
                rosetta_book_promotion_allowed_count,
                promoted_plaintext_gloss_count,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q18_elder_bonelord_sound_binding_audit_v1_items (
                run_id, item_id, item_type, source_table, source_key, status,
                role_label, support_class, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    str(row["item_id"]),
                    str(row["item_type"]),
                    str(row["source_table"]),
                    str(row["source_key"]),
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
                "source_count": source_count,
                "numeric_sound_attestation_count": numeric_sound_attestation_count,
                "shared_creature_voice_context_count": shared_creature_voice_context_count,
                "explicit_semantic_binding_count": explicit_semantic_binding_count,
                "npc_phrase_quarantine_count": npc_phrase_quarantine_count,
                "rosetta_book_promotion_allowed_count": rosetta_book_promotion_allowed_count,
                "promoted_plaintext_gloss_count": promoted_plaintext_gloss_count,
            }
        )
    )


if __name__ == "__main__":
    main()
