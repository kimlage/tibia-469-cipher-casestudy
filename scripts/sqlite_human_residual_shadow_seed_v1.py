#!/usr/bin/env python3
"""Seed human shadow readings for remaining residual books."""

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
        else:
            ids.add(str(tag))
    return ids


def classify(bookid: str, tags_json: str) -> dict[str, str]:
    ids = tag_ids(tags_json)
    if "469_MARKER_LANGUAGE_LABEL_OR_METAFORMULA_RESIDUAL_AUDIT_SAFE" in ids:
        return {
            "subfamily": "469_MARKER_METAFORMULA_RESIDUAL",
            "bridge_id": "B_RESIDUAL_469_METAFORMULA",
            "likely_speech_act": "469 marker/language-label or metaformula audit surface",
            "reading": "A special 469 marker or metaformula line that mixes several operator families; hold as a label/audit surface rather than using it as a cipher key.",
            "confidence": "SPECIAL_METAFORMULA_AUDIT",
        }
    if "UNIQUE_PREFIX_HEADER_FOR_SCRAMBLED_ASSEMBLY_AUDIT_SAFE" in ids:
        return {
            "subfamily": "UNIQUE_SCRAMBLED_HEADER_RESIDUAL",
            "bridge_id": "B_RESIDUAL_UNIQUE_HEADER",
            "likely_speech_act": "unique prefix/header audit line",
            "reading": "A unique prefix/header line for scrambled assembly audit; preserve it as an exceptional header-like surface, not a normal book sentence.",
            "confidence": "UNIQUE_HEADER_AUDIT",
        }
    if "BTII_NSBVN_ATFNAAST_DISPLAY_DRIFT" in ids:
        return {
            "subfamily": "DISPLAY_DRIFT_RESIDUAL",
            "bridge_id": "B_RESIDUAL_DISPLAY_DRIFT",
            "likely_speech_act": "BTII/NSBVN/ATFNAAST display-drift formula block",
            "reading": "A display-drift formula block with BTII/NSBVN/ATFNAAST material; useful as an audit witness for formula/display behavior, not as prose.",
            "confidence": "AUDIT_DISPLAY_DRIFT",
        }
    if "ZERO_PAIR_LOCAL_PAIR_20_54_TRUNCATION_ALIGNMENT" in ids:
        return {
            "subfamily": "LOCAL_PAIR_20_54_TRUNCATION",
            "bridge_id": "B_RESIDUAL_LOCAL_PAIR",
            "likely_speech_act": "local pair truncation member aligned with Book54",
            "reading": "A local-pair truncation line aligned with Book54; read as the shorter member/control of a pair rather than an independent sentence.",
            "confidence": "STRUCTURAL_LOCAL_PAIR_STRONG",
        }
    if "ZERO_PAIR_LOCAL_PAIR_25_39_FAST_BEIE_MICROTEMPLATE" in ids:
        return {
            "subfamily": "LOCAL_PAIR_25_39_FAST_BEIE",
            "bridge_id": "B_RESIDUAL_LOCAL_PAIR",
            "likely_speech_act": "FAST/BEIE local-pair microtemplate",
            "reading": "A FAST/BEIE microtemplate line in a small local pair; useful for pair comparison, not a standalone gloss.",
            "confidence": "STRUCTURAL_LOCAL_PAIR_MICRO",
        }
    if any(tag.startswith("RESIDUAL_TEMPLATE_TO_") for tag in ids):
        matches = sorted(tag.replace("RESIDUAL_TEMPLATE_TO_", "") for tag in ids if tag.startswith("RESIDUAL_TEMPLATE_TO_"))
        return {
            "subfamily": "RESIDUAL_TEMPLATE_CLUSTER",
            "bridge_id": "B_RESIDUAL_TEMPLATE_CLUSTER",
            "likely_speech_act": f"residual template alignment to Books {', '.join(matches)}",
            "reading": f"A residual-template alignment line tied to stronger neighboring Books {', '.join(matches)}; use it as cluster evidence and do not copy those books' readings.",
            "confidence": "STRUCTURAL_TEMPLATE_ALIGNMENT",
        }
    if "LTAST_TTNVVN_BOUNDARY_OPERATOR" in ids:
        return {
            "subfamily": "LTAST_BOUNDARY_RESIDUAL",
            "bridge_id": "B_RESIDUAL_LTAST_BOUNDARY",
            "likely_speech_act": "LTAST/TTNVVN boundary-handoff residual",
            "reading": "An LTAST/TTNVVN boundary-handoff line; it marks a formula/boundary transition but does not provide a lexical translation.",
            "confidence": "STRUCTURAL_BOUNDARY_OPERATOR",
        }
    if "O23_ONAF_VEINLETFNAAST_PAYLOAD_CONTEXT" in ids:
        return {
            "subfamily": "O23_FNAAST_ENDPOINT_PAYLOAD",
            "bridge_id": "B_RESIDUAL_O23_FNAAST_ENDPOINT",
            "likely_speech_act": "O23/ONAF endpoint payload line",
            "reading": "A direct O23/ONAF endpoint line carrying exact VEINLETFNAAST payload context; keep it as endpoint structure without importing meaning into other books.",
            "confidence": "STRUCTURAL_ENDPOINT_PAYLOAD",
        }
    if "BOOK56_CLEAN_COMPONENT_WITH_BOOK38" in ids:
        return {
            "subfamily": "BOOK56_BOOK38_CLEAN_COMPONENT",
            "bridge_id": "B_RESIDUAL_O23_FNAAST_ENDPOINT",
            "likely_speech_act": "Book56 clean component shared with Book38",
            "reading": "A clean component/control line shared with Book38 endpoint material; useful as a component witness, not a full endpoint gloss.",
            "confidence": "STRUCTURAL_COMPONENT_CONTROL",
        }
    if "CHAYENNE_NEAR_VARIANT" in ids:
        return {
            "subfamily": "CHAYENNE_NEAR_VARIANT_RESIDUAL",
            "bridge_id": "B_RESIDUAL_CHAYENNE_NEAR_VARIANT",
            "likely_speech_act": "Chayenne near-frame variant",
            "reading": "A near-frame variant related to the Chayenne external shape; treat it as a frame witness, not the Chayenne phrase itself.",
            "confidence": "STRUCTURAL_NEAR_FRAME",
        }
    if "BOOK7_NEIAAETTA_CONTINUITY" in ids:
        return {
            "subfamily": "NEIAAETTA_CONTINUITY_RESIDUAL",
            "bridge_id": "B_RESIDUAL_NEIAAETTA_CONTINUITY",
            "likely_speech_act": "NEIAAETTA continuity-only control",
            "reading": "A continuity-only line with NEIAAETTA but without the Book7 TIINNEF phase anchor; keep it as a control for phase readings.",
            "confidence": "STRUCTURAL_CONTINUITY_ONLY",
        }
    if "BOOK55_INTERNAL_REPEAT_VARIANT" in ids:
        return {
            "subfamily": "BOOK55_INTERNAL_REPEAT_RESIDUAL",
            "bridge_id": "B_RESIDUAL_BOOK55_REPEAT",
            "likely_speech_act": "Book55 internal repeat/variant control",
            "reading": "An internal repeat/variant line centered on VFETTIITAV material; useful as a repeat-control witness, not a refrain translation.",
            "confidence": "STRUCTURAL_INTERNAL_REPEAT",
        }
    return {
        "subfamily": "UNCLASSIFIED_RESIDUAL",
        "bridge_id": "B_RESIDUAL_TEMPLATE_CLUSTER",
        "likely_speech_act": "unclassified residual line",
        "reading": "An unclassified residual line that needs manual family assignment before stronger human reading.",
        "confidence": "STRUCTURAL_AUDIT_ONLY",
    }


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_residual_shadow_v1_runs (
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

        CREATE TABLE IF NOT EXISTS human_residual_shadow_v1_items (
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


def table_map(conn: sqlite3.Connection, table: str, key: str = "bookid") -> dict[str, dict[str, object]]:
    row = conn.execute(f"SELECT max(run_id) AS run_id FROM {table}").fetchone()
    if row is None or row["run_id"] is None:
        return {}
    run_id = int(row["run_id"])
    return {str(item[key]): dict(item) for item in conn.execute(f"SELECT * FROM {table} WHERE run_id=?", (run_id,)).fetchall() if key in item.keys()}


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    bridge_run_id = max_id(conn, "human_residual_bridge_v1_items")
    source_audit_run_id = max_id(conn, "human_translation_completion_audit_v4_missing_books")
    bridges = {
        row["bridge_id"]: dict(row)
        for row in conn.execute(
            "SELECT * FROM human_residual_bridge_v1_items WHERE run_id=?",
            (bridge_run_id,),
        ).fetchall()
    }
    targets = [
        str(row["bookid"])
        for row in conn.execute(
            "SELECT bookid FROM human_translation_completion_audit_v4_missing_books WHERE run_id=? ORDER BY CAST(bookid AS INTEGER)",
            (source_audit_run_id,),
        ).fetchall()
    ]
    if not targets:
        raise RuntimeError("no residual targets found in latest completion audit v4")

    placeholders = ",".join("?" for _ in targets)
    support_tables = {
        "btii_display_drift_gate": table_map(conn, "btii_display_drift_gate_items"),
        "book55_internal_repeat_gate": table_map(conn, "book55_internal_repeat_gate_items"),
        "book56_clean_component_gate": table_map(conn, "book56_clean_component_gate_items"),
        "book7_phase_continuity_gate": table_map(conn, "book7_phase_continuity_gate_items"),
        "chayenne_near_variant_gate": table_map(conn, "chayenne_near_variant_gate_items"),
        "ltast_boundary_operator_gate": table_map(conn, "ltast_boundary_operator_gate_items"),
        "o23_onaf_payload_gate": table_map(conn, "o23_onaf_payload_gate_items"),
        "residual_template_context_gate": table_map(conn, "residual_template_context_gate_items"),
        "zero_pair_local_context_gate": table_map(conn, "zero_pair_local_context_gate_items"),
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
        cls = classify(bookid, str(row["functional_tags_json"]))
        bridge = bridges[cls["bridge_id"]]
        blocked_claims = [
            "No lexical gloss is promoted for residual components, markers, pairs, endpoints, or display/formula fragments.",
            bridge["blocked_overreach"],
        ]
        evidence = {
            "functional_tags_json": row["functional_tags_json"],
            "honest_text": row["honest_text"],
            "symbol_text": row["symbol_text"],
            "token_text": row["token_text"],
            "support_rows": {name: items.get(bookid, {}) for name, items in support_tables.items()},
        }
        prepared.append(
            {
                "bookid": bookid,
                "subfamily": cls["subfamily"],
                "likely_speech_act": cls["likely_speech_act"],
                "reading": cls["reading"],
                "confidence": cls["confidence"],
                "bridge": bridge,
                "blocked_claims": blocked_claims,
                "falsifier": f"If Book {bookid} gains a stronger non-residual family route, replace this residual reading.",
                "next_probe": bridge["next_probe"],
                "evidence": evidence,
            }
        )

    if len(prepared) != len(targets):
        found = {item["bookid"] for item in prepared}
        missing = [target for target in targets if target not in found]
        raise RuntimeError(f"missing prepared residual targets: {missing}")

    subfamilies = sorted({item["subfamily"] for item in prepared})
    cur = conn.execute(
        """
        INSERT INTO human_residual_shadow_v1_runs
        (created_at, decision, bridge_run_id, source_audit_run_id,
         item_count, subfamily_count, canonical_promotion_count, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            now(),
            "HUMAN_RESIDUAL_SHADOW_READY_NOT_PROMOTED",
            bridge_run_id,
            source_audit_run_id,
            len(prepared),
            len(subfamilies),
            0,
            json.dumps({"subfamilies": subfamilies, "source": "completion_audit_v4_all_remaining_residuals"}, ensure_ascii=False, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)
    for item in prepared:
        bridge = item["bridge"]
        conn.execute(
            """
            INSERT INTO human_residual_shadow_v1_items
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
                "decision": "HUMAN_RESIDUAL_SHADOW_READY_NOT_PROMOTED",
                "item_count": len(prepared),
                "subfamily_count": len(subfamilies),
                "canonical_promotion_count": 0,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
