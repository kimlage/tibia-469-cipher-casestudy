from __future__ import annotations

import importlib.util
import json
import math
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"
AUTHORIAL = ROOT / "analysis" / "authorial_mechanism_20260620"

GATE37_SCRIPT = HERE / "scripts" / "37_cutoff60_source_state_reparse_prototype_gate.py"
GATE76_SCRIPT = HERE / "scripts" / "76_cutoff60_sparse_suffix_parser_gate.py"
GATE72 = TEST_RESULTS / "72_final_source_length_parser_feasibility_audit.json"
GATE76 = TEST_RESULTS / "76_cutoff60_sparse_suffix_parser_gate.json"
FINAL_FORMULA = (
    AUTHORIAL
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_targetmax_saturated_source_substitution_second_pass_partial_boundary_shift_second_pass_formula_469.json"
)
BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"

CUTOFFS = [10, 20, 35, 50, 60]


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


def load_parser_context_for_cutoff(cutoff: int) -> dict[str, Any]:
    gate37 = load_module("gate37_source_state_reparse", GATE37_SCRIPT)
    audit126 = gate37.load_module(f"audit126_cutoff_{cutoff}", gate37.AUDIT_126)
    audit137 = gate37.load_module(f"audit137_cutoff_{cutoff}", gate37.AUDIT_137)
    payload_module = gate37.load_module(
        f"payload_context_cutoff_{cutoff}", audit126.PAYLOAD_CONTEXT
    )
    copy_module = gate37.load_module(
        f"copy_context_cutoff_{cutoff}", audit126.COPY_CONTEXT
    )
    item_module = gate37.load_module(
        f"item_context_cutoff_{cutoff}", audit126.ITEM_CONTEXT
    )

    formula = load_json(FINAL_FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    copy_rows = copy_module.collect_copy_rows(formula, books)
    payload_rows = payload_module.collect_literal_digit_rows(formula, books)
    item_rows, item_stats = item_module.collect_item_rows(formula, books)
    if item_stats["forced_rule_violations"]:
        raise RuntimeError(item_stats["forced_rule_violations"])

    train_counts = audit126.train_counts_for_cutoff(
        cutoff=cutoff,
        formula=formula,
        copy_rows=copy_rows,
        payload_rows=payload_rows,
        item_rows=item_rows,
    )
    source_rows = audit137.collect_source_rows(formula, books)
    if source_rows["errors"]:
        raise RuntimeError(source_rows["errors"])
    source_train_counts = gate37.source_counts(
        [row for row in source_rows["rows"] if int(row["book"]) < cutoff],
        max_source_count=sum(len(text) for text in books.values()) + 1,
    )
    copy_prefixes = gate37.copy_length_prefix_counts(
        train_counts["copy"],
        max_length=max(len(text) for text in books.values()) + 1,
    )
    return {
        "gate37": gate37,
        "audit126": audit126,
        "formula": formula,
        "books": books,
        "train_counts": train_counts,
        "source_train_counts": source_train_counts,
        "copy_prefixes": copy_prefixes,
        "cutoff": cutoff,
    }


def run_cutoff(cutoff: int, gate76_module) -> dict[str, Any]:
    context = load_parser_context_for_cutoff(cutoff)
    gate37 = context["gate37"]
    formula = context["formula"]
    books = context["books"]
    available = "".join(books[str(index)] for index in range(cutoff))
    previous_end = gate37.previous_copy_end_before(formula, cutoff)
    rows = []
    start = time.perf_counter()
    for book in range(cutoff, 70):
        same_policy = gate76_module.same_policy_reprice_bits(
            context=context,
            book=book,
            available=available,
            initial_previous_copy_end=previous_end,
        )
        row = gate76_module.sparse_source_length_parse(
            context=context,
            book=book,
            available=available,
            initial_previous_copy_end=previous_end,
        )
        row["same_policy_reprice_bits"] = same_policy["bits"]
        row["same_policy_roundtrip_ok"] = same_policy["roundtrip_ok"]
        row["same_policy_final_previous_copy_end"] = same_policy[
            "final_previous_copy_end"
        ]
        row["parser_minus_same_policy_reprice_bits"] = (
            row["parser_bits"] - same_policy["bits"]
        )
        if not row["roundtrip_ok"]:
            raise RuntimeError({"cutoff": cutoff, "book": book, "type": "roundtrip"})
        if not row["same_policy_roundtrip_ok"]:
            raise RuntimeError(
                {"cutoff": cutoff, "book": book, "type": "same_policy_roundtrip"}
            )
        rows.append(row)
        available += books[str(book)]
        previous_end = row["final_previous_copy_end"]
    elapsed = time.perf_counter() - start
    parser_better_count = sum(
        1 for row in rows if row["parser_minus_same_policy_reprice_bits"] < -1e-9
    )
    parser_tie_count = sum(
        1
        for row in rows
        if abs(row["parser_minus_same_policy_reprice_bits"]) <= 1e-9
    )
    parser_worse_count = sum(
        1 for row in rows if row["parser_minus_same_policy_reprice_bits"] > 1e-9
    )
    return {
        "cutoff": cutoff,
        "target_books": [cutoff, 69],
        "target_book_count": len(rows),
        "roundtrip_book_count": sum(1 for row in rows if row["roundtrip_ok"]),
        "same_policy_roundtrip_book_count": sum(
            1 for row in rows if row["same_policy_roundtrip_ok"]
        ),
        "raw_positive_book_count": sum(
            1 for row in rows if row["gain_vs_raw_digit_uniform_bits"] > 0
        ),
        "parser_better_than_same_policy_count": parser_better_count,
        "parser_tie_same_policy_count": parser_tie_count,
        "parser_worse_than_same_policy_count": parser_worse_count,
        "elapsed_seconds": elapsed,
        "total_parser_bits": sum(row["parser_bits"] for row in rows),
        "total_same_policy_reprice_bits": sum(
            row["same_policy_reprice_bits"] for row in rows
        ),
        "total_parser_minus_same_policy_reprice_bits": sum(
            row["parser_minus_same_policy_reprice_bits"] for row in rows
        ),
        "total_raw_digit_uniform_bits": sum(row["raw_digit_uniform_bits"] for row in rows),
        "total_gain_vs_raw_digit_uniform_bits": sum(
            row["gain_vs_raw_digit_uniform_bits"] for row in rows
        ),
        "total_transition_evaluations": sum(
            row["transition_evaluations"] for row in rows
        ),
        "total_visited_states": sum(row["visited_state_count"] for row in rows),
        "max_transition_book": max(rows, key=lambda row: row["transition_evaluations"])[
            "book"
        ],
        "max_transition_evaluations": max(
            row["transition_evaluations"] for row in rows
        ),
        "book_rows": rows,
    }


def make_result() -> dict[str, Any]:
    gate72 = load_json(GATE72)
    gate76 = load_json(GATE76)
    assert_boundary("final_source_length_parser_feasibility", gate72)
    assert_boundary("cutoff60_sparse_suffix_parser", gate76)
    gate76_module = load_module("gate76_sparse_suffix_parser", GATE76_SCRIPT)

    start = time.perf_counter()
    cutoff_rows = [run_cutoff(cutoff, gate76_module) for cutoff in CUTOFFS]
    elapsed = time.perf_counter() - start
    total_books = sum(row["target_book_count"] for row in cutoff_rows)
    total_roundtrip = sum(row["roundtrip_book_count"] for row in cutoff_rows)
    total_same_policy_roundtrip = sum(
        row["same_policy_roundtrip_book_count"] for row in cutoff_rows
    )
    total_raw_positive = sum(row["raw_positive_book_count"] for row in cutoff_rows)
    total_parser_worse = sum(
        row["parser_worse_than_same_policy_count"] for row in cutoff_rows
    )
    classification = (
        "multi_cutoff_sparse_suffix_parser_roundtrips"
        if total_roundtrip == total_books and total_same_policy_roundtrip == total_books
        else "multi_cutoff_sparse_suffix_parser_mixed"
    )
    return {
        "schema": "multi_cutoff_sparse_suffix_parser_validation.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "final_formula": rel(FINAL_FORMULA),
            "books_digits": rel(BOOKS_DIGITS),
            "gate37_parser_helpers": rel(GATE37_SCRIPT),
            "gate76_sparse_parser": rel(GATE76_SCRIPT),
            "gate72_feasibility": rel(GATE72),
            "gate76_cutoff60_suffix": rel(GATE76),
        },
        "scope": {
            "analysis_only": True,
            "cutoffs": CUTOFFS,
            "sequential_previous_end_carried_between_books": True,
            "train_counts_frozen_per_cutoff": True,
            "compression_bound_changed": False,
            "new_formula_emitted": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
        },
        "summary": {
            "cutoff_count": len(CUTOFFS),
            "total_suffix_book_evaluations": total_books,
            "total_roundtrip_book_evaluations": total_roundtrip,
            "total_same_policy_roundtrip_book_evaluations": total_same_policy_roundtrip,
            "total_raw_positive_book_evaluations": total_raw_positive,
            "total_parser_better_than_same_policy_count": sum(
                row["parser_better_than_same_policy_count"] for row in cutoff_rows
            ),
            "total_parser_tie_same_policy_count": sum(
                row["parser_tie_same_policy_count"] for row in cutoff_rows
            ),
            "total_parser_worse_than_same_policy_count": total_parser_worse,
            "total_elapsed_seconds": elapsed,
            "total_parser_bits": sum(row["total_parser_bits"] for row in cutoff_rows),
            "total_same_policy_reprice_bits": sum(
                row["total_same_policy_reprice_bits"] for row in cutoff_rows
            ),
            "total_parser_minus_same_policy_reprice_bits": sum(
                row["total_parser_minus_same_policy_reprice_bits"]
                for row in cutoff_rows
            ),
            "total_raw_digit_uniform_bits": sum(
                row["total_raw_digit_uniform_bits"] for row in cutoff_rows
            ),
            "total_gain_vs_raw_digit_uniform_bits": sum(
                row["total_gain_vs_raw_digit_uniform_bits"] for row in cutoff_rows
            ),
            "total_transition_evaluations": sum(
                row["total_transition_evaluations"] for row in cutoff_rows
            ),
            "total_visited_states": sum(
                row["total_visited_states"] for row in cutoff_rows
            ),
            "max_transition_cutoff": max(
                cutoff_rows, key=lambda row: row["max_transition_evaluations"]
            )["cutoff"],
            "max_transition_book": max(
                cutoff_rows, key=lambda row: row["max_transition_evaluations"]
            )["max_transition_book"],
            "max_transition_evaluations": max(
                row["max_transition_evaluations"] for row in cutoff_rows
            ),
            "cutoff_rows": cutoff_rows,
            "interpretation": (
                "Sparse source/length parsing now roundtrips every tested "
                "future suffix for cutoffs 10, 20, 35, 50, and 60 with train "
                "counts frozen at each prefix and previous-copy-end state "
                "carried online. This is stronger predictive/parser evidence, "
                "including a small aggregate improvement over same-policy "
                "reprice with no worse suffix cells. It does not promote a new "
                "compression bound or authorial final method because the rows "
                "are overlapping validation cuts rather than one charged "
                "corpus recipe."
            ),
        },
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "source_length_parser_status": "multi_cutoff_sparse_suffix_parser_executable",
            "generation_explanation_status": "predictive_parser_validation_strengthened_not_final_method",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / "77_multi_cutoff_sparse_suffix_parser_validation.json"
    md_path = TEST_RESULTS / "77_multi_cutoff_sparse_suffix_parser_validation.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    lines = [
        "# Multi-Cutoff Sparse Suffix Parser Validation",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 76 proved the sparse source/length parser on the cutoff-60 suffix.",
        "This gate repeats the same sequential suffix parse at cutoffs `10`,",
        "`20`, `35`, `50`, and `60`, freezing train counts at each prefix and",
        "carrying `previous_copy_end` between held-out books.",
        "",
        "## Summary",
        "",
        f"- Cutoffs: `{', '.join(map(str, CUTOFFS))}`.",
        f"- Suffix book evaluations: `{s['total_suffix_book_evaluations']}`.",
        f"- Roundtrip evaluations: `{s['total_roundtrip_book_evaluations']}/{s['total_suffix_book_evaluations']}`.",
        f"- Same-policy roundtrip evaluations: `{s['total_same_policy_roundtrip_book_evaluations']}/{s['total_suffix_book_evaluations']}`.",
        f"- Raw-positive evaluations: `{s['total_raw_positive_book_evaluations']}/{s['total_suffix_book_evaluations']}`.",
        f"- Parser better/tie/worse than same policy: `{s['total_parser_better_than_same_policy_count']}` / `{s['total_parser_tie_same_policy_count']}` / `{s['total_parser_worse_than_same_policy_count']}`.",
        f"- Total parser bits: `{s['total_parser_bits']:.6f}`.",
        f"- Total same-policy reprice bits: `{s['total_same_policy_reprice_bits']:.6f}`.",
        f"- Parser minus same-policy reprice: `{s['total_parser_minus_same_policy_reprice_bits']:+.6f}` bits.",
        f"- Total raw-uniform gain: `{s['total_gain_vs_raw_digit_uniform_bits']:.3f}` bits.",
        f"- Total transition evaluations: `{s['total_transition_evaluations']}`.",
        f"- Total visited states: `{s['total_visited_states']}`.",
        f"- Hardest parsed cell: cutoff `{s['max_transition_cutoff']}`, book `{s['max_transition_book']}`, `{s['max_transition_evaluations']}` transitions.",
        f"- Elapsed wall time: `{s['total_elapsed_seconds']:.3f}` seconds.",
        "",
        "## Cutoff Rows",
        "",
        "| Cutoff | Books | Roundtrip | Raw-positive | Parser bits | Same-policy | Delta | Transitions | Max book | Seconds |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in s["cutoff_rows"]:
        lines.append(
            "| {cutoff} | {target_book_count} | {roundtrip_book_count}/{target_book_count} | {raw_positive_book_count}/{target_book_count} | {total_parser_bits:.3f} | {total_same_policy_reprice_bits:.3f} | {total_parser_minus_same_policy_reprice_bits:+.3f} | {total_transition_evaluations} | {max_transition_book} | {elapsed_seconds:.3f} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- {s['interpretation']}",
            "- No compression-bound change is introduced.",
            "- No corpus-wide formula promotion is introduced.",
            "- Row0 remains unchanged and exogenous.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        ]
    )
    md_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    result = make_result()
    write_result(result)
    print(json.dumps(result["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
