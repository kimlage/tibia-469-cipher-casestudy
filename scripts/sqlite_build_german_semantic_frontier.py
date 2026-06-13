#!/usr/bin/env python3
"""Build a SQL-first semantic frontier for the German/MHG candidate.

The frontier ranks what to investigate next. It does not translate unknowns.
The scoring favors repeated, anchored, low-coverage, context-rich issues and
penalizes one-letter brace groups that are likely marker drift.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "bonelord_operational.sqlite"

ANCHOR_PATTERNS = [
    ("anchor_weichstein", "WEICHSTEIN", "external_anchor", 90.0, "Use oath/Weichstein context; require external or repeated local support."),
    ("anchor_orangenstrasse", "ORANGENSTRASSE", "external_anchor", 85.0, "Use place-name context; likely entity boundary."),
    ("anchor_reder_koenig", "REDER KOENIG", "entity_formula", 82.0, "Speaker-King formula; inspect adjacent unknowns."),
    ("anchor_salzberg", "SALZBERG", "entity_formula", 78.0, "Name/place formula; inspect nearby title/function words."),
    ("formula_rr_in_rh", "{RR} IN {RH}", "repeated_formula", 88.0, "Repeated low-coverage phrase; test as phrase, not individual tokens."),
    ("formula_sand_home", "SAND IM MIN HEIME", "semantic_formula", 76.0, "Sand/homeland phrase; compare all contexts before glossing."),
    ("formula_nnr_tag_nd", "NNR TAG ND", "temporal_formula", 72.0, "Temporal/ritual formula; inspect following slot."),
    ("formula_ruin_rune", "RUIN", "ritual_cluster", 68.0, "Ruin/rune cluster; inspect collocations and separators."),
    ("formula_ei_gen_hehl", "EI GEN HEHL", "legal_formula", 70.0, "Bond/concealment phrase; inspect opener and object slots."),
    ("formula_hechl", "{HECHL}", "repeated_unknown", 66.0, "Repeated closing/object unknown; test as phrase boundary."),
    ("formula_thenaeut", "THENAEUT", "opaque_token", 64.0, "Opaque repeated-looking form; test with surrounding formula."),
]

MANUAL_HIGH_VALUE = [
    {
        "focus_key": "book49_block",
        "focus_kind": "low_coverage_block",
        "priority_score": 120.0,
        "bookids": ["49"],
        "reason": "Pior livro por cobertura; oito lacunas no mesmo bloco. Tratar como possível segmentação/deslocamento.",
        "next_test": "block_level_alignment_before_token_translation",
    },
    {
        "focus_key": "book30_opening_formula",
        "focus_kind": "low_coverage_block",
        "priority_score": 108.0,
        "bookids": ["30"],
        "reason": "Abertura EUUIGL e cadeia funcional ao redor de THENAEUT; alto risco de erro se traduzir token a token.",
        "next_test": "opening_formula_alignment_and_anchor_search",
    },
    {
        "focus_key": "book55_final_nominal",
        "focus_kind": "low_coverage_block",
        "priority_score": 98.0,
        "bookids": ["55"],
        "reason": "Final ISCHASD em posição nominal; provável entidade/composto ou fórmula final.",
        "next_test": "final_nominal_context_compare",
    },
]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def jdump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def one(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> sqlite3.Row:
    row = conn.execute(sql, params).fetchone()
    if row is None:
        raise SystemExit(f"missing required row for query: {sql}")
    return row


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS german_semantic_frontier_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_canonical_run_id INTEGER NOT NULL,
            source_audit_run_id INTEGER,
            item_count INTEGER NOT NULL,
            high_priority_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS german_semantic_frontier_items (
            run_id INTEGER NOT NULL,
            priority_rank INTEGER NOT NULL,
            focus_key TEXT NOT NULL,
            focus_kind TEXT NOT NULL,
            priority_score REAL NOT NULL,
            risk TEXT NOT NULL,
            status TEXT NOT NULL,
            bookids_json TEXT NOT NULL,
            occurrence_count INTEGER NOT NULL,
            reason TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            next_test TEXT NOT NULL,
            anti_hallucination_rule TEXT NOT NULL,
            PRIMARY KEY (run_id, focus_key)
        );

        CREATE INDEX IF NOT EXISTS idx_german_semantic_frontier_rank
            ON german_semantic_frontier_items(run_id, priority_rank);
        """
    )


def excerpt(text: str, needle: str, radius: int = 80) -> str:
    idx = text.find(needle)
    if idx < 0:
        return text[: radius * 2]
    return text[max(0, idx - radius) : min(len(text), idx + len(needle) + radius)]


def braces(text: str | None) -> list[str]:
    if not text:
        return []
    return re.findall(r"\{([^{}]*)\}", text)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)

    canonical = one(conn, "SELECT * FROM canonical_candidate_runs ORDER BY run_id DESC LIMIT 1")
    audit = conn.execute("SELECT * FROM german_candidate_audit_runs ORDER BY run_id DESC LIMIT 1").fetchone()
    books = conn.execute(
        """
        SELECT *
        FROM canonical_candidate_books
        WHERE run_id=?
        ORDER BY CAST(bookid AS INTEGER)
        """,
        (canonical["run_id"],),
    ).fetchall()

    items: dict[str, dict[str, Any]] = {}

    for manual in MANUAL_HIGH_VALUE:
        key = manual["focus_key"]
        evidence = []
        for row in books:
            if str(row["bookid"]) in manual["bookids"]:
                evidence.append(
                    {
                        "bookid": str(row["bookid"]),
                        "coverage_pct": row["coverage_pct"],
                        "unknown_brace_count": row["unknown_brace_count"],
                        "decoded_excerpt": (row["decoded_primary"] or "")[:240],
                        "english_excerpt": (row["english_gloss"] or "")[:240],
                    }
                )
        items[key] = {
            **manual,
            "risk": "HIGH",
            "occurrence_count": len(evidence),
            "evidence": evidence,
            "anti": "Do not translate the block until phrase/segmentation alternatives are compared.",
        }

    for anchor_key, pattern, kind, base_score, next_test in ANCHOR_PATTERNS:
        evidence = []
        bookids = []
        for row in books:
            text = row["decoded_primary"] or ""
            if pattern in text:
                bookids.append(str(row["bookid"]))
                evidence.append(
                    {
                        "bookid": str(row["bookid"]),
                        "coverage_pct": row["coverage_pct"],
                        "unknown_brace_count": row["unknown_brace_count"],
                        "context": excerpt(text, pattern),
                        "english_context": excerpt(row["english_gloss"] or "", "{?}", 80),
                    }
                )
        if evidence:
            score = base_score + len(bookids) * 4.0
            if any((ev.get("coverage_pct") or 100) < 85 for ev in evidence):
                score += 8.0
            items[anchor_key] = {
                "focus_key": anchor_key,
                "focus_kind": kind,
                "priority_score": score,
                "bookids": bookids,
                "risk": "HIGH" if score >= 80 else "MEDIUM",
                "occurrence_count": len(bookids),
                "reason": f"Pattern `{pattern}` appears in candidate text and can constrain adjacent unknowns.",
                "evidence": evidence[:10],
                "next_test": next_test,
                "anti": "Only promote a gloss if supported by repeated context or external anchor evidence.",
            }

    if audit:
        unknown_rows = conn.execute(
            """
            SELECT *
            FROM german_candidate_unknown_group_items
            WHERE run_id=?
            ORDER BY priority_score DESC, occurrence_count DESC
            """,
            (audit["run_id"],),
        ).fetchall()
        for row in unknown_rows:
            group = row["unknown_group"]
            if len(group) <= 1:
                score = float(row["priority_score"]) * 0.20
                risk = "LOW_MARKER_DRIFT"
                anti = "Do not translate one-letter markers as words without a mechanical explanation."
            else:
                score = float(row["priority_score"])
                risk = "HIGH" if score >= 60 else "MEDIUM"
                anti = "Resolve as phrase/entity first; no free English gloss without anchor."
            key = f"unknown_{group}"
            if key in items:
                items[key]["priority_score"] = max(items[key]["priority_score"], score)
                continue
            items[key] = {
                "focus_key": key,
                "focus_kind": "unknown_group",
                "priority_score": score,
                "bookids": json.loads(row["bookids_json"]),
                "risk": risk,
                "occurrence_count": int(row["occurrence_count"]),
                "reason": f"Unknown group `{group}` occurs {row['occurrence_count']} time(s).",
                "evidence": json.loads(row["sample_context_json"]),
                "next_test": row["next_test"],
                "anti": anti,
            }

    ranked = sorted(items.values(), key=lambda x: (-float(x["priority_score"]), x["focus_key"]))
    cur = conn.execute(
        """
        INSERT INTO german_semantic_frontier_runs
            (created_at, source_canonical_run_id, source_audit_run_id,
             item_count, high_priority_count, payload_json)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            utc_now(),
            canonical["run_id"],
            audit["run_id"] if audit else None,
            len(ranked),
            sum(1 for item in ranked if item["risk"] == "HIGH"),
            jdump({"ranking": "anchor/repetition/low-coverage first; one-letter marker drift penalized"}),
        ),
    )
    run_id = int(cur.lastrowid)

    for idx, item in enumerate(ranked, start=1):
        conn.execute(
            """
            INSERT INTO german_semantic_frontier_items
                (run_id, priority_rank, focus_key, focus_kind, priority_score,
                 risk, status, bookids_json, occurrence_count, reason,
                 evidence_json, next_test, anti_hallucination_rule)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                idx,
                item["focus_key"],
                item["focus_kind"],
                float(item["priority_score"]),
                item["risk"],
                "OPEN",
                jdump(item["bookids"]),
                int(item["occurrence_count"]),
                item["reason"],
                jdump(item["evidence"]),
                item["next_test"],
                item["anti"],
            ),
        )
    conn.commit()

    print(
        json.dumps(
            {
                "frontier_run_id": run_id,
                "source_canonical_run_id": int(canonical["run_id"]),
                "source_audit_run_id": int(audit["run_id"]) if audit else None,
                "item_count": len(ranked),
                "high_priority_count": sum(1 for item in ranked if item["risk"] == "HIGH"),
                "top_items": [
                    {
                        "rank": idx,
                        "focus_key": item["focus_key"],
                        "kind": item["focus_kind"],
                        "score": round(float(item["priority_score"]), 2),
                        "risk": item["risk"],
                        "bookids": item["bookids"],
                    }
                    for idx, item in enumerate(ranked[:15], start=1)
                ],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
