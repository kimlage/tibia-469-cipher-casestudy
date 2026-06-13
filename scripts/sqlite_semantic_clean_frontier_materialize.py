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
        create table if not exists semantic_clean_frontier_runs(
          run_id integer primary key autoincrement,
          created_at text not null,
          source_explanation_run_id integer not null,
          source_belittle_gate_run_id integer,
          candidate_count integer not null,
          actionable_count integer not null,
          masked_as_formula_count integer not null,
          decision text not null,
          next_action text not null,
          payload_json text not null
        );
        create table if not exists semantic_clean_frontier_items(
          run_id integer not null,
          source_rank integer not null,
          phrase text not null,
          frontier_status text not null,
          reason text not null,
          action text not null,
          promotion_allowed integer not null,
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

    erun = one(cur, "select max(run_id) as run_id from semantic_anomaly_boundary_explanation_items")
    brun = one(cur, "select max(run_id) as run_id from belittle_men_formula_drift_gate_runs")
    unexplained = rows(cur, "select * from semantic_anomaly_boundary_explanation_items where run_id=? and explanation_class='UNEXPLAINED_REVIEW' order by anomaly_rank", (erun.get("run_id"),))
    belittle_gate = one(cur, "select * from belittle_men_formula_drift_gate_runs where run_id=?", (brun.get("run_id"),)) if brun.get("run_id") else {}
    items = []
    masked = 0
    actionable = 0
    for u in unexplained:
        phrase = u["phrase"]
        if belittle_gate and ("belittle men" in phrase.lower() or phrase.lower() == "i infinite fasten"):
            status = "MASKED_AS_FORMULA_DISPLAY_DRIFT"
            reason = "belittle_men_formula_drift_gate classified the open family as BENNA/formula display drift"
            action = "exclude from semantic promotion; retain formula/suspect marker"
            masked += 1
            promote = 0
        else:
            status = "ACTIONABLE_REVIEW"
            reason = "not explained by formula/boundary gates"
            action = "requires manual/SQL contrast before any promotion"
            actionable += 1
            promote = 0
        items.append({"source_rank": u["anomaly_rank"], "phrase": phrase, "frontier_status": status, "reason": reason, "action": action, "promotion_allowed": promote, "source": dict(u)})

    decision = "SEMANTIC_CLEAN_FRONTIER_EMPTY_NO_GLOSS" if actionable == 0 else "SEMANTIC_CLEAN_FRONTIER_HAS_ACTIONABLE_REVIEWS"
    next_action = "build next segmentation scorer using formula masks and zero-boundary features; do not promote text" if actionable == 0 else "review actionable clean frontier items"
    cur.execute(
        """
        insert into semantic_clean_frontier_runs
        (created_at, source_explanation_run_id, source_belittle_gate_run_id, candidate_count, actionable_count, masked_as_formula_count, decision, next_action, payload_json)
        values (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (now(), erun.get("run_id") or 0, brun.get("run_id"), len(items), actionable, masked, decision, next_action, j({"items": items, "belittle_gate": belittle_gate})),
    )
    run_id = cur.lastrowid
    for item in items:
        cur.execute(
            """
            insert into semantic_clean_frontier_items
            (run_id, source_rank, phrase, frontier_status, reason, action, promotion_allowed, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, item["source_rank"], item["phrase"], item["frontier_status"], item["reason"], item["action"], item["promotion_allowed"], j(item)),
        )
    con.commit()
    out = {"run_id": run_id, "decision": decision, "candidate_count": len(items), "actionable_count": actionable, "masked_as_formula_count": masked, "next_action": next_action}
    print(json.dumps(out, ensure_ascii=False))
    if args.discord:
        send("\n".join([
            f"[469][semantic-clean-frontier][run={run_id}] frontier semântica limpa materializada",
            f"candidatos vindos das anomalias={len(items)} | acionáveis={actionable} | mascarados como fórmula/display={masked}",
            f"decisão={decision}",
            "interpretação: não temos tradução lexical nova, mas removemos o principal falso inglês recorrente do caminho de decisão.",
            f"próxima ação: {next_action}",
        ]))


if __name__ == "__main__":
    main()
