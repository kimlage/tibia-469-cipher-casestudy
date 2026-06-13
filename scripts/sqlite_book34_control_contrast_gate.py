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
TARGET = "34"
CONTROLS = ("17", "68")
CORE = "LEAFIVNANI"
WINDOW = 18


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(x: Any) -> str:
    return json.dumps(x, ensure_ascii=False, sort_keys=True)


def send(message: str) -> None:
    if not os.path.exists(DISCORD_SCRIPT):
        return
    cmd = f"source ~/.env 2>/dev/null || true; python {DISCORD_SCRIPT} send --channel {DISCORD_CHANNEL} --message {json.dumps(message)}"
    subprocess.run(["/bin/zsh", "-lc", cmd], check=False)


def one(cur: sqlite3.Cursor, sql: str, params=()):
    r = cur.execute(sql, params).fetchone()
    return dict(r) if r else {}


def rows(cur: sqlite3.Cursor, sql: str, params=()):
    return [dict(r) for r in cur.execute(sql, params).fetchall()]


def lcp(a: str, b: str) -> int:
    n = 0
    for ca, cb in zip(a, b):
        if ca != cb:
            break
        n += 1
    return n


def lcsuffix(a: str, b: str) -> int:
    return lcp(a[::-1], b[::-1])


def create(cur: sqlite3.Cursor) -> None:
    cur.executescript(
        """
        create table if not exists book34_control_contrast_gate_runs(
          run_id integer primary key autoincrement,
          created_at text not null,
          core text not null,
          target_bookid text not null,
          controls_json text not null,
          decision text not null,
          left_context_min_match integer not null,
          right_context_min_match integer not null,
          promote_function integer not null,
          gloss_allowed integer not null,
          next_action text not null,
          payload_json text not null
        );
        create table if not exists book34_control_contrast_gate_items(
          run_id integer not null,
          bookid text not null,
          core_pos integer not null,
          left_context text not null,
          right_context text not null,
          reading_status text not null,
          functional_tag_count integer not null,
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

    latest = one(cur, "select max(run_id) as run_id from final_honest_reading_v16_books")
    wanted = (TARGET,) + CONTROLS
    qmarks = ",".join("?" for _ in wanted)
    books = rows(cur, f"select bookid, honest_text, reading_status, functional_tag_count, functional_tags_json from final_honest_reading_v16_books where run_id=? and bookid in ({qmarks})", (latest.get("run_id"), *wanted))
    by_book = {r["bookid"]: r for r in books}

    items = []
    for bookid in wanted:
        r = by_book.get(bookid, {})
        text = r.get("honest_text", "")
        pos = text.find(CORE)
        left = text[max(0, pos - WINDOW):pos] if pos >= 0 else ""
        right = text[pos + len(CORE):pos + len(CORE) + WINDOW] if pos >= 0 else ""
        items.append({"bookid": bookid, "core_pos": pos, "left_context": left, "right_context": right, "row": r})

    target_item = next(i for i in items if i["bookid"] == TARGET)
    left_matches = []
    right_matches = []
    for item in items:
        if item["bookid"] == TARGET:
            continue
        left_matches.append(lcsuffix(target_item["left_context"], item["left_context"]))
        right_matches.append(lcp(target_item["right_context"], item["right_context"]))
    left_min = min(left_matches) if left_matches else 0
    right_min = min(right_matches) if right_matches else 0

    promote = 1 if left_min >= 8 and right_min >= 8 else 0
    decision = "BOOK34_CONTROL_CONTEXT_COMPATIBLE_NO_GLOSS" if promote else "BOOK34_CONTROL_CONTEXT_FRAGMENTED_BLOCK_PROMOTION"
    next_action = "promote only a narrow functional context tag in next honest layer; no lexical gloss" if promote else "keep book34 blocked; recurrence is fragmentary and insufficient for function promotion"

    cur.execute(
        """
        insert into book34_control_contrast_gate_runs
        (created_at, core, target_bookid, controls_json, decision, left_context_min_match, right_context_min_match, promote_function, gloss_allowed, next_action, payload_json)
        values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (now(), CORE, TARGET, j(CONTROLS), decision, left_min, right_min, promote, 0, next_action, j({"items": items, "latest_reading": latest})),
    )
    run_id = cur.lastrowid
    for item in items:
        r = item["row"]
        cur.execute(
            """
            insert into book34_control_contrast_gate_items
            (run_id, bookid, core_pos, left_context, right_context, reading_status, functional_tag_count, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, item["bookid"], item["core_pos"], item["left_context"], item["right_context"], r.get("reading_status", ""), int(r.get("functional_tag_count") or 0), j(item)),
        )
    con.commit()
    out = {"run_id": run_id, "decision": decision, "left_context_min_match": left_min, "right_context_min_match": right_min, "promote_function": promote, "next_action": next_action, "contexts": [{"bookid": i["bookid"], "pos": i["core_pos"], "left": i["left_context"], "right": i["right_context"]} for i in items]}
    print(json.dumps(out, ensure_ascii=False))
    if args.discord:
        context_lines = [f"book {i['bookid']}: ...{i['left_context']}[{CORE}]{i['right_context']}..." for i in items]
        send("\n".join([
            f"[469][book34-control][run={run_id}] contraste 17/34/68 para LEAFIVNANI",
            f"decisão={decision} | match esquerdo mínimo={left_min} | match direito mínimo={right_min} | promove função={promote} | gloss=0",
            *context_lines,
            f"próxima ação: {next_action}",
        ]))


if __name__ == "__main__":
    main()
