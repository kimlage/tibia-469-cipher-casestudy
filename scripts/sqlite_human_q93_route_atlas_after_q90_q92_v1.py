#!/usr/bin/env python3
"""Q93: export human route atlas after Q90-Q92 medium-target closure."""

from __future__ import annotations

import datetime as dt
import json
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
EXPORT_DIR = ROOT / "tmp" / "human_shadow_exports"
MD_EXPORT = EXPORT_DIR / "q93_human_route_atlas_after_q90_q92_v1.md"
JSON_EXPORT = EXPORT_DIR / "q93_human_route_atlas_after_q90_q92_v1.json"

Q82_AUDITS = [
    ("Q82_T01_BENNA_C86_VNCTIIN_FORMULA_HANDOFF", "human_q83_benna_c86_exact_source_audit_v1_runs"),
    ("Q82_T02_C86_VNCTIIN_PAYLOAD_CORRIDOR", "human_q84_c86_vnctiin_exact_source_audit_v1_runs"),
    ("Q82_T03_NAESE_BENNA_COMPOSITE", "human_q86_naese_benna_exact_source_audit_v1_runs"),
    ("Q82_T04_R02_NAESE_SLOT_BRIDGE", "human_q87_r02_naese_exact_source_audit_v1_runs"),
    ("Q82_T05_BOOK49_MATH49_REGISTER", "human_q90_book49_math49_exact_source_audit_v1_runs"),
    ("Q82_T06_BOOK54_PAIR_LOCAL_SPINE", "human_q91_book54_pair_local_spine_exact_source_audit_v1_runs"),
    ("Q82_T07_BOOK7_PHASE_MATHEMAGIC", "human_q88_book7_phase_mathemagic_exact_source_audit_v1_runs"),
    ("Q82_T08_CHAYENNE_FRAME_REGISTER", "human_q92_chayenne_frame_register_exact_source_audit_v1_runs"),
]

ROUTE_OVERRIDES = {
    "B_R02_NAESE_SLOT_BRIDGE": {
        "status": "ALIVE_PRIMARY_HUMAN_ROUTE",
        "route_type": "phase-to-slot bridge",
        "blocked_gloss": "No R02/TRVEIIVNTBB/NAESE/C68/FATCT/IVIFAST lexical gloss.",
        "next_exact_source_target": "Q93_A01_R02_NEGATIVE_CONTROL_SOURCE_LADDER",
    },
    "B_BOOK7_PHASE_MATHEMAGIC": {
        "status": "ALIVE_OPERATOR_DISCOVERY_ROUTE",
        "route_type": "operator/selector route",
        "blocked_gloss": "No Book7, TIINNEF, NEIAAETTA, 3478, or Mathemagica operator word gloss.",
        "next_exact_source_target": "Q93_A02_BOOK7_OPERATOR_HELDOUT_SELECTOR_BENCHMARK",
    },
    "B_BENNA_C86_VNCTIIN_FORMULA_HANDOFF": {
        "status": "ALIVE_PACKET_SHADOW_COMPONENT",
        "route_type": "formula-to-context packet component",
        "blocked_gloss": "Q83 blocks formula-handoff plaintext and component word glosses.",
        "next_exact_source_target": "Q93_A03_Q80_PACKET_SOURCE_AS_PACKET",
    },
    "B_C86_VNCTIIN_PAYLOAD_CORRIDOR": {
        "status": "ALIVE_PACKET_SHADOW_COMPONENT",
        "route_type": "payload/context corridor packet component",
        "blocked_gloss": "Q84 blocks C86/VNCTIIN payload plaintext and component word glosses.",
        "next_exact_source_target": "Q93_A03_Q80_PACKET_SOURCE_AS_PACKET",
    },
    "B_NAESE_BENNA_COMPOSITE": {
        "status": "HELD_COMPOSITE_SHADOW",
        "route_type": "slot-to-formula composite",
        "blocked_gloss": "Q86 blocks NAESE/BENNA plaintext, slot value, and BENNA operator rule.",
        "next_exact_source_target": "REOPEN_ONLY_WITH_NEW_EXACT_SOURCE_OR_PREDICTIVE_RULE",
    },
    "B_BOOK49_MATH49_REGISTER": {
        "status": "CLOSED_MEDIUM_NO_GLOSS",
        "route_type": "repeat/register operator pressure",
        "blocked_gloss": "Q90 blocks 49-key, repeat-register, calibration, and operator-reset glosses.",
        "next_exact_source_target": "NO_REOPEN_WITHOUT_IAEN_NEEN_SOURCE_OR_HELDOUT_PLUS49_PASS",
    },
    "B_BOOK54_PAIR_LOCAL_SPINE": {
        "status": "CLOSED_MEDIUM_NO_GLOSS",
        "route_type": "local-pair/shared-spine control",
        "blocked_gloss": "Q91 blocks shared-spine, prefix, tail, zero, pair, and local-spine word glosses.",
        "next_exact_source_target": "NO_REOPEN_WITHOUT_INDEPENDENT_PAIR_CONVENTION_OR_EXACT_SOURCE",
    },
    "B_CHAYENNE_FRAME_REGISTER": {
        "status": "CLOSED_MEDIUM_EXTERNAL_FRAME_NO_GLOSS",
        "route_type": "source-quarantined external frame/register",
        "blocked_gloss": "Q92 blocks Chayenne phrase, shared-frame, Book8/37/66 plaintext, and component glosses.",
        "next_exact_source_target": "NO_REOPEN_WITHOUT_EXACT_BOOK_SEQUENCE_PLUS_MEANING",
    },
    "B_BOOK12_21_NO_O23_IMPORT": {
        "status": "NEXT_IDEA_CORPUS_ROUTE",
        "route_type": "Book30-family corpus/gathering route",
        "blocked_gloss": "No O23/ONAF/FNAAST endpoint meaning may be imported into Book12/21 base witnesses.",
        "next_exact_source_target": "Q93_A04_BOOK30_GREAT_CALCULATOR_CORPUS_ROUTE",
    },
    "B_BOOK30_SPINE_GREAT_CALCULATOR": {
        "status": "NEXT_IDEA_CORPUS_ROUTE",
        "route_type": "Book30-family corpus/gathering route",
        "blocked_gloss": "No Great Calculator/corpus lore can become direct phrase meaning without exact relation.",
        "next_exact_source_target": "Q93_A04_BOOK30_GREAT_CALCULATOR_CORPUS_ROUTE",
    },
    "B_O23_VNCTIIN_ENDPOINT_CONTEXT": {
        "status": "NEXT_IDEA_ENDPOINT_ROUTE",
        "route_type": "endpoint/context route",
        "blocked_gloss": "No O23/ONAF/VEINLETFNAAST endpoint gloss without spoken or book-level source.",
        "next_exact_source_target": "Q93_A05_O23_ENDPOINT_SOUND_OR_DIALOG_ANCHOR",
    },
    "B_RESIDUAL_O23_FNAAST_ENDPOINT": {
        "status": "NEXT_IDEA_ENDPOINT_ROUTE",
        "route_type": "endpoint/component route",
        "blocked_gloss": "Endpoint/component overlap cannot import meaning across books.",
        "next_exact_source_target": "Q93_A05_O23_ENDPOINT_SOUND_OR_DIALOG_ANCHOR",
    },
}

ACTIONS = [
    {
        "action_id": "Q93_A01_R02_NEGATIVE_CONTROL_SOURCE_LADDER",
        "priority": 1,
        "route_focus": "B_R02_NAESE_SLOT_BRIDGE",
        "books": ["51", "53", "45", "46", "14"],
        "status": "NEXT_PRIMARY_ROUTE",
        "reason": "R02/NAESE is the strongest human route; it now needs local negatives before phrase-level prose.",
        "acceptance_gate": "51/53 must predict slot-bridge behavior better than 45/46/14 and still require exact source before gloss.",
        "expected_failure_mode": "Phase/slot language spreads into nearby R20/R02 connectors and becomes overbroad.",
        "next_probe": "Build an exact-source ladder over 51/53 positives against 45/46/14 controls.",
    },
    {
        "action_id": "Q93_A02_BOOK7_OPERATOR_HELDOUT_SELECTOR_BENCHMARK",
        "priority": 2,
        "route_focus": "B_BOOK7_PHASE_MATHEMAGIC",
        "books": ["7", "6", "19", "31", "57", "49"],
        "status": "NEXT_OPERATOR_ROUTE",
        "reason": "Book7/Mathemagica is useful only if it predicts heldout operators, not if it names a word.",
        "acceptance_gate": "A 3478/1/13/49/94 selector must beat controls on heldout books before any semantic claim.",
        "expected_failure_mode": "Mathemagica output becomes a tempting dictionary key without heldout prediction.",
        "next_probe": "Benchmark operator windows against Book7 positives, Book6 continuity-only, and TIINNEF/VNCTIIN controls.",
    },
    {
        "action_id": "Q93_A03_Q80_PACKET_SOURCE_AS_PACKET",
        "priority": 3,
        "route_focus": "B_BENNA_C86_VNCTIIN_FORMULA_HANDOFF+B_C86_VNCTIIN_PAYLOAD_CORRIDOR",
        "books": ["35", "67", "2", "27", "10"],
        "status": "NEXT_PACKET_ROUTE",
        "reason": "Q83/Q84 failed when audited as separate targets; Q80 may need a packet-level source relation instead.",
        "acceptance_gate": "A source must constrain the packet relation, not just one component, and must reduce contradictions.",
        "expected_failure_mode": "Readable packet prose hides that both component routes failed exact-source promotion.",
        "next_probe": "Search for source relations that bind formula handoff plus payload corridor as one packet.",
    },
    {
        "action_id": "Q93_A04_BOOK30_GREAT_CALCULATOR_CORPUS_ROUTE",
        "priority": 4,
        "route_focus": "B_BOOK30_SPINE_GREAT_CALCULATOR+B_BOOK12_21_NO_O23_IMPORT",
        "books": ["12", "21", "26", "30"],
        "status": "NEXT_CORPUS_ROUTE",
        "reason": "Great Calculator/corpus lore may explain repeated gathered book material without requiring sentence prose.",
        "acceptance_gate": "A corpus/gathering relation must predict Book12/21/26/30 spine behavior and block endpoint import.",
        "expected_failure_mode": "Corpus lore becomes generic permission to read arbitrary repeated text as meaning.",
        "next_probe": "Tie Book30-family spine behavior to in-game Great Calculator/corpus references with controls.",
    },
    {
        "action_id": "Q93_A05_O23_ENDPOINT_SOUND_OR_DIALOG_ANCHOR",
        "priority": 5,
        "route_focus": "B_O23_VNCTIIN_ENDPOINT_CONTEXT+B_RESIDUAL_O23_FNAAST_ENDPOINT",
        "books": ["13", "38", "56"],
        "status": "NEXT_ENDPOINT_ROUTE",
        "reason": "Endpoint material is a compact route where an NPC phrase, sound, spell, or book relation might force value.",
        "acceptance_gate": "Only exact in-game dialogue/book/sound/source relation may attach meaning to O23/ONAF/VEINLETFNAAST.",
        "expected_failure_mode": "Endpoint/component overlap imports meaning into unrelated Book30-family witnesses.",
        "next_probe": "Search in-game transcripts/books for exact endpoint-adjacent phrases before any endpoint gloss.",
    },
]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def slug(value: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "_", value.upper()).strip("_")


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q93_route_atlas_after_q90_q92_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q81_run_id INTEGER NOT NULL,
            q89_run_id INTEGER NOT NULL,
            q90_run_id INTEGER NOT NULL,
            q91_run_id INTEGER NOT NULL,
            q92_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            exported_book_count INTEGER NOT NULL,
            route_group_count INTEGER NOT NULL,
            q82_target_count INTEGER NOT NULL,
            closed_q82_target_count INTEGER NOT NULL,
            alive_route_count INTEGER NOT NULL,
            closed_medium_route_count INTEGER NOT NULL,
            next_action_count INTEGER NOT NULL,
            promoted_gloss_count INTEGER NOT NULL,
            markdown_export_path TEXT NOT NULL,
            json_export_path TEXT NOT NULL,
            next_action_id TEXT NOT NULL,
            result_human_version TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q93_route_atlas_after_q90_q92_v1_groups (
            run_id INTEGER NOT NULL,
            route_id TEXT NOT NULL,
            source_bridge_id TEXT NOT NULL,
            route_status TEXT NOT NULL,
            route_type TEXT NOT NULL,
            book_count INTEGER NOT NULL,
            books_json TEXT NOT NULL,
            allowed_reading TEXT NOT NULL,
            blocked_gloss TEXT NOT NULL,
            next_exact_source_target TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, route_id)
        );

        CREATE TABLE IF NOT EXISTS human_q93_route_atlas_after_q90_q92_v1_books (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            route_id TEXT NOT NULL,
            source_bridge_id TEXT NOT NULL,
            route_status TEXT NOT NULL,
            confidence_tier TEXT NOT NULL,
            audit_status TEXT NOT NULL,
            promotion_status TEXT NOT NULL,
            allowed_reading TEXT NOT NULL,
            blocked_gloss TEXT NOT NULL,
            next_exact_source_target TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        );

        CREATE TABLE IF NOT EXISTS human_q93_route_atlas_after_q90_q92_v1_actions (
            run_id INTEGER NOT NULL,
            action_id TEXT NOT NULL,
            priority INTEGER NOT NULL,
            route_focus TEXT NOT NULL,
            books_json TEXT NOT NULL,
            status TEXT NOT NULL,
            reason TEXT NOT NULL,
            acceptance_gate TEXT NOT NULL,
            expected_failure_mode TEXT NOT NULL,
            next_probe TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, action_id)
        );
        """
    )


def latest_row(conn: sqlite3.Connection, table: str) -> sqlite3.Row:
    row = conn.execute(f"SELECT * FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    if row is None:
        raise RuntimeError(f"missing required row: {table}")
    return row


def load_q81_items(conn: sqlite3.Connection, q81_run_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT *
        FROM human_q81_controlled_shadow_export_v1_items
        WHERE run_id=?
        ORDER BY CAST(bookid AS INTEGER)
        """,
        (q81_run_id,),
    ).fetchall()


def parse_blocked(row: sqlite3.Row, fallback: str) -> str:
    try:
        blocked = json.loads(str(row["blocked_claims_json"]))
    except json.JSONDecodeError:
        blocked = []
    if blocked:
        return str(blocked[-1])
    return fallback


def group_items(items: list[sqlite3.Row]) -> list[dict[str, object]]:
    grouped: dict[str, list[sqlite3.Row]] = {}
    for row in items:
        grouped.setdefault(str(row["source_bridge_id"]), []).append(row)

    groups: list[dict[str, object]] = []
    for idx, (bridge_id, rows) in enumerate(sorted(grouped.items()), start=1):
        override = ROUTE_OVERRIDES.get(bridge_id, {})
        books = [str(row["bookid"]) for row in sorted(rows, key=lambda item: int(item["bookid"]))]
        first = sorted(rows, key=lambda item: int(item["bookid"]))[0]
        route_id = f"Q93_R{idx:02d}_{slug(bridge_id.replace('B_', ''))}"
        status = str(override.get("status", "ATLAS_SHADOW_GROUP_NO_CURRENT_SOURCE_TARGET"))
        route_type = str(override.get("route_type", "controlled atlas shadow group"))
        blocked_gloss = str(
            override.get(
                "blocked_gloss",
                parse_blocked(first, "No lexical or sentence gloss is promoted for this group."),
            )
        )
        next_target = str(override.get("next_exact_source_target", "NO_CURRENT_EXACT_SOURCE_TARGET"))
        allowed_reading = (
            f"Use as {route_type}: "
            f"{str(first['plausible_human_reading']).rstrip('.')}. "
            f"All {len(books)} book(s) stay human-shadow only."
        )
        groups.append(
            {
                "route_id": route_id,
                "source_bridge_id": bridge_id,
                "route_status": status,
                "route_type": route_type,
                "book_count": len(books),
                "books": books,
                "allowed_reading": allowed_reading,
                "blocked_gloss": blocked_gloss,
                "next_exact_source_target": next_target,
            }
        )
    return groups


def render_markdown(run_id: int, decision: str, groups: list[dict[str, object]], actions: list[dict[str, object]]) -> str:
    lines = [
        "# Q93 Human Route Atlas After Q90-Q92",
        "",
        f"Run: `{run_id}`",
        f"Decision: `{decision}`",
        "",
        "This is a route atlas for human translation work. It is not canonical plaintext.",
        "",
        "## Summary",
        "",
        f"- Route groups: `{len(groups)}`",
        f"- Books covered: `{sum(int(group['book_count']) for group in groups)}`",
        "- Q82 exact-source targets audited: `8/8`",
        "- Canonical promoted glosses: `0`",
        f"- Next action: `{actions[0]['action_id']}`",
        "",
        "## Route Groups",
        "",
        "| Route | Status | Books | Allowed Reading | Blocked Gloss | Next Target |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for group in groups:
        books = ", ".join(f"`{book}`" for book in group["books"])
        lines.append(
            "| `{route_id}` | `{status}` | {books} | {allowed} | {blocked} | `{next_target}` |".format(
                route_id=group["route_id"],
                status=group["route_status"],
                books=books,
                allowed=str(group["allowed_reading"]).replace("|", "/"),
                blocked=str(group["blocked_gloss"]).replace("|", "/"),
                next_target=group["next_exact_source_target"],
            )
        )
    lines.extend(
        [
            "",
            "## Next Actions",
            "",
            "| Priority | Action | Books | Gate | Expected Failure |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for action in actions:
        books = ", ".join(f"`{book}`" for book in action["books"])
        lines.append(
            "| `{priority}` | `{action_id}` | {books} | {gate} | {failure} |".format(
                priority=action["priority"],
                action_id=action["action_id"],
                books=books,
                gate=str(action["acceptance_gate"]).replace("|", "/"),
                failure=str(action["expected_failure_mode"]).replace("|", "/"),
            )
        )
    lines.extend(
        [
            "",
            "## Promotion Rule",
            "",
            "Every route remains `NOT_PROMOTED` unless a future source gives exact sequence, provenance, meaning or a mechanically forced value, and failed controls.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q81 = latest_row(conn, "human_q81_controlled_shadow_export_v1_runs")
    q89 = latest_row(conn, "human_q89_route_synthesis_after_q86_q88_v1_runs")
    q90 = latest_row(conn, "human_q90_book49_math49_exact_source_audit_v1_runs")
    q91 = latest_row(conn, "human_q91_book54_pair_local_spine_exact_source_audit_v1_runs")
    q92 = latest_row(conn, "human_q92_chayenne_frame_register_exact_source_audit_v1_runs")
    completion = latest_row(conn, "human_translation_completion_audit_v5_runs")
    q82_audit_rows = [(target_id, latest_row(conn, table)) for target_id, table in Q82_AUDITS]
    items = load_q81_items(conn, int(q81["run_id"]))
    groups = group_items(items)

    exported_book_count = len(items)
    route_group_count = len(groups)
    q82_target_count = len(Q82_AUDITS)
    closed_q82_target_count = sum(
        1 for _, row in q82_audit_rows if int(row["canonical_promotion_allowed_count"]) == 0
    )
    alive_route_count = sum(1 for group in groups if str(group["route_status"]).startswith("ALIVE"))
    closed_medium_route_count = sum(1 for group in groups if "CLOSED_MEDIUM" in str(group["route_status"]))
    next_action_count = len(ACTIONS)
    promoted_gloss_count = int(completion["promoted_gloss_count"])
    result_human_version = (
        "Q93 converts the Q81 70-book shadow into a route atlas after Q90-Q92: "
        "all Q82 exact-source targets have now been audited, medium routes are closed without gloss, "
        "and the next work moves to R02/NAESE controls, Book7 operator benchmarks, Q80 packet-source search, "
        "Book30/Great Calculator corpus routing, and O23 endpoint anchors."
    )
    decision = (
        "Q93_ROUTE_ATLAS_AFTER_Q90_Q92_READY_70_BOOKS_8_Q82_TARGETS_NO_GLOSS"
        if exported_book_count == 70
        and route_group_count >= 30
        and q82_target_count == 8
        and closed_q82_target_count == 8
        and alive_route_count >= 3
        and closed_medium_route_count == 3
        and next_action_count == 5
        and promoted_gloss_count == 0
        and int(q89["promoted_gloss_count"]) == 0
        and int(q90["canonical_promotion_allowed_count"]) == 0
        and int(q91["canonical_promotion_allowed_count"]) == 0
        and int(q92["canonical_promotion_allowed_count"]) == 0
        else "Q93_ROUTE_ATLAS_AFTER_Q90_Q92_REQUIRES_REVIEW"
    )

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "decision": decision,
        "run_id": None,
        "summary": {
            "exported_book_count": exported_book_count,
            "route_group_count": route_group_count,
            "q82_target_count": q82_target_count,
            "closed_q82_target_count": closed_q82_target_count,
            "alive_route_count": alive_route_count,
            "closed_medium_route_count": closed_medium_route_count,
            "promoted_gloss_count": promoted_gloss_count,
        },
        "q82_audits": [
            {
                "target_id": target_id,
                "decision": str(row["decision"]),
                "canonical_promotion_allowed_count": int(row["canonical_promotion_allowed_count"]),
            }
            for target_id, row in q82_audit_rows
        ],
        "groups": groups,
        "actions": ACTIONS,
        "books": [],
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q93_route_atlas_after_q90_q92_v1_runs (
                created_at, decision, q81_run_id, q89_run_id, q90_run_id,
                q91_run_id, q92_run_id, completion_audit_run_id,
                exported_book_count, route_group_count, q82_target_count,
                closed_q82_target_count, alive_route_count, closed_medium_route_count,
                next_action_count, promoted_gloss_count, markdown_export_path,
                json_export_path, next_action_id, result_human_version, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                int(q81["run_id"]),
                int(q89["run_id"]),
                int(q90["run_id"]),
                int(q91["run_id"]),
                int(q92["run_id"]),
                int(completion["run_id"]),
                exported_book_count,
                route_group_count,
                q82_target_count,
                closed_q82_target_count,
                alive_route_count,
                closed_medium_route_count,
                next_action_count,
                promoted_gloss_count,
                str(MD_EXPORT.relative_to(ROOT)),
                str(JSON_EXPORT.relative_to(ROOT)),
                ACTIONS[0]["action_id"],
                result_human_version,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        payload["run_id"] = run_id

        conn.executemany(
            """
            INSERT INTO human_q93_route_atlas_after_q90_q92_v1_groups (
                run_id, route_id, source_bridge_id, route_status, route_type,
                book_count, books_json, allowed_reading, blocked_gloss,
                next_exact_source_target, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    str(group["route_id"]),
                    str(group["source_bridge_id"]),
                    str(group["route_status"]),
                    str(group["route_type"]),
                    int(group["book_count"]),
                    j(group["books"]),
                    str(group["allowed_reading"]),
                    str(group["blocked_gloss"]),
                    str(group["next_exact_source_target"]),
                    j(group),
                )
                for group in groups
            ],
        )

        group_by_bridge = {str(group["source_bridge_id"]): group for group in groups}
        book_rows = []
        for row in items:
            group = group_by_bridge[str(row["source_bridge_id"])]
            blocked_gloss = str(group["blocked_gloss"])
            book_payload = {
                "bookid": str(row["bookid"]),
                "route_id": str(group["route_id"]),
                "source_bridge_id": str(row["source_bridge_id"]),
                "route_status": str(group["route_status"]),
                "confidence_tier": str(row["confidence_tier"]),
                "audit_status": str(row["audit_status"]),
                "promotion_status": str(row["promotion_status"]),
                "allowed_reading": str(row["plausible_human_reading"]),
                "blocked_gloss": blocked_gloss,
                "next_exact_source_target": str(group["next_exact_source_target"]),
            }
            payload["books"].append(book_payload)
            book_rows.append(
                (
                    run_id,
                    str(row["bookid"]),
                    str(group["route_id"]),
                    str(row["source_bridge_id"]),
                    str(group["route_status"]),
                    str(row["confidence_tier"]),
                    str(row["audit_status"]),
                    str(row["promotion_status"]),
                    str(row["plausible_human_reading"]),
                    blocked_gloss,
                    str(group["next_exact_source_target"]),
                    j(book_payload),
                )
            )
        conn.executemany(
            """
            INSERT INTO human_q93_route_atlas_after_q90_q92_v1_books (
                run_id, bookid, route_id, source_bridge_id, route_status,
                confidence_tier, audit_status, promotion_status, allowed_reading,
                blocked_gloss, next_exact_source_target, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            book_rows,
        )

        conn.executemany(
            """
            INSERT INTO human_q93_route_atlas_after_q90_q92_v1_actions (
                run_id, action_id, priority, route_focus, books_json, status,
                reason, acceptance_gate, expected_failure_mode, next_probe, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    action["action_id"],
                    int(action["priority"]),
                    action["route_focus"],
                    j(action["books"]),
                    action["status"],
                    action["reason"],
                    action["acceptance_gate"],
                    action["expected_failure_mode"],
                    action["next_probe"],
                    j(action),
                )
                for action in ACTIONS
            ],
        )

    MD_EXPORT.write_text(render_markdown(run_id, decision, groups, ACTIONS), encoding="utf-8")
    JSON_EXPORT.write_text(j(payload) + "\n", encoding="utf-8")

    print(
        j(
            {
                "run_id": run_id,
                "decision": decision,
                "exported_book_count": exported_book_count,
                "route_group_count": route_group_count,
                "q82_target_count": q82_target_count,
                "closed_q82_target_count": closed_q82_target_count,
                "alive_route_count": alive_route_count,
                "closed_medium_route_count": closed_medium_route_count,
                "next_action_count": next_action_count,
                "promoted_gloss_count": promoted_gloss_count,
                "markdown_export_path": str(MD_EXPORT.relative_to(ROOT)),
                "json_export_path": str(JSON_EXPORT.relative_to(ROOT)),
                "next_action_id": ACTIONS[0]["action_id"],
            }
        )
    )


if __name__ == "__main__":
    main()
