#!/usr/bin/env python3
"""Q30: map the Great Calculator route as a compiled-corpus shadow model."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

MARKERS = [
    "BENNA",
    "NAESE",
    "VNCTIIN",
    "VINVIN",
    "LTAST",
    "TTNVVN",
    "TIINNEF",
    "TAESESTIEN",
    "VNSBLFSINNAI",
    "C86",
    "C68",
    "O23",
    "R20",
    "R02",
    "3478",
]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q30_great_calculator_compiled_corpus_spine_map_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q22_run_id INTEGER NOT NULL,
            q28_run_id INTEGER NOT NULL,
            q29_run_id INTEGER NOT NULL,
            atlas_v6_run_id INTEGER NOT NULL,
            contig_run_id INTEGER NOT NULL,
            contig_narrative_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            book_count INTEGER NOT NULL,
            contig_supported_book_count INTEGER NOT NULL,
            contig_packet_count INTEGER NOT NULL,
            stratum_count INTEGER NOT NULL,
            great_calculator_anchor_present INTEGER NOT NULL,
            external_candidate_structural_allowed INTEGER NOT NULL,
            external_candidate_semantic_allowed INTEGER NOT NULL,
            canonical_promoted_gloss_count INTEGER NOT NULL,
            human_shadow_ready_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q30_great_calculator_compiled_corpus_spine_map_v1_books (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            compiled_stratum TEXT NOT NULL,
            contig_ids_json TEXT NOT NULL,
            source_layer TEXT NOT NULL,
            likely_speech_act TEXT NOT NULL,
            plausible_human_reading TEXT NOT NULL,
            row0_markers_json TEXT NOT NULL,
            translation_use TEXT NOT NULL,
            next_source_question TEXT NOT NULL,
            promotion_status TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        );

        CREATE TABLE IF NOT EXISTS human_q30_great_calculator_compiled_corpus_spine_map_v1_contigs (
            run_id INTEGER NOT NULL,
            basecontigid TEXT NOT NULL,
            booksinorder TEXT NOT NULL,
            compiled_sequence_json TEXT NOT NULL,
            structural_narrative TEXT NOT NULL,
            model_use TEXT NOT NULL,
            next_action TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, basecontigid)
        );
        """
    )


def latest_run_id(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT max(run_id) FROM {table}").fetchone()
    if row is None or row[0] is None:
        raise RuntimeError(f"missing required run: {table}")
    return int(row[0])


def latest_row(conn: sqlite3.Connection, table: str) -> sqlite3.Row:
    row = conn.execute(f"SELECT * FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    if row is None:
        raise RuntimeError(f"missing required row: {table}")
    return row


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return (
        conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (table,),
        ).fetchone()
        is not None
    )


def classify_stratum(row: sqlite3.Row, row0: sqlite3.Row | None) -> str:
    text = " ".join(
        [
            str(row["source_layer"]),
            str(row["likely_speech_act"]),
            str(row["plausible_human_reading"]),
            str(row["support_level"]),
            str(row0["token_text"] if row0 is not None else ""),
            str(row0["symbol_text"] if row0 is not None else ""),
        ]
    ).upper()
    if "NAESE" in text and "BENNA" in text:
        return "COMPOSITE_SLOT_FORMULA_PACKET"
    if "BOOK30" in text or "VNSBLFSINNAI" in text or "TAESESTIEN" in text or "FAMILY SPINE" in text:
        return "FAMILY_SPINE_PACKET"
    if "C86" in text or "VNCTIIN" in text or "PAYLOAD" in text or "CONTEXT CORRIDOR" in text:
        return "PAYLOAD_CONTEXT_CORRIDOR"
    if "NAESE" in text or "SLOT" in text:
        return "SLOT_CLASSIFIER_PACKET"
    if "BENNA" in text or "FORMULA" in text:
        return "FORMULA_HANDOFF_PACKET"
    if "VINVIN" in text or "R20" in text or "R02" in text or "TIINNEF" in text or "3478" in text or "PHASE" in text:
        return "BRANCH_PHASE_CONTROL_PACKET"
    if "LOCAL PAIR" in text or "MICROTEMPLATE" in text or "TEMPLATE ALIGNMENT" in text:
        return "PAIR_TEMPLATE_ALIGNMENT_PACKET"
    if "DISPLAY" in text or "AUDIT" in text or "BOUNDARY" in text or "LTAST" in text or "TTNVVN" in text:
        return "DISPLAY_BOUNDARY_AUDIT_PACKET"
    return "RESIDUAL_COMPILED_FRAGMENT_PACKET"


def next_question(stratum: str) -> str:
    questions = {
        "COMPOSITE_SLOT_FORMULA_PACKET": (
            "Search in-game books/quests for a slot-to-formula or answer-to-ritual bridge before drafting prose."
        ),
        "FAMILY_SPINE_PACKET": (
            "Search Great Calculator and Hellgate-adjacent books for collected-language or repeated-fragment framing."
        ),
        "PAYLOAD_CONTEXT_CORRIDOR": (
            "Look for an in-game context that explains C86/VNCTIIN as a corridor, payload opener, or branch context."
        ),
        "SLOT_CLASSIFIER_PACKET": (
            "Look for a source-backed contrast where the slot changes while surrounding formula structure remains stable."
        ),
        "FORMULA_HANDOFF_PACKET": (
            "Look for ritual, mathematical, or register sources that explain formula handoff without lexical glossing."
        ),
        "BRANCH_PHASE_CONTROL_PACKET": (
            "Look for source-backed phase/branch markers, especially around 3478, TIINNEF, R20, or R02 contexts."
        ),
        "PAIR_TEMPLATE_ALIGNMENT_PACKET": (
            "Look for paired book placement, repeated book families, or local shelf ordering that explains the pair."
        ),
        "DISPLAY_BOUNDARY_AUDIT_PACKET": (
            "Look for evidence that the line is display/boundary material before treating it as message payload."
        ),
        "RESIDUAL_COMPILED_FRAGMENT_PACKET": (
            "Use only as a compiled fragment until a stronger source bridge or contrastive family appears."
        ),
    }
    return questions[stratum]


def marker_hits(row0: sqlite3.Row | None) -> list[str]:
    if row0 is None:
        return []
    haystack = f"{row0['token_text']} {row0['symbol_text']}"
    return [marker for marker in MARKERS if marker in haystack]


def contig_map(conn: sqlite3.Connection, contig_run_id: int) -> tuple[dict[str, list[str]], list[sqlite3.Row]]:
    rows = list(
        conn.execute(
            """
            SELECT *
            FROM contig_max_overlap_items
            WHERE run_id=?
            ORDER BY CAST(basecontigid AS INTEGER)
            """,
            (contig_run_id,),
        )
    )
    by_book: dict[str, list[str]] = {}
    for row in rows:
        for bookid in str(row["booksinorder"]).split("->"):
            by_book.setdefault(bookid, []).append(str(row["basecontigid"]))
    return by_book, rows


def load_atlas(conn: sqlite3.Connection, run_id: int) -> list[sqlite3.Row]:
    return list(
        conn.execute(
            """
            SELECT *
            FROM human_translation_atlas_v6_items
            WHERE run_id=? AND target_kind='book'
            ORDER BY CAST(target_id AS INTEGER)
            """,
            (run_id,),
        )
    )


def load_row0(conn: sqlite3.Connection) -> dict[str, sqlite3.Row]:
    run_id = latest_run_id(conn, "row0_variant_book_tokens")
    return {
        str(row["bookid"]): row
        for row in conn.execute(
            """
            SELECT *
            FROM row0_variant_book_tokens
            WHERE run_id=?
            """,
            (run_id,),
        )
    }


def load_contig_narratives(conn: sqlite3.Connection, run_id: int) -> dict[str, sqlite3.Row]:
    if not table_exists(conn, "contig_structural_narrative_v1_items"):
        return {}
    return {
        str(row["basecontigid"]): row
        for row in conn.execute(
            """
            SELECT *
            FROM contig_structural_narrative_v1_items
            WHERE run_id=?
            """,
            (run_id,),
        )
    }


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q22 = latest_row(conn, "human_q22_cross_quest_shadow_route_prioritization_v1_runs")
    q28 = latest_row(conn, "human_q28_external_candidate_contig_gate_benchmark_v1_runs")
    q29 = latest_row(conn, "human_q29_external_candidate_lore_term_search_audit_v1_runs")
    atlas = latest_row(conn, "human_translation_atlas_v6_runs")
    audit = latest_row(conn, "human_translation_completion_audit_v5_runs")
    contig_run_id = latest_run_id(conn, "contig_max_overlap_items")
    contig_narrative_run_id = latest_run_id(conn, "contig_structural_narrative_v1_items")

    anchor = conn.execute(
        """
        SELECT *
        FROM human_ingame_anchor_corpus_v1_items
        WHERE anchor_id='GREAT_CALCULATOR_GATHER_LANGUAGE'
        ORDER BY run_id DESC
        LIMIT 1
        """
    ).fetchone()
    if anchor is None:
        raise RuntimeError("missing GREAT_CALCULATOR_GATHER_LANGUAGE anchor")

    rows = load_atlas(conn, int(atlas["run_id"]))
    row0_by_book = load_row0(conn)
    contigs_by_book, contig_rows = contig_map(conn, contig_run_id)
    contig_narratives = load_contig_narratives(conn, contig_narrative_run_id)

    book_items: list[dict[str, object]] = []
    stratum_counts: dict[str, int] = {}
    for row in rows:
        bookid = str(row["target_id"])
        row0 = row0_by_book.get(bookid)
        stratum = classify_stratum(row, row0)
        stratum_counts[stratum] = stratum_counts.get(stratum, 0) + 1
        contig_ids = contigs_by_book.get(bookid, [])
        book_items.append(
            {
                "bookid": bookid,
                "compiled_stratum": stratum,
                "contig_ids": contig_ids,
                "source_layer": str(row["source_layer"]),
                "likely_speech_act": str(row["likely_speech_act"]),
                "plausible_human_reading": str(row["plausible_human_reading"]),
                "row0_markers": marker_hits(row0),
                "translation_use": (
                    "human_shadow_functional_version_only; use as source-search prompt, not canonical prose"
                ),
                "next_source_question": next_question(stratum),
                "promotion_status": str(row["promotion_status"]),
                "evidence": {
                    "anchor": dict(anchor),
                    "atlas_item": dict(row),
                    "row0": dict(row0) if row0 is not None else None,
                    "contig_ids": contig_ids,
                },
            }
        )

    contig_items: list[dict[str, object]] = []
    by_book = {str(item["bookid"]): item for item in book_items}
    for contig in contig_rows:
        order = str(contig["booksinorder"]).split("->")
        sequence = [
            {
                "bookid": bookid,
                "compiled_stratum": by_book[bookid]["compiled_stratum"],
                "likely_speech_act": by_book[bookid]["likely_speech_act"],
                "plausible_human_reading": by_book[bookid]["plausible_human_reading"],
            }
            for bookid in order
            if bookid in by_book
        ]
        narrative = contig_narratives.get(str(contig["basecontigid"]))
        contig_items.append(
            {
                "basecontigid": str(contig["basecontigid"]),
                "booksinorder": str(contig["booksinorder"]),
                "compiled_sequence": sequence,
                "structural_narrative": (
                    str(narrative["structural_narrative"])
                    if narrative is not None
                    else "Exact max-overlap contig with no separate structural narrative row."
                ),
                "model_use": (
                    "source-search spine packet; external candidate may be used only for adversarial continuity"
                ),
                "next_action": (
                    "Use the ordered packet to search for in-game book/quest parallels; reject any prose that skips this source step."
                ),
                "evidence": {
                    "contig_max_overlap": dict(contig),
                    "contig_narrative": dict(narrative) if narrative is not None else None,
                    "q28_structural_allowed": int(q28["structural_audit_use_allowed_count"]),
                    "q29_semantic_allowed": int(q29["canonical_promotion_allowed_count"]),
                },
            }
        )

    external_candidate_semantic_allowed = int(q28["semantic_translation_use_allowed_count"]) or int(
        q29["canonical_promotion_allowed_count"]
    )
    canonical_promoted_gloss_count = int(audit["promoted_gloss_count"])
    canonical_promotion_allowed_count = 0
    decision = (
        "Q30_GREAT_CALCULATOR_COMPILED_CORPUS_MODEL_READY_AS_HUMAN_SHADOW_NO_GLOSS"
        if len(book_items) == 70
        and anchor is not None
        and int(q28["structural_audit_use_allowed_count"]) == 1
        and external_candidate_semantic_allowed == 0
        and canonical_promoted_gloss_count == 0
        else "Q30_GREAT_CALCULATOR_COMPILED_CORPUS_MODEL_REQUIRES_REVIEW"
    )
    payload = {
        "question": "Can the Great Calculator route support human translation work without pretending the corpus is solved?",
        "answer": (
            "Yes as a compiled-corpus shadow model: translate books by function, spine, packet, and source-search question."
        ),
        "allowed_reading": (
            "Use the Great Calculator anchor to prefer formula/spine/fragment packets over one continuous prose narrative."
        ),
        "blocked_reading": (
            "Do not infer direct plaintext from the Great Calculator book or from the external German/MHG candidate."
        ),
        "stratum_counts": stratum_counts,
        "next_action": (
            "Use high-confidence packets and exact contigs to drive source searches and controlled human paraphrases."
        ),
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q30_great_calculator_compiled_corpus_spine_map_v1_runs (
                created_at, decision, q22_run_id, q28_run_id, q29_run_id,
                atlas_v6_run_id, contig_run_id, contig_narrative_run_id,
                completion_audit_run_id, book_count, contig_supported_book_count,
                contig_packet_count, stratum_count, great_calculator_anchor_present,
                external_candidate_structural_allowed, external_candidate_semantic_allowed,
                canonical_promoted_gloss_count, human_shadow_ready_count,
                canonical_promotion_allowed_count, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                int(q22["run_id"]),
                int(q28["run_id"]),
                int(q29["run_id"]),
                int(atlas["run_id"]),
                contig_run_id,
                contig_narrative_run_id,
                int(audit["run_id"]),
                len(book_items),
                len(contigs_by_book),
                len(contig_items),
                len(stratum_counts),
                1,
                int(q28["structural_audit_use_allowed_count"]),
                external_candidate_semantic_allowed,
                canonical_promoted_gloss_count,
                len(book_items),
                canonical_promotion_allowed_count,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q30_great_calculator_compiled_corpus_spine_map_v1_books (
                run_id, bookid, compiled_stratum, contig_ids_json, source_layer,
                likely_speech_act, plausible_human_reading, row0_markers_json,
                translation_use, next_source_question, promotion_status,
                evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    str(item["bookid"]),
                    str(item["compiled_stratum"]),
                    j(item["contig_ids"]),
                    str(item["source_layer"]),
                    str(item["likely_speech_act"]),
                    str(item["plausible_human_reading"]),
                    j(item["row0_markers"]),
                    str(item["translation_use"]),
                    str(item["next_source_question"]),
                    str(item["promotion_status"]),
                    j(item["evidence"]),
                )
                for item in book_items
            ],
        )
        conn.executemany(
            """
            INSERT INTO human_q30_great_calculator_compiled_corpus_spine_map_v1_contigs (
                run_id, basecontigid, booksinorder, compiled_sequence_json,
                structural_narrative, model_use, next_action, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    str(item["basecontigid"]),
                    str(item["booksinorder"]),
                    j(item["compiled_sequence"]),
                    str(item["structural_narrative"]),
                    str(item["model_use"]),
                    str(item["next_action"]),
                    j(item["evidence"]),
                )
                for item in contig_items
            ],
        )

    print(
        j(
            {
                "run_id": run_id,
                "decision": decision,
                "book_count": len(book_items),
                "contig_supported_book_count": len(contigs_by_book),
                "contig_packet_count": len(contig_items),
                "stratum_count": len(stratum_counts),
                "stratum_counts": stratum_counts,
                "external_candidate_structural_allowed": int(q28["structural_audit_use_allowed_count"]),
                "external_candidate_semantic_allowed": external_candidate_semantic_allowed,
                "canonical_promoted_gloss_count": canonical_promoted_gloss_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
            }
        )
    )


if __name__ == "__main__":
    main()
