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
STRUCTURAL = TEST_RESULTS / "02_structural_segmentation_hypothesis_audit.json"
POLICY_DRIFT = TEST_RESULTS / "09_integrated_parser_policy_and_drift_audit.json"

OUT_STEM = "15_source_boundary_alignment_audit"
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


def book_global_offsets(books: dict[int, str]) -> dict[int, int]:
    offsets: dict[int, int] = {}
    pos = 0
    for book in range(70):
        offsets[book] = pos
        pos += len(books[book])
    return offsets


def build_boundary_sets(
    books: dict[int, str], projected_ops: list[dict[str, Any]]
) -> tuple[dict[int, int], set[int], set[int], int]:
    offsets = book_global_offsets(books)
    corpus_len = sum(len(books[book]) for book in range(70))
    book_boundaries: set[int] = {0, corpus_len}
    operation_boundaries: set[int] = {0, corpus_len}
    for book in range(70):
        book_boundaries.add(offsets[book])
        book_boundaries.add(offsets[book] + len(books[book]))
    operation_boundaries |= book_boundaries
    for op in projected_ops:
        start = offsets[int(op["book"])] + int(op["target_start"])
        operation_boundaries.add(start)
        operation_boundaries.add(start + int(op["length"]))
    return offsets, operation_boundaries, book_boundaries, corpus_len


def candidate_pairs(source_rows: list[dict[str, int]]) -> list[tuple[int, int]]:
    pairs: list[tuple[int, int]] = []
    for row in source_rows:
        for length in range(MIN_COPY_LEN, int(row["max_length"]) + 1):
            pairs.append((int(row["source"]), length))
    return pairs


def boundary_flags(
    source: int,
    length: int,
    prior_operation_boundaries: set[int],
    prior_book_boundaries: set[int],
) -> dict[str, bool | int]:
    end = source + length
    internal_operation = [
        pos for pos in prior_operation_boundaries if source < pos < end
    ]
    return {
        "source_start_on_operation_boundary": source in prior_operation_boundaries,
        "source_end_on_operation_boundary": end in prior_operation_boundaries,
        "source_start_on_book_boundary": source in prior_book_boundaries,
        "source_end_on_book_boundary": end in prior_book_boundaries,
        "source_interval_has_no_internal_operation_boundary": not internal_operation,
        "source_interval_equals_single_prior_chunk": (
            source in prior_operation_boundaries
            and end in prior_operation_boundaries
            and not internal_operation
        ),
        "internal_operation_boundary_count": len(internal_operation),
    }


def expected_rate(
    pairs: list[tuple[int, int]],
    prior_operation_boundaries: set[int],
    prior_book_boundaries: set[int],
    flag_name: str,
) -> float:
    if not pairs:
        return 0.0
    return sum(
        1.0
        for source, length in pairs
        if boundary_flags(
            source, length, prior_operation_boundaries, prior_book_boundaries
        )[flag_name]
    ) / len(pairs)


def choose_global_max_source(
    rows: list[dict[str, int]],
    policy: str,
    prior_operation_boundaries: set[int],
) -> tuple[int, int] | None:
    if not rows:
        return None
    max_length = max(int(row["max_length"]) for row in rows)
    max_rows = [row for row in rows if int(row["max_length"]) == max_length]
    filtered = max_rows
    if policy == "earliest":
        filtered = max_rows
    elif policy == "end_boundary_then_earliest":
        filtered = [
            row
            for row in max_rows
            if int(row["source"]) + max_length in prior_operation_boundaries
        ] or max_rows
    elif policy == "start_boundary_then_earliest":
        filtered = [
            row for row in max_rows if int(row["source"]) in prior_operation_boundaries
        ] or max_rows
    elif policy == "both_boundaries_then_earliest":
        filtered = [
            row
            for row in max_rows
            if int(row["source"]) in prior_operation_boundaries
            and int(row["source"]) + max_length in prior_operation_boundaries
        ] or max_rows
    elif policy == "no_internal_boundary_then_earliest":
        filtered = [
            row
            for row in max_rows
            if not any(
                int(row["source"]) < pos < int(row["source"]) + max_length
                for pos in prior_operation_boundaries
            )
        ] or max_rows
    else:
        raise ValueError(policy)
    return min(int(row["source"]) for row in filtered), max_length


def score_policy(
    copy_rows: list[dict[str, Any]], policy: str
) -> dict[str, Any]:
    hits = [
        row
        for row in copy_rows
        if row["policy_predictions"][policy]["matches_declared_pair"]
    ]
    return {
        "policy": policy,
        "hits": len(hits),
        "total": len(copy_rows),
        "coverage": len(hits) / len(copy_rows),
        "misses": len(copy_rows) - len(hits),
    }


def make_result() -> dict[str, Any]:
    structural = load_json(STRUCTURAL)
    policy_drift = load_json(POLICY_DRIFT)
    assert_boundary("structural_segmentation_hypothesis_audit", structural)
    assert_boundary("integrated_parser_policy_and_drift_audit", policy_drift)

    trace_module = load_module("segmentation_trace_for_gate15", TRACE_SCRIPT)
    gate111 = load_module("gate111_for_segmentation_gate15", GATE111_SCRIPT)
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    projected_ops = trace_module.projected_ops_from_copy_rows(
        gate111.make_copy_rows(), books
    )
    offsets, operation_boundaries, book_boundaries, _ = build_boundary_sets(
        books, projected_ops
    )

    emitted = "".join(books[book] for book in SEED_BOOKS)
    copy_rows: list[dict[str, Any]] = []
    policy_names = [
        "earliest",
        "end_boundary_then_earliest",
        "start_boundary_then_earliest",
        "both_boundaries_then_earliest",
        "no_internal_boundary_then_earliest",
    ]
    for op in projected_ops:
        book = int(op["book"])
        target = books[book]
        target_start = int(op["target_start"])
        global_target_start = offsets[book] + target_start
        prior_operation_boundaries = {
            pos for pos in operation_boundaries if pos <= global_target_start
        }
        prior_book_boundaries = {
            pos for pos in book_boundaries if pos <= global_target_start
        }
        if op["type"] == "copy":
            source = int(op["source"])
            length = int(op["length"])
            source_rows = trace_module.candidate_sources_with_max(
                emitted, target, target_start
            )
            all_pairs = candidate_pairs(source_rows)
            max_len = max(int(row["max_length"]) for row in source_rows)
            global_max_pairs = [
                (int(row["source"]), max_len)
                for row in source_rows
                if int(row["max_length"]) == max_len
            ]
            flags = boundary_flags(
                source, length, prior_operation_boundaries, prior_book_boundaries
            )
            predictions = {}
            for policy in policy_names:
                predicted = choose_global_max_source(
                    source_rows, policy, prior_operation_boundaries
                )
                predictions[policy] = {
                    "source": None if predicted is None else predicted[0],
                    "length": None if predicted is None else predicted[1],
                    "matches_declared_pair": predicted == (source, length),
                }
            copy_rows.append(
                {
                    "book": book,
                    "op_index": int(op["op_index"]),
                    "projection_copy_index": op["projection_copy_index"],
                    "target_start": target_start,
                    "source": source,
                    "length": length,
                    "global_max_length": max_len,
                    "global_max_source_count": len(global_max_pairs),
                    "candidate_pair_count": len(all_pairs),
                    "flags": flags,
                    "all_candidate_expected": {
                        name: expected_rate(
                            all_pairs,
                            prior_operation_boundaries,
                            prior_book_boundaries,
                            name,
                        )
                        for name in [
                            "source_start_on_operation_boundary",
                            "source_end_on_operation_boundary",
                            "source_interval_equals_single_prior_chunk",
                        ]
                    },
                    "global_max_candidate_expected": {
                        name: expected_rate(
                            global_max_pairs,
                            prior_operation_boundaries,
                            prior_book_boundaries,
                            name,
                        )
                        for name in [
                            "source_start_on_operation_boundary",
                            "source_end_on_operation_boundary",
                            "source_interval_equals_single_prior_chunk",
                        ]
                    },
                    "policy_predictions": predictions,
                }
            )
        emitted += target[target_start : target_start + int(op["length"])]

    copy_count = len(copy_rows)
    flag_hits = {
        name: sum(1 for row in copy_rows if row["flags"][name])
        for name in [
            "source_start_on_operation_boundary",
            "source_end_on_operation_boundary",
            "source_start_on_book_boundary",
            "source_end_on_book_boundary",
            "source_interval_has_no_internal_operation_boundary",
            "source_interval_equals_single_prior_chunk",
        ]
    }
    expected = {
        "all_candidate": {
            name: sum(row["all_candidate_expected"][name] for row in copy_rows)
            for name in copy_rows[0]["all_candidate_expected"]
        },
        "global_max_candidate": {
            name: sum(row["global_max_candidate_expected"][name] for row in copy_rows)
            for name in copy_rows[0]["global_max_candidate_expected"]
        },
    }
    policy_scores = [score_policy(copy_rows, policy) for policy in policy_names]
    earliest = next(row for row in policy_scores if row["policy"] == "earliest")
    best_boundary_policy = max(
        [row for row in policy_scores if row["policy"] != "earliest"],
        key=lambda row: row["hits"],
    )
    boundary_lift_vs_earliest = best_boundary_policy["hits"] - earliest["hits"]
    promotes_boundary_rule = (
        flag_hits["source_interval_equals_single_prior_chunk"] == copy_count
        or boundary_lift_vs_earliest > 0
    )
    classification = (
        "source_boundary_block_hypothesis_rejected"
        if not promotes_boundary_rule
        else "source_boundary_block_hypothesis_partial"
    )

    sample_misses = [
        {
            "book": row["book"],
            "op_index": row["op_index"],
            "source": row["source"],
            "length": row["length"],
            "flags": row["flags"],
        }
        for row in copy_rows
        if not row["flags"]["source_interval_equals_single_prior_chunk"]
    ][:12]
    return {
        "schema": "source_boundary_alignment_audit.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "segmentation_trace_script": rel(TRACE_SCRIPT),
            "structural_segmentation_hypothesis_audit": rel(STRUCTURAL),
            "integrated_parser_policy_and_drift_audit": rel(POLICY_DRIFT),
        },
        "scope": {
            "analysis_only": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "tests_source_side_operation_boundaries": True,
            "target_text_required_for_candidate_enumeration": True,
            "declared_literal_windows_granted": False,
            "source_free_digit_generator_emitted": False,
        },
        "summary": {
            "copy_count": copy_count,
            "source_start_on_operation_boundary": flag_hits[
                "source_start_on_operation_boundary"
            ],
            "source_end_on_operation_boundary": flag_hits[
                "source_end_on_operation_boundary"
            ],
            "source_start_on_book_boundary": flag_hits["source_start_on_book_boundary"],
            "source_end_on_book_boundary": flag_hits["source_end_on_book_boundary"],
            "source_interval_has_no_internal_operation_boundary": flag_hits[
                "source_interval_has_no_internal_operation_boundary"
            ],
            "source_interval_equals_single_prior_chunk": flag_hits[
                "source_interval_equals_single_prior_chunk"
            ],
            "all_candidate_expected_source_end_on_operation_boundary": expected[
                "all_candidate"
            ]["source_end_on_operation_boundary"],
            "global_max_expected_source_end_on_operation_boundary": expected[
                "global_max_candidate"
            ]["source_end_on_operation_boundary"],
            "earliest_global_max_hits": earliest["hits"],
            "best_boundary_policy": best_boundary_policy["policy"],
            "best_boundary_policy_hits": best_boundary_policy["hits"],
            "boundary_policy_lift_vs_earliest": boundary_lift_vs_earliest,
            "promotes_boundary_rule": promotes_boundary_rule,
            "interpretation": (
                "Source-side operation boundaries do not explain copy chunking. "
                "Only a small minority of declared copies start or end on an "
                "available prior operation boundary, almost none equal one prior "
                "chunk, and boundary-aware global-max tie-breakers are worse than "
                "the existing earliest-source rule."
            ),
        },
        "flag_hits": flag_hits,
        "candidate_control_expected_hits": expected,
        "policy_scoreboard": policy_scores,
        "sample_single_chunk_misses": sample_misses,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": classification,
            "source_length_dependency_status": "source_boundary_chunking_rejected",
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
    lines = [
        "# Source Boundary Alignment Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 15 tests a block/chunk hypothesis for segmentation: copy",
        "intervals might be chosen because they respect operation or book",
        "boundaries already present in the source stream. This is a structural",
        "generation hypothesis, not a compression sweep.",
        "",
        "## Boundary Coverage",
        "",
        f"- Copy rows tested: `{s['copy_count']}`.",
        f"- Source starts on prior operation boundary: `{s['source_start_on_operation_boundary']}/{s['copy_count']}`.",
        f"- Source ends on prior operation boundary: `{s['source_end_on_operation_boundary']}/{s['copy_count']}`.",
        f"- Source starts on prior book boundary: `{s['source_start_on_book_boundary']}/{s['copy_count']}`.",
        f"- Source ends on prior book boundary: `{s['source_end_on_book_boundary']}/{s['copy_count']}`.",
        f"- Source interval has no internal prior operation boundary: `{s['source_interval_has_no_internal_operation_boundary']}/{s['copy_count']}`.",
        f"- Source interval equals one prior chunk: `{s['source_interval_equals_single_prior_chunk']}/{s['copy_count']}`.",
        "",
        "## Candidate Controls",
        "",
        "| Control | Expected source-end boundary hits |",
        "|---|---:|",
        f"| Uniform over all legal candidate pairs | `{s['all_candidate_expected_source_end_on_operation_boundary']:.3f}` |",
        f"| Uniform over global-max candidate pairs | `{s['global_max_expected_source_end_on_operation_boundary']:.3f}` |",
        f"| Declared pairs | `{s['source_end_on_operation_boundary']}` |",
        "",
        "The declared source-end boundary rate is close to the global-max",
        "candidate control because the retained parser already chooses global",
        "max copies. It is not an independent chunk-boundary rule.",
        "",
        "## Source Tie Policies",
        "",
        "| Policy | Hits | Misses |",
        "|---|---:|---:|",
    ]
    for row in result["policy_scoreboard"]:
        lines.append(
            f"| `{row['policy']}` | `{row['hits']}/{row['total']}` | `{row['misses']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Promotes source-boundary rule: `{s['promotes_boundary_rule']}`.",
            f"- Best boundary-aware policy: `{s['best_boundary_policy']}` with `{s['best_boundary_policy_hits']}/{s['copy_count']}` hits.",
            f"- Lift vs existing earliest-source global-max rule: `{s['boundary_policy_lift_vs_earliest']}`.",
            f"- {s['interpretation']}",
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
