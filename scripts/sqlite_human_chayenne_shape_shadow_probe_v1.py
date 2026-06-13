#!/usr/bin/env python3
"""Human-route probe for the Chayenne external 469 shape overlap.

The Chayenne phrase is the strongest current external shape overlap. This probe
tests how that shared block behaves inside the current v19 functional layer,
without treating it as a plaintext translation.
"""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
PHRASE_ID = "CHAYENNE_REPLY"
BLOCK = "AEFIEIEFIIVFAEATVAT"


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
        CREATE TABLE IF NOT EXISTS human_chayenne_shape_shadow_probe_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            external_phrase_run_id INTEGER NOT NULL,
            shape_gate_run_id INTEGER NOT NULL,
            book_count INTEGER NOT NULL,
            branch_count INTEGER NOT NULL,
            direct_meaning_allowed INTEGER NOT NULL,
            accepted_human_gloss_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_chayenne_shape_shadow_probe_v1_items (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            block_pos INTEGER NOT NULL,
            left_context TEXT NOT NULL,
            right_context TEXT NOT NULL,
            branch_class TEXT NOT NULL,
            functional_tags_json TEXT NOT NULL,
            human_shadow_role TEXT NOT NULL,
            blocked_claims_json TEXT NOT NULL,
            falsifier TEXT NOT NULL,
            next_probe TEXT NOT NULL,
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


def branch_from_tags(tags: list[dict[str, object]]) -> str:
    tag_ids = {str(tag.get("tag_id")) for tag in tags if isinstance(tag, dict)}
    if "BENNA_FORMULA_BRIDGE" in tag_ids:
        return "BENNA_LTAST_FORMULA_BRANCH"
    if "LTAST_TTNVVN_BOUNDARY_OPERATOR" in tag_ids and "VNCTIIN_CONTEXT_FRAME" in tag_ids:
        return "LTAST_TO_VNCTIIN_BRANCH"
    if "VNCTIIN_CONTEXT_FRAME" in tag_ids:
        return "VNCTIIN_CONTEXT_BRANCH"
    if any(tag.startswith("RESIDUAL_TEMPLATE") for tag in tag_ids):
        return "RESIDUAL_CONTINUATION_BRANCH"
    return "UNCLASSIFIED_CHAYENNE_BRANCH"


def role_for_branch(branch: str) -> tuple[str, list[str], str, str]:
    if branch == "VNCTIIN_CONTEXT_BRANCH":
        return (
            "external shape frame embedded in VNCTIIN context",
            [
                "No proof that the Chayenne phrase means the VNCTIIN context.",
                "No proof that this block is a word or sentence.",
            ],
            "If non-VNCTIIN books share the same context behavior, the branch label is too narrow.",
            "Use Book 8 as the clean VNCTIIN branch control for Chayenne shape.",
        )
    if branch == "LTAST_TO_VNCTIIN_BRANCH":
        return (
            "external shape frame after LTAST boundary handoff into VNCTIIN",
            [
                "LTAST boundary behavior is structural, not a translation.",
                "The same Chayenne block cannot be a single English phrase if its branch context changes.",
            ],
            "If Book 37 does not bridge LTAST into VNCTIIN in held-out controls, demote this branch.",
            "Compare Book 37 against LTAST boundary books without Chayenne shape.",
        )
    if branch == "RESIDUAL_CONTINUATION_BRANCH":
        return (
            "external shape frame in residual continuation template",
            [
                "Residual-template alignment is lower confidence than clean VNCTIIN branches.",
                "No semantic import from Chayenne is allowed.",
            ],
            "If residual templates do not preserve the block context, keep Book 63 audit-only.",
            "Use Book 63 as residual/audit branch, not as a translation witness.",
        )
    if branch == "BENNA_LTAST_FORMULA_BRANCH":
        return (
            "external shape frame inside BENNA/LTAST formula branch",
            [
                "BENNA formula bridge remains functional only.",
                "Shared Chayenne block does not prove BENNA semantics.",
            ],
            "If BENNA/LTAST controls do not predict the block placement, demote branch linkage.",
            "Compare Book 66 against BENNA/LTAST books without external shape.",
        )
    return (
        "unclassified external shape frame",
        ["Branch class is not stable enough for human prose."],
        "If no branch class emerges, keep external shape as audit-only.",
        "Inspect manually.",
    )


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    external_phrase_run_id = max_id(conn, "human_external_phrase_corpus_v1_items")
    shape_gate_run_id = max_id(conn, "chayenne_external_shape_gate_items")
    phrase = conn.execute(
        """
        SELECT *
        FROM human_external_phrase_corpus_v1_items
        WHERE run_id=? AND phrase_id=?
        """,
        (external_phrase_run_id, PHRASE_ID),
    ).fetchone()
    if phrase is None:
        raise RuntimeError("missing CHAYENNE_REPLY in human external phrase corpus")
    overlap_books = [
        str(item.get("bookid"))
        for item in parse_json(phrase["strong_overlap_books_json"], [])
        if item.get("bookid") is not None
    ]
    if not overlap_books:
        raise RuntimeError("CHAYENNE_REPLY has no strong overlap books in current corpus")

    placeholders = ",".join("?" for _ in overlap_books)
    books = conn.execute(
        f"""
        SELECT b.bookid, b.functional_tags_json, t.symbol_text
        FROM final_honest_reading_v19_books b
        JOIN row0_variant_book_tokens t
          ON t.bookid=b.bookid
         AND t.run_id=(SELECT max(run_id) FROM row0_variant_book_tokens)
        WHERE b.run_id=(SELECT max(run_id) FROM final_honest_reading_v19_books)
          AND b.bookid IN ({placeholders})
        ORDER BY CAST(b.bookid AS INTEGER)
        """,
        tuple(overlap_books),
    ).fetchall()

    records = []
    for row in books:
        text = str(row["symbol_text"])
        pos = text.find(BLOCK)
        tags = parse_json(row["functional_tags_json"], [])
        branch = branch_from_tags(tags)
        role, blockers, falsifier, next_probe = role_for_branch(branch)
        records.append(
            {
                "bookid": str(row["bookid"]),
                "block_pos": pos,
                "left_context": text[max(0, pos - 24) : pos] if pos >= 0 else "",
                "right_context": text[pos + len(BLOCK) : pos + len(BLOCK) + 32] if pos >= 0 else "",
                "branch": branch,
                "tags_json": row["functional_tags_json"],
                "role": role,
                "blockers": blockers,
                "falsifier": falsifier,
                "next_probe": next_probe,
            }
        )

    branches = sorted({record["branch"] for record in records})
    if len(branches) >= 3 and all(record["block_pos"] >= 0 for record in records):
        decision = "CHAYENNE_EXTERNAL_SHAPE_IS_REGISTER_FRAME_NOT_SINGLE_GLOSS"
    elif records:
        decision = "CHAYENNE_EXTERNAL_SHAPE_BRANCHING_PARTIAL_NO_GLOSS"
    else:
        decision = "CHAYENNE_EXTERNAL_SHAPE_NOT_ACTIONABLE"
    payload = {
        "phrase_id": PHRASE_ID,
        "block": BLOCK,
        "overlap_books": overlap_books,
        "branches": branches,
        "source_url": phrase["source_url"],
        "principle": "external phrase shape can constrain register/branch behavior, not plaintext",
    }
    cur = conn.execute(
        """
        INSERT INTO human_chayenne_shape_shadow_probe_v1_runs
        (created_at, decision, external_phrase_run_id, shape_gate_run_id,
         book_count, branch_count, direct_meaning_allowed,
         accepted_human_gloss_count, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            now(),
            decision,
            external_phrase_run_id,
            shape_gate_run_id,
            len(records),
            len(branches),
            0,
            0,
            json.dumps(payload, ensure_ascii=False, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)
    for record in records:
        conn.execute(
            """
            INSERT INTO human_chayenne_shape_shadow_probe_v1_items
            (run_id, bookid, block_pos, left_context, right_context,
             branch_class, functional_tags_json, human_shadow_role,
             blocked_claims_json, falsifier, next_probe, evidence_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                record["bookid"],
                record["block_pos"],
                record["left_context"],
                record["right_context"],
                record["branch"],
                record["tags_json"],
                record["role"],
                json.dumps(record["blockers"], ensure_ascii=False, sort_keys=True),
                record["falsifier"],
                record["next_probe"],
                json.dumps(
                    {
                        "phrase_id": PHRASE_ID,
                        "block": BLOCK,
                        "external_phrase_run_id": external_phrase_run_id,
                        "shape_gate_run_id": shape_gate_run_id,
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                ),
            ),
        )

    conn.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "book_count": len(records),
                "branch_count": len(branches),
                "branches": branches,
                "accepted_human_gloss_count": 0,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
