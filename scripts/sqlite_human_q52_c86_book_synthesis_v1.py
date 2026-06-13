#!/usr/bin/env python3
"""Q52: synthesize book-level human readings for all C86 books."""

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
        CREATE TABLE IF NOT EXISTS human_q52_c86_book_synthesis_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q51_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            target_book_count INTEGER NOT NULL,
            profile_count INTEGER NOT NULL,
            ready_functional_book_count INTEGER NOT NULL,
            audit_surface_book_count INTEGER NOT NULL,
            readable_functional_version_count INTEGER NOT NULL,
            prose_gloss_allowed_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q52_c86_book_synthesis_v1_books (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            c86_profile TEXT NOT NULL,
            q51_window_class TEXT NOT NULL,
            payload_gate_decision TEXT NOT NULL,
            q36_likely_speech_act TEXT NOT NULL,
            q36_plausible_human_reading TEXT NOT NULL,
            c86_functional_version TEXT NOT NULL,
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


def profile_for(row: sqlite3.Row) -> str:
    window = str(row["window_class"])
    decision = str(row["payload_gate_decision"])
    ready = decision == "PAYLOAD_BRANCH_FUNCTION_READY_NO_GLOSS"
    if ready and window == "C86_EBFAI_BRANCH_WINDOW":
        return "C86_READY_VINVIN_VTLR_BRANCH"
    if ready and window == "C86_EVIEFIIN_CONTEXT_WINDOW":
        return "C86_READY_VN_C68_TIIN_CONTEXT"
    if window == "C86_EBFAI_BRANCH_WINDOW":
        return "C86_EBFAI_SURFACE_AUDIT"
    if window == "C86_EVIEFIIN_CONTEXT_WINDOW":
        return "C86_EVIEFIIN_SURFACE_AUDIT"
    if window == "C86_ETIE_RESIDUAL_WINDOW":
        return "C86_ETIE_RESIDUAL_AUDIT"
    if window == "C86_EILTAEN_LOCAL_WINDOW":
        return "C86_EILTAEN_LOCAL_AUDIT"
    if window == "C86_EEN_C68_WEAK_WINDOW":
        return "C86_EEN_C68_WEAK_AUDIT"
    if window == "C86_F_EXIT_WINDOW":
        return "C86_F_EXIT_AUDIT"
    if window == "TERMINAL_C86_WINDOW":
        return "C86_TERMINAL_AUDIT"
    return "C86_COMPLEX_AUDIT"


def profile_version(profile: str, row: sqlite3.Row) -> tuple[str, str, str]:
    bookid = str(row["bookid"])
    base = str(row["q36_plausible_human_reading"])
    if profile == "C86_READY_VINVIN_VTLR_BRANCH":
        return (
            f"Book {bookid}: {base} C86 opens an EBFAI branch into VINVIN/VTLR/R20 mechanics; use as branch payload selector, not prose.",
            "human functional C86 branch-selector version; no plaintext",
            "Compare against exact VINVIN/VTLR branch packets before any promotion package.",
        )
    if profile == "C86_READY_VN_C68_TIIN_CONTEXT":
        return (
            f"Book {bookid}: {base} C86 opens an EVIEFIIN branch into VN/C68/TIIN context mechanics; use as context payload selector, not prose.",
            "human functional C86 context-selector version; no plaintext",
            "Compare against Q50 C68 phase/context profiles and the 67->2 bridge.",
        )
    if profile == "C86_EBFAI_SURFACE_AUDIT":
        return (
            f"Book {bookid}: {base} C86 has the EBFAI branch surface but lacks enough edge support, so it remains a surface/audit witness.",
            "C86 audit-only branch surface; no promotion",
            "Require edge support before treating this as VINVIN/VTLR branch payload.",
        )
    if profile == "C86_EVIEFIIN_SURFACE_AUDIT":
        return (
            f"Book {bookid}: {base} C86 has the EVIEFIIN context surface but lacks enough edge support, so it remains a weak/audit bridge.",
            "C86 audit-only context surface; no promotion",
            "Require boundary support before linking this to VN/C68/TIIN context.",
        )
    if profile == "C86_ETIE_RESIDUAL_AUDIT":
        return (
            f"Book {bookid}: {base} C86 opens an ETIE residual payload surface; keep it as local residual evidence.",
            "C86 residual audit surface; no promotion",
            "Do not use as branch selector without a matching edge or repeated family.",
        )
    if profile == "C86_EILTAEN_LOCAL_AUDIT":
        return (
            f"Book {bookid}: {base} C86 opens an EILTAEN local payload surface; keep it as local phase-context residue.",
            "C86 local audit surface; no promotion",
            "Compare with Q39 phase-context controls before any synthesis.",
        )
    if profile == "C86_EEN_C68_WEAK_AUDIT":
        return (
            f"Book {bookid}: {base} C86 opens a weak EEN-C68 sidecar surface; keep it as sidecar audit material.",
            "C86 weak C68-sidecar audit surface; no promotion",
            "Use only as a negative/weak control for C86->C68 routing.",
        )
    if profile == "C86_F_EXIT_AUDIT":
        return (
            f"Book {bookid}: {base} C86 opens an F-exit payload surface tied to display/formula material.",
            "C86 formula/display exit audit surface; no promotion",
            "Compare with display-drift masks before prose synthesis.",
        )
    if profile == "C86_TERMINAL_AUDIT":
        return (
            f"Book {bookid}: {base} C86 is terminal or truncated, marking an evidence limit rather than a translated ending.",
            "C86 terminal audit surface; no promotion",
            "Keep terminal C86 quarantined until a source bridge explains terminal placement.",
        )
    return (
        f"Book {bookid}: {base} C86 has a complex audit profile and cannot be synthesized beyond structural role.",
        "C86 complex audit only",
        "Inspect manually.",
    )


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q51 = latest_row(conn, "human_q51_c86_window_taxonomy_v1_runs")
    audit = latest_row(conn, "human_translation_completion_audit_v5_runs")
    q51_rows = list(
        conn.execute(
            """
            SELECT *
            FROM human_q51_c86_window_taxonomy_v1_books
            WHERE run_id=?
            ORDER BY CAST(bookid AS INTEGER)
            """,
            (int(q51["run_id"]),),
        )
    )
    if not q51_rows:
        raise RuntimeError("missing Q51 C86 books")

    prepared = []
    for row in q51_rows:
        profile = profile_for(row)
        version, translation_use, next_probe = profile_version(profile, row)
        prepared.append(
            {
                "bookid": str(row["bookid"]),
                "c86_profile": profile,
                "q51_window_class": str(row["window_class"]),
                "payload_gate_decision": str(row["payload_gate_decision"]),
                "q36_likely_speech_act": str(row["q36_likely_speech_act"]),
                "q36_plausible_human_reading": str(row["q36_plausible_human_reading"]),
                "c86_functional_version": version,
                "translation_use": translation_use,
                "blocked_claims": [
                    "C86_as_word",
                    "payload_as_sentence",
                    "global_C86_meaning",
                    "canonical_plaintext",
                ],
                "next_probe": next_probe,
                "evidence": {"q51_book": dict(row)},
            }
        )

    profile_counts = Counter(item["c86_profile"] for item in prepared)
    ready_functional_book_count = sum(
        1 for item in prepared if item["payload_gate_decision"] == "PAYLOAD_BRANCH_FUNCTION_READY_NO_GLOSS"
    )
    audit_surface_book_count = len(prepared) - ready_functional_book_count
    readable_functional_version_count = len([item for item in prepared if item["c86_functional_version"]])
    prose_gloss_allowed_count = 0
    canonical_promotion_allowed_count = 0
    decision = (
        "Q52_C86_BOOK_SYNTHESIS_READY_FUNCTIONAL_NO_GLOSS"
        if int(q51["total_c86_book_count"]) == len(prepared) == 17
        and ready_functional_book_count == int(q51["ready_functional_book_count"]) == 10
        and audit_surface_book_count == int(q51["audit_surface_book_count"]) == 7
        and readable_functional_version_count == 17
        and int(audit["promoted_gloss_count"]) == 0
        and prose_gloss_allowed_count == 0
        and canonical_promotion_allowed_count == 0
        else "Q52_C86_BOOK_SYNTHESIS_REQUIRES_REVIEW"
    )
    payload = {
        "question": "Can Q51 produce usable human functional versions for all C86 books?",
        "answer": "Yes. Ten books get edge-supported C86 branch/context selector readings, while seven remain audit-only surfaces.",
        "profile_counts": dict(profile_counts),
        "blocked_use": "This is a human functional layer, not canonical translation.",
        "next_action": "Use C86 and C68 syntheses together to test full branch-to-context-to-slot chains.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q52_c86_book_synthesis_v1_runs (
                created_at, decision, q51_run_id, completion_audit_run_id,
                target_book_count, profile_count, ready_functional_book_count,
                audit_surface_book_count, readable_functional_version_count,
                prose_gloss_allowed_count, canonical_promotion_allowed_count,
                payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                int(q51["run_id"]),
                int(audit["run_id"]),
                len(prepared),
                len(profile_counts),
                ready_functional_book_count,
                audit_surface_book_count,
                readable_functional_version_count,
                prose_gloss_allowed_count,
                canonical_promotion_allowed_count,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q52_c86_book_synthesis_v1_books (
                run_id, bookid, c86_profile, q51_window_class,
                payload_gate_decision, q36_likely_speech_act,
                q36_plausible_human_reading, c86_functional_version,
                translation_use, blocked_claims_json, next_probe,
                evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    item["bookid"],
                    item["c86_profile"],
                    item["q51_window_class"],
                    item["payload_gate_decision"],
                    item["q36_likely_speech_act"],
                    item["q36_plausible_human_reading"],
                    item["c86_functional_version"],
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
                "profile_count": len(profile_counts),
                "ready_functional_book_count": ready_functional_book_count,
                "audit_surface_book_count": audit_surface_book_count,
                "readable_functional_version_count": readable_functional_version_count,
                "prose_gloss_allowed_count": prose_gloss_allowed_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
            }
        )
    )


if __name__ == "__main__":
    main()
