#!/usr/bin/env python3
"""Falsify the second human-promotion package: Books 5/9 NAESE -> BENNA."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
PACKAGE_ID = "PKG_NAESE_BENNA_COMPOSITE_5_9"
CANDIDATE_BOOKS = ("5", "9")


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_promotion_pkg2_naese_benna_falsification_v1_runs (
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

        CREATE TABLE IF NOT EXISTS human_promotion_pkg2_naese_benna_falsification_v1_evidence (
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

        CREATE TABLE IF NOT EXISTS human_promotion_pkg2_naese_benna_falsification_v1_decisions (
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
    latest_composite = max_id(conn, "naese_benna_composite_probe_v1_items")
    latest_c68 = max_id(conn, "c68_fatct_slot_items")
    latest_naese = max_id(conn, "naese_slot_core_v1_items")
    latest_shadow = max_id(conn, "human_slot_formula_shadow_v1_items")
    latest_benna_gate = max_id(conn, "benna_formula_bridge_gate_items")
    latest_benna_core = max_id(conn, "benna_ordered_core_v2_items")
    latest_benna_decision = max_id(conn, "benna_formula_concordance_decision_v1_items")
    latest_c86_gate = max_id(conn, "c86_payload_operator_gate_items")
    latest_c86_route = max_id(conn, "c86_naese_parallel_route_contrast_v3_items")
    latest_o23 = max_id(conn, "o23_endpoint_binding_gate_v1_items")
    latest_negative = max_id(conn, "naese_c68_negative_control_items")

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

        composite = one(
            conn,
            """
            SELECT status, proposed_role, best_naese_anchor, best_naese_lcs,
                   best_benna_anchor, best_benna_lcs, best_negative_anchor,
                   best_negative_lcs, evidence_json
            FROM naese_benna_composite_probe_v1_items
            WHERE run_id=? AND bookid=?
            """,
            (latest_composite, bookid),
        )
        if composite is None:
            raise RuntimeError(f"missing NAESE/BENNA composite evidence for book {bookid}")
        items.append(
            evidence_item(
                f"composite:{bookid}",
                "positive_gate",
                bookid,
                "naese_benna_composite_probe_v1_items",
                str(composite["status"]),
                str(composite["proposed_role"]),
                "POSITIVE_REQUIRED",
                dict(composite),
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
            raise RuntimeError(f"missing C68 slot evidence for book {bookid}")
        items.append(
            evidence_item(
                f"c68:{bookid}",
                "positive_gate",
                bookid,
                "c68_fatct_slot_items",
                str(c68["slot_status"]),
                f'{c68["context_class"]}/{c68["edge_support"]}',
                "POSITIVE_SLOT_SURFACE",
                dict(c68),
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
            raise RuntimeError(f"missing human slot/formula shadow evidence for book {bookid}")
        items.append(
            evidence_item(
                f"shadow:{bookid}",
                "positive_gate",
                bookid,
                "human_slot_formula_shadow_v1_items",
                str(shadow["promotion_status"]),
                str(shadow["likely_speech_act"]),
                "HUMAN_SHADOW_REQUIRED",
                dict(shadow),
            )
        )

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
            raise RuntimeError(f"missing NAESE core control for book {bookid}")
        items.append(
            evidence_item(
                f"naese-control:{bookid}",
                "control_gate",
                bookid,
                "naese_slot_core_v1_items",
                str(naese["status"]),
                str(naese["role_label"]),
                "CONTROL_SURFACE_NAESE_NOT_CANONICAL_SLOT",
                dict(naese),
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
        support_class = (
            "CONTROL_BENNA_CLEAN_TAIL_SUPPORT"
            if str(benna_gate["decision"]) == "BENNA_FORMULA_BRIDGE_CLEAN_WITH_TAIL_NO_GLOSS"
            else "CONTROL_BENNA_VARIANT_SPLIT"
        )
        items.append(
            evidence_item(
                f"benna-gate:{bookid}",
                "control_gate",
                bookid,
                "benna_formula_bridge_gate_items",
                str(benna_gate["decision"]),
                str(benna_gate["functional_label"]),
                support_class,
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
            raise RuntimeError(f"missing BENNA ordered-core control for book {bookid}")
        items.append(
            evidence_item(
                f"benna-core:{bookid}",
                "control_gate",
                bookid,
                "benna_ordered_core_v2_items",
                str(benna_core["status"]),
                str(benna_core["role_label"]),
                "CONTROL_BENNA_PARALLEL_NOT_ORDERED",
                dict(benna_core),
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
            raise RuntimeError(f"missing BENNA body control shadow for book {bookid}")
        items.append(
            evidence_item(
                f"benna-body-shadow:{bookid}",
                "control_gate",
                bookid,
                "human_slot_formula_shadow_v1_items",
                str(row["promotion_status"]),
                str(row["likely_speech_act"]),
                "CONTROL_BENNA_BODY_COMPARISON",
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
            raise RuntimeError(f"missing BENNA body gate for book {bookid}")
        items.append(
            evidence_item(
                f"benna-body-gate:{bookid}",
                "control_gate",
                bookid,
                "benna_formula_bridge_gate_items",
                str(gate["decision"]),
                str(gate["functional_label"]),
                "CONTROL_BENNA_BODY_COMPARISON",
                dict(gate),
            )
        )

    for component in (
        "BENNA_FORMULA_FRAME_OPERATOR",
        "BENNA_PREFIX_SUFFIX_CLEAN_BRIDGE_WITH_LTAST_TAIL",
        "BENNA_VARIANTS_RESIDUALS",
    ):
        row = one(
            conn,
            """
            SELECT status, structural_label, promotion_allowed, plaintext_allowed,
                   next_action, evidence_json
            FROM benna_formula_concordance_decision_v1_items
            WHERE run_id=? AND component=?
            """,
            (latest_benna_decision, component),
        )
        if row is None:
            raise RuntimeError(f"missing BENNA concordance decision {component}")
        items.append(
            evidence_item(
                f"benna-decision:{component}",
                "control_gate",
                "BENNA",
                "benna_formula_concordance_decision_v1_items",
                str(row["status"]),
                str(row["structural_label"]),
                "CONTROL_BENNA_STRUCTURE_NO_GLOSS",
                dict(row),
            )
        )

    clean_vs_audit = one(
        conn,
        """
        SELECT decision, clean_books, clean_pass, audit_negative_count,
               failed_precondition, accepted_prose_gloss_count, payload_json
        FROM benna_clean_vs_audit_gate_v1_runs
        ORDER BY run_id DESC
        LIMIT 1
        """,
    )
    if clean_vs_audit is None:
        raise RuntimeError("missing BENNA clean-vs-audit gate")
    items.append(
        evidence_item(
            "benna-clean-vs-audit",
            "control_gate",
            "BENNA",
            "benna_clean_vs_audit_gate_v1_runs",
            str(clean_vs_audit["decision"]),
            str(clean_vs_audit["failed_precondition"]),
            "CONTROL_FULL_BENNA_PACKAGE_BLOCKED",
            dict(clean_vs_audit),
        )
    )

    c86_branch = one(
        conn,
        """
        SELECT branch_id, payload_class, books_json, downstream_frame, decision,
               functional_label, gloss_allowed, lexical_promotion_allowed,
               reason, next_action, evidence_json
        FROM c86_payload_operator_gate_items
        WHERE run_id=? AND books_json LIKE '%"5"%'
        """,
        (latest_c86_gate,),
    )
    if c86_branch is None:
        raise RuntimeError("missing C86 branch control for Book5")
    items.append(
        evidence_item(
            "c86-book5",
            "control_gate",
            "5",
            "c86_payload_operator_gate_items",
            str(c86_branch["decision"]),
            str(c86_branch["functional_label"]),
            "CONTROL_C86_NEGATIVE_FOR_COMPOSITE",
            dict(c86_branch),
        )
    )

    c86_route = one(
        conn,
        """
        SELECT occurrence_key, pair_class, naese_category, route_decision,
               promotion_allowed, gloss_allowed, semantic_translation_allowed,
               evidence_json
        FROM c86_naese_parallel_route_contrast_v3_items
        WHERE run_id=? AND bookid='5'
        """,
        (latest_c86_route,),
    )
    if c86_route is None:
        raise RuntimeError("missing C86/NAESE route contrast for Book5")
    items.append(
        evidence_item(
            "c86-naese-book5",
            "control_gate",
            "5",
            "c86_naese_parallel_route_contrast_v3_items",
            str(c86_route["route_decision"]),
            str(c86_route["pair_class"]),
            "CONTROL_C86_NEGATIVE_FOR_COMPOSITE",
            dict(c86_route),
        )
    )

    for bookid in ("24", "56"):
        o23 = one(
            conn,
            """
            SELECT frame_text, payload_text, endpoint_class, functional_label,
                   control_role, promotion_allowed, gloss_allowed, evidence_json
            FROM o23_endpoint_binding_gate_v1_items
            WHERE run_id=? AND bookid=?
            """,
            (latest_o23, bookid),
        )
        if o23 is None:
            raise RuntimeError(f"missing O23 endpoint control for book {bookid}")
        items.append(
            evidence_item(
                f"o23-control:{bookid}",
                "control_gate",
                bookid,
                "o23_endpoint_binding_gate_v1_items",
                str(o23["control_role"]),
                str(o23["functional_label"]),
                "CONTROL_O23_NEGATIVE_FOR_COMPOSITE",
                dict(o23),
            )
        )

    for bookid in CANDIDATE_BOOKS:
        neg = one(
            conn,
            """
            SELECT class_name, next_action, payload_json
            FROM naese_c68_negative_control_items
            WHERE run_id=? AND bookid=? AND item_type='naese_occurrence'
            """,
            (latest_negative, bookid),
        )
        if neg is None:
            raise RuntimeError(f"missing NAESE/C68 negative-control occurrence for book {bookid}")
        items.append(
            evidence_item(
                f"naese-negative:{bookid}",
                "control_gate",
                bookid,
                "naese_c68_negative_control_items",
                str(neg["next_action"]),
                str(neg["class_name"]),
                "CONTROL_NAESE_TEMPLATE_EXEMPLAR_NO_BROAD_GLOSS",
                dict(neg),
            )
        )

    context = {
        "queue_run_id": queue_run_id,
        "latest_composite_run_id": latest_composite,
        "latest_c68_run_id": latest_c68,
        "latest_naese_run_id": latest_naese,
        "latest_shadow_run_id": latest_shadow,
        "latest_benna_gate_run_id": latest_benna_gate,
        "latest_benna_core_run_id": latest_benna_core,
        "latest_benna_decision_run_id": latest_benna_decision,
        "latest_c86_gate_run_id": latest_c86_gate,
        "latest_c86_route_run_id": latest_c86_route,
        "latest_o23_run_id": latest_o23,
        "latest_negative_run_id": latest_negative,
    }
    return queue_run_id, items, context


def evidence_dict(item: dict[str, object]) -> dict[str, object]:
    return json.loads(str(item["evidence_json"]))


def classify(items: list[dict[str, object]]) -> tuple[str, dict[str, int], dict[str, str]]:
    positive_pass = 0
    positive_fail = 0
    for item in items:
        support = str(item["support_class"])
        status = str(item["status"])
        if support == "POSITIVE_REQUIRED":
            if status == "PROMOTE_NAESE_TO_BENNA_COMPOSITE_FRAME_NO_GLOSS":
                positive_pass += 1
            else:
                positive_fail += 1
        elif support == "POSITIVE_SLOT_SURFACE":
            if status == "CANONICAL_SLOT_SURFACE_SUPPORT":
                positive_pass += 1
            else:
                positive_fail += 1
        elif support == "HUMAN_SHADOW_REQUIRED":
            if status == "NOT_PROMOTED":
                positive_pass += 1
            else:
                positive_fail += 1

    control_pass = 0
    control_warn = 0
    control_fail = 0
    subtype_notes: dict[str, str] = {}

    for item in items:
        support = str(item["support_class"])
        status = str(item["status"])
        bookid = str(item["bookid"])
        if not support.startswith("CONTROL_"):
            continue
        if support == "CONTROL_SURFACE_NAESE_NOT_CANONICAL_SLOT":
            if status == "QUARANTINED":
                control_warn += 1
                subtype_notes[bookid] = "NAESE surface is present but not promoted as standalone canonical slot."
            else:
                control_fail += 1
        elif support == "CONTROL_BENNA_VARIANT_SPLIT":
            if status == "BENNA_VARIANT_OR_RESIDUAL_FORMULA_AUDIT_ONLY":
                control_warn += 1
                subtype_notes[bookid] = "BENNA side is variant/audit-only; package label may be composite but not clean BENNA body."
            else:
                control_fail += 1
        elif support == "CONTROL_FULL_BENNA_PACKAGE_BLOCKED":
            if "MAINTAIN_NOT_FULL_PROMOTION" in status and evidence_dict(item).get("accepted_prose_gloss_count") == 0:
                control_warn += 1
            else:
                control_fail += 1
        elif support == "CONTROL_BENNA_STRUCTURE_NO_GLOSS":
            evidence = evidence_dict(item)
            if int(evidence.get("plaintext_allowed", 1)) == 0:
                control_pass += 1
            else:
                control_fail += 1
        elif support in {
            "CONTROL_C86_NEGATIVE_FOR_COMPOSITE",
            "CONTROL_O23_NEGATIVE_FOR_COMPOSITE",
        }:
            evidence = evidence_dict(item)
            gloss_allowed = evidence.get("gloss_allowed")
            if gloss_allowed is None:
                gloss_allowed = evidence.get("lexical_promotion_allowed")
            if int(evidence.get("promotion_allowed", 0)) == 0 and int(gloss_allowed or 0) == 0:
                control_pass += 1
            elif int(gloss_allowed or 0) == 0:
                control_pass += 1
            else:
                control_fail += 1
        elif support == "CONTROL_NAESE_TEMPLATE_EXEMPLAR_NO_BROAD_GLOSS":
            if status == "clean_template_exemplar_for_function_inference":
                control_pass += 1
            else:
                control_fail += 1
        else:
            evidence = evidence_dict(item)
            if int(evidence.get("lexical_gloss_allowed", evidence.get("gloss_allowed", 0)) or 0) == 0:
                control_pass += 1
            else:
                control_fail += 1

    if positive_fail == 0 and control_fail == 0:
        decision = "PROMOTE_HUMAN_FUNCTIONAL_COMPOSITE_LABEL_NO_GLOSS_SUBTYPES_SPLIT"
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
        INSERT INTO human_promotion_pkg2_naese_benna_falsification_v1_runs
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
                    "principle": "promote at most a human functional composite label; do not promote NAESE/BENNA/C68/C86/LTAST lexical gloss or prose",
                    "subtype_split": "Book5 is composite with BENNA variant/audit-only side; Book9 is composite with clean LTAST tail support.",
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
            INSERT INTO human_promotion_pkg2_naese_benna_falsification_v1_evidence
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
        "Books 5/9 are a human-functional slot-to-formula composite: the "
        "NAESE/C68 surface slot window feeds a BENNA formula/concordance frame. "
        "Book5 remains the weaker template/composite member; Book9 carries the "
        "cleaner BENNA+LTAST-tail subtype. This is not a plaintext translation."
    )
    blocked_claims = [
        "Do not translate NAESE, C68, BENNA, C86, or LTAST as standalone words.",
        "Do not promote Book5 as a clean BENNA formula body; its BENNA side is variant/audit-only.",
        "Do not copy prose between Books 5 and 9; they share a composite frame but have different tails.",
        "Do not use Book5 terminal C86 as a semantic bridge; the C86 route is held as unsupported/local.",
        "Do not collapse the package into O23/FNAAST endpoint readings.",
    ]
    conn.execute(
        """
        INSERT INTO human_promotion_pkg2_naese_benna_falsification_v1_decisions
        (run_id, decision_id, scope, decision, human_functional_reading,
         subtype_notes_json, blocked_claims_json, next_action, evidence_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            "PKG2_NAESE_BENNA_COMPOSITE_LABEL",
            "Books 5/9 only",
            decision,
            human_functional_reading,
            json.dumps(subtype_notes, ensure_ascii=False, sort_keys=True),
            json.dumps(blocked_claims, ensure_ascii=False),
            "Use as the second promoted human-functional package; next review package is Books 10/35 BENNA->C86/VNCTIIN handoff.",
            json.dumps(
                {
                    "candidate_books": list(CANDIDATE_BOOKS),
                    "positive_required_sources": [
                        "naese_benna_composite_probe_v1_items",
                        "c68_fatct_slot_items",
                        "human_slot_formula_shadow_v1_items",
                    ],
                    "control_sources": [
                        "naese_slot_core_v1_items",
                        "benna_formula_bridge_gate_items",
                        "benna_ordered_core_v2_items",
                        "benna_formula_concordance_decision_v1_items",
                        "benna_clean_vs_audit_gate_v1_runs",
                        "c86_payload_operator_gate_items",
                        "c86_naese_parallel_route_contrast_v3_items",
                        "o23_endpoint_binding_gate_v1_items",
                        "naese_c68_negative_control_items",
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
