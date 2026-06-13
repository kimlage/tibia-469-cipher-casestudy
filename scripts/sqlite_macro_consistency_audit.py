#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sqlite3
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any, Dict, List, Sequence

from sqlite_dead_branch_rules import matching_dead_rules
from sqlite_snapshot_ref import DEFAULT_SNAPSHOT_NAME, resolve_export_id


DEFAULT_DB = "./data/bonelord_operational.sqlite"
COMPOSITION_RE = re.compile(r"Composition tokens:\s*(.+?)(?:\.|;|$)", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit macro prefix-child semantic consistency in the operational SQLite DB")
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--export-id", type=int, default=None)
    parser.add_argument("--snapshot-name", default=DEFAULT_SNAPSHOT_NAME)
    parser.add_argument("--min-base-len", type=int, default=5)
    parser.add_argument("--max-children", type=int, default=25)
    parser.add_argument("--record", action="store_true")
    return parser.parse_args()


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def normalize_words(text: object) -> List[str]:
    return re.findall(r"[a-z]+|<unk>|<e>|<ff>|\<\*\>", str(text or "").lower())


def composition_tokens(notes: object) -> List[str]:
    match = COMPOSITION_RE.search(str(notes or ""))
    if not match:
        return []
    return [part.strip() for part in match.group(1).split("+") if part.strip()]


def canonical_word(word: str) -> str:
    irregular = {
        "eyes": "eye",
        "mines": "mine",
        "nines": "nine",
        "sees": "see",
        "statues": "statue",
    }
    if word in irregular:
        return irregular[word]
    if len(word) > 4 and word.endswith("ies"):
        return word[:-3] + "y"
    if len(word) > 4 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def content_words(text: object) -> set[str]:
    stop = {
        "a",
        "an",
        "and",
        "as",
        "be",
        "i",
        "in",
        "is",
        "it",
        "no",
        "of",
        "or",
        "the",
        "to",
        "we",
        "you",
        "ve",
        "<e>",
        "<ff>",
        "<*>",
    }
    return {canonical_word(word) for word in normalize_words(text) if word not in stop}


def load_glossary(conn: sqlite3.Connection, export_id: int) -> List[Dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT
            token,
            translation,
            totalocc,
            bookcount,
            evidenceclass_v127,
            evidencesources_v127,
            notes
        FROM sheet__glossary
        WHERE __export_id = ?
          AND token IS NOT NULL
          AND translation IS NOT NULL
        ORDER BY length(token), token
        """,
        (export_id,),
    ).fetchall()
    return [dict(row) for row in rows if str(row["token"] or "").strip() and str(row["translation"] or "").strip()]


def has_external_evidence(item: Dict[str, Any]) -> bool:
    haystack = " ".join(str(item.get(key) or "") for key in ("evidenceclass_v127", "evidencesources_v127", "notes")).lower()
    return "external" in haystack or "groundtruth" in haystack or "anchor" in haystack or "crib" in haystack


def strong_independent_tokens(glossary: Sequence[Dict[str, Any]]) -> set[str]:
    strong: set[str] = set()
    for item in glossary:
        token = str(item.get("token") or "")
        evidence = str(item.get("evidenceclass_v127") or "")
        if not token:
            continue
        if evidence == "ANAGRAM_HIGH_BASE":
            strong.add(token)
        elif str(item.get("translation") or "").strip() and str(item.get("bookcount") or "0").split(".")[0].isdigit():
            if int(str(item.get("bookcount") or "0").split(".")[0] or 0) >= 10 and evidence in {"MACRO_ACTIVE", "MICRO_MEDIUM"}:
                strong.add(token)
    return strong


def stronger_independent_prefix(child_token: str, base_token: str, strong_tokens: set[str]) -> str | None:
    if not child_token.startswith(base_token):
        return None
    for idx in range(len(child_token), len(base_token), -1):
        prefix = child_token[:idx]
        if prefix != base_token and prefix in strong_tokens:
            return prefix
    return None


def contradiction_reason(base_words: set[str], child_words: set[str], base_translation: str, child_translation: str) -> str | None:
    if not base_words:
        return None
    if "<unk>" in base_words and "<unk>" not in child_words:
        return "base is unknown but child has fluent translation"
    missing = sorted(base_words - child_words)
    if not missing:
        return None
    if base_translation.lower() in child_translation.lower():
        return None
    return "child translation does not preserve base content words: " + ",".join(missing[:8])


def severity_score(base: Dict[str, Any], children: Sequence[Dict[str, Any]], reason: str, external_child_count: int) -> int:
    bookcount = int(str(base.get("bookcount") or "0").split(".")[0] or 0)
    totalocc = int(str(base.get("totalocc") or "0").split(".")[0] or 0)
    score = 10 + min(bookcount, 20) * 3 + min(totalocc, 30) + min(len(children), 20) * 4
    if "unknown" in reason:
        score += 25
    if external_child_count:
        score -= min(external_child_count * 10, 40)
    if matching_dead_rules((str(base.get("token") or ""),)):
        score -= 30
    return max(score, 0)


def audit(conn: sqlite3.Connection, export_id: int, min_base_len: int, max_children: int) -> List[Dict[str, Any]]:
    glossary = load_glossary(conn, export_id)
    strong_tokens = strong_independent_tokens(glossary)
    by_component: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    prefix_only_count: Dict[str, int] = defaultdict(int)
    for item in glossary:
        token = str(item["token"])
        components = composition_tokens(item.get("notes"))
        item["_component_tokens"] = components
        component_set = set(components)
        for component in components:
            by_component[component].append(item)
        for prefix_len in range(min_base_len, len(token)):
            prefix = token[:prefix_len]
            if prefix not in component_set:
                prefix_only_count[prefix] += 1

    violations: List[Dict[str, Any]] = []
    for base in glossary:
        base_token = str(base["token"])
        if len(base_token) < min_base_len:
            continue
        children = [child for child in by_component.get(base_token, []) if child["token"] != base_token]
        if not children:
            continue
        base_words = content_words(base.get("translation"))
        contradictory_children = []
        external_child_count = 0
        prefix_false_positive_count = prefix_only_count.get(base_token, 0)
        for child in children[: max_children * 3]:
            independent_prefix = stronger_independent_prefix(str(child["token"]), base_token, strong_tokens)
            if independent_prefix:
                prefix_false_positive_count += 1
                continue
            child_words = content_words(child.get("translation"))
            reason = contradiction_reason(base_words, child_words, str(base.get("translation") or ""), str(child.get("translation") or ""))
            if not reason:
                continue
            if has_external_evidence(child):
                external_child_count += 1
            contradictory_children.append(
                {
                    "token": child["token"],
                    "translation": child["translation"],
                    "bookcount": child.get("bookcount"),
                    "totalocc": child.get("totalocc"),
                    "evidence": child.get("evidenceclass_v127"),
                    "reason": reason,
                    "has_external_evidence": has_external_evidence(child),
                    "relationship": "component_exact",
                    "component_tokens": child.get("_component_tokens", []),
                }
            )
            if len(contradictory_children) >= max_children:
                break
        if not contradictory_children:
            continue
        reason = contradictory_children[0]["reason"]
        violations.append(
            {
                "base_token": base_token,
                "base_translation": base["translation"],
                "base_bookcount": base.get("bookcount"),
                "base_totalocc": base.get("totalocc"),
                "base_evidence": base.get("evidenceclass_v127"),
                "child_count": len(contradictory_children),
                "external_child_count": external_child_count,
                "prefix_false_positive_count": prefix_false_positive_count,
                "severity": severity_score(base, contradictory_children, reason, external_child_count),
                "reason": reason,
                "recommended_action": "REVIEW" if not has_external_evidence(base) else "REVIEW_WITH_EXTERNAL_EXCEPTION_CHECK",
                "children": contradictory_children,
            }
        )
    violations.sort(key=lambda item: (-item["severity"], str(item["base_token"])))
    return violations


def record(conn: sqlite3.Connection, export_id: int, violations: Sequence[Dict[str, Any]]) -> int:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS macro_consistency_audit_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            export_id INTEGER NOT NULL,
            violation_count INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS macro_consistency_violations (
            run_id INTEGER NOT NULL,
            rank INTEGER NOT NULL,
            base_token TEXT NOT NULL,
            base_translation TEXT,
            severity INTEGER NOT NULL,
            recommended_action TEXT NOT NULL,
            reason TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, rank)
        );
        """
    )
    created_at = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    cur = conn.execute(
        "INSERT INTO macro_consistency_audit_runs (created_at, export_id, violation_count) VALUES (?, ?, ?)",
        (created_at, export_id, len(violations)),
    )
    run_id = int(cur.lastrowid)
    for rank, item in enumerate(violations, start=1):
        conn.execute(
            """
            INSERT INTO macro_consistency_violations (
                run_id, rank, base_token, base_translation, severity,
                recommended_action, reason, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                rank,
                item["base_token"],
                item["base_translation"],
                int(item["severity"]),
                item["recommended_action"],
                item["reason"],
                json.dumps(item, ensure_ascii=True, sort_keys=True),
            ),
        )
    conn.commit()
    return run_id


def main() -> int:
    args = parse_args()
    conn = connect(args.db)
    try:
        export_id = resolve_export_id(conn, export_id=args.export_id, snapshot_name=args.snapshot_name)
        violations = audit(conn, export_id, args.min_base_len, args.max_children)
        run_id = record(conn, export_id, violations) if args.record else None
    finally:
        conn.close()

    payload = {
        "export_id": export_id,
        "recorded_run_id": run_id,
        "violation_count": len(violations),
        "top_violations": violations[:20],
    }
    print(json.dumps(payload, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
