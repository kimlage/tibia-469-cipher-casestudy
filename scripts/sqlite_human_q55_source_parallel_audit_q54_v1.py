#!/usr/bin/env python3
"""Q55: link Q54 phrase candidates to in-game source parallels without gloss."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

TARGET_BOOKS = ["2", "10", "27", "35", "67"]

ANCHOR_SOURCE_ROLES = {
    "AWB_469_LANGUAGE_MATHEMAGIC": "LANGUAGE_METHOD_MATHEMAGIC",
    "GREAT_CALCULATOR_GATHER_LANGUAGE": "CORPUS_ASSEMBLY_STRUCTURE",
    "PARADOX_1_PLUS_1_KEYS": "QUEST_MATHEMAGIC_OPERATOR_SELECTOR",
}

BRIDGE_SOURCE_ROLES = {
    "BEWARE_LANGUAGE_MATH_NUMERIC_BOOKS": "BONELORD_LANGUAGE_NUMERIC_MATH",
    "BEWARE_UNSPEAKABLE_RITUALS_UNDEAD_ARMY": "RITUAL_OPERATION_REGISTER",
    "THREAT_I_EYESTALK_MAGIC_COMMAND_DEAD": "COMMAND_CONTROL_NECROMANCY_REGISTER",
    "THREAT_II_RESEARCH_EXPERIMENTS": "RESEARCH_EXPERIMENT_REGISTER",
    "THREAT_III_MIND_BODY_SOUL_EXPERIMENTS": "TRANSFORMATION_SLOT_PAYLOAD_REGISTER",
}

SOURCE_PARALLEL_USE = {
    "AWB_469_LANGUAGE_MATHEMAGIC": "Use as method pressure toward numeric/operator processing, not ordinary cipher prose.",
    "GREAT_CALCULATOR_GATHER_LANGUAGE": "Use as corpus-structure pressure: assembled language material can be packetized or compiled.",
    "PARADOX_1_PLUS_1_KEYS": "Use as quest-side operator evidence that mathemagic can select values by context.",
    "BEWARE_LANGUAGE_MATH_NUMERIC_BOOKS": "Use as direct in-game language-frame pressure toward numeric mathematics.",
    "BEWARE_UNSPEAKABLE_RITUALS_UNDEAD_ARMY": "Use as ritual/operation register for formula handoffs.",
    "THREAT_I_EYESTALK_MAGIC_COMMAND_DEAD": "Use as control/command register for payload/context routes.",
    "THREAT_II_RESEARCH_EXPERIMENTS": "Use as research/experiment register for ordered packets.",
    "THREAT_III_MIND_BODY_SOUL_EXPERIMENTS": "Use as transformation/slot/payload register, with strict no-dictionary limits.",
}

WEB_CHECK_STATUS = {
    source_id: "WEB_SOURCE_CHECKED_2026_05_11_REGISTER_PARALLEL_ONLY"
    for source_id in [*ANCHOR_SOURCE_ROLES.keys(), *BRIDGE_SOURCE_ROLES.keys()]
}

BOOK_SOURCE_LINKS = {
    "2": [
        "AWB_469_LANGUAGE_MATHEMAGIC",
        "GREAT_CALCULATOR_GATHER_LANGUAGE",
        "PARADOX_1_PLUS_1_KEYS",
        "BEWARE_LANGUAGE_MATH_NUMERIC_BOOKS",
        "THREAT_II_RESEARCH_EXPERIMENTS",
        "THREAT_III_MIND_BODY_SOUL_EXPERIMENTS",
    ],
    "10": [
        "AWB_469_LANGUAGE_MATHEMAGIC",
        "PARADOX_1_PLUS_1_KEYS",
        "BEWARE_LANGUAGE_MATH_NUMERIC_BOOKS",
        "BEWARE_UNSPEAKABLE_RITUALS_UNDEAD_ARMY",
        "THREAT_II_RESEARCH_EXPERIMENTS",
    ],
    "27": [
        "AWB_469_LANGUAGE_MATHEMAGIC",
        "GREAT_CALCULATOR_GATHER_LANGUAGE",
        "PARADOX_1_PLUS_1_KEYS",
        "THREAT_I_EYESTALK_MAGIC_COMMAND_DEAD",
        "THREAT_II_RESEARCH_EXPERIMENTS",
        "THREAT_III_MIND_BODY_SOUL_EXPERIMENTS",
    ],
    "35": [
        "AWB_469_LANGUAGE_MATHEMAGIC",
        "GREAT_CALCULATOR_GATHER_LANGUAGE",
        "PARADOX_1_PLUS_1_KEYS",
        "BEWARE_LANGUAGE_MATH_NUMERIC_BOOKS",
        "BEWARE_UNSPEAKABLE_RITUALS_UNDEAD_ARMY",
        "THREAT_II_RESEARCH_EXPERIMENTS",
    ],
    "67": [
        "AWB_469_LANGUAGE_MATHEMAGIC",
        "GREAT_CALCULATOR_GATHER_LANGUAGE",
        "BEWARE_LANGUAGE_MATH_NUMERIC_BOOKS",
        "BEWARE_UNSPEAKABLE_RITUALS_UNDEAD_ARMY",
        "THREAT_II_RESEARCH_EXPERIMENTS",
        "THREAT_III_MIND_BODY_SOUL_EXPERIMENTS",
    ],
}

BOOK_SOURCE_SUMMARY = {
    "2": "Mathemagic and assembled-language sources support a context-selected classifier route; Threat II/III keep it in experiment/slot register.",
    "10": "Formula and mathemagic sources support a handoff route; ritual and research sources bound the register.",
    "27": "Quest/operator and Threat I/II/III sources support a held context/payload corridor, not a literal command phrase.",
    "35": "Formula, mathemagic, ritual, and research sources support the contig-backed formula-to-context route.",
    "67": "Assembled-language, ritual, research, and transformation sources support a handoff toward Book 2's classifier path.",
}

BOOK_NEXT_ACTION = {
    "2": "Test whether slot/classifier wording survives contrast against non-Q54 C68 slot controls.",
    "10": "Compare against Book 35 to separate formula handoff from generic context routing.",
    "27": "Search for payload/context contrasts that distinguish hold-open from command/control overreach.",
    "35": "Use as the contig-supported formula route when testing the 35->67->2 edge.",
    "67": "Use as the immediate bridge control for the 67->2 phrase transition.",
}


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q55_source_parallel_audit_q54_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q54_run_id INTEGER NOT NULL,
            anchor_corpus_run_id INTEGER NOT NULL,
            q32_source_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            target_book_count INTEGER NOT NULL,
            source_count INTEGER NOT NULL,
            source_parallel_ready_count INTEGER NOT NULL,
            phrase_source_link_count INTEGER NOT NULL,
            method_anchor_source_count INTEGER NOT NULL,
            quest_operator_source_count INTEGER NOT NULL,
            lore_register_source_count INTEGER NOT NULL,
            direct_gloss_count INTEGER NOT NULL,
            prose_gloss_allowed_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            human_route_version TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q55_source_parallel_audit_q54_v1_sources (
            run_id INTEGER NOT NULL,
            source_id TEXT NOT NULL,
            source_origin TEXT NOT NULL,
            source_origin_run_id INTEGER NOT NULL,
            source_url TEXT NOT NULL,
            source_role TEXT NOT NULL,
            source_claim TEXT NOT NULL,
            source_parallel_use TEXT NOT NULL,
            web_check_status TEXT NOT NULL,
            allowed_inference TEXT NOT NULL,
            blocked_inference TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, source_id)
        );

        CREATE TABLE IF NOT EXISTS human_q55_source_parallel_audit_q54_v1_books (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            phrase_functional_version TEXT NOT NULL,
            confidence_tier TEXT NOT NULL,
            source_ids_json TEXT NOT NULL,
            source_parallel_status TEXT NOT NULL,
            source_parallel_summary TEXT NOT NULL,
            allowed_source_inference TEXT NOT NULL,
            blocked_overreach TEXT NOT NULL,
            next_action TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        );
        """
    )


def latest_row(conn: sqlite3.Connection, table: str) -> sqlite3.Row:
    row = conn.execute(f"SELECT * FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    if row is None:
        raise RuntimeError(f"missing required row: {table}")
    return row


def latest_item_run_id(conn: sqlite3.Connection, table: str, id_column: str) -> int:
    row = conn.execute(f"SELECT max(run_id) AS run_id FROM {table} WHERE {id_column} IS NOT NULL").fetchone()
    if row is None or row["run_id"] is None:
        raise RuntimeError(f"missing required item run: {table}")
    return int(row["run_id"])


def q54_books(conn: sqlite3.Connection, q54_run_id: int) -> dict[str, sqlite3.Row]:
    rows = conn.execute(
        """
        SELECT *
        FROM human_q54_supported_chain_phrase_layer_v1_books
        WHERE run_id=?
        """,
        (q54_run_id,),
    ).fetchall()
    by_book = {str(row["bookid"]): row for row in rows}
    missing = [bookid for bookid in TARGET_BOOKS if bookid not in by_book]
    if missing:
        raise RuntimeError(f"missing Q54 target books: {missing}")
    return by_book


def load_anchor_sources(conn: sqlite3.Connection, run_id: int) -> dict[str, dict[str, object]]:
    placeholders = ",".join("?" for _ in ANCHOR_SOURCE_ROLES)
    rows = conn.execute(
        f"""
        SELECT *
        FROM human_ingame_anchor_corpus_v1_items
        WHERE run_id=? AND anchor_id IN ({placeholders})
        """,
        (run_id, *ANCHOR_SOURCE_ROLES.keys()),
    ).fetchall()
    sources = {}
    for row in rows:
        source_id = str(row["anchor_id"])
        sources[source_id] = {
            "source_id": source_id,
            "source_origin": "human_ingame_anchor_corpus_v1_items",
            "source_origin_run_id": run_id,
            "source_url": str(row["source_url"]),
            "source_role": ANCHOR_SOURCE_ROLES[source_id],
            "source_claim": str(row["claim_summary"]),
            "source_parallel_use": SOURCE_PARALLEL_USE[source_id],
            "web_check_status": WEB_CHECK_STATUS[source_id],
            "allowed_inference": str(row["allowed_inference"]),
            "blocked_inference": str(row["blocked_inference"]),
            "evidence": dict(row),
        }
    missing = [source_id for source_id in ANCHOR_SOURCE_ROLES if source_id not in sources]
    if missing:
        raise RuntimeError(f"missing anchor sources: {missing}")
    return sources


def load_bridge_sources(conn: sqlite3.Connection, run_id: int) -> dict[str, dict[str, object]]:
    placeholders = ",".join("?" for _ in BRIDGE_SOURCE_ROLES)
    rows = conn.execute(
        f"""
        SELECT *
        FROM human_q32_contig1_source_bridge_probe_v1_sources
        WHERE run_id=? AND bridge_id IN ({placeholders})
        """,
        (run_id, *BRIDGE_SOURCE_ROLES.keys()),
    ).fetchall()
    sources = {}
    for row in rows:
        source_id = str(row["bridge_id"])
        sources[source_id] = {
            "source_id": source_id,
            "source_origin": "human_q32_contig1_source_bridge_probe_v1_sources",
            "source_origin_run_id": run_id,
            "source_url": str(row["source_url"]),
            "source_role": BRIDGE_SOURCE_ROLES[source_id],
            "source_claim": str(row["source_claim"]),
            "source_parallel_use": SOURCE_PARALLEL_USE[source_id],
            "web_check_status": WEB_CHECK_STATUS[source_id],
            "allowed_inference": str(row["allowed_inference"]),
            "blocked_inference": str(row["blocked_inference"]),
            "evidence": dict(row),
        }
    missing = [source_id for source_id in BRIDGE_SOURCE_ROLES if source_id not in sources]
    if missing:
        raise RuntimeError(f"missing bridge sources: {missing}")
    return sources


def source_parallel_status(source_ids: list[str]) -> str:
    if len(source_ids) >= 5:
        return "SOURCE_PARALLEL_READY_MULTI_ANCHOR_NO_GLOSS"
    return "SOURCE_PARALLEL_REQUIRES_REVIEW"


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q54 = latest_row(conn, "human_q54_supported_chain_phrase_layer_v1_runs")
    audit = latest_row(conn, "human_translation_completion_audit_v5_runs")
    anchor_run_id = latest_item_run_id(conn, "human_ingame_anchor_corpus_v1_items", "anchor_id")
    q32_source_run_id = latest_item_run_id(conn, "human_q32_contig1_source_bridge_probe_v1_sources", "bridge_id")
    q54_by_book = q54_books(conn, int(q54["run_id"]))

    sources = {}
    sources.update(load_anchor_sources(conn, anchor_run_id))
    sources.update(load_bridge_sources(conn, q32_source_run_id))

    prepared_books = []
    for bookid in TARGET_BOOKS:
        source_ids = BOOK_SOURCE_LINKS[bookid]
        missing_sources = [source_id for source_id in source_ids if source_id not in sources]
        if missing_sources:
            raise RuntimeError(f"book {bookid} references missing sources: {missing_sources}")
        q54_book = q54_by_book[bookid]
        prepared_books.append(
            {
                "bookid": bookid,
                "phrase_functional_version": str(q54_book["phrase_functional_version"]),
                "confidence_tier": str(q54_book["confidence_tier"]),
                "source_ids": source_ids,
                "source_parallel_status": source_parallel_status(source_ids),
                "source_parallel_summary": BOOK_SOURCE_SUMMARY[bookid],
                "allowed_source_inference": (
                    "Use the listed in-game parallels to constrain the human shadow register and route shape only."
                ),
                "blocked_overreach": (
                    "No direct dictionary gloss, no sentence translation, no component meaning, and no canonical promotion."
                ),
                "next_action": BOOK_NEXT_ACTION[bookid],
                "evidence": {
                    "q54_book": dict(q54_book),
                    "sources": [sources[source_id] for source_id in source_ids],
                },
            }
        )

    source_parallel_ready_count = sum(
        1 for item in prepared_books if item["source_parallel_status"] == "SOURCE_PARALLEL_READY_MULTI_ANCHOR_NO_GLOSS"
    )
    phrase_source_link_count = sum(len(item["source_ids"]) for item in prepared_books)
    method_anchor_source_count = 2
    quest_operator_source_count = 1
    lore_register_source_count = len(sources) - method_anchor_source_count - quest_operator_source_count
    direct_gloss_count = 0
    prose_gloss_allowed_count = 0
    canonical_promotion_allowed_count = 0
    human_route_version = (
        "Q54 source-parallel route: the five phrase candidates are supported as mathemagical, compiled, ritual, "
        "research, control, and transformation-register routes. The support constrains register and route shape only; "
        "it does not translate any component or sentence."
    )
    decision = (
        "Q55_Q54_SOURCE_PARALLEL_AUDIT_READY_8_SOURCES_5_PHRASES_NO_GLOSS"
        if len(prepared_books) == 5
        and len(sources) == 8
        and source_parallel_ready_count == 5
        and phrase_source_link_count >= 25
        and method_anchor_source_count == 2
        and quest_operator_source_count == 1
        and lore_register_source_count == 5
        and int(q54["prose_gloss_allowed_count"]) == 0
        and int(q54["canonical_promotion_allowed_count"]) == 0
        and int(audit["promoted_gloss_count"]) == 0
        and direct_gloss_count == 0
        and prose_gloss_allowed_count == 0
        and canonical_promotion_allowed_count == 0
        else "Q55_Q54_SOURCE_PARALLEL_AUDIT_REQUIRES_REVIEW"
    )
    payload = {
        "question": "Can the Q54 phrase candidates be anchored in in-game source parallels without turning into invented prose?",
        "answer": "Yes. Eight registered sources support the route/register layer for all five phrases, but none permits direct gloss.",
        "source_classes": {
            "method_anchor": ["AWB_469_LANGUAGE_MATHEMAGIC", "GREAT_CALCULATOR_GATHER_LANGUAGE"],
            "quest_operator": ["PARADOX_1_PLUS_1_KEYS"],
            "lore_register": sorted(BRIDGE_SOURCE_ROLES),
        },
        "human_route_version": human_route_version,
        "blocked_use": "Do not promote component glosses, sentence translations, or canonical plaintext from this audit.",
        "next_action": "Use source-linked Q54 phrases as falsifiable human shadow readings and search for exact in-game contrast pairs.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q55_source_parallel_audit_q54_v1_runs (
                created_at, decision, q54_run_id, anchor_corpus_run_id,
                q32_source_run_id, completion_audit_run_id, target_book_count,
                source_count, source_parallel_ready_count, phrase_source_link_count,
                method_anchor_source_count, quest_operator_source_count,
                lore_register_source_count, direct_gloss_count,
                prose_gloss_allowed_count, canonical_promotion_allowed_count,
                human_route_version, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                int(q54["run_id"]),
                anchor_run_id,
                q32_source_run_id,
                int(audit["run_id"]),
                len(prepared_books),
                len(sources),
                source_parallel_ready_count,
                phrase_source_link_count,
                method_anchor_source_count,
                quest_operator_source_count,
                lore_register_source_count,
                direct_gloss_count,
                prose_gloss_allowed_count,
                canonical_promotion_allowed_count,
                human_route_version,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q55_source_parallel_audit_q54_v1_sources (
                run_id, source_id, source_origin, source_origin_run_id,
                source_url, source_role, source_claim, source_parallel_use,
                web_check_status, allowed_inference, blocked_inference,
                evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    str(source["source_id"]),
                    str(source["source_origin"]),
                    int(source["source_origin_run_id"]),
                    str(source["source_url"]),
                    str(source["source_role"]),
                    str(source["source_claim"]),
                    str(source["source_parallel_use"]),
                    str(source["web_check_status"]),
                    str(source["allowed_inference"]),
                    str(source["blocked_inference"]),
                    j(source["evidence"]),
                )
                for source in sorted(sources.values(), key=lambda item: str(item["source_id"]))
            ],
        )
        conn.executemany(
            """
            INSERT INTO human_q55_source_parallel_audit_q54_v1_books (
                run_id, bookid, phrase_functional_version, confidence_tier,
                source_ids_json, source_parallel_status, source_parallel_summary,
                allowed_source_inference, blocked_overreach, next_action,
                evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    item["bookid"],
                    item["phrase_functional_version"],
                    item["confidence_tier"],
                    j(item["source_ids"]),
                    item["source_parallel_status"],
                    item["source_parallel_summary"],
                    item["allowed_source_inference"],
                    item["blocked_overreach"],
                    item["next_action"],
                    j(item["evidence"]),
                )
                for item in prepared_books
            ],
        )

    print(
        j(
            {
                "run_id": run_id,
                "decision": decision,
                "q54_run_id": int(q54["run_id"]),
                "target_book_count": len(prepared_books),
                "source_count": len(sources),
                "source_parallel_ready_count": source_parallel_ready_count,
                "phrase_source_link_count": phrase_source_link_count,
                "method_anchor_source_count": method_anchor_source_count,
                "quest_operator_source_count": quest_operator_source_count,
                "lore_register_source_count": lore_register_source_count,
                "direct_gloss_count": direct_gloss_count,
                "prose_gloss_allowed_count": prose_gloss_allowed_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
            }
        )
    )


if __name__ == "__main__":
    main()
