from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"
AUTHORIAL = ROOT / "analysis" / "authorial_mechanism_20260620"

SOURCE_FORMULA = (
    AUTHORIAL
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_default_exception_formula_469.json"
)
BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
COMPILE_134 = AUTHORIAL / "scripts" / "134_op_type_derived_recipe_compile.py"
AUDIT_126 = AUTHORIAL / "scripts" / "126_prequential_recipe_reparse_audit.py"
AUDIT_137 = AUTHORIAL / "scripts" / "137_copy_source_default_decodability_audit.py"
GATE37_SCRIPT = HERE / "scripts" / "37_cutoff60_source_state_reparse_prototype_gate.py"
GATE37_RESULT = TEST_RESULTS / "37_cutoff60_source_state_reparse_prototype_gate.json"

PREFIX_CUTOFFS = [10, 20, 35, 50, 60]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
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
    if decision.get("row0_origin_status") not in {None, "unchanged_exogenous"}:
        raise RuntimeError(f"{name} changed row0 origin")
    if decision.get("translation_or_plaintext_status", "NONE") != "NONE":
        raise RuntimeError(f"{name} introduced plaintext status")


def cutoff_reprice(
    *,
    cutoff: int,
    formula: dict[str, Any],
    books: dict[str, str],
    train_counts: dict[str, Any],
    source_train_counts: dict[str, Any],
    audit126,
    gate37,
) -> dict[str, Any]:
    available = "".join(books[str(book)] for book in range(cutoff))
    previous_end = gate37.previous_copy_end_before(formula, cutoff)
    book_rows = []
    aggregate = {
        "bits": 0.0,
        "uniform_address_reparse_bits": 0.0,
        "raw_digit_uniform_bits": 0.0,
        "copy_source_default_exception_bits": 0.0,
        "copy_source_flag_bits": 0.0,
        "copy_source_exception_bits": 0.0,
        "copy_address_bits_removed": 0.0,
        "source_default_count": 0,
        "source_exception_count": 0,
        "copy_items": 0,
        "copied_digits": 0,
        "literal_runs": 0,
        "literal_digits": 0,
    }
    errors = []
    for book in range(cutoff, 70):
        book_key = str(book)
        encoded = audit126.encode_book_frozen_reparse(
            book=book_key,
            text=books[book_key],
            available=available,
            formula=formula,
            train_counts=train_counts,
        )
        if encoded["validation"]["errors"]:
            errors.extend(
                {"book": book, "error": error}
                for error in encoded["validation"]["errors"]
            )
        repriced = gate37.reprice_encoded_book_source_state(
            encoded=encoded,
            available=available,
            formula=formula,
            source_train_counts=source_train_counts,
            initial_previous_copy_end=previous_end,
        )
        if repriced["rendered"] != books[book_key]:
            errors.append({"book": book, "error": "repriced_render_mismatch"})

        bits = encoded["bits"] - encoded["copy_address_bits"] + repriced["source_bits"]
        raw_bits = len(books[book_key]) * math.log2(10)
        row = {
            "book": book,
            "bits": bits,
            "uniform_address_reparse_bits": encoded["bits"],
            "source_state_minus_uniform_address_bits": bits - encoded["bits"],
            "raw_digit_uniform_bits": raw_bits,
            "gain_vs_raw_digit_uniform_bits": raw_bits - bits,
            "uniform_address_gain_vs_raw_digit_uniform_bits": raw_bits - encoded["bits"],
            "copy_source_default_exception_bits": repriced["source_bits"],
            "copy_source_flag_bits": repriced["source_flag_bits"],
            "copy_source_exception_bits": repriced["source_exception_bits"],
            "copy_address_bits_removed": encoded["copy_address_bits"],
            "source_default_count": repriced["source_default_count"],
            "source_exception_count": repriced["source_exception_count"],
            "copy_items": encoded["copy_items"],
            "copied_digits": encoded["copied_digits"],
            "literal_runs": encoded["literal_runs"],
            "literal_digits": encoded["literal_digits"],
            "roundtrip_ok": not encoded["validation"]["errors"],
        }
        book_rows.append(row)
        for key in aggregate:
            aggregate[key] += row[key]
        previous_end = repriced["final_previous_copy_end"]
        available += books[book_key]

    aggregate["source_state_minus_uniform_address_bits"] = (
        aggregate["bits"] - aggregate["uniform_address_reparse_bits"]
    )
    aggregate["gain_vs_raw_digit_uniform_bits"] = (
        aggregate["raw_digit_uniform_bits"] - aggregate["bits"]
    )
    aggregate["uniform_address_gain_vs_raw_digit_uniform_bits"] = (
        aggregate["raw_digit_uniform_bits"] - aggregate["uniform_address_reparse_bits"]
    )
    roundtrip_count = sum(1 for row in book_rows if row["roundtrip_ok"])
    beats_raw_count = sum(1 for row in book_rows if row["gain_vs_raw_digit_uniform_bits"] > 0)
    beats_uniform_count = sum(
        1 for row in book_rows if row["source_state_minus_uniform_address_bits"] < 0
    )
    return {
        "cutoff": cutoff,
        "train_books": list(range(cutoff)),
        "test_books": list(range(cutoff, 70)),
        "book_count": len(book_rows),
        "roundtrip_book_count": roundtrip_count,
        "beats_raw_book_count": beats_raw_count,
        "beats_uniform_address_reparse_book_count": beats_uniform_count,
        "aggregate": aggregate,
        "book_rows": book_rows,
        "errors": errors,
    }


def make_result() -> dict[str, Any]:
    gate37_result = load_json(GATE37_RESULT)
    assert_boundary("cutoff60_source_state_reparse_prototype_gate", gate37_result)
    gate37 = load_module("gate37_source_state_reprice", GATE37_SCRIPT)
    compile134 = load_module("op_type_compile_134", COMPILE_134)
    audit126 = load_module("audit126", AUDIT_126)
    audit137 = load_module("audit137", AUDIT_137)
    payload_module = load_module("payload_context", audit126.PAYLOAD_CONTEXT)
    copy_module = load_module("copy_context", audit126.COPY_CONTEXT)
    item_module = load_module("item_context", audit126.ITEM_CONTEXT)

    formula = compile134.normalize_ops(load_json(SOURCE_FORMULA))
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    copy_rows = copy_module.collect_copy_rows(formula, books)
    payload_rows = payload_module.collect_literal_digit_rows(formula, books)
    item_rows, item_stats = item_module.collect_item_rows(formula, books)
    if item_stats["forced_rule_violations"]:
        raise RuntimeError(item_stats["forced_rule_violations"])
    source_rows = audit137.collect_source_rows(formula, books)
    if source_rows["errors"]:
        raise RuntimeError(source_rows["errors"])
    max_source_count = sum(len(text) for text in books.values()) + 1

    rows = []
    for cutoff in PREFIX_CUTOFFS:
        train_counts = audit126.train_counts_for_cutoff(
            cutoff=cutoff,
            formula=formula,
            copy_rows=copy_rows,
            payload_rows=payload_rows,
            item_rows=item_rows,
        )
        source_train_counts = gate37.source_counts(
            [row for row in source_rows["rows"] if int(row["book"]) < cutoff],
            max_source_count=max_source_count,
        )
        rows.append(
            cutoff_reprice(
                cutoff=cutoff,
                formula=formula,
                books=books,
                train_counts=train_counts,
                source_train_counts=source_train_counts,
                audit126=audit126,
                gate37=gate37,
            )
        )

    all_roundtrip = all(row["roundtrip_book_count"] == row["book_count"] for row in rows)
    all_raw_positive = all(row["beats_raw_book_count"] == row["book_count"] for row in rows)
    aggregate_uniform_wins = [
        row
        for row in rows
        if row["aggregate"]["source_state_minus_uniform_address_bits"] < 0
    ]
    all_aggregate_beats_uniform = len(aggregate_uniform_wins) == len(rows)
    if all_roundtrip and all_raw_positive and all_aggregate_beats_uniform:
        classification = "multicutoff_source_state_reprice_generalizes_aggregate_unpromoted"
    elif all_roundtrip and all_raw_positive:
        classification = "multicutoff_source_state_reprice_roundtrip_positive_mixed_uniform"
    else:
        classification = "multicutoff_source_state_reprice_mixed_unpromoted"

    return {
        "schema": "multicutoff_source_state_reparse_reprice_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "source_formula": rel(SOURCE_FORMULA),
            "books_digits": rel(BOOKS_DIGITS),
            "gate37_script": rel(GATE37_SCRIPT),
            "gate37_result": rel(GATE37_RESULT),
        },
        "scope": {
            "cutoffs": PREFIX_CUTOFFS,
            "prototype_type": "deterministic reparse recipes repriced with previous_copy_end source default ledger",
            "not_recipe_reoptimization": True,
            "source_counts": "frozen from train prefix for each cutoff",
        },
        "summary": {
            "cutoff_count": len(rows),
            "all_roundtrip": all_roundtrip,
            "all_books_beat_raw": all_raw_positive,
            "aggregate_beats_uniform_cutoff_count": len(aggregate_uniform_wins),
            "rows": rows,
            "total_source_state_bits": sum(row["aggregate"]["bits"] for row in rows),
            "total_uniform_address_reparse_bits": sum(
                row["aggregate"]["uniform_address_reparse_bits"] for row in rows
            ),
            "total_source_state_minus_uniform_address_bits": sum(
                row["aggregate"]["source_state_minus_uniform_address_bits"] for row in rows
            ),
            "total_source_defaults": sum(
                row["aggregate"]["source_default_count"] for row in rows
            ),
            "total_source_exceptions": sum(
                row["aggregate"]["source_exception_count"] for row in rows
            ),
            "remaining_blockers": [
                "This is repricing of deterministic reparse recipes, not source-state recipe reoptimization.",
                "The result validates the source ledger over reparsed recipes but does not promote an active parser.",
                "Compression bound, row0 origin, and semantic status are unchanged.",
            ],
        },
        "decision": {
            "source_state_reparse_status": "multicutoff_reprice_executable_aggregate_signal_unpromoted",
            "recipe_discovery_status": "source_state_reprice_only_no_recipe_reoptimization",
            "compression_bound_status": "unchanged_8177_317_active_bound",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / "38_multicutoff_source_state_reparse_reprice_gate.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    lines = [
        "# Multi-Cutoff Source-State Reparse Reprice Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 37 repriced deterministic reparse recipes at cutoff `60` using the",
        "active `previous_copy_end` source ledger. This gate repeats that repricing",
        "for all prefix cutoffs `10/20/35/50/60` with source counts frozen from",
        "the train prefix for each cutoff.",
        "",
        "## Summary",
        "",
        f"- All cutoffs roundtrip: `{s['all_roundtrip']}`.",
        f"- All books beat raw digit coding: `{s['all_books_beat_raw']}`.",
        f"- Aggregate beats uniform-address reparse at cutoffs: `{s['aggregate_beats_uniform_cutoff_count']}/{s['cutoff_count']}`.",
        f"- Total source-state reprice bits: `{s['total_source_state_bits']:.3f}`.",
        f"- Total uniform-address reparse bits: `{s['total_uniform_address_reparse_bits']:.3f}`.",
        f"- Total source-state minus uniform-address bits: `{s['total_source_state_minus_uniform_address_bits']:+.3f}`.",
        f"- Total defaults/exceptions: `{s['total_source_defaults']}` / `{s['total_source_exceptions']}`.",
        "",
        "## Cutoff Rows",
        "",
        "| Cutoff | Books | Roundtrip | Raw wins | Uniform wins | Source-state bits | Uniform-address bits | Delta | Raw gain | Defaults | Exceptions |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in s["rows"]:
        agg = row["aggregate"]
        lines.append(
            f"| `{row['cutoff']}` | `{row['book_count']}` | "
            f"`{row['roundtrip_book_count']}` | `{row['beats_raw_book_count']}` | "
            f"`{row['beats_uniform_address_reparse_book_count']}` | "
            f"`{agg['bits']:.3f}` | `{agg['uniform_address_reparse_bits']:.3f}` | "
            f"`{agg['source_state_minus_uniform_address_bits']:+.3f}` | "
            f"`{agg['gain_vs_raw_digit_uniform_bits']:.3f}` | "
            f"`{agg['source_default_count']}` | `{agg['source_exception_count']}` |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The `previous_copy_end` source ledger is executable across every tested",
            "prequential cutoff on deterministic reparse recipes. It preserves",
            "roundtrip, keeps every book positive against raw digit coding, and is",
            "cheaper than uniform-address reparse in aggregate at every cutoff.",
            "",
            "This is still not a promoted active parser: recipes are generated by",
            "the existing deterministic reparse, then source choices are repriced.",
            "No source-state-aware recipe reoptimization is performed.",
            "",
            "## Boundary",
            "",
            "- No compression-bound change is introduced.",
            "- No complete active parser or global recipe-discovery promotion is introduced.",
            "- Row0 origin remains unchanged and exogenous.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        ]
    )
    (TEST_RESULTS / "38_multicutoff_source_state_reparse_reprice_gate.md").write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
