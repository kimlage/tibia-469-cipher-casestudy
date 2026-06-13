#!/usr/bin/env python3
"""Q34: give source-anchored human functional versions to remaining Q30 contigs."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
TARGET_CONTIGS = ["0", "4", "5"]

SOURCE_BRIDGES = [
    {
        "bridge_id": "GREAT_CALCULATOR_COMPILED_LANGUAGE",
        "source_url": "https://www.tibiawiki.com.br/wiki/You_Cannot_Even_Imagine_%28Book%29",
        "source_type": "in_game_book_secondary_page",
        "source_claim": "The Great Calculator helped assemble/gather the Bonelord language.",
        "supports_contig_phase": "compiled formula/spine corpus behavior",
        "bridge_strength": "STRONG_CORPUS_STRUCTURE_BRIDGE",
        "allowed_inference": "Prefer packet/spine/template versions over full-sentence prose.",
        "blocked_inference": "Do not infer any direct 469 phrase meaning from this book alone.",
    },
    {
        "bridge_id": "BEWARE_LANGUAGE_MATH_NUMERIC_BOOKS",
        "source_url": "https://tibia.fandom.com/wiki/Beware_of_the_Bonelords_%28Book%29",
        "source_type": "in_game_book_secondary_page",
        "source_claim": "Bonelord books contain only numbers and the language is also mathematics.",
        "supports_contig_phase": "slot/classifier and formula packet behavior",
        "bridge_strength": "STRONG_METHOD_BRIDGE",
        "allowed_inference": "Treat repeated slot/template packets as mathematical language structure.",
        "blocked_inference": "Do not gloss any slot marker as a word.",
    },
    {
        "bridge_id": "BEWARE_BLINKING_CODE_VARIABLE_UNIT",
        "source_url": "https://tibia.fandom.com/wiki/Beware_of_the_Bonelords_%28Book%29",
        "source_type": "in_game_book_secondary_page",
        "source_claim": "A blink could mean syllable, letter, or word.",
        "supports_contig_phase": "variable slot and endpoint unit size",
        "bridge_strength": "MODERATE_UNIT_BRIDGE",
        "allowed_inference": "Keep NAESE/O23/FNAAST units flexible until contrastive proof exists.",
        "blocked_inference": "Do not choose syllable, letter, or word value by intuition.",
    },
    {
        "bridge_id": "AWB_COMPLEX_FORMULA_SUBJECTIVE_VIEWER",
        "source_url": "https://tibia.fandom.com/wiki/A_Wrinkled_Bonelord/Transcripts",
        "source_type": "npc_transcript_secondary_page",
        "source_claim": "The Bonelord name is a complex formula that changes for the subjective viewer.",
        "supports_contig_phase": "formula endpoint and variant control",
        "bridge_strength": "MODERATE_FORMULA_VARIANT_BRIDGE",
        "allowed_inference": "Treat endpoint windows as formula/selector behavior when internally supported.",
        "blocked_inference": "Do not claim any endpoint is the race name.",
    },
    {
        "bridge_id": "THREAT_III_EXPERIMENT_ENDPOINTS",
        "source_url": "https://www.tibiawiki.com.br/wiki/The_Bonelord_Threat_III_%28Book%29",
        "source_type": "in_game_book_secondary_page",
        "source_claim": "Bonelord experiments produced endpoints, failures, abolitions, and destroyed evidence around undead transformations.",
        "supports_contig_phase": "endpoint window and experimental closure context",
        "bridge_strength": "WEAK_CONTEXT_BRIDGE",
        "allowed_inference": "Use only as a search direction for endpoint/closure language.",
        "blocked_inference": "Do not read O23/FNAAST as death, failure, monster, soul, or experiment.",
    },
]

CONTIG_VERSIONS = {
    "0": {
        "human_functional_version": (
            "A two-book slot/bridge pair: both books repeat a NAESE/C68 slot window with an R02 phase bridge. "
            "Humanly, this behaves like a repeated classifier or response-slot template, not a translated sentence."
        ),
        "bridge_ids": [
            "GREAT_CALCULATOR_COMPILED_LANGUAGE",
            "BEWARE_LANGUAGE_MATH_NUMERIC_BOOKS",
            "BEWARE_BLINKING_CODE_VARIABLE_UNIT",
        ],
        "confidence": "MODERATE_STRONG_FUNCTIONAL_PAIR",
    },
    "4": {
        "human_functional_version": (
            "A scoped endpoint packet: Book 13 enters an O23/FNAAST endpoint branch and Book 38 preserves the direct endpoint payload. "
            "Humanly, this is a terminal/closure window that must stay quarantined from global O23 meaning."
        ),
        "bridge_ids": [
            "GREAT_CALCULATOR_COMPILED_LANGUAGE",
            "BEWARE_BLINKING_CODE_VARIABLE_UNIT",
            "AWB_COMPLEX_FORMULA_SUBJECTIVE_VIEWER",
            "THREAT_III_EXPERIMENT_ENDPOINTS",
        ],
        "confidence": "WEAK_MODERATE_SCOPED_ENDPOINT",
    },
    "5": {
        "human_functional_version": (
            "A formula-template handoff pair: Book 47 provides BENNA/IAVNALLBEE template context and Book 40 carries that into a BENNA formula bridge with LTAST boundary. "
            "Humanly, this is a ritual/mathematical formula handoff packet, not prose."
        ),
        "bridge_ids": [
            "GREAT_CALCULATOR_COMPILED_LANGUAGE",
            "BEWARE_LANGUAGE_MATH_NUMERIC_BOOKS",
            "AWB_COMPLEX_FORMULA_SUBJECTIVE_VIEWER",
        ],
        "confidence": "MODERATE_FORMULA_TEMPLATE_PAIR",
    },
}


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q34_remaining_contig_functional_versions_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q30_run_id INTEGER NOT NULL,
            q32_run_id INTEGER NOT NULL,
            q33_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            target_contigs_json TEXT NOT NULL,
            target_book_count INTEGER NOT NULL,
            source_bridge_count INTEGER NOT NULL,
            human_functional_version_count INTEGER NOT NULL,
            weak_endpoint_count INTEGER NOT NULL,
            exact_sequence_bridge_count INTEGER NOT NULL,
            component_gloss_allowed_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            all_q30_contigs_have_human_version INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q34_remaining_contig_functional_versions_v1_sources (
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

        CREATE TABLE IF NOT EXISTS human_q34_remaining_contig_functional_versions_v1_contigs (
            run_id INTEGER NOT NULL,
            basecontigid TEXT NOT NULL,
            booksinorder TEXT NOT NULL,
            structural_narrative TEXT NOT NULL,
            human_functional_version TEXT NOT NULL,
            confidence TEXT NOT NULL,
            source_bridge_ids_json TEXT NOT NULL,
            translation_use TEXT NOT NULL,
            blocked_claims_json TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, basecontigid)
        );

        CREATE TABLE IF NOT EXISTS human_q34_remaining_contig_functional_versions_v1_books (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            basecontigid TEXT NOT NULL,
            contig_position INTEGER NOT NULL,
            compiled_stratum TEXT NOT NULL,
            likely_speech_act TEXT NOT NULL,
            plausible_human_reading TEXT NOT NULL,
            row0_markers_json TEXT NOT NULL,
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


def load_contig(conn: sqlite3.Connection, q30_run_id: int, contig_id: str) -> sqlite3.Row:
    row = conn.execute(
        """
        SELECT *
        FROM human_q30_great_calculator_compiled_corpus_spine_map_v1_contigs
        WHERE run_id=? AND basecontigid=?
        """,
        (q30_run_id, contig_id),
    ).fetchone()
    if row is None:
        raise RuntimeError(f"missing Q30 contig {contig_id}")
    return row


def load_book(conn: sqlite3.Connection, q30_run_id: int, bookid: str) -> sqlite3.Row:
    row = conn.execute(
        """
        SELECT *
        FROM human_q30_great_calculator_compiled_corpus_spine_map_v1_books
        WHERE run_id=? AND bookid=?
        """,
        (q30_run_id, bookid),
    ).fetchone()
    if row is None:
        raise RuntimeError(f"missing Q30 book {bookid}")
    return row


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q30 = latest_row(conn, "human_q30_great_calculator_compiled_corpus_spine_map_v1_runs")
    q32 = latest_row(conn, "human_q32_contig1_source_bridge_probe_v1_runs")
    q33 = latest_row(conn, "human_q33_branch_formula_source_bridge_probe_v1_runs")
    audit = latest_row(conn, "human_translation_completion_audit_v5_runs")
    q30_run_id = int(q30["run_id"])

    contig_items: list[dict[str, object]] = []
    book_rows: list[dict[str, object]] = []
    for contig_id in TARGET_CONTIGS:
        contig = load_contig(conn, q30_run_id, contig_id)
        version = CONTIG_VERSIONS[contig_id]
        order = str(contig["booksinorder"]).split("->")
        contig_items.append(
            {
                "basecontigid": contig_id,
                "booksinorder": str(contig["booksinorder"]),
                "structural_narrative": str(contig["structural_narrative"]),
                "human_functional_version": str(version["human_functional_version"]),
                "confidence": str(version["confidence"]),
                "source_bridge_ids": version["bridge_ids"],
                "translation_use": "human functional contig version only; no component or sentence gloss",
                "blocked_claims": [
                    "component_gloss",
                    "sentence_translation",
                    "global_O23_meaning",
                    "NAESE_as_word",
                    "BENNA_as_word",
                    "FNAAST_as_word",
                    "endpoint_semantics",
                ],
                "evidence": {"q30_contig": dict(contig), "source_bridge_ids": version["bridge_ids"]},
            }
        )
        for index, bookid in enumerate(order):
            book = load_book(conn, q30_run_id, bookid)
            book_rows.append(
                {
                    "bookid": bookid,
                    "basecontigid": contig_id,
                    "contig_position": index + 1,
                    "compiled_stratum": str(book["compiled_stratum"]),
                    "likely_speech_act": str(book["likely_speech_act"]),
                    "plausible_human_reading": str(book["plausible_human_reading"]),
                    "row0_markers_json": str(book["row0_markers_json"]),
                    "evidence": {"q30_book": dict(book)},
                }
            )

    exact_sequence_bridge_count = 0
    component_gloss_allowed_count = 0
    canonical_promotion_allowed_count = 0
    weak_endpoint_count = sum(1 for item in contig_items if str(item["confidence"]).startswith("WEAK"))
    all_q30_contigs_have_human_version = 1
    decision = (
        "Q34_ALL_Q30_CONTIGS_HAVE_SOURCE_ANCHORED_HUMAN_FUNCTIONAL_VERSIONS_NO_GLOSS"
        if len(contig_items) == 3
        and len(book_rows) == 6
        and exact_sequence_bridge_count == 0
        and component_gloss_allowed_count == 0
        and canonical_promotion_allowed_count == 0
        and int(audit["promoted_gloss_count"]) == 0
        and all_q30_contigs_have_human_version == 1
        else "Q34_REMAINING_CONTIG_FUNCTIONAL_VERSIONS_REQUIRES_REVIEW"
    )
    payload = {
        "question": "Can the remaining exact Q30 contigs be assigned human functional versions without unsafe glosses?",
        "answer": "Yes. Together with Q32 and Q33, all six Q30 exact contigs now have source-anchored human functional versions.",
        "allowed_reading": "Use all exact contigs as functional versions and source-search spines.",
        "blocked_reading": "No component gloss, no sentence translation, and no endpoint semantics from context-only sources.",
        "weakness": "Contig 4 remains weaker and scoped because O23/FNAAST has endpoint context but no exact external meaning.",
        "next_action": "Promote a contig-level human shadow atlas only after joining Q32, Q33, and Q34 into one audited view.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q34_remaining_contig_functional_versions_v1_runs (
                created_at, decision, q30_run_id, q32_run_id, q33_run_id,
                completion_audit_run_id, target_contigs_json, target_book_count,
                source_bridge_count, human_functional_version_count,
                weak_endpoint_count, exact_sequence_bridge_count,
                component_gloss_allowed_count, canonical_promotion_allowed_count,
                all_q30_contigs_have_human_version, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                q30_run_id,
                int(q32["run_id"]),
                int(q33["run_id"]),
                int(audit["run_id"]),
                j(TARGET_CONTIGS),
                len(book_rows),
                len(SOURCE_BRIDGES),
                len(contig_items),
                weak_endpoint_count,
                exact_sequence_bridge_count,
                component_gloss_allowed_count,
                canonical_promotion_allowed_count,
                all_q30_contigs_have_human_version,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q34_remaining_contig_functional_versions_v1_sources (
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
            INSERT INTO human_q34_remaining_contig_functional_versions_v1_contigs (
                run_id, basecontigid, booksinorder, structural_narrative,
                human_functional_version, confidence, source_bridge_ids_json,
                translation_use, blocked_claims_json, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    str(item["basecontigid"]),
                    str(item["booksinorder"]),
                    str(item["structural_narrative"]),
                    str(item["human_functional_version"]),
                    str(item["confidence"]),
                    j(item["source_bridge_ids"]),
                    str(item["translation_use"]),
                    j(item["blocked_claims"]),
                    j(item["evidence"]),
                )
                for item in contig_items
            ],
        )
        conn.executemany(
            """
            INSERT INTO human_q34_remaining_contig_functional_versions_v1_books (
                run_id, bookid, basecontigid, contig_position,
                compiled_stratum, likely_speech_act, plausible_human_reading,
                row0_markers_json, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    str(item["bookid"]),
                    str(item["basecontigid"]),
                    int(item["contig_position"]),
                    str(item["compiled_stratum"]),
                    str(item["likely_speech_act"]),
                    str(item["plausible_human_reading"]),
                    str(item["row0_markers_json"]),
                    j(item["evidence"]),
                )
                for item in book_rows
            ],
        )

    print(
        j(
            {
                "run_id": run_id,
                "decision": decision,
                "target_contigs": TARGET_CONTIGS,
                "target_book_count": len(book_rows),
                "source_bridge_count": len(SOURCE_BRIDGES),
                "human_functional_version_count": len(contig_items),
                "weak_endpoint_count": weak_endpoint_count,
                "exact_sequence_bridge_count": exact_sequence_bridge_count,
                "component_gloss_allowed_count": component_gloss_allowed_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
                "all_q30_contigs_have_human_version": all_q30_contigs_have_human_version,
            }
        )
    )


if __name__ == "__main__":
    main()
