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

FINAL_FORMULA = (
    AUTHORIAL
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_targetmax_saturated_source_substitution_second_pass_partial_boundary_shift_second_pass_formula_469.json"
)
BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
GATE37_SCRIPT = HERE / "scripts" / "37_cutoff60_source_state_reparse_prototype_gate.py"
GATE72 = TEST_RESULTS / "72_final_source_length_parser_feasibility_audit.json"

CUTOFF = 60
TARGET_BOOKS = [67, 60]
HARD_BOOK = 66


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


def load_parser_context() -> dict[str, Any]:
    gate37 = load_module("gate37_source_state_reparse", GATE37_SCRIPT)
    audit126 = gate37.load_module("audit126", gate37.AUDIT_126)
    audit137 = gate37.load_module("audit137", gate37.AUDIT_137)
    payload_module = gate37.load_module("payload_context", audit126.PAYLOAD_CONTEXT)
    copy_module = gate37.load_module("copy_context", audit126.COPY_CONTEXT)
    item_module = gate37.load_module("item_context", audit126.ITEM_CONTEXT)

    formula = load_json(FINAL_FORMULA)
    books = {str(k): v for k, v in load_json(BOOKS_DIGITS).items()}
    copy_rows = copy_module.collect_copy_rows(formula, books)
    payload_rows = payload_module.collect_literal_digit_rows(formula, books)
    item_rows, item_stats = item_module.collect_item_rows(formula, books)
    if item_stats["forced_rule_violations"]:
        raise RuntimeError(item_stats["forced_rule_violations"])
    train_counts = audit126.train_counts_for_cutoff(
        cutoff=CUTOFF,
        formula=formula,
        copy_rows=copy_rows,
        payload_rows=payload_rows,
        item_rows=item_rows,
    )
    source_rows = audit137.collect_source_rows(formula, books)
    if source_rows["errors"]:
        raise RuntimeError(source_rows["errors"])
    source_train_counts = gate37.source_counts(
        [row for row in source_rows["rows"] if int(row["book"]) < CUTOFF],
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
    }


def available_before_book(books: dict[str, str], book: int) -> str:
    return "".join(books[str(index)] for index in range(book))


def active_formula_book_bits(
    *,
    context: dict[str, Any],
    book: int,
) -> float:
    formula = context["formula"]
    books = context["books"]
    gate37 = context["gate37"]
    audit126 = context["audit126"]
    available = available_before_book(books, book)
    encoded = audit126.encode_book_frozen_reparse(
        book=str(book),
        text=books[str(book)],
        available=available,
        formula=formula,
        train_counts=context["train_counts"],
    )
    # This is a same-policy comparator, not the fixed active recipe cost.
    repriced = gate37.reprice_encoded_book_source_state(
        encoded=encoded,
        available=available,
        formula=formula,
        source_train_counts=context["source_train_counts"],
        initial_previous_copy_end=gate37.previous_copy_end_before(formula, book),
    )
    return float(encoded["bits"]) - float(encoded["copy_address_bits"]) + float(
        repriced["source_bits"]
    )


def run_book_probe(context: dict[str, Any], book: int) -> dict[str, Any]:
    gate37 = context["gate37"]
    books = context["books"]
    formula = context["formula"]
    start = time.perf_counter()
    result = gate37.active_source_state_reparse_book(
        book=str(book),
        text=books[str(book)],
        available=available_before_book(books, book),
        formula=formula,
        train_counts=context["train_counts"],
        source_train_counts=context["source_train_counts"],
        copy_length_prefixes=context["copy_prefixes"],
        initial_previous_copy_end=gate37.previous_copy_end_before(formula, book),
        audit126=context["audit126"],
    )
    elapsed = time.perf_counter() - start
    raw_bits = len(books[str(book)]) * math.log2(10)
    same_policy_reprice_bits = active_formula_book_bits(context=context, book=book)
    return {
        "book": book,
        "book_digits": len(books[str(book)]),
        "elapsed_seconds": elapsed,
        "roundtrip_ok": result["validation"]["roundtrip_ok"],
        "errors": result["validation"]["errors"],
        "parser_bits": float(result["bits"]),
        "same_policy_reprice_bits": same_policy_reprice_bits,
        "parser_minus_same_policy_reprice_bits": float(result["bits"])
        - same_policy_reprice_bits,
        "raw_digit_uniform_bits": raw_bits,
        "gain_vs_raw_digit_uniform_bits": raw_bits - float(result["bits"]),
        "op_count": len(result["ops"]),
        "literal_runs": result["literal_runs"],
        "literal_digits": result["literal_digits"],
        "copy_items": result["copy_items"],
        "copied_digits": result["copied_digits"],
        "source_default_count": result["source_default_count"],
        "source_exception_count": result["source_exception_count"],
        "state_evaluations": result["state_evaluations"],
        "transition_evaluations": result["transition_evaluations"],
        "previous_end_domain_size": result["previous_end_domain_size"],
        "final_previous_copy_end": result["final_previous_copy_end"],
    }


def make_result() -> dict[str, Any]:
    gate72 = load_json(GATE72)
    assert_boundary("final_source_length_parser_feasibility_audit", gate72)
    context = load_parser_context()
    rows = [run_book_probe(context, book) for book in TARGET_BOOKS]
    hard_proxy = next(
        row
        for row in gate72["book_rows_by_cutoff"][str(CUTOFF)]
        if int(row["book"]) == HARD_BOOK
    )
    all_roundtrip = all(row["roundtrip_ok"] for row in rows)
    all_raw_positive = all(row["gain_vs_raw_digit_uniform_bits"] > 0 for row in rows)
    classification = (
        "book_local_source_length_parser_probe_roundtrips_subset"
        if all_roundtrip and all_raw_positive
        else "book_local_source_length_parser_probe_mixed"
    )
    return {
        "schema": "book_local_source_length_parser_probe.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "final_formula": rel(FINAL_FORMULA),
            "books_digits": rel(BOOKS_DIGITS),
            "gate37_parser": rel(GATE37_SCRIPT),
            "gate72_feasibility": rel(GATE72),
        },
        "scope": {
            "analysis_only": True,
            "cutoff": CUTOFF,
            "target_books": TARGET_BOOKS,
            "hard_book_not_executed": HARD_BOOK,
            "compression_bound_changed": False,
            "new_formula_emitted": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
        },
        "summary": {
            "target_book_count": len(rows),
            "roundtrip_book_count": sum(1 for row in rows if row["roundtrip_ok"]),
            "raw_positive_book_count": sum(
                1 for row in rows if row["gain_vs_raw_digit_uniform_bits"] > 0
            ),
            "total_elapsed_seconds": sum(row["elapsed_seconds"] for row in rows),
            "total_parser_bits": sum(row["parser_bits"] for row in rows),
            "total_same_policy_reprice_bits": sum(
                row["same_policy_reprice_bits"] for row in rows
            ),
            "total_parser_minus_same_policy_reprice_bits": sum(
                row["parser_minus_same_policy_reprice_bits"] for row in rows
            ),
            "total_gain_vs_raw_digit_uniform_bits": sum(
                row["gain_vs_raw_digit_uniform_bits"] for row in rows
            ),
            "total_state_evaluations": sum(row["state_evaluations"] for row in rows),
            "total_transition_evaluations": sum(
                row["transition_evaluations"] for row in rows
            ),
            "book_rows": rows,
            "hard_book_proxy": {
                "book": HARD_BOOK,
                "book_digits": hard_proxy["book_digits"],
                "end_state_proxy": hard_proxy["end_state_proxy"],
                "copy_transition_proxy": hard_proxy["copy_transition_proxy"],
                "copy_candidate_edges": hard_proxy["copy_candidate_edges"],
                "distinct_candidate_end_states": hard_proxy[
                    "distinct_candidate_end_states"
                ],
                "reason_not_executed": (
                    "book 66 is the cutoff-60 hard case by transition proxy; "
                    "it needs pruning/caching before exact execution is a useful gate"
                ),
            },
            "interpretation": (
                "The existing active source/length DP is already executable on "
                "small and medium cutoff-60 books, proving the parser path beyond "
                "a proxy audit. It is not yet promotable: the subset is narrow, "
                "the same-policy reparse comparator is still competitive, and the "
                "hard book remains transition-heavy."
            ),
        },
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "source_length_parser_status": "book_local_subset_executable_hard_book_unresolved",
            "generation_explanation_status": "parser_path_progress_not_formula_promotion",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / "73_book_local_source_length_parser_probe.json"
    md_path = TEST_RESULTS / "73_book_local_source_length_parser_probe.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    lines = [
        "# Book-Local Source/Length Parser Probe",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 72 showed that the final source/length parser is feasible by",
        "state proxy but transition-heavy. This probe runs the existing active",
        "source/length DP on two cutoff-60 books to prove executable parser",
        "behavior before attacking the hard case.",
        "",
        "## Summary",
        "",
        f"- Target books: `{result['scope']['target_books']}`.",
        f"- Roundtrip books: `{s['roundtrip_book_count']}/{s['target_book_count']}`.",
        f"- Books beating raw digit uniform: `{s['raw_positive_book_count']}/{s['target_book_count']}`.",
        f"- Total parser bits: `{s['total_parser_bits']:.3f}`.",
        f"- Total same-policy reprice bits: `{s['total_same_policy_reprice_bits']:.3f}`.",
        f"- Parser minus same-policy reprice: `{s['total_parser_minus_same_policy_reprice_bits']:+.3f}` bits.",
        f"- Total gain versus raw digit uniform: `{s['total_gain_vs_raw_digit_uniform_bits']:.3f}` bits.",
        f"- Total state evaluations: `{s['total_state_evaluations']}`.",
        f"- Total transition evaluations: `{s['total_transition_evaluations']}`.",
        f"- Total elapsed: `{s['total_elapsed_seconds']:.3f}` seconds.",
        "",
        "## Book Rows",
        "",
        "| Book | Digits | Parser bits | Same-policy reprice | Delta | Raw gain | Ops | States | Transitions | Seconds |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in s["book_rows"]:
        lines.append(
            f"| `{row['book']}` | `{row['book_digits']}` | "
            f"`{row['parser_bits']:.3f}` | `{row['same_policy_reprice_bits']:.3f}` | "
            f"`{row['parser_minus_same_policy_reprice_bits']:+.3f}` | "
            f"`{row['gain_vs_raw_digit_uniform_bits']:.3f}` | `{row['op_count']}` | "
            f"`{row['state_evaluations']}` | `{row['transition_evaluations']}` | "
            f"`{row['elapsed_seconds']:.3f}` |"
        )
    hard = s["hard_book_proxy"]
    lines.extend(
        [
            "",
            "## Hard Case Held Back",
            "",
            f"- Book: `{hard['book']}`.",
            f"- Digits: `{hard['book_digits']}`.",
            f"- End-state proxy: `{hard['end_state_proxy']}`.",
            f"- Copy-transition proxy: `{hard['copy_transition_proxy']}`.",
            f"- Copy candidate edges: `{hard['copy_candidate_edges']}`.",
            f"- Distinct candidate end states: `{hard['distinct_candidate_end_states']}`.",
            f"- Reason: {hard['reason_not_executed']}.",
            "",
            "## Decision",
            "",
            f"- {s['interpretation']}",
            "- No compression-bound change is introduced.",
            "- No parser or recipe-discovery promotion is introduced.",
            "- Row0 remains unchanged and exogenous.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        ]
    )
    md_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
