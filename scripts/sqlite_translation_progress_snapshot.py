#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import UTC, datetime
from typing import Any, Dict

from sqlite_snapshot_ref import DEFAULT_SNAPSHOT_NAME, resolve_export_id


DEFAULT_DB = "./data/bonelord_operational.sqlite"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compute a conservative translation progress snapshot from SQLite audit tables")
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--export-id", type=int, default=None)
    parser.add_argument("--snapshot-name", default=DEFAULT_SNAPSHOT_NAME)
    parser.add_argument("--record", action="store_true")
    return parser.parse_args()


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def flow_state(conn: sqlite3.Connection, export_id: int) -> Dict[str, str]:
    rows = conn.execute(
        "SELECT key, value FROM sheet__flowstate WHERE __export_id = ?",
        (export_id,),
    ).fetchall()
    return {str(row["key"]): str(row["value"]) for row in rows if row["key"] is not None}


def scalar(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> int:
    try:
        row = conn.execute(sql, params).fetchone()
        return int(row[0] or 0) if row else 0
    except sqlite3.OperationalError:
        return 0


def pct(value: float) -> float:
    return round(max(0.0, min(100.0, value)), 2)


def latest_macro_violation_count(conn: sqlite3.Connection) -> int:
    row = conn.execute(
        """
        SELECT violation_count
        FROM macro_consistency_audit_runs
        ORDER BY run_id DESC
        LIMIT 1
        """
    ).fetchone()
    return int(row[0] or 0) if row else 0


def latest_macro_recomposition(conn: sqlite3.Connection) -> Dict[str, int]:
    try:
        row = conn.execute(
            """
            SELECT macro_count, changed_count, missing_component_count
            FROM macro_recomposition_audit_runs
            ORDER BY run_id DESC
            LIMIT 1
            """
        ).fetchone()
    except sqlite3.OperationalError:
        row = None
    if not row:
        return {"macro_count": 0, "changed_count": 0, "missing_component_count": 0}
    return {
        "macro_count": int(row["macro_count"] or 0),
        "changed_count": int(row["changed_count"] or 0),
        "missing_component_count": int(row["missing_component_count"] or 0),
    }


def latest_external_phrase_anchors(conn: sqlite3.Connection) -> Dict[str, int]:
    try:
        row = conn.execute(
            """
            SELECT anchor_count, mismatch_count
            FROM external_phrase_anchor_audit_runs
            ORDER BY run_id DESC
            LIMIT 1
            """
        ).fetchone()
    except sqlite3.OperationalError:
        row = None
    if not row:
        return {"anchor_count": 0, "mismatch_count": 0}
    return {
        "anchor_count": int(row["anchor_count"] or 0),
        "mismatch_count": int(row["mismatch_count"] or 0),
    }


def latest_rosetta_wordcode_search(conn: sqlite3.Connection) -> Dict[str, Any]:
    try:
        row = conn.execute(
            """
            SELECT
                anchor_count,
                phrase_count,
                book_segment_occurrences,
                book_phrase_occurrences,
                external_segment_occurrences,
                external_phrase_occurrences,
                source_hit_occurrences,
                candidate_occurrences,
                mode_evidence_pct,
                conclusion
            FROM rosetta_wordcode_search_runs
            ORDER BY run_id DESC
            LIMIT 1
            """
        ).fetchone()
    except sqlite3.OperationalError:
        row = None
    if not row:
        return {
            "anchor_count": 0,
            "phrase_count": 0,
            "book_segment_occurrences": 0,
            "book_phrase_occurrences": 0,
            "external_segment_occurrences": 0,
            "external_phrase_occurrences": 0,
            "source_hit_occurrences": 0,
            "candidate_occurrences": 0,
            "mode_evidence_pct": 0.0,
            "conclusion": "NOT_RUN",
        }
    return {
        "anchor_count": int(row["anchor_count"] or 0),
        "phrase_count": int(row["phrase_count"] or 0),
        "book_segment_occurrences": int(row["book_segment_occurrences"] or 0),
        "book_phrase_occurrences": int(row["book_phrase_occurrences"] or 0),
        "external_segment_occurrences": int(row["external_segment_occurrences"] or 0),
        "external_phrase_occurrences": int(row["external_phrase_occurrences"] or 0),
        "source_hit_occurrences": int(row["source_hit_occurrences"] or 0),
        "candidate_occurrences": int(row["candidate_occurrences"] or 0),
        "mode_evidence_pct": float(row["mode_evidence_pct"] or 0),
        "conclusion": str(row["conclusion"] or ""),
    }


def latest_stability_gate(conn: sqlite3.Connection) -> Dict[str, Any]:
    try:
        row = conn.execute(
            """
            SELECT item_count, blocked_count, caution_count, allow_count, stability_gate_pct
            FROM translation_stability_gate_runs
            ORDER BY run_id DESC
            LIMIT 1
            """
        ).fetchone()
    except sqlite3.OperationalError:
        row = None
    if not row:
        return {
            "item_count": 0,
            "blocked_count": 0,
            "caution_count": 0,
            "allow_count": 0,
            "stability_gate_pct": 100.0,
        }
    return {
        "item_count": int(row["item_count"] or 0),
        "blocked_count": int(row["blocked_count"] or 0),
        "caution_count": int(row["caution_count"] or 0),
        "allow_count": int(row["allow_count"] or 0),
        "stability_gate_pct": float(row["stability_gate_pct"] or 0),
    }


def latest_safe_books(conn: sqlite3.Connection) -> Dict[str, Any]:
    try:
        row = conn.execute(
            """
            SELECT book_count, books_with_blocked, books_with_caution,
                   blocked_hit_count, caution_hit_count, safe_book_clean_pct
            FROM safe_book_translation_runs
            ORDER BY run_id DESC
            LIMIT 1
            """
        ).fetchone()
    except sqlite3.OperationalError:
        row = None
    if not row:
        return {
            "book_count": 0,
            "books_with_blocked": 0,
            "books_with_caution": 0,
            "blocked_hit_count": 0,
            "caution_hit_count": 0,
            "safe_book_clean_pct": 0.0,
        }
    return {
        "book_count": int(row["book_count"] or 0),
        "books_with_blocked": int(row["books_with_blocked"] or 0),
        "books_with_caution": int(row["books_with_caution"] or 0),
        "blocked_hit_count": int(row["blocked_hit_count"] or 0),
        "caution_hit_count": int(row["caution_hit_count"] or 0),
        "safe_book_clean_pct": float(row["safe_book_clean_pct"] or 0),
    }


def latest_npc_wordcode(conn: sqlite3.Connection) -> Dict[str, Any]:
    try:
        row = conn.execute(
            """
            SELECT payload_json
            FROM npc_wordcode_runs
            ORDER BY run_id DESC
            LIMIT 1
            """
        ).fetchone()
    except sqlite3.OperationalError:
        row = None
    if not row:
        return {
            "phrase_count": 0,
            "word_anchor_count": 0,
            "frontier_count": 0,
            "hard_external_word_anchors": 0,
            "soft_external_word_anchors": 0,
            "book_promotion_allowed": 0,
            "quarantine_ok_pct": 0.0,
        }
    try:
        payload = json.loads(str(row["payload_json"] or "{}"))
    except json.JSONDecodeError:
        payload = {}
    word_count = int(payload.get("word_anchor_count") or 0)
    book_allowed = int(payload.get("book_promotion_allowed") or 0)
    quarantine_ok = pct(100.0 * (word_count - book_allowed) / word_count) if word_count else 0.0
    return {
        "phrase_count": int(payload.get("phrase_count") or 0),
        "word_anchor_count": word_count,
        "frontier_count": int(payload.get("frontier_count") or 0),
        "hard_external_word_anchors": int(payload.get("hard_external_word_anchors") or 0),
        "soft_external_word_anchors": int(payload.get("soft_external_word_anchors") or 0),
        "book_promotion_allowed": book_allowed,
        "quarantine_ok_pct": quarantine_ok,
    }


def latest_unknown_surface(conn: sqlite3.Connection) -> Dict[str, Any]:
    try:
        row = conn.execute(
            """
            SELECT unknown_surface_count
            FROM unknown_surface_rank_runs
            ORDER BY run_id DESC
            LIMIT 1
            """
        ).fetchone()
    except sqlite3.OperationalError:
        row = None
    if not row:
        return {"unknown_surface_count": 0, "top_hit_count": 0, "top_book_count": 0}
    top = None
    try:
        top = conn.execute(
            """
            SELECT hit_count, book_count
            FROM unknown_surface_rank_items
            WHERE run_id = (SELECT max(run_id) FROM unknown_surface_rank_runs)
            ORDER BY rank
            LIMIT 1
            """
        ).fetchone()
    except sqlite3.OperationalError:
        top = None
    return {
        "unknown_surface_count": int(row["unknown_surface_count"] or 0),
        "top_hit_count": int(top["hit_count"] or 0) if top else 0,
        "top_book_count": int(top["book_count"] or 0) if top else 0,
    }


def compute(conn: sqlite3.Connection, export_id: int) -> Dict[str, Any]:
    state = flow_state(conn, export_id)
    gt_bad_enforced = int(float(state.get("GTBadEnforcedCount", "0") or 0))
    gt_bad_all = int(float(state.get("GTBadAllCount", "0") or 0))
    soft = int(float(state.get("GTSoftMismatchCount", "0") or 0))
    status = state.get("Status", "")
    mechanical = 100.0 if gt_bad_enforced == 0 and gt_bad_all == 0 and soft == 0 and status != "BLOCKED" else 0.0

    book_total = scalar(conn, "SELECT COUNT(*) FROM translation_audit_books WHERE export_id = ?", (export_id,))
    book_flagged = scalar(conn, "SELECT COUNT(*) FROM translation_audit_books WHERE export_id = ? AND risk_score > 0", (export_id,))
    book_high_risk = scalar(conn, "SELECT COUNT(*) FROM translation_audit_books WHERE export_id = ? AND risk_score >= 6", (export_id,))
    book_clean = pct(100.0 * (book_total - book_flagged) / book_total) if book_total else 0.0
    book_high_risk_free = pct(100.0 * (book_total - book_high_risk) / book_total) if book_total else 0.0

    glossary_total = scalar(conn, "SELECT COUNT(*) FROM translation_audit_glossary WHERE export_id = ?", (export_id,))
    glossary_flagged = scalar(conn, "SELECT COUNT(*) FROM translation_audit_glossary WHERE export_id = ? AND risk_score > 0", (export_id,))
    glossary_changed = scalar(conn, "SELECT COUNT(*) FROM translation_audit_glossary WHERE export_id = ? AND original_translation != audited_translation", (export_id,))
    glossary_clean = pct(100.0 * (glossary_total - glossary_flagged) / glossary_total) if glossary_total else 0.0

    macro_violations = latest_macro_violation_count(conn)
    macro_consistency = pct(100.0 - macro_violations)
    recomposition = latest_macro_recomposition(conn)
    macro_recomposition_clean = (
        pct(100.0 * (recomposition["macro_count"] - recomposition["changed_count"]) / recomposition["macro_count"])
        if recomposition["macro_count"]
        else 0.0
    )
    external_phrase = latest_external_phrase_anchors(conn)
    external_phrase_anchor_pass = (
        pct(100.0 * (external_phrase["anchor_count"] - external_phrase["mismatch_count"]) / external_phrase["anchor_count"])
        if external_phrase["anchor_count"]
        else 0.0
    )
    rosetta_wordcode = latest_rosetta_wordcode_search(conn)
    stability_gate = latest_stability_gate(conn)
    safe_books = latest_safe_books(conn)
    npc_wordcode = latest_npc_wordcode(conn)
    unknown_surface = latest_unknown_surface(conn)

    reliable_read_confidence = pct(
        0.10 * mechanical
        + 0.17 * book_clean
        + 0.06 * book_high_risk_free
        + 0.12 * glossary_clean
        + 0.10 * macro_consistency
        + 0.13 * macro_recomposition_clean
        + 0.12 * external_phrase_anchor_pass
        + 0.12 * stability_gate["stability_gate_pct"]
        + 0.18 * safe_books["safe_book_clean_pct"]
    )

    return {
        "export_id": export_id,
        "iteration": state.get("CurrentIteration"),
        "status": status,
        "mechanical_convergence_pct": pct(mechanical),
        "book_clean_pct": book_clean,
        "book_high_risk_free_pct": book_high_risk_free,
        "glossary_clean_pct": glossary_clean,
        "macro_consistency_pct": macro_consistency,
        "macro_recomposition_clean_pct": macro_recomposition_clean,
        "external_phrase_anchor_pass_pct": external_phrase_anchor_pass,
        "rosetta_wordcode_mode_evidence_pct": pct(rosetta_wordcode["mode_evidence_pct"]),
        "rosetta_wordcode_conclusion": rosetta_wordcode["conclusion"],
        "translation_stability_gate_pct": pct(stability_gate["stability_gate_pct"]),
        "safe_book_clean_pct": pct(safe_books["safe_book_clean_pct"]),
        "npc_wordcode_quarantine_ok_pct": pct(npc_wordcode["quarantine_ok_pct"]),
        "reliable_read_confidence_pct": reliable_read_confidence,
        "counts": {
            "books_total": book_total,
            "books_flagged": book_flagged,
            "books_high_risk": book_high_risk,
            "glossary_total": glossary_total,
            "glossary_flagged": glossary_flagged,
            "glossary_changed_by_audit": glossary_changed,
            "macro_consistency_violations": macro_violations,
            "macro_recomposition_total": recomposition["macro_count"],
            "macro_recomposition_changed": recomposition["changed_count"],
            "macro_recomposition_missing_components": recomposition["missing_component_count"],
            "external_phrase_anchor_count": external_phrase["anchor_count"],
            "external_phrase_anchor_mismatch": external_phrase["mismatch_count"],
            "rosetta_wordcode_anchor_count": rosetta_wordcode["anchor_count"],
            "rosetta_wordcode_phrase_count": rosetta_wordcode["phrase_count"],
            "rosetta_wordcode_book_segment_occurrences": rosetta_wordcode["book_segment_occurrences"],
            "rosetta_wordcode_book_phrase_occurrences": rosetta_wordcode["book_phrase_occurrences"],
            "rosetta_wordcode_external_segment_occurrences": rosetta_wordcode["external_segment_occurrences"],
            "rosetta_wordcode_external_phrase_occurrences": rosetta_wordcode["external_phrase_occurrences"],
            "rosetta_wordcode_source_hit_occurrences": rosetta_wordcode["source_hit_occurrences"],
            "rosetta_wordcode_candidate_occurrences": rosetta_wordcode["candidate_occurrences"],
            "stability_gate_item_count": stability_gate["item_count"],
            "stability_gate_blocked_count": stability_gate["blocked_count"],
            "stability_gate_caution_count": stability_gate["caution_count"],
            "stability_gate_allow_count": stability_gate["allow_count"],
            "safe_book_count": safe_books["book_count"],
            "safe_books_with_blocked": safe_books["books_with_blocked"],
            "safe_books_with_caution": safe_books["books_with_caution"],
            "safe_book_blocked_hit_count": safe_books["blocked_hit_count"],
            "safe_book_caution_hit_count": safe_books["caution_hit_count"],
            "npc_phrase_anchor_count": npc_wordcode["phrase_count"],
            "npc_word_anchor_count": npc_wordcode["word_anchor_count"],
            "npc_frontier_count": npc_wordcode["frontier_count"],
            "npc_hard_external_word_anchors": npc_wordcode["hard_external_word_anchors"],
            "npc_soft_external_word_anchors": npc_wordcode["soft_external_word_anchors"],
            "npc_book_promotion_allowed": npc_wordcode["book_promotion_allowed"],
            "unknown_surface_count": unknown_surface["unknown_surface_count"],
            "unknown_surface_top_hit_count": unknown_surface["top_hit_count"],
            "unknown_surface_top_book_count": unknown_surface["top_book_count"],
            "gt_bad_enforced": gt_bad_enforced,
            "gt_bad_all": gt_bad_all,
            "gt_soft": soft,
        },
        "interpretation": "Conservative reliability metric: mechanical green is not treated as solved if semantic audit and macro consistency still flag unstable text.",
    }


def record(conn: sqlite3.Connection, snapshot: Dict[str, Any]) -> int:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS translation_progress_snapshots (
            progress_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            export_id INTEGER NOT NULL,
            reliable_read_confidence_pct REAL NOT NULL,
            mechanical_convergence_pct REAL NOT NULL,
            payload_json TEXT NOT NULL
        );
        """
    )
    created_at = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    cur = conn.execute(
        """
        INSERT INTO translation_progress_snapshots (
            created_at, export_id, reliable_read_confidence_pct, mechanical_convergence_pct, payload_json
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (
            created_at,
            snapshot["export_id"],
            snapshot["reliable_read_confidence_pct"],
            snapshot["mechanical_convergence_pct"],
            json.dumps(snapshot, ensure_ascii=True, sort_keys=True),
        ),
    )
    conn.commit()
    return int(cur.lastrowid)


def main() -> int:
    args = parse_args()
    conn = connect(args.db)
    try:
        export_id = resolve_export_id(conn, export_id=args.export_id, snapshot_name=args.snapshot_name)
        snapshot = compute(conn, export_id)
        progress_id = record(conn, snapshot) if args.record else None
    finally:
        conn.close()
    snapshot["recorded_progress_id"] = progress_id
    print(json.dumps(snapshot, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
