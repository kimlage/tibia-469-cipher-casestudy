#!/usr/bin/env python3
"""Audit atlas v6 shadow readings for structural contradictions and review tiers."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

BRIDGE_TABLES = [
    "human_anchor_to_shadow_bridge_v1_items",
    "human_c86_vnctiin_bridge_v1_items",
    "human_r20_r02_phase_bridge_v1_items",
    "human_slot_formula_bridge_v1_items",
    "human_residual_bridge_v1_items",
]
AUDIT_TERMS = ("AUDIT", "WEAK", "MICRO", "UNIQUE", "SPECIAL", "HOLDOUT", "NO_PROMOTION")
LOW_PROMOTION_TERMS = AUDIT_TERMS + ("VARIANT", "CONTROL", "RESIDUAL", "DISPLAY_DRIFT")
PROHIBITED_PROMOTION_WORDS = (
    "translate ",
    "translation of",
    "means ",
    "means:",
    "gloss is",
    "word for",
)
NEGATED_PROMOTION_PHRASES = (
    "not a translated",
    "not as translated",
    "no translated",
    "without translated",
    "not a translation",
    "not as translation",
    "no translation",
)


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_json(value: str | None, fallback):
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_atlas_v6_contradiction_audit_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            atlas_v6_run_id INTEGER NOT NULL,
            item_count INTEGER NOT NULL,
            pass_count INTEGER NOT NULL,
            warn_count INTEGER NOT NULL,
            fail_count INTEGER NOT NULL,
            promotion_review_candidate_count INTEGER NOT NULL,
            stable_shadow_count INTEGER NOT NULL,
            audit_only_count INTEGER NOT NULL,
            promoted_gloss_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_atlas_v6_contradiction_audit_v1_items (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            audit_status TEXT NOT NULL,
            review_tier TEXT NOT NULL,
            issue_codes_json TEXT NOT NULL,
            source_layer TEXT NOT NULL,
            confidence_tier TEXT NOT NULL,
            support_level TEXT NOT NULL,
            source_bridge_id TEXT NOT NULL,
            promotion_review_candidate INTEGER NOT NULL,
            reason TEXT NOT NULL,
            next_action TEXT NOT NULL,
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


def load_bridges(conn: sqlite3.Connection) -> dict[str, dict[str, object]]:
    bridges: dict[str, dict[str, object]] = {}
    for table in BRIDGE_TABLES:
        run_id = max_id(conn, table)
        for row in conn.execute(f"SELECT * FROM {table} WHERE run_id=?", (run_id,)).fetchall():
            item = dict(row)
            item["_bridge_table"] = table
            bridges[str(row["bridge_id"])] = item
    return bridges


def has_any(text: str, terms: tuple[str, ...]) -> bool:
    upper = text.upper()
    return any(term in upper for term in terms)


def promotion_review_candidate(row: sqlite3.Row) -> bool:
    confidence = str(row["confidence_tier"])
    support = str(row["support_level"])
    source_layer = str(row["source_layer"])
    combined = f"{confidence} {support} {source_layer}"
    if "STRONG" not in confidence.upper():
        return False
    if has_any(combined, LOW_PROMOTION_TERMS):
        return False
    if source_layer == "human_residual_shadow_v1":
        return False
    return True


def uses_unnegated_promotion_language(reading: str) -> bool:
    lower = reading.lower()
    if any(phrase in lower for phrase in NEGATED_PROMOTION_PHRASES):
        return False
    return any(word in lower for word in PROHIBITED_PROMOTION_WORDS)


def review_tier(row: sqlite3.Row) -> str:
    confidence = str(row["confidence_tier"])
    support = str(row["support_level"])
    combined = f"{confidence} {support} {row['source_layer']}"
    if promotion_review_candidate(row):
        return "PROMOTION_REVIEW_CANDIDATE"
    if has_any(combined, AUDIT_TERMS):
        return "AUDIT_ONLY_SHADOW"
    if "VARIANT" in combined.upper() or "CONTROL" in combined.upper() or "RESIDUAL" in combined.upper():
        return "CONTROL_OR_VARIANT_SHADOW"
    return "STABLE_SHADOW_REVIEW"


def audit_row(row: sqlite3.Row, bridges: dict[str, dict[str, object]]) -> tuple[str, list[str], str, str]:
    issues: list[str] = []
    warnings: list[str] = []
    bridge_id = str(row["source_bridge_id"])
    anchors = parse_json(str(row["anchor_ids_json"]), [])
    blocked_claims = parse_json(str(row["blocked_claims_json"]), [])
    reading = str(row["plausible_human_reading"] or "")
    blocked = str(row["blocked_overreach"] or "")
    falsifier = str(row["falsifier"] or "")
    next_probe = str(row["next_probe"] or "")
    promotion_status = str(row["promotion_status"] or "")

    if str(row["target_kind"]) != "book":
        issues.append("NON_BOOK_TARGET")
    if not reading.strip():
        issues.append("EMPTY_HUMAN_READING")
    if not bridge_id:
        issues.append("MISSING_BRIDGE_ID")
    elif bridge_id not in bridges:
        issues.append("UNKNOWN_BRIDGE_ID")
    if not isinstance(anchors, list) or not anchors:
        issues.append("MISSING_ANCHORS")
    if promotion_status != "NOT_PROMOTED":
        issues.append("UNEXPECTED_CANONICAL_PROMOTION")
    if not blocked_claims:
        warnings.append("EMPTY_BLOCKED_CLAIMS")
    if not blocked.strip():
        warnings.append("EMPTY_BLOCKED_OVERREACH")
    if not falsifier.strip():
        warnings.append("EMPTY_FALSIFIER")
    if not next_probe.strip():
        warnings.append("EMPTY_NEXT_PROBE")

    if uses_unnegated_promotion_language(reading):
        warnings.append("READING_USES_PROMOTION_LANGUAGE")
    if promotion_review_candidate(row) and has_any(reading, AUDIT_TERMS):
        warnings.append("PROMOTION_CANDIDATE_READING_CONTAINS_AUDIT_LANGUAGE")
    if review_tier(row) == "AUDIT_ONLY_SHADOW" and not has_any(f"{reading} {blocked}", ("AUDIT", "CONTROL", "HOLD", "NOT ", "NO ", "WITHOUT", "WEAK")):
        warnings.append("AUDIT_TIER_LACKS_CAUTION_LANGUAGE")

    status = "FAIL" if issues else ("WARN" if warnings else "PASS")
    all_codes = issues + warnings
    if status == "FAIL":
        reason = "hard contradiction or missing required evidence in shadow atlas row"
        next_action = "revise row or bridge before relying on atlas v6"
    elif status == "WARN":
        reason = "shadow reading is usable but has review-language or metadata warnings"
        next_action = "review wording before any promotion attempt"
    else:
        reason = "shadow reading has required anchors, bridge, blocked claims, falsifier, and NOT_PROMOTED status"
        next_action = "keep in atlas; only promote after separate falsification package"
    return status, all_codes, reason, next_action


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    atlas_run_id = max_id(conn, "human_translation_atlas_v6_items")
    bridges = load_bridges(conn)
    rows = conn.execute(
        """
        SELECT *
        FROM human_translation_atlas_v6_items
        WHERE run_id=?
        ORDER BY CAST(target_id AS INTEGER)
        """,
        (atlas_run_id,),
    ).fetchall()
    expected = [str(i) for i in range(70)]
    found = [str(row["target_id"]) for row in rows]
    missing_books = [book for book in expected if book not in found]
    duplicate_books = sorted({book for book in found if found.count(book) > 1}, key=int)

    items = []
    for row in rows:
        status, issue_codes, reason, next_action = audit_row(row, bridges)
        tier = review_tier(row)
        candidate = 1 if promotion_review_candidate(row) else 0
        items.append(
            {
                "bookid": str(row["target_id"]),
                "audit_status": status,
                "review_tier": tier,
                "issue_codes": issue_codes,
                "source_layer": str(row["source_layer"]),
                "confidence_tier": str(row["confidence_tier"]),
                "support_level": str(row["support_level"]),
                "source_bridge_id": str(row["source_bridge_id"]),
                "promotion_review_candidate": candidate,
                "reason": reason,
                "next_action": next_action,
                "evidence": {
                    "likely_speech_act": row["likely_speech_act"],
                    "plausible_human_reading": row["plausible_human_reading"],
                    "anchor_ids_json": row["anchor_ids_json"],
                    "blocked_claims_json": row["blocked_claims_json"],
                    "blocked_overreach": row["blocked_overreach"],
                    "falsifier": row["falsifier"],
                    "next_probe": row["next_probe"],
                    "promotion_status": row["promotion_status"],
                    "bridge_table": bridges.get(str(row["source_bridge_id"]), {}).get("_bridge_table", ""),
                },
            }
        )

    if missing_books:
        for bookid in missing_books:
            items.append(
                {
                    "bookid": bookid,
                    "audit_status": "FAIL",
                    "review_tier": "MISSING_BOOK",
                    "issue_codes": ["MISSING_FROM_ATLAS_V6"],
                    "source_layer": "",
                    "confidence_tier": "",
                    "support_level": "",
                    "source_bridge_id": "",
                    "promotion_review_candidate": 0,
                    "reason": "book is absent from atlas v6",
                    "next_action": "add shadow reading before review",
                    "evidence": {},
                }
            )
    if duplicate_books:
        for item in items:
            if item["bookid"] in duplicate_books:
                item["audit_status"] = "FAIL"
                item["issue_codes"].append("DUPLICATE_BOOK_IN_ATLAS_V6")

    pass_count = sum(1 for item in items if item["audit_status"] == "PASS")
    warn_count = sum(1 for item in items if item["audit_status"] == "WARN")
    fail_count = sum(1 for item in items if item["audit_status"] == "FAIL")
    candidate_count = sum(item["promotion_review_candidate"] for item in items)
    stable_count = sum(1 for item in items if item["review_tier"] in {"STABLE_SHADOW_REVIEW", "CONTROL_OR_VARIANT_SHADOW"})
    audit_count = sum(1 for item in items if item["review_tier"] == "AUDIT_ONLY_SHADOW")
    promoted = sum(1 for row in rows if str(row["promotion_status"]) != "NOT_PROMOTED")
    if fail_count:
        decision = "HUMAN_ATLAS_V6_CONTRADICTION_AUDIT_FAIL_REVISE"
    elif warn_count:
        decision = "HUMAN_ATLAS_V6_CONTRADICTION_AUDIT_PASS_WITH_WARNINGS_NO_PROMOTION"
    else:
        decision = "HUMAN_ATLAS_V6_CONTRADICTION_AUDIT_PASS_NO_PROMOTION"

    cur = conn.execute(
        """
        INSERT INTO human_atlas_v6_contradiction_audit_v1_runs
        (created_at, decision, atlas_v6_run_id, item_count, pass_count,
         warn_count, fail_count, promotion_review_candidate_count,
         stable_shadow_count, audit_only_count, promoted_gloss_count,
         payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            now(),
            decision,
            atlas_run_id,
            len(items),
            pass_count,
            warn_count,
            fail_count,
            candidate_count,
            stable_count,
            audit_count,
            promoted,
            json.dumps(
                {
                    "missing_books": missing_books,
                    "duplicate_books": duplicate_books,
                    "bridge_count": len(bridges),
                    "principle": "audit shadow readings for review readiness only; no canonical gloss promotion",
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
        ),
    )
    run_id = int(cur.lastrowid)
    for item in items:
        conn.execute(
            """
            INSERT INTO human_atlas_v6_contradiction_audit_v1_items
            (run_id, bookid, audit_status, review_tier, issue_codes_json,
             source_layer, confidence_tier, support_level, source_bridge_id,
             promotion_review_candidate, reason, next_action, evidence_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                item["bookid"],
                item["audit_status"],
                item["review_tier"],
                json.dumps(item["issue_codes"], ensure_ascii=False, sort_keys=True),
                item["source_layer"],
                item["confidence_tier"],
                item["support_level"],
                item["source_bridge_id"],
                item["promotion_review_candidate"],
                item["reason"],
                item["next_action"],
                json.dumps(item["evidence"], ensure_ascii=False, sort_keys=True),
            ),
        )

    conn.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "item_count": len(items),
                "pass_count": pass_count,
                "warn_count": warn_count,
                "fail_count": fail_count,
                "promotion_review_candidate_count": candidate_count,
                "stable_shadow_count": stable_count,
                "audit_only_count": audit_count,
                "promoted_gloss_count": promoted,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
