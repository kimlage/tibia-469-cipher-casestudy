#!/usr/bin/env python3
"""Q5 probe: Book20/54 local pair versus physical placement overclaim."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

PAIR_ID = "BOOK20_54_LOCAL_PAIR_CONTEXT"
BOOK20 = "20"
BOOK54 = "54"
SHARED_BLOCK = "LTFNTFEIFAIFAINIIETNEEIVN"

EXTERNAL_LOCATION_EVIDENCE = [
    {
        "item_id": "external-location:book20",
        "project_bookid": BOOK20,
        "source_label": "Tibia-wiki.net Biblioteka w Hellgate",
        "source_url": "https://tibia-wiki.net/wiki/Biblioteka_w_Hellgate",
        "external_title": "Nieznana 6",
        "library": "Hellgate Library",
        "shelf_label": "Trzecia Szafka / third shelf",
        "shelf_index": 3,
        "previous_external_title": "Nieznana 5",
        "next_external_title": "Nieznana 7",
        "exact_numeric_text": "017464834943435282177830457651288952197251081658550649911800364",
        "source_status": "SAME_LIBRARY_LOCATION_CONFIRMED_NOT_ADJACENT_TO_BOOK54",
    },
    {
        "item_id": "external-location:book54",
        "project_bookid": BOOK54,
        "source_label": "Tibia-wiki.net Biblioteka w Hellgate",
        "source_url": "https://tibia-wiki.net/wiki/Biblioteka_w_Hellgate",
        "external_title": "Nieznana 14",
        "library": "Hellgate Library",
        "shelf_label": "Siodma Szafka / seventh shelf",
        "shelf_index": 7,
        "previous_external_title": "Nieznana 13",
        "next_external_title": "Nieznana 15",
        "exact_numeric_text": "435282177830457651288952197251081658550649911800364672431",
        "source_status": "SAME_LIBRARY_LOCATION_CONFIRMED_NOT_ADJACENT_TO_BOOK20",
    },
]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def load_json(value: str | bytes | None, fallback: object) -> object:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q5_book20_54_local_pair_context_probe_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            target_pair_id TEXT NOT NULL,
            support_count INTEGER NOT NULL,
            control_count INTEGER NOT NULL,
            external_location_source_count INTEGER NOT NULL,
            same_library_count INTEGER NOT NULL,
            physical_adjacency_count INTEGER NOT NULL,
            shelf_separation_count INTEGER NOT NULL,
            independent_ingame_pair_convention_count INTEGER NOT NULL,
            promoted_plaintext_gloss_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q5_book20_54_local_pair_context_probe_v1_items (
            run_id INTEGER NOT NULL,
            item_id TEXT NOT NULL,
            item_type TEXT NOT NULL,
            source_table TEXT NOT NULL,
            source_key TEXT NOT NULL,
            status TEXT NOT NULL,
            role_label TEXT NOT NULL,
            support_class TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, item_id)
        );
        """
    )


def latest_id(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT max(run_id) FROM {table}").fetchone()
    if row is None or row[0] is None:
        raise RuntimeError(f"missing required run: {table}")
    return int(row[0])


def one(conn: sqlite3.Connection, sql: str, params: tuple[object, ...] = ()) -> sqlite3.Row | None:
    return conn.execute(sql, params).fetchone()


def all_rows(conn: sqlite3.Connection, sql: str, params: tuple[object, ...] = ()) -> list[sqlite3.Row]:
    return list(conn.execute(sql, params).fetchall())


def item(
    item_id: str,
    item_type: str,
    source_table: str,
    source_key: str,
    status: str,
    role_label: str,
    support_class: str,
    evidence: object,
) -> dict[str, object]:
    return {
        "item_id": item_id,
        "item_type": item_type,
        "source_table": source_table,
        "source_key": source_key,
        "status": status,
        "role_label": role_label,
        "support_class": support_class,
        "evidence_json": j(evidence),
    }


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q_run = latest_id(conn, "human_functional_promotion_synthesis_v1_next_questions")
    pair_run = latest_id(conn, "human_book54_pair_shadow_probe_v1_items")
    pair_run_summary = latest_id(conn, "human_book54_pair_shadow_probe_v1_runs")
    pkg5_run = latest_id(conn, "human_promotion_pkg5_book54_local_pair_falsification_v1_runs")
    zero_pair_run = latest_id(conn, "zero_pair_alignment_items")
    zero_local_run = latest_id(conn, "zero_pair_local_context_gate_items")
    residual_bridge_run = latest_id(conn, "human_residual_bridge_v1_items")

    items: list[dict[str, object]] = []

    q_row = one(
        conn,
        """
        SELECT *
        FROM human_functional_promotion_synthesis_v1_next_questions
        WHERE run_id=? AND question_id='Q5_BOOK20_54_LOCAL_PAIR_CONTEXT'
        """,
        (q_run,),
    )
    if not q_row:
        raise RuntimeError("missing Q5 next question")
    items.append(
        item(
            "precheck:q5-question",
            "precheck",
            "human_functional_promotion_synthesis_v1_next_questions",
            f"run={q_run}:Q5_BOOK20_54_LOCAL_PAIR_CONTEXT",
            "PRECHECK_READY",
            "location or independent pair convention required before stronger Book54 paraphrase",
            "SUPPORT_SQLITE_SELECTION",
            dict(q_row),
        )
    )

    pair_summary = one(
        conn,
        """
        SELECT *
        FROM human_book54_pair_shadow_probe_v1_runs
        WHERE run_id=?
        """,
        (pair_run_summary,),
    )
    if not pair_summary:
        raise RuntimeError("missing Book54 pair probe summary")
    items.append(
        item(
            "support:book54-pair-summary",
            "positive_or_control",
            "human_book54_pair_shadow_probe_v1_runs",
            f"run={pair_run_summary}",
            str(pair_summary["decision"]),
            "Book20/54 shared-core alignment is mechanically strong",
            "SUPPORT_INTERNAL_LOCAL_PAIR_ALIGNMENT_NO_GLOSS",
            dict(pair_summary),
        )
    )

    for bookid in (BOOK20, BOOK54):
        row = one(
            conn,
            """
            SELECT *
            FROM human_book54_pair_shadow_probe_v1_items
            WHERE run_id=? AND bookid=?
            """,
            (pair_run, bookid),
        )
        if not row:
            raise RuntimeError(f"missing Book{bookid} pair probe item")
        items.append(
            item(
                f"support:book54-pair-item:{bookid}",
                "positive_or_control",
                "human_book54_pair_shadow_probe_v1_items",
                f"run={pair_run}:book={bookid}",
                str(row["classification"]),
                str(row["shadow_implication"]),
                "SUPPORT_INTERNAL_PAIR_MEMBER_NO_GLOSS",
                dict(row),
            )
        )

    pkg5_run_row = one(
        conn,
        """
        SELECT decision, positive_pass_count, control_pass_count, control_warn_count,
               control_fail_count, promoted_functional_label_count,
               promoted_plaintext_gloss_count, payload_json
        FROM human_promotion_pkg5_book54_local_pair_falsification_v1_runs
        WHERE run_id=?
        """,
        (pkg5_run,),
    )
    if not pkg5_run_row:
        raise RuntimeError("missing package 5 run")
    items.append(
        item(
            "support:pkg5-promoted-functional-label",
            "positive_or_control",
            "human_promotion_pkg5_book54_local_pair_falsification_v1_runs",
            f"run={pkg5_run}",
            str(pkg5_run_row["decision"]),
            "Book54/20 local-pair shared-spine label survived falsification",
            "SUPPORT_FUNCTIONAL_LABEL_NO_GLOSS",
            dict(pkg5_run_row),
        )
    )

    pkg5_decision = one(
        conn,
        """
        SELECT *
        FROM human_promotion_pkg5_book54_local_pair_falsification_v1_decisions
        WHERE run_id=? AND decision_id='PKG5_BOOK54_LOCAL_PAIR_SHARED_SPINE_LABEL'
        """,
        (pkg5_run,),
    )
    if pkg5_decision:
        items.append(
            item(
                "support:pkg5-decision-scope",
                "positive_or_control",
                "human_promotion_pkg5_book54_local_pair_falsification_v1_decisions",
                f"run={pkg5_run}:PKG5_BOOK54_LOCAL_PAIR_SHARED_SPINE_LABEL",
                str(pkg5_decision["decision"]),
                "scope is local-pair/shared-spine only",
                "SUPPORT_SCOPE_CONTROL_NO_GLOSS",
                dict(pkg5_decision),
            )
        )

    pair_alignment = one(
        conn,
        """
        SELECT *
        FROM zero_pair_alignment_items
        WHERE run_id=? AND pair_id='PAIR_20_54_NIIE_EIVN'
        """,
        (zero_pair_run,),
    )
    if not pair_alignment:
        raise RuntimeError("missing Book20/54 zero-pair alignment")
    items.append(
        item(
            "support:zero-pair:20-54",
            "positive_or_control",
            "zero_pair_alignment_items",
            f"run={zero_pair_run}:PAIR_20_54_NIIE_EIVN",
            str(pair_alignment["alignment_status"]),
            "internal local-pair truncation alignment",
            "SUPPORT_INTERNAL_PAIR_CONVENTION_NO_GLOSS",
            dict(pair_alignment),
        )
    )

    for bookid in (BOOK20, BOOK54):
        local = one(
            conn,
            """
            SELECT *
            FROM zero_pair_local_context_gate_items
            WHERE run_id=? AND context_id='LOCAL_PAIR_20_54_TRUNCATION_ALIGNMENT'
              AND bookid=?
            """,
            (zero_local_run, bookid),
        )
        if not local:
            raise RuntimeError(f"missing local pair context for Book{bookid}")
        items.append(
            item(
                f"support:zero-local:20-54:{bookid}",
                "positive_or_control",
                "zero_pair_local_context_gate_items",
                f"run={zero_local_run}:LOCAL_PAIR_20_54_TRUNCATION_ALIGNMENT:book={bookid}",
                str(local["decision"]),
                str(local["functional_label"]),
                "SUPPORT_INTERNAL_LOCAL_CONTEXT_NO_GLOSS",
                dict(local),
            )
        )

    bridge = one(
        conn,
        """
        SELECT *
        FROM human_residual_bridge_v1_items
        WHERE run_id=? AND bridge_id='B_RESIDUAL_LOCAL_PAIR'
        """,
        (residual_bridge_run,),
    )
    if bridge:
        items.append(
            item(
                "support:residual-local-pair-bridge",
                "positive_or_control",
                "human_residual_bridge_v1_items",
                f"run={residual_bridge_run}:B_RESIDUAL_LOCAL_PAIR",
                str(bridge["support_level"]),
                str(bridge["support_summary"]),
                "SUPPORT_INTERNAL_PAIR_FAMILY_NO_GLOSS",
                dict(bridge),
            )
        )

    for evidence in EXTERNAL_LOCATION_EVIDENCE:
        items.append(
            item(
                str(evidence["item_id"]),
                "external_location",
                "web:tibia-wiki.net/Biblioteka_w_Hellgate",
                str(evidence["external_title"]),
                str(evidence["source_status"]),
                f"Book {evidence['project_bookid']} source location metadata",
                "SUPPORT_SAME_LIBRARY_LOCATION",
                evidence,
            )
        )

    shelf_indices = {str(e["project_bookid"]): int(e["shelf_index"]) for e in EXTERNAL_LOCATION_EVIDENCE}
    same_library_count = len({str(e["project_bookid"]) for e in EXTERNAL_LOCATION_EVIDENCE if e["library"] == "Hellgate Library"})
    physical_adjacency_count = 0
    external_numbers = {str(e["project_bookid"]): int(str(e["external_title"]).split()[-1]) for e in EXTERNAL_LOCATION_EVIDENCE}
    if abs(external_numbers[BOOK20] - external_numbers[BOOK54]) == 1 and shelf_indices[BOOK20] == shelf_indices[BOOK54]:
        physical_adjacency_count = 1
    shelf_separation_count = 1 if shelf_indices[BOOK20] != shelf_indices[BOOK54] else 0

    items.append(
        item(
            "control:external-physical-adjacency",
            "control",
            "web:tibia-wiki.net/Biblioteka_w_Hellgate",
            "Nieznana 6 vs Nieznana 14",
            "PHYSICAL_ADJACENCY_NOT_SUPPORTED",
            "same library but separated by external title number and shelf",
            "CONTROL_PHYSICAL_ADJACENCY_REJECTED",
            {
                "book20_external_title": "Nieznana 6",
                "book54_external_title": "Nieznana 14",
                "book20_shelf_index": shelf_indices[BOOK20],
                "book54_shelf_index": shelf_indices[BOOK54],
                "physical_adjacency_count": physical_adjacency_count,
                "shelf_separation_count": shelf_separation_count,
            },
        )
    )

    for pair_id in ("PAIR_25_39_FAST_BEIE", "PAIR_60_64_R20_LIVRN"):
        control = one(
            conn,
            """
            SELECT *
            FROM zero_pair_alignment_items
            WHERE run_id=? AND pair_id=?
            """,
            (zero_pair_run, pair_id),
        )
        if control:
            items.append(
                item(
                    f"control:pair-family:{pair_id}",
                    "control",
                    "zero_pair_alignment_items",
                    f"run={zero_pair_run}:{pair_id}",
                    str(control["alignment_status"]),
                    "other pair-like alignments show internal pair convention is not Book20/54 prose",
                    "CONTROL_INTERNAL_PAIR_CONVENTION_NOT_PHYSICAL_ANCHOR",
                    dict(control),
                )
            )

    independent_ingame_pair_convention_count = 0
    items.append(
        item(
            "missing:independent-ingame-pair-convention",
            "missing_required_evidence",
            "human_functional_promotion_synthesis_v1_next_questions",
            "Q5_BOOK20_54_LOCAL_PAIR_CONTEXT",
            "MISSING_REQUIRED_EVIDENCE",
            "no independent in-game pair convention beyond internal LCS/zero-pair alignment",
            "MISSING_BLOCKS_STRONGER_BOOK54_PARAPHRASE",
            {
                "note": (
                    "Current evidence supports an internal local-pair/shared-spine label, "
                    "but not a physical adjacent-book convention or external in-game pair convention."
                ),
                "shared_block": SHARED_BLOCK,
            },
        )
    )

    support_count = sum(1 for row in items if str(row["support_class"]).startswith("SUPPORT"))
    control_count = sum(1 for row in items if str(row["support_class"]).startswith("CONTROL"))
    external_location_source_count = len(EXTERNAL_LOCATION_EVIDENCE)
    promoted_plaintext_gloss_count = int(pkg5_run_row["promoted_plaintext_gloss_count"])

    decision = (
        "Q5_BOOK20_54_SAME_LIBRARY_NOT_PHYSICALLY_ADJACENT_NO_STRONGER_PARAPHRASE"
        if support_count >= 8
        and control_count >= 2
        and external_location_source_count == 2
        and same_library_count == 2
        and physical_adjacency_count == 0
        and shelf_separation_count == 1
        and independent_ingame_pair_convention_count == 0
        and promoted_plaintext_gloss_count == 0
        else "Q5_BOOK20_54_CONTEXT_REQUIRES_MANUAL_REVIEW"
    )

    payload = {
        "question": "Can Book20/54's shared spine be anchored to physical book adjacency, shelf context, or a repeated in-game pair convention?",
        "answer": (
            "No stronger physical/contextual anchor is currently supported. The pair is real internally, "
            "and both texts are in Hellgate Library, but external location metadata places the project Book20 "
            "text as Nieznana 6 on the third shelf and the project Book54 text as Nieznana 14 on the seventh shelf."
        ),
        "allowed_reading": "Book54/20 local-pair shared-spine label, internal/mechanical and same-library only.",
        "blocked_reading": "No physical adjacency claim, no shelf-neighborhood claim, no shared-block word gloss, and no stronger Book54 prose.",
        "external_context": {
            "Book20": EXTERNAL_LOCATION_EVIDENCE[0],
            "Book54": EXTERNAL_LOCATION_EVIDENCE[1],
        },
        "internal_context": {
            "shared_block": SHARED_BLOCK,
            "pair_alignment": "PAIR_20_54_NIIE_EIVN",
            "control_pairs": ["PAIR_25_39_FAST_BEIE", "PAIR_60_64_R20_LIVRN"],
        },
        "next_probe": (
            "Keep Book20/54 as a local-pair control. A stronger paraphrase requires a new in-game source "
            "showing why separated Hellgate books should be read as a pair."
        ),
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q5_book20_54_local_pair_context_probe_v1_runs (
                created_at, decision, target_pair_id, support_count, control_count,
                external_location_source_count, same_library_count, physical_adjacency_count,
                shelf_separation_count, independent_ingame_pair_convention_count,
                promoted_plaintext_gloss_count, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                PAIR_ID,
                support_count,
                control_count,
                external_location_source_count,
                same_library_count,
                physical_adjacency_count,
                shelf_separation_count,
                independent_ingame_pair_convention_count,
                promoted_plaintext_gloss_count,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q5_book20_54_local_pair_context_probe_v1_items (
                run_id, item_id, item_type, source_table, source_key, status,
                role_label, support_class, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    str(row["item_id"]),
                    str(row["item_type"]),
                    str(row["source_table"]),
                    str(row["source_key"]),
                    str(row["status"]),
                    str(row["role_label"]),
                    str(row["support_class"]),
                    str(row["evidence_json"]),
                )
                for row in items
            ],
        )

    print(
        j(
            {
                "run_id": run_id,
                "decision": decision,
                "target_pair_id": PAIR_ID,
                "support_count": support_count,
                "control_count": control_count,
                "external_location_source_count": external_location_source_count,
                "same_library_count": same_library_count,
                "physical_adjacency_count": physical_adjacency_count,
                "shelf_separation_count": shelf_separation_count,
                "independent_ingame_pair_convention_count": independent_ingame_pair_convention_count,
                "promoted_plaintext_gloss_count": promoted_plaintext_gloss_count,
            }
        )
    )


if __name__ == "__main__":
    main()
