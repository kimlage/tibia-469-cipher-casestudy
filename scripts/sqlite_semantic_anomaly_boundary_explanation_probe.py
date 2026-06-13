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
TOP_N = 80


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


def classify(phrase: str, recommendation: str):
    p = phrase.lower()
    if "<unk:ttnvvn>" in p or "infinity last" in p or "fasten infinity" in p:
        return "FORMULA_OR_KNOWN_UNKNOWN", "mark as formula/known unknown; do not retext as prose"
    if "<suspect:vtlrnefie>" in p:
        return "SUSPECT_DISPLAY_TOKEN", "keep suspect marker; do not resolve to English"
    if recommendation and "SEGMENTATION" in recommendation:
        return "SEGMENTATION_DRIFT", "candidate for boundary scoring with zero-context features"
    if recommendation and "LOW_PRIORITY" in recommendation:
        return "LOW_PRIORITY_SURFACE_DRIFT", "do not spend confirmation lane unless it rises after formula masking"
    if "with with" in p or "a a" in p or "you've i" in p:
        return "SURFACE_REPETITION_DRIFT", "candidate for display-only cleanup; no lexical promotion"
    return "UNEXPLAINED_REVIEW", "manual/SQL review after known formula and boundary features are applied"


def create(cur: sqlite3.Cursor) -> None:
    cur.executescript(
        """
        create table if not exists semantic_anomaly_boundary_explanation_runs(
          run_id integer primary key autoincrement,
          created_at text not null,
          source_anomaly_run_id integer not null,
          source_zero_gate_run_id integer,
          analyzed_count integer not null,
          explained_count integer not null,
          unexplained_count integer not null,
          decision text not null,
          next_action text not null,
          payload_json text not null
        );
        create table if not exists semantic_anomaly_boundary_explanation_items(
          run_id integer not null,
          anomaly_rank integer not null,
          phrase text not null,
          score integer not null,
          explanation_class text not null,
          action text not null,
          promotion_allowed integer not null,
          evidence_json text not null,
          primary key(run_id, anomaly_rank)
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

    arun = one(cur, "select max(run_id) as run_id from semantic_anomaly_audit_items")
    zrun = one(cur, "select max(run_id) as run_id from zero_context_boundary_feature_gate_runs")
    anomalies = rows(cur, "select * from semantic_anomaly_audit_items where run_id=? order by rank limit ?", (arun.get("run_id"), TOP_N))
    items = []
    explained = 0
    for a in anomalies:
        cls, action = classify(a["phrase"], a.get("recommendation") or "")
        if cls != "UNEXPLAINED_REVIEW":
            explained += 1
        items.append({"rank": a["rank"], "phrase": a["phrase"], "score": a["score"], "recommendation": a.get("recommendation"), "class": cls, "action": action, "promotion_allowed": 0})
    unexplained = len(items) - explained
    decision = "ANOMALIES_MOSTLY_EXPLAINED_AS_FORMULA_BOUNDARY_DRIFT" if explained >= len(items) * 0.75 else "ANOMALIES_NEED_MORE_BOUNDARY_MODELING"
    next_action = "materialize a cleaned anomaly frontier excluding formula/known-unknown/display drift" if unexplained else "no anomaly promotion; maintain markers"
    cur.execute(
        """
        insert into semantic_anomaly_boundary_explanation_runs
        (created_at, source_anomaly_run_id, source_zero_gate_run_id, analyzed_count, explained_count, unexplained_count, decision, next_action, payload_json)
        values (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (now(), arun.get("run_id") or 0, zrun.get("run_id"), len(items), explained, unexplained, decision, next_action, j({"items": items})),
    )
    run_id = cur.lastrowid
    for item in items:
        cur.execute(
            """
            insert into semantic_anomaly_boundary_explanation_items
            (run_id, anomaly_rank, phrase, score, explanation_class, action, promotion_allowed, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, item["rank"], item["phrase"], item["score"], item["class"], item["action"], item["promotion_allowed"], j(item)),
        )
    con.commit()
    out = {"run_id": run_id, "decision": decision, "analyzed_count": len(items), "explained_count": explained, "unexplained_count": unexplained, "next_action": next_action}
    print(json.dumps(out, ensure_ascii=False))
    if args.discord:
        cls_counts = {}
        for item in items:
            cls_counts[item["class"]] = cls_counts.get(item["class"], 0) + 1
        send("\n".join([
            f"[469][anomaly-explain][run={run_id}] anomalias explicadas como fórmula/boundary/display",
            f"analisadas={len(items)} | explicadas={explained} | ainda abertas={unexplained} | classes={j(cls_counts)}",
            f"decisão={decision}",
            "sem promoção semântica: o avanço aqui é limpar falso inglês e separar fórmula/unknown de tradução real.",
            f"próxima ação: {next_action}",
        ]))


if __name__ == "__main__":
    main()
