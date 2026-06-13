#!/usr/bin/env python3
"""Q26: import exact Mathemagic transcript bridges as operator-only evidence."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

TRANSCRIPT_ITEMS = [
    {
        "item_id": "awb:language-mathemagic",
        "source_url": "https://tibia.fandom.com/wiki/A_Wrinkled_Bonelord/Transcripts",
        "source_type": "npc_transcript",
        "speaker": "A Wrinkled Bonelord",
        "trigger": "language",
        "status": "DIRECT_BONELORD_MATHEMAGIC_METHOD_LINK",
        "role_label": "Wrinkled Bonelord says the language heavily relies on mathemagic.",
        "support_class": "SUPPORT_METHOD_CONSTRAINT_OPERATOR_ONLY",
        "evidence": {
            "source_lines": "language response: beyond human comprehension, relies on mathemagic, requires fast numerical processing",
            "allowed_inference": "469 should be tested with numeric/operator machinery.",
            "blocked_inference": "Does not define plaintext or a direct dictionary.",
        },
    },
    {
        "item_id": "awb:minotaur-mages-truth",
        "source_url": "https://tibia.fandom.com/wiki/A_Wrinkled_Bonelord/Transcripts",
        "source_type": "npc_transcript",
        "speaker": "A Wrinkled Bonelord",
        "trigger": "minotaurs",
        "status": "MINOTAUR_MAGE_TRUTH_BRIDGE_SOURCE",
        "role_label": "Wrinkled Bonelord says minotaur mages are close to the truth.",
        "support_class": "SUPPORT_BRIDGE_TO_MINTWALLIN_MATHEMAGICS",
        "evidence": {
            "source_lines": "minotaurs response: their mages are close to truth, closer than they know",
            "allowed_inference": "Mintwallin/minotaur mathemagics is a legitimate in-game bridge candidate.",
            "blocked_inference": "Does not say A Prisoner knows 469 or translates books.",
        },
    },
    {
        "item_id": "a-prisoner:mathemagic-four-outputs",
        "source_url": "https://tibia.fandom.com/wiki/A_Prisoner/Transcripts",
        "source_type": "npc_transcript",
        "speaker": "A Prisoner",
        "trigger": "number/math/1+1",
        "status": "FOUR_MATHEMAGIC_OUTPUTS_ATTESTED",
        "role_label": "A Prisoner gives four possible Mathemagic outputs for 1+1.",
        "support_class": "SUPPORT_OPERATOR_KEY_SET",
        "evidence": {
            "outputs": ["49", "94", "13", "1"],
            "source_lines": "1+1 can equal 49, 94, 13, or 1 depending on mission random value",
            "allowed_inference": "Use 1/13/49/94 as operator/selector candidates.",
            "blocked_inference": "Do not use these numbers as lexical words.",
        },
    },
    {
        "item_id": "riddler:paradox-1-plus-1-gate",
        "source_url": "https://tibia.fandom.com/wiki/The_Paradox_Tower_Quest/Spoiler",
        "source_type": "quest_spoiler_transcript",
        "speaker": "Riddler",
        "trigger": "Seal of Madness",
        "status": "PARADOX_GATE_REQUIRES_MATHEMAGIC_NUMBER",
        "role_label": "Riddler asks 1+1, sends wrong answer through Hellgate, and later accepts A Prisoner's number.",
        "support_class": "SUPPORT_QUEST_OPERATOR_GATE",
        "evidence": {
            "source_lines": "Riddler asks what 1 plus 1 is; A Prisoner later provides the unique number called the secret of mathemagics",
            "allowed_inference": "The quest makes Mathemagic an operational gate, not just flavor text.",
            "blocked_inference": "The gate does not translate 469 books.",
        },
    },
    {
        "item_id": "wyrdin:madman-bonelord-language",
        "source_url": "https://www.tibiawiki.com.br/wiki/Wyrdin",
        "source_type": "npc_spontaneous_speech",
        "speaker": "Wyrdin",
        "trigger": "spontaneous",
        "status": "BONELORD_LANGUAGE_MADMAN_CONTEXT_ATTESTED",
        "role_label": "Wyrdin asks whether bonelord language could be the invention of some madman.",
        "support_class": "SUPPORT_MAD_MAGE_CONTEXT_ONLY",
        "evidence": {
            "source_lines": "spontaneous line links bonelord language to possible madman invention",
            "allowed_inference": "Use as context for testing the Mad Mage/A Prisoner bridge.",
            "blocked_inference": "Wyrdin gives no numeric sequence and no translation.",
        },
    },
]

BRIDGE_EDGES = [
    {
        "edge_id": "awb-language-to-operator-set",
        "source_item_id": "awb:language-mathemagic",
        "target_item_id": "a-prisoner:mathemagic-four-outputs",
        "status": "LIVE_OPERATOR_BRIDGE",
        "support_class": "METHOD_TO_OPERATOR_SET",
        "interpretation": "Bonelord method clue justifies testing 1/13/49/94 as operators.",
        "rejection_rule": "Reject if operator tests do not improve held-out structural prediction.",
    },
    {
        "edge_id": "awb-minotaur-to-prisoner",
        "source_item_id": "awb:minotaur-mages-truth",
        "target_item_id": "a-prisoner:mathemagic-four-outputs",
        "status": "LIVE_CONTEXT_BRIDGE",
        "support_class": "MINOTAUR_MAGE_TO_MINTWALLIN",
        "interpretation": "Wrinkled Bonelord's minotaur-mage remark points toward Mintwallin mathemagics as a plausible bridge.",
        "rejection_rule": "Reject if the bridge stays thematic and does not predict any structural relation.",
    },
    {
        "edge_id": "riddler-to-prisoner-quest-gate",
        "source_item_id": "riddler:paradox-1-plus-1-gate",
        "target_item_id": "a-prisoner:mathemagic-four-outputs",
        "status": "QUEST_GATE_CONFIRMED",
        "support_class": "QUEST_MECHANIC_OPERATOR_LINK",
        "interpretation": "The Paradox Tower quest mechanics bind Riddler's 1+1 question to A Prisoner's output.",
        "rejection_rule": "Do not extend from quest mechanic to plaintext without a separate 469 bridge.",
    },
    {
        "edge_id": "wyrdin-madman-to-prisoner",
        "source_item_id": "wyrdin:madman-bonelord-language",
        "target_item_id": "a-prisoner:mathemagic-four-outputs",
        "status": "CONTEXT_ONLY_BRIDGE",
        "support_class": "MADMAN_CONTEXT",
        "interpretation": "Wyrdin makes the madman hypothesis source-backed, but not solved.",
        "rejection_rule": "Reject as translation evidence unless exact sequences or predictive operator behavior appear.",
    },
]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q26_mathemagic_transcript_bridge_import_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q22_run_id INTEGER NOT NULL,
            transcript_item_count INTEGER NOT NULL,
            bridge_edge_count INTEGER NOT NULL,
            direct_bonelord_mathemagic_link_count INTEGER NOT NULL,
            minotaur_bridge_source_count INTEGER NOT NULL,
            mathemagic_operator_output_count INTEGER NOT NULL,
            direct_plaintext_gloss_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q26_mathemagic_transcript_bridge_import_v1_items (
            run_id INTEGER NOT NULL,
            item_id TEXT NOT NULL,
            source_url TEXT NOT NULL,
            source_type TEXT NOT NULL,
            speaker TEXT NOT NULL,
            trigger TEXT NOT NULL,
            status TEXT NOT NULL,
            role_label TEXT NOT NULL,
            support_class TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, item_id)
        );

        CREATE TABLE IF NOT EXISTS human_q26_mathemagic_transcript_bridge_import_v1_edges (
            run_id INTEGER NOT NULL,
            edge_id TEXT NOT NULL,
            source_item_id TEXT NOT NULL,
            target_item_id TEXT NOT NULL,
            status TEXT NOT NULL,
            support_class TEXT NOT NULL,
            interpretation TEXT NOT NULL,
            rejection_rule TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, edge_id)
        );
        """
    )


def latest_run_id(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT max(run_id) FROM {table}").fetchone()
    if row is None or row[0] is None:
        raise RuntimeError(f"missing required run: {table}")
    return int(row[0])


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q22_run_id = latest_run_id(conn, "human_q22_cross_quest_shadow_route_prioritization_v1_runs")
    direct_bonelord_mathemagic_link_count = sum(
        1 for item in TRANSCRIPT_ITEMS if item["status"] == "DIRECT_BONELORD_MATHEMAGIC_METHOD_LINK"
    )
    minotaur_bridge_source_count = sum(
        1 for item in TRANSCRIPT_ITEMS if "MINOTAUR" in item["status"] or "MINTWALLIN" in item["support_class"]
    )
    outputs = set()
    for item in TRANSCRIPT_ITEMS:
        outputs.update(item["evidence"].get("outputs", []))
    mathemagic_operator_output_count = len(outputs)
    direct_plaintext_gloss_count = 0
    canonical_promotion_allowed_count = 0

    decision = (
        "Q26_MATHEMAGIC_TRANSCRIPT_BRIDGE_IMPORTED_OPERATOR_ONLY_NO_GLOSS"
        if len(TRANSCRIPT_ITEMS) == 5
        and len(BRIDGE_EDGES) == 4
        and direct_bonelord_mathemagic_link_count >= 1
        and minotaur_bridge_source_count >= 1
        and outputs == {"1", "13", "49", "94"}
        and direct_plaintext_gloss_count == 0
        and canonical_promotion_allowed_count == 0
        else "Q26_MATHEMAGIC_TRANSCRIPT_BRIDGE_REQUIRES_MANUAL_REVIEW"
    )
    payload = {
        "question": "Can Mathemagic be used as a source-backed human translation route?",
        "answer": (
            "Yes, as operator/selector machinery only. The in-game transcripts support a bridge from 469 to mathemagic "
            "and from minotaur mages to Mintwallin/A Prisoner, but no source gives plaintext for books."
        ),
        "operator_outputs": sorted(outputs, key=lambda value: int(value)),
        "allowed_reading": "Use 1/13/49/94 as selectors/operators in held-out structural tests.",
        "blocked_reading": "Do not use Mathemagic as a dictionary or phrase translation.",
        "next_action": "Run selector tests only where 1/13/49/94 improve source-independent structure or contradiction reduction.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q26_mathemagic_transcript_bridge_import_v1_runs (
                created_at, decision, q22_run_id, transcript_item_count,
                bridge_edge_count, direct_bonelord_mathemagic_link_count,
                minotaur_bridge_source_count, mathemagic_operator_output_count,
                direct_plaintext_gloss_count, canonical_promotion_allowed_count,
                payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                q22_run_id,
                len(TRANSCRIPT_ITEMS),
                len(BRIDGE_EDGES),
                direct_bonelord_mathemagic_link_count,
                minotaur_bridge_source_count,
                mathemagic_operator_output_count,
                direct_plaintext_gloss_count,
                canonical_promotion_allowed_count,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q26_mathemagic_transcript_bridge_import_v1_items (
                run_id, item_id, source_url, source_type, speaker, trigger,
                status, role_label, support_class, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    str(item["item_id"]),
                    str(item["source_url"]),
                    str(item["source_type"]),
                    str(item["speaker"]),
                    str(item["trigger"]),
                    str(item["status"]),
                    str(item["role_label"]),
                    str(item["support_class"]),
                    j(item["evidence"]),
                )
                for item in TRANSCRIPT_ITEMS
            ],
        )
        conn.executemany(
            """
            INSERT INTO human_q26_mathemagic_transcript_bridge_import_v1_edges (
                run_id, edge_id, source_item_id, target_item_id, status,
                support_class, interpretation, rejection_rule, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    str(edge["edge_id"]),
                    str(edge["source_item_id"]),
                    str(edge["target_item_id"]),
                    str(edge["status"]),
                    str(edge["support_class"]),
                    str(edge["interpretation"]),
                    str(edge["rejection_rule"]),
                    j(edge),
                )
                for edge in BRIDGE_EDGES
            ],
        )

    print(
        j(
            {
                "run_id": run_id,
                "decision": decision,
                "q22_run_id": q22_run_id,
                "transcript_item_count": len(TRANSCRIPT_ITEMS),
                "bridge_edge_count": len(BRIDGE_EDGES),
                "direct_bonelord_mathemagic_link_count": direct_bonelord_mathemagic_link_count,
                "minotaur_bridge_source_count": minotaur_bridge_source_count,
                "mathemagic_operator_output_count": mathemagic_operator_output_count,
                "direct_plaintext_gloss_count": direct_plaintext_gloss_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
            }
        )
    )


if __name__ == "__main__":
    main()
