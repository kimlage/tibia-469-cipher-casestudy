#!/usr/bin/env python3
"""Q13 probe: source ladder and row0 projection for Bonelord Tome 3478/486486 route."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

SOURCE_LADDER = [
    {
        "source_id": "OFFICIAL_TIBIA_SEARCH",
        "source_url": "https://www.tibia.com/",
        "source_tier": "official_search_negative",
        "status": "NO_DIRECT_TIBIA_COM_BONELORD_TOME_SOUND_SOURCE_FOUND",
        "role_label": "No direct official tibia.com source for Bonelord Tome sounds was found in current web search.",
        "allowed_inference": "Keep official/client verification as an open requirement.",
        "blocked_inference": "Do not treat wiki sound text as official primary-source verification.",
    },
    {
        "source_id": "TIBIASECRETS_BONELORD_TOME_HISTORY",
        "source_url": "https://tibiasecrets.com/bonelord_tome",
        "source_tier": "fansite_primary_history",
        "status": "FANSITE_HISTORY_CONFIRMS_ITEM_CONCEPT_469_TOME",
        "role_label": "TibiaSecrets history says the Bonelord Tome concept arose from 469 and Tibia lore/tomes.",
        "allowed_inference": "Use as source-context evidence for why the item belongs in the 469 route.",
        "blocked_inference": "Does not independently verify in-client sounds or any translation.",
    },
    {
        "source_id": "FANDOM_BONELORD_TOME_ITEM",
        "source_url": "https://tibia.fandom.com/wiki/Bonelord_Tome",
        "source_tier": "secondary_item_page",
        "status": "SECONDARY_ITEM_PAGE_LISTS_3478_AND_486486_SOUNDS",
        "role_label": "Fandom item page lists the Knightmare 3478 phrase and 486486 answer/attention line as item sounds.",
        "allowed_inference": "Use as secondary sound attestation pending client verification.",
        "blocked_inference": "Does not promote component gloss.",
    },
    {
        "source_id": "TIBIAWIKI_BR_BONELORD_TOME_ITEM",
        "source_url": "https://www.tibiawiki.com.br/wiki/Bonelord_Tome",
        "source_tier": "secondary_item_page",
        "status": "SECONDARY_ITEM_PAGE_LISTS_3478_AND_486486_SOUNDS",
        "role_label": "TibiaWiki BR lists the same sounds and marks the item as official TibiaSecrets fansite item.",
        "allowed_inference": "Use as independent secondary confirmation of item/sound context.",
        "blocked_inference": "Does not promote component gloss.",
    },
    {
        "source_id": "FANDOM_FAD_2022",
        "source_url": "https://tibia.fandom.com/wiki/Fansite_Appreciation_Day_2022",
        "source_tier": "secondary_event_page",
        "status": "SECONDARY_EVENT_PAGE_LISTS_TIBIASECRETS_BONELORD_TOME",
        "role_label": "FAD 2022 page lists TibiaSecrets | Bonelord Tome as a fansite item lottery entry.",
        "allowed_inference": "Supports official fansite-item context at event level.",
        "blocked_inference": "Does not attest sounds or semantics.",
    },
]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q13_bonelord_tome_source_ladder_projection_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            source_ladder_count INTEGER NOT NULL,
            direct_official_sound_source_count INTEGER NOT NULL,
            secondary_sound_source_count INTEGER NOT NULL,
            fansite_history_source_count INTEGER NOT NULL,
            event_context_source_count INTEGER NOT NULL,
            knightmare_out_of_book_projection_count INTEGER NOT NULL,
            awb_486486_entity_quarantine_count INTEGER NOT NULL,
            client_verification_required_count INTEGER NOT NULL,
            promoted_plaintext_gloss_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q13_bonelord_tome_source_ladder_projection_v1_items (
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


def one(conn: sqlite3.Connection, sql: str, params: tuple[object, ...] = ()) -> sqlite3.Row | None:
    return conn.execute(sql, params).fetchone()


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

    q12_run = latest_id(conn, "human_q12_bonelord_tome_3478_486486_anchor_probe_v1_runs")
    projection_run = latest_id(conn, "confirmed_external_row0_projection_items")
    npc_phrase_run = latest_id(conn, "npc_phrase_anchors")
    ingame_run = latest_id(conn, "human_ingame_anchor_corpus_v1_items")
    rosetta_run = latest_id(conn, "rosetta_anchor_projection_items")

    q12 = one(
        conn,
        "SELECT * FROM human_q12_bonelord_tome_3478_486486_anchor_probe_v1_runs WHERE run_id=?",
        (q12_run,),
    )
    knightmare_projection = one(
        conn,
        """
        SELECT *
        FROM confirmed_external_row0_projection_items
        WHERE run_id=? AND phrase_id='KNIGHTMARE_PHRASE'
        """,
        (projection_run,),
    )
    awb_phrase = one(
        conn,
        """
        SELECT *
        FROM npc_phrase_anchors
        WHERE run_id=? AND phrase_id='NPC-AWB-ID'
        """,
        (npc_phrase_run,),
    )
    awb_ingame = one(
        conn,
        """
        SELECT *
        FROM human_ingame_anchor_corpus_v1_items
        WHERE run_id=? AND anchor_id='AWB_SELF_NAME_486486'
        """,
        (ingame_run,),
    )
    knightmare_ingame = one(
        conn,
        """
        SELECT *
        FROM human_ingame_anchor_corpus_v1_items
        WHERE run_id=? AND anchor_id='KNIGHTMARE_3478_PHRASE'
        """,
        (ingame_run,),
    )
    rosetta_486 = one(
        conn,
        """
        SELECT *
        FROM rosetta_anchor_projection_items
        WHERE run_id=? AND digits='486486'
        """,
        (rosetta_run,),
    )

    items: list[dict[str, object]] = []

    for source in SOURCE_LADDER:
        tier = source["source_tier"]
        if tier == "official_search_negative":
            support_class = "CONTROL_NO_DIRECT_OFFICIAL_SOUND_SOURCE_FOUND"
        elif tier == "secondary_item_page":
            support_class = "SUPPORT_SECONDARY_SOUND_ATTESTATION_PENDING_CLIENT_VERIFICATION"
        elif tier == "fansite_primary_history":
            support_class = "SUPPORT_FANSITE_HISTORY_CONTEXT_NOT_SOUND_VERIFICATION"
        else:
            support_class = "SUPPORT_EVENT_CONTEXT_NOT_SOUND_VERIFICATION"
        add_item(
            items,
            f"source:{source['source_id']}",
            "source_ladder",
            "web_source_audit",
            str(source["source_url"]),
            str(source["status"]),
            str(source["role_label"]),
            support_class,
            source,
        )

    add_item(
        items,
        "prior:q12-colocation",
        "prior_anchor_probe",
        "human_q12_bonelord_tome_3478_486486_anchor_probe_v1_runs",
        f"run={q12_run}",
        str(q12["decision"]) if q12 else "MISSING_Q12",
        "Q12 co-location anchor remains active but no-gloss",
        "SUPPORT_Q12_COLOCATION_NO_GLOSS",
        dict(q12) if q12 else {"missing": True},
    )

    add_item(
        items,
        "projection:knightmare-row0",
        "row0_projection_control",
        "confirmed_external_row0_projection_items",
        f"run={projection_run}:KNIGHTMARE_PHRASE",
        str(knightmare_projection["projection_status"]) if knightmare_projection else "MISSING_KNIGHTMARE_PROJECTION",
        "Knightmare 3478 phrase projects to row0 as external/out-of-book, not book text",
        "CONTROL_KNIGHTMARE_OUT_OF_BOOK_NO_BOOK_PROMOTION",
        dict(knightmare_projection) if knightmare_projection else {"missing": True},
    )

    add_item(
        items,
        "anchor:awb-486486-phrase",
        "npc_phrase_anchor",
        "npc_phrase_anchors",
        f"run={npc_phrase_run}:NPC-AWB-ID",
        str(awb_phrase["promotion_status"]) if awb_phrase else "MISSING_AWB_PHRASE",
        "486486 remains entity/identifier quarantine with no book contamination",
        "SUPPORT_486486_ENTITY_QUARANTINE_NO_BOOK_DECODER",
        dict(awb_phrase) if awb_phrase else {"missing": True},
    )
    add_item(
        items,
        "anchor:awb-486486-ingame",
        "ingame_anchor",
        "human_ingame_anchor_corpus_v1_items",
        f"run={ingame_run}:AWB_SELF_NAME_486486",
        str(awb_ingame["promotion_status"]) if awb_ingame else "MISSING_AWB_INGAME",
        "A Wrinkled Bonelord 486486 anchor remains scoped lore only",
        "SUPPORT_486486_SCOPED_LORE_NO_BOOK_GLOSS",
        dict(awb_ingame) if awb_ingame else {"missing": True},
    )
    add_item(
        items,
        "anchor:knightmare-ingame",
        "ingame_anchor",
        "human_ingame_anchor_corpus_v1_items",
        f"run={ingame_run}:KNIGHTMARE_3478_PHRASE",
        str(knightmare_ingame["promotion_status"]) if knightmare_ingame else "MISSING_KNIGHTMARE_INGAME",
        "Knightmare 3478 phrase remains phrase holdout, not component gloss",
        "SUPPORT_KNIGHTMARE_PHRASE_HOLDOUT_NO_COMPONENT_GLOSS",
        dict(knightmare_ingame) if knightmare_ingame else {"missing": True},
    )
    add_item(
        items,
        "control:rosetta-486486-missing",
        "rosetta_projection_control",
        "rosetta_anchor_projection_items",
        f"run={rosetta_run}:digits=486486",
        str(rosetta_486["projection_status"]) if rosetta_486 else "NO_ROSETTA_WORD_ANCHOR_FOR_486486",
        "486486 is not a promoted rosetta wordcode anchor in the current projection layer",
        "CONTROL_NO_486486_WORDCODE_PROMOTION",
        dict(rosetta_486) if rosetta_486 else {"digits": "486486", "missing": True},
    )

    source_ladder_count = len(SOURCE_LADDER)
    direct_official_sound_source_count = 0
    secondary_sound_source_count = sum(1 for row in SOURCE_LADDER if row["source_tier"] == "secondary_item_page")
    fansite_history_source_count = sum(1 for row in SOURCE_LADDER if row["source_tier"] == "fansite_primary_history")
    event_context_source_count = sum(1 for row in SOURCE_LADDER if row["source_tier"] == "secondary_event_page")
    knightmare_out_of_book_projection_count = int(
        knightmare_projection is not None
        and str(knightmare_projection["projection_status"]) == "EXTERNAL_ROW0_OUT_OF_BOOK_CORPUS"
    )
    awb_486486_entity_quarantine_count = int(
        awb_phrase is not None
        and str(awb_phrase["promotion_status"]) == "ENTITY_QUARANTINE"
        and int(awb_phrase["contaminates_books"]) == 0
    )
    client_verification_required_count = int(direct_official_sound_source_count == 0)
    promoted_plaintext_gloss_count = 0

    decision = (
        "Q13_BONELORD_TOME_SOURCE_LADDER_SUPPORTS_ROUTE_NEEDS_CLIENT_VERIFICATION_NO_GLOSS"
        if source_ladder_count >= 5
        and direct_official_sound_source_count == 0
        and secondary_sound_source_count >= 2
        and fansite_history_source_count >= 1
        and event_context_source_count >= 1
        and knightmare_out_of_book_projection_count == 1
        and awb_486486_entity_quarantine_count == 1
        and client_verification_required_count == 1
        and promoted_plaintext_gloss_count == 0
        else "Q13_BONELORD_TOME_SOURCE_LADDER_REQUIRES_MANUAL_REVIEW"
    )

    payload = {
        "question": "Can Bonelord Tome be used as a stronger source route for 3478/486486 after source-tier and row0 checks?",
        "answer": (
            "Yes as a route-priority source, not as a translation. The source ladder supports the item context through fansite history, secondary item pages, and event context, "
            "but direct official/client sound verification is still missing. Row0 projection keeps Knightmare's 3478 phrase out of the book corpus, and 486486 remains an entity quarantine."
        ),
        "allowed_reading": "Prioritize 3478/486486 phrase-level verification and in-client/item-data confirmation.",
        "blocked_reading": "Do not promote 3478, 486486, or Knightmare phrase components as book glosses.",
        "next_probe": "Create a client/official-data verification target for Bonelord Tome sounds, then compare verified phrase-level behavior against NPC/entity anchors.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q13_bonelord_tome_source_ladder_projection_v1_runs (
                created_at, decision, source_ladder_count,
                direct_official_sound_source_count, secondary_sound_source_count,
                fansite_history_source_count, event_context_source_count,
                knightmare_out_of_book_projection_count,
                awb_486486_entity_quarantine_count,
                client_verification_required_count,
                promoted_plaintext_gloss_count, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                source_ladder_count,
                direct_official_sound_source_count,
                secondary_sound_source_count,
                fansite_history_source_count,
                event_context_source_count,
                knightmare_out_of_book_projection_count,
                awb_486486_entity_quarantine_count,
                client_verification_required_count,
                promoted_plaintext_gloss_count,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q13_bonelord_tome_source_ladder_projection_v1_items (
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
                "source_ladder_count": source_ladder_count,
                "direct_official_sound_source_count": direct_official_sound_source_count,
                "secondary_sound_source_count": secondary_sound_source_count,
                "fansite_history_source_count": fansite_history_source_count,
                "event_context_source_count": event_context_source_count,
                "knightmare_out_of_book_projection_count": knightmare_out_of_book_projection_count,
                "awb_486486_entity_quarantine_count": awb_486486_entity_quarantine_count,
                "client_verification_required_count": client_verification_required_count,
                "promoted_plaintext_gloss_count": promoted_plaintext_gloss_count,
            }
        )
    )


if __name__ == "__main__":
    main()
