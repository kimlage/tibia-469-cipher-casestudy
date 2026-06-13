#!/usr/bin/env python3
"""Q81: export the complete controlled human-shadow atlas."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
EXPORT_DIR = ROOT / "tmp" / "human_shadow_exports"
MD_EXPORT = EXPORT_DIR / "q81_controlled_human_shadow_export_v1.md"
JSON_EXPORT = EXPORT_DIR / "q81_controlled_human_shadow_export_v1.json"


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q81_controlled_shadow_export_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            atlas_v6_run_id INTEGER NOT NULL,
            contradiction_audit_run_id INTEGER NOT NULL,
            q80_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            exported_book_count INTEGER NOT NULL,
            readable_export_count INTEGER NOT NULL,
            anchored_export_count INTEGER NOT NULL,
            contradiction_pass_count INTEGER NOT NULL,
            promotion_status_not_promoted_count INTEGER NOT NULL,
            promoted_gloss_count INTEGER NOT NULL,
            primary_packet_book_count INTEGER NOT NULL,
            heldout_packet_book_count INTEGER NOT NULL,
            markdown_export_path TEXT NOT NULL,
            json_export_path TEXT NOT NULL,
            export_human_version TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q81_controlled_shadow_export_v1_items (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            likely_speech_act TEXT NOT NULL,
            plausible_human_reading TEXT NOT NULL,
            confidence_tier TEXT NOT NULL,
            support_level TEXT NOT NULL,
            source_bridge_id TEXT NOT NULL,
            anchor_ids_json TEXT NOT NULL,
            audit_status TEXT NOT NULL,
            review_tier TEXT NOT NULL,
            promotion_status TEXT NOT NULL,
            packet_roles_json TEXT NOT NULL,
            blocked_claims_json TEXT NOT NULL,
            falsifier TEXT NOT NULL,
            next_probe TEXT NOT NULL,
            export_status TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        );
        """
    )


def latest_row(conn: sqlite3.Connection, table: str) -> sqlite3.Row:
    row = conn.execute(f"SELECT * FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    if row is None:
        raise RuntimeError(f"missing required row: {table}")
    return row


def load_atlas(conn: sqlite3.Connection, atlas_run_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT *
        FROM human_translation_atlas_v6_items
        WHERE run_id=?
        ORDER BY CAST(target_id AS INTEGER)
        """,
        (atlas_run_id,),
    ).fetchall()


def load_audit(conn: sqlite3.Connection, audit_run_id: int) -> dict[str, sqlite3.Row]:
    rows = conn.execute(
        """
        SELECT *
        FROM human_atlas_v6_contradiction_audit_v1_items
        WHERE run_id=?
        """,
        (audit_run_id,),
    ).fetchall()
    return {str(row["bookid"]): row for row in rows}


def load_q80_packet_roles(conn: sqlite3.Connection, q80_run_id: int) -> dict[str, list[dict[str, str]]]:
    rows = conn.execute(
        """
        SELECT packet_id, bookid, route_role, q78_edge_condition_status, q78_control_result
        FROM human_q80_packet_shadow_versions_v1_book_roles
        WHERE run_id=?
        ORDER BY packet_id, CAST(bookid AS INTEGER)
        """,
        (q80_run_id,),
    ).fetchall()
    packet_roles: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        packet_roles.setdefault(str(row["bookid"]), []).append(
            {
                "packet_id": str(row["packet_id"]),
                "route_role": str(row["route_role"]),
                "q78_edge_condition_status": str(row["q78_edge_condition_status"]),
                "q78_control_result": str(row["q78_control_result"]),
            }
        )
    return packet_roles


def build_items(
    atlas_rows: list[sqlite3.Row],
    audit_rows: dict[str, sqlite3.Row],
    packet_roles: dict[str, list[dict[str, str]]],
) -> list[dict[str, object]]:
    items = []
    for row in atlas_rows:
        bookid = str(row["target_id"])
        audit = audit_rows.get(bookid)
        if audit is None:
            raise RuntimeError(f"missing contradiction audit row for book {bookid}")
        roles = packet_roles.get(bookid, [])
        export_status = (
            "INCLUDED_PRIMARY_PACKET_SHADOW_NOT_PROMOTED"
            if any(role["packet_id"] == "Q80_P01_PRIMARY_35_67_2" for role in roles)
            else "INCLUDED_HELDOUT_PACKET_SHADOW_NOT_PROMOTED"
            if any(role["packet_id"] == "Q80_P02_HELDOUT_27_67_2" for role in roles)
            else "INCLUDED_ATLAS_SHADOW_NOT_PROMOTED"
        )
        items.append(
            {
                "bookid": bookid,
                "likely_speech_act": str(row["likely_speech_act"]),
                "plausible_human_reading": str(row["plausible_human_reading"]),
                "confidence_tier": str(row["confidence_tier"]),
                "support_level": str(row["support_level"]),
                "source_bridge_id": str(row["source_bridge_id"]),
                "anchor_ids_json": str(row["anchor_ids_json"]),
                "audit_status": str(audit["audit_status"]),
                "review_tier": str(audit["review_tier"]),
                "promotion_status": str(row["promotion_status"]),
                "packet_roles": roles,
                "blocked_claims_json": str(row["blocked_claims_json"]),
                "falsifier": str(row["falsifier"]),
                "next_probe": str(row["next_probe"]),
                "export_status": export_status,
                "evidence": {"atlas": dict(row), "contradiction_audit": dict(audit), "packet_roles": roles},
            }
        )
    return items


def write_exports(run_id: int, decision: str, items: list[dict[str, object]], summary: dict[str, object]) -> None:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    export = {
        "run_id": run_id,
        "decision": decision,
        "summary": summary,
        "items": items,
    }
    JSON_EXPORT.write_text(j(export) + "\n", encoding="utf-8")

    lines = [
        "# Q81 Controlled Human Shadow Export",
        "",
        f"Run: `{run_id}`",
        f"Decision: `{decision}`",
        "",
        "This is a human-shadow export, not canonical plaintext.",
        "",
        "## Summary",
        "",
        f"- Exported books: `{summary['exported_book_count']}`",
        f"- Readable rows: `{summary['readable_export_count']}`",
        f"- Anchored rows: `{summary['anchored_export_count']}`",
        f"- Contradiction audit PASS rows: `{summary['contradiction_pass_count']}`",
        f"- NOT_PROMOTED rows: `{summary['promotion_status_not_promoted_count']}`",
        f"- Promoted glosses: `{summary['promoted_gloss_count']}`",
        f"- Primary packet books: `{summary['primary_packet_book_count']}`",
        f"- Heldout packet books: `{summary['heldout_packet_book_count']}`",
        "",
        "## Books",
        "",
        "| Book | Confidence | Audit | Packet | Human-shadow reading |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in items:
        roles = item["packet_roles"]
        packet = ",".join(role["packet_id"] for role in roles) if roles else "atlas"
        reading = str(item["plausible_human_reading"]).replace("|", "/")
        lines.append(
            f"| `{item['bookid']}` | `{item['confidence_tier']}` | `{item['audit_status']}` | "
            f"`{packet}` | {reading} |"
        )
    lines.extend(
        [
            "",
            "## Promotion Rule",
            "",
            "Every row in this export remains `NOT_PROMOTED`. Use this artifact for human review, "
            "source search, and contrast planning. Do not cite it as solved plaintext.",
            "",
        ]
    )
    MD_EXPORT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    atlas_run = latest_row(conn, "human_translation_atlas_v6_runs")
    contradiction_run = latest_row(conn, "human_atlas_v6_contradiction_audit_v1_runs")
    q80 = latest_row(conn, "human_q80_packet_shadow_versions_v1_runs")
    completion = latest_row(conn, "human_translation_completion_audit_v5_runs")

    atlas_rows = load_atlas(conn, int(atlas_run["run_id"]))
    audit_rows = load_audit(conn, int(contradiction_run["run_id"]))
    packet_roles = load_q80_packet_roles(conn, int(q80["run_id"]))
    items = build_items(atlas_rows, audit_rows, packet_roles)

    exported_book_count = len(items)
    readable_export_count = sum(1 for item in items if item["plausible_human_reading"])
    anchored_export_count = sum(1 for item in items if item["anchor_ids_json"])
    contradiction_pass_count = sum(1 for item in items if item["audit_status"] == "PASS")
    promotion_status_not_promoted_count = sum(1 for item in items if item["promotion_status"] == "NOT_PROMOTED")
    promoted_gloss_count = int(completion["promoted_gloss_count"])
    primary_packet_book_count = sum(
        1
        for item in items
        if any(role["packet_id"] == "Q80_P01_PRIMARY_35_67_2" for role in item["packet_roles"])
    )
    heldout_packet_book_count = sum(
        1
        for item in items
        if any(role["packet_id"] == "Q80_P02_HELDOUT_27_67_2" for role in item["packet_roles"])
    )
    export_human_version = (
        "Q81 exports all 70 atlas v6 books as controlled human-shadow readings with anchors, "
        "audit status, packet tags, blocked claims, falsifiers, and NOT_PROMOTED status."
    )
    decision = (
        "Q81_CONTROLLED_HUMAN_SHADOW_EXPORT_READY_70_BOOKS_NO_GLOSS"
        if exported_book_count == 70
        and readable_export_count == 70
        and anchored_export_count == 70
        and contradiction_pass_count == 70
        and promotion_status_not_promoted_count == 70
        and promoted_gloss_count == 0
        and primary_packet_book_count == 3
        and heldout_packet_book_count == 3
        else "Q81_CONTROLLED_HUMAN_SHADOW_EXPORT_REQUIRES_REVIEW"
    )
    summary = {
        "exported_book_count": exported_book_count,
        "readable_export_count": readable_export_count,
        "anchored_export_count": anchored_export_count,
        "contradiction_pass_count": contradiction_pass_count,
        "promotion_status_not_promoted_count": promotion_status_not_promoted_count,
        "promoted_gloss_count": promoted_gloss_count,
        "primary_packet_book_count": primary_packet_book_count,
        "heldout_packet_book_count": heldout_packet_book_count,
        "markdown_export_path": str(MD_EXPORT.relative_to(ROOT)),
        "json_export_path": str(JSON_EXPORT.relative_to(ROOT)),
    }
    payload = {
        "question": "Can the complete atlas be exported as a controlled human-shadow translation artifact?",
        "answer": export_human_version,
        "blocked_use": "This export is not canonical plaintext and does not promote any gloss.",
        "next_action": "Use the export to select review clusters and exact-source search targets.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q81_controlled_shadow_export_v1_runs (
                created_at, decision, atlas_v6_run_id, contradiction_audit_run_id,
                q80_run_id, completion_audit_run_id, exported_book_count,
                readable_export_count, anchored_export_count,
                contradiction_pass_count, promotion_status_not_promoted_count,
                promoted_gloss_count, primary_packet_book_count,
                heldout_packet_book_count, markdown_export_path,
                json_export_path, export_human_version, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                int(atlas_run["run_id"]),
                int(contradiction_run["run_id"]),
                int(q80["run_id"]),
                int(completion["run_id"]),
                exported_book_count,
                readable_export_count,
                anchored_export_count,
                contradiction_pass_count,
                promotion_status_not_promoted_count,
                promoted_gloss_count,
                primary_packet_book_count,
                heldout_packet_book_count,
                str(MD_EXPORT.relative_to(ROOT)),
                str(JSON_EXPORT.relative_to(ROOT)),
                export_human_version,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q81_controlled_shadow_export_v1_items (
                run_id, bookid, likely_speech_act, plausible_human_reading,
                confidence_tier, support_level, source_bridge_id,
                anchor_ids_json, audit_status, review_tier,
                promotion_status, packet_roles_json, blocked_claims_json,
                falsifier, next_probe, export_status, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    item["bookid"],
                    item["likely_speech_act"],
                    item["plausible_human_reading"],
                    item["confidence_tier"],
                    item["support_level"],
                    item["source_bridge_id"],
                    item["anchor_ids_json"],
                    item["audit_status"],
                    item["review_tier"],
                    item["promotion_status"],
                    j(item["packet_roles"]),
                    item["blocked_claims_json"],
                    item["falsifier"],
                    item["next_probe"],
                    item["export_status"],
                    j(item["evidence"]),
                )
                for item in items
            ],
        )

    write_exports(run_id, decision, items, summary)
    print(j({"run_id": run_id, "decision": decision, **summary}))


if __name__ == "__main__":
    main()
