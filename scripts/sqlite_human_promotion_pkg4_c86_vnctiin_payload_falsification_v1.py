#!/usr/bin/env python3
"""Falsify package 4: Books 2/27/67 C86 -> VNCTIIN/C68 payload corridor."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
PACKAGE_ID = "PKG_C86_VNCTIIN_PAYLOAD_2_27_67"
CANDIDATE_BOOKS = ("2", "27", "67")


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_promotion_pkg4_c86_vnctiin_payload_falsification_v1_runs (
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

        CREATE TABLE IF NOT EXISTS human_promotion_pkg4_c86_vnctiin_payload_falsification_v1_evidence (
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

        CREATE TABLE IF NOT EXISTS human_promotion_pkg4_c86_vnctiin_payload_falsification_v1_decisions (
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


def find_branch(conn: sqlite3.Connection, run_id: int, branch_id: str) -> sqlite3.Row:
    row = one(
        conn,
        """
        SELECT branch_id, payload_class, books_json, downstream_frame, decision,
               functional_label, gloss_allowed, lexical_promotion_allowed,
               reason, next_action, evidence_json
        FROM c86_payload_operator_gate_items
        WHERE run_id=? AND branch_id=?
        """,
        (run_id, branch_id),
    )
    if row is None:
        raise RuntimeError(f"missing branch {branch_id}")
    return row


def collect_evidence(conn: sqlite3.Connection) -> tuple[int, list[dict[str, object]], dict[str, int]]:
    queue_run_id = latest_queue_run(conn)
    latest_bridge = max_id(conn, "human_c86_vnctiin_bridge_v1_items")
    latest_shadow = max_id(conn, "human_c86_vnctiin_shadow_v1_items")
    latest_c86_gate = max_id(conn, "c86_payload_operator_gate_items")
    latest_chain = max_id(conn, "c86_c68_naese_chain_probe_v1_items")
    latest_route = max_id(conn, "c86_naese_parallel_route_contrast_v3_items")
    latest_typed = max_id(conn, "benna_ltast_c86_c68_typed_exit_occurrence_v2_items")
    latest_q2_matrix = max_id(conn, "q2_handoff_context_payload_matrix_v1_items")
    latest_q2_sequence = max_id(conn, "q2_handoff_state_sequence_v1_items")
    latest_contig = max_id(conn, "contig1_handoff_corridor_v1_items")
    latest_naese = max_id(conn, "naese_slot_core_v1_items")
    latest_c68 = max_id(conn, "c68_fatct_slot_items")
    latest_vnctiin = max_id(conn, "vnctiin_context_frame_gate_items")

    items: list[dict[str, object]] = []

    bridge = one(
        conn,
        """
        SELECT bridge_id, target_family, support_level, support_summary,
               blocked_overreach, next_probe, anchor_evidence_json
        FROM human_c86_vnctiin_bridge_v1_items
        WHERE run_id=? AND bridge_id='B_C86_VNCTIIN_PAYLOAD_CORRIDOR'
        """,
        (latest_bridge,),
    )
    if bridge is None:
        raise RuntimeError("missing C86/VNCTIIN payload bridge")
    items.append(
        evidence_item(
            "bridge:package",
            "positive_gate",
            "2,27,67",
            "human_c86_vnctiin_bridge_v1_items",
            str(bridge["support_level"]),
            str(bridge["target_family"]),
            "POSITIVE_PACKAGE_BRIDGE",
            dict(bridge),
        )
    )

    c86_branch = find_branch(conn, latest_c86_gate, "C86_BRANCH_EVIEFIIN_TO_VN_C68_TIIN")
    items.append(
        evidence_item(
            "c86-branch:eviefiin-vn-c68-tiin",
            "positive_gate",
            "2,10,27,35,67",
            "c86_payload_operator_gate_items",
            str(c86_branch["decision"]),
            str(c86_branch["functional_label"]),
            "POSITIVE_C86_VNCTIIN_BRANCH",
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
            FROM human_c86_vnctiin_shadow_v1_items
            WHERE run_id=? AND bookid=?
            """,
            (latest_shadow, bookid),
        )
        if shadow is None:
            raise RuntimeError(f"missing human C86/VNCTIIN shadow for book {bookid}")
        items.append(
            evidence_item(
                f"shadow:{bookid}",
                "positive_gate",
                bookid,
                "human_c86_vnctiin_shadow_v1_items",
                str(shadow["promotion_status"]),
                str(shadow["likely_speech_act"]),
                "POSITIVE_HUMAN_SHADOW",
                dict(shadow),
            )
        )

        route_rows = all_rows(
            conn,
            """
            SELECT occurrence_key, pair_class, naese_category, route_decision,
                   promotion_allowed, gloss_allowed, semantic_translation_allowed,
                   evidence_json
            FROM c86_naese_parallel_route_contrast_v3_items
            WHERE run_id=? AND bookid=?
            ORDER BY occurrence_key
            """,
            (latest_route, bookid),
        )
        if not route_rows:
            raise RuntimeError(f"missing C86/NAESE route evidence for book {bookid}")
        for row in route_rows:
            support = "POSITIVE_ROUTE_OCCURRENCE" if int(row["promotion_allowed"]) == 1 else "CONTROL_ROUTE_OCCURRENCE_HELD"
            items.append(
                evidence_item(
                    f"route:{bookid}:{row['occurrence_key']}",
                    "positive_gate" if support.startswith("POSITIVE") else "control_gate",
                    bookid,
                    "c86_naese_parallel_route_contrast_v3_items",
                    str(row["route_decision"]),
                    str(row["pair_class"]),
                    support,
                    dict(row),
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
            raise RuntimeError(f"missing Q2 matrix row for book {bookid}")
        items.append(
            evidence_item(
                f"q2-matrix:{bookid}",
                "positive_gate",
                bookid,
                "q2_handoff_context_payload_matrix_v1_items",
                str(q2["q2_role"]),
                str(q2["functional_reading"]),
                "POSITIVE_Q2_ROUTE",
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
        if q2seq is not None:
            items.append(
                evidence_item(
                    f"q2-sequence:{bookid}",
                    "positive_gate",
                    bookid,
                    "q2_handoff_state_sequence_v1_items",
                    str(q2seq["q2_role"]),
                    str(q2seq["state_label"]),
                    "POSITIVE_Q2_ROUTE",
                    dict(q2seq),
                )
            )

        vn = one(
            conn,
            """
            SELECT frame_key, occurrence_role, edge_refs_json, decision,
                   confidence, functional_label, global_c68_gloss_allowed,
                   lexical_gloss_allowed, reason, next_action, evidence_json
            FROM vnctiin_context_frame_gate_items
            WHERE run_id=? AND bookid=?
            """,
            (latest_vnctiin, bookid),
        )
        if vn is None:
            raise RuntimeError(f"missing VNCTIIN frame evidence for book {bookid}")
        items.append(
            evidence_item(
                f"vnctiin-frame:{bookid}",
                "positive_gate",
                bookid,
                "vnctiin_context_frame_gate_items",
                str(vn["decision"]),
                str(vn["functional_label"]),
                "POSITIVE_VNCTIIN_FRAME",
                dict(vn),
            )
        )

    for row in all_rows(
        conn,
        """
        SELECT item_type, item_id, gate_status, evidence_json
        FROM c86_c68_naese_chain_probe_v1_items
        WHERE run_id=?
        ORDER BY item_type, item_id
        """,
        (latest_chain,),
    ):
        if str(row["item_id"]) in {"2", "67", "67->2"}:
            items.append(
                evidence_item(
                    f"chain:{row['item_type']}:{row['item_id']}",
                    "positive_gate",
                    str(row["item_id"]),
                    "c86_c68_naese_chain_probe_v1_items",
                    str(row["gate_status"]),
                    str(row["item_type"]),
                    "POSITIVE_CHAIN_SUPPORT",
                    dict(row),
                )
            )

    for bookid in ("2", "67"):
        typed_rows = all_rows(
            conn,
            """
            SELECT chain_stage, occurrence_key, typed_exit_label, status,
                   contradiction_action, promotion_allowed, gloss_allowed,
                   semantic_translation_allowed, evidence_json
            FROM benna_ltast_c86_c68_typed_exit_occurrence_v2_items
            WHERE run_id=? AND bookid=?
            ORDER BY chain_stage, occurrence_key
            """,
            (latest_typed, bookid),
        )
        if not typed_rows:
            raise RuntimeError(f"missing typed-exit occurrence for book {bookid}")
        for row in typed_rows:
            support = "POSITIVE_TYPED_EXIT" if int(row["promotion_allowed"]) == 1 else "CONTROL_TYPED_EXIT_HELD"
            items.append(
                evidence_item(
                    f"typed:{bookid}:{row['occurrence_key']}",
                    "positive_gate" if support.startswith("POSITIVE") else "control_gate",
                    bookid,
                    "benna_ltast_c86_c68_typed_exit_occurrence_v2_items",
                    str(row["status"]),
                    str(row["typed_exit_label"]),
                    support,
                    dict(row),
                )
            )

    for bookid in ("2", "67"):
        contig = one(
            conn,
            """
            SELECT bookid, contig_position, role_bundle, inferred_stage,
                   status, evidence_json
            FROM contig1_handoff_corridor_v1_items
            WHERE run_id=? AND bookid=?
            """,
            (latest_contig, bookid),
        )
        if contig is None:
            raise RuntimeError(f"missing contig corridor item for book {bookid}")
        items.append(
            evidence_item(
                f"contig:{bookid}",
                "positive_gate",
                bookid,
                "contig1_handoff_corridor_v1_items",
                str(contig["status"]),
                str(contig["inferred_stage"]),
                "POSITIVE_CANONICAL_CONTIG_STAGE",
                dict(contig),
            )
        )

    # Controls: Book2 split, VNCTIIN-only lines, VINVIN branch, and endpoint/context branches.
    for bookid in ("2",):
        naese = one(
            conn,
            """
            SELECT status, role_label, interpretation, evidence_json
            FROM naese_slot_core_v1_items
            WHERE run_id=? AND item_type='book' AND item_id=?
            """,
            (latest_naese, bookid),
        )
        if naese is None:
            raise RuntimeError("missing Book2 NAESE slot control")
        items.append(
            evidence_item(
                "naese-slot:2",
                "control_gate",
                "2",
                "naese_slot_core_v1_items",
                str(naese["status"]),
                str(naese["role_label"]),
                "CONTROL_BOOK2_SLOT_EXIT",
                dict(naese),
            )
        )

        c68 = one(
            conn,
            """
            SELECT context_class, edge_support, slot_status, next_action, payload_json
            FROM c68_fatct_slot_items
            WHERE run_id=? AND bookid=?
            """,
            (latest_c68, bookid),
        )
        if c68 is None:
            raise RuntimeError("missing Book2 C68 slot control")
        items.append(
            evidence_item(
                "c68-slot:2",
                "control_gate",
                "2",
                "c68_fatct_slot_items",
                str(c68["slot_status"]),
                str(c68["context_class"]),
                "CONTROL_BOOK2_SLOT_EXIT",
                dict(c68),
            )
        )

    for bookid in ("23", "24"):
        shadow = one(
            conn,
            """
            SELECT likely_speech_act, plausible_human_reading, confidence_tier,
                   support_level, promotion_status, evidence_json
            FROM human_c86_vnctiin_shadow_v1_items
            WHERE run_id=? AND bookid=?
            """,
            (latest_shadow, bookid),
        )
        if shadow is None:
            raise RuntimeError(f"missing VNCTIIN-only control {bookid}")
        items.append(
            evidence_item(
                f"vnctiin-only-shadow:{bookid}",
                "control_gate",
                bookid,
                "human_c86_vnctiin_shadow_v1_items",
                str(shadow["promotion_status"]),
                str(shadow["likely_speech_act"]),
                "CONTROL_VNCTIIN_ONLY_NOT_PAYLOAD_OPEN",
                dict(shadow),
            )
        )

    for bookid in ("57",):
        shadow = one(
            conn,
            """
            SELECT likely_speech_act, plausible_human_reading, confidence_tier,
                   support_level, promotion_status, evidence_json
            FROM human_c86_vnctiin_shadow_v1_items
            WHERE run_id=? AND bookid=?
            """,
            (latest_shadow, bookid),
        )
        if shadow is None:
            raise RuntimeError("missing Book57 phase-context control")
        items.append(
            evidence_item(
                "phase-context-shadow:57",
                "control_gate",
                "57",
                "human_c86_vnctiin_shadow_v1_items",
                str(shadow["promotion_status"]),
                str(shadow["likely_speech_act"]),
                "CONTROL_PHASE_CONTEXT_NOT_PAYLOAD_PACKAGE",
                dict(shadow),
            )
        )

    vinvin = find_branch(conn, latest_c86_gate, "C86_BRANCH_EBFAI_STAR_VL_TO_VINVIN")
    items.append(
        evidence_item(
            "c86-branch:vinvin-control",
            "control_gate",
            str(vinvin["books_json"]),
            "c86_payload_operator_gate_items",
            str(vinvin["decision"]),
            str(vinvin["functional_label"]),
            "CONTROL_VINVIN_BRANCH_SEPARATE",
            dict(vinvin),
        )
    )

    context = {
        "queue_run_id": queue_run_id,
        "latest_bridge_run_id": latest_bridge,
        "latest_shadow_run_id": latest_shadow,
        "latest_c86_gate_run_id": latest_c86_gate,
        "latest_chain_run_id": latest_chain,
        "latest_route_run_id": latest_route,
        "latest_typed_run_id": latest_typed,
        "latest_q2_matrix_run_id": latest_q2_matrix,
        "latest_q2_sequence_run_id": latest_q2_sequence,
        "latest_contig_run_id": latest_contig,
        "latest_naese_run_id": latest_naese,
        "latest_c68_run_id": latest_c68,
        "latest_vnctiin_run_id": latest_vnctiin,
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
        "2": "Terminal payload-to-slot exit: C86/VNCTIIN route reaches the NAESE/C68 slot; extra C68 occurrence remains held.",
        "27": "Shadow context-payload bridge in the 10->27->2 path; TAILBETFTE suffix is not a word gloss.",
        "67": "Canonical context-payload bridge in the 35->67->2 path.",
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
                ok = status == "STRUCTURAL_PAYLOAD_WITH_EXTERNAL_CONTEXT_FRAME"
            elif support == "POSITIVE_C86_VNCTIIN_BRANCH":
                ok = status == "PAYLOAD_BRANCH_FUNCTION_READY_NO_GLOSS" and int(evidence.get("gloss_allowed", 1)) == 0
            elif support == "POSITIVE_HUMAN_SHADOW":
                ok = status == "NOT_PROMOTED"
            elif support == "POSITIVE_ROUTE_OCCURRENCE":
                ok = int(evidence.get("promotion_allowed", 0)) == 1 and int(evidence.get("gloss_allowed", 1)) == 0
            elif support == "POSITIVE_Q2_ROUTE":
                ok = int(evidence.get("promotion_allowed", 0)) == 1 and int(evidence.get("gloss_allowed", 1)) == 0
            elif support == "POSITIVE_VNCTIIN_FRAME":
                ok = status == "VNCTIIN_CONTEXT_FRAME_NO_GLOSS" and int(evidence.get("lexical_gloss_allowed", 1)) == 0
            elif support == "POSITIVE_CHAIN_SUPPORT":
                ok = status in {"STRUCTURAL_BRANCH_RESOLVED_NO_PROSE", "ORDERED_CORE", "ORDERED_EDGE_ACCEPTED_NO_GLOSS"}
            elif support == "POSITIVE_TYPED_EXIT":
                ok = status == "PROMOTE_STRUCTURE_ONLY" and int(evidence.get("gloss_allowed", 1)) == 0
            elif support == "POSITIVE_CANONICAL_CONTIG_STAGE":
                ok = status == "CANONICAL_CONTIG1_STAGE"
            if ok:
                positive_pass += 1
            else:
                positive_fail += 1
            continue

        if support == "CONTROL_ROUTE_OCCURRENCE_HELD":
            if int(evidence.get("promotion_allowed", 1)) == 0 and int(evidence.get("gloss_allowed", 1)) == 0:
                control_warn += 1
            else:
                control_fail += 1
        elif support == "CONTROL_TYPED_EXIT_HELD":
            if status == "PASS_EXTRA_OCCURRENCE_BLOCKED":
                control_warn += 1
            else:
                control_fail += 1
        elif support == "CONTROL_BOOK2_SLOT_EXIT":
            if status in {"ORDERED_CORE", "CANONICAL_SLOT_SURFACE_SUPPORT"}:
                control_warn += 1
            else:
                control_fail += 1
        elif support == "CONTROL_VNCTIIN_ONLY_NOT_PAYLOAD_OPEN":
            if status == "NOT_PROMOTED" and "context-only" in str(item["role_label"]).lower():
                control_pass += 1
            else:
                control_fail += 1
        elif support == "CONTROL_PHASE_CONTEXT_NOT_PAYLOAD_PACKAGE":
            if status == "NOT_PROMOTED" and "phase" in str(item["role_label"]).lower():
                control_pass += 1
            else:
                control_fail += 1
        elif support == "CONTROL_VINVIN_BRANCH_SEPARATE":
            if status == "PAYLOAD_BRANCH_FUNCTION_READY_NO_GLOSS" and "VINVIN" in str(item["role_label"]):
                control_pass += 1
            else:
                control_fail += 1
        else:
            control_fail += 1

    if positive_fail == 0 and control_fail == 0:
        decision = "PROMOTE_HUMAN_FUNCTIONAL_PAYLOAD_CORRIDOR_LABEL_NO_GLOSS_SLOT_PAYLOAD_SPLIT"
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
        INSERT INTO human_promotion_pkg4_c86_vnctiin_payload_falsification_v1_runs
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
                    "principle": "promote a human functional payload-corridor label only; do not promote C86/VNCTIIN/C68/NAESE lexical gloss or prose",
                    "subtype_split": "Book67 is canonical context-payload bridge, Book27 is shadow context-payload bridge, Book2 is payload-to-slot exit.",
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
            INSERT INTO human_promotion_pkg4_c86_vnctiin_payload_falsification_v1_evidence
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
        "Books 2/27/67 are a human-functional C86/VNCTIIN payload corridor: "
        "C86 EVIEFIINI opens into the VN C68 TIIN context frame. Book67 is the "
        "canonical context-payload bridge from 35->67->2; Book27 is the shadow "
        "context-payload bridge from 10->27->2; Book2 is the payload-to-slot exit "
        "where the route reaches the NAESE/C68 slot. This is not plaintext."
    )
    blocked_claims = [
        "Do not translate C86, VNCTIIN, C68, NAESE, VINVIN, O23, or TAILBETFTE as standalone words.",
        "Do not collapse Book2's NAESE/C68 slot exit into the 27/67 payload subtype.",
        "Do not let Book2's extra C68 occurrence inherit the payload-route promotion.",
        "Do not treat VNCTIIN-only Books 23/24 as payload-open books without C86 evidence.",
        "Do not merge the separate C86->VINVIN branch into the C86/VNCTIIN corridor.",
    ]
    conn.execute(
        """
        INSERT INTO human_promotion_pkg4_c86_vnctiin_payload_falsification_v1_decisions
        (run_id, decision_id, scope, decision, human_functional_reading,
         subtype_notes_json, blocked_claims_json, next_action, evidence_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            "PKG4_C86_VNCTIIN_PAYLOAD_CORRIDOR_LABEL",
            "Books 2/27/67 only",
            decision,
            human_functional_reading,
            json.dumps(subtype_notes, ensure_ascii=False, sort_keys=True),
            json.dumps(blocked_claims, ensure_ascii=False),
            "Use as the fourth promoted human-functional package; next review package is Book54 local-pair spine.",
            json.dumps(
                {
                    "candidate_books": list(CANDIDATE_BOOKS),
                    "positive_required_sources": [
                        "human_c86_vnctiin_bridge_v1_items",
                        "human_c86_vnctiin_shadow_v1_items",
                        "c86_payload_operator_gate_items",
                        "c86_naese_parallel_route_contrast_v3_items",
                        "q2_handoff_context_payload_matrix_v1_items",
                        "q2_handoff_state_sequence_v1_items",
                        "vnctiin_context_frame_gate_items",
                        "c86_c68_naese_chain_probe_v1_items",
                        "benna_ltast_c86_c68_typed_exit_occurrence_v2_items",
                        "contig1_handoff_corridor_v1_items",
                    ],
                    "control_sources": [
                        "naese_slot_core_v1_items",
                        "c68_fatct_slot_items",
                        "human_c86_vnctiin_shadow_v1_items",
                        "c86_payload_operator_gate_items",
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
