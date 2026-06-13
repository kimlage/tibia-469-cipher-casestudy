#!/usr/bin/env python3
"""Build an internal contrastive functional-semantic model, no lexical gloss."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


DB_PATH = Path(__file__).resolve().parents[1] / "data" / "bonelord_operational.sqlite"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def functional_class(function_id: str, policy_status: str) -> str:
    if function_id == "STAR_00":
        return "SEGMENT_BOUNDARY"
    if function_id == "LTAST_TAIL":
        return "CONTINUATION_BOUNDARY"
    if "FORMULA" in function_id or policy_status == "FORMULA_CONTEXT":
        return "FORMULA_OPERATOR"
    if "SLOT" in policy_status or "SLOT" in function_id or function_id == "NAESE_IVIFAST":
        return "SLOT_CLASSIFIER"
    if "R20" in function_id or "R02" in function_id:
        return "PHASE_FRAME"
    if "O23_ONAF" in function_id:
        return "ENDPOINT_CONTINUATION_FRAME"
    if "C86" in function_id:
        return "PAYLOAD_OPEN_OPERATOR"
    if "VINVIN" in function_id:
        return "BRANCH_FRAME"
    if "C68" in function_id:
        return "LOCAL_CONTEXT_FRAME"
    if policy_status == "VALIDATED_MECHANICAL":
        return "MECHANICAL_SUBSTRATE"
    if policy_status == "AUDIT_ONLY":
        return "AUDIT_ONLY"
    return "CONTEXT_OR_AUDIT"


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        create table if not exists internal_functional_semantic_model_runs (
            run_id integer primary key,
            created_at text not null,
            decision text not null,
            item_count integer not null,
            functional_class_count integer not null,
            lexical_gloss_allowed_count integer not null,
            payload_json text not null
        );

        create table if not exists internal_functional_semantic_model_items (
            run_id integer not null,
            item_id text not null,
            source_kind text not null,
            parent_id text,
            policy_status text not null,
            confidence real not null,
            functional_class text not null,
            predicts text not null,
            lexical_gloss_allowed integer not null,
            evidence_json text not null,
            primary key (run_id, item_id)
        );
        """
    )

    run_id = conn.execute("select coalesce(max(run_id), 0) + 1 from internal_functional_semantic_model_runs").fetchone()[0]
    function_run_id = conn.execute("select max(run_id) from row0_function_policy_items").fetchone()[0]
    sub_run_id = conn.execute("select max(run_id) from row0_subfunction_policy_items").fetchone()[0]

    classes = set()
    count = 0
    for row in conn.execute(
        """
        select function_id, policy_status, policy_confidence, policy_decision,
               next_action, gloss_allowed, evidence_json
        from row0_function_policy_items
        where run_id = ?
        """,
        (function_run_id,),
    ):
        cls = functional_class(row["function_id"], row["policy_status"])
        classes.add(cls)
        predicts = row["next_action"]
        conn.execute(
            """
            insert into internal_functional_semantic_model_items
            (run_id, item_id, source_kind, parent_id, policy_status, confidence,
             functional_class, predicts, lexical_gloss_allowed, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                row["function_id"],
                "row0_function",
                None,
                row["policy_status"],
                row["policy_confidence"],
                cls,
                predicts,
                0,
                json.dumps({"policy_decision": row["policy_decision"], "source_evidence": row["evidence_json"]}, ensure_ascii=False),
            ),
        )
        count += 1

    for row in conn.execute(
        """
        select subfunction_id, parent_function_id, policy_status, policy_confidence,
               next_action, gloss_allowed, evidence_json
        from row0_subfunction_policy_items
        where run_id = ?
        """,
        (sub_run_id,),
    ):
        cls = "BRANCH_SUBFUNCTION" if "READY" in row["policy_status"] else "NEGATIVE_BRANCH_CONTROL"
        classes.add(cls)
        conn.execute(
            """
            insert into internal_functional_semantic_model_items
            (run_id, item_id, source_kind, parent_id, policy_status, confidence,
             functional_class, predicts, lexical_gloss_allowed, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                row["subfunction_id"],
                "row0_subfunction",
                row["parent_function_id"],
                row["policy_status"],
                row["policy_confidence"],
                cls,
                row["next_action"],
                0,
                row["evidence_json"],
            ),
        )
        count += 1

    decision = "INTERNAL_FUNCTIONAL_SEMANTIC_MODEL_READY_NO_LEXICAL_GLOSS"
    conn.execute(
        """
        insert into internal_functional_semantic_model_runs
        (run_id, created_at, decision, item_count, functional_class_count,
         lexical_gloss_allowed_count, payload_json)
        values (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            now_iso(),
            decision,
            count,
            len(classes),
            0,
            json.dumps({"function_run_id": function_run_id, "subfunction_run_id": sub_run_id}, ensure_ascii=False),
        ),
    )
    conn.commit()

    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "item_count": count,
                "functional_class_count": len(classes),
                "lexical_gloss_allowed_count": 0,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
