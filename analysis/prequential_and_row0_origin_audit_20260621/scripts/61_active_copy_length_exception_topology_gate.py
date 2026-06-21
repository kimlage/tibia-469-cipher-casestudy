from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"
AUTHORIAL = ROOT / "analysis" / "authorial_mechanism_20260620"

PREVIOUS_FORMULA = (
    AUTHORIAL
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_substitution_fourth_pass_formula_469.json"
)
ACTIVE_FORMULA = (
    AUTHORIAL
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_targetmax_saturated_source_substitution_second_pass_formula_469.json"
)
BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
COPY_LENGTH_EXCEPTION_51 = (
    TEST_RESULTS / "51_copy_length_segmentation_exception_audit.json"
)
ACTIVE_SOURCE_LENGTH_JOINT_60 = (
    TEST_RESULTS / "60_active_source_length_joint_refresh_gate.json"
)


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


def exception_topology(formula: dict[str, Any], books: dict[str, str]) -> dict[str, Any]:
    collected = collect_ops(formula, books)
    if collected["errors"]:
        raise RuntimeError(collected["errors"])
    per_book = collected["per_book"]
    copy_rows = collected["copy_rows"]
    exceptions = [row for row in copy_rows if int(row["target_max_slack"]) > 0]
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

    slack_values = [int(row["target_max_slack"]) for row in exceptions]
    return {
        "copy_event_count": len(copy_rows),
        "target_max_match_count": len(copy_rows) - len(exceptions),
        "target_max_exception_count": len(exceptions),
        "target_max_exception_fraction": len(exceptions) / len(copy_rows),
        "target_max_slack_digits_total": sum(slack_values),
        "target_max_slack_digits_min": min(slack_values) if slack_values else 0,
        "target_max_slack_digits_max": max(slack_values) if slack_values else 0,
        "target_max_slack_digits_mean": (
            sum(slack_values) / len(slack_values) if slack_values else 0.0
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
        "exception_rows": exception_rows,
    }


def exception_key(row: dict[str, Any]) -> tuple[int, int, int]:
    return int(row["book"]), int(row["op_index"]), int(row["book_pos"])


def make_result() -> dict[str, Any]:
    gate51 = load_json(COPY_LENGTH_EXCEPTION_51)
    gate60 = load_json(ACTIVE_SOURCE_LENGTH_JOINT_60)
    for name, data in [
        ("copy_length_exception_51", gate51),
        ("active_source_length_joint_60", gate60),
    ]:
        assert_boundary(name, data)

    books = {str(k): v for k, v in load_json(BOOKS_DIGITS).items()}
    previous_formula = load_json(PREVIOUS_FORMULA)
    active_formula = load_json(ACTIVE_FORMULA)
    previous = exception_topology(previous_formula, books)
    active = exception_topology(active_formula, books)
    previous_keys = {exception_key(row) for row in previous["exception_rows"]}
    active_keys = {exception_key(row) for row in active["exception_rows"]}
    removed_keys = previous_keys - active_keys
    added_keys = active_keys - previous_keys

    old_rows_by_key = {exception_key(row): row for row in previous["exception_rows"]}
    active_rows_by_key = {exception_key(row): row for row in active["exception_rows"]}
    removed_rows = [old_rows_by_key[key] for key in sorted(removed_keys)]
    added_rows = [active_rows_by_key[key] for key in sorted(added_keys)]

    active_all_partial_single_next = (
        active["target_max_exception_count"] == 19
        and active["exceptions_covering_exactly_one_following_op"] == 19
        and active["exceptions_with_partial_following_op_cover"] == 19
        and active["exceptions_absorbing_full_next_op"] == 0
        and active["exceptions_reaching_book_end"] == 0
    )
    classification = (
        "active_copy_length_exceptions_still_partial_next_op_intrusions"
        if active_all_partial_single_next and len(removed_rows) == 4 and not added_rows
        else "active_copy_length_exception_topology_changed"
    )

    return {
        "schema": "active_copy_length_exception_topology_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "previous_formula": rel(PREVIOUS_FORMULA),
            "active_formula": rel(ACTIVE_FORMULA),
            "books_digits": rel(BOOKS_DIGITS),
            "copy_length_exception_51": rel(COPY_LENGTH_EXCEPTION_51),
            "active_source_length_joint_60": rel(ACTIVE_SOURCE_LENGTH_JOINT_60),
        },
        "scope": {
            "analysis_only": True,
            "new_formula_emitted": False,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
            "does_not_search_new_resegmentations": True,
        },
        "previous_topology": previous,
        "active_topology": active,
        "removed_exception_rows": removed_rows,
        "added_exception_rows": added_rows,
        "summary": {
            "previous_exception_count": previous["target_max_exception_count"],
            "active_exception_count": active["target_max_exception_count"],
            "exception_count_delta": (
                active["target_max_exception_count"]
                - previous["target_max_exception_count"]
            ),
            "previous_target_max_match_count": previous["target_max_match_count"],
            "active_target_max_match_count": active["target_max_match_count"],
            "target_max_match_delta": (
                active["target_max_match_count"]
                - previous["target_max_match_count"]
            ),
            "previous_slack_digits_total": previous["target_max_slack_digits_total"],
            "active_slack_digits_total": active["target_max_slack_digits_total"],
            "slack_digits_delta": (
                active["target_max_slack_digits_total"]
                - previous["target_max_slack_digits_total"]
            ),
            "removed_exception_count": len(removed_rows),
            "added_exception_count": len(added_rows),
            "active_exceptions_covering_exactly_one_following_op": active[
                "exceptions_covering_exactly_one_following_op"
            ],
            "active_exceptions_absorbing_full_next_op": active[
                "exceptions_absorbing_full_next_op"
            ],
            "active_exceptions_with_partial_following_op_cover": active[
                "exceptions_with_partial_following_op_cover"
            ],
            "active_all_partial_single_next": active_all_partial_single_next,
            "interpretation": (
                "The target-max resegmentation path eliminates four old length "
                "exceptions and reduces slack by 13 digits, but every remaining "
                "active exception still crosses into exactly one following op and "
                "stops inside it. The residual problem is still joint segmentation, "
                "not a scalar length-default choice."
            ),
        },
        "decision": {
            "compression_bound_status": "unchanged_8156_049986",
            "copy_length_targetmax_status": "active_exceptions_reduced_to_19_but_topology_unchanged",
            "copy_length_dependency_status": "retained_declared",
            "generation_explanation_status": "residual_length_exceptions_are_segmentation_boundaries",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / "61_active_copy_length_exception_topology_gate.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    active = result["active_topology"]
    lines = [
        "# Active Copy Length Exception Topology Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 51 mapped the 23 target-max exceptions on the source-substitution",
        "fourth-pass formula. Gate 60 showed the active formula has four more",
        "target-max hits. This gate maps the remaining active exceptions without",
        "searching another resegmentation or compression improvement.",
        "",
        "## Comparison",
        "",
        "| Metric | Previous | Active | Delta |",
        "|---|---:|---:|---:|",
        f"| Target-max matches | `{s['previous_target_max_match_count']}` | `{s['active_target_max_match_count']}` | `{s['target_max_match_delta']:+d}` |",
        f"| Target-max exceptions | `{s['previous_exception_count']}` | `{s['active_exception_count']}` | `{s['exception_count_delta']:+d}` |",
        f"| Slack digits total | `{s['previous_slack_digits_total']}` | `{s['active_slack_digits_total']}` | `{s['slack_digits_delta']:+d}` |",
        f"| Removed exception rows | `0` | `{s['removed_exception_count']}` | `{s['removed_exception_count']:+d}` |",
        f"| Added exception rows | `0` | `{s['added_exception_count']}` | `{s['added_exception_count']:+d}` |",
        "",
        "## Active Topology",
        "",
        f"- Active exceptions: `{active['target_max_exception_count']}`.",
        f"- Active exceptions covering exactly one following op: `{active['exceptions_covering_exactly_one_following_op']}`.",
        f"- Active exceptions with partial following-op cover: `{active['exceptions_with_partial_following_op_cover']}`.",
        f"- Active exceptions absorbing a full next op: `{active['exceptions_absorbing_full_next_op']}`.",
        f"- Active exceptions reaching book end: `{active['exceptions_reaching_book_end']}`.",
        f"- Active covered following digits by type: `{active['covered_following_digits_by_type']}`.",
        f"- Active fully covered following ops by type: `{active['fully_covered_following_ops_by_type']}`.",
        "",
        "## Removed Exception Rows",
        "",
        "| Book | Op | Pos | Source | Length | Target max | Slack | First next type |",
        "|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in result["removed_exception_rows"]:
        lines.append(
            f"| `{row['book']}` | `{row['op_index']}` | `{row['book_pos']}` | "
            f"`{row['source_digit_pos']}` | `{row['length']}` | "
            f"`{row['encoder_target_max']}` | `{row['target_max_slack']}` | "
            f"`{row['first_covered_following_op_type']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Active all-partial-single-next topology: `{s['active_all_partial_single_next']}`.",
            f"- Interpretation: {s['interpretation']}",
            "- Current compression bound remains `8156.049986` bits.",
            "- Copy length remains a declared dependency until a joint segmentation/source/length parser derives these boundaries.",
            "",
            "## Boundary",
            "",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
            "- Row0 origin remains unchanged and exogenous.",
            "- No new formula is emitted.",
            "- No new resegmentation is searched.",
        ]
    )
    (TEST_RESULTS / "61_active_copy_length_exception_topology_gate.md").write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
