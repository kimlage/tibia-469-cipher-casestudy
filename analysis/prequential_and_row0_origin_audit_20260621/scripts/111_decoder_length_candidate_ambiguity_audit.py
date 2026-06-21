from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

GATE88_SCRIPT = HERE / "scripts" / "88_decoder_side_rule_coverage_audit.py"
GATE88 = TEST_RESULTS / "88_decoder_side_rule_coverage_audit.json"
GATE100 = TEST_RESULTS / "100_skeleton_rule_coverage_audit.json"
GATE110 = TEST_RESULTS / "110_operation_length_dependency_ledger.json"
BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
OUT_STEM = "111_decoder_length_candidate_ambiguity_audit"
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


def percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = (len(ordered) - 1) * q
    lower = int(math.floor(index))
    upper = int(math.ceil(index))
    if lower == upper:
        return ordered[lower]
    return ordered[lower] * (upper - index) + ordered[upper] * (index - lower)


def summarize_ints(values: list[int]) -> dict[str, float | int | None]:
    if not values:
        return {"n": 0, "min": None, "median": None, "mean": None, "max": None}
    return {
        "n": len(values),
        "min": min(values),
        "median": percentile([float(v) for v in values], 0.5),
        "mean": sum(values) / len(values),
        "max": max(values),
    }


def make_copy_rows() -> list[dict[str, Any]]:
    helper88 = load_module("gate88_for_gate111", GATE88_SCRIPT)
    gate86 = helper88.load_module("gate86_for_gate111", helper88.GATE86_SCRIPT)
    gate82 = gate86.load_module("gate82_for_gate111", gate86.GATE82_SCRIPT)
    gate77 = gate82.load_module("gate77_for_gate111", gate82.GATE77_SCRIPT)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    canonical_rows = helper88.stable_projection_rows(gate86, gate82, gate77)
    return helper88.collect_copy_rule_rows(
        canonical_rows=canonical_rows,
        books=books,
        min_len=MIN_COPY_LEN,
    )


def candidate_count_summary(values: list[int]) -> dict[str, Any]:
    total_log2 = sum(math.log2(value) for value in values if value > 0)
    forced = sum(1 for value in values if value == 1)
    return {
        **summarize_ints(values),
        "forced_count": forced,
        "ambiguous_count": len(values) - forced,
        "total_log2_candidate_space": total_log2,
    }


def make_result() -> dict[str, Any]:
    gate88 = load_json(GATE88)
    gate100 = load_json(GATE100)
    gate110 = load_json(GATE110)
    for name, data in [
        ("decoder_side_rule_coverage", gate88),
        ("skeleton_rule_coverage", gate100),
        ("operation_length_dependency", gate110),
    ]:
        assert_boundary(name, data)

    if gate88["classification"] != "decoder_side_rule_coverage_insufficient":
        raise RuntimeError("gate88 no longer rejects decoder-side rules")
    if gate100["summary"]["copy_count"] != gate88["summary"]["projection_copy_event_count"]:
        raise RuntimeError("copy counts differ between gate100 and gate88")
    if gate110["classification"] != "operation_length_dependency_retained":
        raise RuntimeError("gate110 no longer retains length dependency")

    copy_rows = make_copy_rows()
    if len(copy_rows) != gate100["summary"]["copy_count"]:
        raise RuntimeError({"copy_rows": len(copy_rows), "gate100": gate100["summary"]["copy_count"]})

    literal_rows = [
        row for row in gate100["skeleton_rows"] if row["type"] == "literal"
    ]
    if len(literal_rows) != gate100["summary"]["literal_count"]:
        raise RuntimeError(
            {"literal_rows": len(literal_rows), "gate100": gate100["summary"]["literal_count"]}
        )

    copy_candidate_counts = []
    copy_candidate_rows = []
    for row in copy_rows:
        decoder_max = int(row["decoder_max_possible_after_declared_source"])
        candidate_count = max(0, decoder_max - MIN_COPY_LEN + 1)
        if candidate_count <= 0:
            raise RuntimeError({"type": "no_copy_length_candidate", "row": row})
        declared = int(row["length"])
        copy_candidate_counts.append(candidate_count)
        copy_candidate_rows.append(
            {
                "book": int(row["book"]),
                "op_index": int(row["op_index"]),
                "declared_length": declared,
                "decoder_max_possible_after_declared_source": decoder_max,
                "candidate_count_granting_source": candidate_count,
                "declared_is_min_len": declared == MIN_COPY_LEN,
                "declared_is_decoder_max": declared == decoder_max,
                "declared_is_forced_by_candidate_set": candidate_count == 1,
            }
        )

    literal_candidate_counts = []
    literal_candidate_rows = []
    for row in literal_rows:
        remaining = int(row["remaining"])
        declared = int(row["length"])
        candidate_count = remaining
        if candidate_count <= 0:
            raise RuntimeError({"type": "no_literal_length_candidate", "row": row})
        literal_candidate_counts.append(candidate_count)
        literal_candidate_rows.append(
            {
                "book": int(row["book"]),
                "op_index": int(row["op_index"]),
                "declared_length": declared,
                "remaining_book_digits": remaining,
                "candidate_count_granting_type": candidate_count,
                "declared_is_remaining": declared == remaining,
                "declared_is_forced_by_candidate_set": candidate_count == 1,
            }
        )

    all_candidate_counts = copy_candidate_counts + literal_candidate_counts
    copy_summary = candidate_count_summary(copy_candidate_counts)
    literal_summary = candidate_count_summary(literal_candidate_counts)
    all_summary = candidate_count_summary(all_candidate_counts)
    copy_decoder_max_hits = sum(
        1 for row in copy_candidate_rows if row["declared_is_decoder_max"]
    )
    literal_remaining_hits = sum(
        1 for row in literal_candidate_rows if row["declared_is_remaining"]
    )

    promotes_length_generator = (
        all_summary["forced_count"] == len(all_candidate_counts)
        and gate88["summary"]["decoder_joint_covers_all"] is True
    )

    return {
        "schema": "decoder_length_candidate_ambiguity_audit.v1",
        "classification": "decoder_length_candidates_ambiguous_dependency_retained",
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "gate88_decoder_side_rule_coverage": rel(GATE88),
            "gate100_skeleton_rule_coverage": rel(GATE100),
            "gate110_operation_length_dependency": rel(GATE110),
            "books_digits": rel(BOOKS_DIGITS),
        },
        "scope": {
            "analysis_only": True,
            "ambiguity_ledger_only": True,
            "compression_bound_changed": False,
            "new_formula_emitted": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
            "generous_assumption_for_copy_rows": "op_type_and_copy_source_granted",
            "generous_assumption_for_literal_rows": "op_type_granted_payload_unknown",
        },
        "summary": {
            "operation_count": gate100["summary"]["op_count"],
            "copy_count": len(copy_candidate_counts),
            "literal_count": len(literal_candidate_counts),
            "copy_candidate_count_summary": copy_summary,
            "literal_candidate_count_summary": literal_summary,
            "all_candidate_count_summary": all_summary,
            "copy_declared_decoder_max_hits": copy_decoder_max_hits,
            "copy_declared_decoder_max_fraction": copy_decoder_max_hits
            / len(copy_candidate_counts),
            "literal_declared_remaining_hits": literal_remaining_hits,
            "literal_declared_remaining_fraction": literal_remaining_hits
            / len(literal_candidate_counts),
            "forced_length_count_under_generous_assumptions": all_summary[
                "forced_count"
            ],
            "ambiguous_length_count_under_generous_assumptions": all_summary[
                "ambiguous_count"
            ],
            "total_log2_candidate_space_under_generous_assumptions": all_summary[
                "total_log2_candidate_space"
            ],
            "promotes_length_generator": promotes_length_generator,
            "interpretation": (
                "Even under generous decoder assumptions, operation lengths are "
                "not forced. For copy operations this audit grants the declared "
                "source and op type, then counts every syntactically possible "
                "length from min_len to decoder_max. For literal operations it "
                "grants op type but not payload, so every positive remaining "
                "length is possible. The resulting candidate sets remain widely "
                "ambiguous, so the length atlas cannot be replaced by a forced "
                "decoder-side rule at this frontier."
            ),
        },
        "sample_rows": {
            "largest_copy_candidate_sets": sorted(
                copy_candidate_rows,
                key=lambda row: (
                    row["candidate_count_granting_source"],
                    row["book"],
                    row["op_index"],
                ),
                reverse=True,
            )[:10],
            "largest_literal_candidate_sets": sorted(
                literal_candidate_rows,
                key=lambda row: (
                    row["candidate_count_granting_type"],
                    row["book"],
                    row["op_index"],
                ),
                reverse=True,
            )[:10],
        },
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": "length_candidate_ambiguity_blocks_generator_promotion",
            "skeleton_status": "length_sequence_not_forced_even_with_type_and_source_granted",
            "source_dependency_status": "retained_declared_dependency",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    json_path = TEST_RESULTS / f"{OUT_STEM}.json"
    md_path = TEST_RESULTS / f"{OUT_STEM}.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    copy = s["copy_candidate_count_summary"]
    literal = s["literal_candidate_count_summary"]
    all_rows = s["all_candidate_count_summary"]
    lines = [
        "# Decoder Length Candidate Ambiguity Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 110 showed that the length atlas remains the blocker. This audit",
        "tests a generous decoder-side question: if operation type is granted, and",
        "copy source is also granted for copy rows, are the operation lengths",
        "forced by syntax and remaining capacity?",
        "",
        "## Assumptions",
        "",
        "- Copy rows: op type and declared source are granted; candidate lengths are `min_len..decoder_max`.",
        "- Literal rows: op type is granted and payload is unknown; candidate lengths are `1..remaining`.",
        "- This is an ambiguity ledger, not a compression model or new formula.",
        "",
        "## Candidate Counts",
        "",
        "| Scope | Rows | Forced | Ambiguous | Min | Median | Mean | Max | log2 candidate space |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        f"| Copy | `{copy['n']}` | `{copy['forced_count']}` | `{copy['ambiguous_count']}` | `{copy['min']}` | `{copy['median']:.3f}` | `{copy['mean']:.3f}` | `{copy['max']}` | `{copy['total_log2_candidate_space']:.3f}` |",
        f"| Literal | `{literal['n']}` | `{literal['forced_count']}` | `{literal['ambiguous_count']}` | `{literal['min']}` | `{literal['median']:.3f}` | `{literal['mean']:.3f}` | `{literal['max']}` | `{literal['total_log2_candidate_space']:.3f}` |",
        f"| All | `{all_rows['n']}` | `{all_rows['forced_count']}` | `{all_rows['ambiguous_count']}` | `{all_rows['min']}` | `{all_rows['median']:.3f}` | `{all_rows['mean']:.3f}` | `{all_rows['max']}` | `{all_rows['total_log2_candidate_space']:.3f}` |",
        "",
        "## Declared-Length Diagnostics",
        "",
        f"- Copy declared length equals decoder max: `{s['copy_declared_decoder_max_hits']}/{s['copy_count']}`.",
        f"- Literal declared length equals remaining book suffix: `{s['literal_declared_remaining_hits']}/{s['literal_count']}`.",
        f"- Forced length count under generous assumptions: `{s['forced_length_count_under_generous_assumptions']}/{s['operation_count']}`.",
        f"- Ambiguous length count under generous assumptions: `{s['ambiguous_length_count_under_generous_assumptions']}/{s['operation_count']}`.",
        "",
        "## Decision",
        "",
        f"- Promotes length generator: `{s['promotes_length_generator']}`.",
        f"- {s['interpretation']}",
        "- No compression-bound change is introduced.",
        "- No formula is emitted.",
        "- Row0 remains unchanged and exogenous.",
        "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        "",
    ]
    md_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    result = make_result()
    write_result(result)
    print(json.dumps(result["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
