#!/usr/bin/env python3
"""Q19: confirm the Tibia.org Avar Tar variant in Wayback and update the open target."""

from __future__ import annotations

import datetime as dt
import json
import re
import sqlite3
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

TARGET_ID = "TIBIA_ORG_AVAR_VARIANT"
EXACT_SEQUENCE = "62792068657272657261"
SNAPSHOT_TIMESTAMP = "20200915225804"
SNAPSHOT_URL = f"https://web.archive.org/web/{SNAPSHOT_TIMESTAMP}id_/http://www.tibia.org/"
CURRENT_URL = "http://tibia.org/"
FULL_AVAR_VARIANT = (
    "29639 46781! 9063376290 3222011 677 80322429 67538 14805394, "
    "6880326 677 62792068657272657261 337011 72683 149630 4378! "
    "453 639 578300 986372 2953639!"
)


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def fetch(url: str) -> dict[str, object]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            html = resp.read().decode("utf-8", "replace")
            text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))
            pos = html.find(EXACT_SEQUENCE)
            return {
                "url": url,
                "ok": True,
                "status": getattr(resp, "status", None),
                "length": len(html),
                "has_exact_sequence": EXACT_SEQUENCE in html or EXACT_SEQUENCE in text,
                "has_full_avar_variant": FULL_AVAR_VARIANT in html or FULL_AVAR_VARIANT in text,
                "exact_sequence_pos": pos,
                "html_context": html[max(0, pos - 400) : pos + 700] if pos >= 0 else "",
                "text_preview": text[:500],
            }
    except Exception as exc:
        return {"url": url, "ok": False, "error_type": type(exc).__name__, "error": str(exc)}


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q19_tibia_org_avar_variant_wayback_confirmation_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            source_open_target_run_id INTEGER NOT NULL,
            new_open_target_run_id INTEGER NOT NULL,
            current_tibia_org_sequence_hit_count INTEGER NOT NULL,
            wayback_sequence_hit_count INTEGER NOT NULL,
            wayback_full_variant_hit_count INTEGER NOT NULL,
            existing_micro_anchor_count INTEGER NOT NULL,
            explicit_meaning_attested_count INTEGER NOT NULL,
            promoted_plaintext_gloss_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q19_tibia_org_avar_variant_wayback_confirmation_v1_items (
            run_id INTEGER NOT NULL,
            item_id TEXT NOT NULL,
            item_type TEXT NOT NULL,
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


def rows(conn: sqlite3.Connection, sql: str, params: tuple[object, ...] = ()) -> list[sqlite3.Row]:
    return list(conn.execute(sql, params).fetchall())


def add_item(
    out: list[dict[str, object]],
    item_id: str,
    item_type: str,
    source_key: str,
    status: str,
    role_label: str,
    support_class: str,
    evidence: object,
) -> None:
    out.append(
        {
            "item_id": item_id,
            "item_type": item_type,
            "source_key": source_key,
            "status": status,
            "role_label": role_label,
            "support_class": support_class,
            "evidence_json": j(evidence),
        }
    )


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    source_open_target_run_id = latest_id(conn, "external_semantic_open_target_runs")
    micro_anchor_run_id = latest_id(conn, "narcissist_micro_anchor_runs")
    micro_anchor = conn.execute(
        """
        SELECT *
        FROM narcissist_micro_anchor_runs
        WHERE run_id=?
        """,
        (micro_anchor_run_id,),
    ).fetchone()

    current_fetch = fetch(CURRENT_URL)
    wayback_fetch = fetch(SNAPSHOT_URL)

    source_targets = rows(
        conn,
        """
        SELECT *
        FROM external_semantic_open_targets
        WHERE run_id=?
        ORDER BY priority, target_id
        """,
        (source_open_target_run_id,),
    )
    if not source_targets:
        raise RuntimeError("missing open target rows")

    updated_targets: list[dict[str, object]] = []
    for row in source_targets:
        payload = json.loads(str(row["payload_json"] or "{}"))
        item = dict(row)
        if str(row["target_id"]) == TARGET_ID:
            payload.update(
                {
                    "q19_wayback_snapshot": SNAPSHOT_URL,
                    "q19_exact_sequence_confirmed": bool(wayback_fetch.get("has_exact_sequence")),
                    "q19_full_variant_confirmed": bool(wayback_fetch.get("has_full_avar_variant")),
                    "q19_acceptance_gate": "explicit meaning still required for semantic promotion",
                }
            )
            item.update(
                {
                    "current_status": "PRIMARY_ARCHIVE_SEQUENCE_CONFIRMED_NO_EXPLICIT_MEANING",
                    "required_evidence": "explicit source-attested meaning or independent in-game semantic bridge required for semantic promotion",
                    "next_action": "use archived tibia.org sequence as primary phrase/micro-anchor context only; do not promote full phrase or book gloss",
                    "payload_json": j(payload),
                }
            )
        updated_targets.append(item)

    current_tibia_org_sequence_hit_count = int(bool(current_fetch.get("has_exact_sequence")))
    wayback_sequence_hit_count = int(bool(wayback_fetch.get("has_exact_sequence")))
    wayback_full_variant_hit_count = int(bool(wayback_fetch.get("has_full_avar_variant")))
    existing_micro_anchor_count = int(
        micro_anchor is not None
        and str(micro_anchor["decision"]) == "NARCISSIST_MICRO_ANCHOR_ACCEPTED_PROVISIONAL"
        and int(micro_anchor["exact_match"]) == 1
    )
    explicit_meaning_attested_count = 0
    promoted_plaintext_gloss_count = 0

    decision = (
        "Q19_TIBIA_ORG_AVAR_VARIANT_PRIMARY_ARCHIVE_CONFIRMED_MICRO_ANCHOR_ONLY_NO_GLOSS"
        if wayback_sequence_hit_count == 1
        and wayback_full_variant_hit_count == 1
        and existing_micro_anchor_count == 1
        and explicit_meaning_attested_count == 0
        and promoted_plaintext_gloss_count == 0
        else "Q19_TIBIA_ORG_AVAR_VARIANT_WAYBACK_CONFIRMATION_REQUIRES_MANUAL_REVIEW"
    )

    items: list[dict[str, object]] = []
    add_item(
        items,
        "source:current-tibia-org",
        "current_source_fetch",
        CURRENT_URL,
        "CURRENT_TIBIA_ORG_NO_SEQUENCE_HIT" if current_tibia_org_sequence_hit_count == 0 else "CURRENT_TIBIA_ORG_SEQUENCE_HIT",
        "Current tibia.org does not provide the old hidden Avar variant in this fetch.",
        "CONTROL_CURRENT_SITE_NOT_SOURCE",
        current_fetch,
    )
    add_item(
        items,
        "source:wayback-20200915225804",
        "archive_source_fetch",
        SNAPSHOT_URL,
        "WAYBACK_TIBIA_ORG_AVAR_VARIANT_EXACT_SEQUENCE_CONFIRMED" if wayback_sequence_hit_count else "WAYBACK_TIBIA_ORG_VARIANT_NOT_FOUND",
        "Wayback snapshot contains the hidden HTML-comment Avar Tar variant with 62792068657272657261.",
        "SUPPORT_PRIMARY_ARCHIVE_SEQUENCE_CONFIRMED_NO_MEANING",
        wayback_fetch,
    )
    add_item(
        items,
        "anchor:narcissist-micro",
        "existing_micro_anchor",
        f"narcissist_micro_anchor_runs:{micro_anchor_run_id}",
        str(micro_anchor["decision"]) if micro_anchor else "MISSING_NARCISSIST_MICRO_ANCHOR",
        "Existing row0 micro-anchor decodes 62792068657272657261 as NARCISSIST provisionally.",
        "SUPPORT_MICRO_ANCHOR_PROVISIONAL_NO_BOOK_PROMOTION",
        dict(micro_anchor) if micro_anchor else {"missing": True},
    )

    high_priority_count = sum(1 for row in updated_targets if int(row["priority"]) == 1)
    with conn:
        cur = conn.execute(
            """
            INSERT INTO external_semantic_open_target_runs (
                created_at, decision, target_count, high_priority_count, payload_json
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                now(),
                "EXTERNAL_SEMANTIC_OPEN_TARGETS_UPDATED_AFTER_TIBIA_ORG_AVAR_Q19",
                len(updated_targets),
                high_priority_count,
                j({"updated_target": TARGET_ID, "q19_decision": decision}),
            ),
        )
        new_open_target_run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO external_semantic_open_targets (
                run_id, target_id, target_class, exact_sequence,
                current_status, priority, required_evidence,
                next_action, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    new_open_target_run_id,
                    str(row["target_id"]),
                    str(row["target_class"]),
                    str(row["exact_sequence"]),
                    str(row["current_status"]),
                    int(row["priority"]),
                    str(row["required_evidence"]),
                    str(row["next_action"]),
                    str(row["payload_json"]),
                )
                for row in updated_targets
            ],
        )

        cur = conn.execute(
            """
            INSERT INTO human_q19_tibia_org_avar_variant_wayback_confirmation_v1_runs (
                created_at, decision, source_open_target_run_id,
                new_open_target_run_id, current_tibia_org_sequence_hit_count,
                wayback_sequence_hit_count, wayback_full_variant_hit_count,
                existing_micro_anchor_count, explicit_meaning_attested_count,
                promoted_plaintext_gloss_count, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                source_open_target_run_id,
                new_open_target_run_id,
                current_tibia_org_sequence_hit_count,
                wayback_sequence_hit_count,
                wayback_full_variant_hit_count,
                existing_micro_anchor_count,
                explicit_meaning_attested_count,
                promoted_plaintext_gloss_count,
                j(
                    {
                        "question": "Does the Tibia.org Avar Tar variant have primary archived sequence evidence?",
                        "answer": "Yes for the sequence; no for explicit meaning.",
                        "snapshot_url": SNAPSHOT_URL,
                        "target_updated_to": "PRIMARY_ARCHIVE_SEQUENCE_CONFIRMED_NO_EXPLICIT_MEANING",
                    }
                ),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q19_tibia_org_avar_variant_wayback_confirmation_v1_items (
                run_id, item_id, item_type, source_key, status,
                role_label, support_class, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    str(row["item_id"]),
                    str(row["item_type"]),
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
                "source_open_target_run_id": source_open_target_run_id,
                "new_open_target_run_id": new_open_target_run_id,
                "current_tibia_org_sequence_hit_count": current_tibia_org_sequence_hit_count,
                "wayback_sequence_hit_count": wayback_sequence_hit_count,
                "wayback_full_variant_hit_count": wayback_full_variant_hit_count,
                "existing_micro_anchor_count": existing_micro_anchor_count,
                "explicit_meaning_attested_count": explicit_meaning_attested_count,
                "promoted_plaintext_gloss_count": promoted_plaintext_gloss_count,
            }
        )
    )


if __name__ == "__main__":
    main()
