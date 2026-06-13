#!/usr/bin/env python3
"""Q22: prioritize cross-quest human shadow routes after the Avar slot clue."""

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
        CREATE TABLE IF NOT EXISTS human_q22_cross_quest_shadow_route_prioritization_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q21_run_id INTEGER NOT NULL,
            anchor_corpus_run_id INTEGER NOT NULL,
            mathemagic_synthesis_run_id INTEGER NOT NULL,
            route_count INTEGER NOT NULL,
            active_route_count INTEGER NOT NULL,
            source_verified_route_count INTEGER NOT NULL,
            direct_gloss_route_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q22_cross_quest_shadow_route_prioritization_v1_items (
            run_id INTEGER NOT NULL,
            route_id TEXT NOT NULL,
            priority INTEGER NOT NULL,
            route_class TEXT NOT NULL,
            status TEXT NOT NULL,
            anchor_refs_json TEXT NOT NULL,
            source_urls_json TEXT NOT NULL,
            source_basis TEXT NOT NULL,
            human_hypothesis TEXT NOT NULL,
            next_probe TEXT NOT NULL,
            promotion_gate TEXT NOT NULL,
            rejection_rule TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, route_id)
        );
        """
    )


def latest_row(conn: sqlite3.Connection, table: str) -> sqlite3.Row:
    row = conn.execute(f"SELECT * FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    if row is None:
        raise RuntimeError(f"missing required run: {table}")
    return row


def anchor_items(conn: sqlite3.Connection, run_id: int) -> dict[str, dict[str, object]]:
    return {
        str(row["anchor_id"]): dict(row)
        for row in conn.execute(
            """
            SELECT *
            FROM human_ingame_anchor_corpus_v1_items
            WHERE run_id=?
            """,
            (run_id,),
        )
    }


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q21 = latest_row(conn, "human_q21_avar_tar_narcissist_lore_plausibility_v1_runs")
    anchor_run = latest_row(conn, "human_ingame_anchor_corpus_v1_runs")
    math_run = latest_row(conn, "human_mathemagic_shadow_synthesis_v1_runs")
    anchors = anchor_items(conn, int(anchor_run["run_id"]))

    routes = [
        {
            "route_id": "EDITORIAL_VARIANT_SEMANTIC_SLOT_ROUTE",
            "priority": 1,
            "route_class": "exact_external_variant",
            "status": "ACTIVE_SOURCE_SEARCH",
            "anchor_refs": ["Q19_TIBIA_ORG_AVAR_VARIANT", "Q20_VAIN_TO_NARCISSIST", "Q21_AVAR_PERSONA"],
            "source_urls": [
                "https://web.archive.org/web/20200915225804id_/http://www.tibia.org/",
                "https://www.tibiaqa.com/25041/is-avar-tar-lying-about-his-stories",
            ],
            "source_basis": "A primary archived external variant changes exactly one Avar word slot in a themed character context.",
            "human_hypothesis": "Single-slot editorial variants can reveal intended semantic pressure without translating whole books.",
            "next_probe": "Search old official/fansite HTML, item sound lists, and archived pages for other 469 variants with one-slot changes.",
            "promotion_gate": "Exact sequence provenance, one-slot contrast, contextual explanation, and independent non-contradiction.",
            "rejection_rule": "Reject if the variant cannot be tied to a source/context or if it creates free-form prose without contrast.",
            "source_verified": 1,
            "direct_gloss": 0,
            "evidence": {"q21": dict(q21)},
        },
        {
            "route_id": "AVAR_PERSONA_REGISTER_ROUTE",
            "priority": 2,
            "route_class": "npc_persona_register",
            "status": "ACTIVE_SHADOW_CONTEXT",
            "anchor_refs": ["AVAR_TAR_POEM_REGISTER"],
            "source_urls": [
                "https://tibia.fandom.com/wiki/Avar_Tar/Transcripts",
                "https://tibiasecrets.com/Avar-Tar",
            ],
            "source_basis": "Avar Tar is an in-game speaker with boastful persona and an explicit Bonelord-language poem trigger.",
            "human_hypothesis": "Some external/NPC 469 phrases may encode speaker register or joke context rather than neutral book prose.",
            "next_probe": "Compare Avar slot families against other speaker/persona phrases before mapping anything onto Hellgate books.",
            "promotion_gate": "Accept only phrase/register labels unless a source gives exact sequence plus explicit meaning.",
            "rejection_rule": "Reject any attempt to use Avar unreliability as a general book dictionary.",
            "source_verified": 1,
            "direct_gloss": 0,
            "evidence": {"anchor": anchors.get("AVAR_TAR_POEM_REGISTER")},
        },
        {
            "route_id": "MATHEMAGIC_OPERATOR_SELECTOR_ROUTE",
            "priority": 3,
            "route_class": "quest_math_operator",
            "status": "ACTIVE_OPERATOR_TEST",
            "anchor_refs": ["AWB_469_LANGUAGE_MATHEMAGIC", "PARADOX_1_PLUS_1_KEYS"],
            "source_urls": [
                "https://tibia.fandom.com/wiki/A_Wrinkled_Bonelord/Transcripts",
                "https://www.tibia-wiki.net/wiki/Paradox_Tower_Quest/Spoiler",
            ],
            "source_basis": "Wrinkled Bonelord says the language relies on mathemagic; Paradox/Mintwallin gives variable 1+1 operator behavior.",
            "human_hypothesis": "Mathemagics should act as selector/operator machinery over books, slots, and variants, not as a word key.",
            "next_probe": "Use 1/13/49/94 only to rank held-out book/slot candidates and require measured structural improvement.",
            "promotion_gate": "Held-out improvement across source-independent families, zero direct plaintext promotion.",
            "rejection_rule": "Reject any 1/13/49/94 reading that behaves like a dictionary or works only by story fitting.",
            "source_verified": 1,
            "direct_gloss": 0,
            "evidence": {
                "math_run": dict(math_run),
                "anchors": [
                    anchors.get("AWB_469_LANGUAGE_MATHEMAGIC"),
                    anchors.get("PARADOX_1_PLUS_1_KEYS"),
                ],
            },
        },
        {
            "route_id": "GREAT_CALCULATOR_COMPILED_CORPUS_ROUTE",
            "priority": 4,
            "route_class": "lore_corpus_structure",
            "status": "ACTIVE_STRUCTURAL_MODEL",
            "anchor_refs": ["GREAT_CALCULATOR_GATHER_LANGUAGE"],
            "source_urls": ["https://www.tibiawiki.com.br/wiki/You_Cannot_Even_Imagine_%28Book%29"],
            "source_basis": "A translated in-game book links the Great Calculator to assembling/gathering the Bonelord language.",
            "human_hypothesis": "Hellgate may be a compiled corpus of formulas, spines, and fragments rather than one continuous text.",
            "next_probe": "Prioritize spine/tail/family maps and source-lineage tests before drafting full-sentence translations.",
            "promotion_gate": "A compiled-corpus model must reduce contradictions and explain repeated families better than linear prose.",
            "rejection_rule": "Reject long paraphrases that force all books into one continuous narrative.",
            "source_verified": 1,
            "direct_gloss": 0,
            "evidence": {"anchor": anchors.get("GREAT_CALCULATOR_GATHER_LANGUAGE")},
        },
        {
            "route_id": "MINOTAUR_MAGE_TRUTH_BRIDGE_ROUTE",
            "priority": 5,
            "route_class": "quest_bridge",
            "status": "NEEDS_TRANSCRIPT_AUDIT",
            "anchor_refs": ["AWB_MINOTAUR_MAGES_CLOSE_TO_TRUTH", "PARADOX_1_PLUS_1_KEYS"],
            "source_urls": [
                "https://tibia.fandom.com/wiki/A_Wrinkled_Bonelord/Transcripts",
                "https://www.tibia-wiki.net/wiki/Paradox_Tower_Quest/Spoiler",
            ],
            "source_basis": "Wrinkled Bonelord says minotaur mages are close to truth; Paradox route sends the player to Mintwallin mathemagics.",
            "human_hypothesis": "Mintwallin mathemagics may be the nearest in-game operational analogue to Bonelord mathemagic.",
            "next_probe": "Import exact A Prisoner/Riddler transcripts into SQLite and test only source-backed operator relations.",
            "promotion_gate": "Exact transcript rows plus mechanical operator benefit; no phrase gloss.",
            "rejection_rule": "Reject if the bridge remains thematic but cannot predict a structural relation.",
            "source_verified": 0,
            "direct_gloss": 0,
            "evidence": {"anchors": [anchors.get("PARADOX_1_PLUS_1_KEYS")]},
        },
        {
            "route_id": "BONELORD_TOME_CLIENT_SOUND_ROUTE",
            "priority": 6,
            "route_class": "client_sound_verification",
            "status": "BLOCKED_ON_CLIENT_OR_OFFICIAL_DATA",
            "anchor_refs": ["BONELORD_TOME_3478_486486"],
            "source_urls": [
                "https://tibia.fandom.com/wiki/Bonelord_Tome",
                "https://www.tibiawiki.com.br/wiki/Bonelord_Tome",
            ],
            "source_basis": "Secondary item pages co-locate the Knightmare-style 3478 phrase with a 486486 line.",
            "human_hypothesis": "If verified in client data, Bonelord Tome can prioritize phrase-level entity/name/formula tests.",
            "next_probe": "Acquire modern client/official item sound data and verify the sound list before stronger claims.",
            "promotion_gate": "Client or official-data confirmation plus phrase-level consistency; component gloss remains blocked.",
            "rejection_rule": "Reject stronger use until the secondary sound list is verified from client/official data.",
            "source_verified": 0,
            "direct_gloss": 0,
            "evidence": {},
        },
    ]

    active_route_count = sum(1 for route in routes if route["status"].startswith("ACTIVE"))
    source_verified_route_count = sum(int(route["source_verified"]) for route in routes)
    direct_gloss_route_count = sum(int(route["direct_gloss"]) for route in routes)
    canonical_promotion_allowed_count = 0
    decision = "Q22_CROSS_QUEST_HUMAN_SHADOW_ROUTES_PRIORITIZED_NO_GLOSS"
    payload = {
        "principle": (
            "Use in-game and close external references to rank human hypotheses; require exact evidence before any canonical gloss."
        ),
        "route_order": [route["route_id"] for route in sorted(routes, key=lambda item: item["priority"])],
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q22_cross_quest_shadow_route_prioritization_v1_runs (
                created_at, decision, q21_run_id, anchor_corpus_run_id,
                mathemagic_synthesis_run_id, route_count, active_route_count,
                source_verified_route_count, direct_gloss_route_count,
                canonical_promotion_allowed_count, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                int(q21["run_id"]),
                int(anchor_run["run_id"]),
                int(math_run["run_id"]),
                len(routes),
                active_route_count,
                source_verified_route_count,
                direct_gloss_route_count,
                canonical_promotion_allowed_count,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q22_cross_quest_shadow_route_prioritization_v1_items (
                run_id, route_id, priority, route_class, status,
                anchor_refs_json, source_urls_json, source_basis, human_hypothesis,
                next_probe, promotion_gate, rejection_rule, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    str(route["route_id"]),
                    int(route["priority"]),
                    str(route["route_class"]),
                    str(route["status"]),
                    j(route["anchor_refs"]),
                    j(route["source_urls"]),
                    str(route["source_basis"]),
                    str(route["human_hypothesis"]),
                    str(route["next_probe"]),
                    str(route["promotion_gate"]),
                    str(route["rejection_rule"]),
                    j(route["evidence"]),
                )
                for route in routes
            ],
        )

    print(
        j(
            {
                "run_id": run_id,
                "decision": decision,
                "q21_run_id": int(q21["run_id"]),
                "anchor_corpus_run_id": int(anchor_run["run_id"]),
                "mathemagic_synthesis_run_id": int(math_run["run_id"]),
                "route_count": len(routes),
                "active_route_count": active_route_count,
                "source_verified_route_count": source_verified_route_count,
                "direct_gloss_route_count": direct_gloss_route_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
            }
        )
    )


if __name__ == "__main__":
    main()
