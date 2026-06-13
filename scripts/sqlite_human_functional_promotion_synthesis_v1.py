#!/usr/bin/env python3
"""Synthesize falsified human-functional promotions into an operational map."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

PACKAGE_SPECS = [
    {
        "package_id": "PKG_R02_NAESE_SLOT_BRIDGE_51_53",
        "run_table": "human_promotion_pkg1_r02_naese_falsification_v1_runs",
        "decision_table": "human_promotion_pkg1_r02_naese_falsification_v1_decisions",
        "candidate_books": ["51", "53"],
        "context_books": ["22", "42", "46"],
        "functional_label": "R02 phase-to-NAESE/C68 slot bridge",
        "cluster": "PHASE_SLOT_TO_FORMULA_CHAIN",
    },
    {
        "package_id": "PKG_NAESE_BENNA_COMPOSITE_5_9",
        "run_table": "human_promotion_pkg2_naese_benna_falsification_v1_runs",
        "decision_table": "human_promotion_pkg2_naese_benna_falsification_v1_decisions",
        "candidate_books": ["5", "9"],
        "context_books": ["22", "40", "50", "69"],
        "functional_label": "NAESE/C68 slot-to-BENNA formula composite",
        "cluster": "PHASE_SLOT_TO_FORMULA_CHAIN",
    },
    {
        "package_id": "PKG_BENNA_C86_VNCTIIN_HANDOFF_10_35",
        "run_table": "human_promotion_pkg3_benna_c86_handoff_falsification_v1_runs",
        "decision_table": "human_promotion_pkg3_benna_c86_handoff_falsification_v1_decisions",
        "candidate_books": ["10", "35"],
        "context_books": ["2", "27", "40", "50", "67", "69"],
        "functional_label": "BENNA/LTAST formula-to-C86/VNCTIIN handoff",
        "cluster": "PHASE_SLOT_TO_FORMULA_CHAIN",
    },
    {
        "package_id": "PKG_C86_VNCTIIN_PAYLOAD_2_27_67",
        "run_table": "human_promotion_pkg4_c86_vnctiin_payload_falsification_v1_runs",
        "decision_table": "human_promotion_pkg4_c86_vnctiin_payload_falsification_v1_decisions",
        "candidate_books": ["2", "27", "67"],
        "context_books": ["10", "23", "24", "35", "57"],
        "functional_label": "C86/VNCTIIN payload corridor",
        "cluster": "PHASE_SLOT_TO_FORMULA_CHAIN",
    },
    {
        "package_id": "PKG_BOOK54_LOCAL_PAIR_SPINE",
        "run_table": "human_promotion_pkg5_book54_local_pair_falsification_v1_runs",
        "decision_table": "human_promotion_pkg5_book54_local_pair_falsification_v1_decisions",
        "candidate_books": ["54"],
        "context_books": ["20", "25", "39", "60", "64"],
        "functional_label": "Book54/20 local-pair shared spine",
        "cluster": "LOCAL_PAIR_AND_RESIDUALS",
    },
    {
        "package_id": "PKG_BOOK7_PHASE_BRIDGE",
        "run_table": "human_promotion_pkg6_book7_phase_bridge_falsification_v1_runs",
        "decision_table": "human_promotion_pkg6_book7_phase_bridge_falsification_v1_decisions",
        "candidate_books": ["7"],
        "context_books": ["6", "19", "31", "57"],
        "functional_label": "Book7 phase-continuity bridge",
        "cluster": "LOCAL_PAIR_AND_RESIDUALS",
    },
    {
        "package_id": "PKG_BOOK49_REPEAT_REGISTER",
        "run_table": "human_promotion_pkg7_book49_repeat_register_falsification_v1_runs",
        "decision_table": "human_promotion_pkg7_book49_repeat_register_falsification_v1_decisions",
        "candidate_books": ["49"],
        "context_books": ["4", "6", "10", "31", "35", "55", "57", "58", "62"],
        "functional_label": "Book49 self-contained repeat/register formula",
        "cluster": "LOCAL_PAIR_AND_RESIDUALS",
    },
    {
        "package_id": "PKG_CHAYENNE_FRAME_BRANCHES_8_37_66",
        "run_table": "human_promotion_pkg8_chayenne_frame_branch_falsification_v1_runs",
        "decision_table": "human_promotion_pkg8_chayenne_frame_branch_falsification_v1_decisions",
        "candidate_books": ["8", "37", "66"],
        "context_books": ["1", "10", "19", "27", "35", "41", "63"],
        "functional_label": "Chayenne external-shape frame branch/register",
        "cluster": "EXTERNAL_FRAME_BRANCH",
    },
]

NEXT_QUESTIONS = [
    {
        "question_id": "Q1_PHASE_SLOT_FORMULA_PAYLOAD_CHAIN",
        "priority": 1,
        "cluster": "PHASE_SLOT_TO_FORMULA_CHAIN",
        "question": "Can the promoted 51/53 -> 5/9 -> 10/35 -> 2/27/67 chain predict held-out transitions as a procedural register without adding prose?",
        "required_evidence": "contig/order prediction, held-out branch behavior, and contradiction reduction across package boundaries",
        "reject_if": "requires translating R02, NAESE, BENNA, C86, VNCTIIN, C68, LTAST, or TAILBETFTE as words",
        "next_action": "Build a chain-level directionality/holdout probe over the promoted package sequence.",
    },
    {
        "question_id": "Q2_CHAYENNE_PRIMARY_EXPLICIT_GLOSS",
        "priority": 2,
        "cluster": "EXTERNAL_FRAME_BRANCH",
        "question": "Can any primary or trusted in-game source give the exact Chayenne sequence plus explicit meaning?",
        "required_evidence": "exact sequence, provenance, and explicit gloss from primary/trusted source",
        "reject_if": "source only repeats context, gives speculation, or maps near variants without meaning",
        "next_action": "Keep the external frame as structural until a primary explicit gloss is found.",
    },
    {
        "question_id": "Q3_BOOK49_REGISTER_FUNCTION",
        "priority": 3,
        "cluster": "LOCAL_PAIR_AND_RESIDUALS",
        "question": "Does Book49's self-contained repeat/register pattern correlate with calibration/operator-reset use in in-game context?",
        "required_evidence": "book location, neighboring texts, or independent repeated-register parallels",
        "reject_if": "argument depends only on repetition density or the number 49 as a key",
        "next_action": "Search in-game placement/neighborhood and compare with Book55/high-repeat controls.",
    },
    {
        "question_id": "Q4_BOOK7_PHASE_DIRECTION",
        "priority": 4,
        "cluster": "LOCAL_PAIR_AND_RESIDUALS",
        "question": "Does Book7 directionally bridge NEIAAETTA continuity into TIINNEF phase, or is it just local co-occurrence?",
        "required_evidence": "directional contrast against Book6 and TIINNEF+VNCTIIN controls 19/31/57",
        "reject_if": "uses 3478, NEIAAETTA, or TIINNEF as a word gloss",
        "next_action": "Run a directionality-specific phase bridge probe and keep high row0 phase risk active.",
    },
    {
        "question_id": "Q5_BOOK20_54_LOCAL_PAIR_CONTEXT",
        "priority": 5,
        "cluster": "LOCAL_PAIR_AND_RESIDUALS",
        "question": "Can Book20/54's shared spine be anchored to physical book adjacency, shelf context, or a repeated in-game pair convention?",
        "required_evidence": "in-game placement or independent pair convention beyond LCS alignment",
        "reject_if": "treats the shared spine, prefix, or tail as lexical words",
        "next_action": "Investigate source/location metadata before any stronger Book54 paraphrase.",
    },
]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_functional_promotion_synthesis_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            package_count INTEGER NOT NULL,
            promoted_package_count INTEGER NOT NULL,
            promoted_book_count INTEGER NOT NULL,
            cluster_count INTEGER NOT NULL,
            control_fail_count INTEGER NOT NULL,
            promoted_plaintext_gloss_count INTEGER NOT NULL,
            next_question_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_functional_promotion_synthesis_v1_items (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            package_id TEXT NOT NULL,
            package_run_id INTEGER NOT NULL,
            decision TEXT NOT NULL,
            cluster TEXT NOT NULL,
            functional_label TEXT NOT NULL,
            human_functional_reading TEXT NOT NULL,
            book_specific_note TEXT NOT NULL,
            context_books_json TEXT NOT NULL,
            blocked_claims_json TEXT NOT NULL,
            lexical_gloss_allowed INTEGER NOT NULL,
            plaintext_gloss_allowed INTEGER NOT NULL,
            promotion_layer TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid, package_id)
        );

        CREATE TABLE IF NOT EXISTS human_functional_promotion_synthesis_v1_next_questions (
            run_id INTEGER NOT NULL,
            question_id TEXT NOT NULL,
            priority INTEGER NOT NULL,
            cluster TEXT NOT NULL,
            question TEXT NOT NULL,
            required_evidence TEXT NOT NULL,
            reject_if TEXT NOT NULL,
            next_action TEXT NOT NULL,
            PRIMARY KEY (run_id, question_id)
        );
        """
    )


def latest_row(conn: sqlite3.Connection, table: str) -> sqlite3.Row:
    row = conn.execute(f"SELECT * FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    if row is None:
        raise RuntimeError(f"missing table data: {table}")
    return row


def decision_row(conn: sqlite3.Connection, table: str, run_id: int) -> sqlite3.Row:
    row = conn.execute(f"SELECT * FROM {table} WHERE run_id=? LIMIT 1", (run_id,)).fetchone()
    if row is None:
        raise RuntimeError(f"missing decision row: {table}/{run_id}")
    return row


def row_get(row: sqlite3.Row, key: str, default: object = "") -> object:
    return row[key] if key in row.keys() else default


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    atlas_readings: dict[str, str] = {}
    try:
        atlas_run_id = int(conn.execute("SELECT max(run_id) FROM human_translation_atlas_v6_items").fetchone()[0])
        atlas_readings = {
            str(row["target_id"]): str(row["plausible_human_reading"])
            for row in conn.execute(
                """
                SELECT target_id, plausible_human_reading
                FROM human_translation_atlas_v6_items
                WHERE run_id=?
                """,
                (atlas_run_id,),
            )
        }
    except Exception:
        atlas_readings = {}

    package_records = []
    item_records = []
    total_control_fails = 0
    total_plaintext = 0
    for spec in PACKAGE_SPECS:
        run = latest_row(conn, spec["run_table"])
        decision = decision_row(conn, spec["decision_table"], int(run["run_id"]))
        blocked_claims = json.loads(str(decision["blocked_claims_json"]))
        subtype_raw = row_get(decision, "subtype_notes_json", "{}")
        subtype_notes = json.loads(str(subtype_raw or "{}"))
        passed = (
            int(run["control_fail_count"]) == 0
            and int(run["promoted_functional_label_count"]) == 1
            and int(run["promoted_plaintext_gloss_count"]) == 0
            and str(run["decision"]).startswith("PROMOTE_HUMAN_FUNCTIONAL")
        )
        total_control_fails += int(run["control_fail_count"])
        total_plaintext += int(run["promoted_plaintext_gloss_count"])
        package_records.append(
            {
                "package_id": spec["package_id"],
                "run_id": int(run["run_id"]),
                "decision": str(run["decision"]),
                "passed": passed,
                "candidate_books": spec["candidate_books"],
                "context_books": spec["context_books"],
                "cluster": spec["cluster"],
                "positive_pass_count": int(run["positive_pass_count"]),
                "control_pass_count": int(run["control_pass_count"]),
                "control_warn_count": int(run["control_warn_count"]),
            }
        )
        for bookid in spec["candidate_books"]:
            book_note = str(subtype_notes.get(bookid, subtype_notes.get("_default", ""))).strip()
            if not book_note:
                book_note = atlas_readings.get(bookid, "")
            item_records.append(
                {
                    "bookid": bookid,
                    "package_id": spec["package_id"],
                    "package_run_id": int(run["run_id"]),
                    "decision": str(run["decision"]),
                    "cluster": spec["cluster"],
                    "functional_label": spec["functional_label"],
                    "human_functional_reading": str(decision["human_functional_reading"]),
                    "book_specific_note": book_note,
                    "context_books": spec["context_books"],
                    "blocked_claims": blocked_claims,
                    "lexical_gloss_allowed": 0,
                    "plaintext_gloss_allowed": 0,
                    "promotion_layer": "HUMAN_FUNCTIONAL_PROMOTED_NO_GLOSS",
                    "evidence": {
                        "decision_id": decision["decision_id"],
                        "scope": decision["scope"],
                        "positive_pass_count": int(run["positive_pass_count"]),
                        "control_pass_count": int(run["control_pass_count"]),
                        "control_warn_count": int(run["control_warn_count"]),
                        "source_tables": [spec["run_table"], spec["decision_table"]],
                    },
                }
            )

    promoted_packages = [record for record in package_records if record["passed"]]
    clusters = sorted({record["cluster"] for record in package_records})
    decision = (
        "HUMAN_FUNCTIONAL_PROMOTION_MAP_READY_NO_GLOSS"
        if len(promoted_packages) == len(PACKAGE_SPECS) and total_control_fails == 0 and total_plaintext == 0
        else "HUMAN_FUNCTIONAL_PROMOTION_MAP_INCOMPLETE"
    )

    cur = conn.execute(
        """
        INSERT INTO human_functional_promotion_synthesis_v1_runs
        (created_at, decision, package_count, promoted_package_count,
         promoted_book_count, cluster_count, control_fail_count,
         promoted_plaintext_gloss_count, next_question_count, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            now(),
            decision,
            len(PACKAGE_SPECS),
            len(promoted_packages),
            len({record["bookid"] for record in item_records}),
            len(clusters),
            total_control_fails,
            total_plaintext,
            len(NEXT_QUESTIONS),
            json.dumps(
                {
                    "packages": package_records,
                    "clusters": clusters,
                    "warning": "This is a promoted human-functional map only, not a canonical plaintext translation.",
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
        ),
    )
    run_id = int(cur.lastrowid)

    for record in item_records:
        conn.execute(
            """
            INSERT INTO human_functional_promotion_synthesis_v1_items
            (run_id, bookid, package_id, package_run_id, decision, cluster,
             functional_label, human_functional_reading, book_specific_note,
             context_books_json, blocked_claims_json, lexical_gloss_allowed,
             plaintext_gloss_allowed, promotion_layer, evidence_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                record["bookid"],
                record["package_id"],
                record["package_run_id"],
                record["decision"],
                record["cluster"],
                record["functional_label"],
                record["human_functional_reading"],
                record["book_specific_note"],
                json.dumps(record["context_books"], ensure_ascii=False),
                json.dumps(record["blocked_claims"], ensure_ascii=False),
                record["lexical_gloss_allowed"],
                record["plaintext_gloss_allowed"],
                record["promotion_layer"],
                json.dumps(record["evidence"], ensure_ascii=False, sort_keys=True),
            ),
        )

    for question in NEXT_QUESTIONS:
        conn.execute(
            """
            INSERT INTO human_functional_promotion_synthesis_v1_next_questions
            (run_id, question_id, priority, cluster, question,
             required_evidence, reject_if, next_action)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                question["question_id"],
                question["priority"],
                question["cluster"],
                question["question"],
                question["required_evidence"],
                question["reject_if"],
                question["next_action"],
            ),
        )

    conn.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "package_count": len(PACKAGE_SPECS),
                "promoted_package_count": len(promoted_packages),
                "promoted_book_count": len({record["bookid"] for record in item_records}),
                "cluster_count": len(clusters),
                "control_fail_count": total_control_fails,
                "promoted_plaintext_gloss_count": total_plaintext,
                "next_question_count": len(NEXT_QUESTIONS),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
