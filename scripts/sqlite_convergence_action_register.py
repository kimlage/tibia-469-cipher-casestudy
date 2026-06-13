#!/usr/bin/env python3
"""Build an SQLite-native convergence action register.

The register is the coordinator-facing shortlist. It converts existing audit
tables into concrete next actions while preserving the anti-hallucination rule:
structural actions may advance; semantic gloss remains blocked unless explicitly
supported by independent evidence.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


DB_PATH = Path(__file__).resolve().parents[1] / "data" / "bonelord_operational.sqlite"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def max_run(conn: sqlite3.Connection, table: str) -> int | None:
    row = conn.execute(f"select max(run_id) from {table}").fetchone()
    return row[0] if row else None


def add_action(actions: list[dict], family: str, priority: int, status: str, action: str, why: str, gate: str, payload: dict) -> None:
    actions.append(
        {
            "family": family,
            "priority": priority,
            "status": status,
            "action": action,
            "why": why,
            "gate": gate,
            "payload": payload,
        }
    )


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        create table if not exists semantic_convergence_action_runs (
            run_id integer primary key,
            created_at text not null,
            decision text not null,
            action_count integer not null,
            live_action_count integer not null,
            blocked_or_quarantine_count integer not null,
            top_family text,
            payload_json text not null
        );

        create table if not exists semantic_convergence_action_items (
            run_id integer not null,
            rank integer not null,
            family text not null,
            priority integer not null,
            action_status text not null,
            next_action text not null,
            why_selected text not null,
            promotion_gate text not null,
            payload_json text not null,
            primary key (run_id, rank)
        );
        """
    )

    run_id = conn.execute("select coalesce(max(run_id), 0) + 1 from semantic_convergence_action_runs").fetchone()[0]
    actions: list[dict] = []

    cssr_run = max_run(conn, "conservative_semantic_safety_runs")
    formula_mask_promotion_run = max_run(conn, "formula_only_mask_promotion_runs")
    if cssr_run:
        cssr = conn.execute(
            """
            select cssr_pct, flagged_book_count, formula_book_count, blocked_book_count
            from conservative_semantic_safety_runs
            where run_id = ?
            """,
            (cssr_run,),
        ).fetchone()
        add_action(
            actions,
            "CSSR_CONTROL_METRIC",
            100,
            "LIVE_COORDINATION_METRIC",
            "use_cssr_as_primary_semantic_safety_metric",
            "fluency metrics were misleading; CSSR penalizes explicit uncertainty and blocked phrases",
            "improve only by reducing contradiction or uncertainty, not by smoothing text",
            dict(cssr),
        )
    if formula_mask_promotion_run:
        formula_projection = conn.execute(
            """
            select decision, recovered_book_count, still_flagged_book_count,
                   blocked_remaining_count, projected_cssr_pct
            from formula_only_mask_promotion_runs
            where run_id = ?
            """,
            (formula_mask_promotion_run,),
        ).fetchone()
        add_action(
            actions,
            "FORMULA_ONLY_DISPLAY_MASKS_F03_F04_F06",
            78,
            "MATERIALIZED_DISPLAY_SAFE_NO_GLOSS",
            "accept_dead_formula_masks_as_display_only_not_semantic_payload",
            "projection recovers formula-only books while preserving blocked flags",
            "do not convert display formulas into English gloss",
            dict(formula_projection),
        )

    overlap_run = max_run(conn, "overlap_formula_holdout_edge_items")
    overlap_13_38_run = max_run(conn, "overlap_13_38_residual_probe_runs")
    overlap_13_38_decision = None
    if overlap_13_38_run:
        overlap_13_38_decision = conn.execute(
            "select decision from overlap_13_38_residual_probe_runs where run_id = ?",
            (overlap_13_38_run,),
        ).fetchone()["decision"]
    if overlap_run:
        for row in conn.execute(
            """
            select edge_id, basecontigid, left_bookid, right_bookid, holdout_score,
                   classification, overlap_symbols, residual_char_count, masked_overlap
            from overlap_formula_holdout_edge_items
            where run_id = ?
            order by holdout_score desc
            """,
            (overlap_run,),
        ):
            classification = row["classification"]
            if row["edge_id"] == "4:1:13->38" and overlap_13_38_decision:
                add_action(
                    actions,
                    f"OVERLAP_HOLDOUT_{row['edge_id']}",
                    60,
                    "RESOLVED_STRUCTURAL_COMPOSITE_NO_GLOSS",
                    "use_as_boundary_composition_not_payload",
                    "targeted residual probe classified this edge as O23/NAESE/AETTA composition",
                    "reopen only if a new residual segment repeats outside the known structural families",
                    {**dict(row), "resolution_decision": overlap_13_38_decision},
                )
            elif classification == "ALIVE_WEAK":
                add_action(
                    actions,
                    f"OVERLAP_HOLDOUT_{row['edge_id']}",
                    92,
                    "LIVE_STRUCTURAL_FRONTIER",
                    "probe_residual_payload_after_formula_mask",
                    "this edge retains residual overlap after formula masking and may constrain payload boundaries",
                    "must improve boundary consistency without assigning plaintext gloss",
                    dict(row),
                )
            elif classification == "DEAD_OR_FORMULA_ONLY":
                add_action(
                    actions,
                    f"OVERLAP_HOLDOUT_{row['edge_id']}",
                    35,
                    "SUPPRESS_AS_FORMULA_ONLY",
                    "keep_masked_do_not_use_as_payload",
                    "formula masking removes nearly all independent support",
                    "reopen only with a new non-formula mechanical signal",
                    dict(row),
                )
            else:
                add_action(
                    actions,
                    f"OVERLAP_HOLDOUT_{row['edge_id']}",
                    55,
                    "AUDIT_ONLY",
                    "retain_as_boundary_audit",
                    "edge has some residual signal but structural vetoes prevent promotion",
                    "needs independent contig/slot corroboration",
                    dict(row),
                )

    naese_run = max_run(conn, "naese_ivifast_slot_items")
    naese_policy_run = max_run(conn, "naese_slot_policy_runs")
    if naese_run:
        rows = list(
            conn.execute(
                """
                select prefix_class, suffix_class, position_class, next_action,
                       count(*) as occ, count(distinct bookid) as books
                from naese_ivifast_slot_items
                where run_id = ?
                group by prefix_class, suffix_class, position_class, next_action
                order by occ desc, books desc
                """,
                (naese_run,),
            )
        )
        clean = sum(row["occ"] for row in rows if row["next_action"] == "clean_template_exemplar_for_function_inference")
        variants = sum(row["occ"] for row in rows if row["next_action"] != "clean_template_exemplar_for_function_inference")
        if naese_policy_run:
            policy = conn.execute(
                """
                select decision, clean_exemplar_count, variant_count, promoted_boundary_count, audit_only_count
                from naese_slot_policy_runs
                where run_id = ?
                """,
                (naese_policy_run,),
            ).fetchone()
            add_action(
                actions,
                "NAESE_IVIFAST_SLOT_CONTRAST",
                62,
                "MATERIALIZED_SLOT_BOUNDARY_NO_GLOSS",
                "use_clean_exemplars_as_slot_boundaries_keep_variants_audit_only",
                "policy table already separates clean exemplars from variants",
                "do not assign plaintext; variants remain excluded from function promotion",
                {**dict(policy), "matrix": [dict(row) for row in rows]},
            )
        else:
            add_action(
                actions,
                "NAESE_IVIFAST_SLOT_CONTRAST",
                88,
                "LIVE_SLOT_CLASSIFIER_FRONTIER",
                "promote_clean_exemplars_only_as_slot_boundary_no_gloss",
                "clean exemplars can constrain a slot template while variants remain audit-only",
                "minimum clean exemplar count >= 4 and variants must not be collapsed into the same function",
                {"clean_exemplar_count": clean, "variant_count": variants, "matrix": [dict(row) for row in rows]},
            )

    vinvin_run = max_run(conn, "vinvin_branch_subfunction_items")
    vinvin_render_run = max_run(conn, "vinvin_branch_render_policy_runs")
    if vinvin_run:
        for row in conn.execute(
            """
            select suffix_class, occurrence_count, book_count, contig_supported_count,
                   o23_relation_count, partial_or_negative_count, branch_score,
                   branch_status, next_action, books_json
            from vinvin_branch_subfunction_items
            where run_id = ?
            order by branch_score desc
            """,
            (vinvin_run,),
        ):
            if vinvin_render_run:
                render = conn.execute(
                    """
                    select render_status, render_label, next_action
                    from vinvin_branch_render_policy_items
                    where run_id = ? and suffix_class = ?
                    """,
                    (vinvin_render_run, row["suffix_class"]),
                ).fetchone()
                if render and row["branch_status"] == "SUBFUNCTION_READY":
                    status = "MATERIALIZED_STRUCTURAL_BRANCH_NO_GLOSS"
                    priority = 58
                    action = render["next_action"]
                    why = "branch render policy already materialized this as a structural branch"
                    gate = "no plaintext; use render label as boundary/control only"
                elif render:
                    status = "MATERIALIZED_NEGATIVE_CONTROL_NO_GLOSS"
                    priority = 42
                    action = render["next_action"]
                    why = "branch render policy already materialized this as a negative fragment control"
                    gate = "do not promote without new contig support"
                else:
                    status = "AUDIT_GAP"
                    priority = 50
                    action = "inspect_missing_render_policy"
                    why = "source branch has no render policy row"
                    gate = "do not promote until policy exists"
            elif row["branch_status"] == "SUBFUNCTION_READY":
                status = "LIVE_SUBFUNCTION_NO_GLOSS"
                priority = 82
                action = "render_as_structural_branch_and_use_as_negative_control"
                why = "branch has contig support and no partial negatives"
                gate = "no plaintext; only structural branch label until semantic evidence appears"
            else:
                status = "NEGATIVE_CONTROL"
                priority = 45
                action = "keep_as_fragment_control"
                why = "partial branch prevents over-promotion of surface fragments"
                gate = "do not promote unless contig support appears"
            add_action(actions, f"VINVIN_BRANCH_{row['suffix_class']}", priority, status, action, why, gate, dict(row))

    rosetta_run = max_run(conn, "rosetta_anchor_projection_probe_runs")
    if rosetta_run:
        rosetta = conn.execute(
            """
            select decision, anchor_count, compatible_count, quarantined_count, out_of_corpus_count
            from rosetta_anchor_projection_probe_runs
            where run_id = ?
            """,
            (rosetta_run,),
        ).fetchone()
        add_action(
            actions,
            "ROSETTA_EXTERNAL_ANCHORS",
            30,
            "QUARANTINED_NO_BOOK_GLOSS",
            "use_only_as_external_roundtrip_controls",
            "projection found no anchor compatible enough to gloss book corpus",
            "reopen only with phrase-level book alignment, not short substrings",
            dict(rosetta),
        )

    actions.sort(key=lambda item: (-item["priority"], item["family"]))
    live_count = sum(1 for item in actions if item["status"].startswith("LIVE"))
    blocked_count = len(actions) - live_count
    decision = "CONVERGENCE_ACTION_REGISTER_READY_SQLITE_FIRST"
    top_family = actions[0]["family"] if actions else None

    for rank, item in enumerate(actions, start=1):
        conn.execute(
            """
            insert into semantic_convergence_action_items
            (run_id, rank, family, priority, action_status, next_action, why_selected,
             promotion_gate, payload_json)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                rank,
                item["family"],
                item["priority"],
                item["status"],
                item["action"],
                item["why"],
                item["gate"],
                json.dumps(item["payload"], ensure_ascii=False),
            ),
        )

    conn.execute(
        """
        insert into semantic_convergence_action_runs
        (run_id, created_at, decision, action_count, live_action_count,
         blocked_or_quarantine_count, top_family, payload_json)
        values (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            now_iso(),
            decision,
            len(actions),
            live_count,
            blocked_count,
            top_family,
            json.dumps(
                {
                    "cssr_run_id": cssr_run,
                    "overlap_run_id": overlap_run,
                    "naese_run_id": naese_run,
                    "vinvin_run_id": vinvin_run,
                    "rosetta_run_id": rosetta_run,
                    "overlap_13_38_run_id": overlap_13_38_run,
                    "naese_policy_run_id": naese_policy_run,
                    "vinvin_render_run_id": vinvin_render_run,
                    "formula_mask_promotion_run_id": formula_mask_promotion_run,
                },
                ensure_ascii=False,
            ),
        ),
    )
    conn.commit()

    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "action_count": len(actions),
                "live_action_count": live_count,
                "blocked_or_quarantine_count": blocked_count,
                "top_family": top_family,
                "top_actions": [
                    {
                        "family": item["family"],
                        "priority": item["priority"],
                        "status": item["status"],
                        "next_action": item["action"],
                    }
                    for item in actions[:5]
                ],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
