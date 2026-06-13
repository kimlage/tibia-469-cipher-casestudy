#!/usr/bin/env python3
"""Score contig overlap residuals after masking known formula spans."""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "bonelord_operational.sqlite"
TARGET_EDGES = {("0", 1), ("1", 1), ("1", 2), ("1", 3), ("4", 1)}
PARTIAL_FORMULAS = ["CEVIEFIINI"]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def jdump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS overlap_formula_holdout_probe_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_contig_overlap_run_id INTEGER NOT NULL,
            source_formula_mask_run_id INTEGER NOT NULL,
            edge_count INTEGER NOT NULL,
            avg_holdout_score REAL NOT NULL,
            alive_strong_count INTEGER NOT NULL,
            alive_weak_count INTEGER NOT NULL,
            audit_only_count INTEGER NOT NULL,
            dead_or_formula_count INTEGER NOT NULL,
            decision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS overlap_formula_holdout_edge_items (
            run_id INTEGER NOT NULL,
            edge_id TEXT NOT NULL,
            basecontigid TEXT NOT NULL,
            edge_index INTEGER NOT NULL,
            left_bookid TEXT NOT NULL,
            right_bookid TEXT NOT NULL,
            overlap_symbols INTEGER NOT NULL,
            formula_mask_count INTEGER NOT NULL,
            masked_char_count INTEGER NOT NULL,
            residual_char_count INTEGER NOT NULL,
            residual_spans_json TEXT NOT NULL,
            policy_flags_json TEXT NOT NULL,
            residual_recall REAL NOT NULL,
            boundary_consistency REAL NOT NULL,
            policy_cleanliness REAL NOT NULL,
            cross_edge_concordance REAL NOT NULL,
            length_penalty_inverse REAL NOT NULL,
            holdout_score REAL NOT NULL,
            classification TEXT NOT NULL,
            masked_overlap TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, edge_id)
        );
        """
    )


def latest_id(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT run_id FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    if row is None:
        raise SystemExit(f"missing required table data: {table}")
    return int(row["run_id"])


def apply_masks(text: str, masks: list[sqlite3.Row]) -> tuple[str, list[dict[str, Any]]]:
    chars = list(text)
    hits: list[dict[str, Any]] = []
    for mask in sorted(masks, key=lambda row: int(row["segment_len"]), reverse=True):
        segment = mask["segment"]
        start = 0
        while True:
            pos = text.find(segment, start)
            if pos < 0:
                break
            end = pos + len(segment)
            if any(ch == "#" for ch in chars[pos:end]):
                start = pos + 1
                continue
            for idx in range(pos, end):
                chars[idx] = "#"
            hits.append({"mask_id": mask["mask_id"], "segment": segment, "start": pos + 1, "end": end, "len": len(segment)})
            start = pos + 1
    for partial in PARTIAL_FORMULAS:
        start = 0
        while True:
            pos = text.find(partial, start)
            if pos < 0:
                break
            end = pos + len(partial)
            if not any(ch == "#" for ch in chars[pos:end]):
                for idx in range(pos, end):
                    chars[idx] = "#"
                hits.append({"mask_id": "<PARTIAL>", "segment": partial, "start": pos + 1, "end": end, "len": len(partial)})
            start = pos + 1
    return "".join(chars), hits


def residual_spans(masked: str) -> list[dict[str, Any]]:
    spans = []
    idx = 0
    while idx < len(masked):
        while idx < len(masked) and masked[idx] == "#":
            idx += 1
        start = idx
        while idx < len(masked) and masked[idx] != "#":
            idx += 1
        if idx > start:
            text = masked[start:idx]
            clean = text.replace("*", "")
            if clean:
                spans.append({"start": start + 1, "end": idx, "text": text, "len": len(text)})
    return spans


def ngrams(text: str, n: int = 6) -> set[str]:
    clean = text.replace("*", "")
    if len(clean) < n:
        return {clean} if clean else set()
    return {clean[idx : idx + n] for idx in range(len(clean) - n + 1)}


def classify(score: float) -> str:
    if score >= 0.80:
        return "ALIVE_STRONG"
    if score >= 0.60:
        return "ALIVE_WEAK"
    if score >= 0.40:
        return "AUDIT_ONLY"
    return "DEAD_OR_FORMULA_ONLY"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)

    contig_run_id = latest_id(conn, "contig_max_overlap_probe_runs")
    mask_run_id = latest_id(conn, "formula_mask_probe_runs")
    masks = conn.execute(
        """
        SELECT *
        FROM formula_mask_segments
        WHERE run_id=?
        ORDER BY segment_len DESC
        """,
        (mask_run_id,),
    ).fetchall()
    edges = conn.execute(
        """
        SELECT *
        FROM contig_max_overlap_edges
        WHERE run_id=?
        ORDER BY CAST(basecontigid AS INTEGER), edge_index
        """,
        (contig_run_id,),
    ).fetchall()
    targets = [row for row in edges if (str(row["basecontigid"]), int(row["edge_index"])) in TARGET_EDGES]

    precomputed = []
    for row in targets:
        masked, mask_hits = apply_masks(row["overlap_text"] or "", masks)
        spans = residual_spans(masked)
        grams = set()
        for span in spans:
            grams |= ngrams(span["text"])
        flags = []
        if "*" in (row["overlap_text"] or ""):
            flags.append("STAR_00_STRUCTURAL_VETO")
        if any(hit["mask_id"] == "<F02>" for hit in mask_hits):
            flags.append("LTAST_FORMULA_MASKED")
        if any(hit["mask_id"] == "<F01>" for hit in mask_hits):
            flags.append("NAESE_FORMULA_MASKED")
        if any(hit["mask_id"] == "<F05>" or hit["mask_id"] == "<PARTIAL>" for hit in mask_hits):
            flags.append("ICE_PARTIAL_FORMULA_MASKED")
        precomputed.append({"row": row, "masked": masked, "mask_hits": mask_hits, "spans": spans, "ngrams": grams, "flags": flags})

    cur = conn.execute(
        """
        INSERT INTO overlap_formula_holdout_probe_runs
            (created_at, source_contig_overlap_run_id, source_formula_mask_run_id,
             edge_count, avg_holdout_score, alive_strong_count, alive_weak_count,
             audit_only_count, dead_or_formula_count, decision, payload_json)
        VALUES (?, ?, ?, ?, 0, 0, 0, 0, 0, ?, ?)
        """,
        (utc_now(), contig_run_id, mask_run_id, len(precomputed), "PENDING", "{}"),
    )
    run_id = int(cur.lastrowid)

    scores = []
    class_counts = {"ALIVE_STRONG": 0, "ALIVE_WEAK": 0, "AUDIT_ONLY": 0, "DEAD_OR_FORMULA_ONLY": 0}
    for item in precomputed:
        row = item["row"]
        other_ngrams = set()
        for other in precomputed:
            if other is not item:
                other_ngrams |= other["ngrams"]
        own = item["ngrams"]
        shared = own & other_ngrams
        residual_len = sum(span["len"] for span in item["spans"])
        overlap_len = len(row["overlap_text"] or "")
        residual_recall = len(shared) / max(1, len(own))
        boundary_consistency = 1.0 if item["spans"] and not any(span["text"].startswith("*") or span["text"].endswith("*") for span in item["spans"]) else 0.5
        policy_cleanliness = 1.0 if item["mask_hits"] else 0.75
        cross_edge_concordance = len(shared) / max(1, len(own))
        length_penalty_inverse = min(1.0, residual_len / 12.0)
        score = (
            0.35 * residual_recall
            + 0.25 * boundary_consistency
            + 0.20 * policy_cleanliness
            + 0.15 * cross_edge_concordance
            + 0.05 * length_penalty_inverse
        )
        classification = classify(score)
        class_counts[classification] += 1
        scores.append(score)
        masked_char_count = sum(hit["len"] for hit in item["mask_hits"])
        edge_id = f"{row['basecontigid']}:{row['edge_index']}:{row['left_bookid']}->{row['right_bookid']}"
        conn.execute(
            """
            INSERT INTO overlap_formula_holdout_edge_items
                (run_id, edge_id, basecontigid, edge_index, left_bookid, right_bookid,
                 overlap_symbols, formula_mask_count, masked_char_count,
                 residual_char_count, residual_spans_json, policy_flags_json,
                 residual_recall, boundary_consistency, policy_cleanliness,
                 cross_edge_concordance, length_penalty_inverse, holdout_score,
                 classification, masked_overlap, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                edge_id,
                str(row["basecontigid"]),
                int(row["edge_index"]),
                str(row["left_bookid"]),
                str(row["right_bookid"]),
                int(row["overlap_symbols"]),
                len(item["mask_hits"]),
                masked_char_count,
                residual_len,
                jdump(item["spans"]),
                jdump(item["flags"]),
                residual_recall,
                boundary_consistency,
                policy_cleanliness,
                cross_edge_concordance,
                length_penalty_inverse,
                score,
                classification,
                item["masked"],
                jdump({"mask_hits": item["mask_hits"], "shared_ngram_count": len(shared), "own_ngram_count": len(own), "overlap_len": overlap_len}),
            ),
        )

    avg_score = sum(scores) / max(1, len(scores))
    decision = "OVERLAP_HOLDOUT_RESIDUALS_ALIVE" if class_counts["ALIVE_STRONG"] or class_counts["ALIVE_WEAK"] else "OVERLAP_HOLDOUT_FORMULA_DOMINATED"
    conn.execute(
        """
        UPDATE overlap_formula_holdout_probe_runs
        SET avg_holdout_score=?,
            alive_strong_count=?,
            alive_weak_count=?,
            audit_only_count=?,
            dead_or_formula_count=?,
            decision=?,
            payload_json=?
        WHERE run_id=?
        """,
        (
            avg_score,
            class_counts["ALIVE_STRONG"],
            class_counts["ALIVE_WEAK"],
            class_counts["AUDIT_ONLY"],
            class_counts["DEAD_OR_FORMULA_ONLY"],
            decision,
            jdump({"class_counts": class_counts, "gloss_allowed": False}),
            run_id,
        ),
    )
    conn.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "edge_count": len(precomputed),
                "avg_holdout_score": round(avg_score, 4),
                "class_counts": class_counts,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
