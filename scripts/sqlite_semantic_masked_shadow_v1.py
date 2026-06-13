#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import os
import re
import sqlite3
import subprocess
from typing import Any

DB_DEFAULT = "./data/bonelord_operational.sqlite"
DISCORD_CHANNEL = "0"
DISCORD_SCRIPT = "~/.codex/skills/discord/scripts/discord_skill.py"

MASK_RULES = [
    (re.compile(r"if belittle men(?: a i infinite(?: fasten infinity last <UNK:TTNVVN>)?)?", re.I), "<FORMULA:BENNA_DISPLAY_DRIFT>"),
    (re.compile(r"i infinite fasten infinity last <UNK:TTNVVN>", re.I), "<FORMULA:INFINITE_FASTEN_TTNVVN>"),
    (re.compile(r"fasten infinity last <UNK:TTNVVN>", re.I), "<FORMULA:FASTEN_TTNVVN>"),
    (re.compile(r"infinity last <UNK:TTNVVN>", re.I), "<FORMULA:TTNVVN_TAIL>"),
    (re.compile(r"<SUSPECT:VTLRNEFIE> fair fair", re.I), "<SUSPECT:VTLRNEFIE_FAIR_FAIR>"),
]
SUSPECT_PATTERNS = ["belittle", "infinite fasten", "infinity last", "<UNK:TTNVVN>", "<SUSPECT:VTLRNEFIE> fair fair"]


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


def apply_masks(text: str):
    out = text or ""
    hits = []
    for pat, repl in MASK_RULES:
        matches = list(pat.finditer(out))
        if matches:
            hits.append({"pattern": pat.pattern, "replacement": repl, "count": len(matches)})
            out = pat.sub(repl, out)
    remaining = {p: len(re.findall(re.escape(p), out, flags=re.I)) for p in SUSPECT_PATTERNS}
    return out, hits, remaining


def create(cur: sqlite3.Cursor) -> None:
    cur.executescript(
        """
        create table if not exists semantic_masked_shadow_v1_runs(
          run_id integer primary key autoincrement,
          created_at text not null,
          source_best_shadow_run_id integer not null,
          book_count integer not null,
          books_changed integer not null,
          mask_hit_count integer not null,
          remaining_suspect_hit_count integer not null,
          semantic_gloss_allowed integer not null,
          decision text not null,
          next_action text not null,
          payload_json text not null
        );
        create table if not exists semantic_masked_shadow_v1_books(
          run_id integer not null,
          bookid text not null,
          source_text text not null,
          masked_text text not null,
          mask_hits_json text not null,
          remaining_suspects_json text not null,
          changed integer not null,
          semantic_gloss_allowed integer not null,
          evidence_json text not null,
          primary key(run_id, bookid)
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

    source = one(cur, "select max(run_id) as run_id from best_shadow_book_translations")
    books = rows(cur, "select bookid,best_shadow_text from best_shadow_book_translations where run_id=? order by cast(bookid as int)", (source.get("run_id"),))
    rows_out = []
    changed = 0
    mask_hits_total = 0
    remaining_total = 0
    for b in books:
        masked, hits, remaining = apply_masks(b.get("best_shadow_text") or "")
        ch = int(masked != (b.get("best_shadow_text") or ""))
        changed += ch
        mask_hits_total += sum(h["count"] for h in hits)
        remaining_total += sum(remaining.values())
        rows_out.append({"bookid": b["bookid"], "source_text": b.get("best_shadow_text") or "", "masked_text": masked, "hits": hits, "remaining": remaining, "changed": ch})

    decision = "SEMANTIC_SHADOW_MASKED_FORMULA_DRIFT_NO_GLOSS"
    next_action = "use masked shadow for human review and future scoring; keep semantic_gloss_pct at 0 until source-attested meanings exist"
    cur.execute(
        """
        insert into semantic_masked_shadow_v1_runs
        (created_at, source_best_shadow_run_id, book_count, books_changed, mask_hit_count, remaining_suspect_hit_count, semantic_gloss_allowed, decision, next_action, payload_json)
        values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (now(), source.get("run_id") or 0, len(rows_out), changed, mask_hits_total, remaining_total, 0, decision, next_action, j({"rules": [r[1] for r in MASK_RULES]})),
    )
    run_id = cur.lastrowid
    for r in rows_out:
        cur.execute(
            """
            insert into semantic_masked_shadow_v1_books
            (run_id, bookid, source_text, masked_text, mask_hits_json, remaining_suspects_json, changed, semantic_gloss_allowed, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, r["bookid"], r["source_text"], r["masked_text"], j(r["hits"]), j(r["remaining"]), r["changed"], 0, j(r)),
        )
    con.commit()
    out = {"run_id": run_id, "decision": decision, "book_count": len(rows_out), "books_changed": changed, "mask_hit_count": mask_hits_total, "remaining_suspect_hit_count": remaining_total, "semantic_gloss_allowed": 0}
    print(json.dumps(out, ensure_ascii=False))
    if args.discord:
        send("\n".join([
            f"[469][semantic-masked-shadow-v1][run={run_id}] camada semântica mascarada criada",
            f"livros={len(rows_out)} | livros alterados={changed} | máscaras aplicadas={mask_hits_total} | suspeitos restantes={remaining_total} | gloss_allowed=0",
            "interpretação: removemos falso inglês recorrente substituindo por <FORMULA:...>/<SUSPECT:...>. Isso é avanço de confiabilidade, não tradução final.",
            f"próxima ação: {next_action}",
        ]))


if __name__ == "__main__":
    main()
