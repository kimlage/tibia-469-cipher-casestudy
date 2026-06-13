#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import math
import os
import sqlite3
import subprocess
from typing import Any

DB_DEFAULT = "./data/bonelord_operational.sqlite"
DISCORD_CHANNEL = "0"
DISCORD_SCRIPT = "~/.codex/skills/discord/scripts/discord_skill.py"
# Approximate Tibia/Windows-1252 printable alphabet. The exact charset.zip is gated, so this is audit-only.
ALPHABET = ''.join(chr(i) for i in range(32, 127)) + ''.join(chr(i) for i in range(160, 256) if i not in (0x8e, 0x9e))
COMMON = [" the ", " and ", "ing", "ion", "you", "be", "to", "of", "in", "is", "a "]
VOWELS = set("aeiouAEIOU ")


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


def to_base_alphabet(s: str, base: int) -> str:
    n = int(s)
    if n == 0:
        return ALPHABET[0]
    out = []
    while n:
        n, r = divmod(n, base)
        out.append(ALPHABET[r])
    return ''.join(reversed(out))


def text_score(txt: str) -> float:
    if not txt:
        return -999.0
    printable = sum(1 for c in txt if c in ALPHABET) / len(txt)
    ascii_ratio = sum(1 for c in txt if 32 <= ord(c) < 127) / len(txt)
    vowel_ratio = sum(1 for c in txt if c in VOWELS) / len(txt)
    space_ratio = txt.count(' ') / len(txt)
    common_hits = sum(txt.lower().count(w) for w in COMMON)
    weird = sum(1 for c in txt if ord(c) >= 160) / len(txt)
    # Natural text usually has some spaces/vowels and not too much high-ASCII noise.
    return round(printable * 25 + ascii_ratio * 25 + min(vowel_ratio, 0.45) * 40 + min(space_ratio, 0.22) * 30 + common_hits * 8 - weird * 25, 3)


def create(cur: sqlite3.Cursor) -> None:
    cur.executescript(
        """
        create table if not exists charset_base_sweep_audit_runs(
          run_id integer primary key autoincrement,
          created_at text not null,
          alphabet_desc text not null,
          item_count integer not null,
          tested_base_min integer not null,
          tested_base_max integer not null,
          strong_candidate_count integer not null,
          decision text not null,
          next_action text not null,
          payload_json text not null
        );
        create table if not exists charset_base_sweep_audit_items(
          run_id integer not null,
          item_type text not null,
          item_id text not null,
          best_base integer not null,
          best_score real not null,
          decoded_preview text not null,
          candidate_status text not null,
          evidence_json text not null,
          primary key(run_id, item_type, item_id)
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

    items = []
    for b in rows(cur, "select distinct bookid as item_id, digits from sheet__books order by cast(bookid as int)"):
        items.append({"item_type": "book", "item_id": b["item_id"], "digits": b["digits"]})
    fr = rows(cur, "select max(run_id) as run_id from npc_sequence_frontier")[0]["run_id"]
    for s in rows(cur, "select sequence_id as item_id, digits from npc_sequence_frontier where run_id=? and digits is not null", (fr,)):
        items.append({"item_type": "external", "item_id": s["item_id"], "digits": ''.join(ch for ch in s["digits"] if ch.isdigit())})

    results = []
    strong = 0
    for item in items:
        best = {"base": 0, "score": -999.0, "text": ""}
        digits = item["digits"] or ""
        if not digits:
            continue
        # Bases below 32 create very long low-information output; start near common charsets.
        for base in range(64, min(len(ALPHABET), 256) + 1):
            try:
                txt = to_base_alphabet(digits, base)
            except Exception:
                continue
            score = text_score(txt)
            if score > best["score"]:
                best = {"base": base, "score": score, "text": txt}
        status = "CHARSET_BASE_SWEEP_STRONG_CANDIDATE_AUDIT_ONLY" if best["score"] >= 72 and " " in best["text"] and len(best["text"]) >= 8 else "CHARSET_BASE_SWEEP_NO_STRONG_TEXT"
        if status.startswith("CHARSET_BASE_SWEEP_STRONG"):
            strong += 1
        results.append({"item_type": item["item_type"], "item_id": item["item_id"], "best_base": best["base"], "best_score": best["score"], "decoded_preview": best["text"][:180], "candidate_status": status})
    decision = "CHARSET_BASE_SWEEP_HAS_AUDIT_CANDIDATES" if strong else "CHARSET_BASE_SWEEP_NO_BOOK_TRANSLATION_SIGNAL"
    next_action = "inspect strong candidates only; no promotion" if strong else "do not pursue generic base/charset conversion for books"
    cur.execute("insert into charset_base_sweep_audit_runs(created_at,alphabet_desc,item_count,tested_base_min,tested_base_max,strong_candidate_count,decision,next_action,payload_json) values (?,?,?,?,?,?,?,?,?)", (now(), "approx cp1252 printable alphabet; exact OTLand charset unavailable", len(items), 64, min(len(ALPHABET),256), strong, decision, next_action, j({"alphabet_len": len(ALPHABET), "items": results})))
    run_id = cur.lastrowid
    for r in results:
        cur.execute("insert into charset_base_sweep_audit_items(run_id,item_type,item_id,best_base,best_score,decoded_preview,candidate_status,evidence_json) values (?,?,?,?,?,?,?,?)", (run_id,r['item_type'],r['item_id'],r['best_base'],r['best_score'],r['decoded_preview'],r['candidate_status'],j(r)))
    con.commit()
    print(json.dumps({"run_id":run_id,"decision":decision,"item_count":len(items),"strong_candidate_count":strong,"top":[{"id":r['item_id'],"type":r['item_type'],"base":r['best_base'],"score":r['best_score'],"preview":r['decoded_preview'][:80]} for r in sorted(results,key=lambda x:x['best_score'],reverse=True)[:10]]},ensure_ascii=False))
    if args.discord:
        top=sorted(results,key=lambda x:x['best_score'],reverse=True)[:5]
        lines=[f"{r['item_type']}:{r['item_id']} base={r['best_base']} score={r['best_score']} preview={r['decoded_preview'][:60]}" for r in top]
        send('\n'.join([f"[469][charset-base-sweep][run={run_id}] varredura base/charset estilo Tibia",f"itens={len(items)} | candidatos fortes={strong} | gloss=0",*lines,f"decisão={decision}",f"próxima ação: {next_action}"]))
if __name__=='__main__': main()
