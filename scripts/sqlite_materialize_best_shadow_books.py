#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sqlite3
from collections import Counter
from datetime import UTC, datetime
from typing import Any, Dict, List


DEFAULT_DB = "./data/bonelord_operational.sqlite"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Materialize the current best human-audited shadow reading layer")
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--record", action="store_true")
    parser.add_argument("--max-output-books", type=int, default=20)
    return parser.parse_args()


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone() is not None


def latest_run_id(conn: sqlite3.Connection, table: str) -> int | None:
    if not table_exists(conn, table):
        return None
    row = conn.execute(f"SELECT run_id FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    return int(row["run_id"]) if row else None


def translation_token_map(conn: sqlite3.Connection) -> Dict[str, List[str]]:
    rows = conn.execute(
        """
        SELECT token, translation
        FROM sheet__glossary
        WHERE __export_id = 2
          AND translation IS NOT NULL
          AND translation != ''
        """
    ).fetchall()
    by_translation: Dict[str, List[str]] = {}
    for row in rows:
        by_translation.setdefault(str(row["translation"]).lower(), []).append(str(row["token"]))
    return by_translation


def latest_decisions(conn: sqlite3.Connection) -> List[Dict[str, str]]:
    if not table_exists(conn, "semantic_variant_decisions"):
        return []
    rows = conn.execute(
        """
        SELECT d.token, d.chosen_variant, d.confidence, d.scope, d.promote_to_core, d.reason, d.payload_json,
               g.translation AS current_translation
        FROM semantic_variant_decisions d
        JOIN (
            SELECT token, max(decision_id) AS decision_id
            FROM semantic_variant_decisions
            GROUP BY token
        ) latest
          ON latest.decision_id = d.decision_id
        LEFT JOIN sheet__glossary g
          ON g.__export_id = 2
         AND g.token = d.token
        ORDER BY length(g.translation) DESC, d.token
        """
    ).fetchall()
    by_translation = translation_token_map(conn)
    all_rows = [dict(row) for row in rows]
    chosen_by_token = {str(row["token"]): str(row["chosen_variant"] or "") for row in all_rows}
    decisions: List[Dict[str, str]] = []
    for row in rows:
        current = str(row["current_translation"] or "")
        chosen = str(row["chosen_variant"] or "")
        if not current or not chosen or current == chosen:
            continue
        sibling_tokens = by_translation.get(current.lower(), [])
        sibling_choices = {
            token: chosen_by_token[token]
            for token in sibling_tokens
            if token in chosen_by_token and chosen_by_token[token]
        }
        if len(sibling_tokens) > 1:
            unique_choices = set(sibling_choices.values())
            unresolved_siblings = sorted(set(sibling_tokens) - set(sibling_choices))
            if len(unique_choices) > 1 or unresolved_siblings:
                decisions.append(
                    {
                        "token": str(row["token"]),
                        "current": current,
                        "chosen": chosen,
                        "confidence": str(row["confidence"]),
                        "scope": str(row["scope"]),
                        "reason": str(row["reason"]),
                        "apply_mode": "SKIP_AMBIGUOUS_TRANSLATION",
                        "sibling_tokens": ",".join(sorted(sibling_tokens)),
                        "sibling_choices_json": json.dumps(sibling_choices, ensure_ascii=True, sort_keys=True),
                        "unresolved_siblings": ",".join(unresolved_siblings),
                    }
                )
                continue
        decisions.append(
            {
                "token": str(row["token"]),
                "current": current,
                "chosen": chosen,
                "confidence": str(row["confidence"]),
                "scope": str(row["scope"]),
                "reason": str(row["reason"]),
                "apply_mode": "GLOBAL_PHRASE",
                "sibling_tokens": ",".join(sorted(sibling_tokens)),
                "sibling_choices_json": json.dumps(sibling_choices, ensure_ascii=True, sort_keys=True),
                "unresolved_siblings": "",
            }
        )
    return decisions


def apply_decisions(text: str, decisions: List[Dict[str, str]]) -> tuple[str, List[Dict[str, object]]]:
    output = str(text or "")
    hits: List[Dict[str, object]] = []
    for decision in decisions:
        if decision.get("apply_mode") != "GLOBAL_PHRASE":
            continue
        pattern = re.compile(rf"(?<![A-Za-z]){re.escape(decision['current'])}(?![A-Za-z])", re.IGNORECASE)
        count = len(pattern.findall(output))
        if not count:
            continue
        output = pattern.sub(decision["chosen"], output)
        hits.append(
            {
                "token": decision["token"],
                "from": decision["current"],
                "to": decision["chosen"],
                "count": count,
                "confidence": decision["confidence"],
                "scope": decision["scope"],
                "reason": decision["reason"],
                "apply_mode": decision["apply_mode"],
            }
        )
    return output, hits


def latest_ambiguous_rules(conn: sqlite3.Connection) -> List[Dict[str, object]]:
    if not table_exists(conn, "ambiguous_shadow_rule_audit_runs"):
        return []
    run_id = latest_run_id(conn, "ambiguous_shadow_rule_audit_runs")
    if run_id is None:
        return []
    rows = conn.execute(
        """
        SELECT payload_json
        FROM ambiguous_shadow_rule_audit_items
        WHERE run_id = ?
        ORDER BY rank
        """,
        (run_id,),
    ).fetchall()
    rules: List[Dict[str, object]] = []
    for row in rows:
        try:
            payload = json.loads(str(row["payload_json"] or "{}"))
        except json.JSONDecodeError:
            continue
        for rule in payload.get("rules", []):
            if rule.get("safety") != "TOKEN_SPECIFIC_CANDIDATE":
                continue
            rules.append(rule)
    rules.sort(key=lambda rule: (-len(str(rule.get("phrase") or "")), str(rule.get("token") or "")))
    return rules


def latest_phrase_rules(conn: sqlite3.Connection) -> List[Dict[str, object]]:
    if not table_exists(conn, "semantic_phrase_shadow_rules"):
        return []
    rows = conn.execute(
        """
        SELECT token, phrase, replacement, confidence, reason, source_macro, payload_json
        FROM semantic_phrase_shadow_rules
        WHERE active = 1
        ORDER BY length(phrase) DESC, rule_id DESC
        """
    ).fetchall()
    return [dict(row) for row in rows]


def apply_ambiguous_rules(text: str, rules: List[Dict[str, object]]) -> tuple[str, List[Dict[str, object]]]:
    output = str(text or "")
    hits: List[Dict[str, object]] = []
    for rule in rules:
        phrase = str(rule.get("phrase") or "")
        replacement = str(rule.get("replacement") or "")
        if not phrase or not replacement or phrase == replacement:
            continue
        pattern = re.compile(rf"(?<![A-Za-z]){re.escape(phrase)}(?![A-Za-z])", re.IGNORECASE)
        count = len(pattern.findall(output))
        if not count:
            continue
        output = pattern.sub(replacement, output)
        hits.append(
            {
                "token": rule.get("token"),
                "from": phrase,
                "to": replacement,
                "count": count,
                "confidence": "TOKEN_SPECIFIC",
                "scope": "TOKEN_SPECIFIC_SHADOW_RULE",
                "reason": f"Accepted token-specific ambiguous rule from {rule.get('source_macro')}",
                "apply_mode": "TOKEN_SPECIFIC_PHRASE",
            }
        )
    return output, hits


def apply_phrase_rules(text: str, rules: List[Dict[str, object]]) -> tuple[str, List[Dict[str, object]]]:
    output = str(text or "")
    hits: List[Dict[str, object]] = []
    for rule in rules:
        phrase = str(rule.get("phrase") or "")
        replacement = str(rule.get("replacement") or "")
        if not phrase or not replacement or phrase == replacement:
            continue
        pattern = re.compile(rf"(?<![A-Za-z]){re.escape(phrase)}(?![A-Za-z])", re.IGNORECASE)
        count = len(pattern.findall(output))
        if not count:
            continue
        output = pattern.sub(replacement, output)
        hits.append(
            {
                "token": rule.get("token"),
                "from": phrase,
                "to": replacement,
                "count": count,
                "confidence": rule.get("confidence"),
                "scope": "SEMANTIC_PHRASE_SHADOW_RULE",
                "reason": rule.get("reason"),
                "source_macro": rule.get("source_macro"),
                "apply_mode": "SEMANTIC_PHRASE",
            }
        )
    return output, hits


def materialize(
    conn: sqlite3.Connection,
    decisions: List[Dict[str, str]],
    ambiguous_rules: List[Dict[str, object]],
    phrase_rules: List[Dict[str, object]],
) -> Dict[str, object]:
    safe_run_id = latest_run_id(conn, "safe_book_translation_runs")
    if safe_run_id is None:
        raise RuntimeError("safe_book_translation_runs has no rows")
    rows = conn.execute(
        """
        SELECT bookid, safe_text, blocked_hit_count, caution_hit_count, risk_score
        FROM safe_book_translations
        WHERE run_id = ?
        ORDER BY CAST(bookid AS INTEGER)
        """,
        (safe_run_id,),
    ).fetchall()
    items: List[Dict[str, object]] = []
    totals: Counter[str] = Counter()
    for row in rows:
        best_text, hits = apply_decisions(str(row["safe_text"] or ""), decisions)
        best_text, token_hits = apply_ambiguous_rules(best_text, ambiguous_rules)
        hits.extend(token_hits)
        best_text, phrase_hits = apply_phrase_rules(best_text, phrase_rules)
        hits.extend(phrase_hits)
        totals["book_count"] += 1
        if hits:
            totals["books_with_best_shadow_hits"] += 1
        totals["best_shadow_hit_count"] += sum(int(hit["count"]) for hit in hits)
        unresolved = int(row["blocked_hit_count"] or 0)
        suspect_neutral_hits = sum(
            int(hit["count"]) for hit in hits if str(hit["to"]).startswith("<SUSPECT:")
        )
        if unresolved or suspect_neutral_hits:
            totals["books_with_unresolved_or_suspect"] += 1
        items.append(
            {
                "bookid": str(row["bookid"]),
                "safe_text": row["safe_text"],
                "best_shadow_text": best_text,
                "safe_blocked_hit_count": unresolved,
                "safe_caution_hit_count": int(row["caution_hit_count"] or 0),
                "safe_risk_score": int(row["risk_score"] or 0),
                "suspect_neutral_hit_count": suspect_neutral_hits,
                "best_shadow_hits": hits,
            }
        )
    clean_books = totals["book_count"] - totals["books_with_unresolved_or_suspect"]
    best_shadow_clean_pct = round(100.0 * clean_books / totals["book_count"], 2) if totals["book_count"] else 0.0
    return {
        "summary": {
            "safe_book_run_id": safe_run_id,
            "book_count": totals["book_count"],
            "decision_count": len(decisions),
            "active_decision_count": sum(1 for decision in decisions if decision.get("apply_mode") == "GLOBAL_PHRASE"),
            "skipped_ambiguous_decision_count": sum(
                1 for decision in decisions if decision.get("apply_mode") == "SKIP_AMBIGUOUS_TRANSLATION"
            ),
            "token_specific_rule_count": len(ambiguous_rules),
            "semantic_phrase_rule_count": len(phrase_rules),
            "books_with_best_shadow_hits": totals["books_with_best_shadow_hits"],
            "best_shadow_hit_count": totals["best_shadow_hit_count"],
            "books_with_unresolved_or_suspect": totals["books_with_unresolved_or_suspect"],
            "best_shadow_clean_pct": best_shadow_clean_pct,
            "interpretation": "Best shadow is the current most honest human-audited reading layer; it is not a decode-core mutation.",
        },
        "items": items,
        "decisions": decisions,
        "ambiguous_rules": ambiguous_rules,
        "phrase_rules": phrase_rules,
    }


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS best_shadow_book_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            safe_book_run_id INTEGER NOT NULL,
            book_count INTEGER NOT NULL,
            decision_count INTEGER NOT NULL,
            books_with_best_shadow_hits INTEGER NOT NULL,
            best_shadow_hit_count INTEGER NOT NULL,
            books_with_unresolved_or_suspect INTEGER NOT NULL,
            best_shadow_clean_pct REAL NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS best_shadow_book_translations (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            safe_text TEXT,
            best_shadow_text TEXT,
            safe_blocked_hit_count INTEGER NOT NULL,
            safe_caution_hit_count INTEGER NOT NULL,
            safe_risk_score INTEGER NOT NULL,
            suspect_neutral_hit_count INTEGER NOT NULL,
            best_shadow_hits_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        );
        """
    )


def record(conn: sqlite3.Connection, payload: Dict[str, object]) -> int:
    ensure_schema(conn)
    summary = payload["summary"]
    created_at = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    cur = conn.execute(
        """
        INSERT INTO best_shadow_book_runs (
            created_at, safe_book_run_id, book_count, decision_count,
            books_with_best_shadow_hits, best_shadow_hit_count,
            books_with_unresolved_or_suspect, best_shadow_clean_pct, payload_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            created_at,
            summary["safe_book_run_id"],
            summary["book_count"],
            summary["decision_count"],
            summary["books_with_best_shadow_hits"],
            summary["best_shadow_hit_count"],
            summary["books_with_unresolved_or_suspect"],
            summary["best_shadow_clean_pct"],
            json.dumps(
                {
                    **summary,
                    "decisions": payload["decisions"],
                    "ambiguous_rules": payload["ambiguous_rules"],
                    "phrase_rules": payload["phrase_rules"],
                },
                ensure_ascii=True,
                sort_keys=True,
            ),
        ),
    )
    run_id = int(cur.lastrowid)
    for item in payload["items"]:
        conn.execute(
            """
            INSERT INTO best_shadow_book_translations (
                run_id, bookid, safe_text, best_shadow_text,
                safe_blocked_hit_count, safe_caution_hit_count, safe_risk_score,
                suspect_neutral_hit_count, best_shadow_hits_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                item["bookid"],
                item["safe_text"],
                item["best_shadow_text"],
                item["safe_blocked_hit_count"],
                item["safe_caution_hit_count"],
                item["safe_risk_score"],
                item["suspect_neutral_hit_count"],
                json.dumps(item["best_shadow_hits"], ensure_ascii=True, sort_keys=True),
            ),
        )
    conn.commit()
    return run_id


def main() -> int:
    args = parse_args()
    conn = connect(args.db)
    try:
        decisions = latest_decisions(conn)
        ambiguous_rules = latest_ambiguous_rules(conn)
        phrase_rules = latest_phrase_rules(conn)
        payload = materialize(conn, decisions, ambiguous_rules, phrase_rules)
        run_id = record(conn, payload) if args.record else None
    finally:
        conn.close()
    sample = sorted(
        payload["items"],
        key=lambda item: (
            -int(item["safe_blocked_hit_count"]),
            -int(item["suspect_neutral_hit_count"]),
            -len(item["best_shadow_hits"]),
            int(item["bookid"]),
        ),
    )[: args.max_output_books]
    print(
        json.dumps(
            {
                **payload["summary"],
                "recorded_run_id": run_id,
                "decisions": payload["decisions"],
                "ambiguous_rules": payload["ambiguous_rules"],
                "phrase_rules": payload["phrase_rules"],
                "sample_books": sample,
            },
            ensure_ascii=True,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
