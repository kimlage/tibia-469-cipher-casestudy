#!/usr/bin/env python3
"""Q33: source-bridge branch/variant contigs through Wrinkled Bonelord formula lore."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
TARGET_CONTIGS = ["2", "3"]

SOURCE_BRIDGES = [
    {
        "bridge_id": "AWB_COMPLEX_FORMULA_SUBJECTIVE_VIEWER",
        "source_url": "https://tibia.fandom.com/wiki/A_Wrinkled_Bonelord/Transcripts",
        "source_type": "npc_transcript_secondary_page",
        "source_claim": "In Bonelord language the race name is a complex formula and changes for the subjective viewer.",
        "supports_contig_phase": "branch, variant-chain, and endpoint behavior",
        "bridge_strength": "STRONG_FORMULA_VARIANT_BRIDGE",
        "allowed_inference": "Use branch/variant packets as formula-view or selector behavior candidates.",
        "blocked_inference": "Do not claim VINVIN, R20, O23, C86, or any book encodes the race name.",
    },
    {
        "bridge_id": "AWB_LANGUAGE_MATHEMAGIC_PROCESSING",
        "source_url": "https://tibia.fandom.com/wiki/A_Wrinkled_Bonelord/Transcripts",
        "source_type": "npc_transcript_secondary_page",
        "source_claim": "The language relies on mathemagic and requires fast calculation to decipher even basic texts.",
        "supports_contig_phase": "operator/selector processing rather than direct prose",
        "bridge_strength": "STRONG_METHOD_BRIDGE",
        "allowed_inference": "Treat branch packets as objects to calculate/process, not read linearly.",
        "blocked_inference": "Do not promote a mathemagic output unless it improves held-out structure.",
    },
    {
        "bridge_id": "AWB_NUMBERS_LIFE_DEATH",
        "source_url": "https://tibia.fandom.com/wiki/A_Wrinkled_Bonelord/Transcripts",
        "source_type": "npc_transcript_secondary_page",
        "source_claim": "Numbers are essential; mastery of mathematics is mastery over life and death.",
        "supports_contig_phase": "numeric branch control with life/death research context",
        "bridge_strength": "MODERATE_CONTEXT_BRIDGE",
        "allowed_inference": "Let numeric branch packets remain compatible with life/death control themes.",
        "blocked_inference": "Do not gloss any branch marker as life, death, number, or mastery.",
    },
    {
        "bridge_id": "BEWARE_BLINKING_CODE_VARIABLE_UNIT",
        "source_url": "https://tibia.fandom.com/wiki/Beware_of_the_Bonelords_%28Book%29",
        "source_type": "in_game_book_secondary_page",
        "source_claim": "A blink could mean some syllable, letter, or word, making the language not only language but mathematics.",
        "supports_contig_phase": "variable unit size and branch ambiguity",
        "bridge_strength": "MODERATE_UNIT_BRIDGE",
        "allowed_inference": "Keep branch units flexible and avoid one-code-one-word assumptions.",
        "blocked_inference": "Do not choose syllable, letter, or word value without contrastive proof.",
    },
    {
        "bridge_id": "THREAT_II_RESEARCH_EXPERIMENTS",
        "source_url": "https://tibia.fandom.com/wiki/The_Bonelord_Threat_II_%28Book%29",
        "source_type": "in_game_book_secondary_page",
        "source_claim": "Bonelords improved their powers through research and experiments after relying too much on intuition.",
        "supports_contig_phase": "variant-chain as experimental/control sequence",
        "bridge_strength": "MODERATE_CONTEXT_BRIDGE",
        "allowed_inference": "Read branch endpoints as controlled variants or experiment steps in human shadow.",
        "blocked_inference": "Do not turn experiment lore into a direct phrase meaning.",
    },
]

HUMAN_VERSIONS = {
    "2": (
        "A branch/phase packet: the first line establishes a VINVIN-covered R20 context and the second extends it into a longer R20/R02 phase connector. "
        "Humanly, it behaves like a formula variant being carried to a phase endpoint, not like a standalone sentence."
    ),
    "3": (
        "A branch payload pair: two C86-opened VINVIN/R20 lines form a controlled variant chain, with the second book acting as the stronger endpoint. "
        "Humanly, it reads as a selector/branch endpoint packet under the Bonelord complex-formula model, not as lexical prose."
    ),
}


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q33_branch_formula_source_bridge_probe_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q30_run_id INTEGER NOT NULL,
            q32_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            target_contigs_json TEXT NOT NULL,
            target_book_count INTEGER NOT NULL,
            source_bridge_count INTEGER NOT NULL,
            strong_bridge_count INTEGER NOT NULL,
            moderate_bridge_count INTEGER NOT NULL,
            human_functional_version_count INTEGER NOT NULL,
            exact_sequence_bridge_count INTEGER NOT NULL,
            component_gloss_allowed_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q33_branch_formula_source_bridge_probe_v1_sources (
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

        CREATE TABLE IF NOT EXISTS human_q33_branch_formula_source_bridge_probe_v1_contigs (
            run_id INTEGER NOT NULL,
            basecontigid TEXT NOT NULL,
            booksinorder TEXT NOT NULL,
            structural_narrative TEXT NOT NULL,
            human_functional_version TEXT NOT NULL,
            source_bridge_ids_json TEXT NOT NULL,
            translation_use TEXT NOT NULL,
            blocked_claims_json TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, basecontigid)
        );

        CREATE TABLE IF NOT EXISTS human_q33_branch_formula_source_bridge_probe_v1_books (
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
    audit = latest_row(conn, "human_translation_completion_audit_v5_runs")
    q30_run_id = int(q30["run_id"])

    contigs: list[dict[str, object]] = []
    book_rows: list[dict[str, object]] = []
    for contig_id in TARGET_CONTIGS:
        contig = load_contig(conn, q30_run_id, contig_id)
        order = str(contig["booksinorder"]).split("->")
        source_bridge_ids = [source["bridge_id"] for source in SOURCE_BRIDGES]
        contigs.append(
            {
                "basecontigid": contig_id,
                "booksinorder": str(contig["booksinorder"]),
                "structural_narrative": str(contig["structural_narrative"]),
                "human_functional_version": HUMAN_VERSIONS[contig_id],
                "source_bridge_ids": source_bridge_ids,
                "translation_use": "human functional branch/formula version only; no component or sentence gloss",
                "blocked_claims": [
                    "component_gloss",
                    "sentence_translation",
                    "race_name_decoding",
                    "VINVIN_as_word",
                    "R20_as_word",
                    "C86_as_word",
                    "O23_as_word",
                ],
                "evidence": {"q30_contig": dict(contig), "source_bridge_ids": source_bridge_ids},
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

    strong_bridge_count = sum(1 for source in SOURCE_BRIDGES if source["bridge_strength"].startswith("STRONG"))
    moderate_bridge_count = sum(1 for source in SOURCE_BRIDGES if source["bridge_strength"].startswith("MODERATE"))
    exact_sequence_bridge_count = 0
    component_gloss_allowed_count = 0
    canonical_promotion_allowed_count = 0
    decision = (
        "Q33_BRANCH_FORMULA_SOURCE_BRIDGE_SUPPORTS_CONTIG2_3_HUMAN_SHADOW_NO_GLOSS"
        if len(contigs) == 2
        and len(book_rows) == 4
        and strong_bridge_count >= 2
        and moderate_bridge_count >= 2
        and exact_sequence_bridge_count == 0
        and component_gloss_allowed_count == 0
        and canonical_promotion_allowed_count == 0
        and int(audit["promoted_gloss_count"]) == 0
        else "Q33_BRANCH_FORMULA_SOURCE_BRIDGE_REQUIRES_REVIEW"
    )
    payload = {
        "question": "Can branch/variant contigs be given human functional versions anchored in Wrinkled Bonelord formula lore?",
        "answer": "Yes for contigs 2 and 3 as branch/formula shadow versions only.",
        "allowed_reading": "Use AWB complex-formula and mathemagic lines to read VINVIN/R20/C86 packets as branch/variant/endpoint behavior.",
        "blocked_reading": "No race-name decoding, no component gloss, and no sentence-level translation.",
        "next_action": "Search exact in-game contrasts where a formula changes by viewer, name, branch, or endpoint before strengthening any component.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q33_branch_formula_source_bridge_probe_v1_runs (
                created_at, decision, q30_run_id, q32_run_id,
                completion_audit_run_id, target_contigs_json,
                target_book_count, source_bridge_count, strong_bridge_count,
                moderate_bridge_count, human_functional_version_count,
                exact_sequence_bridge_count, component_gloss_allowed_count,
                canonical_promotion_allowed_count, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                q30_run_id,
                int(q32["run_id"]),
                int(audit["run_id"]),
                j(TARGET_CONTIGS),
                len(book_rows),
                len(SOURCE_BRIDGES),
                strong_bridge_count,
                moderate_bridge_count,
                len(contigs),
                exact_sequence_bridge_count,
                component_gloss_allowed_count,
                canonical_promotion_allowed_count,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q33_branch_formula_source_bridge_probe_v1_sources (
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
            INSERT INTO human_q33_branch_formula_source_bridge_probe_v1_contigs (
                run_id, basecontigid, booksinorder, structural_narrative,
                human_functional_version, source_bridge_ids_json,
                translation_use, blocked_claims_json, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    str(item["basecontigid"]),
                    str(item["booksinorder"]),
                    str(item["structural_narrative"]),
                    str(item["human_functional_version"]),
                    j(item["source_bridge_ids"]),
                    str(item["translation_use"]),
                    j(item["blocked_claims"]),
                    j(item["evidence"]),
                )
                for item in contigs
            ],
        )
        conn.executemany(
            """
            INSERT INTO human_q33_branch_formula_source_bridge_probe_v1_books (
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
                "strong_bridge_count": strong_bridge_count,
                "moderate_bridge_count": moderate_bridge_count,
                "human_functional_version_count": len(contigs),
                "exact_sequence_bridge_count": exact_sequence_bridge_count,
                "component_gloss_allowed_count": component_gloss_allowed_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
            }
        )
    )


if __name__ == "__main__":
    main()
