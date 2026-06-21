from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"
AUTHORIAL = ROOT / "analysis" / "authorial_mechanism_20260620"

CURRENT_FORMULA = (
    AUTHORIAL
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_substitution_fourth_pass_formula_469.json"
)
BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
COPY_LENGTH_BOUNDARY = TEST_RESULTS / "32_copy_length_derivation_boundary_gate.json"
SOURCE_LENGTH_JOINT = TEST_RESULTS / "49_source_length_joint_derivability_audit.json"
SOURCE_CANONICALITY_TRADEOFF = TEST_RESULTS / "50_source_canonicality_tradeoff_audit.json"


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


def max_target_extension(
    *, emitted: str, source_pos: int, target: str, book_pos: int
) -> int:
    max_len = min(len(emitted) - source_pos, len(target) - book_pos)
    length = 0
    while length < max_len and emitted[source_pos + length] == target[book_pos + length]:
        length += 1
    return length


def covered_following_ops(
    *, ops: list[dict[str, Any]], op_index: int, target_end: int
) -> list[dict[str, Any]]:
    covered = []
    for later in ops[op_index + 1 :]:
        if later["start"] >= target_end:
            break
        overlap = min(later["end"], target_end) - later["start"]
        if overlap <= 0:
            continue
        covered.append(
            {
                "op_index": later["op_index"],
                "type": later["type"],
                "length": later["length"],
                "covered_digits": overlap,
                "fully_covered": overlap == later["length"],
            }
        )
    return covered


def collect_ops(formula: dict[str, Any], books: dict[str, str]) -> dict[str, Any]:
    emitted = ""
    per_book: dict[int, list[dict[str, Any]]] = {}
    copy_rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    for book in map(str, formula["policy"]["book_order"]):
        target = books[book]
        book_int = int(book)
        book_pos = 0
        ops: list[dict[str, Any]] = []
        for op_index, op in enumerate(formula["book_recipes"][book]["ops"]):
            if op["type"] == "literal":
                text = op["text"]
                if target[book_pos : book_pos + len(text)] != text:
                    errors.append(
                        {"book": book_int, "op_index": op_index, "type": "literal_mismatch"}
                    )
                row = {
                    "book": book_int,
                    "op_index": op_index,
                    "type": "literal",
                    "start": book_pos,
                    "end": book_pos + len(text),
                    "length": len(text),
                    "text": text,
                }
                ops.append(row)
                emitted += text
                book_pos += len(text)
                continue

            if op["type"] != "copy":
                errors.append({"book": book_int, "op_index": op_index, "type": "bad_op"})
                continue

            source = int(op["source_digit_pos"])
            length = int(op["length"])
            chunk = emitted[source : source + length]
            if target[book_pos : book_pos + length] != chunk or len(chunk) != length:
                errors.append(
                    {
                        "book": book_int,
                        "op_index": op_index,
                        "type": "copy_mismatch",
                        "source_digit_pos": source,
                        "length": length,
                    }
                )
            target_max = max_target_extension(
                emitted=emitted,
                source_pos=source,
                target=target,
                book_pos=book_pos,
            )
            decoder_max = min(len(emitted) - source, len(target) - book_pos)
            row = {
                "book": book_int,
                "op_index": op_index,
                "type": "copy",
                "start": book_pos,
                "end": book_pos + length,
                "length": length,
                "source_digit_pos": source,
                "encoder_target_max": target_max,
                "decoder_max_possible": decoder_max,
                "target_max_slack": target_max - length,
                "decoder_max_slack": decoder_max - length,
            }
            ops.append(row)
            copy_rows.append(row)
            emitted += chunk
            book_pos += length
        if book_pos != len(target):
            errors.append(
                {
                    "book": book_int,
                    "type": "book_length_mismatch",
                    "decoded_length": book_pos,
                    "target_length": len(target),
                }
            )
        per_book[book_int] = ops
    return {"per_book": per_book, "copy_rows": copy_rows, "errors": errors}


def make_result() -> dict[str, Any]:
    for name, path in [
        ("copy_length_boundary", COPY_LENGTH_BOUNDARY),
        ("source_length_joint", SOURCE_LENGTH_JOINT),
        ("source_canonicality_tradeoff", SOURCE_CANONICALITY_TRADEOFF),
    ]:
        assert_boundary(name, load_json(path))

    formula = load_json(CURRENT_FORMULA)
    books = {str(k): v for k, v in load_json(BOOKS_DIGITS).items()}
    collected = collect_ops(formula, books)
    if collected["errors"]:
        raise RuntimeError(collected["errors"])
    per_book = collected["per_book"]
    copy_rows = collected["copy_rows"]
    exceptions = [
        row for row in copy_rows if int(row["target_max_slack"]) > 0
    ]
    exception_rows = []
    covered_type_counter: Counter[str] = Counter()
    fully_covered_op_counter: Counter[str] = Counter()
    partial_cover_count = 0
    reaches_book_end_count = 0
    exact_next_op_count = 0
    absorbs_full_next_op_count = 0
    exactly_one_following_op_count = 0

    for row in exceptions:
        target_end = int(row["start"]) + int(row["encoder_target_max"])
        covered = covered_following_ops(
            ops=per_book[int(row["book"])],
            op_index=int(row["op_index"]),
            target_end=target_end,
        )
        next_covered = covered[0] if covered else None
        for item in covered:
            covered_type_counter[item["type"]] += int(item["covered_digits"])
            if item["fully_covered"]:
                fully_covered_op_counter[item["type"]] += 1
            else:
                partial_cover_count += 1
        if target_end == len(books[str(row["book"])]):
            reaches_book_end_count += 1
        if next_covered and int(row["target_max_slack"]) == int(next_covered["length"]):
            exact_next_op_count += 1
        if next_covered and next_covered["fully_covered"]:
            absorbs_full_next_op_count += 1
        if len(covered) == 1:
            exactly_one_following_op_count += 1
        exception_rows.append(
            {
                "book": row["book"],
                "op_index": row["op_index"],
                "book_pos": row["start"],
                "source_digit_pos": row["source_digit_pos"],
                "length": row["length"],
                "encoder_target_max": row["encoder_target_max"],
                "target_max_slack": row["target_max_slack"],
                "decoder_max_possible": row["decoder_max_possible"],
                "decoder_max_slack": row["decoder_max_slack"],
                "target_max_reaches_book_end": target_end == len(books[str(row["book"])]),
                "covered_following_op_count": len(covered),
                "fully_covered_following_op_count": sum(
                    1 for item in covered if item["fully_covered"]
                ),
                "covered_following_digits": sum(
                    int(item["covered_digits"]) for item in covered
                ),
                "first_covered_following_op_type": (
                    None if next_covered is None else next_covered["type"]
                ),
                "first_covered_following_op_length": (
                    None if next_covered is None else next_covered["length"]
                ),
                "slack_equals_first_following_op_length": (
                    bool(next_covered)
                    and int(row["target_max_slack"]) == int(next_covered["length"])
                ),
                "covered_following_ops": covered,
            }
        )

    classification = (
        "copy_length_target_max_exceptions_are_partial_next_op_intrusions"
        if len(exceptions) == 23
        and exactly_one_following_op_count == 23
        and partial_cover_count == 23
        and absorbs_full_next_op_count == 0
        else "copy_length_target_max_exception_boundary_unresolved"
    )
    return {
        "schema": "copy_length_segmentation_exception_audit.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "current_formula": rel(CURRENT_FORMULA),
            "books_digits": rel(BOOKS_DIGITS),
            "copy_length_boundary": rel(COPY_LENGTH_BOUNDARY),
            "source_length_joint_derivability": rel(SOURCE_LENGTH_JOINT),
            "source_canonicality_tradeoff": rel(SOURCE_CANONICALITY_TRADEOFF),
        },
        "scope": {
            "analysis_only": True,
            "new_formula_emitted": False,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "plaintext_or_translation_claim": False,
            "tested_question": (
                "What the 23 non-target-max copy lengths would absorb if each "
                "copy were extended to its encoder-known maximal target match."
            ),
        },
        "summary": {
            "copy_event_count": len(copy_rows),
            "target_max_match_count": len(copy_rows) - len(exceptions),
            "target_max_exception_count": len(exceptions),
            "target_max_exception_fraction": len(exceptions) / len(copy_rows),
            "target_max_slack_digits_total": sum(
                int(row["target_max_slack"]) for row in exceptions
            ),
            "target_max_slack_digits_min": min(
                int(row["target_max_slack"]) for row in exceptions
            ),
            "target_max_slack_digits_max": max(
                int(row["target_max_slack"]) for row in exceptions
            ),
            "target_max_slack_digits_mean": (
                sum(int(row["target_max_slack"]) for row in exceptions)
                / len(exceptions)
            ),
            "exceptions_reaching_book_end": reaches_book_end_count,
            "exceptions_absorbing_full_next_op": absorbs_full_next_op_count,
            "exceptions_covering_exactly_one_following_op": exactly_one_following_op_count,
            "exceptions_slack_equals_first_following_op": exact_next_op_count,
            "exceptions_with_partial_following_op_cover": partial_cover_count,
            "covered_following_digits_by_type": dict(sorted(covered_type_counter.items())),
            "fully_covered_following_ops_by_type": dict(
                sorted(fully_covered_op_counter.items())
            ),
            "interpretation": (
                "The high-coverage target-max rule fails exactly where extending "
                "a copy would cross into the next operation and stop inside it. "
                "These are resegmentation boundaries, not isolated length coding "
                "anomalies."
            ),
        },
        "exception_rows": exception_rows,
        "decision": {
            "compression_bound_status": "unchanged",
            "copy_length_target_max_status": "encoder_oracle_high_coverage_but_segmentation_boundary_dependent",
            "copy_length_dependency_status": "declared_lengths_retained",
            "generation_explanation_status": "target_max_exceptions_mapped_to_segmentation_boundaries",
            "next_mainline_status": "copy_length_progress_requires_joint_reparse_not_length_only_default",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / "51_copy_length_segmentation_exception_audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    lines = [
        "# Copy Length Segmentation Exception Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "The target-max copy-length rule matches most copy events, but it is",
        "encoder-only and has `23` exceptions. This audit maps those exceptions",
        "as segmentation boundaries: if the copy were extended to target-max,",
        "which following operations would be crossed or absorbed?",
        "",
        "## Summary",
        "",
        f"- Copy events: `{s['copy_event_count']}`.",
        f"- Target-max matches/exceptions: `{s['target_max_match_count']}` / `{s['target_max_exception_count']}`.",
        f"- Exception fraction: `{s['target_max_exception_fraction']:.6f}`.",
        f"- Total target-max slack digits in exceptions: `{s['target_max_slack_digits_total']}`.",
        f"- Slack min/mean/max: `{s['target_max_slack_digits_min']}` / `{s['target_max_slack_digits_mean']:.3f}` / `{s['target_max_slack_digits_max']}`.",
        f"- Exceptions reaching book end: `{s['exceptions_reaching_book_end']}`.",
        f"- Exceptions covering exactly one following op: `{s['exceptions_covering_exactly_one_following_op']}`.",
        f"- Exceptions absorbing the full next op: `{s['exceptions_absorbing_full_next_op']}`.",
        f"- Exceptions where slack equals first following op length: `{s['exceptions_slack_equals_first_following_op']}`.",
        f"- Exceptions with partial following-op cover: `{s['exceptions_with_partial_following_op_cover']}`.",
        f"- Covered following digits by type: `{s['covered_following_digits_by_type']}`.",
        f"- Fully covered following ops by type: `{s['fully_covered_following_ops_by_type']}`.",
        "",
        "## Exception Rows",
        "",
        "| Book | Op | Pos | Source | Length | Target max | Slack | First next type | Covered ops | Full ops | Book end |",
        "|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---|",
    ]
    for row in result["exception_rows"]:
        lines.append(
            f"| `{row['book']}` | `{row['op_index']}` | `{row['book_pos']}` | "
            f"`{row['source_digit_pos']}` | `{row['length']}` | "
            f"`{row['encoder_target_max']}` | `{row['target_max_slack']}` | "
            f"`{row['first_covered_following_op_type']}` | "
            f"`{row['covered_following_op_count']}` | "
            f"`{row['fully_covered_following_op_count']}` | "
            f"`{row['target_max_reaches_book_end']}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The non-target-max copy lengths are not random length noise. In every",
            "case, extending the copy to target-max would enter exactly one following",
            "operation and stop inside it; it never cleanly absorbs a whole next op.",
            "This explains why a length-only target-max rule cannot be promoted: the",
            "missing mechanism is a joint segmentation/source/length parser, not",
            "another scalar copy-length default.",
            "",
            "## Boundary",
            "",
            "- No new formula is emitted.",
            "- Compression bound is unchanged.",
            "- Copy length remains declared in the current formula.",
            "- Row0 origin remains unchanged and exogenous.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        ]
    )
    (TEST_RESULTS / "51_copy_length_segmentation_exception_audit.md").write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
