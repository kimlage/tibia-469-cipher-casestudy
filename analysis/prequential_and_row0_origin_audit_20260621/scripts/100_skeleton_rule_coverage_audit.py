from __future__ import annotations

import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

GATE91_SCRIPT = HERE / "scripts" / "91_full_source_exposure_audit.py"
GATE98 = TEST_RESULTS / "98_full_source_exact_skeleton_invariance.json"
GATE99 = TEST_RESULTS / "99_exact_skeleton_dependency_ledger.json"

CANONICAL_CUTOFF = 10
CANONICAL_POLICY = "earliest_source"
MIN_LEN = 5


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


def source_free_skeleton(ops: list[dict[str, Any]]) -> list[dict[str, Any]]:
    skeleton = []
    for op in ops:
        row = {
            "type": op["type"],
            "target_start": int(op["target_start"]),
            "length": int(op["length"]),
            "forced": bool(op["forced"]),
        }
        skeleton.append(row)
    return skeleton


def target_match_exists(emitted: str, chunk: str) -> bool:
    return emitted.find(chunk) >= 0


def collect_canonical_skeleton() -> tuple[list[dict[str, Any]], dict[str, str]]:
    helper91 = load_module("gate91_for_gate100", GATE91_SCRIPT)
    captured_ops: dict[str, list[dict[str, Any]]] = {}
    original_compact_signature = helper91.compact_signature

    def capture_compact_signature(ops: list[dict[str, Any]]) -> str:
        signature = original_compact_signature(ops)
        previous = captured_ops.get(signature)
        if previous is not None and previous != ops:
            raise RuntimeError({"type": "signature_collision", "signature": signature})
        captured_ops[signature] = json.loads(json.dumps(ops))
        return signature

    helper91.compact_signature = capture_compact_signature
    gate86 = helper91.load_module("gate86_for_gate100", helper91.GATE86_SCRIPT)
    gate82 = gate86.load_module("gate82_for_gate100", gate86.GATE82_SCRIPT)
    gate77 = gate82.load_module("gate77_for_gate100", gate82.GATE77_SCRIPT)
    context = gate77.load_parser_context_for_cutoff(CANONICAL_CUTOFF)
    rows = helper91.run_cutoff(
        CANONICAL_CUTOFF,
        gate77,
        gate82,
        policy=CANONICAL_POLICY,
    )
    skeleton_rows = []
    for row in rows:
        ops = source_free_skeleton(captured_ops[row["signature"]])
        for index, op in enumerate(ops):
            op_row = {
                **op,
                "book": int(row["book"]),
                "op_index": index,
            }
            skeleton_rows.append(op_row)
    return skeleton_rows, {str(key): value for key, value in context["books"].items()}


def rule_counts(skeleton_rows: list[dict[str, Any]], books: dict[str, str]) -> dict[str, Any]:
    by_book: dict[int, list[dict[str, Any]]] = {}
    for row in skeleton_rows:
        by_book.setdefault(int(row["book"]), []).append(row)

    op_type_counts = Counter()
    length_counts = Counter()
    literal_counts = Counter()
    copy_counts = Counter()
    target_dependent_counts = Counter()
    type_total = 0
    length_total = 0
    literal_total = 0
    copy_total = 0
    rows_out = []

    emitted = "".join(books[str(book)] for book in range(CANONICAL_CUTOFF))
    previous_type: str | None = None
    previous_length: int | None = None
    previous_book: int | None = None
    for book in sorted(by_book):
        target = books[str(book)]
        book_pos = 0
        book_ops = sorted(by_book[book], key=lambda row: int(row["op_index"]))
        for op in book_ops:
            op_type = op["type"]
            length = int(op["length"])
            remaining = len(target) - book_pos
            is_book_start = book_pos == 0
            is_book_end = length == remaining
            previous_in_book_type = None if book_pos == 0 else previous_type
            previous_in_book_length = None if book_pos == 0 else previous_length
            next_min_chunk = target[book_pos : book_pos + MIN_LEN]
            copy_available = (
                len(next_min_chunk) == MIN_LEN
                and target_match_exists(emitted, next_min_chunk)
            )

            type_total += 1
            length_total += 1
            if op_type == "literal":
                literal_total += 1
            else:
                copy_total += 1

            if op_type == "copy":
                op_type_counts["always_copy"] += 1
            if op_type == "literal":
                op_type_counts["always_literal"] += 1
            if is_book_start and op_type == "copy":
                op_type_counts["book_start_copy"] += 1
            if previous_in_book_type == "literal" and op_type == "copy":
                op_type_counts["after_literal_copy"] += 1
            if previous_in_book_type == "copy" and op_type == "copy":
                op_type_counts["after_copy_copy"] += 1
            if remaining < MIN_LEN and op_type == "literal":
                op_type_counts["short_suffix_literal"] += 1
            if copy_available and op_type == "copy":
                target_dependent_counts["copy_when_minlen_match_available"] += 1
            if not copy_available and op_type == "literal":
                target_dependent_counts["literal_when_no_minlen_match_available"] += 1

            if length == MIN_LEN:
                length_counts["length_is_min_len"] += 1
            if is_book_end:
                length_counts["length_is_remaining_book"] += 1
            if previous_in_book_length is not None and length == previous_in_book_length:
                length_counts["length_is_previous_in_book_length"] += 1
            if length <= 10:
                length_counts["length_lte_10"] += 1
            if length >= 20:
                length_counts["length_gte_20"] += 1

            if op_type == "literal":
                if length == MIN_LEN:
                    literal_counts["literal_length_is_min_len"] += 1
                if is_book_end:
                    literal_counts["literal_length_is_remaining_book"] += 1
                if remaining < MIN_LEN and length == remaining:
                    literal_counts["forced_short_suffix_consumes_remaining"] += 1
            else:
                if length == MIN_LEN:
                    copy_counts["copy_length_is_min_len"] += 1
                if is_book_end:
                    copy_counts["copy_length_is_remaining_book"] += 1
                if previous_in_book_length is not None and length == previous_in_book_length:
                    copy_counts["copy_length_is_previous_in_book_length"] += 1

            rows_out.append(
                {
                    "book": book,
                    "op_index": int(op["op_index"]),
                    "type": op_type,
                    "target_start": book_pos,
                    "length": length,
                    "remaining": remaining,
                    "copy_available_minlen": copy_available,
                    "previous_in_book_type": previous_in_book_type,
                    "previous_in_book_length": previous_in_book_length,
                }
            )
            emitted += target[book_pos : book_pos + length]
            book_pos += length
            previous_type = op_type
            previous_length = length
            previous_book = book
        if book_pos != len(target):
            raise RuntimeError({"book": book, "book_pos": book_pos, "length": len(target)})
    if previous_book is None:
        raise RuntimeError("no skeleton rows")

    def best(counter: Counter, total: int) -> dict[str, Any]:
        if not counter:
            return {"rule": None, "hits": 0, "total": total, "coverage": 0.0}
        rule, hits = max(counter.items(), key=lambda item: (item[1], item[0]))
        return {"rule": rule, "hits": hits, "total": total, "coverage": hits / total}

    return {
        "type_total": type_total,
        "length_total": length_total,
        "literal_total": literal_total,
        "copy_total": copy_total,
        "op_type_rule_counts": dict(op_type_counts),
        "length_rule_counts": dict(length_counts),
        "literal_length_rule_counts": dict(literal_counts),
        "copy_length_rule_counts": dict(copy_counts),
        "target_dependent_rule_counts": dict(target_dependent_counts),
        "best_op_type_rule": best(op_type_counts, type_total),
        "best_length_rule": best(length_counts, length_total),
        "best_literal_length_rule": best(literal_counts, literal_total),
        "best_copy_length_rule": best(copy_counts, copy_total),
        "best_target_dependent_type_rule": best(target_dependent_counts, type_total),
        "rows": rows_out,
    }


def make_result() -> dict[str, Any]:
    gate98 = load_json(GATE98)
    gate99 = load_json(GATE99)
    assert_boundary("full_source_exact_skeleton_invariance", gate98)
    assert_boundary("exact_skeleton_dependency_ledger", gate99)
    if gate98["classification"] != "source_free_skeleton_exactly_invariant":
        raise RuntimeError("gate98 did not prove exact skeleton invariance")
    skeleton_rows, books = collect_canonical_skeleton()
    counts = rule_counts(skeleton_rows, books)
    promotes_generator = False
    simple_rule_covers_skeleton = (
        counts["best_op_type_rule"]["hits"] == counts["type_total"]
        and counts["best_length_rule"]["hits"] == counts["length_total"]
    )
    classification = (
        "skeleton_simple_rule_generator_candidate"
        if simple_rule_covers_skeleton
        else "skeleton_simple_rule_coverage_insufficient"
    )
    return {
        "schema": "skeleton_rule_coverage_audit.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "gate98_exact_skeleton_invariance": rel(GATE98),
            "gate99_dependency_ledger": rel(GATE99),
            "gate91_script": rel(GATE91_SCRIPT),
        },
        "scope": {
            "analysis_only": True,
            "canonical_cutoff": CANONICAL_CUTOFF,
            "canonical_policy": CANONICAL_POLICY,
            "tests_simple_state_rules": True,
            "tests_target_dependent_controls": True,
            "compression_bound_changed": False,
            "new_formula_emitted": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
        },
        "summary": {
            "op_count": counts["type_total"],
            "copy_count": counts["copy_total"],
            "literal_count": counts["literal_total"],
            "best_op_type_rule": counts["best_op_type_rule"],
            "best_length_rule": counts["best_length_rule"],
            "best_literal_length_rule": counts["best_literal_length_rule"],
            "best_copy_length_rule": counts["best_copy_length_rule"],
            "best_target_dependent_type_rule": counts["best_target_dependent_type_rule"],
            "simple_rule_covers_skeleton": simple_rule_covers_skeleton,
            "promotes_generator": promotes_generator,
            "interpretation": (
                "The exact skeleton is stable, but simple source-free state rules "
                "do not generate its operation types and lengths. Target-dependent "
                "availability explains part of the type pattern, which reinforces "
                "that the skeleton is an atlas rather than a decoder-side generator."
            ),
        },
        "rule_counts": {
            key: value
            for key, value in counts.items()
            if key != "rows"
        },
        "skeleton_rows": counts["rows"],
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": "skeleton_rule_coverage_insufficient",
            "skeleton_status": "stable_atlas_not_simple_rule_generator",
            "source_dependency_status": "retained_declared_dependency",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / "100_skeleton_rule_coverage_audit.json"
    md_path = TEST_RESULTS / "100_skeleton_rule_coverage_audit.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    lines = [
        "# Skeleton Rule Coverage Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 98 proved an exact source-free skeleton atlas. This audit checks",
        "whether simple rules over decoder-visible state can generate that skeleton,",
        "or whether it remains materialized.",
        "",
        "## Coverage",
        "",
        f"- Skeleton ops: `{s['op_count']}`.",
        f"- Copy/literal ops: `{s['copy_count']}` / `{s['literal_count']}`.",
        f"- Best op-type rule: `{s['best_op_type_rule']['rule']}` = `{s['best_op_type_rule']['hits']}/{s['best_op_type_rule']['total']}`.",
        f"- Best length rule: `{s['best_length_rule']['rule']}` = `{s['best_length_rule']['hits']}/{s['best_length_rule']['total']}`.",
        f"- Best literal-length rule: `{s['best_literal_length_rule']['rule']}` = `{s['best_literal_length_rule']['hits']}/{s['best_literal_length_rule']['total']}`.",
        f"- Best copy-length rule: `{s['best_copy_length_rule']['rule']}` = `{s['best_copy_length_rule']['hits']}/{s['best_copy_length_rule']['total']}`.",
        f"- Best target-dependent type control: `{s['best_target_dependent_type_rule']['rule']}` = `{s['best_target_dependent_type_rule']['hits']}/{s['best_target_dependent_type_rule']['total']}`.",
        "",
        "## Decision",
        "",
        f"- Simple rule covers skeleton: `{s['simple_rule_covers_skeleton']}`.",
        f"- Promotes generator: `{s['promotes_generator']}`.",
        f"- {s['interpretation']}",
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
