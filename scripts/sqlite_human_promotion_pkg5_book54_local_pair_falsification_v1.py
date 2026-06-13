#!/usr/bin/env python3
"""Falsify package 5: Book54 local-pair shared spine with Book20."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
PACKAGE_ID = "PKG_BOOK54_LOCAL_PAIR_SPINE"
CANDIDATE_BOOKS = ("54",)
PAIR_BOOKS = ("20", "54")
SHARED_BLOCK = "LTFNTFEIFAIFAINIIETNEEIVN"


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_promotion_pkg5_book54_local_pair_falsification_v1_runs (
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

        CREATE TABLE IF NOT EXISTS human_promotion_pkg5_book54_local_pair_falsification_v1_evidence (
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

        CREATE TABLE IF NOT EXISTS human_promotion_pkg5_book54_local_pair_falsification_v1_decisions (
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


def decode_books_json(raw: str) -> set[str]:
    values = json.loads(raw)
    return {str(value) for value in values}


def rows_touching_books(rows: list[sqlite3.Row], books: set[str]) -> list[dict[str, object]]:
    touching = []
    for row in rows:
        row_books = decode_books_json(str(row["books_json"]))
        if row_books & books:
            touching.append(dict(row))
    return touching


def add_zero_absence_controls(
    conn: sqlite3.Connection,
    items: list[dict[str, object]],
    latest_zero_operator: int,
    latest_zero_boundary_feature: int,
    latest_zero_recurrence: int,
    latest_zero_segment_cluster: int,
) -> None:
    candidate_set = set(PAIR_BOOKS)

    operator_rows = all_rows(
        conn,
        """
        SELECT bookid, gate_status, proposed_label, promotion_allowed,
               prose_gloss_allowed, exit_types, reason, next_action,
               evidence_json
        FROM zero_operator_typed_exit_gate_v1_book_decisions
        WHERE run_id=? AND bookid IN ('20', '54')
        ORDER BY CAST(bookid AS INT)
        """,
        (latest_zero_operator,),
    )
    items.append(
        evidence_item(
            "zero-operator:20-54-absence",
            "control_gate",
            "20,54",
            "zero_operator_typed_exit_gate_v1_book_decisions",
            "ABSENT_FOR_CANDIDATE_PAIR" if not operator_rows else "ZERO_OPERATOR_ROWS_PRESENT",
            "no zero operator gate rows for Book20/54",
            "CONTROL_ZERO_OPERATOR_ABSENT",
            {
                "candidate_books": list(PAIR_BOOKS),
                "row_count": len(operator_rows),
                "rows": [dict(row) for row in operator_rows],
                "expected": "no zero-operator evidence should be imported into the local-pair reading",
            },
        )
    )

    boundary_rows = all_rows(
        conn,
        """
        SELECT context_key, books_json, dominant_existing_tags_json,
               feature_status, decision, evidence_json
        FROM zero_context_boundary_feature_gate_items
        WHERE run_id=?
        ORDER BY context_key
        """,
        (latest_zero_boundary_feature,),
    )
    touching_boundary = rows_touching_books(boundary_rows, candidate_set)
    items.append(
        evidence_item(
            "zero-boundary-feature:20-54-absence",
            "control_gate",
            "20,54",
            "zero_context_boundary_feature_gate_items",
            "ABSENT_FOR_CANDIDATE_PAIR" if not touching_boundary else "ZERO_BOUNDARY_FEATURE_PRESENT",
            "no recurrent zero-boundary feature for Book20/54",
            "CONTROL_ZERO_CONTEXT_ABSENT",
            {
                "candidate_books": list(PAIR_BOOKS),
                "touching_row_count": len(touching_boundary),
                "touching_rows": touching_boundary,
            },
        )
    )

    recurrence_rows = all_rows(
        conn,
        """
        SELECT context_key, left_digits, right_digits, occurrence_count,
               book_count, books_json, anchor_overlap_json, decision,
               evidence_json
        FROM zero_context_recurrence_scorer_items
        WHERE run_id=?
        ORDER BY context_key
        """,
        (latest_zero_recurrence,),
    )
    touching_recurrence = rows_touching_books(recurrence_rows, candidate_set)
    items.append(
        evidence_item(
            "zero-recurrence:20-54-absence",
            "control_gate",
            "20,54",
            "zero_context_recurrence_scorer_items",
            "ABSENT_FOR_CANDIDATE_PAIR" if not touching_recurrence else "ZERO_RECURRENCE_PRESENT",
            "no recurrent zero context for Book20/54",
            "CONTROL_ZERO_CONTEXT_ABSENT",
            {
                "candidate_books": list(PAIR_BOOKS),
                "touching_row_count": len(touching_recurrence),
                "touching_rows": touching_recurrence,
            },
        )
    )

    segment_rows = all_rows(
        conn,
        """
        SELECT rank, segment_digits, digit_len, occurrence_count, book_count,
               books_json, dominant_tag_id, dominant_tag_share, review_status,
               decision, evidence_json
        FROM zero_boundary_segment_cluster_v2_items
        WHERE run_id=?
        ORDER BY rank
        """,
        (latest_zero_segment_cluster,),
    )
    touching_segments = rows_touching_books(segment_rows, candidate_set)
    items.append(
        evidence_item(
            "zero-segment-cluster:20-54-absence",
            "control_gate",
            "20,54",
            "zero_boundary_segment_cluster_v2_items",
            "ABSENT_FOR_CANDIDATE_PAIR" if not touching_segments else "ZERO_SEGMENT_CLUSTER_PRESENT",
            "no zero-boundary segment cluster for Book20/54",
            "CONTROL_ZERO_CONTEXT_ABSENT",
            {
                "candidate_books": list(PAIR_BOOKS),
                "touching_row_count": len(touching_segments),
                "touching_rows": touching_segments,
            },
        )
    )


def collect_evidence(conn: sqlite3.Connection) -> tuple[int, list[dict[str, object]], dict[str, int]]:
    queue_run_id = latest_queue_run(conn)
    latest_row0 = max_id(conn, "row0_variant_book_tokens")
    latest_pair_probe = max_id(conn, "human_book54_pair_shadow_probe_v1_items")
    latest_zero_pair = max_id(conn, "zero_pair_alignment_items")
    latest_zero_pair_local = max_id(conn, "zero_pair_local_context_gate_items")
    latest_residual_bridge = max_id(conn, "human_residual_bridge_v1_items")
    latest_residual_shadow = max_id(conn, "human_residual_shadow_v1_items")
    latest_zero_operator = max_id(conn, "zero_operator_typed_exit_gate_v1_book_decisions")
    latest_zero_boundary_feature = max_id(conn, "zero_context_boundary_feature_gate_items")
    latest_zero_recurrence = max_id(conn, "zero_context_recurrence_scorer_items")
    latest_zero_segment_cluster = max_id(conn, "zero_boundary_segment_cluster_v2_items")

    items: list[dict[str, object]] = []

    q = one(
        conn,
        """
        SELECT likely_speech_act, plausible_human_reading, confidence_tier,
               support_level, review_tier, promotion_status, evidence_json
        FROM human_promotion_review_queue_v1_items
        WHERE run_id=? AND package_id=? AND bookid='54'
        """,
        (queue_run_id, PACKAGE_ID),
    )
    if q is None:
        raise RuntimeError("missing queue item for Book54")
    items.append(
        evidence_item(
            "queue:54",
            "candidate",
            "54",
            "human_promotion_review_queue_v1_items",
            str(q["review_tier"]),
            str(q["likely_speech_act"]),
            "QUEUE_CANDIDATE",
            dict(q),
        )
    )

    row20 = one(
        conn,
        """
        SELECT bookid, token_count, symbol_text, token_text, tokens_json
        FROM row0_variant_book_tokens
        WHERE run_id=? AND bookid='20'
        """,
        (latest_row0,),
    )
    row54 = one(
        conn,
        """
        SELECT bookid, token_count, symbol_text, token_text, tokens_json
        FROM row0_variant_book_tokens
        WHERE run_id=? AND bookid='54'
        """,
        (latest_row0,),
    )
    if row20 is None or row54 is None:
        raise RuntimeError("missing row0 Book20/54 tokens")
    row0_evidence = {
        "book20": dict(row20),
        "book54": dict(row54),
        "shared_block": SHARED_BLOCK,
        "shared_block_in_20": SHARED_BLOCK in str(row20["symbol_text"]),
        "shared_block_in_54": SHARED_BLOCK in str(row54["symbol_text"]),
        "book20_prefix": str(row20["symbol_text"]).split(SHARED_BLOCK)[0],
        "book20_suffix": str(row20["symbol_text"]).split(SHARED_BLOCK)[1],
        "book54_prefix": str(row54["symbol_text"]).split(SHARED_BLOCK)[0],
        "book54_suffix": str(row54["symbol_text"]).split(SHARED_BLOCK)[1],
    }
    items.append(
        evidence_item(
            "row0:20-54-shared-spine",
            "positive_gate",
            "20,54",
            "row0_variant_book_tokens",
            "SHARED_SPINE_PRESENT",
            "Book54 preserves Book20 local-pair spine",
            "POSITIVE_ROW0_SHARED_SPINE",
            row0_evidence,
        )
    )

    for bookid in PAIR_BOOKS:
        probe = one(
            conn,
            """
            SELECT bookid, symbol_text, prefix_before_shared, shared_block,
                   suffix_after_shared, classification, shadow_implication,
                   next_action, evidence_json
            FROM human_book54_pair_shadow_probe_v1_items
            WHERE run_id=? AND bookid=?
            """,
            (latest_pair_probe, bookid),
        )
        if probe is None:
            raise RuntimeError(f"missing Book54 pair probe for book {bookid}")
        items.append(
            evidence_item(
                f"book54-pair-probe:{bookid}",
                "positive_gate",
                bookid,
                "human_book54_pair_shadow_probe_v1_items",
                str(probe["classification"]),
                str(probe["shadow_implication"]),
                "POSITIVE_BOOK54_PAIR_PROBE",
                dict(probe),
            )
        )

    pair_20_54 = one(
        conn,
        """
        SELECT pair_id, left_bookid, right_bookid, left_token_count,
               right_token_count, lcs_len, lcs_ratio_shorter,
               lcs_ratio_longer, alignment_status, next_action,
               evidence_json, payload_json
        FROM zero_pair_alignment_items
        WHERE run_id=? AND pair_id='PAIR_20_54_NIIE_EIVN'
        """,
        (latest_zero_pair,),
    )
    if pair_20_54 is None:
        raise RuntimeError("missing zero-pair alignment for Book20/54")
    items.append(
        evidence_item(
            "zero-pair:20-54",
            "positive_gate",
            "20,54",
            "zero_pair_alignment_items",
            str(pair_20_54["alignment_status"]),
            str(pair_20_54["pair_id"]),
            "POSITIVE_ZERO_PAIR_ALIGNMENT",
            dict(pair_20_54),
        )
    )

    for bookid in PAIR_BOOKS:
        local = one(
            conn,
            """
            SELECT context_id, bookid, source_pair_id, policy_status, decision,
                   confidence, functional_label, lexical_gloss_allowed,
                   reason, next_action, evidence_json
            FROM zero_pair_local_context_gate_items
            WHERE run_id=? AND context_id='LOCAL_PAIR_20_54_TRUNCATION_ALIGNMENT'
              AND bookid=?
            """,
            (latest_zero_pair_local, bookid),
        )
        if local is None:
            raise RuntimeError(f"missing zero-pair local context for book {bookid}")
        items.append(
            evidence_item(
                f"zero-local:20-54:{bookid}",
                "positive_gate",
                bookid,
                "zero_pair_local_context_gate_items",
                str(local["decision"]),
                str(local["functional_label"]),
                "POSITIVE_ZERO_LOCAL_CONTEXT",
                dict(local),
            )
        )

    bridge = one(
        conn,
        """
        SELECT bridge_id, target_family, anchor_ids_json, support_level,
               support_summary, blocked_overreach, next_probe,
               anchor_evidence_json, precheck_json
        FROM human_residual_bridge_v1_items
        WHERE run_id=? AND bridge_id='B_RESIDUAL_LOCAL_PAIR'
        """,
        (latest_residual_bridge,),
    )
    if bridge is None:
        raise RuntimeError("missing residual local-pair bridge")
    items.append(
        evidence_item(
            "residual-bridge:local-pair",
            "positive_gate",
            "20,54,25,39",
            "human_residual_bridge_v1_items",
            str(bridge["support_level"]),
            str(bridge["target_family"]),
            "POSITIVE_RESIDUAL_BRIDGE",
            dict(bridge),
        )
    )

    residual20 = one(
        conn,
        """
        SELECT bookid, subfamily, likely_speech_act, plausible_human_reading,
               confidence_tier, source_bridge_id, anchor_ids_json,
               support_level, blocked_claims_json, blocked_overreach,
               falsifier, next_probe, promotion_status, evidence_json
        FROM human_residual_shadow_v1_items
        WHERE run_id=? AND bookid='20'
        """,
        (latest_residual_shadow,),
    )
    if residual20 is None:
        raise RuntimeError("missing Book20 residual local-pair shadow")
    items.append(
        evidence_item(
            "residual-shadow:20",
            "positive_gate",
            "20",
            "human_residual_shadow_v1_items",
            str(residual20["promotion_status"]),
            str(residual20["likely_speech_act"]),
            "POSITIVE_RESIDUAL_SHADOW20",
            dict(residual20),
        )
    )

    residual54 = one(
        conn,
        """
        SELECT bookid, subfamily, likely_speech_act, plausible_human_reading,
               confidence_tier, source_bridge_id, anchor_ids_json,
               support_level, blocked_claims_json, blocked_overreach,
               falsifier, next_probe, promotion_status, evidence_json
        FROM human_residual_shadow_v1_items
        WHERE run_id=? AND bookid='54'
        """,
        (latest_residual_shadow,),
    )
    items.append(
        evidence_item(
            "residual-shadow:54-absence",
            "control_gate",
            "54",
            "human_residual_shadow_v1_items",
            "EXPECTED_SPECIFIC_PROBE_ONLY" if residual54 is None else str(residual54["promotion_status"]),
            "Book54 uses human_book54_pair_shadow_probe_v1 instead of generic residual shadow",
            "WARN_EXPECTED_BOOK54_RESIDUAL_ABSENCE",
            {
                "bookid": "54",
                "row_present": residual54 is not None,
                "row": dict(residual54) if residual54 is not None else None,
                "reason": "Book54 is represented by the specific Book54 pair probe and queue item.",
            },
        )
    )

    # Separate-pair and audit controls.
    for pair_id, support_class in (
        ("PAIR_25_39_FAST_BEIE", "CONTROL_ZERO_PAIR_MICROTEMPLATE"),
        ("PAIR_60_64_R20_LIVRN", "CONTROL_ZERO_PAIR_AUDIT"),
        ("C68_8_23_CONTEXT", "CONTROL_ZERO_PAIR_AUDIT"),
    ):
        row = one(
            conn,
            """
            SELECT pair_id, left_bookid, right_bookid, left_token_count,
                   right_token_count, lcs_len, lcs_ratio_shorter,
                   lcs_ratio_longer, alignment_status, next_action,
                   evidence_json, payload_json
            FROM zero_pair_alignment_items
            WHERE run_id=? AND pair_id=?
            """,
            (latest_zero_pair, pair_id),
        )
        if row is None:
            raise RuntimeError(f"missing zero-pair control {pair_id}")
        items.append(
            evidence_item(
                f"zero-pair-control:{pair_id}",
                "control_gate",
                f'{row["left_bookid"]},{row["right_bookid"]}',
                "zero_pair_alignment_items",
                str(row["alignment_status"]),
                str(row["pair_id"]),
                support_class,
                dict(row),
            )
        )

    for context_id, expected_books, support_class in (
        (
            "LOCAL_PAIR_25_39_FAST_BEIE_MICROTEMPLATE",
            ("25", "39"),
            "CONTROL_ZERO_LOCAL_CONTEXT_SEPARATE_PAIR",
        ),
        (
            "LOCAL_PAIR_60_64_R20_LIVRN_AUDIT",
            ("60", "64"),
            "CONTROL_ZERO_LOCAL_CONTEXT_AUDIT",
        ),
        (
            "LOCAL_PAIR_8_23_C68_CONTEXT_ALIGNMENT",
            ("8", "23"),
            "CONTROL_ZERO_LOCAL_CONTEXT_AUDIT",
        ),
    ):
        for bookid in expected_books:
            local = one(
                conn,
                """
                SELECT context_id, bookid, source_pair_id, policy_status,
                       decision, confidence, functional_label,
                       lexical_gloss_allowed, reason, next_action,
                       evidence_json
                FROM zero_pair_local_context_gate_items
                WHERE run_id=? AND context_id=? AND bookid=?
                """,
                (latest_zero_pair_local, context_id, bookid),
            )
            if local is None:
                raise RuntimeError(f"missing local context control {context_id}/{bookid}")
            items.append(
                evidence_item(
                    f"zero-local-control:{context_id}:{bookid}",
                    "control_gate",
                    bookid,
                    "zero_pair_local_context_gate_items",
                    str(local["decision"]),
                    str(local["functional_label"]),
                    support_class,
                    dict(local),
                )
            )

    for bookid in ("25", "39"):
        residual = one(
            conn,
            """
            SELECT bookid, subfamily, likely_speech_act, plausible_human_reading,
                   confidence_tier, source_bridge_id, anchor_ids_json,
                   support_level, blocked_claims_json, blocked_overreach,
                   falsifier, next_probe, promotion_status, evidence_json
            FROM human_residual_shadow_v1_items
            WHERE run_id=? AND bookid=?
            """,
            (latest_residual_shadow, bookid),
        )
        if residual is None:
            raise RuntimeError(f"missing residual shadow control for book {bookid}")
        items.append(
            evidence_item(
                f"residual-shadow-control:{bookid}",
                "control_gate",
                bookid,
                "human_residual_shadow_v1_items",
                str(residual["promotion_status"]),
                str(residual["likely_speech_act"]),
                "CONTROL_RESIDUAL_SHADOW_SEPARATE_PAIR",
                dict(residual),
            )
        )

    add_zero_absence_controls(
        conn,
        items,
        latest_zero_operator,
        latest_zero_boundary_feature,
        latest_zero_recurrence,
        latest_zero_segment_cluster,
    )

    context = {
        "queue_run_id": queue_run_id,
        "latest_row0_run_id": latest_row0,
        "latest_pair_probe_run_id": latest_pair_probe,
        "latest_zero_pair_run_id": latest_zero_pair,
        "latest_zero_pair_local_run_id": latest_zero_pair_local,
        "latest_residual_bridge_run_id": latest_residual_bridge,
        "latest_residual_shadow_run_id": latest_residual_shadow,
        "latest_zero_operator_run_id": latest_zero_operator,
        "latest_zero_boundary_feature_run_id": latest_zero_boundary_feature,
        "latest_zero_recurrence_run_id": latest_zero_recurrence,
        "latest_zero_segment_cluster_run_id": latest_zero_segment_cluster,
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
        "20": "Longer local-pair member with left prefix NEIEBNB before the shared spine; used as control/context, not as a gloss.",
        "54": "Candidate shorter local-pair member with minimal prefix F, shared spine LTFNTFEIFAIFAINIIETNEEIVN, and tail ALN.",
        "25_39": "Separate FAST/BEIE microtemplate pair; useful as a local-pair control, not evidence that Book54 has the same meaning.",
        "zero_controls": "No zero-operator, recurrent zero-context, or zero-boundary cluster evidence may be imported as a semantic reading for Book20/54.",
    }

    for item in items:
        support = str(item["support_class"])
        status = str(item["status"])
        evidence = evidence_dict(item)
        if support == "QUEUE_CANDIDATE":
            continue

        if support.startswith("POSITIVE_"):
            ok = False
            if support == "POSITIVE_ROW0_SHARED_SPINE":
                ok = (
                    status == "SHARED_SPINE_PRESENT"
                    and bool(evidence.get("shared_block_in_20"))
                    and bool(evidence.get("shared_block_in_54"))
                    and evidence.get("book20_prefix") == "NEIEBNB"
                    and evidence.get("book20_suffix") == ""
                    and evidence.get("book54_prefix") == "F"
                    and evidence.get("book54_suffix") == "ALN"
                )
            elif support == "POSITIVE_BOOK54_PAIR_PROBE":
                inner = inner_json(evidence, "evidence_json")
                ok = (
                    evidence.get("shared_block") == SHARED_BLOCK
                    and int(inner.get("lcs_len", 0)) == 25
                    and float(inner.get("lcs_ratio_shorter", 0.0)) >= 0.86
                    and status
                    in {
                        "LONGER_PAIR_MEMBER_WITH_LEFT_PREFIX",
                        "SHORTER_PAIR_MEMBER_WITH_MINIMAL_PREFIX_AND_EXTRA_TAIL",
                    }
                )
            elif support == "POSITIVE_ZERO_PAIR_ALIGNMENT":
                inner = inner_json(evidence, "evidence_json")
                ok = (
                    status == "PAIR_TRUNCATION_ALIGNMENT_READY"
                    and int(evidence.get("lcs_len", 0)) == 25
                    and float(evidence.get("lcs_ratio_shorter", 0.0)) >= 0.86
                    and inner.get("gloss_allowed") is False
                )
            elif support == "POSITIVE_ZERO_LOCAL_CONTEXT":
                ok = (
                    status == "ZERO_PAIR_LOCAL_CONTEXT_NO_GLOSS"
                    and evidence.get("policy_status") == "LOCAL_CONTEXT_READY"
                    and int(evidence.get("lexical_gloss_allowed", 1)) == 0
                )
            elif support == "POSITIVE_RESIDUAL_BRIDGE":
                ok = (
                    status == "STRUCTURAL_LOCAL_PAIR_NO_GLOSS"
                    and "Do not promote pair alignments" in str(evidence.get("blocked_overreach"))
                )
            elif support == "POSITIVE_RESIDUAL_SHADOW20":
                ok = (
                    status == "NOT_PROMOTED"
                    and evidence.get("support_level") == "STRUCTURAL_LOCAL_PAIR_NO_GLOSS"
                    and evidence.get("subfamily") == "LOCAL_PAIR_20_54_TRUNCATION"
                )
            if ok:
                positive_pass += 1
            else:
                positive_fail += 1
            continue

        if support == "CONTROL_ZERO_PAIR_MICROTEMPLATE":
            inner = inner_json(evidence, "evidence_json")
            if status == "PAIR_MICROTEMPLATE_READY" and inner.get("gloss_allowed") is False:
                control_pass += 1
            else:
                control_fail += 1
        elif support == "CONTROL_ZERO_PAIR_AUDIT":
            inner = inner_json(evidence, "evidence_json")
            if status in {"PAIR_AUDIT_ONLY", "PAIR_CONTEXT_ALIGNMENT"} and inner.get("gloss_allowed") is False:
                control_pass += 1
            else:
                control_fail += 1
        elif support == "CONTROL_ZERO_LOCAL_CONTEXT_SEPARATE_PAIR":
            if (
                status == "ZERO_PAIR_LOCAL_CONTEXT_NO_GLOSS"
                and evidence.get("policy_status") == "LOCAL_CONTEXT_READY"
                and int(evidence.get("lexical_gloss_allowed", 1)) == 0
            ):
                control_pass += 1
            else:
                control_fail += 1
        elif support == "CONTROL_ZERO_LOCAL_CONTEXT_AUDIT":
            if status == "ZERO_PAIR_AUDIT_ONLY_NO_PROMOTION" and int(evidence.get("lexical_gloss_allowed", 1)) == 0:
                control_pass += 1
            else:
                control_fail += 1
        elif support == "CONTROL_RESIDUAL_SHADOW_SEPARATE_PAIR":
            if (
                status == "NOT_PROMOTED"
                and evidence.get("support_level") == "STRUCTURAL_LOCAL_PAIR_NO_GLOSS"
                and evidence.get("subfamily") == "LOCAL_PAIR_25_39_FAST_BEIE"
            ):
                control_pass += 1
            else:
                control_fail += 1
        elif support == "CONTROL_ZERO_OPERATOR_ABSENT":
            if status == "ABSENT_FOR_CANDIDATE_PAIR" and int(evidence.get("row_count", 1)) == 0:
                control_pass += 1
            else:
                control_fail += 1
        elif support == "CONTROL_ZERO_CONTEXT_ABSENT":
            if status == "ABSENT_FOR_CANDIDATE_PAIR" and int(evidence.get("touching_row_count", 1)) == 0:
                control_pass += 1
            else:
                control_fail += 1
        elif support == "WARN_EXPECTED_BOOK54_RESIDUAL_ABSENCE":
            if status == "EXPECTED_SPECIFIC_PROBE_ONLY" and evidence.get("row_present") is False:
                control_warn += 1
            else:
                control_fail += 1
        else:
            control_fail += 1

    if positive_fail == 0 and control_fail == 0:
        decision = "PROMOTE_HUMAN_FUNCTIONAL_LOCAL_PAIR_LABEL_NO_GLOSS_SHARED_SPINE_ONLY"
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
        INSERT INTO human_promotion_pkg5_book54_local_pair_falsification_v1_runs
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
                    "pair_books": list(PAIR_BOOKS),
                    "shared_block": SHARED_BLOCK,
                    "principle": "promote a local-pair shared-spine label only; do not promote a word gloss, zero/taboo semantics, or sentence translation",
                    "scope_split": "Book54 is the candidate shorter member; Book20 is the longer local-pair control/context.",
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
            INSERT INTO human_promotion_pkg5_book54_local_pair_falsification_v1_evidence
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
        "Book54 is the shorter member of a local pair with Book20. It preserves "
        "the shared spine LTFNTFEIFAIFAINIIETNEEIVN with minimal prefix F and "
        "tail ALN, while Book20 preserves the same spine after the longer prefix "
        "NEIEBNB. This promotes only a human-functional local-pair/shared-spine "
        "label, not a plaintext translation."
    )
    blocked_claims = [
        "Do not translate LTFNTFEIFAIFAINIIETNEEIVN as a standalone word or phrase.",
        "Do not translate F, ALN, or NEIEBNB from this package.",
        "Do not infer zero/taboo semantics; Book20/54 have no promoted zero-operator or recurrent zero-context support.",
        "Do not treat truncation alignment as a plaintext abbreviation.",
        "Do not collapse the separate Book25/39 FAST/BEIE microtemplate into the Book20/54 pair.",
        "Do not promote Book20 or Book54 as sentence-level translations from this evidence.",
    ]
    conn.execute(
        """
        INSERT INTO human_promotion_pkg5_book54_local_pair_falsification_v1_decisions
        (run_id, decision_id, scope, decision, human_functional_reading,
         subtype_notes_json, blocked_claims_json, next_action, evidence_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            "PKG5_BOOK54_LOCAL_PAIR_SHARED_SPINE_LABEL",
            "Book54 with Book20 local-pair context only",
            decision,
            human_functional_reading,
            json.dumps(subtype_notes, ensure_ascii=False, sort_keys=True),
            json.dumps(blocked_claims, ensure_ascii=False),
            "Use as the fifth promoted human-functional package; keep searching for independent anchors before any lexical/prose claim.",
            json.dumps(
                {
                    "candidate_books": list(CANDIDATE_BOOKS),
                    "pair_books": list(PAIR_BOOKS),
                    "positive_required_sources": [
                        "row0_variant_book_tokens",
                        "human_book54_pair_shadow_probe_v1_items",
                        "zero_pair_alignment_items",
                        "zero_pair_local_context_gate_items",
                        "human_residual_bridge_v1_items",
                        "human_residual_shadow_v1_items",
                    ],
                    "control_sources": [
                        "zero_pair_alignment_items",
                        "zero_pair_local_context_gate_items",
                        "human_residual_shadow_v1_items",
                        "zero_operator_typed_exit_gate_v1_book_decisions",
                        "zero_context_boundary_feature_gate_items",
                        "zero_context_recurrence_scorer_items",
                        "zero_boundary_segment_cluster_v2_items",
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
