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


def now():
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(x: Any):
    return json.dumps(x, ensure_ascii=False, sort_keys=True)


def one(cur, sql, params=()):
    r = cur.execute(sql, params).fetchone()
    return dict(r) if r else {}


def rows(cur, sql, params=()):
    return [dict(r) for r in cur.execute(sql, params).fetchall()]


def table_exists(cur, table: str) -> bool:
    return bool(
        cur.execute(
            "select 1 from sqlite_master where type in ('table', 'view') and name=?",
            (table,),
        ).fetchone()
    )


def create(cur):
    cur.executescript("""
    create table if not exists translation_progress_status_runs (
        run_id integer primary key autoincrement,
        created_at text not null,
        decision text not null,
        operational_coverage_pct real not null,
        functional_tagged_book_pct real not null,
        semantic_gloss_pct real not null,
        phrase_level_gt_count integer not null,
        book_decode_anchor_count integer not null,
        actionable_frontier_count integer not null,
        payload_json text not null
    );
    """)


def send(message: str):
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
    create(cur)

    v3 = {}
    status_counts = []
    source_layer = None
    if table_exists(cur, "final_honest_reading_v19_runs"):
        v19 = one(cur, "select * from final_honest_reading_v19_runs order by run_id desc limit 1")
        if v19:
            source_layer = "final_honest_reading_v19"
            book_count_row = one(
                cur,
                """
                select
                    count(*) as book_count,
                    sum(case when audit_covered=1 then 1 else 0 end) as audit_covered_book_count,
                    sum(case when gloss_allowed=1 then 1 else 0 end) as semantic_gloss_allowed_count
                from final_honest_reading_v19_books
                where run_id=(select max(run_id) from final_honest_reading_v19_books)
                """,
            )
            book_count = int(book_count_row.get("book_count") or 0)
            tagged = int(v19.get("functionally_tagged_count") or 0)
            gloss_allowed = int(v19.get("gloss_allowed_count") or 0)
            v3 = {
                **v19,
                "book_count": book_count,
                "audit_covered_book_count": int(book_count_row.get("audit_covered_book_count") or 0),
                "functional_tagged_book_count": tagged,
                "functional_tagged_book_pct": round(tagged / book_count * 100, 3) if book_count else 0.0,
                "operational_coverage_pct": 100.0 if book_count and int(book_count_row.get("audit_covered_book_count") or 0) == book_count else 0.0,
                "semantic_gloss_allowed_count": gloss_allowed,
                "semantic_gloss_pct": round(gloss_allowed / book_count * 100, 3) if book_count else 0.0,
            }
            status_counts = rows(
                cur,
                """
                select reading_status, count(*) as n
                from final_honest_reading_v19_books
                where run_id=(select max(run_id) from final_honest_reading_v19_books)
                group by reading_status
                """,
            )

    if not v3:
        v3 = one(cur, "select * from final_honest_reading_v16_runs order by run_id desc limit 1")
        if v3:
            source_layer = "final_honest_reading_v16"
    if not v3:
        v3 = one(cur, "select * from final_honest_reading_v15_runs order by run_id desc limit 1")
        if v3:
            source_layer = "final_honest_reading_v15"
    if not v3:
        v3 = one(cur, "select * from final_honest_reading_v14_runs order by run_id desc limit 1")
        if v3:
            source_layer = "final_honest_reading_v14"
    if not v3:
        v3 = one(cur, "select * from final_honest_reading_v13_runs order by run_id desc limit 1")
        if v3:
            source_layer = "final_honest_reading_v13"
    if not v3:
        v3 = one(cur, "select * from final_honest_reading_v12_runs order by run_id desc limit 1")
        if v3:
            source_layer = "final_honest_reading_v12"
    if not v3:
        v3 = one(cur, "select * from final_honest_reading_v11_runs order by run_id desc limit 1")
        if v3:
            source_layer = "final_honest_reading_v11"
    if not v3:
        v3 = one(cur, "select * from final_honest_reading_v10_runs order by run_id desc limit 1")
        if v3:
            source_layer = "final_honest_reading_v10"
    if not v3:
        v3 = one(cur, "select * from final_honest_reading_v9_runs order by run_id desc limit 1")
        if v3:
            source_layer = "final_honest_reading_v9"
    if not v3:
        v3 = one(cur, "select * from final_honest_reading_v8_runs order by run_id desc limit 1")
        if v3:
            source_layer = "final_honest_reading_v8"
    if not v3:
        v3 = one(cur, "select * from final_honest_reading_v7_runs order by run_id desc limit 1")
        if v3:
            source_layer = "final_honest_reading_v7"
    if not v3:
        v3 = one(cur, "select * from final_honest_reading_v6_runs order by run_id desc limit 1")
        if v3:
            source_layer = "final_honest_reading_v6"
    if not v3:
        v3 = one(cur, "select * from final_honest_reading_v5_runs order by run_id desc limit 1")
        if v3:
            source_layer = "final_honest_reading_v5"
    if not v3:
        v3 = one(cur, "select * from final_honest_reading_v4_runs order by run_id desc limit 1")
        if v3:
            source_layer = "final_honest_reading_v4"
    if not v3:
        v3 = one(cur, "select * from final_honest_reading_v3_runs order by run_id desc limit 1")
        if v3:
            source_layer = "final_honest_reading_v3"
    phrase_gt = one(cur, "select * from phrase_level_gt_gate_runs order by run_id desc limit 1")
    frontier = one(cur, "select * from semantic_actionable_frontier_runs order by run_id desc limit 1")
    ext_gate = one(cur, "select * from external_anchor_provenance_gate_runs order by run_id desc limit 1")
    vin = one(cur, "select * from vinvin_branch_reconciliation_runs order by run_id desc limit 1")
    contrast = one(cur, "select * from semantic_contrast_checkpoint_runs order by run_id desc limit 1")
    if not status_counts:
        status_counts = rows(cur, "select reading_status, count(*) as n from final_honest_reading_v16_books where run_id=(select max(run_id) from final_honest_reading_v16_books) group by reading_status")
    if not status_counts:
        status_counts = rows(cur, "select reading_status, count(*) as n from final_honest_reading_v15_books where run_id=(select max(run_id) from final_honest_reading_v15_books) group by reading_status")
    if not status_counts:
        status_counts = rows(cur, "select reading_status, count(*) as n from final_honest_reading_v14_books where run_id=(select max(run_id) from final_honest_reading_v14_books) group by reading_status")
    if not status_counts:
        status_counts = rows(cur, "select reading_status, count(*) as n from final_honest_reading_v13_books where run_id=(select max(run_id) from final_honest_reading_v13_books) group by reading_status")
    if not status_counts:
        status_counts = rows(cur, "select reading_status, count(*) as n from final_honest_reading_v12_books where run_id=(select max(run_id) from final_honest_reading_v12_books) group by reading_status")
    if not status_counts:
        status_counts = rows(cur, "select reading_status, count(*) as n from final_honest_reading_v11_books where run_id=(select max(run_id) from final_honest_reading_v11_books) group by reading_status")
    if not status_counts:
        status_counts = rows(cur, "select reading_status, count(*) as n from final_honest_reading_v10_books where run_id=(select max(run_id) from final_honest_reading_v10_books) group by reading_status")
    if not status_counts:
        status_counts = rows(cur, "select reading_status, count(*) as n from final_honest_reading_v9_books where run_id=(select max(run_id) from final_honest_reading_v9_books) group by reading_status")
    if not status_counts:
        status_counts = rows(cur, "select reading_status, count(*) as n from final_honest_reading_v8_books where run_id=(select max(run_id) from final_honest_reading_v8_books) group by reading_status")
    if not status_counts:
        status_counts = rows(cur, "select reading_status, count(*) as n from final_honest_reading_v7_books where run_id=(select max(run_id) from final_honest_reading_v7_books) group by reading_status")
    if not status_counts:
        status_counts = rows(cur, "select reading_status, count(*) as n from final_honest_reading_v6_books where run_id=(select max(run_id) from final_honest_reading_v6_books) group by reading_status")
    if not status_counts:
        status_counts = rows(cur, "select reading_status, count(*) as n from final_honest_reading_v5_books where run_id=(select max(run_id) from final_honest_reading_v5_books) group by reading_status")
    if not status_counts:
        status_counts = rows(cur, "select reading_status, count(*) as n from final_honest_reading_v4_books where run_id=(select max(run_id) from final_honest_reading_v4_books) group by reading_status")
    if not status_counts:
        status_counts = rows(cur, "select reading_status, count(*) as n from final_honest_reading_v3_books where run_id=(select max(run_id) from final_honest_reading_v3_books) group by reading_status")

    book_count = int(v3.get("book_count") or 0)
    tagged = int(v3.get("functional_tagged_book_count") or 0)
    tagged_pct = round(tagged / book_count * 100, 3) if book_count else 0.0
    operational = float(v3.get("operational_coverage_pct") or 0.0)
    semantic = float(v3.get("semantic_gloss_pct") or 0.0)
    phrase_count = int(phrase_gt.get("phrase_level_promotable_count") or 0)
    book_anchors = int(phrase_gt.get("book_decode_promotable_count") or 0) + int(ext_gate.get("book_promotable_count") or 0)
    actionable = int(frontier.get("actionable_count") or 0)
    decision = "FUNCTIONAL_PROGRESS_LEXICAL_TRANSLATION_UNSOLVED"

    payload = {
        "source_layer": source_layer,
        "v3": v3,
        "phrase_gt": phrase_gt,
        "frontier": frontier,
        "external_gate": ext_gate,
        "vinvin": vin,
        "contrast": contrast,
        "status_counts": status_counts,
    }
    cur.execute("""
        insert into translation_progress_status_runs
        (created_at, decision, operational_coverage_pct, functional_tagged_book_pct, semantic_gloss_pct,
         phrase_level_gt_count, book_decode_anchor_count, actionable_frontier_count, payload_json)
        values (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (now(), decision, operational, tagged_pct, semantic, phrase_count, book_anchors, actionable, j(payload)))
    run_id = cur.lastrowid
    con.commit()
    out = {"run_id": run_id, "decision": decision, "operational_coverage_pct": operational, "functional_tagged_book_pct": tagged_pct, "semantic_gloss_pct": semantic, "phrase_level_gt_count": phrase_count, "book_decode_anchor_count": book_anchors, "actionable_frontier_count": actionable}
    print(json.dumps(out, ensure_ascii=False))

    if args.discord:
        send("\n".join([
            f"[469][progress][run={run_id}] status consolidado da tradução",
            f"cobertura operacional={operational}% | livros com função auditável={tagged}/{book_count} ({tagged_pct}%) | gloss lexical dos livros={semantic}%",
            f"GT externo frase-level={phrase_count} | anchors promovíveis para decodificar livros={book_anchors} | frontier acionável={actionable}",
            "interpretação: o modelo mecânico/funcional está avançando; a tradução semântica lexical dos livros segue não resolvida porque ainda faltam anchors diretos confiáveis.",
            "próxima direção ativa: contrastes R20/VINVIN e estabilidade NAESE para aumentar função auditável sem alucinar inglês.",
        ]))


if __name__ == "__main__":
    main()
