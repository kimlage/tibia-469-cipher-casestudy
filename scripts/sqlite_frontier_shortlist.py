#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from sqlite_frontier_precheck import cross_sheet_hits, latest_export_id
from sqlite_dead_branch_rules import matching_dead_rules
from sqlite_probe_registry import init_schema as init_probe_registry_schema
from sqlite_snapshot_ref import DEFAULT_SNAPSHOT_NAME


DEFAULT_DB = "./data/bonelord_operational.sqlite"


@dataclass
class Candidate:
    family: str
    search: str
    source: str
    source_key: str
    source_label: str
    bookcount: int = 0
    totalocc: int = 0
    inbooks_count: int = 0
    length: int = 0
    evidence: str = ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SQLite-first shortlist generator")
    parser.add_argument("--db", default=DEFAULT_DB, help="SQLite snapshot DB")
    parser.add_argument("--export-id", type=int, default=None, help="Specific snapshot export_id")
    parser.add_argument("--snapshot-name", default=DEFAULT_SNAPSHOT_NAME, help="Named snapshot ref to use")
    parser.add_argument("--top", type=int, default=5, help="How many candidates to print")
    parser.add_argument("--pool", type=int, default=40, help="How many raw candidates to score per source")
    parser.add_argument("--min-len", type=int, default=8, help="Minimum token length to consider")
    parser.add_argument("--min-bookcount", type=int, default=2, help="Minimum Books footprint for glossary candidates")
    parser.add_argument("--min-totalocc", type=int, default=2, help="Minimum occurrence count for glossary candidates")
    parser.add_argument("--min-inbooks", type=int, default=2, help="Minimum in-books count for external candidates")
    return parser.parse_args()


def normalize_slug(text: str, fallback: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "_", (text or "").strip().lower())
    value = re.sub(r"_+", "_", value).strip("_")
    if not value:
        value = fallback
    if value[0].isdigit():
        value = f"c_{value}"
    return value[:80]


def int_or_zero(value: Any) -> int:
    try:
        return int(value)
    except Exception:
        return 0


def probe_history(conn: sqlite3.Connection, family: str, search: str) -> Dict[str, Any]:
    needle = f"%{search.lower()}%"
    rows = conn.execute(
        """
        SELECT
            COUNT(*) AS runs,
            SUM(CASE WHEN outcome = 'DP_UNUSED' THEN 1 ELSE 0 END) AS dp_unused,
            SUM(CASE WHEN outcome = 'GT_HARD_FAIL' THEN 1 ELSE 0 END) AS gt_hard_fail,
            SUM(CASE WHEN outcome = 'NO_OP' THEN 1 ELSE 0 END) AS no_op,
            MAX(created_at) AS last_seen,
            MAX(outcome) AS last_outcome
        FROM probe_runs
        WHERE lower(family) = lower(?)
           OR lower(probe_name) LIKE ?
           OR lower(reason_selected) LIKE ?
           OR lower(notes) LIKE ?
        """,
        (family, needle, needle, needle),
    ).fetchone()
    runs = int(rows["runs"] or 0) if rows else 0
    dp_unused = int(rows["dp_unused"] or 0) if rows else 0
    gt_hard_fail = int(rows["gt_hard_fail"] or 0) if rows else 0
    no_op = int(rows["no_op"] or 0) if rows else 0
    known_dead = matching_dead_rules((family, search))
    dead = dp_unused >= 2 or gt_hard_fail >= 2 or no_op >= 2 or bool(known_dead)
    return {
        "runs": runs,
        "dp_unused": dp_unused,
        "gt_hard_fail": gt_hard_fail,
        "no_op": no_op,
        "last_seen": rows["last_seen"] if rows else None,
        "last_outcome": rows["last_outcome"] if rows else None,
        "known_dead_rules": [rule.label for rule in known_dead],
        "dead": dead,
    }


def latest_macro_consistency_penalties(conn: sqlite3.Connection) -> Dict[str, Dict[str, Any]]:
    try:
        row = conn.execute(
            """
            SELECT run_id
            FROM macro_consistency_audit_runs
            ORDER BY run_id DESC
            LIMIT 1
            """
        ).fetchone()
        if row is None:
            return {}
        rows = conn.execute(
            """
            SELECT base_token, severity, reason, recommended_action
            FROM macro_consistency_violations
            WHERE run_id = ?
            """,
            (row["run_id"],),
        ).fetchall()
    except sqlite3.OperationalError:
        return {}
    return {
        str(item["base_token"]): {
            "severity": int(item["severity"] or 0),
            "reason": item["reason"],
            "recommended_action": item["recommended_action"],
        }
        for item in rows
    }


def latest_macro_recomposition_changes(conn: sqlite3.Connection) -> Dict[str, Dict[str, Any]]:
    try:
        row = conn.execute(
            """
            SELECT run_id
            FROM macro_recomposition_audit_runs
            ORDER BY run_id DESC
            LIMIT 1
            """
        ).fetchone()
        if row is None:
            return {}
        rows = conn.execute(
            """
            SELECT token, original_translation, audited_recomposed_translation
            FROM macro_recomposition_audit
            WHERE run_id = ?
              AND changed = 1
            """,
            (row["run_id"],),
        ).fetchall()
    except sqlite3.OperationalError:
        return {}
    return {
        str(item["token"]): {
            "original_translation": item["original_translation"],
            "audited_recomposed_translation": item["audited_recomposed_translation"],
        }
        for item in rows
    }


def macro_penalty_for_token(token: str, macro_penalties: Dict[str, Dict[str, Any]]) -> Dict[str, Any] | None:
    normalized_token = token.lstrip("*")
    matches = [
        (base, penalty)
        for base, penalty in macro_penalties.items()
        if token == base
        or normalized_token == base
        or (len(base) >= 5 and (token.startswith(base) or normalized_token.startswith(base) or token.startswith("*" + base)))
    ]
    if not matches:
        return None
    base, penalty = max(matches, key=lambda item: len(item[0]))
    out = dict(penalty)
    out["matched_base_token"] = base
    return out


def recomposition_change_for_token(token: str, recomposition_changes: Dict[str, Dict[str, Any]]) -> Dict[str, Any] | None:
    if token in recomposition_changes:
        return recomposition_changes[token]
    normalized_token = token.lstrip("*")
    if normalized_token in recomposition_changes:
        return recomposition_changes[normalized_token]
    return None


def candidate_pool_glossary(
    conn: sqlite3.Connection,
    export_id: int,
    min_len: int,
    min_bookcount: int,
    min_totalocc: int,
    pool: int,
) -> List[Candidate]:
    rows = conn.execute(
        """
        SELECT
            token,
            translation,
            totalocc,
            bookcount,
            contigcount,
            evidenceclass_v127,
            evidencesources_v127
        FROM sheet__glossary
        WHERE __export_id = ?
          AND length(coalesce(token, '')) >= ?
          AND CAST(coalesce(bookcount, 0) AS INTEGER) >= ?
          AND CAST(coalesce(totalocc, 0) AS INTEGER) >= ?
        ORDER BY CAST(coalesce(bookcount, 0) AS INTEGER) DESC,
                 CAST(coalesce(totalocc, 0) AS INTEGER) DESC,
                 length(coalesce(token, '')) DESC
        LIMIT ?
        """,
        (export_id, min_len, min_bookcount, min_totalocc, pool),
    ).fetchall()
    out: List[Candidate] = []
    for row in rows:
        token = str(row["token"] or "").strip()
        if not token:
            continue
        out.append(
            Candidate(
                family=f"glossary_{normalize_slug(token, 'token')}",
                search=token,
                source="glossary",
                source_key=token,
                source_label=token,
                bookcount=int_or_zero(row["bookcount"]),
                totalocc=int_or_zero(row["totalocc"]),
                length=len(token),
                evidence=str(row["evidenceclass_v127"] or ""),
            )
        )
    return out


def candidate_pool_external(
    conn: sqlite3.Connection,
    export_id: int,
    min_len: int,
    min_inbooks: int,
    pool: int,
) -> List[Candidate]:
    rows = conn.execute(
        """
        SELECT
            refname,
            decodedbase,
            inbooks_count,
            source,
            type
        FROM sheet__externalrefs_v115
        WHERE __export_id = ?
          AND length(coalesce(decodedbase, '')) >= ?
          AND CAST(coalesce(inbooks_count, 0) AS INTEGER) >= ?
        ORDER BY CAST(coalesce(inbooks_count, 0) AS INTEGER) DESC,
                 length(coalesce(decodedbase, '')) DESC
        LIMIT ?
        """,
        (export_id, min_len, min_inbooks, pool),
    ).fetchall()
    out: List[Candidate] = []
    for row in rows:
        decoded = str(row["decodedbase"] or "").strip()
        refname = str(row["refname"] or "").strip()
        if not decoded or not refname:
            continue
        out.append(
            Candidate(
                family=f"external_{normalize_slug(refname, 'ref')}",
                search=decoded,
                source="externalrefs_v115",
                source_key=refname,
                source_label=refname,
                inbooks_count=int_or_zero(row["inbooks_count"]),
                length=len(decoded),
                evidence=str(row["type"] or ""),
            )
        )
    return out


def score_candidate(
    conn: sqlite3.Connection,
    export_id: int,
    cand: Candidate,
    macro_penalties: Dict[str, Dict[str, Any]],
    recomposition_changes: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    history = probe_history(conn, cand.family, cand.search)
    if history["known_dead_rules"]:
        hits = {"books": [], "contigs": [], "glossary": [], "externalrefs_v115": []}
    else:
        hits = cross_sheet_hits(conn, export_id, cand.search, limit=20)
    book_hits = len(hits.get("books", []))
    contig_hits = len(hits.get("contigs", []))
    glossary_hits = len(hits.get("glossary", []))
    external_hits = len(hits.get("externalrefs_v115", []))
    multi_sheet = sum(1 for v in hits.values() if v)
    support = (
        book_hits * 4
        + contig_hits * 3
        + glossary_hits * 2
        + external_hits * 5
        + multi_sheet * 4
    )
    metadata = (
        cand.bookcount * 2
        + cand.totalocc
        + cand.inbooks_count * 3
        + min(cand.length, 60) / 4.0
    )
    penalty = history["runs"] * 4
    if history["dead"]:
        penalty += 40
    if history["known_dead_rules"]:
        penalty += 80
    if history["last_outcome"] == "NO_OP":
        penalty += 8
    macro_penalty = macro_penalty_for_token(cand.search, macro_penalties)
    if macro_penalty:
        penalty += min(int(macro_penalty["severity"]), 80)
    recomposition_change = recomposition_change_for_token(cand.search, recomposition_changes)
    if recomposition_change:
        penalty += 35
    score = round(support + metadata - penalty, 3)
    reasons = []
    if cand.source == "glossary":
        reasons.append(f"glossary bookcount={cand.bookcount} totalocc={cand.totalocc}")
    else:
        reasons.append(f"external inbooks={cand.inbooks_count}")
    reasons.append(f"hits books={book_hits} contigs={contig_hits} glossary={glossary_hits} external={external_hits}")
    if history["dead"]:
        reasons.append("already dead in probe registry")
    if history["known_dead_rules"]:
        reasons.append("matches known dead branch rules: " + ",".join(history["known_dead_rules"]))
    if macro_penalty:
        reasons.append(f"macro consistency penalty={min(int(macro_penalty['severity']), 80)}")
    if recomposition_change:
        reasons.append("macro recomposition changed")
    why = []
    if history["dead"]:
        why.append("family already repeated a dead mode in registry")
    if history["dp_unused"] >= 2:
        why.append("repeat of DP_UNUSED would likely be redundant")
    if history["gt_hard_fail"] >= 2:
        why.append("repeat of GT hard fail would likely be redundant")
    if history["no_op"] >= 2:
        why.append("repeat of pure no-op would likely be redundant")
    if history["known_dead_rules"]:
        why.append("known dead branch from operational plan; needs a deeper mechanical reason before retry")
    if macro_penalty:
        why.append("macro prefix-child contradiction: " + str(macro_penalty["reason"]))
    if recomposition_change:
        why.append(
            "macro recomposes differently from current components: "
            + str(recomposition_change["original_translation"])
            + " -> "
            + str(recomposition_change["audited_recomposed_translation"])
        )
    if hits.get("externalrefs_v115"):
        why.append("family appears in external refs, so a narrower subfamily or different seam can differ")
    if hits.get("books") or hits.get("contigs") or hits.get("glossary"):
        why.append("family has SQLite footprint, so boundary or swallow behavior may differ")
    if not any(hits.values()):
        why.append("no strong SQLite footprint found, so a new run would need a different search key")
    return {
        "family": cand.family,
        "search": cand.search,
        "source": cand.source,
        "source_key": cand.source_key,
        "source_label": cand.source_label,
        "score": score,
        "probe_history": history,
        "macro_consistency": macro_penalty,
        "macro_recomposition_change": recomposition_change,
        "hits": {k: len(v) for k, v in hits.items()},
        "reason_selected": "; ".join(reasons),
        "why_a_new_run_would_be_different": why,
        "recommended_action": (
            "ABANDON"
            if history["dead"]
            else "REVIEW_AUDIT_FIRST"
            if macro_penalty or recomposition_change
            else "REVIEW"
        ),
    }


def main() -> int:
    args = parse_args()
    db_path = Path(args.db)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        init_probe_registry_schema(conn)
        export_id = latest_export_id(conn, export_id=args.export_id, snapshot_name=args.snapshot_name)
        macro_penalties = latest_macro_consistency_penalties(conn)
        recomposition_changes = latest_macro_recomposition_changes(conn)
        pool = []
        pool.extend(
            candidate_pool_glossary(
                conn,
                export_id=export_id,
                min_len=args.min_len,
                min_bookcount=args.min_bookcount,
                min_totalocc=args.min_totalocc,
                pool=args.pool,
            )
        )
        pool.extend(
            candidate_pool_external(
                conn,
                export_id=export_id,
                min_len=args.min_len,
                min_inbooks=args.min_inbooks,
                pool=args.pool,
            )
        )

        scored = [score_candidate(conn, export_id, cand, macro_penalties, recomposition_changes) for cand in pool]
        scored.sort(
            key=lambda item: (
                item["probe_history"]["dead"],
                -item["score"],
                -item["hits"].get("books", 0),
                -item["hits"].get("externalrefs_v115", 0),
                -item["hits"].get("glossary", 0),
            )
        )

        shortlist = []
        seen = set()
        for item in scored:
            key = item["search"]
            if key in seen:
                continue
            seen.add(key)
            item = dict(item)
            item["rank"] = len(shortlist) + 1
            shortlist.append(item)
            if len(shortlist) >= args.top:
                break

        print(
            json.dumps(
                {
                    "export_id": export_id,
                    "top": args.top,
                    "candidate_pool": len(pool),
                    "shortlist": shortlist,
                },
                ensure_ascii=True,
                indent=2,
            )
        )
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
