#!/usr/bin/env python3
"""Falsify the first human-promotion package: Books 51/53 R02 -> NAESE/C68."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
PACKAGE_ID = "PKG_R02_NAESE_SLOT_BRIDGE_51_53"
CANDIDATE_BOOKS = ("51", "53")


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_promotion_pkg1_r02_naese_falsification_v1_runs (
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

        CREATE TABLE IF NOT EXISTS human_promotion_pkg1_r02_naese_falsification_v1_evidence (
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

        CREATE TABLE IF NOT EXISTS human_promotion_pkg1_r02_naese_falsification_v1_decisions (
            run_id INTEGER NOT NULL,
            decision_id TEXT NOT NULL,
            scope TEXT NOT NULL,
            decision TEXT NOT NULL,
            human_functional_reading TEXT NOT NULL,
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


def one(conn: sqlite3.Connection, sql: str, params: tuple[object, ...]) -> sqlite3.Row | None:
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


def collect_evidence(conn: sqlite3.Connection) -> tuple[int, list[dict[str, object]], dict[str, object]]:
    queue_run_id = latest_queue_run(conn)
    latest_naese = max_id(conn, "naese_slot_core_v1_items")
    latest_c68 = max_id(conn, "c68_fatct_slot_items")
    latest_phase = max_id(conn, "r20_r02_naese_phase_gate_v1_items")
    latest_bridge = max_id(conn, "r02_naese_slot_bridge_v1_items")
    latest_narrow = max_id(conn, "r02_narrow_bridge_decision_v1_items")

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

        bridge = one(
            conn,
            """
            SELECT bridge_label, gate_status, evidence_json
            FROM r02_naese_slot_bridge_v1_items
            WHERE run_id=? AND bookid=?
            """,
            (latest_bridge, bookid),
        )
        if bridge is None:
            raise RuntimeError(f"missing R02/NAESE bridge gate for book {bookid}")
        items.append(
            evidence_item(
                f"bridge:{bookid}",
                "positive_gate",
                bookid,
                "r02_naese_slot_bridge_v1_items",
                str(bridge["gate_status"]),
                str(bridge["bridge_label"]),
                "POSITIVE_REQUIRED",
                dict(bridge),
            )
        )

        core = one(
            conn,
            """
            SELECT status, role_label, interpretation, evidence_json
            FROM naese_slot_core_v1_items
            WHERE run_id=? AND item_type='book' AND item_id=?
            """,
            (latest_naese, bookid),
        )
        if core is None:
            raise RuntimeError(f"missing NAESE core evidence for book {bookid}")
        items.append(
            evidence_item(
                f"naese:{bookid}",
                "positive_gate",
                bookid,
                "naese_slot_core_v1_items",
                str(core["status"]),
                str(core["role_label"]),
                "POSITIVE_REQUIRED",
                dict(core),
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
            raise RuntimeError(f"missing C68/FATCT evidence for book {bookid}")
        items.append(
            evidence_item(
                f"c68:{bookid}",
                "positive_gate",
                bookid,
                "c68_fatct_slot_items",
                str(c68["slot_status"]),
                f'{c68["context_class"]}/{c68["edge_support"]}',
                "POSITIVE_REQUIRED",
                dict(c68),
            )
        )

        phase = one(
            conn,
            """
            SELECT expected_class, observed_frame, naese_status, gate_status, evidence_json
            FROM r20_r02_naese_phase_gate_v1_items
            WHERE run_id=? AND bookid=?
            """,
            (latest_phase, bookid),
        )
        if phase is None:
            raise RuntimeError(f"missing R20/R02 phase evidence for book {bookid}")
        items.append(
            evidence_item(
                f"phase:{bookid}",
                "positive_gate",
                bookid,
                "r20_r02_naese_phase_gate_v1_items",
                str(phase["gate_status"]),
                str(phase["observed_frame"]),
                "POSITIVE_REQUIRED",
                dict(phase),
            )
        )

        narrow = one(
            conn,
            """
            SELECT status, structural_label, promotion_allowed, plaintext_allowed,
                   next_action, evidence_json
            FROM r02_narrow_bridge_decision_v1_items
            WHERE run_id=? AND item_id=? AND item_kind='book'
            """,
            (latest_narrow, bookid),
        )
        if narrow is None:
            raise RuntimeError(f"missing narrow bridge decision for book {bookid}")
        items.append(
            evidence_item(
                f"narrow:{bookid}",
                "positive_gate",
                bookid,
                "r02_narrow_bridge_decision_v1_items",
                str(narrow["status"]),
                str(narrow["structural_label"]),
                "FUNCTION_LABEL_ALLOWED_NO_PLAINTEXT",
                dict(narrow),
            )
        )

    control_specs = [
        (
            "naese22",
            "22",
            "naese_slot_core_v1_items",
            """
            SELECT status, role_label, interpretation, evidence_json
            FROM naese_slot_core_v1_items
            WHERE run_id=? AND item_type='book' AND item_id='22'
            """,
            (latest_naese,),
            "CONTROL_CANONICAL_SLOT_NOT_R02",
        ),
        (
            "connector46",
            "46",
            "naese_slot_core_v1_items",
            """
            SELECT status, role_label, interpretation, evidence_json
            FROM naese_slot_core_v1_items
            WHERE run_id=? AND item_type='book' AND item_id='46'
            """,
            (latest_naese,),
            "CONTROL_CONNECTOR_NOT_SLOT_PROOF",
        ),
        (
            "hybrid42",
            "42",
            "book42_hybrid_bridge_v1_items",
            """
            SELECT status, bridge_id AS role_label, interpretation, evidence_json
            FROM book42_hybrid_bridge_v1_items
            WHERE run_id=(SELECT max(run_id) FROM book42_hybrid_bridge_v1_items)
            """,
            (),
            "CONTROL_WEAK_HYBRID_NOT_CLEAN_SLOT",
        ),
        (
            "prefix45",
            "45",
            "book45_r02_prefix_control_v1_items",
            """
            SELECT status, structural_label AS role_label, next_action AS interpretation,
                   evidence_json, promotion_allowed, plaintext_allowed
            FROM book45_r02_prefix_control_v1_items
            WHERE run_id=(SELECT max(run_id) FROM book45_r02_prefix_control_v1_items)
              AND item_id='book45'
            """,
            (),
            "CONTROL_R02_PREFIX_NOT_SLOT",
        ),
        (
            "livrn60",
            "60",
            "r20_livrn_audit_context_policy_items",
            """
            SELECT policy_status AS status, context_id AS role_label,
                   next_action AS interpretation, evidence_json
            FROM r20_livrn_audit_context_policy_items
            WHERE run_id=(SELECT max(run_id) FROM r20_livrn_audit_context_policy_items)
              AND context_id='AUDIT_R20_LIVRN_MICRO_CONTEXT'
            """,
            (),
            "CONTROL_LIVRN_MICRO_AUDIT_ONLY",
        ),
        (
            "direction51_53",
            "51,53",
            "r02_narrow_bridge_decision_v1_items",
            """
            SELECT status, structural_label AS role_label, next_action AS interpretation,
                   evidence_json, promotion_allowed, plaintext_allowed
            FROM r02_narrow_bridge_decision_v1_items
            WHERE run_id=? AND item_id='51->53'
            """,
            (latest_narrow,),
            "CONTROL_DIRECTION_BLOCKED",
        ),
    ]

    for item_id, bookid, table, sql, params, support_class in control_specs:
        row = one(conn, sql, params)
        if row is None:
            raise RuntimeError(f"missing control {item_id}")
        status = str(row["status"])
        role_label = str(row["role_label"])
        items.append(
            evidence_item(
                f"control:{item_id}",
                "control_gate",
                bookid,
                table,
                status,
                role_label,
                support_class,
                dict(row),
            )
        )

    run_context = {
        "queue_run_id": queue_run_id,
        "latest_naese_run_id": latest_naese,
        "latest_c68_run_id": latest_c68,
        "latest_phase_run_id": latest_phase,
        "latest_bridge_run_id": latest_bridge,
        "latest_narrow_run_id": latest_narrow,
    }
    return queue_run_id, items, run_context


def classify(items: list[dict[str, object]]) -> tuple[str, dict[str, int]]:
    required_positive = [i for i in items if i["support_class"] == "POSITIVE_REQUIRED"]
    allowed_label = [i for i in items if i["support_class"] == "FUNCTION_LABEL_ALLOWED_NO_PLAINTEXT"]
    control_items = [i for i in items if str(i["support_class"]).startswith("CONTROL_")]

    positive_pass = 0
    positive_fail = 0
    for item in required_positive:
        status = str(item["status"])
        role = str(item["role_label"])
        if status in {"PASS_R02_SLOT_BRIDGE", "ORDERED_CORE", "SLOT_SUBFUNCTION_READY"}:
            positive_pass += 1
        elif status == "PASS_R02_SLOT_BRIDGE" or role == "R02_SLOT_BRIDGE":
            positive_pass += 1
        else:
            positive_fail += 1

    label_ok = all(
        str(item["status"]) == "PROMOTE_NARROW_PHASE_SLOT_BRIDGE_NO_GLOSS"
        for item in allowed_label
    )
    plaintext_blocked = True
    for item in allowed_label:
        evidence = json.loads(str(item["evidence_json"]))
        plaintext_blocked = plaintext_blocked and int(evidence.get("plaintext_allowed", 1)) == 0

    control_pass = 0
    control_warn = 0
    control_fail = 0
    for item in control_items:
        support_class = str(item["support_class"])
        status = str(item["status"])
        if support_class == "CONTROL_DIRECTION_BLOCKED":
            if status == "HOLD_DIRECTION_NOT_PROMOTED_NO_GLOSS":
                control_warn += 1
            else:
                control_fail += 1
        elif status.startswith(("HOLD_", "ACCEPT_", "AUDIT_", "ORDERED_CORE", "SUPPORT", "QUARANTINED")):
            control_pass += 1
        else:
            control_fail += 1

    if positive_fail == 0 and label_ok and plaintext_blocked and control_fail == 0:
        decision = "PROMOTE_HUMAN_FUNCTIONAL_LABEL_NO_GLOSS_DIRECTION_BLOCKED"
    else:
        decision = "KEEP_IN_REVIEW_NO_PROMOTION"

    return decision, {
        "positive_pass_count": positive_pass + len(allowed_label),
        "control_pass_count": control_pass,
        "control_warn_count": control_warn,
        "control_fail_count": control_fail,
        "promoted_functional_label_count": 1 if decision.startswith("PROMOTE_HUMAN_FUNCTIONAL_LABEL") else 0,
        "promoted_plaintext_gloss_count": 0,
    }


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)
    queue_run_id, items, run_context = collect_evidence(conn)
    decision, counts = classify(items)

    cur = conn.execute(
        """
        INSERT INTO human_promotion_pkg1_r02_naese_falsification_v1_runs
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
                    **run_context,
                    "principle": "promote at most a human functional label; do not promote lexical gloss or prose",
                    "directionality": "51/53 pair is accepted as codescription/slot bridge; 51->53 direction remains blocked",
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
            INSERT INTO human_promotion_pkg1_r02_naese_falsification_v1_evidence
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

    blocked_claims = [
        "Do not translate R02, NAESE, or C68 as standalone words.",
        "Do not infer a full-book sentence for Books 51 or 53.",
        "Do not promote 51->53 directional order; keep the pair as a codescribed bridge until a direction gate passes.",
        "Do not propagate the R02 bridge to Book45, Book42, or LIVRN micro controls.",
    ]
    human_functional_reading = (
        "Books 51/53 are a human-functional phase-to-slot bridge: the R02/TRVEIIVNTBB "
        "context enters the NAESE/C68 slot frame. This is a structural reading for "
        "human review, not a plaintext translation."
    )
    conn.execute(
        """
        INSERT INTO human_promotion_pkg1_r02_naese_falsification_v1_decisions
        (run_id, decision_id, scope, decision, human_functional_reading,
         blocked_claims_json, next_action, evidence_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            "PKG1_R02_NAESE_SLOT_BRIDGE_LABEL",
            "Books 51/53 only",
            decision,
            human_functional_reading,
            json.dumps(blocked_claims, ensure_ascii=False),
            "Use as the first promoted human-functional package; next review package is Books 5/9 NAESE->BENNA composite.",
            json.dumps(
                {
                    "candidate_books": list(CANDIDATE_BOOKS),
                    "positive_required_sources": [
                        "r02_naese_slot_bridge_v1_items",
                        "naese_slot_core_v1_items",
                        "c68_fatct_slot_items",
                        "r20_r02_naese_phase_gate_v1_items",
                    ],
                    "control_sources": [
                        "book45_r02_prefix_control_v1_items",
                        "book42_hybrid_bridge_v1_items",
                        "r20_livrn_audit_context_policy_items",
                        "r02_narrow_bridge_decision_v1_items",
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
