#!/usr/bin/env python3
"""Q44: consolidate Chayenne register-frame set as a non-contig atlas entry."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
TARGET_BOOKS = ["8", "37", "63", "66"]
BLOCK = "AEFIEIEFIIVFAEATVAT"

SOURCE_BRIDGES = [
    {
        "bridge_id": "CHAYENNE_EXTERNAL_FRAME_ANCHOR",
        "source_url": "https://www.tibiawiki.com.br/469",
        "allowed_inference": "Use the Chayenne external 469 reply as a reusable shape/register holdout.",
        "blocked_inference": "Do not translate the Chayenne reply or shared block as a sentence.",
    },
    {
        "bridge_id": "Q2_CHAYENNE_EXPLICIT_GLOSS_AUDIT",
        "source_url": "sqlite:human_q2_chayenne_explicit_gloss_live_audit_v1",
        "allowed_inference": "Exact sequence attestation can constrain external provenance.",
        "blocked_inference": "No explicit gloss or plaintext promotion is available.",
    },
    {
        "bridge_id": "CHAYENNE_SHAPE_BRANCH_TOPOLOGY",
        "source_url": "sqlite:human_chayenne_shape_shadow_probe_v1",
        "allowed_inference": "The shared block crosses distinct branches, so it behaves as a register/frame.",
        "blocked_inference": "Do not treat branch reuse as one fixed English phrase.",
    },
    {
        "bridge_id": "PKG8_CHAYENNE_FUNCTIONAL_FALSIFICATION",
        "source_url": "sqlite:human_promotion_pkg8_chayenne_frame_branch_falsification_v1",
        "allowed_inference": "Books 8/37/66 may carry a human-functional branch label; Book 63 remains audit-held.",
        "blocked_inference": "No component gloss, Chayenne phrase translation, or Book 63 promotion.",
    },
    {
        "bridge_id": "AWB_LANGUAGE_MATHEMAGIC_PROCESSING",
        "source_url": "https://tibia.fandom.com/wiki/A_Wrinkled_Bonelord/Transcripts",
        "allowed_inference": "Use mathemagic/register behavior as an in-game method anchor.",
        "blocked_inference": "Do not promote a mathemagic dictionary key.",
    },
    {
        "bridge_id": "GREAT_CALCULATOR_CORPUS_GATHERING",
        "source_url": "https://www.tibiawiki.com.br/wiki/You_Cannot_Even_Imagine_%28Book%29",
        "allowed_inference": "The 469 books may be compiled or gathered language material rather than linear prose.",
        "blocked_inference": "Do not infer direct phrase meaning from corpus-structure lore.",
    },
]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q44_chayenne_register_frame_atlas_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q37_run_id INTEGER NOT NULL,
            q36_run_id INTEGER NOT NULL,
            chayenne_shape_run_id INTEGER NOT NULL,
            chayenne_branch_run_id INTEGER NOT NULL,
            q2_gloss_audit_run_id INTEGER NOT NULL,
            pkg8_falsification_run_id INTEGER NOT NULL,
            ingame_anchor_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            target_book_count INTEGER NOT NULL,
            source_bridge_count INTEGER NOT NULL,
            branch_count INTEGER NOT NULL,
            exact_external_shape_book_count INTEGER NOT NULL,
            strong_branch_book_count INTEGER NOT NULL,
            audit_branch_book_count INTEGER NOT NULL,
            q2_exact_sequence_attested_count INTEGER NOT NULL,
            q2_explicit_gloss_count INTEGER NOT NULL,
            pkg8_functional_label_count INTEGER NOT NULL,
            component_gloss_allowed_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            family_human_version TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q44_chayenne_register_frame_atlas_v1_books (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            q36_compiled_stratum TEXT NOT NULL,
            q36_likely_speech_act TEXT NOT NULL,
            q36_plausible_human_reading TEXT NOT NULL,
            branch_class TEXT NOT NULL,
            branch_likely_speech_act TEXT NOT NULL,
            branch_plausible_human_reading TEXT NOT NULL,
            confidence_tier TEXT NOT NULL,
            support_level TEXT NOT NULL,
            block_pos INTEGER NOT NULL,
            left_context TEXT NOT NULL,
            right_context TEXT NOT NULL,
            family_human_version TEXT NOT NULL,
            source_bridge_ids_json TEXT NOT NULL,
            translation_use TEXT NOT NULL,
            blocked_claims_json TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        );

        CREATE TABLE IF NOT EXISTS human_q44_chayenne_register_frame_atlas_v1_sources (
            run_id INTEGER NOT NULL,
            bridge_id TEXT NOT NULL,
            source_url TEXT NOT NULL,
            allowed_inference TEXT NOT NULL,
            blocked_inference TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bridge_id)
        );
        """
    )


def parse_json(value: str | None, fallback):
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def latest_row(conn: sqlite3.Connection, table: str) -> sqlite3.Row:
    row = conn.execute(f"SELECT * FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    if row is None:
        raise RuntimeError(f"missing required row: {table}")
    return row


def latest_run_id(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT max(run_id) FROM {table}").fetchone()
    if row is None or row[0] is None:
        raise RuntimeError(f"missing required run: {table}")
    return int(row[0])


def rows_by_book(conn: sqlite3.Connection, table: str, run_id: int) -> dict[str, sqlite3.Row]:
    placeholders = ",".join("?" for _ in TARGET_BOOKS)
    return {
        str(row["bookid"]): row
        for row in conn.execute(
            f"""
            SELECT *
            FROM {table}
            WHERE run_id=? AND bookid IN ({placeholders})
            ORDER BY CAST(bookid AS INTEGER)
            """,
            (run_id, *TARGET_BOOKS),
        )
    }


def q37_frontier_item(conn: sqlite3.Connection, q37_run_id: int) -> sqlite3.Row:
    row = conn.execute(
        """
        SELECT *
        FROM human_q37_noncontig_frontier_selection_v1_items
        WHERE run_id=? AND frontier_id='CHAYENNE_REGISTER_FRAME_SET'
        """,
        (q37_run_id,),
    ).fetchone()
    if row is None:
        raise RuntimeError("missing Q37 Chayenne frontier")
    return row


def q36_books(conn: sqlite3.Connection, q36_run_id: int) -> dict[str, sqlite3.Row]:
    placeholders = ",".join("?" for _ in TARGET_BOOKS)
    return {
        str(row["bookid"]): row
        for row in conn.execute(
            f"""
            SELECT *
            FROM human_q36_book_contig_shadow_integration_v1_items
            WHERE run_id=? AND bookid IN ({placeholders})
            ORDER BY CAST(bookid AS INTEGER)
            """,
            (q36_run_id, *TARGET_BOOKS),
        )
    }


def q2_sources(conn: sqlite3.Connection, q2_run_id: int) -> list[sqlite3.Row]:
    return list(
        conn.execute(
            """
            SELECT *
            FROM human_q2_chayenne_explicit_gloss_live_audit_v1_items
            WHERE run_id=?
            ORDER BY source_id
            """,
            (q2_run_id,),
        )
    )


def ingame_anchors(conn: sqlite3.Connection, anchor_run_id: int) -> list[sqlite3.Row]:
    return list(
        conn.execute(
            """
            SELECT *
            FROM human_ingame_anchor_corpus_v1_items
            WHERE run_id=?
              AND anchor_id IN (
                'CHAYENNE_EXTERNAL_FRAME',
                'AWB_469_LANGUAGE_MATHEMAGIC',
                'GREAT_CALCULATOR_GATHER_LANGUAGE'
              )
            ORDER BY anchor_id
            """,
            (anchor_run_id,),
        )
    )


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q37 = latest_row(conn, "human_q37_noncontig_frontier_selection_v1_runs")
    q36 = latest_row(conn, "human_q36_book_contig_shadow_integration_v1_runs")
    shape = latest_row(conn, "human_chayenne_shape_shadow_probe_v1_runs")
    branch = latest_row(conn, "human_chayenne_branch_shadow_v1_runs")
    q2 = latest_row(conn, "human_q2_chayenne_explicit_gloss_live_audit_v1_runs")
    pkg8 = latest_row(conn, "human_promotion_pkg8_chayenne_frame_branch_falsification_v1_runs")
    audit = latest_row(conn, "human_translation_completion_audit_v5_runs")
    anchor_run_id = latest_run_id(conn, "human_ingame_anchor_corpus_v1_items")

    q37_item = q37_frontier_item(conn, int(q37["run_id"]))
    q36_by_book = q36_books(conn, int(q36["run_id"]))
    shape_by_book = rows_by_book(
        conn,
        "human_chayenne_shape_shadow_probe_v1_items",
        int(shape["run_id"]),
    )
    branch_by_book = rows_by_book(
        conn,
        "human_chayenne_branch_shadow_v1_items",
        int(branch["run_id"]),
    )
    q2_rows = q2_sources(conn, int(q2["run_id"]))
    anchor_rows = ingame_anchors(conn, anchor_run_id)

    missing = [
        bookid
        for bookid in TARGET_BOOKS
        if bookid not in q36_by_book or bookid not in shape_by_book or bookid not in branch_by_book
    ]
    if missing:
        raise RuntimeError(f"missing Chayenne atlas evidence for books: {missing}")

    q37_books = parse_json(str(q37_item["bookids_json"]), [])
    branch_classes = sorted({str(row["branch_class"]) for row in branch_by_book.values()})
    branch_count = len(branch_classes)
    exact_external_shape_book_count = sum(1 for row in shape_by_book.values() if int(row["block_pos"]) >= 0)
    strong_branch_book_count = sum(
        1 for row in branch_by_book.values() if str(row["confidence_tier"]).startswith("STRUCTURAL_STRONG")
    )
    audit_branch_book_count = sum(1 for row in branch_by_book.values() if "AUDIT" in str(row["confidence_tier"]))
    q2_exact_sequence_attested_count = int(q2["exact_sequence_attested_count"])
    q2_explicit_gloss_count = int(q2["explicit_gloss_count"])
    pkg8_functional_label_count = int(pkg8["promoted_functional_label_count"])
    component_gloss_allowed_count = (
        int(shape["direct_meaning_allowed"])
        + int(shape["accepted_human_gloss_count"])
        + int(q2["explicit_gloss_count"])
        + int(q2["plaintext_promotable_count"])
        + int(pkg8["promoted_plaintext_gloss_count"])
    )
    canonical_promotion_allowed_count = (
        int(branch["canonical_promotion_count"])
        + int(q2["plaintext_promotable_count"])
        + int(pkg8["promoted_plaintext_gloss_count"])
    )
    family_human_version = (
        "Chayenne register-frame set: Books 8, 37, 63, and 66 carry the same external Chayenne 469 shape frame through distinct internal contexts. "
        "Read the family as register/context reuse anchored by in-game mathemagic and Great Calculator corpus lore, with Book 63 held as an audit/residual witness, not as a dictionary or Hellgate prose."
    )
    ready = (
        set(map(str, q37_books)) == set(TARGET_BOOKS)
        and len(q36_by_book) == 4
        and len(shape_by_book) == 4
        and len(branch_by_book) == 4
        and branch_count == 4
        and exact_external_shape_book_count == 4
        and strong_branch_book_count == 3
        and audit_branch_book_count == 1
        and q2_exact_sequence_attested_count >= 4
        and q2_explicit_gloss_count == 0
        and int(q2["plaintext_promotable_count"]) == 0
        and pkg8_functional_label_count == 1
        and int(pkg8["promoted_plaintext_gloss_count"]) == 0
        and int(audit["promoted_gloss_count"]) == 0
        and component_gloss_allowed_count == 0
        and canonical_promotion_allowed_count == 0
    )
    decision = (
        "Q44_CHAYENNE_REGISTER_FRAME_ATLAS_READY_NO_GLOSS"
        if ready
        else "Q44_CHAYENNE_REGISTER_FRAME_ATLAS_REQUIRES_REVIEW"
    )
    payload = {
        "question": "Can the remaining Q37 Chayenne frontier become a human atlas entry without importing external gloss?",
        "answer": "Yes, as a source-quarantined register-frame family with Book 63 kept audit-held.",
        "allowed_reading": family_human_version,
        "blocked_reading": "No Chayenne phrase translation, no shared-block gloss, no single sentence, no Hellgate prose claim.",
        "branch_classes": branch_classes,
        "block": BLOCK,
        "next_action": "Re-run non-contig frontier coverage after Q44 so all six Q37 families are accounted for.",
    }
    source_evidence = {
        "q2_sources": [dict(row) for row in q2_rows],
        "ingame_anchors": [dict(row) for row in anchor_rows],
        "shape_run": dict(shape),
        "branch_run": dict(branch),
        "pkg8_run": dict(pkg8),
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q44_chayenne_register_frame_atlas_v1_runs (
                created_at, decision, q37_run_id, q36_run_id,
                chayenne_shape_run_id, chayenne_branch_run_id,
                q2_gloss_audit_run_id, pkg8_falsification_run_id,
                ingame_anchor_run_id, completion_audit_run_id,
                target_book_count, source_bridge_count, branch_count,
                exact_external_shape_book_count, strong_branch_book_count,
                audit_branch_book_count, q2_exact_sequence_attested_count,
                q2_explicit_gloss_count, pkg8_functional_label_count,
                component_gloss_allowed_count, canonical_promotion_allowed_count,
                family_human_version, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                int(q37["run_id"]),
                int(q36["run_id"]),
                int(shape["run_id"]),
                int(branch["run_id"]),
                int(q2["run_id"]),
                int(pkg8["run_id"]),
                anchor_run_id,
                int(audit["run_id"]),
                len(TARGET_BOOKS),
                len(SOURCE_BRIDGES),
                branch_count,
                exact_external_shape_book_count,
                strong_branch_book_count,
                audit_branch_book_count,
                q2_exact_sequence_attested_count,
                q2_explicit_gloss_count,
                pkg8_functional_label_count,
                component_gloss_allowed_count,
                canonical_promotion_allowed_count,
                family_human_version,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q44_chayenne_register_frame_atlas_v1_books (
                run_id, bookid, q36_compiled_stratum, q36_likely_speech_act,
                q36_plausible_human_reading, branch_class,
                branch_likely_speech_act, branch_plausible_human_reading,
                confidence_tier, support_level, block_pos, left_context,
                right_context, family_human_version, source_bridge_ids_json,
                translation_use, blocked_claims_json, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    bookid,
                    str(q36_by_book[bookid]["compiled_stratum"]),
                    str(q36_by_book[bookid]["likely_speech_act"]),
                    str(q36_by_book[bookid]["plausible_human_reading"]),
                    str(branch_by_book[bookid]["branch_class"]),
                    str(branch_by_book[bookid]["likely_speech_act"]),
                    str(branch_by_book[bookid]["plausible_human_reading"]),
                    str(branch_by_book[bookid]["confidence_tier"]),
                    str(branch_by_book[bookid]["support_level"]),
                    int(shape_by_book[bookid]["block_pos"]),
                    str(shape_by_book[bookid]["left_context"]),
                    str(shape_by_book[bookid]["right_context"]),
                    family_human_version,
                    j([source["bridge_id"] for source in SOURCE_BRIDGES]),
                    "human non-contig register-frame atlas only; source-quarantined, not canonical plaintext",
                    j(
                        sorted(
                            set(parse_json(str(shape_by_book[bookid]["blocked_claims_json"]), []))
                            | set(parse_json(str(branch_by_book[bookid]["blocked_claims_json"]), []))
                            | {
                                "chayenne_phrase_translation",
                                "shared_block_gloss",
                                "single_sentence_translation",
                                "hellgate_prose_claim",
                            }
                        )
                    ),
                    j(
                        {
                            "q36_book": dict(q36_by_book[bookid]),
                            "shape_shadow": dict(shape_by_book[bookid]),
                            "branch_shadow": dict(branch_by_book[bookid]),
                        }
                    ),
                )
                for bookid in TARGET_BOOKS
            ],
        )
        conn.executemany(
            """
            INSERT INTO human_q44_chayenne_register_frame_atlas_v1_sources (
                run_id, bridge_id, source_url, allowed_inference,
                blocked_inference, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    str(source["bridge_id"]),
                    str(source["source_url"]),
                    str(source["allowed_inference"]),
                    str(source["blocked_inference"]),
                    j({"source": source, "linked_evidence": source_evidence}),
                )
                for source in SOURCE_BRIDGES
            ],
        )

    print(
        j(
            {
                "run_id": run_id,
                "decision": decision,
                "target_book_count": len(TARGET_BOOKS),
                "source_bridge_count": len(SOURCE_BRIDGES),
                "branch_count": branch_count,
                "exact_external_shape_book_count": exact_external_shape_book_count,
                "strong_branch_book_count": strong_branch_book_count,
                "audit_branch_book_count": audit_branch_book_count,
                "q2_exact_sequence_attested_count": q2_exact_sequence_attested_count,
                "q2_explicit_gloss_count": q2_explicit_gloss_count,
                "pkg8_functional_label_count": pkg8_functional_label_count,
                "component_gloss_allowed_count": component_gloss_allowed_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
            }
        )
    )


if __name__ == "__main__":
    main()
