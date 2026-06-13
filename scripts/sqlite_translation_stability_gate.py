#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter
from datetime import UTC, datetime
from typing import Any, Dict, List

from sqlite_snapshot_ref import DEFAULT_SNAPSHOT_NAME, resolve_export_id


DEFAULT_DB = "./data/bonelord_operational.sqlite"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Materialize SQL-first translation stability gates")
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--export-id", type=int, default=None)
    parser.add_argument("--snapshot-name", default=DEFAULT_SNAPSHOT_NAME)
    parser.add_argument("--record", action="store_true")
    parser.add_argument("--max-output-items", type=int, default=80)
    return parser.parse_args()


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table,),
    ).fetchone()
    return row is not None


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


def decision_rank(decision: str) -> int:
    return {"ALLOW": 0, "CAUTION": 1, "BLOCKED": 2}.get(decision, 0)


def merge_decision(a: str, b: str) -> str:
    return a if decision_rank(a) >= decision_rank(b) else b


def item_key(token: str, kind: str) -> tuple[str, str]:
    return (token, kind)


def add_item(
    items: Dict[tuple[str, str], Dict[str, Any]],
    *,
    token: str,
    item_kind: str,
    family_token: str | None,
    decision: str,
    risk_score: int,
    reason_code: str,
    reason: str,
    current_translation: str | None = None,
    audited_translation: str | None = None,
    recomposed_translation: str | None = None,
    payload: Dict[str, Any] | None = None,
) -> None:
    key = item_key(token, item_kind)
    if key not in items:
        items[key] = {
            "token": token,
            "item_kind": item_kind,
            "family_token": family_token,
            "decision": decision,
            "risk_score": risk_score,
            "reasons": [],
            "current_translation": current_translation,
            "audited_translation": audited_translation,
            "recomposed_translation": recomposed_translation,
            "payload": {},
        }
    item = items[key]
    item["decision"] = merge_decision(str(item["decision"]), decision)
    item["risk_score"] = max(int(item["risk_score"]), int(risk_score))
    if family_token and not item.get("family_token"):
        item["family_token"] = family_token
    for field, value in (
        ("current_translation", current_translation),
        ("audited_translation", audited_translation),
        ("recomposed_translation", recomposed_translation),
    ):
        if value not in (None, "") and item.get(field) in (None, ""):
            item[field] = value
    item["reasons"].append({"code": reason_code, "reason": reason})
    if payload:
        item["payload"].update(payload)


def collect_recomposition(conn: sqlite3.Connection, items: Dict[tuple[str, str], Dict[str, Any]]) -> Counter[str]:
    counts: Counter[str] = Counter()
    run_id = latest_run_id(conn, "macro_recomposition_audit_runs")
    if run_id is None or not table_exists(conn, "macro_recomposition_audit"):
        return counts
    rows = conn.execute(
        """
        SELECT token, original_translation, recomposed_translation, audited_recomposed_translation,
               component_tokens_json, missing_components_json, changed, payload_json
        FROM macro_recomposition_audit
        WHERE run_id = ?
          AND (changed = 1 OR missing_components_json != '[]')
        """,
        (run_id,),
    ).fetchall()
    for row in rows:
        missing = safe_json(row["missing_components_json"], [])
        payload = safe_json(row["payload_json"], {})
        if int(row["changed"] or 0):
            counts["STALE_RECOMPOSED_MACRO"] += 1
            decision = "BLOCKED" if "<UNK>" in str(row["audited_recomposed_translation"] or "") else "CAUTION"
            add_item(
                items,
                token=str(row["token"]),
                item_kind="MACRO",
                family_token=None,
                decision=decision,
                risk_score=7 if decision == "BLOCKED" else 5,
                reason_code="STALE_RECOMPOSED_MACRO",
                reason="Macro translation differs when recomposed from current component translations.",
                current_translation=row["original_translation"],
                audited_translation=row["audited_recomposed_translation"],
                recomposed_translation=row["recomposed_translation"],
                payload={"macro_recomposition_run_id": run_id, "component_tokens": safe_json(row["component_tokens_json"], []), **payload},
            )
        if missing:
            counts["MISSING_COMPONENTS"] += 1
            add_item(
                items,
                token=str(row["token"]),
                item_kind="MACRO",
                family_token=None,
                decision="BLOCKED",
                risk_score=8,
                reason_code="MISSING_COMPONENTS",
                reason="Macro cannot be recomposed because one or more components are missing.",
                current_translation=row["original_translation"],
                audited_translation=row["audited_recomposed_translation"],
                recomposed_translation=row["recomposed_translation"],
                payload={"macro_recomposition_run_id": run_id, "missing_components": missing, **payload},
            )
    return counts


def collect_glossary_baseline(conn: sqlite3.Connection, export_id: int, items: Dict[tuple[str, str], Dict[str, Any]]) -> Counter[str]:
    counts: Counter[str] = Counter()
    if not table_exists(conn, "sheet__glossary"):
        return counts
    rows = conn.execute(
        """
        SELECT token, translation, tokentype, confidence, evidenceclass_v127, evidencescore_v127,
               totalocc, bookcount, notes
        FROM sheet__glossary
        WHERE __export_id = ?
          AND token IS NOT NULL
        """,
        (export_id,),
    ).fetchall()
    for row in rows:
        counts["GLOSSARY_BASELINE"] += 1
        add_item(
            items,
            token=str(row["token"]),
            item_kind="GLOSSARY_TOKEN",
            family_token=None,
            decision="ALLOW",
            risk_score=0,
            reason_code="BASELINE_CLEAN_UNTIL_FLAGGED",
            reason="Baseline glossary item; later gates may downgrade it.",
            current_translation=row["translation"],
            payload={
                "tokentype": row["tokentype"],
                "confidence": row["confidence"],
                "evidenceclass_v127": row["evidenceclass_v127"],
                "evidencescore_v127": row["evidencescore_v127"],
                "totalocc": row["totalocc"],
                "bookcount": row["bookcount"],
                "notes": row["notes"],
            },
        )
    return counts


def load_strong_prefix_tokens(conn: sqlite3.Connection, export_id: int) -> set[str]:
    if not table_exists(conn, "sheet__glossary"):
        return set()
    rows = conn.execute(
        """
        SELECT token
        FROM sheet__glossary
        WHERE __export_id = ?
          AND token IS NOT NULL
          AND (
            evidenceclass_v127 = 'ANAGRAM_HIGH_BASE'
            OR confidence = 'HIGH'
          )
        """,
        (export_id,),
    ).fetchall()
    strong = {str(row["token"]) for row in rows if row["token"] is not None}
    if table_exists(conn, "sheet__codewordmap_auto"):
        code_rows = conn.execute(
            """
            SELECT token
            FROM sheet__codewordmap_auto
            WHERE __export_id = ?
              AND token IS NOT NULL
              AND CAST(topshare AS REAL) >= 0.95
            """,
            (export_id,),
        ).fetchall()
        strong.update(str(row["token"]) for row in code_rows if row["token"] is not None)
    return strong


def has_stronger_independent_prefix(child_token: str, base_token: str, strong_tokens: set[str]) -> str | None:
    if not child_token.startswith(base_token):
        return None
    for idx in range(len(child_token), len(base_token), -1):
        prefix = child_token[:idx]
        if prefix != base_token and prefix in strong_tokens:
            return prefix
    return None


def collect_consistency(conn: sqlite3.Connection, export_id: int, items: Dict[tuple[str, str], Dict[str, Any]]) -> Counter[str]:
    counts: Counter[str] = Counter()
    run_id = latest_run_id(conn, "macro_consistency_audit_runs")
    if run_id is None or not table_exists(conn, "macro_consistency_violations"):
        return counts
    strong_tokens = load_strong_prefix_tokens(conn, export_id)
    rows = conn.execute(
        """
        SELECT base_token, base_translation, severity, recommended_action, reason, payload_json
        FROM macro_consistency_violations
        WHERE run_id = ?
        """,
        (run_id,),
    ).fetchall()
    for row in rows:
        severity = int(row["severity"] or 0)
        payload = safe_json(row["payload_json"], {})
        base_token = str(row["base_token"])
        reason_text = str(row["reason"] or "")
        base_code = "UNKNOWN_BASE_FLUENT_CHILD" if "base is unknown" in reason_text else "CHILD_BASE_MISMATCH"
        counts[base_code] += 1
        add_item(
            items,
            token=base_token,
            item_kind="BASE_FAMILY",
            family_token=base_token,
            decision="CAUTION",
            risk_score=min(9, max(4, severity // 12)),
            reason_code=base_code,
            reason=reason_text,
            current_translation=row["base_translation"],
            payload={"macro_consistency_run_id": run_id, "severity": severity, "recommended_action": row["recommended_action"]},
        )
        for child in payload.get("children", []):
            child_token = str(child.get("token") or "")
            if not child_token:
                continue
            child_reason = str(child.get("reason") or reason_text)
            child_code = "UNKNOWN_BASE_FLUENT_CHILD" if "base is unknown" in child_reason else "CHILD_BASE_MISMATCH"
            independent_prefix = has_stronger_independent_prefix(child_token, base_token, strong_tokens)
            if independent_prefix and child_code == "CHILD_BASE_MISMATCH":
                counts["PREFIX_PARENT_FALSE_POSITIVE"] += 1
                add_item(
                    items,
                    token=child_token,
                    item_kind="MACRO_CHILD",
                    family_token=independent_prefix,
                    decision="ALLOW",
                    risk_score=0,
                    reason_code="PREFIX_PARENT_FALSE_POSITIVE",
                    reason=(
                        f"Short parent {base_token} is not used for this child because "
                        f"{independent_prefix} has stronger independent evidence."
                    ),
                    current_translation=child.get("translation"),
                    payload={
                        "macro_consistency_run_id": run_id,
                        "rejected_parent": base_token,
                        "independent_prefix": independent_prefix,
                        "base_translation": row["base_translation"],
                        "bookcount": child.get("bookcount"),
                        "totalocc": child.get("totalocc"),
                        "evidence": child.get("evidence"),
                    },
                )
                continue
            decision = "BLOCKED" if severity >= 70 and not bool(child.get("has_external_evidence")) else "CAUTION"
            add_item(
                items,
                token=child_token,
                item_kind="MACRO_CHILD",
                family_token=base_token,
                decision=decision,
                risk_score=min(10, max(6, severity // 10)),
                reason_code=child_code,
                reason=child_reason,
                current_translation=child.get("translation"),
                payload={
                    "macro_consistency_run_id": run_id,
                    "severity": severity,
                    "base_translation": row["base_translation"],
                    "bookcount": child.get("bookcount"),
                    "totalocc": child.get("totalocc"),
                    "evidence": child.get("evidence"),
                    "has_external_evidence": child.get("has_external_evidence"),
                },
            )
    return counts


def collect_glossary_risk(conn: sqlite3.Connection, export_id: int, items: Dict[tuple[str, str], Dict[str, Any]]) -> Counter[str]:
    counts: Counter[str] = Counter()
    if not table_exists(conn, "translation_audit_glossary"):
        return counts
    rows = conn.execute(
        """
        SELECT token, original_translation, audited_translation, risk_score, risk_flags_json
        FROM translation_audit_glossary
        WHERE export_id = ?
          AND risk_score > 0
        """,
        (export_id,),
    ).fetchall()
    for row in rows:
        flags = safe_json(row["risk_flags_json"], [])
        codes = [str(flag.get("code") or "") for flag in flags if isinstance(flag, dict)]
        risk_score = int(row["risk_score"] or 0)
        decision = "BLOCKED" if risk_score >= 5 or "TTNVVN_UNKNOWN_MACRO_LEAK" in codes else "CAUTION"
        counts["GLOSSARY_AUDIT_RISK"] += 1
        add_item(
            items,
            token=str(row["token"]),
            item_kind="GLOSSARY_TOKEN",
            family_token=None,
            decision=decision,
            risk_score=risk_score,
            reason_code="GLOSSARY_AUDIT_RISK",
            reason="Glossary audit flags this token as unsafe for confident semantic reading.",
            current_translation=row["original_translation"],
            audited_translation=row["audited_translation"],
            payload={"risk_flags": flags},
        )
    return counts


def summarize(export_id: int, items: Dict[tuple[str, str], Dict[str, Any]], rule_counts: Counter[str]) -> Dict[str, Any]:
    decision_counts = Counter(str(item["decision"]) for item in items.values())
    blocked = decision_counts["BLOCKED"]
    caution = decision_counts["CAUTION"]
    total = len(items)
    allow = decision_counts["ALLOW"]
    stability_pct = round(max(0.0, min(100.0, 100.0 * (total - blocked - 0.35 * caution) / total)), 2) if total else 100.0
    return {
        "export_id": export_id,
        "item_count": total,
        "blocked_count": blocked,
        "caution_count": caution,
        "allow_count": allow,
        "stability_gate_pct": stability_pct,
        "rule_counts": dict(rule_counts),
        "interpretation": "Only ALLOW/CLEAN items should feed confident reading. BLOCKED items are barred from promotion; CAUTION items require external or structural evidence.",
    }


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS translation_stability_gate_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            export_id INTEGER NOT NULL,
            item_count INTEGER NOT NULL,
            blocked_count INTEGER NOT NULL,
            caution_count INTEGER NOT NULL,
            allow_count INTEGER NOT NULL,
            stability_gate_pct REAL NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS translation_stability_gate_items (
            run_id INTEGER NOT NULL,
            token TEXT NOT NULL,
            item_kind TEXT NOT NULL,
            family_token TEXT,
            decision TEXT NOT NULL,
            risk_score INTEGER NOT NULL,
            reasons_json TEXT NOT NULL,
            current_translation TEXT,
            audited_translation TEXT,
            recomposed_translation TEXT,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, token, item_kind)
        );
        """
    )


def record(conn: sqlite3.Connection, summary: Dict[str, Any], items: Dict[tuple[str, str], Dict[str, Any]]) -> int:
    ensure_schema(conn)
    created_at = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    cur = conn.execute(
        """
        INSERT INTO translation_stability_gate_runs (
            created_at, export_id, item_count, blocked_count, caution_count, allow_count,
            stability_gate_pct, payload_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            created_at,
            summary["export_id"],
            summary["item_count"],
            summary["blocked_count"],
            summary["caution_count"],
            summary["allow_count"],
            summary["stability_gate_pct"],
            json.dumps(summary, ensure_ascii=True, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)
    for item in items.values():
        conn.execute(
            """
            INSERT INTO translation_stability_gate_items (
                run_id, token, item_kind, family_token, decision, risk_score, reasons_json,
                current_translation, audited_translation, recomposed_translation, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                item["token"],
                item["item_kind"],
                item["family_token"],
                item["decision"],
                item["risk_score"],
                json.dumps(item["reasons"], ensure_ascii=True, sort_keys=True),
                item["current_translation"],
                item["audited_translation"],
                item["recomposed_translation"],
                json.dumps(item["payload"], ensure_ascii=True, sort_keys=True),
            ),
        )
    conn.commit()
    return run_id


def output_items(items: Dict[tuple[str, str], Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
    ranked = sorted(
        items.values(),
        key=lambda item: (
            -decision_rank(str(item["decision"])),
            -int(item["risk_score"]),
            str(item["family_token"] or ""),
            str(item["token"]),
        ),
    )
    return ranked[:limit]


def main() -> int:
    args = parse_args()
    conn = connect(args.db)
    try:
        export_id = resolve_export_id(conn, export_id=args.export_id, snapshot_name=args.snapshot_name)
        items: Dict[tuple[str, str], Dict[str, Any]] = {}
        rule_counts: Counter[str] = Counter()
        rule_counts.update(collect_glossary_baseline(conn, export_id, items))
        rule_counts.update(collect_recomposition(conn, items))
        rule_counts.update(collect_consistency(conn, export_id, items))
        rule_counts.update(collect_glossary_risk(conn, export_id, items))
        summary = summarize(export_id, items, rule_counts)
        run_id = record(conn, summary, items) if args.record else None
    finally:
        conn.close()

    print(
        json.dumps(
            {
                **summary,
                "recorded_run_id": run_id,
                "sample_items": output_items(items, args.max_output_items),
            },
            ensure_ascii=True,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
