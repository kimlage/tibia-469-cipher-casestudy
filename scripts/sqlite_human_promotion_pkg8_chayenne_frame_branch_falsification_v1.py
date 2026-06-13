#!/usr/bin/env python3
"""Falsify package 8: Chayenne external-shape frame branches."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
PACKAGE_ID = "PKG_CHAYENNE_FRAME_BRANCHES_8_37_66"
CANDIDATE_BOOKS = ("8", "37", "66")
AUDIT_BOOK = "63"
SHARED_BLOCK = "AEFIEIEFIIVFAEATVAT"


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_promotion_pkg8_chayenne_frame_branch_falsification_v1_runs (
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

        CREATE TABLE IF NOT EXISTS human_promotion_pkg8_chayenne_frame_branch_falsification_v1_evidence (
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

        CREATE TABLE IF NOT EXISTS human_promotion_pkg8_chayenne_frame_branch_falsification_v1_decisions (
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
    latest_external_gate = max_id(conn, "chayenne_external_shape_gate_items")
    latest_shape_shadow = max_id(conn, "human_chayenne_shape_shadow_probe_v1_items")
    latest_branch_shadow = max_id(conn, "human_chayenne_branch_shadow_v1_items")
    latest_role_bridge = max_id(conn, "chayenne_role_bridge_gate_v1_items")
    latest_topology = max_id(conn, "chayenne_shape_topology_probe_items")
    latest_primary = max_id(conn, "chayenne_primary_source_search_v1_items")
    latest_exact_near = max_id(conn, "chayenne_exact_near_contrast_v1_items")

    items: list[dict[str, object]] = []

    for bookid in CANDIDATE_BOOKS:
        q = one(
            conn,
            """
            SELECT likely_speech_act, plausible_human_reading, confidence_tier,
                   support_level, review_tier, promotion_status, evidence_json
            FROM human_promotion_review_queue_v1_items
            WHERE run_id=? AND package_id=? AND bookid=?
            """,
            (queue_run_id, PACKAGE_ID, bookid),
        )
        if q is None:
            raise RuntimeError(f"missing queue item for Book{bookid}")
        items.append(
            evidence_item(
                f"queue:{bookid}",
                "candidate",
                bookid,
                "human_promotion_review_queue_v1_items",
                str(q["review_tier"]),
                str(q["likely_speech_act"]),
                "QUEUE_CANDIDATE",
                dict(q),
            )
        )

        external = one(
            conn,
            """
            SELECT bookid, phrase_id, lcs_ratio_phrase, longest_block_len,
                   shared_block, decision, confidence, functional_label,
                   lexical_gloss_allowed, reason, next_action, evidence_json
            FROM chayenne_external_shape_gate_items
            WHERE run_id=? AND bookid=?
            """,
            (latest_external_gate, bookid),
        )
        if external is None:
            raise RuntimeError(f"missing Chayenne external gate for Book{bookid}")
        items.append(
            evidence_item(
                f"external-shape:{bookid}",
                "positive_gate",
                bookid,
                "chayenne_external_shape_gate_items",
                str(external["decision"]),
                str(external["functional_label"]),
                "POSITIVE_EXTERNAL_SHAPE_GATE",
                dict(external),
            )
        )

        shape = one(
            conn,
            """
            SELECT bookid, block_pos, left_context, right_context, branch_class,
                   functional_tags_json, human_shadow_role, blocked_claims_json,
                   falsifier, next_probe, evidence_json
            FROM human_chayenne_shape_shadow_probe_v1_items
            WHERE run_id=? AND bookid=?
            """,
            (latest_shape_shadow, bookid),
        )
        if shape is None:
            raise RuntimeError(f"missing Chayenne shape shadow for Book{bookid}")
        items.append(
            evidence_item(
                f"shape-shadow:{bookid}",
                "positive_gate",
                bookid,
                "human_chayenne_shape_shadow_probe_v1_items",
                str(shape["branch_class"]),
                str(shape["human_shadow_role"]),
                "POSITIVE_HUMAN_SHAPE_BRANCH",
                dict(shape),
            )
        )

        branch = one(
            conn,
            """
            SELECT bookid, branch_class, likely_speech_act, plausible_human_reading,
                   confidence_tier, source_bridge_id, anchor_ids_json,
                   support_level, blocked_claims_json, blocked_overreach,
                   falsifier, next_probe, promotion_status, evidence_json
            FROM human_chayenne_branch_shadow_v1_items
            WHERE run_id=? AND bookid=?
            """,
            (latest_branch_shadow, bookid),
        )
        if branch is None:
            raise RuntimeError(f"missing Chayenne branch shadow for Book{bookid}")
        items.append(
            evidence_item(
                f"branch-shadow:{bookid}",
                "positive_gate",
                bookid,
                "human_chayenne_branch_shadow_v1_items",
                str(branch["promotion_status"]),
                str(branch["branch_class"]),
                "POSITIVE_HUMAN_BRANCH_SHADOW",
                dict(branch),
            )
        )

        role = one(
            conn,
            """
            SELECT bookid, role_group, gate_status, evidence_json
            FROM chayenne_role_bridge_gate_v1_items
            WHERE run_id=? AND bookid=?
            """,
            (latest_role_bridge, bookid),
        )
        if role is None:
            raise RuntimeError(f"missing Chayenne role bridge for Book{bookid}")
        items.append(
            evidence_item(
                f"role-bridge:{bookid}",
                "positive_gate",
                bookid,
                "chayenne_role_bridge_gate_v1_items",
                str(role["gate_status"]),
                str(role["role_group"]),
                "POSITIVE_ROLE_BRIDGE",
                dict(role),
            )
        )

        topology = one(
            conn,
            """
            SELECT bookid, block_pos, left_context, right_context, branch_class,
                   functional_tags_json, next_action, evidence_json
            FROM chayenne_shape_topology_probe_items
            WHERE run_id=? AND bookid=?
            """,
            (latest_topology, bookid),
        )
        if topology is None:
            raise RuntimeError(f"missing Chayenne topology item for Book{bookid}")
        items.append(
            evidence_item(
                f"topology:{bookid}",
                "positive_gate",
                bookid,
                "chayenne_shape_topology_probe_items",
                str(topology["branch_class"]),
                str(topology["next_action"]),
                "POSITIVE_TOPOLOGY_BRANCH",
                dict(topology),
            )
        )

    for table_name, run_id, support_class, status_col, role_col in (
        ("chayenne_external_shape_gate_items", latest_external_gate, "CONTROL_BOOK63_AUDIT_SHAPE", "decision", "functional_label"),
        ("human_chayenne_shape_shadow_probe_v1_items", latest_shape_shadow, "CONTROL_BOOK63_AUDIT_SHAPE_SHADOW", "branch_class", "human_shadow_role"),
        ("human_chayenne_branch_shadow_v1_items", latest_branch_shadow, "CONTROL_BOOK63_AUDIT_BRANCH_SHADOW", "promotion_status", "branch_class"),
        ("chayenne_role_bridge_gate_v1_items", latest_role_bridge, "CONTROL_BOOK63_ROLE_HELD", "gate_status", "role_group"),
        ("chayenne_shape_topology_probe_items", latest_topology, "CONTROL_BOOK63_TOPOLOGY_AUDIT", "branch_class", "next_action"),
    ):
        row = one(conn, f"SELECT * FROM {table_name} WHERE run_id=? AND bookid=?", (run_id, AUDIT_BOOK))
        if row is None:
            raise RuntimeError(f"missing Book63 control in {table_name}")
        items.append(
            evidence_item(
                f"book63-control:{table_name}",
                "control_gate",
                AUDIT_BOOK,
                table_name,
                str(row[status_col]),
                str(row[role_col]),
                support_class,
                dict(row),
            )
        )

    for row in all_rows(
        conn,
        """
        SELECT source_id, source_type, url, sequence_attested,
               explicit_gloss_found, status, note
        FROM chayenne_primary_source_search_v1_items
        WHERE run_id=?
        ORDER BY source_id
        """,
        (latest_primary,),
    ):
        items.append(
            evidence_item(
                f"primary-source:{row['source_id']}",
                "control_gate",
                "8,37,66",
                "chayenne_primary_source_search_v1_items",
                str(row["status"]),
                str(row["source_id"]),
                "CONTROL_PRIMARY_SOURCE_NO_GLOSS",
                dict(row),
            )
        )

    for row in all_rows(
        conn,
        """
        SELECT bookid, best_window, match_class, branch_or_control,
               operational_status, plaintext_allowed, evidence_json
        FROM chayenne_exact_near_contrast_v1_items
        WHERE run_id=? AND operational_status LIKE 'HOLD_NEAR_CONTROL%'
        ORDER BY CAST(bookid AS INT)
        LIMIT 5
        """,
        (latest_exact_near,),
    ):
        items.append(
            evidence_item(
                f"near-control:{row['bookid']}",
                "control_gate",
                str(row["bookid"]),
                "chayenne_exact_near_contrast_v1_items",
                str(row["operational_status"]),
                str(row["match_class"]),
                "CONTROL_NEAR_VARIANT_HELD",
                dict(row),
            )
        )

    context = {
        "queue_run_id": queue_run_id,
        "latest_external_gate_run_id": latest_external_gate,
        "latest_shape_shadow_run_id": latest_shape_shadow,
        "latest_branch_shadow_run_id": latest_branch_shadow,
        "latest_role_bridge_run_id": latest_role_bridge,
        "latest_topology_run_id": latest_topology,
        "latest_primary_source_run_id": latest_primary,
        "latest_exact_near_run_id": latest_exact_near,
    }
    return queue_run_id, items, context


def evidence_dict(item: dict[str, object]) -> dict[str, object]:
    return json.loads(str(item["evidence_json"]))


def tags_all_no_gloss(raw: object) -> bool:
    tags = json.loads(str(raw))
    return bool(tags) and all(tag.get("gloss_allowed") is False for tag in tags)


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
        "8": "Clean VNCTIIN context branch carrying the exact Chayenne external shape frame.",
        "37": "LTAST/TTNVVN boundary handoff into the same external shape frame and then VNCTIIN context.",
        "66": "BENNA/LTAST formula branch carrying the external shape frame; formula context remains functional only.",
        "63": "Residual continuation branch held as audit/control, not promoted with the 8/37/66 package.",
        "sources": "External/community sources attest the sequence or context but do not provide an explicit gloss.",
    }

    for item in items:
        support = str(item["support_class"])
        status = str(item["status"])
        evidence = evidence_dict(item)
        if support == "QUEUE_CANDIDATE":
            continue

        if support.startswith("POSITIVE_"):
            ok = False
            if support == "POSITIVE_EXTERNAL_SHAPE_GATE":
                ok = (
                    status == "CHAYENNE_EXTERNAL_SHAPE_FRAME_NO_GLOSS"
                    and evidence.get("shared_block") == SHARED_BLOCK
                    and int(evidence.get("longest_block_len", 0)) == 19
                    and float(evidence.get("lcs_ratio_phrase", 0.0)) >= 0.88
                    and int(evidence.get("lexical_gloss_allowed", 1)) == 0
                )
            elif support == "POSITIVE_HUMAN_SHAPE_BRANCH":
                inner = inner_json(evidence, "evidence_json")
                ok = (
                    evidence.get("bookid") in set(CANDIDATE_BOOKS)
                    and inner.get("block") == SHARED_BLOCK
                    and tags_all_no_gloss(evidence.get("functional_tags_json"))
                    and evidence.get("branch_class")
                    in {"VNCTIIN_CONTEXT_BRANCH", "LTAST_TO_VNCTIIN_BRANCH", "BENNA_LTAST_FORMULA_BRANCH"}
                )
            elif support == "POSITIVE_HUMAN_BRANCH_SHADOW":
                ok = (
                    status == "NOT_PROMOTED"
                    and evidence.get("bookid") in set(CANDIDATE_BOOKS)
                    and evidence.get("support_level") == "EXTERNAL_SHAPE_PLUS_BRANCH_TOPOLOGY"
                    and evidence.get("branch_class")
                    in {"VNCTIIN_CONTEXT_BRANCH", "LTAST_TO_VNCTIIN_BRANCH", "BENNA_LTAST_FORMULA_BRANCH"}
                )
            elif support == "POSITIVE_ROLE_BRIDGE":
                ok = status == "PASS_RELATED_ROLE" and evidence.get("bookid") in set(CANDIDATE_BOOKS)
            elif support == "POSITIVE_TOPOLOGY_BRANCH":
                inner = inner_json(evidence, "evidence_json")
                ok = (
                    evidence.get("bookid") in set(CANDIDATE_BOOKS)
                    and inner.get("block") == SHARED_BLOCK
                    and tags_all_no_gloss(evidence.get("functional_tags_json"))
                    and "no semantic gloss" in str(evidence.get("next_action"))
                )
            if ok:
                positive_pass += 1
            else:
                positive_fail += 1
            continue

        if support == "CONTROL_BOOK63_AUDIT_SHAPE":
            if (
                status == "CHAYENNE_EXTERNAL_SHAPE_FRAME_NO_GLOSS"
                and evidence.get("bookid") == AUDIT_BOOK
                and int(evidence.get("lexical_gloss_allowed", 1)) == 0
                and float(evidence.get("confidence", 1.0)) < 0.86
            ):
                control_pass += 1
            else:
                control_fail += 1
        elif support == "CONTROL_BOOK63_AUDIT_SHAPE_SHADOW":
            if evidence.get("branch_class") == "RESIDUAL_CONTINUATION_BRANCH" and tags_all_no_gloss(evidence.get("functional_tags_json")):
                control_pass += 1
            else:
                control_fail += 1
        elif support == "CONTROL_BOOK63_AUDIT_BRANCH_SHADOW":
            if (
                status == "NOT_PROMOTED"
                and evidence.get("branch_class") == "RESIDUAL_CONTINUATION_BRANCH"
                and evidence.get("confidence_tier") == "STRUCTURAL_MODERATE_AUDIT_FRAME"
            ):
                control_pass += 1
            else:
                control_fail += 1
        elif support == "CONTROL_BOOK63_ROLE_HELD":
            if status == "PASS_RELATED_ROLE" and evidence.get("role_group") == "CONTEXT_AND_HANDOFF":
                control_pass += 1
            else:
                control_fail += 1
        elif support == "CONTROL_BOOK63_TOPOLOGY_AUDIT":
            inner = inner_json(evidence, "evidence_json")
            if evidence.get("branch_class") == "RESIDUAL_CONTINUATION_BRANCH" and inner.get("block") == SHARED_BLOCK:
                control_pass += 1
            else:
                control_fail += 1
        elif support == "CONTROL_PRIMARY_SOURCE_NO_GLOSS":
            if int(evidence.get("sequence_attested", 0)) == 1 and int(evidence.get("explicit_gloss_found", 1)) == 0:
                control_pass += 1
            else:
                control_fail += 1
        elif support == "CONTROL_NEAR_VARIANT_HELD":
            if status == "HOLD_NEAR_CONTROL_NO_PROMOTION" and int(evidence.get("plaintext_allowed", 1)) == 0:
                control_pass += 1
            else:
                control_fail += 1
        else:
            control_fail += 1

    if positive_fail == 0 and control_fail == 0:
        decision = "PROMOTE_HUMAN_FUNCTIONAL_CHAYENNE_FRAME_BRANCH_LABEL_NO_GLOSS_BOOK63_AUDIT_HELD"
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
        INSERT INTO human_promotion_pkg8_chayenne_frame_branch_falsification_v1_runs
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
                    "audit_book": AUDIT_BOOK,
                    "shared_block": SHARED_BLOCK,
                    "principle": "promote an external-shape branch/register label only; no Chayenne phrase translation, no single English sentence, no Book63 promotion",
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
            INSERT INTO human_promotion_pkg8_chayenne_frame_branch_falsification_v1_evidence
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
        "Books 8/37/66 carry the Chayenne external 469 shape frame "
        "AEFIEIEFIIVFAEATVAT in distinct functional branches: Book8 as a clean "
        "VNCTIIN context branch, Book37 as an LTAST/TTNVVN handoff into VNCTIIN, "
        "and Book66 as a BENNA/LTAST formula branch. This is a register/frame "
        "classification only; the external sequence has no accepted gloss."
    )
    blocked_claims = [
        "Do not translate the Chayenne phrase or shared block AEFIEIEFIIVFAEATVAT.",
        "Do not assign one English sentence to Books 8/37/66.",
        "Do not treat Book63 as promoted; it remains residual/audit control.",
        "Do not promote near variants such as TAEFIEIEFIIVFATFT as equivalent plaintext.",
        "Do not use community/context sources as explicit gloss sources; they attest sequence/context only.",
        "Do not translate VNCTIIN, LTAST, TTNVVN, BENNA, or C68 from this package.",
    ]
    conn.execute(
        """
        INSERT INTO human_promotion_pkg8_chayenne_frame_branch_falsification_v1_decisions
        (run_id, decision_id, scope, decision, human_functional_reading,
         subtype_notes_json, blocked_claims_json, next_action, evidence_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            "PKG8_CHAYENNE_FRAME_BRANCH_LABEL",
            "Books 8/37/66 only, with Book63 and near variants as controls",
            decision,
            human_functional_reading,
            json.dumps(subtype_notes, ensure_ascii=False, sort_keys=True),
            json.dumps(blocked_claims, ensure_ascii=False),
            "Use as the eighth promoted human-functional package; require primary explicit gloss before any Chayenne prose claim.",
            json.dumps(
                {
                    "candidate_books": list(CANDIDATE_BOOKS),
                    "audit_book": AUDIT_BOOK,
                    "positive_required_sources": [
                        "chayenne_external_shape_gate_items",
                        "human_chayenne_shape_shadow_probe_v1_items",
                        "human_chayenne_branch_shadow_v1_items",
                        "chayenne_role_bridge_gate_v1_items",
                        "chayenne_shape_topology_probe_items",
                    ],
                    "control_sources": [
                        "chayenne_primary_source_search_v1_items",
                        "chayenne_exact_near_contrast_v1_items",
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
