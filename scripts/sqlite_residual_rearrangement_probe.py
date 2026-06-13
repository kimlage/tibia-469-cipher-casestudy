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
TARGET_BOOKS = ("4", "34", "49")
MIN_REVIEW_LEN = 24


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


def lcs(a: str, b: str):
    prev = [0] * (len(b) + 1)
    best = (0, 0, 0)
    for i, ca in enumerate(a, 1):
        cur = [0] * (len(b) + 1)
        for k, cb in enumerate(b, 1):
            if ca == cb:
                cur[k] = prev[k - 1] + 1
                if cur[k] > best[0]:
                    best = (cur[k], i - cur[k], k - cur[k])
        prev = cur
    n, ia, ib = best
    return {"length": n, "target_start": ia, "other_start": ib, "text": a[ia:ia+n]}


def transforms(text: str):
    yield "original", text, {"kind": "original"}
    yield "reverse", text[::-1], {"kind": "reverse"}
    n = len(text)
    mid = n // 2
    yield "half_swap_floor", text[mid:] + text[:mid], {"kind": "half_swap", "split": mid}
    if n % 2:
        yield "half_swap_ceil", text[mid+1:] + text[:mid+1], {"kind": "half_swap", "split": mid + 1}
    # Rotation tests the public hypothesis that some books may be halves switched or otherwise cyclically shifted.
    for k in range(1, n):
        yield f"rotate_{k}", text[k:] + text[:k], {"kind": "rotate", "shift": k}


def create(cur: sqlite3.Cursor) -> None:
    cur.executescript(
        """
        create table if not exists residual_rearrangement_probe_runs(
          run_id integer primary key autoincrement,
          created_at text not null,
          target_books_json text not null,
          min_review_len integer not null,
          review_candidate_count integer not null,
          decision text not null,
          next_action text not null,
          payload_json text not null
        );
        create table if not exists residual_rearrangement_probe_items(
          run_id integer not null,
          bookid text not null,
          transform_name text not null,
          matched_bookid text,
          match_len integer not null,
          match_text text not null,
          transform_json text not null,
          decision text not null,
          next_action text not null,
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
    all_rows = rows(cur, "select bookid, honest_text, functional_tag_count, reading_status from final_honest_reading_v16_books where run_id=?", (latest.get("run_id"),))
    by_book = {r["bookid"]: r for r in all_rows}
    tagged = [r for r in all_rows if int(r["functional_tag_count"] or 0) > 0]

    items = []
    review_count = 0
    for bookid in TARGET_BOOKS:
        text = by_book[bookid]["honest_text"]
        best = {"length": -1, "transform_name": "", "matched_bookid": None, "match_text": "", "transform_meta": {}, "target_start": 0, "other_start": 0}
        for name, transformed, meta in transforms(text):
            for other in tagged:
                hit = lcs(transformed, other["honest_text"])
                if hit["length"] > best["length"]:
                    best = {"length": hit["length"], "transform_name": name, "matched_bookid": other["bookid"], "match_text": hit["text"], "transform_meta": meta, "target_start": hit["target_start"], "other_start": hit["other_start"]}
        decision = "NO_REARRANGEMENT_ESCAPE"
        next_action = "keep blocked; rearrangement does not produce a long non-fragmented match"
        if best["length"] >= MIN_REVIEW_LEN:
            decision = "REVIEW_REARRANGEMENT_CANDIDATE_NO_GLOSS"
            next_action = "open a narrow contrast gate for this rearranged continuous match; no semantic gloss"
            review_count += 1
        items.append({"bookid": bookid, **best, "decision": decision, "next_action": next_action})

    decision = "REARRANGEMENT_CANDIDATES_FOUND_NO_GLOSS" if review_count else "REARRANGEMENT_ROUTE_BLOCKED_FOR_ALL_RESIDUALS"
    next_action = "gate each rearrangement candidate with controls" if review_count else "stop structural promotion attempts for these residues; require new external exact anchor or new corpus"
    cur.execute(
        """
        insert into residual_rearrangement_probe_runs
        (created_at, target_books_json, min_review_len, review_candidate_count, decision, next_action, payload_json)
        values (?, ?, ?, ?, ?, ?, ?)
        """,
        (now(), j(TARGET_BOOKS), MIN_REVIEW_LEN, review_count, decision, next_action, j({"latest_reading": latest, "items": items, "external_method_lead": "public s2ward/469 README notes rearranged books/halves switched/single digit changed; tested as audit-only hypothesis"})),
    )
    run_id = cur.lastrowid
    for item in items:
        cur.execute(
            """
            insert into residual_rearrangement_probe_items
            (run_id, bookid, transform_name, matched_bookid, match_len, match_text, transform_json, decision, next_action, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, item["bookid"], item["transform_name"], item["matched_bookid"], item["length"], item["match_text"], j(item["transform_meta"]), item["decision"], item["next_action"], j(item)),
        )
    con.commit()
    out = {"run_id": run_id, "decision": decision, "review_candidate_count": review_count, "items": [{"bookid": i["bookid"], "transform": i["transform_name"], "matched_bookid": i["matched_bookid"], "match_len": i["length"], "decision": i["decision"]} for i in items]}
    print(json.dumps(out, ensure_ascii=False))
    if args.discord:
        item_lines = [f"book {i['bookid']}: transform={i['transform_name']} -> book {i['matched_bookid']} | match_len={i['length']} | decisão={i['decision']}" for i in items]
        send("\n".join([
            f"[469][rearrangement-probe][run={run_id}] teste de rotação/metades nos resíduos finais",
            "hipótese testada: alguns livros podem estar rotacionados, com metades trocadas ou embaralhados; isso veio de fonte pública como pista metodológica, não como tradução.",
            *item_lines,
            f"resultado={decision}",
            f"próxima ação: {next_action}",
        ]))


if __name__ == "__main__":
    main()
