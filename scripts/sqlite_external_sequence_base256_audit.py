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
PRINTABLE = set(range(32, 127)) | {10, 13, 9}


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


def int_to_bytes_dec(s: str) -> bytes:
    n = int(s)
    if n == 0:
        return b"\x00"
    out = bytearray()
    while n:
        n, r = divmod(n, 256)
        out.append(r)
    return bytes(reversed(out))


def printable_score(bs: bytes):
    return sum(1 for b in bs if b in PRINTABLE) / max(1, len(bs))


def create(cur: sqlite3.Cursor) -> None:
    cur.executescript(
        """
        create table if not exists external_sequence_base256_audit_runs(
          run_id integer primary key autoincrement,
          created_at text not null,
          source_frontier_run_id integer not null,
          sequence_count integer not null,
          printable_candidate_count integer not null,
          decision text not null,
          next_action text not null,
          payload_json text not null
        );
        create table if not exists external_sequence_base256_audit_items(
          run_id integer not null,
          sequence_id text not null,
          refname text,
          sequence_kind text not null,
          digit_len integer not null,
          byte_len integer not null,
          printable_score real not null,
          decoded_preview text not null,
          candidate_status text not null,
          evidence_json text not null,
          primary key(run_id, sequence_id)
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
    frun = rows(cur, "select max(run_id) as run_id from npc_sequence_frontier")[0]["run_id"]
    seqs = rows(cur, "select sequence_id, refname, digits, sequence_kind, status, reason, payload_json from npc_sequence_frontier where run_id=? and digits is not null order by sequence_id", (frun,))
    out = []
    cand = 0
    for s in seqs:
        digits = ''.join(ch for ch in (s.get("digits") or "") if ch.isdigit())
        try:
            bs = int_to_bytes_dec(digits)
            dec = bs.decode("cp1252", errors="replace")
            score = round(printable_score(bs), 3)
            wordish = sum(1 for ch in dec if ch.lower() in "aeiou !?.") / max(1, len(dec))
            if score >= 0.85 and wordish >= 0.2:
                status = "BASE256_EXTERNAL_PRINTABLE_CANDIDATE_AUDIT_ONLY"
                cand += 1
            else:
                status = "BASE256_NOT_READABLE"
        except Exception as e:
            bs = b""; dec = str(e); score = 0.0; status = "BASE256_DECODE_ERROR"
        out.append({"sequence_id": s["sequence_id"], "refname": s.get("refname"), "sequence_kind": s["sequence_kind"], "digit_len": len(digits), "byte_len": len(bs), "printable_score": score, "decoded_preview": dec[:160], "candidate_status": status, "source": dict(s)})
    decision = "EXTERNAL_BASE256_CANDIDATES_FOUND_AUDIT_ONLY" if cand else "EXTERNAL_BASE256_NO_READABLE_CANDIDATES"
    next_action = "audit printable external candidates against provenance" if cand else "do not pursue base256 route unless new Vogler/Tibia charset evidence appears"
    cur.execute("insert into external_sequence_base256_audit_runs(created_at,source_frontier_run_id,sequence_count,printable_candidate_count,decision,next_action,payload_json) values (?,?,?,?,?,?,?)", (now(), frun or 0, len(out), cand, decision, next_action, j({"items": out})))
    run_id = cur.lastrowid
    for item in out:
        cur.execute("insert into external_sequence_base256_audit_items(run_id,sequence_id,refname,sequence_kind,digit_len,byte_len,printable_score,decoded_preview,candidate_status,evidence_json) values (?,?,?,?,?,?,?,?,?,?)", (run_id,item['sequence_id'],item.get('refname'),item['sequence_kind'],item['digit_len'],item['byte_len'],item['printable_score'],item['decoded_preview'],item['candidate_status'],j(item)))
    con.commit()
    print(json.dumps({"run_id":run_id,"decision":decision,"sequence_count":len(out),"printable_candidate_count":cand,"candidates":[{"sequence_id":i['sequence_id'],"decoded":i['decoded_preview'],"score":i['printable_score']} for i in out if i['candidate_status'].startswith('BASE256_EXTERNAL')]},ensure_ascii=False))
    if args.discord:
        cand_lines=[f"{i['sequence_id']}: {i['decoded_preview']} score={i['printable_score']}" for i in out if i['candidate_status'].startswith('BASE256_EXTERNAL')][:5] or ["nenhuma sequência externa virou texto legível por base256"]
        send('\n'.join([f"[469][external-base256][run={run_id}] base256 aplicado às sequências externas",f"sequências={len(out)} | candidatos legíveis={cand}",*cand_lines,f"decisão={decision}",f"próxima ação: {next_action}"]))
if __name__=='__main__': main()
