#!/usr/bin/env python3
"""Q51: classify all C86 windows into functional and audit subclasses."""

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
        CREATE TABLE IF NOT EXISTS human_q51_c86_window_taxonomy_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q40_run_id INTEGER NOT NULL,
            q46_run_id INTEGER NOT NULL,
            q50_run_id INTEGER NOT NULL,
            c86_payload_gate_run_id INTEGER NOT NULL,
            c86_subfamily_run_id INTEGER NOT NULL,
            row0_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            total_c86_book_count INTEGER NOT NULL,
            total_observation_count INTEGER NOT NULL,
            window_class_count INTEGER NOT NULL,
            ready_functional_book_count INTEGER NOT NULL,
            audit_surface_book_count INTEGER NOT NULL,
            ebfai_window_count INTEGER NOT NULL,
            eviefiin_window_count INTEGER NOT NULL,
            audit_window_count INTEGER NOT NULL,
            gloss_allowed_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            mechanism_human_version TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q51_c86_window_taxonomy_v1_books (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            c86_token_index INTEGER NOT NULL,
            window_class TEXT NOT NULL,
            payload_gate_branch_id TEXT NOT NULL,
            payload_gate_decision TEXT NOT NULL,
            payload_gate_functional_label TEXT NOT NULL,
            q36_likely_speech_act TEXT NOT NULL,
            q36_plausible_human_reading TEXT NOT NULL,
            transition_role TEXT NOT NULL,
            translation_use TEXT NOT NULL,
            blocked_claims_json TEXT NOT NULL,
            next_action TEXT NOT NULL,
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


def classify_window(right: list[str]) -> tuple[str, str]:
    if right[:5] == ["E", "B", "F", "A", "I"]:
        return "C86_EBFAI_BRANCH_WINDOW", "VINVIN/VTLR branch payload selector"
    if right[:5] == ["E", "V", "I", "E", "F"]:
        return "C86_EVIEFIIN_CONTEXT_WINDOW", "VN/C68/TIIN context payload selector"
    if right[:4] == ["E", "T", "I", "E"]:
        return "C86_ETIE_RESIDUAL_WINDOW", "residual or local surface payload"
    if right[:2] == ["E", "I"]:
        return "C86_EILTAEN_LOCAL_WINDOW", "local or surface payload"
    if right[:2] == ["E", "E"]:
        return "C86_EEN_C68_WEAK_WINDOW", "weak C68-sidecar payload"
    if right[:1] == ["F"]:
        return "C86_F_EXIT_WINDOW", "formula/display exit payload"
    if not right:
        return "TERMINAL_C86_WINDOW", "terminal or truncated C86 marker"
    return "C86_OTHER_WINDOW", "unclassified C86 payload"


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


def payload_gate_by_book(conn: sqlite3.Connection, gate_run_id: int) -> dict[str, sqlite3.Row]:
    out: dict[str, sqlite3.Row] = {}
    rows = conn.execute(
        """
        SELECT *
        FROM c86_payload_operator_gate_items
        WHERE run_id=?
        ORDER BY branch_id
        """,
        (gate_run_id,),
    ).fetchall()
    for row in rows:
        for bookid in json.loads(str(row["books_json"])):
            out[str(bookid)] = row
    return out


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q40 = latest_row(conn, "human_q40_c86_vinvin_branch_trio_atlas_v1_runs")
    q46 = latest_row(conn, "human_q46_family_synthesis_hypothesis_queue_v1_runs")
    q50 = latest_row(conn, "human_q50_c68_book_synthesis_v1_runs")
    gate = latest_row(conn, "c86_payload_operator_gate_runs")
    subfamily = latest_row(conn, "c86_subfamily_split_v1_runs")
    row0_run_id = latest_run_id(conn, "row0_variant_book_tokens")
    q36_run_id = latest_run_id(conn, "human_q36_book_contig_shadow_integration_v1_items")
    audit = latest_row(conn, "human_translation_completion_audit_v5_runs")
    gate_by_book = payload_gate_by_book(conn, int(gate["run_id"]))

    token_rows = conn.execute(
        """
        SELECT bookid, tokens_json
        FROM row0_variant_book_tokens
        WHERE run_id=? AND token_text LIKE '%C86%'
        ORDER BY CAST(bookid AS INTEGER)
        """,
        (row0_run_id,),
    ).fetchall()
    prepared = []
    for row in token_rows:
        bookid = str(row["bookid"])
        tokens = json.loads(str(row["tokens_json"]))
        positions = [index for index, token in enumerate(tokens) if token == "C86"]
        if len(positions) != 1:
            raise RuntimeError(f"expected one C86 occurrence in book {bookid}, found {len(positions)}")
        pos = positions[0]
        right = tokens[pos + 1 : pos + 9]
        window_class, role = classify_window(right)
        q36 = q36_book(conn, q36_run_id, bookid)
        gate_row = gate_by_book.get(bookid)
        if gate_row is None:
            raise RuntimeError(f"missing C86 payload gate for book {bookid}")
        ready = str(gate_row["decision"]) == "PAYLOAD_BRANCH_FUNCTION_READY_NO_GLOSS"
        prepared.append(
            {
                "bookid": bookid,
                "c86_token_index": pos,
                "left_context": tokens[max(0, pos - 6) : pos],
                "right_context": right,
                "window_class": window_class,
                "payload_gate_branch_id": str(gate_row["branch_id"]),
                "payload_gate_decision": str(gate_row["decision"]),
                "payload_gate_functional_label": str(gate_row["functional_label"]),
                "q36_likely_speech_act": str(q36["likely_speech_act"]),
                "q36_plausible_human_reading": str(q36["plausible_human_reading"]),
                "transition_role": role if ready else f"audit-only {role}",
                "translation_use": (
                    "C86 functional branch selector; no plaintext"
                    if ready
                    else "C86 audit/surface payload only; no promotion"
                ),
                "blocked_claims": [
                    "C86_as_word",
                    "branch_payload_as_plaintext",
                    "global_C86_meaning",
                    "canonical_plaintext",
                ],
                "next_action": str(gate_row["next_action"]),
                "evidence": {
                    "q36_book": dict(q36),
                    "payload_gate": dict(gate_row),
                    "left_context": tokens[max(0, pos - 6) : pos],
                    "right_context": right,
                },
            }
        )

    counts = Counter(item["window_class"] for item in prepared)
    ready_functional_book_count = sum(
        1 for item in prepared if item["payload_gate_decision"] == "PAYLOAD_BRANCH_FUNCTION_READY_NO_GLOSS"
    )
    audit_surface_book_count = len(prepared) - ready_functional_book_count
    ebfai_window_count = counts["C86_EBFAI_BRANCH_WINDOW"]
    eviefiin_window_count = counts["C86_EVIEFIIN_CONTEXT_WINDOW"]
    audit_window_count = len(prepared) - ebfai_window_count - eviefiin_window_count
    gloss_allowed_count = int(gate["gloss_allowed_count"])
    canonical_promotion_allowed_count = int(gate["lexical_promotion_allowed"])
    mechanism_human_version = (
        "C86 window taxonomy: C86 has two reusable functional payload windows, EBFAI into VINVIN/VTLR branch mechanics and EVIEFIIN into VN/C68/TIIN context mechanics. "
        "Other C86 windows remain audit/surface payloads and must not be promoted without edge support."
    )
    decision = (
        "Q51_C86_WINDOW_TAXONOMY_READY_10_FUNCTIONAL_7_AUDIT_NO_GLOSS"
        if len(prepared) == 17
        and ready_functional_book_count == 10
        and audit_surface_book_count == 7
        and ebfai_window_count == 6
        and eviefiin_window_count == 6
        and int(gate["ready_branch_count"]) == 2
        and int(subfamily["subfamily_count"]) == 2
        and int(audit["promoted_gloss_count"]) == 0
        and gloss_allowed_count == 0
        and canonical_promotion_allowed_count == 0
        else "Q51_C86_WINDOW_TAXONOMY_REQUIRES_REVIEW"
    )
    payload = {
        "question": "Can all C86 books be separated into functional branch selectors and audit payloads?",
        "answer": "Yes. Ten books have edge-supported functional C86 branch payloads, while seven stay audit/surface only.",
        "class_counts": dict(counts),
        "blocked_use": "C86 remains a branch/payload operator surface, not a lexical word.",
        "next_action": "Materialize book-level C86 functional versions analogous to Q50 C68 synthesis.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q51_c86_window_taxonomy_v1_runs (
                created_at, decision, q40_run_id, q46_run_id, q50_run_id,
                c86_payload_gate_run_id, c86_subfamily_run_id, row0_run_id,
                completion_audit_run_id, total_c86_book_count,
                total_observation_count, window_class_count,
                ready_functional_book_count, audit_surface_book_count,
                ebfai_window_count, eviefiin_window_count, audit_window_count,
                gloss_allowed_count, canonical_promotion_allowed_count,
                mechanism_human_version, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                int(q40["run_id"]),
                int(q46["run_id"]),
                int(q50["run_id"]),
                int(gate["run_id"]),
                int(subfamily["run_id"]),
                row0_run_id,
                int(audit["run_id"]),
                len(prepared),
                len(prepared),
                len(counts),
                ready_functional_book_count,
                audit_surface_book_count,
                ebfai_window_count,
                eviefiin_window_count,
                audit_window_count,
                gloss_allowed_count,
                canonical_promotion_allowed_count,
                mechanism_human_version,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q51_c86_window_taxonomy_v1_books (
                run_id, bookid, c86_token_index, window_class,
                payload_gate_branch_id, payload_gate_decision,
                payload_gate_functional_label, q36_likely_speech_act,
                q36_plausible_human_reading, transition_role,
                translation_use, blocked_claims_json, next_action,
                evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    item["bookid"],
                    item["c86_token_index"],
                    item["window_class"],
                    item["payload_gate_branch_id"],
                    item["payload_gate_decision"],
                    item["payload_gate_functional_label"],
                    item["q36_likely_speech_act"],
                    item["q36_plausible_human_reading"],
                    item["transition_role"],
                    item["translation_use"],
                    j(item["blocked_claims"]),
                    item["next_action"],
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
                "total_c86_book_count": len(prepared),
                "window_class_count": len(counts),
                "ready_functional_book_count": ready_functional_book_count,
                "audit_surface_book_count": audit_surface_book_count,
                "ebfai_window_count": ebfai_window_count,
                "eviefiin_window_count": eviefiin_window_count,
                "audit_window_count": audit_window_count,
                "gloss_allowed_count": gloss_allowed_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
            }
        )
    )


if __name__ == "__main__":
    main()
