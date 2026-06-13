#!/usr/bin/env python3
"""Export a functional, no-gloss row0 view for books and contigs."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "bonelord_operational.sqlite"
DEFAULT_OUT = ROOT / "data" / "exports" / "functional_row0"

FRAME_PATTERNS = [
    ("LTAST_TAIL", "FUNCTION_STRONG", "continuation_operator", ["L", "T", "A", "S", "T", "T", "N"], "<CONT:LTAST_TAIL>", "</CONT>"),
    ("BENNA_FORMULA", "FORMULA_CONTEXT", "formula_context", ["B", "E", "N", "N", "A"], "<FORMULA:BENNA_FORMULA>", "</FORMULA>"),
    ("NAESE_IVIFAST", "SLOT_CLASSIFIER", "slot_classifier", ["I", "V", "I", "F", "A", "S", "T", "F", "N", "E", "I", "E", "I", "N", "T", "A"], "<SLOT:NAESE_IVIFAST>", "</SLOT>"),
    ("C68_FATCT_SLOT", "SLOT_CLASSIFIER", "local_naese_fatct_slot", ["E", "S", "E", "S", "T", "I", "E", "N", "F", "A", "T", "C68", "T", "I", "V", "V", "T", "I", "S", "E", "T"], "<SLOT:C68_FATCT_LOCAL>", "</SLOT>"),
    ("O23_ONAF", "FUNCTION_READY", "endpoint_continuation_frame", ["O23", "N", "A", "F", "I", "E", "I"], "<FRAME:O23_ONAF>", "</FRAME>"),
    ("C86_BRANCH_EVIEFIIN_TO_VN_C68_TIIN", "SUBFUNCTION_READY", "c86_payload_branch", ["C86", "E", "V", "I", "E", "F", "I", "I", "N", "I", "*00", "V", "N", "C68", "T", "I", "I", "N"], "<SUBFN:C86_EVIEFIIN_VN_C68_TIIN>", "</SUBFN>"),
    ("C86_BRANCH_EBFAI_STAR_VL_TO_VINVIN", "SUBFUNCTION_READY", "c86_payload_branch", ["C86", "E", "B", "F", "A", "I", "*00", "V", "L", "V", "E", "E", "I", "I", "V", "E", "V", "I", "N", "V", "I", "N"], "<SUBFN:C86_EBFAI_VINVIN>", "</SUBFN>"),
    ("C86_ICE_OPERATOR_OPEN", "FUNCTION_READY", "operator_payload_right", ["*00", "I", "C86", "E"], "<FRAME:C86_OPERATOR_OPEN>", "</FRAME>"),
    ("R20_VAETRFEVAST_BLOCK", "FUNCTION_READY", "local_phase_block", ["V", "A", "E", "T", "R20", "F", "E", "V", "A", "S", "T"], "<FRAME:R20_VAETRFEVAST>", "</FRAME>"),
    ("R02_TRVEIIVNTBB_BRIDGE", "FUNCTION_READY", "local_phase_bridge", ["T", "R02", "V", "E", "I", "I", "V", "N", "T", "B", "B"], "<FRAME:R02_TRVEIIVNTBB>", "</FRAME>"),
    ("VINVIN_BRANCH_INEIIVNSENI_STAR_LEAENT", "SUBFUNCTION_READY", "vinvin_branch_continuation", ["V", "I", "N", "V", "I", "N", "S", "T", "A", "E", "*00", "V", "T", "L", "R20", "N", "E", "F", "I", "E", "A", "I", "F", "A", "I", "F", "A", "I", "F", "I", "N", "E", "I", "I", "V", "N", "S", "E", "N", "I", "*00", "L", "E", "A", "E", "N", "T"], "<SUBFN:VINVIN_LEAENT>", "</SUBFN>"),
    ("VINVIN_BRANCH_TIFAVONAFIEI", "SUBFUNCTION_READY", "vinvin_branch_o23_continuation", ["V", "I", "N", "V", "I", "N", "S", "T", "A", "E", "*00", "V", "T", "L", "R20", "N", "E", "F", "I", "E", "A", "I", "F", "A", "I", "F", "A", "I", "F", "T", "I", "F", "A", "V", "O23", "N", "A", "F", "I", "E", "I"], "<SUBFN:VINVIN_TIFAVONAFIEI>", "</SUBFN>"),
    ("VINVIN_VTLR", "FUNCTION_READY", "branch_operator_frame", ["V", "I", "N", "V", "I", "N", "S", "T", "A", "E", "*00", "V", "T", "L", "R20", "N", "E", "F", "I", "E"], "<FRAME:VINVIN_VTLR>", "</FRAME>"),
]


def jdump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def latest_id(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT run_id FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    if row is None:
        raise SystemExit(f"missing required table data: {table}")
    return int(row["run_id"])


def find_frame(tokens: list[str], frame: list[str]) -> list[int]:
    starts = []
    size = len(frame)
    for idx in range(0, len(tokens) - size + 1):
        if tokens[idx : idx + size] == frame:
            starts.append(idx)
    return starts


def token_parts(token: str) -> tuple[str, str | None]:
    if token == "*00":
        return "*", "00"
    if len(token) > 1 and token[0].isalpha() and token[1:].isdigit():
        return token[0], token[1:]
    return token, None


def build_spans(tokens: list[str]) -> list[dict[str, Any]]:
    spans: list[dict[str, Any]] = []
    for function_id, status, role, pattern, open_tag, close_tag in FRAME_PATTERNS:
        for start in find_frame(tokens, pattern):
            spans.append(
                {
                    "start": start,
                    "end": start + len(pattern),
                    "text": " ".join(tokens[start : start + len(pattern)]),
                    "function_id": function_id,
                    "role": role,
                    "status": status,
                    "render_open": open_tag,
                    "render_close": close_tag,
                    "precedence": 1 if status == "FUNCTION_STRONG" else 2 if status == "SUBFUNCTION_READY" else 3,
                }
            )
    spans.sort(key=lambda row: (row["start"], row["precedence"], -(row["end"] - row["start"])))
    accepted: list[dict[str, Any]] = []
    occupied: set[int] = set()
    for span in spans:
        positions = set(range(span["start"], span["end"]))
        if occupied & positions:
            continue
        accepted.append(span)
        occupied |= positions
    return sorted(accepted, key=lambda row: row["start"])


def render_tokens(tokens: list[str], spans: list[dict[str, Any]]) -> str:
    opens = {span["start"]: span for span in spans}
    closes = {span["end"]: span for span in spans}
    parts: list[str] = []
    for idx, token in enumerate(tokens):
        if idx in opens:
            parts.append(opens[idx]["render_open"])
        if token == "*00":
            parts.append("<OP:STAR_00:*00>")
        elif token == "O32":
            parts.append("<AUDIT:FRAME_O32_SINGLETON>O32</AUDIT>")
        elif token in {"C68", "C86", "R20", "R02", "O23"}:
            parts.append(f"<CTX:{token}>{token}</CTX>")
        else:
            parts.append(token)
        if idx + 1 in closes:
            parts.append(closes[idx + 1]["render_close"])
    return " ".join(parts)


def export_books(conn: sqlite3.Connection, out_dir: Path) -> tuple[int, int]:
    run_id = latest_id(conn, "row0_variant_frontier_runs")
    rows = conn.execute(
        """
        SELECT bookid, token_count, symbol_text, tokens_json
        FROM row0_variant_book_tokens
        WHERE run_id=?
        ORDER BY CAST(bookid AS INTEGER)
        """,
        (run_id,),
    ).fetchall()
    jsonl_path = out_dir / "functional_row0_books.jsonl"
    txt_path = out_dir / "functional_row0_books.txt"
    item_count = 0
    span_count = 0
    with jsonl_path.open("w", encoding="utf-8") as jf, txt_path.open("w", encoding="utf-8") as tf:
        for row in rows:
            tokens = json.loads(row["tokens_json"] or "[]")
            spans = build_spans(tokens)
            span_count += len(spans)
            token_objs = []
            for idx, token in enumerate(tokens):
                symbol, code = token_parts(token)
                roles = []
                function_ids = []
                if token == "*00":
                    roles.append("boundary_operator")
                    function_ids.append("STAR_00")
                elif token in {"C68", "C86", "R20", "R02", "O23"}:
                    roles.append("context_frame")
                elif token == "O32":
                    roles.append("audit_only")
                token_objs.append({"i": idx, "token": token, "symbol": symbol, "code": code, "roles": roles, "function_ids": function_ids})
            rendered = render_tokens(tokens, spans)
            payload = {
                "view_type": "book",
                "bookid": str(row["bookid"]),
                "row0_variant_run_id": run_id,
                "token_count": int(row["token_count"]),
                "raw_symbol_text": row["symbol_text"],
                "tokens": token_objs,
                "spans": [{k: v for k, v in span.items() if k != "precedence"} for span in spans],
                "rendered": rendered,
                "warnings": ["no_plaintext_gloss", "functional_markers_only"],
            }
            jf.write(jdump(payload) + "\n")
            tf.write(f"BOOK {row['bookid']} | tokens={row['token_count']} | spans={len(spans)}\n{rendered}\n\n")
            item_count += 1
    return item_count, span_count


def export_contigs(conn: sqlite3.Connection, out_dir: Path) -> int:
    rows = conn.execute(
        """
        SELECT c.basecontigid, c.booksinorder, c.basecontig,
               o.run_id AS overlap_run_id, o.expected_length, o.reconstructed_length,
               o.exact_match, o.transition_count, o.min_overlap_symbols,
               o.max_overlap_symbols, o.payload_json
        FROM sheet__contigs c
        LEFT JOIN contig_max_overlap_items o
          ON o.basecontigid = c.basecontigid
         AND o.run_id = (SELECT MAX(run_id) FROM contig_max_overlap_items)
        WHERE c.__export_id = (SELECT MAX(__export_id) FROM sheet__contigs)
        ORDER BY CAST(c.basecontigid AS INTEGER)
        """
    ).fetchall()
    jsonl_path = out_dir / "functional_row0_contigs.jsonl"
    txt_path = out_dir / "functional_row0_contigs.txt"
    with jsonl_path.open("w", encoding="utf-8") as jf, txt_path.open("w", encoding="utf-8") as tf:
        for row in rows:
            books = [part.strip() for part in (row["booksinorder"] or "").split("->") if part.strip()]
            payload = {
                "view_type": "contig",
                "basecontigid": str(row["basecontigid"]),
                "booksinorder": books,
                "overlap_run_id": row["overlap_run_id"],
                "exact_match": bool(row["exact_match"]),
                "expected_length": int(row["expected_length"] or 0),
                "reconstructed_length": int(row["reconstructed_length"] or 0),
                "transition_count": int(row["transition_count"] or 0),
                "overlap": {"min_symbols": int(row["min_overlap_symbols"] or 0), "max_symbols": int(row["max_overlap_symbols"] or 0)},
                "render_policy": "collapse_validated_overlap",
                "raw_basecontig": row["basecontig"],
                "warnings": ["contig_text_not_plaintext", "validated_overlap_only"],
            }
            jf.write(jdump(payload) + "\n")
            tf.write(
                f"CONTIG {row['basecontigid']} | books={row['booksinorder']} | exact_overlap={int(row['exact_match'] or 0)} | len={row['expected_length']}\n"
                f"{row['basecontig']}\n\n"
            )
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    book_count, span_count = export_books(conn, args.out)
    contig_count = export_contigs(conn, args.out)
    summary = {
        "decision": "FUNCTIONAL_ROW0_EXPORT_READY",
        "out_dir": str(args.out),
        "book_count": book_count,
        "contig_count": contig_count,
        "span_count": span_count,
        "gloss_allowed": False,
        "files": [
            str(args.out / "functional_row0_books.jsonl"),
            str(args.out / "functional_row0_books.txt"),
            str(args.out / "functional_row0_contigs.jsonl"),
            str(args.out / "functional_row0_contigs.txt"),
        ],
    }
    (args.out / "summary.json").write_text(jdump(summary) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
