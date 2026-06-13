#!/usr/bin/env python3
"""Q40: consolidate the non-contig C86/VINVIN branch trio."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
TARGET_BOOKS = ["3", "17", "44"]

SOURCE_BRIDGES = [
    "AWB_COMPLEX_FORMULA_SUBJECTIVE_VIEWER",
    "AWB_LANGUAGE_MATHEMAGIC_PROCESSING",
    "AWB_NUMBERS_LIFE_DEATH",
    "BEWARE_BLINKING_CODE_VARIABLE_UNIT",
    "THREAT_II_RESEARCH_EXPERIMENTS",
    "Q33_EXACT_CONTIG_BRANCH_ANALOGUE",
]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q40_c86_vinvin_branch_trio_atlas_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q37_run_id INTEGER NOT NULL,
            q33_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            target_book_count INTEGER NOT NULL,
            exact_contig_analogue_count INTEGER NOT NULL,
            source_bridge_count INTEGER NOT NULL,
            branch_context_count INTEGER NOT NULL,
            component_gloss_allowed_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            family_human_version TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q40_c86_vinvin_branch_trio_atlas_v1_books (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            q36_likely_speech_act TEXT NOT NULL,
            q36_plausible_human_reading TEXT NOT NULL,
            row0_markers_json TEXT NOT NULL,
            family_human_version TEXT NOT NULL,
            source_bridge_ids_json TEXT NOT NULL,
            translation_use TEXT NOT NULL,
            blocked_claims_json TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        );

        CREATE TABLE IF NOT EXISTS human_q40_c86_vinvin_branch_trio_atlas_v1_analogues (
            run_id INTEGER NOT NULL,
            basecontigid TEXT NOT NULL,
            booksinorder TEXT NOT NULL,
            human_functional_version TEXT NOT NULL,
            analogue_use TEXT NOT NULL,
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


def q36_book(conn: sqlite3.Connection, bookid: str) -> sqlite3.Row:
    row = conn.execute(
        """
        SELECT *
        FROM human_q36_book_contig_shadow_integration_v1_items
        WHERE run_id=(SELECT max(run_id) FROM human_q36_book_contig_shadow_integration_v1_items)
          AND bookid=?
        """,
        (bookid,),
    ).fetchone()
    if row is None:
        raise RuntimeError(f"missing Q36 book {bookid}")
    return row


def q33_analogues(conn: sqlite3.Connection, q33_run_id: int) -> list[sqlite3.Row]:
    return list(
        conn.execute(
            """
            SELECT *
            FROM human_q33_branch_formula_source_bridge_probe_v1_contigs
            WHERE run_id=?
            ORDER BY CAST(basecontigid AS INTEGER)
            """,
            (q33_run_id,),
        )
    )


def row0_markers(row: sqlite3.Row) -> str:
    evidence = json.loads(str(row["evidence_json"]))
    return str(evidence["q30_book"]["row0_markers_json"])


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q37 = latest_row(conn, "human_q37_noncontig_frontier_selection_v1_runs")
    q33 = latest_row(conn, "human_q33_branch_formula_source_bridge_probe_v1_runs")
    audit = latest_row(conn, "human_translation_completion_audit_v5_runs")
    q33_run_id = int(q33["run_id"])

    target_rows = [q36_book(conn, bookid) for bookid in TARGET_BOOKS]
    analogues = q33_analogues(conn, q33_run_id)
    branch_context_count = sum(
        1 for row in target_rows if str(row["likely_speech_act"]) == "C86 payload-open into VINVIN/VTLR branch"
    )
    family_human_version = (
        "C86/VINVIN non-contig branch trio: Books 3, 17, and 44 repeat a C86-opened VINVIN/VTLR/R20 branch shape outside the exact contigs. "
        "By analogy with Q33's exact branch packets, this trio should be read as non-contig selector/branch payload evidence under the complex-formula model, not as lexical prose."
    )
    component_gloss_allowed_count = 0
    canonical_promotion_allowed_count = 0
    decision = (
        "Q40_C86_VINVIN_BRANCH_TRIO_ATLAS_READY_NO_GLOSS"
        if len(target_rows) == 3
        and len(analogues) == 2
        and branch_context_count == 3
        and int(q33["component_gloss_allowed_count"]) == 0
        and int(q33["canonical_promotion_allowed_count"]) == 0
        and int(audit["promoted_gloss_count"]) == 0
        and component_gloss_allowed_count == 0
        and canonical_promotion_allowed_count == 0
        else "Q40_C86_VINVIN_BRANCH_TRIO_ATLAS_REQUIRES_REVIEW"
    )
    payload = {
        "question": "Can Q37 priority 3 generalize the Q33 exact branch/variant model to non-contig books?",
        "answer": "Yes, as a C86/VINVIN non-contig branch trio with Q33 as exact-contig analogue.",
        "allowed_reading": family_human_version,
        "blocked_reading": "No component gloss for C86, VINVIN, VTLR, R20, O23, or any target book.",
        "next_action": "Use this trio to contrast branch payloads against VNCTIIN/TIINNEF phase-context and C86/VNCTIIN payload books.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q40_c86_vinvin_branch_trio_atlas_v1_runs (
                created_at, decision, q37_run_id, q33_run_id,
                completion_audit_run_id, target_book_count,
                exact_contig_analogue_count, source_bridge_count,
                branch_context_count, component_gloss_allowed_count,
                canonical_promotion_allowed_count, family_human_version,
                payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                int(q37["run_id"]),
                q33_run_id,
                int(audit["run_id"]),
                len(TARGET_BOOKS),
                len(analogues),
                len(SOURCE_BRIDGES),
                branch_context_count,
                component_gloss_allowed_count,
                canonical_promotion_allowed_count,
                family_human_version,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q40_c86_vinvin_branch_trio_atlas_v1_books (
                run_id, bookid, q36_likely_speech_act,
                q36_plausible_human_reading, row0_markers_json,
                family_human_version, source_bridge_ids_json, translation_use,
                blocked_claims_json, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    str(row["bookid"]),
                    str(row["likely_speech_act"]),
                    str(row["plausible_human_reading"]),
                    row0_markers(row),
                    family_human_version,
                    j(SOURCE_BRIDGES),
                    "human non-contig branch atlas only; not canonical plaintext",
                    j(["component_gloss", "sentence_translation", "C86_as_word", "VINVIN_as_word", "R20_as_word", "O23_as_word"]),
                    j({"q36_book": dict(row)}),
                )
                for row in target_rows
            ],
        )
        conn.executemany(
            """
            INSERT INTO human_q40_c86_vinvin_branch_trio_atlas_v1_analogues (
                run_id, basecontigid, booksinorder, human_functional_version,
                analogue_use, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    str(row["basecontigid"]),
                    str(row["booksinorder"]),
                    str(row["human_functional_version"]),
                    "exact-contig analogue for non-contig branch trio; no semantic promotion",
                    j({"q33_contig": dict(row)}),
                )
                for row in analogues
            ],
        )

    print(
        j(
            {
                "run_id": run_id,
                "decision": decision,
                "target_book_count": len(TARGET_BOOKS),
                "exact_contig_analogue_count": len(analogues),
                "source_bridge_count": len(SOURCE_BRIDGES),
                "branch_context_count": branch_context_count,
                "component_gloss_allowed_count": component_gloss_allowed_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
            }
        )
    )


if __name__ == "__main__":
    main()
