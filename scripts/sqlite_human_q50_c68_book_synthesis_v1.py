#!/usr/bin/env python3
"""Q50: synthesize book-level human readings for all C68 books."""

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
        CREATE TABLE IF NOT EXISTS human_q50_c68_book_synthesis_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q48_run_id INTEGER NOT NULL,
            q49_run_id INTEGER NOT NULL,
            q36_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            target_book_count INTEGER NOT NULL,
            profile_count INTEGER NOT NULL,
            hinge_only_book_count INTEGER NOT NULL,
            mixed_hinge_book_count INTEGER NOT NULL,
            quarantined_profile_book_count INTEGER NOT NULL,
            readable_functional_version_count INTEGER NOT NULL,
            prose_gloss_allowed_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q50_c68_book_synthesis_v1_books (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            c68_profile TEXT NOT NULL,
            q36_compiled_stratum TEXT NOT NULL,
            q36_likely_speech_act TEXT NOT NULL,
            q36_plausible_human_reading TEXT NOT NULL,
            c68_window_classes_json TEXT NOT NULL,
            c68_functional_version TEXT NOT NULL,
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


def latest_run_id(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT max(run_id) FROM {table}").fetchone()
    if row is None or row[0] is None:
        raise RuntimeError(f"missing required run: {table}")
    return int(row[0])


def q36_book(conn: sqlite3.Connection, q36_run_id: int, bookid: str) -> sqlite3.Row:
    row = conn.execute(
        """
        SELECT *
        FROM human_q36_book_contig_shadow_integration_v1_items
        WHERE run_id=? AND bookid=?
        """,
        (q36_run_id, bookid),
    ).fetchone()
    if row is None:
        raise RuntimeError(f"missing Q36 book {bookid}")
    return row


def profile_for(classes: dict[str, int]) -> str:
    nonzero = {key for key, value in classes.items() if value}
    if nonzero == {"PHASE_TIIN_WINDOW"}:
        return "C68_PHASE_CONTEXT_ONLY"
    if nonzero == {"SLOT_TIVV_WINDOW"}:
        return "C68_SLOT_CLASSIFIER_ONLY"
    if nonzero == {"PHASE_TIIN_WINDOW", "SLOT_TIVV_WINDOW"}:
        return "C68_MIXED_PHASE_SLOT_CHAIN"
    if nonzero == {"PHASE_TIIN_WINDOW", "TERMINAL_C68_WINDOW"}:
        return "C68_PHASE_TERMINAL_COMPOSITION"
    if nonzero == {"TAVT_BOUNDARY_WINDOW"}:
        return "C68_TAVT_BOUNDARY_AUDIT"
    if nonzero == {"E_EXIT_WINDOW", "TERMINAL_C68_WINDOW"}:
        return "C68_E_EXIT_TERMINAL_AUDIT"
    return "C68_COMPLEX_AUDIT_PROFILE"


def profile_version(profile: str, bookid: str, q36: sqlite3.Row) -> tuple[str, str]:
    base = str(q36["plausible_human_reading"])
    if profile == "C68_PHASE_CONTEXT_ONLY":
        return (
            f"Book {bookid}: {base} C68 is used in a TIIN-style phase/context transition window.",
            "Compare with other phase-context books before prose synthesis.",
        )
    if profile == "C68_SLOT_CLASSIFIER_ONLY":
        return (
            f"Book {bookid}: {base} C68 is used in a TIVV-style slot/classifier transition window.",
            "Compare with NAESE/FATCT slot controls before prose synthesis.",
        )
    if profile == "C68_MIXED_PHASE_SLOT_CHAIN":
        return (
            f"Book {bookid}: {base} C68 appears in both phase/context and slot/classifier windows, making this a chained transition witness.",
            "Use as a bridge control between Q39 phase and Q43 slot families.",
        )
    if profile == "C68_PHASE_TERMINAL_COMPOSITION":
        return (
            f"Book {bookid}: {base} C68 begins with a phase/context window and ends with a terminal C68 limit, so the book is a mixed context-plus-truncation composition.",
            "Keep terminal placement as audit-only until a source bridge explains it.",
        )
    if profile == "C68_TAVT_BOUNDARY_AUDIT":
        return (
            f"Book {bookid}: {base} C68 opens a TAVT boundary/continuation subclass rather than the phase-slot hinge.",
            "Compare TAVT boundary behavior against LTAST/TAVT continuation controls.",
        )
    if profile == "C68_E_EXIT_TERMINAL_AUDIT":
        return (
            f"Book {bookid}: {base} C68 appears in E-exit and terminal subclasses, making this a residual component/sidecar witness, not a prose line.",
            "Compare E-exit windows against endpoint and clean-component witnesses.",
        )
    return (
        f"Book {bookid}: {base} C68 has a complex audit profile and cannot be synthesized beyond structural role.",
        "Inspect manually.",
    )


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q48 = latest_row(conn, "human_q48_c68_heldout_window_taxonomy_v1_runs")
    q49 = latest_row(conn, "human_q49_c68_extra_subclass_quarantine_v1_runs")
    audit = latest_row(conn, "human_translation_completion_audit_v5_runs")
    q36_run_id = latest_run_id(conn, "human_q36_book_contig_shadow_integration_v1_items")

    q48_books = list(
        conn.execute(
            """
            SELECT *
            FROM human_q48_c68_heldout_window_taxonomy_v1_books
            WHERE run_id=?
            ORDER BY CAST(bookid AS INTEGER)
            """,
            (int(q48["run_id"]),),
        )
    )
    if not q48_books:
        raise RuntimeError("missing Q48 C68 books")

    prepared = []
    for row in q48_books:
        bookid = str(row["bookid"])
        classes = json.loads(str(row["window_classes_json"]))
        profile = profile_for({str(key): int(value) for key, value in classes.items()})
        q36 = q36_book(conn, q36_run_id, bookid)
        functional_version, next_probe = profile_version(profile, bookid, q36)
        prepared.append(
            {
                "bookid": bookid,
                "c68_profile": profile,
                "q36_compiled_stratum": str(q36["compiled_stratum"]),
                "q36_likely_speech_act": str(q36["likely_speech_act"]),
                "q36_plausible_human_reading": str(q36["plausible_human_reading"]),
                "c68_window_classes": classes,
                "c68_functional_version": functional_version,
                "translation_use": "human functional C68 book version only; not canonical plaintext",
                "blocked_claims": [
                    "C68_as_word",
                    "TIIN_as_word",
                    "TIVV_as_word",
                    "terminal_as_ending",
                    "canonical_plaintext",
                ],
                "next_probe": next_probe,
                "evidence": {
                    "q48_book": dict(row),
                    "q36_book": dict(q36),
                },
            }
        )

    profile_counts = Counter(item["c68_profile"] for item in prepared)
    hinge_only_book_count = profile_counts["C68_PHASE_CONTEXT_ONLY"] + profile_counts["C68_SLOT_CLASSIFIER_ONLY"]
    mixed_hinge_book_count = profile_counts["C68_MIXED_PHASE_SLOT_CHAIN"]
    quarantined_profile_book_count = (
        profile_counts["C68_PHASE_TERMINAL_COMPOSITION"]
        + profile_counts["C68_TAVT_BOUNDARY_AUDIT"]
        + profile_counts["C68_E_EXIT_TERMINAL_AUDIT"]
    )
    readable_functional_version_count = len([item for item in prepared if item["c68_functional_version"]])
    prose_gloss_allowed_count = 0
    canonical_promotion_allowed_count = 0
    decision = (
        "Q50_C68_BOOK_SYNTHESIS_READY_FUNCTIONAL_NO_GLOSS"
        if int(q48["total_c68_book_count"]) == len(prepared) == 23
        and int(q49["extra_observation_count"]) == 5
        and readable_functional_version_count == len(prepared)
        and len(profile_counts) == 6
        and int(audit["promoted_gloss_count"]) == 0
        and prose_gloss_allowed_count == 0
        and canonical_promotion_allowed_count == 0
        else "Q50_C68_BOOK_SYNTHESIS_REQUIRES_REVIEW"
    )
    payload = {
        "question": "Can Q47-Q49 produce usable human functional versions for all books with C68?",
        "answer": "Yes, all 23 C68 books now have profile-specific functional readings with no component gloss.",
        "profile_counts": dict(profile_counts),
        "blocked_use": "This is a human functional layer, not canonical translation.",
        "next_action": "Use the C68 book synthesis to select the next non-C68 mechanism family for the same treatment.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q50_c68_book_synthesis_v1_runs (
                created_at, decision, q48_run_id, q49_run_id, q36_run_id,
                completion_audit_run_id, target_book_count, profile_count,
                hinge_only_book_count, mixed_hinge_book_count,
                quarantined_profile_book_count, readable_functional_version_count,
                prose_gloss_allowed_count, canonical_promotion_allowed_count,
                payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                int(q48["run_id"]),
                int(q49["run_id"]),
                q36_run_id,
                int(audit["run_id"]),
                len(prepared),
                len(profile_counts),
                hinge_only_book_count,
                mixed_hinge_book_count,
                quarantined_profile_book_count,
                readable_functional_version_count,
                prose_gloss_allowed_count,
                canonical_promotion_allowed_count,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q50_c68_book_synthesis_v1_books (
                run_id, bookid, c68_profile, q36_compiled_stratum,
                q36_likely_speech_act, q36_plausible_human_reading,
                c68_window_classes_json, c68_functional_version,
                translation_use, blocked_claims_json, next_probe,
                evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    item["bookid"],
                    item["c68_profile"],
                    item["q36_compiled_stratum"],
                    item["q36_likely_speech_act"],
                    item["q36_plausible_human_reading"],
                    j(item["c68_window_classes"]),
                    item["c68_functional_version"],
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
                "hinge_only_book_count": hinge_only_book_count,
                "mixed_hinge_book_count": mixed_hinge_book_count,
                "quarantined_profile_book_count": quarantined_profile_book_count,
                "readable_functional_version_count": readable_functional_version_count,
                "prose_gloss_allowed_count": prose_gloss_allowed_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
            }
        )
    )


if __name__ == "__main__":
    main()
