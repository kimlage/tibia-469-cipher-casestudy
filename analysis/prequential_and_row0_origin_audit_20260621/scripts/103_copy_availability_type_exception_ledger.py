from __future__ import annotations

import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

GATE100 = TEST_RESULTS / "100_skeleton_rule_coverage_audit.json"
GATE99 = TEST_RESULTS / "99_exact_skeleton_dependency_ledger.json"

RANDOM_SEED = 469103
CONTROL_TRIALS = 20000


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


def predict_type(row: dict[str, Any]) -> str:
    return "copy" if bool(row["copy_available_minlen"]) else "literal"


def count_errors(rows: list[dict[str, Any]], availability: list[bool]) -> int:
    errors = 0
    for row, available in zip(rows, availability, strict=True):
        predicted = "copy" if available else "literal"
        if predicted != row["type"]:
            errors += 1
    return errors


def summarize(values: list[int]) -> dict[str, Any]:
    return {
        "trials": len(values),
        "min": min(values),
        "median": median(values),
        "mean": mean(values),
        "max": max(values),
    }


def make_corpus_control(rows: list[dict[str, Any]], rng: random.Random) -> list[int]:
    available_count = sum(1 for row in rows if row["copy_available_minlen"])
    values = []
    for _ in range(CONTROL_TRIALS):
        available_indexes = set(rng.sample(range(len(rows)), available_count))
        availability = [idx in available_indexes for idx in range(len(rows))]
        values.append(count_errors(rows, availability))
    return values


def make_book_control(rows: list[dict[str, Any]], rng: random.Random) -> list[int]:
    indexes_by_book: dict[int, list[int]] = defaultdict(list)
    available_by_book: dict[int, int] = defaultdict(int)
    for idx, row in enumerate(rows):
        book = int(row["book"])
        indexes_by_book[book].append(idx)
        if row["copy_available_minlen"]:
            available_by_book[book] += 1

    values = []
    for _ in range(CONTROL_TRIALS):
        available = [False] * len(rows)
        for book, indexes in indexes_by_book.items():
            for idx in rng.sample(indexes, available_by_book[book]):
                available[idx] = True
        values.append(count_errors(rows, available))
    return values


def log_hypergeom_all_copies_inside_available(
    total_rows: int, copy_rows: int, available_rows: int
) -> float:
    literal_rows = total_rows - copy_rows
    literal_available = available_rows - copy_rows
    if literal_available < 0 or literal_available > literal_rows:
        return float("-inf")
    return (
        math.lgamma(literal_rows + 1)
        - math.lgamma(literal_available + 1)
        - math.lgamma(literal_rows - literal_available + 1)
        - (
            math.lgamma(total_rows + 1)
            - math.lgamma(available_rows + 1)
            - math.lgamma(total_rows - available_rows + 1)
        )
    )


def make_result() -> dict[str, Any]:
    gate99 = load_json(GATE99)
    gate100 = load_json(GATE100)
    assert_boundary("exact_skeleton_dependency_ledger", gate99)
    assert_boundary("skeleton_rule_coverage_audit", gate100)
    if gate100["classification"] != "skeleton_simple_rule_coverage_insufficient":
        raise RuntimeError("gate100 did not reject simple skeleton rules")

    rows = sorted(
        gate100["skeleton_rows"],
        key=lambda row: (int(row["book"]), int(row["op_index"])),
    )
    op_count = len(rows)
    copy_count = sum(1 for row in rows if row["type"] == "copy")
    literal_count = op_count - copy_count
    availability = [bool(row["copy_available_minlen"]) for row in rows]
    availability_count = sum(availability)

    error_rows = [
        row
        for row in rows
        if predict_type(row) != row["type"]
    ]
    unavailable_copy_rows = [
        row
        for row in rows
        if row["type"] == "copy" and not row["copy_available_minlen"]
    ]
    forced_literal_rows = [
        row
        for row in rows
        if row["type"] == "literal" and not row["copy_available_minlen"]
    ]
    optional_literal_rows = [
        row
        for row in rows
        if row["type"] == "literal" and row["copy_available_minlen"]
    ]

    always_copy_errors = literal_count
    always_literal_errors = copy_count
    availability_errors = len(error_rows)
    availability_hits = op_count - availability_errors
    exact_atlas_records = int(gate99["summary"]["skeleton_atlas_records"])
    copy_source_fields = int(gate99["summary"]["copy_items"])
    literal_payload_chunks = int(gate99["summary"]["literal_runs"])
    skeleton_total_materialized = int(
        gate99["summary"]["skeleton_total_materialized_records"]
    )

    length_records = op_count
    optional_literal_exception_records = len(optional_literal_rows)
    availability_conditioned_skeleton_records = (
        length_records + optional_literal_exception_records
    )
    availability_conditioned_total_records = (
        availability_conditioned_skeleton_records
        + copy_source_fields
        + literal_payload_chunks
    )

    rng = random.Random(RANDOM_SEED)
    corpus_control_errors = make_corpus_control(rows, rng)
    book_control_errors = make_book_control(rows, rng)
    corpus_empirical_p = (
        sum(1 for value in corpus_control_errors if value <= availability_errors)
        / CONTROL_TRIALS
    )
    book_empirical_p = (
        sum(1 for value in book_control_errors if value <= availability_errors)
        / CONTROL_TRIALS
    )
    log_p = log_hypergeom_all_copies_inside_available(
        total_rows=op_count,
        copy_rows=copy_count,
        available_rows=availability_count,
    )
    hypergeom_p = math.exp(log_p)

    classification = "copy_availability_type_exception_audit_only"
    return {
        "schema": "copy_availability_type_exception_ledger.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "gate99_exact_skeleton_dependency_ledger": rel(GATE99),
            "gate100_skeleton_rule_coverage": rel(GATE100),
        },
        "scope": {
            "analysis_only": True,
            "tests_target_dependent_copy_availability": True,
            "target_text_dependency_retained": True,
            "compression_bound_changed": False,
            "new_formula_emitted": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
        },
        "summary": {
            "op_count": op_count,
            "copy_count": copy_count,
            "literal_count": literal_count,
            "copy_available_rows": availability_count,
            "copy_unavailable_rows": op_count - availability_count,
            "unavailable_copy_exceptions": len(unavailable_copy_rows),
            "forced_literal_rows": len(forced_literal_rows),
            "optional_literal_exceptions": len(optional_literal_rows),
            "availability_rule_hits": availability_hits,
            "availability_rule_errors": availability_errors,
            "availability_rule_coverage": availability_hits / op_count,
            "copy_recall_given_availability": (
                (copy_count - len(unavailable_copy_rows)) / copy_count
            ),
            "literal_forced_share": len(forced_literal_rows) / literal_count,
            "always_copy_errors": always_copy_errors,
            "always_literal_errors": always_literal_errors,
            "error_delta_vs_always_copy": availability_errors - always_copy_errors,
            "target_dependent_type_exception_fields": optional_literal_exception_records,
            "type_field_delta_vs_explicit_op_types": (
                optional_literal_exception_records - op_count
            ),
            "exact_atlas_records": exact_atlas_records,
            "availability_conditioned_skeleton_records": (
                availability_conditioned_skeleton_records
            ),
            "availability_conditioned_total_records": (
                availability_conditioned_total_records
            ),
            "record_delta_vs_exact_skeleton_atlas": (
                availability_conditioned_skeleton_records - exact_atlas_records
            ),
            "record_delta_vs_gate99_total_materialized": (
                availability_conditioned_total_records - skeleton_total_materialized
            ),
            "promotes_generator": False,
            "interpretation": (
                "Target-dependent copy availability contains every copy event "
                "and forces 36 literal rows; only 17 available-copy literal "
                "exceptions remain. This is a strong mechanical clue about op "
                "type, but it depends on target text/copy availability and, "
                "after length/source/payload records are paid, it does not "
                "replace the exact skeleton atlas with a smaller generator."
            ),
        },
        "controls": {
            "random_seed": RANDOM_SEED,
            "trials": CONTROL_TRIALS,
            "corpus_availability_shuffle": {
                **summarize(corpus_control_errors),
                "empirical_p_errors_lte_observed": corpus_empirical_p,
            },
            "book_availability_shuffle": {
                **summarize(book_control_errors),
                "empirical_p_errors_lte_observed": book_empirical_p,
            },
            "hypergeom_all_copies_inside_available_set": {
                "p": hypergeom_p,
                "log_p": log_p,
            },
        },
        "contingency": {
            f"{key[0]}|available_{str(key[1]).lower()}": value
            for key, value in sorted(
                Counter(
                    (row["type"], bool(row["copy_available_minlen"])) for row in rows
                ).items()
            )
        },
        "optional_literal_exception_rows": [
            {
                "book": int(row["book"]),
                "op_index": int(row["op_index"]),
                "target_start": int(row["target_start"]),
                "length": int(row["length"]),
                "remaining": int(row["remaining"]),
                "previous_in_book_type": row["previous_in_book_type"],
                "previous_in_book_length": row["previous_in_book_length"],
            }
            for row in optional_literal_rows
        ],
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": "target_dependent_type_clue_audit_only",
            "skeleton_status": "exact_atlas_retained",
            "source_dependency_status": "retained_declared_dependency",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / "103_copy_availability_type_exception_ledger.json"
    md_path = TEST_RESULTS / "103_copy_availability_type_exception_ledger.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    controls = result["controls"]
    lines = [
        "# Copy Availability Type Exception Ledger",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 100 showed that simple source-free rules do not generate the",
        "operation skeleton. This ledger tests the stronger target-dependent",
        "copy-availability clue: predict `copy` whenever a min-length copy is",
        "available at the target position, otherwise predict `literal`.",
        "",
        "## Result",
        "",
        f"- Operations: `{s['op_count']}`.",
        f"- Copies/literals: `{s['copy_count']}` / `{s['literal_count']}`.",
        f"- Copy-available rows: `{s['copy_available_rows']}`.",
        f"- Unavailable copy exceptions: `{s['unavailable_copy_exceptions']}`.",
        f"- Forced literal rows with no copy available: `{s['forced_literal_rows']}`.",
        f"- Optional literal exceptions while copy is available: `{s['optional_literal_exceptions']}`.",
        f"- Availability-rule hits/errors: `{s['availability_rule_hits']}` / `{s['availability_rule_errors']}`.",
        f"- Availability-rule coverage: `{s['availability_rule_coverage']:.6f}`.",
        f"- Error delta vs always-copy baseline: `{s['error_delta_vs_always_copy']}`.",
        f"- Type fields if target availability is allowed: `{s['target_dependent_type_exception_fields']}`.",
        f"- Type-field delta vs explicit op types: `{s['type_field_delta_vs_explicit_op_types']}`.",
        f"- Availability-conditioned skeleton records: `{s['availability_conditioned_skeleton_records']}`.",
        f"- Record delta vs exact skeleton atlas: `{s['record_delta_vs_exact_skeleton_atlas']}`.",
        f"- Record delta vs gate-99 total materialized records: `{s['record_delta_vs_gate99_total_materialized']}`.",
        "",
        "## Controls",
        "",
        f"- Corpus availability shuffle errors min/median/mean/max: `{controls['corpus_availability_shuffle']['min']}` / `{controls['corpus_availability_shuffle']['median']}` / `{controls['corpus_availability_shuffle']['mean']:.3f}` / `{controls['corpus_availability_shuffle']['max']}`.",
        f"- Corpus shuffle empirical p(errors <= observed): `{controls['corpus_availability_shuffle']['empirical_p_errors_lte_observed']:.6f}`.",
        f"- Book availability shuffle errors min/median/mean/max: `{controls['book_availability_shuffle']['min']}` / `{controls['book_availability_shuffle']['median']}` / `{controls['book_availability_shuffle']['mean']:.3f}` / `{controls['book_availability_shuffle']['max']}`.",
        f"- Book shuffle empirical p(errors <= observed): `{controls['book_availability_shuffle']['empirical_p_errors_lte_observed']:.6f}`.",
        f"- Hypergeometric p(all copies inside available set): `{controls['hypergeom_all_copies_inside_available_set']['p']:.6e}`.",
        "",
        "## Decision",
        "",
        f"- Promotes generator: `{s['promotes_generator']}`.",
        f"- {s['interpretation']}",
        "- Taxonomy: `AUDIT_ONLY`.",
        "- No compression-bound change is introduced.",
        "- No formula is emitted.",
        "- Row0 remains unchanged and exogenous.",
        "- No plaintext, translation, semantic reading, or case reopening is introduced.",
    ]
    md_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    result = make_result()
    write_result(result)
    print(json.dumps(result["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
