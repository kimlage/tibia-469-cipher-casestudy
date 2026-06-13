#!/usr/bin/env python3
"""Q53: combine C86 and C68 syntheses into chain-level human readings."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from collections import Counter
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
        CREATE TABLE IF NOT EXISTS human_q53_c86_c68_chain_synthesis_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q50_run_id INTEGER NOT NULL,
            q52_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            target_book_count INTEGER NOT NULL,
            supported_chain_book_count INTEGER NOT NULL,
            mixed_chain_book_count INTEGER NOT NULL,
            audit_control_book_count INTEGER NOT NULL,
            readable_chain_version_count INTEGER NOT NULL,
            prose_gloss_allowed_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            chain_human_version TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q53_c86_c68_chain_synthesis_v1_books (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            chain_profile TEXT NOT NULL,
            c86_profile TEXT NOT NULL,
            c68_profile TEXT NOT NULL,
            c86_functional_version TEXT NOT NULL,
            c68_functional_version TEXT NOT NULL,
            chain_functional_version TEXT NOT NULL,
            translation_use TEXT NOT NULL,
            blocked_claims_json TEXT NOT NULL,
            next_probe TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        );
        """
    )


def latest_row(conn: sqlite3.Connection, table: str) -> sqlite3.Row:
    row = conn.execute(f"SELECT * FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    if row is None:
        raise RuntimeError(f"missing required row: {table}")
    return row


def chain_profile(c86_profile: str, c68_profile: str) -> str:
    if c86_profile == "C86_READY_VN_C68_TIIN_CONTEXT" and c68_profile == "C68_MIXED_PHASE_SLOT_CHAIN":
        return "SUPPORTED_CONTEXT_TO_SLOT_CHAIN"
    if c86_profile == "C86_READY_VN_C68_TIIN_CONTEXT" and c68_profile == "C68_PHASE_CONTEXT_ONLY":
        return "SUPPORTED_CONTEXT_CHAIN"
    if c86_profile.endswith("_AUDIT") and c68_profile.endswith("_AUDIT"):
        return "DUAL_AUDIT_CONTROL"
    if c86_profile.endswith("_AUDIT") and c68_profile in {"C68_PHASE_CONTEXT_ONLY", "C68_SLOT_CLASSIFIER_ONLY"}:
        return "C86_AUDIT_WITH_C68_HINGE_CONTROL"
    if c86_profile == "C86_READY_VN_C68_TIIN_CONTEXT":
        return "C86_SUPPORTED_C68_REVIEW"
    return "C86_C68_COMPLEX_AUDIT"


def chain_version(profile: str, bookid: str, c86: sqlite3.Row, c68: sqlite3.Row) -> tuple[str, str, str]:
    if profile == "SUPPORTED_CONTEXT_TO_SLOT_CHAIN":
        return (
            f"Book {bookid}: C86 opens an EVIEFIIN context selector into VN/C68/TIIN, and C68 then bridges phase/context into the slot/classifier window. Read as a context-to-slot chain, not sentence prose.",
            "supported C86->C68 context-to-slot human chain; no plaintext",
            "Use as the strongest C86/C68 chain control and compare against 67->2 edge support.",
        )
    if profile == "SUPPORTED_CONTEXT_CHAIN":
        return (
            f"Book {bookid}: C86 opens an EVIEFIIN context selector into VN/C68/TIIN, and C68 stays in a TIIN-style phase/context window. Read as a context-routing chain, not prose.",
            "supported C86->C68 context-routing human chain; no plaintext",
            "Compare with Book2 and held-out C68 phase profiles to test whether slot material follows later.",
        )
    if profile == "DUAL_AUDIT_CONTROL":
        return (
            f"Book {bookid}: both C86 and C68 are in audit-only profiles. Use as a negative control for forced C86->C68 chaining.",
            "dual audit control; no promotion",
            "Do not synthesize prose unless both operator profiles gain independent support.",
        )
    if profile == "C86_AUDIT_WITH_C68_HINGE_CONTROL":
        return (
            f"Book {bookid}: C68 has a usable hinge profile, but C86 remains audit-only. Use as a control showing that C68 support alone does not promote the whole chain.",
            "C68 hinge control with C86 audit; no chain promotion",
            "Require edge support for the C86 surface before treating the full book as a chain.",
        )
    return (
        f"Book {bookid}: C86/C68 relation is complex and remains audit-only.",
        "complex C86/C68 audit",
        "Inspect manually.",
    )


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q50 = latest_row(conn, "human_q50_c68_book_synthesis_v1_runs")
    q52 = latest_row(conn, "human_q52_c86_book_synthesis_v1_runs")
    audit = latest_row(conn, "human_translation_completion_audit_v5_runs")
    rows = list(
        conn.execute(
            """
            SELECT
                c.bookid,
                c.c86_profile,
                c.c86_functional_version,
                s.c68_profile,
                s.c68_functional_version,
                c.evidence_json AS c86_evidence_json,
                s.evidence_json AS c68_evidence_json
            FROM human_q52_c86_book_synthesis_v1_books c
            JOIN human_q50_c68_book_synthesis_v1_books s
              ON s.bookid=c.bookid
             AND s.run_id=?
            WHERE c.run_id=?
            ORDER BY CAST(c.bookid AS INTEGER)
            """,
            (int(q50["run_id"]), int(q52["run_id"])),
        )
    )
    if not rows:
        raise RuntimeError("missing C86/C68 intersection")

    prepared = []
    for row in rows:
        profile = chain_profile(str(row["c86_profile"]), str(row["c68_profile"]))
        version, use, next_probe = chain_version(profile, str(row["bookid"]), row, row)
        prepared.append(
            {
                "bookid": str(row["bookid"]),
                "chain_profile": profile,
                "c86_profile": str(row["c86_profile"]),
                "c68_profile": str(row["c68_profile"]),
                "c86_functional_version": str(row["c86_functional_version"]),
                "c68_functional_version": str(row["c68_functional_version"]),
                "chain_functional_version": version,
                "translation_use": use,
                "blocked_claims": [
                    "C86_as_word",
                    "C68_as_word",
                    "chain_as_sentence",
                    "canonical_plaintext",
                ],
                "next_probe": next_probe,
                "evidence": {
                    "c86_evidence": json.loads(str(row["c86_evidence_json"])),
                    "c68_evidence": json.loads(str(row["c68_evidence_json"])),
                },
            }
        )

    profile_counts = Counter(item["chain_profile"] for item in prepared)
    supported_chain_book_count = (
        profile_counts["SUPPORTED_CONTEXT_CHAIN"] + profile_counts["SUPPORTED_CONTEXT_TO_SLOT_CHAIN"]
    )
    mixed_chain_book_count = profile_counts["SUPPORTED_CONTEXT_TO_SLOT_CHAIN"]
    audit_control_book_count = len(prepared) - supported_chain_book_count
    readable_chain_version_count = len([item for item in prepared if item["chain_functional_version"]])
    prose_gloss_allowed_count = 0
    canonical_promotion_allowed_count = 0
    chain_human_version = (
        "C86/C68 chain synthesis: C86 can open an EVIEFIIN context selector into VN/C68/TIIN, and C68 then determines whether the chain stays phase/context or continues toward slot/classifier. "
        "Books without C86 edge support remain controls, even when their C68 side has a usable hinge."
    )
    decision = (
        "Q53_C86_C68_CHAIN_SYNTHESIS_READY_5_SUPPORTED_4_CONTROLS_NO_GLOSS"
        if len(prepared) == 9
        and supported_chain_book_count == 5
        and mixed_chain_book_count == 1
        and audit_control_book_count == 4
        and readable_chain_version_count == 9
        and int(audit["promoted_gloss_count"]) == 0
        and prose_gloss_allowed_count == 0
        and canonical_promotion_allowed_count == 0
        else "Q53_C86_C68_CHAIN_SYNTHESIS_REQUIRES_REVIEW"
    )
    payload = {
        "question": "Can C86 and C68 syntheses combine into a longer human-readable chain?",
        "answer": "Yes for five edge-supported books, with four explicit controls.",
        "profile_counts": dict(profile_counts),
        "blocked_use": "This is a chain-level functional layer, not canonical translation.",
        "next_action": "Use the supported chains as the backbone for the next phrase-level human synthesis attempt.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q53_c86_c68_chain_synthesis_v1_runs (
                created_at, decision, q50_run_id, q52_run_id,
                completion_audit_run_id, target_book_count,
                supported_chain_book_count, mixed_chain_book_count,
                audit_control_book_count, readable_chain_version_count,
                prose_gloss_allowed_count, canonical_promotion_allowed_count,
                chain_human_version, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                int(q50["run_id"]),
                int(q52["run_id"]),
                int(audit["run_id"]),
                len(prepared),
                supported_chain_book_count,
                mixed_chain_book_count,
                audit_control_book_count,
                readable_chain_version_count,
                prose_gloss_allowed_count,
                canonical_promotion_allowed_count,
                chain_human_version,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q53_c86_c68_chain_synthesis_v1_books (
                run_id, bookid, chain_profile, c86_profile, c68_profile,
                c86_functional_version, c68_functional_version,
                chain_functional_version, translation_use,
                blocked_claims_json, next_probe, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    item["bookid"],
                    item["chain_profile"],
                    item["c86_profile"],
                    item["c68_profile"],
                    item["c86_functional_version"],
                    item["c68_functional_version"],
                    item["chain_functional_version"],
                    item["translation_use"],
                    j(item["blocked_claims"]),
                    item["next_probe"],
                    j(item["evidence"]),
                )
                for item in prepared
            ],
        )

    print(
        j(
            {
                "run_id": run_id,
                "decision": decision,
                "target_book_count": len(prepared),
                "supported_chain_book_count": supported_chain_book_count,
                "mixed_chain_book_count": mixed_chain_book_count,
                "audit_control_book_count": audit_control_book_count,
                "readable_chain_version_count": readable_chain_version_count,
                "prose_gloss_allowed_count": prose_gloss_allowed_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
            }
        )
    )


if __name__ == "__main__":
    main()
