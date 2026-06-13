#!/usr/bin/env python3
"""Q2 audit: does the Chayenne 469 reply have an explicit trusted gloss?"""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

CHAYENNE_DIGITS = "114514519485611451908304576512282177 6612527570584"
CHAYENNE_ROW0_SHAPE = "AEFIEIEFIIVFAEATVAT"


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q2_chayenne_explicit_gloss_live_audit_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            source_count INTEGER NOT NULL,
            exact_sequence_attested_count INTEGER NOT NULL,
            explicit_gloss_count INTEGER NOT NULL,
            plaintext_promotable_count INTEGER NOT NULL,
            method_only_source_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q2_chayenne_explicit_gloss_live_audit_v1_items (
            run_id INTEGER NOT NULL,
            source_id TEXT NOT NULL,
            source_type TEXT NOT NULL,
            url TEXT NOT NULL,
            exact_sequence_attested INTEGER NOT NULL,
            explicit_gloss_found INTEGER NOT NULL,
            plaintext_promotable INTEGER NOT NULL,
            status TEXT NOT NULL,
            note TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, source_id)
        );
        """
    )


def source(
    source_id: str,
    source_type: str,
    url: str,
    exact_sequence_attested: int,
    explicit_gloss_found: int,
    plaintext_promotable: int,
    status: str,
    note: str,
    evidence: object,
) -> dict[str, object]:
    return {
        "source_id": source_id,
        "source_type": source_type,
        "url": url,
        "exact_sequence_attested": exact_sequence_attested,
        "explicit_gloss_found": explicit_gloss_found,
        "plaintext_promotable": plaintext_promotable,
        "status": status,
        "note": note,
        "evidence_json": json.dumps(evidence, ensure_ascii=False, sort_keys=True),
    }


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    sources = [
        source(
            "portaltibia_interview_pt",
            "fansite_interview_with_cipsoft_content_lead",
            "https://portaltibia.com.br/pt/entrevista-com-chayenne-lider-do-time-de-content-management-da-cipsoft/",
            1,
            0,
            0,
            "EXACT_SEQUENCE_REPLY_NO_GLOSS",
            "The interview question asks about Beholder language and the answer is only the 469-like reply plus emoticons; no meaning is supplied.",
            {
                "checked": "2026-05-11",
                "lines": "85-87",
                "sequence": CHAYENNE_DIGITS,
                "row0_shape": CHAYENNE_ROW0_SHAPE,
            },
        ),
        source(
            "portaltibia_forum_interview_en",
            "forum_mirror_of_interview",
            "https://forum.portaltibia.com.br/topic/11420-entrevista-com-chayenne/",
            1,
            0,
            0,
            "EXACT_SEQUENCE_REPLY_NO_GLOSS",
            "The English forum mirror preserves the same question and Chayenne's numeric answer, but gives no translation.",
            {
                "checked": "2026-05-11",
                "lines": "254-256",
                "sequence": CHAYENNE_DIGITS,
                "row0_shape": CHAYENNE_ROW0_SHAPE,
            },
        ),
        source(
            "tibiawiki_br_469_chayenne",
            "wiki_context",
            "https://www.tibiawiki.com.br/index.php?stableid=148406&title=469",
            1,
            0,
            0,
            "EXACT_SEQUENCE_CONTEXT_NO_GLOSS",
            "The page records the 2009 Chayenne interview sequence and frames it as a CipSoft joke that the language could be translated, not as an explicit meaning.",
            {
                "checked": "2026-05-11",
                "lines": "43-48",
                "sequence": CHAYENNE_DIGITS,
                "row0_shape": CHAYENNE_ROW0_SHAPE,
            },
        ),
        source(
            "s2ward_469_chayenne_corpus",
            "community_corpus",
            "https://github.com/s2ward/469",
            1,
            0,
            0,
            "EXACT_SEQUENCE_CORPUS_NO_GLOSS",
            "The corpus quotes the Chayenne reply and links it with in-game/NPC anchors, but does not give an explicit translation.",
            {
                "checked": "2026-05-11",
                "lines": "291-297",
                "sequence": CHAYENNE_DIGITS,
                "row0_shape": CHAYENNE_ROW0_SHAPE,
            },
        ),
        source(
            "tibiasecrets_hellgate_averages_chayenne",
            "secondary_research_method_context",
            "https://www.tibiasecrets.com/article166",
            0,
            0,
            0,
            "METHOD_CONTEXT_NO_EXACT_GLOSS",
            "The article treats Chayenne and other NPC/poll phrases as excerpts present in Hellgate context, not as complete translated books or explicit glosses.",
            {
                "checked": "2026-05-11",
                "lines": "84-88",
                "sequence": CHAYENNE_DIGITS,
                "row0_shape": CHAYENNE_ROW0_SHAPE,
            },
        ),
    ]

    exact_sequence_attested_count = sum(int(row["exact_sequence_attested"]) for row in sources)
    explicit_gloss_count = sum(int(row["explicit_gloss_found"]) for row in sources)
    plaintext_promotable_count = sum(int(row["plaintext_promotable"]) for row in sources)
    method_only_source_count = sum(1 for row in sources if row["status"] == "METHOD_CONTEXT_NO_EXACT_GLOSS")
    decision = (
        "Q2_CHAYENNE_EXPLICIT_GLOSS_REJECTED_SEQUENCE_ATTESTED_FRAME_ONLY"
        if exact_sequence_attested_count and explicit_gloss_count == 0 and plaintext_promotable_count == 0
        else "Q2_CHAYENNE_REQUIRES_MANUAL_REVIEW"
    )

    payload = {
        "question": "Can any primary or trusted in-game source give the exact Chayenne sequence plus explicit meaning?",
        "answer": "No current checked source gives an explicit gloss; use Chayenne only as an external frame/register witness.",
        "sequence": CHAYENNE_DIGITS,
        "row0_shape": CHAYENNE_ROW0_SHAPE,
        "promotion_rule": "sequence/context attestation is allowed; plaintext/gloss promotion remains blocked",
        "next_probe": "Search other external/NPC phrases for reusable shape frames and in-game branch behavior rather than direct prose.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q2_chayenne_explicit_gloss_live_audit_v1_runs (
                created_at, decision, source_count, exact_sequence_attested_count,
                explicit_gloss_count, plaintext_promotable_count, method_only_source_count,
                payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                len(sources),
                exact_sequence_attested_count,
                explicit_gloss_count,
                plaintext_promotable_count,
                method_only_source_count,
                json.dumps(payload, ensure_ascii=False, sort_keys=True),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q2_chayenne_explicit_gloss_live_audit_v1_items (
                run_id, source_id, source_type, url, exact_sequence_attested,
                explicit_gloss_found, plaintext_promotable, status, note, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    row["source_id"],
                    row["source_type"],
                    row["url"],
                    row["exact_sequence_attested"],
                    row["explicit_gloss_found"],
                    row["plaintext_promotable"],
                    row["status"],
                    row["note"],
                    row["evidence_json"],
                )
                for row in sources
            ],
        )

    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "source_count": len(sources),
                "exact_sequence_attested_count": exact_sequence_attested_count,
                "explicit_gloss_count": explicit_gloss_count,
                "plaintext_promotable_count": plaintext_promotable_count,
                "method_only_source_count": method_only_source_count,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
