#!/usr/bin/env python3
"""Q16 audit: primary-context access for the 2020 official poll option C."""

from __future__ import annotations

import datetime as dt
import json
import re
import sqlite3
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

TARGET_ID = "POLL_2020_OPTION_C"
EXACT_SEQUENCE = "663 902073 7223 67538 467 80097"
QUESTION_TEXT = "When the veils of shrouded truths are lifted, who can stand?"

OFFICIAL_URLS = [
    "https://www.tibia.com/community/?subtopic=polls&page=show&questionaireid=1009",
    "https://www.tibia.com/community/?subtopic=polls&page=show&questionaireid=1009&pollingtype=polling",
    "https://www.tibia.com/community/?subtopic=polls&page=show&questionaireid=1009&step=showresult",
    "https://www.tibia.com/community/?subtopic=polls&page=show&questionaireid=1009&answer=1",
]

COMMUNITY_CONTEXT_SOURCES = [
    {
        "source_id": "REDDIT_TODAYS_POLL_CAN_YOU_STAND_FOR",
        "source_url": "https://www.reddit.com/r/TibiaMMO/comments/g1pi5b/todays_poll_can_you_stand_for/",
        "source_tier": "community_snapshot",
        "status": "COMMUNITY_PAGE_ATTESTS_QUESTION_AND_OPTION_C",
        "risk": "not primary; useful for context and source URL only",
    },
    {
        "source_id": "S2WARD_469_GITHUB_README",
        "source_url": "https://github.com/s2ward/469",
        "source_tier": "community_research_repo",
        "status": "COMMUNITY_REPO_ATTESTS_QUESTION_AND_OPTION_C",
        "risk": "not primary; no explicit 469 meaning",
    },
    {
        "source_id": "TIBIASECRETS_ARTICLE160",
        "source_url": "https://tibiasecrets.com/article160",
        "source_tier": "community_research_article",
        "status": "COMMUNITY_ARTICLE_ATTESTS_OPTION_C_AS_2014_OR_2020_POLL_CONTEXT",
        "risk": "not primary; article analysis cannot become acceptance gate alone",
    },
]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def clean_html(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", text)


def fetch_text(url: str, timeout: int = 20) -> dict[str, object]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            html = resp.read().decode("utf-8", "replace")
            text = clean_html(html)
            return {
                "url": url,
                "ok": True,
                "status": getattr(resp, "status", None),
                "final_url": resp.geturl(),
                "length": len(html),
                "has_exact_sequence": EXACT_SEQUENCE in text,
                "has_question_text": QUESTION_TEXT in text,
                "content_preview": text[:500],
            }
    except Exception as exc:  # network result is evidence, not fatal
        return {"url": url, "ok": False, "error_type": type(exc).__name__, "error": str(exc)}


def fetch_cdx() -> dict[str, object]:
    cdx_url = (
        "https://web.archive.org/cdx?url="
        + urllib.parse.quote(OFFICIAL_URLS[0], safe="")
        + "&output=json&fl=timestamp,original,statuscode,mimetype,digest&filter=statuscode:200&collapse=digest"
    )
    try:
        req = urllib.request.Request(cdx_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8", "replace")
            try:
                parsed = json.loads(body)
            except json.JSONDecodeError:
                parsed = None
            return {
                "url": cdx_url,
                "ok": True,
                "status": getattr(resp, "status", None),
                "row_count": max(0, len(parsed) - 1) if isinstance(parsed, list) else None,
                "body_preview": body[:1000],
            }
    except urllib.error.HTTPError as exc:
        return {"url": cdx_url, "ok": False, "error_type": "HTTPError", "status": exc.code, "error": str(exc)}
    except Exception as exc:
        return {"url": cdx_url, "ok": False, "error_type": type(exc).__name__, "error": str(exc)}


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q16_poll2020_primary_context_access_audit_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            official_url_count INTEGER NOT NULL,
            official_fetch_success_count INTEGER NOT NULL,
            official_exact_content_hit_count INTEGER NOT NULL,
            wayback_cdx_success_count INTEGER NOT NULL,
            community_context_source_count INTEGER NOT NULL,
            primary_context_resolved_count INTEGER NOT NULL,
            promoted_plaintext_gloss_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q16_poll2020_primary_context_access_audit_v1_items (
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


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    open_target_run = latest_id(conn, "external_semantic_open_target_runs")
    open_target = conn.execute(
        """
        SELECT *
        FROM external_semantic_open_targets
        WHERE run_id=? AND target_id=?
        """,
        (open_target_run, TARGET_ID),
    ).fetchone()

    official_results = [fetch_text(url) for url in OFFICIAL_URLS]
    cdx_result = fetch_cdx()

    items: list[dict[str, object]] = []
    for idx, result in enumerate(official_results, start=1):
        has_content = bool(result.get("has_exact_sequence")) and bool(result.get("has_question_text"))
        items.append(
            {
                "item_id": f"official:tibia-url:{idx}",
                "item_type": "official_url_fetch",
                "source_key": str(result["url"]),
                "status": "OFFICIAL_PAGE_CONTENT_MATCHED" if has_content else "OFFICIAL_PAGE_FETCHED_WITHOUT_POLL_CONTENT" if result.get("ok") else "OFFICIAL_PAGE_FETCH_FAILED",
                "role_label": "Official Tibia poll URL access attempt.",
                "support_class": "PRIMARY_CONTEXT_MATCH" if has_content else "BLOCK_PRIMARY_CONTEXT_NOT_RESOLVED",
                "evidence_json": j(result),
            }
        )

    items.append(
        {
            "item_id": "archive:wayback-cdx",
            "item_type": "archive_cdx_fetch",
            "source_key": str(cdx_result["url"]),
            "status": "WAYBACK_CDX_ACCESS_OK" if cdx_result.get("ok") else "WAYBACK_CDX_ACCESS_FAILED",
            "role_label": "Wayback CDX attempt for official poll URL.",
            "support_class": "ARCHIVE_CONTEXT_POSSIBLE" if cdx_result.get("ok") else "BLOCK_ARCHIVE_CONTEXT_NOT_RESOLVED",
            "evidence_json": j(cdx_result),
        }
    )

    for source in COMMUNITY_CONTEXT_SOURCES:
        items.append(
            {
                "item_id": f"community:{source['source_id']}",
                "item_type": "community_context_source",
                "source_key": str(source["source_url"]),
                "status": str(source["status"]),
                "role_label": "Community source preserves poll context but is not primary.",
                "support_class": "SUPPORT_COMMUNITY_CONTEXT_ONLY",
                "evidence_json": j(source),
            }
        )

    items.append(
        {
            "item_id": "target:external-open-target",
            "item_type": "open_target_context",
            "source_key": f"run={open_target_run}:{TARGET_ID}",
            "status": str(open_target["current_status"]) if open_target else "MISSING_OPEN_TARGET",
            "role_label": "Current external target remains open pending primary context.",
            "support_class": "CONTROL_TARGET_REMAINS_OPEN",
            "evidence_json": j(dict(open_target) if open_target else {"missing": True}),
        }
    )

    official_url_count = len(OFFICIAL_URLS)
    official_fetch_success_count = sum(1 for result in official_results if result.get("ok"))
    official_exact_content_hit_count = sum(
        1 for result in official_results if result.get("has_exact_sequence") and result.get("has_question_text")
    )
    wayback_cdx_success_count = int(bool(cdx_result.get("ok")))
    community_context_source_count = len(COMMUNITY_CONTEXT_SOURCES)
    primary_context_resolved_count = int(official_exact_content_hit_count > 0 or wayback_cdx_success_count > 0)
    promoted_plaintext_gloss_count = 0

    decision = (
        "Q16_POLL_2020_PRIMARY_CONTEXT_STILL_OPEN_COMMUNITY_CONTEXT_ONLY_NO_GLOSS"
        if official_url_count == len(OFFICIAL_URLS)
        and official_exact_content_hit_count == 0
        and primary_context_resolved_count == 0
        and community_context_source_count >= 3
        and promoted_plaintext_gloss_count == 0
        else "Q16_POLL_2020_PRIMARY_CONTEXT_AUDIT_REQUIRES_MANUAL_REVIEW"
    )

    payload = {
        "question": "Can the 2020 official poll option C target be closed from current primary/archived access?",
        "answer": "No. Current official URLs did not expose the poll content, and the archive/CDX attempt did not resolve a usable primary snapshot in this run.",
        "allowed_reading": "Use community sources as context/backlog pointers only.",
        "blocked_reading": "Do not promote option C semantics, and do not treat community copies as the primary acceptance gate.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q16_poll2020_primary_context_access_audit_v1_runs (
                created_at, decision, official_url_count,
                official_fetch_success_count, official_exact_content_hit_count,
                wayback_cdx_success_count, community_context_source_count,
                primary_context_resolved_count, promoted_plaintext_gloss_count,
                payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                official_url_count,
                official_fetch_success_count,
                official_exact_content_hit_count,
                wayback_cdx_success_count,
                community_context_source_count,
                primary_context_resolved_count,
                promoted_plaintext_gloss_count,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q16_poll2020_primary_context_access_audit_v1_items (
                run_id, item_id, item_type, source_key, status,
                role_label, support_class, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    item["item_id"],
                    item["item_type"],
                    item["source_key"],
                    item["status"],
                    item["role_label"],
                    item["support_class"],
                    item["evidence_json"],
                )
                for item in items
            ],
        )

    print(
        j(
            {
                "run_id": run_id,
                "decision": decision,
                "official_url_count": official_url_count,
                "official_fetch_success_count": official_fetch_success_count,
                "official_exact_content_hit_count": official_exact_content_hit_count,
                "wayback_cdx_success_count": wayback_cdx_success_count,
                "community_context_source_count": community_context_source_count,
                "primary_context_resolved_count": primary_context_resolved_count,
                "promoted_plaintext_gloss_count": promoted_plaintext_gloss_count,
            }
        )
    )


if __name__ == "__main__":
    main()
