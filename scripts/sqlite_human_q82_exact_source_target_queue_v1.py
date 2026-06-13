#!/usr/bin/env python3
"""Q82: build exact-source target queue from Q81 promotion-review rows."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

TARGET_META = {
    "B_C86_VNCTIIN_PAYLOAD_CORRIDOR": {
        "priority": "CRITICAL",
        "target_family": "C86_VNCTIIN_PAYLOAD_CORRIDOR",
        "search_question": "Can any in-game source bind C86/VNCTIIN-bearing sequences to a specific payload/context meaning?",
        "key_terms": ["CEVIEFIINI", "VNCTIIN", "TAILBETFTE", "NAESE"],
        "source_strategy": "Search exact C86/VNCTIIN strings around Threat I/II/III, Hellgate, Chayenne/Knightmare/Avar leads, and book pages.",
    },
    "B_BENNA_C86_VNCTIIN_FORMULA_HANDOFF": {
        "priority": "CRITICAL",
        "target_family": "BENNA_C86_VNCTIIN_FORMULA_HANDOFF",
        "search_question": "Can a source prove BENNA formula handoff into C86/VNCTIIN context rather than only structural routing?",
        "key_terms": ["BENNA", "LTAST", "TAILBETFTE", "VNCTIIN"],
        "source_strategy": "Search exact BENNA/LTAST/TAILBETFTE handoff strings against Mathemagica, Honeminas/formula, Paradox, and numeric book references.",
    },
    "B_NAESE_BENNA_COMPOSITE": {
        "priority": "HIGH",
        "target_family": "NAESE_BENNA_COMPOSITE",
        "search_question": "Can any exact source distinguish NAESE/C68 slot material flowing into BENNA formula body?",
        "key_terms": ["NAESE", "FATCT", "IVIFAST", "BENNA"],
        "source_strategy": "Search exact NAESE/BENNA composite strings and contrast against clean NAESE slot and BENNA formula controls.",
    },
    "B_R02_NAESE_SLOT_BRIDGE": {
        "priority": "HIGH",
        "target_family": "R02_NAESE_SLOT_BRIDGE",
        "search_question": "Can any source bind R02 phase bridge into NAESE/C68 slot mechanics?",
        "key_terms": ["ANIVVENINTEIN", "NAESE", "FATCT", "IVIFAST"],
        "source_strategy": "Search exact R02/NAESE bridge substrings and compare Books 51/53 against 45/46 and Book14 controls.",
    },
    "B_BOOK7_PHASE_MATHEMAGIC": {
        "priority": "MEDIUM",
        "target_family": "BOOK7_PHASE_MATHEMAGIC",
        "search_question": "Can Mathemagica or Paradox prove the Book7 phase continuation/handoff rule?",
        "key_terms": ["TIINNEF", "NEIAAETTA", "PARADOX"],
        "source_strategy": "Search exact Book7-family phase strings and test them against mathemagic operator references.",
    },
    "B_BOOK49_MATH49_REGISTER": {
        "priority": "MEDIUM",
        "target_family": "BOOK49_MATH49_REGISTER",
        "search_question": "Can the self-contained Book49 repeat shape be tied to a real in-game 49/math operator?",
        "key_terms": ["IAEN", "NEEN", "49", "PARADOX"],
        "source_strategy": "Search exact repeat fragments and +49/mod70 relations against Paradox and numeric-language references.",
    },
    "B_BOOK54_PAIR_LOCAL_SPINE": {
        "priority": "MEDIUM",
        "target_family": "BOOK54_PAIR_LOCAL_SPINE",
        "search_question": "Can the Book54 local-pair spine be confirmed outside its local alignment with Book20?",
        "key_terms": ["FLTFNTFEIFAIFAINIIETNEEIVNALN", "zero", "pair"],
        "source_strategy": "Search exact Book54 string and compare against zero-boundary/local-pair contexts.",
    },
    "B_CHAYENNE_FRAME_REGISTER": {
        "priority": "MEDIUM_EXTERNAL_FRAME_RISK",
        "target_family": "CHAYENNE_FRAME_REGISTER",
        "search_question": "Can Chayenne-frame books be anchored inside game relationships rather than external register shape only?",
        "key_terms": ["VNCTIIN", "LTAST", "CHAYENNE", "KNIGHTMARE", "AVAR"],
        "source_strategy": "Search exact Chayenne-frame strings, then require in-game provenance before promotion.",
    },
}

PRIORITY_ORDER = {
    "CRITICAL": 1,
    "HIGH": 2,
    "MEDIUM": 3,
    "MEDIUM_EXTERNAL_FRAME_RISK": 4,
}


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q82_exact_source_target_queue_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q81_run_id INTEGER NOT NULL,
            contradiction_audit_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            promotion_review_book_count INTEGER NOT NULL,
            target_family_count INTEGER NOT NULL,
            critical_target_count INTEGER NOT NULL,
            high_target_count INTEGER NOT NULL,
            medium_target_count INTEGER NOT NULL,
            external_frame_risk_target_count INTEGER NOT NULL,
            exact_source_hit_count INTEGER NOT NULL,
            lexical_ready_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            queue_human_version TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q82_exact_source_target_queue_v1_targets (
            run_id INTEGER NOT NULL,
            target_id TEXT NOT NULL,
            source_bridge_id TEXT NOT NULL,
            priority TEXT NOT NULL,
            priority_rank INTEGER NOT NULL,
            target_family TEXT NOT NULL,
            book_count INTEGER NOT NULL,
            books_json TEXT NOT NULL,
            key_terms_json TEXT NOT NULL,
            exemplar_sequences_json TEXT NOT NULL,
            search_question TEXT NOT NULL,
            source_strategy TEXT NOT NULL,
            acceptance_gate TEXT NOT NULL,
            rejection_rule TEXT NOT NULL,
            target_status TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, target_id)
        );

        CREATE TABLE IF NOT EXISTS human_q82_exact_source_target_queue_v1_books (
            run_id INTEGER NOT NULL,
            target_id TEXT NOT NULL,
            bookid TEXT NOT NULL,
            likely_speech_act TEXT NOT NULL,
            plausible_human_reading TEXT NOT NULL,
            confidence_tier TEXT NOT NULL,
            symbol_text TEXT NOT NULL,
            falsifier TEXT NOT NULL,
            next_probe TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, target_id, bookid)
        );
        """
    )


def latest_row(conn: sqlite3.Connection, table: str) -> sqlite3.Row:
    row = conn.execute(f"SELECT * FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    if row is None:
        raise RuntimeError(f"missing required row: {table}")
    return row


def load_review_rows(conn: sqlite3.Connection, audit_run_id: int, q81_run_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT
            audit.bookid,
            audit.source_bridge_id,
            audit.confidence_tier,
            audit.reason,
            audit.next_action AS audit_next_action,
            export.likely_speech_act,
            export.plausible_human_reading,
            export.falsifier,
            export.next_probe,
            row0.symbol_text
        FROM human_atlas_v6_contradiction_audit_v1_items AS audit
        JOIN human_q81_controlled_shadow_export_v1_items AS export
            ON export.bookid = audit.bookid
            AND export.run_id = ?
        JOIN row0_variant_book_tokens AS row0
            ON row0.bookid = audit.bookid
            AND row0.run_id = (SELECT max(run_id) FROM row0_variant_book_tokens)
        WHERE audit.run_id=?
            AND audit.promotion_review_candidate=1
        ORDER BY audit.source_bridge_id, CAST(audit.bookid AS INTEGER)
        """,
        (q81_run_id, audit_run_id),
    ).fetchall()


def grouped(rows: list[sqlite3.Row]) -> dict[str, list[sqlite3.Row]]:
    groups: dict[str, list[sqlite3.Row]] = {}
    for row in rows:
        groups.setdefault(str(row["source_bridge_id"]), []).append(row)
    return groups


def exemplar_sequences(rows: list[sqlite3.Row]) -> list[dict[str, str]]:
    exemplars = []
    for row in rows[:3]:
        symbol_text = str(row["symbol_text"])
        exemplars.append(
            {
                "bookid": str(row["bookid"]),
                "symbol_prefix": symbol_text[:120],
                "symbol_length": str(len(symbol_text)),
            }
        )
    return exemplars


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q81 = latest_row(conn, "human_q81_controlled_shadow_export_v1_runs")
    contradiction = latest_row(conn, "human_atlas_v6_contradiction_audit_v1_runs")
    completion = latest_row(conn, "human_translation_completion_audit_v5_runs")

    review_rows = load_review_rows(conn, int(contradiction["run_id"]), int(q81["run_id"]))
    groups = grouped(review_rows)
    missing_meta = sorted(set(groups) - set(TARGET_META))
    if missing_meta:
        raise RuntimeError(f"missing target metadata for source bridges: {missing_meta}")

    target_rows = []
    book_rows = []
    for source_bridge_id, rows in groups.items():
        meta = TARGET_META[source_bridge_id]
        priority = meta["priority"]
        target_id = f"Q82_T{len(target_rows) + 1:02d}_{meta['target_family']}"
        books = [str(row["bookid"]) for row in rows]
        target = {
            "target_id": target_id,
            "source_bridge_id": source_bridge_id,
            "priority": priority,
            "priority_rank": PRIORITY_ORDER[priority],
            "target_family": meta["target_family"],
            "book_count": len(rows),
            "books": books,
            "key_terms": meta["key_terms"],
            "exemplar_sequences": exemplar_sequences(rows),
            "search_question": meta["search_question"],
            "source_strategy": meta["source_strategy"],
            "acceptance_gate": (
                "Accept only if an in-game or official/primary source gives the exact sequence, "
                "its provenance, a meaning or mechanically forced value, and failed controls."
            ),
            "rejection_rule": (
                "Reject register-only lore, external-only shape matches, and any plausible prose "
                "that lacks exact sequence-plus-meaning evidence."
            ),
            "target_status": "QUEUED_EXACT_SOURCE_REQUIRED_NO_PROMOTION",
            "evidence": {
                "books": [dict(row) for row in rows],
                "q81_decision": str(q81["decision"]),
                "completion_decision": str(completion["decision"]),
            },
        }
        target_rows.append(target)
        for row in rows:
            book_rows.append(
                {
                    "target_id": target_id,
                    "bookid": str(row["bookid"]),
                    "likely_speech_act": str(row["likely_speech_act"]),
                    "plausible_human_reading": str(row["plausible_human_reading"]),
                    "confidence_tier": str(row["confidence_tier"]),
                    "symbol_text": str(row["symbol_text"]),
                    "falsifier": str(row["falsifier"]),
                    "next_probe": str(row["next_probe"]),
                    "evidence": dict(row),
                }
            )

    target_rows.sort(key=lambda row: (int(row["priority_rank"]), row["target_family"]))
    for idx, row in enumerate(target_rows, start=1):
        old_id = row["target_id"]
        new_id = f"Q82_T{idx:02d}_{row['target_family']}"
        row["target_id"] = new_id
        for book in book_rows:
            if book["target_id"] == old_id:
                book["target_id"] = new_id

    promotion_review_book_count = len(review_rows)
    target_family_count = len(target_rows)
    critical_target_count = sum(1 for row in target_rows if row["priority"] == "CRITICAL")
    high_target_count = sum(1 for row in target_rows if row["priority"] == "HIGH")
    medium_target_count = sum(1 for row in target_rows if row["priority"] == "MEDIUM")
    external_frame_risk_target_count = sum(1 for row in target_rows if row["priority"] == "MEDIUM_EXTERNAL_FRAME_RISK")
    exact_source_hit_count = 0
    lexical_ready_count = 0
    canonical_promotion_allowed_count = 0
    queue_human_version = (
        "Q82 queues eight exact-source target families from the 15 promotion-review shadow rows. "
        "The queue prioritizes Q80 packet families first, then composite/slot bridges, then medium-risk controls."
    )
    decision = (
        "Q82_EXACT_SOURCE_TARGET_QUEUE_READY_8_FAMILIES_15_BOOKS_NO_PROMOTION"
        if promotion_review_book_count == 15
        and target_family_count == 8
        and critical_target_count == 2
        and high_target_count == 2
        and medium_target_count == 3
        and external_frame_risk_target_count == 1
        and int(completion["promoted_gloss_count"]) == 0
        else "Q82_EXACT_SOURCE_TARGET_QUEUE_REQUIRES_REVIEW"
    )
    payload = {
        "question": "Which human-shadow families should be searched next for exact in-game source evidence?",
        "answer": queue_human_version,
        "blocked_use": "Queued targets are not lexical promotions.",
        "next_action": "Execute CRITICAL targets first: C86/VNCTIIN payload corridor and BENNA->C86/VNCTIIN handoff.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q82_exact_source_target_queue_v1_runs (
                created_at, decision, q81_run_id, contradiction_audit_run_id,
                completion_audit_run_id, promotion_review_book_count,
                target_family_count, critical_target_count, high_target_count,
                medium_target_count, external_frame_risk_target_count,
                exact_source_hit_count, lexical_ready_count,
                canonical_promotion_allowed_count, queue_human_version,
                payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                int(q81["run_id"]),
                int(contradiction["run_id"]),
                int(completion["run_id"]),
                promotion_review_book_count,
                target_family_count,
                critical_target_count,
                high_target_count,
                medium_target_count,
                external_frame_risk_target_count,
                exact_source_hit_count,
                lexical_ready_count,
                canonical_promotion_allowed_count,
                queue_human_version,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q82_exact_source_target_queue_v1_targets (
                run_id, target_id, source_bridge_id, priority, priority_rank,
                target_family, book_count, books_json, key_terms_json,
                exemplar_sequences_json, search_question, source_strategy,
                acceptance_gate, rejection_rule, target_status, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    row["target_id"],
                    row["source_bridge_id"],
                    row["priority"],
                    row["priority_rank"],
                    row["target_family"],
                    row["book_count"],
                    j(row["books"]),
                    j(row["key_terms"]),
                    j(row["exemplar_sequences"]),
                    row["search_question"],
                    row["source_strategy"],
                    row["acceptance_gate"],
                    row["rejection_rule"],
                    row["target_status"],
                    j(row["evidence"]),
                )
                for row in target_rows
            ],
        )
        conn.executemany(
            """
            INSERT INTO human_q82_exact_source_target_queue_v1_books (
                run_id, target_id, bookid, likely_speech_act,
                plausible_human_reading, confidence_tier, symbol_text,
                falsifier, next_probe, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    row["target_id"],
                    row["bookid"],
                    row["likely_speech_act"],
                    row["plausible_human_reading"],
                    row["confidence_tier"],
                    row["symbol_text"],
                    row["falsifier"],
                    row["next_probe"],
                    j(row["evidence"]),
                )
                for row in book_rows
            ],
        )

    print(
        j(
            {
                "run_id": run_id,
                "decision": decision,
                "promotion_review_book_count": promotion_review_book_count,
                "target_family_count": target_family_count,
                "critical_target_count": critical_target_count,
                "high_target_count": high_target_count,
                "medium_target_count": medium_target_count,
                "external_frame_risk_target_count": external_frame_risk_target_count,
                "exact_source_hit_count": exact_source_hit_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
            }
        )
    )


if __name__ == "__main__":
    main()
