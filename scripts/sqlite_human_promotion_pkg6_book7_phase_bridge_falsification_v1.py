#!/usr/bin/env python3
"""Falsify package 6: Book7 phase-continuity bridge."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
PACKAGE_ID = "PKG_BOOK7_PHASE_BRIDGE"
CANDIDATE_BOOKS = ("7",)
CONTROL_BOOKS = ("6", "19", "31", "57")


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_promotion_pkg6_book7_phase_bridge_falsification_v1_runs (
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

        CREATE TABLE IF NOT EXISTS human_promotion_pkg6_book7_phase_bridge_falsification_v1_evidence (
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

        CREATE TABLE IF NOT EXISTS human_promotion_pkg6_book7_phase_bridge_falsification_v1_decisions (
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
    latest_phase_probe = max_id(conn, "book7_phase_anchor_probe_runs")
    latest_phase_anchor = max_id(conn, "book7_phase_anchor_items")
    latest_phase_gate = max_id(conn, "book7_phase_continuity_gate_items")
    latest_human_book7 = max_id(conn, "human_book7_phase_shadow_probe_v1_items")
    latest_audit_policy = max_id(conn, "book7_audit_context_policy_items")
    latest_boundary = max_id(conn, "phase_boundary_control_gate_v1_items")
    latest_row0_path = max_id(conn, "row0_phase_operator_path_gate_v1_items")
    latest_residual_shadow = max_id(conn, "human_residual_shadow_v1_items")

    items: list[dict[str, object]] = []

    q = one(
        conn,
        """
        SELECT likely_speech_act, plausible_human_reading, confidence_tier,
               support_level, review_tier, promotion_status, evidence_json
        FROM human_promotion_review_queue_v1_items
        WHERE run_id=? AND package_id=? AND bookid='7'
        """,
        (queue_run_id, PACKAGE_ID),
    )
    if q is None:
        raise RuntimeError("missing queue item for Book7")
    items.append(
        evidence_item(
            "queue:7",
            "candidate",
            "7",
            "human_promotion_review_queue_v1_items",
            str(q["review_tier"]),
            str(q["likely_speech_act"]),
            "QUEUE_CANDIDATE",
            dict(q),
        )
    )

    probe = one(
        conn,
        """
        SELECT run_id, source_row0_variant_run_id, phase_anchor_positive_count,
               continuity_positive_count, swallow_control_count, local_score,
               decision, payload_json
        FROM book7_phase_anchor_probe_runs
        WHERE run_id=?
        """,
        (latest_phase_probe,),
    )
    if probe is None:
        raise RuntimeError("missing Book7 phase anchor probe run")
    items.append(
        evidence_item(
            "phase-probe:summary",
            "positive_gate",
            "6,7,19,31,57",
            "book7_phase_anchor_probe_runs",
            str(probe["decision"]),
            "phase anchor/continuity split with swallow controls",
            "POSITIVE_PHASE_PROBE_SUMMARY",
            dict(probe),
        )
    )

    human7 = one(
        conn,
        """
        SELECT bookid, symbol_text, component_hits_json, classification,
               shadow_implication, next_action, evidence_json
        FROM human_book7_phase_shadow_probe_v1_items
        WHERE run_id=? AND bookid='7'
        """,
        (latest_human_book7,),
    )
    if human7 is None:
        raise RuntimeError("missing human Book7 phase bridge row")
    items.append(
        evidence_item(
            "human-book7:bridge",
            "positive_gate",
            "7",
            "human_book7_phase_shadow_probe_v1_items",
            str(human7["classification"]),
            str(human7["shadow_implication"]),
            "POSITIVE_HUMAN_BOOK7_BRIDGE",
            dict(human7),
        )
    )

    for pattern_id in ("TIINNEF_PHASE_ANCHOR", "NEIAAETTA_CONTINUITY"):
        anchor = one(
            conn,
            """
            SELECT pattern_id, bookid, positions_json, context_status,
                   next_action, payload_json
            FROM book7_phase_anchor_items
            WHERE run_id=? AND bookid='7' AND pattern_id=?
            """,
            (latest_phase_anchor, pattern_id),
        )
        if anchor is None:
            raise RuntimeError(f"missing Book7 anchor item {pattern_id}")
        items.append(
            evidence_item(
                f"phase-anchor:7:{pattern_id}",
                "positive_gate",
                "7",
                "book7_phase_anchor_items",
                str(anchor["context_status"]),
                str(anchor["pattern_id"]),
                "POSITIVE_BOOK7_PHASE_ANCHOR_ITEM",
                dict(anchor),
            )
        )

        gate = one(
            conn,
            """
            SELECT bookid, pattern_id, positions_json, context_status,
                   decision, confidence, functional_label,
                   lexical_gloss_allowed, reason, next_action, evidence_json
            FROM book7_phase_continuity_gate_items
            WHERE run_id=? AND bookid='7' AND pattern_id=?
            """,
            (latest_phase_gate, pattern_id),
        )
        if gate is None:
            raise RuntimeError(f"missing Book7 phase gate item {pattern_id}")
        items.append(
            evidence_item(
                f"phase-gate:7:{pattern_id}",
                "positive_gate",
                "7",
                "book7_phase_continuity_gate_items",
                str(gate["decision"]),
                str(gate["functional_label"]),
                "POSITIVE_BOOK7_PHASE_GATE_ITEM",
                dict(gate),
            )
        )

    boundary7 = one(
        conn,
        """
        SELECT bookid, gate_status, proposed_label, promotion_allowed,
               prose_gloss_allowed, has_3478, risk_class, reason,
               next_action, evidence_json
        FROM phase_boundary_control_gate_v1_items
        WHERE run_id=? AND bookid='7'
        """,
        (latest_boundary,),
    )
    if boundary7 is None:
        raise RuntimeError("missing Book7 phase boundary gate")
    items.append(
        evidence_item(
            "phase-boundary:7",
            "positive_gate",
            "7",
            "phase_boundary_control_gate_v1_items",
            str(boundary7["gate_status"]),
            str(boundary7["proposed_label"]),
            "POSITIVE_BOOK7_BOUNDARY_CONTROL",
            dict(boundary7),
        )
    )

    for bookid in CONTROL_BOOKS:
        control = one(
            conn,
            """
            SELECT bookid, symbol_text, component_hits_json, classification,
                   shadow_implication, next_action, evidence_json
            FROM human_book7_phase_shadow_probe_v1_items
            WHERE run_id=? AND bookid=?
            """,
            (latest_human_book7, bookid),
        )
        if control is None:
            raise RuntimeError(f"missing human Book7 phase control {bookid}")
        items.append(
            evidence_item(
                f"human-book7-control:{bookid}",
                "control_gate",
                bookid,
                "human_book7_phase_shadow_probe_v1_items",
                str(control["classification"]),
                str(control["shadow_implication"]),
                "CONTROL_HUMAN_PHASE_CONTEXT_SPLIT",
                dict(control),
            )
        )

    for bookid, pattern_id in (
        ("6", "NEIAAETTA_CONTINUITY"),
        ("19", "TIINNEF_PHASE_ANCHOR"),
        ("31", "TIINNEF_PHASE_ANCHOR"),
        ("57", "TIINNEF_PHASE_ANCHOR"),
    ):
        anchor = one(
            conn,
            """
            SELECT pattern_id, bookid, positions_json, context_status,
                   next_action, payload_json
            FROM book7_phase_anchor_items
            WHERE run_id=? AND bookid=? AND pattern_id=?
            """,
            (latest_phase_anchor, bookid, pattern_id),
        )
        if anchor is None:
            raise RuntimeError(f"missing phase anchor control {bookid}/{pattern_id}")
        items.append(
            evidence_item(
                f"phase-anchor-control:{bookid}:{pattern_id}",
                "control_gate",
                bookid,
                "book7_phase_anchor_items",
                str(anchor["context_status"]),
                str(anchor["pattern_id"]),
                "CONTROL_PHASE_ANCHOR_CONTEXT_SPLIT",
                dict(anchor),
            )
        )

        gate = one(
            conn,
            """
            SELECT bookid, pattern_id, positions_json, context_status,
                   decision, confidence, functional_label,
                   lexical_gloss_allowed, reason, next_action, evidence_json
            FROM book7_phase_continuity_gate_items
            WHERE run_id=? AND bookid=? AND pattern_id=?
            """,
            (latest_phase_gate, bookid, pattern_id),
        )
        if gate is None:
            raise RuntimeError(f"missing phase gate control {bookid}/{pattern_id}")
        items.append(
            evidence_item(
                f"phase-gate-control:{bookid}:{pattern_id}",
                "control_gate",
                bookid,
                "book7_phase_continuity_gate_items",
                str(gate["decision"]),
                str(gate["functional_label"]),
                "CONTROL_PHASE_GATE_CONTEXT_SPLIT_NO_GLOSS",
                dict(gate),
            )
        )

    for pattern_id in ("AAETTA_SWALLOW_CONTROL", "EIEINT_SWALLOW_CONTROL", "NENIIF_SWALLOW_CONTROL"):
        gate = one(
            conn,
            """
            SELECT bookid, pattern_id, positions_json, context_status,
                   decision, confidence, functional_label,
                   lexical_gloss_allowed, reason, next_action, evidence_json
            FROM book7_phase_continuity_gate_items
            WHERE run_id=? AND bookid='7' AND pattern_id=?
            """,
            (latest_phase_gate, pattern_id),
        )
        if gate is None:
            raise RuntimeError(f"missing Book7 swallow control {pattern_id}")
        items.append(
            evidence_item(
                f"phase-gate-swallow-control:7:{pattern_id}",
                "control_gate",
                "7",
                "book7_phase_continuity_gate_items",
                str(gate["decision"]),
                str(gate["functional_label"]),
                "CONTROL_BOOK7_SWALLOW_NO_PROMOTION",
                dict(gate),
            )
        )

    boundary6 = one(
        conn,
        """
        SELECT bookid, gate_status, proposed_label, promotion_allowed,
               prose_gloss_allowed, has_3478, risk_class, reason,
               next_action, evidence_json
        FROM phase_boundary_control_gate_v1_items
        WHERE run_id=? AND bookid='6'
        """,
        (latest_boundary,),
    )
    if boundary6 is None:
        raise RuntimeError("missing Book6 phase boundary control")
    items.append(
        evidence_item(
            "phase-boundary-control:6",
            "control_gate",
            "6",
            "phase_boundary_control_gate_v1_items",
            str(boundary6["gate_status"]),
            str(boundary6["proposed_label"]),
            "CONTROL_BOOK6_BOUNDARY_HELD",
            dict(boundary6),
        )
    )

    residual6 = one(
        conn,
        """
        SELECT bookid, subfamily, likely_speech_act, plausible_human_reading,
               confidence_tier, source_bridge_id, anchor_ids_json,
               support_level, blocked_claims_json, blocked_overreach,
               falsifier, next_probe, promotion_status, evidence_json
        FROM human_residual_shadow_v1_items
        WHERE run_id=? AND bookid='6'
        """,
        (latest_residual_shadow,),
    )
    if residual6 is None:
        raise RuntimeError("missing Book6 residual continuity control")
    items.append(
        evidence_item(
            "residual-shadow-control:6",
            "control_gate",
            "6",
            "human_residual_shadow_v1_items",
            str(residual6["promotion_status"]),
            str(residual6["likely_speech_act"]),
            "CONTROL_BOOK6_RESIDUAL_CONTINUITY_ONLY",
            dict(residual6),
        )
    )

    for bookid in ("6", "7"):
        row0_path = one(
            conn,
            """
            SELECT bookid, gate_status, proposed_label, path_resolved,
                   promotion_allowed, prose_gloss_allowed,
                   selected_path_rank, margin, reason, next_action,
                   evidence_json
            FROM row0_phase_operator_path_gate_v1_items
            WHERE run_id=? AND bookid=?
            """,
            (latest_row0_path, bookid),
        )
        if row0_path is None:
            raise RuntimeError(f"missing row0 phase path gate for book {bookid}")
        support = "WARN_BOOK7_ROW0_PATH_STABLE_BUT_NO_SEMANTIC_LABEL" if bookid == "7" else "CONTROL_BOOK6_ROW0_PATH_HELD"
        items.append(
            evidence_item(
                f"row0-phase-path:{bookid}",
                "control_gate",
                bookid,
                "row0_phase_operator_path_gate_v1_items",
                str(row0_path["gate_status"]),
                str(row0_path["proposed_label"]),
                support,
                dict(row0_path),
            )
        )

    audit = one(
        conn,
        """
        SELECT context_id, policy_status, policy_confidence, books_json,
               evidence_json, next_action, payload_json
        FROM book7_audit_context_policy_items
        WHERE run_id=? AND context_id='AUDIT_BOOK7_PHASE_OMISSION_CONTEXT'
        """,
        (latest_audit_policy,),
    )
    if audit is None:
        raise RuntimeError("missing Book7 audit context policy")
    items.append(
        evidence_item(
            "book7-audit-context-policy",
            "control_gate",
            "7",
            "book7_audit_context_policy_items",
            str(audit["policy_status"]),
            str(audit["context_id"]),
            "WARN_BOOK7_AUDIT_CONTEXT_HELD",
            dict(audit),
        )
    )

    context = {
        "queue_run_id": queue_run_id,
        "latest_phase_probe_run_id": latest_phase_probe,
        "latest_phase_anchor_run_id": latest_phase_anchor,
        "latest_phase_gate_run_id": latest_phase_gate,
        "latest_human_book7_run_id": latest_human_book7,
        "latest_audit_policy_run_id": latest_audit_policy,
        "latest_boundary_run_id": latest_boundary,
        "latest_row0_path_run_id": latest_row0_path,
        "latest_residual_shadow_run_id": latest_residual_shadow,
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


def component_hits(evidence: dict[str, object]) -> dict[str, int]:
    raw = evidence.get("component_hits_json")
    if raw is None:
        return {}
    return {key: int(value) for key, value in json.loads(str(raw)).items()}


def classify(items: list[dict[str, object]]) -> tuple[str, dict[str, int], dict[str, str]]:
    positive_pass = 0
    positive_fail = 0
    control_pass = 0
    control_warn = 0
    control_fail = 0
    subtype_notes = {
        "7": "Candidate bridge: has TIINNEF before NEIAAETTA and no VNCTIIN, so it bridges continuity into local phase anchor.",
        "6": "Continuity-only control: has NEIAAETTA without TIINNEF, so Book7 reading must not be imported into Book6.",
        "19_31_57": "Phase-context controls: TIINNEF appears inside VNCTIIN/context material, not as the Book7 bridge shape.",
        "swallow_controls": "AAETTA/EIEINT/NENIIF surfaces in Book7 are explicitly swallow/superset controls.",
        "risk": "High row0 phase risk remains active; only the human-functional label is promoted, with no lexical or prose reading.",
    }

    for item in items:
        support = str(item["support_class"])
        status = str(item["status"])
        evidence = evidence_dict(item)
        if support == "QUEUE_CANDIDATE":
            continue

        if support.startswith("POSITIVE_"):
            ok = False
            if support == "POSITIVE_PHASE_PROBE_SUMMARY":
                payload = inner_json(evidence, "payload_json")
                ok = (
                    status == "BOOK7_PHASE_ANCHORS_AUDIT_READY_NO_GLOSS"
                    and int(evidence.get("phase_anchor_positive_count", 0)) == 2
                    and int(evidence.get("continuity_positive_count", 0)) == 2
                    and int(evidence.get("swallow_control_count", 0)) >= 6
                    and payload.get("gloss_allowed") is False
                )
            elif support == "POSITIVE_HUMAN_BOOK7_BRIDGE":
                hits = component_hits(evidence)
                ok = (
                    status == "PHASE_BRIDGE_CONTINUITY_TO_ANCHOR"
                    and hits.get("NEIAAETTA", -1) >= 0
                    and hits.get("TIINNEF", -1) >= 0
                    and hits.get("VNCTIIN", 0) == -1
                )
            elif support == "POSITIVE_BOOK7_PHASE_ANCHOR_ITEM":
                payload = inner_json(evidence, "payload_json")
                ok = (
                    evidence.get("bookid") == "7"
                    and evidence.get("pattern_id") in {"TIINNEF_PHASE_ANCHOR", "NEIAAETTA_CONTINUITY"}
                    and status in {"PHASE_ANCHOR_POSITIVE", "CONTINUITY_POSITIVE"}
                    and payload.get("gloss_allowed") is False
                )
            elif support == "POSITIVE_BOOK7_PHASE_GATE_ITEM":
                ok = (
                    status == "BOOK7_PHASE_CONTINUITY_NO_GLOSS"
                    and evidence.get("bookid") == "7"
                    and evidence.get("pattern_id") in {"TIINNEF_PHASE_ANCHOR", "NEIAAETTA_CONTINUITY"}
                    and int(evidence.get("lexical_gloss_allowed", 1)) == 0
                )
            elif support == "POSITIVE_BOOK7_BOUNDARY_CONTROL":
                ok = (
                    status == "PROMOTE_3478_PHASE_BOUNDARY_CONTROL_NO_GLOSS"
                    and int(evidence.get("promotion_allowed", 0)) == 1
                    and int(evidence.get("prose_gloss_allowed", 1)) == 0
                    and evidence.get("risk_class") == "HIGH_ROW0_PHASE_RISK"
                )
            if ok:
                positive_pass += 1
            else:
                positive_fail += 1
            continue

        if support == "CONTROL_HUMAN_PHASE_CONTEXT_SPLIT":
            if status in {"CONTINUITY_ONLY_CONTROL", "PHASE_CONTEXT_CONTROL"}:
                control_pass += 1
            else:
                control_fail += 1
        elif support == "CONTROL_PHASE_ANCHOR_CONTEXT_SPLIT":
            payload = inner_json(evidence, "payload_json")
            if (
                evidence.get("bookid") in set(CONTROL_BOOKS)
                and evidence.get("pattern_id") in {"TIINNEF_PHASE_ANCHOR", "NEIAAETTA_CONTINUITY"}
                and payload.get("gloss_allowed") is False
            ):
                control_pass += 1
            else:
                control_fail += 1
        elif support == "CONTROL_PHASE_GATE_CONTEXT_SPLIT_NO_GLOSS":
            if (
                status == "BOOK7_PHASE_CONTINUITY_NO_GLOSS"
                and evidence.get("bookid") in set(CONTROL_BOOKS)
                and int(evidence.get("lexical_gloss_allowed", 1)) == 0
            ):
                control_pass += 1
            else:
                control_fail += 1
        elif support == "CONTROL_BOOK7_SWALLOW_NO_PROMOTION":
            if status == "BOOK7_SWALLOW_CONTROL_NO_PROMOTION" and int(evidence.get("lexical_gloss_allowed", 1)) == 0:
                control_pass += 1
            else:
                control_fail += 1
        elif support == "CONTROL_BOOK6_BOUNDARY_HELD":
            if (
                status == "HOLD_3478_DISPLAY_PHASE_CONTROL"
                and int(evidence.get("promotion_allowed", 1)) == 0
                and int(evidence.get("prose_gloss_allowed", 1)) == 0
            ):
                control_pass += 1
            else:
                control_fail += 1
        elif support == "CONTROL_BOOK6_RESIDUAL_CONTINUITY_ONLY":
            if (
                status == "NOT_PROMOTED"
                and evidence.get("support_level") == "STRUCTURAL_CONTINUITY_ONLY_NO_PHASE_GLOSS"
            ):
                control_pass += 1
            else:
                control_fail += 1
        elif support == "CONTROL_BOOK6_ROW0_PATH_HELD":
            if (
                status == "CURRENT_ROW0_OPERATOR_PATH_STABLE_NO_GLOSS"
                and int(evidence.get("promotion_allowed", 1)) == 0
                and int(evidence.get("prose_gloss_allowed", 1)) == 0
            ):
                control_pass += 1
            else:
                control_fail += 1
        elif support == "WARN_BOOK7_ROW0_PATH_STABLE_BUT_NO_SEMANTIC_LABEL":
            if (
                status == "CURRENT_ROW0_OPERATOR_PATH_STABLE_NO_GLOSS"
                and int(evidence.get("promotion_allowed", 1)) == 0
                and int(evidence.get("prose_gloss_allowed", 1)) == 0
            ):
                control_warn += 1
            else:
                control_fail += 1
        elif support == "WARN_BOOK7_AUDIT_CONTEXT_HELD":
            payload = inner_json(evidence, "payload_json")
            if (
                status == "AUDIT_CONTEXT"
                and evidence.get("next_action") == "retain_for_phase_omission_audit_do_not_promote"
                and payload.get("gloss_allowed") is False
            ):
                control_warn += 1
            else:
                control_fail += 1
        else:
            control_fail += 1

    if positive_fail == 0 and control_fail == 0:
        decision = "PROMOTE_HUMAN_FUNCTIONAL_PHASE_BRIDGE_LABEL_NO_GLOSS_HIGH_PHASE_RISK_HELD"
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
        INSERT INTO human_promotion_pkg6_book7_phase_bridge_falsification_v1_runs
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
                    "control_books": list(CONTROL_BOOKS),
                    "principle": "promote a phase-continuity bridge label only; keep high phase risk, no NEIAAETTA/TIINNEF gloss, no 3478 gloss",
                    "scope_split": "Book7 bridges NEIAAETTA continuity into TIINNEF phase anchor; Book6 and 19/31/57 are controls.",
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
            INSERT INTO human_promotion_pkg6_book7_phase_bridge_falsification_v1_evidence
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
        "Book7 is a phase-continuity bridge: it combines a TIINNEF local phase "
        "anchor with NEIAAETTA local continuity, unlike Book6's continuity-only "
        "shape and unlike Books19/31/57 where TIINNEF appears inside VNCTIIN/"
        "context material. This is a human-functional route label under high "
        "row0 phase risk, not a plaintext translation."
    )
    blocked_claims = [
        "Do not translate NEIAAETTA, TIINNEF, VNCTIIN, BENNA, AAETTA, EIEINT, or NENIIF as words from this package.",
        "Do not promote 3478/beholder semantics from Book7's boundary-control evidence.",
        "Do not import Book7's phase-bridge label into Book6, which remains continuity-only.",
        "Do not treat Books19/31/57 TIINNEF+VNCTIIN contexts as the same Book7 bridge.",
        "Do not override the active high row0 phase-risk warning.",
        "Do not promote Book7 as a sentence-level translation.",
    ]
    conn.execute(
        """
        INSERT INTO human_promotion_pkg6_book7_phase_bridge_falsification_v1_decisions
        (run_id, decision_id, scope, decision, human_functional_reading,
         subtype_notes_json, blocked_claims_json, next_action, evidence_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            "PKG6_BOOK7_PHASE_CONTINUITY_BRIDGE_LABEL",
            "Book7 only, with Book6 and Books19/31/57 as controls",
            decision,
            human_functional_reading,
            json.dumps(subtype_notes, ensure_ascii=False, sort_keys=True),
            json.dumps(blocked_claims, ensure_ascii=False),
            "Use as the sixth promoted human-functional package; any future prose claim must first resolve row0 phase risk and find independent semantic anchor evidence.",
            json.dumps(
                {
                    "candidate_books": list(CANDIDATE_BOOKS),
                    "control_books": list(CONTROL_BOOKS),
                    "positive_required_sources": [
                        "book7_phase_anchor_probe_runs",
                        "human_book7_phase_shadow_probe_v1_items",
                        "book7_phase_anchor_items",
                        "book7_phase_continuity_gate_items",
                        "phase_boundary_control_gate_v1_items",
                    ],
                    "control_sources": [
                        "human_book7_phase_shadow_probe_v1_items",
                        "book7_phase_anchor_items",
                        "book7_phase_continuity_gate_items",
                        "phase_boundary_control_gate_v1_items",
                        "human_residual_shadow_v1_items",
                        "row0_phase_operator_path_gate_v1_items",
                        "book7_audit_context_policy_items",
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
