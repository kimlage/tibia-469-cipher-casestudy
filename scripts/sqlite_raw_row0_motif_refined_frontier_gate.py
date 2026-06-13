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
BOUNDARY_TOKENS = {"*00", "L", "T", "A", "S", "V", "N", "I", "E", "F"}
KNOWN_SUBSTRINGS = ("L T A S T", "T T N V", "C68", "N A E S E", "B E N N A", "V N C68", "C86", "O23", "R20", "R02")


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


def create(cur: sqlite3.Cursor) -> None:
    cur.executescript(
        """
        create table if not exists raw_row0_motif_refined_frontier_gate_runs(
          run_id integer primary key autoincrement,
          created_at text not null,
          source_gate_run_id integer not null,
          input_new_count integer not null,
          retained_count integer not null,
          reclassified_count integer not null,
          decision text not null,
          next_action text not null,
          payload_json text not null
        );
        create table if not exists raw_row0_motif_refined_frontier_gate_items(
          run_id integer not null,
          source_rank integer not null,
          motif text not null,
          refined_status text not null,
          reason text not null,
          next_action text not null,
          evidence_json text not null,
          primary key(run_id, source_rank)
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

    grun = one(cur, "select max(run_id) as run_id from raw_row0_motif_function_gate_items")
    items_in = rows(cur, "select * from raw_row0_motif_function_gate_items where run_id=? and gate_status='NEW_RAW_STRUCTURAL_FRONTIER_NO_GLOSS' order by source_rank", (grun.get("run_id"),))
    out = []
    retained = 0
    reclassified = 0
    for item in items_in:
        motif = item["motif"]
        toks = motif.split()
        has_known = any(s in motif for s in KNOWN_SUBSTRINGS)
        only_boundary_surface = "*00" in toks and all(t in BOUNDARY_TOKENS for t in toks)
        ev = json.loads(item.get("evidence_json") or "{}")
        share = float(item.get("dominant_tag_share") or 0)
        dom = item.get("dominant_tag_id") or ""
        if has_known or only_boundary_surface or share >= 0.5:
            status = "RECLASSIFIED_EXISTING_BOUNDARY_FEATURE_NO_GLOSS"
            reason = f"motif is boundary/known-family surface (dominant={dom}, share={share})"
            next_action = "feed as feature to boundary scorer; do not open new hypothesis lane"
            reclassified += 1
        else:
            status = "RETAINED_NEW_RAW_FRONTIER_NO_GLOSS"
            reason = "not explained by known family or pure *00 boundary surface"
            next_action = "open narrow structural contrast lane"
            retained += 1
        out.append({"source_rank": item["source_rank"], "motif": motif, "refined_status": status, "reason": reason, "next_action": next_action, "source": dict(item), "source_evidence": ev})

    decision = "REFINED_RAW_FRONTIER_RETAINED_ITEMS" if retained else "REFINED_RAW_FRONTIER_EMPTY_ALL_BOUNDARY_FEATURES"
    next_action = "open retained narrow contrast lanes" if retained else "no new raw structural lane; seek external exact anchor or deeper generative model"
    cur.execute(
        """
        insert into raw_row0_motif_refined_frontier_gate_runs
        (created_at, source_gate_run_id, input_new_count, retained_count, reclassified_count, decision, next_action, payload_json)
        values (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (now(), grun.get("run_id") or 0, len(out), retained, reclassified, decision, next_action, j({"items": out})),
    )
    run_id = cur.lastrowid
    for item in out:
        cur.execute(
            """
            insert into raw_row0_motif_refined_frontier_gate_items
            (run_id, source_rank, motif, refined_status, reason, next_action, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, item["source_rank"], item["motif"], item["refined_status"], item["reason"], item["next_action"], j(item)),
        )
    con.commit()
    result = {"run_id": run_id, "decision": decision, "input_new_count": len(out), "retained_count": retained, "reclassified_count": reclassified, "retained": [{"motif": i["motif"], "reason": i["reason"]} for i in out if i["refined_status"].startswith("RETAINED")][:10]}
    print(json.dumps(result, ensure_ascii=False))
    if args.discord:
        lines = [f"{k+1}. {i['motif']} | {i['reason']}" for k, i in enumerate(out) if i["refined_status"].startswith("RETAINED")][:5] or ["nenhum motivo raw novo sobreviveu; todos reclassificados como boundary/família existente"]
        send("\n".join([
            f"[469][raw-motif-refined][run={run_id}] frontier raw refinada",
            f"entrada={len(out)} | retidos={retained} | reclassificados={reclassified} | gloss=0",
            *lines,
            f"decisão={decision}",
            f"próxima ação: {next_action}",
        ]))


if __name__ == "__main__":
    main()
