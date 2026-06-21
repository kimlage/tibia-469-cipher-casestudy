from __future__ import annotations

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
RESULT_152 = REPORTS / "152_cross_op_near_tie_decomposition.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def available_before_position(
    formula: dict[str, Any],
    books: dict[str, str],
    *,
    book: int,
    pos: int,
) -> str:
    available = "".join(books[str(index)] for index in range(book))
    book_pos = 0
    for op in formula["book_recipes"][str(book)]["ops"]:
        if book_pos >= pos:
            break
        if "text" in op:
            text = op["text"]
            take = min(len(text), pos - book_pos)
            available += text[:take]
            book_pos += take
            continue
        source = int(op["source_digit_pos"])
        length = min(int(op["length"]), pos - book_pos)
        available += available[source : source + length]
        book_pos += length
    if book_pos != pos:
        raise RuntimeError({"book": book, "book_pos": book_pos, "expected": pos})
    return available


def copy_candidates(
    available: str,
    target: str,
    *,
    pos: int,
    min_len: int,
) -> list[dict[str, int]]:
    if len(target) - pos < min_len:
        return []
    needle = target[pos : pos + min_len]
    out = []
    for source in range(max(0, len(available) - min_len + 1)):
        if available[source : source + min_len] != needle:
            continue
        length = min_len
        while (
            pos + length < len(target)
            and source + length < len(available)
            and target[pos + length] == available[source + length]
        ):
            length += 1
        out.append({"source_digit_pos": source, "max_length": length})
    return out


def make_result() -> dict[str, Any]:
    formula = load_json(SOURCE_FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    near_tie = load_json(RESULT_152)
    candidate = near_tie["candidate"]
    deltas = near_tie["component_deltas"]
    total_delta = float(near_tie["delta_checks"]["total_delta_bits"])
    source_delta = float(deltas["copy_source_default_exception_bits"])
    length_delta = float(deltas["copy_length_default_exception_bits"])
    non_source_delta = total_delta - source_delta
    non_copy_delta = total_delta - source_delta - length_delta
    break_even_source_delta = -non_source_delta
    available = available_before_position(
        formula,
        books,
        book=int(candidate["book"]),
        pos=int(candidate["book_pos"]),
    )
    candidates = copy_candidates(
        available,
        books[str(candidate["book"])],
        pos=int(candidate["book_pos"]),
        min_len=int(formula["policy"]["min_len"]),
    )
    full_length_sources = [
        row
        for row in candidates
        if int(row["max_length"]) >= int(candidate["copy_length"])
    ]
    selected_is_earliest_full_length = (
        int(candidate["source_digit_pos"])
        == min(row["source_digit_pos"] for row in full_length_sources)
    )
    no_source_oracle_delta = total_delta - source_delta
    no_source_no_length_oracle_delta = total_delta - source_delta - length_delta
    classification = "cross_op_source_break_even_blocks_promotion"
    return {
        "schema": "cross_op_source_break_even_audit.v1",
        "test": "153_cross_op_source_break_even_audit",
        "classification": classification,
        "translation_delta": "NONE",
        "plaintext_claim": False,
        "case_reopened": False,
        "source_formula": rel(SOURCE_FORMULA),
        "source_candidate_audit": rel(RESULT_152),
        "candidate": candidate,
        "component_deltas": deltas,
        "source_candidates_at_position": {
            "candidate_count": len(candidates),
            "full_length_source_count": len(full_length_sources),
            "full_length_sources": full_length_sources,
            "selected_source_is_earliest_full_length": selected_is_earliest_full_length,
        },
        "break_even": {
            "active_total_delta_bits": total_delta,
            "active_copy_source_delta_bits": source_delta,
            "non_source_delta_bits": non_source_delta,
            "break_even_copy_source_delta_bits": break_even_source_delta,
            "source_delta_margin_over_break_even_bits": source_delta - break_even_source_delta,
            "no_source_oracle_delta_bits": no_source_oracle_delta,
            "no_source_no_length_oracle_delta_bits": no_source_no_length_oracle_delta,
            "copy_length_delta_bits": length_delta,
            "non_copy_delta_bits": non_copy_delta,
        },
        "decision": {
            "compression_bound_changed": False,
            "source_free_oracle_promoted": False,
            "candidate_promoted": False,
            "row0_origin_changed": False,
            "semantic_delta": "NONE",
        },
    }


def render_markdown(result: dict[str, Any]) -> str:
    b = result["break_even"]
    source = result["source_candidates_at_position"]
    candidate = result["candidate"]
    lines = [
        "# 153. Cross-Op Source Break-Even Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Audit 152 showed that the best cross-op literal repair loses by only",
        "`0.027` bits, mostly because of copy-source cost. This audit quantifies",
        "the break-even source cost and checks whether the selected source is an",
        "ordinary candidate or an earliest full-length occurrence.",
        "",
        "## Candidate Source Context",
        "",
        f"- Book/op/pos: `{candidate['book']}` / `{candidate['op_index']}` / `{candidate['book_pos']}`",
        f"- Source/copy length: `{candidate['source_digit_pos']}` / `{candidate['copy_length']}`",
        f"- Candidate sources at position: `{source['candidate_count']}`",
        f"- Full-length sources for this copy length: `{source['full_length_source_count']}`",
        f"- Selected source is earliest full-length source: `{source['selected_source_is_earliest_full_length']}`",
        "",
        "Full-length sources:",
        "",
        "| Source | Max length |",
        "|---:|---:|",
    ]
    for row in source["full_length_sources"]:
        lines.append(f"| `{row['source_digit_pos']}` | `{row['max_length']}` |")
    lines.extend(
        [
            "",
            "## Break-Even Ledger",
            "",
            f"- Active delta: `{b['active_total_delta_bits']:.6f}` bits",
            f"- Active copy-source delta: `{b['active_copy_source_delta_bits']:.6f}` bits",
            f"- Non-source delta: `{b['non_source_delta_bits']:.6f}` bits",
            f"- Break-even copy-source delta: `{b['break_even_copy_source_delta_bits']:.6f}` bits",
            f"- Source margin over break-even: `{b['source_delta_margin_over_break_even_bits']:.6f}` bits",
            f"- No-source oracle delta: `{b['no_source_oracle_delta_bits']:.6f}` bits",
            f"- No-source/no-length oracle delta: `{b['no_source_no_length_oracle_delta_bits']:.6f}` bits",
            "",
            "## Interpretation",
            "",
            "The candidate would improve under a non-decodable source-free oracle,",
            "but the active ledger must still identify the copied source. The",
            "selected source is the earliest full-length occurrence, which is a",
            "useful encoder-side clue, but not a decoder-side derivation of the",
            "copied text. The real active source cost is only `0.027` bits above",
            "break-even, so this is a tight mechanical frontier rather than a",
            "promotable formula.",
            "",
            "## Decision",
            "",
            "- Compression bound unchanged.",
            "- Source-free oracle not promoted.",
            "- Candidate not promoted.",
            "- Row0 origin, plaintext, and semantic status unchanged.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    result = make_result()
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "153_cross_op_source_break_even_audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / "153_cross_op_source_break_even_audit.md").write_text(
        render_markdown(result),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
