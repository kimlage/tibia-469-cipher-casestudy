#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import os
import random
import sqlite3
import subprocess
from collections import Counter
from typing import Any

DB_DEFAULT = "./data/bonelord_operational.sqlite"
DISCORD_CHANNEL = "0"
DISCORD_SCRIPT = "~/.codex/skills/discord/scripts/discord_skill.py"
CTX = 6
SHUFFLES = 80
SEED = 469


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


def zero_contexts(book_digits):
    contexts = []
    for bookid, digits in book_digits:
        start = 0
        while True:
            pos = digits.find("00", start)
            if pos < 0:
                break
            left = digits[max(0, pos - CTX):pos]
            right = digits[pos+2:pos+2+CTX]
            contexts.append((left + "|" + right, bookid))
            start = pos + 1
    return contexts


def recurrent_count(contexts, min_books=2):
    books = {}
    for ctx, bookid in contexts:
        books.setdefault(ctx, set()).add(bookid)
    rec = {k: v for k, v in books.items() if len(v) >= min_books}
    high = {k: v for k, v in books.items() if len(v) >= 4}
    return len(rec), len(high), sorted([(k, len(v), sorted(v, key=lambda x: int(x) if x.isdigit() else 9999)) for k, v in high.items()], key=lambda x: x[1], reverse=True)


def create(cur: sqlite3.Cursor) -> None:
    cur.executescript(
        """
        create table if not exists zero_context_shuffle_control_runs(
          run_id integer primary key autoincrement,
          created_at text not null,
          context_size integer not null,
          shuffle_count integer not null,
          real_recurrent_count integer not null,
          real_high_count integer not null,
          shuffle_recurrent_avg real not null,
          shuffle_high_avg real not null,
          high_zscore real not null,
          decision text not null,
          next_action text not null,
          payload_json text not null
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

    paths = rows(cur, "select bookid, reconstructed_digits from row0_path_reconstruction_items where run_id=(select max(run_id) from row0_path_reconstruction_items) and selected=1 order by cast(bookid as int)")
    real_books = [(p["bookid"], p["reconstructed_digits"] or "") for p in paths]
    real_rec, real_high, real_top = recurrent_count(zero_contexts(real_books))
    rng = random.Random(SEED)
    sh_rec = []
    sh_high = []
    for _ in range(SHUFFLES):
        shuffled = []
        for bookid, digits in real_books:
            chars = list(digits)
            rng.shuffle(chars)
            shuffled.append((bookid, ''.join(chars)))
        r, h, _top = recurrent_count(zero_contexts(shuffled))
        sh_rec.append(r)
        sh_high.append(h)
    avg_rec = sum(sh_rec) / len(sh_rec)
    avg_high = sum(sh_high) / len(sh_high)
    var_high = sum((x - avg_high) ** 2 for x in sh_high) / max(1, len(sh_high) - 1)
    sd_high = var_high ** 0.5
    z = round((real_high - avg_high) / sd_high, 3) if sd_high else 999.0 if real_high > avg_high else 0.0
    if z >= 3 and real_high > avg_high:
        decision = "ZERO_CONTEXTS_PASS_SHUFFLE_CONTROL_STRUCTURAL_SIGNAL"
        next_action = "use zero-context features in raw-digit segmentation model; no gloss"
    else:
        decision = "ZERO_CONTEXTS_FAIL_OR_WEAK_SHUFFLE_CONTROL"
        next_action = "do not rely on zero-context recurrence as generative signal"
    cur.execute(
        """
        insert into zero_context_shuffle_control_runs
        (created_at, context_size, shuffle_count, real_recurrent_count, real_high_count, shuffle_recurrent_avg, shuffle_high_avg, high_zscore, decision, next_action, payload_json)
        values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (now(), CTX, SHUFFLES, real_rec, real_high, round(avg_rec,3), round(avg_high,3), z, decision, next_action, j({"seed": SEED, "real_top_high": real_top[:20], "shuffle_recurrent": sh_rec, "shuffle_high": sh_high})),
    )
    run_id = cur.lastrowid
    con.commit()
    out = {"run_id": run_id, "decision": decision, "real_recurrent_count": real_rec, "real_high_count": real_high, "shuffle_recurrent_avg": round(avg_rec,3), "shuffle_high_avg": round(avg_high,3), "high_zscore": z, "next_action": next_action}
    print(json.dumps(out, ensure_ascii=False))
    if args.discord:
        send("\n".join([
            f"[469][zero-shuffle-control][run={run_id}] controle negativo dos contextos 00",
            f"real recorrentes={real_rec}, high={real_high} | shuffle avg recorrentes={avg_rec:.3f}, high={avg_high:.3f} | z={z}",
            f"decisão={decision}",
            "interpretação: isso mede se 00 carrega estrutura real além de acaso; ainda não promove tradução.",
            f"próxima ação: {next_action}",
        ]))


if __name__ == "__main__":
    main()
