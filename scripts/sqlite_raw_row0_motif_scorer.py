#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import os
import sqlite3
import subprocess
from collections import defaultdict
from typing import Any

DB_DEFAULT = "./data/bonelord_operational.sqlite"
DISCORD_CHANNEL = "0"
DISCORD_SCRIPT = "~/.codex/skills/discord/scripts/discord_skill.py"
COMMON = set("AEFINTVLSBR")
MAX_ITEMS = 120
MIN_BOOKS = 3


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


def has_structure(tokens):
    rare = [t for t in tokens if len(t) > 1 or t not in COMMON]
    return len(rare) >= 1


def create(cur: sqlite3.Cursor) -> None:
    cur.executescript(
        """
        create table if not exists raw_row0_motif_scorer_runs(
          run_id integer primary key autoincrement,
          created_at text not null,
          source_row0_run_id integer not null,
          motif_count integer not null,
          selected_count integer not null,
          decision text not null,
          next_action text not null,
          payload_json text not null
        );
        create table if not exists raw_row0_motif_scorer_items(
          run_id integer not null,
          rank integer not null,
          motif text not null,
          n integer not null,
          hit_count integer not null,
          book_count integer not null,
          books_json text not null,
          rare_token_count integer not null,
          zero_context_overlap_count integer not null,
          known_dead_overlap integer not null,
          score real not null,
          review_status text not null,
          decision text not null,
          evidence_json text not null,
          primary key(run_id, rank)
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

    row0run = one(cur, "select max(run_id) as run_id from row0_variant_book_tokens")
    book_rows = rows(cur, "select bookid, tokens_json from row0_variant_book_tokens where run_id=?", (row0run.get("run_id"),))
    zero_run = one(cur, "select max(run_id) as run_id from zero_context_boundary_feature_gate_items")
    zero_books = set()
    for z in rows(cur, "select books_json from zero_context_boundary_feature_gate_items where run_id=? and feature_status like 'ACCEPT%'", (zero_run.get("run_id"),)):
        try:
            zero_books.update(json.loads(z["books_json"] or "[]"))
        except Exception:
            pass
    dead_books = {"4", "34", "49"}
    stats = {}
    examples = defaultdict(list)
    for b in book_rows:
        try:
            toks = json.loads(b["tokens_json"] or "[]")
        except Exception:
            toks = []
        for n in range(4, 11):
            for i in range(0, max(0, len(toks) - n + 1)):
                ng = tuple(toks[i:i+n])
                if not has_structure(ng):
                    continue
                motif = " ".join(ng)
                st = stats.setdefault(motif, {"n": n, "hits": 0, "books": set(), "rare": len([t for t in ng if len(t) > 1 or t not in COMMON])})
                st["hits"] += 1
                st["books"].add(b["bookid"])
                if len(examples[motif]) < 6:
                    examples[motif].append({"bookid": b["bookid"], "token_pos": i})
    motifs = []
    for motif, st in stats.items():
        bc = len(st["books"])
        if bc < MIN_BOOKS:
            continue
        dead_overlap = int(bool(st["books"] & dead_books))
        zero_overlap = len(st["books"] & zero_books)
        score = bc * 10 + st["hits"] + st["rare"] * 4 + zero_overlap * 3 - dead_overlap * 20
        if dead_overlap:
            status = "AUDIT_ONLY_DEAD_BOOK_OVERLAP"
            decision = "do not promote; overlaps blocked residual books"
        elif zero_overlap >= 2:
            status = "STRUCTURAL_REVIEW_ZERO_FEATURE_SUPPORTED_NO_GLOSS"
            decision = "candidate raw motif for boundary/structure review; no semantic gloss"
        else:
            status = "RAW_STRUCTURAL_REVIEW_NO_GLOSS"
            decision = "candidate raw motif for structural clustering; no semantic gloss"
        motifs.append({"motif": motif, "n": st["n"], "hit_count": st["hits"], "book_count": bc, "books": sorted(st["books"], key=lambda x: int(x) if x.isdigit() else 9999), "rare_token_count": st["rare"], "zero_context_overlap_count": zero_overlap, "known_dead_overlap": dead_overlap, "score": round(score, 3), "review_status": status, "decision": decision, "examples": examples[motif]})
    motifs.sort(key=lambda x: (x["review_status"] != "STRUCTURAL_REVIEW_ZERO_FEATURE_SUPPORTED_NO_GLOSS", -x["score"], x["motif"]))
    selected = motifs[:MAX_ITEMS]
    decision = "RAW_ROW0_MOTIFS_READY_FOR_STRUCTURAL_CONTRAST_NO_GLOSS" if selected else "NO_RAW_ROW0_MOTIFS_FOUND"
    next_action = "gate top motifs against existing functional families and holdouts; do not translate" if selected else "seek new source corpus"
    cur.execute(
        """
        insert into raw_row0_motif_scorer_runs
        (created_at, source_row0_run_id, motif_count, selected_count, decision, next_action, payload_json)
        values (?, ?, ?, ?, ?, ?, ?)
        """,
        (now(), row0run.get("run_id") or 0, len(motifs), len(selected), decision, next_action, j({"min_books": MIN_BOOKS, "max_items": MAX_ITEMS, "zero_books": sorted(zero_books), "dead_books": sorted(dead_books)})),
    )
    run_id = cur.lastrowid
    for rank, m in enumerate(selected, 1):
        cur.execute(
            """
            insert into raw_row0_motif_scorer_items
            (run_id, rank, motif, n, hit_count, book_count, books_json, rare_token_count, zero_context_overlap_count, known_dead_overlap, score, review_status, decision, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, rank, m["motif"], m["n"], m["hit_count"], m["book_count"], j(m["books"]), m["rare_token_count"], m["zero_context_overlap_count"], m["known_dead_overlap"], m["score"], m["review_status"], m["decision"], j(m)),
        )
    con.commit()
    out = {"run_id": run_id, "decision": decision, "motif_count": len(motifs), "selected_count": len(selected), "top": [{"motif": m["motif"], "books": m["book_count"], "score": m["score"], "status": m["review_status"]} for m in selected[:10]]}
    print(json.dumps(out, ensure_ascii=False))
    if args.discord:
        top_lines = [f"{i+1}. {m['motif']} | books={m['book_count']} | score={m['score']} | {m['review_status']}" for i, m in enumerate(selected[:5])]
        send("\n".join([
            f"[469][raw-row0-motif][run={run_id}] scorer raw row0 sem inglês circular",
            f"motivos={len(motifs)} | selecionados={len(selected)} | gloss=0",
            *top_lines,
            f"decisão={decision}",
            f"próxima ação: {next_action}",
        ]))


if __name__ == "__main__":
    main()
