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


def create(cur: sqlite3.Cursor) -> None:
    cur.executescript(
        """
        create table if not exists semantic_optimization_problem_runs(
          run_id integer primary key autoincrement,
          created_at text not null,
          problem_id text not null,
          objective text not null,
          hard_constraints_json text not null,
          soft_objectives_json text not null,
          negative_controls_json text not null,
          holdouts_json text not null,
          first_probe text not null,
          decision text not null,
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
    cur = con.cursor()
    create(cur)

    hard_constraints = [
        "no book-level gloss unless exact source-attested sequence+meaning or independently validated segmentation survives holdouts",
        "do not derive component dictionary from phrase-level DP roundtrip alone",
        "Tibia.org hex signature is contamination, not 469 semantic anchor",
        "books 4/34/49 remain blocked unless new non-fragmented route appears",
        "all proposed semantic readings must preserve ExternalRoundTrip phrase holdouts: Knightmare1 and Poll2014_C",
    ]
    soft_objectives = [
        "maximize stable segmentation into plausible Middle/Old English compatible tokens",
        "minimize semantic contradictions across repeated row0 components",
        "reward predictions that explain article160 holdout cluster 15/16/39 without using it as training truth",
        "penalize wildcard/00 overuse and anagram freedom unless needed by multiple independent holdouts",
        "prefer readings that leave unresolved tokens explicit instead of filling with fluent hallucinated English",
    ]
    negative_controls = [
        "Book49 O32/NEEI/LEII residual family",
        "Book4 unsupported C86/O23/R20 mixed surface",
        "Book34 fragmented LEAFIVNANI recurrence with controls 17/68",
        "AvarTar poem as external holdout only",
    ]
    holdouts = [
        "NPC Knightmare1 phrase-level roundtrip: BE A WIT THAN BE <*> FOOL, no component gloss",
        "Poll2014_C phrase-level roundtrip: you've through so yet far away, no component gloss",
        "Article160 fast/boots/fifteen-statues cluster: books 15/16/39, component-only, no promotion",
        "NPC Elder2 look-at-you phrase: external NPC only, no book contamination",
    ]
    first_probe = "build sqlite_semantic_segmentation_scorer.py over row0/honest text for books 15/16/39 plus NPC phrase holdouts; output candidate segmentations with unresolved markers, not translations"
    payload = {
        "problem_id": "SEMANTIC_CONSISTENCY_UNDER_RESTRICTIONS_V1",
        "rationale": "Mechanical coverage is high but semantic gloss is zero. The next useful step is constrained semantic scoring, not more structural promotion or fluent rewriting.",
    }
    cur.execute(
        """
        insert into semantic_optimization_problem_runs
        (created_at, problem_id, objective, hard_constraints_json, soft_objectives_json, negative_controls_json, holdouts_json, first_probe, decision, payload_json)
        values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (now(), "SEMANTIC_CONSISTENCY_UNDER_RESTRICTIONS_V1", "reduce semantic contradiction while keeping unverifiable gloss at zero", j(hard_constraints), j(soft_objectives), j(negative_controls), j(holdouts), first_probe, "NEXT_MODE_REGISTERED_NO_GLOSS_PROMOTION", j(payload)),
    )
    run_id = cur.lastrowid
    con.commit()
    out = {"run_id": run_id, "decision": "NEXT_MODE_REGISTERED_NO_GLOSS_PROMOTION", "first_probe": first_probe}
    print(json.dumps(out, ensure_ascii=False))
    if args.discord:
        send("\n".join([
            f"[469][semantic-optimization][run={run_id}] novo modo registrado: consistência semântica sob restrições",
            "objetivo: reduzir contradição semântica mantendo gloss não-verificado em 0, em vez de gerar frases fluentes.",
            "hard gates: sem significado por DP isolado; sem usar assinatura hex; sem promover 4/34/49; holdouts NPC precisam continuar válidos.",
            "primeiro probe: scorer de segmentação semântica para 15/16/39 + holdouts NPC, emitindo <UNK>/<SUSPECT> em vez de inventar inglês.",
        ]))


if __name__ == "__main__":
    main()
