#!/usr/bin/env python3
"""Materialize a source-aware in-game anchor corpus for human translation work."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"


ANCHORS = [
    {
        "anchor_id": "AWB_SELF_NAME_486486",
        "source_id": "WRINKLED_BONELORD_TRANSCRIPT",
        "source_url": "https://tibia.fandom.com/wiki/A_Wrinkled_Bonelord/Transcripts",
        "anchor_type": "NPC_DIALOGUE_NUMERIC_LORE",
        "exact_sequence": "486486",
        "claim_summary": "A Wrinkled Bonelord gives 486486 as his name/self-identification.",
        "human_use": "proper-name/formula constraint only",
        "route_ids": ["R1_INGAME_CONTEXT_CORPUS", "R4_NAME_AS_FORMULA", "R10_EXTERNAL_EXACT_GLOSS_ROUTE"],
        "allowed_inference": "Bonelord names may be numeric/formula-like; use as named anchor, not book decoder.",
        "blocked_inference": "Do not translate 486486 into a general word or use it to decode Hellgate books.",
        "risk": "secondary transcript source; verify against in-game dialogue if stronger promotion is attempted",
        "promotion_status": "SCOPED_LORE_ANCHOR_NO_BOOK_GLOSS",
    },
    {
        "anchor_id": "AWB_TIBIA_ONE",
        "source_id": "WRINKLED_BONELORD_TRANSCRIPT",
        "source_url": "https://tibia.fandom.com/wiki/A_Wrinkled_Bonelord/Transcripts",
        "anchor_type": "NPC_DIALOGUE_NUMERIC_LORE",
        "exact_sequence": "1",
        "claim_summary": "A Wrinkled Bonelord associates the number 1 with Tibia.",
        "human_use": "world/one numeric constraint",
        "route_ids": ["R1_INGAME_CONTEXT_CORPUS", "R9_ZERO_ONE_TABOO_INVERSION"],
        "allowed_inference": "One/world relations can guide boundary/operator hypotheses.",
        "blocked_inference": "Do not use 1 as a universal lexical value inside all books.",
        "risk": "dialogue context-specific",
        "promotion_status": "SCOPED_LORE_ANCHOR_NO_BOOK_GLOSS",
    },
    {
        "anchor_id": "AWB_ZERO_TABOO",
        "source_id": "WRINKLED_BONELORD_TRANSCRIPT",
        "source_url": "https://tibia.fandom.com/wiki/A_Wrinkled_Bonelord/Transcripts",
        "anchor_type": "NPC_DIALOGUE_NUMERIC_LORE",
        "exact_sequence": "0",
        "claim_summary": "A Wrinkled Bonelord treats 0 as obscene/taboo.",
        "human_use": "zero/taboo boundary constraint",
        "route_ids": ["R1_INGAME_CONTEXT_CORPUS", "R9_ZERO_ONE_TABOO_INVERSION"],
        "allowed_inference": "Use as a boundary/taboo/inversion hypothesis for row0/omitted-zero behavior.",
        "blocked_inference": "Do not read every zero or star boundary as obscenity.",
        "risk": "dialogue context-specific; row0 uses omitted leading zeros mechanically",
        "promotion_status": "SCOPED_LORE_ANCHOR_NO_BOOK_GLOSS",
    },
    {
        "anchor_id": "AWB_469_LANGUAGE_MATHEMAGIC",
        "source_id": "WRINKLED_BONELORD_TRANSCRIPT",
        "source_url": "https://tibia.fandom.com/wiki/A_Wrinkled_Bonelord/Transcripts",
        "anchor_type": "NPC_DIALOGUE_LANGUAGE_METHOD",
        "exact_sequence": "469",
        "claim_summary": "A Wrinkled Bonelord links the language of his kind to numbers/mathemagic.",
        "human_use": "method constraint",
        "route_ids": ["R1_INGAME_CONTEXT_CORPUS", "R3_MATHEMAGIC_OPERATOR_GRID"],
        "allowed_inference": "Prefer numeric/operator hypotheses over ordinary substitution ciphers.",
        "blocked_inference": "Do not assume mathemagic outputs are direct plaintext.",
        "risk": "broad lore constraint, not a phrase translation",
        "promotion_status": "METHOD_ANCHOR_NO_BOOK_GLOSS",
    },
    {
        "anchor_id": "PARADOX_1_PLUS_1_KEYS",
        "source_id": "PARADOX_TOWER_MATHEMAGICS",
        "source_url": "https://www.tibia-wiki.net/wiki/Paradox_Tower_Quest/Spoiler",
        "anchor_type": "QUEST_MATHEMAGIC_OPERATOR",
        "exact_sequence": "1;13;49;94",
        "claim_summary": "Paradox/Mintwallin mathemagics provides variable 1+1 outputs represented operationally as 1, 13, 49, 94.",
        "human_use": "operator-key inventory",
        "route_ids": ["R3_MATHEMAGIC_OPERATOR_GRID", "R8_MINOTAUR_MAGE_TRUTH_BRIDGE"],
        "allowed_inference": "Use 1/13/49/94 as selector/operator candidates.",
        "blocked_inference": "Do not use 1/13/49/94 as a direct dictionary or solved key.",
        "risk": "quest-spoiler source and per-player variation; still in-game puzzle anchor",
        "promotion_status": "OPERATOR_ANCHOR_NO_PLAINTEXT",
    },
    {
        "anchor_id": "GREAT_CALCULATOR_GATHER_LANGUAGE",
        "source_id": "YOU_CANNOT_EVEN_IMAGINE",
        "source_url": "https://www.tibiawiki.com.br/wiki/You_Cannot_Even_Imagine_%28Book%29",
        "anchor_type": "BOOK_LORE_CORPUS_STRUCTURE",
        "exact_sequence": "",
        "claim_summary": "A translated in-game book says the Great Calculator gathered/collected Bonelord language material.",
        "human_use": "corpus-structure hypothesis",
        "route_ids": ["R1_INGAME_CONTEXT_CORPUS", "R7_GREAT_CALCULATOR_LINEAGE"],
        "allowed_inference": "The 469 corpus may be compiled/gathered material rather than one linear text.",
        "blocked_inference": "Do not infer any direct 469 phrase meaning from this book alone.",
        "risk": "translated wiki page; not a 469 text",
        "promotion_status": "CORPUS_STRUCTURE_ANCHOR_NO_BOOK_GLOSS",
    },
    {
        "anchor_id": "HONEMINAS_FORMULA_PARALLEL",
        "source_id": "HONEMINAS_FORMULA",
        "source_url": "https://www.tibiawiki.com.br/Honeminas_Formula",
        "anchor_type": "BOOK_LORE_FORMULA_PARALLEL",
        "exact_sequence": "",
        "claim_summary": "Tibia lore includes explicit formula notation tied to magic/creation structure.",
        "human_use": "parallel formula grammar",
        "route_ids": ["R3_MATHEMAGIC_OPERATOR_GRID", "R7_GREAT_CALCULATOR_LINEAGE"],
        "allowed_inference": "Formulaic language is a plausible in-game discourse mode.",
        "blocked_inference": "Do not bridge Honeminas to Bonelord without a mechanical or lore link.",
        "risk": "not Bonelord-specific",
        "promotion_status": "PARALLEL_FORMULA_ANCHOR_NO_BOOK_GLOSS",
    },
    {
        "anchor_id": "CHAYENNE_EXTERNAL_FRAME",
        "source_id": "TIBIAWIKI_BR_469_SYNTHESIS",
        "source_url": "https://www.tibiawiki.com.br/469",
        "anchor_type": "EXTERNAL_469_SHAPE_HOLDOUT",
        "exact_sequence": "114514519485611451908304576512282177 6612527570584",
        "claim_summary": "Chayenne's external 469 reply projects to the shared frame AEFIEIEFIIVFAEATVAT in Books 8/37/63/66.",
        "human_use": "register/frame holdout",
        "route_ids": ["R2_NPC_PHRASE_STYLE_COMPARATOR", "R3_MATHEMAGIC_OPERATOR_GRID"],
        "allowed_inference": "External 469 can supply reusable shape/register constraints.",
        "blocked_inference": "Do not translate the block as one sentence because it spans multiple internal branches.",
        "risk": "mixed provenance; no explicit meaning",
        "promotion_status": "REGISTER_FRAME_ANCHOR_NO_SINGLE_GLOSS",
    },
    {
        "anchor_id": "KNIGHTMARE_3478_PHRASE",
        "source_id": "TIBIAWIKI_BR_469_SYNTHESIS",
        "source_url": "https://www.tibiawiki.com.br/469",
        "anchor_type": "EXTERNAL_469_PHRASE_HOLDOUT",
        "exact_sequence": "3478 67 90871 97664 3466 0 345",
        "claim_summary": "Knightmare-associated external phrase includes 3478 and is a phrase-level holdout in the project.",
        "human_use": "name/formula and phrase-level holdout",
        "route_ids": ["R2_NPC_PHRASE_STYLE_COMPARATOR", "R4_NAME_AS_FORMULA", "R10_EXTERNAL_EXACT_GLOSS_ROUTE"],
        "allowed_inference": "Use to test whether 3478/name-formula behavior generalizes.",
        "blocked_inference": "Do not derive component gloss or book meaning from the phrase-level holdout.",
        "risk": "external phrase lacks explicit meaning",
        "promotion_status": "PHRASE_HOLDOUT_NO_COMPONENT_GLOSS",
    },
    {
        "anchor_id": "AVAR_TAR_POEM_REGISTER",
        "source_id": "TIBIAQA_AVAR_TAR_POEM",
        "source_url": "https://www.tibiaqa.com/20625/which-npcs-are-speaking-bonelord-469-language",
        "anchor_type": "NPC_STYLE_REGISTER_HOLDOUT",
        "exact_sequence": "29639 46781 9063376290 3222011 677 80322429 67538 14805394 6880326 677 63378129 337011 72683 149630 4378 453 639 578300 986372 2953639",
        "claim_summary": "Avar Tar gives a long numeric poem/register when prompted about Bonelord language.",
        "human_use": "poem/register comparator",
        "route_ids": ["R2_NPC_PHRASE_STYLE_COMPARATOR", "R10_EXTERNAL_EXACT_GLOSS_ROUTE"],
        "allowed_inference": "Use as style/register contrast outside the Hellgate book corpus.",
        "blocked_inference": "Do not use unreliable/speculative Avar context to promote book semantics.",
        "risk": "fansite transcription; NPC may be unreliable/speculative",
        "promotion_status": "REGISTER_HOLDOUT_NO_BOOK_GLOSS",
    },
]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_ingame_anchor_corpus_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            anchor_count INTEGER NOT NULL,
            scoped_anchor_count INTEGER NOT NULL,
            operator_anchor_count INTEGER NOT NULL,
            register_anchor_count INTEGER NOT NULL,
            accepted_book_gloss_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_ingame_anchor_corpus_v1_items (
            run_id INTEGER NOT NULL,
            anchor_id TEXT NOT NULL,
            source_id TEXT NOT NULL,
            source_url TEXT NOT NULL,
            anchor_type TEXT NOT NULL,
            exact_sequence TEXT NOT NULL,
            claim_summary TEXT NOT NULL,
            human_use TEXT NOT NULL,
            route_ids_json TEXT NOT NULL,
            allowed_inference TEXT NOT NULL,
            blocked_inference TEXT NOT NULL,
            risk TEXT NOT NULL,
            promotion_status TEXT NOT NULL,
            PRIMARY KEY (run_id, anchor_id)
        );
        """
    )


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    scoped = sum(1 for item in ANCHORS if "SCOPED" in item["promotion_status"] or item["anchor_type"].startswith("NPC_DIALOGUE"))
    operator = sum(1 for item in ANCHORS if "OPERATOR" in item["anchor_type"] or "Mathemagic" in item["human_use"])
    register = sum(1 for item in ANCHORS if "REGISTER" in item["anchor_type"] or "register" in item["human_use"].lower())
    payload = {
        "principle": "in-game anchors constrain human readings; they do not promote book gloss unless exact sequence plus meaning is attested",
        "source_priority": ["in-game NPC/book/quest", "near-primary external phrase", "fansite/community synthesis"],
    }
    cur = conn.execute(
        """
        INSERT INTO human_ingame_anchor_corpus_v1_runs
        (created_at, decision, anchor_count, scoped_anchor_count,
         operator_anchor_count, register_anchor_count,
         accepted_book_gloss_count, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            now(),
            "HUMAN_INGAME_ANCHOR_CORPUS_READY_NO_BOOK_GLOSS",
            len(ANCHORS),
            scoped,
            operator,
            register,
            0,
            json.dumps(payload, ensure_ascii=False, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)
    for item in ANCHORS:
        conn.execute(
            """
            INSERT INTO human_ingame_anchor_corpus_v1_items
            (run_id, anchor_id, source_id, source_url, anchor_type,
             exact_sequence, claim_summary, human_use, route_ids_json,
             allowed_inference, blocked_inference, risk, promotion_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                item["anchor_id"],
                item["source_id"],
                item["source_url"],
                item["anchor_type"],
                item["exact_sequence"],
                item["claim_summary"],
                item["human_use"],
                json.dumps(item["route_ids"], ensure_ascii=False, sort_keys=True),
                item["allowed_inference"],
                item["blocked_inference"],
                item["risk"],
                item["promotion_status"],
            ),
        )

    conn.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": "HUMAN_INGAME_ANCHOR_CORPUS_READY_NO_BOOK_GLOSS",
                "anchor_count": len(ANCHORS),
                "scoped_anchor_count": scoped,
                "operator_anchor_count": operator,
                "register_anchor_count": register,
                "accepted_book_gloss_count": 0,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
