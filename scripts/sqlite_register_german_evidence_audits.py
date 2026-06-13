#!/usr/bin/env python3
"""Register external-anchor and internal-pattern audits for the German candidate.

This encodes the latest research into SQLite so ranking no longer treats
German-looking names as strong Tibia lore anchors.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "bonelord_operational.sqlite"


ANCHOR_AUDIT = [
    {
        "anchor_key": "WEICHSTEIN",
        "classification": "PROBABLE_GERMAN_LEXICAL_ARTIFACT",
        "confidence": "MEDIUM_HIGH",
        "tibia_lore_status": "NO_EXACT_MATCH_FOUND",
        "semantic_use": "weak_lexical_hint_only",
        "impact": "Do not use as in-game proper name. Possible old German/lexical soft-stone or malachite clue.",
        "source_note": "External search found no Tibia entity; non-Tibia usage exists for Weichstein.",
    },
    {
        "anchor_key": "ORANGENSTRASSE",
        "classification": "PROBABLE_EXTERNAL_GERMAN_CONTAMINATION",
        "confidence": "HIGH",
        "tibia_lore_status": "NO_EXACT_MATCH_FOUND",
        "semantic_use": "display_only_suspect",
        "impact": "Do not use as Tibia place. Treat as suspicious toponym-like output.",
        "source_note": "No Tibia entity; real-world Orangenstrasse/Orangenstraße exists.",
    },
    {
        "anchor_key": "REDER KOENIG",
        "classification": "PROBABLE_TITLE_ARTIFACT",
        "confidence": "MEDIUM_HIGH",
        "tibia_lore_status": "NO_EXACT_MATCH_FOUND",
        "semantic_use": "internal_formula_only",
        "impact": "Do not promote as Red King/Reder King. Use only as recurring internal formula.",
        "source_note": "Tibia has kings, but no Reder König/Red King exact match.",
    },
    {
        "anchor_key": "REDER KOENIG SALZBERG",
        "classification": "COMPOSITE_ARTIFACT",
        "confidence": "HIGH",
        "tibia_lore_status": "NO_EXACT_MATCH_FOUND",
        "semantic_use": "suspect_formula",
        "impact": "Treat as German-like cluster, not lore anchor.",
        "source_note": "No exact in-game phrase; Salzberg not found as Tibia entity.",
    },
    {
        "anchor_key": "SCHARDT",
        "classification": "PROBABLE_NAME_ARTIFACT",
        "confidence": "MEDIUM_HIGH",
        "tibia_lore_status": "NO_EXACT_MATCH_FOUND",
        "semantic_use": "display_name_only",
        "impact": "Preserve as name-like token, but do not infer lore.",
        "source_note": "No exact Tibia entity found.",
    },
    {
        "anchor_key": "WINDUNRUH",
        "classification": "LOCAL_LEXICAL_WEAK",
        "confidence": "MEDIUM",
        "tibia_lore_status": "NO_EXACT_MATCH_FOUND",
        "semantic_use": "local_phrase_only",
        "impact": "Can be read locally as wind/unrest only if mechanical split supports it.",
        "source_note": "No exact lore anchor; wind-up items are unrelated English.",
    },
    {
        "anchor_key": "GOTTDIENER",
        "classification": "WEAK_THEMATIC_PARALLEL",
        "confidence": "LOW_MEDIUM",
        "tibia_lore_status": "NO_EXACT_MATCH_FOUND",
        "semantic_use": "weak_theme_only",
        "impact": "May hint at servant-of-god theme, not a proper term.",
        "source_note": "Weak parallel to divine servant lore, not exact term.",
    },
    {
        "anchor_key": "SALZBERG",
        "classification": "PARTIAL_LEXICAL_ARTIFACT",
        "confidence": "MEDIUM",
        "tibia_lore_status": "NO_EXACT_MATCH_FOUND",
        "semantic_use": "split_salz_from_berg",
        "impact": "Salt exists in Tibia; Salzberg as a place/entity does not. Do not promote compound.",
        "source_note": "Salt-related items/areas exist, but not Salzberg exact.",
    },
]


PATTERN_AUDIT = [
    {
        "pattern_key": "SAND IM MIN HEIME",
        "classification": "RECURRING_FORMULA",
        "bookids": ["11", "32", "36", "43", "58", "59"],
        "impact": "Treat as larger frame candidate, especially with URALTE STEIN / SCHARDT / RUIN contexts.",
        "next_test": "expand_window_to_full_formula",
    },
    {
        "pattern_key": "NNR TAG ND",
        "classification": "CORRUPT_CONNECTOR_OR_MICROTOKEN",
        "bookids": ["6", "7"],
        "impact": "Do not gloss NNR or ND as words. Keep as suspect until mechanical split improves.",
        "next_test": "inspect_pair_boundaries_and_adjacent_unknowns",
    },
    {
        "pattern_key": "RUIN",
        "classification": "RECURRING_LEXEME",
        "bookids": ["0", "6", "9", "22", "37", "47", "58", "59", "69"],
        "impact": "Distinct from RUNE. Useful narrative lexeme, not enough for full formula alone.",
        "next_test": "neighbor_distribution_ruin_vs_rune",
    },
    {
        "pattern_key": "RUNE",
        "classification": "RECURRING_LEXEME_OR_ENTITY",
        "bookids": ["6", "10", "16", "18", "24", "31", "33", "35", "40", "41", "48", "53", "66"],
        "impact": "Do not merge with RUIN. Appears in RUNE MANIER / RUNEN EID frames.",
        "next_test": "neighbor_distribution_ruin_vs_rune",
    },
    {
        "pattern_key": "HEHL_HEL_HECHL_HECHELT",
        "classification": "MORPHOLOGICAL_OR_SEGMENTATION_FAMILY",
        "bookids": ["3", "13", "16", "17", "21", "24", "28", "34", "45", "46", "51", "53", "58", "60", "62", "64", "65", "68"],
        "impact": "Promising family for controlled folding, but high risk of over-merging.",
        "next_test": "temporary_family_fold_with_regression_check",
    },
    {
        "pattern_key": "REDER_KOENIG_ORANGENSTRASSE_CLUSTER",
        "classification": "INTERNAL_CLUSTER_NOT_EXTERNAL_ANCHOR",
        "bookids": ["10", "27", "35", "40", "57"],
        "impact": "Useful internally because it recurs, but external audit says no Tibia exact match.",
        "next_test": "left_right_window_stability",
    },
    {
        "pattern_key": "THENAEUT_ORANGENSTRASSE_CLUSTER",
        "classification": "INTERNAL_CLUSTER_NOT_EXTERNAL_ANCHOR",
        "bookids": ["12", "21", "26"],
        "impact": "Treat THENAEUT as unknown entity-like token; do not lore-promote Orangenstrasse.",
        "next_test": "entity_cluster_window_stability",
    },
]


DEMOTED_FRONTIER_KEYS = {
    "anchor_orangenstrasse": 0.42,
    "anchor_reder_koenig": 0.48,
    "anchor_weichstein": 0.52,
    "anchor_salzberg": 0.50,
}


PROMOTED_INTERNAL_KEYS = {
    "formula_sand_home": 1.25,
    "formula_ruin_rune": 1.18,
    "formula_hechl": 1.25,
    "formula_nnr_tag_nd": 1.08,
    "formula_thenaeut": 0.95,
    "formula_ei_gen_hehl": 1.10,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def jdump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def one(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> sqlite3.Row:
    row = conn.execute(sql, params).fetchone()
    if row is None:
        raise SystemExit(f"missing required row for query: {sql}")
    return row


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS german_external_anchor_audit_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_canonical_run_id INTEGER NOT NULL,
            anchor_count INTEGER NOT NULL,
            artifact_or_weak_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS german_external_anchor_audit_items (
            run_id INTEGER NOT NULL,
            anchor_key TEXT NOT NULL,
            classification TEXT NOT NULL,
            confidence TEXT NOT NULL,
            tibia_lore_status TEXT NOT NULL,
            semantic_use TEXT NOT NULL,
            impact TEXT NOT NULL,
            source_note TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, anchor_key)
        );

        CREATE TABLE IF NOT EXISTS german_internal_pattern_audit_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_canonical_run_id INTEGER NOT NULL,
            pattern_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS german_internal_pattern_audit_items (
            run_id INTEGER NOT NULL,
            pattern_key TEXT NOT NULL,
            classification TEXT NOT NULL,
            bookids_json TEXT NOT NULL,
            impact TEXT NOT NULL,
            next_test TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, pattern_key)
        );

        CREATE TABLE IF NOT EXISTS german_semantic_frontier_adjusted_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_frontier_run_id INTEGER NOT NULL,
            anchor_audit_run_id INTEGER NOT NULL,
            pattern_audit_run_id INTEGER NOT NULL,
            item_count INTEGER NOT NULL,
            demoted_external_anchor_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS german_semantic_frontier_adjusted_items (
            run_id INTEGER NOT NULL,
            priority_rank INTEGER NOT NULL,
            source_priority_rank INTEGER NOT NULL,
            focus_key TEXT NOT NULL,
            focus_kind TEXT NOT NULL,
            original_score REAL NOT NULL,
            adjusted_score REAL NOT NULL,
            risk TEXT NOT NULL,
            status TEXT NOT NULL,
            bookids_json TEXT NOT NULL,
            reason TEXT NOT NULL,
            next_test TEXT NOT NULL,
            adjustment_reason TEXT NOT NULL,
            anti_hallucination_rule TEXT NOT NULL,
            PRIMARY KEY (run_id, focus_key)
        );
        """
    )


def adjusted_item(row: sqlite3.Row) -> dict[str, Any]:
    key = row["focus_key"]
    original = float(row["priority_score"])
    score = original
    status = row["status"]
    risk = row["risk"]
    reason = "no adjustment"
    if key in DEMOTED_FRONTIER_KEYS:
        score = original * DEMOTED_FRONTIER_KEYS[key]
        status = "DEMOTED_EXTERNAL_ANCHOR_NOT_LORE_CONFIRMED"
        risk = "MEDIUM_ARTIFACT_AUDIT"
        reason = "External audit found no Tibia exact anchor; use only as internal pattern."
    elif key in PROMOTED_INTERNAL_KEYS:
        score = original * PROMOTED_INTERNAL_KEYS[key]
        status = "PROMOTED_INTERNAL_PATTERN"
        risk = row["risk"] if row["risk"] != "LOW_MARKER_DRIFT" else "MEDIUM"
        reason = "Internal SQL pattern audit supports controlled local investigation."
    elif key.startswith("unknown_") and len(key.removeprefix("unknown_")) <= 1:
        score = original * 0.50
        status = "DEMOTED_SINGLE_MARKER_DRIFT"
        risk = "LOW_MARKER_DRIFT"
        reason = "One-letter groups are too likely to be marker drift for semantic promotion."
    return {
        "source_priority_rank": int(row["priority_rank"]),
        "focus_key": key,
        "focus_kind": row["focus_kind"],
        "original_score": original,
        "adjusted_score": score,
        "risk": risk,
        "status": status,
        "bookids_json": row["bookids_json"],
        "reason": row["reason"],
        "next_test": row["next_test"],
        "adjustment_reason": reason,
        "anti_hallucination_rule": row["anti_hallucination_rule"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)

    canonical = one(conn, "SELECT * FROM canonical_candidate_runs ORDER BY run_id DESC LIMIT 1")
    frontier = one(conn, "SELECT * FROM german_semantic_frontier_runs ORDER BY run_id DESC LIMIT 1")

    cur = conn.execute(
        """
        INSERT INTO german_external_anchor_audit_runs
            (created_at, source_canonical_run_id, anchor_count, artifact_or_weak_count, payload_json)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            utc_now(),
            canonical["run_id"],
            len(ANCHOR_AUDIT),
            len(ANCHOR_AUDIT),
            jdump({"source": "external lore audit", "effect": "demote unconfirmed German-looking anchors"}),
        ),
    )
    anchor_run_id = int(cur.lastrowid)
    for item in ANCHOR_AUDIT:
        conn.execute(
            """
            INSERT INTO german_external_anchor_audit_items
                (run_id, anchor_key, classification, confidence, tibia_lore_status,
                 semantic_use, impact, source_note, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                anchor_run_id,
                item["anchor_key"],
                item["classification"],
                item["confidence"],
                item["tibia_lore_status"],
                item["semantic_use"],
                item["impact"],
                item["source_note"],
                jdump(item),
            ),
        )

    cur = conn.execute(
        """
        INSERT INTO german_internal_pattern_audit_runs
            (created_at, source_canonical_run_id, pattern_count, payload_json)
        VALUES (?, ?, ?, ?)
        """,
        (
            utc_now(),
            canonical["run_id"],
            len(PATTERN_AUDIT),
            jdump({"source": "SQL pattern audit", "effect": "prefer internal repetition over external-lore assumptions"}),
        ),
    )
    pattern_run_id = int(cur.lastrowid)
    for item in PATTERN_AUDIT:
        conn.execute(
            """
            INSERT INTO german_internal_pattern_audit_items
                (run_id, pattern_key, classification, bookids_json, impact, next_test, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                pattern_run_id,
                item["pattern_key"],
                item["classification"],
                jdump(item["bookids"]),
                item["impact"],
                item["next_test"],
                jdump(item),
            ),
        )

    source_items = conn.execute(
        """
        SELECT *
        FROM german_semantic_frontier_items
        WHERE run_id=?
        ORDER BY priority_rank
        """,
        (frontier["run_id"],),
    ).fetchall()
    adjusted = sorted((adjusted_item(row) for row in source_items), key=lambda x: (-x["adjusted_score"], x["focus_key"]))
    demoted_count = sum(1 for item in adjusted if item["status"] == "DEMOTED_EXTERNAL_ANCHOR_NOT_LORE_CONFIRMED")

    cur = conn.execute(
        """
        INSERT INTO german_semantic_frontier_adjusted_runs
            (created_at, source_frontier_run_id, anchor_audit_run_id, pattern_audit_run_id,
             item_count, demoted_external_anchor_count, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            utc_now(),
            frontier["run_id"],
            anchor_run_id,
            pattern_run_id,
            len(adjusted),
            demoted_count,
            jdump({"ranking": "external lore demoted; internal repeated formulas preferred"}),
        ),
    )
    adjusted_run_id = int(cur.lastrowid)

    for rank, item in enumerate(adjusted, start=1):
        conn.execute(
            """
            INSERT INTO german_semantic_frontier_adjusted_items
                (run_id, priority_rank, source_priority_rank, focus_key, focus_kind,
                 original_score, adjusted_score, risk, status, bookids_json,
                 reason, next_test, adjustment_reason, anti_hallucination_rule)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                adjusted_run_id,
                rank,
                item["source_priority_rank"],
                item["focus_key"],
                item["focus_kind"],
                item["original_score"],
                item["adjusted_score"],
                item["risk"],
                item["status"],
                item["bookids_json"],
                item["reason"],
                item["next_test"],
                item["adjustment_reason"],
                item["anti_hallucination_rule"],
            ),
        )
    conn.commit()

    print(
        json.dumps(
            {
                "anchor_audit_run_id": anchor_run_id,
                "pattern_audit_run_id": pattern_run_id,
                "adjusted_frontier_run_id": adjusted_run_id,
                "item_count": len(adjusted),
                "demoted_external_anchor_count": demoted_count,
                "top_items": [
                    {
                        "rank": idx,
                        "focus_key": item["focus_key"],
                        "score": round(item["adjusted_score"], 2),
                        "status": item["status"],
                        "risk": item["risk"],
                    }
                    for idx, item in enumerate(adjusted[:15], start=1)
                ],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
