#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import sqlite3
import subprocess
import tempfile
import time
from typing import Dict, List, Optional, Sequence, Tuple

from sqlite_snapshot_ref import DEFAULT_SNAPSHOT_NAME, fetch_export_row, resolve_export_id

DEFAULT_DB = "./data/bonelord_workbook.sqlite"
DEFAULT_CHANNEL_ID = "0"
DISCORD_SKILL_SCRIPT = "~/.codex/skills/discord/scripts/discord_skill.py"
DEFAULT_ENV_FILE = "~/.env"
MAX_MESSAGE_CHARS = 1800
SEND_RETRY_MAX = 6


def load_env_file(path: str) -> None:
    if not path or not os.path.exists(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                if not key:
                    continue
                if (value.startswith('"') and value.endswith('"')) or (
                    value.startswith("'") and value.endswith("'")
                ):
                    value = value[1:-1]
                os.environ.setdefault(key, value)
    except Exception:
        # Best effort only.
        return


def clean_value(v: object, missing_placeholder: str = "<empty>") -> str:
    if v is None:
        return missing_placeholder
    s = str(v).strip()
    if not s:
        return missing_placeholder
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = " / ".join(part.strip() for part in s.split("\n") if part.strip())
    return s or missing_placeholder


def sort_maybe_numeric(value: str) -> Tuple[int, int | str]:
    try:
        return (0, int(value))
    except Exception:
        return (1, value)


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def latest_export(conn: sqlite3.Connection) -> sqlite3.Row:
    row = conn.execute("SELECT * FROM exports ORDER BY export_id DESC LIMIT 1").fetchone()
    if row is None:
        raise SystemExit("No snapshots in SQLite DB.")
    return row


def fetch_flow_value(conn: sqlite3.Connection, export_id: int, key: str) -> str:
    row = conn.execute(
        """
        SELECT value
        FROM sheet__flowstate
        WHERE __export_id = ? AND key = ?
        ORDER BY __row_index
        LIMIT 1
        """,
        (export_id, key),
    ).fetchone()
    if row is None or row["value"] is None:
        return "unknown"
    return str(row["value"])


def extract_books(conn: sqlite3.Connection, export_id: int) -> List[str]:
    rows = conn.execute(
        """
        SELECT
            bookid,
            translation_strictplus_v108,
            translation_semantic_auto,
            translation_english_auto,
            translation_contextenglish_auto
        FROM sheet__books
        WHERE __export_id = ?
        ORDER BY CAST(bookid AS INTEGER), __row_index
        """,
        (export_id,),
    ).fetchall()
    out: List[str] = []
    for row in rows:
        book_id = clean_value(row["bookid"])
        if book_id == "<empty>":
            continue
        strict_plus = clean_value(row["translation_strictplus_v108"])
        semantic = clean_value(row["translation_semantic_auto"])
        english = clean_value(row["translation_english_auto"])
        context = clean_value(row["translation_contextenglish_auto"])
        out.append(
            "\n".join(
                [
                    f"Book {book_id}",
                    f"StrictPlus: {strict_plus}",
                    f"Semantic: {semantic}",
                    f"English: {english}",
                    f"ContextEnglish: {context}",
                ]
            )
        )
    return out


def extract_contigs(conn: sqlite3.Connection, export_id: int) -> List[str]:
    rows = conn.execute(
        """
        SELECT
            basecontigid,
            translation_strictplus_v108,
            translation_semneutral_v123,
            translation_highonly_v123
        FROM sheet__contigs
        WHERE __export_id = ?
        ORDER BY CAST(basecontigid AS INTEGER), __row_index
        """,
        (export_id,),
    ).fetchall()
    out: List[str] = []
    for row in rows:
        contig_id = clean_value(row["basecontigid"])
        if contig_id == "<empty>":
            continue
        strict_plus = clean_value(row["translation_strictplus_v108"])
        sem_neutral = clean_value(row["translation_semneutral_v123"])
        high_only = clean_value(row["translation_highonly_v123"])
        out.append(
            "\n".join(
                [
                    f"Contig {contig_id}",
                    f"StrictPlus: {strict_plus}",
                    f"SemNeutral: {sem_neutral}",
                    f"HighOnly: {high_only}",
                ]
            )
        )
    return out


def extract_external_roundtrip_latest(conn: sqlite3.Connection, export_id: int) -> Dict[str, Tuple[str, str]]:
    tables = {
        row["name"]
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
    }
    if "sheet__externalroundtrip_auto" not in tables:
        return {}
    rows = conn.execute(
        """
        SELECT
            refname,
            dp_current,
            pass,
            COALESCE(CAST(iteration AS INTEGER), 0) AS iteration
        FROM sheet__externalroundtrip_auto
        WHERE __export_id = ?
        ORDER BY refname, iteration DESC, __row_index DESC
        """,
        (export_id,),
    ).fetchall()
    latest: Dict[str, Tuple[int, str, str]] = {}
    for row in rows:
        ref_name = clean_value(row["refname"], missing_placeholder="")
        if not ref_name:
            continue
        iteration = int(row["iteration"] or 0)
        dp_current = clean_value(row["dp_current"], missing_placeholder="<missing>")
        passed = clean_value(row["pass"], missing_placeholder="<missing>")
        prev = latest.get(ref_name)
        if prev is None or iteration >= prev[0]:
            latest[ref_name] = (iteration, dp_current, passed)
    return {k: (v[1], v[2]) for k, v in latest.items()}


def extract_externals(conn: sqlite3.Connection, export_id: int) -> List[str]:
    rt_map = extract_external_roundtrip_latest(conn, export_id)
    rows = conn.execute(
        """
        SELECT
            refname,
            type,
            source,
            dp_strictplus,
            codestreamdp_readable_v119,
            codestreamdp_lossless_v119
        FROM sheet__externalrefs_v115
        WHERE __export_id = ?
        ORDER BY __row_index
        """,
        (export_id,),
    ).fetchall()
    out: List[str] = []
    for row in rows:
        ref_name = clean_value(row["refname"])
        if ref_name == "<empty>":
            continue
        typ = clean_value(row["type"])
        source = clean_value(row["source"])
        dp_strict = clean_value(row["dp_strictplus"])
        cs_read = clean_value(row["codestreamdp_readable_v119"])
        cs_loss = clean_value(row["codestreamdp_lossless_v119"])
        dp_current, passed = rt_map.get(ref_name, ("<missing>", "<missing>"))

        out.append(
            "\n".join(
                [
                    f"{ref_name} | type={typ} | source={source}",
                    f"DP_StrictPlus: {dp_strict}",
                    f"CodeStream_Readable: {cs_read}",
                    f"CodeStream_Lossless: {cs_loss}",
                    f"DP_Current: {dp_current} | Pass={passed}",
                ]
            )
        )
    return out


def split_block_by_line(block: str, max_len: int) -> List[str]:
    lines = block.split("\n")
    chunks: List[str] = []
    cur: List[str] = []
    cur_len = 0
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if len(line) > max_len:
            line = line[: max_len - 3] + "..."
        add_len = len(line) + (1 if cur else 0)
        if cur and cur_len + add_len > max_len:
            chunks.append("\n".join(cur))
            cur = [line]
            cur_len = len(line)
        else:
            if cur:
                cur_len += 1 + len(line)
            else:
                cur_len = len(line)
            cur.append(line)
    if cur:
        chunks.append("\n".join(cur))
    return chunks


def build_section_messages(
    section_name: str,
    items: Sequence[str],
    iteration: str,
    max_chars: int = MAX_MESSAGE_CHARS,
) -> List[str]:
    body_limit = max_chars - 120
    item_units: List[str] = []
    for item in items:
        item = item.strip()
        if not item:
            continue
        if len(item) <= body_limit:
            item_units.append(item)
        else:
            item_units.extend(split_block_by_line(item, body_limit))

    bodies: List[str] = []
    cur = ""
    for unit in item_units:
        candidate = unit if not cur else f"{cur}\n\n{unit}"
        if len(candidate) <= body_limit:
            cur = candidate
        else:
            if cur:
                bodies.append(cur)
            cur = unit
    if cur:
        bodies.append(cur)

    total = max(1, len(bodies))
    if not bodies:
        bodies = ["<sem conteudo>"]
        total = 1

    messages: List[str] = []
    for i, body in enumerate(bodies, start=1):
        header = f"[TRADUCAO-AUDIT][SECAO {section_name} {i}/{total}][iter={iteration}]"
        msg = f"{header}\n{body}"
        if len(msg) > max_chars:
            # Hard guard (shouldn't happen due to conservative body_limit).
            msg = msg[: max_chars - 3] + "..."
        messages.append(msg)
    return messages


def send_discord_message(channel_id: str, message: str) -> None:
    attempts = 0
    while True:
        attempts += 1
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as tf:
            tf.write(message)
            msg_path = tf.name
        try:
            proc = subprocess.run(
                [
                    "python",
                    DISCORD_SKILL_SCRIPT,
                    "send",
                    "--channel",
                    channel_id,
                    "--message-file",
                    msg_path,
                ],
                capture_output=True,
                text=True,
                env=os.environ.copy(),
            )
        finally:
            try:
                os.unlink(msg_path)
            except OSError:
                pass

        if proc.returncode == 0:
            return

        stderr = proc.stderr or ""
        wait_s = None
        m = re.search(r"retry_after=([0-9]+(?:\.[0-9]+)?)s", stderr)
        if m:
            wait_s = float(m.group(1))
        else:
            m_json = re.search(r'"retry_after"\s*:\s*([0-9]+(?:\.[0-9]+)?)', stderr)
            if m_json:
                wait_s = float(m_json.group(1))

        if wait_s is not None and attempts < SEND_RETRY_MAX:
            time.sleep(max(0.5, wait_s))
            continue

        raise RuntimeError(
            "Discord send failed.\n"
            f"channel={channel_id}\n"
            f"returncode={proc.returncode}\n"
            f"stderr={stderr.strip()}\n"
            f"stdout={(proc.stdout or '').strip()}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Export full translation snapshot from SQLite to Discord.")
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--export-id", type=int, default=None)
    parser.add_argument("--snapshot-name", default=DEFAULT_SNAPSHOT_NAME)
    parser.add_argument("--channel", default=DEFAULT_CHANNEL_ID)
    parser.add_argument("--max-chars", type=int, default=MAX_MESSAGE_CHARS)
    parser.add_argument("--env-file", default=DEFAULT_ENV_FILE)
    args = parser.parse_args()

    load_env_file(args.env_file)

    conn = connect(args.db)
    try:
        export_id = resolve_export_id(conn, export_id=args.export_id, snapshot_name=args.snapshot_name)
        export = fetch_export_row(conn, export_id)
        artifact_path = export["artifact_path"] if "artifact_path" in export.keys() and export["artifact_path"] else export["workbook_path"]
        iteration = fetch_flow_value(conn, export_id, "CurrentIteration")

        books_items = extract_books(conn, export_id)
        contigs_items = extract_contigs(conn, export_id)
        external_items = extract_externals(conn, export_id)

        books_msgs = build_section_messages("BOOKS", books_items, iteration, args.max_chars)
        contigs_msgs = build_section_messages("CONTIGS", contigs_items, iteration, args.max_chars)
        external_msgs = build_section_messages("EXTERNOS", external_items, iteration, args.max_chars)

        total_section_msgs = len(books_msgs) + len(contigs_msgs) + len(external_msgs)
        total_expected = total_section_msgs + 2

        index_msg = "\n".join(
            [
                f"[TRADUCAO-AUDIT][INDICE][iter={iteration}]",
                f"Snapshot export_id: {export_id}",
                f"Artifact: {artifact_path}",
                f"Canal: bonelord-logs ({args.channel})",
                "Formato: comparativo por camadas",
                "Itens:",
                f"- Books: {len(books_items)} (chunks={len(books_msgs)})",
                f"- Contigs: {len(contigs_items)} (chunks={len(contigs_msgs)})",
                f"- Externos: {len(external_items)} (chunks={len(external_msgs)})",
                f"Mensagens previstas: {total_expected} (indice+secoes+conclusao)",
            ]
        )

        sent = 0
        send_discord_message(args.channel, index_msg)
        sent += 1

        for msg in books_msgs:
            send_discord_message(args.channel, msg)
            sent += 1
        for msg in contigs_msgs:
            send_discord_message(args.channel, msg)
            sent += 1
        for msg in external_msgs:
            send_discord_message(args.channel, msg)
            sent += 1

        final_msg = "\n".join(
            [
                f"[TRADUCAO-AUDIT][CONCLUSAO][iter={iteration}]",
                "Checksum envio:",
                f"- Books enviados: {len(books_items)}",
                f"- Contigs enviados: {len(contigs_items)}",
                f"- Externos enviados: {len(external_items)}",
                f"- Mensagens de seções: {total_section_msgs}",
                f"- Mensagens totais enviadas: {sent + 1}",
                "Status: OK",
            ]
        )
        send_discord_message(args.channel, final_msg)
        sent += 1

        print(
            f"DONE iter={iteration} channel={args.channel} "
            f"books={len(books_items)} contigs={len(contigs_items)} externals={len(external_items)} "
            f"messages_sent={sent} export_id={export_id}"
        )
    finally:
        conn.close()


if __name__ == "__main__":
    main()
