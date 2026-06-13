#!/usr/bin/env python3
"""Seed human shadow readings for BENNA/formula and NAESE/C68 slot books."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
REASONS = {
    "BENNA/formula family not yet converted to human shadow reading",
    "NAESE/C68 slot family needs slot shadow reading",
}


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


def classify(bookid: str, tags_json: str, evidence: dict[str, object]) -> dict[str, str]:
    ids = tag_ids(tags_json)
    c68_context = str(evidence.get("c68_context_class", ""))
    naese_core = str(evidence.get("naese_core", ""))
    has_benna = "BENNA_FORMULA_BRIDGE" in ids or bool(evidence.get("benna_bridge"))
    has_c86 = "C86_PAYLOAD_OPERATOR" in ids
    has_vn = "VNCTIIN_CONTEXT_FRAME" in ids
    has_tail = "TAILBETFTE_SUFFIX_FRAME" in ids

    if bookid == "5":
        return {
            "subfamily": "NAESE_BENNA_COMPOSITE_FRAME",
            "bridge_id": "B_NAESE_BENNA_COMPOSITE",
            "likely_speech_act": "NAESE/C68 slot-to-BENNA formula composite",
            "reading": "A composite slot-to-formula line: NAESE/C68 slot material flows into a BENNA formula body, with no lexical meaning assigned to either component.",
            "confidence": "STRUCTURAL_STRONG_COMPOSITE_FRAME",
        }
    if bookid == "9":
        return {
            "subfamily": "NAESE_BENNA_COMPOSITE_WITH_LTAST_TAIL",
            "bridge_id": "B_NAESE_BENNA_COMPOSITE",
            "likely_speech_act": "NAESE/C68 slot-to-BENNA formula composite with LTAST tail",
            "reading": "A strong composite line where the NAESE/C68 slot window feeds a BENNA formula/concordance body and continues into an LTAST boundary tail.",
            "confidence": "STRUCTURAL_STRONG_COMPOSITE_WITH_TAIL",
        }
    if has_benna and has_c86 and has_vn:
        detail = "with TAILBETFTE suffix" if has_tail else "without explicit TAILBETFTE suffix"
        return {
            "subfamily": "BENNA_C86_VNCTIIN_FORMULA_HANDOFF",
            "bridge_id": "B_BENNA_C86_VNCTIIN_FORMULA_HANDOFF",
            "likely_speech_act": f"BENNA formula body handing off to C86/VNCTIIN context ({detail})",
            "reading": f"A BENNA formula/concordance line that hands off into C86/VNCTIIN context, {detail}; read as formula-to-context routing, not prose.",
            "confidence": "STRUCTURAL_STRONG_FORMULA_HANDOFF",
        }
    if bookid == "69":
        return {
            "subfamily": "BENNA_LOCAL_CLEAN_H2_CONTROL",
            "bridge_id": "B_BENNA_FORMULA_BODY",
            "likely_speech_act": "local clean BENNA/H2 formula control without contig edge",
            "reading": "A clean local BENNA formula-control line with stable H2/VNALL-style support, but no contig edge; use as local formula evidence only.",
            "confidence": "STRUCTURAL_LOCAL_CONTROL_NO_EDGE",
        }
    if has_benna:
        if bool(evidence.get("benna_display_variant")):
            return {
                "subfamily": "BENNA_FORMULA_COMPOSITE_VARIANT",
                "bridge_id": "B_BENNA_FORMULA_BODY",
                "likely_speech_act": "BENNA formula composite variant",
                "reading": "A BENNA formula-body variant with enough local support for shadow reading, but still no literal formula translation.",
                "confidence": "STRUCTURAL_FORMULA_VARIANT",
            }
        return {
            "subfamily": "BENNA_FORMULA_BODY_WITH_LTAST_TAIL",
            "bridge_id": "B_BENNA_FORMULA_BODY",
            "likely_speech_act": "BENNA formula/concordance body with LTAST boundary tail",
            "reading": "A BENNA formula/concordance body with an LTAST boundary tail; useful as repeated formula structure, not as English prose.",
            "confidence": "STRUCTURAL_FORMULA_BODY_NO_GLOSS",
        }
    if "QUARANTINED" in naese_core:
        return {
            "subfamily": "NAESE_WEAK_HYBRID_AUDIT",
            "bridge_id": "B_NAESE_WEAK_HYBRID_AUDIT",
            "likely_speech_act": "weak or hybrid NAESE/C68 slot audit line",
            "reading": "A weak/hybrid NAESE-adjacent line that must remain audit-only until a stronger boundary or branch control appears.",
            "confidence": "STRUCTURAL_WEAK_AUDIT",
        }
    if "VARIANT:NAESE_VARIANT" in naese_core or "VARIANT" in c68_context:
        return {
            "subfamily": "NAESE_VARIANT_WINDOW",
            "bridge_id": "B_NAESE_VARIANT_WINDOW",
            "likely_speech_act": "NAESE/C68 controlled variant slot window",
            "reading": "A controlled NAESE/C68 variant-window line, structurally related to the canonical slot but not strong enough for a clean slot reading.",
            "confidence": "STRUCTURAL_SLOT_VARIANT",
        }
    if "ORDERED_CORE:CANONICAL_SLOT" in naese_core or c68_context == "CANONICAL_NAESE_FATCT_SLOT":
        return {
            "subfamily": "NAESE_CANONICAL_SLOT",
            "bridge_id": "B_NAESE_CANONICAL_SLOT",
            "likely_speech_act": "canonical NAESE/C68/FATCT slot classifier",
            "reading": "A canonical NAESE/C68/FATCT slot-classifier line, usable as a local slot witness but not a translated phrase.",
            "confidence": "STRUCTURAL_SLOT_CLASSIFIER",
        }
    return {
        "subfamily": "SLOT_FORMULA_UNCLASSIFIED",
        "bridge_id": "B_NAESE_WEAK_HYBRID_AUDIT",
        "likely_speech_act": "unclassified slot/formula line",
        "reading": "An unclassified slot/formula-family line requiring manual split before stronger human reading.",
        "confidence": "STRUCTURAL_AUDIT_ONLY",
    }


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_slot_formula_shadow_v1_runs (
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

        CREATE TABLE IF NOT EXISTS human_slot_formula_shadow_v1_items (
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


def table_map(conn: sqlite3.Connection, sql: str, params: tuple[object, ...], key: str) -> dict[str, dict[str, object]]:
    return {str(row[key]): dict(row) for row in conn.execute(sql, params).fetchall()}


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    bridge_run_id = max_id(conn, "human_slot_formula_bridge_v1_items")
    source_audit_run_id = max_id(conn, "human_translation_completion_audit_v3_missing_books")
    bridges = {
        row["bridge_id"]: dict(row)
        for row in conn.execute(
            "SELECT * FROM human_slot_formula_bridge_v1_items WHERE run_id=?",
            (bridge_run_id,),
        ).fetchall()
    }
    targets = [
        str(row["bookid"])
        for row in conn.execute(
            """
            SELECT bookid
            FROM human_translation_completion_audit_v3_missing_books
            WHERE run_id=?
              AND reason_missing IN (?, ?)
            ORDER BY CAST(bookid AS INTEGER)
            """,
            (source_audit_run_id, *sorted(REASONS)),
        ).fetchall()
    ]
    if not targets:
        raise RuntimeError("no BENNA/NAESE targets found in latest completion audit v3")

    placeholders = ",".join("?" for _ in targets)
    benna = table_map(
        conn,
        f"""
        SELECT * FROM benna_formula_bridge_gate_items
        WHERE run_id=(SELECT max(run_id) FROM benna_formula_bridge_gate_items)
          AND bookid IN ({placeholders})
        """,
        tuple(targets),
        "bookid",
    )
    c68 = table_map(
        conn,
        f"""
        SELECT * FROM c68_fatct_slot_items
        WHERE run_id=(SELECT max(run_id) FROM c68_fatct_slot_items)
          AND bookid IN ({placeholders})
        """,
        tuple(targets),
        "bookid",
    )
    naese_core = {
        str(row["item_id"]): dict(row)
        for row in conn.execute(
            f"""
            SELECT * FROM naese_slot_core_v1_items
            WHERE run_id=(SELECT max(run_id) FROM naese_slot_core_v1_items)
              AND item_type='book'
              AND item_id IN ({placeholders})
            """,
            tuple(targets),
        ).fetchall()
    }
    naese_benna = table_map(
        conn,
        f"""
        SELECT * FROM naese_benna_composite_probe_v1_items
        WHERE run_id=(SELECT max(run_id) FROM naese_benna_composite_probe_v1_items)
          AND bookid IN ({placeholders})
        """,
        tuple(targets),
        "bookid",
    )
    benna_display = table_map(
        conn,
        f"""
        SELECT * FROM benna_display_variant_reassessment_v1_items
        WHERE run_id=(SELECT max(run_id) FROM benna_display_variant_reassessment_v1_items)
          AND bookid IN ({placeholders})
        """,
        tuple(targets),
        "bookid",
    )
    benna_69 = {
        str(row["item_id"]): dict(row)
        for row in conn.execute(
            "SELECT * FROM benna_69_edge_resolution_v1_items WHERE run_id=(SELECT max(run_id) FROM benna_69_edge_resolution_v1_items)"
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
        core = naese_core.get(bookid)
        evidence = {
            "benna_bridge": benna.get(bookid, {}),
            "benna_display_variant": benna_display.get(bookid, {}),
            "benna_69_edge": benna_69.get(bookid, {}),
            "c68_slot": c68.get(bookid, {}),
            "c68_context_class": c68.get(bookid, {}).get("context_class", ""),
            "naese_core": f"{core['status']}:{core['role_label']}" if core else "",
            "naese_core_row": core or {},
            "naese_benna_composite": naese_benna.get(bookid, {}),
        }
        cls = classify(bookid, str(row["functional_tags_json"]), evidence)
        bridge = bridges[cls["bridge_id"]]
        blocked_claims = [
            "No lexical gloss is promoted for BENNA, NAESE, C68, C86, VNCTIIN, LTAST, or related formula/slot components.",
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
                    **evidence,
                    "functional_tags_json": row["functional_tags_json"],
                    "honest_text": row["honest_text"],
                    "symbol_text": row["symbol_text"],
                    "token_text": row["token_text"],
                },
            }
        )

    if len(prepared) != len(targets):
        found = {item["bookid"] for item in prepared}
        missing = [target for target in targets if target not in found]
        raise RuntimeError(f"missing prepared slot/formula targets: {missing}")

    subfamilies = sorted({item["subfamily"] for item in prepared})
    cur = conn.execute(
        """
        INSERT INTO human_slot_formula_shadow_v1_runs
        (created_at, decision, bridge_run_id, source_audit_run_id,
         item_count, subfamily_count, canonical_promotion_count, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            now(),
            "HUMAN_SLOT_FORMULA_SHADOW_READY_NOT_PROMOTED",
            bridge_run_id,
            source_audit_run_id,
            len(prepared),
            len(subfamilies),
            0,
            json.dumps({"subfamilies": subfamilies, "source": "completion_audit_v3_missing_benna_naese"}, ensure_ascii=False, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)
    for item in prepared:
        bridge = item["bridge"]
        conn.execute(
            """
            INSERT INTO human_slot_formula_shadow_v1_items
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
                "decision": "HUMAN_SLOT_FORMULA_SHADOW_READY_NOT_PROMOTED",
                "item_count": len(prepared),
                "subfamily_count": len(subfamilies),
                "canonical_promotion_count": 0,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
