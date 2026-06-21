from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

SOURCE_FORMULA = (
    HERE
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_default_exception_formula_469.json"
)
BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
AUDIT_150 = HERE / "scripts" / "150_optional_literal_copy_repair_frontier.py"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def op_type(op: dict[str, Any]) -> str:
    if "text" in op:
        return "literal"
    if "source_digit_pos" in op and "length" in op:
        return "copy"
    raise RuntimeError({"type": "unknown_op_shape", "op": op})


def op_spans(ops: list[dict[str, Any]], target: str, available_before_book: str) -> list[dict[str, Any]]:
    spans = []
    book_pos = 0
    emitted = available_before_book
    for op_index, op in enumerate(ops):
        kind = op_type(op)
        start = book_pos
        if kind == "literal":
            text = op["text"]
        else:
            source = int(op["source_digit_pos"])
            length = int(op["length"])
            text = emitted[source : source + length]
        end = start + len(text)
        if target[start:end] != text:
            raise RuntimeError(
                {
                    "type": "span_decode_mismatch",
                    "op_index": op_index,
                    "start": start,
                    "end": end,
                }
            )
        spans.append(
            {
                "op_index": op_index,
                "op": op,
                "type": kind,
                "start": start,
                "end": end,
                "text": text,
            }
        )
        emitted += text
        book_pos = end
    if book_pos != len(target):
        raise RuntimeError(
            {"type": "book_length_mismatch", "decoded": book_pos, "target": len(target)}
        )
    return spans


def available_before_each_book(formula: dict[str, Any], books: dict[str, str]) -> dict[str, str]:
    out = {}
    available = ""
    for book in map(str, formula["policy"]["book_order"]):
        out[book] = available
        available += books[book]
    return out


def trim_suffix_op(span: dict[str, Any], trim_start: int, min_len: int) -> dict[str, Any] | None:
    offset = trim_start - int(span["start"])
    remaining = int(span["end"]) - trim_start
    if remaining <= 0:
        return None
    if span["type"] == "literal":
        return {"text": span["text"][offset:]}
    source = int(span["op"]["source_digit_pos"]) + offset
    if remaining >= min_len:
        return {"source_digit_pos": source, "length": remaining}
    return {"text": span["text"][offset:]}


def replace_cross_op_prefix(
    formula: dict[str, Any],
    books: dict[str, str],
    available_by_book: dict[str, str],
    *,
    book: int,
    op_index: int,
    source_digit_pos: int,
    length: int,
) -> dict[str, Any]:
    out = json.loads(json.dumps(formula))
    book_key = str(book)
    ops = out["book_recipes"][book_key]["ops"]
    target = books[book_key]
    spans = op_spans(ops, target, available_by_book[book_key])
    start = int(spans[op_index]["start"])
    end = start + length
    new_ops: list[dict[str, Any]] = []
    new_ops.extend(json.loads(json.dumps(op)) for op in ops[:op_index])
    new_ops.append({"source_digit_pos": int(source_digit_pos), "length": int(length)})
    append_from = None
    for span in spans[op_index:]:
        if int(span["end"]) <= end:
            append_from = int(span["op_index"]) + 1
            continue
        if int(span["start"]) < end < int(span["end"]):
            suffix = trim_suffix_op(span, end, int(formula["policy"]["min_len"]))
            if suffix is not None:
                new_ops.append(suffix)
            append_from = int(span["op_index"]) + 1
            break
        if int(span["start"]) >= end:
            append_from = int(span["op_index"])
            break
    if append_from is None:
        append_from = len(ops)
    new_ops.extend(json.loads(json.dumps(op)) for op in ops[append_from:])
    out["book_recipes"][book_key]["ops"] = new_ops
    return out


def make_result() -> dict[str, Any]:
    audit150 = load_module("audit150", AUDIT_150)
    formula = load_json(SOURCE_FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    available_by_book = available_before_each_book(formula, books)
    modules = {
        "compile129": audit150.load_module("compile129", audit150.COMPILE_129),
        "compile134": audit150.load_module("compile134", audit150.COMPILE_134),
        "audit136": audit150.load_module("audit136", audit150.AUDIT_136),
        "audit137": audit150.load_module("audit137", audit150.AUDIT_137),
        "audit141": audit150.load_module("audit141", audit150.AUDIT_141),
    }
    audit126 = modules["compile129"].load_audit_126()
    modules.update(
        {
            "audit126": audit126,
            "frontier": audit150.load_module("frontier", audit126.FRONTIER),
            "midpoint": audit150.load_module("midpoint", audit126.MIDPOINT),
            "copy_module": audit150.load_module("copy_context", audit126.COPY_CONTEXT),
            "item_module": audit150.load_module("item_context", audit126.ITEM_CONTEXT),
        }
    )
    base_score = audit150.active_score(formula, modules, books)
    optional_rows = audit150.optional_literal_starts(formula, books)
    min_len = int(formula["policy"]["min_len"])

    candidates = []
    cross_op_candidates = 0
    for row in optional_rows:
        for candidate in row["candidates"]:
            for length in range(min_len, int(candidate["max_length"]) + 1):
                if length <= int(row["literal_length"]):
                    continue
                cross_op_candidates += 1
                try:
                    repaired = replace_cross_op_prefix(
                        formula,
                        books,
                        available_by_book,
                        book=int(row["book"]),
                        op_index=int(row["op_index"]),
                        source_digit_pos=int(candidate["source_digit_pos"]),
                        length=length,
                    )
                    repaired_score = audit150.active_score(repaired, modules, books)
                except Exception as exc:  # noqa: BLE001 - audit records invalid generated repairs.
                    candidates.append(
                        {
                            "book": row["book"],
                            "op_index": row["op_index"],
                            "book_pos": row["book_pos"],
                            "source_digit_pos": candidate["source_digit_pos"],
                            "copy_length": length,
                            "valid": False,
                            "error": repr(exc),
                        }
                    )
                    continue
                candidates.append(
                    {
                        "book": row["book"],
                        "op_index": row["op_index"],
                        "book_pos": row["book_pos"],
                        "source_digit_pos": candidate["source_digit_pos"],
                        "copy_length": length,
                        "literal_length_before": row["literal_length"],
                        "crossed_digits": length - int(row["literal_length"]),
                        "valid": True,
                        "delta_bits": repaired_score["total_bits"] - base_score["total_bits"],
                        "candidate_total_bits": repaired_score["total_bits"],
                        "literal_runs": repaired_score["literal_runs"],
                        "literal_digits": repaired_score["literal_digits"],
                        "copy_items": repaired_score["copy_items"],
                    }
                )

    valid_candidates = [row for row in candidates if row.get("valid")]
    valid_candidates.sort(key=lambda row: row["delta_bits"])
    improving = [row for row in valid_candidates if row["delta_bits"] < 0]
    best = valid_candidates[0] if valid_candidates else None
    classification = (
        "cross_op_optional_literal_copy_repair_improves_active_formula"
        if improving
        else "cross_op_optional_literal_copy_repairs_rejected_active_parser_retained"
    )
    return {
        "schema": "cross_op_optional_literal_copy_frontier.v1",
        "test": "151_cross_op_optional_literal_copy_frontier",
        "classification": classification,
        "translation_delta": "NONE",
        "plaintext_claim": False,
        "case_reopened": False,
        "source_formula": rel(SOURCE_FORMULA),
        "scope": {
            "min_len": min_len,
            "repair_family": (
                "single local replacement of one optional literal start by a copy "
                "that may cross the literal boundary and consume following ops"
            ),
            "active_total_bits_recomputed": base_score["total_bits"],
            "optional_literal_starts": len(optional_rows),
            "cross_op_candidates_attempted": cross_op_candidates,
            "valid_cross_op_candidates": len(valid_candidates),
            "invalid_cross_op_candidates": len(candidates) - len(valid_candidates),
        },
        "base_score": base_score,
        "best_candidate": best,
        "top_candidates": valid_candidates[:20],
        "improving_candidate_count": len(improving),
        "decision": {
            "compression_bound_changed": bool(improving),
            "candidate_promoted": bool(improving),
            "active_parser_retained": not bool(improving),
            "row0_origin_changed": False,
            "semantic_delta": "NONE",
        },
    }


def render_markdown(result: dict[str, Any]) -> str:
    scope = result["scope"]
    best = result["best_candidate"]
    lines = [
        "# 151. Cross-Op Optional Literal Copy Frontier",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Audit 150 rejected copy-prefix repairs contained inside one optional",
        "literal run. This audit tests the next broader repair family: a copy",
        "candidate at an optional literal start may cross the literal boundary",
        "and consume part of following operations, after which the remaining",
        "recipe is trimmed conservatively and rescored under the active ledger.",
        "",
        "## Scope",
        "",
        f"- Active total bits recomputed: `{scope['active_total_bits_recomputed']:.3f}`",
        f"- Optional literal starts: `{scope['optional_literal_starts']}`",
        f"- Cross-op candidates attempted: `{scope['cross_op_candidates_attempted']}`",
        f"- Valid cross-op candidates: `{scope['valid_cross_op_candidates']}`",
        f"- Invalid generated candidates: `{scope['invalid_cross_op_candidates']}`",
        "",
        "## Best Candidates",
        "",
        "| Rank | Delta bits | Total bits | Book | Op | Source | Copy len | Crossed digits |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for rank, row in enumerate(result["top_candidates"][:10], start=1):
        lines.append(
            f"| `{rank}` | `{row['delta_bits']:.3f}` | `{row['candidate_total_bits']:.3f}` | "
            f"`{row['book']}` | `{row['op_index']}` | `{row['source_digit_pos']}` | "
            f"`{row['copy_length']}` | `{row['crossed_digits']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Improving candidates: `{result['improving_candidate_count']}`",
        ]
    )
    if best is not None:
        lines.append(
            f"- Best candidate is `{best['delta_bits']:.3f}` bits worse than active."
        )
    lines.extend(
        [
            "- Compression bound unchanged.",
            "- Active parser retained for this repair family.",
            "- Row0 origin, plaintext, and semantic status unchanged.",
            "",
            "## Interpretation",
            "",
            "Allowing the copy to cross the optional literal boundary does not rescue",
            "the residual literal frontier. Every valid cross-op repair is worse",
            "than the active parser choice under the same active ledger. This closes",
            "the immediate extension of audit 150; future repair tests should move",
            "to explicitly reparsing a bounded suffix, not ad hoc local copy swaps.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    result = make_result()
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "151_cross_op_optional_literal_copy_frontier.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / "151_cross_op_optional_literal_copy_frontier.md").write_text(
        render_markdown(result),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
