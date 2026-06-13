#!/usr/bin/env python3
"""Q12 probe: Bonelord Tome as an in-game 3478/486486 co-location anchor."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

SOURCE_EVIDENCE = [
    {
        "source_id": "TIBIA_FANDOM_BONELORD_TOME",
        "source_url": "https://tibia.fandom.com/wiki/Bonelord_Tome",
        "source_class": "secondary_wiki_item_page",
        "claim": "Bonelord Tome item sounds include the Knightmare 3478 phrase and a 486486 answer/attention line.",
        "risk": "secondary wiki extraction; verify in client or official item data before any stronger promotion",
    },
    {
        "source_id": "TIBIAWIKI_BR_BONELORD_TOME",
        "source_url": "https://www.tibiawiki.com.br/wiki/Bonelord_Tome",
        "source_class": "secondary_wiki_item_page",
        "claim": "Portuguese TibiaWiki page lists the same sounds and marks the item as an official TibiaSecrets fansite item.",
        "risk": "secondary wiki extraction; confirms item context but not a translation key",
    },
]

ANCHORS = [
    {
        "anchor_id": "BONELORD_TOME_3478_PHRASE",
        "exact_sequence": "3478 67 90871 97664 3466 0 345",
        "anchor_role": "repeated in-game/fansite item phrase",
        "allowed_inference": "Use as a phrase-level 3478 holdout linked to Bonelord/TibiaSecrets context.",
        "blocked_inference": "Do not split into component gloss for 3478, 67, 90871, 97664, 3466, 0, or 345.",
    },
    {
        "anchor_id": "BONELORD_TOME_486486_ANSWERS",
        "exact_sequence": "486486",
        "anchor_role": "proper-name/answer-oracle lore constraint",
        "allowed_inference": "Strengthens 486486 as an entity/formula/knowledge anchor already present in Wrinkled Bonelord lore.",
        "blocked_inference": "Do not use 486486 as a general book decoder or lexical value.",
    },
    {
        "anchor_id": "BONELORD_TOME_OCULI_LINE",
        "exact_sequence": "Oculi plus vident, quam oculus.",
        "anchor_role": "eye/vision lore parallel",
        "allowed_inference": "Use as Bonelord multi-eye/vision thematic support only.",
        "blocked_inference": "Do not map the Latin line to any 469 token or row0 symbol.",
    },
]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q12_bonelord_tome_3478_486486_anchor_probe_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            source_count INTEGER NOT NULL,
            exact_anchor_count INTEGER NOT NULL,
            colocation_anchor_count INTEGER NOT NULL,
            prior_486486_anchor_count INTEGER NOT NULL,
            q8_transition_control_count INTEGER NOT NULL,
            q9_no_component_gloss_control_count INTEGER NOT NULL,
            promoted_plaintext_gloss_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q12_bonelord_tome_3478_486486_anchor_probe_v1_items (
            run_id INTEGER NOT NULL,
            item_id TEXT NOT NULL,
            item_type TEXT NOT NULL,
            source_table TEXT NOT NULL,
            source_key TEXT NOT NULL,
            status TEXT NOT NULL,
            role_label TEXT NOT NULL,
            support_class TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, item_id)
        );
        """
    )


def latest_id(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT max(run_id) FROM {table}").fetchone()
    if row is None or row[0] is None:
        raise RuntimeError(f"missing required run: {table}")
    return int(row[0])


def one(conn: sqlite3.Connection, sql: str, params: tuple[object, ...] = ()) -> sqlite3.Row | None:
    return conn.execute(sql, params).fetchone()


def add_item(
    out: list[dict[str, object]],
    item_id: str,
    item_type: str,
    source_table: str,
    source_key: str,
    status: str,
    role_label: str,
    support_class: str,
    evidence: object,
) -> None:
    out.append(
        {
            "item_id": item_id,
            "item_type": item_type,
            "source_table": source_table,
            "source_key": source_key,
            "status": status,
            "role_label": role_label,
            "support_class": support_class,
            "evidence_json": j(evidence),
        }
    )


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    ingame_run = latest_id(conn, "human_ingame_anchor_corpus_v1_items")
    q8_run = latest_id(conn, "human_q8_book6_7_phase_path_3478_transition_probe_v1_runs")
    q9_run = latest_id(conn, "human_q9_book6_7_heldout_support_audit_v1_runs")

    q8 = one(
        conn,
        "SELECT * FROM human_q8_book6_7_phase_path_3478_transition_probe_v1_runs WHERE run_id=?",
        (q8_run,),
    )
    q9 = one(
        conn,
        "SELECT * FROM human_q9_book6_7_heldout_support_audit_v1_runs WHERE run_id=?",
        (q9_run,),
    )
    awb_486486 = one(
        conn,
        """
        SELECT *
        FROM human_ingame_anchor_corpus_v1_items
        WHERE run_id=? AND anchor_id='AWB_SELF_NAME_486486'
        """,
        (ingame_run,),
    )

    items: list[dict[str, object]] = []

    for source in SOURCE_EVIDENCE:
        add_item(
            items,
            f"source:{source['source_id']}",
            "source_evidence",
            "web_external_source",
            str(source["source_url"]),
            "SOURCE_ATTESTS_BONELORD_TOME_CONTEXT",
            str(source["claim"]),
            "SUPPORT_SOURCE_CONTEXT_SECONDARY_VERIFY_BEFORE_PROMOTION",
            source,
        )

    for anchor in ANCHORS:
        support_class = (
            "SUPPORT_3478_PHRASE_COLOCATED_WITH_486486_NO_COMPONENT_GLOSS"
            if anchor["anchor_id"] == "BONELORD_TOME_3478_PHRASE"
            else "SUPPORT_486486_ANSWER_ORACLE_ANCHOR_NO_BOOK_GLOSS"
            if anchor["anchor_id"] == "BONELORD_TOME_486486_ANSWERS"
            else "CONTROL_THEMATIC_EYE_LORE_NO_TOKEN_MAPPING"
        )
        add_item(
            items,
            f"anchor:{anchor['anchor_id']}",
            "tome_anchor",
            "web_external_source",
            "Bonelord Tome sounds",
            "BONELORD_TOME_ANCHOR_ACCEPTED_AS_LORE_CONSTRAINT_NO_GLOSS",
            str(anchor["anchor_role"]),
            support_class,
            anchor,
        )

    add_item(
        items,
        "prior:awb-486486",
        "prior_ingame_anchor",
        "human_ingame_anchor_corpus_v1_items",
        f"run={ingame_run}:AWB_SELF_NAME_486486",
        str(awb_486486["promotion_status"]) if awb_486486 else "MISSING_AWB_486486_ANCHOR",
        "Existing Wrinkled Bonelord 486486 anchor remains scoped and no-gloss",
        "SUPPORT_PRIOR_486486_SCOPED_LORE_ANCHOR",
        dict(awb_486486) if awb_486486 else {"missing": True},
    )

    add_item(
        items,
        "control:q8-3478-transition",
        "prior_transition_control",
        "human_q8_book6_7_phase_path_3478_transition_probe_v1_runs",
        f"run={q8_run}",
        str(q8["decision"]) if q8 else "MISSING_Q8",
        "Q8 already keeps 3478 as transition-control, not payload",
        "CONTROL_Q8_3478_NO_PAYLOAD_GLOSS",
        dict(q8) if q8 else {"missing": True},
    )
    add_item(
        items,
        "control:q9-no-heldout-component-gloss",
        "prior_no_gloss_control",
        "human_q9_book6_7_heldout_support_audit_v1_runs",
        f"run={q9_run}",
        str(q9["decision"]) if q9 else "MISSING_Q9",
        "Q9 blocks component gloss or Book6/7 prose from current held-out tables",
        "CONTROL_Q9_NO_COMPONENT_GLOSS",
        dict(q9) if q9 else {"missing": True},
    )

    source_count = len(SOURCE_EVIDENCE)
    exact_anchor_count = len(ANCHORS)
    colocation_anchor_count = 1
    prior_486486_anchor_count = int(awb_486486 is not None)
    q8_transition_control_count = int(q8 is not None and int(q8["promoted_plaintext_gloss_count"]) == 0)
    q9_no_component_gloss_control_count = int(q9 is not None and int(q9["promoted_plaintext_gloss_count"]) == 0)
    promoted_plaintext_gloss_count = 0

    decision = (
        "Q12_BONELORD_TOME_ADDS_INGAME_3478_486486_COLOCATION_ANCHOR_NO_COMPONENT_GLOSS"
        if source_count >= 2
        and exact_anchor_count >= 3
        and colocation_anchor_count == 1
        and prior_486486_anchor_count == 1
        and q8_transition_control_count == 1
        and q9_no_component_gloss_control_count == 1
        and promoted_plaintext_gloss_count == 0
        else "Q12_BONELORD_TOME_ANCHOR_REQUIRES_MANUAL_REVIEW"
    )

    payload = {
        "question": "Does Bonelord Tome add a useful in-game anchor for the 3478/486486 route?",
        "answer": (
            "Yes as a lore/phrase co-location anchor only. The item context co-locates the Knightmare 3478 phrase with 486486 as an answer/attention anchor, "
            "and reinforces the Bonelord/TibiaSecrets knowledge framing. It does not translate 3478, Book6/7, or any component."
        ),
        "allowed_reading": "Use Bonelord Tome to prioritize 3478/486486 phrase-level tests and source verification.",
        "blocked_reading": "Do not derive component gloss, sentence prose, or a book decoder from the item sounds.",
        "next_probe": (
            "Compare external phrases containing 3478 and 486486 against row0 phrase-level projections; verify Bonelord Tome sounds in-client or via official item data before stronger claims."
        ),
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q12_bonelord_tome_3478_486486_anchor_probe_v1_runs (
                created_at, decision, source_count, exact_anchor_count,
                colocation_anchor_count, prior_486486_anchor_count,
                q8_transition_control_count, q9_no_component_gloss_control_count,
                promoted_plaintext_gloss_count, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                source_count,
                exact_anchor_count,
                colocation_anchor_count,
                prior_486486_anchor_count,
                q8_transition_control_count,
                q9_no_component_gloss_control_count,
                promoted_plaintext_gloss_count,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q12_bonelord_tome_3478_486486_anchor_probe_v1_items (
                run_id, item_id, item_type, source_table, source_key, status,
                role_label, support_class, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    str(row["item_id"]),
                    str(row["item_type"]),
                    str(row["source_table"]),
                    str(row["source_key"]),
                    str(row["status"]),
                    str(row["role_label"]),
                    str(row["support_class"]),
                    str(row["evidence_json"]),
                )
                for row in items
            ],
        )

    print(
        j(
            {
                "run_id": run_id,
                "decision": decision,
                "source_count": source_count,
                "exact_anchor_count": exact_anchor_count,
                "colocation_anchor_count": colocation_anchor_count,
                "prior_486486_anchor_count": prior_486486_anchor_count,
                "q8_transition_control_count": q8_transition_control_count,
                "q9_no_component_gloss_control_count": q9_no_component_gloss_control_count,
                "promoted_plaintext_gloss_count": promoted_plaintext_gloss_count,
            }
        )
    )


if __name__ == "__main__":
    main()
