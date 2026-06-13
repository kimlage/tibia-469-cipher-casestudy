#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import os
import sqlite3
import subprocess
from collections import Counter
from typing import Any

DB_DEFAULT = "./data/bonelord_operational.sqlite"
DISCORD_CHANNEL = "0"
DISCORD_SCRIPT = "~/.codex/skills/discord/scripts/discord_skill.py"


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(x: Any) -> str:
    return json.dumps(x, ensure_ascii=False, sort_keys=True)


def send(message: str) -> None:
    if not os.path.exists(DISCORD_SCRIPT):
        return
    cmd = f"source ~/.env 2>/dev/null || true; python {DISCORD_SCRIPT} send --channel {DISCORD_CHANNEL} --message {json.dumps(message)}"
    subprocess.run(["/bin/zsh", "-lc", cmd], check=False)


def rows(cur: sqlite3.Cursor, sql: str, params=()):
    return [dict(r) for r in cur.execute(sql, params).fetchall()]


def one(cur: sqlite3.Cursor, sql: str, params=()):
    r = cur.execute(sql, params).fetchone()
    return dict(r) if r else {}


def create(cur: sqlite3.Cursor) -> None:
    cur.executescript(
        """
        create table if not exists raw_row0_motif_function_gate_runs(
          run_id integer primary key autoincrement,
          created_at text not null,
          source_motif_run_id integer not null,
          reviewed_count integer not null,
          already_explained_count integer not null,
          new_frontier_count integer not null,
          decision text not null,
          next_action text not null,
          payload_json text not null
        );
        create table if not exists raw_row0_motif_function_gate_items(
          run_id integer not null,
          source_rank integer not null,
          motif text not null,
          books_json text not null,
          dominant_tag_id text,
          dominant_tag_share real not null,
          gate_status text not null,
          decision text not null,
          evidence_json text not null,
          primary key(run_id, source_rank)
        );
        """
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DB_DEFAULT)
    ap.add_argument("--discord", action="store_true")
    args = ap.parse_args()
    con = sqlite3.connect(args.db)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    create(cur)

    mrun = one(cur, "select max(run_id) as run_id from raw_row0_motif_scorer_items")
    latest_reading = one(cur, "select max(run_id) as run_id from final_honest_reading_v16_books")
    motifs = rows(cur, "select * from raw_row0_motif_scorer_items where run_id=? order by rank", (mrun.get("run_id"),))
    items = []
    already = 0
    new = 0
    for m in motifs:
        books = json.loads(m["books_json"] or "[]")
        tag_counter = Counter()
        if books:
            q = ",".join("?" for _ in books)
            readings = rows(cur, f"select bookid,functional_tags_json,functional_tag_count from final_honest_reading_v16_books where run_id=? and bookid in ({q})", (latest_reading.get("run_id"), *books))
        else:
            readings = []
        tagged_books = 0
        for r in readings:
            tags = json.loads(r.get("functional_tags_json") or "[]") if r.get("functional_tags_json") else []
            if tags:
                tagged_books += 1
            for tag in tags:
                tag_counter[tag.get("tag_id") or tag.get("label") or "UNKNOWN"] += 1
        dom, dom_count = (tag_counter.most_common(1)[0] if tag_counter else (None, 0))
        share = round(dom_count / max(1, len(books)), 3)
        motif_text = m["motif"]
        if share >= 0.6 or any(x in motif_text for x in ("C68", "VNCTIIN", "BENNA", "R20", "R02", "O23", "NAESE")):
            status = "ALREADY_EXPLAINED_BY_FUNCTIONAL_FAMILY"
            decision = "do not open new lane; use as support for existing structural class"
            already += 1
        elif int(m["known_dead_overlap"] or 0):
            status = "BLOCKED_DEAD_BOOK_OVERLAP"
            decision = "do not open; overlaps dead residual family"
            already += 1
        else:
            status = "NEW_RAW_STRUCTURAL_FRONTIER_NO_GLOSS"
            decision = "eligible for narrow structural contrast; no semantic gloss"
            new += 1
        items.append({"source_rank": m["rank"], "motif": motif_text, "books": books, "dominant_tag_id": dom, "dominant_tag_share": share, "gate_status": status, "decision": decision, "source": dict(m), "tag_counts": dict(tag_counter)})

    decision = "RAW_MOTIF_GATE_HAS_NEW_FRONTIER" if new else "RAW_MOTIF_GATE_ALL_EXPLAINED_OR_BLOCKED"
    next_action = "open narrow probes for new raw structural motifs" if new else "do not pursue raw motifs; seek new external/source evidence"
    cur.execute(
        """
        insert into raw_row0_motif_function_gate_runs
        (created_at, source_motif_run_id, reviewed_count, already_explained_count, new_frontier_count, decision, next_action, payload_json)
        values (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (now(), mrun.get("run_id") or 0, len(items), already, new, decision, next_action, j({"items": items})),
    )
    run_id = cur.lastrowid
    for item in items:
        cur.execute(
            """
            insert into raw_row0_motif_function_gate_items
            (run_id, source_rank, motif, books_json, dominant_tag_id, dominant_tag_share, gate_status, decision, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, item["source_rank"], item["motif"], j(item["books"]), item["dominant_tag_id"], item["dominant_tag_share"], item["gate_status"], item["decision"], j(item)),
        )
    con.commit()
    out = {"run_id": run_id, "decision": decision, "reviewed_count": len(items), "already_explained_count": already, "new_frontier_count": new, "top_new": [{"motif": i["motif"], "books": len(i["books"]), "dominant": i["dominant_tag_id"], "share": i["dominant_tag_share"]} for i in items if i["gate_status"] == "NEW_RAW_STRUCTURAL_FRONTIER_NO_GLOSS"][:10]}
    print(json.dumps(out, ensure_ascii=False))
    if args.discord:
        top_new = [i for i in items if i["gate_status"] == "NEW_RAW_STRUCTURAL_FRONTIER_NO_GLOSS"][:5]
        lines = [f"{k+1}. {i['motif']} | books={len(i['books'])} | dom={i['dominant_tag_id']} share={i['dominant_tag_share']}" for k, i in enumerate(top_new)] or ["nenhum motivo raw novo; top motivos já explicados por famílias existentes"]
        send("\n".join([
            f"[469][raw-motif-gate][run={run_id}] gate contra famílias funcionais existentes",
            f"revisados={len(items)} | já explicados/bloqueados={already} | novos={new} | gloss=0",
            *lines,
            f"decisão={decision}",
            f"próxima ação: {next_action}",
        ]))


if __name__ == "__main__":
    main()
