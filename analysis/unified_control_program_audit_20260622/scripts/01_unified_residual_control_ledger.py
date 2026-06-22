from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
COPY_SOURCE_LEDGER = (
    ROOT
    / "analysis"
    / "copy_source_generation_audit_20260621"
    / "reports"
    / "test_results"
    / "01_copy_source_ledger.json"
)
COPY_HINT_LOWER_BOUND = (
    ROOT
    / "analysis"
    / "latent_transducer_generation_audit_20260622"
    / "reports"
    / "test_results"
    / "08_copy_hint_stream_lower_bound.json"
)
COPY_HINT_STRUCTURE = (
    ROOT
    / "analysis"
    / "latent_transducer_generation_audit_20260622"
    / "reports"
    / "test_results"
    / "09_copy_hint_stream_structure_gate.json"
)

OUT_STEM = "01_unified_residual_control_ledger"
DIGIT_BITS = math.log2(10)
COPY_HINT_POLICY = "frequent_longest"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def assert_boundary(name: str, data: dict[str, Any]) -> None:
    if data.get("translation_delta") != "NONE":
        raise RuntimeError(f"{name} changed translation boundary")
    if data.get("case_reopened", False) is not False:
        raise RuntimeError(f"{name} reopened case")
    if data.get("plaintext_claim", False) is not False:
        raise RuntimeError(f"{name} introduced plaintext")
    decision = data.get("decision", {})
    if decision.get("row0_origin_status") not in {
        None,
        "unchanged_exogenous",
        "exogenous_under_current_evidence",
    }:
        raise RuntimeError(f"{name} changed row0 origin")
    if decision.get("translation_or_plaintext_status", "NONE") != "NONE":
        raise RuntimeError(f"{name} introduced translation/plaintext")


def length_bucket(length: int) -> str:
    if length <= 8:
        return "len_0008"
    if length <= 16:
        return "len_0016"
    if length <= 32:
        return "len_0032"
    if length <= 64:
        return "len_0064"
    if length <= 128:
        return "len_0128"
    return "len_0256p"


def rank_bucket(rank: int | None) -> str | None:
    if rank is None:
        return None
    return f"rank_log2_{int(math.floor(math.log2(rank))):02d}"


def target_phase(book: int) -> str:
    if book < 20:
        return "phase_10_19"
    if book < 35:
        return "phase_20_34"
    if book < 50:
        return "phase_35_49"
    if book < 60:
        return "phase_50_59"
    return "phase_60_69"


def op_pos_bucket(op_index: int, op_count: int) -> str:
    if op_index == 0:
        return "first"
    if op_index == op_count - 1:
        return "last"
    if op_index <= 2:
        return "early"
    return "middle"


def unique_chunks_at_length(available: str, length: int) -> list[dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for source in range(0, len(available) - length + 1):
        chunk = available[source : source + length]
        row = rows.get(chunk)
        if row is None:
            rows[chunk] = {
                "chunk": chunk,
                "min_source": source,
                "max_source": source,
                "count": 1,
            }
        else:
            row["max_source"] = source
            row["count"] += 1
    return list(rows.values())


def frequent_longest_key(row: dict[str, Any], available_len: int, length: int) -> tuple[Any, ...]:
    return (
        -int(row["count"]),
        available_len - (int(row["max_source"]) + length),
        row["chunk"],
    )


def copy_hint_metrics(available: str, payload: str) -> dict[str, Any]:
    length = len(payload)
    rows = unique_chunks_at_length(available, length)
    correct = next(row for row in rows if row["chunk"] == payload)
    correct_key = frequent_longest_key(correct, len(available), length)
    rank = 1 + sum(
        1
        for row in rows
        if frequent_longest_key(row, len(available), length) < correct_key
    )
    return {
        "same_length_chunk_count": len(rows),
        "copy_hint_policy": COPY_HINT_POLICY,
        "copy_hint_rank": rank,
        "copy_hint_rank_bits": math.log2(rank),
        "copy_hint_rank_bucket": rank_bucket(rank),
        "same_length_chunk_hint_bits": math.log2(len(rows)),
        "copy_hint_source_occurrences": int(correct["count"]),
    }


def make_ledger() -> dict[str, Any]:
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    copy_ledger = load_json(COPY_SOURCE_LEDGER)
    hint_lower = load_json(COPY_HINT_LOWER_BOUND)
    hint_structure = load_json(COPY_HINT_STRUCTURE)
    assert_boundary("copy_source_ledger", copy_ledger)
    assert_boundary("copy_hint_stream_lower_bound", hint_lower)
    assert_boundary("copy_hint_stream_structure_gate", hint_structure)
    rows: list[dict[str, Any]] = []
    literal_tape_pos = 0
    global_op_index = 0
    for book_key, ops in copy_ledger["canonical_ops_by_book"].items():
        book = int(book_key)
        target = books[book]
        emitted_base = "".join(books[index] for index in range(book))
        running_start = 0
        for op_index, op in enumerate(ops):
            op_type = op["type"]
            length = int(op["length"])
            target_start = int(op["target_start"])
            if target_start != running_start:
                raise RuntimeError(f"target_start mismatch book={book} op={op_index}")
            row: dict[str, Any] = {
                "book": book,
                "book_phase": target_phase(book),
                "op_index": op_index,
                "global_op_index": global_op_index,
                "op_pos_bucket": op_pos_bucket(op_index, len(ops)),
                "target_start": target_start,
                "book_length": len(target),
                "remaining_before_op": len(target) - target_start,
                "op_type": op_type,
                "length": length,
                "length_bucket": length_bucket(length),
                "type_length_symbol": f"{op_type}:{length_bucket(length)}",
                "target_start_status": "derived_from_prior_lengths",
                "op_type_status": "external_control_stream",
                "length_status": "external_control_stream",
                "row0_origin_status": "unchanged_exogenous",
                "translation_or_plaintext_status": "NONE",
                "compression_bound_status": "unchanged_8154_676268",
                "validated_clues": [],
                "external_fields": ["op_type", "length"],
                "target_text_dependency": [],
            }
            if op_type == "literal":
                payload = op["payload"]
                row.update(
                    {
                        "literal_payload": payload,
                        "literal_tape_start": literal_tape_pos,
                        "literal_tape_end": literal_tape_pos + len(payload),
                        "literal_payload_bits": len(payload) * DIGIT_BITS,
                        "literal_payload_status": "external_innovation_tape",
                        "copy_source_raw": None,
                        "source_address_bits": 0.0,
                        "same_length_chunk_hint_bits": 0.0,
                        "copy_hint_rank_bits": 0.0,
                        "copy_hint_rank": None,
                        "copy_hint_rank_bucket": None,
                    }
                )
                row["external_fields"].append("literal_payload")
                row["validated_clues"].append(
                    "innovation_tape_structure_clue_not_generator"
                )
                row["target_text_dependency"].append("literal_payload_is_target_digits")
                literal_tape_pos += len(payload)
            elif op_type == "copy":
                source = int(op["source"])
                available = emitted_base + target[:target_start]
                payload = target[target_start : target_start + length]
                if available[source : source + length] != payload:
                    raise RuntimeError(f"copy source mismatch book={book} op={op_index}")
                hint = copy_hint_metrics(available, payload)
                row.update(
                    {
                        "literal_payload": None,
                        "literal_tape_start": None,
                        "literal_tape_end": None,
                        "literal_payload_bits": 0.0,
                        "literal_payload_status": None,
                        "copy_source_raw": source,
                        "source_address_bits": math.log2(
                            max(1, len(available) - length + 1)
                        ),
                        **hint,
                        "copy_hint_status": "external_copy_control_stream",
                    }
                )
                row["external_fields"].extend(["copy_hint_rank"])
                row["validated_clues"].append("copy_hint_lower_bound_promoted")
                row["validated_clues"].append("copy_hint_simple_structure_rejected")
                row["target_text_dependency"].append(
                    "copy_hint_rank_computed_against_canonical_target_payload"
                )
            else:
                raise RuntimeError(op_type)
            rows.append(row)
            running_start += length
            global_op_index += 1
    summary = {
        "books": len(copy_ledger["canonical_ops_by_book"]),
        "ops": len(rows),
        "literal_ops": sum(1 for row in rows if row["op_type"] == "literal"),
        "copy_ops": sum(1 for row in rows if row["op_type"] == "copy"),
        "literal_digits": sum(row["length"] for row in rows if row["op_type"] == "literal"),
        "copy_digits": sum(row["length"] for row in rows if row["op_type"] == "copy"),
        "literal_payload_bits": sum(row["literal_payload_bits"] for row in rows),
        "source_address_bits": sum(row["source_address_bits"] for row in rows),
        "same_length_chunk_hint_bits": sum(
            row["same_length_chunk_hint_bits"] for row in rows
        ),
        "copy_hint_rank_bits": sum(row["copy_hint_rank_bits"] for row in rows),
        "unique_type_length_symbols": len({row["type_length_symbol"] for row in rows}),
        "literal_tape_digits": literal_tape_pos,
        "target_start_derived_ops": sum(
            1 for row in rows if row["target_start_status"] == "derived_from_prior_lengths"
        ),
    }
    return {
        "schema": "unified_residual_control_ledger_v1",
        "scope": "analysis_only_unified_external_program_ledger",
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "copy_source_ledger": rel(COPY_SOURCE_LEDGER),
            "copy_hint_stream_lower_bound": rel(COPY_HINT_LOWER_BOUND),
            "copy_hint_stream_structure_gate": rel(COPY_HINT_STRUCTURE),
        },
        "ledger_rows": rows,
        "summary": summary,
        "classification": "unified_residual_control_ledger_built",
        "decision": {
            "promotes_generator": False,
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
            "compression_bound_status": "unchanged_8154_676268",
        },
        "case_reopened": False,
        "plaintext_claim": False,
        "translation_delta": "NONE",
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Unified Residual Control Ledger",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Summary",
        "",
        f"- Books covered: `{s['books']}` derived books.",
        f"- Ops: `{s['ops']}` (`{s['copy_ops']}` copy, `{s['literal_ops']}` literal).",
        f"- Target starts derived from prior lengths: `{s['target_start_derived_ops']}/{s['ops']}`.",
        f"- Literal tape digits/bits: `{s['literal_tape_digits']}` / `{s['literal_payload_bits']:.3f}`.",
        f"- Copy digits: `{s['copy_digits']}`.",
        f"- Source-address bits: `{s['source_address_bits']:.3f}`.",
        f"- Same-length chunk hint bits: `{s['same_length_chunk_hint_bits']:.3f}`.",
        f"- Rank-coded copy hint bits: `{s['copy_hint_rank_bits']:.3f}`.",
        f"- Unique type:length symbols: `{s['unique_type_length_symbols']}`.",
        "",
        "## Field Status",
        "",
        "- `target_start`: derived if the prior operation lengths are known.",
        "- `op_type`: external control stream in this ledger.",
        "- `length`: external control stream in this ledger.",
        "- `literal_payload`: external innovation tape.",
        "- `copy_source_raw`: replaced analytically by a paid same-length copy hint where length is granted.",
        "- `copy_hint_rank`: external copy-control stream; lower bound promoted, simple rank-bucket structure rejected.",
        "- `row0`: unchanged exogenous.",
        "",
        "## Sample Rows",
        "",
        "| Book | Op | Start | Type | Len | External Fields | Clues | Target Dependency |",
        "| ---: | ---: | ---: | --- | ---: | --- | --- | --- |",
    ]
    for row in result["ledger_rows"][:12]:
        lines.append(
            f"| `{row['book']}` | `{row['op_index']}` | `{row['target_start']}` | "
            f"`{row['op_type']}` | `{row['length']}` | "
            f"`{','.join(row['external_fields'])}` | "
            f"`{','.join(row['validated_clues'])}` | "
            f"`{','.join(row['target_text_dependency'])}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- This is a ledger of residual external program fields, not a promoted generator.",
            "- It is the substrate for residual-cost, coupling, and holdout tests in this front.",
            "- No plaintext, translation, row0-origin claim, or case reopening is introduced.",
            "",
        ]
    )
    (TEST_RESULTS / f"{OUT_STEM}.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    result = make_ledger()
    (TEST_RESULTS / f"{OUT_STEM}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    write_markdown(result)
    print(json.dumps({"classification": result["classification"], "summary": result["summary"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
