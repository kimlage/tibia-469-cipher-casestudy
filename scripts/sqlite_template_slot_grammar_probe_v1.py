#!/usr/bin/env python3
"""Infer conservative template/slot grammar candidates from accepted functional books."""
from __future__ import annotations

import json
import sqlite3
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def lcp(strings):
    if not strings:
        return ""
    pref = strings[0]
    for s in strings[1:]:
        while not s.startswith(pref) and pref:
            pref = pref[:-1]
    return pref


def lcsuf(strings):
    rev = [s[::-1] for s in strings]
    return lcp(rev)[::-1]


def motifs(s: str):
    known = ["BENNA", "NAESE", "VINVIN", "VNCTIIN", "ONAF", "FNAAST", "LTAST", "VFETTIIT", "VTLRNEFIE", "BTILBETA"]
    return [m for m in known if m in s]


def main() -> None:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        create table if not exists template_slot_grammar_probe_v1_runs (
            run_id integer primary key autoincrement,
            created_at text not null,
            decision text not null,
            role_count integer not null,
            template_count integer not null,
            residual_testable_count integer not null,
            accepted_prose_gloss_count integer not null,
            summary_json text not null
        );
        create table if not exists template_slot_grammar_probe_v1_templates (
            run_id integer not null,
            functional_reading text not null,
            support_count integer not null,
            support_books text not null,
            common_prefix text not null,
            common_suffix text not null,
            shared_motifs text not null,
            grammar_status text not null,
            next_action text not null,
            evidence_json text not null,
            primary key (run_id, functional_reading)
        );
        create table if not exists template_slot_grammar_probe_v1_residuals (
            run_id integer not null,
            bookid text not null,
            best_template text not null,
            match_status text not null,
            shared_motifs text not null,
            recommendation text not null,
            evidence_json text not null,
            primary key (run_id, bookid)
        );
        """
    )
    latest = conn.execute("select max(run_id) as run_id from honest_full_functional_reading_v1_books").fetchone()["run_id"]
    rows = list(conn.execute(
        """
        select b.bookid, b.status, b.functional_reading, t.symbol_text
        from honest_full_functional_reading_v1_books b
        join row0_variant_book_tokens t on t.bookid=b.bookid
        where b.run_id=? and b.status in ('FUNCTIONAL_CORE','FUNCTIONAL_RELATED')
        order by b.bookid+0
        """,
        (latest,),
    ))
    by_role = defaultdict(list)
    for r in rows:
        by_role[r["functional_reading"]].append(r)

    templates = []
    for role, rs in sorted(by_role.items()):
        texts = [r["symbol_text"] for r in rs]
        books = [r["bookid"] for r in rs]
        pref = lcp(texts)
        suf = lcsuf(texts)
        shared = sorted(set.intersection(*(set(motifs(t)) for t in texts))) if len(texts) > 1 else motifs(texts[0])
        support = len(rs)
        if support >= 2 and (len(pref) >= 8 or len(suf) >= 8 or shared):
            status = "TEMPLATE_CANDIDATE_NO_GLOSS"
            next_action = "Use as structural slot frame; test residuals by motif/boundary concordance only."
        elif support >= 2:
            status = "PAIR_ONLY_WEAK_TEMPLATE_NO_GLOSS"
            next_action = "Keep as pair/variant frame until boundary evidence improves."
        else:
            status = "SINGLETON_ROLE_NO_TEMPLATE"
            next_action = "Do not project to residuals without additional support."
        templates.append({"role": role, "books": books, "texts": texts, "prefix": pref, "suffix": suf, "shared": shared, "status": status, "next_action": next_action})

    residuals = list(conn.execute(
        """
        select g.bookid, g.current_status, g.current_reading, g.next_method, t.symbol_text
        from remaining_gap_checkpoint_v1_items g
        join row0_variant_book_tokens t on t.bookid=g.bookid
        where g.run_id=(select max(run_id) from remaining_gap_checkpoint_v1_items)
        order by g.bookid+0
        """
    ))
    residual_items = []
    for r in residuals:
        rmotifs = set(motifs(r["symbol_text"]))
        best = ("NONE", 0, [])
        for tmpl in templates:
            if tmpl["status"] == "SINGLETON_ROLE_NO_TEMPLATE":
                continue
            overlap = sorted(rmotifs.intersection(tmpl["shared"]))
            score = len(overlap)
            if tmpl["prefix"] and tmpl["prefix"] in r["symbol_text"]:
                score += 2
            if tmpl["suffix"] and tmpl["suffix"] in r["symbol_text"]:
                score += 2
            if score > best[1]:
                best = (tmpl["role"], score, overlap)
        if best[1] >= 3:
            status = "TESTABLE_TEMPLATE_CONCORDANCE_REQUIRED"
            rec = "Potential non-LCS template concordance; run contrast with negative controls before promotion."
        elif best[1] > 0:
            status = "WEAK_MOTIF_OVERLAP_ONLY"
            rec = "Weak motif overlap; keep held unless boundary concordance improves."
        else:
            status = "NO_TEMPLATE_SIGNAL"
            rec = "No template projection signal."
        residual_items.append({"bookid": r["bookid"], "best_template": best[0], "match_status": status, "shared_motifs": best[2], "recommendation": rec, "evidence": dict(r)})

    testable = sum(1 for x in residual_items if x["match_status"] == "TESTABLE_TEMPLATE_CONCORDANCE_REQUIRED")
    summary = {
        "latest_honest_run": latest,
        "template_status_counts": {},
        "residual_status_counts": {},
        "principle": "template grammar is structural only; accepted prose gloss remains zero",
    }
    for t in templates:
        summary["template_status_counts"][t["status"]] = summary["template_status_counts"].get(t["status"], 0) + 1
    for r in residual_items:
        summary["residual_status_counts"][r["match_status"]] = summary["residual_status_counts"].get(r["match_status"], 0) + 1

    cur = conn.execute(
        """
        insert into template_slot_grammar_probe_v1_runs
        (created_at, decision, role_count, template_count, residual_testable_count, accepted_prose_gloss_count, summary_json)
        values (?, ?, ?, ?, ?, ?, ?)
        """,
        (utc_now(), "TEMPLATE_SLOT_GRAMMAR_STRUCTURAL_NO_GLOSS", len(by_role), sum(1 for t in templates if t["status"] != "SINGLETON_ROLE_NO_TEMPLATE"), testable, 0, json.dumps(summary, ensure_ascii=False, sort_keys=True)),
    )
    run_id = cur.lastrowid
    for t in templates:
        conn.execute(
            """
            insert into template_slot_grammar_probe_v1_templates
            (run_id, functional_reading, support_count, support_books, common_prefix, common_suffix, shared_motifs, grammar_status, next_action, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, t["role"], len(t["books"]), ",".join(t["books"]), t["prefix"], t["suffix"], ",".join(t["shared"]), t["status"], t["next_action"], json.dumps({"books": t["books"], "texts": t["texts"]}, ensure_ascii=False, sort_keys=True)),
        )
    for r in residual_items:
        conn.execute(
            """
            insert into template_slot_grammar_probe_v1_residuals
            (run_id, bookid, best_template, match_status, shared_motifs, recommendation, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, r["bookid"], r["best_template"], r["match_status"], ",".join(r["shared_motifs"]), r["recommendation"], json.dumps(r["evidence"], ensure_ascii=False, sort_keys=True)),
        )
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": "TEMPLATE_SLOT_GRAMMAR_STRUCTURAL_NO_GLOSS", "role_count": len(by_role), "template_count": sum(1 for t in templates if t["status"] != "SINGLETON_ROLE_NO_TEMPLATE"), "residual_testable_count": testable, "accepted_prose_gloss_count": 0, "summary": summary}, ensure_ascii=False))


if __name__ == "__main__":
    main()
