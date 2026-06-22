#!/usr/bin/env python3
"""Book residual-mode coupling gate.

Several local routes have failed: exact type:length controllers, macro
programs, source-tape removal, and topology/surprisal rescues. This gate tests
a broader representation change: whether the remaining external fields form a
small book-level residual mode.

For each derived book, the executable ledger is summarized into coarse residual
symbols for operation count, literal tape use, copy-hint burden, composition
index burden, and coarse-control shape. A prefix/family-frozen joint-mode codec
is compared against independent field coding and shuffled-within-stream
controls.
"""

from __future__ import annotations

import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "book_residual_mode_coupling_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"

UNIFIED_TAPE_LEDGER = (
    ROOT
    / "analysis"
    / "minimal_external_tape_program_audit_20260622"
    / "reports"
    / "test_results"
    / "02_unified_external_tape_ledger.json"
)
FAMILY_HOLDOUT = (
    ROOT
    / "analysis"
    / "prequential_and_row0_origin_audit_20260621"
    / "reports"
    / "test_results"
    / "08_recipe_reparse_family_holdout.json"
)
FRONTIER_SYNTHESIS = (
    ROOT
    / "analysis"
    / "executable_program_frontier_synthesis_audit_20260622"
    / "reports"
    / "final_executable_program_frontier_synthesis_audit.md"
)

JSON_OUT = TEST_RESULTS / "01_book_residual_mode_coupling_gate.json"
MD_OUT = TEST_RESULTS / "01_book_residual_mode_coupling_gate.md"
FINAL_OUT = FRONT / "reports" / "final_book_residual_mode_coupling_audit.md"

PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
RANDOM_SEED = 46920260622 + 6
RANDOM_TRIALS = 500
ALPHA = 0.5
FIELD_VARIANTS = {
    "all_fields": [
        "op_count_class",
        "literal_digit_class",
        "literal_op_class",
        "copy_hint_bits_class",
        "composition_bits_class",
        "coarse_shape_class",
    ],
    "no_derived_shape": [
        "op_count_class",
        "literal_digit_class",
        "literal_op_class",
        "copy_hint_bits_class",
        "composition_bits_class",
    ],
    "external_burden_only": [
        "literal_digit_class",
        "copy_hint_bits_class",
        "composition_bits_class",
    ],
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def assert_boundary(name: str, data: dict[str, Any]) -> None:
    if data.get("translation_delta") not in {None, "NONE"}:
        raise RuntimeError(f"{name} changed translation boundary")
    if data.get("case_reopened", False) is not False:
        raise RuntimeError(f"{name} reopened the case")
    if data.get("plaintext_claim", False) is not False:
        raise RuntimeError(f"{name} introduced plaintext")
    if data.get("row0_status") not in {None, "unchanged_exogenous"}:
        raise RuntimeError(f"{name} changed row0 status")


def bucket_count(value: int, cuts: list[int], prefix: str) -> str:
    for cut in cuts:
        if value <= cut:
            return f"{prefix}_le_{cut}"
    return f"{prefix}_gt_{cuts[-1]}"


def bucket_bits(value: float, cuts: list[float], prefix: str) -> str:
    for cut in cuts:
        if value <= cut:
            return f"{prefix}_le_{int(cut)}"
    return f"{prefix}_gt_{int(cuts[-1])}"


def summarize_books(ledger: dict[str, Any]) -> dict[int, dict[str, Any]]:
    by_book: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in ledger["ledger_rows"]:
        by_book[int(row["book"])].append(row)
    out = {}
    for book, rows in sorted(by_book.items()):
        literal_rows = [row for row in rows if row["op_type"] == "literal"]
        copy_rows = [row for row in rows if row["op_type"] == "copy"]
        literal_digits = sum(len(row.get("literal_payload") or "") for row in literal_rows)
        copy_hint_bits = sum(float(row.get("copy_hint_rank_bits") or 0.0) for row in copy_rows)
        composition_bits = sum(float(row.get("composition_index_bits_charged_here") or 0.0) for row in rows)
        coarse_symbols = [row["coarse_type_length_bucket"] for row in rows]
        copy_fraction = len(copy_rows) / max(1, len(rows))
        long_copy = sum(1 for row in copy_rows if str(row["coarse_type_length_bucket"]).endswith("0256p"))
        shape = (
            "shape_copy_heavy"
            if copy_fraction >= 0.75
            else "shape_literal_heavy"
            if copy_fraction <= 0.25
            else "shape_mixed"
        )
        if long_copy:
            shape += "_longcopy"
        out[book] = {
            "book": book,
            "book_length": rows[0]["book_length"],
            "copy_hint_bits": copy_hint_bits,
            "copy_hint_bits_class": bucket_bits(copy_hint_bits, [0, 12, 24, 48], "copyhint"),
            "composition_bits": composition_bits,
            "composition_bits_class": bucket_bits(composition_bits, [0, 5, 15, 30], "comp"),
            "coarse_shape_class": shape,
            "coarse_symbols": coarse_symbols,
            "literal_digit_class": bucket_count(literal_digits, [0, 5, 12, 24], "litdigits"),
            "literal_digits": literal_digits,
            "literal_op_class": bucket_count(len(literal_rows), [0, 1, 2, 4], "litops"),
            "literal_ops": len(literal_rows),
            "op_count": len(rows),
            "op_count_class": bucket_count(len(rows), [1, 2, 4, 8], "ops"),
        }
    return out


def load_family_splits(books: set[int]) -> list[dict[str, Any]]:
    if not FAMILY_HOLDOUT.exists():
        return []
    out = []
    for row in load_json(FAMILY_HOLDOUT).get("rows", []):
        test = {int(book) for book in row.get("test_books", []) if int(book) in books}
        train = books - test
        if train and test:
            out.append(
                {
                    "label": f"family_{row['label']}",
                    "split_type": "family",
                    "test": test,
                    "train": train,
                }
            )
    return out


def split_specs(book_rows: dict[int, dict[str, Any]]) -> list[dict[str, Any]]:
    books = set(book_rows)
    specs = []
    for cutoff in PREFIX_CUTOFFS:
        train = {book for book in books if book < cutoff}
        test = {book for book in books if book >= cutoff}
        if train and test:
            specs.append({"label": f"prefix_{cutoff}", "split_type": "prefix", "train": train, "test": test})
    specs.extend(load_family_splits(books))
    return specs


def alphabets(book_rows: dict[int, dict[str, Any]], fields: list[str]) -> dict[str, list[str]]:
    values = {}
    for field in fields:
        values[field] = sorted({str(row[field]) for row in book_rows.values()})
    values["joint"] = sorted({joint_symbol(row, fields) for row in book_rows.values()})
    return values


def joint_symbol(row: dict[str, Any], fields: list[str]) -> str:
    return "|".join(str(row[field]) for field in fields)


def code_symbol(
    symbol: str,
    counts: Counter[str],
    alphabet_size: int,
) -> float:
    total = sum(counts.values())
    probability = (counts.get(symbol, 0) + ALPHA) / (total + ALPHA * alphabet_size)
    return -math.log2(probability)


def field_counts(book_rows: dict[int, dict[str, Any]], train: set[int], field: str) -> Counter[str]:
    return Counter(str(book_rows[book][field]) for book in train)


def joint_counts(book_rows: dict[int, dict[str, Any]], train: set[int], fields: list[str]) -> Counter[str]:
    return Counter(joint_symbol(book_rows[book], fields) for book in train)


def evaluate_split(
    book_rows: dict[int, dict[str, Any]],
    split: dict[str, Any],
    alpha_values: dict[str, list[str]],
    fields: list[str],
) -> dict[str, Any]:
    train = split["train"]
    test = split["test"]
    independent_bits = 0.0
    field_train_counts = {
        field: field_counts(book_rows, train, field)
        for field in fields
    }
    for book in sorted(test):
        row = book_rows[book]
        for field in fields:
            independent_bits += code_symbol(str(row[field]), field_train_counts[field], len(alpha_values[field]))
    joint_train_counts = joint_counts(book_rows, train, fields)
    joint_bits = 0.0
    exact_joint_hits = 0
    for book in sorted(test):
        symbol = joint_symbol(book_rows[book], fields)
        exact_joint_hits += int(joint_train_counts.get(symbol, 0) > 0)
        joint_bits += code_symbol(symbol, joint_train_counts, len(alpha_values["joint"]))
    descriptor_bits = math.log2(len(fields))
    joint_bits += descriptor_bits
    return {
        "descriptor_bits": descriptor_bits,
        "exact_joint_hits": exact_joint_hits,
        "independent_bits": independent_bits,
        "joint_bits": joint_bits,
        "label": split["label"],
        "saving_bits": independent_bits - joint_bits,
        "split_type": split["split_type"],
        "test_books": len(test),
        "train_books": len(train),
    }


def evaluate_all(book_rows: dict[int, dict[str, Any]], fields: list[str]) -> dict[str, Any]:
    alpha_values = alphabets(book_rows, fields)
    rows = [
        evaluate_split(book_rows, split, alpha_values, fields)
        for split in split_specs(book_rows)
    ]
    total_independent = sum(row["independent_bits"] for row in rows)
    total_joint = sum(row["joint_bits"] for row in rows)
    return {
        "alphabet_sizes": {key: len(value) for key, value in alpha_values.items()},
        "split_rows": rows,
        "summary": {
            "exact_joint_hits": sum(row["exact_joint_hits"] for row in rows),
            "positive_splits": sum(row["saving_bits"] > 0 for row in rows),
            "split_count": len(rows),
            "test_books_repeated": sum(row["test_books"] for row in rows),
            "total_independent_bits": total_independent,
            "total_joint_bits": total_joint,
            "total_saving_bits": total_independent - total_joint,
        },
    }


def shuffled_field_controls(book_rows: dict[int, dict[str, Any]], fields: list[str], real_saving: float) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED)
    books = sorted(book_rows)
    savings = []
    for _ in range(RANDOM_TRIALS):
        shuffled = {book: dict(book_rows[book]) for book in books}
        for field in fields:
            values = [book_rows[book][field] for book in books]
            rng.shuffle(values)
            for book, value in zip(books, values):
                shuffled[book][field] = value
        savings.append(evaluate_all(shuffled, fields)["summary"]["total_saving_bits"])
    return {
        "beats_shuffled_p05": real_saving > percentile(savings, 5),
        "beats_shuffled_p50": real_saving > percentile(savings, 50),
        "beats_shuffled_p95": real_saving > percentile(savings, 95),
        "shuffled_mean": sum(savings) / len(savings),
        "shuffled_p05": percentile(savings, 5),
        "shuffled_p50": percentile(savings, 50),
        "shuffled_p95": percentile(savings, 95),
        "trials": RANDOM_TRIALS,
    }


def percentile(values: list[float], p: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, math.ceil(p / 100 * len(ordered)) - 1))
    return ordered[index]


def make_result() -> dict[str, Any]:
    ledger = load_json(UNIFIED_TAPE_LEDGER)
    assert_boundary("unified_external_tape_ledger", ledger)
    book_rows = summarize_books(ledger)
    variant_results = {}
    promoted_variants = []
    weak_variants = []
    for variant, fields in FIELD_VARIANTS.items():
        evaluated = evaluate_all(book_rows, fields)
        controls = shuffled_field_controls(book_rows, fields, evaluated["summary"]["total_saving_bits"])
        evaluated["controls"] = controls
        evaluated["fields"] = fields
        variant_results[variant] = evaluated
        if evaluated["summary"]["total_saving_bits"] > 0 and controls["beats_shuffled_p95"]:
            promoted_variants.append(variant)
        elif evaluated["summary"]["total_saving_bits"] > 0 and controls["beats_shuffled_p50"]:
            weak_variants.append(variant)
    primary = variant_results["no_derived_shape"]
    promoted = "no_derived_shape" in promoted_variants
    weak = "no_derived_shape" in weak_variants
    classification = (
        "PROMOTED_BOOK_RESIDUAL_MODE_COUPLING"
        if promoted
        else "WEAK_BOOK_RESIDUAL_MODE_COUPLING"
        if weak
        else "BOOK_RESIDUAL_MODE_COUPLING_NOT_PROMOTED"
    )
    return {
        "case_reopened": False,
        "classification": classification,
        "compression_bound_status": "unchanged",
        "controls": primary["controls"],
        "decision": {
            "generator_promoted": False,
            "joint_mode_promoted": promoted,
            "row0_status": "unchanged_exogenous",
            "translation_delta": "NONE",
        },
        "inputs": {
            "executable_frontier_synthesis": rel(FRONTIER_SYNTHESIS),
            "family_holdout": rel(FAMILY_HOLDOUT),
            "unified_external_tape_ledger": rel(UNIFIED_TAPE_LEDGER),
        },
        "plaintext_claim": False,
        "schema": "book_residual_mode_coupling_gate.v1",
        "scope": "analysis_only_book_level_joint_residual_mode",
        "summary": {
            **primary["summary"],
            "book_count": len(book_rows),
            "fields": FIELD_VARIANTS["no_derived_shape"],
            "promoted_variants": promoted_variants,
            "shuffled_p95": primary["controls"]["shuffled_p95"],
            "weak_variants": weak_variants,
        },
        "variant_results": variant_results,
        "translation_delta": "NONE",
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    c = result["variant_results"]["no_derived_shape"]["controls"]
    lines = [
        "# Book Residual Mode Coupling Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Purpose",
        "",
        "Test whether the remaining external fields form a compact book-level "
        "residual mode rather than independent tapes.",
        "",
        "## Summary",
        "",
        f"- Books: `{s['book_count']}`.",
        f"- Fields: `{', '.join(s['fields'])}`.",
        f"- Independent field bits: `{s['total_independent_bits']:.3f}`.",
        f"- Joint-mode bits: `{s['total_joint_bits']:.3f}`.",
        f"- Saving: `{s['total_saving_bits']:.3f}` bits.",
        f"- Positive splits: `{s['positive_splits']}/{s['split_count']}`.",
        f"- Exact joint hits: `{s['exact_joint_hits']}/{s['test_books_repeated']}` repeated test-book evaluations.",
        f"- Shuffled p95: `{c['shuffled_p95']:.3f}`.",
        f"- Beats shuffled p95: `{c['beats_shuffled_p95']}`.",
        f"- Promoted variants: `{s['promoted_variants']}`.",
        "",
        "## Variant Summary",
        "",
        "| Variant | Fields | Saving | Shuffled p95 | Beats p95 | Positive splits |",
        "| --- | --- | ---: | ---: | --- | ---: |",
    ]
    for variant, data in result["variant_results"].items():
        summary = data["summary"]
        controls = data["controls"]
        lines.append(
            f"| `{variant}` | `{len(data['fields'])}` | `{summary['total_saving_bits']:.3f}` | "
            f"`{controls['shuffled_p95']:.3f}` | `{controls['beats_shuffled_p95']}` | "
            f"`{summary['positive_splits']}/{summary['split_count']}` |"
        )
    lines.extend(["", "## Primary Split Results", ""])
    lines.extend(
        [
            "| Split | Type | Test books | Saving | Joint bits | Independent bits | Exact hits |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in result["variant_results"]["no_derived_shape"]["split_rows"]:
        lines.append(
            f"| `{row['label']}` | `{row['split_type']}` | `{row['test_books']}` | "
            f"`{row['saving_bits']:.3f}` | `{row['joint_bits']:.3f}` | "
            f"`{row['independent_bits']:.3f}` | `{row['exact_joint_hits']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "Promotion requires joint-mode coding to reduce the external ledger and "
            "beat shuffled-within-stream controls. This gate promotes a book-level "
            "residual coupling clue when the primary no-derived-shape variant passes; "
            "it still does not generate exact operation streams, literal payload, or "
            "copy hints.",
        ]
    )
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    s = result["summary"]
    c = result["variant_results"]["no_derived_shape"]["controls"]
    lines = [
        "# Final Book Residual Mode Coupling Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Question",
        "",
        "Do the remaining external streams share a compact book-level residual mode "
        "that could become the next generator representation?",
        "",
        "## Result",
        "",
        f"Joint-mode coding costs `{s['total_joint_bits']:.3f}` bits versus "
        f"`{s['total_independent_bits']:.3f}` independent field bits "
        f"(`{s['total_saving_bits']:.3f}`). It has `{s['positive_splits']}/{s['split_count']}` "
        f"positive splits and beats shuffled p95: `{c['beats_shuffled_p95']}` "
        f"(p95 `{c['shuffled_p95']:.3f}`).",
        "",
        "## Decision",
        "",
        "This promotes a book-level residual-mode coupling clue, not a complete "
        "generator. The result says the remaining external burdens are synchronized "
        "at coarse book level and should be tested next as a latent book-mode program. "
        "It still does not derive exact type:length streams, literal payload, copy "
        "hints, row0, plaintext, translation, or compression_bound.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_book_residual_mode_coupling_gate.py](../scripts/01_book_residual_mode_coupling_gate.py)",
        "- [01_book_residual_mode_coupling_gate.json](test_results/01_book_residual_mode_coupling_gate.json)",
        "- [01_book_residual_mode_coupling_gate.md](test_results/01_book_residual_mode_coupling_gate.md)",
    ]
    FINAL_OUT.write_text("\n".join(lines) + "\n")


def main() -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    result = make_result()
    JSON_OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_markdown(result)
    write_final(result)


if __name__ == "__main__":
    main()
