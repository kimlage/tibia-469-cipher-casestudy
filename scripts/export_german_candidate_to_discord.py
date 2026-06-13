#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sqlite3
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "bonelord_operational.sqlite"
DISCORD_SKILL = Path("~/.codex/skills/discord/scripts/discord_skill.py")
CODEX_LOGS = "1471835253889962206"
BONELORD_LOGS = "0"


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def env_with_dotenv() -> dict[str, str]:
    env = os.environ.copy()
    path = Path("~/.env")
    if path.exists():
        for line in path.read_text().splitlines():
            if not line or line.lstrip().startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            env.setdefault(key.strip(), value.strip().strip('"').strip("'"))
    return env


def chunks(lines: list[str], limit: int) -> list[str]:
    out: list[str] = []
    current: list[str] = []
    size = 0
    for line in lines:
        add = len(line) + 1
        if current and size + add > limit:
            out.append("\n".join(current))
            current = []
            size = 0
        current.append(line)
        size += add
    if current:
        out.append("\n".join(current))
    return out


def send(channel: str, message: str) -> None:
    subprocess.run(
        ["python", str(DISCORD_SKILL), "send", "--channel", channel, "--message", message],
        cwd=str(ROOT),
        env=env_with_dotenv(),
        text=True,
        capture_output=True,
        check=False,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--channel", default=CODEX_LOGS)
    parser.add_argument("--summary-channel", default=BONELORD_LOGS)
    parser.add_argument("--limit", type=int, default=1800)
    parser.add_argument("--send", action="store_true")
    args = parser.parse_args()

    with connect() as conn:
        run = conn.execute("SELECT * FROM german_candidate_runs ORDER BY run_id DESC LIMIT 1").fetchone()
        if not run:
            raise SystemExit("no german candidate run found")
        books = conn.execute(
            "SELECT * FROM german_candidate_books WHERE run_id=? ORDER BY CAST(bookid AS INTEGER)",
            (run["run_id"],),
        ).fetchall()
        contigs = conn.execute(
            "SELECT * FROM german_candidate_contigs WHERE run_id=? ORDER BY CAST(basecontigid AS INTEGER)",
            (run["run_id"],),
        ).fetchall()

    book_lines = [
        f"[GERMAN-CANDIDATE][BOOKS][run={run['run_id']}][status={run['status']}]",
        f"coverage_avg={run['avg_coverage_pct']}% | coverage_min={run['min_coverage_pct']}% | pair_coverage={run['pair_coverage_pct']}%",
        "Observacao: candidato mecanicamente validado; nao e prova final da intencao da CipSoft.",
        "",
    ]
    for row in books:
        book_lines.extend(
            [
                f"Book {row['bookid']} | coverage={row['coverage_pct']}% | digits={row['digit_len']}",
                f"DE: {row['decoded_german'] or '<missing>'}",
                f"EN: {row['english'] or '<missing>'}",
                "",
            ]
        )

    contig_lines = [
        f"[GERMAN-CANDIDATE][CONTIGS][run={run['run_id']}][status={run['status']}]",
        "",
    ]
    for row in contigs:
        contig_lines.extend(
            [
                f"Contig {row['basecontigid']} | books={row['booksinorder']} | coverage_avg={row['coverage_avg_pct']}%",
                f"DE:\n{row['decoded_german']}",
                f"EN:\n{row['english']}",
                "",
            ]
        )

    book_chunks = chunks(book_lines, args.limit)
    contig_chunks = chunks(contig_lines, args.limit)
    index = (
        f"[GERMAN-CANDIDATE][INDEX][run={run['run_id']}]\n"
        f"books={len(books)} chunks={len(book_chunks)} | contigs={len(contigs)} chunks={len(contig_chunks)}\n"
        f"status={run['status']} | avg={run['avg_coverage_pct']}% | min={run['min_coverage_pct']}% | pair={run['pair_coverage_pct']}%"
    )
    done = (
        f"[GERMAN-CANDIDATE][DONE][run={run['run_id']}]\n"
        f"sent_books={len(books)} sent_contigs={len(contigs)} total_chunks={1 + len(book_chunks) + len(contig_chunks) + 1}"
    )
    if args.send:
        send(args.channel, index)
        for chunk in book_chunks:
            send(args.channel, chunk)
        for chunk in contig_chunks:
            send(args.channel, chunk)
        send(args.channel, done)
        send(
            args.summary_channel,
            f"[469][export][german-candidate] Publiquei no codex-logs o dump da nova hipótese alemã/MHG: {len(books)} livros, {len(contigs)} contigs, {len(book_chunks)+len(contig_chunks)+2} mensagens.",
        )
    print(index)
    print(done)


if __name__ == "__main__":
    main()
