#!/usr/bin/env python3
"""Seed first human-readable shadow readings for selected frontier books.

These are not translations. They are controlled paraphrase hypotheses designed
to create falsifiable next work while preserving the canonical no-gloss layer.
"""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"


SEED_ITEMS = [
    {
        "bookid": "49",
        "route_id": "R5_PLAUSIBLE_PROSE_SHADOW",
        "candidate_status": "SHADOW_DRAFT_AUDIT_ONLY",
        "likely_speech_act": "self-contained repeat formula or chant",
        "human_paraphrase": "A closed formula that appears to bind or repeat itself; likely a calibration/refrain rather than narrative prose.",
        "blocked_claims": [
            "No lexical word gloss for IAEN/NEEN/etc.",
            "No proof that the repeated shape means a ritual phrase.",
            "No canonical translation promotion.",
        ],
        "falsifier": "If a held-out self-contained repeat behaves as ordinary narrative or maps cleanly to another functional tag.",
        "next_probe": "Compare Book 49 against all self-contained repeat and display-drift families; test whether repeat density predicts formula/register class.",
    },
    {
        "bookid": "12",
        "route_id": "R5_PLAUSIBLE_PROSE_SHADOW",
        "candidate_status": "SHADOW_DRAFT_AUDIT_ONLY",
        "likely_speech_act": "compact Book30-family shared-base terminal witness",
        "human_paraphrase": "A short Book30-family witness: it is almost entirely the shared TAESESTIEN/VNSBLFSINNAI base also present in Book 21, with no direct O23/ONAF/FNAAST endpoint marker.",
        "blocked_claims": [
            "The shared Book30-family spine has function, not meaning.",
            "O23/endpoint influence is indirect through frontier anchoring and is not present as a direct marker in Book 12.",
            "No word-level prose translation.",
        ],
        "falsifier": "If Book 12 does not share the Book21 base or if direct O23 marker evidence appears in Book12 controls.",
        "next_probe": "Use Book12/21 as shared-base controls and test whether terminal wording should stay structural rather than O23-derived.",
    },
    {
        "bookid": "30",
        "route_id": "R5_PLAUSIBLE_PROSE_SHADOW",
        "candidate_status": "SHADOW_DRAFT_AUDIT_ONLY",
        "likely_speech_act": "alternate Book30-family spine witness",
        "human_paraphrase": "An alternate Book30-family witness: it preserves TAESESTIEN and the shared VNSBLFSINNAI spine, but diverges from the long-tail form used by Books 12/21/26.",
        "blocked_claims": [
            "No proof that this is a title, name, or object label.",
            "NAESE-variant anchoring is structural only.",
            "Book 30 is not proven to be the full family centroid.",
            "No canonical translation promotion.",
        ],
        "falsifier": "If Book 30 does not preserve the same VNSBLFSINNAI spine or if the alternate tail has no family relation.",
        "next_probe": "Treat Book 30 as an alternate spine witness and test whether 12/21/26 form a separate long-tail subfamily.",
    },
    {
        "bookid": "26",
        "route_id": "R5_PLAUSIBLE_PROSE_SHADOW",
        "candidate_status": "SHADOW_DRAFT_AUDIT_ONLY",
        "likely_speech_act": "Book30-family spine introduced from a branch/prefix",
        "human_paraphrase": "A branch-prefixed transition into the shared VNSBLFSINNAI spine and long-tail form, notably without the TAESESTIEN subcomponent seen in Books 12/21/30.",
        "blocked_claims": [
            "VINVIN/C86 payload branch is only a frontier relation.",
            "The prefix cannot yet be read as a word or command.",
            "TAESESTIEN is not universal across the family.",
            "No canonical translation promotion.",
        ],
        "falsifier": "If the prefix does not align with any branch/context role or if the long-tail relation fails across held-out examples.",
        "next_probe": "Test whether the FLEEIIFTEI/NBLIBEIEFSEENE prefix selects the same role as the Book17/26 frontier relation while preserving the VNSBLFSINNAI long-tail subfamily.",
    },
    {
        "bookid": "7",
        "route_id": "R5_PLAUSIBLE_PROSE_SHADOW",
        "candidate_status": "SHADOW_DRAFT_AUDIT_ONLY",
        "likely_speech_act": "phase continuation or handoff line",
        "human_paraphrase": "A phase-continuity line: it appears to carry a sequence through a local phase anchor rather than introduce a new independent message.",
        "blocked_claims": [
            "NEIAAETTA and TIINNEF are phase anchors, not translated words.",
            "No known external/in-game prose meaning for the sequence.",
            "No canonical translation promotion.",
        ],
        "falsifier": "If Book7-family phase anchors do not predict continuity in Books 6/7/19/31/57.",
        "next_probe": "Build a small phase-chain graph for Books 6/7/19/31/57 and test directionality.",
    },
    {
        "bookid": "21",
        "route_id": "R5_PLAUSIBLE_PROSE_SHADOW",
        "candidate_status": "SHADOW_DRAFT_AUDIT_ONLY",
        "likely_speech_act": "Book30-family spine plus bridge/tail extension",
        "human_paraphrase": "A Book30-family shared-base witness that preserves nearly all of Book 12's base and adds the TIVNSENI*LAELBEV tail extension, without direct O23/ONAF/FNAAST markers.",
        "blocked_claims": [
            "R02 slot bridge is structural, not a translated connective.",
            "Tail content is unknown.",
            "The Book21 extension is not an O23 endpoint gloss.",
            "No canonical translation promotion.",
        ],
        "falsifier": "If the added tail does not correlate with bridge behavior or if the Book12/21 shared base fails.",
        "next_probe": "Compare TIVNSENI*LAELBEV against R02 bridge books and Book30-family books without the extension.",
    },
    {
        "bookid": "54",
        "route_id": "R5_PLAUSIBLE_PROSE_SHADOW",
        "candidate_status": "SHADOW_DRAFT_AUDIT_ONLY",
        "likely_speech_act": "shared-core local pair member with its own tail",
        "human_paraphrase": "An abbreviated member of a local pair that preserves the shared LTFNTFEIFAIFAINIIETNEEIVN block from Book 20 while using a shorter prefix and its own small tail.",
        "blocked_claims": [
            "The pair with Book 20 is alignment evidence only.",
            "Truncation does not imply abbreviation in plaintext.",
            "The shared block is not proven to be a lexical phrase.",
            "No canonical translation promotion.",
        ],
        "falsifier": "If Book 54 does not align mechanically with Book 20 or if the shared block does not predict local pair behavior.",
        "next_probe": "Use the Book20/54 alignment view to test whether LTFNTFEIFAIFAINIIETNEEIVN behaves as a reusable local-pair spine or only as an accidental overlap.",
    },
]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_shadow_reading_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            route_run_id INTEGER NOT NULL,
            item_count INTEGER NOT NULL,
            canonical_promotion_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_shadow_reading_v1_items (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            route_id TEXT NOT NULL,
            candidate_status TEXT NOT NULL,
            likely_speech_act TEXT NOT NULL,
            human_paraphrase TEXT NOT NULL,
            anchors_json TEXT NOT NULL,
            functional_basis_json TEXT NOT NULL,
            blocked_claims_json TEXT NOT NULL,
            falsifier TEXT NOT NULL,
            next_probe TEXT NOT NULL,
            canonical_promotion_status TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        );
        """
    )


def latest_route_run(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT max(run_id) AS run_id FROM human_translation_route_v1_runs").fetchone()
    if row is None or row["run_id"] is None:
        raise RuntimeError("Run sqlite_human_translation_routes_v1.py first")
    return int(row["run_id"])


def book_context(conn: sqlite3.Connection) -> dict[str, dict[str, object]]:
    rows = conn.execute(
        """
        SELECT b.bookid, b.functional_tags_json, b.honest_text, b.evidence_json,
               t.symbol_text,
               f.anchor_bookid, f.anchor_role, f.math_relation_status, f.source_frontier_status
        FROM final_honest_reading_v19_books b
        LEFT JOIN row0_variant_book_tokens t
          ON t.bookid=b.bookid
         AND t.run_id=(SELECT max(run_id) FROM row0_variant_book_tokens)
        LEFT JOIN human_translation_route_v1_frontier_books f
          ON f.bookid=b.bookid
         AND f.run_id=(SELECT max(run_id) FROM human_translation_route_v1_frontier_books)
        WHERE b.run_id=(SELECT max(run_id) FROM final_honest_reading_v19_books)
        """
    ).fetchall()
    return {str(row["bookid"]): dict(row) for row in rows}


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    route_run_id = latest_route_run(conn)
    context = book_context(conn)
    payload = {
        "policy": "shadow paraphrases only; unknowns and blockers remain explicit",
        "route_run_id": route_run_id,
        "seed_books": [item["bookid"] for item in SEED_ITEMS],
    }
    cur = conn.execute(
        """
        INSERT INTO human_shadow_reading_v1_runs
        (created_at, decision, route_run_id, item_count, canonical_promotion_count, payload_json)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            now(),
            "HUMAN_SHADOW_READINGS_SEEDED_NOT_PROMOTED",
            route_run_id,
            len(SEED_ITEMS),
            0,
            json.dumps(payload, ensure_ascii=False, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)

    for item in SEED_ITEMS:
        ctx = context.get(item["bookid"], {})
        anchors = {
            "route_run_id": route_run_id,
            "frontier_anchor_bookid": ctx.get("anchor_bookid"),
            "frontier_anchor_role": ctx.get("anchor_role"),
            "math_relation_status": ctx.get("math_relation_status"),
            "source_frontier_status": ctx.get("source_frontier_status"),
            "in_game_policy": "must be backed by registry sources before any stronger claim",
        }
        functional_basis = {
            "functional_tags_json": ctx.get("functional_tags_json"),
            "honest_text": ctx.get("honest_text"),
            "symbol_text": ctx.get("symbol_text"),
        }
        evidence = {
            "canonical_layer": "final_honest_reading_v19",
            "gloss_allowed": False,
            "promotion_rule": "requires exact or predictive in-game support beyond this draft",
        }
        conn.execute(
            """
            INSERT INTO human_shadow_reading_v1_items
            (run_id, bookid, route_id, candidate_status, likely_speech_act,
             human_paraphrase, anchors_json, functional_basis_json,
             blocked_claims_json, falsifier, next_probe,
             canonical_promotion_status, evidence_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                item["bookid"],
                item["route_id"],
                item["candidate_status"],
                item["likely_speech_act"],
                item["human_paraphrase"],
                json.dumps(anchors, ensure_ascii=False, sort_keys=True),
                json.dumps(functional_basis, ensure_ascii=False, sort_keys=True),
                json.dumps(item["blocked_claims"], ensure_ascii=False, sort_keys=True),
                item["falsifier"],
                item["next_probe"],
                "NOT_PROMOTED",
                json.dumps(evidence, ensure_ascii=False, sort_keys=True),
            ),
        )

    conn.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": "HUMAN_SHADOW_READINGS_SEEDED_NOT_PROMOTED",
                "route_run_id": route_run_id,
                "item_count": len(SEED_ITEMS),
                "canonical_promotion_count": 0,
                "seed_books": [item["bookid"] for item in SEED_ITEMS],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
