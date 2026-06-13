#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import os
import sqlite3
import subprocess
from typing import Any

DB_DEFAULT = "./data/bonelord_operational.sqlite"
DISCORD_CHANNEL = "0"
DISCORD_SCRIPT = "~/.codex/skills/discord/scripts/discord_skill.py"


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(x: Any) -> str:
    return json.dumps(x, ensure_ascii=False, sort_keys=True)


def rows(cur, sql, params=()):
    return [dict(r) for r in cur.execute(sql, params).fetchall()]


def latest(cur, table: str):
    r = cur.execute(f"select max(run_id) from {table}").fetchone()
    return r[0] if r and r[0] is not None else None


def create_tables(cur):
    cur.executescript(
        """
        create table if not exists final_honest_reading_v3_runs (
            run_id integer primary key autoincrement,
            created_at text not null,
            decision text not null,
            source_v2_run_id integer not null,
            source_contrast_run_id integer not null,
            book_count integer not null,
            audit_covered_book_count integer not null,
            functional_tagged_book_count integer not null,
            semantic_gloss_allowed_count integer not null,
            operational_coverage_pct real not null,
            semantic_gloss_pct real not null,
            payload_json text not null
        );
        create table if not exists final_honest_reading_v3_books (
            run_id integer not null,
            bookid text not null,
            reading_status text not null,
            audit_covered integer not null,
            gloss_allowed integer not null,
            functional_tag_count integer not null,
            functional_tags_json text not null,
            honest_text text not null,
            evidence_json text not null,
            primary key (run_id, bookid)
        );
        """
    )


def add_tag(tags, tag_id, label, source, confidence):
    tags.append({"tag_id": tag_id, "label": label, "source": source, "confidence": confidence, "gloss_allowed": False})


def build_book_tags(cur):
    tags_by_book: dict[str, list[dict[str, Any]]] = {}

    for r in rows(cur, "select * from vinvin_branch_subfunction_items where run_id=(select max(run_id) from vinvin_branch_subfunction_items)"):
        books = json.loads(r["books_json"] or "[]")
        if r["branch_status"] == "SUBFUNCTION_READY":
            for b in books:
                add_tag(tags_by_book.setdefault(str(b), []), "VINVIN_BRANCH_SUBFUNCTION", f"branch selector: {r['suffix_class']}", "vinvin_branch_subfunction_items", float(r["branch_score"]))
        else:
            for b in books:
                add_tag(tags_by_book.setdefault(str(b), []), "VINVIN_NEGATIVE_CONTROL", f"negative/partial branch control: {r['suffix_class']}", "vinvin_branch_subfunction_items", float(r["branch_score"]))

    for r in rows(cur, "select * from c68_fatct_slot_items where run_id=(select max(run_id) from c68_fatct_slot_items)"):
        label = "local NAESE/IVIFAST slot classifier" if r["context_class"] == "CANONICAL_NAESE_FATCT_SLOT" else f"C68/FATCT variant control: {r['context_class']}"
        conf = 0.81 if r["context_class"] == "CANONICAL_NAESE_FATCT_SLOT" else 0.42
        add_tag(tags_by_book.setdefault(str(r["bookid"]), []), "NAESE_C68_FATCT_LOCAL_SLOT", label, "c68_fatct_slot_items", conf)

    for r in rows(cur, "select * from r20_r02_phase_frame_items where run_id=(select max(run_id) from r20_r02_phase_frame_items)"):
        books = json.loads(r["books_json"] or "[]")
        if r["phase_status"] == "PHASE_FRAME_READY":
            label = f"phase boundary/bridge frame: {r['frame_key']}"
            conf = float(r["phase_score"])
        elif "MICRO" in r["frame_key"]:
            label = f"micro context audit-only: {r['frame_key']}"
            conf = float(r["phase_score"])
        else:
            label = f"phase-related covered context: {r['frame_key']}"
            conf = float(r["phase_score"])
        for b in books:
            add_tag(tags_by_book.setdefault(str(b), []), "R20_R02_PHASE_FRAME", label, "r20_r02_phase_frame_items", conf)

    return tags_by_book


def send_discord(message: str):
    if not os.path.exists(DISCORD_SCRIPT):
        return
    cmd = f"source ~/.env 2>/dev/null || true; python {DISCORD_SCRIPT} send --channel {DISCORD_CHANNEL} --message {json.dumps(message)}"
    subprocess.run(["/bin/zsh", "-lc", cmd], check=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DB_DEFAULT)
    ap.add_argument("--discord", action="store_true")
    args = ap.parse_args()

    con = sqlite3.connect(args.db)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    create_tables(cur)

    v2_run = latest(cur, "final_honest_reading_v2_books")
    contrast_run = latest(cur, "semantic_contrast_checkpoint_items")
    source_books = rows(cur, "select * from final_honest_reading_v2_books where run_id=? order by cast(bookid as integer)", (v2_run,))
    tags_by_book = build_book_tags(cur)

    decision = "FINAL_HONEST_READING_V3_FUNCTIONAL_TAGS_NO_SEMANTIC_TRANSLATION"
    book_count = len(source_books)
    audit_count = sum(int(b["audit_covered"]) for b in source_books)
    tagged_count = sum(1 for b in source_books if tags_by_book.get(str(b["bookid"])))
    gloss_count = 0
    coverage = round((audit_count / book_count) * 100, 3) if book_count else 0.0
    semantic_pct = 0.0

    cur.execute(
        """
        insert into final_honest_reading_v3_runs
        (created_at, decision, source_v2_run_id, source_contrast_run_id, book_count, audit_covered_book_count,
         functional_tagged_book_count, semantic_gloss_allowed_count, operational_coverage_pct, semantic_gloss_pct, payload_json)
        values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (now(), decision, v2_run, contrast_run, book_count, audit_count, tagged_count, gloss_count, coverage, semantic_pct,
         j({"note": "v3 adds functional tags only; it does not convert book text to English plaintext"})),
    )
    run_id = cur.lastrowid

    for b in source_books:
        bookid = str(b["bookid"])
        tags = tags_by_book.get(bookid, [])
        status = "FUNCTIONALLY_TAGGED_NO_GLOSS" if tags else b["reading_status"]
        tag_prefix = ""
        if tags:
            compact = "; ".join(t["label"] for t in tags)
            tag_prefix = f"<FUNCTIONAL:{compact}> "
        evidence = json.loads(b["evidence_json"] or "{}")
        evidence["v3_functional_tags"] = tags
        cur.execute(
            """
            insert into final_honest_reading_v3_books
            (run_id, bookid, reading_status, audit_covered, gloss_allowed, functional_tag_count,
             functional_tags_json, honest_text, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, bookid, status, int(b["audit_covered"]), 0, len(tags), j(tags), tag_prefix + b["honest_text"], j(evidence)),
        )

    con.commit()
    out = {
        "run_id": run_id,
        "decision": decision,
        "book_count": book_count,
        "audit_covered_book_count": audit_count,
        "functional_tagged_book_count": tagged_count,
        "semantic_gloss_allowed_count": gloss_count,
        "operational_coverage_pct": coverage,
        "semantic_gloss_pct": semantic_pct,
    }
    print(json.dumps(out, ensure_ascii=False))

    if args.discord:
        send_discord("\n".join([
            f"[469][honest-reading-v3][run={run_id}] camada funcional gerada sem inventar tradução",
            f"livros={book_count} | cobertos={audit_count}/{book_count} ({coverage}%) | livros com tags funcionais={tagged_count} | gloss lexical={semantic_pct}%",
            "o que avançou: rótulos auditáveis de branch/slot/fase foram aplicados aos livros onde há contraste interno; nenhum texto dos livros foi convertido para inglês sem prova externa.",
            "estado honesto: estrutura/função avançando; tradução lexical dos livros continua não resolvida.",
        ]))


if __name__ == "__main__":
    main()
