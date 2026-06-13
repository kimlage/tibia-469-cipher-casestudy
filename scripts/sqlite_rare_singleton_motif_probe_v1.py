#!/usr/bin/env python3
"""Probe rare/singleton unresolved row0 motifs by substring containment and contrast."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
TARGETS = ("7", "20", "25", "39", "49", "54")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def lcs(a: str, b: str) -> str:
    if not a or not b:
        return ""
    prev = [0] * (len(b) + 1)
    best_len = 0
    best_end = 0
    for i, ca in enumerate(a, 1):
        cur = [0] * (len(b) + 1)
        for j, cb in enumerate(b, 1):
            if ca == cb:
                cur[j] = prev[j - 1] + 1
                if cur[j] > best_len:
                    best_len = cur[j]
                    best_end = i
        prev = cur
    return a[best_end - best_len:best_end]


def ngrams(s: str, n: int):
    return {s[i:i+n] for i in range(0, max(0, len(s) - n + 1))}


def main() -> None:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        create table if not exists rare_singleton_motif_probe_v1_runs (
            run_id integer primary key autoincrement,
            created_at text not null,
            decision text not null,
            target_count integer not null,
            motif_family_count integer not null,
            structural_promotion_count integer not null,
            semantic_promotion_count integer not null,
            accepted_prose_gloss_count integer not null,
            summary_json text not null
        );
        create table if not exists rare_singleton_motif_probe_v1_items (
            run_id integer not null,
            bookid text not null,
            motif_family text not null,
            probe_status text not null,
            proposed_role text not null,
            structural_promotion_allowed integer not null,
            semantic_promotion_allowed integer not null,
            prose_gloss_allowed integer not null,
            best_anchor text not null,
            best_lcs_len integer not null,
            best_lcs_text text not null,
            containment_parent text not null,
            reason text not null,
            next_action text not null,
            evidence_json text not null,
            primary key (run_id, bookid)
        );
        """
    )
    rows = {
        r["bookid"]: r["symbol_text"]
        for r in conn.execute("select bookid, symbol_text from row0_variant_book_tokens")
    }
    statuses = {
        r["bookid"]: dict(r)
        for r in conn.execute(
            """
            select bookid, current_status, current_reading, next_method
            from remaining_gap_checkpoint_v1_items
            where run_id=(select max(run_id) from remaining_gap_checkpoint_v1_items)
            """
        )
    }

    items = []
    for bookid in TARGETS:
        text = rows[bookid]
        best = ("NONE", "")
        containers = []
        for other, other_text in rows.items():
            if other == bookid:
                continue
            common = lcs(text, other_text)
            if len(common) > len(best[1]):
                best = (other, common)
            if text in other_text:
                containers.append(other)

        # Family-specific classifications: structural only, not semantic.
        if bookid in ("25", "39"):
            motif_family = "FASTBEIE_INTEIIS_SHORT_LONG_PAIR"
            proposed_role = "RARE_MOTIF_PAIR_STRUCTURAL_COMPONENT"
            structural_allowed = 1
            reason = "Book 25 is a near-complete short motif embedded in book 39, giving a reliable structural pair but not a semantic function."
            next_action = "Use as structural contrast pair; seek where FASTBEIE motif attaches to accepted functional anchors before semantic promotion."
        elif bookid in ("20", "54"):
            motif_family = "FNTFEIFAIFAINIIETNEEIVN_SHARED_TAIL_PAIR"
            proposed_role = "RARE_SHARED_TAIL_STRUCTURAL_COMPONENT"
            structural_allowed = 1
            reason = "Books 20 and 54 share a long tail motif, reliable as a structural pair but currently detached from accepted functional anchors."
            next_action = "Use pair as anchor for rare-tail boundary tests; do not assign meaning without a bridge to contigs or accepted roles."
        elif bookid == "7":
            motif_family = "ELBEE_AETTA_SURFACE_SINGLETON"
            proposed_role = "RARE_SURFACE_SINGLETON_AUDIT"
            structural_allowed = 0
            reason = "Book 7 has no strong family containment; only weak surface fragments, so confirmation would likely be no-op."
            next_action = "Keep unresolved; reopen only if SQLite ngram context links ELBEE/AETTA to accepted role transitions."
        else:
            motif_family = "NEE_EILE_REPETITIVE_SINGLETON"
            proposed_role = "RARE_REPETITIVE_SINGLETON_AUDIT"
            structural_allowed = 0
            reason = "Book 49 is dominated by repetitive NEE/EILE material with no reliable accepted-role bridge."
            next_action = "Treat as low-information singleton until repetition model or external exact evidence improves."

        evidence = {
            "status": statuses.get(bookid),
            "symbol_text": text,
            "containers": containers,
            "best_lcs_anchor": best[0],
            "best_lcs_text": best[1],
            "target_6grams_sample": sorted(ngrams(text, 6))[:20],
        }
        items.append(
            {
                "bookid": bookid,
                "motif_family": motif_family,
                "probe_status": "STRUCTURAL_PAIR_NO_GLOSS" if structural_allowed else "AUDIT_SINGLETON_NO_GLOSS",
                "proposed_role": proposed_role,
                "structural_promotion_allowed": structural_allowed,
                "semantic_promotion_allowed": 0,
                "prose_gloss_allowed": 0,
                "best_anchor": best[0],
                "best_lcs_len": len(best[1]),
                "best_lcs_text": best[1],
                "containment_parent": ",".join(containers) if containers else "NONE",
                "reason": reason,
                "next_action": next_action,
                "evidence_json": json.dumps(evidence, ensure_ascii=False, sort_keys=True),
            }
        )

    family_count = len({i["motif_family"] for i in items})
    structural_count = sum(i["structural_promotion_allowed"] for i in items)
    summary = {
        "targets": list(TARGETS),
        "families": sorted({i["motif_family"] for i in items}),
        "structural_only_promotions": structural_count,
        "semantic_promotions": 0,
        "accepted_prose_glosses": 0,
    }
    cur = conn.execute(
        """
        insert into rare_singleton_motif_probe_v1_runs
        (created_at, decision, target_count, motif_family_count, structural_promotion_count,
         semantic_promotion_count, accepted_prose_gloss_count, summary_json)
        values (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (utc_now(), "RARE_MOTIFS_STRUCTURAL_ONLY_NO_SEMANTIC_GLOSS", len(TARGETS), family_count, structural_count, 0, 0, json.dumps(summary, ensure_ascii=False, sort_keys=True)),
    )
    run_id = cur.lastrowid
    for item in items:
        conn.execute(
            """
            insert into rare_singleton_motif_probe_v1_items
            (run_id, bookid, motif_family, probe_status, proposed_role,
             structural_promotion_allowed, semantic_promotion_allowed, prose_gloss_allowed,
             best_anchor, best_lcs_len, best_lcs_text, containment_parent, reason, next_action, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, item["bookid"], item["motif_family"], item["probe_status"], item["proposed_role"], item["structural_promotion_allowed"], item["semantic_promotion_allowed"], item["prose_gloss_allowed"], item["best_anchor"], item["best_lcs_len"], item["best_lcs_text"], item["containment_parent"], item["reason"], item["next_action"], item["evidence_json"]),
        )
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": "RARE_MOTIFS_STRUCTURAL_ONLY_NO_SEMANTIC_GLOSS", **summary}, ensure_ascii=False))


if __name__ == "__main__":
    main()
