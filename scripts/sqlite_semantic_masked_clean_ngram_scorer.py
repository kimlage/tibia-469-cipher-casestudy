#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import os
import re
import sqlite3
import subprocess
from collections import defaultdict
from typing import Any

DB_DEFAULT = "./data/bonelord_operational.sqlite"
DISCORD_CHANNEL = "0"
DISCORD_SCRIPT = "~/.codex/skills/discord/scripts/discord_skill.py"
STOP = {"a","i","in","of","to","be","so","no","we","or","as","is","if","it","the","and","you've","you","me","my","lo","eye","fine","fair","far","yet","into","with","do"}
TOKEN_RE = re.compile(r"<[^>]+>|[A-Za-z']+|↵")
MIN_BOOKS = 3
MAX_ITEMS = 100


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


def toks(text: str):
    return [t.lower() for t in TOKEN_RE.findall(text or "")]


def clean_ngram(parts):
    if any(p.startswith("<") for p in parts):
        return False
    content = [p for p in parts if p not in STOP and p != "↵"]
    if not content:
        return False
    if len(content) == 1 and len(content[0]) <= 3:
        return False
    return True


def create(cur: sqlite3.Cursor) -> None:
    cur.executescript(
        """
        create table if not exists semantic_masked_clean_ngram_scorer_runs(
          run_id integer primary key autoincrement,
          created_at text not null,
          source_masked_run_id integer not null,
          candidate_count integer not null,
          review_candidate_count integer not null,
          decision text not null,
          next_action text not null,
          payload_json text not null
        );
        create table if not exists semantic_masked_clean_ngram_scorer_items(
          run_id integer not null,
          rank integer not null,
          phrase text not null,
          n integer not null,
          hit_count integer not null,
          book_count integer not null,
          books_json text not null,
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

    source = one(cur, "select max(run_id) as run_id from semantic_masked_shadow_v2_books")
    books = rows(cur, "select bookid, masked_text from semantic_masked_shadow_v2_books where run_id=? order by cast(bookid as int)", (source.get("run_id"),))
    stats = {}
    examples = defaultdict(list)
    for b in books:
        tt = toks(b["masked_text"])
        for n in range(2, 7):
            for i in range(0, max(0, len(tt) - n + 1)):
                ng = tuple(tt[i:i+n])
                if not clean_ngram(ng):
                    continue
                phrase = " ".join(ng)
                st = stats.setdefault(phrase, {"n": n, "hits": 0, "books": set()})
                st["hits"] += 1
                st["books"].add(b["bookid"])
                if len(examples[phrase]) < 5:
                    examples[phrase].append({"bookid": b["bookid"], "token_pos": i})
    candidates = []
    for phrase, st in stats.items():
        bc = len(st["books"])
        if bc < MIN_BOOKS:
            continue
        rare_content = [p for p in phrase.split() if p not in STOP]
        weird_penalty = sum(1 for p in rare_content if p in {"belittle","blimey","unfeasible","intenable","biface","frutify"}) * 10
        score = bc * 10 + st["hits"] + len(rare_content) * 2 - weird_penalty
        if score <= 0:
            continue
        if any(w in phrase for w in ("belittle", "infinite", "fasten", "infinity")):
            status = "REJECT_FORMULA_OR_MASK_LEAK"
            decision = "do not review; should be covered by formula masks"
        elif weird_penalty:
            status = "LOW_CONFIDENCE_DISPLAY_DRIFT"
            decision = "keep as display drift unless independently supported"
        else:
            status = "REVIEW_CLEAN_RECURRENT_PHRASE_NO_GLOSS"
            decision = "candidate for contrastive review only; no lexical promotion"
        candidates.append({"phrase": phrase, "n": st["n"], "hit_count": st["hits"], "book_count": bc, "books": sorted(st["books"], key=lambda x: int(x) if x.isdigit() else 9999), "score": round(score, 3), "review_status": status, "decision": decision, "examples": examples[phrase]})
    candidates.sort(key=lambda x: (x["review_status"] != "REVIEW_CLEAN_RECURRENT_PHRASE_NO_GLOSS", -x["score"], x["phrase"]))
    selected = candidates[:MAX_ITEMS]
    review_count = sum(1 for c in selected if c["review_status"] == "REVIEW_CLEAN_RECURRENT_PHRASE_NO_GLOSS")
    decision = "CLEAN_RECURRENT_PHRASES_READY_FOR_CONTRASTIVE_REVIEW_NO_GLOSS" if review_count else "NO_CLEAN_SEMANTIC_CANDIDATES_AFTER_MASKING"
    next_action = "run contrastive source/raw alignment on top clean recurrent phrases; no promotion" if review_count else "seek new external anchors"
    cur.execute(
        """
        insert into semantic_masked_clean_ngram_scorer_runs
        (created_at, source_masked_run_id, candidate_count, review_candidate_count, decision, next_action, payload_json)
        values (?, ?, ?, ?, ?, ?, ?)
        """,
        (now(), source.get("run_id") or 0, len(candidates), review_count, decision, next_action, j({"min_books": MIN_BOOKS, "max_items": MAX_ITEMS})),
    )
    run_id = cur.lastrowid
    for rank, c in enumerate(selected, 1):
        cur.execute(
            """
            insert into semantic_masked_clean_ngram_scorer_items
            (run_id, rank, phrase, n, hit_count, book_count, books_json, score, review_status, decision, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, rank, c["phrase"], c["n"], c["hit_count"], c["book_count"], j(c["books"]), c["score"], c["review_status"], c["decision"], j(c)),
        )
    con.commit()
    out = {"run_id": run_id, "decision": decision, "candidate_count": len(candidates), "review_candidate_count": review_count, "top": [{"phrase": c["phrase"], "books": c["book_count"], "score": c["score"], "status": c["review_status"]} for c in selected[:10]]}
    print(json.dumps(out, ensure_ascii=False))
    if args.discord:
        top_lines = [f"{i+1}. {c['phrase']} | books={c['book_count']} | score={c['score']} | {c['review_status']}" for i, c in enumerate(selected[:5])]
        send("\n".join([
            f"[469][clean-ngram-scorer][run={run_id}] candidatos limpos após máscaras v2",
            f"candidatos={len(candidates)} | candidatos para revisão={review_count} | gloss=0",
            *top_lines,
            f"decisão={decision}",
            f"próxima ação: {next_action}",
        ]))


if __name__ == "__main__":
    main()
