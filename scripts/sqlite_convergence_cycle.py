#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "bonelord_operational.sqlite"
DISCORD_SKILL = Path("~/.codex/skills/discord/scripts/discord_skill.py")
BONELORD_LOGS_CHANNEL = "0"


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run_json(cmd: list[str]) -> dict[str, Any]:
    proc = subprocess.run(cmd, cwd=str(ROOT), text=True, capture_output=True, check=True)
    return json.loads(proc.stdout)


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def top_rows(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT action_rank, phrase, hit_count, book_count, score, action_class
        FROM semantic_actionable_frontier_items
        WHERE run_id=(SELECT MAX(run_id) FROM semantic_actionable_frontier_runs)
        ORDER BY action_rank
        LIMIT 8
        """
    ).fetchall()


def latest_counts(conn: sqlite3.Connection) -> dict[str, Any]:
    row = conn.execute(
        """
        SELECT run_id, source_anomaly_run_id, actionable_count,
               excluded_known_count, excluded_blocked_count
        FROM semantic_actionable_frontier_runs
        ORDER BY run_id DESC
        LIMIT 1
        """
    ).fetchone()
    blocked = conn.execute("SELECT COUNT(*) AS n FROM semantic_blocked_phrases").fetchone()["n"]
    known = conn.execute("SELECT COUNT(*) AS n FROM semantic_known_unresolved_slots").fetchone()["n"]
    formulas = conn.execute("SELECT COUNT(*) AS n FROM semantic_formula_families").fetchone()["n"]
    return {
        "frontier_run_id": int(row["run_id"]) if row else None,
        "source_anomaly_run_id": int(row["source_anomaly_run_id"]) if row else None,
        "actionable_count": int(row["actionable_count"]) if row else 0,
        "excluded_known_count": int(row["excluded_known_count"]) if row else 0,
        "excluded_blocked_count": int(row["excluded_blocked_count"]) if row else 0,
        "blocked_phrase_count": int(blocked),
        "known_slot_count": int(known),
        "formula_family_count": int(formulas),
    }


def post_discord(message: str) -> None:
    if not DISCORD_SKILL.exists():
        return
    env = os.environ.copy()
    env_path = Path("~/.env")
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if not line or line.lstrip().startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            env.setdefault(key.strip(), value.strip().strip('"').strip("'"))
    subprocess.run(
        ["python", str(DISCORD_SKILL), "send", "--channel", BONELORD_LOGS_CHANNEL, "--message", message],
        cwd=str(ROOT),
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def build_message(summary: dict[str, Any], top: list[sqlite3.Row]) -> str:
    top_lines = []
    for row in top[:5]:
        top_lines.append(
            f"{row['action_rank']}. {row['phrase']} "
            f"({row['hit_count']} hits/{row['book_count']} books, score={row['score']}, {row['action_class']})"
        )
    if not top_lines:
        top_lines.append("nenhum alvo acionável novo; continuar busca externa/estrutural")
    return textwrap.dedent(
        f"""
        [469][cycle][{now()}]
        Estado SQL-first atualizado.
        best_shadow={summary['best_shadow_run_id']} | microtoken={summary['microtoken_run_id']} | formula={summary['formula_run_id']} | frontier={summary['frontier_run_id']}
        alvos acionáveis={summary['actionable_count']} | conhecidos/suspeitos excluídos={summary['excluded_known_count']} | famílias bloqueadas/audit-only excluídas={summary['excluded_blocked_count']}
        slots conhecidos={summary['known_slot_count']} | frases bloqueadas={summary['blocked_phrase_count']} | fórmulas={summary['formula_family_count']}
        Top acionável:
        {chr(10).join(top_lines)}
        Interpretação: o loop está priorizando confiança semântica. Itens excluídos não são resolvidos; são conhecidos como fórmula, suspeito ou audit-only para evitar falsa tradução.
        """
    ).strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--discord", action="store_true")
    args = parser.parse_args()

    best = run_json(["python", str(ROOT / "scripts/sqlite_materialize_best_shadow_books.py"), "--record", "--max-output-books", "0"])
    micro = run_json(["python", str(ROOT / "scripts/sqlite_microtoken_neutral_shadow.py"), "--record"])
    formula = run_json(["python", str(ROOT / "scripts/sqlite_formula_shadow.py"), "--limit", "30"])
    anomaly = run_json(["python", str(ROOT / "scripts/sqlite_semantic_anomaly_audit.py"), "--record", "--source", "microtoken_neutral"])
    frontier = run_json(["python", str(ROOT / "scripts/sqlite_semantic_actionable_frontier.py"), "--record", "--source", "microtoken_neutral", "--limit", "20"])

    with connect() as conn:
        counts = latest_counts(conn)
        top = top_rows(conn)
    summary = {
        **counts,
        "best_shadow_run_id": best.get("recorded_run_id"),
        "microtoken_run_id": micro.get("recorded_run_id"),
        "formula_run_id": formula.get("recorded_run_id"),
        "anomaly_run_id": anomaly.get("recorded_run_id"),
        "frontier_recorded_run_id": frontier.get("recorded_run_id"),
    }
    message = build_message(summary, top)
    if args.discord:
        post_discord(message)
    print(json.dumps({"summary": summary, "top": [dict(row) for row in top], "message": message}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
