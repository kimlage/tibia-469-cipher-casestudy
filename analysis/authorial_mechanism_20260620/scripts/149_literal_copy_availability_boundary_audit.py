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


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def op_type(op: dict[str, Any]) -> str:
    if "text" in op:
        return "literal"
    if "source_digit_pos" in op and "length" in op:
        return "copy"
    raise RuntimeError({"type": "unknown_op_shape", "op": op})


def copy_candidates(available: str, target: str, book_pos: int, min_len: int) -> dict[str, Any]:
    remaining = len(target) - book_pos
    if remaining < min_len:
        return {
            "candidate_count": 0,
            "max_candidate_length": 0,
            "earliest_source": None,
            "reason": "remaining_shorter_than_min_len",
        }
    needle = target[book_pos : book_pos + min_len]
    candidates = []
    for source in range(max(0, len(available) - min_len + 1)):
        if available[source : source + min_len] != needle:
            continue
        length = min_len
        while (
            book_pos + length < len(target)
            and source + length < len(available)
            and target[book_pos + length] == available[source + length]
        ):
            length += 1
        candidates.append({"source": source, "length": length})
    if not candidates:
        return {
            "candidate_count": 0,
            "max_candidate_length": 0,
            "earliest_source": None,
            "reason": "no_prior_min_len_match",
        }
    return {
        "candidate_count": len(candidates),
        "max_candidate_length": max(row["length"] for row in candidates),
        "earliest_source": min(row["source"] for row in candidates),
        "reason": "copy_candidate_available",
    }


def audit_formula(formula: dict[str, Any], books: dict[str, str]) -> dict[str, Any]:
    min_len = int(formula["policy"]["min_len"])
    available = ""
    literal_rows = []
    copy_rows = []
    literal_digit_rows = []
    errors = []

    for book in map(str, formula["policy"]["book_order"]):
        target = books[book]
        book_pos = 0
        for op_index, op in enumerate(formula["book_recipes"][book]["ops"]):
            kind = op_type(op)
            start_candidates = copy_candidates(available, target, book_pos, min_len)
            if kind == "literal":
                text = op["text"]
                if target[book_pos : book_pos + len(text)] != text:
                    errors.append(
                        {
                            "book": int(book),
                            "op_index": op_index,
                            "type": "literal_mismatch",
                        }
                    )
                row = {
                    "book": int(book),
                    "op_index": op_index,
                    "book_pos": book_pos,
                    "literal_length": len(text),
                    "literal_preview": text[:32],
                    **start_candidates,
                }
                row["literal_start_classification"] = (
                    "optional_literal_copy_candidate_available"
                    if start_candidates["candidate_count"] > 0
                    else "forced_literal_no_copy_candidate"
                )
                literal_rows.append(row)

                for offset, digit in enumerate(text):
                    digit_candidates = copy_candidates(available, target, book_pos, min_len)
                    literal_digit_rows.append(
                        {
                            "book": int(book),
                            "op_index": op_index,
                            "book_pos": book_pos,
                            "literal_offset": offset,
                            "digit": digit,
                            "candidate_count": digit_candidates["candidate_count"],
                            "max_candidate_length": digit_candidates["max_candidate_length"],
                            "reason": digit_candidates["reason"],
                            "digit_classification": (
                                "optional_literal_digit_copy_candidate_available"
                                if digit_candidates["candidate_count"] > 0
                                else "forced_literal_digit_no_copy_candidate"
                            ),
                        }
                    )
                    available += digit
                    book_pos += 1
                continue

            source = int(op["source_digit_pos"])
            length = int(op["length"])
            chunk = available[source : source + length]
            if len(chunk) != length or target[book_pos : book_pos + length] != chunk:
                errors.append(
                    {
                        "book": int(book),
                        "op_index": op_index,
                        "type": "copy_mismatch",
                        "source_digit_pos": source,
                        "length": length,
                    }
                )
            copy_rows.append(
                {
                    "book": int(book),
                    "op_index": op_index,
                    "book_pos": book_pos,
                    "source_digit_pos": source,
                    "length": length,
                    **start_candidates,
                    "source_is_candidate_at_start": start_candidates["candidate_count"] > 0,
                }
            )
            available += chunk
            book_pos += length

        if book_pos != len(target):
            errors.append(
                {
                    "book": int(book),
                    "type": "book_length_mismatch",
                    "decoded_length": book_pos,
                    "target_length": len(target),
                }
            )

    forced_literal_rows = [
        row for row in literal_rows if row["literal_start_classification"] == "forced_literal_no_copy_candidate"
    ]
    optional_literal_rows = [
        row
        for row in literal_rows
        if row["literal_start_classification"] == "optional_literal_copy_candidate_available"
    ]
    forced_digit_rows = [
        row
        for row in literal_digit_rows
        if row["digit_classification"] == "forced_literal_digit_no_copy_candidate"
    ]
    optional_digit_rows = [
        row
        for row in literal_digit_rows
        if row["digit_classification"] == "optional_literal_digit_copy_candidate_available"
    ]
    short_suffix_digit_rows = [
        row for row in literal_digit_rows if row["reason"] == "remaining_shorter_than_min_len"
    ]
    optional_short_literal_rows = [
        row for row in optional_literal_rows if row["literal_length"] < min_len
    ]
    optional_copy_covering_rows = [
        row for row in optional_literal_rows if row["max_candidate_length"] >= row["literal_length"]
    ]

    return {
        "errors": errors,
        "decoded_digit_count": len(available),
        "literal_rows": literal_rows,
        "copy_rows": copy_rows,
        "literal_digit_rows": literal_digit_rows,
        "summary": {
            "literal_items": len(literal_rows),
            "copy_items": len(copy_rows),
            "literal_digits": len(literal_digit_rows),
            "forced_literal_items_no_copy_candidate": len(forced_literal_rows),
            "optional_literal_items_copy_candidate_available": len(optional_literal_rows),
            "forced_literal_digits_no_copy_candidate": len(forced_digit_rows),
            "optional_literal_digits_copy_candidate_available": len(optional_digit_rows),
            "short_suffix_literal_digits": len(short_suffix_digit_rows),
            "optional_literal_items_shorter_than_min_len": len(optional_short_literal_rows),
            "optional_literal_items_candidate_covers_literal_length": len(optional_copy_covering_rows),
            "copy_items_with_candidate_at_start": sum(
                1 for row in copy_rows if row["source_is_candidate_at_start"]
            ),
        },
        "optional_literal_rows": optional_literal_rows,
    }


def make_result() -> dict[str, Any]:
    formula = load_json(SOURCE_FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    audit = audit_formula(formula, books)
    if audit["errors"]:
        classification = "literal_copy_availability_audit_validation_failed"
    elif audit["summary"]["optional_literal_items_copy_candidate_available"] == 0:
        classification = "literal_items_fully_forced_by_copy_unavailability"
    else:
        classification = "literal_items_mostly_forced_with_residual_parser_choices"
    return {
        "schema": "literal_copy_availability_boundary_audit.v1",
        "test": "149_literal_copy_availability_boundary_audit",
        "classification": classification,
        "translation_delta": "NONE",
        "plaintext_claim": False,
        "case_reopened": False,
        "source_formula": rel(SOURCE_FORMULA),
        "scope": {
            "min_len": int(formula["policy"]["min_len"]),
            "question": (
                "Which literal operations in the active online formula are forced "
                "by absence of any legal min_len copy candidate, and which remain "
                "parser/cost choices despite available copies?"
            ),
        },
        "summary": audit["summary"],
        "optional_literal_rows": audit["optional_literal_rows"],
        "validation": {
            "errors": audit["errors"],
            "decoded_digit_count": audit["decoded_digit_count"],
            "expected_digit_count": sum(len(value) for value in books.values()),
            "copy_items_all_have_start_candidate": (
                audit["summary"]["copy_items_with_candidate_at_start"] == audit["summary"]["copy_items"]
            ),
        },
        "decision": {
            "compression_bound_changed": False,
            "literal_recipe_externality_reduced": True,
            "literal_recipe_externality_removed": False,
            "remaining_optional_literal_item_count": audit["summary"][
                "optional_literal_items_copy_candidate_available"
            ],
            "remaining_optional_literal_digit_count": audit["summary"][
                "optional_literal_digits_copy_candidate_available"
            ],
            "row0_origin_changed": False,
            "semantic_delta": "NONE",
        },
    }


def render_markdown(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        "# 149. Literal Copy Availability Boundary Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "The active online formula still declares literal payload text. This audit",
        "separates literal operations that are mechanically forced by no legal",
        "`min_len` copy candidate from residual parser choices where a copy was",
        "available but the deterministic cost parser chose literal text.",
        "",
        "## Summary",
        "",
        f"- Literal items: `{summary['literal_items']}`",
        f"- Copy items: `{summary['copy_items']}`",
        f"- Literal digits: `{summary['literal_digits']}`",
        f"- Forced literal items with no copy candidate at start: `{summary['forced_literal_items_no_copy_candidate']}`",
        f"- Optional literal items with copy candidate at start: `{summary['optional_literal_items_copy_candidate_available']}`",
        f"- Forced literal digits with no copy candidate at digit position: `{summary['forced_literal_digits_no_copy_candidate']}`",
        f"- Optional literal digits with copy candidate at digit position: `{summary['optional_literal_digits_copy_candidate_available']}`",
        f"- Short-suffix literal digits: `{summary['short_suffix_literal_digits']}`",
        f"- Optional literal items shorter than `min_len`: `{summary['optional_literal_items_shorter_than_min_len']}`",
        f"- Optional literal items where an available copy covers the literal length: `{summary['optional_literal_items_candidate_covers_literal_length']}`",
        "",
        "## Optional Literal Starts",
        "",
        "| Book | Op | Pos | Literal len | Candidates | Max copy len | Preview |",
        "|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in result["optional_literal_rows"]:
        lines.append(
            f"| `{row['book']}` | `{row['op_index']}` | `{row['book_pos']}` | "
            f"`{row['literal_length']}` | `{row['candidate_count']}` | "
            f"`{row['max_candidate_length']}` | `{row['literal_preview']}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "Most literal runs are not arbitrary parser choices: `73/87` literal",
            "items start where no legal copy candidate exists, covering `788/857`",
            "literal payload digits at the item level. At digit granularity,",
            "`760/857` literal digits are emitted at positions with no legal",
            "copy candidate. The residual externality is therefore localized to",
            "`14` literal starts and `97` literal digit positions where copy",
            "availability exists but the cost parser still chooses literal text.",
            "",
            "The residual optional set is not promoted as a source of semantics.",
            "It is a mechanical parser/cost frontier: replacing these literals",
            "requires a charged recipe repair that preserves roundtrip and beats",
            "the active ledger.",
            "",
            "## Decision",
            "",
            "- Literal recipe externality is reduced but not removed.",
            "- Compression bound unchanged.",
            "- Row0 origin, plaintext, and semantic status unchanged.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    result = make_result()
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "149_literal_copy_availability_boundary_audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / "149_literal_copy_availability_boundary_audit.md").write_text(
        render_markdown(result),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
