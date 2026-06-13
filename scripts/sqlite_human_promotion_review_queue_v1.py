#!/usr/bin/env python3
"""Materialize promotion-review packages from atlas v6 shadow candidates."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

PACKAGE_RULES = {
    "B_R02_NAESE_SLOT_BRIDGE": {
        "package_id": "PKG_R02_NAESE_SLOT_BRIDGE_51_53",
        "priority": 1,
        "review_goal": "test whether Books 51/53 can promote a narrow R02->NAESE/C68 slot-bridge label",
        "next_test": "contrast 51/53 against Book22 canonical NAESE slot, Book46 connector, Book42 weak hybrid, and R02/LIVRN micro controls",
        "blocked_promotion": "no R02/NAESE/C68 lexical gloss and no full-book plaintext",
    },
    "B_NAESE_BENNA_COMPOSITE": {
        "package_id": "PKG_NAESE_BENNA_COMPOSITE_5_9",
        "priority": 2,
        "review_goal": "test whether Books 5/9 can promote a narrow slot-to-formula composite-frame label",
        "next_test": "contrast 5/9 against Book22 slot-only, Books 40/50/69 BENNA body, and O23/C86 negatives",
        "blocked_promotion": "no BENNA or NAESE word gloss and no copied prose between Books 5/9",
    },
    "B_BENNA_C86_VNCTIIN_FORMULA_HANDOFF": {
        "package_id": "PKG_BENNA_C86_VNCTIIN_HANDOFF_10_35",
        "priority": 3,
        "review_goal": "test whether Books 10/35 can promote a BENNA formula handoff into C86/VNCTIIN context label",
        "next_test": "contrast 10/35 against C86 payload corridor books 2/27/67 and BENNA body controls 40/50/69",
        "blocked_promotion": "no BENNA/C86/VNCTIIN/LTAST lexical gloss",
    },
    "B_C86_VNCTIIN_PAYLOAD_CORRIDOR": {
        "package_id": "PKG_C86_VNCTIIN_PAYLOAD_2_27_67",
        "priority": 4,
        "review_goal": "test whether Books 2/27/67 can promote a narrow C86 payload-to-VNCTIIN/C68 corridor label",
        "next_test": "split 2 NAESE/C68 slot from 27/67 TAILBETFTE suffix and compare against VNCTIIN-only controls 23/24",
        "blocked_promotion": "no C86/VNCTIIN/C68 lexical gloss and no single corridor sentence",
    },
    "B_BOOK54_PAIR_LOCAL_SPINE": {
        "package_id": "PKG_BOOK54_LOCAL_PAIR_SPINE",
        "priority": 5,
        "review_goal": "test whether Book54 can promote a narrow local-pair shared-spine label with Book20",
        "next_test": "contrast Book54 against Book20, Book25/39 local pair, and zero-boundary controls",
        "blocked_promotion": "no shared block word gloss and no zero/taboo semantic import",
    },
    "B_BOOK7_PHASE_MATHEMAGIC": {
        "package_id": "PKG_BOOK7_PHASE_BRIDGE",
        "priority": 6,
        "review_goal": "test whether Book7 can promote a narrow phase-continuity bridge label",
        "next_test": "contrast Book7 against Book6 continuity-only and Books19/31/57 TIINNEF+VNCTIIN phase controls",
        "blocked_promotion": "no NEIAAETTA or TIINNEF lexical gloss",
    },
    "B_BOOK49_MATH49_REGISTER": {
        "package_id": "PKG_BOOK49_REPEAT_REGISTER",
        "priority": 7,
        "review_goal": "test whether Book49 can promote a narrow self-contained repeat/register label",
        "next_test": "contrast Book49 against Book55 internal repeat and other high-repeat controls",
        "blocked_promotion": "no 49 dictionary key and no refrain plaintext",
    },
    "B_CHAYENNE_FRAME_REGISTER": {
        "package_id": "PKG_CHAYENNE_FRAME_BRANCHES_8_37_66",
        "priority": 8,
        "review_goal": "test whether Books 8/37/66 can promote a register-frame branch label tied to Chayenne shape",
        "next_test": "keep Book63 audit-frame as control and verify exact/near-frame boundaries before any package promotion",
        "blocked_promotion": "no Chayenne phrase translation and no single English sentence for the shared frame",
    },
}


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_promotion_review_queue_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            atlas_v6_audit_run_id INTEGER NOT NULL,
            package_count INTEGER NOT NULL,
            candidate_count INTEGER NOT NULL,
            top_package_id TEXT NOT NULL,
            canonical_promotion_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_promotion_review_queue_v1_packages (
            run_id INTEGER NOT NULL,
            package_id TEXT NOT NULL,
            source_bridge_id TEXT NOT NULL,
            priority INTEGER NOT NULL,
            book_ids_json TEXT NOT NULL,
            candidate_count INTEGER NOT NULL,
            review_goal TEXT NOT NULL,
            next_test TEXT NOT NULL,
            blocked_promotion TEXT NOT NULL,
            package_status TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, package_id)
        );

        CREATE TABLE IF NOT EXISTS human_promotion_review_queue_v1_items (
            run_id INTEGER NOT NULL,
            package_id TEXT NOT NULL,
            bookid TEXT NOT NULL,
            source_bridge_id TEXT NOT NULL,
            likely_speech_act TEXT NOT NULL,
            plausible_human_reading TEXT NOT NULL,
            confidence_tier TEXT NOT NULL,
            support_level TEXT NOT NULL,
            review_tier TEXT NOT NULL,
            promotion_status TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        );
        """
    )


def max_id(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT max(run_id) AS run_id FROM {table}").fetchone()
    if row is None or row["run_id"] is None:
        raise RuntimeError(f"missing required run: {table}")
    return int(row["run_id"])


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    audit_run_id = max_id(conn, "human_atlas_v6_contradiction_audit_v1_items")
    audit_summary = conn.execute(
        "SELECT * FROM human_atlas_v6_contradiction_audit_v1_runs WHERE run_id=?",
        (audit_run_id,),
    ).fetchone()
    if audit_summary is None:
        raise RuntimeError("missing atlas v6 audit summary")
    if int(audit_summary["fail_count"]) != 0 or int(audit_summary["warn_count"]) != 0:
        raise RuntimeError("atlas v6 audit is not clean; do not build promotion queue")

    rows = conn.execute(
        """
        SELECT a.*, q.review_tier, q.audit_status
        FROM human_atlas_v6_contradiction_audit_v1_items q
        JOIN human_translation_atlas_v6_items a
          ON a.target_id=q.bookid
         AND a.run_id=(SELECT max(run_id) FROM human_translation_atlas_v6_items)
        WHERE q.run_id=?
          AND q.review_tier='PROMOTION_REVIEW_CANDIDATE'
        ORDER BY a.source_bridge_id, CAST(a.target_id AS INTEGER)
        """,
        (audit_run_id,),
    ).fetchall()
    packages: dict[str, list[sqlite3.Row]] = defaultdict(list)
    for row in rows:
        bridge_id = str(row["source_bridge_id"])
        if bridge_id not in PACKAGE_RULES:
            raise RuntimeError(f"missing package rule for candidate bridge {bridge_id}")
        packages[bridge_id].append(row)

    sorted_bridge_ids = sorted(packages, key=lambda bridge_id: (PACKAGE_RULES[bridge_id]["priority"], bridge_id))
    top_package_id = PACKAGE_RULES[sorted_bridge_ids[0]]["package_id"] if sorted_bridge_ids else ""
    decision = "HUMAN_PROMOTION_REVIEW_QUEUE_READY_NO_CANONICAL_PROMOTION"
    cur = conn.execute(
        """
        INSERT INTO human_promotion_review_queue_v1_runs
        (created_at, decision, atlas_v6_audit_run_id, package_count,
         candidate_count, top_package_id, canonical_promotion_count, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            now(),
            decision,
            audit_run_id,
            len(packages),
            len(rows),
            top_package_id,
            0,
            json.dumps(
                {
                    "principle": "queue promotion-review packages only; no canonical gloss promotion",
                    "source_audit_decision": audit_summary["decision"],
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
        ),
    )
    run_id = int(cur.lastrowid)
    for bridge_id in sorted_bridge_ids:
        rule = PACKAGE_RULES[bridge_id]
        package_rows = sorted(packages[bridge_id], key=lambda row: int(row["target_id"]))
        book_ids = [str(row["target_id"]) for row in package_rows]
        conn.execute(
            """
            INSERT INTO human_promotion_review_queue_v1_packages
            (run_id, package_id, source_bridge_id, priority, book_ids_json,
             candidate_count, review_goal, next_test, blocked_promotion,
             package_status, evidence_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                rule["package_id"],
                bridge_id,
                rule["priority"],
                json.dumps(book_ids, ensure_ascii=False),
                len(package_rows),
                rule["review_goal"],
                rule["next_test"],
                rule["blocked_promotion"],
                "READY_FOR_FALSIFICATION_NO_PROMOTION",
                json.dumps(
                    {
                        "books": book_ids,
                        "confidence_tiers": sorted({str(row["confidence_tier"]) for row in package_rows}),
                        "support_levels": sorted({str(row["support_level"]) for row in package_rows}),
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                ),
            ),
        )
        for row in package_rows:
            conn.execute(
                """
                INSERT INTO human_promotion_review_queue_v1_items
                (run_id, package_id, bookid, source_bridge_id,
                 likely_speech_act, plausible_human_reading,
                 confidence_tier, support_level, review_tier,
                 promotion_status, evidence_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    rule["package_id"],
                    str(row["target_id"]),
                    bridge_id,
                    row["likely_speech_act"],
                    row["plausible_human_reading"],
                    row["confidence_tier"],
                    row["support_level"],
                    row["review_tier"],
                    row["promotion_status"],
                    json.dumps(
                        {
                            "anchor_ids_json": row["anchor_ids_json"],
                            "blocked_claims_json": row["blocked_claims_json"],
                            "blocked_overreach": row["blocked_overreach"],
                            "falsifier": row["falsifier"],
                            "next_probe": row["next_probe"],
                        },
                        ensure_ascii=False,
                        sort_keys=True,
                    ),
                ),
            )

    conn.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "package_count": len(packages),
                "candidate_count": len(rows),
                "top_package_id": top_package_id,
                "canonical_promotion_count": 0,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
