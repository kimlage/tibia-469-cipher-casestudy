#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sqlite3
from collections import Counter, defaultdict
from datetime import UTC, datetime
from typing import Any


DEFAULT_DB = "./data/bonelord_operational.sqlite"
TOKEN_RE = re.compile(r"<[^>]+>|[A-Za-z']+")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rank short-token drift inside semantic anomaly phrases")
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--record", action="store_true")
    parser.add_argument("--top-anomalies", type=int, default=80)
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


def safe_json(raw: object, default: Any) -> Any:
    if raw in (None, ""):
        return default
    try:
        return json.loads(str(raw))
    except json.JSONDecodeError:
        return default


def micro_glossary(conn: sqlite3.Connection) -> dict[str, dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT token, translation, tokentype, confidence, evidenceclass_v127,
               evidencescore_v127, totalocc, bookcount, notes
        FROM sheet__glossary
        WHERE __export_id = 2
          AND (
            length(token) = 1
            OR evidenceclass_v127 LIKE 'MICRO%'
            OR tokentype = 'marker'
          )
        """
    ).fetchall()
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        payload = dict(row)
        out[str(row["token"])] = payload
    return out


def macro_owners(conn: sqlite3.Connection, tokens: set[str]) -> dict[str, list[dict[str, Any]]]:
    run_id = latest_run_id(conn, "macro_recomposition_audit_runs")
    if run_id is None:
        return {}
    rows = conn.execute(
        """
        SELECT token, original_translation, audited_recomposed_translation, component_tokens_json, changed
        FROM macro_recomposition_audit
        WHERE run_id = ?
        """,
        (run_id,),
    ).fetchall()
    owners: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        components = [str(item) for item in safe_json(row["component_tokens_json"], [])]
        for token in tokens:
            if token not in components:
                continue
            owners[token].append(
                {
                    "macro": str(row["token"]),
                    "original_translation": str(row["original_translation"] or ""),
                    "audited_recomposed_translation": str(row["audited_recomposed_translation"] or ""),
                    "components": components,
                    "changed": int(row["changed"] or 0),
                }
            )
    for token in owners:
        owners[token].sort(key=lambda item: (len(item["macro"]), item["macro"]))
        owners[token] = owners[token][:16]
    return owners


def anomaly_rows(conn: sqlite3.Connection, limit: int) -> tuple[int | None, list[sqlite3.Row]]:
    run_id = latest_run_id(conn, "semantic_anomaly_audit_runs")
    if run_id is None:
        return None, []
    rows = conn.execute(
        """
        SELECT rank, phrase, score, payload_json
        FROM semantic_anomaly_audit_items
        WHERE run_id = ?
        ORDER BY rank
        LIMIT ?
        """,
        (run_id, limit),
    ).fetchall()
    return run_id, rows


def normalize_word(value: object) -> str:
    return re.sub(r"[^a-z']+", "", str(value or "").lower())


def build_payload(conn: sqlite3.Connection, top_anomalies: int) -> dict[str, Any]:
    anomaly_run_id, rows = anomaly_rows(conn, top_anomalies)
    glossary = micro_glossary(conn)
    translation_to_tokens: dict[str, list[str]] = defaultdict(list)
    for token, payload in glossary.items():
        translation = normalize_word(payload.get("translation"))
        if translation:
            translation_to_tokens[translation].append(token)

    buckets: dict[str, dict[str, Any]] = {}
    for row in rows:
        phrase = str(row["phrase"] or "")
        words = [normalize_word(word) for word in TOKEN_RE.findall(phrase)]
        payload = safe_json(row["payload_json"], {})
        for word in words:
            for token in translation_to_tokens.get(word, []):
                bucket = buckets.setdefault(
                    token,
                    {
                        "token": token,
                        "translation": glossary[token].get("translation"),
                        "anomaly_hit_count": 0,
                        "anomaly_score_sum": 0,
                        "phrases": Counter(),
                        "examples": [],
                        "glossary": glossary[token],
                    },
                )
                bucket["anomaly_hit_count"] += 1
                bucket["anomaly_score_sum"] += int(row["score"] or 0)
                bucket["phrases"][phrase] += 1
                if len(bucket["examples"]) < 10:
                    examples = payload.get("examples", [])
                    bucket["examples"].append(
                        {
                            "rank": int(row["rank"]),
                            "phrase": phrase,
                            "score": int(row["score"] or 0),
                            "example": examples[0] if examples else {},
                        }
                    )

    owner_map = macro_owners(conn, set(buckets))
    items: list[dict[str, Any]] = []
    for token, bucket in buckets.items():
        glossary_payload = bucket["glossary"]
        evidence = str(glossary_payload.get("evidenceclass_v127") or "")
        confidence = str(glossary_payload.get("confidence") or "")
        if str(glossary_payload.get("tokentype") or "") == "marker":
            recommendation = "KEEP_AS_MARKER_ONLY"
        elif evidence == "GROUNDTRUTH":
            recommendation = "KEEP_ANCHOR_BUT_AUDIT_MACRO_CONTEXT"
        elif evidence.startswith("MICRO") or len(token) == 1:
            recommendation = "REQUIRE_PHRASE_LEVEL_PROOF_BEFORE_SEMANTIC_USE"
        else:
            recommendation = "MONITOR"
        item = {
            "token": token,
            "translation": bucket["translation"],
            "confidence": confidence,
            "evidenceclass": evidence,
            "anomaly_hit_count": int(bucket["anomaly_hit_count"]),
            "anomaly_score_sum": int(bucket["anomaly_score_sum"]),
            "top_phrases": bucket["phrases"].most_common(8),
            "examples": bucket["examples"],
            "macro_owners": owner_map.get(token, []),
            "recommendation": recommendation,
            "glossary": glossary_payload,
        }
        item["priority_score"] = item["anomaly_score_sum"] + item["anomaly_hit_count"] * 20
        items.append(item)
    items.sort(key=lambda item: (-int(item["priority_score"]), str(item["token"])))
    return {
        "semantic_anomaly_run_id": anomaly_run_id,
        "item_count": len(items),
        "items": items,
        "interpretation": (
            "Microtoken readings may be mechanically useful but should not be treated as natural-language semantics "
            "inside recurring anomalous formulas without phrase-level support."
        ),
    }


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS microtoken_drift_audit_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            semantic_anomaly_run_id INTEGER,
            item_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS microtoken_drift_audit_items (
            run_id INTEGER NOT NULL,
            rank INTEGER NOT NULL,
            token TEXT NOT NULL,
            translation TEXT,
            anomaly_hit_count INTEGER NOT NULL,
            anomaly_score_sum INTEGER NOT NULL,
            priority_score INTEGER NOT NULL,
            recommendation TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, rank)
        );
        """
    )


def record(conn: sqlite3.Connection, payload: dict[str, Any]) -> int:
    ensure_schema(conn)
    created_at = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    cur = conn.execute(
        """
        INSERT INTO microtoken_drift_audit_runs (
            created_at, semantic_anomaly_run_id, item_count, payload_json
        ) VALUES (?, ?, ?, ?)
        """,
        (
            created_at,
            payload["semantic_anomaly_run_id"],
            payload["item_count"],
            json.dumps({k: v for k, v in payload.items() if k != "items"}, ensure_ascii=True, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)
    for rank, item in enumerate(payload["items"], start=1):
        conn.execute(
            """
            INSERT INTO microtoken_drift_audit_items (
                run_id, rank, token, translation, anomaly_hit_count,
                anomaly_score_sum, priority_score, recommendation, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                rank,
                item["token"],
                item["translation"],
                item["anomaly_hit_count"],
                item["anomaly_score_sum"],
                item["priority_score"],
                item["recommendation"],
                json.dumps(item, ensure_ascii=True, sort_keys=True),
            ),
        )
    conn.commit()
    return run_id


def main() -> int:
    args = parse_args()
    conn = connect(args.db)
    try:
        payload = build_payload(conn, args.top_anomalies)
        run_id = record(conn, payload) if args.record else None
    finally:
        conn.close()
    print(
        json.dumps(
            {
                "recorded_run_id": run_id,
                "semantic_anomaly_run_id": payload["semantic_anomaly_run_id"],
                "item_count": payload["item_count"],
                "top": [
                    {
                        "rank": idx,
                        "token": item["token"],
                        "translation": item["translation"],
                        "hits": item["anomaly_hit_count"],
                        "score_sum": item["anomaly_score_sum"],
                        "recommendation": item["recommendation"],
                    }
                    for idx, item in enumerate(payload["items"][:20], start=1)
                ],
            },
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
