from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

PREQ = ROOT / "analysis" / "prequential_and_row0_origin_audit_20260621"
GATE111_SCRIPT = PREQ / "scripts" / "111_decoder_length_candidate_ambiguity_audit.py"
BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
TRACE_SCRIPT = HERE / "scripts" / "01_segmentation_decision_trace.py"
DEPENDENCY = TEST_RESULTS / "04_parser_dependency_reduction_ledger.json"
ONLINE_LITERAL = TEST_RESULTS / "06_online_literal_stop_rule_audit.json"
LITERAL_EXCEPTION = TEST_RESULTS / "07_literal_stop_exception_topology_audit.json"

OUT_STEM = "08_integrated_online_literal_parser_audit"
SEED_BOOKS = list(range(10))
MIN_COPY_LEN = 5


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


def offset_rows(trace_module, emitted: str, target: str, start: int) -> list[dict[str, int]]:
    rows: list[dict[str, int]] = []
    for offset in range(len(target) - start + 1):
        if start + offset >= len(target):
            max_copy_length = 0
        else:
            candidates = trace_module.candidate_sources_with_max(
                emitted + target[start : start + offset],
                target,
                start + offset,
            )
            max_copy_length = max(
                [row["max_length"] for row in candidates],
                default=0,
            )
        rows.append(
            {
                "offset": offset,
                "max_copy_length": max_copy_length,
                "total_advance": offset + max_copy_length,
            }
        )
    return rows


def predict_first_confirmed_peak(
    rows: list[dict[str, int]], field: str, confirm_window: int
) -> int | None:
    for index, offset in enumerate(rows):
        if offset["max_copy_length"] < MIN_COPY_LEN:
            continue
        value = offset[field]
        if all(
            index + step >= len(rows) or rows[index + step][field] <= value
            for step in range(1, confirm_window + 1)
        ):
            return offset["offset"]
    return None


def choose_copy(trace_module, emitted: str, target: str, pos: int) -> dict[str, int] | None:
    candidates = trace_module.candidate_sources_with_max(emitted, target, pos)
    if not candidates:
        return None
    max_length = max(row["max_length"] for row in candidates)
    source = min(row["source"] for row in candidates if row["max_length"] == max_length)
    return {"source": source, "length": max_length}


def parse_book(
    trace_module,
    target: str,
    emitted: str,
    confirm_window: int,
) -> tuple[list[dict[str, Any]], str]:
    pos = 0
    ops: list[dict[str, Any]] = []
    while pos < len(target):
        rows = offset_rows(trace_module, emitted, target, pos)
        predicted_offset = predict_first_confirmed_peak(
            rows,
            "max_copy_length",
            confirm_window,
        )
        if predicted_offset is None:
            ops.append(
                {
                    "type": "literal",
                    "target_start": pos,
                    "length": len(target) - pos,
                    "source": None,
                }
            )
            emitted += target[pos:]
            pos = len(target)
            continue

        if predicted_offset > 0:
            ops.append(
                {
                    "type": "literal",
                    "target_start": pos,
                    "length": predicted_offset,
                    "source": None,
                }
            )
            emitted += target[pos : pos + predicted_offset]
            pos += predicted_offset

        copy = choose_copy(trace_module, emitted, target, pos)
        if copy is None:
            raise RuntimeError(
                {
                    "type": "predicted_offset_without_copy",
                    "target_start": pos,
                    "predicted_offset": predicted_offset,
                }
            )
        ops.append(
            {
                "type": "copy",
                "target_start": pos,
                "length": copy["length"],
                "source": copy["source"],
            }
        )
        emitted += target[pos : pos + copy["length"]]
        pos += copy["length"]
    return ops, emitted


def normalized_projected_ops(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "type": row["type"],
            "target_start": int(row["target_start"]),
            "length": int(row["length"]),
            "source": row["source"],
        }
        for row in rows
    ]


def compare_ops(
    book: int, predicted: list[dict[str, Any]], projected: list[dict[str, Any]]
) -> dict[str, Any] | None:
    if predicted == projected:
        return None
    first_diff = None
    for index, (left, right) in enumerate(zip(predicted, projected)):
        if left != right:
            first_diff = {
                "index": index,
                "predicted": left,
                "stable_projection": right,
            }
            break
    if first_diff is None:
        index = min(len(predicted), len(projected))
        first_diff = {
            "index": index,
            "predicted": None if index >= len(predicted) else predicted[index],
            "stable_projection": None if index >= len(projected) else projected[index],
        }
    return {
        "book": book,
        "predicted_op_count": len(predicted),
        "stable_projection_op_count": len(projected),
        "first_diff": first_diff,
    }


def make_result() -> dict[str, Any]:
    dependency = load_json(DEPENDENCY)
    online_literal = load_json(ONLINE_LITERAL)
    literal_exception = load_json(LITERAL_EXCEPTION)
    for name, data in [
        ("parser_dependency_reduction_ledger", dependency),
        ("online_literal_stop_rule_audit", online_literal),
        ("literal_stop_exception_topology_audit", literal_exception),
    ]:
        assert_boundary(name, data)

    best = online_literal["summary"]["best_policy"]
    if best["policy"] != "first_confirmed_max_copy_length_peak":
        raise RuntimeError("gate 06 selected policy changed")
    confirm_window = int(best["confirm_window"])

    trace_module = load_module("segmentation_trace_for_gate08", TRACE_SCRIPT)
    gate111 = load_module("gate111_for_segmentation_gate08", GATE111_SCRIPT)
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    stable_ops = trace_module.projected_ops_from_copy_rows(gate111.make_copy_rows(), books)
    stable_by_book: dict[int, list[dict[str, Any]]] = {}
    for op in stable_ops:
        stable_by_book.setdefault(int(op["book"]), []).append(op)
    for rows in stable_by_book.values():
        rows.sort(key=lambda row: int(row["target_start"]))

    emitted = "".join(books[book] for book in SEED_BOOKS)
    exact_books: list[int] = []
    mismatch_rows: list[dict[str, Any]] = []
    predicted_copy_count = 0
    predicted_literal_count = 0
    predicted_literal_digits = 0
    stable_copy_count = 0
    stable_literal_count = 0
    stable_literal_digits = 0

    for book in range(10, 70):
        predicted, emitted = parse_book(
            trace_module,
            books[book],
            emitted,
            confirm_window,
        )
        projected = normalized_projected_ops(stable_by_book.get(book, []))
        predicted_copy_count += sum(1 for row in predicted if row["type"] == "copy")
        predicted_literal_count += sum(1 for row in predicted if row["type"] == "literal")
        predicted_literal_digits += sum(
            int(row["length"]) for row in predicted if row["type"] == "literal"
        )
        stable_copy_count += sum(1 for row in projected if row["type"] == "copy")
        stable_literal_count += sum(1 for row in projected if row["type"] == "literal")
        stable_literal_digits += sum(
            int(row["length"]) for row in projected if row["type"] == "literal"
        )
        mismatch = compare_ops(book, predicted, projected)
        if mismatch is None:
            exact_books.append(book)
        else:
            mismatch_rows.append(mismatch)

    greedy = dependency["full_greedy_parser_control"]
    exact_count = len(exact_books)
    tested_books = 60
    greedy_exact = int(greedy["exact_book_count"])
    if exact_count == tested_books:
        classification = "integrated_online_literal_parser_exact_target_text_parser_not_source_free"
        generation_status = "integrated_target_text_parser_exact_against_stable_projection"
    elif exact_count > greedy_exact:
        classification = "integrated_online_literal_parser_partial_improvement_not_promoted"
        generation_status = "integrated_parser_improves_greedy_but_drifts"
    else:
        classification = "integrated_online_literal_parser_no_improvement_not_promoted"
        generation_status = "integrated_parser_does_not_improve_greedy_exact_books"

    return {
        "schema": "integrated_online_literal_parser_audit.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "parser_dependency_reduction_ledger": rel(DEPENDENCY),
            "online_literal_stop_rule_audit": rel(ONLINE_LITERAL),
            "literal_stop_exception_topology_audit": rel(LITERAL_EXCEPTION),
            "books_digits": rel(BOOKS_DIGITS),
        },
        "scope": {
            "analysis_only": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "target_text_required": True,
            "declared_literal_windows_granted": False,
            "declared_copy_starts_granted": False,
            "source_free_digit_generator_emitted": False,
        },
        "parser": {
            "literal_stop_policy": best["policy"],
            "confirm_window": confirm_window,
            "copy_policy": "longest_previous_target_match_earliest_source_tie",
            "book_order": "canonical_10_to_69_after_seed_books_0_to_9",
        },
        "summary": {
            "tested_books": tested_books,
            "exact_book_count": exact_count,
            "mismatch_book_count": len(mismatch_rows),
            "exact_books": exact_books,
            "mismatch_books": [row["book"] for row in mismatch_rows],
            "exact_books_delta_vs_full_greedy": exact_count - greedy_exact,
            "full_greedy_exact_books": greedy_exact,
            "predicted_operation_count": predicted_copy_count + predicted_literal_count,
            "stable_projection_operation_count": stable_copy_count + stable_literal_count,
            "predicted_copy_count": predicted_copy_count,
            "stable_copy_count": stable_copy_count,
            "predicted_literal_gap_count": predicted_literal_count,
            "stable_literal_gap_count": stable_literal_count,
            "predicted_literal_digit_count": predicted_literal_digits,
            "stable_literal_digit_count": stable_literal_digits,
            "sample_mismatches": mismatch_rows[:12],
            "interpretation": (
                "The frozen online literal stop rule is tested as an executable "
                "parser rather than inside declared literal windows. Any mismatch "
                "means the local stop rule drifts when it must choose subsequent "
                "operation starts itself."
            ),
        },
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": generation_status,
            "integrated_parser_status": classification,
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / f"{OUT_STEM}.json"
    md_path = TEST_RESULTS / f"{OUT_STEM}.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    parser = result["parser"]
    lines = [
        "# Integrated Online Literal Parser Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 06 scored an online literal-stop rule inside known literal gaps.",
        "This gate freezes that rule and lets it parse each non-seed book",
        "end-to-end, without granting declared literal windows or declared copy",
        "starts.",
        "",
        "## Parser",
        "",
        f"- Literal stop policy: `{parser['literal_stop_policy']}`.",
        f"- Confirm window: `{parser['confirm_window']}`.",
        f"- Copy policy: `{parser['copy_policy']}`.",
        f"- Book order: `{parser['book_order']}`.",
        "",
        "## Result",
        "",
        f"- Exact books vs stable projection: `{s['exact_book_count']}/{s['tested_books']}`.",
        f"- Full greedy exact books: `{s['full_greedy_exact_books']}/{s['tested_books']}`.",
        f"- Delta vs full greedy: `{s['exact_books_delta_vs_full_greedy']}`.",
        f"- Predicted operations: `{s['predicted_operation_count']}` vs stable `{s['stable_projection_operation_count']}`.",
        f"- Predicted copy ops: `{s['predicted_copy_count']}` vs stable `{s['stable_copy_count']}`.",
        f"- Predicted literal gaps: `{s['predicted_literal_gap_count']}` vs stable `{s['stable_literal_gap_count']}`.",
        f"- Predicted literal digits: `{s['predicted_literal_digit_count']}` vs stable `{s['stable_literal_digit_count']}`.",
        "",
        "## Mismatch Sample",
        "",
        "| Book | Predicted ops | Stable ops | First diff |",
        "|---:|---:|---:|---|",
    ]
    for row in s["sample_mismatches"]:
        lines.append(
            f"| `{row['book']}` | `{row['predicted_op_count']}` | "
            f"`{row['stable_projection_op_count']}` | "
            f"`{json.dumps(row['first_diff'], sort_keys=True)}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- {s['interpretation']}",
            f"- Integrated parser status: `{result['decision']['integrated_parser_status']}`.",
            "- The result remains target-text-aware and analysis-only.",
            "- Compression bound is unchanged.",
            "- Row0 remains exogenous and unchanged.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
            "",
        ]
    )
    md_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    result = make_result()
    write_result(result)
    print(json.dumps(result["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
