#!/usr/bin/env python3
"""Falsify package 7: Book49 self-contained repeat/register label."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
PACKAGE_ID = "PKG_BOOK49_REPEAT_REGISTER"
CANDIDATE_BOOKS = ("49",)
REPEAT_CONTROLS = ("31", "57", "6", "55", "10", "62", "35", "4", "46", "51", "58")


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_promotion_pkg7_book49_repeat_register_falsification_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            package_id TEXT NOT NULL,
            source_queue_run_id INTEGER NOT NULL,
            decision TEXT NOT NULL,
            candidate_books_json TEXT NOT NULL,
            positive_pass_count INTEGER NOT NULL,
            control_pass_count INTEGER NOT NULL,
            control_warn_count INTEGER NOT NULL,
            control_fail_count INTEGER NOT NULL,
            promoted_functional_label_count INTEGER NOT NULL,
            promoted_plaintext_gloss_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_promotion_pkg7_book49_repeat_register_falsification_v1_evidence (
            run_id INTEGER NOT NULL,
            item_id TEXT NOT NULL,
            item_type TEXT NOT NULL,
            bookid TEXT NOT NULL,
            source_table TEXT NOT NULL,
            status TEXT NOT NULL,
            role_label TEXT NOT NULL,
            support_class TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, item_id)
        );

        CREATE TABLE IF NOT EXISTS human_promotion_pkg7_book49_repeat_register_falsification_v1_decisions (
            run_id INTEGER NOT NULL,
            decision_id TEXT NOT NULL,
            scope TEXT NOT NULL,
            decision TEXT NOT NULL,
            human_functional_reading TEXT NOT NULL,
            subtype_notes_json TEXT NOT NULL,
            blocked_claims_json TEXT NOT NULL,
            next_action TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, decision_id)
        );
        """
    )


def max_id(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT max(run_id) AS run_id FROM {table}").fetchone()
    if row is None or row["run_id"] is None:
        raise RuntimeError(f"missing required run: {table}")
    return int(row["run_id"])


def one(conn: sqlite3.Connection, sql: str, params: tuple[object, ...] = ()) -> sqlite3.Row | None:
    return conn.execute(sql, params).fetchone()


def all_rows(conn: sqlite3.Connection, sql: str, params: tuple[object, ...] = ()) -> list[sqlite3.Row]:
    return list(conn.execute(sql, params).fetchall())


def evidence_item(
    item_id: str,
    item_type: str,
    bookid: str,
    source_table: str,
    status: str,
    role_label: str,
    support_class: str,
    evidence: object,
) -> dict[str, object]:
    return {
        "item_id": item_id,
        "item_type": item_type,
        "bookid": bookid,
        "source_table": source_table,
        "status": status,
        "role_label": role_label,
        "support_class": support_class,
        "evidence_json": json.dumps(evidence, ensure_ascii=False, sort_keys=True),
    }


def latest_queue_run(conn: sqlite3.Connection) -> int:
    row = one(
        conn,
        """
        SELECT run_id
        FROM human_promotion_review_queue_v1_packages
        WHERE package_id=?
        ORDER BY run_id DESC
        LIMIT 1
        """,
        (PACKAGE_ID,),
    )
    if row is None:
        raise RuntimeError(f"missing queue package {PACKAGE_ID}")
    return int(row["run_id"])


def collect_evidence(conn: sqlite3.Connection) -> tuple[int, list[dict[str, object]], dict[str, int]]:
    queue_run_id = latest_queue_run(conn)
    latest_self = max_id(conn, "book49_selfcontainment_gate_runs")
    latest_human = max_id(conn, "human_book49_repeat_shadow_probe_v1_items")
    latest_residual = max_id(conn, "book49_residual_negative_items")
    latest_audit = max_id(conn, "book49_audit_context_policy_items")
    latest_book55 = max_id(conn, "book55_internal_repeat_gate_items")

    items: list[dict[str, object]] = []

    q = one(
        conn,
        """
        SELECT likely_speech_act, plausible_human_reading, confidence_tier,
               support_level, review_tier, promotion_status, evidence_json
        FROM human_promotion_review_queue_v1_items
        WHERE run_id=? AND package_id=? AND bookid='49'
        """,
        (queue_run_id, PACKAGE_ID),
    )
    if q is None:
        raise RuntimeError("missing queue item for Book49")
    items.append(
        evidence_item(
            "queue:49",
            "candidate",
            "49",
            "human_promotion_review_queue_v1_items",
            str(q["review_tier"]),
            str(q["likely_speech_act"]),
            "QUEUE_CANDIDATE",
            dict(q),
        )
    )

    self_gate = one(
        conn,
        """
        SELECT bookid, token_count, repeated_ngram_count,
               repeated_token_coverage, external_note_present, decision,
               functional_tag, next_action, payload_json
        FROM book49_selfcontainment_gate_runs
        WHERE run_id=?
        """,
        (latest_self,),
    )
    if self_gate is None:
        raise RuntimeError("missing Book49 self-containment gate")
    items.append(
        evidence_item(
            "book49:selfcontainment",
            "positive_gate",
            "49",
            "book49_selfcontainment_gate_runs",
            str(self_gate["decision"]),
            str(self_gate["functional_tag"]),
            "POSITIVE_BOOK49_SELF_CONTAINMENT",
            dict(self_gate),
        )
    )

    human49 = one(
        conn,
        """
        SELECT bookid, token_count, repeated_ngram_count,
               repeated_token_coverage, repeat_rank, final_tag_present,
               classification, shadow_implication, next_action, evidence_json
        FROM human_book49_repeat_shadow_probe_v1_items
        WHERE run_id=? AND bookid='49'
        """,
        (latest_human,),
    )
    if human49 is None:
        raise RuntimeError("missing human Book49 repeat row")
    items.append(
        evidence_item(
            "human-book49:repeat-supported",
            "positive_gate",
            "49",
            "human_book49_repeat_shadow_probe_v1_items",
            str(human49["classification"]),
            str(human49["shadow_implication"]),
            "POSITIVE_HUMAN_BOOK49_REPEAT",
            dict(human49),
        )
    )

    for row in all_rows(
        conn,
        """
        SELECT pattern_id, bookid, positions_json, residual_status,
               next_action, payload_json
        FROM book49_residual_negative_items
        WHERE run_id=? AND bookid='49'
        ORDER BY pattern_id
        """,
        (latest_residual,),
    ):
        items.append(
            evidence_item(
                f"book49-residual:{row['pattern_id']}",
                "positive_gate",
                "49",
                "book49_residual_negative_items",
                str(row["residual_status"]),
                str(row["pattern_id"]),
                "POSITIVE_BOOK49_RESIDUAL_COMPONENT_HELD",
                dict(row),
            )
        )

    for bookid in REPEAT_CONTROLS:
        control = one(
            conn,
            """
            SELECT bookid, token_count, repeated_ngram_count,
                   repeated_token_coverage, repeat_rank, final_tag_present,
                   classification, shadow_implication, next_action, evidence_json
            FROM human_book49_repeat_shadow_probe_v1_items
            WHERE run_id=? AND bookid=?
            """,
            (latest_human, bookid),
        )
        if control is None:
            raise RuntimeError(f"missing repeat control {bookid}")
        items.append(
            evidence_item(
                f"human-book49-repeat-control:{bookid}",
                "control_gate",
                bookid,
                "human_book49_repeat_shadow_probe_v1_items",
                str(control["classification"]),
                str(control["shadow_implication"]),
                "CONTROL_REPEAT_ALONE_NOT_SEMANTIC",
                dict(control),
            )
        )

    for row in all_rows(
        conn,
        """
        SELECT bookid, positions_json, occurrence_count, role, decision,
               confidence, functional_label, lexical_gloss_allowed,
               reason, next_action, evidence_json
        FROM book55_internal_repeat_gate_items
        WHERE run_id=?
        ORDER BY CAST(bookid AS INT)
        """,
        (latest_book55,),
    ):
        items.append(
            evidence_item(
                f"book55-repeat-control:{row['bookid']}",
                "control_gate",
                str(row["bookid"]),
                "book55_internal_repeat_gate_items",
                str(row["decision"]),
                str(row["functional_label"]),
                "CONTROL_BOOK55_INTERNAL_REPEAT_SEPARATE",
                dict(row),
            )
        )

    for row in all_rows(
        conn,
        """
        SELECT pattern_id, bookid, positions_json, residual_status,
               next_action, payload_json
        FROM book49_residual_negative_items
        WHERE run_id=? AND residual_status='CONTROL_REPETITION_HIT'
        ORDER BY CAST(bookid AS INT), pattern_id
        LIMIT 10
        """,
        (latest_residual,),
    ):
        items.append(
            evidence_item(
                f"book49-residual-control:{row['bookid']}:{row['pattern_id']}",
                "control_gate",
                str(row["bookid"]),
                "book49_residual_negative_items",
                str(row["residual_status"]),
                str(row["pattern_id"]),
                "CONTROL_BOOK49_RESIDUAL_COMPONENT_NOT_GLOSS",
                dict(row),
            )
        )

    audit = one(
        conn,
        """
        SELECT context_id, policy_status, policy_confidence, books_json,
               evidence_json, next_action, payload_json
        FROM book49_audit_context_policy_items
        WHERE run_id=? AND context_id='AUDIT_BOOK49_O32_NEEI_RESIDUAL_CONTEXT'
        """,
        (latest_audit,),
    )
    if audit is None:
        raise RuntimeError("missing Book49 audit context policy")
    items.append(
        evidence_item(
            "book49-audit-context-policy",
            "control_gate",
            "49",
            "book49_audit_context_policy_items",
            str(audit["policy_status"]),
            str(audit["context_id"]),
            "WARN_BOOK49_RESIDUAL_AUDIT_CONTEXT_HELD",
            dict(audit),
        )
    )

    context = {
        "queue_run_id": queue_run_id,
        "latest_selfcontainment_run_id": latest_self,
        "latest_human_repeat_run_id": latest_human,
        "latest_residual_negative_run_id": latest_residual,
        "latest_audit_context_run_id": latest_audit,
        "latest_book55_repeat_run_id": latest_book55,
    }
    return queue_run_id, items, context


def evidence_dict(item: dict[str, object]) -> dict[str, object]:
    return json.loads(str(item["evidence_json"]))


def inner_json(evidence: dict[str, object], key: str) -> dict[str, object]:
    raw = evidence.get(key)
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    return json.loads(str(raw))


def classify(items: list[dict[str, object]]) -> tuple[str, dict[str, int], dict[str, str]]:
    positive_pass = 0
    positive_fail = 0
    control_pass = 0
    control_warn = 0
    control_fail = 0
    subtype_notes = {
        "49": "Candidate self-contained repeat/register formula: rank 1 repeat profile, coverage 0.85, audit-safe functional tag only.",
        "55": "Separate internal repeat/variant control; repeat exists but is not the same Book49 register.",
        "high_repeat_controls": "Books 31/57/6/10/62/35/4/46/51/58 show high repetition elsewhere, blocking repeat-alone semantics.",
        "residual_components": "O32/NEEI/EEILEE/LEII components stay residual/audit components with no word gloss.",
    }

    for item in items:
        support = str(item["support_class"])
        status = str(item["status"])
        evidence = evidence_dict(item)
        if support == "QUEUE_CANDIDATE":
            continue

        if support.startswith("POSITIVE_"):
            ok = False
            if support == "POSITIVE_BOOK49_SELF_CONTAINMENT":
                ok = (
                    status == "BOOK49_SELF_CONTAINED_REPEAT_FORMULA_ACCEPT_AUDIT_SAFE"
                    and evidence.get("functional_tag") == "SELF_CONTAINED_REPEAT_FORMULA_AUDIT_SAFE"
                    and float(evidence.get("repeated_token_coverage", 0.0)) >= 0.85
                    and int(evidence.get("external_note_present", 0)) == 1
                    and "gloss disallowed" in str(evidence.get("next_action", "")).lower()
                )
            elif support == "POSITIVE_HUMAN_BOOK49_REPEAT":
                ok = (
                    status == "SELF_CONTAINED_REPEAT_FORMULA_SUPPORTED"
                    and int(evidence.get("repeat_rank", 999)) == 1
                    and float(evidence.get("repeated_token_coverage", 0.0)) >= 0.85
                    and int(evidence.get("final_tag_present", 0)) == 1
                )
            elif support == "POSITIVE_BOOK49_RESIDUAL_COMPONENT_HELD":
                payload = inner_json(evidence, "payload_json")
                ok = (
                    status == "BOOK49_RESIDUAL_HIT"
                    and payload.get("gloss_allowed") is False
                    and str(evidence.get("next_action")) == "retain_as_book49_residual_audit"
                )
            if ok:
                positive_pass += 1
            else:
                positive_fail += 1
            continue

        if support == "CONTROL_REPEAT_ALONE_NOT_SEMANTIC":
            if status in {"HIGH_REPEAT_CONTROL", "INTERNAL_REPEAT_CONTROL"}:
                control_pass += 1
            else:
                control_fail += 1
        elif support == "CONTROL_BOOK55_INTERNAL_REPEAT_SEPARATE":
            if int(evidence.get("lexical_gloss_allowed", 1)) == 0 and status in {
                "BOOK55_INTERNAL_REPEAT_VARIANT_NO_GLOSS",
                "BOOK55_REPEAT_CONTROL_NO_PROMOTION",
            }:
                control_pass += 1
            else:
                control_fail += 1
        elif support == "CONTROL_BOOK49_RESIDUAL_COMPONENT_NOT_GLOSS":
            payload = inner_json(evidence, "payload_json")
            if status == "CONTROL_REPETITION_HIT" and payload.get("gloss_allowed") is False:
                control_pass += 1
            else:
                control_fail += 1
        elif support == "WARN_BOOK49_RESIDUAL_AUDIT_CONTEXT_HELD":
            payload = inner_json(evidence, "payload_json")
            if (
                status == "AUDIT_CONTEXT"
                and evidence.get("next_action") == "retain_as_residual_negative_control_do_not_promote_o32_or_neei"
                and payload.get("gloss_allowed") is False
            ):
                control_warn += 1
            else:
                control_fail += 1
        else:
            control_fail += 1

    if positive_fail == 0 and control_fail == 0:
        decision = "PROMOTE_HUMAN_FUNCTIONAL_REPEAT_REGISTER_LABEL_NO_GLOSS_RESIDUAL_COMPONENTS_HELD"
    else:
        decision = "KEEP_IN_REVIEW_NO_PROMOTION"

    return decision, {
        "positive_pass_count": positive_pass,
        "control_pass_count": control_pass,
        "control_warn_count": control_warn,
        "control_fail_count": control_fail,
        "promoted_functional_label_count": 1 if decision.startswith("PROMOTE_HUMAN_FUNCTIONAL") else 0,
        "promoted_plaintext_gloss_count": 0,
    }, subtype_notes


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)
    queue_run_id, items, context = collect_evidence(conn)
    decision, counts, subtype_notes = classify(items)

    cur = conn.execute(
        """
        INSERT INTO human_promotion_pkg7_book49_repeat_register_falsification_v1_runs
        (created_at, package_id, source_queue_run_id, decision,
         candidate_books_json, positive_pass_count, control_pass_count,
         control_warn_count, control_fail_count, promoted_functional_label_count,
         promoted_plaintext_gloss_count, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            now(),
            PACKAGE_ID,
            queue_run_id,
            decision,
            json.dumps(list(CANDIDATE_BOOKS), ensure_ascii=False),
            counts["positive_pass_count"],
            counts["control_pass_count"],
            counts["control_warn_count"],
            counts["control_fail_count"],
            counts["promoted_functional_label_count"],
            counts["promoted_plaintext_gloss_count"],
            json.dumps(
                {
                    **context,
                    "repeat_controls": list(REPEAT_CONTROLS),
                    "principle": "promote a self-contained repeat/register label only; no 49 key, no residual-component word gloss, no refrain prose",
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
        ),
    )
    run_id = int(cur.lastrowid)

    for item in items:
        conn.execute(
            """
            INSERT INTO human_promotion_pkg7_book49_repeat_register_falsification_v1_evidence
            (run_id, item_id, item_type, bookid, source_table, status,
             role_label, support_class, evidence_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                item["item_id"],
                item["item_type"],
                item["bookid"],
                item["source_table"],
                item["status"],
                item["role_label"],
                item["support_class"],
                item["evidence_json"],
            ),
        )

    human_functional_reading = (
        "Book49 is a self-contained repeat/register formula: its row0 line has "
        "the strongest repeat profile in the reviewed set, with repeated-token "
        "coverage 0.85 and a self-containment audit note. The package promotes "
        "only a functional register label, while O32/NEEI/EEILEE/LEII remain "
        "residual audit components with no word gloss."
    )
    blocked_claims = [
        "Do not use 49 as a dictionary key or numeric plaintext key.",
        "Do not translate IAEN, NEEN, O32, NEEI, EEILEE, LEII, or any Book49 repeat component as a word.",
        "Do not convert the repeat/register label into a refrain, chant, spell, or sentence translation.",
        "Do not use repetition alone as semantic evidence; high-repeat controls exist outside Book49.",
        "Do not collapse Book55's VFETTIITAV repeat/variant frame into Book49.",
        "Do not override the Book49 residual audit context for O32/NEEI.",
    ]
    conn.execute(
        """
        INSERT INTO human_promotion_pkg7_book49_repeat_register_falsification_v1_decisions
        (run_id, decision_id, scope, decision, human_functional_reading,
         subtype_notes_json, blocked_claims_json, next_action, evidence_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            "PKG7_BOOK49_REPEAT_REGISTER_LABEL",
            "Book49 only, with Book55 and high-repeat rows as controls",
            decision,
            human_functional_reading,
            json.dumps(subtype_notes, ensure_ascii=False, sort_keys=True),
            json.dumps(blocked_claims, ensure_ascii=False),
            "Use as the seventh promoted human-functional package; require independent semantic anchor before any refrain/prose claim.",
            json.dumps(
                {
                    "candidate_books": list(CANDIDATE_BOOKS),
                    "positive_required_sources": [
                        "book49_selfcontainment_gate_runs",
                        "human_book49_repeat_shadow_probe_v1_items",
                        "book49_residual_negative_items",
                    ],
                    "control_sources": [
                        "human_book49_repeat_shadow_probe_v1_items",
                        "book55_internal_repeat_gate_items",
                        "book49_residual_negative_items",
                        "book49_audit_context_policy_items",
                    ],
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
        ),
    )

    conn.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "package_id": PACKAGE_ID,
                "decision": decision,
                **counts,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
