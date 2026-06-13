#!/usr/bin/env python3
"""Q31: register Bonelord Tome provenance as a 486486 question/oracle frame."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

SOURCES = [
    {
        "source_id": "FANDOM_BONELORD_TOME_FINAL",
        "source_kind": "secondary_item_page",
        "source_url": "https://tibia.fandom.com/wiki/Bonelord_Tome",
        "source_date_or_version": "Version 12.71.11017 / August 24, 2021",
        "evidence_summary": "Final item page lists the 3478 phrase, a 486486 answers line, TibiaSecrets proximity line, and knowledge-price line.",
        "supports_3478_phrase": 1,
        "supports_486486_question_oracle": 1,
        "supports_design_provenance": 0,
        "allowed_inference": "Use as phrase-level Bonelord Tome co-location evidence for 3478 and 486486.",
        "blocked_inference": "Do not split 3478, 486486, or the surrounding numbers into component glosses.",
    },
    {
        "source_id": "TIBIAWIKI_BR_BONELORD_TOME_FINAL",
        "source_kind": "secondary_item_page",
        "source_url": "https://www.tibiawiki.com.br/wiki/Bonelord_Tome",
        "source_date_or_version": "Approved page snapshot 2025-04-28; item added 2021-08-24",
        "evidence_summary": "Portuguese TibiaWiki item page lists the same sound set and says it is an official TibiaSecrets fansite item.",
        "supports_3478_phrase": 1,
        "supports_486486_question_oracle": 1,
        "supports_design_provenance": 0,
        "allowed_inference": "Use as independent wiki corroboration of the final item sound set.",
        "blocked_inference": "Do not treat the wiki page as client data or a direct 469 translation.",
    },
    {
        "source_id": "META_TIBIAQA_DESIGN_CONTEST_LUPUS",
        "source_kind": "design_provenance",
        "source_url": "https://meta.tibiaqa.com/208/fansite-item-design-contest",
        "source_date_or_version": "Lupus Aurelius answer edited 2019-02-01",
        "evidence_summary": "Original Bonelord Tome design described a cursed 469 book from Hellgate and proposed question/answer sounds including Go ask to 486486.",
        "supports_3478_phrase": 0,
        "supports_486486_question_oracle": 1,
        "supports_design_provenance": 1,
        "allowed_inference": "Use as provenance that 486486 was already framed as an answer/question target in the item concept.",
        "blocked_inference": "Do not treat rejected/proposed sounds as final in-game text unless also present in final item sources.",
    },
    {
        "source_id": "TIBIASECRETS_GREAT_CALCULATOR_CONTEXT",
        "source_kind": "community_research_context",
        "source_url": "https://www.tibiasecrets.com/article166",
        "source_date_or_version": "Article crawled 2026-05 source search",
        "evidence_summary": "TibiaSecrets quotes the Great Calculator book and frames calculation as a serious route, while admitting the solution is not concrete.",
        "supports_3478_phrase": 0,
        "supports_486486_question_oracle": 0,
        "supports_design_provenance": 0,
        "allowed_inference": "Use as external research context consistent with Q30's compiled-corpus/calculation route.",
        "blocked_inference": "Do not promote its arithmetic theory as an accepted translation.",
    },
]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q31_bonelord_tome_provenance_bridge_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q12_run_id INTEGER NOT NULL,
            q30_run_id INTEGER NOT NULL,
            source_count INTEGER NOT NULL,
            final_item_source_count INTEGER NOT NULL,
            design_provenance_source_count INTEGER NOT NULL,
            exact_3478_phrase_source_count INTEGER NOT NULL,
            question_oracle_486486_source_count INTEGER NOT NULL,
            client_or_official_data_source_count INTEGER NOT NULL,
            component_gloss_allowed_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q31_bonelord_tome_provenance_bridge_v1_items (
            run_id INTEGER NOT NULL,
            source_id TEXT NOT NULL,
            source_kind TEXT NOT NULL,
            source_url TEXT NOT NULL,
            source_date_or_version TEXT NOT NULL,
            status TEXT NOT NULL,
            evidence_summary TEXT NOT NULL,
            supports_3478_phrase INTEGER NOT NULL,
            supports_486486_question_oracle INTEGER NOT NULL,
            supports_design_provenance INTEGER NOT NULL,
            allowed_inference TEXT NOT NULL,
            blocked_inference TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, source_id)
        );
        """
    )


def latest_run_id(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT max(run_id) FROM {table}").fetchone()
    if row is None or row[0] is None:
        raise RuntimeError(f"missing required run: {table}")
    return int(row[0])


def source_status(source: dict[str, object]) -> str:
    if source["supports_3478_phrase"] and source["supports_486486_question_oracle"]:
        return "FINAL_ITEM_CROSS_WIKI_3478_486486_COLOCATION"
    if source["supports_design_provenance"] and source["supports_486486_question_oracle"]:
        return "DESIGN_PROVENANCE_486486_QUESTION_ORACLE_FRAME"
    return "CONTEXT_ONLY_NO_DIRECT_TOME_PHRASE_PROMOTION"


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q12_run_id = latest_run_id(conn, "human_q12_bonelord_tome_3478_486486_anchor_probe_v1_runs")
    q30_run_id = latest_run_id(conn, "human_q30_great_calculator_compiled_corpus_spine_map_v1_runs")

    final_item_source_count = sum(1 for source in SOURCES if source["source_kind"] == "secondary_item_page")
    design_provenance_source_count = sum(1 for source in SOURCES if source["supports_design_provenance"])
    exact_3478_phrase_source_count = sum(1 for source in SOURCES if source["supports_3478_phrase"])
    question_oracle_486486_source_count = sum(1 for source in SOURCES if source["supports_486486_question_oracle"])
    client_or_official_data_source_count = 0
    component_gloss_allowed_count = 0
    canonical_promotion_allowed_count = 0
    decision = (
        "Q31_BONELORD_TOME_PROVENANCE_STRENGTHENS_486486_QUESTION_ORACLE_FRAME_NO_COMPONENT_GLOSS"
        if exact_3478_phrase_source_count >= 2
        and question_oracle_486486_source_count >= 3
        and design_provenance_source_count >= 1
        and component_gloss_allowed_count == 0
        and canonical_promotion_allowed_count == 0
        else "Q31_BONELORD_TOME_PROVENANCE_REQUIRES_REVIEW"
    )
    payload = {
        "question": "Does Bonelord Tome provenance add a safer human route for 486486?",
        "answer": (
            "Yes, as a question/answer/oracle frame only. Final item pages co-locate 3478 and 486486, and the original design concept already used 486486 as an answer target."
        ),
        "allowed_reading": "Prioritize 486486 as a phrase-level source/answer/attention anchor in Bonelord Tome contexts.",
        "blocked_reading": "No component gloss for 486486, 3478, or any Knightmare phrase number.",
        "source_verification_status": "secondary_item_pages_plus_design_provenance; still not direct client extraction",
        "next_action": "Search for exact in-game/client data or official fansite award pages before upgrading source verification.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q31_bonelord_tome_provenance_bridge_v1_runs (
                created_at, decision, q12_run_id, q30_run_id, source_count,
                final_item_source_count, design_provenance_source_count,
                exact_3478_phrase_source_count, question_oracle_486486_source_count,
                client_or_official_data_source_count, component_gloss_allowed_count,
                canonical_promotion_allowed_count, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                q12_run_id,
                q30_run_id,
                len(SOURCES),
                final_item_source_count,
                design_provenance_source_count,
                exact_3478_phrase_source_count,
                question_oracle_486486_source_count,
                client_or_official_data_source_count,
                component_gloss_allowed_count,
                canonical_promotion_allowed_count,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q31_bonelord_tome_provenance_bridge_v1_items (
                run_id, source_id, source_kind, source_url, source_date_or_version,
                status, evidence_summary, supports_3478_phrase,
                supports_486486_question_oracle, supports_design_provenance,
                allowed_inference, blocked_inference, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    str(source["source_id"]),
                    str(source["source_kind"]),
                    str(source["source_url"]),
                    str(source["source_date_or_version"]),
                    source_status(source),
                    str(source["evidence_summary"]),
                    int(source["supports_3478_phrase"]),
                    int(source["supports_486486_question_oracle"]),
                    int(source["supports_design_provenance"]),
                    str(source["allowed_inference"]),
                    str(source["blocked_inference"]),
                    j(source),
                )
                for source in SOURCES
            ],
        )

    print(
        j(
            {
                "run_id": run_id,
                "decision": decision,
                "source_count": len(SOURCES),
                "final_item_source_count": final_item_source_count,
                "design_provenance_source_count": design_provenance_source_count,
                "exact_3478_phrase_source_count": exact_3478_phrase_source_count,
                "question_oracle_486486_source_count": question_oracle_486486_source_count,
                "client_or_official_data_source_count": client_or_official_data_source_count,
                "component_gloss_allowed_count": component_gloss_allowed_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
            }
        )
    )


if __name__ == "__main__":
    main()
