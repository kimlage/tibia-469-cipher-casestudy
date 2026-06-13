#!/usr/bin/env python3
"""Q32: source-bridge Q30 contig 1 into a human functional version."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
TARGET_CONTIG = "1"

SOURCE_BRIDGES = [
    {
        "bridge_id": "BEWARE_LANGUAGE_MATH_NUMERIC_BOOKS",
        "source_url": "https://tibia.fandom.com/wiki/Beware_of_the_Bonelords_%28Book%29",
        "source_type": "in_game_book_secondary_page",
        "source_claim": "Bonelord tongue is a blinking code; it is not only language but also mathematics; their books contain only numbers.",
        "supports_contig_phase": "formula/display head and mathemagical frame",
        "bridge_strength": "STRONG_CONTEXT_BRIDGE",
        "allowed_inference": "Read contig 1 as math/formula-first structure rather than natural prose.",
        "blocked_inference": "Do not translate any C86/C68/NAESE/BENNA component from this source alone.",
    },
    {
        "bridge_id": "BEWARE_UNSPEAKABLE_RITUALS_UNDEAD_ARMY",
        "source_url": "https://tibia.fandom.com/wiki/Beware_of_the_Bonelords_%28Book%29",
        "source_type": "in_game_book_secondary_page",
        "source_claim": "Rumours describe Bonelord settlements improving unspeakable necromantic rituals and creating an undead army.",
        "supports_contig_phase": "formula handoff and ritual/operation register",
        "bridge_strength": "MODERATE_CONTEXT_BRIDGE",
        "allowed_inference": "Use ritual/operation register for human shadow versions of formula handoffs.",
        "blocked_inference": "Do not assign a specific ritual name or narrative sentence to the contig.",
    },
    {
        "bridge_id": "THREAT_I_EYESTALK_MAGIC_COMMAND_DEAD",
        "source_url": "https://www.tibiawiki.com.br/wiki/The_Bonelord_Threat_I_%28Book%29",
        "source_type": "in_game_book_secondary_page",
        "source_claim": "Bonelords use eye-stalk magic and necromancy to command the dead as a strategy.",
        "supports_contig_phase": "payload/context corridor as command/control context",
        "bridge_strength": "MODERATE_CONTEXT_BRIDGE",
        "allowed_inference": "Let payload/context packets remain compatible with command/control language.",
        "blocked_inference": "Do not claim C86 or VNCTIIN means command, dead, eye, or necromancy.",
    },
    {
        "bridge_id": "THREAT_II_RESEARCH_EXPERIMENTS",
        "source_url": "https://tibia.fandom.com/wiki/The_Bonelord_Threat_II_%28Book%29",
        "source_type": "in_game_book_secondary_page",
        "source_claim": "After decline, Bonelords worked on weaknesses through research and experiments to improve innate powers.",
        "supports_contig_phase": "handoff from formula/display into payload/context experimentation",
        "bridge_strength": "MODERATE_CONTEXT_BRIDGE",
        "allowed_inference": "Prefer experimental/research framing for ordered packets rather than linear narrative.",
        "blocked_inference": "Do not turn research lore into a dictionary key.",
    },
    {
        "bridge_id": "THREAT_III_MIND_BODY_SOUL_EXPERIMENTS",
        "source_url": "https://www.tibiawiki.com.br/wiki/The_Bonelord_Threat_III_%28Book%29",
        "source_type": "in_game_book_secondary_page",
        "source_claim": "Bonelord experiments include souls, minds, bodies, living/dead switching, and monstrous undead attempts.",
        "supports_contig_phase": "slot/payload context as experimental transformation register",
        "bridge_strength": "MODERATE_CONTEXT_BRIDGE",
        "allowed_inference": "Use as a source-search direction for slot/payload packets involving transformation or control.",
        "blocked_inference": "Do not map NAESE/C68 slots to soul, mind, body, undead, or monster without exact contrast.",
    },
]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q32_contig1_source_bridge_probe_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q30_run_id INTEGER NOT NULL,
            q31_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            target_contig TEXT NOT NULL,
            target_books_json TEXT NOT NULL,
            source_bridge_count INTEGER NOT NULL,
            strong_context_bridge_count INTEGER NOT NULL,
            moderate_context_bridge_count INTEGER NOT NULL,
            exact_sequence_bridge_count INTEGER NOT NULL,
            component_gloss_allowed_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            human_functional_version TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q32_contig1_source_bridge_probe_v1_sources (
            run_id INTEGER NOT NULL,
            bridge_id TEXT NOT NULL,
            source_url TEXT NOT NULL,
            source_type TEXT NOT NULL,
            source_claim TEXT NOT NULL,
            supports_contig_phase TEXT NOT NULL,
            bridge_strength TEXT NOT NULL,
            allowed_inference TEXT NOT NULL,
            blocked_inference TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bridge_id)
        );

        CREATE TABLE IF NOT EXISTS human_q32_contig1_source_bridge_probe_v1_books (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            contig_position INTEGER NOT NULL,
            compiled_stratum TEXT NOT NULL,
            likely_speech_act TEXT NOT NULL,
            plausible_human_reading TEXT NOT NULL,
            row0_markers_json TEXT NOT NULL,
            source_bridge_ids_json TEXT NOT NULL,
            revised_human_shadow_use TEXT NOT NULL,
            blocked_claims_json TEXT NOT NULL,
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


def load_q30_contig(conn: sqlite3.Connection, q30_run_id: int) -> sqlite3.Row:
    row = conn.execute(
        """
        SELECT *
        FROM human_q30_great_calculator_compiled_corpus_spine_map_v1_contigs
        WHERE run_id=? AND basecontigid=?
        """,
        (q30_run_id, TARGET_CONTIG),
    ).fetchone()
    if row is None:
        raise RuntimeError(f"missing Q30 target contig {TARGET_CONTIG}")
    return row


def load_q30_books(conn: sqlite3.Connection, q30_run_id: int, order: list[str]) -> list[sqlite3.Row]:
    by_book = {
        str(row["bookid"]): row
        for row in conn.execute(
            """
            SELECT *
            FROM human_q30_great_calculator_compiled_corpus_spine_map_v1_books
            WHERE run_id=?
            """,
            (q30_run_id,),
        )
    }
    missing = [bookid for bookid in order if bookid not in by_book]
    if missing:
        raise RuntimeError(f"missing Q30 books for contig {TARGET_CONTIG}: {missing}")
    return [by_book[bookid] for bookid in order]


def bridges_for_book(book: sqlite3.Row) -> list[str]:
    text = f"{book['compiled_stratum']} {book['likely_speech_act']} {book['row0_markers_json']}".upper()
    bridge_ids: list[str] = []
    if "FORMULA" in text or "BENNA" in text or "LTAST" in text or "TTNVVN" in text:
        bridge_ids.extend(["BEWARE_LANGUAGE_MATH_NUMERIC_BOOKS", "BEWARE_UNSPEAKABLE_RITUALS_UNDEAD_ARMY"])
    if "PAYLOAD" in text or "CONTEXT" in text or "C86" in text or "VNCTIIN" in text:
        bridge_ids.extend(["THREAT_I_EYESTALK_MAGIC_COMMAND_DEAD", "THREAT_II_RESEARCH_EXPERIMENTS"])
    if "SLOT" in text or "NAESE" in text or "C68" in text:
        bridge_ids.append("THREAT_III_MIND_BODY_SOUL_EXPERIMENTS")
    return sorted(set(bridge_ids))


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q30 = latest_row(conn, "human_q30_great_calculator_compiled_corpus_spine_map_v1_runs")
    q31 = latest_row(conn, "human_q31_bonelord_tome_provenance_bridge_v1_runs")
    audit = latest_row(conn, "human_translation_completion_audit_v5_runs")
    q30_run_id = int(q30["run_id"])

    contig = load_q30_contig(conn, q30_run_id)
    order = str(contig["booksinorder"]).split("->")
    books = load_q30_books(conn, q30_run_id, order)

    strong_context_bridge_count = sum(1 for source in SOURCE_BRIDGES if source["bridge_strength"] == "STRONG_CONTEXT_BRIDGE")
    moderate_context_bridge_count = sum(1 for source in SOURCE_BRIDGES if source["bridge_strength"] == "MODERATE_CONTEXT_BRIDGE")
    exact_sequence_bridge_count = 0
    component_gloss_allowed_count = 0
    canonical_promotion_allowed_count = 0
    human_functional_version = (
        "A source-backed functional reading of contig 58->35->67->2: a mathemagical formula/display head hands off into a "
        "Bonelord research/control context, then narrows into a slot/payload classifier. This is a ritual/experimental packet, "
        "not a sentence-level translation."
    )
    decision = (
        "Q32_CONTIG1_SOURCE_BRIDGE_SUPPORTS_FORMULA_CONTEXT_SLOT_HUMAN_SHADOW_NO_GLOSS"
        if len(order) == 4
        and len(SOURCE_BRIDGES) == 5
        and strong_context_bridge_count >= 1
        and moderate_context_bridge_count >= 3
        and exact_sequence_bridge_count == 0
        and component_gloss_allowed_count == 0
        and canonical_promotion_allowed_count == 0
        and int(audit["promoted_gloss_count"]) == 0
        else "Q32_CONTIG1_SOURCE_BRIDGE_REQUIRES_REVIEW"
    )
    payload = {
        "question": "Can Q30 contig 1 be given a human functional version anchored in in-game books?",
        "answer": "Yes as a functional ritual/experimental packet, not as plaintext.",
        "supported_shape": "formula/display -> research/control context -> slot/payload classifier",
        "allowed_reading": human_functional_version,
        "blocked_reading": "No component gloss for BENNA, C86, C68, VNCTIIN, NAESE, LTAST, TTNVVN, or any book sentence.",
        "web_source_gate": "secondary pages for in-game books; no direct client extraction or exact sequence meaning",
        "next_action": "Use this contig as a source-search spine for exact in-game contrasts around rituals, experiments, command/control, and slot changes.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q32_contig1_source_bridge_probe_v1_runs (
                created_at, decision, q30_run_id, q31_run_id,
                completion_audit_run_id, target_contig, target_books_json,
                source_bridge_count, strong_context_bridge_count,
                moderate_context_bridge_count, exact_sequence_bridge_count,
                component_gloss_allowed_count, canonical_promotion_allowed_count,
                human_functional_version, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                q30_run_id,
                int(q31["run_id"]),
                int(audit["run_id"]),
                TARGET_CONTIG,
                j(order),
                len(SOURCE_BRIDGES),
                strong_context_bridge_count,
                moderate_context_bridge_count,
                exact_sequence_bridge_count,
                component_gloss_allowed_count,
                canonical_promotion_allowed_count,
                human_functional_version,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q32_contig1_source_bridge_probe_v1_sources (
                run_id, bridge_id, source_url, source_type, source_claim,
                supports_contig_phase, bridge_strength, allowed_inference,
                blocked_inference, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    str(source["bridge_id"]),
                    str(source["source_url"]),
                    str(source["source_type"]),
                    str(source["source_claim"]),
                    str(source["supports_contig_phase"]),
                    str(source["bridge_strength"]),
                    str(source["allowed_inference"]),
                    str(source["blocked_inference"]),
                    j(source),
                )
                for source in SOURCE_BRIDGES
            ],
        )
        conn.executemany(
            """
            INSERT INTO human_q32_contig1_source_bridge_probe_v1_books (
                run_id, bookid, contig_position, compiled_stratum,
                likely_speech_act, plausible_human_reading, row0_markers_json,
                source_bridge_ids_json, revised_human_shadow_use,
                blocked_claims_json, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    str(book["bookid"]),
                    index + 1,
                    str(book["compiled_stratum"]),
                    str(book["likely_speech_act"]),
                    str(book["plausible_human_reading"]),
                    str(book["row0_markers_json"]),
                    j(bridges_for_book(book)),
                    "Use as a source-anchored functional packet member; do not draft sentence prose.",
                    j(
                        [
                            "component_gloss",
                            "sentence_translation",
                            "direct_necromancy_word_mapping",
                            "external_candidate_semantics",
                        ]
                    ),
                    j({"q30_book": dict(book), "source_bridge_ids": bridges_for_book(book), "q30_contig": dict(contig)}),
                )
                for index, book in enumerate(books)
            ],
        )

    print(
        j(
            {
                "run_id": run_id,
                "decision": decision,
                "target_contig": TARGET_CONTIG,
                "target_books": order,
                "source_bridge_count": len(SOURCE_BRIDGES),
                "strong_context_bridge_count": strong_context_bridge_count,
                "moderate_context_bridge_count": moderate_context_bridge_count,
                "exact_sequence_bridge_count": exact_sequence_bridge_count,
                "component_gloss_allowed_count": component_gloss_allowed_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
                "human_functional_version": human_functional_version,
            }
        )
    )


if __name__ == "__main__":
    main()
