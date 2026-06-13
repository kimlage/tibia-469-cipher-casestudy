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
COMMON_SINGLETONS = set("AEFINTVLSBRCODGHUMYPWKQXZJ")


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


def create(cur: sqlite3.Cursor) -> None:
    cur.executescript(
        """
        create table if not exists final_residual_class_probe_runs(
          run_id integer primary key autoincrement,
          created_at text not null,
          target_books_json text not null,
          promotable_count integer not null,
          blocked_count integer not null,
          decision text not null,
          next_action text not null,
          payload_json text not null
        );
        create table if not exists final_residual_class_probe_items(
          run_id integer not null,
          bookid text not null,
          class_label text not null,
          rare_tokens_json text not null,
          best_lcs_bookid text,
          best_lcs_len integer not null,
          best_lcs_text text not null,
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

    latest_tokens = one(cur, "select max(run_id) as run_id from row0_variant_book_tokens")
    token_rows = rows(cur, "select bookid, tokens_json from row0_variant_book_tokens where run_id=?", (latest_tokens.get("run_id"),))
    tokens_by_book = {r["bookid"]: json.loads(r["tokens_json"]) for r in token_rows}
    all_books_by_token: dict[str, set[str]] = {}
    for bookid, toks in tokens_by_book.items():
        for tok in set(toks):
            all_books_by_token.setdefault(tok, set()).add(bookid)

    latest_reading = one(cur, "select max(run_id) as run_id from final_honest_reading_v16_books")
    reading_rows = rows(cur, "select bookid, honest_text, functional_tag_count from final_honest_reading_v16_books where run_id=?", (latest_reading.get("run_id"),))
    readings = {r["bookid"]: r for r in reading_rows}
    tagged = [r for r in reading_rows if int(r["functional_tag_count"] or 0) > 0]

    seg_latest = one(cur, "select max(run_id) as run_id from hard_residual_segmentation_probe_items")
    seg = {r["bookid"]: r for r in rows(cur, "select * from hard_residual_segmentation_probe_items where run_id=?", (seg_latest.get("run_id"),))}

    items = []
    promotable = 0
    for bookid in TARGET_BOOKS:
        toks = tokens_by_book.get(bookid, [])
        rare = []
        for tok in sorted(set(toks)):
            freq = len(all_books_by_token.get(tok, set()))
            if tok not in COMMON_SINGLETONS and (len(tok) > 1 or freq <= 3):
                rare.append({"token": tok, "book_count": freq, "books": sorted(all_books_by_token.get(tok, set()), key=lambda x: int(x) if x.isdigit() else 9999)})
        target_text = readings.get(bookid, {}).get("honest_text", "")
        best = {"length": 0, "bookid": None, "text": "", "target_start": 0, "other_start": 0}
        for other in tagged:
            hit = lcs(target_text, other["honest_text"])
            if hit["length"] > best["length"]:
                best = {**hit, "bookid": other["bookid"]}
        class_label = seg.get(bookid, {}).get("dominant_class") or "UNCLASSIFIED_RESIDUAL"
        decision = "BLOCKED_NO_SAFE_FUNCTIONAL_PROMOTION"
        next_action = "require a new exact anchor or a non-fragmented contrastive match that excludes known controls"
        if best["length"] >= 40 and bookid == "34":
            decision = "REVIEW_NONFRAGMENTED_LCS_CANDIDATE_NO_GLOSS"
            next_action = "open a narrow gate for the continuous LCS only; do not infer meaning"
        if decision.startswith("REVIEW"):
            promotable += 1
        items.append({
            "bookid": bookid,
            "class_label": class_label,
            "rare_tokens": rare,
            "best_lcs": best,
            "decision": decision,
            "next_action": next_action,
            "segmentation": seg.get(bookid, {}),
        })

    blocked = len(items) - promotable
    decision = "RESIDUAL_CLASS_PROBE_FOUND_NARROW_REVIEW_CANDIDATES" if promotable else "RESIDUAL_CLASS_PROBE_ALL_BLOCKED"
    next_action = "review candidates with narrow gates; no gloss promotion" if promotable else "shift to external exact anchors and semantic evidence search"
    cur.execute(
        """
        insert into final_residual_class_probe_runs
        (created_at, target_books_json, promotable_count, blocked_count, decision, next_action, payload_json)
        values (?, ?, ?, ?, ?, ?, ?)
        """,
        (now(), j(TARGET_BOOKS), promotable, blocked, decision, next_action, j({"latest_tokens": latest_tokens, "latest_reading": latest_reading, "items": items})),
    )
    run_id = cur.lastrowid
    for item in items:
        cur.execute(
            """
            insert into final_residual_class_probe_items
            (run_id, bookid, class_label, rare_tokens_json, best_lcs_bookid, best_lcs_len, best_lcs_text, decision, next_action, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, item["bookid"], item["class_label"], j(item["rare_tokens"]), item["best_lcs"].get("bookid"), item["best_lcs"].get("length") or 0, item["best_lcs"].get("text") or "", item["decision"], item["next_action"], j(item)),
        )
    con.commit()
    out = {"run_id": run_id, "decision": decision, "promotable_count": promotable, "blocked_count": blocked, "items": [{"bookid": i["bookid"], "class": i["class_label"], "best_lcs_bookid": i["best_lcs"].get("bookid"), "best_lcs_len": i["best_lcs"].get("length"), "decision": i["decision"]} for i in items]}
    print(json.dumps(out, ensure_ascii=False))
    if args.discord:
        item_lines = [f"book {i['bookid']}: classe={i['class_label']} | melhor LCS=book {i['best_lcs'].get('bookid')} len={i['best_lcs'].get('length')} | decisão={i['decision']}" for i in items]
        send("\n".join([
            f"[469][residual-class][run={run_id}] probe de classe dos resíduos finais",
            *item_lines,
            "leitura: nenhum gloss semântico foi liberado. Se houver LCS longo, ele abre apenas uma revisão estrutural estreita, não tradução em inglês.",
            f"próxima ação: {next_action}",
        ]))


if __name__ == "__main__":
    main()
