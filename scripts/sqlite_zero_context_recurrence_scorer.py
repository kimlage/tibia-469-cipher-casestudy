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
CTX = 6
MIN_BOOKS = 2


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


def find_all(text: str, needle: str):
    start = 0
    while True:
        pos = text.find(needle, start)
        if pos < 0:
            break
        yield pos
        start = pos + 1


def create(cur: sqlite3.Cursor) -> None:
    cur.executescript(
        """
        create table if not exists zero_context_recurrence_scorer_runs(
          run_id integer primary key autoincrement,
          created_at text not null,
          context_size integer not null,
          total_zero_count integer not null,
          recurrent_context_count integer not null,
          high_value_context_count integer not null,
          decision text not null,
          next_action text not null,
          payload_json text not null
        );
        create table if not exists zero_context_recurrence_scorer_items(
          run_id integer not null,
          context_key text not null,
          left_digits text not null,
          right_digits text not null,
          occurrence_count integer not null,
          book_count integer not null,
          books_json text not null,
          anchor_overlap_json text not null,
          decision text not null,
          evidence_json text not null,
          primary key(run_id, context_key)
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

    latest_paths = one(cur, "select max(run_id) as run_id from row0_path_reconstruction_items")
    paths = rows(cur, "select bookid, reconstructed_digits, decoded_text from row0_path_reconstruction_items where run_id=? and selected=1", (latest_paths.get("run_id"),))
    latest_anchor = one(cur, "select max(run_id) as run_id from npc_wordcode_anchors")
    anchors = rows(cur, "select anchor_id, digits, strength from npc_wordcode_anchors where run_id=?", (latest_anchor.get("run_id"),))

    groups = {}
    total_zero = 0
    for p in paths:
        digits = p["reconstructed_digits"] or ""
        for pos in find_all(digits, "00"):
            total_zero += 1
            left = digits[max(0, pos - CTX):pos]
            right = digits[pos + 2:pos + 2 + CTX]
            key = f"{left}|{right}"
            g = groups.setdefault(key, {"left": left, "right": right, "occurrences": [], "books": set()})
            g["books"].add(p["bookid"])
            g["occurrences"].append({"bookid": p["bookid"], "pos": pos, "decoded_context": (p["decoded_text"] or "")[max(0, pos//2 - 8):pos//2 + 16]})

    items = []
    recurrent = 0
    high_value = 0
    for key, g in groups.items():
        book_count = len(g["books"])
        if book_count < MIN_BOOKS:
            continue
        recurrent += 1
        ctx_string = g["left"] + "00" + g["right"]
        overlaps = [a for a in anchors if a["digits"] in ctx_string]
        decision = "RECURRENT_ZERO_CONTEXT_AUDIT_ONLY"
        if book_count >= 3 and overlaps:
            decision = "HIGH_VALUE_ZERO_CONTEXT_WITH_ANCHOR_OVERLAP_NO_GLOSS"
            high_value += 1
        elif book_count >= 4:
            decision = "HIGH_VALUE_ZERO_CONTEXT_NO_ANCHOR_NO_GLOSS"
            high_value += 1
        items.append({"key": key, "left": g["left"], "right": g["right"], "occurrence_count": len(g["occurrences"]), "book_count": book_count, "books": sorted(g["books"], key=lambda x: int(x) if x.isdigit() else 9999), "anchor_overlap": overlaps, "decision": decision, "occurrences": g["occurrences"]})
    items.sort(key=lambda x: (x["book_count"], x["occurrence_count"], len(x["anchor_overlap"])), reverse=True)

    decision = "RECURRENT_ZERO_CONTEXTS_FOUND_FOR_BOUNDARY_MODEL" if high_value else "ZERO_CONTEXT_DIFFUSE_NO_BOUNDARY_PROMOTION"
    next_action = "use recurrent 00 contexts as structural boundary features in segmentation scorer; no gloss" if high_value else "keep 00 as explicit unknown/null without segmentation promotion"
    cur.execute(
        """
        insert into zero_context_recurrence_scorer_runs
        (created_at, context_size, total_zero_count, recurrent_context_count, high_value_context_count, decision, next_action, payload_json)
        values (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (now(), CTX, total_zero, recurrent, high_value, decision, next_action, j({"latest_paths": latest_paths, "latest_anchor": latest_anchor, "top_items": items[:50]})),
    )
    run_id = cur.lastrowid
    for item in items[:200]:
        cur.execute(
            """
            insert into zero_context_recurrence_scorer_items
            (run_id, context_key, left_digits, right_digits, occurrence_count, book_count, books_json, anchor_overlap_json, decision, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, item["key"], item["left"], item["right"], item["occurrence_count"], item["book_count"], j(item["books"]), j(item["anchor_overlap"]), item["decision"], j(item)),
        )
    con.commit()
    out = {"run_id": run_id, "decision": decision, "total_zero_count": total_zero, "recurrent_context_count": recurrent, "high_value_context_count": high_value, "top": [{"left": i["left"], "right": i["right"], "book_count": i["book_count"], "books": i["books"], "decision": i["decision"]} for i in items[:5]]}
    print(json.dumps(out, ensure_ascii=False))
    if args.discord:
        top_lines = [f"00ctx {i['left']}|{i['right']} books={','.join(i['books'][:8])} nbooks={i['book_count']} decisão={i['decision']}" for i in items[:3]]
        send("\n".join([
            f"[469][zero-context][run={run_id}] recorrência local do 00",
            f"zeros={total_zero} | contextos recorrentes={recurrent} | high-value={high_value}",
            *top_lines,
            f"decisão={decision}",
            f"próxima ação: {next_action}",
        ]))


if __name__ == "__main__":
    main()
