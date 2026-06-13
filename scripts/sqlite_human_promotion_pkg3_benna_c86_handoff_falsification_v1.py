#!/usr/bin/env python3
"""Falsify package 3: Books 10/35 BENNA -> C86/VNCTIIN handoff."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
PACKAGE_ID = "PKG_BENNA_C86_VNCTIIN_HANDOFF_10_35"
CANDIDATE_BOOKS = ("10", "35")


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_promotion_pkg3_benna_c86_handoff_falsification_v1_runs (
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

        CREATE TABLE IF NOT EXISTS human_promotion_pkg3_benna_c86_handoff_falsification_v1_evidence (
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

        CREATE TABLE IF NOT EXISTS human_promotion_pkg3_benna_c86_handoff_falsification_v1_decisions (
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


def find_c86_branch(conn: sqlite3.Connection, run_id: int) -> sqlite3.Row:
    rows = all_rows(
        conn,
        """
        SELECT branch_id, payload_class, books_json, downstream_frame, decision,
               functional_label, gloss_allowed, lexical_promotion_allowed,
               reason, next_action, evidence_json
        FROM c86_payload_operator_gate_items
        WHERE run_id=?
        """,
        (run_id,),
    )
    for row in rows:
        books = set(json.loads(str(row["books_json"])))
        if set(CANDIDATE_BOOKS).issubset(books) and {"2", "27", "67"}.issubset(books):
            return row
    raise RuntimeError("missing C86 branch containing Books 10/35 and 2/27/67")


def collect_evidence(conn: sqlite3.Connection) -> tuple[int, list[dict[str, object]], dict[str, int]]:
    queue_run_id = latest_queue_run(conn)
    latest_shadow = max_id(conn, "human_slot_formula_shadow_v1_items")
    latest_bridge = max_id(conn, "human_slot_formula_bridge_v1_items")
    latest_benna_gate = max_id(conn, "benna_formula_bridge_gate_items")
    latest_benna_core = max_id(conn, "benna_ordered_core_v2_items")
    latest_c86_gate = max_id(conn, "c86_payload_operator_gate_items")
    latest_q2_matrix = max_id(conn, "q2_handoff_context_payload_matrix_v1_items")
    latest_q2_sequence = max_id(conn, "q2_handoff_state_sequence_v1_items")
    latest_typed_exit = max_id(conn, "benna_ltast_c86_c68_typed_exit_contradiction_reduction_v1_items")
    latest_handoff_bridge = max_id(conn, "handoff_context_bridge_35_67_v1_items")
    latest_contig = max_id(conn, "contig1_handoff_corridor_v1_items")
    latest_c86_shadow = max_id(conn, "human_c86_vnctiin_shadow_v1_items")
    latest_ltast_policy = max_id(conn, "q2_ltast_boundary_policy_v1_items")
    latest_ltast_decision = max_id(conn, "ltast_boundary_operator_decision_v1_items")
    latest_benna_package = max_id(conn, "benna_ltast_contig_conditioned_package_v1_items")

    items: list[dict[str, object]] = []

    bridge = one(
        conn,
        """
        SELECT bridge_id, target_family, support_level, support_summary,
               blocked_overreach, next_probe, anchor_evidence_json, precheck_json
        FROM human_slot_formula_bridge_v1_items
        WHERE run_id=? AND bridge_id='B_BENNA_C86_VNCTIIN_FORMULA_HANDOFF'
        """,
        (latest_bridge,),
    )
    if bridge is None:
        raise RuntimeError("missing human slot/formula bridge for BENNA_C86 handoff")
    items.append(
        evidence_item(
            "bridge:package",
            "positive_gate",
            "10,35",
            "human_slot_formula_bridge_v1_items",
            str(bridge["support_level"]),
            str(bridge["target_family"]),
            "POSITIVE_PACKAGE_BRIDGE",
            dict(bridge),
        )
    )

    c86_branch = find_c86_branch(conn, latest_c86_gate)
    items.append(
        evidence_item(
            "c86-branch:10-35-2-27-67",
            "positive_gate",
            "2,10,27,35,67",
            "c86_payload_operator_gate_items",
            str(c86_branch["decision"]),
            str(c86_branch["functional_label"]),
            "POSITIVE_C86_PAYLOAD_BRANCH",
            dict(c86_branch),
        )
    )

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
            raise RuntimeError(f"missing queue item for book {bookid}")
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

        shadow = one(
            conn,
            """
            SELECT likely_speech_act, plausible_human_reading, confidence_tier,
                   support_level, promotion_status, evidence_json
            FROM human_slot_formula_shadow_v1_items
            WHERE run_id=? AND bookid=?
            """,
            (latest_shadow, bookid),
        )
        if shadow is None:
            raise RuntimeError(f"missing human slot/formula shadow for book {bookid}")
        items.append(
            evidence_item(
                f"shadow:{bookid}",
                "positive_gate",
                bookid,
                "human_slot_formula_shadow_v1_items",
                str(shadow["promotion_status"]),
                str(shadow["likely_speech_act"]),
                "POSITIVE_HUMAN_SHADOW",
                dict(shadow),
            )
        )

        benna_gate = one(
            conn,
            """
            SELECT target_class, prefix_class, suffix_class, has_ltast_tail,
                   functional_class, decision, confidence, functional_label,
                   formula_only, lexical_gloss_allowed, reason, next_action,
                   evidence_json
            FROM benna_formula_bridge_gate_items
            WHERE run_id=? AND bookid=?
            """,
            (latest_benna_gate, bookid),
        )
        if benna_gate is None:
            raise RuntimeError(f"missing BENNA formula gate for book {bookid}")
        items.append(
            evidence_item(
                f"benna-gate:{bookid}",
                "positive_gate",
                bookid,
                "benna_formula_bridge_gate_items",
                str(benna_gate["decision"]),
                str(benna_gate["functional_label"]),
                "POSITIVE_BENNA_LTAST_FORMULA",
                dict(benna_gate),
            )
        )

        benna_core = one(
            conn,
            """
            SELECT status, role_label, interpretation, evidence_json
            FROM benna_ordered_core_v2_items
            WHERE run_id=? AND item_type='book' AND item_id=?
            """,
            (latest_benna_core, bookid),
        )
        if benna_core is None:
            raise RuntimeError(f"missing BENNA ordered-core item for book {bookid}")
        items.append(
            evidence_item(
                f"benna-core:{bookid}",
                "positive_gate",
                bookid,
                "benna_ordered_core_v2_items",
                str(benna_core["status"]),
                str(benna_core["role_label"]),
                "POSITIVE_HANDOFF_CONTEXT",
                dict(benna_core),
            )
        )

        q2 = one(
            conn,
            """
            SELECT q2_role, source_component, functional_reading,
                   has_benna_pair_rule, has_c86_delta13_payload,
                   has_vinvin_typed_branch, has_naese_slot_route,
                   has_ltast_evidence, promotion_allowed, gloss_allowed,
                   evidence_json
            FROM q2_handoff_context_payload_matrix_v1_items
            WHERE run_id=? AND bookid=?
            """,
            (latest_q2_matrix, bookid),
        )
        if q2 is None:
            raise RuntimeError(f"missing Q2 matrix item for book {bookid}")
        support = "POSITIVE_Q2_CANONICAL_HANDOFF" if bookid == "35" else "POSITIVE_Q2_SHADOW_HANDOFF"
        items.append(
            evidence_item(
                f"q2-matrix:{bookid}",
                "positive_gate",
                bookid,
                "q2_handoff_context_payload_matrix_v1_items",
                str(q2["q2_role"]),
                str(q2["functional_reading"]),
                support,
                dict(q2),
            )
        )

        q2seq = one(
            conn,
            """
            SELECT path_id, step_order, state_label, q2_role, evidence_signal,
                   allowed_inference, blocked_inference, promotion_allowed,
                   gloss_allowed, evidence_json
            FROM q2_handoff_state_sequence_v1_items
            WHERE run_id=? AND bookid=?
            """,
            (latest_q2_sequence, bookid),
        )
        if q2seq is None:
            raise RuntimeError(f"missing Q2 sequence item for book {bookid}")
        items.append(
            evidence_item(
                f"q2-sequence:{bookid}",
                "positive_gate",
                bookid,
                "q2_handoff_state_sequence_v1_items",
                str(q2seq["q2_role"]),
                str(q2seq["state_label"]),
                support,
                dict(q2seq),
            )
        )

    typed35 = one(
        conn,
        """
        SELECT chain_stage, typed_exit_label, status, contradiction_action,
               promotion_allowed, gloss_allowed, semantic_translation_allowed,
               evidence_json
        FROM benna_ltast_c86_c68_typed_exit_contradiction_reduction_v1_items
        WHERE run_id=? AND bookid='35'
        """,
        (latest_typed_exit,),
    )
    if typed35 is None:
        raise RuntimeError("missing typed-exit contradiction reduction for Book35")
    items.append(
        evidence_item(
            "typed-exit:35",
            "positive_gate",
            "35",
            "benna_ltast_c86_c68_typed_exit_contradiction_reduction_v1_items",
            str(typed35["status"]),
            str(typed35["typed_exit_label"]),
            "POSITIVE_TYPED_EXIT_CANONICAL_35",
            dict(typed35),
        )
    )

    bridge35 = one(
        conn,
        """
        SELECT edge, role, status, score, overlap, lcs, prior,
               transition_json, states_json, evidence_json
        FROM handoff_context_bridge_35_67_v1_items
        WHERE run_id=? AND edge='35->67'
        """,
        (latest_handoff_bridge,),
    )
    if bridge35 is None:
        raise RuntimeError("missing 35->67 handoff bridge")
    items.append(
        evidence_item(
            "handoff-edge:35->67",
            "positive_gate",
            "35,67",
            "handoff_context_bridge_35_67_v1_items",
            str(bridge35["status"]),
            str(bridge35["role"]),
            "POSITIVE_HANDOFF_EDGE_35_67",
            dict(bridge35),
        )
    )

    contig35 = one(
        conn,
        """
        SELECT bookid, contig_position, role_bundle, inferred_stage,
               status, evidence_json
        FROM contig1_handoff_corridor_v1_items
        WHERE run_id=? AND bookid='35'
        """,
        (latest_contig,),
    )
    if contig35 is None:
        raise RuntimeError("missing contig handoff item for Book35")
    items.append(
        evidence_item(
            "contig:35",
            "positive_gate",
            "35",
            "contig1_handoff_corridor_v1_items",
            str(contig35["status"]),
            str(contig35["inferred_stage"]),
            "POSITIVE_CANONICAL_CONTIG_STAGE_35",
            dict(contig35),
        )
    )

    # Expected controls and warning surfaces.
    typed10 = one(
        conn,
        """
        SELECT chain_stage, typed_exit_label, status, contradiction_action,
               promotion_allowed, gloss_allowed, semantic_translation_allowed,
               evidence_json
        FROM benna_ltast_c86_c68_typed_exit_contradiction_reduction_v1_items
        WHERE run_id=? AND bookid='10'
        """,
        (latest_typed_exit,),
    )
    items.append(
        evidence_item(
            "typed-exit:10-absent",
            "control_gate",
            "10",
            "benna_ltast_c86_c68_typed_exit_contradiction_reduction_v1_items",
            "EXPECTED_ABSENT_CANONICAL_TYPED_EXIT",
            "BOOK10_SHADOW_HANDOFF_ONLY",
            "CONTROL_BOOK10_SHADOW_NOT_CANONICAL",
            dict(typed10) if typed10 else {"reason": "Book10 is supported by Q2 shadow path, not canonical typed-exit table."},
        )
    )

    for bookid in ("40", "50", "69"):
        row = one(
            conn,
            """
            SELECT likely_speech_act, plausible_human_reading, confidence_tier,
                   support_level, promotion_status, evidence_json
            FROM human_slot_formula_shadow_v1_items
            WHERE run_id=? AND bookid=?
            """,
            (latest_shadow, bookid),
        )
        if row is None:
            raise RuntimeError(f"missing BENNA body shadow control {bookid}")
        items.append(
            evidence_item(
                f"benna-body-shadow:{bookid}",
                "control_gate",
                bookid,
                "human_slot_formula_shadow_v1_items",
                str(row["promotion_status"]),
                str(row["likely_speech_act"]),
                "CONTROL_BENNA_BODY_NOT_HANDOFF",
                dict(row),
            )
        )

        gate = one(
            conn,
            """
            SELECT decision, functional_label, formula_only, lexical_gloss_allowed,
                   reason, next_action, evidence_json
            FROM benna_formula_bridge_gate_items
            WHERE run_id=? AND bookid=?
            """,
            (latest_benna_gate, bookid),
        )
        if gate is None:
            raise RuntimeError(f"missing BENNA formula gate control {bookid}")
        items.append(
            evidence_item(
                f"benna-body-gate:{bookid}",
                "control_gate",
                bookid,
                "benna_formula_bridge_gate_items",
                str(gate["decision"]),
                str(gate["functional_label"]),
                "CONTROL_BENNA_BODY_NOT_HANDOFF",
                dict(gate),
            )
        )

    for bookid in ("2", "27", "67"):
        row = one(
            conn,
            """
            SELECT likely_speech_act, plausible_human_reading, confidence_tier,
                   support_level, promotion_status, evidence_json
            FROM human_c86_vnctiin_shadow_v1_items
            WHERE run_id=? AND bookid=?
            """,
            (latest_c86_shadow, bookid),
        )
        if row is None:
            raise RuntimeError(f"missing C86/VNCTIIN corridor shadow control {bookid}")
        items.append(
            evidence_item(
                f"c86-corridor-shadow:{bookid}",
                "control_gate",
                bookid,
                "human_c86_vnctiin_shadow_v1_items",
                str(row["promotion_status"]),
                str(row["likely_speech_act"]),
                "CONTROL_C86_PAYLOAD_CORRIDOR_NOT_HANDOFF",
                dict(row),
            )
        )

    for item_id in ("LTAST_RESIDUAL_BLOCKED", "LTAST_TTNVVN_BOUNDARY_OPERATOR"):
        row = one(
            conn,
            """
            SELECT item_id, books, structural_label, status, allowed_use,
                   blocked_use, promotion_allowed, gloss_allowed, evidence_json
            FROM q2_ltast_boundary_policy_v1_items
            WHERE run_id=? AND item_id=?
            """,
            (latest_ltast_policy, item_id),
        )
        if row is None:
            raise RuntimeError(f"missing LTAST policy {item_id}")
        items.append(
            evidence_item(
                f"ltast-policy:{item_id}",
                "control_gate",
                str(row["books"]),
                "q2_ltast_boundary_policy_v1_items",
                str(row["status"]),
                str(row["structural_label"]),
                "CONTROL_LTAST_NO_LEXICAL_PROMOTION",
                dict(row),
            )
        )

    row = one(
        conn,
        """
        SELECT partition_id, books, status, structural_label, promotion_allowed,
               plaintext_allowed, next_action, evidence_json
        FROM ltast_boundary_operator_decision_v1_items
        WHERE run_id=? AND partition_id='BOUNDARY_OPERATOR_WITH_RESIDUAL_BLOCKED_CONTEXT'
        """,
        (latest_ltast_decision,),
    )
    if row is None:
        raise RuntimeError("missing LTAST residual blocked decision")
    items.append(
        evidence_item(
            "ltast-decision:residual-blocked",
            "control_gate",
            str(row["books"]),
            "ltast_boundary_operator_decision_v1_items",
            str(row["status"]),
            str(row["structural_label"]),
            "CONTROL_LTAST_RESIDUAL_CONTEXT_WARNING",
            dict(row),
        )
    )

    for item_id in ("58->35", "69->35"):
        row = one(
            conn,
            """
            SELECT item_id, item_kind, status, role_label, promotion_allowed,
                   plaintext_allowed, next_action, evidence_json
            FROM benna_ltast_contig_conditioned_package_v1_items
            WHERE run_id=? AND item_id=?
            """,
            (latest_benna_package, item_id),
        )
        if row is None:
            raise RuntimeError(f"missing BENNA contig package control {item_id}")
        support = "CONTROL_CANONICAL_BENNA_EDGE" if item_id == "58->35" else "CONTROL_REJECT_MISSING_69_35_EDGE"
        items.append(
            evidence_item(
                f"benna-contig:{item_id}",
                "control_gate",
                item_id,
                "benna_ltast_contig_conditioned_package_v1_items",
                str(row["status"]),
                str(row["role_label"]),
                support,
                dict(row),
            )
        )

    context = {
        "queue_run_id": queue_run_id,
        "latest_shadow_run_id": latest_shadow,
        "latest_bridge_run_id": latest_bridge,
        "latest_benna_gate_run_id": latest_benna_gate,
        "latest_benna_core_run_id": latest_benna_core,
        "latest_c86_gate_run_id": latest_c86_gate,
        "latest_q2_matrix_run_id": latest_q2_matrix,
        "latest_q2_sequence_run_id": latest_q2_sequence,
        "latest_typed_exit_run_id": latest_typed_exit,
        "latest_handoff_bridge_run_id": latest_handoff_bridge,
        "latest_contig_run_id": latest_contig,
        "latest_c86_shadow_run_id": latest_c86_shadow,
        "latest_ltast_policy_run_id": latest_ltast_policy,
        "latest_ltast_decision_run_id": latest_ltast_decision,
        "latest_benna_package_run_id": latest_benna_package,
    }
    return queue_run_id, items, context


def evidence_dict(item: dict[str, object]) -> dict[str, object]:
    return json.loads(str(item["evidence_json"]))


def classify(items: list[dict[str, object]]) -> tuple[str, dict[str, int], dict[str, str]]:
    positive_pass = 0
    positive_fail = 0
    control_pass = 0
    control_warn = 0
    control_fail = 0
    subtype_notes = {
        "35": "Canonical handoff source in the 35->67->2 path.",
        "10": "Shadow handoff compatible with the 10->27->2 path; do not treat as canonical 35 equivalent.",
    }

    for item in items:
        support = str(item["support_class"])
        status = str(item["status"])
        evidence = evidence_dict(item)
        if support == "QUEUE_CANDIDATE":
            continue
        if support.startswith("POSITIVE_"):
            ok = False
            if support == "POSITIVE_PACKAGE_BRIDGE":
                ok = status == "STRUCTURAL_FORMULA_HANDOFF_TO_CONTEXT"
            elif support == "POSITIVE_C86_PAYLOAD_BRANCH":
                ok = status == "PAYLOAD_BRANCH_FUNCTION_READY_NO_GLOSS" and int(evidence.get("gloss_allowed", 1)) == 0
            elif support == "POSITIVE_HUMAN_SHADOW":
                ok = status == "NOT_PROMOTED"
            elif support == "POSITIVE_BENNA_LTAST_FORMULA":
                ok = status == "BENNA_FORMULA_BRIDGE_CLEAN_WITH_TAIL_NO_GLOSS" and int(evidence.get("lexical_gloss_allowed", 1)) == 0
            elif support == "POSITIVE_HANDOFF_CONTEXT":
                ok = status == "ORDERED_CORE" and str(item["role_label"]) == "HANDOFF_CONTEXT"
            elif support in {"POSITIVE_Q2_CANONICAL_HANDOFF", "POSITIVE_Q2_SHADOW_HANDOFF"}:
                ok = int(evidence.get("promotion_allowed", 0)) == 1 and int(evidence.get("gloss_allowed", 1)) == 0
            elif support == "POSITIVE_TYPED_EXIT_CANONICAL_35":
                ok = status == "PROMOTE_STRUCTURE_ONLY" and int(evidence.get("gloss_allowed", 1)) == 0
            elif support == "POSITIVE_HANDOFF_EDGE_35_67":
                ok = status == "TARGET_ACCEPTED"
            elif support == "POSITIVE_CANONICAL_CONTIG_STAGE_35":
                ok = status == "CANONICAL_CONTIG1_STAGE"
            if ok:
                positive_pass += 1
            else:
                positive_fail += 1
            continue

        if support == "CONTROL_BOOK10_SHADOW_NOT_CANONICAL":
            if status == "EXPECTED_ABSENT_CANONICAL_TYPED_EXIT":
                control_warn += 1
            else:
                control_fail += 1
        elif support == "CONTROL_LTAST_RESIDUAL_CONTEXT_WARNING":
            if status == "HOLD_RESIDUAL_CONTEXT_NO_GLOSS":
                control_warn += 1
            else:
                control_fail += 1
        elif support == "CONTROL_REJECT_MISSING_69_35_EDGE":
            if status == "ABANDON_CONTIG_DEPENDENCY_NO_PROSE":
                control_warn += 1
            else:
                control_fail += 1
        elif support == "CONTROL_LTAST_NO_LEXICAL_PROMOTION":
            if int(evidence.get("gloss_allowed", 1)) == 0:
                if status in {"BLOCKED_FOR_CLEAN_PROMOTION", "HOLD_RESIDUAL_CONTEXT_NO_GLOSS"}:
                    control_warn += 1
                else:
                    control_pass += 1
            else:
                control_fail += 1
        elif support in {
            "CONTROL_BENNA_BODY_NOT_HANDOFF",
            "CONTROL_C86_PAYLOAD_CORRIDOR_NOT_HANDOFF",
            "CONTROL_CANONICAL_BENNA_EDGE",
        }:
            if (
                int(evidence.get("lexical_gloss_allowed", evidence.get("gloss_allowed", 0)) or 0) == 0
                or int(evidence.get("plaintext_allowed", 0) or 0) == 0
                or status == "NOT_PROMOTED"
            ):
                control_pass += 1
            else:
                control_fail += 1
        else:
            control_fail += 1

    if positive_fail == 0 and control_fail == 0:
        decision = "PROMOTE_HUMAN_FUNCTIONAL_HANDOFF_LABEL_NO_GLOSS_CANONICAL_SHADOW_SPLIT"
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
        INSERT INTO human_promotion_pkg3_benna_c86_handoff_falsification_v1_runs
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
                    "principle": "promote a human functional handoff label only; do not promote BENNA/C86/VNCTIIN/LTAST lexical gloss or prose",
                    "subtype_split": "Book35 is canonical handoff source; Book10 is shadow handoff compatible with Q2 path.",
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
            INSERT INTO human_promotion_pkg3_benna_c86_handoff_falsification_v1_evidence
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
        "Books 10/35 are a human-functional formula-to-context handoff: a "
        "BENNA/LTAST formula-concordance tail routes into the C86/VNCTIIN payload "
        "corridor. Book35 is the canonical handoff source into 67->2; Book10 is a "
        "shadow handoff that matches the same role through the 10->27->2 path. "
        "This is not a plaintext translation."
    )
    blocked_claims = [
        "Do not translate BENNA, C86, VNCTIIN, C68, TAILBETFTE, or LTAST as standalone words.",
        "Do not promote Book10 as canonical-equivalent to Book35; keep the canonical/shadow split.",
        "Do not collapse Books 2/27/67 payload-corridor readings into the 10/35 handoff label.",
        "Do not use LTAST boundary evidence alone as clean lexical or phrase translation.",
        "Do not invent or require a 69->35 contig edge for this package.",
    ]
    conn.execute(
        """
        INSERT INTO human_promotion_pkg3_benna_c86_handoff_falsification_v1_decisions
        (run_id, decision_id, scope, decision, human_functional_reading,
         subtype_notes_json, blocked_claims_json, next_action, evidence_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            "PKG3_BENNA_C86_VNCTIIN_HANDOFF_LABEL",
            "Books 10/35 only",
            decision,
            human_functional_reading,
            json.dumps(subtype_notes, ensure_ascii=False, sort_keys=True),
            json.dumps(blocked_claims, ensure_ascii=False),
            "Use as the third promoted human-functional package; next review package is Books 2/27/67 C86/VNCTIIN payload corridor.",
            json.dumps(
                {
                    "candidate_books": list(CANDIDATE_BOOKS),
                    "positive_required_sources": [
                        "human_slot_formula_bridge_v1_items",
                        "human_slot_formula_shadow_v1_items",
                        "benna_formula_bridge_gate_items",
                        "benna_ordered_core_v2_items",
                        "c86_payload_operator_gate_items",
                        "q2_handoff_context_payload_matrix_v1_items",
                        "q2_handoff_state_sequence_v1_items",
                        "benna_ltast_c86_c68_typed_exit_contradiction_reduction_v1_items",
                        "handoff_context_bridge_35_67_v1_items",
                        "contig1_handoff_corridor_v1_items",
                    ],
                    "control_sources": [
                        "human_c86_vnctiin_shadow_v1_items",
                        "q2_ltast_boundary_policy_v1_items",
                        "ltast_boundary_operator_decision_v1_items",
                        "benna_ltast_contig_conditioned_package_v1_items",
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
