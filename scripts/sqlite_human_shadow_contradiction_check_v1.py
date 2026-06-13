#!/usr/bin/env python3
"""Audit human shadow readings against canonical functional evidence.

The goal is to keep plausible prose useful but falsifiable. A shadow reading
passes only if it stays non-promoted, cites a live route, exposes blockers, has a
falsifier/next probe, and matches the functional tag family it claims.
"""

from __future__ import annotations

import datetime as dt
import json
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"


EXPECTED_TAG_FRAGMENTS = {
    "49": ["SELF_CONTAINED_REPEAT_FORMULA"],
    "12": ["BOOK30_CORE_CONTEXT"],
    "30": ["BOOK30_CORE_CONTEXT"],
    "26": ["BOOK30_CORE_CONTEXT"],
    "7": ["BOOK7_NEIAAETTA_CONTINUITY", "BOOK7_TIINNEF_PHASE_ANCHOR"],
    "21": ["BOOK30_CORE_CONTEXT"],
    "54": ["ZERO_PAIR_LOCAL_PAIR_20_54_TRUNCATION_ALIGNMENT"],
}

FORBIDDEN_DIRECT_GLOSS_PATTERNS = [
    r"\btranslates?\s+to\b",
    r"\bmeans?\s+['\"]",
    r"\bis\s+the\s+word\s+for\b",
    r"\bcanonical\s+translation\b",
]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_shadow_contradiction_check_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            shadow_run_id INTEGER NOT NULL,
            route_run_id INTEGER NOT NULL,
            external_phrase_run_id INTEGER,
            checked_count INTEGER NOT NULL,
            pass_count INTEGER NOT NULL,
            contradiction_count INTEGER NOT NULL,
            promotion_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_shadow_contradiction_check_v1_items (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            route_id TEXT NOT NULL,
            check_status TEXT NOT NULL,
            issue_count INTEGER NOT NULL,
            issues_json TEXT NOT NULL,
            functional_match_json TEXT NOT NULL,
            external_overlap_json TEXT NOT NULL,
            next_action TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        );
        """
    )


def max_id(conn: sqlite3.Connection, table: str, required: bool = True) -> int | None:
    row = conn.execute(f"SELECT max(run_id) AS run_id FROM {table}").fetchone()
    if row is None or row["run_id"] is None:
        if required:
            raise RuntimeError(f"missing required run: {table}")
        return None
    return int(row["run_id"])


def parse_json(value: str | None, fallback):
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def tag_blob(functional_basis: dict[str, object]) -> str:
    tags = functional_basis.get("functional_tags_json")
    return tags if isinstance(tags, str) else json.dumps(tags, ensure_ascii=False, sort_keys=True)


def direct_gloss_issues(text: str) -> list[str]:
    issues = []
    for pattern in FORBIDDEN_DIRECT_GLOSS_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            issues.append(f"forbidden direct-gloss wording matched: {pattern}")
    return issues


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    shadow_run_id = max_id(conn, "human_shadow_reading_v1_items")
    route_run_id = max_id(conn, "human_translation_route_v1_routes")
    external_phrase_run_id = max_id(conn, "human_external_phrase_corpus_v1_items", required=False)

    route_ids = {
        row["route_id"]
        for row in conn.execute(
            "SELECT route_id FROM human_translation_route_v1_routes WHERE run_id=?",
            (route_run_id,),
        ).fetchall()
    }

    external_by_book: dict[str, list[dict[str, object]]] = {}
    if external_phrase_run_id is not None:
        for row in conn.execute(
            """
            SELECT phrase_id, strong_overlap_books_json, shared_blocks_json
            FROM human_external_phrase_corpus_v1_items
            WHERE run_id=?
            """,
            (external_phrase_run_id,),
        ).fetchall():
            for overlap in parse_json(row["strong_overlap_books_json"], []):
                bookid = str(overlap.get("bookid"))
                external_by_book.setdefault(bookid, []).append(
                    {
                        "phrase_id": row["phrase_id"],
                        "overlap": overlap,
                        "shared_blocks": parse_json(row["shared_blocks_json"], []),
                    }
                )

    items = conn.execute(
        """
        SELECT *
        FROM human_shadow_reading_v1_items
        WHERE run_id=?
        ORDER BY CAST(bookid AS INTEGER)
        """,
        (shadow_run_id,),
    ).fetchall()

    checked = []
    for row in items:
        issues: list[str] = []
        bookid = str(row["bookid"])
        route_id = str(row["route_id"])
        functional_basis = parse_json(row["functional_basis_json"], {})
        blockers = parse_json(row["blocked_claims_json"], [])
        blob = tag_blob(functional_basis)

        if route_id not in route_ids:
            issues.append(f"route not found in latest human route registry: {route_id}")
        if row["canonical_promotion_status"] != "NOT_PROMOTED":
            issues.append(f"canonical promotion status is not NOT_PROMOTED: {row['canonical_promotion_status']}")
        if "SHADOW" not in row["candidate_status"]:
            issues.append(f"candidate status is not explicitly shadow: {row['candidate_status']}")
        if not isinstance(blockers, list) or len(blockers) < 2:
            issues.append("blocked claims are missing or too sparse")
        if not row["falsifier"].strip():
            issues.append("missing falsifier")
        if not row["next_probe"].strip():
            issues.append("missing next probe")
        issues.extend(direct_gloss_issues(row["human_paraphrase"]))

        expected = EXPECTED_TAG_FRAGMENTS.get(bookid, [])
        matched = [fragment for fragment in expected if fragment in blob]
        missing = [fragment for fragment in expected if fragment not in blob]
        if missing:
            issues.append(f"functional tag mismatch; missing expected fragments: {', '.join(missing)}")

        external_overlap = external_by_book.get(bookid, [])
        if external_overlap:
            # External overlap is not a contradiction by itself, but a shadow draft
            # must explicitly route through source comparison before prose expansion.
            if "external" not in row["next_probe"].lower() and "shape" not in row["next_probe"].lower():
                issues.append("book has strong external phrase overlap but next_probe does not mention external/shape review")

        status = "SHADOW_CONSISTENT_READY_FOR_NEXT_PROBE" if not issues else "SHADOW_CONTRADICTION_OR_INCOMPLETE"
        next_action = (
            "Run the stated next_probe; do not promote prose."
            if not issues
            else "Revise or demote the shadow reading before using it for semantic search."
        )
        checked.append(
            {
                "bookid": bookid,
                "route_id": route_id,
                "status": status,
                "issues": issues,
                "functional_match": {
                    "expected": expected,
                    "matched": matched,
                    "missing": missing,
                },
                "external_overlap": external_overlap,
                "next_action": next_action,
                "evidence": {
                    "shadow_run_id": shadow_run_id,
                    "route_run_id": route_run_id,
                    "external_phrase_run_id": external_phrase_run_id,
                    "likely_speech_act": row["likely_speech_act"],
                },
            }
        )

    pass_count = sum(1 for row in checked if row["status"] == "SHADOW_CONSISTENT_READY_FOR_NEXT_PROBE")
    contradiction_count = len(checked) - pass_count
    promotion_count = sum(
        1
        for row in items
        if row["canonical_promotion_status"] != "NOT_PROMOTED"
    )
    decision = (
        "HUMAN_SHADOW_READINGS_CONSISTENT_NEXT_PROBES_READY"
        if contradiction_count == 0 and promotion_count == 0
        else "HUMAN_SHADOW_READINGS_NEED_REVISION"
    )
    payload = {
        "policy": "human prose remains shadow unless it survives independent probes",
        "expected_tag_fragments": EXPECTED_TAG_FRAGMENTS,
    }
    cur = conn.execute(
        """
        INSERT INTO human_shadow_contradiction_check_v1_runs
        (created_at, decision, shadow_run_id, route_run_id, external_phrase_run_id,
         checked_count, pass_count, contradiction_count, promotion_count, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            now(),
            decision,
            shadow_run_id,
            route_run_id,
            external_phrase_run_id,
            len(checked),
            pass_count,
            contradiction_count,
            promotion_count,
            json.dumps(payload, ensure_ascii=False, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)
    for row in checked:
        conn.execute(
            """
            INSERT INTO human_shadow_contradiction_check_v1_items
            (run_id, bookid, route_id, check_status, issue_count, issues_json,
             functional_match_json, external_overlap_json, next_action, evidence_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                row["bookid"],
                row["route_id"],
                row["status"],
                len(row["issues"]),
                json.dumps(row["issues"], ensure_ascii=False, sort_keys=True),
                json.dumps(row["functional_match"], ensure_ascii=False, sort_keys=True),
                json.dumps(row["external_overlap"], ensure_ascii=False, sort_keys=True),
                row["next_action"],
                json.dumps(row["evidence"], ensure_ascii=False, sort_keys=True),
            ),
        )

    conn.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "checked_count": len(checked),
                "pass_count": pass_count,
                "contradiction_count": contradiction_count,
                "promotion_count": promotion_count,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
