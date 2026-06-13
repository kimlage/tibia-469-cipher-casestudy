#!/usr/bin/env python3
"""Seed human shadow readings for missing R20/R02 phase-family books."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_json(value: str | None, fallback):
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def tag_ids(tags_json: str) -> set[str]:
    tags = parse_json(tags_json, [])
    ids: set[str] = set()
    for tag in tags:
        if isinstance(tag, dict):
            ids.add(str(tag.get("tag_id", "")))
    return ids


def has_seq(tokens: list[str], seq: list[str]) -> bool:
    size = len(seq)
    return any(tokens[index : index + size] == seq for index in range(0, max(0, len(tokens) - size + 1)))


def token_facts(tokens: list[str], tags_json: str, naese_status: str) -> dict[str, object]:
    ids = tag_ids(tags_json)
    facts = {
        "has_r02_bridge": has_seq(tokens, ["R02", "V", "E", "I", "I", "V", "N", "T", "B"])
        or has_seq(tokens, ["T", "R02", "V", "E", "I", "I", "V", "N", "T", "B"]),
        "has_r20_phase": has_seq(tokens, ["V", "A", "E", "T", "R20", "F", "E", "V", "A", "S", "T"]),
        "has_r20_vtlr": has_seq(tokens, ["V", "T", "L", "R20", "N", "E", "F", "I", "E"]),
        "has_r02_livrn": has_seq(tokens, ["L", "I", "V", "R02", "N"]),
        "has_r20_livrn": has_seq(tokens, ["L", "I", "V", "R20", "N"]),
        "has_zero_ltast_boundary": has_seq(tokens, ["*00", "L", "T", "A", "S", "T", "T", "N", "V", "V", "N", "N", "F", "I", "E"]),
        "has_vinvin_branch": "VINVIN_BRANCH_SUBFUNCTION" in ids or "VINVIN_NEGATIVE_CONTROL" in ids,
        "has_naese_slot": "NAESE_C68_FATCT_LOCAL_SLOT" in ids,
        "naese_status": naese_status,
    }
    return facts


def classify(bookid: str, facts: dict[str, object]) -> dict[str, str]:
    naese_status = str(facts["naese_status"])
    has_r02_bridge = bool(facts["has_r02_bridge"])
    has_r20_phase = bool(facts["has_r20_phase"])
    has_vinvin_branch = bool(facts["has_vinvin_branch"])
    has_r20_vtlr = bool(facts["has_r20_vtlr"])
    has_r02_livrn = bool(facts["has_r02_livrn"])
    has_r20_livrn = bool(facts["has_r20_livrn"])
    has_zero_ltast_boundary = bool(facts["has_zero_ltast_boundary"])

    if bookid == "14" or (has_r02_bridge and has_zero_ltast_boundary):
        return {
            "subfamily": "R02_LTAST_BOUNDARY_AUDIT",
            "bridge_id": "B_R02_LTAST_BOUNDARY_AUDIT",
            "likely_speech_act": "R02-prefaced boundary/audit fragment with zero exits toward VNA/LTAST material",
            "reading": "A weak R02 boundary-audit fragment that touches VNA/LTAST-like boundary material; hold as structural context, not as translated prose.",
            "confidence": "STRUCTURAL_WEAK_BOUNDARY_AUDIT",
        }
    if has_r02_bridge and "ORDERED_CORE:R02_SLOT_BRIDGE" in naese_status:
        return {
            "subfamily": "R02_NAESE_SLOT_BRIDGE",
            "bridge_id": "B_R02_NAESE_SLOT_BRIDGE",
            "likely_speech_act": "R02 phase bridge into NAESE/C68 slot mechanics",
            "reading": "A strong R02 phase-to-slot bridge line: it carries the R02/TRVEIIVNTBB bridge into the NAESE/C68 slot frame without giving R02 or NAESE a lexical gloss.",
            "confidence": "STRUCTURAL_STRONG_PHASE_SLOT_BRIDGE",
        }
    if has_r02_bridge and (has_r20_phase or "CONTEXT_CONNECTOR" in naese_status):
        return {
            "subfamily": "R02_R20_CONTEXT_CONNECTOR",
            "bridge_id": "B_R02_R20_CONTEXT_CONNECTOR",
            "likely_speech_act": "R02/R20 context connector adjacent to slot mechanics",
            "reading": "A context-connector line joining R20 phase-block material to the R02 bridge corridor; related to the slot bridge but not itself a clean slot proof.",
            "confidence": "STRUCTURAL_MODERATE_CONTEXT_CONNECTOR",
        }
    if has_vinvin_branch and has_r20_phase:
        return {
            "subfamily": "VINVIN_R20_PHASE_ENDPOINT",
            "bridge_id": "B_R20_PHASE_BLOCK",
            "likely_speech_act": "VINVIN-covered R20 branch ending in an R20 phase block",
            "reading": "A VINVIN-covered branch line that reaches an R20 phase-block endpoint; read as branch plus phase endpoint, not as independent R20 prose.",
            "confidence": "STRUCTURAL_MODERATE_BRANCH_ENDPOINT",
        }
    if has_vinvin_branch or has_r20_vtlr:
        return {
            "subfamily": "VINVIN_R20_COVERED_BRANCH",
            "bridge_id": "B_VINVIN_R20_COVERED_BRANCH",
            "likely_speech_act": "VINVIN-covered R20/VTLR branch context",
            "reading": "A covered branch/context line where the R20/VTLR frame is subordinated to VINVIN branch mechanics rather than acting as a standalone phrase.",
            "confidence": "STRUCTURAL_COVERED_BRANCH_CONTROL",
        }
    if has_r20_phase and has_r20_livrn:
        return {
            "subfamily": "R20_PHASE_WITH_LIVRN_MICRO",
            "bridge_id": "B_R20_PHASE_BLOCK",
            "likely_speech_act": "R20 phase block with LIVRN microcontext",
            "reading": "An R20 phase-block line with an attached LIVRN microcontext; the phase block is visible, but the microcontext remains audit-only.",
            "confidence": "STRUCTURAL_PHASE_WITH_AUDIT_MICRO",
        }
    if has_r20_phase:
        return {
            "subfamily": "R20_PHASE_BLOCK",
            "bridge_id": "B_R20_PHASE_BLOCK",
            "likely_speech_act": "local R20 phase block",
            "reading": "A local R20 phase-block line; use it as phase/control material and do not promote R20 as a word.",
            "confidence": "STRUCTURAL_PHASE_BLOCK_NO_GLOSS",
        }
    if has_r02_livrn or has_r20_livrn:
        return {
            "subfamily": "R_LIVRN_MICRO_AUDIT",
            "bridge_id": "B_R_LIVRN_MICRO_AUDIT",
            "likely_speech_act": "R02/R20 LIVRN microcontext audit line",
            "reading": "A low-support LIVRN microcontext line; useful as an audit control only, with no phrase-level translation.",
            "confidence": "STRUCTURAL_AUDIT_MICRO_ONLY",
        }
    return {
        "subfamily": "R20_R02_UNCLASSIFIED",
        "bridge_id": "B_R20_PHASE_BLOCK",
        "likely_speech_act": "unclassified R20/R02-family line",
        "reading": "An unclassified R20/R02-family line requiring manual split before stronger human reading.",
        "confidence": "STRUCTURAL_AUDIT_ONLY",
    }


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_r20_r02_phase_shadow_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            bridge_run_id INTEGER NOT NULL,
            source_audit_run_id INTEGER NOT NULL,
            item_count INTEGER NOT NULL,
            subfamily_count INTEGER NOT NULL,
            canonical_promotion_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_r20_r02_phase_shadow_v1_items (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            subfamily TEXT NOT NULL,
            likely_speech_act TEXT NOT NULL,
            plausible_human_reading TEXT NOT NULL,
            confidence_tier TEXT NOT NULL,
            source_bridge_id TEXT NOT NULL,
            anchor_ids_json TEXT NOT NULL,
            support_level TEXT NOT NULL,
            blocked_claims_json TEXT NOT NULL,
            blocked_overreach TEXT NOT NULL,
            falsifier TEXT NOT NULL,
            next_probe TEXT NOT NULL,
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

    bridge_run_id = max_id(conn, "human_r20_r02_phase_bridge_v1_items")
    source_audit_run_id = max_id(conn, "human_translation_completion_audit_v2_missing_books")
    bridges = {
        row["bridge_id"]: dict(row)
        for row in conn.execute(
            "SELECT * FROM human_r20_r02_phase_bridge_v1_items WHERE run_id=?",
            (bridge_run_id,),
        ).fetchall()
    }
    targets = [
        str(row["bookid"])
        for row in conn.execute(
            """
            SELECT bookid
            FROM human_translation_completion_audit_v2_missing_books
            WHERE run_id=?
              AND reason_missing='R20/R02 phase family needs bridge/phase shadow reading'
            ORDER BY CAST(bookid AS INTEGER)
            """,
            (source_audit_run_id,),
        ).fetchall()
    ]
    if not targets:
        raise RuntimeError("no R20/R02 targets found in latest completion audit v2")

    placeholders = ",".join("?" for _ in targets)
    naese_status = {
        str(row["item_id"]): f"{row['status']}:{row['role_label']}"
        for row in conn.execute(
            f"""
            SELECT item_id, status, role_label
            FROM naese_slot_core_v1_items
            WHERE run_id=(SELECT max(run_id) FROM naese_slot_core_v1_items)
              AND item_type='book'
              AND item_id IN ({placeholders})
            """,
            tuple(targets),
        ).fetchall()
    }
    phase_gate = {
        str(row["bookid"]): dict(row)
        for row in conn.execute(
            f"""
            SELECT *
            FROM r20_r02_naese_phase_gate_v1_items
            WHERE run_id=(SELECT max(run_id) FROM r20_r02_naese_phase_gate_v1_items)
              AND bookid IN ({placeholders})
            """,
            tuple(targets),
        ).fetchall()
    }
    books = conn.execute(
        f"""
        SELECT b.bookid, b.functional_tags_json, b.honest_text,
               t.symbol_text, t.token_text, t.tokens_json
        FROM final_honest_reading_v19_books b
        JOIN row0_variant_book_tokens t
          ON t.bookid=b.bookid
         AND t.run_id=(SELECT max(run_id) FROM row0_variant_book_tokens)
        WHERE b.run_id=(SELECT max(run_id) FROM final_honest_reading_v19_books)
          AND b.bookid IN ({placeholders})
        ORDER BY CAST(b.bookid AS INTEGER)
        """,
        tuple(targets),
    ).fetchall()

    prepared = []
    for row in books:
        bookid = str(row["bookid"])
        tokens = parse_json(str(row["tokens_json"]), [])
        facts = token_facts(tokens, str(row["functional_tags_json"]), naese_status.get(bookid, "NO_NAESE_SLOT_RECORD:"))
        cls = classify(bookid, facts)
        bridge = bridges[cls["bridge_id"]]
        blocked_claims = [
            "No lexical gloss is promoted for R20, R02, NAESE, C68, VINVIN, LIVRN, or LTAST components.",
            bridge["blocked_overreach"],
        ]
        prepared.append(
            {
                "bookid": bookid,
                "subfamily": cls["subfamily"],
                "likely_speech_act": cls["likely_speech_act"],
                "reading": cls["reading"],
                "confidence": cls["confidence"],
                "bridge": bridge,
                "blocked_claims": blocked_claims,
                "falsifier": f"If Book {bookid} fails its {cls['subfamily']} controls or collapses into a stronger neighboring family, revise the reading.",
                "next_probe": bridge["next_probe"],
                "evidence": {
                    "facts": facts,
                    "functional_tags_json": row["functional_tags_json"],
                    "honest_text": row["honest_text"],
                    "phase_gate": phase_gate.get(bookid, {}),
                    "symbol_text": row["symbol_text"],
                    "token_text": row["token_text"],
                },
            }
        )

    if len(prepared) != len(targets):
        found = {item["bookid"] for item in prepared}
        missing = [target for target in targets if target not in found]
        raise RuntimeError(f"missing prepared R20/R02 targets: {missing}")

    subfamilies = sorted({item["subfamily"] for item in prepared})
    cur = conn.execute(
        """
        INSERT INTO human_r20_r02_phase_shadow_v1_runs
        (created_at, decision, bridge_run_id, source_audit_run_id,
         item_count, subfamily_count, canonical_promotion_count, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            now(),
            "HUMAN_R20_R02_PHASE_SHADOW_READY_NOT_PROMOTED",
            bridge_run_id,
            source_audit_run_id,
            len(prepared),
            len(subfamilies),
            0,
            json.dumps({"subfamilies": subfamilies, "source": "completion_audit_v2_missing_r20_r02"}, ensure_ascii=False, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)
    for item in prepared:
        bridge = item["bridge"]
        conn.execute(
            """
            INSERT INTO human_r20_r02_phase_shadow_v1_items
            (run_id, bookid, subfamily, likely_speech_act,
             plausible_human_reading, confidence_tier, source_bridge_id,
             anchor_ids_json, support_level, blocked_claims_json,
             blocked_overreach, falsifier, next_probe, promotion_status,
             evidence_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                item["bookid"],
                item["subfamily"],
                item["likely_speech_act"],
                item["reading"],
                item["confidence"],
                bridge["bridge_id"],
                bridge["anchor_ids_json"],
                bridge["support_level"],
                json.dumps(item["blocked_claims"], ensure_ascii=False, sort_keys=True),
                bridge["blocked_overreach"],
                item["falsifier"],
                item["next_probe"],
                "NOT_PROMOTED",
                json.dumps(item["evidence"], ensure_ascii=False, sort_keys=True),
            ),
        )

    conn.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": "HUMAN_R20_R02_PHASE_SHADOW_READY_NOT_PROMOTED",
                "item_count": len(prepared),
                "subfamily_count": len(subfamilies),
                "canonical_promotion_count": 0,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
