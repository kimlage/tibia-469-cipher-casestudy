#!/usr/bin/env python3
"""Bind external 469 phrases to the human-translation route layer.

This does not translate the phrases. It gives the shadow workflow a typed,
source-aware corpus for Avar Tar, Chayenne, Knightmare, Poll, and NPC sound
anchors, using the latest row0 projection/LCS runs as mechanical evidence.
"""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"


PHRASE_META = {
    "AVAR_ORIGINAL_POEM": {
        "source_id": "TIBIAQA_AVAR_TAR_POEM",
        "source_url": "https://www.tibiaqa.com/20625/which-npcs-are-speaking-bonelord-469-language",
        "source_label": "Avar Tar numeric poem",
        "in_game_anchor": "Avar Tar response to Bonelord language keyword",
        "route_ids": ["R1_INGAME_CONTEXT_CORPUS", "R2_NPC_PHRASE_STYLE_COMPARATOR", "R10_EXTERNAL_EXACT_GLOSS_ROUTE"],
        "candidate_use": "out-of-book poem/register comparator; not Hellgate book plaintext",
        "risk": "fansite transcription and NPC register; no exact semantic attestation",
    },
    "CHAYENNE_REPLY": {
        "source_id": "TIBIAWIKI_BR_469_SYNTHESIS",
        "source_url": "https://www.tibiawiki.com.br/469",
        "source_label": "Chayenne 2009 numeric reply",
        "in_game_anchor": "CipSoft/content-team interview answer discussed as 469",
        "route_ids": ["R2_NPC_PHRASE_STYLE_COMPARATOR", "R3_MATHEMAGIC_OPERATOR_GRID", "R10_EXTERNAL_EXACT_GLOSS_ROUTE"],
        "candidate_use": "strong shape holdout for Books 8/37/63/66; structural only",
        "risk": "near-primary/public synthesis; no explicit human meaning",
    },
    "KNIGHTMARE_PHRASE": {
        "source_id": "TIBIAWIKI_BR_469_SYNTHESIS",
        "source_url": "https://www.tibiawiki.com.br/469",
        "source_label": "Knightmare anniversary phrase",
        "in_game_anchor": "Knightmare NPC/event phrase plus 3478 lore",
        "route_ids": ["R2_NPC_PHRASE_STYLE_COMPARATOR", "R4_NAME_AS_FORMULA", "R10_EXTERNAL_EXACT_GLOSS_ROUTE"],
        "candidate_use": "proper-name/formula constraint and external phrase holdout",
        "risk": "source is synthesized; no response gloss",
    },
    "POLL_2020_OPTION_C": {
        "source_id": "POLL_OPTION_C_EXTERNAL",
        "source_url": "https://tibia.fandom.com/wiki/469",
        "source_label": "Poll option C external phrase",
        "in_game_anchor": "external phrase-level GT target used by the project",
        "route_ids": ["R2_NPC_PHRASE_STYLE_COMPARATOR", "R10_EXTERNAL_EXACT_GLOSS_ROUTE"],
        "candidate_use": "phrase-level holdout only",
        "risk": "not an in-game book anchor by itself",
    },
    "ELDER_BONELORD_SOUNDS": {
        "source_id": "NPC_SOUND_ANCHOR",
        "source_url": "https://tibia.fandom.com/wiki/469",
        "source_label": "Elder Bonelord/NPC sound anchor",
        "in_game_anchor": "Bonelord-family NPC utterance",
        "route_ids": ["R2_NPC_PHRASE_STYLE_COMPARATOR", "R9_ZERO_ONE_TABOO_INVERSION", "R10_EXTERNAL_EXACT_GLOSS_ROUTE"],
        "candidate_use": "NPC-only speech/sound comparator",
        "risk": "NPC sound context does not imply book semantics",
    },
}


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_external_phrase_corpus_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            projection_run_id INTEGER NOT NULL,
            lcs_run_id INTEGER NOT NULL,
            chayenne_gate_run_id INTEGER,
            phrase_count INTEGER NOT NULL,
            exact_book_hit_count INTEGER NOT NULL,
            strong_shape_overlap_phrase_count INTEGER NOT NULL,
            accepted_semantic_gloss_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_external_phrase_corpus_v1_items (
            run_id INTEGER NOT NULL,
            phrase_id TEXT NOT NULL,
            raw_digits TEXT NOT NULL,
            source_id TEXT NOT NULL,
            source_url TEXT NOT NULL,
            source_label TEXT NOT NULL,
            in_game_anchor TEXT NOT NULL,
            route_ids_json TEXT NOT NULL,
            row0_global_symbols TEXT NOT NULL,
            word_symbols_json TEXT NOT NULL,
            unknown_codes_json TEXT NOT NULL,
            exact_book_hits_json TEXT NOT NULL,
            strong_overlap_books_json TEXT NOT NULL,
            shared_blocks_json TEXT NOT NULL,
            candidate_use TEXT NOT NULL,
            risk TEXT NOT NULL,
            next_action TEXT NOT NULL,
            semantic_gloss_status TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, phrase_id)
        );
        """
    )


def max_id(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT max(run_id) AS run_id FROM {table}").fetchone()
    if row is None or row["run_id"] is None:
        raise RuntimeError(f"missing required table/run: {table}")
    return int(row["run_id"])


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    projection_run_id = max_id(conn, "confirmed_external_row0_projection_items")
    lcs_run_id = max_id(conn, "external_row0_lcs_probe_items")
    chayenne_gate_run_id = None
    row = conn.execute("SELECT max(run_id) AS run_id FROM chayenne_external_shape_gate_runs").fetchone()
    if row and row["run_id"] is not None:
        chayenne_gate_run_id = int(row["run_id"])

    projections = {
        row["phrase_id"]: dict(row)
        for row in conn.execute(
            """
            SELECT *
            FROM confirmed_external_row0_projection_items
            WHERE run_id=?
            """,
            (projection_run_id,),
        ).fetchall()
    }
    lcs_rows = conn.execute(
        """
        SELECT *
        FROM external_row0_lcs_probe_items
        WHERE run_id=?
        ORDER BY phrase_id, CAST(bookid AS INTEGER)
        """,
        (lcs_run_id,),
    ).fetchall()
    overlaps: dict[str, list[dict[str, object]]] = {}
    for row in lcs_rows:
        if row["candidate_status"] == "STRONG_EXTERNAL_SHAPE_OVERLAP":
            overlaps.setdefault(row["phrase_id"], []).append(dict(row))

    phrase_ids = [pid for pid in sorted(PHRASE_META) if pid in projections]
    exact_count = sum(1 for pid in phrase_ids if json.loads(projections[pid]["exact_book_hits_json"] or "[]"))
    strong_phrase_count = sum(1 for pid in phrase_ids if overlaps.get(pid))

    payload = {
        "principle": "external phrases are source-aware human-route evidence, not direct book translations",
        "phrase_ids": phrase_ids,
        "projection_run_id": projection_run_id,
        "lcs_run_id": lcs_run_id,
        "chayenne_gate_run_id": chayenne_gate_run_id,
    }
    cur = conn.execute(
        """
        INSERT INTO human_external_phrase_corpus_v1_runs
        (created_at, decision, projection_run_id, lcs_run_id, chayenne_gate_run_id,
         phrase_count, exact_book_hit_count, strong_shape_overlap_phrase_count,
         accepted_semantic_gloss_count, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            now(),
            "HUMAN_EXTERNAL_PHRASE_CORPUS_READY_NO_GLOSS",
            projection_run_id,
            lcs_run_id,
            chayenne_gate_run_id,
            len(phrase_ids),
            exact_count,
            strong_phrase_count,
            0,
            json.dumps(payload, ensure_ascii=False, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)

    for pid in phrase_ids:
        meta = PHRASE_META[pid]
        projection = projections[pid]
        strong = overlaps.get(pid, [])
        strong_books = [
            {
                "bookid": row["bookid"],
                "ratio": row["lcs_ratio_phrase"],
                "longest_block_len": row["longest_block_len"],
            }
            for row in strong
        ]
        shared_blocks = sorted({row["shared_block"] for row in strong if row["shared_block"]})
        if strong:
            next_action = "Use as structural holdout; test shared shape against route claims before any human paraphrase."
        elif json.loads(projection["exact_book_hits_json"] or "[]"):
            next_action = "Exact book hit requires source/context review before any semantic use."
        else:
            next_action = "Keep as external-only comparator; do not promote book semantics."
        evidence = {
            "projection_status": projection["projection_status"],
            "projection_recommendation": projection["recommendation"],
            "projection_payload": projection["payload_json"],
            "strong_overlap_count": len(strong),
        }
        conn.execute(
            """
            INSERT INTO human_external_phrase_corpus_v1_items
            (run_id, phrase_id, raw_digits, source_id, source_url, source_label,
             in_game_anchor, route_ids_json, row0_global_symbols, word_symbols_json,
             unknown_codes_json, exact_book_hits_json, strong_overlap_books_json,
             shared_blocks_json, candidate_use, risk, next_action,
             semantic_gloss_status, evidence_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                pid,
                projection["raw_digits"],
                meta["source_id"],
                meta["source_url"],
                meta["source_label"],
                meta["in_game_anchor"],
                json.dumps(meta["route_ids"], ensure_ascii=False, sort_keys=True),
                projection["global_symbols"],
                projection["word_symbols_json"],
                projection["unknown_codes_json"],
                projection["exact_book_hits_json"],
                json.dumps(strong_books, ensure_ascii=False, sort_keys=True),
                json.dumps(shared_blocks, ensure_ascii=False, sort_keys=True),
                meta["candidate_use"],
                meta["risk"],
                next_action,
                "NO_EXPLICIT_MEANING_NO_BOOK_PROMOTION",
                json.dumps(evidence, ensure_ascii=False, sort_keys=True),
            ),
        )

    conn.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": "HUMAN_EXTERNAL_PHRASE_CORPUS_READY_NO_GLOSS",
                "projection_run_id": projection_run_id,
                "lcs_run_id": lcs_run_id,
                "phrase_count": len(phrase_ids),
                "exact_book_hit_count": exact_count,
                "strong_shape_overlap_phrase_count": strong_phrase_count,
                "accepted_semantic_gloss_count": 0,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
