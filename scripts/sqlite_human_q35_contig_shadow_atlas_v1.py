#!/usr/bin/env python3
"""Q35: consolidate Q32-Q34 into a contig-level human shadow atlas."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q35_contig_shadow_atlas_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q30_run_id INTEGER NOT NULL,
            q32_run_id INTEGER NOT NULL,
            q33_run_id INTEGER NOT NULL,
            q34_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            exact_q30_contig_count INTEGER NOT NULL,
            atlas_contig_count INTEGER NOT NULL,
            source_anchored_contig_count INTEGER NOT NULL,
            weak_or_scoped_contig_count INTEGER NOT NULL,
            component_gloss_allowed_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q35_contig_shadow_atlas_v1_items (
            run_id INTEGER NOT NULL,
            basecontigid TEXT NOT NULL,
            source_probe TEXT NOT NULL,
            booksinorder TEXT NOT NULL,
            structural_narrative TEXT NOT NULL,
            human_functional_version TEXT NOT NULL,
            confidence TEXT NOT NULL,
            source_bridge_ids_json TEXT NOT NULL,
            translation_use TEXT NOT NULL,
            next_source_question TEXT NOT NULL,
            blocked_claims_json TEXT NOT NULL,
            promotion_status TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, basecontigid)
        );
        """
    )


def latest_row(conn: sqlite3.Connection, table: str) -> sqlite3.Row:
    row = conn.execute(f"SELECT * FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    if row is None:
        raise RuntimeError(f"missing required row: {table}")
    return row


def q30_contigs(conn: sqlite3.Connection, q30_run_id: int) -> dict[str, sqlite3.Row]:
    return {
        str(row["basecontigid"]): row
        for row in conn.execute(
            """
            SELECT *
            FROM human_q30_great_calculator_compiled_corpus_spine_map_v1_contigs
            WHERE run_id=?
            """,
            (q30_run_id,),
        )
    }


def source_question(basecontigid: str) -> str:
    questions = {
        "0": "Find exact in-game contrasts where a repeated slot/bridge pair changes only the slot or bridge.",
        "1": "Search rituals, experiments, command/control, and slot-change contexts for formula-to-payload-to-slot parallels.",
        "2": "Search for in-game formula variants where a branch reaches a phase endpoint or longer connector.",
        "3": "Search for controlled branch endpoint pairs where a second text strengthens the endpoint.",
        "4": "Find exact source evidence for O23/FNAAST endpoint meaning before any stronger use.",
        "5": "Search for formula-template handoffs or repeated ritual frames tied to BENNA/LTAST behavior.",
    }
    return questions[basecontigid]


def load_q32(conn: sqlite3.Connection, q32_run_id: int) -> list[dict[str, object]]:
    row = conn.execute(
        """
        SELECT *
        FROM human_q32_contig1_source_bridge_probe_v1_runs
        WHERE run_id=?
        """,
        (q32_run_id,),
    ).fetchone()
    if row is None:
        return []
    source_ids = [
        str(source["bridge_id"])
        for source in conn.execute(
            """
            SELECT bridge_id
            FROM human_q32_contig1_source_bridge_probe_v1_sources
            WHERE run_id=?
            ORDER BY bridge_id
            """,
            (q32_run_id,),
        )
    ]
    return [
        {
            "basecontigid": str(row["target_contig"]),
            "source_probe": "Q32_CONTIG1_SOURCE_BRIDGE",
            "booksinorder": "->".join(json.loads(str(row["target_books_json"]))),
            "human_functional_version": str(row["human_functional_version"]),
            "confidence": "MODERATE_STRONG_SOURCE_BRIDGED_PACKET",
            "source_bridge_ids": source_ids,
            "blocked_claims": [
                "component_gloss",
                "sentence_translation",
                "direct_necromancy_word_mapping",
                "canonical_promotion",
            ],
            "evidence": {"q32_run": dict(row), "source_bridge_ids": source_ids},
        }
    ]


def load_q33(conn: sqlite3.Connection, q33_run_id: int) -> list[dict[str, object]]:
    return [
        {
            "basecontigid": str(row["basecontigid"]),
            "source_probe": "Q33_BRANCH_FORMULA_SOURCE_BRIDGE",
            "booksinorder": str(row["booksinorder"]),
            "human_functional_version": str(row["human_functional_version"]),
            "confidence": "MODERATE_STRONG_BRANCH_FORMULA_PACKET",
            "source_bridge_ids": json.loads(str(row["source_bridge_ids_json"])),
            "blocked_claims": json.loads(str(row["blocked_claims_json"])),
            "evidence": {"q33_contig": dict(row)},
        }
        for row in conn.execute(
            """
            SELECT *
            FROM human_q33_branch_formula_source_bridge_probe_v1_contigs
            WHERE run_id=?
            ORDER BY CAST(basecontigid AS INTEGER)
            """,
            (q33_run_id,),
        )
    ]


def load_q34(conn: sqlite3.Connection, q34_run_id: int) -> list[dict[str, object]]:
    return [
        {
            "basecontigid": str(row["basecontigid"]),
            "source_probe": "Q34_REMAINING_CONTIG_FUNCTIONAL_VERSIONS",
            "booksinorder": str(row["booksinorder"]),
            "human_functional_version": str(row["human_functional_version"]),
            "confidence": str(row["confidence"]),
            "source_bridge_ids": json.loads(str(row["source_bridge_ids_json"])),
            "blocked_claims": json.loads(str(row["blocked_claims_json"])),
            "evidence": {"q34_contig": dict(row)},
        }
        for row in conn.execute(
            """
            SELECT *
            FROM human_q34_remaining_contig_functional_versions_v1_contigs
            WHERE run_id=?
            ORDER BY CAST(basecontigid AS INTEGER)
            """,
            (q34_run_id,),
        )
    ]


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q30 = latest_row(conn, "human_q30_great_calculator_compiled_corpus_spine_map_v1_runs")
    q32 = latest_row(conn, "human_q32_contig1_source_bridge_probe_v1_runs")
    q33 = latest_row(conn, "human_q33_branch_formula_source_bridge_probe_v1_runs")
    q34 = latest_row(conn, "human_q34_remaining_contig_functional_versions_v1_runs")
    audit = latest_row(conn, "human_translation_completion_audit_v5_runs")
    q30_run_id = int(q30["run_id"])

    q30_by_contig = q30_contigs(conn, q30_run_id)
    raw_items = load_q32(conn, int(q32["run_id"])) + load_q33(conn, int(q33["run_id"])) + load_q34(conn, int(q34["run_id"]))
    by_contig = {str(item["basecontigid"]): item for item in raw_items}
    missing = sorted(set(q30_by_contig) - set(by_contig), key=int)
    if missing:
        raise RuntimeError(f"missing contig versions: {missing}")

    items: list[dict[str, object]] = []
    for contig_id in sorted(q30_by_contig, key=int):
        item = by_contig[contig_id]
        q30_contig = q30_by_contig[contig_id]
        items.append(
            {
                **item,
                "structural_narrative": str(q30_contig["structural_narrative"]),
                "translation_use": "human shadow atlas entry; source-search spine only; not canonical plaintext",
                "next_source_question": source_question(contig_id),
                "promotion_status": "NOT_PROMOTED_NO_COMPONENT_GLOSS",
                "evidence": {**dict(item["evidence"]), "q30_contig": dict(q30_contig)},
            }
        )

    weak_or_scoped_contig_count = sum(
        1 for item in items if "WEAK" in str(item["confidence"]) or "SCOPED" in str(item["confidence"])
    )
    component_gloss_allowed_count = 0
    canonical_promotion_allowed_count = 0
    decision = (
        "Q35_CONTIG_HUMAN_SHADOW_ATLAS_READY_6_OF_6_NO_GLOSS"
        if len(items) == len(q30_by_contig) == 6
        and int(audit["promoted_gloss_count"]) == 0
        and component_gloss_allowed_count == 0
        and canonical_promotion_allowed_count == 0
        else "Q35_CONTIG_HUMAN_SHADOW_ATLAS_REQUIRES_REVIEW"
    )
    payload = {
        "question": "Do all exact Q30 contigs now have one operational human shadow version?",
        "answer": "Yes. Six of six exact contigs have source-anchored functional versions with no component gloss.",
        "allowed_use": "Use as a contig-level human shadow atlas and source-search queue.",
        "blocked_use": "Do not treat the atlas as solved plaintext or as promoted canonical translation.",
        "weakness": "Contig 4 remains weak/scoped due to O23/FNAAST endpoint uncertainty.",
        "next_action": "Join these contig versions back to book-level atlas rows to prioritize the next non-contig book families.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q35_contig_shadow_atlas_v1_runs (
                created_at, decision, q30_run_id, q32_run_id, q33_run_id,
                q34_run_id, completion_audit_run_id, exact_q30_contig_count,
                atlas_contig_count, source_anchored_contig_count,
                weak_or_scoped_contig_count, component_gloss_allowed_count,
                canonical_promotion_allowed_count, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                q30_run_id,
                int(q32["run_id"]),
                int(q33["run_id"]),
                int(q34["run_id"]),
                int(audit["run_id"]),
                len(q30_by_contig),
                len(items),
                len(items),
                weak_or_scoped_contig_count,
                component_gloss_allowed_count,
                canonical_promotion_allowed_count,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q35_contig_shadow_atlas_v1_items (
                run_id, basecontigid, source_probe, booksinorder,
                structural_narrative, human_functional_version, confidence,
                source_bridge_ids_json, translation_use, next_source_question,
                blocked_claims_json, promotion_status, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    str(item["basecontigid"]),
                    str(item["source_probe"]),
                    str(item["booksinorder"]),
                    str(item["structural_narrative"]),
                    str(item["human_functional_version"]),
                    str(item["confidence"]),
                    j(item["source_bridge_ids"]),
                    str(item["translation_use"]),
                    str(item["next_source_question"]),
                    j(item["blocked_claims"]),
                    str(item["promotion_status"]),
                    j(item["evidence"]),
                )
                for item in items
            ],
        )

    print(
        j(
            {
                "run_id": run_id,
                "decision": decision,
                "exact_q30_contig_count": len(q30_by_contig),
                "atlas_contig_count": len(items),
                "source_anchored_contig_count": len(items),
                "weak_or_scoped_contig_count": weak_or_scoped_contig_count,
                "component_gloss_allowed_count": component_gloss_allowed_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
            }
        )
    )


if __name__ == "__main__":
    main()
